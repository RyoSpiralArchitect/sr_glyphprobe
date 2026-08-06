from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "validate_mlx_llama32_3b_bf16_parity.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_mlx_llama32_3b_bf16_parity", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def _synthetic_phase(backend_name: str) -> dict:
    arrays: dict[str, np.ndarray] = {}
    prompts: list[dict] = []
    cases: list[dict] = []
    plan_cases: dict[str, dict] = {}
    benchmark_cells: list[dict] = []
    baseline_activation = np.linspace(
        -1.0, 1.0, VALIDATOR.EXPECTED_MODEL_WIDTH, dtype=np.float32
    )
    reference_rms = VALIDATOR._rms(baseline_activation)
    target_rms = VALIDATOR.RELATIVE_INTERVENTION_RMS * reference_rms
    vector = VALIDATOR._intervention_vector(target_rms)
    vector_sha256 = VALIDATOR._array_sha256(vector)

    for prompt_index, prompt in enumerate(VALIDATOR.PROMPTS):
        prompt_id = VALIDATOR._prompt_id(prompt_index)
        token_ids = [10 + prompt_index, 100 + prompt_index]
        baseline_logits = np.asarray(
            [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
            dtype=np.float32,
        )
        arrays[
            VALIDATOR._array_key(prompt_index, None, "baseline_logits")
        ] = baseline_logits
        prompts.append(
            {
                "id": prompt_id,
                "prompt": prompt,
                "prompt_sha256": VALIDATOR.hashlib.sha256(
                    prompt.encode("utf-8")
                ).hexdigest(),
                "token_ids": token_ids,
                "tokens": [f"token-{value}" for value in token_ids],
                "token_count": len(token_ids),
                "determinism": {
                    "token_ids_match": True,
                    "argmax_match": True,
                    "max_abs_logit_delta": 0.0,
                },
            }
        )
        for layer in VALIDATOR.LAYERS:
            case_id = VALIDATOR._case_id(prompt_index, layer)
            activation = baseline_activation + np.float32(layer / 100.0)
            layer_reference_rms = VALIDATOR._rms(activation)
            layer_target_rms = (
                VALIDATOR.RELATIVE_INTERVENTION_RMS * layer_reference_rms
            )
            layer_vector = VALIDATOR._intervention_vector(layer_target_rms)
            layer_vector_sha256 = VALIDATOR._array_sha256(layer_vector)
            changed_logits = baseline_logits + np.asarray(
                [0.01, -0.02, 0.03, -0.01, 0.02, -0.03, 0.01, 0.04],
                dtype=np.float32,
            )
            arrays[
                VALIDATOR._array_key(prompt_index, layer, "baseline_activation")
            ] = activation
            arrays[
                VALIDATOR._array_key(prompt_index, layer, "changed_logits")
            ] = changed_logits
            arrays[
                VALIDATOR._array_key(prompt_index, layer, "changed_activation")
            ] = activation + layer_vector
            case_row = {
                "id": case_id,
                "prompt_id": prompt_id,
                "layer": layer,
                "baseline_argmax": int(np.argmax(baseline_logits)),
                "changed_argmax": int(np.argmax(changed_logits)),
                "zero_hook": {
                    "max_logit_delta": 0.0,
                    "max_activation_delta": 0.0,
                },
                "reference_activation_rms": layer_reference_rms,
                "target_vector_rms": layer_target_rms,
                "realized_vector_rms": VALIDATOR._rms(layer_vector),
                "vector_sha256": layer_vector_sha256,
            }
            cases.append(case_row)
            plan_cases[case_id] = {
                key: case_row[key]
                for key in (
                    "reference_activation_rms",
                    "target_vector_rms",
                    "realized_vector_rms",
                    "vector_sha256",
                )
            }
            plan_cases[case_id]["vector_float32"] = layer_vector.tolist()
            sample = 10.0 if backend_name == "transformers_mps" else 8.0
            benchmark_cells.append(
                {
                    "id": case_id,
                    "prompt_id": prompt_id,
                    "layer": layer,
                    "samples_ms": [sample] * VALIDATOR.REPEATS,
                    "summary": VALIDATOR._distribution_summary(
                        [sample] * VALIDATOR.REPEATS
                    ),
                }
            )

    phase = {
        "schema_version": 1,
        "backend": backend_name,
        "model": VALIDATOR.MODEL_ID,
        "revision": VALIDATOR.MODEL_REVISION,
        "dtype": VALIDATOR.DTYPE,
        "site": VALIDATOR.SITE,
        "layers": list(VALIDATOR.LAYERS),
        "add_special_tokens": VALIDATOR.ADD_SPECIAL_TOKENS,
        "observed_architecture": {
            "num_layers": VALIDATOR.EXPECTED_NUM_LAYERS,
            "model_width": VALIDATOR.EXPECTED_MODEL_WIDTH,
            "vocab_size_from_logits": VALIDATOR.EXPECTED_VOCAB_SIZE,
            "block_path": "model.layers",
        },
        "load_time_ms": 1.0,
        "model_receipt": {
            "backend": backend_name,
            "model_artifact": {
                "file_count": VALIDATOR.EXPECTED_ARTIFACT_FILE_COUNT,
                "total_bytes": VALIDATOR.EXPECTED_ARTIFACT_TOTAL_BYTES,
                "manifest_sha256": VALIDATOR.EXPECTED_ARTIFACT_MANIFEST_SHA256,
            },
        },
        "model_identity_sha256": (
            "b" * 64 if backend_name == "transformers_mps" else "c" * 64
        ),
        "implementation": {
            "package_version": "0.1.0",
            "source_file_count": 12,
            "source_tree_sha256": "d" * 64,
        },
        "prompts": prompts,
        "cases": cases,
        "benchmark": {
            "warmups_per_cell": VALIDATOR.WARMUPS,
            "repeats_per_cell": VALIDATOR.REPEATS,
            "cells": benchmark_cells,
        },
        "arrays": arrays,
    }
    if backend_name == "transformers_mps":
        phase["intervention_plan"] = {
            "model": VALIDATOR.MODEL_ID,
            "revision": VALIDATOR.MODEL_REVISION,
            "width": VALIDATOR.EXPECTED_MODEL_WIDTH,
            "layers": list(VALIDATOR.LAYERS),
            "relative_rms": VALIDATOR.RELATIVE_INTERVENTION_RMS,
            "direction": (
                "float32 linspace(-0.05, 0.05, 3072), centered, RMS-normalized"
            ),
            "cases": plan_cases,
        }
    assert vector_sha256
    assert target_rms > 0
    return phase


def test_frozen_model_architecture_prompts_and_thresholds() -> None:
    assert VALIDATOR.MODEL_ID == "mlx-community/Llama-3.2-3B-bf16"
    assert (
        VALIDATOR.MODEL_REVISION
        == "60a99aaf43164077157d64bf909b7b61143c6a6d"
    )
    assert VALIDATOR.DTYPE == "bfloat16"
    assert (
        VALIDATOR.PROTOCOL_ID
        == "glyphprobe-e2-llama32-3b-mlx-engineering-validation-v2"
    )
    assert VALIDATOR.VALIDATOR_VERSION == 2
    assert (
        VALIDATOR.SUPERSEDES_PROTOCOL_ID
        == "glyphprobe-e2-llama32-3b-mlx-engineering-validation-v1"
    )
    assert (
        VALIDATOR.TECHNICAL_CHANGE
        == "MLX BF16 arrays cast to mx.float32 before NumPy export"
    )
    assert VALIDATOR.LAYERS == (5, 11)
    assert VALIDATOR.ADD_SPECIAL_TOKENS is False
    assert (
        VALIDATOR.EXPECTED_NUM_LAYERS,
        VALIDATOR.EXPECTED_MODEL_WIDTH,
        VALIDATOR.EXPECTED_VOCAB_SIZE,
    ) == (28, 3072, 128_256)
    assert VALIDATOR.PROMPTS[:3] == ("🌒", "🐑", "Mark: 🤑\nAnchor:")
    assert VALIDATOR.PROMPTS[3:] == (
        "Continue briefly: The scientist opened the notebook and",
        (
            "Write a concise two-sentence explanation of why a careful scientist "
            "records every calibration setting before comparing experimental "
            "interventions."
        ),
    )
    assert len(VALIDATOR.PROMPTS) == 5
    assert (VALIDATOR.WARMUPS, VALIDATOR.REPEATS) == (2, 10)
    assert VALIDATOR.THRESHOLDS == {
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

    direction = VALIDATOR._fixed_unit_direction()
    assert direction.dtype == np.float32
    assert direction.shape == (3072,)
    assert VALIDATOR._rms(direction) == pytest.approx(1.0, abs=2e-7)
    vector = VALIDATOR._intervention_vector(0.123)
    assert VALIDATOR._rms(vector) == pytest.approx(0.123, rel=2e-7)
    assert VALIDATOR.VALIDATION_CONFIG["protocol_id"] == VALIDATOR.PROTOCOL_ID
    assert VALIDATOR.VALIDATION_CONFIG["validator_version"] == 2
    assert (
        VALIDATOR.VALIDATION_CONFIG["supersedes_protocol_id"]
        == VALIDATOR.SUPERSEDES_PROTOCOL_ID
    )
    assert (
        VALIDATOR.VALIDATION_CONFIG["technical_change"]
        == VALIDATOR.TECHNICAL_CHANGE
    )
    assert len(VALIDATOR.VALIDATION_CONFIG_SHA256) == 64


def test_v2_protocol_and_default_output_are_distinct_from_frozen_v1() -> None:
    v1_protocol_id = "glyphprobe-e2-llama32-3b-mlx-engineering-validation-v1"
    v1_output = Path("validation/mlx_llama32_3b_bf16_parity/receipt.json")
    v1_validation_config_sha256 = (
        "425d3fa53576fd5e8000efdbcd77ca27122e1c797590590c756d42e8f3f0155c"
    )

    assert VALIDATOR.PROTOCOL_ID != v1_protocol_id
    assert VALIDATOR.DEFAULT_OUTPUT == Path(
        "validation/mlx_llama32_3b_bf16_parity_v2/receipt.json"
    )
    assert VALIDATOR.DEFAULT_OUTPUT != v1_output
    assert VALIDATOR.VALIDATION_CONFIG_SHA256 != v1_validation_config_sha256


def test_fake_subprocess_command_is_offline_and_pinned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict = {}
    expected_phase = {"backend": "transformers_mps"}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(VALIDATOR.subprocess, "run", fake_run)
    monkeypatch.setattr(
        VALIDATOR, "_read_worker_bundle", lambda output_dir: expected_phase
    )
    phase, lifecycle = VALIDATOR._run_worker_subprocess(
        "transformers_mps", tmp_path / "phase"
    )

    assert phase is expected_phase
    assert lifecycle["launch_mode"] == "isolated_completed_subprocess"
    assert captured["command"] == [
        VALIDATOR.sys.executable,
        str(SCRIPT_PATH),
        "--_worker-backend",
        "transformers_mps",
        "--_worker-output-dir",
        str(tmp_path / "phase"),
    ]
    assert captured["kwargs"]["check"] is False
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["env"]["HF_HUB_OFFLINE"] == "1"
    assert captured["kwargs"]["env"]["TRANSFORMERS_OFFLINE"] == "1"


def test_run_is_strictly_sequential_and_receipt_schema_is_backend_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    torch_phase = _synthetic_phase("transformers_mps")
    mlx_phase = _synthetic_phase("mlx_gpu")
    calls: list[str] = []

    def fake_worker(backend_name, output_dir, intervention_plan_path=None):
        calls.append(backend_name)
        if backend_name == "transformers_mps":
            assert intervention_plan_path is None
            return copy.deepcopy(torch_phase), {
                "backend": backend_name,
                "launch_mode": "isolated_completed_subprocess",
                "returncode": 0,
                "wall_time_ms": 1.0,
            }
        assert calls == ["transformers_mps", "mlx_gpu"]
        assert intervention_plan_path is not None
        plan = json.loads(intervention_plan_path.read_text(encoding="utf-8"))
        assert plan == torch_phase["intervention_plan"]
        return copy.deepcopy(mlx_phase), {
            "backend": backend_name,
            "launch_mode": "isolated_completed_subprocess",
            "returncode": 0,
            "wall_time_ms": 1.0,
        }

    monkeypatch.setattr(VALIDATOR, "_run_worker_subprocess", fake_worker)
    receipt = VALIDATOR.run_validation(tmp_path / "receipt.json")

    assert calls == ["transformers_mps", "mlx_gpu"]
    assert receipt["schema_version"] == 3
    assert receipt["protocol_id"] == VALIDATOR.PROTOCOL_ID
    assert receipt["validator_version"] == 2
    assert receipt["supersedes_protocol_id"] == VALIDATOR.SUPERSEDES_PROTOCOL_ID
    assert receipt["technical_change"] == VALIDATOR.TECHNICAL_CHANGE
    assert receipt["status"] == "validated_mlx_selected"
    assert receipt["claim_boundary"] == VALIDATOR.CLAIM_BOUNDARY
    assert receipt["scientific_result"] is False
    assert receipt["model"] == VALIDATOR.MODEL_ID
    assert receipt["revision"] == VALIDATOR.MODEL_REVISION
    assert receipt["dtype"] == "bfloat16"
    assert receipt["site"] == "resid_post"
    assert receipt["intervention_layers"] == [5, 11]
    assert receipt["parity"]["pass"] is True
    assert receipt["benchmark"]["speed_gate"]["pass"] is True
    assert receipt["process_lifecycle"]["simultaneous_model_residency"] is False
    assert receipt["process_lifecycle"]["order"] == [
        "transformers_mps",
        "mlx_gpu",
    ]
    assert receipt["data_scope"] == {
        "study_target_banks_accessed": False,
        "confirmatory_or_causal_outcomes_accessed": False,
    }
    assert receipt["model_artifact"]["backend_manifests_match"] is True
    assert receipt["validation_config"] == {
        "payload": VALIDATOR.VALIDATION_CONFIG,
        "sha256": VALIDATOR.VALIDATION_CONFIG_SHA256,
    }
    assert len(receipt["cases"]) == 10
    assert receipt["parity"]["total"] == 60


def test_receipt_write_is_atomic_and_never_overwrites(tmp_path: Path) -> None:
    destination = tmp_path / "validation" / "receipt.json"
    VALIDATOR._atomic_write_json_no_overwrite(destination, {"status": "first"})
    first_bytes = destination.read_bytes()
    first_inode = destination.stat().st_ino

    with pytest.raises(VALIDATOR.ValidationError, match="Refusing to overwrite"):
        VALIDATOR._atomic_write_json_no_overwrite(
            destination, {"status": "second"}
        )

    assert destination.read_bytes() == first_bytes
    assert destination.stat().st_ino == first_inode


def test_model_artifact_inventory_is_pinned_before_engineering_forwards() -> None:
    good = _synthetic_phase("transformers_mps")["model_receipt"]
    assert VALIDATOR._artifact_summary(good) == {
        "file_count": VALIDATOR.EXPECTED_ARTIFACT_FILE_COUNT,
        "total_bytes": VALIDATOR.EXPECTED_ARTIFACT_TOTAL_BYTES,
        "manifest_sha256": VALIDATOR.EXPECTED_ARTIFACT_MANIFEST_SHA256,
    }
    bad = copy.deepcopy(good)
    bad["model_artifact"]["file_count"] += 1
    with pytest.raises(VALIDATOR.ValidationError, match="frozen downloaded manifest"):
        VALIDATOR._artifact_summary(bad)

    worker_source = inspect.getsource(VALIDATOR._worker_phase)
    assert worker_source.index("_artifact_summary(model_receipt)") < worker_source.index(
        "for prompt_index, prompt in enumerate(PROMPTS)"
    )


def test_existing_receipt_fails_before_any_worker_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "receipt.json"
    destination.write_text('{"sealed": true}\n', encoding="utf-8")

    def forbidden_worker(*args, **kwargs):
        raise AssertionError("worker must not start when the receipt exists")

    monkeypatch.setattr(VALIDATOR, "_run_worker_subprocess", forbidden_worker)
    with pytest.raises(VALIDATOR.ValidationError, match="Refusing to overwrite"):
        VALIDATOR.run_validation(destination)


def test_validation_orchestration_never_opens_holdout_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    torch_phase = _synthetic_phase("transformers_mps")
    mlx_phase = _synthetic_phase("mlx_gpu")
    original_open = Path.open
    opened: list[str] = []
    forbidden_suffixes = (
        "data/targets/p2_confirmatory_targets_v1.jsonl",
        "data/targets/c1_causal_holdout_targets_v1.jsonl",
    )

    def guarded_open(path: Path, *args, **kwargs):
        normalized = path.as_posix()
        assert not normalized.endswith(forbidden_suffixes)
        opened.append(normalized)
        return original_open(path, *args, **kwargs)

    phases = iter((torch_phase, mlx_phase))

    def fake_worker(backend_name, output_dir, intervention_plan_path=None):
        phase = copy.deepcopy(next(phases))
        return phase, {
            "backend": backend_name,
            "launch_mode": "isolated_completed_subprocess",
            "returncode": 0,
            "wall_time_ms": 1.0,
        }

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(VALIDATOR, "_run_worker_subprocess", fake_worker)
    receipt = VALIDATOR.run_validation(tmp_path / "receipt.json")

    assert receipt["data_scope"]["study_target_banks_accessed"] is False
    assert not any("data/targets" in path for path in opened)
    source = inspect.getsource(VALIDATOR)
    assert "p2_confirmatory_targets_v1" not in source
    assert "c1_causal_holdout_targets_v1" not in source
