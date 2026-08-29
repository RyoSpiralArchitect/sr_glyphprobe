#!/usr/bin/env python3
"""Derive exploratory T13-EA F4--F6 point tables after scientific closeout.

The production path is deliberately ordered.  It validates an independently
written scientific-open receipt, checks the exact production tree, opens only
the three zero-control ledgers and arrays, and requires an exact no-op before
any non-zero response, baseline-logit, or source-activation value is opened.

All results are descriptive and exploratory.  Raw CountSketch buckets, token
IDs, and hidden-space vectors are compared only within a model.  Cross-model
comparisons use scalar target profiles only.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping, Sequence
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import uuid
from typing import Any

import numpy as np
import yaml


ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
CONFIG_PATH = Path("configs/emoji_steering_specificity_analysis_v0.yaml")
ACQUISITION_CONFIG_PATH = Path("configs/emoji_steering_specificity_harvest_v0.yaml")
PREFLIGHT_DIRECTORY = Path("validation/emoji_steering_specificity_harvest_v0")
ENDPOINT_ORDER = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
VIEW_ORDER = (
    "glyph",
    "unicode_name",
    "component_name",
    "codepoint_literal",
    "decomposed_form",
)
PAIR_ORDER = (
    ("glyph_vs_unicode_name", "glyph", "unicode_name"),
    ("glyph_vs_decomposed_form", "glyph", "decomposed_form"),
    (
        "unicode_name_vs_decomposed_form",
        "unicode_name",
        "decomposed_form",
    ),
)
HEX = frozenset("0123456789abcdef")


class GeometryAnalysisError(RuntimeError):
    """Raised when the scientific-open, no-op, or geometry contract fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GeometryAnalysisError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected YAML object: {path}")
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
                f"Expected JSON object: {path}:{line_number}",
            )
            rows.append(value)
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in HEX for character in value)
    )


def _write_json(path: Path, value: Any) -> None:
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    with path.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _config() -> dict[str, Any]:
    value = _read_yaml(_root() / CONFIG_PATH)
    _require(value.get("analysis_id") == ANALYSIS_ID, "Analysis ID changed")
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Source protocol changed",
    )
    families = {str(row["id"]): row for row in value["scientific_output_families"]}
    _require(
        tuple(families)[-3:]
        == ("F4_target_sensitivity", "F5_output_direction", "F6_source_geometry"),
        "F4--F6 family order changed",
    )
    gate = value["integrity_gate"]
    _require(gate["external_closeout_root_required"] is True, "Closeout gate changed")
    _require(
        gate["zero_hook_value_gate_runs_before_nonzero_outcome_rows"] is True,
        "Zero-first gate changed",
    )
    _require(
        families["F5_output_direction"]["comparison_scope"]["cross_model"]
        == "scalar_condition_rank_concordance_only",
        "F5 cross-model boundary changed",
    )
    _require(
        families["F6_source_geometry"]["cross_model_vector_comparison"]
        == "forbidden_different_hidden_spaces",
        "F6 hidden-space boundary changed",
    )
    return value


def _acquisition_config() -> dict[str, Any]:
    value = _read_yaml(_root() / ACQUISITION_CONFIG_PATH)
    _require(value.get("protocol_id") == SOURCE_PROTOCOL_ID, "Protocol changed")
    return value


def endpoint_values(row: Mapping[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for name in ENDPOINT_ORDER[:4]:
        value = float(row[name])
        _require(math.isfinite(value), f"Nonfinite response endpoint: {name}")
        result[name] = value
    entropy0 = float(row["baseline_entropy"])
    entropy1 = float(row["intervened_entropy"])
    _require(math.isfinite(entropy0) and math.isfinite(entropy1), "Nonfinite entropy")
    _require(isinstance(row["argmax_flip"], bool), "argmax_flip is not boolean")
    result["entropy_change"] = entropy1 - entropy0
    result["argmax_flip_rate"] = float(row["argmax_flip"])
    return result


def _rankdata(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    _require(array.ndim == 1 and bool(np.isfinite(array).all()), "Invalid ranks")
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(len(array), dtype=np.float64)
    start = 0
    while start < len(array):
        stop = start + 1
        while stop < len(array) and array[order[stop]] == array[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def spearman_rank_correlation(
    left: Sequence[float], right: Sequence[float]
) -> float | None:
    """Return average-tie Spearman correlation, or ``None`` if undefined."""

    _require(len(left) == len(right) and len(left) >= 2, "Invalid rank vectors")
    x = _rankdata(left)
    y = _rankdata(right)
    x -= np.mean(x)
    y -= np.mean(y)
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denominator == 0.0:
        return None
    return float(np.dot(x, y) / denominator)


def cosine_at_comparison(left: np.ndarray, right: np.ndarray) -> float | None:
    """Normalize only for this comparison; return null for a zero norm."""

    x = np.asarray(left, dtype=np.float64)
    y = np.asarray(right, dtype=np.float64)
    _require(x.shape == y.shape and x.ndim == 1, "Cosine shape mismatch")
    _require(bool(np.isfinite(x).all() and np.isfinite(y).all()), "Nonfinite cosine")
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denominator == 0.0:
        return None
    return float(np.dot(x, y) / denominator)


def _mean_median(values: Sequence[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    _require(len(array) > 0 and bool(np.isfinite(array).all()), "Empty summary")
    return {
        "n": len(array),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def validate_scientific_open_receipt(
    receipt: Mapping[str, Any], run_root: Path
) -> dict[str, Any]:
    """Validate an external inventory receipt without opening scientific values."""

    config = _config()
    roles = [str(value) for value in config["acquisition_gate"]["required_role_order"]]
    _require(
        receipt.get("analysis_id") == ANALYSIS_ID, "Open receipt analysis mismatch"
    )
    _require(
        receipt.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Open receipt protocol mismatch",
    )
    _require(
        receipt.get("status") == "scientific_open_closeout_complete",
        "Scientific-open closeout is incomplete",
    )
    _require(int(receipt.get("schema_version", -1)) == 1, "Closeout schema changed")
    _require(receipt.get("scientific_open_authorized") is True, "Open not authorized")
    _require(
        receipt.get("independent_hash_verification") is True,
        "Independent hash verification absent",
    )
    _require(receipt.get("scientific_values_parsed") is False, "Receipt is not blind")
    _require(
        int(receipt.get("roles_complete", -1))
        == int(receipt.get("roles_required", -2))
        == len(roles),
        "Role closeout count mismatch",
    )
    observed_root = Path(str(receipt["run_root"])).expanduser().resolve(strict=True)
    _require(observed_root == run_root.resolve(strict=True), "Run root mismatch")
    closeout_root = receipt.get("run_binding_root_sha256")
    _require(_is_sha256(closeout_root), "External closeout root missing")
    inventory = receipt.get("role_bindings")
    _require(
        isinstance(inventory, list) and len(inventory) == len(roles), "Bad bindings"
    )
    by_role = {str(row["role"]): row for row in inventory}
    _require(list(by_role) == roles, "Role binding order changed")
    role_roots: dict[str, str] = {}
    for role in roles:
        row = by_role[role]
        role_root = row.get("role_binding_root_sha256")
        _require(_is_sha256(role_root), f"Role binding root missing: {role}")
        role_roots[role] = str(role_root)
    files = receipt.get("verified_file_bindings")
    allowed = receipt.get("canonical_allowed_relative_paths")
    _require(isinstance(files, list) and files, "Verified file bindings missing")
    _require(isinstance(allowed, list) and allowed, "Canonical path set missing")
    _require(
        int(receipt.get("total_verified_files", -1)) == len(files),
        "Verified file count changed",
    )
    _require(
        int(receipt.get("total_verified_bytes", -1))
        == sum(int(row["bytes"]) for row in files),
        "Verified byte count changed",
    )
    observed_paths = [str(row["relative_path"]) for row in files]
    _require(observed_paths == sorted(observed_paths), "Verified paths are not sorted")
    _require(len(observed_paths) == len(set(observed_paths)), "Duplicate verified path")
    _require(
        set(observed_paths) <= set(map(str, allowed)), "Noncanonical verified path"
    )
    for row in files:
        relative = Path(str(row["relative_path"]))
        _require(
            not relative.is_absolute() and ".." not in relative.parts, "Unsafe path"
        )
        _require(_is_sha256(row.get("sha256")), "Verified file hash changed")
    return {
        "run_root": str(observed_root),
        "external_closeout_root_sha256": str(closeout_root),
        "role_binding_root_sha256": role_roots,
    }


def _audit_closeout_same_process(run_root: Path, receipt_path: Path) -> dict[str, Any]:
    """Re-run the independent exact-schema/hash closeout before any value read."""

    module_path = (
        _root() / "scripts" / "audit_emoji_steering_specificity_analysis_v0.py"
    )
    spec = importlib.util.spec_from_file_location("t13ea_closeout_audit", module_path)
    _require(
        spec is not None and spec.loader is not None, "Closeout auditor unavailable"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.audit_verified_closeout(run_root, receipt_path)
    _require(
        result.get("status") == "scientific_open_closeout_audit_pass"
        and result.get("scientific_values_parsed") is False,
        "Same-process closeout audit failed",
    )
    return dict(result)


class ValueOpenGate:
    """A small state machine enforcing external receipt then all-zero first open."""

    def __init__(self) -> None:
        self.scientific_open_validated = False
        self.zero_gate_complete = False
        self.trace: list[str] = []

    def authorize(self) -> None:
        _require(not self.scientific_open_validated, "Receipt already validated")
        self.scientific_open_validated = True
        self.trace.append("external_scientific_open_receipt_validated")

    def open_jsonl(
        self, path: Path, *, zero_control: bool = False
    ) -> list[dict[str, Any]]:
        _require(
            self.scientific_open_validated, "Scientific-open receipt not validated"
        )
        _require(
            zero_control or self.zero_gate_complete,
            "Nonzero ledger opened before the zero-control gate",
        )
        self.trace.append(f"{'zero' if zero_control else 'nonzero'}:jsonl:{path}")
        return _read_jsonl(path)

    def open_array(
        self, path: Path, *, zero_control: bool = False, mmap: bool = True
    ) -> np.ndarray:
        _require(
            self.scientific_open_validated, "Scientific-open receipt not validated"
        )
        _require(
            zero_control or self.zero_gate_complete,
            "Nonzero array opened before the zero-control gate",
        )
        self.trace.append(f"{'zero' if zero_control else 'nonzero'}:npy:{path}")
        return np.load(path, mmap_mode="r" if mmap else None, allow_pickle=False)

    def complete_zero_gate(self) -> None:
        _require(
            self.scientific_open_validated, "Scientific-open receipt not validated"
        )
        _require(not self.zero_gate_complete, "Zero gate already complete")
        self.zero_gate_complete = True
        self.trace.append("all_pilot_zero_controls_exact_noop")


def validate_zero_control(
    rows: Sequence[Mapping[str, Any]],
    *,
    top_positive_ids: np.ndarray,
    top_positive_values: np.ndarray,
    top_negative_ids: np.ndarray,
    top_negative_values: np.ndarray,
    countsketch: np.ndarray,
    vocab_size: int,
) -> dict[str, Any]:
    """Enforce the first-open exact value gate; tied top IDs are allowed."""

    count = len(rows)
    arrays = (
        top_positive_ids,
        top_positive_values,
        top_negative_ids,
        top_negative_values,
        countsketch,
    )
    _require(
        count > 0 and all(array.shape[0] == count for array in arrays), "Zero rows"
    )
    _require(
        np.issubdtype(top_positive_ids.dtype, np.integer)
        and np.issubdtype(top_negative_ids.dtype, np.integer),
        "Zero top IDs must be integers",
    )
    for ids in (top_positive_ids, top_negative_ids):
        _require(
            bool(((ids >= 0) & (ids < vocab_size)).all()),
            "Zero-control tied top ID outside vocabulary",
        )
    for values in (top_positive_values, top_negative_values, countsketch):
        _require(bool(np.isfinite(values).all()), "Nonfinite zero-control array")
        _require(bool(np.equal(values, 0).all()), "Zero-control array is nonzero")
    for index, row in enumerate(rows):
        _require(int(row["response_index"]) == index, "Zero response index changed")
        _require(row.get("condition_kind") == "zero_direction", "Wrong zero kind")
        _require(float(row["magnitude"]) == 0.0 and int(row["sign"]) == 0, "Bad zero")
        for endpoint in ENDPOINT_ORDER[:4]:
            _require(float(row[endpoint]) == 0.0, f"Zero scalar is nonzero: {endpoint}")
        _require(
            float(row["baseline_entropy"]) == float(row["intervened_entropy"]),
            "Zero entropy changed",
        )
        _require(
            int(row["baseline_argmax_id"]) == int(row["intervened_argmax_id"]),
            "Zero argmax changed",
        )
        _require(
            0 <= int(row["baseline_argmax_id"]) < vocab_size,
            "Zero argmax outside vocabulary",
        )
        _require(row["argmax_flip"] is False, "Zero argmax flip changed")
    return {
        "status": "exact_noop_pass",
        "rows": count,
        "tied_top_ids_allowed_and_range_checked": True,
        "scalar_equalities": 7,
        "zero_array_families": 3,
    }


def validate_zero_gate_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_run_binding_root_sha256: str | None = None,
    expected_scientific_open_receipt_sha256: str | None = None,
    expected_pilot_roles: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate the reusable exact-no-op receipt consumed by sibling analyzers."""

    _require(int(receipt.get("schema_version", -1)) == 1, "Zero receipt schema changed")
    _require(receipt.get("analysis_id") == ANALYSIS_ID, "Zero receipt analysis changed")
    _require(
        receipt.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Zero receipt protocol changed",
    )
    _require(
        receipt.get("status") == "all_pilot_zero_controls_exact_noop",
        "Zero receipt is incomplete",
    )
    run_binding = receipt.get("run_binding_root_sha256")
    open_hash = receipt.get("scientific_open_receipt_sha256")
    _require(_is_sha256(run_binding), "Zero receipt run binding missing")
    _require(_is_sha256(open_hash), "Zero receipt open binding missing")
    if expected_run_binding_root_sha256 is not None:
        _require(run_binding == expected_run_binding_root_sha256, "Zero run changed")
    if expected_scientific_open_receipt_sha256 is not None:
        _require(
            open_hash == expected_scientific_open_receipt_sha256, "Zero open changed"
        )
    models = receipt.get("models")
    _require(isinstance(models, list) and models, "Zero model receipts missing")
    roles = [str(row["model"]) for row in models]
    if expected_pilot_roles is not None:
        _require(roles == list(expected_pilot_roles), "Zero pilot order changed")
    _require(len(roles) == len(set(roles)), "Duplicate zero pilot role")
    for row in models:
        _require(row.get("status") == "exact_noop_pass", "Zero model did not pass")
        _require(int(row.get("rows", 0)) > 0, "Zero model row count missing")
    trace = receipt.get("zero_phase_value_open_trace")
    _require(isinstance(trace, list) and trace, "Zero phase trace missing")
    _require(
        trace[0] == "external_scientific_open_receipt_validated"
        and trace[-1] == "all_pilot_zero_controls_exact_noop"
        and all("nonzero:" not in str(value) for value in trace),
        "Zero phase open order changed",
    )
    _require(
        receipt.get("scientific_values_opened_before_all_zero") is False,
        "Early scientific value read recorded",
    )
    return {
        "status": "zero_gate_receipt_audit_pass",
        "run_binding_root_sha256": str(run_binding),
        "pilot_roles": roles,
    }


def baseline_target_features(
    logits: np.ndarray, target_ids: Sequence[str], target_groups: Sequence[str]
) -> list[dict[str, Any]]:
    """Compute target entropy and top-two logit margin in float64."""

    values = np.asarray(logits, dtype=np.float64)
    _require(values.ndim == 2 and values.shape[0] == len(target_ids), "Baseline shape")
    _require(len(target_ids) == len(target_groups), "Target metadata shape")
    shifted = values - np.max(values, axis=1, keepdims=True)
    exp = np.exp(shifted)
    probabilities = exp / np.sum(exp, axis=1, keepdims=True)
    log_probabilities = shifted - np.log(np.sum(exp, axis=1, keepdims=True))
    entropies = -np.sum(probabilities * log_probabilities, axis=1)
    top_two = np.partition(values, -2, axis=1)[:, -2:]
    margins = np.max(top_two, axis=1) - np.min(top_two, axis=1)
    return [
        {
            "target_index": index,
            "target_id": str(target_ids[index]),
            "target_group": str(target_groups[index]),
            "baseline_entropy": float(entropies[index]),
            "baseline_top_two_logit_margin": float(margins[index]),
        }
        for index in range(len(target_ids))
    ]


def analyze_target_sensitivity(
    baseline_features: Sequence[Mapping[str, Any]],
    response_rows: Sequence[Mapping[str, Any]],
    *,
    expected_target_count: int | None = None,
) -> dict[str, Any]:
    """Build F4 profiles and descriptive target sensitivity diagnostics."""

    feature_index = {
        (str(row["model"]), int(row["target_index"])): row for row in baseline_features
    }
    sums: dict[tuple[Any, ...], float] = defaultdict(float)
    counts: dict[tuple[Any, ...], int] = defaultdict(int)
    metadata: dict[tuple[Any, ...], tuple[str, str]] = {}
    for row in response_rows:
        kind = str(row["condition_kind"])
        _require(kind != "zero_direction", "Zero rows do not enter F4")
        model = str(row["model"])
        target_index = int(row["target_index"])
        _require((model, target_index) in feature_index, "Missing baseline feature")
        feature = feature_index[(model, target_index)]
        _require(
            str(row["target_id"]) == str(feature["target_id"])
            and str(row["target_group"]) == str(feature["target_group"]),
            "Response target metadata changed",
        )
        for endpoint, value in endpoint_values(row).items():
            key = (model, kind, endpoint, target_index)
            sums[key] += value
            counts[key] += 1
            metadata[key] = (str(row["target_id"]), str(row["target_group"]))
    profiles = []
    for key in sorted(sums):
        model, kind, endpoint, target_index = key
        target_id, target_group = metadata[key]
        feature = feature_index[(model, target_index)]
        profiles.append(
            {
                "model": model,
                "condition_kind": kind,
                "endpoint": endpoint,
                "target_index": target_index,
                "target_id": target_id,
                "target_group": target_group,
                "response_mean": sums[key] / counts[key],
                "response_rows": counts[key],
                "baseline_entropy": float(feature["baseline_entropy"]),
                "baseline_top_two_logit_margin": float(
                    feature["baseline_top_two_logit_margin"]
                ),
            }
        )
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in profiles:
        grouped[(row["model"], row["condition_kind"], row["endpoint"])].append(row)
    associations = []
    group_heterogeneity = []
    for key, rows in sorted(grouped.items()):
        rows.sort(key=lambda row: int(row["target_index"]))
        if expected_target_count is not None:
            _require(
                len(rows) == expected_target_count
                and [int(row["target_index"]) for row in rows]
                == list(range(expected_target_count)),
                f"Incomplete F4 target profile: {key}",
            )
        response = [float(row["response_mean"]) for row in rows]
        associations.append(
            {
                "model": key[0],
                "condition_kind": key[1],
                "endpoint": key[2],
                "target_count": len(rows),
                "baseline_entropy_spearman": spearman_rank_correlation(
                    [float(row["baseline_entropy"]) for row in rows], response
                ),
                "baseline_top_two_logit_margin_spearman": spearman_rank_correlation(
                    [float(row["baseline_top_two_logit_margin"]) for row in rows],
                    response,
                ),
            }
        )
        by_group: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            by_group[str(row["target_group"])].append(float(row["response_mean"]))
        means = {
            group: float(np.mean(values)) for group, values in sorted(by_group.items())
        }
        group_heterogeneity.append(
            {
                "model": key[0],
                "condition_kind": key[1],
                "endpoint": key[2],
                "group_means": means,
                "group_mean_range": max(means.values()) - min(means.values()),
                "interpretation": "sensitivity_diagnostic_not_source_specificity",
            }
        )
    return {
        "family_id": "F4_target_sensitivity",
        "status": "exploratory_point_derivation_complete",
        "profile_scope": {
            "level": "coarse_condition_kind_pooled_target_diagnostic",
            "pooled_over": [
                "sign",
                "depth",
                "dose",
                "source_form",
                "item_or_prototype_or_random_seed",
            ],
            "not_a_fixed_stratum_effect": True,
        },
        "baseline_features": list(baseline_features),
        "target_profiles": profiles,
        "associations": associations,
        "target_group_heterogeneity": group_heterogeneity,
    }


def output_direction_pair_metrics(
    *,
    negative_sketch: np.ndarray,
    positive_sketch: np.ndarray,
    negative_positive_ids: np.ndarray,
    negative_positive_values: np.ndarray,
    negative_negative_ids: np.ndarray,
    negative_negative_values: np.ndarray,
    positive_positive_ids: np.ndarray,
    positive_positive_values: np.ndarray,
    positive_negative_ids: np.ndarray,
    positive_negative_values: np.ndarray,
) -> dict[str, float | None]:
    """Compare one +/- pair within a model; no vectors are persisted."""

    top_k = len(negative_positive_ids)
    arrays = (
        negative_positive_ids,
        negative_positive_values,
        negative_negative_ids,
        negative_negative_values,
        positive_positive_ids,
        positive_positive_values,
        positive_negative_ids,
        positive_negative_values,
    )
    _require(top_k > 0 and all(len(value) == top_k for value in arrays), "Top-k shape")
    pos_swap = (
        len(set(map(int, positive_positive_ids)) & set(map(int, negative_negative_ids)))
        / top_k
    )
    neg_swap = (
        len(set(map(int, positive_negative_ids)) & set(map(int, negative_positive_ids)))
        / top_k
    )
    sign_purity = float(
        np.mean(
            np.concatenate(
                (
                    positive_positive_values > 0,
                    negative_positive_values > 0,
                    positive_negative_values < 0,
                    negative_negative_values < 0,
                )
            )
        )
    )
    return {
        "countsketch_cosine": cosine_at_comparison(negative_sketch, positive_sketch),
        "sign_reversed_countsketch_cosine": cosine_at_comparison(
            -negative_sketch, positive_sketch
        ),
        "positive_to_negative_top64_overlap": pos_swap,
        "negative_to_positive_top64_overlap": neg_swap,
        "mean_swapped_top64_overlap": 0.5 * (pos_swap + neg_swap),
        "top_tail_sign_purity": sign_purity,
    }


def _summarize_metric_records(
    records: Sequence[Mapping[str, Any]], group_fields: Sequence[str]
) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        groups[tuple(row[field] for field in group_fields)].append(row)
    result = []
    metric_names = (
        "countsketch_cosine",
        "sign_reversed_countsketch_cosine",
        "positive_to_negative_top64_overlap",
        "negative_to_positive_top64_overlap",
        "mean_swapped_top64_overlap",
        "top_tail_sign_purity",
    )
    for key, rows in sorted(groups.items()):
        summaries: dict[str, Any] = {}
        for name in metric_names:
            values = [float(row[name]) for row in rows if row[name] is not None]
            summaries[name] = (
                _mean_median(values) if values else {"n": 0, "value": None}
            )
        result.append(
            {
                **dict(zip(group_fields, key, strict=True)),
                "sign_pairs": len(rows),
                "statistics": summaries,
            }
        )
    return result


def cross_model_scalar_rank_concordance(
    target_profiles: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Compare only scalar target ranks; role-namespaced random rows are not aligned."""

    grouped: dict[tuple[str, str], dict[str, dict[int, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for row in target_profiles:
        key = (str(row["condition_kind"]), str(row["endpoint"]))
        grouped[key][str(row["model"])][int(row["target_index"])] = float(
            row["response_mean"]
        )
    result = []
    for (kind, endpoint), by_model in sorted(grouped.items()):
        models = sorted(by_model)
        for left_index, left in enumerate(models):
            for right in models[left_index + 1 :]:
                targets = sorted(set(by_model[left]) & set(by_model[right]))
                _require(len(targets) >= 2, "Cross-model target profile incomplete")
                result.append(
                    {
                        "left_model": left,
                        "right_model": right,
                        "condition_kind": kind,
                        "endpoint": endpoint,
                        "target_count": len(targets),
                        "spearman": spearman_rank_correlation(
                            [by_model[left][target] for target in targets],
                            [by_model[right][target] for target in targets],
                        ),
                        "comparison_space": "scalar_target_profile_only",
                    }
                )
    return result


def source_shard_geometry(
    *,
    role: str,
    directions: np.ndarray,
    wrapper_deltas: np.ndarray,
    view_mask: np.ndarray,
    item_start: int,
    item_systems: Mapping[int, str],
    token_rows: Mapping[tuple[int, str], Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]] | int]:
    """Validate and summarize one mmap-backed source shard."""

    _require(directions.ndim == 4 and wrapper_deltas.ndim == 5, "Source rank changed")
    _require(view_mask.shape == directions.shape[:2], "Source mask shape changed")
    _require(wrapper_deltas.shape[:2] == view_mask.shape, "Delta mask shape changed")
    _require(wrapper_deltas.shape[2] == 4, "Wrapper count changed")
    _require(wrapper_deltas.shape[3:] == directions.shape[2:], "Source width changed")
    dispersion_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    availability_rows: list[dict[str, Any]] = []
    integrity_vectors = 0
    for local_index in range(len(view_mask)):
        item_index = item_start + local_index
        system = str(item_systems[item_index])
        for view_index, view in enumerate(VIEW_ORDER):
            present = bool(view_mask[local_index, view_index])
            availability_rows.append(
                {
                    "model": role,
                    "item_index": item_index,
                    "glyph_system": system,
                    "source_form": view,
                    "status": "present" if present else "structurally_absent",
                }
            )
            delta = np.asarray(wrapper_deltas[local_index, view_index])
            direction = np.asarray(directions[local_index, view_index])
            if not present:
                _require(
                    bool(np.isnan(delta).all() and np.isnan(direction).all()),
                    "Absent source form is not NaN",
                )
                continue
            _require((item_index, view) in token_rows, "Tokenizer signature missing")
            recomputed = np.mean(delta, axis=0, dtype=np.float64).astype(np.float32)
            _require(
                np.array_equal(recomputed, direction), "Direction mean integrity failed"
            )
            token = token_rows[(item_index, view)]
            for depth_index in range(direction.shape[0]):
                center = direction[depth_index].astype(np.float64)
                wrappers = delta[:, depth_index].astype(np.float64)
                center_rms = float(np.sqrt(np.mean(np.square(center))))
                residual_rms = float(
                    np.sqrt(np.mean(np.square(wrappers - center[None, :])))
                )
                wrapper_cosines = [
                    cosine_at_comparison(wrapper, center) for wrapper in wrappers
                ]
                _require(
                    all(value is not None for value in wrapper_cosines), "Zero source"
                )
                dispersion_rows.append(
                    {
                        "model": role,
                        "item_index": item_index,
                        "glyph_system": system,
                        "source_form": view,
                        "depth_index": depth_index,
                        "wrapper_residual_rms_over_direction_rms": (
                            residual_rms / center_rms if center_rms > 0.0 else None
                        ),
                        "mean_wrapper_direction_cosine": float(
                            np.mean([float(value) for value in wrapper_cosines])
                        ),
                        "raw_token_count": int(token["raw_token_count"]),
                        "added_count_signature": str(token["added_count_signature"]),
                    }
                )
                integrity_vectors += 1
        for pair, left, right in PAIR_ORDER:
            left_index = VIEW_ORDER.index(left)
            right_index = VIEW_ORDER.index(right)
            status = (
                "present"
                if bool(view_mask[local_index, left_index])
                and bool(view_mask[local_index, right_index])
                else "structurally_unavailable"
            )
            if status != "present":
                pair_rows.append(
                    {
                        "model": role,
                        "item_index": item_index,
                        "glyph_system": system,
                        "pair": pair,
                        "status": status,
                        "depth_cosines": None,
                    }
                )
                continue
            left_values = np.asarray(directions[local_index, left_index])
            right_values = np.asarray(directions[local_index, right_index])
            cosines = [
                cosine_at_comparison(left_values[index], right_values[index])
                for index in range(left_values.shape[0])
            ]
            _require(all(value is not None for value in cosines), "Zero source pair")
            left_token = token_rows[(item_index, left)]
            right_token = token_rows[(item_index, right)]
            pair_rows.append(
                {
                    "model": role,
                    "item_index": item_index,
                    "glyph_system": system,
                    "pair": pair,
                    "status": "present",
                    "depth_cosines": [float(value) for value in cosines],
                    "final_minus_first": float(cosines[-1]) - float(cosines[0]),
                    "left_token_signature": (
                        f"{left_token['raw_token_count']}|"
                        f"{left_token['added_count_signature']}"
                    ),
                    "right_token_signature": (
                        f"{right_token['raw_token_count']}|"
                        f"{right_token['added_count_signature']}"
                    ),
                    "token_count_signature_exact_match": bool(
                        int(left_token["raw_token_count"])
                        == int(right_token["raw_token_count"])
                        and str(left_token["added_count_signature"])
                        == str(right_token["added_count_signature"])
                    ),
                }
            )
    return {
        "direction_vectors_integrity_checked": integrity_vectors,
        "dispersion_rows": dispersion_rows,
        "pair_rows": pair_rows,
        "availability_rows": availability_rows,
    }


def summarize_source_geometry(
    dispersion_rows: Sequence[Mapping[str, Any]],
    pair_rows: Sequence[Mapping[str, Any]],
    availability_rows: Sequence[Mapping[str, Any]],
    *,
    integrity_vectors: int,
) -> dict[str, Any]:
    pair_groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    trajectory_groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    pair_stratum_groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    pair_match_groups: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in pair_rows:
        if row["status"] != "present":
            continue
        for depth, value in enumerate(row["depth_cosines"]):
            pair_groups[(row["model"], row["glyph_system"], row["pair"], depth)].append(
                float(value)
            )
            pair_stratum_groups[
                (
                    row["model"],
                    row["pair"],
                    depth,
                    row["left_token_signature"],
                    row["right_token_signature"],
                )
            ].append(float(value))
            pair_match_groups[
                (
                    row["model"],
                    row["glyph_system"],
                    row["pair"],
                    depth,
                    bool(row["token_count_signature_exact_match"]),
                )
            ].append(float(value))
        trajectory_groups[(row["model"], row["glyph_system"], row["pair"])].append(
            float(row["final_minus_first"])
        )
    pair_summaries = [
        {
            "model": key[0],
            "glyph_system": key[1],
            "pair": key[2],
            "depth_index": key[3],
            "cosine": _mean_median(values),
        }
        for key, values in sorted(pair_groups.items())
    ]
    trajectories = [
        {
            "model": key[0],
            "glyph_system": key[1],
            "pair": key[2],
            "final_minus_first": _mean_median(values),
        }
        for key, values in sorted(trajectory_groups.items())
    ]
    dispersion_groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    stratum_groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in dispersion_rows:
        dispersion_groups[
            (row["model"], row["glyph_system"], row["source_form"], row["depth_index"])
        ].append(row)
        stratum_groups[
            (
                row["model"],
                row["source_form"],
                row["depth_index"],
                row["raw_token_count"],
                row["added_count_signature"],
            )
        ].append(row)
    wrapper_dispersion = []
    for key, rows in sorted(dispersion_groups.items()):
        residual = [
            float(row["wrapper_residual_rms_over_direction_rms"])
            for row in rows
            if row["wrapper_residual_rms_over_direction_rms"] is not None
        ]
        wrapper_dispersion.append(
            {
                "model": key[0],
                "glyph_system": key[1],
                "source_form": key[2],
                "depth_index": key[3],
                "relative_residual_rms": _mean_median(residual),
                "wrapper_direction_cosine": _mean_median(
                    [float(row["mean_wrapper_direction_cosine"]) for row in rows]
                ),
            }
        )
    token_strata = []
    for key, rows in sorted(stratum_groups.items()):
        token_strata.append(
            {
                "metric": "wrapper_direction_cosine",
                "model": key[0],
                "source_form": key[1],
                "depth_index": key[2],
                "raw_token_count": key[3],
                "added_count_signature": key[4],
                "items": len(rows),
                "wrapper_direction_cosine": _mean_median(
                    [float(row["mean_wrapper_direction_cosine"]) for row in rows]
                ),
                "scope": "token_count_signatures_only_no_exact_token_id_claim",
            }
        )
    for key, values in sorted(pair_stratum_groups.items()):
        token_strata.append(
            {
                "metric": "source_form_pair_cosine",
                "model": key[0],
                "pair": key[1],
                "depth_index": key[2],
                "left_token_signature": key[3],
                "right_token_signature": key[4],
                "items": len(values),
                "pair_cosine": _mean_median(values),
                "scope": "token_count_signatures_only_no_exact_token_id_claim",
            }
        )
    tokenizer_match_summaries = [
        {
            "model": key[0],
            "glyph_system": key[1],
            "pair": key[2],
            "depth_index": key[3],
            "token_count_signature_exact_match": key[4],
            "items": len(values),
            "pair_cosine": _mean_median(values),
            "scope": "token_count_signatures_only_no_exact_token_id_claim",
        }
        for key, values in sorted(pair_match_groups.items())
    ]
    availability_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in availability_rows:
        availability_counts[
            (str(row["model"]), str(row["source_form"]), str(row["status"]))
        ] += 1
    return {
        "family_id": "F6_source_geometry",
        "status": "exploratory_point_derivation_complete",
        "direction_mean_integrity_vectors_checked": integrity_vectors,
        "glyph_name_decomposition_cosines": pair_summaries,
        "wrapper_dispersion": wrapper_dispersion,
        "depth_trajectories": trajectories,
        "tokenizer_signature_strata": token_strata,
        "tokenizer_signature_match_summaries": tokenizer_match_summaries,
        "source_form_availability": [
            {
                "model": key[0],
                "source_form": key[1],
                "status": key[2],
                "items": count,
            }
            for key, count in sorted(availability_counts.items())
        ],
        "structural_missingness": [
            dict(row) for row in availability_rows if row["status"] != "present"
        ],
        "cross_model_vector_comparison": "forbidden_different_hidden_spaces",
    }


def _assert_exact_tree(run_root: Path, roles: Sequence[str], pilots: set[str]) -> None:
    acquisition = _acquisition_config()
    systems = [str(value) for value in acquisition["population"]["system_order"]]
    for role in roles:
        root = run_root / role
        _require((root / "baseline").is_dir(), f"Baseline missing: {role}")
        source = root / "source"
        expected_source = {f"shard-{index:04d}" for index in range(12)}
        _require(
            {path.name for path in source.iterdir() if path.is_dir()}
            == expected_source,
            f"Source tree changed: {role}",
        )
        if role not in pilots:
            _require(not (root / "pilot").exists(), f"Nonpilot response tree: {role}")
            continue
        pilot = root / "pilot"
        expected = {
            "zero": {"all-sites"},
            "item": expected_source,
            "prototype": set(systems),
            "random": {f"site-{index:02d}" for index in range(8)},
        }
        _require(
            {path.name for path in pilot.iterdir() if path.is_dir()} == set(expected),
            f"Pilot tree kinds changed: {role}",
        )
        for kind, names in expected.items():
            _require(
                {path.name for path in (pilot / kind).iterdir() if path.is_dir()}
                == names,
                f"Pilot tree changed: {role}/{kind}",
            )


def _zero_gate(
    run_root: Path,
    pilots: Sequence[str],
    gate: ValueOpenGate,
    preflight_directory: Path,
) -> list[dict[str, Any]]:
    results = []
    model_config = _read_yaml(
        _root() / "configs" / "semantic_atlas_cross_model_replication_v0.yaml"
    )["models"]
    for role in pilots:
        _read_json(preflight_directory / f"{role}.json")
        vocab_size = int(model_config[role]["expected_vocab_size"])
        directory = run_root / role / "pilot" / "zero" / "all-sites"
        rows = gate.open_jsonl(directory / "response_ledger.jsonl", zero_control=True)
        result = validate_zero_control(
            rows,
            top_positive_ids=gate.open_array(
                directory / "top_positive_ids.npy", zero_control=True
            ),
            top_positive_values=gate.open_array(
                directory / "top_positive_values.npy", zero_control=True
            ),
            top_negative_ids=gate.open_array(
                directory / "top_negative_ids.npy", zero_control=True
            ),
            top_negative_values=gate.open_array(
                directory / "top_negative_values.npy", zero_control=True
            ),
            countsketch=gate.open_array(
                directory / "countsketch.npy", zero_control=True
            ),
            vocab_size=vocab_size,
        )
        results.append({"model": role, **result})
    gate.complete_zero_gate()
    return results


def _response_directories(run_root: Path, role: str) -> list[Path]:
    pilot = run_root / role / "pilot"
    return [
        *sorted((pilot / "item").iterdir()),
        *sorted((pilot / "prototype").iterdir()),
        *sorted((pilot / "random").iterdir()),
    ]


def _f4_inputs(
    run_root: Path,
    pilots: Sequence[str],
    gate: ValueOpenGate,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline = []
    response_rows = []
    response_counts: dict[str, int] = defaultdict(int)
    for role in pilots:
        directory = run_root / role / "baseline"
        metadata = _read_json(directory / "metadata.json")
        logits = gate.open_array(directory / "target_logits.npy")
        features = baseline_target_features(
            logits, metadata["target_ids"], metadata["target_groups"]
        )
        baseline.extend({"model": role, **row} for row in features)
        del logits
        for response_directory in _response_directories(run_root, role):
            rows = gate.open_jsonl(response_directory / "response_ledger.jsonl")
            expected_kind = {
                "item": "item_source_form",
                "prototype": "glyph_system_source_form_prototype",
                "random": "random_direction",
            }[response_directory.parent.name]
            for index, row in enumerate(rows):
                _require(int(row["response_index"]) == index, "Response index changed")
                _require(
                    row.get("condition_kind") == expected_kind,
                    "Response shard condition changed",
                )
                sign = int(row["sign"])
                _require(
                    sign == 1
                    if expected_kind == "random_direction"
                    else sign in {-1, 1},
                    "Response sign grid changed",
                )
                response_rows.append({"model": role, **row})
                response_counts[role] += 1
    expected_nonzero = int(
        _acquisition_config()["pilot"]["expected_response_rows_per_model"]
    ) - int(
        _acquisition_config()["pilot"]["zero_grid"]["expected_response_rows_per_model"]
    )
    for role in pilots:
        _require(
            response_counts[role] == expected_nonzero, f"F4 rows incomplete: {role}"
        )
    return baseline, response_rows


def _f5(
    run_root: Path,
    pilots: Sequence[str],
    gate: ValueOpenGate,
    target_profiles: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    pair_records: list[dict[str, Any]] = []
    per_model_counts: dict[str, int] = defaultdict(int)
    model_config = _read_yaml(
        _root() / "configs" / "semantic_atlas_cross_model_replication_v0.yaml"
    )["models"]
    for role in pilots:
        vocab_size = int(model_config[role]["expected_vocab_size"])
        pilot = run_root / role / "pilot"
        for kind in ("item", "prototype"):
            for directory in sorted((pilot / kind).iterdir()):
                rows = gate.open_jsonl(directory / "response_ledger.jsonl")
                arrays = {
                    name: gate.open_array(directory / f"{name}.npy")
                    for name in (
                        "top_positive_ids",
                        "top_positive_values",
                        "top_negative_ids",
                        "top_negative_values",
                        "countsketch",
                    )
                }
                _require(
                    all(array.shape[0] == len(rows) for array in arrays.values()),
                    "F5 response array row count changed",
                )
                for name in ("top_positive_ids", "top_negative_ids"):
                    ids = arrays[name]
                    _require(np.issubdtype(ids.dtype, np.integer), "F5 top ID dtype")
                    _require(
                        bool(((ids >= 0) & (ids < vocab_size)).all()),
                        "F5 top ID outside model vocabulary",
                    )
                for name in (
                    "top_positive_values",
                    "top_negative_values",
                    "countsketch",
                ):
                    _require(
                        bool(np.isfinite(arrays[name]).all()), "F5 nonfinite array"
                    )
                by_key: dict[tuple[Any, ...], dict[int, Mapping[str, Any]]] = (
                    defaultdict(dict)
                )
                for index, row in enumerate(rows):
                    _require(
                        int(row["response_index"]) == index, "Response index changed"
                    )
                    key_fields = (
                        (
                            "item_index",
                            "glyph_system",
                            "view",
                            "target_index",
                            "site_index",
                            "magnitude",
                        )
                        if kind == "item"
                        else (
                            "glyph_system",
                            "view",
                            "target_index",
                            "site_index",
                            "magnitude",
                        )
                    )
                    key = tuple(row[field] for field in key_fields)
                    sign = int(row["sign"])
                    _require(
                        sign in {-1, 1} and sign not in by_key[key], "Sign pair changed"
                    )
                    by_key[key][sign] = row
                for key, pair in by_key.items():
                    _require(set(pair) == {-1, 1}, "Incomplete sign pair")
                    negative_index = int(pair[-1]["response_index"])
                    positive_index = int(pair[1]["response_index"])
                    metrics = output_direction_pair_metrics(
                        negative_sketch=arrays["countsketch"][negative_index],
                        positive_sketch=arrays["countsketch"][positive_index],
                        negative_positive_ids=arrays["top_positive_ids"][
                            negative_index
                        ],
                        negative_positive_values=arrays["top_positive_values"][
                            negative_index
                        ],
                        negative_negative_ids=arrays["top_negative_ids"][
                            negative_index
                        ],
                        negative_negative_values=arrays["top_negative_values"][
                            negative_index
                        ],
                        positive_positive_ids=arrays["top_positive_ids"][
                            positive_index
                        ],
                        positive_positive_values=arrays["top_positive_values"][
                            positive_index
                        ],
                        positive_negative_ids=arrays["top_negative_ids"][
                            positive_index
                        ],
                        positive_negative_values=arrays["top_negative_values"][
                            positive_index
                        ],
                    )
                    pair_records.append(
                        {
                            "model": role,
                            "condition_kind": str(pair[1]["condition_kind"]),
                            "glyph_system": str(pair[1]["glyph_system"]),
                            "source_form": str(pair[1]["view"]),
                            "depth_fraction": float(pair[1]["depth_fraction"]),
                            "magnitude": float(pair[1]["magnitude"]),
                            **metrics,
                        }
                    )
                    per_model_counts[role] += 1
                del arrays
    summaries = _summarize_metric_records(
        pair_records,
        (
            "model",
            "condition_kind",
            "glyph_system",
            "source_form",
            "depth_fraction",
            "magnitude",
        ),
    )
    acquisition = _acquisition_config()["pilot"]
    expected_pairs = (
        int(acquisition["item_grid"]["expected_response_rows_per_model"])
        + int(acquisition["prototype_grid"]["expected_response_rows_per_model"])
    ) // 2
    for role in pilots:
        _require(
            per_model_counts[role] == expected_pairs, f"F5 pairs incomplete: {role}"
        )
    return {
        "family_id": "F5_output_direction",
        "status": "exploratory_point_derivation_complete",
        "within_model_sign_pair_summaries": summaries,
        "within_model_sign_pairs": dict(sorted(per_model_counts.items())),
        "cross_model_rank_concordance": cross_model_scalar_rank_concordance(
            target_profiles
        ),
        "random_direction_sign_pair": {
            "status": "unavailable",
            "reason": "frozen_random_grid_has_positive_orientation_only",
        },
        "raw_countsketch_or_token_id_cross_model_comparisons": 0,
    }


def _f6(
    run_root: Path,
    roles: Sequence[str],
    gate: ValueOpenGate,
    preflight_directory: Path,
) -> dict[str, Any]:
    all_dispersion: list[dict[str, Any]] = []
    all_pairs: list[dict[str, Any]] = []
    all_availability: list[dict[str, Any]] = []
    integrity_vectors = 0
    for role in roles:
        preflight = _read_json(preflight_directory / f"{role}.json")
        token_rows = {
            (int(row["item_index"]), str(row["view"])): row
            for row in preflight["source_rows"]
        }
        _require(len(token_rows) == 912, f"Tokenizer source rows changed: {role}")
        for shard_index in range(12):
            directory = run_root / role / "source" / f"shard-{shard_index:04d}"
            receipt = _read_json(directory / "receipt.json")
            item_start = int(receipt["item_start"])
            observations = _read_jsonl(directory / "observations.jsonl")
            item_systems: dict[int, str] = {}
            for row in observations:
                item = int(row["global_item_index"])
                system = str(row["glyph_system"])
                _require(
                    item_systems.setdefault(item, system) == system,
                    "Source item system changed",
                )
            directions = gate.open_array(directory / "directions.npy")
            deltas = gate.open_array(directory / "wrapper_deltas.npy")
            mask = gate.open_array(directory / "view_mask.npy")
            result = source_shard_geometry(
                role=role,
                directions=directions,
                wrapper_deltas=deltas,
                view_mask=mask,
                item_start=item_start,
                item_systems=item_systems,
                token_rows=token_rows,
            )
            integrity_vectors += int(result["direction_vectors_integrity_checked"])
            all_dispersion.extend(result["dispersion_rows"])
            all_pairs.extend(result["pair_rows"])
            all_availability.extend(result["availability_rows"])
            del directions, deltas, mask
    expected_integrity = 9 * int(
        _acquisition_config()["source_bank"][
            "expected_mean_direction_vectors_per_model"
        ]
    )
    _require(integrity_vectors == expected_integrity, "F6 source bank incomplete")
    return summarize_source_geometry(
        all_dispersion,
        all_pairs,
        all_availability,
        integrity_vectors=integrity_vectors,
    )


def _validate_preflight_bindings(
    preflight_directory: Path, roles: Sequence[str]
) -> dict[str, str]:
    """Bind tokenizer metadata to the prospectively committed receipts."""

    committed_directory = (_root() / PREFLIGHT_DIRECTORY).resolve(strict=True)
    aggregate_path = committed_directory / "aggregate.json"
    aggregate = _read_json(aggregate_path)
    _require(
        aggregate.get("protocol_id") == SOURCE_PROTOCOL_ID
        and aggregate.get("status")
        == "runtime_and_tokenizer_preflight_pass_zero_model_forward",
        "Committed runtime preflight is invalid",
    )
    _require(
        aggregate.get("model_order") == list(roles),
        "Committed runtime preflight role order changed",
    )
    supplied_aggregate = preflight_directory / "aggregate.json"
    _require(
        supplied_aggregate.is_file()
        and _sha256(supplied_aggregate) == _sha256(aggregate_path),
        "Supplied runtime preflight aggregate is not the frozen receipt",
    )
    bindings: dict[str, str] = {}
    for role in roles:
        supplied = preflight_directory / f"{role}.json"
        committed = committed_directory / f"{role}.json"
        expected = str(aggregate.get("receipt_sha256", {}).get(role))
        _require(
            supplied.is_file()
            and committed.is_file()
            and _sha256(supplied) == _sha256(committed) == expected,
            f"Tokenizer preflight is not the frozen receipt: {role}",
        )
        bindings[role] = expected
    return bindings


def execute_analysis(
    *,
    run_root: Path,
    scientific_open_receipt: Path,
    preflight_directory: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """Run zero-first F4--F6 derivation and atomically seal a new directory."""

    _config()
    run_root = run_root.expanduser().resolve(strict=True)
    receipt_path = scientific_open_receipt.expanduser().resolve(strict=True)
    preflight_directory = preflight_directory.expanduser().resolve(strict=True)
    output_directory = output_directory.expanduser().resolve()
    _require(
        not output_directory.exists(), f"Output already exists: {output_directory}"
    )
    _require(
        not receipt_path.is_relative_to(run_root),
        "Scientific-open receipt must be outside the sealed run root",
    )
    _require(
        not output_directory.is_relative_to(run_root),
        "Analysis output must be outside the sealed run root",
    )
    config = _config()
    roles = [str(value) for value in config["acquisition_gate"]["required_role_order"]]
    pilots = [str(value) for value in config["acquisition_gate"]["pilot_roles"]]
    preflight_bindings = _validate_preflight_bindings(preflight_directory, roles)
    same_process_audit = _audit_closeout_same_process(run_root, receipt_path)
    receipt = _read_json(receipt_path)
    closeout = validate_scientific_open_receipt(receipt, run_root)
    gate = ValueOpenGate()
    gate.authorize()
    _assert_exact_tree(run_root, roles, set(pilots))
    zero = _zero_gate(run_root, pilots, gate, preflight_directory)
    baseline, response_rows = _f4_inputs(run_root, pilots, gate)
    f4 = analyze_target_sensitivity(baseline, response_rows, expected_target_count=32)
    del baseline, response_rows
    f5 = _f5(run_root, pilots, gate, f4["target_profiles"])
    f6 = _f6(run_root, roles, gate, preflight_directory)
    stage = (
        output_directory.parent / f".{output_directory.name}.stage-{uuid.uuid4().hex}"
    )
    _require(not stage.exists(), "Output stage collision")
    stage.mkdir(parents=True)
    scientific_open_receipt_sha256 = _sha256(receipt_path)
    zero_receipt = {
        "schema_version": 1,
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "all_pilot_zero_controls_exact_noop",
        "run_binding_root_sha256": closeout["external_closeout_root_sha256"],
        "scientific_open_receipt_sha256": scientific_open_receipt_sha256,
        "models": zero,
        "zero_phase_value_open_trace": gate.trace[
            : gate.trace.index("all_pilot_zero_controls_exact_noop") + 1
        ],
        "scientific_values_opened_before_all_zero": False,
    }
    validate_zero_gate_receipt(
        zero_receipt,
        expected_run_binding_root_sha256=closeout["external_closeout_root_sha256"],
        expected_scientific_open_receipt_sha256=scientific_open_receipt_sha256,
        expected_pilot_roles=pilots,
    )
    outputs = {
        "zero_hook_exact_noop.json": zero_receipt,
        "F4_target_sensitivity.json": f4,
        "F5_output_direction.json": f5,
        "F6_source_geometry.json": f6,
    }
    bindings: dict[str, dict[str, Any]] = {}
    for name, value in outputs.items():
        path = stage / name
        _write_json(path, value)
        bindings[name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    analysis_receipt = {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "exploratory_f4_f5_f6_point_derivation_complete",
        "decision_status": "no_primary_no_significance_test_no_confirmatory_verdict",
        "input_closeout": {
            **closeout,
            "same_process_audit": same_process_audit,
            "scientific_open_receipt_sha256": scientific_open_receipt_sha256,
            "scientific_open_receipt_path": str(receipt_path),
            "preflight_receipt_sha256": preflight_bindings,
            "input_binding_sha256": _canonical_sha256(
                {"closeout": closeout, "preflight": preflight_bindings}
            ),
        },
        "value_open_order": gate.trace,
        "zero_hook_gate": "all_pilot_exact_noop_before_nonzero_values",
        "outputs": bindings,
        "raw_arrays_copied": False,
        "bootstrap_intervals_included": False,
        "claim_boundary": config["claim_boundary"],
    }
    _write_json(stage / "analysis_receipt.json", analysis_receipt)
    os.replace(stage, output_directory)
    return analysis_receipt


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--run-root", type=Path, required=True)
    root.add_argument("--scientific-open-receipt", type=Path, required=True)
    root.add_argument("--preflight-directory", type=Path, default=PREFLIGHT_DIRECTORY)
    root.add_argument("--output-directory", type=Path, required=True)
    return root


def main() -> None:
    args = parser().parse_args()
    result = execute_analysis(
        run_root=args.run_root,
        scientific_open_receipt=args.scientific_open_receipt,
        preflight_directory=args.preflight_directory,
        output_directory=args.output_directory,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
