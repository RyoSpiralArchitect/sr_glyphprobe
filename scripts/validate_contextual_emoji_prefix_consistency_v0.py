#!/usr/bin/env python3
"""Independently check a bounded numerical diagnostic, without model imports.

This checker reads receipts only. It independently reconstructs input geometry,
arithmetic and gates; it cannot regenerate logits from their saved SHA-256.
Partial or refused acquisitions remain explicitly incomplete, not successes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-prefix-consistency-v0"
METHODS = ("original_a_1", "original_b_1", "original_a_2", "original_b_2",
           "padded_a", "padded_b", "prefix_only")
GATES = ("historical_exact_parity", "repeated_original_exact_equality",
         "padded_prefix_exact_equality", "padded_predictor_logits_exact_equality")
POLICY = {"gpu_index": 0, "allocator_cap_mib": 9728, "driver_allowance_mib": 512,
          "minimum_free_before_load_mib": 12288, "minimum_free_before_forward_mib": 4096,
          "walltime_seconds": 600, "maximum_forward_attempts": 56,
          "allow_other_pids": False, "change_peer_processes": False}
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
PORTABLE_REVISION = "portable_deterministic_auxiliary_squared_shift_v1"
PORTABLE_OPERATION = "For each coefficient-change row only: mean_squared_cell_shift = math.fsum(d*d for four binary64 contextual-score differences)/4; all other fields unchanged"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe(path):
    path = Path(path)
    require(path.name not in PROTECTED and path.resolve().name not in PROTECTED,
            "Protected bank access prohibited")
    return path.resolve()


def digest(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def decode(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=nonfinite)


def read(path):
    return decode(safe(path).read_text(encoding="utf-8"))


def rows(path):
    lines = safe(path).read_text(encoding="utf-8").splitlines()
    require(lines and all(line.strip() for line in lines), "Empty/blank forward record")
    return [decode(line) for line in lines]


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def token_ids(values):
    return isinstance(values, list) and values and all(type(v) is int and 0 <= v < 128256 for v in values)


def probabilities(values, total, expected_count):
    require(isinstance(values, list) and len(values) == expected_count and
            all(finite(v) and v <= 0 for v in values), "Invalid token probabilities")
    require(finite(total) and math.fsum(values) == total, "Exact saved token sum differs")


def validate_cases(spec):
    require(spec["protocol_id"] == PROTOCOL and spec["schema_version"] in (1, 2), "Unsupported protocol")
    if spec["schema_version"] == 2:
        require(spec["preflight_revision"] == PORTABLE_REVISION, "Unsupported preflight revision")
    require(spec["compute_policy"] == POLICY and spec["methods"] == list(METHODS), "Policy/method pin differs")
    require(spec["planned_inputs"] == 8 and spec["planned_forward_attempts"] == 56, "Planned denominator differs")
    for key in ("new_stimuli", "new_scientific_n", "tokenizer_calls", "generation_calls", "downloads", "prepare_model_forwards"):
        require(type(spec[key]) is int and spec[key] == 0, f"Specification ceiling differs: {key}")
    scoring = spec["scoring"]
    require(scoring["dtype"] == "bfloat16" and scoring["attention"] == "eager" and
            scoring["use_cache"] is False and scoring["log_softmax_dtype"] == "float32" and
            scoring["historical_parity_tolerance"] == 0 and scoring["same_shape_prefix_tolerance"] == 0,
            "Scoring identity/tolerance differs")
    cases = spec["inputs"]
    require(len(cases) == 8 and len({c["input_id"] for c in cases}) == 8, "Eight unique inputs required")
    for case in cases:
        identity = case["identity"]
        require(len(identity) == 5 and all(isinstance(v, str) and v for v in identity) and
                case["input_id"] == "/".join(identity), "Input identity differs")
        require(identity[0] in ("original", "explicit_negation", "adjective_pair") and
                identity[1] in ("emoji", "word") and identity[3] in ("p", "q") and identity[4] in ("a", "b"),
                "Unknown historical identity")
        require(set(case["candidates"]) == {"a", "b"}, "Candidate pair incomplete")
        for candidate, row in case["candidates"].items():
            prompt, tokens, full = row["prompt_token_ids"], row["candidate_token_ids"], row["input_token_ids"]
            require(row["status"] == "completed" and token_ids(prompt) and token_ids(tokens) and
                    full == prompt + tokens and len(full) <= 160, "Historical token geometry differs")
            require(row["prompt_token_count"] == len(prompt) and row["candidate_token_count"] == len(tokens) and
                    row["first_candidate_predictor_position"] == len(prompt) - 1, "Historical predictor boundary differs")
            for field, expected in (("block_id", identity[2]), ("context", identity[3]),
                                    ("variant", identity[4]), ("candidate", candidate)):
                require(row[field] == expected, f"Historical identity field differs: {field}")
            probabilities(row["candidate_token_logprobs"], row["sequence_logprob_sum"], len(tokens))
        a, b = (case["candidates"][c] for c in ("a", "b"))
        require(a["prompt_token_ids"] == b["prompt_token_ids"], "Candidate prompts differ")
        n = case["shared_prefix_token_count"]
        require(type(n) is int and 0 < n <= min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])),
                "Invalid shared prefix length")
        require(a["candidate_token_ids"][:n] == b["candidate_token_ids"][:n] == case["shared_prefix_token_ids"],
                "Shared prefix token identity differs")
        require(n == min(len(a["candidate_token_ids"]), len(b["candidate_token_ids"])) or
                a["candidate_token_ids"][n] != b["candidate_token_ids"][n], "Shared prefix not maximal")
        require(math.fsum(a["candidate_token_logprobs"][:n]) - math.fsum(b["candidate_token_logprobs"][:n]) ==
                case["historical_prefix_residual"], "Historical prefix residual differs")
    return cases


def geometry(case, method):
    """Independent construction from the recorded prompt/candidate token IDs."""
    candidate = "b" if method in ("original_b_1", "original_b_2", "padded_b") else "a"
    saved = case["candidates"][candidate]
    prompt = list(saved["prompt_token_ids"])
    continuation = list(saved["candidate_token_ids"])
    prefix = case["shared_prefix_token_count"]
    if method == "prefix_only":
        continuation = continuation[:prefix]
    valid = len(prompt) + len(continuation)
    padded = method in ("padded_a", "padded_b")
    total = max(len(r["input_token_ids"]) for r in case["candidates"].values()) if padded else valid
    return {"input_token_ids": prompt + continuation + [0] * (total - valid),
            "attention_mask": [1] * valid + [0] * (total - valid),
            "position_ids": list(range(total)) if padded else None,
            "valid_length": valid, "total_length": total, "prompt_length": len(prompt),
            "candidate_token_ids": continuation, "predictor_positions": list(range(len(prompt) - 1, valid - 1)),
            "normalization_start": len(prompt) - 1, "normalization_stop": total - 1,
            "shared_prefix_token_count": prefix}


def verify_forwards(cases, records):
    planned = [(case, method) for case in cases for method in METHODS]
    require(len(records) == 56 and len({r["event_id"] for r in records}) == 56, "Forward denominator/duplicate differs")
    halted = False
    attempts = 0
    for (case, method), row in zip(planned, records):
        event_id = f"{case['input_id']}::{method}"
        require(row["event_id"] == event_id and row["input_id"] == case["input_id"] and row["method"] == method,
                "Forward identity/order differs")
        expected = geometry(case, method)
        require(row["geometry"] == expected, "Forward geometry differs")
        status = row["status"]
        require(status in ("completed", "failed", "not_run") and type(row["forward_attempted"]) is bool,
                "Invalid forward status")
        require(row["forward_attempted"] == (status != "not_run"), "Attempt/status mismatch")
        require(not halted or status == "not_run", "Forward continued after a stop boundary")
        attempts += row["forward_attempted"]
        if status == "completed":
            probabilities(row["candidate_token_logprobs"], row["sequence_logprob_sum"], len(expected["candidate_token_ids"]))
            require(row["shared_prediction_logits_shape"] == [case["shared_prefix_token_count"], 128256] and
                    row["shared_prediction_logits_dtype"] == "float32" and valid_hash(row["shared_prediction_logits_sha256"]) and
                    row["logits_hash_byte_order"] in ("little", "big"), "Shared logit receipt shape/hash/type differs")
            require(row["normalization_rectangle_shape"] == [expected["normalization_stop"] - expected["normalization_start"], 128256],
                    "Normalization rectangle differs")
            require(finite(row["elapsed_seconds"]) and row["elapsed_seconds"] >= 0, "Invalid forward duration")
            if method.startswith("original"):
                candidate = "b" if method.startswith("original_b") else "a"
                old = case["candidates"][candidate]
                actual = (row["candidate_token_logprobs"] == old["candidate_token_logprobs"] and
                          row["sequence_logprob_sum"] == old["sequence_logprob_sum"])
                require(row.get("historical_exact_parity") is actual, "Saved historical parity disagrees with arithmetic")
                require(actual or row.get("boundary_error_after_score"), "Failed historical parity did not stop run")
        else:
            require(isinstance(row.get("reason"), str) and row["reason"], "Missing stop reason")
            require(not any(k in row for k in ("candidate_token_logprobs", "sequence_logprob_sum")), "Unscored row contains scores")
        if status != "completed" or row.get("boundary_error_after_score"):
            halted = True
    require(attempts <= 56, "Forward-attempt cap exceeded")
    return attempts


def polarity(score):
    return "a" if score > 0 else "b" if score < 0 else "tie"


def derive(cases, records):
    diagnostics, compact = [], []
    for case in cases:
        by_method = {r["method"]: r for r in records if r["input_id"] == case["input_id"]}
        available = lambda method: by_method[method]["status"] == "completed"
        n = case["shared_prefix_token_count"]
        result = {"input_id": case["input_id"], **{key: None for key in GATES}}
        if all(available(m) for m in METHODS[:4]):
            result["historical_exact_parity"] = all(
                by_method[m]["candidate_token_logprobs"] == case["candidates"]["b" if m.startswith("original_b") else "a"]["candidate_token_logprobs"] and
                by_method[m]["sequence_logprob_sum"] == case["candidates"]["b" if m.startswith("original_b") else "a"]["sequence_logprob_sum"]
                for m in METHODS[:4])
            result["repeated_original_exact_equality"] = all(
                by_method[f"original_{c}_1"]["candidate_token_logprobs"] == by_method[f"original_{c}_2"]["candidate_token_logprobs"] and
                by_method[f"original_{c}_1"]["shared_prediction_logits_sha256"] == by_method[f"original_{c}_2"]["shared_prediction_logits_sha256"]
                for c in ("a", "b"))
        if available("padded_a") and available("padded_b"):
            a, b = (by_method[m] for m in ("padded_a", "padded_b"))
            result["padded_prefix_exact_equality"] = a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n]
            result["padded_predictor_logits_exact_equality"] = (
                a["shared_prediction_logits_sha256"] == b["shared_prediction_logits_sha256"] and
                a["shared_prediction_logits_shape"] == b["shared_prediction_logits_shape"] and
                a["logits_hash_byte_order"] == b["logits_hash_byte_order"])
            result["padded_prefix_max_absolute_logprob_difference"] = max(abs(x-y) for x,y in zip(
                a["candidate_token_logprobs"][:n], b["candidate_token_logprobs"][:n]))
        result["cross_shape_descriptive_comparisons"] = []
        for left, right in (("original_a_1", "original_b_1"), ("original_a_1", "padded_a"),
                            ("original_b_1", "padded_b"), ("original_a_1", "prefix_only"),
                            ("original_b_1", "prefix_only"), ("padded_a", "prefix_only")):
            if available(left) and available(right):
                a, b = by_method[left], by_method[right]
                result["cross_shape_descriptive_comparisons"].append({"left": left, "right": right,
                    "prefix_logprobs_exact_equal": a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n],
                    "prefix_max_absolute_logprob_difference": max(abs(x-y) for x,y in zip(
                        a["candidate_token_logprobs"][:n], b["candidate_token_logprobs"][:n])),
                    "shared_predictor_logits_exact_equal": a["shared_prediction_logits_sha256"] == b["shared_prediction_logits_sha256"],
                    "not_a_historical_total_parity_gate": True})
        scores = {}
        for label, methods in (("original", ("original_a_1", "original_b_1")), ("padded", ("padded_a", "padded_b"))):
            value = (by_method[methods[0]]["sequence_logprob_sum"] - by_method[methods[1]]["sequence_logprob_sum"]
                     if all(available(m) for m in methods) else None)
            scores[label] = {"a_minus_b_logprob": value, "preferred_candidate": polarity(value) if value is not None else None}
        comparison = None
        result["full_score_geometry_comparison"] = None
        if all(scores[m]["a_minus_b_logprob"] is not None for m in ("original", "padded")):
            a, b = (scores[m]["a_minus_b_logprob"] for m in ("original", "padded"))
            comparison = {"score_change": b-a, "strict_sign_flip": a*b < 0,
                          "any_tie": a == 0 or b == 0, "polarity_changed": polarity(a) != polarity(b)}
            result["full_score_geometry_comparison"] = {"s_original": a, "s_padded": b,
                "original_preferred_candidate": polarity(a), "padded_preferred_candidate": polarity(b),
                "preference_or_tie_changed": polarity(a) != polarity(b), "strict_nonzero_polarity_flip": a*b < 0,
                "same_candidate_max_absolute_logprob_difference": {c: max(abs(x-y) for x,y in zip(
                    by_method[f"original_{c}_1"]["candidate_token_logprobs"], by_method[f"padded_{c}"]["candidate_token_logprobs"]))
                    for c in ("a", "b")}, "descriptive_only_not_corrected_scores_or_H_verdict": True}
        compact.append({"input_id": case["input_id"], "selection_reason": case["selection_reason"],
            "completed_forwards": sum(available(m) for m in METHODS), "planned_forwards": 7,
            "historical_prefix_residual": case["historical_prefix_residual"],
            "shared_prefix_token_count": n, **{k: result[k] for k in GATES},
            "maximum_cross_shape_prefix_logprob_difference": max((c["prefix_max_absolute_logprob_difference"]
                for c in result["cross_shape_descriptive_comparisons"]), default=None),
            "original_vs_padded_scores": scores, "polarity_comparison": comparison})
        diagnostics.append(result)
    all_done = all(r["status"] == "completed" for r in records)
    boundaries_admissible = not any("boundary_error_after_score" in r for r in records)
    passed = all_done and boundaries_admissible and all(d[key] is True for d in diagnostics for key in GATES)
    return {"input_diagnostics": diagnostics, "all_56_scores_completed": all_done,
            "all_scored_boundaries_admissible": boundaries_admissible,
            "numerical_gate_passed": passed, "block_H_recomputed": False,
            "scientific_population_verdict": None}, compact


def verify_resources(receipt, records, policy):
    observations = receipt["observations"]
    require(isinstance(observations, list) and observations, "Missing resource observations")
    blocked = []
    for index, row in enumerate(observations):
        require(row["status"] in ("allowed", "blocked") and type(row["own_pid"]) is int and row["own_pid"] > 0,
                "Invalid resource status/PID")
        if row["status"] == "blocked":
            require(isinstance(row.get("error"), str) and row["error"], "Blocked observation lacks reason")
            blocked.append(index)
            continue
        require(row["phase"] in ("before_load", "forward_boundary"), "Unknown resource phase")
        require(all(type(row[k]) is int and row[k] >= 0 for k in ("total_mib", "free_mib", "minimum_free_mib", "own_process_mib")),
                "Invalid resource memory values")
        minimum = policy["minimum_free_before_load_mib" if row["phase"] == "before_load" else "minimum_free_before_forward_mib"]
        process = row["process_memory_mib"]
        require(all(isinstance(k, str) and k.isdigit() and type(v) is int and v >= 0 for k,v in process.items()),
                "Invalid GPU process inventory")
        peers = sorted(int(k) for k in process if int(k) != row["own_pid"])
        require(row["observed_peer_pids"] == peers == [], "Allowed observation contains peer GPU PID")
        require(row["minimum_free_mib"] == minimum and minimum <= row["free_mib"] <= row["total_mib"] and
                row["own_process_mib"] == process.get(str(row["own_pid"]), 0) and
                row["own_process_mib"] <= policy["allocator_cap_mib"] + policy["driver_allowance_mib"],
                "Allowed resource observation violates policy")
    maximum = max((o.get("own_process_mib", 0) for o in observations), default=0)
    require(receipt["maximum_observed_own_process_mib"] == maximum, "Maximum observed memory differs")
    attempted = [r for r in records if r["forward_attempted"]]
    labelled = [o for o in observations if o.get("event_id") is not None]
    coverage = None
    if attempted and labelled:
        by_event = {}
        planned_ids = {r["event_id"] for r in records}
        rank = {r["event_id"]: index for index, r in enumerate(records)}
        observed_order = []
        for row in labelled:
            require(row["event_id"] in planned_ids and row.get("boundary") in ("before", "after"),
                    "Unknown resource event/boundary")
            require(row["phase"] == "forward_boundary", "Forward event has wrong resource phase")
            key = (row["event_id"], row["boundary"])
            require(key not in by_event, "Duplicate resource event/boundary")
            by_event[key] = row
            observed_order.append(2 * rank[row["event_id"]] + (row["boundary"] == "after"))
        require(observed_order == sorted(observed_order), "Resource event boundaries out of order")
        for row in attempted:
            before = by_event.get((row["event_id"], "before"))
            require(before is not None and before["status"] == "allowed", "Attempt lacks allowed before boundary")
            after = by_event.get((row["event_id"], "after"))
            if row["status"] == "completed" and not row.get("boundary_error_after_score"):
                require(after is not None and after["status"] == "allowed", "Completed call lacks allowed after boundary")
        coverage = all(by_event.get((r["event_id"], boundary), {}).get("status") == "allowed"
                       for r in attempted for boundary in ("before", "after"))
    elif attempted:
        # Older runner format has no event attribution: counts alone do not
        # prove that a particular check brackets a particular forward.
        require(len([o for o in observations if o["phase"] == "forward_boundary"]) >= len(attempted),
                "Fewer resource boundaries than actual attempts")
    if blocked:
        require(blocked == [len(observations) - 1], "Resource observation continued after refusal")
    return {"observations": len(observations), "blocked_observations": len(blocked),
            "all_observations_allowed": not blocked, "per_forward_allowed_before_and_after": coverage,
            "event_labelled_observations": len(labelled), "maximum_observed_own_process_mib": maximum,
            "minimum_observed_free_mib": min((o["free_mib"] for o in observations if "free_mib" in o), default=None),
            "unobserved_between_checks": True, "peer_workload_impact_measured": False}


def source_paths(root, spec):
    bound = {}
    for key, entry in spec["source_files"].items():
        relative = Path(entry["path"])
        require(not relative.is_absolute() and ".." not in relative.parts and valid_hash(entry["sha256"]), "Invalid source pin")
        path = safe(root / relative)
        require(path.is_relative_to(root) and digest(path) == entry["sha256"], f"Pinned source differs: {key}")
        bound[key] = path
    require(bound, "Missing source pins")
    return bound


def verify_historical_rows(cases, paths):
    required = {"emoji_cells", "word_cells", "cells.jsonl", "runtime"}
    require(required <= set(paths), "Historical raw/runtime source bindings incomplete")
    index = {}
    for name, carrier in (("emoji_cells", "emoji"), ("word_cells", "word"), ("cells.jsonl", None)):
        for row in rows(paths[name]):
            if row["variant"] == "absent":
                continue
            key = ("original" if carrier else row["pair_id"], carrier or row["carrier_kind"],
                   row["block_id"], row["context"], row["variant"], row["candidate"])
            require(key not in index, "Duplicate historical source cell")
            index[key] = row
    for case in cases:
        for candidate, row in case["candidates"].items():
            key = (*case["identity"], candidate)
            require(key in index and row == index[key], "Embedded historical cell differs from pinned raw source")


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def exact_differences(before, after, path=()):
    """Compare all fields; no float tolerance or key exclusion is permitted."""
    if isinstance(before, dict) and isinstance(after, dict):
        require(before.keys() == after.keys(), "Portable report dictionary keys differ")
        result = []
        for key in sorted(before):
            result.extend(exact_differences(before[key], after[key], path + (key,)))
        return result
    if isinstance(before, list) and isinstance(after, list):
        require(len(before) == len(after), "Portable report list lengths differ")
        result = []
        for index in range(len(before)):
            result.extend(exact_differences(before[index], after[index], path + (index,)))
        return result
    return [] if before == after else [{"path": list(path), "before": before, "after": after}]


def deterministic_squared_shift(parent):
    """Independent scalar replay of the sole versioned auxiliary operation."""
    replay = decode(json.dumps(parent, allow_nan=False))
    tables = replay["decompositions"]
    lookup = {(row["pair_id"], row["carrier"], row["block_id"]): row for row in tables}
    require(len(tables) == len(lookup) == 144, "Portable replay requires 144 unique decomposition tables")
    changes = replay["coefficient_change_rows"]
    require(len(changes) == 144, "Portable replay requires 144 coefficient-change rows")
    seen = set()
    for row in changes:
        identity = (row["pair_from"], row["pair_to"], row["carrier"], row["block_id"])
        require(identity not in seen and identity[0] != identity[1], "Duplicate/invalid portable comparison identity")
        seen.add(identity)
        left_key = (row["pair_from"], row["carrier"], row["block_id"])
        right_key = (row["pair_to"], row["carrier"], row["block_id"])
        require(left_key in lookup and right_key in lookup, "Portable comparison references absent table")
        squared = []
        for context, cue in (("p", "a"), ("p", "b"), ("q", "a"), ("q", "b")):
            left, right = lookup[left_key]["t"][context][cue], lookup[right_key]["t"][context][cue]
            require(finite(left) and finite(right), "Nonfinite portable scalar input")
            delta = right - left
            squared.append(delta * delta)
        row["mean_squared_cell_shift"] = math.fsum(squared) / 4
        require(finite(row["mean_squared_cell_shift"]), "Nonfinite deterministic squared shift")
    return replay


def auxiliary_differences_only(changes):
    seen = set()
    for change in changes:
        require(set(change) == {"path", "before", "after"}, "Unexpected auxiliary difference fields")
        path = change["path"]
        require(isinstance(path, list) and len(path) == 3 and path[0] == "coefficient_change_rows" and
                type(path[1]) is int and 0 <= path[1] < 144 and path[2] == "mean_squared_cell_shift" and
                finite(change["before"]) and finite(change["after"]) and change["before"] != change["after"],
                "Change extends beyond declared auxiliary field")
        require(tuple(path) not in seen, "Duplicate auxiliary difference path")
        seen.add(tuple(path))


def verify_portable_preflight(spec, paths, started):
    if spec["schema_version"] == 1:
        return {"schema_version": 1, "portable_reference_required": False,
                "portable_deterministic_replay_verified": None, "native_replay_receipt_verified": None}
    required = {"measurement", "measurement_analyzer", "runner", "portable_measurement_reference"}
    require(required <= set(paths), "Portable preflight sources incomplete")
    entry = spec["portable_measurement_reference"]
    require(entry == spec["source_files"]["portable_measurement_reference"], "Portable reference/spec binding differs")
    parent = read(paths["measurement"])
    replay = deterministic_squared_shift(parent)
    changes = exact_differences(parent, replay)
    auxiliary_differences_only(changes)
    expected_payload = {"protocol_id": "glyphprobe-measurement-portable-squared-shift-replay-v1",
        "parent_analysis_sha256": digest(paths["measurement"]),
        "parent_analyzer_sha256": digest(paths["measurement_analyzer"]),
        "replay_implementation_sha256": digest(paths["runner"]),
        "operation": PORTABLE_OPERATION, "parent_artifact_modified": False,
        "model_probability_tolerance": 0, "all_other_fields_exactly_equal_to_parent": True,
        "changes_from_parent": changes, "analysis": replay}
    portable = read(paths["portable_measurement_reference"])
    require(portable == expected_payload, "Full deterministic portable reference differs")
    reference_sha = hashlib.sha256(canonical_bytes(expected_payload)).hexdigest()
    require(reference_sha == entry["sha256"], "Portable reference canonical hash differs")
    native_receipt = started["measurement_native_replay_portability"]
    require(native_receipt["protocol_id"] == "glyphprobe-measurement-native-replay-portability-diagnostic-v1" and
            native_receipt["parent_analysis_sha256"] == digest(paths["measurement"]) and
            native_receipt["portable_reference_sha256"] == reference_sha,
            "Native replay provenance differs")
    native_changes = native_receipt["native_replay_differences_from_parent"]
    auxiliary_differences_only(native_changes)
    reconstructed_native = decode(json.dumps(parent, allow_nan=False))
    for change in native_changes:
        row = reconstructed_native["coefficient_change_rows"][change["path"][1]]
        require(row["mean_squared_cell_shift"] == change["before"], "Native difference before value differs from parent")
        row["mean_squared_cell_shift"] = change["after"]
    require(exact_differences(parent, reconstructed_native) == native_changes, "Native difference order/content differs")
    require(native_receipt["native_replay_exactly_equals_parent"] is (not native_changes) and
            native_receipt["differences_confined_to_declared_auxiliary_field"] is True and
            native_receipt["full_deterministic_replay_exactly_equals_portable_reference"] is True,
            "Native replay gate metadata differs")
    require(hashlib.sha256(canonical_bytes(reconstructed_native)).hexdigest() == native_receipt["native_analysis_json_sha256"],
            "Reconstructed native report hash differs")
    require(deterministic_squared_shift(reconstructed_native) == replay, "Native deterministic replay differs")
    require(all(isinstance(native_receipt[k], str) and native_receipt[k] for k in ("python", "platform")),
            "Native replay environment missing")
    require(native_receipt["causal_source_of_native_difference"] ==
            "not_isolated; native power expression and deterministic multiplication use different operation definitions",
            "Native replay cause ceiling changed")
    return {"schema_version": 2, "preflight_revision": PORTABLE_REVISION,
        "portable_reference_required": True, "portable_reference_sha256": reference_sha,
        "portable_deterministic_replay_verified": True,
        "portable_auxiliary_fields_changed_from_parent": len(changes),
        "all_nonauxiliary_fields_exactly_equal_to_parent": True, "parent_artifact_modified": False,
        "native_replay_receipt_verified": True, "native_auxiliary_fields_changed_from_parent": len(native_changes),
        "native_replay_exactly_equals_parent": not native_changes,
        "native_analysis_json_sha256": native_receipt["native_analysis_json_sha256"],
        "remote_native_execution_independently_repeated": False,
        "verification_scope": "Reconstructed recorded native differences and canonical hash; no remote/native execution or causal attribution."}


def analyze(specification, run_dir, root=ROOT):
    specification, run_dir, root = safe(specification), safe(run_dir), safe(root)
    spec, started, completed = read(specification), read(run_dir / "run_started.json"), read(run_dir / "run_completed.json")
    cases = validate_cases(spec)
    paths = source_paths(root, spec)
    verify_historical_rows(cases, paths)
    require(started["protocol_id"] == completed["protocol_id"] == PROTOCOL and
            started["specification_sha256"] == digest(specification), "Start/specification identity differs")
    require(started["actual_source_files"] == spec["source_files"] and started["compute_policy"] == POLICY and
            started["planned_forward_attempts"] == completed["planned_forward_attempts"] == 56, "Started source/policy differs")
    portable_preflight = verify_portable_preflight(spec, paths, started)
    mandatory = {"forwards.jsonl", "diagnostics.json", "occupancy_checks.json", "run_started.json"}
    allowed = mandatory | {"runtime.json", "implementation_sources.json"}
    artifacts = completed["artifacts"]
    require(mandatory <= set(artifacts) <= allowed, "Completion artifact inventory differs")
    for name in allowed:
        require((run_dir / name).exists() == (name in artifacts), "Unbound/missing completion artifact")
    for name, pin in artifacts.items():
        require(valid_hash(pin) and digest(run_dir / name) == pin, f"Completion artifact hash differs: {name}")
    if "implementation_sources.json" in artifacts:
        implementation = read(run_dir / "implementation_sources.json")
        require(implementation["separate_from_historical_core_runtime"] is True and
                set(implementation["files"]) == {"modeling_llama", "masking_utils"} and all(
                    isinstance(v["path"], str) and v["path"] and valid_hash(v["sha256"])
                    for v in implementation["files"].values()), "Invalid implementation-source receipt")
    records = rows(run_dir / "forwards.jsonl")
    attempts = verify_forwards(cases, records)
    derived, compact = derive(cases, records)
    diagnostics = read(run_dir / "diagnostics.json")
    for key, value in derived.items():
        require(diagnostics[key] == value, f"Runner diagnostics disagree: {key}")
    runtime = read(run_dir / "runtime.json") if "runtime.json" in artifacts else None
    runtime_equal = runtime == spec["historical_runtime"] if runtime is not None else False
    if "runtime" in paths:
        require(read(paths["runtime"]) == spec["historical_runtime"], "Embedded historical runtime differs from source")
    require(completed["full_runtime_identity_matches_historical"] is runtime_equal, "Runtime summary disagrees")
    require(attempts == 0 or runtime_equal, "Forward executed without complete historical runtime identity")
    resources = verify_resources(read(run_dir / "occupancy_checks.json"), records, POLICY)
    require(type(started["pid"]) is int and started["pid"] > 0 and all(
        o["own_pid"] == started["pid"] for o in read(run_dir / "occupancy_checks.json")["observations"]),
        "Resource PID differs from run identity")
    require(completed["forward_attempts"] == attempts and completed["status_counts"] == dict(Counter(r["status"] for r in records)),
            "Completion forward/status denominator differs")
    require(completed["numerical_gate_passed"] is derived["numerical_gate_passed"], "Completion numerical gate differs")
    for key in ("new_scientific_n", "new_stimuli", "tokenizer_calls", "generation_calls", "downloads"):
        require(type(completed[key]) is int and completed[key] == 0, f"Run ceiling differs: {key}")
    require(completed["block_H_recomputed"] is False, "Unexpected block-H recomputation")
    require(finite(completed["elapsed_seconds"]) and completed["elapsed_seconds"] >= 0, "Invalid elapsed time")
    peak = completed["peak_torch_memory_mib"]
    if peak is not None:
        require(all(finite(peak[k]) and 0 <= peak[k] <= POLICY["allocator_cap_mib"] for k in ("allocated_mib", "reserved_mib")),
                "Allocator memory cap exceeded")
    stopped = completed["stop_reason"] is not None
    expected_status = ("stopped_partial" if stopped else "completed_numerical_gate_passed" if derived["numerical_gate_passed"]
                       else "completed_numerical_gate_failed")
    require(completed["status"] == expected_status, "Completion status disagrees")
    require(stopped or all(r["status"] == "completed" and not r.get("boundary_error_after_score") for r in records),
            "Unreported partial/stop boundary")
    require(stopped or resources["all_observations_allowed"], "Unreported resource refusal")
    if not stopped:
        require(completed["elapsed_seconds"] < POLICY["walltime_seconds"], "Completed run exceeded walltime cap")
    bounded_pass = (derived["numerical_gate_passed"] and runtime_equal and not stopped and
                    resources["all_observations_allowed"] and resources["per_forward_allowed_before_and_after"] is True)
    result = {"protocol_id": PROTOCOL + "-independent-validation", "schema_version": 1,
        "status": "verified_bounded_numerical_gate" if bounded_pass else "verified_partial_or_numerical_gate_not_passed",
        "receipt_integrity_verified": True, "bounded_numerical_gate_passed": bounded_pass,
        "numerical_gate_passed": derived["numerical_gate_passed"], "all_56_scores_completed": derived["all_56_scores_completed"],
        "all_scored_boundaries_admissible": derived["all_scored_boundaries_admissible"],
        "planned_inputs": 8, "planned_forward_attempts": 56, "actual_forward_attempts": attempts,
        "completed_forward_scores": sum(r["status"] == "completed" for r in records),
        "status_counts": dict(Counter(r["status"] for r in records)), "stop_reason": completed["stop_reason"],
        "full_runtime_identity_matches_historical": runtime_equal if runtime is not None else None,
        "resource_validation": resources, "peak_torch_memory_mib": peak, "input_summary": compact,
        "measurement_preflight_validation": portable_preflight,
        "new_scientific_n": 0, "block_H_recomputed": False, "scientific_population_verdict": None,
        "claim_ceiling": "Eight selected engineering inputs; no corrected scientific scores, population estimate, or causal attribution.",
        "limitations": ["Logit bytes were not saved: equality is attested by hashes, shapes and selected log probabilities.",
            "Resource observations do not establish absence of activity between checks or peer-workload throughput impact.",
            "Unknown missing/runtime/resource gates do not count as numerical validation success."],
        "provenance": {"checker_path": str(Path(__file__).resolve()), "checker_sha256": digest(Path(__file__)),
            "specification": {"path": str(specification), "sha256": digest(specification)},
            "run_completed": {"path": str(run_dir / "run_completed.json"), "sha256": digest(run_dir / "run_completed.json")},
            "artifact_sha256": artifacts, "source_files": spec["source_files"],
            "checker_model_forwards": 0, "checker_tokenizer_calls": 0, "checker_network_calls": 0}}
    return result


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
    args = parser.parse_args()
    require(not safe(args.output).exists(), "Refusing to overwrite validation output")
    result = analyze(args.specification, args.run_dir)
    write_output(args.output, result)
    print(json.dumps({k: result[k] for k in ("status", "actual_forward_attempts", "completed_forward_scores",
                                           "bounded_numerical_gate_passed", "new_scientific_n")}, sort_keys=True))


if __name__ == "__main__":
    main()
