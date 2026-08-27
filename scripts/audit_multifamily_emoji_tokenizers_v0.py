#!/usr/bin/env python3
"""Run the frozen, tokenizer-only multifamily emoji census.

This script never loads model weights. It records every frozen tokenizer roster
entry, including load failures, and emits atomic machine-readable artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import json
import os
import platform
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


PROTOCOL_ID = "glyphprobe-multifamily-tokenizer-census-v0"
DEFAULT_CONFIG = Path("configs/multifamily_tokenizer_census_v0.yaml")
TOKENIZATION_FILENAME = "tokenizations.jsonl"
PAIRWISE_FILENAME = "pairwise_controls.jsonl"
SUMMARY_FILENAME = "summary.json"
RECEIPT_FILENAME = "receipt.json"
CHECKSUM_FILENAME = "SHA256SUMS"


class CensusError(RuntimeError):
    """Raised when the frozen census contract is violated."""


@dataclass(frozen=True)
class StaticAuthority:
    root: Path
    config_path: Path
    config: Mapping[str, Any]
    manifest_path: Path
    manifest: Mapping[str, Any]
    items: tuple[Mapping[str, Any], ...]
    contexts: tuple[Mapping[str, str], ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CensusError(message)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(value: Any, *, pretty: bool) -> bytes:
    indent = 2 if pretty else None
    separators = None if pretty else (",", ":")
    text = json.dumps(
        value,
        ensure_ascii=False,
        indent=indent,
        separators=separators,
        sort_keys=True,
    )
    return (text + "\n").encode("utf-8")


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.partial-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_json(path: Path, value: Any) -> None:
    _write_bytes_atomic(path, _json_bytes(value, pretty=True))


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    temporary = path.with_name(f".{path.name}.partial-{os.getpid()}")
    with temporary.open("wb") as handle:
        for row in rows:
            handle.write(_json_bytes(row, pretty=False))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_yaml(path: Path) -> Mapping[str, Any]:
    _require(path.is_file(), f"Missing YAML file: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"YAML root must be a mapping: {path}")
    return value


def _read_json(path: Path) -> Mapping[str, Any]:
    _require(path.is_file(), f"Missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"JSON root must be a mapping: {path}")
    return value


def _resolve_from(base: Path, value: str) -> Path:
    return (base / value).resolve()


def _validate_manifest_hashes(root: Path, manifest: Mapping[str, Any]) -> None:
    records = manifest.get("frozen_files")
    _require(isinstance(records, list) and records, "Manifest frozen_files missing")
    seen: set[str] = set()
    for record in records:
        _require(isinstance(record, dict), "Frozen file record must be a mapping")
        relative = record.get("path")
        expected = record.get("sha256")
        _require(isinstance(relative, str) and relative, "Frozen file path missing")
        _require(relative not in seen, f"Duplicate frozen file: {relative}")
        seen.add(relative)
        _require(
            isinstance(expected, str) and len(expected) == 64,
            f"Invalid frozen SHA-256: {relative}",
        )
        path = (root / relative).resolve()
        _require(path.is_file(), f"Frozen file missing: {relative}")
        _require(_sha256(path) == expected, f"Frozen SHA-256 differs: {relative}")


def _normalize_item(
    row: Mapping[str, Any], source: Mapping[str, Any], source_index: int
) -> Mapping[str, Any]:
    item_id = row.get("id")
    glyph = row.get("glyph")
    factors = row.get("factors") or {}
    labels = row.get("labels") or []
    _require(isinstance(item_id, str) and item_id, "Panel item id missing")
    _require(isinstance(glyph, str) and glyph, f"Panel glyph missing: {item_id}")
    _require(isinstance(factors, dict), f"Panel factors invalid: {item_id}")
    _require(
        isinstance(labels, list) and all(isinstance(label, str) for label in labels),
        f"Panel labels invalid: {item_id}",
    )

    if source.get("census_family_from_item"):
        family = factors.get("census_family")
    else:
        family = source.get("census_family")
    if source.get("construction_from_item"):
        construction = factors.get("construction")
    else:
        construction = source.get("construction")
    _require(isinstance(family, str) and family, f"Census family missing: {item_id}")
    _require(
        isinstance(construction, str) and construction,
        f"Construction missing: {item_id}",
    )

    base_id = factors.get("base_id")
    component_ids = factors.get("component_ids") or []
    _require(
        base_id is None or isinstance(base_id, str), f"base_id invalid: {item_id}"
    )
    _require(
        isinstance(component_ids, list)
        and all(isinstance(value, str) for value in component_ids),
        f"component_ids invalid: {item_id}",
    )

    return {
        "id": item_id,
        "glyph": glyph,
        "census_family": family,
        "construction": construction,
        "base_id": base_id,
        "component_ids": list(component_ids),
        "labels": list(labels),
        "source_panel_id": source["id"],
        "source_index": source_index,
        "codepoints": [f"U+{ord(character):04X}" for character in glyph],
        "codepoint_count": len(glyph),
        "utf8_hex": glyph.encode("utf-8").hex(),
        "contains_zwj": "\u200d" in glyph,
        "contains_vs16": "\ufe0f" in glyph,
    }


def load_static_authority(
    *, root: Path, config_path: Path, verify_manifest: bool = True
) -> StaticAuthority:
    root = root.resolve()
    config_path = config_path.resolve()
    config = _read_yaml(config_path)
    _require(config.get("protocol_id") == PROTOCOL_ID, "Protocol ID differs")

    manifest_value = config.get("manifest_path")
    _require(isinstance(manifest_value, str), "manifest_path missing")
    manifest_path = _resolve_from(config_path.parent, manifest_value)
    manifest = _read_json(manifest_path)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Manifest protocol differs")
    if verify_manifest:
        _validate_manifest_hashes(root, manifest)

    contexts_raw = (config.get("tokenization") or {}).get("contexts")
    _require(isinstance(contexts_raw, list) and contexts_raw, "Contexts missing")
    contexts: list[Mapping[str, str]] = []
    context_ids: set[str] = set()
    for context in contexts_raw:
        _require(isinstance(context, dict), "Context must be a mapping")
        context_id = context.get("id")
        template = context.get("template")
        _require(
            isinstance(context_id, str) and context_id not in context_ids,
            "Context ID missing or duplicated",
        )
        _require(
            isinstance(template, str) and template.count("{item}") == 1,
            f"Context template invalid: {context_id}",
        )
        context_ids.add(context_id)
        contexts.append({"id": context_id, "template": template})

    pairwise_contexts = (config.get("pairwise_controls") or {}).get("contexts")
    _require(
        isinstance(pairwise_contexts, list)
        and pairwise_contexts
        and set(pairwise_contexts).issubset(context_ids),
        "Pairwise context IDs are invalid",
    )

    sources = config.get("panel_sources")
    _require(isinstance(sources, list) and sources, "Panel sources missing")
    items: list[Mapping[str, Any]] = []
    for source in sources:
        _require(isinstance(source, dict), "Panel source must be a mapping")
        source_id = source.get("id")
        relative = source.get("path")
        expected = source.get("expected_items")
        _require(isinstance(source_id, str) and source_id, "Panel source id missing")
        _require(isinstance(relative, str), f"Panel path missing: {source_id}")
        _require(isinstance(expected, int) and expected > 0, "Panel count invalid")
        panel_path = _resolve_from(config_path.parent, relative)
        panel = _read_yaml(panel_path)
        rows = panel.get("items")
        _require(
            isinstance(rows, list) and len(rows) == expected,
            f"Panel item count differs: {source_id}",
        )
        for index, row in enumerate(rows):
            _require(isinstance(row, dict), f"Panel row invalid: {source_id}/{index}")
            items.append(_normalize_item(row, source, index))

    expected_total = config.get("expected_total_items")
    _require(
        isinstance(expected_total, int) and len(items) == expected_total,
        "Total panel item count differs",
    )
    ids = [str(item["id"]) for item in items]
    glyphs = [str(item["glyph"]) for item in items]
    _require(len(ids) == len(set(ids)), "Panel item IDs overlap")
    _require(len(glyphs) == len(set(glyphs)), "Panel glyph strings overlap")
    item_ids = set(ids)
    for item in items:
        base_id = item["base_id"]
        if base_id is not None:
            _require(base_id in item_ids and base_id != item["id"], f"Invalid base: {item['id']}")
        for component_id in item["component_ids"]:
            _require(
                component_id in item_ids and component_id != item["id"],
                f"Invalid component: {item['id']}/{component_id}",
            )

    rosters = config.get("node_rosters")
    _require(isinstance(rosters, dict) and rosters, "Node rosters missing")
    for node, roster in rosters.items():
        _require(isinstance(node, str) and node, "Node roster ID invalid")
        _require(isinstance(roster, list) and roster, f"Node roster empty: {node}")
        labels = [entry.get("label") for entry in roster if isinstance(entry, dict)]
        _require(
            len(labels) == len(roster)
            and all(isinstance(label, str) and label for label in labels)
            and len(labels) == len(set(labels)),
            f"Node roster labels invalid: {node}",
        )

    forbidden = config.get("forbidden_research_inputs")
    _require(
        isinstance(forbidden, list)
        and "data/targets/p2_confirmatory_targets_v1.jsonl" in forbidden
        and "data/targets/c1_causal_holdout_targets_v1.jsonl" in forbidden,
        "Protected target exclusions are not explicit",
    )

    static_counts = manifest.get("static_counts")
    _require(isinstance(static_counts, dict), "Manifest static counts missing")
    _require(static_counts.get("panel_items") == len(items), "Manifest panel count differs")
    _require(
        static_counts.get("contexts") == len(contexts),
        "Manifest context count differs",
    )
    _require(
        static_counts.get("unordered_item_pairs") == len(items) * (len(items) - 1) // 2,
        "Manifest pair count differs",
    )
    _require(manifest.get("node_rosters") == rosters, "Manifest node rosters differ")
    contract = manifest.get("tokenization_contract")
    _require(isinstance(contract, dict), "Manifest tokenization contract missing")
    _require(
        contract.get("context_ids") == [context["id"] for context in contexts],
        "Manifest context order differs",
    )
    _require(
        contract.get("pairwise_context_ids") == pairwise_contexts,
        "Manifest pairwise context order differs",
    )
    _require(contract.get("retain_all_pairs") is True, "All-pairs rule is not frozen")
    _require(
        contract.get("retain_roster_failures") is True,
        "Roster-failure retention is not frozen",
    )
    _require(contract.get("model_forward_calls") == 0, "Model-forward count is not zero")
    _require(
        manifest.get("expected_outputs")
        == [
            TOKENIZATION_FILENAME,
            PAIRWISE_FILENAME,
            SUMMARY_FILENAME,
            RECEIPT_FILENAME,
            CHECKSUM_FILENAME,
        ],
        "Manifest output filenames differ",
    )
    frozen_paths = {record["path"] for record in manifest["frozen_files"]}
    _require(not frozen_paths.intersection(forbidden), "Protected input frozen by manifest")

    return StaticAuthority(
        root=root,
        config_path=config_path,
        config=config,
        manifest_path=manifest_path,
        manifest=manifest,
        items=tuple(items),
        contexts=tuple(contexts),
    )


def _parse_tokenizer_arguments(values: Sequence[str]) -> Mapping[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        label, separator, raw_path = value.partition("=")
        _require(separator == "=" and label and raw_path, f"Invalid --tokenizer: {value}")
        _require(label not in parsed, f"Duplicate tokenizer label: {label}")
        parsed[label] = Path(raw_path).expanduser().resolve()
    return parsed


def _roster_for_node(authority: StaticAuthority, node: str) -> tuple[Mapping[str, str], ...]:
    rosters = authority.config["node_rosters"]
    _require(node in rosters, f"Unknown node roster: {node}")
    return tuple(dict(entry) for entry in rosters[node])


def _asset_hashes(path: Path) -> Mapping[str, str]:
    if not path.is_dir():
        return {}
    names = {
        "added_tokens.json",
        "chat_template.jinja",
        "config.json",
        "merges.txt",
        "special_tokens_map.json",
        "vocab.json",
    }
    records: dict[str, str] = {}
    for candidate in sorted(path.iterdir(), key=lambda value: value.name):
        if not candidate.is_file():
            continue
        if candidate.name.startswith("tokenizer") or candidate.name in names:
            records[candidate.name] = _sha256(candidate)
    return records


def _snapshot_revision(path: Path) -> str | None:
    parts = path.parts
    if "snapshots" not in parts:
        return None
    index = parts.index("snapshots")
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def _config_model_type(path: Path) -> str | None:
    config_path = path / "config.json"
    if not config_path.is_file():
        return None
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    model_type = value.get("model_type") if isinstance(value, dict) else None
    return model_type if isinstance(model_type, str) else None


def _load_tokenizer(path: Path, tokenization: Mapping[str, Any]) -> Any:
    _require(path.is_dir(), f"Tokenizer path is not a directory: {path}")
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(path),
        local_files_only=bool(tokenization["local_files_only"]),
        use_fast=bool(tokenization["use_fast"]),
        trust_remote_code=bool(tokenization["trust_remote_code"]),
    )
    _require(bool(getattr(tokenizer, "is_fast", False)), "Tokenizer is not fast")
    return tokenizer


def _decode(tokenizer: Any, token_ids: Sequence[int]) -> str:
    try:
        return tokenizer.decode(
            list(token_ids),
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
    except TypeError:
        return tokenizer.decode(list(token_ids), skip_special_tokens=False)


def tokenize_item(
    *,
    tokenizer: Any,
    tokenizer_label: str,
    node: str,
    item: Mapping[str, Any],
    context: Mapping[str, str],
) -> Mapping[str, Any]:
    prefix, suffix = context["template"].split("{item}")
    glyph = str(item["glyph"])
    text = f"{prefix}{glyph}{suffix}"
    span_start = len(prefix)
    span_end = span_start + len(glyph)
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_attention_mask=False,
        return_offsets_mapping=True,
        return_token_type_ids=False,
    )
    token_ids = [int(value) for value in encoded["input_ids"]]
    offsets = [[int(start), int(end)] for start, end in encoded["offset_mapping"]]
    _require(len(token_ids) == len(offsets), "Token IDs and offsets differ")
    pieces = [str(value) for value in tokenizer.convert_ids_to_tokens(token_ids)]
    _require(len(pieces) == len(token_ids), "Token pieces and IDs differ")
    span_positions = [
        index
        for index, (start, end) in enumerate(offsets)
        if end > span_start and start < span_end
    ]
    _require(span_positions, f"No token overlaps item span: {item['id']}/{context['id']}")
    span_ids = [token_ids[index] for index in span_positions]
    span_pieces = [pieces[index] for index in span_positions]
    decoded = _decode(tokenizer, token_ids)

    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "node": node,
        "tokenizer_label": tokenizer_label,
        "item_id": item["id"],
        "census_family": item["census_family"],
        "construction": item["construction"],
        "base_id": item["base_id"],
        "component_ids": item["component_ids"],
        "source_panel_id": item["source_panel_id"],
        "context_id": context["id"],
        "glyph": glyph,
        "codepoints": item["codepoints"],
        "codepoint_count": item["codepoint_count"],
        "utf8_hex": item["utf8_hex"],
        "contains_zwj": item["contains_zwj"],
        "contains_vs16": item["contains_vs16"],
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "item_char_span": [span_start, span_end],
        "token_ids": token_ids,
        "token_pieces": pieces,
        "offset_mapping": offsets,
        "whole_token_count": len(token_ids),
        "span_token_positions": span_positions,
        "span_token_ids": span_ids,
        "span_token_pieces": span_pieces,
        "span_token_count": len(span_ids),
        "decoded_text": decoded,
        "roundtrip_exact": decoded == text,
    }


def _common_prefix_length(left: Sequence[int], right: Sequence[int]) -> int:
    count = 0
    for left_value, right_value in zip(left, right, strict=False):
        if left_value != right_value:
            break
        count += 1
    return count


def build_pairwise_rows(
    *,
    authority: StaticAuthority,
    successful_labels: Sequence[str],
    tokenizations: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    wanted_contexts = list(authority.config["pairwise_controls"]["contexts"])
    lookup = {
        (row["tokenizer_label"], row["item_id"], row["context_id"]): row
        for row in tokenizations
    }
    rows: list[Mapping[str, Any]] = []
    for left, right in itertools.combinations(authority.items, 2):
        context_records: dict[str, Any] = {}
        for context_id in wanted_contexts:
            equal_count_labels: list[str] = []
            same_first_labels: list[str] = []
            same_first_two_labels: list[str] = []
            exact_sequence_labels: list[str] = []
            prefix_lengths: dict[str, int] = {}
            for label in successful_labels:
                left_row = lookup[(label, left["id"], context_id)]
                right_row = lookup[(label, right["id"], context_id)]
                left_ids = left_row["span_token_ids"]
                right_ids = right_row["span_token_ids"]
                prefix = _common_prefix_length(left_ids, right_ids)
                prefix_lengths[label] = prefix
                if len(left_ids) == len(right_ids):
                    equal_count_labels.append(label)
                if prefix >= 1:
                    same_first_labels.append(label)
                if prefix >= 2:
                    same_first_two_labels.append(label)
                if left_ids == right_ids:
                    exact_sequence_labels.append(label)
            denominator = len(successful_labels)
            context_records[context_id] = {
                "successful_tokenizer_count": denominator,
                "equal_token_count_labels": equal_count_labels,
                "same_first_token_labels": same_first_labels,
                "same_first_two_token_labels": same_first_two_labels,
                "exact_sequence_labels": exact_sequence_labels,
                "shared_prefix_lengths": prefix_lengths,
                "all_equal_token_count": len(equal_count_labels) == denominator,
                "same_first_token_fraction": (
                    len(same_first_labels) / denominator if denominator else None
                ),
            }
        rows.append(
            {
                "schema_version": 1,
                "protocol_id": PROTOCOL_ID,
                "node": None,
                "left_item_id": left["id"],
                "left_family": left["census_family"],
                "left_construction": left["construction"],
                "right_item_id": right["id"],
                "right_family": right["census_family"],
                "right_construction": right["construction"],
                "contexts": context_records,
            }
        )
    return rows


def build_summary(
    *,
    authority: StaticAuthority,
    node: str,
    successful_labels: Sequence[str],
    tokenizer_results: Sequence[Mapping[str, Any]],
    tokenizations: Sequence[Mapping[str, Any]],
    pairwise_rows: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    raw_rows = [row for row in tokenizations if row["context_id"] == "raw"]
    raw_lookup = {
        (row["tokenizer_label"], row["item_id"]): row for row in raw_rows
    }
    family_histograms: dict[str, Any] = {}
    for label in successful_labels:
        by_family: dict[str, Counter[int]] = defaultdict(Counter)
        for row in raw_rows:
            if row["tokenizer_label"] == label:
                by_family[str(row["census_family"])][int(row["span_token_count"])] += 1
        family_histograms[label] = {
            family: {str(count): frequency for count, frequency in sorted(hist.items())}
            for family, hist in sorted(by_family.items())
        }

    item_ranges: list[Mapping[str, Any]] = []
    relation_deltas: list[Mapping[str, Any]] = []
    for item in authority.items:
        counts = {
            label: int(raw_lookup[(label, item["id"])]["span_token_count"])
            for label in successful_labels
        }
        values = list(counts.values())
        item_ranges.append(
            {
                "item_id": item["id"],
                "census_family": item["census_family"],
                "construction": item["construction"],
                "token_counts": counts,
                "minimum": min(values) if values else None,
                "maximum": max(values) if values else None,
                "range": max(values) - min(values) if values else None,
            }
        )
        if item["base_id"] is not None:
            relation_deltas.append(
                {
                    "relation": "base_delta",
                    "item_id": item["id"],
                    "reference_ids": [item["base_id"]],
                    "token_count_delta": {
                        label: counts[label]
                        - int(raw_lookup[(label, item["base_id"])]["span_token_count"])
                        for label in successful_labels
                    },
                }
            )
        if item["component_ids"]:
            relation_deltas.append(
                {
                    "relation": "component_sum_gap",
                    "item_id": item["id"],
                    "reference_ids": item["component_ids"],
                    "token_count_delta": {
                        label: counts[label]
                        - sum(
                            int(raw_lookup[(label, component_id)]["span_token_count"])
                            for component_id in item["component_ids"]
                        )
                        for label in successful_labels
                    },
                }
            )

    all_context_equal_pairs = 0
    for row in pairwise_rows:
        contexts = row["contexts"]
        if all(value["all_equal_token_count"] for value in contexts.values()):
            all_context_equal_pairs += 1

    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "node": node,
        "analysis_role": "descriptive_tokenizer_structure_only",
        "claim_boundary": authority.config["claim_boundary"],
        "panel_item_count": len(authority.items),
        "context_count": len(authority.contexts),
        "roster_count": len(tokenizer_results),
        "successful_tokenizer_count": len(successful_labels),
        "tokenizer_results": list(tokenizer_results),
        "raw_family_token_count_histograms": family_histograms,
        "cross_tokenizer_item_ranges": item_ranges,
        "relation_token_count_deltas": relation_deltas,
        "pairwise_row_count": len(pairwise_rows),
        "pairs_equal_count_in_all_reported_contexts": all_context_equal_pairs,
        "interpretation_limits": [
            "Token IDs are compared only within a tokenizer, never across vocabularies.",
            "Equal token counts or shared prefixes do not establish semantic matching.",
            "Tokenizer structure does not establish activation, behavior, mechanism, or causality.",
        ],
    }


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_census(
    *, authority: StaticAuthority, node: str, output: Path, tokenizer_paths: Mapping[str, Path]
) -> int:
    roster = _roster_for_node(authority, node)
    expected_labels = [entry["label"] for entry in roster]
    _require(
        set(tokenizer_paths) == set(expected_labels),
        "Provided tokenizer labels must exactly match the frozen node roster",
    )
    output = output.expanduser().resolve()
    _require(not output.exists(), f"Output path already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".incoming-{output.name}-{os.getpid()}"
    _require(not staging.exists(), f"Staging path already exists: {staging}")
    staging.mkdir()

    started_at = _utc_now()
    tokenization_config = authority.config["tokenization"]
    tokenizer_results: list[Mapping[str, Any]] = []
    tokenizations: list[Mapping[str, Any]] = []
    successful_labels: list[str] = []
    exit_code = 0
    try:
        for roster_entry in roster:
            label = str(roster_entry["label"])
            path = tokenizer_paths[label]
            result: dict[str, Any] = {
                "label": label,
                "canonical_model_id": roster_entry["canonical_model_id"],
                "local_path": str(path),
                "snapshot_revision": _snapshot_revision(path),
                "model_type": _config_model_type(path),
                "asset_sha256": _asset_hashes(path),
            }
            try:
                tokenizer = _load_tokenizer(path, tokenization_config)
                tokenizer_rows: list[Mapping[str, Any]] = []
                result.update(
                    {
                        "status": "success",
                        "tokenizer_class": type(tokenizer).__name__,
                        "is_fast": bool(tokenizer.is_fast),
                        "vocab_size": int(getattr(tokenizer, "vocab_size", -1)),
                        "tokenizer_length": int(len(tokenizer)),
                    }
                )
                for item in authority.items:
                    for context in authority.contexts:
                        tokenizer_rows.append(
                            tokenize_item(
                                tokenizer=tokenizer,
                                tokenizer_label=label,
                                node=node,
                                item=item,
                                context=context,
                            )
                        )
                tokenizations.extend(tokenizer_rows)
                successful_labels.append(label)
            except Exception as exc:  # failure retention is part of the protocol
                result.update(
                    {
                        "status": "failure",
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:2000],
                    }
                )
                exit_code = 1
            tokenizer_results.append(result)

        tokenizations.sort(
            key=lambda row: (
                expected_labels.index(row["tokenizer_label"]),
                next(
                    index
                    for index, item in enumerate(authority.items)
                    if item["id"] == row["item_id"]
                ),
                next(
                    index
                    for index, context in enumerate(authority.contexts)
                    if context["id"] == row["context_id"]
                ),
            )
        )
        pairwise_rows = build_pairwise_rows(
            authority=authority,
            successful_labels=successful_labels,
            tokenizations=tokenizations,
        )
        for row in pairwise_rows:
            row["node"] = node
        summary = build_summary(
            authority=authority,
            node=node,
            successful_labels=successful_labels,
            tokenizer_results=tokenizer_results,
            tokenizations=tokenizations,
            pairwise_rows=pairwise_rows,
        )

        _write_jsonl(staging / TOKENIZATION_FILENAME, tokenizations)
        _write_jsonl(staging / PAIRWISE_FILENAME, pairwise_rows)
        _write_json(staging / SUMMARY_FILENAME, summary)
        data_hashes = {
            name: _sha256(staging / name)
            for name in [TOKENIZATION_FILENAME, PAIRWISE_FILENAME, SUMMARY_FILENAME]
        }
        receipt = {
            "schema_version": 1,
            "protocol_id": PROTOCOL_ID,
            "node": node,
            "status": (
                "complete"
                if len(successful_labels) == len(roster)
                else "complete_with_failures"
                if successful_labels
                else "failed_no_tokenizer_loaded"
            ),
            "started_at": started_at,
            "completed_at": _utc_now(),
            "role": "tokenizer_only_structural_census",
            "claim_boundary": authority.config["claim_boundary"],
            "model_forward_calls": 0,
            "protected_target_files_opened": 0,
            "config": {
                "path": str(authority.config_path.relative_to(authority.root)),
                "sha256": _sha256(authority.config_path),
            },
            "manifest": {
                "path": str(authority.manifest_path.relative_to(authority.root)),
                "sha256": _sha256(authority.manifest_path),
            },
            "script": {
                "path": str(Path(__file__).resolve().relative_to(authority.root)),
                "sha256": _sha256(Path(__file__).resolve()),
            },
            "environment": {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "python": platform.python_version(),
                "transformers": _package_version("transformers"),
                "tokenizers": _package_version("tokenizers"),
            },
            "frozen_roster_labels": expected_labels,
            "successful_labels": successful_labels,
            "tokenizer_results": tokenizer_results,
            "row_counts": {
                TOKENIZATION_FILENAME: len(tokenizations),
                PAIRWISE_FILENAME: len(pairwise_rows),
            },
            "output_sha256": data_hashes,
        }
        _write_json(staging / RECEIPT_FILENAME, receipt)
        all_names = [
            TOKENIZATION_FILENAME,
            PAIRWISE_FILENAME,
            SUMMARY_FILENAME,
            RECEIPT_FILENAME,
        ]
        checksum_lines = [
            f"{_sha256(staging / name)}  {name}" for name in sorted(all_names)
        ]
        _write_bytes_atomic(
            staging / CHECKSUM_FILENAME, ("\n".join(checksum_lines) + "\n").encode("utf-8")
        )
        os.replace(staging, output)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    if not successful_labels:
        return 2
    return exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--node", choices=("mac1", "mac2", "furnace"))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--tokenizer",
        action="append",
        default=[],
        metavar="LABEL=PATH",
        help="Frozen roster label and local tokenizer directory; repeat per label.",
    )
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    config_path = args.config
    if not config_path.is_absolute():
        config_path = root / config_path
    try:
        authority = load_static_authority(root=root, config_path=config_path)
        if args.validate_only:
            print(
                json.dumps(
                    {
                        "status": "valid",
                        "protocol_id": PROTOCOL_ID,
                        "panel_item_count": len(authority.items),
                        "context_count": len(authority.contexts),
                        "node_roster_counts": {
                            node: len(entries)
                            for node, entries in authority.config["node_rosters"].items()
                        },
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        _require(args.node is not None, "--node is required")
        _require(args.output is not None, "--output is required")
        tokenizer_paths = _parse_tokenizer_arguments(args.tokenizer)
        return run_census(
            authority=authority,
            node=args.node,
            output=args.output,
            tokenizer_paths=tokenizer_paths,
        )
    except (CensusError, OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
