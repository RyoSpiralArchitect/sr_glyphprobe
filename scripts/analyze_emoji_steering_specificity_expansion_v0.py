#!/usr/bin/env python3
"""Open and analyze T14-X only after the complete six-role run validates."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
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

import emoji_steering_specificity_expansion_v0 as t14x  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-expansion-analysis-v0"
SOURCE_PROTOCOL_ID = t14x.PROTOCOL_ID
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_steering_specificity_expansion_analysis_v0.yaml")
FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_expansion_analysis_v0.json"
)
VALIDATION_DIRECTORY = Path(
    "validation/emoji_steering_specificity_expansion_analysis_v0"
)
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
ENDPOINTS = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
FAMILIES = (
    "X1_structured_vs_covariance_null",
    "X2_glyph_system_decomposition",
    "X3_prototype_source_form_specificity",
    "X4_item_source_form_specificity",
    "X5_depth_contrast",
    "X6_null_family_sensitivity",
    "X7_sign_orientation",
)
STATIC_FROZEN_ASSETS = (
    "configs/emoji_steering_specificity_expansion_analysis_v0.yaml",
    "docs/EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.md",
    "docs/EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.ja.md",
    "scripts/analyze_emoji_steering_specificity_expansion_v0.py",
    "tests/test_analyze_emoji_steering_specificity_expansion_v0.py",
    "validation/emoji_steering_specificity_expansion_analysis_v0/design_preflight.json",
)


class ExpansionAnalysisError(RuntimeError):
    """Raised when the T14-XA scientific-open contract is incomplete."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExpansionAnalysisError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@cache
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("analysis_id") == ANALYSIS_ID, "T14-XA analysis ID changed")
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "T14-XA source protocol changed",
    )
    return value


def _sha256(path: Path) -> str:
    return atlas._sha256(path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            _require(
                isinstance(value, dict), f"Invalid JSONL row: {path}:{line_number}"
            )
            rows.append(value)
    return rows


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"Refusing to overwrite T14-XA output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    stage = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    stage.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(stage, path)


def audit_design() -> dict[str, Any]:
    config = _config()
    observed = {}
    for binding in config["source_bindings"].values():
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T14-XA source binding missing: {path}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T14-XA source changed: {path}")
        observed[path.relative_to(_root()).as_posix()] = actual
    _require(
        tuple(str(value) for value in config["model_order"]) == t14x.model_roles(),
        "T14-XA model order changed",
    )
    _require(
        tuple(float(value) for value in config["depth_fractions"]) == (0.875, 1.0),
        "T14-XA depth order changed",
    )
    _require(
        tuple(str(value) for value in config["scalar_endpoints"]) == ENDPOINTS,
        "T14-XA endpoint order changed",
    )
    _require(
        tuple(str(row["id"]) for row in config["complete_families"]) == FAMILIES,
        "T14-XA complete-family order changed",
    )
    _require(
        int(config["target_summary"]["bootstrap_replicates"]) == 20_000,
        "T14-XA bootstrap count changed",
    )
    _require(
        config["reporting"]["all_complete_families_required"] is True
        and config["reporting"]["no_confirmatory_or_causal_verdict"] is True,
        "T14-XA reporting boundary changed",
    )
    return {
        "status": "pass",
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "model_cells": 6,
        "depth_cells": 2,
        "target_rows": 32,
        "response_rows_expected": 559_488,
        "complete_families": list(FAMILIES),
        "scalar_endpoints": list(ENDPOINTS),
        "bootstrap_replicates": 20_000,
        "source_bindings": observed,
        "source_run_audited": False,
        "scientific_response_values_read": False,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    value = audit_design()
    _write_json(output, value)
    return value


def freeze(output: Path) -> dict[str, Any]:
    preflight = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(preflight == audit_design(), "T14-XA preflight is stale")
    assets = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T14-XA frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "analysis_frozen_before_complete_run_scientific_open",
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "complete_families": list(FAMILIES),
        "model_roles": list(t14x.model_roles()),
        "response_values_read_at_freeze": 0,
        "partial_model_outputs_opened_at_freeze": 0,
    }
    _write_json(output, value)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("analysis_id") == ANALYSIS_ID, "T14-XA freeze changed")
    _require(
        value.get("status") == "analysis_frozen_before_complete_run_scientific_open",
        "T14-XA freeze incomplete",
    )
    for relative, expected in value["frozen_assets"].items():
        candidate = _root() / str(relative)
        _require(candidate.is_file(), f"T14-XA frozen asset missing: {relative}")
        _require(_sha256(candidate) == expected, f"T14-XA asset changed: {relative}")
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(value["frozen_assets"]),
        "scientific_response_values_read": False,
    }


def endpoint_value(row: Mapping[str, Any], endpoint: str) -> float:
    _require(endpoint in ENDPOINTS, f"Unknown T14-XA endpoint: {endpoint}")
    if endpoint == "entropy_change":
        value = float(row["intervened_entropy"]) - float(row["baseline_entropy"])
    elif endpoint == "argmax_flip_rate":
        _require(isinstance(row.get("argmax_flip"), bool), "argmax_flip changed")
        value = float(row["argmax_flip"])
    else:
        value = float(row[endpoint])
    _require(math.isfinite(value), f"Nonfinite T14-XA endpoint: {endpoint}")
    return value


def _stable_seed(base: int, namespace: str, key: Sequence[Any]) -> int:
    payload = json.dumps(
        [base, namespace, *key], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def target_summary(
    records: Sequence[Mapping[str, Any]], *, replicates: int, seed: int
) -> dict[str, Any]:
    _require(bool(records), "Cannot summarize an empty T14-XA cell")
    by_target: dict[str, float] = {}
    for row in records:
        target = str(row["target_id"])
        _require(target not in by_target, f"Duplicate target estimand: {target}")
        value = float(row["value"])
        _require(math.isfinite(value), "Nonfinite target estimand")
        by_target[target] = value
    values = np.asarray([by_target[key] for key in sorted(by_target)])
    _require(values.shape == (32,), "T14-XA target cell is incomplete")
    rng = np.random.default_rng(seed)
    samples = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 1000):
        stop = min(start + 1000, replicates)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        samples[start:stop] = np.median(values[indices], axis=1)
    low, high = np.quantile(samples, (0.025, 0.975))
    return {
        "target_rows": 32,
        "aggregate": "median",
        "median": float(np.median(values)),
        "mean": float(np.mean(values)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "bootstrap_95_percent_interval": [float(low), float(high)],
        "bootstrap_replicates": replicates,
    }


def _summarize_cells(
    records: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    *,
    namespace: str,
    replicates: int,
    seed: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        key = tuple(row[field] for field in fields)
        grouped[key].append(row)
    output = []
    for key, values in sorted(grouped.items()):
        output.append(
            {
                **dict(zip(fields, key, strict=True)),
                **target_summary(
                    values,
                    replicates=replicates,
                    seed=_stable_seed(seed, namespace, key),
                ),
            }
        )
    return output


def _load_rows(run_root: Path, kind: str) -> list[dict[str, Any]]:
    rows = []
    for role in t14x.model_roles():
        for site_index in t14x.SITE_INDICES:
            directory = t14x._output_directory(run_root, role, kind, site_index)
            t14x.validate_shard(directory, role, kind, site_index)
            for value in _read_jsonl(directory / "response_ledger.jsonl"):
                value["model"] = role
                rows.append(value)
    expected = {
        "item": 70_656 * 6,
        "prototype": 14_336 * 6,
        "null": 8_192 * 6,
    }[kind]
    _require(len(rows) == expected, f"T14-XA {kind} row count changed")
    return rows


def _target_median_records(
    grouped_values: Mapping[tuple[Any, ...], Sequence[float]],
    key_fields: Sequence[str],
    *,
    endpoint: str,
) -> list[dict[str, Any]]:
    output = []
    for key, values in grouped_values.items():
        _require(bool(values), "Empty T14-XA repeated-measure cell")
        output.append(
            {
                **dict(zip(key_fields, key, strict=True)),
                "value": _condition_reduce(values, endpoint),
            }
        )
    return output


def _condition_reduce(values: Sequence[float], endpoint: str) -> float:
    array = np.asarray(values, dtype=np.float64)
    _require(bool(len(array)) and bool(np.isfinite(array).all()), "Invalid repeat cell")
    if endpoint == "argmax_flip_rate":
        return float(np.mean(array))
    return float(np.median(array))


def _x1_x2(
    prototype_rows: Sequence[Mapping[str, Any]],
    null_rows: Sequence[Mapping[str, Any]],
    endpoint: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    structured: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    structured_system: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    null: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in prototype_rows:
        if row["view"] != "glyph":
            continue
        base = (row["model"], float(row["depth_fraction"]), str(row["target_id"]))
        value = endpoint_value(row, endpoint)
        structured[base].append(value)
        structured_system[(*base, str(row["glyph_system"]))].append(value)
    for row in null_rows:
        base = (row["model"], float(row["depth_fraction"]), str(row["target_id"]))
        null[base].append(endpoint_value(row, endpoint))
    _require(set(structured) == set(null), "T14-XA structured/null targets differ")
    x1 = []
    x2 = []
    systems = tuple(
        str(value) for value in t14x._config()["population"]["system_order"]
    )
    for base in sorted(structured):
        _require(len(structured[base]) == 48, "T14-XA structured roster changed")
        _require(len(null[base]) == 128, "T14-XA null roster changed")
        null_median = _condition_reduce(null[base], endpoint)
        common = {
            "model": base[0],
            "depth_fraction": base[1],
            "target_id": base[2],
            "endpoint": endpoint,
        }
        x1.append(
            {
                **common,
                "value": _condition_reduce(structured[base], endpoint) - null_median,
            }
        )
        for system in systems:
            values = structured_system[(*base, system)]
            _require(len(values) == 8, "T14-XA system prototype roster changed")
            x2.append(
                {
                    **common,
                    "glyph_system": system,
                    "value": _condition_reduce(values, endpoint) - null_median,
                }
            )
    return x1, x2


def _x3(rows: Sequence[Mapping[str, Any]], endpoint: str) -> list[dict[str, Any]]:
    paired: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in rows:
        key = (
            row["model"],
            float(row["depth_fraction"]),
            str(row["glyph_system"]),
            str(row["target_id"]),
            int(row["held_out_wrapper_index"]),
            int(row["sign"]),
        )
        view = str(row["view"])
        _require(view not in paired[key], "Duplicate T14-XA prototype view")
        paired[key][view] = endpoint_value(row, endpoint)
    target_values: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for key, views in paired.items():
        _require("glyph" in views, "T14-XA glyph prototype missing")
        for other, value in views.items():
            if other == "glyph":
                continue
            target_key = (*key[:4], f"glyph_minus_{other}", endpoint)
            target_values[target_key].append(views["glyph"] - value)
    output = _target_median_records(
        target_values,
        (
            "model",
            "depth_fraction",
            "glyph_system",
            "target_id",
            "contrast",
            "endpoint",
        ),
        endpoint=endpoint,
    )
    _require(
        all(len(values) == 8 for values in target_values.values()),
        "T14-XA prototype pairing changed",
    )
    return output


def _x4(rows: Sequence[Mapping[str, Any]], endpoint: str) -> list[dict[str, Any]]:
    paired: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for row in rows:
        key = (
            row["model"],
            float(row["depth_fraction"]),
            str(row["glyph_system"]),
            int(row["item_index"]),
            str(row["target_id"]),
            int(row["sign"]),
        )
        view = str(row["view"])
        _require(view not in paired[key], "Duplicate T14-XA item view")
        paired[key][view] = endpoint_value(row, endpoint)
    target_values: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for key, views in paired.items():
        _require(
            "glyph" in views and "unicode_name" in views, "T14-XA item pair missing"
        )
        for other in ("unicode_name", "decomposed_form"):
            if other not in views:
                continue
            target_key = (
                key[0],
                key[1],
                key[2],
                key[4],
                f"glyph_minus_{other}",
                endpoint,
            )
            target_values[target_key].append(views["glyph"] - views[other])
    return _target_median_records(
        target_values,
        (
            "model",
            "depth_fraction",
            "glyph_system",
            "target_id",
            "contrast",
            "endpoint",
        ),
        endpoint=endpoint,
    )


def _x5(x1: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    paired: dict[tuple[Any, ...], dict[float, float]] = defaultdict(dict)
    for row in x1:
        key = (row["model"], row["target_id"], row["endpoint"])
        paired[key][float(row["depth_fraction"])] = float(row["value"])
    output = []
    for key, values in paired.items():
        _require(set(values) == {0.875, 1.0}, "T14-XA depth pair changed")
        output.append(
            {
                "model": key[0],
                "target_id": key[1],
                "endpoint": key[2],
                "contrast": "depth_0p875_minus_1p0",
                "value": values[0.875] - values[1.0],
            }
        )
    return output


def _x6(rows: Sequence[Mapping[str, Any]], endpoint: str) -> list[dict[str, Any]]:
    values: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in rows:
        key = (
            row["model"],
            float(row["depth_fraction"]),
            str(row["target_id"]),
            str(row["null_family"]),
        )
        values[key].append(endpoint_value(row, endpoint))
    paired: dict[tuple[Any, ...], dict[str, float]] = defaultdict(dict)
    for key, repeats in values.items():
        _require(len(repeats) == 64, "T14-XA null-family roster changed")
        paired[key[:3]][key[3]] = _condition_reduce(repeats, endpoint)
    output = []
    for key, families in paired.items():
        _require(set(families) == set(t14x.FAMILIES), "T14-XA null families changed")
        output.append(
            {
                "model": key[0],
                "depth_fraction": key[1],
                "target_id": key[2],
                "endpoint": endpoint,
                "contrast": "gaussian_minus_rademacher",
                "value": families["centered_item_residual_gaussian"]
                - families["centered_item_residual_rademacher"],
            }
        )
    return output


def _x7(rows: Sequence[Mapping[str, Any]], endpoint: str) -> list[dict[str, Any]]:
    values: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for row in rows:
        if row["view"] != "glyph":
            continue
        key = (
            row["model"],
            float(row["depth_fraction"]),
            str(row["target_id"]),
            int(row["sign"]),
        )
        values[key].append(endpoint_value(row, endpoint))
    paired: dict[tuple[Any, ...], dict[int, float]] = defaultdict(dict)
    for key, repeats in values.items():
        _require(len(repeats) == 24, "T14-XA sign roster changed")
        paired[key[:3]][key[3]] = _condition_reduce(repeats, endpoint)
    output = []
    for key, signs in paired.items():
        _require(set(signs) == {-1, 1}, "T14-XA sign pair changed")
        output.append(
            {
                "model": key[0],
                "depth_fraction": key[1],
                "target_id": key[2],
                "endpoint": endpoint,
                "contrast": "positive_minus_negative_orientation",
                "value": signs[1] - signs[-1],
            }
        )
    return output


def analyze_rows(
    item_rows: Sequence[Mapping[str, Any]],
    prototype_rows: Sequence[Mapping[str, Any]],
    null_rows: Sequence[Mapping[str, Any]],
    *,
    replicates: int,
    seed: int,
) -> dict[str, Any]:
    family_records: dict[str, list[dict[str, Any]]] = {
        family: [] for family in FAMILIES
    }
    for endpoint in ENDPOINTS:
        x1, x2 = _x1_x2(prototype_rows, null_rows, endpoint)
        family_records[FAMILIES[0]].extend(x1)
        family_records[FAMILIES[1]].extend(x2)
        family_records[FAMILIES[2]].extend(_x3(prototype_rows, endpoint))
        family_records[FAMILIES[3]].extend(_x4(item_rows, endpoint))
        family_records[FAMILIES[5]].extend(_x6(null_rows, endpoint))
        family_records[FAMILIES[6]].extend(_x7(prototype_rows, endpoint))
    family_records[FAMILIES[4]] = _x5(family_records[FAMILIES[0]])
    fields = {
        FAMILIES[0]: ("model", "depth_fraction", "endpoint"),
        FAMILIES[1]: ("model", "depth_fraction", "glyph_system", "endpoint"),
        FAMILIES[2]: (
            "model",
            "depth_fraction",
            "glyph_system",
            "contrast",
            "endpoint",
        ),
        FAMILIES[3]: (
            "model",
            "depth_fraction",
            "glyph_system",
            "contrast",
            "endpoint",
        ),
        FAMILIES[4]: ("model", "contrast", "endpoint"),
        FAMILIES[5]: ("model", "depth_fraction", "contrast", "endpoint"),
        FAMILIES[6]: ("model", "depth_fraction", "contrast", "endpoint"),
    }
    result = {}
    for family in FAMILIES:
        result[family] = {
            "status": "exploratory_complete_family",
            "target_level_rows": len(family_records[family]),
            "summaries": _summarize_cells(
                family_records[family],
                fields[family],
                namespace=family,
                replicates=replicates,
                seed=seed,
            ),
        }
    return result


def analyze_run(run_root: Path, output: Path) -> dict[str, Any]:
    freeze_receipt = audit_freeze()
    run_receipt = t14x.audit_run(run_root)
    _require(
        run_receipt.get("status") == "complete_closed_to_adaptive_selection"
        and int(run_receipt.get("roles_complete")) == 6
        and int(run_receipt.get("response_rows")) == 559_488,
        "T14-XA complete-run gate failed",
    )
    item_rows = _load_rows(run_root, "item")
    prototype_rows = _load_rows(run_root, "prototype")
    null_rows = _load_rows(run_root, "null")
    summary = _config()["target_summary"]
    families = analyze_rows(
        item_rows,
        prototype_rows,
        null_rows,
        replicates=int(summary["bootstrap_replicates"]),
        seed=int(summary["bootstrap_seed"]),
    )
    value = {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "all_complete_families_exploratory_analysis_complete",
        "claim_boundary": _config()["claim_boundary"],
        "analysis_freeze_manifest_sha256": freeze_receipt["manifest_sha256"],
        "source_run_audit": run_receipt,
        "scientific_open_order": [
            "analysis_freeze_audit",
            "six_role_source_run_audit",
            "scalar_ledger_open",
            "all_complete_family_derivation",
        ],
        "families": families,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output, value)
    return {
        "status": value["status"],
        "complete_families": len(families),
        "output_sha256": _sha256(output),
        "confirmatory_status": False,
        "causal_claim_authorized": False,
    }


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    preflight = commands.add_parser("write-design-preflight")
    preflight.add_argument(
        "--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH
    )
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    commands.add_parser("audit-freeze")
    run = commands.add_parser("analyze-run")
    run.add_argument("--run-root", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "write-design-preflight":
        result = write_design_preflight(args.output)
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    else:
        result = analyze_run(args.run_root, args.output)
    _print(result)


if __name__ == "__main__":
    main()
