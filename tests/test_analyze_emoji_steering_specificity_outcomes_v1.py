from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_steering_specificity_outcomes_v1.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_emoji_steering_specificity_outcomes_v1", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _zero_rows(js_divergence: float, count: int = 256) -> list[dict]:
    return [
        {
            "response_index": index,
            "condition_kind": "zero_direction",
            "site_index": index // 32,
            "block_index": index // 32,
            "depth_fraction": (index // 32 + 1) / 8,
            "magnitude": 0.0,
            "sign": 0,
            "target_index": index % 32,
            "target_id": f"target-{index % 32:02d}",
            "target_group": f"group-{index % 4}",
            "kl_baseline_to_intervened": 0.0,
            "js_divergence": js_divergence,
            "total_variation": 0.0,
            "logit_delta_rms": 0.0,
            "baseline_entropy": 1.25,
            "intervened_entropy": 1.25,
            "baseline_argmax_id": 3,
            "intervened_argmax_id": 3,
            "argmax_flip": False,
        }
        for index in range(count)
    ]


def _zero_arrays(count: int = 256) -> dict[str, np.ndarray]:
    return {
        "top_positive_ids": np.full((count, 3), 3, dtype=np.int32),
        "top_positive_values": np.zeros((count, 3), dtype=np.float32),
        "top_negative_ids": np.full((count, 3), 3, dtype=np.int32),
        "top_negative_values": np.zeros((count, 3), dtype=np.float32),
        "countsketch": np.zeros((count, 4), dtype=np.float32),
    }


def test_shared_v1_zero_validator_accepts_bounded_js_roundtrip() -> None:
    geometry = MODULE._load_geometry_v1()
    residual = 4.0 * float(np.finfo(np.float32).eps)
    result = geometry.validate_zero_control_v1(
        _zero_rows(residual), **_zero_arrays(), vocab_size=16
    )
    assert result["status"] == MODULE.ZERO_GATE_STATUS
    assert result["js_residual"]["maximum_absolute"] == residual
    assert result["js_residual"]["tolerance"] == MODULE.JS_ABS_TOLERANCE
    assert result["historical_v0_exact_js_gate"] == (
        MODULE.HISTORICAL_V0_ZERO_GATE_STATUS
    )
    assert (
        result["v0_exact_js_predicate_on_current_rows"]
        == MODULE.V0_CURRENT_PREDICATE_FAIL
    )


def test_shared_v1_zero_validator_allows_current_rows_to_be_exact_zero() -> None:
    geometry = MODULE._load_geometry_v1()
    result = geometry.validate_zero_control_v1(
        _zero_rows(0.0), **_zero_arrays(), vocab_size=16
    )
    assert result["status"] == MODULE.ZERO_GATE_STATUS
    assert (
        result["v0_exact_js_predicate_on_current_rows"]
        == MODULE.V0_CURRENT_PREDICATE_PASS
    )
    assert result["historical_v0_exact_js_gate"] == (
        MODULE.HISTORICAL_V0_ZERO_GATE_STATUS
    )


def test_shared_v1_zero_validator_rejects_js_over_bound() -> None:
    geometry = MODULE._load_geometry_v1()
    residual = 9.0 * float(np.finfo(np.float32).eps)
    with pytest.raises(geometry.GeometryAnalysisError, match="JS"):
        geometry.validate_zero_control_v1(
            _zero_rows(residual), **_zero_arrays(), vocab_size=16
        )


def test_full_closeout_then_zero_gate_precede_nonzero_ledgers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    receipt_path = tmp_path / "closeout.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_id": MODULE.V0.ANALYSIS_ID,
                "source_protocol_id": MODULE.V0.SOURCE_PROTOCOL_ID,
                "status": "scientific_open_closeout_complete",
                "scientific_open_authorized": True,
                "independent_hash_verification": True,
                "scientific_values_parsed": False,
                "run_root": str(run_root.resolve()),
                "roles_complete": 9,
                "roles_required": 9,
                "run_binding_root_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    events: list[str] = []

    def amendment_freeze():
        events.append("amendment_freeze")
        return {
            "status": "amendment_freeze_audit_pass",
            "amendment_id": MODULE.AMENDMENT_ID,
            "scientific_values_parsed_by_auditor": False,
        }

    def preflight(_directory, roles):
        events.append("preflight")
        return {role: "b" * 64 for role in roles}

    def audit(*_args):
        events.append("closeout")
        return {
            "status": "scientific_open_closeout_audit_pass",
            "scientific_values_parsed": False,
            "run_binding_root_sha256": "a" * 64,
        }

    def zero(*_args):
        events.append("zero")
        return {
            "status": "all_pilot_zero_controls_amendment_v1_pass",
            "zero_policy": {"primitive_noop_equalities": "exact"},
        }

    def ledger(_root, _role, kind, _count):
        events.append(kind)
        return []

    monkeypatch.setattr(
        MODULE, "_audit_amendment_freeze_same_process", amendment_freeze
    )
    monkeypatch.setattr(MODULE, "_validate_preflight_bindings_same_process", preflight)
    monkeypatch.setattr(MODULE, "_audit_closeout_same_process", audit)
    monkeypatch.setattr(MODULE, "_verify_zero_gate_same_process", zero)
    monkeypatch.setattr(MODULE, "_load_kind_ledgers", ledger)
    monkeypatch.setattr(
        MODULE,
        "_acquisition_config",
        lambda: {"pilot": {"roles": ["synthetic_role"]}},
    )

    preflight_directory = tmp_path / "preflight"
    preflight_directory.mkdir()
    *_, authorization = MODULE.load_authorized_rows(
        run_root, receipt_path, preflight_directory
    )
    assert events == [
        "amendment_freeze",
        "preflight",
        "closeout",
        "zero",
        "item",
        "prototype",
        "random",
    ]
    assert authorization["value_open_order"][:4] == [
        "same_process_amendment_freeze_audit",
        "frozen_preflight_receipt_binding",
        "same_process_full_closeout_audit",
        "all_pilot_zero_controls_only",
    ]


def test_v0_compact_results_are_preserved_under_amendment_metadata() -> None:
    source = {
        "analysis_id": MODULE.V0.ANALYSIS_ID,
        "status": "exploratory_f1_f2_f3_complete",
        "decision_status": "no_confirmatory_verdict",
        "families": {
            "F1_item_source_form": {
                "paired_contrasts": [{"value": 1}, {"value": 2}],
                "summaries": ["drop"],
                "pooled_summaries": ["drop"],
                "overall_summaries": [{"mean": 1.5}],
                "system_summaries": [{"mean": 1.0}],
            },
            "F2_prototype_depth_dose": {
                "dose_order_records": [{"value": 1}],
                "sign_pair_records": [{"value": 2}],
                "source_form_contrasts": [{"value": 3}],
                "surface_summaries": ["drop"],
                "sign_pair_summaries": ["drop"],
                "complete_surface_summaries": [{"mean": 2.0}],
                "headline_macro_summaries": [{"mean": 3.0}],
            },
            "F3_random_null_calibration": {
                "prototype_calibrations": [{"value": 4}],
                "calibration_summaries": [{"mean": 4.0}],
                "headline_macro_summaries": [{"mean": 5.0}],
            },
        },
    }
    compact = MODULE.compact_production_output(source)
    authorization = {
        "zero_hook_gate": {
            "zero_policy": {
                "primitive_noop_equalities": "exact",
                "js_absolute_tolerance": MODULE.JS_ABS_TOLERANCE,
            },
            "historical_v0_exact_js_gate": {
                "status": MODULE.HISTORICAL_V0_ZERO_GATE_STATUS,
                "failed_model_roles": "unknown_not_recorded",
                "exact_failed_value": "unknown_not_recorded",
            },
            "v0_exact_js_predicate_on_current_rows": {
                "classification": "counterfactual_diagnostic_not_historical_record",
                "would_fail_model_roles": ["synthetic_model"],
                "would_pass_model_roles": [],
            },
        }
    }
    result = MODULE._apply_amendment_metadata(compact, authorization)

    assert result["analysis_id"] == MODULE.AMENDMENT_ID
    assert result["original_analysis_v0"]["analysis_id"] == MODULE.V0.ANALYSIS_ID
    assert result["original_analysis_v0"]["f1_f2_f3_math"] == "reused_unchanged"
    assert (
        result["original_analysis_v0"]["historical_exact_js_gate"]["failed_model_roles"]
        == "unknown_not_recorded"
    )
    assert result["production_output"]["mode"] == "compact_fixed_summaries"
    assert result["families"]["F1_item_source_form"]["overall_summaries"] == [
        {"mean": 1.5}
    ]
    assert (
        result["families"]["F1_item_source_form"]["omitted_derived_detail"][0][
            "record_count"
        ]
        == 2
    )
    assert result["amendment_v1"]["no_confirmatory_verdict"] is True


def test_command_defaults_to_point_estimates_and_forbids_unregistered_count(
    tmp_path: Path,
) -> None:
    args = MODULE.parser().parse_args(
        [
            "--run-root",
            "/tmp/run",
            "--scientific-open-receipt",
            "/tmp/closeout.json",
            "--output",
            "/tmp/result.json",
        ]
    )
    assert args.bootstrap_replicates == 0

    run_root = tmp_path / "run"
    run_root.mkdir()
    with pytest.raises(MODULE.OutcomeAnalysisError, match="registered bootstrap"):
        MODULE.analyze_run(
            run_root,
            tmp_path / "closeout.json",
            tmp_path / "result.json",
            bootstrap_replicates=1,
        )


def test_production_output_is_external_and_never_overwritten(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    receipt = tmp_path / "closeout.json"
    with pytest.raises(MODULE.OutcomeAnalysisError, match="outside the sealed"):
        MODULE.analyze_run(run_root, receipt, run_root / "analysis.json")

    existing = tmp_path / "existing.json"
    existing.write_text("preserve", encoding="utf-8")
    with pytest.raises(MODULE.OutcomeAnalysisError, match="already exists"):
        MODULE.analyze_run(run_root, receipt, existing)
    assert existing.read_text(encoding="utf-8") == "preserve"
