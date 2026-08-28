from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mistral7b_base_depth_distance_v0.py"
SPEC = importlib.util.spec_from_file_location("mistral7b_base_depth_distance_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _config() -> dict:
    return yaml.safe_load((ROOT / MODULE.CONFIG_PATH).read_text(encoding="utf-8"))


def test_config_freezes_one_unseen_base_cell_and_depth_interaction() -> None:
    config = _config()
    endpoint = config["primary_endpoint"]
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["models"]["order"] == list(MODULE.MODEL_ROLES)
    assert len(config["models"][MODULE.MODEL_ROLES[0]]["expected_artifact_files"]) == 12
    assert config["selection_provenance"]["selected_after_t6_outcomes_were_known"] is True
    assert config["selection_provenance"]["scientific_confirmation"] is False
    assert config["layers"]["expected_resolved_layers"] == [0, 8, 16, 24, 31]
    assert endpoint["id"] == "distance1_recurrence_intersection_early_minus_late_attenuation"
    assert endpoint["distance_contrast_weights"] == [0.375, 0.125, -0.125, -0.375]
    assert endpoint["early_depth_index"] == 0
    assert endpoint["late_depth_indices"] == [1, 2, 3, 4]
    assert endpoint["randomization_draws"] == 19999
    assert endpoint["hypothesis_family"] == list(MODULE.MODEL_ROLES)
    assert endpoint["multiplicity"] == "none_one_model_one_intersection_union_test"


def test_panel_is_the_unchanged_five_by_ten_roster() -> None:
    config = _config()
    panel = MODULE._panel(config)
    assert len(panel) == 50
    assert [item["id"] for item in panel] == [
        f"{family}_slot_{slot:02d}"
        for family in config["panel"]["family_order"]
        for slot in config["panel"]["slot_order"]
    ]


def _synthetic_depth_signal() -> np.ndarray:
    rng = np.random.default_rng(42)
    shared = rng.normal(size=(10, 48))
    interaction = rng.normal(scale=0.55, size=(5, 10, 48))
    tensor = np.empty((5, 10, 2, 4, 5, 48), dtype=np.float64)
    early_scale = [4.0, 2.8, 1.6, 0.7]
    late_scale = [1.5, 1.5, 1.5, 1.5]
    for family in range(5):
        for slot in range(10):
            for carrier in range(2):
                for distance in range(4):
                    for depth in range(5):
                        scale = early_scale[distance] if depth == 0 else late_scale[distance]
                        tensor[family, slot, carrier, distance, depth] = (
                            scale * shared[slot] + interaction[family, slot]
                        )
    return tensor


def test_depth_interaction_statistic_is_fixed_deterministic_and_positive() -> None:
    kwargs = {
        "weights": [0.375, 0.125, -0.125, -0.375],
        "early_depth_index": 0,
        "late_depth_indices": [1, 2, 3, 4],
        "draws": 99,
        "seed": 987,
    }
    first = MODULE.depth_distance_randomization(_synthetic_depth_signal(), **kwargs)
    second = MODULE.depth_distance_randomization(_synthetic_depth_signal(), **kwargs)
    assert first["early_attenuation"] > first["late_mean_attenuation"]
    assert first["early_minus_late_attenuation_component"]["statistic"] > 0
    assert first["depth_distance_profile"] .shape == (5, 4)
    assert first["distance_profile"].shape == (4,)
    assert first["intersection_union_raw_p"] == pytest.approx(
        max(
            first["distance1_recurrence_component"]["raw_p"],
            first["early_minus_late_attenuation_component"]["raw_p"],
        )
    )
    assert first["intersection_union_raw_p"] == second["intersection_union_raw_p"]
    assert np.array_equal(first["null_profile_mean"], second["null_profile_mean"])


def test_depth_interaction_rejects_any_post_freeze_depth_reselection() -> None:
    with pytest.raises(MODULE.base.ProtocolError, match="Late depths"):
        MODULE.depth_distance_randomization(
            _synthetic_depth_signal(),
            weights=[0.375, 0.125, -0.125, -0.375],
            early_depth_index=0,
            late_depth_indices=[2, 3, 4],
            draws=9,
            seed=1,
        )


def test_outcome_registry_exhausts_the_two_component_truth_table() -> None:
    def primary(recurrence_p: float, interaction_p: float) -> dict:
        return {
            "distance1_recurrence_component": {"raw_p": recurrence_p},
            "early_minus_late_attenuation_component": {"raw_p": interaction_p},
        }

    assert MODULE._outcome_pattern(primary(0.01, 0.02), alpha=0.05) == (
        "recurrence_and_early_depth_attenuation_excess"
    )
    assert MODULE._outcome_pattern(primary(0.01, 0.20), alpha=0.05) == (
        "recurrence_without_early_depth_attenuation_excess"
    )
    assert MODULE._outcome_pattern(primary(0.20, 0.01), alpha=0.05) == (
        "early_depth_attenuation_excess_without_recurrence"
    )
    assert MODULE._outcome_pattern(primary(0.20, 0.20), alpha=0.05) == (
        "neither_primary_component"
    )


def test_delegated_surface_restores_t6_authority() -> None:
    names = ("PROTOCOL_ID", "SCHEMA_VERSION", "MANIFEST_PATH", "CONFIG_PATH", "PREFLIGHT_PATH", "MODEL_ROLES")
    before = {name: getattr(MODULE.t6, name) for name in names}
    with MODULE._delegated_t6_surface():
        assert MODULE.t6.PROTOCOL_ID == MODULE.PROTOCOL_ID
        assert MODULE.t6.MODEL_ROLES == MODULE.MODEL_ROLES
    assert {name: getattr(MODULE.t6, name) for name in names} == before


def test_protocol_forbids_intervention_confirmation_and_tuning_claims() -> None:
    config = _config()
    forbidden = set(config["forbidden_actions"])
    assert "activation_intervention" in forbidden
    assert "behavioral_generation" in forbidden
    assert "protected_target_access" in forbidden
    assert "instruction_tuning_effect_claim" in forbidden
    assert "independent_confirmation_claim" in forbidden
    assert "inferential_pooling_with_t6" in forbidden
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"intervention_calls": 0' in source
    assert '"generation_calls": 0' in source
    assert '"protected_target_files_opened": 0' in source
    assert '"multiplicity_decision_authorized": False' in source
