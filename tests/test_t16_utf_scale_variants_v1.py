from __future__ import annotations

import importlib.util
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
