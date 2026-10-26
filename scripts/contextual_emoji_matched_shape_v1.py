#!/usr/bin/env python3
"""Bounded matched-shape reacquisition of 1,248 existing development scores.

Prepare is stdlib-only. Run is a separate offline BF16 action with 64 sentinel
forwards, no new stimuli or tokenization, strict occupancy and exact replay gates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-matched-shape-v1"
PREFIX_PATH = "scripts/contextual_emoji_prefix_consistency_v0.py"
PREFIX_SHA = "5ee9d2120c51e26db936ef37e0e1d4607aaf606fad41fb4970fc20210b985d65"
PRIOR = "validation/contextual_emoji_prefix_consistency_v0/portable_preflight"
PRIOR_PINS = {
    "prefix_specification": ("specification.json", "751a81c07b518adf2359ffa4f65235c2ca5b41a3f8c75fee0450477e5419e8de"),
    "prefix_prior_independent": ("independent_validation.json", "4592c2d6af4ded9af5cbeff98363e958cdb90f2ed81a2e4a795b4768fbaf338b"),
    "prefix_prior_forwards": ("run56/forwards.jsonl", "09a8a4ca0296677017376299b85edf65ce1e1d1f405b5a69cc5213e4f769b4e0"),
    "prefix_prior_runtime": ("run56/runtime.json", "952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323"),
    "prefix_prior_implementation": ("run56/implementation_sources.json", "c84131b308d4b82a23ff0aaf85b25dd61c18b9ad02696f8b206ead8a45ef382a"),
    "prefix_prior_completed": ("run56/run_completed.json", "9438ba6c52ee517007090cb23272ca47cba931578fda628963db271346980c06"),
    "prefix_prior_started": ("run56/run_started.json", "e3d71453d7b022e09301881e77b248fdd7d2cbe74c05a03b10090ee3caaeccea"),
    "prefix_prior_diagnostics": ("run56/diagnostics.json", "81798d317c4650812e625559ccc57ec6f730639e37d045ead58a81381de41a4f"),
    "prefix_prior_occupancy": ("run56/occupancy_checks.json", "37951a2fed80175ce6ae40b453962dc810415e79a9d01c2ed62d128a16e7ef3b"),
}

if hashlib.sha256((ROOT / PREFIX_PATH).read_bytes()).hexdigest() != PREFIX_SHA:
    raise ValueError("Pinned prefix implementation changed")
_module_spec = importlib.util.spec_from_file_location("glyphprobe_matched_shape_prefix", ROOT / PREFIX_PATH)
prefix = importlib.util.module_from_spec(_module_spec)
_module_spec.loader.exec_module(prefix)
require, safe, digest, read, write, rows, now = (prefix.require, prefix.safe, prefix.digest,
    prefix.read, prefix.write, prefix.rows, prefix.now)
POLICY = {**prefix.POLICY, "walltime_seconds": 900, "maximum_forward_attempts": 1312}
SENTINEL_METHODS = ("original_a_1", "original_b_1", "padded_a", "padded_b")
SCORE_FIELDS = ("candidate_token_logprobs", "sequence_logprob_sum",
    "shared_prediction_logits_sha256", "shared_prediction_logits_shape",
    "shared_prediction_logits_dtype", "logits_hash_byte_order", "normalization_rectangle_shape")


def inventory(emoji, word, additional):
    """Keep every historical scientific row; absent rows have one shared identity."""
    indexed = {}
    for origin, values in (("emoji_cells", emoji), ("word_cells", word), ("cells.jsonl", additional)):
        for row in values:
            prefix.validate_record(row)
            if origin == "emoji_cells":
                pair, carrier = "original", "shared_absent" if row["variant"] == "absent" else "emoji"
            elif origin == "word_cells":
                pair, carrier = "original", "word"
            else:
                pair, carrier = row["pair_id"], row["carrier_kind"]
            require(pair in ("original", "explicit_negation", "adjective_pair") and
                carrier in ("emoji", "word", "shared_absent") and row["candidate"] in ("a", "b") and
                row["context"] in ("p", "q") and row["variant"] in ("a", "b", "absent"), "Invalid historical identity")
            require((carrier == "shared_absent") == (row["variant"] == "absent") and
                (carrier != "shared_absent" or origin == "emoji_cells"), "Unexpected or duplicated absent cohort")
            key = (pair, carrier, row["block_id"], row["context"], row["variant"], row["candidate"])
            require(key not in indexed, "Duplicate historical source identity")
            require(type(row["eta"]) is int and row["eta"] in (-1, 1) and isinstance(row["family"], str),
                "Missing or invalid authored direction/family")
            indexed[key] = (origin, row)
    require(len(indexed) == 1248, "Exactly 1248 historical sequence scores required")
    blocks = {key[2] for key in indexed}
    require(len(blocks) == 24 and len({row["family"] for _, row in indexed.values()}) == 6,
        "Historical 24-block/six-family coverage differs")
    expected = {(pair, carrier, block, context, cue, candidate)
        for pair in ("original", "explicit_negation", "adjective_pair") for carrier in ("emoji", "word")
        for block in blocks for context in ("p", "q") for cue in ("a", "b") for candidate in ("a", "b")}
    expected |= {("original", "shared_absent", block, context, "absent", candidate)
        for block in blocks for context in ("p", "q") for candidate in ("a", "b")}
    require(set(indexed) == expected, "Missing/extra historical scientific cell")
    cases = []
    for key in sorted({key[:-1] for key in indexed}):
        a, b = [indexed[(*key, candidate)][1] for candidate in ("a", "b")]
        require(a["prompt_token_ids"] == b["prompt_token_ids"] and a["prompt"] == b["prompt"], "Paired prompts differ")
        require(a["eta"] == b["eta"] and a["family"] == b["family"], "Paired direction/family differs")
        n = 0
        for x, y in zip(a["candidate_token_ids"], b["candidate_token_ids"]):
            if x != y:
                break
            n += 1
        require(n > 0, "Every paired input requires a shared candidate prefix")
        cases.append({"input_id": "/".join(key), "identity": list(key),
            "shared_prefix_token_count": n, "shared_prefix_token_ids": a["candidate_token_ids"][:n],
            "candidates": {"a": a, "b": b},
            "historical_sources": {c: {"source_file_key": indexed[(*key, c)][0],
                "source_cell_id": indexed[(*key, c)][1]["cell_id"],
                "unique_source_key": [indexed[(*key, c)][0], indexed[(*key, c)][1]["cell_id"]]}
                for c in ("a", "b")}})
    require(len(cases) == 624, "Exactly 624 paired inputs required")
    require(len({tuple(v["unique_source_key"]) for c in cases for v in c["historical_sources"].values()}) == 1248,
        "Historical source key collision")
    return cases


def design(root):
    root = safe(root)
    prior_entries = {key: {"path": f"{PRIOR}/{relative}", "sha256": pin}
        for key, (relative, pin) in PRIOR_PINS.items()}
    paths = {key: prefix.bound_file(root, entry) for key, entry in prior_entries.items()}
    old = prefix.verify_specification(paths["prefix_specification"], root)
    completed = read(paths["prefix_prior_completed"])
    validation = read(paths["prefix_prior_independent"])
    require(completed["status"] == "completed_numerical_gate_passed" and completed["forward_attempts"] == 56 and
        validation["receipt_integrity_verified"] and validation["bounded_numerical_gate_passed"],
        "Prior eight-input diagnostic was not independently validated")
    prior_rows = rows(paths["prefix_prior_forwards"])
    require(len(prior_rows) == 56 and all(row["status"] == "completed" for row in prior_rows), "Prior diagnostic incomplete")
    prior_index = {(r["input_id"], r["method"]): r for r in prior_rows}
    require(len(prior_index) == 56, "Prior diagnostic duplicated")
    sources = {**old["source_files"], **prior_entries}
    sources["prefix_runner"] = sources.pop("runner")
    sources["runner"] = {"path": "scripts/contextual_emoji_matched_shape_v1.py", "sha256": digest(Path(__file__))}
    for entry in sources.values():
        prefix.bound_file(root, entry)
    cases = inventory(*(rows(root / sources[name]["path"]) for name in ("emoji_cells", "word_cells", "cells.jsonl")))
    indexed_cases = {c["input_id"]: c for c in cases}
    sentinels = []
    for case in old["inputs"]:
        require(case["candidates"] == indexed_cases[case["input_id"]]["candidates"], "Sentinel historical rows differ")
        expected = {method: prior_index[case["input_id"], method] for method in SENTINEL_METHODS}
        for method, row in expected.items():
            require(row["geometry"] == prefix.call_geometry(case, method), "Prior sentinel geometry differs")
            prefix.validate_score(row, row)
            if method.startswith("original"):
                require(prefix.original_matches(case, row, row), "Prior original parity differs")
        sentinels.append({**case, "expected_scores": expected})
    result = {"protocol_id": PROTOCOL, "schema_version": 1,
        "status": "prepared_rescoring_existing_development_not_new_scientific_n",
        "claim_ceiling": "matched_shape_reassessment_of_existing_24_authored_development_scenarios_only",
        "source_files": sources, "portable_measurement_reference": old["portable_measurement_reference"],
        "compute_policy": POLICY, "planned_forward_attempts": 1312,
        "planned_scientific_sequence_scores": 1248, "planned_scientific_inputs": 624,
        "planned_sentinel_forwards": 64, "new_scientific_n": 0, "new_stimuli": 0,
        "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0, "prepare_model_forwards": 0,
        "scientific_inventory": {"original_emoji_crossed": 192, "original_word_crossed": 192,
            "shared_original_absent": 96, "explicit_negation_crossed": 384, "adjective_pair_crossed": 384},
        "model_path": old["model_path"], "model_artifact": old["model_artifact"],
        "runtime_packages": old["runtime_packages"], "python_version": old["python_version"],
        "historical_runtime": old["historical_runtime"],
        "expected_implementation_sources": read(paths["prefix_prior_implementation"]),
        "scoring": {**old["scoring"], "prefix_only": "not run", "primary_estimator": "full_candidate_sequence_logprob_sum",
            "sentinel_tolerance": 0, "end_to_begin_tolerance": 0,
            "scientific_sentinel_repeat_tolerance": 0,
            "scientific_prefix_failure_policy": "finish_bounded_inventory_and_fail_acceptance_gate",
            "sentinel_resource_runtime_failure_policy": "stop_and_preserve_planned_missingness"},
        "inputs": cases, "sentinels": sentinels}
    require(len(plans(result)) == 1312, "Forward schedule differs")
    return result


def prepare(root, output):
    root, output = safe(root), safe(output)
    require(not output.exists(), "Refusing to overwrite specification")
    require(output.is_relative_to(root), "Specification must be inside repository")
    spec = {"created_at_utc": now(), **design(root)}
    write(output, spec)
    return spec


def verify_specification(path, root=ROOT):
    spec = read(path)
    require(isinstance(spec.get("created_at_utc"), str), "Missing preparation timestamp")
    require({k: v for k, v in spec.items() if k != "created_at_utc"} == design(root),
        "Specification changed after preparation")
    return spec


def plans(spec):
    events = []
    for phase, cases, methods in (("begin", spec["sentinels"], SENTINEL_METHODS),
            ("scientific", spec["inputs"], ("padded_a", "padded_b")),
            ("end", spec["sentinels"], SENTINEL_METHODS)):
        for case in cases:
            for method in methods:
                events.append({"event_id": f"{phase}::{case['input_id']}::{method}",
                    "phase": phase, "input_id": case["input_id"], "method": method,
                    "geometry": prefix.call_geometry(case, method)})
    require(len(events) == 1312 and len({r["event_id"] for r in events}) == 1312, "Exactly 1312 unique planned forwards required")
    return events


def exact_score(left, right):
    return all(left.get(field) == right.get(field) and field in left and field in right for field in SCORE_FIELDS)


def validate_score(score, event):
    prefix.validate_score(score, event)
    geometry = event["geometry"]
    require(score["shared_prediction_logits_shape"] == [geometry["shared_prefix_token_count"], 128256] and
        score["normalization_rectangle_shape"] == [geometry["normalization_stop"] - geometry["normalization_start"], 128256],
        "Invalid model-vocabulary score geometry")
    require(score["logits_hash_byte_order"] in ("little", "big") and
        all(c in "0123456789abcdef" for c in score["shared_prediction_logits_sha256"]), "Invalid predictor hash encoding")


def execute(spec, scorer, before, after, emit, deadline, initial_error=None):
    """Every attempted call has an after guard, including a failed scorer."""
    cases = {c["input_id"]: c for c in spec["inputs"]}
    sentinels = {c["input_id"]: c for c in spec["sentinels"]}
    records, attempts, blocked, beginnings = [], 0, initial_error, {}
    for event in plans(spec):
        row = {**event, "status": "not_run", "forward_attempted": False}
        if blocked is not None:
            row["reason"] = blocked
        else:
            try:
                deadline()
                before(event)
                require(attempts < 1312, "Forward-attempt cap reached")
                attempts += 1
                row["forward_attempted"] = True
                try:
                    score = scorer(cases[event["input_id"]], event)
                    validate_score(score, event)
                    row.update(score, status="completed")
                    if event["phase"] == "scientific" and event["input_id"] in sentinels:
                        case = sentinels[event["input_id"]]
                        row["scientific_sentinel_exact_parity"] = exact_score(score, case["expected_scores"][event["method"]])
                        require(row["scientific_sentinel_exact_parity"], "Scientific sentinel exact replay parity failed")
                    if event["phase"] != "scientific":
                        case = sentinels[event["input_id"]]
                        row["sentinel_exact_parity"] = exact_score(score, case["expected_scores"][event["method"]])
                        if event["method"].startswith("original"):
                            row["historical_exact_parity"] = prefix.original_matches(case, event, score)
                            require(row["historical_exact_parity"], "Original sentinel historical parity failed")
                        require(row["sentinel_exact_parity"], "Sentinel exact prior-score/logit parity failed")
                        key = event["input_id"], event["method"]
                        if event["phase"] == "begin":
                            beginnings[key] = row
                        else:
                            row["end_begin_exact_parity"] = exact_score(row, beginnings[key])
                            require(row["end_begin_exact_parity"], "End/begin exact sentinel parity failed")
                finally:
                    after(event)
                deadline()
            except BaseException as exc:
                blocked = f"{type(exc).__name__}: {exc}"
                if row["status"] == "completed":
                    row["boundary_error_after_score"] = blocked
                else:
                    row["status"] = "failed" if row["forward_attempted"] else "not_run"
                    row["reason"] = blocked
        row["recorded_at_utc"] = now()
        records.append(row)
        emit(row)
    return records, attempts, blocked


def evaluate(spec, records):
    planned = plans(spec)
    require(len(records) == 1312, "Planned forward denominator changed")
    for expected, row in zip(planned, records):
        require(all(row.get(k) == v for k, v in expected.items()), "Forward identity/order/geometry differs")
        require(row["status"] in ("completed", "failed", "not_run") and type(row["forward_attempted"]) is bool and
            row["forward_attempted"] == (row["status"] != "not_run"), "Invalid forward status/attempt")
        if row["status"] == "completed":
            validate_score(row, expected)
        else:
            require("candidate_token_logprobs" not in row and "sequence_logprob_sum" not in row, "Uncompleted row has scores")
    indexed = {r["event_id"]: r for r in records}
    comparisons = []
    for case in spec["inputs"]:
        pair = [indexed[f"scientific::{case['input_id']}::padded_{c}"] for c in ("a", "b")]
        result = {"input_id": case["input_id"], "prefix_logprobs_exact_equal": None,
            "shared_predictor_logits_exact_equal": None, "s_matched_shape": None, "s_historical": None}
        if all(row["status"] == "completed" for row in pair):
            a, b = pair
            n = case["shared_prefix_token_count"]
            result.update(prefix_logprobs_exact_equal=a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n],
                shared_predictor_logits_exact_equal=all(a[k] == b[k] for k in
                    ("shared_prediction_logits_sha256", "shared_prediction_logits_shape", "shared_prediction_logits_dtype", "logits_hash_byte_order")),
                s_matched_shape=a["sequence_logprob_sum"] - b["sequence_logprob_sum"],
                s_historical=case["candidates"]["a"]["sequence_logprob_sum"] - case["candidates"]["b"]["sequence_logprob_sum"])
        comparisons.append(result)
    sentinel_checks = []
    scientific_sentinel_checks = []
    for case in spec["sentinels"]:
        for method in SENTINEL_METHODS:
            begin, end = [indexed[f"{phase}::{case['input_id']}::{method}"] for phase in ("begin", "end")]
            complete = begin["status"] == end["status"] == "completed"
            sentinel_checks.append({"input_id": case["input_id"], "method": method,
                "begin_exact_prior": exact_score(begin, case["expected_scores"][method]) if begin["status"] == "completed" else None,
                "end_exact_prior": exact_score(end, case["expected_scores"][method]) if end["status"] == "completed" else None,
                "end_exact_begin": exact_score(begin, end) if complete else None})
            if method.startswith("padded"):
                scientific = indexed[f"scientific::{case['input_id']}::{method}"]
                scientific_sentinel_checks.append({"input_id": case["input_id"], "method": method,
                    "scientific_exact_prior": exact_score(scientific, case["expected_scores"][method])
                        if scientific["status"] == "completed" else None})
    completed = sum(r["status"] == "completed" for r in records)
    scientific_completed = sum(r["status"] == "completed" and r["phase"] == "scientific" for r in records)
    prefixes = sum(r["prefix_logprobs_exact_equal"] is True and r["shared_predictor_logits_exact_equal"] is True for r in comparisons)
    boundary = not any("boundary_error_after_score" in r for r in records)
    sentinel_pass = all(r[key] is True for r in sentinel_checks for key in ("begin_exact_prior", "end_exact_prior", "end_exact_begin"))
    scientific_sentinel_pass = all(r["scientific_exact_prior"] is True for r in scientific_sentinel_checks)
    return {"planned_forward_attempts": 1312, "completed_forward_scores": completed,
        "planned_scientific_sequence_scores": 1248, "completed_scientific_scores": scientific_completed,
        "planned_scientific_inputs": 624, "completed_scientific_inputs": sum(r["s_matched_shape"] is not None for r in comparisons),
        "matching_scientific_prefixes": prefixes, "all1312_scores_completed": completed == 1312,
        "all624_prefixes_exact": prefixes == 624, "sentinel_exact_parity": sentinel_pass,
        "all_sentinel_scientific_repeats_exact": scientific_sentinel_pass,
        "all_scored_boundaries_admissible": boundary,
        "numerical_gate_passed": completed == 1312 and prefixes == 624 and sentinel_pass and scientific_sentinel_pass and boundary,
        "input_comparisons": comparisons, "sentinel_comparisons": sentinel_checks,
        "scientific_sentinel_comparisons": scientific_sentinel_checks,
        "new_scientific_n": 0, "claim_ceiling": "scoring-consistency gate; scientific interpretation requires independent analysis"}


def run(spec_path, output):
    output = safe(output)
    require(not output.exists(), "Refusing to reuse a run directory")
    spec = verify_specification(spec_path)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    _, _, _, native = prefix.load_measurement_replay(ROOT)
    write(output / "run_started.json", {"started_at_utc": now(), "pid": os.getpid(), "protocol_id": PROTOCOL,
        "specification_sha256": digest(spec_path), "actual_source_files": spec["source_files"],
        "planned_forward_attempts": 1312, "compute_policy": POLICY, "measurement_native_replay_portability": native})
    observations = []
    def deadline():
        require(time.monotonic() - started < 900, "900-second walltime budget exhausted")
    def observe(before_load=False, event=None, boundary=None):
        def record(observation):
            observations.append({**observation, "event_id": event["event_id"] if event else None,
                "boundary": boundary or ("preload" if before_load else "after_allocation")})
        return prefix.resource_guard(before_load=before_load, emit=record)
    def runtime_emit(runtime):
        write(output / "runtime.json", runtime)
    def implementation_emit(value):
        write(output / "implementation_sources.json", value)
        require(value == spec["expected_implementation_sources"], "Model/masking implementation differs from passed diagnostic")
    def alarm(signum, frame):
        raise TimeoutError("900-second process walltime alarm")
    old_alarm = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 900)
    resources, torch, model, base = {}, None, None, None
    error, records, attempts = None, [], 0
    try:
        try:
            observe(True)
            torch, model, base = prefix.load_model(spec, observe, runtime_emit, implementation_emit, deadline, resources)
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        with (output / "forwards.jsonl").open("x", encoding="utf-8") as handle:
            def emit(row):
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            records, attempts, error = execute(spec,
                lambda case, event: prefix.score_call(torch, model, base, case, event),
                lambda event: observe(False, event, "before"), lambda event: observe(False, event, "after"),
                emit, deadline, error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_alarm)
        peak = None
        torch = resources.get("torch", torch)
        if torch is not None and torch.cuda.is_initialized():
            peak = {"allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                "reserved_mib": torch.cuda.max_memory_reserved() / 2**20}
            model = None
            resources.pop("model", None)
            gc.collect()
            torch.cuda.empty_cache()
        write(output / "occupancy_checks.json", {"observations": observations,
            "maximum_observed_own_process_mib": max((o.get("own_process_mib", 0) for o in observations), default=0)})
    diagnostics = evaluate(spec, records)
    write(output / "diagnostics.json", diagnostics)
    summary = {"protocol_id": PROTOCOL, "finished_at_utc": now(),
        "status": "completed_numerical_gate_passed" if diagnostics["numerical_gate_passed"] and error is None else
            "stopped_partial" if error is not None else "completed_numerical_gate_failed",
        "forward_attempts": attempts, "planned_forward_attempts": 1312,
        "planned_scientific_sequence_scores": 1248, "planned_sentinel_forwards": 64,
        "status_counts": dict(Counter(r["status"] for r in records)), "stop_reason": error,
        "elapsed_seconds": time.monotonic() - started, "peak_torch_memory_mib": peak,
        "full_runtime_identity_matches_historical": read(output / "runtime.json") == spec["historical_runtime"]
            if (output / "runtime.json").exists() else False,
        "implementation_sources_match_prior": read(output / "implementation_sources.json") == spec["expected_implementation_sources"]
            if (output / "implementation_sources.json").exists() else False,
        "new_scientific_n": 0, "new_stimuli": 0, "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0,
        "numerical_gate_passed": diagnostics["numerical_gate_passed"],
        "artifacts": {name: digest(output / name) for name in
            ("forwards.jsonl", "diagnostics.json", "occupancy_checks.json", "run_started.json")}}
    for name in ("runtime.json", "implementation_sources.json"):
        if (output / name).exists():
            summary["artifacts"][name] = digest(output / name)
    write(output / "run_completed.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--specification", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        spec = prepare(args.root, args.output)
        result = {"status": spec["status"], "specification_sha256": digest(args.output),
            "planned_forward_attempts": 1312, "planned_scientific_sequence_scores": 1248,
            "model_forwards": 0, "tokenizer_calls": 0}
    else:
        result = run(args.specification, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0 if args.command == "prepare" or result["status"] == "completed_numerical_gate_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
