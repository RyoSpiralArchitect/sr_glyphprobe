"""Synthetic, model-free tests for post hoc measurement algebra and refusal gates."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("measurement_analysis", ROOT / "scripts/analyze_contextual_emoji_measurement_v0.py")
analysis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analysis)


def table(b0=0, bC=0, bV=0, bCV=0, eta=1):
    return {c: {v: eta * (b0 + bC * C + bV * V + bCV * C * V) for v, V in analysis.CUE.items()}
            for c, C in analysis.CONTEXT.items()}


def fixture():
    blocks = [{"block_id": f"family{f}_{i}", "family": f"family{f}", "eta": 1} for f in range(6) for i in range(4)]
    rows = []
    for p in analysis.PAIR_IDS:
        for c in analysis.CARRIERS:
            for b in blocks:
                s = table(bCV=1)
                rows.append({"pair_id": p, "carrier": c, "block_id": b["block_id"], "family": b["family"],
                    "s": s, "H": 4, "complete": True, "all_four_aligned": True, "effect_crossover": True})
    return blocks, rows


class AlgebraTests(unittest.TestCase):
    def test_reconstruct_and_identities(self):
        d = analysis.decompose(table(2, -3, 4, 5), 1)
        self.assertEqual(d["coefficients"], {"b0": 2, "bC": -3, "bV": 4, "bCV": 5})
        self.assertEqual(d["H"], 20)
        self.assertEqual(d["maximum_reconstruction_absolute_error"], 0)
        self.assertTrue(d["H_equals_sum_signed_margins"])

    def test_positive_H_without_crossover(self):
        d = analysis.decompose(table(bV=2, bCV=1), 1)
        self.assertGreater(d["H"], 0)
        self.assertFalse(d["effect_crossover"])

    def test_crossover_without_all_four(self):
        d = analysis.decompose(table(b0=2, bCV=1), 1)
        self.assertTrue(d["effect_crossover"])
        self.assertFalse(d["all_four_aligned"])
        self.assertEqual(d["aligned_inputs"], 2)

    def test_all_four_and_strict_ties(self):
        self.assertTrue(analysis.decompose(table(bCV=1), 1)["all_four_aligned"])
        d = analysis.decompose(table(b0=1, bCV=1), 1)
        self.assertEqual(d["tied_inputs"], 2)
        self.assertFalse(d["all_four_aligned"])
        zero = analysis.decompose(table(), 1)
        self.assertEqual(zero["tied_inputs"], 4)
        self.assertFalse(zero["effect_crossover"])

    def test_absent_context_shift_preserves_interaction_and_cue_term(self):
        s = table(1, 2, 3, 4)
        a = analysis.decompose(s, 1)
        b = analysis.decompose(analysis.shifted_score(s, {"p": 7, "q": -5}), 1)
        self.assertEqual(a["H"], b["H"])
        self.assertEqual(a["coefficients"]["bV"], b["coefficients"]["bV"])
        self.assertNotEqual(a["coefficients"]["b0"], b["coefficients"]["b0"])
        self.assertNotEqual(a["coefficients"]["bC"], b["coefficients"]["bC"])

    def test_eta_and_candidate_swap_invariance(self):
        a = analysis.decompose(table(1, 2, 3, 4, eta=1), 1)
        b = analysis.decompose(table(1, 2, 3, 4, eta=-1), -1)
        self.assertEqual(a, b)

    def test_nonfinite_missing_and_extra_grid_refused(self):
        for value in (float("nan"), float("inf"), None, "1", True):
            s = table()
            s["p"]["a"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                analysis.decompose(s, 1)
        for mutate in (lambda s: s.pop("q"), lambda s: s["p"].pop("a"), lambda s: s.update(extra={})):
            s = table()
            mutate(s)
            with self.assertRaises(ValueError):
                analysis.decompose(s, 1)

    def test_orthogonal_energy_and_zero_change(self):
        a = analysis.decompose(table(), 1)
        b = analysis.decompose(table(1, 2, 3, 4), 1)
        change = analysis.coefficient_change(a, b)
        self.assertEqual(change["mean_squared_cell_shift"], 30)
        self.assertAlmostEqual(sum(change["energy_shares"].values()), 1)
        self.assertEqual(change["energy_shares"]["b0"], 1 / 30)
        self.assertTrue(analysis.coefficient_change(a, a)["zero_shift"])
        self.assertTrue(all(x is None for x in analysis.coefficient_change(a, a)["energy_shares"].values()))

    def test_flip_threshold_requires_both_magnitudes_and_excludes_ties(self):
        a = analysis.decompose({"p": {"a": -0.2, "b": -2}, "q": {"a": 0, "b": 2}}, 1)
        b = analysis.decompose({"p": {"a": 2, "b": 0.2}, "q": {"a": 2, "b": 2}}, 1)
        low = analysis.threshold_flips(a, b, 0)
        high = analysis.threshold_flips(a, b, 1)
        self.assertEqual(low["strict_sign_flips"], 2)
        self.assertEqual(low["eligible_inputs_with_tie"], 1)
        self.assertEqual(high["eligible_inputs"], 1)
        self.assertEqual(high["strict_sign_flips"], 0)


class GridTests(unittest.TestCase):
    def test_complete_grid_stability_and_all_family_omissions(self):
        blocks, rows = fixture()
        d = analysis.build_decompositions(rows, blocks)
        self.assertEqual(len(d), 144)
        report = analysis.summarize(d, blocks)
        self.assertEqual(len(report["leave_one_family_out"]), 36)
        for c in analysis.CARRIERS:
            self.assertEqual(report["all_pair_stability_summary"][c]["stable_correct"], 96)
            self.assertEqual(report["all_pair_stability_summary"][c]["all_four_aligned_all_pairs_blocks"], 24)
        self.assertTrue(all(r["retained_blocks"] == 20 for r in report["leave_one_family_out"]))

    def test_duplicate_missing_changed_and_unrun_rows_refused(self):
        for mutation in ("duplicate", "missing", "unrun", "nonfinite", "H", "family"):
            blocks, rows = fixture()
            if mutation == "duplicate": rows[1] = deepcopy(rows[0])
            if mutation == "missing": rows.pop()
            if mutation == "unrun": rows[0]["complete"] = False
            if mutation == "nonfinite": rows[0]["s"]["p"]["a"] = float("nan")
            if mutation == "H": rows[0]["H"] = 5
            if mutation == "family": rows[0]["family"] = "wrong"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                analysis.build_decompositions(rows, blocks)


class PrefixAndIOTests(unittest.TestCase):
    @staticmethod
    def scorer(row):
        return math.fsum(row["candidate_token_logprobs"])

    def test_shared_prefix_residual_retained_and_tail_additive(self):
        a = {"status": "completed", "prompt": "p", "prompt_token_ids": [1], "candidate_token_ids": [2, 3],
             "candidate_token_count": 2, "candidate_token_logprobs": [-1, -2]}
        b = dict(a, candidate_token_ids=[2, 4, 5], candidate_token_count=3, candidate_token_logprobs=[-1.125, -2, -3])
        split = analysis.token_prefix_split(a, b, self.scorer)
        self.assertEqual(split["shared_prefix_token_count"], 1)
        self.assertEqual(split["s_prefix"], 0.125)
        self.assertEqual(split["s_total"], split["s_prefix"] + split["s_tail"])
        self.assertEqual(split["prefix_per_token_probability_residuals"], [0.125])

    def test_zero_prefix_and_changed_prompt_refusal(self):
        a = {"status": "completed", "prompt": "p", "prompt_token_ids": [1], "candidate_token_ids": [2],
             "candidate_token_count": 1, "candidate_token_logprobs": [-1]}
        b = dict(a, candidate_token_ids=[3])
        self.assertEqual(analysis.token_prefix_split(a, b, self.scorer)["s_prefix"], 0)
        b["prompt"] = "q"
        with self.assertRaises(ValueError): analysis.token_prefix_split(a, b, self.scorer)

    def test_refuse_overwrite_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "report.json"
            analysis.write_output(out, {"value": 1})
            with self.assertRaises(ValueError): analysis.write_output(out, {"value": 2})
            self.assertEqual(json.loads(out.read_text()), {"value": 1})
            with self.assertRaises(ValueError): analysis.write_output(Path(directory) / "bad.json", {"value": float("nan")})
            self.assertFalse((Path(directory) / "bad.json").exists())

    def test_duplicate_keys_nonfinite_and_protected_files_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "input.json"
            for payload in ('{"x": 1, "x": 2}', '{"x": NaN}'):
                out.write_text(payload)
                with self.assertRaises(ValueError): analysis.read(out)
        for name in analysis.PROTECTED:
            with self.assertRaises(ValueError): analysis.safe(Path("/not-opened") / name)

    def test_independent_analyzer_hash_checked_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            source = root / "scripts/summarize_contextual_emoji_candidate_wording_v0.py"
            source.write_text('raise AssertionError("source must not execute before pin check")\n')
            with self.assertRaises(ValueError):
                analysis.load_existing_analyzer(root, "0" * 64)


if __name__ == "__main__":
    unittest.main()
