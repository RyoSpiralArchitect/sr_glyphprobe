#!/usr/bin/env python3
"""Freeze/audit the exposed-384 CPU design; no tokenizer, model, or bank reader.

This is a design/input freeze, not acquisition admission. A future runner and
analysis implementation must bind this specification and pass its replay gate.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import os
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-t22-kv-cpu-exposed384-design-v0"
PILOT = "validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json"
PARENT = "validation/t22_cpu_engineering_v0/canary"
LEXICAL = "validation/t22_cpu_lexical_canary_v0/acquisition"
PINS = {
    PILOT: "0015887f2dc37318a577c748d2b3b2f8f217982d377d6ce12662feeb37d389d5",
    PARENT + "/specification.json": "d334efa55ad2438079e27ba05347eb92f421bd51ad1066e060371f259b939df7",
    PARENT + "/acquisition_receipt.json": "27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901",
    LEXICAL + "/specification.json": "e6da21348028f8fffe6bda879336beeffcbf515e1862271dada2db6f4bf56067",
    LEXICAL + "/acquisition_receipt.json": "5bac71106134a2c5f56cbc5c8e371e5e48832e084ca233a2d020ffa7598d10b2",
}
TEST = "tests/test_t22_kv_exploration_spec_v0.py"
FILES = (
    "scripts/t22_kv_exploration_spec_v0.py", TEST,
    "docs/T22_KV_EXPLORATION_CPU_V0.md", "docs/T22_KV_EXPLORATION_CPU_V0.ja.md",
    "scripts/t22_kv_dissection_v0.py", "scripts/t22_kv_cpu_canary_v0.py",
    "scripts/t22_cpu_lexical_canary_v0.py", "scripts/t21_glyph_context_path_pilot_v0.py",
    "scripts/validate_t22_cpu_acquisition_v0.py", "src/glyphprobe/io.py",
    "src/glyphprobe/provenance.py", "configs/t21_glyph_context_path_pilot_v0.yaml",
)
CARRIERS = ("pipe", "article_a")
OPS = ("none", "k", "v", "kv")
POSITIONS = ("glyph", "suffix")


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    def pairs(values):
        result = {}
        for key, value in values:
            check(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=invalid)


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def source_hashes(root):
    return {name: sha(root / name) for name in FILES}


def input_geometry(pilot, canary):
    check(pilot["target_count"] == 384 and pilot["source_count"] == 128,
          "Exactly 384 targets and 128 sources required")
    check(pilot["reserve_access_allowed"] is False, "Historical reserve access prohibited")
    targets, sources = pilot["target_tokens"], pilot["source_tokens"]
    check(len(targets) == 384 and len(sources) == 128, "Input count mismatch")
    check(targets[:8] == canary["target_tokens"] and sources == canary["source_tokens"]
          and pilot["donor_indices"][:8] == canary["donor_indices"], "Changed eight-item overlap")
    check(pilot["model_artifact"] == canary["model_artifact"], "Changed model pin")
    suffixes = {}
    for group in (targets, sources):
        for index, row in enumerate(group):
            check(type(row["index"]) is int and row["index"] == index, "Changed original item order")
            raw = row["raw"]
            check(set(raw) == {"glyph", "alias_label", "codepoint_literal"}, "Changed token views")
            check(len(raw["glyph"]) in (2, 3), "Unsupported glyph length")
            check(set(row["sequences"]) == set(CARRIERS), "Changed carriers")
            for carrier in CARRIERS:
                check(set(row["sequences"][carrier]) == set(raw), "Changed sequence views")
                for view, prefix in raw.items():
                    sequence = row["sequences"][carrier][view]
                    check(prefix and len(sequence) == len(prefix) + 8
                          and sequence[:len(prefix)] == prefix, "Changed eight-token carrier geometry")
                    check(all(type(token) is int and 0 <= token < 128256 for token in sequence),
                          "Invalid token ID")
                    suffix = sequence[-8:]
                    if carrier in suffixes:
                        check(suffixes[carrier] == suffix, "Carrier differs across views/items")
                    suffixes[carrier] = suffix
    for view in ("glyph", "alias_label"):
        check(len({tuple(row["raw"][view]) for row in targets + sources}) == 512,
              "Duplicate or overlapping " + view)
    check(len(pilot["donor_indices"]) == 384, "Missing donor rows")
    for row, donors in zip(targets, pilot["donor_indices"]):
        check(len(donors) == 2 and len(set(donors)) == 2
              and all(type(d) is int and 0 <= d < 128 for d in donors), "Invalid fixed donor pair")
        check(all(len(sources[d]["raw"]["glyph"]) == len(row["raw"]["glyph"]) for d in donors),
              "Donor token counts differ")
    hist = {name: dict(sorted(Counter(str(len(r["raw"]["glyph"])) for r in group).items()))
            for name, group in (("target", targets), ("source", sources))}
    check(hist == {"target": {"2": 68, "3": 316}, "source": {"2": 22, "3": 106}},
          "Changed population composition")
    return hist


def row_layout(length):
    check(type(length) is int and length in (2, 3), "Unsupported glyph length")
    readout = length + 8 - 1
    return [{"operation": op, "position": pos, "donor_slot": donor,
             "anchor": 21, "distance": 8, "readout_position": readout,
             "selected_positions": list(range(length)) if pos == "glyph"
             else list(range(readout - length, readout))}
            for op in OPS for pos in POSITIONS for donor in (0, 1)]


def design():
    return {
        "population": {"n_items": 384, "source_count": 128,
                       "target_order": "original_T21_pilot_indices_0_through_383",
                       "previous_T22_outcomes_known_indices": list(range(8)),
                       "exclude_previous_eight": False, "fresh_confirmation": False,
                       "donors_and_gallery": "unchanged_original_T21_pilot",
                       "outcome_selection_or_retuning": False},
        "intervention": {"anchor": 21, "reset": "same_item_codepoint_readout_residual",
                         "active_blocks": list(range(22, 28)), "distance": 8,
                         "carriers": list(CARRIERS), "operations": list(OPS),
                         "position_groups": list(POSITIONS), "query_local": True,
                         "keys": "post_RoPE", "values": "unrotated_values",
                         "same_slot_neutral": "path_replacement_disabled_reset_retained",
                         "extension_batch_size": 16, "row_layouts": {
                             str(length): row_layout(length) for length in (2, 3)}},
        "acquisition": {"source_alias_single_sequence_forwards": 256,
                        "per_target_per_carrier": ["stock_glyph", "adapter_idle_glyph",
                            "donor_0_capture", "donor_1_capture", "codepoint_reset_capture",
                            "extension_active_batch16", "extension_neutral_batch16",
                            "stock_glyph_replay_for_alias_gate", "alias_single_sequence"],
                        "per_target_calls": 18, "per_target_sequences": 78,
                        "total_calls": 7168, "total_sequences": 30208,
                        "reacquire_all_384_and_128_aliases": True,
                        "legacy_88_row_batch_repeated_for_each_target": False,
                        "gate_indices": list(range(8)), "gate_rows_count_toward_384": True,
                        "first8_gate": "exact_all_26_saved_nonlegacy_arrays_and_target_aliases",
                        "source_alias_gate": "exact_all_128_two_carrier_original_CPU_alias_rows",
                        "before_item_8": "all_first8_replay_checks_pass",
                        "persist": ["26_nonlegacy_arrays_per_item", "target_alias_rows",
                                    "source_alias_rows", "per_item_checks_counts_timing_and_hashes"],
                        "generation_calls": 0, "tokenizer_calls": 0, "training_calls": 0},
        "analysis": {"readout": "final_norm_last_carrier_token_distance8", "float": "float64",
                     "normalization": "L2", "gallery": "own_first_then_original_128_sources",
                     "top1_tie_rule": "own_first_argmax", "own_rank": "1_plus_strictly_greater_competitors",
                     "competitor_tie_rule": "first_in_original_source_order",
                     "scores_shape": [384, 2, 2, 16, 129], "scored_rows": 24576,
                     "cosines": 3170304, "effect": "active_minus_identical_slot_neutral",
                     "adjusted": "mean_carrier_donor(effect_suffix_minus_effect_glyph)_within_item",
                     "absolute_glyph": "minus_mean_carrier_donor(effect_glyph)_within_item",
                     "nonadditivity": "adjusted_KV_minus_K_minus_V",
                     "metrics": ["own_cosine", "max_competitor_cosine", "competitor_identity",
                                 "own_minus_max_competitor", "matched_donor_cosine",
                                 "own_minus_matched_donor", "own_rank", "own_first_top1"],
                     "numeric_summaries": ["all_item_values", "mean", "median", "sample_sd_ddof1",
                                           "min", "max", "positive_zero_negative_counts",
                                           "quantiles_0.025_0.25_0.5_0.75_0.975_numpy_linear"],
                     "summary_strata": ["all_384", "carrier_separately", "glyph_token_count_2_or_3"],
                     "no_inference_for_diagnostic_strata": True,
                     "preserve_carrier_donor_rows": True, "population_intervals": False,
                     "hypothesis_tests": False, "efficacy_screen": False, "winner_selection": False,
                     "reference_exact_zero": True, "arithmetic_tolerance": 1e-12,
                     "diagnostics": ["own_minus_competitor_decomposition",
                                     "local_vs_actual_neutral_attention_weights_by_block_and_head",
                                     "headwise_weight_L1_and_glyph_suffix_mass",
                                     "top1_discordance_and_full_competitor_IDs"],
                     "no_partial_effect_report": True},
        "execution_admission": {"admitted": False, "runner_source_sha256": None,
                                "analysis_source_sha256": None, "required": [
                                    "source_bound_synthetic_validation_of_new_runner_and_analysis",
                                    "execution_manifest_binding_this_exact_design_and_runner_analysis_hashes",
                                    "exact_model_manifest_before_and_after_acquisition",
                                    "runtime_pin_and_adapter_source_match",
                                    "independent_saved_array_audit",
                                    "first8_and_source_alias_exact_replay_before_item_8",
                                    "independent_384_metric_reconstruction_before_interpretation"]},
        "runtime_policy": {"torch": "2.13.0+cpu", "transformers": "5.15.0", "numpy": "2.5.4",
                           "dtype": "bfloat16", "attention": "eager", "threads": 4,
                           "interop_threads": 1, "device": "cpu", "seed": 2026092100,
                           "quantization": False, "remote_code": False, "cache": False,
                           "padding": False, "single_model_process": True},
        "resources": {"planning_estimate_is_not_measured_runner_runtime": True,
                      "max_cumulative_active_hours": 48, "max_active_hours_per_invocation": 8,
                      "rss_limit_gib": 20, "minimum_free_disk_gib_before_start_or_resume": 20,
                      "run_artifact_limit_gib": 10,
                      "budget_action": "pause_preserve_chunks_no_effect_screen_no_completion_claim",
                      "resume": "identical_incomplete_work_only_hash_validate_all_committed_chunks",
                      "unknown_interrupted_time": "resolve_in_execution_ledger_before_resume",
                      "completed_run": "immutable",
                      "hash_runtime_parity_nonfinite_failure": "stop_no_scientific_interpretation",
                      "amendment": "new_version_and_explanation_before_affected_acquisition"},
        "unrun_controls": ["historical_GPU_replay", "codepoint_gallery", "restoration",
                           "reference_attention_clamp", "intact_vs_reset_design", "nonemoji_panel",
                           "generation_behavior", "new_confirmatory_population"],
    }


def bound_inputs(root):
    for path, expected in PINS.items():
        check(sha(root / path) == expected, "Historical evidence changed: " + path)
    pilot, canary = read(root / PILOT), read(root / PARENT / "specification.json")
    geometry = input_geometry(pilot, canary)
    lexical = read(root / LEXICAL / "specification.json")
    check(lexical["runtime"] == canary["runtime"] and lexical["model_artifact"] == canary["model_artifact"]
          and lexical["source_tokens"] == pilot["source_tokens"] and lexical["numpy"] == "2.5.4",
          "Alias acquisition differs from CPU parent")
    parent_receipt = read(root / PARENT / "acquisition_receipt.json")
    check(parent_receipt["target_items"] == 8 and all(v is True for v in parent_receipt["checks"].values()),
          "Incomplete parent engineering evidence")
    pins = dict(PINS)
    for specification in (canary, lexical):
        for name, expected in specification["source_sha256"].items():
            check(name.startswith(("scripts/", "tests/", "docs/", "src/", "configs/", "validation/"))
                  and ".." not in Path(name).parts, "Unexpected historical source path")
            check(sha(root / name) == expected, "Historical bound source changed: " + name)
            pins[name] = expected
    for name in ("torch", "transformers", "dtype", "attention", "threads", "interop_threads", "device"):
        check(canary["runtime"][name] == design()["runtime_policy"][name], "Reference runtime pin mismatch")
    selected, full = [], []
    for index in range(8):
        name = f"item_{index:04d}"
        path = PARENT + "/" + name + "/receipt.json"
        check(sha(root / path) == parent_receipt["chunks"][name], "Changed timing item receipt")
        pins[path] = sha(root / path)
        item = read(root / path)
        arrays = PARENT + "/" + name + "/states.npz"
        check(sha(root / arrays) == item["states_sha256"], "Changed replay array")
        pins[arrays] = item["states_sha256"]
        timing = item["timing_seconds"]
        chosen = [timing[f"{carrier}_{stage}"] for carrier in CARRIERS for stage in
                  ("stock", "t22_idle", "t22_donor_0", "t22_donor_1", "t22_reset_capture",
                   "extension_active", "extension_neutral")]
        check(all(type(t) in (float, int) and t >= 0 for t in chosen), "Invalid stage timing")
        selected.append(sum(chosen))
        full.append(timing["total"])
    alias_receipt = read(root / LEXICAL / "acquisition_receipt.json")
    gallery = LEXICAL + "/gallery.npz"
    check(sha(root / gallery) == alias_receipt["gallery_sha256"], "Changed alias replay gallery")
    pins[gallery] = alias_receipt["gallery_sha256"]
    alias_seconds = alias_receipt["elapsed_seconds_after_manifest_this_invocation"]
    # Four target alias/replay forwards plus two per source, all single sequence.
    alias_proxy = alias_seconds * (384 * 4 + 128 * 2) / 288
    budget = {"selected_stage_seconds_per_canary_item": selected,
              "selected_stage_mean_seconds": statistics.mean(selected),
              "alias_time_scaling_proxy_seconds": alias_proxy,
              "projected_hours_mean": (384 * statistics.mean(selected) + alias_proxy) / 3600,
              "projected_hours_slowest_canary_scenario": (384 * max(selected) + alias_proxy) / 3600,
              "repeat_full_engineering_projected_hours": (384 * statistics.mean(full) + alias_proxy) / 3600,
              "caveat": "Stage-time extrapolation plus alias scaling (including old load/final manifest overhead); not measured reduced-runner time or a confidence bound. New shapes/resource conditions can differ."}
    return pilot, canary, geometry, pins, budget


def payload(root):
    pilot, canary, geometry, pins, budget = bound_inputs(root)
    return {"protocol_id": PROTOCOL, "status": "design_frozen_execution_not_admitted",
            "source_sha256": source_hashes(root), "evidence_sha256": pins,
            "target_tokens": pilot["target_tokens"], "source_tokens": pilot["source_tokens"],
            "donor_indices": pilot["donor_indices"], "token_length_counts": geometry,
            "model_artifact": pilot["model_artifact"], "reference_runtime": canary["runtime"],
            "design": design(), "execution_budget": budget,
            "new_384_acquisition_model_forwards": 0, "protected_bank_reads": 0,
            "t22_eight_outcomes_previously_seen": True}


def validate(root, output):
    check(not output.exists() and not output.with_suffix(".junit.xml").exists(), "Validation output exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    before = source_hashes(root)
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", TEST]
    collected = subprocess.run([*command, "--collect-only"], cwd=root, env=env,
                               capture_output=True, text=True, check=True)
    nodes = [line for line in collected.stdout.splitlines() if line.startswith(TEST + "::")]
    check(len(nodes) > 0, "No design tests collected")
    xml = output.with_suffix(".junit.xml")
    run = subprocess.run([*command, f"--junitxml={xml}"], cwd=root, env=env,
                         capture_output=True, text=True)
    print(run.stdout, end="")
    counts = {key: sum(int(s.get(key, 0)) for s in ET.parse(xml).getroot().findall("testsuite"))
              for key in ("tests", "failures", "errors", "skipped")}
    ok = (run.returncode == 0 and counts["tests"] == len(nodes)
          and counts["failures"] == counts["errors"] == counts["skipped"] == 0
          and source_hashes(root) == before)
    result = {"protocol_id": PROTOCOL, "status": "pass" if ok else "fail",
              "source_sha256": before, "test_counts": counts, "collected": len(nodes),
              "exit_code": run.returncode, "junit_sha256": sha(xml),
              "model_forwards": 0, "protected_bank_reads": 0}
    write(output, result)
    check(ok, "Design validation failed")
    return result


def freeze(root, validation, output):
    check(not output.exists(), "Specification output already exists")
    validation = validation.resolve()
    check(validation.is_relative_to(root.resolve()), "Validation receipt must be inside this checkout")
    receipt = read(validation)
    check(receipt["protocol_id"] == PROTOCOL and receipt["status"] == "pass"
          and receipt["source_sha256"] == source_hashes(root), "Current source-bound validation required")
    counts = receipt["test_counts"]
    check(type(counts["tests"]) is int and counts["tests"] > 0
          and counts["tests"] == receipt["collected"] and receipt["exit_code"] == 0
          and all(counts[k] == 0 for k in ("errors", "failures", "skipped")), "Incomplete test validation")
    check(sha(validation.with_suffix(".junit.xml")) == receipt["junit_sha256"], "Changed validation XML")
    result = payload(root)
    result.update(created_at_utc=datetime.now(timezone.utc).isoformat(),
                  validation_receipt=validation.relative_to(root.resolve()).as_posix(),
                  validation_receipt_sha256=sha(validation))
    check(source_hashes(root) == result["source_sha256"], "Sources changed during freeze")
    write(output, result)
    return {"status": result["status"], "specification_sha256": sha(output), "acquisition_admitted": False}


def audit(root, specification, expected_sha):
    check(sha(specification) == expected_sha, "Externally pinned specification changed")
    stored = read(specification)
    path = stored["validation_receipt"]
    check(not Path(path).is_absolute() and ".." not in Path(path).parts, "Unsafe validation path")
    check(sha(root / path) == stored["validation_receipt_sha256"], "Changed validation receipt")
    receipt = read(root / path)
    check(receipt["status"] == "pass" and receipt["source_sha256"] == source_hashes(root),
          "Validation does not bind current design")
    check(sha((root / path).with_suffix(".junit.xml")) == receipt["junit_sha256"], "Changed validation XML")
    expected = payload(root)
    for key, value in expected.items():
        check(stored[key] == value, "Frozen design mismatch: " + key)
    check(set(stored) == set(expected) | {"created_at_utc", "validation_receipt", "validation_receipt_sha256"},
          "Unexpected specification fields")
    return {"status": "pass", "protocol_id": PROTOCOL, "specification_sha256": expected_sha,
            "target_items": 384, "source_items": 128, "first_eight_retained": True,
            "acquisition_admitted": False, "model_forwards": 0, "protected_bank_reads": 0,
            "boundary": "Deterministic design/input integrity audit, not independent model or outcome validation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--output", type=Path, required=True)
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--validation", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    audit_parser = commands.add_parser("audit")
    audit_parser.add_argument("--specification", type=Path, required=True)
    audit_parser.add_argument("--expected-sha256", required=True)
    audit_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate(args.repo, args.output)
    elif args.command == "freeze":
        result = freeze(args.repo, args.validation, args.output)
    else:
        check(not args.output.exists(), "Audit output already exists")
        result = audit(args.repo, args.specification, args.expected_sha256)
        write(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
