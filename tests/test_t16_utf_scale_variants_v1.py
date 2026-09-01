from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "t16_utf_scale_variants_v1.py"
SPEC = importlib.util.spec_from_file_location("t16_utf_x1", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_factorial_counts_and_zero_forward_design() -> None:
    result = MODULE.audit_design()
    assert result["status"] == "design_pass_zero_x1_model_forwards"
    assert result["records_per_model"] == 57_312
    assert result["records_total"] == 515_808
    assert result["model_forwards"] == 0
    assert len(result["model_roles"]) == 9
    assert len(result["chunks"]) == 11


def test_scale_clone_bytes_and_n1_prompt_collapse() -> None:
    grouped: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    for row in MODULE.chunk_records("scale"):
        if row["scale_variant"] == "clone_exact_utf":
            anchor = MODULE._systems()[int(row["system_index"])]["items"][
                int(row["rotation"])
            ]["glyph"]
            assert row["sequence"] == anchor * int(row["n"])
            assert row["sequence"].encode("utf-8") == anchor.encode("utf-8") * int(
                row["n"]
            )
        if row["n"] == 1:
            key = (str(row["system_id"]), int(row["rotation"]), str(row["wrapper_id"]))
            grouped.setdefault(key, []).append(row)
    assert len(grouped) == 96
    for values in grouped.values():
        assert {row["scale_variant"] for row in values} == set(MODULE.SCALE_VARIANTS)
        assert len({row["unique_prompt_index"] for row in values}) == 1


def test_order_variants_preserve_anchor_and_exact_multiset() -> None:
    for family in MODULE.DIVERSITY_FAMILIES:
        values = [
            MODULE._ordered_items(3, 2, 64, family, variant)
            for variant in MODULE.ORDER_VARIANTS
        ]
        assert all(value[0] == values[0][0] for value in values)
        assert len({MODULE._multiset_sha256(value) for value in values}) == 1
    assert MODULE._ordered_items(
        3, 2, 64, "cross", "shuffle_seed17_tail"
    ) == MODULE._ordered_items(3, 2, 64, "cross", "shuffle_seed17_tail")


def test_position_variants_have_one_anchor_and_exact_multiset() -> None:
    for family in MODULE.DIVERSITY_FAMILIES:
        values = [
            MODULE._position_items(4, 1, 128, family, position)
            for position in MODULE.ANCHOR_POSITIONS
        ]
        anchor = MODULE._systems()[4]["items"][1]["glyph"]
        assert all(value.count(anchor) == 1 for value in values)
        assert len({MODULE._multiset_sha256(value) for value in values}) == 1
        assert values[0][0] == anchor
        assert values[1][64] == anchor
        assert values[2][-1] == anchor


def test_all_separator_chunks_keep_item_order() -> None:
    condition = ("atomic", 0, 16, "w01_mark_anchor", "within", "reverse_tail")
    hashes = set()
    for separator in MODULE.SEPARATORS:
        rows = MODULE.chunk_records(f"order_{separator}")
        lookup = MODULE._order_lookup(rows)
        hashes.add(lookup[condition]["item_order_sha256"])
    assert len(hashes) == 1


def test_committed_result_and_closeout_bind_complete_run() -> None:
    analysis_path = ROOT / "validation/t16_utf_scale_variants_v1/results/analysis.json"
    closeout_path = ROOT / "validation/t16_utf_scale_variants_v1/closeout.json"
    run_log_path = ROOT / "validation/t16_utf_scale_variants_v1/run.log"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    closeout = json.loads(closeout_path.read_text(encoding="utf-8"))

    assert analysis["status"] == "utf_scale_variants_analysis_complete"
    assert analysis["audit"] == {
        **analysis["audit"],
        "status": (
            "all_nine_roles_all_chunks_complete_integrated_scientific_open_authorized"
        ),
        "roles_complete": 9,
        "chunks_complete": 99,
        "records": 515_808,
        "unique_prompts_across_model_chunk_namespaces": 514_080,
        "generation_calls": 0,
    }
    assert closeout["raw_arrays_copied_from_furnace"] is False
    assert closeout["protected_target_banks_opened"] is False
    assert closeout["allocator_warnings"]["recoverable_warning_count"] == 6
    assert closeout["allocator_warnings"]["fatal_exceptions"] == 0
    assert (
        hashlib.sha256(analysis_path.read_bytes()).hexdigest()
        == closeout["analysis"]["sha256"]
    )
    assert (
        hashlib.sha256(run_log_path.read_bytes()).hexdigest()
        == closeout["run_log"]["sha256"]
    )


def test_committed_result_preserves_descriptive_boundaries() -> None:
    analysis = json.loads(
        (ROOT / "validation/t16_utf_scale_variants_v1/results/analysis.json").read_text(
            encoding="utf-8"
        )
    )
    primary_positive = 0
    n500_positive = 0
    interval_positive = 0
    blocked_largest = 0
    position_cross_larger = 0
    position_last_larger = 0

    for model in analysis["results"].values():
        for cell in model.values():
            scale = cell["scale"]
            assert set(scale["per_n_medians"]["1"].values()) == {0.0}
            summary = scale["primary_summaries"]["cross_minus_within"]
            primary_positive += summary["principal_unit_median"] > 0.0
            interval_positive += summary["bootstrap_95_percent_interval"][0] > 0.0
            n500_positive += scale["per_n_medians"]["500"]["cross_minus_within"] > 0.0

            for family in MODULE.DIVERSITY_FAMILIES:
                variants = cell["order"][family]
                values = {
                    variant: variants[variant]["primary_summary"][
                        "principal_unit_median"
                    ]
                    for variant in MODULE.ORDER_VARIANTS[1:]
                }
                blocked_largest += max(values, key=values.get) == "blocked_tail"

                positions = cell["position"][family]
                position_last_larger += (
                    positions["last"]["primary_summary"]["principal_unit_median"]
                    > positions["middle"]["primary_summary"]["principal_unit_median"]
                )

            for position in MODULE.ANCHOR_POSITIONS[1:]:
                position_cross_larger += (
                    cell["position"]["cross"][position]["primary_summary"][
                        "principal_unit_median"
                    ]
                    > cell["position"]["within"][position]["primary_summary"][
                        "principal_unit_median"
                    ]
                )

    assert primary_positive == 36
    assert n500_positive == 36
    assert interval_positive == 36
    assert blocked_largest == 72
    assert position_cross_larger == 72
    assert position_last_larger == 71
    for claim in (
        "tokenizer_independent_unicode_claim_authorized",
        "emoji_meaning_claim_authorized",
        "causal_circuit_claim_authorized",
        "instruction_tuning_effect_claim_authorized",
        "scaling_law_claim_authorized",
        "model_population_generality_claim_authorized",
    ):
        assert analysis[claim] is False


def test_result_documents_are_bilingual() -> None:
    stem = "T16_UTF_SCALE_VARIANTS_V1_RESULTS"
    assert (ROOT / "docs" / f"{stem}.md").is_file()
    assert (ROOT / "docs" / f"{stem}.ja.md").is_file()
