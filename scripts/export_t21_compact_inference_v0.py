#!/usr/bin/env python3
"""Export validated item-level T21-C contrasts for model-free statistical replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import t21_glyph_context_path_confirmation_v0 as confirmation
import t21_path_inference_v0 as stats


def export(analysis_root: Path, output: Path) -> dict:
    p = confirmation.pilot
    receipt = p.read_json(analysis_root / "analysis_receipt.json")
    independent = p.read_json(
        p.ROOT / confirmation.VALIDATION / "results/independent_validation.json"
    )
    p.require(
        independent["status"] == "pass"
        and independent["target_items_validated"] == 195,
        "Independent validation required",
    )
    p.require(
        independent["analysis_receipt_sha256"]
        == p.sha256(analysis_root / "analysis_receipt.json"),
        "Independent validation targets different analysis",
    )
    for name, expected in receipt["outputs"].items():
        p.require(
            p.sha256(analysis_root / name) == expected, "Analysis payload changed"
        )
    with np.load(analysis_root / "item_metrics.npz", allow_pickle=False) as f:
        primary = stats.contrast_matrix(f["alias_margin_effect"])
        top1 = stats.contrast_matrix(f["alias_top1_effect"])
    p.require(primary.shape == top1.shape == (195, 5), "Item shape changed")
    value = {
        "protocol_id": confirmation.PROTOCOL,
        "status": "derived_from_independently_validated_item_metrics",
        "created_at_utc": p.now(),
        "target_items": 195,
        "anchor": 21,
        "context_indices": [1, 3],
        "donors_averaged_per_item": 2,
        "contrast_order": list(stats.NAMES),
        "analysis_receipt_sha256": p.sha256(analysis_root / "analysis_receipt.json"),
        "item_metrics_sha256": receipt["outputs"]["item_metrics.npz"],
        "specification_sha256": receipt["specification_sha256"],
        "rows": [
            {
                "item_index": i,
                "alias_margin_contrasts": primary[i].tolist(),
                "alias_top1_contrasts": top1[i].tolist(),
            }
            for i in range(195)
        ],
        "boundary": "Derived scalar contrasts, not raw model states; permits statistical replay only.",
    }
    p.write_json(output, value)
    return {
        "status": "compact_contrasts_exported",
        "target_items": 195,
        "sha256": p.sha256(output),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.analysis_root, args.output), indent=2))
