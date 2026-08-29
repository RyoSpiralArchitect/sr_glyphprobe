#!/usr/bin/env python3
"""Analyze the exploratory T13-EA F1--F3 outcome families.

The command-line path is fail closed: it reads response ledgers only after an
independent T13-EA inventory receipt authorizes the scientific open.  It never
loads activation arrays, logit arrays, model artifacts, tokenizers, prompt
banks, or target-bank files.  The public ``analyze_rows`` function exists so
the complete-family mathematics can be tested with synthetic rows before any
T13-EH scientific outcome is inspected.

Every output is descriptive and exploratory.  No statistic in this module is
a primary endpoint, a significance test, a practical-effect decision, or a
confirmatory verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import yaml


ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
CONFIG_PATH = Path("configs/emoji_steering_specificity_analysis_v0.yaml")
ACQUISITION_CONFIG_PATH = Path("configs/emoji_steering_specificity_harvest_v0.yaml")
BOUNDARY_AUDIT_PATH = Path("scripts/audit_emoji_steering_specificity_analysis_v0.py")
GEOMETRY_ANALYZER_PATH = Path(
    "scripts/analyze_emoji_steering_specificity_geometry_v0.py"
)

FAMILY_ORDER = (
    "F1_item_source_form",
    "F2_prototype_depth_dose",
    "F3_random_null_calibration",
)
ENDPOINT_ORDER = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
SOURCE_FORM_ORDER = (
    "glyph",
    "unicode_name",
    "component_name",
    "codepoint_literal",
    "decomposed_form",
)
ITEM_SOURCE_FORMS = ("glyph", "unicode_name", "decomposed_form")
ITEM_CONTRASTS = (
    ("glyph_minus_unicode_name", "glyph", "unicode_name"),
    ("glyph_minus_decomposed_form", "glyph", "decomposed_form"),
    (
        "unicode_name_minus_decomposed_form",
        "unicode_name",
        "decomposed_form",
    ),
)
RANDOM_QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)
SIGNED_REVERSAL_ENDPOINTS = ("entropy_change",)
NONNEGATIVE_ENDPOINTS = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "argmax_flip_rate",
)


class OutcomeAnalysisError(RuntimeError):
    """Raised when an outcome or scientific-open contract is incomplete."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OutcomeAnalysisError(message)


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    stage = path.parent / f".{path.name}.stage-{uuid.uuid4().hex}"
    with stage.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(stage, path)
    except FileExistsError as error:
        stage.unlink()
        raise OutcomeAnalysisError(f"Refusing to overwrite output: {path}") from error
    stage.unlink()


def _config() -> dict[str, Any]:
    value = _read_yaml(_root() / CONFIG_PATH)
    _require(value.get("analysis_id") == ANALYSIS_ID, "T13-EA analysis ID changed")
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EA source protocol changed",
    )
    families = value["scientific_output_families"][:3]
    registered = tuple(str(row["id"]) for row in families)
    _require(registered == FAMILY_ORDER, "T13-EA F1--F3 family order changed")
    f1, f2, f3 = families
    _require(
        f1.get("missing_form_policy")
        == "structural_missingness_reported_without_imputation",
        "T13-EA F1 missingness policy changed",
    )
    _require(
        f2.get("ordered_dose_transform")
        == {
            "entropy_change": "sign_times_endpoint",
            "other_scalar_endpoints": "raw_endpoint",
        },
        "T13-EA F2 dose transform changed",
    )
    _require(
        f3.get("null_scope") == "positive_orientation_isotropic_hidden_space_only"
        and f3.get("calibrated_prototype_signs") == [1],
        "T13-EA F3 positive-only null scope changed",
    )
    _require(
        tuple(str(value) for value in value["scalar_endpoints"]) == ENDPOINT_ORDER,
        "T13-EA scalar endpoint order changed",
    )
    reporting = value["reporting"]
    _require(
        reporting["all_registered_families_reported"] is True,
        "T13-EA complete-family reporting changed",
    )
    _require(
        reporting["no_primary_hypothesis"] is True
        and reporting["no_confirmatory_verdict"] is True,
        "T13-EA exploratory claim boundary changed",
    )
    return value


def _acquisition_config() -> dict[str, Any]:
    value = _read_yaml(_root() / ACQUISITION_CONFIG_PATH)
    _require(
        value.get("protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EH acquisition protocol changed",
    )
    return value


def _stable_seed(base_seed: int, namespace: str, key: Sequence[Any]) -> int:
    payload = json.dumps(
        [int(base_seed), namespace, *key],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _as_float(value: Any, label: str) -> float:
    _require(not isinstance(value, bool), f"Expected numeric {label}")
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise OutcomeAnalysisError(f"Expected numeric {label}") from error
    _require(np.isfinite(result), f"Nonfinite {label}")
    return result


def endpoint_values(row: Mapping[str, Any]) -> dict[str, float]:
    """Return the six frozen scalar endpoints for one synthetic or real row."""

    direct = {
        endpoint: _as_float(row.get(endpoint), endpoint)
        for endpoint in ENDPOINT_ORDER[:4]
    }
    baseline_entropy = _as_float(row.get("baseline_entropy"), "baseline_entropy")
    intervened_entropy = _as_float(row.get("intervened_entropy"), "intervened_entropy")
    flip = row.get("argmax_flip")
    _require(isinstance(flip, bool), "argmax_flip must be boolean")
    direct["entropy_change"] = intervened_entropy - baseline_entropy
    direct["argmax_flip_rate"] = float(flip)
    return direct


def _source_forms_for_system(system: str, *, item: bool) -> tuple[str, ...]:
    if item:
        return (
            ("glyph", "unicode_name")
            if system == "atomic_anchor"
            else ITEM_SOURCE_FORMS
        )
    return (
        ("glyph", "unicode_name", "codepoint_literal")
        if system == "atomic_anchor"
        else SOURCE_FORM_ORDER
    )


def _row_identity(row: Mapping[str, Any], fields: Sequence[str]) -> tuple[Any, ...]:
    values = []
    for field in fields:
        _require(field in row, f"Missing row field: {field}")
        values.append(row[field])
    return tuple(values)


def _index_unique(
    rows: Iterable[Mapping[str, Any]], fields: Sequence[str], label: str
) -> dict[tuple[Any, ...], Mapping[str, Any]]:
    result: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for row in rows:
        key = _row_identity(row, fields)
        _require(key not in result, f"Duplicate {label} cell: {key}")
        result[key] = row
    return result


def _sorted_values(rows: Sequence[Mapping[str, Any]], field: str) -> list[Any]:
    return sorted({row[field] for row in rows})


def _validate_common_rows(rows: Sequence[Mapping[str, Any]], kind: str) -> None:
    _require(bool(rows), f"No {kind} rows")
    for row in rows:
        _row_identity(
            row,
            (
                "model",
                "target_index",
                "target_id",
                "target_group",
                "depth_fraction",
                "magnitude",
                "sign",
            ),
        )
        _require(row.get("condition_kind") == kind, f"Wrong condition kind: {kind}")
        _require(int(row["sign"]) in {-1, 1}, f"Invalid sign in {kind}")
        endpoint_values(row)


def _validate_item_grid(rows: Sequence[Mapping[str, Any]]) -> None:
    _validate_common_rows(rows, "item_source_form")
    index = _index_unique(
        rows,
        (
            "model",
            "item_index",
            "target_index",
            "sign",
            "view",
        ),
        "item",
    )
    models = _sorted_values(rows, "model")
    targets = _sorted_values(rows, "target_index")
    items: dict[Any, str] = {}
    for row in rows:
        item = row["item_index"]
        system = str(row["glyph_system"])
        _require(items.setdefault(item, system) == system, "Item system changed")
    for model in models:
        for item, system in sorted(items.items()):
            expected_views = _source_forms_for_system(system, item=True)
            for target in targets:
                for sign in (-1, 1):
                    for view in expected_views:
                        _require(
                            (model, item, target, sign, view) in index,
                            "Incomplete item source-form grid: "
                            f"{(model, item, target, sign, view)}",
                        )
    _require(
        len(index)
        == sum(
            len(_source_forms_for_system(system, item=True))
            for system in items.values()
        )
        * len(models)
        * len(targets)
        * 2,
        "Unexpected item source-form cell",
    )


def _validate_prototype_grid(rows: Sequence[Mapping[str, Any]]) -> None:
    _validate_common_rows(rows, "glyph_system_source_form_prototype")
    index = _index_unique(
        rows,
        (
            "model",
            "glyph_system",
            "view",
            "target_index",
            "depth_fraction",
            "magnitude",
            "sign",
        ),
        "prototype",
    )
    models = _sorted_values(rows, "model")
    systems = _sorted_values(rows, "glyph_system")
    targets = _sorted_values(rows, "target_index")
    depths = _sorted_values(rows, "depth_fraction")
    magnitudes = _sorted_values(rows, "magnitude")
    for model in models:
        for system in systems:
            for view in _source_forms_for_system(str(system), item=False):
                for target in targets:
                    for depth in depths:
                        for magnitude in magnitudes:
                            for sign in (-1, 1):
                                key = (
                                    model,
                                    system,
                                    view,
                                    target,
                                    depth,
                                    magnitude,
                                    sign,
                                )
                                _require(
                                    key in index,
                                    f"Incomplete prototype grid: {key}",
                                )
    expected_views = sum(
        len(_source_forms_for_system(str(system), item=False)) for system in systems
    )
    expected = (
        len(models) * expected_views * len(targets) * len(depths) * len(magnitudes) * 2
    )
    _require(len(index) == expected, "Unexpected prototype cell")


def _validate_random_grid(rows: Sequence[Mapping[str, Any]]) -> None:
    _validate_common_rows(rows, "random_direction")
    index = _index_unique(
        rows,
        (
            "model",
            "target_index",
            "depth_fraction",
            "magnitude",
            "seed_index",
        ),
        "random",
    )
    models = _sorted_values(rows, "model")
    targets = _sorted_values(rows, "target_index")
    depths = _sorted_values(rows, "depth_fraction")
    magnitudes = _sorted_values(rows, "magnitude")
    seeds = _sorted_values(rows, "seed_index")
    _require(
        all(int(row["sign"]) == 1 for row in rows),
        "Random grid must use its frozen positive orientation",
    )
    expected = {
        (model, target, depth, magnitude, seed)
        for model in models
        for target in targets
        for depth in depths
        for magnitude in magnitudes
        for seed in seeds
    }
    _require(set(index) == expected, "Incomplete or unexpected random grid")


def _validate_cross_family_grid(
    item_rows: Sequence[Mapping[str, Any]],
    prototype_rows: Sequence[Mapping[str, Any]],
    random_rows: Sequence[Mapping[str, Any]],
) -> None:
    target_metadata: dict[Any, tuple[str, str]] = {}
    for rows in (item_rows, prototype_rows, random_rows):
        for row in rows:
            target = row["target_index"]
            metadata = (str(row["target_id"]), str(row["target_group"]))
            _require(
                target_metadata.setdefault(target, metadata) == metadata,
                f"Target metadata changed: {target}",
            )
    for field in ("model", "target_index"):
        expected = set(_sorted_values(item_rows, field))
        _require(
            set(_sorted_values(prototype_rows, field)) == expected
            and set(_sorted_values(random_rows, field)) == expected,
            f"Cross-family {field} grid differs",
        )
    _require(
        set(_sorted_values(prototype_rows, "depth_fraction"))
        == set(_sorted_values(random_rows, "depth_fraction")),
        "Prototype/random depth grid differs",
    )
    _require(
        set(_sorted_values(prototype_rows, "magnitude"))
        == set(_sorted_values(random_rows, "magnitude")),
        "Prototype/random magnitude grid differs",
    )


def _bootstrap_mean_interval(
    records: Sequence[Mapping[str, Any]],
    *,
    value_fields: Sequence[str],
    cluster_fields: Sequence[str],
    replicates: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    _require(replicates > 0, "Bootstrap replicates must be positive")
    values = np.asarray(
        [[_as_float(row[field], field) for field in value_fields] for row in records],
        dtype=np.float64,
    )
    _require(len(values) > 0, "Cannot bootstrap an empty cell")
    codes: list[np.ndarray] = []
    level_counts: list[int] = []
    for field in cluster_fields:
        levels = sorted({row[field] for row in records})
        _require(bool(levels), f"No cluster levels for {field}")
        lookup = {value: index for index, value in enumerate(levels)}
        codes.append(
            np.asarray([lookup[row[field]] for row in records], dtype=np.int64)
        )
        level_counts.append(len(levels))
    rng = np.random.default_rng(seed)
    samples = np.empty((replicates, len(value_fields)), dtype=np.float64)
    for start in range(0, replicates, 128):
        stop = min(replicates, start + 128)
        batch = stop - start
        weights = np.ones((batch, len(records)), dtype=np.float64)
        for code, count in zip(codes, level_counts, strict=True):
            cluster_weights = rng.multinomial(
                count, np.full(count, 1.0 / count), size=batch
            )
            weights *= cluster_weights[:, code]
        denominators = np.sum(weights, axis=1)
        _require(bool((denominators > 0).all()), "Degenerate cluster bootstrap draw")
        samples[start:stop] = (weights @ values) / denominators[:, None]
    result: dict[str, dict[str, float]] = {}
    for index, field in enumerate(value_fields):
        low, high = np.quantile(samples[:, index], (0.025, 0.975))
        result[field] = {"ci95_low": float(low), "ci95_high": float(high)}
    return result


def _summary(
    records: Sequence[Mapping[str, Any]],
    *,
    value_fields: Sequence[str],
    cluster_fields: Sequence[str],
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    values = {
        field: np.asarray([_as_float(row[field], field) for row in records])
        for field in value_fields
    }
    intervals = (
        _bootstrap_mean_interval(
            records,
            value_fields=value_fields,
            cluster_fields=cluster_fields,
            replicates=replicates,
            seed=seed,
        )
        if replicates > 0
        else {}
    )
    return {
        "n_rows": len(records),
        "cluster_counts": {
            field: len({row[field] for row in records}) for field in cluster_fields
        },
        "statistics": {
            field: {
                "mean": float(np.mean(value)),
                "median": float(np.median(value)),
                "minimum": float(np.min(value)),
                "maximum": float(np.max(value)),
                **intervals.get(field, {}),
            }
            for field, value in values.items()
        },
    }


def _group_records(
    records: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> dict[tuple[Any, ...], list[Mapping[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[_row_identity(row, fields)].append(row)
    return dict(grouped)


def analyze_f1(
    rows: Sequence[Mapping[str, Any]], *, replicates: int, seed: int
) -> dict[str, Any]:
    _validate_item_grid(rows)
    index = _index_unique(
        rows,
        (
            "model",
            "item_index",
            "target_index",
            "sign",
            "view",
        ),
        "item",
    )
    bases = sorted(
        {
            (
                row["model"],
                row["item_index"],
                row["glyph_system"],
                row["target_index"],
                row["target_id"],
                row["target_group"],
                int(row["sign"]),
            )
            for row in rows
        }
    )
    paired: list[dict[str, Any]] = []
    for model, item, system, target, target_id, target_group, sign in bases:
        available = _source_forms_for_system(str(system), item=True)
        for contrast, left, right in ITEM_CONTRASTS:
            if left not in available or right not in available:
                continue
            left_values = endpoint_values(index[(model, item, target, sign, left)])
            right_values = endpoint_values(index[(model, item, target, sign, right)])
            for endpoint in ENDPOINT_ORDER:
                paired.append(
                    {
                        "model": model,
                        "glyph_system": system,
                        "item_index": item,
                        "target_index": target,
                        "target_id": target_id,
                        "target_group": target_group,
                        "sign": sign,
                        "contrast": contrast,
                        "left_source_form": left,
                        "right_source_form": right,
                        "endpoint": endpoint,
                        "paired_difference": left_values[endpoint]
                        - right_values[endpoint],
                    }
                )
    group_fields = ("model", "glyph_system", "contrast", "sign", "endpoint")
    system_summaries = []
    for key, records in sorted(_group_records(paired, group_fields).items()):
        summary_seed = _stable_seed(seed, "F1", key)
        system_summaries.append(
            {
                **dict(zip(group_fields, key, strict=True)),
                "eligible_item_count": len({row["item_index"] for row in records}),
                "eligible_target_count": len({row["target_index"] for row in records}),
                "denominator_rule": "complete_paired_rows_no_imputation",
                "weighting": "eligible_item_by_target_micro_within_model",
                **_summary(
                    records,
                    value_fields=("paired_difference",),
                    cluster_fields=("item_index", "target_index"),
                    replicates=replicates,
                    seed=summary_seed,
                ),
            }
        )
    pooled_fields = ("model", "contrast", "sign", "endpoint")
    pooled_summaries = []
    for key, records in sorted(_group_records(paired, pooled_fields).items()):
        pooled_summaries.append(
            {
                **dict(zip(pooled_fields, key, strict=True)),
                "eligible_item_count": len({row["item_index"] for row in records}),
                "eligible_target_count": len({row["target_index"] for row in records}),
                "denominator_rule": "complete_paired_rows_no_imputation",
                "weighting": "eligible_item_by_target_micro_within_model",
                **_summary(
                    records,
                    value_fields=("paired_difference",),
                    cluster_fields=("item_index", "target_index"),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F1-pooled", key),
                ),
            }
        )
    systems = _sorted_values(rows, "glyph_system")
    availability = [
        {
            "glyph_system": system,
            "contrast": contrast,
            "status": "available"
            if left in _source_forms_for_system(str(system), item=True)
            and right in _source_forms_for_system(str(system), item=True)
            else "structurally_unavailable",
        }
        for system in systems
        for contrast, left, right in ITEM_CONTRASTS
    ]
    denominator_rows = []
    all_items = {row["item_index"] for row in rows}
    for contrast, left, right in ITEM_CONTRASTS:
        eligible_items = {
            row["item_index"]
            for row in rows
            if left in _source_forms_for_system(str(row["glyph_system"]), item=True)
            and right in _source_forms_for_system(str(row["glyph_system"]), item=True)
        }
        denominator_rows.append(
            {
                "contrast": contrast,
                "eligible_item_count": len(eligible_items),
                "production_expected_eligible_item_count": (
                    192 if contrast == "glyph_minus_unicode_name" else 168
                ),
                "excluded_item_count": len(all_items - eligible_items),
                "missing_value_policy": "no_imputation",
            }
        )
    return {
        "family_id": FAMILY_ORDER[0],
        "status": "exploratory_complete_family",
        "paired_contrasts": paired,
        "summaries": system_summaries,
        "system_summaries": system_summaries,
        "pooled_summaries": pooled_summaries,
        "overall_summaries": pooled_summaries,
        "contrast_availability": availability,
        "contrast_denominators": denominator_rows,
        "token_matching_scope": {
            "maximum_supported_label": "count_signature_only",
            "token_identity_matched": False,
            "prefix_token_identity_matched": False,
            "semantic_equivalence_claimed": False,
        },
        "rows_retained": len(rows),
    }


def _prototype_endpoint_cells(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        for endpoint, value in endpoint_values(row).items():
            result.append(
                {
                    "model": row["model"],
                    "glyph_system": row["glyph_system"],
                    "source_form": row["view"],
                    "target_index": row["target_index"],
                    "target_id": row["target_id"],
                    "target_group": row["target_group"],
                    "depth_fraction": float(row["depth_fraction"]),
                    "magnitude": float(row["magnitude"]),
                    "sign": int(row["sign"]),
                    "endpoint": endpoint,
                    "value": value,
                }
            )
    return result


def analyze_f2(
    rows: Sequence[Mapping[str, Any]], *, replicates: int, seed: int
) -> dict[str, Any]:
    _validate_prototype_grid(rows)
    cells = _prototype_endpoint_cells(rows)
    surface_fields = (
        "model",
        "glyph_system",
        "source_form",
        "depth_fraction",
        "magnitude",
        "sign",
        "endpoint",
    )
    surface = []
    for key, records in sorted(_group_records(cells, surface_fields).items()):
        surface.append(
            {
                **dict(zip(surface_fields, key, strict=True)),
                **_summary(
                    records,
                    value_fields=("value",),
                    cluster_fields=("target_index",),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F2-surface", key),
                ),
            }
        )
    headline_fields = (
        "model",
        "source_form",
        "depth_fraction",
        "magnitude",
        "sign",
        "endpoint",
    )
    headline_summaries = []
    for key, records in sorted(_group_records(surface, headline_fields).items()):
        system_means = np.asarray(
            [float(row["statistics"]["value"]["mean"]) for row in records],
            dtype=np.float64,
        )
        headline_summaries.append(
            {
                **dict(zip(headline_fields, key, strict=True)),
                "eligible_systems": sorted(str(row["glyph_system"]) for row in records),
                "eligible_system_count": len(records),
                "targets_per_system": sorted(
                    {int(row["cluster_counts"]["target_index"]) for row in records}
                ),
                "weighting": (
                    "eligible_system_equal_weight_macro_of_target_micro_means"
                ),
                "mean": float(np.mean(system_means)),
                "minimum_system_mean": float(np.min(system_means)),
                "maximum_system_mean": float(np.max(system_means)),
            }
        )

    dose_base_fields = (
        "model",
        "glyph_system",
        "source_form",
        "target_index",
        "target_id",
        "target_group",
        "depth_fraction",
        "sign",
        "endpoint",
    )
    dose_records = []
    for key, records in sorted(_group_records(cells, dose_base_fields).items()):
        ordered = sorted(records, key=lambda row: float(row["magnitude"]))
        magnitudes = [float(row["magnitude"]) for row in ordered]
        _require(
            len(magnitudes) == len(set(magnitudes)),
            f"Duplicate dose cell: {key}",
        )
        values = [float(row["value"]) for row in ordered]
        endpoint = str(key[-1])
        sign = int(key[-2])
        transformed = (
            [sign * value for value in values]
            if endpoint == "entropy_change"
            else values
        )
        dose_records.append(
            {
                **dict(zip(dose_base_fields, key, strict=True)),
                "dose_count": len(values),
                "ordered_dose_transform": (
                    "sign_times_endpoint"
                    if endpoint == "entropy_change"
                    else "raw_endpoint"
                ),
                "ordered_non_decreasing": float(
                    all(
                        right >= left
                        for left, right in zip(transformed, transformed[1:])
                    )
                ),
            }
        )
    dose_summary_fields = (
        "model",
        "glyph_system",
        "source_form",
        "depth_fraction",
        "sign",
        "endpoint",
    )
    dose_summaries = []
    for key, records in sorted(
        _group_records(dose_records, dose_summary_fields).items()
    ):
        dose_summaries.append(
            {
                **dict(zip(dose_summary_fields, key, strict=True)),
                **_summary(
                    records,
                    value_fields=("ordered_non_decreasing",),
                    cluster_fields=("target_index",),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F2-dose", key),
                ),
            }
        )

    sign_base_fields = (
        "model",
        "glyph_system",
        "source_form",
        "target_index",
        "target_id",
        "target_group",
        "depth_fraction",
        "magnitude",
        "endpoint",
    )
    sign_records = []
    for key, records in sorted(_group_records(cells, sign_base_fields).items()):
        by_sign = {int(row["sign"]): float(row["value"]) for row in records}
        _require(set(by_sign) == {-1, 1}, f"Incomplete sign pair: {key}")
        positive = by_sign[1]
        negative = by_sign[-1]
        endpoint = str(key[-1])
        magnitude_denominator = abs(positive) + abs(negative)
        record = {
            **dict(zip(sign_base_fields, key, strict=True)),
            "positive_value": positive,
            "negative_value": negative,
            "positive_minus_negative": positive - negative,
            "magnitude_symmetry_absolute_residual": abs(abs(positive) - abs(negative)),
            "magnitude_symmetry_normalized_residual": (
                abs(abs(positive) - abs(negative)) / magnitude_denominator
                if magnitude_denominator > 0.0
                else 0.0
            ),
            "reversal_evidence_eligible": endpoint in SIGNED_REVERSAL_ENDPOINTS,
            "interpretation": (
                "signed_reversal_diagnostic"
                if endpoint in SIGNED_REVERSAL_ENDPOINTS
                else "orientation_asymmetry_only_not_reversal_evidence"
            ),
        }
        if endpoint in SIGNED_REVERSAL_ENDPOINTS:
            denominator = abs(positive) + abs(negative)
            record.update(
                {
                    "positive_plus_negative": positive + negative,
                    "normalized_antisymmetry_residual": (
                        abs(positive + negative) / denominator
                        if denominator > 0.0
                        else 0.0
                    ),
                }
            )
        sign_records.append(record)
    sign_summary_fields = (
        "model",
        "glyph_system",
        "source_form",
        "depth_fraction",
        "magnitude",
        "endpoint",
    )
    sign_orientation_summaries = []
    orientation_values = (
        "positive_value",
        "negative_value",
        "positive_minus_negative",
        "magnitude_symmetry_absolute_residual",
        "magnitude_symmetry_normalized_residual",
    )
    for key, records in sorted(
        _group_records(sign_records, sign_summary_fields).items()
    ):
        sign_orientation_summaries.append(
            {
                **dict(zip(sign_summary_fields, key, strict=True)),
                "interpretation": (
                    "signed_endpoint_orientation_summary"
                    if key[-1] in SIGNED_REVERSAL_ENDPOINTS
                    else "nonnegative_endpoint_orientation_asymmetry_only"
                ),
                **_summary(
                    records,
                    value_fields=orientation_values,
                    cluster_fields=("target_index",),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F2-sign", key),
                ),
            }
        )
    antisymmetry_records = [
        row for row in sign_records if row["endpoint"] in SIGNED_REVERSAL_ENDPOINTS
    ]
    sign_antisymmetry_summaries = []
    for key, records in sorted(
        _group_records(antisymmetry_records, sign_summary_fields).items()
    ):
        sign_antisymmetry_summaries.append(
            {
                **dict(zip(sign_summary_fields, key, strict=True)),
                "interpretation": "signed_reversal_diagnostic_not_causal_evidence",
                **_summary(
                    records,
                    value_fields=(
                        "positive_plus_negative",
                        "normalized_antisymmetry_residual",
                    ),
                    cluster_fields=("target_index",),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F2-antisymmetry", key),
                ),
            }
        )

    source_base_fields = (
        "model",
        "glyph_system",
        "target_index",
        "target_id",
        "target_group",
        "depth_fraction",
        "magnitude",
        "sign",
        "endpoint",
    )
    source_contrasts = []
    for key, records in sorted(_group_records(cells, source_base_fields).items()):
        by_source = {str(row["source_form"]): float(row["value"]) for row in records}
        expected = _source_forms_for_system(str(key[1]), item=False)
        _require(
            set(by_source) == set(expected), f"Prototype source forms differ: {key}"
        )
        for left_index, left in enumerate(expected):
            for right in expected[left_index + 1 :]:
                source_contrasts.append(
                    {
                        **dict(zip(source_base_fields, key, strict=True)),
                        "contrast": f"{left}_minus_{right}",
                        "left_source_form": left,
                        "right_source_form": right,
                        "paired_difference": by_source[left] - by_source[right],
                    }
                )
    source_summary_fields = (
        "model",
        "glyph_system",
        "contrast",
        "depth_fraction",
        "magnitude",
        "sign",
        "endpoint",
    )
    source_summaries = []
    for key, records in sorted(
        _group_records(source_contrasts, source_summary_fields).items()
    ):
        source_summaries.append(
            {
                **dict(zip(source_summary_fields, key, strict=True)),
                **_summary(
                    records,
                    value_fields=("paired_difference",),
                    cluster_fields=("target_index",),
                    replicates=replicates,
                    seed=_stable_seed(seed, "F2-source", key),
                ),
            }
        )
    return {
        "family_id": FAMILY_ORDER[1],
        "status": "exploratory_complete_family",
        "surface_summaries": surface,
        "complete_surface_summaries": surface,
        "headline_macro_summaries": headline_summaries,
        "dose_order_records": dose_records,
        "dose_order_summaries": dose_summaries,
        "sign_pair_records": sign_records,
        "sign_pair_summaries": sign_orientation_summaries,
        "sign_orientation_summaries": sign_orientation_summaries,
        "sign_antisymmetry_summaries": sign_antisymmetry_summaries,
        "sign_reversal_endpoint_policy": {
            "eligible": list(SIGNED_REVERSAL_ENDPOINTS),
            "nonnegative_orientation_only": list(NONNEGATIVE_ENDPOINTS),
            "countsketch_sign_reversal": "deferred_to_F5_within_model_only",
        },
        "source_form_contrasts": source_contrasts,
        "source_form_contrast_summaries": source_summaries,
        "rows_retained": len(rows),
    }


def _random_endpoint_cells(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        for endpoint, value in endpoint_values(row).items():
            result.append(
                {
                    "model": row["model"],
                    "target_index": row["target_index"],
                    "target_id": row["target_id"],
                    "target_group": row["target_group"],
                    "depth_fraction": float(row["depth_fraction"]),
                    "magnitude": float(row["magnitude"]),
                    "seed_index": int(row["seed_index"]),
                    "endpoint": endpoint,
                    "value": value,
                }
            )
    return result


def _midrank_percentile(value: float, null: np.ndarray) -> float:
    return float(
        (np.count_nonzero(null < value) + 0.5 * np.count_nonzero(null == value))
        / len(null)
    )


def _bootstrap_calibration(
    prototype_by_target: Mapping[Any, float],
    random_by_target: Mapping[Any, Mapping[Any, float]],
    *,
    replicates: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    _require(replicates > 0, "Calibration bootstrap replicates must be positive")
    targets = sorted(prototype_by_target)
    _require(targets == sorted(random_by_target), "Calibration target grid differs")
    seed_levels = sorted(next(iter(random_by_target.values())))
    _require(bool(seed_levels), "Calibration random grid is empty")
    _require(
        all(sorted(values) == seed_levels for values in random_by_target.values()),
        "Calibration random seed grid differs by target",
    )
    prototypes = np.asarray([prototype_by_target[target] for target in targets])
    random = np.asarray(
        [
            [random_by_target[target][seed_level] for seed_level in seed_levels]
            for target in targets
        ],
        dtype=np.float64,
    )
    rng = np.random.default_rng(seed)
    differences = np.empty(replicates, dtype=np.float64)
    percentiles = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 128):
        stop = min(replicates, start + 128)
        batch = stop - start
        target_counts = rng.multinomial(
            len(targets), np.full(len(targets), 1.0 / len(targets)), size=batch
        )
        sampled_seeds = rng.integers(
            0, len(seed_levels), size=(batch, len(seed_levels))
        )
        for offset in range(batch):
            sampled_null = random[:, sampled_seeds[offset]]
            medians = np.median(sampled_null, axis=1)
            ranks = np.mean(
                (sampled_null < prototypes[:, None])
                + 0.5 * (sampled_null == prototypes[:, None]),
                axis=1,
            )
            weights = target_counts[offset]
            differences[start + offset] = float(
                np.sum(weights * (prototypes - medians)) / np.sum(weights)
            )
            percentiles[start + offset] = float(
                np.sum(weights * ranks) / np.sum(weights)
            )
    result = {}
    for name, values in (
        ("prototype_minus_random_median", differences),
        ("prototype_random_percentile", percentiles),
    ):
        low, high = np.quantile(values, (0.025, 0.975))
        result[name] = {"ci95_low": float(low), "ci95_high": float(high)}
    return result


def analyze_f3(
    prototype_rows: Sequence[Mapping[str, Any]],
    random_rows: Sequence[Mapping[str, Any]],
    *,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    _validate_prototype_grid(prototype_rows)
    _validate_random_grid(random_rows)
    prototype_cells = _prototype_endpoint_cells(prototype_rows)
    random_cells = _random_endpoint_cells(random_rows)
    null_fields = (
        "model",
        "target_index",
        "target_id",
        "target_group",
        "depth_fraction",
        "magnitude",
        "endpoint",
    )
    null_quantiles = []
    random_lookup: dict[tuple[Any, ...], dict[Any, float]] = {}
    for key, records in sorted(_group_records(random_cells, null_fields).items()):
        values = np.asarray([float(row["value"]) for row in records])
        seeds = {int(row["seed_index"]): float(row["value"]) for row in records}
        _require(len(seeds) == len(records), f"Duplicate random seed cell: {key}")
        random_lookup[(key[0], key[1], key[4], key[5], key[6])] = seeds
        null_quantiles.append(
            {
                **dict(zip(null_fields, key, strict=True)),
                "random_seed_count": len(values),
                "quantiles": {
                    f"q{int(quantile * 100):02d}": float(np.quantile(values, quantile))
                    for quantile in RANDOM_QUANTILES
                },
            }
        )

    calibrations = []
    for row in prototype_cells:
        if int(row["sign"]) != 1:
            continue
        lookup_key = (
            row["model"],
            row["target_index"],
            row["depth_fraction"],
            row["magnitude"],
            row["endpoint"],
        )
        _require(
            lookup_key in random_lookup, f"Missing matched random null: {lookup_key}"
        )
        null = np.asarray(list(random_lookup[lookup_key].values()), dtype=np.float64)
        value = float(row["value"])
        calibrations.append(
            {
                **row,
                "random_median": float(np.median(null)),
                "prototype_minus_random_median": value - float(np.median(null)),
                "prototype_random_percentile": _midrank_percentile(value, null),
                "random_seed_count": len(null),
            }
        )

    summary_fields = (
        "model",
        "glyph_system",
        "source_form",
        "depth_fraction",
        "magnitude",
        "sign",
        "endpoint",
    )
    summaries = []
    for key, records in sorted(_group_records(calibrations, summary_fields).items()):
        prototype_by_target = {
            row["target_index"]: float(row["value"]) for row in records
        }
        _require(
            len(prototype_by_target) == len(records),
            f"Duplicate prototype calibration target: {key}",
        )
        random_by_target = {
            target: random_lookup[(key[0], target, key[3], key[4], key[6])]
            for target in prototype_by_target
        }
        intervals = (
            _bootstrap_calibration(
                prototype_by_target,
                random_by_target,
                replicates=replicates,
                seed=_stable_seed(seed, "F3-calibration", key),
            )
            if replicates > 0
            else {}
        )
        differences = np.asarray(
            [float(row["prototype_minus_random_median"]) for row in records]
        )
        percentiles = np.asarray(
            [float(row["prototype_random_percentile"]) for row in records]
        )
        summaries.append(
            {
                **dict(zip(summary_fields, key, strict=True)),
                "n_targets": len(records),
                "random_seed_count_per_target": len(
                    next(iter(random_by_target.values()))
                ),
                "prototype_minus_random_median": {
                    "mean": float(np.mean(differences)),
                    "median": float(np.median(differences)),
                    **intervals.get("prototype_minus_random_median", {}),
                },
                "prototype_random_percentile": {
                    "mean": float(np.mean(percentiles)),
                    "median": float(np.median(percentiles)),
                    **intervals.get("prototype_random_percentile", {}),
                },
            }
        )
    headline_fields = (
        "model",
        "source_form",
        "depth_fraction",
        "magnitude",
        "endpoint",
    )
    headline_summaries = []
    for key, records in sorted(_group_records(calibrations, headline_fields).items()):
        by_system = _group_records(records, ("glyph_system",))
        system_differences = np.asarray(
            [
                np.mean([float(row["prototype_minus_random_median"]) for row in values])
                for values in by_system.values()
            ],
            dtype=np.float64,
        )
        system_percentiles = np.asarray(
            [
                np.mean([float(row["prototype_random_percentile"]) for row in values])
                for values in by_system.values()
            ],
            dtype=np.float64,
        )
        headline_summaries.append(
            {
                **dict(zip(headline_fields, key, strict=True)),
                "calibrated_sign": 1,
                "eligible_systems": sorted(str(system[0]) for system in by_system),
                "eligible_system_count": len(by_system),
                "targets_per_system": sorted(
                    {
                        len({row["target_index"] for row in values})
                        for values in by_system.values()
                    }
                ),
                "weighting": (
                    "eligible_system_equal_weight_macro_of_target_micro_means"
                ),
                "prototype_minus_random_median_mean": float(
                    np.mean(system_differences)
                ),
                "prototype_random_percentile_mean": float(np.mean(system_percentiles)),
            }
        )
    return {
        "family_id": FAMILY_ORDER[2],
        "status": "exploratory_complete_family",
        "random_null_definition": (
            "positive_orientation_isotropic_standard_normal_then_unit_rms"
        ),
        "negative_random_orientation_acquired": False,
        "negative_prototype_policy": (
            "retained_in_F2_but_not_called_sign_matched_random_calibration"
        ),
        "random_quantiles": null_quantiles,
        "prototype_calibrations": calibrations,
        "calibration_summaries": summaries,
        "headline_macro_summaries": headline_summaries,
        "prototype_rows_retained": len(prototype_rows),
        "calibrated_positive_prototype_rows": sum(
            int(row["sign"]) == 1 for row in prototype_rows
        ),
        "uncalibrated_negative_prototype_rows": sum(
            int(row["sign"]) == -1 for row in prototype_rows
        ),
        "random_rows_retained": len(random_rows),
    }


def _require_frozen_grid_counts(
    item_rows: Sequence[Mapping[str, Any]],
    prototype_rows: Sequence[Mapping[str, Any]],
    random_rows: Sequence[Mapping[str, Any]],
) -> None:
    acquisition = _acquisition_config()
    roles = tuple(str(value) for value in acquisition["pilot"]["roles"])
    for rows, grid, label in (
        (item_rows, "item_grid", "item"),
        (prototype_rows, "prototype_grid", "prototype"),
        (random_rows, "random_grid", "random"),
    ):
        observed = {str(row["model"]) for row in rows}
        _require(observed == set(roles), f"Frozen {label} pilot roster differs")
        expected = int(acquisition["pilot"][grid]["expected_response_rows_per_model"])
        for role in roles:
            _require(
                sum(str(row["model"]) == role for row in rows) == expected,
                f"Frozen {label} row count differs: {role}",
            )
    target_indices = set(range(32))
    _require(
        {int(row["target_index"]) for row in item_rows} == target_indices,
        "Frozen item target grid differs",
    )
    item_systems: dict[int, str] = {}
    for row in item_rows:
        item = int(row["item_index"])
        system = str(row["glyph_system"])
        _require(
            item_systems.setdefault(item, system) == system,
            f"Frozen item system differs: {item}",
        )
        _require(
            float(row["depth_fraction"]) == 0.5 and float(row["magnitude"]) == 0.25,
            "Frozen F1 depth or magnitude differs",
        )
    _require(set(item_systems) == set(range(192)), "Frozen F1 item population differs")
    observed_system_counts = {
        system: sum(value == system for value in item_systems.values())
        for system in acquisition["population"]["system_order"]
    }
    _require(
        observed_system_counts == acquisition["population"]["expected_system_counts"],
        "Frozen F1 system denominators differ",
    )
    depths = {float(value) for value in acquisition["depth"]["normalized_fractions"]}
    prototype_magnitudes = {
        float(value) for value in acquisition["pilot"]["prototype_grid"]["magnitudes"]
    }
    random_magnitudes = {
        float(value) for value in acquisition["pilot"]["random_grid"]["magnitudes"]
    }
    _require(
        {float(row["depth_fraction"]) for row in prototype_rows} == depths
        and {float(row["depth_fraction"]) for row in random_rows} == depths,
        "Frozen F2/F3 depth grid differs",
    )
    _require(
        {float(row["magnitude"]) for row in prototype_rows} == prototype_magnitudes
        and {float(row["magnitude"]) for row in random_rows} == random_magnitudes,
        "Frozen F2/F3 magnitude grid differs",
    )
    _require(
        {int(row["seed_index"]) for row in random_rows} == set(range(64)),
        "Frozen F3 seed-index grid differs",
    )


def analyze_rows(
    item_rows: Sequence[Mapping[str, Any]],
    prototype_rows: Sequence[Mapping[str, Any]],
    random_rows: Sequence[Mapping[str, Any]],
    *,
    bootstrap_replicates: int | None = None,
    bootstrap_seed: int | None = None,
    require_frozen_grid: bool = False,
) -> dict[str, Any]:
    """Analyze complete F1--F3 rows; intended tests pass only synthetic rows."""

    config = _config()
    reporting = config["reporting"]
    replicates = (
        int(reporting["bootstrap_replicates"])
        if bootstrap_replicates is None
        else int(bootstrap_replicates)
    )
    seed = (
        int(reporting["bootstrap_seed"])
        if bootstrap_seed is None
        else int(bootstrap_seed)
    )
    _require(replicates >= 0, "Bootstrap replicates must be nonnegative")
    _validate_item_grid(item_rows)
    _validate_prototype_grid(prototype_rows)
    _validate_random_grid(random_rows)
    _validate_cross_family_grid(item_rows, prototype_rows, random_rows)
    if require_frozen_grid:
        _require_frozen_grid_counts(item_rows, prototype_rows, random_rows)
    families = {
        FAMILY_ORDER[0]: analyze_f1(item_rows, replicates=replicates, seed=seed),
        FAMILY_ORDER[1]: analyze_f2(prototype_rows, replicates=replicates, seed=seed),
        FAMILY_ORDER[2]: analyze_f3(
            prototype_rows, random_rows, replicates=replicates, seed=seed
        ),
    }
    return {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "exploratory_f1_f2_f3_complete",
        "claim_boundary": config["claim_boundary"],
        "decision_status": "no_primary_no_significance_test_no_confirmatory_verdict",
        "family_order": list(FAMILY_ORDER),
        "endpoint_order": list(ENDPOINT_ORDER),
        "cross_model_comparison_policy": {
            "scalar_summary_comparison": "descriptive_only",
            "countsketch_coordinate_comparison": "forbidden",
            "token_id_comparison": "forbidden",
        },
        "reporting": {
            "multiplicity": reporting["multiplicity"],
            "registered_interval": reporting["interval"],
            "executed_interval": reporting["interval"] if replicates > 0 else None,
            "registered_bootstrap_replicates": int(reporting["bootstrap_replicates"]),
            "executed_bootstrap_replicates": replicates,
            "bootstrap_seed": seed,
            "bootstrap_status": (
                "registered_replicates_computed_hash_merge_pending"
                if replicates == int(reporting["bootstrap_replicates"])
                else "point_estimates_only_bootstrap_pending"
                if replicates == 0
                else "synthetic_or_development_override_not_paper_interval_gate"
            ),
            "paper_interval_gate_satisfied": False,
            "paper_interval_gate_requirement": reporting["paper_interval_gate"],
            "all_registered_families_reported": True,
            "outcome_based_family_or_cell_filtering": False,
        },
        "families": families,
    }


def _validate_scientific_open_receipt(
    receipt_path: Path, run_root: Path
) -> dict[str, Any]:
    _require(
        not receipt_path.is_relative_to(run_root),
        "Scientific-open closeout receipt must be outside run root",
    )
    receipt = _read_json(receipt_path)
    _require(receipt.get("schema_version") == 1, "Closeout schema version differs")
    _require(receipt.get("analysis_id") == ANALYSIS_ID, "Inventory analysis ID differs")
    _require(
        receipt.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Inventory source protocol differs",
    )
    _require(
        receipt.get("status") == "scientific_open_closeout_complete",
        "Scientific-open closeout incomplete",
    )
    _require(
        receipt.get("scientific_open_authorized") is True,
        "Scientific open is not authorized",
    )
    _require(
        receipt.get("independent_hash_verification") is True,
        "Independent hash verification missing",
    )
    _require(
        receipt.get("scientific_values_parsed") is False,
        "Closeout must remain outcome blind",
    )
    _require(
        Path(str(receipt.get("run_root"))).resolve() == run_root,
        "Inventory run root differs",
    )
    _require(
        int(receipt.get("roles_complete", -1))
        == int(receipt.get("roles_required", -2))
        == 9,
        "Inventory role completion differs",
    )
    run_binding_root = receipt.get("run_binding_root_sha256")
    _require(
        isinstance(run_binding_root, str)
        and len(run_binding_root) == 64
        and all(character in "0123456789abcdef" for character in run_binding_root),
        "Closeout run binding root is invalid",
    )
    return receipt


def _audit_closeout_same_process(
    run_root: Path, receipt_path: Path, expected_binding_root: str
) -> dict[str, Any]:
    path = _root() / BOUNDARY_AUDIT_PATH
    spec = importlib.util.spec_from_file_location(
        "glyphprobe_t13ea_same_process_closeout_audit", path
    )
    _require(
        spec is not None and spec.loader is not None,
        "Cannot load T13-EA boundary auditor",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    audit = getattr(module, "audit_verified_closeout", None)
    _require(callable(audit), "T13-EA closeout auditor is unavailable")
    result = audit(run_root, receipt_path)
    _require(
        isinstance(result, dict)
        and result.get("status") == "scientific_open_closeout_audit_pass"
        and result.get("scientific_values_parsed") is False
        and result.get("run_binding_root_sha256") == expected_binding_root,
        "Same-process scientific-open closeout audit differs",
    )
    return result


def _verify_bound_file(path: Path, role: str) -> dict[str, Any]:
    shard_receipt = _read_json(path.parent / "receipt.json")
    _require(
        shard_receipt.get("protocol_id") == SOURCE_PROTOCOL_ID
        and shard_receipt.get("model_role") == role,
        f"Artifact receipt authority differs: {path}",
    )
    files = shard_receipt.get("files")
    _require(isinstance(files, dict), f"Artifact receipt bindings missing: {path}")
    binding = files.get(path.name)
    _require(isinstance(binding, dict), f"Artifact binding missing: {path}")
    _require(
        path.stat().st_size == int(binding.get("bytes", -1))
        and _sha256(path) == str(binding.get("sha256")),
        f"Artifact changed after closeout: {path}",
    )
    return shard_receipt


def _verify_zero_gate_same_process(
    run_root: Path, run_binding_root: str
) -> dict[str, Any]:
    """Open only zero controls and call the shared exact-noop verifier."""

    path = _root() / GEOMETRY_ANALYZER_PATH
    spec = importlib.util.spec_from_file_location(
        "glyphprobe_t13ea_shared_zero_verifier", path
    )
    _require(
        spec is not None and spec.loader is not None,
        "Cannot load shared T13-EA zero verifier",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verifier = getattr(module, "validate_zero_control", None)
    _require(callable(verifier), "Shared T13-EA zero verifier is unavailable")
    config = _config()
    pilots = [str(value) for value in config["acquisition_gate"]["pilot_roles"]]
    model_config = _read_yaml(
        _root() / "configs/semantic_atlas_cross_model_replication_v0.yaml"
    )["models"]
    results = []
    for role in pilots:
        directory = run_root / role / "pilot" / "zero" / "all-sites"
        names = (
            "response_ledger.jsonl",
            "top_positive_ids.npy",
            "top_positive_values.npy",
            "top_negative_ids.npy",
            "top_negative_values.npy",
            "countsketch.npy",
        )
        for name in names:
            _verify_bound_file(directory / name, role)
        rows = _read_jsonl(directory / "response_ledger.jsonl")
        result = verifier(
            rows,
            top_positive_ids=np.load(
                directory / "top_positive_ids.npy", mmap_mode="r", allow_pickle=False
            ),
            top_positive_values=np.load(
                directory / "top_positive_values.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            top_negative_ids=np.load(
                directory / "top_negative_ids.npy", mmap_mode="r", allow_pickle=False
            ),
            top_negative_values=np.load(
                directory / "top_negative_values.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            countsketch=np.load(
                directory / "countsketch.npy", mmap_mode="r", allow_pickle=False
            ),
            vocab_size=int(model_config[role]["expected_vocab_size"]),
        )
        _require(
            result.get("status") == "exact_noop_pass"
            and int(result.get("rows", -1)) == 256,
            f"Zero-hook gate failed: {role}",
        )
        results.append({"model": role, **result})
    return {
        "status": "all_pilot_zero_controls_exact_noop",
        "run_binding_root_sha256": run_binding_root,
        "models": results,
        "nonzero_response_values_read_before_gate": False,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            _require(
                isinstance(value, dict), f"Expected JSON object: {path}:{line_number}"
            )
            rows.append(value)
    return rows


def _load_kind_ledgers(
    run_root: Path, role: str, kind: str, expected_shards: int
) -> list[dict[str, Any]]:
    base = run_root / role / "pilot" / kind
    paths = sorted(base.glob("*/response_ledger.jsonl"))
    _require(len(paths) == expected_shards, f"{role}/{kind} shard count differs")
    rows = []
    condition_kind = {
        "item": "item_source_form",
        "prototype": "glyph_system_source_form_prototype",
        "random": "random_direction",
    }[kind]
    for path in paths:
        _verify_bound_file(path, role)
        for value in _read_jsonl(path):
            _require(
                value.get("condition_kind") == condition_kind,
                f"Wrong condition kind in {path}",
            )
            if "model" in value:
                _require(value["model"] == role, f"Ledger model differs: {path}")
            row = dict(value)
            row["model"] = role
            rows.append(row)
    return rows


def load_authorized_rows(
    run_root: Path, scientific_open_receipt: Path
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Load only response ledgers after the independent scientific-open gate."""

    root = run_root.expanduser().resolve(strict=True)
    receipt_path = scientific_open_receipt.expanduser().resolve(strict=True)
    closeout = _validate_scientific_open_receipt(receipt_path, root)
    closeout_audit = _audit_closeout_same_process(
        root, receipt_path, str(closeout["run_binding_root_sha256"])
    )
    zero_gate = _verify_zero_gate_same_process(
        root, str(closeout["run_binding_root_sha256"])
    )
    acquisition = _acquisition_config()
    roles = [str(value) for value in acquisition["pilot"]["roles"]]
    item_rows: list[dict[str, Any]] = []
    prototype_rows: list[dict[str, Any]] = []
    random_rows: list[dict[str, Any]] = []
    for role in roles:
        item_rows.extend(_load_kind_ledgers(root, role, "item", 12))
        prototype_rows.extend(_load_kind_ledgers(root, role, "prototype", 6))
        random_rows.extend(_load_kind_ledgers(root, role, "random", 8))
    return (
        item_rows,
        prototype_rows,
        random_rows,
        {
            "closeout_sha256": _sha256(receipt_path),
            "same_process_closeout_audit": closeout_audit,
            "zero_hook_gate": zero_gate,
        },
    )


def compact_production_output(result: dict[str, Any]) -> dict[str, Any]:
    """Drop bulky derived detail rows while retaining every fixed summary."""

    families = result["families"]
    omissions = {
        FAMILY_ORDER[0]: ("paired_contrasts",),
        FAMILY_ORDER[1]: (
            "dose_order_records",
            "sign_pair_records",
            "source_form_contrasts",
        ),
        FAMILY_ORDER[2]: ("prototype_calibrations",),
    }
    for family_id, keys in omissions.items():
        family = families[family_id]
        rows = []
        for key in keys:
            value = family.pop(key)
            rows.append(
                {
                    "key": key,
                    "record_count": len(value),
                    "recomputable_from": "hash_bound_sealed_response_ledgers",
                    "omission_reason": "production_json_size_control",
                }
            )
        family["omitted_derived_detail"] = rows
    f1 = families[FAMILY_ORDER[0]]
    f1.pop("summaries", None)
    f1.pop("pooled_summaries", None)
    f2 = families[FAMILY_ORDER[1]]
    f2.pop("surface_summaries", None)
    f2.pop("sign_pair_summaries", None)
    result["production_output"] = {
        "mode": "compact_fixed_summaries",
        "detailed_derived_records_written": False,
        "raw_response_ledgers_remain_sealed_authority": True,
        "all_registered_family_summaries_retained": True,
    }
    return result


def analyze_run(
    run_root: Path,
    scientific_open_receipt: Path,
    output: Path,
    *,
    bootstrap_replicates: int = 0,
) -> dict[str, Any]:
    resolved_run_root = run_root.expanduser().resolve(strict=True)
    resolved_output = output.expanduser().resolve()
    _require(
        not resolved_output.is_relative_to(resolved_run_root),
        "Analysis output must be outside the sealed run root",
    )
    _require(
        not resolved_output.exists(),
        f"Analysis output already exists: {resolved_output}",
    )
    registered_replicates = int(_config()["reporting"]["bootstrap_replicates"])
    _require(
        bootstrap_replicates in {0, registered_replicates},
        "Production execution permits point estimates or the registered bootstrap only",
    )
    item_rows, prototype_rows, random_rows, authorization = load_authorized_rows(
        run_root, scientific_open_receipt
    )
    result = analyze_rows(
        item_rows,
        prototype_rows,
        random_rows,
        bootstrap_replicates=bootstrap_replicates,
        require_frozen_grid=True,
    )
    result = compact_production_output(result)
    result["scientific_open_receipt"] = {
        "path": str(scientific_open_receipt.expanduser().resolve()),
        "sha256": hashlib.sha256(
            scientific_open_receipt.expanduser().resolve().read_bytes()
        ).hexdigest(),
    }
    result["value_open_authorization"] = authorization
    _write_json(resolved_output, result)
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--run-root", type=Path, required=True)
    result.add_argument("--scientific-open-receipt", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=0,
        help=(
            "0 writes point estimates with bootstrap explicitly pending; "
            "the only other accepted value is the registered 20000"
        ),
    )
    return result


def main() -> None:
    args = parser().parse_args()
    result = analyze_run(
        args.run_root,
        args.scientific_open_receipt,
        args.output,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(
        json.dumps(
            {
                "analysis_id": result["analysis_id"],
                "status": result["status"],
                "output": str(args.output.expanduser().resolve()),
                "family_order": result["family_order"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
