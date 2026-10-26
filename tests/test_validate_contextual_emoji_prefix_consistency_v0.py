"""Synthetic-only independent receipt-checker tests; no model or runner import."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prefix_checker", ROOT / "scripts/validate_contextual_emoji_prefix_consistency_v0.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def dump_rows(path, values):
    path.write_text("".join(json.dumps(v, sort_keys=True, allow_nan=False) + "\n" for v in values), encoding="utf-8")


def resource(event=None, boundary="preload", blocked=False):
    return {"observed_at_utc": "2026-10-07T00:00:00+00:00", "own_pid": 123,
        "phase": "forward_boundary" if event else "before_load", "event_id": event, "boundary": boundary,
        "status": "blocked" if blocked else "allowed", "total_mib": 24000, "free_mib": 16000,
        "minimum_free_mib": 4096 if event else 12288, "own_process_mib": 7000,
        "observed_peer_pids": [], "process_memory_mib": {"123": 7000},
        **({"error": "Synthetic stop"} if blocked else {})}


def fixture(root, completed_count=56, runtime_present=True):
    run = root / "run"
    run.mkdir()
    runtime = {"python": "synthetic", "model_config": {"id2label": {"0": "label"}}, "dtype": "bfloat16"}
    cases = []
    for i in range(8):
        pair, carrier = ("original", "emoji") if i < 3 else ("original", "word") if i < 6 else ("adjective_pair", "emoji")
        identity = [pair, carrier, f"family_{i}", "p", "a"]
        candidates = {}
        for candidate, ids, probs in (("a", [7, 8], [-1., -2.]), ("b", [7, 9, 10], [-1.25, -2., -1.])):
            candidates[candidate] = {"status": "completed", "prompt_token_ids": [1, 2],
                "candidate_token_ids": ids, "input_token_ids": [1, 2] + ids,
                "prompt_token_count": 2, "candidate_token_count": len(ids),
                "first_candidate_predictor_position": 1, "candidate_token_logprobs": probs,
                "sequence_logprob_sum": math.fsum(probs), "block_id": identity[2], "context": "p",
                "variant": "a", "candidate": candidate, "pair_id": pair, "carrier_kind": carrier}
        cases.append({"input_id": "/".join(identity), "identity": identity, "selection_reason": "synthetic_test",
            "historical_prefix_residual": .25, "shared_prefix_token_count": 1,
            "shared_prefix_token_ids": [7], "candidates": candidates})
    raw_sources = {"emoji_cells": [], "word_cells": [], "cells.jsonl": []}
    for case in cases:
        key = "cells.jsonl" if case["identity"][0] != "original" else case["identity"][1] + "_cells"
        raw_sources[key].extend(case["candidates"].values())
    source_files = {}
    for name, values in raw_sources.items():
        path = root / (name.replace(".", "_") + ".jsonl")
        dump_rows(path, values)
        source_files[name] = {"path": path.name, "sha256": checker.digest(path)}
    historical_runtime = root / "historical_runtime.json"
    dump(historical_runtime, runtime)
    source_files["runtime"] = {"path": historical_runtime.name, "sha256": checker.digest(historical_runtime)}
    spec = {"protocol_id": checker.PROTOCOL, "schema_version": 1,
        "compute_policy": deepcopy(checker.POLICY), "methods": list(checker.METHODS),
        "planned_inputs": 8, "planned_forward_attempts": 56,
        "new_stimuli": 0, "new_scientific_n": 0, "tokenizer_calls": 0, "generation_calls": 0,
        "downloads": 0, "prepare_model_forwards": 0,
        "scoring": {"dtype": "bfloat16", "attention": "eager", "use_cache": False,
            "log_softmax_dtype": "float32", "historical_parity_tolerance": 0, "same_shape_prefix_tolerance": 0},
        "inputs": cases, "source_files": source_files, "historical_runtime": runtime}
    spec_path = root / "specification.json"
    dump(spec_path, spec)
    started = {"protocol_id": checker.PROTOCOL, "pid": 123, "specification_sha256": checker.digest(spec_path),
        "actual_source_files": source_files, "compute_policy": deepcopy(checker.POLICY), "planned_forward_attempts": 56}
    records, observations = [], [resource()]
    for case in cases:
        for method in checker.METHODS:
            event = f"{case['input_id']}::{method}"
            g = checker.geometry(case, method)
            row = {"event_id": event, "input_id": case["input_id"], "method": method, "geometry": g,
                "status": "not_run", "forward_attempted": False, "reason": "Synthetic stop"}
            if len(records) < completed_count:
                candidate = "b" if method.startswith(("original_b", "padded_b")) else "a"
                probs = list(case["candidates"][candidate]["candidate_token_logprobs"])
                label = "a" if candidate == "a" else "b"
                if method.startswith("padded"):
                    probs[0], label = -1., "c"
                elif method == "prefix_only":
                    probs, label = [-.875], "d"
                row.pop("reason")
                row.update(status="completed", forward_attempted=True, candidate_token_logprobs=probs,
                    sequence_logprob_sum=math.fsum(probs), shared_prediction_logits_sha256=label * 64,
                    shared_prediction_logits_shape=[1, 128256], shared_prediction_logits_dtype="float32",
                    logits_hash_byte_order="little", elapsed_seconds=.1,
                    normalization_rectangle_shape=[g["normalization_stop"] - g["normalization_start"], 128256])
                if method.startswith("original"):
                    row["historical_exact_parity"] = True
                observations.extend((resource(event, "before"), resource(event, "after")))
            elif len(records) == completed_count:
                observations.append(resource(event, "before", blocked=True))
            records.append(row)
    diagnostics, _ = checker.derive(cases, records)
    stop = None if completed_count == 56 else "Synthetic stop"
    completed = {"protocol_id": checker.PROTOCOL, "planned_forward_attempts": 56,
        "forward_attempts": completed_count, "status_counts": dict(checker.Counter(r["status"] for r in records)),
        "stop_reason": stop, "status": "completed_numerical_gate_passed" if stop is None else "stopped_partial",
        "numerical_gate_passed": diagnostics["numerical_gate_passed"],
        "elapsed_seconds": 10, "peak_torch_memory_mib": {"allocated_mib": 6500, "reserved_mib": 7000},
        "full_runtime_identity_matches_historical": runtime_present,
        "new_scientific_n": 0, "new_stimuli": 0, "block_H_recomputed": False,
        "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0}
    dump(run / "run_started.json", started)
    dump(run / "diagnostics.json", diagnostics)
    dump(run / "occupancy_checks.json", {"observations": observations, "maximum_observed_own_process_mib": 7000})
    dump_rows(run / "forwards.jsonl", records)
    if runtime_present:
        dump(run / "runtime.json", runtime)
    repin(run, completed)
    return spec_path, run, spec, records


def repin(run, completed=None):
    completed = checker.read(run / "run_completed.json") if completed is None else completed
    completed["artifacts"] = {name: checker.digest(run / name) for name in
        ("run_started.json", "forwards.jsonl", "diagnostics.json", "occupancy_checks.json", "runtime.json") if (run / name).exists()}
    dump(run / "run_completed.json", completed)


def upgrade_portable_fixture(root, spec_path, run):
    spec = checker.read(spec_path)
    tables, changes = [], []
    pairs = ("original", "explicit_negation", "adjective_pair")
    for i, pair in enumerate(pairs):
        for carrier in ("emoji", "word"):
            for block in range(24):
                tables.append({"pair_id": pair, "carrier": carrier, "block_id": str(block),
                    "t": {c: {v: i * .25 + block for v in ("a", "b")} for c in ("p", "q")}})
    for i, j in ((0, 1), (0, 2), (1, 2)):
        for carrier in ("emoji", "word"):
            for block in range(24):
                changes.append({"pair_from": pairs[i], "pair_to": pairs[j], "carrier": carrier,
                    "block_id": str(block), "mean_squared_cell_shift": ((j-i)*.25)*((j-i)*.25)})
    parent = {"decompositions": tables, "coefficient_change_rows": changes, "untouched_scientific_sentinel": {"H": 1.25}}
    parent["coefficient_change_rows"][0]["mean_squared_cell_shift"] += .125
    parent_path = root / "parent_analysis.json"
    dump(parent_path, parent)
    for key, path in (("measurement", parent_path), ("measurement_analyzer", root / "old_analyzer.py"),
                      ("runner", root / "runner.py")):
        if key != "measurement":
            path.write_text("# Pinned fixture only; never imported.\n")
        spec["source_files"][key] = {"path": path.name, "sha256": checker.digest(path)}
    replay = checker.deterministic_squared_shift(parent)
    payload = {"protocol_id": "glyphprobe-measurement-portable-squared-shift-replay-v1",
        "parent_analysis_sha256": checker.digest(parent_path),
        "parent_analyzer_sha256": checker.digest(root / "old_analyzer.py"),
        "replay_implementation_sha256": checker.digest(root / "runner.py"),
        "operation": checker.PORTABLE_OPERATION, "parent_artifact_modified": False,
        "model_probability_tolerance": 0, "all_other_fields_exactly_equal_to_parent": True,
        "changes_from_parent": checker.exact_differences(parent, replay), "analysis": replay}
    reference = root / "measurement_portable_replay.json"
    reference.write_bytes(checker.canonical_bytes(payload))
    entry = {"path": reference.name, "sha256": checker.digest(reference)}
    spec.update(schema_version=2, preflight_revision=checker.PORTABLE_REVISION, portable_measurement_reference=entry)
    spec["source_files"]["portable_measurement_reference"] = entry
    dump(spec_path, spec)
    native = deepcopy(parent)
    native["coefficient_change_rows"][1]["mean_squared_cell_shift"] += .0625
    native_receipt = {"protocol_id": "glyphprobe-measurement-native-replay-portability-diagnostic-v1",
        "parent_analysis_sha256": checker.digest(parent_path), "portable_reference_sha256": checker.digest(reference),
        "native_replay_exactly_equals_parent": False, "native_replay_differences_from_parent": checker.exact_differences(parent, native),
        "differences_confined_to_declared_auxiliary_field": True,
        "full_deterministic_replay_exactly_equals_portable_reference": True,
        "native_analysis_json_sha256": checker.hashlib.sha256(checker.canonical_bytes(native)).hexdigest(),
        "python": "synthetic", "platform": "synthetic",
        "causal_source_of_native_difference": "not_isolated; native power expression and deterministic multiplication use different operation definitions"}
    started = checker.read(run / "run_started.json")
    started.update(specification_sha256=checker.digest(spec_path), actual_source_files=spec["source_files"],
                   measurement_native_replay_portability=native_receipt)
    dump(run / "run_started.json", started)
    repin(run)
    return parent, spec, payload


class IndependentReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_full_56_numerical_gate(self):
        spec, run, _, _ = fixture(self.root)
        report = checker.analyze(spec, run, self.root)
        self.assertEqual(report["status"], "verified_bounded_numerical_gate")
        self.assertEqual(report["actual_forward_attempts"], 56)
        self.assertEqual(len(report["input_summary"]), 8)
        first = report["input_summary"][0]
        self.assertEqual(first["maximum_cross_shape_prefix_logprob_difference"], .375)
        self.assertEqual(first["original_vs_padded_scores"]["original"]["a_minus_b_logprob"], 1.25)
        self.assertEqual(first["polarity_comparison"]["score_change"], -.25)
        self.assertFalse(first["polarity_comparison"]["strict_sign_flip"])
        self.assertEqual(report["new_scientific_n"], 0)
        self.assertIsNone(report["scientific_population_verdict"])

    def test_partial_preserves_unknowns(self):
        spec, run, _, _ = fixture(self.root, completed_count=2)
        report = checker.analyze(spec, run, self.root)
        self.assertFalse(report["bounded_numerical_gate_passed"])
        self.assertEqual(report["actual_forward_attempts"], 2)
        self.assertEqual(report["completed_forward_scores"], 2)
        self.assertIsNone(report["input_summary"][0]["historical_exact_parity"])
        self.assertIsNone(report["input_summary"][1]["original_vs_padded_scores"]["original"]["preferred_candidate"])

    def test_zero_forward_missing_runtime(self):
        spec, run, _, _ = fixture(self.root, completed_count=0, runtime_present=False)
        report = checker.analyze(spec, run, self.root)
        self.assertEqual(report["actual_forward_attempts"], 0)
        self.assertIsNone(report["full_runtime_identity_matches_historical"])
        self.assertFalse(report["bounded_numerical_gate_passed"])

    def test_artifact_hash_tamper(self):
        spec, run, _, records = fixture(self.root)
        records[0]["elapsed_seconds"] = .2
        dump_rows(run / "forwards.jsonl", records)
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            checker.analyze(spec, run, self.root)

    def test_duplicates_and_geometry_tamper(self):
        spec, run, _, records = fixture(self.root)
        original = deepcopy(records)
        for mutate in (lambda r: r.__setitem__(1, deepcopy(r[0])),
                       lambda r: r[0]["geometry"]["attention_mask"].__setitem__(0, 0),
                       lambda r: r[4]["geometry"].__setitem__("position_ids", None),
                       lambda r: r[0].__setitem__("shared_prediction_logits_shape", [1, 128255])):
            records = deepcopy(original)
            mutate(records)
            dump_rows(run / "forwards.jsonl", records)
            repin(run)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                checker.analyze(spec, run, self.root)

    def test_score_tamper_even_with_rehashed_artifact(self):
        spec, run, _, records = fixture(self.root)
        records[0]["candidate_token_logprobs"][0] = -.5
        dump_rows(run / "forwards.jsonl", records)
        repin(run)
        with self.assertRaisesRegex(ValueError, "token sum"):
            checker.analyze(spec, run, self.root)

    def test_finite_and_hash_syntax(self):
        spec, run, _, records = fixture(self.root)
        records[0]["shared_prediction_logits_sha256"] = "g" * 64
        dump_rows(run / "forwards.jsonl", records)
        repin(run)
        with self.assertRaisesRegex(ValueError, "hash/type"):
            checker.analyze(spec, run, self.root)
        for value in (float("inf"), float("nan"), True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checker.probabilities([value], value, 1)

    def test_saved_diagnostics_tamper(self):
        spec, run, _, _ = fixture(self.root)
        diagnostics = checker.read(run / "diagnostics.json")
        diagnostics["input_diagnostics"][0]["historical_exact_parity"] = False
        dump(run / "diagnostics.json", diagnostics)
        repin(run)
        with self.assertRaisesRegex(ValueError, "diagnostics disagree"):
            checker.analyze(spec, run, self.root)

    def test_full_runtime_comparison_includes_nested_fields(self):
        spec, run, _, _ = fixture(self.root)
        runtime = checker.read(run / "runtime.json")
        runtime["model_config"]["id2label"]["0"] = "changed"
        dump(run / "runtime.json", runtime)
        repin(run)
        with self.assertRaisesRegex(ValueError, "Runtime summary"):
            checker.analyze(spec, run, self.root)

    def test_changed_runtime_zero_forward_is_failed_gate_not_success(self):
        spec, run, _, _ = fixture(self.root, completed_count=0)
        runtime = checker.read(run / "runtime.json")
        runtime["dtype"] = "float32"
        dump(run / "runtime.json", runtime)
        completed = checker.read(run / "run_completed.json")
        completed["full_runtime_identity_matches_historical"] = False
        repin(run, completed)
        report = checker.analyze(spec, run, self.root)
        self.assertFalse(report["full_runtime_identity_matches_historical"])
        self.assertFalse(report["bounded_numerical_gate_passed"])

    def test_peer_disallowed_and_missing_after_boundary(self):
        spec, run, _, _ = fixture(self.root)
        original = checker.read(run / "occupancy_checks.json")
        changed = deepcopy(original)
        changed["observations"][1]["process_memory_mib"]["999"] = 500
        changed["observations"][1]["observed_peer_pids"] = [999]
        dump(run / "occupancy_checks.json", changed)
        repin(run)
        with self.assertRaisesRegex(ValueError, "peer GPU"):
            checker.analyze(spec, run, self.root)
        changed = deepcopy(original)
        changed["observations"].pop(2)
        dump(run / "occupancy_checks.json", changed)
        repin(run)
        with self.assertRaisesRegex(ValueError, "after boundary"):
            checker.analyze(spec, run, self.root)

    def test_unlabelled_resource_checks_are_unknown(self):
        spec, run, _, _ = fixture(self.root)
        value = checker.read(run / "occupancy_checks.json")
        for observation in value["observations"]:
            observation.pop("event_id")
            observation.pop("boundary")
        dump(run / "occupancy_checks.json", value)
        repin(run)
        report = checker.analyze(spec, run, self.root)
        self.assertIsNone(report["resource_validation"]["per_forward_allowed_before_and_after"])
        self.assertTrue(report["numerical_gate_passed"])
        self.assertFalse(report["bounded_numerical_gate_passed"])

    def test_final_after_boundary_failure_cannot_pass(self):
        spec, run, specification, records = fixture(self.root)
        records[-1]["boundary_error_after_score"] = "Synthetic final boundary refusal"
        dump_rows(run / "forwards.jsonl", records)
        diagnostics, _ = checker.derive(specification["inputs"], records)
        dump(run / "diagnostics.json", diagnostics)
        value = checker.read(run / "occupancy_checks.json")
        value["observations"][-1]["status"] = "blocked"
        value["observations"][-1]["error"] = "Synthetic final boundary refusal"
        dump(run / "occupancy_checks.json", value)
        completed = checker.read(run / "run_completed.json")
        completed.update(status="stopped_partial", stop_reason="Synthetic final boundary refusal", numerical_gate_passed=False)
        repin(run, completed)
        report = checker.analyze(spec, run, self.root)
        self.assertEqual(report["completed_forward_scores"], 56)
        self.assertFalse(report["all_scored_boundaries_admissible"])
        self.assertFalse(report["numerical_gate_passed"])
        self.assertFalse(report["bounded_numerical_gate_passed"])

    def test_source_and_specification_pin_tamper(self):
        spec, run, specification, _ = fixture(self.root)
        specification["inputs"][0]["selection_reason"] = "changed"
        dump(spec, specification)
        with self.assertRaisesRegex(ValueError, "Start/specification"):
            checker.analyze(spec, run, self.root)

    def test_resource_order_and_allocator_cap(self):
        spec, run, _, _ = fixture(self.root)
        original = checker.read(run / "occupancy_checks.json")
        altered = deepcopy(original)
        altered["observations"][1], altered["observations"][2] = altered["observations"][2], altered["observations"][1]
        dump(run / "occupancy_checks.json", altered)
        repin(run)
        with self.assertRaisesRegex(ValueError, "out of order"):
            checker.analyze(spec, run, self.root)
        dump(run / "occupancy_checks.json", original)
        completed = checker.read(run / "run_completed.json")
        completed["peak_torch_memory_mib"]["reserved_mib"] = 9729
        repin(run, completed)
        with self.assertRaisesRegex(ValueError, "Allocator memory cap"):
            checker.analyze(spec, run, self.root)

    def test_saved_source_candidate_cannot_be_replaced_by_repinning_spec(self):
        spec, run, specification, _ = fixture(self.root)
        case = specification["inputs"][0]
        case["candidates"]["a"]["candidate_token_logprobs"][0] = -1.5
        case["candidates"]["a"]["sequence_logprob_sum"] = -3.5
        case["historical_prefix_residual"] = -.25
        dump(spec, specification)
        started = checker.read(run / "run_started.json")
        started["specification_sha256"] = checker.digest(spec)
        dump(run / "run_started.json", started)
        repin(run)
        with self.assertRaisesRegex(ValueError, "pinned raw source"):
            checker.analyze(spec, run, self.root)

    def test_negative_numerical_gate_can_be_complete(self):
        spec, run, specification, records = fixture(self.root)
        records[5]["shared_prediction_logits_sha256"] = "e" * 64
        dump_rows(run / "forwards.jsonl", records)
        diagnostics, _ = checker.derive(specification["inputs"], records)
        dump(run / "diagnostics.json", diagnostics)
        completed = checker.read(run / "run_completed.json")
        completed.update(status="completed_numerical_gate_failed", numerical_gate_passed=False)
        repin(run, completed)
        report = checker.analyze(spec, run, self.root)
        self.assertTrue(report["all_56_scores_completed"])
        self.assertFalse(report["bounded_numerical_gate_passed"])
        self.assertFalse(report["input_summary"][0]["padded_predictor_logits_exact_equality"])

    def test_ties_are_neither_strict_flip_nor_preferred(self):
        spec, run, specification, records = fixture(self.root)
        records[4]["sequence_logprob_sum"] = records[5]["sequence_logprob_sum"]
        _, compact = checker.derive(specification["inputs"], records)
        self.assertEqual(compact[0]["original_vs_padded_scores"]["padded"]["preferred_candidate"], "tie")
        self.assertTrue(compact[0]["polarity_comparison"]["any_tie"])
        self.assertFalse(compact[0]["polarity_comparison"]["strict_sign_flip"])

    def test_output_is_exclusive_and_protected_banks_refused(self):
        path = self.root / "report.json"
        checker.write_output(path, {"value": 1})
        with self.assertRaises(FileExistsError):
            checker.write_output(path, {"value": 2})
        self.assertEqual(checker.read(path), {"value": 1})
        for bank in checker.PROTECTED:
            with self.assertRaisesRegex(ValueError, "Protected"):
                checker.safe(self.root / bank)

    def test_duplicate_json_keys_and_nonfinite_json_refused(self):
        for text in ('{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.decode(text)

    def test_schema2_full_deterministic_reference_and_native_diff_receipt(self):
        spec, run, _, _ = fixture(self.root)
        parent, _, _ = upgrade_portable_fixture(self.root, spec, run)
        report = checker.analyze(spec, run, self.root)
        self.assertTrue(report["bounded_numerical_gate_passed"])
        preflight = report["measurement_preflight_validation"]
        self.assertTrue(preflight["portable_deterministic_replay_verified"])
        self.assertEqual(preflight["portable_auxiliary_fields_changed_from_parent"], 1)
        self.assertEqual(preflight["native_auxiliary_fields_changed_from_parent"], 1)
        self.assertFalse(preflight["remote_native_execution_independently_repeated"])
        self.assertEqual(checker.deterministic_squared_shift(parent)["coefficient_change_rows"][0]["mean_squared_cell_shift"], .0625)
        self.assertEqual(parent["coefficient_change_rows"][0]["mean_squared_cell_shift"], .1875)

    def test_schema2_native_hash_and_nonauxiliary_difference_tamper(self):
        spec, run, _, _ = fixture(self.root)
        upgrade_portable_fixture(self.root, spec, run)
        original = checker.read(run / "run_started.json")
        for mutate in (lambda r: r.__setitem__("native_analysis_json_sha256", "a" * 64),
                       lambda r: r["native_replay_differences_from_parent"][0].__setitem__("path", ["untouched_scientific_sentinel", "H"]),
                       lambda r: r["native_replay_differences_from_parent"][0].__setitem__("before", 999),
                       lambda r: r.__setitem__("native_replay_exactly_equals_parent", True)):
            started = deepcopy(original)
            mutate(started["measurement_native_replay_portability"])
            dump(run / "run_started.json", started)
            repin(run)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                checker.analyze(spec, run, self.root)

    def test_schema2_entire_reference_compared_even_if_repinned(self):
        spec_path, run, _, _ = fixture(self.root)
        _, spec, payload = upgrade_portable_fixture(self.root, spec_path, run)
        payload["analysis"]["untouched_scientific_sentinel"]["H"] = 999
        reference = self.root / "measurement_portable_replay.json"
        reference.write_bytes(checker.canonical_bytes(payload))
        entry = {"path": reference.name, "sha256": checker.digest(reference)}
        spec["portable_measurement_reference"] = entry
        spec["source_files"]["portable_measurement_reference"] = entry
        dump(spec_path, spec)
        started = checker.read(run / "run_started.json")
        started.update(specification_sha256=checker.digest(spec_path), actual_source_files=spec["source_files"])
        started["measurement_native_replay_portability"]["portable_reference_sha256"] = entry["sha256"]
        dump(run / "run_started.json", started)
        repin(run)
        with self.assertRaisesRegex(ValueError, "Full deterministic portable reference"):
            checker.analyze(spec_path, run, self.root)

    def test_portable_duplicate_or_nonfinite_tables_refused(self):
        spec, run, _, _ = fixture(self.root)
        parent, _, _ = upgrade_portable_fixture(self.root, spec, run)
        changed = deepcopy(parent)
        changed["coefficient_change_rows"][1] = deepcopy(changed["coefficient_change_rows"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate/invalid"):
            checker.deterministic_squared_shift(changed)
        changed = deepcopy(parent)
        changed["decompositions"][0]["t"]["p"]["a"] = True
        with self.assertRaisesRegex(ValueError, "Nonfinite portable scalar"):
            checker.deterministic_squared_shift(changed)


if __name__ == "__main__":
    unittest.main()
