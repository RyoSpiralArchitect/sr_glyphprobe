"""Synthetic, model-free tests for the independent paired-score comparator."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/compare_contextual_emoji_word_control_v0.py"
SPEC = importlib.util.spec_from_file_location("independent_word_comparison", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def dump(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")


def records(path, rows):
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def make_spec(word):
    blocks, cells = [], []
    for family in range(6):
        for index in range(4):
            eta = 1 if index % 2 == 0 else -1
            orientation = {}
            for context in ("p", "q"):
                orientation[f"context_{context}"] = {}
                for variant in ("a", "b"):
                    sign = eta * (1 if (context, variant) in (("p", "a"), ("q", "b")) else -1)
                    orientation[f"context_{context}"][f"emoji_{variant}"] = "a" if sign > 0 else "b"
            block = {"block_id": f"f{family}_{index}", "family": f"f{family}", "eta": eta,
                     "orientation": orientation, "design_status": "author_defined_development",
                     "interpretation_status": "unvalidated_author_defined", "context_p": "Goal p: {emoji}\nReply:",
                     "context_q": "Goal q: {emoji}\nReply:", "emoji_a": "X", "emoji_b": "Y",
                     "candidate_a": " yes.", "candidate_b": " no.",
                     "planned_word_alternatives": {"a": "alpha", "b": "beta"}}
            blocks.append(block)
            for context in ("p", "q"):
                template = block[f"context_{context}"]
                begin = template.index("{emoji}")
                for variant in (("a", "b") if word else ("a", "b", "absent")):
                    surface = block["planned_word_alternatives"][variant] if word else "" if variant == "absent" else block[f"emoji_{variant}"]
                    prefix = "carrier" if word else "emoji"
                    for candidate in ("a", "b"):
                        tokens = [20, 21] if candidate == "a" else [22, 23]
                        prompt = [10, 11] if not word else [10, 11, 12]
                        cell = {"cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                                "block_id": block["block_id"], "family": block["family"], "eta": eta,
                                "context": context, "variant": variant, "candidate": candidate,
                                "prompt": template.replace("{emoji}", surface), "continuation": block[f"candidate_{candidate}"],
                                f"{prefix}_surface": surface, f"{prefix}_char_start": begin,
                                f"{prefix}_char_end": begin + len(surface), "status": "ready",
                                "prompt_token_ids": prompt, "candidate_token_ids": tokens, "input_token_ids": prompt + tokens,
                                "prompt_token_count": len(prompt), "candidate_token_count": 2,
                                "first_candidate_predictor_position": len(prompt) - 1,
                                "candidate_token_strings": [" token", "."],
                                f"{prefix}_token_positions": [len(prompt) - 1] if surface else [],
                                f"{prefix}_token_count": 1 if surface else 0,
                                f"{prefix}_token_offsets": [[begin, begin + len(surface)]] if surface else [],
                                f"{prefix}_tokens_cross_span_boundary": False}
                        if word:
                            cell["carrier_kind"] = "word"
                        cells.append(cell)
    n = 192 if word else 288
    protocol = mod.WORD_PROTOCOL if word else mod.EMOJI_PROTOCOL
    cfg = {"protocol_id": protocol,
           "inputs": {"sha256": "1" * 64, "expected_blocks": 24, "expected_families": 6, "expected_blocks_per_family": 4},
           "model": {"artifact_manifest_sha256": mod.MODEL_SHA, "download": False, "local_files_only": True, "dtype": "bf16"},
           "scoring": {"add_special_tokens": False, "include_eos": False, "normalization": "none", "boundary": "joint_tokenization_exact_prefix", "J": 1},
           "budget": {"max_sequences": n, "max_input_tokens": 512, "max_candidate_tokens": 64}}
    return {"schema_version": 1, "protocol_id": protocol, "status": "development_preflight_zero_model_forwards",
            "claim_ceiling": mod.CLAIM, "confirmatory": False, "model_forwards": 0, "generation_calls": 0,
            "route_instrumented": False, "intervention_executed": False, "config": cfg,
            "source": {"files": {"inputs": {"sha256": "1" * 64}, "baseline_helpers": {"sha256": mod.BASELINE_RUNNER_SHA}}},
            "model_artifact": {"manifest_sha256": mod.MODEL_SHA},
            "runtime_packages": {"torch": "synthetic-not-a-model"}, "python_version": "synthetic",
            "tokenizer_class": "synthetic", "tokenizer_vocab_size": 32, "blocks": blocks, "cells": cells,
            "denominator": {"planned_blocks": 24, "planned_cells": n, "preflight_counts": {"ready": n}}}


def make_rows(spec, scale=1, poor=False, tie=False, missing=None):
    result = []
    for index, planned in enumerate(spec["cells"]):
        row = deepcopy(planned)
        if missing is not None and index in missing:
            row.update(status="not_run", reason="synthetic_missing")
        else:
            diagonal = (row["context"], row["variant"]) in (("p", "a"), ("q", "b"))
            s = 0 if row["variant"] == "absent" else row["eta"] * (2 if diagonal else -2) * scale
            if poor:
                s += 10
            if tie:
                s = 0
            total = -20 + s / 2 if row["candidate"] == "a" else -20 - s / 2
            row.update(status="completed", candidate_token_logprobs=[total / 2, total / 2], sequence_logprob_sum=total)
        result.append(row)
    return result


def write_run(root, spec, rows):
    root.mkdir()
    specification = root / "specification.json"
    dump(specification, spec)
    word = spec["protocol_id"] == mod.WORD_PROTOCOL
    n = len(rows)
    started = {"protocol_id": spec["protocol_id"], "schema_version": 1, "status": "started",
               "specification_sha256": mod.digest(specification), "local_specification_sha256": mod.digest(specification),
               "planned_cells": n, "planned_blocks": 24, "planned_cell_ids": [r["cell_id"] for r in rows],
               "model_artifact": spec["model_artifact"], "source": spec["source"], "claim_ceiling": mod.CLAIM,
               "confirmatory": False, "route_instrumented": False, "intervention_executed": False, "generation_calls": 0}
    if word:
        started["comparators"] = spec["comparators"]
    else:
        started["explicit_smoke_cell_limit"] = None
    dump(root / "run_started.json", started)
    records(root / "cells.jsonl", rows)
    # Synthetic fixtures use mathematical truth cases, never model results.
    math_result = mod.reconstruct(spec, rows, word)
    summary = {"denominator": math_result["denominator"], "blocks": math_result["blocks"],
               "planned_population_equal_family_mean_H": math_result["planned_population_equal_family_mean_H"],
               "positive_H_count": math_result["positive_H_blocks"],
               "intended_delta_crossover_count": math_result["directional_crossover_blocks"],
               "absolute_author_aligned_count": math_result["absolute_author_alignment"]["aligned_inputs"],
               "all_four_author_aligned_block_count": math_result["absolute_author_alignment"]["all_four_aligned_blocks"]}
    summary["family_denominators"] = {name: {"planned_blocks": 4, "completed_blocks": row["completed_blocks"],
                                           "incomplete_blocks": 4 - row["completed_blocks"],
                                           "full_family_mean_H": row["full_family_mean_H"]}
                                     for name, row in math_result["families"].items()}
    if word:
        for name, row in math_result["families"].items():
            summary["family_denominators"][name].update(positive_H_count=row["positive_H_blocks"],
                                                       intended_delta_crossover_count=row["directional_crossover_blocks"])
    dump(root / "summary.json", summary)
    runtime = {"packages": spec["runtime_packages"], "synthetic": True}
    dump(root / "runtime.json", runtime)
    finished = {**started, "status": "completed" if math_result["complete_population"] else "partial_or_failed",
                "denominator": math_result["denominator"], "semantic_claim_supported": False,
                "progress": {"forward_calls_attempted": math_result["forward_calls_attempted_recomputed"]},
                "cells_sha256": mod.digest(root / "cells.jsonl"), "summary_sha256": mod.digest(root / "summary.json")}
    if word:
        occupancy = {"policy": "fail_closed_other_compute_pid_before_each_forward",
                     "successful_checks": [{"other_compute_pids": []}]}
        dump(root / "occupancy_checks.json", occupancy)
        finished["occupancy_checks_sha256"] = mod.digest(root / "occupancy_checks.json")
    dump(root / "run_completed.json", finished)
    return specification


class IndependentWordComparisonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def fixture(self, poor=False, missing=None):
        emoji = make_spec(False)
        emoji_path = write_run(self.root / "emoji", emoji, make_rows(emoji))
        word = make_spec(True)
        comparators = {"baseline_specification": {"sha256": mod.digest(emoji_path)},
                       "baseline_cells": {"sha256": mod.digest(emoji_path.parent / "cells.jsonl")},
                       "baseline_runner": {"sha256": mod.BASELINE_RUNNER_SHA},
                       "baseline_runtime": {"sha256": mod.digest(emoji_path.parent / "runtime.json")}}
        word["comparators"] = comparators
        word["config"]["comparators"] = comparators
        word_path = write_run(self.root / "word", word, make_rows(word, scale=2, poor=poor, missing=missing))
        return word_path, emoji_path

    def compare_fixture(self, word, emoji):
        with patch.object(mod, "EMOJI_SPEC_SHA", mod.digest(emoji)), patch.object(mod, "EMOJI_CELLS_SHA", mod.digest(emoji.parent / "cells.jsonl")), patch.object(mod, "BASELINE_RUNTIME_SHA", mod.digest(emoji.parent / "runtime.json")):
            return mod.compare(word.parent, word, emoji.parent)

    def test_complete_expected_mathematical_result(self):
        word, emoji = self.fixture()
        out = self.compare_fixture(word, emoji)
        self.assertEqual(out["word"]["planned_population_equal_family_mean_H"], 16)
        self.assertEqual(out["emoji"]["planned_population_equal_family_mean_H"], 8)
        self.assertEqual(out["paired"]["full_population_equal_family_mean_H_word_minus_emoji"], 8)
        self.assertEqual(out["word"]["absolute_author_alignment"]["aligned_inputs"], 96)
        self.assertEqual(out["word"]["absolute_author_alignment"]["all_four_aligned_blocks"], 24)
        self.assertEqual(out["paired"]["absolute_alignment_transitions"], {"aligned->aligned": 96})
        self.assertEqual(out["paired"]["token_geometry"]["carrier_position_mismatches"], 96)
        self.assertEqual(out["paired"]["token_geometry"]["exclusions_based_on_geometry"], 0)
        self.assertEqual(out["paired"]["within_word_token_geometry"]["planned_context_pairs"], 48)
        self.assertEqual(out["paired"]["within_word_token_geometry"]["carrier_position_mismatches"], 0)
        self.assertEqual(out["paired"]["completed_paired_blocks"], 24)
        self.assertFalse(out["summary_numerics_used"])

    def test_positive_H_can_have_poor_absolute_alignment(self):
        word, emoji = self.fixture(poor=True)
        out = self.compare_fixture(word, emoji)
        self.assertEqual(out["word"]["positive_H_blocks"], 24)
        self.assertEqual(out["word"]["directional_crossover_blocks"], 24)
        self.assertEqual(out["word"]["absolute_author_alignment"]["aligned_inputs"], 48)
        self.assertEqual(out["word"]["absolute_author_alignment"]["all_four_aligned_blocks"], 0)
        self.assertEqual(out["paired"]["absolute_alignment_transitions"], {"aligned->aligned": 48, "aligned->misaligned": 48})

    def test_missing_cells_keep_population_null_and_available_counts(self):
        word, emoji = self.fixture(missing={0})
        out = self.compare_fixture(word, emoji)
        self.assertEqual(out["word"]["denominator"]["cell_status_counts"], {"not_run": 1, "completed": 191})
        self.assertEqual(out["word"]["denominator"]["planned_cells"], 192)
        self.assertEqual(out["word"]["absolute_author_alignment"]["completed_inputs"], 95)
        self.assertIsNone(out["word"]["planned_population_equal_family_mean_H"])
        self.assertIsNone(out["paired"]["full_population_equal_family_mean_H_word_minus_emoji"])
        self.assertIsNone(out["paired"]["full_population_mean_author_oriented_margin_change"])
        self.assertIsNone(out["word"]["families"]["f0"]["full_family_mean_H"])
        self.assertEqual(out["paired"]["completed_paired_blocks"], 23)

    def test_ties_are_not_aligned(self):
        spec = make_spec(True)
        result = mod.reconstruct(spec, make_rows(spec, tie=True), True)
        self.assertEqual(result["absolute_author_alignment"]["tied_inputs"], 96)
        self.assertEqual(result["absolute_author_alignment"]["aligned_inputs"], 0)
        self.assertEqual(result["positive_H_blocks"], 0)

    def test_missing_record_is_not_silent_missingness(self):
        spec = make_spec(True)
        with self.assertRaisesRegex(ValueError, "Missing acquisition records"):
            mod.reconstruct(spec, make_rows(spec)[:-1], True)

    def test_modified_input_and_orientation_rejected(self):
        for field in ("prompt", "continuation", "eta"):
            spec = make_spec(True)
            spec["cells"][0][field] = "changed"
            with self.subTest(field=field), self.assertRaises(ValueError):
                mod.check_spec(spec, True)

    def test_changed_candidate_even_consistently_rejected_in_pairing(self):
        word, emoji = make_spec(True), make_spec(False)
        word["blocks"][0]["candidate_a"] = " changed candidate"
        wr, er = mod.reconstruct(word, make_rows(word), True), mod.reconstruct(emoji, make_rows(emoji), False)
        with self.assertRaisesRegex(ValueError, "blocks/candidates/orientation"):
            mod.paired_comparison(word, wr, emoji, er)

    def test_candidate_token_change_rejected(self):
        word, emoji = make_spec(True), make_spec(False)
        word["cells"][0]["candidate_token_ids"] = [3, 4]
        wr, er = mod.reconstruct(word, make_rows(word), True), mod.reconstruct(emoji, make_rows(emoji), False)
        with self.assertRaisesRegex(ValueError, "Candidate token identity changed"):
            mod.paired_comparison(word, wr, emoji, er)

    def test_reject_hash_failure(self):
        word, emoji = self.fixture()
        with (word.parent / "cells.jsonl").open("a") as handle:
            handle.write("\n")
        with self.assertRaisesRegex(ValueError, "cell hash"):
            self.compare_fixture(word, emoji)

    def test_reject_runtime_mismatch(self):
        word, emoji = self.fixture()
        dump(word.parent / "runtime.json", {"different": True})
        with self.assertRaisesRegex(ValueError, "Runtime parity failure"):
            self.compare_fixture(word, emoji)

    def test_reject_summary_after_reconstruction(self):
        word, emoji = self.fixture()
        summary = mod.read_object(word.parent / "summary.json")
        summary["blocks"][0]["H"] = 500
        dump(word.parent / "summary.json", summary)
        final = mod.read_object(word.parent / "run_completed.json")
        final["summary_sha256"] = mod.digest(word.parent / "summary.json")
        dump(word.parent / "run_completed.json", final)
        with self.assertRaisesRegex(ValueError, "Numerical mismatch"):
            self.compare_fixture(word, emoji)

    def test_invalid_probability_and_changed_sum_rejected(self):
        spec = make_spec(True)
        for mode in ("positive", "nan", "sum", "bool"):
            rows = make_rows(spec)
            if mode == "sum":
                rows[0]["sequence_logprob_sum"] += 1
            else:
                rows[0]["candidate_token_logprobs"][0] = {"positive": 1, "nan": float("nan"), "bool": True}[mode]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                mod.reconstruct(spec, rows, True)

    def test_duplicate_json_key_and_protected_paths(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            mod.decode('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "Protected"):
            mod.safe(Path("p2_confirmatory_targets_v1.jsonl"))


if __name__ == "__main__":
    unittest.main()
