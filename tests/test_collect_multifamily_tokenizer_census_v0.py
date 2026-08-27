from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "collect_multifamily_tokenizer_census_v0.py"
SPEC = importlib.util.spec_from_file_location("collect_multifamily_census", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


def row(label: str, item: str, context: str, ids: list[int]) -> dict[str, object]:
    return {
        "tokenizer_label": label,
        "item_id": item,
        "context_id": context,
        "token_ids": ids,
        "offset_mapping": [[index, index + 1] for index in range(len(ids))],
        "whole_token_count": len(ids),
        "span_token_positions": list(range(len(ids))),
        "span_token_ids": ids,
        "span_token_count": len(ids),
        "decoded_text": item,
        "roundtrip_exact": True,
    }


class CollectorTests(unittest.TestCase):
    def test_common_prefix_length(self) -> None:
        self.assertEqual(collector.common_prefix_length([1, 2, 3], [1, 2, 9]), 2)
        self.assertEqual(collector.common_prefix_length([1], [9]), 0)
        self.assertEqual(collector.common_prefix_length([], []), 0)

    def test_public_metadata_scrubs_absolute_paths_only(self) -> None:
        value = {
            "local_path": "/Users/example/model",
            "relative_path": "models/example",
            "repo_id": "org/model",
            "nested": ["/home/example/cache", "plain"],
        }
        scrubbed = collector.scrub_public_metadata(value)
        self.assertEqual(scrubbed["local_path"], collector.LOCAL_PATH_REDACTION)
        self.assertEqual(scrubbed["nested"][0], collector.LOCAL_PATH_REDACTION)
        self.assertEqual(scrubbed["relative_path"], "models/example")
        self.assertEqual(scrubbed["repo_id"], "org/model")
        self.assertEqual(collector.absolute_path_values(scrubbed), [])

    def test_output_classes_ignore_label_but_not_tokenization(self) -> None:
        rows = [
            row("alpha", "a", "raw", [1, 2]),
            row("alpha", "b", "raw", [1, 3]),
            row("beta", "a", "raw", [1, 2]),
            row("beta", "b", "raw", [1, 3]),
            row("gamma", "a", "raw", [8]),
            row("gamma", "b", "raw", [9]),
        ]
        original_items = collector.EXPECTED_ITEMS
        original_contexts = collector.EXPECTED_CONTEXTS
        collector.EXPECTED_ITEMS = 2
        collector.EXPECTED_CONTEXTS = ("raw",)
        try:
            classes = collector.build_equivalence_classes(rows)
        finally:
            collector.EXPECTED_ITEMS = original_items
            collector.EXPECTED_CONTEXTS = original_contexts
        self.assertEqual(len(classes), 2)
        memberships = sorted(sorted(value["labels"]) for value in classes)
        self.assertEqual(memberships, [["alpha", "beta"], ["gamma"]])

    def test_universal_candidate_requires_every_label(self) -> None:
        lookup = {
            ("a", "target", "raw"): row("a", "target", "raw", [1, 2, 3]),
            ("a", "candidate", "raw"): row("a", "candidate", "raw", [1, 2, 9]),
            ("b", "target", "raw"): row("b", "target", "raw", [4, 5, 6]),
            ("b", "candidate", "raw"): row("b", "candidate", "raw", [4, 8, 9]),
        }
        self.assertEqual(
            collector.candidate_ids(
                lookup=lookup,
                labels=["a", "b"],
                target_id="target",
                candidate_item_ids=["candidate"],
                context_id="raw",
                minimum_prefix=1,
            ),
            ["candidate"],
        )
        self.assertEqual(
            collector.candidate_ids(
                lookup=lookup,
                labels=["a", "b"],
                target_id="target",
                candidate_item_ids=["candidate"],
                context_id="raw",
                minimum_prefix=2,
            ),
            [],
        )

    def test_published_validator_detects_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            aggregate = {
                "analysis_id": collector.ANALYSIS_ID,
            }
            (root / "aggregate.json").write_bytes(collector.json_bytes(aggregate))
            nested = root / "source_nodes" / "mac1"
            nested.mkdir(parents=True)
            (nested / "receipt.json").write_bytes(collector.json_bytes({}))
            (nested / "summary.json").write_bytes(collector.json_bytes({}))
            source_sums = {
                "receipt.json": collector.sha256(nested / "receipt.json"),
                "summary.json": collector.sha256(nested / "summary.json"),
                "tokenizations.jsonl": "1" * 64,
                "pairwise_controls.jsonl": "2" * 64,
            }
            (nested / "SOURCE_SHA256SUMS").write_text(
                "\n".join(f"{digest}  {name}" for name, digest in source_sums.items())
                + "\n"
            )
            node_checksums = [
                f"{collector.sha256(nested / name)}  {name}"
                for name in ("receipt.json", "summary.json", "SOURCE_SHA256SUMS")
            ]
            (nested / "SHA256SUMS").write_text("\n".join(node_checksums) + "\n")
            receipt = {
                "status": "pass",
                "analysis_id": collector.ANALYSIS_ID,
                "aggregate": {
                    "sha256": collector.sha256(root / "aggregate.json"),
                },
                "script": {"sha256": collector.sha256(SCRIPT)},
                "public_source_metadata": {
                    "receipt_and_summary_copies": "absolute_paths_redacted"
                },
                "source_nodes": {
                    "mac1": {
                        "receipt_sha256": source_sums["receipt.json"],
                        "summary_sha256": source_sums["summary.json"],
                        "tokenizations_sha256": source_sums["tokenizations.jsonl"],
                        "pairwise_controls_sha256": source_sums[
                            "pairwise_controls.jsonl"
                        ],
                        "source_sha256sums_sha256": collector.sha256(
                            nested / "SOURCE_SHA256SUMS"
                        ),
                    }
                },
            }
            (root / "collection_receipt.json").write_bytes(
                collector.json_bytes(receipt)
            )
            checksums = [
                f"{collector.sha256(root / name)}  {name}"
                for name in (
                    "aggregate.json",
                    "collection_receipt.json",
                    "source_nodes/mac1/SHA256SUMS",
                    "source_nodes/mac1/SOURCE_SHA256SUMS",
                    "source_nodes/mac1/receipt.json",
                    "source_nodes/mac1/summary.json",
                )
            ]
            (root / "SHA256SUMS").write_text("\n".join(checksums) + "\n")
            original_nodes = collector.NODES
            collector.NODES = ("mac1",)
            try:
                result = collector.validate_published_output(root, SCRIPT)
            finally:
                collector.NODES = original_nodes
            self.assertEqual(result["status"], "pass")
            (root / "aggregate.json").write_text(json.dumps({"changed": True}))
            collector.NODES = ("mac1",)
            try:
                with self.assertRaisesRegex(
                    collector.CollectionError, "checksum differs"
                ):
                    collector.validate_published_output(root, SCRIPT)
            finally:
                collector.NODES = original_nodes

    def test_checked_in_aggregate_matches_bounded_result_summary(self) -> None:
        artifact = ROOT / "artifacts" / "multifamily_tokenizer_census_v0"
        validation = collector.validate_published_output(artifact, SCRIPT)
        self.assertEqual(validation["status"], "pass")

        aggregate = json.loads((artifact / "aggregate.json").read_text())
        self.assertEqual(aggregate["unique_output_class_count"], 7)
        expected_integrity = {
            "roster_entries": 14,
            "successful_roster_entries": 14,
            "panel_items": 115,
            "tokenization_rows": 6440,
            "pairwise_rows": 19665,
            "model_forward_calls": 0,
            "protected_target_files_opened": 0,
        }
        for key, expected in expected_integrity.items():
            with self.subTest(key=key):
                self.assertEqual(aggregate["integrity"][key], expected)
        self.assertEqual(
            aggregate["cross_class_raw_range_histogram"],
            {"0": 6, "1": 6, "2": 10, "3": 3, "4": 78, "5": 6, "7": 5, "13": 1},
        )
        self.assertEqual(aggregate["roundtrip"]["failure_count"], 345)
        flags = aggregate["decision_relevant_descriptive_flags"]
        self.assertFalse(
            flags[
                "blue_circle_has_universal_equal_count_prefix_1_candidate_in_any_fixed_context"
            ]
        )
        self.assertFalse(
            flags[
                "blue_square_has_universal_equal_count_prefix_1_candidate_in_any_fixed_context"
            ]
        )


if __name__ == "__main__":
    unittest.main()
