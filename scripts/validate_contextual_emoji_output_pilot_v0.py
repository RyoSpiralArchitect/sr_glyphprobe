#!/usr/bin/env python3
"""Independent, standard-library-only audit of saved development-pilot cells.

No acquisition-runner, tokenizer, model, or numerical inference code is imported.
The runner summary is read only after reconstruction, as a comparison target.
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


PROTOCOL = "glyphprobe-contextual-emoji-output-pilot-v0"
CLAIM = "author_defined_development_labels_only_not_semantic_or_confirmatory"
MODEL_PIN = "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
MODEL_REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
CONTEXTS = ("p", "q")
VARIANTS = ("a", "b", "absent")
CANDIDATES = ("a", "b")


def check(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def safe(path: Path) -> Path:
    check(path.name not in PROTECTED, "Protected target path prohibited")
    resolved = path.resolve()
    check(resolved.name not in PROTECTED, "Protected target path prohibited")
    return resolved


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        check(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(text: str) -> Any:
    def invalid(value: str) -> None:
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid)


def read_object(path: Path) -> dict[str, Any]:
    value = decode(safe(path).read_text(encoding="utf-8"))
    check(isinstance(value, dict), "Expected JSON object")
    return value


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def positive_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def token_ids(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, int) and not isinstance(item, bool) and item >= 0 for item in value
    )


def planned_from_blocks(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Construct literal input identities without importing the runner."""
    check(spec.get("protocol_id") == PROTOCOL and spec.get("schema_version") == 1,
          "Specification identity mismatch")
    check(spec.get("status") == "development_preflight_zero_model_forwards", "Wrong preflight status")
    check(spec.get("claim_ceiling") == CLAIM and spec.get("confirmatory") is False, "Claim ceiling changed")
    for key in ("model_forwards", "generation_calls"):
        check(spec.get(key) == 0, f"Preflight {key} must be zero")
    for key in ("intervention_executed", "route_instrumented"):
        check(spec.get(key) is False, f"Preflight {key} changed")
    cfg = spec["config"]
    check(cfg.get("protocol_id") == PROTOCOL, "Config protocol mismatch")
    check(cfg["inputs"]["expected_blocks"] == 24 and cfg["inputs"]["expected_families"] == 6
          and cfg["inputs"]["expected_blocks_per_family"] == 4, "Development denominator changed")
    check(cfg["inputs"]["sha256"] == spec["source"]["files"]["inputs"]["sha256"], "Input binding mismatch")
    model = cfg["model"]
    check(model["artifact_manifest_sha256"] == MODEL_PIN and model["revision"] == MODEL_REVISION,
          "Intended model artifact pin changed")
    check(spec["model_artifact"]["manifest_sha256"] == MODEL_PIN, "Recorded model artifact mismatch")
    check(model.get("local_files_only") is True and model.get("download") is False
          and model.get("dtype") == "bf16", "Model execution boundary changed")
    for key, value in {"add_special_tokens": False, "include_eos": False,
                       "normalization": "none", "boundary": "joint_tokenization_exact_prefix", "J": 1}.items():
        check(cfg["scoring"].get(key) == value, f"Scoring rule changed: {key}")
    check(cfg["budget"]["max_sequences"] == 288, "Sequence denominator changed")
    blocks = spec["blocks"]
    check(isinstance(blocks, list) and len(blocks) == 24, "Expected exactly 24 development blocks")
    ids = [row["block_id"] for row in blocks]
    check(all(isinstance(item, str) and item for item in ids) and len(set(ids)) == 24,
          "Invalid or duplicate block IDs")
    families = Counter(row["family"] for row in blocks)
    check(len(families) == 6 and set(families.values()) == {4}, "Family denominator changed")
    planned: list[dict[str, Any]] = []
    for block in blocks:
        check(block.get("design_status") == "author_defined_development"
              and block.get("interpretation_status") == "unvalidated_author_defined", "Block claim boundary changed")
        eta = block["eta"]
        check(type(eta) is int and eta in (-1, 1), "Invalid orientation sign")
        check(block["emoji_a"] != block["emoji_b"] and block["candidate_a"] != block["candidate_b"],
              "Collapsed alternatives")
        intended = {"context_p": {"emoji_a": "a", "emoji_b": "b"},
                    "context_q": {"emoji_a": "b", "emoji_b": "a"}}
        if eta == -1:
            intended = {context: {emoji: ("b" if candidate == "a" else "a")
                                  for emoji, candidate in mapping.items()}
                        for context, mapping in intended.items()}
        check(block.get("orientation") == intended, "Orientation map and eta disagree")
        for context in CONTEXTS:
            template = block[f"context_{context}"]
            check(isinstance(template, str) and template.count("{emoji}") == 1, "Malformed prompt slot")
            start = template.index("{emoji}")
            for variant in VARIANTS:
                surface = "" if variant == "absent" else block[f"emoji_{variant}"]
                for candidate in CANDIDATES:
                    planned.append({
                        "cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                        "block_id": block["block_id"], "family": block["family"],
                        "context": context, "variant": variant, "candidate": candidate,
                        "prompt": template.replace("{emoji}", surface),
                        "continuation": block[f"candidate_{candidate}"], "emoji_surface": surface,
                        "emoji_char_start": start, "emoji_char_end": start + len(surface), "eta": eta,
                    })
    check(len(spec["cells"]) == len(planned) == 288, "Specification cell denominator changed")
    for expected, cell in zip(planned, spec["cells"], strict=True):
        check(all(cell.get(key) == value for key, value in expected.items()),
              f"Changed planned cell: {expected['cell_id']}")
        check(cell["status"] in ("ready", "failed_preflight"), "Invalid preflight cell status")
        if cell["status"] == "ready":
            prompt, continuation, full = cell["prompt_token_ids"], cell["candidate_token_ids"], cell["input_token_ids"]
            check(token_ids(prompt) and token_ids(continuation) and token_ids(full), "Invalid token IDs")
            check(full == prompt + continuation, "Joint token-prefix identity mismatch")
            check(cell["prompt_token_count"] == len(prompt) and cell["candidate_token_count"] == len(continuation),
                  "Token count mismatch")
            check(len(full) <= cfg["budget"]["max_input_tokens"]
                  and len(continuation) <= cfg["budget"]["max_candidate_tokens"], "Token budget exceeded")
            check(cell["first_candidate_predictor_position"] == len(prompt) - 1, "Predictor position mismatch")
            check(len(cell["candidate_token_strings"]) == len(continuation), "Candidate token strings incomplete")
            positions = cell["emoji_token_positions"]
            check(isinstance(positions, list) and all(type(p) is int and 0 <= p < len(prompt) for p in positions)
                  and positions == sorted(set(positions)), "Invalid emoji token positions")
            check(cell["emoji_token_count"] == len(positions)
                  and len(cell["emoji_token_offsets"]) == len(positions), "Emoji diagnostic count mismatch")
            check(bool(positions) == (cell["variant"] != "absent"), "Emoji span presence mismatch")
    expected_denominator = {"planned_blocks": 24, "planned_cells": 288,
                            "preflight_counts": dict(Counter(row["status"] for row in spec["cells"]))}
    check(spec["denominator"] == expected_denominator, "Preflight denominator mismatch")
    return planned


def arithmetic(spec: dict[str, Any], rows: list[dict[str, Any]], smoke_limit: int | None) -> dict[str, Any]:
    """Recompute from per-token scores, never trusting saved sequence totals."""
    check(len(rows) == 288, "Missing or additional acquisition records")
    expected_ids = [cell["cell_id"] for cell in spec["cells"]]
    check([row["cell_id"] for row in rows] == expected_ids, "Missing, duplicate, reordered, or changed cell IDs")
    check(smoke_limit is None or type(smoke_limit) is int and 0 <= smoke_limit <= 288, "Invalid smoke limit")
    sums: dict[str, float] = {}
    maximum_error = 0.0
    for index, (before, row) in enumerate(zip(spec["cells"], rows, strict=True)):
        for key, value in before.items():
            if key != "status":
                check(key in row and row[key] == value, f"Saved cell field changed: {row['cell_id']}:{key}")
        state = row["status"]
        check(state in {"completed", "failed", "failed_preflight", "not_run"}, "Unknown cell status")
        check((state == "failed_preflight") == (before["status"] == "failed_preflight"), "Preflight status was rewritten")
        if smoke_limit is not None and index >= smoke_limit:
            check(state in {"not_run", "failed_preflight"}, "Acquisition exceeded explicit smoke limit")
        if row.get("reason") == "explicit_partial_smoke_limit":
            check(state == "not_run" and smoke_limit is not None and index >= smoke_limit, "Invalid smoke exclusion")
        if state != "completed":
            check("candidate_token_logprobs" not in row and "sequence_logprob_sum" not in row,
                  "Uncompleted cell carries apparently completed scores")
            continue
        values = row["candidate_token_logprobs"]
        check(isinstance(values, list) and len(values) == before["candidate_token_count"], "Incomplete per-token scores")
        check(all(finite_number(value) and value <= 1e-6 for value in values), "Invalid per-token log probabilities")
        total = math.fsum(values)
        stored = row["sequence_logprob_sum"]
        check(finite_number(stored), "Nonfinite stored sequence total")
        error = abs(stored - total)
        check(error <= 1e-10, "Stored sequence total differs from full token sum")
        maximum_error = max(maximum_error, error)
        sums[row["cell_id"]] = total
    reports = []
    for block in spec["blocks"]:
        block_id = block["block_id"]
        scores: dict[str, dict[str, float | None]] = {"p": {}, "q": {}}
        missing = []
        for context in CONTEXTS:
            for variant in VARIANTS:
                keys = [f"{block_id}:{context}:{variant}:{candidate}" for candidate in CANDIDATES]
                available = all(key in sums for key in keys)
                scores[context][variant] = sums[keys[0]] - sums[keys[1]] if available else None
                if not available:
                    missing.append(f"{context}:{variant}")
        deltas = {}
        for context in CONTEXTS:
            a, b = scores[context]["a"], scores[context]["b"]
            deltas[context] = None if a is None or b is None else b - a
        dp, dq = deltas["p"], deltas["q"]
        have_cross = dp is not None and dq is not None
        reports.append({"block_id": block_id, "family": block["family"], "eta": block["eta"],
                        "complete_with_absent_controls": not missing, "missing_pairs": missing,
                        "s": scores, "delta_p": dp, "delta_q": dq,
                        "H": block["eta"] * (dq - dp) if have_cross else None,
                        "intended_delta_crossover": (block["eta"] * dp < 0 < block["eta"] * dq) if have_cross else None})
    families = {}
    for name in sorted({block["family"] for block in spec["blocks"]}):
        members = [row for row in reports if row["family"] == name]
        available = [row["H"] for row in members if row["complete_with_absent_controls"]]
        families[name] = {"planned_blocks": 4, "completed_blocks": len(available),
                          "incomplete_blocks": 4 - len(available),
                          "available_complete_block_mean_H": math.fsum(available) / len(available) if available else None,
                          "full_family_mean_H": math.fsum(available) / 4 if len(available) == 4 else None}
    ncomplete = sum(row["complete_with_absent_controls"] for row in reports)
    counts = dict(Counter(row["status"] for row in rows))
    denominator = {"planned_blocks": 24, "completed_blocks": ncomplete, "incomplete_blocks": 24 - ncomplete,
                   "planned_cells": 288, "recorded_cells": len(rows), "cell_status_counts": counts}
    return {"blocks": reports, "families": families, "denominator": denominator,
            "complete_population": ncomplete == 24,
            "planned_population_equal_family_mean_H": math.fsum(row["full_family_mean_H"] for row in families.values()) / 6
                if ncomplete == 24 else None,
            "sequence_totals_recomputed": len(sums), "maximum_sequence_sum_error": maximum_error,
            "forward_calls_attempted_recomputed": counts.get("completed", 0) + counts.get("failed", 0)}


def expected_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Express independently reconstructed outputs in the acquisition schema."""
    blocks = []
    for row in result["blocks"]:
        item = {key: value for key, value in row.items() if key != "complete_with_absent_controls"}
        item.update(status="completed" if row["complete_with_absent_controls"] else "incomplete", claim_ceiling=CLAIM)
        blocks.append(item)
    full_blocks = [row["H"] for row in result["blocks"] if row["complete_with_absent_controls"]]
    available_families = {name: row["available_complete_block_mean_H"] for name, row in result["families"].items()
                          if row["completed_blocks"] > 0}
    family_counts = {name: {key: value for key, value in row.items() if key != "available_complete_block_mean_H"}
                     for name, row in result["families"].items()}
    return {"blocks": blocks, "denominator": result["denominator"], "descriptive_only": True,
            "confirmatory": False, "claim_ceiling": CLAIM,
            "complete_block_mean_H": math.fsum(full_blocks) / len(full_blocks) if full_blocks else None,
            "family_complete_block_mean_H": available_families,
            "mean_of_available_family_means_H": math.fsum(available_families.values()) / len(available_families)
                if available_families else None,
            "family_denominators": family_counts,
            "planned_population_equal_family_mean_H": result["planned_population_equal_family_mean_H"],
            "available_case_summaries_are_not_full_population_estimates": True,
            "incomplete_population_warning": not result["complete_population"],
            "semantic_claim_supported": False, "route_instrumented": False, "intervention_executed": False}


def exploratory_diagnostics(spec: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    """Author-oriented absolute preference and acquisition-token geometry only."""
    alignment_rows = []
    alignment_blocks = []
    for block in result["blocks"]:
        block_rows = []
        for context in CONTEXTS:
            for variant in ("a", "b"):
                score = block["s"][context][variant]
                positive_diagonal = (context, variant) in (("p", "a"), ("q", "b"))
                desired_sign = block["eta"] * (1 if positive_diagonal else -1)
                expected = "a" if desired_sign > 0 else "b"
                observed = None if score is None else "a" if score > 0 else "b" if score < 0 else "tie"
                entry = {"block_id": block["block_id"], "context": context, "variant": variant,
                         "s": score, "author_expected_candidate": expected,
                         "higher_probability_candidate": observed,
                         "aligned": observed == expected if observed is not None else None}
                alignment_rows.append(entry)
                block_rows.append(entry)
        available = all(row["aligned"] is not None for row in block_rows)
        alignment_blocks.append({"block_id": block["block_id"], "crossed_inputs_complete": available,
                                 "all_four_aligned": all(row["aligned"] is True for row in block_rows) if available else None})

    by_id = {cell["cell_id"]: cell for cell in spec["cells"]}
    geometry_rows = []
    for block in spec["blocks"]:
        for context in CONTEXTS:
            variants = {}
            for variant in ("a", "b"):
                pair = [by_id[f"{block['block_id']}:{context}:{variant}:{candidate}"] for candidate in CANDIDATES]
                available = all(cell["status"] == "ready" for cell in pair)
                if available:
                    check(pair[0]["prompt_token_ids"] == pair[1]["prompt_token_ids"]
                          and pair[0]["emoji_token_positions"] == pair[1]["emoji_token_positions"],
                          "Same rendered prompt has different token geometry across candidates")
                variants[variant] = pair[0]["emoji_token_positions"] if available else None
            available = all(value is not None for value in variants.values())
            geometry_rows.append({"block_id": block["block_id"], "context": context,
                                  "emoji_a_positions": variants["a"], "emoji_b_positions": variants["b"],
                                  "arrays_match": variants["a"] == variants["b"] if available else None})
    completed = sum(row["aligned"] is not None for row in alignment_rows)
    aligned = sum(row["aligned"] is True for row in alignment_rows)
    geometry_completed = sum(row["arrays_match"] is not None for row in geometry_rows)
    return {
        "status": "exploratory_author_label_diagnostics_not_human_task_accuracy",
        "post_acquisition_request": True,
        "inference_performed": False,
        "alignment_rule": "Strict sign of raw candidate_a_minus_candidate_b logprob against eta-defined author mapping; ties are not aligned.",
        "absolute_candidate_alignment": {
            "planned_crossed_input_cells": 96, "completed_crossed_input_cells": completed,
            "missing_crossed_input_cells": 96 - completed, "aligned_crossed_input_cells": aligned,
            "misaligned_crossed_input_cells": sum(row["aligned"] is False for row in alignment_rows),
            "tied_crossed_input_cells": sum(row["higher_probability_candidate"] == "tie" for row in alignment_rows),
            "planned_denominator_fraction": aligned / 96 if completed == 96 else None,
            "planned_blocks": 24,
            "blocks_with_complete_crossed_inputs": sum(row["crossed_inputs_complete"] for row in alignment_blocks),
            "all_four_aligned_blocks": sum(row["all_four_aligned"] is True for row in alignment_blocks),
            "input_cells": alignment_rows, "blocks": alignment_blocks,
        },
        "within_context_emoji_token_position_arrays": {
            "source": "saved_preflight_specification_not_new_tokenizer_or_model_execution",
            "planned_pairs": 48, "available_pairs": geometry_completed, "missing_pairs": 48 - geometry_completed,
            "mismatched_pairs": sum(row["arrays_match"] is False for row in geometry_rows),
            "matched_pairs": sum(row["arrays_match"] is True for row in geometry_rows),
            "pairs": geometry_rows,
        },
        "claim_limits": [
            "Author-defined candidate alignment is not human-validated task success or accuracy.",
            "Positive H or an emoji-effect crossover does not imply absolute candidate alignment.",
            "Token-position mismatch is a future intervention-design diagnostic, not a baseline exclusion or causal result.",
        ],
    }


def compare_summary(expected: Any, observed: Any, path: str = "summary") -> dict[str, Any]:
    """Strict structure and flags; finite floating-point comparison at 1e-10."""
    maximum = 0.0
    numeric_values = 0

    def visit(left: Any, right: Any, name: str) -> None:
        nonlocal maximum, numeric_values
        if isinstance(left, dict):
            check(isinstance(right, dict) and left.keys() == right.keys(), f"Summary fields differ: {name}")
            for key, value in left.items():
                visit(value, right[key], f"{name}.{key}")
        elif isinstance(left, list):
            check(isinstance(right, list) and len(left) == len(right), f"Summary list differs: {name}")
            for index, (a, b) in enumerate(zip(left, right, strict=True)):
                visit(a, b, f"{name}[{index}]")
        elif isinstance(left, float):
            check(finite_number(right), f"Summary nonfinite or nonnumeric value: {name}")
            error = abs(left - right)
            check(error <= 1e-10, f"Summary numerical mismatch: {name}")
            maximum = max(maximum, error)
            numeric_values += 1
        else:
            check(type(left) is type(right) and left == right, f"Summary value mismatch: {name}")

    visit(expected, observed, path)
    return {"compared_after_independent_reconstruction": True, "maximum_absolute_numeric_error": maximum,
            "floating_point_values_compared": numeric_values, "absolute_tolerance": 1e-10}


def validate(run_dir: Path, specification: Path, require_full: bool = False) -> dict[str, Any]:
    """Use a separately supplied preflight to bind the saved run specification."""
    authority_hash = digest(specification)
    local = run_dir / "specification.json"
    local_hash = digest(local)
    check(local_hash == authority_hash, "Run specification differs from supplied preflight")
    spec = read_object(specification)
    planned_from_blocks(spec)
    start = read_object(run_dir / "run_started.json")
    finish = read_object(run_dir / "run_completed.json")
    ids = [cell["cell_id"] for cell in spec["cells"]]
    for receipt in (start, finish):
        check(receipt.get("protocol_id") == PROTOCOL and receipt.get("schema_version") == 1, "Run identity mismatch")
        check(receipt.get("specification_sha256") == authority_hash
              and receipt.get("local_specification_sha256") == local_hash, "Specification hash mismatch")
        check(receipt.get("planned_cell_ids") == ids and receipt.get("planned_blocks") == 24
              and receipt.get("planned_cells") == 288, "Run planned denominator changed")
        check(receipt.get("source") == spec["source"] and receipt.get("model_artifact") == spec["model_artifact"],
              "Run source or model binding changed")
        check(receipt.get("claim_ceiling") == CLAIM and receipt.get("confirmatory") is False, "Run claim boundary changed")
        check(receipt.get("generation_calls") == 0 and receipt.get("route_instrumented") is False
              and receipt.get("intervention_executed") is False, "Run expanded beyond baseline")
    check(start["status"] == "started", "Invalid start receipt")
    for key, value in start.items():
        if key != "status":
            check(finish.get(key) == value, f"Initial receipt field changed: {key}")
    cells_path = run_dir / "cells.jsonl"
    check(digest(cells_path) == finish["cells_sha256"], "Acquired cells hash mismatch")
    # The acquisition aggregate is not an input to any calculation below.
    check(digest(run_dir / "summary.json") == finish["summary_sha256"], "Summary file hash mismatch")
    lines = safe(cells_path).read_text(encoding="utf-8").splitlines()
    check(all(line.strip() for line in lines), "Blank acquisition record")
    rows = [decode(line) for line in lines]
    check(all(isinstance(row, dict) for row in rows), "Invalid acquisition record")
    result = arithmetic(spec, rows, start["explicit_smoke_cell_limit"])
    # Deliberately first parse the comparison target only after all estimates exist.
    comparison = compare_summary(expected_summary(result), read_object(run_dir / "summary.json"))
    diagnostics = exploratory_diagnostics(spec, result)
    check(finish["denominator"] == result["denominator"], "Recorded denominator differs from reconstructed denominator")
    check(finish["progress"]["forward_calls_attempted"] == result["forward_calls_attempted_recomputed"], "Attempted-forward denominator mismatch")
    check(finish["status"] == ("completed" if result["complete_population"] else "partial_or_failed"), "Completion status mismatch")
    check(finish.get("semantic_claim_supported") is False, "Unsupported semantic claim")
    if require_full:
        check(start["explicit_smoke_cell_limit"] is None and result["complete_population"], "A full non-smoke population was required")
    if result["complete_population"]:
        scope = "full_development_population" if start["explicit_smoke_cell_limit"] is None else "explicit_smoke_with_complete_population"
    else:
        scope = "partial_explicit_smoke" if start["explicit_smoke_cell_limit"] is not None else "partial_or_failed_acquisition"
    return {"protocol_id": PROTOCOL, "validator_schema_version": 1, "status": "validated_saved_scalar_arithmetic",
            "validation_scope": scope, "specification_sha256": authority_hash,
            "cells_sha256": finish["cells_sha256"], "run_completed_sha256": digest(run_dir / "run_completed.json"),
            "validator_sha256": digest(Path(__file__)), "summary_numerics_used": False,
            "summary_comparison": comparison,
            "exploratory_author_label_diagnostics": diagnostics,
            "model_loaded": False, "tokenizer_loaded": False, "resampling_performed": False,
            "model_probability_reexecution_verified": False,
            "confirmatory": False, "semantic_claim_supported": False, "causal_claim_supported": False,
            "claim_ceiling": CLAIM,
            "limitations": ["Validates saved token-score arithmetic and bound record consistency, not logits or model execution.",
                            "Source and model files are not reopened; their identities remain the acquisition receipts' claims.",
                            "An explicit smoke run is never an independent replication or an untouched confirmation."],
            **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--specification", required=True, type=Path, help="Separately preserved preflight JSON")
    parser.add_argument("--require-full", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional new receipt; refuses to overwrite")
    args = parser.parse_args()
    try:
        result = validate(args.run_dir, args.specification, args.require_full)
        rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.output:
            destination = safe(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            print(rendered, end="")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"status": "validation_failed", "error_type": type(error).__name__, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
