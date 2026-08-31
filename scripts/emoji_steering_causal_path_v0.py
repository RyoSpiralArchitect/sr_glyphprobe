#!/usr/bin/env python3
"""Freeze, localize, and confirm the T14-C causal path experiment."""

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

import emoji_steering_specificity_expansion_v0 as t14x  # noqa: E402
import emoji_steering_specificity_harvest_v0 as t13  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-emoji-steering-causal-path-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_steering_causal_path_v0.yaml")
FREEZE_PATH = Path("data/manifests/emoji_steering_causal_path_v0.json")
SITE_MANIFEST_PATH = Path("data/manifests/emoji_steering_causal_site_v0.json")
VALIDATION_DIRECTORY = Path("validation/emoji_steering_causal_path_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
LOCALIZATION_ROLE = "llama32_3b_base_bf16"
STATIC_FROZEN_ASSETS = (
    "configs/emoji_steering_causal_path_v0.yaml",
    "docs/EMOJI_STEERING_CAUSAL_PATH_V0.md",
    "docs/EMOJI_STEERING_CAUSAL_PATH_V0.ja.md",
    "scripts/emoji_steering_causal_path_v0.py",
    "tests/test_emoji_steering_causal_path_v0.py",
    "validation/emoji_steering_causal_path_v0/design_preflight.json",
)


class CausalPathError(RuntimeError):
    """Raised when a T14-C gate or binding is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CausalPathError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@cache
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T14-C protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    return atlas._sha256(path)


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


def _candidate_sites() -> tuple[tuple[str, int], ...]:
    return tuple(
        (str(row["site"]), int(row["block_index"]))
        for row in _config()["localization"]["candidate_order"]
    )


def _control_sites() -> tuple[tuple[str, int], tuple[str, int]]:
    values = _config()["localization"]["controls"]
    positive = values["positive"]
    negative = values["negative"]
    return (
        (str(positive["site"]), int(positive["block_index"])),
        (str(negative["site"]), int(negative["block_index"])),
    )


def _all_localization_sites() -> tuple[tuple[str, int], ...]:
    positive, negative = _control_sites()
    return (*_candidate_sites(), positive, negative)


def audit_design() -> dict[str, Any]:
    config = _config()
    observed: dict[str, str] = {}
    for key in (
        "t13_harvest_config",
        "t13_scientific_open_closeout",
        "t14x_execution_freeze",
        "public_localization_targets",
    ):
        binding = config["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"T14-C bound input missing: {key}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T14-C input changed: {key}")
        observed[path.relative_to(_root()).as_posix()] = actual
    t14x.audit_freeze()
    _require(LOCALIZATION_ROLE == config["fixed_model"]["role"], "Model role changed")
    spec = t10._model_spec(LOCALIZATION_ROLE)
    _require(spec["expected_num_layers"] == 28, "Llama layer count changed")
    _require(spec["expected_model_dim"] == 3072, "Llama width changed")
    injection_block = int(config["treatment"]["injection_block_index"])
    _require(
        t13.layer_indices(LOCALIZATION_ROLE)[6] == injection_block, "Depth changed"
    )
    _require(
        _candidate_sites()
        == tuple(
            (site, layer) for layer in range(24, 28) for site in ("attn_out", "mlp_out")
        ),
        "Candidate site roster changed",
    )
    _require(
        _control_sites() == (("resid_pre", 24), ("mlp_out", 22)), "Controls changed"
    )
    structured = len(
        config["treatment"]["structured_directions"]["glyph_systems"]
    ) * int(config["treatment"]["structured_directions"]["wrapper_folds"])
    null = (
        len(config["treatment"]["null_directions"]["families"])
        * int(config["treatment"]["null_directions"]["wrapper_folds"])
        * int(config["treatment"]["null_directions"]["seeds_per_family_per_fold"])
    )
    signs = len(config["treatment"]["signs"])
    conditions = (structured + null) * signs
    _require(
        structured == 24 and null == 16 and conditions == 80, "Direction count changed"
    )
    localization_records = 32 * conditions * len(_all_localization_sites())
    confirmation_records = int(config["c1_v2_bank"]["rows"]) * conditions
    _require(localization_records == 25_600, "Localization record count changed")
    _require(confirmation_records == 15_360, "C1 v2 record count changed")
    _require(
        config["c1_v2_bank"]["status_at_design_freeze"] == "not_generated",
        "C1 v2 bank status changed",
    )
    _require(
        not (_root() / SITE_MANIFEST_PATH).exists(),
        "Selected site exists before localization freeze",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "fixed_model_role": LOCALIZATION_ROLE,
        "injection_block_index": injection_block,
        "candidate_sites": [
            {"site": site, "block_index": layer} for site, layer in _candidate_sites()
        ],
        "control_sites": [
            {"site": site, "block_index": layer} for site, layer in _control_sites()
        ],
        "structured_directions_before_sign": structured,
        "null_directions_before_sign": null,
        "signed_conditions_per_target": conditions,
        "localization_targets": 32,
        "localization_response_records": localization_records,
        "c1_v2_targets_planned": int(config["c1_v2_bank"]["rows"]),
        "c1_v2_response_records_planned": confirmation_records,
        "source_bindings": observed,
        "model_weights_loaded": False,
        "model_forward_sequences": 0,
        "localization_outcomes_opened": False,
        "c1_v2_bank_generated": False,
        "c1_v2_target_rows_opened": 0,
        "generation_calls": 0,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    value = audit_design()
    _write_json(output, value)
    return value


def freeze(output: Path) -> dict[str, Any]:
    preflight = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(preflight == audit_design(), "T14-C design preflight is stale")
    assets: dict[str, str] = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"T14-C frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "localization_freeze_complete_before_any_t14c_forward",
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "fixed_model_role": LOCALIZATION_ROLE,
        "candidate_sites": [
            {"site": site, "block_index": layer} for site, layer in _candidate_sites()
        ],
        "control_sites": [
            {"site": site, "block_index": layer} for site, layer in _control_sites()
        ],
        "localization_response_records": 25_600,
        "c1_v2_response_records_planned": 15_360,
        "model_forward_sequences_at_freeze": 0,
        "localization_outcomes_available_at_freeze": False,
        "c1_v2_bank_generated_at_freeze": False,
        "c1_v2_target_rows_opened_at_freeze": 0,
    }
    _write_json(output, manifest)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T14-C freeze mismatch")
    _require(
        value.get("status") == "localization_freeze_complete_before_any_t14c_forward",
        "T14-C localization freeze incomplete",
    )
    for relative, expected in value["frozen_assets"].items():
        candidate = _root() / str(relative)
        _require(candidate.is_file(), f"T14-C frozen asset missing: {relative}")
        _require(
            _sha256(candidate) == str(expected), f"T14-C asset changed: {relative}"
        )
    _require(value["fixed_model_role"] == LOCALIZATION_ROLE, "T14-C model changed")
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(value["frozen_assets"]),
    }


def _causal_null_seed(fold: int, family: str, seed_index: int) -> int:
    payload = f"glyphprobe-t14c-v0:{fold}:{family}:{seed_index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def condition_directions(
    source_run_root: Path,
) -> tuple[list[dict[str, Any]], np.ndarray]:
    expected_root = Path(_config()["source_bindings"]["source_run_root"])
    _require(source_run_root.resolve() == expected_root, "T14-C source root changed")
    t14x._validate_source_role(source_run_root, LOCALIZATION_ROLE)
    wrapper_deltas, mask = t14x._load_wrapper_deltas(source_run_root, LOCALIZATION_ROLE)
    site_index = 6
    metadata: list[dict[str, Any]] = []
    vectors: list[np.ndarray] = []
    for fold in range(4):
        loo = t14x._leave_one_wrapper_out(wrapper_deltas, fold)
        prototypes = t14x._prototype_map(loo, mask, site_index)
        for system in _config()["treatment"]["structured_directions"]["glyph_systems"]:
            vector = prototypes[(str(system), "glyph")]
            for sign in (-1, 1):
                metadata.append(
                    {
                        "direction_kind": "structured_glyph_system_prototype",
                        "glyph_system": str(system),
                        "held_out_wrapper_index": fold,
                        "sign": sign,
                    }
                )
                vectors.append(vector * np.float32(sign))
        residuals = t14x._residual_matrix(loo, mask, site_index, prototypes)
        for family in _config()["treatment"]["null_directions"]["families"]:
            for seed_index in range(2):
                seed = _causal_null_seed(fold, str(family), seed_index)
                vector = t14x._null_direction(residuals, str(family), seed)
                for sign in (-1, 1):
                    metadata.append(
                        {
                            "direction_kind": "signed_source_covariance_null",
                            "null_family": str(family),
                            "held_out_wrapper_index": fold,
                            "seed_index": seed_index,
                            "seed": seed,
                            "sign": sign,
                        }
                    )
                    vectors.append(vector * np.float32(sign))
    array = np.stack(vectors, axis=0).astype(np.float32)
    array = t14x._unit_rows(array)
    _require(
        len(metadata) == 80 and array.shape == (80, 3072), "Condition roster changed"
    )
    return metadata, array


_TARGET_GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
    "comparison",
    "counterfactual",
    "summarization",
    "transformation",
    "dialogue",
    "constrained_writing",
)
_AGENTS = (
    "archivist",
    "baker",
    "carpenter",
    "designer",
    "engineer",
    "farmer",
    "geologist",
    "historian",
    "inspector",
    "journalist",
    "librarian",
    "mechanic",
    "navigator",
    "operator",
    "planner",
    "researcher",
    "surveyor",
    "teacher",
    "technician",
    "volunteer",
)
_OBJECTS = (
    "archive",
    "battery",
    "bridge",
    "calendar",
    "camera",
    "dataset",
    "engine",
    "garden",
    "instrument",
    "journal",
    "map",
    "notebook",
    "package",
    "report",
    "sample",
    "schedule",
    "sensor",
    "shelter",
    "toolkit",
    "workshop",
)
_PLACES = (
    "courtyard",
    "field station",
    "harbor",
    "laboratory",
    "library",
    "market",
    "museum",
    "observatory",
    "office",
    "orchard",
    "railway platform",
    "reading room",
    "school",
    "studio",
    "test site",
    "warehouse",
)
_QUALITIES = (
    "accurate",
    "compact",
    "durable",
    "efficient",
    "fair",
    "flexible",
    "portable",
    "quiet",
    "reliable",
    "reversible",
    "safe",
    "simple",
    "stable",
    "transparent",
    "verifiable",
    "weather-resistant",
)


def _pick(values: Sequence[str], seed: int, namespace: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:{namespace}:{index}".encode("utf-8")).digest()
    return values[int.from_bytes(digest[:8], "big") % len(values)]


def _build_target_prompt(group: str, index: int, seed: int) -> str:
    agent = _pick(_AGENTS, seed, f"{group}:agent", index)
    other = _pick(_AGENTS, seed, f"{group}:other", index)
    obj = _pick(_OBJECTS, seed, f"{group}:object", index)
    other_obj = _pick(_OBJECTS, seed, f"{group}:other_object", index)
    place = _pick(_PLACES, seed, f"{group}:place", index)
    quality = _pick(_QUALITIES, seed, f"{group}:quality", index)
    templates = {
        "continuation": f"Complete with one natural continuation:\nAt the {place}, the {agent} checked the {obj} before",
        "factual": f"Answer in one concise sentence:\nWhy can a {obj} be described as {quality} in a controlled test?",
        "reasoning": f"State what follows logically and explain briefly:\nEvery {quality} {obj} is logged. This {obj} is {quality}.",
        "procedural": f"Give three compact steps for having a {agent} verify a {obj} at the {place}.",
        "classification": f"Classify as physical, social, or abstract, then give one reason:\nA {quality} {obj} maintained by a {agent}.",
        "planning": f"Propose a minimal one-day plan for a {agent} and a {other} to inspect a {obj} at the {place}.",
        "comparison": f"Compare a {quality} {obj} with a {other_obj}; give one similarity and one difference.",
        "counterfactual": f"Answer briefly:\nIf the {agent} had not brought the {obj} to the {place}, what would most likely need to change?",
        "summarization": f"Summarize in one sentence:\nThe {agent} tested the {obj} twice at the {place}. The second test used a more {quality} procedure.",
        "transformation": f"Rewrite in the passive voice without adding facts:\nThe {agent} recorded the {quality} {obj} at the {place}.",
        "dialogue": f"Write one concise reply from the {other}:\n{agent.title()}: Did you verify the {obj} at the {place}?",
        "constrained_writing": f"Write exactly eight words about a {quality} {obj} in the {place}.",
    }
    return templates[group]


def build_target_rows(seed: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group in _TARGET_GROUPS:
        for index in range(16):
            prompt = _build_target_prompt(group, index, seed)
            rows.append(
                {
                    "id": f"c1v2_{group}_{index + 1:02d}",
                    "group": group,
                    "prompt": (f"{prompt}\nCase reference: {group}-{index + 1:02d}."),
                }
            )
    _require(len(rows) == 192, "C1 v2 target count changed")
    _require(len({row["id"] for row in rows}) == 192, "C1 v2 IDs are not unique")
    _require(
        len({row["prompt"] for row in rows}) == 192, "C1 v2 prompts are not unique"
    )
    _require(
        all(not any(ord(char) > 0xFFFF for char in row["prompt"]) for row in rows),
        "C1 v2 prompt contains astral glyphs",
    )
    return rows


def _tensor_from_output(output: Any) -> tuple[Any, Any]:
    if hasattr(output, "shape"):
        return output, lambda value: value
    if isinstance(output, tuple) and output and hasattr(output[0], "shape"):
        return output[0], lambda value: (value, *output[1:])
    if isinstance(output, list) and output and hasattr(output[0], "shape"):
        return output[0], lambda value: [value, *output[1:]]
    raise CausalPathError(f"Cannot identify tensor in module output {type(output)!r}")


def _tensor_from_input(inputs: tuple[Any, ...]) -> tuple[Any, Any]:
    _require(
        bool(inputs) and hasattr(inputs[0], "shape"), "Cannot identify module input"
    )
    return inputs[0], lambda value: (value, *inputs[1:])


def _site_module(
    blocks: Sequence[Any], site: str, block_index: int
) -> tuple[Any, bool]:
    block = blocks[block_index]
    if site == "resid_pre":
        return block, True
    names = (
        ("self_attn", "attn", "attention")
        if site == "attn_out"
        else ("mlp", "feed_forward", "ffn")
    )
    for name in names:
        if hasattr(block, name):
            return getattr(block, name), False
    raise CausalPathError(f"Could not discover {site} in block {block_index}")


def _forward_batch(
    *,
    torch: Any,
    model: Any,
    input_ids: Any,
    attention_mask: Any,
    injection_block: Any,
    injection_vectors: Any | None,
    mediator_module: Any | None,
    mediator_is_pre: bool,
    mediator_replacement: Any | None,
    capture_mediator: bool,
) -> tuple[Any, Any | None]:
    handles: list[Any] = []
    captured: dict[str, Any] = {}
    if injection_vectors is not None:

        def injection_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            raw, rebuild = _tensor_from_output(output)
            changed = raw.clone()
            changed[:, -1, :] = changed[:, -1, :] + injection_vectors.to(
                device=raw.device, dtype=raw.dtype
            )
            return rebuild(changed)

        handles.append(injection_block.register_forward_hook(injection_hook))
    if mediator_module is not None and mediator_is_pre:

        def mediator_pre_hook(_module: Any, inputs: tuple[Any, ...]) -> Any:
            raw, rebuild = _tensor_from_input(inputs)
            if capture_mediator:
                captured["value"] = raw[:, -1, :].detach().clone()
            if mediator_replacement is None:
                return None
            changed = raw.clone()
            changed[:, -1, :] = mediator_replacement.to(
                device=raw.device, dtype=raw.dtype
            )
            return rebuild(changed)

        handles.append(mediator_module.register_forward_pre_hook(mediator_pre_hook))
    elif mediator_module is not None:

        def mediator_post_hook(_module: Any, _inputs: Any, output: Any) -> Any:
            raw, rebuild = _tensor_from_output(output)
            if capture_mediator:
                captured["value"] = raw[:, -1, :].detach().clone()
            if mediator_replacement is None:
                return output
            changed = raw.clone()
            changed[:, -1, :] = mediator_replacement.to(
                device=raw.device, dtype=raw.dtype
            )
            return rebuild(changed)

        handles.append(mediator_module.register_forward_hook(mediator_post_hook))
    try:
        with torch.inference_mode():
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                return_dict=True,
            )
        logits = output.logits[:, -1, :].detach().float()
    finally:
        for handle in handles:
            handle.remove()
    return logits, captured.get("value")


def _capture_target_rms(
    *,
    torch: Any,
    model: Any,
    input_ids: Any,
    attention_mask: Any,
    injection_block: Any,
) -> tuple[Any, float]:
    captured: dict[str, Any] = {}

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        raw, _ = _tensor_from_output(output)
        captured["value"] = raw[0, -1, :].detach().float().clone()
        return output

    handle = injection_block.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                use_cache=False,
                return_dict=True,
            )
        logits = output.logits[0, -1, :].detach().float()
    finally:
        handle.remove()
    value = captured["value"]
    rms = float(torch.sqrt(torch.mean(value * value)).item())
    _require(math.isfinite(rms) and rms > 0, "Target activation RMS is invalid")
    return logits, rms


def causal_patch_batch(
    *,
    torch: Any,
    model: Any,
    input_ids_single: Any,
    attention_mask_single: Any,
    blocks: Sequence[Any],
    unit_vectors: np.ndarray,
    target_rms: float,
    site: str,
    block_index: int,
) -> dict[str, np.ndarray]:
    _require(unit_vectors.ndim == 2 and len(unit_vectors) > 0, "Empty treatment batch")
    magnitude = float(_config()["treatment"]["magnitude"])
    scaled = unit_vectors.astype(np.float32) * np.float32(target_rms * magnitude)
    all_vectors = np.concatenate(
        (np.zeros((2, scaled.shape[1]), dtype=np.float32), scaled), axis=0
    )
    device = next(model.parameters()).device
    vector_tensor = torch.tensor(all_vectors, dtype=torch.float32, device=device)
    count = len(all_vectors)
    input_ids = input_ids_single.repeat(count, 1)
    attention_mask = attention_mask_single.repeat(count, 1)
    injection_block = blocks[int(_config()["treatment"]["injection_block_index"])]
    mediator_module, mediator_is_pre = _site_module(blocks, site, block_index)
    treatment_logits, mediator = _forward_batch(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vector_tensor,
        mediator_module=mediator_module,
        mediator_is_pre=mediator_is_pre,
        mediator_replacement=None,
        capture_mediator=True,
    )
    _require(
        mediator is not None and mediator.shape[0] == count, "Mediator capture failed"
    )
    baseline_mediator = mediator[:1].expand_as(mediator)
    necessity_logits, _ = _forward_batch(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vector_tensor,
        mediator_module=mediator_module,
        mediator_is_pre=mediator_is_pre,
        mediator_replacement=baseline_mediator,
        capture_mediator=False,
    )
    sufficiency_logits, _ = _forward_batch(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=None,
        mediator_module=mediator_module,
        mediator_is_pre=mediator_is_pre,
        mediator_replacement=mediator,
        capture_mediator=False,
    )
    restoration_logits, _ = _forward_batch(
        torch=torch,
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        injection_block=injection_block,
        injection_vectors=vector_tensor,
        mediator_module=mediator_module,
        mediator_is_pre=mediator_is_pre,
        mediator_replacement=mediator,
        capture_mediator=False,
    )
    result = {
        "baseline": treatment_logits[:1].detach().cpu().numpy(),
        "zero": treatment_logits[1:2].detach().cpu().numpy(),
        "treatment": treatment_logits[2:].detach().cpu().numpy(),
        "necessity": necessity_logits[2:].detach().cpu().numpy(),
        "sufficiency": sufficiency_logits[2:].detach().cpu().numpy(),
        "restoration": restoration_logits[2:].detach().cpu().numpy(),
    }
    _require(
        all(np.isfinite(value).all() for value in result.values()),
        "Causal patch produced nonfinite logits",
    )
    return result


def _scalar_metrics(baseline: np.ndarray, other: np.ndarray) -> dict[str, np.ndarray]:
    base = np.asarray(baseline, dtype=np.float64)
    value = np.asarray(other, dtype=np.float64)
    if base.shape[0] == 1 and value.shape[0] != 1:
        base = np.repeat(base, value.shape[0], axis=0)
    base_shift = base - np.max(base, axis=-1, keepdims=True)
    value_shift = value - np.max(value, axis=-1, keepdims=True)
    p0 = np.exp(base_shift)
    p1 = np.exp(value_shift)
    p0 /= np.sum(p0, axis=-1, keepdims=True)
    p1 /= np.sum(p1, axis=-1, keepdims=True)
    logp0 = np.log(np.clip(p0, 1e-300, None))
    logp1 = np.log(np.clip(p1, 1e-300, None))
    mean = 0.5 * (p0 + p1)
    log_mean = np.log(np.clip(mean, 1e-300, None))
    return {
        "kl": np.sum(p0 * (logp0 - logp1), axis=-1),
        "js": 0.5 * np.sum(p0 * (logp0 - log_mean), axis=-1)
        + 0.5 * np.sum(p1 * (logp1 - log_mean), axis=-1),
        "tv": 0.5 * np.sum(np.abs(p0 - p1), axis=-1),
        "logit_rms": np.sqrt(np.mean(np.square(value - base), axis=-1)),
        "entropy_change": -np.sum(p1 * logp1, axis=-1) + np.sum(p0 * logp0, axis=-1),
        "argmax_flip": (np.argmax(base, axis=-1) != np.argmax(value, axis=-1)).astype(
            np.int8
        ),
    }


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
                "status": "yielded_before_new_shard_for_foreign_gpu_contention",
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(75)


def _public_targets() -> list[dict[str, str]]:
    binding = _config()["source_bindings"]["public_localization_targets"]
    path = _root() / str(binding["path"])
    rows = _read_jsonl(path)
    return _validate_target_rows(rows, int(binding["expected_rows"]), c1_v2=False)


def _validate_target_rows(
    values: Sequence[Mapping[str, Any]], expected_rows: int, *, c1_v2: bool
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for value in values:
        row = {
            "id": str(value.get("id", "")),
            "group": str(value.get("group", "")),
            "prompt": str(value.get("prompt", "")),
        }
        _require(all(row.values()), "Target row contains an empty required field")
        rows.append(row)
    _require(len(rows) == expected_rows, "Target row count changed")
    _require(len({row["id"] for row in rows}) == len(rows), "Target IDs changed")
    _require(
        len({row["prompt"] for row in rows}) == len(rows),
        "Target prompts are not unique",
    )
    if c1_v2:
        _require(expected_rows == 192, "C1 v2 row count changed")
        _require(
            all(row["id"].startswith("c1v2_") for row in rows),
            "C1 v2 target namespace changed",
        )
        counts = {
            group: sum(row["group"] == group for row in rows)
            for group in _TARGET_GROUPS
        }
        _require(
            set(row["group"] for row in rows) == set(_TARGET_GROUPS),
            "C1 v2 strata changed",
        )
        _require(set(counts.values()) == {16}, "C1 v2 stratum balance changed")
    return rows


def _encode_prompt(
    torch: Any, tokenizer: Any, model: Any, prompt: str
) -> tuple[Any, Any]:
    ids = t13._token_ids(tokenizer, prompt)
    device = next(model.parameters()).device
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    return input_ids, torch.ones_like(input_ids)


def _site_name(site: str, block_index: int) -> str:
    return f"site-{site}-block-{block_index:02d}"


def _site_directory(output_root: Path, phase: str, site: str, block_index: int) -> Path:
    return output_root / phase / _site_name(site, block_index)


def _atomic_directory(final: Path) -> tuple[Path, Path]:
    _require(not final.exists(), f"T14-C final output already exists: {final}")
    final.parent.mkdir(parents=True, exist_ok=True)
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not stage.exists(), "T14-C staging collision")
    stage.mkdir()
    return stage, final


def _append_causal_rows(
    *,
    rows: list[dict[str, Any]],
    phase: str,
    site: str,
    block_index: int,
    target_index: int,
    target: Mapping[str, str],
    metadata: Sequence[Mapping[str, Any]],
    result: Mapping[str, np.ndarray],
) -> tuple[float, float, float]:
    treatment = _scalar_metrics(result["baseline"], result["treatment"])
    necessity = _scalar_metrics(result["baseline"], result["necessity"])
    sufficiency = _scalar_metrics(result["baseline"], result["sufficiency"])
    sufficiency_error = _scalar_metrics(result["treatment"], result["sufficiency"])
    restoration = _scalar_metrics(result["treatment"], result["restoration"])
    zero = _scalar_metrics(result["baseline"], result["zero"])
    for index, condition in enumerate(metadata):
        row = dict(condition)
        row.update(
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "phase": phase,
                "site": site,
                "block_index": block_index,
                "target_index": target_index,
                "target_id": target["id"],
                "target_group": target["group"],
                "treatment_js": float(treatment["js"][index]),
                "treatment_kl": float(treatment["kl"][index]),
                "treatment_tv": float(treatment["tv"][index]),
                "treatment_logit_rms": float(treatment["logit_rms"][index]),
                "treatment_entropy_change": float(treatment["entropy_change"][index]),
                "treatment_argmax_flip": bool(treatment["argmax_flip"][index]),
                "necessity_js": float(necessity["js"][index]),
                "necessity_drop_js": float(
                    treatment["js"][index] - necessity["js"][index]
                ),
                "sufficiency_js": float(sufficiency["js"][index]),
                "sufficiency_error_js": float(sufficiency_error["js"][index]),
                "sufficiency_error_logit_rms": float(
                    sufficiency_error["logit_rms"][index]
                ),
                "restoration_error_js": float(restoration["js"][index]),
                "restoration_error_logit_rms": float(restoration["logit_rms"][index]),
            }
        )
        rows.append(row)
    return (
        float(np.max(restoration["js"])),
        float(np.max(restoration["logit_rms"])),
        float(np.max(np.abs(zero["js"]))),
    )


def _expected_site_rows(phase: str) -> int:
    if phase == "localization":
        return 32 * 80
    _require(phase == "confirmation", f"Unknown T14-C phase: {phase}")
    return 192 * 80


def _execute_site(
    *,
    phase: str,
    site: str,
    block_index: int,
    output_root: Path,
    targets: Sequence[Mapping[str, str]],
    metadata: Sequence[Mapping[str, Any]],
    unit_vectors: np.ndarray,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
) -> dict[str, Any]:
    final = _site_directory(output_root, phase, site, block_index)
    if final.exists():
        return validate_site(final, phase, site, block_index)
    _yield_if_contended(output_root, f"before_{phase}_{_site_name(site, block_index)}")
    _require(len(metadata) == len(unit_vectors) == 80, "Condition matrix changed")
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    maximum_restoration_js = 0.0
    maximum_restoration_rms = 0.0
    maximum_zero_js = 0.0
    batch_size = int(_config()["runtime"]["condition_batch_size"])
    batch_invocations = 0
    for target_index, target in enumerate(targets):
        _yield_if_contended(
            output_root,
            f"during_{phase}_{_site_name(site, block_index)}_before_target_{target_index}",
        )
        input_ids, attention_mask = _encode_prompt(
            torch, tokenizer, model, target["prompt"]
        )
        _, target_rms = _capture_target_rms(
            torch=torch,
            model=model,
            input_ids=input_ids,
            attention_mask=attention_mask,
            injection_block=blocks[
                int(_config()["treatment"]["injection_block_index"])
            ],
        )
        for start in range(0, len(metadata), batch_size):
            stop = min(start + batch_size, len(metadata))
            batch_meta = []
            for condition_index in range(start, stop):
                value = dict(metadata[condition_index])
                value["condition_index"] = condition_index
                batch_meta.append(value)
            result = causal_patch_batch(
                torch=torch,
                model=model,
                input_ids_single=input_ids,
                attention_mask_single=attention_mask,
                blocks=blocks,
                unit_vectors=unit_vectors[start:stop],
                target_rms=target_rms,
                site=site,
                block_index=block_index,
            )
            restoration_js, restoration_rms, zero_js = _append_causal_rows(
                rows=rows,
                phase=phase,
                site=site,
                block_index=block_index,
                target_index=target_index,
                target=target,
                metadata=batch_meta,
                result=result,
            )
            maximum_restoration_js = max(maximum_restoration_js, restoration_js)
            maximum_restoration_rms = max(maximum_restoration_rms, restoration_rms)
            maximum_zero_js = max(maximum_zero_js, zero_js)
            batch_invocations += 1
    expected_rows = _expected_site_rows(phase)
    _require(len(rows) == expected_rows, "T14-C site response count changed")
    stage, final = _atomic_directory(final)
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "site_complete",
        "phase": phase,
        "site": site,
        "block_index": block_index,
        "response_rows": len(rows),
        "target_rows": len(targets),
        "signed_conditions_per_target": len(metadata),
        "condition_batch_invocations": batch_invocations,
        "model_forward_sequences": len(targets) + 4 * batch_invocations,
        "maximum_restoration_error_js": maximum_restoration_js,
        "maximum_restoration_error_logit_rms": maximum_restoration_rms,
        "maximum_explicit_zero_js": maximum_zero_js,
        "response_ledger_sha256": _sha256(stage / "response_ledger.jsonl"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_site(final, phase, site, block_index)


def validate_site(
    directory: Path, phase: str, site: str, block_index: int
) -> dict[str, Any]:
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Site protocol changed")
    _require(receipt.get("status") == "site_complete", "Site is incomplete")
    _require(receipt.get("phase") == phase, "Site phase changed")
    _require(receipt.get("site") == site, "Site name changed")
    _require(int(receipt.get("block_index")) == block_index, "Site block changed")
    ledger = directory / "response_ledger.jsonl"
    _require(
        _sha256(ledger) == receipt["response_ledger_sha256"],
        "Site ledger hash changed",
    )
    rows = _read_jsonl(ledger)
    expected = _expected_site_rows(phase)
    _require(len(rows) == expected, "Site ledger row count changed")
    _require(int(receipt["response_rows"]) == expected, "Site receipt count changed")
    target_count = 32 if phase == "localization" else 192
    roster: dict[str, set[int]] = {}
    numeric = (
        "treatment_js",
        "necessity_js",
        "necessity_drop_js",
        "sufficiency_js",
        "sufficiency_error_js",
        "sufficiency_error_logit_rms",
        "restoration_error_js",
        "restoration_error_logit_rms",
    )
    for row in rows:
        _require(row["phase"] == phase, "Ledger phase changed")
        _require(row["site"] == site, "Ledger site changed")
        _require(int(row["block_index"]) == block_index, "Ledger block changed")
        _require(
            all(math.isfinite(float(row[key])) for key in numeric),
            "Ledger contains nonfinite metrics",
        )
        roster.setdefault(str(row["target_id"]), set()).add(int(row["condition_index"]))
    _require(len(roster) == target_count, "Site target count changed")
    _require(
        all(indices == set(range(80)) for indices in roster.values()),
        "Site condition roster changed",
    )
    return {
        "status": "pass",
        "phase": phase,
        "site": site,
        "block_index": block_index,
        "response_rows": expected,
        "maximum_restoration_error_js": float(receipt["maximum_restoration_error_js"]),
        "maximum_restoration_error_logit_rms": float(
            receipt["maximum_restoration_error_logit_rms"]
        ),
        "maximum_explicit_zero_js": float(receipt["maximum_explicit_zero_js"]),
    }


def _load_runtime(
    preflight_directory: Path,
) -> tuple[Any, Any, Any, Any, Sequence[Any]]:
    snapshot = t13.t11._locate_local_snapshot(LOCALIZATION_ROLE)
    torch, tokenizer, model, receipt = t13._load_model(
        LOCALIZATION_ROLE, snapshot, preflight_directory
    )
    blocks = t10._resolve_attr(
        model, str(t10._model_spec(LOCALIZATION_ROLE)["expected_block_path"])
    )
    _require(len(blocks) == 28, "T14-C runtime layer count changed")
    return torch, tokenizer, model, receipt, blocks


def _phase_summary_path(output_root: Path, phase: str) -> Path:
    return output_root / phase / "summary.json"


def _run_phase(
    *,
    phase: str,
    sites: Sequence[tuple[str, int]],
    targets: Sequence[Mapping[str, str]],
    output_root: Path,
    source_run_root: Path,
    preflight_directory: Path,
) -> dict[str, Any]:
    audit_freeze()
    summary_path = _phase_summary_path(output_root, phase)
    if summary_path.is_file():
        return validate_phase(output_root, phase, sites)
    _yield_if_contended(output_root, f"before_{phase}_model_load")
    metadata, vectors = condition_directions(source_run_root)
    torch, tokenizer, model, model_receipt, blocks = _load_runtime(preflight_directory)
    started = time.perf_counter()
    results = []
    try:
        for site, block_index in sites:
            results.append(
                _execute_site(
                    phase=phase,
                    site=site,
                    block_index=block_index,
                    output_root=output_root,
                    targets=targets,
                    metadata=metadata,
                    unit_vectors=vectors,
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    blocks=blocks,
                )
            )
    finally:
        del model
        torch.cuda.empty_cache()
    total = sum(int(row["response_rows"]) for row in results)
    expected = _expected_site_rows(phase) * len(sites)
    _require(total == expected, "T14-C phase response count changed")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": f"{phase}_complete",
        "phase": phase,
        "sites": [
            {"site": site, "block_index": block_index} for site, block_index in sites
        ],
        "target_rows": len(targets),
        "signed_conditions_per_target": len(metadata),
        "response_rows": total,
        "source_run_root": str(source_run_root),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_receipt": model_receipt,
        "generation_calls": 0,
        "elapsed_seconds_this_process": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(summary_path, summary)
    return validate_phase(output_root, phase, sites)


def run_localization(
    *, output_root: Path, source_run_root: Path, preflight_directory: Path
) -> dict[str, Any]:
    _require(
        not (_root() / SITE_MANIFEST_PATH).exists(),
        "Selected site already exists; localization cannot be adapted",
    )
    return _run_phase(
        phase="localization",
        sites=_all_localization_sites(),
        targets=_public_targets(),
        output_root=output_root,
        source_run_root=source_run_root,
        preflight_directory=preflight_directory,
    )


def validate_phase(
    output_root: Path, phase: str, sites: Sequence[tuple[str, int]]
) -> dict[str, Any]:
    results = [
        validate_site(
            _site_directory(output_root, phase, site, block_index),
            phase,
            site,
            block_index,
        )
        for site, block_index in sites
    ]
    summary_path = _phase_summary_path(output_root, phase)
    summary = _read_json(summary_path)
    _require(summary.get("protocol_id") == PROTOCOL_ID, "Phase protocol changed")
    _require(summary.get("status") == f"{phase}_complete", "Phase is incomplete")
    total = sum(int(row["response_rows"]) for row in results)
    _require(int(summary.get("response_rows")) == total, "Phase total changed")
    return {
        "status": "pass",
        "phase": phase,
        "sites_complete": len(results),
        "response_rows": total,
        "summary_sha256": _sha256(summary_path),
    }


def _target_estimands(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["target_id"]), []).append(row)
    result: list[dict[str, Any]] = []
    for target_id, values in grouped.items():
        structured = [
            row
            for row in values
            if row["direction_kind"] == "structured_glyph_system_prototype"
        ]
        null = [
            row
            for row in values
            if row["direction_kind"] == "signed_source_covariance_null"
        ]
        _require(len(structured) == 48 and len(null) == 32, "Estimand roster changed")

        def difference(key: str) -> float:
            return float(
                np.median([float(row[key]) for row in structured])
                - np.median([float(row[key]) for row in null])
            )

        result.append(
            {
                "target_id": target_id,
                "target_group": str(values[0]["target_group"]),
                "treatment_excess_js": difference("treatment_js"),
                "necessity_excess_js": difference("necessity_drop_js"),
                "sufficiency_excess_js": difference("sufficiency_js"),
            }
        )
    return sorted(result, key=lambda row: str(row["target_id"]))


def _site_evidence(
    localization_root: Path, site: str, block_index: int
) -> dict[str, Any]:
    directory = _site_directory(localization_root, "localization", site, block_index)
    validated = validate_site(directory, "localization", site, block_index)
    rows = _read_jsonl(directory / "response_ledger.jsonl")
    target_values = _target_estimands(rows)
    return {
        "site": site,
        "block_index": block_index,
        "median_target_treatment_excess_js": float(
            np.median([row["treatment_excess_js"] for row in target_values])
        ),
        "median_target_necessity_excess_js": float(
            np.median([row["necessity_excess_js"] for row in target_values])
        ),
        "median_target_sufficiency_excess_js": float(
            np.median([row["sufficiency_excess_js"] for row in target_values])
        ),
        "maximum_restoration_error_js": validated["maximum_restoration_error_js"],
        "maximum_restoration_error_logit_rms": validated[
            "maximum_restoration_error_logit_rms"
        ],
        "maximum_explicit_zero_js": validated["maximum_explicit_zero_js"],
        "target_rows": len(target_values),
    }


def select_site(localization_root: Path, output: Path) -> dict[str, Any]:
    audit_freeze()
    _require(not output.exists(), "Selected-site manifest already exists")
    phase = validate_phase(localization_root, "localization", _all_localization_sites())
    config = _config()["localization"]["selector"]["eligibility"]
    candidate_evidence = [
        _site_evidence(localization_root, site, block_index)
        for site, block_index in _candidate_sites()
    ]
    positive_site, negative_site = _control_sites()
    positive_directory = _site_directory(
        localization_root, "localization", *positive_site
    )
    negative_directory = _site_directory(
        localization_root, "localization", *negative_site
    )
    positive_rows = _read_jsonl(positive_directory / "response_ledger.jsonl")
    negative_rows = _read_jsonl(negative_directory / "response_ledger.jsonl")
    positive_median = float(
        np.median([float(row["necessity_drop_js"]) for row in positive_rows])
    )
    positive_maximum_necessity_js = max(
        float(row["necessity_js"]) for row in positive_rows
    )
    positive_maximum_sufficiency_error_js = max(
        float(row["sufficiency_error_js"]) for row in positive_rows
    )
    negative_absolute_median = float(
        np.median([abs(float(row["necessity_drop_js"])) for row in negative_rows])
    )
    positive_pass = (
        positive_median
        >= float(config["positive_control_necessity_drop_median_minimum"])
        and positive_maximum_necessity_js
        <= float(config["positive_control_maximum_necessity_js"])
        and positive_maximum_sufficiency_error_js
        <= float(config["positive_control_maximum_sufficiency_error_js"])
    )
    negative_pass = negative_absolute_median <= float(
        config["negative_control_absolute_necessity_drop_median_maximum"]
    )
    eligible: list[dict[str, Any]] = []
    for evidence in candidate_evidence:
        fidelity = float(evidence["maximum_restoration_error_logit_rms"]) <= float(
            config["maximum_restoration_logit_rms_error"]
        ) and float(evidence["maximum_restoration_error_js"]) <= float(
            config["maximum_restoration_js_error"]
        )
        evidence["eligible"] = bool(fidelity and positive_pass and negative_pass)
        if evidence["eligible"]:
            eligible.append(evidence)
    _require(eligible, "No T14-C candidate passed engineering eligibility")
    order = {site: index for index, site in enumerate(_candidate_sites())}
    selected = sorted(
        eligible,
        key=lambda row: (
            -float(row["median_target_necessity_excess_js"]),
            order[(str(row["site"]), int(row["block_index"]))],
        ),
    )[0]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "selected_site_bound_before_c1_v2_materialization",
        "localization_root": str(localization_root.resolve()),
        "localization_summary_sha256": phase["summary_sha256"],
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "causal_executor_and_analyzer_sha256": _sha256(Path(__file__)),
        "selected_site": {
            "site": selected["site"],
            "block_index": selected["block_index"],
        },
        "selected_score": selected["median_target_necessity_excess_js"],
        "candidate_evidence": candidate_evidence,
        "control_evidence": {
            "positive_control_median_necessity_drop_js": positive_median,
            "positive_control_maximum_necessity_js": positive_maximum_necessity_js,
            "positive_control_maximum_sufficiency_error_js": (
                positive_maximum_sufficiency_error_js
            ),
            "positive_control_pass": positive_pass,
            "upstream_sham_median_absolute_necessity_drop_js": negative_absolute_median,
            "upstream_sham_pass": negative_pass,
        },
        "c1_v2_target_rows_generated": 0,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output, manifest)
    return {
        "status": "selected_site_bound",
        "site": selected["site"],
        "block_index": selected["block_index"],
        "manifest_sha256": _sha256(output),
        "c1_v2_target_rows_generated": 0,
    }


def audit_site_manifest() -> dict[str, Any]:
    audit_freeze()
    path = _root() / SITE_MANIFEST_PATH
    manifest = _read_json(path)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Site manifest changed")
    _require(
        manifest.get("status") == "selected_site_bound_before_c1_v2_materialization",
        "Selected site is not frozen",
    )
    _require(
        manifest["causal_executor_and_analyzer_sha256"] == _sha256(Path(__file__)),
        "Causal executor/analyzer changed after site selection",
    )
    localization_root = Path(str(manifest["localization_root"]))
    summary = _phase_summary_path(localization_root, "localization")
    _require(
        _sha256(summary) == manifest["localization_summary_sha256"],
        "Localization summary changed after selection",
    )
    selected = manifest["selected_site"]
    site = (str(selected["site"]), int(selected["block_index"]))
    _require(site in _candidate_sites(), "Selected site is outside frozen roster")
    return {
        "status": "pass",
        "site": site[0],
        "block_index": site[1],
        "manifest_sha256": _sha256(path),
        "localization_root": str(localization_root),
    }


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


def _pushed_site_gate() -> dict[str, str]:
    protected = (
        SITE_MANIFEST_PATH.as_posix(),
        FREEZE_PATH.as_posix(),
        CONFIG_PATH.as_posix(),
        "scripts/emoji_steering_causal_path_v0.py",
        "docs/EMOJI_STEERING_CAUSAL_PATH_V0.md",
        "docs/EMOJI_STEERING_CAUSAL_PATH_V0.ja.md",
        "tests/test_emoji_steering_causal_path_v0.py",
    )
    status = _git_value("status", "--porcelain", "--", *protected)
    _require(not status, "T14-C protected files are not committed")
    head = _git_value("rev-parse", "HEAD")
    remote = _git_value("rev-parse", "origin/main")
    _require(head == remote, "T14-C selected-site commit is not pushed to origin/main")
    _require(
        _git_value("ls-files", SITE_MANIFEST_PATH.as_posix())
        == SITE_MANIFEST_PATH.as_posix(),
        "Selected-site manifest is not tracked",
    )
    return {"head_commit": head, "origin_main_commit": remote}


def materialize_bank(output: Path, receipt_output: Path) -> dict[str, Any]:
    site = audit_site_manifest()
    git = _pushed_site_gate()
    _require(not output.exists(), "C1 v2 target bank already exists")
    _require(not receipt_output.exists(), "C1 v2 target receipt already exists")
    seed = int(_config()["c1_v2_bank"]["generator_seed"])
    rows = _validate_target_rows(build_target_rows(seed), 192, c1_v2=True)
    public_prompts = {row["prompt"] for row in _public_targets()}
    _require(
        not any(row["prompt"] in public_prompts for row in rows),
        "C1 v2 overlaps the public localization bank",
    )
    _write_jsonl(output, rows)
    counts = {
        group: sum(row["group"] == group for row in rows) for group in _TARGET_GROUPS
    }
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "c1_v2_materialized_after_selected_site_push",
        "target_bank_path": str(output.resolve()),
        "target_bank_sha256": _sha256(output),
        "target_rows": len(rows),
        "stratum_counts": counts,
        "generator_seed": seed,
        "selected_site_manifest_sha256": site["manifest_sha256"],
        "site": site["site"],
        "block_index": site["block_index"],
        **git,
        "prompt_bodies_printed": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(receipt_output, receipt)
    return {
        "status": receipt["status"],
        "target_rows": receipt["target_rows"],
        "stratum_counts": counts,
        "target_bank_sha256": receipt["target_bank_sha256"],
        "receipt_sha256": _sha256(receipt_output),
        "prompt_bodies_printed": False,
    }


def _load_c1_v2_bank(target_bank: Path, target_receipt: Path) -> list[dict[str, str]]:
    receipt = _read_json(target_receipt)
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "C1 v2 receipt changed")
    _require(
        receipt.get("status") == "c1_v2_materialized_after_selected_site_push",
        "C1 v2 materialization gate incomplete",
    )
    _require(
        Path(str(receipt["target_bank_path"])).resolve() == target_bank.resolve(),
        "C1 v2 target path changed",
    )
    _require(
        _sha256(target_bank) == receipt["target_bank_sha256"],
        "C1 v2 target bank hash changed",
    )
    site = audit_site_manifest()
    _require(
        receipt["selected_site_manifest_sha256"] == site["manifest_sha256"],
        "C1 v2 selected-site binding changed",
    )
    return _validate_target_rows(_read_jsonl(target_bank), 192, c1_v2=True)


def run_confirmation(
    *,
    output_root: Path,
    source_run_root: Path,
    preflight_directory: Path,
    target_bank: Path,
    target_receipt: Path,
) -> dict[str, Any]:
    site = audit_site_manifest()
    _pushed_site_gate()
    targets = _load_c1_v2_bank(target_bank, target_receipt)
    return _run_phase(
        phase="confirmation",
        sites=((str(site["site"]), int(site["block_index"])),),
        targets=targets,
        output_root=output_root,
        source_run_root=source_run_root,
        preflight_directory=preflight_directory,
    )


def _bootstrap_median(
    values: np.ndarray,
    groups: Sequence[str],
    *,
    replicates: int,
    seed: int,
) -> np.ndarray:
    _require(values.shape == (192,), "Bootstrap target vector changed")
    strata = []
    group_array = np.asarray(groups, dtype=object)
    for group in _TARGET_GROUPS:
        indices = np.flatnonzero(group_array == group)
        _require(indices.shape == (16,), "Bootstrap stratum changed")
        strata.append(indices)
    rng = np.random.default_rng(seed)
    results: list[np.ndarray] = []
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        sampled = np.concatenate(
            [
                indices[rng.integers(0, len(indices), size=(count, len(indices)))]
                for indices in strata
            ],
            axis=1,
        )
        results.append(np.median(values[sampled], axis=1))
    output = np.concatenate(results)
    _require(output.shape == (replicates,), "Bootstrap replicate count changed")
    return output


def _sign_flip_p_value(values: np.ndarray, *, draws: int, seed: int) -> float:
    _require(values.shape == (192,), "Sign-flip target vector changed")
    observed = float(np.median(values))
    rng = np.random.default_rng(seed)
    extreme = 0
    for start in range(0, draws, 1000):
        count = min(1000, draws - start)
        signs = rng.integers(0, 2, size=(count, len(values)), dtype=np.int8)
        signs = signs.astype(np.float64) * 2.0 - 1.0
        null_values = np.median(signs * values[None, :], axis=1)
        extreme += int(np.count_nonzero(null_values >= observed))
    return float((extreme + 1) / (draws + 1))


def analyze_confirmation(*, output_root: Path, output: Path) -> dict[str, Any]:
    site = audit_site_manifest()
    selected = (str(site["site"]), int(site["block_index"]))
    phase = validate_phase(output_root, "confirmation", (selected,))
    directory = _site_directory(output_root, "confirmation", *selected)
    rows = _read_jsonl(directory / "response_ledger.jsonl")
    target_values = _target_estimands(rows)
    _require(len(target_values) == 192, "C1 v2 target estimands changed")
    groups = [str(row["target_group"]) for row in target_values]
    uncertainty = _config()["causal_confirmation"]["uncertainty"]
    randomization = _config()["causal_confirmation"]["randomization"]
    floors = _config()["causal_confirmation"]["practical_floors"]
    specifications = (
        ("treatment", "treatment_excess_js", "treatment_excess_js"),
        ("necessity", "necessity_excess_js", "necessity_excess_js"),
        ("sufficiency", "sufficiency_excess_js", "sufficiency_excess_js"),
    )
    estimands: dict[str, dict[str, Any]] = {}
    components_pass = []
    for name, key, floor_key in specifications:
        values = np.asarray([float(row[key]) for row in target_values])
        bootstrap = _bootstrap_median(
            values,
            groups,
            replicates=int(uncertainty["replicates"]),
            seed=int(uncertainty["seed"])
            + int(uncertainty["component_seed_offsets"][name]),
        )
        lower = float(np.quantile(bootstrap, 0.025))
        upper = float(np.quantile(bootstrap, 0.975))
        p_value = _sign_flip_p_value(
            values,
            draws=int(randomization["draws"]),
            seed=int(randomization["seed"])
            + int(randomization["component_seed_offsets"][name]),
        )
        floor = float(floors[floor_key])
        passed = lower > floor and p_value < 0.05
        components_pass.append(passed)
        estimands[name] = {
            "target_level_aggregate": "median",
            "point_estimate": float(np.median(values)),
            "bootstrap_95_percent_interval": [lower, upper],
            "practical_floor": floor,
            "one_sided_sign_flip_p_value_against_zero": p_value,
            "component_pass": passed,
        }
    receipt = _read_json(directory / "receipt.json")
    eligibility = _config()["localization"]["selector"]["eligibility"]
    restoration_pass = float(receipt["maximum_restoration_error_logit_rms"]) <= float(
        eligibility["maximum_restoration_logit_rms_error"]
    ) and float(receipt["maximum_restoration_error_js"]) <= float(
        eligibility["maximum_restoration_js_error"]
    )
    zero_pass = float(receipt["maximum_explicit_zero_js"]) <= 1.0e-12
    site_manifest = _read_json(_root() / SITE_MANIFEST_PATH)
    sham_pass = bool(site_manifest["control_evidence"]["upstream_sham_pass"])
    decision = bool(
        all(components_pass) and restoration_pass and zero_pass and sham_pass
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_iut_pass" if decision else "causal_iut_non_rejecting",
        "claim_boundary": _config()["claim_boundary"],
        "selected_site": {"site": selected[0], "block_index": selected[1]},
        "confirmation_summary_sha256": phase["summary_sha256"],
        "principal_sampling_unit": "target_prompt",
        "target_rows": 192,
        "estimands": estimands,
        "engineering_gates": {
            "restoration_pass": restoration_pass,
            "maximum_restoration_error_js": float(
                receipt["maximum_restoration_error_js"]
            ),
            "maximum_restoration_error_logit_rms": float(
                receipt["maximum_restoration_error_logit_rms"]
            ),
            "explicit_zero_pass": zero_pass,
            "maximum_explicit_zero_js": float(receipt["maximum_explicit_zero_js"]),
            "upstream_sham_pass_from_frozen_localization": sham_pass,
        },
        "intersection_union_decision": decision,
        "confirmatory_claim_authorized": decision,
        "forbidden_claims": _config()["forbidden_claims"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output, result)
    return {
        "status": result["status"],
        "intersection_union_decision": decision,
        "output_sha256": _sha256(output),
        "confirmatory_claim_authorized": decision,
    }


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    commands = value.add_subparsers(dest="command", required=True)
    commands.add_parser("audit-design")
    preflight = commands.add_parser("write-design-preflight")
    preflight.add_argument(
        "--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH
    )
    freeze_parser = commands.add_parser("freeze")
    freeze_parser.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    commands.add_parser("audit-freeze")
    localization = commands.add_parser("run-localization")
    localization.add_argument("--output-root", required=True, type=Path)
    localization.add_argument("--source-run-root", required=True, type=Path)
    localization.add_argument("--preflight-directory", required=True, type=Path)
    validate_localization = commands.add_parser("validate-localization")
    validate_localization.add_argument("--output-root", required=True, type=Path)
    selector = commands.add_parser("select-site")
    selector.add_argument("--localization-root", required=True, type=Path)
    selector.add_argument("--output", type=Path, default=_root() / SITE_MANIFEST_PATH)
    commands.add_parser("audit-site-manifest")
    materialize = commands.add_parser("materialize-bank")
    materialize.add_argument("--output", required=True, type=Path)
    materialize.add_argument("--receipt-output", required=True, type=Path)
    confirmation = commands.add_parser("run-confirmation")
    confirmation.add_argument("--output-root", required=True, type=Path)
    confirmation.add_argument("--source-run-root", required=True, type=Path)
    confirmation.add_argument("--preflight-directory", required=True, type=Path)
    confirmation.add_argument("--target-bank", required=True, type=Path)
    confirmation.add_argument("--target-receipt", required=True, type=Path)
    validate_confirmation = commands.add_parser("validate-confirmation")
    validate_confirmation.add_argument("--output-root", required=True, type=Path)
    analysis = commands.add_parser("analyze-confirmation")
    analysis.add_argument("--output-root", required=True, type=Path)
    analysis.add_argument("--output", required=True, type=Path)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "write-design-preflight":
        result = write_design_preflight(args.output)
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run-localization":
        result = run_localization(
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            preflight_directory=args.preflight_directory,
        )
    elif args.command == "validate-localization":
        result = validate_phase(
            args.output_root, "localization", _all_localization_sites()
        )
    elif args.command == "select-site":
        result = select_site(args.localization_root, args.output)
    elif args.command == "audit-site-manifest":
        result = audit_site_manifest()
    elif args.command == "materialize-bank":
        result = materialize_bank(args.output, args.receipt_output)
    elif args.command == "run-confirmation":
        result = run_confirmation(
            output_root=args.output_root,
            source_run_root=args.source_run_root,
            preflight_directory=args.preflight_directory,
            target_bank=args.target_bank,
            target_receipt=args.target_receipt,
        )
    elif args.command == "validate-confirmation":
        site = audit_site_manifest()
        result = validate_phase(
            args.output_root,
            "confirmation",
            ((str(site["site"]), int(site["block_index"])),),
        )
    else:
        result = analyze_confirmation(output_root=args.output_root, output=args.output)
    _print(result)


if __name__ == "__main__":
    main()
