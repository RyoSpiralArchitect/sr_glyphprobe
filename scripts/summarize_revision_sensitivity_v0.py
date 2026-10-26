#!/usr/bin/env python3
"""Descriptive threshold/depth arithmetic from existing compact results only.

No model, tokenizer, target bank, bootstrap, permutation, or new p-value.
Historical decisions and input files are never rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    "models": "validation/t19_lexical_alias_unicode_control_v0/results/model_cell_results.json",
    "primary": "validation/t19_lexical_alias_unicode_control_v0/results/cross_model_primary_result.json",
    "depth": "validation/t19_lexical_alias_unicode_control_v0/results/depth_profiles.json",
    "fixed": "validation/t19_lexical_alias_component_causal_v0/results/causal_site_results.json",
    "optimized": "validation/t20_lexical_alias_optimized_subspace_causal_v0/results/causal_site_results.json",
}
FLOORS = (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10)
COMPONENTS = ("unrestricted", "matched")
LATE_DEPTHS = (0.75, 0.875, 1.0)


def summarize() -> dict:
    records = {}
    bindings = []
    for name, relative in INPUTS.items():
        data = (ROOT / relative).read_bytes()
        records[name] = json.loads(data)
        bindings.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest()})

    models = records["models"]["models"]
    roles = [row["model_role"] for row in models]
    if len(roles) != 9 or len(set(roles)) != 9:
        raise ValueError("Expected exactly nine unique model configurations")
    primary = records["primary"]["cross_model_primary"]
    core = set(primary["core_roles"])
    if len(core) != 4 or not core.issubset(roles):
        raise ValueError("Unexpected core roster")
    minima = {
        row["model_role"]: min(
            row["kind_components"]["emoji"][component]["alias_minus_codepoint_top1"]
            for component in COMPONENTS
        )
        for row in models
    }
    if not all(row["model_iut_p"] < 0.05 for row in models):
        raise ValueError(
            "Fixed statistical results differ from audited nine-model case"
        )

    threshold_rows = []
    for floor in FLOORS:
        passing = sorted(role for role, value in minima.items() if value >= floor)
        core_count = len(core.intersection(passing))
        threshold_rows.append(
            {
                "floor": floor,
                "models_meeting_both_observed_effect_floors": len(passing),
                "core_models_meeting_both_observed_effect_floors": core_count,
                "three_of_four_practical_conjunction": core_count >= 3,
                "passing_roles": passing,
            }
        )

    depth_rows = records["depth"]["rows"]
    depth_means = {}
    for role in roles:
        for depth in LATE_DEPTHS:
            selected = [
                r
                for r in depth_rows
                if r["model_role"] == role
                and r["glyph_kind"] == "emoji"
                and r["normalized_depth"] == depth
            ]
            contexts = {(r["carrier"], r["distance"]) for r in selected}
            if len(selected) != 8 or len(contexts) != 8:
                raise ValueError(f"Incomplete contexts for {role} / {depth}")
            depth_means[(role, depth)] = {
                component: math.fsum(
                    r[f"{component}_alias_minus_codepoint_top1"] for r in selected
                )
                / 8
                for component in COMPONENTS
            }
    depth_summaries = []
    for depths in ((0.75,), (0.875,), (1.0,), (0.875, 1.0), (0.75, 1.0), (0.75, 0.875)):
        values = {
            role: min(
                math.fsum(depth_means[(role, d)][c] for d in depths) / len(depths)
                for c in COMPONENTS
            )
            for role in roles
        }
        depth_summaries.append(
            {
                "included_depths": depths,
                "minimum_over_models_and_components": min(values.values()),
                "models_with_both_point_estimates_at_least_0p02": sum(
                    v >= 0.02 for v in values.values()
                ),
                "model_component_minima": values,
            }
        )

    causal = {}
    for arm, count in (("fixed", 6), ("optimized", 9)):
        sites = records[arm]["sites"]
        if len(sites) != count:
            raise ValueError(f"Unexpected site count: {arm}")
        causal[arm] = []
        for row in sites:
            lower = min(
                row["necessity_interval"]["lower_95"],
                row["sufficiency_interval"]["lower_95"],
            )
            causal[arm].append(
                {
                    "block_index": row["block_index"],
                    "site": row["site"],
                    "primary_site": row["primary_site"],
                    "minimum_stored_lower_bound": lower,
                    "stored_site_iut_p": row["site_iut_p"],
                    "both_stored_lower_bounds_strictly_positive": lower > 0,
                    "uncorrected_iut_below_0p05": row["site_iut_p"] < 0.05,
                    "stored_verdict": row.get("verdict"),
                }
            )

    return {
        "schema_version": 1,
        "status": "descriptive_arithmetic_from_saved_summaries",
        "new_model_forwards": 0,
        "new_resampling_draws": 0,
        "historical_decisions_modified": False,
        "interpretation": "Post-outcome sensitivity only. Statistical values are held fixed; no depth-specific significance or new confirmation is claimed. Calibration failures remain unresolved.",
        "inputs": bindings,
        "stored_cross_model_partial_conjunction_p": primary["partial_conjunction_p"],
        "largest_floor_supported_by_all_nine_point_estimates": min(minima.values()),
        "largest_floor_supported_by_three_core_point_estimates": sorted(
            (minima[r] for r in core), reverse=True
        )[2],
        "thresholds": threshold_rows,
        "late_depth_point_estimates": depth_summaries,
        "causal_stored_intervals_and_p_values": causal,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="New JSON file; refuses to overwrite"
    )
    args = parser.parse_args()
    result = summarize()
    serialized = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "sha256": hashlib.sha256(serialized.encode()).hexdigest(),
                    "status": result["status"],
                }
            )
        )
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
