#!/usr/bin/env python3
"""Freeze, capture, and analyze the T17-GN glyph/name depth trajectory."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import uuid

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-glyph-name-depth-trajectory-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/glyph_name_depth_trajectory_v0.yaml")
VALIDATION_DIRECTORY = Path("validation/glyph_name_depth_trajectory_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
FREEZE_PATH = Path("data/manifests/glyph_name_depth_trajectory_v0.json")
VIEW_ORDER = ("glyph", "unicode_name", "codepoint_literal")
PAIR_ORDER = (("glyph_name", 0, 1), ("glyph_codepoint", 0, 2))
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
DEPTH_FRACTIONS = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
SOURCE_BINDING_KEYS = (
    "population_manifest",
    "t10_freeze_manifest",
    "t9_primary_result",
    "t10_primary_result",
    "t10_engineering_preflight",
)
STATIC_ASSETS = (
    "configs/glyph_name_depth_trajectory_v0.yaml",
    "docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0.md",
    "docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0.ja.md",
    "scripts/glyph_name_depth_trajectory_v0.py",
    "tests/test_glyph_name_depth_trajectory_v0.py",
    "validation/glyph_name_depth_trajectory_v0/design_preflight.json",
)


class TrajectoryError(RuntimeError):
    """Raised when a frozen T17-GN contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TrajectoryError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def _source_paths() -> tuple[tuple[Path, str], ...]:
    bindings = _config()["source_bindings"]
    return tuple(
        (
            _root() / str(bindings[key]),
            str(bindings[f"{key}_sha256"]),
        )
        for key in SOURCE_BINDING_KEYS
    )


def resolved_layers(role: str) -> tuple[int, ...]:
    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    count = int(t10._model_spec(role)["expected_num_layers"])
    return tuple(
        min(count - 1, math.floor(fraction * count)) for fraction in DEPTH_FRACTIONS
    )


def audit_design() -> dict[str, Any]:
    config = _config()
    _require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model order changed")
    _require(
        tuple(float(value) for value in config["depth"]["normalized_fractions"])
        == DEPTH_FRACTIONS,
        "Depth fractions changed",
    )
    _require(
        tuple(t10.model_roles()) != MODEL_ROLES,
        "T17 order must be independent of T10 display order",
    )
    _require(set(t10.model_roles()) == set(MODEL_ROLES), "T10/T17 model roster changed")
    population = t10.items()
    _require(len(population) == 292, "Population count changed")
    _require(
        [int(row["source_index"]) for row in population]
        == sorted(int(row["source_index"]) for row in population),
        "Population order changed",
    )
    source_hashes: dict[str, str] = {}
    for path, expected in _source_paths():
        _require(path.is_file(), f"Bound source missing: {path}")
        actual = _sha256(path)
        _require(actual == expected, f"Bound source changed: {path.name}")
        source_hashes[path.relative_to(_root()).as_posix()] = actual
    resolved = {role: list(resolved_layers(role)) for role in MODEL_ROLES}
    _require(
        all(len(set(indices)) == len(DEPTH_FRACTIONS) for indices in resolved.values()),
        "Depth resolution collapsed",
    )
    forwards_per_model = len(population) * len(VIEW_ORDER) * 2
    vectors_per_model = forwards_per_model * 4 * len(DEPTH_FRACTIONS)
    acquisition = config["acquisition"]
    _require(
        forwards_per_model
        == int(acquisition["expected_model_forward_calls_per_model"]),
        "Forward budget changed",
    )
    _require(
        vectors_per_model == int(acquisition["expected_readout_vectors_per_model"]),
        "Vector budget changed",
    )
    _require(
        forwards_per_model * len(MODEL_ROLES)
        == int(acquisition["expected_total_model_forward_calls"]),
        "Total forward budget changed",
    )
    _require(
        vectors_per_model * len(MODEL_ROLES)
        == int(acquisition["expected_total_readout_vectors"]),
        "Total vector budget changed",
    )
    t9 = _read_json(_root() / str(config["source_bindings"]["t9_primary_result"]))
    t10_primary = _read_json(
        _root() / str(config["source_bindings"]["t10_primary_result"])
    )
    _require(t9.get("alignment_confirmed") is True, "T9 source outcome changed")
    _require(t10_primary.get("positive") is False, "T10 source outcome changed")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t17_model_forwards",
        "population_items": len(population),
        "views": list(VIEW_ORDER),
        "model_roles": list(MODEL_ROLES),
        "resolved_block_indices": resolved,
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "model_forwards_per_role": forwards_per_model,
        "model_forwards_total": forwards_per_model * len(MODEL_ROLES),
        "readout_vectors_per_role": vectors_per_model,
        "readout_vectors_total": vectors_per_model * len(MODEL_ROLES),
        "source_hashes": source_hashes,
        "population_prior_exposed": True,
        "confirmatory_claim_authorized": False,
        "rendered_glyph_perception_claim_authorized": False,
        "model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    _require(not output.exists(), f"Design preflight exists: {output}")
    value = audit_design()
    _write_json(output, value)
    return {"status": "pass", "output": output.as_posix(), "sha256": _sha256(output)}


def _frozen_assets() -> tuple[str, ...]:
    sources = tuple(path.relative_to(_root()).as_posix() for path, _ in _source_paths())
    tokenizers = tuple(
        (
            Path("validation/semantic_atlas_cross_model_replication_v0/tokenizers")
            / f"{role}.json"
        ).as_posix()
        for role in MODEL_ROLES
    )
    return STATIC_ASSETS + sources + tokenizers


def freeze(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(
        design.get("status") == "design_pass_zero_t17_model_forwards",
        "Design preflight incomplete",
    )
    _require(
        int(design.get("model_forwards", -1)) == 0,
        "Design preflight used a model forward",
    )
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        _require(path.is_file(), f"Frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    t10_freeze = _read_json(
        _root() / "data/manifests/semantic_atlas_cross_model_replication_v0.json"
    )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t17_model_forwards",
        "experiment_role": _config()["experiment_role"],
        "claim_boundary": _config()["claim_boundary"],
        "assets": assets,
        "model_artifacts": t10_freeze["model_artifacts"],
        "model_roles": list(MODEL_ROLES),
        "population_items": 292,
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "resolved_block_indices": design["resolved_block_indices"],
        "model_forwards_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "confirmatory_claim_authorized": False,
    }
    _require(not output.exists(), f"Freeze manifest exists: {output}")
    _write_json(output, value)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
    }


def _git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_root(), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def audit_freeze(*, require_pushed: bool = False) -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch")
    _require(
        value.get("status") == "final_execution_freeze_zero_t17_model_forwards",
        "Freeze status incomplete",
    )
    for relative, expected in value["assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"Frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"Frozen asset changed: {relative}")
    git: dict[str, Any] = {"required": False}
    if require_pushed:
        head = _git_value("rev-parse", "HEAD")
        remote_main = _git_value("rev-parse", "origin/main")
        _require(
            head == remote_main, "T17-GN freeze commit is not pushed to origin/main"
        )
        _git_value("cat-file", "-e", f"HEAD:{FREEZE_PATH.as_posix()}")
        git = {"required": True, "head": head, "origin_main": remote_main}
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path), "git": git}


def _yield_if_contended(output_root: Path, role: str, boundary: str) -> None:
    pids = atlas._foreign_gpu_pids()
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


def _shard_count() -> int:
    return math.ceil(
        len(t10.items()) / int(_config()["acquisition"]["item_shard_size"])
    )


def _capture_shard(
    *,
    role: str,
    shard_index: int,
    output_root: Path,
    torch: Any,
    tokenizer: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
    roster: Mapping[str, Any],
) -> dict[str, Any]:
    del tokenizer
    config = _config()
    role_root = output_root / role
    final = role_root / f"shard_{shard_index:04d}"
    if final.is_dir():
        return validate_shard(role, shard_index, output_root)
    _yield_if_contended(output_root, role, f"before_shard_{shard_index:04d}")
    role_root.mkdir(parents=True, exist_ok=True)
    stale = list(role_root.glob(f".shard_{shard_index:04d}.stage-*"))
    _require(not stale, f"Incomplete shard stage requires adjudication: {stale}")
    stage = role_root / f".shard_{shard_index:04d}.stage-{uuid.uuid4().hex}"
    stage.mkdir()
    population = t10.items()
    size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * size
    stop = min(len(population), start + size)
    _require(start < stop, f"Shard index out of range: {shard_index}")
    shard_items = population[start:stop]
    layer_indices = resolved_layers(role)
    width = int(t10._model_spec(role)["expected_model_dim"])
    activations = np.empty(
        (len(shard_items), 3, 2, 4, len(DEPTH_FRACTIONS), width),
        dtype=np.float32,
    )
    all_records = t10._records(roster, t10._config())
    records = [
        {**row, "item_offset": int(row["item_offset"]) - start}
        for row in all_records
        if start <= int(row["item_offset"]) < stop
    ]
    _require(len(records) == len(shard_items) * 6, "Shard record count changed")
    _write_json(
        stage / "execution_intent.json",
        {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "forward_may_begin_after_this_record",
            "model_role": role,
            "shard_index": shard_index,
            "item_index_start": start,
            "item_index_stop_exclusive": stop,
            "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        },
    )
    distances = [int(value) for value in config["input"]["distance_order"]]
    observations: list[dict[str, Any]] = []
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for record_index, row in enumerate(records):
        if record_index and record_index % 128 == 0:
            _yield_if_contended(
                output_root, role, f"shard_{shard_index:04d}_record_{record_index}"
            )
        ids = [int(value) for value in row["input_ids"]]
        input_ids = torch.tensor([ids], dtype=torch.long, device="cuda")
        attention_mask = torch.ones_like(input_ids)
        positions = [len(row["raw_ids"]) + distance - 1 for distance in distances]
        before = time.perf_counter()
        with torch.inference_mode():
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                output_hidden_states=True,
                return_dict=True,
            )
        torch.cuda.synchronize()
        states = tuple(output.hidden_states[index + 1] for index in layer_indices)
        _require(len(states) == len(DEPTH_FRACTIONS), "Depth state count changed")
        selected = torch.stack(states, dim=2)
        position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
        captured = selected[0, position_tensor].float().cpu().numpy()
        _require(
            captured.shape == (4, len(DEPTH_FRACTIONS), width), "Captured shape changed"
        )
        _require(bool(np.isfinite(captured).all()), "Nonfinite activation")
        local_index = int(row["item_offset"])
        activations[local_index, int(row["view_index"]), int(row["carrier_index"])] = (
            captured
        )
        item = shard_items[local_index]
        observations.append(
            {
                "item_index": start + local_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "view": str(row["view"]),
                "carrier": str(row["carrier"]),
                "raw_token_count": len(row["raw_ids"]),
                "input_token_count": len(ids),
                "readout_positions": positions,
                "forward_latency_ms": (time.perf_counter() - before) * 1000.0,
            }
        )
        del (
            output,
            states,
            selected,
            position_tensor,
            captured,
            input_ids,
            attention_mask,
        )
    _require(bool(np.isfinite(activations).all()), "Shard contains nonfinite values")
    np.save(stage / "activations.npy", activations, allow_pickle=False)
    _write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "glyph_name_depth_shard_complete",
        "model_role": role,
        "shard_index": shard_index,
        "item_index_start": start,
        "item_index_stop_exclusive": stop,
        "item_count": len(shard_items),
        "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        "activation_shape": list(activations.shape),
        "activation_dtype": str(activations.dtype),
        "axis_order": config["acquisition"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": list(config["input"]["carrier_order"]),
        "distance_order": distances,
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "resolved_block_indices": list(layer_indices),
        "model_forward_calls": len(records),
        "readout_vectors": int(np.prod(activations.shape[:-1])),
        "elapsed_seconds": time.perf_counter() - started,
        "peak_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "model": dict(model_receipt),
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "outputs": {
            "execution_intent.json": _sha256(stage / "execution_intent.json"),
            "activations.npy": _sha256(stage / "activations.npy"),
            "observations.jsonl": _sha256(stage / "observations.jsonl"),
        },
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_shard(role, shard_index, output_root)


def validate_shard(role: str, shard_index: int, output_root: Path) -> dict[str, Any]:
    directory = output_root / role / f"shard_{shard_index:04d}"
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Shard protocol mismatch")
    _require(receipt.get("model_role") == role, "Shard role mismatch")
    _require(int(receipt.get("shard_index", -1)) == shard_index, "Shard index mismatch")
    for name, expected in receipt["outputs"].items():
        _require(
            _sha256(directory / name) == expected,
            f"Shard output changed: {role}/{shard_index}/{name}",
        )
    size = int(_config()["acquisition"]["item_shard_size"])
    expected_items = t10.items()[shard_index * size : (shard_index + 1) * size]
    width = int(t10._model_spec(role)["expected_model_dim"])
    expected_shape = (len(expected_items), 3, 2, 4, len(DEPTH_FRACTIONS), width)
    _require(
        tuple(receipt["activation_shape"]) == expected_shape,
        "Shard receipt shape mismatch",
    )
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    _require(
        array.shape == expected_shape and array.dtype == np.float32,
        "Shard array contract mismatch",
    )
    _require(
        int(receipt["model_forward_calls"]) == len(expected_items) * 6,
        "Shard forward count mismatch",
    )
    return {
        "status": "pass",
        "model_role": role,
        "shard_index": shard_index,
        "items": len(expected_items),
        "forwards": int(receipt["model_forward_calls"]),
        "vectors": int(receipt["readout_vectors"]),
    }


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    role_root = output_root / role
    _require(
        not list(role_root.glob(".shard_*.stage-*")),
        f"Incomplete shard stage blocks role: {role}",
    )
    shards = [
        validate_shard(role, index, output_root) for index in range(_shard_count())
    ]
    receipt_path = role_root / "role_receipt.json"
    _require(receipt_path.is_file(), f"Role receipt missing: {role}")
    receipt = _read_json(receipt_path)
    _require(
        receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("model_role") == role,
        "Role receipt mismatch",
    )
    _require(int(receipt["items"]) == len(t10.items()), "Role item count mismatch")
    _require(
        int(receipt["model_forward_calls"]) == sum(row["forwards"] for row in shards),
        "Role forward count mismatch",
    )
    return {
        "status": "pass",
        "model_role": role,
        "items": int(receipt["items"]),
        "shards": len(shards),
        "model_forward_calls": int(receipt["model_forward_calls"]),
        "readout_vectors": int(receipt["readout_vectors"]),
        "elapsed_seconds": float(receipt["elapsed_seconds"]),
        "peak_cuda_memory_bytes": int(receipt["peak_cuda_memory_bytes"]),
    }


def _finalize_role(role: str, output_root: Path) -> dict[str, Any]:
    role_root = output_root / role
    path = role_root / "role_receipt.json"
    if path.exists():
        return validate_role(role, output_root)
    shards = [
        validate_shard(role, index, output_root) for index in range(_shard_count())
    ]
    receipts = [
        _read_json(role_root / f"shard_{index:04d}" / "receipt.json")
        for index in range(_shard_count())
    ]
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "glyph_name_depth_role_complete",
        "model_role": role,
        "items": sum(row["items"] for row in shards),
        "shards": len(shards),
        "model_forward_calls": sum(row["forwards"] for row in shards),
        "readout_vectors": sum(row["vectors"] for row in shards),
        "elapsed_seconds": sum(float(row["elapsed_seconds"]) for row in receipts),
        "peak_cuda_memory_bytes": max(
            int(row["peak_cuda_memory_bytes"]) for row in receipts
        ),
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(path, value)
    return validate_role(role, output_root)


def run_role(role: str, model_path: Path, output_root: Path) -> dict[str, Any]:
    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    audit_freeze(require_pushed=True)
    role_root = output_root / role
    if (role_root / "role_receipt.json").exists():
        return validate_role(role, output_root)
    _yield_if_contended(output_root, role, "before_model_load")
    torch, tokenizer, model, _last_block, model_receipt, roster = t10._load_model(
        role, model_path
    )
    try:
        for shard_index in range(_shard_count()):
            _capture_shard(
                role=role,
                shard_index=shard_index,
                output_root=output_root,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                model_receipt=model_receipt,
                roster=roster,
            )
    finally:
        del model
        torch.cuda.empty_cache()
    return _finalize_role(role, output_root)


def audit_run(output_root: Path) -> dict[str, Any]:
    roles = [validate_role(role, output_root) for role in MODEL_ROLES]
    return {
        "status": "all_nine_roles_complete",
        "protocol_id": PROTOCOL_ID,
        "roles_complete": len(roles),
        "items_per_role": sorted({row["items"] for row in roles}),
        "shards_complete": sum(row["shards"] for row in roles),
        "model_forward_calls": sum(row["model_forward_calls"] for row in roles),
        "readout_vectors": sum(row["readout_vectors"] for row in roles),
        "elapsed_seconds": sum(row["elapsed_seconds"] for row in roles),
        "maximum_peak_cuda_memory_bytes": max(
            row["peak_cuda_memory_bytes"] for row in roles
        ),
        "intervention_calls": 0,
        "generation_calls": 0,
    }


def _normalized_view(value: np.ndarray) -> np.ndarray:
    centered = np.asarray(value, dtype=np.float64) - np.mean(
        value, axis=0, keepdims=True, dtype=np.float64
    )
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    _require(bool(np.all(norms > 0.0)), "Zero centered row norm")
    return centered / norms


def _pair_metrics(
    first: np.ndarray, second: np.ndarray
) -> tuple[dict[str, float], np.ndarray]:
    left = _normalized_view(first)
    right = _normalized_view(second)
    similarities = left @ right.T
    count = similarities.shape[0]
    order = np.arange(count)
    diagonal = similarities[order, order]
    forward = np.argmax(similarities, axis=1)
    reverse = np.argmax(similarities, axis=0)
    rank_forward = 1 + np.sum(similarities > diagonal[:, None], axis=1)
    rank_reverse = 1 + np.sum(similarities > diagonal[None, :], axis=0)
    off_diagonal = (float(np.sum(similarities)) - float(np.sum(diagonal))) / (
        count * (count - 1)
    )
    left_gram = left @ left.T
    right_gram = right @ right.T
    denominator = math.sqrt(
        float(np.sum(left_gram * left_gram)) * float(np.sum(right_gram * right_gram))
    )
    _require(denominator > 0.0, "CKA denominator is zero")
    metrics = {
        "paired_cosine_mean": float(np.mean(diagonal)),
        "off_diagonal_cosine_mean": off_diagonal,
        "paired_minus_off_diagonal_margin": float(np.mean(diagonal)) - off_diagonal,
        "top1_accuracy_forward": float(np.mean(forward == order)),
        "top1_accuracy_reverse": float(np.mean(reverse == order)),
        "mean_reciprocal_rank_forward": float(np.mean(1.0 / rank_forward)),
        "mean_reciprocal_rank_reverse": float(np.mean(1.0 / rank_reverse)),
        "centered_linear_cka": float(np.sum(left_gram * right_gram) / denominator),
    }
    correctness = (forward == order).astype(np.float64)
    return metrics, correctness


def _context_metrics(values: np.ndarray) -> tuple[dict[str, Any], np.ndarray]:
    pairs: dict[str, dict[str, float]] = {}
    correctness: dict[str, np.ndarray] = {}
    for name, left, right in PAIR_ORDER:
        pairs[name], correctness[name] = _pair_metrics(
            values[:, left], values[:, right]
        )
    difference = {
        key: float(pairs["glyph_name"][key] - pairs["glyph_codepoint"][key])
        for key in pairs["glyph_name"]
    }
    return {
        "pairs": pairs,
        "glyph_name_minus_glyph_codepoint": difference,
    }, correctness["glyph_name"] - correctness["glyph_codepoint"]


def _bootstrap_intervals(
    item_effects: np.ndarray, replicates: int, seed: int
) -> list[list[float]]:
    count = item_effects.shape[0]
    rng = np.random.default_rng(seed)
    probabilities = np.full(count, 1.0 / count, dtype=np.float64)
    bootstrap = np.empty((replicates, item_effects.shape[1]), dtype=np.float64)
    chunk = 1000
    for start in range(0, replicates, chunk):
        stop = min(replicates, start + chunk)
        weights = rng.multinomial(count, probabilities, size=stop - start)
        bootstrap[start:stop] = (weights @ item_effects) / count
    return [
        [
            float(np.quantile(bootstrap[:, index], 0.025)),
            float(np.quantile(bootstrap[:, index], 0.975)),
        ]
        for index in range(item_effects.shape[1])
    ]


def _trajectory_summary(depth_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    values = [float(row["headline_top1_contrast_mean"]) for row in depth_rows]
    lowers = [float(row["bootstrap_95_percent_interval"][0]) for row in depth_rows]
    sustained_point = next(
        (
            DEPTH_FRACTIONS[index]
            for index in range(len(values))
            if all(value > 0.0 for value in values[index:])
        ),
        None,
    )
    sustained_interval = next(
        (
            DEPTH_FRACTIONS[index]
            for index in range(len(lowers))
            if all(value > 0.0 for value in lowers[index:])
        ),
        None,
    )
    peak_index = max(range(len(values)), key=values.__getitem__)
    return {
        "initial_value": values[0],
        "final_value": values[-1],
        "final_minus_initial": values[-1] - values[0],
        "peak_normalized_depth": DEPTH_FRACTIONS[peak_index],
        "peak_value": values[peak_index],
        "earliest_sustained_positive_point_estimate_depth": sustained_point,
        "earliest_sustained_positive_bootstrap_interval_depth": sustained_interval,
        "trapezoidal_depth_auc": float(
            np.trapezoid(values, x=np.asarray(DEPTH_FRACTIONS))
        ),
        "positive_depth_count": sum(value > 0.0 for value in values),
        "bootstrap_lower_positive_depth_count": sum(value > 0.0 for value in lowers),
    }


def _load_role_array(role: str, output_root: Path) -> np.ndarray:
    arrays = [
        np.load(
            output_root / role / f"shard_{index:04d}" / "activations.npy",
            mmap_mode="r",
            allow_pickle=False,
        )
        for index in range(_shard_count())
    ]
    result = np.concatenate(arrays, axis=0)
    _require(
        result.shape[0] == len(t10.items()), f"Role array item count changed: {role}"
    )
    return result


def _analyze_role(role: str, output_root: Path, role_index: int) -> dict[str, Any]:
    values = _load_role_array(role, output_root)
    tokenizer_receipt = _read_json(t10._receipt_path(role))
    eligible = np.asarray(
        tokenizer_receipt["tokenizer"]["exact_triple_strata"][
            "eligible_global_indices"
        ],
        dtype=np.int64,
    )
    context_order = [
        {"carrier": carrier, "distance": distance}
        for carrier in _config()["input"]["carrier_order"]
        for distance in _config()["input"]["distance_order"]
    ]
    depth_rows: list[dict[str, Any]] = []
    full_effects: list[np.ndarray] = []
    matched_effects: list[np.ndarray] = []
    cell_rows: list[dict[str, Any]] = []
    for depth_index, depth in enumerate(DEPTH_FRACTIONS):
        context_effects: list[np.ndarray] = []
        context_effects_matched: list[np.ndarray] = []
        depth_cells: list[dict[str, Any]] = []
        for carrier_index, carrier in enumerate(_config()["input"]["carrier_order"]):
            for distance_index, distance in enumerate(
                _config()["input"]["distance_order"]
            ):
                cell_values = np.asarray(
                    values[:, :, carrier_index, distance_index, depth_index, :]
                )
                metrics, effect = _context_metrics(cell_values)
                matched_metrics, matched_effect = _context_metrics(
                    cell_values[eligible]
                )
                row = {
                    "model_role": role,
                    "normalized_depth": depth,
                    "resolved_block_index": resolved_layers(role)[depth_index],
                    "carrier": carrier,
                    "distance": distance,
                    "unrestricted": metrics,
                    "tokenization_matched": {
                        "item_count": int(len(eligible)),
                        **matched_metrics,
                    },
                }
                cell_rows.append(row)
                depth_cells.append(row)
                context_effects.append(effect)
                context_effects_matched.append(matched_effect)
        item_effect = np.mean(np.stack(context_effects), axis=0)
        item_effect_matched = np.mean(np.stack(context_effects_matched), axis=0)
        full_effects.append(item_effect)
        matched_effects.append(item_effect_matched)
        name_top1 = [
            row["unrestricted"]["pairs"]["glyph_name"]["top1_accuracy_forward"]
            for row in depth_cells
        ]
        codepoint_top1 = [
            row["unrestricted"]["pairs"]["glyph_codepoint"]["top1_accuracy_forward"]
            for row in depth_cells
        ]
        margins = [
            row["unrestricted"]["glyph_name_minus_glyph_codepoint"][
                "paired_minus_off_diagonal_margin"
            ]
            for row in depth_cells
        ]
        cka = [
            row["unrestricted"]["glyph_name_minus_glyph_codepoint"][
                "centered_linear_cka"
            ]
            for row in depth_cells
        ]
        matched_contrasts = [
            row["tokenization_matched"]["glyph_name_minus_glyph_codepoint"][
                "top1_accuracy_forward"
            ]
            for row in depth_cells
        ]
        depth_rows.append(
            {
                "normalized_depth": depth,
                "resolved_block_index": resolved_layers(role)[depth_index],
                "context_count": len(depth_cells),
                "headline_top1_contrast_mean": float(np.mean(item_effect)),
                "headline_top1_contrast_minimum_context": float(
                    min(np.asarray(name_top1) - np.asarray(codepoint_top1))
                ),
                "glyph_name_top1_mean": float(np.mean(name_top1)),
                "glyph_codepoint_top1_mean": float(np.mean(codepoint_top1)),
                "paired_margin_contrast_mean": float(np.mean(margins)),
                "centered_linear_cka_contrast_mean": float(np.mean(cka)),
                "tokenization_matched_top1_contrast_mean": float(
                    np.mean(matched_contrasts)
                ),
            }
        )
    replicates = int(_config()["analysis"]["uncertainty"]["replicates"])
    seed = int(_config()["analysis"]["uncertainty"]["seed"]) + role_index * 10
    full_matrix = np.stack(full_effects, axis=1)
    matched_matrix = np.stack(matched_effects, axis=1)
    intervals = _bootstrap_intervals(full_matrix, replicates, seed)
    matched_intervals = _bootstrap_intervals(matched_matrix, replicates, seed + 1)
    for index, row in enumerate(depth_rows):
        row["bootstrap_95_percent_interval"] = intervals[index]
        row["tokenization_matched_bootstrap_95_percent_interval"] = matched_intervals[
            index
        ]
    return {
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "resolved_block_indices": list(resolved_layers(role)),
        "item_count": len(t10.items()),
        "tokenization_matched_item_count": int(len(eligible)),
        "context_order": context_order,
        "depth_curve": depth_rows,
        "trajectory": _trajectory_summary(depth_rows),
        "cell_metrics": cell_rows,
    }


def _write_curve_csv(path: Path, results: Mapping[str, Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "model_role",
                "normalized_depth",
                "resolved_block_index",
                "headline_top1_contrast_mean",
                "bootstrap_lower",
                "bootstrap_upper",
                "minimum_context_contrast",
                "glyph_name_top1_mean",
                "glyph_codepoint_top1_mean",
                "paired_margin_contrast_mean",
                "centered_linear_cka_contrast_mean",
                "tokenization_matched_top1_contrast_mean",
            ),
        )
        writer.writeheader()
        for role in MODEL_ROLES:
            for row in results[role]["depth_curve"]:
                writer.writerow(
                    {
                        "model_role": role,
                        "normalized_depth": row["normalized_depth"],
                        "resolved_block_index": row["resolved_block_index"],
                        "headline_top1_contrast_mean": row[
                            "headline_top1_contrast_mean"
                        ],
                        "bootstrap_lower": row["bootstrap_95_percent_interval"][0],
                        "bootstrap_upper": row["bootstrap_95_percent_interval"][1],
                        "minimum_context_contrast": row[
                            "headline_top1_contrast_minimum_context"
                        ],
                        "glyph_name_top1_mean": row["glyph_name_top1_mean"],
                        "glyph_codepoint_top1_mean": row["glyph_codepoint_top1_mean"],
                        "paired_margin_contrast_mean": row[
                            "paired_margin_contrast_mean"
                        ],
                        "centered_linear_cka_contrast_mean": row[
                            "centered_linear_cka_contrast_mean"
                        ],
                        "tokenization_matched_top1_contrast_mean": row[
                            "tokenization_matched_top1_contrast_mean"
                        ],
                    }
                )


def _write_svg(path: Path, results: Mapping[str, Mapping[str, Any]]) -> None:
    width, height = 1100, 680
    left, right, top, bottom = 95, 270, 55, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    all_values = [
        float(row["headline_top1_contrast_mean"])
        for role in MODEL_ROLES
        for row in results[role]["depth_curve"]
    ]
    y_min = min(-0.01, min(all_values))
    y_max = max(0.01, max(all_values))
    pad = max(0.005, (y_max - y_min) * 0.08)
    y_min -= pad
    y_max += pad
    colors = (
        "#0072B2",
        "#E69F00",
        "#009E73",
        "#CC79A7",
        "#56B4E9",
        "#D55E00",
        "#F0E442",
        "#332288",
        "#999999",
    )

    def x(value: float) -> float:
        return left + value * plot_width

    def y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    rows = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="95" y="30" font-family="sans-serif" font-size="20" font-weight="600">T17-GN: glyph→name minus glyph→codepoint retrieval over depth</text>',
    ]
    for tick in np.linspace(y_min, y_max, 7):
        rows.append(
            f'<line x1="{left}" x2="{left + plot_width}" y1="{y(tick):.2f}" y2="{y(tick):.2f}" stroke="#dddddd"/>'
        )
        rows.append(
            f'<text x="{left - 10}" y="{y(tick) + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick:.3f}</text>'
        )
    rows.append(
        f'<line x1="{left}" x2="{left + plot_width}" y1="{y(0):.2f}" y2="{y(0):.2f}" stroke="#222222" stroke-width="1.2"/>'
    )
    for depth in DEPTH_FRACTIONS:
        rows.append(
            f'<line x1="{x(depth):.2f}" x2="{x(depth):.2f}" y1="{top}" y2="{top + plot_height}" stroke="#eeeeee"/>'
        )
        rows.append(
            f'<text x="{x(depth):.2f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="sans-serif" font-size="12">{depth:g}</text>'
        )
    for index, role in enumerate(MODEL_ROLES):
        curve = results[role]["depth_curve"]
        points = " ".join(
            f"{x(float(row['normalized_depth'])):.2f},{y(float(row['headline_top1_contrast_mean'])):.2f}"
            for row in curve
        )
        color = colors[index]
        rows.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.4"/>'
        )
        for row in curve:
            rows.append(
                f'<circle cx="{x(float(row["normalized_depth"])):.2f}" cy="{y(float(row["headline_top1_contrast_mean"])):.2f}" r="2.8" fill="{color}"/>'
            )
        legend_y = top + 20 + index * 28
        rows.append(
            f'<line x1="{left + plot_width + 24}" x2="{left + plot_width + 54}" y1="{legend_y}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        rows.append(
            f'<text x="{left + plot_width + 62}" y="{legend_y + 4}" font-family="sans-serif" font-size="12">{html.escape(role)}</text>'
        )
    rows.extend(
        [
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 25}" text-anchor="middle" font-family="sans-serif" font-size="14">normalized decoder depth</text>',
            f'<text x="22" y="{top + plot_height / 2:.2f}" transform="rotate(-90 22 {top + plot_height / 2:.2f})" text-anchor="middle" font-family="sans-serif" font-size="14">equal-context top-1 contrast</text>',
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def analyze(
    output_root: Path, output: Path, curve_csv: Path, figure: Path
) -> dict[str, Any]:
    audit = audit_run(output_root)
    results = {
        role: _analyze_role(role, output_root, role_index)
        for role_index, role in enumerate(MODEL_ROLES)
    }
    cross_model: list[dict[str, Any]] = []
    for depth_index, depth in enumerate(DEPTH_FRACTIONS):
        rows = [results[role]["depth_curve"][depth_index] for role in MODEL_ROLES]
        values = [float(row["headline_top1_contrast_mean"]) for row in rows]
        cross_model.append(
            {
                "normalized_depth": depth,
                "model_count": len(rows),
                "median_headline_top1_contrast": float(np.median(values)),
                "minimum_headline_top1_contrast": min(values),
                "maximum_headline_top1_contrast": max(values),
                "positive_model_count": sum(value > 0.0 for value in values),
                "bootstrap_lower_positive_model_count": sum(
                    float(row["bootstrap_95_percent_interval"][0]) > 0.0 for row in rows
                ),
                "tokenization_matched_positive_model_count": sum(
                    float(row["tokenization_matched_top1_contrast_mean"]) > 0.0
                    for row in rows
                ),
            }
        )
    qwen_roles = [str(value) for value in _config()["models"]["qwen_scale_order"]]
    qwen_profile = [
        {
            "normalized_depth": depth,
            "ordered_model_roles": qwen_roles,
            "ordered_headline_top1_contrasts": [
                results[role]["depth_curve"][depth_index]["headline_top1_contrast_mean"]
                for role in qwen_roles
            ],
        }
        for depth_index, depth in enumerate(DEPTH_FRACTIONS)
    ]
    _write_curve_csv(curve_csv, results)
    _write_svg(figure, results)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "glyph_name_depth_trajectory_analysis_complete",
        "analysis_role": "exploratory_prior_exposed_depth_atlas",
        "audit": audit,
        "model_order": list(MODEL_ROLES),
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "results": results,
        "cross_model_depth_profile": cross_model,
        "qwen_four_checkpoint_depth_profile": qwen_profile,
        "outputs": {
            "curve_csv": curve_csv.as_posix(),
            "curve_csv_sha256": _sha256(curve_csv),
            "figure": figure.as_posix(),
            "figure_sha256": _sha256(figure),
        },
        "population_prior_exposed": True,
        "confirmatory_claim_authorized": False,
        "rendered_glyph_perception_claim_authorized": False,
        "emoji_meaning_claim_authorized": False,
        "tokenizer_independent_claim_authorized": False,
        "causal_or_behavioral_claim_authorized": False,
        "model_population_generality_claim_authorized": False,
    }
    _write_json(output, payload)
    return {
        "status": "pass",
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "curve_csv_sha256": _sha256(curve_csv),
        "figure_sha256": _sha256(figure),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design")
    preflight = sub.add_parser("write-preflight")
    preflight.add_argument(
        "--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH
    )
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    audit_parser = sub.add_parser("audit-freeze")
    audit_parser.add_argument("--require-pushed", action="store_true")
    run = sub.add_parser("run-role")
    run.add_argument("--role", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    validate = sub.add_parser("validate-role")
    validate.add_argument("--role", choices=MODEL_ROLES, required=True)
    validate.add_argument("--output-root", type=Path, required=True)
    audit = sub.add_parser("audit-run")
    audit.add_argument("--output-root", type=Path, required=True)
    analyze_parser = sub.add_parser("analyze")
    analyze_parser.add_argument("--output-root", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.add_argument("--curve-csv", type=Path, required=True)
    analyze_parser.add_argument("--figure", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "write-preflight":
        result = write_design_preflight(args.output)
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze(require_pushed=args.require_pushed)
    elif args.command == "run-role":
        result = run_role(args.role, args.model_path, args.output_root)
    elif args.command == "validate-role":
        result = validate_role(args.role, args.output_root)
    elif args.command == "audit-run":
        result = audit_run(args.output_root)
    elif args.command == "analyze":
        result = analyze(args.output_root, args.output, args.curve_csv, args.figure)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
