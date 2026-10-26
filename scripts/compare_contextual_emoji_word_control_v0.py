#!/usr/bin/env python3
"""Independently audit and compare saved word-control and emoji token scores.

Standard library only: no acquisition runner, tokenizer, model, or score
execution is imported. Source/model identities remain receipt assertions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

EMOJI_PROTOCOL = "glyphprobe-contextual-emoji-output-pilot-v0"
WORD_PROTOCOL = "glyphprobe-contextual-emoji-word-control-v0"
CLAIM = "author_defined_development_labels_only_not_semantic_or_confirmatory"
EMOJI_SPEC_SHA = "04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5"
EMOJI_CELLS_SHA = "ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97"
MODEL_SHA = "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
BASELINE_RUNNER_SHA = "ccce1d18b701708506b61fa20cc1724fed3dd4c44ebfcecde66b20c635944daa"
BASELINE_RUNTIME_SHA = "952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323"
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
CONTEXTS = ("p", "q")
ALTERNATIVES = ("a", "b")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe(path: Path) -> Path:
    check(path.name not in PROTECTED and path.resolve().name not in PROTECTED,
          "Protected target path prohibited")
    return path.resolve()


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def decode(text: str) -> Any:
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            check(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(text, object_pairs_hook=object_pairs, parse_constant=invalid)


def read_object(path: Path) -> dict:
    result = decode(safe(path).read_text(encoding="utf-8"))
    check(isinstance(result, dict), "Expected JSON object")
    return result


def finite(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def close(left, right, label) -> None:
    check(finite(left) and finite(right) and abs(left - right) <= 1e-10,
          f"Numerical mismatch: {label}")


def compare_values(expected, actual, label="summary") -> None:
    """Compare the requested independently derived subset, allowing metadata."""
    if isinstance(expected, dict):
        check(isinstance(actual, dict), f"Expected mapping: {label}")
        for key, value in expected.items():
            check(key in actual, f"Missing comparison field: {label}.{key}")
            compare_values(value, actual[key], f"{label}.{key}")
    elif isinstance(expected, list):
        check(isinstance(actual, list) and len(expected) == len(actual), f"List mismatch: {label}")
        for index, (a, b) in enumerate(zip(expected, actual, strict=True)):
            compare_values(a, b, f"{label}[{index}]")
    elif isinstance(expected, float):
        close(expected, actual, label)
    else:
        check(type(expected) is type(actual) and expected == actual, f"Value mismatch: {label}")


def validate_blocks(blocks: list) -> None:
    check(len(blocks) == 24, "Expected 24 blocks")
    ids = [row["block_id"] for row in blocks]
    check(len(set(ids)) == 24, "Duplicate block IDs")
    counts = Counter(row["family"] for row in blocks)
    check(len(counts) == 6 and set(counts.values()) == {4}, "Expected six families of four")
    for row in blocks:
        check(type(row["eta"]) is int and row["eta"] in (-1, 1), "Invalid eta")
        check(row["design_status"] == "author_defined_development" and
              row["interpretation_status"] == "unvalidated_author_defined", "Changed author-label boundary")
        check(row["candidate_a"] != row["candidate_b"], "Collapsed candidates")
        check(row["emoji_a"] != row["emoji_b"], "Collapsed emoji alternatives")
        for context in CONTEXTS:
            check(row[f"context_{context}"].count("{emoji}") == 1, "Malformed carrier slot")
            for variant in ALTERNATIVES:
                sign = row["eta"] * (1 if (context, variant) in (("p", "a"), ("q", "b")) else -1)
                check(row["orientation"][f"context_{context}"][f"emoji_{variant}"] ==
                      ("a" if sign > 0 else "b"), "Orientation and eta disagree")


def check_tokens(cell: dict, spec: dict, word: bool) -> None:
    if cell["status"] == "failed_preflight":
        return
    check(cell["status"] == "ready", "Invalid preflight status")
    for key in ("prompt_token_ids", "candidate_token_ids", "input_token_ids"):
        check(isinstance(cell[key], list) and cell[key] and
              all(type(x) is int and x >= 0 for x in cell[key]), f"Invalid IDs: {key}")
    p, c = cell["prompt_token_ids"], cell["candidate_token_ids"]
    check(cell["input_token_ids"] == p + c, "Candidate joint-prefix identity changed")
    check(cell["prompt_token_count"] == len(p) and cell["candidate_token_count"] == len(c),
          "Token count mismatch")
    check(len(cell["input_token_ids"]) <= spec["config"]["budget"]["max_input_tokens"] and
          len(c) <= spec["config"]["budget"]["max_candidate_tokens"], "Token budget exceeded")
    check(cell["first_candidate_predictor_position"] == len(p) - 1, "Predictor position changed")
    check(len(cell["candidate_token_strings"]) == len(c), "Candidate token strings incomplete")
    prefix = "carrier" if word else "emoji"
    positions = cell[f"{prefix}_token_positions"]
    check(isinstance(positions, list) and positions == sorted(set(positions)) and
          all(type(x) is int and 0 <= x < len(p) for x in positions), "Invalid carrier positions")
    check(cell[f"{prefix}_token_count"] == len(positions) and
          len(cell[f"{prefix}_token_offsets"]) == len(positions), "Carrier position count mismatch")
    check(bool(positions) == (cell["variant"] != "absent"), "Carrier position presence mismatch")


def check_spec(spec: dict, word: bool) -> None:
    protocol = WORD_PROTOCOL if word else EMOJI_PROTOCOL
    n = 192 if word else 288
    check(spec["schema_version"] == 1 and spec["protocol_id"] == protocol, "Specification protocol mismatch")
    check(spec["status"] == "development_preflight_zero_model_forwards", "Invalid preflight boundary")
    check(spec["claim_ceiling"] == CLAIM and spec["confirmatory"] is False, "Changed claim ceiling")
    check(spec["model_forwards"] == 0 and spec["generation_calls"] == 0 and
          spec["route_instrumented"] is False and spec["intervention_executed"] is False,
          "Preflight exceeded boundary")
    check(spec["model_artifact"]["manifest_sha256"] == MODEL_SHA, "Model pin changed")
    config = spec["config"]
    check(config["protocol_id"] == protocol and config["budget"]["max_sequences"] == n,
          "Configured sequence budget changed")
    check(config["inputs"]["sha256"] == spec["source"]["files"]["inputs"]["sha256"], "Input hash binding mismatch")
    check(config["inputs"]["expected_blocks"] == 24 and config["inputs"]["expected_families"] == 6 and
          config["inputs"]["expected_blocks_per_family"] == 4, "Input denominator changed")
    check(config["model"]["artifact_manifest_sha256"] == MODEL_SHA and config["model"]["download"] is False and
          config["model"]["local_files_only"] is True and config["model"]["dtype"] == "bf16", "Model config boundary changed")
    for key, value in {"add_special_tokens": False, "include_eos": False, "normalization": "none",
                       "boundary": "joint_tokenization_exact_prefix", "J": 1}.items():
        check(config["scoring"][key] == value, f"Scoring rule changed: {key}")
    validate_blocks(spec["blocks"])
    variants = ALTERNATIVES if word else (*ALTERNATIVES, "absent")
    planned = []
    for block in spec["blocks"]:
        if word:
            words = block["planned_word_alternatives"]
            check(set(words) == {"a", "b"} and all(isinstance(x, str) and x for x in words.values()) and
                  words["a"] != words["b"], "Distinct, pre-existing two-word mapping required")
        for context in CONTEXTS:
            template = block[f"context_{context}"]
            begin = template.index("{emoji}")
            for variant in variants:
                surface = (block["planned_word_alternatives"][variant] if word else
                           "" if variant == "absent" else block[f"emoji_{variant}"])
                for candidate in ALTERNATIVES:
                    expected = {"cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                                "block_id": block["block_id"], "family": block["family"], "eta": block["eta"],
                                "context": context, "variant": variant, "candidate": candidate,
                                "prompt": template.replace("{emoji}", surface),
                                "continuation": block[f"candidate_{candidate}"]}
                    prefix = "carrier" if word else "emoji"
                    expected.update({f"{prefix}_surface": surface, f"{prefix}_char_start": begin,
                                     f"{prefix}_char_end": begin + len(surface)})
                    if word:
                        expected["carrier_kind"] = "word"
                    planned.append(expected)
    check(len(spec["cells"]) == len(planned) == n, "Planned cell denominator changed")
    for expected, actual in zip(planned, spec["cells"], strict=True):
        for key, value in expected.items():
            check(actual.get(key) == value, f"Planned input changed: {expected['cell_id']}:{key}")
        check_tokens(actual, spec, word)
    check(spec["denominator"] == {"planned_blocks": 24, "planned_cells": n,
                                 "preflight_counts": dict(Counter(c["status"] for c in spec["cells"]))},
          "Preflight denominator changed")


def reconstruct(spec: dict, rows: list, word: bool) -> dict:
    """Compute all scores from individual token log probabilities."""
    n = 192 if word else 288
    check(len(rows) == n, "Missing acquisition records (unrun cells must retain rows)")
    check([r["cell_id"] for r in rows] == [r["cell_id"] for r in spec["cells"]], "Cell ID order changed")
    totals = {}
    for planned, actual in zip(spec["cells"], rows, strict=True):
        for key, value in planned.items():
            if key != "status":
                check(actual.get(key) == value, f"Immutable cell changed: {actual['cell_id']}:{key}")
        state = actual["status"]
        check(state in ("completed", "failed", "not_run", "failed_preflight"), "Invalid acquired state")
        check((state == "failed_preflight") == (planned["status"] == "failed_preflight"), "Preflight status rewritten")
        if state != "completed":
            check("candidate_token_logprobs" not in actual and "sequence_logprob_sum" not in actual,
                  "Unfinished row carries completed scores")
            continue
        values = actual["candidate_token_logprobs"]
        check(len(values) == actual["candidate_token_count"] and all(finite(x) and x <= 1e-6 for x in values),
              "Invalid or incomplete token scores")
        total = math.fsum(values)
        close(total, actual["sequence_logprob_sum"], actual["cell_id"])
        totals[actual["cell_id"]] = total
    blocks = []
    variants = ALTERNATIVES if word else (*ALTERNATIVES, "absent")
    for original in spec["blocks"]:
        identity, eta = original["block_id"], original["eta"]
        s, alignment, inputs = {}, {}, []
        for context in CONTEXTS:
            s[context], alignment[context] = {}, {}
            for variant in variants:
                keys = [f"{identity}:{context}:{variant}:{candidate}" for candidate in ALTERNATIVES]
                value = totals[keys[0]] - totals[keys[1]] if all(k in totals for k in keys) else None
                s[context][variant] = value
                if variant == "absent":
                    continue
                sign = eta * (1 if (context, variant) in (("p", "a"), ("q", "b")) else -1)
                expected = "a" if sign > 0 else "b"
                winner = None if value is None else "a" if value > 0 else "b" if value < 0 else "tie"
                aligned = winner == expected if winner is not None else None
                alignment[context][variant] = aligned
                inputs.append({"context": context, "variant": variant, "s": value,
                               "author_expected_candidate": expected, "higher_probability_candidate": winner,
                               "aligned": aligned, "author_oriented_margin": None if value is None else sign * value})
        delta = {c: None if any(s[c][v] is None for v in ALTERNATIVES) else s[c]["b"] - s[c]["a"]
                 for c in CONTEXTS}
        cross_complete = all(delta[c] is not None for c in CONTEXTS)
        complete = all(value is not None for c in CONTEXTS for value in s[c].values())
        aligned_count = sum(row["aligned"] is True for row in inputs)
        blocks.append({"block_id": identity, "family": original["family"], "eta": eta,
                       "complete": complete, "crossed_inputs_complete": cross_complete,
                       "s": s, "delta_p": delta["p"], "delta_q": delta["q"],
                       "H": eta * (delta["q"] - delta["p"]) if cross_complete else None,
                       "intended_delta_crossover": eta * delta["p"] < 0 < eta * delta["q"] if cross_complete else None,
                       "absolute_author_alignment": alignment,
                       "absolute_author_alignment_available": sum(r["aligned"] is not None for r in inputs),
                       "absolute_author_aligned_count": aligned_count,
                       "all_four_author_aligned": aligned_count == 4 if cross_complete else None,
                       "input_cells": inputs})
    family_rows = {}
    for family in sorted({b["family"] for b in blocks}):
        members = [b for b in blocks if b["family"] == family]
        values = [b["H"] for b in members if b["complete"]]
        family_rows[family] = {"planned_blocks": 4, "completed_blocks": len(values),
                               "available_complete_block_mean_H": math.fsum(values) / len(values) if values else None,
                               "full_family_mean_H": math.fsum(values) / 4 if len(values) == 4 else None,
                               "positive_H_blocks": sum(b["H"] is not None and b["H"] > 0 for b in members),
                               "directional_crossover_blocks": sum(b["intended_delta_crossover"] is True for b in members),
                               "aligned_inputs": sum(r["aligned"] is True for b in members for r in b["input_cells"]),
                               "all_four_aligned_blocks": sum(b["all_four_author_aligned"] is True for b in members)}
    counts = dict(Counter(row["status"] for row in rows))
    nc = sum(b["complete"] for b in blocks)
    inputs = [r for b in blocks for r in b["input_cells"]]
    na = sum(r["aligned"] is not None for r in inputs)
    denominator = {"planned_blocks": 24, "completed_blocks": nc, "incomplete_blocks": 24 - nc,
                   "planned_cells": n, "recorded_cells": len(rows), "cell_status_counts": counts}
    if word:
        denominator.update(planned_crossed_input_conditions=96, available_absolute_author_alignment_conditions=na)
    return {"blocks": blocks, "families": family_rows,
            "denominator": denominator,
            "forward_calls_attempted_recomputed": counts.get("completed", 0) + counts.get("failed", 0),
            "complete_population": nc == 24,
            "planned_population_equal_family_mean_H": math.fsum(b["H"] for b in blocks) / 24 if nc == 24 else None,
            "positive_H_blocks": sum(b["H"] is not None and b["H"] > 0 for b in blocks),
            "directional_crossover_blocks": sum(b["intended_delta_crossover"] is True for b in blocks),
            "absolute_author_alignment": {"planned_inputs": 96, "completed_inputs": na, "missing_inputs": 96 - na,
                                          "aligned_inputs": sum(r["aligned"] is True for r in inputs),
                                          "tied_inputs": sum(r["higher_probability_candidate"] == "tie" for r in inputs),
                                          "all_four_aligned_blocks": sum(b["all_four_author_aligned"] is True for b in blocks)}}


def audit_run(run_dir: Path, spec_path: Path, word: bool) -> tuple[dict, dict, dict]:
    spec_sha = digest(spec_path)
    check(digest(run_dir / "specification.json") == spec_sha, "Local specification hash changed")
    spec = read_object(spec_path)
    check_spec(spec, word)
    start, finish = read_object(run_dir / "run_started.json"), read_object(run_dir / "run_completed.json")
    n = 192 if word else 288
    for receipt in (start, finish):
        check(receipt["protocol_id"] == spec["protocol_id"] and receipt["schema_version"] == 1, "Run identity changed")
        check(receipt["specification_sha256"] == receipt["local_specification_sha256"] == spec_sha,
              "Receipt specification hash changed")
        check(receipt["planned_cells"] == n and receipt["planned_blocks"] == 24 and
              receipt["planned_cell_ids"] == [r["cell_id"] for r in spec["cells"]], "Run denominator changed")
        check(receipt["model_artifact"] == spec["model_artifact"] and receipt["source"] == spec["source"],
              "Run model/source identity changed")
        check(receipt["claim_ceiling"] == CLAIM and receipt["confirmatory"] is False and
              receipt["route_instrumented"] is False and receipt["intervention_executed"] is False and
              receipt["generation_calls"] == 0, "Run claim or action boundary changed")
        if word:
            check(receipt["comparators"] == spec["comparators"], "Run comparator bindings changed")
    check(start["status"] == "started", "Invalid start receipt")
    for key, value in start.items():
        if key != "status":
            check(finish.get(key) == value, f"Start receipt changed: {key}")
    check(digest(run_dir / "cells.jsonl") == finish["cells_sha256"], "Acquired cell hash mismatch")
    check(digest(run_dir / "summary.json") == finish["summary_sha256"], "Summary hash mismatch")
    lines = safe(run_dir / "cells.jsonl").read_text(encoding="utf-8").splitlines()
    check(all(line.strip() for line in lines), "Blank acquisition record")
    rows = [decode(line) for line in lines]
    limit = start.get("explicit_smoke_cell_limit")
    check(limit is None or type(limit) is int and 0 <= limit <= n, "Invalid smoke limit")
    if limit is not None:
        check(all(r["status"] in ("not_run", "failed_preflight") for r in rows[limit:]), "Smoke budget exceeded")
    result = reconstruct(spec, rows, word)
    check(result["denominator"] == finish["denominator"], "Recorded denominator mismatch")
    progress = finish["progress"]
    if word:
        scorer_attempts = progress.get("scorer_calls_attempted", progress["forward_calls_attempted"])
        check(result["forward_calls_attempted_recomputed"] == scorer_attempts <= n,
              "Scorer attempt budget mismatch")
        completed_count = result["denominator"]["cell_status_counts"].get("completed", 0)
        check(completed_count <= progress["forward_calls_attempted"] <= scorer_attempts,
              "Forward budget mismatch")
        check(digest(run_dir / "occupancy_checks.json") == finish["occupancy_checks_sha256"],
              "Occupancy receipt hash mismatch")
        occupancy = read_object(run_dir / "occupancy_checks.json")
        check(occupancy["policy"] == "fail_closed_other_compute_pid_before_each_forward", "Occupancy policy changed")
        check(all(r["other_compute_pids"] == [] for r in occupancy["successful_checks"]),
              "Occupied GPU passed a guard")
        result["actual_forward_calls_recorded"] = progress["forward_calls_attempted"]
    else:
        check(result["forward_calls_attempted_recomputed"] == progress["forward_calls_attempted"] <= n,
              "Forward budget mismatch")
    check(finish["status"] == ("completed" if result["complete_population"] else "partial_or_failed"),
          "Run completion status mismatch")
    check(finish["semantic_claim_supported"] is False, "Unsupported semantic claim")
    # First read the numerical summary only after reconstruction.
    summary = read_object(run_dir / "summary.json")
    subset = {"denominator": result["denominator"], "planned_population_equal_family_mean_H":
              result["planned_population_equal_family_mean_H"]}
    compare_values(subset, summary)
    fields = ("block_id", "family", "eta", "s", "delta_p", "delta_q", "H", "intended_delta_crossover")
    compare_values([{k: row[k] for k in fields} for row in result["blocks"]], summary["blocks"], "summary.blocks")
    if word:
        alignment_fields = ("absolute_author_alignment", "absolute_author_alignment_available",
                            "absolute_author_aligned_count", "all_four_author_aligned")
        compare_values([{k: row[k] for k in alignment_fields} for row in result["blocks"]],
                       summary["blocks"], "summary.block_alignment")
        compare_values({"positive_H_count": result["positive_H_blocks"],
                        "intended_delta_crossover_count": result["directional_crossover_blocks"],
                        "absolute_author_aligned_count": result["absolute_author_alignment"]["aligned_inputs"],
                        "all_four_author_aligned_block_count": result["absolute_author_alignment"]["all_four_aligned_blocks"]}, summary)
    family_subset = {name: {"planned_blocks": 4, "completed_blocks": row["completed_blocks"],
                            "incomplete_blocks": 4 - row["completed_blocks"],
                            "full_family_mean_H": row["full_family_mean_H"]}
                     for name, row in result["families"].items()}
    if word:
        for name, row in result["families"].items():
            family_subset[name].update(positive_H_count=row["positive_H_blocks"],
                                       intended_delta_crossover_count=row["directional_crossover_blocks"])
    compare_values(family_subset, summary["family_denominators"], "summary.families")
    result["bindings"] = {"specification_sha256": spec_sha, "cells_sha256": finish["cells_sha256"],
                          "run_completed_sha256": digest(run_dir / "run_completed.json"),
                          "runtime_sha256": digest(run_dir / "runtime.json"), "explicit_smoke_cell_limit": limit}
    return spec, result, read_object(run_dir / "runtime.json")


def paired_comparison(word_spec: dict, word: dict, emoji_spec: dict, emoji: dict) -> dict:
    check(word_spec["blocks"] == emoji_spec["blocks"], "Word control changed blocks/candidates/orientation")
    eb = {b["block_id"]: b for b in emoji["blocks"]}
    ec = {c["cell_id"]: c for c in emoji_spec["cells"]}
    wc = {c["cell_id"]: c for c in word_spec["cells"]}
    block_rows, input_rows, geometry, within_word_geometry = [], [], [], []
    transitions = Counter()
    for w in word["blocks"]:
        e = eb[w["block_id"]]
        available = w["complete"] and e["complete"]
        block_rows.append({"block_id": w["block_id"], "family": w["family"], "complete": available,
                           "H_word": w["H"], "H_emoji": e["H"],
                           "H_word_minus_emoji": w["H"] - e["H"] if available else None,
                           "delta_p_word_minus_emoji": w["delta_p"] - e["delta_p"] if w["delta_p"] is not None and e["delta_p"] is not None else None,
                           "delta_q_word_minus_emoji": w["delta_q"] - e["delta_q"] if w["delta_q"] is not None and e["delta_q"] is not None else None})
        for context in CONTEXTS:
            variants = [wc[f"{w['block_id']}:{context}:{variant}:a"] for variant in ALTERNATIVES]
            ready = all(cell["status"] == "ready" for cell in variants)
            within_word_geometry.append({"block_id": w["block_id"], "context": context, "available": ready,
                                         "word_a_positions": variants[0].get("carrier_token_positions"),
                                         "word_b_positions": variants[1].get("carrier_token_positions"),
                                         "word_a_prompt_tokens": variants[0].get("prompt_token_count"),
                                         "word_b_prompt_tokens": variants[1].get("prompt_token_count"),
                                         "carrier_position_arrays_match": variants[0].get("carrier_token_positions") == variants[1].get("carrier_token_positions") if ready else None,
                                         "prompt_token_counts_match": variants[0].get("prompt_token_count") == variants[1].get("prompt_token_count") if ready else None})
        ei = {(i["context"], i["variant"]): i for i in e["input_cells"]}
        for wi in w["input_cells"]:
            key = wi["context"], wi["variant"]
            old = ei[key]
            ready = wi["s"] is not None and old["s"] is not None
            transition = None if not ready else f"{old['higher_probability_candidate']}->{wi['higher_probability_candidate']}"
            status = lambda row: "missing" if row["aligned"] is None else "tie" if row["higher_probability_candidate"] == "tie" else "aligned" if row["aligned"] else "misaligned"
            alignment_transition = f"{status(old)}->{status(wi)}"
            transitions[alignment_transition] += 1
            absent = e["s"][wi["context"]]["absent"]
            input_rows.append({"block_id": w["block_id"], "family": w["family"], "context": key[0], "variant": key[1],
                               "available": ready, "s_word": wi["s"], "s_emoji": old["s"],
                               "s_word_minus_emoji": wi["s"] - old["s"] if ready else None,
                               "author_oriented_margin_change": wi["author_oriented_margin"] - old["author_oriented_margin"] if ready else None,
                               "candidate_transition": transition, "alignment_transition": alignment_transition,
                               "reused_baseline_absent_s": absent,
                               "word_minus_reused_absent_s": wi["s"] - absent if wi["s"] is not None and absent is not None else None,
                               "emoji_minus_reused_absent_s": old["s"] - absent if old["s"] is not None and absent is not None else None})
            ids = [f"{w['block_id']}:{key[0]}:{key[1]}:{c}" for c in ALTERNATIVES]
            new, oldc = wc[ids[0]], ec[ids[0]]
            candidates_available = all(wc[x]["status"] == ec[x]["status"] == "ready" for x in ids)
            if candidates_available:
                for x in ids:
                    check(wc[x]["candidate_token_ids"] == ec[x]["candidate_token_ids"], "Candidate token identity changed")
                    check(wc[x]["continuation"] == ec[x]["continuation"], "Candidate text changed")
                for source, prefix in ((wc, "carrier"), (ec, "emoji")):
                    check(source[ids[0]]["prompt_token_ids"] == source[ids[1]]["prompt_token_ids"] and
                          source[ids[0]][f"{prefix}_token_positions"] == source[ids[1]][f"{prefix}_token_positions"],
                          "Same prompt changed across candidates")
            geometry.append({"block_id": w["block_id"], "context": key[0], "variant": key[1],
                             "available": candidates_available,
                             "word_carrier_positions": new.get("carrier_token_positions"),
                             "emoji_carrier_positions": oldc.get("emoji_token_positions"),
                             "carrier_position_arrays_match": new.get("carrier_token_positions") == oldc.get("emoji_token_positions") if candidates_available else None,
                             "word_prompt_tokens": new.get("prompt_token_count"), "emoji_prompt_tokens": oldc.get("prompt_token_count"),
                             "prompt_token_counts_match": new.get("prompt_token_count") == oldc.get("prompt_token_count") if candidates_available else None,
                             "word_carrier_crosses_span_boundary": new.get("carrier_tokens_cross_span_boundary"),
                             "emoji_carrier_crosses_span_boundary": oldc.get("emoji_tokens_cross_span_boundary"),
                             "candidate_token_identity_matches": True if candidates_available else None})
            if candidates_available:
                a_ids, b_ids = wc[ids[0]]["candidate_token_ids"], wc[ids[1]]["candidate_token_ids"]
                geometry[-1].update(candidate_a_is_token_prefix_of_b=len(a_ids) < len(b_ids) and b_ids[:len(a_ids)] == a_ids,
                                    candidate_b_is_token_prefix_of_a=len(b_ids) < len(a_ids) and a_ids[:len(b_ids)] == b_ids,
                                    candidates_same_token_sequence=a_ids == b_ids)
    complete = [b for b in block_rows if b["complete"]]
    families = {}
    for family in sorted({b["family"] for b in block_rows}):
        values = [b["H_word_minus_emoji"] for b in complete if b["family"] == family]
        families[family] = {"planned_blocks": 4, "completed_paired_blocks": len(values),
                            "available_paired_mean_H_word_minus_emoji": math.fsum(values) / len(values) if values else None,
                            "full_family_mean_H_word_minus_emoji": math.fsum(values) / 4 if len(values) == 4 else None}
    margins = [r["author_oriented_margin_change"] for r in input_rows if r["available"]]
    return {"planned_blocks": 24, "completed_paired_blocks": len(complete), "missing_paired_blocks": 24 - len(complete),
            "full_population_equal_family_mean_H_word_minus_emoji": math.fsum(b["H_word_minus_emoji"] for b in complete) / 24 if len(complete) == 24 else None,
            "paired_H_word_greater_blocks": sum(b["H_word_minus_emoji"] > 0 for b in complete),
            "paired_H_word_less_blocks": sum(b["H_word_minus_emoji"] < 0 for b in complete),
            "paired_H_tied_blocks": sum(b["H_word_minus_emoji"] == 0 for b in complete),
            "families": families, "blocks": block_rows, "matched_input_cells": input_rows,
            "planned_input_cells": 96, "completed_paired_input_cells": len(margins),
            "full_population_mean_author_oriented_margin_change": math.fsum(margins) / 96 if len(margins) == 96 else None,
            "absolute_alignment_transitions": dict(transitions),
            "token_geometry": {"planned_input_pairs": 96, "available_pairs": sum(r["available"] for r in geometry),
                               "carrier_position_mismatches": sum(r["carrier_position_arrays_match"] is False for r in geometry),
                               "prompt_token_count_mismatches": sum(r["prompt_token_counts_match"] is False for r in geometry),
                               "rows": geometry, "exclusions_based_on_geometry": 0,
                               "outcomes_used_for_eligibility": False},
            "within_word_token_geometry": {"planned_context_pairs": 48,
                                           "available_pairs": sum(r["available"] for r in within_word_geometry),
                                           "missing_pairs": sum(not r["available"] for r in within_word_geometry),
                                           "carrier_position_mismatches": sum(r["carrier_position_arrays_match"] is False for r in within_word_geometry),
                                           "prompt_token_count_mismatches": sum(r["prompt_token_counts_match"] is False for r in within_word_geometry),
                                           "rows": within_word_geometry, "exclusions_based_on_geometry": 0,
                                           "outcomes_used_for_eligibility": False},
            "absent_control_source": "saved_emoji_baseline_only_no_additional_absent_forwards"}


def compare(word_run_dir: Path, word_specification: Path, emoji_run_dir: Path) -> dict:
    check(digest(emoji_run_dir / "specification.json") == EMOJI_SPEC_SHA, "Pinned emoji specification changed")
    check(digest(emoji_run_dir / "cells.jsonl") == EMOJI_CELLS_SHA, "Pinned emoji cells changed")
    check(digest(emoji_run_dir / "runtime.json") == BASELINE_RUNTIME_SHA, "Pinned emoji runtime changed")
    word_spec = read_object(word_specification)
    pins = {"baseline_specification": EMOJI_SPEC_SHA, "baseline_cells": EMOJI_CELLS_SHA,
            "baseline_runner": BASELINE_RUNNER_SHA, "baseline_runtime": BASELINE_RUNTIME_SHA}
    for key, value in pins.items():
        check(word_spec["comparators"][key]["sha256"] == value and
              word_spec["config"]["comparators"][key]["sha256"] == value,
              f"Comparator pin changed: {key}")
    check(word_spec["source"]["files"]["baseline_helpers"]["sha256"] == BASELINE_RUNNER_SHA,
          "Scoring helper identity changed")
    emoji_spec, emoji, emoji_runtime = audit_run(emoji_run_dir, emoji_run_dir / "specification.json", False)
    word_spec, word, word_runtime = audit_run(word_run_dir, word_specification, True)
    check(word_spec["model_artifact"] == emoji_spec["model_artifact"], "Model artifact parity failure")
    check(word_spec["source"]["files"]["inputs"]["sha256"] == emoji_spec["source"]["files"]["inputs"]["sha256"],
          "Stimulus file identity changed")
    for key in ("python_version", "runtime_packages", "tokenizer_class", "tokenizer_vocab_size"):
        check(word_spec[key] == emoji_spec[key], f"Runtime/tokenizer parity failure: {key}")
    check(word_runtime == emoji_runtime, "Runtime parity failure; no pooled/comparable result permitted")
    comparison = paired_comparison(word_spec, word, emoji_spec, emoji)
    return {"comparison_schema_version": 1, "protocol_id": WORD_PROTOCOL,
            "status": "independent_saved_arithmetic_and_paired_comparison_validated",
            "model_runtime_parity": True, "summary_numerics_used": False,
            "model_loaded": False, "tokenizer_loaded": False, "model_forwards": 0,
            "model_probability_reexecution_verified": False, "source_model_files_reopened": False,
            "confirmatory": False, "semantic_claim_supported": False, "causal_claim_supported": False,
            "pvalues_or_confidence_intervals_computed": False, "claim_ceiling": CLAIM,
            "validator_sha256": digest(Path(__file__)), "word": word, "emoji": emoji, "paired": comparison,
            "limitations": ["Selected after inspecting the emoji pilot; word comparison is development evidence.",
                            "Author-defined alignment is not human-validated accuracy or meaning.",
                            "Word and emoji carrier token lengths/positions need not match; no outcome-based exclusions.",
                            "Fixed candidate prefix probabilities without EOS are not normalized answer-choice probabilities.",
                            "Six families with recurring emoji and block-specific word phrases do not establish population-level generalization.",
                            "Arithmetic and receipts are checked; underlying model probabilities are not independently rerun."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--word-run-dir", required=True, type=Path)
    parser.add_argument("--word-specification", required=True, type=Path)
    parser.add_argument("--emoji-run-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New JSON receipt; refuses to overwrite")
    args = parser.parse_args()
    try:
        result = compare(args.word_run_dir, args.word_specification, args.emoji_run_dir)
        text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
        destination = safe(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(text)
        print(json.dumps({"status": result["status"], "output": str(destination),
                          "word_denominator": result["word"]["denominator"]}))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"status": "comparison_failed", "error": str(error),
                          "error_type": type(error).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
