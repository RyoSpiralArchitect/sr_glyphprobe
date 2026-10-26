#!/usr/bin/env python3
"""Prospective, offline factual-support readout qualification, not emoji evidence.

Inventory/analysis are standard-library only. Prepare tokenizes without model
forwards; run is explicit and requires the externally retained specification
digest. Every planned forward remains visible after a refusal or interruption.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SELF = "scripts/readout_qualification_v1.py"
PROTOCOL = "glyphprobe-text-only-readout-qualification-v1"
OLD_SPEC = "validation/contextual_emoji_matched_shape_v1/specification.json"
OLD_SHA = "63e16fc7e60079032eade81a9cc599a1cea1b2db287373b077d08f078d162ecf"
PREFIX = "scripts/contextual_emoji_prefix_consistency_v0.py"
PREFIX_SHA = "5ee9d2120c51e26db936ef37e0e1d4607aaf606fad41fb4970fc20210b985d65"
PAIRS = 2304
MAX_FORWARDS = 4640
WALL_SECONDS = 1800
STATES = ("positive", "negative", "unknown")
QUESTION_FORMS = ("direct", "nested_true", "nested_false")
FORMATS = ("full_sentence", "minimal", "letters_normal", "letters_reversed")
PRIMARY = {"split": "reserved_check", "question_form": "direct", "answer_format": "minimal",
           "planned_pairs": 96, "required_correct": 96, "required_ties": 0,
           "required_complete_roots": 16, "required_correct_per_root": 6,
           "numerical_gate_required": True, "selection_after_outputs": False}
LABEL_GATE = {"split": "reserved_check", "question_form": "direct",
              "answer_formats": ["letters_normal", "letters_reversed"], "planned_pairs": 192,
              "required_correct": 192, "required_ties": 0, "numerical_gate_required": True,
              "separate_from_primary": True}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prefix = module(ROOT / PREFIX, "readout_qualification_prefix")
require, read, write, digest, now = prefix.require, prefix.read, prefix.write, prefix.digest, prefix.now
require(digest(ROOT / PREFIX) == PREFIX_SHA, "Historical prefix helper changed")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def object_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def roots():
    """New authored roots; no historical targets or author responses are read."""
    maintenance = [
        ("Ada", "rinsed", "copper kettle"), ("Bryn", "polished", "silver buckle"),
        ("Cleo", "mended", "canvas awning"), ("Dev", "oiled", "iron hinge"),
        ("Esme", "scrubbed", "stone basin"), ("Faris", "varnished", "oak stool"),
        ("Gita", "sharpened", "steel chisel"), ("Hale", "patched", "leather satchel"),
    ]
    storage = [
        ("amber bead", "cedar box"), ("ivory comb", "velvet pouch"),
        ("jade pendant", "glass cabinet"), ("linen napkin", "wicker basket"),
        ("maple spoon", "ceramic jar"), ("nickel coin", "cotton envelope"),
        ("opal ring", "walnut drawer"), ("pewter whistle", "cardboard case"),
    ]
    delivery = [
        ("Inez", "brass compass", "Jules"), ("Kavi", "blue ribbon", "Luz"),
        ("Marek", "wooden flute", "Nia"), ("Oren", "purple notebook", "Pia"),
        ("Rafi", "striped scarf", "Suri"), ("Tariq", "clay figurine", "Uma"),
        ("Veda", "red lantern", "Wren"), ("Xavi", "woven mat", "Yara"),
    ]
    garden = [
        ("elm seedling", "watered", "Zeno"), ("birch sapling", "staked", "Alba"),
        ("fern pot", "replanted", "Belen"), ("rose bush", "pruned", "Cai"),
        ("tulip bulb", "buried", "Della"), ("ivy vine", "trimmed", "Ewan"),
        ("mint sprig", "harvested", "Faye"), ("cedar shoot", "mulched", "Galen"),
    ]
    groups = [
        ("maintenance", "development", [(f"{n} has {v} the {o}", f"{n} has not {v} the {o}") for n, v, o in maintenance]),
        ("storage", "development", [(f"the {o} is inside the {p}", f"the {o} is not inside the {p}") for o, p in storage]),
        ("delivery", "reserved_check", [(f"{n} handed the {o} to {r}", f"{n} did not hand the {o} to {r}") for n, o, r in delivery]),
        ("garden", "reserved_check", [(f"the {o} was {v} by {n}", f"the {o} was not {v} by {n}") for o, v, n in garden]),
    ]
    result = []
    for family, split, propositions in groups:
        for i, (positive, negative) in enumerate(propositions, 1):
            result.append({"root_id": f"{family}_{i:02d}", "family": family, "split": split,
                           "positive_proposition": positive, "negative_proposition": negative})
    require(len(result) == 32 and len({r["positive_proposition"] for r in result}) == 32, "Root inventory differs")
    return result


def response_format(name):
    # Both letter mappings keep physical label order A, B and the same syntax.
    # Only the semantic mapping changes. Candidate a always denotes logical yes.
    if name == "letters_normal":
        labels, answers = "A means yes; B means no.", {"a": " A", "b": " B"}
    elif name == "letters_reversed":
        labels, answers = "A means no; B means yes.", {"a": " B", "b": " A"}
    elif name == "minimal":
        labels, answers = "Yes means yes; No means no.", {"a": " Yes", "b": " No"}
    else:
        require(name == "full_sentence", "Unknown response format")
        labels = '"The answer is yes." means yes; "The answer is no." means no.'
        answers = {"a": " The answer is yes.", "b": " The answer is no."}
    return "Response labels: " + labels + "\nGive only the response label.", answers


def inventory():
    result = []
    for root in roots():
        for state in STATES:
            report = (root[state + "_proposition"] + "." if state != "unknown" else
                      "The report does not specify whether " + root["positive_proposition"] + ".")
            for query in ("positive", "negative"):
                proposition = root[query + "_proposition"]
                supported = state == query
                questions = {
                    "direct": f"Does the report explicitly state that {proposition}?",
                    "nested_true": f"Is it true that the report explicitly states that {proposition}?",
                    "nested_false": f"Is it false that the report explicitly states that {proposition}?",
                }
                for question_form, question in questions.items():
                    for answer_format in FORMATS:
                        instructions, answers = response_format(answer_format)
                        prompt = ("Judge what the report explicitly states, not what happened in the world. "
                                  "A report that does not specify whether a proposition holds explicitly states "
                                  "neither that proposition nor its negation.\n" + instructions +
                                  "\nReport: " + report + "\nQuestion: " + question + "\nAnswer:")
                        result.append({**root, "input_id": "::".join((root["root_id"], state, query, question_form, answer_format)),
                            "report_state": state, "query_polarity": query, "proposition": proposition,
                            "report": report, "question_form": question_form, "question": question,
                            "answer_format": answer_format, "prompt": prompt, "answers": answers,
                            "proposition_supported": supported,
                            "expected_yes": supported if question_form != "nested_false" else not supported,
                            "reference_status": "stipulated_explicit_support_not_human_semantic_gold"})
    require(len(result) == PAIRS and len({r["input_id"] for r in result}) == PAIRS, "Pair inventory differs")
    return result


def shared_count(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def tokenize_inventory(tokenizer):
    result = []
    for row in inventory():
        prompt = tokenizer.encode(row["prompt"], add_special_tokens=True)
        candidates = {}
        for key, answer in row["answers"].items():
            ids = tokenizer.encode(row["prompt"] + answer, add_special_tokens=True)
            require(ids[:len(prompt)] == prompt and 0 < len(prompt) < len(ids) <= 512,
                    "Candidate tokenizer boundary or length differs")
            candidates[key] = {"input_token_ids": ids, "prompt_token_count": len(prompt),
                               "candidate_token_ids": ids[len(prompt):], "continuation": answer}
        a, b = (candidates[k]["candidate_token_ids"] for k in ("a", "b"))
        shared = shared_count(a, b)
        require(shared < min(len(a), len(b)), "Answers must diverge before either candidate ends")
        result.append({**row, "candidates": candidates, "shared_prefix_token_count": shared,
                       "causal_predictor_token_count": shared + 1})
    return result


def policy():
    return {**prefix.POLICY, "walltime_seconds": WALL_SECONDS, "maximum_forward_attempts": MAX_FORWARDS}


def sources():
    files = [SELF, PREFIX, prefix.BASE_PATH, "src/glyphprobe/provenance.py", "src/glyphprobe/io.py",
             "tests/test_readout_qualification_v1.py"]
    for path in ("docs/READOUT_QUALIFICATION_V1.md", "docs/READOUT_QUALIFICATION_V1.ja.md"):
        if (ROOT / path).exists():
            files.append(path)
    return {p: digest(ROOT / p) for p in files}


RUNTIME_KEYS = ("model_path", "model_artifact", "runtime_packages", "python_version", "historical_runtime",
                "expected_implementation_sources", "scoring")


def prepare(output):
    require(not output.exists(), "Specification already exists")
    require(digest(ROOT / OLD_SPEC) == OLD_SHA, "Historical specification changed")
    require(digest(ROOT / prefix.BASE_PATH) == prefix.BASE_SHA, "Historical scorer changed")
    old = read(ROOT / OLD_SPEC)
    base = module(ROOT / prefix.BASE_PATH, "readout_qualification_base_prepare")
    require(base.package_versions() == old["runtime_packages"] and platform.python_version() == old["python_version"],
            "Historical package/Python identity differs")
    require(base.artifact_receipt(Path(old["model_path"])) == old["model_artifact"], "Model artifacts changed")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(old["model_path"], local_files_only=True, trust_remote_code=False)
    pins = sources()
    inputs = tokenize_inventory(tokenizer)
    require(sources() == pins, "Source changed during preparation")
    spec = {key: old[key] for key in RUNTIME_KEYS}
    spec.update(protocol_id=PROTOCOL, created_at_utc=now(), source_files=pins, prior_specification_sha256=OLD_SHA,
        inputs=inputs, sentinels=old["sentinels"], inventory_sha256=object_sha(inventory()),
        tokenized_inputs_sha256=object_sha(inputs), primary=PRIMARY, label_robustness_gate=LABEL_GATE, compute_policy=policy(),
        planned_pairs=PAIRS, planned_scientific_sequence_scores=4608, planned_sentinel_forwards=32,
        planned_forward_attempts=MAX_FORWARDS, independent_fact_roots=32,
        split_roots={"development": 16, "reserved_check": 16},
        preparation={"tokenizer_calls": 6912, "model_forwards": 0, "downloads": 0, "generation_calls": 0,
                     "tokenizer_class": type(tokenizer).__name__},
        qualification_scoring={"candidate_mapping": "a=yes; b=no, including reversed letter labels",
            "padding_and_normalization": "same padded length and same float32 normalization rectangle per pair",
            "predictor_gate": "exact n+1 float32 predictor-logit bytes, including first divergent token",
            "score": "sum of all continuation token log probabilities; no length normalization",
            "alternative_formats": "prespecified descriptive reports; never replace the primary"},
        claim_ceiling="operational factual-support qualification in this model/prompt; not emoji, semantic, or population evidence")
    write(output, spec)
    return {"status": "prepared", "pairs": PAIRS, "planned_forward_attempts": MAX_FORWARDS,
            "specification_sha256": digest(output), "maximum_sequence_length": max(
                len(c["input_token_ids"]) for r in inputs for c in r["candidates"].values())}


def validate_inputs(inputs):
    fresh = inventory()
    require(len(inputs) == PAIRS, "Prepared pair denominator changed")
    for expected, saved in zip(fresh, inputs):
        require(all(saved.get(k) == v for k, v in expected.items()), "Prepared prompt/design changed")
        a, b = [saved["candidates"][k] for k in ("a", "b")]
        n = a["prompt_token_count"]
        require(type(n) is int and n > 0 and n == b["prompt_token_count"] and
                a["input_token_ids"][:n] == b["input_token_ids"][:n], "Prompt token identity changed")
        for key, c in saved["candidates"].items():
            ids = c["input_token_ids"]
            require(0 < n < len(ids) <= 512 and all(type(t) is int and 0 <= t < 128256 for t in ids), "Invalid token IDs")
            require(c["candidate_token_ids"] == ids[n:] and c["continuation"] == saved["answers"][key], "Candidate boundary changed")
        shared = shared_count(a["candidate_token_ids"], b["candidate_token_ids"])
        require(shared < min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])) and
                saved["shared_prefix_token_count"] == shared and saved["causal_predictor_token_count"] == shared + 1,
                "First-divergence predictor span changed")


def verify(spec_path, expected_sha=None):
    if expected_sha is not None:
        require(digest(spec_path) == expected_sha, "Externally pinned specification digest differs")
    spec = read(spec_path)
    require(spec["protocol_id"] == PROTOCOL and spec["primary"] == PRIMARY and
            spec["label_robustness_gate"] == LABEL_GATE and spec["compute_policy"] == policy(),
            "Protocol, primary, or resource policy changed")
    require(spec["planned_pairs"] == PAIRS and spec["planned_forward_attempts"] == MAX_FORWARDS and
            spec["planned_scientific_sequence_scores"] == 4608 and spec["planned_sentinel_forwards"] == 32,
            "Planned denominator changed")
    require(spec["source_files"] == sources(), "Bound source changed since preparation")
    require(digest(ROOT / OLD_SPEC) == OLD_SHA and spec["prior_specification_sha256"] == OLD_SHA, "Historical specification changed")
    old = read(ROOT / OLD_SPEC)
    for key in (*RUNTIME_KEYS, "sentinels"):
        require(spec[key] == old[key], "Historical identity changed: " + key)
    require(len(spec["sentinels"]) == 8 and spec["inventory_sha256"] == object_sha(inventory()) and
            spec["tokenized_inputs_sha256"] == object_sha(spec["inputs"]), "Inventory/token receipt changed")
    validate_inputs(spec["inputs"])
    return spec


def plans(spec):
    events = []
    for phase, cases in (("begin", spec["sentinels"]), ("qualification", spec["inputs"]), ("end", spec["sentinels"])):
        for case in cases:
            for method in ("padded_a", "padded_b"):
                events.append({"event_id": f"{phase}::{case['input_id']}::{method}", "phase": phase,
                    "input_id": case["input_id"], "method": method, "geometry": prefix.call_geometry(case, method)})
    require(len(events) == MAX_FORWARDS and len({r["event_id"] for r in events}) == MAX_FORWARDS, "Forward inventory changed")
    return events


def exact(a, b):
    return all(a.get(k) == b.get(k) for k in ("candidate_token_logprobs", "sequence_logprob_sum",
        "shared_prediction_logits_sha256", "shared_prediction_logits_shape", "shared_prediction_logits_dtype",
        "logits_hash_byte_order", "normalization_rectangle_shape"))


def score_call(torch, model, base, case, event, device="cuda"):
    if event["phase"] != "qualification":
        return prefix.score_call(torch, model, base, case, event, device)
    geometry = event["geometry"]
    started = time.monotonic()
    with torch.inference_mode():
        output = model(input_ids=torch.tensor([geometry["input_token_ids"]], dtype=torch.long, device=device),
                       attention_mask=torch.tensor([geometry["attention_mask"]], dtype=torch.long, device=device),
                       position_ids=torch.tensor([geometry["position_ids"]], dtype=torch.long, device=device), use_cache=False)
        logits = output.logits
        require(tuple(logits.shape[:2]) == (1, geometry["total_length"]), "Unexpected logits geometry")
        rectangle = logits[0, geometry["normalization_start"]:geometry["normalization_stop"]].float()
        logprobs = torch.log_softmax(rectangle, dim=-1)
        targets = torch.tensor(geometry["candidate_token_ids"], dtype=torch.long, device=device)
        values = [float(v) for v in logprobs[:len(targets)].gather(-1, targets[:, None]).squeeze(-1).cpu().tolist()]
        start, n = geometry["prompt_length"] - 1, case["shared_prefix_token_count"]
        predictors = logits[0, start:start+n+1].float().contiguous().cpu()
        require(bool(torch.isfinite(predictors).all()), "Nonfinite causal predictor logits")
        shared = predictors[:n].contiguous()
        score = {"candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values),
            "shared_prediction_logits_sha256": hashlib.sha256(shared.numpy().tobytes(order="C")).hexdigest(),
            "shared_prediction_logits_shape": list(shared.shape), "shared_prediction_logits_dtype": "float32",
            "causal_prediction_logits_sha256": hashlib.sha256(predictors.numpy().tobytes(order="C")).hexdigest(),
            "causal_prediction_logits_shape": list(predictors.shape), "causal_prediction_logits_dtype": "float32",
            "logits_hash_byte_order": sys.byteorder,
            "normalization_rectangle_shape": list(rectangle.shape)}
    if device == "cuda":
        torch.cuda.synchronize()
    score["elapsed_seconds"] = time.monotonic() - started
    return score


def validate_score(score, event):
    prefix.validate_score(score, event)
    g = event["geometry"]
    rectangle = score["normalization_rectangle_shape"]
    require(len(rectangle) == 2 and rectangle[0] == g["normalization_stop"]-g["normalization_start"] and
            type(rectangle[1]) is int and rectangle[1] > 0, "Normalization rectangle differs")
    require(score["shared_prediction_logits_shape"] == [g["shared_prefix_token_count"], rectangle[1]] and
            score["logits_hash_byte_order"] in ("little", "big"), "Shared hash dimensions/order differ")
    if event["phase"] == "qualification":
        require(score["causal_prediction_logits_shape"] == [g["shared_prefix_token_count"] + 1, rectangle[1]] and
                score["causal_prediction_logits_dtype"] == "float32" and
                isinstance(score["causal_prediction_logits_sha256"], str) and
                len(score["causal_prediction_logits_sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in score["causal_prediction_logits_sha256"]),
                "First-divergent-token predictor receipt missing or invalid")


def execute(spec, scorer, before, after, emit, deadline, initial_error=None):
    by_id = {r["input_id"]: r for r in spec["inputs"] + spec["sentinels"]}
    records, attempted, error, begins = [], 0, initial_error, {}
    # Signals may interrupt a model forward, but never a partly persisted JSONL
    # row or the append immediately following it. Outside scoring, handlers only
    # request an orderly stop; the request is consumed before another forward.
    # This also makes the finite not_run drain safe from repeated Ctrl-C/alarm.
    interruptible, pending_interrupt = False, None
    stop_signals = {signal.SIGALRM, signal.SIGINT}
    previous_handlers = {sig: signal.getsignal(sig) for sig in stop_signals}
    def stop_handler(signum, _frame):
        nonlocal pending_interrupt
        exc = TimeoutError("Wall time alarm") if signum == signal.SIGALRM else KeyboardInterrupt("Orderly interrupt requested")
        if pending_interrupt is None:
            pending_interrupt = f"{type(exc).__name__}: {exc}"
        if interruptible:
            raise exc
    for sig in stop_signals:
        signal.signal(sig, stop_handler)
    try:
        for event in plans(spec):
            error = error or pending_interrupt
            row = {**event, "status": "not_run", "forward_attempted": False}
            if error is not None:
                row["reason"] = error
            else:
                try:
                    interruptible = True
                    deadline()
                    before(event)
                    require(attempted < MAX_FORWARDS, "Forward cap reached")
                    attempted += 1
                    row["forward_attempted"] = True
                    try:
                        score = scorer(by_id[event["input_id"]], event)
                        validate_score(score, event)
                        row.update(score, status="completed")
                        if event["phase"] != "qualification":
                            require(exact(score, by_id[event["input_id"]]["expected_scores"][event["method"]]), "Historical sentinel differs")
                            key = event["input_id"], event["method"]
                            if event["phase"] == "begin":
                                begins[key] = score
                            else:
                                require(exact(score, begins[key]), "End sentinel differs")
                    finally:
                        after(event)
                    deadline()
                except BaseException as exc:
                    interruptible = False
                    error = f"{type(exc).__name__}: {exc}"
                    if row["status"] == "completed":
                        row["boundary_error_after_score"] = error
                    else:
                        row["status"] = "failed" if row["forward_attempted"] else "not_run"
                        row["reason"] = error
                finally:
                    interruptible = False
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, stop_signals)
            try:
                row["recorded_at_utc"] = now()
                emit(row)
                records.append(row)
            finally:
                # A signal pending during emission is delivered here, after both
                # persistence and append. The noninterruptible handler records
                # it without raising, so no duplicate/partial row is retried.
                signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
            error = error or pending_interrupt
    finally:
        interruptible = False
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    return records, attempted, error


def preference(margin):
    return None if margin is None or margin == 0 else margin > 0


def pair_diagnostic(case, a, b):
    done = a["status"] == b["status"] == "completed"
    n = case["shared_prefix_token_count"]
    common_equal = done and a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n]
    fields = ("shared_prediction_logits_sha256", "shared_prediction_logits_shape", "shared_prediction_logits_dtype",
              "causal_prediction_logits_sha256", "causal_prediction_logits_shape", "causal_prediction_logits_dtype",
              "logits_hash_byte_order", "normalization_rectangle_shape")
    predictor_equal = done and all(a[k] == b[k] for k in fields)
    s = a["sequence_logprob_sum"] - b["sequence_logprob_sum"] if done else None
    common_s = math.fsum(a["candidate_token_logprobs"][:n]) - math.fsum(b["candidate_token_logprobs"][:n]) if done else None
    answer_s = a["candidate_token_logprobs"][n] - b["candidate_token_logprobs"][n] if done else None
    tail_s = math.fsum(a["candidate_token_logprobs"][n:]) - math.fsum(b["candidate_token_logprobs"][n:]) if done else None
    selected = preference(s)
    return {k: case[k] for k in ("input_id", "root_id", "family", "split", "report_state", "query_polarity",
        "question_form", "answer_format", "proposition_supported", "expected_yes")} | {
        "completed": done, "shared_prefix_logprobs_exact": common_equal,
        "causal_predictors_exact": predictor_equal, "prefix_exact": common_equal and predictor_equal,
        "shared_prefix_token_count": n, "causal_predictor_token_count": n+1,
        "s_yes_minus_no": s, "s_shared_prefix": common_s, "s_first_divergent_token": answer_s,
        "s_divergent_tail": tail_s, "decomposition_residual": s-common_s-tail_s if done else None,
        "selected_yes": selected, "tie": done and s == 0, "correct": done and selected is not None and selected == case["expected_yes"],
        "first_token_selected_yes": preference(answer_s), "first_token_tie": done and answer_s == 0,
        "first_token_correct": done and preference(answer_s) is not None and preference(answer_s) == case["expected_yes"],
        "first_token_vs_sum_strict_reversal": done and answer_s*s < 0,
        "candidate_token_logprobs": {"yes": a.get("candidate_token_logprobs"), "no": b.get("candidate_token_logprobs")}}


def group_metrics(rows):
    """Missing/tied cells remain in every planned denominator."""
    n = len(rows)
    correct, completed = sum(r["correct"] for r in rows), sum(r["completed"] for r in rows)
    by_root = defaultdict(list)
    for row in rows:
        by_root[row["root_id"]].append(row)
    strata = {}
    for key in ("report_state", "proposition_supported"):
        groups = defaultdict(list)
        for row in rows:
            groups[str(row[key]).lower()].append(row)
        cells = {name: {"planned": len(group), "correct": sum(r["correct"] for r in group),
                       "completed": sum(r["completed"] for r in group),
                       "accuracy_planned_denominator": sum(r["correct"] for r in group)/len(group)}
                 for name, group in sorted(groups.items())}
        strata[key] = {"groups": cells, "macro_accuracy": math.fsum(g["accuracy_planned_denominator"] for g in cells.values())/len(cells)}
    return {"planned_pairs": n, "completed_pairs": completed, "missing_pairs": n-completed,
        "correct": correct, "incorrect_completed_nontied": sum(r["completed"] and not r["tie"] and not r["correct"] for r in rows),
        "ties": sum(r["tie"] for r in rows), "accuracy_planned_denominator": correct/n,
        "constant_no_correct": sum(not r["expected_yes"] for r in rows),
        "constant_no_accuracy": sum(not r["expected_yes"] for r in rows)/n,
        "planned_roots": len(by_root), "complete_roots": sum(all(r["completed"] for r in group) for group in by_root.values()),
        "all_correct_roots": sum(all(r["correct"] for r in group) for group in by_root.values()),
        "roots": [{"root_id": root, "planned_pairs": len(group), "completed_pairs": sum(r["completed"] for r in group),
                   "correct": sum(r["correct"] for r in group), "ties": sum(r["tie"] for r in group)} for root, group in sorted(by_root.items())],
        "strata": strata,
        "first_token_correct": sum(r["first_token_correct"] for r in rows),
        "first_token_ties": sum(r["first_token_tie"] for r in rows),
        "first_token_vs_sum_strict_reversals": sum(r["first_token_vs_sum_strict_reversal"] for r in rows)}


def consistency(rows, axis, left, right, inverse=False):
    fields = ("root_id", "report_state", "query_polarity", "question_form", "answer_format")
    index = {tuple(r[k] for k in fields): r for r in rows}
    result = []
    for a in rows:
        if a[axis] != left:
            continue
        key = tuple(right if k == axis else a[k] for k in fields)
        b = index[key]
        completed = a["completed"] and b["completed"]
        decidable = completed and a["selected_yes"] is not None and b["selected_yes"] is not None
        result.append({"left_input_id": a["input_id"], "right_input_id": b["input_id"], "split": a["split"],
                       "completed": completed, "decidable": decidable,
                       "consistent": decidable and ((a["selected_yes"] != b["selected_yes"]) if inverse else
                                                     (a["selected_yes"] == b["selected_yes"]))})
    return {"planned": len(result), "completed": sum(r["completed"] for r in result),
            "decidable": sum(r["decidable"] for r in result), "consistent": sum(r["consistent"] for r in result),
            "inconsistent_decidable": sum(r["decidable"] and not r["consistent"] for r in result),
            "ties_or_missing": sum(not r["decidable"] for r in result), "pairs": result}


def analyze(spec, records):
    expected = plans(spec)
    require(len(records) == len(expected), "Missing planned forward rows")
    for plan, row in zip(expected, records):
        require(all(row.get(k) == v for k, v in plan.items()), "Forward identity/geometry/order changed")
        require(row["status"] in ("completed", "failed", "not_run") and type(row["forward_attempted"]) is bool and
                row["forward_attempted"] == (row["status"] != "not_run"), "Invalid forward status")
        if row["status"] == "completed":
            validate_score(row, plan)
        else:
            require("candidate_token_logprobs" not in row and "sequence_logprob_sum" not in row, "Uncompleted row carries a score")
    index = {r["event_id"]: r for r in records}
    sentinels = []
    for case in spec["sentinels"]:
        for method in ("padded_a", "padded_b"):
            a, b = [index[f"{phase}::{case['input_id']}::{method}"] for phase in ("begin", "end")]
            sentinels.append(a["status"] == b["status"] == "completed" and exact(a, b) and exact(a, case["expected_scores"][method]))
    pairs = [pair_diagnostic(case, *[index[f"qualification::{case['input_id']}::padded_{key}"] for key in ("a", "b")])
             for case in spec["inputs"]]
    numerical = all(r["status"] == "completed" and "boundary_error_after_score" not in r for r in records) and all(sentinels) and all(r["prefix_exact"] for r in pairs)
    groups = []
    for split in ("development", "reserved_check"):
        for form in QUESTION_FORMS:
            for fmt in FORMATS:
                selected = [r for r in pairs if r["split"] == split and r["question_form"] == form and r["answer_format"] == fmt]
                groups.append({"split": split, "question_form": form, "answer_format": fmt, **group_metrics(selected)})
    primary = next(g for g in groups if all(g[k] == PRIMARY[k] for k in ("split", "question_form", "answer_format")))
    qualified = numerical and primary["planned_pairs"] == 96 and primary["completed_pairs"] == 96 and primary["correct"] == 96 and primary["ties"] == 0 and primary["all_correct_roots"] == 16
    labels = group_metrics([r for r in pairs if r["split"] == "reserved_check" and r["question_form"] == "direct"
                           and r["answer_format"] in LABEL_GATE["answer_formats"]])
    label_passed = numerical and labels["planned_pairs"] == 192 and labels["completed_pairs"] == 192 and labels["correct"] == 192 and labels["ties"] == 0
    return {"protocol_id": PROTOCOL, "numerical_gate_passed": numerical, "sentinels_exact": all(sentinels),
        "planned_pairs": PAIRS, "completed_pairs": sum(p["completed"] for p in pairs),
        "status_counts": dict(Counter(r["status"] for r in records)), "primary_definition": PRIMARY,
        "primary": primary, "primary_qualification_passed": qualified,
        "label_robustness_definition": LABEL_GATE, "label_robustness": labels,
        "label_robustness_passed": label_passed,
        "qualification_status": "qualified_for_this_explicit_support_protocol" if qualified else
            "not_qualified" if numerical else "not_evaluable_numerical_or_incomplete",
        "groups": groups,
        "label_mapping_consistency": consistency(pairs, "answer_format", "letters_normal", "letters_reversed"),
        "nested_true_direct_consistency": consistency(pairs, "question_form", "direct", "nested_true"),
        "nested_false_direct_polarity_consistency": consistency(pairs, "question_form", "direct", "nested_false", True),
        "pairs": pairs, "inferential_p_values_computed": False,
        "claim_ceiling": "fixed operational qualification only; no population accuracy, emoji interpretation, human validation, or causal claim"}


def run(spec_path, output, expected_sha):
    require(expected_sha is not None, "Run requires externally retained specification SHA-256")
    require(not output.exists(), "Run output exists; no overwrite or silent resume")
    spec = verify(spec_path, expected_sha)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    write(output / "run_started.json", {"protocol_id": PROTOCOL, "pid": os.getpid(), "started_at_utc": now(),
        "specification_sha256": expected_sha, "source_files": spec["source_files"], "compute_policy": spec["compute_policy"]})
    observations, resources = [], {}
    def deadline():
        require(time.monotonic()-started < WALL_SECONDS, "Wall time cap exhausted")
    def observe(before_load=False, event=None, boundary=None):
        return prefix.resource_guard(before_load=before_load, emit=lambda obs: observations.append({**obs,
            "event_id": event["event_id"] if event else None, "boundary": boundary}))
    def implementation(value):
        write(output / "implementation_sources.json", value)
        require(value == spec["expected_implementation_sources"], "Model/mask implementation changed")
    def alarm(*_):
        raise TimeoutError("Wall time alarm")
    previous_alarm = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, WALL_SECONDS)
    records, attempts, error, torch, model, base, peak = [], 0, None, None, None, None, None
    try:
        try:
            torch, model, base = prefix.load_model(spec, observe, lambda r: write(output / "runtime.json", r),
                                                   implementation, deadline, resources)
            require(digest(spec_path) == expected_sha and spec["source_files"] == sources(), "Prepared inputs/source changed during model loading")
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        with (output / "forwards.jsonl").open("x", encoding="utf-8") as handle:
            def emit(row):
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            records, attempts, error = execute(spec, lambda c, e: score_call(torch, model, base, c, e),
                lambda e: observe(False, e, "before"), lambda e: observe(False, e, "after"), emit, deadline, error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_alarm)
        torch = resources.get("torch", torch)
        if torch is not None and torch.cuda.is_initialized():
            peak = {"allocated_mib": torch.cuda.max_memory_allocated()/2**20, "reserved_mib": torch.cuda.max_memory_reserved()/2**20}
            model = None
            resources.pop("model", None)
            gc.collect()
            torch.cuda.empty_cache()
        write(output / "occupancy_checks.json", {"observations": observations})
    if digest(spec_path) != expected_sha or spec["source_files"] != sources():
        error = error or "Source/specification changed during execution"
    analysis = analyze(spec, records)
    if error is not None:
        analysis.update(numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
                        qualification_status="not_evaluable_numerical_or_incomplete", execution_error=error)
    write(output / "analysis.json", analysis)
    summary = {"protocol_id": PROTOCOL, "status": "completed" if analysis["numerical_gate_passed"] else "stopped_or_gate_failed",
        "finished_at_utc": now(), "specification_sha256": expected_sha, "source_files": spec["source_files"],
        "forward_attempts": attempts, "planned_forward_attempts": MAX_FORWARDS,
        "elapsed_seconds": time.monotonic()-started, "stop_reason": error,
        "numerical_gate_passed": analysis["numerical_gate_passed"],
        "primary_qualification_passed": analysis["primary_qualification_passed"],
        "label_robustness_passed": analysis["label_robustness_passed"],
        "qualification_status": analysis["qualification_status"], "completed_pairs": analysis["completed_pairs"],
        "status_counts": analysis["status_counts"], "peak_torch_memory_mib": peak,
        "downloads": 0, "generation_calls": 0, "artifacts": {p.name: digest(p) for p in output.iterdir() if p.is_file()}}
    write(output / "run_completed.json", summary)
    return summary


def analyze_saved(spec_path, run_path, output, expected_sha):
    require(expected_sha is not None, "Analysis requires specification SHA-256")
    require(not output.exists(), "Analysis output exists")
    spec = verify(spec_path, expected_sha)
    receipt = read(run_path / "run_completed.json")
    require(receipt["specification_sha256"] == expected_sha, "Run belongs to another specification")
    for name, sha in receipt["artifacts"].items():
        require(Path(name).name == name and digest(run_path / name) == sha, "Saved run artifact changed")
    records = prefix.rows(run_path / "forwards.jsonl")
    result = analyze(spec, records)
    if receipt["stop_reason"] is not None:
        result.update(numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
                      qualification_status="not_evaluable_numerical_or_incomplete", execution_error=receipt["stop_reason"])
    require(result == read(run_path / "analysis.json"), "Standard-library replay differs from saved result")
    result["replay_provenance"] = {"specification_sha256": expected_sha, "run_receipt_sha256": digest(run_path / "run_completed.json"),
                                   "all_saved_artifact_hashes_verified": True, "model_forwards": 0}
    write(output, result)
    return {"status": "replayed_exactly", "output_sha256": digest(output),
            "numerical_gate_passed": result["numerical_gate_passed"], "primary_qualification_passed": result["primary_qualification_passed"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inventory", "prepare", "verify", "run", "analyze"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--specification", type=Path)
    parser.add_argument("--expected-specification-sha256")
    parser.add_argument("--run", type=Path)
    args = parser.parse_args()
    if args.command == "inventory":
        require(args.output is not None, "Inventory output required")
        write(args.output, {"protocol_id": PROTOCOL, "primary": PRIMARY, "label_robustness_gate": LABEL_GATE, "roots": roots(), "inputs": inventory(),
                            "inventory_sha256": object_sha(inventory()), "planned_forward_attempts": MAX_FORWARDS})
        result = {"pairs": PAIRS, "sha256": digest(args.output), "model_forwards": 0}
    elif args.command == "prepare":
        result = prepare(args.output)
    elif args.command == "verify":
        spec = verify(args.specification, args.expected_specification_sha256)
        result = {"status": "verified", "pairs": len(spec["inputs"]), "specification_sha256": digest(args.specification)}
    elif args.command == "run":
        result = run(args.specification, args.output, args.expected_specification_sha256)
    else:
        result = analyze_saved(args.specification, args.run, args.output, args.expected_specification_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if args.command == "run" and not result["numerical_gate_passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
