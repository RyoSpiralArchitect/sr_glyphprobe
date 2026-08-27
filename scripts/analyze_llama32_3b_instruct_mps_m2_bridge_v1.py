#!/usr/bin/env python3
"""Outcome-blind analysis correction v1 for the Llama M2 bridge v0.

The analyzer reads four complete stored-fingerprint runs, validates their exact
model/config/input grid, and rebuilds all leave-one-target-group-out prototypes
inside one joint stratified bootstrap. The first endpoint subtracts the median
of the three minimum-overlap null panels; the mandatory sensitivity subtracts
the fully disjoint panel A alone. No model is loaded and protected P2/C1 banks
are outside the input surface.

Correction v1 changes only the validation of ``resolved_config.yaml``: that
file preserves normalized depth specifications ``[0.2, 0.4]`` while the run
summary separately records resolved layers ``[5, 11]``. Analysis v0 failed at
that first config check before opening any run receipt, summary, or ledger.
"""

from __future__ import annotations

import argparse
import copy
from collections import defaultdict
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np
import orjson
import yaml


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ID = "glyphprobe-llama32-3b-instruct-mps-m2-bridge-analysis-v1"
ANALYSIS_MANIFEST_PATH = (
    ROOT
    / "data"
    / "manifests"
    / "llama32_3b_instruct_mps_m2_bridge_analysis_v1.json"
)
EXECUTION_RECEIPT_PATH = (
    ROOT
    / "validation"
    / "llama32_3b_instruct_mps_m2_bridge_v0"
    / "execution.json"
)
EXECUTION_RECEIPT_SHA256 = "1d872ae1474422f743f1bf92433fcefb159cc512355a6bc4ddd99f65656638e2"
MODEL_ALIAS = "/private/tmp/glyphprobe-llama32-3b-instruct-v0"
MODEL_REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"
MODEL_MANIFEST_SHA256 = "c698f962b8587e2c38dcb86e344928aa5db3c7386e160230d493fcaf9166ecf6"
TARGET_PATH = ROOT / "data" / "targets" / "prestage_targets.jsonl"
TARGET_SHA256 = "91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7"
TARGET_FIRST24_SHA256 = "26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b"
WRAPPER_PATH = ROOT / "data" / "wrappers" / "source_wrappers.jsonl"
WRAPPER_SHA256 = "310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee"
EXPECTED_TARGET_GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
)
LAYERS = (5, 11)
STRENGTH = 0.05
DIRECTION_SEEDS = (101, 211, 307)
FINGERPRINT_DIM = 96
FINGERPRINT_SEED = 8675309
RANDOM_DIRECTIONS_PER_LAYER = 8
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20260828
BOOTSTRAP_CHUNK_SIZE = 128
DELTA = 0.06
EPSILON = 1.0e-12
ROLE_ORDER = ("primary", "null_a", "null_b", "null_c")
CONFIG_PATHS = {
    "primary": ROOT / "configs" / "llama32_3b_instruct_mps_m2_primary_v0.yaml",
    "null_a": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_a_v0.yaml",
    "null_b": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_b_v0.yaml",
    "null_c": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_c_v0.yaml",
}
PANEL_PATHS = {
    "primary": ROOT / "data" / "emoji_panels" / "colored_shapes.yaml",
    "null_a": ROOT / "data" / "emoji_panels" / "llama32_m2_matched_null_a_v2.yaml",
    "null_b": ROOT / "data" / "emoji_panels" / "llama32_m2_matched_null_b_v2.yaml",
    "null_c": ROOT / "data" / "emoji_panels" / "llama32_m2_matched_null_c_v2.yaml",
}
PANEL_SHA256 = {
    "primary": "6c9138425f1744d700040c0562c8521472d249f39bd97ff6106fa68cd3c19e97",
    "null_a": "2bcafdc1ec855606d84c2f606b66b60bb5ca3c8a8631b9b532b6054b1a4ccc03",
    "null_b": "5764afad3e07ad2f18c1012ccbe2ff90f7d37c822513793385dc5d579a1b421f",
    "null_c": "5a771c9fecd8453a125b43e50340a4dc6d0d1814308f6237fbb6a14fa76a8a82",
}

BASE_ANALYZER = ROOT / "scripts" / "analyze_m2_confirmatory.py"
BASE_SPEC = importlib.util.spec_from_file_location("glyphprobe_m2_math_v1", BASE_ANALYZER)
if BASE_SPEC is None or BASE_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Cannot load analysis math: {BASE_ANALYZER}")
BASE = importlib.util.module_from_spec(BASE_SPEC)
BASE_SPEC.loader.exec_module(BASE)

DEPENDENCE_ANALYZER = ROOT / "scripts" / "analyze_m2_dependence_sensitivity_v1.py"
DEP_SPEC = importlib.util.spec_from_file_location(
    "glyphprobe_m2_dependence_math_v1", DEPENDENCE_ANALYZER
)
if DEP_SPEC is None or DEP_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Cannot load bootstrap math: {DEPENDENCE_ANALYZER}")
sys.path.insert(0, str((ROOT / "scripts").resolve()))
try:
    DEP = importlib.util.module_from_spec(DEP_SPEC)
    DEP_SPEC.loader.exec_module(DEP)
finally:
    sys.path.pop(0)


class BridgeAnalysisError(RuntimeError):
    """Raised when frozen evidence or an analysis invariant fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BridgeAnalysisError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _selected_lines_sha256(path: Path, count: int) -> str:
    with path.open("rb") as handle:
        lines = [line for line in handle if line.strip()]
    _require(len(lines) >= count, f"{path.name} has fewer than {count} rows")
    return hashlib.sha256(b"".join(lines[:count])).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    _require(path.is_file() and not path.is_symlink(), f"Missing JSONL: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = orjson.loads(line)
            _require(isinstance(value, dict), f"Non-object at {path}:{line_number}")
            rows.append(value)
    return rows


def _read_json(path: Path) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(), f"Missing JSON: {path}")
    value = orjson.loads(path.read_bytes())
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise BridgeAnalysisError(
            result.stderr.strip() or f"git {' '.join(args)} failed"
        )
    return result.stdout.strip()


def _validate_public_analysis_freeze() -> dict[str, Any]:
    _require(
        ANALYSIS_MANIFEST_PATH.is_file() and not ANALYSIS_MANIFEST_PATH.is_symlink(),
        "Analysis correction manifest is missing",
    )
    manifest = _read_json(ANALYSIS_MANIFEST_PATH)
    _require(manifest.get("analysis_id") == ANALYSIS_ID, "Analysis manifest ID differs")
    _require(
        manifest.get("status") == "outcome_blind_analysis_correction_v1_frozen",
        "Analysis manifest status differs",
    )
    files = manifest.get("static_files")
    _require(isinstance(files, Mapping) and files, "Analysis static file map is missing")
    _require(manifest.get("static_file_count") == len(files), "Static file count differs")
    for relative, expected in files.items():
        path = (ROOT / str(relative)).resolve()
        _require(ROOT in path.parents, f"Static path escapes repository: {relative}")
        _require(path.is_file() and not path.is_symlink(), f"Static file missing: {relative}")
        _require(path.stat().st_size == expected["bytes"], f"Static bytes differ: {relative}")
        _require(_sha256_file(path) == expected["sha256"], f"Static hash differs: {relative}")

    _require(
        _sha256_file(EXECUTION_RECEIPT_PATH) == EXECUTION_RECEIPT_SHA256,
        "Execution receipt hash differs",
    )
    execution = _read_json(EXECUTION_RECEIPT_PATH)
    _require(
        execution.get("status") == "execution_complete_analysis_not_run",
        "Execution receipt status differs",
    )
    _require(execution.get("analysis_authorized") is True, "Execution did not authorize analysis")
    _require(execution.get("completed_process_count") == 4, "Execution process count differs")
    _require(execution.get("expected_process_count") == 4, "Expected process count differs")

    _require(not _git("status", "--porcelain"), "Analysis requires a clean public worktree")
    branch = _git("branch", "--show-current")
    head = _git("rev-parse", "HEAD")
    origin = _git("rev-parse", "origin/main")
    _require(branch == "main", f"Analysis requires main, observed {branch!r}")
    _require(head == origin, "Analysis HEAD must equal origin/main")
    return {
        "analysis_manifest": {
            "path": ANALYSIS_MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": _sha256_file(ANALYSIS_MANIFEST_PATH),
            "all_static_hashes_verified": True,
        },
        "execution_receipt": {
            "path": EXECUTION_RECEIPT_PATH.relative_to(ROOT).as_posix(),
            "sha256": EXECUTION_RECEIPT_SHA256,
            "analysis_authorized": True,
        },
        "git_authority": {
            "branch": branch,
            "analysis_commit": head,
            "origin_main_commit": origin,
            "worktree_clean_before_analysis": True,
        },
    }


def _nested(value: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = value
    for part in path:
        _require(isinstance(current, Mapping) and part in current, f"Missing config field {'.'.join(path)}")
        current = current[part]
    return current


def _target_authority() -> tuple[dict[str, str], tuple[str, ...]]:
    _require(_sha256_file(TARGET_PATH) == TARGET_SHA256, "Prestage target hash differs")
    _require(
        _selected_lines_sha256(TARGET_PATH, 24) == TARGET_FIRST24_SHA256,
        "First-24 prestage slice hash differs",
    )
    rows = _read_jsonl(TARGET_PATH)[:24]
    _require(len(rows) == 24, "Need exactly 24 prestage targets")
    groups: dict[str, str] = {}
    ids: list[str] = []
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        target_id = row.get("id")
        group = row.get("group")
        prompt = row.get("prompt")
        _require(isinstance(target_id, str) and target_id, "Target ID missing")
        _require(isinstance(group, str) and group in EXPECTED_TARGET_GROUPS, "Target group differs")
        _require(isinstance(prompt, str) and prompt, "Target prompt missing")
        _require(target_id not in groups, "Duplicate target ID")
        groups[target_id] = group
        ids.append(target_id)
        counts[group] += 1
    _require(counts == {group: 4 for group in EXPECTED_TARGET_GROUPS}, "Target strata are not six by four")
    return groups, tuple(ids)


def _common_config_signature(config: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(dict(config))
    normalized.pop("panel", None)
    run = normalized.get("run")
    if isinstance(run, dict):
        run.pop("name", None)
        run.pop("output_root", None)
    return normalized


def _validate_config(config: Mapping[str, Any], role: str) -> None:
    _require(role in ROLE_ORDER, f"Unknown panel role: {role}")
    panel_files = {
        "primary": "../data/emoji_panels/colored_shapes.yaml",
        "null_a": "../data/emoji_panels/llama32_m2_matched_null_a_v2.yaml",
        "null_b": "../data/emoji_panels/llama32_m2_matched_null_b_v2.yaml",
        "null_c": "../data/emoji_panels/llama32_m2_matched_null_c_v2.yaml",
    }
    run_names = {
        "primary": "llama32-3b-instruct-mps-m2-primary-v0",
        "null_a": "llama32-3b-instruct-mps-m2-null-a-v0",
        "null_b": "llama32-3b-instruct-mps-m2-null-b-v0",
        "null_c": "llama32-3b-instruct-mps-m2-null-c-v0",
    }
    expected = {
        ("schema_version",): 1,
        ("mode",): "internal",
        ("backend", "kind"): "transformers",
        ("backend", "model"): MODEL_ALIAS,
        ("backend", "revision"): MODEL_REVISION,
        ("backend", "device"): "mps",
        ("backend", "dtype"): "bfloat16",
        ("backend", "local_files_only"): True,
        ("backend", "add_special_tokens"): False,
        ("backend", "trust_remote_code"): False,
        ("run", "name"): run_names[role],
        ("run", "output_root"): "../runs",
        ("run", "seeds"): list(DIRECTION_SEEDS),
        ("run", "deterministic_torch"): False,
        ("run", "resume"): False,
        ("run", "fail_fast"): True,
        ("run", "replicate_mode"): "wrapper_subsample",
        ("run", "wrapper_subsample_fraction"): 0.75,
        ("panel", "file"): panel_files[role],
        ("panel", "neutral_glyph"): "🟰",
        ("panel", "centroid_mode"): "panel",
        ("source", "wrappers_file"): "../data/wrappers/source_wrappers.jsonl",
        ("source", "max_wrappers"): 16,
        ("source", "anchor_position"): "last_nonpad",
        ("targets", "cases_file"): "../data/targets/prestage_targets.jsonl",
        ("targets", "max_cases"): 24,
        ("targets", "calibration_cases"): 6,
        ("capture", "site"): "resid_post",
        ("capture", "layers"): [0.2, 0.4],
        ("capture", "position"): "last_nonpad",
        ("capture", "return_attentions"): False,
        ("intervention", "mode"): "activation_add",
        ("intervention", "normalization"): "rms",
        ("intervention", "strengths"): [STRENGTH],
        ("intervention", "position"): "last_nonpad",
        ("intervention", "clip", "mode"): "global_rms",
        ("intervention", "clip", "max_ratio"): 0.25,
        ("intervention", "iso_kl", "enabled"): False,
        ("controls", "random_directions_per_layer"): RANDOM_DIRECTIONS_PER_LAYER,
        ("controls", "zero_direction"): True,
        ("controls", "sign_flip"): False,
        ("controls", "sign_flip_strengths"): [],
        ("controls", "label_shuffle_permutations"): 0,
        ("controls", "include_neutral_direction"): False,
        ("metrics", "top_k"): 50,
        ("metrics", "fingerprint_dim"): FINGERPRINT_DIM,
        ("metrics", "fingerprint_seed"): FINGERPRINT_SEED,
        ("metrics", "split_half_repeats"): 200,
        ("metrics", "rbo_p"): 0.9,
        ("metrics", "save_top_logit_deltas"): 32,
        ("metrics", "save_fingerprints"): True,
        ("metrics", "epsilon"): EPSILON,
        ("sae", "enabled"): False,
        ("surface", "emoji_template"): "{emoji}\n{prompt}",
        ("surface", "neutral_template"): "{prompt}",
        ("surface", "system_prompt"): None,
    }
    for path, wanted in expected.items():
        observed = _nested(config, path)
        _require(observed == wanted and type(observed) is type(wanted), f"Frozen config differs for {role}:{'.'.join(path)}")


def _extract_fingerprint(row: Mapping[str, Any], line_number: int) -> np.ndarray:
    distribution = row.get("distribution")
    value = distribution.get("fingerprint") if isinstance(distribution, Mapping) else None
    vector = np.asarray(value, dtype=np.float64)
    _require(vector.shape == (FINGERPRINT_DIM,), f"Fingerprint shape differs at row {line_number}")
    _require(np.all(np.isfinite(vector)), f"Non-finite fingerprint at row {line_number}")
    norm = float(np.linalg.norm(vector))
    _require(norm > EPSILON, f"Zero fingerprint at row {line_number}")
    return vector / norm


def _load_panel_run(
    run_dir: Path,
    role: str,
    target_groups: Mapping[str, str],
    target_ids: Sequence[str],
) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    _require(run_dir.is_dir() and not run_dir.is_symlink(), f"Missing run: {run_dir}")
    config_path = run_dir / "resolved_config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    _require(isinstance(config, dict), f"Resolved config is invalid: {run_dir}")
    _validate_config(config, role)

    receipt = _read_json(run_dir / "receipt.json")
    _require(receipt.get("status") == "complete", f"Run is incomplete: {role}")
    _require(receipt.get("backend", {}).get("model") == MODEL_ALIAS, f"Run model alias differs: {role}")
    model_receipt = receipt.get("model_receipt", {})
    _require(model_receipt.get("backend") == "transformers", f"Backend receipt differs: {role}")
    _require(model_receipt.get("device") == "mps", f"Model device differs: {role}")
    _require(model_receipt.get("dtype") == "bfloat16", f"Model dtype differs: {role}")
    _require(model_receipt.get("num_layers") == 28, f"Layer count differs: {role}")
    _require(model_receipt.get("d_model") == 3072, f"Model width differs: {role}")
    _require(model_receipt.get("parameter_count") == 3_212_749_824, f"Parameter count differs: {role}")
    artifact = model_receipt.get("model_artifact", {})
    _require(artifact.get("manifest_sha256") == MODEL_MANIFEST_SHA256, f"Model artifact differs: {role}")

    resolved_inputs = _read_json(run_dir / "resolved_inputs.json")
    _require(tuple(resolved_inputs.get("target_ids", [])) == tuple(target_ids), f"Target order differs: {role}")
    wrapper_ids = resolved_inputs.get("wrapper_ids", [])
    _require(isinstance(wrapper_ids, list) and len(wrapper_ids) == 16 and len(set(wrapper_ids)) == 16, f"Wrapper grid differs: {role}")
    panel_rows = resolved_inputs.get("panel", [])
    _require(isinstance(panel_rows, list) and len(panel_rows) == 10, f"Panel size differs: {role}")
    condition_ids = tuple(str(row["id"]) for row in panel_rows)
    glyph_by_condition = {str(row["id"]): str(row["glyph"]) for row in panel_rows}
    _require(len(set(condition_ids)) == 10 and len(set(glyph_by_condition.values())) == 10, f"Panel uniqueness differs: {role}")

    expected_hashes = {
        f"input_00:{CONFIG_PATHS[role].name}": _sha256_file(CONFIG_PATHS[role]),
        f"input_01:{PANEL_PATHS[role].name}": PANEL_SHA256[role],
        f"input_02:{WRAPPER_PATH.name}": WRAPPER_SHA256,
        f"input_03:{TARGET_PATH.name}": TARGET_SHA256,
    }
    _require(receipt.get("input_hashes") == expected_hashes, f"Run input hashes differ: {role}")

    summary = _read_json(run_dir / "summary.json")
    _require(summary.get("error_count") == 0, f"Run contains errors: {role}")
    _require(summary.get("resolved_layers") == list(LAYERS), f"Resolved layers differ: {role}")
    _require(summary.get("seed_count") == 3 and summary.get("target_case_count") == 24, f"Run dimensions differ: {role}")
    _require(summary.get("random_control_count") == 2 * 3 * 24 * RANDOM_DIRECTIONS_PER_LAYER, f"Random control count differs: {role}")
    _require(summary.get("zero_hook_control_count") == 2 * 24, f"Zero-hook count differs: {role}")
    _require(float(summary.get("zero_hook_max_activation_delta_rms", math.inf)) <= 1e-6, f"Zero-hook activation failed: {role}")
    _require(float(summary.get("zero_hook_max_logit_delta_rms", math.inf)) <= 1e-6, f"Zero-hook logits failed: {role}")

    ledger_path = run_dir / "interventions.jsonl"
    raw_rows = _read_jsonl(ledger_path)
    vectors: dict[tuple[int, float, int, str, str], np.ndarray] = {}
    observed_targets: dict[str, str] = {}
    cells: set[tuple[int, float, int]] = set()
    condition_types: dict[str, int] = defaultdict(int)
    for line_number, row in enumerate(raw_rows, 1):
        condition_type = str(row.get("condition_type", ""))
        condition_types[condition_type] += 1
        if not (
            condition_type == "emoji"
            and row.get("sign") == 1
            and row.get("calibration") == "rms"
        ):
            continue
        layer = int(row["layer"])
        strength = float(row["strength"])
        seed = int(row["seed"])
        condition_id = str(row["condition_id"])
        target_id = str(row["target_id"])
        target_group = str(row["target_group"])
        _require(condition_id in glyph_by_condition, f"Unknown condition in {role}")
        _require(target_groups.get(target_id) == target_group, f"Target group differs in {role}")
        key = (layer, strength, seed, condition_id, target_id)
        _require(key not in vectors, f"Duplicate emoji row in {role}")
        vectors[key] = _extract_fingerprint(row, line_number)
        observed_targets[target_id] = target_group
        cells.add((layer, strength, seed))
    expected_cells = {
        (layer, STRENGTH, seed) for layer in LAYERS for seed in DIRECTION_SEEDS
    }
    _require(cells == expected_cells, f"Cell grid differs: {role}")
    _require(observed_targets == dict(target_groups), f"Target grid differs: {role}")
    expected_keys = {
        (layer, STRENGTH, seed, condition_id, target_id)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_id in condition_ids
        for target_id in target_ids
    }
    _require(set(vectors) == expected_keys, f"Emoji grid is incomplete: {role}")
    _require(condition_types.get("emoji") == 1440, f"Emoji row count differs: {role}")
    _require(condition_types.get("random") == 1152, f"Random row count differs: {role}")
    _require(condition_types.get("zero") == 48, f"Zero row count differs: {role}")
    _require(sum(condition_types.values()) == 2640, f"Ledger row count differs: {role}")
    return {
        "label": role,
        "run_dir": run_dir,
        "ledger_path": ledger_path,
        "config_path": config_path,
        "config": config,
        "analysis_config": _common_config_signature(config),
        "vectors": vectors,
        "conditions": tuple(sorted(condition_ids)),
        "targets": dict(target_groups),
        "cells": cells,
        "eligible_row_count": len(vectors),
        "glyph_by_condition": glyph_by_condition,
        "summary": summary,
        "receipt": receipt,
    }


def _validate_cross_panel(panels: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reference = panels[0]
    for panel in panels[1:]:
        _require(panel["targets"] == reference["targets"], "Cross-panel target grid differs")
        _require(panel["cells"] == reference["cells"], "Cross-panel cell grid differs")
        _require(panel["analysis_config"] == reference["analysis_config"], "Cross-panel config differs")
    glyph_sets = {
        panel["label"]: set(panel["glyph_by_condition"].values()) for panel in panels
    }
    _require(all(not glyph_sets["primary"] & glyph_sets[role] for role in ROLE_ORDER[1:]), "Primary overlaps a null panel")
    observed = {
        "null_a_null_b": sorted(glyph_sets["null_a"] & glyph_sets["null_b"]),
        "null_a_null_c": sorted(glyph_sets["null_a"] & glyph_sets["null_c"]),
        "null_b_null_c": sorted(glyph_sets["null_b"] & glyph_sets["null_c"]),
    }
    _require(observed == {"null_a_null_b": ["🟀"], "null_a_null_c": [], "null_b_null_c": ["🟄"]}, "Null overlap contract differs")
    return {"glyph_overlaps": observed, "null_panels_independent": False}


def _score_layer_chunk(
    layer_vectors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> tuple[np.ndarray, np.ndarray]:
    _require(layer_vectors.ndim == 5 and layer_vectors.shape[0] == 4, "Panel tensor shape differs")
    panel_count, seed_count, condition_count, target_count, _ = layer_vectors.shape
    _require(seed_count == 3 and condition_count == 10 and target_count == 24, "Tensor dimensions differ")
    floating_weights = weights.astype(np.float64, copy=False)
    batch_size = weights.shape[0]
    panel_target_scores = np.empty((batch_size, panel_count, target_count), dtype=np.float64)
    total_sums = np.einsum("bt,psctd->bpscd", floating_weights, layer_vectors, optimize=True)
    for raw_indices in group_indices:
        held_indices = np.asarray(raw_indices, dtype=np.int64)
        held_vectors = layer_vectors[:, :, :, held_indices, :]
        held_sums = np.einsum(
            "bh,pschd->bpscd",
            floating_weights[:, held_indices],
            held_vectors,
            optimize=True,
        )
        training_sums = total_sums - held_sums
        norms = np.linalg.norm(training_sums, axis=-1, keepdims=True)
        _require(np.all(np.isfinite(norms)) and np.all(norms > EPSILON), "Prototype norm failed")
        prototypes = training_sums / norms
        same_sum = np.einsum("bpscd,pschd->bpsh", prototypes, held_vectors, optimize=True)
        all_sum = np.einsum(
            "bpsd,pshd->bpsh",
            prototypes.sum(axis=3),
            held_vectors.sum(axis=2),
            optimize=True,
        )
        seed_scores = (condition_count * same_sum - all_sum) / (
            condition_count * (condition_count - 1)
        )
        panel_target_scores[:, :, held_indices] = seed_scores.mean(axis=2)
    ensemble_effects = panel_target_scores[:, 0] - np.median(
        panel_target_scores[:, 1:4], axis=1
    )
    panel_a_effects = panel_target_scores[:, 0] - panel_target_scores[:, 1]
    denominator = floating_weights.sum(axis=1)
    _require(np.all(denominator > 0), "Bootstrap replicate has zero mass")
    ensemble = np.sum(floating_weights * ensemble_effects, axis=1) / denominator
    panel_a = np.sum(floating_weights * panel_a_effects, axis=1) / denominator
    return ensemble, panel_a


def _bootstrap(
    panel_tensors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
    chunk_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    ensemble = np.empty((len(LAYERS), weights.shape[0]), dtype=np.float64)
    panel_a = np.empty_like(ensemble)
    for layer_index in range(len(LAYERS)):
        for start in range(0, weights.shape[0], chunk_size):
            stop = min(start + chunk_size, weights.shape[0])
            first, second = _score_layer_chunk(
                panel_tensors[:, layer_index], weights[start:stop], group_indices
            )
            ensemble[layer_index, start:stop] = first
            panel_a[layer_index, start:stop] = second
    _require(np.all(np.isfinite(ensemble)) and np.all(np.isfinite(panel_a)), "Bootstrap is non-finite")
    return ensemble, panel_a


def _atomic_write_no_overwrite(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.exists(), f"Refusing to overwrite output: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _input_record(panel: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "role": panel["label"],
        "run_id": panel["receipt"]["run_id"],
        "run_seal": panel["receipt"]["run_seal"],
        "ledger_sha256": _sha256_file(panel["ledger_path"]),
        "config_sha256": _sha256_file(panel["config_path"]),
        "eligible_emoji_rows": panel["eligible_row_count"],
        "model_artifact_manifest_sha256": panel["receipt"]["model_receipt"]["model_artifact"]["manifest_sha256"],
    }


def _render_report(receipt: Mapping[str, Any]) -> str:
    lines = [
        "# Llama 3.2 3B Instruct M2 bridge analysis correction v1 results",
        "",
        "This is a prospectively frozen but exploratory bridge on 24 previously used",
        "prestage targets. It is not an independent confirmation or a scale curve.",
        "",
        "| Layer | Ensemble mean | Ensemble 95% interval | Disjoint A-only mean | A-only 95% interval |",
        "|---:|---:|:---:|---:|:---:|",
    ]
    for row in receipt["results"]:
        lines.append(
            f"| {row['layer']} | {row['ensemble']['point_mean']:.8f} | "
            f"[{row['ensemble']['interval_95']['low']:.8f}, {row['ensemble']['interval_95']['high']:.8f}] | "
            f"{row['disjoint_panel_a_only']['point_mean']:.8f} | "
            f"[{row['disjoint_panel_a_only']['interval_95']['low']:.8f}, "
            f"{row['disjoint_panel_a_only']['interval_95']['high']:.8f}] |"
        )
    lines.extend(
        [
            "",
            f"Primary exploratory criterion: `{receipt['primary_decision']['status']}`.",
            "Both layer-5 lower bounds must exceed the prespecified delta 0.06; layer 11",
            "cannot rescue layer 5.",
            "",
            "The null ensemble has the unavoidable two-placement overlap documented by",
            "the tokenizer-only design. Panel A is fully disjoint and is therefore reported",
            "as a mandatory sensitivity. Random directions and zero hooks are secondary",
            "integrity controls. No p-value or confirmatory status is assigned.",
            "",
            "No model forward was performed by this analyzer, and P2/C1 were not accessed.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze(
    run_dirs: Mapping[str, Path],
    *,
    output_dir: Path,
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES,
    bootstrap_seed: int = BOOTSTRAP_SEED,
    chunk_size: int = BOOTSTRAP_CHUNK_SIZE,
) -> dict[str, Any]:
    analysis_freeze = _validate_public_analysis_freeze()
    _require(set(run_dirs) == set(ROLE_ORDER), "Four named run roles are required")
    _require(len({Path(path).resolve() for path in run_dirs.values()}) == 4, "Run paths must be distinct")
    target_groups, ordered_target_ids = _target_authority()
    _require(_sha256_file(WRAPPER_PATH) == WRAPPER_SHA256, "Wrapper hash differs")
    for role in ROLE_ORDER:
        _require(_sha256_file(PANEL_PATHS[role]) == PANEL_SHA256[role], f"Panel hash differs: {role}")
    panels = [
        _load_panel_run(run_dirs[role], role, target_groups, ordered_target_ids)
        for role in ROLE_ORDER
    ]
    overlap = _validate_cross_panel(panels)
    target_ids, group_indices = DEP._ordered_target_grid(target_groups)
    panel_tensors = DEP._stack_panels(
        panels,
        layers=LAYERS,
        direction_seeds=DIRECTION_SEEDS,
        strength=STRENGTH,
        target_ids=target_ids,
    )
    weights = DEP._stratified_bootstrap_weights(
        replicates=bootstrap_replicates,
        seed=bootstrap_seed,
        target_count=len(target_ids),
        group_indices=group_indices,
    )
    point_weights = np.ones((1, len(target_ids)), dtype=np.int16)
    point_ensemble: list[float] = []
    point_a: list[float] = []
    for layer_index in range(len(LAYERS)):
        first, second = _score_layer_chunk(
            panel_tensors[:, layer_index], point_weights, group_indices
        )
        point_ensemble.append(float(first[0]))
        point_a.append(float(second[0]))
    ensemble_dist, a_dist = _bootstrap(
        panel_tensors, weights, group_indices, int(chunk_size)
    )

    target_rows: list[dict[str, Any]] = []
    for layer in LAYERS:
        scores = [
            BASE._panel_target_scores(
                panel,
                layer=layer,
                strength=STRENGTH,
                direction_seeds=DIRECTION_SEEDS,
            )[0]
            for panel in panels
        ]
        for target_id in target_ids:
            null_values = [float(row[target_id]) for row in scores[1:]]
            target_rows.append(
                {
                    "layer": layer,
                    "target_id": target_id,
                    "target_group": target_groups[target_id],
                    "primary_score": float(scores[0][target_id]),
                    "null_scores": {
                        "a": null_values[0],
                        "b": null_values[1],
                        "c": null_values[2],
                    },
                    "ensemble_adjusted_effect": float(
                        scores[0][target_id] - np.median(null_values)
                    ),
                    "disjoint_panel_a_adjusted_effect": float(
                        scores[0][target_id] - null_values[0]
                    ),
                }
            )

    results: list[dict[str, Any]] = []
    for index, layer in enumerate(LAYERS):
        ensemble_low, ensemble_high = np.quantile(ensemble_dist[index], (0.025, 0.975))
        a_low, a_high = np.quantile(a_dist[index], (0.025, 0.975))
        results.append(
            {
                "layer": layer,
                "normalized_depth_spec": [0.2, 0.4][index],
                "role": "primary" if layer == 5 else "secondary_non_rescuing_comparator",
                "ensemble": {
                    "point_mean": point_ensemble[index],
                    "interval_95": {"low": float(ensemble_low), "high": float(ensemble_high)},
                    "lower_bound_exceeds_delta": bool(ensemble_low > DELTA),
                },
                "disjoint_panel_a_only": {
                    "point_mean": point_a[index],
                    "interval_95": {"low": float(a_low), "high": float(a_high)},
                    "lower_bound_exceeds_delta": bool(a_low > DELTA),
                },
            }
        )
    primary_pass = (
        results[0]["ensemble"]["lower_bound_exceeds_delta"]
        and results[0]["disjoint_panel_a_only"]["lower_bound_exceeds_delta"]
    )
    primary_decision = {
        "layer": 5,
        "delta": DELTA,
        "status": (
            "exploratory_bridge_pattern_observed"
            if primary_pass
            else "exploratory_bridge_criterion_not_met"
        ),
        "requires_both_ensemble_and_disjoint_a_lower_bounds_above_delta": True,
        "layer_11_can_rescue": False,
        "confirmatory_status": False,
    }

    output_dir = output_dir.resolve()
    _require(not output_dir.exists(), f"Refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    target_path = output_dir / "target_effects.jsonl"
    bootstrap_path = output_dir / "bootstrap_layer_means.jsonl"
    report_path = output_dir / "report.md"
    receipt_path = output_dir / "analysis_receipt.json"
    _atomic_write_no_overwrite(
        target_path,
        b"".join(orjson.dumps(row, option=orjson.OPT_SORT_KEYS) + b"\n" for row in target_rows),
    )
    bootstrap_rows = [
        {
            "replicate_index": replicate,
            "layers": {
                str(layer): {
                    "ensemble": float(ensemble_dist[index, replicate]),
                    "disjoint_panel_a_only": float(a_dist[index, replicate]),
                }
                for index, layer in enumerate(LAYERS)
            },
        }
        for replicate in range(bootstrap_replicates)
    ]
    _atomic_write_no_overwrite(
        bootstrap_path,
        b"".join(orjson.dumps(row, option=orjson.OPT_SORT_KEYS) + b"\n" for row in bootstrap_rows),
    )
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "analysis_id": ANALYSIS_ID,
        "status": "complete",
        "claim_boundary": {
            "exploratory": True,
            "reused_prestage_targets": True,
            "independent_confirmation": False,
            "scale_curve": False,
            "tokenization_free": False,
            "semantic_or_causal_claim": False,
            "model_forward_count_by_analyzer": 0,
            "protected_p2_or_c1_accessed": False,
            "analysis_correction_version": 1,
            "analysis_v0_failed_before_outcome_read": True,
        },
        "inputs": [_input_record(panel) for panel in panels],
        "model_cell": {
            "model": "meta-llama/Llama-3.2-3B-Instruct",
            "revision": MODEL_REVISION,
            "artifact_manifest_sha256": MODEL_MANIFEST_SHA256,
            "backend": "transformers",
            "device": "mps",
            "runtime_dtype": "bfloat16",
        },
        "parameters": {
            "layers": list(LAYERS),
            "normalized_depth_specs": [0.2, 0.4],
            "resolved_layers_validated_from_run_summary": list(LAYERS),
            "strength": STRENGTH,
            "direction_seeds": list(DIRECTION_SEEDS),
            "random_directions_per_layer": RANDOM_DIRECTIONS_PER_LAYER,
            "fingerprint_dim": FINGERPRINT_DIM,
            "fingerprint_seed": FINGERPRINT_SEED,
            "bootstrap_replicates": bootstrap_replicates,
            "bootstrap_seed": bootstrap_seed,
            "chunk_size_computational_only": chunk_size,
            "delta": DELTA,
        },
        "resampling": {
            "unit": "target",
            "strata": list(EXPECTED_TARGET_GROUPS),
            "draws_per_stratum": [4] * 6,
            "joint_across_panels_layers_and_endpoints": True,
            "prototype_rebuilt_inside_each_replicate": True,
            "direction_seeds_averaged_inside_target": True,
        },
        "panel_dependence": overlap,
        "results": results,
        "primary_decision": primary_decision,
        "secondary_run_summaries": {
            panel["label"]: {
                "emoji_fingerprint_advantage": panel["summary"].get("emoji_fingerprint_advantage"),
                "cross_seed_fingerprint_advantage": panel["summary"].get("cross_seed_fingerprint_advantage"),
                "random_control_count": panel["summary"].get("random_control_count"),
                "zero_hook_max_activation_delta_rms": panel["summary"].get("zero_hook_max_activation_delta_rms"),
                "zero_hook_max_logit_delta_rms": panel["summary"].get("zero_hook_max_logit_delta_rms"),
            }
            for panel in panels
        },
        "validation": {
            "public_analysis_freeze": analysis_freeze,
            "analyzer_sha256": _sha256_file(Path(__file__)),
            "base_math_sha256": _sha256_file(BASE_ANALYZER),
            "dependence_math_sha256": _sha256_file(DEPENDENCE_ANALYZER),
            "target_slice_sha256": TARGET_FIRST24_SHA256,
            "wrapper_sha256": WRAPPER_SHA256,
            "target_effect_row_count": len(target_rows),
            "bootstrap_row_count": len(bootstrap_rows),
        },
    }
    report = _render_report(receipt)
    _atomic_write_no_overwrite(report_path, report.encode("utf-8"))
    receipt["outputs"] = {
        "target_effects": {"file": target_path.name, "sha256": _sha256_file(target_path)},
        "bootstrap_layer_means": {"file": bootstrap_path.name, "sha256": _sha256_file(bootstrap_path)},
        "report": {"file": report_path.name, "sha256": _sha256_file(report_path)},
    }
    _atomic_write_no_overwrite(
        receipt_path,
        orjson.dumps(receipt, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2) + b"\n",
    )
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-run", type=Path, required=True)
    parser.add_argument("--null-a-run", type=Path, required=True)
    parser.add_argument("--null-b-run", type=Path, required=True)
    parser.add_argument("--null-c-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        receipt = analyze(
            {
                "primary": args.primary_run,
                "null_a": args.null_a_run,
                "null_b": args.null_b_run,
                "null_c": args.null_c_run,
            },
            output_dir=args.output_dir,
        )
    except (BridgeAnalysisError, OSError, ValueError) as exc:
        print(f"analysis_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "analysis_id": ANALYSIS_ID,
                "status": receipt["status"],
                "primary_decision": receipt["primary_decision"],
                "output_dir": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
