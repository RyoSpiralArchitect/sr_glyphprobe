from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mistral7b_semantic_atlas_reserve_confirmation_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "semantic_atlas_reserve_confirmation", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_reserve_population_is_complete_deterministic_and_still_unacquired() -> None:
    items = MODULE.confirmation_items()

    assert len(items) == 292
    assert [item["confirmation_index"] for item in items] == list(range(292))
    assert [item["source_index"] for item in items] == sorted(
        item["source_index"] for item in items
    )
    assert {item["role"] for item in items} == {"reserved_unrun"}
    assert all(item["acquisition_index"] is None for item in items)
    assert all(item["included_in_acquisition"] is False for item in items)


def test_single_primary_family_and_acquisition_budget_are_fixed() -> None:
    config = MODULE._config()
    primary = config["primary_endpoint"]
    acquisition = config["acquisition"]

    assert acquisition["layers"] == [31]
    assert acquisition["batch_size_unique_sequences"] == 1
    assert acquisition["expected_shards"] == 10
    assert acquisition["expected_model_forward_calls"] == 1752
    assert acquisition["expected_readout_vectors"] == 7008
    assert primary["cells"] == "complete_two_carrier_by_four_distance_grid"
    assert primary["statistic"] == (
        "minimum_over_eight_cells_of_glyph_name_top1_minus_glyph_codepoint_top1"
    )
    assert primary["practical_minimum"] == 0.02
    assert primary["randomization_seed"] == 20260828
    assert primary["randomization_draws"] == 19999
    assert primary["alpha"] == 0.05
    assert primary["multiplicity"] == "none_single_global_minimum_statistic"


def test_discovery_basis_reconstructs_from_published_complete_cells() -> None:
    result = MODULE.audit_design_basis()

    assert result["status"] == "pass"
    assert result["cell_count"] == 8
    assert result["observed_minimum_cell_contrast"] == pytest.approx(
        0.08076009538490325
    )
    assert result["observed_equal_cell_mean_contrast"] == pytest.approx(
        0.13539192931784783
    )
    assert result["reserve_items"] == 292
    assert result["reserve_model_inputs_forwarded"] == 0


def test_primary_randomization_is_deterministic_and_conjunctive() -> None:
    item_count = 12
    order = np.arange(item_count, dtype=np.int64)
    name = np.tile(order, (8, 1))
    codepoint = np.tile(np.roll(order, 1), (8, 1))

    one = MODULE.primary_randomization_test(
        name,
        codepoint,
        draws=99,
        seed=17,
        alpha=0.05,
        practical_minimum=0.02,
    )
    two = MODULE.primary_randomization_test(
        name,
        codepoint,
        draws=99,
        seed=17,
        alpha=0.05,
        practical_minimum=0.02,
    )

    assert one == two
    assert one["observed_minimum_cell_contrast"] == 1.0
    assert one["p_value"] == 0.01
    assert one["alignment_confirmed"] is True
    assert one["outcome_pattern"] == (
        "transport_robust_late_depth_glyph_name_alignment_confirmed"
    )

    name[7] = codepoint[7]
    failed = MODULE.primary_randomization_test(
        name,
        codepoint,
        draws=99,
        seed=17,
        alpha=0.05,
        practical_minimum=0.02,
    )
    assert failed["observed_minimum_cell_contrast"] == 0.0
    assert failed["alignment_confirmed"] is False
    assert failed["outcome_pattern"] == "not_confirmed_under_frozen_rule"
    assert failed["t8_reserve_question_closed"] is True


@pytest.mark.skipif(
    not __import__("torch").cuda.is_available(), reason="CUDA-only cell metric test"
)
def test_cell_metric_retrieves_identical_name_geometry() -> None:
    import torch

    rng = np.random.default_rng(7)
    glyph = rng.normal(size=(12, 32)).astype(np.float32)
    values = np.stack([glyph, glyph, np.roll(glyph, 1, axis=0)], axis=0)

    metrics, name_prediction, codepoint_prediction = MODULE._cell_metrics(torch, values)

    np.testing.assert_array_equal(name_prediction, np.arange(12))
    assert metrics["pairs"]["glyph_name"]["top1_accuracy_forward"] == 1.0
    assert metrics["pairs"]["glyph_name"]["centered_linear_cka"] == pytest.approx(1.0)
    assert np.mean(codepoint_prediction == np.arange(12)) == 0.0


def test_freeze_audits_when_manifest_exists() -> None:
    if (ROOT / MODULE.FREEZE_PATH).is_file():
        assert MODULE.audit_freeze()["status"] == "pass"


def test_claim_boundary_forbids_semantic_and_post_outcome_rescue() -> None:
    config = MODULE._config()
    forbidden = set(config["forbidden_actions"])

    assert "reserve_forward_before_freeze_commit" in forbidden
    assert "reserve_item_replacement_or_exclusion" in forbidden
    assert (
        "alternate_layer_carrier_distance_or_metric_selection_after_outcome"
        in forbidden
    )
    assert "threshold_or_random_seed_change_after_outcome" in forbidden
    assert "semantic_causal_mechanistic_behavioral_or_model_general_claim" in forbidden
    assert config["secondary_outputs"]["decision_authorized"] is False
