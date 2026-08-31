#!/usr/bin/env python3
"""Open the complete T15-A run and compute every frozen descriptive family."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import uuid
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import emoji_word_incongruence_interaction_v0 as t15  # noqa: E402


ANALYSIS_ID = "glyphprobe-emoji-word-incongruence-interaction-analysis-v0"
SCHEMA_VERSION = 1
ENDPOINTS = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
FAMILIES = (
    "A0_joint_additivity_residual_incongruent_minus_congruent",
    "A1_shared_response_fingerprint_true_minus_cross_axis_null",
    "A2_response_energy_true_minus_cross_axis_null",
    "A3_source_direction_rms_true_minus_cross_axis_null",
    "A4_word_minus_emoji_main_response",
    "A5_source_order_sensitivity",
    "A6_depth_and_dose_heterogeneity",
)


class InteractionAnalysisError(RuntimeError):
    """Raised when a complete frozen T15-A analysis cannot be produced."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InteractionAnalysisError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            _require(
                isinstance(value, dict),
                f"Invalid JSONL row: {path}:{line_number}",
            )
            rows.append(value)
    return rows


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"Refusing to overwrite T15-A analysis: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    stage.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(stage, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def endpoint_value(row: Mapping[str, Any], endpoint: str) -> float:
    _require(endpoint in ENDPOINTS, f"Unknown T15-A endpoint: {endpoint}")
    if endpoint == "entropy_change":
        value = float(row["intervened_entropy"]) - float(row["baseline_entropy"])
    elif endpoint == "argmax_flip_rate":
        _require(isinstance(row.get("argmax_flip"), bool), "argmax_flip changed")
        value = float(row["argmax_flip"])
    else:
        value = float(row[endpoint])
    _require(math.isfinite(value), f"Nonfinite endpoint: {endpoint}")
    return value


def _stable_seed(base: int, namespace: str, key: Sequence[Any]) -> int:
    payload = json.dumps(
        [base, namespace, *key], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def unit_summary(
    values: Sequence[float],
    *,
    expected_units: int,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    _require(array.shape == (expected_units,), "T15-A unit cell is incomplete")
    _require(bool(np.isfinite(array).all()), "T15-A unit cell is nonfinite")
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 1000):
        stop = min(start + 1000, replicates)
        indices = rng.integers(
            0,
            expected_units,
            size=(stop - start, expected_units),
        )
        samples[start:stop] = np.median(array[indices], axis=1)
    low, high = np.quantile(samples, (0.025, 0.975))
    return {
        "unit_rows": expected_units,
        "aggregate": "median",
        "median": float(np.median(array)),
        "mean": float(np.mean(array)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
        "bootstrap_95_percent_interval": [float(low), float(high)],
        "bootstrap_replicates": replicates,
    }


def _summarize_records(
    records: Sequence[Mapping[str, Any]],
    *,
    cell_fields: Sequence[str],
    unit_field: str,
    expected_units: int,
    namespace: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in records:
        key = tuple(row[field] for field in cell_fields)
        unit = str(row[unit_field])
        _require(unit not in grouped[key], f"Duplicate T15-A unit: {key}/{unit}")
        grouped[key][unit] = float(row["value"])
    config = t15._config()["analysis"]
    replicates = int(config["bootstrap_replicates"])
    base_seed = int(config["bootstrap_seed"])
    output = []
    for key, by_unit in sorted(grouped.items()):
        _require(len(by_unit) == expected_units, f"Incomplete T15-A cell: {key}")
        ordered = [by_unit[name] for name in sorted(by_unit)]
        output.append(
            {
                **dict(zip(cell_fields, key, strict=True)),
                **unit_summary(
                    ordered,
                    expected_units=expected_units,
                    replicates=replicates,
                    seed=_stable_seed(base_seed, namespace, key),
                ),
            }
        )
    _require(bool(output), f"No T15-A cells summarized: {namespace}")
    return output


def _source_rows(run_root: Path, filename: str) -> list[dict[str, Any]]:
    rows = []
    for role in t15.model_roles():
        directory = t15._source_directory(run_root, role)
        rows.extend(_read_jsonl(directory / filename))
    return rows


def _a0(run_root: Path) -> dict[str, Any]:
    values: dict[tuple[str, int, float, str, str], list[float]] = defaultdict(list)
    for row in _source_rows(run_root, "source_metrics.jsonl"):
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
    bases = {key[:-1] for key in values}
    for base in sorted(bases):
        congruent = values[(*base, "congruent")]
        incongruent = values[(*base, "incongruent")]
        _require(len(congruent) == len(incongruent) == 8, "A0 repeat count changed")
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
        "summary": _summarize_records(
            records,
            cell_fields=("model", "site_index", "depth_fraction"),
            unit_field="axis_id",
            expected_units=8,
            namespace="A0",
        ),
    }


def _pairwise_cosine_median(vectors: np.ndarray) -> tuple[float, int]:
    value = np.asarray(vectors, dtype=np.float64)
    _require(value.ndim == 2 and value.shape[0] == 8, "Fingerprint axis matrix changed")
    norms = np.linalg.norm(value, axis=1)
    zero_count = int(np.sum(norms <= 0.0))
    safe = np.where(norms > 0.0, norms, 1.0)
    normalized = value / safe[:, None]
    similarities = normalized @ normalized.T
    upper = similarities[np.triu_indices(8, 1)]
    _require(upper.shape == (28,), "Fingerprint pair count changed")
    return float(np.median(upper)), zero_count


def _fingerprint_for_shard(
    run_root: Path,
    role: str,
    site_index: int,
    kind: str,
) -> dict[tuple[str, float, int, int | None], tuple[float, int]]:
    directory = t15._response_directory(run_root, role, kind, site_index)
    rows = _read_jsonl(directory / "response_ledger.jsonl")
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
    for key, indices in grouped.items():
        _require(len(indices) == 8, f"Fingerprint repeat count changed: {key}")
        base, axis = key[:-1], key[-1]
        _require(axis not in reduced[base], f"Duplicate fingerprint axis: {key}")
        reduced[base][axis] = np.median(sketches[indices], axis=0)
    output = {}
    for key, by_axis in reduced.items():
        _require(len(by_axis) == 8, f"Fingerprint axis count changed: {key}")
        matrix = np.stack([by_axis[name] for name in sorted(by_axis)])
        output[key] = _pairwise_cosine_median(matrix)
    expected = 32 * 2 * 2 * (3 if kind == "cross_axis_null" else 1)
    _require(len(output) == expected, f"Fingerprint cell count changed: {kind}")
    return output


def _a1(run_root: Path) -> dict[str, Any]:
    records = []
    for role in t15.model_roles():
        for site_index in t15.SITE_INDICES:
            true = _fingerprint_for_shard(run_root, role, site_index, "true_conflict")
            cross = _fingerprint_for_shard(
                run_root, role, site_index, "cross_axis_null"
            )
            for target in t15.targets():
                for magnitude in t15._config()["intervention"]["magnitudes"]:
                    for sign in t15._config()["intervention"]["signs"]:
                        true_value, true_zeros = true[
                            (str(target["id"]), float(magnitude), int(sign), None)
                        ]
                        controls = [
                            cross[
                                (
                                    str(target["id"]),
                                    float(magnitude),
                                    int(sign),
                                    int(shift),
                                )
                            ]
                            for shift in t15.panel()["cross_axis_cyclic_shifts"]
                        ]
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
                                "cross_axis_fingerprint_median": float(
                                    np.median([item[0] for item in controls])
                                ),
                                "zero_axis_vectors_true": true_zeros,
                                "zero_axis_vectors_cross_total": sum(
                                    item[1] for item in controls
                                ),
                                "value": true_value
                                - float(np.median([item[0] for item in controls])),
                            }
                        )
    summary = _summarize_records(
        records,
        cell_fields=(
            "model",
            "site_index",
            "depth_fraction",
            "magnitude",
            "sign",
        ),
        unit_field="target_id",
        expected_units=32,
        namespace="A1",
    )
    return {
        "estimand": "median_pairwise_axis_countsketch_cosine_true_minus_median_of_three_cross_axis_controls",
        "repeat_reduction": "coordinatewise_median_over_four_folds_and_two_source_orders",
        "zero_vector_cosine_policy": "zero_vector_contributes_zero_cosine",
        "target_estimands": records,
        "summary": summary,
    }


def _response_reductions(
    run_root: Path,
    kind: str,
    *,
    retain_order: bool = False,
) -> dict[tuple[Any, ...], dict[str, float]]:
    output: dict[tuple[Any, ...], dict[str, float]] = {}
    for role in t15.model_roles():
        for site_index in t15.SITE_INDICES:
            directory = t15._response_directory(run_root, role, kind, site_index)
            grouped: dict[tuple[Any, ...], dict[str, list[float]]] = defaultdict(
                lambda: defaultdict(list)
            )
            for row in _read_jsonl(directory / "response_ledger.jsonl"):
                key: tuple[Any, ...] = (
                    role,
                    site_index,
                    float(row["depth_fraction"]),
                    str(row["target_id"]),
                    float(row["magnitude"]),
                    int(row["sign"]),
                )
                if retain_order:
                    key = (*key, str(row["source_order"]))
                for endpoint in ENDPOINTS:
                    grouped[key][endpoint].append(endpoint_value(row, endpoint))
            for key, by_endpoint in grouped.items():
                _require(key not in output, f"Duplicate response cell: {kind}/{key}")
                output[key] = {
                    endpoint: float(np.median(values))
                    for endpoint, values in by_endpoint.items()
                }
    return output


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
        for endpoint in ENDPOINTS:
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
        "summary": _summarize_records(
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
            expected_units=32,
            namespace=family,
        ),
    }


def _a3(run_root: Path) -> dict[str, Any]:
    grouped: dict[tuple[str, int, float, str, str], list[float]] = defaultdict(list)
    for row in _source_rows(run_root, "direction_catalog.jsonl"):
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
    bases = {key[:-1] for key in grouped}
    for base in sorted(bases):
        true = grouped[(*base, "true_conflict")]
        cross = grouped[(*base, "cross_axis_null")]
        _require(len(true) == 8 and len(cross) == 24, "A3 repeat count changed")
        records.append(
            {
                "model": base[0],
                "site_index": base[1],
                "depth_fraction": base[2],
                "axis_id": base[3],
                "value": float(np.median(true) - np.median(cross)),
            }
        )
    return {
        "estimand": "median_true_source_direction_rms_minus_median_cross_axis_direction_rms",
        "axis_estimands": records,
        "summary": _summarize_records(
            records,
            cell_fields=("model", "site_index", "depth_fraction"),
            unit_field="axis_id",
            expected_units=8,
            namespace="A3",
        ),
    }


def _a5(run_root: Path) -> dict[str, Any]:
    reduced = _response_reductions(
        run_root,
        "true_conflict",
        retain_order=True,
    )
    bases = {key[:-1] for key in reduced}
    records = []
    for base in sorted(bases):
        emoji_first = reduced[(*base, "emoji_then_word")]
        word_first = reduced[(*base, "word_then_emoji")]
        for endpoint in ENDPOINTS:
            records.append(
                {
                    "model": base[0],
                    "site_index": base[1],
                    "depth_fraction": base[2],
                    "target_id": base[3],
                    "magnitude": base[4],
                    "sign": base[5],
                    "endpoint": endpoint,
                    "value": float(emoji_first[endpoint] - word_first[endpoint]),
                }
            )
    return {
        "estimand": "emoji_then_word_median_response_minus_word_then_emoji_median_response",
        "target_estimands": records,
        "summary": _summarize_records(
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
            expected_units=32,
            namespace="A5",
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
    depth_records = []
    dose_records = []
    for role in t15.model_roles():
        for target in t15.targets():
            for sign in t15._config()["intervention"]["signs"]:
                shallow = lookup[(role, 6, target["id"], primary, int(sign))]
                deep = lookup[(role, 7, target["id"], primary, int(sign))]
                depth_records.append(
                    {
                        "model": role,
                        "target_id": target["id"],
                        "sign": int(sign),
                        "magnitude": primary,
                        "contrast": "depth_1.0_minus_0.875",
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
                                t15._config()["source_capture"]["depth_fractions"][
                                    t15.SITE_INDICES.index(site_index)
                                ]
                            ),
                            "target_id": target["id"],
                            "sign": int(sign),
                            "contrast": "magnitude_0.25_minus_0.125",
                            "value": high - low,
                        }
                    )
    return {
        "basis": "A1 target-level true-minus-cross fingerprint estimand",
        "depth_target_estimands": depth_records,
        "depth_summary": _summarize_records(
            depth_records,
            cell_fields=("model", "sign", "magnitude", "contrast"),
            unit_field="target_id",
            expected_units=32,
            namespace="A6_depth",
        ),
        "dose_target_estimands": dose_records,
        "dose_summary": _summarize_records(
            dose_records,
            cell_fields=(
                "model",
                "site_index",
                "depth_fraction",
                "sign",
                "contrast",
            ),
            unit_field="target_id",
            expected_units=32,
            namespace="A6_dose",
        ),
    }


def analyze(run_root: Path, output: Path) -> dict[str, Any]:
    # This is the only scientific-open gate. No source metric, response ledger,
    # or CountSketch value is read before the complete four-role audit passes.
    run_audit = t15.audit_run(run_root)
    _require(
        run_audit.get("scientific_open_authorized") is True, "Scientific open denied"
    )
    a0 = _a0(run_root)
    a1 = _a1(run_root)
    true = _response_reductions(run_root, "true_conflict")
    cross = _response_reductions(run_root, "cross_axis_null")
    emoji = _response_reductions(run_root, "emoji_main")
    word = _response_reductions(run_root, "word_main")
    a2 = _paired_response_family(
        true,
        cross,
        family="A2",
        estimand="median_true_response_minus_median_cross_axis_response",
    )
    a3 = _a3(run_root)
    a4 = _paired_response_family(
        word,
        emoji,
        family="A4",
        estimand="median_word_main_response_minus_median_emoji_main_response",
    )
    a5 = _a5(run_root)
    a6 = _a6(a1)
    families = dict(zip(FAMILIES, (a0, a1, a2, a3, a4, a5, a6), strict=True))
    result = {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": t15.PROTOCOL_ID,
        "status": "complete_exploratory_descriptive_analysis",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_root": str(run_root.resolve()),
        "run_audit": run_audit,
        "families": families,
        "family_order": list(FAMILIES),
        "primary_descriptive_cell": t15._config()["analysis"][
            "primary_descriptive_cell"
        ],
        "claim_boundary": t15._config()["claim_boundary"],
        "confirmatory_status": False,
        "causal_claim_authorized": False,
        "semantic_understanding_claim_authorized": False,
        "adaptive_selection_performed": False,
        "significance_tests": "none_exploratory_descriptive_only",
    }
    _write_json(output, result)
    return {
        "status": "pass",
        "analysis_output": str(output),
        "analysis_output_sha256": _sha256(output),
        "complete_families": list(FAMILIES),
        "response_rows": run_audit["response_rows"],
        "confirmatory_status": False,
    }


def validate_output(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    _require(value.get("analysis_id") == ANALYSIS_ID, "Analysis ID changed")
    _require(
        value.get("source_protocol_id") == t15.PROTOCOL_ID,
        "Analysis source protocol changed",
    )
    _require(value.get("family_order") == list(FAMILIES), "Family order changed")
    _require(set(value.get("families", {})) == set(FAMILIES), "Families incomplete")
    _require(value.get("confirmatory_status") is False, "Confirmatory status changed")
    _require(
        value.get("causal_claim_authorized") is False,
        "Causal boundary changed",
    )
    return {
        "status": "pass",
        "analysis_output_sha256": _sha256(path),
        "complete_families": list(FAMILIES),
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    subparsers = value.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("analyze")
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    audit = subparsers.add_parser("validate-output")
    audit.add_argument("--path", type=Path, required=True)
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
