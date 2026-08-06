#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import orjson

from glyphprobe.config import load_experiment_config
from glyphprobe.io import stable_hash, write_json
from glyphprobe.provenance import implementation_receipt, input_hash_receipt


def _read_json(path: Path) -> dict[str, Any]:
    return orjson.loads(path.read_bytes())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = orjson.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Expected object at {path}:{line_no}")
            rows.append(value)
    return rows


def _median(rows: Iterable[dict[str, Any]], field: str) -> float:
    return float(statistics.median(float(row[field]) for row in rows))


def _close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def _quartiles(values: list[float]) -> tuple[float, float]:
    cuts = statistics.quantiles(values, n=4, method="inclusive")
    return float(cuts[0]), float(cuts[2])


def _fingerprint_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    advantages = [float(row["emoji_advantage_over_random"]) for row in rows]
    random_separations = [float(row["random_separation"]) for row in rows]
    q1, q3 = _quartiles(random_separations)
    iqr = q3 - q1
    low, high = q1 - 3.0 * iqr, q3 + 3.0 * iqr
    three_iqr_extremes = [
        {
            "layer": row["layer"],
            "seed": row["seed"],
            "strength": row["strength"],
            "random_separation": row["random_separation"],
            "emoji_advantage_over_random": row["emoji_advantage_over_random"],
        }
        for row in rows
        if not low <= float(row["random_separation"]) <= high
    ]
    extreme_keys = {
        (row["layer"], row["seed"], row["strength"])
        for row in three_iqr_extremes
    }
    filtered_advantages = [
        float(row["emoji_advantage_over_random"])
        for row in rows
        if (row["layer"], row["seed"], row["strength"]) not in extreme_keys
    ]
    by_layer: dict[str, dict[str, Any]] = {}
    for layer in sorted({int(row["layer"]) for row in rows}):
        layer_rows = [row for row in rows if int(row["layer"]) == layer]
        by_layer[str(layer)] = {
            "count": len(layer_rows),
            "median_advantage": _median(layer_rows, "emoji_advantage_over_random"),
            "min_advantage": min(float(row["emoji_advantage_over_random"]) for row in layer_rows),
            "max_advantage": max(float(row["emoji_advantage_over_random"]) for row in layer_rows),
        }
    by_seed: dict[str, dict[str, Any]] = {}
    for seed in sorted({int(row["seed"]) for row in rows}):
        seed_rows = [row for row in rows if int(row["seed"]) == seed]
        by_seed[str(seed)] = {
            "count": len(seed_rows),
            "median_advantage": _median(seed_rows, "emoji_advantage_over_random"),
            "positive_count": sum(
                float(row["emoji_advantage_over_random"]) > 0 for row in seed_rows
            ),
        }
    by_strength: dict[str, dict[str, Any]] = {}
    for strength in sorted({float(row["strength"]) for row in rows}):
        strength_rows = [row for row in rows if float(row["strength"]) == strength]
        by_strength[str(strength)] = {
            "count": len(strength_rows),
            "median_advantage": _median(
                strength_rows, "emoji_advantage_over_random"
            ),
            "positive_count": sum(
                float(row["emoji_advantage_over_random"]) > 0
                for row in strength_rows
            ),
        }
    p_values = [float(row["emoji_label_permutation_p"]) for row in rows]
    return {
        "row_count": len(rows),
        "advantage": {
            "median": float(statistics.median(advantages)),
            "min": float(min(advantages)),
            "max": float(max(advantages)),
            "positive_count": sum(value > 0 for value in advantages),
            "positive_rate": sum(value > 0 for value in advantages) / len(advantages),
            "median_without_three_iqr_extremes": (
                float(statistics.median(filtered_advantages)) if filtered_advantages else None
            ),
            "by_layer": by_layer,
            "by_seed": by_seed,
            "by_strength": by_strength,
        },
        "random_separation": {
            "median": float(statistics.median(random_separations)),
            "q1": q1,
            "q3": q3,
            "three_iqr_bounds": [low, high],
            "three_iqr_extremes": three_iqr_extremes,
            "interpretation": (
                "Random-control separation is heterogeneous across cells. The predefined "
                "three-IQR diagnostic does not itself license removing any cell."
            ),
        },
        "permutation_screen": {
            "median_p": float(statistics.median(p_values)),
            "minimum_p": float(min(p_values)),
            "at_minimum_count": sum(value == min(p_values) for value in p_values),
            "note": "Screening p-values are not multiplicity-corrected global significance tests.",
        },
    }


def _integrity_outcome(all_pass: bool) -> dict[str, Any]:
    if all_pass:
        return {
            "status": "ready_with_caveats",
            "scientific_result": True,
            "decision": (
                "Artifact is internally consistent and suitable for designing a targeted "
                "causal follow-up, with the stated caveats."
            ),
        }
    return {
        "status": "needs_revision",
        "scientific_result": False,
        "decision": "Do not use the artifact until failed integrity checks are resolved.",
    }


def validate(run_dir: Path, config_path: Path | None = None) -> dict[str, Any]:
    receipt = _read_json(run_dir / "receipt.json")
    summary = _read_json(run_dir / "summary.json")
    plan = _read_json(run_dir / "plan.json")
    interventions = _read_jsonl(run_dir / "interventions.jsonl")
    fingerprint_rows = _read_jsonl(run_dir / "fingerprint_summary.jsonl")
    cross_seed_rows = _read_jsonl(run_dir / "cross_seed_fingerprint_summary.jsonl")
    scalar_rows = _read_jsonl(run_dir / "scalar_balance_summary.jsonl")
    dose_rows = _read_jsonl(run_dir / "dose_response_summary.jsonl")
    sign_rows = _read_jsonl(run_dir / "sign_flip_summary.jsonl")
    source_item_rows = _read_jsonl(run_dir / "source_item_metrics.jsonl")
    baseline_rows = _read_jsonl(run_dir / "target_baselines.jsonl")
    tokenization_rows = _read_jsonl(run_dir / "tokenization.jsonl")

    expected_interventions = sum(
        int(plan[name])
        for name in (
            "emoji_intervention_calls",
            "random_control_calls",
            "generic_emoji_control_calls",
            "zero_hook_control_calls",
            "iso_kl_evaluation_calls",
        )
    )
    expected_condition_counts = {
        "emoji": int(plan["emoji_intervention_calls"]),
        "random": int(plan["random_control_calls"]),
        "generic_emoji": int(plan["generic_emoji_control_calls"]),
        "zero": int(plan["zero_hook_control_calls"]),
    }
    actual_condition_counts = Counter(str(row.get("condition_type")) for row in interventions)
    task_ids = [str(row.get("task_id")) for row in interventions]
    required_fields = {
        "task_id",
        "seed",
        "layer",
        "condition_type",
        "condition_id",
        "strength",
        "sign",
        "target_id",
        "calibration",
        "distribution",
        "activation",
        "scale",
    }
    missing_required = sum(not required_fields.issubset(row) for row in interventions)
    task_id_mismatches = 0
    nonfinite_core = 0
    for row in interventions:
        payload = {
            "seed": row["seed"],
            "layer": row["layer"],
            "condition_type": row["condition_type"],
            "condition_id": row["condition_id"],
            "strength": row["strength"],
            "sign": row["sign"],
            "target_id": row["target_id"],
            "calibration": row["calibration"],
        }
        if stable_hash(payload, length=24) != row["task_id"]:
            task_id_mismatches += 1
        core_values = (
            row["latency_ms"],
            row["distribution"]["logit_delta_rms"],
            row["distribution"]["kl_base_to_intervened"],
            row["activation"]["actual_activation_delta_rms"],
            row["scale"]["perturbation_to_target_rms"],
        )
        nonfinite_core += sum(not math.isfinite(float(value)) for value in core_values)

    zero_rows = [row for row in interventions if row["condition_type"] == "zero"]
    emoji_scalar_rows = [row for row in scalar_rows if row["condition_type"] == "emoji"]
    emoji_dose_rows = [row for row in dose_rows if row["condition_type"] == "emoji"]
    recomputed = {
        "intervention_record_count": len(interventions),
        "random_control_count": actual_condition_counts["random"],
        "zero_hook_control_count": len(zero_rows),
        "zero_hook_max_logit_delta_rms": max(
            float(row["distribution"]["logit_delta_rms"]) for row in zero_rows
        ),
        "zero_hook_max_activation_delta_rms": max(
            float(row["activation"]["actual_activation_delta_rms"]) for row in zero_rows
        ),
        "median_direction_replicate_alignment": _median(
            source_item_rows, "direction_replicate_alignment_mean"
        ),
        "emoji_fingerprint_advantage": _median(
            fingerprint_rows, "emoji_advantage_over_random"
        ),
        "median_emoji_label_permutation_p": _median(
            fingerprint_rows, "emoji_label_permutation_p"
        ),
        "cross_seed_fingerprint_advantage": _median(
            cross_seed_rows, "cross_seed_advantage_over_random"
        ),
        "median_emoji_perturbation_ratio_max_abs_error": _median(
            emoji_scalar_rows, "perturbation_ratio_max_abs_error"
        ),
        "median_emoji_kl_dose_monotonicity": _median(
            emoji_dose_rows, "kl_adjacent_nondecreasing_mean"
        ),
        "median_sign_antisymmetry": _median(sign_rows, "antisymmetry_score_median"),
    }
    summary_discrepancies = {
        key: {"summary": summary.get(key), "recomputed": value}
        for key, value in recomputed.items()
        if not (
            summary.get(key) == value
            if isinstance(value, int)
            else _close(float(summary.get(key)), float(value))
        )
    }

    if config_path is None:
        candidate = Path("configs") / str(receipt["config_path"])
        config_path = candidate if candidate.is_file() else None
    if config_path is None:
        current_input_hashes: dict[str, str] = {}
    else:
        _, current_inputs = load_experiment_config(config_path)
        current_input_hashes = input_hash_receipt(current_inputs.input_paths)
    implementation_now = implementation_receipt()
    primary_tokenization = [
        row for row in tokenization_rows if row.get("emoji_id") != "__neutral__"
    ]
    neutral_rows = [row for row in tokenization_rows if row.get("emoji_id") == "__neutral__"]
    wrapper_mismatches = [
        row["emoji_id"]
        for row in primary_tokenization
        if any(
            len({
                int(item["token_count"])
                for candidate in primary_tokenization
                for item in candidate["wrapper_tokenization"]
                if item["wrapper_id"] == wrapper["wrapper_id"]
            })
            != 1
            for wrapper in row["wrapper_tokenization"]
        )
    ]
    baseline_ids = [str(row["target_id"]) for row in baseline_rows]
    prompt_hashes = [str(row["prompt_hash"]) for row in baseline_rows]

    checks = [
        {"id": "receipt_complete", "pass": receipt["status"] == "complete"},
        {"id": "errors_absent", "pass": not (run_dir / "errors.jsonl").exists()},
        {
            "id": "input_hashes_match",
            "pass": current_input_hashes == receipt["input_hashes"],
            "value": current_input_hashes,
        },
        {
            "id": "implementation_hash_matches",
            "pass": implementation_now["source_tree_sha256"]
            == receipt["implementation"]["source_tree_sha256"],
            "value": implementation_now,
        },
        {
            "id": "intervention_count_matches_plan",
            "pass": len(interventions) == expected_interventions,
            "value": {"actual": len(interventions), "expected": expected_interventions},
        },
        {
            "id": "condition_counts_match_plan",
            "pass": dict(actual_condition_counts) == expected_condition_counts,
            "value": {
                "actual": dict(actual_condition_counts),
                "expected": expected_condition_counts,
            },
        },
        {
            "id": "task_ids_unique",
            "pass": len(task_ids) == len(set(task_ids)),
            "value": {"rows": len(task_ids), "unique": len(set(task_ids))},
        },
        {
            "id": "task_ids_recompute",
            "pass": task_id_mismatches == 0,
            "value": task_id_mismatches,
        },
        {
            "id": "required_fields_complete",
            "pass": missing_required == 0,
            "value": missing_required,
        },
        {"id": "core_metrics_finite", "pass": nonfinite_core == 0, "value": nonfinite_core},
        {
            "id": "targets_unique_and_complete",
            "pass": (
                len(baseline_ids) == int(plan["target_count"])
                and len(baseline_ids) == len(set(baseline_ids))
                and len(prompt_hashes) == len(set(prompt_hashes))
            ),
            "value": {
                "rows": len(baseline_ids),
                "unique_ids": len(set(baseline_ids)),
                "unique_prompt_hashes": len(set(prompt_hashes)),
            },
        },
        {
            "id": "primary_token_count_balance",
            "pass": len({int(row["raw_token_count"]) for row in primary_tokenization}) == 1,
            "value": [int(row["raw_token_count"]) for row in primary_tokenization],
        },
        {
            "id": "wrapper_token_count_balance",
            "pass": not wrapper_mismatches,
            "value": sorted(set(wrapper_mismatches)),
        },
        {
            "id": "headline_metrics_recompute",
            "pass": not summary_discrepancies,
            "value": {"recomputed": recomputed, "discrepancies": summary_discrepancies},
        },
        {
            "id": "readiness_consistent",
            "pass": (
                summary["readiness"]["passed"] == 11
                and summary["readiness"]["total"] == 11
                and all(bool(row["pass"]) for row in summary["readiness"]["checks"])
                and summary["causal_claim_authorized"] is False
            ),
            "value": summary["readiness"],
        },
    ]

    fingerprint_profile = _fingerprint_profile(fingerprint_rows)
    finished = datetime.fromisoformat(receipt["finished_at"])
    started = datetime.fromisoformat(receipt["started_at"])
    all_pass = all(bool(check["pass"]) for check in checks)
    outcome = _integrity_outcome(all_pass)
    return {
        "schema_version": 1,
        **outcome,
        "run_id": receipt["run_id"],
        "run_dir": receipt["run_id"],
        "as_of": receipt["finished_at"],
        "runtime_seconds": (finished - started).total_seconds(),
        "intended_use": "pre-causal activation screening only",
        "causal_claim_authorized": False,
        "checks": checks,
        "passed": sum(bool(check["pass"]) for check in checks),
        "total": len(checks),
        "recomputed_headlines": recomputed,
        "fingerprint_profile": fingerprint_profile,
        "target_group_counts": dict(Counter(str(row["group"]) for row in baseline_rows)),
        "tokenization_profile": {
            "primary_count": len(primary_tokenization),
            "primary_token_counts": [
                int(row["raw_token_count"]) for row in primary_tokenization
            ],
            "neutral_token_count": (
                int(neutral_rows[0]["raw_token_count"]) if neutral_rows else None
            ),
            "distinct_primary_token_sequences": len(
                {tuple(row["raw_token_ids"]) for row in primary_tokenization}
            ),
            "blue_circle_prefix_differs": any(
                row.get("emoji_id") == "blue_circle"
                and row.get("raw_token_ids", [None, None])[1] != 253
                for row in primary_tokenization
            ),
        },
        "caveats": [
            "This is a pre-causal map; it does not identify glyph meaning, a circuit, or a causal path.",
            "The full pipeline was run only on MLX. Torch/MPS parity is adapter-level across fixed prompts, layers, and vectors, not a duplicate 14,208-record run.",
            "Primary glyph token counts are balanced, but token identities are not: blue_circle has a different middle token prefix, and the neutral glyph is one token versus three for primaries.",
            "Permutation p-values are screening flags at a finite 1/1001 floor and are not multiplicity-corrected global significance tests.",
            "Fingerprint advantage is heterogeneous at cell level (including non-positive cells); use the median and cross-seed aggregate rather than cherry-picking the maximum row.",
            "Seeds are repeated direction estimates, not independent observational units; target prompts are the principal sampling clusters.",
            "Iso-KL, SAE, generation, resid_pre, attn_out, mlp_out, and path-level causal tests were not run.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a completed GlyphProbe standard run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    result = validate(run_dir, args.config.resolve() if args.config else None)
    write_json(args.output.resolve(), result)
    print(f"status={result['status']}")
    print(f"checks={result['passed']}/{result['total']}")
    print(f"output={args.output.resolve()}")
    return 0 if result["status"] == "ready_with_caveats" else 1


if __name__ == "__main__":
    raise SystemExit(main())
