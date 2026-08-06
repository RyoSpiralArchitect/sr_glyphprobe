#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import platform
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np

from glyphprobe.backends.mlx_backend import MLXBackend
from glyphprobe.backends.transformers_backend import TransformersBackend
from glyphprobe.config import BackendConfig
from glyphprobe.io import write_json
from glyphprobe.provenance import implementation_receipt, stable_model_identity
from glyphprobe.records import Intervention


DEFAULT_MODEL = "openai-community/gpt2"
DEFAULT_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
DEFAULT_PROMPTS = (
    "🟤",
    "Mark: 🟫\nAnchor:",
    "Continue briefly: The scientist opened the notebook and",
    (
        "Write a concise two-sentence explanation of why a careful scientist records "
        "every calibration setting before comparing experimental interventions."
    ),
)
STANDARD_LAYERS = (2, 4, 7, 9)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _comparison(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    ref = np.asarray(reference, dtype=np.float64).reshape(-1)
    cand = np.asarray(candidate, dtype=np.float64).reshape(-1)
    if ref.shape != cand.shape:
        return {
            "shape_match": False,
            "reference_shape": list(ref.shape),
            "candidate_shape": list(cand.shape),
        }
    diff = cand - ref
    rmse = float(np.sqrt(np.mean(np.square(diff))))
    reference_rms = float(np.sqrt(np.mean(np.square(ref))))
    candidate_rms = float(np.sqrt(np.mean(np.square(cand))))
    denom = float(np.linalg.norm(ref) * np.linalg.norm(cand))
    cosine = float(np.dot(ref, cand) / denom) if denom > 0 else None
    return {
        "shape_match": True,
        "max_abs": float(np.max(np.abs(diff))) if diff.size else 0.0,
        "rmse": rmse,
        "reference_rms": reference_rms,
        "candidate_rms": candidate_rms,
        "rms_ratio": candidate_rms / max(reference_rms, 1e-12),
        "normalized_rmse": rmse / max(reference_rms, 1e-12),
        "cosine": cosine,
    }


def _metric_pass(
    metric: dict[str, Any],
    *,
    max_nrmse: float,
    min_cosine: float,
    rms_ratio: tuple[float, float] | None = None,
) -> bool:
    if not metric.get("shape_match"):
        return False
    cosine = metric.get("cosine")
    passed = (
        metric.get("normalized_rmse", float("inf")) <= max_nrmse
        and cosine is not None
        and cosine >= min_cosine
    )
    if rms_ratio is not None:
        passed = passed and rms_ratio[0] <= metric.get("rms_ratio", 0.0) <= rms_ratio[1]
    return bool(passed)


def _timed_forward(
    backend: Any,
    prompt: str,
    intervention: Intervention,
    *,
    layer: int,
) -> float:
    started = time.perf_counter()
    backend.forward(
        prompt,
        capture_layers=[layer],
        site="resid_post",
        intervention=intervention,
    )
    return (time.perf_counter() - started) * 1000.0


def _distribution_summary(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    p95_index = min(len(ordered) - 1, int(np.ceil(0.95 * len(ordered))) - 1)
    return {
        "median_ms": float(statistics.median(values)),
        "mean_ms": float(statistics.fmean(values)),
        "min_ms": float(min(values)),
        "p95_ms": float(ordered[p95_index]),
    }


def _benchmark(
    torch_backend: TransformersBackend,
    mlx_backend: MLXBackend,
    *,
    prompts: list[str],
    layers: tuple[int, ...],
    vector: np.ndarray,
    warmups: int,
    repeats: int,
) -> dict[str, Any]:
    aggregate: dict[str, list[float]] = {"transformers_mps": [], "mlx_gpu": []}
    cells: list[dict[str, Any]] = []
    prompt_token_counts = [len(torch_backend.tokenize(prompt).token_ids) for prompt in prompts]
    for prompt_index, (prompt, token_count) in enumerate(zip(prompts, prompt_token_counts)):
        for layer in layers:
            intervention = Intervention(
                layer=layer,
                vector=vector,
                site="resid_post",
                position="last_nonpad",
                label="fixed-parity-vector",
            )
            for _ in range(warmups):
                _timed_forward(torch_backend, prompt, intervention, layer=layer)
                _timed_forward(mlx_backend, prompt, intervention, layer=layer)

            samples: dict[str, list[float]] = {"transformers_mps": [], "mlx_gpu": []}
            for repeat in range(repeats):
                order = (
                    (("transformers_mps", torch_backend), ("mlx_gpu", mlx_backend))
                    if repeat % 2 == 0
                    else (("mlx_gpu", mlx_backend), ("transformers_mps", torch_backend))
                )
                for label, backend in order:
                    elapsed = _timed_forward(backend, prompt, intervention, layer=layer)
                    samples[label].append(elapsed)
                    aggregate[label].append(elapsed)
            cells.append(
                {
                    "prompt_id": f"prompt_{prompt_index:02d}",
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "prompt_token_count": token_count,
                    "layer": layer,
                    "transformers_mps": _distribution_summary(samples["transformers_mps"]),
                    "mlx_gpu": _distribution_summary(samples["mlx_gpu"]),
                    "mlx_speedup": float(
                        statistics.median(samples["transformers_mps"])
                        / statistics.median(samples["mlx_gpu"])
                    ),
                }
            )

    summary: dict[str, Any] = {
        "method": (
            "alternating synchronized end-to-end backend.forward wall time over the "
            "sealed standard layers and multiple prompt-length buckets; includes "
            "tokenization, capture/intervention, device evaluation, and NumPy transfer"
        ),
        "warmups_per_cell": warmups,
        "repeats_per_cell": repeats,
        "prompt_token_counts": prompt_token_counts,
        "layers": list(layers),
        "cell_count": len(cells),
        "cells": cells,
        "transformers_mps": _distribution_summary(aggregate["transformers_mps"]),
        "mlx_gpu": _distribution_summary(aggregate["mlx_gpu"]),
    }
    torch_median = summary["transformers_mps"]["median_ms"]
    mlx_median = summary["mlx_gpu"]["median_ms"]
    summary["mlx_speedup"] = float(torch_median / mlx_median)
    summary["speed_gate"] = {
        "criterion": (
            "Across the predefined layer-by-length matrix, MLX aggregate median "
            "end-to-end latency is at least 5% lower than Transformers/MPS"
        ),
        "pass": bool(mlx_median <= 0.95 * torch_median),
    }
    return summary


def _parity_gate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for case in cases:
        baseline_activations_pass = all(
            _metric_pass(value, max_nrmse=5e-4, min_cosine=0.99999)
            for value in case["baseline_activations"].values()
        )
        fixed_pass = (
            _metric_pass(case["changed_logits"], max_nrmse=5e-4, min_cosine=0.99999)
            and _metric_pass(
                case["changed_activation"], max_nrmse=5e-4, min_cosine=0.99999
            )
            and _metric_pass(
                case["logit_delta"],
                max_nrmse=5e-3,
                min_cosine=0.995,
                rms_ratio=(0.995, 1.005),
            )
            and _metric_pass(
                case["activation_delta"],
                max_nrmse=5e-4,
                min_cosine=0.99999,
                rms_ratio=(0.999, 1.001),
            )
            and _metric_pass(
                case["torch_intervention_fidelity"],
                max_nrmse=1e-5,
                min_cosine=0.999999,
            )
            and _metric_pass(
                case["mlx_intervention_fidelity"],
                max_nrmse=1e-5,
                min_cosine=0.999999,
            )
            and case["changed_argmax_match"]
        )
        checks.extend(
            [
                {
                    "id": f"{case['id']}:token_ids",
                    "pass": case["token_ids_match"],
                    "value": case["token_ids_match"],
                    "criterion": "Exact token ID equality",
                },
                {
                    "id": f"{case['id']}:baseline_logits",
                    "pass": (
                        _metric_pass(
                            case["baseline_logits"],
                            max_nrmse=5e-4,
                            min_cosine=0.99999,
                        )
                        and case["baseline_argmax_match"]
                    ),
                    "value": case["baseline_logits"],
                    "criterion": "NRMSE <= 5e-4, cosine >= 0.99999, and exact argmax",
                },
                {
                    "id": f"{case['id']}:baseline_activations",
                    "pass": baseline_activations_pass,
                    "value": case["baseline_activations"],
                    "criterion": "Each standard-layer resid_post NRMSE <= 5e-4 and cosine >= 0.99999",
                },
                {
                    "id": f"{case['id']}:zero_hook",
                    "pass": all(value <= 1e-7 for value in case["zero_hook"].values()),
                    "value": case["zero_hook"],
                    "criterion": "Zero vector changes neither logits nor captured activation above 1e-7",
                },
                {
                    "id": f"{case['id']}:fixed_intervention",
                    "pass": fixed_pass,
                    "value": {
                        key: case[key]
                        for key in (
                            "changed_logits",
                            "changed_activation",
                            "logit_delta",
                            "activation_delta",
                            "torch_intervention_fidelity",
                            "mlx_intervention_fidelity",
                        )
                    },
                    "criterion": (
                        "Changed outputs preserve baseline tolerances; logit-delta NRMSE <= 5e-3, "
                        "cosine >= 0.995, RMS ratio in [0.995,1.005]; activation deltas and "
                        "injected-vector magnitude agree; exact changed argmax"
                    ),
                },
            ]
        )
    return {
        "checks": checks,
        "passed": sum(bool(item["pass"]) for item in checks),
        "total": len(checks),
        "pass": all(bool(item["pass"]) for item in checks),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    common = {
        "model": args.model,
        "revision": args.revision,
        "dtype": "float32",
        "local_files_only": True,
        "add_special_tokens": True,
    }
    torch_backend = TransformersBackend(
        BackendConfig(kind="transformers", device="mps", **common)
    )
    mlx_backend = MLXBackend(BackendConfig(kind="mlx", device="gpu", **common))
    mlx_backend._parity_probe_mode = True
    load_times: dict[str, float] = {}
    try:
        started = time.perf_counter()
        torch_backend.load()
        load_times["transformers_mps_ms"] = (time.perf_counter() - started) * 1000.0
        started = time.perf_counter()
        mlx_backend.load()
        load_times["mlx_gpu_ms"] = (time.perf_counter() - started) * 1000.0

        if torch_backend.model_dim != mlx_backend.model_dim:
            return {
                "schema_version": 2,
                "status": "validation_failed",
                "reason": "model_width_mismatch",
                "torch_model_dim": torch_backend.model_dim,
                "mlx_model_dim": mlx_backend.model_dim,
            }
        width = int(torch_backend.model_dim)
        fixed_vector = np.linspace(-0.05, 0.05, width, dtype=np.float32)
        zero_vector = np.zeros(width, dtype=np.float32)
        cases: list[dict[str, Any]] = []
        for prompt_index, prompt in enumerate(args.prompts):
            torch_base = torch_backend.forward(
                prompt, capture_layers=list(STANDARD_LAYERS), site="resid_post"
            )
            mlx_base = mlx_backend.forward(
                prompt, capture_layers=list(STANDARD_LAYERS), site="resid_post"
            )
            for layer in STANDARD_LAYERS:
                zero = Intervention(
                    layer=layer,
                    vector=zero_vector,
                    site="resid_post",
                    label="zero-parity-vector",
                )
                changed = Intervention(
                    layer=layer,
                    vector=fixed_vector,
                    site="resid_post",
                    label="fixed-parity-vector",
                )
                torch_zero = torch_backend.forward(
                    prompt, capture_layers=[layer], site="resid_post", intervention=zero
                )
                mlx_zero = mlx_backend.forward(
                    prompt, capture_layers=[layer], site="resid_post", intervention=zero
                )
                torch_changed = torch_backend.forward(
                    prompt, capture_layers=[layer], site="resid_post", intervention=changed
                )
                mlx_changed = mlx_backend.forward(
                    prompt, capture_layers=[layer], site="resid_post", intervention=changed
                )
                torch_activation_delta = (
                    torch_changed.activations[layer] - torch_base.activations[layer]
                )
                mlx_activation_delta = (
                    mlx_changed.activations[layer] - mlx_base.activations[layer]
                )
                cases.append(
                    {
                        "id": f"prompt_{prompt_index:02d}_layer_{layer:02d}",
                        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                        "token_count": len(torch_base.token_ids),
                        "intervention_layer": layer,
                        "token_ids_match": torch_base.token_ids == mlx_base.token_ids,
                        "baseline_argmax_match": int(np.argmax(torch_base.logits))
                        == int(np.argmax(mlx_base.logits)),
                        "baseline_logits": _comparison(torch_base.logits, mlx_base.logits),
                        "baseline_activations": {
                            str(capture_layer): _comparison(
                                torch_base.activations[capture_layer],
                                mlx_base.activations[capture_layer],
                            )
                            for capture_layer in STANDARD_LAYERS
                        },
                        "zero_hook": {
                            "torch_max_logit_delta": float(
                                np.max(np.abs(torch_zero.logits - torch_base.logits))
                            ),
                            "mlx_max_logit_delta": float(
                                np.max(np.abs(mlx_zero.logits - mlx_base.logits))
                            ),
                            "torch_max_activation_delta": float(
                                np.max(
                                    np.abs(
                                        torch_zero.activations[layer]
                                        - torch_base.activations[layer]
                                    )
                                )
                            ),
                            "mlx_max_activation_delta": float(
                                np.max(
                                    np.abs(
                                        mlx_zero.activations[layer]
                                        - mlx_base.activations[layer]
                                    )
                                )
                            ),
                        },
                        "changed_argmax_match": int(np.argmax(torch_changed.logits))
                        == int(np.argmax(mlx_changed.logits)),
                        "changed_logits": _comparison(
                            torch_changed.logits, mlx_changed.logits
                        ),
                        "changed_activation": _comparison(
                            torch_changed.activations[layer], mlx_changed.activations[layer]
                        ),
                        "logit_delta": _comparison(
                            torch_changed.logits - torch_base.logits,
                            mlx_changed.logits - mlx_base.logits,
                        ),
                        "activation_delta": _comparison(
                            torch_activation_delta, mlx_activation_delta
                        ),
                        "torch_intervention_fidelity": _comparison(
                            fixed_vector, torch_activation_delta
                        ),
                        "mlx_intervention_fidelity": _comparison(
                            fixed_vector, mlx_activation_delta
                        ),
                    }
                )

        parity = _parity_gate(cases)
        benchmark = _benchmark(
            torch_backend,
            mlx_backend,
            prompts=list(args.prompts),
            layers=STANDARD_LAYERS,
            vector=fixed_vector,
            warmups=args.warmups,
            repeats=args.repeats,
        )
        status = (
            "validated_mlx_selected"
            if parity["pass"] and benchmark["speed_gate"]["pass"]
            else "validation_failed"
        )
        implementation = implementation_receipt()
        torch_model_receipt = torch_backend.model_receipt()
        mlx_model_receipt = mlx_backend.model_receipt()
        return {
            "schema_version": 2,
            "status": status,
            "claim_boundary": "pinned-gpt2-fp32-resid-post-backend-parity-and-speed-only",
            "scientific_result": False,
            "model": args.model,
            "revision": args.revision,
            "dtype": "float32",
            "site": "resid_post",
            "capture_layers": list(STANDARD_LAYERS),
            "intervention_layers": list(STANDARD_LAYERS),
            "fixed_intervention": {
                "construction": "float32 linspace(-0.05, 0.05, model_width)",
                "width": width,
                "rms": float(np.sqrt(np.mean(np.square(fixed_vector)))),
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
            "validator_sha256": _sha256(Path(__file__).resolve()),
            "implementation": implementation,
            "load_times": load_times,
            "torch_model_receipt": torch_model_receipt,
            "torch_model_identity_sha256": stable_model_identity(torch_model_receipt)[
                "sha256"
            ],
            "mlx_model_receipt": mlx_model_receipt,
            "mlx_model_identity_sha256": stable_model_identity(mlx_model_receipt)["sha256"],
            "parity": parity,
            "cases": cases,
            "benchmark": benchmark,
            "decision": (
                "Use MLX for the pinned GPT-2 FP32 resid_post standard cell only"
                if status == "validated_mlx_selected"
                else "Do not use MLX for scientific runs until failed gates are resolved"
            ),
        }
    finally:
        mlx_backend.close()
        torch_backend.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate pinned GPT-2 FP32 standard-layer parity and synchronized MLX speed."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/mlx_gpt2_parity/receipt.json"),
    )
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--prompt", dest="prompts", action="append")
    args = parser.parse_args()
    if args.warmups < 0 or args.repeats <= 0:
        parser.error("--warmups must be non-negative and --repeats must be positive")
    if args.prompts is None:
        args.prompts = list(DEFAULT_PROMPTS)
    receipt = run(args)
    write_json(args.output.resolve(), receipt)
    print(f"status={receipt['status']}")
    if "parity" in receipt:
        print(f"parity={receipt['parity']['passed']}/{receipt['parity']['total']}")
        print(f"mlx_speedup={receipt['benchmark']['mlx_speedup']:.3f}x")
    print(f"receipt={args.output.resolve()}")
    return 0 if receipt["status"] == "validated_mlx_selected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
