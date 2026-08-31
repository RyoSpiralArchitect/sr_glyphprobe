#!/usr/bin/env python3
"""Freeze, capture, and analyze exact-UTF repetition and mixing."""

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


PROTOCOL_ID = "glyphprobe-t16-utf-identity-mixing-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/t16_utf_identity_mixing_v0.yaml")
PANEL_PATH = Path("data/panels/t16_utf_identity_mixing_panel_v0.json")
FREEZE_PATH = Path("data/manifests/t16_utf_identity_mixing_v0.json")
VALIDATION_DIRECTORY = Path("validation/t16_utf_identity_mixing_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_DIRECTORY = VALIDATION_DIRECTORY / "tokenizers"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
MODEL_ROLES = ("gemma2_2b_it_bf16", "mistral7b_instruct_v03_bf16")
SYSTEM_IDS = ("atomic", "presentation", "modifier", "zwj", "regional", "keycap")
MIXTURES = ("clone_exact_utf", "within_system_mix", "cross_system_mix")
N_VALUES = (1, 2, 4, 8, 16)
ROTATIONS = (0, 1, 2, 3)
SITE_POSITIONS = (1, 3, 5, 7)
WRAPPER_IDS = (
    "w01_mark_anchor",
    "w04_token_state",
    "w10_sequence_continuation",
    "w15_observation_inference",
)
STATIC_ASSETS = (
    "configs/t16_utf_identity_mixing_v0.yaml",
    "data/panels/t16_utf_identity_mixing_panel_v0.json",
    "docs/T16_UTF_IDENTITY_MIXING_V0.md",
    "docs/T16_UTF_IDENTITY_MIXING_V0.ja.md",
    "scripts/t16_utf_identity_mixing_v0.py",
    "tests/test_t16_utf_identity_mixing_v0.py",
    "validation/t16_utf_identity_mixing_v0/design_preflight.json",
)
FROZEN_ASSETS = (
    *STATIC_ASSETS,
    "validation/t16_utf_identity_mixing_v0/tokenizers/gemma2_2b_it_bf16.json",
    "validation/t16_utf_identity_mixing_v0/tokenizers/mistral7b_instruct_v03_bf16.json",
    "validation/t16_utf_identity_mixing_v0/tokenizer_preflight.json",
)


class UTFMixingError(RuntimeError):
    """Raised when a T16-UTF design or execution gate fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise UTFMixingError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
            _require(isinstance(value, dict), f"Invalid JSONL row: {path}:{line_number}")
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
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


@cache
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-UTF config changed")
    return value


@cache
def _panel() -> dict[str, Any]:
    value = _read_json(_root() / PANEL_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-UTF panel changed")
    return value


@cache
def _systems() -> tuple[dict[str, Any], ...]:
    systems = tuple(_panel()["systems"])
    _require(tuple(str(row["id"]) for row in systems) == SYSTEM_IDS, "System order changed")
    return systems


@cache
def _wrappers() -> tuple[dict[str, str], ...]:
    binding = _config()["source_bindings"]["wrappers"]
    path = _root() / str(binding["path"])
    _require(path.is_file() and _sha256(path) == str(binding["sha256"]), "Wrapper file changed")
    by_id = {str(row["id"]): row for row in _read_jsonl(path)}
    _require(tuple(binding["selected_ids"]) == WRAPPER_IDS, "Wrapper selection changed")
    result = tuple({"id": wrapper_id, "template": str(by_id[wrapper_id]["template"])} for wrapper_id in WRAPPER_IDS)
    _require(all("{emoji}" in row["template"] for row in result), "Wrapper placeholder changed")
    return result


def _codepoints(text: str) -> list[str]:
    return [f"U+{ord(char):04X}" for char in text]


def _audit_panel_structure() -> None:
    _require(len(_systems()) == 6, "System count changed")
    all_glyphs: list[str] = []
    for system in _systems():
        items = system["items"]
        _require(len(items) == 4, f"Item count changed: {system['id']}")
        for item in items:
            glyph = str(item["glyph"])
            expected = [str(value) for value in item["codepoints"]]
            _require(_codepoints(glyph) == expected, f"Codepoint receipt changed: {system['id']}/{glyph}")
            all_glyphs.append(glyph)
            values = [ord(char) for char in glyph]
            if system["id"] == "atomic":
                _require(len(values) == 1, "Atomic rule changed")
            elif system["id"] == "presentation":
                _require(len(values) == 2 and values[1] == 0xFE0F, "Presentation rule changed")
            elif system["id"] == "modifier":
                _require(len(values) == 2 and values[1] == 0x1F3FD, "Modifier rule changed")
            elif system["id"] == "zwj":
                _require(len(values) == 3 and values[1] == 0x200D, "ZWJ rule changed")
            elif system["id"] == "regional":
                _require(len(values) == 2 and all(0x1F1E6 <= value <= 0x1F1FF for value in values), "Regional rule changed")
            else:
                _require(len(values) == 3 and values[1:] == [0xFE0F, 0x20E3], "Keycap rule changed")
    _require(len(set(all_glyphs)) == 24, "Panel glyphs are not unique")


def _sequence(system_index: int, rotation: int, n: int, mixture: str) -> str:
    systems = _systems()
    if mixture == "clone_exact_utf":
        values = [str(systems[system_index]["items"][rotation]["glyph"])] * n
    elif mixture == "within_system_mix":
        values = [str(systems[system_index]["items"][(rotation + index) % 4]["glyph"]) for index in range(n)]
    else:
        _require(mixture == "cross_system_mix", f"Unknown mixture: {mixture}")
        values = [str(systems[(system_index + index) % len(systems)]["items"][rotation]["glyph"]) for index in range(n)]
    return "".join(values)


@cache
def records() -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    prompt_to_index: dict[str, int] = {}
    for system_index, system in enumerate(_systems()):
        for rotation in ROTATIONS:
            anchor = str(system["items"][rotation]["glyph"])
            for n in N_VALUES:
                for mixture in MIXTURES:
                    sequence = _sequence(system_index, rotation, n, mixture)
                    _require(sequence.startswith(anchor), "First-item invariant changed")
                    for wrapper_index, wrapper in enumerate(_wrappers()):
                        prompt = wrapper["template"].format(emoji=sequence)
                        if prompt not in prompt_to_index:
                            prompt_to_index[prompt] = len(prompt_to_index)
                        rows.append(
                            {
                                "record_index": len(rows),
                                "system_id": str(system["id"]),
                                "system_index": system_index,
                                "rotation": rotation,
                                "n": n,
                                "mixture": mixture,
                                "wrapper_index": wrapper_index,
                                "wrapper_id": wrapper["id"],
                                "unique_prompt_index": prompt_to_index[prompt],
                                "sequence_sha256": hashlib.sha256(sequence.encode("utf-8")).hexdigest(),
                                "sequence_utf8_bytes": len(sequence.encode("utf-8")),
                                "sequence_unicode_scalars": len(sequence),
                                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                                "sequence": sequence,
                                "prompt": prompt,
                            }
                        )
    _require(len(rows) == 1440, "T16-UTF record count changed")
    _require(len(prompt_to_index) == 1248, "T16-UTF unique prompt count changed")
    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["n"] == 1:
            grouped[(str(row["system_id"]), int(row["rotation"]), str(row["wrapper_id"]))].append(row)
    _require(all(len({int(row["unique_prompt_index"]) for row in values}) == 1 for values in grouped.values()), "n=1 prompt collapse changed")
    return tuple(rows)


def _unique_prompts() -> list[str]:
    values: list[str | None] = [None] * 1248
    for row in records():
        index = int(row["unique_prompt_index"])
        if values[index] is None:
            values[index] = str(row["prompt"])
        else:
            _require(values[index] == row["prompt"], "Unique prompt mapping changed")
    _require(all(value is not None for value in values), "Unique prompt roster incomplete")
    return [str(value) for value in values]


def audit_design() -> dict[str, Any]:
    _audit_panel_structure()
    config = _config()
    _require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model order changed")
    _require(tuple(config["factorial"]["system_order"]) == SYSTEM_IDS, "Config system order changed")
    _require(tuple(config["factorial"]["n_values"]) == N_VALUES, "n roster changed")
    _require(tuple(config["factorial"]["rotations"]) == ROTATIONS, "Rotation roster changed")
    _require(tuple(config["factorial"]["mixture_conditions"]) == MIXTURES, "Mixture roster changed")
    _require(tuple(config["capture"]["site_indices_in_t13_eight_depth_roster"]) == SITE_POSITIONS, "Depth positions changed")
    _require(len(records()) == 1440 and len(_unique_prompts()) == 1248, "Factorial counts changed")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t16utf_model_forwards",
        "panel_sha256": _sha256(_root() / PANEL_PATH),
        "wrapper_sha256": _sha256(_root() / str(config["source_bindings"]["wrappers"]["path"])),
        "model_roles": list(MODEL_ROLES),
        "system_ids": list(SYSTEM_IDS),
        "n_values": list(N_VALUES),
        "mixtures": list(MIXTURES),
        "records_per_model": 1440,
        "unique_prompts_per_model": 1248,
        "depths_per_model": 4,
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
    _require(resolved.is_dir(), f"T16-UTF snapshot missing: {role}")
    _require(resolved.name == str(t10._model_spec(role)["revision"]), f"T16-UTF revision changed: {role}")
    return resolved


def _token_ids(tokenizer: Any, prompt: str) -> list[int]:
    return [int(value) for value in tokenizer(prompt, add_special_tokens=False, return_attention_mask=False)["input_ids"]]


def _matched_token_counts(counts: Sequence[int]) -> dict[str, int]:
    mapping = {int(row["record_index"]): int(counts[int(row["record_index"])]) for row in records()}
    lookup = {
        (str(row["system_id"]), int(row["rotation"]), int(row["n"]), str(row["wrapper_id"]), str(row["mixture"])): mapping[int(row["record_index"])]
        for row in records()
    }
    result: dict[str, int] = {}
    for mixture in ("within_system_mix", "cross_system_mix"):
        count = 0
        for system_id in SYSTEM_IDS:
            for rotation in ROTATIONS:
                for n in N_VALUES[1:]:
                    for wrapper_id in WRAPPER_IDS:
                        clone = lookup[(system_id, rotation, n, wrapper_id, "clone_exact_utf")]
                        mixed = lookup[(system_id, rotation, n, wrapper_id, mixture)]
                        count += int(clone == mixed)
        result[mixture] = count
    return result


def tokenizer_preflight(role: str, output: Path, model_path: Path | None) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoTokenizer

    audit_design()
    _require(role in MODEL_ROLES, f"Unknown T16-UTF role: {role}")
    snapshot = _locate_snapshot(role, model_path)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False, use_fast=True)
    prompts = _unique_prompts()
    unique_ids = [_token_ids(tokenizer, prompt) for prompt in prompts]
    record_counts = [len(unique_ids[int(row["unique_prompt_index"])]) for row in records()]
    final_tokens: dict[str, int] = {}
    for wrapper_id in WRAPPER_IDS:
        values = {
            unique_ids[int(row["unique_prompt_index"])][-1]
            for row in records()
            if row["wrapper_id"] == wrapper_id
        }
        _require(len(values) == 1, f"Final wrapper token changed: {role}/{wrapper_id}")
        final_tokens[wrapper_id] = next(iter(values))
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_preflight_pass_zero_t16utf_model_forwards",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "revision": t10._model_spec(role)["revision"],
        "artifact": model_artifact_receipt(snapshot),
        "tokenizer_class": type(tokenizer).__name__,
        "records": len(records()),
        "unique_prompts": len(prompts),
        "ordered_unique_prompt_sha256": _canonical_sha256(prompts),
        "ordered_unique_token_ids_sha256": _canonical_sha256(unique_ids),
        "record_token_counts": record_counts,
        "record_token_counts_sha256": _canonical_sha256(record_counts),
        "minimum_token_count": min(record_counts),
        "maximum_token_count": max(record_counts),
        "final_wrapper_token_ids": final_tokens,
        "exact_token_count_matched_pairs": _matched_token_counts(record_counts),
        "model_forwards": 0,
    }
    _write_json(output, value)
    return value


def aggregate_preflight(directory: Path, output: Path) -> dict[str, Any]:
    audit_design()
    roles: dict[str, Any] = {}
    for role in MODEL_ROLES:
        path = directory / f"{role}.json"
        value = _read_json(path)
        _require(value.get("status") == "tokenizer_preflight_pass_zero_t16utf_model_forwards", "Tokenizer preflight incomplete")
        _require(value.get("model_role") == role, "Tokenizer role changed")
        roles[role] = {
            "receipt_sha256": _sha256(path),
            "artifact_manifest_sha256": value["artifact"]["manifest_sha256"],
            "ordered_unique_token_ids_sha256": value["ordered_unique_token_ids_sha256"],
            "record_token_counts_sha256": value["record_token_counts_sha256"],
            "minimum_token_count": value["minimum_token_count"],
            "maximum_token_count": value["maximum_token_count"],
            "final_wrapper_token_ids": value["final_wrapper_token_ids"],
            "exact_token_count_matched_pairs": value["exact_token_count_matched_pairs"],
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "all_tokenizer_preflights_pass_zero_t16utf_model_forwards",
        "model_roles": list(MODEL_ROLES),
        "roles": roles,
        "model_forwards": 0,
    }
    _write_json(output, result)
    return result


def freeze(output: Path) -> dict[str, Any]:
    design = audit_design()
    _require((_root() / TOKENIZER_PREFLIGHT_PATH).is_file(), "T16-UTF tokenizer aggregate missing")
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T16-UTF frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t16utf_model_forwards",
        "assets": assets,
        "model_roles": list(MODEL_ROLES),
        "records_per_model": design["records_per_model"],
        "unique_prompts_per_model": design["unique_prompts_per_model"],
        "depths_per_model": design["depths_per_model"],
        "model_forwards_at_freeze": 0,
        "tokenizer_independent_unicode_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def audit_freeze() -> dict[str, Any]:
    design = audit_design()
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-UTF freeze protocol changed")
    _require(value.get("status") == "final_execution_freeze_zero_t16utf_model_forwards", "T16-UTF freeze incomplete")
    _require(int(value["records_per_model"]) == design["records_per_model"], "Frozen record count changed")
    for relative, expected in value["assets"].items():
        asset = _root() / relative
        _require(asset.is_file() and _sha256(asset) == expected, f"T16-UTF frozen asset changed: {relative}")
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path)}


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
    raise SystemExit(int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"]))


def _validate_runtime_tokenizer(role: str, tokenizer: Any, snapshot: Path) -> list[int]:
    from glyphprobe.provenance import model_artifact_receipt

    frozen = _read_json(_root() / TOKENIZER_DIRECTORY / f"{role}.json")
    artifact = model_artifact_receipt(snapshot)
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == frozen["artifact"][key], f"T16-UTF runtime artifact changed: {role}/{key}")
    ids = [_token_ids(tokenizer, prompt) for prompt in _unique_prompts()]
    _require(_canonical_sha256(ids) == frozen["ordered_unique_token_ids_sha256"], "T16-UTF runtime tokenization changed")
    counts = [len(ids[int(row["unique_prompt_index"])]) for row in records()]
    _require(_canonical_sha256(counts) == frozen["record_token_counts_sha256"], "T16-UTF token counts changed")
    return counts


def _tensor_from_output(output: Any) -> Any:
    if hasattr(output, "shape"):
        return output
    if isinstance(output, (tuple, list)) and output and hasattr(output[0], "shape"):
        return output[0]
    raise UTFMixingError(f"Cannot identify tensor in output {type(output)!r}")


def run_role(*, role: str, output_root: Path, model_preflight_directory: Path, model_path: Path | None) -> dict[str, Any]:
    audit_freeze()
    _require(role in MODEL_ROLES, f"Unknown T16-UTF role: {role}")
    final = output_root / role
    if final.is_dir():
        return validate_role(role, output_root)
    _yield_if_contended(output_root, role, "before_model_load")
    snapshot = _locate_snapshot(role, model_path)
    torch, tokenizer, model, model_receipt = t13._load_model(role, snapshot, model_preflight_directory)
    record_counts = _validate_runtime_tokenizer(role, tokenizer, snapshot)
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    block_indices = tuple(t13.layer_indices(role)[position] for position in SITE_POSITIONS)
    prompts = _unique_prompts()
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    captures: list[list[np.ndarray]] = [[] for _ in block_indices]
    started = time.perf_counter()
    batch_size = int(_config()["runtime"]["batch_size"])
    try:
        for start in range(0, len(prompts), batch_size):
            if start % 128 == 0:
                _yield_if_contended(output_root, role, f"before_unique_prompt_{start}")
            batch = prompts[start : start + batch_size]
            encoded = tokenizer(batch, add_special_tokens=False, padding=True, return_tensors="pt")
            device = next(model.parameters()).device
            input_ids = encoded["input_ids"].to(device)
            attention_mask = encoded["attention_mask"].to(device)
            captured: dict[int, Any] = {}
            handles = []
            for site_position, block_index in enumerate(block_indices):

                def hook(_module: Any, _inputs: Any, output: Any, *, site_position: int = site_position) -> Any:
                    raw = _tensor_from_output(output)
                    captured[site_position] = raw[:, -1, :].detach().float().cpu().numpy()
                    return output

                handles.append(blocks[block_index].register_forward_hook(hook))
            try:
                with torch.inference_mode():
                    model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, return_dict=True)
            finally:
                for handle in handles:
                    handle.remove()
            _require(set(captured) == set(range(4)), "T16-UTF capture incomplete")
            for site_position in range(4):
                captures[site_position].append(captured[site_position])
    finally:
        del model
        torch.cuda.empty_cache()
    hidden = np.stack([np.concatenate(values, axis=0) for values in captures], axis=1).astype(np.float32)
    width = int(t10._model_spec(role)["expected_model_dim"])
    _require(hidden.shape == (1248, 4, width), "T16-UTF hidden shape changed")
    _require(bool(np.isfinite(hidden).all()), "T16-UTF hidden array nonfinite")
    ledger = [
        {
            **{key: value for key, value in row.items() if key not in ("sequence", "prompt")},
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "model_role": role,
            "token_count": record_counts[int(row["record_index"])],
        }
        for row in records()
    ]
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not final.exists() and not stage.exists(), "T16-UTF output collision")
    stage.mkdir(parents=True)
    np.save(stage / "hidden_states.npy", hidden, allow_pickle=False)
    _write_jsonl(stage / "records.jsonl", ledger)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "utf_identity_mixing_role_complete",
        "model_role": role,
        "records": len(ledger),
        "unique_prompts": len(prompts),
        "block_indices": list(block_indices),
        "depth_fractions": list(_config()["capture"]["normalized_depth_fractions"]),
        "hidden_shape": list(hidden.shape),
        "hidden_states_sha256": _sha256(stage / "hidden_states.npy"),
        "records_sha256": _sha256(stage / "records.jsonl"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_receipt": model_receipt,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_role(role, output_root)


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    directory = output_root / role
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "T16-UTF receipt protocol changed")
    _require(receipt.get("status") == "utf_identity_mixing_role_complete", "T16-UTF role incomplete")
    _require(receipt.get("model_role") == role, "T16-UTF role changed")
    hidden_path = directory / "hidden_states.npy"
    ledger_path = directory / "records.jsonl"
    _require(_sha256(hidden_path) == receipt["hidden_states_sha256"], "T16-UTF hidden file changed")
    _require(_sha256(ledger_path) == receipt["records_sha256"], "T16-UTF ledger changed")
    hidden = np.load(hidden_path, mmap_mode="r", allow_pickle=False)
    width = int(t10._model_spec(role)["expected_model_dim"])
    _require(hidden.shape == (1248, 4, width), "T16-UTF validation shape changed")
    _require(bool(np.isfinite(hidden).all()), "T16-UTF validation nonfinite")
    rows = _read_jsonl(ledger_path)
    _require(len(rows) == 1440, "T16-UTF validation row count changed")
    return {
        "status": "pass",
        "model_role": role,
        "records": len(rows),
        "unique_prompts": int(receipt["unique_prompts"]),
        "receipt_sha256": _sha256(directory / "receipt.json"),
    }


def audit_run(output_root: Path) -> dict[str, Any]:
    audit_freeze()
    roles = [validate_role(role, output_root) for role in MODEL_ROLES]
    return {
        "status": "both_roles_complete_scientific_open_authorized",
        "roles_complete": len(roles),
        "records": sum(int(row["records"]) for row in roles),
        "unique_prompts": sum(int(row["unique_prompts"]) for row in roles),
        "generation_calls": 0,
    }


def _cosine_distance(first: np.ndarray, second: np.ndarray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    _require(denominator > 0 and math.isfinite(denominator), "T16-UTF cosine denominator invalid")
    value = 1.0 - float(np.dot(first, second) / denominator)
    return float(max(0.0, min(2.0, value)))


def _bootstrap(values: np.ndarray, systems: Sequence[str], seed: int) -> np.ndarray:
    _require(values.shape == (96,), "T16-UTF bootstrap vector changed")
    labels = np.asarray(systems, dtype=object)
    strata = [np.flatnonzero(labels == system) for system in SYSTEM_IDS]
    _require(all(len(indices) == 16 for indices in strata), "T16-UTF bootstrap strata changed")
    replicates = int(_config()["analysis"]["uncertainty"]["bootstrap_replicates"])
    rng = np.random.default_rng(seed)
    chunks: list[np.ndarray] = []
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        sampled = np.concatenate([indices[rng.integers(0, len(indices), size=(count, len(indices)))] for indices in strata], axis=1)
        chunks.append(np.median(values[sampled], axis=1))
    return np.concatenate(chunks)


def _record_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, int, int, str, str], Mapping[str, Any]]:
    result = {
        (str(row["system_id"]), int(row["rotation"]), int(row["n"]), str(row["wrapper_id"]), str(row["mixture"])): row
        for row in rows
    }
    _require(len(result) == 1440, "T16-UTF record lookup changed")
    return result


def analyze(output_root: Path, output: Path) -> dict[str, Any]:
    audit = audit_run(output_root)
    all_results: dict[str, Any] = {}
    seed = int(_config()["analysis"]["uncertainty"]["bootstrap_seed"])
    offset = 0
    for role in MODEL_ROLES:
        directory = output_root / role
        rows = _read_jsonl(directory / "records.jsonl")
        lookup = _record_lookup(rows)
        hidden = np.load(directory / "hidden_states.npy", mmap_mode="r", allow_pickle=False)
        role_result: dict[str, Any] = {}
        for site_position, depth in enumerate(_config()["capture"]["normalized_depth_fractions"]):
            units: list[dict[str, Any]] = []
            per_n: dict[int, dict[str, list[float]]] = {n: defaultdict(list) for n in N_VALUES}
            matched: dict[str, dict[int, list[float]]] = {
                "within_system_mix": defaultdict(list),
                "cross_system_mix": defaultdict(list),
            }
            for system_id in SYSTEM_IDS:
                for rotation in ROTATIONS:
                    for wrapper_id in WRAPPER_IDS:
                        base_row = lookup[(system_id, rotation, 1, wrapper_id, "clone_exact_utf")]
                        base_index = int(base_row["unique_prompt_index"])
                        n1_indices = {
                            int(lookup[(system_id, rotation, 1, wrapper_id, mixture)]["unique_prompt_index"])
                            for mixture in MIXTURES
                        }
                        _require(n1_indices == {base_index}, "T16-UTF n=1 hidden mapping changed")
                        base = np.asarray(hidden[base_index, site_position], dtype=np.float64)
                        endpoint_values: dict[str, list[float]] = {
                            "clone_growth": [],
                            "within_extra": [],
                            "cross_extra": [],
                            "cross_minus_within": [],
                        }
                        for n in N_VALUES:
                            clone_row = lookup[(system_id, rotation, n, wrapper_id, "clone_exact_utf")]
                            within_row = lookup[(system_id, rotation, n, wrapper_id, "within_system_mix")]
                            cross_row = lookup[(system_id, rotation, n, wrapper_id, "cross_system_mix")]
                            clone = np.asarray(hidden[int(clone_row["unique_prompt_index"]), site_position], dtype=np.float64)
                            within = np.asarray(hidden[int(within_row["unique_prompt_index"]), site_position], dtype=np.float64)
                            cross = np.asarray(hidden[int(cross_row["unique_prompt_index"]), site_position], dtype=np.float64)
                            clone_growth = _cosine_distance(clone, base)
                            within_extra = _cosine_distance(within, clone)
                            cross_extra = _cosine_distance(cross, clone)
                            cross_minus = cross_extra - within_extra
                            values = {
                                "clone_growth": clone_growth,
                                "within_extra": within_extra,
                                "cross_extra": cross_extra,
                                "cross_minus_within": cross_minus,
                            }
                            for name, value in values.items():
                                per_n[n][name].append(value)
                                if n > 1:
                                    endpoint_values[name].append(value)
                            if n > 1 and int(within_row["token_count"]) == int(clone_row["token_count"]):
                                matched["within_system_mix"][n].append(within_extra)
                            if n > 1 and int(cross_row["token_count"]) == int(clone_row["token_count"]):
                                matched["cross_system_mix"][n].append(cross_extra)
                        units.append(
                            {
                                "system_id": system_id,
                                "rotation": rotation,
                                "wrapper_id": wrapper_id,
                                **{name: float(np.mean(values)) for name, values in endpoint_values.items()},
                            }
                        )
            _require(len(units) == 96, "T16-UTF principal unit count changed")
            summaries: dict[str, Any] = {}
            system_labels = [str(row["system_id"]) for row in units]
            for name in ("clone_growth", "within_extra", "cross_extra", "cross_minus_within"):
                values = np.asarray([float(row[name]) for row in units])
                bootstrap = _bootstrap(values, system_labels, seed + offset)
                summaries[name] = {
                    "principal_unit_median": float(np.median(values)),
                    "bootstrap_95_percent_interval": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
                    "system_medians": {
                        system: float(np.median([row[name] for row in units if row["system_id"] == system]))
                        for system in SYSTEM_IDS
                    },
                }
                offset += 1
            n_values = {
                str(n): {name: float(np.median(values)) for name, values in per_n[n].items()}
                for n in N_VALUES
            }
            _require(all(abs(n_values["1"][name]) <= 1.0e-12 for name in ("clone_growth", "within_extra", "cross_extra", "cross_minus_within")), "T16-UTF n=1 geometry invariant failed")
            matched_summary = {
                mixture: {
                    str(n): {
                        "pairs": len(values),
                        "median_cosine_distance": float(np.median(values)) if values else None,
                    }
                    for n, values in by_n.items()
                }
                for mixture, by_n in matched.items()
            }
            role_result[f"depth_{float(depth):g}"] = {
                "block_index": int(_read_json(directory / "receipt.json")["block_indices"][site_position]),
                "primary_summaries": summaries,
                "per_n_medians": n_values,
                "exact_token_count_matched_subsets": matched_summary,
            }
        all_results[role] = role_result
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "utf_identity_mixing_analysis_complete",
        "audit": audit,
        "results": all_results,
        "decision_status": "exploratory_no_binary_scientific_gate",
        "claim_boundary": _config()["claim_boundary"],
        "tokenizer_independent_unicode_claim_authorized": False,
        "emoji_meaning_claim_authorized": False,
        "causal_circuit_claim_authorized": False,
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
    subparsers.add_parser("audit-freeze")
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
        result = audit_freeze()
    elif args.command == "run-role":
        result = run_role(role=args.role, output_root=args.output_root, model_preflight_directory=args.model_preflight_directory, model_path=args.model_path)
    elif args.command == "audit-run":
        result = audit_run(args.output_root)
    else:
        result = analyze(args.output_root, args.output)
    _print(result)


if __name__ == "__main__":
    main()
