#!/usr/bin/env python3
"""Model-free wording sensitivity from saved per-token scores; no runner import."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

PROTOCOL = "glyphprobe-contextual-emoji-candidate-wording-v0"
PAIR_IDS = ("original", "explicit_negation", "adjective_pair")
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
PINS = {
    "emoji_spec": "04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5",
    "word_spec": "ba8eabb588d48eca68041f475440e64b3f6e0db1fa6ab4f5aa56ee7083b0c519",
    "emoji_cells": "ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97",
    "word_cells": "1026d3001ad4390662bfec608cfeca28d1610f7ba7117b6401494d8fa929ad91",
    "runtime": "952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323",
}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def safe(path):
    check(path.name not in PROTECTED and path.resolve().name not in PROTECTED, "Protected historical bank")
    return path.resolve()


def digest(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def decode(value):
    def pairs(items):
        result = {}
        for key, item in items:
            check(key not in result, "Duplicate JSON key")
            result[key] = item
        return result
    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(value, object_pairs_hook=pairs, parse_constant=invalid)


def read(path):
    return decode(safe(path).read_text(encoding="utf-8"))


def rows(path):
    lines = safe(path).read_text(encoding="utf-8").splitlines()
    check(all(line.strip() for line in lines), "Blank record")
    return [decode(line) for line in lines]


def total(row):
    if row["status"] != "completed":
        check("sequence_logprob_sum" not in row and "candidate_token_logprobs" not in row, "Unrun row carries scores")
        return None
    values = row["candidate_token_logprobs"]
    check(len(values) == row["candidate_token_count"] and values and
          all(type(x) in (float, int) and math.isfinite(x) and x <= 1e-6 for x in values), "Invalid token scores")
    result = math.fsum(values)
    check(type(row["sequence_logprob_sum"]) in (int, float) and math.isfinite(row["sequence_logprob_sum"])
          and abs(result - row["sequence_logprob_sum"]) <= 1e-10, "Token sum mismatch")
    return result


def expected_text(block, panel, pair_id, candidate):
    if pair_id == "original":
        return block[f"candidate_{candidate}"]
    pair = next(p for p in panel["additional_pairs"] if p["pair_id"] == pair_id)
    positive_is_a = block["eta"] == 1
    return pair["positive" if ((candidate == "a") == positive_is_a) else "negative"]


def calculate(blocks, panel, new_rows, emoji_rows, word_rows):
    check(len(blocks) == 24 and len({b["block_id"] for b in blocks}) == 24, "24 distinct blocks required")
    families = Counter(b["family"] for b in blocks)
    check(len(families) == 6 and set(families.values()) == {4}, "Six complete families required")
    lookup = {b["block_id"]: b for b in blocks}
    check(len(new_rows) == 768 and len(emoji_rows) == 288 and len(word_rows) == 192, "Recorded denominators changed")
    check([p["pair_id"] for p in panel["additional_pairs"]] == list(PAIR_IDS[1:]), "Fixed pairs required")
    scores = {}
    geometry = []
    for carrier, originals in (("emoji", emoji_rows), ("word", word_rows)):
        selected = [r for r in originals if r["variant"] in ("a", "b")]
        check(len(selected) == 192, "Historical crossed denominator changed")
        current = [r for r in new_rows if r["carrier_kind"] == carrier]
        for row, pair_id in [(r, "original") for r in selected] + [(r, r["pair_id"]) for r in current]:
            check(pair_id in PAIR_IDS and row["status"] in ("completed", "failed", "not_run", "failed_preflight"), "Unknown condition/state")
            b = lookup[row["block_id"]]
            context, variant, candidate = row["context"], row["variant"], row["candidate"]
            check(context in ("p", "q") and variant in ("a", "b") and candidate in ("a", "b"), "Invalid crossed cell")
            key = pair_id, carrier, b["block_id"], context, variant, candidate
            check(key not in scores, "Duplicate score identity")
            cue = b[f"emoji_{variant}"] if carrier == "emoji" else b["planned_word_alternatives"][variant]
            check(row["prompt"] == b[f"context_{context}"].replace("{emoji}", cue) and
                  row["continuation"] == expected_text(b, panel, pair_id, candidate) and row["eta"] == b["eta"],
                  "Stimulus/candidate/orientation changed")
            scores[key] = total(row)
            if pair_id != "original":
                check(row["cell_id"] == ":".join(key), "New ID differs from condition")
                geometry.append({k: row.get(k) for k in ("cell_id", "pair_id", "carrier_kind", "block_id", "context", "variant",
                    "candidate", "prompt_token_count", "candidate_token_count", "candidate_token_ids", "carrier_token_positions",
                    "first_candidate_predictor_position", "status")})
    check(len(scores) == 1152, "Combined crossed score denominator changed")
    reports = []
    for pair_id in PAIR_IDS:
        for carrier in ("emoji", "word"):
            for b in blocks:
                s, labels = {}, {}
                for c in ("p", "q"):
                    s[c], labels[c] = {}, {}
                    for v in ("a", "b"):
                        values = [scores[(pair_id, carrier, b["block_id"], c, v, k)] for k in ("a", "b")]
                        value = None if any(x is None for x in values) else values[0] - values[1]
                        s[c][v] = value
                        sign = b["eta"] * (1 if (c, v) in (("p", "a"), ("q", "b")) else -1)
                        check(b["orientation"][f"context_{c}"][f"emoji_{v}"] == ("a" if sign > 0 else "b"), "Orientation inconsistent")
                        labels[c][v] = None if value is None else "tie" if value == 0 else "aligned" if sign * value > 0 else "misaligned"
                complete = all(x is not None for c in s.values() for x in c.values())
                d = {c: s[c]["b"] - s[c]["a"] if all(x is not None for x in s[c].values()) else None for c in s}
                reports.append({"pair_id": pair_id, "carrier": carrier, "block_id": b["block_id"], "family": b["family"],
                    "s": s, "complete": complete, "delta_p": d["p"], "delta_q": d["q"],
                    "H": b["eta"] * (d["q"] - d["p"]) if complete else None,
                    "effect_crossover": b["eta"] * d["p"] < 0 < b["eta"] * d["q"] if complete else None,
                    "author_alignment": labels,
                    "all_four_aligned": all(x == "aligned" for c in labels.values() for x in c.values()) if complete else None})
    per_pair = {}
    for pair_id in PAIR_IDS:
        per_pair[pair_id] = {}
        for carrier in ("emoji", "word"):
            rr = [r for r in reports if r["pair_id"] == pair_id and r["carrier"] == carrier]
            complete = [r for r in rr if r["complete"]]
            family_means = {f: math.fsum(r["H"] for r in rr if r["family"] == f) / 4
                            if all(r["complete"] for r in rr if r["family"] == f) else None for f in families}
            labels = [x for r in rr for c in r["author_alignment"].values() for x in c.values()]
            per_pair[pair_id][carrier] = {"planned_blocks": 24, "completed_blocks": len(complete),
                "full_population_mean_H": math.fsum(family_means.values()) / 6 if len(complete) == 24 else None,
                "family_mean_H": family_means, "positive_H_blocks": sum(r["H"] > 0 for r in complete),
                "effect_crossover_blocks": sum(r["effect_crossover"] for r in complete),
                "planned_inputs": 96, "available_inputs": sum(x is not None for x in labels),
                "aligned_inputs": labels.count("aligned"), "tied_inputs": labels.count("tie"),
                "all_four_aligned_blocks": sum(r["all_four_aligned"] is True for r in rr)}
    indexed = {(r["pair_id"], r["carrier"], r["block_id"]): r for r in reports}
    stability, contrasts = [], []
    for b in blocks:
        for carrier in ("emoji", "word"):
            rr = [indexed[(p, carrier, b["block_id"])] for p in PAIR_IDS]
            hs = [r["H"] for r in rr]
            complete = all(h is not None for h in hs)
            preference = []
            for c in ("p", "q"):
                for v in ("a", "b"):
                    states = [r["author_alignment"][c][v] for r in rr]
                    preference.append({"context": c, "variant": v, "states_by_pair": states,
                                       "varies_across_pairs": len(set(states)) > 1 if None not in states else None})
            stability.append({"block_id": b["block_id"], "carrier": carrier, "H_by_pair": hs, "complete": complete,
                "mean_H": math.fsum(hs) / 3 if complete else None, "range_H": max(hs) - min(hs) if complete else None,
                "H_sign_class": ("all_positive" if min(hs) > 0 else "all_negative" if max(hs) < 0 else "zero_or_mixed") if complete else None,
                "effect_crossover_all_three": all(r["effect_crossover"] for r in rr) if complete else None,
                "absolute_preference_stability": preference})
        differences = [indexed[(p, "word", b["block_id"])]["H"] - indexed[(p, "emoji", b["block_id"])]["H"]
                       if indexed[(p, "word", b["block_id"])]["complete"] and indexed[(p, "emoji", b["block_id"])]["complete"] else None for p in PAIR_IDS]
        complete = None not in differences
        contrasts.append({"block_id": b["block_id"], "family": b["family"], "word_minus_emoji_by_pair": differences,
                          "mean_word_minus_emoji": math.fsum(differences) / 3 if complete else None,
                          "sign_class": ("all_word_greater" if min(differences) > 0 else "all_emoji_greater" if max(differences) < 0 else "zero_or_mixed") if complete else None})
    return {"per_pair": per_pair, "blocks": reports, "stability": stability, "paired_contrasts": contrasts,
        "full_population_equal_pair_mean_H": {c: math.fsum(per_pair[p][c]["full_population_mean_H"] for p in PAIR_IDS) / 3
             if all(per_pair[p][c]["full_population_mean_H"] is not None for p in PAIR_IDS) else None for c in ("emoji", "word")},
        "new_cell_status_counts": dict(Counter(r["status"] for r in new_rows)), "planned_new_cells": 768,
        "reused_crossed_cells": 384, "new_geometry": geometry, "no_geometry_or_outcome_exclusions": True,
        "new_absent_controls": "unavailable_original_candidate_absent_scores_are_not_transferable"}


def analyze(run_dir, spec_path, root):
    spec = read(spec_path)
    check(spec["protocol_id"] == PROTOCOL and spec["status"] == "tokenized_preflight_zero_model_forwards", "Wrong specification")
    check(digest(run_dir / "specification.json") == digest(spec_path), "Run specification changed")
    start, finish = read(run_dir / "run_started.json"), read(run_dir / "run_completed.json")
    check(start["specification_sha256"] == start["local_specification_sha256"] == digest(spec_path), "Preparation hash mismatch")
    for k, value in start.items():
        if k != "status":
            check(finish[k] == value, "Initial receipt changed")
    check(start["planned_cells"] == 768 and start["reused_crossed_cells"] == 384 and start["confirmatory"] is False
          and start["generation_calls"] == 0 and start["intervention_executed"] is False, "Run scope changed")
    check(digest(run_dir / "cells.jsonl") == finish["cells_sha256"], "New raw cells hash mismatch")
    new = rows(run_dir / "cells.jsonl")
    check(len(spec["cells"]) == len(new) == 768, "Missing planned cells")
    for before, after in zip(spec["cells"], new, strict=True):
        check(all(after.get(k) == v for k, v in before.items() if k != "status"), "Planned cell fields changed")
        check((after["status"] == "failed_preflight") == (before["status"] == "failed_preflight"), "Preflight state rewritten")
        if before["status"] == "ready":
            check(before["input_token_ids"] == before["prompt_token_ids"] + before["candidate_token_ids"]
                  and len(before["input_token_ids"]) <= 96 and before["candidate_token_count"] == len(before["candidate_token_ids"]),
                  "Planned token boundary/budget changed")
    count = Counter(r["status"] for r in new)
    check(dict(count) == finish["cell_status_counts"] and finish["recorded_cells"] == 768, "Denominator mismatch")
    attempts = finish["progress"]["forward_calls_attempted"]
    check(count["completed"] <= attempts <= count["completed"] + count["failed"] <= 768, "Forward budget mismatch")
    check(finish["status"] == ("completed" if count["completed"] == 768 else "partial_or_failed"), "Completion mismatch")
    check(digest(run_dir / "occupancy_checks.json") == finish["occupancy_checks_sha256"], "Occupancy hash mismatch")
    policy = spec["config"]["compute_policy"]
    check(policy["mode"] == "staged_shared_cuda" and policy["allocator_cap_mib"] == 2560 and
          policy["driver_allowance_mib"] == 512 and policy["minimum_free_mib"] == 4096 and
          policy["parity_original_crossed_cells"] == 384 and policy["parity_tolerance"] == 0, "Compute policy changed")
    occupancy = read(run_dir / "occupancy_checks.json")
    check(occupancy["policy"] == policy, "Occupancy policy mismatch")
    for r in occupancy["successful_checks"]:
        check(set(r["observed_peer_pids"]) <= set(policy["allowed_peer_pids"]) and
              r["free_mib"] >= r["minimum_free_mib_applied"] >= 4096 and r["own_process_mib"] <= 3072,
              "Resource guard violated")
    reference = {}
    for name, pin in PINS.items():
        entry = spec["config"]["references"][name]
        path = root / entry["path"]
        check(entry["sha256"] == spec["source_files"][name]["sha256"] == digest(path) == pin, "Historical reference changed")
        reference[name] = path
    old_spec = read(reference["emoji_spec"])
    check(spec["blocks"] == old_spec["blocks"] == read(reference["word_spec"])["blocks"], "Original blocks changed")
    panel_path = root / spec["config"]["candidate_panel"]["path"]
    check(digest(panel_path) == spec["config"]["candidate_panel"]["sha256"] ==
          "480d236a87e40e20a4ea339e0514c2a06a0707ec248413ca0260e56868a52730" and
          read(panel_path) == spec["candidate_panel"], "Candidate panel changed")
    check(spec["model_artifact"] == old_spec["model_artifact"], "Model artifact identity changed")
    check(digest(run_dir / "placement.json") == finish["placement_sha256"], "Placement receipt hash mismatch")
    placement = read(run_dir / "placement.json")
    check(placement["policy"] == policy and placement["arithmetic_device"] == "cuda" and
          placement["quantization"] is False and placement["placement_changed_from_historical"] is True,
          "Placement policy changed")
    check(digest(run_dir / "parity.jsonl") == finish["parity_sha256"], "Parity raw hash mismatch")
    parity = rows(run_dir / "parity.jsonl")
    parity_count = Counter(r["status"] for r in parity)
    check(len(parity) == 384 and dict(parity_count) == finish["parity_status_counts"], "Parity denominator changed")
    original_rows = {c: rows(reference[f"{c}_cells"]) for c in ("emoji", "word")}
    original_index = {(c, r["cell_id"]): r for c, rr in original_rows.items() for r in rr if r["variant"] in ("a", "b")}
    seen = set()
    for r in parity:
        check(r["status"] in ("completed", "failed", "not_run"), "Invalid parity status")
        key = r["carrier_kind"], r["baseline_cell_id"]
        check(key not in seen and key in original_index, "Duplicate/unexpected parity row")
        seen.add(key)
        source = original_index[key]
        check(all(r[k] == source[k] for k in ("prompt", "continuation", "input_token_ids", "candidate_token_ids", "prompt_token_ids")) and
              r["reference_logprobs"] == source["candidate_token_logprobs"] and r["reference_sum"] == source["sequence_logprob_sum"],
              "Parity reference changed")
        total(r)
        if r["status"] == "completed":
            check(r["exact_match"] is True and r["candidate_token_logprobs"] == r["reference_logprobs"]
                  and r["sequence_logprob_sum"] == r["reference_sum"], "Parity mismatch admitted")
    parity_pass = parity_count["completed"] == 384
    check(finish["parity_passed"] == parity_pass and (not count["completed"] or parity_pass), "New data admitted before parity")
    parity_attempts = finish["parity_progress"]["forward_calls_attempted"]
    check(parity_count["completed"] <= parity_attempts <= parity_count["completed"] + parity_count["failed"] <= 384,
          "Parity forward budget mismatch")
    check(finish["total_model_forward_attempts"] == attempts + parity_attempts <= 1152, "Combined forward budget mismatch")
    runtime_match = finish["runtime_sha256"] == PINS["runtime"]
    if count["completed"] or parity_count["completed"]:
        check(runtime_match and digest(run_dir / "runtime.json") == PINS["runtime"], "Runtime parity failure")
    report = calculate(spec["blocks"], spec["candidate_panel"], new, original_rows["emoji"], original_rows["word"])
    return {"protocol_id": PROTOCOL, "status": "saved_wording_arithmetic_recomputed", "model_forwards": 0,
        "model_loaded": False, "tokenizer_loaded": False, "confirmatory": False, "human_validation": "absent",
        "semantic_claim_supported": False, "causal_claim_supported": False,
        "core_runtime_parity": runtime_match, "historical_384_cell_exact_parity": parity_pass,
        "placement_changed_from_historical": True, "new_probability_reexecution_verified": False,
        "parity_status_counts": dict(parity_count), "total_model_forward_attempts": finish["total_model_forward_attempts"],
        "source_model_files_reopened": False, "new_absent_forwards": 0,
        "specification_sha256": digest(spec_path), "cells_sha256": finish["cells_sha256"],
        "analyzer_sha256": digest(Path(__file__)), **report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = analyze(args.run_dir, args.specification, args.root)
        destination = safe(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n")
        print(json.dumps({"status": report["status"], "new_cell_status_counts": report["new_cell_status_counts"]}))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({"status": "analysis_failed", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
