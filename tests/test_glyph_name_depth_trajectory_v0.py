from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "glyph_name_depth_trajectory_v0.py"
SPEC = importlib.util.spec_from_file_location("glyph_name_depth_trajectory_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_design_binds_prior_exposed_population_and_zero_forward_budget() -> None:
    result = MODULE.audit_design()

    assert result["status"] == "design_pass_zero_t17_model_forwards"
    assert result["population_items"] == 292
    assert result["population_prior_exposed"] is True
    assert result["confirmatory_claim_authorized"] is False
    assert result["rendered_glyph_perception_claim_authorized"] is False
    assert result["model_forwards"] == 0
    assert result["model_forwards_total"] == 15_768
    assert result["readout_vectors_total"] == 567_648
    assert len(result["model_roles"]) == 9


def test_depth_resolution_is_unique_and_architecture_specific() -> None:
    assert MODULE.resolved_layers("olmo2_1b_base_bf16") == (
        0,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        15,
    )
    assert MODULE.resolved_layers("qwen25_3b_base_bf16") == (
        0,
        4,
        9,
        13,
        18,
        22,
        27,
        31,
        35,
    )
    assert MODULE.resolved_layers("llama32_3b_base_bf16") == (
        0,
        3,
        7,
        10,
        14,
        17,
        21,
        24,
        27,
    )
    for role in MODULE.MODEL_ROLES:
        assert len(set(MODULE.resolved_layers(role))) == 9


def test_pair_metrics_recover_exact_item_correspondence() -> None:
    rng = np.random.default_rng(7)
    values = rng.normal(size=(16, 12))
    exact, correctness = MODULE._pair_metrics(values, values.copy())
    shuffled, shuffled_correctness = MODULE._pair_metrics(
        values, np.roll(values, 1, axis=0)
    )

    assert exact["top1_accuracy_forward"] == 1.0
    assert exact["top1_accuracy_reverse"] == 1.0
    assert np.all(correctness == 1.0)
    assert shuffled["top1_accuracy_forward"] == 0.0
    assert np.all(shuffled_correctness == 0.0)
    assert (
        exact["paired_minus_off_diagonal_margin"]
        > shuffled["paired_minus_off_diagonal_margin"]
    )
    assert exact["centered_linear_cka"] == pytest.approx(1.0)


def test_bootstrap_is_deterministic_and_tracks_constant_columns() -> None:
    values = np.column_stack(
        (
            np.ones(20, dtype=np.float64),
            np.zeros(20, dtype=np.float64),
            np.linspace(-1.0, 1.0, 20),
        )
    )
    first = MODULE._bootstrap_intervals(values, 199, 31)
    second = MODULE._bootstrap_intervals(values, 199, 31)

    assert first == second
    assert first[0] == [1.0, 1.0]
    assert first[1] == [0.0, 0.0]
    assert first[2][0] < 0.0 < first[2][1]


def test_registered_trajectory_summaries_are_not_outcome_adaptive() -> None:
    rows = []
    for index, depth in enumerate(MODULE.DEPTH_FRACTIONS):
        value = -0.02 if index < 3 else 0.01 * (index - 2)
        rows.append(
            {
                "normalized_depth": depth,
                "headline_top1_contrast_mean": value,
                "bootstrap_95_percent_interval": [value - 0.005, value + 0.005],
            }
        )
    summary = MODULE._trajectory_summary(rows)

    assert summary["earliest_sustained_positive_point_estimate_depth"] == 0.375
    assert summary["earliest_sustained_positive_bootstrap_interval_depth"] == 0.375
    assert summary["peak_normalized_depth"] == 1.0
    assert summary["positive_depth_count"] == 6


def test_config_blocks_semantic_and_confirmatory_reinterpretation() -> None:
    config = MODULE._config()
    forbidden = set(config["forbidden_actions"])

    assert (
        config["population"]["inferential_role"]
        == "fixed_prior_exposed_exploratory_population"
    )
    assert config["analysis"]["multiplicity"] == "none_exploratory_descriptive_atlas"
    assert (
        config["analysis"]["outcome_adaptive_depth_or_model_selection"] == "forbidden"
    )
    assert "reinterpretation_as_rendered_font_glyph_perception" in forbidden
    assert (
        "reinterpretation_as_new_item_confirmation_or_independent_replication"
        in forbidden
    )
    assert "raw_activation_commit_to_git" in forbidden


def test_freeze_audits_if_manifest_exists() -> None:
    if (ROOT / MODULE.FREEZE_PATH).is_file():
        assert MODULE.audit_freeze()["status"] == "pass"
