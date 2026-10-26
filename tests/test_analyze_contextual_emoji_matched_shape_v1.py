"""Synthetic acquisition receipts over existing development IDs; no model imports.

The historical fixtures remain real, immutable provenance. Every new forward
here is fabricated test data, never scientific evidence or a real acquisition.
"""
from copy import deepcopy
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("matched_shape_checker_test", ROOT / "scripts/analyze_contextual_emoji_matched_shape_v1.py")
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)
PRIOR = ROOT / "validation/contextual_emoji_prefix_consistency_v0/portable_preflight"


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def dump_rows(path, values):
    path.write_text("".join(json.dumps(v, sort_keys=True, allow_nan=False) + "\n" for v in values), encoding="utf-8")


def synthetic_spec():
    old = checker.read(PRIOR / "specification.json")
    sources = deepcopy(old["source_files"])
    sources["prefix_runner"] = sources.pop("runner")
    sources["runner"] = {"path": "scripts/contextual_emoji_matched_shape_v1.py",
                         "sha256": checker.digest(ROOT / "scripts/contextual_emoji_matched_shape_v1.py")}
    files = {"prefix_specification": PRIOR / "specification.json", "prefix_prior_independent": PRIOR / "independent_validation.json"}
    for key, filename in (("forwards", "forwards.jsonl"), ("completed", "run_completed.json"),
                          ("runtime", "runtime.json"), ("implementation", "implementation_sources.json"),
                          ("started", "run_started.json"), ("diagnostics", "diagnostics.json"), ("occupancy", "occupancy_checks.json")):
        files["prefix_prior_" + key] = PRIOR / "run56" / filename
    sources.update({key: {"path": str(path.relative_to(ROOT)), "sha256": checker.digest(path)} for key, path in files.items()})
    grouped = {}
    for name, kind in (("emoji_cells", "emoji"), ("word_cells", "word"), ("cells.jsonl", None)):
        for row in checker.rows(ROOT / sources[name]["path"]):
            pair = "original" if kind else row["pair_id"]
            carrier = "shared_absent" if row["variant"] == "absent" else kind or row["carrier_kind"]
            identity = pair, carrier, row["block_id"], row["context"], row["variant"]
            case = grouped.setdefault(identity, {"identity": list(identity), "input_id": "/".join(identity),
                                                  "candidates": {}, "historical_sources": {}})
            case["candidates"][row["candidate"]] = row
            case["historical_sources"][row["candidate"]] = {"source_file_key": name, "source_cell_id": row["cell_id"],
                                                          "unique_source_key": [name, row["cell_id"]]}
    for case in grouped.values():
        a, b = (case["candidates"][c]["candidate_token_ids"] for c in ("a", "b"))
        n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        case.update(shared_prefix_token_count=n, shared_prefix_token_ids=a[:n])
    old_rows = {(r["input_id"], r["method"]): r for r in checker.rows(PRIOR / "run56/forwards.jsonl")}
    sentinels = [{**deepcopy(c), "expected_scores": {m: old_rows[c["input_id"], m] for m in checker.METHODS}} for c in old["inputs"]]
    return {"protocol_id": checker.PROTOCOL, "schema_version": 1, "compute_policy": deepcopy(checker.POLICY),
        **checker.COUNTS, "planned_sentinel_forwards": 64, "new_scientific_n": 0, "new_stimuli": 0,
        "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0, "prepare_model_forwards": 0,
        "scoring": deepcopy(old["scoring"]), "inputs": [grouped[k] for k in sorted(grouped)], "sentinels": sentinels,
        "source_files": sources, "expected_implementation_sources": checker.read(PRIOR / "run56/implementation_sources.json"),
        **{k: old[k] for k in ("historical_runtime", "model_path", "model_artifact", "runtime_packages", "python_version")}}


def resource(event=None, boundary="preload", blocked=False):
    return {"observed_at_utc": "2026-10-10T00:00:00+00:00", "own_pid": 123,
        "phase": "forward_boundary" if event else "before_load", "event_id": event, "boundary": boundary,
        "status": "blocked" if blocked else "allowed", "total_mib": 32607, "free_mib": 16000,
        "minimum_free_mib": 4096 if event else 12288, "own_process_mib": 7000,
        "observed_peer_pids": [], "process_memory_mib": {"123": 7000},
        **({"error": "Synthetic contention"} if blocked else {})}


def recompute(run, spec, records, observations, stop=None):
    matches = [checker.core_equal(r, next(c for c in spec["sentinels"] if c["input_id"] == r["input_id"])["expected_scores"][r["method"]])
               for r in records if r["phase"] != "scientific" and r["status"] == "completed"]
    diagnostics = {**checker.derive_gates(spec["inputs"], records, matches, spec["sentinels"]),
                   **checker.derive_detailed_diagnostics(spec["inputs"], spec["sentinels"], records)}
    dump(run / "diagnostics.json", diagnostics)
    dump_rows(run / "forwards.jsonl", records)
    dump(run / "occupancy_checks.json", {"observations": observations,
         "maximum_observed_own_process_mib": max(o.get("own_process_mib", 0) for o in observations)})
    completed = {"protocol_id": checker.PROTOCOL, "planned_forward_attempts": 1312,
        "planned_scientific_sequence_scores": 1248, "planned_sentinel_forwards": 64,
        "forward_attempts": sum(r["forward_attempted"] for r in records),
        "status_counts": dict(Counter(r["status"] for r in records)), "stop_reason": stop,
        "status": "stopped_partial" if stop else "completed_numerical_gate_passed" if diagnostics["numerical_gate_passed"] else "completed_numerical_gate_failed",
        "elapsed_seconds": 10, "peak_torch_memory_mib": {"allocated_mib": 6500, "reserved_mib": 7000},
        "full_runtime_identity_matches_historical": checker.read(run / "runtime.json") == spec["historical_runtime"],
        "implementation_sources_match_prior": checker.read(run / "implementation_sources.json") == spec["expected_implementation_sources"],
        "numerical_gate_passed": diagnostics["numerical_gate_passed"],
        "new_scientific_n": 0, "new_stimuli": 0, "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0}
    repin(run, completed)


def repin(run, completed=None):
    completed = checker.read(run / "run_completed.json") if completed is None else completed
    completed["artifacts"] = {name: checker.digest(run / name) for name in
        ("run_started.json", "forwards.jsonl", "diagnostics.json", "occupancy_checks.json", "runtime.json", "implementation_sources.json")}
    dump(run / "run_completed.json", completed)


def fixture(root, count=1312):
    spec = synthetic_spec()
    spec_path, run = root / "specification.json", root / "run"
    run.mkdir()
    dump(spec_path, spec)
    dump(run / "run_started.json", {"protocol_id": checker.PROTOCOL, "pid": 123,
        "specification_sha256": checker.digest(spec_path), "actual_source_files": spec["source_files"],
        "compute_policy": spec["compute_policy"], "planned_forward_attempts": 1312})
    dump(run / "runtime.json", spec["historical_runtime"])
    dump(run / "implementation_sources.json", spec["expected_implementation_sources"])
    records, observations = [], [resource()]
    sentinels = {c["input_id"]: c for c in spec["sentinels"]}
    for phase, case, method in checker.schedule(spec["inputs"], spec["sentinels"]):
        event = f"{phase}::{case['input_id']}::{method}"
        g = checker.geometry(case, method)
        row = {"event_id": event, "phase": phase, "input_id": case["input_id"], "method": method, "geometry": g,
               "status": "not_run", "forward_attempted": False, "reason": "Synthetic partial"}
        if len(records) < count:
            candidate = "b" if method in ("original_b_1", "padded_b") else "a"
            probs = list(case["candidates"][candidate]["candidate_token_logprobs"])
            n = case["shared_prefix_token_count"]
            if phase == "scientific" and case["input_id"] not in sentinels:
                probs[:n] = case["candidates"]["a"]["candidate_token_logprobs"][:n]
                score = {"candidate_token_logprobs": probs, "sequence_logprob_sum": math.fsum(probs),
                    "shared_prediction_logits_sha256": "c" * 64, "shared_prediction_logits_shape": [n, 128256],
                    "shared_prediction_logits_dtype": "float32", "logits_hash_byte_order": "little",
                    "normalization_rectangle_shape": [g["normalization_stop"] - g["normalization_start"], 128256]}
            else:
                score = {k: deepcopy(sentinels[case["input_id"]]["expected_scores"][method][k]) for k in checker.CORE}
            row.pop("reason")
            row.update(score, status="completed", forward_attempted=True, elapsed_seconds=.001)
            if phase != "scientific":
                row["sentinel_exact_parity"] = True
                if method.startswith("original"):
                    row["historical_exact_parity"] = True
                if phase == "end":
                    row["end_begin_exact_parity"] = True
            elif case["input_id"] in sentinels:
                row["scientific_sentinel_exact_parity"] = True
            observations.extend((resource(event, "before"), resource(event, "after")))
        elif len(records) == count:
            observations.append(resource(event, "before", blocked=True))
        records.append(row)
    recompute(run, spec, records, observations, None if count == 1312 else "Synthetic partial")
    return spec_path, run, spec, records, observations


class MatchedShapeCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="glyphprobe-checker-test-")
        self.addCleanup(self.temporary.cleanup)
        self.spec_path, self.run, self.spec, self.records, self.observations = fixture(Path(self.temporary.name))

    def analyze(self):
        return checker.analyze(self.spec_path, self.run, ROOT)

    def test_complete_receipt_and_exact_denominators(self):
        result = self.analyze()
        self.assertTrue(result["bounded_numerical_gate_passed"])
        self.assertTrue(result["resource_gate_passed"])
        self.assertTrue(result["analysis"]["eligible_for_versioned_score_replacement"])
        self.assertEqual(result["analysis"]["block_table_count"], 144)
        self.assertEqual(len(result["analysis"]["input_rows"]), 624)
        self.assertEqual(len(result["analysis"]["shared_absent_diagnostics"]), 48)
        self.assertEqual(result["analysis"]["old_nonzero_prefix_residuals"]["crossed"], 355)
        self.assertFalse(result["confirmatory_evidence"])
        self.assertEqual(result["new_scientific_n"], 0)

    def test_completed_numerical_negative_is_not_eligible(self):
        row = next(r for r in self.records if r["phase"] == "scientific" and r["method"] == "padded_b" and
                   r["input_id"] not in {c["input_id"] for c in self.spec["sentinels"]})
        row["candidate_token_logprobs"][0] -= .125
        row["sequence_logprob_sum"] = math.fsum(row["candidate_token_logprobs"])
        recompute(self.run, self.spec, self.records, self.observations)
        result = self.analyze()
        self.assertFalse(result["bounded_numerical_gate_passed"])
        self.assertTrue(result["resource_gate_passed"])
        self.assertFalse(result["analysis"]["eligible_for_versioned_score_replacement"])
        self.assertEqual(result["counts"]["matching_scientific_prefixes"], 623)

    def test_partial_retains_all_planned_denominators(self):
        with tempfile.TemporaryDirectory() as folder:
            path, run, _, _, _ = fixture(Path(folder), count=40)
            result = checker.analyze(path, run, ROOT)
        self.assertFalse(result["bounded_numerical_gate_passed"])
        self.assertEqual(result["counts"]["actual_forward_attempts"], 40)
        self.assertEqual(result["analysis"]["planned_block_tables"], 144)
        self.assertIsNone(result["analysis"]["block_tables"])

    def test_run_artifact_hash_tamper(self):
        with (self.run / "forwards.jsonl").open("a") as handle:
            handle.write(" ")
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            self.analyze()

    def test_duplicate_event(self):
        self.records[33]["event_id"] = self.records[32]["event_id"]
        dump_rows(self.run / "forwards.jsonl", self.records)
        repin(self.run)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.analyze()

    def test_mask_geometry_tamper(self):
        row = next(r for r in self.records if 0 in r["geometry"]["attention_mask"])
        row["geometry"]["attention_mask"][-1] = 1
        dump_rows(self.run / "forwards.jsonl", self.records)
        repin(self.run)
        with self.assertRaisesRegex(ValueError, "geometry"):
            self.analyze()

    def test_runtime_drift_before_forward_is_rejected(self):
        runtime = checker.read(self.run / "runtime.json")
        runtime["synthetic_runtime_drift"] = True
        dump(self.run / "runtime.json", runtime)
        recompute(self.run, self.spec, self.records, self.observations)
        with self.assertRaisesRegex(ValueError, "without exact runtime"):
            self.analyze()

    def test_implementation_drift_is_rejected(self):
        implementation = checker.read(self.run / "implementation_sources.json")
        implementation["files"]["modeling_llama"]["sha256"] = "0" * 64
        dump(self.run / "implementation_sources.json", implementation)
        recompute(self.run, self.spec, self.records, self.observations)
        with self.assertRaisesRegex(ValueError, "without exact runtime/implementation"):
            self.analyze()

    def test_missing_resource_event_label_is_rejected(self):
        self.observations[1]["event_id"] = None
        recompute(self.run, self.spec, self.records, self.observations)
        with self.assertRaisesRegex(ValueError, "before boundary"):
            self.analyze()

    def test_peer_pid_in_allowed_resource_observation_is_rejected(self):
        self.observations[1]["process_memory_mib"]["456"] = 1
        self.observations[1]["observed_peer_pids"] = [456]
        recompute(self.run, self.spec, self.records, self.observations)
        with self.assertRaisesRegex(ValueError, "peer GPU PID"):
            self.analyze()

    def test_final_resource_refusal_ineligible_despite_full_scores(self):
        self.observations[-1].update(status="blocked", error="Synthetic contention")
        self.records[-1]["boundary_error_after_score"] = "Synthetic contention"
        recompute(self.run, self.spec, self.records, self.observations, "Synthetic contention")
        result = self.analyze()
        self.assertTrue(result["score_equalities_gate_passed"])
        self.assertFalse(result["resource_gate_passed"])
        self.assertFalse(result["analysis"]["eligible_for_versioned_score_replacement"])
        self.assertEqual(result["counts"]["completed_scientific_scores"], 1248)

    def test_failed_end_prior_parity_need_not_have_end_begin_metadata(self):
        row = self.records[-1]
        row["candidate_token_logprobs"][-1] -= .125
        row["sequence_logprob_sum"] = math.fsum(row["candidate_token_logprobs"])
        row["sentinel_exact_parity"] = False
        row.pop("end_begin_exact_parity")
        row["boundary_error_after_score"] = "Synthetic sentinel mismatch"
        recompute(self.run, self.spec, self.records, self.observations, "Synthetic sentinel mismatch")
        result = self.analyze()
        self.assertFalse(result["bounded_numerical_gate_passed"])
        self.assertFalse(result["analysis"]["eligible_for_versioned_score_replacement"])
        self.assertEqual(result["counts"]["completed_scientific_scores"], 1248)

    def test_missing_after_boundary_on_failed_call_rejected(self):
        self.records[-1]["boundary_error_after_score"] = "Synthetic after failure"
        self.observations.pop()
        recompute(self.run, self.spec, self.records, self.observations, "Synthetic after failure")
        with self.assertRaisesRegex(ValueError, "boundary receipt"):
            self.analyze()

    def test_scientific_sentinel_full_score_mismatch_is_not_accepted(self):
        target = next(i for i, r in enumerate(self.records) if r["phase"] == "scientific" and "scientific_sentinel_exact_parity" in r)
        row = self.records[target]
        row["candidate_token_logprobs"][-1] -= .25
        row["sequence_logprob_sum"] = math.fsum(row["candidate_token_logprobs"])
        row["scientific_sentinel_exact_parity"] = False
        row["boundary_error_after_score"] = "Synthetic scientific sentinel mismatch"
        for later in self.records[target + 1:]:
            for key in checker.CORE:
                later.pop(key, None)
            later.update(status="not_run", forward_attempted=False, reason="Synthetic scientific sentinel mismatch")
        self.observations = self.observations[:1 + 2 * (target + 1)]
        recompute(self.run, self.spec, self.records, self.observations, "Synthetic scientific sentinel mismatch")
        result = self.analyze()
        self.assertFalse(result["bounded_numerical_gate_passed"])
        self.assertFalse(result["counts"]["all_sentinel_scientific_repeats_exact"])
        self.assertFalse(result["analysis"]["eligible_for_versioned_score_replacement"])

    def test_nonfinite_score_rejected(self):
        self.records[33]["candidate_token_logprobs"][0] = float("nan")
        with self.assertRaisesRegex(ValueError, "Invalid token"):
            checker.verify_records(self.spec["inputs"], self.spec["sentinels"], self.records)

    def test_positive_logprob_rejected(self):
        self.records[33]["candidate_token_logprobs"][0] = .5
        with self.assertRaisesRegex(ValueError, "Invalid token"):
            checker.verify_records(self.spec["inputs"], self.spec["sentinels"], self.records)

    def test_item_level_transition_matches_full_candidate_scores(self):
        case = next(c for c in self.spec["inputs"] if c["identity"][:3] == ["original", "emoji", "affect_01"])
        block_cases = [c for c in self.spec["inputs"] if c["identity"][:3] == case["identity"][:3]]
        for c in block_cases:
            context, cue = c["identity"][3:]
            desired = (1 if context == "q" else -1) * (1 if cue == "b" else -1)
            for candidate in ("a", "b"):
                row = next(r for r in self.records if r["phase"] == "scientific" and r["input_id"] == c["input_id"] and r["method"] == "padded_" + candidate)
                probs = [-1.] * len(row["candidate_token_logprobs"])
                # Same prefix, selected finite total controlled using last token.
                target = -20 + desired if candidate == "a" else -20
                probs[-1] = target - math.fsum(probs[:-1])
                row["candidate_token_logprobs"], row["sequence_logprob_sum"] = probs, math.fsum(probs)
        _, _, blocks = checker.validate_spec(self.spec)
        result = checker.scientific_analysis(self.spec["inputs"], self.records, blocks)
        table = next(t for t in result["block_tables"] if (t["pair_id"], t["carrier"], t["block_id"]) == ("original", "emoji", "affect_01"))
        self.assertEqual(table["new"]["H"], 4)
        self.assertTrue(table["new"]["all_four_aligned"])
        self.assertTrue(table["all_four_aligned_changed"])
        self.assertEqual(table["new"]["minimum_author_signed_margin"], 1)

    def test_decomposition_negative_and_tie_boundaries(self):
        positive = {"p": {"a": 1., "b": -1.}, "q": {"a": -1., "b": 1.}}
        r = checker.decompose(positive, -1)
        self.assertEqual(r["H"], -4)
        self.assertFalse(r["effect_crossover"])
        self.assertFalse(r["all_four_aligned"])
        tied = checker.decompose({c: {v: 0. for v in ("a", "b")} for c in ("p", "q")}, 1)
        self.assertEqual(tied["tied_inputs"], 4)
        self.assertEqual(tied["H_sign"], "zero")

    def test_output_is_exclusive(self):
        output = Path(self.temporary.name) / "out.json"
        checker.write_output(output, {"synthetic": True})
        with self.assertRaises(FileExistsError):
            checker.write_output(output, {})


if __name__ == "__main__":
    unittest.main()
