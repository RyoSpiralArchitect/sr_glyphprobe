#!/usr/bin/env python3
"""Run T13-EA F4--F6 under the frozen zero-gate numerical amendment v1.

This is an execution wrapper around the frozen v0 geometry helpers.  It does
not revise F4--F6.  It replaces only the rejected exact-JS zero gate with the
prospectively frozen amendment: primitive no-op observables remain exact, while
the derived JS scalar may contain a finite, two-sided float32 log/exp roundtrip
residual bounded by eight float32 epsilons.

The same-process full closeout rehash finishes before the first zero-control
value is opened.  Every pilot zero-control ledger then passes the amended gate
before any baseline, nonzero response, CountSketch, or source-bank value is
opened.  Output is written atomically outside the sealed run root and is never
overwritten.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import ctypes
import errno
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import sys
import uuid
from typing import Any

import numpy as np


AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
SOURCE_ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
AMENDMENT_CONFIG_PATH = Path(
    "configs/emoji_steering_specificity_zero_gate_amendment_v1.yaml"
)
PREFLIGHT_DIRECTORY = Path("validation/emoji_steering_specificity_harvest_v0")
ZERO_GATE_STATUS = "primitive_exact_noop_with_bounded_float32_js_roundtrip"
ZERO_RECEIPT_STATUS = (
    "all_pilot_zero_controls_primitive_exact_with_bounded_float32_js_roundtrip"
)
ANALYSIS_STATUS = (
    "exploratory_f4_f5_f6_point_derivation_complete_under_zero_gate_amendment_v1"
)
EXPECTED_ZERO_ROWS = 8 * 32
EXPECTED_SITE_COUNT = 8
EXPECTED_TARGET_COUNT = 32
EXACT_PRIMITIVES = [
    "kl_baseline_to_intervened_equals_zero",
    "total_variation_equals_zero",
    "logit_delta_rms_equals_zero",
    "baseline_entropy_equals_intervened_entropy",
    "baseline_argmax_equals_intervened_argmax",
    "argmax_flip_is_false",
    "top_positive_values_equal_zero",
    "top_negative_values_equal_zero",
    "countsketch_equals_zero",
    "top_positive_ids_in_vocab",
    "top_negative_ids_in_vocab",
    "baseline_argmax_id_in_vocab",
    "intervened_argmax_id_in_vocab",
]


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_v0() -> Any:
    path = _root() / "scripts" / "analyze_emoji_steering_specificity_geometry_v0.py"
    spec = importlib.util.spec_from_file_location(
        "analyze_emoji_steering_specificity_geometry_v0_for_v1", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Frozen v0 geometry analyzer is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V0 = _load_v0()
GeometryAnalysisError = V0.GeometryAnalysisError


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GeometryAnalysisError(message)


def _publish_directory_no_replace(stage: Path, destination: Path) -> None:
    """Atomically publish a directory while refusing every existing target.

    Python's ordinary ``rename``/``replace`` APIs may replace an existing empty
    directory.  The platform no-replace primitives close that race while
    retaining one-step publication of the already complete stage directory.
    Unsupported kernels fail closed instead of falling back to replacement.
    """

    _require(stage.is_dir() and not stage.is_symlink(), "Output stage is invalid")
    _require(stage.parent == destination.parent, "Output stage crossed a directory")
    source_bytes = os.fsencode(stage)
    destination_bytes = os.fsencode(destination)
    library = ctypes.CDLL(None, use_errno=True)
    ctypes.set_errno(0)
    if sys.platform.startswith("linux"):
        rename_no_replace = getattr(library, "renameat2", None)
        _require(
            rename_no_replace is not None,
            "Atomic no-replace publication is unavailable on this Linux libc",
        )
        rename_no_replace.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename_no_replace.restype = ctypes.c_int
        result = rename_no_replace(
            -100,  # AT_FDCWD
            source_bytes,
            -100,
            destination_bytes,
            1,  # RENAME_NOREPLACE
        )
    elif sys.platform == "darwin":
        rename_no_replace = getattr(library, "renamex_np", None)
        _require(
            rename_no_replace is not None,
            "Atomic no-replace publication is unavailable on this macOS libc",
        )
        rename_no_replace.argtypes = (
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        rename_no_replace.restype = ctypes.c_int
        result = rename_no_replace(
            source_bytes,
            destination_bytes,
            0x00000004,  # RENAME_EXCL
        )
    else:
        raise GeometryAnalysisError(
            f"Atomic no-replace publication is unsupported: {sys.platform}"
        )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        raise GeometryAnalysisError(f"Output already exists: {destination}")
    if error in {errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EINVAL}:
        raise GeometryAnalysisError(
            f"Atomic no-replace publication is unavailable: {os.strerror(error)}"
        )
    raise GeometryAnalysisError(
        f"Atomic no-replace publication failed: {os.strerror(error)}"
    )


def _audit_amendment_freeze_same_process() -> dict[str, Any]:
    """Audit the committed amendment bundle before closeout or value access."""

    path = (
        _root()
        / "scripts"
        / "audit_emoji_steering_specificity_zero_gate_amendment_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "audit_emoji_steering_specificity_zero_gate_amendment_v1_for_geometry", path
    )
    _require(
        spec is not None and spec.loader is not None,
        "Amendment freeze auditor is unavailable",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.audit_freeze()
    _require(isinstance(result, dict), "Amendment freeze audit returned no receipt")
    _require(
        result.get("status") == "amendment_freeze_audit_pass",
        "Amendment freeze audit failed",
    )
    _require(
        result.get("amendment_id") == AMENDMENT_ID,
        "Amendment freeze audit ID changed",
    )
    manifest = (
        _root()
        / "data"
        / "manifests"
        / "emoji_steering_specificity_zero_gate_amendment_v1.json"
    )
    _require(manifest.is_file(), "Amendment freeze manifest is missing")
    return {
        **dict(result),
        "freeze_manifest_path": str(manifest.relative_to(_root())),
        "freeze_manifest_sha256": V0._sha256(manifest),
    }


def _amendment_config() -> dict[str, Any]:
    """Load and fail closed on the frozen numerical amendment contract."""

    path = _root() / AMENDMENT_CONFIG_PATH
    value = V0._read_yaml(path)
    _require(value.get("amendment_id") == AMENDMENT_ID, "Amendment ID changed")
    _require(
        value.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Amendment source analysis changed",
    )
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Amendment source protocol changed",
    )
    _require(
        value.get("status_at_freeze")
        == "post_failure_nonadaptive_numerical_amendment_before_live_js_residual_magnitude_inspection",
        "Amendment freeze status changed",
    )
    corrected = value.get("corrected_zero_gate")
    _require(isinstance(corrected, dict), "Corrected zero gate is missing")
    js = corrected.get("js_divergence")
    _require(isinstance(js, dict), "Amended JS contract is missing")
    expected_tolerance = float(8 * np.finfo(np.float32).eps)
    _require(
        js.get("policy") == "bounded_float32_log_exp_roundtrip_residual",
        "Amended JS policy changed",
    )
    _require(
        type(js.get("float32_epsilon_multiplier")) is int
        and int(js["float32_epsilon_multiplier"]) == 8,
        "Amended JS epsilon multiplier changed",
    )
    _require(
        type(js.get("maximum_absolute")) in {int, float}
        and not isinstance(js.get("maximum_absolute"), bool)
        and float(js["maximum_absolute"]) == expected_tolerance,
        "Amended JS absolute bound changed",
    )
    _require(js.get("two_sided") is True, "Amended JS bound is not two-sided")
    exact = corrected.get("exact_primitives")
    _require(
        exact == EXACT_PRIMITIVES,
        "Exact primitive list changed in the amendment",
    )
    return value


def _js_tolerance(explicit: float | None = None) -> float:
    config = _amendment_config()
    configured = float(
        config["corrected_zero_gate"]["js_divergence"]["maximum_absolute"]
    )
    independently_derived = float(8 * np.finfo(np.float32).eps)
    _require(configured == independently_derived, "JS tolerance derivation changed")
    if explicit is not None:
        _require(
            math.isfinite(float(explicit)) and float(explicit) == independently_derived,
            "Explicit JS tolerance is not the frozen amendment bound",
        )
    return independently_derived


def _number(value: Any, label: str) -> float:
    _require(
        type(value) in {int, float} and not isinstance(value, bool),
        f"{label} is not numeric",
    )
    result = float(value)
    _require(math.isfinite(result), f"{label} is nonfinite")
    return result


def _integer(value: Any, label: str) -> int:
    _require(type(value) is int, f"{label} is not an integer")
    return int(value)


def _expected_target_identity(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[str]]:
    _require(len(rows) == EXPECTED_TARGET_COUNT, "Expected target grid changed")
    ids: list[str] = []
    groups: list[str] = []
    for index, row in enumerate(rows):
        target_id = row.get("id")
        target_group = row.get("group")
        _require(
            isinstance(target_id, str) and target_id,
            f"Expected target ID missing: {index}",
        )
        _require(
            isinstance(target_group, str) and target_group,
            f"Expected target group missing: {index}",
        )
        ids.append(target_id)
        groups.append(target_group)
    _require(len(ids) == len(set(ids)), "Expected target IDs are not unique")
    return ids, groups


def validate_zero_control_v1(
    rows: Sequence[Mapping[str, Any]],
    *,
    top_positive_ids: np.ndarray,
    top_positive_values: np.ndarray,
    top_negative_ids: np.ndarray,
    top_negative_values: np.ndarray,
    countsketch: np.ndarray,
    vocab_size: int,
    expected_target_rows: Sequence[Mapping[str, Any]] | None = None,
    expected_block_indices: Sequence[int] | None = None,
    expected_depth_fractions: Sequence[float] | None = None,
    js_abs_tolerance: float | None = None,
) -> dict[str, Any]:
    """Validate the exact 8 x 32 zero grid under amendment v1.

    KL, TV, logit RMS, entropy identity, argmax identity, top-delta values,
    and CountSketch remain exact.  Only JS is admitted as a finite signed
    roundtrip residual within the frozen float32 bound.  Top IDs are undefined
    under all-zero deltas, so only their integer dtype and vocabulary range are
    checked.
    """

    tolerance = _js_tolerance(js_abs_tolerance)
    count = len(rows)
    _require(count == EXPECTED_ZERO_ROWS, "Zero ledger must contain 256 rows")
    _require(type(vocab_size) is int and vocab_size > 0, "Invalid vocabulary size")
    arrays = (
        top_positive_ids,
        top_positive_values,
        top_negative_ids,
        top_negative_values,
        countsketch,
    )
    _require(
        all(
            isinstance(array, np.ndarray) and array.shape[0] == count
            for array in arrays
        ),
        "Zero-control array row count changed",
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

    target_ids: list[str] | None = None
    target_groups: list[str] | None = None
    if expected_target_rows is not None:
        target_ids, target_groups = _expected_target_identity(expected_target_rows)
    if expected_block_indices is not None:
        _require(
            len(expected_block_indices) == EXPECTED_SITE_COUNT
            and all(
                type(value) is int and value >= 0 for value in expected_block_indices
            ),
            "Expected block-index grid changed",
        )
    if expected_depth_fractions is not None:
        _require(
            len(expected_depth_fractions) == EXPECTED_SITE_COUNT
            and all(
                type(value) in {int, float}
                and not isinstance(value, bool)
                and math.isfinite(float(value))
                for value in expected_depth_fractions
            ),
            "Expected depth-fraction grid changed",
        )

    required_fields = {
        "condition_kind",
        "site_index",
        "block_index",
        "depth_fraction",
        "magnitude",
        "sign",
        "target_index",
        "target_id",
        "target_group",
        "response_index",
        "kl_baseline_to_intervened",
        "js_divergence",
        "total_variation",
        "baseline_entropy",
        "intervened_entropy",
        "logit_delta_rms",
        "baseline_argmax_id",
        "intervened_argmax_id",
        "argmax_flip",
    }
    js_values: list[float] = []
    observed_pairs: set[tuple[int, int]] = set()
    inferred_targets: dict[int, tuple[str, str]] = {}
    inferred_sites: dict[int, tuple[int, float]] = {}
    for response_index, row in enumerate(rows):
        _require(set(row) == required_fields, "Zero ledger fields changed")
        _require(
            _integer(row["response_index"], "response_index") == response_index,
            "Zero response index changed",
        )
        site_index = _integer(row["site_index"], "site_index")
        target_index = _integer(row["target_index"], "target_index")
        _require(
            site_index == response_index // EXPECTED_TARGET_COUNT
            and target_index == response_index % EXPECTED_TARGET_COUNT,
            "Zero response order is not site-major target-minor",
        )
        _require(
            0 <= site_index < EXPECTED_SITE_COUNT
            and 0 <= target_index < EXPECTED_TARGET_COUNT,
            "Zero grid index outside registered range",
        )
        pair = (site_index, target_index)
        _require(pair not in observed_pairs, "Duplicate zero site-target cell")
        observed_pairs.add(pair)
        _require(row.get("condition_kind") == "zero_direction", "Wrong zero kind")
        _require(_number(row["magnitude"], "magnitude") == 0.0, "Bad zero magnitude")
        _require(_integer(row["sign"], "sign") == 0, "Bad zero sign")

        target_id = row.get("target_id")
        target_group = row.get("target_group")
        _require(
            isinstance(target_id, str) and target_id,
            "Zero target ID is missing",
        )
        _require(
            isinstance(target_group, str) and target_group,
            "Zero target group is missing",
        )
        target_identity = (target_id, target_group)
        _require(
            inferred_targets.setdefault(target_index, target_identity)
            == target_identity,
            "Zero target identity changed across depths",
        )
        if target_ids is not None and target_groups is not None:
            _require(
                target_id == target_ids[target_index]
                and target_group == target_groups[target_index],
                "Zero target identity differs from frozen preflight",
            )

        block_index = _integer(row["block_index"], "block_index")
        depth_fraction = _number(row["depth_fraction"], "depth_fraction")
        _require(block_index >= 0, "Zero block index is negative")
        site_identity = (block_index, depth_fraction)
        _require(
            inferred_sites.setdefault(site_index, site_identity) == site_identity,
            "Zero site metadata changed across targets",
        )
        if expected_block_indices is not None:
            _require(
                block_index == int(expected_block_indices[site_index]),
                "Zero block index differs from frozen baseline metadata",
            )
        if expected_depth_fractions is not None:
            _require(
                depth_fraction == float(expected_depth_fractions[site_index]),
                "Zero depth fraction differs from frozen baseline metadata",
            )

        for endpoint in (
            "kl_baseline_to_intervened",
            "total_variation",
            "logit_delta_rms",
        ):
            _require(
                _number(row[endpoint], endpoint) == 0.0,
                f"Primitive zero scalar is nonzero: {endpoint}",
            )
        js = _number(row["js_divergence"], "js_divergence")
        _require(abs(js) <= tolerance, "JS residual exceeds amended float32 bound")
        js_values.append(js)

        baseline_entropy = _number(row["baseline_entropy"], "baseline_entropy")
        intervened_entropy = _number(row["intervened_entropy"], "intervened_entropy")
        _require(
            baseline_entropy == intervened_entropy,
            "Primitive zero entropy changed",
        )
        baseline_argmax = _integer(row["baseline_argmax_id"], "baseline_argmax_id")
        intervened_argmax = _integer(
            row["intervened_argmax_id"], "intervened_argmax_id"
        )
        _require(
            baseline_argmax == intervened_argmax,
            "Primitive zero argmax changed",
        )
        _require(
            0 <= baseline_argmax < vocab_size,
            "Primitive zero argmax outside vocabulary",
        )
        _require(row["argmax_flip"] is False, "Primitive zero argmax flip changed")

    _require(
        observed_pairs
        == {
            (site_index, target_index)
            for site_index in range(EXPECTED_SITE_COUNT)
            for target_index in range(EXPECTED_TARGET_COUNT)
        },
        "Zero ledger is not the exact 8 x 32 Cartesian product",
    )
    residuals = np.asarray(js_values, dtype=np.float64)
    maximum_absolute = float(np.max(np.abs(residuals)))
    v0_predicate_would_fail = bool(np.not_equal(residuals, 0.0).any())
    return {
        "status": ZERO_GATE_STATUS,
        "rows": count,
        "grid": {
            "site_count": EXPECTED_SITE_COUNT,
            "target_count": EXPECTED_TARGET_COUNT,
            "unique_site_target_cells": len(observed_pairs),
            "order": "site_major_target_minor_response_index",
        },
        "primitive_exact_noop": {
            "kl_baseline_to_intervened": True,
            "total_variation": True,
            "logit_delta_rms": True,
            "entropy_identity": True,
            "argmax_identity_no_flip_and_in_range": True,
            "top_positive_and_negative_values": True,
            "countsketch": True,
        },
        "tied_top_ids_allowed_and_range_checked": True,
        "js_residual": {
            "minimum": float(np.min(residuals)),
            "maximum": float(np.max(residuals)),
            "maximum_absolute": maximum_absolute,
            "tolerance": tolerance,
            "two_sided": True,
            "all_finite": True,
            "exact_zero_rows": int(np.equal(residuals, 0.0).sum()),
            "nonzero_rows": int(np.not_equal(residuals, 0.0).sum()),
        },
        "historical_v0_exact_js_gate": (
            "failed_closed_on_js_divergence_per_frozen_failure_receipt"
        ),
        "v0_exact_js_predicate_on_current_rows": (
            "would_fail_nonzero_roundtrip_residual"
            if v0_predicate_would_fail
            else "would_pass_all_js_exact_zero"
        ),
        "no_claim_of_exact_js": True,
    }


class ValueOpenGateV1:
    """Enforce closeout -> zero values -> all later values without v0 relabeling."""

    def __init__(self) -> None:
        self.scientific_open_validated = False
        self.zero_gate_complete = False
        self.trace: list[str] = []

    def authorize_after_closeout_rehash(
        self, same_process_audit: Mapping[str, Any]
    ) -> None:
        _require(not self.scientific_open_validated, "Receipt already validated")
        _require(
            same_process_audit.get("status") == "scientific_open_closeout_audit_pass"
            and same_process_audit.get("scientific_values_parsed") is False,
            "Full same-process closeout rehash did not pass",
        )
        self.scientific_open_validated = True
        self.trace.extend(
            (
                "same_process_full_closeout_rehash_complete",
                "external_scientific_open_receipt_validated",
            )
        )

    def open_jsonl(
        self, path: Path, *, zero_control: bool = False
    ) -> list[dict[str, Any]]:
        _require(
            self.scientific_open_validated,
            "Scientific-open receipt not validated after full closeout rehash",
        )
        _require(
            zero_control or self.zero_gate_complete,
            "Nonzero ledger opened before the amended zero-control gate",
        )
        self.trace.append(f"{'zero' if zero_control else 'nonzero'}:jsonl:{path}")
        return V0._read_jsonl(path)

    def open_array(
        self, path: Path, *, zero_control: bool = False, mmap: bool = True
    ) -> np.ndarray:
        _require(
            self.scientific_open_validated,
            "Scientific-open receipt not validated after full closeout rehash",
        )
        _require(
            zero_control or self.zero_gate_complete,
            "Nonzero array opened before the amended zero-control gate",
        )
        self.trace.append(f"{'zero' if zero_control else 'nonzero'}:npy:{path}")
        return np.load(path, mmap_mode="r" if mmap else None, allow_pickle=False)

    def complete_zero_gate(self) -> None:
        _require(
            self.scientific_open_validated, "Scientific-open receipt not validated"
        )
        _require(not self.zero_gate_complete, "Amended zero gate already complete")
        self.zero_gate_complete = True
        self.trace.append(ZERO_RECEIPT_STATUS)


def load_zero_gate_expectations(
    run_root: Path,
    role: str,
    preflight_directory: Path,
) -> dict[str, Any]:
    """Load role expectations bound to frozen preflight and sealed metadata."""

    supplied_preflight = preflight_directory / f"{role}.json"
    committed_directory = (_root() / PREFLIGHT_DIRECTORY).resolve(strict=True)
    committed_preflight = committed_directory / f"{role}.json"
    aggregate = V0._read_json(committed_directory / "aggregate.json")
    expected_hash = str(aggregate.get("receipt_sha256", {}).get(role))
    _require(
        supplied_preflight.is_file()
        and committed_preflight.is_file()
        and V0._sha256(supplied_preflight)
        == V0._sha256(committed_preflight)
        == expected_hash,
        f"Zero-gate preflight is not the frozen receipt: {role}",
    )
    preflight = V0._read_json(supplied_preflight)
    target_rows = preflight.get("target_rows")
    _require(
        isinstance(target_rows, list) and len(target_rows) == EXPECTED_TARGET_COUNT,
        f"Frozen preflight targets changed: {role}",
    )
    baseline = V0._read_json(run_root / role / "baseline" / "metadata.json")
    expected_ids, expected_groups = _expected_target_identity(target_rows)
    _require(
        baseline.get("target_ids") == expected_ids
        and baseline.get("target_groups") == expected_groups,
        f"Baseline target identity differs from frozen preflight: {role}",
    )
    blocks = baseline.get("block_indices")
    depths = baseline.get("depth_fractions")
    _require(
        isinstance(blocks, list) and isinstance(depths, list),
        f"Baseline site metadata missing: {role}",
    )
    return {
        "target_rows": target_rows,
        "block_indices": blocks,
        "depth_fractions": depths,
    }


def _zero_gate_v1(
    run_root: Path,
    pilots: Sequence[str],
    gate: ValueOpenGateV1,
    preflight_directory: Path,
) -> list[dict[str, Any]]:
    model_config = V0._read_yaml(
        _root() / "configs" / "semantic_atlas_cross_model_replication_v0.yaml"
    )["models"]
    results: list[dict[str, Any]] = []
    for role in pilots:
        expectations = load_zero_gate_expectations(run_root, role, preflight_directory)
        directory = run_root / role / "pilot" / "zero" / "all-sites"
        rows = gate.open_jsonl(directory / "response_ledger.jsonl", zero_control=True)
        result = validate_zero_control_v1(
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
            vocab_size=int(model_config[role]["expected_vocab_size"]),
            expected_target_rows=expectations["target_rows"],
            expected_block_indices=expectations["block_indices"],
            expected_depth_fractions=expectations["depth_fractions"],
        )
        results.append({"model": role, **result})
    gate.complete_zero_gate()
    return results


def validate_zero_gate_receipt_v1(
    receipt: Mapping[str, Any],
    *,
    expected_run_binding_root_sha256: str | None = None,
    expected_scientific_open_receipt_sha256: str | None = None,
    expected_pilot_roles: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate the reusable amendment-v1 zero receipt."""

    _require(int(receipt.get("schema_version", -1)) == 1, "Zero receipt schema changed")
    _require(receipt.get("amendment_id") == AMENDMENT_ID, "Zero amendment changed")
    _require(
        receipt.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Zero receipt source analysis changed",
    )
    _require(
        receipt.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Zero receipt protocol changed",
    )
    _require(receipt.get("status") == ZERO_RECEIPT_STATUS, "Zero receipt incomplete")
    run_binding = receipt.get("run_binding_root_sha256")
    open_hash = receipt.get("scientific_open_receipt_sha256")
    _require(V0._is_sha256(run_binding), "Zero receipt run binding missing")
    _require(V0._is_sha256(open_hash), "Zero receipt open binding missing")
    _require(
        receipt.get("amendment_config_sha256")
        == V0._sha256(_root() / AMENDMENT_CONFIG_PATH),
        "Zero receipt amendment config binding changed",
    )
    _require(
        V0._is_sha256(receipt.get("amendment_freeze_manifest_sha256")),
        "Zero receipt amendment freeze binding missing",
    )
    if expected_run_binding_root_sha256 is not None:
        _require(run_binding == expected_run_binding_root_sha256, "Zero run changed")
    if expected_scientific_open_receipt_sha256 is not None:
        _require(
            open_hash == expected_scientific_open_receipt_sha256, "Zero open changed"
        )
    models = receipt.get("models")
    _require(isinstance(models, list) and models, "Zero model receipts missing")
    roles = [str(row.get("model")) for row in models]
    if expected_pilot_roles is not None:
        _require(roles == list(expected_pilot_roles), "Zero pilot order changed")
    _require(len(roles) == len(set(roles)), "Duplicate zero pilot role")
    current_would_fail_roles = []
    current_would_pass_roles = []
    for row in models:
        _require(
            row.get("status") == ZERO_GATE_STATUS, "Amended model gate did not pass"
        )
        _require(
            int(row.get("rows", 0)) == EXPECTED_ZERO_ROWS, "Zero model grid changed"
        )
        _require(row.get("no_claim_of_exact_js") is True, "Exact JS was claimed")
        residual = row.get("js_residual")
        _require(isinstance(residual, dict), "Zero model JS residual receipt missing")
        minimum = _number(residual.get("minimum"), "js_residual.minimum")
        maximum = _number(residual.get("maximum"), "js_residual.maximum")
        observed_bound = _number(
            residual.get("maximum_absolute"), "js_residual.maximum_absolute"
        )
        recorded_tolerance = _number(residual.get("tolerance"), "js_residual.tolerance")
        _require(
            observed_bound <= _js_tolerance()
            and recorded_tolerance == _js_tolerance()
            and minimum <= maximum
            and observed_bound == max(abs(minimum), abs(maximum))
            and residual.get("two_sided") is True
            and residual.get("all_finite") is True
            and int(residual.get("exact_zero_rows", -1))
            + int(residual.get("nonzero_rows", -1))
            == EXPECTED_ZERO_ROWS,
            "Zero model JS residual receipt exceeds the amendment",
        )
        _require(
            row.get("historical_v0_exact_js_gate")
            == "failed_closed_on_js_divergence_per_frozen_failure_receipt",
            "Historical v0 gate provenance changed",
        )
        current_predicate = row.get("v0_exact_js_predicate_on_current_rows")
        _require(
            current_predicate
            in {
                "would_fail_nonzero_roundtrip_residual",
                "would_pass_all_js_exact_zero",
            },
            "Current-row v0 predicate diagnostic changed",
        )
        destination = (
            current_would_fail_roles
            if current_predicate == "would_fail_nonzero_roundtrip_residual"
            else current_would_pass_roles
        )
        destination.append(str(row["model"]))
    original = receipt.get("original_v0_exact_js_gate")
    _require(
        isinstance(original, dict)
        and original.get("status") == "failed"
        and original.get("failure_field") == "js_divergence"
        and original.get("exact_failed_value_recorded") is False
        and original.get("failed_model_role_recorded") is False
        and original.get("authority") == "frozen_v0_failure_receipt",
        "Original v0 exact-JS failure is not recorded",
    )
    current = receipt.get("v0_exact_js_predicate_on_current_rows")
    _require(
        isinstance(current, dict)
        and current.get("would_fail_model_roles") == current_would_fail_roles
        and current.get("would_pass_model_roles") == current_would_pass_roles,
        "Current-row v0 predicate summary changed",
    )
    trace = receipt.get("zero_phase_value_open_trace")
    _require(isinstance(trace, list) and trace, "Amended zero trace missing")
    _require(
        trace[0] == "same_process_full_closeout_rehash_complete"
        and trace[-1] == ZERO_RECEIPT_STATUS
        and all("nonzero:" not in str(value) for value in trace),
        "Amended zero phase open order changed",
    )
    _require(
        receipt.get("scientific_values_opened_before_all_zero") is False,
        "Early scientific value read recorded",
    )
    _require(receipt.get("no_claim_of_exact_js") is True, "Receipt claims exact JS")
    return {
        "status": "zero_gate_amendment_v1_receipt_audit_pass",
        "run_binding_root_sha256": str(run_binding),
        "pilot_roles": roles,
        "v0_exact_js_predicate_on_current_rows": {
            "would_fail_model_roles": current_would_fail_roles,
            "would_pass_model_roles": current_would_pass_roles,
        },
    }


def execute_analysis(
    *,
    run_root: Path,
    scientific_open_receipt: Path,
    preflight_directory: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """Run unchanged v0 F4--F6 after the explicit amendment-v1 zero gate."""

    amendment_freeze_audit = _audit_amendment_freeze_same_process()
    amendment = _amendment_config()
    source_config = V0._config()
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
    roles = [
        str(value) for value in source_config["acquisition_gate"]["required_role_order"]
    ]
    pilots = [str(value) for value in source_config["acquisition_gate"]["pilot_roles"]]
    preflight_bindings = V0._validate_preflight_bindings(preflight_directory, roles)

    # This rehash is deliberately before gate construction and every value open.
    same_process_audit = V0._audit_closeout_same_process(run_root, receipt_path)
    receipt = V0._read_json(receipt_path)
    closeout = V0.validate_scientific_open_receipt(receipt, run_root)
    gate = ValueOpenGateV1()
    gate.authorize_after_closeout_rehash(same_process_audit)
    V0._assert_exact_tree(run_root, roles, set(pilots))
    zero = _zero_gate_v1(run_root, pilots, gate, preflight_directory)

    # No nonzero helper is called until every pilot zero grid passes above.
    baseline, response_rows = V0._f4_inputs(run_root, pilots, gate)
    f4 = V0.analyze_target_sensitivity(
        baseline, response_rows, expected_target_count=EXPECTED_TARGET_COUNT
    )
    del baseline, response_rows
    f5 = V0._f5(run_root, pilots, gate, f4["target_profiles"])
    f6 = V0._f6(run_root, roles, gate, preflight_directory)

    scientific_open_receipt_sha256 = V0._sha256(receipt_path)
    current_would_fail_roles = [
        str(row["model"])
        for row in zero
        if row["v0_exact_js_predicate_on_current_rows"]
        == "would_fail_nonzero_roundtrip_residual"
    ]
    current_would_pass_roles = [
        str(row["model"])
        for row in zero
        if row["v0_exact_js_predicate_on_current_rows"]
        == "would_pass_all_js_exact_zero"
    ]
    zero_receipt = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "source_analysis_id": SOURCE_ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": ZERO_RECEIPT_STATUS,
        "run_binding_root_sha256": closeout["external_closeout_root_sha256"],
        "scientific_open_receipt_sha256": scientific_open_receipt_sha256,
        "amendment_config_sha256": V0._sha256(_root() / AMENDMENT_CONFIG_PATH),
        "amendment_freeze_manifest_sha256": amendment_freeze_audit[
            "freeze_manifest_sha256"
        ],
        "models": zero,
        "original_v0_exact_js_gate": {
            "status": "failed",
            "failure_field": "js_divergence",
            "exact_failed_value_recorded": False,
            "failed_model_role_recorded": False,
            "authority": "frozen_v0_failure_receipt",
        },
        "v0_exact_js_predicate_on_current_rows": {
            "would_fail_model_roles": current_would_fail_roles,
            "would_pass_model_roles": current_would_pass_roles,
        },
        "zero_phase_value_open_trace": gate.trace[
            : gate.trace.index(ZERO_RECEIPT_STATUS) + 1
        ],
        "scientific_values_opened_before_all_zero": False,
        "no_claim_of_exact_js": True,
    }
    validate_zero_gate_receipt_v1(
        zero_receipt,
        expected_run_binding_root_sha256=closeout["external_closeout_root_sha256"],
        expected_scientific_open_receipt_sha256=scientific_open_receipt_sha256,
        expected_pilot_roles=pilots,
    )
    outputs = {
        "zero_hook_exact_primitives_bounded_js_v1.json": zero_receipt,
        "F4_target_sensitivity.json": f4,
        "F5_output_direction.json": f5,
        "F6_source_geometry.json": f6,
    }

    stage = (
        output_directory.parent / f".{output_directory.name}.stage-{uuid.uuid4().hex}"
    )
    _require(not stage.exists(), "Output stage collision")
    stage.mkdir(parents=True)
    try:
        bindings: dict[str, dict[str, Any]] = {}
        for name, value in outputs.items():
            path = stage / name
            V0._write_json(path, value)
            bindings[name] = {"bytes": path.stat().st_size, "sha256": V0._sha256(path)}
        analysis_receipt = {
            "schema_version": 1,
            "amendment_id": AMENDMENT_ID,
            "source_analysis_id": SOURCE_ANALYSIS_ID,
            "source_protocol_id": SOURCE_PROTOCOL_ID,
            "status": ANALYSIS_STATUS,
            "decision_status": "no_primary_no_significance_test_no_confirmatory_verdict",
            "amendment": {
                "status_at_freeze": amendment["status_at_freeze"],
                "config_path": str(AMENDMENT_CONFIG_PATH),
                "config_sha256": V0._sha256(_root() / AMENDMENT_CONFIG_PATH),
                "freeze_audit": amendment_freeze_audit,
                "scope": "zero_gate_numerical_parser_only_f4_f5_f6_unchanged",
            },
            "input_closeout": {
                **closeout,
                "same_process_audit": same_process_audit,
                "scientific_open_receipt_sha256": scientific_open_receipt_sha256,
                "scientific_open_receipt_path": str(receipt_path),
                "preflight_receipt_sha256": preflight_bindings,
                "input_binding_sha256": V0._canonical_sha256(
                    {
                        "closeout": closeout,
                        "preflight": preflight_bindings,
                        "amendment_config_sha256": V0._sha256(
                            _root() / AMENDMENT_CONFIG_PATH
                        ),
                    }
                ),
            },
            "value_open_order": gate.trace,
            "zero_hook_gate": ZERO_GATE_STATUS,
            "original_v0_exact_js_gate": zero_receipt["original_v0_exact_js_gate"],
            "no_claim_of_exact_js": True,
            "outputs": bindings,
            "raw_arrays_copied": False,
            "bootstrap_intervals_included": False,
            "claim_boundary": source_config["claim_boundary"],
        }
        V0._write_json(stage / "analysis_receipt.json", analysis_receipt)
        _require(
            not output_directory.exists(),
            f"Output appeared during analysis: {output_directory}",
        )
        _publish_directory_no_replace(stage, output_directory)
        return analysis_receipt
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


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
