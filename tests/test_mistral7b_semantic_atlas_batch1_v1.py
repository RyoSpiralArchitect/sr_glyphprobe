from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mistral7b_semantic_atlas_batch1_v1.py"
SPEC = importlib.util.spec_from_file_location("mistral7b_semantic_atlas_batch1_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_merged_config_changes_only_operational_batch_contract() -> None:
    config = MODULE.merged_config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["storage"]["batch_size_unique_sequences"] == 1
    assert config["storage"]["expected_acquired_items"] == 892
    assert config["storage"]["expected_unique_input_sequences"] == 5352
    assert config["storage"]["expected_readout_vectors"] == 192672
    assert config["input"]["fused_distance_readout"] is True
    assert config["layers"]["expected_resolved_layers"] == [0, 4, 8, 12, 16, 20, 24, 28, 31]


def test_source_failure_is_bound_and_reserve_was_not_opened() -> None:
    receipt = json.loads(
        (
            ROOT
            / "validation/mistral7b_semantic_atlas_v0/capture_validation_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "validation_failed"
    assert receipt["case_count"] == 18
    assert receipt["passed_case_count"] == 0
    assert receipt["reserve_forward_calls"] == 0


def test_delegated_surface_restores_v0_authority() -> None:
    original = (MODULE.v0.PROTOCOL_ID, MODULE.v0.CONFIG_PATH, MODULE.v0.FREEZE_PATH)
    with MODULE._delegated_surface():
        assert MODULE.v0.PROTOCOL_ID == MODULE.PROTOCOL_ID
        assert MODULE.v0.CONFIG_PATH == MODULE.CONFIG_PATH
        assert MODULE.v0.FREEZE_PATH == MODULE.FREEZE_PATH
    assert (MODULE.v0.PROTOCOL_ID, MODULE.v0.CONFIG_PATH, MODULE.v0.FREEZE_PATH) == original


def test_v1_freeze_audit_when_manifest_exists() -> None:
    if (ROOT / MODULE.FREEZE_PATH).is_file():
        assert MODULE.audit_freeze()["status"] == "pass"
