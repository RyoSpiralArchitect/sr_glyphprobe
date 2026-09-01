from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import fresh_composite_glyph_lexical_confirmation_v0 as t18  # noqa: E402
import validate_fresh_composite_glyph_lexical_confirmation_v0_result as independent  # noqa: E402


def test_frozen_population_contract() -> None:
    audit = t18.audit_selection(rescan_exposure=False)
    assert audit["status"] == "pass"
    assert audit["items"] == 192
    assert audit["model_forward_calls"] == 0
    rows = t18.items()
    assert Counter(row["glyph_system"] for row in rows) == {
        "modifier": 64,
        "zwj": 96,
        "regional_flag": 32,
    }
    assert [row["selection_index"] for row in rows] == list(range(192))
    for view in t18.VIEW_ORDER:
        assert len({row[view] for row in rows}) == 192
    families = {
        (row["glyph_system"], row["canonical_family_codepoint"]) for row in rows
    }
    assert len(families) == 192


def test_population_excludes_complete_t11_selection() -> None:
    old = json.loads(
        (
            ROOT / "data/manifests/glyph_system_decomposition_selection_v0.json"
        ).read_text()
    )
    old_codepoints = {row["codepoint"] for row in old["items"]}
    assert not old_codepoints.intersection(row["codepoint"] for row in t18.items())
    assert all(row["identity_in_t11_selection"] is False for row in t18.items())
    assert all(
        row["exact_surface_hit_count_in_exposure_tree"] == 0 for row in t18.items()
    )


def test_config_budgets_and_primary_window() -> None:
    config = t18._config()
    assert tuple(config["models"]["order"]) == t18.MODEL_ROLES
    assert tuple(config["models"]["core_order"]) == t18.CORE_ROLES
    assert tuple(config["population"]["glyph_system_order"]) == t18.SYSTEM_ORDER
    assert tuple(config["depth"]["primary_normalized_fractions"]) == t18.PRIMARY_DEPTHS
    forwards = 192 * 4 * 2
    vectors = forwards * 4 * 9
    assert forwards == config["acquisition"]["expected_model_forward_calls_per_model"]
    assert vectors == config["acquisition"]["expected_readout_vectors_per_model"]
    assert forwards * 9 == config["acquisition"]["expected_total_model_forward_calls"]
    assert vectors * 9 == config["acquisition"]["expected_total_readout_vectors"]
    assert config["model_primary_endpoint"]["randomization_draws"] == 19_999
    assert config["model_primary_endpoint"]["practical_minimum"] == 0.02


def test_depth_resolution_is_unique_for_all_models() -> None:
    for role in t18.MODEL_ROLES:
        values = t18.resolved_layers(role)
        assert len(values) == 9
        assert len(set(values)) == 9
        assert values == tuple(sorted(values))


def test_round_robin_selection_is_deterministic_and_family_unique() -> None:
    rows = []
    for subgroup in ("a", "b", "c"):
        for index in range(5):
            rows.append(
                {
                    "subgroup": subgroup,
                    "codepoint": f"{ord(subgroup):X} {index:X}",
                    "canonical_family_codepoint": f"{ord(subgroup):X} {index:X}",
                }
            )
    first = t18._round_robin_select(rows, "modifier", 8)
    second = t18._round_robin_select(list(reversed(rows)), "modifier", 8)
    assert [row["codepoint"] for row in first] == [row["codepoint"] for row in second]
    assert len({row["canonical_family_codepoint"] for row in first}) == 8
    assert max(Counter(row["subgroup"] for row in first).values()) <= 3


def test_pair_metrics_retrieves_identical_rows() -> None:
    rng = np.random.default_rng(4)
    values = rng.normal(size=(12, 32))
    metrics, forward, reverse = t18._pair_metrics(values, values.copy())
    assert metrics["top1_accuracy_forward"] == 1.0
    assert metrics["top1_accuracy_reverse"] == 1.0
    assert np.array_equal(forward, np.arange(12))
    assert np.array_equal(reverse, np.arange(12))
    assert metrics["centered_linear_cka"] > 0.999999


def test_primary_randomization_uses_equal_system_weight(monkeypatch) -> None:
    predictions: dict[str, np.ndarray] = {}
    for system, count in zip(t18.SYSTEM_ORDER, (4, 5, 6), strict=True):
        identity = np.tile(np.arange(count), (24, 1))
        shifted = np.tile(np.roll(np.arange(count), 1), (24, 1))
        predictions[f"unrestricted__{system}__english"] = identity
        predictions[f"unrestricted__{system}__codepoint"] = shifted
    config = copy.deepcopy(t18._config())
    config["model_primary_endpoint"]["descriptive_uncertainty"]["replicates"] = 16
    monkeypatch.setattr(t18, "_config", lambda: config)
    result = t18.randomization_test(
        predictions,
        component="unrestricted",
        strata_by_system=None,
        draws=31,
        seed=123,
        practical_minimum=0.02,
    )
    assert result["observed_equal_system_equal_context_contrast"] == 1.0
    assert result["practical_pass"] is True
    assert result["p_value"] == 1 / 32
    assert all(
        row["contrast_equal_context_mean"] == 1.0
        for row in result["system_results"].values()
    )


def test_independent_multiple_testing_helpers() -> None:
    adjusted = independent.holm({"a": 0.001, "b": 0.02, "c": 0.9}, alpha=0.05)
    assert adjusted["a"]["reject"] is True
    assert adjusted["c"]["reject"] is False
    partial = independent.partial_conjunction(
        {"a": 0.001, "b": 0.01, "c": 0.02, "d": 0.9}, r=3
    )
    assert partial["rth_p"] == 0.02
    assert partial["p_value"] == 0.04


def test_source_hashes_are_pinned_in_selection() -> None:
    config = t18._config()
    manifest = json.loads((ROOT / t18.SELECTION_PATH).read_text())
    assert (
        manifest["source_bindings"]["unicode_emoji_test"]["sha256"]
        == config["source_bindings"]["unicode_emoji_test"]["sha256"]
    )
    for key in t18.CLDR_FILES:
        assert (
            manifest["source_bindings"]["cldr"][key]["sha256"]
            == config["source_bindings"]["cldr"][key]["sha256"]
        )


def test_claim_boundary_is_fail_closed() -> None:
    config = t18._config()
    assert (
        config["population"]["not_authorized_as"]
        == "pretraining_holdout_or_semantic_concept_holdout"
    )
    assert (
        config["tokenization_guardrail"]["japanese_secondary_decision_authorized"]
        is False
    )
    forbidden = set(config["forbidden_actions"])
    assert "activation_intervention" in forbidden
    assert "behavioral_generation" in forbidden
    assert config["bounded_model_cell_family"][
        "relationship_to_cross_model_primary"
    ].endswith("cannot_rescue_partial_conjunction")
