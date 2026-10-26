"""Synthetic author-pilot package tests; never expose real items or answer keys."""
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("author_pilot", ROOT / "scripts/contextual_emoji_author_pilot_v0.py")
pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pilot)


def synthetic_objects(seed=7):
    blocks, panel = pilot.demo_materials()
    return pilot.objects(blocks, panel, {"synthetic": {"path": "none", "sha256": "0" * 64}}, seed, demo=True)


def rewrite(path, value):
    # Explicit test-only tampering, never a real prepared package.
    path.write_bytes(pilot.canonical(value))


def rehash(package, relative):
    manifest = pilot.read_json(package / "manifest.json")
    manifest["artifacts"][relative] = pilot.sha256(package / relative)
    rewrite(package / "manifest.json", manifest)


class AllocationTests(unittest.TestCase):
    def test_balance_for_many_private_seeds(self):
        blocks, _ = pilot.demo_materials()
        for seed in range(100):
            counts = pilot.balance_counts(pilot.allocate(blocks, seed))
            self.assertEqual(counts["items"], 24)
            self.assertEqual(counts["carrier_totals"], {"emoji": 12, "word": 12})
            self.assertEqual(counts["items_per_candidate_pair"], 8)
            self.assertEqual(counts["items_per_carrier_candidate_pair"], 4)
            self.assertEqual(counts["original_a_first"], 12)
            self.assertEqual(counts["absent_items"], 0)

    def test_deterministic_replay_and_seed_variation(self):
        a = synthetic_objects(7)
        self.assertEqual(a, synthetic_objects(7))
        self.assertNotEqual(a[0], synthetic_objects(8)[0])

    def test_selection_independent_of_labels_and_extraneous_results(self):
        blocks, _ = pilot.demo_materials()
        changed = deepcopy(blocks)
        for block in changed:
            block["eta"] = -1
            block["orientation"] = {}
            block["model_result_should_never_be_read"] = object()
        self.assertEqual(pilot.allocate(blocks, 9), pilot.allocate(changed, 9))

    def test_opaque_ids_no_source_mapping_in_participant(self):
        participant, answer, assignment, _ = synthetic_objects()
        self.assertEqual(set(participant), pilot.PARTICIPANT_FIELDS)
        self.assertTrue(pilot.PACKAGE_PATTERN.fullmatch(participant["package_id"]))
        for item in participant["items"]:
            self.assertEqual(set(item), {"id", "prompt", "responses"})
            self.assertTrue(pilot.ITEM_PATTERN.fullmatch(item["id"]))
        self.assertNotIn("seed", participant)
        self.assertNotIn("items", {k: v for k, v in participant.items() if k != "items"})
        self.assertEqual([r["id"] for r in participant["items"]], [r["id"] for r in answer["items"]])
        self.assertEqual([r["id"] for r in participant["items"]], [r["id"] for r in assignment["items"]])

    def test_source_literal_whitespace_and_negative_eta_mapping_preserved(self):
        blocks, panel = pilot.demo_materials()
        block = blocks[0]
        original = pilot.response_candidates(block, panel, "original")
        self.assertEqual(original["a"], block["candidate_a"])
        for row in blocks:
            row["eta"] = -1
            for context in row["orientation"].values():
                for cue in context:
                    context[cue] = "b" if context[cue] == "a" else "a"
        participant, answer, allocation, _ = pilot.objects(blocks, panel, {}, 8, demo=True)
        by_id = {r["id"]: r for r in allocation["items"]}
        by_block = {r["block_id"]: r for r in blocks}
        by_answer = {r["id"]: r for r in answer["items"]}
        for item in participant["items"]:
            row = by_id[item["id"]]
            source = by_block[row["block_id"]]
            choices = pilot.response_candidates(source, panel, row["pair_id"])
            self.assertEqual(item["responses"], [choices[k] for k in row["display_order"]])
            self.assertTrue(all(text.startswith(" ") for text in item["responses"]))
            authored = source["orientation"][f"context_{row['context']}"][f"emoji_{row['cue']}"]
            self.assertEqual(by_answer[item["id"]]["displayed_authored_response"], row["display_order"].index(authored) + 1)

    def test_bad_seed_and_balance_fail_closed(self):
        blocks, _ = pilot.demo_materials()
        for seed in (-1, True, 1.25, 2**256, "private"):
            with self.assertRaises(ValueError):
                pilot.allocate(blocks, seed)
        rows = pilot.allocate(blocks, 10)
        rows[0]["carrier"] = "absent"
        with self.assertRaises(ValueError):
            pilot.balance_counts(rows)

    def test_source_shapes_only_no_real_package_generation(self):
        blocks, panel, sources = pilot.load_sources(ROOT)
        self.assertEqual(len(blocks), 24)
        self.assertEqual(len(panel["additional_pairs"]), 2)
        self.assertEqual(set(sources), set(pilot.SOURCE_PINS) | {"generator"})


class AllowlistTests(unittest.TestCase):
    def setUp(self):
        self.participant = synthetic_objects()[0]

    def test_extra_fields_rejected_at_all_levels(self):
        for field in ("eta", "seed", "model_score", "answer_key", "source_id", "label", "order_mapping"):
            for level in ("top", "item"):
                candidate = deepcopy(self.participant)
                target = candidate if level == "top" else candidate["items"][0]
                target[field] = "private"
                with self.assertRaisesRegex(ValueError, "allowlist"):
                    pilot.validate_participant(candidate)

    def test_nonopaque_duplicate_and_invalid_ids_rejected(self):
        for changed in ("original/emoji/item", "item_123", 12):
            candidate = deepcopy(self.participant)
            candidate["items"][0]["id"] = changed
            with self.assertRaises(ValueError):
                pilot.validate_participant(candidate)
        candidate = deepcopy(self.participant)
        candidate["items"][1]["id"] = candidate["items"][0]["id"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            pilot.validate_participant(candidate)

    def test_response_types_lengths_and_placeholders_rejected(self):
        for responses in (["same", "same"], ["one"], ["one", {"answer": True}], ["one", ""], "not-list"):
            candidate = deepcopy(self.participant)
            candidate["items"][0]["responses"] = responses
            with self.assertRaises(ValueError):
                pilot.validate_participant(candidate)
        candidate = deepcopy(self.participant)
        candidate["items"][0]["prompt"] = "template {emoji}"
        with self.assertRaises(ValueError):
            pilot.validate_participant(candidate)

    def test_duplicate_nonfinite_json_and_protected_paths_rejected(self):
        for text in ('{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}'):
            with self.assertRaises(ValueError):
                pilot.decode(text)
        for name in pilot.PROTECTED:
            with self.assertRaises(ValueError):
                pilot.read_json(Path("/tmp") / name)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name).resolve() / "synthetic-package"
        self.summary = pilot.build(ROOT, self.package, seed=42, demo=True)

    def test_verify_permissions_hashes_and_safe_output(self):
        self.assertEqual(self.summary, pilot.verify(self.package, ROOT))
        self.assertEqual(self.summary["mode"], "synthetic_demo")
        self.assertEqual(self.summary["total_items"], 24)
        self.assertFalse(self.summary["checks"]["model_outcomes_read"])
        for relative in (".", "participant", "private"):
            self.assertEqual(stat.S_IMODE((self.package / relative).stat().st_mode), 0o700)
        for relative in (*pilot.ARTIFACTS, "manifest.json"):
            self.assertEqual(stat.S_IMODE((self.package / relative).stat().st_mode), 0o600)
        text = json.dumps(self.summary)
        for forbidden in ("Practice alternative", "Synthetic practice scenario", '"seed"', "display_order", "authored_eta", "block_id"):
            self.assertNotIn(forbidden, text)

    def test_output_collision_does_not_modify_existing_bytes(self):
        old = {name: pilot.sha256(self.package / name) for name in (*pilot.ARTIFACTS, "manifest.json")}
        with self.assertRaisesRegex(ValueError, "existing"):
            pilot.build(ROOT, self.package, seed=99, demo=True)
        self.assertEqual(old, {name: pilot.sha256(self.package / name) for name in old})
        with self.assertRaises(FileExistsError):
            pilot.write_exclusive(self.package / "manifest.json", {})

    def test_simple_hash_tamper_rejected(self):
        path = self.package / "participant/participant.json"
        value = pilot.read_json(path)
        value["items"][0]["responses"][0] += " tampered"
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            pilot.verify(self.package, ROOT)

    def test_rehashed_participant_tamper_rejected_by_literal_replay(self):
        path = self.package / "participant/participant.json"
        value = pilot.read_json(path)
        value["items"][0]["responses"][0] += " tampered"
        rewrite(path, value)
        rehash(self.package, "participant/participant.json")
        with self.assertRaisesRegex(ValueError, "source-bound assignment"):
            pilot.verify(self.package, ROOT)

    def test_rehashed_answer_label_tamper_rejected(self):
        path = self.package / "private/answer_key.json"
        value = pilot.read_json(path)
        value["items"][0]["displayed_authored_response"] = 0
        rewrite(path, value)
        rehash(self.package, "private/answer_key.json")
        with self.assertRaisesRegex(ValueError, "authored key"):
            pilot.verify(self.package, ROOT)

    def test_rehashed_assignment_tamper_rejected(self):
        path = self.package / "private/assignment_key.json"
        value = pilot.read_json(path)
        value["items"][0]["context"] = "unplanned"
        rewrite(path, value)
        rehash(self.package, "private/assignment_key.json")
        with self.assertRaisesRegex(ValueError, "assignment differs"):
            pilot.verify(self.package, ROOT)

    def test_loose_permission_and_extra_participant_file_refused(self):
        path = self.package / "private/answer_key.json"
        path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "owner-only"):
            pilot.verify(self.package, ROOT)
        path.chmod(0o600)
        pilot.write_exclusive(self.package / "participant/private.json", {"secret": "synthetic"})
        with self.assertRaisesRegex(ValueError, "extra files"):
            pilot.verify(self.package, ROOT)

    def test_symlink_refused(self):
        path = self.package / "participant/participant.json"
        backup = Path(self.temp.name) / "synthetic-backup.json"
        path.rename(backup)
        path.symlink_to(backup)
        with self.assertRaisesRegex(ValueError, "symlink"):
            pilot.verify(self.package, ROOT)

    def test_manifest_source_and_inventory_tamper_refused(self):
        path = self.package / "manifest.json"
        original = pilot.read_json(path)
        value = deepcopy(original)
        value["sources"]["generator"]["sha256"] = "0" * 64
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "source binding"):
            pilot.verify(self.package, ROOT)
        value = deepcopy(original)
        value["artifacts"]["../../other"] = "0" * 64
        rewrite(path, value)
        with self.assertRaisesRegex(ValueError, "artifact inventory"):
            pilot.verify(self.package, ROOT)

    def test_demo_reads_no_real_source_files(self):
        reads = []
        original = pilot.sha256
        def record(path):
            reads.append(Path(path).name)
            return original(path)
        with patch.object(pilot, "sha256", side_effect=record):
            pilot.load_sources(ROOT, demo=True)
        self.assertEqual(set(reads), {"contextual_emoji_author_pilot_v0.py"})

    def test_cli_output_is_safe_on_success_and_failure(self):
        for args in (["inspect", "--package", str(self.package)],
                     ["build", "--output", str(Path(self.temp.name) / "bad-seed"), "--seed", "PRIVATE_BAD_SEED", "--demo"]):
            output = io.StringIO()
            with patch("sys.argv", ["pilot", *args]), patch("sys.stdout", output):
                code = pilot.main()
            text = output.getvalue()
            self.assertIn(code, (0, 2))
            for forbidden in ("PRIVATE_BAD_SEED", "Practice alternative", "display_order", '"seed"', "authored_eta"):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
