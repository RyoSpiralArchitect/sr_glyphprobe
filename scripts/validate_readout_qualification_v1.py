#!/usr/bin/env python3
"""Independent, standard-library saved-score audit; never acquires model outputs.

This checker imports neither the acquisition runner nor its analysis. It checks
the finite-set protocol, reconstructs its schedule and numerical summaries,
and compares them with the retained analysis. It rejects incomplete runs.
It is not independent reacquisition, semantic validation, or an inference test.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path


PROTOCOL = "glyphprobe-text-only-readout-qualification-v1"
STATES = ("positive", "negative", "unknown")
FORMS = ("direct", "nested_true", "nested_false")
FORMATS = ("full_sentence", "minimal", "letters_normal", "letters_reversed")
FAMILIES = {"maintenance": "development", "storage": "development",
            "delivery": "reserved_check", "garden": "reserved_check"}
PRIMARY = {"split": "reserved_check", "question_form": "direct", "answer_format": "minimal",
           "planned_pairs": 96, "required_correct": 96, "required_ties": 0,
           "required_complete_roots": 16, "required_correct_per_root": 6,
           "numerical_gate_required": True, "selection_after_outputs": False}
LABEL_GATE = {"split": "reserved_check", "question_form": "direct",
              "answer_formats": ["letters_normal", "letters_reversed"], "planned_pairs": 192,
              "required_correct": 192, "required_ties": 0, "numerical_gate_required": True,
              "separate_from_primary": True}
EXACT_SCORE_FIELDS = ("candidate_token_logprobs", "sequence_logprob_sum",
    "shared_prediction_logits_sha256", "shared_prediction_logits_shape",
    "shared_prediction_logits_dtype", "logits_hash_byte_order", "normalization_rectangle_shape")
PAIR_FIELDS = ("input_id", "root_id", "family", "split", "report_state", "query_polarity",
              "question_form", "answer_format", "proposition_supported", "expected_yes")
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def decode(text):
    def invalid(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(text, object_pairs_hook=no_duplicate_keys, parse_constant=invalid)


def read(path):
    return decode(Path(path).read_text(encoding="utf-8"))


def valid_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def shared_length(a, b):
    count = 0
    for x, y in zip(a, b):
        if x != y:
            break
        count += 1
    return count


def answer_definition(fmt):
    definitions = {
        "full_sentence": ('"The answer is yes." means yes; "The answer is no." means no.',
                          {"a": " The answer is yes.", "b": " The answer is no."}),
        "minimal": ("Yes means yes; No means no.", {"a": " Yes", "b": " No"}),
        "letters_normal": ("A means yes; B means no.", {"a": " A", "b": " B"}),
        "letters_reversed": ("A means no; B means yes.", {"a": " B", "b": " A"}),
    }
    return definitions[fmt]


def validate_inventory(spec):
    require(spec["protocol_id"] == PROTOCOL, "Protocol differs")
    require(spec["primary"] == PRIMARY and spec["label_robustness_gate"] == LABEL_GATE, "Decision rules differ")
    require((spec["planned_pairs"], spec["planned_scientific_sequence_scores"],
             spec["planned_sentinel_forwards"], spec["planned_forward_attempts"]) == (2304, 4608, 32, 4640),
            "Planned denominator differs")
    inputs = spec["inputs"]
    require(len(inputs) == 2304 and len(spec["sentinels"]) == 8, "Input/sentinel inventory differs")
    require(object_sha(inputs) == spec["tokenized_inputs_sha256"], "Tokenized inventory hash differs")
    untokenized = [{k: v for k, v in row.items() if k not in
                   ("candidates", "shared_prefix_token_count", "causal_predictor_token_count")} for row in inputs]
    require(object_sha(untokenized) == spec["inventory_sha256"], "Untokenized inventory hash differs")
    by_root = defaultdict(list)
    for row in inputs:
        root, state, query, form, fmt = (row[k] for k in
            ("root_id", "report_state", "query_polarity", "question_form", "answer_format"))
        require(state in STATES and query in STATES[:2] and form in FORMS and fmt in FORMATS, "Unknown cell factor")
        require(row["input_id"] == "::".join((root, state, query, form, fmt)), "Input identifier differs")
        require(row["family"] in FAMILIES and row["split"] == FAMILIES[row["family"]], "Family/split differs")
        require(root.startswith(row["family"] + "_"), "Root/family differs")
        positive, negative = row["positive_proposition"], row["negative_proposition"]
        require(isinstance(positive, str) and isinstance(negative, str) and positive and negative and
                positive != negative, "Proposition pair invalid")
        proposition = positive if query == "positive" else negative
        report = (positive + "." if state == "positive" else negative + "." if state == "negative" else
                  "The report does not specify whether " + positive + ".")
        question = {"direct": f"Does the report explicitly state that {proposition}?",
                    "nested_true": f"Is it true that the report explicitly states that {proposition}?",
                    "nested_false": f"Is it false that the report explicitly states that {proposition}?"}[form]
        supported = state != "unknown" and state == query
        expected = not supported if form == "nested_false" else supported
        labels, answers = answer_definition(fmt)
        prompt = ("Judge what the report explicitly states, not what happened in the world. "
                  "A report that does not specify whether a proposition holds explicitly states "
                  "neither that proposition nor its negation.\nResponse labels: " + labels +
                  "\nGive only the response label.\nReport: " + report + "\nQuestion: " + question + "\nAnswer:")
        require(row["report"] == report and row["proposition"] == proposition and row["question"] == question and
                row["prompt"] == prompt and row["answers"] == answers, "Report/question/physical response mapping differs")
        require(type(row["proposition_supported"]) is bool and row["proposition_supported"] == supported and
                type(row["expected_yes"]) is bool and row["expected_yes"] == expected,
                "Logical support reference differs (unknown is not negative evidence)")
        require(row["reference_status"] == "stipulated_explicit_support_not_human_semantic_gold", "Reference status differs")
        candidates = row["candidates"]
        require(set(candidates) == {"a", "b"}, "Candidate set differs")
        for key, candidate in candidates.items():
            ids, n = candidate["input_token_ids"], candidate["prompt_token_count"]
            require(type(n) is int and 0 < n < len(ids) <= 512 and
                    all(type(t) is int and 0 <= t < 128256 for t in ids), "Token geometry invalid")
            require(candidate["candidate_token_ids"] == ids[n:] and candidate["continuation"] == answers[key],
                    "Candidate continuation differs")
        a, b = candidates["a"], candidates["b"]
        n = a["prompt_token_count"]
        require(n == b["prompt_token_count"] and a["input_token_ids"][:n] == b["input_token_ids"][:n],
                "Prompt token identity differs")
        shared = shared_length(a["candidate_token_ids"], b["candidate_token_ids"])
        require(shared < min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])) and
                row["shared_prefix_token_count"] == shared and row["causal_predictor_token_count"] == shared + 1,
                "First-divergence span differs")
        by_root[root].append(row)
    require(len(by_root) == 32 and len({r["input_id"] for r in inputs}) == 2304, "Root/cell identities differ")
    expected_grid = set(itertools.product(STATES, STATES[:2], FORMS, FORMATS))
    roots_per_family = Counter()
    for root, rows in by_root.items():
        require(len(rows) == 72 and {(r["report_state"], r["query_polarity"], r["question_form"], r["answer_format"])
                                    for r in rows} == expected_grid, "Root factorial incomplete")
        for key in ("family", "split", "positive_proposition", "negative_proposition"):
            require(len({r[key] for r in rows}) == 1, "Root metadata changed across conditions")
        roots_per_family[rows[0]["family"]] += 1
    require(dict(roots_per_family) == {name: 8 for name in FAMILIES}, "Root/family balance differs")


def geometry(case, key):
    candidate = case["candidates"][key]
    ids = candidate["input_token_ids"]
    prompt = candidate["prompt_token_count"]
    total = max(len(c["input_token_ids"]) for c in case["candidates"].values())
    return {"input_token_ids": ids + [0] * (total - len(ids)),
            "attention_mask": [1] * len(ids) + [0] * (total - len(ids)), "position_ids": list(range(total)),
            "valid_length": len(ids), "total_length": total, "prompt_length": prompt,
            "candidate_token_ids": ids[prompt:], "predictor_positions": list(range(prompt - 1, len(ids) - 1)),
            "normalization_start": prompt - 1, "normalization_stop": total - 1,
            "shared_prefix_token_count": case["shared_prefix_token_count"]}


def schedule(spec):
    events = []
    for phase, cases in (("begin", spec["sentinels"]), ("qualification", spec["inputs"]), ("end", spec["sentinels"])):
        for case in cases:
            for key in ("a", "b"):
                method = "padded_" + key
                events.append(({"event_id": f"{phase}::{case['input_id']}::{method}", "phase": phase,
                    "input_id": case["input_id"], "method": method, "geometry": geometry(case, key)}, case))
    require(len(events) == 4640 and len({e["event_id"] for e, _ in events}) == 4640, "Schedule identity/count differs")
    return events


def validate_score(row, event):
    require(row["status"] == "completed" and row["forward_attempted"] is True and
            "boundary_error_after_score" not in row, "Incomplete or boundary-failed run is not validatable")
    values, g = row["candidate_token_logprobs"], event["geometry"]
    require(len(values) == len(g["candidate_token_ids"]) and all(finite(v) and v <= 0 for v in values),
            "Invalid token log probabilities")
    require(finite(row["sequence_logprob_sum"]) and math.fsum(values) == row["sequence_logprob_sum"],
            "Token sum differs from sequence score")
    n = g["shared_prefix_token_count"]
    require(row["normalization_rectangle_shape"] == [g["normalization_stop"]-g["normalization_start"], 128256] and
            row["shared_prediction_logits_shape"] == [n, 128256] and
            row["shared_prediction_logits_dtype"] == "float32" and
            row["logits_hash_byte_order"] in ("little", "big") and valid_hash(row["shared_prediction_logits_sha256"]),
            "Predictor/normalization receipt invalid")
    if n == 0:
        require(row["shared_prediction_logits_sha256"] == EMPTY_SHA, "Empty prefix hash invalid")
    if event["phase"] == "qualification":
        require(row["causal_prediction_logits_shape"] == [n+1, 128256] and
                row["causal_prediction_logits_dtype"] == "float32" and
                valid_hash(row["causal_prediction_logits_sha256"]), "First-divergent predictor receipt invalid")


def selected(margin):
    return None if margin == 0 else margin > 0


def pair_summary(case, a, b):
    n = case["shared_prefix_token_count"]
    require(a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n], "Shared prefix scores differ")
    for key in ("shared_prediction_logits_sha256", "shared_prediction_logits_shape", "shared_prediction_logits_dtype",
                "causal_prediction_logits_sha256", "causal_prediction_logits_shape", "causal_prediction_logits_dtype",
                "logits_hash_byte_order", "normalization_rectangle_shape"):
        require(a[key] == b[key], "First-divergence/prefix predictor receipts differ: " + key)
    yes, no = a["candidate_token_logprobs"], b["candidate_token_logprobs"]
    margin = math.fsum(yes) - math.fsum(no)
    common = math.fsum(yes[:n]) - math.fsum(no[:n])
    first = yes[n] - no[n]
    tail = math.fsum(yes[n:]) - math.fsum(no[n:])
    # Re-derive logical reference, even though inventory metadata was checked above.
    support = case["report_state"] != "unknown" and case["report_state"] == case["query_polarity"]
    expected = not support if case["question_form"] == "nested_false" else support
    return {k: case[k] for k in PAIR_FIELDS} | {
        "proposition_supported": support, "expected_yes": expected, "completed": True,
        "shared_prefix_logprobs_exact": True, "causal_predictors_exact": True, "prefix_exact": True,
        "shared_prefix_token_count": n, "causal_predictor_token_count": n+1,
        "s_yes_minus_no": margin, "s_shared_prefix": common, "s_first_divergent_token": first,
        "s_divergent_tail": tail, "decomposition_residual": margin-common-tail,
        "selected_yes": selected(margin), "tie": margin == 0,
        "correct": margin != 0 and selected(margin) == expected,
        "first_token_selected_yes": selected(first), "first_token_tie": first == 0,
        "first_token_correct": first != 0 and selected(first) == expected,
        "first_token_vs_sum_strict_reversal": first*margin < 0,
        "candidate_token_logprobs": {"yes": yes, "no": no}}


def metrics(rows):
    n = len(rows)
    require(n > 0, "Empty summary group")
    roots = defaultdict(list)
    for row in rows:
        roots[row["root_id"]].append(row)
    strata = {}
    for key in ("report_state", "proposition_supported"):
        grouped = defaultdict(list)
        for row in rows:
            grouped[str(row[key]).lower()].append(row)
        cells = {name: {"planned": len(group), "correct": sum(r["correct"] for r in group),
                       "completed": len(group), "accuracy_planned_denominator": sum(r["correct"] for r in group)/len(group)}
                 for name, group in sorted(grouped.items())}
        strata[key] = {"groups": cells, "macro_accuracy": math.fsum(c["accuracy_planned_denominator"] for c in cells.values())/len(cells)}
    correct = sum(r["correct"] for r in rows)
    return {"planned_pairs": n, "completed_pairs": n, "missing_pairs": 0,
        "correct": correct, "incorrect_completed_nontied": sum(not r["tie"] and not r["correct"] for r in rows),
        "ties": sum(r["tie"] for r in rows), "accuracy_planned_denominator": correct/n,
        "constant_no_correct": sum(not r["expected_yes"] for r in rows),
        "constant_no_accuracy": sum(not r["expected_yes"] for r in rows)/n,
        "planned_roots": len(roots), "complete_roots": len(roots),
        "all_correct_roots": sum(all(r["correct"] for r in group) for group in roots.values()),
        "roots": [{"root_id": root, "planned_pairs": len(group), "completed_pairs": len(group),
                   "correct": sum(r["correct"] for r in group), "ties": sum(r["tie"] for r in group)}
                  for root, group in sorted(roots.items())], "strata": strata,
        "first_token_correct": sum(r["first_token_correct"] for r in rows),
        "first_token_ties": sum(r["first_token_tie"] for r in rows),
        "first_token_vs_sum_strict_reversals": sum(r["first_token_vs_sum_strict_reversal"] for r in rows)}


def consistency(rows, axis, left, right, inverse=False):
    keys = ("root_id", "report_state", "query_polarity", "question_form", "answer_format")
    index = {tuple(r[k] for k in keys): r for r in rows}
    pairs = []
    for a in rows:
        if a[axis] != left:
            continue
        b = index[tuple(right if k == axis else a[k] for k in keys)]
        decidable = a["selected_yes"] is not None and b["selected_yes"] is not None
        same = a["selected_yes"] == b["selected_yes"]
        pairs.append({"left_input_id": a["input_id"], "right_input_id": b["input_id"], "split": a["split"],
                      "completed": True, "decidable": decidable, "consistent": decidable and (not same if inverse else same)})
    return {"planned": len(pairs), "completed": len(pairs), "decidable": sum(p["decidable"] for p in pairs),
            "consistent": sum(p["consistent"] for p in pairs),
            "inconsistent_decidable": sum(p["decidable"] and not p["consistent"] for p in pairs),
            "ties_or_missing": sum(not p["decidable"] for p in pairs), "pairs": pairs}


def recompute(spec, records, saved):
    validate_inventory(spec)
    events = schedule(spec)
    require(len(records) == 4640, "Missing/extra planned forward rows")
    index = {}
    for row, (event, case) in zip(records, events):
        require(all(row.get(k) == v for k, v in event.items()), "Forward identity/order/geometry differs")
        validate_score(row, event)
        index[event["event_id"]] = row
        if event["phase"] != "qualification":
            reference = case["expected_scores"][event["method"]]
            require(all(row[k] == reference[k] for k in EXACT_SCORE_FIELDS), "Historical sentinel differs")
    pairs = [pair_summary(case, *[index[f"qualification::{case['input_id']}::padded_{key}"] for key in ("a", "b")])
             for case in spec["inputs"]]
    groups = []
    for split, form, fmt in itertools.product(("development", "reserved_check"), FORMS, FORMATS):
        subset = [r for r in pairs if (r["split"], r["question_form"], r["answer_format"]) == (split, form, fmt)]
        groups.append({"split": split, "question_form": form, "answer_format": fmt, **metrics(subset)})
    primary = next(g for g in groups if all(g[k] == PRIMARY[k] for k in ("split", "question_form", "answer_format")))
    labels = metrics([r for r in pairs if r["split"] == "reserved_check" and r["question_form"] == "direct" and
                      r["answer_format"] in ("letters_normal", "letters_reversed")])
    primary_pass = primary["correct"] == 96 and primary["ties"] == 0 and primary["all_correct_roots"] == 16
    label_pass = labels["correct"] == 192 and labels["ties"] == 0
    expected = {"protocol_id": PROTOCOL, "numerical_gate_passed": True, "sentinels_exact": True,
        "planned_pairs": 2304, "completed_pairs": 2304, "status_counts": {"completed": 4640},
        "primary_definition": PRIMARY, "primary": primary, "primary_qualification_passed": primary_pass,
        "label_robustness_definition": LABEL_GATE, "label_robustness": labels, "label_robustness_passed": label_pass,
        "qualification_status": "qualified_for_this_explicit_support_protocol" if primary_pass else "not_qualified",
        "groups": groups, "pairs": pairs, "inferential_p_values_computed": False,
        "label_mapping_consistency": consistency(pairs, "answer_format", "letters_normal", "letters_reversed"),
        "nested_true_direct_consistency": consistency(pairs, "question_form", "direct", "nested_true"),
        "nested_false_direct_polarity_consistency": consistency(pairs, "question_form", "direct", "nested_false", True)}
    require("execution_error" not in saved, "Saved analysis records an execution error")
    for key, value in expected.items():
        require(saved.get(key) == value, "Saved analysis differs from independent calculation: " + key)
    families, root_margins = [], []
    for family, form, fmt in itertools.product(FAMILIES, FORMS, FORMATS):
        subset = [r for r in pairs if (r["family"], r["question_form"], r["answer_format"]) == (family, form, fmt)]
        families.append({"family": family, "split": FAMILIES[family], "question_form": form, "answer_format": fmt,
                         **metrics(subset)})
        for root in sorted({r["root_id"] for r in subset}):
            cells = [r for r in subset if r["root_id"] == root]
            signed = [(1 if r["expected_yes"] else -1)*r["s_yes_minus_no"] for r in cells]
            root_margins.append({"root_id": root, "family": family, "split": FAMILIES[family],
                "question_form": form, "answer_format": fmt, "planned_pairs": len(cells),
                "correct": sum(r["correct"] for r in cells), "ties": sum(r["tie"] for r in cells),
                "minimum_reference_signed_margin_nats": min(signed), "mean_reference_signed_margin_nats": math.fsum(signed)/len(signed)})
    return {"protocol_id": PROTOCOL, "independent_arithmetic_validation_passed": True,
            "planned_forward_rows": 4640, "validated_forward_rows": 4640, "validated_pairs": 2304,
            "primary": primary, "primary_qualification_passed": primary_pass, "label_robustness": labels,
            "label_robustness_passed": label_pass, "groups": groups, "family_groups": families,
            "root_margin_summaries": root_margins, "saved_analysis_fields_compared": sorted(expected),
            "supplemental_summary_status": "post-acquisition numerical summaries; no changed gate or selection",
            "model_forwards": 0, "tokenizer_calls": 0, "inference_tests": 0,
            "independent_reacquisition": False,
            "claim_ceiling": "Independent saved-score arithmetic audit only; no semantic, population, or causal validation"}


def validate_files(specification, run, expected_sha, output):
    specification, run, output = Path(specification), Path(run), Path(output)
    require(valid_hash(expected_sha), "An externally retained specification SHA-256 is required")
    require(not output.exists(), "Refusing to overwrite validator output")
    require(sha(specification) == expected_sha, "Externally pinned specification SHA-256 differs")
    spec, receipt = read(specification), read(run / "run_completed.json")
    require(receipt["protocol_id"] == PROTOCOL and receipt["specification_sha256"] == expected_sha,
            "Run/specification binding differs")
    require(receipt["source_files"] == spec["source_files"], "Run source binding differs")
    require(receipt["status"] == "completed" and receipt["stop_reason"] is None and
            receipt["numerical_gate_passed"] is True and receipt["forward_attempts"] == 4640 and
            receipt["planned_forward_attempts"] == 4640 and receipt["completed_pairs"] == 2304 and
            receipt["status_counts"] == {"completed": 4640}, "Incomplete or numerical-failed run receipt")
    artifacts = receipt["artifacts"]
    require({"forwards.jsonl", "analysis.json", "run_started.json"}.issubset(artifacts), "Required artifact hashes missing")
    for name, expected in artifacts.items():
        require(isinstance(name, str) and Path(name).name == name and name not in (".", "..") and valid_hash(expected),
                "Invalid artifact name/hash")
        path = run / name
        require(path.is_file() and path.resolve().is_relative_to(run.resolve()) and sha(path) == expected,
                "Saved artifact hash/path differs: " + name)
    started = read(run / "run_started.json")
    require(started["protocol_id"] == PROTOCOL and started["specification_sha256"] == expected_sha and
            started["source_files"] == spec["source_files"], "Started-run binding differs")
    lines = (run / "forwards.jsonl").read_text(encoding="utf-8").splitlines()
    require(len(lines) == 4640 and all(line.strip() for line in lines), "Forward JSONL denominator differs")
    result = recompute(spec, [decode(line) for line in lines], read(run / "analysis.json"))
    for key in ("primary_qualification_passed", "label_robustness_passed"):
        require(receipt[key] == result[key], "Completion receipt verdict differs: " + key)
    result["provenance"] = {"specification_sha256": expected_sha,
        "run_completed_sha256": sha(run / "run_completed.json"), "forwards_sha256": sha(run / "forwards.jsonl"),
        "saved_analysis_sha256": sha(run / "analysis.json"), "all_recorded_artifact_hashes_verified": True,
        "validator_source_sha256": sha(Path(__file__)), "created_at_utc": datetime.now(timezone.utc).isoformat()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
    return {"status": "independently_recomputed_saved_scores", "output_sha256": sha(output),
            "primary_qualification_passed": result["primary_qualification_passed"],
            "label_robustness_passed": result["label_robustness_passed"], "model_forwards": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--expected-specification-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate_files(args.specification, args.run, args.expected_specification_sha256, args.output), indent=2))


if __name__ == "__main__":
    main()
