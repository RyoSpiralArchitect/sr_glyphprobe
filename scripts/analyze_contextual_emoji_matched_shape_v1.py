#!/usr/bin/env python3
"""Independent, CPU-only verification and old/new analysis of matched-shape scores.

No runner, model, tokenizer, GPU, or network imports. Previous independent
checker helpers are hash-pinned for parsing and resource validation only;
schedule, geometry, score arithmetic and development-grid endpoints are rebuilt
here. A complete acquisition is not an independently sampled scientific N.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-matched-shape-v1"
HELPER_SHA = "9e8d9079327e24011c0776374af67b56acf226a624445c27f00aded19d701464"
HELPER_PATH = ROOT / "scripts/validate_contextual_emoji_prefix_consistency_v0.py"
if hashlib.sha256(HELPER_PATH.read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError("Pinned independent parsing/resource helper changed")
_module = importlib.util.spec_from_file_location("matched_shape_prior_checker", HELPER_PATH)
prior = importlib.util.module_from_spec(_module)
_module.loader.exec_module(prior)
require, safe, digest, read, rows = prior.require, prior.safe, prior.digest, prior.read, prior.rows
finite, valid_hash, token_ids, probabilities = prior.finite, prior.valid_hash, prior.token_ids, prior.probabilities
POLICY = {**prior.POLICY, "walltime_seconds": 900, "maximum_forward_attempts": 1312}
PAIRS = ("original", "explicit_negation", "adjective_pair")
CARRIERS = ("emoji", "word")
METHODS = ("original_a_1", "original_b_1", "padded_a", "padded_b")
CORE = ("candidate_token_logprobs", "sequence_logprob_sum", "shared_prediction_logits_sha256",
        "shared_prediction_logits_shape", "shared_prediction_logits_dtype", "logits_hash_byte_order",
        "normalization_rectangle_shape")
COUNTS = {"planned_forward_attempts": 1312, "planned_scientific_sequence_scores": 1248,
          "planned_scientific_inputs": 624}


def validate_case(case):
    identity = case["identity"]
    require(len(identity) == 5 and all(isinstance(v, str) and v for v in identity) and
            case["input_id"] == "/".join(identity), "Input identity differs")
    pair, carrier, block, context, cue = identity
    require(pair in PAIRS and context in ("p", "q") and
            ((carrier in CARRIERS and cue in ("a", "b")) or
             (pair == "original" and carrier == "shared_absent" and cue == "absent")), "Unknown case identity")
    require(set(case["candidates"]) == {"a", "b"}, "Candidate pair incomplete")
    for candidate, row in case["candidates"].items():
        prompt, tokens = row["prompt_token_ids"], row["candidate_token_ids"]
        require(row["status"] == "completed" and token_ids(prompt) and token_ids(tokens) and
                row["input_token_ids"] == prompt + tokens and len(prompt) + len(tokens) <= 160,
                "Historical token geometry differs")
        require(row["prompt_token_count"] == len(prompt) and row["candidate_token_count"] == len(tokens) and
                row["first_candidate_predictor_position"] == len(prompt) - 1, "Historical predictor boundary differs")
        for field, expected in (("block_id", block), ("context", context), ("variant", cue), ("candidate", candidate)):
            require(row[field] == expected, "Historical identity field differs: " + field)
        require(type(row["eta"]) is int and row["eta"] in (-1, 1) and isinstance(row["family"], str) and row["family"],
                "Invalid author direction/family")
        probabilities(row["candidate_token_logprobs"], row["sequence_logprob_sum"], len(tokens))
    a, b = (case["candidates"][c] for c in ("a", "b"))
    require(a["prompt_token_ids"] == b["prompt_token_ids"] and a["eta"] == b["eta"] and a["family"] == b["family"],
            "Pair prompt/direction/family differs")
    n = case["shared_prefix_token_count"]
    require(type(n) is int and 0 < n <= min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])) and
            a["candidate_token_ids"][:n] == b["candidate_token_ids"][:n] == case["shared_prefix_token_ids"],
            "Invalid shared-prefix geometry")
    require(n == min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])) or
            a["candidate_token_ids"][n] != b["candidate_token_ids"][n], "Shared prefix is not maximal")


def validate_spec(spec):
    require(spec["protocol_id"] == PROTOCOL and spec["schema_version"] == 1, "Unsupported protocol")
    require(spec["compute_policy"] == POLICY, "Compute policy differs")
    for key, value in COUNTS.items():
        require(spec[key] == value, "Planned denominator differs: " + key)
    require(spec["planned_sentinel_forwards"] == 64, "Sentinel forward denominator differs")
    for key in ("new_scientific_n", "new_stimuli", "tokenizer_calls", "generation_calls", "downloads", "prepare_model_forwards"):
        require(type(spec[key]) is int and spec[key] == 0, "Specification ceiling differs: " + key)
    scoring = spec["scoring"]
    require(scoring["dtype"] == "bfloat16" and scoring["attention"] == "eager" and scoring["use_cache"] is False and
            scoring["log_softmax_dtype"] == "float32" and scoring["historical_parity_tolerance"] == 0 and
            scoring["same_shape_prefix_tolerance"] == 0, "Scoring identity/tolerance differs")
    cases, sentinels = spec["inputs"], spec["sentinels"]
    require(len(cases) == len({c["input_id"] for c in cases}) == 624, "Expected 624 unique input pairs")
    require([c["identity"] for c in cases] == sorted(c["identity"] for c in cases), "Scientific input order differs")
    for case in cases + sentinels:
        validate_case(case)
    blocks = {}
    for case in cases:
        row = case["candidates"]["a"]
        value = {"eta": row["eta"], "family": row["family"]}
        require(blocks.setdefault(row["block_id"], value) == value, "Scenario metadata differs across views")
    require(len(blocks) == 24, "Expected 24 scenarios")
    require(len(Counter(b["family"] for b in blocks.values())) == 6 and
            set(Counter(b["family"] for b in blocks.values()).values()) == {4}, "Expected six four-scenario families")
    expected = {(p, k, b, c, v) for p in PAIRS for k in CARRIERS for b in blocks for c in ("p", "q") for v in ("a", "b")}
    expected |= {("original", "shared_absent", b, c, "absent") for b in blocks for c in ("p", "q")}
    require({tuple(c["identity"]) for c in cases} == expected, "Fixed input grid differs")
    require(len(sentinels) == len({c["input_id"] for c in sentinels}) == 8, "Expected eight unique sentinels")
    lookup = {c["input_id"]: c for c in cases}
    for sentinel in sentinels:
        require(sentinel["input_id"] in lookup and sentinel["candidates"] == lookup[sentinel["input_id"]]["candidates"] and
                sentinel["shared_prefix_token_ids"] == lookup[sentinel["input_id"]]["shared_prefix_token_ids"],
                "Sentinel differs from corresponding scientific input")
        require(set(sentinel["expected_scores"]) == set(METHODS), "Sentinel method inventory differs")
    return cases, sentinels, blocks


def geometry(case, method):
    """Rebuild full model and FP32 normalization shapes without runner imports."""
    candidate = "b" if method in ("original_b_1", "padded_b") else "a"
    saved = case["candidates"][candidate]
    prompt, continuation = saved["prompt_token_ids"], saved["candidate_token_ids"]
    valid = len(prompt) + len(continuation)
    padded = method.startswith("padded")
    total = max(len(r["input_token_ids"]) for r in case["candidates"].values()) if padded else valid
    return {"input_token_ids": prompt + continuation + [0] * (total - valid),
            "attention_mask": [1] * valid + [0] * (total - valid), "position_ids": list(range(total)) if padded else None,
            "valid_length": valid, "total_length": total, "prompt_length": len(prompt),
            "candidate_token_ids": continuation, "predictor_positions": list(range(len(prompt) - 1, valid - 1)),
            "normalization_start": len(prompt) - 1, "normalization_stop": total - 1,
            "shared_prefix_token_count": case["shared_prefix_token_count"]}


def schedule(cases, sentinels):
    return [(phase, case, method) for phase, inputs, methods in
            (("begin", sentinels, METHODS), ("scientific", cases, ("padded_a", "padded_b")), ("end", sentinels, METHODS))
            for case in inputs for method in methods]


def core_equal(left, right):
    return all(left[key] == right[key] for key in CORE)


def verify_records(cases, sentinels, records):
    planned = schedule(cases, sentinels)
    require(len(records) == len({r["event_id"] for r in records}) == 1312, "Forward denominator/duplicate differs")
    attempts, halted, begin = 0, False, {}
    sentinel_lookup = {c["input_id"]: c for c in sentinels}
    sentinel_matches = []
    for (phase, case, method), row in zip(planned, records):
        event = f"{phase}::{case['input_id']}::{method}"
        require(row["event_id"] == event and row["phase"] == phase and row["input_id"] == case["input_id"] and
                row["method"] == method, "Forward identity/order differs")
        g = geometry(case, method)
        require(row["geometry"] == g, "Forward geometry differs")
        status = row["status"]
        require(status in ("completed", "failed", "not_run") and type(row["forward_attempted"]) is bool and
                row["forward_attempted"] == (status != "not_run"), "Invalid forward status/attempt")
        require(not halted or status == "not_run", "Forward continued after a stop boundary")
        attempts += row["forward_attempted"]
        if status == "completed":
            probabilities(row["candidate_token_logprobs"], row["sequence_logprob_sum"], len(g["candidate_token_ids"]))
            require(row["shared_prediction_logits_shape"] == [case["shared_prefix_token_count"], 128256] and
                    row["shared_prediction_logits_dtype"] == "float32" and valid_hash(row["shared_prediction_logits_sha256"]) and
                    row["logits_hash_byte_order"] in ("little", "big"), "Invalid shared-logit receipt")
            require(row["normalization_rectangle_shape"] == [g["normalization_stop"] - g["normalization_start"], 128256],
                    "Normalization rectangle differs")
            require(finite(row["elapsed_seconds"]) and row["elapsed_seconds"] >= 0, "Invalid forward duration")
            if phase == "scientific" and case["input_id"] in sentinel_lookup:
                equal = core_equal(row, sentinel_lookup[case["input_id"]]["expected_scores"][method])
                require(row["scientific_sentinel_exact_parity"] is equal, "Scientific sentinel metadata disagrees")
                require(equal or row.get("boundary_error_after_score"), "Scientific sentinel mismatch did not stop run")
            if phase != "scientific":
                equal = core_equal(row, case["expected_scores"][method])
                require(row["sentinel_exact_parity"] is equal, "Sentinel parity metadata disagrees")
                if method.startswith("original"):
                    old = case["candidates"]["b" if method == "original_b_1" else "a"]
                    historical = row["candidate_token_logprobs"] == old["candidate_token_logprobs"] and row["sequence_logprob_sum"] == old["sequence_logprob_sum"]
                    require(row["historical_exact_parity"] is historical, "Historical sentinel parity metadata disagrees")
                    require(historical or row.get("boundary_error_after_score"), "Historical parity failure did not stop run")
                if phase == "begin":
                    begin[case["input_id"], method] = row
                else:
                    require((case["input_id"], method) in begin, "End sentinel lacks begin sentinel")
                    end_equal = core_equal(row, begin[case["input_id"], method])
                    if "end_begin_exact_parity" in row:
                        require(row["end_begin_exact_parity"] is end_equal, "End/begin parity metadata disagrees")
                    else:
                        require(not equal and row.get("boundary_error_after_score"), "End/begin parity missing without prior failure")
                    equal &= end_equal
                sentinel_matches.append(equal)
                require(equal or row.get("boundary_error_after_score"), "Failed sentinel did not stop run")
        else:
            require(isinstance(row.get("reason"), str) and row["reason"], "Missing stopped-row reason")
            require(not any(k in row for k in CORE), "Unscored row contains score fields")
        if status != "completed" or row.get("boundary_error_after_score"):
            halted = True
    require(attempts <= 1312, "Forward-attempt bound exceeded")
    return attempts, sentinel_matches


def prefix_exact(case, a, b):
    n = case["shared_prefix_token_count"]
    return (a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n] and
            a["shared_prediction_logits_sha256"] == b["shared_prediction_logits_sha256"] and
            a["shared_prediction_logits_shape"] == b["shared_prediction_logits_shape"] and
            a["shared_prediction_logits_dtype"] == b["shared_prediction_logits_dtype"] and
            a["logits_hash_byte_order"] == b["logits_hash_byte_order"])


def derive_gates(cases, records, sentinel_matches, sentinels):
    scientific = {(r["input_id"], r["method"]): r for r in records if r["phase"] == "scientific"}
    complete = [(c, scientific[c["input_id"], "padded_a"], scientific[c["input_id"], "padded_b"]) for c in cases
                if all(scientific[c["input_id"], m]["status"] == "completed" for m in ("padded_a", "padded_b"))]
    matching = sum(prefix_exact(c, a, b) for c, a, b in complete)
    all_done = all(r["status"] == "completed" for r in records)
    sentinel_pass = len(sentinel_matches) == 64 and all(sentinel_matches)
    scientific_sentinel_pass = all(scientific[c["input_id"], m]["status"] == "completed" and
        core_equal(scientific[c["input_id"], m], c["expected_scores"][m]) for c in sentinels for m in ("padded_a", "padded_b"))
    admissible = not any(r.get("boundary_error_after_score") for r in records)
    return {**COUNTS, "completed_forward_scores": sum(r["status"] == "completed" for r in records),
        "completed_scientific_scores": sum(r["status"] == "completed" for r in scientific.values()),
        "completed_scientific_inputs": len(complete), "matching_scientific_prefixes": matching,
        "all1312_scores_completed": all_done, "all624_prefixes_exact": matching == 624,
        "all_sentinel_scientific_repeats_exact": scientific_sentinel_pass,
        "sentinel_exact_parity": sentinel_pass, "all_scored_boundaries_admissible": admissible,
        "numerical_gate_passed": all_done and matching == 624 and sentinel_pass and scientific_sentinel_pass and admissible}


def derive_detailed_diagnostics(cases, sentinels, records):
    indexed = {(r["phase"], r["input_id"], r["method"]): r for r in records}
    inputs, sentinel_results = [], []
    for case in cases:
        a, b = (indexed["scientific", case["input_id"], "padded_" + k] for k in ("a", "b"))
        row = {"input_id": case["input_id"], "prefix_logprobs_exact_equal": None,
               "shared_predictor_logits_exact_equal": None, "s_matched_shape": None, "s_historical": None}
        if a["status"] == b["status"] == "completed":
            n = case["shared_prefix_token_count"]
            row.update(prefix_logprobs_exact_equal=a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n],
                shared_predictor_logits_exact_equal=all(a[k] == b[k] for k in
                    ("shared_prediction_logits_sha256", "shared_prediction_logits_shape", "shared_prediction_logits_dtype", "logits_hash_byte_order")),
                s_matched_shape=a["sequence_logprob_sum"] - b["sequence_logprob_sum"],
                s_historical=case["candidates"]["a"]["sequence_logprob_sum"] - case["candidates"]["b"]["sequence_logprob_sum"])
        inputs.append(row)
    for case in sentinels:
        for method in METHODS:
            begin, end = (indexed[p, case["input_id"], method] for p in ("begin", "end"))
            sentinel_results.append({"input_id": case["input_id"], "method": method,
                "begin_exact_prior": core_equal(begin, case["expected_scores"][method]) if begin["status"] == "completed" else None,
                "end_exact_prior": core_equal(end, case["expected_scores"][method]) if end["status"] == "completed" else None,
                "end_exact_begin": core_equal(begin, end) if begin["status"] == end["status"] == "completed" else None})
    scientific_sentinels = []
    for case in sentinels:
        for method in ("padded_a", "padded_b"):
            row = indexed["scientific", case["input_id"], method]
            scientific_sentinels.append({"input_id": case["input_id"], "method": method,
                "scientific_exact_prior": core_equal(row, case["expected_scores"][method]) if row["status"] == "completed" else None})
    return {"input_comparisons": inputs, "sentinel_comparisons": sentinel_results,
            "scientific_sentinel_comparisons": scientific_sentinels}


def verify_sources(cases, sentinels, paths, spec, root):
    required = {"emoji_cells", "word_cells", "cells.jsonl", "runtime", "prefix_specification",
                "prefix_prior_forwards", "prefix_prior_completed", "prefix_prior_independent",
                "prefix_prior_runtime", "prefix_prior_implementation"}
    require(required <= set(paths), "Historical source inventory incomplete")
    source_index = {}
    unique_raw_keys = set()
    for name, carrier in (("emoji_cells", "emoji"), ("word_cells", "word"), ("cells.jsonl", None)):
        source_rows = rows(paths[name])
        require(len(source_rows) == {"emoji_cells": 288, "word_cells": 192, "cells.jsonl": 768}[name], "Historical source denominator differs")
        for row in source_rows:
            pair = "original" if carrier else row["pair_id"]
            kind = "shared_absent" if row["variant"] == "absent" else carrier or row["carrier_kind"]
            identity = pair, kind, row["block_id"], row["context"], row["variant"], row["candidate"]
            require(identity not in source_index, "Duplicate historical raw identity")
            require((name, row["cell_id"]) not in unique_raw_keys, "Duplicate raw file/cell identity")
            unique_raw_keys.add((name, row["cell_id"]))
            source_index[identity] = row
    require(len(source_index) == 1248, "Historical raw denominator differs")
    for case in cases:
        for candidate, row in case["candidates"].items():
            require(source_index.get((*case["identity"], candidate)) == row, "Embedded old row differs from pinned raw source")
            origin = "emoji_cells" if case["identity"][1] in ("emoji", "shared_absent") and case["identity"][0] == "original" else (
                "word_cells" if case["identity"][0] == "original" else "cells.jsonl")
            require(case["historical_sources"][candidate] == {"source_file_key": origin, "source_cell_id": row["cell_id"],
                "unique_source_key": [origin, row["cell_id"]]}, "Historical raw-source identity metadata differs")
    require(read(paths["runtime"]) == spec["historical_runtime"] == read(paths["prefix_prior_runtime"]),
            "Historical full-runtime binding differs")
    require(read(paths["prefix_prior_implementation"]) == spec["expected_implementation_sources"], "Implementation pin differs")
    old_spec = read(paths["prefix_specification"])
    for key, entry in old_spec["source_files"].items():
        require(spec["source_files"]["prefix_runner" if key == "runner" else key] == entry, "Historical source pin changed")
    for key in ("historical_runtime", "model_path", "model_artifact", "runtime_packages", "python_version"):
        require(spec[key] == old_spec[key], "Historical model/runtime setting changed: " + key)
    require([c["input_id"] for c in sentinels] == [c["input_id"] for c in old_spec["inputs"]], "Eight-sentinel panel differs")
    old_rows = {(r["input_id"], r["method"]): r for r in rows(paths["prefix_prior_forwards"])}
    for sentinel in sentinels:
        for method in METHODS:
            require(sentinel["expected_scores"][method] == old_rows[sentinel["input_id"], method],
                    "Embedded sentinel score differs from pinned prior forward")
    # Re-run the previous independent receipt validator; its booleans are not
    # accepted merely because the saved report says pass.
    prior_report = prior.analyze(paths["prefix_specification"], paths["prefix_prior_completed"].parent, root)
    require(prior_report["bounded_numerical_gate_passed"] is True and
            read(paths["prefix_prior_independent"])["bounded_numerical_gate_passed"] is True,
            "Prior eight-input bounded gate not independently verified")


def polarity(value):
    return "a" if value > 0 else "b" if value < 0 else "tie"


def describe(values):
    values = list(values)
    require(values and all(finite(x) for x in values), "Empty/nonfinite descriptive denominator")
    return {"n": len(values), "mean": math.fsum(values) / len(values), "median": statistics.median(values),
            "minimum": min(values), "maximum": max(values)}


def decompose(s, eta):
    require(set(s) == {"p", "q"} and all(set(s[c]) == {"a", "b"} for c in s), "Incomplete block grid")
    require(type(eta) is int and eta in (-1, 1) and all(finite(v) for ss in s.values() for v in ss.values()),
            "Invalid decomposition input")
    context, cue = {"p": -1, "q": 1}, {"a": -1, "b": 1}
    t = {c: {v: eta * s[c][v] for v in cue} for c in context}
    margins = {c: {v: context[c] * cue[v] * t[c][v] for v in cue} for c in context}
    terms = [(c, v) for c in context for v in cue]
    coefficients = {name: math.fsum(t[c][v] * (context[c] if cterm else 1) * (cue[v] if vterm else 1)
                    for c, v in terms) / 4 for name, cterm, vterm in
                    (("b0", False, False), ("bC", True, False), ("bV", False, True), ("bCV", True, True))}
    delta = {c: eta * (s[c]["b"] - s[c]["a"]) for c in context}
    h = delta["q"] - delta["p"]
    flat = [margins[c][v] for c, v in terms]
    return {"s": s, "t": t, "H": h, "H_positive": h > 0, "H_sign": "positive" if h > 0 else "negative" if h < 0 else "zero",
            "delta": delta, "coefficients": coefficients, "author_signed_margins": margins,
            "minimum_author_signed_margin": min(flat), "aligned_inputs": sum(v > 0 for v in flat),
            "tied_inputs": sum(v == 0 for v in flat), "effect_crossover": delta["p"] < 0 < delta["q"],
            "all_four_aligned": min(flat) > 0, "H_minus_sum_signed_margins": h - math.fsum(flat),
            "H_minus_four_bCV": h - 4 * coefficients["bCV"]}


def scientific_analysis(cases, records, blocks):
    """Recompute all endpoints from full candidate scores; never drop prefixes."""
    indexed = {(r["input_id"], r["method"]): r for r in records if r["phase"] == "scientific"}
    complete = all(indexed[c["input_id"], m]["status"] == "completed" for c in cases for m in ("padded_a", "padded_b"))
    if not complete:
        return {"status": "not_computed_incomplete_grid", "planned_sequence_scores": 1248, "planned_input_pairs": 624,
                "planned_crossed_inputs": 576, "planned_shared_absent_inputs": 48, "planned_block_tables": 144,
                "completed_sequence_scores": sum(r["status"] == "completed" for r in indexed.values()),
                "block_tables": None, "per_pair_carrier": None, "transitions": None, "new_scientific_n": 0}
    input_rows, pair_index = [], {}
    for case in cases:
        pair, carrier, block, context, cue = case["identity"]
        a, b = (indexed[case["input_id"], m] for m in ("padded_a", "padded_b"))
        old_a, old_b = (case["candidates"][k] for k in ("a", "b"))
        old_s, new_s = old_a["sequence_logprob_sum"] - old_b["sequence_logprob_sum"], a["sequence_logprob_sum"] - b["sequence_logprob_sum"]
        n = case["shared_prefix_token_count"]
        entry = {"input_id": case["input_id"], "pair_id": pair, "carrier": carrier, "block_id": block,
            "family": blocks[block]["family"], "eta": blocks[block]["eta"], "context": context, "cue": cue,
            "old_s": old_s, "new_s": new_s, "s_change": new_s - old_s,
            "old_choice": polarity(old_s), "new_choice": polarity(new_s),
            "choice_or_tie_changed": polarity(old_s) != polarity(new_s), "strict_sign_flip": old_s * new_s < 0,
            "old_prefix_residual": math.fsum(old_a["candidate_token_logprobs"][:n]) - math.fsum(old_b["candidate_token_logprobs"][:n]),
            "new_prefix_residual": math.fsum(a["candidate_token_logprobs"][:n]) - math.fsum(b["candidate_token_logprobs"][:n]),
            "shared_prefix_exact": prefix_exact(case, a, b),
            "candidate_sequence_score_changes": {k: fresh["sequence_logprob_sum"] - old["sequence_logprob_sum"]
                for k, fresh, old in (("a", a, old_a), ("b", b, old_b))},
            "candidate_max_absolute_token_logprob_change": {k: max(abs(x-y) for x,y in zip(
                fresh["candidate_token_logprobs"], old["candidate_token_logprobs"])) for k, fresh, old in (("a", a, old_a), ("b", b, old_b))}}
        if carrier != "shared_absent":
            sign = (-1 if context == "p" else 1) * (-1 if cue == "a" else 1) * entry["eta"]
            entry.update(old_author_signed_margin=sign * old_s, new_author_signed_margin=sign * new_s,
                         author_alignment_changed=(sign * old_s > 0) != (sign * new_s > 0))
        input_rows.append(entry)
        pair_index[tuple(case["identity"])] = entry
    tables = []
    for pair, carrier, block in itertools.product(PAIRS, CARRIERS, sorted(blocks)):
        versions = {}
        for version in ("old", "new"):
            s = {c: {v: pair_index[pair, carrier, block, c, v][version + "_s"] for v in ("a", "b")} for c in ("p", "q")}
            versions[version] = decompose(s, blocks[block]["eta"])
        old, new = versions["old"], versions["new"]
        tables.append({"pair_id": pair, "carrier": carrier, "block_id": block, **blocks[block], **versions,
            "H_change": new["H"] - old["H"], "H_sign_changed": new["H_sign"] != old["H_sign"],
            "effect_crossover_changed": new["effect_crossover"] != old["effect_crossover"],
            "all_four_aligned_changed": new["all_four_aligned"] != old["all_four_aligned"],
            "aligned_inputs_change": new["aligned_inputs"] - old["aligned_inputs"]})
    summaries = []
    for pair, carrier in itertools.product(PAIRS, CARRIERS):
        selected = [r for r in tables if (r["pair_id"], r["carrier"]) == (pair, carrier)]
        rr = [r for r in input_rows if (r["pair_id"], r["carrier"]) == (pair, carrier)]
        summary = {"pair_id": pair, "carrier": carrier, "blocks": 24, "inputs": 96}
        for version in ("old", "new"):
            summary[version] = {"H": describe(r[version]["H"] for r in selected),
                "H_positive_blocks": sum(r[version]["H_positive"] for r in selected),
                "effect_crossover_blocks": sum(r[version]["effect_crossover"] for r in selected),
                "all_four_aligned_blocks": sum(r[version]["all_four_aligned"] for r in selected),
                "aligned_inputs": sum(r[version]["aligned_inputs"] for r in selected),
                "tied_inputs": sum(r[version]["tied_inputs"] for r in selected),
                "minimum_signed_margin": describe(r[version]["minimum_author_signed_margin"] for r in selected)}
        summary["changes"] = {"H": describe(r["H_change"] for r in selected), "s": describe(r["s_change"] for r in rr),
            "choice_or_tie_changed": sum(r["choice_or_tie_changed"] for r in rr),
            **{key: sum(r[key] for r in selected) for key in ("H_sign_changed", "effect_crossover_changed", "all_four_aligned_changed")}}
        summaries.append(summary)
    all_pair_stability = []
    table_index = {(r["pair_id"], r["carrier"], r["block_id"]): r for r in tables}
    for carrier in CARRIERS:
        summary = {"carrier": carrier, "blocks": 24, "inputs": 96}
        for version in ("old", "new"):
            metrics = {key + "_all_pairs_blocks": sum(all(table_index[p, carrier, b][version][key] for p in PAIRS) for b in blocks)
                       for key in ("H_positive", "effect_crossover", "all_four_aligned")}
            metrics["candidate_polarity_varies_across_pairs_inputs"] = sum(len({pair_index[p, carrier, b, c, v][version + "_choice"]
                for p in PAIRS}) > 1 for b in blocks for c in ("p", "q") for v in ("a", "b"))
            summary[version] = metrics
        all_pair_stability.append(summary)
    absent = []
    for carrier, block in itertools.product(CARRIERS, sorted(blocks)):
        entry = {"pair_id": "original", "carrier": carrier, "block_id": block, "baseline": "shared_original_absent"}
        for version in ("old", "new"):
            base = {c: pair_index["original", "shared_absent", block, c, "absent"][version + "_s"] for c in ("p", "q")}
            unshifted = table_index["original", carrier, block][version]
            shifted = {c: {v: unshifted["s"][c][v] - base[c] for v in ("a", "b")} for c in ("p", "q")}
            decomposition = decompose(shifted, blocks[block]["eta"])
            entry[version] = {"absent_s": base, "baseline_subtracted": decomposition,
                              "H_change_from_baseline_subtraction": decomposition["H"] - unshifted["H"]}
        absent.append(entry)
    crossed = [r for r in input_rows if r["carrier"] != "shared_absent"]
    absent_inputs = [r for r in input_rows if r["carrier"] == "shared_absent"]
    transitions = {"H_sign": [r for r in tables if r["H_sign_changed"]],
        "effect_crossover": [r for r in tables if r["effect_crossover_changed"]],
        "all_four_aligned": [r for r in tables if r["all_four_aligned_changed"]],
        "crossed_candidate_choice": [r for r in crossed if r["choice_or_tie_changed"]],
        "shared_absent_candidate_choice": [r for r in absent_inputs if r["choice_or_tie_changed"]]}
    return {"status": "complete_descriptive_development_grid", "sequence_scores": 1248, "input_pairs": 624,
        "crossed_inputs": 576, "shared_absent_inputs": 48, "block_table_count": 144,
        "development_scenarios": 24, "families": 6, "new_scientific_n": 0,
        "input_rows": input_rows, "block_tables": tables, "per_pair_carrier": summaries,
        "all_pair_stability": all_pair_stability, "transitions": transitions,
        "transition_counts": {key: len(value) for key, value in transitions.items()},
        "crossed_s_change": describe(r["s_change"] for r in crossed),
        "maximum_absolute_crossed_s_change": max(abs(r["s_change"]) for r in crossed),
        "maximum_absolute_H_change": max(abs(r["H_change"]) for r in tables),
        "shared_absent_diagnostics": absent,
        "absent_coverage": {"unique_scored_absent_pairs": 48, "shared_original_block_carrier_tables": 48,
            "new_wording_absent_scores_available": False, "shared_baseline_is_not_duplicated_scientific_n": True},
        "all_624_prefix_residuals_zero": all(r["new_prefix_residual"] == 0 for r in input_rows),
        "old_nonzero_prefix_residuals": {"crossed": sum(r["old_prefix_residual"] != 0 for r in crossed),
            "shared_absent": sum(r["old_prefix_residual"] != 0 for r in absent_inputs)},
        "interpretation": "Descriptive rescoring of the same authored development scenarios; no human accuracy, independent confirmation, emoji-specific advantage, or causal result."}


def analyze(specification, run_dir, root=ROOT):
    specification, run_dir, root = safe(specification), safe(run_dir), safe(root)
    spec, started, completed = read(specification), read(run_dir / "run_started.json"), read(run_dir / "run_completed.json")
    cases, sentinels, blocks = validate_spec(spec)
    paths = prior.source_paths(root, spec)
    verify_sources(cases, sentinels, paths, spec, root)
    require(started["protocol_id"] == completed["protocol_id"] == PROTOCOL and
            started["specification_sha256"] == digest(specification), "Run/specification identity differs")
    require(started["actual_source_files"] == spec["source_files"] and started["compute_policy"] == POLICY and
            started["planned_forward_attempts"] == completed["planned_forward_attempts"] == 1312, "Run policy/source binding differs")
    mandatory = {"run_started.json", "forwards.jsonl", "diagnostics.json", "occupancy_checks.json"}
    allowed = mandatory | {"runtime.json", "implementation_sources.json"}
    artifacts = completed["artifacts"]
    require(mandatory <= set(artifacts) <= allowed, "Artifact inventory differs")
    for name in allowed:
        require((run_dir / name).exists() == (name in artifacts), "Missing/unbound artifact")
    for name, pin in artifacts.items():
        require(valid_hash(pin) and digest(run_dir / name) == pin, "Run artifact hash differs: " + name)
    records = rows(run_dir / "forwards.jsonl")
    attempts, sentinel_matches = verify_records(cases, sentinels, records)
    gates = derive_gates(cases, records, sentinel_matches, sentinels)
    diagnostics = read(run_dir / "diagnostics.json")
    for key, value in {**gates, **derive_detailed_diagnostics(cases, sentinels, records)}.items():
        require(diagnostics[key] == value, "Runner diagnostic disagrees: " + key)
    runtime = read(run_dir / "runtime.json") if "runtime.json" in artifacts else None
    runtime_equal = runtime == spec["historical_runtime"] if runtime is not None else False
    implementation = read(run_dir / "implementation_sources.json") if "implementation_sources.json" in artifacts else None
    implementation_equal = implementation == spec["expected_implementation_sources"] if implementation is not None else False
    require(completed["full_runtime_identity_matches_historical"] is runtime_equal, "Runtime summary disagrees")
    require(completed["implementation_sources_match_prior"] is implementation_equal, "Implementation summary disagrees")
    require(attempts == 0 or runtime_equal and implementation_equal, "Forward executed without exact runtime/implementation identity")
    resource_receipt = read(run_dir / "occupancy_checks.json")
    resources = prior.verify_resources(resource_receipt, records, POLICY)
    require(type(started["pid"]) is int and started["pid"] > 0 and all(o["own_pid"] == started["pid"] for o in resource_receipt["observations"]),
            "Resource/run PID differs")
    # Unlike the historical helper's legacy allowance, every attempted call in
    # this new protocol must have identifiable before/after resource boundaries.
    require(attempts == 0 or resources["event_labelled_observations"] > 0, "Missing event-labelled resource checks")
    observed_boundaries = {(o.get("event_id"), o.get("boundary")) for o in resource_receipt["observations"]}
    require(all((r["event_id"], boundary) in observed_boundaries for r in records if r["forward_attempted"]
                for boundary in ("before", "after")), "Attempted call lacks a resource boundary receipt")
    require(completed["forward_attempts"] == attempts and completed["status_counts"] == dict(Counter(r["status"] for r in records)),
            "Completion denominator differs")
    require(completed["numerical_gate_passed"] is gates["numerical_gate_passed"], "Completion gate disagrees")
    require(completed["planned_scientific_sequence_scores"] == 1248 and completed["planned_sentinel_forwards"] == 64,
            "Completion scientific/sentinel denominator differs")
    for key in ("new_scientific_n", "new_stimuli", "tokenizer_calls", "generation_calls", "downloads"):
        require(type(completed[key]) is int and completed[key] == 0, "Run ceiling differs: " + key)
    require(finite(completed["elapsed_seconds"]) and completed["elapsed_seconds"] >= 0, "Invalid run duration")
    peak = completed["peak_torch_memory_mib"]
    if peak is not None:
        require(all(finite(peak[k]) and 0 <= peak[k] <= POLICY["allocator_cap_mib"] for k in ("allocated_mib", "reserved_mib")),
                "Allocator cap exceeded")
    stopped = completed["stop_reason"] is not None
    expected_status = "stopped_partial" if stopped else "completed_numerical_gate_passed" if gates["numerical_gate_passed"] else "completed_numerical_gate_failed"
    require(completed["status"] == expected_status, "Completion status disagrees")
    require(stopped or gates["all1312_scores_completed"] and gates["all_scored_boundaries_admissible"] and
            resources["all_observations_allowed"], "Unreported partial/resource stop")
    if not stopped:
        require(completed["elapsed_seconds"] < POLICY["walltime_seconds"], "Walltime bound exceeded")
    resource_gate = resources["all_observations_allowed"] and resources["per_forward_allowed_before_and_after"] is True
    passed = gates["numerical_gate_passed"] and runtime_equal and implementation_equal and resource_gate and not stopped
    analysis = scientific_analysis(cases, records, blocks)
    analysis["eligible_for_versioned_score_replacement"] = passed
    return {"protocol_id": PROTOCOL + "-independent-analysis", "schema_version": 1,
        "status": "verified_complete_matched_shape_grid" if passed else "verified_partial_or_gate_not_passed",
        "receipt_integrity_verified": True, "bounded_numerical_gate_passed": passed,
        "numerical_gate_passed": gates["numerical_gate_passed"], "resource_gate_passed": resource_gate,
        "score_equalities_gate_passed": gates["all1312_scores_completed"] and gates["all624_prefixes_exact"] and gates["sentinel_exact_parity"] and gates["all_sentinel_scientific_repeats_exact"],
        "full_runtime_identity_matches_historical": runtime_equal if runtime is not None else None,
        "implementation_identity_matches_prior_panel": implementation_equal if implementation is not None else None,
        "counts": {**gates, "actual_forward_attempts": attempts, "planned_engineering_sentinel_forwards": 64},
        "status_counts": dict(Counter(r["status"] for r in records)), "stop_reason": completed["stop_reason"],
        "resource_validation": resources, "peak_torch_memory_mib": peak, "analysis": analysis,
        "new_scientific_n": 0, "human_accuracy_measured": False, "confirmatory_evidence": False,
        "claim_ceiling": "Same 24 authored development scenarios and six families. New measurement version only; no new stimuli, independent replication, human validation, or causal claim.",
        "limitations": ["Shared predictor-logit equality is attested by saved hashes and selected probabilities; full logits were not retained.",
            "Resource observations leave unobserved intervals and do not establish peer-workload throughput impact.",
            "Word/emoji token geometry differs; these data do not establish emoji-specific advantage.",
            "No new-wording absent controls were acquired; the original absent controls are shared diagnostics only."],
        "provenance": {"checker_sha256": digest(Path(__file__)), "prior_independent_helper_sha256": HELPER_SHA,
            "specification_sha256": digest(specification), "run_completed_sha256": digest(run_dir / "run_completed.json"),
            "artifact_sha256": artifacts, "source_files": spec["source_files"],
            "checker_model_forwards": 0, "checker_tokenizer_calls": 0, "checker_network_calls": 0}}


def write_output(path, value):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    require(not safe(args.output).exists(), "Refusing to overwrite analysis output")
    result = analyze(args.specification, args.run_dir, args.root)
    write_output(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "bounded_numerical_gate_passed", "new_scientific_n")}, sort_keys=True))


if __name__ == "__main__":
    main()
