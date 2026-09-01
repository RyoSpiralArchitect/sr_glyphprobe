#!/usr/bin/env python3
"""Freeze, capture, and analyze the T16-UTF-X1 scale/variant stress test."""

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
import random
import subprocess
import sys
import time
from typing import Any
import uuid

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import emoji_steering_specificity_harvest_v0 as t13  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402
import t16_utf_identity_mixing_v0 as t16  # noqa: E402


PROTOCOL_ID = "glyphprobe-t16-utf-scale-variants-v1"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/t16_utf_scale_variants_v1.yaml")
FREEZE_PATH = Path("data/manifests/t16_utf_scale_variants_v1.json")
VALIDATION_DIRECTORY = Path("validation/t16_utf_scale_variants_v1")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_DIRECTORY = VALIDATION_DIRECTORY / "tokenizers"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"

MODEL_ROLES = (
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
SYSTEM_IDS = ("atomic", "presentation", "modifier", "zwj", "regional", "keycap")
ROTATIONS = (0, 1, 2, 3)
WRAPPER_IDS = (
    "w01_mark_anchor",
    "w04_token_state",
    "w10_sequence_continuation",
    "w15_observation_inference",
)
SITE_POSITIONS = (1, 3, 5, 7)
SCALE_N_VALUES = (
    1,
    2,
    3,
    4,
    5,
    6,
    8,
    12,
    16,
    24,
    32,
    48,
    64,
    96,
    128,
    192,
    256,
    384,
    500,
)
SCALE_VARIANTS = ("clone_exact_utf", "within_cycle_forward", "cross_cycle_forward")
VARIANT_N_VALUES = (8, 16, 32, 64, 128, 256)
DIVERSITY_FAMILIES = ("within", "cross")
ORDER_VARIANTS = (
    "forward_tail",
    "reverse_tail",
    "blocked_tail",
    "interleave_ends_tail",
    "shuffle_seed17_tail",
    "shuffle_seed43_tail",
)
ANCHOR_POSITIONS = ("first", "middle", "last")
SEPARATORS = {
    "none": "",
    "ascii_space": " ",
    "comma_space": ", ",
    "newline": "\n",
    "ascii_pipe": " | ",
}
CHUNK_IDS = (
    "scale",
    *(f"order_{separator}" for separator in SEPARATORS),
    *(f"position_{separator}" for separator in SEPARATORS),
)
EXPECTED_RECORDS = {
    "scale": 5_472,
    **{f"order_{separator}": 6_912 for separator in SEPARATORS},
    **{f"position_{separator}": 3_456 for separator in SEPARATORS},
}
EXPECTED_RECORDS_PER_MODEL = 57_312

STATIC_ASSETS = (
    "configs/t16_utf_scale_variants_v1.yaml",
    "data/panels/t16_utf_identity_mixing_panel_v0.json",
    "data/manifests/t16_utf_identity_mixing_v0.json",
    "data/wrappers/source_wrappers.jsonl",
    "configs/semantic_atlas_cross_model_replication_v0.yaml",
    "validation/emoji_steering_specificity_harvest_v0/aggregate.json",
    "docs/T16_UTF_SCALE_VARIANTS_V1.md",
    "docs/T16_UTF_SCALE_VARIANTS_V1.ja.md",
    "scripts/t16_utf_scale_variants_v1.py",
    "tests/test_t16_utf_scale_variants_v1.py",
    "validation/t16_utf_scale_variants_v1/design_preflight.json",
)


class UTFScaleError(RuntimeError):
    """Raised when a T16-UTF-X1 design, execution, or analysis gate fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UTFScaleError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stream_rows_sha256(rows: Sequence[Sequence[int]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = json.dumps(list(row), separators=(",", ":")).encode("ascii")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root is not an object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-UTF-X1 config changed")
    return value


def _systems() -> tuple[dict[str, Any], ...]:
    return t16._systems()


def _wrappers() -> tuple[dict[str, str], ...]:
    return t16._wrappers()


def _cycle_items(system_index: int, rotation: int, n: int, family: str) -> list[str]:
    systems = _systems()
    if family == "clone":
        return [str(systems[system_index]["items"][rotation]["glyph"])] * n
    if family == "within":
        return [
            str(systems[system_index]["items"][(rotation + index) % 4]["glyph"])
            for index in range(n)
        ]
    _require(family == "cross", f"Unknown diversity family: {family}")
    return [
        str(systems[(system_index + index) % 6]["items"][rotation]["glyph"])
        for index in range(n)
    ]


def _ordered_items(
    system_index: int,
    rotation: int,
    n: int,
    family: str,
    variant: str,
) -> list[str]:
    values = _cycle_items(system_index, rotation, n, family)
    anchor, tail = values[0], values[1:]
    if variant == "forward_tail":
        ordered = tail
    elif variant == "reverse_tail":
        ordered = list(reversed(tail))
    elif variant == "blocked_tail":
        rank = {glyph: index for index, glyph in enumerate(dict.fromkeys(values))}
        ordered = sorted(tail, key=lambda glyph: rank[glyph])
    elif variant == "interleave_ends_tail":
        ordered = []
        left, right = 0, len(tail) - 1
        while left <= right:
            ordered.append(tail[left])
            left += 1
            if left <= right:
                ordered.append(tail[right])
                right -= 1
    else:
        _require(
            variant in ("shuffle_seed17_tail", "shuffle_seed43_tail"),
            f"Unknown order variant: {variant}",
        )
        seed = 17 if variant == "shuffle_seed17_tail" else 43
        generator = random.Random(seed + 10_000 * system_index + 100 * rotation + n)
        ordered = list(tail)
        generator.shuffle(ordered)
    result = [anchor, *ordered]
    _require(
        sorted(result) == sorted(values),
        "Order variant changed the exact item multiset",
    )
    _require(result[0] == anchor, "Order variant moved the anchor from first position")
    return result


def _position_items(
    system_index: int, rotation: int, n: int, family: str, position: str
) -> list[str]:
    systems = _systems()
    anchor = str(systems[system_index]["items"][rotation]["glyph"])
    if family == "within":
        alternatives = [
            str(systems[system_index]["items"][(rotation + offset) % 4]["glyph"])
            for offset in (1, 2, 3)
        ]
    else:
        _require(family == "cross", f"Unknown position background: {family}")
        alternatives = [
            str(systems[(system_index + offset) % 6]["items"][rotation]["glyph"])
            for offset in (1, 2, 3, 4, 5)
        ]
    background = [alternatives[index % len(alternatives)] for index in range(n - 1)]
    indices = {"first": 0, "middle": n // 2, "last": n - 1}
    _require(position in indices, f"Unknown anchor position: {position}")
    background.insert(indices[position], anchor)
    _require(
        len(background) == n and background.count(anchor) == 1,
        "Singleton anchor invariant failed",
    )
    return background


def _multiset_sha256(items: Sequence[str]) -> str:
    return _canonical_sha256(sorted(item.encode("utf-8").hex() for item in items))


def _item_order_sha256(items: Sequence[str]) -> str:
    return _canonical_sha256([item.encode("utf-8").hex() for item in items])


def _base_record(
    *,
    chunk_id: str,
    system_index: int,
    rotation: int,
    n: int,
    wrapper_index: int,
    items: Sequence[str],
    separator_id: str,
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    system = _systems()[system_index]
    wrapper = _wrappers()[wrapper_index]
    separator = SEPARATORS[separator_id]
    sequence = separator.join(items)
    prompt = wrapper["template"].format(emoji=sequence)
    anchor = str(system["items"][rotation]["glyph"])
    return {
        "chunk_id": chunk_id,
        "system_id": str(system["id"]),
        "system_index": system_index,
        "rotation": rotation,
        "anchor_sha256": hashlib.sha256(anchor.encode("utf-8")).hexdigest(),
        "n": n,
        "wrapper_index": wrapper_index,
        "wrapper_id": wrapper["id"],
        "separator_id": separator_id,
        "item_multiset_sha256": _multiset_sha256(items),
        "item_order_sha256": _item_order_sha256(items),
        "sequence_sha256": hashlib.sha256(sequence.encode("utf-8")).hexdigest(),
        "sequence_utf8_bytes": len(sequence.encode("utf-8")),
        "sequence_unicode_scalars": len(sequence),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "sequence": sequence,
        "prompt": prompt,
        **dict(fields),
    }


@cache
def chunk_records(chunk_id: str) -> tuple[dict[str, Any], ...]:
    _require(chunk_id in CHUNK_IDS, f"Unknown chunk: {chunk_id}")
    rows: list[dict[str, Any]] = []
    prompt_to_index: dict[str, int] = {}
    if chunk_id == "scale":
        for system_index in range(len(SYSTEM_IDS)):
            for rotation in ROTATIONS:
                for n in SCALE_N_VALUES:
                    for variant in SCALE_VARIANTS:
                        family = {
                            "clone_exact_utf": "clone",
                            "within_cycle_forward": "within",
                            "cross_cycle_forward": "cross",
                        }[variant]
                        items = _cycle_items(system_index, rotation, n, family)
                        for wrapper_index in range(len(WRAPPER_IDS)):
                            rows.append(
                                _base_record(
                                    chunk_id=chunk_id,
                                    system_index=system_index,
                                    rotation=rotation,
                                    n=n,
                                    wrapper_index=wrapper_index,
                                    items=items,
                                    separator_id="none",
                                    fields={"lane": "scale", "scale_variant": variant},
                                )
                            )
    elif chunk_id.startswith("order_"):
        separator_id = chunk_id.removeprefix("order_")
        for system_index in range(len(SYSTEM_IDS)):
            for rotation in ROTATIONS:
                for n in VARIANT_N_VALUES:
                    for family in DIVERSITY_FAMILIES:
                        reference_multiset: str | None = None
                        for variant in ORDER_VARIANTS:
                            items = _ordered_items(
                                system_index, rotation, n, family, variant
                            )
                            observed = _multiset_sha256(items)
                            reference_multiset = (
                                observed
                                if reference_multiset is None
                                else reference_multiset
                            )
                            _require(
                                observed == reference_multiset,
                                "Order paired multiset invariant failed",
                            )
                            for wrapper_index in range(len(WRAPPER_IDS)):
                                rows.append(
                                    _base_record(
                                        chunk_id=chunk_id,
                                        system_index=system_index,
                                        rotation=rotation,
                                        n=n,
                                        wrapper_index=wrapper_index,
                                        items=items,
                                        separator_id=separator_id,
                                        fields={
                                            "lane": "order",
                                            "diversity_family": family,
                                            "order_variant": variant,
                                        },
                                    )
                                )
    else:
        separator_id = chunk_id.removeprefix("position_")
        for system_index in range(len(SYSTEM_IDS)):
            for rotation in ROTATIONS:
                for n in VARIANT_N_VALUES:
                    for family in DIVERSITY_FAMILIES:
                        reference_multiset = None
                        for position in ANCHOR_POSITIONS:
                            items = _position_items(
                                system_index, rotation, n, family, position
                            )
                            observed = _multiset_sha256(items)
                            reference_multiset = (
                                observed
                                if reference_multiset is None
                                else reference_multiset
                            )
                            _require(
                                observed == reference_multiset,
                                "Position paired multiset invariant failed",
                            )
                            for wrapper_index in range(len(WRAPPER_IDS)):
                                rows.append(
                                    _base_record(
                                        chunk_id=chunk_id,
                                        system_index=system_index,
                                        rotation=rotation,
                                        n=n,
                                        wrapper_index=wrapper_index,
                                        items=items,
                                        separator_id=separator_id,
                                        fields={
                                            "lane": "position",
                                            "background_family": family,
                                            "anchor_position": position,
                                        },
                                    )
                                )
    for index, row in enumerate(rows):
        prompt = str(row["prompt"])
        if prompt not in prompt_to_index:
            prompt_to_index[prompt] = len(prompt_to_index)
        row["chunk_record_index"] = index
        row["unique_prompt_index"] = prompt_to_index[prompt]
    _require(
        len(rows) == EXPECTED_RECORDS[chunk_id], f"Record count changed: {chunk_id}"
    )
    return tuple(rows)


@cache
def unique_prompts(chunk_id: str) -> tuple[str, ...]:
    rows = chunk_records(chunk_id)
    count = 1 + max(int(row["unique_prompt_index"]) for row in rows)
    values: list[str | None] = [None] * count
    for row in rows:
        index = int(row["unique_prompt_index"])
        prompt = str(row["prompt"])
        if values[index] is None:
            values[index] = prompt
        else:
            _require(
                values[index] == prompt, f"Unique prompt mapping changed: {chunk_id}"
            )
    _require(
        all(value is not None for value in values),
        f"Unique prompt roster incomplete: {chunk_id}",
    )
    return tuple(str(value) for value in values)


def audit_design() -> dict[str, Any]:
    config = _config()
    _require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model order changed")
    _require(
        tuple(config["factorial"]["systems"]) == SYSTEM_IDS, "System order changed"
    )
    _require(
        tuple(config["factorial"]["rotations"]) == ROTATIONS, "Rotation order changed"
    )
    _require(
        tuple(config["factorial"]["wrappers"]) == WRAPPER_IDS, "Wrapper order changed"
    )
    _require(
        tuple(config["factorial"]["scale_lane"]["n_values"]) == SCALE_N_VALUES,
        "Scale n roster changed",
    )
    _require(
        tuple(config["factorial"]["order_lane"]["order_variants"]) == ORDER_VARIANTS,
        "Order variants changed",
    )
    _require(
        tuple(config["factorial"]["order_lane"]["separators"]) == tuple(SEPARATORS),
        "Separator order changed",
    )
    _require(
        tuple(config["factorial"]["position_lane"]["anchor_positions"])
        == ANCHOR_POSITIONS,
        "Anchor positions changed",
    )
    t16._audit_panel_structure()
    for key, binding in config["source_bindings"].items():
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"Bound source missing: {key}")
        _require(
            _sha256(path) == str(binding["sha256"]), f"Bound source changed: {key}"
        )
    counts = {chunk_id: len(chunk_records(chunk_id)) for chunk_id in CHUNK_IDS}
    unique = {chunk_id: len(unique_prompts(chunk_id)) for chunk_id in CHUNK_IDS}
    _require(
        sum(counts.values()) == EXPECTED_RECORDS_PER_MODEL, "Total record count changed"
    )
    scale_n1 = [row for row in chunk_records("scale") if int(row["n"]) == 1]
    grouped: dict[tuple[str, int, str], set[int]] = defaultdict(set)
    for row in scale_n1:
        grouped[
            (str(row["system_id"]), int(row["rotation"]), str(row["wrapper_id"]))
        ].add(int(row["unique_prompt_index"]))
    _require(
        len(grouped) == 96 and all(len(values) == 1 for values in grouped.values()),
        "Scale n=1 prompt collapse changed",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_x1_model_forwards",
        "model_roles": list(MODEL_ROLES),
        "chunks": list(CHUNK_IDS),
        "records_by_chunk": counts,
        "unique_prompts_by_chunk": unique,
        "records_per_model": sum(counts.values()),
        "unique_prompts_per_model_across_chunk_namespaces": sum(unique.values()),
        "records_total": len(MODEL_ROLES) * sum(counts.values()),
        "scale_n_values": list(SCALE_N_VALUES),
        "order_variants": list(ORDER_VARIANTS),
        "separators": list(SEPARATORS),
        "anchor_positions": list(ANCHOR_POSITIONS),
        "model_forwards": 0,
        "tokenizer_independent_unicode_claim_authorized": False,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    result = audit_design()
    _write_json(output, result)
    return result


def _locate_snapshot(role: str, supplied: Path | None) -> Path:
    path = supplied if supplied is not None else t13.t11._locate_local_snapshot(role)
    resolved = path.resolve()
    spec = t10._model_spec(role)
    _require(resolved.is_dir(), f"T16-UTF-X1 snapshot missing: {role}")
    _require(
        resolved.name == str(spec["revision"]), f"T16-UTF-X1 revision changed: {role}"
    )
    return resolved


def _token_ids(tokenizer: Any, prompts: Sequence[str]) -> list[list[int]]:
    value = tokenizer(
        list(prompts),
        add_special_tokens=False,
        padding=False,
        return_attention_mask=False,
    )["input_ids"]
    return [[int(token) for token in row] for row in value]


def _tokenizer_chunk(tokenizer: Any, chunk_id: str) -> dict[str, Any]:
    prompts = unique_prompts(chunk_id)
    unique_ids = _token_ids(tokenizer, prompts)
    counts = [len(row) for row in unique_ids]
    multisets = [_canonical_sha256(sorted(row)) for row in unique_ids]
    record_counts = [
        counts[int(row["unique_prompt_index"])] for row in chunk_records(chunk_id)
    ]
    record_multisets = [
        multisets[int(row["unique_prompt_index"])] for row in chunk_records(chunk_id)
    ]
    return {
        "records": len(chunk_records(chunk_id)),
        "unique_prompts": len(prompts),
        "ordered_unique_prompt_sha256": _canonical_sha256(prompts),
        "ordered_unique_token_ids_sha256": _stream_rows_sha256(unique_ids),
        "record_token_counts_sha256": _canonical_sha256(record_counts),
        "record_token_multisets_sha256": _canonical_sha256(record_multisets),
        "minimum_token_count": min(counts),
        "maximum_token_count": max(counts),
    }


def tokenizer_preflight(
    role: str, output: Path, model_path: Path | None
) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoConfig, AutoTokenizer

    audit_design()
    _require(role in MODEL_ROLES, f"Unknown T16-UTF-X1 role: {role}")
    snapshot = _locate_snapshot(role, model_path)
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    model_config = AutoConfig.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    chunks = {chunk_id: _tokenizer_chunk(tokenizer, chunk_id) for chunk_id in CHUNK_IDS}
    maximum = max(int(value["maximum_token_count"]) for value in chunks.values())
    hard_max = int(_config()["tokenization"]["hard_max_full_prompt_tokens"])
    _require(
        maximum <= hard_max,
        f"Prompt exceeds hard token cap: {role}/{maximum}>{hard_max}",
    )
    context_candidates = [
        int(value)
        for name in ("max_position_embeddings", "n_positions", "seq_length")
        if (value := getattr(model_config, name, None)) is not None and int(value) > 0
    ]
    _require(
        not context_candidates or maximum <= min(context_candidates),
        f"Prompt exceeds model context: {role}",
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_preflight_pass_zero_x1_model_forwards",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "revision": t10._model_spec(role)["revision"],
        "artifact": model_artifact_receipt(snapshot),
        "tokenizer_class": type(tokenizer).__name__,
        "model_context_candidates": context_candidates,
        "hard_max_full_prompt_tokens": hard_max,
        "minimum_token_count": min(
            int(value["minimum_token_count"]) for value in chunks.values()
        ),
        "maximum_token_count": maximum,
        "chunks": chunks,
        "model_weights_loaded": False,
        "model_forwards": 0,
    }
    _write_json(output, result)
    return result


def aggregate_preflight(directory: Path, output: Path) -> dict[str, Any]:
    audit_design()
    roles: dict[str, Any] = {}
    for role in MODEL_ROLES:
        path = directory / f"{role}.json"
        value = _read_json(path)
        _require(
            value.get("protocol_id") == PROTOCOL_ID,
            f"Tokenizer protocol changed: {role}",
        )
        _require(
            value.get("status") == "tokenizer_preflight_pass_zero_x1_model_forwards",
            f"Tokenizer preflight incomplete: {role}",
        )
        _require(value.get("model_role") == role, f"Tokenizer role changed: {role}")
        roles[role] = {
            "receipt_sha256": _sha256(path),
            "artifact_manifest_sha256": value["artifact"]["manifest_sha256"],
            "minimum_token_count": value["minimum_token_count"],
            "maximum_token_count": value["maximum_token_count"],
            "chunks": {
                chunk_id: {
                    "ordered_unique_token_ids_sha256": value["chunks"][chunk_id][
                        "ordered_unique_token_ids_sha256"
                    ],
                    "record_token_counts_sha256": value["chunks"][chunk_id][
                        "record_token_counts_sha256"
                    ],
                    "record_token_multisets_sha256": value["chunks"][chunk_id][
                        "record_token_multisets_sha256"
                    ],
                }
                for chunk_id in CHUNK_IDS
            },
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "all_nine_tokenizer_preflights_pass_zero_x1_model_forwards",
        "model_roles": list(MODEL_ROLES),
        "roles": roles,
        "model_forwards": 0,
    }
    _write_json(output, result)
    return result


def _frozen_assets() -> tuple[str, ...]:
    return (
        *STATIC_ASSETS,
        *(
            f"validation/t16_utf_scale_variants_v1/tokenizers/{role}.json"
            for role in MODEL_ROLES
        ),
        "validation/t16_utf_scale_variants_v1/tokenizer_preflight.json",
    )


def freeze(output: Path) -> dict[str, Any]:
    design = audit_design()
    aggregate = _read_json(_root() / TOKENIZER_PREFLIGHT_PATH)
    _require(
        aggregate.get("status")
        == "all_nine_tokenizer_preflights_pass_zero_x1_model_forwards",
        "T16-UTF-X1 tokenizer aggregate missing or incomplete",
    )
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        _require(path.is_file(), f"T16-UTF-X1 frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_x1_model_forwards",
        "assets": assets,
        "model_roles": list(MODEL_ROLES),
        "chunks": list(CHUNK_IDS),
        "records_per_model": design["records_per_model"],
        "records_total": design["records_total"],
        "depths_per_model": 4,
        "model_forwards_at_freeze": 0,
        "tokenizer_independent_unicode_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def audit_freeze(*, require_pushed: bool = False) -> dict[str, Any]:
    design = audit_design()
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(
        value.get("protocol_id") == PROTOCOL_ID, "T16-UTF-X1 freeze protocol changed"
    )
    _require(
        value.get("status") == "final_execution_freeze_zero_x1_model_forwards",
        "T16-UTF-X1 freeze incomplete",
    )
    _require(
        int(value["records_per_model"]) == design["records_per_model"],
        "Frozen record count changed",
    )
    for relative, expected in value["assets"].items():
        asset = _root() / relative
        _require(
            asset.is_file() and _sha256(asset) == expected,
            f"T16-UTF-X1 frozen asset changed: {relative}",
        )
    git: dict[str, Any] = {"required": require_pushed}
    if require_pushed:
        protected = [FREEZE_PATH.as_posix(), *value["assets"].keys()]
        _require(
            not _git_value("status", "--porcelain", "--", *protected),
            "T16-UTF-X1 protected files are not committed",
        )
        head = _git_value("rev-parse", "HEAD")
        upstream = _git_value("rev-parse", "@{u}")
        _require(
            head == upstream, "T16-UTF-X1 freeze commit is not pushed to its upstream"
        )
        _require(
            _git_value("cat-file", "-e", f"HEAD:{FREEZE_PATH.as_posix()}") == "",
            "Freeze manifest is not committed",
        )
        git = {"required": True, "head": head, "upstream": upstream}
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path), "git": git}


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
                "status": "yielded_for_foreign_gpu_contention",
                "model_role": role,
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(
        int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"])
    )


def _runtime_tokenization(
    role: str, chunk_id: str, tokenizer: Any
) -> tuple[list[list[int]], list[int], list[str]]:
    frozen = _read_json(_root() / TOKENIZER_DIRECTORY / f"{role}.json")
    prompts = unique_prompts(chunk_id)
    ids = _token_ids(tokenizer, prompts)
    counts = [len(row) for row in ids]
    multisets = [_canonical_sha256(sorted(row)) for row in ids]
    records_for_chunk = chunk_records(chunk_id)
    record_counts = [
        counts[int(row["unique_prompt_index"])] for row in records_for_chunk
    ]
    record_multisets = [
        multisets[int(row["unique_prompt_index"])] for row in records_for_chunk
    ]
    expected = frozen["chunks"][chunk_id]
    _require(
        _stream_rows_sha256(ids) == expected["ordered_unique_token_ids_sha256"],
        f"Runtime token IDs changed: {role}/{chunk_id}",
    )
    _require(
        _canonical_sha256(record_counts) == expected["record_token_counts_sha256"],
        f"Runtime token counts changed: {role}/{chunk_id}",
    )
    _require(
        _canonical_sha256(record_multisets)
        == expected["record_token_multisets_sha256"],
        f"Runtime token multisets changed: {role}/{chunk_id}",
    )
    return ids, counts, multisets


def _tensor_from_output(output: Any) -> Any:
    if hasattr(output, "shape"):
        return output
    if isinstance(output, (tuple, list)) and output and hasattr(output[0], "shape"):
        return output[0]
    raise UTFScaleError(f"Cannot identify tensor in output {type(output)!r}")


def _batches(role: str, counts: Sequence[int]) -> list[list[int]]:
    cap = int(_config()["runtime"]["max_batch_size_by_role"][role])
    budget = int(_config()["runtime"]["max_padded_tokens_per_batch_by_role"][role])
    ordered = sorted(range(len(counts)), key=lambda index: (int(counts[index]), index))
    batches: list[list[int]] = []
    current: list[int] = []
    maximum = 0
    for index in ordered:
        candidate_maximum = max(maximum, int(counts[index]))
        candidate_count = len(current) + 1
        if current and (
            candidate_count > cap or candidate_maximum * candidate_count > budget
        ):
            batches.append(current)
            current = []
            maximum = 0
        current.append(index)
        maximum = max(maximum, int(counts[index]))
    if current:
        batches.append(current)
    _require(
        sum(len(batch) for batch in batches) == len(counts),
        "Batch scheduler lost prompts",
    )
    _require(
        all(len(batch) <= cap for batch in batches),
        "Batch scheduler exceeded count cap",
    )
    _require(
        all(
            len(batch) == 1
            or max(int(counts[index]) for index in batch) * len(batch) <= budget
            for batch in batches
        ),
        "Batch scheduler exceeded token budget",
    )
    return batches


def _capture_chunk(
    *,
    role: str,
    chunk_id: str,
    output_root: Path,
    torch: Any,
    tokenizer: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    final = output_root / role / chunk_id
    if final.is_dir():
        return validate_chunk(role, chunk_id, output_root)
    _yield_if_contended(output_root, role, f"before_chunk_{chunk_id}")
    ids, counts, multisets = _runtime_tokenization(role, chunk_id, tokenizer)
    del ids
    prompts = unique_prompts(chunk_id)
    width = int(t10._model_spec(role)["expected_model_dim"])
    hidden = np.empty((len(prompts), 4, width), dtype=np.float32)
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    block_indices = tuple(
        t13.layer_indices(role)[position] for position in SITE_POSITIONS
    )
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    started = time.perf_counter()
    processed = 0
    batch_count = 0
    for batch_indices in _batches(role, counts):
        if processed % 128 < len(batch_indices):
            _yield_if_contended(
                output_root, role, f"{chunk_id}_before_processed_{processed}"
            )
        batch_prompts = [prompts[index] for index in batch_indices]
        encoded = tokenizer(
            batch_prompts, add_special_tokens=False, padding=True, return_tensors="pt"
        )
        device = next(model.parameters()).device
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        captured: dict[int, Any] = {}
        handles = []
        for site_position, block_index in enumerate(block_indices):

            def hook(
                _module: Any,
                _inputs: Any,
                output: Any,
                *,
                site_position: int = site_position,
            ) -> Any:
                raw = _tensor_from_output(output)
                captured[site_position] = raw[:, -1, :].detach().float().cpu().numpy()
                return output

            handles.append(blocks[block_index].register_forward_hook(hook))
        try:
            with torch.inference_mode():
                model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=False,
                    return_dict=True,
                )
        finally:
            for handle in handles:
                handle.remove()
        _require(
            set(captured) == set(range(4)), f"Capture incomplete: {role}/{chunk_id}"
        )
        for site_position in range(4):
            hidden[np.asarray(batch_indices), site_position, :] = captured[
                site_position
            ]
        processed += len(batch_indices)
        batch_count += 1
    _require(
        bool(np.isfinite(hidden).all()), f"Hidden array nonfinite: {role}/{chunk_id}"
    )
    records_for_chunk = chunk_records(chunk_id)
    ledger = [
        {
            **{
                key: value
                for key, value in row.items()
                if key not in ("sequence", "prompt")
            },
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "model_role": role,
            "token_count": counts[int(row["unique_prompt_index"])],
            "token_multiset_sha256": multisets[int(row["unique_prompt_index"])],
        }
        for row in records_for_chunk
    ]
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(
        not final.exists() and not stage.exists(),
        f"Output collision: {role}/{chunk_id}",
    )
    stage.mkdir(parents=True)
    np.save(stage / "hidden_states.npy", hidden, allow_pickle=False)
    _write_jsonl(stage / "records.jsonl", ledger)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "utf_scale_variant_chunk_complete",
        "model_role": role,
        "chunk_id": chunk_id,
        "records": len(ledger),
        "unique_prompts": len(prompts),
        "block_indices": list(block_indices),
        "depth_fractions": list(_config()["capture"]["normalized_depth_fractions"]),
        "hidden_shape": list(hidden.shape),
        "hidden_states_sha256": _sha256(stage / "hidden_states.npy"),
        "records_sha256": _sha256(stage / "records.jsonl"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_receipt": dict(model_receipt),
        "batch_count": batch_count,
        "minimum_token_count": min(counts),
        "maximum_token_count": max(counts),
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_chunk(role, chunk_id, output_root)


def validate_chunk(role: str, chunk_id: str, output_root: Path) -> dict[str, Any]:
    directory = output_root / role / chunk_id
    receipt = _read_json(directory / "receipt.json")
    _require(
        receipt.get("protocol_id") == PROTOCOL_ID,
        f"Receipt protocol changed: {role}/{chunk_id}",
    )
    _require(
        receipt.get("status") == "utf_scale_variant_chunk_complete",
        f"Chunk incomplete: {role}/{chunk_id}",
    )
    _require(
        receipt.get("model_role") == role and receipt.get("chunk_id") == chunk_id,
        "Receipt identity changed",
    )
    hidden_path = directory / "hidden_states.npy"
    ledger_path = directory / "records.jsonl"
    _require(
        _sha256(hidden_path) == receipt["hidden_states_sha256"],
        f"Hidden hash changed: {role}/{chunk_id}",
    )
    _require(
        _sha256(ledger_path) == receipt["records_sha256"],
        f"Ledger hash changed: {role}/{chunk_id}",
    )
    hidden = np.load(hidden_path, mmap_mode="r", allow_pickle=False)
    expected_shape = (
        len(unique_prompts(chunk_id)),
        4,
        int(t10._model_spec(role)["expected_model_dim"]),
    )
    _require(hidden.shape == expected_shape, f"Hidden shape changed: {role}/{chunk_id}")
    _require(
        bool(np.isfinite(hidden).all()), f"Hidden array nonfinite: {role}/{chunk_id}"
    )
    rows = _read_jsonl(ledger_path)
    _require(
        len(rows) == EXPECTED_RECORDS[chunk_id],
        f"Ledger row count changed: {role}/{chunk_id}",
    )
    return {
        "status": "pass",
        "model_role": role,
        "chunk_id": chunk_id,
        "records": len(rows),
        "unique_prompts": int(receipt["unique_prompts"]),
        "receipt_sha256": _sha256(directory / "receipt.json"),
    }


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    chunks = [validate_chunk(role, chunk_id, output_root) for chunk_id in CHUNK_IDS]
    return {
        "status": "all_chunks_complete",
        "model_role": role,
        "chunks": len(chunks),
        "records": sum(int(row["records"]) for row in chunks),
        "unique_prompts_across_chunk_namespaces": sum(
            int(row["unique_prompts"]) for row in chunks
        ),
        "chunk_receipts": {
            str(row["chunk_id"]): str(row["receipt_sha256"]) for row in chunks
        },
    }


def run_role(
    *,
    role: str,
    output_root: Path,
    model_preflight_directory: Path,
    model_path: Path | None,
) -> dict[str, Any]:
    audit_freeze(require_pushed=True)
    _require(role in MODEL_ROLES, f"Unknown T16-UTF-X1 role: {role}")
    missing = [
        chunk_id
        for chunk_id in CHUNK_IDS
        if not (output_root / role / chunk_id).is_dir()
    ]
    if not missing:
        return validate_role(role, output_root)
    _yield_if_contended(output_root, role, "before_model_load")
    snapshot = _locate_snapshot(role, model_path)
    torch, tokenizer, model, model_receipt = t13._load_model(
        role, snapshot, model_preflight_directory
    )
    try:
        for chunk_id in CHUNK_IDS:
            _capture_chunk(
                role=role,
                chunk_id=chunk_id,
                output_root=output_root,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                model_receipt=model_receipt,
            )
    finally:
        del model
        torch.cuda.empty_cache()
    result = validate_role(role, output_root)
    _write_json(output_root / role / "role_receipt.json", result)
    return result


def audit_run(output_root: Path) -> dict[str, Any]:
    audit_freeze(require_pushed=True)
    roles = [validate_role(role, output_root) for role in MODEL_ROLES]
    return {
        "status": "all_nine_roles_all_chunks_complete_integrated_scientific_open_authorized",
        "roles_complete": len(roles),
        "chunks_complete": sum(int(row["chunks"]) for row in roles),
        "records": sum(int(row["records"]) for row in roles),
        "unique_prompts_across_model_chunk_namespaces": sum(
            int(row["unique_prompts_across_chunk_namespaces"]) for row in roles
        ),
        "generation_calls": 0,
        "roles": roles,
    }


def _cosine_distance(first: np.ndarray, second: np.ndarray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    _require(
        denominator > 0 and math.isfinite(denominator), "Cosine denominator invalid"
    )
    value = 1.0 - float(np.dot(first, second) / denominator)
    return float(max(0.0, min(2.0, value)))


def _bootstrap(values: np.ndarray, systems: Sequence[str], seed: int) -> np.ndarray:
    _require(values.shape == (96,), "Bootstrap principal-unit vector changed")
    labels = np.asarray(systems, dtype=object)
    strata = [np.flatnonzero(labels == system) for system in SYSTEM_IDS]
    _require(all(len(indices) == 16 for indices in strata), "Bootstrap strata changed")
    replicates = int(_config()["analysis"]["uncertainty"]["bootstrap_replicates"])
    rng = np.random.default_rng(seed)
    chunks: list[np.ndarray] = []
    for start in range(0, replicates, 1_000):
        count = min(1_000, replicates - start)
        sampled = np.concatenate(
            [
                indices[rng.integers(0, len(indices), size=(count, len(indices)))]
                for indices in strata
            ],
            axis=1,
        )
        chunks.append(np.median(values[sampled], axis=1))
    return np.concatenate(chunks)


def _unit_summary(
    units: Sequence[Mapping[str, Any]], field: str, seed: int
) -> dict[str, Any]:
    _require(len(units) == 96, f"Principal-unit count changed: {field}")
    values = np.asarray([float(row[field]) for row in units], dtype=np.float64)
    systems = [str(row["system_id"]) for row in units]
    bootstrap = _bootstrap(values, systems, seed)
    return {
        "principal_unit_median": float(np.median(values)),
        "principal_unit_iqr": [
            float(np.quantile(values, 0.25)),
            float(np.quantile(values, 0.75)),
        ],
        "bootstrap_95_percent_interval": [
            float(np.quantile(bootstrap, 0.025)),
            float(np.quantile(bootstrap, 0.975)),
        ],
        "positive_principal_units": int(np.count_nonzero(values > 0.0)),
        "system_medians": {
            system: float(
                np.median(
                    [float(row[field]) for row in units if row["system_id"] == system]
                )
            )
            for system in SYSTEM_IDS
        },
    }


def _load_chunk(
    role: str, chunk_id: str, output_root: Path
) -> tuple[list[dict[str, Any]], np.ndarray]:
    validate_chunk(role, chunk_id, output_root)
    directory = output_root / role / chunk_id
    return (
        _read_jsonl(directory / "records.jsonl"),
        np.load(directory / "hidden_states.npy", mmap_mode="r", allow_pickle=False),
    )


def _scale_lookup(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, int, int, str, str], Mapping[str, Any]]:
    result = {
        (
            str(row["system_id"]),
            int(row["rotation"]),
            int(row["n"]),
            str(row["wrapper_id"]),
            str(row["scale_variant"]),
        ): row
        for row in rows
    }
    _require(len(result) == EXPECTED_RECORDS["scale"], "Scale lookup changed")
    return result


def _order_lookup(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, int, int, str, str, str], Mapping[str, Any]]:
    result = {
        (
            str(row["system_id"]),
            int(row["rotation"]),
            int(row["n"]),
            str(row["wrapper_id"]),
            str(row["diversity_family"]),
            str(row["order_variant"]),
        ): row
        for row in rows
    }
    _require(len(result) == 6_912, "Order lookup changed")
    return result


def _position_lookup(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, int, int, str, str, str], Mapping[str, Any]]:
    result = {
        (
            str(row["system_id"]),
            int(row["rotation"]),
            int(row["n"]),
            str(row["wrapper_id"]),
            str(row["background_family"]),
            str(row["anchor_position"]),
        ): row
        for row in rows
    }
    _require(len(result) == 3_456, "Position lookup changed")
    return result


def _hidden_vector(
    hidden: np.ndarray, row: Mapping[str, Any], depth_index: int
) -> np.ndarray:
    return np.asarray(
        hidden[int(row["unique_prompt_index"]), depth_index], dtype=np.float64
    )


def _match_rates(
    pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> dict[str, Any]:
    _require(bool(pairs), "Token-match pair roster is empty")
    count_matches = sum(
        int(first["token_count"]) == int(second["token_count"])
        for first, second in pairs
    )
    multiset_matches = sum(
        str(first["token_multiset_sha256"]) == str(second["token_multiset_sha256"])
        for first, second in pairs
    )
    return {
        "pairs": len(pairs),
        "exact_token_count_matches": count_matches,
        "exact_token_count_match_rate": count_matches / len(pairs),
        "exact_full_prompt_token_multiset_matches": multiset_matches,
        "exact_full_prompt_token_multiset_match_rate": multiset_matches / len(pairs),
    }


def _analyze_scale(
    role: str,
    output_root: Path,
    depth_index: int,
    seed_base: int,
) -> dict[str, Any]:
    rows, hidden = _load_chunk(role, "scale", output_root)
    lookup = _scale_lookup(rows)
    per_n: dict[int, dict[str, list[float]]] = {
        n: defaultdict(list) for n in SCALE_N_VALUES
    }
    match_pairs: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = {
        "within_cycle_forward": [],
        "cross_cycle_forward": [],
    }
    match_pairs_by_n: dict[
        str, dict[int, list[tuple[Mapping[str, Any], Mapping[str, Any]]]]
    ] = {variant: defaultdict(list) for variant in match_pairs}
    units: list[dict[str, Any]] = []
    for system_id in SYSTEM_IDS:
        for rotation in ROTATIONS:
            for wrapper_id in WRAPPER_IDS:
                base_row = lookup[
                    (system_id, rotation, 1, wrapper_id, "clone_exact_utf")
                ]
                n1 = {
                    int(
                        lookup[(system_id, rotation, 1, wrapper_id, variant)][
                            "unique_prompt_index"
                        ]
                    )
                    for variant in SCALE_VARIANTS
                }
                _require(
                    n1 == {int(base_row["unique_prompt_index"])},
                    "Scale n=1 prompt invariant failed",
                )
                base = _hidden_vector(hidden, base_row, depth_index)
                endpoint_values: dict[str, list[float]] = defaultdict(list)
                for n in SCALE_N_VALUES:
                    clone_row = lookup[
                        (system_id, rotation, n, wrapper_id, "clone_exact_utf")
                    ]
                    within_row = lookup[
                        (system_id, rotation, n, wrapper_id, "within_cycle_forward")
                    ]
                    cross_row = lookup[
                        (system_id, rotation, n, wrapper_id, "cross_cycle_forward")
                    ]
                    clone = _hidden_vector(hidden, clone_row, depth_index)
                    within = _hidden_vector(hidden, within_row, depth_index)
                    cross = _hidden_vector(hidden, cross_row, depth_index)
                    values = {
                        "clone_growth": _cosine_distance(clone, base),
                        "within_extra": _cosine_distance(within, clone),
                        "cross_extra": _cosine_distance(cross, clone),
                    }
                    values["cross_minus_within"] = (
                        values["cross_extra"] - values["within_extra"]
                    )
                    for name, value in values.items():
                        per_n[n][name].append(value)
                        if n > 1:
                            endpoint_values[name].append(value)
                    if n > 1:
                        for variant, row in (
                            ("within_cycle_forward", within_row),
                            ("cross_cycle_forward", cross_row),
                        ):
                            pair = (clone_row, row)
                            match_pairs[variant].append(pair)
                            match_pairs_by_n[variant][n].append(pair)
                units.append(
                    {
                        "system_id": system_id,
                        "rotation": rotation,
                        "wrapper_id": wrapper_id,
                        **{
                            name: float(np.mean(values))
                            for name, values in endpoint_values.items()
                        },
                    }
                )
    _require(len(units) == 96, "Scale principal-unit count changed")
    n1_values = per_n[1]
    _require(
        all(
            max(abs(value) for value in values) <= 1.0e-12
            for values in n1_values.values()
        ),
        "Scale n=1 geometry invariant failed",
    )
    summaries = {
        name: _unit_summary(units, name, seed_base + offset)
        for offset, name in enumerate(
            ("clone_growth", "within_extra", "cross_extra", "cross_minus_within")
        )
    }
    return {
        "primary_summaries": summaries,
        "per_n_medians": {
            str(n): {
                name: float(np.median(values)) for name, values in per_n[n].items()
            }
            for n in SCALE_N_VALUES
        },
        "token_matching": {
            variant: {
                "all_n_gt_1": _match_rates(pairs),
                "by_n": {
                    str(n): _match_rates(match_pairs_by_n[variant][n])
                    for n in SCALE_N_VALUES
                    if n > 1
                },
            }
            for variant, pairs in match_pairs.items()
        },
        "n1_exact_geometry_zero": True,
    }


def _analyze_order(
    role: str,
    output_root: Path,
    depth_index: int,
    seed_base: int,
) -> dict[str, Any]:
    loaded = {
        separator: _load_chunk(role, f"order_{separator}", output_root)
        for separator in SEPARATORS
    }
    lookups = {
        separator: _order_lookup(rows) for separator, (rows, _hidden) in loaded.items()
    }
    result: dict[str, Any] = {}
    offset = 0
    for family in DIVERSITY_FAMILIES:
        family_result: dict[str, Any] = {}
        for variant in ORDER_VARIANTS[1:]:
            unit_rows: list[dict[str, Any]] = []
            per_n: dict[int, list[float]] = defaultdict(list)
            per_separator: dict[str, list[float]] = defaultdict(list)
            pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
            for system_id in SYSTEM_IDS:
                for rotation in ROTATIONS:
                    for wrapper_id in WRAPPER_IDS:
                        values: list[float] = []
                        for separator in SEPARATORS:
                            _rows, hidden = loaded[separator]
                            lookup = lookups[separator]
                            for n in VARIANT_N_VALUES:
                                reference = lookup[
                                    (
                                        system_id,
                                        rotation,
                                        n,
                                        wrapper_id,
                                        family,
                                        "forward_tail",
                                    )
                                ]
                                observed = lookup[
                                    (
                                        system_id,
                                        rotation,
                                        n,
                                        wrapper_id,
                                        family,
                                        variant,
                                    )
                                ]
                                _require(
                                    reference["item_multiset_sha256"]
                                    == observed["item_multiset_sha256"],
                                    "Order item multiset changed",
                                )
                                value = _cosine_distance(
                                    _hidden_vector(hidden, observed, depth_index),
                                    _hidden_vector(hidden, reference, depth_index),
                                )
                                values.append(value)
                                per_n[n].append(value)
                                per_separator[separator].append(value)
                                pairs.append((reference, observed))
                        unit_rows.append(
                            {
                                "system_id": system_id,
                                "rotation": rotation,
                                "wrapper_id": wrapper_id,
                                "order_displacement": float(np.mean(values)),
                            }
                        )
            family_result[variant] = {
                "primary_summary": _unit_summary(
                    unit_rows, "order_displacement", seed_base + offset
                ),
                "per_n_median": {
                    str(n): float(np.median(per_n[n])) for n in VARIANT_N_VALUES
                },
                "per_separator_median": {
                    separator: float(np.median(per_separator[separator]))
                    for separator in SEPARATORS
                },
                "token_matching": _match_rates(pairs),
            }
            offset += 1
        result[family] = family_result
    return result


def _analyze_position(
    role: str,
    output_root: Path,
    depth_index: int,
    seed_base: int,
) -> dict[str, Any]:
    loaded = {
        separator: _load_chunk(role, f"position_{separator}", output_root)
        for separator in SEPARATORS
    }
    lookups = {
        separator: _position_lookup(rows)
        for separator, (rows, _hidden) in loaded.items()
    }
    result: dict[str, Any] = {}
    offset = 0
    for family in DIVERSITY_FAMILIES:
        family_result: dict[str, Any] = {}
        for position in ANCHOR_POSITIONS[1:]:
            unit_rows: list[dict[str, Any]] = []
            per_n: dict[int, list[float]] = defaultdict(list)
            per_separator: dict[str, list[float]] = defaultdict(list)
            pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
            for system_id in SYSTEM_IDS:
                for rotation in ROTATIONS:
                    for wrapper_id in WRAPPER_IDS:
                        values: list[float] = []
                        for separator in SEPARATORS:
                            _rows, hidden = loaded[separator]
                            lookup = lookups[separator]
                            for n in VARIANT_N_VALUES:
                                reference = lookup[
                                    (
                                        system_id,
                                        rotation,
                                        n,
                                        wrapper_id,
                                        family,
                                        "first",
                                    )
                                ]
                                observed = lookup[
                                    (
                                        system_id,
                                        rotation,
                                        n,
                                        wrapper_id,
                                        family,
                                        position,
                                    )
                                ]
                                _require(
                                    reference["item_multiset_sha256"]
                                    == observed["item_multiset_sha256"],
                                    "Position item multiset changed",
                                )
                                value = _cosine_distance(
                                    _hidden_vector(hidden, observed, depth_index),
                                    _hidden_vector(hidden, reference, depth_index),
                                )
                                values.append(value)
                                per_n[n].append(value)
                                per_separator[separator].append(value)
                                pairs.append((reference, observed))
                        unit_rows.append(
                            {
                                "system_id": system_id,
                                "rotation": rotation,
                                "wrapper_id": wrapper_id,
                                "position_displacement": float(np.mean(values)),
                            }
                        )
            family_result[position] = {
                "primary_summary": _unit_summary(
                    unit_rows, "position_displacement", seed_base + offset
                ),
                "per_n_median": {
                    str(n): float(np.median(per_n[n])) for n in VARIANT_N_VALUES
                },
                "per_separator_median": {
                    separator: float(np.median(per_separator[separator]))
                    for separator in SEPARATORS
                },
                "token_matching": _match_rates(pairs),
            }
            offset += 1
        result[family] = family_result
    return result


def _analyze_separators(
    role: str,
    output_root: Path,
    depth_index: int,
    seed_base: int,
) -> dict[str, Any]:
    loaded = {
        separator: _load_chunk(role, f"order_{separator}", output_root)
        for separator in SEPARATORS
    }
    lookups = {
        separator: _order_lookup(rows) for separator, (rows, _hidden) in loaded.items()
    }
    reference_rows, reference_hidden = loaded["none"]
    del reference_rows
    result: dict[str, Any] = {}
    for offset, separator in enumerate(tuple(SEPARATORS)[1:]):
        _rows, observed_hidden = loaded[separator]
        unit_rows: list[dict[str, Any]] = []
        per_n: dict[int, list[float]] = defaultdict(list)
        pairs: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        for system_id in SYSTEM_IDS:
            for rotation in ROTATIONS:
                for wrapper_id in WRAPPER_IDS:
                    values: list[float] = []
                    for family in DIVERSITY_FAMILIES:
                        for variant in ORDER_VARIANTS:
                            for n in VARIANT_N_VALUES:
                                key = (
                                    system_id,
                                    rotation,
                                    n,
                                    wrapper_id,
                                    family,
                                    variant,
                                )
                                reference = lookups["none"][key]
                                observed = lookups[separator][key]
                                _require(
                                    reference["item_order_sha256"]
                                    == observed["item_order_sha256"],
                                    "Separator changed item order",
                                )
                                value = _cosine_distance(
                                    _hidden_vector(
                                        observed_hidden, observed, depth_index
                                    ),
                                    _hidden_vector(
                                        reference_hidden, reference, depth_index
                                    ),
                                )
                                values.append(value)
                                per_n[n].append(value)
                                pairs.append((reference, observed))
                    unit_rows.append(
                        {
                            "system_id": system_id,
                            "rotation": rotation,
                            "wrapper_id": wrapper_id,
                            "separator_displacement": float(np.mean(values)),
                        }
                    )
        result[separator] = {
            "primary_summary": _unit_summary(
                unit_rows, "separator_displacement", seed_base + offset
            ),
            "per_n_median": {
                str(n): float(np.median(per_n[n])) for n in VARIANT_N_VALUES
            },
            "token_matching": _match_rates(pairs),
        }
    return result


def analyze(output_root: Path, output: Path) -> dict[str, Any]:
    audit = audit_run(output_root)
    seed = int(_config()["analysis"]["uncertainty"]["bootstrap_seed"])
    all_results: dict[str, Any] = {}
    for role_index, role in enumerate(MODEL_ROLES):
        role_result: dict[str, Any] = {}
        receipt = _read_json(output_root / role / "scale" / "receipt.json")
        for depth_index, depth in enumerate(
            _config()["capture"]["normalized_depth_fractions"]
        ):
            cell_seed = seed + role_index * 100_000 + depth_index * 1_000
            role_result[f"depth_{float(depth):g}"] = {
                "block_index": int(receipt["block_indices"][depth_index]),
                "scale": _analyze_scale(role, output_root, depth_index, cell_seed),
                "order": _analyze_order(
                    role, output_root, depth_index, cell_seed + 100
                ),
                "position": _analyze_position(
                    role, output_root, depth_index, cell_seed + 200
                ),
                "separator": _analyze_separators(
                    role, output_root, depth_index, cell_seed + 300
                ),
            }
        all_results[role] = role_result
    cross_model: dict[str, Any] = {}
    for depth in _config()["capture"]["normalized_depth_fractions"]:
        depth_key = f"depth_{float(depth):g}"
        medians = {
            role: float(
                all_results[role][depth_key]["scale"]["primary_summaries"][
                    "cross_minus_within"
                ]["principal_unit_median"]
            )
            for role in MODEL_ROLES
        }
        n500 = {
            role: float(
                all_results[role][depth_key]["scale"]["per_n_medians"]["500"][
                    "cross_minus_within"
                ]
            )
            for role in MODEL_ROLES
        }
        cross_model[depth_key] = {
            "scale_cross_minus_within_positive_cells": sum(
                value > 0.0 for value in medians.values()
            ),
            "scale_cross_minus_within_medians": medians,
            "n500_cross_minus_within_positive_cells": sum(
                value > 0.0 for value in n500.values()
            ),
            "n500_cross_minus_within_medians": n500,
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "utf_scale_variants_analysis_complete",
        "audit": audit,
        "results": all_results,
        "cross_model_descriptive": cross_model,
        "decision_status": "exploratory_no_binary_scientific_gate",
        "claim_boundary": _config()["claim_boundary"],
        "tokenizer_independent_unicode_claim_authorized": False,
        "emoji_meaning_claim_authorized": False,
        "causal_circuit_claim_authorized": False,
        "instruction_tuning_effect_claim_authorized": False,
        "scaling_law_claim_authorized": False,
        "model_population_generality_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-design")
    design = subparsers.add_parser("write-design-preflight")
    design.add_argument("--output", type=Path, default=DESIGN_PREFLIGHT_PATH)
    preflight = subparsers.add_parser("preflight-role")
    preflight.add_argument("--role", required=True)
    preflight.add_argument("--output", type=Path, required=True)
    preflight.add_argument("--model-path", type=Path)
    aggregate = subparsers.add_parser("aggregate-preflight")
    aggregate.add_argument("--directory", type=Path, required=True)
    aggregate.add_argument("--output", type=Path, required=True)
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=FREEZE_PATH)
    audit_freeze_parser = subparsers.add_parser("audit-freeze")
    audit_freeze_parser.add_argument("--require-pushed", action="store_true")
    run_parser = subparsers.add_parser("run-role")
    run_parser.add_argument("--role", required=True)
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--model-preflight-directory", type=Path, required=True)
    run_parser.add_argument("--model-path", type=Path)
    audit_parser = subparsers.add_parser("audit-run")
    audit_parser.add_argument("--output-root", type=Path, required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--output-root", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "write-design-preflight":
        result = write_design_preflight(args.output)
    elif args.command == "preflight-role":
        result = tokenizer_preflight(args.role, args.output, args.model_path)
    elif args.command == "aggregate-preflight":
        result = aggregate_preflight(args.directory, args.output)
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze(require_pushed=args.require_pushed)
    elif args.command == "run-role":
        result = run_role(
            role=args.role,
            output_root=args.output_root,
            model_preflight_directory=args.model_preflight_directory,
            model_path=args.model_path,
        )
    elif args.command == "audit-run":
        result = audit_run(args.output_root)
    else:
        result = analyze(args.output_root, args.output)
    _print(result)


if __name__ == "__main__":
    main()
