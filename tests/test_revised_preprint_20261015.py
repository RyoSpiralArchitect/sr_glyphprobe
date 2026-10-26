"""Fail-closed document checks; no protected or private records are opened."""
import importlib.util
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "artifacts/public_release_20261015/evidence/readout_qualification_v1"
source = ROOT / "paper/scripts/validate_revised_preprint_20261015.py"
spec = importlib.util.spec_from_file_location("revised_preprint_checks", source)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


@pytest.mark.parametrize("message", ["Overfull \\hbox", "undefined citations", "Rerun to get references", "multiply defined"])
def test_log_rejects_layout_or_reference_problem(message):
    with pytest.raises(ValueError):
        check.check_log(message)


def test_underfull_warning_is_not_hidden_as_failure():
    check.check_log("Underfull \\hbox (badness 10000)")


def test_all_preserved_pins_are_actual_file_hashes():
    for path, expected in check.PRESERVED.items():
        assert len(expected) == 64
        assert check.sha(ROOT / path) == expected


def test_current_paper_preserves_prospective_and_interpretive_boundaries():
    appendix = (ROOT / "paper/readout_qualification_20261015.tex").read_text()
    main = (ROOT / "paper/main.tex").read_text()
    assert "not an external\npreregistration" in appendix
    assert "not independent tasks" in appendix
    assert "all 96 reserved cases" in appendix and "all 192 reserved" in appendix
    assert "Constant\nNo attains 64/96" in appendix
    assert "not a replacement\nprimary estimator" in appendix
    assert "never a negative event label" in appendix
    assert r"\input{readout_qualification_20261015.tex}" in main
    assert "Revised preprint, October 15, 2026" in main


def test_new_docs_are_bilingual():
    for name in ("RELEASE_CANDIDATE_20261015", "REVISION_NOTES_20261015", "CURRENT_CLAIMS_20261015"):
        for suffix in (".md", ".ja.md"):
            assert (ROOT / "paper" / (name + suffix)).is_file()


def test_qualification_example_matches_prepared_input_exactly():
    text = (ROOT / "paper/readout_qualification_20261015.tex").read_text()
    matches = re.findall(r"% qualification-input: (\S+)\n\\begin\{contextinput\}\n(.*?)\n\\end\{contextinput\}", text, flags=re.S)
    assert len(matches) == 1
    identifier, displayed = matches[0]
    # Public projection retains the exact scientific inputs; its bindings are
    # independently verified by test_public_integration_20261026.py.
    prepared = json.loads((PUBLIC / "specification.public.json").read_text())
    row = next(r for r in prepared["inputs"] if r["input_id"] == identifier)
    assert displayed.replace("\\\\\n", "\n") == row["prompt"]
    assert row["answers"] == {"a": " Yes", "b": " No"}
    assert row["expected_yes"] is False


def test_reported_new_results_match_checked_records():
    data = json.loads((PUBLIC / "analysis.public.json").read_text())
    audit = json.loads((PUBLIC / "independent_validation.public.json").read_text())
    assert data["primary"] == audit["primary"]
    assert data["numerical_gate_passed"] and audit["independent_arithmetic_validation_passed"]
    assert data["primary"]["correct"] == 88 and data["primary"]["ties"] == 4
    assert data["primary"]["incorrect_completed_nontied"] == 4
    assert data["primary"]["all_correct_roots"] == 8
    assert data["label_robustness"]["correct"] == 104 and data["label_robustness"]["ties"] == 19
    assert not data["primary_qualification_passed"] and not data["label_robustness_passed"]
    appendix = (ROOT / "paper/readout_qualification_20261015.tex").read_text()
    for fragment in ("correct on 88/96 cases", "four choices are incorrect and four are tied",
                     "104/192 choices are correct", "69 are incorrect, and 19 are tied",
                     "889.366 seconds", "precision was not varied"):
        assert fragment in appendix
    full = [r for r in data["pairs"] if (r["split"], r["question_form"], r["answer_format"]) ==
            ("reserved_check", "direct", "full_sentence")]
    assert sum(r["first_token_tie"] for r in full) == 12
    assert all(r["correct"] for r in full if r["first_token_tie"])
    assert not any(r["first_token_vs_sum_strict_reversal"] for r in full)


def test_generated_qualification_tables_equal_numeric_projection():
    path = ROOT / "scripts/summarize_readout_qualification_v1.py"
    module_spec = importlib.util.spec_from_file_location("qualification_table_check", path)
    formatter = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(formatter)
    directory = ROOT / "paper/generated/readout_qualification_20261015"
    summary = json.loads((directory / "summary.json").read_text())
    assert (directory / "tables.tex").read_text() == formatter.tex(summary)
    assert summary["counts"]["completed_forwards"] == 4640
    assert summary["label_mapping"]["reserved_direct"]["jointly_correct"] == 14
    assert summary["label_mapping"]["reserved_direct"]["ties_or_missing"] == 18


@pytest.mark.parametrize("counts", ["tests='0' errors='0' failures='0' skipped='0'", "tests='5' errors='0' failures='1' skipped='0'", "tests='5' errors='0' failures='0' skipped='1'"])
def test_test_receipt_rejects_incomplete_validation(tmp_path, counts):
    path = tmp_path / "tests.xml"
    path.write_text(f"<testsuites><testsuite {counts}/></testsuites>")
    with pytest.raises(ValueError):
        check.check_tests(path)


def test_test_receipt_accepts_nonempty_passed_suite(tmp_path):
    path = tmp_path / "tests.xml"
    path.write_text("<testsuites><testsuite tests='5' errors='0' failures='0' skipped='0'/></testsuites>")
    assert check.check_tests(path) == {"tests": 5, "errors": 0, "failures": 0, "skipped": 0}
