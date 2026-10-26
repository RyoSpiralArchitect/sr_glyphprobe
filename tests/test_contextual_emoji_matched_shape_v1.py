"""CPU/stdlib synthetic orchestration checks; no model/tokenizer/GPU/network."""
from copy import deepcopy
import hashlib
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("matched_shape", ROOT / "scripts/contextual_emoji_matched_shape_v1.py")
matched = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(matched)


def raw(candidate, block, context, cue, pair="original", carrier="emoji"):
    index = int(block.split("_")[1])
    prompt = [1, 2, 3 + index]
    ids = [101, 102, 103] if candidate == "a" else [101, 102, 104, 105]
    values = [-1.0, -2.0, -3.0] if candidate == "a" else [-1.0, -2.0, -4.0, -5.0]
    cell = f"{block}:{context}:{cue}:{candidate}"
    if pair != "original":
        cell = f"{pair}:{carrier}:{cell}"
    return {"status": "completed", "prompt": "synthetic prompt", "prompt_token_ids": prompt,
        "candidate_token_ids": ids, "input_token_ids": prompt + ids, "prompt_token_count": len(prompt),
        "candidate_token_count": len(ids), "first_candidate_predictor_position": len(prompt) - 1,
        "candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values),
        "pair_id": pair, "carrier_kind": carrier, "block_id": block, "context": context,
        "variant": cue, "candidate": candidate, "cell_id": cell, "eta": 1,
        "family": f"family_{index % 6}"}


def historical():
    emoji, word, additional = [], [], []
    for index in range(24):
        block = f"block_{index:02d}"
        for context in ("p", "q"):
            for cue in ("a", "b", "absent"):
                for candidate in ("a", "b"):
                    emoji.append(raw(candidate, block, context, cue))
                    if cue != "absent":
                        word.append(raw(candidate, block, context, cue, carrier="word"))
                        for pair in ("explicit_negation", "adjective_pair"):
                            for carrier in ("emoji", "word"):
                                additional.append(raw(candidate, block, context, cue, pair, carrier))
    return emoji, word, additional


def score(case, event):
    candidate = "b" if event["method"] in ("original_b_1", "padded_b") else "a"
    values = case["candidates"][candidate]["candidate_token_logprobs"]
    geometry = event["geometry"]
    return {"candidate_token_logprobs": list(values), "sequence_logprob_sum": math.fsum(values),
        "shared_prediction_logits_sha256": hashlib.sha256(b"synthetic shared prefix logits").hexdigest(),
        "shared_prediction_logits_shape": [2, 128256], "shared_prediction_logits_dtype": "float32",
        "logits_hash_byte_order": "little", "normalization_rectangle_shape": [
            geometry["normalization_stop"] - geometry["normalization_start"], 128256], "elapsed_seconds": 0.0}


def specification():
    cases = matched.inventory(*historical())
    sentinels = []
    for case in cases[:8]:
        expected = {method: score(case, {"method": method, "geometry": matched.prefix.call_geometry(case, method)})
            for method in matched.SENTINEL_METHODS}
        sentinels.append({**case, "expected_scores": expected})
    return {"inputs": cases, "sentinels": sentinels}


def execute(spec, scorer=score, before=None, after=None, deadline=None, initial_error=None):
    return matched.execute(spec, scorer, before or (lambda event: None), after or (lambda event: None),
        lambda row: None, deadline or (lambda: None), initial_error)


class InventoryTests(unittest.TestCase):
    def test_exact_real_pinned_inventory_and_prior_panel(self):
        spec = matched.design(ROOT)
        self.assertEqual((len(spec["inputs"]), len(spec["sentinels"])), (624, 8))
        self.assertEqual(spec["planned_forward_attempts"], 1312)
        self.assertEqual(spec["new_scientific_n"], 0)
        self.assertEqual(spec["prepare_model_forwards"], 0)
        self.assertEqual(spec["tokenizer_calls"], 0)
        self.assertEqual(spec["compute_policy"]["walltime_seconds"], 900)
        self.assertEqual(spec["compute_policy"]["maximum_forward_attempts"], 1312)
        self.assertEqual(sum(c["identity"][1] == "shared_absent" for c in spec["inputs"]), 48)
        old = matched.rows(ROOT / spec["source_files"]["emoji_cells"]["path"])
        absent = {r["cell_id"]: r for r in old if r["variant"] == "absent"}
        retained = {r["cell_id"]: r for c in spec["inputs"] if c["identity"][1] == "shared_absent"
            for r in c["candidates"].values()}
        self.assertEqual(retained, absent)

    def test_inventory_order_independent_and_complete(self):
        sources = historical()
        a = matched.inventory(*sources)
        b = matched.inventory(*(list(reversed(rows)) for rows in sources))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 624)
        keys = [tuple(r["unique_source_key"]) for c in a for r in c["historical_sources"].values()]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 1248)

    def test_duplicate_missing_and_invalid_absent_rejected(self):
        sources = historical()
        duplicate = deepcopy(sources); duplicate[0].append(duplicate[0][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            matched.inventory(*duplicate)
        missing = deepcopy(sources); missing[0].pop()
        with self.assertRaisesRegex(ValueError, "1248"):
            matched.inventory(*missing)
        bad = deepcopy(sources); bad[1][0]["variant"] = "absent"
        with self.assertRaisesRegex(ValueError, "absent"):
            matched.inventory(*bad)

    def test_prompt_direction_prefix_and_source_key_errors_rejected(self):
        for change in ("prompt", "eta", "prefix", "cell_id"):
            sources = historical()
            row = sources[0][0]
            if change == "prompt":
                row["prompt"] = "different"
            elif change == "eta":
                row["eta"] = -1
            elif change == "prefix":
                row["candidate_token_ids"][0] = 99
                row["input_token_ids"][row["prompt_token_count"]] = 99
            else:
                row["cell_id"] = sources[0][1]["cell_id"]
            with self.subTest(change=change), self.assertRaises(ValueError):
                matched.inventory(*sources)

    def test_source_and_spec_overwrite_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "validation") as directory:
            path = Path(directory) / "specification.json"
            spec = matched.prepare(ROOT, path)
            self.assertEqual(spec, matched.verify_specification(path))
            with self.assertRaisesRegex(ValueError, "overwrite"):
                matched.prepare(ROOT, path)
        with patch.object(matched.prefix, "bound_file", side_effect=ValueError("pin changed")):
            with self.assertRaisesRegex(ValueError, "pin changed"):
                matched.design(ROOT)

    def test_specification_drift_stops_before_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "specification.json"
            matched.write(path, {"created_at_utc": "test", "invalid": True})
            with patch.object(matched, "design", return_value={"valid": True}), \
                    patch.object(matched.prefix, "load_model") as load, \
                    self.assertRaisesRegex(ValueError, "Specification changed"):
                matched.run(path, Path(directory) / "run")
            load.assert_not_called()


class ScheduleAndExecutionTests(unittest.TestCase):
    def setUp(self):
        self.spec = specification()

    def test_schedule_exact_counts_order_and_common_shape(self):
        events = matched.plans(self.spec)
        self.assertEqual(len(events), 1312)
        self.assertEqual([r["phase"] for r in events], ["begin"] * 32 + ["scientific"] * 1248 + ["end"] * 32)
        for i in range(32, 1280, 2):
            a, b = events[i:i+2]
            self.assertEqual(a["geometry"]["total_length"], b["geometry"]["total_length"])
            self.assertEqual(a["geometry"]["normalization_stop"], b["geometry"]["normalization_stop"])
            self.assertEqual(a["geometry"]["position_ids"], b["geometry"]["position_ids"])
            self.assertEqual(a["geometry"]["attention_mask"][-1], 0)
            self.assertEqual(b["geometry"]["attention_mask"][-1], 1)
            self.assertEqual(len(a["geometry"]["candidate_token_ids"]), 3)
        self.assertNotIn("prefix_only", {r["method"] for r in events})

    def test_completed_gate_and_all_boundaries(self):
        boundaries = []
        records, attempts, error = execute(self.spec,
            before=lambda e: boundaries.append((e["event_id"], "before")),
            after=lambda e: boundaries.append((e["event_id"], "after")))
        analysis = matched.evaluate(self.spec, records)
        self.assertEqual(attempts, 1312)
        self.assertIsNone(error)
        self.assertEqual(len(boundaries), 2624)
        self.assertTrue(analysis["numerical_gate_passed"])
        self.assertEqual(analysis["matching_scientific_prefixes"], 624)
        self.assertEqual(analysis["completed_scientific_scores"], 1248)

    def test_scientific_prefix_failure_collects_full_bounded_inventory(self):
        sentinel_ids = {c["input_id"] for c in self.spec["sentinels"]}
        def changed(case, event):
            result = score(case, event)
            if event["phase"] == "scientific" and event["method"] == "padded_b" and event["input_id"] not in sentinel_ids:
                result["candidate_token_logprobs"][0] -= 0.125
                result["sequence_logprob_sum"] = math.fsum(result["candidate_token_logprobs"])
            return result
        records, attempts, error = execute(self.spec, changed)
        self.assertEqual(attempts, 1312)
        self.assertIsNone(error)
        analysis = matched.evaluate(self.spec, records)
        self.assertFalse(analysis["all624_prefixes_exact"])
        self.assertTrue(analysis["sentinel_exact_parity"])
        self.assertFalse(analysis["numerical_gate_passed"])

    def test_scientific_logit_hash_failure_detected_even_equal_probabilities(self):
        sentinel_ids = {c["input_id"] for c in self.spec["sentinels"]}
        def changed(case, event):
            result = score(case, event)
            if event["phase"] == "scientific" and event["method"] == "padded_b" and event["input_id"] not in sentinel_ids:
                result["shared_prediction_logits_sha256"] = "0" * 64
            return result
        records, _, _ = execute(self.spec, changed)
        analysis = matched.evaluate(self.spec, records)
        self.assertEqual(analysis["matching_scientific_prefixes"], 8)
        self.assertFalse(analysis["numerical_gate_passed"])

    def test_scientific_sentinel_failure_stops_without_extra_calls(self):
        def changed(case, event):
            result = score(case, event)
            if event["phase"] == "scientific":
                result["candidate_token_logprobs"][-1] -= 0.25
                result["sequence_logprob_sum"] = math.fsum(result["candidate_token_logprobs"])
            return result
        records, attempts, error = execute(self.spec, changed)
        self.assertEqual(attempts, 33)
        self.assertIn("Scientific sentinel exact", error)
        analysis = matched.evaluate(self.spec, records)
        self.assertFalse(analysis["all_sentinel_scientific_repeats_exact"])
        self.assertFalse(analysis["numerical_gate_passed"])

    def test_begin_sentinel_failure_stops_and_guards_after(self):
        after = []
        def changed(case, event):
            result = score(case, event)
            result["shared_prediction_logits_sha256"] = "0" * 64
            return result
        records, attempts, error = execute(self.spec, changed, after=lambda e: after.append(e["event_id"]))
        self.assertEqual(attempts, 1)
        self.assertEqual(len(after), 1)
        self.assertEqual(len(records), 1312)
        self.assertEqual(sum(r["status"] == "not_run" for r in records), 1311)
        self.assertIn("Sentinel exact", error)
        self.assertFalse(matched.evaluate(self.spec, records)["numerical_gate_passed"])

    def test_last_sentinel_failure_invalidates_all_scientific_scores(self):
        final = matched.plans(self.spec)[-1]["event_id"]
        def changed(case, event):
            result = score(case, event)
            if event["event_id"] == final:
                result["shared_prediction_logits_sha256"] = "0" * 64
            return result
        records, attempts, error = execute(self.spec, changed)
        analysis = matched.evaluate(self.spec, records)
        self.assertEqual(attempts, 1312)
        self.assertIsNotNone(error)
        self.assertEqual(analysis["completed_scientific_scores"], 1248)
        self.assertFalse(analysis["numerical_gate_passed"])

    def test_final_boundary_failure_does_not_pass_complete_numeric_scores(self):
        final = matched.plans(self.spec)[-1]["event_id"]
        def after(event):
            if event["event_id"] == final:
                raise ValueError("peer appeared")
        records, attempts, error = execute(self.spec, after=after)
        analysis = matched.evaluate(self.spec, records)
        self.assertEqual(attempts, 1312)
        self.assertTrue(analysis["all1312_scores_completed"])
        self.assertTrue(analysis["sentinel_exact_parity"])
        self.assertFalse(analysis["all_scored_boundaries_admissible"])
        self.assertFalse(analysis["numerical_gate_passed"])
        self.assertIn("peer appeared", error)

    def test_admission_failure_and_initial_error_preserve_unknowns(self):
        def blocked(event):
            raise ValueError("occupied")
        for initial in (None, "load failed"):
            records, attempts, error = execute(self.spec, before=blocked, initial_error=initial)
            self.assertEqual(attempts, 0)
            self.assertEqual(len(records), 1312)
            self.assertTrue(all(r["status"] == "not_run" for r in records))
            result = matched.evaluate(self.spec, records)
            self.assertFalse(result["numerical_gate_passed"])
            self.assertTrue(all(r["s_matched_shape"] is None for r in result["input_comparisons"]))

    def test_failed_score_still_has_post_guard_and_no_scored_values(self):
        after = []
        def failed(case, event):
            raise RuntimeError("synthetic scorer failure")
        records, attempts, error = execute(self.spec, failed, after=lambda e: after.append(e["event_id"]))
        self.assertEqual(attempts, 1)
        self.assertEqual(len(after), 1)
        self.assertEqual(records[0]["status"], "failed")
        self.assertNotIn("sequence_logprob_sum", records[0])
        self.assertFalse(matched.evaluate(self.spec, records)["numerical_gate_passed"])

    def test_nonfinite_or_wrong_geometry_stops(self):
        for kind in ("nan", "vocabulary", "hash", "sum"):
            def bad(case, event):
                result = score(case, event)
                if kind == "nan":
                    result["candidate_token_logprobs"][0] = math.nan
                elif kind == "vocabulary":
                    result["normalization_rectangle_shape"][1] = 64
                elif kind == "hash":
                    result["shared_prediction_logits_sha256"] = "z" * 64
                else:
                    result["sequence_logprob_sum"] -= 1
                return result
            records, attempts, error = execute(self.spec, bad)
            with self.subTest(kind=kind):
                self.assertEqual(attempts, 1)
                self.assertEqual(records[0]["status"], "failed")
                self.assertFalse(matched.evaluate(self.spec, records)["numerical_gate_passed"])

    def test_deadline_stops_without_forward(self):
        def expired():
            raise TimeoutError("budget exhausted")
        records, attempts, error = execute(self.spec, deadline=expired)
        self.assertEqual(attempts, 0)
        self.assertIn("budget exhausted", error)
        self.assertEqual(len(records), 1312)

    def test_tampered_event_order_or_geometry_rejected(self):
        records, _, _ = execute(self.spec)
        bad = deepcopy(records); bad[0], bad[1] = bad[1], bad[0]
        with self.assertRaisesRegex(ValueError, "identity/order/geometry"):
            matched.evaluate(self.spec, bad)
        bad = deepcopy(records); bad[100]["geometry"]["normalization_stop"] -= 1
        with self.assertRaisesRegex(ValueError, "identity/order/geometry"):
            matched.evaluate(self.spec, bad)


if __name__ == "__main__":
    unittest.main()
