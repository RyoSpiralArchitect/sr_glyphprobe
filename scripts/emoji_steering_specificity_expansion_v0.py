#!/usr/bin/env python3
"""Freeze and execute the T14-X late-depth exploratory expansion.

The executable deliberately contains no scientific aggregation or model/site
selection. It reuses the hash-bound T13 source bank, writes external-only
response shards, and stays closed to scientific interpretation until all six
roles validate.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import emoji_steering_specificity_harvest_v0 as t13  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-expansion-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_steering_specificity_expansion_v0.yaml")
FREEZE_PATH = Path("data/manifests/emoji_steering_specificity_expansion_v0.json")
VALIDATION_DIRECTORY = Path("validation/emoji_steering_specificity_expansion_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
SITE_INDICES = (6, 7)
FAMILIES = (
    "centered_item_residual_gaussian",
    "centered_item_residual_rademacher",
)
STATIC_FROZEN_ASSETS = (
    "configs/emoji_steering_specificity_expansion_v0.yaml",
    "docs/EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md",
    "docs/EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md",
    "scripts/emoji_steering_specificity_expansion_v0.py",
    "tests/test_emoji_steering_specificity_expansion_v0.py",
    "validation/emoji_steering_specificity_expansion_v0/design_preflight.json",
)


class ExpansionError(RuntimeError):
    """Raised when the T14-X execution contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExpansionError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@cache
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T14-X protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    return atlas._sha256(path)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@cache
def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


@cache
def targets() -> list[dict[str, str]]:
    return t13.targets()


@cache
def population() -> list[dict[str, Any]]:
    return t13.population()


@cache
def _source_closeout() -> dict[str, Any]:
    binding = _config()["source_bindings"]["t13_scientific_open_closeout"]
    path = _root() / str(binding["path"])
    _require(path.is_file(), "T14-X T13 closeout is missing")
    _require(_sha256(path) == str(binding["sha256"]), "T14-X closeout changed")
    value = _read_json(path)
    _require(value.get("scientific_open_authorized") is True, "T13 is not open")
    _require(value.get("roles_complete") == 9, "T13 role closeout is incomplete")
    _require(
        value.get("run_root")
        == _config()["source_bindings"]["source_run_binding"]["expected_run_root"],
        "T13 source run root binding changed",
    )
    return value


def _expected_counts() -> dict[str, int]:
    target_count = len(targets())
    item_directions = 0
    for item in population():
        item_directions += sum(
            view in t13.available_views(item) for view in t13.ITEM_VIEW_ORDER
        )
    prototype_count = sum(
        3 if system == "atomic_anchor" else 5
        for system in _config()["population"]["system_order"]
    )
    sites = len(SITE_INDICES)
    signs = len(_config()["intervention"]["signs"])
    folds = int(_config()["grids"]["wrapper_holdout_prototype"]["folds"])
    seeds = int(
        _config()["grids"]["signed_source_covariance_null"][
            "seeds_per_family_per_fold_per_depth"
        ]
    )
    item_rows = item_directions * sites * signs * target_count
    prototype_rows = prototype_count * folds * sites * signs * target_count
    null_rows = len(FAMILIES) * seeds * folds * sites * signs * target_count
    zero_rows = sites * target_count
    return {
        "item_directions": item_directions,
        "system_view_prototypes": prototype_count,
        "item_rows": item_rows,
        "prototype_rows": prototype_rows,
        "null_rows": null_rows,
        "zero_rows": zero_rows,
        "rows_per_model": item_rows + prototype_rows + null_rows + zero_rows,
        "rows_total": (item_rows + prototype_rows + null_rows + zero_rows)
        * len(model_roles()),
    }


def audit_design() -> dict[str, Any]:
    config = _config()
    observed: dict[str, str] = {}
    for key in (
        "t13_harvest_config",
        "t13_harvest_freeze",
        "t13_scientific_open_closeout",
        "public_targets",
    ):
        binding = config["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T14-X bound input is missing: {key}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T14-X input changed: {key}")
        observed[path.relative_to(_root()).as_posix()] = actual
    _source_closeout()
    _require(len(targets()) == 32, "T14-X public target count changed")
    _require(len(population()) == 192, "T14-X source population changed")
    _require(set(model_roles()).issubset(t13.model_roles()), "Unknown T14-X role")
    _require(
        len(model_roles()) == 6 and len(set(model_roles())) == 6, "Role count changed"
    )
    _require(
        tuple(float(value) for value in config["intervention"]["depth_fractions"])
        == (0.875, 1.0),
        "T14-X depth fractions changed",
    )
    t13_storage = t13._config()["pilot"]["response_storage"]
    _require(
        int(config["storage"]["top_positive_and_negative_logit_deltas"])
        == int(t13_storage["top_positive_and_negative_logit_deltas"]),
        "T14-X/T13 top-k storage contract differs",
    )
    _require(
        int(config["storage"]["countsketch_dimension"])
        == int(t13_storage["countsketch_dimension"]),
        "T14-X/T13 CountSketch dimension differs",
    )
    _require(
        int(config["storage"]["countsketch_seed"])
        == int(t13_storage["countsketch_seed"]),
        "T14-X/T13 CountSketch seed differs",
    )
    for role in model_roles():
        indices = t13.layer_indices(role)
        _require(indices[6] < indices[7], f"T14-X late sites collapsed: {role}")
    counts = _expected_counts()
    for key, config_key in (
        ("item_rows", "item"),
        ("prototype_rows", "wrapper_holdout_prototype"),
        ("null_rows", "signed_source_covariance_null"),
        ("zero_rows", "zero"),
    ):
        _require(
            counts[key] == int(config["grids"][config_key]["rows_per_model"]),
            f"T14-X count changed: {key}",
        )
    _require(
        counts["rows_per_model"] == int(config["grids"]["expected_rows_per_model"]),
        "T14-X per-model total changed",
    )
    _require(
        counts["rows_total"] == int(config["grids"]["expected_rows_total"]),
        "T14-X global total changed",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "model_roles": list(model_roles()),
        "model_cells": len(model_roles()),
        "source_items": len(population()),
        "public_targets": len(targets()),
        "late_depth_sites": list(SITE_INDICES),
        **counts,
        "source_bindings": observed,
        "model_weights_loaded": False,
        "model_forward_sequences": 0,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "protected_or_future_target_banks_opened": 0,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    value = audit_design()
    _write_json(output, value)
    return value


def freeze(output: Path) -> dict[str, Any]:
    preflight = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(preflight == audit_design(), "T14-X design preflight is stale")
    assets: dict[str, str] = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T14-X frozen asset is missing: {relative}")
        assets[relative] = _sha256(path)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t14x_model_forward",
        "experiment_role": _config()["experiment_role"],
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "source_run_root": _source_closeout()["run_root"],
        "source_run_binding_root_sha256": _source_closeout()["run_binding_root_sha256"],
        "supersedes_zero_forward_manifest_sha256": _config()["freeze_history"][
            "superseded_zero_forward_manifest_sha256"
        ],
        "model_forwards_between_freezes": _config()["freeze_history"][
            "t14x_model_forwards_between_freezes"
        ],
        "model_order": list(model_roles()),
        "expected_rows_per_model": _expected_counts()["rows_per_model"],
        "expected_rows_total": _expected_counts()["rows_total"],
        "model_forward_sequences_at_freeze": 0,
        "intervention_sequences_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
        "protected_or_future_target_banks_opened_at_freeze": 0,
    }
    _write_json(output, manifest)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T14-X freeze mismatch")
    _require(
        value.get("status") == "freeze_complete_before_any_t14x_model_forward",
        "T14-X freeze is incomplete",
    )
    for relative, expected in value["frozen_assets"].items():
        candidate = _root() / str(relative)
        _require(candidate.is_file(), f"T14-X frozen asset missing: {relative}")
        _require(
            _sha256(candidate) == str(expected), f"T14-X asset changed: {relative}"
        )
    _require(value["model_order"] == list(model_roles()), "T14-X role order changed")
    _require(
        int(value["expected_rows_total"]) == _expected_counts()["rows_total"],
        "T14-X frozen row total changed",
    )
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(value["frozen_assets"]),
    }


def _validate_source_role(source_run_root: Path, role: str) -> dict[str, Any]:
    expected = Path(_source_closeout()["run_root"])
    _require(source_run_root.resolve() == expected, "T14-X source run root changed")
    t13.validate_baseline(source_run_root / role / "baseline", role)
    wrapper_vectors = 0
    direction_vectors = 0
    for shard_index in range(12):
        directory = source_run_root / role / "source" / f"shard-{shard_index:04d}"
        t13.validate_source_shard(directory, role, shard_index)
        receipt = _read_json(directory / "receipt.json")
        wrapper_vectors += int(receipt["wrapper_delta_vectors"])
        direction_vectors += int(receipt["mean_direction_vectors"])
    _require(wrapper_vectors == 29184, "T14-X wrapper-vector source count changed")
    _require(direction_vectors == 7296, "T14-X direction source count changed")
    return {
        "status": "pass",
        "model_role": role,
        "wrapper_delta_vectors": wrapper_vectors,
        "mean_direction_vectors": direction_vectors,
    }


def _load_wrapper_deltas(
    source_run_root: Path, role: str
) -> tuple[np.ndarray, np.ndarray]:
    arrays: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    for shard_index in range(12):
        directory = source_run_root / role / "source" / f"shard-{shard_index:04d}"
        t13.validate_source_shard(directory, role, shard_index)
        arrays.append(np.load(directory / "wrapper_deltas.npy", allow_pickle=False))
        masks.append(np.load(directory / "view_mask.npy", allow_pickle=False))
    value = np.concatenate(arrays, axis=0)
    mask = np.concatenate(masks, axis=0)
    _require(value.shape[:4] == (192, 5, 4, 8), "T14-X wrapper bank changed")
    _require(mask.shape == (192, 5), "T14-X view mask changed")
    return value, mask


def _leave_one_wrapper_out(wrapper_deltas: np.ndarray, held_out: int) -> np.ndarray:
    _require(0 <= held_out < 4, "T14-X wrapper fold is invalid")
    keep = [index for index in range(4) if index != held_out]
    return np.mean(wrapper_deltas[:, :, keep, :, :], axis=2, dtype=np.float64).astype(
        np.float32
    )


def _unit_rows(value: np.ndarray) -> np.ndarray:
    rms = t13._rms_rows(value)
    _require(bool(np.isfinite(rms).all()) and bool((rms > 0).all()), "Invalid RMS")
    return (value / rms[:, None]).astype(np.float32)


def _prototype_map(
    loo: np.ndarray,
    mask: np.ndarray,
    site_index: int,
) -> dict[tuple[str, str], np.ndarray]:
    rows = population()
    result: dict[tuple[str, str], np.ndarray] = {}
    for system in _config()["population"]["system_order"]:
        item_indices = [
            index for index, item in enumerate(rows) if item["glyph_system"] == system
        ]
        for view in t13.VIEW_ORDER:
            view_index = t13.VIEW_ORDER.index(view)
            eligible = [
                index for index in item_indices if bool(mask[index, view_index])
            ]
            if not eligible:
                continue
            values = np.stack(
                [loo[index, view_index, site_index] for index in eligible], axis=0
            )
            prototype = np.mean(_unit_rows(values), axis=0, dtype=np.float64).astype(
                np.float32
            )
            _require(
                bool(np.isfinite(prototype).all())
                and float(t13._rms_rows(prototype[None, :])[0]) > 0,
                "T14-X prototype is invalid",
            )
            result[(str(system), view)] = prototype
    _require(len(result) == 28, "T14-X prototype roster changed")
    return result


def _residual_matrix(
    loo: np.ndarray,
    mask: np.ndarray,
    site_index: int,
    prototypes: Mapping[tuple[str, str], np.ndarray],
) -> np.ndarray:
    residuals: list[np.ndarray] = []
    for item_index, item in enumerate(population()):
        system = str(item["glyph_system"])
        for view in t13.VIEW_ORDER:
            view_index = t13.VIEW_ORDER.index(view)
            if not bool(mask[item_index, view_index]):
                continue
            item_vector = loo[item_index, view_index, site_index]
            item_unit = _unit_rows(item_vector[None, :])[0]
            prototype_unit = _unit_rows(prototypes[(system, view)][None, :])[0]
            residual = item_unit - prototype_unit
            if float(t13._rms_rows(residual[None, :])[0]) > 1e-8:
                residuals.append(residual.astype(np.float32))
    matrix = np.stack(residuals, axis=0)
    matrix -= np.mean(matrix, axis=0, dtype=np.float64).astype(np.float32)
    finite_rms = t13._rms_rows(matrix)
    matrix = matrix[finite_rms > 1e-8]
    _require(len(matrix) >= 500, "T14-X residual population is too small")
    _require(bool(np.isfinite(matrix).all()), "T14-X residual matrix is nonfinite")
    return matrix


def _null_seed(
    role: str,
    site_index: int,
    fold: int,
    family: str,
    seed_index: int,
) -> int:
    payload = (
        f"glyphprobe-t14x-v0:{role}:{site_index}:{fold}:{family}:{seed_index}"
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _null_direction(matrix: np.ndarray, family: str, seed: int) -> np.ndarray:
    _require(family in FAMILIES, "T14-X null family is unknown")
    rng = np.random.default_rng(seed)
    if family == "centered_item_residual_gaussian":
        weights = rng.standard_normal(len(matrix))
    else:
        weights = rng.choice(np.asarray([-1.0, 1.0]), size=len(matrix))
    value = (weights @ matrix) / math.sqrt(len(matrix))
    result = _unit_rows(np.asarray(value, dtype=np.float32)[None, :])[0]
    _require(bool(np.isfinite(result).all()), "T14-X null direction is nonfinite")
    return result


def _output_directory(
    output_root: Path,
    role: str,
    kind: str,
    site_index: int,
) -> Path:
    return output_root / role / kind / f"site-{site_index:02d}"


def _yield_if_contended(output_root: Path, role: str, boundary: str) -> None:
    pids = t13._foreign_gpu_pids()
    if not pids:
        return
    receipt = output_root / role / "yield_receipt.json"
    if not receipt.exists():
        _write_json(
            receipt,
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "status": "yielded_before_new_shard_for_foreign_gpu_contention",
                "model_role": role,
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(
        int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"])
    )


def _write_shard(
    *,
    final: Path,
    role: str,
    kind: str,
    site_index: int,
    rows: list[dict[str, Any]],
    positive_ids: list[np.ndarray],
    positive_values: list[np.ndarray],
    negative_ids: list[np.ndarray],
    negative_values: list[np.ndarray],
    sketches: list[np.ndarray],
    invocations: int,
    started: float,
) -> None:
    stage, final = t13._atomic_directory(final)
    t13._write_jsonl(stage / "response_ledger.jsonl", rows)
    arrays = {
        "top_positive_ids.npy": np.concatenate(positive_ids, axis=0),
        "top_positive_values.npy": np.concatenate(positive_values, axis=0),
        "top_negative_ids.npy": np.concatenate(negative_ids, axis=0),
        "top_negative_values.npy": np.concatenate(negative_values, axis=0),
        "countsketch.npy": np.concatenate(sketches, axis=0),
    }
    for name, value in arrays.items():
        _require(value.shape[0] == len(rows), f"T14-X shard row mismatch: {name}")
        _require(bool(np.isfinite(value).all()), f"T14-X shard nonfinite: {name}")
        np.save(stage / name, value, allow_pickle=False)
    files = t13._directory_file_bindings(stage, ("response_ledger.jsonl", *arrays))
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "response_shard_complete",
        "model_role": role,
        "shard_kind": kind,
        "site_index": site_index,
        "depth_fraction": float(
            _config()["intervention"]["depth_fractions"][SITE_INDICES.index(site_index)]
        ),
        "response_rows": len(rows),
        "intervention_sequences": len(rows),
        "baseline_guard_sequences": invocations,
        "batched_model_invocations": invocations,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    t13._seal_directory(stage, final, receipt)


def _expected_shard_rows(kind: str) -> int:
    counts = _expected_counts()
    mapping = {
        "item": counts["item_rows"] // len(SITE_INDICES),
        "prototype": counts["prototype_rows"] // len(SITE_INDICES),
        "null": counts["null_rows"] // len(SITE_INDICES),
        "zero": counts["zero_rows"] // len(SITE_INDICES),
    }
    _require(kind in mapping, "T14-X shard kind is unknown")
    return mapping[kind]


def validate_shard(
    directory: Path, role: str, kind: str, site_index: int
) -> dict[str, Any]:
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "T14-X receipt mismatch")
    _require(receipt.get("model_role") == role, "T14-X role receipt mismatch")
    _require(receipt.get("shard_kind") == kind, "T14-X shard kind mismatch")
    _require(int(receipt.get("site_index")) == site_index, "T14-X site mismatch")
    rows = int(receipt["response_rows"])
    _require(rows == _expected_shard_rows(kind), "T14-X shard row count changed")
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(path.is_file(), f"T14-X shard file missing: {name}")
        _require(_sha256(path) == str(binding["sha256"]), f"T14-X file changed: {name}")
    top_k = int(_config()["storage"]["top_positive_and_negative_logit_deltas"])
    for name in (
        "top_positive_ids.npy",
        "top_positive_values.npy",
        "top_negative_ids.npy",
        "top_negative_values.npy",
    ):
        value = np.load(directory / name, mmap_mode="r", allow_pickle=False)
        _require(value.shape == (rows, top_k), f"T14-X top-k shape changed: {name}")
        _require(bool(np.isfinite(value).all()), f"T14-X top-k nonfinite: {name}")
    sketch = np.load(directory / "countsketch.npy", mmap_mode="r", allow_pickle=False)
    _require(
        sketch.shape == (rows, int(_config()["storage"]["countsketch_dimension"])),
        "T14-X CountSketch shape changed",
    )
    _require(bool(np.isfinite(sketch).all()), "T14-X CountSketch is nonfinite")
    with (directory / "response_ledger.jsonl").open("r", encoding="utf-8") as handle:
        ledger_rows = sum(1 for line in handle if line.strip())
    _require(ledger_rows == rows, "T14-X ledger row count changed")
    return {"status": "pass", "model_role": role, "kind": kind, "rows": rows}


def _execute_groups(
    *,
    role: str,
    kind: str,
    site_index: int,
    output_root: Path,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    groups: Sequence[tuple[int, int, list[dict[str, Any]], np.ndarray]],
) -> Path:
    final = _output_directory(output_root, role, kind, site_index)
    if final.exists():
        validate_shard(final, role, kind, site_index)
        return final
    _yield_if_contended(output_root, role, f"before_{kind}_site_{site_index:02d}")
    started = time.perf_counter()
    result = t13._run_condition_groups(
        role=role,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        groups=groups,
    )
    rows, pos_ids, pos_values, neg_ids, neg_values, sketches, invocations = result
    _write_shard(
        final=final,
        role=role,
        kind=kind,
        site_index=site_index,
        rows=rows,
        positive_ids=pos_ids,
        positive_values=pos_values,
        negative_ids=neg_ids,
        negative_values=neg_values,
        sketches=sketches,
        invocations=invocations,
        started=started,
    )
    validate_shard(final, role, kind, site_index)
    return final


def _item_groups(
    role: str,
    site_index: int,
    directions: np.ndarray,
    mask: np.ndarray,
    target_rms: np.ndarray,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    magnitude = float(_config()["intervention"]["magnitude"])
    block_index = int(t13.layer_indices(role)[site_index])
    depth_fraction = float(
        _config()["intervention"]["depth_fractions"][SITE_INDICES.index(site_index)]
    )
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        raw: list[np.ndarray] = []
        signs: list[int] = []
        for item_index, item in enumerate(population()):
            for view in t13.ITEM_VIEW_ORDER:
                view_index = t13.VIEW_ORDER.index(view)
                if not bool(mask[item_index, view_index]):
                    continue
                for sign in (-1, 1):
                    metadata.append(
                        {
                            "condition_kind": "item_source_form_late_depth",
                            "item_index": item_index,
                            "depth_index": int(item["depth_index"]),
                            "codepoint": str(item["codepoint"]),
                            "glyph_system": str(item["glyph_system"]),
                            "view": view,
                            "site_index": site_index,
                            "block_index": block_index,
                            "depth_fraction": depth_fraction,
                            "magnitude": magnitude,
                            "sign": sign,
                            "target_index": target_index,
                            "target_id": target["id"],
                            "target_group": target["group"],
                        }
                    )
                    raw.append(directions[item_index, view_index, site_index])
                    signs.append(sign)
        unit = _unit_rows(np.stack(raw, axis=0))
        scaled = unit * np.asarray(signs, dtype=np.float32)[:, None] * magnitude
        scaled *= float(target_rms[target_index, site_index])
        groups.append((site_index, target_index, metadata, scaled.astype(np.float32)))
    return groups


def _prototype_groups(
    role: str,
    site_index: int,
    wrapper_deltas: np.ndarray,
    mask: np.ndarray,
    target_rms: np.ndarray,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    magnitude = float(_config()["intervention"]["magnitude"])
    block_index = int(t13.layer_indices(role)[site_index])
    depth_fraction = float(
        _config()["intervention"]["depth_fractions"][SITE_INDICES.index(site_index)]
    )
    fold_maps = []
    for fold in range(4):
        loo = _leave_one_wrapper_out(wrapper_deltas, fold)
        fold_maps.append(_prototype_map(loo, mask, site_index))
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        raw: list[np.ndarray] = []
        signs: list[int] = []
        for fold, prototypes in enumerate(fold_maps):
            for (system, view), vector in prototypes.items():
                for sign in (-1, 1):
                    metadata.append(
                        {
                            "condition_kind": "wrapper_holdout_system_view_prototype",
                            "glyph_system": system,
                            "view": view,
                            "held_out_wrapper_index": fold,
                            "site_index": site_index,
                            "block_index": block_index,
                            "depth_fraction": depth_fraction,
                            "magnitude": magnitude,
                            "sign": sign,
                            "target_index": target_index,
                            "target_id": target["id"],
                            "target_group": target["group"],
                        }
                    )
                    raw.append(vector)
                    signs.append(sign)
        unit = _unit_rows(np.stack(raw, axis=0))
        scaled = unit * np.asarray(signs, dtype=np.float32)[:, None] * magnitude
        scaled *= float(target_rms[target_index, site_index])
        groups.append((site_index, target_index, metadata, scaled.astype(np.float32)))
    return groups


def _null_groups(
    role: str,
    site_index: int,
    wrapper_deltas: np.ndarray,
    mask: np.ndarray,
    target_rms: np.ndarray,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    magnitude = float(_config()["intervention"]["magnitude"])
    block_index = int(t13.layer_indices(role)[site_index])
    depth_fraction = float(
        _config()["intervention"]["depth_fractions"][SITE_INDICES.index(site_index)]
    )
    seeds_per_family = int(
        _config()["grids"]["signed_source_covariance_null"][
            "seeds_per_family_per_fold_per_depth"
        ]
    )
    null_rows: list[tuple[int, str, int, int, np.ndarray]] = []
    for fold in range(4):
        loo = _leave_one_wrapper_out(wrapper_deltas, fold)
        prototypes = _prototype_map(loo, mask, site_index)
        residuals = _residual_matrix(loo, mask, site_index, prototypes)
        for family in FAMILIES:
            for seed_index in range(seeds_per_family):
                seed = _null_seed(role, site_index, fold, family, seed_index)
                vector = _null_direction(residuals, family, seed)
                null_rows.append((fold, family, seed_index, seed, vector))
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        raw: list[np.ndarray] = []
        signs: list[int] = []
        for fold, family, seed_index, seed, vector in null_rows:
            for sign in (-1, 1):
                metadata.append(
                    {
                        "condition_kind": "signed_source_covariance_null",
                        "null_family": family,
                        "held_out_wrapper_index": fold,
                        "seed_index": seed_index,
                        "seed": seed,
                        "site_index": site_index,
                        "block_index": block_index,
                        "depth_fraction": depth_fraction,
                        "magnitude": magnitude,
                        "sign": sign,
                        "target_index": target_index,
                        "target_id": target["id"],
                        "target_group": target["group"],
                    }
                )
                raw.append(vector)
                signs.append(sign)
        unit = _unit_rows(np.stack(raw, axis=0))
        scaled = unit * np.asarray(signs, dtype=np.float32)[:, None] * magnitude
        scaled *= float(target_rms[target_index, site_index])
        groups.append((site_index, target_index, metadata, scaled.astype(np.float32)))
    return groups


def _zero_groups(
    role: str,
    site_index: int,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    width = int(t10._model_spec(role)["expected_model_dim"])
    block_index = int(t13.layer_indices(role)[site_index])
    depth_fraction = float(
        _config()["intervention"]["depth_fractions"][SITE_INDICES.index(site_index)]
    )
    groups = []
    for target_index, target in enumerate(targets()):
        metadata = [
            {
                "condition_kind": "zero_direction",
                "site_index": site_index,
                "block_index": block_index,
                "depth_fraction": depth_fraction,
                "magnitude": 0.0,
                "sign": 0,
                "target_index": target_index,
                "target_id": target["id"],
                "target_group": target["group"],
            }
        ]
        groups.append(
            (site_index, target_index, metadata, np.zeros((1, width), dtype=np.float32))
        )
    return groups


def _validate_zero_values(directory: Path) -> dict[str, float]:
    max_js = 0.0
    with (directory / "response_ledger.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            _require(row["kl_baseline_to_intervened"] == 0.0, "Zero-hook KL changed")
            _require(row["total_variation"] == 0.0, "Zero-hook TV changed")
            _require(row["logit_delta_rms"] == 0.0, "Zero-hook RMS changed")
            _require(
                row["baseline_entropy"] == row["intervened_entropy"],
                "Zero-hook entropy changed",
            )
            _require(
                row["baseline_argmax_id"] == row["intervened_argmax_id"],
                "Zero-hook argmax changed",
            )
            max_js = max(max_js, abs(float(row["js_divergence"])))
    bound = 8.0 * float(np.finfo(np.float32).eps)
    _require(max_js <= bound, "Zero-hook JS exceeds the frozen float32 bound")
    sketch = np.load(directory / "countsketch.npy", allow_pickle=False)
    _require(bool((sketch == 0).all()), "Zero-hook CountSketch changed")
    return {"maximum_absolute_js": max_js, "js_bound": bound}


def run_role(
    *,
    role: str,
    output_root: Path,
    source_run_root: Path,
    preflight_directory: Path,
    model_path: Path | None,
) -> dict[str, Any]:
    audit_freeze()
    _require(role in model_roles(), f"Unknown T14-X role: {role}")
    summary_path = output_root / role / "summary.json"
    if summary_path.is_file():
        return validate_role(role, output_root)
    _validate_source_role(source_run_root, role)
    _yield_if_contended(output_root, role, "before_model_load")
    snapshot = (
        model_path if model_path is not None else t13.t11._locate_local_snapshot(role)
    )
    torch, tokenizer, model, model_receipt = t13._load_model(
        role, snapshot, preflight_directory
    )
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    directions, direction_mask = t13._load_source_directions(source_run_root, role)
    wrapper_deltas, wrapper_mask = _load_wrapper_deltas(source_run_root, role)
    _require(
        np.array_equal(direction_mask, wrapper_mask), "T14-X source masks disagree"
    )
    target_rms = t13._target_rms(source_run_root / role / "baseline")
    started = time.perf_counter()
    rows_total = 0
    zero_bounds: dict[str, dict[str, float]] = {}
    for site_index in SITE_INDICES:
        zero = _execute_groups(
            role=role,
            kind="zero",
            site_index=site_index,
            output_root=output_root,
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            blocks=blocks,
            groups=_zero_groups(role, site_index),
        )
        zero_bounds[str(site_index)] = _validate_zero_values(zero)
        rows_total += _expected_shard_rows("zero")
        for kind, groups in (
            (
                "item",
                _item_groups(role, site_index, directions, direction_mask, target_rms),
            ),
            (
                "prototype",
                _prototype_groups(
                    role, site_index, wrapper_deltas, wrapper_mask, target_rms
                ),
            ),
            (
                "null",
                _null_groups(
                    role, site_index, wrapper_deltas, wrapper_mask, target_rms
                ),
            ),
        ):
            _execute_groups(
                role=role,
                kind=kind,
                site_index=site_index,
                output_root=output_root,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                groups=groups,
            )
            rows_total += _expected_shard_rows(kind)
    _require(rows_total == _expected_counts()["rows_per_model"], "T14-X total changed")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "source_run_root": str(source_run_root),
        "source_run_binding_root_sha256": _source_closeout()["run_binding_root_sha256"],
        "response_rows": rows_total,
        "generation_calls": 0,
        "zero_hook_bounds": zero_bounds,
        "model_receipt": model_receipt,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "elapsed_seconds_this_process": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(summary_path, summary)
    result = validate_role(role, output_root)
    del model
    torch.cuda.empty_cache()
    return result


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    _require(role in model_roles(), f"Unknown T14-X role: {role}")
    rows = 0
    for site_index in SITE_INDICES:
        for kind in ("zero", "item", "prototype", "null"):
            directory = _output_directory(output_root, role, kind, site_index)
            validate_shard(directory, role, kind, site_index)
            if kind == "zero":
                _validate_zero_values(directory)
            rows += _expected_shard_rows(kind)
    summary = _read_json(output_root / role / "summary.json")
    _require(summary.get("protocol_id") == PROTOCOL_ID, "T14-X summary mismatch")
    _require(summary.get("status") == "role_complete", "T14-X role incomplete")
    _require(int(summary.get("response_rows")) == rows, "T14-X summary rows changed")
    _require(rows == _expected_counts()["rows_per_model"], "T14-X role rows changed")
    return {"status": "pass", "model_role": role, "response_rows": rows}


def audit_run(output_root: Path) -> dict[str, Any]:
    audit_freeze()
    results = [validate_role(role, output_root) for role in model_roles()]
    total = sum(int(row["response_rows"]) for row in results)
    _require(total == _expected_counts()["rows_total"], "T14-X run total changed")
    return {
        "status": "complete_closed_to_adaptive_selection",
        "protocol_id": PROTOCOL_ID,
        "roles_complete": len(results),
        "response_rows": total,
        "scientific_open_authorized": True,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
        "generation_calls": 0,
    }


def run_all(
    *,
    output_root: Path,
    source_run_root: Path,
    preflight_directory: Path,
) -> dict[str, Any]:
    completed = []
    for role in model_roles():
        completed.append(
            run_role(
                role=role,
                output_root=output_root,
                source_run_root=source_run_root,
                preflight_directory=preflight_directory,
                model_path=None,
            )
        )
    total = sum(int(row["response_rows"]) for row in completed)
    _require(total == _expected_counts()["rows_total"], "T14-X run-all total changed")
    return audit_run(output_root)


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
    run = commands.add_parser("run-role")
    run.add_argument("--role", required=True, choices=model_roles())
    run.add_argument("--output-root", required=True, type=Path)
    run.add_argument("--source-run-root", required=True, type=Path)
    run.add_argument("--preflight-directory", required=True, type=Path)
    run.add_argument("--model-path", type=Path)
    run_all_parser = commands.add_parser("run-all")
    run_all_parser.add_argument("--output-root", required=True, type=Path)
    run_all_parser.add_argument("--source-run-root", required=True, type=Path)
    run_all_parser.add_argument("--preflight-directory", required=True, type=Path)
    validate = commands.add_parser("validate-role")
    validate.add_argument("--role", required=True, choices=model_roles())
    validate.add_argument("--output-root", required=True, type=Path)
    audit = commands.add_parser("audit-run")
    audit.add_argument("--output-root", required=True, type=Path)
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
    elif args.command == "run-role":
        result = run_role(
            role=args.role,
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            preflight_directory=args.preflight_directory,
            model_path=args.model_path,
        )
    elif args.command == "run-all":
        result = run_all(
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            preflight_directory=args.preflight_directory,
        )
    elif args.command == "validate-role":
        result = validate_role(args.role, args.output_root)
    else:
        result = audit_run(args.output_root)
    _print(result)


if __name__ == "__main__":
    main()
