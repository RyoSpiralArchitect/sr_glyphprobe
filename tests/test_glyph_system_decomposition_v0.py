from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "glyph_system_decomposition_v0.py"
SELECTION = ROOT / "data" / "manifests" / "glyph_system_decomposition_selection_v0.json"
SPEC = importlib.util.spec_from_file_location("t11_glyph_system", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_committed_selection_is_deterministic_balanced_and_keeps_reserve_unforwarded() -> None:
    value = json.loads(SELECTION.read_text(encoding="utf-8"))
    items = value["items"]

    assert MODULE._sha256(SELECTION) == (
        "7484f9b3b1902e38d2cf57e2b783d4f39c8c21fe96ec182c34c4e4c1934a1693"
    )
    assert value["status"] == "prospective_selection_complete_zero_t11_model_forwards"
    assert value["selected_item_count"] == 1_111
    assert value["acquired_item_count"] == 843
    assert value["reserve_item_count"] == 268
    assert value["depth_item_count"] == 192
    assert value["model_forward_calls"] == 0
    assert all(not row["included_in_acquisition"] for row in items if row["role"] == "reserve_unrun")
    assert all(row["role"] != "reserve_unrun" for row in items if row["included_in_depth_subset"])
    assert Counter(row["glyph_system"] for row in items if row["included_in_depth_subset"]) == {
        "atomic_anchor": 24,
        "presentation": 24,
        "modifier": 40,
        "zwj": 56,
        "regional_flag": 40,
        "keycap": 8,
    }
    atomic_depth_groups = Counter(
        row["group"]
        for row in items
        if row["included_in_depth_subset"] and row["glyph_system"] == "atomic_anchor"
    )
    assert set(atomic_depth_groups.values()) == {3}
    assert len(atomic_depth_groups) == 8


def test_system_classifier_and_decomposition_cover_the_frozen_families() -> None:
    assert MODULE._classify_system([0x1F600]) == "atomic_anchor"
    assert MODULE._classify_system([0x263A, 0xFE0F]) == "presentation"
    assert MODULE._classify_system([0x1F44B, 0x1F3FD]) == "modifier"
    assert MODULE._classify_system([0x1F62E, 0x200D, 0x1F4A8]) == "zwj"
    assert MODULE._classify_system([0x1F1EF, 0x1F1F5]) == "regional_flag"
    assert MODULE._classify_system([0x0031, 0xFE0F, 0x20E3]) == "keycap"
    assert MODULE._classify_system([0x1F3F4, 0xE0067, 0xE0062, 0xE007F]) == "tag_flag"
    assert MODULE._decomposed_form("presentation", [0x263A, 0xFE0F]) == "☺"
    assert MODULE._decomposed_form("modifier", [0x1F44B, 0x1F3FD]) == "👋 🏽"
    assert MODULE._decomposed_form("zwj", [0x1F62E, 0x200D, 0x1F4A8]) == "😮 💨"
    assert MODULE._decomposed_form("regional_flag", [0x1F1EF, 0x1F1F5]) == "JP"
    assert MODULE._decomposed_form("keycap", [0x0031, 0xFE0F, 0x20E3]) == "1"


def test_design_audit_recomputes_zero_forward_counts() -> None:
    result = MODULE.audit_design()

    assert result["status"] == "pass"
    assert result["selected_items"] == 1_111
    assert result["acquired_items"] == 843
    assert result["reserve_items"] == 268
    assert result["present_item_views"] == 4_087
    assert result["depth_item_views"] == 912
    assert result["broad_readout_vectors_per_model"] == 65_392
    assert result["depth_readout_vectors_per_model"] == 43_776
    assert result["shards_per_model"] == 53
    assert result["model_cells"] == 9
    assert result["expected_total_model_forward_calls"] == 73_566
    assert result["model_forward_calls"] == 0


def test_matched_control_cycles_inside_strata_without_self_matches() -> None:
    rows = [
        {"acquisition_index": 2, "glyph_system": "zwj", "codepoint": "A"},
        {"acquisition_index": 5, "glyph_system": "zwj", "codepoint": "B"},
        {"acquisition_index": 9, "glyph_system": "zwj", "codepoint": "C"},
        {"acquisition_index": 12, "glyph_system": "zwj", "codepoint": "D"},
    ]
    token_ids = {2: [1, 2], 5: [3, 4], 9: [5, 6, 7], 12: [8, 9, 10]}
    result = MODULE._control_mapping(
        rows,
        token_ids,
        role="synthetic",
        target_view="unicode_name",
        strict_prefix=False,
    )

    mapping = {row["item_index"]: row["wrong_target_item_index"] for row in result["mapping"]}
    assert result["eligible_item_count"] == 4
    assert result["coverage"] == 1.0
    assert set(mapping) == {2, 5, 9, 12}
    assert all(source != target for source, target in mapping.items())
    assert {len(token_ids[source]) == len(token_ids[target]) for source, target in mapping.items()} == {True}


def test_depth_resolution_and_continuous_metrics_are_fixed() -> None:
    assert MODULE._depth_hidden_state_indices(16) == (4, 8, 12)
    assert MODULE._depth_hidden_state_indices(28) == (7, 14, 21)
    assert MODULE._depth_hidden_state_indices(36) == (9, 18, 27)

    left = np.eye(8, dtype=np.float32)
    same = MODULE._pair_metrics(left, left)
    shifted = MODULE._pair_metrics(left, np.roll(left, 1, axis=0))
    assert same["top1_accuracy_forward"] == 1.0
    assert shifted["top1_accuracy_forward"] == 0.0
    assert same["retrieval_distribution_forward"] == {
        "retrieved_unique_target_count": 8,
        "retrieval_breadth_fraction": 1.0,
        "top_decile_target_count": 1,
        "top_decile_prediction_concentration": 0.125,
        "maximum_single_target_prediction_fraction": 0.125,
    }
    assert np.isclose(same["centered_linear_cka"], 1.0)
    assert MODULE._safe_spearman(np.arange(6), np.arange(6)[::-1]) == -1.0


def test_balanced_three_way_variance_recovers_a_pure_model_effect() -> None:
    values = np.broadcast_to(np.asarray([0.0, 1.0, 2.0])[:, None, None], (3, 2, 4))
    result = MODULE._balanced_three_way_variance(values)

    assert result["balanced_shape_model_by_system_by_context"] == [3, 2, 4]
    assert np.isclose(
        result["components"]["model"]["share_of_total_sum_squares"], 1.0
    )
    assert all(
        np.isclose(component["share_of_total_sum_squares"], 0.0)
        for name, component in result["components"].items()
        if name != "model"
    )
    assert result["sum_squares_reconciliation_error"] < 1e-12


def test_system_cell_emits_required_and_strict_matched_summaries() -> None:
    items = MODULE.selection_items(acquired_only=True)
    indices = [
        int(row["acquisition_index"])
        for row in items
        if row["glyph_system"] == "keycap"
    ]
    mapping = [
        {
            "item_index": source,
            "wrong_target_item_index": indices[(position + 1) % len(indices)],
        }
        for position, source in enumerate(indices)
    ]
    control = {
        "eligible_item_count": len(indices),
        "total_item_count": len(indices),
        "coverage": 1.0,
        "mapping": mapping,
    }
    controls = {
        target: {
            "keycap": {
                "required": control,
                "strict_prefix_sensitivity": control,
            }
        }
        for target in ("unicode_name", "component_name")
    }
    rng = np.random.default_rng(7)
    values = rng.normal(size=(len(items), len(MODULE.VIEW_ORDER), 12)).astype(np.float32)
    for index in indices:
        values[index, MODULE.VIEW_ORDER.index("unicode_name")] = (
            values[index, MODULE.VIEW_ORDER.index("glyph")] + 0.01
        )
        values[index, MODULE.VIEW_ORDER.index("component_name")] = (
            values[index, MODULE.VIEW_ORDER.index("glyph")] + 0.02
        )
        values[index, MODULE.VIEW_ORDER.index("decomposed_form")] = (
            values[index, MODULE.VIEW_ORDER.index("glyph")] + 0.03
        )

    public, arrays = MODULE._system_cell(
        values,
        system="keycap",
        global_indices=indices,
        controls=controls,
        seed=11,
        draws=20,
    )

    assert public["matched_incorrect_label_advantage"]["glyph_unicode_name"][
        "eligible_item_count"
    ] == len(indices)
    assert public["strict_prefix_matched_sensitivity"]["unicode_name"][
        "eligible_item_count"
    ] == len(indices)
    assert "glyph_unicode_name" in public["strict_prefix_matched_sensitivity"][
        "unicode_name"
    ]["pairs"]
    assert "strict_prefix__glyph_unicode_name_matched_advantage" in arrays
    assert public["pairs"]["glyph_unicode_name"]["retrieval_distribution_forward"][
        "retrieval_breadth_fraction"
    ] > 0


def test_depth_trajectory_records_first_nonzero_interval_and_final_delta(monkeypatch) -> None:
    monkeypatch.setattr(MODULE, "model_roles", lambda: ("synthetic",))
    monkeypatch.setattr(
        MODULE,
        "_config",
        lambda: {"analysis": {"analysis_systems": ["zwj"]}},
    )
    rows = []
    for index, endpoint in enumerate(MODULE.DEPTH_ENDPOINT_ORDER):
        lower = -0.1 if index < 2 else 0.01
        rows.append(
            {
                "model_role": "synthetic",
                "glyph_system": "zwj",
                "carrier": "article_a",
                "distance": 1,
                "endpoint": endpoint,
                "matched_incorrect_label_advantage": {
                    "glyph_unicode_name": {
                        "median": 0.1 * index,
                        "bootstrap_percentile_95_interval": [lower, 0.2 + index],
                    }
                },
                "decomposition_contrasts": {},
            }
        )

    result = MODULE._depth_trajectory_rows(rows)

    assert len(result) == 1
    assert result[0]["first_depth_with_interval_excluding_zero"] == {
        "endpoint": "interblock_depth_0p50",
        "direction": "positive",
        "descriptive_only": True,
    }
    assert np.isclose(
        result[0]["returned_final_minus_raw_last_block_median_delta"], 0.1
    )


def test_frozen_view_text_is_unique_within_each_selected_system() -> None:
    items = MODULE.selection_items(acquired_only=False)
    for system in MODULE._config()["selection"]["system_order"]:
        system_items = [row for row in items if row["glyph_system"] == system]
        for view in MODULE._available_views(system_items[0]):
            values = [MODULE._view_text(row, view) for row in system_items]
            assert len(values) == len(set(values))
