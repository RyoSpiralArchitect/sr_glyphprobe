from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_semantic_atlas_cross_model_diagnostics_v1.py"
BUNDLE = ROOT / "artifacts" / "semantic_atlas_cross_model_diagnostics_v1"
EXPECTED_DIAGNOSTICS_SHA256 = (
    "6f5e42643b9fcfe0c444f2ef8aecd4ed4df6fa3dd4e10de08f11856971acc990"
)
SPEC = importlib.util.spec_from_file_location("t10_diagnostics_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_committed_diagnostic_bundle_validates_and_binds_implementation() -> None:
    result = MODULE.validate_bundle(BUNDLE)
    payload = json.loads((BUNDLE / "diagnostics.json").read_text(encoding="utf-8"))

    assert result == {
        "status": "pass",
        "ledger_targets_rehashed": 2,
        "raw_archive_validated": True,
        "registered_primary_unchanged": True,
    }
    assert MODULE.sha256(BUNDLE / "diagnostics.json") == EXPECTED_DIAGNOSTICS_SHA256
    assert payload["implementation_script_sha256"] == MODULE.sha256(SCRIPT)
    assert payload["t10_primary_changed"] is False
    assert payload["t10_rescue_authorized"] is False


def test_committed_diagnostics_retain_the_registered_negative_and_raw_reconstruction() -> None:
    payload = json.loads((BUNDLE / "diagnostics.json").read_text(encoding="utf-8"))
    primary = payload["compact_diagnostics"]["registered_primary_unchanged"]
    raw = payload["raw_diagnostics"]["raw_archive_validation"]

    assert primary["authorized_wording"] == (
        "cross_model_replication_not_established_under_frozen_rule"
    )
    assert primary["partial_conjunction_p_value"] == 0.0001
    assert primary["core_practical_pass_count"] == 2
    assert primary["floor_as_net_correct_items_at_n_292"] == 6
    assert raw["shards"] == 333
    assert raw["prediction_arrays_reconstructed"] == 36
    assert raw["prediction_mismatches"] == 0
    assert raw["maximum_top1_contrast_absolute_error"] < 2e-8


def test_diagnostics_support_the_continuous_t11_design_motivation() -> None:
    payload = json.loads((BUNDLE / "diagnostics.json").read_text(encoding="utf-8"))
    compact = payload["compact_diagnostics"]
    geometry = payload["raw_diagnostics"]["cross_model_item_geometry"]

    assert compact["carrier_distance_heterogeneity"]["cross_model_profile_spearman"]["median"] < 0
    assert compact["item_support"]["items_hit_by_at_least_one_model"] == 233
    assert compact["item_support"]["items_hit_by_all_nine_models"] == 0
    assert compact["name_vs_codepoint"]["codepoint_zero_cells"] == 13
    assert compact["metric_convergence_and_divergence"]["all_72_margin_contrasts_positive"] is True
    assert geometry["glyph_final"]["pair_medians_over_eight_contexts"]["median"] < (
        geometry["unicode_name_final"]["pair_medians_over_eight_contexts"]["median"]
    )


def test_metric_helpers_are_deterministic_on_synthetic_values() -> None:
    left = np.eye(6, dtype=np.float64)
    right = np.roll(left, 1, axis=0)
    same = MODULE.retrieval_metrics(left, left)
    shifted = MODULE.retrieval_metrics(left, right)

    assert same["top1"] == 1.0
    assert shifted["top1"] == 0.0
    assert MODULE.linear_cka(left, left) == 1.0
    assert MODULE.safe_spearman([1, 2, 3], [3, 2, 1]) == -1.0
    shares = MODULE.anova_profile_shares([1, 2, 3, 4, 2, 3, 4, 5])
    assert np.isclose(sum(shares.values()), 1.0)
