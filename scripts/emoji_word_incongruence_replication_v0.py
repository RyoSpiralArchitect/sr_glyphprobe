#!/usr/bin/env python3
"""Freeze and execute the T15-B prospective interaction replication.

T15-B reuses the audited T15-A execution engine under a scoped profile. The
profile replaces axes, targets, model roles, controls, counts, and frozen
assets without mutating the closed T15-A module outside the active call.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import cache
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import emoji_word_incongruence_interaction_v0 as base  # noqa: E402


PROTOCOL_ID = "glyphprobe-emoji-word-incongruence-replication-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_word_incongruence_replication_v0.yaml")
PANEL_PATH = Path("data/panels/emoji_word_incongruence_axes_v1.json")
TARGET_PATH = Path("data/targets/t15b_untouched_targets_v0.jsonl")
FREEZE_PATH = Path("data/manifests/emoji_word_incongruence_replication_v0.json")
VALIDATION_DIRECTORY = Path("validation/emoji_word_incongruence_replication_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
PREFLIGHT_AGGREGATE_NAME = "aggregate.json"
SITE_INDICES = base.SITE_INDICES
POLARITIES = base.POLARITIES
SOURCE_ORDERS = base.SOURCE_ORDERS
DIRECTION_KINDS = base.DIRECTION_KINDS
SHARD_KINDS = base.SHARD_KINDS
DESIGN_ASSETS = (
    "configs/emoji_word_incongruence_replication_v0.yaml",
    "data/panels/emoji_word_incongruence_axes_v1.json",
    "data/targets/t15b_untouched_targets_v0.jsonl",
    "docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md",
    "docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md",
    "scripts/emoji_word_incongruence_replication_v0.py",
    "scripts/analyze_emoji_word_incongruence_replication_v0.py",
    "scripts/emoji_word_incongruence_interaction_v0.py",
    "scripts/analyze_emoji_word_incongruence_interaction_v0.py",
    "scripts/emoji_steering_specificity_harvest_v0.py",
    "scripts/semantic_atlas_cross_model_replication_v0.py",
    "scripts/mistral7b_semantic_atlas_v0.py",
    "tests/test_emoji_word_incongruence_replication_v0.py",
    "tests/test_analyze_emoji_word_incongruence_replication_v0.py",
    "validation/emoji_word_incongruence_replication_v0/design_preflight.json",
)
FROZEN_ASSETS = (*DESIGN_ASSETS, str(TOKENIZER_PREFLIGHT_PATH))


class ReplicationError(RuntimeError):
    """Raised when the prospective T15-B contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReplicationError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return base._sha256(path)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@cache
def _config() -> dict[str, Any]:
    value = base.atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T15-B protocol mismatch")
    return value


@cache
def panel() -> dict[str, Any]:
    value = base._read_json(_root() / PANEL_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T15-B panel mismatch")
    return value


@cache
def axes() -> tuple[dict[str, Any], ...]:
    value = tuple(panel()["axes"])
    expected = tuple(str(item) for item in panel()["axis_order"])
    _require(tuple(str(row["id"]) for row in value) == expected, "Axis order changed")
    return value


@cache
def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


@cache
def wrappers() -> tuple[dict[str, str], ...]:
    selected = tuple(base.t13.wrappers())
    expected = tuple(
        str(value) for value in _config()["source_bindings"]["wrappers"]["selected_ids"]
    )
    _require(tuple(row["id"] for row in selected) == expected, "Wrapper order changed")
    return selected


@cache
def targets() -> tuple[dict[str, str], ...]:
    binding = _config()["source_bindings"]["untouched_targets"]
    path = _root() / str(binding["path"])
    _require(path == _root() / TARGET_PATH, "T15-B target path changed")
    _require(path.is_file(), "T15-B target bank missing")
    _require(_sha256(path) == str(binding["sha256"]), "T15-B target bank changed")
    rows = base._read_jsonl(path)
    _require(len(rows) == int(binding["expected_rows"]), "Target count changed")
    return tuple(
        {
            "id": str(row["id"]),
            "group": str(row["group"]),
            "prompt": str(row["prompt"]),
        }
        for row in rows
    )


def _expected_counts() -> dict[str, int]:
    axis_count = len(axes())
    orders = len(SOURCE_ORDERS)
    folds = len(wrappers())
    sites = len(SITE_INDICES)
    signs = len(_config()["intervention"]["signs"])
    magnitudes = len(_config()["intervention"]["magnitudes"])
    target_count = len(targets())
    shifts = len(panel()["cross_axis_cyclic_shifts"])
    source_prompts = (
        orders * folds
        + 2 * axis_count * len(POLARITIES) * orders * folds
        + axis_count * len(POLARITIES) ** 2 * orders * folds
        + axis_count * shifts * len(POLARITIES) ** 2 * orders * folds
    )
    source_metrics = (
        axis_count
        * (1 + shifts)
        * len(POLARITIES) ** 2
        * orders
        * folds
        * sites
    )
    directions = axis_count * (3 + shifts) * orders * folds * sites
    base_rows = (
        axis_count * orders * folds * sites * signs * magnitudes * target_count
    )
    true_rows = base_rows
    cross_rows = base_rows * shifts
    emoji_rows = base_rows
    word_rows = base_rows
    zero_rows = sites * target_count
    per_model = true_rows + cross_rows + emoji_rows + word_rows + zero_rows
    return {
        "source_prompts": source_prompts,
        "source_metric_rows": source_metrics,
        "direction_catalog_rows": directions,
        "true_conflict_rows": true_rows,
        "cross_axis_null_rows": cross_rows,
        "emoji_main_rows": emoji_rows,
        "word_main_rows": word_rows,
        "zero_rows": zero_rows,
        "rows_per_model": per_model,
        "rows_total": per_model * len(model_roles()),
    }


def _bound_input_hashes() -> dict[str, str]:
    observed: dict[str, str] = {}
    for key, binding in _config()["source_bindings"].items():
        if not isinstance(binding, Mapping) or "path" not in binding:
            continue
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T15-B bound input missing: {key}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T15-B input changed: {key}")
        observed[str(key)] = actual
    return observed


def _old_axis_items() -> tuple[set[str], set[str]]:
    old = base._read_json(
        _root() / "data/panels/emoji_word_incongruence_axes_v0.json"
    )
    emoji = {
        str(axis[pole]["emoji"])
        for axis in old["axes"]
        for pole in POLARITIES
    }
    words = {
        str(axis[pole]["word"]).casefold()
        for axis in old["axes"]
        for pole in POLARITIES
    }
    return emoji, words


def _audit_target_bank() -> dict[str, Any]:
    rows = targets()
    ids = [row["id"] for row in rows]
    prompts = [row["prompt"] for row in rows]
    _require(len(ids) == len(set(ids)), "T15-B target IDs are not unique")
    _require(len(prompts) == len(set(prompts)), "T15-B target prompts are not unique")
    _require(all(value.startswith("t15b_") for value in ids), "Target ID namespace changed")
    expected_groups = tuple(
        str(value)
        for value in _config()["source_bindings"]["untouched_targets"][
            "expected_groups"
        ]
    )
    counts = Counter(row["group"] for row in rows)
    expected_per_group = int(
        _config()["source_bindings"]["untouched_targets"]["rows_per_group"]
    )
    _require(
        tuple(counts) == expected_groups
        and counts == {group: expected_per_group for group in expected_groups},
        "T15-B target groups changed",
    )
    old_emoji, old_words = _old_axis_items()
    new_emoji = {
        str(axis[pole]["emoji"])
        for axis in axes()
        for pole in POLARITIES
    }
    new_words = {
        str(axis[pole]["word"]).casefold()
        for axis in axes()
        for pole in POLARITIES
    }
    forbidden_emoji = old_emoji | new_emoji
    forbidden_words = old_words | new_words
    for row in rows:
        prompt = row["prompt"]
        lower = prompt.casefold()
        _require(
            not any(glyph in prompt for glyph in forbidden_emoji),
            f"Target contains axis emoji: {row['id']}",
        )
        _require(
            not any(
                re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", lower)
                for word in forbidden_words
            ),
            f"Target contains axis word: {row['id']}",
        )
    return {
        "target_rows": len(rows),
        "target_groups": dict(counts),
        "target_ids_sha256": _canonical_sha256(ids),
        "target_prompts_sha256": _canonical_sha256(prompts),
        "axis_lexical_overlap": 0,
    }


def _audit_design_impl() -> dict[str, Any]:
    observed = _bound_input_hashes()
    _require(len(axes()) == 8, "T15-B axis count changed")
    _require(
        tuple(int(value) for value in panel()["cross_axis_cyclic_shifts"])
        == (1, 2, 3, 4, 5, 6, 7),
        "T15-B control shifts changed",
    )
    _require(
        model_roles()
        == ("smollm2_1p7b_base_bf16", "mistral7b_instruct_v03_bf16"),
        "T15-B model roster changed",
    )
    _require(set(model_roles()).issubset(base.t13.model_roles()), "Unknown model role")
    old_config = base.atlas._read_yaml(
        _root() / "configs/emoji_word_incongruence_interaction_v0.yaml"
    )
    _require(
        not set(model_roles()).intersection(old_config["models"]["order"]),
        "T15-B model role overlaps T15-A",
    )
    old_emoji, old_words = _old_axis_items()
    new_emoji = {
        str(axis[pole]["emoji"])
        for axis in axes()
        for pole in POLARITIES
    }
    new_words = {
        str(axis[pole]["word"]).casefold()
        for axis in axes()
        for pole in POLARITIES
    }
    _require(not old_emoji.intersection(new_emoji), "T15-B emoji overlap T15-A")
    _require(not old_words.intersection(new_words), "T15-B word overlap T15-A")
    _require(
        len(new_emoji) == len(new_words) == 16,
        "T15-B axis identities are not unique",
    )
    target_audit = _audit_target_bank()
    _require(
        tuple(float(value) for value in _config()["source_capture"]["depth_fractions"])
        == (0.875, 1.0),
        "T15-B depths changed",
    )
    _require(
        tuple(float(value) for value in _config()["intervention"]["magnitudes"])
        == (0.125, 0.25),
        "T15-B magnitudes changed",
    )
    _require(len(targets()) == 48, "T15-B target count changed")
    storage = base.t13._config()["pilot"]["response_storage"]
    _require(
        int(_config()["storage"]["top_positive_and_negative_logit_deltas"])
        == int(storage["top_positive_and_negative_logit_deltas"]),
        "T15-B top-k storage differs from runtime helper",
    )
    _require(
        int(_config()["storage"]["countsketch_dimension"])
        == int(storage["countsketch_dimension"])
        and int(_config()["storage"]["countsketch_seed"])
        == int(storage["countsketch_seed"]),
        "T15-B CountSketch contract differs from runtime helper",
    )
    _require(
        _config()["runtime"]["critical_versions"]
        == base.t13._config()["runtime"]["critical_versions"],
        "T15-B critical versions differ from runtime helper",
    )
    base._audit_lexical_balance()
    counts = _expected_counts()
    _require(
        len(base.source_prompt_records()) == counts["source_prompts"],
        "T15-B source prompt arithmetic changed",
    )
    grid = _config()["grids"]
    for key, value in (
        ("true_conflict_rows_per_model", counts["true_conflict_rows"]),
        ("cross_axis_null_rows_per_model", counts["cross_axis_null_rows"]),
        ("emoji_main_rows_per_model", counts["emoji_main_rows"]),
        ("word_main_rows_per_model", counts["word_main_rows"]),
        ("zero_rows_per_model", counts["zero_rows"]),
        ("expected_rows_per_model", counts["rows_per_model"]),
        ("expected_rows_total", counts["rows_total"]),
    ):
        _require(int(grid[key]) == value, f"T15-B grid arithmetic changed: {key}")
    _require(
        int(_config()["source_capture"]["expected_prompt_sequences_per_model"])
        == counts["source_prompts"],
        "T15-B source count binding changed",
    )
    _require(
        int(_config()["source_capture"]["expected_source_metric_rows_per_model"])
        == counts["source_metric_rows"],
        "T15-B source metric binding changed",
    )
    _require(
        int(_config()["source_capture"]["expected_direction_catalog_rows_per_model"])
        == counts["direction_catalog_rows"],
        "T15-B direction binding changed",
    )
    closeout = base._read_json(
        _root() / str(_config()["source_bindings"]["t15a_closeout"]["path"])
    )
    _require(
        closeout.get("interval_class_counts", {})
        .get("A1_primary_shared_response_fingerprint", {})
        .get("positive")
        == 16,
        "T15-A source candidate binding changed",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t15b_model_forwards",
        "bound_inputs": observed,
        "model_roles": list(model_roles()),
        "t15a_model_role_overlap": 0,
        "axis_ids": [axis["id"] for axis in axes()],
        "source_orders": list(SOURCE_ORDERS),
        "wrapper_ids": [row["id"] for row in wrappers()],
        "target_audit": target_audit,
        "counts": counts,
        "model_forwards": 0,
        "replication_decision_available": False,
        "semantic_understanding_claim_authorized": False,
        "causal_claim_authorized": False,
    }


_PATCHED_BASE_NAMES = (
    "PROTOCOL_ID",
    "SCHEMA_VERSION",
    "CONFIG_PATH",
    "PANEL_PATH",
    "FREEZE_PATH",
    "VALIDATION_DIRECTORY",
    "DESIGN_PREFLIGHT_PATH",
    "TOKENIZER_PREFLIGHT_PATH",
    "PREFLIGHT_AGGREGATE_NAME",
    "DESIGN_ASSETS",
    "FROZEN_ASSETS",
    "_config",
    "panel",
    "axes",
    "model_roles",
    "wrappers",
    "targets",
    "_expected_counts",
    "_bound_input_hashes",
    "audit_design",
    "_direction_groups",
)


@contextmanager
def profile_scope() -> Iterator[None]:
    saved = {name: getattr(base, name) for name in _PATCHED_BASE_NAMES}
    saved_t13_targets = base.t13.targets
    base.source_prompt_records.cache_clear()
    replacements = {
        "PROTOCOL_ID": PROTOCOL_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "CONFIG_PATH": CONFIG_PATH,
        "PANEL_PATH": PANEL_PATH,
        "FREEZE_PATH": FREEZE_PATH,
        "VALIDATION_DIRECTORY": VALIDATION_DIRECTORY,
        "DESIGN_PREFLIGHT_PATH": DESIGN_PREFLIGHT_PATH,
        "TOKENIZER_PREFLIGHT_PATH": TOKENIZER_PREFLIGHT_PATH,
        "PREFLIGHT_AGGREGATE_NAME": PREFLIGHT_AGGREGATE_NAME,
        "DESIGN_ASSETS": DESIGN_ASSETS,
        "FROZEN_ASSETS": FROZEN_ASSETS,
        "_config": _config,
        "panel": panel,
        "axes": axes,
        "model_roles": model_roles,
        "wrappers": wrappers,
        "targets": targets,
        "_expected_counts": _expected_counts,
        "_bound_input_hashes": _bound_input_hashes,
        "audit_design": _audit_design_impl,
        "_direction_groups": _direction_groups_impl,
    }
    for name, value in replacements.items():
        setattr(base, name, value)
    base.t13.targets = lambda: [dict(row) for row in targets()]
    try:
        yield
    finally:
        base.source_prompt_records.cache_clear()
        base.t13.targets = saved_t13_targets
        for name, value in saved.items():
            setattr(base, name, value)


def audit_design() -> dict[str, Any]:
    with profile_scope():
        return _audit_design_impl()


def source_prompt_records() -> tuple[dict[str, Any], ...]:
    with profile_scope():
        return base.source_prompt_records()


def _target_directory(output_root: Path, role: str) -> Path:
    return output_root / role / "target"


def _run_target_capture(
    *,
    role: str,
    output_root: Path,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
) -> Path:
    final = _target_directory(output_root, role)
    if final.exists():
        _validate_target_capture(final, role)
        return final
    base._yield_if_contended(output_root, role, "before_target_capture")
    stage, final = base.t13._atomic_directory(final)
    target_rows = targets()
    prompts = [row["prompt"] for row in target_rows]
    sites = [int(value) for value in base.t13.layer_indices(role)]
    started = time.perf_counter()
    activations, _, token_counts, batch_calls = base.t13._capture_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        prompts=prompts,
        batch_size=1,
    )
    np.save(stage / "target_activations.npy", activations, allow_pickle=False)
    metadata = {
        "target_ids": [row["id"] for row in target_rows],
        "target_groups": [row["group"] for row in target_rows],
        "target_prompt_sha256": [
            hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
            for row in target_rows
        ],
        "target_token_counts": [int(value) for value in token_counts],
        "block_indices": sites,
        "depth_fractions": _config()["target_capture"][
            "normalized_depth_fractions"
        ],
        "prompt_bodies_stored": False,
    }
    base._write_json(stage / "metadata.json", metadata)
    files = base.t13._directory_file_bindings(
        stage, ("target_activations.npy", "metadata.json")
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "target_capture_complete",
        "model_role": role,
        "target_sequences": len(target_rows),
        "batched_model_invocations": batch_calls,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    base.t13._seal_directory(stage, final, receipt)
    _validate_target_capture(final, role)
    return final


def _validate_target_capture(directory: Path, role: str) -> dict[str, Any]:
    receipt = base._read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Target receipt mismatch")
    _require(receipt.get("model_role") == role, "Target role changed")
    _require(receipt.get("status") == "target_capture_complete", "Target incomplete")
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and _sha256(path) == binding["sha256"],
            f"Target capture file changed: {name}",
        )
    width = int(base.t10._model_spec(role)["expected_model_dim"])
    value = np.load(
        directory / "target_activations.npy", mmap_mode="r", allow_pickle=False
    )
    _require(
        value.shape == (len(targets()), 8, width),
        "Target activation shape changed",
    )
    _require(str(value.dtype) == "float32", "Target activation dtype changed")
    _require(bool(np.isfinite(value).all()), "Target activations are nonfinite")
    metadata = base._read_json(directory / "metadata.json")
    _require(
        metadata["target_ids"] == [row["id"] for row in targets()],
        "Target ID order changed",
    )
    _require(metadata.get("prompt_bodies_stored") is False, "Prompt body leaked")
    _require(
        metadata["target_prompt_sha256"]
        == [
            hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
            for row in targets()
        ],
        "Target prompt hashes changed",
    )
    return {"status": "pass", "model_role": role, "target_rows": len(targets())}


def _target_rms(directory: Path) -> np.ndarray:
    values = np.load(directory / "target_activations.npy", allow_pickle=False)
    rms = np.sqrt(np.mean(np.square(values, dtype=np.float64), axis=-1))
    _require(
        rms.shape == (len(targets()), 8)
        and bool(np.isfinite(rms).all())
        and bool((rms > 0).all()),
        "T15-B target RMS changed",
    )
    return rms


def _direction_groups_impl(
    role: str,
    kind: str,
    site_index: int,
    source_directory: Path,
    target_rms: np.ndarray,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    catalog = base._read_jsonl(source_directory / "direction_catalog.jsonl")
    directions = np.load(source_directory / "directions.npy", allow_pickle=False)
    selected = [
        row
        for row in catalog
        if row["direction_kind"] == kind and int(row["site_index"]) == site_index
    ]
    repeats = len(axes()) * len(SOURCE_ORDERS) * len(wrappers())
    expected = (
        repeats * len(panel()["cross_axis_cyclic_shifts"])
        if kind == "cross_axis_null"
        else repeats
    )
    _require(len(selected) == expected, f"Direction count changed: {kind}/{site_index}")
    floor = float(_config()["intervention"]["degeneracy_floor_rms"])
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        vectors: list[np.ndarray] = []
        for row in selected:
            raw = directions[int(row["direction_index"])]
            rms = float(row["source_direction_rms"])
            unit = np.zeros_like(raw) if rms <= floor else raw / rms
            for magnitude in _config()["intervention"]["magnitudes"]:
                for sign in _config()["intervention"]["signs"]:
                    metadata.append(
                        {
                            **{
                                key: value
                                for key, value in row.items()
                                if key != "direction_index"
                            },
                            "condition_kind": kind,
                            "magnitude": float(magnitude),
                            "sign": int(sign),
                            "target_index": target_index,
                            "target_id": target["id"],
                            "target_group": target["group"],
                        }
                    )
                    vectors.append(
                        unit
                        * float(magnitude)
                        * int(sign)
                        * float(target_rms[target_index, site_index])
                    )
        groups.append(
            (site_index, target_index, metadata, np.stack(vectors).astype(np.float32))
        )
    return groups


def _run_role_impl(
    *,
    role: str,
    output_root: Path,
    model_preflight_directory: Path,
    tokenizer_preflight_directory: Path,
    model_path: Path | None,
) -> dict[str, Any]:
    base.audit_freeze()
    base.audit_preflight(tokenizer_preflight_directory)
    _require(role in model_roles(), f"Unknown T15-B role: {role}")
    summary_path = output_root / role / "summary.json"
    if summary_path.is_file():
        return _validate_role_impl(role, output_root)
    base._yield_if_contended(output_root, role, "before_model_load")
    snapshot = base._locate_snapshot(role, model_path).resolve()
    torch, tokenizer, model, model_receipt = base.t13._load_model(
        role, snapshot, model_preflight_directory
    )
    base._validate_runtime_tokenizer(
        role, tokenizer, snapshot, tokenizer_preflight_directory
    )
    blocks = base.t10._resolve_attr(
        model, str(base.t10._model_spec(role)["expected_block_path"])
    )
    started = time.perf_counter()
    target_directory = _run_target_capture(
        role=role,
        output_root=output_root,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
    )
    source_directory = base._run_source_capture(
        role=role,
        output_root=output_root,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
    )
    target_rms = _target_rms(target_directory)
    rows_total = 0
    zero_bounds: dict[str, dict[str, float]] = {}
    for site_index in SITE_INDICES:
        zero = base._execute_groups(
            role=role,
            kind="zero",
            site_index=site_index,
            output_root=output_root,
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            blocks=blocks,
            groups=base._zero_groups(role, site_index),
        )
        zero_bounds[str(site_index)] = base._validate_zero_values(zero)
        rows_total += base._expected_shard_rows("zero")
        for kind in DIRECTION_KINDS:
            base._execute_groups(
                role=role,
                kind=kind,
                site_index=site_index,
                output_root=output_root,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                groups=_direction_groups_impl(
                    role, kind, site_index, source_directory, target_rms
                ),
            )
            rows_total += base._expected_shard_rows(kind)
    _require(rows_total == _expected_counts()["rows_per_model"], "Role total changed")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "response_rows": rows_total,
        "source_prompt_sequences": len(base.source_prompt_records()),
        "target_sequences": len(targets()),
        "generation_calls": 0,
        "zero_hook_bounds": zero_bounds,
        "model_receipt": model_receipt,
        "target_capture_receipt_sha256": _sha256(target_directory / "receipt.json"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "elapsed_seconds_this_process": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    base._write_json(summary_path, summary)
    result = _validate_role_impl(role, output_root)
    del model
    torch.cuda.empty_cache()
    return result


_BASE_VALIDATE_ROLE = base.validate_role


def _validate_role_impl(role: str, output_root: Path) -> dict[str, Any]:
    result = _BASE_VALIDATE_ROLE(role, output_root)
    target = _validate_target_capture(_target_directory(output_root, role), role)
    summary = base._read_json(output_root / role / "summary.json")
    _require(int(summary.get("target_sequences")) == len(targets()), "Target summary changed")
    return {**result, "target_rows": int(target["target_rows"])}


def _audit_run_impl(output_root: Path) -> dict[str, Any]:
    base.audit_freeze()
    results = [_validate_role_impl(role, output_root) for role in model_roles()]
    total = sum(int(row["response_rows"]) for row in results)
    _require(total == _expected_counts()["rows_total"], "T15-B run total changed")
    return {
        "status": "complete_closed_to_adaptive_selection",
        "protocol_id": PROTOCOL_ID,
        "roles_complete": len(results),
        "response_rows": total,
        "source_prompt_sequences": len(base.source_prompt_records()) * len(results),
        "target_sequences": len(targets()) * len(results),
        "scientific_open_authorized": True,
        "replication_decision_available": True,
        "semantic_understanding_claim_authorized": False,
        "causal_claim_authorized": False,
        "generation_calls": 0,
    }


def run_role(
    *,
    role: str,
    output_root: Path,
    model_preflight_directory: Path,
    tokenizer_preflight_directory: Path,
    model_path: Path | None = None,
) -> dict[str, Any]:
    with profile_scope():
        return _run_role_impl(
            role=role,
            output_root=output_root,
            model_preflight_directory=model_preflight_directory,
            tokenizer_preflight_directory=tokenizer_preflight_directory,
            model_path=model_path,
        )


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    with profile_scope():
        return _validate_role_impl(role, output_root)


def audit_run(output_root: Path) -> dict[str, Any]:
    with profile_scope():
        return _audit_run_impl(output_root)


def _source_directory(output_root: Path, role: str) -> Path:
    return base._source_directory(output_root, role)


def _response_directory(
    output_root: Path, role: str, kind: str, site_index: int
) -> Path:
    return base._response_directory(output_root, role, kind, site_index)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    design = commands.add_parser("write-design-preflight")
    design.add_argument("--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH)
    token = commands.add_parser("preflight-role")
    token.add_argument("--role", required=True, choices=model_roles())
    token.add_argument("--output", required=True, type=Path)
    token.add_argument("--model-path", type=Path)
    aggregate = commands.add_parser("aggregate-preflight")
    aggregate.add_argument("--directory", required=True, type=Path)
    aggregate.add_argument("--output", required=True, type=Path)
    audit_preflight = commands.add_parser("audit-preflight")
    audit_preflight.add_argument("--directory", required=True, type=Path)
    audit_preflight.add_argument("--without-frozen-binding", action="store_true")
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    commands.add_parser("audit-freeze")
    run = commands.add_parser("run-role")
    run.add_argument("--role", required=True, choices=model_roles())
    run.add_argument("--output-root", required=True, type=Path)
    run.add_argument("--model-preflight-directory", required=True, type=Path)
    run.add_argument("--tokenizer-preflight-directory", required=True, type=Path)
    run.add_argument("--model-path", type=Path)
    run_all = commands.add_parser("run-all")
    run_all.add_argument("--output-root", required=True, type=Path)
    run_all.add_argument("--model-preflight-directory", required=True, type=Path)
    run_all.add_argument("--tokenizer-preflight-directory", required=True, type=Path)
    validate = commands.add_parser("validate-role")
    validate.add_argument("--role", required=True, choices=model_roles())
    validate.add_argument("--output-root", required=True, type=Path)
    audit = commands.add_parser("audit-run")
    audit.add_argument("--output-root", required=True, type=Path)
    return value


def main() -> None:
    args = parser().parse_args()
    with profile_scope():
        if args.command == "audit-design":
            result = _audit_design_impl()
        elif args.command == "write-design-preflight":
            result = base.write_design_preflight(args.output)
        elif args.command == "preflight-role":
            result = base.preflight_role(args.role, args.output, args.model_path)
        elif args.command == "aggregate-preflight":
            result = base.aggregate_preflight(args.directory, args.output)
        elif args.command == "audit-preflight":
            result = base.audit_preflight(
                args.directory,
                require_frozen_binding=not args.without_frozen_binding,
            )
        elif args.command == "freeze":
            result = base.freeze(args.output)
        elif args.command == "audit-freeze":
            result = base.audit_freeze()
        elif args.command == "run-role":
            result = _run_role_impl(
                role=args.role,
                output_root=args.output_root,
                model_preflight_directory=args.model_preflight_directory,
                tokenizer_preflight_directory=args.tokenizer_preflight_directory,
                model_path=args.model_path,
            )
        elif args.command == "run-all":
            for role in model_roles():
                _run_role_impl(
                    role=role,
                    output_root=args.output_root,
                    model_preflight_directory=args.model_preflight_directory,
                    tokenizer_preflight_directory=args.tokenizer_preflight_directory,
                    model_path=None,
                )
            result = _audit_run_impl(args.output_root)
        elif args.command == "validate-role":
            result = _validate_role_impl(args.role, args.output_root)
        else:
            result = _audit_run_impl(args.output_root)
    base._print(result)


if __name__ == "__main__":
    main()
