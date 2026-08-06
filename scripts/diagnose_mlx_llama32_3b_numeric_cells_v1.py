#!/usr/bin/env python3
"""Engineering-only numeric-cell screen for the sealed Llama 3.2 3B artifact.

This screen is deliberately narrower than a parity qualification.  It evaluates
two independent runtime-dtype candidates (FP16 and FP32) against fixed backend
calibration prompts, then selects at most one candidate for a future *separately
frozen* full parity validator.  It never reads a study target bank and its
receipt cannot authorize scientific activation interventions.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from glyphprobe.config import BackendConfig
from glyphprobe.io import json_dumps
from glyphprobe.provenance import implementation_receipt, stable_model_identity
from glyphprobe.records import Intervention


MODEL_ID = "mlx-community/Llama-3.2-3B-bf16"
MODEL_REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1"
VALIDATOR_VERSION = 1
NUMERIC_CANDIDATES = ("float16", "float32")
SITE = "resid_post"
LAYERS = (5, 11)
ADD_SPECIAL_TOKENS = False
EXPECTED_NUM_LAYERS = 28
EXPECTED_MODEL_WIDTH = 3072
EXPECTED_VOCAB_SIZE = 128_256
EXPECTED_PARAMETER_COUNT = 3_212_749_824
EXPECTED_ARTIFACT_FILE_COUNT = 9
EXPECTED_ARTIFACT_TOTAL_BYTES = 6_434_705_789
EXPECTED_ARTIFACT_MANIFEST_SHA256 = (
    "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
)
RELATIVE_INTERVENTION_RMS = 0.05
WARMUPS = 2
REPEATS = 10
DEFAULT_OUTPUT = Path("validation/mlx_llama32_3b_numeric_screen_v1/receipt.json")
CLAIM_BOUNDARY = "engineering-only-runtime-dtype-candidate-screen"

# These are fixed before execution.  They reuse the v2 intervention-fidelity
# and speed gates verbatim; no observed v2 value is used to relax them.
THRESHOLDS: dict[str, Any] = {
    "intervention_fidelity": {
        "max_normalized_rmse": 0.01,
        "min_cosine": 0.999,
    },
    "zero_hook_max_abs": 1e-7,
    "speed": {"mlx_max_fraction_of_transformers_median": 0.95},
    "exact_token_ids": True,
    "exact_argmax": True,
    "selection_tie_relative_latency": 0.01,
}

PROMPTS = (
    "🌒",
    "🐑",
    "Mark: 🤑\nAnchor:",
    "Continue briefly: The scientist opened the notebook and",
    (
        "Write a concise two-sentence explanation of why a careful scientist records "
        "every calibration setting before comparing experimental interventions."
    ),
)

VALIDATION_CONFIG: dict[str, Any] = {
    "protocol_id": PROTOCOL_ID,
    "validator_version": VALIDATOR_VERSION,
    "model": MODEL_ID,
    "revision": MODEL_REVISION,
    "artifact_storage_dtype": "bfloat16",
    "runtime_dtype_candidates": list(NUMERIC_CANDIDATES),
    "site": SITE,
    "layers": list(LAYERS),
    "add_special_tokens": ADD_SPECIAL_TOKENS,
    "expected_architecture": {
        "num_layers": EXPECTED_NUM_LAYERS,
        "model_width": EXPECTED_MODEL_WIDTH,
        "vocab_size": EXPECTED_VOCAB_SIZE,
        "parameter_count": EXPECTED_PARAMETER_COUNT,
    },
    "expected_model_artifact": {
        "file_count": EXPECTED_ARTIFACT_FILE_COUNT,
        "total_bytes": EXPECTED_ARTIFACT_TOTAL_BYTES,
        "manifest_sha256": EXPECTED_ARTIFACT_MANIFEST_SHA256,
    },
    "prompts": list(PROMPTS),
    "relative_intervention_rms": RELATIVE_INTERVENTION_RMS,
    "direction": "float32 linspace(-0.05, 0.05, 3072), centered, RMS-normalized",
    "warmups_per_cell": WARMUPS,
    "repeats_per_cell": REPEATS,
    "thresholds": THRESHOLDS,
    "selection_rule": (
        "candidate eligible iff exact token/determinism, exact zero hook, both "
        "backend fidelity gates, runtime-dtype identity, and speed gate pass; one "
        "eligible candidate wins; if both are eligible choose lower MLX aggregate "
        "median, with FP32 selected when medians differ by <= 1 percent; none is no-go"
    ),
}
VALIDATION_CONFIG_SHA256 = hashlib.sha256(
    json_dumps(VALIDATION_CONFIG, pretty=False).encode("utf-8")
).hexdigest()


class ValidationError(RuntimeError):
    pass


class WorkerFailure(ValidationError):
    def __init__(self, message: str, lifecycle: dict[str, Any]) -> None:
        super().__init__(message)
        self.lifecycle = lifecycle


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rms(value: np.ndarray) -> float:
    array = np.asarray(value, dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(array))))


def _fixed_unit_direction(width: int = EXPECTED_MODEL_WIDTH) -> np.ndarray:
    raw = np.linspace(-0.05, 0.05, width, dtype=np.float32)
    raw = raw - np.mean(raw, dtype=np.float32)
    return np.asarray(raw / _rms(raw), dtype=np.float32)


def _intervention_vector(target_rms: float) -> np.ndarray:
    return np.asarray(_fixed_unit_direction() * target_rms, dtype=np.float32)


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(np.asarray(value, dtype=np.float32))
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


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
    rmse = _rms(diff)
    reference_rms = _rms(ref)
    candidate_rms = _rms(cand)
    denominator = float(np.linalg.norm(ref) * np.linalg.norm(cand))
    return {
        "shape_match": True,
        "max_abs": float(np.max(np.abs(diff))) if diff.size else 0.0,
        "rmse": rmse,
        "reference_rms": reference_rms,
        "candidate_rms": candidate_rms,
        "rms_ratio": candidate_rms / max(reference_rms, 1e-12),
        "normalized_rmse": rmse / max(reference_rms, 1e-12),
        "cosine": float(np.dot(ref, cand) / denominator) if denominator > 0 else None,
    }


def _metric_pass(metric: dict[str, Any], threshold: dict[str, Any]) -> bool:
    cosine = metric.get("cosine")
    required = (
        metric.get("normalized_rmse"),
        metric.get("reference_rms"),
        metric.get("candidate_rms"),
        cosine,
    )
    return bool(
        metric.get("shape_match")
        and all(value is not None and np.isfinite(value) for value in required)
        and metric.get("normalized_rmse", float("inf"))
        <= threshold["max_normalized_rmse"]
        and cosine is not None
        and cosine >= threshold["min_cosine"]
    )


def _distribution_summary(values: list[float]) -> dict[str, float | bool | None]:
    if not values:
        raise ValidationError("Cannot summarize an empty timing sample")
    ordered = sorted(float(value) for value in values)
    if not all(np.isfinite(value) for value in ordered):
        return {
            "finite": False,
            "median_ms": None,
            "mean_ms": None,
            "min_ms": None,
            "p95_ms": None,
        }
    p95_index = min(len(ordered) - 1, int(np.ceil(0.95 * len(ordered))) - 1)
    return {
        "finite": True,
        "median_ms": float(statistics.median(ordered)),
        "mean_ms": float(statistics.fmean(ordered)),
        "min_ms": float(min(ordered)),
        "p95_ms": float(ordered[p95_index]),
    }


def _prompt_id(index: int) -> str:
    return f"prompt_{index:02d}"


def _case_id(prompt_index: int, layer: int) -> str:
    return f"{_prompt_id(prompt_index)}_layer_{layer:02d}"


def _atomic_write_json_no_overwrite(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ValidationError(f"Refusing to overwrite existing receipt: {path}")
    payload = (json_dumps(value, pretty=True) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            raise ValidationError(
                f"Refusing to overwrite existing receipt: {path}"
            ) from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_worker_bundle(output_dir: Path, metadata: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "phase.json").write_text(
        json_dumps(metadata, pretty=True) + "\n", encoding="utf-8"
    )


def _read_worker_bundle(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "phase.json"
    if not path.is_file():
        raise ValidationError(f"Worker did not produce phase metadata: {output_dir}")
    return json.loads(path.read_text(encoding="utf-8"))


def _backend_for_worker(backend_name: str, dtype: str):
    common = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "dtype": dtype,
        "local_files_only": True,
        "trust_remote_code": False,
        "add_special_tokens": ADD_SPECIAL_TOKENS,
    }
    if backend_name == "transformers_mps":
        from glyphprobe.backends.transformers_backend import TransformersBackend

        return TransformersBackend(
            BackendConfig(kind="transformers", device="mps", **common)
        )
    if backend_name == "mlx_gpu":
        from glyphprobe.backends.mlx_backend import MLXBackend

        backend = MLXBackend(BackendConfig(kind="mlx", device="gpu", **common))
        backend._parity_probe_mode = True
        return backend
    raise ValidationError(f"Unsupported worker backend: {backend_name}")


def _validate_loaded_backend(backend: Any, backend_name: str) -> None:
    failures: list[str] = []
    if backend.num_layers != EXPECTED_NUM_LAYERS:
        failures.append(f"layers={backend.num_layers!r}")
    if backend.model_dim != EXPECTED_MODEL_WIDTH:
        failures.append(f"width={backend.model_dim!r}")
    if backend.block_path != "model.layers":
        failures.append(f"block_path={backend.block_path!r}")
    if failures:
        raise ValidationError(
            f"Loaded {backend_name} model does not match the sealed architecture: "
            + ", ".join(failures)
        )


def _parameter_dtype_audit(
    backend: Any, backend_name: str, dtype: str
) -> dict[str, Any]:
    if backend_name == "transformers_mps":
        values = list(backend.model.parameters())
    elif backend_name == "mlx_gpu":
        from mlx.utils import tree_flatten

        values = [
            value
            for _, value in tree_flatten(backend.model.parameters())
            if hasattr(value, "dtype") and hasattr(value, "shape")
        ]
    else:
        raise ValidationError(f"Unsupported backend for dtype audit: {backend_name}")
    counts: dict[str, int] = {}
    for value in values:
        element_count = int(np.prod(tuple(value.shape), dtype=np.int64))
        resolved = str(value.dtype)
        counts[resolved] = counts.get(resolved, 0) + element_count
    expected = "float16" if dtype == "float16" else "float32"
    total = sum(counts.values())
    return {
        "requested_runtime_dtype": dtype,
        "parameter_element_count": total,
        "expected_parameter_element_count": EXPECTED_PARAMETER_COUNT,
        "parameter_dtype_element_counts": counts,
        "all_parameter_dtypes_match_requested": bool(counts)
        and all(expected in resolved.lower() for resolved in counts),
        "parameter_count_matches_expected": total == EXPECTED_PARAMETER_COUNT,
        "non_parameter_buffers_claim": (
            "Not audited as candidate dtype; precision-sensitive auxiliary buffers "
            "such as RoPE may use an implementation-defined dtype."
        ),
    }


def _runtime_dtype_audit(
    model_receipt: dict[str, Any], parameter_audit: dict[str, Any], dtype: str
) -> dict[str, Any]:
    loader = model_receipt.get("loader_metadata", {})
    resolved = model_receipt.get("resolved_dtype", loader.get("resolved_dtype"))
    normalized = str(resolved).lower()
    expected = "float16" if dtype == "float16" else "float32"
    return {
        "requested_runtime_dtype": dtype,
        "resolved_runtime_dtype": str(resolved),
        "resolved_matches_requested": expected in normalized,
        "parameter_audit": parameter_audit,
        "artifact_storage_dtype": "bfloat16",
        "artifact_manifest": model_receipt.get("model_artifact"),
    }


def _plan_for_baselines(
    baselines: dict[str, np.ndarray],
) -> dict[str, dict[str, Any]]:
    plan: dict[str, dict[str, Any]] = {}
    for case_id, activation in baselines.items():
        reference_rms = _rms(activation)
        vector = _intervention_vector(RELATIVE_INTERVENTION_RMS * reference_rms)
        plan[case_id] = {
            "reference_activation_rms": reference_rms,
            "target_vector_rms": _rms(vector),
            "vector_sha256": _array_sha256(vector),
            "vector_float32": vector.tolist(),
        }
    return plan


def _load_plan(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {
        _case_id(prompt_index, layer)
        for prompt_index in range(len(PROMPTS))
        for layer in LAYERS
    }:
        raise ValidationError("Intervention plan case set drifted")
    for case_id, row in payload.items():
        vector = np.asarray(row.get("vector_float32"), dtype=np.float32)
        if vector.shape != (EXPECTED_MODEL_WIDTH,) or not np.all(np.isfinite(vector)):
            raise ValidationError(f"Invalid intervention vector for {case_id}")
        if _array_sha256(vector) != row.get("vector_sha256"):
            raise ValidationError(f"Intervention vector hash drifted for {case_id}")
    return payload


def _timed_forward(
    backend: Any, prompt: str, intervention: Intervention, layer: int
) -> float:
    started = time.perf_counter()
    backend.forward(
        prompt, capture_layers=[layer], site=SITE, intervention=intervention
    )
    return (time.perf_counter() - started) * 1000.0


def _worker_phase(
    backend_name: str,
    dtype: str,
    output_dir: Path,
    intervention_plan_path: Path | None,
) -> None:
    is_transformers = backend_name == "transformers_mps"
    if is_transformers != (intervention_plan_path is None):
        raise ValidationError("Transformers derives the plan and MLX consumes it")
    plan = (
        None if intervention_plan_path is None else _load_plan(intervention_plan_path)
    )
    backend = _backend_for_worker(backend_name, dtype)
    prompt_records: list[dict[str, Any]] = []
    case_records: list[dict[str, Any]] = []
    benchmark_cells: list[dict[str, Any]] = []
    baselines: dict[str, np.ndarray] = {}
    baseline_logits: dict[str, np.ndarray] = {}
    load_started = time.perf_counter()
    try:
        backend.load()
        load_ms = (time.perf_counter() - load_started) * 1000.0
        _validate_loaded_backend(backend, backend_name)
        model_receipt = backend.model_receipt()
        parameter_audit = _parameter_dtype_audit(backend, backend_name, dtype)
        runtime_dtype = _runtime_dtype_audit(model_receipt, parameter_audit, dtype)
        artifact = runtime_dtype["artifact_manifest"]
        expected_artifact = {
            "file_count": EXPECTED_ARTIFACT_FILE_COUNT,
            "total_bytes": EXPECTED_ARTIFACT_TOTAL_BYTES,
            "manifest_sha256": EXPECTED_ARTIFACT_MANIFEST_SHA256,
        }
        if (
            not isinstance(artifact, dict)
            or {key: artifact.get(key) for key in expected_artifact}
            != expected_artifact
        ):
            raise ValidationError(
                "Loaded model artifact does not match sealed BF16 manifest"
            )

        for prompt_index, prompt in enumerate(PROMPTS):
            baseline = backend.forward(prompt, capture_layers=list(LAYERS), site=SITE)
            repeat = backend.forward(prompt, capture_layers=list(LAYERS), site=SITE)
            if baseline.logits.shape != (EXPECTED_VOCAB_SIZE,):
                raise ValidationError(f"{backend_name} returned wrong vocab shape")
            prompt_records.append(
                {
                    "id": _prompt_id(prompt_index),
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "prompt_utf8_hex": prompt.encode("utf-8").hex(),
                    "prompt_utf8_bytes": len(prompt.encode("utf-8")),
                    "token_ids": baseline.token_ids,
                    "token_count": len(baseline.token_ids),
                    "last_nonpad_position": len(baseline.token_ids) - 1,
                    "determinism": {
                        "token_ids_match": baseline.token_ids == repeat.token_ids,
                        "argmax_match": int(np.argmax(baseline.logits))
                        == int(np.argmax(repeat.logits)),
                        "max_abs_logit_delta": float(
                            np.max(np.abs(repeat.logits - baseline.logits))
                        ),
                    },
                }
            )
            for layer in LAYERS:
                case_id = _case_id(prompt_index, layer)
                baselines[case_id] = baseline.activations[layer]
                baseline_logits[case_id] = baseline.logits

        if plan is None:
            plan = _plan_for_baselines(baselines)

        for prompt_index, prompt in enumerate(PROMPTS):
            for layer in LAYERS:
                case_id = _case_id(prompt_index, layer)
                row = plan[case_id]
                vector = np.asarray(row["vector_float32"], dtype=np.float32)
                zero = Intervention(
                    layer=layer,
                    vector=np.zeros(EXPECTED_MODEL_WIDTH, dtype=np.float32),
                    site=SITE,
                    position="last_nonpad",
                    label="numeric-screen-zero-vector",
                )
                changed = Intervention(
                    layer=layer,
                    vector=vector,
                    site=SITE,
                    position="last_nonpad",
                    label="numeric-screen-fixed-relative-rms-vector",
                )
                baseline_activation = baselines[case_id]
                zero_result = backend.forward(
                    prompt, capture_layers=[layer], site=SITE, intervention=zero
                )
                changed_result = backend.forward(
                    prompt, capture_layers=[layer], site=SITE, intervention=changed
                )
                case_records.append(
                    {
                        "id": case_id,
                        "prompt_id": _prompt_id(prompt_index),
                        "layer": layer,
                        "vector_sha256": row["vector_sha256"],
                        "target_vector_rms": row["target_vector_rms"],
                        "zero_hook": {
                            "max_logit_delta": float(
                                np.max(
                                    np.abs(
                                        zero_result.logits - baseline_logits[case_id]
                                    )
                                )
                            ),
                            "max_activation_delta": float(
                                np.max(
                                    np.abs(
                                        zero_result.activations[layer]
                                        - baseline_activation
                                    )
                                )
                            ),
                        },
                        "intervention_fidelity": _comparison(
                            vector,
                            changed_result.activations[layer] - baseline_activation,
                        ),
                    }
                )

                for _ in range(WARMUPS):
                    _timed_forward(backend, prompt, changed, layer)
                samples = [
                    _timed_forward(backend, prompt, changed, layer)
                    for _ in range(REPEATS)
                ]
                benchmark_cells.append(
                    {
                        "id": case_id,
                        "prompt_id": _prompt_id(prompt_index),
                        "layer": layer,
                        "samples_ms": samples,
                        "summary": _distribution_summary(samples),
                    }
                )

        metadata: dict[str, Any] = {
            "schema_version": 1,
            "backend": backend_name,
            "runtime_dtype": dtype,
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "site": SITE,
            "layers": list(LAYERS),
            "add_special_tokens": ADD_SPECIAL_TOKENS,
            "load_time_ms": load_ms,
            "model_receipt": model_receipt,
            "model_identity_sha256": stable_model_identity(model_receipt)["sha256"],
            "runtime_dtype_audit": runtime_dtype,
            "implementation": implementation_receipt(),
            "prompts": prompt_records,
            "cases": case_records,
            "benchmark": {
                "warmups_per_cell": WARMUPS,
                "repeats_per_cell": REPEATS,
                "cells": benchmark_cells,
            },
        }
        if is_transformers:
            metadata["intervention_plan"] = plan
        _write_worker_bundle(output_dir, metadata)
    finally:
        backend.close()


def _worker_command(
    backend_name: str, dtype: str, output_dir: Path, plan_path: Path | None
) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_worker-backend",
        backend_name,
        "--_worker-dtype",
        dtype,
        "--_worker-output-dir",
        str(output_dir),
    ]
    if plan_path is not None:
        command.extend(["--_worker-intervention-plan", str(plan_path)])
    return command


def _run_worker_subprocess(
    backend_name: str, dtype: str, output_dir: Path, plan_path: Path | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    environment = os.environ.copy()
    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"
    started = time.perf_counter()
    completed = subprocess.run(
        _worker_command(backend_name, dtype, output_dir, plan_path),
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    wall_time_ms = (time.perf_counter() - started) * 1000.0
    lifecycle = {
        "backend": backend_name,
        "runtime_dtype": dtype,
        "launch_mode": "isolated_completed_subprocess",
        "returncode": completed.returncode,
        "wall_time_ms": wall_time_ms,
    }
    if completed.returncode != 0:
        raise WorkerFailure(
            f"{backend_name}/{dtype} worker failed with exit code {completed.returncode}: "
            + completed.stderr[-4000:].strip(),
            lifecycle,
        )
    try:
        phase = _read_worker_bundle(output_dir)
        if phase.get("backend") != backend_name or phase.get("runtime_dtype") != dtype:
            raise ValidationError(
                "Worker returned a mismatched backend or runtime dtype"
            )
    except ValidationError as exc:
        raise WorkerFailure(str(exc), lifecycle) from exc
    return phase, lifecycle


def _indexed(
    rows: list[dict[str, Any]], label: str, expected: int
) -> dict[str, dict[str, Any]]:
    mapped = {row["id"]: row for row in rows}
    if len(rows) != expected or len(mapped) != expected:
        raise ValidationError(f"Incomplete or duplicate {label}")
    return mapped


def _candidate_summary(
    dtype: str,
    torch_phase: dict[str, Any],
    mlx_phase: dict[str, Any],
    lifecycle: list[dict[str, Any]],
) -> dict[str, Any]:
    expected_cases = len(PROMPTS) * len(LAYERS)
    torch_prompts = _indexed(
        torch_phase["prompts"], "Transformers prompts", len(PROMPTS)
    )
    mlx_prompts = _indexed(mlx_phase["prompts"], "MLX prompts", len(PROMPTS))
    torch_cases = _indexed(torch_phase["cases"], "Transformers cases", expected_cases)
    mlx_cases = _indexed(mlx_phase["cases"], "MLX cases", expected_cases)
    torch_cells = _indexed(
        torch_phase["benchmark"]["cells"],
        "Transformers benchmark cells",
        expected_cases,
    )
    mlx_cells = _indexed(
        mlx_phase["benchmark"]["cells"], "MLX benchmark cells", expected_cases
    )
    if set(torch_prompts) != set(mlx_prompts) or set(torch_cases) != set(mlx_cases):
        raise ValidationError("Backend prompt or case sets differ")
    if torch_phase["implementation"] != mlx_phase["implementation"]:
        raise ValidationError("Implementation changed between isolated workers")

    prompt_checks: list[dict[str, Any]] = []
    for prompt_id in sorted(torch_prompts):
        torch_row = torch_prompts[prompt_id]
        mlx_row = mlx_prompts[prompt_id]
        identity_fields = (
            "prompt_sha256",
            "prompt_utf8_hex",
            "prompt_utf8_bytes",
            "last_nonpad_position",
        )
        torch_identity = {field: torch_row.get(field) for field in identity_fields}
        mlx_identity = {field: mlx_row.get(field) for field in identity_fields}
        identity_match = torch_identity == mlx_identity and all(
            value is not None for value in torch_identity.values()
        )
        passed = bool(
            identity_match
            and torch_row["token_ids"] == mlx_row["token_ids"]
            and torch_row["determinism"]["token_ids_match"]
            and mlx_row["determinism"]["token_ids_match"]
            and torch_row["determinism"]["argmax_match"]
            and mlx_row["determinism"]["argmax_match"]
        )
        prompt_checks.append(
            {
                "id": prompt_id,
                "pass": passed,
                "transformers_mps": torch_row["determinism"],
                "mlx_gpu": mlx_row["determinism"],
                "prompt_identity": {
                    "match": identity_match,
                    "transformers_mps": torch_identity,
                    "mlx_gpu": mlx_identity,
                },
                "cross_backend_token_ids_match": torch_row["token_ids"]
                == mlx_row["token_ids"],
            }
        )

    case_checks: list[dict[str, Any]] = []
    for case_id in sorted(torch_cases):
        torch_case = torch_cases[case_id]
        mlx_case = mlx_cases[case_id]
        if torch_case["vector_sha256"] != mlx_case["vector_sha256"]:
            raise ValidationError(f"Shared intervention vector drifted: {case_id}")
        zero_values = [
            torch_case["zero_hook"]["max_logit_delta"],
            torch_case["zero_hook"]["max_activation_delta"],
            mlx_case["zero_hook"]["max_logit_delta"],
            mlx_case["zero_hook"]["max_activation_delta"],
        ]
        zero_pass = all(
            value <= THRESHOLDS["zero_hook_max_abs"] for value in zero_values
        )
        torch_fidelity_pass = _metric_pass(
            torch_case["intervention_fidelity"], THRESHOLDS["intervention_fidelity"]
        )
        mlx_fidelity_pass = _metric_pass(
            mlx_case["intervention_fidelity"], THRESHOLDS["intervention_fidelity"]
        )
        case_checks.append(
            {
                "id": case_id,
                "zero_hook_pass": zero_pass,
                "transformers_intervention_fidelity_pass": torch_fidelity_pass,
                "mlx_intervention_fidelity_pass": mlx_fidelity_pass,
                "zero_hook": {
                    "transformers_mps": torch_case["zero_hook"],
                    "mlx_gpu": mlx_case["zero_hook"],
                },
                "intervention_fidelity": {
                    "transformers_mps": torch_case["intervention_fidelity"],
                    "mlx_gpu": mlx_case["intervention_fidelity"],
                },
            }
        )

    torch_samples = [
        value for row in torch_cells.values() for value in row["samples_ms"]
    ]
    mlx_samples = [value for row in mlx_cells.values() for value in row["samples_ms"]]
    if (
        len(torch_samples) != expected_cases * REPEATS
        or len(mlx_samples) != expected_cases * REPEATS
    ):
        raise ValidationError("Benchmark repeat count drifted")
    torch_summary = _distribution_summary(torch_samples)
    mlx_summary = _distribution_summary(mlx_samples)
    finite_samples = bool(torch_summary["finite"] and mlx_summary["finite"])
    speed_fraction = (
        mlx_summary["median_ms"] / torch_summary["median_ms"]
        if finite_samples
        else None
    )
    speed_pass = bool(
        finite_samples
        and speed_fraction is not None
        and speed_fraction
        <= THRESHOLDS["speed"]["mlx_max_fraction_of_transformers_median"]
    )
    finite_zero_hook = all(
        np.isfinite(value)
        for row in case_checks
        for backend_values in row["zero_hook"].values()
        for value in backend_values.values()
    )
    finite_fidelity = all(
        all(
            value is not None and np.isfinite(value)
            for value in (
                metric.get("normalized_rmse"),
                metric.get("reference_rms"),
                metric.get("candidate_rms"),
                metric.get("cosine"),
            )
        )
        for row in case_checks
        for metric in row["intervention_fidelity"].values()
    )
    dtype_identity_pass = bool(
        torch_phase["runtime_dtype_audit"]["resolved_matches_requested"]
        and mlx_phase["runtime_dtype_audit"]["resolved_matches_requested"]
        and torch_phase["runtime_dtype_audit"]["parameter_audit"][
            "all_parameter_dtypes_match_requested"
        ]
        and mlx_phase["runtime_dtype_audit"]["parameter_audit"][
            "all_parameter_dtypes_match_requested"
        ]
        and torch_phase["runtime_dtype_audit"]["parameter_audit"][
            "parameter_count_matches_expected"
        ]
        and mlx_phase["runtime_dtype_audit"]["parameter_audit"][
            "parameter_count_matches_expected"
        ]
    )
    gates = {
        "tokens_and_determinism": all(row["pass"] for row in prompt_checks),
        "zero_hook": finite_zero_hook
        and all(row["zero_hook_pass"] for row in case_checks),
        "intervention_fidelity": all(
            row["transformers_intervention_fidelity_pass"]
            and row["mlx_intervention_fidelity_pass"]
            for row in case_checks
        )
        and finite_fidelity,
        "runtime_dtype_identity": dtype_identity_pass,
        "speed": speed_pass,
    }
    return {
        "runtime_dtype": dtype,
        "artifact_storage_dtype": "bfloat16",
        "eligible": all(gates.values()),
        "gates": gates,
        "prompt_checks": prompt_checks,
        "case_checks": case_checks,
        "benchmark": {
            "method": (
                "Non-interleaved isolated-process end-to-end backend.forward wall "
                "time; each call includes tokenization, capture, intervention, device "
                "evaluation, and NumPy transfer."
            ),
            "transformers_mps": torch_summary,
            "mlx_gpu": mlx_summary,
            "mlx_fraction_of_transformers_median": speed_fraction,
            "finite_samples": finite_samples,
            "cells": [
                {
                    "id": case_id,
                    "transformers_mps": {
                        "samples_ms": torch_cells[case_id]["samples_ms"],
                        "summary": _distribution_summary(
                            torch_cells[case_id]["samples_ms"]
                        ),
                    },
                    "mlx_gpu": {
                        "samples_ms": mlx_cells[case_id]["samples_ms"],
                        "summary": _distribution_summary(
                            mlx_cells[case_id]["samples_ms"]
                        ),
                    },
                }
                for case_id in sorted(torch_cells)
            ],
            "speed_gate": {
                "criterion": "MLX aggregate median <= 0.95 times Transformers/MPS aggregate median",
                "pass": speed_pass,
            },
        },
        "runtime_dtype_audit": {
            "transformers_mps": torch_phase["runtime_dtype_audit"],
            "mlx_gpu": mlx_phase["runtime_dtype_audit"],
        },
        "model_artifact": torch_phase["runtime_dtype_audit"]["artifact_manifest"],
        "transformers_model_identity_sha256": torch_phase["model_identity_sha256"],
        "mlx_model_identity_sha256": mlx_phase["model_identity_sha256"],
        "implementation": torch_phase["implementation"],
        "load_times": {
            "transformers_mps_ms": torch_phase["load_time_ms"],
            "mlx_gpu_ms": mlx_phase["load_time_ms"],
        },
        "process_lifecycle": lifecycle,
    }


def _select_candidate(candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        candidate
        for candidate in NUMERIC_CANDIDATES
        if candidates[candidate]["eligible"]
    ]
    if not eligible:
        return {
            "selected_runtime_dtype": None,
            "decision": "no_go_no_eligible_numeric_candidate",
            "reason": "No candidate passed every prespecified engineering gate",
        }
    if len(eligible) == 1:
        return {
            "selected_runtime_dtype": eligible[0],
            "decision": "single_eligible_candidate",
            "reason": "Only one candidate passed every prespecified engineering gate",
        }
    fp16_latency = candidates["float16"]["benchmark"]["mlx_gpu"]["median_ms"]
    fp32_latency = candidates["float32"]["benchmark"]["mlx_gpu"]["median_ms"]
    relative_difference = abs(fp16_latency - fp32_latency) / min(
        fp16_latency, fp32_latency
    )
    if relative_difference <= THRESHOLDS["selection_tie_relative_latency"]:
        selected = "float32"
        decision = "both_eligible_tie_select_fp32"
    else:
        selected = "float16" if fp16_latency < fp32_latency else "float32"
        decision = "both_eligible_select_lower_mlx_median"
    return {
        "selected_runtime_dtype": selected,
        "decision": decision,
        "reason": "Both candidates passed every engineering gate",
        "fp16_mlx_median_ms": fp16_latency,
        "fp32_mlx_median_ms": fp32_latency,
        "relative_latency_difference": relative_difference,
    }


def _failed_candidate(
    dtype: str, error: ValidationError, lifecycle: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "runtime_dtype": dtype,
        "artifact_storage_dtype": "bfloat16",
        "eligible": False,
        "gates": {
            "tokens_and_determinism": False,
            "zero_hook": False,
            "intervention_fidelity": False,
            "runtime_dtype_identity": False,
            "speed": False,
        },
        "failure": {
            "kind": "engineering_worker_or_contract_failure",
            "message": str(error),
        },
        "process_lifecycle": lifecycle,
    }


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in (
        "glyphprobe",
        "numpy",
        "torch",
        "transformers",
        "mlx",
        "mlx-lm",
    ):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def run_screen(output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_path = output_path.resolve()
    if output_path.exists():
        raise ValidationError(f"Refusing to overwrite existing receipt: {output_path}")
    candidates: dict[str, dict[str, Any]] = {}
    lifecycle: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(
        prefix="glyphprobe-llama32-numeric-screen-"
    ) as temporary:
        temporary_root = Path(temporary)
        for dtype in NUMERIC_CANDIDATES:
            candidate_lifecycle: list[dict[str, Any]] = []
            try:
                torch_phase, torch_lifecycle = _run_worker_subprocess(
                    "transformers_mps",
                    dtype,
                    temporary_root / f"{dtype}-transformers",
                )
                candidate_lifecycle.append(torch_lifecycle)
                plan = torch_phase.get("intervention_plan")
                if not isinstance(plan, dict):
                    raise ValidationError(
                        "Transformers worker did not produce an intervention plan"
                    )
                plan_path = temporary_root / f"{dtype}-intervention-plan.json"
                plan_path.write_text(
                    json_dumps(plan, pretty=True) + "\n", encoding="utf-8"
                )
                gc.collect()
                mlx_phase, mlx_lifecycle = _run_worker_subprocess(
                    "mlx_gpu", dtype, temporary_root / f"{dtype}-mlx", plan_path
                )
                candidate_lifecycle.append(mlx_lifecycle)
                lifecycle.extend(candidate_lifecycle)
                candidates[dtype] = _candidate_summary(
                    dtype, torch_phase, mlx_phase, candidate_lifecycle
                )
            except ValidationError as exc:
                if isinstance(exc, WorkerFailure):
                    candidate_lifecycle.append(exc.lifecycle)
                lifecycle.extend(candidate_lifecycle)
                candidates[dtype] = _failed_candidate(dtype, exc, candidate_lifecycle)
    selection = _select_candidate(candidates)
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "validator_version": VALIDATOR_VERSION,
        "status": "engineering_screen_complete",
        "claim_boundary": CLAIM_BOUNDARY,
        "scientific_result": False,
        "selection_is_not_scientific_authorization": True,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "artifact_storage_dtype": "bfloat16",
        "site": SITE,
        "capture_layers": list(LAYERS),
        "intervention_layers": list(LAYERS),
        "data_scope": {
            "study_target_banks_accessed": False,
            "confirmatory_or_causal_outcomes_accessed": False,
        },
        "validation_config": {
            "payload": VALIDATION_CONFIG,
            "sha256": VALIDATION_CONFIG_SHA256,
        },
        "validator_sha256": _sha256(Path(__file__).resolve()),
        "implementation": implementation_receipt(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "dependency_versions": _package_versions(),
            "worker_network_mode": "Hugging Face and Transformers offline",
        },
        "process_lifecycle": {
            "mode": "strictly sequential isolated subprocesses",
            "order": [
                "float16/transformers_mps",
                "float16/mlx_gpu",
                "float32/transformers_mps",
                "float32/mlx_gpu",
            ],
            "simultaneous_model_residency": False,
            "phases": lifecycle,
        },
        "candidates": candidates,
        "selection": selection,
        "decision": (
            "A selected candidate requires a separately frozen full parity validator "
            "before any scientific grid; no selection is an MLX no-go."
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--_worker-backend", choices=("transformers_mps", "mlx_gpu"))
    parser.add_argument("--_worker-dtype", choices=NUMERIC_CANDIDATES)
    parser.add_argument("--_worker-output-dir", type=Path)
    parser.add_argument("--_worker-intervention-plan", type=Path)
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if args._worker_backend is not None:
        if args._worker_dtype is None or args._worker_output_dir is None:
            parser.error("internal worker mode requires dtype and output directory")
        _worker_phase(
            args._worker_backend,
            args._worker_dtype,
            args._worker_output_dir,
            args._worker_intervention_plan,
        )
        return 0
    if any(
        value is not None
        for value in (
            args._worker_dtype,
            args._worker_output_dir,
            args._worker_intervention_plan,
        )
    ):
        parser.error("internal worker arguments require --_worker-backend")
    output_path = args.output.resolve()
    try:
        receipt = run_screen(output_path)
        _atomic_write_json_no_overwrite(output_path, receipt)
    except ValidationError as exc:
        parser.exit(2, f"validation error: {exc}\n")
    print(f"status={receipt['status']}")
    print(f"selection={receipt['selection']['selected_runtime_dtype']}")
    print(f"receipt={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
