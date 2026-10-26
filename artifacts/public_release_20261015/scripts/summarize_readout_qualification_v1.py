#!/usr/bin/env python3
"""Publishable numeric projection of independently checked saved scores only.

Creates one machine-readable summary and generated TeX tables. No model calls,
tokenization, hypothesis selection, p-values, confidence intervals, or changes
to historical/frozen inputs occur. Incomplete or unvalidated runs are refused.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path


PROTOCOL = "glyphprobe-text-only-readout-qualification-v1"
FORMS = ("direct", "nested_true", "nested_false")
FORMATS = ("full_sentence", "minimal", "letters_normal", "letters_reversed")
STATES = ("positive", "negative", "unknown")
SPLITS = ("development", "reserved_check")
FORM_NAMES = {"direct": "Direct", "nested_true": "Nested true", "nested_false": "Nested false"}
FORMAT_NAMES = {"full_sentence": "Full sentence", "minimal": "Minimal Yes/No",
                "letters_normal": "A = Yes", "letters_reversed": "A = No"}
VALIDATOR = Path(__file__).with_name("validate_readout_qualification_v1.py")


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=invalid)


def cell_counts(rows):
    require(rows, "Empty publication cell")
    completed = sum(r["completed"] for r in rows)
    correct = sum(r["correct"] for r in rows)
    by_root = defaultdict(list)
    by_support = defaultdict(list)
    for row in rows:
        by_root[row["root_id"]].append(row)
        by_support[row["proposition_supported"]].append(row)
    require(set(by_support) == {False, True}, "Both support classes required for balanced accuracy")
    accuracy_by_support = {"supported" if support else "unsupported": {
        "planned": len(group), "completed": sum(r["completed"] for r in group),
        "correct": sum(r["correct"] for r in group),
        "accuracy": sum(r["correct"] for r in group)/len(group)} for support, group in by_support.items()}
    return {"planned_pairs": len(rows), "completed_pairs": completed, "missing_pairs": len(rows)-completed,
        "correct": correct, "ties": sum(r["tie"] for r in rows),
        "incorrect_nontied": sum(r["completed"] and not r["tie"] and not r["correct"] for r in rows),
        "accuracy_planned_denominator": correct/len(rows),
        "support_class_balanced_accuracy": math.fsum(g["accuracy"] for g in accuracy_by_support.values())/2,
        "support_classes": accuracy_by_support, "planned_roots": len(by_root),
        "all_cases_correct_roots": sum(all(r["correct"] for r in group) for group in by_root.values()),
        "cases_per_root": sorted({len(group) for group in by_root.values()}),
        "first_token_correct": sum(r["first_token_correct"] for r in rows),
        "first_token_ties": sum(r["first_token_tie"] for r in rows),
        "first_token_vs_sequence_strict_reversals": sum(r["first_token_vs_sum_strict_reversal"] for r in rows),
        "constant_no_correct": sum(not r["expected_yes"] for r in rows),
        "constant_no_accuracy": sum(not r["expected_yes"] for r in rows)/len(rows)}


def simple_counts(rows):
    """Counts for state strata, including unknown-only strata with one support class."""
    return {"planned_pairs": len(rows), "completed_pairs": sum(r["completed"] for r in rows),
        "missing_pairs": sum(not r["completed"] for r in rows), "correct": sum(r["correct"] for r in rows),
        "ties": sum(r["tie"] for r in rows),
        "incorrect_nontied": sum(r["completed"] and not r["tie"] and not r["correct"] for r in rows),
        "first_token_correct": sum(r["first_token_correct"] for r in rows),
        "first_token_ties": sum(r["first_token_tie"] for r in rows),
        "first_token_vs_sequence_strict_reversals": sum(r["first_token_vs_sum_strict_reversal"] for r in rows)}


def paired_rows(rows, axis, left, right, inverse=False):
    fields = ("root_id", "report_state", "query_polarity", "question_form", "answer_format")
    index = {tuple(r[k] for k in fields): r for r in rows}
    require(len(index) == len(rows), "Duplicate analytical pair identity")
    result = []
    for a in rows:
        if a[axis] != left:
            continue
        b = index[tuple(right if k == axis else a[k] for k in fields)]
        completed = a["completed"] and b["completed"]
        decidable = completed and not a["tie"] and not b["tie"]
        equal = a["selected_yes"] == b["selected_yes"]
        result.append({"left_input_id": a["input_id"], "right_input_id": b["input_id"],
            "root_id": a["root_id"], "split": a["split"], "report_state": a["report_state"],
            "question_form": a["question_form"], "answer_format": a["answer_format"],
            "completed": completed, "decidable": decidable,
            "consistent": decidable and (not equal if inverse else equal),
            "jointly_correct": a["correct"] and b["correct"],
            "both_wrong_nontied": decidable and not a["correct"] and not b["correct"]})
    return result


def paired_counts(rows):
    return {"planned_comparisons": len(rows), "completed_comparisons": sum(r["completed"] for r in rows),
        "decidable_comparisons": sum(r["decidable"] for r in rows),
        "consistent": sum(r["consistent"] for r in rows),
        "inconsistent_decidable": sum(r["decidable"] and not r["consistent"] for r in rows),
        "ties_or_missing": sum(not r["decidable"] for r in rows),
        "jointly_correct": sum(r["jointly_correct"] for r in rows),
        "both_wrong_nontied": sum(r["both_wrong_nontied"] for r in rows)}


def gate_inputs(analysis, independent):
    require(analysis["protocol_id"] == independent["protocol_id"] == PROTOCOL, "Protocol differs")
    require(independent["independent_arithmetic_validation_passed"] is True and
            independent["validated_forward_rows"] == independent["planned_forward_rows"] == 4640 and
            independent["validated_pairs"] == 2304 and independent["model_forwards"] == 0 and
            independent["tokenizer_calls"] == 0 and independent["inference_tests"] == 0 and
            independent["independent_reacquisition"] is False, "Independent numerical validation gate missing")
    require(analysis["numerical_gate_passed"] is True and analysis["sentinels_exact"] is True and
            analysis["planned_pairs"] == analysis["completed_pairs"] == 2304 and
            analysis["status_counts"] == {"completed": 4640} and "execution_error" not in analysis,
            "Incomplete/numerically invalid run cannot produce publication tables")
    for key in ("groups", "primary", "label_robustness", "primary_qualification_passed", "label_robustness_passed"):
        require(analysis[key] == independent[key], "Analysis/independent-validator mismatch: " + key)
    require(len(analysis["groups"]) == 24 and len(analysis["pairs"]) == 2304 and
            len(independent["family_groups"]) == 48 and len(independent["root_margin_summaries"]) == 384,
            "Projection input dimensions differ")


def project(analysis, independent):
    gate_inputs(analysis, independent)
    pairs = analysis["pairs"]
    require(len({r["input_id"] for r in pairs}) == 2304 and all(r["completed"] for r in pairs),
            "Pair inventory incomplete or duplicated")
    main_rows, format_diagnostics = [], []
    for form, fmt in itertools.product(FORMS, FORMATS):
        row = {"question_form": form, "answer_format": fmt}
        for split in SPLITS:
            subset = [r for r in pairs if (r["split"], r["question_form"], r["answer_format"]) == (split, form, fmt)]
            counts = cell_counts(subset)
            require(counts["planned_pairs"] == 96 and counts["planned_roots"] == 16 and counts["cases_per_root"] == [6],
                    "Main-table denominator differs")
            source_group = next(g for g in analysis["groups"] if
                (g["split"], g["question_form"], g["answer_format"]) == (split, form, fmt))
            for new, old in (("correct", "correct"), ("ties", "ties"), ("all_cases_correct_roots", "all_correct_roots"),
                             ("first_token_correct", "first_token_correct"), ("first_token_ties", "first_token_ties"),
                             ("first_token_vs_sequence_strict_reversals", "first_token_vs_sum_strict_reversals")):
                require(counts[new] == source_group[old], "Projection/group arithmetic differs: " + new)
            require(counts["support_class_balanced_accuracy"] == source_group["strata"]["proposition_supported"]["macro_accuracy"],
                    "Class-balanced accuracy differs")
            row[split] = counts
            format_diagnostics.append({"split": split, "question_form": form, "answer_format": fmt, **counts})
        main_rows.append(row)
    states = []
    for state, form, fmt in itertools.product(STATES, FORMS, FORMATS):
        subset = [r for r in pairs if r["split"] == "reserved_check" and
                  (r["report_state"], r["question_form"], r["answer_format"]) == (state, form, fmt)]
        counts = simple_counts(subset)
        require(counts["planned_pairs"] == 32, "Reserved state denominator differs")
        states.append({"split": "reserved_check", "report_state": state, "question_form": form,
                       "answer_format": fmt, **counts})
    mappings = paired_rows(pairs, "answer_format", "letters_normal", "letters_reversed")
    mapping_groups = []
    for split, form, state in itertools.product(SPLITS, FORMS, STATES):
        subset = [r for r in mappings if (r["split"], r["question_form"], r["report_state"]) == (split, form, state)]
        require(len(subset) == 32, "Mapping-comparison denominator differs")
        mapping_groups.append({"split": split, "question_form": form, "report_state": state, **paired_counts(subset)})
    questions = {}
    for name, left, right, invert in (
        ("direct_vs_nested_true", "direct", "nested_true", False),
        ("direct_vs_nested_false", "direct", "nested_false", True),
        ("nested_true_vs_nested_false", "nested_true", "nested_false", True)):
        comparisons = paired_rows(pairs, "question_form", left, right, invert)
        require(len(comparisons) == 768, "Question-comparison denominator differs")
        groups = []
        for split, fmt, state in itertools.product(SPLITS, FORMATS, STATES):
            subset = [r for r in comparisons if (r["split"], r["answer_format"], r["report_state"]) == (split, fmt, state)]
            groups.append({"split": split, "answer_format": fmt, "report_state": state, **paired_counts(subset)})
        questions[name] = {"normalization": "opposite decoded answers" if invert else "same decoded answer",
                           "overall": paired_counts(comparisons), "groups": groups, "pairs": comparisons}
    for name, saved_key in (("direct_vs_nested_true", "nested_true_direct_consistency"),
                            ("direct_vs_nested_false", "nested_false_direct_polarity_consistency")):
        computed, saved = questions[name]["overall"], analysis[saved_key]
        require(computed["consistent"] == saved["consistent"] and computed["decidable_comparisons"] == saved["decidable"] and
                computed["ties_or_missing"] == saved["ties_or_missing"], "Question consistency differs")
    mapping_overall = paired_counts(mappings)
    require(mapping_overall["planned_comparisons"] == 576 and
            mapping_overall["consistent"] == analysis["label_mapping_consistency"]["consistent"],
            "Mapping consistency differs")
    reserved_direct = paired_counts([r for r in mappings if r["split"] == "reserved_check" and r["question_form"] == "direct"])
    require(reserved_direct["planned_comparisons"] == 96, "Reserved direct mapping count differs")
    return {"protocol_id": PROTOCOL, "projection_version": "publication-numerical-projection-v1",
        "numerical_and_independent_validation_passed": True,
        "primary_qualification_passed": analysis["primary_qualification_passed"],
        "label_robustness_passed": analysis["label_robustness_passed"],
        "qualification_status": analysis["qualification_status"],
        "counts": {"planned_forwards": 4640, "completed_forwards": 4640, "planned_pairs": 2304,
                   "completed_pairs": 2304, "missing_pairs": 0, "fact_roots": 32, "template_families": 4,
                   "development_roots": 16, "reserved_check_roots": 16},
        "main_rows": main_rows, "reserved_state_rows": states,
        "label_mapping": {"interpretation": "Decoded answer agreement is distinct from joint correctness",
                          "overall": mapping_overall, "reserved_direct": reserved_direct,
                          "groups": mapping_groups, "pairs": mappings},
        "question_consistency": questions, "format_readout_diagnostics": format_diagnostics,
        "family_groups": independent["family_groups"], "root_margin_summaries": independent["root_margin_summaries"],
        "primary": analysis["primary"], "label_robustness": analysis["label_robustness"],
        "estimators": {"primary": "Full continuation log-probability difference; all candidate tokens summed",
            "secondary": "First divergent continuation-token log-probability difference; never substituted for primary",
            "balanced_accuracy": "Unweighted mean of correctness over supported and unsupported proposition classes",
            "root_success": "All six report-state by assertion cells correct for one question/answer format",
            "ties": "Zero margin; retained in full denominator and never counted correct",
            "missingness": "Incomplete runs are refused, not filtered into apparently complete tables"},
        "new_model_forwards": 0, "new_tokenizer_calls": 0, "new_inferential_tests": 0,
        "new_confidence_intervals": 0, "independent_reacquisition": False,
        "claim_ceiling": "Finite-set descriptive numerical projection; no new semantic, population, or causal evidence"}


def tex(summary):
    """Two readable table panels plus the 12-row reserved report-state table."""
    lines = ["% Generated from independently validated saved scores. Do not edit by hand.",
        "% Development/reserved-check roots are repeated across formats; no new independent N.",
        r"\begin{table}[p]", r"\centering\small", r"\setlength{\tabcolsep}{3pt}",
        r"\textbf{A. Whole-continuation decisions and all-six-case roots}\par\smallskip",
        r"\begin{tabular}{llrrrrrr}", r"\toprule",
        r"& & \multicolumn{2}{c}{Correct / 96} & \multicolumn{2}{c}{All six / 16} & \multicolumn{2}{c}{Balanced (\%)} \\",
        r"Question & Answer format & Dev. & Check & Dev. & Check & Dev. & Check \\", r"\midrule"]
    last = None
    for row in summary["main_rows"]:
        if last is not None and row["question_form"] != last:
            lines.append(r"\addlinespace")
        last = row["question_form"]
        a, b = row["development"], row["reserved_check"]
        lines.append(f"{FORM_NAMES[last]} & {FORMAT_NAMES[row['answer_format']]} & "
            f"{a['correct']}/96 & {b['correct']}/96 & {a['all_cases_correct_roots']}/16 & {b['all_cases_correct_roots']}/16 & "
            f"{100*a['support_class_balanced_accuracy']:.1f} & {100*b['support_class_balanced_accuracy']:.1f} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\par\medskip",
        r"\textbf{B. Ties and the separate first-divergent-token diagnostic}\par\smallskip",
        r"\begin{tabular}{llrrrrrr}", r"\toprule",
        r"& & \multicolumn{2}{c}{Sequence ties / 96} & \multicolumn{2}{c}{Token correct / 96} & \multicolumn{2}{c}{Token ties / 96} \\",
        r"Question & Answer format & Dev. & Check & Dev. & Check & Dev. & Check \\", r"\midrule"]
    last = None
    for row in summary["main_rows"]:
        if last is not None and row["question_form"] != last:
            lines.append(r"\addlinespace")
        last = row["question_form"]
        a, b = row["development"], row["reserved_check"]
        lines.append(f"{FORM_NAMES[last]} & {FORMAT_NAMES[row['answer_format']]} & "
            f"{a['ties']}/96 & {b['ties']}/96 & {a['first_token_correct']}/96 & {b['first_token_correct']}/96 & "
            f"{a['first_token_ties']}/96 & {b['first_token_ties']}/96 " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}",
        r"\caption{Explicit-report format qualification. Each split contains 16 roots, each crossed with three report states and two assertions (96 cases per format). ``All six'' counts roots correct on every case. Balanced accuracy averages the supported and unsupported classes; it is not human semantic accuracy. Panel B retains ties and reports a separate token-level estimator. The direct/minimal reserved-check condition is the fixed primary; other formats do not replace it.}",
        r"\label{tab:readout-qualification-main}", r"\end{table}", "",
        r"\begin{table}[t]", r"\centering\small", r"\begin{tabular}{llrrr}", r"\toprule",
        r"& & \multicolumn{3}{c}{Reserved-check correct / 32 (ties)} \\",
        r"Question & Answer format & Explicit P & Explicit not-P & Unknown \\", r"\midrule"]
    index = {(r["report_state"], r["question_form"], r["answer_format"]): r for r in summary["reserved_state_rows"]}
    last = None
    for form, fmt in itertools.product(FORMS, FORMATS):
        if last is not None and form != last:
            lines.append(r"\addlinespace")
        last = form
        cells = [index[state, form, fmt] for state in STATES]
        lines.append(f"{FORM_NAMES[form]} & {FORMAT_NAMES[fmt]} & " +
                     " & ".join(f"{r['correct']}/32 ({r['ties']})" for r in cells) + " " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}",
        r"\caption{Reserved-check decisions separated by report state. Each state contains 16 roots queried about both P and not-P. Unknown reports support neither assertion; this does not mean the event is false. Nested-false questions invert the expected answer about explicit support. Parentheses retain ties within the full 32-case denominator.}",
        r"\label{tab:readout-qualification-states}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def build(analysis_path, independent_path, output):
    analysis_path, independent_path, output = Path(analysis_path), Path(independent_path), Path(output)
    require(not output.exists(), "Refusing to overwrite publication projection directory")
    analysis_hash, independent_hash = sha(analysis_path), sha(independent_path)
    analysis, independent = read(analysis_path), read(independent_path)
    provenance = independent["provenance"]
    require(provenance["saved_analysis_sha256"] == analysis_hash and
            provenance["all_recorded_artifact_hashes_verified"] is True,
            "Analysis hash/independent artifact-verification binding differs")
    for field in ("specification_sha256", "run_completed_sha256", "forwards_sha256", "validator_source_sha256"):
        require(valid_hash(provenance[field]), "Missing/invalid independent provenance hash: " + field)
    require(provenance["validator_source_sha256"] == sha(VALIDATOR), "Independent-validator source identity differs")
    summary = project(analysis, independent)
    summary["provenance"] = {**provenance, "analysis_sha256": analysis_hash,
        "independent_validation_sha256": independent_hash, "projection_source_sha256": sha(Path(__file__)),
        "projection_created_at_utc": datetime.now(timezone.utc).isoformat()}
    tables = tex(summary)
    require(sha(analysis_path) == analysis_hash and sha(independent_path) == independent_hash,
            "Input changed during publication projection")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "summary.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    with (output / "tables.tex").open("x", encoding="utf-8") as handle:
        handle.write(tables)
    receipt = {"status": "projected_independently_validated_saved_scores", "protocol_id": PROTOCOL,
        "analysis_sha256": analysis_hash, "independent_validation_sha256": independent_hash,
        "projection_source_sha256": sha(Path(__file__)), "new_model_forwards": 0,
        "primary_qualification_passed": summary["primary_qualification_passed"],
        "label_robustness_passed": summary["label_robustness_passed"],
        "artifacts": {"summary.json": sha(output / "summary.json"), "tables.tex": sha(output / "tables.tex")}}
    with (output / "projection_receipt.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--independent-validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.analysis, args.independent_validation, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
