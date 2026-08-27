from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_matched_slot_geometry_v0.py"
SPEC = importlib.util.spec_from_file_location("multifamily_matched_slot_geometry_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@dataclass
class Tokenized:
    token_ids: list[int]
    tokens: list[str]


def _config() -> dict:
    return yaml.safe_load(
        (ROOT / "configs" / "multifamily_matched_slot_geometry_v0.yaml").read_text()
    )


def _panel() -> list[dict]:
    return MODULE._load_panel(ROOT, _config())


def test_frozen_config_declares_all_depth_omnibus_and_two_model_holm_family() -> None:
    config = _config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["layers"]["fractions"] == [0.0, 0.25, 0.5, 0.75, 1.0]
    endpoint = config["primary_endpoint"]
    assert endpoint["id"] == "all_depth_matched_slot_fraction_after_family_centering"
    assert endpoint["randomization_draws"] == 19999
    assert endpoint["seed"] == 20260828
    assert endpoint["synchronized_across_depths"] is True
    assert endpoint["multiplicity"] == "holm"
    assert endpoint["hypothesis_family"] == list(MODULE.MODEL_ROLES)
    assert endpoint["decision_scope"] == "model_level_all_depth_omnibus_only"


def test_panel_is_complete_ordered_factorial_with_matched_low_bits() -> None:
    config = _config()
    panel = _panel()
    families = config["panel"]["family_order"]
    slots = config["panel"]["slot_order"]
    assert len(panel) == 50
    assert [row["id"] for row in panel] == [
        f"{family}_slot_{slot:02d}" for family in families for slot in slots
    ]
    for slot in slots:
        rows = [row for row in panel if row["factors"]["matched_slot"] == f"slot_{slot:02d}"]
        assert len(rows) == 5
        assert len({ord(row["glyph"]) & 0x3F for row in rows}) == 1
        assert all(len(row["glyph"]) == 1 for row in rows)


def test_distinct_atomic_token_contract_accepts_exactly_fifty_unique_tokens() -> None:
    panel = _panel()
    spec = _config()["models"]["gemma2_2b_4bit"]
    rows = [Tokenized([1000 + index], [row["glyph"]]) for index, row in enumerate(panel)]
    receipt = MODULE.validate_tokenization_matrix(rows, panel, spec)
    assert receipt["kind"] == "distinct_atomic_tokens"
    assert receipt["observed_item_token_counts"] == [1]
    assert receipt["unique_sequence_count"] == 50
    assert receipt["minimum_shared_prefix_across_panel"] == 0


def test_distinct_atomic_token_contract_rejects_duplicate_sequence() -> None:
    panel = _panel()
    spec = _config()["models"]["gemma2_2b_4bit"]
    rows = [Tokenized([1000 + index], [row["glyph"]]) for index, row in enumerate(panel)]
    rows[-1] = Tokenized(rows[0].token_ids, [panel[-1]["glyph"]])
    with pytest.raises(MODULE.base.ProtocolError, match="Unique token-sequence"):
        MODULE.validate_tokenization_matrix(rows, panel, spec)


def test_olmo_token_contract_is_exact_prefix_family_slot_factorization() -> None:
    panel = _panel()
    spec = _config()["models"]["olmo3_7b_bf16"]
    contract = spec["tokenization_contract"]
    rows = []
    for item in panel:
        family = item["factors"]["family"]
        slot = int(item["factors"]["matched_slot"].removeprefix("slot_"))
        ids = [
            contract["shared_prefix_token_id"],
            contract["family_token_ids"][family],
            contract["slot_token_ids"][slot],
        ]
        rows.append(Tokenized(ids, [str(value) for value in ids]))
    receipt = MODULE.validate_tokenization_matrix(rows, panel, spec)
    assert receipt["kind"] == "exact_prefix_family_slot_factorization"
    assert receipt["observed_item_token_counts"] == [3]
    assert receipt["minimum_shared_prefix_across_panel"] == 1
    assert len({tuple(row) for row in receipt["token_sequences"]}) == 50


def test_olmo_token_contract_rejects_wrong_family_or_slot_token() -> None:
    panel = _panel()
    spec = _config()["models"]["olmo3_7b_bf16"]
    contract = spec["tokenization_contract"]
    rows = []
    for item in panel:
        family = item["factors"]["family"]
        slot = int(item["factors"]["matched_slot"].removeprefix("slot_"))
        rows.append(
            Tokenized(
                [9468, contract["family_token_ids"][family], contract["slot_token_ids"][slot]],
                [],
            )
        )
    rows[11] = Tokenized([9468, 999, 240], [])
    with pytest.raises(MODULE.base.ProtocolError, match="Exact token factorization"):
        MODULE.validate_tokenization_matrix(rows, panel, spec)


def test_factor_geometry_recovers_additive_family_and_slot_structure() -> None:
    rng = np.random.default_rng(31)
    family = rng.normal(size=(5, 1, 7))
    slot = rng.normal(size=(1, 10, 7))
    values = family + slot
    result = MODULE.factor_geometry(values)
    assert result["slot_fraction_after_family_centering"] == pytest.approx(1.0)
    assert result["family_fraction_after_slot_centering"] == pytest.approx(1.0)
    assert result["ss_interaction"] == pytest.approx(0.0, abs=1e-20)
    assert result["ss_total"] == pytest.approx(
        result["ss_family"] + result["ss_slot"] + result["ss_interaction"]
    )


def test_factor_geometry_detects_interaction_without_changing_decomposition() -> None:
    rng = np.random.default_rng(41)
    values = rng.normal(size=(5, 10, 9))
    result = MODULE.factor_geometry(values)
    assert 0.0 <= result["slot_fraction_after_family_centering"] <= 1.0
    assert 0.0 <= result["family_fraction_after_slot_centering"] <= 1.0
    assert 0.0 <= result["interaction_fraction_of_total"] <= 1.0
    assert result["ss_total"] == pytest.approx(
        result["ss_family"] + result["ss_slot"] + result["ss_interaction"]
    )


def test_synchronized_randomization_is_deterministic_and_uses_all_depths() -> None:
    rng = np.random.default_rng(51)
    family = rng.normal(size=(5, 1, 1, 6))
    slot = rng.normal(size=(1, 10, 1, 6))
    depth_scale = np.asarray([0.8, 1.0, 1.2])
    tensor = family + slot * depth_scale[None, None, :, None]
    first = MODULE.synchronized_slot_randomization(tensor, draws=199, seed=77)
    second = MODULE.synchronized_slot_randomization(tensor, draws=199, seed=77)
    assert first == second
    assert first["observed_depth_profile"] == pytest.approx([1.0, 1.0, 1.0])
    assert first["observed_omnibus"] == pytest.approx(1.0)
    assert first["omnibus_excess_over_null_mean"] > 0
    assert first["omnibus_p_greater_equal"] == pytest.approx(1 / 200)
    assert len(first["per_depth_p_greater_equal"]) == 3


def test_outcome_registry_is_total_for_predeclared_branches() -> None:
    config = _config()
    registry = config["outcome_pattern_registry"]
    assert set(registry) == {
        "dual_model_slot_recurrence_candidate",
        "gemma_only_heterogeneity",
        "olmo_only_token_structured_recurrence",
        "opposite_null_centered_direction",
        "no_dual_model_slot_recurrence",
    }
    primary = {
        MODULE.MODEL_ROLES[0]: {"excess_over_null_mean": 0.1, "holm_reject": True},
        MODULE.MODEL_ROLES[1]: {"excess_over_null_mean": 0.2, "holm_reject": True},
    }
    assert MODULE._outcome_pattern(primary) == "dual_model_slot_recurrence_candidate"
    primary[MODULE.MODEL_ROLES[1]]["holm_reject"] = False
    assert MODULE._outcome_pattern(primary) == "gemma_only_heterogeneity"
    primary[MODULE.MODEL_ROLES[0]]["holm_reject"] = False
    primary[MODULE.MODEL_ROLES[1]]["holm_reject"] = True
    assert MODULE._outcome_pattern(primary) == "olmo_only_token_structured_recurrence"
    primary[MODULE.MODEL_ROLES[0]]["excess_over_null_mean"] = -0.1
    assert MODULE._outcome_pattern(primary) == "opposite_null_centered_direction"


def test_protocol_forbids_intervention_generation_target_access_and_layer_fishing() -> None:
    config = _config()
    assert set(config["forbidden_actions"]) == {
        "activation_intervention",
        "behavioral_generation",
        "protected_target_access",
        "post_outcome_layer_family_endpoint_or_seed_selection",
        "direct_cross_model_effect_magnitude_comparison",
    }
    source = SCRIPT.read_text()
    assert "intervention_calls\": 0" in source
    assert "generation_calls\": 0" in source
    assert "protected_target_files_opened\": 0" in source
    assert "multiplicity_decision_authorized\": False" in source


def test_manifest_binds_protocol_assets_and_model_artifacts() -> None:
    manifest_path = ROOT / MODULE.MANIFEST_PATH
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert set(manifest["model_artifacts"]) == set(MODULE.MODEL_ROLES)
    assert manifest["static_counts"]["panel_items"] == 50
    assert manifest["static_counts"]["randomization_draws_per_model"] == 19999
    audit = MODULE.audit_freeze(ROOT)
    assert audit["status"] == "pass"
    assert audit["model_roles"] == list(MODULE.MODEL_ROLES)
