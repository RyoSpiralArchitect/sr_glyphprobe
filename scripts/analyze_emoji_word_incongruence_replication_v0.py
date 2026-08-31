#!/usr/bin/env python3
"""Open the complete T15-B run and apply the frozen replication gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_emoji_word_incongruence_interaction_v0 as original  # noqa: E402
import emoji_word_incongruence_replication_v0 as t15  # noqa: E402


ANALYSIS_ID = "glyphprobe-emoji-word-incongruence-replication-analysis-v0"
R1_FAMILY = "R1_pooled_A1_prospective_replication"
A1_FAMILY = "A1_shared_response_fingerprint_true_minus_all_cross_axis_nulls"
FAMILIES = (
    R1_FAMILY,
    "A0_joint_additivity_residual_incongruent_minus_congruent",
    A1_FAMILY,
    "A2_response_energy_true_minus_cross_axis_null",
    "A3_source_direction_rms_true_minus_cross_axis_null",
    "A4_word_minus_emoji_main_response",
    "A5_source_order_sensitivity",
    "A6_depth_and_dose_heterogeneity",
)


class ReplicationAnalysisError(RuntimeError):
    """Raised when the complete T15-B analysis cannot be produced."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReplicationAnalysisError(message)


def _a0(run_root: Path) -> dict[str, Any]:
    values: dict[tuple[str, int, float, str, str], list[float]] = defaultdict(list)
    for row in original._source_rows(run_root, "source_metrics.jsonl"):
        if row["source_kind"] != "core_pair":
            continue
        key = (
            str(row["model_role"]),
            int(row["site_index"]),
            float(row["depth_fraction"]),
            str(row["axis_id"]),
            str(row["congruence"]),
        )
        values[key].append(float(row["joint_additivity_residual_rms"]))
    records = []
    expected_repeats = len(t15.SOURCE_ORDERS) * len(t15.wrappers()) * 2
    for base in sorted({key[:-1] for key in values}):
        congruent = values[(*base, "congruent")]
        incongruent = values[(*base, "incongruent")]
        _require(
            len(congruent) == len(incongruent) == expected_repeats,
            "T15-B A0 repeat count changed",
        )
        records.append(
            {
                "model": base[0],
                "site_index": base[1],
                "depth_fraction": base[2],
                "axis_id": base[3],
                "value": float(np.median(incongruent) - np.median(congruent)),
            }
        )
    return {
        "estimand": "median_incongruent_residual_rms_minus_median_congruent_residual_rms",
        "axis_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=("model", "site_index", "depth_fraction"),
            unit_field="axis_id",
            expected_units=len(t15.axes()),
            namespace="T15B_A0",
        ),
    }


def _fingerprint_for_shard(
    run_root: Path,
    role: str,
    site_index: int,
    kind: str,
) -> dict[tuple[str, float, int, int | None], tuple[float, int]]:
    directory = t15._response_directory(run_root, role, kind, site_index)
    rows = original._read_jsonl(directory / "response_ledger.jsonl")
    sketches = np.load(directory / "countsketch.npy", mmap_mode="r", allow_pickle=False)
    _require(sketches.shape[0] == len(rows), "Fingerprint ledger/sketch mismatch")
    grouped: dict[tuple[str, float, int, int | None, str], list[int]] = defaultdict(
        list
    )
    for index, row in enumerate(rows):
        shift = int(row["shift"]) if kind == "cross_axis_null" else None
        key = (
            str(row["target_id"]),
            float(row["magnitude"]),
            int(row["sign"]),
            shift,
            str(row["axis_id"]),
        )
        grouped[key].append(index)
    reduced: dict[tuple[str, float, int, int | None], dict[str, np.ndarray]] = (
        defaultdict(dict)
    )
    expected_repeats = len(t15.SOURCE_ORDERS) * len(t15.wrappers())
    for key, indices in grouped.items():
        _require(
            len(indices) == expected_repeats,
            f"Fingerprint repeat count changed: {key}",
        )
        base_key, axis = key[:-1], key[-1]
        _require(axis not in reduced[base_key], f"Duplicate fingerprint axis: {key}")
        reduced[base_key][axis] = np.median(sketches[indices], axis=0)
    output = {}
    for key, by_axis in reduced.items():
        _require(len(by_axis) == len(t15.axes()), f"Fingerprint axis count changed: {key}")
        matrix = np.stack([by_axis[name] for name in sorted(by_axis)])
        output[key] = original._pairwise_cosine_median(matrix)
    multiplier = (
        len(t15.panel()["cross_axis_cyclic_shifts"])
        if kind == "cross_axis_null"
        else 1
    )
    expected = (
        len(t15.targets())
        * len(t15._config()["intervention"]["magnitudes"])
        * len(t15._config()["intervention"]["signs"])
        * multiplier
    )
    _require(len(output) == expected, f"Fingerprint cell count changed: {kind}")
    return output


def _a1(run_root: Path) -> dict[str, Any]:
    records = []
    shifts = tuple(int(value) for value in t15.panel()["cross_axis_cyclic_shifts"])
    for role in t15.model_roles():
        for site_index in t15.SITE_INDICES:
            true = _fingerprint_for_shard(run_root, role, site_index, "true_conflict")
            cross = _fingerprint_for_shard(
                run_root, role, site_index, "cross_axis_null"
            )
            for target in t15.targets():
                for magnitude in t15._config()["intervention"]["magnitudes"]:
                    for sign in t15._config()["intervention"]["signs"]:
                        key = (str(target["id"]), float(magnitude), int(sign), None)
                        true_value, true_zeros = true[key]
                        controls = [
                            cross[
                                (
                                    str(target["id"]),
                                    float(magnitude),
                                    int(sign),
                                    shift,
                                )
                            ]
                            for shift in shifts
                        ]
                        control_value = float(np.median([item[0] for item in controls]))
                        records.append(
                            {
                                "model": role,
                                "site_index": site_index,
                                "depth_fraction": float(
                                    t15._config()["source_capture"]["depth_fractions"][
                                        t15.SITE_INDICES.index(site_index)
                                    ]
                                ),
                                "target_id": target["id"],
                                "magnitude": float(magnitude),
                                "sign": int(sign),
                                "true_fingerprint": true_value,
                                "cross_axis_fingerprint_median": control_value,
                                "cross_axis_controls": len(controls),
                                "zero_axis_vectors_true": true_zeros,
                                "zero_axis_vectors_cross_total": sum(
                                    item[1] for item in controls
                                ),
                                "value": true_value - control_value,
                            }
                        )
    return {
        "estimand": "median_pairwise_axis_countsketch_cosine_true_minus_median_of_all_seven_cross_axis_controls",
        "repeat_reduction": "coordinatewise_median_over_four_folds_and_two_source_orders",
        "zero_vector_cosine_policy": "zero_vector_contributes_zero_cosine",
        "target_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=(
                "model",
                "site_index",
                "depth_fraction",
                "magnitude",
                "sign",
            ),
            unit_field="target_id",
            expected_units=len(t15.targets()),
            namespace="T15B_A1",
        ),
    }


def _paired_response_family(
    left: Mapping[tuple[Any, ...], Mapping[str, float]],
    right: Mapping[tuple[Any, ...], Mapping[str, float]],
    *,
    family: str,
    estimand: str,
) -> dict[str, Any]:
    _require(set(left) == set(right), f"{family} paired cells changed")
    records = []
    for key in sorted(left):
        for endpoint in original.ENDPOINTS:
            records.append(
                {
                    "model": key[0],
                    "site_index": key[1],
                    "depth_fraction": key[2],
                    "target_id": key[3],
                    "magnitude": key[4],
                    "sign": key[5],
                    "endpoint": endpoint,
                    "value": float(left[key][endpoint] - right[key][endpoint]),
                }
            )
    return {
        "estimand": estimand,
        "target_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=(
                "model",
                "site_index",
                "depth_fraction",
                "magnitude",
                "sign",
                "endpoint",
            ),
            unit_field="target_id",
            expected_units=len(t15.targets()),
            namespace=f"T15B_{family}",
        ),
    }


def _a3(run_root: Path) -> dict[str, Any]:
    grouped: dict[tuple[str, int, float, str, str], list[float]] = defaultdict(list)
    for row in original._source_rows(run_root, "direction_catalog.jsonl"):
        if row["direction_kind"] not in {"true_conflict", "cross_axis_null"}:
            continue
        key = (
            str(row["model_role"]),
            int(row["site_index"]),
            float(row["depth_fraction"]),
            str(row["axis_id"]),
            str(row["direction_kind"]),
        )
        grouped[key].append(float(row["source_direction_rms"]))
    records = []
    repeats = len(t15.SOURCE_ORDERS) * len(t15.wrappers())
    cross_repeats = repeats * len(t15.panel()["cross_axis_cyclic_shifts"])
    for base_key in sorted({key[:-1] for key in grouped}):
        true = grouped[(*base_key, "true_conflict")]
        cross = grouped[(*base_key, "cross_axis_null")]
        _require(
            len(true) == repeats and len(cross) == cross_repeats,
            "T15-B A3 repeat count changed",
        )
        records.append(
            {
                "model": base_key[0],
                "site_index": base_key[1],
                "depth_fraction": base_key[2],
                "axis_id": base_key[3],
                "value": float(np.median(true) - np.median(cross)),
            }
        )
    return {
        "estimand": "median_true_source_direction_rms_minus_median_all_cross_axis_direction_rms",
        "axis_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=("model", "site_index", "depth_fraction"),
            unit_field="axis_id",
            expected_units=len(t15.axes()),
            namespace="T15B_A3",
        ),
    }


def _a5(run_root: Path) -> dict[str, Any]:
    reduced = original._response_reductions(
        run_root, "true_conflict", retain_order=True
    )
    records = []
    for base_key in sorted({key[:-1] for key in reduced}):
        emoji_first = reduced[(*base_key, "emoji_then_word")]
        word_first = reduced[(*base_key, "word_then_emoji")]
        for endpoint in original.ENDPOINTS:
            records.append(
                {
                    "model": base_key[0],
                    "site_index": base_key[1],
                    "depth_fraction": base_key[2],
                    "target_id": base_key[3],
                    "magnitude": base_key[4],
                    "sign": base_key[5],
                    "endpoint": endpoint,
                    "value": float(emoji_first[endpoint] - word_first[endpoint]),
                }
            )
    return {
        "estimand": "emoji_then_word_median_response_minus_word_then_emoji_median_response",
        "target_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=(
                "model",
                "site_index",
                "depth_fraction",
                "magnitude",
                "sign",
                "endpoint",
            ),
            unit_field="target_id",
            expected_units=len(t15.targets()),
            namespace="T15B_A5",
        ),
    }


def _a6(a1: Mapping[str, Any]) -> dict[str, Any]:
    lookup = {
        (
            row["model"],
            row["site_index"],
            row["target_id"],
            row["magnitude"],
            row["sign"],
        ): float(row["value"])
        for row in a1["target_estimands"]
    }
    primary = float(t15._config()["intervention"]["primary_magnitude"])
    lower = min(float(value) for value in t15._config()["intervention"]["magnitudes"])
    shallow_site, deep_site = t15.SITE_INDICES
    depths = t15._config()["source_capture"]["depth_fractions"]
    depth_records = []
    dose_records = []
    for role in t15.model_roles():
        for target in t15.targets():
            for sign in t15._config()["intervention"]["signs"]:
                shallow = lookup[(role, shallow_site, target["id"], primary, int(sign))]
                deep = lookup[(role, deep_site, target["id"], primary, int(sign))]
                depth_records.append(
                    {
                        "model": role,
                        "target_id": target["id"],
                        "sign": int(sign),
                        "magnitude": primary,
                        "contrast": f"depth_{depths[1]}_minus_{depths[0]}",
                        "value": deep - shallow,
                    }
                )
                for site_index in t15.SITE_INDICES:
                    low = lookup[(role, site_index, target["id"], lower, int(sign))]
                    high = lookup[(role, site_index, target["id"], primary, int(sign))]
                    dose_records.append(
                        {
                            "model": role,
                            "site_index": site_index,
                            "depth_fraction": float(
                                depths[t15.SITE_INDICES.index(site_index)]
                            ),
                            "target_id": target["id"],
                            "sign": int(sign),
                            "contrast": f"magnitude_{primary}_minus_{lower}",
                            "value": high - low,
                        }
                    )
    return {
        "basis": "A1 target-level true-minus-all-cross fingerprint estimand",
        "depth_target_estimands": depth_records,
        "depth_summary": original._summarize_records(
            depth_records,
            cell_fields=("model", "sign", "magnitude", "contrast"),
            unit_field="target_id",
            expected_units=len(t15.targets()),
            namespace="T15B_A6_depth",
        ),
        "dose_target_estimands": dose_records,
        "dose_summary": original._summarize_records(
            dose_records,
            cell_fields=(
                "model",
                "site_index",
                "depth_fraction",
                "sign",
                "contrast",
            ),
            unit_field="target_id",
            expected_units=len(t15.targets()),
            namespace="T15B_A6_dose",
        ),
    }


def _r1(a1: Mapping[str, Any]) -> dict[str, Any]:
    primary = float(t15._config()["intervention"]["primary_magnitude"])
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in a1["target_estimands"]:
        if float(row["magnitude"]) == primary:
            grouped[(str(row["model"]), str(row["target_id"]))].append(
                float(row["value"])
            )
    records = []
    expected_within_target = len(t15.SITE_INDICES) * len(
        t15._config()["intervention"]["signs"]
    )
    for (role, target_id), values in sorted(grouped.items()):
        _require(
            len(values) == expected_within_target,
            f"R1 within-target cell count changed: {role}/{target_id}",
        )
        records.append(
            {
                "model": role,
                "target_id": target_id,
                "magnitude": primary,
                "within_target_cells": expected_within_target,
                "value": float(np.median(values)),
            }
        )
    config = t15._config()["analysis"]
    summaries = []
    for role in t15.model_roles():
        values = [row["value"] for row in records if row["model"] == role]
        summary = original.unit_summary(
            values,
            expected_units=len(t15.targets()),
            replicates=int(config["bootstrap_replicates"]),
            seed=original._stable_seed(
                int(config["bootstrap_seed"]), "T15B_R1", (role, primary)
            ),
        )
        lower = float(summary["bootstrap_95_percent_interval"][0])
        summaries.append(
            {
                "model": role,
                "magnitude": primary,
                "bonferroni_one_sided_alpha": 0.025,
                "lower_bound_above_zero": lower > 0.0,
                **summary,
            }
        )
    supported = all(row["lower_bound_above_zero"] for row in summaries)
    return {
        "estimand": "per_model_median_across_targets_of_within_target_median_A1_over_two_depths_and_two_signs",
        "target_estimands": records,
        "summary": summaries,
        "decision_rule": "both_frozen_model_2p5_percentile_bootstrap_lower_bounds_above_zero",
        "multiplicity": "Bonferroni one-sided alpha 0.025 per model; family alpha at most 0.05",
        "replication_support": supported,
        "decision": "support" if supported else "not_supported",
        "semantic_understanding_claim_authorized": False,
        "causal_claim_authorized": False,
    }


def analyze(run_root: Path, output: Path) -> dict[str, Any]:
    with t15.profile_scope():
        saved = {
            "t15": original.t15,
            "ANALYSIS_ID": original.ANALYSIS_ID,
            "_a0": original._a0,
            "_fingerprint_for_shard": original._fingerprint_for_shard,
            "_a1": original._a1,
            "_paired_response_family": original._paired_response_family,
            "_a3": original._a3,
            "_a5": original._a5,
            "_a6": original._a6,
            "_write_json": original._write_json,
        }

        def writer(path: Path, value: Mapping[str, Any]) -> None:
            result = dict(value)
            families = dict(result["families"])
            a1 = families.pop(
                "A1_shared_response_fingerprint_true_minus_cross_axis_null"
            )
            families = {
                R1_FAMILY: _r1(a1),
                "A0_joint_additivity_residual_incongruent_minus_congruent": families[
                    "A0_joint_additivity_residual_incongruent_minus_congruent"
                ],
                A1_FAMILY: a1,
                "A2_response_energy_true_minus_cross_axis_null": families[
                    "A2_response_energy_true_minus_cross_axis_null"
                ],
                "A3_source_direction_rms_true_minus_cross_axis_null": families[
                    "A3_source_direction_rms_true_minus_cross_axis_null"
                ],
                "A4_word_minus_emoji_main_response": families[
                    "A4_word_minus_emoji_main_response"
                ],
                "A5_source_order_sensitivity": families[
                    "A5_source_order_sensitivity"
                ],
                "A6_depth_and_dose_heterogeneity": families[
                    "A6_depth_and_dose_heterogeneity"
                ],
            }
            result.update(
                {
                    "analysis_id": ANALYSIS_ID,
                    "status": "complete_prospective_holdout_replication_analysis",
                    "families": families,
                    "family_order": list(FAMILIES),
                    "primary_replication_family": R1_FAMILY,
                    "replication_gate": families[R1_FAMILY]["decision"],
                    "replication_support": families[R1_FAMILY][
                        "replication_support"
                    ],
                    "confirmatory_status": False,
                    "semantic_understanding_claim_authorized": False,
                    "causal_claim_authorized": False,
                }
            )
            saved["_write_json"](path, result)

        original.t15 = t15
        original.ANALYSIS_ID = ANALYSIS_ID
        original._a0 = _a0
        original._fingerprint_for_shard = _fingerprint_for_shard
        original._a1 = _a1
        original._paired_response_family = _paired_response_family
        original._a3 = _a3
        original._a5 = _a5
        original._a6 = _a6
        original._write_json = writer
        try:
            original.analyze(run_root, output)
            return original._read_json(output)
        finally:
            for name, value in saved.items():
                setattr(original, name, value)


def validate_output(path: Path) -> dict[str, Any]:
    with t15.profile_scope():
        t15.base.audit_freeze()
        value = original._read_json(path)
    _require(value.get("analysis_id") == ANALYSIS_ID, "Analysis ID changed")
    _require(value.get("family_order") == list(FAMILIES), "Analysis families changed")
    _require(
        value.get("status") == "complete_prospective_holdout_replication_analysis",
        "Analysis status changed",
    )
    r1 = value["families"][R1_FAMILY]
    _require(len(r1["summary"]) == len(t15.model_roles()), "R1 model count changed")
    observed = all(row["lower_bound_above_zero"] for row in r1["summary"])
    _require(observed == bool(value["replication_support"]), "R1 decision changed")
    _require(
        value.get("confirmatory_status") is False
        and value.get("semantic_understanding_claim_authorized") is False
        and value.get("causal_claim_authorized") is False,
        "T15-B claim boundary changed",
    )
    return {
        "status": "pass",
        "analysis_id": ANALYSIS_ID,
        "analysis_output_sha256": original._sha256(path),
        "complete_families": list(FAMILIES),
        "replication_gate": value["replication_gate"],
        "replication_support": value["replication_support"],
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    run = commands.add_parser("analyze")
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    validate = commands.add_parser("validate-output")
    validate.add_argument("--path", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "analyze":
        result = analyze(args.run_root, args.output)
    else:
        result = validate_output(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
