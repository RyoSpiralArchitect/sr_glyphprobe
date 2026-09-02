import copy
import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_t21_compact_inference_v0 as compact_validator  # noqa: E402


def inputs():
    directory = ROOT / "validation/t21_glyph_context_path_confirmation_v0/results"
    return (
        json.loads((directory / "item_contrasts.json").read_text()),
        json.loads((directory / "confirmation_result.json").read_text()),
    )


def test_compact_statistical_replay():
    compact, result = inputs()
    check = compact_validator.verify(compact, result)
    assert check["status"] == "pass"
    assert check["target_items"] == 195
    assert check["maximum_numeric_error"] < 1e-12


def test_duplicate_target_is_rejected():
    compact, result = inputs()
    compact["rows"][1]["item_index"] = 0
    with pytest.raises(ValueError, match="duplicate"):
        compact_validator.verify(compact, result)


def test_changed_result_bound_is_rejected():
    compact, result = inputs()
    changed = copy.deepcopy(result)
    changed["primary"]["contrasts"]["necessity_absolute"]["lower_simultaneous_95"] += (
        0.01
    )
    with pytest.raises(ValueError, match="numerical reconstruction"):
        compact_validator.verify(compact, changed)


def test_paper_table_has_all_five_means_and_simultaneous_bounds():
    _compact, result = inputs()
    tex = (ROOT / "paper/main.tex").read_text()
    end = tex.index(r"\label{tab:t21}")
    start = tex.rfind(r"\begin{table}", 0, end)
    table = tex[start:end]
    for row in result["primary"]["contrasts"].values():
        assert f"{row['mean']:.6f}" in table
        assert f"{row['lower_simultaneous_95']:.6f}" in table
    assert "one-sided" in table and "simultaneous" in table
    assert "$n=195$" in table


def test_table6_all_seven_secondary_sites_remain_explicit():
    tex = (ROOT / "paper/main.tex").read_text()
    end = tex.index(r"\label{tab:t20}")
    start = tex.rfind(r"\begin{table}", 0, end)
    table = tex[start:end].split(r"\end{tabular}")[0]
    assert len(re.findall(r"&\s*secondary\s*\\\\", table)) == 7
    assert "Primary verdict" in table
