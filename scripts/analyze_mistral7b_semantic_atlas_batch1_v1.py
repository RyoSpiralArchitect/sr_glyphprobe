#!/usr/bin/env python3
"""Bind the frozen semantic-atlas analyzer to the validated batch-one v1 run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_mistral7b_semantic_atlas_v0 as analyzer  # noqa: E402
import mistral7b_semantic_atlas_batch1_v1 as batch1  # noqa: E402


VALIDATION_PATH = Path(
    "validation/mistral7b_semantic_atlas_batch1_v1/capture_validation_v1.json"
)
EXPECTED_VALIDATION_SHA256 = (
    "52367403f7dfd99c2390498f7c005b29fd555e673dab4231f4983b125cab51d2"
)


def analyze(run_root: Path, output: Path, *, knn_k: int = 10) -> dict[str, Any]:
    root = batch1.v0._root()
    validation = batch1.v0._read_json(root / VALIDATION_PATH)
    batch1.v0._require(
        batch1.v0._sha256(root / VALIDATION_PATH) == EXPECTED_VALIDATION_SHA256,
        "Batch1 capture-validation hash mismatch",
    )
    batch1.v0._require(validation.get("status") == "pass", "Batch1 capture validation failed")
    batch1.v0._require(validation.get("passed_case_count") == 18, "Batch1 validation case mismatch")
    batch1.v0._require(validation.get("reserve_forward_calls") == 0, "Batch1 validation touched reserve")
    with batch1._delegated_surface():
        receipt = analyzer.analyze(run_root, output, knn_k=knn_k)
    receipt["capture_validation_sha256"] = EXPECTED_VALIDATION_SHA256
    receipt["canonical_source_protocol_id"] = batch1.PROTOCOL_ID
    batch1.v0._write_json(output / "analysis_receipt.json", receipt)
    batch1.v0._write_ledger(
        output,
        (
            "cell_metrics.jsonl",
            "item_pair_cosines.jsonl",
            "layer_summary.json",
            "analysis_receipt.json",
        ),
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--knn-k", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(analyze(args.run, args.output, knn_k=args.knn_k), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
