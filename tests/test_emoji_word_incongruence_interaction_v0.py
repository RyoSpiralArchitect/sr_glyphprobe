from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emoji_word_incongruence_interaction_v0.py"
SPEC = importlib.util.spec_from_file_location("t15_interaction", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_design_arithmetic_balance_and_claim_boundary() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "design_pass_zero_t15_model_forwards"
    assert design["model_roles"] == list(MODULE.model_roles())
    assert len(design["axis_ids"]) == 8
    assert design["counts"] == {
        "source_prompts": 1_288,
        "source_metric_rows": 2_048,
        "direction_catalog_rows": 768,
        "true_conflict_rows": 16_384,
        "cross_axis_null_rows": 49_152,
        "emoji_main_rows": 16_384,
        "word_main_rows": 16_384,
        "zero_rows": 64,
        "rows_per_model": 98_368,
        "rows_total": 393_472,
    }
    assert design["model_forwards"] == 0
    assert design["confirmatory_status"] is False
    assert design["causal_claim_authorized"] is False
    assert [row["id"] for row in MODULE.targets()] == [
        row["id"] for row in MODULE.t13.targets()
    ]
    assert (
        MODULE._config()["storage"]["countsketch_dimension"]
        == MODULE.t13._config()["pilot"]["response_storage"]["countsketch_dimension"]
    )
    assert (
        MODULE._config()["storage"]["countsketch_seed"]
        == MODULE.t13._config()["pilot"]["response_storage"]["countsketch_seed"]
    )


def test_source_roster_is_exactly_balanced() -> None:
    rows = MODULE.source_prompt_records()
    assert len(rows) == 1_288
    assert Counter(row["source_kind"] for row in rows) == {
        "frame": 8,
        "emoji_component": 128,
        "word_component": 128,
        "core_pair": 256,
        "cross_pair": 768,
    }
    core = [row for row in rows if row["source_kind"] == "core_pair"]
    for axis in MODULE.axes():
        for order in MODULE.SOURCE_ORDERS:
            for wrapper_index in range(4):
                cell = [
                    row
                    for row in core
                    if row["axis_id"] == axis["id"]
                    and row["source_order"] == order
                    and row["wrapper_index"] == wrapper_index
                ]
                assert Counter(row["congruence"] for row in cell) == {
                    "congruent": 2,
                    "incongruent": 2,
                }
                assert Counter(row["emoji_polarity"] for row in cell) == {
                    "positive": 2,
                    "negative": 2,
                }
                assert Counter(row["word_polarity"] for row in cell) == {
                    "positive": 2,
                    "negative": 2,
                }


def test_factorial_interaction_cancels_additive_mains() -> None:
    records = MODULE.source_prompt_records()
    lookup = MODULE._lookup_index(records)
    deltas = np.zeros((len(records), 2, 5), dtype=np.float32)
    emoji_effect = {
        "positive": np.array([1, 2, 3, 4, 5], dtype=np.float32),
        "negative": np.array([-2, 1, 0, 3, -1], dtype=np.float32),
    }
    word_effect = {
        "positive": np.array([4, -1, 2, 0, 3], dtype=np.float32),
        "negative": np.array([0, 3, -2, 1, 4], dtype=np.float32),
    }
    axis_id = str(MODULE.axes()[0]["id"])
    for wrapper_index in range(4):
        for emoji_polarity in MODULE.POLARITIES:
            for word_polarity in MODULE.POLARITIES:
                index = MODULE._pair_index(
                    lookup,
                    "core_pair",
                    "emoji_then_word",
                    wrapper_index,
                    axis_id,
                    axis_id,
                    emoji_polarity,
                    word_polarity,
                )
                deltas[index, 0] = (
                    emoji_effect[emoji_polarity] + word_effect[word_polarity]
                )
    additive = MODULE._interaction_vector(
        deltas,
        lookup,
        site_position=0,
        axis_id=axis_id,
        word_axis_id=axis_id,
        order="emoji_then_word",
        wrappers_used=(0, 1, 2),
        source_kind="core_pair",
    )
    assert np.array_equal(additive, np.zeros(5, dtype=np.float32))

    injected = np.array([0.5, -1.0, 2.0, 0.25, -0.75], dtype=np.float32)
    for wrapper_index in range(3):
        for emoji_polarity, word_polarity in (
            ("positive", "negative"),
            ("negative", "positive"),
        ):
            index = MODULE._pair_index(
                lookup,
                "core_pair",
                "emoji_then_word",
                wrapper_index,
                axis_id,
                axis_id,
                emoji_polarity,
                word_polarity,
            )
            deltas[index, 0] += injected
    observed = MODULE._interaction_vector(
        deltas,
        lookup,
        site_position=0,
        axis_id=axis_id,
        word_axis_id=axis_id,
        order="emoji_then_word",
        wrappers_used=(0, 1, 2),
        source_kind="core_pair",
    )
    assert np.allclose(observed, injected)


def test_protocol_never_opens_protected_target_banks() -> None:
    config = MODULE._config()
    assert (
        "data/targets/p2_confirmatory_targets_v1.jsonl"
        in config["forbidden_research_inputs"]
    )
    assert (
        "data/targets/c1_causal_holdout_targets_v1.jsonl"
        in config["forbidden_research_inputs"]
    )
    source = SCRIPT.read_text(encoding="utf-8")
    assert "p2_confirmatory_targets_v1.jsonl" not in source
    assert "c1_causal_holdout_targets_v1.jsonl" not in source


def test_english_and_japanese_protocols_bind_same_counts() -> None:
    english = (ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md").read_text(
        encoding="utf-8"
    )
    japanese = (
        ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "1,288" in text
        assert "98,368" in text
        assert "393,472" in text
        assert "20,000" in text
        assert "T15-C" in text


def test_closeout_and_bilingual_results_bind_the_same_exploratory_boundary() -> None:
    closeout = json.loads(
        (
            ROOT
            / "validation"
            / "emoji_word_incongruence_interaction_v0"
            / "t15a_closeout.json"
        ).read_text(encoding="utf-8")
    )
    assert (
        closeout["status"]
        == "exploratory_complete_family_with_post_open_implementation_repair"
    )
    assert closeout["run"]["response_rows"] == 393_472
    assert closeout["run"]["model_roles_complete"] == 4
    assert closeout["run"]["generation_calls"] == 0
    assert closeout["confirmatory_status"] is False
    assert closeout["semantic_understanding_claim_authorized"] is False
    assert closeout["causal_claim_authorized"] is False
    assert closeout["analysis_repair"]["estimands_changed"] is False
    assert closeout["analysis_repair"]["bootstrap_changed"] is False
    assert closeout["interval_class_counts"][
        "A1_primary_shared_response_fingerprint"
    ] == {"mixed": 0, "negative": 0, "positive": 16, "total": 16}
    assert len(closeout["primary_a1_magnitude_0p25"]) == 16
    assert all(
        row["bootstrap_95_percent_interval"][0] > 0
        for row in closeout["primary_a1_magnitude_0p25"]
    )

    english = (
        ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md"
    ).read_text(encoding="utf-8")
    japanese = (
        ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "393,472" in text
        assert "16" in text
        assert "20,000" in text
        assert "post-open" in text
        assert "T15-C" in text
        assert "f089b31fbea245ad9fe4e5727c7dc618fa38e79bc27474c76ef435bd51fec5fe" in text
