#!/usr/bin/env python3
"""Freeze and execute the T15-A emoji × word interaction atlas.

The executor keeps source capture, steering, and scientific aggregation
separate. Scientific values may be inspected only after every frozen model
role validates.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
import hashlib
import json
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


PROTOCOL_ID = "glyphprobe-emoji-word-incongruence-interaction-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_word_incongruence_interaction_v0.yaml")
PANEL_PATH = Path("data/panels/emoji_word_incongruence_axes_v0.json")
FREEZE_PATH = Path("data/manifests/emoji_word_incongruence_interaction_v0.json")
VALIDATION_DIRECTORY = Path("validation/emoji_word_incongruence_interaction_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
PREFLIGHT_AGGREGATE_NAME = "aggregate.json"
SITE_INDICES = (6, 7)
POLARITIES = ("positive", "negative")
SOURCE_ORDERS = ("emoji_then_word", "word_then_emoji")
DIRECTION_KINDS = (
    "true_conflict",
    "cross_axis_null",
    "emoji_main",
    "word_main",
)
SHARD_KINDS = (*DIRECTION_KINDS, "zero")
DESIGN_ASSETS = (
    "configs/emoji_word_incongruence_interaction_v0.yaml",
    "data/panels/emoji_word_incongruence_axes_v0.json",
    "docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md",
    "docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md",
    "scripts/emoji_word_incongruence_interaction_v0.py",
    "scripts/analyze_emoji_word_incongruence_interaction_v0.py",
    "tests/test_emoji_word_incongruence_interaction_v0.py",
    "tests/test_analyze_emoji_word_incongruence_interaction_v0.py",
    "validation/emoji_word_incongruence_interaction_v0/design_preflight.json",
)
FROZEN_ASSETS = (*DESIGN_ASSETS, str(TOKENIZER_PREFLIGHT_PATH))


class InteractionError(RuntimeError):
    """Raised when the T15-A contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InteractionError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@cache
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T15-A protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    return atlas._sha256(path)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                _require(isinstance(value, dict), f"JSONL row is not an object: {path}")
                rows.append(value)
    return rows


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
            )
    os.replace(temporary, path)


@cache
def panel() -> dict[str, Any]:
    value = _read_json(_root() / PANEL_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T15-A panel mismatch")
    return value


@cache
def axes() -> tuple[dict[str, Any], ...]:
    value = tuple(panel()["axes"])
    order = tuple(str(item) for item in panel()["axis_order"])
    _require(tuple(str(row["id"]) for row in value) == order, "Axis order changed")
    return value


@cache
def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


@cache
def wrappers() -> tuple[dict[str, str], ...]:
    selected = tuple(t13.wrappers())
    expected = tuple(
        str(value) for value in _config()["source_bindings"]["wrappers"]["selected_ids"]
    )
    _require(tuple(row["id"] for row in selected) == expected, "Wrapper order changed")
    return selected


@cache
def targets() -> tuple[dict[str, str], ...]:
    return tuple(t13.targets())


def _frame(order: str, emoji: str, word: str) -> str:
    _require(order in SOURCE_ORDERS, f"Unknown source order: {order}")
    template = str(_config()["factorial"]["source_frames"][order])
    return template.format(emoji=emoji, word=word)


def _source_prompt(order: str, emoji: str, word: str, wrapper_text: str) -> str:
    return f"{_frame(order, emoji, word)}\n{wrapper_text}"


@cache
def source_prompt_records() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []

    def append(kind: str, order: str, wrapper_index: int, **metadata: Any) -> None:
        emoji = str(metadata.pop("emoji", ""))
        word = str(metadata.pop("word", ""))
        wrapper = wrappers()[wrapper_index]
        row = {
            "source_index": len(rows),
            "source_kind": kind,
            "source_order": order,
            "wrapper_index": wrapper_index,
            "wrapper_id": wrapper["id"],
            **metadata,
        }
        row["text"] = _source_prompt(order, emoji, word, wrapper["text"])
        rows.append(row)

    for order in SOURCE_ORDERS:
        for wrapper_index in range(len(wrappers())):
            append("frame", order, wrapper_index)

    for order in SOURCE_ORDERS:
        for wrapper_index in range(len(wrappers())):
            for axis in axes():
                for polarity in POLARITIES:
                    append(
                        "emoji_component",
                        order,
                        wrapper_index,
                        axis_id=axis["id"],
                        emoji_polarity=polarity,
                        emoji=axis[polarity]["emoji"],
                    )
                    append(
                        "word_component",
                        order,
                        wrapper_index,
                        axis_id=axis["id"],
                        word_axis_id=axis["id"],
                        word_polarity=polarity,
                        word=axis[polarity]["word"],
                    )

    for order in SOURCE_ORDERS:
        for wrapper_index in range(len(wrappers())):
            for axis in axes():
                for emoji_polarity in POLARITIES:
                    for word_polarity in POLARITIES:
                        append(
                            "core_pair",
                            order,
                            wrapper_index,
                            axis_id=axis["id"],
                            word_axis_id=axis["id"],
                            emoji_polarity=emoji_polarity,
                            word_polarity=word_polarity,
                            congruence=(
                                "congruent"
                                if emoji_polarity == word_polarity
                                else "incongruent"
                            ),
                            emoji=axis[emoji_polarity]["emoji"],
                            word=axis[word_polarity]["word"],
                        )

    shifts = tuple(int(value) for value in panel()["cross_axis_cyclic_shifts"])
    for order in SOURCE_ORDERS:
        for wrapper_index in range(len(wrappers())):
            for axis_index, axis in enumerate(axes()):
                for shift in shifts:
                    word_axis = axes()[(axis_index + shift) % len(axes())]
                    for emoji_polarity in POLARITIES:
                        for word_polarity in POLARITIES:
                            append(
                                "cross_pair",
                                order,
                                wrapper_index,
                                axis_id=axis["id"],
                                word_axis_id=word_axis["id"],
                                shift=shift,
                                emoji_polarity=emoji_polarity,
                                word_polarity=word_polarity,
                                checkerboard_class=(
                                    "diagonal"
                                    if emoji_polarity == word_polarity
                                    else "off_diagonal"
                                ),
                                emoji=axis[emoji_polarity]["emoji"],
                                word=word_axis[word_polarity]["word"],
                            )
    _require(
        len(rows)
        == int(_config()["source_capture"]["expected_prompt_sequences_per_model"]),
        "T15-A source prompt count changed",
    )
    return tuple(rows)


def _expected_counts() -> dict[str, int]:
    axis_count = len(axes())
    orders = len(SOURCE_ORDERS)
    folds = len(wrappers())
    sites = len(SITE_INDICES)
    signs = len(_config()["intervention"]["signs"])
    magnitudes = len(_config()["intervention"]["magnitudes"])
    target_count = len(targets())
    shifts = len(panel()["cross_axis_cyclic_shifts"])
    base = axis_count * orders * folds * sites * signs * magnitudes * target_count
    true_rows = base
    cross_rows = base * shifts
    emoji_rows = base
    word_rows = base
    zero_rows = sites * target_count
    per_model = true_rows + cross_rows + emoji_rows + word_rows + zero_rows
    return {
        "source_prompts": len(source_prompt_records()),
        "source_metric_rows": 2048,
        "direction_catalog_rows": 768,
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
    for key in (
        "wrappers",
        "public_targets",
        "t13_harvest_config",
        "t13_harvest_freeze",
        "t13_scientific_open_closeout",
        "t14_closeout",
        "t14xa_closeout",
    ):
        binding = _config()["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T15-A bound input missing: {key}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T15-A input changed: {key}")
        observed[key] = actual
    observed["axes"] = _sha256(_root() / PANEL_PATH)
    return observed


def _audit_lexical_balance() -> None:
    core = [row for row in source_prompt_records() if row["source_kind"] == "core_pair"]
    for axis in axes():
        axis_rows = [row for row in core if row["axis_id"] == axis["id"]]
        for order in SOURCE_ORDERS:
            for wrapper_index in range(len(wrappers())):
                cell = [
                    row
                    for row in axis_rows
                    if row["source_order"] == order
                    and row["wrapper_index"] == wrapper_index
                ]
                _require(len(cell) == 4, "T15-A core factorial cell count changed")
                emoji_counts = Counter(row["emoji_polarity"] for row in cell)
                word_counts = Counter(row["word_polarity"] for row in cell)
                class_counts = Counter(row["congruence"] for row in cell)
                _require(
                    emoji_counts == {"positive": 2, "negative": 2},
                    "Emoji balance changed",
                )
                _require(
                    word_counts == {"positive": 2, "negative": 2},
                    "Word balance changed",
                )
                _require(
                    class_counts == {"congruent": 2, "incongruent": 2},
                    "Class balance changed",
                )


def audit_design() -> dict[str, Any]:
    observed = _bound_input_hashes()
    _require(len(axes()) == 8, "T15-A axis count changed")
    _require(
        tuple(panel()["cross_axis_cyclic_shifts"]) == (1, 3, 5),
        "Control shifts changed",
    )
    _require(
        len(model_roles()) == 4 and len(set(model_roles())) == 4, "Model roster changed"
    )
    _require(set(model_roles()).issubset(t13.model_roles()), "Unknown T15-A model role")
    _require(
        tuple(float(v) for v in _config()["source_capture"]["depth_fractions"])
        == (0.875, 1.0),
        "Depths changed",
    )
    _require(
        tuple(float(v) for v in _config()["intervention"]["magnitudes"])
        == (0.125, 0.25),
        "Magnitudes changed",
    )
    _require(len(targets()) == 32, "Public target count changed")
    _require(
        [row["id"] for row in targets()] == [row["id"] for row in t13.targets()],
        "T15-A target order differs from the T13 runtime helper",
    )
    t13_storage = t13._config()["pilot"]["response_storage"]
    _require(
        int(_config()["storage"]["top_positive_and_negative_logit_deltas"])
        == int(t13_storage["top_positive_and_negative_logit_deltas"]),
        "T15-A top-k storage differs from the T13 runtime helper",
    )
    _require(
        int(_config()["storage"]["countsketch_dimension"])
        == int(t13_storage["countsketch_dimension"])
        and int(_config()["storage"]["countsketch_seed"])
        == int(t13_storage["countsketch_seed"]),
        "T15-A CountSketch contract differs from the T13 runtime helper",
    )
    _require(
        _config()["runtime"]["critical_versions"]
        == t13._config()["runtime"]["critical_versions"],
        "T15-A critical versions differ from the T13 runtime helper",
    )
    _audit_lexical_balance()
    counts = _expected_counts()
    grid = _config()["grids"]
    for key, observed_value in (
        ("true_conflict_rows_per_model", counts["true_conflict_rows"]),
        ("cross_axis_null_rows_per_model", counts["cross_axis_null_rows"]),
        ("emoji_main_rows_per_model", counts["emoji_main_rows"]),
        ("word_main_rows_per_model", counts["word_main_rows"]),
        ("zero_rows_per_model", counts["zero_rows"]),
        ("expected_rows_per_model", counts["rows_per_model"]),
        ("expected_rows_total", counts["rows_total"]),
    ):
        _require(
            int(grid[key]) == observed_value, f"T15-A grid arithmetic changed: {key}"
        )
    t14 = _read_json(
        _root() / str(_config()["source_bindings"]["t14_closeout"]["path"])
    )
    _require(
        t14.get("status") == "complete_with_negative_causal_iut",
        "T14 closeout status changed",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t15_model_forwards",
        "bound_inputs": observed,
        "model_roles": list(model_roles()),
        "axis_ids": [axis["id"] for axis in axes()],
        "source_orders": list(SOURCE_ORDERS),
        "wrapper_ids": [row["id"] for row in wrappers()],
        "counts": counts,
        "model_forwards": 0,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    value = audit_design()
    _write_json(output, value)
    return value


def _locate_snapshot(role: str, model_path: Path | None) -> Path:
    return (
        model_path if model_path is not None else t13.t11._locate_local_snapshot(role)
    )


def _tokenizer_receipt(
    role: str, snapshot: Path, tokenizer: Any | None = None
) -> dict[str, Any]:
    if tokenizer is None:
        from glyphprobe.provenance import model_artifact_receipt
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
        )
        artifact = model_artifact_receipt(snapshot)
    else:
        from glyphprobe.provenance import model_artifact_receipt

        artifact = model_artifact_receipt(snapshot)
    records = source_prompt_records()
    token_ids = [t13._token_ids(tokenizer, str(row["text"])) for row in records]
    final_ids: dict[str, int] = {}
    for order in SOURCE_ORDERS:
        for wrapper_index, wrapper in enumerate(wrappers()):
            indices = [
                index
                for index, row in enumerate(records)
                if row["source_order"] == order
                and row["wrapper_index"] == wrapper_index
            ]
            values = {int(token_ids[index][-1]) for index in indices}
            _require(
                len(values) == 1, f"Final token changed: {role}/{order}/{wrapper['id']}"
            )
            final_ids[f"{order}/{wrapper['id']}"] = next(iter(values))
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_preflight_pass",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "revision": t10._model_spec(role)["revision"],
        "artifact": artifact,
        "prompt_sequences": len(records),
        "ordered_prompt_sha256": _canonical_sha256([row["text"] for row in records]),
        "ordered_token_ids_sha256": _canonical_sha256(token_ids),
        "minimum_token_count": min(len(ids) for ids in token_ids),
        "maximum_token_count": max(len(ids) for ids in token_ids),
        "group_final_token_ids": final_ids,
        "model_forwards": 0,
    }


def preflight_role(role: str, output: Path, model_path: Path | None) -> dict[str, Any]:
    audit_design()
    _require(role in model_roles(), f"Unknown T15-A role: {role}")
    snapshot = _locate_snapshot(role, model_path).resolve()
    value = _tokenizer_receipt(role, snapshot)
    _write_json(output, value)
    return value


def aggregate_preflight(directory: Path, output: Path) -> dict[str, Any]:
    audit_design()
    roles: dict[str, Any] = {}
    final_token_groups = None
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(path.is_file(), f"T15-A tokenizer receipt missing: {role}")
        value = _read_json(path)
        _require(
            value.get("status") == "tokenizer_preflight_pass",
            "Tokenizer preflight failed",
        )
        _require(value.get("model_role") == role, "Tokenizer role changed")
        _require(
            int(value.get("prompt_sequences")) == len(source_prompt_records()),
            "Tokenizer prompt count changed",
        )
        keys = tuple(sorted(value["group_final_token_ids"]))
        if final_token_groups is None:
            final_token_groups = keys
        _require(keys == final_token_groups, "Tokenizer final-token groups changed")
        roles[role] = {
            "receipt_sha256": _sha256(path),
            "ordered_prompt_sha256": value["ordered_prompt_sha256"],
            "ordered_token_ids_sha256": value["ordered_token_ids_sha256"],
            "minimum_token_count": value["minimum_token_count"],
            "maximum_token_count": value["maximum_token_count"],
            "artifact_manifest_sha256": value["artifact"]["manifest_sha256"],
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "all_tokenizer_preflights_pass_zero_model_forwards",
        "model_roles": list(model_roles()),
        "prompt_sequences_per_model": len(source_prompt_records()),
        "final_token_groups_per_model": len(final_token_groups or ()),
        "roles": roles,
        "model_forwards": 0,
    }
    _write_json(output, result)
    return result


def audit_preflight(
    directory: Path, *, require_frozen_binding: bool = True
) -> dict[str, Any]:
    aggregate_path = directory / PREFLIGHT_AGGREGATE_NAME
    _require(aggregate_path.is_file(), "T15-A aggregate preflight missing")
    value = _read_json(aggregate_path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Preflight protocol changed")
    _require(
        value.get("status") == "all_tokenizer_preflights_pass_zero_model_forwards",
        "Preflight incomplete",
    )
    _require(
        value.get("model_roles") == list(model_roles()), "Preflight role order changed"
    )
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(path.is_file(), f"T15-A tokenizer receipt missing: {role}")
        _require(
            _sha256(path) == value["roles"][role]["receipt_sha256"],
            f"Tokenizer receipt changed: {role}",
        )
    if require_frozen_binding:
        frozen = _root() / TOKENIZER_PREFLIGHT_PATH
        _require(frozen.is_file(), "Frozen tokenizer preflight missing")
        _require(
            _sha256(aggregate_path) == _sha256(frozen),
            "Runtime tokenizer aggregate differs from freeze",
        )
    return {"status": "pass", "model_roles": list(model_roles()), "model_forwards": 0}


def freeze(output: Path) -> dict[str, Any]:
    design = audit_design()
    _require(
        (_root() / TOKENIZER_PREFLIGHT_PATH).is_file(),
        "Tokenizer preflight must be committed before freeze",
    )
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T15-A frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t15_model_forwards",
        "assets": assets,
        "model_roles": list(model_roles()),
        "axis_ids": [axis["id"] for axis in axes()],
        "expected_counts": design["counts"],
        "tokenizer_preflight_sha256": _sha256(_root() / TOKENIZER_PREFLIGHT_PATH),
        "model_forwards_at_freeze": 0,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
    }
    _write_json(output, value)
    return value


def audit_freeze() -> dict[str, Any]:
    audit_design()
    path = _root() / FREEZE_PATH
    _require(path.is_file(), "T15-A final freeze missing")
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Freeze protocol changed")
    _require(
        value.get("status") == "final_execution_freeze_zero_t15_model_forwards",
        "Freeze status changed",
    )
    _require(
        value.get("model_roles") == list(model_roles()), "Freeze role order changed"
    )
    _require(
        value.get("expected_counts") == _expected_counts(), "Freeze counts changed"
    )
    for relative, expected in value["assets"].items():
        path_value = _root() / relative
        _require(
            path_value.is_file() and _sha256(path_value) == expected,
            f"Frozen asset changed: {relative}",
        )
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path)}


def _source_directory(output_root: Path, role: str) -> Path:
    return output_root / role / "source"


def _response_directory(
    output_root: Path, role: str, kind: str, site_index: int
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


def _record_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("source_kind"),
        row.get("source_order"),
        int(row.get("wrapper_index", -1)),
        row.get("axis_id"),
        row.get("word_axis_id"),
        row.get("emoji_polarity"),
        row.get("word_polarity"),
        int(row.get("shift", -1)),
    )


def _rms(vector: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(vector, dtype=np.float64))))


def _lookup_index(records: Sequence[Mapping[str, Any]]) -> dict[tuple[Any, ...], int]:
    result = {_record_key(row): index for index, row in enumerate(records)}
    _require(len(result) == len(records), "T15-A source record keys are not unique")
    return result


def _component_index(
    lookup: Mapping[tuple[Any, ...], int],
    kind: str,
    order: str,
    wrapper_index: int,
    axis_id: str,
    polarity: str,
) -> int:
    if kind == "emoji_component":
        key = (kind, order, wrapper_index, axis_id, None, polarity, None, -1)
    else:
        key = (kind, order, wrapper_index, axis_id, axis_id, None, polarity, -1)
    return int(lookup[key])


def _pair_index(
    lookup: Mapping[tuple[Any, ...], int],
    kind: str,
    order: str,
    wrapper_index: int,
    axis_id: str,
    word_axis_id: str,
    emoji_polarity: str,
    word_polarity: str,
    shift: int = -1,
) -> int:
    key = (
        kind,
        order,
        wrapper_index,
        axis_id,
        word_axis_id,
        emoji_polarity,
        word_polarity,
        shift,
    )
    return int(lookup[key])


def _interaction_vector(
    deltas: np.ndarray,
    lookup: Mapping[tuple[Any, ...], int],
    *,
    site_position: int,
    axis_id: str,
    word_axis_id: str,
    order: str,
    wrappers_used: Sequence[int],
    source_kind: str,
    shift: int = -1,
) -> np.ndarray:
    wrapper_vectors = []
    for wrapper_index in wrappers_used:
        cells: dict[tuple[str, str], np.ndarray] = {}
        for emoji_polarity in POLARITIES:
            for word_polarity in POLARITIES:
                index = _pair_index(
                    lookup,
                    source_kind,
                    order,
                    wrapper_index,
                    axis_id,
                    word_axis_id,
                    emoji_polarity,
                    word_polarity,
                    shift,
                )
                cells[(emoji_polarity, word_polarity)] = deltas[index, site_position]
        off = 0.5 * (cells[("positive", "negative")] + cells[("negative", "positive")])
        diagonal = 0.5 * (
            cells[("positive", "positive")] + cells[("negative", "negative")]
        )
        wrapper_vectors.append(off - diagonal)
    return np.mean(np.stack(wrapper_vectors), axis=0, dtype=np.float64).astype(
        np.float32
    )


def _main_vector(
    deltas: np.ndarray,
    lookup: Mapping[tuple[Any, ...], int],
    *,
    site_position: int,
    axis_id: str,
    order: str,
    wrappers_used: Sequence[int],
    main: str,
) -> np.ndarray:
    wrapper_vectors = []
    for wrapper_index in wrappers_used:
        cells = {
            (emoji_polarity, word_polarity): deltas[
                _pair_index(
                    lookup,
                    "core_pair",
                    order,
                    wrapper_index,
                    axis_id,
                    axis_id,
                    emoji_polarity,
                    word_polarity,
                ),
                site_position,
            ]
            for emoji_polarity in POLARITIES
            for word_polarity in POLARITIES
        }
        if main == "emoji_main":
            positive = 0.5 * (
                cells[("positive", "positive")] + cells[("positive", "negative")]
            )
            negative = 0.5 * (
                cells[("negative", "positive")] + cells[("negative", "negative")]
            )
        else:
            positive = 0.5 * (
                cells[("positive", "positive")] + cells[("negative", "positive")]
            )
            negative = 0.5 * (
                cells[("positive", "negative")] + cells[("negative", "negative")]
            )
        wrapper_vectors.append(positive - negative)
    return np.mean(np.stack(wrapper_vectors), axis=0, dtype=np.float64).astype(
        np.float32
    )


def _source_products(
    role: str,
    records: Sequence[Mapping[str, Any]],
    deltas: np.ndarray,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], np.ndarray]:
    lookup = _lookup_index(records)
    source_metrics: list[dict[str, Any]] = []
    for row_index, row in enumerate(records):
        if row["source_kind"] not in {"core_pair", "cross_pair"}:
            continue
        axis_id = str(row["axis_id"])
        word_axis_id = str(row["word_axis_id"])
        emoji_index = _component_index(
            lookup,
            "emoji_component",
            str(row["source_order"]),
            int(row["wrapper_index"]),
            axis_id,
            str(row["emoji_polarity"]),
        )
        word_index = _component_index(
            lookup,
            "word_component",
            str(row["source_order"]),
            int(row["wrapper_index"]),
            word_axis_id,
            str(row["word_polarity"]),
        )
        for site_position, site_index in enumerate(SITE_INDICES):
            residual = (
                deltas[row_index, site_position]
                - deltas[emoji_index, site_position]
                - deltas[word_index, site_position]
            )
            metric = {key: value for key, value in row.items() if key != "text"}
            metric.update(
                {
                    "model_role": role,
                    "site_index": site_index,
                    "block_index": int(t13.layer_indices(role)[site_index]),
                    "depth_fraction": float(
                        _config()["source_capture"]["depth_fractions"][site_position]
                    ),
                    "pair_delta_rms": _rms(deltas[row_index, site_position]),
                    "emoji_component_rms": _rms(deltas[emoji_index, site_position]),
                    "word_component_rms": _rms(deltas[word_index, site_position]),
                    "joint_additivity_residual_rms": _rms(residual),
                }
            )
            source_metrics.append(metric)

    catalog: list[dict[str, Any]] = []
    vectors: list[np.ndarray] = []
    floor = float(_config()["intervention"]["degeneracy_floor_rms"])
    axis_by_id = {str(axis["id"]): axis for axis in axes()}
    shifts = tuple(int(value) for value in panel()["cross_axis_cyclic_shifts"])
    for site_position, site_index in enumerate(SITE_INDICES):
        for held_out_wrapper in range(len(wrappers())):
            train_wrappers = [
                index for index in range(len(wrappers())) if index != held_out_wrapper
            ]
            for order in SOURCE_ORDERS:
                for axis_index, axis in enumerate(axes()):
                    axis_id = str(axis["id"])
                    candidates: list[tuple[str, int | None, str, np.ndarray]] = []
                    candidates.append(
                        (
                            "true_conflict",
                            None,
                            axis_id,
                            _interaction_vector(
                                deltas,
                                lookup,
                                site_position=site_position,
                                axis_id=axis_id,
                                word_axis_id=axis_id,
                                order=order,
                                wrappers_used=train_wrappers,
                                source_kind="core_pair",
                            ),
                        )
                    )
                    candidates.append(
                        (
                            "emoji_main",
                            None,
                            axis_id,
                            _main_vector(
                                deltas,
                                lookup,
                                site_position=site_position,
                                axis_id=axis_id,
                                order=order,
                                wrappers_used=train_wrappers,
                                main="emoji_main",
                            ),
                        )
                    )
                    candidates.append(
                        (
                            "word_main",
                            None,
                            axis_id,
                            _main_vector(
                                deltas,
                                lookup,
                                site_position=site_position,
                                axis_id=axis_id,
                                order=order,
                                wrappers_used=train_wrappers,
                                main="word_main",
                            ),
                        )
                    )
                    for shift in shifts:
                        word_axis_id = str(
                            axes()[(axis_index + shift) % len(axes())]["id"]
                        )
                        _require(
                            word_axis_id in axis_by_id, "Cross-axis word axis changed"
                        )
                        candidates.append(
                            (
                                "cross_axis_null",
                                shift,
                                word_axis_id,
                                _interaction_vector(
                                    deltas,
                                    lookup,
                                    site_position=site_position,
                                    axis_id=axis_id,
                                    word_axis_id=word_axis_id,
                                    order=order,
                                    wrappers_used=train_wrappers,
                                    source_kind="cross_pair",
                                    shift=shift,
                                ),
                            )
                        )
                    for kind, shift, word_axis_id, vector in candidates:
                        rms = _rms(vector)
                        vectors.append(vector)
                        catalog.append(
                            {
                                "direction_index": len(catalog),
                                "model_role": role,
                                "direction_kind": kind,
                                "axis_id": axis_id,
                                "word_axis_id": word_axis_id,
                                "shift": shift,
                                "source_order": order,
                                "held_out_wrapper_index": held_out_wrapper,
                                "held_out_wrapper_id": wrappers()[held_out_wrapper][
                                    "id"
                                ],
                                "site_index": site_index,
                                "block_index": int(t13.layer_indices(role)[site_index]),
                                "depth_fraction": float(
                                    _config()["source_capture"]["depth_fractions"][
                                        site_position
                                    ]
                                ),
                                "source_direction_rms": rms,
                                "direction_degenerate": rms <= floor,
                            }
                        )
    direction_array = np.stack(vectors).astype(np.float32)
    _require(
        len(source_metrics) == _expected_counts()["source_metric_rows"],
        "Source metric count changed",
    )
    _require(
        len(catalog) == _expected_counts()["direction_catalog_rows"],
        "Direction catalog count changed",
    )
    _require(bool(np.isfinite(direction_array).all()), "Direction catalog is nonfinite")
    return source_metrics, catalog, direction_array


def _run_source_capture(
    *,
    role: str,
    output_root: Path,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
) -> Path:
    final = _source_directory(output_root, role)
    if final.exists():
        validate_source(final, role)
        return final
    _yield_if_contended(output_root, role, "before_source_capture")
    stage, final = t13._atomic_directory(final)
    records = [dict(row) for row in source_prompt_records()]
    prompts = [str(row["text"]) for row in records]
    sites = [int(t13.layer_indices(role)[index]) for index in SITE_INDICES]
    started = time.perf_counter()
    activations, _, token_counts, batch_calls = t13._capture_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        prompts=prompts,
        batch_size=int(t13._config()["models"]["batch_size"][role]),
    )
    frame_indices = {
        (row["source_order"], int(row["wrapper_index"])): index
        for index, row in enumerate(records)
        if row["source_kind"] == "frame"
    }
    deltas = np.empty_like(activations, dtype=np.float32)
    public_records: list[dict[str, Any]] = []
    for index, row in enumerate(records):
        frame_index = frame_indices[(row["source_order"], int(row["wrapper_index"]))]
        deltas[index] = activations[index] - activations[frame_index]
        public = {key: value for key, value in row.items() if key != "text"}
        public["token_count"] = int(token_counts[index])
        public["prompt_sha256"] = hashlib.sha256(
            str(row["text"]).encode("utf-8")
        ).hexdigest()
        public_records.append(public)
    source_metrics, catalog, directions = _source_products(role, records, deltas)
    np.save(stage / "source_deltas.npy", deltas, allow_pickle=False)
    np.save(stage / "directions.npy", directions, allow_pickle=False)
    _write_jsonl(stage / "source_records.jsonl", public_records)
    _write_jsonl(stage / "source_metrics.jsonl", source_metrics)
    _write_jsonl(stage / "direction_catalog.jsonl", catalog)
    files = t13._directory_file_bindings(
        stage,
        (
            "source_deltas.npy",
            "directions.npy",
            "source_records.jsonl",
            "source_metrics.jsonl",
            "direction_catalog.jsonl",
        ),
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "source_capture_complete",
        "model_role": role,
        "prompt_sequences": len(records),
        "source_metric_rows": len(source_metrics),
        "direction_catalog_rows": len(catalog),
        "batched_model_invocations": batch_calls,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    t13._seal_directory(stage, final, receipt)
    validate_source(final, role)
    return final


def validate_source(directory: Path, role: str) -> dict[str, Any]:
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Source receipt mismatch")
    _require(receipt.get("model_role") == role, "Source role changed")
    _require(receipt.get("status") == "source_capture_complete", "Source incomplete")
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and _sha256(path) == binding["sha256"],
            f"Source file changed: {name}",
        )
    width = int(t10._model_spec(role)["expected_model_dim"])
    deltas = np.load(directory / "source_deltas.npy", mmap_mode="r", allow_pickle=False)
    directions = np.load(
        directory / "directions.npy", mmap_mode="r", allow_pickle=False
    )
    _require(
        deltas.shape == (len(source_prompt_records()), len(SITE_INDICES), width),
        "Source delta shape changed",
    )
    _require(
        directions.shape == (_expected_counts()["direction_catalog_rows"], width),
        "Direction shape changed",
    )
    _require(
        bool(np.isfinite(deltas).all() and np.isfinite(directions).all()),
        "Source arrays are nonfinite",
    )
    _require(
        len(_read_jsonl(directory / "source_records.jsonl"))
        == len(source_prompt_records()),
        "Source records changed",
    )
    _require(
        len(_read_jsonl(directory / "source_metrics.jsonl"))
        == _expected_counts()["source_metric_rows"],
        "Source metrics changed",
    )
    _require(
        len(_read_jsonl(directory / "direction_catalog.jsonl"))
        == _expected_counts()["direction_catalog_rows"],
        "Direction catalog changed",
    )
    return {"status": "pass", "model_role": role}


def _direction_groups(
    role: str,
    kind: str,
    site_index: int,
    source_directory: Path,
    target_rms: np.ndarray,
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    catalog = _read_jsonl(source_directory / "direction_catalog.jsonl")
    directions = np.load(source_directory / "directions.npy", allow_pickle=False)
    selected = [
        row
        for row in catalog
        if row["direction_kind"] == kind and int(row["site_index"]) == site_index
    ]
    expected_directions = 192 if kind == "cross_axis_null" else 64
    _require(
        len(selected) == expected_directions,
        f"Direction count changed: {kind}/{site_index}",
    )
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


def _zero_groups(
    role: str, site_index: int
) -> list[tuple[int, int, list[dict[str, Any]], np.ndarray]]:
    width = int(t10._model_spec(role)["expected_model_dim"])
    groups = []
    for target_index, target in enumerate(targets()):
        metadata = [
            {
                "condition_kind": "zero",
                "model_role": role,
                "site_index": site_index,
                "block_index": int(t13.layer_indices(role)[site_index]),
                "depth_fraction": float(
                    _config()["source_capture"]["depth_fractions"][
                        SITE_INDICES.index(site_index)
                    ]
                ),
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


def _expected_shard_rows(kind: str) -> int:
    mapping = {
        "true_conflict": _expected_counts()["true_conflict_rows"] // len(SITE_INDICES),
        "cross_axis_null": _expected_counts()["cross_axis_null_rows"]
        // len(SITE_INDICES),
        "emoji_main": _expected_counts()["emoji_main_rows"] // len(SITE_INDICES),
        "word_main": _expected_counts()["word_main_rows"] // len(SITE_INDICES),
        "zero": _expected_counts()["zero_rows"] // len(SITE_INDICES),
    }
    _require(kind in mapping, f"Unknown T15-A shard kind: {kind}")
    return mapping[kind]


def _write_response_shard(
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
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    arrays = {
        "top_positive_ids.npy": np.concatenate(positive_ids, axis=0),
        "top_positive_values.npy": np.concatenate(positive_values, axis=0),
        "top_negative_ids.npy": np.concatenate(negative_ids, axis=0),
        "top_negative_values.npy": np.concatenate(negative_values, axis=0),
        "countsketch.npy": np.concatenate(sketches, axis=0),
    }
    for name, value in arrays.items():
        _require(value.shape[0] == len(rows), f"Response row mismatch: {name}")
        _require(bool(np.isfinite(value).all()), f"Response array nonfinite: {name}")
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
            _config()["source_capture"]["depth_fractions"][
                SITE_INDICES.index(site_index)
            ]
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
    final = _response_directory(output_root, role, kind, site_index)
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
    _write_response_shard(
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


def validate_shard(
    directory: Path, role: str, kind: str, site_index: int
) -> dict[str, Any]:
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Response receipt mismatch")
    _require(receipt.get("model_role") == role, "Response role changed")
    _require(receipt.get("shard_kind") == kind, "Response kind changed")
    _require(int(receipt.get("site_index")) == site_index, "Response site changed")
    rows = int(receipt["response_rows"])
    _require(rows == _expected_shard_rows(kind), "Response row count changed")
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and _sha256(path) == binding["sha256"],
            f"Response file changed: {name}",
        )
    top_k = int(_config()["storage"]["top_positive_and_negative_logit_deltas"])
    for name in (
        "top_positive_ids.npy",
        "top_positive_values.npy",
        "top_negative_ids.npy",
        "top_negative_values.npy",
    ):
        value = np.load(directory / name, mmap_mode="r", allow_pickle=False)
        _require(value.shape == (rows, top_k), f"Top-k shape changed: {name}")
        _require(bool(np.isfinite(value).all()), f"Top-k nonfinite: {name}")
    sketch = np.load(directory / "countsketch.npy", mmap_mode="r", allow_pickle=False)
    _require(
        sketch.shape == (rows, int(_config()["storage"]["countsketch_dimension"])),
        "CountSketch shape changed",
    )
    _require(bool(np.isfinite(sketch).all()), "CountSketch is nonfinite")
    _require(
        len(_read_jsonl(directory / "response_ledger.jsonl")) == rows,
        "Ledger count changed",
    )
    return {"status": "pass", "model_role": role, "kind": kind, "rows": rows}


def _validate_zero_values(directory: Path) -> dict[str, float]:
    maximum_js = 0.0
    for row in _read_jsonl(directory / "response_ledger.jsonl"):
        _require(float(row["kl_baseline_to_intervened"]) == 0.0, "Zero KL changed")
        _require(float(row["total_variation"]) == 0.0, "Zero TV changed")
        _require(float(row["logit_delta_rms"]) == 0.0, "Zero RMS changed")
        _require(
            row["baseline_argmax_id"] == row["intervened_argmax_id"],
            "Zero argmax changed",
        )
        maximum_js = max(maximum_js, abs(float(row["js_divergence"])))
    bound = 8.0 * float(np.finfo(np.float32).eps)
    _require(maximum_js <= bound, "Zero JS exceeds bound")
    sketch = np.load(directory / "countsketch.npy", allow_pickle=False)
    _require(bool((sketch == 0).all()), "Zero sketch changed")
    return {"maximum_absolute_js": maximum_js, "js_bound": bound}


def _validate_runtime_tokenizer(
    role: str, tokenizer: Any, snapshot: Path, preflight_directory: Path
) -> None:
    expected = _read_json(preflight_directory / f"{role}.json")
    observed = _tokenizer_receipt(role, snapshot, tokenizer)
    for key in (
        "ordered_prompt_sha256",
        "ordered_token_ids_sha256",
        "group_final_token_ids",
        "artifact",
    ):
        _require(
            observed[key] == expected[key], f"Runtime tokenizer changed: {role}/{key}"
        )


def run_role(
    *,
    role: str,
    output_root: Path,
    source_run_root: Path,
    model_preflight_directory: Path,
    tokenizer_preflight_directory: Path,
    model_path: Path | None,
) -> dict[str, Any]:
    audit_freeze()
    audit_preflight(tokenizer_preflight_directory)
    _require(role in model_roles(), f"Unknown T15-A role: {role}")
    summary_path = output_root / role / "summary.json"
    if summary_path.is_file():
        return validate_role(role, output_root)
    baseline = source_run_root / role / "baseline"
    t13.validate_baseline(baseline, role)
    _yield_if_contended(output_root, role, "before_model_load")
    snapshot = _locate_snapshot(role, model_path).resolve()
    torch, tokenizer, model, model_receipt = t13._load_model(
        role, snapshot, model_preflight_directory
    )
    _validate_runtime_tokenizer(
        role, tokenizer, snapshot, tokenizer_preflight_directory
    )
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    started = time.perf_counter()
    source_directory = _run_source_capture(
        role=role,
        output_root=output_root,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
    )
    target_rms = t13._target_rms(baseline)
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
        for kind in DIRECTION_KINDS:
            _execute_groups(
                role=role,
                kind=kind,
                site_index=site_index,
                output_root=output_root,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                groups=_direction_groups(
                    role, kind, site_index, source_directory, target_rms
                ),
            )
            rows_total += _expected_shard_rows(kind)
    _require(
        rows_total == _expected_counts()["rows_per_model"], "T15-A role total changed"
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "source_run_root": str(source_run_root),
        "response_rows": rows_total,
        "source_prompt_sequences": len(source_prompt_records()),
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
    _require(role in model_roles(), f"Unknown T15-A role: {role}")
    validate_source(_source_directory(output_root, role), role)
    rows = 0
    for site_index in SITE_INDICES:
        for kind in SHARD_KINDS:
            directory = _response_directory(output_root, role, kind, site_index)
            validate_shard(directory, role, kind, site_index)
            if kind == "zero":
                _validate_zero_values(directory)
            rows += _expected_shard_rows(kind)
    summary = _read_json(output_root / role / "summary.json")
    _require(summary.get("protocol_id") == PROTOCOL_ID, "T15-A summary mismatch")
    _require(summary.get("status") == "role_complete", "T15-A role incomplete")
    _require(int(summary.get("response_rows")) == rows, "T15-A summary rows changed")
    _require(rows == _expected_counts()["rows_per_model"], "T15-A role rows changed")
    return {"status": "pass", "model_role": role, "response_rows": rows}


def audit_run(output_root: Path) -> dict[str, Any]:
    audit_freeze()
    results = [validate_role(role, output_root) for role in model_roles()]
    total = sum(int(row["response_rows"]) for row in results)
    _require(total == _expected_counts()["rows_total"], "T15-A run total changed")
    return {
        "status": "complete_closed_to_adaptive_selection",
        "protocol_id": PROTOCOL_ID,
        "roles_complete": len(results),
        "response_rows": total,
        "source_prompt_sequences": len(source_prompt_records()) * len(results),
        "scientific_open_authorized": True,
        "confirmatory_status": False,
        "causal_claim_authorized": False,
        "generation_calls": 0,
    }


def run_all(
    *,
    output_root: Path,
    source_run_root: Path,
    model_preflight_directory: Path,
    tokenizer_preflight_directory: Path,
) -> dict[str, Any]:
    for role in model_roles():
        run_role(
            role=role,
            output_root=output_root,
            source_run_root=source_run_root,
            model_preflight_directory=model_preflight_directory,
            tokenizer_preflight_directory=tokenizer_preflight_directory,
            model_path=None,
        )
    return audit_run(output_root)


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    preflight_design = commands.add_parser("write-design-preflight")
    preflight_design.add_argument(
        "--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH
    )
    preflight_role_parser = commands.add_parser("preflight-role")
    preflight_role_parser.add_argument("--role", required=True, choices=model_roles())
    preflight_role_parser.add_argument("--output", required=True, type=Path)
    preflight_role_parser.add_argument("--model-path", type=Path)
    aggregate = commands.add_parser("aggregate-preflight")
    aggregate.add_argument("--directory", required=True, type=Path)
    aggregate.add_argument("--output", required=True, type=Path)
    audit_preflight_parser = commands.add_parser("audit-preflight")
    audit_preflight_parser.add_argument("--directory", required=True, type=Path)
    audit_preflight_parser.add_argument("--without-frozen-binding", action="store_true")
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    commands.add_parser("audit-freeze")
    run = commands.add_parser("run-role")
    run.add_argument("--role", required=True, choices=model_roles())
    run.add_argument("--output-root", required=True, type=Path)
    run.add_argument("--source-run-root", required=True, type=Path)
    run.add_argument("--model-preflight-directory", required=True, type=Path)
    run.add_argument("--tokenizer-preflight-directory", required=True, type=Path)
    run.add_argument("--model-path", type=Path)
    run_all_parser = commands.add_parser("run-all")
    run_all_parser.add_argument("--output-root", required=True, type=Path)
    run_all_parser.add_argument("--source-run-root", required=True, type=Path)
    run_all_parser.add_argument("--model-preflight-directory", required=True, type=Path)
    run_all_parser.add_argument(
        "--tokenizer-preflight-directory", required=True, type=Path
    )
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
    elif args.command == "preflight-role":
        result = preflight_role(args.role, args.output, args.model_path)
    elif args.command == "aggregate-preflight":
        result = aggregate_preflight(args.directory, args.output)
    elif args.command == "audit-preflight":
        result = audit_preflight(
            args.directory, require_frozen_binding=not args.without_frozen_binding
        )
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run-role":
        result = run_role(
            role=args.role,
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            model_preflight_directory=args.model_preflight_directory,
            tokenizer_preflight_directory=args.tokenizer_preflight_directory,
            model_path=args.model_path,
        )
    elif args.command == "run-all":
        result = run_all(
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            model_preflight_directory=args.model_preflight_directory,
            tokenizer_preflight_directory=args.tokenizer_preflight_directory,
        )
    elif args.command == "validate-role":
        result = validate_role(args.role, args.output_root)
    else:
        result = audit_run(args.output_root)
    _print(result)


if __name__ == "__main__":
    main()
