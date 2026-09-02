import ast
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import t21_glyph_context_path_confirmation_v0 as confirmation  # noqa: E402
import validate_t21_glyph_context_path_confirmation_v0 as independent  # noqa: E402


def row(index: int) -> dict:
    return {
        "codepoint": f"{index:04X}",
        "alias_label": f"alias{index}",
        "canonical_label": f"canonical{index}",
        "glyph": chr(0x1000 + index),
        "codepoint_literal": f"U+{index:04X}",
        "source_index": index,
    }


def test_all_and_only_remaining_items_are_admitted():
    matched = [row(i) for i in range(954)]
    used = [row(i) for i in range(759)]
    remaining = confirmation.remaining_items(matched, used)
    assert len(remaining) == 195
    assert [r["source_index"] for r in remaining] == list(range(759, 954))
    assert [r["bank_index"] for r in remaining] == list(range(195))


def test_previous_alias_mismatch_fails_closed():
    matched = [row(i) for i in range(954)]
    used = [row(i) for i in range(759)]
    used[23]["alias_label"] = "changed"
    with pytest.raises(ValueError, match="different allocation"):
        confirmation.remaining_items(matched, used)


def test_count_and_uniqueness_fail_closed():
    matched = [row(i) for i in range(953)]
    with pytest.raises(ValueError, match="pool changed"):
        confirmation.remaining_items(matched, [row(i) for i in range(759)])
    matched = [row(i) for i in range(954)]
    matched[-1]["alias_label"] = matched[-2]["alias_label"]
    with pytest.raises(ValueError, match="Duplicate"):
        confirmation.remaining_items(matched, [row(i) for i in range(759)])


def test_confirmation_source_never_calls_prohibited_builders_or_scanner():
    tree = ast.parse(
        (ROOT / "scripts/t21_glyph_context_path_confirmation_v0.py").read_text()
    )
    prohibited = {"_text_exposure", "build_selection", "_rebuild_t19_matched_emoji"}
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    calls |= {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not calls & prohibited


def test_fixed_primary_contract():
    cfg = confirmation.config()
    assert cfg["population"]["target_count"] == 195
    assert cfg["intervention"]["primary_anchor"] == 21
    assert cfg["intervention"]["primary_context_indices"] == [1, 3]
    assert cfg["inference"]["contrasts"] == list(confirmation.stats.NAMES)
    assert cfg["inference"]["positive_rule"].startswith("complete_validated")


def test_independent_simultaneous_bound_reconstruction():
    import numpy as np

    x = np.random.default_rng(892).normal(0.25, 0.7, (195, 5))
    a = confirmation.stats.simultaneous_lower(x, replicates=1000)
    b = independent.max_t(x, replicates=1000)
    assert a["critical_value"] == pytest.approx(b["critical"], abs=1e-12)
    for j, name in enumerate(confirmation.stats.NAMES):
        assert a["contrasts"][name]["lower_simultaneous_95"] == pytest.approx(
            b["lower"][j], abs=1e-12
        )
