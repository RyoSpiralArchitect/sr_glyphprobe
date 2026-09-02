#!/usr/bin/env python3
"""Item-level simultaneous inference and pilot-only precision planning for T21."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import t21_glyph_context_path_pilot_v0 as pilot


NAMES = tuple(pilot.CONTRASTS)
REPLICATES = 20000
INFERENCE_SEED = 2026092201
PLANNING_SEED = 2026092202


def contrast_matrix(
    metric: np.ndarray, anchor: int = 21, contexts: tuple[int, ...] = (1, 3)
) -> np.ndarray:
    """Average carriers and donors within items, then form the five contrasts."""
    x = np.asarray(metric, dtype=np.float64)
    pilot.require(x.ndim == 5 and x.shape[1:] == (4, 2, 2, 11), "Metric shape changed")
    pilot.require(np.isfinite(x).all(), "Nonfinite metric")
    values = x[:, list(contexts), pilot.ANCHORS.index(anchor)].mean(axis=(1, 2))
    return np.column_stack(
        [
            values[:, pilot.CONDITIONS.index(positive)]
            - values[:, pilot.CONDITIONS.index(negative)]
            for positive, negative in pilot.CONTRASTS.values()
        ]
    )


def simultaneous_lower(
    x: np.ndarray, *, replicates: int = REPLICATES, seed: int = INFERENCE_SEED
) -> dict:
    """One-sided 95% single-step max-studentized item-bootstrap lower bounds.

    Resampling indices are shared across the five endpoints. A zero-variance
    endpoint or resample is a failed inference check, never a positive result.
    Coverage is approximate and conditional on the fixed source gallery.
    """
    x = np.asarray(x, dtype=np.float64)
    pilot.require(
        x.ndim == 2 and x.shape[1] == 5 and len(x) >= 3,
        "Expected at least three items and exactly five contrasts",
    )
    pilot.require(np.isfinite(x).all() and replicates >= 100, "Invalid inference input")
    n = len(x)
    means = x.mean(axis=0)
    se = x.std(axis=0, ddof=1) / np.sqrt(n)
    pilot.require(bool((se > 1e-14).all()), "Degenerate original standard error")
    rng = np.random.default_rng(seed)
    maxima = np.empty(replicates)
    for start in range(0, replicates, 250):
        count = min(250, replicates - start)
        sampled = x[rng.integers(n, size=(count, n))]
        boot_se = sampled.std(axis=1, ddof=1) / np.sqrt(n)
        pilot.require(
            bool((boot_se > 1e-14).all()), "Degenerate bootstrap standard error"
        )
        maxima[start : start + count] = ((sampled.mean(axis=1) - means) / boot_se).max(
            axis=1
        )
    critical = float(np.quantile(maxima, 0.95, method="linear"))
    lower = means - critical * se
    return {
        "method": "one_sided_single_step_max_studentized_item_bootstrap",
        "confidence": 0.95,
        "coverage": "approximate_simultaneous_conditional_on_fixed_source_pool",
        "replicates": replicates,
        "seed": seed,
        "target_items": n,
        "critical_value": critical,
        "contrasts": {
            name: {
                "mean": float(means[j]),
                "standard_error": float(se[j]),
                "lower_simultaneous_95": float(lower[j]),
                "directional_pass": bool(lower[j] > 0),
            }
            for j, name in enumerate(NAMES)
        },
        "all_five_positive": bool((lower > 0).all()),
    }


def planning_power(
    x: np.ndarray,
    critical: float,
    *,
    size: int = 195,
    cohorts: int = 5000,
    seed: int = PLANNING_SEED,
) -> dict:
    """Conditional planning only: empirical cohorts and a pilot-fixed critical value."""
    mean = x.mean(axis=0)
    pilot_se = x.std(axis=0, ddof=1) / np.sqrt(len(x))
    centered = x - mean
    scenarios = {
        "pilot_mean": mean,
        "pilot_mean_minus_one_pilot_se": mean - pilot_se,
        "half_pilot_mean": mean * 0.5,
    }
    successes = {key: 0 for key in scenarios}
    rng = np.random.default_rng(seed)
    for start in range(0, cohorts, 250):
        count = min(250, cohorts - start)
        sampled = centered[rng.integers(len(x), size=(count, size))]
        mean_noise = sampled.mean(axis=1)
        se = sampled.std(axis=1, ddof=1) / np.sqrt(size)
        for key, effect in scenarios.items():
            successes[key] += int(
                ((mean_noise + effect - critical * se) > 0).all(axis=1).sum()
            )
    return {
        "purpose": "planning_not_observed_confirmation_power",
        "planned_target_items": size,
        "simulated_cohorts": cohorts,
        "seed": seed,
        "pilot_fixed_critical_value": critical,
        "all_five_pass_probability": {
            key: successes[key] / cohorts for key in scenarios
        },
        "caveats": [
            "Conditions on the 384-item empirical covariance and fixed source pool.",
            "The selected anchor can yield optimistic pilot estimates.",
            "The remaining population can differ from the pilot; no guarantee of power.",
            "Confirmation will recompute its own critical value, not reuse this approximation.",
        ],
    }


def diagnostic_summary(x: np.ndarray) -> dict:
    n = len(x)
    out = {}
    for j, name in enumerate(NAMES):
        col = x[:, j]
        trim = max(1, int(np.ceil(n * 0.05)))
        out[name] = {
            "n": n,
            "mean": float(col.mean()),
            "median": float(np.median(col)),
            "positive_fraction": float((col > 0).mean()),
            "quantiles_05_25_75_95": np.quantile(
                col, [0.05, 0.25, 0.75, 0.95]
            ).tolist(),
            "minimum_leave_one_out_mean": float(((col.sum() - col) / (n - 1)).min()),
            "mean_after_removing_largest_five_percent": float(
                np.sort(col)[:-trim].mean()
            ),
        }
    return out


def plan(analysis_root: Path, specification: Path, output: Path) -> dict:
    pilot.require(not output.exists(), "Planning report already exists")
    receipt = pilot.read_json(analysis_root / "analysis_receipt.json")
    pilot.require(
        pilot.sha256(specification) == receipt["specification_sha256"],
        "Pilot specification mismatch",
    )
    for name, expected in receipt["outputs"].items():
        pilot.require(
            pilot.sha256(analysis_root / name) == expected, "Pilot analysis changed"
        )
    decision = pilot.read_json(analysis_root / "pilot_result.json")
    pilot.require(
        decision["candidate_anchor"] == 21 and decision["target_items"] == 384,
        "The prespecified pilot did not select anchor 21",
    )
    spec = pilot.audit_spec(specification)
    with np.load(analysis_root / "item_metrics.npz", allow_pickle=False) as f:
        metrics = {name: f[name] for name in f.files}
    x = contrast_matrix(metrics["alias_margin_effect"])
    pilot.require(len(x) == 384, "Pilot item count changed")
    simultaneous = simultaneous_lower(x)
    lengths = np.asarray([len(t["raw"]["glyph"]) for t in spec["target_tokens"]])
    report = {
        "status": "pilot_precision_and_quality_checked_confirmation_not_accessed",
        "created_at_utc": pilot.now(),
        "analysis_receipt_sha256": pilot.sha256(
            analysis_root / "analysis_receipt.json"
        ),
        "pilot_specification_sha256": pilot.sha256(specification),
        "inference_code_sha256": pilot.sha256(Path(__file__)),
        "candidate_anchor": 21,
        "target_items": 384,
        "statistical_unit": "target_item_after_averaging_two_carriers_and_two_donors",
        "reserve_items_accessed": 0,
        "reserve_model_forwards": 0,
        "pilot_only_simultaneous_bounds": simultaneous,
        "planning": planning_power(x, simultaneous["critical_value"]),
        "quality": diagnostic_summary(x),
        "descriptive_carrier_diagnostics": {
            pilot.CONTEXTS[ci][0]: diagnostic_summary(
                contrast_matrix(metrics["alias_margin_effect"], contexts=(ci,))
            )
            for ci in (1, 3)
        },
        "descriptive_token_length_diagnostics": {
            str(length): diagnostic_summary(x[lengths == length])
            for length in sorted(set(lengths))
        },
        "descriptive_other_endpoint_means": {
            name: dict(
                zip(
                    NAMES,
                    contrast_matrix(metrics[name]).mean(axis=0).tolist(),
                    strict=True,
                )
            )
            for name in (
                "alias_top1_effect",
                "donor_margin_effect",
                "codepoint_margin_effect",
                "codepoint_top1_effect",
            )
        },
        "interpretation": "Exploratory positive screen only; no prospective or emoji-specific causal claim.",
    }
    pilot.write_json(output, report)
    return {
        "status": report["status"],
        "planning": report["planning"],
        "report_sha256": pilot.sha256(output),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-analysis", type=Path, required=True)
    parser.add_argument(
        "--pilot-specification", type=Path, default=pilot.ROOT / pilot.SPEC
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            plan(args.pilot_analysis, args.pilot_specification, args.output), indent=2
        )
    )


if __name__ == "__main__":
    main()
