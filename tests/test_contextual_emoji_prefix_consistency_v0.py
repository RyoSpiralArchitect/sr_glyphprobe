"""Synthetic/CPU-only tests; no pretrained model, tokenizer, GPU, or network."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prefix_consistency", ROOT / "scripts/contextual_emoji_prefix_consistency_v0.py")
prefix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prefix)


def record(candidate="a", equal=False, residual=0):
    prompt = [1, 2, 3]
    ids = [11, 12, 13] if candidate == "a" else [11, 12, 14] + ([] if equal else [15])
    values = [-1.0 - residual if candidate == "a" else -1.0, -2.0] + [-3.0] * (len(ids) - 2)
    return {"status": "completed", "prompt_token_ids": prompt, "candidate_token_ids": ids,
            "input_token_ids": prompt + ids, "prompt_token_count": len(prompt),
            "candidate_token_count": len(ids), "first_candidate_predictor_position": len(prompt)-1,
            "candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values)}


def fixture():
    descriptions = [("original", "emoji", "affect_01", .25, False),
                    ("explicit_negation", "emoji", "affect_03", .5, False),
                    ("adjective_pair", "emoji", "thermal_04", .75, False),
                    ("original", "emoji", "global_01", 2, False),
                    ("original", "emoji", "aa_equal", 0, True),
                    ("original", "word", "aa_equal", 0, True),
                    ("adjective_pair", "emoji", "aa_unequal", 0, False),
                    ("adjective_pair", "word", "aa_unequal", 0, False),
                    ("original", "emoji", "zzz_fill", .125, False)]
    splits, indexed = [], {}
    for pair, carrier, block, residual, equal in descriptions:
        key = pair, carrier, block, "p", "a"
        split = dict(zip(("pair_id", "carrier", "block_id", "context", "cue"), key))
        split.update(s_prefix=-residual, shared_prefix_token_count=2, shared_prefix_token_ids=[11, 12])
        splits.append(split)
        for candidate in ("a", "b"):
            indexed[(*key, candidate)] = record(candidate, equal, residual)
    return splits, indexed


def cases():
    return prefix.select_inputs(*fixture())


def score(case, event):
    method = event["method"]
    candidate = "b" if method.startswith(("original_b", "padded_b")) else "a"
    values = list(case["candidates"][candidate]["candidate_token_logprobs"])
    if method.startswith("padded"):
        values[:2] = case["candidates"]["a"]["candidate_token_logprobs"][:2]
    if method == "prefix_only":
        values = values[:2]
    return {"candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values),
        "shared_prediction_logits_sha256": hashlib.sha256(json.dumps(values[:2]).encode()).hexdigest(),
        "shared_prediction_logits_shape": [2, 64], "shared_prediction_logits_dtype": "float32",
        "elapsed_seconds": 0.0}


def xml(total=24576, free=20000, processes=()):
    entries = "".join(f"<process_info><pid>{pid}</pid><type>{kind}</type><used_memory>{used} MiB</used_memory></process_info>"
                      for pid, used, kind in processes)
    return f"<nvidia_smi_log><gpu><fb_memory_usage><total>{total} MiB</total><free>{free} MiB</free></fb_memory_usage><processes>{entries}</processes></gpu></nvidia_smi_log>"


class PreparationTests(unittest.TestCase):
    def test_exact_pinned_real_selection_without_model_or_tokenizer(self):
        expected = ["original/emoji/affect_01/p/b", "explicit_negation/emoji/affect_03/q/b",
                    "adjective_pair/emoji/thermal_04/p/b", "original/emoji/thermal_04/p/a",
                    "original/emoji/completion_02/p/a", "original/word/completion_02/p/a",
                    "adjective_pair/emoji/affect_01/p/a", "adjective_pair/word/affect_01/p/a"]
        design = prefix.design(ROOT)
        self.assertEqual([c["input_id"] for c in design["inputs"]], expected)
        self.assertEqual(design["prepare_model_forwards"], 0)
        self.assertEqual(design["tokenizer_calls"], 0)
        self.assertEqual(len(prefix.plans(design["inputs"])), 56)

    def test_synthetic_selection_deterministic_under_shuffle(self):
        splits, indexed = fixture()
        a = prefix.select_inputs(splits, indexed)
        b = prefix.select_inputs(list(reversed(splits)), dict(reversed(list(indexed.items()))))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 8)
        for case in a[4:6]:
            self.assertEqual(case["candidates"]["a"]["candidate_token_count"], case["candidates"]["b"]["candidate_token_count"])
        for case in a[6:8]:
            self.assertNotEqual(case["candidates"]["a"]["candidate_token_count"], case["candidates"]["b"]["candidate_token_count"])
        self.assertEqual({c["identity"][1] for c in a[4:6]}, {"emoji", "word"})
        self.assertEqual({c["identity"][1] for c in a[6:8]}, {"emoji", "word"})

    def test_global_maximum_deduplicates_and_fills_to_eight(self):
        splits, indexed = fixture()
        splits[0]["s_prefix"] = -4
        indexed[(*prefix.identity(splits[0]), "a")] = record("a", False, 4)
        selected = prefix.select_inputs(splits, indexed)
        self.assertEqual(len(selected), 8)
        self.assertEqual(selected[-1]["selection_reason"], "stratified_lexicographic_fill_after_deduplication")
        self.assertEqual(len({c["input_id"] for c in selected}), 8)

    def test_ties_use_lexical_identity(self):
        splits, indexed = fixture()
        extra = deepcopy(splits[0]); extra["context"] = "q"
        splits.append(extra)
        for c in ("a", "b"):
            indexed[(*prefix.identity(extra), c)] = deepcopy(indexed[(*prefix.identity(splits[0]), c)])
        self.assertEqual(prefix.select_inputs(splits, indexed)[0]["identity"][3], "p")

    def test_duplicate_missing_nonfinite_and_prefix_mismatch_refused(self):
        splits, indexed = fixture()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            prefix.select_inputs(splits + [splits[0]], indexed)
        missing = dict(indexed); missing.pop(next(iter(missing)))
        with self.assertRaisesRegex(ValueError, "Missing"):
            prefix.select_inputs(splits, missing)
        for bad in (math.nan, math.inf, True):
            altered = deepcopy(splits); altered[0]["s_prefix"] = bad
            with self.subTest(value=bad), self.assertRaises(ValueError):
                prefix.select_inputs(altered, indexed)
        altered = deepcopy(splits); altered[0]["shared_prefix_token_ids"] = [88, 99]
        with self.assertRaisesRegex(ValueError, "prefix differs"):
            prefix.select_inputs(altered, indexed)

    def test_record_boundary_and_sum_refusal(self):
        prefix.validate_record(record())
        for key, value in (("candidate_token_count", 9), ("first_candidate_predictor_position", 8),
                           ("sequence_logprob_sum", -999), ("candidate_token_logprobs", [math.nan, -1, -2])):
            row = record(); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                prefix.validate_record(row)

    def test_duplicate_raw_cell_refused(self):
        row = record(); row.update(variant="a", candidate="a", block_id="test", context="p")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            prefix.indexed_records([row, row], [], [])

    def test_json_duplicate_nonfinite_and_protected_paths_refused(self):
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError):
                prefix.decode(text)
        for name in prefix.PROTECTED:
            with self.assertRaisesRegex(ValueError, "Protected"):
                prefix.safe(Path("/tmp") / name)

    def test_bad_pin_and_path_escape_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prefix.write(root / "input.json", {"ok": True})
            with self.assertRaisesRegex(ValueError, "Pinned"):
                prefix.bound_file(root, {"path": "input.json", "sha256": "0" * 64})
            with self.assertRaisesRegex(ValueError, "relative"):
                prefix.bound_file(root, {"path": "../input.json", "sha256": "0" * 64})
            with self.assertRaisesRegex(ValueError, "Measurement analysis pin"):
                with patch.object(prefix, "digest", return_value="0" * 64):
                    prefix.design(root)

    def test_output_and_spec_overwrite_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "spec.json"
            prefix.write(destination, {"old": True})
            with self.assertRaises(FileExistsError):
                prefix.write(destination, {"new": True})
            with self.assertRaisesRegex(ValueError, "overwrite"):
                prefix.prepare(ROOT, destination)
            self.assertEqual(prefix.read(destination), {"old": True})

    def test_spec_mismatch_fails_before_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spec.json"
            reference = Path(directory) / "reference.json"
            prefix.write(reference, {"reference": True})
            prefix.write(path, {"created_at_utc": "test", "x": 1,
                "portable_measurement_reference": {"path": "reference.json", "sha256": prefix.digest(reference)}})
            with patch.object(prefix, "design", return_value={"x": 2}), self.assertRaisesRegex(ValueError, "Specification changed"):
                prefix.verify_specification(path, Path(directory))

    def test_portable_full_reference_replay_preserves_all_other_fields(self):
        parent = prefix.read(ROOT / prefix.ANALYSIS_PATH)
        portable = prefix.auxiliary_squared_shift_replay(parent)
        changes = prefix.differences(parent, portable)
        prefix.require_auxiliary_only(changes)
        self.assertEqual(len(changes), 6)
        self.assertEqual(portable["candidate_prefix_tail"], parent["candidate_prefix_tail"])
        self.assertEqual(portable["decompositions"], parent["decompositions"])
        self.assertEqual(prefix.auxiliary_squared_shift_replay(portable), portable)
        # The complete new reference is deterministic, rather than comparing
        # the historical auxiliary value approximately.
        native = deepcopy(parent)
        native["coefficient_change_rows"][0]["mean_squared_cell_shift"] = math.nextafter(
            native["coefficient_change_rows"][0]["mean_squared_cell_shift"], math.inf)
        prefix.require_auxiliary_only(prefix.differences(parent, native))
        self.assertEqual(prefix.auxiliary_squared_shift_replay(native), portable)

    def test_any_nonauxiliary_replay_change_fails_closed(self):
        parent = prefix.read(ROOT / prefix.ANALYSIS_PATH)
        native = deepcopy(parent)
        native["candidate_prefix_tail"]["input_splits"][0]["s_prefix"] += .001
        with self.assertRaisesRegex(ValueError, "outside the declared"):
            prefix.require_auxiliary_only(prefix.differences(parent, native))
        native = deepcopy(parent)
        native["coefficient_change_rows"][0]["mean_squared_cell_shift"] = math.nan
        with self.assertRaisesRegex(ValueError, "outside the declared"):
            prefix.require_auxiliary_only(prefix.differences(parent, native))

    def test_portable_payload_hash_and_native_observation_are_separate(self):
        parent, _, payload, observation = prefix.load_measurement_replay(ROOT)
        self.assertEqual(payload["parent_analysis_sha256"], prefix.ANALYSIS_SHA)
        self.assertEqual(payload["analysis"], prefix.auxiliary_squared_shift_replay(parent))
        self.assertTrue(payload["all_other_fields_exactly_equal_to_parent"])
        self.assertFalse(payload["parent_artifact_modified"])
        self.assertEqual(payload["model_probability_tolerance"], 0)
        self.assertEqual(observation["portable_reference_sha256"], hashlib.sha256(prefix.json_bytes(payload)).hexdigest())
        self.assertNotIn("python", payload)
        self.assertIn("python", observation)
        self.assertTrue(observation["full_deterministic_replay_exactly_equals_portable_reference"])

    def test_prepare_creates_reference_and_refuses_reuse(self):
        payload = {"reference": True}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); path = root / "prep/specification.json"
            def design(root, reference):
                return {"portable_measurement_reference": {"path": str(reference.relative_to(root)),
                        "sha256": prefix.digest(reference)}, "schema_version": 2}
            with patch.object(prefix, "load_measurement_replay", return_value=({}, {}, payload, {})), \
                 patch.object(prefix, "design", side_effect=design):
                prepared = prefix.prepare(root, path)
            reference = path.with_name("measurement_portable_replay.json")
            self.assertEqual(prefix.read(reference), payload)
            self.assertEqual(prepared["portable_measurement_reference"]["sha256"], prefix.digest(reference))
            with self.assertRaisesRegex(ValueError, "overwrite"):
                prefix.prepare(root, path)


class GeometryTests(unittest.TestCase):
    def test_padding_masks_positions_and_prediction_indices(self):
        case = cases()[0]
        a, b = (prefix.call_geometry(case, m) for m in ("padded_a", "padded_b"))
        self.assertEqual(a["total_length"], b["total_length"])
        self.assertEqual(a["input_token_ids"][-1], 0)
        self.assertEqual(a["attention_mask"], [1]*6 + [0])
        self.assertEqual(b["attention_mask"], [1]*7)
        self.assertEqual(a["position_ids"], b["position_ids"])
        self.assertEqual(a["predictor_positions"], [2, 3, 4])
        self.assertEqual(b["predictor_positions"], [2, 3, 4, 5])
        self.assertEqual(a["normalization_stop"], b["normalization_stop"])
        self.assertEqual(a["candidate_token_ids"], [11, 12, 13])
        original = prefix.call_geometry(case, "original_a_1")
        self.assertIsNone(original["position_ids"])
        self.assertEqual(original["input_token_ids"], case["candidates"]["a"]["input_token_ids"])
        shared = prefix.call_geometry(case, "prefix_only")
        self.assertEqual(shared["candidate_token_ids"], [11, 12])
        self.assertEqual(shared["input_token_ids"], [1, 2, 3, 11, 12])
        self.assertIsNone(shared["position_ids"])

    def test_cpu_toy_scoring_common_normalization_rectangle(self):
        try:
            import torch
        except ImportError:
            self.skipTest("CPU torch unavailable; no pretrained/GPU fallback")
        base = prefix.module(ROOT / prefix.BASE_PATH, "prefix_test_base")
        class Toy:
            def __init__(self):
                self.calls = []
            def __call__(self, **kwargs):
                self.calls.append(kwargs)
                length = kwargs["input_ids"].shape[1]
                logits = torch.arange(64, dtype=torch.bfloat16).expand(1, length, 64).clone()
                return SimpleNamespace(logits=logits)
        toy = Toy(); case = cases()[0]
        events = {e["method"]: e for e in prefix.plans(cases()) if e["input_id"] == case["input_id"]}
        rectangles = []
        original_log_softmax = torch.log_softmax
        def tracked(tensor, *args, **kwargs):
            rectangles.append((tuple(tensor.shape), tensor.dtype))
            return original_log_softmax(tensor, *args, **kwargs)
        with patch.object(torch, "log_softmax", side_effect=tracked):
            a = prefix.score_call(torch, toy, base, case, events["padded_a"], "cpu")
            b = prefix.score_call(torch, toy, base, case, events["padded_b"], "cpu")
        self.assertEqual(rectangles, [((4, 64), torch.float32)]*2)
        self.assertEqual(a["shared_prediction_logits_sha256"], b["shared_prediction_logits_sha256"])
        self.assertEqual(a["candidate_token_logprobs"][:2], b["candidate_token_logprobs"][:2])
        self.assertEqual(len(a["candidate_token_logprobs"]), 3)
        self.assertEqual(len(b["candidate_token_logprobs"]), 4)
        self.assertEqual(toy.calls[0]["attention_mask"].tolist(), [[1,1,1,1,1,1,0]])
        self.assertEqual(toy.calls[0]["position_ids"].tolist(), [list(range(7))])
        prefix.score_call(torch, toy, base, case, events["original_a_1"], "cpu")
        self.assertNotIn("position_ids", toy.calls[-1])
        self.assertFalse(toy.calls[-1]["use_cache"])


class GuardTests(unittest.TestCase):
    def test_empty_and_own_only_allowed(self):
        self.assertEqual(prefix.resource_guard(True, lambda: xml(), pid=10)["status"], "allowed")
        result = prefix.resource_guard(False, lambda: xml(free=6000, processes=[(10, 9000, "C")]), pid=10)
        self.assertEqual(result["own_process_mib"], 9000)

    def test_peer_including_graphics_refused_and_receipted(self):
        for kind in ("C", "G", "C+G"):
            observations = []
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "Other GPU PID"):
                prefix.resource_guard(False, lambda: xml(processes=[(20, 1, kind)]), observations.append, pid=10)
            self.assertEqual(observations[0]["status"], "blocked")
            self.assertEqual(observations[0]["observed_peer_pids"], [20])

    def test_free_floors_and_own_cap_are_inclusive(self):
        for before, free in ((True, 12288), (False, 4096)):
            prefix.resource_guard(before, lambda: xml(free=free), pid=10)
            with self.assertRaisesRegex(ValueError, "Free VRAM"):
                prefix.resource_guard(before, lambda: xml(free=free-1), pid=10)
        prefix.resource_guard(False, lambda: xml(processes=[(10, 10240, "C")]), pid=10)
        with self.assertRaisesRegex(ValueError, "allowance"):
            prefix.resource_guard(False, lambda: xml(processes=[(10, 10241, "C")]), pid=10)

    def test_unknown_inventory_fails_closed(self):
        for bad in ("bad xml", xml().replace("<processes></processes>", ""),
                    xml().replace("20000 MiB", "N/A"),
                    xml(processes=[(10, 5, "C"), (10, 6, "C")]),
                    "<nvidia_smi_log></nvidia_smi_log>"):
            with self.subTest(xml=bad), self.assertRaises((ValueError, prefix.ET.ParseError)):
                prefix.resource_guard(False, lambda: bad, pid=10)


class ExecutionTests(unittest.TestCase):
    def execute(self, scorer=score, before=lambda: None, after=lambda: None, deadline=lambda: None, error=None):
        emitted = []
        result = prefix.execute(cases(), scorer, lambda event: before(), lambda event: after(), emitted.append, deadline, error)
        self.assertEqual(result[0], emitted)
        self.assertEqual(len(result[0]), 56)
        return result

    def test_all56_attempted_no_extra_forward_and_exact_gates(self):
        records, attempts, error = self.execute()
        self.assertEqual(attempts, 56)
        self.assertIsNone(error)
        result = prefix.evaluate(cases(), records)
        self.assertTrue(result["numerical_gate_passed"])
        self.assertFalse(result["block_H_recomputed"])

    def test_callbacks_bind_every_event_in_order(self):
        calls = []
        records, attempts, _ = prefix.execute(cases(), score,
            lambda event: calls.append((event["event_id"], "before")),
            lambda event: calls.append((event["event_id"], "after")), lambda row: None, lambda: None)
        self.assertEqual(attempts, 56)
        self.assertEqual(calls, [(r["event_id"], boundary) for r in records for boundary in ("before", "after")])

    def test_same_shape_failure_is_final_gate_not_early_diagnostic_stop(self):
        def altered(case, event):
            value = score(case, event)
            if event["method"] == "padded_b":
                value["candidate_token_logprobs"][0] -= .01
                value["sequence_logprob_sum"] = math.fsum(value["candidate_token_logprobs"])
            return value
        records, attempts, error = self.execute(altered)
        self.assertEqual(attempts, 56)
        self.assertIsNone(error)
        self.assertFalse(prefix.evaluate(cases(), records)["numerical_gate_passed"])

    def test_logit_hash_alone_can_fail_same_shape_gate(self):
        def altered(case, event):
            value = score(case, event)
            if event["method"] == "padded_b":
                value["shared_prediction_logits_sha256"] = "0"*64
            return value
        records, attempts, _ = self.execute(altered)
        result = prefix.evaluate(cases(), records)
        self.assertEqual(attempts, 56)
        self.assertTrue(result["input_diagnostics"][0]["padded_prefix_exact_equality"])
        self.assertFalse(result["input_diagnostics"][0]["padded_predictor_logits_exact_equality"])

    def test_historical_parity_failure_stops_remaining_attempts(self):
        def altered(case, event):
            value = score(case, event)
            value["candidate_token_logprobs"][0] -= .001
            value["sequence_logprob_sum"] = math.fsum(value["candidate_token_logprobs"])
            return value
        records, attempts, error = self.execute(altered)
        self.assertEqual(attempts, 1)
        self.assertIn("parity failed", error)
        self.assertFalse(records[0]["historical_exact_parity"])
        self.assertTrue(all(r["status"] == "not_run" for r in records[1:]))

    def test_repeat_logit_change_stops_even_with_identical_scores(self):
        def altered(case, event):
            value = score(case, event)
            if event["method"].endswith("_2"):
                value["shared_prediction_logits_sha256"] = "0"*64
            return value
        records, attempts, error = self.execute(altered)
        self.assertEqual(attempts, 3)
        self.assertIn("Repeated original predictor logits", error)
        self.assertEqual(sum(r["status"] == "not_run" for r in records), 53)

    def test_resource_refusal_before_call_attempts_zero(self):
        def fail():
            raise ValueError("contention")
        records, attempts, error = self.execute(before=fail)
        self.assertEqual(attempts, 0)
        self.assertTrue(all(not r["forward_attempted"] for r in records))
        self.assertIn("contention", error)

    def test_failure_during_forward_preserves_failed_plus_notrun(self):
        def fail(case, event):
            raise RuntimeError("synthetic OOM")
        records, attempts, _ = self.execute(fail)
        self.assertEqual(attempts, 1)
        self.assertEqual(records[0]["status"], "failed")
        self.assertEqual(sum(r["status"] == "not_run" for r in records), 55)

    def test_after_forward_contention_keeps_completed_score(self):
        def fail():
            raise ValueError("new peer")
        records, attempts, _ = self.execute(after=fail)
        self.assertEqual(attempts, 1)
        self.assertEqual(records[0]["status"], "completed")
        self.assertIn("new peer", records[0]["boundary_error_after_score"])

    def test_final_after_forward_contention_fails_gate_with_all_scores(self):
        calls = []
        def fail_last():
            calls.append(1)
            if len(calls) == 56:
                raise ValueError("final new peer")
        records, attempts, error = self.execute(after=fail_last)
        result = prefix.evaluate(cases(), records)
        self.assertEqual(attempts, 56)
        self.assertIsNotNone(error)
        self.assertTrue(result["all_56_scores_completed"])
        self.assertFalse(result["all_scored_boundaries_admissible"])
        self.assertFalse(result["numerical_gate_passed"])

    def test_full_geometry_comparison_reports_sign_and_tie_changes(self):
        def altered(case, event):
            value = score(case, event)
            if event["method"] == "padded_a":
                value["candidate_token_logprobs"][-1] -= 10
                value["sequence_logprob_sum"] = math.fsum(value["candidate_token_logprobs"])
            return value
        records, attempts, _ = self.execute(altered)
        result = prefix.evaluate(cases(), records)
        self.assertEqual(attempts, 56)
        comparison = result["input_diagnostics"][0]["full_score_geometry_comparison"]
        self.assertEqual(comparison["original_preferred_candidate"], "a")
        self.assertEqual(comparison["padded_preferred_candidate"], "b")
        self.assertTrue(comparison["strict_nonzero_polarity_flip"])
        self.assertGreater(comparison["same_candidate_max_absolute_logprob_difference"]["a"], 0)

    def test_walltime_and_load_error_preserve_all56_notrun(self):
        def fail():
            raise TimeoutError("deadline")
        for kwargs in ({"deadline": fail}, {"error": "model identity failed"}):
            records, attempts, error = self.execute(**kwargs)
            self.assertEqual(attempts, 0)
            self.assertTrue(all(r["status"] == "not_run" for r in records))
            self.assertIsNotNone(error)

    def test_nonfinite_and_invalid_score_are_failed_attempts(self):
        def invalid(case, event):
            value = score(case, event); value["candidate_token_logprobs"][0] = math.nan
            return value
        records, attempts, error = self.execute(invalid)
        self.assertEqual(attempts, 1)
        self.assertEqual(records[0]["status"], "failed")
        self.assertNotIn("candidate_token_logprobs", records[0])
        self.assertIn("Invalid scored probabilities", error)

    def test_evaluate_rejects_missing_and_duplicate_rows(self):
        records, _, _ = self.execute()
        for invalid in (records[:-1], records[:55] + [records[0]]):
            with self.assertRaisesRegex(ValueError, "denominator"):
                prefix.evaluate(cases(), invalid)

    def test_run_refusal_writes_complete_notrun_receipts_without_loading(self):
        spec = {"inputs": cases(), "source_files": {}, "historical_runtime": {}}
        def occupied(before_load=False, emit=None):
            if emit:
                emit({"status": "blocked", "observed_peer_pids": [777]})
            raise ValueError("GPU occupied")
        with tempfile.TemporaryDirectory() as directory:
            spec_path = Path(directory) / "spec.json"; prefix.write(spec_path, spec)
            out = Path(directory) / "run"
            with patch.object(prefix, "verify_specification", return_value=spec), \
                 patch.object(prefix, "resource_guard", side_effect=occupied), \
                 patch.object(prefix, "load_model") as load:
                result = prefix.run(spec_path, out)
            load.assert_not_called()
            self.assertEqual(result["status"], "stopped_partial")
            self.assertEqual(result["forward_attempts"], 0)
            self.assertEqual(result["status_counts"], {"not_run": 56})
            self.assertEqual(len(prefix.rows(out / "forwards.jsonl")), 56)
            self.assertTrue((out / "run_started.json").is_file())
            self.assertTrue((out / "run_completed.json").is_file())
            self.assertFalse((out / "runtime.json").exists())
            observation = prefix.read(out / "occupancy_checks.json")["observations"][0]
            self.assertIsNone(observation["event_id"])
            self.assertEqual(observation["boundary"], "preload")
            with self.assertRaisesRegex(ValueError, "reuse"):
                prefix.run(spec_path, out)

    def test_mock_run_receipts_bind_all112_forward_boundaries(self):
        spec = {"inputs": cases(), "source_files": {}, "historical_runtime": {}}
        def allowed(before_load=False, emit=None):
            observation = {"status": "allowed", "observed_peer_pids": [], "own_process_mib": 10}
            emit(observation)
            return observation
        def load(spec, observe, runtime_emit, implementation_emit, deadline, resources):
            observe(True, boundary="before_allocation")
            observe(False, boundary="after_allocation")
            runtime_emit({}); implementation_emit({"files": {}})
            return SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: False)), None, None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spec.json"; prefix.write(path, spec)
            out = Path(directory) / "run"
            with patch.object(prefix, "verify_specification", return_value=spec), \
                 patch.object(prefix, "resource_guard", side_effect=allowed), \
                 patch.object(prefix, "load_model", side_effect=load), \
                 patch.object(prefix, "score_call", side_effect=lambda torch, model, base, case, event: score(case, event)):
                result = prefix.run(path, out)
            self.assertEqual(result["status"], "completed_numerical_gate_passed")
            observations = prefix.read(out / "occupancy_checks.json")["observations"]
            forward = [r for r in observations if r["event_id"] is not None]
            self.assertEqual(len(forward), 112)
            self.assertEqual([(r["event_id"], r["boundary"]) for r in forward],
                [(p["event_id"], b) for p in prefix.plans(cases()) for b in ("before", "after")])


if __name__ == "__main__":
    unittest.main()
