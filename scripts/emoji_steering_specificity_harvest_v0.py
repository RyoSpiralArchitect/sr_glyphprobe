#!/usr/bin/env python3
"""Freeze and acquire the T13-EH exploratory GPU harvest.

The executable deliberately contains no scientific decision or outcome
selection routine.  It records a reusable source-direction bank, target
baselines, and fixed intervention-response tensors for later CPU/MPS analysis.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import glyph_system_decomposition_v0 as t11  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_steering_specificity_harvest_v0.yaml")
FREEZE_PATH = Path("data/manifests/emoji_steering_specificity_harvest_v0.json")
VALIDATION_DIRECTORY = Path("validation/emoji_steering_specificity_harvest_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
RUNTIME_AGGREGATE_NAME = "aggregate.json"
VIEW_ORDER = (
    "glyph",
    "unicode_name",
    "component_name",
    "codepoint_literal",
    "decomposed_form",
)
ITEM_VIEW_ORDER = ("glyph", "unicode_name", "decomposed_form")
STATIC_FROZEN_ASSETS = (
    "configs/emoji_steering_specificity_harvest_v0.yaml",
    "docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md",
    "docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md",
    "scripts/emoji_steering_specificity_harvest_v0.py",
    "scripts/run_emoji_steering_specificity_harvest_v0_queue.sh",
    "tests/test_emoji_steering_specificity_harvest_v0.py",
    "validation/emoji_steering_specificity_harvest_v0/design_preflight.json",
)


class HarvestError(RuntimeError):
    """Raised when the T13-EH acquisition contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HarvestError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T13-EH config protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    return atlas._sha256(path)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            _require(
                isinstance(value, dict),
                f"JSONL row is not an object: {path}:{line_number}",
            )
            rows.append(value)
    return rows


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
            )


def _runtime_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for package in ("glyphprobe", "torch", "transformers", "numpy", "PyYAML"):
        try:
            values[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            values[package] = None
    return values


def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


def pilot_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["pilot"]["roles"])


def population() -> list[dict[str, Any]]:
    config = _config()
    binding = config["source_bindings"]["t11_selection_manifest"]
    path = _root() / str(binding["path"])
    _require(path.is_file(), "T13-EH source population manifest missing")
    _require(
        _sha256(path) == str(binding["sha256"]), "T13-EH population binding changed"
    )
    value = atlas._read_json(path)
    rows = [
        dict(row) for row in value["items"] if bool(row["included_in_depth_subset"])
    ]
    rows.sort(key=lambda row: int(row["depth_index"]))
    expected = config["population"]
    _require(
        len(rows) == int(expected["expected_items"]), "T13-EH population count changed"
    )
    _require(
        [int(row["depth_index"]) for row in rows] == list(range(len(rows))),
        "T13-EH depth population order changed",
    )
    counts = Counter(str(row["glyph_system"]) for row in rows)
    _require(
        counts
        == Counter(
            {str(k): int(v) for k, v in expected["expected_system_counts"].items()}
        ),
        "T13-EH system quotas changed",
    )
    _require(
        sum(len(row["available_views"]) for row in rows)
        == int(expected["expected_present_item_views"]),
        "T13-EH present-view count changed",
    )
    _require(
        all(row["role"] != "reserve_unrun" for row in rows),
        "Unexposed reserve leaked into T13-EH",
    )
    return rows


def wrappers() -> list[dict[str, str]]:
    config = _config()
    binding = config["source_bindings"]["source_wrappers"]
    path = _root() / str(binding["path"])
    _require(path.is_file(), "T13-EH source wrapper file missing")
    _require(_sha256(path) == str(binding["sha256"]), "T13-EH wrapper binding changed")
    rows = _read_jsonl(path)
    by_id = {str(row["id"]): row for row in rows}
    selected = [by_id[str(value)] for value in binding["selected_ids"]]
    _require(
        len(rows) == int(binding["expected_rows"]),
        "T13-EH wrapper source count changed",
    )
    _require(len(selected) == 4, "T13-EH selected wrapper count changed")
    _require(
        all("{emoji}" in str(row["template"]) for row in selected),
        "Wrapper placeholder missing",
    )
    return [
        {
            "id": str(row["id"]),
            "text": str(row["template"]).replace("{emoji}", "").strip(),
        }
        for row in selected
    ]


def targets() -> list[dict[str, str]]:
    config = _config()
    binding = config["source_bindings"]["public_targets"]
    path = _root() / str(binding["path"])
    _require(path.is_file(), "T13-EH public target file missing")
    _require(_sha256(path) == str(binding["sha256"]), "T13-EH target binding changed")
    rows = _read_jsonl(path)
    _require(len(rows) == int(binding["expected_rows"]), "T13-EH target count changed")
    return [
        {"id": str(row["id"]), "group": str(row["group"]), "prompt": str(row["prompt"])}
        for row in rows
    ]


def available_views(item: Mapping[str, Any]) -> tuple[str, ...]:
    values = tuple(str(value) for value in item["available_views"])
    _require(all(view in VIEW_ORDER for view in values), "Unknown T13-EH source form")
    return tuple(view for view in VIEW_ORDER if view in values)


def source_text(item: Mapping[str, Any], view: str) -> str:
    if view == "glyph":
        value = item["glyph"]
    elif view == "unicode_name":
        value = item["name"]
    else:
        value = item.get(view)
    _require(isinstance(value, str) and bool(value), f"Missing source form: {view}")
    return value


def layer_indices(role: str) -> tuple[int, ...]:
    _require(role in model_roles(), f"Unknown T13-EH role: {role}")
    layers = int(t10._model_spec(role)["expected_num_layers"])
    fractions = [float(value) for value in _config()["depth"]["normalized_fractions"]]
    indices = tuple(max(0, int(math.floor(value * layers)) - 1) for value in fractions)
    _require(
        len(indices) == 8 and len(set(indices)) == 8,
        f"T13-EH depth sites collapsed: {role}",
    )
    _require(indices[-1] == layers - 1, f"T13-EH final block mapping changed: {role}")
    return indices


def audit_design() -> dict[str, Any]:
    config = _config()
    observed: dict[str, str] = {}
    for key in (
        "t11_selection_manifest",
        "public_targets",
        "source_wrappers",
        "t10_model_config",
        "t10_freeze_manifest",
    ):
        binding = config["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T13-EH bound source missing: {key}")
        actual = _sha256(path)
        _require(
            actual == str(binding["sha256"]), f"T13-EH bound source changed: {key}"
        )
        observed[path.relative_to(_root()).as_posix()] = actual
    rows = population()
    source_views = sum(len(available_views(row)) for row in rows)
    item_directions = sum(
        sum(view in available_views(row) for view in ITEM_VIEW_ORDER) for row in rows
    )
    prototype_count = sum(
        len(VIEW_ORDER) if system != "atomic_anchor" else 3
        for system in config["population"]["system_order"]
    )
    _require(source_views == 912, "T13-EH source view arithmetic changed")
    _require(item_directions == 552, "T13-EH item intervention arithmetic changed")
    _require(prototype_count == 28, "T13-EH prototype arithmetic changed")
    _require(
        set(model_roles()) == set(t10.model_roles()),
        "T13-EH model roster differs from T10",
    )
    _require(
        pilot_roles()
        == ("qwen25_0p5b_base_bf16", "llama32_3b_base_bf16", "qwen25_7b_base_bf16"),
        "Pilot roster changed",
    )
    for role in model_roles():
        layer_indices(role)
    expected_item = item_directions * len(targets()) * 2
    expected_prototype = prototype_count * 8 * 3 * 2 * len(targets())
    expected_random = 64 * 8 * 3 * len(targets())
    expected_zero = 8 * len(targets())
    _require(
        expected_item
        == int(config["pilot"]["item_grid"]["expected_response_rows_per_model"]),
        "Item-grid count changed",
    )
    _require(
        expected_prototype
        == int(config["pilot"]["prototype_grid"]["expected_response_rows_per_model"]),
        "Prototype-grid count changed",
    )
    _require(
        expected_random
        == int(config["pilot"]["random_grid"]["expected_response_rows_per_model"]),
        "Random-grid count changed",
    )
    _require(
        expected_zero
        == int(config["pilot"]["zero_grid"]["expected_response_rows_per_model"]),
        "Zero-grid count changed",
    )
    _require(
        expected_item + expected_prototype + expected_random + expected_zero
        == int(config["pilot"]["expected_response_rows_per_model"]),
        "Pilot total changed",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "population_items": len(rows),
        "present_item_views": source_views,
        "source_wrappers": len(wrappers()),
        "public_targets": len(targets()),
        "depth_sites_per_model": 8,
        "model_cells": len(model_roles()),
        "pilot_model_cells": len(pilot_roles()),
        "item_intervention_directions_per_model": item_directions,
        "system_view_prototypes_per_model": prototype_count,
        "pilot_response_rows_per_model": expected_item
        + expected_prototype
        + expected_random
        + expected_zero,
        "pilot_response_rows_total": (
            expected_item + expected_prototype + expected_random + expected_zero
        )
        * len(pilot_roles()),
        "protected_target_files_opened": 0,
        "model_weights_loaded": False,
        "model_forward_sequences": 0,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "source_bindings": observed,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    value = audit_design()
    _write_json(output, value)
    return value


def freeze(output: Path) -> dict[str, Any]:
    design = atlas._read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(design == audit_design(), "T13-EH design preflight is stale")
    assets: dict[str, str] = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T13-EH frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t13eh_model_forward",
        "experiment_role": _config()["experiment_role"],
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "model_order": list(model_roles()),
        "pilot_roles": list(pilot_roles()),
        "population_items": len(population()),
        "public_targets": len(targets()),
        "model_forward_sequences_at_freeze": 0,
        "intervention_sequences_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
        "protected_target_files_opened_at_freeze": 0,
    }
    _write_json(output, manifest)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    manifest = atlas._read_json(path)
    _require(
        manifest.get("protocol_id") == PROTOCOL_ID, "T13-EH freeze protocol mismatch"
    )
    _require(
        manifest.get("status") == "freeze_complete_before_any_t13eh_model_forward",
        "T13-EH freeze incomplete",
    )
    for relative, expected in manifest["frozen_assets"].items():
        candidate = _root() / str(relative)
        _require(candidate.is_file(), f"T13-EH frozen asset missing: {relative}")
        _require(
            _sha256(candidate) == str(expected),
            f"T13-EH frozen asset changed: {relative}",
        )
    _require(
        manifest["model_order"] == list(model_roles()),
        "T13-EH frozen model order changed",
    )
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(manifest["frozen_assets"]),
    }


def _token_ids(tokenizer: Any, text: str) -> list[int]:
    value = tokenizer(text, add_special_tokens=False, return_attention_mask=False)
    ids = value["input_ids"]
    _require(
        isinstance(ids, list) and ids and all(isinstance(v, int) for v in ids),
        "Tokenizer returned invalid IDs",
    )
    decoded = tokenizer.decode(
        ids, skip_special_tokens=False, clean_up_tokenization_spaces=False
    )
    _require(isinstance(decoded, str), "Tokenizer decode failed")
    return [int(value) for value in ids]


def tokenizer_receipt(role: str, model_path: Path) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoTokenizer

    _require(role in model_roles(), f"Unknown T13-EH role: {role}")
    spec = t10._model_spec(role)
    snapshot = model_path.resolve()
    _require(snapshot.is_dir(), f"T13-EH snapshot missing: {role}")
    _require(
        snapshot.name == str(spec["revision"]),
        f"T13-EH snapshot revision changed: {role}",
    )
    t10._validate_weight_artifact_completeness(snapshot)
    artifact = model_artifact_receipt(snapshot)
    upstream = atlas._read_json(
        _root() / Path(_config()["source_bindings"]["t10_freeze_manifest"]["path"])
    )
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(
            artifact[key] == upstream["model_artifacts"][role][key],
            f"T13-EH artifact changed: {role}/{key}",
        )
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    sequence_rows: list[list[int]] = []
    wrapper_rows = wrappers()
    bare_ids = {row["id"]: _token_ids(tokenizer, row["text"]) for row in wrapper_rows}
    sequence_rows.extend(bare_ids[row["id"]] for row in wrapper_rows)
    source_rows: list[dict[str, Any]] = []
    for item_index, item in enumerate(population()):
        for view in available_views(item):
            text = source_text(item, view)
            raw = _token_ids(tokenizer, text)
            sequence_rows.append(raw)
            added_counts: list[int] = []
            context_counts: list[int] = []
            for wrapper in wrapper_rows:
                context = _token_ids(tokenizer, f"{text}\n{wrapper['text']}")
                sequence_rows.append(context)
                context_counts.append(len(context))
                added_counts.append(len(context) - len(bare_ids[wrapper["id"]]))
            source_rows.append(
                {
                    "item_index": item_index,
                    "depth_index": int(item["depth_index"]),
                    "codepoint": str(item["codepoint"]),
                    "glyph_system": str(item["glyph_system"]),
                    "view": view,
                    "raw_token_count": len(raw),
                    "context_token_counts": context_counts,
                    "added_token_counts": added_counts,
                    "added_count_signature": ":".join(
                        str(value) for value in added_counts
                    ),
                }
            )
    target_rows: list[dict[str, Any]] = []
    for target in targets():
        ids = _token_ids(tokenizer, target["prompt"])
        sequence_rows.append(ids)
        target_rows.append(
            {"id": target["id"], "group": target["group"], "token_count": len(ids)}
        )
    signature_counts = Counter(row["added_count_signature"] for row in source_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_preflight_pass_zero_model_weight_load_zero_forward",
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "artifact": artifact,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": len(tokenizer),
        "ordered_sequence_sha256": _canonical_sha256(sequence_rows),
        "ordered_sequence_count": len(sequence_rows),
        "source_rows": source_rows,
        "target_rows": target_rows,
        "added_count_signature_strata": len(signature_counts),
        "source_rows_in_non_singleton_added_count_strata": sum(
            count for count in signature_counts.values() if count >= 2
        ),
        "model_weights_loaded": False,
        "model_forward_sequences": 0,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "protected_target_files_opened": 0,
    }


def preflight_role(role: str, output: Path, model_path: Path | None) -> dict[str, Any]:
    audit_freeze()
    snapshot = (
        model_path if model_path is not None else t11._locate_local_snapshot(role)
    )
    value = tokenizer_receipt(role, snapshot)
    _write_json(output, value)
    return {
        "status": "pass",
        "model_role": role,
        "receipt_sha256": _sha256(output),
        "source_rows": len(value["source_rows"]),
        "target_rows": len(value["target_rows"]),
    }


def aggregate_preflight(directory: Path, output: Path) -> dict[str, Any]:
    audit_freeze()
    receipts: dict[str, str] = {}
    artifacts: dict[str, Any] = {}
    for role in model_roles():
        path = directory / f"{role}.json"
        value = atlas._read_json(path)
        _require(
            value["protocol_id"] == PROTOCOL_ID and value["model_role"] == role,
            f"T13-EH preflight role mismatch: {role}",
        )
        _require(
            value["status"]
            == "tokenizer_preflight_pass_zero_model_weight_load_zero_forward",
            f"T13-EH preflight failed: {role}",
        )
        _require(
            len(value["source_rows"]) == 912 and len(value["target_rows"]) == 32,
            f"T13-EH preflight row count changed: {role}",
        )
        receipts[role] = _sha256(path)
        artifacts[role] = value["artifact"]
    versions = _runtime_versions()
    config = _config()
    for package, expected in config["runtime"]["critical_versions"].items():
        _require(
            versions.get(package) == str(expected),
            f"T13-EH runtime version changed: {package}",
        )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "runtime_and_tokenizer_preflight_pass_zero_model_forward",
        "model_order": list(model_roles()),
        "pilot_roles": list(pilot_roles()),
        "receipt_sha256": receipts,
        "model_artifacts": artifacts,
        "runtime_versions": versions,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_weights_loaded": False,
        "model_forward_sequences": 0,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "protected_target_files_opened": 0,
    }
    _write_json(output, value)
    return {
        "status": "pass",
        "aggregate_sha256": _sha256(output),
        "model_cells": len(receipts),
    }


def preflight_all(directory: Path) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    for role in model_roles():
        preflight_role(role, directory / f"{role}.json", None)
    return aggregate_preflight(directory, directory / RUNTIME_AGGREGATE_NAME)


def audit_preflight(directory: Path) -> dict[str, Any]:
    aggregate = atlas._read_json(directory / RUNTIME_AGGREGATE_NAME)
    _require(
        aggregate["protocol_id"] == PROTOCOL_ID, "T13-EH aggregate protocol mismatch"
    )
    _require(
        aggregate["status"]
        == "runtime_and_tokenizer_preflight_pass_zero_model_forward",
        "T13-EH aggregate preflight incomplete",
    )
    _require(
        aggregate["model_order"] == list(model_roles()),
        "T13-EH aggregate model order changed",
    )
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(path.is_file(), f"T13-EH role preflight missing: {role}")
        _require(
            _sha256(path) == aggregate["receipt_sha256"][role],
            f"T13-EH role preflight changed: {role}",
        )
    return {
        "status": "pass",
        "aggregate_sha256": _sha256(directory / RUNTIME_AGGREGATE_NAME),
        "model_cells": len(model_roles()),
    }


def _foreign_gpu_pids() -> list[int]:
    completed = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=pid",
            "--format=csv,noheader,nounits",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    _require(completed.returncode == 0, "nvidia-smi compute-process query failed")
    own = os.getpid()
    values: list[int] = []
    for line in completed.stdout.splitlines():
        try:
            pid = int(line.strip().split(",", 1)[0])
        except ValueError:
            continue
        if pid != own:
            values.append(pid)
    return sorted(set(values))


def _yield_if_contended(run_root: Path, role: str, boundary: str) -> None:
    pids = _foreign_gpu_pids()
    if not pids:
        return
    receipt = run_root / role / "yield_receipt.json"
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
        int(_config()["acquisition_policy"]["yield_exit_code_on_foreign_contention"])
    )


def _raw_tensor(value: Any) -> Any:
    return value[0] if isinstance(value, tuple) else value


def _capture_prompt_batch(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    sites: Sequence[int],
    prompts: Sequence[str],
    return_logits: bool,
) -> tuple[np.ndarray, np.ndarray | None, list[int]]:
    _require(bool(prompts), "T13-EH capture batch is empty")
    device = next(model.parameters()).device
    ids = [_token_ids(tokenizer, prompt) for prompt in prompts]
    lengths = [len(value) for value in ids]
    pad_id = tokenizer.pad_token_id
    if pad_id is None:
        pad_id = tokenizer.eos_token_id
    if pad_id is None:
        pad_id = 0
    width = max(lengths)
    input_ids = torch.full(
        (len(ids), width), int(pad_id), dtype=torch.long, device=device
    )
    attention_mask = torch.zeros((len(ids), width), dtype=torch.long, device=device)
    for row, values in enumerate(ids):
        input_ids[row, : len(values)] = torch.tensor(
            values, dtype=torch.long, device=device
        )
        attention_mask[row, : len(values)] = 1
    positions = torch.tensor(
        [value - 1 for value in lengths], dtype=torch.long, device=device
    )
    batch_rows = torch.arange(len(ids), dtype=torch.long, device=device)
    captures: dict[int, Any] = {}
    handles = []
    for site_index, block_index in enumerate(sites):

        def hook(
            _module: Any, _inputs: Any, output: Any, *, index: int = site_index
        ) -> None:
            raw = _raw_tensor(output)
            captures[index] = raw[batch_rows, positions].float().cpu().numpy()

        handles.append(blocks[int(block_index)].register_forward_hook(hook))
    try:
        with torch.inference_mode():
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                return_dict=True,
            )
        _require(len(captures) == len(sites), "T13-EH capture hook count changed")
        activations = np.stack([captures[index] for index in range(len(sites))], axis=1)
        logits = None
        if return_logits:
            logits = output.logits[batch_rows, positions].float().cpu().numpy()
    finally:
        for handle in handles:
            handle.remove()
    _require(
        bool(np.isfinite(activations).all()), "T13-EH activation capture is nonfinite"
    )
    if logits is not None:
        _require(
            bool(np.isfinite(logits).all()), "T13-EH baseline logits are nonfinite"
        )
    return activations.astype(np.float32, copy=False), logits, lengths


def _capture_prompts(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    sites: Sequence[int],
    prompts: Sequence[str],
    batch_size: int,
    return_logits: bool = False,
) -> tuple[np.ndarray, np.ndarray | None, list[int], int]:
    activation_parts: list[np.ndarray] = []
    logit_parts: list[np.ndarray] = []
    lengths: list[int] = []
    batch_calls = 0
    for start in range(0, len(prompts), batch_size):
        activations, logits, counts = _capture_prompt_batch(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            blocks=blocks,
            sites=sites,
            prompts=prompts[start : start + batch_size],
            return_logits=return_logits,
        )
        activation_parts.append(activations)
        if logits is not None:
            logit_parts.append(logits)
        lengths.extend(counts)
        batch_calls += 1
    all_activations = np.concatenate(activation_parts, axis=0)
    all_logits = np.concatenate(logit_parts, axis=0) if logit_parts else None
    return all_activations, all_logits, lengths, batch_calls


def _atomic_directory(final: Path) -> tuple[Path, Path]:
    _require(not final.exists(), f"T13-EH final output already exists: {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not stage.exists(), "T13-EH stage collision")
    stage.mkdir(parents=False)
    return stage, final


def _seal_directory(stage: Path, final: Path, receipt: Mapping[str, Any]) -> None:
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)


def _directory_file_bindings(
    directory: Path, names: Sequence[str]
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in names:
        path = directory / name
        _require(path.is_file(), f"T13-EH output missing before seal: {name}")
        result[name] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    return result


def _baseline_directory(run_root: Path, role: str) -> Path:
    return run_root / role / "baseline"


def _source_directory(run_root: Path, role: str, shard_index: int) -> Path:
    return run_root / role / "source" / f"shard-{shard_index:04d}"


def _response_directory(run_root: Path, role: str, kind: str, name: str) -> Path:
    return run_root / role / "pilot" / kind / name


def _run_baseline(
    *,
    role: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    sites: Sequence[int],
    run_root: Path,
) -> Path:
    final = _baseline_directory(run_root, role)
    if final.exists():
        validate_baseline(final, role)
        return final
    _yield_if_contended(run_root, role, "before_baseline")
    stage, final = _atomic_directory(final)
    started = time.perf_counter()
    wrapper_prompts = [row["text"] for row in wrappers()]
    wrapper_activations, _, wrapper_counts, wrapper_batches = _capture_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        prompts=wrapper_prompts,
        batch_size=len(wrapper_prompts),
    )
    target_activations, target_logits, target_counts, target_batches = _capture_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        prompts=[row["prompt"] for row in targets()],
        batch_size=1,
        return_logits=True,
    )
    _require(target_logits is not None, "T13-EH baseline logits missing")
    np.save(stage / "wrapper_activations.npy", wrapper_activations, allow_pickle=False)
    np.save(stage / "target_activations.npy", target_activations, allow_pickle=False)
    np.save(stage / "target_logits.npy", target_logits, allow_pickle=False)
    metadata = {
        "wrapper_ids": [row["id"] for row in wrappers()],
        "wrapper_token_counts": wrapper_counts,
        "target_ids": [row["id"] for row in targets()],
        "target_groups": [row["group"] for row in targets()],
        "target_token_counts": target_counts,
        "block_indices": list(sites),
        "depth_fractions": _config()["depth"]["normalized_fractions"],
    }
    _write_json(stage / "metadata.json", metadata)
    files = _directory_file_bindings(
        stage,
        (
            "wrapper_activations.npy",
            "target_activations.npy",
            "target_logits.npy",
            "metadata.json",
        ),
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "baseline_complete",
        "model_role": role,
        "unique_forward_sequences": len(wrapper_prompts) + len(targets()),
        "batched_model_invocations": wrapper_batches + target_batches,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    _seal_directory(stage, final, receipt)
    validate_baseline(final, role)
    return final


def validate_baseline(directory: Path, role: str) -> dict[str, Any]:
    receipt = atlas._read_json(directory / "receipt.json")
    _require(
        receipt["protocol_id"] == PROTOCOL_ID and receipt["model_role"] == role,
        "T13-EH baseline receipt mismatch",
    )
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and path.stat().st_size == int(binding["bytes"]),
            f"T13-EH baseline file changed: {name}",
        )
        _require(
            _sha256(path) == binding["sha256"], f"T13-EH baseline hash changed: {name}"
        )
    width = int(t10._model_spec(role)["expected_model_dim"])
    vocab = int(t10._model_spec(role)["expected_vocab_size"])
    wrapper = np.load(
        directory / "wrapper_activations.npy", mmap_mode="r", allow_pickle=False
    )
    target = np.load(
        directory / "target_activations.npy", mmap_mode="r", allow_pickle=False
    )
    logits = np.load(directory / "target_logits.npy", mmap_mode="r", allow_pickle=False)
    _require(wrapper.shape == (4, 8, width), "T13-EH wrapper baseline shape changed")
    _require(target.shape == (32, 8, width), "T13-EH target activation shape changed")
    _require(logits.shape == (32, vocab), "T13-EH target logit shape changed")
    _require(
        str(wrapper.dtype) == str(target.dtype) == str(logits.dtype) == "float32",
        "T13-EH baseline dtype changed",
    )
    _require(
        bool(
            np.isfinite(wrapper).all()
            and np.isfinite(target).all()
            and np.isfinite(logits).all()
        ),
        "T13-EH baseline contains nonfinite values",
    )
    return {"status": "pass", "model_role": role}


def _run_source_shard(
    *,
    role: str,
    shard_index: int,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    sites: Sequence[int],
    run_root: Path,
    baseline_directory: Path,
) -> Path:
    final = _source_directory(run_root, role, shard_index)
    if final.exists():
        validate_source_shard(final, role, shard_index)
        return final
    _yield_if_contended(run_root, role, f"before_source_shard_{shard_index:04d}")
    rows = population()
    shard_size = int(_config()["source_bank"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(rows), start + shard_size)
    _require(start < stop, f"T13-EH source shard out of range: {shard_index}")
    items = rows[start:stop]
    wrapper_rows = wrappers()
    prompts: list[str] = []
    records: list[tuple[int, int, int]] = []
    for local_index, item in enumerate(items):
        for view_index, view in enumerate(VIEW_ORDER):
            if view not in available_views(item):
                continue
            text = source_text(item, view)
            for wrapper_index, wrapper in enumerate(wrapper_rows):
                prompts.append(f"{text}\n{wrapper['text']}")
                records.append((local_index, view_index, wrapper_index))
    batch_size = int(_config()["models"]["batch_size"][role])
    started = time.perf_counter()
    captured, _, token_counts, batch_calls = _capture_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        prompts=prompts,
        batch_size=batch_size,
    )
    base = np.load(baseline_directory / "wrapper_activations.npy", allow_pickle=False)
    width = int(t10._model_spec(role)["expected_model_dim"])
    deltas = np.full(
        (len(items), len(VIEW_ORDER), 4, 8, width), np.nan, dtype=np.float32
    )
    view_mask = np.zeros((len(items), len(VIEW_ORDER)), dtype=np.bool_)
    for row_index, (local_index, view_index, wrapper_index) in enumerate(records):
        deltas[local_index, view_index, wrapper_index] = (
            captured[row_index] - base[wrapper_index]
        )
        view_mask[local_index, view_index] = True
    directions = np.full(
        (len(items), len(VIEW_ORDER), 8, width), np.nan, dtype=np.float32
    )
    for local_index in range(len(items)):
        for view_index in range(len(VIEW_ORDER)):
            if view_mask[local_index, view_index]:
                directions[local_index, view_index] = np.mean(
                    deltas[local_index, view_index], axis=0, dtype=np.float64
                ).astype(np.float32)
    _require(
        bool(np.isfinite(deltas[view_mask]).all()),
        "T13-EH present wrapper delta is nonfinite",
    )
    _require(
        bool(np.isnan(deltas[~view_mask]).all()),
        "T13-EH absent wrapper delta is not NaN",
    )
    _require(
        bool(np.isfinite(directions[view_mask]).all()),
        "T13-EH present direction is nonfinite",
    )
    stage, final = _atomic_directory(final)
    np.save(stage / "wrapper_deltas.npy", deltas, allow_pickle=False)
    np.save(stage / "directions.npy", directions, allow_pickle=False)
    np.save(stage / "view_mask.npy", view_mask, allow_pickle=False)
    metadata_rows = []
    cursor = 0
    for local_index, item in enumerate(items):
        for view in available_views(item):
            for wrapper_index, wrapper in enumerate(wrapper_rows):
                metadata_rows.append(
                    {
                        "global_item_index": start + local_index,
                        "depth_index": int(item["depth_index"]),
                        "codepoint": str(item["codepoint"]),
                        "glyph_system": str(item["glyph_system"]),
                        "view": view,
                        "wrapper_id": wrapper["id"],
                        "token_count": int(token_counts[cursor]),
                    }
                )
                cursor += 1
    _require(cursor == len(prompts), "T13-EH source metadata order changed")
    _write_jsonl(stage / "observations.jsonl", metadata_rows)
    files = _directory_file_bindings(
        stage,
        ("wrapper_deltas.npy", "directions.npy", "view_mask.npy", "observations.jsonl"),
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "source_shard_complete",
        "model_role": role,
        "shard_index": shard_index,
        "item_start": start,
        "item_stop_exclusive": stop,
        "present_item_views": int(view_mask.sum()),
        "unique_forward_sequences": len(prompts),
        "batched_model_invocations": batch_calls,
        "wrapper_delta_vectors": int(view_mask.sum()) * 4 * 8,
        "mean_direction_vectors": int(view_mask.sum()) * 8,
        "intervention_sequences": 0,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    _seal_directory(stage, final, receipt)
    validate_source_shard(final, role, shard_index)
    return final


def validate_source_shard(
    directory: Path, role: str, shard_index: int
) -> dict[str, Any]:
    receipt = atlas._read_json(directory / "receipt.json")
    _require(
        receipt["protocol_id"] == PROTOCOL_ID and receipt["model_role"] == role,
        "T13-EH source receipt mismatch",
    )
    _require(
        int(receipt["shard_index"]) == shard_index, "T13-EH source shard index changed"
    )
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and _sha256(path) == binding["sha256"],
            f"T13-EH source file changed: {name}",
        )
    width = int(t10._model_spec(role)["expected_model_dim"])
    count = int(receipt["item_stop_exclusive"]) - int(receipt["item_start"])
    delta = np.load(directory / "wrapper_deltas.npy", mmap_mode="r", allow_pickle=False)
    direction = np.load(directory / "directions.npy", mmap_mode="r", allow_pickle=False)
    mask = np.load(directory / "view_mask.npy", allow_pickle=False)
    _require(
        delta.shape == (count, 5, 4, 8, width), "T13-EH wrapper-delta shape changed"
    )
    _require(direction.shape == (count, 5, 8, width), "T13-EH direction shape changed")
    _require(mask.shape == (count, 5), "T13-EH view-mask shape changed")
    _require(
        str(delta.dtype) == str(direction.dtype) == "float32",
        "T13-EH source dtype changed",
    )
    _require(
        bool(np.isfinite(delta[mask]).all() and np.isfinite(direction[mask]).all()),
        "T13-EH source values are nonfinite",
    )
    _require(
        bool(np.isnan(delta[~mask]).all() and np.isnan(direction[~mask]).all()),
        "T13-EH absent source values are not NaN",
    )
    return {"status": "pass", "model_role": role, "shard_index": shard_index}


def _rms_rows(value: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(np.square(value, dtype=np.float64), axis=-1))


def _splitmix64_arrays(
    vocab_size: int, dimension: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    with np.errstate(over="ignore"):
        values = np.arange(vocab_size, dtype=np.uint64) + np.uint64(seed)
        values += np.uint64(0x9E3779B97F4A7C15)
        values = (values ^ (values >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        values = (values ^ (values >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        values ^= values >> np.uint64(31)
    buckets = (values % np.uint64(dimension)).astype(np.int64)
    signs = np.where((values >> np.uint64(63)) == 0, 1.0, -1.0).astype(np.float32)
    return buckets, signs


def _response_metrics(
    *,
    torch: Any,
    baseline: Any,
    intervened: Any,
    sketch_bucket: Any,
    sketch_sign: Any,
    top_k: int,
    sketch_dimension: int,
) -> dict[str, Any]:
    base = baseline.float()
    other = intervened.float()
    logp0 = torch.log_softmax(base, dim=-1)
    logp1 = torch.log_softmax(other, dim=-1)
    p0 = torch.exp(logp0)
    p1 = torch.exp(logp1)
    mean = 0.5 * (p0 + p1)
    log_mean = torch.log(torch.clamp(mean, min=1e-30))
    kl = torch.sum(p0 * (logp0 - logp1), dim=-1)
    js = 0.5 * torch.sum(p0 * (logp0 - log_mean), dim=-1) + 0.5 * torch.sum(
        p1 * (logp1 - log_mean), dim=-1
    )
    tv = 0.5 * torch.sum(torch.abs(p0 - p1), dim=-1)
    entropy0 = -torch.sum(p0 * logp0, dim=-1)
    entropy1 = -torch.sum(p1 * logp1, dim=-1)
    delta = other - base
    positive_values, positive_ids = torch.topk(delta, k=top_k, dim=-1)
    negative_abs, negative_ids = torch.topk(-delta, k=top_k, dim=-1)
    negative_values = -negative_abs
    sketch = torch.zeros(
        (delta.shape[0], sketch_dimension), dtype=torch.float32, device=delta.device
    )
    sketch.scatter_add_(
        1, sketch_bucket.expand(delta.shape[0], -1), delta * sketch_sign
    )
    return {
        "kl": kl.detach().cpu().numpy(),
        "js": js.detach().cpu().numpy(),
        "tv": tv.detach().cpu().numpy(),
        "entropy0": entropy0.detach().cpu().numpy(),
        "entropy1": entropy1.detach().cpu().numpy(),
        "delta_rms": torch.sqrt(torch.mean(delta * delta, dim=-1))
        .detach()
        .cpu()
        .numpy(),
        "baseline_argmax": torch.argmax(base, dim=-1).detach().cpu().numpy(),
        "intervened_argmax": torch.argmax(other, dim=-1).detach().cpu().numpy(),
        "positive_ids": positive_ids.detach().cpu().numpy().astype(np.int32),
        "positive_values": positive_values.detach().cpu().numpy().astype(np.float32),
        "negative_ids": negative_ids.detach().cpu().numpy().astype(np.int32),
        "negative_values": negative_values.detach().cpu().numpy().astype(np.float32),
        "sketch": sketch.detach().cpu().numpy().astype(np.float32),
    }


def _intervene_batch(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    block: Any,
    prompt: str,
    vectors: np.ndarray,
    sketch_bucket: Any,
    sketch_sign: Any,
) -> dict[str, Any]:
    _require(
        vectors.ndim == 2 and len(vectors) > 0, "T13-EH intervention batch is empty"
    )
    ids = _token_ids(tokenizer, prompt)
    all_vectors = np.concatenate(
        (np.zeros((1, vectors.shape[1]), dtype=np.float32), vectors), axis=0
    )
    device = next(model.parameters()).device
    vector_tensor = torch.tensor(all_vectors, dtype=torch.float32, device=device)
    input_ids = torch.tensor([ids], dtype=torch.long, device=device).repeat(
        len(all_vectors), 1
    )
    attention_mask = torch.ones_like(input_ids)

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        raw = _raw_tensor(output)
        changed = raw.clone()
        changed[:, -1, :] = changed[:, -1, :] + vector_tensor.to(dtype=changed.dtype)
        if isinstance(output, tuple):
            return (changed, *output[1:])
        return changed

    handle = block.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                return_dict=True,
            )
        logits = output.logits[:, -1, :]
    finally:
        handle.remove()
    baseline = logits[:1].expand(len(vectors), -1)
    return _response_metrics(
        torch=torch,
        baseline=baseline,
        intervened=logits[1:],
        sketch_bucket=sketch_bucket,
        sketch_sign=sketch_sign,
        top_k=int(
            _config()["pilot"]["response_storage"][
                "top_positive_and_negative_logit_deltas"
            ]
        ),
        sketch_dimension=int(
            _config()["pilot"]["response_storage"]["countsketch_dimension"]
        ),
    )


def _write_response_shard(
    *,
    final: Path,
    role: str,
    shard_kind: str,
    shard_name: str,
    rows: list[dict[str, Any]],
    positive_ids: list[np.ndarray],
    positive_values: list[np.ndarray],
    negative_ids: list[np.ndarray],
    negative_values: list[np.ndarray],
    sketches: list[np.ndarray],
    started: float,
    batched_invocations: int,
) -> None:
    stage, final = _atomic_directory(final)
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    arrays = {
        "top_positive_ids.npy": np.concatenate(positive_ids, axis=0),
        "top_positive_values.npy": np.concatenate(positive_values, axis=0),
        "top_negative_ids.npy": np.concatenate(negative_ids, axis=0),
        "top_negative_values.npy": np.concatenate(negative_values, axis=0),
        "countsketch.npy": np.concatenate(sketches, axis=0),
    }
    for name, value in arrays.items():
        _require(
            value.shape[0] == len(rows), f"T13-EH response array row mismatch: {name}"
        )
        _require(
            bool(np.isfinite(value).all()),
            f"T13-EH response array is nonfinite: {name}",
        )
        np.save(stage / name, value, allow_pickle=False)
    files = _directory_file_bindings(stage, ("response_ledger.jsonl", *arrays.keys()))
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "response_shard_complete",
        "model_role": role,
        "shard_kind": shard_kind,
        "shard_name": shard_name,
        "response_rows": len(rows),
        "intervention_sequences": len(rows),
        "baseline_guard_sequences": batched_invocations,
        "batched_model_invocations": batched_invocations,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "files": files,
    }
    _seal_directory(stage, final, receipt)


def validate_response_shard(
    directory: Path, role: str, expected_kind: str, expected_rows: int | None = None
) -> dict[str, Any]:
    receipt = atlas._read_json(directory / "receipt.json")
    _require(
        receipt["protocol_id"] == PROTOCOL_ID and receipt["model_role"] == role,
        "T13-EH response receipt mismatch",
    )
    _require(
        receipt["shard_kind"] == expected_kind, "T13-EH response shard kind changed"
    )
    rows = int(receipt["response_rows"])
    if expected_rows is not None:
        _require(rows == expected_rows, "T13-EH response row count changed")
    for name, binding in receipt["files"].items():
        path = directory / name
        _require(
            path.is_file() and _sha256(path) == binding["sha256"],
            f"T13-EH response file changed: {name}",
        )
    top_k = int(
        _config()["pilot"]["response_storage"]["top_positive_and_negative_logit_deltas"]
    )
    sketch_dim = int(_config()["pilot"]["response_storage"]["countsketch_dimension"])
    for name in (
        "top_positive_ids.npy",
        "top_positive_values.npy",
        "top_negative_ids.npy",
        "top_negative_values.npy",
    ):
        value = np.load(directory / name, mmap_mode="r", allow_pickle=False)
        _require(
            value.shape == (rows, top_k), f"T13-EH top-delta shape changed: {name}"
        )
        _require(
            bool(np.isfinite(value).all()),
            f"T13-EH top-delta values are nonfinite: {name}",
        )
    sketch = np.load(directory / "countsketch.npy", mmap_mode="r", allow_pickle=False)
    _require(sketch.shape == (rows, sketch_dim), "T13-EH CountSketch shape changed")
    _require(bool(np.isfinite(sketch).all()), "T13-EH CountSketch is nonfinite")
    with (directory / "response_ledger.jsonl").open("r", encoding="utf-8") as handle:
        ledger_rows = sum(1 for line in handle if line.strip())
    _require(ledger_rows == rows, "T13-EH response ledger count changed")
    return {"status": "pass", "model_role": role, "response_rows": rows}


def _append_batch_results(
    *,
    metadata: Sequence[Mapping[str, Any]],
    metrics: Mapping[str, Any],
    rows: list[dict[str, Any]],
    positive_ids: list[np.ndarray],
    positive_values: list[np.ndarray],
    negative_ids: list[np.ndarray],
    negative_values: list[np.ndarray],
    sketches: list[np.ndarray],
) -> None:
    count = len(metadata)
    _require(metrics["sketch"].shape[0] == count, "T13-EH metric batch count changed")
    offset = len(rows)
    for index, value in enumerate(metadata):
        row = dict(value)
        row.update(
            {
                "response_index": offset + index,
                "kl_baseline_to_intervened": float(metrics["kl"][index]),
                "js_divergence": float(metrics["js"][index]),
                "total_variation": float(metrics["tv"][index]),
                "baseline_entropy": float(metrics["entropy0"][index]),
                "intervened_entropy": float(metrics["entropy1"][index]),
                "logit_delta_rms": float(metrics["delta_rms"][index]),
                "baseline_argmax_id": int(metrics["baseline_argmax"][index]),
                "intervened_argmax_id": int(metrics["intervened_argmax"][index]),
                "argmax_flip": bool(
                    metrics["baseline_argmax"][index]
                    != metrics["intervened_argmax"][index]
                ),
            }
        )
        rows.append(row)
    positive_ids.append(metrics["positive_ids"])
    positive_values.append(metrics["positive_values"])
    negative_ids.append(metrics["negative_ids"])
    negative_values.append(metrics["negative_values"])
    sketches.append(metrics["sketch"])


def _run_condition_groups(
    *,
    role: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    groups: Sequence[tuple[int, int, list[dict[str, Any]], np.ndarray]],
) -> tuple[
    list[dict[str, Any]],
    list[np.ndarray],
    list[np.ndarray],
    list[np.ndarray],
    list[np.ndarray],
    list[np.ndarray],
    int,
]:
    batch_size = int(_config()["models"]["batch_size"][role])
    vocab = int(t10._model_spec(role)["expected_vocab_size"])
    sketch_dim = int(_config()["pilot"]["response_storage"]["countsketch_dimension"])
    sketch_seed = int(_config()["pilot"]["response_storage"]["countsketch_seed"])
    bucket_np, sign_np = _splitmix64_arrays(vocab, sketch_dim, sketch_seed)
    device = next(model.parameters()).device
    bucket = torch.tensor(bucket_np, dtype=torch.long, device=device).unsqueeze(0)
    sign = torch.tensor(sign_np, dtype=torch.float32, device=device).unsqueeze(0)
    target_rows = targets()
    rows: list[dict[str, Any]] = []
    positive_ids: list[np.ndarray] = []
    positive_values: list[np.ndarray] = []
    negative_ids: list[np.ndarray] = []
    negative_values: list[np.ndarray] = []
    sketches: list[np.ndarray] = []
    invocations = 0
    for site_index, target_index, metadata, vectors in groups:
        _require(
            len(metadata) == len(vectors), "T13-EH condition/vector count mismatch"
        )
        for start in range(0, len(metadata), batch_size):
            batch_meta = metadata[start : start + batch_size]
            batch_vectors = vectors[start : start + batch_size]
            metrics = _intervene_batch(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                block=blocks[int(layer_indices(role)[site_index])],
                prompt=target_rows[target_index]["prompt"],
                vectors=batch_vectors,
                sketch_bucket=bucket,
                sketch_sign=sign,
            )
            _append_batch_results(
                metadata=batch_meta,
                metrics=metrics,
                rows=rows,
                positive_ids=positive_ids,
                positive_values=positive_values,
                negative_ids=negative_ids,
                negative_values=negative_values,
                sketches=sketches,
            )
            invocations += 1
    return (
        rows,
        positive_ids,
        positive_values,
        negative_ids,
        negative_values,
        sketches,
        invocations,
    )


def _load_source_directions(run_root: Path, role: str) -> tuple[np.ndarray, np.ndarray]:
    directions: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    for shard_index in range(
        int(_config()["source_bank"]["expected_shards_per_model"])
    ):
        directory = _source_directory(run_root, role, shard_index)
        validate_source_shard(directory, role, shard_index)
        directions.append(np.load(directory / "directions.npy", allow_pickle=False))
        masks.append(np.load(directory / "view_mask.npy", allow_pickle=False))
    value = np.concatenate(directions, axis=0)
    mask = np.concatenate(masks, axis=0)
    _require(value.shape[:3] == (192, 5, 8), "T13-EH full direction bank shape changed")
    _require(mask.shape == (192, 5), "T13-EH full direction mask shape changed")
    return value, mask


def _target_rms(baseline_directory: Path) -> np.ndarray:
    values = np.load(baseline_directory / "target_activations.npy", allow_pickle=False)
    rms = _rms_rows(values)
    _require(
        rms.shape == (32, 8) and bool(np.isfinite(rms).all()) and bool((rms > 0).all()),
        "T13-EH target RMS changed",
    )
    return rms


def _scale_vectors(
    unit_vectors: np.ndarray, target_rms: float, signed_alpha: float
) -> np.ndarray:
    rms = _rms_rows(unit_vectors)
    _require(
        bool(np.isfinite(rms).all()) and bool((rms > 0).all()),
        "T13-EH direction RMS invalid",
    )
    return (
        unit_vectors / rms[:, None] * (float(target_rms) * float(signed_alpha))
    ).astype(np.float32)


def _run_item_response_shard(
    *,
    role: str,
    shard_index: int,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    run_root: Path,
    baseline_directory: Path,
    directions: np.ndarray,
    mask: np.ndarray,
) -> Path:
    final = _response_directory(run_root, role, "item", f"shard-{shard_index:04d}")
    if final.exists():
        validate_response_shard(final, role, "item")
        return final
    _yield_if_contended(run_root, role, f"before_item_response_{shard_index:04d}")
    shard_size = int(_config()["source_bank"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(192, start + shard_size)
    rows_pop = population()
    primary_fraction = float(_config()["depth"]["primary_item_intervention_fraction"])
    site_index = [
        float(value) for value in _config()["depth"]["normalized_fractions"]
    ].index(primary_fraction)
    target_rms = _target_rms(baseline_directory)
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        raw_vectors: list[np.ndarray] = []
        for item_index in range(start, stop):
            item = rows_pop[item_index]
            for view in ITEM_VIEW_ORDER:
                view_index = VIEW_ORDER.index(view)
                if not bool(mask[item_index, view_index]):
                    continue
                for sign in (-1, 1):
                    metadata.append(
                        {
                            "condition_kind": "item_source_form",
                            "item_index": item_index,
                            "depth_index": int(item["depth_index"]),
                            "codepoint": str(item["codepoint"]),
                            "glyph_system": str(item["glyph_system"]),
                            "view": view,
                            "site_index": site_index,
                            "block_index": int(layer_indices(role)[site_index]),
                            "depth_fraction": primary_fraction,
                            "magnitude": 0.25,
                            "sign": sign,
                            "target_index": target_index,
                            "target_id": target["id"],
                            "target_group": target["group"],
                        }
                    )
                    raw_vectors.append(directions[item_index, view_index, site_index])
        unit = np.stack(raw_vectors, axis=0)
        signs = np.asarray([row["sign"] for row in metadata], dtype=np.float32)
        scaled = _scale_vectors(unit, float(target_rms[target_index, site_index]), 0.25)
        scaled *= signs[:, None]
        groups.append((site_index, target_index, metadata, scaled))
    started = time.perf_counter()
    result = _run_condition_groups(
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
        shard_kind="item",
        shard_name=f"shard-{shard_index:04d}",
        rows=rows,
        positive_ids=pos_ids,
        positive_values=pos_values,
        negative_ids=neg_ids,
        negative_values=neg_values,
        sketches=sketches,
        started=started,
        batched_invocations=invocations,
    )
    validate_response_shard(final, role, "item")
    return final


def _prototype(
    directions: np.ndarray,
    mask: np.ndarray,
    item_indices: Sequence[int],
    view_index: int,
    site_index: int,
) -> np.ndarray:
    values = np.stack(
        [
            directions[index, view_index, site_index]
            for index in item_indices
            if bool(mask[index, view_index])
        ],
        axis=0,
    )
    _require(len(values) > 1, "T13-EH prototype source population too small")
    normalized = values / _rms_rows(values)[:, None]
    result = np.mean(normalized, axis=0, dtype=np.float64).astype(np.float32)
    _require(
        bool(np.isfinite(result).all()) and float(_rms_rows(result[None, :])[0]) > 0,
        "T13-EH prototype invalid",
    )
    return result


def _run_prototype_response_shard(
    *,
    role: str,
    system: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    run_root: Path,
    baseline_directory: Path,
    directions: np.ndarray,
    mask: np.ndarray,
) -> Path:
    final = _response_directory(run_root, role, "prototype", system)
    if final.exists():
        validate_response_shard(final, role, "prototype")
        return final
    _yield_if_contended(run_root, role, f"before_prototype_response_{system}")
    population_rows = population()
    indices = [
        index
        for index, item in enumerate(population_rows)
        if item["glyph_system"] == system
    ]
    available = [
        view
        for view in VIEW_ORDER
        if any(bool(mask[index, VIEW_ORDER.index(view)]) for index in indices)
    ]
    target_rms = _target_rms(baseline_directory)
    groups = []
    magnitudes = [
        float(value) for value in _config()["pilot"]["prototype_grid"]["magnitudes"]
    ]
    for site_index, fraction in enumerate(_config()["depth"]["normalized_fractions"]):
        prototypes = {
            view: _prototype(
                directions, mask, indices, VIEW_ORDER.index(view), site_index
            )
            for view in available
        }
        for target_index, target in enumerate(targets()):
            metadata: list[dict[str, Any]] = []
            raw_vectors: list[np.ndarray] = []
            signed_alphas: list[float] = []
            for view in available:
                for magnitude in magnitudes:
                    for sign in (-1, 1):
                        metadata.append(
                            {
                                "condition_kind": "glyph_system_source_form_prototype",
                                "glyph_system": system,
                                "view": view,
                                "prototype_source_items": sum(
                                    bool(mask[index, VIEW_ORDER.index(view)])
                                    for index in indices
                                ),
                                "site_index": site_index,
                                "block_index": int(layer_indices(role)[site_index]),
                                "depth_fraction": float(fraction),
                                "magnitude": magnitude,
                                "sign": sign,
                                "target_index": target_index,
                                "target_id": target["id"],
                                "target_group": target["group"],
                            }
                        )
                        raw_vectors.append(prototypes[view])
                        signed_alphas.append(sign * magnitude)
            unit = np.stack(raw_vectors, axis=0)
            scaled = unit / _rms_rows(unit)[:, None]
            scaled *= np.asarray(signed_alphas, dtype=np.float32)[:, None]
            scaled *= float(target_rms[target_index, site_index])
            groups.append(
                (site_index, target_index, metadata, scaled.astype(np.float32))
            )
    started = time.perf_counter()
    result = _run_condition_groups(
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
        shard_kind="prototype",
        shard_name=system,
        rows=rows,
        positive_ids=pos_ids,
        positive_values=pos_values,
        negative_ids=neg_ids,
        negative_values=neg_values,
        sketches=sketches,
        started=started,
        batched_invocations=invocations,
    )
    validate_response_shard(final, role, "prototype")
    return final


def _random_seed(role: str, site_index: int, seed_index: int) -> int:
    namespace = str(_config()["pilot"]["random_grid"]["seed_namespace"])
    digest = hashlib.sha256(
        f"{namespace}:{role}:{site_index}:{seed_index}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _run_random_response_shard(
    *,
    role: str,
    site_index: int,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    run_root: Path,
    baseline_directory: Path,
) -> Path:
    final = _response_directory(run_root, role, "random", f"site-{site_index:02d}")
    if final.exists():
        validate_response_shard(final, role, "random", 64 * 3 * 32)
        return final
    _yield_if_contended(run_root, role, f"before_random_response_{site_index:02d}")
    width = int(t10._model_spec(role)["expected_model_dim"])
    random_directions = []
    for seed_index in range(64):
        rng = np.random.default_rng(_random_seed(role, site_index, seed_index))
        random_directions.append(rng.standard_normal(width).astype(np.float32))
    random_array = np.stack(random_directions, axis=0)
    target_rms = _target_rms(baseline_directory)
    magnitudes = [
        float(value) for value in _config()["pilot"]["random_grid"]["magnitudes"]
    ]
    groups = []
    for target_index, target in enumerate(targets()):
        metadata: list[dict[str, Any]] = []
        raw_vectors: list[np.ndarray] = []
        alphas: list[float] = []
        for magnitude in magnitudes:
            for seed_index in range(64):
                metadata.append(
                    {
                        "condition_kind": "random_direction",
                        "seed_index": seed_index,
                        "seed": _random_seed(role, site_index, seed_index),
                        "site_index": site_index,
                        "block_index": int(layer_indices(role)[site_index]),
                        "depth_fraction": float(
                            _config()["depth"]["normalized_fractions"][site_index]
                        ),
                        "magnitude": magnitude,
                        "sign": 1,
                        "target_index": target_index,
                        "target_id": target["id"],
                        "target_group": target["group"],
                    }
                )
                raw_vectors.append(random_array[seed_index])
                alphas.append(magnitude)
        unit = np.stack(raw_vectors, axis=0)
        scaled = unit / _rms_rows(unit)[:, None]
        scaled *= np.asarray(alphas, dtype=np.float32)[:, None]
        scaled *= float(target_rms[target_index, site_index])
        groups.append((site_index, target_index, metadata, scaled.astype(np.float32)))
    started = time.perf_counter()
    result = _run_condition_groups(
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
        shard_kind="random",
        shard_name=f"site-{site_index:02d}",
        rows=rows,
        positive_ids=pos_ids,
        positive_values=pos_values,
        negative_ids=neg_ids,
        negative_values=neg_values,
        sketches=sketches,
        started=started,
        batched_invocations=invocations,
    )
    validate_response_shard(final, role, "random", 64 * 3 * 32)
    return final


def _run_zero_response_shard(
    *,
    role: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    run_root: Path,
) -> Path:
    final = _response_directory(run_root, role, "zero", "all-sites")
    if final.exists():
        validate_response_shard(final, role, "zero", 256)
        return final
    _yield_if_contended(run_root, role, "before_zero_response")
    width = int(t10._model_spec(role)["expected_model_dim"])
    groups = []
    for site_index, fraction in enumerate(_config()["depth"]["normalized_fractions"]):
        for target_index, target in enumerate(targets()):
            metadata = [
                {
                    "condition_kind": "zero_direction",
                    "site_index": site_index,
                    "block_index": int(layer_indices(role)[site_index]),
                    "depth_fraction": float(fraction),
                    "magnitude": 0.0,
                    "sign": 0,
                    "target_index": target_index,
                    "target_id": target["id"],
                    "target_group": target["group"],
                }
            ]
            groups.append(
                (
                    site_index,
                    target_index,
                    metadata,
                    np.zeros((1, width), dtype=np.float32),
                )
            )
    started = time.perf_counter()
    result = _run_condition_groups(
        role=role,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        groups=groups,
    )
    rows, pos_ids, pos_values, neg_ids, neg_values, sketches, invocations = result
    _require(
        all(row["kl_baseline_to_intervened"] == 0.0 for row in rows),
        "T13-EH zero-hook KL is nonzero",
    )
    _require(
        all(row["logit_delta_rms"] == 0.0 for row in rows),
        "T13-EH zero-hook logit delta is nonzero",
    )
    _write_response_shard(
        final=final,
        role=role,
        shard_kind="zero",
        shard_name="all-sites",
        rows=rows,
        positive_ids=pos_ids,
        positive_values=pos_values,
        negative_ids=neg_ids,
        negative_values=neg_values,
        sketches=sketches,
        started=started,
        batched_invocations=invocations,
    )
    validate_response_shard(final, role, "zero", 256)
    return final


def _validate_runtime_receipt(
    role: str, preflight_directory: Path, snapshot: Path
) -> None:
    aggregate = audit_preflight(preflight_directory)
    _require(aggregate["status"] == "pass", "T13-EH runtime preflight invalid")
    expected = atlas._read_json(preflight_directory / f"{role}.json")
    observed = tokenizer_receipt(role, snapshot)
    _require(
        observed["ordered_sequence_sha256"] == expected["ordered_sequence_sha256"],
        f"T13-EH runtime tokenization changed: {role}",
    )
    _require(
        observed["artifact"] == expected["artifact"],
        f"T13-EH runtime artifact changed: {role}",
    )


def _load_model(
    role: str,
    snapshot: Path,
    preflight_directory: Path,
) -> tuple[Any, Any, Any, dict[str, Any]]:
    import torch
    import transformers
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoModelForCausalLM, AutoTokenizer

    aggregate = audit_preflight(preflight_directory)
    _require(aggregate["status"] == "pass", "T13-EH runtime preflight invalid")
    versions = _runtime_versions()
    for package, expected in _config()["runtime"]["critical_versions"].items():
        _require(
            versions.get(package) == str(expected),
            f"T13-EH runtime version changed: {package}",
        )
    _require(torch.cuda.is_available(), "T13-EH CUDA is unavailable")
    _require(torch.cuda.is_bf16_supported(), "T13-EH CUDA BF16 is unavailable")
    _require(
        str(torch.cuda.get_device_name(0)) == str(_config()["runtime"]["hardware_pin"]),
        "T13-EH GPU identity changed",
    )
    spec = t10._model_spec(role)
    resolved = snapshot.resolve()
    _require(resolved.is_dir(), f"T13-EH model snapshot missing: {role}")
    _require(
        resolved.name == str(spec["revision"]),
        f"T13-EH model revision changed: {role}",
    )
    t10._validate_weight_artifact_completeness(resolved)
    expected = atlas._read_json(preflight_directory / f"{role}.json")
    artifact = model_artifact_receipt(resolved)
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(
            artifact[key] == expected["artifact"][key],
            f"T13-EH model artifact changed: {role}/{key}",
        )
    tokenizer = AutoTokenizer.from_pretrained(
        resolved, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    _validate_runtime_receipt(role, preflight_directory, resolved)
    dtype_key = (
        "dtype"
        if int(transformers.__version__.split(".", 1)[0]) >= 5
        else "torch_dtype"
    )
    model = AutoModelForCausalLM.from_pretrained(
        resolved,
        local_files_only=True,
        trust_remote_code=False,
        **{dtype_key: torch.bfloat16},
    )
    model.to("cuda")
    model.eval()
    _require(
        type(model).__name__ == str(spec["expected_model_class"]),
        f"T13-EH loaded model class changed: {role}",
    )
    _require(
        int(model.config.num_hidden_layers) == int(spec["expected_num_layers"]),
        f"T13-EH loaded layer count changed: {role}",
    )
    parameter_count = sum(int(parameter.numel()) for parameter in model.parameters())
    _require(
        parameter_count == int(spec["expected_parameter_count"]),
        f"T13-EH parameter count changed: {role}",
    )
    dtypes = Counter(str(parameter.dtype) for parameter in model.parameters())
    _require(
        set(dtypes) == {"torch.bfloat16"},
        f"T13-EH parameter dtype changed: {role}",
    )
    receipt = {
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "model_class": type(model).__name__,
        "parameter_count": parameter_count,
        "parameter_dtype_tensor_counts": dict(dtypes),
        "artifact": artifact,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "gpu": str(torch.cuda.get_device_name(0)),
        "runtime_preflight_aggregate_sha256": _sha256(
            preflight_directory / RUNTIME_AGGREGATE_NAME
        ),
        "tokenizer_receipt_sha256": _sha256(preflight_directory / f"{role}.json"),
    }
    return torch, tokenizer, model, receipt


def run_role(
    role: str,
    run_root: Path,
    preflight_directory: Path,
    t11_preflight_directory: Path,
    model_path: Path | None,
) -> dict[str, Any]:
    audit_freeze()
    audit_preflight(preflight_directory)
    _require(role in model_roles(), f"Unknown T13-EH role: {role}")
    summary_path = run_root / role / "summary.json"
    if summary_path.is_file():
        result = validate_role(role, run_root)
        result["pilot_role"] = role in pilot_roles()
        return result
    _yield_if_contended(run_root, role, "before_model_load")
    snapshot = (
        model_path if model_path is not None else t11._locate_local_snapshot(role)
    )
    del t11_preflight_directory
    torch, tokenizer, model, model_receipt = _load_model(
        role, snapshot, preflight_directory
    )
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    sites = layer_indices(role)
    started = time.perf_counter()
    baseline = _run_baseline(
        role=role,
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=blocks,
        sites=sites,
        run_root=run_root,
    )
    shard_count = int(_config()["source_bank"]["expected_shards_per_model"])
    for shard_index in range(shard_count):
        _run_source_shard(
            role=role,
            shard_index=shard_index,
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            blocks=blocks,
            sites=sites,
            run_root=run_root,
            baseline_directory=baseline,
        )
    response_rows = 0
    if role in pilot_roles():
        directions, mask = _load_source_directions(run_root, role)
        _run_zero_response_shard(
            role=role,
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            blocks=blocks,
            run_root=run_root,
        )
        response_rows += 256
        for shard_index in range(shard_count):
            directory = _run_item_response_shard(
                role=role,
                shard_index=shard_index,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                run_root=run_root,
                baseline_directory=baseline,
                directions=directions,
                mask=mask,
            )
            response_rows += int(
                atlas._read_json(directory / "receipt.json")["response_rows"]
            )
        for system in _config()["population"]["system_order"]:
            directory = _run_prototype_response_shard(
                role=role,
                system=str(system),
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                run_root=run_root,
                baseline_directory=baseline,
                directions=directions,
                mask=mask,
            )
            response_rows += int(
                atlas._read_json(directory / "receipt.json")["response_rows"]
            )
        for site_index in range(8):
            directory = _run_random_response_shard(
                role=role,
                site_index=site_index,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                run_root=run_root,
                baseline_directory=baseline,
            )
            response_rows += int(
                atlas._read_json(directory / "receipt.json")["response_rows"]
            )
        _require(
            response_rows
            == int(_config()["pilot"]["expected_response_rows_per_model"]),
            "T13-EH completed pilot row count changed",
        )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "pilot_role": role in pilot_roles(),
        "source_shards": shard_count,
        "population_items": len(population()),
        "present_item_views": 912,
        "source_forward_sequences": int(
            _config()["source_bank"]["expected_total_forward_sequences_per_model"]
        ),
        "intervention_response_rows": response_rows,
        "generation_calls": 0,
        "model_receipt": model_receipt,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "runtime_preflight_aggregate_sha256": _sha256(
            preflight_directory / RUNTIME_AGGREGATE_NAME
        ),
        "elapsed_seconds_this_process": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if summary_path.exists():
        existing = atlas._read_json(summary_path)
        _require(
            existing["status"] == "role_complete",
            "T13-EH existing role summary invalid",
        )
    else:
        _write_json(summary_path, summary)
    validate_role(role, run_root)
    del model
    torch.cuda.empty_cache()
    return {
        "status": "pass",
        "model_role": role,
        "pilot_role": role in pilot_roles(),
        "response_rows": response_rows,
    }


def validate_role(role: str, run_root: Path) -> dict[str, Any]:
    validate_baseline(_baseline_directory(run_root, role), role)
    source_sequences = 36
    wrapper_vectors = 0
    direction_vectors = 0
    for shard_index in range(
        int(_config()["source_bank"]["expected_shards_per_model"])
    ):
        directory = _source_directory(run_root, role, shard_index)
        validate_source_shard(directory, role, shard_index)
        receipt = atlas._read_json(directory / "receipt.json")
        source_sequences += int(receipt["unique_forward_sequences"])
        wrapper_vectors += int(receipt["wrapper_delta_vectors"])
        direction_vectors += int(receipt["mean_direction_vectors"])
    _require(
        source_sequences
        == int(_config()["source_bank"]["expected_total_forward_sequences_per_model"]),
        "T13-EH role source sequence count changed",
    )
    _require(
        wrapper_vectors
        == int(_config()["source_bank"]["expected_wrapper_delta_vectors_per_model"]),
        "T13-EH wrapper vector count changed",
    )
    _require(
        direction_vectors
        == int(_config()["source_bank"]["expected_mean_direction_vectors_per_model"]),
        "T13-EH mean direction count changed",
    )
    response_rows = 0
    if role in pilot_roles():
        response_rows += validate_response_shard(
            _response_directory(run_root, role, "zero", "all-sites"), role, "zero", 256
        )["response_rows"]
        for shard_index in range(12):
            response_rows += validate_response_shard(
                _response_directory(run_root, role, "item", f"shard-{shard_index:04d}"),
                role,
                "item",
            )["response_rows"]
        for system in _config()["population"]["system_order"]:
            response_rows += validate_response_shard(
                _response_directory(run_root, role, "prototype", str(system)),
                role,
                "prototype",
            )["response_rows"]
        for site_index in range(8):
            response_rows += validate_response_shard(
                _response_directory(run_root, role, "random", f"site-{site_index:02d}"),
                role,
                "random",
                64 * 3 * 32,
            )["response_rows"]
        _require(
            response_rows
            == int(_config()["pilot"]["expected_response_rows_per_model"]),
            "T13-EH role pilot count changed",
        )
    summary = atlas._read_json(run_root / role / "summary.json")
    _require(
        summary["protocol_id"] == PROTOCOL_ID and summary["model_role"] == role,
        "T13-EH role summary mismatch",
    )
    return {
        "status": "pass",
        "model_role": role,
        "source_forward_sequences": source_sequences,
        "response_rows": response_rows,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    design = sub.add_parser("design-preflight")
    design.add_argument("--output", type=Path, default=DESIGN_PREFLIGHT_PATH)
    frozen = sub.add_parser("freeze")
    frozen.add_argument("--output", type=Path, default=FREEZE_PATH)
    sub.add_parser("audit-freeze")
    one = sub.add_parser("preflight-role")
    one.add_argument("--role", required=True)
    one.add_argument("--output", type=Path, required=True)
    one.add_argument("--model-path", type=Path)
    all_roles = sub.add_parser("preflight-all")
    all_roles.add_argument("--output-dir", type=Path, required=True)
    aggregate = sub.add_parser("aggregate-preflight")
    aggregate.add_argument("--directory", type=Path, required=True)
    aggregate.add_argument("--output", type=Path, required=True)
    audit = sub.add_parser("audit-preflight")
    audit.add_argument("--directory", type=Path, required=True)
    run = sub.add_parser("run-role")
    run.add_argument("--role", required=True)
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--preflight-dir", type=Path, required=True)
    run.add_argument("--t11-preflight-dir", type=Path, required=True)
    run.add_argument("--model-path", type=Path)
    validate = sub.add_parser("validate-role")
    validate.add_argument("--role", required=True)
    validate.add_argument("--run-root", type=Path, required=True)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "design-preflight":
        value = write_design_preflight(_root() / args.output)
    elif args.command == "freeze":
        value = freeze(_root() / args.output)
    elif args.command == "audit-freeze":
        value = audit_freeze()
    elif args.command == "preflight-role":
        value = preflight_role(args.role, args.output, args.model_path)
    elif args.command == "preflight-all":
        value = preflight_all(args.output_dir)
    elif args.command == "aggregate-preflight":
        value = aggregate_preflight(args.directory, args.output)
    elif args.command == "audit-preflight":
        value = audit_preflight(args.directory)
    elif args.command == "run-role":
        value = run_role(
            args.role,
            args.run_root,
            args.preflight_dir,
            args.t11_preflight_dir,
            args.model_path,
        )
    else:
        value = validate_role(args.role, args.run_root)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
