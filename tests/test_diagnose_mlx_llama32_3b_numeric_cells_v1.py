from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "diagnose_mlx_llama32_3b_numeric_cells_v1.py"
SPEC = importlib.util.spec_from_file_location("mlx_numeric_screen", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
SCREEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREEN)


def _metric() -> dict:
    return {
        "shape_match": True,
        "normalized_rmse": 0.001,
        "cosine": 0.9999,
        "reference_rms": 1.0,
        "candidate_rms": 1.0,
        "rms_ratio": 1.0,
        "max_abs": 0.001,
    }


def _phase(backend: str, dtype: str, sample_ms: float) -> dict:
    prompts = [
        {
            "id": SCREEN._prompt_id(index),
            "prompt_sha256": f"prompt-sha-{index}",
            "prompt_utf8_hex": f"{index:02x}",
            "prompt_utf8_bytes": index + 1,
            "token_ids": [index + 1, index + 10],
            "last_nonpad_position": 1,
            "determinism": {
                "token_ids_match": True,
                "argmax_match": True,
                "max_abs_logit_delta": 0.0,
            },
        }
        for index in range(len(SCREEN.PROMPTS))
    ]
    cases = []
    cells = []
    for prompt_index in range(len(SCREEN.PROMPTS)):
        for layer in SCREEN.LAYERS:
            case_id = SCREEN._case_id(prompt_index, layer)
            cases.append(
                {
                    "id": case_id,
                    "vector_sha256": "a" * 64,
                    "zero_hook": {
                        "max_logit_delta": 0.0,
                        "max_activation_delta": 0.0,
                    },
                    "intervention_fidelity": _metric(),
                }
            )
            cells.append(
                {
                    "id": case_id,
                    "samples_ms": [sample_ms] * SCREEN.REPEATS,
                }
            )
    artifact = {
        "file_count": SCREEN.EXPECTED_ARTIFACT_FILE_COUNT,
        "total_bytes": SCREEN.EXPECTED_ARTIFACT_TOTAL_BYTES,
        "manifest_sha256": SCREEN.EXPECTED_ARTIFACT_MANIFEST_SHA256,
    }
    result = {
        "backend": backend,
        "runtime_dtype": dtype,
        "prompts": prompts,
        "cases": cases,
        "benchmark": {"cells": cells},
        "implementation": {"source_tree_sha256": "b" * 64},
        "runtime_dtype_audit": {
            "requested_runtime_dtype": dtype,
            "resolved_runtime_dtype": dtype,
            "resolved_matches_requested": True,
            "parameter_audit": {
                "all_parameter_dtypes_match_requested": True,
                "parameter_count_matches_expected": True,
            },
            "artifact_storage_dtype": "bfloat16",
            "artifact_manifest": artifact,
        },
        "model_identity_sha256": f"{backend}-{dtype}",
        "load_time_ms": 1.0,
    }
    if backend == "transformers_mps":
        result["intervention_plan"] = {}
    return result


def _candidate(dtype: str, mlx_median_ms: float, eligible: bool = True) -> dict:
    gates = {
        "tokens_and_determinism": eligible,
        "zero_hook": eligible,
        "intervention_fidelity": eligible,
        "runtime_dtype_identity": eligible,
        "speed": eligible,
    }
    return {
        "runtime_dtype": dtype,
        "eligible": eligible,
        "gates": gates,
        "benchmark": {"mlx_gpu": {"median_ms": mlx_median_ms}},
    }


def test_frozen_screen_scope_and_thresholds() -> None:
    assert SCREEN.PROTOCOL_ID == "glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1"
    assert SCREEN.NUMERIC_CANDIDATES == ("float16", "float32")
    assert SCREEN.MODEL_ID == "mlx-community/Llama-3.2-3B-bf16"
    assert SCREEN.MODEL_REVISION == "60a99aaf43164077157d64bf909b7b61143c6a6d"
    assert SCREEN.LAYERS == (5, 11)
    assert len(SCREEN.PROMPTS) == 5
    assert SCREEN.RELATIVE_INTERVENTION_RMS == 0.05
    assert (SCREEN.WARMUPS, SCREEN.REPEATS) == (2, 10)
    assert SCREEN.THRESHOLDS == {
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
    assert SCREEN.VALIDATION_CONFIG["artifact_storage_dtype"] == "bfloat16"
    assert SCREEN.EXPECTED_PARAMETER_COUNT == 3_212_749_824


def test_selection_rules_are_deterministic_and_no_go_is_explicit() -> None:
    candidates = {
        "float16": _candidate("float16", 90.0),
        "float32": _candidate("float32", 90.8),
    }
    tie = SCREEN._select_candidate(candidates)
    assert tie["selected_runtime_dtype"] == "float32"
    assert tie["decision"] == "both_eligible_tie_select_fp32"

    candidates["float32"] = _candidate("float32", 100.0)
    fastest = SCREEN._select_candidate(candidates)
    assert fastest["selected_runtime_dtype"] == "float16"
    assert fastest["decision"] == "both_eligible_select_lower_mlx_median"

    candidates["float16"] = _candidate("float16", 90.0, eligible=False)
    only = SCREEN._select_candidate(candidates)
    assert only["selected_runtime_dtype"] == "float32"
    assert only["decision"] == "single_eligible_candidate"

    candidates["float32"] = _candidate("float32", 100.0, eligible=False)
    no_go = SCREEN._select_candidate(candidates)
    assert no_go["selected_runtime_dtype"] is None
    assert no_go["decision"] == "no_go_no_eligible_numeric_candidate"


def test_candidate_summary_requires_all_fixed_gates() -> None:
    torch_phase = _phase("transformers_mps", "float32", 100.0)
    mlx_phase = _phase("mlx_gpu", "float32", 90.0)
    summary = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert summary["eligible"] is True
    assert summary["gates"] == {
        "tokens_and_determinism": True,
        "zero_hook": True,
        "intervention_fidelity": True,
        "runtime_dtype_identity": True,
        "speed": True,
    }

    mlx_phase["cases"][0]["intervention_fidelity"]["normalized_rmse"] = 0.02
    failed = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert failed["eligible"] is False
    assert failed["gates"]["intervention_fidelity"] is False

    mlx_phase = _phase("mlx_gpu", "float32", 90.0)
    mlx_phase["prompts"][0]["prompt_utf8_hex"] = "mismatch"
    identity_failed = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert identity_failed["eligible"] is False
    assert identity_failed["gates"]["tokens_and_determinism"] is False

    mlx_phase = _phase("mlx_gpu", "float32", 90.0)
    mlx_phase["runtime_dtype_audit"]["parameter_audit"][
        "parameter_count_matches_expected"
    ] = False
    dtype_failed = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert dtype_failed["eligible"] is False
    assert dtype_failed["gates"]["runtime_dtype_identity"] is False


def test_nonfinite_metric_or_timing_samples_are_explicitly_ineligible() -> None:
    torch_phase = _phase("transformers_mps", "float32", 100.0)
    mlx_phase = _phase("mlx_gpu", "float32", 90.0)
    mlx_phase["cases"][0]["intervention_fidelity"]["cosine"] = float("nan")
    metric_failed = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert metric_failed["eligible"] is False
    assert metric_failed["gates"]["intervention_fidelity"] is False

    mlx_phase = _phase("mlx_gpu", "float32", 90.0)
    mlx_phase["benchmark"]["cells"][0]["samples_ms"][0] = float("nan")
    timing_failed = SCREEN._candidate_summary("float32", torch_phase, mlx_phase, [])
    assert timing_failed["eligible"] is False
    assert timing_failed["benchmark"]["finite_samples"] is False
    assert timing_failed["gates"]["speed"] is False


def test_screen_receipt_is_engineering_only_and_no_overwrite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_worker(
        backend_name: str,
        dtype: str,
        output_dir: Path,
        plan_path: Path | None = None,
    ) -> tuple[dict, dict]:
        del output_dir, plan_path
        sample_ms = 100.0 if backend_name == "transformers_mps" else 90.0
        return _phase(backend_name, dtype, sample_ms), {
            "backend": backend_name,
            "runtime_dtype": dtype,
            "returncode": 0,
        }

    monkeypatch.setattr(SCREEN, "_run_worker_subprocess", fake_worker)
    output = tmp_path / "receipt.json"
    receipt = SCREEN.run_screen(output)

    assert receipt["status"] == "engineering_screen_complete"
    assert receipt["scientific_result"] is False
    assert receipt["selection_is_not_scientific_authorization"] is True
    assert receipt["data_scope"] == {
        "study_target_banks_accessed": False,
        "confirmatory_or_causal_outcomes_accessed": False,
    }
    assert receipt["selection"]["selected_runtime_dtype"] == "float32"
    prompt_check = receipt["candidates"]["float32"]["prompt_checks"][0]
    assert prompt_check["prompt_identity"] == {
        "match": True,
        "transformers_mps": {
            "prompt_sha256": "prompt-sha-0",
            "prompt_utf8_hex": "00",
            "prompt_utf8_bytes": 1,
            "last_nonpad_position": 1,
        },
        "mlx_gpu": {
            "prompt_sha256": "prompt-sha-0",
            "prompt_utf8_hex": "00",
            "prompt_utf8_bytes": 1,
            "last_nonpad_position": 1,
        },
    }
    assert not output.exists(), "run_screen assembles; only atomic publication writes"

    SCREEN._atomic_write_json_no_overwrite(output, receipt)
    with pytest.raises(SCREEN.ValidationError, match="Refusing to overwrite"):
        SCREEN._atomic_write_json_no_overwrite(output, receipt)


def test_screen_records_a_candidate_worker_failure_as_no_go_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_worker(
        backend_name: str,
        dtype: str,
        output_dir: Path,
        plan_path: Path | None = None,
    ) -> tuple[dict, dict]:
        del output_dir, plan_path
        if dtype == "float16":
            raise SCREEN.WorkerFailure(
                "synthetic FP16 worker failure",
                {
                    "backend": backend_name,
                    "runtime_dtype": dtype,
                    "returncode": 9,
                    "wall_time_ms": 12.0,
                },
            )
        sample_ms = 100.0 if backend_name == "transformers_mps" else 90.0
        return _phase(backend_name, dtype, sample_ms), {
            "backend": backend_name,
            "runtime_dtype": dtype,
            "returncode": 0,
        }

    monkeypatch.setattr(SCREEN, "_run_worker_subprocess", fake_worker)
    receipt = SCREEN.run_screen(tmp_path / "receipt.json")

    assert receipt["candidates"]["float16"]["eligible"] is False
    assert receipt["candidates"]["float16"]["failure"]["kind"] == (
        "engineering_worker_or_contract_failure"
    )
    assert receipt["candidates"]["float16"]["process_lifecycle"] == [
        {
            "backend": "transformers_mps",
            "runtime_dtype": "float16",
            "returncode": 9,
            "wall_time_ms": 12.0,
        }
    ]
    assert receipt["selection"]["selected_runtime_dtype"] == "float32"
