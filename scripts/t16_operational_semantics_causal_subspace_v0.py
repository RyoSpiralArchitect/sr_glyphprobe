#!/usr/bin/env python3
"""Freeze and run T16 operational semantics and causal-subspace tests."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from functools import cache
import hashlib
import itertools
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


PROTOCOL_ID = "glyphprobe-t16-operational-semantics-causal-subspace-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/t16_operational_semantics_causal_subspace_v0.yaml")
PANEL_PATH = Path("data/panels/emoji_operational_semantics_axes_v0.json")
T15B_PANEL_PATH = Path("data/panels/emoji_word_incongruence_axes_v1.json")
FREEZE_PATH = Path("data/manifests/t16_operational_semantics_causal_subspace_v0.json")
VALIDATION_DIRECTORY = Path("validation/t16_operational_semantics_causal_subspace_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_DIRECTORY = VALIDATION_DIRECTORY / "tokenizers"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
BEHAVIOR_ROLES = ("gemma2_2b_it_bf16", "mistral7b_instruct_v03_bf16")
CAUSAL_ROLE = "mistral7b_instruct_v03_bf16"
POLES = ("pole_a", "pole_b")
T15B_POLES = ("positive", "negative")
MAPPINGS = ("correct_is_A", "correct_is_B")
SITE_INDICES = (6, 7)
STATIC_ASSETS = (
    "configs/t16_operational_semantics_causal_subspace_v0.yaml",
    "data/panels/emoji_operational_semantics_axes_v0.json",
    "data/panels/emoji_word_incongruence_axes_v1.json",
    "docs/T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0.md",
    "docs/T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0.ja.md",
    "scripts/t16_operational_semantics_causal_subspace_v0.py",
    "tests/test_t16_operational_semantics_causal_subspace_v0.py",
    "validation/t16_operational_semantics_causal_subspace_v0/design_preflight.json",
)
FROZEN_ASSETS = (
    *STATIC_ASSETS,
    "validation/t16_operational_semantics_causal_subspace_v0/tokenizers/gemma2_2b_it_bf16.json",
    "validation/t16_operational_semantics_causal_subspace_v0/tokenizers/mistral7b_instruct_v03_bf16.json",
    "validation/t16_operational_semantics_causal_subspace_v0/tokenizer_preflight.json",
)


class T16Error(RuntimeError):
    """Raised when a T16 design, execution, or analysis gate fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T16Error(message)


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
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16 config protocol changed")
    return value


@cache
def _panel() -> dict[str, Any]:
    value = _read_json(_root() / PANEL_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T16 panel protocol changed")
    return value


@cache
def _axes() -> tuple[dict[str, Any], ...]:
    axes = tuple(_panel()["axes"])
    order = tuple(str(value) for value in _panel()["axis_order"])
    _require(tuple(str(axis["id"]) for axis in axes) == order, "Axis order changed")
    return axes


@cache
def _t15b_axes() -> tuple[dict[str, Any], ...]:
    panel = _read_json(_root() / T15B_PANEL_PATH)
    order = tuple(str(value) for value in panel["axis_order"])
    axes = tuple(panel["axes"])
    _require(tuple(str(axis["id"]) for axis in axes) == order, "T15-B axes changed")
    return axes


def _behavior_records(task: str) -> list[dict[str, Any]]:
    templates = tuple(str(value) for value in _config()["behavior"]["templates"][task])
    rows: list[dict[str, Any]] = []
    for axis in _axes():
        for emoji_pole in POLES:
            other_pole = POLES[1 - POLES.index(emoji_pole)]
            emoji = str(axis[emoji_pole]["emoji"])
            if task == "meaning_choice":
                combinations = [(emoji_pole, "match")]
            else:
                combinations = [(word_pole, "match" if word_pole == emoji_pole else "mismatch") for word_pole in POLES]
            for word_pole, truth in combinations:
                for template_index, template in enumerate(templates):
                    for mapping in MAPPINGS:
                        if task == "meaning_choice":
                            correct = str(axis[emoji_pole]["word"])
                            incorrect = str(axis[other_pole]["word"])
                            option_a, option_b = (
                                (correct, incorrect)
                                if mapping == "correct_is_A"
                                else (incorrect, correct)
                            )
                            prompt = template.format(
                                emoji=emoji, option_a=option_a, option_b=option_b
                            )
                        else:
                            word = str(axis[word_pole]["word"])
                            correct = truth
                            incorrect = "mismatch" if truth == "match" else "match"
                            option_a, option_b = (
                                (correct, incorrect)
                                if mapping == "correct_is_A"
                                else (incorrect, correct)
                            )
                            prompt = template.format(
                                emoji=emoji,
                                word=word,
                                option_a=option_a,
                                option_b=option_b,
                            )
                        correct_label = "A" if mapping == "correct_is_A" else "B"
                        rows.append(
                            {
                                "record_index": len(rows),
                                "task": task,
                                "axis_id": str(axis["id"]),
                                "emoji_pole": emoji_pole,
                                "word_pole": word_pole,
                                "truth": truth,
                                "template_index": template_index,
                                "answer_mapping": mapping,
                                "correct_label": correct_label,
                                "incorrect_label": "B" if correct_label == "A" else "A",
                                "user_prompt": prompt,
                            }
                        )
    return rows


def _causal_target_records() -> list[dict[str, Any]]:
    templates = tuple(
        str(value)
        for value in _config()["behavior"]["templates"]["congruence_judgment"]
    )
    selected = tuple(int(value) for value in _config()["causal_subspace"]["target_templates"])
    rows: list[dict[str, Any]] = []
    for axis in _t15b_axes():
        for emoji_pole in T15B_POLES:
            for word_pole in T15B_POLES:
                truth = "match" if emoji_pole == word_pole else "mismatch"
                emoji = str(axis[emoji_pole]["emoji"])
                word = str(axis[word_pole]["word"])
                for template_index in selected:
                    template = templates[template_index]
                    for mapping in MAPPINGS:
                        correct = truth
                        incorrect = "mismatch" if truth == "match" else "match"
                        option_a, option_b = (
                            (correct, incorrect)
                            if mapping == "correct_is_A"
                            else (incorrect, correct)
                        )
                        prompt = template.format(
                            emoji=emoji,
                            word=word,
                            option_a=option_a,
                            option_b=option_b,
                        )
                        correct_label = "A" if mapping == "correct_is_A" else "B"
                        match_label = correct_label if truth == "match" else ("B" if correct_label == "A" else "A")
                        mismatch_label = "B" if match_label == "A" else "A"
                        rows.append(
                            {
                                "target_index": len(rows),
                                "axis_id": str(axis["id"]),
                                "emoji_pole": emoji_pole,
                                "word_pole": word_pole,
                                "truth": truth,
                                "template_index": template_index,
                                "answer_mapping": mapping,
                                "correct_label": correct_label,
                                "incorrect_label": "B" if correct_label == "A" else "A",
                                "match_label": match_label,
                                "mismatch_label": mismatch_label,
                                "user_prompt": prompt,
                            }
                        )
    return rows


def _render_prompt(tokenizer: Any, user_prompt: str) -> str:
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": user_prompt}],
        tokenize=False,
        add_generation_prompt=True,
    )
    _require(isinstance(rendered, str) and rendered, "Chat template returned no text")
    return rendered


def _token_ids(tokenizer: Any, text: str) -> list[int]:
    values = tokenizer.encode(text, add_special_tokens=False)
    return [int(value) for value in values]


def _bound_input_hashes() -> dict[str, str]:
    config = _config()
    observed: dict[str, str] = {}
    for key in ("operational_axes", "t15b_axes", "t15b_closeout"):
        binding = config["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"Bound T16 input missing: {key}")
        actual = _sha256(path)
        if "sha256" in binding:
            _require(actual == str(binding["sha256"]), f"Bound input changed: {key}")
        observed[key] = actual
    return observed


def audit_design() -> dict[str, Any]:
    config = _config()
    observed = _bound_input_hashes()
    _require(len(_axes()) == 8, "Operational axis count changed")
    _require(len(_t15b_axes()) == 8, "T15-B axis count changed")
    _require(
        not ({axis["id"] for axis in _axes()} & {axis["id"] for axis in _t15b_axes()}),
        "Operational axes overlap T15-B axis labels",
    )
    _require(
        tuple(config["models"]["behavior_order"]) == BEHAVIOR_ROLES,
        "Behavior model order changed",
    )
    _require(config["models"]["causal_role"] == CAUSAL_ROLE, "Causal role changed")
    _require(tuple(config["causal_subspace"]["source_site_indices"]) == SITE_INDICES, "Causal sites changed")
    _require(tuple(config["causal_subspace"]["source_block_indices"]) == (27, 31), "Causal blocks changed")
    _require(t13.layer_indices(CAUSAL_ROLE)[6:] == (27, 31), "Mistral layer mapping changed")
    counts = {
        "meaning_choice_rows_per_model": len(_behavior_records("meaning_choice")),
        "congruence_judgment_rows_per_model": len(_behavior_records("congruence_judgment")),
        "causal_target_rows": len(_causal_target_records()),
        "causal_conditions_per_target_per_site": 21,
        "causal_response_rows": len(_causal_target_records()) * len(SITE_INDICES) * 21,
    }
    _require(counts["meaning_choice_rows_per_model"] == 128, "Meaning grid changed")
    _require(counts["congruence_judgment_rows_per_model"] == 256, "Congruence grid changed")
    _require(counts["causal_target_rows"] == 128, "Causal target grid changed")
    closeout = _read_json(
        _root() / str(config["source_bindings"]["t15b_closeout"]["path"])
    )
    _require(
        closeout.get("status")
        == config["source_bindings"]["t15b_closeout"]["expected_status"],
        "T15-B closeout status changed",
    )
    _require(closeout.get("causal_claim_authorized") is False, "T15-B causal boundary changed")
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t16_model_forwards",
        "bound_inputs": observed,
        "behavior_roles": list(BEHAVIOR_ROLES),
        "causal_role": CAUSAL_ROLE,
        "operational_axis_ids": [str(axis["id"]) for axis in _axes()],
        "t15b_axis_ids": [str(axis["id"]) for axis in _t15b_axes()],
        "counts": counts,
        "model_forwards": 0,
        "unrestricted_semantic_understanding_claim_authorized": False,
        "unique_or_complete_circuit_claim_authorized": False,
    }


def write_design_preflight(output: Path) -> dict[str, Any]:
    result = audit_design()
    _write_json(output, result)
    return result


def _locate_snapshot(role: str, supplied: Path | None) -> Path:
    path = supplied if supplied is not None else t13.t11._locate_local_snapshot(role)
    resolved = path.resolve()
    spec = t10._model_spec(role)
    _require(resolved.is_dir(), f"Model snapshot missing: {role}")
    _require(resolved.name == str(spec["revision"]), f"Model revision changed: {role}")
    return resolved


def tokenizer_preflight(role: str, output: Path, model_path: Path | None) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoTokenizer

    audit_design()
    _require(role in BEHAVIOR_ROLES, f"Unknown T16 role: {role}")
    snapshot = _locate_snapshot(role, model_path)
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    label_ids = {label: _token_ids(tokenizer, label) for label in ("A", "B")}
    _require(all(len(values) == 1 for values in label_ids.values()), "Answer label is not one token")
    records = _behavior_records("meaning_choice") + _behavior_records("congruence_judgment")
    if role == CAUSAL_ROLE:
        records += _causal_target_records()
    prompts = [_render_prompt(tokenizer, str(record["user_prompt"])) for record in records]
    prompt_ids = [_token_ids(tokenizer, prompt) for prompt in prompts]
    for prompt, ids in zip(prompts, prompt_ids, strict=True):
        for label in ("A", "B"):
            combined = _token_ids(tokenizer, prompt + label)
            _require(
                combined[: len(ids)] == ids and combined[len(ids) :] == label_ids[label],
                f"Answer token boundary changed: {role}/{label}",
            )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_preflight_pass_zero_t16_model_forwards",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "revision": t10._model_spec(role)["revision"],
        "artifact": model_artifact_receipt(snapshot),
        "tokenizer_class": type(tokenizer).__name__,
        "answer_token_ids": {key: values[0] for key, values in label_ids.items()},
        "prompt_sequences": len(prompts),
        "ordered_user_prompt_sha256": _canonical_sha256([record["user_prompt"] for record in records]),
        "ordered_rendered_prompt_sha256": _canonical_sha256(prompts),
        "ordered_token_ids_sha256": _canonical_sha256(prompt_ids),
        "minimum_token_count": min(len(ids) for ids in prompt_ids),
        "maximum_token_count": max(len(ids) for ids in prompt_ids),
        "model_forwards": 0,
    }
    _write_json(output, value)
    return value


def aggregate_preflight(directory: Path, output: Path) -> dict[str, Any]:
    audit_design()
    roles: dict[str, Any] = {}
    for role in BEHAVIOR_ROLES:
        path = directory / f"{role}.json"
        value = _read_json(path)
        _require(value.get("protocol_id") == PROTOCOL_ID, "Tokenizer protocol changed")
        _require(value.get("status") == "tokenizer_preflight_pass_zero_t16_model_forwards", "Tokenizer preflight incomplete")
        _require(value.get("model_role") == role, "Tokenizer role changed")
        roles[role] = {
            "receipt_sha256": _sha256(path),
            "artifact_manifest_sha256": value["artifact"]["manifest_sha256"],
            "answer_token_ids": value["answer_token_ids"],
            "ordered_rendered_prompt_sha256": value["ordered_rendered_prompt_sha256"],
            "ordered_token_ids_sha256": value["ordered_token_ids_sha256"],
            "prompt_sequences": value["prompt_sequences"],
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "all_tokenizer_preflights_pass_zero_t16_model_forwards",
        "model_roles": list(BEHAVIOR_ROLES),
        "roles": roles,
        "model_forwards": 0,
    }
    _write_json(output, result)
    return result


def freeze(output: Path) -> dict[str, Any]:
    design = audit_design()
    _require((_root() / TOKENIZER_PREFLIGHT_PATH).is_file(), "Tokenizer aggregate missing")
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"Frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t16_model_forwards",
        "assets": assets,
        "expected_counts": design["counts"],
        "behavior_roles": list(BEHAVIOR_ROLES),
        "causal_role": CAUSAL_ROLE,
        "model_forwards_at_freeze": 0,
        "confirmatory_status": False,
        "unrestricted_semantic_understanding_claim_authorized": False,
        "unique_or_complete_circuit_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def audit_freeze() -> dict[str, Any]:
    design = audit_design()
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Freeze protocol changed")
    _require(value.get("status") == "final_execution_freeze_zero_t16_model_forwards", "Freeze incomplete")
    _require(value.get("expected_counts") == design["counts"], "Frozen counts changed")
    for relative, expected in value["assets"].items():
        asset = _root() / relative
        _require(asset.is_file() and _sha256(asset) == expected, f"Frozen asset changed: {relative}")
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path)}


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
                "status": "yielded_before_new_phase_for_foreign_gpu_contention",
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"]))


def _validate_runtime_tokenizer(role: str, tokenizer: Any, snapshot: Path) -> dict[str, int]:
    from glyphprobe.provenance import model_artifact_receipt

    frozen = _read_json(_root() / TOKENIZER_DIRECTORY / f"{role}.json")
    artifact = model_artifact_receipt(snapshot)
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == frozen["artifact"][key], f"Runtime artifact changed: {role}/{key}")
    labels = {label: _token_ids(tokenizer, label) for label in ("A", "B")}
    _require({key: value[0] for key, value in labels.items()} == frozen["answer_token_ids"], "Answer tokens changed")
    return {key: value[0] for key, value in labels.items()}


def _load_model(role: str, model_preflight_directory: Path, model_path: Path | None) -> tuple[Any, Any, Any, Sequence[Any], dict[str, int], dict[str, Any]]:
    snapshot = _locate_snapshot(role, model_path)
    torch, tokenizer, model, receipt = t13._load_model(role, snapshot, model_preflight_directory)
    label_ids = _validate_runtime_tokenizer(role, tokenizer, snapshot)
    blocks = t10._resolve_attr(model, str(t10._model_spec(role)["expected_block_path"]))
    return torch, tokenizer, model, blocks, label_ids, receipt


def _batch_logits(torch: Any, tokenizer: Any, model: Any, prompts: Sequence[str]) -> np.ndarray:
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    encoded = tokenizer(
        list(prompts),
        add_special_tokens=False,
        padding=True,
        return_tensors="pt",
    )
    device = next(model.parameters()).device
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    with torch.inference_mode():
        output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, return_dict=True)
    return output.logits[:, -1, :].detach().float().cpu().numpy()


def run_behavior_role(*, role: str, output_root: Path, model_preflight_directory: Path, model_path: Path | None) -> dict[str, Any]:
    audit_freeze()
    _require(role in BEHAVIOR_ROLES, f"Unknown behavior role: {role}")
    final = output_root / role / "behavior"
    if final.is_dir():
        return validate_behavior_role(role, output_root)
    _yield_if_contended(output_root, f"before_behavior_model_load_{role}")
    torch, tokenizer, model, _blocks, label_ids, model_receipt = _load_model(role, model_preflight_directory, model_path)
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    batch_size = int(_config()["runtime"]["batch_size"])
    try:
        for task in ("meaning_choice", "congruence_judgment"):
            _yield_if_contended(output_root, f"before_behavior_task_{role}_{task}")
            records = _behavior_records(task)
            for start in range(0, len(records), batch_size):
                batch = records[start : start + batch_size]
                prompts = [_render_prompt(tokenizer, str(record["user_prompt"])) for record in batch]
                logits = _batch_logits(torch, tokenizer, model, prompts)
                for record, values in zip(batch, logits, strict=True):
                    correct = float(values[label_ids[str(record["correct_label"])]] )
                    incorrect = float(values[label_ids[str(record["incorrect_label"])]] )
                    rows.append(
                        {
                            **{key: value for key, value in record.items() if key != "user_prompt"},
                            "schema_version": SCHEMA_VERSION,
                            "protocol_id": PROTOCOL_ID,
                            "model_role": role,
                            "prompt_sha256": hashlib.sha256(str(record["user_prompt"]).encode("utf-8")).hexdigest(),
                            "correct_minus_incorrect_logit": correct - incorrect,
                            "forced_choice_correct": bool(correct > incorrect),
                        }
                    )
    finally:
        del model
        torch.cuda.empty_cache()
    expected = len(_behavior_records("meaning_choice")) + len(_behavior_records("congruence_judgment"))
    _require(len(rows) == expected, "Behavior response count changed")
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not final.exists() and not stage.exists(), "Behavior output collision")
    stage.mkdir(parents=True)
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "behavior_role_complete",
        "model_role": role,
        "response_rows": len(rows),
        "task_counts": dict(Counter(str(row["task"]) for row in rows)),
        "response_ledger_sha256": _sha256(stage / "response_ledger.jsonl"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_receipt": model_receipt,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_behavior_role(role, output_root)


def validate_behavior_role(role: str, output_root: Path) -> dict[str, Any]:
    directory = output_root / role / "behavior"
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Behavior receipt protocol changed")
    _require(receipt.get("status") == "behavior_role_complete", "Behavior role incomplete")
    _require(receipt.get("model_role") == role, "Behavior role changed")
    ledger = directory / "response_ledger.jsonl"
    _require(_sha256(ledger) == receipt["response_ledger_sha256"], "Behavior ledger changed")
    rows = _read_jsonl(ledger)
    expected = len(_behavior_records("meaning_choice")) + len(_behavior_records("congruence_judgment"))
    _require(len(rows) == expected == int(receipt["response_rows"]), "Behavior row count changed")
    _require(all(math.isfinite(float(row["correct_minus_incorrect_logit"])) for row in rows), "Behavior ledger nonfinite")
    return {"status": "pass", "model_role": role, "response_rows": len(rows), "receipt_sha256": _sha256(directory / "receipt.json")}


def audit_behavior(output_root: Path) -> dict[str, Any]:
    audit_freeze()
    roles = [validate_behavior_role(role, output_root) for role in BEHAVIOR_ROLES]
    return {
        "status": "behavior_complete_scientific_open_authorized",
        "roles_complete": len(roles),
        "response_rows": sum(int(row["response_rows"]) for row in roles),
        "generation_calls": 0,
    }


def _bootstrap_axis_median(values: np.ndarray, replicates: int, seed: int) -> np.ndarray:
    _require(values.shape == (8,), "Axis bootstrap requires eight values")
    rng = np.random.default_rng(seed)
    chunks: list[np.ndarray] = []
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        sampled = values[rng.integers(0, 8, size=(count, 8))]
        chunks.append(np.median(sampled, axis=1))
    return np.concatenate(chunks)


def _exact_sign_flip_p(values: np.ndarray) -> float:
    _require(values.shape == (8,), "Exact sign flip requires eight values")
    observed = float(np.mean(values))
    null = []
    for bits in itertools.product((-1.0, 1.0), repeat=8):
        null.append(float(np.mean(values * np.asarray(bits))))
    return float(np.mean(np.asarray(null) >= observed - 1e-15))


def _interval_and_test(values: np.ndarray, seed: int) -> dict[str, Any]:
    replicates = int(_config()["analysis"]["bootstrap_replicates"])
    bootstrap = _bootstrap_axis_median(values, replicates, seed)
    return {
        "axis_values": [float(value) for value in values],
        "axis_median": float(np.median(values)),
        "bootstrap_95_percent_interval": [float(np.quantile(bootstrap, 0.025)), float(np.quantile(bootstrap, 0.975))],
        "exact_one_sided_sign_flip_p_value": _exact_sign_flip_p(values),
    }


def analyze_behavior(output_root: Path, output: Path) -> dict[str, Any]:
    audit = audit_behavior(output_root)
    axis_order = [str(axis["id"]) for axis in _axes()]
    seed = int(_config()["analysis"]["bootstrap_seed"])
    cells: dict[str, Any] = {}
    passed = []
    offset = 0
    for role in BEHAVIOR_ROLES:
        rows = _read_jsonl(output_root / role / "behavior" / "response_ledger.jsonl")
        for task in ("meaning_choice", "congruence_judgment"):
            values = np.asarray([
                np.median([float(row["correct_minus_incorrect_logit"]) for row in rows if row["task"] == task and row["axis_id"] == axis_id])
                for axis_id in axis_order
            ])
            result = _interval_and_test(values, seed + offset)
            threshold = 0.0125
            cell_pass = result["bootstrap_95_percent_interval"][0] > 0.0 and result["exact_one_sided_sign_flip_p_value"] <= threshold
            result["bonferroni_one_sided_alpha"] = threshold
            result["cell_pass"] = cell_pass
            result["forced_choice_accuracy"] = float(np.mean([bool(row["forced_choice_correct"]) for row in rows if row["task"] == task]))
            cells[f"{role}/{task}"] = result
            passed.append(cell_pass)
            offset += 1
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "behavior_analysis_complete",
        "audit": audit,
        "cells": cells,
        "decision": "operational_association_and_congruence_supported" if all(passed) else "operational_behavior_gate_not_supported",
        "all_four_cells_pass": bool(all(passed)),
        "claim_boundary": _config()["claim_boundary"],
        "unrestricted_semantic_understanding_claim_authorized": False,
        "natural_language_contradiction_detection_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def _rms(vector: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(vector, dtype=np.float64))))


def _verify_t15b_source(source_directory: Path) -> tuple[list[dict[str, Any]], np.ndarray]:
    binding = _config()["source_bindings"]["t15b_source"]
    _require(source_directory.is_dir(), "T15-B source directory missing")
    for name, expected in binding["expected_files"].items():
        path = source_directory / str(name)
        _require(path.is_file() and _sha256(path) == str(expected), f"T15-B source changed: {name}")
    receipt = _read_json(source_directory / "receipt.json")
    _require(receipt.get("status") == "source_capture_complete", "T15-B source incomplete")
    _require(receipt.get("model_role") == CAUSAL_ROLE, "T15-B source role changed")
    catalog = _read_jsonl(source_directory / "direction_catalog.jsonl")
    directions = np.load(source_directory / "directions.npy", allow_pickle=False)
    _require(directions.shape == (1280, 4096), "T15-B direction array shape changed")
    _require(len(catalog) == len(directions), "T15-B catalog shape changed")
    return catalog, directions.astype(np.float64)


def _matching_rows(catalog: Sequence[Mapping[str, Any]], true_row: Mapping[str, Any], kind: str) -> list[Mapping[str, Any]]:
    keys = ("site_index", "axis_id", "source_order", "held_out_wrapper_index")
    return [row for row in catalog if row["direction_kind"] == kind and all(row[key] == true_row[key] for key in keys)]


def _source_subspaces(source_directory: Path) -> tuple[dict[int, dict[str, dict[str, np.ndarray]]], dict[str, Any]]:
    catalog, directions = _verify_t15b_source(source_directory)
    result: dict[int, dict[str, dict[str, np.ndarray]]] = {}
    diagnostics: dict[str, Any] = {}
    tolerance = 1.0e-6
    axis_ids = [str(axis["id"]) for axis in _t15b_axes()]
    for site_index in SITE_INDICES:
        site_values: dict[str, dict[str, np.ndarray]] = {}
        for axis_id in axis_ids:
            true_rows = [row for row in catalog if row["direction_kind"] == "true_conflict" and int(row["site_index"]) == site_index and row["axis_id"] == axis_id]
            _require(len(true_rows) == 8, f"True source roster changed: {site_index}/{axis_id}")
            full_parts: list[np.ndarray] = []
            residual_parts: list[np.ndarray] = []
            projection_parts: list[np.ndarray] = []
            cross_parts: dict[int, list[np.ndarray]] = {shift: [] for shift in range(1, 8)}
            ranks: list[int] = []
            for true_row in true_rows:
                cross = _matching_rows(catalog, true_row, "cross_axis_null")
                emoji_main = _matching_rows(catalog, true_row, "emoji_main")
                word_main = _matching_rows(catalog, true_row, "word_main")
                _require(len(cross) == 7 and len(emoji_main) == len(word_main) == 1, "Nuisance roster changed")
                nuisance_rows = [*cross, *emoji_main, *word_main]
                nuisance = np.stack([directions[int(row["direction_index"])] for row in nuisance_rows])
                scales = np.sqrt(np.mean(np.square(nuisance), axis=1))
                _require(bool(np.all(scales > 0)), "Degenerate nuisance direction")
                normalized = nuisance / scales[:, None]
                _u, singular, vt = np.linalg.svd(normalized, full_matrices=False)
                rank = int(np.count_nonzero(singular > singular[0] * tolerance))
                ranks.append(rank)
                basis = vt[:rank]
                full = directions[int(true_row["direction_index"])]
                projection = basis.T @ (basis @ full)
                residual = full - projection
                full_parts.append(full)
                projection_parts.append(projection)
                residual_parts.append(residual)
                for row in cross:
                    cross_parts[int(row["shift"])].append(directions[int(row["direction_index"])])
            full_axis = np.mean(np.stack(full_parts), axis=0)
            residual_axis = np.mean(np.stack(residual_parts), axis=0)
            projection_axis = np.mean(np.stack(projection_parts), axis=0)
            restoration = _rms(full_axis - residual_axis - projection_axis)
            full_rms = _rms(full_axis)
            _require(full_rms > 0 and restoration <= 1.0e-6, "Source decomposition restoration failed")
            vectors = {
                "full": full_axis / full_rms,
                "residual": residual_axis / full_rms,
                "projection": projection_axis / full_rms,
            }
            for shift, parts in cross_parts.items():
                cross_axis = np.mean(np.stack(parts), axis=0)
                cross_rms = _rms(cross_axis)
                _require(cross_rms > 0, "Degenerate aggregated cross-axis direction")
                vectors[f"cross_{shift}"] = cross_axis / cross_rms
            site_values[axis_id] = {key: value.astype(np.float32) for key, value in vectors.items()}
            diagnostics[f"site_{site_index}/{axis_id}"] = {
                "nuisance_ranks": ranks,
                "full_rms": full_rms,
                "residual_rms_relative_to_full": _rms(residual_axis) / full_rms,
                "projection_rms_relative_to_full": _rms(projection_axis) / full_rms,
                "restoration_error_rms": restoration,
            }
        result[site_index] = site_values
    return result, diagnostics


def _tensor_from_output(output: Any) -> tuple[Any, Any]:
    if hasattr(output, "shape"):
        return output, lambda value: value
    if isinstance(output, tuple) and output and hasattr(output[0], "shape"):
        return output[0], lambda value: (value, *output[1:])
    if isinstance(output, list) and output and hasattr(output[0], "shape"):
        return output[0], lambda value: [value, *output[1:]]
    raise T16Error(f"Cannot identify tensor in output {type(output)!r}")


def _encode_single(torch: Any, tokenizer: Any, model: Any, prompt: str) -> tuple[Any, Any]:
    ids = _token_ids(tokenizer, prompt)
    device = next(model.parameters()).device
    input_ids = torch.tensor([ids], dtype=torch.long, device=device)
    return input_ids, torch.ones_like(input_ids)


def _baseline_logits_and_rms(torch: Any, model: Any, input_ids: Any, attention_mask: Any, block: Any) -> tuple[np.ndarray, float]:
    captured: dict[str, Any] = {}

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        raw, _rebuild = _tensor_from_output(output)
        captured["value"] = raw[0, -1, :].detach().float()
        return output

    handle = block.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, return_dict=True)
    finally:
        handle.remove()
    value = captured["value"]
    rms = float(torch.sqrt(torch.mean(value * value)).item())
    _require(math.isfinite(rms) and rms > 0, "Target activation RMS invalid")
    return output.logits[0, -1, :].detach().float().cpu().numpy(), rms


def _injected_logits(torch: Any, model: Any, input_ids: Any, attention_mask: Any, block: Any, vectors: np.ndarray) -> np.ndarray:
    device = next(model.parameters()).device
    vector_tensor = torch.tensor(vectors, dtype=torch.float32, device=device)
    count = len(vectors)

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        raw, rebuild = _tensor_from_output(output)
        changed = raw.clone()
        changed[:, -1, :] = changed[:, -1, :] + vector_tensor.to(device=raw.device, dtype=raw.dtype)
        return rebuild(changed)

    handle = block.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(
                input_ids=input_ids.repeat(count, 1),
                attention_mask=attention_mask.repeat(count, 1),
                use_cache=False,
                return_dict=True,
            )
    finally:
        handle.remove()
    return output.logits[:, -1, :].detach().float().cpu().numpy()


def _condition_vectors(vectors: Mapping[str, np.ndarray], scale: float) -> tuple[list[dict[str, Any]], np.ndarray]:
    metadata = [{"condition_kind": "zero", "sign": 0, "shift": None}]
    values = [np.zeros_like(vectors["full"])]
    for kind in ("full", "residual", "projection"):
        for sign in (-1, 1):
            metadata.append({"condition_kind": kind, "sign": sign, "shift": None})
            values.append(vectors[kind] * np.float32(sign * scale))
    for shift in range(1, 8):
        for sign in (-1, 1):
            metadata.append({"condition_kind": "cross", "sign": sign, "shift": shift})
            values.append(vectors[f"cross_{shift}"] * np.float32(sign * scale))
    _require(len(metadata) == len(values) == 21, "Causal condition roster changed")
    return metadata, np.stack(values).astype(np.float32)


def run_causal(*, output_root: Path, source_directory: Path, model_preflight_directory: Path, model_path: Path | None) -> dict[str, Any]:
    audit_freeze()
    final = output_root / CAUSAL_ROLE / "causal_subspace"
    if final.is_dir():
        return validate_causal(output_root)
    _yield_if_contended(output_root, "before_causal_source_decomposition")
    subspaces, diagnostics = _source_subspaces(source_directory)
    _yield_if_contended(output_root, "before_causal_model_load")
    torch, tokenizer, model, blocks, label_ids, model_receipt = _load_model(CAUSAL_ROLE, model_preflight_directory, model_path)
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    maximum_zero_error = 0.0
    try:
        targets = _causal_target_records()
        magnitude = float(_config()["causal_subspace"]["magnitude"])
        for site_index in SITE_INDICES:
            _yield_if_contended(output_root, f"before_causal_site_{site_index}")
            block_index = int(t13.layer_indices(CAUSAL_ROLE)[site_index])
            block = blocks[block_index]
            for target_index, target in enumerate(targets):
                if target_index % 16 == 0:
                    _yield_if_contended(output_root, f"during_causal_site_{site_index}_target_{target_index}")
                prompt = _render_prompt(tokenizer, str(target["user_prompt"]))
                input_ids, attention_mask = _encode_single(torch, tokenizer, model, prompt)
                baseline, target_rms = _baseline_logits_and_rms(torch, model, input_ids, attention_mask, block)
                metadata, injections = _condition_vectors(subspaces[site_index][str(target["axis_id"])], magnitude * target_rms)
                logits = _injected_logits(torch, model, input_ids, attention_mask, block, injections)
                maximum_zero_error = max(maximum_zero_error, float(np.max(np.abs(logits[0] - baseline))))
                mismatch_id = label_ids[str(target["mismatch_label"])]
                match_id = label_ids[str(target["match_label"])]
                correct_id = label_ids[str(target["correct_label"])]
                incorrect_id = label_ids[str(target["incorrect_label"])]
                for condition, values in zip(metadata, logits, strict=True):
                    rows.append(
                        {
                            **{key: value for key, value in target.items() if key != "user_prompt"},
                            **condition,
                            "schema_version": SCHEMA_VERSION,
                            "protocol_id": PROTOCOL_ID,
                            "model_role": CAUSAL_ROLE,
                            "site_index": site_index,
                            "block_index": block_index,
                            "depth_fraction": float(_config()["causal_subspace"]["source_depth_fractions"][SITE_INDICES.index(site_index)]),
                            "prompt_sha256": hashlib.sha256(str(target["user_prompt"]).encode("utf-8")).hexdigest(),
                            "mismatch_minus_match_logit": float(values[mismatch_id] - values[match_id]),
                            "correct_minus_incorrect_logit": float(values[correct_id] - values[incorrect_id]),
                        }
                    )
    finally:
        del model
        torch.cuda.empty_cache()
    expected = audit_design()["counts"]["causal_response_rows"]
    _require(len(rows) == expected, "Causal response row count changed")
    stage = final.parent / f".{final.name}.stage-{uuid.uuid4().hex}"
    _require(not final.exists() and not stage.exists(), "Causal output collision")
    stage.mkdir(parents=True)
    _write_jsonl(stage / "response_ledger.jsonl", rows)
    _write_json(stage / "decomposition_diagnostics.json", diagnostics)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_subspace_complete",
        "model_role": CAUSAL_ROLE,
        "response_rows": len(rows),
        "target_rows": len(_causal_target_records()),
        "site_indices": list(SITE_INDICES),
        "conditions_per_target_per_site": 21,
        "maximum_zero_hook_logit_error": maximum_zero_error,
        "maximum_vector_restoration_error_rms": max(float(value["restoration_error_rms"]) for value in diagnostics.values()),
        "source_direction_catalog_sha256": _sha256(source_directory / "direction_catalog.jsonl"),
        "source_directions_sha256": _sha256(source_directory / "directions.npy"),
        "response_ledger_sha256": _sha256(stage / "response_ledger.jsonl"),
        "decomposition_diagnostics_sha256": _sha256(stage / "decomposition_diagnostics.json"),
        "freeze_manifest_sha256": _sha256(_root() / FREEZE_PATH),
        "model_receipt": model_receipt,
        "generation_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(stage / "receipt.json", receipt)
    os.replace(stage, final)
    return validate_causal(output_root)


def validate_causal(output_root: Path) -> dict[str, Any]:
    directory = output_root / CAUSAL_ROLE / "causal_subspace"
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Causal receipt protocol changed")
    _require(receipt.get("status") == "causal_subspace_complete", "Causal run incomplete")
    ledger = directory / "response_ledger.jsonl"
    diagnostics = directory / "decomposition_diagnostics.json"
    _require(_sha256(ledger) == receipt["response_ledger_sha256"], "Causal ledger changed")
    _require(_sha256(diagnostics) == receipt["decomposition_diagnostics_sha256"], "Causal diagnostics changed")
    rows = _read_jsonl(ledger)
    expected = audit_design()["counts"]["causal_response_rows"]
    _require(len(rows) == expected == int(receipt["response_rows"]), "Causal rows changed")
    _require(all(math.isfinite(float(row["mismatch_minus_match_logit"])) for row in rows), "Causal ledger nonfinite")
    return {
        "status": "pass",
        "response_rows": len(rows),
        "maximum_zero_hook_logit_error": float(receipt["maximum_zero_hook_logit_error"]),
        "maximum_vector_restoration_error_rms": float(receipt["maximum_vector_restoration_error_rms"]),
        "receipt_sha256": _sha256(directory / "receipt.json"),
    }


def _antisymmetry(values: Sequence[Mapping[str, Any]], kind: str, shift: int | None = None) -> float:
    selected = [row for row in values if row["condition_kind"] == kind and (shift is None or int(row["shift"]) == shift)]
    _require(len(selected) == 2 and {int(row["sign"]) for row in selected} == {-1, 1}, "Signed condition pair changed")
    by_sign = {int(row["sign"]): float(row["mismatch_minus_match_logit"]) for row in selected}
    return 0.5 * (by_sign[1] - by_sign[-1])


def analyze_causal(output_root: Path, output: Path) -> dict[str, Any]:
    audit = validate_causal(output_root)
    rows = _read_jsonl(output_root / CAUSAL_ROLE / "causal_subspace" / "response_ledger.jsonl")
    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["site_index"]), int(row["target_index"]))].append(row)
    target_estimands: list[dict[str, Any]] = []
    for (site_index, target_index), values in sorted(grouped.items()):
        full = _antisymmetry(values, "full")
        residual = _antisymmetry(values, "residual")
        projection = _antisymmetry(values, "projection")
        cross = np.asarray([_antisymmetry(values, "cross", shift) for shift in range(1, 8)])
        target_estimands.append(
            {
                "site_index": site_index,
                "target_index": target_index,
                "axis_id": str(values[0]["axis_id"]),
                "treatment": full - float(np.median(cross)),
                "sufficiency": residual - float(np.median(cross)),
                "necessity": full - projection,
                "baseline_correct_logodds": float(next(row for row in values if row["condition_kind"] == "zero")["correct_minus_incorrect_logit"]),
            }
        )
    axis_order = [str(axis["id"]) for axis in _t15b_axes()]
    seed = int(_config()["analysis"]["bootstrap_seed"]) + 100
    estimands: dict[str, Any] = {}
    passed = []
    for offset, name in enumerate(("treatment", "sufficiency", "necessity")):
        axis_values = np.asarray([
            np.median([float(row[name]) for row in target_estimands if row["axis_id"] == axis_id])
            for axis_id in axis_order
        ])
        result = _interval_and_test(axis_values, seed + offset)
        alpha = 0.05 / 3.0
        component_pass = result["bootstrap_95_percent_interval"][0] > 0.0 and result["exact_one_sided_sign_flip_p_value"] <= alpha
        result["bonferroni_one_sided_alpha"] = alpha
        result["component_pass"] = component_pass
        estimands[name] = result
        passed.append(component_pass)
    engineering_pass = audit["maximum_zero_hook_logit_error"] <= 1.0e-10 and audit["maximum_vector_restoration_error_rms"] <= 1.0e-6
    decision = bool(all(passed) and engineering_pass)
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_subspace_analysis_complete",
        "audit": audit,
        "estimands": estimands,
        "baseline_forced_choice_accuracy": float(np.mean([row["baseline_correct_logodds"] > 0 for row in target_estimands])),
        "engineering_invariants_pass": engineering_pass,
        "decision": "source_defined_residual_subspace_causal_effect_supported" if decision else "causal_subspace_gate_not_supported",
        "causal_subspace_gate_pass": decision,
        "claim_boundary": _config()["claim_boundary"],
        "unique_or_complete_circuit_claim_authorized": False,
        "unrestricted_semantic_understanding_claim_authorized": False,
    }
    _write_json(output, result)
    return result


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("audit-design", "audit-freeze"):
        subparsers.add_parser(name)
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
    behavior = subparsers.add_parser("run-behavior-role")
    behavior.add_argument("--role", required=True)
    behavior.add_argument("--output-root", type=Path, required=True)
    behavior.add_argument("--model-preflight-directory", type=Path, required=True)
    behavior.add_argument("--model-path", type=Path)
    audit_behavior_parser = subparsers.add_parser("audit-behavior")
    audit_behavior_parser.add_argument("--output-root", type=Path, required=True)
    analyze_behavior_parser = subparsers.add_parser("analyze-behavior")
    analyze_behavior_parser.add_argument("--output-root", type=Path, required=True)
    analyze_behavior_parser.add_argument("--output", type=Path, required=True)
    causal = subparsers.add_parser("run-causal")
    causal.add_argument("--output-root", type=Path, required=True)
    causal.add_argument("--source-directory", type=Path, required=True)
    causal.add_argument("--model-preflight-directory", type=Path, required=True)
    causal.add_argument("--model-path", type=Path)
    audit_causal_parser = subparsers.add_parser("audit-causal")
    audit_causal_parser.add_argument("--output-root", type=Path, required=True)
    analyze_causal_parser = subparsers.add_parser("analyze-causal")
    analyze_causal_parser.add_argument("--output-root", type=Path, required=True)
    analyze_causal_parser.add_argument("--output", type=Path, required=True)
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
    elif args.command == "run-behavior-role":
        result = run_behavior_role(role=args.role, output_root=args.output_root, model_preflight_directory=args.model_preflight_directory, model_path=args.model_path)
    elif args.command == "audit-behavior":
        result = audit_behavior(args.output_root)
    elif args.command == "analyze-behavior":
        result = analyze_behavior(args.output_root, args.output)
    elif args.command == "run-causal":
        result = run_causal(output_root=args.output_root, source_directory=args.source_directory, model_preflight_directory=args.model_preflight_directory, model_path=args.model_path)
    elif args.command == "audit-causal":
        result = validate_causal(args.output_root)
    else:
        result = analyze_causal(args.output_root, args.output)
    _print(result)


if __name__ == "__main__":
    main()
