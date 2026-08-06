#!/usr/bin/env python3
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
PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mlx-engineering-validation-v2"
VALIDATOR_VERSION = 2
SUPERSEDES_PROTOCOL_ID = (
    "glyphprobe-e2-llama32-3b-mlx-engineering-validation-v1"
)
TECHNICAL_CHANGE = "MLX BF16 arrays cast to mx.float32 before NumPy export"
DTYPE = "bfloat16"
SITE = "resid_post"
LAYERS = (5, 11)
ADD_SPECIAL_TOKENS = False
EXPECTED_NUM_LAYERS = 28
EXPECTED_MODEL_WIDTH = 3072
EXPECTED_VOCAB_SIZE = 128_256
EXPECTED_ARTIFACT_FILE_COUNT = 9
EXPECTED_ARTIFACT_TOTAL_BYTES = 6_434_705_789
EXPECTED_ARTIFACT_MANIFEST_SHA256 = (
    "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
)
RELATIVE_INTERVENTION_RMS = 0.05
WARMUPS = 2
REPEATS = 10
DEFAULT_OUTPUT = Path(
    "validation/mlx_llama32_3b_bf16_parity_v2/receipt.json"
)
CLAIM_BOUNDARY = (
    "pinned-llama32-3b-bf16-resid-post-backend-parity-and-speed-only"
)

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

# These BF16 thresholds are part of the validator definition. They must not be tuned
# in response to this model cell's outputs.
THRESHOLDS: dict[str, Any] = {
    "baseline": {"max_normalized_rmse": 0.02, "min_cosine": 0.999},
    "changed": {"max_normalized_rmse": 0.02, "min_cosine": 0.999},
    "logit_delta": {
        "max_normalized_rmse": 0.05,
        "min_cosine": 0.99,
        "rms_ratio": [0.95, 1.05],
    },
    "activation_delta": {
        "max_normalized_rmse": 0.02,
        "min_cosine": 0.999,
        "rms_ratio": [0.98, 1.02],
    },
    "intervention_fidelity": {
        "max_normalized_rmse": 0.01,
        "min_cosine": 0.999,
    },
    "zero_hook_max_abs": 1e-7,
    "speed": {"mlx_max_fraction_of_transformers_median": 0.95},
    "exact_token_ids": True,
    "exact_argmax": True,
}

VALIDATION_CONFIG: dict[str, Any] = {
    "protocol_id": PROTOCOL_ID,
    "validator_version": VALIDATOR_VERSION,
    "supersedes_protocol_id": SUPERSEDES_PROTOCOL_ID,
    "technical_change": TECHNICAL_CHANGE,
    "model": MODEL_ID,
    "revision": MODEL_REVISION,
    "dtype": DTYPE,
    "site": SITE,
    "layers": list(LAYERS),
    "add_special_tokens": ADD_SPECIAL_TOKENS,
    "expected_architecture": {
        "num_layers": EXPECTED_NUM_LAYERS,
        "model_width": EXPECTED_MODEL_WIDTH,
        "vocab_size": EXPECTED_VOCAB_SIZE,
    },
    "expected_model_artifact": {
        "file_count": EXPECTED_ARTIFACT_FILE_COUNT,
        "total_bytes": EXPECTED_ARTIFACT_TOTAL_BYTES,
        "manifest_sha256": EXPECTED_ARTIFACT_MANIFEST_SHA256,
    },
    "prompts": list(PROMPTS),
    "relative_intervention_rms": RELATIVE_INTERVENTION_RMS,
    "direction": (
        "float32 linspace(-0.05, 0.05, 3072), centered, RMS-normalized"
    ),
    "warmups_per_cell": WARMUPS,
    "repeats_per_cell": REPEATS,
    "thresholds": THRESHOLDS,
}
VALIDATION_CONFIG_SHA256 = hashlib.sha256(
    json_dumps(VALIDATION_CONFIG, pretty=False).encode("utf-8")
).hexdigest()


class ValidationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(value: np.ndarray) -> str:
    array = np.ascontiguousarray(np.asarray(value, dtype=np.float32))
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def _rms(value: np.ndarray) -> float:
    array = np.asarray(value, dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(array))))


def _fixed_unit_direction(width: int = EXPECTED_MODEL_WIDTH) -> np.ndarray:
    raw = np.linspace(-0.05, 0.05, width, dtype=np.float32)
    raw = raw - np.mean(raw, dtype=np.float32)
    return np.asarray(raw / _rms(raw), dtype=np.float32)


def _intervention_vector(target_rms: float) -> np.ndarray:
    return np.asarray(_fixed_unit_direction() * target_rms, dtype=np.float32)


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


def _metric_pass(metric: dict[str, Any], threshold: dict[str, Any]) -> bool:
    if not metric.get("shape_match"):
        return False
    cosine = metric.get("cosine")
    passed = (
        metric.get("normalized_rmse", float("inf"))
        <= threshold["max_normalized_rmse"]
        and cosine is not None
        and cosine >= threshold["min_cosine"]
    )
    ratio = threshold.get("rms_ratio")
    if ratio is not None:
        passed = passed and ratio[0] <= metric.get("rms_ratio", 0.0) <= ratio[1]
    return bool(passed)


def _distribution_summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValidationError("Cannot summarize an empty timing sample")
    ordered = sorted(float(value) for value in values)
    p95_index = min(len(ordered) - 1, int(np.ceil(0.95 * len(ordered))) - 1)
    return {
        "median_ms": float(statistics.median(ordered)),
        "mean_ms": float(statistics.fmean(ordered)),
        "min_ms": float(min(ordered)),
        "p95_ms": float(ordered[p95_index]),
    }


def _prompt_id(index: int) -> str:
    return f"prompt_{index:02d}"


def _case_id(prompt_index: int, layer: int) -> str:
    return f"{_prompt_id(prompt_index)}_layer_{layer:02d}"


def _array_key(prompt_index: int, layer: int | None, value: str) -> str:
    prefix = _prompt_id(prompt_index)
    if layer is not None:
        prefix = f"{prefix}_layer_{layer:02d}"
    return f"{prefix}_{value}"


def _atomic_write_json_no_overwrite(path: Path, value: Any) -> None:
    """Publish complete JSON atomically, failing if the destination already exists."""
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
            raise ValidationError(f"Refusing to overwrite existing receipt: {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary_path.unlink(missing_ok=True)


def _write_worker_bundle(
    output_dir: Path,
    metadata: dict[str, Any],
    arrays: dict[str, np.ndarray],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    arrays_path = output_dir / "arrays.npz"
    np.savez_compressed(arrays_path, **arrays)
    metadata = dict(metadata)
    metadata["array_keys"] = sorted(arrays)
    metadata["arrays_sha256"] = _sha256(arrays_path)
    (output_dir / "phase.json").write_text(
        json_dumps(metadata, pretty=True) + "\n", encoding="utf-8"
    )


def _read_worker_bundle(output_dir: Path) -> dict[str, Any]:
    metadata_path = output_dir / "phase.json"
    arrays_path = output_dir / "arrays.npz"
    if not metadata_path.is_file() or not arrays_path.is_file():
        raise ValidationError(f"Worker did not produce a complete bundle: {output_dir}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("arrays_sha256") != _sha256(arrays_path):
        raise ValidationError(f"Worker array exchange hash mismatch: {output_dir}")
    with np.load(arrays_path, allow_pickle=False) as archive:
        actual_keys = sorted(archive.files)
        if actual_keys != metadata.get("array_keys"):
            raise ValidationError(f"Worker array exchange key mismatch: {output_dir}")
        arrays = {key: np.array(archive[key], copy=True) for key in actual_keys}
    metadata["arrays"] = arrays
    return metadata


def _backend_for_worker(backend_name: str):
    common = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "dtype": DTYPE,
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
    if backend_name == "transformers_mps" and backend.block_path != "model.layers":
        failures.append(f"block_path={backend.block_path!r}")
    if backend_name == "mlx_gpu" and backend.block_path != "model.layers":
        failures.append(f"block_path={backend.block_path!r}")
    if failures:
        raise ValidationError(
            "Loaded model does not match the frozen Llama 3.2 3B architecture: "
            + ", ".join(failures)
        )


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
        site=SITE,
        intervention=intervention,
    )
    return (time.perf_counter() - started) * 1000.0


def _load_intervention_plan(path: Path) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "width": EXPECTED_MODEL_WIDTH,
        "layers": list(LAYERS),
        "relative_rms": RELATIVE_INTERVENTION_RMS,
        "direction": "float32 linspace(-0.05, 0.05, 3072), centered, RMS-normalized",
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise ValidationError(f"Intervention plan field {key!r} drifted")
    expected_cases = {
        _case_id(prompt_index, layer)
        for prompt_index in range(len(PROMPTS))
        for layer in LAYERS
    }
    if set(plan.get("cases", {})) != expected_cases:
        raise ValidationError("Intervention plan case set drifted")
    for case_id, row in plan["cases"].items():
        vector = np.asarray(row.get("vector_float32"), dtype=np.float32)
        if vector.shape != (EXPECTED_MODEL_WIDTH,) or not np.all(np.isfinite(vector)):
            raise ValidationError(f"Intervention plan vector is invalid for {case_id}")
        if _array_sha256(vector) != row.get("vector_sha256"):
            raise ValidationError(f"Intervention plan vector hash drifted for {case_id}")
        if not np.isclose(
            _rms(vector), float(row.get("target_vector_rms", float("nan"))), rtol=2e-7
        ):
            raise ValidationError(f"Intervention plan vector RMS drifted for {case_id}")
    return plan


def _worker_phase(
    backend_name: str,
    output_dir: Path,
    intervention_plan_path: Path | None,
) -> None:
    if backend_name == "transformers_mps" and intervention_plan_path is not None:
        raise ValidationError("Transformers worker derives, rather than consumes, the plan")
    if backend_name == "mlx_gpu" and intervention_plan_path is None:
        raise ValidationError("MLX worker requires the Transformers-derived plan")

    plan = (
        _load_intervention_plan(intervention_plan_path)
        if intervention_plan_path is not None
        else None
    )
    backend = _backend_for_worker(backend_name)
    arrays: dict[str, np.ndarray] = {}
    prompt_records: list[dict[str, Any]] = []
    case_records: list[dict[str, Any]] = []
    benchmark_cells: list[dict[str, Any]] = []
    derived_plan_cases: dict[str, dict[str, Any]] = {}
    load_started = time.perf_counter()
    try:
        backend.load()
        load_ms = (time.perf_counter() - load_started) * 1000.0
        _validate_loaded_backend(backend, backend_name)
        model_receipt = backend.model_receipt()
        _artifact_summary(model_receipt)
        model_identity_sha256 = stable_model_identity(model_receipt)["sha256"]

        for prompt_index, prompt in enumerate(PROMPTS):
            prompt_id = _prompt_id(prompt_index)
            baseline = backend.forward(
                prompt, capture_layers=list(LAYERS), site=SITE
            )
            if baseline.logits.shape != (EXPECTED_VOCAB_SIZE,):
                raise ValidationError(
                    f"{backend_name} returned vocab shape {baseline.logits.shape!r}"
                )
            deterministic_repeat = backend.forward(
                prompt, capture_layers=list(LAYERS), site=SITE
            )
            arrays[_array_key(prompt_index, None, "baseline_logits")] = baseline.logits
            prompt_records.append(
                {
                    "id": prompt_id,
                    "prompt": prompt,
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "token_ids": baseline.token_ids,
                    "tokens": baseline.tokens,
                    "token_count": len(baseline.token_ids),
                    "determinism": {
                        "token_ids_match": (
                            baseline.token_ids == deterministic_repeat.token_ids
                        ),
                        "argmax_match": (
                            int(np.argmax(baseline.logits))
                            == int(np.argmax(deterministic_repeat.logits))
                        ),
                        "max_abs_logit_delta": float(
                            np.max(
                                np.abs(
                                    deterministic_repeat.logits - baseline.logits
                                )
                            )
                        ),
                    },
                }
            )

            for layer in LAYERS:
                case_id = _case_id(prompt_index, layer)
                baseline_activation = baseline.activations[layer]
                arrays[
                    _array_key(prompt_index, layer, "baseline_activation")
                ] = baseline_activation
                if plan is None:
                    reference_rms = _rms(baseline_activation)
                    target_rms = RELATIVE_INTERVENTION_RMS * reference_rms
                    vector = _intervention_vector(target_rms)
                else:
                    reference_rms = float(
                        plan["cases"][case_id]["reference_activation_rms"]
                    )
                    target_rms = float(plan["cases"][case_id]["target_vector_rms"])
                    vector = np.asarray(
                        plan["cases"][case_id]["vector_float32"], dtype=np.float32
                    )
                vector_sha256 = _array_sha256(vector)
                if plan is not None and vector_sha256 != plan["cases"][case_id][
                    "vector_sha256"
                ]:
                    raise ValidationError(f"Intervention vector hash drifted for {case_id}")
                if plan is None:
                    derived_plan_cases[case_id] = {
                        "reference_activation_rms": reference_rms,
                        "target_vector_rms": target_rms,
                        "realized_vector_rms": _rms(vector),
                        "vector_sha256": vector_sha256,
                        "vector_float32": vector.tolist(),
                    }

                zero = Intervention(
                    layer=layer,
                    vector=np.zeros(EXPECTED_MODEL_WIDTH, dtype=np.float32),
                    site=SITE,
                    position="last_nonpad",
                    label="zero-parity-vector",
                )
                changed = Intervention(
                    layer=layer,
                    vector=vector,
                    site=SITE,
                    position="last_nonpad",
                    label="fixed-relative-rms-parity-vector",
                )
                zero_result = backend.forward(
                    prompt,
                    capture_layers=[layer],
                    site=SITE,
                    intervention=zero,
                )
                changed_result = backend.forward(
                    prompt,
                    capture_layers=[layer],
                    site=SITE,
                    intervention=changed,
                )
                arrays[_array_key(prompt_index, layer, "changed_logits")] = (
                    changed_result.logits
                )
                arrays[_array_key(prompt_index, layer, "changed_activation")] = (
                    changed_result.activations[layer]
                )
                case_records.append(
                    {
                        "id": case_id,
                        "prompt_id": prompt_id,
                        "layer": layer,
                        "baseline_argmax": int(np.argmax(baseline.logits)),
                        "changed_argmax": int(np.argmax(changed_result.logits)),
                        "zero_hook": {
                            "max_logit_delta": float(
                                np.max(np.abs(zero_result.logits - baseline.logits))
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
                        "reference_activation_rms": reference_rms,
                        "target_vector_rms": target_rms,
                        "realized_vector_rms": _rms(vector),
                        "vector_sha256": vector_sha256,
                    }
                )

        for prompt_index, prompt in enumerate(PROMPTS):
            for layer in LAYERS:
                case_id = _case_id(prompt_index, layer)
                plan_row = (
                    derived_plan_cases[case_id]
                    if plan is None
                    else plan["cases"][case_id]
                )
                vector = np.asarray(plan_row["vector_float32"], dtype=np.float32)
                intervention = Intervention(
                    layer=layer,
                    vector=vector,
                    site=SITE,
                    position="last_nonpad",
                    label="fixed-relative-rms-parity-vector",
                )
                for _ in range(WARMUPS):
                    _timed_forward(
                        backend, prompt, intervention, layer=layer
                    )
                samples = [
                    _timed_forward(backend, prompt, intervention, layer=layer)
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
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "dtype": DTYPE,
            "site": SITE,
            "layers": list(LAYERS),
            "add_special_tokens": ADD_SPECIAL_TOKENS,
            "observed_architecture": {
                "num_layers": backend.num_layers,
                "model_width": backend.model_dim,
                "vocab_size_from_logits": EXPECTED_VOCAB_SIZE,
                "block_path": backend.block_path,
            },
            "load_time_ms": load_ms,
            "model_receipt": model_receipt,
            "model_identity_sha256": model_identity_sha256,
            "implementation": implementation_receipt(),
            "prompts": prompt_records,
            "cases": case_records,
            "benchmark": {
                "warmups_per_cell": WARMUPS,
                "repeats_per_cell": REPEATS,
                "cells": benchmark_cells,
            },
        }
        if plan is None:
            metadata["intervention_plan"] = {
                "model": MODEL_ID,
                "revision": MODEL_REVISION,
                "width": EXPECTED_MODEL_WIDTH,
                "layers": list(LAYERS),
                "relative_rms": RELATIVE_INTERVENTION_RMS,
                "direction": (
                    "float32 linspace(-0.05, 0.05, 3072), centered, "
                    "RMS-normalized"
                ),
                "cases": derived_plan_cases,
            }
        _write_worker_bundle(output_dir, metadata, arrays)
    finally:
        backend.close()


def _worker_command(
    backend_name: str,
    output_dir: Path,
    intervention_plan_path: Path | None,
) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--_worker-backend",
        backend_name,
        "--_worker-output-dir",
        str(output_dir),
    ]
    if intervention_plan_path is not None:
        command.extend(["--_worker-intervention-plan", str(intervention_plan_path)])
    return command


def _run_worker_subprocess(
    backend_name: str,
    output_dir: Path,
    intervention_plan_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    command = _worker_command(backend_name, output_dir, intervention_plan_path)
    environment = os.environ.copy()
    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    wall_time_ms = (time.perf_counter() - started) * 1000.0
    if completed.returncode != 0:
        stderr = completed.stderr[-4000:].strip()
        raise ValidationError(
            f"{backend_name} worker failed with exit code {completed.returncode}: {stderr}"
        )
    phase = _read_worker_bundle(output_dir)
    if phase.get("backend") != backend_name:
        raise ValidationError(f"{backend_name} worker returned a mismatched backend label")
    lifecycle = {
        "backend": backend_name,
        "launch_mode": "isolated_completed_subprocess",
        "returncode": completed.returncode,
        "wall_time_ms": wall_time_ms,
    }
    return phase, lifecycle


def _case_map(phase: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = phase.get("cases", [])
    mapped = {row["id"]: row for row in rows}
    if len(mapped) != len(PROMPTS) * len(LAYERS) or len(mapped) != len(rows):
        raise ValidationError(f"{phase.get('backend')} worker case set is incomplete")
    return mapped


def _prompt_map(phase: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = phase.get("prompts", [])
    mapped = {row["id"]: row for row in rows}
    if len(mapped) != len(PROMPTS) or len(mapped) != len(rows):
        raise ValidationError(f"{phase.get('backend')} worker prompt set is incomplete")
    return mapped


def _build_parity_cases(
    torch_phase: dict[str, Any], mlx_phase: dict[str, Any]
) -> list[dict[str, Any]]:
    torch_cases = _case_map(torch_phase)
    mlx_cases = _case_map(mlx_phase)
    torch_prompts = _prompt_map(torch_phase)
    mlx_prompts = _prompt_map(mlx_phase)
    torch_arrays = torch_phase["arrays"]
    mlx_arrays = mlx_phase["arrays"]
    cases: list[dict[str, Any]] = []
    for prompt_index, prompt in enumerate(PROMPTS):
        prompt_id = _prompt_id(prompt_index)
        torch_prompt = torch_prompts[prompt_id]
        mlx_prompt = mlx_prompts[prompt_id]
        baseline_logits_key = _array_key(prompt_index, None, "baseline_logits")
        torch_baseline_logits = torch_arrays[baseline_logits_key]
        mlx_baseline_logits = mlx_arrays[baseline_logits_key]
        for layer in LAYERS:
            case_id = _case_id(prompt_index, layer)
            torch_case = torch_cases[case_id]
            mlx_case = mlx_cases[case_id]
            baseline_activation_key = _array_key(
                prompt_index, layer, "baseline_activation"
            )
            changed_logits_key = _array_key(prompt_index, layer, "changed_logits")
            changed_activation_key = _array_key(
                prompt_index, layer, "changed_activation"
            )
            torch_baseline_activation = torch_arrays[baseline_activation_key]
            mlx_baseline_activation = mlx_arrays[baseline_activation_key]
            torch_changed_logits = torch_arrays[changed_logits_key]
            mlx_changed_logits = mlx_arrays[changed_logits_key]
            torch_changed_activation = torch_arrays[changed_activation_key]
            mlx_changed_activation = mlx_arrays[changed_activation_key]
            torch_activation_delta = (
                torch_changed_activation - torch_baseline_activation
            )
            mlx_activation_delta = mlx_changed_activation - mlx_baseline_activation
            plan_row = torch_phase["intervention_plan"]["cases"][case_id]
            vector = np.asarray(plan_row["vector_float32"], dtype=np.float32)
            if torch_case["vector_sha256"] != mlx_case["vector_sha256"]:
                raise ValidationError(f"Backend intervention vector hashes differ: {case_id}")
            cases.append(
                {
                    "id": case_id,
                    "prompt_id": prompt_id,
                    "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "token_count": len(torch_prompt["token_ids"]),
                    "layer": layer,
                    "token_ids_match": (
                        torch_prompt["token_ids"] == mlx_prompt["token_ids"]
                    ),
                    "baseline_argmax_match": (
                        torch_case["baseline_argmax"]
                        == mlx_case["baseline_argmax"]
                    ),
                    "changed_argmax_match": (
                        torch_case["changed_argmax"]
                        == mlx_case["changed_argmax"]
                    ),
                    "within_backend_determinism": {
                        "transformers_mps": torch_prompt["determinism"],
                        "mlx_gpu": mlx_prompt["determinism"],
                    },
                    "baseline_logits": _comparison(
                        torch_baseline_logits, mlx_baseline_logits
                    ),
                    "baseline_activation": _comparison(
                        torch_baseline_activation, mlx_baseline_activation
                    ),
                    "zero_hook": {
                        "transformers_mps": torch_case["zero_hook"],
                        "mlx_gpu": mlx_case["zero_hook"],
                    },
                    "changed_logits": _comparison(
                        torch_changed_logits, mlx_changed_logits
                    ),
                    "changed_activation": _comparison(
                        torch_changed_activation, mlx_changed_activation
                    ),
                    "logit_delta": _comparison(
                        torch_changed_logits - torch_baseline_logits,
                        mlx_changed_logits - mlx_baseline_logits,
                    ),
                    "activation_delta": _comparison(
                        torch_activation_delta, mlx_activation_delta
                    ),
                    "transformers_intervention_fidelity": _comparison(
                        vector, torch_activation_delta
                    ),
                    "mlx_intervention_fidelity": _comparison(
                        vector, mlx_activation_delta
                    ),
                    "fixed_intervention": {
                        "reference": "Transformers/MPS baseline resid_post RMS",
                        "reference_activation_rms": torch_case[
                            "reference_activation_rms"
                        ],
                        "relative_rms": RELATIVE_INTERVENTION_RMS,
                        "target_vector_rms": torch_case["target_vector_rms"],
                        "realized_vector_rms": torch_case["realized_vector_rms"],
                        "vector_sha256": torch_case["vector_sha256"],
                        "vector_float32": vector.tolist(),
                    },
                }
            )
    return cases


def _parity_gate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for case in cases:
        determinism = case["within_backend_determinism"]
        determinism_pass = all(
            row["token_ids_match"] and row["argmax_match"]
            for row in determinism.values()
        )
        zero_values = [
            value
            for backend_values in case["zero_hook"].values()
            for value in backend_values.values()
        ]
        checks.extend(
            [
                {
                    "id": f"{case['id']}:tokens_and_determinism",
                    "pass": bool(case["token_ids_match"] and determinism_pass),
                    "criterion": (
                        "Exact cross-backend token IDs and exact repeated-forward "
                        "within-backend token IDs/argmax"
                    ),
                    "value": {
                        "cross_backend_token_ids_match": case["token_ids_match"],
                        "within_backend": determinism,
                    },
                },
                {
                    "id": f"{case['id']}:baseline",
                    "pass": bool(
                        case["baseline_argmax_match"]
                        and _metric_pass(case["baseline_logits"], THRESHOLDS["baseline"])
                        and _metric_pass(
                            case["baseline_activation"], THRESHOLDS["baseline"]
                        )
                    ),
                    "criterion": (
                        "Baseline logits and activation NRMSE <= 0.02, cosine >= "
                        "0.999, and exact argmax"
                    ),
                    "value": {
                        "argmax_match": case["baseline_argmax_match"],
                        "logits": case["baseline_logits"],
                        "activation": case["baseline_activation"],
                    },
                },
                {
                    "id": f"{case['id']}:zero_hook",
                    "pass": bool(
                        all(value <= THRESHOLDS["zero_hook_max_abs"] for value in zero_values)
                    ),
                    "criterion": "Every zero-hook max absolute delta <= 1e-7",
                    "value": case["zero_hook"],
                },
                {
                    "id": f"{case['id']}:changed_outputs",
                    "pass": bool(
                        case["changed_argmax_match"]
                        and _metric_pass(case["changed_logits"], THRESHOLDS["changed"])
                        and _metric_pass(
                            case["changed_activation"], THRESHOLDS["changed"]
                        )
                    ),
                    "criterion": (
                        "Changed logits and activation NRMSE <= 0.02, cosine >= "
                        "0.999, and exact argmax"
                    ),
                    "value": {
                        "argmax_match": case["changed_argmax_match"],
                        "logits": case["changed_logits"],
                        "activation": case["changed_activation"],
                    },
                },
                {
                    "id": f"{case['id']}:deltas",
                    "pass": bool(
                        _metric_pass(case["logit_delta"], THRESHOLDS["logit_delta"])
                        and _metric_pass(
                            case["activation_delta"], THRESHOLDS["activation_delta"]
                        )
                    ),
                    "criterion": (
                        "Logit-delta NRMSE <= 0.05, cosine >= 0.99, RMS ratio in "
                        "[0.95,1.05]; activation-delta NRMSE <= 0.02, cosine >= "
                        "0.999, RMS ratio in [0.98,1.02]"
                    ),
                    "value": {
                        "logits": case["logit_delta"],
                        "activation": case["activation_delta"],
                    },
                },
                {
                    "id": f"{case['id']}:intervention_fidelity",
                    "pass": bool(
                        _metric_pass(
                            case["transformers_intervention_fidelity"],
                            THRESHOLDS["intervention_fidelity"],
                        )
                        and _metric_pass(
                            case["mlx_intervention_fidelity"],
                            THRESHOLDS["intervention_fidelity"],
                        )
                    ),
                    "criterion": (
                        "Each backend's captured activation delta versus the shared "
                        "float32 vector has NRMSE <= 0.01 and cosine >= 0.999"
                    ),
                    "value": {
                        "transformers_mps": case[
                            "transformers_intervention_fidelity"
                        ],
                        "mlx_gpu": case["mlx_intervention_fidelity"],
                    },
                },
            ]
        )
    return {
        "thresholds": THRESHOLDS,
        "checks": checks,
        "passed": sum(bool(check["pass"]) for check in checks),
        "total": len(checks),
        "pass": all(bool(check["pass"]) for check in checks),
    }


def _benchmark_gate(
    torch_phase: dict[str, Any], mlx_phase: dict[str, Any]
) -> dict[str, Any]:
    def cells_by_id(phase: dict[str, Any]) -> dict[str, dict[str, Any]]:
        cells = phase["benchmark"]["cells"]
        mapped = {cell["id"]: cell for cell in cells}
        if len(mapped) != len(PROMPTS) * len(LAYERS):
            raise ValidationError("Benchmark phase has an incomplete cell set")
        return mapped

    torch_cells = cells_by_id(torch_phase)
    mlx_cells = cells_by_id(mlx_phase)
    if set(torch_cells) != set(mlx_cells):
        raise ValidationError("Backend benchmark cell sets differ")
    cells: list[dict[str, Any]] = []
    torch_aggregate: list[float] = []
    mlx_aggregate: list[float] = []
    for case_id in sorted(torch_cells):
        torch_samples = [float(value) for value in torch_cells[case_id]["samples_ms"]]
        mlx_samples = [float(value) for value in mlx_cells[case_id]["samples_ms"]]
        if len(torch_samples) != REPEATS or len(mlx_samples) != REPEATS:
            raise ValidationError(f"Benchmark repeat count drifted for {case_id}")
        torch_aggregate.extend(torch_samples)
        mlx_aggregate.extend(mlx_samples)
        torch_summary = _distribution_summary(torch_samples)
        mlx_summary = _distribution_summary(mlx_samples)
        cells.append(
            {
                "id": case_id,
                "prompt_id": torch_cells[case_id]["prompt_id"],
                "layer": torch_cells[case_id]["layer"],
                "transformers_mps": torch_summary,
                "mlx_gpu": mlx_summary,
                "mlx_speedup": (
                    torch_summary["median_ms"] / mlx_summary["median_ms"]
                ),
            }
        )
    torch_summary = _distribution_summary(torch_aggregate)
    mlx_summary = _distribution_summary(mlx_aggregate)
    speed_fraction = THRESHOLDS["speed"][
        "mlx_max_fraction_of_transformers_median"
    ]
    return {
        "method": (
            "Non-interleaved isolated-process end-to-end backend.forward wall time; "
            "the Transformers/MPS phase, including all measurements, exits before "
            "the MLX/GPU phase starts. Each call includes tokenization, capture, "
            "intervention, device evaluation, and NumPy transfer."
        ),
        "interpretation": "machine-specific engineering selection gate only",
        "warmups_per_cell": WARMUPS,
        "repeats_per_cell": REPEATS,
        "layers": list(LAYERS),
        "prompt_token_counts": [
            row["token_count"] for row in torch_phase["prompts"]
        ],
        "cell_count": len(cells),
        "cells": cells,
        "transformers_mps": torch_summary,
        "mlx_gpu": mlx_summary,
        "mlx_speedup": torch_summary["median_ms"] / mlx_summary["median_ms"],
        "speed_gate": {
            "criterion": (
                "MLX aggregate median end-to-end latency <= 0.95 times the "
                "Transformers/MPS aggregate median"
            ),
            "mlx_fraction_of_transformers_median": (
                mlx_summary["median_ms"] / torch_summary["median_ms"]
            ),
            "pass": bool(
                mlx_summary["median_ms"]
                <= speed_fraction * torch_summary["median_ms"]
            ),
        },
    }


def _artifact_summary(model_receipt: dict[str, Any]) -> dict[str, Any]:
    artifact = model_receipt.get("model_artifact")
    if not isinstance(artifact, dict):
        raise ValidationError("Backend model receipt lacks an artifact manifest")
    required = ("file_count", "total_bytes", "manifest_sha256")
    if any(key not in artifact for key in required):
        raise ValidationError("Backend model artifact manifest is incomplete")
    summary = {key: artifact[key] for key in required}
    expected = {
        "file_count": EXPECTED_ARTIFACT_FILE_COUNT,
        "total_bytes": EXPECTED_ARTIFACT_TOTAL_BYTES,
        "manifest_sha256": EXPECTED_ARTIFACT_MANIFEST_SHA256,
    }
    if summary != expected:
        raise ValidationError(
            "Backend model artifact does not match the frozen downloaded manifest"
        )
    return summary


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for distribution in (
        "glyphprobe",
        "numpy",
        "torch",
        "transformers",
        "mlx",
        "mlx-lm",
        "huggingface-hub",
    ):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    return versions


def _physical_memory_bytes() -> int | None:
    try:
        return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _validate_phase_contract(phase: dict[str, Any], backend_name: str) -> None:
    expected = {
        "backend": backend_name,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "dtype": DTYPE,
        "site": SITE,
        "layers": list(LAYERS),
        "add_special_tokens": ADD_SPECIAL_TOKENS,
    }
    for key, value in expected.items():
        if phase.get(key) != value:
            raise ValidationError(f"{backend_name} phase field {key!r} drifted")
    architecture = phase.get("observed_architecture", {})
    if architecture.get("num_layers") != EXPECTED_NUM_LAYERS:
        raise ValidationError(f"{backend_name} phase layer count drifted")
    if architecture.get("model_width") != EXPECTED_MODEL_WIDTH:
        raise ValidationError(f"{backend_name} phase model width drifted")
    if architecture.get("vocab_size_from_logits") != EXPECTED_VOCAB_SIZE:
        raise ValidationError(f"{backend_name} phase vocabulary size drifted")


def _assemble_receipt(
    torch_phase: dict[str, Any],
    mlx_phase: dict[str, Any],
    lifecycle: list[dict[str, Any]],
) -> dict[str, Any]:
    _validate_phase_contract(torch_phase, "transformers_mps")
    _validate_phase_contract(mlx_phase, "mlx_gpu")
    if torch_phase["implementation"] != mlx_phase["implementation"]:
        raise ValidationError("GlyphProbe implementation changed between worker phases")
    torch_artifact = _artifact_summary(torch_phase["model_receipt"])
    mlx_artifact = _artifact_summary(mlx_phase["model_receipt"])
    if torch_artifact != mlx_artifact:
        raise ValidationError("Backend model artifact manifests differ")
    cases = _build_parity_cases(torch_phase, mlx_phase)
    parity = _parity_gate(cases)
    benchmark = _benchmark_gate(torch_phase, mlx_phase)
    status = (
        "validated_mlx_selected"
        if parity["pass"] and benchmark["speed_gate"]["pass"]
        else "validation_failed"
    )
    return {
        "schema_version": 3,
        "protocol_id": PROTOCOL_ID,
        "validator_version": VALIDATOR_VERSION,
        "supersedes_protocol_id": SUPERSEDES_PROTOCOL_ID,
        "technical_change": TECHNICAL_CHANGE,
        "status": status,
        "claim_boundary": CLAIM_BOUNDARY,
        "scientific_result": False,
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "dtype": DTYPE,
        "site": SITE,
        "add_special_tokens": ADD_SPECIAL_TOKENS,
        "capture_layers": list(LAYERS),
        "intervention_layers": list(LAYERS),
        "expected_architecture": {
            "num_layers": EXPECTED_NUM_LAYERS,
            "model_width": EXPECTED_MODEL_WIDTH,
            "vocab_size": EXPECTED_VOCAB_SIZE,
        },
        "fixed_intervention": {
            "construction": (
                "float32 linspace(-0.05, 0.05, 3072), centered and normalized "
                "to RMS 1, then scaled per prompt/layer to 0.05 times the "
                "Transformers/MPS baseline resid_post RMS"
            ),
            "relative_rms": RELATIVE_INTERVENTION_RMS,
            "shared_between_backends": True,
            "reference_backend": "transformers_mps",
        },
        "prompt_role": "fixed backend-engineering calibration inputs, not outcome targets",
        "prompts": [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "prompt_sha256": row["prompt_sha256"],
                "token_ids": row["token_ids"],
                "tokens": row["tokens"],
                "token_count": row["token_count"],
            }
            for row in torch_phase["prompts"]
        ],
        "data_scope": {
            "study_target_banks_accessed": False,
            "confirmatory_or_causal_outcomes_accessed": False,
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "physical_memory_bytes": _physical_memory_bytes(),
            "dependency_versions": _package_versions(),
            "worker_network_mode": "Hugging Face and Transformers offline",
        },
        "validation_config": {
            "payload": VALIDATION_CONFIG,
            "sha256": VALIDATION_CONFIG_SHA256,
        },
        "validator_sha256": _sha256(Path(__file__).resolve()),
        "implementation": torch_phase["implementation"],
        "process_lifecycle": {
            "mode": "strictly sequential isolated subprocesses",
            "order": ["transformers_mps", "mlx_gpu"],
            "simultaneous_model_residency": False,
            "phases": lifecycle,
        },
        "load_times": {
            "transformers_mps_ms": torch_phase["load_time_ms"],
            "mlx_gpu_ms": mlx_phase["load_time_ms"],
        },
        "model_artifact": {
            **torch_artifact,
            "backend_manifests_match": True,
        },
        "torch_model_receipt": torch_phase["model_receipt"],
        "torch_model_identity_sha256": torch_phase["model_identity_sha256"],
        "mlx_model_receipt": mlx_phase["model_receipt"],
        "mlx_model_identity_sha256": mlx_phase["model_identity_sha256"],
        "parity": parity,
        "cases": cases,
        "benchmark": benchmark,
        "decision": (
            "Use MLX only for the pinned Llama 3.2 3B BF16 resid_post layers 5 and 11"
            if status == "validated_mlx_selected"
            else "Do not use MLX for this scientific cell until failed gates are resolved"
        ),
    }


def run_validation(output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    output_path = output_path.resolve()
    if output_path.exists():
        raise ValidationError(f"Refusing to overwrite existing receipt: {output_path}")
    with tempfile.TemporaryDirectory(prefix="glyphprobe-llama32-parity-") as temporary:
        temporary_root = Path(temporary)
        torch_phase, torch_lifecycle = _run_worker_subprocess(
            "transformers_mps", temporary_root / "transformers"
        )
        intervention_plan = torch_phase.get("intervention_plan")
        if not isinstance(intervention_plan, dict):
            raise ValidationError("Transformers worker did not produce an intervention plan")
        plan_path = temporary_root / "intervention_plan.json"
        plan_path.write_text(
            json_dumps(intervention_plan, pretty=True) + "\n", encoding="utf-8"
        )

        # subprocess.run has returned, so the full Transformers model process is gone.
        gc.collect()
        mlx_phase, mlx_lifecycle = _run_worker_subprocess(
            "mlx_gpu", temporary_root / "mlx", plan_path
        )
        return _assemble_receipt(
            torch_phase,
            mlx_phase,
            [torch_lifecycle, mlx_lifecycle],
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the frozen Llama 3.2 3B BF16 resid_post MLX parity and "
            "engineering speed cell."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--_worker-backend",
        choices=("transformers_mps", "mlx_gpu"),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--_worker-output-dir", type=Path, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--_worker-intervention-plan", type=Path, help=argparse.SUPPRESS
    )
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if args._worker_backend is not None:
        if args._worker_output_dir is None:
            parser.error("internal worker mode requires --_worker-output-dir")
        _worker_phase(
            args._worker_backend,
            args._worker_output_dir,
            args._worker_intervention_plan,
        )
        return 0
    if args._worker_output_dir is not None or args._worker_intervention_plan is not None:
        parser.error("internal worker arguments require --_worker-backend")

    output_path = args.output.resolve()
    try:
        receipt = run_validation(output_path)
        _atomic_write_json_no_overwrite(output_path, receipt)
    except ValidationError as exc:
        parser.exit(2, f"validation error: {exc}\n")
    print(f"status={receipt['status']}")
    print(f"parity={receipt['parity']['passed']}/{receipt['parity']['total']}")
    print(f"mlx_speedup={receipt['benchmark']['mlx_speedup']:.3f}x")
    print(f"receipt={output_path}")
    return 0 if receipt["status"] == "validated_mlx_selected" else 1


if __name__ == "__main__":
    raise SystemExit(main())
