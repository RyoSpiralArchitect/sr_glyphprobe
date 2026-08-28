from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mistral7b_semantic_atlas_v0.py"
SPEC = importlib.util.spec_from_file_location("mistral7b_semantic_atlas_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _config() -> dict:
    return yaml.safe_load((ROOT / MODULE.CONFIG_PATH).read_text(encoding="utf-8"))


def test_fixed_high_n_grid_and_fused_readout_contract() -> None:
    config = _config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["selection"]["expected_total_candidates"] == 1184
    assert config["selection"]["expected_calibration_prior_exposed"] == 50
    assert config["selection"]["expected_discovery_unseen"] == 842
    assert config["selection"]["expected_reserved_unrun"] == 292
    assert config["views"]["order"] == list(MODULE.VIEW_ORDER)
    assert config["input"]["distance_order"] == [1, 2, 4, 8]
    assert config["layers"]["expected_resolved_layers"] == [0, 4, 8, 12, 16, 20, 24, 28, 31]
    assert config["storage"]["expected_acquired_items"] == 892
    assert config["storage"]["expected_shards"] == 28
    assert config["storage"]["expected_unique_input_sequences"] == 892 * 3 * 2
    assert config["storage"]["expected_readout_vectors"] == 892 * 3 * 2 * 4 * 9
    assert config["execution_policy"]["one_forward_per_unique_view_carrier_sequence"] is True
    assert config["input"]["fused_distance_readout"] is True


def test_hash_split_is_stable_and_e1_always_calibration() -> None:
    namespace = "glyphprobe-t8-v0"
    assert MODULE._role("1F351", True, namespace) == "calibration_prior_exposed"
    assert MODULE._role("1F600", False, namespace) in {"discovery_unseen", "reserved_unrun"}
    assert MODULE._role("1F600", False, namespace) == MODULE._role("1F600", False, namespace)


def test_layer_resolution_matches_frozen_mistral_depths() -> None:
    fractions = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
    assert MODULE._resolve_layers(32, fractions) == [0, 4, 8, 12, 16, 20, 24, 28, 31]


def test_selection_and_preflight_are_zero_forward_and_reserve_is_unrun() -> None:
    selection_path = ROOT / MODULE.SELECTION_PATH
    preflight_path = ROOT / MODULE.PREFLIGHT_PATH
    if not selection_path.is_file() or not preflight_path.is_file():
        return
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    assert selection["model_forward_calls"] == 0
    assert selection["model_weights_loaded"] is False
    assert selection["role_counts"] == {
        "calibration_prior_exposed": 50,
        "discovery_unseen": 842,
        "reserved_unrun": 292,
    }
    acquired = [row for row in selection["candidates"] if row["included_in_acquisition"]]
    reserved = [row for row in selection["candidates"] if row["role"] == "reserved_unrun"]
    assert [row["acquisition_index"] for row in acquired] == list(range(892))
    assert all(row["acquisition_index"] is None for row in reserved)
    assert preflight["model_forward_calls"] == 0
    assert preflight["model_weights_loaded"] is False
    assert preflight["reserved_unrun_model_inputs_forwarded"] == 0


def test_protocol_forbids_reserve_forward_and_semantic_claim() -> None:
    forbidden = set(_config()["forbidden_actions"])
    assert "reserved_unrun_model_forward" in forbidden
    assert "outcome_guided_item_view_carrier_distance_layer_or_shard_selection" in forbidden
    assert "semantic_or_tokenizer_causal_claim_from_acquisition_alone" in forbidden
    assert "confirmatory_or_phase_i_gate_claim" in forbidden


def test_freeze_audit_when_manifest_exists() -> None:
    if (ROOT / MODULE.FREEZE_PATH).is_file():
        assert MODULE.audit_freeze()["status"] == "pass"
