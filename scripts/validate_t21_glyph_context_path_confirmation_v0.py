#!/usr/bin/env python3
"""Independent metric and simultaneous-inference reconstruction for T21-C."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import validate_t21_glyph_context_path_pilot_v0 as prior


CONDITIONS = prior.CONDITIONS
CONTRASTS = prior.CONTRASTS


def check(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def max_t(x: np.ndarray, replicates: int = 20000, seed: int = 2026092201) -> dict:
    n = len(x)
    means = x.mean(axis=0)
    se = x.std(axis=0, ddof=1) / np.sqrt(n)
    check(bool((se > 1e-14).all()), "Degenerate standard error")
    rng = np.random.default_rng(seed)
    maxima = np.empty(replicates)
    for start in range(0, replicates, 500):
        count = min(500, replicates - start)
        rows = rng.integers(0, n, size=(count, n))
        values = x[rows]
        boot_se = values.std(axis=1, ddof=1) / np.sqrt(n)
        check(bool((boot_se > 1e-14).all()), "Degenerate bootstrap standard error")
        maxima[start : start + count] = ((values.mean(axis=1) - means) / boot_se).max(
            axis=1
        )
    critical = float(np.quantile(maxima, 0.95, method="linear"))
    lower = means - critical * se
    return {
        "critical": critical,
        "means": means,
        "se": se,
        "lower": lower,
        "all_positive": bool((lower > 0).all()),
    }


def validate(run_root: Path, analysis_root: Path, output: Path) -> dict:
    check(not output.exists(), "Validation output already exists")
    acquisition = prior.read(run_root / "acquisition_receipt.json")
    specification = prior.read(run_root / "specification.json")
    analysis = prior.read(analysis_root / "analysis_receipt.json")
    check(
        acquisition["status"] == "acquisition_complete"
        and acquisition["mode"] == "confirmation"
        and acquisition["target_items"]
        == acquisition["reserve_items_forwarded"]
        == 195,
        "Incomplete confirmation acquisition",
    )
    check(
        prior.digest(run_root / "specification.json")
        == acquisition["specification_sha256"],
        "Specification bytes changed",
    )
    check(
        analysis["acquisition_receipt_sha256"]
        == prior.digest(run_root / "acquisition_receipt.json"),
        "Analysis points to another acquisition",
    )
    for name, expected in analysis["outputs"].items():
        check(
            prior.digest(analysis_root / name) == expected, "Analysis payload changed"
        )
    with np.load(run_root / "source_states.npz", allow_pickle=False) as f:
        source = f["states"]
    with np.load(analysis_root / "item_metrics.npz", allow_pickle=False) as f:
        reported = {name: f[name] for name in f.files}
    rebuilt = {name: np.empty_like(values) for name, values in reported.items()}
    covered = set()
    for name, receipt_hash in sorted(acquisition["chunks"].items()):
        directory = run_root / name
        check(
            prior.digest(directory / "receipt.json") == receipt_hash,
            "Changed chunk receipt",
        )
        receipt = prior.read(directory / "receipt.json")
        check(
            receipt["specification_sha256"] == acquisition["specification_sha256"],
            "Mixed specification",
        )
        check(
            prior.digest(directory / "states.npz") == receipt["states_sha256"],
            "Changed state bytes",
        )
        with np.load(directory / "states.npz", allow_pickle=False) as f:
            baseline, states, neutral, indices = (
                f["baseline"],
                f["intervention"],
                f["neutral_reference"],
                f["item_indices"],
            )
        check(
            np.array_equal(indices, np.arange(receipt["start"], receipt["stop"])),
            "Item order changed",
        )
        for condition in (0, 1, 9, 10):
            check(
                np.array_equal(states[..., condition, :], neutral[..., condition, :]),
                "Same-slot control differs",
            )
        for local, index in enumerate(indices.tolist()):
            check(index not in covered, "Duplicate item")
            covered.add(index)
            for context in range(4):
                actual = prior.reconstruct_item(
                    states[local, context],
                    baseline[local, context, 1],
                    baseline[local, context, 2],
                    source[:, context, 1],
                    source[:, context, 2],
                    specification["donor_indices"][index],
                )
                reference = prior.reconstruct_item(
                    neutral[local, context],
                    baseline[local, context, 1],
                    baseline[local, context, 2],
                    source[:, context, 1],
                    source[:, context, 2],
                    specification["donor_indices"][index],
                )
                for metric, values in actual.items():
                    rebuilt[metric][index, context] = values
                    rebuilt[metric + "_effect"][index, context] = (
                        values - reference[metric]
                    )
    check(covered == set(range(195)), "Incomplete coverage")
    errors = {
        name: float(np.max(np.abs(rebuilt[name] - reported[name]))) for name in rebuilt
    }
    check(
        all(error < 1e-10 for error in errors.values()), "Metric reconstruction differs"
    )
    # Fixed primary: contexts 1 and 3, anchor index 0, mean within item.
    values = rebuilt["alias_margin_effect"][:, [1, 3], 0].mean(axis=(1, 2))
    matrix = np.column_stack(
        [
            values[:, positive] - values[:, negative]
            for _name, positive, negative in CONTRASTS
        ]
    )
    independent = max_t(matrix)
    result = prior.read(analysis_root / "confirmation_result.json")
    reported_rows = result["primary"]["contrasts"]
    for j, (name, _positive, _negative) in enumerate(CONTRASTS):
        row = reported_rows[name]
        check(abs(row["mean"] - independent["means"][j]) < 1e-12, "Mean differs")
        check(abs(row["standard_error"] - independent["se"][j]) < 1e-12, "SE differs")
        check(
            abs(row["lower_simultaneous_95"] - independent["lower"][j]) < 1e-12,
            "Simultaneous bound differs",
        )
    check(
        abs(result["primary"]["critical_value"] - independent["critical"]) < 1e-12,
        "Critical value differs",
    )
    check(
        result["primary"]["all_five_positive"] == independent["all_positive"],
        "Verdict differs",
    )
    expected_verdict = (
        "conditional_path_contribution_supported"
        if independent["all_positive"]
        else (
            "joint_path_claim_not_supported"
            if independent["lower"][0] > 0
            else "calibration_unresolved"
        )
    )
    check(result["verdict"] == expected_verdict, "Claim-label mapping differs")
    receipt = {
        "status": "pass",
        "validator": Path(__file__).name,
        "validator_sha256": prior.digest(Path(__file__)),
        "acquisition_receipt_sha256": prior.digest(
            run_root / "acquisition_receipt.json"
        ),
        "analysis_receipt_sha256": prior.digest(
            analysis_root / "analysis_receipt.json"
        ),
        "target_items_validated": 195,
        "maximum_metric_errors": errors,
        "critical_value_error": abs(
            result["primary"]["critical_value"] - independent["critical"]
        ),
        "verdict": expected_verdict,
        "claim": "independent numerical reconstruction, not a second experimental replication",
    }
    with output.open("x", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate(args.run_root, args.analysis_root, args.output),
            indent=2,
            sort_keys=True,
        )
    )
