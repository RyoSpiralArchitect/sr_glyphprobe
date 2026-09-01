#!/usr/bin/env python3
"""Freeze, acquire, and analyze T19 lexical aliases and Unicode controls."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
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

import fresh_composite_glyph_lexical_confirmation_v0 as engine  # noqa: E402
import glyph_system_decomposition_v0 as t11  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-t19-lexical-alias-unicode-control-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/t19_lexical_alias_unicode_control_v0.yaml")
SELECTION_PATH = Path("data/manifests/t19_lexical_alias_unicode_control_v0.json")
FREEZE_PATH = Path("data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json")
VALIDATION_DIRECTORY = Path("validation/t19_lexical_alias_unicode_control_v0")
DESIGN_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "design_preflight.json"
TOKENIZER_DIRECTORY = VALIDATION_DIRECTORY / "tokenizers"
ENGINEERING_PREFLIGHT_PATH = VALIDATION_DIRECTORY / "engineering_preflight.json"
VIEW_ORDER = ("glyph", "canonical_label", "alias_label", "codepoint_literal")
KIND_ORDER = ("emoji", "symbol")
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
    ("glyph_canonical", 0, 1),
    ("glyph_alias", 0, 2),
    ("glyph_codepoint", 0, 3),
    ("canonical_alias", 1, 2),
)
SOURCE_FILENAMES = {
    "unicode_emoji_test": "emoji-test.txt",
    "unicode_data": "UnicodeData-17.0.0.txt",
    "emoji_data": "emoji-data-17.0.0.txt",
}


class T19Error(RuntimeError):
    """Raised when a T19 contract or artifact invariant is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T19Error(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
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


def _selection_hash(*parts: str) -> str:
    namespace = str(_config()["population"]["selection_namespace"])
    return _hash_text(":".join((namespace, *parts)))


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


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _git_value(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=_root(), check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _verify_source(path: Path, spec: Mapping[str, Any]) -> bytes:
    raw = path.read_bytes()
    _require(len(raw) == int(spec["expected_bytes"]), f"Source bytes changed: {path}")
    _require(hashlib.sha256(raw).hexdigest() == str(spec["sha256"]), f"Source hash changed: {path}")
    return raw


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def _strict_aliases(canonical: str, values: Sequence[str]) -> list[str]:
    canonical_words = _words(canonical)
    result = {
        str(value).strip()
        for value in values
        if _words(str(value)) and _words(str(value)).isdisjoint(canonical_words)
    }
    return sorted(result, key=lambda value: (_selection_hash("alias", value), value))


def _maximum_alias_matching(
    rows: Sequence[Mapping[str, Any]], *, forbidden_aliases: set[str] | None = None
) -> list[dict[str, Any]]:
    forbidden = forbidden_aliases or set()
    match: dict[str, int] = {}
    order = sorted(
        range(len(rows)),
        key=lambda index: (
            len([value for value in rows[index]["alias_candidates"] if value not in forbidden]),
            _selection_hash("matching-item", str(rows[index]["kind"]), str(rows[index]["codepoint"])),
        ),
    )

    def visit(index: int, seen: set[str]) -> bool:
        aliases = sorted(
            (value for value in rows[index]["alias_candidates"] if value not in forbidden),
            key=lambda value: _selection_hash(
                "matching-edge", str(rows[index]["kind"]), str(rows[index]["codepoint"]), str(value)
            ),
        )
        for alias in aliases:
            if alias in seen:
                continue
            seen.add(alias)
            if alias not in match or visit(match[alias], seen):
                match[alias] = index
                return True
        return False

    for index in order:
        visit(index, set())
    matched = [{**dict(rows[index]), "alias_label": alias} for alias, index in match.items()]
    matched.sort(key=lambda row: (str(row["kind"]), int(row["source_index"])))
    return matched


def _cldr_annotations(source_directory: Path) -> dict[str, dict[str, list[str]]]:
    config = _config()["source_bindings"]["cldr"]
    merged: dict[str, dict[str, list[str]]] = {}
    for key in ("english_annotations", "english_derived_annotations"):
        spec = config[key]
        raw = _verify_source(source_directory / str(spec["filename"]), spec)
        value = json.loads(raw.decode("utf-8"))
        current = value[str(spec["root_key"])]["annotations"]
        overlap = set(merged).intersection(current)
        _require(not overlap, "Unexpected CLDR base/derived overlap")
        merged.update({str(glyph): dict(row) for glyph, row in current.items()})
    return merged


def _unicode_data(raw: bytes) -> dict[int, tuple[str, str]]:
    result: dict[int, tuple[str, str]] = {}
    for line in raw.decode("utf-8").splitlines():
        fields = line.split(";")
        _require(len(fields) >= 3, "Malformed UnicodeData row")
        result[int(fields[0], 16)] = (fields[1], fields[2])
    return result


def _emoji_property(raw: bytes) -> set[int]:
    result: set[int] = set()
    for line in raw.decode("utf-8").splitlines():
        value = line.split("#", 1)[0].strip()
        if not value:
            continue
        span, prop = (part.strip() for part in value.split(";"))
        if prop != "Emoji":
            continue
        bounds = span.split("..")
        result.update(range(int(bounds[0], 16), int(bounds[-1], 16) + 1))
    return result


def _text_exposure(commit: str) -> tuple[dict[str, str], set[str]]:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        cwd=_root(),
        check=True,
        capture_output=True,
    ).stdout
    texts: dict[str, str] = {}
    characters: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        for member in handle.getmembers():
            if not member.isfile():
                continue
            stream = handle.extractfile(member)
            _require(stream is not None, f"Cannot read archived blob: {member.name}")
            raw = stream.read()
            if b"\0" in raw:
                continue
            try:
                value = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            texts[member.name] = value
            characters.update(value)
    return texts, characters


def _round_robin(
    rows: Sequence[Mapping[str, Any]], *, count: int, role: str
) -> list[dict[str, Any]]:
    by_stratum: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stratum[str(row["semantic_stratum"])].append(dict(row))
    for stratum, members in by_stratum.items():
        members.sort(
            key=lambda row: _selection_hash(role, "item", stratum, str(row["codepoint"]))
        )
    stratum_order = sorted(
        by_stratum, key=lambda stratum: _selection_hash(role, "stratum", stratum)
    )
    selected: list[dict[str, Any]] = []
    round_index = 0
    while len(selected) < count:
        progressed = False
        for stratum in stratum_order:
            if round_index >= len(by_stratum[stratum]) or len(selected) >= count:
                continue
            selected.append(dict(by_stratum[stratum][round_index]))
            progressed = True
        _require(progressed, f"Population unavailable for role: {role}")
        round_index += 1
    return selected


def build_selection(source_directory: Path, output: Path) -> dict[str, Any]:
    config = _config()
    sources = config["source_bindings"]
    emoji_raw = _verify_source(
        source_directory / SOURCE_FILENAMES["unicode_emoji_test"], sources["unicode_emoji_test"]
    )
    unicode_raw = _verify_source(
        source_directory / SOURCE_FILENAMES["unicode_data"], sources["unicode_data"]
    )
    emoji_data_raw = _verify_source(
        source_directory / SOURCE_FILENAMES["emoji_data"], sources["emoji_data"]
    )
    parsed = t11._parse_unicode_source(emoji_raw)
    _require(parsed["version"] == str(sources["unicode_emoji_test"]["version"]), "Emoji version changed")
    _require(
        len(parsed["fully_qualified"]) == int(sources["unicode_emoji_test"]["expected_fully_qualified_entries"]),
        "Emoji source count changed",
    )
    annotations = _cldr_annotations(source_directory)
    unicode_data = _unicode_data(unicode_raw)
    emoji_property = _emoji_property(emoji_data_raw)

    exposure = sources["exposure_tree"]
    commit = str(exposure["commit"])
    _require(_git_value("rev-parse", f"{commit}^{{tree}}") == str(exposure["tree"]), "Exposure tree changed")
    _require(len(_git_value("ls-tree", "-r", "--name-only", commit).splitlines()) == int(exposure["tracked_paths"]), "Exposure path count changed")
    texts, text_characters = _text_exposure(commit)
    _require(len(texts) == int(exposure["expected_utf8_text_without_nul_paths"]), "Exposure text path count changed")

    maximum_version = tuple(int(part) for part in str(config["population"]["maximum_emoji_version"]).split("."))
    emoji_candidates: list[dict[str, Any]] = []
    emoji_exclusions = Counter()
    for source_index, source_row in enumerate(parsed["fully_qualified"]):
        codepoints = tuple(int(value) for value in source_row["codepoints"])
        if len(codepoints) != 1:
            emoji_exclusions["not_one_codepoint"] += 1
            continue
        if tuple(int(part) for part in str(source_row["emoji_version"]).split(".")) > maximum_version:
            emoji_exclusions["newer_than_maximum_version"] += 1
            continue
        glyph = chr(codepoints[0])
        annotation = annotations.get(glyph) or annotations.get(glyph + "\ufe0f")
        if annotation is None or not annotation.get("tts"):
            emoji_exclusions["missing_cldr_tts"] += 1
            continue
        canonical = str(annotation["tts"][0])
        _require(canonical == str(source_row["name"]), f"Emoji tts/name mismatch: {codepoints[0]:04X}")
        aliases = _strict_aliases(canonical, annotation.get("default", []))
        if not aliases:
            emoji_exclusions["no_lexically_disjoint_keyword"] += 1
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
    symbol_exclusions = Counter()
    for glyph, annotation in annotations.items():
        if len(glyph) != 1:
            symbol_exclusions["not_one_codepoint"] += 1
            continue
        codepoint = ord(glyph)
        info = unicode_data.get(codepoint)
        if info is None or not info[1].startswith("S"):
            symbol_exclusions["not_unicode_symbol_category"] += 1
            continue
        if codepoint in emoji_property:
            symbol_exclusions["emoji_property_true"] += 1
            continue
        if glyph in text_characters:
            symbol_exclusions["surface_in_frozen_text_repository"] += 1
            continue
        if not annotation.get("tts"):
            symbol_exclusions["missing_cldr_tts"] += 1
            continue
        canonical = str(annotation["tts"][0])
        aliases = _strict_aliases(canonical, annotation.get("default", []))
        if not aliases:
            symbol_exclusions["no_lexically_disjoint_keyword"] += 1
            continue
        symbol_candidates.append(
            {
                "kind": "symbol",
                "glyph_system": "symbol",
                "glyph": glyph,
                "codepoint": f"{codepoint:04X}",
                "codepoints": [f"U+{codepoint:04X}"],
                "codepoint_literal": f"U+{codepoint:04X}",
                "canonical_label": canonical,
                "unicode_name": info[0],
                "unicode_category": info[1],
                "alias_candidates": aliases,
                "semantic_stratum": info[1],
                "source_index": codepoint,
                "prior_repository_text_surface_exposed": False,
            }
        )

    matched_symbols = _maximum_alias_matching(symbol_candidates)
    symbol_aliases = {str(row["alias_label"]) for row in matched_symbols}
    matched_emoji = _maximum_alias_matching(emoji_candidates, forbidden_aliases=symbol_aliases)
    population = config["population"]
    _require(
        len(matched_symbols) == int(population["observational_items_per_kind"]),
        "Complete symbol alias-matching pool changed",
    )
    observation_emoji = _round_robin(
        matched_emoji,
        count=int(population["observational_items_per_kind"]),
        role="observational-emoji",
    )
    used = {str(row["codepoint"]) for row in observation_emoji}
    remaining = [row for row in matched_emoji if str(row["codepoint"]) not in used]
    causal_source = _round_robin(
        remaining,
        count=int(population["causal_source_emoji_items"]),
        role="causal-source",
    )
    used.update(str(row["codepoint"]) for row in causal_source)
    remaining = [row for row in remaining if str(row["codepoint"]) not in used]
    causal_eval = _round_robin(
        remaining,
        count=int(population["causal_eval_emoji_items"]),
        role="causal-eval",
    )

    observational = [*observation_emoji, *matched_symbols]
    observational.sort(key=lambda row: (KIND_ORDER.index(str(row["kind"])), int(row["source_index"])))
    for index, row in enumerate(observational):
        row["selection_index"] = index
        row["bank_role"] = "observational_confirm"
    for index, row in enumerate(causal_source):
        row["bank_index"] = index
        row["bank_role"] = "causal_source"
    for index, row in enumerate(causal_eval):
        row["bank_index"] = index
        row["bank_role"] = "causal_eval"
    all_selected = [*observational, *causal_source, *causal_eval]
    aliases = [str(row["alias_label"]) for row in all_selected]
    _require(len(aliases) == len(set(aliases)), "Selected alias labels are not globally unique")
    codepoints = [str(row["codepoint"]) for row in all_selected]
    _require(len(codepoints) == len(set(codepoints)), "Selected banks overlap")
    for row in all_selected:
        _require(_words(str(row["canonical_label"])).isdisjoint(_words(str(row["alias_label"]))), "Alias lexical-disjointness changed")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "three_banks_selected_zero_t19_model_forwards_or_interventions",
        "source_bindings": {
            "unicode_emoji_test_sha256": hashlib.sha256(emoji_raw).hexdigest(),
            "unicode_data_sha256": hashlib.sha256(unicode_raw).hexdigest(),
            "emoji_data_sha256": hashlib.sha256(emoji_data_raw).hexdigest(),
            "cldr_sha256": {
                key: str(config["source_bindings"]["cldr"][key]["sha256"])
                for key in ("english_annotations", "english_derived_annotations")
            },
        },
        "exposure_audit": {
            "commit": commit,
            "tree": str(exposure["tree"]),
            "tracked_paths": int(exposure["tracked_paths"]),
            "utf8_text_without_nul_paths": len(texts),
            "definition": str(exposure["definition"]),
            "selected_symbol_surface_hits": 0,
            "observational_emoji_prior_surface_exposure_allowed": True,
        },
        "candidate_census": {
            "emoji_before_matching": len(emoji_candidates),
            "emoji_after_symbol_reserved_alias_matching": len(matched_emoji),
            "symbol_before_matching": len(symbol_candidates),
            "symbol_after_matching": len(matched_symbols),
            "emoji_exclusions": dict(sorted(emoji_exclusions.items())),
            "symbol_exclusions": dict(sorted(symbol_exclusions.items())),
        },
        "label_construction": dict(config["label_construction"]),
        "observational_items": observational,
        "causal_source_items": causal_source,
        "causal_eval_items": causal_eval,
        "counts": {
            "observational_total": len(observational),
            "observational_by_kind": dict(Counter(str(row["kind"]) for row in observational)),
            "causal_source": len(causal_source),
            "causal_eval": len(causal_eval),
        },
        "model_forward_calls": 0,
        "causal_source_model_forward_calls": 0,
        "causal_eval_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "pretraining_holdout_claim_authorized": False,
        "human_paraphrase_quality_claim_authorized": False,
    }
    _require(not output.exists(), f"Selection exists: {output}")
    _write_json(output, manifest)
    return {
        "status": "pass",
        "observational_items": len(observational),
        "observational_by_kind": manifest["counts"]["observational_by_kind"],
        "causal_source_items": len(causal_source),
        "causal_eval_items": len(causal_eval),
        "selection_sha256": _sha256(output),
        "model_forward_calls": 0,
    }


def _selection_manifest() -> dict[str, Any]:
    value = _read_json(_root() / SELECTION_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Selection protocol mismatch")
    _require(
        value.get("status") == "three_banks_selected_zero_t19_model_forwards_or_interventions",
        "Selection status changed",
    )
    return value


def items() -> list[dict[str, Any]]:
    rows = [dict(row) for row in _selection_manifest()["observational_items"]]
    rows.sort(key=lambda row: int(row["selection_index"]))
    return rows


def causal_items(role: str) -> list[dict[str, Any]]:
    key = {"source": "causal_source_items", "eval": "causal_eval_items"}.get(role)
    _require(key is not None, f"Unknown causal bank role: {role}")
    rows = [dict(row) for row in _selection_manifest()[key]]
    rows.sort(key=lambda row: int(row["bank_index"]))
    return rows


def audit_selection(*, rescan_exposure: bool = True) -> dict[str, Any]:
    config = _config()
    observational = items()
    source = causal_items("source")
    evaluation = causal_items("eval")
    expected = int(config["population"]["observational_items_per_kind"])
    _require(len(observational) == expected * 2, "Observational count changed")
    _require(Counter(str(row["kind"]) for row in observational) == Counter({"emoji": expected, "symbol": expected}), "Observational kind counts changed")
    _require(len(source) == int(config["population"]["causal_source_emoji_items"]), "Causal source count changed")
    _require(len(evaluation) == int(config["population"]["causal_eval_emoji_items"]), "Causal eval count changed")
    all_rows = [*observational, *source, *evaluation]
    _require(len({str(row["codepoint"]) for row in all_rows}) == len(all_rows), "Bank identity overlap")
    _require(len({str(row["alias_label"]) for row in all_rows}) == len(all_rows), "Alias uniqueness changed")
    for row in all_rows:
        _require(_words(str(row["canonical_label"])).isdisjoint(_words(str(row["alias_label"]))), "Alias disjointness changed")
    exposure_rescan = {"performed": False}
    if rescan_exposure:
        exposure = config["source_bindings"]["exposure_tree"]
        texts, _characters = _text_exposure(str(exposure["commit"]))
        hits = [
            {"codepoint": row["codepoint"], "paths": [path for path, text in texts.items() if str(row["glyph"]) in text]}
            for row in observational
            if row["kind"] == "symbol"
        ]
        _require(not any(row["paths"] for row in hits), "Selected symbol surface exposure changed")
        exposure_rescan = {"performed": True, "text_paths": len(texts), "symbol_hits": 0}
    for key in ("t10_freeze", "t18_result"):
        binding = config["source_bindings"][key]
        path = _root() / str(binding["path"])
        _require(_sha256(path) == str(binding["sha256"]), f"Bound source changed: {key}")
    return {
        "status": "pass",
        "observational_items": len(observational),
        "causal_source_items": len(source),
        "causal_eval_items": len(evaluation),
        "selection_sha256": _sha256(_root() / SELECTION_PATH),
        "exposure_rescan": exposure_rescan,
        "model_forward_calls": 0,
        "intervention_calls": 0,
    }


def resolved_layers(role: str) -> tuple[int, ...]:
    layers = int(t10._model_spec(role)["expected_num_layers"])
    return tuple(min(layers - 1, math.floor(value * layers)) for value in DEPTH_FRACTIONS)


def audit_design(output: Path | None = None) -> dict[str, Any]:
    config = _config()
    selection = audit_selection(rescan_exposure=True)
    _require(tuple(config["input"]["view_order"]) == VIEW_ORDER, "View order changed")
    _require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model order changed")
    _require(tuple(config["models"]["core_order"]) == CORE_ROLES, "Core order changed")
    expected_items = int(config["population"]["observational_items_per_kind"]) * 2
    expected_forwards = expected_items * len(VIEW_ORDER) * len(config["input"]["carrier_order"])
    expected_vectors = expected_items * len(VIEW_ORDER) * len(config["input"]["carrier_order"]) * len(config["input"]["distance_order"]) * len(DEPTH_FRACTIONS)
    acquisition = config["acquisition"]
    _require(expected_forwards == int(acquisition["expected_model_forward_calls_per_model"]), "Per-model forward count changed")
    _require(expected_vectors == int(acquisition["expected_readout_vectors_per_model"]), "Per-model vector count changed")
    _require(expected_forwards * len(MODEL_ROLES) == int(acquisition["expected_total_model_forward_calls"]), "Total forward count changed")
    primary_sites = config["causal_followup"]["primary_sites"]
    _require([(row["site"], int(row["block_index"])) for row in primary_sites] == [("attn_out", 24), ("mlp_out", 24)], "Causal primary sites changed")
    _require(int(config["causal_followup"]["subspace"]["rank"]) == 8, "Causal rank changed")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_pass_zero_t19_model_forwards_or_interventions",
        "selection_sha256": selection["selection_sha256"],
        "observational_items": expected_items,
        "causal_source_items": selection["causal_source_items"],
        "causal_eval_items": selection["causal_eval_items"],
        "model_roles": list(MODEL_ROLES),
        "core_roles": list(CORE_ROLES),
        "resolved_block_indices": {role: list(resolved_layers(role)) for role in MODEL_ROLES},
        "expected_model_forward_calls": int(acquisition["expected_total_model_forward_calls"]),
        "expected_readout_vectors": int(acquisition["expected_total_readout_vectors"]),
        "causal_primary_sites": primary_sites,
        "causal_secondary_sites": config["causal_followup"]["secondary_sites"],
        "causal_subspace_rank": 8,
        "causal_go_gate_open": False,
        "model_forwards": 0,
        "model_weights_loaded": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    if output is not None:
        _require(not output.exists(), f"Design preflight exists: {output}")
        _write_json(output, value)
    return value


def _sequence_hash(rows: Sequence[Sequence[int]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(json.dumps([int(value) for value in row], separators=(",", ":")).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _tokenizer_asset_hashes(snapshot: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json", "vocab.json", "merges.txt", "tokenizer.model"):
        path = snapshot / name
        if path.is_file():
            result[name] = _sha256(path.resolve())
    _require(result, f"No tokenizer assets found: {snapshot}")
    return result


def _strata_receipt(item_rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, Any]:
    by_kind: dict[str, dict[tuple[Any, ...], list[int]]] = {kind: defaultdict(list) for kind in KIND_ORDER}
    for row in item_rows:
        kind = str(row["glyph_kind"])
        by_kind[kind][tuple(row[field] for field in fields)].append(int(row["item_index"]))
    global_by_kind: dict[str, list[int]] = {}
    local_strata_by_kind: dict[str, list[list[int]]] = {}
    strata_by_kind: dict[str, list[dict[str, Any]]] = {}
    for kind in KIND_ORDER:
        groups = by_kind[kind]
        eligible_groups = [indices for _key, indices in sorted(groups.items()) if len(indices) >= 2]
        eligible = sorted(index for group in eligible_groups for index in group)
        lookup = {global_index: local for local, global_index in enumerate(eligible)}
        global_by_kind[kind] = eligible
        local_strata_by_kind[kind] = [[lookup[index] for index in group] for group in eligible_groups]
        strata_by_kind[kind] = [
            {"key": list(key), "global_item_indices": indices, "count": len(indices)}
            for key, indices in sorted(groups.items())
        ]
    union = sorted(index for kind in KIND_ORDER for index in global_by_kind[kind])
    return {
        "key_fields": list(fields),
        "eligible_item_count": len(union),
        "excluded_singleton_item_count": len(item_rows) - len(union),
        "eligible_item_count_by_kind": {kind: len(global_by_kind[kind]) for kind in KIND_ORDER},
        "eligible_global_indices_by_kind": global_by_kind,
        "eligible_local_strata_by_kind": local_strata_by_kind,
        "strata_by_kind": strata_by_kind,
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
            ids = [int(value) for value in tokenizer.encode(str(item[view]), add_special_tokens=False)]
            _require(ids, f"Empty tokenization: {item['codepoint']}/{view}")
            raw_by_view[view].append(ids)
            lengths[view] = len(ids)
        item_rows.append(
            {
                "item_index": item_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_kind": str(item["kind"]),
                "token_counts": lengths,
                "glyph_token_count": lengths["glyph"],
                "canonical_label_token_count": lengths["canonical_label"],
                "alias_label_token_count": lengths["alias_label"],
                "codepoint_literal_token_count": lengths["codepoint_literal"],
            }
        )
    for kind in KIND_ORDER:
        indices = [index for index, row in enumerate(population) if row["kind"] == kind]
        for view in VIEW_ORDER:
            _require(len({tuple(raw_by_view[view][index]) for index in indices}) == len(indices), f"Non-unique token sequence: {kind}/{view}")

    carrier_rows: dict[str, Any] = {}
    maximum_tokens = 0
    for carrier in config["input"]["carrier_order"]:
        carrier = str(carrier)
        spec = config["input"]["carriers"][carrier]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        unit_ids = [int(value) for value in tokenizer.encode(unit, add_special_tokens=False)]
        _require(len(unit_ids) == 1, f"Carrier is not one token: {carrier}")
        prefix_exact = 0
        decode_exact = 0
        for view in VIEW_ORDER:
            for item_index, item in enumerate(population):
                text = str(item[view]) + unit * repeats
                ids = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
                expected = raw_by_view[view][item_index] + unit_ids * repeats
                _require(ids == expected, f"Carrier boundary changed: {item['codepoint']}/{view}/{carrier}")
                combined[view][carrier].append(ids)
                prefix_exact += int(ids[:-repeats] == raw_by_view[view][item_index])
                decode_exact += int(tokenizer.decode(ids, clean_up_tokenization_spaces=False, skip_special_tokens=False) == text)
                maximum_tokens = max(maximum_tokens, len(ids))
        expected_cases = len(population) * len(VIEW_ORDER)
        _require(prefix_exact == expected_cases and decode_exact == expected_cases, f"Carrier compatibility failed: {carrier}")
        carrier_rows[carrier] = {
            "unit": unit,
            "repeats": repeats,
            "token_id": unit_ids[0],
            "prefix_exact_count": prefix_exact,
            "decode_exact_count": decode_exact,
        }
    primary = _strata_receipt(
        item_rows,
        ("glyph_token_count", "canonical_label_token_count", "alias_label_token_count", "codepoint_literal_token_count"),
    )
    guardrail = config["tokenization_guardrail"]
    _require(int(primary["eligible_item_count"]) >= int(guardrail["minimum_eligible_items_total"]), "Matched total below frozen minimum")
    for kind in KIND_ORDER:
        _require(int(primary["eligible_item_count_by_kind"][kind]) >= int(guardrail["minimum_eligible_items_per_kind"]), f"Matched coverage below minimum: {kind}")
    tuple_counts = {
        kind: Counter(
            tuple(row[field] for field in primary["key_fields"])
            for row in item_rows
            if row["glyph_kind"] == kind
        )
        for kind in KIND_ORDER
    }
    common_tuples = sorted(set(tuple_counts["emoji"]).intersection(tuple_counts["symbol"]))
    cross_kind = {
        "common_exact_tuples": [
            {"key": list(key), "emoji_count": int(tuple_counts["emoji"][key]), "symbol_count": int(tuple_counts["symbol"][key])}
            for key in common_tuples
        ],
        "emoji_items_in_common_tuples": sum(tuple_counts["emoji"][key] for key in common_tuples),
        "symbol_items_in_common_tuples": sum(tuple_counts["symbol"][key] for key in common_tuples),
        "decision_authorized": False,
    }
    receipt = {
        "item_count": len(population),
        "view_order": list(VIEW_ORDER),
        "item_token_counts": item_rows,
        "token_count_histograms": {
            view: {str(length): int(count) for length, count in sorted(Counter(len(ids) for ids in raw_by_view[view]).items())}
            for view in VIEW_ORDER
        },
        "ordered_sequence_sha256": {
            "raw": {view: _sequence_hash(raw_by_view[view]) for view in VIEW_ORDER},
            "combined": {
                view: {carrier: _sequence_hash(combined[view][carrier]) for carrier in config["input"]["carrier_order"]}
                for view in VIEW_ORDER
            },
        },
        "carriers": carrier_rows,
        "maximum_combined_token_count": maximum_tokens,
        "primary_exact_strata": primary,
        "cross_kind_common_exact_tuple_secondary": cross_kind,
    }
    return {"raw_ids": raw_by_view, "combined_ids": combined, "receipt": receipt}


def _tokenizer_receipt_path(role: str) -> Path:
    return _root() / TOKENIZER_DIRECTORY / f"{role}.json"


def tokenizer_preflight(role: str, model_path: Path, output: Path) -> dict[str, Any]:
    from transformers import AutoTokenizer

    _require(role in MODEL_ROLES, f"Unknown model role: {role}")
    audit_design()
    snapshot = model_path.resolve()
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False, use_fast=True)
    roster = _tokenize_roster(tokenizer)
    reference = t10._tokenize_roster(tokenizer, t10._config())["receipt"]
    frozen_reference = _read_json(t10._receipt_path(role))["tokenizer"]
    reference_exact = reference["ordered_sequence_sha256"] == frozen_reference["ordered_sequence_sha256"]
    _require(reference_exact, f"Tokenizer differs on complete T10 surface: {role}")
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_only_preflight_pass_zero_t19_model_forwards",
        "model_role": role,
        "artifact_model_id": t10._model_spec(role)["artifact_model_id"],
        "frozen_model_revision": t10._model_spec(role)["revision"],
        "preflight_snapshot_basename": snapshot.name,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": int(len(tokenizer)),
        "tokenizer_asset_sha256": _tokenizer_asset_hashes(snapshot),
        "t10_reference_surface_sequence_equivalence": True,
        "t10_reference_surface_receipt_sha256": _sha256(t10._receipt_path(role)),
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
        "matched_items": value["tokenizer"]["primary_exact_strata"]["eligible_item_count"],
        "matched_by_kind": value["tokenizer"]["primary_exact_strata"]["eligible_item_count_by_kind"],
        "cross_kind_common": value["tokenizer"]["cross_kind_common_exact_tuple_secondary"],
        "sha256": _sha256(output),
        "model_forward_calls": 0,
    }


def assemble_engineering_preflight(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(design.get("status") == "design_pass_zero_t19_model_forwards_or_interventions", "Design preflight incomplete")
    roles: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for role in MODEL_ROLES:
        path = _tokenizer_receipt_path(role)
        value = _read_json(path)
        _require(value.get("protocol_id") == PROTOCOL_ID and value.get("model_role") == role, f"Tokenizer receipt mismatch: {role}")
        _require(value.get("t10_reference_surface_sequence_equivalence") is True, f"Tokenizer reference mismatch: {role}")
        _require(int(value.get("model_forward_calls", -1)) == 0, f"Tokenizer preflight used a forward: {role}")
        primary = value["tokenizer"]["primary_exact_strata"]
        roles[role] = {
            "matched_items": int(primary["eligible_item_count"]),
            "matched_items_by_kind": {kind: int(primary["eligible_item_count_by_kind"][kind]) for kind in KIND_ORDER},
            "cross_kind_common_exact_tuple_secondary": value["tokenizer"]["cross_kind_common_exact_tuple_secondary"],
            "maximum_combined_token_count": int(value["tokenizer"]["maximum_combined_token_count"]),
        }
        hashes[role] = _sha256(path)
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "nine_tokenizer_preflights_pass_zero_t19_model_forwards",
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "tokenizer_receipt_sha256": hashes,
        "roles": roles,
        "minimum_matched_items": min(row["matched_items"] for row in roles.values()),
        "minimum_matched_items_by_kind": {kind: min(row["matched_items_by_kind"][kind] for row in roles.values()) for kind in KIND_ORDER},
        "model_forwards": 0,
        "model_weights_loaded": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _require(not output.exists(), f"Engineering preflight exists: {output}")
    _write_json(output, value)
    return {"status": "pass", "sha256": _sha256(output), "minimum_matched_items": value["minimum_matched_items"], "minimum_matched_items_by_kind": value["minimum_matched_items_by_kind"]}


def _static_assets() -> tuple[str, ...]:
    return (
        CONFIG_PATH.as_posix(),
        SELECTION_PATH.as_posix(),
        "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md",
        "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md",
        "scripts/t19_lexical_alias_unicode_control_v0.py",
        "scripts/t19_lexical_alias_component_causal_v0.py",
        "tests/test_t19_lexical_alias_unicode_control_v0.py",
        "tests/test_t19_lexical_alias_component_causal_v0.py",
        DESIGN_PREFLIGHT_PATH.as_posix(),
        ENGINEERING_PREFLIGHT_PATH.as_posix(),
        "validation/t19_lexical_alias_component_causal_v0/design_preflight.json",
        "validation/t19_lexical_alias_component_causal_v0/tokenizer_preflight.json",
    )


def _frozen_assets() -> tuple[str, ...]:
    bound = tuple(str(_config()["source_bindings"][key]["path"]) for key in ("t10_freeze", "t18_result"))
    tokenizers = tuple((TOKENIZER_DIRECTORY / f"{role}.json").as_posix() for role in MODEL_ROLES)
    return (*_static_assets(), *bound, *tokenizers)


def build_freeze(output: Path) -> dict[str, Any]:
    design = _read_json(_root() / DESIGN_PREFLIGHT_PATH)
    engineering = _read_json(_root() / ENGINEERING_PREFLIGHT_PATH)
    _require(design.get("status") == "design_pass_zero_t19_model_forwards_or_interventions", "Design incomplete")
    _require(engineering.get("status") == "nine_tokenizer_preflights_pass_zero_t19_model_forwards", "Engineering preflight incomplete")
    _require(int(design["model_forwards"]) == 0 and int(engineering["model_forwards"]) == 0, "Preflight used a model forward")
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        _require(path.is_file(), f"Frozen asset missing: {relative}")
        assets[relative] = _sha256(path)
    t10_freeze = _read_json(_root() / str(_config()["source_bindings"]["t10_freeze"]["path"]))
    value = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "final_execution_freeze_zero_t19_model_forwards_or_interventions",
        "experiment_label": _config()["experiment_label"],
        "claim_boundary": _config()["claim_boundary"],
        "frozen_assets": assets,
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "engineering_preflight_sha256": _sha256(_root() / ENGINEERING_PREFLIGHT_PATH),
        "tokenizer_receipt_sha256": engineering["tokenizer_receipt_sha256"],
        "model_artifacts": t10_freeze["model_artifacts"],
        "model_roles": list(MODEL_ROLES),
        "core_roles": list(CORE_ROLES),
        "observational_items": len(items()),
        "causal_source_items": len(causal_items("source")),
        "causal_eval_items": len(causal_items("eval")),
        "view_order": list(VIEW_ORDER),
        "glyph_kind_order": list(KIND_ORDER),
        "normalized_depth_fractions": list(DEPTH_FRACTIONS),
        "primary_normalized_depth_fractions": list(PRIMARY_DEPTHS),
        "resolved_block_indices": design["resolved_block_indices"],
        "causal_primary_sites": design["causal_primary_sites"],
        "causal_secondary_sites": design["causal_secondary_sites"],
        "causal_subspace_rank": design["causal_subspace_rank"],
        "model_forwards_at_freeze": 0,
        "causal_source_model_forwards_at_freeze": 0,
        "causal_eval_model_forwards_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "causal_go_gate_open_at_freeze": False,
        "exact_surface_holdout": False,
        "endpoint_and_alias_followup_is_prospective": True,
        "pretraining_or_semantic_holdout": False,
    }
    _require(not output.exists(), f"Freeze exists: {output}")
    _write_json(output, value)
    return {"status": "pass", "manifest_sha256": _sha256(output), "frozen_asset_count": len(assets), "model_forwards": 0}


def audit_freeze(*, require_pushed: bool = False) -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    value = _read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch")
    _require(value.get("status") == "final_execution_freeze_zero_t19_model_forwards_or_interventions", "Freeze status incomplete")
    _require(int(value.get("model_forwards_at_freeze", -1)) == 0 and int(value.get("intervention_calls_at_freeze", -1)) == 0, "Freeze used model compute")
    for relative, expected in value["frozen_assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"Frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"Frozen asset changed: {relative}")
    git = {"required": False}
    if require_pushed:
        head = _git_value("rev-parse", "HEAD")
        remote = _git_value("rev-parse", "origin/main")
        _require(head == remote, "T19 freeze commit is not pushed to origin/main")
        _git_value("cat-file", "-e", f"HEAD:{FREEZE_PATH.as_posix()}")
        git = {"required": True, "head": head, "origin_main": remote}
    return {"status": "pass", "freeze_manifest_sha256": _sha256(path), "git": git}


def _activate_engine() -> None:
    engine.PROTOCOL_ID = PROTOCOL_ID
    engine.CONFIG_PATH = CONFIG_PATH
    engine.SELECTION_PATH = SELECTION_PATH
    engine.VALIDATION_DIRECTORY = VALIDATION_DIRECTORY
    engine.DESIGN_PREFLIGHT_PATH = DESIGN_PREFLIGHT_PATH
    engine.TOKENIZER_DIRECTORY = TOKENIZER_DIRECTORY
    engine.ENGINEERING_PREFLIGHT_PATH = ENGINEERING_PREFLIGHT_PATH
    engine.FREEZE_PATH = FREEZE_PATH
    engine.VIEW_ORDER = VIEW_ORDER
    engine.SYSTEM_ORDER = KIND_ORDER
    engine.MODEL_ROLES = MODEL_ROLES
    engine.CORE_ROLES = CORE_ROLES
    engine.DEPTH_FRACTIONS = DEPTH_FRACTIONS
    engine.PRIMARY_DEPTHS = PRIMARY_DEPTHS
    engine.PRIMARY_DEPTH_INDICES = PRIMARY_DEPTH_INDICES
    engine.PAIR_ORDER = PAIR_ORDER
    engine._config = _config
    engine.items = items
    engine.audit_freeze = audit_freeze
    engine._tokenize_roster = _tokenize_roster
    engine._tokenizer_receipt_path = _tokenizer_receipt_path
    engine.resolved_layers = resolved_layers


def run_role(role: str, model_path: Path, output_root: Path) -> dict[str, Any]:
    _activate_engine()
    return engine.run_role(role, model_path, output_root)


def validate_role(role: str, output_root: Path) -> dict[str, Any]:
    _activate_engine()
    return engine.validate_role(role, output_root)


def audit_run(output_root: Path) -> dict[str, Any]:
    _activate_engine()
    return engine.audit_run(output_root)


def _metrics_for_views(values: np.ndarray) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    result: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    for name, left, right in PAIR_ORDER:
        metrics, forward, reverse = engine._pair_metrics(values[:, left], values[:, right])
        result[name] = metrics
        predictions[f"{name}_forward"] = forward
        predictions[f"{name}_reverse"] = reverse
    result["canonical_minus_codepoint"] = {key: float(result["glyph_canonical"][key] - result["glyph_codepoint"][key]) for key in result["glyph_canonical"]}
    result["alias_minus_codepoint"] = {key: float(result["glyph_alias"][key] - result["glyph_codepoint"][key]) for key in result["glyph_alias"]}
    result["alias_minus_canonical"] = {key: float(result["glyph_alias"][key] - result["glyph_canonical"][key]) for key in result["glyph_alias"]}
    return result, predictions


def _load_role_array(role: str, output_root: Path) -> np.ndarray:
    _activate_engine()
    return engine._load_role_array(role, output_root)


def summarize_role(role: str, output_root: Path, summary_root: Path) -> dict[str, Any]:
    validate_role(role, output_root)
    final = summary_root / role
    _require(not final.exists(), f"Summary exists: {final}")
    stage = summary_root / f".{role}.stage-{uuid.uuid4().hex}"
    stage.mkdir(parents=True)
    values = _load_role_array(role, output_root)
    population = items()
    token_receipt = _read_json(_tokenizer_receipt_path(role))["tokenizer"]
    indices_by_kind = {
        kind: np.asarray([index for index, item in enumerate(population) if item["kind"] == kind], dtype=np.int64)
        for kind in KIND_ORDER
    }
    matched_by_kind = {
        kind: np.asarray(token_receipt["primary_exact_strata"]["eligible_global_indices_by_kind"][kind], dtype=np.int64)
        for kind in KIND_ORDER
    }
    cell_rows: list[dict[str, Any]] = []
    prediction_lists: dict[str, list[np.ndarray]] = defaultdict(list)
    context_index = 0
    started = time.perf_counter()
    for depth_index, depth in enumerate(DEPTH_FRACTIONS):
        for carrier_index, carrier in enumerate(_config()["input"]["carrier_order"]):
            for distance_index, distance in enumerate(_config()["input"]["distance_order"]):
                for kind in KIND_ORDER:
                    global_indices = indices_by_kind[kind]
                    cell_values = np.asarray(values[global_indices, :, carrier_index, distance_index, depth_index, :])
                    unrestricted, predictions = _metrics_for_views(cell_values)
                    matched_indices = matched_by_kind[kind]
                    matched_values = np.asarray(values[matched_indices, :, carrier_index, distance_index, depth_index, :])
                    matched, matched_predictions = _metrics_for_views(matched_values)
                    cell_rows.append(
                        {
                            "model_role": role,
                            "normalized_depth": depth,
                            "resolved_block_index": resolved_layers(role)[depth_index],
                            "carrier": str(carrier),
                            "distance": int(distance),
                            "glyph_kind": kind,
                            "unrestricted_item_count": int(len(global_indices)),
                            "matched_item_count": int(len(matched_indices)),
                            "unrestricted": unrestricted,
                            "tokenization_matched": matched,
                        }
                    )
                    if depth_index in PRIMARY_DEPTH_INDICES:
                        for component, source in (("unrestricted", predictions), ("matched", matched_predictions)):
                            for target in ("canonical", "alias", "codepoint"):
                                prediction_lists[f"{component}__{kind}__{target}"].append(source[f"glyph_{target}_forward"])
                if depth_index in PRIMARY_DEPTH_INDICES:
                    context_index += 1
    _require(context_index == 24, "Primary context count changed")
    predictions_np = {key: np.stack(rows) for key, rows in prediction_lists.items()}
    for component in ("unrestricted", "matched"):
        for kind in KIND_ORDER:
            expected = len(indices_by_kind[kind]) if component == "unrestricted" else len(matched_by_kind[kind])
            for target in ("canonical", "alias", "codepoint"):
                _require(predictions_np[f"{component}__{kind}__{target}"].shape == (24, expected), f"Prediction shape changed: {component}/{kind}/{target}")
    _write_jsonl(stage / "cell_metrics.jsonl", cell_rows)
    np.savez_compressed(stage / "primary_predictions.npz", **predictions_np)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t19_role_summary_complete",
        "model_role": role,
        "cell_rows": len(cell_rows),
        "primary_contexts": context_index,
        "prediction_shapes": {key: list(value.shape) for key, value in predictions_np.items()},
        "matched_items_by_kind": {kind: len(matched_by_kind[kind]) for kind in KIND_ORDER},
        "source_role_receipt_sha256": _sha256(output_root / role / "role_receipt.json"),
        "freeze_manifest_sha256": audit_freeze()["freeze_manifest_sha256"],
        "elapsed_seconds": time.perf_counter() - started,
        "outputs": {
            "cell_metrics.jsonl": _sha256(stage / "cell_metrics.jsonl"),
            "primary_predictions.npz": _sha256(stage / "primary_predictions.npz"),
        },
    }
    _write_json(stage / "summary_receipt.json", receipt)
    engine._write_ledger(stage, ("cell_metrics.jsonl", "primary_predictions.npz", "summary_receipt.json"))
    os.replace(stage, final)
    return validate_summary(role, summary_root)


def validate_summary(role: str, summary_root: Path) -> dict[str, Any]:
    directory = summary_root / role
    receipt = _read_json(directory / "summary_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("model_role") == role, "Summary receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"Summary output changed: {role}/{name}")
    with np.load(directory / "primary_predictions.npz", allow_pickle=False) as values:
        _require(set(values.files) == set(receipt["prediction_shapes"]), f"Prediction keys changed: {role}")
        for key in values.files:
            _require(list(values[key].shape) == receipt["prediction_shapes"][key], f"Prediction shape changed: {role}/{key}")
    return {"status": "pass", "role": role, "cell_rows": int(receipt["cell_rows"]), "summary_sha256": _sha256(directory / "summary_receipt.json")}


def _effect(alias_predictions: np.ndarray, codepoint_predictions: np.ndarray) -> tuple[float, np.ndarray]:
    _require(alias_predictions.shape == codepoint_predictions.shape, "Prediction shape mismatch")
    order = np.arange(alias_predictions.shape[1])
    item_values = np.mean(alias_predictions == order[None, :], axis=0) - np.mean(codepoint_predictions == order[None, :], axis=0)
    return float(np.mean(item_values)), item_values.astype(np.float64)


def _randomization_test(
    alias_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
    strata: Sequence[Sequence[int]],
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    observed, _items = _effect(alias_predictions, codepoint_predictions)
    rng = np.random.default_rng(seed)
    count = alias_predictions.shape[1]
    base = np.arange(count)
    fixed_codepoint = np.mean(codepoint_predictions == base[None, :])
    exceedances = 0
    null_sum = 0.0
    null_sumsq = 0.0
    for _draw in range(draws):
        mapping = base.copy()
        for stratum in strata:
            indices = np.asarray(stratum, dtype=np.int64)
            mapping[indices] = rng.permutation(indices)
        statistic = float(np.mean(alias_predictions == mapping[None, :]) - fixed_codepoint)
        exceedances += int(statistic >= observed - 1e-15)
        null_sum += statistic
        null_sumsq += statistic * statistic
    mean = null_sum / draws
    variance = max(0.0, null_sumsq / draws - mean * mean)
    return {
        "observed": observed,
        "draws": draws,
        "seed": seed,
        "exceedances": exceedances,
        "p_value_one_sided": (1 + exceedances) / (draws + 1),
        "null_mean": mean,
        "null_sd": math.sqrt(variance),
    }


def _bootstrap_interval(item_values: np.ndarray, *, replicates: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    count = len(item_values)
    draws = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 500):
        stop = min(replicates, start + 500)
        indices = rng.integers(0, count, size=(stop - start, count))
        draws[start:stop] = np.mean(item_values[indices], axis=1)
    return {
        "replicates": replicates,
        "seed": seed,
        "lower_95": float(np.quantile(draws, 0.025)),
        "upper_95": float(np.quantile(draws, 0.975)),
        "bootstrap_mean": float(np.mean(draws)),
    }


def _holm(rows: Sequence[Mapping[str, Any]], alpha: float) -> list[dict[str, Any]]:
    ordered = sorted((dict(row) for row in rows), key=lambda row: (float(row["model_iut_p"]), str(row["model_role"])))
    still_rejecting = True
    result: list[dict[str, Any]] = []
    count = len(ordered)
    for index, row in enumerate(ordered):
        threshold = alpha / (count - index)
        reject = still_rejecting and float(row["model_iut_p"]) <= threshold
        still_rejecting = bool(reject)
        row["holm_rank"] = index + 1
        row["holm_threshold"] = threshold
        row["holm_reject"] = bool(reject and row["practical_pass"])
        result.append(row)
    return sorted(result, key=lambda row: MODEL_ROLES.index(str(row["model_role"])))


def analyze_summaries(summary_root: Path, output: Path) -> dict[str, Any]:
    _require(not output.exists(), f"Analysis output exists: {output}")
    config = _config()
    draws = int(config["model_primary_endpoint"]["randomization_draws"])
    bootstrap_replicates = int(config["model_primary_endpoint"]["descriptive_uncertainty"]["replicates"])
    seed_base = int(config["model_primary_endpoint"]["seed_base"])
    practical = float(config["model_primary_endpoint"]["practical_minimum"])
    model_rows: list[dict[str, Any]] = []
    depth_rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for role_index, role in enumerate(MODEL_ROLES):
        validate_summary(role, summary_root)
        receipt = _read_json(_tokenizer_receipt_path(role))["tokenizer"]
        with np.load(summary_root / role / "primary_predictions.npz", allow_pickle=False) as values:
            kind_components: dict[str, Any] = {}
            for kind_index, kind in enumerate(KIND_ORDER):
                components: dict[str, Any] = {}
                for component_index, component in enumerate(("unrestricted", "matched")):
                    alias = np.asarray(values[f"{component}__{kind}__alias"])
                    codepoint = np.asarray(values[f"{component}__{kind}__codepoint"])
                    canonical = np.asarray(values[f"{component}__{kind}__canonical"])
                    effect, item_values = _effect(alias, codepoint)
                    canonical_effect, canonical_items = _effect(canonical, codepoint)
                    alias_canonical = item_values - canonical_items
                    if component == "unrestricted":
                        strata = [list(range(alias.shape[1]))]
                    else:
                        strata = receipt["primary_exact_strata"]["eligible_local_strata_by_kind"][kind]
                    seed = seed_base + role_index * 100 + kind_index * 10 + component_index
                    randomization = _randomization_test(alias, codepoint, strata, draws=draws, seed=seed)
                    components[component] = {
                        "item_count": int(alias.shape[1]),
                        "alias_minus_codepoint_top1": effect,
                        "canonical_minus_codepoint_top1": canonical_effect,
                        "alias_minus_canonical_top1": float(np.mean(alias_canonical)),
                        "randomization": randomization,
                        "descriptive_interval": _bootstrap_interval(item_values, replicates=bootstrap_replicates, seed=seed + 1000),
                    }
                kind_components[kind] = components
            emoji = kind_components["emoji"]
            model_iut_p = max(float(emoji["unrestricted"]["randomization"]["p_value_one_sided"]), float(emoji["matched"]["randomization"]["p_value_one_sided"]))
            practical_pass = all(float(emoji[component]["alias_minus_codepoint_top1"]) >= practical for component in ("unrestricted", "matched"))
            model_rows.append(
                {
                    "model_role": role,
                    "kind_components": kind_components,
                    "emoji_minus_symbol_alias_codepoint_difference": {
                        component: float(kind_components["emoji"][component]["alias_minus_codepoint_top1"] - kind_components["symbol"][component]["alias_minus_codepoint_top1"])
                        for component in ("unrestricted", "matched")
                    },
                    "model_iut_p": model_iut_p,
                    "practical_pass": practical_pass,
                    "model_positive": bool(model_iut_p <= float(config["model_primary_endpoint"]["alpha"]) and practical_pass),
                }
            )
        for line in (summary_root / role / "cell_metrics.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            depth_rows.append(
                {
                    "model_role": role,
                    "normalized_depth": row["normalized_depth"],
                    "resolved_block_index": row["resolved_block_index"],
                    "carrier": row["carrier"],
                    "distance": row["distance"],
                    "glyph_kind": row["glyph_kind"],
                    "unrestricted_alias_minus_codepoint_top1": row["unrestricted"]["alias_minus_codepoint"]["top1_accuracy_forward"],
                    "matched_alias_minus_codepoint_top1": row["tokenization_matched"]["alias_minus_codepoint"]["top1_accuracy_forward"],
                    "unrestricted_canonical_minus_codepoint_top1": row["unrestricted"]["canonical_minus_codepoint"]["top1_accuracy_forward"],
                    "matched_canonical_minus_codepoint_top1": row["tokenization_matched"]["canonical_minus_codepoint"]["top1_accuracy_forward"],
                }
            )

    core = sorted((row for row in model_rows if row["model_role"] in CORE_ROLES), key=lambda row: float(row["model_iut_p"]))
    rth = float(core[2]["model_iut_p"])
    partial_p = min(1.0, 2.0 * rth)
    practical_count = sum(bool(row["model_positive"]) for row in core)
    cross_positive = partial_p <= float(config["cross_model_primary"]["alpha"]) and practical_count >= 3
    cross_model = {
        "id": config["cross_model_primary"]["id"],
        "core_roles": list(CORE_ROLES),
        "ordered_core_model_iut_p_values": [{"model_role": row["model_role"], "p_value": row["model_iut_p"]} for row in core],
        "rth_smallest_model_iut_p": rth,
        "partial_conjunction_p": partial_p,
        "core_model_positive_count": practical_count,
        "statistical_pass": partial_p <= float(config["cross_model_primary"]["alpha"]),
        "practical_pass": practical_count >= 3,
        "positive": cross_positive,
        "causal_go_gate_open": cross_positive,
    }
    bounded = _holm(model_rows, float(config["model_primary_endpoint"]["alpha"]))
    output.mkdir(parents=True)
    _write_json(output / "model_cell_results.json", {"schema_version": SCHEMA_VERSION, "protocol_id": PROTOCOL_ID, "models": bounded})
    _write_json(output / "cross_model_primary_result.json", {"schema_version": SCHEMA_VERSION, "protocol_id": PROTOCOL_ID, "cross_model_primary": cross_model})
    _write_json(output / "depth_profiles.json", {"schema_version": SCHEMA_VERSION, "protocol_id": PROTOCOL_ID, "rows": depth_rows})
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "t19_observational_analysis_complete",
        "model_cells": len(model_rows),
        "core_cells": len(core),
        "randomization_draws_per_component": draws,
        "bootstrap_replicates_per_component": bootstrap_replicates,
        "cross_model_primary_positive": cross_positive,
        "causal_go_gate_open": cross_positive,
        "claim_boundary": config["claim_boundary"],
        "elapsed_seconds": time.perf_counter() - started,
        "outputs": {
            name: _sha256(output / name)
            for name in ("model_cell_results.json", "cross_model_primary_result.json", "depth_profiles.json")
        },
        "raw_activations_committed": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json(output / "analysis_receipt.json", receipt)
    engine._write_ledger(output, ("model_cell_results.json", "cross_model_primary_result.json", "depth_profiles.json", "analysis_receipt.json"))
    return {"status": "pass", "cross_model_primary_positive": cross_positive, "causal_go_gate_open": cross_positive, "partial_conjunction_p": partial_p, "core_positive_count": practical_count, "analysis_receipt_sha256": _sha256(output / "analysis_receipt.json")}


def validate_analysis(directory: Path) -> dict[str, Any]:
    receipt = _read_json(directory / "analysis_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "t19_observational_analysis_complete", "Analysis receipt mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"Analysis output changed: {name}")
    cross = _read_json(directory / "cross_model_primary_result.json")["cross_model_primary"]
    _require(bool(cross["positive"]) == bool(receipt["cross_model_primary_positive"]), "Cross-model result mismatch")
    _require(bool(cross["causal_go_gate_open"]) == bool(receipt["causal_go_gate_open"]), "Causal gate mismatch")
    return {"status": "pass", "causal_go_gate_open": bool(cross["causal_go_gate_open"]), "analysis_receipt_sha256": _sha256(directory / "analysis_receipt.json")}


def _print(value: Mapping[str, Any]) -> None:
    print(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True))


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    sub = value.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-selection")
    build.add_argument("--source-directory", type=Path, required=True)
    build.add_argument("--output", type=Path, default=_root() / SELECTION_PATH)
    audit = sub.add_parser("audit-selection")
    audit.add_argument("--no-rescan-exposure", action="store_true")
    design = sub.add_parser("audit-design")
    design.add_argument("--output", type=Path)
    token = sub.add_parser("tokenizer-preflight")
    token.add_argument("--role", required=True, choices=MODEL_ROLES)
    token.add_argument("--model-path", type=Path, required=True)
    token.add_argument("--output", type=Path, required=True)
    engineering = sub.add_parser("assemble-engineering-preflight")
    engineering.add_argument("--output", type=Path, default=_root() / ENGINEERING_PREFLIGHT_PATH)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    freeze_audit = sub.add_parser("audit-freeze")
    freeze_audit.add_argument("--require-pushed", action="store_true")
    run = sub.add_parser("run-role")
    run.add_argument("--role", required=True, choices=MODEL_ROLES)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output-root", type=Path, required=True)
    run_audit = sub.add_parser("audit-run")
    run_audit.add_argument("--output-root", type=Path, required=True)
    summary = sub.add_parser("summarize-role")
    summary.add_argument("--role", required=True, choices=MODEL_ROLES)
    summary.add_argument("--output-root", type=Path, required=True)
    summary.add_argument("--summary-root", type=Path, required=True)
    summary_audit = sub.add_parser("validate-summary")
    summary_audit.add_argument("--role", required=True, choices=MODEL_ROLES)
    summary_audit.add_argument("--summary-root", type=Path, required=True)
    analysis = sub.add_parser("analyze-summaries")
    analysis.add_argument("--summary-root", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    analysis_audit = sub.add_parser("validate-analysis")
    analysis_audit.add_argument("--directory", type=Path, required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    if args.command == "build-selection":
        result = build_selection(args.source_directory, args.output)
    elif args.command == "audit-selection":
        result = audit_selection(rescan_exposure=not args.no_rescan_exposure)
    elif args.command == "audit-design":
        result = audit_design(args.output)
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(args.role, args.model_path, args.output)
    elif args.command == "assemble-engineering-preflight":
        result = assemble_engineering_preflight(args.output)
    elif args.command == "freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze(require_pushed=args.require_pushed)
    elif args.command == "run-role":
        result = run_role(args.role, args.model_path, args.output_root)
    elif args.command == "audit-run":
        result = audit_run(args.output_root)
    elif args.command == "summarize-role":
        result = summarize_role(args.role, args.output_root, args.summary_root)
    elif args.command == "validate-summary":
        result = validate_summary(args.role, args.summary_root)
    elif args.command == "analyze-summaries":
        result = analyze_summaries(args.summary_root, args.output)
    elif args.command == "validate-analysis":
        result = validate_analysis(args.directory)
    else:
        raise AssertionError(args.command)
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
