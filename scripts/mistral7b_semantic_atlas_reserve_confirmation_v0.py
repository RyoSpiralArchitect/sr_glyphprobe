#!/usr/bin/env python3
"""Freeze, acquire, and decide the single-use T8 reserve confirmation."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


PROTOCOL_ID = "glyphprobe-mistral7b-semantic-atlas-reserve-confirmation-v0"
CONFIG_PATH = Path("configs/mistral7b_semantic_atlas_reserve_confirmation_v0.yaml")
FREEZE_PATH = Path(
    "data/manifests/mistral7b_semantic_atlas_reserve_confirmation_v0.json"
)
FROZEN_ASSETS = (
    "configs/mistral7b_semantic_atlas_reserve_confirmation_v0.yaml",
    "data/manifests/mistral7b_semantic_atlas_selection_v0.json",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/PUBLIC_MANIFEST.json",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/run/run_receipt.json",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/validation/batch1_capture_validation_pass.json",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/analysis/analysis_receipt.json",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/analysis/cell_metrics.jsonl",
    "artifacts/mistral7b_semantic_atlas_batch1_v1/analysis/layer_summary.json",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md",
    "scripts/mistral7b_semantic_atlas_reserve_confirmation_v0.py",
    "scripts/mistral7b_semantic_atlas_v0.py",
    "tests/test_mistral7b_semantic_atlas_reserve_confirmation_v0.py",
    "validation/mistral7b_semantic_atlas_v0/engineering_preflight.json",
)
VIEW_ORDER = ("glyph", "unicode_name", "codepoint_literal")
PAIR_ORDER = (("glyph_name", 0, 1), ("glyph_codepoint", 0, 2))


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    atlas._require(value.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return value


def _binding_pairs(config: Mapping[str, Any]) -> list[tuple[Path, str]]:
    bindings = config["source_bindings"]
    names = (
        "selection_manifest",
        "canonical_run_receipt",
        "canonical_capture_validation",
        "discovery_analysis_receipt",
        "discovery_cell_metrics",
        "discovery_layer_summary",
        "discovery_public_manifest",
        "original_engineering_preflight",
    )
    return [
        (_root() / str(bindings[name]), str(bindings[f"{name}_sha256"]))
        for name in names
    ]


def _audit_source_bindings(config: Mapping[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in _binding_pairs(config):
        atlas._require(path.is_file(), f"Bound source missing: {path.name}")
        actual = atlas._sha256(path)
        atlas._require(actual == expected, f"Bound source changed: {path.name}")
        observed[path.relative_to(_root()).as_posix()] = actual

    bindings = config["source_bindings"]
    run = atlas._read_json(_root() / str(bindings["canonical_run_receipt"]))
    capture = atlas._read_json(_root() / str(bindings["canonical_capture_validation"]))
    analysis = atlas._read_json(_root() / str(bindings["discovery_analysis_receipt"]))
    selection = atlas._read_json(_root() / str(bindings["selection_manifest"]))
    atlas._require(run.get("status") == "pass", "Canonical run did not pass")
    atlas._require(
        int(run.get("reserved_unrun_model_inputs_forwarded", -1)) == 0,
        "Canonical run touched reserve",
    )
    atlas._require(
        capture.get("status") == "pass"
        and int(capture.get("passed_case_count", -1)) == 18
        and float(capture.get("minimum_exact_element_fraction", -1.0)) == 1.0,
        "Canonical batch-one capture was not bit-exact",
    )
    atlas._require(
        int(capture.get("reserve_forward_calls", -1)) == 0,
        "Capture validation touched reserve",
    )
    atlas._require(
        analysis.get("status") == "pass"
        and int(analysis.get("reserved_unrun_model_inputs_forwarded", -1)) == 0,
        "Discovery analysis reserve boundary failed",
    )
    atlas._require(
        int(selection["role_counts"]["reserved_unrun"])
        == int(config["population"]["expected_items"]),
        "Reserve count changed",
    )
    return observed


def confirmation_items() -> list[dict[str, Any]]:
    config = _config()
    selection = atlas._read_json(
        _root() / str(config["source_bindings"]["selection_manifest"])
    )
    rows = [
        dict(row)
        for row in selection["candidates"]
        if str(row["role"]) == str(config["population"]["source_role"])
    ]
    rows.sort(key=lambda row: int(row["source_index"]))
    atlas._require(
        len(rows) == int(config["population"]["expected_items"]),
        "Reserve population changed",
    )
    for index, row in enumerate(rows):
        atlas._require(row.get("acquisition_index") is None, "Reserve was acquired")
        atlas._require(
            row.get("included_in_acquisition") is False,
            "Reserve acquisition flag changed",
        )
        row["confirmation_index"] = index
    return rows


def audit_design_basis() -> dict[str, Any]:
    config = _config()
    _audit_source_bindings(config)
    path = _root() / str(config["source_bindings"]["discovery_cell_metrics"])
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    selected = [
        row
        for row in rows
        if row["population"] == "discovery_unseen"
        and int(row["layer"]) == int(config["primary_endpoint"]["layer"])
    ]
    selected.sort(
        key=lambda row: (
            list(config["input"]["carrier_order"]).index(row["carrier"]),
            list(config["input"]["distance_order"]).index(int(row["distance"])),
        )
    )
    atlas._require(len(selected) == 8, "Discovery design grid is incomplete")
    contrasts = [
        float(row["pairs"]["glyph_name"]["top1_accuracy_forward"])
        - float(row["pairs"]["glyph_codepoint"]["top1_accuracy_forward"])
        for row in selected
    ]
    basis = config["discovery_design_basis"]
    observed_minimum = float(min(contrasts))
    observed_mean = float(np.mean(contrasts))
    atlas._require(
        abs(observed_minimum - float(basis["observed_minimum_cell_contrast"])) <= 1e-12,
        "Discovery minimum binding mismatch",
    )
    atlas._require(
        abs(observed_mean - float(basis["observed_equal_cell_mean_contrast"])) <= 1e-12,
        "Discovery mean binding mismatch",
    )
    atlas._require(
        float(config["primary_endpoint"]["practical_minimum"]) < observed_minimum,
        "Practical floor does not sit below discovery minimum",
    )
    return {
        "status": "pass",
        "cell_count": len(selected),
        "observed_minimum_cell_contrast": observed_minimum,
        "observed_equal_cell_mean_contrast": observed_mean,
        "reserve_items": len(confirmation_items()),
        "reserve_model_inputs_forwarded": 0,
    }


def build_freeze(output: Path) -> dict[str, Any]:
    config = _config()
    source_hashes = _audit_source_bindings(config)
    design = audit_design_basis()
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = _root() / relative
        atlas._require(path.is_file(), f"Frozen asset missing: {relative}")
        assets[relative] = atlas._sha256(path)
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_reserve_confirmation_forward",
        "experiment_role": config["experiment_role"],
        "claim_boundary": config["claim_boundary"],
        "frozen_assets": assets,
        "source_bindings": source_hashes,
        "discovery_design_audit": design,
        "reserve_items": int(config["population"]["expected_items"]),
        "reserve_model_inputs_forwarded_at_freeze": 0,
        "expected_model_forward_calls": int(
            config["acquisition"]["expected_model_forward_calls"]
        ),
        "primary_endpoint": config["primary_endpoint"],
        "scientific_result_available_at_freeze": False,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
    }
    atlas._require(not output.exists(), "Freeze manifest already exists")
    atlas._write_json(output, payload)
    return {
        "status": "pass",
        "manifest_sha256": atlas._sha256(output),
        "frozen_asset_count": len(assets),
    }


def audit_freeze() -> dict[str, Any]:
    config = _config()
    manifest = atlas._read_json(_root() / FREEZE_PATH)
    atlas._require(
        manifest.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch"
    )
    atlas._require(
        manifest.get("status")
        == "freeze_complete_before_any_reserve_confirmation_forward",
        "Freeze is incomplete",
    )
    for relative, expected in manifest["frozen_assets"].items():
        path = _root() / relative
        atlas._require(path.is_file(), f"Frozen asset missing: {relative}")
        atlas._require(
            atlas._sha256(path) == expected, f"Frozen asset changed: {relative}"
        )
    current_sources = _audit_source_bindings(config)
    atlas._require(
        current_sources == manifest["source_bindings"], "Source bindings changed"
    )
    atlas._require(
        int(manifest["reserve_model_inputs_forwarded_at_freeze"]) == 0,
        "Freeze records a reserve forward",
    )
    return {
        "status": "pass",
        "manifest_sha256": atlas._sha256(_root() / FREEZE_PATH),
        "frozen_asset_count": len(manifest["frozen_assets"]),
    }


def _run_one_shard(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
    config: Mapping[str, Any],
    freeze: Mapping[str, Any],
    run_root: Path,
    shard_index: int,
) -> dict[str, Any]:
    items_all = confirmation_items()
    shard_size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(items_all), start + shard_size)
    atlas._require(start < stop, f"Shard index out of range: {shard_index}")
    items = items_all[start:stop]
    layers = [int(value) for value in config["acquisition"]["layers"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    width = int(config["model"]["expected_model_dim"])
    stage, final = atlas._atomic_shard_directory(run_root, shard_index)
    intent = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "forward_may_begin_after_this_record",
        "shard_index": shard_index,
        "confirmation_index_start": start,
        "confirmation_index_stop_exclusive": stop,
        "item_codepoints": [str(item["codepoint"]) for item in items],
        "retry_policy": "never_automatically_reacquire_a_partial_shard",
    }
    atlas._write_json(stage / "execution_intent.json", intent)
    activations = np.empty(
        (
            len(items),
            len(VIEW_ORDER),
            len(carriers),
            len(distances),
            len(layers),
            width,
        ),
        dtype=np.float32,
    )
    records = atlas._record_rows(items, config)
    batch_size = int(config["acquisition"]["batch_size_unique_sequences"])
    atlas._require(batch_size == 1, "Confirmation batch size must remain one")
    pad_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 0
    observations: list[dict[str, Any]] = []
    forward_calls = 0
    started = time.perf_counter()
    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]
        max_tokens = max(len(row["input_ids"]) for row in batch)
        input_ids = torch.full(
            (len(batch), max_tokens), int(pad_id), dtype=torch.long, device="cuda"
        )
        attention_mask = torch.zeros(
            (len(batch), max_tokens), dtype=torch.long, device="cuda"
        )
        positions: list[list[int]] = []
        for index, row in enumerate(batch):
            ids = row["input_ids"]
            input_ids[index, : len(ids)] = torch.tensor(
                ids, dtype=torch.long, device="cuda"
            )
            attention_mask[index, : len(ids)] = 1
            positions.append(
                [len(row["raw_ids"]) + distance - 1 for distance in distances]
            )
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
        atlas._require(
            len(output.hidden_states)
            == int(config["model"]["expected_num_layers"]) + 1,
            "Hidden-state roster mismatch",
        )
        selected = torch.stack(
            [output.hidden_states[layer + 1] for layer in layers], dim=2
        )
        position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
        batch_tensor = torch.arange(len(batch), device="cuda")[:, None]
        captured = selected[batch_tensor, position_tensor].float().cpu().numpy()
        atlas._require(
            captured.shape == (len(batch), len(distances), len(layers), width),
            "Captured batch shape mismatch",
        )
        atlas._require(bool(np.isfinite(captured).all()), "Nonfinite activation")
        for index, row in enumerate(batch):
            item = items[int(row["item_offset"])]
            values = captured[index]
            activations[
                int(row["item_offset"]),
                int(row["view_index"]),
                int(row["carrier_index"]),
            ] = values
            observations.append(
                {
                    "confirmation_index": int(item["confirmation_index"]),
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
                    "forward_latency_ms": elapsed_ms,
                }
            )
        forward_calls += 1
        del output, selected, captured, input_ids, attention_mask
        del position_tensor, batch_tensor
    atlas._require(bool(np.isfinite(activations).all()), "Shard is nonfinite")
    np.save(stage / "activations.npy", activations, allow_pickle=False)
    atlas._write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "shard_index": shard_index,
        "confirmation_index_start": start,
        "confirmation_index_stop_exclusive": stop,
        "item_count": len(items),
        "item_codepoints": [str(item["codepoint"]) for item in items],
        "role_counts": dict(Counter(str(item["role"]) for item in items)),
        "activation_shape": list(activations.shape),
        "activation_dtype": str(activations.dtype),
        "axis_order": config["acquisition"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": carriers,
        "distance_order": distances,
        "layers": layers,
        "unique_input_sequences": len(records),
        "model_forward_calls": forward_calls,
        "reserved_items_forwarded": len(items),
        "reserved_model_inputs_forwarded": len(records),
        "causal_readout_vectors": int(np.prod(activations.shape[:-1])),
        "fused_distance_readout": True,
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
        "model": model_receipt,
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "source_selection_sha256": str(
            config["source_bindings"]["selection_manifest_sha256"]
        ),
        "outputs": {
            "execution_intent.json": atlas._sha256(stage / "execution_intent.json"),
            "activations.npy": atlas._sha256(stage / "activations.npy"),
            "observations.jsonl": atlas._sha256(stage / "observations.jsonl"),
        },
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_decision_authorized": False,
    }
    atlas._write_json(stage / "shard_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        (
            "execution_intent.json",
            "activations.npy",
            "observations.jsonl",
            "shard_receipt.json",
        ),
    )
    stage.rename(final)
    return receipt


def validate_shard(directory: Path) -> dict[str, Any]:
    config = _config()
    names = (
        "execution_intent.json",
        "activations.npy",
        "observations.jsonl",
        "shard_receipt.json",
        "SHA256SUMS",
    )
    for name in names:
        atlas._require((directory / name).is_file(), f"Missing shard file: {name}")
    receipt = atlas._read_json(directory / "shard_receipt.json")
    atlas._require(
        receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass",
        "Shard receipt mismatch",
    )
    for name, expected in receipt["outputs"].items():
        atlas._require(
            atlas._sha256(directory / name) == expected,
            f"Shard output hash mismatch: {name}",
        )
    shard_index = int(receipt["shard_index"])
    shard_size = int(config["acquisition"]["item_shard_size"])
    expected_items = confirmation_items()[
        shard_index * shard_size : (shard_index + 1) * shard_size
    ]
    atlas._require(
        receipt["item_codepoints"]
        == [str(item["codepoint"]) for item in expected_items],
        "Shard population changed",
    )
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    expected_shape = (
        len(expected_items),
        3,
        2,
        4,
        1,
        int(config["model"]["expected_model_dim"]),
    )
    atlas._require(tuple(array.shape) == expected_shape, "Shard shape mismatch")
    atlas._require(str(array.dtype) == "float32", "Shard dtype mismatch")
    for start in range(0, len(expected_items), 4):
        atlas._require(
            bool(np.isfinite(np.asarray(array[start : start + 4])).all()),
            "Shard has nonfinite values",
        )
    expected_inputs = len(expected_items) * len(VIEW_ORDER) * 2
    atlas._require(
        int(receipt["model_forward_calls"]) == expected_inputs,
        "Shard forward count mismatch",
    )
    atlas._require(
        int(receipt["reserved_model_inputs_forwarded"]) == expected_inputs,
        "Shard reserve forward count mismatch",
    )
    return {
        "status": "pass",
        "shard_index": shard_index,
        "item_count": len(expected_items),
    }


def run_shards(
    model_path: Path, run_root: Path, shard_start: int, shard_stop: int | None
) -> dict[str, Any]:
    freeze = audit_freeze()
    config = _config()
    _audit_source_bindings(config)
    atlas._validate_runtime(config)
    expected_shards = int(config["acquisition"]["expected_shards"])
    stop = expected_shards if shard_stop is None else shard_stop
    atlas._require(0 <= shard_start < stop <= expected_shards, "Invalid shard range")
    run_root.mkdir(parents=True, exist_ok=True)
    atlas._require(
        not list(run_root.glob(".shard_*.partial-*")),
        "Partial shard exists; automatic retry is forbidden",
    )
    atlas._require(
        not (run_root / "run_receipt.json").exists(), "Run is already finalized"
    )
    lock = run_root / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise atlas.AtlasError("Run root already has an active writer lock") from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    os.close(descriptor)
    session_rows: list[dict[str, Any]] = []
    model = None
    status = "fail"
    try:
        pending = [
            index
            for index in range(shard_start, stop)
            if not (run_root / f"shard_{index:04d}").exists()
        ]
        for index in range(shard_start, stop):
            existing = run_root / f"shard_{index:04d}"
            if existing.exists():
                validate_shard(existing)
        if not pending:
            status = "pass"
            return {
                "status": status,
                "message": "requested shards already complete",
                "events": [],
            }
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(
                f"Foreign GPU compute PIDs before model load: {foreign}"
            )
        torch, tokenizer, model, model_receipt = atlas._load_model(model_path, config)
        for shard_index in pending:
            foreign = atlas._foreign_gpu_pids()
            if foreign:
                raise atlas.ContentionDetected(
                    f"Foreign GPU compute PIDs before shard {shard_index}: {foreign}"
                )
            receipt = _run_one_shard(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                model_receipt=model_receipt,
                config=config,
                freeze=freeze,
                run_root=run_root,
                shard_index=shard_index,
            )
            session_rows.append(
                {
                    "shard_index": shard_index,
                    "item_count": receipt["item_count"],
                    "model_forward_calls": receipt["model_forward_calls"],
                    "elapsed_ms": receipt["elapsed_ms"],
                }
            )
        status = "pass"
    except atlas.ContentionDetected as exc:
        status = "yielded_on_contention"
        session_rows.append({"contention": str(exc)})
    finally:
        if model is not None:
            del model
            import torch

            torch.cuda.empty_cache()
        lock.unlink(missing_ok=True)
        session_path = run_root / (
            f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_"
            f"{uuid.uuid4().hex[:8]}.json"
        )
        atlas._write_json(
            session_path,
            {
                "schema_version": 1,
                "protocol_id": PROTOCOL_ID,
                "status": status,
                "requested_shard_start": shard_start,
                "requested_shard_stop_exclusive": stop,
                "events": session_rows,
            },
        )
    return {"status": status, "events": session_rows}


def finalize_run(run_root: Path) -> dict[str, Any]:
    freeze = audit_freeze()
    config = _config()
    atlas._require(
        not list(run_root.glob(".shard_*.partial-*")),
        "Partial shard makes automatic completion invalid",
    )
    atlas._require(
        not (run_root / "run_receipt.json").exists(), "Run already finalized"
    )
    receipts: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for index in range(int(config["acquisition"]["expected_shards"])):
        directory = run_root / f"shard_{index:04d}"
        validate_shard(directory)
        receipt = atlas._read_json(directory / "shard_receipt.json")
        atlas._require(int(receipt["shard_index"]) == index, "Shard order mismatch")
        receipts.append(receipt)
        hashes[directory.name] = atlas._sha256(directory / "SHA256SUMS")
    items = sum(int(receipt["item_count"]) for receipt in receipts)
    inputs = sum(int(receipt["model_forward_calls"]) for receipt in receipts)
    vectors = sum(int(receipt["causal_readout_vectors"]) for receipt in receipts)
    atlas._require(
        items == int(config["population"]["expected_items"]), "Item count mismatch"
    )
    atlas._require(
        inputs == int(config["acquisition"]["expected_model_forward_calls"]),
        "Forward count mismatch",
    )
    atlas._require(
        vectors == int(config["acquisition"]["expected_readout_vectors"]),
        "Vector count mismatch",
    )
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "experiment_role": config["experiment_role"],
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "source_selection_sha256": str(
            config["source_bindings"]["selection_manifest_sha256"]
        ),
        "reserve_items": items,
        "reserved_items_forwarded": items,
        "reserved_model_inputs_forwarded": inputs,
        "unique_input_sequences": inputs,
        "model_forward_calls": inputs,
        "causal_readout_vectors": vectors,
        "shard_count": len(receipts),
        "shard_ledger_sha256": hashes,
        "activation_dtype": "float32",
        "axis_order": config["acquisition"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": config["input"]["distance_order"],
        "layers": config["acquisition"]["layers"],
        "acquisition_status": "complete_analysis_pending",
        "confirmatory_status": None,
        "intervention_calls": 0,
        "generation_calls": 0,
        "raw_activations_committed_to_git": False,
    }
    atlas._write_json(run_root / "run_receipt.json", receipt)
    atlas._write_json(
        run_root / "SHARD_INDEX.json", {"protocol_id": PROTOCOL_ID, "shards": hashes}
    )
    atlas._write_ledger(run_root, ("run_receipt.json", "SHARD_INDEX.json"))
    return receipt


def _pair_metrics(
    torch: Any, left: Any, right: Any
) -> tuple[dict[str, float], Any, Any]:
    similarity = left @ right.T
    count = int(similarity.shape[0])
    order = torch.arange(count, device=similarity.device)
    diagonal = torch.diagonal(similarity)
    prediction_forward = similarity.argmax(dim=1)
    prediction_reverse = similarity.argmax(dim=0)
    ranks_forward = 1 + (similarity > diagonal[:, None]).sum(dim=1)
    ranks_reverse = 1 + (similarity > diagonal[None, :]).sum(dim=0)
    off_diagonal = (similarity.sum() - diagonal.sum()) / max(1, count * (count - 1))
    metrics = {
        "paired_cosine_mean": float(diagonal.mean().item()),
        "off_diagonal_cosine_mean": float(off_diagonal.item()),
        "paired_minus_off_diagonal_margin": float(
            (diagonal.mean() - off_diagonal).item()
        ),
        "top1_accuracy_forward": float(
            (prediction_forward == order).float().mean().item()
        ),
        "top1_accuracy_reverse": float(
            (prediction_reverse == order).float().mean().item()
        ),
        "mean_reciprocal_rank_forward": float(
            (1.0 / ranks_forward.float()).mean().item()
        ),
        "mean_reciprocal_rank_reverse": float(
            (1.0 / ranks_reverse.float()).mean().item()
        ),
    }
    return metrics, prediction_forward.detach().cpu(), prediction_reverse.detach().cpu()


def _cell_metrics(
    torch: Any, values: np.ndarray
) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    tensor = torch.from_numpy(np.asarray(values, dtype=np.float32)).to("cuda")
    centered = tensor - tensor.mean(dim=1, keepdim=True)
    normalized = torch.nn.functional.normalize(centered, p=2, dim=-1, eps=1e-12)
    centered_grams = [centered[index] @ centered[index].T for index in range(3)]
    pair_results: dict[str, Any] = {}
    predictions: dict[str, Any] = {}
    reverse_predictions: dict[str, Any] = {}
    for name, left, right in PAIR_ORDER:
        metrics, prediction, reverse_prediction = _pair_metrics(
            torch, normalized[left], normalized[right]
        )
        denominator = torch.sqrt(
            torch.sum(centered_grams[left].square())
            * torch.sum(centered_grams[right].square())
        )
        metrics["centered_linear_cka"] = float(
            (
                torch.sum(centered_grams[left] * centered_grams[right])
                / torch.clamp(denominator, min=1e-30)
            ).item()
        )
        pair_results[name] = metrics
        predictions[name] = prediction
        reverse_predictions[name] = reverse_prediction
    result = {
        "pairs": pair_results,
        "glyph_name_minus_glyph_codepoint": {
            key: float(
                pair_results["glyph_name"][key] - pair_results["glyph_codepoint"][key]
            )
            for key in (
                "paired_cosine_mean",
                "paired_minus_off_diagonal_margin",
                "top1_accuracy_forward",
                "top1_accuracy_reverse",
                "mean_reciprocal_rank_forward",
                "mean_reciprocal_rank_reverse",
                "centered_linear_cka",
            )
        },
    }
    del tensor, centered, normalized, centered_grams
    return (
        result,
        predictions["glyph_name"].numpy(),
        predictions["glyph_codepoint"].numpy(),
    )


def primary_randomization_test(
    name_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
    *,
    draws: int,
    seed: int,
    alpha: float,
    practical_minimum: float,
) -> dict[str, Any]:
    atlas._require(name_predictions.ndim == 2, "Name prediction matrix rank changed")
    atlas._require(
        name_predictions.shape == codepoint_predictions.shape,
        "Prediction shapes differ",
    )
    cell_count, item_count = name_predictions.shape
    order = np.arange(item_count, dtype=np.int64)
    name_top1 = np.mean(name_predictions == order[None, :], axis=1)
    codepoint_top1 = np.mean(codepoint_predictions == order[None, :], axis=1)
    contrasts = name_top1 - codepoint_top1
    observed = float(np.min(contrasts))
    rng = np.random.default_rng(seed)
    null_statistics = np.empty(draws, dtype=np.float64)
    exceedances = 0
    for index in range(draws):
        permutation = rng.permutation(item_count)
        permuted_name = np.mean(name_predictions == permutation[None, :], axis=1)
        statistic = float(np.min(permuted_name - codepoint_top1))
        null_statistics[index] = statistic
        exceedances += int(statistic >= observed)
    p_value = float((1 + exceedances) / (draws + 1))
    confirmed = bool(p_value <= alpha and observed >= practical_minimum)
    return {
        "status": "pass",
        "outcome_pattern": (
            "transport_robust_late_depth_glyph_name_alignment_confirmed"
            if confirmed
            else "not_confirmed_under_frozen_rule"
        ),
        "alignment_confirmed": confirmed,
        "t8_reserve_question_closed": True,
        "item_count": item_count,
        "cell_count": cell_count,
        "name_top1_by_cell": name_top1.tolist(),
        "codepoint_top1_by_cell": codepoint_top1.tolist(),
        "contrast_by_cell": contrasts.tolist(),
        "observed_minimum_cell_contrast": observed,
        "observed_equal_cell_mean_contrast": float(np.mean(contrasts)),
        "practical_minimum": practical_minimum,
        "randomization_draws": draws,
        "randomization_seed": seed,
        "exceedances": exceedances,
        "p_value": p_value,
        "alpha": alpha,
        "multiplicity": "none_single_global_minimum_statistic",
        "null_statistic_quantiles": {
            str(quantile): float(np.quantile(null_statistics, quantile))
            for quantile in (0.0, 0.5, 0.95, 0.99, 1.0)
        },
    }


def analyze(run_root: Path, output: Path) -> dict[str, Any]:
    import torch

    freeze = audit_freeze()
    config = _config()
    source_receipt = atlas._read_json(run_root / "run_receipt.json")
    atlas._require(
        source_receipt.get("protocol_id") == PROTOCOL_ID
        and source_receipt.get("status") == "pass",
        "Source run is not complete",
    )
    atlas._require(
        int(source_receipt["reserved_items_forwarded"])
        == int(config["population"]["expected_items"]),
        "Reserve population was not completely forwarded",
    )
    for index in range(int(config["acquisition"]["expected_shards"])):
        validate_shard(run_root / f"shard_{index:04d}")
    foreign = atlas._foreign_gpu_pids()
    if foreign:
        raise atlas.ContentionDetected(
            f"Foreign GPU compute PIDs before confirmation analysis: {foreign}"
        )
    torch.set_float32_matmul_precision("highest")
    arrays = [
        np.load(
            run_root / f"shard_{index:04d}" / "activations.npy",
            mmap_mode="r",
            allow_pickle=False,
        )
        for index in range(int(config["acquisition"]["expected_shards"]))
    ]
    items = confirmation_items()
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    cell_rows: list[dict[str, Any]] = []
    name_predictions: list[np.ndarray] = []
    codepoint_predictions: list[np.ndarray] = []
    item_rows = [
        {
            "confirmation_index": int(item["confirmation_index"]),
            "source_index": int(item["source_index"]),
            "codepoint": str(item["codepoint"]),
            "glyph": str(item["glyph"]),
            "name": str(item["name"]),
            "group": str(item["group"]),
            "subgroup": str(item["subgroup"]),
            "cells": [],
        }
        for item in items
    ]
    for carrier_index, carrier in enumerate(carriers):
        for distance_index, distance in enumerate(distances):
            if atlas._foreign_gpu_pids():
                raise atlas.ContentionDetected(
                    "Foreign GPU compute PID appeared during confirmation analysis"
                )
            all_values = np.concatenate(
                [
                    np.asarray(array[:, :, carrier_index, distance_index, 0, :])
                    for array in arrays
                ],
                axis=0,
            )
            values = np.transpose(all_values, (1, 0, 2))
            metrics, name_prediction, codepoint_prediction = _cell_metrics(
                torch, values
            )
            name_predictions.append(name_prediction)
            codepoint_predictions.append(codepoint_prediction)
            cell_rows.append(
                {
                    "cell_index": len(cell_rows),
                    "item_count": len(items),
                    "layer": int(config["primary_endpoint"]["layer"]),
                    "carrier": carrier,
                    "carrier_index": carrier_index,
                    "distance": distance,
                    "distance_index": distance_index,
                    **metrics,
                }
            )
            for item_index, row in enumerate(item_rows):
                row["cells"].append(
                    {
                        "carrier": carrier,
                        "distance": distance,
                        "glyph_name_predicted_confirmation_index": int(
                            name_prediction[item_index]
                        ),
                        "glyph_codepoint_predicted_confirmation_index": int(
                            codepoint_prediction[item_index]
                        ),
                        "glyph_name_top1_correct": bool(
                            int(name_prediction[item_index]) == item_index
                        ),
                        "glyph_codepoint_top1_correct": bool(
                            int(codepoint_prediction[item_index]) == item_index
                        ),
                    }
                )
            del all_values, values
    primary_spec = config["primary_endpoint"]
    primary = primary_randomization_test(
        np.stack(name_predictions),
        np.stack(codepoint_predictions),
        draws=int(primary_spec["randomization_draws"]),
        seed=int(primary_spec["randomization_seed"]),
        alpha=float(primary_spec["alpha"]),
        practical_minimum=float(primary_spec["practical_minimum"]),
    )
    primary.update(
        {
            "protocol_id": PROTOCOL_ID,
            "statistic": primary_spec["statistic"],
            "randomization_null": primary_spec["randomization_null"],
            "positive_rule": primary_spec["positive_rule"],
            "cell_order": [
                {"carrier": row["carrier"], "distance": row["distance"]}
                for row in cell_rows
            ],
        }
    )
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    atlas._require(not output.exists(), "Analysis output already exists")
    stage.mkdir(parents=True)
    atlas._write_jsonl(stage / "cell_metrics.jsonl", cell_rows)
    atlas._write_jsonl(stage / "item_retrieval_outcomes.jsonl", item_rows)
    atlas._write_json(stage / "primary_result.json", primary)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "outcome_pattern": primary["outcome_pattern"],
        "alignment_confirmed": primary["alignment_confirmed"],
        "t8_reserve_question_closed": True,
        "analysis_role": "prospectively_frozen_single_primary_confirmation",
        "source_run_receipt_sha256": atlas._sha256(run_root / "run_receipt.json"),
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "reserve_items": len(items),
        "cell_row_count": len(cell_rows),
        "item_row_count": len(item_rows),
        "primary_result_sha256": atlas._sha256(stage / "primary_result.json"),
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "confirmatory_status": bool(primary["alignment_confirmed"]),
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "model_general_claim_authorized": False,
        "phase_i_gate_closed": False,
    }
    atlas._write_json(stage / "analysis_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        (
            "cell_metrics.jsonl",
            "item_retrieval_outcomes.jsonl",
            "primary_result.json",
            "analysis_receipt.json",
        ),
    )
    stage.rename(output)
    torch.cuda.empty_cache()
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design-basis")
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
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--run", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit-design-basis":
        result = audit_design_basis()
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
    elif args.command == "analyze":
        result = analyze(args.run, args.output)
    else:  # pragma: no cover
        raise atlas.AtlasError(f"Unknown command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
