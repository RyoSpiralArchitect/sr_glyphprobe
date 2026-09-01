#!/usr/bin/env python3
"""Conditional T19-C attn_out/mlp_out causal lexical-subspace experiment."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
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

import emoji_steering_causal_path_v0 as causal_engine  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402
import t19_lexical_alias_unicode_control_v0 as t19  # noqa: E402


PROTOCOL_ID = "glyphprobe-t19-lexical-alias-component-causal-v0"
SCHEMA_VERSION = 1
ROLE = "llama32_3b_base_bf16"
GO_MANIFEST_PATH = Path("data/manifests/t19_lexical_alias_component_causal_v0_go.json")
VALIDATION_DIRECTORY = Path("validation/t19_lexical_alias_component_causal_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
SOURCE_SITE_ORDER = (
    ("attn_out", 21),
    ("mlp_out", 21),
    ("attn_out", 24),
    ("mlp_out", 24),
    ("attn_out", 27),
    ("mlp_out", 27),
)
PRIMARY_SITES = (("attn_out", 24), ("mlp_out", 24))
SOURCE_VIEWS = ("glyph", "alias_label")
EVAL_VIEWS = ("glyph", "alias_label", "codepoint_literal")


class T19CausalError(RuntimeError):
    """Raised when the frozen T19-C protocol is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T19CausalError(message)


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
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _git_value(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=_root(), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _site_key(site: str, block_index: int) -> str:
    return f"{site}__block_{block_index:02d}"


def audit_design(output: Path | None = None) -> dict[str, Any]:
    config = t19._config()["causal_followup"]
    selection = t19.audit_selection(rescan_exposure=False)
    primary = tuple((str(row["site"]), int(row["block_index"])) for row in config["primary_sites"])
    secondary = tuple((str(row["site"]), int(row["block_index"])) for row in config["secondary_sites"])
    _require(primary == PRIMARY_SITES, "Primary causal sites changed")
    _require(set((*primary, *secondary)) == set(SOURCE_SITE_ORDER), "Causal site roster changed")
    _require(str(config["fixed_model"]["role"]) == ROLE, "Causal role changed")
    spec = t10._model_spec(ROLE)
    _require(int(spec["expected_num_layers"]) == 28 and int(spec["expected_model_dim"]) == 3072, "Causal model geometry changed")
    _require(int(config["subspace"]["rank"]) == 8, "Subspace rank changed")
    _require(selection["causal_source_items"] == int(config["source_bank"]["rows"]), "Source bank count changed")
    _require(selection["causal_eval_items"] == int(config["evaluation_bank"]["rows"]), "Eval bank count changed")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_design_pass_zero_source_or_eval_forwards",
        "parent_protocol_id": t19.PROTOCOL_ID,
        "selection_manifest_sha256": selection["selection_sha256"],
        "model_role": ROLE,
        "source_rows": selection["causal_source_items"],
        "evaluation_rows": selection["causal_eval_items"],
        "site_order": [{"site": site, "block_index": block} for site, block in SOURCE_SITE_ORDER],
        "primary_sites": [{"site": site, "block_index": block} for site, block in PRIMARY_SITES],
        "subspace_rank": int(config["subspace"]["rank"]),
        "causal_go_gate_open": False,
        "source_model_forwards": 0,
        "evaluation_model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    if output is not None:
        _require(not output.exists(), f"Causal design preflight exists: {output}")
        _write_json(output, value)
    return value


def _tokenizer_sequences(tokenizer: Any, rows: Sequence[Mapping[str, Any]], views: Sequence[str]) -> dict[str, Any]:
    carrier = str(t19._config()["input"]["carriers"]["pipe"]["unit"])
    repeats = int(t19._config()["input"]["carriers"]["pipe"]["repeats"])
    carrier_ids = [int(value) for value in tokenizer.encode(carrier, add_special_tokens=False)]
    _require(len(carrier_ids) == 1, "Causal carrier is not one token")
    hashes: dict[str, str] = {}
    histograms: dict[str, dict[str, int]] = {}
    maximum = 0
    for view in views:
        raw_rows: list[list[int]] = []
        combined_rows: list[list[int]] = []
        for row in rows:
            text = str(row[view])
            raw = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
            combined = [int(value) for value in tokenizer.encode(text + carrier * repeats, add_special_tokens=False)]
            _require(combined == raw + carrier_ids * repeats, f"Causal carrier boundary changed: {row['codepoint']}/{view}")
            _require(tokenizer.decode(combined, clean_up_tokenization_spaces=False, skip_special_tokens=False) == text + carrier * repeats, f"Causal decode changed: {row['codepoint']}/{view}")
            raw_rows.append(raw)
            combined_rows.append(combined)
            maximum = max(maximum, len(combined))
        hashes[f"raw__{view}"] = t19._sequence_hash(raw_rows)
        hashes[f"combined__{view}"] = t19._sequence_hash(combined_rows)
        histograms[view] = {str(length): int(count) for length, count in sorted(__import__("collections").Counter(len(row) for row in raw_rows).items())}
    return {
        "rows": len(rows),
        "views": list(views),
        "carrier": carrier,
        "carrier_repeats": repeats,
        "carrier_token_id": carrier_ids[0],
        "ordered_sequence_sha256": hashes,
        "raw_token_count_histograms": histograms,
        "maximum_combined_tokens": maximum,
    }


def tokenizer_preflight(model_path: Path, output: Path) -> dict[str, Any]:
    from transformers import AutoTokenizer

    design = audit_design()
    tokenizer = AutoTokenizer.from_pretrained(model_path.resolve(), local_files_only=True, trust_remote_code=False, use_fast=True)
    t10_reference = t10._tokenize_roster(tokenizer, t10._config())["receipt"]
    frozen_reference = _read_json(t10._receipt_path(ROLE))["tokenizer"]
    _require(t10_reference["ordered_sequence_sha256"] == frozen_reference["ordered_sequence_sha256"], "Causal tokenizer differs on T10 reference")
    source = _tokenizer_sequences(tokenizer, t19.causal_items("source"), SOURCE_VIEWS)
    evaluation = _tokenizer_sequences(tokenizer, t19.causal_items("eval"), EVAL_VIEWS)
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_tokenizer_preflight_pass_zero_source_or_eval_forwards",
        "model_role": ROLE,
        "artifact_model_id": t10._model_spec(ROLE)["artifact_model_id"],
        "frozen_model_revision": t10._model_spec(ROLE)["revision"],
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": int(len(tokenizer)),
        "tokenizer_asset_sha256": t19._tokenizer_asset_hashes(model_path.resolve()),
        "t10_reference_surface_sequence_equivalence": True,
        "design_preflight": design,
        "source_bank": source,
        "evaluation_bank": evaluation,
        "source_model_forwards": 0,
        "evaluation_model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"Causal tokenizer preflight exists: {output}")
    _write_json(output, value)
    return {"status": "pass", "source_rows": source["rows"], "evaluation_rows": evaluation["rows"], "sha256": _sha256(output), "model_forwards": 0}


def admit_go(observational_analysis: Path, output: Path) -> dict[str, Any]:
    t19.audit_freeze(require_pushed=True)
    validated = t19.validate_analysis(observational_analysis)
    _require(validated["causal_go_gate_open"] is True, "T19-L causal go gate is closed")
    _require(not output.exists(), f"Causal go manifest exists: {output}")
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    tokenizer = _read_json(_root() / TOKENIZER_PREFLIGHT_PATH)
    _require(design.get("status") == "causal_design_pass_zero_source_or_eval_forwards", "Causal design preflight incomplete")
    _require(tokenizer.get("status") == "causal_tokenizer_preflight_pass_zero_source_or_eval_forwards", "Causal tokenizer preflight incomplete")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_go_admitted_before_source_or_eval_forwards",
        "parent_freeze_manifest_sha256": t19.audit_freeze()["freeze_manifest_sha256"],
        "observational_analysis_receipt_sha256": validated["analysis_receipt_sha256"],
        "causal_design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "causal_tokenizer_preflight_sha256": _sha256(_root() / TOKENIZER_PREFLIGHT_PATH),
        "causal_executor_analyzer_sha256": _sha256(Path(__file__)),
        "source_bank_sha256": _bank_hash(t19.causal_items("source")),
        "evaluation_bank_sha256": _bank_hash(t19.causal_items("eval")),
        "source_model_forwards_at_go": 0,
        "evaluation_model_forwards_at_go": 0,
        "intervention_calls_at_go": 0,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output, value)
    return {"status": "pass", "go_manifest_sha256": _sha256(output), "source_model_forwards": 0, "evaluation_model_forwards": 0}


def _bank_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(list(rows), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def audit_go(*, require_pushed: bool = False) -> dict[str, Any]:
    t19.audit_freeze(require_pushed=require_pushed)
    path = _root() / GO_MANIFEST_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID and value.get("status") == "causal_go_admitted_before_source_or_eval_forwards", "Causal go manifest mismatch")
    _require(value["causal_executor_analyzer_sha256"] == _sha256(Path(__file__)), "Causal executor changed after go")
    _require(value["source_bank_sha256"] == _bank_hash(t19.causal_items("source")), "Source bank changed")
    _require(value["evaluation_bank_sha256"] == _bank_hash(t19.causal_items("eval")), "Evaluation bank changed")
    if require_pushed:
        _require(_git_value("rev-parse", "HEAD") == _git_value("rev-parse", "origin/main"), "Causal go commit is not pushed")
        _git_value("cat-file", "-e", f"HEAD:{GO_MANIFEST_PATH.as_posix()}")
    return {"status": "pass", "go_manifest_sha256": _sha256(path)}


def _yield_if_contended(output_root: Path, boundary: str) -> None:
    pids = atlas._foreign_gpu_pids()
    if not pids:
        return
    output_root.mkdir(parents=True, exist_ok=True)
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
    raise SystemExit(int(t19._config()["execution_policy"]["yield_exit_code_on_foreign_contention"]))


def _load_model(model_path: Path) -> tuple[Any, Any, Any, Sequence[Any], dict[str, Any]]:
    t10._validate_runtime(t10._config())
    torch, tokenizer, model, _last_block, receipt, _roster = t10._load_model(ROLE, model_path)
    blocks = t10._resolve_attr(model, str(t10._model_spec(ROLE)["expected_block_path"]))
    return torch, tokenizer, model, blocks, receipt


def _view_input(tokenizer: Any, row: Mapping[str, Any], view: str) -> tuple[list[int], int]:
    carrier = str(t19._config()["input"]["carriers"]["pipe"]["unit"])
    repeats = int(t19._config()["input"]["carriers"]["pipe"]["repeats"])
    raw = [int(value) for value in tokenizer.encode(str(row[view]), add_special_tokens=False)]
    ids = [int(value) for value in tokenizer.encode(str(row[view]) + carrier * repeats, add_special_tokens=False)]
    carrier_ids = [int(value) for value in tokenizer.encode(carrier, add_special_tokens=False)]
    _require(len(carrier_ids) == 1 and ids == raw + carrier_ids * repeats, "Runtime carrier sequence changed")
    return ids, len(raw)


def _capture_sites_and_final(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    row: Mapping[str, Any],
    view: str,
    batch_count: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    ids, position = _view_input(tokenizer, row, view)
    _require(batch_count >= 1, "Capture batch count must be positive")
    input_ids = torch.tensor([ids], dtype=torch.long, device="cuda").repeat(batch_count, 1)
    attention_mask = torch.ones_like(input_ids)
    captured: dict[tuple[str, int], Any] = {}
    handles = []
    for site, block_index in SOURCE_SITE_ORDER:
        module, is_pre = causal_engine._site_module(blocks, site, block_index)
        _require(not is_pre, "T19-C component site unexpectedly uses a pre-hook")

        def hook(_module: Any, _inputs: Any, output: Any, *, key: tuple[str, int] = (site, block_index)) -> Any:
            raw, _rebuild = causal_engine._tensor_from_output(output)
            captured[key] = raw[0, position, :].detach().float().cpu().numpy()
            return output

        handles.append(module.register_forward_hook(hook))
    try:
        with torch.inference_mode():
            output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, output_hidden_states=True, return_dict=True)
        final = output.hidden_states[-1][0, position, :].detach().float().cpu().numpy()
    finally:
        for handle in handles:
            handle.remove()
    sites = np.stack([captured[key] for key in SOURCE_SITE_ORDER]).astype(np.float32)
    return sites, final.astype(np.float32)


def _forward_replacements(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    blocks: Sequence[Any],
    row: Mapping[str, Any],
    view: str,
    site: str,
    block_index: int,
    replacements: np.ndarray,
) -> np.ndarray:
    ids, position = _view_input(tokenizer, row, view)
    count = int(replacements.shape[0])
    input_ids = torch.tensor([ids], dtype=torch.long, device="cuda").repeat(count, 1)
    attention_mask = torch.ones_like(input_ids)
    module, is_pre = causal_engine._site_module(blocks, site, block_index)
    _require(not is_pre, "T19-C component site unexpectedly uses a pre-hook")
    replacement_tensor = torch.tensor(replacements, dtype=torch.float32, device="cuda")

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        raw, rebuild = causal_engine._tensor_from_output(output)
        changed = raw.clone()
        changed[:, position, :] = replacement_tensor.to(dtype=raw.dtype, device=raw.device)
        return rebuild(changed)

    handle = module.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            output = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False, output_hidden_states=True, return_dict=True)
        result = output.hidden_states[-1][:, position, :].detach().float().cpu().numpy()
    finally:
        handle.remove()
    _require(result.shape[0] == count and np.isfinite(result).all(), "Causal replacement produced invalid final states")
    return result.astype(np.float32)


def _row_normalized(value: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = np.mean(value, axis=0, dtype=np.float64)
    centered = np.asarray(value, dtype=np.float64) - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    _require(bool(np.all(norms > 0)), "Zero source row norm")
    return centered / norms, mean.astype(np.float32)


def _source_subspace(glyph: np.ndarray, alias: np.ndarray, rank: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    g, mean_g = _row_normalized(glyph)
    a, _mean_a = _row_normalized(alias)
    qg, rg = np.linalg.qr(g.T, mode="reduced")
    qa, ra = np.linalg.qr(a.T, mode="reduced")
    u_small, _singular, _right = np.linalg.svd(rg @ ra.T, full_matrices=False)
    learned = qg @ u_small[:, :rank]
    learned, _ = np.linalg.qr(learned, mode="reduced")
    combined = np.concatenate((g, a), axis=0)
    source_span, source_singular, _ = np.linalg.svd(combined.T, full_matrices=False)
    tolerance = source_singular[0] * max(combined.shape) * np.finfo(np.float64).eps
    source_span = source_span[:, source_singular > tolerance]
    _require(source_span.shape[1] >= 2 * rank, "Source span is too small for learned and control subspaces")
    rng = np.random.default_rng(seed)
    candidate = source_span @ rng.normal(size=(source_span.shape[1], rank * 2))
    candidate = candidate - learned @ (learned.T @ candidate)
    random_basis, _ = np.linalg.qr(candidate, mode="reduced")
    random_basis = random_basis[:, :rank]
    _require(learned.shape == random_basis.shape == (glyph.shape[1], rank), "Subspace shape changed")
    _require(float(np.max(np.abs(learned.T @ learned - np.eye(rank)))) < 1e-8, "Learned subspace is not orthonormal")
    _require(float(np.max(np.abs(random_basis.T @ random_basis - np.eye(rank)))) < 1e-8, "Random subspace is not orthonormal")
    _require(float(np.max(np.abs(learned.T @ random_basis))) < 1e-8, "Control overlaps the learned subspace")
    return learned.astype(np.float32), random_basis.astype(np.float32), mean_g


def run_source(model_path: Path, output_root: Path) -> dict[str, Any]:
    audit_go(require_pushed=True)
    _require(not output_root.exists(), f"Source output exists: {output_root}")
    _yield_if_contended(output_root, "before_source_model_load")
    stage = output_root.with_name(f".{output_root.name}.stage-{uuid.uuid4().hex}")
    stage.mkdir(parents=True)
    torch, tokenizer, model, blocks, model_receipt = _load_model(model_path)
    rows = t19.causal_items("source")
    width = int(t10._model_spec(ROLE)["expected_model_dim"])
    activations = np.empty((len(SOURCE_SITE_ORDER), len(rows), len(SOURCE_VIEWS), width), dtype=np.float32)
    final_states = np.empty((len(rows), len(SOURCE_VIEWS), width), dtype=np.float32)
    started = time.perf_counter()
    forwards = 0
    try:
        for item_index, row in enumerate(rows):
            if item_index % 8 == 0:
                _yield_if_contended(output_root, f"source_item_{item_index:04d}")
            for view_index, view in enumerate(SOURCE_VIEWS):
                sites, final = _capture_sites_and_final(torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row, view=view)
                activations[:, item_index, view_index, :] = sites
                final_states[item_index, view_index] = final
                forwards += 1
    finally:
        del model
        torch.cuda.empty_cache()
    np.save(stage / "source_activations.npy", activations, allow_pickle=False)
    np.save(stage / "source_final_states.npy", final_states, allow_pickle=False)
    rank = int(t19._config()["causal_followup"]["subspace"]["rank"])
    learned = np.empty((len(SOURCE_SITE_ORDER), width, rank), dtype=np.float32)
    random_basis = np.empty_like(learned)
    glyph_means = np.empty((len(SOURCE_SITE_ORDER), width), dtype=np.float32)
    for site_index, (site, block_index) in enumerate(SOURCE_SITE_ORDER):
        learned[site_index], random_basis[site_index], glyph_means[site_index] = _source_subspace(
            activations[site_index, :, 0, :],
            activations[site_index, :, 1, :],
            rank,
            2026090300 + site_index,
        )
    np.savez_compressed(stage / "subspaces.npz", learned=learned, random_control=random_basis, glyph_means=glyph_means)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_source_subspaces_complete",
        "model_role": ROLE,
        "source_rows": len(rows),
        "source_bank_sha256": _bank_hash(rows),
        "site_order": [{"site": site, "block_index": block} for site, block in SOURCE_SITE_ORDER],
        "subspace_rank": rank,
        "model_forward_calls": forwards,
        "intervention_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "model": model_receipt,
        "go_manifest_sha256": audit_go()["go_manifest_sha256"],
        "outputs": {
            name: _sha256(stage / name)
            for name in ("source_activations.npy", "source_final_states.npy", "subspaces.npz")
        },
    }
    _write_json(stage / "source_receipt.json", receipt)
    t19.engine._write_ledger(stage, ("source_activations.npy", "source_final_states.npy", "subspaces.npz", "source_receipt.json"))
    os.replace(stage, output_root)
    return validate_source(output_root)


def validate_source(output_root: Path) -> dict[str, Any]:
    receipt = _read_json(output_root / "source_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "causal_source_subspaces_complete", "Source receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output_root / name) == expected, f"Source output changed: {name}")
    with np.load(output_root / "subspaces.npz", allow_pickle=False) as values:
        learned = values["learned"]
        random_basis = values["random_control"]
        _require(learned.shape == random_basis.shape == (6, 3072, 8), "Source subspace shape changed")
        for value in (learned, random_basis):
            for index in range(6):
                _require(float(np.max(np.abs(value[index].T @ value[index] - np.eye(8)))) < 2e-5, "Stored subspace is not orthonormal")
        for index in range(6):
            _require(float(np.max(np.abs(learned[index].T @ random_basis[index]))) < 2e-5, "Stored control overlaps the learned subspace")
    return {"status": "pass", "source_rows": int(receipt["source_rows"]), "model_forward_calls": int(receipt["model_forward_calls"]), "source_receipt_sha256": _sha256(output_root / "source_receipt.json")}


def _project(value: np.ndarray, basis: np.ndarray) -> np.ndarray:
    return basis @ (basis.T @ value)


def run_evaluation(model_path: Path, source_root: Path, output_root: Path) -> dict[str, Any]:
    audit_go(require_pushed=True)
    source = validate_source(source_root)
    _require(not output_root.exists(), f"Evaluation output exists: {output_root}")
    _yield_if_contended(output_root, "before_eval_model_load")
    stage = output_root.with_name(f".{output_root.name}.stage-{uuid.uuid4().hex}")
    stage.mkdir(parents=True)
    with np.load(source_root / "subspaces.npz", allow_pickle=False) as values:
        learned = np.asarray(values["learned"], dtype=np.float32)
        random_basis = np.asarray(values["random_control"], dtype=np.float32)
        glyph_means = np.asarray(values["glyph_means"], dtype=np.float32)
    torch, tokenizer, model, blocks, model_receipt = _load_model(model_path)
    rows = t19.causal_items("eval")
    width = int(t10._model_spec(ROLE)["expected_model_dim"])
    sites = len(SOURCE_SITE_ORDER)
    baseline_targets = np.empty((len(rows), 2, width), dtype=np.float32)
    baseline_queries = np.empty((len(rows), 2, width), dtype=np.float32)
    baseline_components = np.empty((sites, len(rows), 2, width), dtype=np.float32)
    glyph_conditions = np.empty((sites, len(rows), 4, width), dtype=np.float32)
    codepoint_conditions = np.empty((sites, len(rows), 3, width), dtype=np.float32)
    forwards = 0
    interventions = 0
    started = time.perf_counter()
    try:
        for item_index, row in enumerate(rows):
            if item_index % 4 == 0:
                _yield_if_contended(output_root, f"eval_item_{item_index:04d}")
            glyph_sites, glyph_final = _capture_sites_and_final(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                row=row,
                view="glyph",
                batch_count=4,
            )
            codepoint_sites, codepoint_final = _capture_sites_and_final(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                blocks=blocks,
                row=row,
                view="codepoint_literal",
                batch_count=3,
            )
            _alias_sites, alias_final = _capture_sites_and_final(torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row, view="alias_label")
            forwards += 3
            baseline_queries[item_index, 0] = glyph_final
            baseline_queries[item_index, 1] = codepoint_final
            baseline_targets[item_index, 0] = alias_final
            baseline_targets[item_index, 1] = codepoint_final
            baseline_components[:, item_index, 0] = glyph_sites
            baseline_components[:, item_index, 1] = codepoint_sites
            for site_index, (site, block_index) in enumerate(SOURCE_SITE_ORDER):
                g = glyph_sites[site_index]
                c = codepoint_sites[site_index]
                centered_g = g - glyph_means[site_index]
                learned_g = _project(centered_g, learned[site_index])
                random_g = _project(centered_g, random_basis[site_index])
                glyph_replacements = np.stack((g, g - learned_g, g - random_g, (g - learned_g) + learned_g)).astype(np.float32)
                learned_patch = _project(g - c, learned[site_index])
                random_patch = _project(g - c, random_basis[site_index])
                codepoint_replacements = np.stack((c, c + learned_patch, c + random_patch)).astype(np.float32)
                glyph_conditions[site_index, item_index] = _forward_replacements(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row, view="glyph", site=site, block_index=block_index, replacements=glyph_replacements
                )
                codepoint_conditions[site_index, item_index] = _forward_replacements(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row, view="codepoint_literal", site=site, block_index=block_index, replacements=codepoint_replacements
                )
                forwards += 2
                interventions += 7
    finally:
        del model
        torch.cuda.empty_cache()
    np.savez_compressed(
        stage / "evaluation_states.npz",
        baseline_targets=baseline_targets,
        baseline_queries=baseline_queries,
        baseline_components=baseline_components,
        glyph_conditions=glyph_conditions,
        codepoint_conditions=codepoint_conditions,
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_evaluation_complete_sealed",
        "model_role": ROLE,
        "evaluation_rows": len(rows),
        "evaluation_bank_sha256": _bank_hash(rows),
        "site_order": [{"site": site, "block_index": block} for site, block in SOURCE_SITE_ORDER],
        "glyph_condition_order": ["zero_hook", "necessity", "random_necessity", "restoration"],
        "codepoint_condition_order": ["zero_hook", "sufficiency", "random_sufficiency"],
        "model_forward_calls": forwards,
        "intervention_rows": interventions,
        "elapsed_seconds": time.perf_counter() - started,
        "source_receipt_sha256": source["source_receipt_sha256"],
        "go_manifest_sha256": audit_go()["go_manifest_sha256"],
        "model": model_receipt,
        "outputs": {"evaluation_states.npz": _sha256(stage / "evaluation_states.npz")},
    }
    _write_json(stage / "evaluation_receipt.json", receipt)
    t19.engine._write_ledger(stage, ("evaluation_states.npz", "evaluation_receipt.json"))
    os.replace(stage, output_root)
    return validate_evaluation(output_root, source_root)


def validate_evaluation(output_root: Path, source_root: Path) -> dict[str, Any]:
    source = validate_source(source_root)
    receipt = _read_json(output_root / "evaluation_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "causal_evaluation_complete_sealed", "Evaluation receipt mismatch")
    _require(receipt["source_receipt_sha256"] == source["source_receipt_sha256"], "Evaluation source binding changed")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output_root / name) == expected, f"Evaluation output changed: {name}")
    with np.load(output_root / "evaluation_states.npz", allow_pickle=False) as values:
        _require(values["baseline_targets"].shape == (192, 2, 3072), "Target shape changed")
        _require(values["baseline_queries"].shape == (192, 2, 3072), "Query shape changed")
        _require(values["glyph_conditions"].shape == (6, 192, 4, 3072), "Glyph condition shape changed")
        _require(values["codepoint_conditions"].shape == (6, 192, 3, 3072), "Codepoint condition shape changed")
    return {"status": "pass", "evaluation_rows": int(receipt["evaluation_rows"]), "model_forward_calls": int(receipt["model_forward_calls"]), "intervention_rows": int(receipt["intervention_rows"]), "evaluation_receipt_sha256": _sha256(output_root / "evaluation_receipt.json")}


def _normalized(value: np.ndarray) -> np.ndarray:
    centered = np.asarray(value, dtype=np.float64) - np.mean(value, axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    _require(bool(np.all(norms > 0)), "Zero analysis row norm")
    return centered / norms


def _retrieval_item_values(query: np.ndarray, alias_target: np.ndarray, codepoint_target: np.ndarray) -> tuple[float, np.ndarray, dict[str, float]]:
    q = _normalized(query)
    alias = _normalized(alias_target)
    codepoint = _normalized(codepoint_target)
    order = np.arange(len(q))
    alias_predictions = np.argmax(q @ alias.T, axis=1)
    codepoint_predictions = np.argmax(q @ codepoint.T, axis=1)
    values = (alias_predictions == order).astype(np.float64) - (codepoint_predictions == order).astype(np.float64)
    metrics = {
        "alias_top1": float(np.mean(alias_predictions == order)),
        "codepoint_top1": float(np.mean(codepoint_predictions == order)),
        "alias_minus_codepoint_top1": float(np.mean(values)),
    }
    return float(np.mean(values)), values, metrics


def _sign_flip(values: np.ndarray, *, draws: int, seed: int) -> dict[str, Any]:
    observed = float(np.mean(values))
    rng = np.random.default_rng(seed)
    exceedances = 0
    for start in range(0, draws, 2000):
        stop = min(draws, start + 2000)
        signs = rng.integers(0, 2, size=(stop - start, len(values)), dtype=np.int8) * 2 - 1
        statistics = np.mean(signs * values[None, :], axis=1)
        exceedances += int(np.sum(statistics >= observed - 1e-15))
    return {"draws": draws, "seed": seed, "observed": observed, "exceedances": exceedances, "p_value_one_sided": (1 + exceedances) / (draws + 1)}


def _bootstrap(values: np.ndarray, *, replicates: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 500):
        stop = min(replicates, start + 500)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        draws[start:stop] = np.mean(values[indices], axis=1)
    return {"replicates": replicates, "seed": seed, "lower_95": float(np.quantile(draws, 0.025)), "upper_95": float(np.quantile(draws, 0.975)), "bootstrap_mean": float(np.mean(draws))}


def analyze(evaluation_root: Path, source_root: Path, output: Path) -> dict[str, Any]:
    _require(not output.exists(), f"Causal analysis output exists: {output}")
    evaluation = validate_evaluation(evaluation_root, source_root)
    with np.load(evaluation_root / "evaluation_states.npz", allow_pickle=False) as arrays:
        targets = np.asarray(arrays["baseline_targets"], dtype=np.float32)
        queries = np.asarray(arrays["baseline_queries"], dtype=np.float32)
        glyph_conditions = np.asarray(arrays["glyph_conditions"], dtype=np.float32)
        codepoint_conditions = np.asarray(arrays["codepoint_conditions"], dtype=np.float32)
    alias_target = targets[:, 0]
    codepoint_target = targets[:, 1]
    _base_glyph_effect, base_glyph_items, base_glyph_metrics = _retrieval_item_values(queries[:, 0], alias_target, codepoint_target)
    _base_codepoint_effect, base_codepoint_items, base_codepoint_metrics = _retrieval_item_values(queries[:, 1], alias_target, codepoint_target)
    draws = 99999
    replicates = 20000
    practical = float(t19._config()["causal_followup"]["primary_decision"]["practical_minimum_each"])
    rows: list[dict[str, Any]] = []
    for site_index, (site, block_index) in enumerate(SOURCE_SITE_ORDER):
        _zero_glyph, _zero_glyph_items, zero_glyph_metrics = _retrieval_item_values(glyph_conditions[site_index, :, 0], alias_target, codepoint_target)
        _necessity, necessity_items, necessity_metrics = _retrieval_item_values(glyph_conditions[site_index, :, 1], alias_target, codepoint_target)
        _random_necessity, random_necessity_items, random_necessity_metrics = _retrieval_item_values(glyph_conditions[site_index, :, 2], alias_target, codepoint_target)
        _restoration, _restoration_items, restoration_metrics = _retrieval_item_values(glyph_conditions[site_index, :, 3], alias_target, codepoint_target)
        _zero_cp, _zero_cp_items, zero_cp_metrics = _retrieval_item_values(codepoint_conditions[site_index, :, 0], alias_target, codepoint_target)
        _sufficiency, sufficiency_items, sufficiency_metrics = _retrieval_item_values(codepoint_conditions[site_index, :, 1], alias_target, codepoint_target)
        _random_sufficiency, random_sufficiency_items, random_sufficiency_metrics = _retrieval_item_values(codepoint_conditions[site_index, :, 2], alias_target, codepoint_target)
        necessity_adjusted = random_necessity_items - necessity_items
        sufficiency_adjusted = sufficiency_items - random_sufficiency_items
        necessity_test = _sign_flip(necessity_adjusted, draws=draws, seed=2026090400 + site_index * 10)
        sufficiency_test = _sign_flip(sufficiency_adjusted, draws=draws, seed=2026090401 + site_index * 10)
        necessity_interval = _bootstrap(necessity_adjusted, replicates=replicates, seed=2026090500 + site_index * 10)
        sufficiency_interval = _bootstrap(sufficiency_adjusted, replicates=replicates, seed=2026090501 + site_index * 10)
        zero_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, 0] - queries[:, 0]) ** 2)))
        zero_cp_rms = float(np.sqrt(np.mean((codepoint_conditions[site_index, :, 0] - queries[:, 1]) ** 2)))
        restoration_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, 3] - queries[:, 0]) ** 2)))
        row = {
            "site": site,
            "block_index": block_index,
            "primary_site": (site, block_index) in PRIMARY_SITES,
            "baseline_glyph": base_glyph_metrics,
            "baseline_codepoint": base_codepoint_metrics,
            "conditions": {
                "zero_glyph": zero_glyph_metrics,
                "necessity": necessity_metrics,
                "random_necessity": random_necessity_metrics,
                "restoration": restoration_metrics,
                "zero_codepoint": zero_cp_metrics,
                "sufficiency": sufficiency_metrics,
                "random_sufficiency": random_sufficiency_metrics,
            },
            "necessity_adjusted_effect": float(np.mean(necessity_adjusted)),
            "sufficiency_adjusted_effect": float(np.mean(sufficiency_adjusted)),
            "necessity_test": necessity_test,
            "sufficiency_test": sufficiency_test,
            "necessity_interval": necessity_interval,
            "sufficiency_interval": sufficiency_interval,
            "site_iut_p": max(float(necessity_test["p_value_one_sided"]), float(sufficiency_test["p_value_one_sided"])),
            "practical_and_interval_pass": bool(
                float(np.mean(necessity_adjusted)) >= practical
                and float(np.mean(sufficiency_adjusted)) >= practical
                and float(necessity_interval["lower_95"]) > practical
                and float(sufficiency_interval["lower_95"]) > practical
            ),
            "engineering": {
                "zero_glyph_final_rms": zero_rms,
                "zero_codepoint_final_rms": zero_cp_rms,
                "restoration_final_rms": restoration_rms,
                "pass": max(zero_rms, zero_cp_rms, restoration_rms) <= 1e-6,
            },
        }
        rows.append(row)
    primary_rows = sorted((row for row in rows if row["primary_site"]), key=lambda row: (float(row["site_iut_p"]), str(row["site"])))
    still = True
    for index, row in enumerate(primary_rows):
        threshold = 0.05 / (len(primary_rows) - index)
        reject = still and float(row["site_iut_p"]) <= threshold
        still = bool(reject)
        row["holm_rank"] = index + 1
        row["holm_threshold"] = threshold
        row["primary_positive"] = bool(reject and row["practical_and_interval_pass"] and row["engineering"]["pass"])
    positive_sites = [f"{row['site']}:{row['block_index']}" for row in primary_rows if row["primary_positive"]]
    output.mkdir(parents=True)
    _write_json(output / "causal_site_results.json", {"schema_version": SCHEMA_VERSION, "protocol_id": PROTOCOL_ID, "sites": rows})
    primary_result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_primary_complete",
        "primary_sites": [{"site": row["site"], "block_index": row["block_index"], "site_iut_p": row["site_iut_p"], "holm_threshold": row["holm_threshold"], "positive": row["primary_positive"]} for row in sorted(primary_rows, key=lambda row: PRIMARY_SITES.index((str(row["site"]), int(row["block_index"]))))],
        "positive_sites": positive_sites,
        "positive": bool(positive_sites),
        "claim_boundary": t19._config()["claim_boundary"],
    }
    _write_json(output / "causal_primary_result.json", primary_result)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "causal_analysis_complete",
        "evaluation_receipt_sha256": evaluation["evaluation_receipt_sha256"],
        "sites": len(rows),
        "primary_positive": primary_result["positive"],
        "positive_sites": positive_sites,
        "sign_flip_draws_per_component": draws,
        "bootstrap_replicates_per_component": replicates,
        "outputs": {name: _sha256(output / name) for name in ("causal_site_results.json", "causal_primary_result.json")},
    }
    _write_json(output / "analysis_receipt.json", receipt)
    t19.engine._write_ledger(output, ("causal_site_results.json", "causal_primary_result.json", "analysis_receipt.json"))
    return {"status": "pass", "primary_positive": primary_result["positive"], "positive_sites": positive_sites, "analysis_receipt_sha256": _sha256(output / "analysis_receipt.json")}


def validate_analysis(output: Path) -> dict[str, Any]:
    receipt = _read_json(output / "analysis_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "causal_analysis_complete", "Causal analysis receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output / name) == expected, f"Causal analysis output changed: {name}")
    primary = _read_json(output / "causal_primary_result.json")
    _require(bool(primary["positive"]) == bool(receipt["primary_positive"]), "Causal primary mismatch")
    return {"status": "pass", "primary_positive": bool(primary["positive"]), "positive_sites": list(primary["positive_sites"]), "analysis_receipt_sha256": _sha256(output / "analysis_receipt.json")}


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    sub = value.add_subparsers(dest="command", required=True)
    design = sub.add_parser("audit-design")
    design.add_argument("--output", type=Path)
    token = sub.add_parser("tokenizer-preflight")
    token.add_argument("--model-path", type=Path, required=True)
    token.add_argument("--output", type=Path, default=_root() / TOKENIZER_PREFLIGHT_PATH)
    go = sub.add_parser("admit-go")
    go.add_argument("--observational-analysis", type=Path, required=True)
    go.add_argument("--output", type=Path, default=_root() / GO_MANIFEST_PATH)
    go_audit = sub.add_parser("audit-go")
    go_audit.add_argument("--require-pushed", action="store_true")
    source = sub.add_parser("run-source")
    source.add_argument("--model-path", type=Path, required=True)
    source.add_argument("--output-root", type=Path, required=True)
    source_audit = sub.add_parser("validate-source")
    source_audit.add_argument("--output-root", type=Path, required=True)
    evaluation = sub.add_parser("run-evaluation")
    evaluation.add_argument("--model-path", type=Path, required=True)
    evaluation.add_argument("--source-root", type=Path, required=True)
    evaluation.add_argument("--output-root", type=Path, required=True)
    evaluation_audit = sub.add_parser("validate-evaluation")
    evaluation_audit.add_argument("--source-root", type=Path, required=True)
    evaluation_audit.add_argument("--output-root", type=Path, required=True)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--source-root", type=Path, required=True)
    analysis.add_argument("--evaluation-root", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    analysis_audit = sub.add_parser("validate-analysis")
    analysis_audit.add_argument("--output", type=Path, required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design(args.output)
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(args.model_path, args.output)
    elif args.command == "admit-go":
        result = admit_go(args.observational_analysis, args.output)
    elif args.command == "audit-go":
        result = audit_go(require_pushed=args.require_pushed)
    elif args.command == "run-source":
        result = run_source(args.model_path, args.output_root)
    elif args.command == "validate-source":
        result = validate_source(args.output_root)
    elif args.command == "run-evaluation":
        result = run_evaluation(args.model_path, args.source_root, args.output_root)
    elif args.command == "validate-evaluation":
        result = validate_evaluation(args.output_root, args.source_root)
    elif args.command == "analyze":
        result = analyze(args.evaluation_root, args.source_root, args.output)
    elif args.command == "validate-analysis":
        result = validate_analysis(args.output)
    else:
        raise AssertionError(args.command)
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
