#!/usr/bin/env python3
"""Run the frozen Milestone 2 target-cluster confirmatory analysis.

The analysis follows ``docs/MILESTONE2_PROTOCOL.md``.  It reads the positive,
RMS-calibrated emoji rows from one colored-shape intervention ledger and three
fixed matched-null ledgers.  Direction seeds are averaged inside each target;
only targets enter the bootstrap and sign-flip inference.

The script fails closed on model, resolved-configuration, target, condition, or
cell-grid mismatches.  It does not run a model and does not infer missing rows.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import orjson
import yaml


PROTOCOL_ID = "glyphprobe-m2-tokenization-controls-v1"
DEFAULT_MODEL = "openai-community/gpt2"
DEFAULT_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
DEFAULT_BACKEND = "mlx"
DEFAULT_DTYPE = "float32"
DEFAULT_SITE = "resid_post"
DEFAULT_LAYERS = (2, 4)
DEFAULT_STRENGTH = 0.05
DEFAULT_DIRECTION_SEEDS = (101, 211, 307)
DEFAULT_FINGERPRINT_DIM = 96
DEFAULT_FINGERPRINT_SEED = 8_675_309
DEFAULT_DELTA = 0.06
DEFAULT_BOOTSTRAP_REPLICATES = 20_000
DEFAULT_BOOTSTRAP_SEED = 20_260_806
DEFAULT_SIGN_FLIP_DRAWS = 100_000
DEFAULT_SIGN_FLIP_SEED = 20_260_807
DEFAULT_ALPHA = 0.05
DEFAULT_TARGETS_PER_GROUP = 8
PINNED_PARITY_RECEIPT_SHA256 = (
    "98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679"
)
FROZEN_P2_TARGET_SHA256 = (
    "9913f1c33d611b86ff9f5518fe8203319967187e060b3e6a222ce4e3cf27b324"
)
FROZEN_P2_TARGET_PATH = Path("data/targets/p2_confirmatory_targets_v1.jsonl")
ALLOWED_SOURCE_WRAPPER_BASENAMES = frozenset(
    {"source_wrappers.jsonl", "milestone2_independent_source_wrappers_v1.jsonl"}
)
EXPECTED_TARGET_GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
)
EXPECTED_CONDITIONS_PER_PANEL = 10
EPSILON = 1e-12

STATUS_ROBUST = "robust to the prespecified matched controls"
STATUS_EQUIVALENT = "practically equivalent to the matched-null ensemble"
STATUS_UNRESOLVED = "unresolved"


class M2AnalysisError(ValueError):
    """Raised when a frozen-analysis prerequisite is not satisfied."""


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, option=option)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value, pretty=True) + b"\n")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    _atomic_write(path, b"".join(_json_bytes(dict(row)) + b"\n" for row in rows))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise M2AnalysisError(f"Missing intervention ledger: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise M2AnalysisError(
                    f"Invalid JSONL at {path}:{line_number}: {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise M2AnalysisError(f"Expected an object at {path}:{line_number}")
            rows.append(value)
    if not rows:
        raise M2AnalysisError(f"Intervention ledger is empty: {path}")
    return rows


def _read_json_object(path: Path, *, description: str) -> dict[str, Any]:
    if not path.is_file():
        raise M2AnalysisError(f"Missing {description}: {path}")
    try:
        value = orjson.loads(path.read_bytes())
    except orjson.JSONDecodeError as exc:
        raise M2AnalysisError(f"Invalid JSON in {description} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise M2AnalysisError(f"Expected a JSON object in {description}: {path}")
    return value


def _load_frozen_target_groups() -> tuple[dict[str, str], Path]:
    """Load the hash-pinned P2 bank used to authorize IDs and strata."""

    path = Path(__file__).resolve().parents[1] / FROZEN_P2_TARGET_PATH
    if not path.is_file():
        raise M2AnalysisError(f"Missing frozen P2 target bank: {path}")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != FROZEN_P2_TARGET_SHA256:
        raise M2AnalysisError(
            "Frozen P2 target bank SHA-256 mismatch: "
            f"expected {FROZEN_P2_TARGET_SHA256}, observed {actual_sha256}"
        )
    groups: dict[str, str] = {}
    for line_number, row in enumerate(_read_jsonl(path), start=1):
        target_id = row.get("id")
        group = row.get("group")
        if not isinstance(target_id, str) or not target_id:
            raise M2AnalysisError(f"Frozen P2 row {line_number} has no valid ID")
        if not isinstance(group, str) or group not in EXPECTED_TARGET_GROUPS:
            raise M2AnalysisError(
                f"Frozen P2 row {line_number} has invalid group: {group!r}"
            )
        if target_id in groups:
            raise M2AnalysisError(f"Frozen P2 target ID is duplicated: {target_id}")
        groups[target_id] = group
    if len(groups) != len(EXPECTED_TARGET_GROUPS) * DEFAULT_TARGETS_PER_GROUP:
        raise M2AnalysisError(
            f"Frozen P2 bank must contain exactly 48 targets; observed {len(groups)}"
        )
    return groups, path


def _load_config(run_dir: Path) -> tuple[dict[str, Any], Path]:
    path = run_dir / "resolved_config.yaml"
    if not path.is_file():
        raise M2AnalysisError(f"Missing resolved configuration: {path}")
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise M2AnalysisError(f"Expected a mapping in {path}")
    return value, path


def _nested(config: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = config
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            raise M2AnalysisError(
                f"Resolved configuration is missing {'.'.join(path)}"
            )
        current = current[part]
    return current


def _analysis_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Remove only fields that must differ between fixed panel runs."""

    normalized = copy.deepcopy(dict(config))
    run = normalized.get("run")
    if isinstance(run, dict):
        run.pop("name", None)
        run.pop("output_root", None)
    # Panel content and its path identify the treatment arm.  Every other
    # resolved setting remains part of the strict cross-run config signature.
    normalized.pop("panel", None)
    return normalized


def _canonical_hash(value: Any) -> str:
    return _sha256_bytes(_json_bytes(value))


def _validate_fixed_config(
    config: Mapping[str, Any],
    *,
    fingerprint_dim: int,
    fingerprint_seed: int,
    direction_seeds: Sequence[int],
) -> None:
    expected = {
        ("backend", "model"): DEFAULT_MODEL,
        ("backend", "revision"): DEFAULT_REVISION,
        ("backend", "kind"): DEFAULT_BACKEND,
        ("backend", "dtype"): DEFAULT_DTYPE,
        ("backend", "validation_receipt_sha256"): PINNED_PARITY_RECEIPT_SHA256,
        ("capture", "site"): DEFAULT_SITE,
        ("capture", "layers"): list(DEFAULT_LAYERS),
        ("intervention", "normalization"): "rms",
        ("intervention", "strengths"): [DEFAULT_STRENGTH],
        ("targets", "max_cases"): len(EXPECTED_TARGET_GROUPS)
        * DEFAULT_TARGETS_PER_GROUP,
        ("controls", "random_directions_per_layer"): 0,
        ("controls", "zero_direction"): True,
        ("controls", "sign_flip"): False,
        ("controls", "include_neutral_direction"): False,
        ("metrics", "fingerprint_dim"): int(fingerprint_dim),
    }
    for path, wanted in expected.items():
        observed = _nested(config, path)
        type_mismatch = (
            isinstance(wanted, bool)
            and observed is not wanted
            or type(wanted) is int
            and (type(observed) is not int or observed != wanted)
        )
        if observed != wanted or type_mismatch:
            raise M2AnalysisError(
                f"Protocol config mismatch at {'.'.join(path)}: "
                f"expected {wanted!r}, observed {observed!r}"
            )
    observed_seed = int(
        (config.get("metrics") or {}).get("fingerprint_seed", DEFAULT_FINGERPRINT_SEED)
    )
    if observed_seed != int(fingerprint_seed):
        raise M2AnalysisError(
            "Protocol config mismatch at metrics.fingerprint_seed: "
            f"expected {fingerprint_seed}, observed {observed_seed}"
        )
    raw_configured_seeds = _nested(config, ("run", "seeds"))
    if not isinstance(raw_configured_seeds, list) or any(
        type(value) is not int for value in raw_configured_seeds
    ):
        raise M2AnalysisError(
            "Protocol config mismatch at run.seeds: expected a list of integer seeds"
        )
    configured_seeds = tuple(raw_configured_seeds)
    if configured_seeds != tuple(int(value) for value in direction_seeds):
        raise M2AnalysisError(
            "Protocol config mismatch at run.seeds: "
            f"expected {tuple(direction_seeds)}, observed {configured_seeds}"
        )
    target_basename = Path(str(_nested(config, ("targets", "cases_file")))).name
    if target_basename != "p2_confirmatory_targets_v1.jsonl":
        raise M2AnalysisError(
            "Protocol config mismatch at targets.cases_file: expected basename "
            f"'p2_confirmatory_targets_v1.jsonl', observed {target_basename!r}"
        )
    source_basename = Path(str(_nested(config, ("source", "wrappers_file")))).name
    if source_basename not in ALLOWED_SOURCE_WRAPPER_BASENAMES:
        raise M2AnalysisError(
            "Protocol config mismatch at source.wrappers_file: expected one of "
            f"{sorted(ALLOWED_SOURCE_WRAPPER_BASENAMES)}, observed {source_basename!r}"
        )


def _validate_protocol_parameters(
    *,
    layers: Sequence[int],
    strength: float,
    direction_seeds: Sequence[int],
    fingerprint_dim: int,
    fingerprint_seed: int,
    delta: float,
    bootstrap_replicates: int,
    bootstrap_seed: int,
    sign_flip_draws: int,
    sign_flip_seed: int,
    alpha: float,
    expected_targets_per_group: int,
) -> None:
    if any(type(value) is not int for value in layers):
        raise M2AnalysisError(
            "Strict protocol parameter mismatch; layers must be exact integer constants"
        )
    if any(type(value) is not int for value in direction_seeds):
        raise M2AnalysisError(
            "Strict protocol parameter mismatch; direction seeds must be exact integers"
        )
    integral_parameters = {
        "fingerprint_dim": fingerprint_dim,
        "fingerprint_seed": fingerprint_seed,
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": bootstrap_seed,
        "sign_flip_draws": sign_flip_draws,
        "sign_flip_seed": sign_flip_seed,
        "expected_targets_per_group": expected_targets_per_group,
    }
    invalid_integral = {
        name: value
        for name, value in integral_parameters.items()
        if type(value) is not int
    }
    if invalid_integral:
        raise M2AnalysisError(
            "Strict protocol parameter mismatch; integer constants have invalid types: "
            f"{invalid_integral}"
        )
    float_parameters = {"strength": strength, "delta": delta, "alpha": alpha}
    invalid_float = {
        name: value for name, value in float_parameters.items() if type(value) is not float
    }
    if invalid_float:
        raise M2AnalysisError(
            "Strict protocol parameter mismatch; floating constants have invalid types: "
            f"{invalid_float}"
        )
    observed = {
        "layers": tuple(layers),
        "strength": float(strength),
        "direction_seeds": tuple(direction_seeds),
        "fingerprint_dim": fingerprint_dim,
        "fingerprint_seed": fingerprint_seed,
        "delta": float(delta),
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": bootstrap_seed,
        "sign_flip_draws": sign_flip_draws,
        "sign_flip_seed": sign_flip_seed,
        "alpha": float(alpha),
        "expected_targets_per_group": expected_targets_per_group,
    }
    expected = {
        "layers": DEFAULT_LAYERS,
        "strength": DEFAULT_STRENGTH,
        "direction_seeds": DEFAULT_DIRECTION_SEEDS,
        "fingerprint_dim": DEFAULT_FINGERPRINT_DIM,
        "fingerprint_seed": DEFAULT_FINGERPRINT_SEED,
        "delta": DEFAULT_DELTA,
        "bootstrap_replicates": DEFAULT_BOOTSTRAP_REPLICATES,
        "bootstrap_seed": DEFAULT_BOOTSTRAP_SEED,
        "sign_flip_draws": DEFAULT_SIGN_FLIP_DRAWS,
        "sign_flip_seed": DEFAULT_SIGN_FLIP_SEED,
        "alpha": DEFAULT_ALPHA,
        "expected_targets_per_group": DEFAULT_TARGETS_PER_GROUP,
    }
    mismatches = {
        name: {"expected": expected[name], "observed": value}
        for name, value in observed.items()
        if value != expected[name]
    }
    if mismatches:
        raise M2AnalysisError(
            "Strict protocol parameter mismatch; protocol v1 constants are immutable: "
            f"{mismatches}"
        )


def _load_and_validate_run_evidence(
    run_dir: Path, *, ledger_target_ids: Sequence[str]
) -> dict[str, Any]:
    receipt_path = run_dir / "receipt.json"
    receipt = _read_json_object(receipt_path, description="run receipt")
    if receipt.get("status") != "complete":
        raise M2AnalysisError(
            f"Run receipt status must be 'complete' in {receipt_path}; "
            f"observed {receipt.get('status')!r}"
        )
    input_hashes = receipt.get("input_hashes")
    if not isinstance(input_hashes, dict):
        raise M2AnalysisError(f"Run receipt has no input_hashes mapping: {receipt_path}")
    if not all(isinstance(value, str) for value in input_hashes.values()):
        raise M2AnalysisError(
            f"Run receipt input_hashes values must all be strings: {receipt_path}"
        )
    hash_values = set(input_hashes.values())
    required_hashes = {FROZEN_P2_TARGET_SHA256, PINNED_PARITY_RECEIPT_SHA256}
    missing_hashes = sorted(required_hashes - hash_values)
    if missing_hashes:
        raise M2AnalysisError(
            f"Run receipt input_hashes is missing frozen evidence in {receipt_path}: "
            f"{missing_hashes}"
        )

    resolved_inputs_path = run_dir / "resolved_inputs.json"
    resolved_inputs = _read_json_object(
        resolved_inputs_path, description="resolved run inputs"
    )
    resolved_target_ids = resolved_inputs.get("target_ids")
    if not isinstance(resolved_target_ids, list) or not all(
        isinstance(value, str) and value for value in resolved_target_ids
    ):
        raise M2AnalysisError(
            f"resolved_inputs.json must contain a non-empty string target_ids list: "
            f"{resolved_inputs_path}"
        )
    if len(resolved_target_ids) != 48 or len(set(resolved_target_ids)) != 48:
        raise M2AnalysisError(
            f"resolved_inputs target_ids must contain exactly 48 unique IDs: "
            f"{resolved_inputs_path}"
        )
    ledger_ids = list(ledger_target_ids)
    if len(ledger_ids) != 48 or set(resolved_target_ids) != set(ledger_ids):
        raise M2AnalysisError(
            f"resolved_inputs target IDs do not exactly match the ledger target grid: "
            f"{resolved_inputs_path}"
        )
    return {
        "receipt_path": receipt_path,
        "resolved_inputs_path": resolved_inputs_path,
    }


def _finite_number(value: Any, *, field: str, line_number: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise M2AnalysisError(f"Row {line_number} has invalid {field}: {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise M2AnalysisError(f"Row {line_number} has non-finite {field}")
    return result


def _extract_fingerprint(
    row: Mapping[str, Any], *, line_number: int, fingerprint_dim: int
) -> np.ndarray:
    distribution = row.get("distribution")
    value = distribution.get("fingerprint") if isinstance(distribution, Mapping) else None
    if value is None:
        value = row.get("fingerprint")
    vector = np.asarray(value, dtype=np.float64) if value is not None else np.asarray([])
    if vector.ndim != 1 or vector.size != fingerprint_dim:
        raise M2AnalysisError(
            f"Row {line_number} fingerprint dimension mismatch: "
            f"expected {fingerprint_dim}, observed shape {vector.shape}"
        )
    if not np.all(np.isfinite(vector)):
        raise M2AnalysisError(f"Row {line_number} fingerprint contains non-finite values")
    norm = float(np.linalg.norm(vector))
    if norm <= EPSILON:
        raise M2AnalysisError(f"Row {line_number} fingerprint has zero norm")
    return vector / norm


def _eligible(row: Mapping[str, Any]) -> bool:
    sign = row.get("sign")
    return (
        not isinstance(sign, bool)
        and sign == 1
        and row.get("calibration") == "rms"
        and row.get("condition_type") == "emoji"
    )


def _load_panel(
    run_dir: Path,
    *,
    label: str,
    fingerprint_dim: int,
    fingerprint_seed: int,
    layers: Sequence[int],
    strength: float,
    direction_seeds: Sequence[int],
    expected_targets_per_group: int,
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    config, config_path = _load_config(run_dir)
    _validate_fixed_config(
        config,
        fingerprint_dim=fingerprint_dim,
        fingerprint_seed=fingerprint_seed,
        direction_seeds=direction_seeds,
    )
    ledger_path = run_dir / "interventions.jsonl"
    raw_rows = _read_jsonl(ledger_path)

    vectors: dict[tuple[int, float, int, str, str], np.ndarray] = {}
    targets: dict[str, str] = {}
    conditions: set[str] = set()
    cells: set[tuple[int, float, int]] = set()
    for line_number, row in enumerate(raw_rows, start=1):
        if not _eligible(row):
            continue
        required = ("layer", "strength", "seed", "condition_id", "target_id", "target_group")
        missing = [field for field in required if field not in row]
        if missing:
            raise M2AnalysisError(
                f"Eligible row {line_number} in {ledger_path} is missing: "
                f"{', '.join(missing)}"
            )
        layer = int(_finite_number(row["layer"], field="layer", line_number=line_number))
        row_strength = _finite_number(
            row["strength"], field="strength", line_number=line_number
        )
        seed = int(_finite_number(row["seed"], field="seed", line_number=line_number))
        condition_id = str(row["condition_id"])
        target_id = str(row["target_id"])
        target_group = str(row["target_group"])
        if not condition_id or not target_id or not target_group:
            raise M2AnalysisError(f"Eligible row {line_number} has an empty identifier")
        previous_group = targets.get(target_id)
        if previous_group is not None and previous_group != target_group:
            raise M2AnalysisError(
                f"Target {target_id!r} has inconsistent groups in {ledger_path}: "
                f"{previous_group!r} and {target_group!r}"
            )
        targets[target_id] = target_group
        conditions.add(condition_id)
        cell = (layer, row_strength, seed)
        cells.add(cell)
        key = (layer, row_strength, seed, condition_id, target_id)
        if key in vectors:
            raise M2AnalysisError(f"Duplicate eligible grid row in {ledger_path}: {key}")
        vectors[key] = _extract_fingerprint(
            row, line_number=line_number, fingerprint_dim=fingerprint_dim
        )

    if not vectors:
        raise M2AnalysisError(
            f"No positive RMS emoji fingerprints were found in {ledger_path}"
        )
    if len(conditions) != EXPECTED_CONDITIONS_PER_PANEL:
        raise M2AnalysisError(
            f"Panel {label} must have exactly {EXPECTED_CONDITIONS_PER_PANEL} conditions; "
            f"observed {len(conditions)}"
        )
    expected_cells = {
        (int(layer), float(strength), int(seed))
        for layer in layers
        for seed in direction_seeds
    }
    if cells != expected_cells:
        raise M2AnalysisError(
            f"Panel {label} cell grid does not match the frozen primary grid: "
            f"missing={sorted(expected_cells - cells)}, extra={sorted(cells - expected_cells)}"
        )

    by_group: dict[str, list[str]] = defaultdict(list)
    for target_id, group in targets.items():
        by_group[group].append(target_id)
    if set(by_group) != set(EXPECTED_TARGET_GROUPS):
        raise M2AnalysisError(
            f"Panel {label} target-group grid mismatch: expected "
            f"{list(EXPECTED_TARGET_GROUPS)}, observed {sorted(by_group)}"
        )
    wrong_counts = {
        group: len(target_ids)
        for group, target_ids in by_group.items()
        if len(target_ids) != expected_targets_per_group
    }
    if wrong_counts:
        raise M2AnalysisError(
            f"Panel {label} target-group grid must contain exactly "
            f"{expected_targets_per_group} targets per group; observed {wrong_counts}"
        )

    run_evidence = _load_and_validate_run_evidence(
        run_dir, ledger_target_ids=sorted(targets)
    )

    expected_keys = {
        (layer, cell_strength, seed, condition_id, target_id)
        for layer, cell_strength, seed in expected_cells
        for condition_id in conditions
        for target_id in targets
    }
    observed_keys = set(vectors)
    if observed_keys != expected_keys:
        raise M2AnalysisError(
            f"Panel {label} condition/target/cell grid is incomplete: "
            f"missing_count={len(expected_keys - observed_keys)}, "
            f"extra_count={len(observed_keys - expected_keys)}"
        )

    return {
        "label": label,
        "run_dir": run_dir,
        "ledger_path": ledger_path,
        "config_path": config_path,
        "config": config,
        "analysis_config": _analysis_config(config),
        "vectors": vectors,
        "conditions": tuple(sorted(conditions)),
        "targets": targets,
        "cells": cells,
        "eligible_row_count": len(vectors),
        "run_receipt_path": run_evidence["receipt_path"],
        "resolved_inputs_path": run_evidence["resolved_inputs_path"],
    }


def _validate_cross_panel_grids(panels: Sequence[Mapping[str, Any]]) -> None:
    reference = panels[0]
    reference_targets = reference["targets"]
    reference_cells = reference["cells"]
    reference_config = reference["analysis_config"]
    for panel in panels[1:]:
        if panel["targets"] != reference_targets:
            missing = sorted(set(reference_targets) - set(panel["targets"]))
            extra = sorted(set(panel["targets"]) - set(reference_targets))
            regrouped = sorted(
                target_id
                for target_id in set(reference_targets) & set(panel["targets"])
                if reference_targets[target_id] != panel["targets"][target_id]
            )
            raise M2AnalysisError(
                f"Target grid mismatch for panel {panel['label']}: "
                f"missing={missing}, extra={extra}, regrouped={regrouped}"
            )
        if panel["cells"] != reference_cells:
            raise M2AnalysisError(f"Cell grid mismatch for panel {panel['label']}")
        if panel["analysis_config"] != reference_config:
            raise M2AnalysisError(
                f"Resolved config mismatch for panel {panel['label']} after excluding "
                "only run-output and panel-treatment fields"
            )


def _cosine(first: np.ndarray, second: np.ndarray) -> float:
    # Stored vectors and prototypes are unit normalized, but keeping the full
    # denominator makes this helper safe and explicit.
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator <= EPSILON:
        raise M2AnalysisError("A zero-norm vector reached the cosine endpoint")
    return float(np.dot(first, second) / denominator)


def _unit_mean(vectors: Sequence[np.ndarray]) -> np.ndarray:
    if not vectors:
        raise M2AnalysisError("Cannot construct a prototype from an empty target set")
    mean = np.mean(np.asarray(vectors, dtype=np.float64), axis=0)
    norm = float(np.linalg.norm(mean))
    if norm <= EPSILON:
        raise M2AnalysisError("A leave-one-group-out prototype has zero norm")
    return mean / norm


def _panel_target_scores(
    panel: Mapping[str, Any], *, layer: int, strength: float, direction_seeds: Sequence[int]
) -> tuple[dict[str, float], dict[str, dict[int, float]]]:
    conditions: tuple[str, ...] = panel["conditions"]
    targets: Mapping[str, str] = panel["targets"]
    vectors: Mapping[tuple[int, float, int, str, str], np.ndarray] = panel["vectors"]
    target_ids = tuple(sorted(targets))

    prototypes: dict[tuple[int, str, str], np.ndarray] = {}
    for seed in direction_seeds:
        for held_out_group in EXPECTED_TARGET_GROUPS:
            training_targets = [
                target_id
                for target_id in target_ids
                if targets[target_id] != held_out_group
            ]
            for condition_id in conditions:
                prototypes[(int(seed), held_out_group, condition_id)] = _unit_mean(
                    [
                        vectors[(layer, strength, int(seed), condition_id, target_id)]
                        for target_id in training_targets
                    ]
                )

    seed_scores: dict[str, dict[int, float]] = {}
    target_scores: dict[str, float] = {}
    for target_id in target_ids:
        group = targets[target_id]
        within: dict[int, float] = {}
        for seed in direction_seeds:
            same: list[float] = []
            cross: list[float] = []
            for condition_id in conditions:
                fingerprint = vectors[
                    (layer, strength, int(seed), condition_id, target_id)
                ]
                same.append(
                    _cosine(
                        fingerprint,
                        prototypes[(int(seed), group, condition_id)],
                    )
                )
                cross.extend(
                    _cosine(
                        fingerprint,
                        prototypes[(int(seed), group, other_condition)],
                    )
                    for other_condition in conditions
                    if other_condition != condition_id
                )
            within[int(seed)] = float(np.mean(same) - np.mean(cross))
        seed_scores[target_id] = within
        target_scores[target_id] = float(np.mean(list(within.values())))
    return target_scores, seed_scores


def _stratified_bootstrap(
    effects: Mapping[str, float],
    target_groups: Mapping[str, str],
    *,
    replicates: int,
    seed: int,
) -> np.ndarray:
    if replicates <= 0:
        raise M2AnalysisError("Bootstrap replicate count must be positive")
    rng = np.random.default_rng(seed)
    bootstrap_sum = np.zeros(replicates, dtype=np.float64)
    total_count = 0
    for group in EXPECTED_TARGET_GROUPS:
        values = np.asarray(
            [
                effects[target_id]
                for target_id in sorted(effects)
                if target_groups[target_id] == group
            ],
            dtype=np.float64,
        )
        if values.size == 0:
            raise M2AnalysisError(f"No target effects are available for group {group}")
        indices = rng.integers(0, values.size, size=(replicates, values.size))
        bootstrap_sum += values[indices].sum(axis=1)
        total_count += int(values.size)
    return bootstrap_sum / total_count


def _sign_flip_p_value(
    effects: Sequence[float],
    *,
    delta: float,
    draws: int,
    seed: int,
) -> tuple[float, float, int]:
    if draws <= 0:
        raise M2AnalysisError("Sign-flip draw count must be positive")
    centered = np.asarray(effects, dtype=np.float64) - float(delta)
    observed = float(np.mean(centered))
    rng = np.random.default_rng(seed)
    exceedances = 0
    remaining = int(draws)
    while remaining:
        chunk = min(remaining, 10_000)
        signs = rng.integers(0, 2, size=(chunk, centered.size), dtype=np.int8)
        signs = signs * 2 - 1
        statistics = np.mean(signs * centered, axis=1)
        exceedances += int(np.count_nonzero(statistics >= observed))
        remaining -= chunk
    p_value = float((exceedances + 1) / (draws + 1))
    return p_value, observed, exceedances


def _holm_adjust(raw_p_values: Mapping[int, float]) -> dict[int, float]:
    ordered = sorted(raw_p_values.items(), key=lambda item: (item[1], item[0]))
    family_size = len(ordered)
    adjusted: dict[int, float] = {}
    running_max = 0.0
    for rank, (layer, p_value) in enumerate(ordered):
        candidate = min(1.0, (family_size - rank) * float(p_value))
        running_max = max(running_max, candidate)
        adjusted[layer] = running_max
    return adjusted


def _midrank_percentile(value: float, null_values: Sequence[float]) -> float:
    below = sum(item < value and not math.isclose(item, value, abs_tol=1e-15) for item in null_values)
    equal = sum(math.isclose(item, value, rel_tol=0.0, abs_tol=1e-15) for item in null_values)
    return float((below + 0.5 * equal) / len(null_values))


def _status(
    *, ci_low: float, ci_high: float, delta: float, holm_p: float, alpha: float
) -> str:
    if ci_low > delta and holm_p < alpha:
        return STATUS_ROBUST
    if ci_low >= -delta and ci_high <= delta:
        return STATUS_EQUIVALENT
    return STATUS_UNRESOLVED


def _input_record(panel: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "panel_role": panel["label"],
        "run_label": panel["run_dir"].name,
        "interventions_file": panel["ledger_path"].name,
        "interventions_sha256": _sha256_file(panel["ledger_path"]),
        "resolved_config_file": panel["config_path"].name,
        "resolved_config_sha256": _sha256_file(panel["config_path"]),
        "run_receipt_file": panel["run_receipt_path"].name,
        "run_receipt_sha256": _sha256_file(panel["run_receipt_path"]),
        "resolved_inputs_file": panel["resolved_inputs_path"].name,
        "resolved_inputs_sha256": _sha256_file(panel["resolved_inputs_path"]),
        "frozen_p2_target_sha256_verified": FROZEN_P2_TARGET_SHA256,
        "pinned_parity_receipt_sha256_verified": PINNED_PARITY_RECEIPT_SHA256,
        "run_receipt_status": "complete",
        "resolved_input_target_count": 48,
        "eligible_positive_rms_emoji_row_count": panel["eligible_row_count"],
        "condition_ids": list(panel["conditions"]),
    }


def _markdown_report(
    *,
    analysis_id: str,
    protocol_conformant: bool,
    inputs: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
    parameters: Mapping[str, Any],
    target_effects_sha256: str,
    target_effect_count: int,
) -> str:
    lines = [
        "# Milestone 2 confirmatory analysis report",
        "",
        f"Analysis ID: `{analysis_id}`",
        "",
        "## Primary results",
        "",
        "| Layer | Mean adjusted target effect | 95% stratified bootstrap CI | "
        "Raw sign-flip p | Holm-adjusted p | Status |",
        "|---:|---:|:---:|---:|---:|:---|",
    ]
    if not protocol_conformant:
        lines[3:3] = [
            "**NON-PROTOCOL SYNTHETIC VALIDATION:** protocol v1 claims are not authorized.",
            "",
        ]
    for result in results:
        lines.append(
            f"| {result['layer']} | {result['mean_adjusted_target_effect']:.8f} | "
            f"[{result['bootstrap_ci_95']['low']:.8f}, "
            f"{result['bootstrap_ci_95']['high']:.8f}] | "
            f"{result['sign_flip']['raw_one_sided_p']:.8g} | "
            f"{result['holm_adjusted_one_sided_p']:.8g} | "
            f"{result['status']} |"
        )
    lines.extend(
        [
            "",
            "The minimally meaningful excess is "
            f"`delta = {parameters['delta']}`. The interval is a percentile cluster "
            "bootstrap that resamples targets within each of the six frozen groups. "
            "The one-sided sign-flip screen is applied to `D[t] - delta`; Holm "
            "correction covers the two primary layers.",
            "",
            "## Evidence hashes",
            "",
            "| Role | Intervention ledger SHA-256 | Resolved config SHA-256 | "
            "Run receipt SHA-256 | Resolved inputs SHA-256 |",
            "|:---|:---|:---|:---|:---|",
        ]
    )
    for input_record in inputs:
        lines.append(
            f"| {input_record['panel_role']} | "
            f"`{input_record['interventions_sha256']}` | "
            f"`{input_record['resolved_config_sha256']}` | "
            f"`{input_record['run_receipt_sha256']}` | "
            f"`{input_record['resolved_inputs_sha256']}` |"
        )
    lines.extend(
        [
            "",
            f"Target effects: `{target_effects_sha256}` ({target_effect_count} "
            "layer-target rows).",
            "",
            "## Independence and claim boundaries",
            "",
            "- The effective observation unit is a target. Direction seeds are "
            "averaged within each target and do not increase sample size.",
            "- Conditions, null panels, bootstrap replicates, and sign-flip draws "
            "are not independent observations.",
            "- A robust result supports robustness only to the prespecified "
            "token-count and token-prefix matched controls. It is not a "
            "tokenization-free, semantic, mechanistic, or causal glyph effect.",
            "- Practical equivalence is restricted to this endpoint, margin, frozen "
            "bank, and matched-null ensemble. It does not prove that tokenization "
            "caused the exploratory result.",
            "- Failure to pass either rule remains unresolved and is not evidence of "
            "absence.",
            "",
            "This report is generated from the frozen ledgers. Do not edit it by hand.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze_confirmatory(
    primary_run: Path,
    matched_null_runs: Sequence[Path],
    *,
    output_dir: Path,
    layers: Sequence[int] = DEFAULT_LAYERS,
    strength: float = DEFAULT_STRENGTH,
    direction_seeds: Sequence[int] = DEFAULT_DIRECTION_SEEDS,
    fingerprint_dim: int = DEFAULT_FINGERPRINT_DIM,
    fingerprint_seed: int = DEFAULT_FINGERPRINT_SEED,
    delta: float = DEFAULT_DELTA,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
    sign_flip_draws: int = DEFAULT_SIGN_FLIP_DRAWS,
    sign_flip_seed: int = DEFAULT_SIGN_FLIP_SEED,
    alpha: float = DEFAULT_ALPHA,
    expected_targets_per_group: int = DEFAULT_TARGETS_PER_GROUP,
    strict_protocol: bool = True,
) -> dict[str, Any]:
    """Validate four run directories, run the frozen analysis, and write outputs."""

    if strict_protocol:
        _validate_protocol_parameters(
            layers=layers,
            strength=strength,
            direction_seeds=direction_seeds,
            fingerprint_dim=fingerprint_dim,
            fingerprint_seed=fingerprint_seed,
            delta=delta,
            bootstrap_replicates=bootstrap_replicates,
            bootstrap_seed=bootstrap_seed,
            sign_flip_draws=sign_flip_draws,
            sign_flip_seed=sign_flip_seed,
            alpha=alpha,
            expected_targets_per_group=expected_targets_per_group,
        )
    analysis_id = PROTOCOL_ID if strict_protocol else "nonprotocol-synthetic-validation"

    if len(matched_null_runs) != 3:
        raise M2AnalysisError(
            f"Exactly three matched-null run directories are required; observed "
            f"{len(matched_null_runs)}"
        )
    resolved_layers = tuple(int(value) for value in layers)
    resolved_seeds = tuple(int(value) for value in direction_seeds)
    if len(resolved_layers) != 2 or len(set(resolved_layers)) != 2:
        raise M2AnalysisError("The primary family must contain exactly two distinct layers")
    if len(resolved_seeds) != 3 or len(set(resolved_seeds)) != 3:
        raise M2AnalysisError("Exactly three distinct direction seeds are required")
    if fingerprint_dim <= 0 or delta <= 0 or not 0 < alpha < 1:
        raise M2AnalysisError("Fingerprint dimension and delta must be positive; alpha must be in (0, 1)")

    roles = ("primary_colored_shapes", "matched_null_a", "matched_null_b", "matched_null_c")
    run_dirs = (Path(primary_run), *(Path(path) for path in matched_null_runs))
    resolved_run_dirs = tuple(path.resolve() for path in run_dirs)
    if len(set(resolved_run_dirs)) != 4:
        raise M2AnalysisError(
            "The primary and three matched-null inputs must be four distinct run directories"
        )
    panels = [
        _load_panel(
            run_dir,
            label=label,
            fingerprint_dim=int(fingerprint_dim),
            fingerprint_seed=int(fingerprint_seed),
            layers=resolved_layers,
            strength=float(strength),
            direction_seeds=resolved_seeds,
            expected_targets_per_group=int(expected_targets_per_group),
        )
        for label, run_dir in zip(roles, run_dirs)
    ]
    _validate_cross_panel_grids(panels)
    frozen_target_path: Path | None = None
    if strict_protocol:
        frozen_target_groups, frozen_target_path = _load_frozen_target_groups()
        if panels[0]["targets"] != frozen_target_groups:
            missing = sorted(set(frozen_target_groups) - set(panels[0]["targets"]))
            extra = sorted(set(panels[0]["targets"]) - set(frozen_target_groups))
            regrouped = sorted(
                target_id
                for target_id in set(frozen_target_groups) & set(panels[0]["targets"])
                if frozen_target_groups[target_id] != panels[0]["targets"][target_id]
            )
            raise M2AnalysisError(
                "Ledger target IDs/groups do not match the hash-pinned P2 bank: "
                f"missing={missing}, extra={extra}, regrouped={regrouped}"
            )
    condition_sets = [set(panel["conditions"]) for panel in panels]
    for left in range(len(condition_sets)):
        for right in range(left + 1, len(condition_sets)):
            overlap = sorted(condition_sets[left] & condition_sets[right])
            if overlap:
                raise M2AnalysisError(
                    f"Condition IDs must be disjoint across fixed panels; "
                    f"{roles[left]} and {roles[right]} overlap at {overlap}"
                )

    target_groups: Mapping[str, str] = panels[0]["targets"]
    layer_payloads: dict[int, dict[str, Any]] = {}
    target_effect_rows: list[dict[str, Any]] = []
    raw_p_values: dict[int, float] = {}
    for layer in resolved_layers:
        panel_scores: list[dict[str, float]] = []
        panel_seed_scores: list[dict[str, dict[int, float]]] = []
        for panel in panels:
            scores, seed_scores = _panel_target_scores(
                panel,
                layer=layer,
                strength=float(strength),
                direction_seeds=resolved_seeds,
            )
            panel_scores.append(scores)
            panel_seed_scores.append(seed_scores)

        effects: dict[str, float] = {}
        for target_id in sorted(target_groups):
            null_scores = [panel_scores[index][target_id] for index in (1, 2, 3)]
            null_median = float(np.median(null_scores))
            effect = float(panel_scores[0][target_id] - null_median)
            effects[target_id] = effect
            target_effect_rows.append(
                {
                    "analysis_id": analysis_id,
                    "protocol_conformant": bool(strict_protocol),
                    "layer": layer,
                    "strength": float(strength),
                    "target_id": target_id,
                    "target_group": target_groups[target_id],
                    "primary_score": panel_scores[0][target_id],
                    "matched_null_scores": {
                        "a": null_scores[0],
                        "b": null_scores[1],
                        "c": null_scores[2],
                    },
                    "matched_null_median": null_median,
                    "adjusted_target_effect_D": effect,
                    "primary_seed_scores": {
                        str(seed): panel_seed_scores[0][target_id][seed]
                        for seed in resolved_seeds
                    },
                    "matched_null_seed_scores": {
                        label: {
                            str(seed): panel_seed_scores[index][target_id][seed]
                            for seed in resolved_seeds
                        }
                        for label, index in (("a", 1), ("b", 2), ("c", 3))
                    },
                    "direction_seeds_averaged_within_target": True,
                }
            )

        bootstrap = _stratified_bootstrap(
            effects,
            target_groups,
            replicates=int(bootstrap_replicates),
            seed=int(bootstrap_seed),
        )
        ci_low, ci_high = np.quantile(bootstrap, (0.025, 0.975))
        p_value, observed_centered, exceedances = _sign_flip_p_value(
            list(effects.values()),
            delta=float(delta),
            draws=int(sign_flip_draws),
            seed=int(sign_flip_seed),
        )
        raw_p_values[layer] = p_value
        primary_values = list(panel_scores[0].values())
        null_medians = [
            float(np.median([panel_scores[index][target_id] for index in (1, 2, 3)]))
            for target_id in sorted(target_groups)
        ]
        layer_payloads[layer] = {
            "layer": layer,
            "strength": float(strength),
            "target_observation_count": len(effects),
            "mean_adjusted_target_effect": float(np.mean(list(effects.values()))),
            "median_adjusted_target_effect": float(np.median(list(effects.values()))),
            "mean_primary_score": float(np.mean(primary_values)),
            "mean_matched_null_median_score": float(np.mean(null_medians)),
            "bootstrap_ci_95": {
                "method": "percentile stratified target-cluster bootstrap",
                "low": float(ci_low),
                "high": float(ci_high),
                "replicates": int(bootstrap_replicates),
                "seed": int(bootstrap_seed),
                "resampling": (
                    f"{expected_targets_per_group} targets with replacement inside each "
                    f"of {len(EXPECTED_TARGET_GROUPS)} fixed groups"
                ),
            },
            "sign_flip": {
                "contrast": "D[t] - delta",
                "observed_centered_mean": observed_centered,
                "raw_one_sided_p": p_value,
                "draws": int(sign_flip_draws),
                "seed": int(sign_flip_seed),
                "exceedance_count": exceedances,
                "plus_one_correction": True,
            },
            "descriptive": {
                "positive_adjusted_target_count": sum(value > 0 for value in effects.values()),
                "nonpositive_adjusted_target_count": sum(value <= 0 for value in effects.values()),
                "primary_midrank_percentile_within_three_null_panel_means": _midrank_percentile(
                    float(np.mean(primary_values)),
                    [
                        float(np.mean(list(panel_scores[index].values())))
                        for index in (1, 2, 3)
                    ],
                ),
            },
        }

    adjusted = _holm_adjust(raw_p_values)
    primary_results: list[dict[str, Any]] = []
    for layer in resolved_layers:
        result = layer_payloads[layer]
        result["holm_adjusted_one_sided_p"] = adjusted[layer]
        result["status"] = _status(
            ci_low=result["bootstrap_ci_95"]["low"],
            ci_high=result["bootstrap_ci_95"]["high"],
            delta=float(delta),
            holm_p=adjusted[layer],
            alpha=float(alpha),
        )
        primary_results.append(result)

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target_effects_path = output_dir / "m2_target_effects.jsonl"
    report_path = output_dir / "m2_confirmatory_report.md"
    receipt_path = output_dir / "m2_confirmatory_receipt.json"
    _write_jsonl(target_effects_path, target_effect_rows)
    target_effects_sha256 = _sha256_file(target_effects_path)
    input_records = [_input_record(panel) for panel in panels]
    parameters = {
        "layers": list(resolved_layers),
        "strength": float(strength),
        "direction_seeds": list(resolved_seeds),
        "fingerprint_dim": int(fingerprint_dim),
        "fingerprint_seed": int(fingerprint_seed),
        "delta": float(delta),
        "bootstrap_replicates": int(bootstrap_replicates),
        "bootstrap_seed": int(bootstrap_seed),
        "sign_flip_draws": int(sign_flip_draws),
        "sign_flip_seed": int(sign_flip_seed),
        "alpha": float(alpha),
    }
    report = _markdown_report(
        analysis_id=analysis_id,
        protocol_conformant=bool(strict_protocol),
        inputs=input_records,
        results=primary_results,
        parameters=parameters,
        target_effects_sha256=target_effects_sha256,
        target_effect_count=len(target_effect_rows),
    )
    _atomic_write(report_path, report.encode("utf-8"))
    report_sha256 = _sha256_file(report_path)

    receipt = {
        "schema_version": 1,
        "analysis_id": analysis_id,
        "protocol_id": PROTOCOL_ID if strict_protocol else None,
        "protocol_conformant": bool(strict_protocol),
        "analysis": "leave-one-target-group-out matched-panel confirmatory analysis",
        "inputs": input_records,
        "validation": {
            "model": DEFAULT_MODEL,
            "revision": DEFAULT_REVISION,
            "backend": DEFAULT_BACKEND,
            "dtype": DEFAULT_DTYPE,
            "intervention_site": DEFAULT_SITE,
            "analysis_config_sha256": _canonical_hash(panels[0]["analysis_config"]),
            "cross_panel_analysis_config_match": True,
            "cross_panel_target_grid_match": True,
            "cross_panel_cell_grid_match": True,
            "conditions_per_panel": EXPECTED_CONDITIONS_PER_PANEL,
            "target_groups": list(EXPECTED_TARGET_GROUPS),
            "targets_per_group": int(expected_targets_per_group),
            "strict_protocol_parameters_enforced": bool(strict_protocol),
            "frozen_p2_target_sha256": FROZEN_P2_TARGET_SHA256,
            "frozen_p2_target_file_sha256_verified": (
                _sha256_file(frozen_target_path) if frozen_target_path is not None else None
            ),
            "ledger_target_ids_and_groups_match_frozen_bank": bool(strict_protocol),
            "pinned_parity_receipt_sha256": PINNED_PARITY_RECEIPT_SHA256,
            "all_run_receipts_complete": True,
            "all_run_input_hashes_bind_frozen_target_and_parity_receipt": True,
            "all_resolved_input_target_ids_match_ledger": True,
        },
        "parameters": parameters,
        "endpoint": {
            "condition_prototypes": "leave one complete target group out",
            "target_score": "mean same-condition cosine minus mean cross-condition cosine",
            "seed_aggregation": "arithmetic mean within target before panel adjustment",
            "adjusted_target_effect": "primary score minus median of null panels a, b, and c",
            "estimand": "mean adjusted target effect across frozen P2 targets",
        },
        "primary_results": primary_results,
        "multiplicity": {
            "method": "Holm family-wise correction",
            "family_layers": list(resolved_layers),
            "alpha": float(alpha),
        },
        "independence_boundary": {
            "effective_observation_unit": "target cluster",
            "effective_n_per_layer": len(target_groups),
            "direction_seed_replicates_per_target": len(resolved_seeds),
            "direction_seeds_averaged_within_target": True,
            "direction_seeds_counted_as_independent_observations": False,
            "conditions_counted_as_independent_observations": False,
            "matched_null_panels_counted_as_independent_observations": False,
            "bootstrap_or_sign_flip_replicates_counted_as_observations": False,
        },
        "status_definitions": {
            STATUS_ROBUST: (
                "95% bootstrap lower bound exceeds delta and the one-sided "
                "Holm-adjusted sign-flip p-value is below alpha"
            ),
            STATUS_EQUIVALENT: "the full 95% bootstrap interval lies inside [-delta, delta]",
            STATUS_UNRESOLVED: "neither prespecified rule is satisfied",
        },
        "outputs": {
            "target_effects": {
                "file": target_effects_path.name,
                "sha256": target_effects_sha256,
                "row_count": len(target_effect_rows),
            },
            "report": {
                "file": report_path.name,
                "sha256": report_sha256,
            },
        },
        "claim_boundaries": [
            (
                "Robustness is conditional on the prespecified token-count and "
                "token-prefix controls; it is not a tokenization-free glyph effect."
            ),
            (
                "Practical equivalence does not prove that tokenization caused the "
                "exploratory result."
            ),
            "Unresolved is not evidence of absence.",
            "This pre-causal endpoint does not establish semantics, mechanism, or causality.",
        ],
        "claim_stage": (
            "milestone-2-confirmatory-tokenization-control"
            if strict_protocol
            else "nonprotocol-synthetic-validation"
        ),
    }
    _write_json(receipt_path, receipt)
    return receipt


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-run", type=Path, required=True)
    parser.add_argument(
        "--matched-null-runs",
        type=Path,
        nargs=3,
        metavar=("NULL_A", "NULL_B", "NULL_C"),
        required=True,
        help="Exactly three fixed matched-null run directories, in A/B/C order",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        receipt = analyze_confirmatory(
            args.primary_run,
            args.matched_null_runs,
            output_dir=args.output_dir,
            strict_protocol=True,
        )
    except M2AnalysisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = {
        "protocol_id": PROTOCOL_ID,
        "receipt": str(Path(args.output_dir).resolve() / "m2_confirmatory_receipt.json"),
        "statuses": {
            str(result["layer"]): result["status"]
            for result in receipt["primary_results"]
        },
    }
    print(orjson.dumps(summary).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
