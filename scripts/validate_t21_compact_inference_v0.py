#!/usr/bin/env python3
"""Replay T21-C simultaneous inference from compact scalar contrasts, without a model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ORDER = [
    "calibration",
    "necessity_absolute",
    "necessity_position_adjusted",
    "rescue_absolute",
    "rescue_position_adjusted",
]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(compact: dict, result: dict) -> dict:
    check(
        compact["protocol_id"]
        == result["protocol_id"]
        == "glyphprobe-t21-glyph-context-path-confirmation-v0",
        "Protocol changed",
    )
    check(
        compact["target_items"]
        == result["target_items"]
        == len(compact["rows"])
        == 195,
        "Population changed",
    )
    check(
        compact["contrast_order"] == ORDER
        and compact["anchor"] == result["candidate_anchor"] == 21,
        "Contrast family or candidate changed",
    )
    check(
        compact["context_indices"] == [1, 3]
        and compact["donors_averaged_per_item"] == 2,
        "Aggregation changed",
    )
    check(
        [row["item_index"] for row in compact["rows"]] == list(range(195)),
        "Missing or duplicate item",
    )
    x = np.asarray(
        [row["alias_margin_contrasts"] for row in compact["rows"]], dtype=float
    )
    top1 = np.asarray(
        [row["alias_top1_contrasts"] for row in compact["rows"]], dtype=float
    )
    check(
        x.shape == top1.shape == (195, 5)
        and np.isfinite(x).all()
        and np.isfinite(top1).all(),
        "Invalid scalar contrasts",
    )
    primary = result["primary"]
    check(
        primary["replicates"] == 20000
        and primary["seed"] == 2026092201
        and primary["confidence"] == 0.95,
        "Inference settings changed",
    )
    n = 195
    mean = x.mean(axis=0)
    se = x.std(axis=0, ddof=1) / np.sqrt(n)
    check(bool((se > 1e-14).all()), "Degenerate original standard error")
    rng = np.random.default_rng(2026092201)
    maxima = []
    for _ in range(40):
        y = x[rng.integers(n, size=(500, n))]
        sy = y.std(axis=1, ddof=1) / np.sqrt(n)
        check(bool((sy > 1e-14).all()), "Degenerate bootstrap standard error")
        maxima.extend(((y.mean(axis=1) - mean) / sy).max(axis=1).tolist())
    critical = float(np.quantile(maxima, 0.95, method="linear"))
    lower = mean - critical * se
    differences = []
    for j, name in enumerate(ORDER):
        row = primary["contrasts"][name]
        differences.extend(
            [
                abs(row["mean"] - mean[j]),
                abs(row["standard_error"] - se[j]),
                abs(row["lower_simultaneous_95"] - lower[j]),
                abs(
                    result["secondary_endpoint_means"]["alias_top1_effect"][name]
                    - top1[:, j].mean()
                ),
            ]
        )
        check(
            bool(lower[j] > 0) == row["directional_pass"],
            "Per-contrast decision differs",
        )
    differences.append(abs(primary["critical_value"] - critical))
    check(max(differences) < 1e-10, "Compact numerical reconstruction differs")
    check(
        primary["all_five_positive"] == bool((lower > 0).all()),
        "Joint decision differs",
    )
    verdict = (
        "conditional_path_contribution_supported"
        if (lower > 0).all()
        else (
            "joint_path_claim_not_supported"
            if lower[0] > 0
            else "calibration_unresolved"
        )
    )
    check(result["verdict"] == verdict, "Verdict label differs")
    return {
        "status": "pass",
        "target_items": n,
        "replicates": 20000,
        "maximum_numeric_error": float(max(differences)),
        "verdict": verdict,
        "boundary": "Statistical replay from derived contrasts; raw-state correctness is a separate check.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = verify(
        json.loads(args.compact.read_text()), json.loads(args.result.read_text())
    )
    value.update(
        {
            "compact_sha256": hashlib.sha256(args.compact.read_bytes()).hexdigest(),
            "result_sha256": hashlib.sha256(args.result.read_bytes()).hexdigest(),
            "validator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
    )
    if args.output:
        with args.output.open("x", encoding="utf-8") as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.write("\n")
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
