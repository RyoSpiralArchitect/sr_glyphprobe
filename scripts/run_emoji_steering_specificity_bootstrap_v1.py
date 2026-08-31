#!/usr/bin/env python3
"""Prepare, execute, and merge the frozen T13-EA bootstrap v1.

The production path reuses the already authorized T13-EA response-ledger
loader.  It never opens activation arrays, logits, model artifacts, prompt
text, or protected target banks.  A one-time compact bundle retains only the
scalar target/item populations required by the 600 frozen high-level
estimands.  Chunks are deterministic functions of replicate IDs, so schedule
order and host assignment cannot change the resampling draws.

This is a post-outcome computational amendment.  Its intervals are
descriptive and exploratory; no command in this module emits a significance
test or confirmatory verdict.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import stat
from types import ModuleType
from typing import Any

import numpy as np
import yaml


EXECUTION_ID = "glyphprobe-emoji-steering-specificity-bootstrap-execution-v1"
SOURCE_ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
CONFIG_PATH = Path("configs/emoji_steering_specificity_bootstrap_execution_v1.yaml")
ROSTER_PATH = Path("configs/emoji_steering_specificity_bootstrap_estimands_v1.json")
FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_bootstrap_execution_v1.json"
)
AUDITOR_PATH = Path(
    "scripts/audit_emoji_steering_specificity_bootstrap_execution_v1.py"
)
OUTCOMES_V1_PATH = Path("scripts/analyze_emoji_steering_specificity_outcomes_v1.py")

PILOT_MODELS = (
    "qwen25_0p5b_base_bf16",
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
)
ENDPOINT_ORDER = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
CONTRAST_ORDER = (
    "glyph_minus_unicode_name",
    "glyph_minus_decomposed_form",
    "unicode_name_minus_decomposed_form",
)
CONTRAST_FORMS = {
    "glyph_minus_unicode_name": ("glyph", "unicode_name"),
    "glyph_minus_decomposed_form": ("glyph", "decomposed_form"),
    "unicode_name_minus_decomposed_form": (
        "unicode_name",
        "decomposed_form",
    ),
}
SIGN_ORDER = (-1, 1)
DEPTH_ORDER = (0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
MAGNITUDE_ORDER = (0.125, 0.25, 0.5)
SYSTEM_ORDER = (
    "atomic_anchor",
    "presentation",
    "modifier",
    "zwj",
    "regional_flag",
    "keycap",
)
SOURCE_FORM_ORDER = (
    "glyph",
    "unicode_name",
    "component_name",
    "codepoint_literal",
    "decomposed_form",
)
F2_ANTISYMMETRY_METRICS = (
    "normalized_antisymmetry_residual",
    "positive_plus_negative",
)
F3_METRICS = (
    "prototype_minus_random_median_mean",
    "prototype_random_percentile_mean",
)

REGISTERED_REPLICATES = 20_000
BOOTSTRAP_SEED = 2_026_082_913
CHUNK_SIZE = 200
CHUNK_COUNT = 100
SENTINEL_REPLICATE_IDS = (0, 9_999, 19_999)
POINT_REPLAY_TOLERANCE = 1.0e-12
EXPECTED_ESTIMANDS = 600
EXPECTED_FAMILY_COUNTS = {
    "F1_item_source_form": 108,
    "F2_prototype_depth_dose": 168,
    "F3_random_null_calibration": 324,
}

ARRAY_FILENAMES = {
    "f1_values": "f1_values.npy",
    "f2_raw_target": "f2_raw_target.npy",
    "f2_dose_target": "f2_dose_target.npy",
    "f2_antisymmetry_target": "f2_antisymmetry_target.npy",
    "f3_prototype_weighted": "f3_prototype_weighted.npy",
    "f3_midrank_indicator_weighted": "f3_midrank_indicator_weighted.npy",
    "f3_random_values": "f3_random_values.npy",
    "observed_values": "observed_values.npy",
}


class BootstrapExecutionError(RuntimeError):
    """Raised when a frozen bootstrap input or output fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapExecutionError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _regular_file(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise BootstrapExecutionError(f"Missing {label}: {path}") from error
    _require(stat.S_ISREG(metadata.st_mode), f"{label} is not a regular file: {path}")
    _require(not stat.S_ISLNK(metadata.st_mode), f"{label} is a symlink: {path}")


def _read_json(path: Path) -> dict[str, Any]:
    _regular_file(path, "JSON input")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BootstrapExecutionError(f"Cannot read JSON: {path}") from error
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    _regular_file(path, "YAML input")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected YAML object: {path}")
    return value


def _write_bytes_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise BootstrapExecutionError(
            f"Refusing to overwrite output: {path}"
        ) from error


def _write_json_new(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    _write_bytes_new(path, (payload + "\n").encode("utf-8"))


def _write_jsonl_new(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    payload = b"".join(_canonical_json(row) + b"\n" for row in rows)
    _write_bytes_new(path, payload)


def _write_npy_new(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            np.save(handle, value, allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise BootstrapExecutionError(
            f"Refusing to overwrite output: {path}"
        ) from error


def _binding(path: Path) -> dict[str, Any]:
    _regular_file(path, "bound file")
    return {"bytes": path.stat().st_size, "sha256": _sha256(path)}


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    _require(spec is not None and spec.loader is not None, f"Cannot load: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _config() -> dict[str, Any]:
    value = _read_yaml(_root() / CONFIG_PATH)
    _require(value.get("execution_id") == EXECUTION_ID, "Execution ID changed")
    _require(
        value.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Source analysis ID changed",
    )
    registered = value.get("registered_bootstrap", {})
    _require(
        registered.get("replicates") == REGISTERED_REPLICATES
        and registered.get("seed") == BOOTSTRAP_SEED,
        "Registered bootstrap changed",
    )
    schedule = value.get("chunk_schedule", {})
    _require(
        schedule.get("chunk_size") == CHUNK_SIZE
        and schedule.get("chunk_count") == CHUNK_COUNT
        and tuple(schedule.get("sentinel_replicate_ids", [])) == SENTINEL_REPLICATE_IDS,
        "Chunk schedule changed",
    )
    return value


def _audit_freeze() -> dict[str, Any]:
    module = _load_module(
        _root() / AUDITOR_PATH,
        "glyphprobe_t13ea_bootstrap_execution_v1_auditor",
    )
    result = module.audit_freeze()
    _require(
        isinstance(result, dict)
        and result.get("status") == "bootstrap_execution_freeze_audit_pass"
        and result.get("scientific_values_parsed_by_auditor") is False,
        "Bootstrap execution freeze audit failed",
    )
    return result


def _depth_label(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "p")


def _estimand_id(
    family: str,
    table: str,
    factors: Sequence[tuple[str, Any]],
    metric: str,
) -> str:
    parts = [family, table]
    parts.extend(f"{key}={value}" for key, value in factors)
    parts.append(f"metric={metric}")
    return "/".join(parts)


def generate_estimand_roster(
    models: Sequence[str] = PILOT_MODELS,
    depths: Sequence[float] = DEPTH_ORDER,
) -> list[dict[str, Any]]:
    """Generate the complete systematic high-level estimand roster."""

    rows: list[dict[str, Any]] = []

    def append(
        family: str,
        table: str,
        factors: Sequence[tuple[str, Any]],
        metric: str,
        point_source: str,
        definition: str,
    ) -> None:
        normalized = [
            (key, _depth_label(value) if key == "depth_fraction" else value)
            for key, value in factors
        ]
        rows.append(
            {
                "index": len(rows),
                "estimand_id": _estimand_id(family, table, normalized, metric),
                "family": family,
                "table": table,
                "factors": {key: value for key, value in factors},
                "metric": metric,
                "point_source": point_source,
                "definition": definition,
            }
        )

    for model in models:
        for contrast in CONTRAST_ORDER:
            for sign in SIGN_ORDER:
                for endpoint in ENDPOINT_ORDER:
                    append(
                        "F1_item_source_form",
                        "overall_model_sign",
                        (
                            ("model", model),
                            ("contrast", contrast),
                            ("sign", sign),
                            ("endpoint", endpoint),
                        ),
                        "paired_difference_mean",
                        "families.F1_item_source_form.overall_model_sign_rows.mean",
                        "Eligible item-by-target micro mean of the paired source-form difference.",
                    )

    for model in models:
        for endpoint in ENDPOINT_ORDER:
            for depth in depths:
                append(
                    "F2_prototype_depth_dose",
                    "raw_headline_by_model_endpoint_depth",
                    (
                        ("model", model),
                        ("endpoint", endpoint),
                        ("depth_fraction", float(depth)),
                    ),
                    "raw_headline_mean",
                    "families.F2_prototype_depth_dose.raw_headline_mean_by_model_endpoint_depth.mean",
                    "Equal-form, eligible-system macro, equal-magnitude and equal-sign response mean.",
                )
            append(
                "F2_prototype_depth_dose",
                "dose_ordering_by_model_endpoint",
                (("model", model), ("endpoint", endpoint)),
                "ordered_non_decreasing_weighted_mean",
                "families.F2_prototype_depth_dose.dose_ordering_by_model_endpoint.weighted_mean",
                "Target-weighted monotone-dose fraction over every registered condition cell.",
            )
        for metric in F2_ANTISYMMETRY_METRICS:
            append(
                "F2_prototype_depth_dose",
                "entropy_antisymmetry_by_model",
                (("model", model),),
                metric,
                f"families.F2_prototype_depth_dose.entropy_antisymmetry_by_model.{metric}.weighted_mean",
                "Target-weighted entropy sign-pair diagnostic over all registered prototype cells.",
            )

    for model in models:
        for endpoint in ENDPOINT_ORDER:
            for depth in depths:
                for metric in F3_METRICS:
                    append(
                        "F3_random_null_calibration",
                        "by_model_endpoint_depth",
                        (
                            ("model", model),
                            ("endpoint", endpoint),
                            ("depth_fraction", float(depth)),
                        ),
                        metric,
                        f"families.F3_random_null_calibration.by_model_endpoint_depth.{metric}",
                        "Equal-form, eligible-system macro random-relative target mean at fixed depth.",
                    )
            for metric in F3_METRICS:
                append(
                    "F3_random_null_calibration",
                    "by_model_endpoint",
                    (("model", model), ("endpoint", endpoint)),
                    metric,
                    f"families.F3_random_null_calibration.by_model_endpoint.{metric}",
                    "Equal-depth average of the registered random-relative target mean.",
                )

    return rows


def roster_document() -> dict[str, Any]:
    rows = generate_estimand_roster()
    counts = {
        family: sum(row["family"] == family for row in rows)
        for family in EXPECTED_FAMILY_COUNTS
    }
    _require(len(rows) == EXPECTED_ESTIMANDS, "Generated estimand count differs")
    _require(counts == EXPECTED_FAMILY_COUNTS, "Generated family counts differ")
    return {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "complete_post_outcome_high_level_estimand_roster",
        "scientific_outcomes_seen_before_roster_freeze": True,
        "selection_rule": (
            "complete systematic high-level reporting rows; no outcome-based "
            "model, family, cell, sign, depth, or endpoint filter"
        ),
        "estimand_count": len(rows),
        "family_counts": counts,
        "estimands": rows,
    }


def _load_roster(path: Path | None = None) -> dict[str, Any]:
    roster_path = _root() / ROSTER_PATH if path is None else path
    value = _read_json(roster_path)
    _require(value == roster_document(), "Estimand roster differs from generator")
    return value


def _index(values: Sequence[Any]) -> dict[Any, int]:
    _require(len(values) == len(set(values)), "Duplicate factor level")
    return {value: index for index, value in enumerate(values)}


def build_bundle_arrays(
    item_rows: Sequence[Mapping[str, Any]],
    prototype_rows: Sequence[Mapping[str, Any]],
    random_rows: Sequence[Mapping[str, Any]],
    *,
    endpoint_values: Callable[[Mapping[str, Any]], Mapping[str, float]],
    models: Sequence[str] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Build the compact target/item populations used by every replicate."""

    _require(bool(item_rows and prototype_rows and random_rows), "Empty source rows")
    model_order = tuple(models or sorted({str(row["model"]) for row in item_rows}))
    item_order = tuple(sorted({int(row["item_index"]) for row in item_rows}))
    target_order = tuple(sorted({int(row["target_index"]) for row in item_rows}))
    depth_order = tuple(
        sorted({float(row["depth_fraction"]) for row in prototype_rows})
    )
    magnitude_order = tuple(sorted({float(row["magnitude"]) for row in prototype_rows}))
    random_seed_order = tuple(sorted({int(row["seed_index"]) for row in random_rows}))
    observed_system_forms = {
        (str(row["glyph_system"]), str(row["view"])) for row in prototype_rows
    }
    system_form_order = tuple(
        sorted(
            observed_system_forms,
            key=lambda value: (
                SYSTEM_ORDER.index(value[0])
                if value[0] in SYSTEM_ORDER
                else len(SYSTEM_ORDER),
                SOURCE_FORM_ORDER.index(value[1])
                if value[1] in SOURCE_FORM_ORDER
                else len(SOURCE_FORM_ORDER),
                value,
            ),
        )
    )
    source_form_order = tuple(
        value
        for value in SOURCE_FORM_ORDER
        if any(sf == value for _, sf in system_form_order)
    )
    sign_order = tuple(sorted({int(row["sign"]) for row in prototype_rows}))
    endpoint_order = ENDPOINT_ORDER

    mi = _index(model_order)
    ii = _index(item_order)
    ti = _index(target_order)
    di = _index(depth_order)
    gi = _index(magnitude_order)
    si = _index(sign_order)
    ei = _index(endpoint_order)
    qi = _index(system_form_order)
    ri = _index(random_seed_order)

    item_lookup: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    item_forms: dict[int, set[str]] = defaultdict(set)
    for row in item_rows:
        key = (
            str(row["model"]),
            int(row["item_index"]),
            int(row["target_index"]),
            int(row["sign"]),
            str(row["view"]),
        )
        _require(key not in item_lookup, f"Duplicate item row: {key}")
        item_lookup[key] = row
        item_forms[int(row["item_index"])].add(str(row["view"]))

    f1 = np.zeros(
        (
            len(model_order),
            len(CONTRAST_ORDER),
            len(sign_order),
            len(endpoint_order),
            len(item_order),
            len(target_order),
        ),
        dtype=np.float64,
    )
    f1_item_positions: dict[str, list[int]] = {}
    for contrast_index, contrast in enumerate(CONTRAST_ORDER):
        left, right = CONTRAST_FORMS[contrast]
        eligible = [
            item for item in item_order if {left, right}.issubset(item_forms[item])
        ]
        _require(bool(eligible), f"No eligible F1 items: {contrast}")
        f1_item_positions[contrast] = [ii[item] for item in eligible]
        for model in model_order:
            for sign in sign_order:
                for item in eligible:
                    for target in target_order:
                        left_key = (model, item, target, sign, left)
                        right_key = (model, item, target, sign, right)
                        _require(
                            left_key in item_lookup and right_key in item_lookup,
                            f"Incomplete F1 pair: {left_key} / {right_key}",
                        )
                        left_values = endpoint_values(item_lookup[left_key])
                        right_values = endpoint_values(item_lookup[right_key])
                        for endpoint in endpoint_order:
                            f1[
                                mi[model],
                                contrast_index,
                                si[sign],
                                ei[endpoint],
                                ii[item],
                                ti[target],
                            ] = float(left_values[endpoint]) - float(
                                right_values[endpoint]
                            )

    prototype = np.full(
        (
            len(model_order),
            len(system_form_order),
            len(target_order),
            len(depth_order),
            len(magnitude_order),
            len(sign_order),
            len(endpoint_order),
        ),
        np.nan,
        dtype=np.float64,
    )
    for row in prototype_rows:
        position = (
            mi[str(row["model"])],
            qi[(str(row["glyph_system"]), str(row["view"]))],
            ti[int(row["target_index"])],
            di[float(row["depth_fraction"])],
            gi[float(row["magnitude"])],
            si[int(row["sign"])],
        )
        _require(
            np.isnan(prototype[position]).all(), f"Duplicate prototype row: {position}"
        )
        values = endpoint_values(row)
        prototype[position] = [float(values[name]) for name in endpoint_order]
    _require(bool(np.isfinite(prototype).all()), "Incomplete prototype tensor")

    random = np.full(
        (
            len(model_order),
            len(target_order),
            len(depth_order),
            len(magnitude_order),
            len(random_seed_order),
            len(endpoint_order),
        ),
        np.nan,
        dtype=np.float64,
    )
    for row in random_rows:
        position = (
            mi[str(row["model"])],
            ti[int(row["target_index"])],
            di[float(row["depth_fraction"])],
            gi[float(row["magnitude"])],
            ri[int(row["seed_index"])],
        )
        _require(np.isnan(random[position]).all(), f"Duplicate random row: {position}")
        values = endpoint_values(row)
        random[position] = [float(values[name]) for name in endpoint_order]
    _require(bool(np.isfinite(random).all()), "Incomplete random tensor")

    form_counts = {
        form: sum(source_form == form for _, source_form in system_form_order)
        for form in source_form_order
    }
    _require(all(value > 0 for value in form_counts.values()), "Empty source form")
    form_weights = np.asarray(
        [
            1.0 / (len(source_form_order) * form_counts[source_form])
            for _, source_form in system_form_order
        ],
        dtype=np.float64,
    )
    _require(abs(float(np.sum(form_weights)) - 1.0) < 1e-15, "Form weights differ")

    # M,Q,T,D,G,S,E -> M,T,D,G,S,E -> M,E,D,T
    form_macro = np.tensordot(prototype, form_weights, axes=([1], [0]))
    raw_target = np.mean(form_macro, axis=(3, 4)).transpose(0, 3, 2, 1)

    dose_values = prototype.copy()
    entropy_index = ei["entropy_change"]
    for sign_index, sign in enumerate(sign_order):
        dose_values[:, :, :, :, :, sign_index, entropy_index] *= sign
    monotone = np.all(np.diff(dose_values, axis=4) >= 0.0, axis=4).astype(np.float64)
    # M,Q,T,D,S,E -> M,E,T
    dose_target = np.mean(monotone, axis=(1, 3, 4)).transpose(0, 2, 1)

    positive = prototype[:, :, :, :, :, si[1], entropy_index]
    negative = prototype[:, :, :, :, :, si[-1], entropy_index]
    denominator = np.abs(positive) + np.abs(negative)
    normalized = np.divide(
        np.abs(positive + negative),
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0.0,
    )
    signed_sum = positive + negative
    # Each becomes M,T after equal Q,D,G aggregation.
    anti_target = np.stack(
        (
            np.mean(normalized, axis=(1, 3, 4)),
            np.mean(signed_sum, axis=(1, 3, 4)),
        ),
        axis=1,
    )

    positive_prototype = prototype[:, :, :, :, :, si[1], :]
    prototype_weighted = np.tensordot(
        positive_prototype, form_weights, axes=([1], [0])
    ).transpose(0, 2, 3, 4, 1)
    # random: M,T,D,G,R,E -> M,D,G,E,T,R
    random_ordered = random.transpose(0, 2, 3, 5, 1, 4)
    indicator_weighted = np.zeros_like(random, dtype=np.float64)
    for system_form_index, weight in enumerate(form_weights):
        candidate = positive_prototype[:, system_form_index, :, :, :, :]
        indicator_weighted += weight * (
            (random < candidate[..., None, :]).astype(np.float64)
            + 0.5 * (random == candidate[..., None, :]).astype(np.float64)
        )
    indicator_ordered = indicator_weighted.transpose(0, 2, 3, 5, 1, 4)

    arrays = {
        "f1_values": np.ascontiguousarray(f1, dtype=np.float64),
        "f2_raw_target": np.ascontiguousarray(raw_target, dtype=np.float64),
        "f2_dose_target": np.ascontiguousarray(dose_target, dtype=np.float64),
        "f2_antisymmetry_target": np.ascontiguousarray(anti_target, dtype=np.float64),
        "f3_prototype_weighted": np.ascontiguousarray(
            prototype_weighted, dtype=np.float64
        ),
        "f3_midrank_indicator_weighted": np.ascontiguousarray(
            indicator_ordered, dtype=np.float64
        ),
        "f3_random_values": np.ascontiguousarray(random_ordered, dtype=np.float64),
    }
    _require(
        all(bool(np.isfinite(value).all()) for value in arrays.values()),
        "Non-finite compact bundle value",
    )
    metadata = {
        "models": list(model_order),
        "items": list(item_order),
        "targets": list(target_order),
        "depths": list(depth_order),
        "magnitudes": list(magnitude_order),
        "random_seeds": list(random_seed_order),
        "signs": list(sign_order),
        "endpoints": list(endpoint_order),
        "system_forms": [
            {"glyph_system": system, "source_form": source_form}
            for system, source_form in system_form_order
        ],
        "source_forms": list(source_form_order),
        "f1_item_positions_by_contrast": f1_item_positions,
        "array_axis_contract": {
            "f1_values": ["model", "contrast", "sign", "endpoint", "item", "target"],
            "f2_raw_target": ["model", "endpoint", "depth", "target"],
            "f2_dose_target": ["model", "endpoint", "target"],
            "f2_antisymmetry_target": ["model", "metric", "target"],
            "f3_prototype_weighted": [
                "model",
                "depth",
                "magnitude",
                "endpoint",
                "target",
            ],
            "f3_midrank_indicator_weighted": [
                "model",
                "depth",
                "magnitude",
                "endpoint",
                "target",
                "random_seed",
            ],
            "f3_random_values": [
                "model",
                "depth",
                "magnitude",
                "endpoint",
                "target",
                "random_seed",
            ],
        },
    }
    return arrays, metadata


def _counter_sample_counts(
    *, seed: int, namespace: str, replicate_id: int, population_size: int
) -> np.ndarray:
    """Return unbiased counter-SHA256 resample counts across runtimes."""

    _require(population_size > 0, "Population size must be positive")
    _require(0 <= replicate_id < REGISTERED_REPLICATES, "Replicate ID out of range")
    counts = np.zeros(population_size, dtype=np.int64)
    modulus = 1 << 64
    cutoff = modulus - (modulus % population_size)
    for draw_index in range(population_size):
        attempt = 0
        while True:
            payload = _canonical_json(
                [int(seed), namespace, int(replicate_id), draw_index, attempt]
            )
            value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
            if value < cutoff:
                counts[value % population_size] += 1
                break
            attempt += 1
    _require(int(np.sum(counts)) == population_size, "Sampler draw count differs")
    return counts


def _resampled_median(values: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """Median along the final axis after applying integer multiplicities."""

    _require(values.ndim >= 1, "Median input has no axis")
    _require(values.shape[-1] == len(counts), "Median seed axis differs")
    total = int(np.sum(counts))
    _require(total > 0, "Median resample is empty")
    order = np.argsort(values, axis=-1, kind="stable")
    ordered_counts = np.take(counts, order)
    cumulative = np.cumsum(ordered_counts, axis=-1)
    if total % 2:
        index = np.argmax(cumulative > total // 2, axis=-1)
        return np.take_along_axis(
            values, np.take_along_axis(order, index[..., None], axis=-1), axis=-1
        )[..., 0]
    lower_rank = total // 2 - 1
    upper_rank = total // 2
    lower_index = np.argmax(cumulative > lower_rank, axis=-1)
    upper_index = np.argmax(cumulative > upper_rank, axis=-1)
    lower_order = np.take_along_axis(order, lower_index[..., None], axis=-1)
    upper_order = np.take_along_axis(order, upper_index[..., None], axis=-1)
    lower = np.take_along_axis(values, lower_order, axis=-1)[..., 0]
    upper = np.take_along_axis(values, upper_order, axis=-1)[..., 0]
    return (lower + upper) / 2.0


def _compute_values(
    arrays: Mapping[str, np.ndarray],
    metadata: Mapping[str, Any],
    *,
    target_counts: np.ndarray,
    item_counts_by_contrast: Mapping[str, np.ndarray],
    seed_counts_by_model_depth: Mapping[tuple[int, int], np.ndarray],
) -> np.ndarray:
    models = tuple(str(value) for value in metadata["models"])
    depths = tuple(float(value) for value in metadata["depths"])
    target_total = int(np.sum(target_counts))
    _require(target_total == len(metadata["targets"]), "Target draw count differs")

    f1_result = np.empty(
        (len(models), len(CONTRAST_ORDER), len(SIGN_ORDER), len(ENDPOINT_ORDER)),
        dtype=np.float64,
    )
    positions_by_contrast = metadata["f1_item_positions_by_contrast"]
    for model_index in range(len(models)):
        for contrast_index, contrast in enumerate(CONTRAST_ORDER):
            positions = np.asarray(positions_by_contrast[contrast], dtype=np.int64)
            item_counts = np.asarray(item_counts_by_contrast[contrast], dtype=np.int64)
            _require(len(item_counts) == len(positions), "F1 item-count axis differs")
            _require(int(np.sum(item_counts)) == len(positions), "F1 item draws differ")
            values = np.take(
                arrays["f1_values"][model_index, contrast_index],
                positions,
                axis=2,
            )
            f1_result[model_index, contrast_index] = np.einsum(
                "i,seit,t->se",
                item_counts,
                values,
                target_counts,
                optimize=False,
            ) / (len(positions) * target_total)

    f2_raw = (
        np.einsum("medt,t->med", arrays["f2_raw_target"], target_counts, optimize=False)
        / target_total
    )
    f2_dose = (
        np.einsum("met,t->me", arrays["f2_dose_target"], target_counts, optimize=False)
        / target_total
    )
    f2_anti = (
        np.einsum(
            "mkt,t->mk",
            arrays["f2_antisymmetry_target"],
            target_counts,
            optimize=False,
        )
        / target_total
    )

    f3_depth = np.empty(
        (len(models), len(ENDPOINT_ORDER), len(depths), len(F3_METRICS)),
        dtype=np.float64,
    )
    seed_total = len(metadata["random_seeds"])
    for model_index in range(len(models)):
        for depth_index in range(len(depths)):
            seed_counts = np.asarray(
                seed_counts_by_model_depth[(model_index, depth_index)],
                dtype=np.int64,
            )
            _require(
                len(seed_counts) == seed_total
                and int(np.sum(seed_counts)) == seed_total,
                "F3 seed resample differs",
            )
            random_values = arrays["f3_random_values"][model_index, depth_index]
            medians = _resampled_median(random_values, seed_counts)
            differences = (
                arrays["f3_prototype_weighted"][model_index, depth_index] - medians
            )
            percentiles = (
                np.einsum(
                    "getr,r->get",
                    arrays["f3_midrank_indicator_weighted"][model_index, depth_index],
                    seed_counts,
                    optimize=False,
                )
                / seed_total
            )
            difference_by_magnitude = (
                np.einsum("get,t->ge", differences, target_counts, optimize=False)
                / target_total
            )
            percentile_by_magnitude = (
                np.einsum("get,t->ge", percentiles, target_counts, optimize=False)
                / target_total
            )
            f3_depth[model_index, :, depth_index, 0] = np.mean(
                difference_by_magnitude, axis=0
            )
            f3_depth[model_index, :, depth_index, 1] = np.mean(
                percentile_by_magnitude, axis=0
            )
    f3_overall = np.mean(f3_depth, axis=2)

    values: list[float] = []
    for model_index in range(len(models)):
        for contrast_index in range(len(CONTRAST_ORDER)):
            for sign_index in range(len(SIGN_ORDER)):
                for endpoint_index in range(len(ENDPOINT_ORDER)):
                    values.append(
                        float(
                            f1_result[
                                model_index,
                                contrast_index,
                                sign_index,
                                endpoint_index,
                            ]
                        )
                    )
    for model_index in range(len(models)):
        for endpoint_index in range(len(ENDPOINT_ORDER)):
            for depth_index in range(len(depths)):
                values.append(float(f2_raw[model_index, endpoint_index, depth_index]))
            values.append(float(f2_dose[model_index, endpoint_index]))
        for metric_index in range(len(F2_ANTISYMMETRY_METRICS)):
            values.append(float(f2_anti[model_index, metric_index]))
    for model_index in range(len(models)):
        for endpoint_index in range(len(ENDPOINT_ORDER)):
            for depth_index in range(len(depths)):
                for metric_index in range(len(F3_METRICS)):
                    values.append(
                        float(
                            f3_depth[
                                model_index,
                                endpoint_index,
                                depth_index,
                                metric_index,
                            ]
                        )
                    )
            for metric_index in range(len(F3_METRICS)):
                values.append(
                    float(f3_overall[model_index, endpoint_index, metric_index])
                )
    result = np.asarray(values, dtype=np.float64)
    expected = len(generate_estimand_roster(models, depths))
    _require(len(result) == expected, "Computed estimand vector length differs")
    _require(bool(np.isfinite(result).all()), "Non-finite estimand value")
    return result


def observed_values(
    arrays: Mapping[str, np.ndarray], metadata: Mapping[str, Any]
) -> np.ndarray:
    target_counts = np.ones(len(metadata["targets"]), dtype=np.int64)
    item_counts = {
        contrast: np.ones(len(positions), dtype=np.int64)
        for contrast, positions in metadata["f1_item_positions_by_contrast"].items()
    }
    seed_counts = {
        (model_index, depth_index): np.ones(
            len(metadata["random_seeds"]), dtype=np.int64
        )
        for model_index in range(len(metadata["models"]))
        for depth_index in range(len(metadata["depths"]))
    }
    return _compute_values(
        arrays,
        metadata,
        target_counts=target_counts,
        item_counts_by_contrast=item_counts,
        seed_counts_by_model_depth=seed_counts,
    )


def compute_replicate_values(
    arrays: Mapping[str, np.ndarray],
    metadata: Mapping[str, Any],
    replicate_id: int,
    *,
    seed: int = BOOTSTRAP_SEED,
) -> np.ndarray:
    target_counts = _counter_sample_counts(
        seed=seed,
        namespace="target/all-families-all-models",
        replicate_id=replicate_id,
        population_size=len(metadata["targets"]),
    )
    item_counts: dict[str, np.ndarray] = {}
    for contrast, positions in metadata["f1_item_positions_by_contrast"].items():
        namespace = (
            "F1/items/all-192"
            if contrast == "glyph_minus_unicode_name"
            else "F1/items/decomposable-168"
        )
        item_counts[contrast] = _counter_sample_counts(
            seed=seed,
            namespace=namespace,
            replicate_id=replicate_id,
            population_size=len(positions),
        )
    seed_counts: dict[tuple[int, int], np.ndarray] = {}
    for model_index, model in enumerate(metadata["models"]):
        for depth_index, depth in enumerate(metadata["depths"]):
            seed_counts[(model_index, depth_index)] = _counter_sample_counts(
                seed=seed,
                namespace=f"F3/random-seeds/{model}/{_depth_label(float(depth))}",
                replicate_id=replicate_id,
                population_size=len(metadata["random_seeds"]),
            )
    return _compute_values(
        arrays,
        metadata,
        target_counts=target_counts,
        item_counts_by_contrast=item_counts,
        seed_counts_by_model_depth=seed_counts,
    )


def _expected_point_values(summary: Mapping[str, Any]) -> np.ndarray:
    families = summary.get("families")
    _require(isinstance(families, dict), "Point summary families missing")
    roster = generate_estimand_roster()

    def row_lookup(rows: Any, fields: Sequence[str]) -> dict[tuple[Any, ...], Any]:
        _require(isinstance(rows, list), "Point summary table is not a list")
        result: dict[tuple[Any, ...], Any] = {}
        for row in rows:
            _require(isinstance(row, dict), "Point summary row is not an object")
            key = tuple(row[field] for field in fields)
            _require(key not in result, f"Duplicate point summary row: {key}")
            result[key] = row
        return result

    f1 = families["F1_item_source_form"]
    f2 = families["F2_prototype_depth_dose"]
    f3 = families["F3_random_null_calibration"]
    f1_rows = row_lookup(
        f1["overall_model_sign_rows"], ("model", "contrast", "sign", "endpoint")
    )
    f2_raw = row_lookup(
        f2["raw_headline_mean_by_model_endpoint_depth"],
        ("model", "endpoint", "depth_fraction"),
    )
    f2_dose = row_lookup(f2["dose_ordering_by_model_endpoint"], ("model", "endpoint"))
    f2_anti = row_lookup(f2["entropy_antisymmetry_by_model"], ("model",))
    f3_depth = row_lookup(
        f3["by_model_endpoint_depth"], ("model", "endpoint", "depth_fraction")
    )
    f3_overall = row_lookup(f3["by_model_endpoint"], ("model", "endpoint"))

    values: list[float] = []
    for row in roster:
        factors = row["factors"]
        table = row["table"]
        metric = row["metric"]
        if table == "overall_model_sign":
            source = f1_rows[
                (
                    factors["model"],
                    factors["contrast"],
                    factors["sign"],
                    factors["endpoint"],
                )
            ]
            value = source["mean"]
        elif table == "raw_headline_by_model_endpoint_depth":
            source = f2_raw[
                (factors["model"], factors["endpoint"], factors["depth_fraction"])
            ]
            value = source["mean"]
        elif table == "dose_ordering_by_model_endpoint":
            source = f2_dose[(factors["model"], factors["endpoint"])]
            value = source["weighted_mean"]
        elif table == "entropy_antisymmetry_by_model":
            source = f2_anti[(factors["model"],)]
            value = source[metric]["weighted_mean"]
        elif table == "by_model_endpoint_depth":
            source = f3_depth[
                (factors["model"], factors["endpoint"], factors["depth_fraction"])
            ]
            value = source[metric]
        else:
            _require(table == "by_model_endpoint", f"Unknown roster table: {table}")
            source = f3_overall[(factors["model"], factors["endpoint"])]
            value = source[metric]
        number = float(value)
        _require(math.isfinite(number), f"Non-finite point value: {row['estimand_id']}")
        values.append(number)
    return np.asarray(values, dtype=np.float64)


def _validate_production_metadata(metadata: Mapping[str, Any]) -> None:
    _require(
        tuple(metadata["models"]) == PILOT_MODELS, "Production model order differs"
    )
    _require(
        tuple(metadata["targets"]) == tuple(range(32)), "Production target grid differs"
    )
    _require(tuple(metadata["depths"]) == DEPTH_ORDER, "Production depth grid differs")
    _require(
        tuple(metadata["magnitudes"]) == MAGNITUDE_ORDER, "Production dose grid differs"
    )
    _require(
        tuple(metadata["random_seeds"]) == tuple(range(64)), "Random seed grid differs"
    )
    _require(tuple(metadata["signs"]) == SIGN_ORDER, "Production sign grid differs")
    _require(tuple(metadata["endpoints"]) == ENDPOINT_ORDER, "Endpoint grid differs")
    _require(len(metadata["items"]) == 192, "F1 item population differs")
    _require(len(metadata["system_forms"]) == 28, "Prototype system-form grid differs")
    counts = {
        contrast: len(positions)
        for contrast, positions in metadata["f1_item_positions_by_contrast"].items()
    }
    _require(
        counts
        == {
            "glyph_minus_unicode_name": 192,
            "glyph_minus_decomposed_form": 168,
            "unicode_name_minus_decomposed_form": 168,
        },
        "F1 contrast populations differ",
    )


def prepare_bundle(
    *,
    run_root: Path,
    scientific_open_receipt: Path,
    preflight_directory: Path,
    output: Path,
) -> dict[str, Any]:
    audit = _audit_freeze()
    config = _config()
    _load_roster()
    destination = output.expanduser().resolve()
    _require(not destination.exists(), f"Refusing to overwrite bundle: {destination}")
    _require(
        not destination.is_relative_to(_root()),
        "Production bundle must remain outside the Git worktree",
    )

    module = _load_module(
        _root() / OUTCOMES_V1_PATH,
        "glyphprobe_t13ea_outcomes_v1_for_bootstrap_execution",
    )
    item_rows, prototype_rows, random_rows, authorization = module.load_authorized_rows(
        run_root, scientific_open_receipt, preflight_directory
    )
    module.V0._require_frozen_grid_counts(item_rows, prototype_rows, random_rows)
    arrays, metadata = build_bundle_arrays(
        item_rows,
        prototype_rows,
        random_rows,
        endpoint_values=module.V0.endpoint_values,
        models=PILOT_MODELS,
    )
    _validate_production_metadata(metadata)
    observed = observed_values(arrays, metadata)
    _require(len(observed) == EXPECTED_ESTIMANDS, "Observed roster length differs")

    summary_binding = config["source_bindings"]["point_reporting_summary"]
    summary_path = _root() / summary_binding["path"]
    _require(
        _binding(summary_path)
        == {"bytes": summary_binding["bytes"], "sha256": summary_binding["sha256"]},
        "Point summary binding changed",
    )
    expected = _expected_point_values(_read_json(summary_path))
    absolute = np.abs(observed - expected)
    _require(
        bool((absolute <= POINT_REPLAY_TOLERANCE).all()),
        (
            "Compact bundle does not replay the public point summary; "
            f"maximum absolute difference={float(np.max(absolute)):.17g}"
        ),
    )
    arrays = {**arrays, "observed_values": observed}

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    array_bindings: dict[str, Any] = {}
    for name, filename in ARRAY_FILENAMES.items():
        path = destination / filename
        _write_npy_new(path, np.asarray(arrays[name], dtype="<f8"))
        array_bindings[filename] = {
            **_binding(path),
            "dtype": str(np.load(path, mmap_mode="r", allow_pickle=False).dtype),
            "shape": list(np.load(path, mmap_mode="r", allow_pickle=False).shape),
        }

    freeze_path = _root() / FREEZE_PATH
    roster_path = _root() / ROSTER_PATH
    manifest = {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "bootstrap_population_bundle_complete",
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": _sha256(freeze_path),
        "execution_config_sha256": _sha256(_root() / CONFIG_PATH),
        "estimand_roster_sha256": _sha256(roster_path),
        "estimand_count": EXPECTED_ESTIMANDS,
        "point_replay": {
            "status": "all_600_observed_values_match_bound_public_summary",
            "absolute_tolerance": POINT_REPLAY_TOLERANCE,
            "maximum_absolute_difference": float(np.max(absolute)),
            "point_reporting_summary_sha256": summary_binding["sha256"],
        },
        "source_authorization": {
            "amendment_id": authorization["amendment_id"],
            "scientific_open_receipt_sha256": authorization["closeout_sha256"],
            "run_binding_root_sha256": authorization["same_process_closeout_audit"][
                "run_binding_root_sha256"
            ],
            "zero_hook_status": authorization["zero_hook_gate"]["status"],
        },
        "metadata": metadata,
        "arrays": array_bindings,
        "forbidden_contents_absent": [
            "raw_activation_arrays",
            "raw_logit_arrays",
            "model_weights_or_caches",
            "prompt_or_target_text",
            "protected_target_banks",
        ],
        "same_process_freeze_audit": audit,
    }
    _write_json_new(destination / "bundle_manifest.json", manifest)
    return {
        "status": manifest["status"],
        "bundle": str(destination),
        "bundle_manifest_sha256": _sha256(destination / "bundle_manifest.json"),
        "estimand_count": EXPECTED_ESTIMANDS,
        "maximum_point_replay_difference": float(np.max(absolute)),
    }


def load_bundle(path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any], str]:
    root = path.expanduser().resolve(strict=True)
    manifest_path = root / "bundle_manifest.json"
    manifest = _read_json(manifest_path)
    _require(
        manifest.get("execution_id") == EXECUTION_ID, "Bundle execution ID differs"
    )
    _require(
        manifest.get("status") == "bootstrap_population_bundle_complete",
        "Bundle is incomplete",
    )
    _require(
        manifest.get("execution_config_sha256") == _sha256(_root() / CONFIG_PATH)
        and manifest.get("estimand_roster_sha256") == _sha256(_root() / ROSTER_PATH)
        and manifest.get("freeze_manifest_sha256") == _sha256(_root() / FREEZE_PATH),
        "Bundle freeze binding differs",
    )
    bindings = manifest.get("arrays")
    _require(isinstance(bindings, dict), "Bundle array bindings missing")
    _require(
        set(bindings) == set(ARRAY_FILENAMES.values()), "Bundle array roster differs"
    )
    arrays: dict[str, np.ndarray] = {}
    for name, filename in ARRAY_FILENAMES.items():
        source = root / filename
        binding = bindings[filename]
        _require(
            _binding(source)
            == {"bytes": int(binding["bytes"]), "sha256": str(binding["sha256"])},
            f"Bundle array binding differs: {filename}",
        )
        value = np.load(source, mmap_mode="r", allow_pickle=False)
        _require(
            str(value.dtype) == binding["dtype"], f"Bundle dtype differs: {filename}"
        )
        _require(
            list(value.shape) == binding["shape"], f"Bundle shape differs: {filename}"
        )
        _require(bool(np.isfinite(value).all()), f"Non-finite bundle array: {filename}")
        arrays[name] = value
    metadata = manifest.get("metadata")
    _require(isinstance(metadata, dict), "Bundle metadata missing")
    _validate_production_metadata(metadata)
    _require(
        len(arrays["observed_values"]) == EXPECTED_ESTIMANDS, "Observed vector differs"
    )
    return arrays, metadata, _sha256(manifest_path)


def _runtime_fingerprint() -> dict[str, Any]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "machine": platform.machine(),
        "system": platform.system(),
        "byteorder": "little" if np.little_endian else "big",
        "float64_iec559": bool(np.finfo(np.float64).bits == 64),
    }


def _vector_block_sha256(replicate_ids: Sequence[int], values: np.ndarray) -> str:
    ids = np.asarray(replicate_ids, dtype=">i8")
    data = np.asarray(values, dtype=">f8")
    return _sha256_bytes(ids.tobytes(order="C") + data.tobytes(order="C"))


def compute_chunk_matrix(
    arrays: Mapping[str, np.ndarray],
    metadata: Mapping[str, Any],
    replicate_ids: Sequence[int],
) -> np.ndarray:
    estimand_count = len(
        generate_estimand_roster(metadata["models"], metadata["depths"])
    )
    values = np.empty((len(replicate_ids), estimand_count), dtype=np.float64)
    for offset, replicate_id in enumerate(replicate_ids):
        values[offset] = compute_replicate_values(arrays, metadata, int(replicate_id))
    _require(bool(np.isfinite(values).all()), "Non-finite chunk value")
    return values


def run_chunk(*, bundle: Path, output_root: Path, chunk_id: int) -> dict[str, Any]:
    _audit_freeze()
    _load_roster()
    _require(0 <= chunk_id < CHUNK_COUNT, "Chunk ID out of range")
    arrays, metadata, bundle_manifest_sha256 = load_bundle(bundle)
    start = chunk_id * CHUNK_SIZE
    stop = start + CHUNK_SIZE
    replicate_ids = np.arange(start, stop, dtype=np.int64)
    values = compute_chunk_matrix(arrays, metadata, replicate_ids.tolist())
    sentinel_values = compute_chunk_matrix(
        arrays, metadata, list(SENTINEL_REPLICATE_IDS)
    )
    sentinel_sha256 = _vector_block_sha256(SENTINEL_REPLICATE_IDS, sentinel_values)

    root = output_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"chunk-{chunk_id:04d}"
    _require(not destination.exists(), f"Refusing to overwrite chunk: {destination}")
    destination.mkdir()
    ids_path = destination / "replicate_ids.npy"
    values_path = destination / "estimand_values.npy"
    _write_npy_new(ids_path, replicate_ids.astype("<i8"))
    _write_npy_new(values_path, values.astype("<f8"))
    receipt = {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "bootstrap_chunk_complete",
        "chunk_id": chunk_id,
        "chunk_name": f"chunk-{chunk_id:04d}",
        "replicate_start_inclusive": start,
        "replicate_stop_exclusive": stop,
        "replicate_count": CHUNK_SIZE,
        "estimand_count": EXPECTED_ESTIMANDS,
        "bundle_manifest_sha256": bundle_manifest_sha256,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "execution_config_sha256": _sha256(_root() / CONFIG_PATH),
        "estimand_roster_sha256": _sha256(_root() / ROSTER_PATH),
        "sentinel_replicate_ids": list(SENTINEL_REPLICATE_IDS),
        "sentinel_values_sha256": sentinel_sha256,
        "payload_values_sha256": _vector_block_sha256(replicate_ids, values),
        "files": {
            "replicate_ids.npy": _binding(ids_path),
            "estimand_values.npy": _binding(values_path),
        },
        "runtime_fingerprint": _runtime_fingerprint(),
        "claim_boundary": "pointwise_descriptive_exploratory_intervals_only",
    }
    _write_json_new(destination / "receipt.json", receipt)
    return {
        "status": receipt["status"],
        "chunk_id": chunk_id,
        "replicate_range": [start, stop],
        "sentinel_values_sha256": sentinel_sha256,
        "receipt_sha256": _sha256(destination / "receipt.json"),
    }


def _validate_chunk(
    path: Path,
    *,
    expected_chunk_id: int,
    bundle_manifest_sha256: str,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any], str]:
    receipt_path = path / "receipt.json"
    receipt = _read_json(receipt_path)
    start = expected_chunk_id * CHUNK_SIZE
    stop = start + CHUNK_SIZE
    _require(receipt.get("execution_id") == EXECUTION_ID, "Chunk execution ID differs")
    _require(receipt.get("status") == "bootstrap_chunk_complete", "Chunk incomplete")
    _require(receipt.get("chunk_id") == expected_chunk_id, "Chunk ID differs")
    _require(
        receipt.get("chunk_name") == f"chunk-{expected_chunk_id:04d}",
        "Chunk name differs",
    )
    _require(
        receipt.get("replicate_start_inclusive") == start
        and receipt.get("replicate_stop_exclusive") == stop
        and receipt.get("replicate_count") == CHUNK_SIZE,
        "Chunk replicate range differs",
    )
    _require(
        receipt.get("estimand_count") == EXPECTED_ESTIMANDS, "Chunk roster differs"
    )
    _require(
        receipt.get("bundle_manifest_sha256") == bundle_manifest_sha256,
        "Chunk bundle binding differs",
    )
    _require(
        receipt.get("freeze_manifest_sha256") == _sha256(_root() / FREEZE_PATH)
        and receipt.get("execution_config_sha256") == _sha256(_root() / CONFIG_PATH)
        and receipt.get("estimand_roster_sha256") == _sha256(_root() / ROSTER_PATH),
        "Chunk freeze binding differs",
    )
    files = receipt.get("files")
    _require(isinstance(files, dict), "Chunk file bindings missing")
    ids_path = path / "replicate_ids.npy"
    values_path = path / "estimand_values.npy"
    for filename, source in (
        ("replicate_ids.npy", ids_path),
        ("estimand_values.npy", values_path),
    ):
        binding = files.get(filename)
        _require(isinstance(binding, dict), f"Chunk binding missing: {filename}")
        _require(
            _binding(source)
            == {"bytes": int(binding["bytes"]), "sha256": str(binding["sha256"])},
            f"Chunk payload changed: {filename}",
        )
    ids = np.load(ids_path, allow_pickle=False)
    values = np.load(values_path, allow_pickle=False)
    expected_ids = np.arange(start, stop, dtype=np.int64)
    _require(np.array_equal(ids, expected_ids), "Chunk replicate IDs differ")
    _require(
        values.shape == (CHUNK_SIZE, EXPECTED_ESTIMANDS), "Chunk value shape differs"
    )
    _require(bool(np.isfinite(values).all()), "Chunk contains non-finite values")
    _require(
        receipt.get("payload_values_sha256") == _vector_block_sha256(ids, values),
        "Chunk semantic payload hash differs",
    )
    _require(
        tuple(receipt.get("sentinel_replicate_ids", [])) == SENTINEL_REPLICATE_IDS,
        "Chunk sentinel roster differs",
    )
    return ids, values, receipt, _sha256(receipt_path)


def _linear_quantile(values: np.ndarray, q: float) -> np.ndarray:
    _require(values.ndim == 2 and len(values) > 0, "Quantile matrix differs")
    ordered = np.sort(values, axis=0, kind="stable")
    h = (len(values) - 1) * q
    lower = int(math.floor(h))
    upper = int(math.ceil(h))
    fraction = h - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def merge_chunks(*, bundle: Path, chunks_root: Path, output: Path) -> dict[str, Any]:
    _audit_freeze()
    roster = _load_roster()
    arrays, _metadata, bundle_manifest_sha256 = load_bundle(bundle)
    source = chunks_root.expanduser().resolve(strict=True)
    entries = sorted(path.name for path in source.iterdir())
    expected_entries = [f"chunk-{index:04d}" for index in range(CHUNK_COUNT)]
    _require(
        entries == expected_entries,
        "Chunk directory roster is incomplete or has extras",
    )

    all_values = np.empty((REGISTERED_REPLICATES, EXPECTED_ESTIMANDS), dtype=np.float64)
    chunk_receipts: list[dict[str, Any]] = []
    sentinel_hashes: set[str] = set()
    runtimes: list[dict[str, Any]] = []
    for chunk_id, name in enumerate(expected_entries):
        ids, values, receipt, receipt_sha256 = _validate_chunk(
            source / name,
            expected_chunk_id=chunk_id,
            bundle_manifest_sha256=bundle_manifest_sha256,
        )
        all_values[ids] = values
        sentinel_hash = str(receipt["sentinel_values_sha256"])
        sentinel_hashes.add(sentinel_hash)
        runtimes.append(receipt["runtime_fingerprint"])
        chunk_receipts.append(
            {
                "chunk_id": chunk_id,
                "receipt_sha256": receipt_sha256,
                "payload_values_sha256": receipt["payload_values_sha256"],
            }
        )
    _require(len(sentinel_hashes) == 1, "Chunk runtime sentinel hashes differ")
    _require(
        bool(np.isfinite(all_values).all()), "Merged replicate matrix is incomplete"
    )

    low = _linear_quantile(all_values, 0.025)
    high = _linear_quantile(all_values, 0.975)
    observed = np.asarray(arrays["observed_values"], dtype=np.float64)
    estimands = roster["estimands"]
    interval_rows = [
        {
            "index": index,
            "estimand_id": estimand["estimand_id"],
            "family": estimand["family"],
            "table": estimand["table"],
            "factors": estimand["factors"],
            "metric": estimand["metric"],
            "observed": float(observed[index]),
            "ci95_low": float(low[index]),
            "ci95_high": float(high[index]),
            "bootstrap_replicates": REGISTERED_REPLICATES,
            "interval": "two_sided_pointwise_percentile_95",
            "quantile_method": "linear_h_equals_n_minus_1_times_q",
            "decision_status": "descriptive_exploratory_no_significance_test",
        }
        for index, estimand in enumerate(estimands)
    ]

    destination = output.expanduser().resolve()
    _require(not destination.exists(), f"Refusing to overwrite merge: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()
    intervals_path = destination / "intervals.jsonl"
    _write_jsonl_new(intervals_path, interval_rows)
    unique_runtimes = []
    seen_runtime_payloads: set[bytes] = set()
    for runtime in runtimes:
        payload = _canonical_json(runtime)
        if payload not in seen_runtime_payloads:
            seen_runtime_payloads.add(payload)
            unique_runtimes.append(runtime)
    receipt = {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "status": "registered_bootstrap_complete_and_hash_merged",
        "claim_boundary": (
            "post-outcome pointwise descriptive exploratory intervals; no "
            "primary, significance, confirmatory, semantic, or mechanistic claim"
        ),
        "bundle_manifest_sha256": bundle_manifest_sha256,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "execution_config_sha256": _sha256(_root() / CONFIG_PATH),
        "estimand_roster_sha256": _sha256(_root() / ROSTER_PATH),
        "registered_replicates": REGISTERED_REPLICATES,
        "completed_replicates": REGISTERED_REPLICATES,
        "chunk_count": CHUNK_COUNT,
        "estimand_count": EXPECTED_ESTIMANDS,
        "coverage": {
            "first_replicate_id": 0,
            "last_replicate_id": REGISTERED_REPLICATES - 1,
            "missing": 0,
            "duplicate": 0,
            "extra": 0,
        },
        "sentinel_values_sha256": sentinel_hashes.pop(),
        "runtime_fingerprints": unique_runtimes,
        "chunks": chunk_receipts,
        "intervals": {"intervals.jsonl": _binding(intervals_path)},
        "bootstrap_execution_gate_satisfied": True,
        "paper_interval_gate_satisfied": True,
        "confirmatory_gate_satisfied": False,
        "exact_roster_was_prospective": False,
    }
    _write_json_new(destination / "merge_receipt.json", receipt)
    return {
        "status": receipt["status"],
        "output": str(destination),
        "completed_replicates": REGISTERED_REPLICATES,
        "estimand_count": EXPECTED_ESTIMANDS,
        "sentinel_values_sha256": receipt["sentinel_values_sha256"],
        "merge_receipt_sha256": _sha256(destination / "merge_receipt.json"),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    roster = subparsers.add_parser("write-roster")
    roster.add_argument("--output", type=Path, default=ROSTER_PATH)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--run-root", type=Path, required=True)
    prepare.add_argument("--scientific-open-receipt", type=Path, required=True)
    prepare.add_argument(
        "--preflight-directory",
        type=Path,
        default=Path("validation/emoji_steering_specificity_harvest_v0"),
    )
    prepare.add_argument("--output", type=Path, required=True)

    chunk = subparsers.add_parser("run-chunk")
    chunk.add_argument("--bundle", type=Path, required=True)
    chunk.add_argument("--output-root", type=Path, required=True)
    chunk.add_argument("--chunk-id", type=int, required=True)

    merge = subparsers.add_parser("merge")
    merge.add_argument("--bundle", type=Path, required=True)
    merge.add_argument("--chunks-root", type=Path, required=True)
    merge.add_argument("--output", type=Path, required=True)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.command == "write-roster":
        output = args.output if args.output.is_absolute() else _root() / args.output
        _write_json_new(output, roster_document())
        value = {
            "status": "estimand_roster_written",
            "output": str(output),
            "estimand_count": EXPECTED_ESTIMANDS,
            "sha256": _sha256(output),
        }
    elif args.command == "prepare":
        value = prepare_bundle(
            run_root=args.run_root,
            scientific_open_receipt=args.scientific_open_receipt,
            preflight_directory=args.preflight_directory,
            output=args.output,
        )
    elif args.command == "run-chunk":
        value = run_chunk(
            bundle=args.bundle,
            output_root=args.output_root,
            chunk_id=args.chunk_id,
        )
    else:
        value = merge_chunks(
            bundle=args.bundle,
            chunks_root=args.chunks_root,
            output=args.output,
        )
    value["reported_at_utc"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
