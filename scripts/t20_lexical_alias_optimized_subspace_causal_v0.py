#!/usr/bin/env python3
"""Conditional T20-C optimized-subspace causal lexical experiment.

T20-C follows the registered T19-C negative. It keeps the T19 acquisition
grammar (pinned model, receipt-bound stages, self-hashing executor) and
changes exactly five prespecified things: the tested subspace may be learned
by interchange optimization on the frozen 128-item source bank; three
residual-stream sites join the six component sites; the decision endpoint is
gated on the alias-retrieval component alone with a codepoint self-retrieval
guard; evaluation uses 384 fresh atomic emoji read in four contexts; and every
site carries a full-representation interchange ceiling as a positive control.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence
import uuid

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import emoji_steering_causal_path_v0 as causal_engine  # noqa: E402
import glyph_system_decomposition_v0 as t11  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402
import t19_lexical_alias_unicode_control_v0 as t19  # noqa: E402
import t19_lexical_alias_component_causal_v0 as t19c  # noqa: E402


PROTOCOL_ID = "glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0"
SCHEMA_VERSION = 1
ROLE = "llama32_3b_base_bf16"
CONFIG_PATH = Path("configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml")
SELECTION_PATH = Path("data/manifests/t20_lexical_alias_optimized_subspace_causal_v0.json")
FREEZE_PATH = Path("data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_freeze.json")
GO_MANIFEST_PATH = Path("data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_go.json")
VALIDATION_DIRECTORY = Path("validation/t20_lexical_alias_optimized_subspace_causal_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "tokenizer_preflight.json"
SITE_ORDER = (
    ("resid_out", 21),
    ("resid_out", 24),
    ("resid_out", 27),
    ("attn_out", 21),
    ("mlp_out", 21),
    ("attn_out", 24),
    ("mlp_out", 24),
    ("attn_out", 27),
    ("mlp_out", 27),
)
PRIMARY_SITES = (("resid_out", 21), ("resid_out", 24))
CONTEXT_ORDER = (("pipe", 1), ("pipe", 4), ("article_a", 1), ("article_a", 4))
TRAINING_CONTEXT = ("pipe", 1)
SOURCE_VIEWS = ("glyph", "alias_label", "codepoint_literal")
EVAL_VIEWS = ("glyph", "alias_label", "codepoint_literal")
GLYPH_CONDITION_ORDER = (
    "zero_hook",
    "necessity_optimized",
    "necessity_random",
    "necessity_svd",
    "restoration_optimized",
    "full_interchange_codepoint",
)
CODEPOINT_CONDITION_ORDER = (
    "zero_hook",
    "sufficiency_optimized",
    "sufficiency_random",
    "sufficiency_svd",
    "full_interchange_glyph",
)
RANDOM_SEED_BASE = 2026091000
TRAINING_SEED_BASE = 2026091300
SIGN_FLIP_SEED_BASE = (2026091100, 2026091101)
BOOTSTRAP_SEED_BASE = (2026091200, 2026091201)


class T20CausalError(RuntimeError):
    """Raised when the frozen T20-C protocol is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T20CausalError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T20 config protocol mismatch")
    return value


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


def _bank_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(list(rows), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _site_module(blocks: Sequence[Any], site: str, block_index: int) -> tuple[Any, bool]:
    if site == "resid_out":
        return blocks[block_index], False
    return causal_engine._site_module(blocks, site, block_index)


def _verify_bound_source(key: str) -> Path:
    binding = _config()["source_bindings"][key]
    path = _root() / str(binding["path"])
    if "sha256" in binding:
        _require(_sha256(path) == str(binding["sha256"]), f"Bound T19 source changed: {key}")
    return path


# --------------------------------------------------------------------------
# Selection: byte-identical T19 reproduction audit plus a fresh 384 bank.
# --------------------------------------------------------------------------


def _rebuild_t19_matched_emoji(source_directory: Path) -> list[dict[str, Any]]:
    """Reproduce the T19 emoji candidate set and alias matching verbatim.

    This mirrors the frozen T19 builder exactly (same helper functions, same
    namespace hashes) so the fresh bank is drawn from the same deterministic
    matching that produced the frozen banks.
    """

    config = t19._config()
    sources = config["source_bindings"]
    emoji_raw = t19._verify_source(source_directory / t19.SOURCE_FILENAMES["unicode_emoji_test"], sources["unicode_emoji_test"])
    unicode_raw = t19._verify_source(source_directory / t19.SOURCE_FILENAMES["unicode_data"], sources["unicode_data"])
    emoji_data_raw = t19._verify_source(source_directory / t19.SOURCE_FILENAMES["emoji_data"], sources["emoji_data"])
    parsed = t11._parse_unicode_source(emoji_raw)
    annotations = t19._cldr_annotations(source_directory)
    unicode_data = t19._unicode_data(unicode_raw)
    emoji_property = t19._emoji_property(emoji_data_raw)
    _texts, text_characters = t19._text_exposure(str(sources["exposure_tree"]["commit"]))

    maximum_version = tuple(int(part) for part in str(config["population"]["maximum_emoji_version"]).split("."))
    emoji_candidates: list[dict[str, Any]] = []
    for source_index, source_row in enumerate(parsed["fully_qualified"]):
        codepoints = tuple(int(value) for value in source_row["codepoints"])
        if len(codepoints) != 1:
            continue
        if tuple(int(part) for part in str(source_row["emoji_version"]).split(".")) > maximum_version:
            continue
        glyph = chr(codepoints[0])
        annotation = annotations.get(glyph) or annotations.get(glyph + "\ufe0f")
        if annotation is None or not annotation.get("tts"):
            continue
        canonical = str(annotation["tts"][0])
        aliases = t19._strict_aliases(canonical, annotation.get("default", []))
        if not aliases:
            continue
        emoji_candidates.append(
            {
                "kind": "emoji",
                "glyph_system": "emoji",
                "glyph": glyph,
                "codepoint": f"{codepoints[0]:04X}",
                "codepoints": [f"U+{codepoints[0]:04X}"],
                "codepoint_literal": f"U+{codepoints[0]:04X}",
                "canonical_label": canonical,
                "alias_candidates": aliases,
                "semantic_stratum": str(source_row["group"]),
                "subgroup": str(source_row["subgroup"]),
                "emoji_version": str(source_row["emoji_version"]),
                "source_index": source_index,
                "prior_repository_text_surface_exposed": glyph in text_characters,
            }
        )

    symbol_candidates: list[dict[str, Any]] = []
    for glyph, annotation in annotations.items():
        if len(glyph) != 1:
            continue
        codepoint = ord(glyph)
        info = unicode_data.get(codepoint)
        if info is None or not info[1].startswith("S"):
            continue
        if codepoint in emoji_property:
            continue
        if glyph in text_characters:
            continue
        if not annotation.get("tts"):
            continue
        canonical = str(annotation["tts"][0])
        aliases = t19._strict_aliases(canonical, annotation.get("default", []))
        if not aliases:
            continue
        symbol_candidates.append(
            {
                "kind": "symbol",
                "codepoint": f"{codepoint:04X}",
                "canonical_label": canonical,
                "alias_candidates": aliases,
                "source_index": codepoint,
            }
        )

    matched_symbols = t19._maximum_alias_matching(symbol_candidates)
    symbol_aliases = {str(row["alias_label"]) for row in matched_symbols}
    matched_emoji = t19._maximum_alias_matching(emoji_candidates, forbidden_aliases=symbol_aliases)
    census = t19._selection_manifest()["candidate_census"]
    _require(len(emoji_candidates) == int(census["emoji_before_matching"]), "Emoji candidate census changed")
    _require(len(matched_emoji) == int(census["emoji_after_symbol_reserved_alias_matching"]), "Emoji matching census changed")
    return matched_emoji


def build_selection(source_directory: Path, output: Path) -> dict[str, Any]:
    config = _config()
    for key in ("t19_config", "t19_selection", "t19_freeze"):
        _verify_bound_source(key)

    with tempfile.TemporaryDirectory(prefix="t20-selection-audit-") as scratch:
        reproduction = Path(scratch) / "t19_reproduction.json"
        t19.build_selection(source_directory, reproduction)
        reproduced = _sha256(reproduction)
    frozen = str(config["source_bindings"]["t19_selection"]["sha256"])
    _require(reproduced == frozen, f"T19 selection reproduction diverged: {reproduced} != {frozen}")

    matched_emoji = _rebuild_t19_matched_emoji(source_directory)
    t19_manifest = t19._selection_manifest()
    used_rows = [
        *[row for row in t19_manifest["observational_items"] if row["kind"] == "emoji"],
        *t19_manifest["causal_source_items"],
        *t19_manifest["causal_eval_items"],
    ]
    used_alias = {str(row["codepoint"]): str(row["alias_label"]) for row in used_rows}
    matched_by_codepoint = {str(row["codepoint"]): str(row["alias_label"]) for row in matched_emoji}
    for codepoint, alias in used_alias.items():
        _require(matched_by_codepoint.get(codepoint) == alias, f"Reproduced matching diverged at {codepoint}")

    unused = [row for row in matched_emoji if str(row["codepoint"]) not in used_alias]
    count = int(config["population"]["fresh_eval_emoji_items"])
    _require(len(unused) >= count, f"Fresh pool too small: {len(unused)} < {count}")
    fresh = t19._round_robin(unused, count=count, role=str(config["population"]["fresh_eval_role"]))
    for index, row in enumerate(fresh):
        row["bank_index"] = index
        row["bank_role"] = "t20_causal_fresh_eval"

    t19_aliases = {str(row["alias_label"]) for kind in ("observational_items", "causal_source_items", "causal_eval_items") for row in t19_manifest[kind]}
    t19_codepoints = {str(row["codepoint"]) for kind in ("observational_items", "causal_source_items", "causal_eval_items") for row in t19_manifest[kind]}
    fresh_aliases = [str(row["alias_label"]) for row in fresh]
    fresh_codepoints = [str(row["codepoint"]) for row in fresh]
    _require(len(set(fresh_aliases)) == count, "Fresh aliases are not unique")
    _require(len(set(fresh_codepoints)) == count, "Fresh codepoints are not unique")
    _require(not set(fresh_aliases).intersection(t19_aliases), "Fresh aliases overlap a T19 bank")
    _require(not set(fresh_codepoints).intersection(t19_codepoints), "Fresh codepoints overlap a T19 bank")
    for row in fresh:
        _require(t19._words(str(row["canonical_label"])).isdisjoint(t19._words(str(row["alias_label"]))), "Fresh alias disjointness violated")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "fresh_bank_selected_zero_t20_model_forwards_or_interventions",
        "t19_selection_sha256": frozen,
        "t19_selection_reproduction_sha256": reproduced,
        "matched_emoji_total": len(matched_emoji),
        "t19_used_emoji": len(used_alias),
        "unused_matched_emoji": len(unused),
        "fresh_eval_items": fresh,
        "fresh_eval_stratum_histogram": dict(sorted(Counter(str(row["semantic_stratum"]) for row in fresh).items())),
        "counts": {"fresh_eval": len(fresh)},
        "source_bank_rule": "reuse_frozen_t19_causal_source_items_verbatim",
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"T20 selection exists: {output}")
    _write_json(output, manifest)
    return {
        "status": "pass",
        "fresh_eval_items": len(fresh),
        "unused_matched_emoji": len(unused),
        "selection_sha256": _sha256(output),
        "t19_reproduction_byte_identical": True,
        "model_forward_calls": 0,
    }


def _selection_manifest() -> dict[str, Any]:
    value = _read_json(_root() / SELECTION_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T20 selection protocol mismatch")
    _require(value.get("status") == "fresh_bank_selected_zero_t20_model_forwards_or_interventions", "T20 selection status changed")
    return value


def fresh_items() -> list[dict[str, Any]]:
    rows = [dict(row) for row in _selection_manifest()["fresh_eval_items"]]
    rows.sort(key=lambda row: int(row["bank_index"]))
    return rows


def source_items() -> list[dict[str, Any]]:
    return t19.causal_items("source")


def audit_selection() -> dict[str, Any]:
    manifest = _selection_manifest()
    fresh = fresh_items()
    count = int(_config()["population"]["fresh_eval_emoji_items"])
    _require(len(fresh) == count, "Fresh bank count changed")
    _require(manifest["t19_selection_sha256"] == str(_config()["source_bindings"]["t19_selection"]["sha256"]), "Fresh bank binds a different T19 selection")
    t19_manifest = t19._selection_manifest()
    t19_codepoints = {str(row["codepoint"]) for kind in ("observational_items", "causal_source_items", "causal_eval_items") for row in t19_manifest[kind]}
    t19_aliases = {str(row["alias_label"]) for kind in ("observational_items", "causal_source_items", "causal_eval_items") for row in t19_manifest[kind]}
    _require(not {str(row["codepoint"]) for row in fresh}.intersection(t19_codepoints), "Fresh bank overlaps T19 codepoints")
    _require(not {str(row["alias_label"]) for row in fresh}.intersection(t19_aliases), "Fresh bank overlaps T19 aliases")
    for row in fresh:
        _require(t19._words(str(row["canonical_label"])).isdisjoint(t19._words(str(row["alias_label"]))), "Fresh alias disjointness changed")
    return {
        "status": "pass",
        "fresh_eval_items": len(fresh),
        "source_items": len(source_items()),
        "selection_sha256": _sha256(_root() / SELECTION_PATH),
    }


# --------------------------------------------------------------------------
# Preflights, freeze, and admission.
# --------------------------------------------------------------------------


def audit_design(output: Path | None = None) -> dict[str, Any]:
    config = _config()
    selection = audit_selection()
    t19.audit_freeze()
    sites = tuple((str(row["site"]), int(row["block_index"])) for row in config["sites"]["order"])
    primary = tuple((str(row["site"]), int(row["block_index"])) for row in config["sites"]["primary"])
    _require(sites == SITE_ORDER, "T20 site roster changed")
    _require(primary == PRIMARY_SITES, "T20 primary sites changed")
    _require(int(config["subspace"]["rank"]) == 8, "T20 rank changed")
    spec = t10._model_spec(ROLE)
    _require(int(spec["expected_num_layers"]) == 28 and int(spec["expected_model_dim"]) == 3072, "T20 model geometry changed")
    contexts = tuple((str(carrier), int(distance)) for carrier in config["input"]["carrier_order"] for distance in config["input"]["distance_order"])
    _require(tuple(sorted(contexts)) == tuple(sorted(CONTEXT_ORDER)), "T20 context roster changed")
    decision = config["primary_decision"]
    _require(float(decision["practical_minimum_each"]) == 0.02, "T20 floor changed")
    _require(float(decision["ceiling_positive_control"]["informative_minimum"]) == 0.06, "T20 ceiling minimum changed")
    expected_eval_forwards = len(fresh_items()) * len(CONTEXT_ORDER) * (3 + 2 * len(SITE_ORDER))
    _require(expected_eval_forwards == int(config["acquisition"]["expected_evaluation_forwards"]), "T20 evaluation forward budget changed")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_design_pass_zero_source_or_eval_forwards",
        "parent_protocol_id": t19c.PROTOCOL_ID,
        "selection_sha256": selection["selection_sha256"],
        "model_role": ROLE,
        "source_rows": len(source_items()),
        "fresh_eval_rows": len(fresh_items()),
        "site_order": [{"site": site, "block_index": block} for site, block in SITE_ORDER],
        "primary_sites": [{"site": site, "block_index": block} for site, block in PRIMARY_SITES],
        "context_order": [{"carrier": carrier, "distance": distance} for carrier, distance in CONTEXT_ORDER],
        "subspace_rank": 8,
        "constructions": list(config["subspace"]["constructions"]),
        "causal_go_gate_open": False,
        "source_model_forwards": 0,
        "evaluation_model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    if output is not None:
        _require(not output.exists(), f"T20 design preflight exists: {output}")
        _write_json(output, value)
    return value


def _context_input(tokenizer: Any, row: Mapping[str, Any], view: str, carrier: str, distance: int) -> tuple[list[int], int]:
    spec = t19._config()["input"]["carriers"][carrier]
    unit = str(spec["unit"])
    repeats = int(spec["repeats"])
    _require(distance <= repeats, "Distance exceeds carrier repeats")
    raw = [int(value) for value in tokenizer.encode(str(row[view]), add_special_tokens=False)]
    ids = [int(value) for value in tokenizer.encode(str(row[view]) + unit * repeats, add_special_tokens=False)]
    unit_ids = [int(value) for value in tokenizer.encode(unit, add_special_tokens=False)]
    _require(len(unit_ids) == 1 and ids == raw + unit_ids * repeats, "T20 carrier sequence changed")
    return ids, len(raw) + distance - 1


def tokenizer_preflight(model_path: Path, output: Path) -> dict[str, Any]:
    from transformers import AutoTokenizer

    design = audit_design()
    tokenizer = AutoTokenizer.from_pretrained(model_path.resolve(), local_files_only=True, trust_remote_code=False, use_fast=True)
    reference = t10._tokenize_roster(tokenizer, t10._config())["receipt"]
    frozen_reference = _read_json(t10._receipt_path(ROLE))["tokenizer"]
    _require(reference["ordered_sequence_sha256"] == frozen_reference["ordered_sequence_sha256"], "T20 tokenizer differs on T10 reference")
    banks: dict[str, Any] = {}
    for bank_name, rows, views in (("source", source_items(), SOURCE_VIEWS), ("fresh_eval", fresh_items(), EVAL_VIEWS)):
        hashes: dict[str, str] = {}
        maximum = 0
        for view in views:
            raw_rows = []
            for row in rows:
                raw = [int(value) for value in tokenizer.encode(str(row[view]), add_special_tokens=False)]
                _require(bool(raw), f"Empty tokenization: {row['codepoint']}/{view}")
                raw_rows.append(raw)
            _require(len({tuple(ids) for ids in raw_rows}) == len(raw_rows), f"Non-unique sequences: {bank_name}/{view}")
            hashes[f"raw__{view}"] = t19._sequence_hash(raw_rows)
            for carrier, distance in CONTEXT_ORDER:
                combined_rows = []
                for row in rows:
                    ids, position = _context_input(tokenizer, row, view, carrier, distance)
                    _require(position < len(ids), "Readout position out of range")
                    combined_rows.append(ids)
                    maximum = max(maximum, len(ids))
                hashes[f"combined__{view}__{carrier}__d{distance}"] = t19._sequence_hash(combined_rows)
        banks[bank_name] = {"rows": len(rows), "views": list(views), "ordered_sequence_sha256": hashes, "maximum_combined_tokens": maximum}
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_tokenizer_preflight_pass_zero_source_or_eval_forwards",
        "model_role": ROLE,
        "artifact_model_id": t10._model_spec(ROLE)["artifact_model_id"],
        "frozen_model_revision": t10._model_spec(ROLE)["revision"],
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_asset_sha256": t19._tokenizer_asset_hashes(model_path.resolve()),
        "design_preflight": design,
        "banks": banks,
        "source_model_forwards": 0,
        "evaluation_model_forwards": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"T20 tokenizer preflight exists: {output}")
    _write_json(output, value)
    return {"status": "pass", "source_rows": banks["source"]["rows"], "fresh_eval_rows": banks["fresh_eval"]["rows"], "sha256": _sha256(output), "model_forwards": 0}


def _frozen_assets() -> tuple[str, ...]:
    return (
        CONFIG_PATH.as_posix(),
        SELECTION_PATH.as_posix(),
        "configs/t19_lexical_alias_unicode_control_v0.yaml",
        "data/manifests/t19_lexical_alias_unicode_control_v0.json",
        "data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json",
        "data/manifests/t19_lexical_alias_component_causal_v0_go.json",
        "docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md",
        "docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.ja.md",
        "scripts/t20_lexical_alias_optimized_subspace_causal_v0.py",
        "scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py",
        "tests/test_t20_lexical_alias_optimized_subspace_causal_v0.py",
        DESIGN_PREFLIGHT_PATH.as_posix(),
        TOKENIZER_PREFLIGHT_PATH.as_posix(),
    )


def build_freeze(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    token = _read_json(_root() / TOKENIZER_PREFLIGHT_PATH)
    _require(design.get("status") == "t20_design_pass_zero_source_or_eval_forwards", "T20 design preflight incomplete")
    _require(token.get("status") == "t20_tokenizer_preflight_pass_zero_source_or_eval_forwards", "T20 tokenizer preflight incomplete")
    _require(int(design["source_model_forwards"]) == 0 and int(token["source_model_forwards"]) == 0, "T20 preflight used a forward")
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        _require(path.is_file(), f"T20 frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_final_execution_freeze_zero_source_or_eval_forwards",
        "experiment_label": _config()["experiment_label"],
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "t19_freeze_manifest_sha256": _sha256(_root() / t19.FREEZE_PATH),
        "site_order": [{"site": site, "block_index": block} for site, block in SITE_ORDER],
        "primary_sites": [{"site": site, "block_index": block} for site, block in PRIMARY_SITES],
        "context_order": [{"carrier": carrier, "distance": distance} for carrier, distance in CONTEXT_ORDER],
        "subspace_rank": 8,
        "source_model_forwards_at_freeze": 0,
        "evaluation_model_forwards_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
    }
    _require(not output.exists(), f"T20 freeze exists: {output}")
    _write_json(output, value)
    return {"status": "pass", "manifest_sha256": _sha256(output), "frozen_asset_count": len(assets), "model_forwards": 0}


def audit_freeze(*, require_pushed: bool = False) -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T20 freeze protocol mismatch")
    _require(value.get("status") == "t20_final_execution_freeze_zero_source_or_eval_forwards", "T20 freeze status incomplete")
    for relative, expected in value["frozen_assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"T20 frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"T20 frozen asset changed: {relative}")
    git = {"required": False}
    if require_pushed:
        head = _git_value("rev-parse", "HEAD")
        remote = _git_value("rev-parse", "origin/main")
        _require(head == remote, "T20 freeze commit is not pushed to origin/main")
        _git_value("cat-file", "-e", f"HEAD:{FREEZE_PATH.as_posix()}")
        git = {"required": True, "head": head, "origin_main": remote}
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path), "git": git}


def admit_go(t19_causal_analysis: Path, output: Path) -> dict[str, Any]:
    t19.audit_freeze(require_pushed=True)
    t19c.audit_go(require_pushed=True)
    freeze = audit_freeze(require_pushed=True)
    parent = t19c.validate_analysis(t19_causal_analysis)
    _require(parent["status"] == "pass", "T19-C analysis is not validated")
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    token = _read_json(_root() / TOKENIZER_PREFLIGHT_PATH)
    _require(design.get("status") == "t20_design_pass_zero_source_or_eval_forwards", "T20 design preflight incomplete")
    _require(token.get("status") == "t20_tokenizer_preflight_pass_zero_source_or_eval_forwards", "T20 tokenizer preflight incomplete")
    _require(not output.exists(), f"T20 go manifest exists: {output}")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_go_admitted_before_source_or_eval_forwards",
        "t20_freeze_manifest_sha256": freeze["freeze_manifest_sha256"],
        "t19_freeze_manifest_sha256": t19.audit_freeze()["freeze_manifest_sha256"],
        "t19_causal_analysis_receipt_sha256": parent["analysis_receipt_sha256"],
        "t19_causal_primary_positive": bool(parent["primary_positive"]),
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "tokenizer_preflight_sha256": _sha256(_root() / TOKENIZER_PREFLIGHT_PATH),
        "causal_executor_analyzer_sha256": _sha256(Path(__file__)),
        "source_bank_sha256": _bank_hash(source_items()),
        "fresh_eval_bank_sha256": _bank_hash(fresh_items()),
        "source_model_forwards_at_go": 0,
        "evaluation_model_forwards_at_go": 0,
        "intervention_calls_at_go": 0,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output, value)
    return {"status": "pass", "go_manifest_sha256": _sha256(output), "source_model_forwards": 0, "evaluation_model_forwards": 0}


def audit_go(*, require_pushed: bool = False) -> dict[str, Any]:
    audit_freeze(require_pushed=require_pushed)
    path = _root() / GO_MANIFEST_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID and value.get("status") == "t20_go_admitted_before_source_or_eval_forwards", "T20 go manifest mismatch")
    _require(value["causal_executor_analyzer_sha256"] == _sha256(Path(__file__)), "T20 executor changed after go")
    _require(value["source_bank_sha256"] == _bank_hash(source_items()), "T20 source bank changed")
    _require(value["fresh_eval_bank_sha256"] == _bank_hash(fresh_items()), "T20 fresh eval bank changed")
    if require_pushed:
        _require(_git_value("rev-parse", "HEAD") == _git_value("rev-parse", "origin/main"), "T20 go commit is not pushed")
        _git_value("cat-file", "-e", f"HEAD:{GO_MANIFEST_PATH.as_posix()}")
    return {"status": "pass", "go_manifest_sha256": _sha256(path)}


# --------------------------------------------------------------------------
# Acquisition helpers.
# --------------------------------------------------------------------------


def _yield_if_contended(output_root: Path, boundary: str) -> None:
    pids = atlas._foreign_gpu_pids()
    if not pids:
        return
    output_root.mkdir(parents=True, exist_ok=True)
    receipt = output_root / "yield_receipt.json"
    if not receipt.exists():
        _write_json(receipt, {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "yielded_for_foreign_gpu_contention",
            "boundary": boundary,
            "foreign_gpu_pids": pids,
            "time_utc": datetime.now(timezone.utc).isoformat(),
        })
    raise SystemExit(int(t19._config()["execution_policy"]["yield_exit_code_on_foreign_contention"]))


def _load_model(model_path: Path) -> tuple[Any, Any, Any, Sequence[Any], dict[str, Any]]:
    t10._validate_runtime(t10._config())
    torch, tokenizer, model, _last_block, receipt, _roster = t10._load_model(ROLE, model_path)
    blocks = t10._resolve_attr(model, str(t10._model_spec(ROLE)["expected_block_path"]))
    return torch, tokenizer, model, blocks, receipt


def _capture_sites_and_final(
    *, torch: Any, tokenizer: Any, model: Any, blocks: Sequence[Any], row: Mapping[str, Any],
    view: str, carrier: str, distance: int, batch_count: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    ids, position = _context_input(tokenizer, row, view, carrier, distance)
    input_ids = torch.tensor([ids], dtype=torch.long, device="cuda").repeat(batch_count, 1)
    attention_mask = torch.ones_like(input_ids)
    captured: dict[tuple[str, int], Any] = {}
    handles = []
    for site, block_index in SITE_ORDER:
        module, is_pre = _site_module(blocks, site, block_index)
        _require(not is_pre, "T20 site unexpectedly uses a pre-hook")

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
    sites = np.stack([captured[key] for key in SITE_ORDER]).astype(np.float32)
    return sites, final.astype(np.float32)


def _forward_replacements(
    *, torch: Any, tokenizer: Any, model: Any, blocks: Sequence[Any], row: Mapping[str, Any],
    view: str, carrier: str, distance: int, site: str, block_index: int, replacements: np.ndarray,
) -> np.ndarray:
    ids, position = _context_input(tokenizer, row, view, carrier, distance)
    count = int(replacements.shape[0])
    input_ids = torch.tensor([ids], dtype=torch.long, device="cuda").repeat(count, 1)
    attention_mask = torch.ones_like(input_ids)
    module, is_pre = _site_module(blocks, site, block_index)
    _require(not is_pre, "T20 site unexpectedly uses a pre-hook")
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
    _require(result.shape[0] == count and np.isfinite(result).all(), "T20 replacement produced invalid final states")
    return result.astype(np.float32)


def _svd_and_random_subspace(glyph: np.ndarray, alias: np.ndarray, rank: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return t19c._source_subspace(glyph, alias, rank, seed)


def _train_split(count: int, train: int) -> tuple[np.ndarray, np.ndarray]:
    order = sorted(range(count), key=lambda index: hashlib.sha256(f"{PROTOCOL_ID}:split:{index}".encode("ascii")).hexdigest())
    train_indices = np.asarray(sorted(order[:train]), dtype=np.int64)
    val_indices = np.asarray(sorted(order[train:]), dtype=np.int64)
    return train_indices, val_indices


def _train_optimized_basis(
    *, torch: Any, tokenizer: Any, model: Any, blocks: Sequence[Any], rows: Sequence[Mapping[str, Any]],
    site: str, block_index: int, site_index: int,
    glyph_states: np.ndarray, codepoint_states: np.ndarray, alias_finals: np.ndarray,
    glyph_mean: np.ndarray, seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    config = _config()["subspace"]["training"]
    rank = int(_config()["subspace"]["rank"])
    width = glyph_states.shape[1]
    carrier, distance = TRAINING_CONTEXT
    steps = int(config["steps"])
    batch_items = int(config["batch_items"])
    temperature = float(config["infonce_temperature"])
    margin = float(config["necessity_margin"])
    necessity_weight = float(config["necessity_weight"])
    learning_rate = float(config["learning_rate"])
    train_idx, val_idx = _train_split(len(rows), int(config["train_items"]))

    device = "cuda"
    generator = torch.Generator(device="cpu")
    generator.manual_seed(TRAINING_SEED_BASE + site_index * 10 + seed)
    torch.manual_seed(TRAINING_SEED_BASE + site_index * 10 + seed)

    gallery = torch.tensor(alias_finals, dtype=torch.float32, device=device)
    gallery_mean = gallery.mean(dim=0, keepdim=True)
    gallery_n = torch.nn.functional.normalize(gallery - gallery_mean, dim=1)
    glyph_t = torch.tensor(glyph_states, dtype=torch.float32, device=device)
    codepoint_t = torch.tensor(codepoint_states, dtype=torch.float32, device=device)
    mean_t = torch.tensor(glyph_mean, dtype=torch.float32, device=device)

    module, is_pre = _site_module(blocks, site, block_index)
    _require(not is_pre, "T20 training site unexpectedly uses a pre-hook")

    linear = torch.nn.Linear(width, rank, bias=False, dtype=torch.float32, device=device)
    torch.nn.init.orthogonal_(linear.weight)
    linear = torch.nn.utils.parametrizations.orthogonal(linear)
    optimizer = torch.optim.Adam(linear.parameters(), lr=learning_rate)

    inputs_cache: dict[str, tuple[Any, Any, Any]] = {}
    for view in ("glyph", "codepoint_literal"):
        ids_rows, positions = [], []
        for row in rows:
            ids, position = _context_input(tokenizer, row, view, carrier, distance)
            ids_rows.append(ids)
            positions.append(position)
        longest = max(len(ids) for ids in ids_rows)
        pad_id = int(tokenizer.eos_token_id)
        padded = torch.full((len(rows), longest), pad_id, dtype=torch.long, device=device)
        mask = torch.zeros((len(rows), longest), dtype=torch.long, device=device)
        for index, ids in enumerate(ids_rows):
            padded[index, : len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)
            mask[index, : len(ids)] = 1
        inputs_cache[view] = (padded, mask, torch.tensor(positions, dtype=torch.long, device=device))

    def _final_states(view: str, indices: Any, replacement: Any) -> Any:
        padded, mask, positions = inputs_cache[view]
        batch_ids = padded[indices]
        batch_mask = mask[indices]
        batch_positions = positions[indices]

        def hook(_module: Any, _inputs: Any, output: Any) -> Any:
            raw, rebuild = causal_engine._tensor_from_output(output)
            changed = raw.clone()
            changed[torch.arange(len(batch_positions), device=device), batch_positions, :] = replacement.to(raw.dtype)
            return rebuild(changed)

        handle = module.register_forward_hook(hook)
        try:
            output = model(input_ids=batch_ids, attention_mask=batch_mask, use_cache=False, output_hidden_states=True, return_dict=True)
            final = output.hidden_states[-1][torch.arange(len(batch_positions), device=device), batch_positions, :]
        finally:
            handle.remove()
        return final.float()

    def _losses(indices: Any) -> tuple[Any, Any]:
        basis = linear.weight  # (rank, width), orthonormal rows
        g = glyph_t[indices]
        c = codepoint_t[indices]
        patched = c + (g - c) @ basis.T @ basis
        ablated = g - (g - mean_t) @ basis.T @ basis
        z = _final_states("codepoint_literal", indices, patched)
        y = _final_states("glyph", indices, ablated)
        z_n = torch.nn.functional.normalize(z - gallery_mean, dim=1)
        y_n = torch.nn.functional.normalize(y - gallery_mean, dim=1)
        logits_suff = temperature * (z_n @ gallery_n.T)
        suff_loss = torch.nn.functional.cross_entropy(logits_suff, indices)
        sims_nec = y_n @ gallery_n.T
        own = sims_nec[torch.arange(len(indices), device=device), indices]
        masked = sims_nec.clone()
        masked[torch.arange(len(indices), device=device), indices] = -2.0
        best_other = masked.max(dim=1).values
        nec_loss = torch.relu(margin + own - best_other).mean()
        return suff_loss, nec_loss

    def _validation_score() -> float:
        with torch.no_grad():
            basis = linear.weight
            indices = torch.tensor(val_idx, dtype=torch.long, device=device)
            g = glyph_t[indices]
            c = codepoint_t[indices]
            patched = c + (g - c) @ basis.T @ basis
            ablated = g - (g - mean_t) @ basis.T @ basis
            z = _final_states("codepoint_literal", indices, patched)
            y = _final_states("glyph", indices, ablated)
            z_n = torch.nn.functional.normalize(z - gallery_mean, dim=1)
            y_n = torch.nn.functional.normalize(y - gallery_mean, dim=1)
            patched_top1 = float((torch.argmax(z_n @ gallery_n.T, dim=1) == indices).float().mean())
            ablated_top1 = float((torch.argmax(y_n @ gallery_n.T, dim=1) == indices).float().mean())
        return patched_top1 - ablated_top1

    train_pool = torch.tensor(train_idx, dtype=torch.long, device=device)
    best_score = -np.inf
    best_basis = np.ascontiguousarray(linear.weight.detach().float().cpu().numpy().T)
    history: list[dict[str, float]] = []
    forward_passes = 0
    for step in range(steps):
        permutation = torch.randperm(len(train_pool), generator=generator)[:batch_items]
        indices = train_pool[permutation.to(device)]
        optimizer.zero_grad(set_to_none=True)
        suff_loss, nec_loss = _losses(indices)
        loss = suff_loss + necessity_weight * nec_loss
        loss.backward()
        torch.nn.utils.clip_grad_norm_(linear.parameters(), 1.0)
        optimizer.step()
        forward_passes += 2
        if (step + 1) % 50 == 0 or step == steps - 1:
            score = _validation_score()
            forward_passes += 2
            history.append({"step": step + 1, "loss": float(loss.detach()), "suff_loss": float(suff_loss.detach()), "nec_loss": float(nec_loss.detach()), "validation_score": score})
            if score > best_score:
                best_score = score
                best_basis = np.ascontiguousarray(linear.weight.detach().float().cpu().numpy().T)
    basis = best_basis.astype(np.float32)
    gram = basis.T @ basis
    _require(float(np.max(np.abs(gram - np.eye(basis.shape[1])))) < 1e-4, "Optimized basis is not orthonormal")
    q, _ = np.linalg.qr(basis.astype(np.float64))
    basis = np.ascontiguousarray(q[:, : basis.shape[1]]).astype(np.float32)
    receipt = {
        "seed": seed,
        "train_items": int(len(train_idx)),
        "validation_items": int(len(val_idx)),
        "best_validation_score": float(best_score),
        "history": history,
        "training_forward_passes": forward_passes,
    }
    return basis, receipt


def run_training(model_path: Path, output_root: Path) -> dict[str, Any]:
    audit_go(require_pushed=True)
    _require(not output_root.exists(), f"T20 training output exists: {output_root}")
    _yield_if_contended(output_root, "before_training_model_load")
    stage = output_root.with_name(f".{output_root.name}.stage-{uuid.uuid4().hex}")
    stage.mkdir(parents=True)
    torch, tokenizer, model, blocks, model_receipt = _load_model(model_path)
    rows = source_items()
    width = int(t10._model_spec(ROLE)["expected_model_dim"])
    carrier, distance = TRAINING_CONTEXT
    activations = np.empty((len(SITE_ORDER), len(rows), len(SOURCE_VIEWS), width), dtype=np.float32)
    finals = np.empty((len(rows), len(SOURCE_VIEWS), width), dtype=np.float32)
    forwards = 0
    started = time.perf_counter()
    for item_index, row in enumerate(rows):
        if item_index % 8 == 0:
            _yield_if_contended(output_root, f"training_capture_{item_index:04d}")
        for view_index, view in enumerate(SOURCE_VIEWS):
            sites, final = _capture_sites_and_final(torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row, view=view, carrier=carrier, distance=distance)
            activations[:, item_index, view_index, :] = sites
            finals[item_index, view_index] = final
            forwards += 1
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    rank = int(_config()["subspace"]["rank"])
    seeds = [int(value) for value in _config()["subspace"]["training"]["seeds"]]
    learned = np.empty((len(SITE_ORDER), width, rank), dtype=np.float32)
    svd_basis = np.empty_like(learned)
    random_basis = np.empty_like(learned)
    glyph_means = np.empty((len(SITE_ORDER), width), dtype=np.float32)
    training_receipts: list[dict[str, Any]] = []
    training_forward_passes = 0
    try:
        for site_index, (site, block_index) in enumerate(SITE_ORDER):
            svd_basis[site_index], random_basis[site_index], glyph_means[site_index] = _svd_and_random_subspace(
                activations[site_index, :, 0, :],
                activations[site_index, :, 1, :],
                rank,
                RANDOM_SEED_BASE + site_index,
            )
            candidates: list[tuple[float, int, np.ndarray, dict[str, Any]]] = []
            for seed in seeds:
                _yield_if_contended(output_root, f"training_site_{site_index}_seed_{seed}")
                basis, receipt = _train_optimized_basis(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, rows=rows,
                    site=site, block_index=block_index, site_index=site_index,
                    glyph_states=activations[site_index, :, 0, :],
                    codepoint_states=activations[site_index, :, 2, :],
                    alias_finals=finals[:, 1, :],
                    glyph_mean=glyph_means[site_index],
                    seed=seed,
                )
                receipt.update({"site": site, "block_index": block_index})
                training_receipts.append(receipt)
                training_forward_passes += int(receipt["training_forward_passes"])
                candidates.append((float(receipt["best_validation_score"]), seed, basis, receipt))
            candidates.sort(key=lambda value: (-value[0], value[1]))
            learned[site_index] = candidates[0][2]
            training_receipts.append({
                "site": site,
                "block_index": block_index,
                "selected_seed": candidates[0][1],
                "selected_validation_score": candidates[0][0],
                "selection_rule": "max_validation_patched_minus_ablated_top1_then_lowest_seed",
            })
    finally:
        del model
        torch.cuda.empty_cache()
    np.save(stage / "source_activations.npy", activations, allow_pickle=False)
    np.save(stage / "source_final_states.npy", finals, allow_pickle=False)
    np.savez_compressed(
        stage / "subspaces.npz",
        optimized=learned,
        cross_covariance_svd=svd_basis,
        random_control=random_basis,
        glyph_means=glyph_means,
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_training_complete",
        "model_role": ROLE,
        "source_rows": len(rows),
        "source_bank_sha256": _bank_hash(rows),
        "site_order": [{"site": site, "block_index": block} for site, block in SITE_ORDER],
        "subspace_rank": rank,
        "training_context": {"carrier": carrier, "distance": distance},
        "capture_forward_calls": forwards,
        "training_batched_forward_passes": training_forward_passes,
        "evaluation_model_forwards": 0,
        "intervention_calls": 0,
        "elapsed_seconds": time.perf_counter() - started,
        "model": model_receipt,
        "go_manifest_sha256": audit_go()["go_manifest_sha256"],
        "training_receipts": training_receipts,
        "outputs": {name: _sha256(stage / name) for name in ("source_activations.npy", "source_final_states.npy", "subspaces.npz")},
    }
    _write_json(stage / "training_receipt.json", receipt)
    t19.engine._write_ledger(stage, ("source_activations.npy", "source_final_states.npy", "subspaces.npz", "training_receipt.json"))
    os.replace(stage, output_root)
    return validate_training(output_root)


def validate_training(output_root: Path) -> dict[str, Any]:
    receipt = _read_json(output_root / "training_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "t20_training_complete", "T20 training receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output_root / name) == expected, f"T20 training output changed: {name}")
    with np.load(output_root / "subspaces.npz", allow_pickle=False) as values:
        for key in ("optimized", "cross_covariance_svd", "random_control"):
            basis = values[key]
            _require(basis.shape == (len(SITE_ORDER), 3072, 8), f"T20 subspace shape changed: {key}")
            for index in range(len(SITE_ORDER)):
                gram = basis[index].T @ basis[index]
                _require(float(np.max(np.abs(gram - np.eye(8)))) < 2e-5, f"T20 stored subspace not orthonormal: {key}/{index}")
        for index in range(len(SITE_ORDER)):
            overlap = float(np.max(np.abs(values["cross_covariance_svd"][index].T @ values["random_control"][index])))
            _require(overlap < 2e-5, "T20 random control overlaps the svd subspace")
    return {
        "status": "pass",
        "source_rows": int(receipt["source_rows"]),
        "capture_forward_calls": int(receipt["capture_forward_calls"]),
        "training_batched_forward_passes": int(receipt["training_batched_forward_passes"]),
        "training_receipt_sha256": _sha256(output_root / "training_receipt.json"),
    }


def run_evaluation(model_path: Path, training_root: Path, output_root: Path) -> dict[str, Any]:
    audit_go(require_pushed=True)
    training = validate_training(training_root)
    _require(not output_root.exists(), f"T20 evaluation output exists: {output_root}")
    _yield_if_contended(output_root, "before_eval_model_load")
    stage = output_root.with_name(f".{output_root.name}.stage-{uuid.uuid4().hex}")
    stage.mkdir(parents=True)
    with np.load(training_root / "subspaces.npz", allow_pickle=False) as values:
        optimized = np.asarray(values["optimized"], dtype=np.float32)
        svd_basis = np.asarray(values["cross_covariance_svd"], dtype=np.float32)
        random_basis = np.asarray(values["random_control"], dtype=np.float32)
        glyph_means = np.asarray(values["glyph_means"], dtype=np.float32)
    torch, tokenizer, model, blocks, model_receipt = _load_model(model_path)
    rows = fresh_items()
    width = int(t10._model_spec(ROLE)["expected_model_dim"])
    sites = len(SITE_ORDER)
    contexts = len(CONTEXT_ORDER)
    baseline_finals = np.empty((len(rows), contexts, len(EVAL_VIEWS), width), dtype=np.float32)
    baseline_components = np.empty((sites, len(rows), contexts, 2, width), dtype=np.float32)
    glyph_conditions = np.empty((sites, len(rows), contexts, len(GLYPH_CONDITION_ORDER), width), dtype=np.float32)
    codepoint_conditions = np.empty((sites, len(rows), contexts, len(CODEPOINT_CONDITION_ORDER), width), dtype=np.float32)
    forwards = 0
    interventions = 0
    started = time.perf_counter()
    try:
        for item_index, row in enumerate(rows):
            if item_index % 4 == 0:
                _yield_if_contended(output_root, f"eval_item_{item_index:04d}")
            for context_index, (carrier, distance) in enumerate(CONTEXT_ORDER):
                glyph_sites, glyph_final = _capture_sites_and_final(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                    view="glyph", carrier=carrier, distance=distance, batch_count=len(GLYPH_CONDITION_ORDER),
                )
                codepoint_sites, codepoint_final = _capture_sites_and_final(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                    view="codepoint_literal", carrier=carrier, distance=distance, batch_count=len(CODEPOINT_CONDITION_ORDER),
                )
                _alias_sites, alias_final = _capture_sites_and_final(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                    view="alias_label", carrier=carrier, distance=distance,
                )
                forwards += 3
                baseline_finals[item_index, context_index, 0] = glyph_final
                baseline_finals[item_index, context_index, 1] = alias_final
                baseline_finals[item_index, context_index, 2] = codepoint_final
                baseline_components[:, item_index, context_index, 0] = glyph_sites
                baseline_components[:, item_index, context_index, 1] = codepoint_sites
                for site_index, (site, block_index) in enumerate(SITE_ORDER):
                    g = glyph_sites[site_index]
                    c = codepoint_sites[site_index]
                    centered_g = g - glyph_means[site_index]
                    nec_opt = t19c._project(centered_g, optimized[site_index])
                    nec_rand = t19c._project(centered_g, random_basis[site_index])
                    nec_svd = t19c._project(centered_g, svd_basis[site_index])
                    glyph_replacements = np.stack((
                        g,
                        g - nec_opt,
                        g - nec_rand,
                        g - nec_svd,
                        (g - nec_opt) + nec_opt,
                        c,
                    )).astype(np.float32)
                    suff_opt = t19c._project(g - c, optimized[site_index])
                    suff_rand = t19c._project(g - c, random_basis[site_index])
                    suff_svd = t19c._project(g - c, svd_basis[site_index])
                    codepoint_replacements = np.stack((
                        c,
                        c + suff_opt,
                        c + suff_rand,
                        c + suff_svd,
                        g,
                    )).astype(np.float32)
                    glyph_conditions[site_index, item_index, context_index] = _forward_replacements(
                        torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                        view="glyph", carrier=carrier, distance=distance, site=site, block_index=block_index,
                        replacements=glyph_replacements,
                    )
                    codepoint_conditions[site_index, item_index, context_index] = _forward_replacements(
                        torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                        view="codepoint_literal", carrier=carrier, distance=distance, site=site, block_index=block_index,
                        replacements=codepoint_replacements,
                    )
                    forwards += 2
                    interventions += (len(GLYPH_CONDITION_ORDER) - 1) + (len(CODEPOINT_CONDITION_ORDER) - 1)
    finally:
        del model
        torch.cuda.empty_cache()
    np.savez_compressed(
        stage / "evaluation_states.npz",
        baseline_finals=baseline_finals,
        baseline_components=baseline_components,
        glyph_conditions=glyph_conditions,
        codepoint_conditions=codepoint_conditions,
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_evaluation_complete_sealed",
        "model_role": ROLE,
        "evaluation_rows": len(rows),
        "fresh_eval_bank_sha256": _bank_hash(rows),
        "site_order": [{"site": site, "block_index": block} for site, block in SITE_ORDER],
        "context_order": [{"carrier": carrier, "distance": distance} for carrier, distance in CONTEXT_ORDER],
        "glyph_condition_order": list(GLYPH_CONDITION_ORDER),
        "codepoint_condition_order": list(CODEPOINT_CONDITION_ORDER),
        "model_forward_calls": forwards,
        "intervention_rows": interventions,
        "elapsed_seconds": time.perf_counter() - started,
        "training_receipt_sha256": training["training_receipt_sha256"],
        "go_manifest_sha256": audit_go()["go_manifest_sha256"],
        "model": model_receipt,
        "outputs": {"evaluation_states.npz": _sha256(stage / "evaluation_states.npz")},
    }
    _write_json(stage / "evaluation_receipt.json", receipt)
    t19.engine._write_ledger(stage, ("evaluation_states.npz", "evaluation_receipt.json"))
    os.replace(stage, output_root)
    return validate_evaluation(output_root, training_root)


def validate_evaluation(output_root: Path, training_root: Path) -> dict[str, Any]:
    training = validate_training(training_root)
    receipt = _read_json(output_root / "evaluation_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "t20_evaluation_complete_sealed", "T20 evaluation receipt mismatch")
    _require(receipt["training_receipt_sha256"] == training["training_receipt_sha256"], "T20 evaluation training binding changed")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output_root / name) == expected, f"T20 evaluation output changed: {name}")
    rows = int(_config()["population"]["fresh_eval_emoji_items"])
    with np.load(output_root / "evaluation_states.npz", allow_pickle=False) as values:
        _require(values["baseline_finals"].shape == (rows, 4, 3, 3072), "T20 baseline shape changed")
        _require(values["baseline_components"].shape == (9, rows, 4, 2, 3072), "T20 component shape changed")
        _require(values["glyph_conditions"].shape == (9, rows, 4, 6, 3072), "T20 glyph condition shape changed")
        _require(values["codepoint_conditions"].shape == (9, rows, 4, 5, 3072), "T20 codepoint condition shape changed")
    return {
        "status": "pass",
        "evaluation_rows": int(receipt["evaluation_rows"]),
        "model_forward_calls": int(receipt["model_forward_calls"]),
        "intervention_rows": int(receipt["intervention_rows"]),
        "evaluation_receipt_sha256": _sha256(output_root / "evaluation_receipt.json"),
    }


# --------------------------------------------------------------------------
# Analysis.
# --------------------------------------------------------------------------


def _hits_by_context(queries: np.ndarray, alias_targets: np.ndarray, codepoint_targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-item alias-hit and codepoint-hit fractions averaged over contexts.

    queries: (items, contexts, width); targets likewise per view.
    """

    items, contexts, _width = queries.shape
    alias_hits = np.zeros((items, contexts), dtype=np.float64)
    codepoint_hits = np.zeros((items, contexts), dtype=np.float64)
    order = np.arange(items)
    for context in range(contexts):
        q = t19c._normalized(queries[:, context])
        alias = t19c._normalized(alias_targets[:, context])
        codepoint = t19c._normalized(codepoint_targets[:, context])
        alias_hits[:, context] = (np.argmax(q @ alias.T, axis=1) == order).astype(np.float64)
        codepoint_hits[:, context] = (np.argmax(q @ codepoint.T, axis=1) == order).astype(np.float64)
    return alias_hits.mean(axis=1), codepoint_hits.mean(axis=1)


def analyze(evaluation_root: Path, training_root: Path, output: Path) -> dict[str, Any]:
    _require(not output.exists(), f"T20 analysis output exists: {output}")
    evaluation = validate_evaluation(evaluation_root, training_root)
    decision = _config()["primary_decision"]
    practical = float(decision["practical_minimum_each"])
    guard_minimum = 0.90
    ceiling_minimum = float(decision["ceiling_positive_control"]["informative_minimum"])
    draws = int(decision["sign_flip_draws"])
    replicates = int(decision["bootstrap_replicates"])
    with np.load(evaluation_root / "evaluation_states.npz", allow_pickle=False) as arrays:
        baseline_finals = np.asarray(arrays["baseline_finals"], dtype=np.float32)
        glyph_conditions = np.asarray(arrays["glyph_conditions"], dtype=np.float32)
        codepoint_conditions = np.asarray(arrays["codepoint_conditions"], dtype=np.float32)
    alias_targets = baseline_finals[:, :, 1]
    codepoint_targets = baseline_finals[:, :, 2]

    def _condition_metrics(states: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
        alias_items, codepoint_items = _hits_by_context(states, alias_targets, codepoint_targets)
        return alias_items, codepoint_items, {
            "alias_top1": float(np.mean(alias_items)),
            "codepoint_top1": float(np.mean(codepoint_items)),
            "alias_minus_codepoint_top1": float(np.mean(alias_items - codepoint_items)),
        }

    base_glyph_alias, _bg_cp, base_glyph_metrics = _condition_metrics(baseline_finals[:, :, 0])
    _bc_alias, _bc_cp, base_codepoint_metrics = _condition_metrics(baseline_finals[:, :, 2])

    rows: list[dict[str, Any]] = []
    for site_index, (site, block_index) in enumerate(SITE_ORDER):
        glyph_metrics: dict[str, Any] = {}
        glyph_alias_items: dict[str, np.ndarray] = {}
        for condition_index, condition in enumerate(GLYPH_CONDITION_ORDER):
            alias_items, codepoint_items, metrics = _condition_metrics(glyph_conditions[site_index, :, :, condition_index])
            glyph_metrics[condition] = metrics
            glyph_alias_items[condition] = alias_items
        codepoint_metrics: dict[str, Any] = {}
        codepoint_alias_items: dict[str, np.ndarray] = {}
        codepoint_self_items: dict[str, np.ndarray] = {}
        for condition_index, condition in enumerate(CODEPOINT_CONDITION_ORDER):
            alias_items, codepoint_items, metrics = _condition_metrics(codepoint_conditions[site_index, :, :, condition_index])
            codepoint_metrics[condition] = metrics
            codepoint_alias_items[condition] = alias_items
            codepoint_self_items[condition] = codepoint_items

        necessity_adjusted = glyph_alias_items["necessity_random"] - glyph_alias_items["necessity_optimized"]
        sufficiency_adjusted = codepoint_alias_items["sufficiency_optimized"] - codepoint_alias_items["sufficiency_random"]
        necessity_svd_adjusted = glyph_alias_items["necessity_random"] - glyph_alias_items["necessity_svd"]
        sufficiency_svd_adjusted = codepoint_alias_items["sufficiency_svd"] - codepoint_alias_items["sufficiency_random"]
        necessity_test = t19c._sign_flip(necessity_adjusted, draws=draws, seed=SIGN_FLIP_SEED_BASE[0] + site_index * 10)
        sufficiency_test = t19c._sign_flip(sufficiency_adjusted, draws=draws, seed=SIGN_FLIP_SEED_BASE[1] + site_index * 10)
        necessity_interval = t19c._bootstrap(necessity_adjusted, replicates=replicates, seed=BOOTSTRAP_SEED_BASE[0] + site_index * 10)
        sufficiency_interval = t19c._bootstrap(sufficiency_adjusted, replicates=replicates, seed=BOOTSTRAP_SEED_BASE[1] + site_index * 10)
        sufficiency_ceiling = float(np.mean(codepoint_alias_items["full_interchange_glyph"] - codepoint_alias_items["zero_hook"]))
        necessity_ceiling = float(np.mean(glyph_alias_items["zero_hook"] - glyph_alias_items["full_interchange_codepoint"]))
        self_retrieval_guard = float(np.mean(codepoint_self_items["sufficiency_optimized"]))
        zero_glyph_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, :, 0] - baseline_finals[:, :, 0]) ** 2)))
        zero_codepoint_rms = float(np.sqrt(np.mean((codepoint_conditions[site_index, :, :, 0] - baseline_finals[:, :, 2]) ** 2)))
        restoration_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, :, 4] - baseline_finals[:, :, 0]) ** 2)))
        engineering_pass = max(zero_glyph_rms, zero_codepoint_rms, restoration_rms) <= float(decision["engineering_rms_maximum"])
        practical_and_interval_pass = bool(
            float(np.mean(necessity_adjusted)) >= practical
            and float(np.mean(sufficiency_adjusted)) >= practical
            and float(necessity_interval["lower_95"]) > practical
            and float(sufficiency_interval["lower_95"]) > practical
        )
        guard_pass = bool(self_retrieval_guard >= guard_minimum)
        row = {
            "site": site,
            "block_index": block_index,
            "primary_site": (site, block_index) in PRIMARY_SITES,
            "baseline_glyph": base_glyph_metrics,
            "baseline_codepoint": base_codepoint_metrics,
            "glyph_conditions": glyph_metrics,
            "codepoint_conditions": codepoint_metrics,
            "necessity_adjusted_effect": float(np.mean(necessity_adjusted)),
            "sufficiency_adjusted_effect": float(np.mean(sufficiency_adjusted)),
            "necessity_svd_adjusted_effect": float(np.mean(necessity_svd_adjusted)),
            "sufficiency_svd_adjusted_effect": float(np.mean(sufficiency_svd_adjusted)),
            "necessity_test": necessity_test,
            "sufficiency_test": sufficiency_test,
            "necessity_interval": necessity_interval,
            "sufficiency_interval": sufficiency_interval,
            "site_iut_p": max(float(necessity_test["p_value_one_sided"]), float(sufficiency_test["p_value_one_sided"])),
            "sufficiency_ceiling": sufficiency_ceiling,
            "necessity_ceiling": necessity_ceiling,
            "ceiling_informative": bool(sufficiency_ceiling >= ceiling_minimum),
            "self_retrieval_guard": self_retrieval_guard,
            "self_retrieval_guard_pass": guard_pass,
            "practical_and_interval_pass": practical_and_interval_pass,
            "engineering": {
                "zero_glyph_final_rms": zero_glyph_rms,
                "zero_codepoint_final_rms": zero_codepoint_rms,
                "restoration_final_rms": restoration_rms,
                "pass": engineering_pass,
            },
        }
        rows.append(row)

    primary_rows = sorted((row for row in rows if row["primary_site"]), key=lambda row: (float(row["site_iut_p"]), str(row["site"]), int(row["block_index"])))
    still = True
    for index, row in enumerate(primary_rows):
        threshold = 0.05 / (len(primary_rows) - index)
        reject = still and float(row["site_iut_p"]) <= threshold
        still = bool(reject)
        row["holm_rank"] = index + 1
        row["holm_threshold"] = threshold
        row["primary_positive"] = bool(
            reject
            and row["practical_and_interval_pass"]
            and row["self_retrieval_guard_pass"]
            and row["engineering"]["pass"]
        )
        if row["primary_positive"]:
            row["verdict"] = "positive"
        elif row["ceiling_informative"]:
            row["verdict"] = "negative_with_informative_ceiling"
        else:
            row["verdict"] = "uncalibratable_at_endpoint"
    positive_sites = [f"{row['site']}:{row['block_index']}" for row in primary_rows if row["primary_positive"]]
    output.mkdir(parents=True)
    _write_json(output / "causal_site_results.json", {"schema_version": SCHEMA_VERSION, "protocol_id": PROTOCOL_ID, "sites": rows})
    primary_result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_primary_complete",
        "primary_sites": [
            {
                "site": row["site"],
                "block_index": row["block_index"],
                "site_iut_p": row["site_iut_p"],
                "holm_threshold": row["holm_threshold"],
                "positive": row["primary_positive"],
                "verdict": row["verdict"],
                "sufficiency_ceiling": row["sufficiency_ceiling"],
                "necessity_ceiling": row["necessity_ceiling"],
            }
            for row in sorted(primary_rows, key=lambda row: PRIMARY_SITES.index((str(row["site"]), int(row["block_index"]))))
        ],
        "positive_sites": positive_sites,
        "positive": bool(positive_sites),
        "claim_boundary": _config()["claim_boundary"],
    }
    _write_json(output / "causal_primary_result.json", primary_result)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_analysis_complete",
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
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "t20_analysis_complete", "T20 analysis receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(output / name) == expected, f"T20 analysis output changed: {name}")
    primary = _read_json(output / "causal_primary_result.json")
    _require(bool(primary["positive"]) == bool(receipt["primary_positive"]), "T20 primary mismatch")
    return {"status": "pass", "primary_positive": bool(primary["positive"]), "positive_sites": list(primary["positive_sites"]), "analysis_receipt_sha256": _sha256(output / "analysis_receipt.json")}


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    sub = value.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("build-selection")
    selection.add_argument("--source-directory", type=Path, required=True)
    selection.add_argument("--output", type=Path, default=_root() / SELECTION_PATH)
    sub.add_parser("audit-selection")
    design = sub.add_parser("audit-design")
    design.add_argument("--output", type=Path)
    token = sub.add_parser("tokenizer-preflight")
    token.add_argument("--model-path", type=Path, required=True)
    token.add_argument("--output", type=Path, default=_root() / TOKENIZER_PREFLIGHT_PATH)
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    freeze_audit = sub.add_parser("audit-freeze")
    freeze_audit.add_argument("--require-pushed", action="store_true")
    go = sub.add_parser("admit-go")
    go.add_argument("--t19-causal-analysis", type=Path, required=True)
    go.add_argument("--output", type=Path, default=_root() / GO_MANIFEST_PATH)
    go_audit = sub.add_parser("audit-go")
    go_audit.add_argument("--require-pushed", action="store_true")
    training = sub.add_parser("run-training")
    training.add_argument("--model-path", type=Path, required=True)
    training.add_argument("--output-root", type=Path, required=True)
    training_audit = sub.add_parser("validate-training")
    training_audit.add_argument("--output-root", type=Path, required=True)
    evaluation = sub.add_parser("run-evaluation")
    evaluation.add_argument("--model-path", type=Path, required=True)
    evaluation.add_argument("--training-root", type=Path, required=True)
    evaluation.add_argument("--output-root", type=Path, required=True)
    evaluation_audit = sub.add_parser("validate-evaluation")
    evaluation_audit.add_argument("--training-root", type=Path, required=True)
    evaluation_audit.add_argument("--output-root", type=Path, required=True)
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--training-root", type=Path, required=True)
    analysis.add_argument("--evaluation-root", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    analysis_audit = sub.add_parser("validate-analysis")
    analysis_audit.add_argument("--output", type=Path, required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    if args.command == "build-selection":
        result = build_selection(args.source_directory, args.output)
    elif args.command == "audit-selection":
        result = audit_selection()
    elif args.command == "audit-design":
        result = audit_design(args.output)
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(args.model_path, args.output)
    elif args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze(require_pushed=args.require_pushed)
    elif args.command == "admit-go":
        result = admit_go(args.t19_causal_analysis, args.output)
    elif args.command == "audit-go":
        result = audit_go(require_pushed=args.require_pushed)
    elif args.command == "run-training":
        result = run_training(args.model_path, args.output_root)
    elif args.command == "validate-training":
        result = validate_training(args.output_root)
    elif args.command == "run-evaluation":
        result = run_evaluation(args.model_path, args.training_root, args.output_root)
    elif args.command == "validate-evaluation":
        result = validate_evaluation(args.output_root, args.training_root)
    elif args.command == "analyze":
        result = analyze(args.evaluation_root, args.training_root, args.output)
    elif args.command == "validate-analysis":
        result = validate_analysis(args.output)
    else:
        raise AssertionError(args.command)
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
