#!/usr/bin/env python3
"""Freeze and run the T16 joint late-band causal mediation test."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
import hashlib
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

import emoji_steering_causal_path_v0 as t14  # noqa: E402
import emoji_steering_specificity_harvest_v0 as t13  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


PROTOCOL_ID = "glyphprobe-t16-distributed-late-band-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/t16_distributed_late_band_v0.yaml")
FREEZE_PATH = Path("data/manifests/t16_distributed_late_band_v0.json")
VALIDATION_DIRECTORY = Path("validation/t16_distributed_late_band_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
MODEL_ROLE = "llama32_3b_base_bf16"
TARGET_GROUPS = t14._TARGET_GROUPS
STATIC_ASSETS = (
    "configs/t16_distributed_late_band_v0.yaml",
    "docs/T16_DISTRIBUTED_LATE_BAND_V0.md",
    "docs/T16_DISTRIBUTED_LATE_BAND_V0.ja.md",
    "scripts/t16_distributed_late_band_v0.py",
    "tests/test_t16_distributed_late_band_v0.py",
    "validation/t16_distributed_late_band_v0/design_preflight.json",
)


class DistributedPathError(RuntimeError):
    """Raised when the T16 distributed-path contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DistributedPathError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
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
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-DP config changed")
    return value


def _joint_sites() -> tuple[tuple[str, int], ...]:
    return tuple(
        (str(row["site"]), int(row["block_index"]))
        for row in _config()["joint_mediator_band"]["ordered_sites"]
    )


def _bound_hashes() -> dict[str, str]:
    observed: dict[str, str] = {}
    for key in ("t14_config", "t14_freeze", "t14_selected_site", "t14_closeout"):
        binding = _config()["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T16-DP bound input missing: {key}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T16-DP bound input changed: {key}")
        observed[key] = actual
    return observed


def audit_design() -> dict[str, Any]:
    config = _config()
    observed = _bound_hashes()
    expected_sites = tuple(
        (site, block)
        for block in range(24, 28)
        for site in ("attn_out", "mlp_out")
    )
    _require(_joint_sites() == expected_sites, "Joint late-band roster changed")
    _require(config["fixed_model"]["role"] == MODEL_ROLE, "T16-DP model changed")
    _require(int(config["treatment"]["injection_block_index"]) == 23, "Injection block changed")
    _require(float(config["treatment"]["magnitude"]) == 0.25, "Magnitude changed")
    _require(int(config["treatment"]["signed_conditions_per_target"]) == 80, "Condition count changed")
    _require(int(config["fresh_target_bank"]["rows"]) == 192, "Target count changed")
    _require(config["fresh_target_bank"]["status_at_design_freeze"] == "not_generated", "Target status changed")
    closeout = _read_json(_root() / str(config["source_bindings"]["t14_closeout"]["path"]))
    _require(closeout.get("status") == config["source_bindings"]["t14_closeout"]["expected_status"], "T14 closeout changed")
    selected = _read_json(_root() / str(config["source_bindings"]["t14_selected_site"]["path"]))
    _require(selected["control_evidence"]["upstream_sham_pass"] is True, "Bound upstream sham changed")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t16dp_model_forwards",
        "bound_inputs": observed,
        "model_role": MODEL_ROLE,
        "joint_sites": [{"site": site, "block_index": block} for site, block in _joint_sites()],
        "target_rows_planned": 192,
        "response_rows_planned": 15360,
        "target_bank_generated": False,
        "model_forwards": 0,
        "unique_minimal_or_complete_circuit_claim_authorized": False,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    result = audit_design()
    _write_json(output, result)
    return result


def freeze(output: Path) -> dict[str, Any]:
    design = audit_design()
    assets: dict[str, str] = {}
    for relative in STATIC_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T16-DP frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t16dp_model_forwards",
        "assets": assets,
        "joint_sites": design["joint_sites"],
        "target_rows_planned": 192,
        "response_rows_planned": 15360,
        "target_bank_generated_at_freeze": False,
        "model_forwards_at_freeze": 0,
        "unique_minimal_or_complete_circuit_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def audit_freeze() -> dict[str, Any]:
    design = audit_design()
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16-DP freeze protocol changed")
    _require(value.get("status") == "final_execution_freeze_zero_t16dp_model_forwards", "T16-DP freeze incomplete")
    _require(value.get("joint_sites") == design["joint_sites"], "Frozen joint sites changed")
    for relative, expected in value["assets"].items():
        asset = _root() / relative
        _require(asset.is_file() and _sha256(asset) == expected, f"T16-DP frozen asset changed: {relative}")
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path)}


def _git_value(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    _require(completed.returncode == 0, f"Git gate failed: {' '.join(arguments)}")
    return completed.stdout.strip()


def _pushed_freeze_gate() -> dict[str, str]:
    protected = (*STATIC_ASSETS, FREEZE_PATH.as_posix())
    _require(not _git_value("status", "--porcelain", "--", *protected), "T16-DP protected files are not committed")
    head = _git_value("rev-parse", "HEAD")
    upstream = _git_value("rev-parse", "@{u}")
    _require(head == upstream, "T16-DP freeze commit is not pushed to its upstream")
    return {"head_commit": head, "upstream_commit": upstream}


def _validate_targets(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    result = [
        {"id": str(row.get("id", "")), "group": str(row.get("group", "")), "prompt": str(row.get("prompt", ""))}
        for row in rows
    ]
    _require(len(result) == 192, "T16-DP target count changed")
    _require(len({row["id"] for row in result}) == 192, "T16-DP target IDs changed")
    _require(len({row["prompt"] for row in result}) == 192, "T16-DP target prompts changed")
    _require(set(row["group"] for row in result) == set(TARGET_GROUPS), "T16-DP target strata changed")
    _require(all(sum(row["group"] == group for row in result) == 16 for group in TARGET_GROUPS), "T16-DP target balance changed")
    _require(all(row["id"].startswith("t16dp_") for row in result), "T16-DP target namespace changed")
    return result


def materialize_bank(output: Path, receipt_output: Path) -> dict[str, Any]:
    audit_freeze()
    git = _pushed_freeze_gate()
    _require(not output.exists() and not receipt_output.exists(), "T16-DP target output exists")
    seed = int(_config()["fresh_target_bank"]["generator_seed"])
    generated = t14.build_target_rows(seed)
    rows = _validate_targets(
        [
            {"id": str(row["id"]).replace("c1v2_", "t16dp_", 1), "group": row["group"], "prompt": row["prompt"]}
            for row in generated
        ]
    )
    retired_seed = int(_config()["fresh_target_bank"]["retired_t14_c1_v2_generator_seed"])
    retired_prompts = {row["prompt"] for row in t14.build_target_rows(retired_seed)}
    public_prompts = {row["prompt"] for row in t14._public_targets()}
    _require(not ({row["prompt"] for row in rows} & retired_prompts), "T16-DP overlaps T14 C1 v2")
    _require(not ({row["prompt"] for row in rows} & public_prompts), "T16-DP overlaps public targets")
    _write_jsonl(output, rows)
    counts = {group: sum(row["group"] == group for row in rows) for group in TARGET_GROUPS}
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "fresh_target_bank_materialized_after_pushed_freeze",
        "target_bank_path": str(output.resolve()),
        "target_bank_sha256": _sha256(output),
        "target_rows": len(rows),
        "stratum_counts": counts,
        "generator_seed": seed,
        "retired_t14_exact_prompt_overlap": 0,
        "public_exact_prompt_overlap": 0,
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        **git,
        "prompt_bodies_printed": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(receipt_output, receipt)
    return {
        "status": receipt["status"],
        "target_rows": len(rows),
        "stratum_counts": counts,
        "target_bank_sha256": receipt["target_bank_sha256"],
        "receipt_sha256": _sha256(receipt_output),
        "prompt_bodies_printed": False,
    }


def _load_bank(target_bank: Path, target_receipt: Path) -> list[dict[str, str]]:
    receipt = _read_json(target_receipt)
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "T16-DP target receipt changed")
    _require(receipt.get("status") == "fresh_target_bank_materialized_after_pushed_freeze", "T16-DP target bank not admitted")
    _require(Path(str(receipt["target_bank_path"])).resolve() == target_bank.resolve(), "T16-DP target path changed")
    _require(_sha256(target_bank) == receipt["target_bank_sha256"], "T16-DP target bank changed")
    _require(receipt["freeze_manifest_sha256"] == _sha256(_root() / FREEZE_PATH), "T16-DP target freeze changed")
    return _validate_targets(_read_jsonl(target_bank))


def _yield_if_contended(output_root: Path, boundary: str) -> None:
    pids = t13._foreign_gpu_pids()
    if not pids:
        return
    receipt = output_root / "yield_receipt.json"
    if not receipt.exists():
        _write_json(
            receipt,
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "status": "yielded_for_foreign_gpu_contention",
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"]))


def _joint_modules(blocks: Sequence[Any]) -> list[tuple[Any, bool, str, int]]:
    result = []
    for site, block_index in _joint_sites():
        module, is_pre = t14._site_module(blocks, site, block_index)
        result.append((module, is_pre, site, block_index))
    return result


def _joint_forward(
    *,
    torch: Any,
    model: Any,
    input_ids: Any,
    attention_mask: Any,
    injection_block: Any,
    injection_vectors: Any | None,
    mediators: Sequence[tuple[Any, bool, str, int]],
    replacements: Sequence[Any] | None,
    capture: bool,
) -> tuple[Any, list[Any] | None]:
    handles: list[Any] = []
    captured: dict[int, Any] = {}
    if injection_vectors is not None:

        def injection_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            raw, rebuild = t14._tensor_from_output(output)
            changed = raw.clone()
            changed[:, -1, :] = changed[:, -1, :] + injection_vectors.to(device=raw.device, dtype=raw.dtype)
            return rebuild(changed)

        handles.append(injection_block.register_forward_hook(injection_hook))

    for index, (module, is_pre, _site, _block) in enumerate(mediators):
        replacement = None if replacements is None else replacements[index]
        if is_pre:

            def pre_hook(_module: Any, inputs: tuple[Any, ...], *, index: int = index, replacement: Any = replacement) -> Any:
                raw, rebuild = t14._tensor_from_input(inputs)
                if capture:
                    captured[index] = raw[:, -1, :].detach().clone()
                if replacement is None:
                    return None
                changed = raw.clone()
                changed[:, -1, :] = replacement.to(device=raw.device, dtype=raw.dtype)
                return rebuild(changed)

            handles.append(module.register_forward_pre_hook(pre_hook))
        else:

            def post_hook(_module: Any, _inputs: Any, output: Any, *, index: int = index, replacement: Any = replacement) -> Any:
                raw, rebuild = t14._tensor_from_output(output)
                if capture:
                    captured[index] = raw[:, -1, :].detach().clone()
                if replacement is None:
                    return output
                changed = raw.clone()
                changed[:, -1, :] = replacement.to(device=raw.device, dtype=raw.dtype)
                return rebuild(changed)

            handles.append(module.register_forward_hook(post_hook))
    try:
        with torch.inference_mode():
            output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, return_dict=True)
    finally:
        for handle in handles:
            handle.remove()
    values = None
    if capture:
        _require(set(captured) == set(range(len(mediators))), "Joint mediator capture incomplete")
        values = [captured[index] for index in range(len(mediators))]
    return output.logits[:, -1, :].detach().float(), values


def _causal_patch_batch(
    *,
    torch: Any,
    model: Any,
    input_ids_single: Any,
    attention_mask_single: Any,
    blocks: Sequence[Any],
    unit_vectors: np.ndarray,
    target_rms: float,
) -> dict[str, np.ndarray]:
    magnitude = float(_config()["treatment"]["magnitude"])
    scaled = unit_vectors.astype(np.float32) * np.float32(target_rms * magnitude)
    all_vectors = np.concatenate((np.zeros((2, scaled.shape[1]), dtype=np.float32), scaled), axis=0)
    device = next(model.parameters()).device
    vectors = torch.tensor(all_vectors, dtype=torch.float32, device=device)
    count = len(all_vectors)
    input_ids = input_ids_single.repeat(count, 1)
    attention_mask = attention_mask_single.repeat(count, 1)
    injection_block = blocks[int(_config()["treatment"]["injection_block_index"])]
    mediators = _joint_modules(blocks)
    treatment_logits, captured = _joint_forward(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vectors,
        mediators=mediators,
        replacements=None,
        capture=True,
    )
    _require(captured is not None and len(captured) == 8, "Joint capture changed")
    baseline = [value[:1].expand_as(value) for value in captured]
    necessity_logits, _ = _joint_forward(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vectors,
        mediators=mediators,
        replacements=baseline,
        capture=False,
    )
    sufficiency_logits, _ = _joint_forward(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=None,
        mediators=mediators,
        replacements=captured,
        capture=False,
    )
    restoration_logits, _ = _joint_forward(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vectors,
        mediators=mediators,
        replacements=captured,
        capture=False,
    )
    result = {
        "baseline": treatment_logits[:1].cpu().numpy(),
        "zero": treatment_logits[1:2].cpu().numpy(),
        "treatment": treatment_logits[2:].cpu().numpy(),
        "necessity": necessity_logits[2:].cpu().numpy(),
        "sufficiency": sufficiency_logits[2:].cpu().numpy(),
        "restoration": restoration_logits[2:].cpu().numpy(),
    }
    _require(all(np.isfinite(value).all() for value in result.values()), "Joint patch nonfinite")
    return result


def _append_rows(
    rows: list[dict[str, Any]],
    target_index: int,
    target: Mapping[str, str],
    metadata: Sequence[Mapping[str, Any]],
    result: Mapping[str, np.ndarray],
) -> tuple[float, float, float]:
    treatment = t14._scalar_metrics(result["baseline"], result["treatment"])
    necessity = t14._scalar_metrics(result["baseline"], result["necessity"])
    sufficiency = t14._scalar_metrics(result["baseline"], result["sufficiency"])
    restoration = t14._scalar_metrics(result["treatment"], result["restoration"])
    zero = t14._scalar_metrics(result["baseline"], result["zero"])
    for index, condition in enumerate(metadata):
        rows.append(
            {
                **dict(condition),
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "target_index": target_index,
                "target_id": target["id"],
                "target_group": target["group"],
                "treatment_js": float(treatment["js"][index]),
                "treatment_kl": float(treatment["kl"][index]),
                "treatment_tv": float(treatment["tv"][index]),
                "treatment_logit_rms": float(treatment["logit_rms"][index]),
                "necessity_js": float(necessity["js"][index]),
                "necessity_drop_js": float(treatment["js"][index] - necessity["js"][index]),
                "sufficiency_js": float(sufficiency["js"][index]),
                "restoration_error_js": float(restoration["js"][index]),
                "restoration_error_logit_rms": float(restoration["logit_rms"][index]),
            }
        )
    return float(np.max(restoration["js"])), float(np.max(restoration["logit_rms"])), float(np.max(np.abs(zero["js"])))


def run(
    *,
    output_root: Path,
    source_run_root: Path,
    preflight_directory: Path,
    target_bank: Path,
    target_receipt: Path,
) -> dict[str, Any]:
    audit_freeze()
    targets = _load_bank(target_bank, target_receipt)
    final = output_root / "joint-late-band"
    if final.is_dir():
        return validate_run(output_root)
    _yield_if_contended(output_root, "before_condition_load")
    metadata, unit_vectors = t14.condition_directions(source_run_root)
    _require(len(metadata) == len(unit_vectors) == 80, "T16-DP condition matrix changed")
    _yield_if_contended(output_root, "before_model_load")
    torch, tokenizer, model, model_receipt, blocks = t14._load_runtime(preflight_directory)
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    maximum_restoration_js = 0.0
    maximum_restoration_rms = 0.0
    maximum_zero_js = 0.0
    batch_size = int(_config()["runtime"]["condition_batch_size"])
    invocations = 0
    try:
        for target_index, target in enumerate(targets):
            if target_index % 16 == 0:
                _yield_if_contended(output_root, f"before_target_{target_index}")
            input_ids, attention_mask = t14._encode_prompt(torch, tokenizer, model, target["prompt"])
            _, target_rms = t14._capture_target_rms(
                torch=torch,
                model=model,
                input_ids=input_ids,
                attention_mask=attention_mask,
                injection_block=blocks[int(_config()["treatment"]["injection_block_index"])],
            )
            for start in range(0, len(metadata), batch_size):
                stop = min(start + batch_size, len(metadata))
                batch_meta = [{**dict(metadata[index]), "condition_index": index} for index in range(start, stop)]
                result = _causal_patch_batch(
                    torch=torch,
                    model=model,
                    input_ids_single=input_ids,
                    attention_mask_single=attention_mask,
                    blocks=blocks,
                    unit_vectors=unit_vectors[start:stop],
                    target_rms=target_rms,
                )
                restoration_js, restoration_rms, zero_js = _append_rows(rows, target_index, target, batch_meta, result)
                maximum_restoration_js = max(maximum_restoration_js, restoration_js)
                maximum_restoration_rms = max(maximum_restoration_rms, restoration_rms)
                maximum_zero_js = max(maximum_zero_js, zero_js)
                invocations += 1
    finally:
        del model
        torch.cuda.empty_cache()
    _require(len(rows) == 15360, "T16-DP response count changed")
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not final.exists() and not stage.exists(), "T16-DP output collision")
    stage.mkdir(parents=True)
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "joint_late_band_complete",
        "model_role": MODEL_ROLE,
        "joint_sites": [{"site": site, "block_index": block} for site, block in _joint_sites()],
        "target_rows": len(targets),
        "response_rows": len(rows),
        "condition_batch_invocations": invocations,
        "model_forward_sequences": len(targets) + 4 * invocations,
        "maximum_restoration_error_js": maximum_restoration_js,
        "maximum_restoration_error_logit_rms": maximum_restoration_rms,
        "maximum_explicit_zero_js": maximum_zero_js,
        "target_bank_sha256": _sha256(target_bank),
        "target_receipt_sha256": _sha256(target_receipt),
        "response_ledger_sha256": _sha256(stage / "response_ledger.jsonl"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "source_run_root": str(source_run_root),
        "model_receipt": model_receipt,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_run(output_root)


def validate_run(output_root: Path) -> dict[str, Any]:
    directory = output_root / "joint-late-band"
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "T16-DP run protocol changed")
    _require(receipt.get("status") == "joint_late_band_complete", "T16-DP run incomplete")
    ledger = directory / "response_ledger.jsonl"
    _require(_sha256(ledger) == receipt["response_ledger_sha256"], "T16-DP ledger changed")
    rows = _read_jsonl(ledger)
    _require(len(rows) == int(receipt["response_rows"]) == 15360, "T16-DP rows changed")
    numeric = ("treatment_js", "necessity_js", "necessity_drop_js", "sufficiency_js", "restoration_error_js", "restoration_error_logit_rms")
    _require(all(all(math.isfinite(float(row[key])) for key in numeric) for row in rows), "T16-DP ledger nonfinite")
    return {
        "status": "pass",
        "target_rows": int(receipt["target_rows"]),
        "response_rows": len(rows),
        "maximum_restoration_error_js": float(receipt["maximum_restoration_error_js"]),
        "maximum_restoration_error_logit_rms": float(receipt["maximum_restoration_error_logit_rms"]),
        "maximum_explicit_zero_js": float(receipt["maximum_explicit_zero_js"]),
        "receipt_sha256": _sha256(directory / "receipt.json"),
    }


def _target_estimands(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["target_id"]), []).append(row)
    result: list[dict[str, Any]] = []
    for target_id, values in grouped.items():
        structured = [row for row in values if row["direction_kind"] == "structured_glyph_system_prototype"]
        null = [row for row in values if row["direction_kind"] == "signed_source_covariance_null"]
        _require(len(structured) == 48 and len(null) == 32, "T16-DP estimand roster changed")

        def difference(key: str) -> float:
            return float(np.median([float(row[key]) for row in structured]) - np.median([float(row[key]) for row in null]))

        result.append(
            {
                "target_id": target_id,
                "target_group": str(values[0]["target_group"]),
                "treatment": difference("treatment_js"),
                "necessity": difference("necessity_drop_js"),
                "sufficiency": difference("sufficiency_js"),
            }
        )
    _require(len(result) == 192, "T16-DP target estimands changed")
    return sorted(result, key=lambda row: str(row["target_id"]))


def _bootstrap(values: np.ndarray, groups: Sequence[str], seed: int) -> np.ndarray:
    _require(values.shape == (192,), "T16-DP bootstrap vector changed")
    group_array = np.asarray(groups, dtype=object)
    strata = [np.flatnonzero(group_array == group) for group in TARGET_GROUPS]
    _require(all(len(indices) == 16 for indices in strata), "T16-DP bootstrap strata changed")
    replicates = int(_config()["analysis"]["bootstrap"]["replicates"])
    rng = np.random.default_rng(seed)
    results: list[np.ndarray] = []
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        sampled = np.concatenate([indices[rng.integers(0, len(indices), size=(count, len(indices)))] for indices in strata], axis=1)
        results.append(np.median(values[sampled], axis=1))
    return np.concatenate(results)


def _sign_flip(values: np.ndarray, seed: int) -> float:
    observed = float(np.median(values))
    draws = int(_config()["analysis"]["randomization"]["draws"])
    rng = np.random.default_rng(seed)
    extreme = 0
    for start in range(0, draws, 1000):
        count = min(1000, draws - start)
        signs = rng.integers(0, 2, size=(count, len(values)), dtype=np.int8).astype(np.float64) * 2.0 - 1.0
        extreme += int(np.count_nonzero(np.median(signs * values[None, :], axis=1) >= observed))
    return float((extreme + 1) / (draws + 1))


def analyze(output_root: Path, output: Path) -> dict[str, Any]:
    audit = validate_run(output_root)
    rows = _read_jsonl(output_root / "joint-late-band" / "response_ledger.jsonl")
    targets = _target_estimands(rows)
    groups = [str(row["target_group"]) for row in targets]
    floors = _config()["analysis"]["practical_floors"]
    bootstrap_seed = int(_config()["analysis"]["bootstrap"]["seed"])
    random_seed = int(_config()["analysis"]["randomization"]["seed"])
    estimands: dict[str, Any] = {}
    passed = []
    for offset, name in enumerate(("treatment", "necessity", "sufficiency")):
        values = np.asarray([float(row[name]) for row in targets])
        bootstrap = _bootstrap(values, groups, bootstrap_seed + offset)
        lower = float(np.quantile(bootstrap, 0.025))
        upper = float(np.quantile(bootstrap, 0.975))
        p_value = _sign_flip(values, random_seed + offset)
        floor = float(floors[name])
        component_pass = lower > floor and p_value < 0.05
        estimands[name] = {
            "target_median": float(np.median(values)),
            "bootstrap_95_percent_interval": [lower, upper],
            "practical_floor": floor,
            "one_sided_sign_flip_p_value": p_value,
            "component_pass": component_pass,
        }
        passed.append(component_pass)
    selected = _read_json(_root() / str(_config()["source_bindings"]["t14_selected_site"]["path"]))
    sham_pass = bool(selected["control_evidence"]["upstream_sham_pass"])
    engineering = (
        audit["maximum_restoration_error_logit_rms"] <= 1.0e-5
        and audit["maximum_restoration_error_js"] <= 1.0e-7
        and audit["maximum_explicit_zero_js"] <= 1.0e-12
        and sham_pass
    )
    decision = bool(all(passed) and engineering)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "distributed_late_band_analysis_complete",
        "audit": audit,
        "estimands": estimands,
        "bound_t14_upstream_sham_pass": sham_pass,
        "engineering_gates_pass": engineering,
        "distributed_late_band_iut_pass": decision,
        "decision": "joint_late_band_mediation_supported" if decision else "joint_late_band_iut_non_rejecting",
        "claim_boundary": _config()["claim_boundary"],
        "unique_minimal_or_complete_circuit_claim_authorized": False,
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
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=FREEZE_PATH)
    subparsers.add_parser("audit-freeze")
    bank = subparsers.add_parser("materialize-bank")
    bank.add_argument("--output", type=Path, required=True)
    bank.add_argument("--receipt-output", type=Path, required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--output-root", type=Path, required=True)
    run_parser.add_argument("--source-run-root", type=Path, required=True)
    run_parser.add_argument("--preflight-directory", type=Path, required=True)
    run_parser.add_argument("--target-bank", type=Path, required=True)
    run_parser.add_argument("--target-receipt", type=Path, required=True)
    validate = subparsers.add_parser("validate-run")
    validate.add_argument("--output-root", type=Path, required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--output-root", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "write-design-preflight":
        result = write_design_preflight(args.output)
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "materialize-bank":
        result = materialize_bank(args.output, args.receipt_output)
    elif args.command == "run":
        result = run(
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            preflight_directory=args.preflight_directory,
            target_bank=args.target_bank,
            target_receipt=args.target_receipt,
        )
    elif args.command == "validate-run":
        result = validate_run(args.output_root)
    else:
        result = analyze(args.output_root, args.output)
    _print(result)


if __name__ == "__main__":
    main()
