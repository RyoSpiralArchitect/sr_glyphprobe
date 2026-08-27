from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_multifamily_matched_slot_geometry_v0_repair_v1.py"
SPEC = importlib.util.spec_from_file_location("matched_slot_analysis_repair_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_yaml_null_key_reproduces_the_serialization_root_cause() -> None:
    config = yaml.safe_load(
        (ROOT / "configs" / "multifamily_matched_slot_geometry_v0.yaml").read_text()
    )
    endpoint = config["primary_endpoint"]
    assert None in endpoint
    assert endpoint[None] == "independent_within_family_slot_label_permutation"


def test_normalizer_changes_only_none_mapping_keys() -> None:
    source = {
        "alpha": 0.05,
        None: "independent_within_family_slot_label_permutation",
        "nested": [{"seed": 20260828, "draws": 19999}],
    }
    normalized = MODULE.normalize_json_mapping_keys(source)
    assert normalized == {
        "alpha": 0.05,
        "null": "independent_within_family_slot_label_permutation",
        "nested": [{"seed": 20260828, "draws": 19999}],
    }
    assert source[None] == normalized["null"]
    assert source["alpha"] == normalized["alpha"]


def test_normalizer_rejects_other_non_string_keys_and_collisions() -> None:
    with pytest.raises(MODULE.frozen.base.ProtocolError, match="Unsupported"):
        MODULE.normalize_json_mapping_keys({1: "not authorized"})
    with pytest.raises(MODULE.frozen.base.ProtocolError, match="collision"):
        MODULE.normalize_json_mapping_keys({None: "left", "null": "right"})


def test_failure_receipt_binds_both_unmodified_runs_before_repair() -> None:
    receipt = json.loads(
        (
            ROOT
            / "validation"
            / "multifamily_matched_slot_geometry_v0"
            / "analysis_attempt_01_failure.json"
        ).read_text()
    )
    assert receipt["status"] == "failed_before_publication"
    assert receipt["output_directory_published"] is False
    assert receipt["analysis_values_inspected"] is False
    assert receipt["scientific_result_available"] is False
    assert set(receipt["bound_inputs"]) == set(MODULE.frozen.MODEL_ROLES)
    assert all(set(files) == set(MODULE.INPUT_FILES) for files in receipt["bound_inputs"].values())


def test_repair_manifest_changes_serialization_only() -> None:
    manifest = json.loads((ROOT / MODULE.REPAIR_MANIFEST_PATH).read_text())
    assert manifest["repair_id"] == MODULE.REPAIR_ID
    assert manifest["change_scope"] == "json_mapping_key_normalization_only"
    assert manifest["scientific_choices_changed"] is False
    assert manifest["frozen_statistics_changed"] is False
    assert manifest["input_runs"] == json.loads(
        (
            ROOT
            / "validation"
            / "multifamily_matched_slot_geometry_v0"
            / "analysis_attempt_01_failure.json"
        ).read_text()
    )["bound_inputs"]


def test_wrapper_delegates_to_frozen_analyzer_and_keeps_choices_immutable() -> None:
    source = SCRIPT.read_text()
    assert "frozen.analyze_runs(run_directories, output)" in source
    assert "normalize_json_mapping_keys" in source
    for forbidden in (
        "randomization_draws =",
        "randomization_seed =",
        "familywise_alpha =",
        "synchronized_slot_randomization(",
        "factor_geometry(",
        "holm_adjust(",
    ):
        assert forbidden not in source


def test_repair_freeze_audit_passes() -> None:
    audit = MODULE.audit_repair(ROOT)
    assert audit["status"] == "pass"
    assert audit["repair_id"] == MODULE.REPAIR_ID
    assert audit["scientific_choices_changed"] is False
