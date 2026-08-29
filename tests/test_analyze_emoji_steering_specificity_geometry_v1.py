from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_steering_specificity_geometry_v1.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_emoji_steering_specificity_geometry_v1", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _targets() -> list[dict]:
    return [
        {"id": f"target-{index:02d}", "group": f"group-{index % 4}"}
        for index in range(32)
    ]


def _zero_rows() -> list[dict]:
    targets = _targets()
    rows = []
    for site_index in range(8):
        for target_index, target in enumerate(targets):
            rows.append(
                {
                    "condition_kind": "zero_direction",
                    "site_index": site_index,
                    "block_index": site_index * 2,
                    "depth_fraction": (site_index + 1) / 8,
                    "magnitude": 0.0,
                    "sign": 0,
                    "target_index": target_index,
                    "target_id": target["id"],
                    "target_group": target["group"],
                    "response_index": len(rows),
                    "kl_baseline_to_intervened": 0.0,
                    "js_divergence": 0.0,
                    "total_variation": 0.0,
                    "baseline_entropy": 2.5,
                    "intervened_entropy": 2.5,
                    "logit_delta_rms": 0.0,
                    "baseline_argmax_id": 4,
                    "intervened_argmax_id": 4,
                    "argmax_flip": False,
                }
            )
    return rows


def _zero_arrays() -> dict[str, np.ndarray]:
    count = 256
    return {
        "top_positive_ids": np.tile(np.arange(4, dtype=np.int32), (count, 1)),
        "top_positive_values": np.zeros((count, 4), dtype=np.float32),
        "top_negative_ids": np.tile(np.arange(4, dtype=np.int32), (count, 1)),
        "top_negative_values": np.zeros((count, 4), dtype=np.float32),
        "countsketch": np.zeros((count, 8), dtype=np.float32),
    }


def _validate(rows: list[dict], arrays: dict[str, np.ndarray] | None = None) -> dict:
    return MODULE.validate_zero_control_v1(
        rows,
        **(_zero_arrays() if arrays is None else arrays),
        vocab_size=8,
        expected_target_rows=_targets(),
        expected_block_indices=[index * 2 for index in range(8)],
        expected_depth_fractions=[(index + 1) / 8 for index in range(8)],
    )


def test_amended_zero_gate_accepts_two_sided_sub_bound_js_and_reports_residuals() -> (
    None
):
    rows = _zero_rows()
    tolerance = float(8 * np.finfo(np.float32).eps)
    rows[0]["js_divergence"] = tolerance / 2
    rows[1]["js_divergence"] = -tolerance
    result = _validate(rows)

    assert result["status"] == (
        "primitive_exact_noop_with_bounded_float32_js_roundtrip"
    )
    assert result["historical_v0_exact_js_gate"] == (
        "failed_closed_on_js_divergence_per_frozen_failure_receipt"
    )
    assert result["v0_exact_js_predicate_on_current_rows"] == (
        "would_fail_nonzero_roundtrip_residual"
    )
    assert result["js_residual"] == {
        "minimum": -tolerance,
        "maximum": tolerance / 2,
        "maximum_absolute": tolerance,
        "tolerance": tolerance,
        "two_sided": True,
        "all_finite": True,
        "exact_zero_rows": 254,
        "nonzero_rows": 2,
    }
    assert result["grid"]["unique_site_target_cells"] == 256
    assert result["no_claim_of_exact_js"] is True


def test_amended_zero_gate_also_accepts_exact_zero_js_without_data_dependent_failure() -> (
    None
):
    result = _validate(_zero_rows())
    assert result["status"] == MODULE.ZERO_GATE_STATUS
    assert result["v0_exact_js_predicate_on_current_rows"] == (
        "would_pass_all_js_exact_zero"
    )
    assert result["js_residual"]["maximum_absolute"] == 0.0


def test_amended_zero_gate_rejects_js_over_the_independently_derived_bound() -> None:
    rows = _zero_rows()
    tolerance = float(8 * np.finfo(np.float32).eps)
    rows[7]["js_divergence"] = float(np.nextafter(tolerance, np.inf))
    with pytest.raises(MODULE.GeometryAnalysisError, match="JS residual exceeds"):
        _validate(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("kl_baseline_to_intervened", float(np.finfo(np.float64).tiny)),
        ("total_variation", -float(np.finfo(np.float64).tiny)),
        ("logit_delta_rms", float(np.finfo(np.float32).tiny)),
        ("intervened_entropy", 2.5000001),
        ("intervened_argmax_id", 5),
        ("argmax_flip", True),
    ),
)
def test_amended_zero_gate_rejects_any_nonzero_primitive(
    field: str, value: object
) -> None:
    rows = _zero_rows()
    rows[11][field] = value
    with pytest.raises(MODULE.GeometryAnalysisError, match="Primitive zero"):
        _validate(rows)


def test_amended_zero_gate_rejects_nonzero_arrays_and_out_of_range_ids() -> None:
    arrays = _zero_arrays()
    arrays["countsketch"][3, 2] = np.finfo(np.float32).tiny
    with pytest.raises(MODULE.GeometryAnalysisError, match="array is nonzero"):
        _validate(_zero_rows(), arrays)

    arrays = _zero_arrays()
    arrays["top_positive_ids"][4, 1] = 8
    with pytest.raises(MODULE.GeometryAnalysisError, match="outside vocabulary"):
        _validate(_zero_rows(), arrays)


def test_amended_zero_gate_rejects_grid_or_frozen_identity_drift() -> None:
    rows = _zero_rows()
    rows[32]["site_index"] = 0
    with pytest.raises(MODULE.GeometryAnalysisError, match="site-major"):
        _validate(rows)

    rows = _zero_rows()
    rows[31]["target_group"] = "changed"
    with pytest.raises(MODULE.GeometryAnalysisError, match="frozen preflight"):
        _validate(rows)


def test_value_gate_never_opens_nonzero_before_amended_zero_completion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    array_path = tmp_path / "values.npy"
    np.save(array_path, np.zeros((1,), dtype=np.float32), allow_pickle=False)
    gate = MODULE.ValueOpenGateV1()

    with pytest.raises(MODULE.GeometryAnalysisError, match="not validated"):
        gate.open_jsonl(path, zero_control=True)
    gate.authorize_after_closeout_rehash(
        {
            "status": "scientific_open_closeout_audit_pass",
            "scientific_values_parsed": False,
        }
    )
    with pytest.raises(MODULE.GeometryAnalysisError, match="before the amended"):
        gate.open_jsonl(path)
    with pytest.raises(MODULE.GeometryAnalysisError, match="before the amended"):
        gate.open_array(array_path)
    assert gate.open_jsonl(path, zero_control=True) == [{}]
    gate.complete_zero_gate()
    assert gate.open_jsonl(path) == [{}]
    assert gate.trace[0] == "same_process_full_closeout_rehash_complete"
    assert gate.trace[-2] == MODULE.ZERO_RECEIPT_STATUS
    assert "exact_noop" not in MODULE.ZERO_RECEIPT_STATUS


def test_atomic_directory_publication_never_replaces_racing_empty_destination(
    tmp_path: Path,
) -> None:
    stage = tmp_path / ".analysis.stage"
    stage.mkdir()
    (stage / "complete.json").write_text('{"complete":true}\n', encoding="utf-8")
    destination = tmp_path / "analysis"

    # Simulate another process creating the destination after the caller's
    # final absence check but immediately before the atomic publication call.
    assert not destination.exists()
    destination.mkdir()
    with pytest.raises(MODULE.GeometryAnalysisError, match="Output already exists"):
        MODULE._publish_directory_no_replace(stage, destination)

    assert stage.is_dir()
    assert (stage / "complete.json").is_file()
    assert destination.is_dir()
    assert list(destination.iterdir()) == []


def test_atomic_directory_publication_exposes_complete_stage_in_one_step(
    tmp_path: Path,
) -> None:
    stage = tmp_path / ".analysis.stage"
    stage.mkdir()
    (stage / "complete.json").write_text('{"complete":true}\n', encoding="utf-8")
    destination = tmp_path / "analysis"

    MODULE._publish_directory_no_replace(stage, destination)

    assert not stage.exists()
    assert destination.is_dir()
    assert (destination / "complete.json").read_text(encoding="utf-8") == (
        '{"complete":true}\n'
    )


def test_amended_zero_receipt_names_v1_and_records_original_v0_failure() -> None:
    tolerance = float(8 * np.finfo(np.float32).eps)
    model = {
        "model": "pilot",
        "status": MODULE.ZERO_GATE_STATUS,
        "rows": 256,
        "no_claim_of_exact_js": True,
        "historical_v0_exact_js_gate": (
            "failed_closed_on_js_divergence_per_frozen_failure_receipt"
        ),
        "v0_exact_js_predicate_on_current_rows": (
            "would_fail_nonzero_roundtrip_residual"
        ),
        "js_residual": {
            "minimum": -tolerance,
            "maximum": tolerance,
            "maximum_absolute": tolerance,
            "tolerance": tolerance,
            "two_sided": True,
            "all_finite": True,
            "exact_zero_rows": 254,
            "nonzero_rows": 2,
        },
    }
    receipt = {
        "schema_version": 1,
        "amendment_id": MODULE.AMENDMENT_ID,
        "source_analysis_id": MODULE.SOURCE_ANALYSIS_ID,
        "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": MODULE.ZERO_RECEIPT_STATUS,
        "run_binding_root_sha256": "a" * 64,
        "scientific_open_receipt_sha256": "b" * 64,
        "amendment_config_sha256": MODULE.V0._sha256(
            ROOT / MODULE.AMENDMENT_CONFIG_PATH
        ),
        "amendment_freeze_manifest_sha256": "c" * 64,
        "models": [model],
        "original_v0_exact_js_gate": {
            "status": "failed",
            "failure_field": "js_divergence",
            "exact_failed_value_recorded": False,
            "failed_model_role_recorded": False,
            "authority": "frozen_v0_failure_receipt",
        },
        "v0_exact_js_predicate_on_current_rows": {
            "would_fail_model_roles": ["pilot"],
            "would_pass_model_roles": [],
        },
        "zero_phase_value_open_trace": [
            "same_process_full_closeout_rehash_complete",
            "external_scientific_open_receipt_validated",
            "zero:jsonl:synthetic",
            MODULE.ZERO_RECEIPT_STATUS,
        ],
        "scientific_values_opened_before_all_zero": False,
        "no_claim_of_exact_js": True,
    }
    result = MODULE.validate_zero_gate_receipt_v1(
        receipt,
        expected_run_binding_root_sha256="a" * 64,
        expected_scientific_open_receipt_sha256="b" * 64,
        expected_pilot_roles=["pilot"],
    )
    assert result["status"] == "zero_gate_amendment_v1_receipt_audit_pass"
    assert result["v0_exact_js_predicate_on_current_rows"] == {
        "would_fail_model_roles": ["pilot"],
        "would_pass_model_roles": [],
    }


def test_execute_orders_amendment_audit_closeout_zero_then_f4_f5_f6(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    run_root = tmp_path / "sealed-run"
    run_root.mkdir()
    preflight = tmp_path / "preflight"
    preflight.mkdir()
    receipt = tmp_path / "closeout.json"
    receipt.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "analysis"

    def amendment_audit() -> dict:
        events.append("amendment-freeze-audit")
        return {
            "status": "amendment_freeze_audit_pass",
            "amendment_id": MODULE.AMENDMENT_ID,
            "freeze_manifest_sha256": "c" * 64,
        }

    def closeout_audit(_run_root: Path, _receipt: Path) -> dict:
        events.append("full-closeout-rehash")
        return {
            "status": "scientific_open_closeout_audit_pass",
            "scientific_values_parsed": False,
        }

    def zero_gate(
        _run_root: Path,
        _pilots: list[str],
        gate: MODULE.ValueOpenGateV1,
        _preflight: Path,
    ) -> list[dict]:
        events.append("zero-values")
        gate.complete_zero_gate()
        return [
            {
                "model": "pilot",
                "status": MODULE.ZERO_GATE_STATUS,
                "rows": 256,
                "no_claim_of_exact_js": True,
                "historical_v0_exact_js_gate": (
                    "failed_closed_on_js_divergence_per_frozen_failure_receipt"
                ),
                "v0_exact_js_predicate_on_current_rows": (
                    "would_pass_all_js_exact_zero"
                ),
                "js_residual": {
                    "minimum": 0.0,
                    "maximum": 0.0,
                    "maximum_absolute": 0.0,
                    "tolerance": float(8 * np.finfo(np.float32).eps),
                    "two_sided": True,
                    "all_finite": True,
                    "exact_zero_rows": 256,
                    "nonzero_rows": 0,
                },
            }
        ]

    def f4_inputs(
        _run_root: Path, _pilots: list[str], gate: MODULE.ValueOpenGateV1
    ) -> tuple[list[dict], list[dict]]:
        assert gate.zero_gate_complete is True
        events.append("nonzero-f4")
        return [], []

    monkeypatch.setattr(MODULE, "_audit_amendment_freeze_same_process", amendment_audit)
    monkeypatch.setattr(
        MODULE,
        "_amendment_config",
        lambda: {
            "status_at_freeze": "synthetic-frozen",
            "corrected_zero_gate": {
                "js_divergence": {
                    "maximum_absolute": float(8 * np.finfo(np.float32).eps)
                }
            },
        },
    )
    monkeypatch.setattr(
        MODULE.V0,
        "_config",
        lambda: {
            "acquisition_gate": {
                "required_role_order": ["pilot"],
                "pilot_roles": ["pilot"],
            },
            "claim_boundary": "synthetic-test-only",
        },
    )
    monkeypatch.setattr(
        MODULE.V0,
        "_validate_preflight_bindings",
        lambda _directory, _roles: {"pilot": "d" * 64},
    )
    monkeypatch.setattr(MODULE.V0, "_audit_closeout_same_process", closeout_audit)
    monkeypatch.setattr(MODULE.V0, "_read_json", lambda _path: {})
    monkeypatch.setattr(
        MODULE.V0,
        "validate_scientific_open_receipt",
        lambda _receipt, _run_root: {
            "external_closeout_root_sha256": "a" * 64,
            "run_root": str(run_root),
        },
    )
    monkeypatch.setattr(MODULE.V0, "_assert_exact_tree", lambda *_args: None)
    monkeypatch.setattr(MODULE, "_zero_gate_v1", zero_gate)
    monkeypatch.setattr(MODULE.V0, "_f4_inputs", f4_inputs)
    monkeypatch.setattr(
        MODULE.V0,
        "analyze_target_sensitivity",
        lambda *_args, **_kwargs: {
            "family_id": "F4_target_sensitivity",
            "target_profiles": [],
        },
    )

    def f5(*_args: object) -> dict:
        events.append("nonzero-f5")
        return {"family_id": "F5_output_direction"}

    def f6(*_args: object) -> dict:
        events.append("nonzero-f6")
        return {"family_id": "F6_source_geometry"}

    monkeypatch.setattr(MODULE.V0, "_f5", f5)
    monkeypatch.setattr(MODULE.V0, "_f6", f6)

    result = MODULE.execute_analysis(
        run_root=run_root,
        scientific_open_receipt=receipt,
        preflight_directory=preflight,
        output_directory=output,
    )
    assert events == [
        "amendment-freeze-audit",
        "full-closeout-rehash",
        "zero-values",
        "nonzero-f4",
        "nonzero-f5",
        "nonzero-f6",
    ]
    assert result["amendment"]["freeze_audit"]["freeze_manifest_sha256"] == "c" * 64
    assert result["source_analysis_id"] == MODULE.SOURCE_ANALYSIS_ID
    assert result["no_claim_of_exact_js"] is True
    assert output.is_dir()
