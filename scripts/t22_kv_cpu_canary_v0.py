#!/usr/bin/env python3
"""Separate exposed-item CPU engineering canary, never a historical GPU replay.

Only the eight versioned T21 canary token rows and their original donors are
eligible. No tokenizer, target-bank reader, downloader, gallery, or scientific
effect estimator is used here. The historical strict GPU gate is unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
from typing import Any
import uuid

import numpy as np

import t21_glyph_context_path_pilot_v0 as historical
import t22_kv_dissection_v0 as t22


ROOT = historical.ROOT
PROTOCOL = "glyphprobe-t22-kv-cpu-engineering-canary-v0"
CARRIERS = ("pipe", "article_a")
POSITION_CONDITIONS = ("reset_glyph_donor", "reset_suffix_donor")
BLOCKS = tuple(range(22, 28))
REQUIRED_TORCH = "2.13.0+cpu"
REQUIRED_TRANSFORMERS = "5.15.0"
MODEL_DIMENSIONS = {"layers": 28, "hidden_size": 3072, "attention_heads": 24,
                    "kv_heads": 8, "head_dim": 128}
ENGINEERING_CHECKS = (
    "stock_historical_exact", "stock_t22_exact", "donor_and_reset_captures_exact",
    "same_cpu_legacy_kv_full_hidden_states_exact",
    "same_cpu_legacy_neutral_full_hidden_states_exact",
    "same_slot_no_op_and_roundtrip_exact", "local_v_attention_weights_unchanged",
    "nonreadout_attention_outputs_unchanged", "complete_actual_attention_diagnostics",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _progress(stage: str, **details: Any) -> None:
    print(json.dumps({"stage": stage, **details}, sort_keys=True), flush=True)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _model_dimensions(model: Any) -> dict[str, int]:
    return {"layers": len(model.model.layers), "hidden_size": model.config.hidden_size,
            "attention_heads": model.config.num_attention_heads,
            "kv_heads": model.config.num_key_value_heads,
            "head_dim": model.model.layers[0].self_attn.head_dim}


def legacy_rows(glyph_length: int) -> list[dict[str, Any]]:
    """Preserve T21 patch_item's exact original 88-row order and batch size."""
    return [
        {
            "distance": distance,
            "distance_index": distance_index,
            "anchor": anchor,
            "condition": condition,
            "donor_slot": donor,
            "glyph_length": glyph_length,
            "position": glyph_length + distance - 1,
        }
        for distance_index, distance in enumerate((4, 8))
        for anchor in historical.ANCHORS
        for donor in range(2)
        for condition in historical.CONDITIONS
    ]


def extension_rows(glyph_length: int) -> list[dict[str, Any]]:
    return [
        {
            "distance": 8,
            "distance_index": 1,
            "anchor": 21,
            "condition": condition,
            "donor_slot": donor,
            "glyph_length": glyph_length,
            "position": glyph_length + 7,
            "operation": operation,
        }
        for operation in t22.OPERATIONS
        for condition in POSITION_CONDITIONS
        for donor in range(2)
    ]


def _validate_tokens(tokens: dict, donor_tokens: list[dict]) -> None:
    require(len(donor_tokens) == 2, "Exactly the two predetermined donors are required")
    length = len(tokens["raw"]["glyph"])
    require(1 <= length <= 3, "Unsupported glyph token count")
    for donor in donor_tokens:
        require(len(donor["raw"]["glyph"]) == length, "Donor token-count mismatch")
    for carrier in CARRIERS:
        for row in (tokens, *donor_tokens):
            views = ("glyph", "codepoint_literal") if row is tokens else ("glyph",)
            for view in views:
                ids = row["sequences"][carrier][view]
                raw = row["raw"][view]
                require(len(ids) == len(raw) + 8 and ids[:len(raw)] == raw,
                        "Expected the original unpadded eight-carrier sequence")
                require(all(type(token) is int and token >= 0 for token in ids),
                        "Invalid token IDs")


def _capture(torch: Any, model: Any, controller: Any, tokens: dict,
             carrier: str, view: str, forward: Any, stage: str) -> tuple[Any, dict, dict]:
    controller.mode = "capture"
    controller.positions = [len(tokens["raw"][view]) + distance - 1 for distance in (4, 8)]
    controller.captured_states, controller.captured_kv = {}, {}
    hidden = forward(tokens["sequences"][carrier][view], 1, stage)
    states, kv = controller.captured_states, controller.captured_kv
    controller.mode = "idle"
    require(set(states) == set(historical.ANCHORS), "Missing reset capture layers")
    require(set(kv) == set(BLOCKS), "Missing donor capture layers")
    return hidden, states, kv


def _same_captures(torch: Any, expected: dict, actual: dict, label: str) -> None:
    require(expected.keys() == actual.keys(), f"{label} capture keys changed")
    for key, value in expected.items():
        other = actual[key]
        if isinstance(value, tuple):
            require(all(torch.equal(a, b) for a, b in zip(value, other, strict=True)),
                    f"{label} capture differs at block {key}")
        else:
            require(torch.equal(value, other), f"{label} capture differs at block {key}")


def _patch(torch: Any, controller: Any, ids: list[int], rows: list[dict],
           resets: dict, donors: list[dict], forward: Any, stage: str) -> tuple[Any, Any]:
    controller.mode, controller.rows = "patch", rows
    controller.resets, controller.donor_kv = resets, donors
    controller.neutral_path = False
    active = forward(ids, len(rows), stage + "_active")
    controller.neutral_path = True
    neutral = forward(ids, len(rows), stage + "_neutral")
    controller.neutral_path, controller.mode = False, "idle"
    for index, row in enumerate(rows):
        if row["condition"] in ("intact", "reset", "no_op", "reset_roundtrip") or row.get("operation") == "none":
            require(torch.equal(active[index], neutral[index]),
                    f"Same-slot no-op/roundtrip failed at row {index}")
    return active, neutral


def _readouts(torch: Any, hidden: Any, rows: list[dict]) -> np.ndarray:
    positions = torch.tensor([row["position"] for row in rows], dtype=torch.long)
    return hidden[torch.arange(len(rows)), positions].float().numpy().copy()


def _diagnostic_arrays(diagnostics: list[dict], rows: list[dict], length: int) -> dict[str, np.ndarray]:
    expected = {(neutral, block, row) for neutral in (False, True)
                for block in BLOCKS for row in range(len(rows))}
    observed = {}
    for entry in diagnostics:
        key = (entry["neutral_path"], entry["block"], entry["row"])
        require(key not in observed, "Duplicate attention diagnostic")
        observed[key] = entry
    require(observed.keys() == expected, "Incomplete extension attention diagnostics")
    ordered = [observed[key] for key in sorted(expected)]
    result = {}
    for field in ("weights", "baseline_weights"):
        values = np.stack([entry[field].float().numpy() for entry in ordered])
        result[field] = values.reshape(2, len(BLOCKS), len(rows), *values.shape[1:])
    selected = np.zeros((len(ordered), length), dtype=np.bool_)
    glyph = np.zeros_like(selected)
    suffix = np.zeros_like(selected)
    for index, entry in enumerate(ordered):
        selected[index, list(entry["selected_positions"])] = True
        row = rows[entry["row"]]
        groups = historical.position_groups(row["glyph_length"], row["distance"])
        glyph[index, list(groups["glyph"])] = True
        suffix[index, list(groups["suffix"])] = True
    result["selected_mask"] = selected.reshape(2, len(BLOCKS), len(rows), length)
    for label, mask in (("selected", selected), ("glyph", glyph), ("suffix", suffix)):
        shaped = mask.reshape(2, len(BLOCKS), len(rows), length)
        result[label + "_mass"] = (result["weights"] * shaped[..., None, :]).sum(axis=-1, dtype=np.float32)
    return result


def run_item(torch: Any, model: Any, tokens: dict,
             donor_tokens: list[dict]) -> dict[str, Any]:
    """Run real or tiny CPU engineering inputs, returning arrays and checks.

    Tiny test models may use FP32. The production CLI separately enforces the
    pinned model manifest, dimensions, versions, CPU BF16, and eager attention.
    Full hidden states are compared; persisted legacy/extension arrays contain
    the corresponding per-row readouts. No lexical outcome is calculated.
    """
    _validate_tokens(tokens, donor_tokens)
    require(not model.training, "Evaluation mode is required")
    require(len(model.model.layers) == 28, "A 28-layer Llama model is required")
    require(all(parameter.device.type == "cpu" for parameter in model.parameters()),
            "CPU parameters are required")
    require(model.config._attn_implementation == "eager", "Eager attention is required")
    started = time.perf_counter()
    arrays: dict[str, np.ndarray] = {}
    timings: dict[str, float] = {}
    calls, sequences, off_target = 0, 0, 0

    def forward(ids: list[int], batch: int, stage: str) -> Any:
        nonlocal calls, sequences
        _progress(stage, status="starting", batch=batch)
        before = time.perf_counter()
        inputs = torch.tensor([ids], device="cpu", dtype=torch.long).repeat(batch, 1)
        with torch.inference_mode():
            hidden = model.model(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                                 use_cache=False, return_dict=True).last_hidden_state.detach()
        require(bool(torch.isfinite(hidden).all()), "Nonfinite final hidden states")
        calls += 1
        sequences += batch
        timings[stage] = time.perf_counter() - before
        _progress(stage, status="complete", elapsed_seconds=timings[stage], peak_rss_bytes=_peak_rss_bytes())
        return hidden

    length = len(tokens["raw"]["glyph"])
    old_rows, new_rows = legacy_rows(length), extension_rows(length)
    require(len(old_rows) == 88 and len(new_rows) == 16, "Batch geometry changed")
    for carrier in CARRIERS:
        ids = tokens["sequences"][carrier]["glyph"]
        stock = forward(ids, 1, f"{carrier}_stock")
        arrays[f"{carrier}_stock_hidden"] = stock[0].float().numpy().copy()
        old = historical.AttentionPath(model.model.layers)
        try:
            idle = forward(ids, 1, f"{carrier}_historical_idle")
            require(torch.equal(stock, idle), "Historical adapter stock parity failed")
            donor_kv = []
            for index, donor in enumerate(donor_tokens):
                _, _, kv = _capture(torch, model, old, donor, carrier, "glyph", forward,
                                    f"{carrier}_historical_donor_{index}")
                donor_kv.append(kv)
            reset_hidden, resets, _ = _capture(torch, model, old, tokens, carrier, "codepoint_literal", forward,
                                             f"{carrier}_historical_reset_capture")
            arrays[f"{carrier}_codepoint_hidden"] = reset_hidden[0].float().numpy().copy()
            arrays[f"{carrier}_reset_states"] = np.stack([resets[anchor].float().numpy() for anchor in historical.ANCHORS])
            for component, label in enumerate(("keys", "values")):
                arrays[f"{carrier}_donor_{label}"] = np.stack([
                    np.stack([kv[block][component].float().numpy() for block in BLOCKS])
                    for kv in donor_kv
                ])
            legacy, legacy_neutral = _patch(torch, old, ids, old_rows, resets, donor_kv,
                                            forward, f"{carrier}_historical_legacy")
            off_target += old.offtarget_checks
        finally:
            old.close()
        new = t22.AttentionPath(model.model.layers, record_attention=False)
        try:
            idle = forward(ids, 1, f"{carrier}_t22_idle")
            require(torch.equal(stock, idle), "T22 adapter stock parity failed")
            new_donors = []
            for index, donor in enumerate(donor_tokens):
                _, _, kv = _capture(torch, model, new, donor, carrier, "glyph", forward,
                                    f"{carrier}_t22_donor_{index}")
                _same_captures(torch, donor_kv[index], kv, "Donor K/V")
                new_donors.append(kv)
            _, new_resets, _ = _capture(torch, model, new, tokens, carrier, "codepoint_literal", forward,
                                       f"{carrier}_t22_reset_capture")
            _same_captures(torch, resets, new_resets, "Codepoint reset")
            joint, joint_neutral = _patch(torch, new, ids, old_rows, new_resets, new_donors,
                                          forward, f"{carrier}_t22_legacy")
            require(torch.equal(legacy, joint), "CPU legacy KV full-state equality failed")
            require(torch.equal(legacy_neutral, joint_neutral), "CPU legacy neutral full-state equality failed")
            for label, value in (("historical", legacy), ("historical_neutral", legacy_neutral),
                                 ("t22", joint), ("t22_neutral", joint_neutral)):
                arrays[f"{carrier}_legacy_{label}"] = _readouts(torch, value, old_rows)
            new.record_attention = True
            new.diagnostics.clear()
            extension, extension_neutral = _patch(torch, new, ids, new_rows, new_resets, new_donors,
                                                forward, f"{carrier}_extension")
            arrays[f"{carrier}_extension"] = _readouts(torch, extension, new_rows)
            arrays[f"{carrier}_extension_neutral"] = _readouts(torch, extension_neutral, new_rows)
            for label, value in _diagnostic_arrays(new.diagnostics, new_rows, len(ids)).items():
                arrays[f"{carrier}_attention_{label}"] = value
            off_target += new.offtarget_checks
        finally:
            new.close()
    for name, value in arrays.items():
        require(value.dtype in (np.dtype("float32"), np.dtype("bool")), f"Unexpected dtype: {name}")
        require(bool(np.isfinite(value).all()), f"Nonfinite saved array: {name}")
    return {
        "arrays": arrays,
        "checks": {name: True for name in ENGINEERING_CHECKS},
        "timing_seconds": {**timings, "total": time.perf_counter() - started},
        "forward_calls": calls, "sequence_forwards": sequences,
        "offtarget_attention_checks": off_target,
        "peak_rss_bytes": _peak_rss_bytes(),
    }


def exposed_inputs() -> dict[str, Any]:
    """Audit static receipts and return only the already exposed eight inputs."""
    pilot = historical.audit_spec(ROOT / historical.SPEC)
    exposed = historical.read_json(t22.CANARY_SPEC)
    require(exposed["target_count"] == 8 and exposed["source_count"] == 128,
            "Exposed canary counts changed")
    require(exposed["target_tokens"] == pilot["target_tokens"][:8]
            and exposed["source_tokens"] == pilot["source_tokens"]
            and exposed["donor_indices"] == pilot["donor_indices"][:8],
            "Inputs differ from the original exposed canary")
    require(exposed["model_artifact"] == pilot["model_artifact"], "Model pin differs")
    require(pilot["model_artifact"]["file_count"] == 9, "Expected nine model artifact files")
    return exposed


def source_hashes() -> dict[str, str]:
    paths = (Path(__file__), ROOT / "scripts/t22_kv_dissection_v0.py",
             ROOT / "scripts/t21_glyph_context_path_pilot_v0.py",
             ROOT / "tests/test_t22_kv_cpu_canary_v0.py",
             ROOT / "src/glyphprobe/provenance.py", ROOT / historical.SPEC,
             t22.CANARY_SPEC, ROOT / historical.CONFIG)
    return {path.relative_to(ROOT).as_posix(): historical.sha256(path) for path in paths}


def _runtime(torch: Any, transformers: Any, threads: int) -> dict[str, Any]:
    from transformers.models.llama.modeling_llama import LlamaAttention

    require(torch.__version__ == REQUIRED_TORCH, "CPU Torch version mismatch")
    require(transformers.__version__ == REQUIRED_TRANSFORMERS, "Transformers version mismatch")
    require(type(threads) is int and threads > 0, "Threads must be a positive integer")
    torch.set_num_threads(threads)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        require(torch.get_num_interop_threads() == 1, "Cannot pin interop threads after parallel work")
    return {"torch": torch.__version__, "transformers": transformers.__version__,
            "python": sys.version, "device": "cpu", "dtype": "bfloat16", "attention": "eager",
            "threads": torch.get_num_threads(), "interop_threads": torch.get_num_interop_threads(),
            "platform": platform.platform(), "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
            "llama_attention_source_sha256": hashlib.sha256(inspect.getsource(LlamaAttention.forward).encode()).hexdigest()}


def _validate_model_artifact(model_path: Path, exposed: dict) -> dict:
    from glyphprobe.provenance import model_artifact_receipt

    actual = model_artifact_receipt(model_path)
    require(actual == exposed["model_artifact"], "Exact nine-file model manifest mismatch")
    return actual


def _specification(exposed: dict, artifact: dict, runtime: dict, items: int) -> dict:
    require(items in (1, 8), "Only the fixed first-item pilot or eight-item canary is permitted")
    return {"protocol_id": PROTOCOL, "stage": "cpu_engineering_timing_pilot" if items == 1 else "cpu_engineering_canary",
            "target_count": items, "eligible_target_count": 8,
            "target_tokens": exposed["target_tokens"][:items],
            "donor_indices": exposed["donor_indices"][:items],
            "source_tokens": exposed["source_tokens"], "model_artifact": artifact,
            "runtime": runtime, "source_sha256": source_hashes(),
            "model_dimensions": MODEL_DIMENSIONS,
            "carriers": list(CARRIERS), "legacy_rows": "original_88_rows_unchanged",
            "extension_rows": "operation_then_position_then_donor_16_rows_separate_batch",
            "anchor": 21, "distance": 8, "active_blocks": list(BLOCKS),
            "attention_diagnostics_axes": ["active_then_neutral", "block_22_through_27", "extension_row", "head", "position_if_weights"],
            "attention_mass_accumulation": "float32_from_recorded_actual_weights",
            "scientific_result": False, "historical_gpu_replay": False,
            "historical_gpu_acquisition_gate_changed": False,
            "gallery_acquired": False, "lexical_effect_estimated": False,
            "efficacy_screen": False, "protected_bank_reads": 0,
            "generation_calls": 0, "seed": 2026092100}


def _array_schema(tokens: dict, dimensions: dict) -> dict[str, dict]:
    length = len(tokens["raw"]["glyph"]) + 8
    codepoint_length = len(tokens["raw"]["codepoint_literal"]) + 8
    width, heads = dimensions["hidden_size"], dimensions["attention_heads"]
    shapes = {"stock_hidden": [length, width], "codepoint_hidden": [codepoint_length, width],
              "reset_states": [2, 2, width],
              "donor_keys": [2, 6, dimensions["kv_heads"], length, dimensions["head_dim"]],
              "donor_values": [2, 6, dimensions["kv_heads"], length, dimensions["head_dim"]],
              "extension": [16, width], "extension_neutral": [16, width],
              "attention_weights": [2, 6, 16, heads, length],
              "attention_baseline_weights": [2, 6, 16, heads, length],
              "attention_selected_mask": [2, 6, 16, length]}
    for label in ("historical", "historical_neutral", "t22", "t22_neutral"):
        shapes[f"legacy_{label}"] = [88, width]
    for label in ("selected_mass", "glyph_mass", "suffix_mass"):
        shapes[f"attention_{label}"] = [2, 6, 16, heads]
    return {f"{carrier}_{name}": {"shape": shape, "dtype": "bool" if name == "attention_selected_mask" else "float32"}
            for carrier in CARRIERS for name, shape in shapes.items()}


def verify_item(path: Path, specification_hash: str, item_index: int) -> dict:
    specification_path = path.parent / "specification.json"
    require(historical.sha256(specification_path) == specification_hash, "Parent specification hash changed")
    specification = historical.read_json(specification_path)
    require(specification["protocol_id"] == PROTOCOL
            and 0 <= item_index < specification["target_count"], "Invalid item specification identity")
    tokens = specification["target_tokens"][item_index]
    expected_arrays = _array_schema(tokens, specification["model_dimensions"])
    receipt = historical.read_json(path / "receipt.json")
    require(receipt["protocol_id"] == PROTOCOL and receipt["item_index"] == item_index,
            "Stored item identity changed")
    require(receipt["specification_sha256"] == specification_hash, "Stored item specification changed")
    require(historical.sha256(path / "states.npz") == receipt["states_sha256"], "Stored item arrays changed")
    require(set(receipt["checks"]) == set(ENGINEERING_CHECKS)
            and all(value is True for value in receipt["checks"].values()),
            "Stored item engineering checks incomplete")
    require(receipt["scientific_result"] is False and receipt["historical_gpu_replay"] is False
            and receipt["protected_bank_reads"] == 0 and receipt["generation_calls"] == 0,
            "Stored item claim boundary changed")
    require(receipt["arrays"] == expected_arrays, "Stored array schema differs from the specified row geometry")
    with np.load(path / "states.npz", allow_pickle=False) as arrays:
        require(set(arrays.files) == set(receipt["arrays"]), "Stored array names changed")
        for name, metadata in receipt["arrays"].items():
            value = arrays[name]
            require(list(value.shape) == metadata["shape"] and str(value.dtype) == metadata["dtype"],
                    f"Stored array shape/dtype changed: {name}")
            require(bool(np.isfinite(value).all()), f"Nonfinite stored array: {name}")
        for carrier in CARRIERS:
            require(np.array_equal(arrays[f"{carrier}_legacy_historical"], arrays[f"{carrier}_legacy_t22"])
                    and np.array_equal(arrays[f"{carrier}_legacy_historical_neutral"], arrays[f"{carrier}_legacy_t22_neutral"]),
                    "Stored same-CPU legacy outputs disagree")
            weights = arrays[f"{carrier}_attention_weights"]
            baseline = arrays[f"{carrier}_attention_baseline_weights"]
            require(np.array_equal(weights[1], baseline[1]), "Stored neutral attention differs from its baseline")
            mask = arrays[f"{carrier}_attention_selected_mask"]
            expected_mask = np.zeros(mask.shape, dtype=np.bool_)
            for index, row in enumerate(extension_rows(len(tokens["raw"]["glyph"]))):
                positions = historical.foreign_positions(row["condition"], row["glyph_length"], row["distance"])
                expected_mask[0, :, index, list(positions)] = True
                if row["operation"] in ("none", "v"):
                    require(np.array_equal(weights[0, :, index], baseline[0, :, index]),
                            "Stored local V/reference attention changed")
                if row["operation"] == "none":
                    require(np.array_equal(arrays[f"{carrier}_extension"][index], arrays[f"{carrier}_extension_neutral"][index]),
                            "Stored reference operation is not a no-op")
            require(np.array_equal(mask, expected_mask), "Stored intervention positions differ from the specification")
            positions = historical.position_groups(len(tokens["raw"]["glyph"]), 8)
            for label in ("selected", "glyph", "suffix"):
                mass_mask = mask if label == "selected" else np.zeros_like(mask)
                if label != "selected":
                    mass_mask[..., list(positions[label])] = True
                mass = (weights * mass_mask[..., None, :]).sum(axis=-1, dtype=np.float32)
                require(np.array_equal(mass, arrays[f"{carrier}_attention_{label}_mass"]),
                        f"Stored {label} mass differs from actual attention weights")
    return receipt


def _check_sources(specification: dict) -> None:
    require(source_hashes() == specification["source_sha256"], "Bound source changed during acquisition")


def run(model_path: Path, output: Path, *, items: int = 1, threads: int = 4,
        resume: bool = False) -> dict[str, Any]:
    require(items in (1, 8), "Only the fixed first-item pilot or eight-item canary is permitted")
    require(type(threads) is int and threads > 0, "Threads must be a positive integer")
    require(not output.resolve().is_relative_to(model_path.resolve()), "Outputs must be outside the immutable model snapshot")
    if output.exists() and not resume:
        raise FileExistsError(f"Output exists: {output}; choose an unused path or explicit --resume")
    if resume:
        require(output.is_dir(), "Resume output is missing")
        require(not (output / "acquisition_receipt.json").exists(), "Completed runs cannot be resumed or expanded")
    import torch
    import transformers
    from transformers import AutoModelForCausalLM

    started = time.perf_counter()
    exposed = exposed_inputs()
    runtime = _runtime(torch, transformers, threads)
    _progress("model_manifest", status="starting")
    artifact = _validate_model_artifact(model_path, exposed)
    _progress("model_manifest", status="complete", bytes=artifact["total_bytes"])
    specification = _specification(exposed, artifact, runtime, items)
    specification_path = output / "specification.json"
    if resume:
        require(historical.read_json(specification_path) == specification, "Resume requires identical inputs/code/model/runtime")
    else:
        output.mkdir(parents=True, exist_ok=False)
        historical.write_json(specification_path, specification)
    specification_hash = historical.sha256(specification_path)
    existing = {}
    for index in range(items):
        destination = output / f"item_{index:04d}"
        if destination.exists():
            existing[index] = verify_item(destination, specification_hash, index)
    torch.manual_seed(specification["seed"])
    _progress("model_load", status="starting", device="cpu", dtype="bfloat16")
    load_started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
                                               trust_remote_code=False, dtype=torch.bfloat16,
                                               attn_implementation="eager").to("cpu").eval()
    expected = historical.config()["model"]
    require(type(model).__name__ == "LlamaForCausalLM", "Unexpected model class")
    require(len(model.model.layers) == expected["layers"]
            and model.config.hidden_size == expected["hidden_size"]
            and sum(parameter.numel() for parameter in model.parameters()) == expected["parameters"],
            "Model architecture/parameter count mismatch")
    require(_model_dimensions(model) == specification["model_dimensions"],
            "Model attention geometry mismatch")
    require({parameter.dtype for parameter in model.parameters()} == {torch.bfloat16}, "All model parameters must be BF16")
    load_seconds = time.perf_counter() - load_started
    _progress("model_load", status="complete", elapsed_seconds=load_seconds, peak_rss_bytes=_peak_rss_bytes())
    chunk_hashes, item_receipts = {}, []
    try:
        for index, tokens in enumerate(specification["target_tokens"]):
            _check_sources(specification)
            destination = output / f"item_{index:04d}"
            if index in existing:
                receipt = existing[index]
                _progress("item", item=index, status="validated_existing")
            else:
                _progress("item", item=index, status="starting", total=items)
                donors = [specification["source_tokens"][donor]
                          for donor in specification["donor_indices"][index]]
                result = run_item(torch, model, tokens, donors)
                _check_sources(specification)
                partial = output / f".item_{index:04d}.partial-{uuid.uuid4().hex}"
                partial.mkdir()
                np.savez_compressed(partial / "states.npz", **result["arrays"])
                receipt = {"protocol_id": PROTOCOL, "item_index": index,
                           "specification_sha256": specification_hash,
                           "states_sha256": historical.sha256(partial / "states.npz"),
                           "arrays": {name: {"shape": list(value.shape), "dtype": str(value.dtype)}
                                      for name, value in result.pop("arrays").items()},
                           **result, "completed_at_utc": historical.now(),
                           "scientific_result": False, "historical_gpu_replay": False,
                           "protected_bank_reads": 0, "generation_calls": 0}
                historical.write_json(partial / "receipt.json", receipt)
                verify_item(partial, specification_hash, index)
                require(not destination.exists(), "Item destination appeared concurrently")
                partial.rename(destination)
                _progress("item", item=index, status="complete", elapsed_seconds=receipt["timing_seconds"]["total"])
            chunk_hashes[destination.name] = historical.sha256(destination / "receipt.json")
            item_receipts.append(receipt)
        _check_sources(specification)
        require(_validate_model_artifact(model_path, exposed) == artifact,
                "Model files changed during acquisition")
        acquisition = {"protocol_id": PROTOCOL,
                       "status": "cpu_engineering_timing_pilot_complete" if items == 1 else "cpu_engineering_canary_complete",
                       "specification_sha256": specification_hash, "target_items": items,
                       "chunks": chunk_hashes, "runtime": runtime, "model_artifact": artifact,
                       "checks": {name: all(receipt["checks"][name] for receipt in item_receipts)
                                  for name in item_receipts[0]["checks"]},
                       "forward_calls_across_items": sum(receipt["forward_calls"] for receipt in item_receipts),
                       "sequence_forwards_across_items": sum(receipt["sequence_forwards"] for receipt in item_receipts),
                       "model_load_seconds_this_invocation": load_seconds,
                       "elapsed_seconds_this_invocation": time.perf_counter() - started,
                       "peak_rss_bytes_this_invocation": _peak_rss_bytes(),
                       "scientific_result": False, "historical_gpu_replay": False,
                       "historical_gpu_acquisition_gate_changed": False,
                       "lexical_effect_estimated": False, "gallery_acquired": False,
                       "efficacy_screen": False, "protected_bank_reads": 0,
                       "generation_calls": 0, "completed_at_utc": historical.now()}
        historical.write_json(output / "acquisition_receipt.json", acquisition)
        return {"status": acquisition["status"], "target_items": items,
                "acquisition_receipt_sha256": historical.sha256(output / "acquisition_receipt.json"),
                "scientific_result": False, "historical_gpu_replay": False}
    finally:
        del model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("run", help="CPU engineering only; no historical GPU replay or effect estimate")
    acquire.add_argument("--model-path", type=Path, required=True)
    acquire.add_argument("--output", type=Path, required=True)
    acquire.add_argument("--items", type=int, choices=(1, 8), default=1)
    acquire.add_argument("--threads", type=int, default=4)
    acquire.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.model_path, args.output, items=args.items,
                         threads=args.threads, resume=args.resume), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
