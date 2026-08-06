#!/usr/bin/env python3
"""Analyze the fixed E1 token-isomorphic emoji-family exploratory lattice.

The CLI accepts exactly five role-bound run directories.  It reads stored
positive RMS emoji fingerprints, validates the complete exploratory cell, and
reports all within-family and ordered cross-family matched-slot endpoints.
Every stratified target-bootstrap replicate rebuilds all data-dependent
leave-one-target-group-out prototypes.  This is descriptive exploration: no
p-value, multiplicity decision, equivalence decision, selection, or status is
produced by this analyzer.

Only the existing 24-target prestage bank is accepted.  No holdout bank is
loaded or referenced by the implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import orjson
import yaml


ANALYSIS_ID = "glyphprobe-e1-token-isomorphic-emoji-families-v1"
SCHEMA_VERSION = 1
MODEL = "openai-community/gpt2"
REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
BACKEND = "mlx"
DTYPE = "float32"
SITE = "resid_post"
LAYERS = (2, 4)
PRIMARY_LAYER = 2
NEGATIVE_COMPARATOR_LAYER = 4
STRENGTH = 0.05
DIRECTION_SEEDS = (101, 211, 307)
FINGERPRINT_DIM = 96
FINGERPRINT_SEED = 8_675_309
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20_260_808
BOOTSTRAP_CHUNK_SIZE = 128
TARGET_GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
)
TARGETS_PER_GROUP = 4
CONDITIONS_PER_FAMILY = 10
EXPECTED_POSITIVE_ROWS_PER_RUN = (
    len(LAYERS) * len(DIRECTION_SEEDS) * CONDITIONS_PER_FAMILY
    * len(TARGET_GROUPS) * TARGETS_PER_GROUP
)
EXPECTED_RANDOM_ROWS_PER_RUN = 288
EXPECTED_ZERO_ROWS_PER_RUN = 48
EXPECTED_INTERVENTION_ROWS_PER_RUN = 1_776
EPSILON = 1e-12

PARITY_PATH = Path("validation/mlx_gpt2_parity/receipt.json")
PARITY_SHA256 = "98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679"
TARGET_PATH = Path("data/targets/prestage_targets.jsonl")
TARGET_SHA256 = "91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7"
SOURCE_PATH = Path("data/wrappers/source_wrappers.jsonl")
SOURCE_SHA256 = "310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee"
MANIFEST_PATH = Path("data/manifests/emoji_family_exploratory_v1.json")

ENDPOINT_WITHIN = "within_family_slot_separation_M_diag"
ENDPOINT_TRANSFER = "ordered_cross_family_same_slot_transfer_M_offdiag"
ENDPOINT_SPECIFICITY = "family_specificity_R"
ENDPOINT_GLOBAL = "equal_family_global_specificity_R_global"
OUTPUT_FILENAMES = (
    "family_target_scores.jsonl",
    "transfer_target_scores.jsonl",
    "family_cell_summary.jsonl",
    "transfer_cell_summary.jsonl",
    "emoji_family_exploratory_receipt.json",
    "report.md",
)
EXPECTED_OUTPUT_ROWS = {
    "family_target_scores.jsonl": 240,
    "transfer_target_scores.jsonl": 960,
    "family_cell_summary.jsonl": 10,
    "transfer_cell_summary.jsonl": 40,
}
OUTPUT_UNIQUE_KEYS = {
    "family_target_scores.jsonl": ["family", "layer", "target_id"],
    "transfer_target_scores.jsonl": [
        "source_family",
        "prototype_family",
        "layer",
        "target_id",
    ],
    "family_cell_summary.jsonl": ["family", "layer"],
    "transfer_cell_summary.jsonl": ["source_family", "prototype_family", "layer"],
}

FAMILY_ORDER = ("sky", "food", "animals", "transport", "social")
ROLE_SPECS: dict[str, dict[str, Any]] = {
    "sky": {
        "config": Path("configs/e1_sky_moon_mlx.yaml"),
        "config_sha256": "b2bfe45d102d4a2d6231a27aadc70bbdddbb7aa6f7e460d6189c91e029071dde",
        "panel": Path("data/emoji_panels/e1_sky_moon.yaml"),
        "panel_sha256": "811b0850574004bd56c9eb6419e814b273d02d13a97b815938095f66f3c1e1e1",
        "run_name": "e1-sky-token-isomorphic-exploratory-mlx",
        "middle_token": 234,
        "codepoint_start": 0x1F311,
    },
    "food": {
        "config": Path("configs/e1_food_mlx.yaml"),
        "config_sha256": "83c6da6f64342f5fb7594f4a4e040c93d0f1007cedd33c139165f91663f31c5e",
        "panel": Path("data/emoji_panels/e1_food.yaml"),
        "panel_sha256": "6fb16ccf141b2dabb33dfe9d20913568d2a294285c9bc7f8f8063c197280e7a3",
        "run_name": "e1-food-token-isomorphic-exploratory-mlx",
        "middle_token": 235,
        "codepoint_start": 0x1F351,
    },
    "animals": {
        "config": Path("configs/e1_animals_mlx.yaml"),
        "config_sha256": "7bbbc5e111a553a96af247b54ac8aab39c5a82d90de93c49d2fa3e90c9999665",
        "panel": Path("data/emoji_panels/e1_animals.yaml"),
        "panel_sha256": "2455d8de88af37fed0925c4df93f3914fba6abb275a05907198baaca2a7954b5",
        "run_name": "e1-animals-token-isomorphic-exploratory-mlx",
        "middle_token": 238,
        "codepoint_start": 0x1F411,
    },
    "transport": {
        "config": Path("configs/e1_transport_mlx.yaml"),
        "config_sha256": "5b279cd1f8351dcb14d9a8f78eecf9c69d5ed9fd0961cf82bc6e2e9f550f04c8",
        "panel": Path("data/emoji_panels/e1_transport.yaml"),
        "panel_sha256": "784dbba21328757db97a8ff65e310cf15707b178d37b11fce033e47832c5d67f",
        "run_name": "e1-transport-token-isomorphic-exploratory-mlx",
        "middle_token": 248,
        "codepoint_start": 0x1F691,
    },
    "social": {
        "config": Path("configs/e1_social_mlx.yaml"),
        "config_sha256": "5559856737531767b4e25c322320712ee0a34b329414d4fefe2b9573aa17203c",
        "panel": Path("data/emoji_panels/e1_social.yaml"),
        "panel_sha256": "b43ba3290c499c248c2bc034af0d3454463fcf5e5d4d64e5fab4fd62ee5cf1a6",
        "run_name": "e1-social-token-isomorphic-exploratory-mlx",
        "middle_token": 97,
        "codepoint_start": 0x1F911,
    },
}


class ExploratoryAnalysisError(ValueError):
    """Raised when an E1 input or analysis invariant fails."""


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, option=option)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value, pretty=True) + b"\n")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    _atomic_write(path, b"".join(_json_bytes(dict(row)) + b"\n" for row in rows))


def _read_json_object(path: Path, description: str) -> dict[str, Any]:
    if not path.is_file():
        raise ExploratoryAnalysisError(f"Missing {description}: {path}")
    try:
        value = orjson.loads(path.read_bytes())
    except orjson.JSONDecodeError as exc:
        raise ExploratoryAnalysisError(f"Invalid JSON in {description}: {path}") from exc
    if not isinstance(value, dict):
        raise ExploratoryAnalysisError(f"Expected a JSON object in {description}: {path}")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ExploratoryAnalysisError(f"Missing {description}: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise ExploratoryAnalysisError(
                    f"Invalid JSONL at {path}:{line_number}"
                ) from exc
            if not isinstance(row, dict):
                raise ExploratoryAnalysisError(f"Expected object at {path}:{line_number}")
            rows.append(row)
    if not rows:
        raise ExploratoryAnalysisError(f"Empty {description}: {path}")
    return rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _verified_repo_file(root: Path, relative: Path, expected_sha256: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_file():
        raise ExploratoryAnalysisError(f"Missing fixed input: {relative}")
    observed = _sha256_file(path)
    if observed != expected_sha256:
        raise ExploratoryAnalysisError(
            f"Fixed input SHA-256 mismatch for {relative}: "
            f"expected {expected_sha256}, observed {observed}"
        )
    return path


def _load_fixed_authority(root: Path) -> dict[str, Any]:
    manifest_path = root / MANIFEST_PATH
    manifest = _read_json_object(manifest_path, "fixed E1 manifest")
    if manifest.get("schema_version") != 1:
        raise ExploratoryAnalysisError("Unsupported E1 manifest schema")
    if manifest.get("protocol_id") != ANALYSIS_ID:
        raise ExploratoryAnalysisError("E1 manifest protocol ID differs")
    fixed_analysis = manifest.get("fixed_analysis")
    if not isinstance(fixed_analysis, dict):
        raise ExploratoryAnalysisError("E1 manifest has no fixed analysis block")
    expected_analysis = {
        "analysis_id": ANALYSIS_ID,
        "script_path": Path(__file__).resolve().relative_to(root).as_posix(),
        "primary_layer": PRIMARY_LAYER,
        "secondary_layer": NEGATIVE_COMPARATOR_LAYER,
        "bootstrap_resamples": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "rebuild_loto_prototypes_inside_each_replicate": True,
        "direction_seeds_nested_within_target": True,
        "p_values": False,
        "multiplicity_decisions": False,
    }
    for field, wanted in expected_analysis.items():
        if fixed_analysis.get(field) != wanted:
            raise ExploratoryAnalysisError(
                f"E1 manifest analysis mismatch at {field}: "
                f"expected {wanted!r}, observed {fixed_analysis.get(field)!r}"
            )
    if fixed_analysis.get("script_sha256") != _sha256_file(Path(__file__).resolve()):
        raise ExploratoryAnalysisError("E1 manifest analysis implementation SHA-256 differs")
    if fixed_analysis.get("output_filenames") != list(OUTPUT_FILENAMES):
        raise ExploratoryAnalysisError("E1 manifest output filenames differ")
    if fixed_analysis.get("expected_output_rows") != EXPECTED_OUTPUT_ROWS:
        raise ExploratoryAnalysisError("E1 manifest output row counts differ")
    if fixed_analysis.get("output_unique_keys") != OUTPUT_UNIQUE_KEYS:
        raise ExploratoryAnalysisError("E1 manifest output unique keys differ")
    endpoints = fixed_analysis.get("endpoints")
    if not isinstance(endpoints, dict) or {
        endpoints.get("M", {}).get("within_family_id"),
        endpoints.get("M", {}).get("ordered_cross_family_id"),
        endpoints.get("R", {}).get("id"),
        endpoints.get("R_global", {}).get("id"),
    } != {ENDPOINT_WITHIN, ENDPOINT_TRANSFER, ENDPOINT_SPECIFICITY, ENDPOINT_GLOBAL}:
        raise ExploratoryAnalysisError("E1 manifest endpoint IDs differ")

    expected_execution_cell = {
        "mode": "internal",
        "backend": {
            "kind": BACKEND,
            "model": MODEL,
            "revision": REVISION,
            "device": "gpu",
            "dtype": DTYPE,
            "local_files_only": True,
            "add_special_tokens": False,
            "trust_remote_code": False,
        },
        "run": {
            "seeds": list(DIRECTION_SEEDS),
            "resume": True,
            "fail_fast": True,
            "replicate_mode": "wrapper_subsample",
            "wrapper_subsample_fraction": 0.75,
        },
        "panel": {"neutral_glyph": "🟰", "centroid_mode": "panel"},
        "source": {"max_wrappers": 16, "anchor_position": "last_nonpad"},
        "targets": {"max_cases": 24, "calibration_cases": 6},
        "capture": {
            "site": SITE,
            "layers": list(LAYERS),
            "position": "last_nonpad",
            "return_attentions": False,
        },
        "intervention": {
            "mode": "activation_add",
            "normalization": "rms",
            "strengths": [STRENGTH],
            "position": "last_nonpad",
            "clip": {"mode": "global_rms", "max_ratio": 0.25},
            "iso_kl_enabled": False,
        },
        "controls": {
            "random_directions_per_layer": 2,
            "zero_direction": True,
            "sign_flip": False,
            "sign_flip_strengths": [],
            "label_shuffle_permutations": 0,
            "include_neutral_direction": False,
        },
        "metrics": {
            "top_k": 50,
            "fingerprint_dim": FINGERPRINT_DIM,
            "fingerprint_seed": FINGERPRINT_SEED,
            "split_half_repeats": 200,
            "rbo_p": 0.9,
            "save_top_logit_deltas": 32,
            "save_fingerprints": True,
            "epsilon": EPSILON,
        },
        "sae_enabled": False,
        "surface": {
            "emoji_template": "{emoji}\n{prompt}",
            "neutral_template": "{prompt}",
            "system_prompt": None,
        },
        "fixed_family_layer_strength_seed_cell_count": 30,
        "expected_forward_calls_per_family": {
            "source": 176,
            "target_baseline": 24,
            "emoji_intervention": EXPECTED_POSITIVE_ROWS_PER_RUN,
            "random_control": EXPECTED_RANDOM_ROWS_PER_RUN,
            "generic_emoji_control": 0,
            "zero_hook_control": EXPECTED_ZERO_ROWS_PER_RUN,
            "total": 1976,
            "intervention_rows": EXPECTED_INTERVENTION_ROWS_PER_RUN,
        },
        "expected_forward_calls_all_families": 9880,
        "expected_intervention_rows_all_families": 8880,
    }
    if manifest.get("fixed_execution_cell") != expected_execution_cell:
        raise ExploratoryAnalysisError("E1 manifest fixed execution cell differs")

    parity_path = _verified_repo_file(root, PARITY_PATH, PARITY_SHA256)
    target_path = _verified_repo_file(root, TARGET_PATH, TARGET_SHA256)
    source_path = _verified_repo_file(root, SOURCE_PATH, SOURCE_SHA256)

    shared_inputs = manifest.get("shared_inputs")
    target_spec = shared_inputs.get("target") if isinstance(shared_inputs, dict) else None
    source_spec = shared_inputs.get("source") if isinstance(shared_inputs, dict) else None
    if not isinstance(target_spec, dict) or not isinstance(source_spec, dict):
        raise ExploratoryAnalysisError("E1 manifest shared input bindings are incomplete")
    all_target_rows = _read_jsonl(target_path, "fixed prestage targets")
    if len(all_target_rows) != target_spec.get("file_record_count"):
        raise ExploratoryAnalysisError("Prestage target file row count differs from manifest")
    selected_count = target_spec.get("selected_record_count")
    if selected_count != len(TARGET_GROUPS) * TARGETS_PER_GROUP:
        raise ExploratoryAnalysisError("E1 manifest must select exactly 24 targets")

    targets: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for row in all_target_rows[:selected_count]:
        target_id = row.get("id")
        group = row.get("group")
        if not isinstance(target_id, str) or not target_id or target_id in seen_targets:
            raise ExploratoryAnalysisError("Fixed prestage target IDs are invalid")
        if group not in TARGET_GROUPS:
            raise ExploratoryAnalysisError(f"Unexpected prestage target group: {group!r}")
        seen_targets.add(target_id)
        targets.append({"id": target_id, "group": group})
    if len(targets) != len(TARGET_GROUPS) * TARGETS_PER_GROUP:
        raise ExploratoryAnalysisError("Fixed prestage target bank must contain 24 rows")
    group_counts = defaultdict(int)
    for row in targets:
        group_counts[row["group"]] += 1
    if dict(group_counts) != {group: TARGETS_PER_GROUP for group in TARGET_GROUPS}:
        raise ExploratoryAnalysisError("Fixed prestage target groups are not six by four")
    if [row["id"] for row in targets] != target_spec.get("ordered_selected_ids"):
        raise ExploratoryAnalysisError("Selected target ID order differs from E1 manifest")
    if [row["group"] for row in targets] != target_spec.get("ordered_selected_groups"):
        raise ExploratoryAnalysisError("Selected target group order differs from E1 manifest")

    wrappers: list[str] = []
    for row in _read_jsonl(source_path, "fixed source wrappers"):
        wrapper_id = row.get("id")
        template = row.get("template")
        if not isinstance(wrapper_id, str) or not wrapper_id or wrapper_id in wrappers:
            raise ExploratoryAnalysisError("Fixed source wrapper IDs are invalid")
        if not isinstance(template, str) or template.count("{emoji}") != 1:
            raise ExploratoryAnalysisError(f"Invalid source wrapper: {wrapper_id}")
        wrappers.append(wrapper_id)
    if len(wrappers) != 16:
        raise ExploratoryAnalysisError("Fixed source wrapper bank must contain 16 rows")
    if len(wrappers) != source_spec.get("selected_record_count"):
        raise ExploratoryAnalysisError("Selected source wrapper count differs from manifest")
    if wrappers != source_spec.get("ordered_ids"):
        raise ExploratoryAnalysisError("Source wrapper ID order differs from E1 manifest")

    manifest_panels = manifest.get("panels")
    if not isinstance(manifest_panels, list):
        raise ExploratoryAnalysisError("E1 manifest panel bindings are missing")
    panels_by_role = {
        row.get("role"): row for row in manifest_panels if isinstance(row, dict)
    }
    if set(panels_by_role) != set(FAMILY_ORDER):
        raise ExploratoryAnalysisError("E1 manifest family roles differ")

    roles: dict[str, dict[str, Any]] = {}
    expected_suffixes: tuple[int, ...] | None = None
    for role in FAMILY_ORDER:
        spec = ROLE_SPECS[role]
        manifest_panel = panels_by_role[role]
        expected_manifest_panel = {
            "path": spec["panel"].as_posix(),
            "sha256": spec["panel_sha256"],
            "config_path": spec["config"].as_posix(),
            "config_sha256": spec["config_sha256"],
            "run_name": spec["run_name"],
            "factor_family": role,
            "family_middle_token_id": spec["middle_token"],
        }
        for field, wanted in expected_manifest_panel.items():
            if manifest_panel.get(field) != wanted:
                raise ExploratoryAnalysisError(
                    f"E1 manifest {role} binding mismatch at {field}"
                )
        config_path = _verified_repo_file(root, spec["config"], spec["config_sha256"])
        panel_path = _verified_repo_file(root, spec["panel"], spec["panel_sha256"])
        panel_document = yaml.safe_load(panel_path.read_text(encoding="utf-8"))
        items = panel_document.get("items") if isinstance(panel_document, dict) else None
        if not isinstance(items, list) or len(items) != CONDITIONS_PER_FAMILY:
            raise ExploratoryAnalysisError(f"Fixed panel {role} must contain ten items")
        expected_ids = tuple(f"{role}_slot_{index:02d}" for index in range(10))
        observed_ids = tuple(item.get("id") for item in items if isinstance(item, dict))
        if observed_ids != expected_ids:
            raise ExploratoryAnalysisError(f"Fixed panel {role} IDs/order differ")
        glyphs: list[str] = []
        suffixes: list[int] = []
        for index, item in enumerate(items):
            glyph = item.get("glyph")
            factors = item.get("factors")
            codepoint = int(spec["codepoint_start"]) + index
            if not isinstance(glyph, str) or len(glyph) != 1 or ord(glyph) != codepoint:
                raise ExploratoryAnalysisError(f"Fixed panel {role} codepoint grid differs")
            if not isinstance(factors, dict) or factors != {
                "family": role,
                "matched_slot": f"slot_{index:02d}",
                "codepoint": f"U+{codepoint:04X}",
            }:
                raise ExploratoryAnalysisError(f"Fixed panel {role} factors differ")
            glyphs.append(glyph)
            # The pinned byte-level GPT-2 lattice maps these consecutive code
            # points to a shared first token, one role middle, and suffix 239..248.
            suffixes.append(239 + index)
        suffix_tuple = tuple(suffixes)
        if expected_suffixes is None:
            expected_suffixes = suffix_tuple
        elif suffix_tuple != expected_suffixes:
            raise ExploratoryAnalysisError("Fixed matched-slot suffix grid differs by role")
        roles[role] = {
            **spec,
            "config_path": config_path,
            "panel_path": panel_path,
            "panel_items": items,
            "condition_ids": expected_ids,
            "glyphs": tuple(glyphs),
            "suffix_tokens": suffix_tuple,
        }
    return {
        "root": root,
        "manifest_path": manifest_path,
        "manifest_sha256": _sha256_file(manifest_path),
        "parity_path": parity_path,
        "target_path": target_path,
        "source_path": source_path,
        "targets": targets,
        "target_ids": tuple(row["id"] for row in targets),
        "target_groups": {row["id"]: row["group"] for row in targets},
        "wrapper_ids": tuple(wrappers),
        "roles": roles,
    }


def _nested(mapping: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = mapping
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            raise ExploratoryAnalysisError(f"Resolved config is missing {'.'.join(path)}")
        current = current[part]
    return current


def _validate_resolved_config(config: Mapping[str, Any], role: str) -> None:
    spec = ROLE_SPECS[role]
    expected: dict[tuple[str, ...], Any] = {
        ("schema_version",): 1,
        ("mode",): "internal",
        ("backend", "kind"): BACKEND,
        ("backend", "model"): MODEL,
        ("backend", "revision"): REVISION,
        ("backend", "device"): "gpu",
        ("backend", "dtype"): DTYPE,
        ("backend", "local_files_only"): True,
        ("backend", "add_special_tokens"): False,
        ("backend", "trust_remote_code"): False,
        ("backend", "validation_receipt_sha256"): PARITY_SHA256,
        ("run", "name"): spec["run_name"],
        ("run", "seeds"): list(DIRECTION_SEEDS),
        ("run", "resume"): True,
        ("run", "fail_fast"): True,
        ("run", "replicate_mode"): "wrapper_subsample",
        ("run", "wrapper_subsample_fraction"): 0.75,
        ("panel", "neutral_glyph"): "🟰",
        ("panel", "centroid_mode"): "panel",
        ("source", "max_wrappers"): 16,
        ("source", "anchor_position"): "last_nonpad",
        ("targets", "max_cases"): 24,
        ("targets", "calibration_cases"): 6,
        ("capture", "site"): SITE,
        ("capture", "layers"): list(LAYERS),
        ("capture", "position"): "last_nonpad",
        ("capture", "return_attentions"): False,
        ("intervention", "mode"): "activation_add",
        ("intervention", "position"): "last_nonpad",
        ("intervention", "normalization"): "rms",
        ("intervention", "strengths"): [STRENGTH],
        ("intervention", "clip", "mode"): "global_rms",
        ("intervention", "clip", "max_ratio"): 0.25,
        ("intervention", "iso_kl", "enabled"): False,
        ("controls", "random_directions_per_layer"): 2,
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
        if observed != wanted or isinstance(wanted, bool) and observed is not wanted:
            raise ExploratoryAnalysisError(
                f"Role {role} config mismatch at {'.'.join(path)}: "
                f"expected {wanted!r}, observed {observed!r}"
            )
    path_checks = {
        ("backend", "validation_receipt"): PARITY_PATH.name,
        ("panel", "file"): spec["panel"].name,
        ("source", "wrappers_file"): SOURCE_PATH.name,
        ("targets", "cases_file"): TARGET_PATH.name,
    }
    for path, basename in path_checks.items():
        observed = Path(str(_nested(config, path))).name
        if observed != basename:
            raise ExploratoryAnalysisError(
                f"Role {role} config path mismatch at {'.'.join(path)}: {observed!r}"
            )


def _finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExploratoryAnalysisError(f"Invalid numeric {field}: {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ExploratoryAnalysisError(f"Non-finite numeric {field}")
    return result


def _fingerprint(row: Mapping[str, Any], *, line_number: int) -> np.ndarray:
    distribution = row.get("distribution")
    value = distribution.get("fingerprint") if isinstance(distribution, Mapping) else None
    vector = np.asarray(value, dtype=np.float64) if value is not None else np.asarray([])
    if vector.ndim != 1 or vector.size != FINGERPRINT_DIM:
        raise ExploratoryAnalysisError(
            f"Row {line_number} fingerprint must have dimension {FINGERPRINT_DIM}"
        )
    if not np.all(np.isfinite(vector)):
        raise ExploratoryAnalysisError(f"Row {line_number} fingerprint is non-finite")
    norm = float(np.linalg.norm(vector))
    if norm <= EPSILON:
        raise ExploratoryAnalysisError(f"Row {line_number} fingerprint has zero norm")
    return vector / norm


def _eligible_positive_emoji(row: Mapping[str, Any]) -> bool:
    sign = row.get("sign")
    return (
        not isinstance(sign, bool)
        and sign == 1
        and row.get("calibration") == "rms"
        and row.get("condition_type") == "emoji"
    )


def _validate_summary(run_dir: Path, role: str) -> tuple[dict[str, Any], Path]:
    path = run_dir / "summary.json"
    summary = _read_json_object(path, f"{role} run summary")
    exact_counts = {
        "error_count": 0,
        "intervention_record_count": EXPECTED_INTERVENTION_ROWS_PER_RUN,
        "random_control_count": EXPECTED_RANDOM_ROWS_PER_RUN,
        "zero_hook_control_count": EXPECTED_ZERO_ROWS_PER_RUN,
        "emoji_count": CONDITIONS_PER_FAMILY,
        "target_case_count": 24,
        "seed_count": 3,
        "strength_count": 1,
        "resolved_layers": list(LAYERS),
    }
    for field, wanted in exact_counts.items():
        if summary.get(field) != wanted:
            raise ExploratoryAnalysisError(
                f"Role {role} summary mismatch at {field}: "
                f"expected {wanted!r}, observed {summary.get(field)!r}"
            )
    for field in ("zero_hook_max_activation_delta_rms", "zero_hook_max_logit_delta_rms"):
        value = _finite(summary.get(field), field=f"summary.{field}")
        if value > 1e-6:
            raise ExploratoryAnalysisError(f"Role {role} zero-hook error exceeds 1e-6")
    return summary, path


def _load_fingerprint_screening(
    run_dir: Path, role: str
) -> tuple[dict[tuple[int, int], dict[str, Any]], Path]:
    path = run_dir / "fingerprint_summary.jsonl"
    rows = _read_jsonl(path, f"{role} fingerprint summary")
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    required_numbers = (
        "emoji_same_split_cosine",
        "emoji_cross_cosine",
        "emoji_separation",
        "emoji_split_repeat_mean",
        "emoji_split_repeat_median",
        "emoji_split_repeat_ci_low",
        "emoji_split_repeat_ci_high",
        "random_same_split_cosine",
        "random_cross_cosine",
        "random_separation",
        "random_split_repeat_mean",
        "random_split_repeat_ci_low",
        "random_split_repeat_ci_high",
        "emoji_advantage_over_random",
    )
    for row in rows:
        layer = int(_finite(row.get("layer"), field="fingerprint_summary.layer"))
        seed = int(_finite(row.get("seed"), field="fingerprint_summary.seed"))
        strength = _finite(row.get("strength"), field="fingerprint_summary.strength")
        if layer not in LAYERS or seed not in DIRECTION_SEEDS or strength != STRENGTH:
            raise ExploratoryAnalysisError(f"Role {role} fingerprint summary has extra cell")
        key = (layer, seed)
        if key in cells:
            raise ExploratoryAnalysisError(f"Role {role} fingerprint summary duplicates {key}")
        values = {field: _finite(row.get(field), field=field) for field in required_numbers}
        split_seed = int(_finite(row.get("split_seed"), field="split_seed"))
        if row.get("emoji_condition_count") != CONDITIONS_PER_FAMILY:
            raise ExploratoryAnalysisError(f"Role {role} screening condition count differs")
        if row.get("emoji_target_count") != 24 or row.get("random_target_count") != 24:
            raise ExploratoryAnalysisError(f"Role {role} screening target count differs")
        if row.get("random_condition_count") != 2:
            raise ExploratoryAnalysisError(f"Role {role} random condition count differs")
        if row.get("emoji_split_repeat_count") != 200:
            raise ExploratoryAnalysisError(f"Role {role} split repeat count differs")
        if row.get("emoji_label_permutation_count") != 0:
            raise ExploratoryAnalysisError(f"Role {role} permutation count is not zero")
        for forbidden_field in (
            "emoji_label_permutation_p",
            "emoji_label_permutation_null_mean",
            "emoji_label_permutation_null_std",
        ):
            if row.get(forbidden_field) is not None:
                raise ExploratoryAnalysisError(
                    f"Role {role} generated a forbidden permutation statistic"
                )
        cells[key] = {
            "split_seed": split_seed,
            **values,
            "emoji_condition_count": CONDITIONS_PER_FAMILY,
            "emoji_target_count": 24,
            "emoji_split_repeat_count": 200,
            "random_condition_count": 2,
            "random_target_count": 24,
        }
    expected = {(layer, seed) for layer in LAYERS for seed in DIRECTION_SEEDS}
    if set(cells) != expected:
        raise ExploratoryAnalysisError(f"Role {role} fingerprint summary grid is incomplete")
    return cells, path


def _load_run(run_dir: Path, role: str, authority: Mapping[str, Any]) -> dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    spec = authority["roles"][role]
    config_path = run_dir / "resolved_config.yaml"
    if not config_path.is_file():
        raise ExploratoryAnalysisError(f"Missing resolved config: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ExploratoryAnalysisError(f"Resolved config is not a mapping: {config_path}")
    _validate_resolved_config(config, role)

    receipt_path = run_dir / "receipt.json"
    receipt = _read_json_object(receipt_path, f"{role} run receipt")
    if receipt.get("status") != "complete":
        raise ExploratoryAnalysisError(f"Role {role} run receipt is not complete")
    expected_hashes = {
        f"input_00:{spec['config'].name}": spec["config_sha256"],
        f"input_01:{PARITY_PATH.name}": PARITY_SHA256,
        f"input_02:{spec['panel'].name}": spec["panel_sha256"],
        f"input_03:{SOURCE_PATH.name}": SOURCE_SHA256,
        f"input_04:{TARGET_PATH.name}": TARGET_SHA256,
    }
    if receipt.get("input_hashes") != expected_hashes:
        raise ExploratoryAnalysisError(f"Role {role} receipt input hashes do not match role")

    resolved_inputs_path = run_dir / "resolved_inputs.json"
    resolved_inputs = _read_json_object(resolved_inputs_path, f"{role} resolved inputs")
    if resolved_inputs.get("panel") != spec["panel_items"]:
        raise ExploratoryAnalysisError(f"Role {role} resolved panel does not match fixed panel")
    if resolved_inputs.get("target_ids") != list(authority["target_ids"]):
        raise ExploratoryAnalysisError(f"Role {role} resolved target IDs differ")
    if resolved_inputs.get("wrapper_ids") != list(authority["wrapper_ids"]):
        raise ExploratoryAnalysisError(f"Role {role} resolved wrapper IDs differ")

    summary, summary_path = _validate_summary(run_dir, role)
    screening, screening_path = _load_fingerprint_screening(run_dir, role)

    ledger_path = run_dir / "interventions.jsonl"
    rows = _read_jsonl(ledger_path, f"{role} intervention ledger")
    if len(rows) != EXPECTED_INTERVENTION_ROWS_PER_RUN:
        raise ExploratoryAnalysisError(
            f"Role {role} intervention ledger row count differs: "
            f"expected {EXPECTED_INTERVENTION_ROWS_PER_RUN}, observed {len(rows)}"
        )
    condition_counts = Counter(row.get("condition_type") for row in rows)
    expected_condition_counts = {
        "emoji": EXPECTED_POSITIVE_ROWS_PER_RUN,
        "random": EXPECTED_RANDOM_ROWS_PER_RUN,
        "zero": EXPECTED_ZERO_ROWS_PER_RUN,
    }
    if dict(condition_counts) != expected_condition_counts:
        raise ExploratoryAnalysisError(
            f"Role {role} ledger condition rows differ: "
            f"expected {expected_condition_counts}, observed {dict(condition_counts)}"
        )

    random_cell_counts: Counter[tuple[int, int]] = Counter()
    random_cell_targets: dict[tuple[int, int, str], set[str]] = defaultdict(set)
    zero_by_layer: dict[int, dict[str, Any]] = {}
    for row in rows:
        condition_type = row.get("condition_type")
        if condition_type == "random":
            layer = int(_finite(row.get("layer"), field="random.layer"))
            seed = int(_finite(row.get("seed"), field="random.seed"))
            strength = _finite(row.get("strength"), field="random.strength")
            condition_id = row.get("condition_id")
            target_id = row.get("target_id")
            if (
                layer not in LAYERS
                or seed not in DIRECTION_SEEDS
                or strength != STRENGTH
                or row.get("sign") != 1
                or row.get("calibration") != "rms"
                or condition_id not in {"random_00", "random_01"}
                or target_id not in authority["target_ids"]
                or row.get("target_group") != authority["target_groups"][target_id]
            ):
                raise ExploratoryAnalysisError(f"Role {role} has invalid random control row")
            random_cell_counts[(layer, seed)] += 1
            random_cell_targets[(layer, seed, condition_id)].add(str(target_id))
        elif condition_type == "zero":
            layer = int(_finite(row.get("layer"), field="zero.layer"))
            target_id = row.get("target_id")
            if (
                layer not in LAYERS
                or row.get("seed") != DIRECTION_SEEDS[0]
                or _finite(row.get("strength"), field="zero.strength") != 0.0
                or row.get("sign") != 0
                or row.get("calibration") != "zero_hook"
                or row.get("condition_id") != "__zero_hook__"
                or target_id not in authority["target_ids"]
                or row.get("target_group") != authority["target_groups"][target_id]
            ):
                raise ExploratoryAnalysisError(f"Role {role} has invalid zero-hook row")
            distribution = row.get("distribution")
            activation = row.get("activation")
            if not isinstance(distribution, Mapping) or not isinstance(activation, Mapping):
                raise ExploratoryAnalysisError(f"Role {role} zero-hook metrics are missing")
            logit_error = _finite(
                distribution.get("logit_delta_rms"), field="zero.logit_delta_rms"
            )
            activation_error = _finite(
                activation.get("actual_activation_delta_rms"),
                field="zero.actual_activation_delta_rms",
            )
            cell = zero_by_layer.setdefault(
                layer,
                {
                    "target_ids": set(),
                    "logit_errors": [],
                    "activation_errors": [],
                },
            )
            if target_id in cell["target_ids"]:
                raise ExploratoryAnalysisError(
                    f"Role {role} duplicates zero-hook target {target_id} at layer {layer}"
                )
            cell["target_ids"].add(target_id)
            cell["logit_errors"].append(logit_error)
            cell["activation_errors"].append(activation_error)

    expected_random_cells = {
        (layer, seed): 2 * len(authority["target_ids"])
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
    }
    if dict(random_cell_counts) != expected_random_cells:
        raise ExploratoryAnalysisError(f"Role {role} random-control grid is incomplete")
    expected_target_set = set(authority["target_ids"])
    if any(targets != expected_target_set for targets in random_cell_targets.values()):
        raise ExploratoryAnalysisError(f"Role {role} random-control targets are incomplete")
    if set(random_cell_targets) != {
        (layer, seed, condition_id)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_id in ("random_00", "random_01")
    }:
        raise ExploratoryAnalysisError(f"Role {role} random-control conditions differ")
    if set(zero_by_layer) != set(LAYERS):
        raise ExploratoryAnalysisError(f"Role {role} zero-hook layer grid is incomplete")
    zero_summary_by_layer: dict[int, dict[str, Any]] = {}
    for layer in LAYERS:
        cell = zero_by_layer[layer]
        if cell["target_ids"] != expected_target_set:
            raise ExploratoryAnalysisError(f"Role {role} zero-hook targets are incomplete")
        max_logit = max(cell["logit_errors"])
        max_activation = max(cell["activation_errors"])
        if max_logit > 1e-6 or max_activation > 1e-6:
            raise ExploratoryAnalysisError(f"Role {role} zero-hook error exceeds 1e-6")
        zero_summary_by_layer[layer] = {
            "row_count": len(cell["target_ids"]),
            "max_logit_delta_rms": max_logit,
            "max_activation_delta_rms": max_activation,
        }

    vectors: dict[tuple[int, int, str, str], np.ndarray] = {}
    target_groups: dict[str, str] = {}
    condition_to_glyph = dict(zip(spec["condition_ids"], spec["glyphs"]))
    for line_number, row in enumerate(rows, 1):
        if not _eligible_positive_emoji(row):
            continue
        required = ("layer", "strength", "seed", "condition_id", "target_id", "target_group")
        if any(field not in row for field in required):
            raise ExploratoryAnalysisError(f"Eligible row {line_number} is incomplete")
        layer = int(_finite(row["layer"], field="ledger.layer"))
        strength = _finite(row["strength"], field="ledger.strength")
        seed = int(_finite(row["seed"], field="ledger.seed"))
        condition_id = str(row["condition_id"])
        target_id = str(row["target_id"])
        target_group = str(row["target_group"])
        if layer not in LAYERS or strength != STRENGTH or seed not in DIRECTION_SEEDS:
            raise ExploratoryAnalysisError(f"Role {role} has an extra eligible cell")
        if condition_id not in condition_to_glyph:
            raise ExploratoryAnalysisError(f"Role {role} has unexpected condition {condition_id}")
        if row.get("glyph") != condition_to_glyph[condition_id]:
            raise ExploratoryAnalysisError(f"Role {role} ledger glyph/condition mismatch")
        expected_group = authority["target_groups"].get(target_id)
        if expected_group is None or target_group != expected_group:
            raise ExploratoryAnalysisError(f"Role {role} ledger target/group mismatch")
        if target_id in target_groups and target_groups[target_id] != target_group:
            raise ExploratoryAnalysisError(f"Role {role} target group is inconsistent")
        target_groups[target_id] = target_group
        key = (layer, seed, condition_id, target_id)
        if key in vectors:
            raise ExploratoryAnalysisError(f"Role {role} duplicate eligible row: {key}")
        vectors[key] = _fingerprint(row, line_number=line_number)

    expected_keys = {
        (layer, seed, condition_id, target_id)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_id in spec["condition_ids"]
        for target_id in authority["target_ids"]
    }
    if set(vectors) != expected_keys or len(vectors) != EXPECTED_POSITIVE_ROWS_PER_RUN:
        raise ExploratoryAnalysisError(
            f"Role {role} positive emoji grid incomplete: "
            f"expected {len(expected_keys)}, observed {len(vectors)}"
        )
    return {
        "role": role,
        "run_dir": run_dir,
        "config_path": config_path,
        "receipt_path": receipt_path,
        "resolved_inputs_path": resolved_inputs_path,
        "summary_path": summary_path,
        "screening_path": screening_path,
        "ledger_path": ledger_path,
        "vectors": vectors,
        "screening": screening,
        "summary": summary,
        "condition_ids": spec["condition_ids"],
        "eligible_row_count": len(vectors),
        "ledger_row_count": len(rows),
        "condition_counts": expected_condition_counts,
        "random_cell_counts": dict(random_cell_counts),
        "zero_summary_by_layer": zero_summary_by_layer,
    }


def _group_indices(
    target_ids: Sequence[str], target_groups: Mapping[str, str]
) -> tuple[tuple[int, ...], ...]:
    result: list[tuple[int, ...]] = []
    for group in TARGET_GROUPS:
        indices = tuple(
            index for index, target_id in enumerate(target_ids)
            if target_groups[target_id] == group
        )
        if len(indices) != TARGETS_PER_GROUP:
            raise ExploratoryAnalysisError(f"Target group {group} is not size four")
        result.append(indices)
    return tuple(result)


def _tensor(runs: Sequence[Mapping[str, Any]], target_ids: Sequence[str]) -> np.ndarray:
    tensor = np.empty(
        (
            len(FAMILY_ORDER), len(LAYERS), len(DIRECTION_SEEDS),
            CONDITIONS_PER_FAMILY, len(target_ids), FINGERPRINT_DIM,
        ),
        dtype=np.float64,
    )
    for family_index, run in enumerate(runs):
        for layer_index, layer in enumerate(LAYERS):
            for seed_index, seed in enumerate(DIRECTION_SEEDS):
                for slot_index, condition_id in enumerate(run["condition_ids"]):
                    for target_index, target_id in enumerate(target_ids):
                        tensor[family_index, layer_index, seed_index, slot_index, target_index] = (
                            run["vectors"][(layer, seed, condition_id, target_id)]
                        )
    return tensor


def _bootstrap_weights(
    replicates: int, seed: int, target_count: int,
    group_indices: Sequence[Sequence[int]],
) -> tuple[np.ndarray, np.ndarray]:
    if replicates <= 0:
        raise ExploratoryAnalysisError("Bootstrap replicate count must be positive")
    rng = np.random.default_rng(int(seed))
    weights = np.zeros((replicates, target_count), dtype=np.int16)
    draws_by_group: list[np.ndarray] = []
    rows = np.arange(replicates, dtype=np.int64)
    for raw_indices in group_indices:
        indices = np.asarray(raw_indices, dtype=np.int64)
        local = rng.integers(0, indices.size, size=(replicates, indices.size))
        draws = indices[local]
        draws_by_group.append(draws)
        for column in range(indices.size):
            np.add.at(weights, (rows, draws[:, column]), 1)
    draws = np.concatenate(draws_by_group, axis=1)
    if not np.all(weights.sum(axis=1) == target_count):
        raise ExploratoryAnalysisError("Bootstrap target multiplicities are invalid")
    return weights, draws


def _score_layer_chunk_by_seed(
    layer_vectors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> np.ndarray:
    """Return [replicate, source family, prototype family, seed, target]."""

    if layer_vectors.shape[:3] != (
        len(FAMILY_ORDER), len(DIRECTION_SEEDS), CONDITIONS_PER_FAMILY
    ):
        raise ExploratoryAnalysisError("Layer tensor has an invalid family/seed/slot grid")
    family_count, seed_count, slot_count, target_count, _ = layer_vectors.shape
    if weights.ndim != 2 or weights.shape[1] != target_count:
        raise ExploratoryAnalysisError("Bootstrap weights do not match target tensor")
    floating_weights = weights.astype(np.float64, copy=False)
    scores = np.empty(
        (weights.shape[0], family_count, family_count, seed_count, target_count),
        dtype=np.float64,
    )
    total_sums = np.einsum(
        "bt,fsctd->bfscd", floating_weights, layer_vectors, optimize=True
    )
    for raw_indices in group_indices:
        held = np.asarray(raw_indices, dtype=np.int64)
        held_vectors = layer_vectors[:, :, :, held, :]
        held_sums = np.einsum(
            "bh,fschd->bfscd",
            floating_weights[:, held],
            held_vectors,
            optimize=True,
        )
        training_sums = total_sums - held_sums
        norms = np.linalg.norm(training_sums, axis=-1, keepdims=True)
        if np.any(norms <= EPSILON) or not np.all(np.isfinite(norms)):
            raise ExploratoryAnalysisError(
                "A resampled leave-one-group-out prototype has zero/non-finite norm"
            )
        prototypes = training_sums / norms
        same_sum = np.einsum(
            "bqscd,aschd->baqsh", prototypes, held_vectors, optimize=True
        )
        all_sum = np.einsum(
            "bqsd,ashd->baqsh",
            prototypes.sum(axis=3),
            held_vectors.sum(axis=2),
            optimize=True,
        )
        held_scores = (slot_count * same_sum - all_sum) / (
            slot_count * (slot_count - 1)
        )
        scores[:, :, :, :, held] = held_scores
    if not np.all(np.isfinite(scores)):
        raise ExploratoryAnalysisError("Endpoint scores contain non-finite values")
    return scores


def _weighted_median(values: np.ndarray, draws: np.ndarray) -> np.ndarray:
    """Median sampled target values; values [B,...,T], draws [B,T]."""

    gather = draws.reshape(
        (draws.shape[0],) + (1,) * (values.ndim - 2) + (draws.shape[1],)
    )
    gather = np.broadcast_to(gather, values.shape[:-1] + (draws.shape[1],))
    sampled = np.take_along_axis(values, gather, axis=-1)
    return np.median(sampled, axis=-1)


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Mean sampled target values; values [B,...,T], weights [B,T]."""

    if values.shape[0] != weights.shape[0] or values.shape[-1] != weights.shape[1]:
        raise ExploratoryAnalysisError("Bootstrap values and target weights differ")
    floating = weights.astype(np.float64, copy=False)
    expanded = floating.reshape(
        (floating.shape[0],) + (1,) * (values.ndim - 2) + (floating.shape[1],)
    )
    denominator = floating.sum(axis=1).reshape(
        (floating.shape[0],) + (1,) * (values.ndim - 2)
    )
    return np.sum(values * expanded, axis=-1) / denominator


def _bootstrap_endpoints(
    tensor: np.ndarray,
    weights: np.ndarray,
    draws: np.ndarray,
    group_indices: Sequence[Sequence[int]],
    *,
    chunk_size: int,
) -> dict[str, np.ndarray]:
    layer_count = tensor.shape[1]
    family_count = tensor.shape[0]
    replicates = weights.shape[0]
    if chunk_size <= 0:
        raise ExploratoryAnalysisError("Bootstrap chunk size must be positive")
    matrix_means = np.empty(
        (layer_count, replicates, family_count, family_count), dtype=np.float64
    )
    specificity_means = np.empty(
        (layer_count, replicates, family_count), dtype=np.float64
    )
    global_specificity = np.empty((layer_count, replicates), dtype=np.float64)
    for layer_index in range(layer_count):
        for start in range(0, replicates, chunk_size):
            stop = min(start + chunk_size, replicates)
            seed_scores = _score_layer_chunk_by_seed(
                tensor[:, layer_index], weights[start:stop], group_indices
            )
            target_scores = seed_scores.mean(axis=3)
            matrix_means[layer_index, start:stop] = _weighted_mean(
                target_scores, weights[start:stop]
            )
            diagonal = np.stack(
                [target_scores[:, index, index] for index in range(family_count)],
                axis=1,
            )
            cross_medians = np.stack(
                [
                    np.median(
                        target_scores[:, source][:, np.asarray([
                            destination for destination in range(family_count)
                            if destination != source
                        ]), :],
                        axis=1,
                    )
                    for source in range(family_count)
                ],
                axis=1,
            )
            specificity = diagonal - cross_medians
            chunk_weights = weights[start:stop].astype(np.float64)
            family_means = np.sum(
                specificity * chunk_weights[:, None, :], axis=2
            ) / chunk_weights.sum(axis=1)[:, None]
            specificity_means[layer_index, start:stop] = family_means
            global_specificity[layer_index, start:stop] = family_means.mean(axis=1)
    return {
        "matrix_means": matrix_means,
        "specificity_means": specificity_means,
        "global_specificity": global_specificity,
    }


def _interval(values: np.ndarray) -> dict[str, float]:
    low, high = np.quantile(values, (0.025, 0.975))
    return {"low": float(low), "high": float(high)}


def _input_record(run: Mapping[str, Any]) -> dict[str, Any]:
    role = run["role"]
    spec = ROLE_SPECS[role]
    return {
        "role": role,
        "run_label": run["run_dir"].name,
        "fixed_config_file": spec["config"].as_posix(),
        "fixed_config_sha256": spec["config_sha256"],
        "fixed_panel_file": spec["panel"].as_posix(),
        "fixed_panel_sha256": spec["panel_sha256"],
        "interventions_sha256": _sha256_file(run["ledger_path"]),
        "resolved_config_sha256": _sha256_file(run["config_path"]),
        "run_receipt_sha256": _sha256_file(run["receipt_path"]),
        "resolved_inputs_sha256": _sha256_file(run["resolved_inputs_path"]),
        "summary_sha256": _sha256_file(run["summary_path"]),
        "fingerprint_summary_sha256": _sha256_file(run["screening_path"]),
        "positive_emoji_row_count": run["eligible_row_count"],
        "zero_hook_max_activation_delta_rms": run["summary"][
            "zero_hook_max_activation_delta_rms"
        ],
        "zero_hook_max_logit_delta_rms": run["summary"][
            "zero_hook_max_logit_delta_rms"
        ],
    }


def _layer_role(layer: int) -> str:
    if layer == PRIMARY_LAYER:
        return "primary_exploratory"
    if layer == NEGATIVE_COMPARATOR_LAYER:
        return "prespecified_secondary_negative_comparator"
    raise ExploratoryAnalysisError(f"Unexpected layer: {layer}")


def _observed_endpoints(
    tensor: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> dict[str, np.ndarray]:
    layer_count = tensor.shape[1]
    family_count = tensor.shape[0]
    target_count = tensor.shape[-2]
    seed_scores = np.empty(
        (
            layer_count,
            family_count,
            family_count,
            len(DIRECTION_SEEDS),
            target_count,
        ),
        dtype=np.float64,
    )
    unit_weights = np.ones((1, target_count), dtype=np.int16)
    for layer_index in range(layer_count):
        seed_scores[layer_index] = _score_layer_chunk_by_seed(
            tensor[:, layer_index], unit_weights, group_indices
        )[0]
    target_matrix = seed_scores.mean(axis=3)
    within = np.stack(
        [target_matrix[:, index, index] for index in range(family_count)], axis=1
    )
    cross_median = np.stack(
        [
            np.median(
                target_matrix[:, source][:, np.asarray([
                    destination for destination in range(family_count)
                    if destination != source
                ]), :],
                axis=1,
            )
            for source in range(family_count)
        ],
        axis=1,
    )
    specificity = within - cross_median
    global_specificity = specificity.mean(axis=1)
    return {
        "seed_scores": seed_scores,
        "target_matrix": target_matrix,
        "within": within,
        "cross_median": cross_median,
        "specificity": specificity,
        "global_specificity": global_specificity,
    }


def _target_group_means(
    values: np.ndarray,
    target_ids: Sequence[str],
    target_groups: Mapping[str, str],
) -> dict[str, float]:
    if values.ndim != 1 or values.size != len(target_ids):
        raise ExploratoryAnalysisError("Target-group summary values have invalid shape")
    return {
        group: float(np.mean([
            values[index]
            for index, target_id in enumerate(target_ids)
            if target_groups[target_id] == group
        ]))
        for group in TARGET_GROUPS
    }


def _assert_exact_keys(
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    expected: set[tuple[Any, ...]],
    description: str,
) -> None:
    observed: list[tuple[Any, ...]] = [
        tuple(row.get(field) for field in fields) for row in rows
    ]
    if len(observed) != len(set(observed)):
        raise ExploratoryAnalysisError(f"{description} contains duplicate keys")
    if set(observed) != expected:
        missing = len(expected - set(observed))
        extra = len(set(observed) - expected)
        raise ExploratoryAnalysisError(
            f"{description} key grid differs: {missing} missing and {extra} extra"
        )


def _build_rows(
    runs: Sequence[Mapping[str, Any]],
    authority: Mapping[str, Any],
    observed: Mapping[str, np.ndarray],
    bootstrap: Mapping[str, np.ndarray],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    target_ids = authority["target_ids"]
    target_groups = authority["target_groups"]
    family_target_rows: list[dict[str, Any]] = []
    transfer_target_rows: list[dict[str, Any]] = []
    family_cell_rows: list[dict[str, Any]] = []
    transfer_cell_rows: list[dict[str, Any]] = []
    layer_receipts: list[dict[str, Any]] = []

    for layer_index, layer in enumerate(LAYERS):
        layer_role = _layer_role(layer)
        target_matrix = observed["target_matrix"][layer_index]
        seed_scores = observed["seed_scores"][layer_index]
        specificity = observed["specificity"][layer_index]
        cross_median = observed["cross_median"][layer_index]

        for family_index, family in enumerate(FAMILY_ORDER):
            for target_index, target_id in enumerate(target_ids):
                family_target_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "analysis_id": ANALYSIS_ID,
                        "endpoint_ids": [ENDPOINT_WITHIN, ENDPOINT_SPECIFICITY],
                        "family": family,
                        "layer": layer,
                        "layer_role": layer_role,
                        "strength": STRENGTH,
                        "target_id": target_id,
                        "target_group": target_groups[target_id],
                        "within_family_M_by_direction_seed": {
                            str(seed): float(
                                seed_scores[
                                    family_index, family_index, seed_index, target_index
                                ]
                            )
                            for seed_index, seed in enumerate(DIRECTION_SEEDS)
                        },
                        "within_family_M": float(
                            observed["within"][layer_index, family_index, target_index]
                        ),
                        "cross_family_transfer_median_M": float(
                            cross_median[family_index, target_index]
                        ),
                        "family_specificity_R": float(
                            specificity[family_index, target_index]
                        ),
                    }
                )

            within_values = observed["within"][layer_index, family_index]
            specificity_values = specificity[family_index]
            descriptive_controls_by_seed: list[dict[str, Any]] = []
            run = runs[family_index]
            for seed in DIRECTION_SEEDS:
                screening = run["screening"][(layer, seed)]
                descriptive_controls_by_seed.append(
                    {
                        "seed": seed,
                        "random_intervention_row_count": run["random_cell_counts"][
                            (layer, seed)
                        ],
                        **screening,
                    }
                )
            family_cell_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "analysis_id": ANALYSIS_ID,
                    "endpoint_ids": [ENDPOINT_WITHIN, ENDPOINT_SPECIFICITY],
                    "family": family,
                    "layer": layer,
                    "layer_role": layer_role,
                    "strength": STRENGTH,
                    "target_count": len(target_ids),
                    "direction_seeds": list(DIRECTION_SEEDS),
                    "within_family_M_target_mean": float(np.mean(within_values)),
                    "within_family_M_target_mean_ci95": _interval(
                        bootstrap["matrix_means"][:, :, family_index, family_index][
                            layer_index
                        ]
                    ),
                    "within_family_M_target_median_secondary": float(
                        np.median(within_values)
                    ),
                    "within_family_M_target_group_means_secondary": _target_group_means(
                        within_values, target_ids, target_groups
                    ),
                    "cross_family_transfer_median_M_target_mean": float(
                        np.mean(cross_median[family_index])
                    ),
                    "family_specificity_R_target_mean": float(
                        np.mean(specificity_values)
                    ),
                    "family_specificity_R_target_mean_ci95": _interval(
                        bootstrap["specificity_means"][layer_index, :, family_index]
                    ),
                    "family_specificity_R_target_median_secondary": float(
                        np.median(specificity_values)
                    ),
                    "family_specificity_R_target_group_means_secondary": _target_group_means(
                        specificity_values, target_ids, target_groups
                    ),
                    "descriptive_fingerprint_controls_by_direction_seed": (
                        descriptive_controls_by_seed
                    ),
                    "zero_hook_control": run["zero_summary_by_layer"][layer],
                    "control_use": (
                        "descriptive_only; random and zero-hook controls are not "
                        "E1 endpoint observations"
                    ),
                }
            )

        for source_index, source_family in enumerate(FAMILY_ORDER):
            for prototype_index, prototype_family in enumerate(FAMILY_ORDER):
                if source_index == prototype_index:
                    continue
                values = target_matrix[source_index, prototype_index]
                for target_index, target_id in enumerate(target_ids):
                    transfer_target_rows.append(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "analysis_id": ANALYSIS_ID,
                            "endpoint_id": ENDPOINT_TRANSFER,
                            "source_family": source_family,
                            "prototype_family": prototype_family,
                            "matrix_notation": f"{source_family}<-{prototype_family}",
                            "layer": layer,
                            "layer_role": layer_role,
                            "strength": STRENGTH,
                            "target_id": target_id,
                            "target_group": target_groups[target_id],
                            "cross_family_M_by_direction_seed": {
                                str(seed): float(
                                    seed_scores[
                                        source_index,
                                        prototype_index,
                                        seed_index,
                                        target_index,
                                    ]
                                )
                                for seed_index, seed in enumerate(DIRECTION_SEEDS)
                            },
                            "cross_family_M": float(values[target_index]),
                        }
                    )
                transfer_cell_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "analysis_id": ANALYSIS_ID,
                        "endpoint_id": ENDPOINT_TRANSFER,
                        "source_family": source_family,
                        "prototype_family": prototype_family,
                        "matrix_notation": f"{source_family}<-{prototype_family}",
                        "layer": layer,
                        "layer_role": layer_role,
                        "strength": STRENGTH,
                        "target_count": len(target_ids),
                        "direction_seeds": list(DIRECTION_SEEDS),
                        "cross_family_M_target_mean": float(np.mean(values)),
                        "cross_family_M_target_mean_ci95": _interval(
                            bootstrap["matrix_means"][
                                layer_index, :, source_index, prototype_index
                            ]
                        ),
                        "cross_family_M_target_median_secondary": float(
                            np.median(values)
                        ),
                        "cross_family_M_target_group_means_secondary": _target_group_means(
                            values, target_ids, target_groups
                        ),
                    }
                )

        matrix_cells: list[dict[str, Any]] = []
        for source_index, source_family in enumerate(FAMILY_ORDER):
            for prototype_index, prototype_family in enumerate(FAMILY_ORDER):
                values = target_matrix[source_index, prototype_index]
                matrix_cells.append(
                    {
                        "source_family": source_family,
                        "prototype_family": prototype_family,
                        "diagonal": source_index == prototype_index,
                        "target_mean": float(np.mean(values)),
                        "target_mean_ci95": _interval(
                            bootstrap["matrix_means"][
                                layer_index, :, source_index, prototype_index
                            ]
                        ),
                        "target_median_secondary": float(np.median(values)),
                    }
                )
        family_specificity_rows = [
            {
                "family": family,
                "target_mean": float(np.mean(specificity[family_index])),
                "target_mean_ci95": _interval(
                    bootstrap["specificity_means"][layer_index, :, family_index]
                ),
                "target_median_secondary": float(
                    np.median(specificity[family_index])
                ),
            }
            for family_index, family in enumerate(FAMILY_ORDER)
        ]
        global_values = observed["global_specificity"][layer_index]
        layer_receipts.append(
            {
                "layer": layer,
                "layer_role": layer_role,
                "full_M_matrix": {
                    "row_role": "source_family_fingerprints",
                    "column_role": "prototype_family",
                    "family_order": list(FAMILY_ORDER),
                    "cells": matrix_cells,
                },
                "family_specificity_R": family_specificity_rows,
                "equal_family_global_specificity_R_global": {
                    "target_mean": float(np.mean(global_values)),
                    "target_mean_ci95": _interval(
                        bootstrap["global_specificity"][layer_index]
                    ),
                    "target_median_secondary": float(np.median(global_values)),
                },
            }
        )

    expected_family_targets = {
        (family, layer, target_id)
        for family in FAMILY_ORDER
        for layer in LAYERS
        for target_id in target_ids
    }
    expected_transfer_targets = {
        (source, prototype, layer, target_id)
        for source in FAMILY_ORDER
        for prototype in FAMILY_ORDER
        if source != prototype
        for layer in LAYERS
        for target_id in target_ids
    }
    expected_family_cells = {
        (family, layer) for family in FAMILY_ORDER for layer in LAYERS
    }
    expected_transfer_cells = {
        (source, prototype, layer)
        for source in FAMILY_ORDER
        for prototype in FAMILY_ORDER
        if source != prototype
        for layer in LAYERS
    }
    _assert_exact_keys(
        family_target_rows,
        ("family", "layer", "target_id"),
        expected_family_targets,
        "family target scores",
    )
    _assert_exact_keys(
        transfer_target_rows,
        ("source_family", "prototype_family", "layer", "target_id"),
        expected_transfer_targets,
        "transfer target scores",
    )
    _assert_exact_keys(
        family_cell_rows,
        ("family", "layer"),
        expected_family_cells,
        "family cell summary",
    )
    _assert_exact_keys(
        transfer_cell_rows,
        ("source_family", "prototype_family", "layer"),
        expected_transfer_cells,
        "transfer cell summary",
    )
    if [len(family_target_rows), len(transfer_target_rows), len(family_cell_rows), len(transfer_cell_rows)] != [
        240,
        960,
        10,
        40,
    ]:
        raise ExploratoryAnalysisError("Published E1 row counts differ from the freeze")
    return (
        family_target_rows,
        transfer_target_rows,
        family_cell_rows,
        transfer_cell_rows,
        layer_receipts,
    )


def _format_estimate(value: float, interval: Mapping[str, float]) -> str:
    return f"{value:.6f} [{interval['low']:.6f}, {interval['high']:.6f}]"


def _render_report(
    family_cells: Sequence[Mapping[str, Any]],
    transfer_cells: Sequence[Mapping[str, Any]],
    layer_receipts: Sequence[Mapping[str, Any]],
    runs: Sequence[Mapping[str, Any]],
    *,
    bootstrap_replicates: int,
    bootstrap_seed: int,
) -> str:
    family_lookup = {
        (row["family"], row["layer"]): row for row in family_cells
    }
    transfer_lookup = {
        (row["source_family"], row["prototype_family"], row["layer"]): row
        for row in transfer_cells
    }
    receipt_lookup = {row["layer"]: row for row in layer_receipts}
    lines = [
        "# E1 token-isomorphic emoji-family exploratory report",
        "",
        "This report publishes the complete prespecified five-family lattice. "
        "All estimates are descriptive and use only positive-strength RMS emoji "
        "fingerprints from the fixed MLX FP32 cell.",
        "",
        "The strongest permitted interpretation is exploratory matched-slot "
        "fingerprint recurrence under a fixed middle-token family substitution "
        "in one pinned GPT-2 MLX FP32 intervention cell. Family identity remains "
        "perfectly confounded with the family-middle token.",
        "",
        "## Fixed analysis",
        "",
        f"- Families: {', '.join(FAMILY_ORDER)}",
        f"- Layers: {PRIMARY_LAYER} (primary exploratory), "
        f"{NEGATIVE_COMPARATOR_LAYER} (prespecified secondary negative comparator)",
        f"- Direction seeds nested within target: {', '.join(map(str, DIRECTION_SEEDS))}",
        "- Targets: 24, four in each of six fixed groups",
        f"- Bootstrap: {bootstrap_replicates:,} joint group-stratified target resamples, "
        f"seed {bootstrap_seed}; all LOTO prototypes rebuilt inside every replicate",
        "- Interval notation below: observed target mean [2.5th, 97.5th bootstrap percentiles]",
        "",
    ]
    for layer in LAYERS:
        layer_result = receipt_lookup[layer]
        lines.extend(
            [
                f"## Layer {layer}: {_layer_role(layer).replace('_', ' ')}",
                "",
                "### Complete M matrix",
                "",
                "Rows are source-family fingerprints; columns are prototype families. "
                "Diagonal cells are within-family M and off-diagonal cells are ordered "
                "cross-family matched-slot transfer M.",
                "",
                "| source \\ prototype | " + " | ".join(FAMILY_ORDER) + " |",
                "|---|" + "---:|" * len(FAMILY_ORDER),
            ]
        )
        for source in FAMILY_ORDER:
            entries: list[str] = []
            for prototype in FAMILY_ORDER:
                if source == prototype:
                    row = family_lookup[(source, layer)]
                    value = row["within_family_M_target_mean"]
                    interval = row["within_family_M_target_mean_ci95"]
                else:
                    row = transfer_lookup[(source, prototype, layer)]
                    value = row["cross_family_M_target_mean"]
                    interval = row["cross_family_M_target_mean_ci95"]
                entries.append(_format_estimate(value, interval))
            lines.append(f"| {source} | " + " | ".join(entries) + " |")
        lines.extend(
            [
                "",
                "### Family specificity R",
                "",
                "For each target, R is its within-family M minus the median of its "
                "four off-diagonal prototype-family M values.",
                "",
                "| family | target mean R [95% bootstrap interval] | target median (secondary) |",
                "|---|---:|---:|",
            ]
        )
        for row in layer_result["family_specificity_R"]:
            lines.append(
                f"| {row['family']} | "
                f"{_format_estimate(row['target_mean'], row['target_mean_ci95'])} | "
                f"{row['target_median_secondary']:.6f} |"
            )
        global_row = layer_result["equal_family_global_specificity_R_global"]
        lines.extend(
            [
                "",
                "Equal-family global R: "
                f"**{_format_estimate(global_row['target_mean'], global_row['target_mean_ci95'])}**.",
                "",
            ]
        )

    lines.extend(
        [
            "## Descriptive controls and integrity",
            "",
            "Every family-by-layer-by-direction-seed random-control separation and "
            "emoji advantage-over-random value is retained in "
            "`family_cell_summary.jsonl`. No label permutations were run, and this "
            "analyzer computes no p-values. The random controls are descriptive "
            "screens, not E1 endpoint observations.",
            "",
            "| family | intervention rows | emoji rows used | random rows | zero-hook rows | max zero activation RMS | max zero logit RMS |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for run in runs:
        lines.append(
            f"| {run['role']} | {run['ledger_row_count']} | "
            f"{run['eligible_row_count']} | {run['condition_counts']['random']} | "
            f"{run['condition_counts']['zero']} | "
            f"{float(run['summary']['zero_hook_max_activation_delta_rms']):.10f} | "
            f"{float(run['summary']['zero_hook_max_logit_delta_rms']):.10f} |"
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This exploration does not establish semantic categories, a "
            "tokenizer-independent glyph property, causal localization, "
            "cross-model generality, backend replication, or behavioral meaning. "
            "It produces no significance, equivalence, multiplicity, selection, "
            "confirmation, robustness, or paper-gate decision.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze_exploratory(
    sky_run: Path,
    food_run: Path,
    animals_run: Path,
    transport_run: Path,
    social_run: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Validate five role-bound runs and publish the complete E1 analysis."""

    root = _repo_root()
    authority = _load_fixed_authority(root)
    run_paths = {
        "sky": Path(sky_run).resolve(),
        "food": Path(food_run).resolve(),
        "animals": Path(animals_run).resolve(),
        "transport": Path(transport_run).resolve(),
        "social": Path(social_run).resolve(),
    }
    if len(set(run_paths.values())) != len(FAMILY_ORDER):
        raise ExploratoryAnalysisError("The five family roles must use distinct run directories")
    for role, path in run_paths.items():
        if not path.is_dir():
            raise ExploratoryAnalysisError(f"Role {role} run directory is missing: {path}")
    output_dir = Path(output_dir).resolve()
    if output_dir in set(run_paths.values()):
        raise ExploratoryAnalysisError("Output directory cannot be one of the run directories")
    if output_dir.exists():
        raise ExploratoryAnalysisError("Output directory must not already exist")

    runs = [_load_run(run_paths[role], role, authority) for role in FAMILY_ORDER]
    target_ids = authority["target_ids"]
    group_indices = _group_indices(target_ids, authority["target_groups"])
    endpoint_tensor = _tensor(runs, target_ids)
    observed = _observed_endpoints(endpoint_tensor, group_indices)
    weights, draws = _bootstrap_weights(
        BOOTSTRAP_REPLICATES,
        BOOTSTRAP_SEED,
        len(target_ids),
        group_indices,
    )
    bootstrap = _bootstrap_endpoints(
        endpoint_tensor,
        weights,
        draws,
        group_indices,
        chunk_size=BOOTSTRAP_CHUNK_SIZE,
    )
    (
        family_target_rows,
        transfer_target_rows,
        family_cell_rows,
        transfer_cell_rows,
        layer_receipts,
    ) = _build_rows(runs, authority, observed, bootstrap)
    report = _render_report(
        family_cell_rows,
        transfer_cell_rows,
        layer_receipts,
        runs,
        bootstrap_replicates=BOOTSTRAP_REPLICATES,
        bootstrap_seed=BOOTSTRAP_SEED,
    )

    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_parent))
    try:
        family_target_path = staging / "family_target_scores.jsonl"
        transfer_target_path = staging / "transfer_target_scores.jsonl"
        family_cell_path = staging / "family_cell_summary.jsonl"
        transfer_cell_path = staging / "transfer_cell_summary.jsonl"
        report_path = staging / "report.md"
        _write_jsonl(family_target_path, family_target_rows)
        _write_jsonl(transfer_target_path, transfer_target_rows)
        _write_jsonl(family_cell_path, family_cell_rows)
        _write_jsonl(transfer_cell_path, transfer_cell_rows)
        _atomic_write(report_path, report.encode("utf-8"))

        hashed_outputs = [
            {
                "filename": path.name,
                "sha256": _sha256_file(path),
                **(
                    {"row_count": count}
                    if count is not None
                    else {}
                ),
            }
            for path, count in (
                (family_target_path, len(family_target_rows)),
                (transfer_target_path, len(transfer_target_rows)),
                (family_cell_path, len(family_cell_rows)),
                (transfer_cell_path, len(transfer_cell_rows)),
                (report_path, None),
            )
        ]
        input_records = [_input_record(run) for run in runs]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "analysis_id": ANALYSIS_ID,
            "analysis_implementation": {
                "path": Path(__file__).resolve().relative_to(root).as_posix(),
                "sha256": _sha256_file(Path(__file__).resolve()),
            },
            "manifest_binding": {
                "path": MANIFEST_PATH.as_posix(),
                "sha256": authority["manifest_sha256"],
            },
            "claim_boundary": (
                "Exploratory matched-slot fingerprint recurrence under a fixed "
                "middle-token family substitution in one pinned GPT-2 MLX FP32 "
                "intervention cell; no semantic, tokenizer-independent, causal, "
                "cross-model, backend-replication, or paper-gate claim is authorized."
            ),
            "fixed_cell": {
                "model": MODEL,
                "revision": REVISION,
                "backend": BACKEND,
                "dtype": DTYPE,
                "site": SITE,
                "layers": list(LAYERS),
                "primary_layer": PRIMARY_LAYER,
                "secondary_negative_comparator_layer": NEGATIVE_COMPARATOR_LAYER,
                "strength": STRENGTH,
                "direction_seeds": list(DIRECTION_SEEDS),
                "fingerprint_dim": FINGERPRINT_DIM,
                "fingerprint_seed": FINGERPRINT_SEED,
            },
            "target_sampling": {
                "bank_role": "reused_exploratory_prestage_targets",
                "selected_first_rows": len(target_ids),
                "ordered_target_ids": list(target_ids),
                "ordered_target_groups": [
                    authority["target_groups"][target_id] for target_id in target_ids
                ],
                "group_order": list(TARGET_GROUPS),
                "targets_per_group": TARGETS_PER_GROUP,
            },
            "endpoint_definitions": {
                ENDPOINT_WITHIN: (
                    "seed-averaged diagonal matched-slot cosine minus mean "
                    "mismatched-slot cosine"
                ),
                ENDPOINT_TRANSFER: (
                    "seed-averaged ordered off-diagonal matched-slot transfer M"
                ),
                ENDPOINT_SPECIFICITY: (
                    "within-family target M minus the median target M over the four "
                    "other prototype families"
                ),
                ENDPOINT_GLOBAL: (
                    "equal-family mean of family-specific target R, then target mean"
                ),
                "primary_cell_aggregate": "equal-target arithmetic mean",
                "target_medians": "secondary_description_only",
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "sampling_unit": "target_prompt_cluster",
                "stratification": "four targets sampled with replacement in each of six groups",
                "joint_across_all_families_layers_endpoints_and_pairs": True,
                "direction_seeds_nested_within_target": True,
                "loto_prototypes_rebuilt_inside_each_replicate": True,
                "interval": "95_percentile_2.5_97.5",
                "replicate_aggregate": "equal-target arithmetic mean",
            },
            "input_runs": input_records,
            "row_completeness": {
                "per_family_expected_intervention_rows": EXPECTED_INTERVENTION_ROWS_PER_RUN,
                "per_family_expected_positive_rms_emoji_rows": EXPECTED_POSITIVE_ROWS_PER_RUN,
                "per_family_expected_random_rows": EXPECTED_RANDOM_ROWS_PER_RUN,
                "per_family_expected_zero_hook_rows": EXPECTED_ZERO_ROWS_PER_RUN,
                "all_families_observed_intervention_rows": sum(
                    run["ledger_row_count"] for run in runs
                ),
                "all_families_observed_positive_rms_emoji_rows": sum(
                    run["eligible_row_count"] for run in runs
                ),
                "all_families_observed_random_rows": sum(
                    run["condition_counts"]["random"] for run in runs
                ),
                "all_families_observed_zero_hook_rows": sum(
                    run["condition_counts"]["zero"] for run in runs
                ),
                "published_row_counts": {
                    "family_target_scores.jsonl": len(family_target_rows),
                    "transfer_target_scores.jsonl": len(transfer_target_rows),
                    "family_cell_summary.jsonl": len(family_cell_rows),
                    "transfer_cell_summary.jsonl": len(transfer_cell_rows),
                },
                "exact_unique_key_grids_verified": True,
            },
            "zero_hook_integrity_by_family_and_layer": [
                {
                    "family": run["role"],
                    "layer": layer,
                    **run["zero_summary_by_layer"][layer],
                }
                for run in runs
                for layer in LAYERS
            ],
            "descriptive_control_boundary": {
                "random_control_cells_reported": len(FAMILY_ORDER)
                * len(LAYERS)
                * len(DIRECTION_SEEDS),
                "label_permutations_run": 0,
                "p_values_computed_by_analyzer": False,
                "endpoint_decisions_computed": False,
                "selection_performed": False,
                "random_and_zero_hook_controls_are_endpoint_observations": False,
            },
            "results_by_layer": layer_receipts,
            "output_inventory": [
                "family_target_scores.jsonl",
                "transfer_target_scores.jsonl",
                "family_cell_summary.jsonl",
                "transfer_cell_summary.jsonl",
                "emoji_family_exploratory_receipt.json",
                "report.md",
            ],
            "hashed_outputs_excluding_self": hashed_outputs,
        }
        receipt_path = staging / "emoji_family_exploratory_receipt.json"
        _write_json(receipt_path, receipt)
        observed_names = {path.name for path in staging.iterdir()}
        if observed_names != set(receipt["output_inventory"]):
            raise ExploratoryAnalysisError("Staged E1 output inventory differs")
        os.replace(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sky-run", required=True, type=Path)
    parser.add_argument("--food-run", required=True, type=Path)
    parser.add_argument("--animals-run", required=True, type=Path)
    parser.add_argument("--transport-run", required=True, type=Path)
    parser.add_argument("--social-run", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = analyze_exploratory(
            args.sky_run,
            args.food_run,
            args.animals_run,
            args.transport_run,
            args.social_run,
            args.output_dir,
        )
    except ExploratoryAnalysisError as exc:
        print(f"E1 analysis blocked: {exc}", file=sys.stderr)
        return 2
    print(
        f"Published {len(receipt['output_inventory'])} E1 files to "
        f"{Path(args.output_dir).resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
