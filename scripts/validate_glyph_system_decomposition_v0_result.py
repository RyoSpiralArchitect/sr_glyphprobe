#!/usr/bin/env python3
"""Independent compact validation for the T11 glyph-system atlas result.

This module intentionally does not import glyph_system_decomposition_v0.py.
It rehashes the returned compact inputs, recomputes item-margin summaries from
the per-model NPZ arrays, and independently rebuilds the model-agreement,
variance, and depth-trajectory tables used by the public interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


SCHEMA_VERSION = 1
PROTOCOL_ID = "glyphprobe-glyph-system-decomposition-v0"
MODEL_ORDER = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
    "qwen25_0p5b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "qwen25_3b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
ANALYSIS_SYSTEMS = (
    "atomic_anchor",
    "presentation",
    "modifier",
    "zwj",
    "regional_flag",
    "keycap",
)
DECOMPOSITION_SYSTEMS = ANALYSIS_SYSTEMS[1:]
BROAD_ENDPOINTS = (
    "raw_last_decoder_block_output",
    "returned_final_hidden_state",
)
DEPTH_ENDPOINTS = (
    "embedding_output",
    "interblock_depth_0p25",
    "interblock_depth_0p50",
    "interblock_depth_0p75",
    "raw_last_decoder_block_output",
    "returned_final_hidden_state",
)
CONTEXTS = tuple(
    (carrier, distance)
    for carrier in ("article_a", "pipe")
    for distance in (1, 2, 4, 8)
)
METRICS = (
    "matched_glyph_unicode_name",
    "matched_glyph_component_name",
    "matched_decomposed_form_unicode_name",
    "matched_decomposed_form_component_name",
    "lexicalization",
    "presentation_or_fusion",
    "component_tracking",
)
HEADLINE_METRICS = (
    "matched_glyph_unicode_name",
    "lexicalization",
    "presentation_or_fusion",
    "component_tracking",
)
EXPECTED_ANALYSIS_FILES = {
    "analysis.json",
    "broad_system_cell_metrics.jsonl",
    "depth_system_cell_metrics.jsonl",
    "depth_trajectories.jsonl",
    "cross_model_geometry.jsonl",
    "cross_model_item_margin_agreement.jsonl",
    "report.md",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            require(isinstance(value, dict), f"Expected JSON object: {path}:{line_number}")
            rows.append(value)
    return rows


def verify_sha256sums(directory: Path) -> dict[str, str]:
    ledger = directory / "SHA256SUMS"
    require(ledger.is_file(), f"Missing checksum ledger: {ledger}")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        require(len(parts) == 2, f"Malformed checksum line: {ledger}:{line_number}")
        digest, name = parts
        name = name.lstrip("* ")
        require(len(digest) == 64, f"Malformed SHA-256: {ledger}:{line_number}")
        require(name not in entries, f"Duplicate checksum target: {ledger}:{name}")
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe checksum target: {ledger}:{name}",
        )
        target = directory / relative
        require(target.is_file(), f"Missing checksum target: {target}")
        require(sha256(target) == digest, f"Checksum mismatch: {target}")
        entries[name] = digest
    return entries


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_output(output: Path, payload: Mapping[str, Any], report: str) -> None:
    require(not output.exists(), f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        write_json(stage / "independent_validation.json", payload)
        (stage / "report.md").write_text(report, encoding="utf-8")
        lines = [
            f"{sha256(stage / name)}  {name}\n"
            for name in ("independent_validation.json", "report.md")
        ]
        (stage / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def metric_summary(row: Mapping[str, Any], metric: str) -> Mapping[str, Any] | None:
    if metric.startswith("matched_"):
        value = row["matched_incorrect_label_advantage"].get(
            metric.removeprefix("matched_")
        )
    else:
        value = row["decomposition_contrasts"].get(metric)
    return value if isinstance(value, Mapping) else None


def metric_array_suffix(metric: str) -> str:
    if metric.startswith("matched_"):
        return f"{metric.removeprefix('matched_')}_matched_advantage"
    return metric


def finite_median(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    require(array.size > 0, "Cannot take median of an empty finite array")
    return float(np.median(array))


def distribution(values: Iterable[float]) -> dict[str, Any]:
    array = np.asarray(list(values), dtype=np.float64)
    array = array[np.isfinite(array)]
    require(array.size > 0, "Empty distribution")
    return {
        "count": int(array.size),
        "minimum": float(np.min(array)),
        "median": float(np.median(array)),
        "maximum": float(np.max(array)),
        "positive_fraction": float(np.mean(array > 0)),
    }


def assert_close(left: float, right: float, message: str, tolerance: float = 1e-12) -> None:
    require(math.isfinite(left) and math.isfinite(right), f"Non-finite value: {message}")
    require(abs(left - right) <= tolerance, f"{message}: {left} != {right}")


def rankdata(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(array.size, dtype=np.float64)
    start = 0
    while start < array.size:
        stop = start + 1
        while stop < array.size and array[order[stop]] == array[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    finite = np.isfinite(a) & np.isfinite(b)
    a = a[finite]
    b = b[finite]
    if a.size < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return 0.0
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])


def balanced_three_way(values: np.ndarray) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    require(array.ndim == 3 and all(size >= 2 for size in array.shape), "Invalid three-way grid")
    require(bool(np.all(np.isfinite(array))), "Non-finite three-way grid")
    model_count, system_count, context_count = array.shape
    grand = float(np.mean(array))
    model = np.mean(array, axis=(1, 2), keepdims=True) - grand
    system = np.mean(array, axis=(0, 2), keepdims=True) - grand
    context = np.mean(array, axis=(0, 1), keepdims=True) - grand
    model_system = np.mean(array, axis=2, keepdims=True) - grand - model - system
    model_context = np.mean(array, axis=1, keepdims=True) - grand - model - context
    system_context = np.mean(array, axis=0, keepdims=True) - grand - system - context
    three_way = array - grand - model - system - context - model_system - model_context - system_context
    sums = {
        "model": float(system_count * context_count * np.sum(np.square(model))),
        "glyph_system": float(model_count * context_count * np.sum(np.square(system))),
        "context": float(model_count * system_count * np.sum(np.square(context))),
        "model_by_glyph_system": float(context_count * np.sum(np.square(model_system))),
        "model_by_context": float(system_count * np.sum(np.square(model_context))),
        "glyph_system_by_context": float(model_count * np.sum(np.square(system_context))),
        "model_by_glyph_system_by_context": float(np.sum(np.square(three_way))),
    }
    degrees = {
        "model": model_count - 1,
        "glyph_system": system_count - 1,
        "context": context_count - 1,
        "model_by_glyph_system": (model_count - 1) * (system_count - 1),
        "model_by_context": (model_count - 1) * (context_count - 1),
        "glyph_system_by_context": (system_count - 1) * (context_count - 1),
        "model_by_glyph_system_by_context": (model_count - 1) * (system_count - 1) * (context_count - 1),
    }
    total = float(np.sum(np.square(array - grand)))
    return {
        "balanced_shape_model_by_system_by_context": list(array.shape),
        "grand_mean": grand,
        "total_sum_squares": total,
        "total_degrees_of_freedom": int(array.size - 1),
        "total_variance_zero": bool(total <= 1e-30),
        "components": {
            name: {
                "sum_squares": value,
                "degrees_of_freedom": int(degrees[name]),
                "share_of_total_sum_squares": float(value / total) if total > 1e-30 else 0.0,
            }
            for name, value in sums.items()
        },
        "sum_squares_reconciliation_error": float(abs(sum(sums.values()) - total)),
    }


def validate_analysis_invariants(
    analysis: Mapping[str, Any],
    broad_rows: Sequence[Mapping[str, Any]],
    depth_rows: Sequence[Mapping[str, Any]],
    trajectories: Sequence[Mapping[str, Any]],
    geometry_rows: Sequence[Mapping[str, Any]],
    agreement_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    require(analysis["schema_version"] == SCHEMA_VERSION, "Analysis schema changed")
    require(analysis["protocol_id"] == PROTOCOL_ID, "Analysis protocol changed")
    require(analysis["status"] == "pass", "Analysis did not pass")
    require(tuple(analysis["model_order"]) == MODEL_ORDER, "Model order changed")
    require(analysis["analysis_role"] == "prospective_for_outcomes_exploratory_discovery_only_atlas", "Analysis role changed")
    require(analysis["reserve_items"] == 268, "Reserve size changed")
    require(analysis["reserve_model_forward_calls"] == 0, "Reserve received a model forward")
    require(analysis["reserve_outcomes_inspected"] is False, "Reserve outcomes were inspected")
    require(analysis["t12_endpoint_frozen"] is False, "T12 was silently frozen")
    require(analysis["model_forward_calls"] == 0, "Analysis performed model forwards")
    require(analysis["total_acquisition_model_forward_calls"] == 73_566, "Acquisition forward count changed")
    require(analysis["t10_primary_changed"] is False, "T10 primary changed")
    require(analysis["t10_rescue_authorized"] is False, "T10 rescue was authorized")
    for flag in (
        "semantic_claim_authorized",
        "causal_claim_authorized",
        "tokenizer_independence_claim_authorized",
        "scale_law_claim_authorized",
        "model_general_claim_authorized",
        "single_authoritative_landing_pattern_selected",
    ):
        require(analysis[flag] is False, f"Unexpected authorized claim: {flag}")
    counts = {
        "broad_system_cell_metrics": len(broad_rows),
        "depth_system_cell_metrics": len(depth_rows),
        "depth_trajectories": len(trajectories),
        "cross_model_geometry": len(geometry_rows),
        "cross_model_item_margin_agreement": len(agreement_rows),
    }
    require(counts == {
        "broad_system_cell_metrics": 1_008,
        "depth_system_cell_metrics": 2_592,
        "depth_trajectories": 2_592,
        "cross_model_geometry": 1_040,
        "cross_model_item_margin_agreement": 720,
    }, "T11 analysis row counts changed")
    require(analysis["depth_trajectory_row_count"] == counts["depth_trajectories"], "Depth row receipt mismatch")
    require(analysis["cross_model_geometry_row_count"] == counts["cross_model_geometry"], "Geometry row receipt mismatch")
    require(analysis["cross_model_item_margin_agreement_row_count"] == counts["cross_model_item_margin_agreement"], "Agreement row receipt mismatch")

    broad_keys = {
        (
            row["model_role"], row["glyph_system"], row["endpoint"],
            row["carrier"], int(row["distance"]),
        )
        for row in broad_rows
    }
    depth_keys = {
        (
            row["model_role"], row["glyph_system"], row["endpoint"],
            row["carrier"], int(row["distance"]),
        )
        for row in depth_rows
    }
    require(len(broad_keys) == len(broad_rows), "Duplicate broad cell")
    require(len(depth_keys) == len(depth_rows), "Duplicate depth cell")
    require({row["model_role"] for row in broad_rows} == set(MODEL_ORDER), "Broad model coverage changed")
    require({row["glyph_system"] for row in broad_rows} == set(ANALYSIS_SYSTEMS) | {"tag_flag"}, "Broad system coverage changed")
    require({row["endpoint"] for row in broad_rows} == set(BROAD_ENDPOINTS), "Broad endpoints changed")
    require({row["glyph_system"] for row in depth_rows} == set(ANALYSIS_SYSTEMS), "Depth systems changed")
    require({row["endpoint"] for row in depth_rows} == set(DEPTH_ENDPOINTS), "Depth endpoints changed")
    return counts


def validate_summary_bindings(
    analysis: Mapping[str, Any],
    summaries_root: Path,
) -> tuple[dict[str, Any], dict[str, np.lib.npyio.NpzFile]]:
    validation: dict[str, Any] = {}
    arrays: dict[str, np.lib.npyio.NpzFile] = {}
    try:
        for role in MODEL_ORDER:
            directory = summaries_root / role
            entries = verify_sha256sums(directory)
            require(set(entries) == {
                "broad_system_cell_metrics.jsonl",
                "depth_system_cell_metrics.jsonl",
                "item_margins.npz",
                "summary_receipt.json",
            }, f"Summary payload changed: {role}")
            receipt = read_json(directory / "summary_receipt.json")
            require(receipt["model_role"] == role, f"Summary role mismatch: {role}")
            expected = analysis["input_summary_receipt_sha256"][role]
            require(sha256(directory / "summary_receipt.json") == expected, f"Analysis summary binding mismatch: {role}")
            arrays[role] = np.load(directory / "item_margins.npz", allow_pickle=False)
            validation[role] = {
                "sha256sums_sha256": sha256(directory / "SHA256SUMS"),
                "summary_receipt_sha256": expected,
                "item_margins_sha256": entries["item_margins.npz"],
                "item_margin_array_count": len(arrays[role].files),
            }
        return validation, arrays
    except BaseException:
        for value in arrays.values():
            value.close()
        raise


def validate_cell_medians(
    broad_rows: Sequence[Mapping[str, Any]],
    depth_rows: Sequence[Mapping[str, Any]],
    arrays: Mapping[str, np.lib.npyio.NpzFile],
) -> dict[str, Any]:
    counts = Counter()
    mismatches: list[dict[str, Any]] = []
    for scope, rows in (("broad", broad_rows), ("depth", depth_rows)):
        for row in rows:
            prefix = (
                f"{scope}__{row['endpoint']}__{row['carrier']}__d{row['distance']}__"
                f"{row['glyph_system']}__"
            )
            stored = arrays[str(row["model_role"])]
            for metric in METRICS:
                summary = metric_summary(row, metric)
                if summary is None:
                    continue
                key = prefix + metric_array_suffix(metric)
                require(key in stored.files, f"Missing item-margin array: {row['model_role']}:{key}")
                observed = finite_median(stored[key])
                expected = float(summary["median"])
                counts[f"{scope}_registered_metric_medians"] += 1
                if abs(observed - expected) > 1e-12:
                    mismatches.append({"model_role": row["model_role"], "array_key": key, "observed": observed, "expected": expected})
            for view, strict in row["strict_prefix_matched_sensitivity"].items():
                del view
                for pair, summary in strict.get("pairs", {}).items():
                    key = prefix + f"strict_prefix__{pair}_matched_advantage"
                    require(key in stored.files, f"Missing strict item-margin array: {row['model_role']}:{key}")
                    observed = finite_median(stored[key])
                    expected = float(summary["median"])
                    counts[f"{scope}_strict_prefix_metric_medians"] += 1
                    if abs(observed - expected) > 1e-12:
                        mismatches.append({"model_role": row["model_role"], "array_key": key, "observed": observed, "expected": expected})
    require(not mismatches, f"Item-margin median mismatches: {mismatches[:3]}")
    return {
        **{name: int(value) for name, value in sorted(counts.items())},
        "total_checked": int(sum(counts.values())),
        "mismatch_count": len(mismatches),
        "tolerance": 1e-12,
    }


def validate_margin_agreement(
    rows: Sequence[Mapping[str, Any]],
    arrays: Mapping[str, np.lib.npyio.NpzFile],
) -> dict[str, Any]:
    common = set.intersection(*(set(value.files) for value in arrays.values()))
    keys = sorted(key for key in common if key.endswith("__glyph_unicode_name_matched_advantage"))
    require(len(keys) == 720, "Common item-margin agreement key count changed")
    published = {str(row["array_key"]): row for row in rows}
    require(set(keys) == set(published), "Published item-margin agreement keys changed")
    for key in keys:
        correlations = [
            safe_spearman(arrays[left][key], arrays[right][key])
            for left_index, left in enumerate(MODEL_ORDER)
            for right in MODEL_ORDER[left_index + 1 :]
        ]
        observed = distribution(correlations)
        expected = published[key]
        for name in ("minimum", "median", "maximum", "positive_fraction"):
            assert_close(float(observed[name]), float(expected[name]), f"Agreement mismatch {key}:{name}")
        require(observed["count"] == expected["count"] == 36, f"Agreement pair count changed: {key}")
    return {
        "rows_recomputed": len(keys),
        "model_pairs_per_row": 36,
        "mismatch_count": 0,
        "tolerance": 1e-12,
    }


def validate_variance(
    analysis: Mapping[str, Any],
    broad_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    lookup = {
        (row["model_role"], row["glyph_system"], row["carrier"], int(row["distance"])): row
        for row in broad_rows
        if row["endpoint"] == "returned_final_hidden_state"
        and row["glyph_system"] in ANALYSIS_SYSTEMS
    }
    checked = 0
    for metric in METRICS:
        included_systems = [
            system
            for system in ANALYSIS_SYSTEMS
            if metric_summary(lookup[(MODEL_ORDER[0], system, *CONTEXTS[0])], metric) is not None
        ]
        grid = np.empty((len(MODEL_ORDER), len(included_systems), len(CONTEXTS)), dtype=np.float64)
        for model_index, role in enumerate(MODEL_ORDER):
            for system_index, system in enumerate(included_systems):
                for context_index, (carrier, distance) in enumerate(CONTEXTS):
                    summary = metric_summary(lookup[(role, system, carrier, distance)], metric)
                    require(summary is not None, f"Partially missing variance metric: {metric}/{system}")
                    grid[model_index, system_index, context_index] = float(summary["median"])
        observed = balanced_three_way(grid)
        expected = analysis["model_by_system_by_context_variance_decomposition"][metric]
        require(expected["model_order"] == list(MODEL_ORDER), f"Variance model order changed: {metric}")
        require(expected["glyph_system_order"] == included_systems, f"Variance systems changed: {metric}")
        require(expected["context_order"] == [f"{c}:d{d}" for c, d in CONTEXTS], f"Variance contexts changed: {metric}")
        assert_close(observed["grand_mean"], float(expected["grand_mean"]), f"Variance mean mismatch: {metric}")
        assert_close(observed["total_sum_squares"], float(expected["total_sum_squares"]), f"Variance total mismatch: {metric}")
        for component, value in observed["components"].items():
            published = expected["components"][component]
            assert_close(value["sum_squares"], float(published["sum_squares"]), f"Variance SS mismatch: {metric}/{component}")
            assert_close(value["share_of_total_sum_squares"], float(published["share_of_total_sum_squares"]), f"Variance share mismatch: {metric}/{component}")
            require(value["degrees_of_freedom"] == published["degrees_of_freedom"], f"Variance df mismatch: {metric}/{component}")
        checked += 1
    return {"metrics_recomputed": checked, "mismatch_count": 0, "tolerance": 1e-12}


def validate_depth_trajectories(
    depth_rows: Sequence[Mapping[str, Any]],
    trajectory_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    lookup = {
        (row["model_role"], row["glyph_system"], row["carrier"], int(row["distance"]), row["endpoint"]): row
        for row in depth_rows
    }
    checked = 0
    for row in trajectory_rows:
        summaries = []
        for endpoint in DEPTH_ENDPOINTS:
            source = lookup[(row["model_role"], row["glyph_system"], row["carrier"], int(row["distance"]), endpoint)]
            summary = metric_summary(source, str(row["metric"]))
            require(summary is not None, f"Missing trajectory source metric: {row['metric']}")
            summaries.append(summary)
        first: dict[str, Any] | None = None
        for endpoint, summary, published in zip(DEPTH_ENDPOINTS, summaries, row["trajectory"], strict=True):
            interval = [float(value) for value in summary["bootstrap_percentile_95_interval"]]
            relation = "positive" if interval[0] > 0 else "negative" if interval[1] < 0 else "includes_zero"
            require(published["endpoint"] == endpoint, "Trajectory endpoint changed")
            require(published["bootstrap_percentile_95_interval"] == interval, "Trajectory interval changed")
            require(published["interval_relation_to_zero"] == relation, "Trajectory interval relation changed")
            assert_close(float(published["median_item_margin"]), float(summary["median"]), "Trajectory median changed")
            if first is None and relation != "includes_zero":
                first = {"endpoint": endpoint, "direction": relation, "descriptive_only": True}
        require(row["first_depth_with_interval_excluding_zero"] == first, "First interval-exclusion depth changed")
        delta = float(summaries[-1]["median"] - summaries[-2]["median"])
        assert_close(delta, float(row["returned_final_minus_raw_last_block_median_delta"]), "Trajectory final-minus-raw delta changed")
        require(row["decision_authorized"] is False, "Trajectory received decision authority")
        checked += 1
    require(checked == 2_592, "Trajectory validation count changed")
    return {"rows_recomputed": checked, "mismatch_count": 0, "tolerance": 1e-12}


def preflight_coverage(preflight: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    entries = verify_sha256sums(preflight)
    require(set(entries) == {"aggregate.json", *(f"{role}.json" for role in MODEL_ORDER)}, "Preflight payload changed")
    aggregate = read_json(preflight / "aggregate.json")
    require(
        aggregate["status"]
        == "all_nine_tokenizer_preflights_complete_zero_t11_model_forwards",
        "Preflight aggregate status changed",
    )
    require(aggregate["model_forward_calls"] == 0, "Preflight performed model forwards")
    require(aggregate["reserve_model_forward_calls"] == 0, "Preflight forwarded reserve")
    require(aggregate["model_weights_loaded"] is False, "Preflight loaded model weights")
    require(tuple(aggregate["model_order"]) == MODEL_ORDER, "Preflight model order changed")
    required: dict[tuple[str, str], list[float]] = defaultdict(list)
    strict: dict[tuple[str, str], list[float]] = defaultdict(list)
    for role in MODEL_ORDER:
        receipt = read_json(preflight / f"{role}.json")
        require(receipt["model_role"] == role, f"Preflight role mismatch: {role}")
        controls = receipt["tokenizer"]["matched_incorrect_label_controls"]
        for view, systems in controls.items():
            for system, payload in systems.items():
                required[(system, view)].append(float(payload["required"]["coverage"]))
                strict[(system, view)].append(float(payload["strict_prefix_sensitivity"]["coverage"]))
    coverage: dict[str, Any] = {}
    for key in sorted(required):
        system, view = key
        req = distribution(required[key])
        sen = distribution(strict[key])
        require(req["minimum"] >= 0.75, f"Required control coverage below gate: {system}/{view}")
        coverage[f"{system}:{view}"] = {"required": req, "strict_prefix_sensitivity": sen}
    binding = {
        "sha256sums_sha256": sha256(preflight / "SHA256SUMS"),
        "aggregate_sha256": sha256(preflight / "aggregate.json"),
        "aggregate_receipt": {
            "status": aggregate["status"],
            "model_forward_calls": aggregate["model_forward_calls"],
            "reserve_model_forward_calls": aggregate["reserve_model_forward_calls"],
            "model_weights_loaded": aggregate["model_weights_loaded"],
        },
    }
    return binding, coverage


def metric_cell_distribution(rows: Sequence[Mapping[str, Any]], metric: str) -> dict[str, Any]:
    summaries = [metric_summary(row, metric) for row in rows]
    summaries = [value for value in summaries if value is not None]
    require(summaries, f"No metric values: {metric}")
    result = distribution(float(value["median"]) for value in summaries)
    positive = sum(float(value["bootstrap_percentile_95_interval"][0]) > 0 for value in summaries)
    negative = sum(float(value["bootstrap_percentile_95_interval"][1]) < 0 for value in summaries)
    result["descriptive_bootstrap_interval_positive_count"] = positive
    result["descriptive_bootstrap_interval_negative_count"] = negative
    result["descriptive_bootstrap_interval_includes_zero_count"] = len(summaries) - positive - negative
    return result


def returned_final_headlines(broad_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    final_rows = [row for row in broad_rows if row["endpoint"] == "returned_final_hidden_state"]
    output: dict[str, Any] = {}
    for system in ANALYSIS_SYSTEMS:
        rows = [row for row in final_rows if row["glyph_system"] == system]
        metrics = ["matched_glyph_unicode_name"] if system == "atomic_anchor" else list(METRICS)
        output[system] = {metric: metric_cell_distribution(rows, metric) for metric in metrics}
    return output


def strict_prefix_headlines(broad_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    final_rows = [row for row in broad_rows if row["endpoint"] == "returned_final_hidden_state"]
    output: dict[str, Any] = {}
    for system in ANALYSIS_SYSTEMS:
        rows = [row for row in final_rows if row["glyph_system"] == system]
        for view in ("unicode_name", "component_name"):
            pairs = sorted({pair for row in rows for pair in row["strict_prefix_matched_sensitivity"].get(view, {}).get("pairs", {})})
            for pair in pairs:
                strict = [row["strict_prefix_matched_sensitivity"][view]["pairs"].get(pair) for row in rows]
                strict = [value for value in strict if value is not None]
                required_values = [row["matched_incorrect_label_advantage"].get(pair) for row in rows]
                required_values = [value for value in required_values if value is not None]
                key = f"{system}:{view}:{pair}"
                output[key] = {
                    "required_cell_median_distribution": distribution(float(value["median"]) for value in required_values),
                    "strict_prefix_cell_median_distribution": metric_cell_distribution_from_summaries(strict),
                }
    return output


def metric_cell_distribution_from_summaries(summaries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    require(summaries, "No strict-prefix summaries")
    result = distribution(float(value["median"]) for value in summaries)
    positive = sum(float(value["bootstrap_percentile_95_interval"][0]) > 0 for value in summaries)
    negative = sum(float(value["bootstrap_percentile_95_interval"][1]) < 0 for value in summaries)
    result["descriptive_bootstrap_interval_positive_count"] = positive
    result["descriptive_bootstrap_interval_negative_count"] = negative
    result["descriptive_bootstrap_interval_includes_zero_count"] = len(summaries) - positive - negative
    return result


def retrieval_headlines(broad_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for endpoint in BROAD_ENDPOINTS:
        for system in (*ANALYSIS_SYSTEMS, "tag_flag"):
            rows = [row for row in broad_rows if row["endpoint"] == endpoint and row["glyph_system"] == system]
            pairs = [row["pairs"]["glyph_unicode_name"] for row in rows]
            output[f"{endpoint}:{system}"] = {
                "cell_count": len(pairs),
                "top1_accuracy_forward_median": float(np.median([pair["top1_accuracy_forward"] for pair in pairs])),
                "mean_reciprocal_rank_forward_median": float(np.median([pair["mean_reciprocal_rank_forward"] for pair in pairs])),
                "paired_minus_off_diagonal_margin_median": float(np.median([pair["paired_minus_off_diagonal_margin"] for pair in pairs])),
                "retrieval_breadth_fraction_forward_median": float(np.median([pair["retrieval_distribution_forward"]["retrieval_breadth_fraction"] for pair in pairs])),
                "top_decile_prediction_concentration_forward_median": float(np.median([pair["retrieval_distribution_forward"]["top_decile_prediction_concentration"] for pair in pairs])),
            }
    return output


def agreement_headlines(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        parts = str(row["array_key"]).split("__")
        if parts[0] != "broad" or parts[1] != "returned_final_hidden_state" or "strict_prefix" in parts:
            continue
        groups[(parts[4], "required_token_length_matched")].append(float(row["median"]))
    return {
        f"{system}:{control}": distribution(values)
        for (system, control), values in sorted(groups.items())
    }


def geometry_headlines(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        if row["endpoint"] != "returned_final_hidden_state":
            continue
        groups[(row["analysis_axis"], row["glyph_system"], row["view_or_pair"])].append(float(row["median"]))
    return {
        f"{axis}:{system}:{view}": distribution(values)
        for (axis, system, view), values in sorted(groups.items())
    }


def variance_headlines(analysis: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for metric, payload in analysis["model_by_system_by_context_variance_decomposition"].items():
        output[metric] = {
            "grand_mean": payload["grand_mean"],
            "glyph_system_order": payload["glyph_system_order"],
            "share_of_total_sum_squares": {
                name: component["share_of_total_sum_squares"]
                for name, component in payload["components"].items()
            },
        }
    return output


def depth_headlines(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["metric"] in HEADLINE_METRICS:
            groups[(row["glyph_system"], row["metric"])].append(row)
    output: dict[str, Any] = {}
    for (system, metric), values in sorted(groups.items()):
        first = Counter()
        negative_first = 0
        for row in values:
            marker = row["first_depth_with_interval_excluding_zero"]
            if marker is None:
                first["none"] += 1
            else:
                first[str(marker["endpoint"])] += 1
                negative_first += marker["direction"] == "negative"
        output[f"{system}:{metric}"] = {
            "trajectory_count": len(values),
            "first_interval_excluding_zero": {endpoint: int(first[endpoint]) for endpoint in (*DEPTH_ENDPOINTS, "none")},
            "negative_first_count": int(negative_first),
            "returned_final_minus_raw_last_block_median_delta": distribution(float(row["returned_final_minus_raw_last_block_median_delta"]) for row in values),
        }
    return output


def qwen_profiles(broad_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    roles = (
        "qwen25_0p5b_base_bf16",
        "qwen25_1p5b_base_bf16",
        "qwen25_3b_base_bf16",
        "qwen25_7b_base_bf16",
    )
    final = [row for row in broad_rows if row["endpoint"] == "returned_final_hidden_state"]
    profiles: dict[str, Any] = {}
    increasing = 0
    for system in ANALYSIS_SYSTEMS:
        metrics = ["matched_glyph_unicode_name"] if system == "atomic_anchor" else list(METRICS)
        for metric in metrics:
            values = []
            for role in roles:
                summaries = [metric_summary(row, metric) for row in final if row["glyph_system"] == system and row["model_role"] == role]
                require(all(summary is not None for summary in summaries) and len(summaries) == 8, f"Incomplete Qwen profile: {system}/{metric}/{role}")
                values.append(float(np.median([summary["median"] for summary in summaries if summary is not None])))
            monotonic = all(left < right for left, right in zip(values, values[1:]))
            increasing += int(monotonic)
            profiles[f"{system}:{metric}"] = {"values_in_size_order": values, "strictly_increasing": monotonic}
    return {
        "model_order": list(roles),
        "profile_count": len(profiles),
        "strictly_increasing_profile_count": increasing,
        "profiles": profiles,
        "scale_law_claim_authorized": False,
    }


def build_report(payload: Mapping[str, Any]) -> str:
    checks = payload["independent_recomputations"]
    return (
        "# T11 independent compact validation\n\n"
        "Status: **PASS; share with caveats**.\n\n"
        f"- Recomputed {checks['stored_item_margin_cell_medians']['total_checked']:,} stored item-margin cell medians with zero mismatches.\n"
        f"- Recomputed {checks['cross_model_item_margin_agreement']['rows_recomputed']:,} cross-model agreement rows with zero mismatches.\n"
        f"- Recomputed {checks['balanced_three_way_variance']['metrics_recomputed']} balanced variance decompositions and {checks['depth_trajectories']['rows_recomputed']:,} depth trajectories with zero mismatches.\n"
        "- Cross-model activation geometry was hash- and schema-checked but not independently rebuilt because that requires the omitted raw activation archive.\n"
        "- T11 remains exploratory. The T10 primary is unchanged, the 268-item reserve remains unforwarded, and no semantic, causal, tokenizer-independent, scale-law, or model-general claim is authorized.\n"
    )


def validate(
    analysis_dir: Path,
    summaries_root: Path,
    preflight_dir: Path,
) -> dict[str, Any]:
    analysis_entries = verify_sha256sums(analysis_dir)
    require(set(analysis_entries) == EXPECTED_ANALYSIS_FILES, "Analysis checksum payload changed")
    analysis = read_json(analysis_dir / "analysis.json")
    broad_rows = read_jsonl(analysis_dir / "broad_system_cell_metrics.jsonl")
    depth_rows = read_jsonl(analysis_dir / "depth_system_cell_metrics.jsonl")
    trajectory_rows = read_jsonl(analysis_dir / "depth_trajectories.jsonl")
    geometry_rows = read_jsonl(analysis_dir / "cross_model_geometry.jsonl")
    agreement_rows = read_jsonl(analysis_dir / "cross_model_item_margin_agreement.jsonl")
    row_counts = validate_analysis_invariants(
        analysis, broad_rows, depth_rows, trajectory_rows, geometry_rows, agreement_rows
    )
    preflight_binding, coverage = preflight_coverage(preflight_dir)
    summary_bindings, arrays = validate_summary_bindings(analysis, summaries_root)
    try:
        recomputations = {
            "stored_item_margin_cell_medians": validate_cell_medians(broad_rows, depth_rows, arrays),
            "cross_model_item_margin_agreement": validate_margin_agreement(agreement_rows, arrays),
            "balanced_three_way_variance": validate_variance(analysis, broad_rows),
            "depth_trajectories": validate_depth_trajectories(depth_rows, trajectory_rows),
            "cross_model_geometry": {
                "status": "hash_and_schema_checked_not_independently_recomputed",
                "row_count": len(geometry_rows),
                "reason": "Independent reconstruction requires the omitted approximately 9.15 GiB raw activation archive.",
            },
            "descriptive_bootstrap_intervals": {
                "status": "stored_intervals_reconciled_through_depth_tables_not_fully_resampled",
                "reason": "All interval values used in depth trajectories were reconciled, but the full item-bootstrap family was not independently rerun.",
            },
        }
    finally:
        for value in arrays.values():
            value.close()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "validation_role": "independent_compact_result_validation",
        "status": "pass",
        "overall_assessment": "share_with_caveats",
        "input_bindings": {
            "analysis_sha256sums_sha256": sha256(analysis_dir / "SHA256SUMS"),
            "analysis_file_sha256": analysis_entries,
            "preflight": preflight_binding,
            "summaries": summary_bindings,
            "run_receipt_sha256_bound_but_external": analysis["input_run_receipt_sha256"],
        },
        "invariants": {
            "model_cells": 9,
            "acquired_items": 843,
            "reserve_items": 268,
            "total_acquisition_model_forward_calls": 73_566,
            "analysis_model_forward_calls": 0,
            "reserve_model_forward_calls": 0,
            "reserve_outcomes_inspected": False,
            "t10_primary_changed": False,
            "row_counts": row_counts,
        },
        "independent_recomputations": recomputations,
        "matched_control_coverage_across_model_tokenizer_cells": coverage,
        "returned_final_cell_distributions": returned_final_headlines(broad_rows),
        "strict_prefix_sensitivity": strict_prefix_headlines(broad_rows),
        "retrieval_cell_medians": retrieval_headlines(broad_rows),
        "returned_final_required_margin_cross_model_agreement": agreement_headlines(agreement_rows),
        "returned_final_cross_model_geometry_context_distributions": geometry_headlines(geometry_rows),
        "returned_final_balanced_variance_decomposition": variance_headlines(analysis),
        "depth_headlines": depth_headlines(trajectory_rows),
        "qwen_size_ordered_profiles_descriptive_only": qwen_profiles(broad_rows),
        "claim_boundary": {
            "exploratory_only": True,
            "single_authoritative_landing_pattern_selected": False,
            "t10_rescue_authorized": False,
            "semantic_claim_authorized": False,
            "causal_claim_authorized": False,
            "tokenizer_independence_claim_authorized": False,
            "scale_law_claim_authorized": False,
            "instruction_tuning_claim_authorized": False,
            "architecture_or_model_generality_claim_authorized": False,
            "independent_replication_claim_authorized": False,
        },
        "required_caveats": [
            "The nine frozen cells confound architecture, size, tokenizer, training corpus, and tuning.",
            "Cell-bootstrap intervals are descriptive and do not form a multiplicity-controlled confirmatory family.",
            "The strict first-target-token sensitivity has sharply uneven coverage across glyph systems and cannot replace the required exact-token-length controls.",
            "Tag flags are a three-item microcase and carry no distributional or matched-control claim.",
            "Cross-model activation geometry was not independently reconstructed without the omitted raw activation archive.",
            "T12 must freeze one endpoint and multiplicity family before any reserve model outcome is opened.",
        ],
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--summaries-root", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = validate(args.analysis, args.summaries_root, args.preflight)
    report = build_report(payload)
    write_output(args.output, payload, report)
    print(json.dumps({
        "status": payload["status"],
        "overall_assessment": payload["overall_assessment"],
        "output": str(args.output),
        "stored_item_margin_cell_medians": payload["independent_recomputations"]["stored_item_margin_cell_medians"],
        "cross_model_item_margin_agreement": payload["independent_recomputations"]["cross_model_item_margin_agreement"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
