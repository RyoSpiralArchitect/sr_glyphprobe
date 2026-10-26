"""Synthetic saved-score publication checks; no real model/tokenizer work."""
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


s = load("publication_readout_summary", ROOT / "scripts/summarize_readout_qualification_v1.py")
fixtures = load("publication_validator_fixtures", ROOT / "tests/test_validate_readout_qualification_v1.py")


@pytest.fixture(scope="module")
def source():
    spec = fixtures.specification.__wrapped__()
    rows = fixtures.fixture_records(spec)
    analysis = fixtures.m.q.analyze(spec, rows)
    independent = fixtures.v.recompute(spec, rows, analysis)
    return spec, rows, analysis, independent


def test_complete_projection_denominators(source):
    _, _, analysis, independent = source
    result = s.project(analysis, independent)
    assert len(result["main_rows"]) == 12
    assert len(result["reserved_state_rows"]) == 36
    assert len(result["family_groups"]) == 48
    assert len(result["root_margin_summaries"]) == 384
    for row in result["main_rows"]:
        for split in s.SPLITS:
            cell = row[split]
            assert cell["correct"] == cell["completed_pairs"] == cell["planned_pairs"] == 96
            assert cell["all_cases_correct_roots"] == 16
            assert cell["support_class_balanced_accuracy"] == 1
            assert cell["first_token_correct"] == 96
            assert cell["missing_pairs"] == cell["ties"] == 0
    assert all(row["planned_pairs"] == row["correct"] == 32 for row in result["reserved_state_rows"])
    assert result["label_mapping"]["overall"]["consistent"] == 576
    assert result["label_mapping"]["reserved_direct"]["jointly_correct"] == 96
    assert all(value["overall"]["consistent"] == 768 for value in result["question_consistency"].values())
    assert result["new_model_forwards"] == result["new_tokenizer_calls"] == result["new_inferential_tests"] == 0
    assert result["independent_reacquisition"] is False


def test_ties_and_failed_primary_remain_visible(source):
    spec = source[0]
    target = next(r["input_id"] for r in spec["inputs"] if r["split"] == "reserved_check" and
                  r["question_form"] == "direct" and r["answer_format"] == "minimal")
    def modify(case, event):
        return {"tie": True} if case["input_id"] == target else {}
    rows = fixtures.fixture_records(spec, modify)
    analysis = fixtures.m.q.analyze(spec, rows)
    independent = fixtures.v.recompute(spec, rows, analysis)
    summary = s.project(analysis, independent)
    main = next(r["reserved_check"] for r in summary["main_rows"] if
                r["question_form"] == "direct" and r["answer_format"] == "minimal")
    assert main["planned_pairs"] == main["completed_pairs"] == 96
    assert main["correct"] == 95 and main["ties"] == 1
    assert main["all_cases_correct_roots"] == 15
    assert main["first_token_correct"] == 95 and main["first_token_ties"] == 1
    assert not summary["primary_qualification_passed"]
    assert summary["label_robustness_passed"]
    assert "95/96" in s.tex(summary)


def test_mapping_agreement_is_not_joint_correctness(source):
    spec = source[0]
    def modify(case, event):
        return {"correct": False} if event["phase"] == "qualification" and case["answer_format"].startswith("letters_") else {}
    rows = fixtures.fixture_records(spec, modify)
    analysis = fixtures.m.q.analyze(spec, rows)
    independent = fixtures.v.recompute(spec, rows, analysis)
    summary = s.project(analysis, independent)
    mapping = summary["label_mapping"]["overall"]
    assert mapping["consistent"] == mapping["planned_comparisons"] == 576
    assert mapping["jointly_correct"] == 0
    assert mapping["both_wrong_nontied"] == 576
    assert summary["primary_qualification_passed"]
    assert not summary["label_robustness_passed"]


def test_constant_no_baseline_is_not_balanced_accuracy(source):
    spec = source[0]
    def modify(case, event):
        if event["phase"] != "qualification":
            return {}
        return {"correct": not case["expected_yes"]}
    rows = fixtures.fixture_records(spec, modify)
    analysis = fixtures.m.q.analyze(spec, rows)
    independent = fixtures.v.recompute(spec, rows, analysis)
    summary = s.project(analysis, independent)
    direct = next(r["reserved_check"] for r in summary["main_rows"] if
                  r["question_form"] == "direct" and r["answer_format"] == "minimal")
    assert direct["correct"] == 64
    assert direct["accuracy_planned_denominator"] == 2/3
    assert direct["support_class_balanced_accuracy"] == 0.5
    assert direct["all_cases_correct_roots"] == 0
    assert not summary["primary_qualification_passed"]


def test_sequence_and_token_estimators_stay_separate(source):
    spec = source[0]
    rows = fixtures.fixture_records(spec)
    target = next(r for r in rows if r["phase"] == "qualification" and r["method"] == "padded_a" and
                  "reserved_check" not in r["input_id"] and r["input_id"].endswith("::direct::full_sentence"))
    target["candidate_token_logprobs"][-1] = -4.0
    target["sequence_logprob_sum"] = math.fsum(target["candidate_token_logprobs"])
    analysis = fixtures.m.q.analyze(spec, rows)
    independent = fixtures.v.recompute(spec, rows, analysis)
    summary = s.project(analysis, independent)
    diagnostics = summary["format_readout_diagnostics"]
    assert sum(r["first_token_vs_sequence_strict_reversals"] for r in diagnostics) == 1
    assert sum(r["correct"] for r in diagnostics) == 2303
    assert sum(r["first_token_correct"] for r in diagnostics) == 2304


@pytest.mark.parametrize("change", ["gate", "missing", "group", "source_count"])
def test_unvalidated_or_mismatched_projection_rejected(source, change):
    _, _, analysis, independent = copy.deepcopy(source)
    if change == "gate":
        independent["independent_arithmetic_validation_passed"] = False
    elif change == "missing":
        analysis["completed_pairs"] = 2303
    elif change == "group":
        independent["groups"][0]["correct"] = 0
    elif change == "source_count":
        independent["validated_forward_rows"] = 4639
    with pytest.raises(ValueError):
        s.project(analysis, independent)


def test_generated_tex_denominators_and_claim_boundary(source):
    summary = s.project(source[2], source[3])
    output = s.tex(summary)
    assert output.count(r"\begin{table}") == output.count(r"\end{table}") == 2
    assert output.count(r"\begin{tabular}") == output.count(r"\end{tabular}") == 3
    assert "Correct / 96" in output and "All six / 16" in output
    assert "Token correct / 96" in output and "Sequence ties / 96" in output
    assert "Reserved-check correct / 32 (ties)" in output
    assert "not human semantic accuracy" in output
    assert "Unknown reports support neither assertion" in output
    assert "tab:readout-qualification-main" in output
    assert "tab:readout-qualification-states" in output


def bound_files(tmp_path, source):
    spec, rows, analysis, _ = source
    spec_path, run, digest, independent_path = fixtures.write_fixture(tmp_path, spec, (rows, analysis))
    fixtures.v.validate_files(spec_path, run, digest, independent_path)
    return run / "analysis.json", independent_path, tmp_path / "publication"


def test_file_api_hashes_receipts_and_no_overwrite(tmp_path, source):
    analysis_path, independent_path, output = bound_files(tmp_path, source)
    receipt = s.build(analysis_path, independent_path, output)
    assert receipt["status"] == "projected_independently_validated_saved_scores"
    assert receipt["artifacts"]["summary.json"] == s.sha(output / "summary.json")
    assert receipt["artifacts"]["tables.tex"] == s.sha(output / "tables.tex")
    summary = s.read(output / "summary.json")
    assert summary["provenance"]["analysis_sha256"] == s.sha(analysis_path)
    assert summary["provenance"]["independent_validation_sha256"] == s.sha(independent_path)
    assert summary["provenance"]["projection_source_sha256"] == s.sha(ROOT / "scripts/summarize_readout_qualification_v1.py")
    with pytest.raises(ValueError, match="overwrite"):
        s.build(analysis_path, independent_path, output)


@pytest.mark.parametrize("change", ["analysis_hash", "validator_hash", "unvalidated", "no_artifact_gate"])
def test_file_api_binding_failures_leave_no_output(tmp_path, source, change):
    analysis_path, independent_path, output = bound_files(tmp_path, source)
    if change == "analysis_hash":
        with analysis_path.open("a", encoding="utf-8") as handle:
            handle.write("\n")
    else:
        validation = s.read(independent_path)
        if change == "validator_hash":
            validation["provenance"]["validator_source_sha256"] = "0" * 64
        elif change == "unvalidated":
            validation["independent_arithmetic_validation_passed"] = False
        else:
            validation["provenance"]["all_recorded_artifact_hashes_verified"] = False
        independent_path.write_text(json.dumps(validation), encoding="utf-8")
    with pytest.raises(ValueError):
        s.build(analysis_path, independent_path, output)
    assert not output.exists()


def test_projection_imports_no_acquisition_library():
    text = (ROOT / "scripts/summarize_readout_qualification_v1.py").read_text()
    assert "import torch" not in text and "import transformers" not in text
    assert "import readout_qualification_v1" not in text and "importlib" not in text
