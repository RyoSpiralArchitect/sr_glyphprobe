#!/usr/bin/env python3
"""Freeze, acquire, and analyze T18 fresh composite-glyph lexical alignment."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
from typing import Any, Iterable, Mapping, Sequence
import uuid

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import glyph_system_decomposition_v0 as t11  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-fresh-composite-glyph-lexical-confirmation-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/fresh_composite_glyph_lexical_confirmation_v0.yaml")
SELECTION_PATH = Path(
    "data/manifests/fresh_composite_glyph_lexical_confirmation_v0.json"
)
VALIDATION_DIRECTORY = Path("validation/fresh_composite_glyph_lexical_confirmation_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_DIRECTORY = VALIDATION_DIRECTORY / "tokenizers"
ENGINEERING_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "engineering_preflight.json"
FREEZE_PATH = Path(
    "data/manifests/fresh_composite_glyph_lexical_confirmation_v0_freeze.json"
)
VIEW_ORDER = ("glyph", "english_short_name", "japanese_short_name", "codepoint_literal")
SYSTEM_ORDER = ("modifier", "zwj", "regional_flag")
MODEL_ROLES = (
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
CORE_ROLES = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
)
DEPTH_FRACTIONS = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
PRIMARY_DEPTHS = (0.75, 0.875, 1.0)
PRIMARY_DEPTH_INDICES = tuple(DEPTH_FRACTIONS.index(value) for value in PRIMARY_DEPTHS)
PAIR_ORDER = (
    ("glyph_english", 0, 1),
    ("glyph_japanese", 0, 2),
    ("glyph_codepoint", 0, 3),
    ("english_japanese", 1, 2),
)
CLDR_FILES = {
    "english_annotations": "annotations-en.json",
    "english_derived_annotations": "annotations-derived-en.json",
    "japanese_annotations": "annotations-ja.json",
    "japanese_derived_annotations": "annotations-derived-ja.json",
}
STATIC_ASSETS = (
    CONFIG_PATH.as_posix(),
    SELECTION_PATH.as_posix(),
    "README.md",
    "README.ja.md",
    "docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md",
    "docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md",
    "scripts/fresh_composite_glyph_lexical_confirmation_v0.py",
    "scripts/validate_fresh_composite_glyph_lexical_confirmation_v0_result.py",
    "tests/test_fresh_composite_glyph_lexical_confirmation_v0.py",
    DESIGN_PREFLIGHT_PATH.as_posix(),
    ENGINEERING_PREFLIGHT_PATH.as_posix(),
)


class T18Error(RuntimeError):
    """Raised when a frozen T18 contract is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T18Error(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def _write_ledger(directory: Path, names: Sequence[str]) -> None:
    lines = [f"{_sha256(directory / name)}  {name}\n" for name in names]
    (directory / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def _git_value(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_root(), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _version_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _selection_hash(*parts: str) -> str:
    namespace = str(_config()["population"]["selection_namespace"])
    return _hash_text(":".join((namespace, *parts)))


def _verify_external_source(path: Path, spec: Mapping[str, Any]) -> bytes:
    raw = path.read_bytes()
    _require(
        len(raw) == int(spec["expected_bytes"]),
        f"Source byte count changed: {path.name}",
    )
    _require(
        hashlib.sha256(raw).hexdigest() == str(spec["sha256"]),
        f"Source hash changed: {path.name}",
    )
    return raw


def _cldr_map(raw: bytes, root_key: str) -> dict[str, dict[str, list[str]]]:
    value = json.loads(raw.decode("utf-8"))
    annotations = value[root_key]["annotations"]
    _require(
        isinstance(annotations, dict) and annotations, "CLDR annotations are empty"
    )
    return {str(key): dict(row) for key, row in annotations.items()}


def _merged_cldr(cldr_directory: Path, locale: str) -> dict[str, dict[str, list[str]]]:
    config = _config()["source_bindings"]["cldr"]
    keys = (
        ("english_annotations", "english_derived_annotations")
        if locale == "en"
        else ("japanese_annotations", "japanese_derived_annotations")
    )
    merged: dict[str, dict[str, list[str]]] = {}
    for key in keys:
        spec = config[key]
        raw = _verify_external_source(cldr_directory / CLDR_FILES[key], spec)
        current = _cldr_map(raw, str(spec["root_key"]))
        overlap = set(merged).intersection(current)
        _require(not overlap, f"Unexpected CLDR base/derived overlap: {locale}")
        merged.update(current)
    return merged


def _lookup_annotation(
    annotations: Mapping[str, Mapping[str, Sequence[str]]], glyph: str
) -> tuple[str, Mapping[str, Sequence[str]]] | None:
    for key in (glyph, glyph.replace("\ufe0f", "").replace("\ufe0e", "")):
        if key in annotations:
            return key, annotations[key]
    return None


def _git_archive_blobs(commit: str) -> dict[str, bytes]:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        cwd=_root(),
        check=True,
        capture_output=True,
    ).stdout
    blobs: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        for member in handle.getmembers():
            if not member.isfile():
                continue
            stream = handle.extractfile(member)
            _require(stream is not None, f"Cannot read archived blob: {member.name}")
            blobs[member.name] = stream.read()
    return blobs


def _canonical_family(codepoints: Sequence[int]) -> tuple[int, ...]:
    return tuple(
        int(value) for value in codepoints if not 0x1F3FB <= int(value) <= 0x1F3FF
    )


def _family_text(codepoints: Sequence[int]) -> str:
    return " ".join(f"{int(value):04X}" for value in _canonical_family(codepoints))


def _round_robin_select(
    rows: Sequence[Mapping[str, Any]], system: str, quota: int
) -> list[dict[str, Any]]:
    by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row["canonical_family_codepoint"])].append(row)
    representatives: list[dict[str, Any]] = []
    for family, members in sorted(by_family.items()):
        chosen = min(
            members,
            key=lambda row: _selection_hash(
                "representative", system, family, str(row["codepoint"])
            ),
        )
        representatives.append(dict(chosen))
    by_subgroup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in representatives:
        by_subgroup[str(row["subgroup"])].append(row)
    for subgroup in by_subgroup:
        by_subgroup[subgroup].sort(
            key=lambda row: _selection_hash("selection", system, str(row["codepoint"]))
        )
    subgroup_order = sorted(
        by_subgroup,
        key=lambda subgroup: _selection_hash("subgroup", system, subgroup),
    )
    selected: list[dict[str, Any]] = []
    round_index = 0
    while len(selected) < quota:
        progressed = False
        for subgroup in subgroup_order:
            if round_index >= len(by_subgroup[subgroup]) or len(selected) >= quota:
                continue
            row = dict(by_subgroup[subgroup][round_index])
            row["subgroup_round"] = round_index
            selected.append(row)
            progressed = True
        _require(progressed, f"System quota unavailable: {system}")
        round_index += 1
    return selected


def build_selection(
    emoji_test: Path, cldr_directory: Path, output: Path
) -> dict[str, Any]:
    config = _config()
    source_spec = config["source_bindings"]["unicode_emoji_test"]
    source = _verify_external_source(emoji_test, source_spec)
    parsed = t11._parse_unicode_source(source)
    _require(
        parsed["version"] == str(source_spec["unicode_emoji_version"]),
        "Emoji source version changed",
    )
    full = parsed["fully_qualified"]
    _require(
        len(full) == int(source_spec["expected_fully_qualified_entries"]),
        "Emoji source count changed",
    )
    english = _merged_cldr(cldr_directory, "en")
    japanese = _merged_cldr(cldr_directory, "ja")
    _require(set(english) == set(japanese), "English/Japanese CLDR key sets differ")

    t11_spec = config["source_bindings"]["t11_selection"]
    t11_path = _root() / str(t11_spec["path"])
    _require(
        _sha256(t11_path) == str(t11_spec["sha256"]), "T11 selection binding changed"
    )
    t11_manifest = _read_json(t11_path)
    excluded_identities = {str(row["codepoint"]) for row in t11_manifest["items"]}

    exposure = config["source_bindings"]["exposure_tree"]
    commit = str(exposure["commit"])
    _require(
        _git_value("rev-parse", f"{commit}^{{tree}}") == str(exposure["tree"]),
        "Exposure tree changed",
    )
    blobs = _git_archive_blobs(commit)
    _require(
        len(blobs) == int(exposure["tracked_paths"]), "Exposure path count changed"
    )

    eligible: list[dict[str, Any]] = []
    census = Counter()
    exclusions = Counter()
    hit_path_examples: list[dict[str, Any]] = []
    maximum_version = _version_key(str(config["population"]["maximum_emoji_version"]))
    for source_index, original in enumerate(full):
        values = tuple(int(value) for value in original["codepoints"])
        system = t11._classify_system(values)
        census[f"source_{system}"] += 1
        if system not in SYSTEM_ORDER:
            exclusions["outside_frozen_system_roster"] += 1
            continue
        if _version_key(str(original["emoji_version"])) > maximum_version:
            exclusions["newer_than_maximum_emoji_version"] += 1
            continue
        codepoint = str(original["codepoint"])
        if codepoint in excluded_identities:
            exclusions["identity_in_complete_t11_selection"] += 1
            continue
        glyph = "".join(chr(value) for value in values)
        hit_paths = sorted(
            path for path, raw in blobs.items() if glyph.encode("utf-8") in raw
        )
        if hit_paths:
            exclusions["exact_surface_in_exposure_tree"] += 1
            if len(hit_path_examples) < 32:
                hit_path_examples.append(
                    {"codepoint": codepoint, "glyph": glyph, "paths": hit_paths[:8]}
                )
            continue
        en = _lookup_annotation(english, glyph)
        ja = _lookup_annotation(japanese, glyph)
        if en is None or ja is None or not en[1].get("tts") or not ja[1].get("tts"):
            exclusions["missing_cldr_tts"] += 1
            continue
        english_name = str(en[1]["tts"][0])
        _require(
            english_name == str(original["name"]),
            f"Emoji short name/CLDR English tts mismatch: {codepoint}",
        )
        row = {
            "source_index": source_index,
            "codepoint": codepoint,
            "codepoints": [f"U+{value:04X}" for value in values],
            "codepoint_literal": " ".join(f"U+{value:04X}" for value in values),
            "glyph": glyph,
            "english_short_name": english_name,
            "japanese_short_name": str(ja[1]["tts"][0]),
            "cldr_english_lookup_surface": en[0],
            "cldr_japanese_lookup_surface": ja[0],
            "cldr_english_keywords": [str(value) for value in en[1].get("default", [])],
            "glyph_system": system,
            "canonical_family_codepoint": _family_text(values),
            "group": str(original["group"]),
            "subgroup": str(original["subgroup"]),
            "emoji_version": str(original["emoji_version"]),
        }
        eligible.append(row)
        census[f"eligible_{system}"] += 1

    selected: list[dict[str, Any]] = []
    quotas = config["population"]["quotas"]
    for system in SYSTEM_ORDER:
        system_rows = [row for row in eligible if row["glyph_system"] == system]
        chosen = _round_robin_select(system_rows, system, int(quotas[system]))
        selected.extend(chosen)
    selected.sort(key=lambda row: int(row["source_index"]))
    for selection_index, row in enumerate(selected):
        row["selection_index"] = selection_index
        row["selection_hash"] = _selection_hash(
            "selection", str(row["glyph_system"]), str(row["codepoint"])
        )
        row["exact_surface_hit_count_in_exposure_tree"] = 0
        row["identity_in_t11_selection"] = False

    _require(
        len(selected) == int(config["population"]["expected_items"]),
        "Selected count changed",
    )
    _require(
        Counter(str(row["glyph_system"]) for row in selected)
        == Counter({str(key): int(value) for key, value in quotas.items()}),
        "Selected system quotas changed",
    )
    for view in VIEW_ORDER:
        values = [str(row[view]) for row in selected]
        _require(
            len(values) == len(set(values)), f"Selected view is non-unique: {view}"
        )
    families = [
        (str(row["glyph_system"]), str(row["canonical_family_codepoint"]))
        for row in selected
    ]
    _require(len(families) == len(set(families)), "Canonical family repeated")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "prospective_exact_surface_selection_complete_zero_t18_model_forwards",
        "source_bindings": {
            "unicode_emoji_test": {
                "url": source_spec["url"],
                "bytes": len(source),
                "sha256": hashlib.sha256(source).hexdigest(),
                "version": parsed["version"],
                "fully_qualified_entries": len(full),
            },
            "cldr": {
                key: {
                    "url": config["source_bindings"]["cldr"][key]["url"],
                    "bytes": int(
                        config["source_bindings"]["cldr"][key]["expected_bytes"]
                    ),
                    "sha256": str(config["source_bindings"]["cldr"][key]["sha256"]),
                }
                for key in CLDR_FILES
            },
            "t11_selection_sha256": _sha256(t11_path),
        },
        "exposure_audit": {
            "commit": commit,
            "tree": str(exposure["tree"]),
            "regular_git_blobs_scanned": len(blobs),
            "definition": str(exposure["definition"]),
            "selected_exact_surface_hits": 0,
            "selected_t11_identity_hits": 0,
            "excluded_candidate_hit_path_examples": hit_path_examples,
            "claim_scope": "repository_relative_exact_UTF8_surface_freshness_only",
        },
        "selection": {
            "namespace": str(config["population"]["selection_namespace"]),
            "maximum_emoji_version": str(config["population"]["maximum_emoji_version"]),
            "system_order": list(SYSTEM_ORDER),
            "quotas": {str(key): int(value) for key, value in quotas.items()},
            "eligible_census": dict(sorted(census.items())),
            "exclusion_census": dict(sorted(exclusions.items())),
            "canonical_family_rule": str(config["population"]["canonical_family_rule"]),
            "within_system_selection": str(
                config["population"]["within_system_selection"]
            ),
            "final_order": str(config["population"]["final_order"]),
        },
        "items": selected,
        "item_count": len(selected),
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "pretraining_holdout_claim_authorized": False,
        "semantic_concept_holdout_claim_authorized": False,
    }
    _require(not output.exists(), f"Selection output exists: {output}")
    _write_json(output, manifest)
    return {
        "status": "pass",
        "items": len(selected),
        "system_counts": dict(Counter(row["glyph_system"] for row in selected)),
        "sha256": _sha256(output),
        "model_forward_calls": 0,
    }


def items() -> list[dict[str, Any]]:
    manifest = _read_json(_root() / SELECTION_PATH)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Selection protocol mismatch")
    _require(
        manifest.get("status")
        == "prospective_exact_surface_selection_complete_zero_t18_model_forwards",
        "Selection status changed",
    )
    rows = [dict(row) for row in manifest["items"]]
    rows.sort(key=lambda row: int(row["selection_index"]))
    return rows


def audit_selection(*, rescan_exposure: bool = True) -> dict[str, Any]:
    config = _config()
    manifest = _read_json(_root() / SELECTION_PATH)
    rows = items()
    _require(
        len(rows) == int(config["population"]["expected_items"]),
        "Selection item count changed",
    )
    _require(
        [int(row["selection_index"]) for row in rows] == list(range(len(rows))),
        "Selection order changed",
    )
    quotas = Counter(str(row["glyph_system"]) for row in rows)
    _require(
        quotas
        == Counter(
            {
                str(key): int(value)
                for key, value in config["population"]["quotas"].items()
            }
        ),
        "Selection quotas changed",
    )
    for view in VIEW_ORDER:
        values = [str(row[view]) for row in rows]
        _require(len(values) == len(set(values)), f"Selection view collapsed: {view}")
    families = [
        (row["glyph_system"], row["canonical_family_codepoint"]) for row in rows
    ]
    _require(len(families) == len(set(families)), "Selection family repeated")
    t11_spec = config["source_bindings"]["t11_selection"]
    t11_path = _root() / str(t11_spec["path"])
    _require(_sha256(t11_path) == str(t11_spec["sha256"]), "T11 binding changed")
    old = {str(row["codepoint"]) for row in _read_json(t11_path)["items"]}
    _require(
        not old.intersection(str(row["codepoint"]) for row in rows),
        "T11 identity leaked into T18",
    )
    if rescan_exposure:
        exposure = config["source_bindings"]["exposure_tree"]
        blobs = _git_archive_blobs(str(exposure["commit"]))
        _require(
            len(blobs) == int(exposure["tracked_paths"]), "Exposure path count changed"
        )
        for row in rows:
            raw = str(row["glyph"]).encode("utf-8")
            _require(
                not any(raw in blob for blob in blobs.values()),
                f"Selected glyph was exposed: {row['codepoint']}",
            )
    _require(
        int(manifest.get("model_forward_calls", -1)) == 0,
        "Selection used a model forward",
    )
    return {
        "status": "pass",
        "items": len(rows),
        "system_counts": dict(quotas),
        "exact_surface_fresh_relative_to_frozen_tree": True,
        "outside_complete_t11_selection": True,
        "selection_sha256": _sha256(_root() / SELECTION_PATH),
        "model_forward_calls": 0,
    }


def resolved_layers(role: str) -> tuple[int, ...]:
    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    count = int(t10._model_spec(role)["expected_num_layers"])
    return tuple(min(count - 1, math.floor(value * count)) for value in DEPTH_FRACTIONS)


def audit_design(output: Path | None = None) -> dict[str, Any]:
    config = _config()
    # The standalone selection audit performs the expensive immutable-tree
    # byte rescan. Downstream preflights bind that audited manifest by hash.
    selection = audit_selection(rescan_exposure=False)
    _require(
        tuple(str(value) for value in config["models"]["order"]) == MODEL_ROLES,
        "Model order changed",
    )
    _require(
        tuple(str(value) for value in config["models"]["core_order"]) == CORE_ROLES,
        "Core order changed",
    )
    _require(
        tuple(
            float(value) for value in config["depth"]["collected_normalized_fractions"]
        )
        == DEPTH_FRACTIONS,
        "Depth roster changed",
    )
    _require(
        tuple(float(value) for value in config["depth"]["primary_normalized_fractions"])
        == PRIMARY_DEPTHS,
        "Primary depth window changed",
    )
    source_hashes: dict[str, str] = {}
    for key in ("t11_selection", "t10_freeze", "t17_result"):
        spec = config["source_bindings"][key]
        path = _root() / str(spec["path"])
        _require(path.is_file(), f"Bound source missing: {path}")
        _require(
            _sha256(path) == str(spec["sha256"]), f"Bound source changed: {path.name}"
        )
        source_hashes[path.relative_to(_root()).as_posix()] = _sha256(path)
    resolved = {role: list(resolved_layers(role)) for role in MODEL_ROLES}
    _require(
        all(len(set(value)) == len(DEPTH_FRACTIONS) for value in resolved.values()),
        "Depth resolution collapsed",
    )
    forwards = len(items()) * len(VIEW_ORDER) * 2
    vectors = forwards * 4 * len(DEPTH_FRACTIONS)
    acquisition = config["acquisition"]
    _require(
        forwards == int(acquisition["expected_model_forward_calls_per_model"]),
        "Per-model forward budget changed",
    )
    _require(
        vectors == int(acquisition["expected_readout_vectors_per_model"]),
        "Per-model vector budget changed",
    )
    _require(
        forwards * len(MODEL_ROLES)
        == int(acquisition["expected_total_model_forward_calls"]),
        "Total forward budget changed",
    )
    _require(
        vectors * len(MODEL_ROLES)
        == int(acquisition["expected_total_readout_vectors"]),
        "Total vector budget changed",
    )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t18_model_forwards",
        "selection": selection,
        "source_hashes": source_hashes,
        "views": list(VIEW_ORDER),
        "systems": list(SYSTEM_ORDER),
        "model_roles": list(MODEL_ROLES),
        "core_roles": list(CORE_ROLES),
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "primary_normalized_depth_fractions": list(PRIMARY_DEPTHS),
        "resolved_block_indices": resolved,
        "model_forwards_per_role": forwards,
        "model_forwards_total": forwards * len(MODEL_ROLES),
        "readout_vectors_per_role": vectors,
        "readout_vectors_total": vectors * len(MODEL_ROLES),
        "exact_surface_holdout": True,
        "pretraining_or_semantic_holdout": False,
        "model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    if output is not None:
        _require(not output.exists(), f"Design preflight exists: {output}")
        _write_json(output, value)
    return value


def _view_text(item: Mapping[str, Any], view: str) -> str:
    _require(view in VIEW_ORDER, f"Unknown view: {view}")
    value = item.get(view)
    _require(isinstance(value, str) and bool(value), f"Unavailable view: {view}")
    return value


def _sequence_hash(rows: Sequence[Sequence[int]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        encoded = json.dumps([int(value) for value in row], separators=(",", ":"))
        digest.update(encoded.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _tokenizer_asset_hashes(snapshot: Path) -> dict[str, str]:
    names = (
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "added_tokens.json",
        "vocab.json",
        "merges.txt",
        "tokenizer.model",
    )
    result: dict[str, str] = {}
    for name in names:
        path = snapshot / name
        if path.is_file():
            result[name] = _sha256(path.resolve())
    _require(result, f"No tokenizer assets found: {snapshot}")
    return result


def _strata_receipt(
    item_rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
) -> dict[str, Any]:
    by_system: dict[str, dict[tuple[Any, ...], list[int]]] = {
        system: defaultdict(list) for system in SYSTEM_ORDER
    }
    for row in item_rows:
        system = str(row["glyph_system"])
        key = tuple(row[field] for field in fields)
        by_system[system][key].append(int(row["item_index"]))
    eligible_global_by_system: dict[str, list[int]] = {}
    eligible_local_strata_by_system: dict[str, list[list[int]]] = {}
    strata_rows: dict[str, list[dict[str, Any]]] = {}
    for system in SYSTEM_ORDER:
        groups = by_system[system]
        eligible_groups = [
            indices for _, indices in sorted(groups.items()) if len(indices) >= 2
        ]
        eligible = sorted(index for group in eligible_groups for index in group)
        lookup = {global_index: local for local, global_index in enumerate(eligible)}
        local = [[lookup[index] for index in group] for group in eligible_groups]
        eligible_global_by_system[system] = eligible
        eligible_local_strata_by_system[system] = local
        strata_rows[system] = [
            {"key": list(key), "global_item_indices": indices, "count": len(indices)}
            for key, indices in sorted(groups.items())
        ]
    eligible_union = sorted(
        index for system in SYSTEM_ORDER for index in eligible_global_by_system[system]
    )
    return {
        "key_fields": list(fields),
        "eligible_item_count": len(eligible_union),
        "excluded_singleton_item_count": len(item_rows) - len(eligible_union),
        "eligible_item_count_by_system": {
            system: len(eligible_global_by_system[system]) for system in SYSTEM_ORDER
        },
        "eligible_global_indices_by_system": eligible_global_by_system,
        "eligible_local_strata_by_system": eligible_local_strata_by_system,
        "strata_by_system": strata_rows,
    }


def _tokenize_roster(tokenizer: Any) -> dict[str, Any]:
    config = _config()
    population = items()
    raw_by_view: dict[str, list[list[int]]] = {view: [] for view in VIEW_ORDER}
    combined: dict[str, dict[str, list[list[int]]]] = {
        view: {str(carrier): [] for carrier in config["input"]["carrier_order"]}
        for view in VIEW_ORDER
    }
    item_rows: list[dict[str, Any]] = []
    for item_index, item in enumerate(population):
        lengths: dict[str, int] = {}
        for view in VIEW_ORDER:
            raw = [
                int(value)
                for value in tokenizer.encode(
                    _view_text(item, view), add_special_tokens=False
                )
            ]
            _require(raw, f"Empty tokenization: {item['codepoint']}/{view}")
            raw_by_view[view].append(raw)
            lengths[view] = len(raw)
        item_rows.append(
            {
                "item_index": item_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_system": str(item["glyph_system"]),
                "token_counts": lengths,
                "glyph_token_count": lengths["glyph"],
                "english_short_name_token_count": lengths["english_short_name"],
                "japanese_short_name_token_count": lengths["japanese_short_name"],
                "codepoint_literal_token_count": lengths["codepoint_literal"],
            }
        )
    for view in VIEW_ORDER:
        _require(
            len({tuple(row) for row in raw_by_view[view]}) == len(population),
            f"Non-unique token sequence: {view}",
        )
    carrier_rows: dict[str, Any] = {}
    maximum_tokens = 0
    for carrier in config["input"]["carrier_order"]:
        carrier = str(carrier)
        spec = config["input"]["carriers"][carrier]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        unit_ids = [
            int(value) for value in tokenizer.encode(unit, add_special_tokens=False)
        ]
        _require(len(unit_ids) == 1, f"Carrier is not one token: {carrier}")
        prefix_exact = 0
        decode_exact = 0
        for view in VIEW_ORDER:
            for item_index, item in enumerate(population):
                text = _view_text(item, view) + unit * repeats
                ids = [
                    int(value)
                    for value in tokenizer.encode(text, add_special_tokens=False)
                ]
                expected = raw_by_view[view][item_index] + unit_ids * repeats
                _require(
                    ids == expected,
                    f"Carrier boundary changed: {item['codepoint']}/{view}/{carrier}",
                )
                combined[view][carrier].append(ids)
                prefix_exact += int(ids[:-repeats] == raw_by_view[view][item_index])
                decode_exact += int(
                    tokenizer.decode(
                        ids,
                        clean_up_tokenization_spaces=False,
                        skip_special_tokens=False,
                    )
                    == text
                )
                maximum_tokens = max(maximum_tokens, len(ids))
        expected_cases = len(population) * len(VIEW_ORDER)
        _require(
            prefix_exact == expected_cases, f"Carrier prefix check failed: {carrier}"
        )
        _require(
            decode_exact == expected_cases, f"Carrier decode check failed: {carrier}"
        )
        carrier_rows[carrier] = {
            "unit": unit,
            "repeats": repeats,
            "token_id": unit_ids[0],
            "prefix_exact_count": prefix_exact,
            "decode_exact_count": decode_exact,
        }
    primary = _strata_receipt(
        item_rows,
        (
            "glyph_token_count",
            "english_short_name_token_count",
            "codepoint_literal_token_count",
        ),
    )
    secondary = _strata_receipt(
        item_rows,
        (
            "glyph_token_count",
            "japanese_short_name_token_count",
            "english_short_name_token_count",
        ),
    )
    guardrail = config["tokenization_guardrail"]
    _require(
        int(primary["eligible_item_count"])
        >= int(guardrail["minimum_eligible_items_total"]),
        "Primary exact-stratum coverage below frozen total minimum",
    )
    for system in SYSTEM_ORDER:
        _require(
            int(primary["eligible_item_count_by_system"][system])
            >= int(guardrail["minimum_eligible_items_per_system"]),
            f"Primary exact-stratum coverage below system minimum: {system}",
        )
    token_histograms = {
        view: {
            str(length): int(count)
            for length, count in sorted(
                Counter(len(ids) for ids in raw_by_view[view]).items()
            )
        }
        for view in VIEW_ORDER
    }
    return {
        "raw_ids": raw_by_view,
        "combined_ids": combined,
        "receipt": {
            "item_count": len(population),
            "view_order": list(VIEW_ORDER),
            "item_token_counts": item_rows,
            "token_count_histograms": token_histograms,
            "ordered_sequence_sha256": {
                "raw": {view: _sequence_hash(raw_by_view[view]) for view in VIEW_ORDER},
                "combined": {
                    view: {
                        carrier: _sequence_hash(combined[view][carrier])
                        for carrier in config["input"]["carrier_order"]
                    }
                    for view in VIEW_ORDER
                },
            },
            "carriers": carrier_rows,
            "maximum_combined_token_count": maximum_tokens,
            "primary_exact_strata": primary,
            "japanese_secondary_exact_strata": secondary,
        },
    }


def tokenizer_preflight(role: str, model_path: Path, output: Path) -> dict[str, Any]:
    from transformers import AutoTokenizer

    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    audit_design()
    snapshot = model_path.resolve()
    _require(snapshot.is_dir(), f"Tokenizer snapshot missing: {snapshot}")
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    roster = _tokenize_roster(tokenizer)
    t10_roster = t10._tokenize_roster(tokenizer, t10._config())["receipt"]
    t10_receipt = _read_json(t10._receipt_path(role))["tokenizer"]
    reference_exact = (
        t10_roster["ordered_sequence_sha256"] == t10_receipt["ordered_sequence_sha256"]
    )
    _require(
        reference_exact,
        f"Tokenizer proxy differs on the complete T10 reference surface: {role}",
    )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_only_candidate_preflight_pass_zero_t18_model_forwards",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "frozen_model_revision": t10._model_spec(role)["revision"],
        "preflight_snapshot_basename": snapshot.name,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": int(len(tokenizer)),
        "tokenizer_asset_sha256": _tokenizer_asset_hashes(snapshot),
        "t10_reference_surface_sequence_equivalence": reference_exact,
        "t10_reference_surface_receipt_sha256": _sha256(t10._receipt_path(role)),
        "exact_frozen_model_runtime_revalidation_required": True,
        "tokenizer": roster["receipt"],
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "model_forward_calls": 0,
        "model_weights_loaded": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"Tokenizer preflight exists: {output}")
    _write_json(output, value)
    return {
        "status": "pass",
        "role": role,
        "primary_matched_items": value["tokenizer"]["primary_exact_strata"][
            "eligible_item_count"
        ],
        "primary_matched_by_system": value["tokenizer"]["primary_exact_strata"][
            "eligible_item_count_by_system"
        ],
        "japanese_matched_items": value["tokenizer"]["japanese_secondary_exact_strata"][
            "eligible_item_count"
        ],
        "sha256": _sha256(output),
        "model_forward_calls": 0,
    }


def _tokenizer_receipt_path(role: str) -> Path:
    return _root() / TOKENIZER_DIRECTORY / f"{role}.json"


def assemble_engineering_preflight(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(
        design.get("status") == "design_pass_zero_t18_model_forwards",
        "Design preflight incomplete",
    )
    roles: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for role in MODEL_ROLES:
        path = _tokenizer_receipt_path(role)
        value = _read_json(path)
        _require(
            value.get("protocol_id") == PROTOCOL_ID,
            f"Tokenizer protocol mismatch: {role}",
        )
        _require(value.get("model_role") == role, f"Tokenizer role mismatch: {role}")
        _require(
            value.get("t10_reference_surface_sequence_equivalence") is True,
            f"Tokenizer reference mismatch: {role}",
        )
        _require(
            int(value.get("model_forward_calls", -1)) == 0,
            f"Tokenizer preflight used a forward: {role}",
        )
        primary = value["tokenizer"]["primary_exact_strata"]
        roles[role] = {
            "primary_matched_items": int(primary["eligible_item_count"]),
            "primary_matched_items_by_system": {
                system: int(primary["eligible_item_count_by_system"][system])
                for system in SYSTEM_ORDER
            },
            "japanese_secondary_matched_items": int(
                value["tokenizer"]["japanese_secondary_exact_strata"][
                    "eligible_item_count"
                ]
            ),
            "maximum_combined_token_count": int(
                value["tokenizer"]["maximum_combined_token_count"]
            ),
            "exact_frozen_model_runtime_revalidation_required": True,
        }
        hashes[role] = _sha256(path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "nine_tokenizer_candidate_preflights_pass_zero_t18_model_forwards",
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "tokenizer_receipt_sha256": hashes,
        "roles": roles,
        "minimum_primary_matched_items": min(
            row["primary_matched_items"] for row in roles.values()
        ),
        "minimum_primary_matched_items_by_system": {
            system: min(
                row["primary_matched_items_by_system"][system] for row in roles.values()
            )
            for system in SYSTEM_ORDER
        },
        "minimum_japanese_secondary_matched_items": min(
            row["japanese_secondary_matched_items"] for row in roles.values()
        ),
        "exact_frozen_model_runtime_sequence_revalidation_required_before_first_forward": True,
        "model_forwards": 0,
        "model_weights_loaded": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"Engineering preflight exists: {output}")
    _write_json(output, value)
    return {
        "status": "pass",
        "sha256": _sha256(output),
        **{
            key: value[key]
            for key in (
                "minimum_primary_matched_items",
                "minimum_primary_matched_items_by_system",
                "minimum_japanese_secondary_matched_items",
            )
        },
    }


def _frozen_assets() -> tuple[str, ...]:
    tokenizers = tuple(
        (TOKENIZER_DIRECTORY / f"{role}.json").as_posix() for role in MODEL_ROLES
    )
    config = _config()
    sources = tuple(
        str(config["source_bindings"][key]["path"])
        for key in ("t11_selection", "t10_freeze", "t17_result")
    )
    return STATIC_ASSETS + tokenizers + sources


def build_freeze(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    engineering = _read_json(_root() / ENGINEERING_PREFLIGHT_PATH)
    _require(
        design.get("status") == "design_pass_zero_t18_model_forwards",
        "Design preflight incomplete",
    )
    _require(
        engineering.get("status")
        == "nine_tokenizer_candidate_preflights_pass_zero_t18_model_forwards",
        "Engineering preflight incomplete",
    )
    _require(
        int(design.get("model_forwards", -1)) == 0
        and int(engineering.get("model_forwards", -1)) == 0,
        "Preflight used a model forward",
    )
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        _require(path.is_file(), f"Frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    t10_freeze = _read_json(
        _root() / str(_config()["source_bindings"]["t10_freeze"]["path"])
    )
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t18_model_forwards",
        "experiment_role": _config()["experiment_role"],
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "engineering_preflight_sha256": _sha256(_root() / ENGINEERING_PREFLIGHT_PATH),
        "tokenizer_receipt_sha256": engineering["tokenizer_receipt_sha256"],
        "model_artifacts": t10_freeze["model_artifacts"],
        "model_roles": list(MODEL_ROLES),
        "core_roles": list(CORE_ROLES),
        "population_items": len(items()),
        "view_order": list(VIEW_ORDER),
        "system_order": list(SYSTEM_ORDER),
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "primary_normalized_depth_fractions": list(PRIMARY_DEPTHS),
        "resolved_block_indices": design["resolved_block_indices"],
        "model_forwards_at_freeze": 0,
        "model_weights_loaded_at_freeze": False,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "exact_frozen_model_runtime_sequence_revalidation_required_before_first_forward": True,
        "exact_surface_holdout": True,
        "pretraining_or_semantic_holdout": False,
    }
    _require(not output.exists(), f"Freeze manifest exists: {output}")
    _write_json(output, value)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
        "model_forwards": 0,
    }


def audit_freeze(*, require_pushed: bool = False) -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch")
    _require(
        value.get("status") == "final_execution_freeze_zero_t18_model_forwards",
        "Freeze status incomplete",
    )
    _require(
        int(value.get("model_forwards_at_freeze", -1)) == 0,
        "Freeze used a model forward",
    )
    for relative, expected in value["frozen_assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"Frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"Frozen asset changed: {relative}")
    git: dict[str, Any] = {"required": False}
    if require_pushed:
        head = _git_value("rev-parse", "HEAD")
        remote_main = _git_value("rev-parse", "origin/main")
        _require(head == remote_main, "T18 freeze commit is not pushed to origin/main")
        _git_value("cat-file", "-e", f"HEAD:{FREEZE_PATH.as_posix()}")
        git = {"required": True, "head": head, "origin_main": remote_main}
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path), "git": git}


def _records(roster: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item_index, _item in enumerate(items()):
        for view_index, view in enumerate(VIEW_ORDER):
            raw_ids = [int(value) for value in roster["raw_ids"][view][item_index]]
            for carrier_index, carrier in enumerate(
                _config()["input"]["carrier_order"]
            ):
                carrier = str(carrier)
                rows.append(
                    {
                        "item_offset": item_index,
                        "view_index": view_index,
                        "view": view,
                        "carrier_index": carrier_index,
                        "carrier": carrier,
                        "raw_ids": raw_ids,
                        "input_ids": [
                            int(value)
                            for value in roster["combined_ids"][view][carrier][
                                item_index
                            ]
                        ],
                    }
                )
    return rows


def _yield_if_contended(output_root: Path, role: str, boundary: str) -> None:
    pids = atlas._foreign_gpu_pids()
    if not pids:
        return
    role_root = output_root / role
    role_root.mkdir(parents=True, exist_ok=True)
    receipt = role_root / "yield_receipt.json"
    if not receipt.exists():
        _write_json(
            receipt,
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "status": "yielded_for_foreign_gpu_contention",
                "model_role": role,
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "time_utc": datetime.now(timezone.utc).isoformat(),
            },
        )
    raise SystemExit(
        int(_config()["execution_policy"]["yield_exit_code_on_foreign_contention"])
    )


def _shard_count() -> int:
    return math.ceil(len(items()) / int(_config()["acquisition"]["item_shard_size"]))


def _capture_shard(
    *,
    role: str,
    shard_index: int,
    output_root: Path,
    torch: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
    roster: Mapping[str, Any],
) -> dict[str, Any]:
    config = _config()
    role_root = output_root / role
    final = role_root / f"shard_{shard_index:04d}"
    if final.is_dir():
        return validate_shard(role, shard_index, output_root)
    _yield_if_contended(output_root, role, f"before_shard_{shard_index:04d}")
    role_root.mkdir(parents=True, exist_ok=True)
    stale = list(role_root.glob(f".shard_{shard_index:04d}.stage-*"))
    _require(not stale, f"Incomplete shard stage requires adjudication: {stale}")
    stage = role_root / f".shard_{shard_index:04d}.stage-{uuid.uuid4().hex}"
    stage.mkdir()
    population = items()
    size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * size
    stop = min(len(population), start + size)
    _require(start < stop, f"Shard index out of range: {shard_index}")
    shard_items = population[start:stop]
    layer_indices = resolved_layers(role)
    width = int(t10._model_spec(role)["expected_model_dim"])
    activations = np.empty(
        (len(shard_items), len(VIEW_ORDER), 2, 4, len(DEPTH_FRACTIONS), width),
        dtype=np.float32,
    )
    records = [
        {**row, "item_offset": int(row["item_offset"]) - start}
        for row in _records(roster)
        if start <= int(row["item_offset"]) < stop
    ]
    _require(
        len(records) == len(shard_items) * len(VIEW_ORDER) * 2,
        "Shard record count changed",
    )
    _write_json(
        stage / "execution_intent.json",
        {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "forward_may_begin_after_this_record",
            "model_role": role,
            "shard_index": shard_index,
            "item_index_start": start,
            "item_index_stop_exclusive": stop,
            "item_codepoints": [str(item["codepoint"]) for item in shard_items],
            "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        },
    )
    distances = [int(value) for value in config["input"]["distance_order"]]
    observations: list[dict[str, Any]] = []
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for record_index, row in enumerate(records):
        if record_index and record_index % 128 == 0:
            _yield_if_contended(
                output_root, role, f"shard_{shard_index:04d}_record_{record_index}"
            )
        ids = [int(value) for value in row["input_ids"]]
        input_ids = torch.tensor([ids], dtype=torch.long, device="cuda")
        attention_mask = torch.ones_like(input_ids)
        positions = [len(row["raw_ids"]) + distance - 1 for distance in distances]
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
        states = tuple(output.hidden_states[index + 1] for index in layer_indices)
        _require(len(states) == len(DEPTH_FRACTIONS), "Depth state count changed")
        selected = torch.stack(states, dim=2)
        position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
        captured = selected[0, position_tensor].float().cpu().numpy()
        _require(
            captured.shape == (4, len(DEPTH_FRACTIONS), width), "Captured shape changed"
        )
        _require(bool(np.isfinite(captured).all()), "Nonfinite activation")
        local_index = int(row["item_offset"])
        activations[local_index, int(row["view_index"]), int(row["carrier_index"])] = (
            captured
        )
        item = shard_items[local_index]
        observations.append(
            {
                "item_index": start + local_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_system": str(item["glyph_system"]),
                "view": str(row["view"]),
                "carrier": str(row["carrier"]),
                "raw_token_count": len(row["raw_ids"]),
                "input_token_count": len(ids),
                "readout_positions": positions,
                "forward_latency_ms": (time.perf_counter() - before) * 1000.0,
            }
        )
        del (
            output,
            states,
            selected,
            position_tensor,
            captured,
            input_ids,
            attention_mask,
        )
    _require(bool(np.isfinite(activations).all()), "Shard contains nonfinite values")
    np.save(stage / "activations.npy", activations, allow_pickle=False)
    _write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "fresh_composite_glyph_shard_complete",
        "model_role": role,
        "shard_index": shard_index,
        "item_index_start": start,
        "item_index_stop_exclusive": stop,
        "item_count": len(shard_items),
        "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        "activation_shape": list(activations.shape),
        "activation_dtype": str(activations.dtype),
        "axis_order": config["acquisition"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": list(config["input"]["carrier_order"]),
        "distance_order": distances,
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "resolved_block_indices": list(layer_indices),
        "model_forward_calls": len(records),
        "readout_vectors": int(np.prod(activations.shape[:-1])),
        "elapsed_seconds": time.perf_counter() - started,
        "peak_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "model": dict(model_receipt),
        "runtime_t18_token_sequences_match_frozen_preflight": True,
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "outputs": {
            "execution_intent.json": _sha256(stage / "execution_intent.json"),
            "activations.npy": _sha256(stage / "activations.npy"),
            "observations.jsonl": _sha256(stage / "observations.jsonl"),
        },
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(stage / "receipt.json", receipt)
    _write_ledger(
        stage,
        (
            "execution_intent.json",
            "activations.npy",
            "observations.jsonl",
            "receipt.json",
        ),
    )
    os.replace(stage, final)
    return validate_shard(role, shard_index, output_root)


def validate_shard(role: str, shard_index: int, output_root: Path) -> dict[str, Any]:
    directory = output_root / role / f"shard_{shard_index:04d}"
    for name in (
        "execution_intent.json",
        "activations.npy",
        "observations.jsonl",
        "receipt.json",
        "SHA256SUMS",
    ):
        _require(
            (directory / name).is_file(),
            f"Shard file missing: {role}/{shard_index}/{name}",
        )
    receipt = _read_json(directory / "receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Shard protocol mismatch")
    _require(receipt.get("model_role") == role, "Shard role mismatch")
    _require(int(receipt.get("shard_index", -1)) == shard_index, "Shard index mismatch")
    _require(
        receipt.get("runtime_t18_token_sequences_match_frozen_preflight") is True,
        "Runtime tokenizer was not admitted",
    )
    for name, expected in receipt["outputs"].items():
        _require(
            _sha256(directory / name) == expected,
            f"Shard output changed: {role}/{shard_index}/{name}",
        )
    size = int(_config()["acquisition"]["item_shard_size"])
    expected_items = items()[shard_index * size : (shard_index + 1) * size]
    width = int(t10._model_spec(role)["expected_model_dim"])
    expected_shape = (
        len(expected_items),
        len(VIEW_ORDER),
        2,
        4,
        len(DEPTH_FRACTIONS),
        width,
    )
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    _require(
        array.shape == expected_shape and array.dtype == np.float32,
        "Shard array contract mismatch",
    )
    _require(
        receipt["item_codepoints"] == [str(row["codepoint"]) for row in expected_items],
        "Shard population changed",
    )
    expected_forwards = len(expected_items) * len(VIEW_ORDER) * 2
    _require(
        int(receipt["model_forward_calls"]) == expected_forwards,
        "Shard forward count changed",
    )
    return {
        "status": "pass",
        "model_role": role,
        "shard_index": shard_index,
        "items": len(expected_items),
        "forwards": expected_forwards,
        "vectors": int(receipt["readout_vectors"]),
    }


def _finalize_role(role: str, output_root: Path) -> dict[str, Any]:
    role_root = output_root / role
    path = role_root / "role_receipt.json"
    if path.exists():
        return validate_role(role, output_root)
    shards = [
        validate_shard(role, index, output_root) for index in range(_shard_count())
    ]
    receipts = [
        _read_json(role_root / f"shard_{index:04d}" / "receipt.json")
        for index in range(_shard_count())
    ]
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "fresh_composite_glyph_role_complete",
        "model_role": role,
        "items": sum(row["items"] for row in shards),
        "shards": len(shards),
        "model_forward_calls": sum(row["forwards"] for row in shards),
        "readout_vectors": sum(row["vectors"] for row in shards),
        "elapsed_seconds": sum(float(row["elapsed_seconds"]) for row in receipts),
        "peak_cuda_memory_bytes": max(
            int(row["peak_cuda_memory_bytes"]) for row in receipts
        ),
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_t18_token_sequences_match_frozen_preflight": True,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(path, value)
    _write_ledger(role_root, ("role_receipt.json",))
    return validate_role(role, output_root)


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    role_root = output_root / role
    _require(
        not list(role_root.glob(".shard_*.stage-*")),
        f"Incomplete shard stage blocks role: {role}",
    )
    shards = [
        validate_shard(role, index, output_root) for index in range(_shard_count())
    ]
    receipt = _read_json(role_root / "role_receipt.json")
    _require(
        receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("model_role") == role,
        "Role receipt mismatch",
    )
    _require(int(receipt["items"]) == len(items()), "Role item count changed")
    _require(
        int(receipt["model_forward_calls"]) == sum(row["forwards"] for row in shards),
        "Role forward count changed",
    )
    return {
        "status": "pass",
        "model_role": role,
        "items": int(receipt["items"]),
        "shards": len(shards),
        "model_forward_calls": int(receipt["model_forward_calls"]),
        "readout_vectors": int(receipt["readout_vectors"]),
        "elapsed_seconds": float(receipt["elapsed_seconds"]),
        "peak_cuda_memory_bytes": int(receipt["peak_cuda_memory_bytes"]),
    }


def run_role(role: str, model_path: Path, output_root: Path) -> dict[str, Any]:
    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    audit_freeze(require_pushed=True)
    role_root = output_root / role
    if (role_root / "role_receipt.json").exists():
        return validate_role(role, output_root)
    _yield_if_contended(output_root, role, "before_model_load")
    t10._validate_runtime(t10._config())
    torch, tokenizer, model, _last_block, model_receipt, _t10_roster = t10._load_model(
        role, model_path
    )
    try:
        roster = _tokenize_roster(tokenizer)
        frozen = _read_json(_tokenizer_receipt_path(role))["tokenizer"]
        _require(
            roster["receipt"]["ordered_sequence_sha256"]
            == frozen["ordered_sequence_sha256"],
            "Exact frozen-model tokenizer differs from T18 candidate preflight",
        )
        for shard_index in range(_shard_count()):
            _capture_shard(
                role=role,
                shard_index=shard_index,
                output_root=output_root,
                torch=torch,
                model=model,
                model_receipt=model_receipt,
                roster=roster,
            )
    finally:
        del model
        torch.cuda.empty_cache()
    return _finalize_role(role, output_root)


def audit_run(output_root: Path) -> dict[str, Any]:
    roles = [validate_role(role, output_root) for role in MODEL_ROLES]
    return {
        "status": "all_nine_roles_complete",
        "protocol_id": PROTOCOL_ID,
        "roles_complete": len(roles),
        "items_per_role": sorted({row["items"] for row in roles}),
        "shards_complete": sum(row["shards"] for row in roles),
        "model_forward_calls": sum(row["model_forward_calls"] for row in roles),
        "readout_vectors": sum(row["readout_vectors"] for row in roles),
        "elapsed_seconds": sum(row["elapsed_seconds"] for row in roles),
        "maximum_peak_cuda_memory_bytes": max(
            row["peak_cuda_memory_bytes"] for row in roles
        ),
        "intervention_calls": 0,
        "generation_calls": 0,
    }


def _normalized_view(value: np.ndarray) -> np.ndarray:
    centered = np.asarray(value, dtype=np.float64) - np.mean(
        value, axis=0, keepdims=True, dtype=np.float64
    )
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    _require(bool(np.all(norms > 0.0)), "Zero centered row norm")
    return centered / norms


def _pair_metrics(
    first: np.ndarray, second: np.ndarray
) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    left = _normalized_view(first)
    right = _normalized_view(second)
    similarities = left @ right.T
    count = similarities.shape[0]
    order = np.arange(count)
    diagonal = similarities[order, order]
    forward = np.argmax(similarities, axis=1)
    reverse = np.argmax(similarities, axis=0)
    rank_forward = 1 + np.sum(similarities > diagonal[:, None], axis=1)
    rank_reverse = 1 + np.sum(similarities > diagonal[None, :], axis=0)
    off_diagonal = (float(np.sum(similarities)) - float(np.sum(diagonal))) / (
        count * (count - 1)
    )
    left_gram = left @ left.T
    right_gram = right @ right.T
    denominator = math.sqrt(
        float(np.sum(left_gram * left_gram)) * float(np.sum(right_gram * right_gram))
    )
    _require(denominator > 0.0, "CKA denominator is zero")
    metrics = {
        "paired_cosine_mean": float(np.mean(diagonal)),
        "off_diagonal_cosine_mean": off_diagonal,
        "paired_minus_off_diagonal_margin": float(np.mean(diagonal)) - off_diagonal,
        "top1_accuracy_forward": float(np.mean(forward == order)),
        "top1_accuracy_reverse": float(np.mean(reverse == order)),
        "mean_reciprocal_rank_forward": float(np.mean(1.0 / rank_forward)),
        "mean_reciprocal_rank_reverse": float(np.mean(1.0 / rank_reverse)),
        "centered_linear_cka": float(np.sum(left_gram * right_gram) / denominator),
    }
    return metrics, forward.astype(np.int64), reverse.astype(np.int64)


def _metrics_for_views(
    values: np.ndarray,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    result: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    for name, left, right in PAIR_ORDER:
        metrics, forward, reverse = _pair_metrics(values[:, left], values[:, right])
        result[name] = metrics
        predictions[f"{name}_forward"] = forward
        predictions[f"{name}_reverse"] = reverse
    result["english_minus_codepoint"] = {
        key: float(result["glyph_english"][key] - result["glyph_codepoint"][key])
        for key in result["glyph_english"]
    }
    result["japanese_minus_codepoint"] = {
        key: float(result["glyph_japanese"][key] - result["glyph_codepoint"][key])
        for key in result["glyph_japanese"]
    }
    return result, predictions


def _load_role_array(role: str, output_root: Path) -> np.ndarray:
    arrays = [
        np.load(
            output_root / role / f"shard_{index:04d}" / "activations.npy",
            mmap_mode="r",
            allow_pickle=False,
        )
        for index in range(_shard_count())
    ]
    result = np.concatenate(arrays, axis=0)
    _require(result.shape[0] == len(items()), f"Role array item count changed: {role}")
    return result


def summarize_role(role: str, output_root: Path, summary_root: Path) -> dict[str, Any]:
    validate_role(role, output_root)
    final = summary_root / role
    _require(not final.exists(), f"Summary exists: {final}")
    stage = summary_root / f".{role}.stage-{uuid.uuid4().hex}"
    stage.mkdir(parents=True)
    values = _load_role_array(role, output_root)
    population = items()
    token_receipt = _read_json(_tokenizer_receipt_path(role))["tokenizer"]
    indices_by_system = {
        system: np.asarray(
            [
                index
                for index, item in enumerate(population)
                if item["glyph_system"] == system
            ],
            dtype=np.int64,
        )
        for system in SYSTEM_ORDER
    }
    primary_eligible = {
        system: np.asarray(
            token_receipt["primary_exact_strata"]["eligible_global_indices_by_system"][
                system
            ],
            dtype=np.int64,
        )
        for system in SYSTEM_ORDER
    }
    japanese_eligible = {
        system: np.asarray(
            token_receipt["japanese_secondary_exact_strata"][
                "eligible_global_indices_by_system"
            ][system],
            dtype=np.int64,
        )
        for system in SYSTEM_ORDER
    }
    cell_rows: list[dict[str, Any]] = []
    prediction_lists: dict[str, list[np.ndarray]] = defaultdict(list)
    context_index = 0
    started = time.perf_counter()
    for depth_index, depth in enumerate(DEPTH_FRACTIONS):
        for carrier_index, carrier in enumerate(_config()["input"]["carrier_order"]):
            for distance_index, distance in enumerate(
                _config()["input"]["distance_order"]
            ):
                for system in SYSTEM_ORDER:
                    global_indices = indices_by_system[system]
                    cell_values = np.asarray(
                        values[
                            global_indices,
                            :,
                            carrier_index,
                            distance_index,
                            depth_index,
                            :,
                        ]
                    )
                    unrestricted, predictions = _metrics_for_views(cell_values)
                    matched_indices = primary_eligible[system]
                    matched_values = np.asarray(
                        values[
                            matched_indices,
                            :,
                            carrier_index,
                            distance_index,
                            depth_index,
                            :,
                        ]
                    )
                    matched, matched_predictions = _metrics_for_views(matched_values)
                    japanese_indices = japanese_eligible[system]
                    japanese_values = np.asarray(
                        values[
                            japanese_indices,
                            :,
                            carrier_index,
                            distance_index,
                            depth_index,
                            :,
                        ]
                    )
                    japanese_matched, _ = _metrics_for_views(japanese_values)
                    cell_rows.append(
                        {
                            "model_role": role,
                            "normalized_depth": depth,
                            "resolved_block_index": resolved_layers(role)[depth_index],
                            "carrier": str(carrier),
                            "distance": int(distance),
                            "glyph_system": system,
                            "unrestricted_item_count": int(len(global_indices)),
                            "primary_matched_item_count": int(len(matched_indices)),
                            "japanese_secondary_matched_item_count": int(
                                len(japanese_indices)
                            ),
                            "unrestricted": unrestricted,
                            "primary_tokenization_matched": matched,
                            "japanese_secondary_tokenization_matched": japanese_matched,
                        }
                    )
                    if depth_index in PRIMARY_DEPTH_INDICES:
                        _require(context_index < 24, "Primary context index overflow")
                        prediction_lists[f"unrestricted__{system}__english"].append(
                            predictions["glyph_english_forward"]
                        )
                        prediction_lists[f"unrestricted__{system}__codepoint"].append(
                            predictions["glyph_codepoint_forward"]
                        )
                        prediction_lists[f"matched__{system}__english"].append(
                            matched_predictions["glyph_english_forward"]
                        )
                        prediction_lists[f"matched__{system}__codepoint"].append(
                            matched_predictions["glyph_codepoint_forward"]
                        )
                if depth_index in PRIMARY_DEPTH_INDICES:
                    context_index += 1
    _require(context_index == 24, "Primary context roster changed")
    predictions_np = {key: np.stack(rows) for key, rows in prediction_lists.items()}
    for component in ("unrestricted", "matched"):
        for system in SYSTEM_ORDER:
            expected = (
                len(indices_by_system[system])
                if component == "unrestricted"
                else len(primary_eligible[system])
            )
            for target in ("english", "codepoint"):
                _require(
                    predictions_np[f"{component}__{system}__{target}"].shape
                    == (24, expected),
                    f"Prediction shape changed: {component}/{system}/{target}",
                )
    np.savez_compressed(stage / "primary_predictions.npz", **predictions_np)
    _write_jsonl(stage / "cell_metrics.jsonl", cell_rows)
    run_receipt = _read_json(output_root / role / "role_receipt.json")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "fresh_composite_glyph_summary_complete",
        "model_role": role,
        "item_count": len(population),
        "cell_metric_rows": len(cell_rows),
        "primary_context_count": context_index,
        "primary_depth_fractions": list(PRIMARY_DEPTHS),
        "system_item_counts": {
            system: int(len(indices_by_system[system])) for system in SYSTEM_ORDER
        },
        "primary_matched_item_counts": {
            system: int(len(primary_eligible[system])) for system in SYSTEM_ORDER
        },
        "japanese_secondary_matched_item_counts": {
            system: int(len(japanese_eligible[system])) for system in SYSTEM_ORDER
        },
        "input_role_receipt_sha256": _sha256(output_root / role / "role_receipt.json"),
        "input_model_forward_calls": int(run_receipt["model_forward_calls"]),
        "elapsed_seconds": time.perf_counter() - started,
        "outputs": {
            "primary_predictions.npz": _sha256(stage / "primary_predictions.npz"),
            "cell_metrics.jsonl": _sha256(stage / "cell_metrics.jsonl"),
        },
        "analysis_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(stage / "summary_receipt.json", receipt)
    _write_ledger(
        stage, ("primary_predictions.npz", "cell_metrics.jsonl", "summary_receipt.json")
    )
    os.replace(stage, final)
    return validate_summary(role, summary_root)


def validate_summary(role: str, summary_root: Path) -> dict[str, Any]:
    directory = summary_root / role
    for name in (
        "primary_predictions.npz",
        "cell_metrics.jsonl",
        "summary_receipt.json",
        "SHA256SUMS",
    ):
        _require((directory / name).is_file(), f"Summary file missing: {role}/{name}")
    receipt = _read_json(directory / "summary_receipt.json")
    _require(
        receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("model_role") == role,
        "Summary receipt mismatch",
    )
    for name, expected in receipt["outputs"].items():
        _require(
            _sha256(directory / name) == expected,
            f"Summary output changed: {role}/{name}",
        )
    with np.load(directory / "primary_predictions.npz", allow_pickle=False) as stored:
        for component in ("unrestricted", "matched"):
            for system in SYSTEM_ORDER:
                count = int(
                    receipt["system_item_counts"][system]
                    if component == "unrestricted"
                    else receipt["primary_matched_item_counts"][system]
                )
                for target in ("english", "codepoint"):
                    _require(
                        stored[f"{component}__{system}__{target}"].shape == (24, count),
                        "Summary prediction shape changed",
                    )
    return {"status": "pass", "model_role": role, "receipt": receipt}


def _stratified_permutation(
    rng: np.random.Generator, item_count: int, strata: Sequence[Sequence[int]]
) -> np.ndarray:
    order = np.arange(item_count, dtype=np.int64)
    flattened = sorted(int(value) for group in strata for value in group)
    _require(
        flattened == list(range(item_count)), "Matched strata do not partition items"
    )
    _require(all(len(group) >= 2 for group in strata), "Matched stratum is singleton")
    result = order.copy()
    for group in strata:
        indices = np.asarray(group, dtype=np.int64)
        result[indices] = rng.permutation(indices)
    return result


def _component_statistic(
    predictions: Mapping[str, np.ndarray], component: str
) -> tuple[float, dict[str, Any], dict[str, np.ndarray]]:
    system_rows: dict[str, Any] = {}
    effects: dict[str, np.ndarray] = {}
    for system in SYSTEM_ORDER:
        name = predictions[f"{component}__{system}__english"]
        codepoint = predictions[f"{component}__{system}__codepoint"]
        order = np.arange(name.shape[1], dtype=np.int64)
        name_correct = name == order[None, :]
        codepoint_correct = codepoint == order[None, :]
        effect = np.mean(name_correct.astype(np.float64) - codepoint_correct, axis=0)
        effects[system] = effect
        system_rows[system] = {
            "item_count": int(name.shape[1]),
            "context_count": int(name.shape[0]),
            "english_top1_equal_context_mean": float(np.mean(name_correct)),
            "codepoint_top1_equal_context_mean": float(np.mean(codepoint_correct)),
            "contrast_equal_context_mean": float(np.mean(effect)),
        }
    observed = float(
        np.mean([row["contrast_equal_context_mean"] for row in system_rows.values()])
    )
    return observed, system_rows, effects


def _bootstrap_effects(
    effects: Mapping[str, np.ndarray], *, replicates: int, seed: int
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    values = np.empty(replicates, dtype=np.float64)
    for draw in range(replicates):
        system_values = []
        for system in SYSTEM_ORDER:
            row = effects[system]
            sample = rng.integers(0, len(row), size=len(row))
            system_values.append(float(np.mean(row[sample])))
        values[draw] = float(np.mean(system_values))
    return {
        "method": "independent_within_system_item_bootstrap_on_fixed_top1_predictions",
        "replicates": replicates,
        "seed": seed,
        "percentile_95_interval": [
            float(np.quantile(values, 0.025)),
            float(np.quantile(values, 0.975)),
        ],
    }


def randomization_test(
    predictions: Mapping[str, np.ndarray],
    *,
    component: str,
    strata_by_system: Mapping[str, Sequence[Sequence[int]]] | None,
    draws: int,
    seed: int,
    practical_minimum: float,
) -> dict[str, Any]:
    observed, system_rows, effects = _component_statistic(predictions, component)
    uncertainty = _config()["model_primary_endpoint"]["descriptive_uncertainty"]
    rng = np.random.default_rng(seed)
    null_values = np.empty(draws, dtype=np.float64)
    exceedances = 0
    for draw in range(draws):
        system_statistics: list[float] = []
        for system in SYSTEM_ORDER:
            name = predictions[f"{component}__{system}__english"]
            codepoint = predictions[f"{component}__{system}__codepoint"]
            item_count = int(name.shape[1])
            if strata_by_system is None:
                permutation = rng.permutation(item_count)
            else:
                permutation = _stratified_permutation(
                    rng, item_count, strata_by_system[system]
                )
            permuted_name = float(np.mean(name == permutation[None, :]))
            order = np.arange(item_count, dtype=np.int64)
            codepoint_top1 = float(np.mean(codepoint == order[None, :]))
            system_statistics.append(permuted_name - codepoint_top1)
        statistic = float(np.mean(system_statistics))
        null_values[draw] = statistic
        exceedances += int(statistic >= observed)
    return {
        "component": component,
        "system_order": list(SYSTEM_ORDER),
        "context_count_per_system": 24,
        "observed_equal_system_equal_context_contrast": observed,
        "system_results": system_rows,
        "practical_minimum": practical_minimum,
        "practical_pass": bool(observed >= practical_minimum),
        "randomization_draws": draws,
        "randomization_seed": seed,
        "exceedances": exceedances,
        "p_value": float((1 + exceedances) / (draws + 1)),
        "null_statistic_quantiles": {
            str(q): float(np.quantile(null_values, q))
            for q in (0.0, 0.5, 0.95, 0.99, 1.0)
        },
        "descriptive_item_bootstrap": _bootstrap_effects(
            effects,
            replicates=int(uncertainty["replicates"]),
            seed=seed + 1000,
        ),
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def _depth_profiles(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for depth in DEPTH_FRACTIONS:
        selected = [row for row in rows if float(row["normalized_depth"]) == depth]
        _require(
            len(selected) == len(SYSTEM_ORDER) * 2 * 4, "Depth cell roster changed"
        )
        profile: dict[str, Any] = {
            "normalized_depth": depth,
            "cell_count": len(selected),
        }
        for component, key in (
            ("unrestricted", "unrestricted"),
            ("primary_tokenization_matched", "primary_tokenization_matched"),
        ):
            profile[component] = {}
            for language, pair in (
                ("english", "glyph_english"),
                ("japanese", "glyph_japanese"),
            ):
                contrasts = [
                    float(row[key][pair]["top1_accuracy_forward"])
                    - float(row[key]["glyph_codepoint"]["top1_accuracy_forward"])
                    for row in selected
                ]
                profile[component][
                    f"{language}_minus_codepoint_top1_equal_cell_mean"
                ] = float(np.mean(contrasts))
                profile[component][f"{language}_minus_codepoint_top1_minimum_cell"] = (
                    float(np.min(contrasts))
                )
        result.append(profile)
    return result


def analyze_summaries(summary_root: Path, output: Path) -> dict[str, Any]:
    audit_freeze()
    config = _config()
    endpoint = config["model_primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    floor = float(endpoint["practical_minimum"])
    seed_base = int(endpoint["seed_base"])
    model_results: dict[str, Any] = {}
    depth_profiles: dict[str, Any] = {}
    summary_hashes: dict[str, str] = {}
    for role_index, role in enumerate(MODEL_ROLES):
        validated = validate_summary(role, summary_root)
        summary_hashes[role] = _sha256(summary_root / role / "summary_receipt.json")
        with np.load(
            summary_root / role / "primary_predictions.npz", allow_pickle=False
        ) as stored:
            predictions = {key: np.asarray(stored[key]) for key in stored.files}
        token = _read_json(_tokenizer_receipt_path(role))["tokenizer"]
        strata = token["primary_exact_strata"]["eligible_local_strata_by_system"]
        unrestricted = randomization_test(
            predictions,
            component="unrestricted",
            strata_by_system=None,
            draws=draws,
            seed=seed_base + role_index * 10 + 1,
            practical_minimum=floor,
        )
        matched = randomization_test(
            predictions,
            component="matched",
            strata_by_system=strata,
            draws=draws,
            seed=seed_base + role_index * 10 + 2,
            practical_minimum=floor,
        )
        iut_p = max(float(unrestricted["p_value"]), float(matched["p_value"]))
        practical = bool(unrestricted["practical_pass"] and matched["practical_pass"])
        model_results[role] = {
            "model_role": role,
            "selection_role": t10._model_spec(role)["selection_role"],
            "unrestricted_component": unrestricted,
            "tokenization_matched_component": matched,
            "intersection_union_p_value": iut_p,
            "practical_pass": practical,
            "raw_model_cell_pass": bool(
                iut_p <= float(endpoint["alpha"]) and practical
            ),
            "summary_receipt_sha256": summary_hashes[role],
            "primary_matched_items_by_system": validated["receipt"][
                "primary_matched_item_counts"
            ],
        }
        rows = _read_jsonl(summary_root / role / "cell_metrics.jsonl")
        depth_profiles[role] = _depth_profiles(rows)

    raw_iut = {
        role: float(model_results[role]["intersection_union_p_value"])
        for role in MODEL_ROLES
    }
    holm = t10.holm_adjust(
        raw_iut, float(config["bounded_model_cell_family"]["familywise_alpha"])
    )
    for role in MODEL_ROLES:
        model_results[role]["holm_adjusted_p"] = holm[role]["adjusted_p"]
        model_results[role]["holm_reject"] = holm[role]["reject"]
        model_results[role]["bounded_model_cell_claim_pass"] = bool(
            holm[role]["reject"] and model_results[role]["practical_pass"]
        )
    partial = t10.partial_conjunction(
        {role: raw_iut[role] for role in CORE_ROLES},
        int(config["cross_model_primary"]["r"]),
    )
    core_practical_count = sum(
        int(model_results[role]["practical_pass"]) for role in CORE_ROLES
    )
    core_joint_pass_count = sum(
        int(model_results[role]["raw_model_cell_pass"]) for role in CORE_ROLES
    )
    statistical_pass = bool(
        partial["p_value"] <= float(config["cross_model_primary"]["alpha"])
    )
    practical_pass = bool(
        core_joint_pass_count >= int(config["cross_model_primary"]["r"])
    )
    positive = bool(statistical_pass and practical_pass)
    outcome_pattern = (
        "fresh_exact_surfaces_confirmed_in_at_least_three_of_four_core_cells"
        if positive
        else "fresh_exact_surface_cross_model_confirmation_not_established"
    )
    cross_primary = {
        **partial,
        "core_order": list(CORE_ROLES),
        "core_practical_pass_count": core_practical_count,
        "core_joint_statistical_and_practical_pass_count": core_joint_pass_count,
        "statistical_pass": statistical_pass,
        "practical_pass": practical_pass,
        "positive": positive,
        "outcome_pattern": outcome_pattern,
        "authorized_wording": (
            config["cross_model_primary"]["authorized_positive_wording"]
            if positive
            else "fresh_exact_surface_cross_model_confirmation_not_established_under_frozen_rule"
        ),
        "independence_claim_authorized": False,
    }
    stage = output.parent / f".{output.name}.stage-{uuid.uuid4().hex}"
    _require(not output.exists(), f"Analysis output exists: {output}")
    stage.mkdir(parents=True)
    _write_json(stage / "cross_model_primary_result.json", cross_primary)
    _write_json(stage / "model_cell_results.json", model_results)
    _write_json(stage / "depth_profiles.json", depth_profiles)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": "prospectively_frozen_exact_surface_fresh_confirmation",
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "input_summary_receipt_sha256": summary_hashes,
        "model_order": list(MODEL_ROLES),
        "core_order": list(CORE_ROLES),
        "cross_model_primary": cross_primary,
        "holm_family_size": len(MODEL_ROLES),
        "randomization_draws_per_model_component": draws,
        "outcome_pattern": outcome_pattern,
        "analysis_model_forward_calls": 0,
        "total_acquisition_model_forward_calls": int(
            config["acquisition"]["expected_total_model_forward_calls"]
        ),
        "intervention_calls": 0,
        "generation_calls": 0,
        "rendered_glyph_claim_authorized": False,
        "pretraining_or_semantic_holdout_claim_authorized": False,
        "causal_claim_authorized": False,
        "behavioral_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "model_general_claim_authorized": False,
        "independent_replication_claim_authorized": False,
    }
    _write_json(stage / "analysis_receipt.json", receipt)
    lines = [
        "# Fresh composite-glyph lexical confirmation v0 result\n\n",
        f"Outcome: `{outcome_pattern}`.\n\n",
        "| Model cell | Unrestricted estimate | Matched estimate | Unrestricted p | Matched p | IUT p | Holm p | Practical |\n",
        "|---|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for role in MODEL_ROLES:
        row = model_results[role]
        lines.append(
            f"| `{role}` | {row['unrestricted_component']['observed_equal_system_equal_context_contrast']:.6f} | "
            f"{row['tokenization_matched_component']['observed_equal_system_equal_context_contrast']:.6f} | "
            f"{row['unrestricted_component']['p_value']:.7f} | {row['tokenization_matched_component']['p_value']:.7f} | "
            f"{row['intersection_union_p_value']:.7f} | {row['holm_adjusted_p']:.7f} | {str(row['practical_pass']).lower()} |\n"
        )
    lines.extend(
        [
            "\n",
            f"Core partial-conjunction p: `{partial['p_value']:.7f}`; practical-only core passes: `{core_practical_count}/4`; joint model-IUT-and-practical core passes: `{core_joint_pass_count}/4`.\n\n",
            "Freshness is relative to the frozen tracked repository tree and exact UTF-8 surfaces. It is not a pretraining or semantic-concept holdout. The result concerns text-codepoint sequence geometry, not rendered-glyph perception, causality, or behavior.\n",
        ]
    )
    (stage / "report.md").write_text("".join(lines), encoding="utf-8")
    _write_ledger(
        stage,
        (
            "cross_model_primary_result.json",
            "model_cell_results.json",
            "depth_profiles.json",
            "analysis_receipt.json",
            "report.md",
        ),
    )
    os.replace(stage, output)
    return receipt


def validate_analysis(directory: Path) -> dict[str, Any]:
    for name in (
        "cross_model_primary_result.json",
        "model_cell_results.json",
        "depth_profiles.json",
        "analysis_receipt.json",
        "report.md",
        "SHA256SUMS",
    ):
        _require((directory / name).is_file(), f"Analysis file missing: {name}")
    receipt = _read_json(directory / "analysis_receipt.json")
    _require(
        receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass",
        "Analysis receipt mismatch",
    )
    _require(
        tuple(receipt["model_order"]) == MODEL_ROLES, "Analysis model order changed"
    )
    _require(
        receipt.get("rendered_glyph_claim_authorized") is False,
        "Rendered-glyph claim was authorized",
    )
    _require(
        receipt.get("pretraining_or_semantic_holdout_claim_authorized") is False,
        "Semantic holdout claim was authorized",
    )
    _require(
        receipt.get("causal_claim_authorized") is False, "Causal claim was authorized"
    )
    return {
        "status": "pass",
        "outcome_pattern": receipt["outcome_pattern"],
        "cross_model_primary": receipt["cross_model_primary"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("build-selection")
    selection.add_argument("--emoji-test", type=Path, required=True)
    selection.add_argument("--cldr-directory", type=Path, required=True)
    selection.add_argument("--output", type=Path, default=_root() / SELECTION_PATH)
    sub.add_parser("audit-selection")
    design = sub.add_parser("design-preflight")
    design.add_argument("--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH)
    tokenizer = sub.add_parser("tokenizer-preflight")
    tokenizer.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    tokenizer.add_argument("--model-path", type=Path, required=True)
    tokenizer.add_argument("--output", type=Path, required=True)
    assemble = sub.add_parser("assemble-preflight")
    assemble.add_argument(
        "--output", type=Path, default=_root() / ENGINEERING_PREFLIGHT_PATH
    )
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    freeze_audit = sub.add_parser("audit-freeze")
    freeze_audit.add_argument("--require-pushed", action="store_true")
    run = sub.add_parser("run-role")
    run.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    validate_run_parser = sub.add_parser("validate-run")
    validate_run_parser.add_argument("--output-root", type=Path, required=True)
    summary = sub.add_parser("summarize-role")
    summary.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    summary.add_argument("--output-root", type=Path, required=True)
    summary.add_argument("--summary-root", type=Path, required=True)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--summary-root", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    validate_analysis_parser = sub.add_parser("validate-analysis")
    validate_analysis_parser.add_argument("--analysis", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "build-selection":
        value = build_selection(args.emoji_test, args.cldr_directory, args.output)
    elif args.command == "audit-selection":
        value = audit_selection()
    elif args.command == "design-preflight":
        value = audit_design(args.output)
    elif args.command == "tokenizer-preflight":
        value = tokenizer_preflight(args.model_label, args.model_path, args.output)
    elif args.command == "assemble-preflight":
        value = assemble_engineering_preflight(args.output)
    elif args.command == "build-freeze":
        value = build_freeze(args.output)
    elif args.command == "audit-freeze":
        value = audit_freeze(require_pushed=args.require_pushed)
    elif args.command == "run-role":
        value = run_role(args.model_label, args.model_path, args.output_root)
    elif args.command == "validate-run":
        value = audit_run(args.output_root)
    elif args.command == "summarize-role":
        value = summarize_role(args.model_label, args.output_root, args.summary_root)
    elif args.command == "analyze":
        value = analyze_summaries(args.summary_root, args.output)
    elif args.command == "validate-analysis":
        value = validate_analysis(args.analysis)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
