#!/usr/bin/env python3
"""Freeze, acquire, resume, and validate the Mistral semantic atlas v0.

The runner performs no intervention or generation.  It fuses the four causal
carrier readouts into one forward per unique item/view/carrier sequence and
publishes independently verifiable item shards so furnace contention can stop
the run without losing completed work.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-mistral7b-semantic-atlas-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/mistral7b_semantic_atlas_v0.yaml")
SELECTION_PATH = Path("data/manifests/mistral7b_semantic_atlas_selection_v0.json")
PREFLIGHT_PATH = Path("validation/mistral7b_semantic_atlas_v0/engineering_preflight.json")
FREEZE_PATH = Path("data/manifests/mistral7b_semantic_atlas_v0.json")
FROZEN_ASSETS = (
    "configs/mistral7b_semantic_atlas_v0.yaml",
    "data/manifests/mistral7b_semantic_atlas_selection_v0.json",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_V0.md",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md",
    "scripts/mistral_semantic_candidate_census_v0.py",
    "scripts/mistral7b_semantic_atlas_v0.py",
    "tests/test_mistral7b_semantic_atlas_v0.py",
    "validation/mistral7b_semantic_atlas_v0/engineering_preflight.json",
)
VIEW_ORDER = ("glyph", "unicode_name", "codepoint_literal")
ROLE_ORDER = ("calibration_prior_exposed", "discovery_unseen", "reserved_unrun")


class AtlasError(RuntimeError):
    """Fail-closed protocol or artifact error."""


class ContentionDetected(AtlasError):
    """A foreign compute PID appeared at an item-shard boundary."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AtlasError(message)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path.name}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected YAML object: {path.name}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sequence_sha256(rows: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _role(codepoint: str, used_in_e1: bool, namespace: str) -> str:
    if used_in_e1:
        return "calibration_prior_exposed"
    digest = hashlib.sha256(f"{namespace}:{codepoint}".encode("ascii")).digest()
    return "reserved_unrun" if int.from_bytes(digest, "big") % 4 == 0 else "discovery_unseen"


def _view_text(item: Mapping[str, Any], view: str) -> str:
    if view == "glyph":
        return str(item["glyph"])
    if view == "unicode_name":
        return str(item["name"])
    if view == "codepoint_literal":
        return str(item["codepoint_literal"])
    raise AtlasError(f"Unknown view: {view}")


def _stored_view_ids(item: Mapping[str, Any], view: str) -> list[int]:
    key = {
        "glyph": "token_ids",
        "unicode_name": "name_token_ids",
        "codepoint_literal": "codepoint_token_ids",
    }[view]
    return [int(value) for value in item[key]]


def _selection_rows(selection: Mapping[str, Any], *, acquired_only: bool) -> list[dict[str, Any]]:
    rows = selection.get("candidates")
    _require(isinstance(rows, list), "Selection candidates are absent")
    typed = [dict(row) for row in rows]
    if acquired_only:
        typed = [row for row in typed if bool(row["included_in_acquisition"])]
        typed.sort(key=lambda row: int(row["acquisition_index"]))
    return typed


def build_selection(census_path: Path, output: Path) -> dict[str, Any]:
    census = _read_json(census_path)
    config = _read_yaml(_root() / CONFIG_PATH)
    spec = config["selection"]
    _require(census.get("status") == "tokenizer_only_zero_forward_census", "Census status mismatch")
    _require(census.get("model_forward_calls") == 0, "Census used a model forward")
    _require(census.get("model_weights_loaded") is False, "Census loaded model weights")
    _require(int(census["candidate_count"]) == int(spec["expected_total_candidates"]), "Census size mismatch")
    _require(census["source"]["unicode_emoji_version"] == "17.0", "Unicode version mismatch")
    _require(census["model"]["revision"] == config["model"]["revision"], "Tokenizer revision mismatch")
    namespace = str(spec["split_namespace"])
    rows: list[dict[str, Any]] = []
    acquisition_index = 0
    for source_index, original in enumerate(census["candidates"]):
        item = dict(original)
        role = _role(str(item["codepoint"]), bool(item["used_in_e1"]), namespace)
        included = role != str(spec["reserve_role"])
        item.update(
            {
                "source_index": source_index,
                "role": role,
                "included_in_acquisition": included,
                "acquisition_index": acquisition_index if included else None,
            }
        )
        if included:
            acquisition_index += 1
        rows.append(item)
    counts = Counter(str(row["role"]) for row in rows)
    expected = {
        "calibration_prior_exposed": int(spec["expected_calibration_prior_exposed"]),
        "discovery_unseen": int(spec["expected_discovery_unseen"]),
        "reserved_unrun": int(spec["expected_reserved_unrun"]),
    }
    _require(dict(counts) == expected, f"Prospective split counts changed: {dict(counts)}")
    _require(acquisition_index == int(config["storage"]["expected_acquired_items"]), "Acquisition size mismatch")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "prospective_selection_complete_zero_model_forwards",
        "source": census["source"],
        "tokenizer": census["model"],
        "source_census_sha256": _sha256(census_path),
        "split_namespace": namespace,
        "split_rule": spec["split_rule"],
        "role_order": list(ROLE_ORDER),
        "role_counts": expected,
        "candidate_count": len(rows),
        "acquired_item_count": acquisition_index,
        "reserved_item_count": expected["reserved_unrun"],
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "candidates": rows,
    }
    _write_json(output, payload)
    return {
        "status": "pass",
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "role_counts": expected,
    }


def _runtime_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for package in ("glyphprobe", "torch", "transformers", "numpy", "PyYAML"):
        try:
            values[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            values[package] = None
    return values


def build_preflight(selection_path: Path, model_path: Path, output: Path) -> dict[str, Any]:
    config = _read_yaml(_root() / CONFIG_PATH)
    selection = _read_json(selection_path)
    _require(selection.get("protocol_id") == PROTOCOL_ID, "Selection protocol mismatch")
    _require(selection.get("model_forward_calls") == 0, "Selection forward count changed")
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoConfig, AutoTokenizer
    import torch

    model_spec = config["model"]
    snapshot = model_path.resolve()
    _require(snapshot.is_dir(), "Model snapshot is absent")
    _require(snapshot.name == str(model_spec["revision"]), "Model revision directory mismatch")
    artifact = model_artifact_receipt(snapshot)
    for field, expected in (
        ("manifest_sha256", model_spec["expected_artifact_manifest_sha256"]),
        ("file_count", model_spec["expected_artifact_file_count"]),
        ("total_bytes", model_spec["expected_artifact_total_bytes"]),
    ):
        _require(artifact[field] == expected, f"Artifact {field} mismatch")
    architecture = AutoConfig.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    _require(architecture.model_type == model_spec["expected_model_type"], "Model type mismatch")
    _require(int(architecture.num_hidden_layers) == int(model_spec["expected_num_layers"]), "Layer count mismatch")
    _require(int(architecture.hidden_size) == int(model_spec["expected_model_dim"]), "Width mismatch")
    _require(int(architecture.vocab_size) == int(model_spec["expected_vocab_size"]), "Vocab mismatch")
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False, use_fast=True)
    _require(int(getattr(tokenizer, "vocab_size", len(tokenizer))) == int(model_spec["expected_tokenizer_vocab_size"]), "Tokenizer vocab mismatch")

    rows = _selection_rows(selection, acquired_only=False)
    acquired = [row for row in rows if bool(row["included_in_acquisition"])]
    raw_sequences: dict[str, list[list[int]]] = {view: [] for view in VIEW_ORDER}
    combined_sequences: dict[str, dict[str, list[list[int]]]] = {
        view: {carrier: [] for carrier in config["input"]["carrier_order"]}
        for view in VIEW_ORDER
    }
    token_count_histograms: dict[str, dict[str, int]] = {}
    combined_max_tokens = 0
    for view in VIEW_ORDER:
        for item in rows:
            observed = [int(value) for value in tokenizer.encode(_view_text(item, view), add_special_tokens=False)]
            _require(observed == _stored_view_ids(item, view), f"Stored tokenization changed: {item['codepoint']}/{view}")
            raw_sequences[view].append(observed)
        token_count_histograms[view] = {
            str(key): int(value)
            for key, value in sorted(Counter(len(row) for row in raw_sequences[view]).items())
        }
    carrier_receipts: dict[str, Any] = {}
    for carrier in config["input"]["carrier_order"]:
        carrier_spec = config["input"]["carriers"][carrier]
        unit = str(carrier_spec["unit"])
        repeats = int(carrier_spec["repeats"])
        unit_ids = [int(value) for value in tokenizer.encode(unit, add_special_tokens=False)]
        _require(unit_ids == [int(carrier_spec["expected_token_id"])], f"Carrier token changed: {carrier}")
        roundtrip = 0
        prefix_preserved = 0
        for view in VIEW_ORDER:
            for item in acquired:
                raw = _stored_view_ids(item, view)
                text = _view_text(item, view) + unit * repeats
                combined = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
                expected = raw + unit_ids * repeats
                _require(combined == expected, f"Carrier boundary changed: {item['codepoint']}/{view}/{carrier}")
                combined_sequences[view][carrier].append(combined)
                prefix_preserved += int(combined[: len(raw)] == raw)
                roundtrip += int(tokenizer.decode(combined, clean_up_tokenization_spaces=False, skip_special_tokens=False) == text)
                combined_max_tokens = max(combined_max_tokens, len(combined))
        expected_rows = len(acquired) * len(VIEW_ORDER)
        _require(prefix_preserved == expected_rows, f"Prefix preservation failed: {carrier}")
        _require(roundtrip == expected_rows, f"Roundtrip failed: {carrier}")
        carrier_receipts[carrier] = {
            "unit": unit,
            "token_id": unit_ids[0],
            "prefix_preserved_count": prefix_preserved,
            "roundtrip_exact_count": roundtrip,
        }
    ordered_hashes = {
        view: {
            "all_candidate_raw": _sequence_sha256(raw_sequences[view]),
            "acquired_combined": {
                carrier: _sequence_sha256(combined_sequences[view][carrier])
                for carrier in config["input"]["carrier_order"]
            },
        }
        for view in VIEW_ORDER
    }
    versions = _runtime_versions()
    for package, expected in config["runtime"]["critical_versions"].items():
        _require(versions.get(package) == str(expected), f"Runtime version mismatch: {package}")
    _require(torch.cuda.is_available(), "CUDA unavailable")
    _require(torch.cuda.is_bf16_supported(), "CUDA BF16 unavailable")
    _require(str(torch.cuda.get_device_name(0)) == str(config["runtime"]["hardware_pin"]), "GPU identity mismatch")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "static_preflight_pass_execution_gate_pending",
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "selection_manifest_sha256": _sha256(selection_path),
        "source": selection["source"],
        "candidate_counts": {
            "total": len(rows),
            "acquired": len(acquired),
            "reserved_unrun": len(rows) - len(acquired),
            "roles": selection["role_counts"],
        },
        "tokenizer": {
            "class": type(tokenizer).__name__,
            "vocab_size": int(getattr(tokenizer, "vocab_size", len(tokenizer))),
            "view_token_count_histograms": token_count_histograms,
            "ordered_sequence_hashes": ordered_hashes,
            "carriers": carrier_receipts,
            "maximum_combined_token_count": combined_max_tokens,
        },
        "model_artifact": artifact,
        "architecture": {
            "model_type": architecture.model_type,
            "num_hidden_layers": int(architecture.num_hidden_layers),
            "hidden_size": int(architecture.hidden_size),
            "vocab_size": int(architecture.vocab_size),
        },
        "furnace_static_environment": {
            "gpu": str(torch.cuda.get_device_name(0)),
            "gpu_memory_total_mib": int(torch.cuda.get_device_properties(0).total_memory // 2**20),
            "versions": versions,
            "cuda_available": True,
            "bfloat16_supported": True,
            "local_files_only": True,
        },
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "reserved_unrun_model_inputs_forwarded": 0,
        "scientific_result_available": False,
    }
    _write_json(output, payload)
    return {"status": "pass", "output": output.as_posix(), "sha256": _sha256(output)}


def build_freeze(output: Path) -> dict[str, Any]:
    root = _root()
    config = _read_yaml(root / CONFIG_PATH)
    selection = _read_json(root / SELECTION_PATH)
    preflight = _read_json(root / PREFLIGHT_PATH)
    _require(config.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    _require(selection.get("protocol_id") == PROTOCOL_ID, "Selection protocol mismatch")
    _require(preflight.get("protocol_id") == PROTOCOL_ID, "Preflight protocol mismatch")
    _require(preflight.get("model_forward_calls") == 0, "Preflight used model forwards")
    _require(preflight.get("model_weights_loaded") is False, "Preflight loaded weights")
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = root / relative
        _require(path.is_file(), f"Missing frozen asset: {relative}")
        assets[relative] = _sha256(path)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t8_model_forward",
        "frozen_assets": assets,
        "selection_manifest_sha256": _sha256(root / SELECTION_PATH),
        "engineering_preflight_sha256": _sha256(root / PREFLIGHT_PATH),
        "model_artifact": preflight["model_artifact"],
        "candidate_counts": preflight["candidate_counts"],
        "model_forward_calls_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "reserved_unrun_model_inputs_forwarded_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
    }
    _write_json(output, payload)
    return {"status": "pass", "manifest_sha256": _sha256(output), "frozen_asset_count": len(assets)}


def audit_freeze() -> dict[str, Any]:
    root = _root()
    manifest = _read_json(root / FREEZE_PATH)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch")
    _require(manifest.get("status") == "freeze_complete_before_any_t8_model_forward", "Freeze incomplete")
    for relative, expected in manifest["frozen_assets"].items():
        path = root / relative
        _require(path.is_file(), f"Frozen asset missing: {relative}")
        _require(_sha256(path) == expected, f"Frozen asset changed: {relative}")
    _require(_sha256(root / SELECTION_PATH) == manifest["selection_manifest_sha256"], "Selection hash mismatch")
    _require(_sha256(root / PREFLIGHT_PATH) == manifest["engineering_preflight_sha256"], "Preflight hash mismatch")
    return {"status": "pass", "manifest_sha256": _sha256(root / FREEZE_PATH), "frozen_asset_count": len(manifest["frozen_assets"])}


def _foreign_gpu_pids() -> list[int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    )
    own = os.getpid()
    values: list[int] = []
    for line in result.stdout.splitlines():
        text = line.strip()
        if text and text.isdigit() and int(text) != own:
            values.append(int(text))
    return sorted(set(values))


def _resolve_layers(num_layers: int, fractions: Sequence[float]) -> list[int]:
    return [min(num_layers - 1, math.floor(float(value) * num_layers)) for value in fractions]


def _atomic_shard_directory(root: Path, shard_index: int) -> tuple[Path, Path]:
    final = root / f"shard_{shard_index:04d}"
    stage = root / f".shard_{shard_index:04d}.partial-{uuid.uuid4().hex}"
    _require(not final.exists(), f"Shard already exists: {final.name}")
    stage.mkdir(parents=True)
    return stage, final


def _write_ledger(directory: Path, names: Sequence[str]) -> None:
    lines = [f"{_sha256(directory / name)}  {name}" for name in names]
    (directory / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_runtime(config: Mapping[str, Any]) -> dict[str, Any]:
    versions = _runtime_versions()
    for package, expected in config["runtime"]["critical_versions"].items():
        _require(versions.get(package) == str(expected), f"Runtime version mismatch: {package}")
    return versions


def _load_model(model_path: Path, config: Mapping[str, Any]) -> tuple[Any, Any, Any, dict[str, Any]]:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from glyphprobe.provenance import model_artifact_receipt

    _require(torch.cuda.is_available(), "CUDA unavailable")
    _require(torch.cuda.is_bf16_supported(), "CUDA BF16 unavailable")
    _require(str(torch.cuda.get_device_name(0)) == str(config["runtime"]["hardware_pin"]), "GPU identity mismatch")
    artifact = model_artifact_receipt(model_path)
    model_spec = config["model"]
    _require(artifact["manifest_sha256"] == model_spec["expected_artifact_manifest_sha256"], "Artifact manifest mismatch")
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False, use_fast=True)
    dtype_key = "dtype" if int(transformers.__version__.split(".", 1)[0]) >= 5 else "torch_dtype"
    kwargs = {"local_files_only": True, "trust_remote_code": False, dtype_key: torch.bfloat16}
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.to("cuda")
    model.eval()
    _require(type(model).__name__ == model_spec["expected_model_class"], "Model class mismatch")
    _require(int(model.config.num_hidden_layers) == int(model_spec["expected_num_layers"]), "Layer count mismatch")
    parameter_count = sum(int(parameter.numel()) for parameter in model.parameters())
    _require(parameter_count == int(model_spec["expected_parameter_count"]), "Parameter count mismatch")
    dtype_elements = Counter(str(parameter.dtype) for parameter in model.parameters() for _ in (0,))
    _require(set(dtype_elements) == {"torch.bfloat16"}, "Loaded parameter dtype mismatch")
    receipt = {
        "model_class": type(model).__name__,
        "parameter_count": parameter_count,
        "parameter_dtype_tensor_counts": dict(dtype_elements),
        "artifact": artifact,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "gpu": str(torch.cuda.get_device_name(0)),
    }
    return torch, tokenizer, model, receipt


def _record_rows(items: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    for item_offset, item in enumerate(items):
        for view_index, view in enumerate(VIEW_ORDER):
            raw_ids = _stored_view_ids(item, view)
            for carrier_index, carrier in enumerate(carriers):
                carrier_spec = config["input"]["carriers"][carrier]
                carrier_id = int(carrier_spec["expected_token_id"])
                rows.append(
                    {
                        "item_offset": item_offset,
                        "view_index": view_index,
                        "view": view,
                        "carrier_index": carrier_index,
                        "carrier": carrier,
                        "raw_ids": raw_ids,
                        "input_ids": raw_ids + [carrier_id] * int(carrier_spec["repeats"]),
                    }
                )
    return rows


def _run_one_shard(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
    config: Mapping[str, Any],
    selection: Mapping[str, Any],
    freeze: Mapping[str, Any],
    run_root: Path,
    shard_index: int,
) -> dict[str, Any]:
    acquired = _selection_rows(selection, acquired_only=True)
    shard_size = int(config["storage"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(acquired), start + shard_size)
    _require(start < stop, f"Shard index out of range: {shard_index}")
    items = acquired[start:stop]
    layers = [int(value) for value in config["layers"]["expected_resolved_layers"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    width = int(config["model"]["expected_model_dim"])
    activations = np.empty(
        (len(items), len(VIEW_ORDER), len(carriers), len(distances), len(layers), width),
        dtype=np.float32,
    )
    records = _record_rows(items, config)
    batch_size = int(config["storage"]["batch_size_unique_sequences"])
    pad_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 0
    observations: list[dict[str, Any]] = []
    forward_batches = 0
    started = time.perf_counter()
    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]
        max_tokens = max(len(row["input_ids"]) for row in batch)
        input_ids = torch.full((len(batch), max_tokens), int(pad_id), dtype=torch.long, device="cuda")
        attention_mask = torch.zeros((len(batch), max_tokens), dtype=torch.long, device="cuda")
        positions: list[list[int]] = []
        for index, row in enumerate(batch):
            ids = row["input_ids"]
            input_ids[index, : len(ids)] = torch.tensor(ids, dtype=torch.long, device="cuda")
            attention_mask[index, : len(ids)] = 1
            positions.append([len(row["raw_ids"]) + distance - 1 for distance in distances])
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
        elapsed_ms = (time.perf_counter() - before) * 1000.0
        _require(len(output.hidden_states) == int(config["model"]["expected_num_layers"]) + 1, "Hidden-state roster mismatch")
        selected = torch.stack([output.hidden_states[layer + 1] for layer in layers], dim=2)
        position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
        batch_tensor = torch.arange(len(batch), device="cuda")[:, None]
        captured = selected[batch_tensor, position_tensor].float().cpu().numpy()
        _require(captured.shape == (len(batch), len(distances), len(layers), width), "Captured batch shape mismatch")
        _require(bool(np.isfinite(captured).all()), "Nonfinite activation")
        for index, row in enumerate(batch):
            item = items[int(row["item_offset"])]
            values = captured[index]
            activations[int(row["item_offset"]), int(row["view_index"]), int(row["carrier_index"])] = values
            observations.append(
                {
                    "acquisition_index": int(item["acquisition_index"]),
                    "source_index": int(item["source_index"]),
                    "codepoint": str(item["codepoint"]),
                    "glyph": str(item["glyph"]),
                    "name": str(item["name"]),
                    "group": str(item["group"]),
                    "subgroup": str(item["subgroup"]),
                    "role": str(item["role"]),
                    "view": str(row["view"]),
                    "view_index": int(row["view_index"]),
                    "carrier": str(row["carrier"]),
                    "carrier_index": int(row["carrier_index"]),
                    "raw_token_ids": [int(value) for value in row["raw_ids"]],
                    "input_token_ids": [int(value) for value in row["input_ids"]],
                    "readout_positions": positions[index],
                    "activation_rms_by_distance_layer": np.sqrt(
                        np.mean(np.square(values, dtype=np.float64), axis=-1)
                    ).tolist(),
                    "batch_forward_latency_ms": elapsed_ms,
                }
            )
        forward_batches += 1
        del output, selected, captured, input_ids, attention_mask, position_tensor, batch_tensor
    _require(bool(np.isfinite(activations).all()), "Shard contains nonfinite activations")
    stage, final = _atomic_shard_directory(run_root, shard_index)
    try:
        np.save(stage / "activations.npy", activations, allow_pickle=False)
        _write_jsonl(stage / "observations.jsonl", observations)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "shard_index": shard_index,
            "acquisition_index_start": start,
            "acquisition_index_stop_exclusive": stop,
            "item_count": len(items),
            "item_codepoints": [str(item["codepoint"]) for item in items],
            "role_counts": dict(Counter(str(item["role"]) for item in items)),
            "activation_shape": list(activations.shape),
            "activation_dtype": str(activations.dtype),
            "axis_order": config["storage"]["activation_axis_order"],
            "view_order": list(VIEW_ORDER),
            "carrier_order": carriers,
            "distance_order": distances,
            "layers": layers,
            "unique_input_sequences": len(records),
            "causal_readout_vectors": int(np.prod(activations.shape[:-1])),
            "batched_model_forward_calls": forward_batches,
            "fused_distance_readout": True,
            "elapsed_ms": (time.perf_counter() - started) * 1000.0,
            "model": model_receipt,
            "freeze_manifest_sha256": freeze["manifest_sha256"],
            "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
            "outputs": {
                "activations.npy": _sha256(stage / "activations.npy"),
                "observations.jsonl": _sha256(stage / "observations.jsonl"),
            },
            "intervention_calls": 0,
            "generation_calls": 0,
            "reserved_unrun_model_inputs_forwarded": 0,
            "scientific_decision_authorized": False,
        }
        _write_json(stage / "shard_receipt.json", receipt)
        _write_ledger(stage, ("activations.npy", "observations.jsonl", "shard_receipt.json"))
        stage.rename(final)
        return receipt
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def run_shards(model_path: Path, run_root: Path, shard_start: int, shard_stop: int | None) -> dict[str, Any]:
    freeze = audit_freeze()
    config = _read_yaml(_root() / CONFIG_PATH)
    selection = _read_json(_root() / SELECTION_PATH)
    preflight = _read_json(_root() / PREFLIGHT_PATH)
    _require(_sha256(_root() / SELECTION_PATH) == preflight["selection_manifest_sha256"], "Preflight selection binding mismatch")
    _validate_runtime(config)
    expected_shards = int(config["storage"]["expected_shards"])
    stop = expected_shards if shard_stop is None else shard_stop
    _require(0 <= shard_start < stop <= expected_shards, "Invalid shard range")
    run_root.mkdir(parents=True, exist_ok=True)
    lock = run_root / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise AtlasError("Run root already has an active writer lock") from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    os.close(descriptor)
    session_rows: list[dict[str, Any]] = []
    model = None
    try:
        pending = [index for index in range(shard_start, stop) if not (run_root / f"shard_{index:04d}").exists()]
        for index in range(shard_start, stop):
            existing = run_root / f"shard_{index:04d}"
            if existing.exists():
                validate_shard(existing, config=config)
        if not pending:
            return {"status": "pass", "message": "requested shards already complete", "completed": []}
        foreign = _foreign_gpu_pids()
        if foreign:
            raise ContentionDetected(f"Foreign GPU compute PIDs before model load: {foreign}")
        torch, tokenizer, model, model_receipt = _load_model(model_path, config)
        for shard_index in pending:
            foreign = _foreign_gpu_pids()
            if foreign:
                raise ContentionDetected(f"Foreign GPU compute PIDs before shard {shard_index}: {foreign}")
            receipt = _run_one_shard(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                model_receipt=model_receipt,
                config=config,
                selection=selection,
                freeze=freeze,
                run_root=run_root,
                shard_index=shard_index,
            )
            session_rows.append(
                {
                    "shard_index": shard_index,
                    "item_count": receipt["item_count"],
                    "elapsed_ms": receipt["elapsed_ms"],
                }
            )
        status = "pass"
    except ContentionDetected as exc:
        status = "yielded_on_contention"
        session_rows.append({"contention": str(exc)})
    finally:
        if model is not None:
            del model
            import torch

            torch.cuda.empty_cache()
        lock.unlink(missing_ok=True)
        session_path = run_root / f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}.json"
        _write_json(
            session_path,
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "status": locals().get("status", "fail"),
                "requested_shard_start": shard_start,
                "requested_shard_stop_exclusive": stop,
                "events": session_rows,
            },
        )
    return {"status": status, "events": session_rows}


def validate_shard(directory: Path, *, config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if config is None:
        config = _read_yaml(_root() / CONFIG_PATH)
    for name in ("activations.npy", "observations.jsonl", "shard_receipt.json", "SHA256SUMS"):
        _require((directory / name).is_file(), f"Missing shard file: {name}")
    receipt = _read_json(directory / "shard_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "Shard receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"Shard output hash mismatch: {name}")
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    _require(list(array.shape) == receipt["activation_shape"], "Shard array shape mismatch")
    _require(str(array.dtype) == "float32", "Shard array dtype mismatch")
    _require(array.shape[1:] == (3, 2, 4, 9, int(config["model"]["expected_model_dim"])), "Shard fixed dimensions changed")
    for start in range(0, array.shape[0], 4):
        _require(bool(np.isfinite(np.asarray(array[start : start + 4])).all()), "Shard has nonfinite values")
    return {"status": "pass", "shard_index": receipt["shard_index"], "item_count": receipt["item_count"]}


def finalize_run(run_root: Path) -> dict[str, Any]:
    freeze = audit_freeze()
    config = _read_yaml(_root() / CONFIG_PATH)
    selection = _read_json(_root() / SELECTION_PATH)
    expected_shards = int(config["storage"]["expected_shards"])
    receipts: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for index in range(expected_shards):
        directory = run_root / f"shard_{index:04d}"
        validate_shard(directory, config=config)
        receipt = _read_json(directory / "shard_receipt.json")
        _require(int(receipt["shard_index"]) == index, "Shard order mismatch")
        receipts.append(receipt)
        hashes[directory.name] = _sha256(directory / "SHA256SUMS")
    item_count = sum(int(receipt["item_count"]) for receipt in receipts)
    unique_inputs = sum(int(receipt["unique_input_sequences"]) for receipt in receipts)
    vectors = sum(int(receipt["causal_readout_vectors"]) for receipt in receipts)
    _require(item_count == int(config["storage"]["expected_acquired_items"]), "Final item count mismatch")
    _require(unique_inputs == int(config["storage"]["expected_unique_input_sequences"]), "Final input count mismatch")
    _require(vectors == int(config["storage"]["expected_readout_vectors"]), "Final vector count mismatch")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "experiment_role": config["experiment_role"],
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "candidate_counts": selection["role_counts"],
        "acquired_item_count": item_count,
        "reserved_unrun_item_count": int(selection["reserved_item_count"]),
        "unique_input_sequences": unique_inputs,
        "causal_readout_vectors": vectors,
        "batched_model_forward_calls": sum(int(receipt["batched_model_forward_calls"]) for receipt in receipts),
        "shard_count": len(receipts),
        "shard_ledger_sha256": hashes,
        "activation_dtype": "float32",
        "axis_order": config["storage"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": config["input"]["distance_order"],
        "layers": config["layers"]["expected_resolved_layers"],
        "intervention_calls": 0,
        "generation_calls": 0,
        "reserved_unrun_model_inputs_forwarded": 0,
        "confirmatory_status": False,
        "phase_i_gate_closed": False,
        "raw_activations_committed_to_git": False,
    }
    _write_json(run_root / "run_receipt.json", receipt)
    _write_json(run_root / "SHARD_INDEX.json", {"protocol_id": PROTOCOL_ID, "shards": hashes})
    _write_ledger(run_root, ("run_receipt.json", "SHARD_INDEX.json"))
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("build-selection")
    selection.add_argument("--census", type=Path, required=True)
    selection.add_argument("--output", type=Path, default=_root() / SELECTION_PATH)
    preflight = sub.add_parser("build-preflight")
    preflight.add_argument("--selection", type=Path, default=_root() / SELECTION_PATH)
    preflight.add_argument("--model", type=Path, required=True)
    preflight.add_argument("--output", type=Path, default=_root() / PREFLIGHT_PATH)
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    sub.add_parser("audit-freeze")
    run = sub.add_parser("run")
    run.add_argument("--model", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--shard-start", type=int, default=0)
    run.add_argument("--shard-stop", type=int)
    validate = sub.add_parser("validate-shard")
    validate.add_argument("--shard", type=Path, required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--run", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "build-selection":
        result = build_selection(args.census, args.output)
    elif args.command == "build-preflight":
        result = build_preflight(args.selection, args.model, args.output)
    elif args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run":
        result = run_shards(args.model, args.output, args.shard_start, args.shard_stop)
    elif args.command == "validate-shard":
        result = validate_shard(args.shard)
    elif args.command == "finalize":
        result = finalize_run(args.run)
    else:  # pragma: no cover
        raise AtlasError(f"Unknown command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
