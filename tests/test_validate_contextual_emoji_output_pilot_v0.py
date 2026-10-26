"""Synthetic model-free fixtures; no acquisition runner or model dependency."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/validate_contextual_emoji_output_pilot_v0.py"
MODULE_SPEC = importlib.util.spec_from_file_location("independent_output_validator", MODULE_PATH)
validator = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(validator)


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def fixture(directory: Path, limit=None, fail_index=None):
    blocks, cells, rows = [], [], []
    for family in range(6):
        for index in range(4):
            eta = 1 if index % 2 == 0 else -1
            orientation = {"context_p": {"emoji_a": "a", "emoji_b": "b"},
                           "context_q": {"emoji_a": "b", "emoji_b": "a"}}
            if eta < 0:
                orientation = {c: {e: ("b" if a == "a" else "a") for e, a in m.items()}
                               for c, m in orientation.items()}
            block = {"block_id": f"f{family}_{index}", "family": f"family{family}", "eta": eta,
                     "orientation": orientation, "design_status": "author_defined_development",
                     "interpretation_status": "unvalidated_author_defined", "context_p": "Goal p: {emoji}\nReply:",
                     "context_q": "Goal q: {emoji}\nReply:", "emoji_a": "x", "emoji_b": "y",
                     "candidate_a": " yes.", "candidate_b": " no."}
            blocks.append(block)
            for context in ("p", "q"):
                template = block[f"context_{context}"]
                start = template.index("{emoji}")
                for variant in ("a", "b", "absent"):
                    surface = "" if variant == "absent" else block[f"emoji_{variant}"]
                    for candidate in ("a", "b"):
                        candidate_ids = [20, 21] if candidate == "a" else [22, 23]
                        cell = {"cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                                "block_id": block["block_id"], "family": block["family"], "eta": eta,
                                "context": context, "variant": variant, "candidate": candidate,
                                "prompt": template.replace("{emoji}", surface), "continuation": block[f"candidate_{candidate}"],
                                "emoji_surface": surface, "emoji_char_start": start, "emoji_char_end": start + len(surface),
                                "status": "ready", "prompt_token_ids": [10, 11], "candidate_token_ids": candidate_ids,
                                "input_token_ids": [10, 11] + candidate_ids, "prompt_token_count": 2, "candidate_token_count": 2,
                                "candidate_token_strings": [" token", "."], "first_candidate_predictor_position": 1,
                                "emoji_token_positions": [1] if surface else [], "emoji_token_count": 1 if surface else 0,
                                "emoji_token_offsets": [[start, start + 1]] if surface else [],
                                "emoji_tokens_cross_span_boundary": False}
                        cells.append(cell)
                        row = deepcopy(cell)
                        i = len(rows)
                        if fail_index is not None and i == fail_index:
                            row.update(status="failed", error="synthetic failure", error_type="RuntimeError")
                        elif fail_index is not None and i > fail_index:
                            row.update(status="not_run", reason="stopped_after_cell_failure")
                        elif limit is not None and i >= limit:
                            row.update(status="not_run", reason="explicit_partial_smoke_limit")
                        else:
                            desired = 0 if variant == "absent" else (2 if (context, variant) in (("p", "a"), ("q", "b")) else -2)
                            desired *= eta
                            total = -2 + (desired / 2 if candidate == "a" else -desired / 2)
                            row.update(status="completed", candidate_token_logprobs=[total / 2, total / 2], sequence_logprob_sum=total)
                        rows.append(row)
    config = {"protocol_id": validator.PROTOCOL,
              "inputs": {"expected_blocks": 24, "expected_families": 6, "expected_blocks_per_family": 4, "sha256": "1" * 64},
              "model": {"artifact_manifest_sha256": validator.MODEL_PIN, "revision": validator.MODEL_REVISION,
                        "local_files_only": True, "download": False, "dtype": "bf16"},
              "scoring": {"add_special_tokens": False, "include_eos": False, "normalization": "none",
                          "boundary": "joint_tokenization_exact_prefix", "J": 1},
              "budget": {"max_sequences": 288, "max_input_tokens": 512, "max_candidate_tokens": 64}}
    spec = {"protocol_id": validator.PROTOCOL, "schema_version": 1, "status": "development_preflight_zero_model_forwards",
            "claim_ceiling": validator.CLAIM, "confirmatory": False, "model_forwards": 0, "generation_calls": 0,
            "intervention_executed": False, "route_instrumented": False, "config": config,
            "source": {"files": {"inputs": {"sha256": "1" * 64}}},
            "model_artifact": {"manifest_sha256": validator.MODEL_PIN}, "blocks": blocks, "cells": cells,
            "denominator": {"planned_blocks": 24, "planned_cells": 288, "preflight_counts": {"ready": 288}}}
    original = directory / "original_preflight.json"
    run = directory / "run"
    run.mkdir()
    dump(original, spec)
    dump(run / "specification.json", spec)
    started = {"protocol_id": validator.PROTOCOL, "schema_version": 1, "status": "started",
               "specification_sha256": validator.digest(original), "local_specification_sha256": validator.digest(original),
               "planned_cell_ids": [cell["cell_id"] for cell in cells], "planned_blocks": 24, "planned_cells": 288,
               "source": spec["source"], "model_artifact": spec["model_artifact"], "claim_ceiling": validator.CLAIM,
               "confirmatory": False, "generation_calls": 0, "route_instrumented": False, "intervention_executed": False,
               "explicit_smoke_cell_limit": limit}
    dump(run / "run_started.json", started)
    write_rows(run, rows)
    # These are synthetic arithmetic fixtures, never a scientific result.
    # No acquisition runner is imported, including to create its comparison target.
    comparison = validator.expected_summary(validator.arithmetic(spec, rows, limit))
    dump(run / "summary.json", comparison)
    complete = sum(all(row["status"] == "completed" for row in rows[i:i + 12]) for i in range(0, 288, 12))
    denominator = {"planned_blocks": 24, "completed_blocks": complete, "incomplete_blocks": 24 - complete,
                   "planned_cells": 288, "recorded_cells": 288, "cell_status_counts": dict(Counter(row["status"] for row in rows))}
    final = {**started, "status": "completed" if complete == 24 else "partial_or_failed", "semantic_claim_supported": False,
             "denominator": denominator, "cells_sha256": validator.digest(run / "cells.jsonl"),
             "summary_sha256": validator.digest(run / "summary.json"),
             "progress": {"forward_calls_attempted": sum(row["status"] in ("completed", "failed") for row in rows)}}
    dump(run / "run_completed.json", final)
    return run, original, spec, rows, final


def write_rows(run, rows):
    (run / "cells.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class IndependentValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_full_arithmetic_then_summary_comparison(self):
        run, original, _, _, _ = fixture(self.base)
        result = validator.validate(run, original, require_full=True)
        self.assertEqual(result["validation_scope"], "full_development_population")
        self.assertEqual(result["sequence_totals_recomputed"], 288)
        self.assertEqual(result["planned_population_equal_family_mean_H"], 8)
        self.assertEqual(result["maximum_sequence_sum_error"], 0)
        self.assertTrue(all(row["H"] == 8 and row["intended_delta_crossover"] for row in result["blocks"]))
        self.assertTrue(all(row["full_family_mean_H"] == 8 for row in result["families"].values()))
        self.assertFalse(result["summary_numerics_used"])
        self.assertEqual(result["summary_comparison"]["maximum_absolute_numeric_error"], 0)

    def test_smoke_keeps_full_missing_denominator(self):
        run, original, _, _, _ = fixture(self.base, limit=12)
        result = validator.validate(run, original)
        self.assertEqual(result["validation_scope"], "partial_explicit_smoke")
        self.assertEqual(result["denominator"]["completed_blocks"], 1)
        self.assertEqual(result["denominator"]["cell_status_counts"], {"completed": 12, "not_run": 276})
        self.assertIsNone(result["planned_population_equal_family_mean_H"])
        self.assertTrue(all(row["full_family_mean_H"] is None for row in result["families"].values()))
        with self.assertRaisesRegex(ValueError, "full non-smoke"):
            validator.validate(run, original, require_full=True)

    def test_failure_is_not_an_explicit_smoke(self):
        run, original, _, _, _ = fixture(self.base, fail_index=13)
        result = validator.validate(run, original)
        self.assertEqual(result["validation_scope"], "partial_or_failed_acquisition")
        self.assertEqual(result["forward_calls_attempted_recomputed"], 14)
        self.assertIsNone(result["planned_population_equal_family_mean_H"])

    def test_absent_missing_keeps_crossed_H_but_excludes_block(self):
        _, _, spec, rows, _ = fixture(self.base)
        rows[10] = {**spec["cells"][10], "status": "not_run", "reason": "synthetic"}
        result = validator.arithmetic(spec, rows, None)
        self.assertEqual(result["blocks"][0]["H"], 8)
        self.assertFalse(result["blocks"][0]["complete_with_absent_controls"])
        self.assertIsNone(result["families"]["family0"]["full_family_mean_H"])

    def test_changed_spec_hash_rejected(self):
        run, original, spec, _, _ = fixture(self.base)
        spec["blocks"][0]["candidate_a"] = " changed"
        dump(run / "specification.json", spec)
        with self.assertRaisesRegex(ValueError, "supplied preflight"):
            validator.validate(run, original)

    def test_changed_cell_id_rejected_even_with_rehashed_file(self):
        run, original, _, rows, final = fixture(self.base)
        rows[0]["cell_id"] = "invented"
        write_rows(run, rows)
        final["cells_sha256"] = validator.digest(run / "cells.jsonl")
        dump(run / "run_completed.json", final)
        with self.assertRaisesRegex(ValueError, "cell IDs"):
            validator.validate(run, original)

    def test_duplicate_or_missing_cell_rejected(self):
        _, _, spec, rows, _ = fixture(self.base)
        for altered in (rows[:-1], rows + [rows[-1]], [rows[0]] + rows[:-1]):
            with self.subTest(length=len(altered)), self.assertRaises(ValueError):
                validator.arithmetic(spec, altered, None)

    def test_immutable_token_change_rejected(self):
        _, _, spec, rows, _ = fixture(self.base)
        rows[0]["candidate_token_ids"] = [5, 6]
        with self.assertRaisesRegex(ValueError, "field changed"):
            validator.arithmetic(spec, rows, None)

    def test_sequence_not_sum_rejected(self):
        _, _, spec, rows, _ = fixture(self.base)
        rows[0]["sequence_logprob_sum"] += 0.01
        with self.assertRaisesRegex(ValueError, "full token sum"):
            validator.arithmetic(spec, rows, None)

    def test_invalid_scores_rejected(self):
        _, _, spec, rows, _ = fixture(self.base)
        for bad in ([float("nan"), -1], [0.1, -1], [True, -1], [-1]):
            changed = deepcopy(rows)
            changed[0]["candidate_token_logprobs"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validator.arithmetic(spec, changed, None)

    def test_orientation_and_family_denominator_rejected(self):
        _, _, spec, _, _ = fixture(self.base)
        for change in ("orientation", "family", "pin"):
            changed = deepcopy(spec)
            if change == "orientation":
                changed["blocks"][0]["eta"] = -1
            elif change == "family":
                changed["blocks"][0]["family"] = "family1"
            else:
                changed["config"]["model"]["artifact_manifest_sha256"] = "0" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                validator.planned_from_blocks(changed)

    def test_recorded_denominator_rejected(self):
        run, original, _, _, final = fixture(self.base)
        final["denominator"]["planned_cells"] = 12
        dump(run / "run_completed.json", final)
        with self.assertRaisesRegex(ValueError, "denominator"):
            validator.validate(run, original)

    def test_changed_summary_rejected_after_recomputation(self):
        run, original, _, _, final = fixture(self.base)
        summary = validator.read_object(run / "summary.json")
        summary["blocks"][0]["H"] = 100
        dump(run / "summary.json", summary)
        final["summary_sha256"] = validator.digest(run / "summary.json")
        dump(run / "run_completed.json", final)
        with self.assertRaisesRegex(ValueError, "Summary numerical mismatch"):
            validator.validate(run, original)

    def test_smoke_limit_cannot_hide_extra_forwards(self):
        _, _, spec, rows, _ = fixture(self.base)
        with self.assertRaisesRegex(ValueError, "exceeded explicit smoke"):
            validator.arithmetic(spec, rows, 12)

    def test_positive_H_does_not_imply_crossover(self):
        _, _, spec, rows, _ = fixture(self.base)
        # Block 0: delta_p = +1, delta_q = +2 -> H = +1, but no reversal.
        wanted = {("p", "a"): 0, ("p", "b"): 1, ("q", "a"): 0, ("q", "b"): 2}
        for row in rows[:12]:
            score = wanted.get((row["context"], row["variant"]), 0)
            total = -3 + (score / 2 if row["candidate"] == "a" else -score / 2)
            row.update(candidate_token_logprobs=[total / 2, total / 2], sequence_logprob_sum=total)
        result = validator.arithmetic(spec, rows, None)
        self.assertEqual(result["blocks"][0]["H"], 1)
        self.assertFalse(result["blocks"][0]["intended_delta_crossover"])

    def test_absolute_alignment_respects_eta(self):
        _, _, spec, rows, _ = fixture(self.base)
        result = validator.arithmetic(spec, rows, None)
        diagnostics = validator.exploratory_diagnostics(spec, result)
        alignment = diagnostics["absolute_candidate_alignment"]
        self.assertEqual(alignment["aligned_crossed_input_cells"], 96)
        self.assertEqual(alignment["all_four_aligned_blocks"], 24)
        self.assertEqual(alignment["tied_crossed_input_cells"], 0)
        self.assertEqual(diagnostics["within_context_emoji_token_position_arrays"]["mismatched_pairs"], 0)

    def test_positive_H_does_not_imply_absolute_success(self):
        _, _, spec, rows, _ = fixture(self.base)
        # Every candidate-A score is higher; an interaction nevertheless remains.
        wanted = {("p", "a"): 2, ("p", "b"): 3, ("q", "a"): 2, ("q", "b"): 4}
        for row in rows[:12]:
            score = wanted.get((row["context"], row["variant"]), 0)
            total = -5 + (score / 2 if row["candidate"] == "a" else -score / 2)
            row.update(candidate_token_logprobs=[total / 2, total / 2], sequence_logprob_sum=total)
        result = validator.arithmetic(spec, rows, None)
        diagnostics = validator.exploratory_diagnostics(spec, result)
        self.assertEqual(result["blocks"][0]["H"], 1)
        self.assertEqual(diagnostics["absolute_candidate_alignment"]["aligned_crossed_input_cells"], 94)
        self.assertFalse(diagnostics["absolute_candidate_alignment"]["blocks"][0]["all_four_aligned"])

    def test_alignment_missingness_and_ties_are_not_success(self):
        _, _, spec, rows, _ = fixture(self.base, limit=12)
        rows[0]["candidate_token_logprobs"] = rows[1]["candidate_token_logprobs"][:]
        rows[0]["sequence_logprob_sum"] = rows[1]["sequence_logprob_sum"]
        result = validator.arithmetic(spec, rows, 12)
        alignment = validator.exploratory_diagnostics(spec, result)["absolute_candidate_alignment"]
        self.assertEqual(alignment["completed_crossed_input_cells"], 4)
        self.assertEqual(alignment["missing_crossed_input_cells"], 92)
        self.assertEqual(alignment["aligned_crossed_input_cells"], 3)
        self.assertEqual(alignment["tied_crossed_input_cells"], 1)
        self.assertEqual(alignment["all_four_aligned_blocks"], 0)
        self.assertIsNone(alignment["planned_denominator_fraction"])

    def test_token_position_mismatch_uses_arrays_not_just_counts(self):
        _, _, spec, rows, _ = fixture(self.base)
        for cell in spec["cells"]:
            if cell["variant"] == "b":
                cell["emoji_token_positions"] = [0]
        result = validator.arithmetic(fixture_spec := deepcopy(spec),
                                      [dict(row, emoji_token_positions=[0]) if row["variant"] == "b" else row for row in rows], None)
        geometry = validator.exploratory_diagnostics(fixture_spec, result)["within_context_emoji_token_position_arrays"]
        self.assertEqual(geometry["available_pairs"], 48)
        self.assertEqual(geometry["mismatched_pairs"], 48)

    def test_protected_path_rejected_without_open(self):
        with self.assertRaisesRegex(ValueError, "Protected"):
            validator.digest(self.base / "p2_confirmatory_targets_v1.jsonl")

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validator.decode('{"status":"completed","status":"failed"}')


if __name__ == "__main__":
    unittest.main()
