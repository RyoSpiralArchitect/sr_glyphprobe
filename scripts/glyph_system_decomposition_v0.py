#!/usr/bin/env python3
"""Freeze and run the T11 glyph-system decomposition atlas.

T11 is a discovery-only observational study.  It acquires standards-defined
multi-codepoint emoji systems plus prior-exposed atomic anchors across the same
nine frozen model/tokenizer cells as T10.  It performs no intervention or
generation, and it never forwards the separately selected T11 reserve.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import re
import sys
import tempfile
import time
import unicodedata
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-glyph-system-decomposition-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/glyph_system_decomposition_v0.yaml")
SELECTION_PATH = Path("data/manifests/glyph_system_decomposition_selection_v0.json")
DESIGN_PREFLIGHT_PATH = Path(
    "validation/glyph_system_decomposition_v0/design_preflight.json"
)
FREEZE_PATH = Path("data/manifests/glyph_system_decomposition_v0.json")
VIEW_ORDER = (
    "glyph",
    "unicode_name",
    "component_name",
    "codepoint_literal",
    "decomposed_form",
)
BROAD_ENDPOINT_ORDER = (
    "raw_last_decoder_block_output",
    "returned_final_hidden_state",
)
DEPTH_ENDPOINT_ORDER = (
    "embedding_output",
    "interblock_depth_0p25",
    "interblock_depth_0p50",
    "interblock_depth_0p75",
    "raw_last_decoder_block_output",
    "returned_final_hidden_state",
)
EMOJI_LINE_RE = re.compile(
    r"^(?P<codepoints>[0-9A-F ]+)\s*;\s*(?P<status>[a-z-]+)\s*#\s*"
    r"(?P<glyph>\S+)\s+E(?P<emoji_version>[0-9.]+)\s+(?P<name>.+)$"
)
STATIC_FROZEN_ASSETS = (
    "configs/glyph_system_decomposition_v0.yaml",
    "data/manifests/glyph_system_decomposition_selection_v0.json",
    "docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md",
    "docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md",
    "scripts/glyph_system_decomposition_v0.py",
    "tests/test_glyph_system_decomposition_v0.py",
    "validation/glyph_system_decomposition_v0/design_preflight.json",
)


class T11Error(RuntimeError):
    """Raised when a frozen T11 invariant fails."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T11Error(message)


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T11 config mismatch")
    _require(tuple(value["views"]["order"]) == VIEW_ORDER, "T11 view order changed")
    _require(
        tuple(value["endpoints"]["broad_order"]) == BROAD_ENDPOINT_ORDER,
        "T11 broad endpoint order changed",
    )
    _require(
        tuple(value["endpoints"]["depth_order"]) == DEPTH_ENDPOINT_ORDER,
        "T11 depth endpoint order changed",
    )
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial-{uuid.uuid4().hex}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _validate_ledger(directory: Path, expected_names: Sequence[str]) -> dict[str, str]:
    ledger = directory / "SHA256SUMS"
    _require(ledger.is_file(), f"Missing T11 ledger: {ledger}")
    observed: dict[str, str] = {}
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, name = raw.split(maxsplit=1)
        relative = Path(name.lstrip("*"))
        _require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe T11 ledger path: {relative}",
        )
        normalized = relative.as_posix()
        _require(normalized not in observed, f"Duplicate T11 ledger row: {normalized}")
        _require((directory / relative).is_file(), f"Missing T11 ledger target: {normalized}")
        _require(_sha256(directory / relative) == digest, f"T11 ledger mismatch: {normalized}")
        observed[normalized] = digest
    _require(set(observed) == set(expected_names), "T11 ledger file roster changed")
    return observed


def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


def _model_spec(role: str) -> dict[str, Any]:
    _require(role in model_roles(), f"Unknown T11 model role: {role}")
    return t10._model_spec(role)


def _classify_system(codepoints: Sequence[int]) -> str:
    values = tuple(int(value) for value in codepoints)
    if len(values) == 1:
        return "atomic_anchor"
    if 0x20E3 in values:
        return "keycap"
    if len(values) == 2 and all(0x1F1E6 <= value <= 0x1F1FF for value in values):
        return "regional_flag"
    if 0xE007F in values:
        return "tag_flag"
    if 0x200D in values:
        return "zwj"
    if any(0x1F3FB <= value <= 0x1F3FF for value in values):
        return "modifier"
    if 0xFE0F in values or 0xFE0E in values:
        return "presentation"
    raise T11Error(f"Unclassified fully-qualified sequence: {values}")


def _parse_unicode_source(source: bytes) -> dict[str, Any]:
    text = source.decode("utf-8")
    version = ""
    group = ""
    subgroup = ""
    all_rows: list[dict[str, Any]] = []
    fully_qualified: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.startswith("# Version:"):
            version = line.split(":", 1)[1].strip()
        elif line.startswith("# group:"):
            group = line.split(":", 1)[1].strip()
        elif line.startswith("# subgroup:"):
            subgroup = line.split(":", 1)[1].strip()
        else:
            match = EMOJI_LINE_RE.match(line)
            if match is None:
                continue
            raw = match.groupdict()
            codepoints = tuple(int(value, 16) for value in raw["codepoints"].split())
            row = {
                "codepoints": codepoints,
                "codepoint": " ".join(f"{value:04X}" for value in codepoints),
                "glyph": raw["glyph"],
                "name": raw["name"],
                "emoji_version": raw["emoji_version"],
                "status": raw["status"],
                "group": group,
                "subgroup": subgroup,
            }
            all_rows.append(row)
            if raw["status"] == "fully-qualified":
                fully_qualified.append(row)
    _require(bool(version) and bool(fully_qualified), "Unicode source did not parse")
    return {
        "version": version,
        "all_rows": all_rows,
        "fully_qualified": fully_qualified,
    }


def _name_map(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[int, ...], str]:
    priority = {"component": 0, "fully-qualified": 1, "minimally-qualified": 2, "unqualified": 3}
    selected: dict[tuple[int, ...], tuple[int, str]] = {}
    for row in rows:
        key = tuple(int(value) for value in row["codepoints"])
        rank = priority.get(str(row["status"]), 9)
        if key not in selected or rank < selected[key][0]:
            selected[key] = (rank, str(row["name"]))
    return {key: value[1] for key, value in selected.items()}


def _scalar_label(value: int, names: Mapping[tuple[int, ...], str]) -> str:
    if 0x1F1E6 <= value <= 0x1F1FF:
        return f"letter {chr(ord('A') + value - 0x1F1E6)}"
    if 0xE0061 <= value <= 0xE007A:
        return f"tag letter {chr(ord('a') + value - 0xE0061)}"
    if (value,) in names:
        return str(names[(value,)])
    try:
        return unicodedata.name(chr(value)).lower().replace("combining enclosing keycap", "keycap")
    except ValueError:
        return f"u+{value:04x}"


def _cluster_label(values: Sequence[int], names: Mapping[tuple[int, ...], str]) -> str:
    key = tuple(int(value) for value in values)
    for candidate in (key, tuple(value for value in key if value not in (0xFE0E, 0xFE0F))):
        if candidate in names:
            return str(names[candidate])
    return " + ".join(
        _scalar_label(value, names)
        for value in key
        if value not in (0xFE0E, 0xFE0F)
    )


def _component_name(
    system: str,
    codepoints: Sequence[int],
    names: Mapping[tuple[int, ...], str],
) -> str | None:
    values = tuple(int(value) for value in codepoints)
    if system == "atomic_anchor":
        return None
    if system == "presentation":
        return _cluster_label([value for value in values if value not in (0xFE0E, 0xFE0F)], names)
    if system == "modifier":
        return " + ".join(
            _scalar_label(value, names)
            for value in values
            if value not in (0xFE0E, 0xFE0F)
        )
    if system == "zwj":
        clusters: list[list[int]] = [[]]
        for value in values:
            if value == 0x200D:
                clusters.append([])
            else:
                clusters[-1].append(value)
        return " + ".join(_cluster_label(cluster, names) for cluster in clusters)
    if system == "regional_flag":
        return " + ".join(_scalar_label(value, names) for value in values)
    if system == "keycap":
        base = next(value for value in values if value not in (0xFE0E, 0xFE0F, 0x20E3))
        return f"{_scalar_label(base, names)} + keycap"
    if system == "tag_flag":
        labels = [_scalar_label(values[0], names)]
        labels.extend(
            _scalar_label(value, names)
            for value in values[1:]
            if value != 0xE007F
        )
        return " + ".join(labels)
    raise T11Error(f"Unknown component system: {system}")


def _decomposed_form(system: str, codepoints: Sequence[int]) -> str | None:
    values = tuple(int(value) for value in codepoints)
    if system == "atomic_anchor":
        return None
    if system == "presentation":
        return "".join(chr(value) for value in values if value not in (0xFE0E, 0xFE0F))
    if system == "modifier":
        return " ".join(chr(value) for value in values if value not in (0xFE0E, 0xFE0F))
    if system == "zwj":
        clusters: list[str] = []
        current: list[int] = []
        for value in values:
            if value == 0x200D:
                clusters.append("".join(chr(part) for part in current))
                current = []
            else:
                current.append(value)
        clusters.append("".join(chr(part) for part in current))
        return " ".join(clusters)
    if system == "regional_flag":
        return "".join(chr(ord("A") + value - 0x1F1E6) for value in values)
    if system == "keycap":
        base = next(value for value in values if value not in (0xFE0E, 0xFE0F, 0x20E3))
        return chr(base)
    if system == "tag_flag":
        return "".join(
            chr(ord("a") + value - 0xE0061)
            for value in values
            if 0xE0061 <= value <= 0xE007A
        )
    raise T11Error(f"Unknown decomposed system: {system}")


def _view_text(item: Mapping[str, Any], view: str) -> str:
    key = {
        "glyph": "glyph",
        "unicode_name": "name",
        "component_name": "component_name",
        "codepoint_literal": "codepoint_literal",
        "decomposed_form": "decomposed_form",
    }[view]
    value = item.get(key)
    _require(isinstance(value, str) and bool(value), f"Unavailable T11 view: {view}")
    return value


def _available_views(item: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in item["available_views"])


def _selection_hash(namespace: str, system: str, codepoint: str) -> str:
    return _hash_text(f"{namespace}:{system}:{codepoint}")


def build_selection(source_path: Path, output: Path) -> dict[str, Any]:
    config = _config()
    source_spec = config["source_bindings"]["unicode_emoji_test"]
    source = source_path.read_bytes()
    _require(len(source) == int(source_spec["expected_bytes"]), "Unicode source byte count changed")
    _require(hashlib.sha256(source).hexdigest() == source_spec["sha256"], "Unicode source hash changed")
    parsed = _parse_unicode_source(source)
    _require(parsed["version"] == source_spec["unicode_emoji_version"], "Unicode version changed")
    full = parsed["fully_qualified"]
    _require(len(full) == int(source_spec["expected_fully_qualified_entries"]), "Fully-qualified count changed")
    names = _name_map(parsed["all_rows"])
    rows_by_system: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source_index, original in enumerate(full):
        values = tuple(int(value) for value in original["codepoints"])
        system = _classify_system(values)
        glyph = "".join(chr(value) for value in values)
        _require(glyph == original["glyph"], f"Glyph/codepoint mismatch: {original['codepoint']}")
        component = _component_name(system, values, names)
        decomposed = _decomposed_form(system, values)
        available = (
            ["glyph", "unicode_name", "codepoint_literal"]
            if system == "atomic_anchor"
            else list(VIEW_ORDER)
        )
        row = {
            "source_index": source_index,
            "codepoint": str(original["codepoint"]),
            "codepoints": [f"U+{value:04X}" for value in values],
            "glyph": glyph,
            "name": str(original["name"]),
            "component_name": component,
            "codepoint_literal": " ".join(f"U+{value:04X}" for value in values),
            "decomposed_form": decomposed,
            "glyph_system": system,
            "group": str(original["group"]),
            "subgroup": str(original["subgroup"]),
            "emoji_version": str(original["emoji_version"]),
            "available_views": available,
        }
        rows_by_system[system].append(row)
    observed_counts = {key: len(value) for key, value in rows_by_system.items()}
    _require(observed_counts == source_spec["expected_fully_qualified_system_counts"], "System census changed")

    selection_namespace = str(config["selection"]["selection_namespace"])
    reserve_namespace = str(config["selection"]["reserve_namespace"])
    selected: list[dict[str, Any]] = []
    anchor_groups = [str(value) for value in config["selection"]["atomic_anchor_groups"]]
    anchor_quota = int(config["selection"]["quotas"]["atomic_anchor"]["calibration_prior_exposed"])
    _require(anchor_quota % len(anchor_groups) == 0, "Atomic quota is not group-balanced")
    per_group = anchor_quota // len(anchor_groups)
    for group in anchor_groups:
        candidates = [row for row in rows_by_system["atomic_anchor"] if row["group"] == group]
        candidates.sort(key=lambda row: _selection_hash(selection_namespace, group, row["codepoint"]))
        _require(len(candidates) >= per_group, f"Atomic group is too small: {group}")
        for row in candidates[:per_group]:
            selected.append({**row, "role": "calibration_prior_exposed"})

    for system in config["selection"]["system_order"]:
        system = str(system)
        if system == "atomic_anchor":
            continue
        quota = config["selection"]["quotas"][system]
        discovery_count = int(quota["discovery_unseen"])
        reserve_count = int(quota["reserve_unrun"])
        total = discovery_count + reserve_count
        candidates = sorted(
            rows_by_system[system],
            key=lambda row: _selection_hash(selection_namespace, system, row["codepoint"]),
        )[:total]
        _require(len(candidates) == total, f"System quota unavailable: {system}")
        reserve_codes = {
            row["codepoint"]
            for row in sorted(
                candidates,
                key=lambda row: _selection_hash(reserve_namespace, system, row["codepoint"]),
            )[:reserve_count]
        }
        for row in candidates:
            role = "reserve_unrun" if row["codepoint"] in reserve_codes else "discovery_unseen"
            selected.append({**row, "role": role})

    selected.sort(key=lambda row: int(row["source_index"]))
    depth_namespace = str(config["selection"]["depth_namespace"])
    depth_codes: set[str] = set()
    for system, quota_value in config["depth_subset"]["quotas"].items():
        system = str(system)
        quota = int(quota_value)
        if system == "atomic_anchor":
            per_depth_group = int(config["depth_subset"]["atomic_anchor_per_group"])
            _require(
                per_depth_group * len(anchor_groups) == quota,
                "Atomic depth quota is not group-balanced",
            )
            for group in anchor_groups:
                group_candidates = [
                    row
                    for row in selected
                    if row["glyph_system"] == system
                    and row["group"] == group
                    and row["role"] != "reserve_unrun"
                ]
                group_candidates.sort(
                    key=lambda row: _selection_hash(
                        depth_namespace, f"{system}:{group}", row["codepoint"]
                    )
                )
                _require(
                    len(group_candidates) >= per_depth_group,
                    f"Atomic depth group quota unavailable: {group}",
                )
                depth_codes.update(
                    str(row["codepoint"])
                    for row in group_candidates[:per_depth_group]
                )
            continue
        candidates = [
            row
            for row in selected
            if row["glyph_system"] == system and row["role"] != "reserve_unrun"
        ]
        candidates.sort(
            key=lambda row: _selection_hash(depth_namespace, system, row["codepoint"])
        )
        _require(len(candidates) >= quota, f"Depth quota unavailable: {system}")
        depth_codes.update(str(row["codepoint"]) for row in candidates[:quota])

    acquisition_index = 0
    depth_index = 0
    for selection_index, row in enumerate(selected):
        included = row["role"] != "reserve_unrun"
        in_depth = str(row["codepoint"]) in depth_codes
        _require(not in_depth or included, "Reserve leaked into depth subset")
        row.update(
            {
                "selection_index": selection_index,
                "included_in_acquisition": included,
                "acquisition_index": acquisition_index if included else None,
                "included_in_depth_subset": in_depth,
                "depth_index": depth_index if in_depth else None,
                "selection_hash": _selection_hash(selection_namespace, str(row["glyph_system"]), str(row["codepoint"])),
                "reserve_hash": _selection_hash(reserve_namespace, str(row["glyph_system"]), str(row["codepoint"])),
                "depth_hash": _selection_hash(
                    depth_namespace,
                    (
                        f"atomic_anchor:{row['group']}"
                        if row["glyph_system"] == "atomic_anchor"
                        else str(row["glyph_system"])
                    ),
                    str(row["codepoint"]),
                ),
            }
        )
        if included:
            acquisition_index += 1
        if in_depth:
            depth_index += 1

    role_counts = Counter(str(row["role"]) for row in selected)
    system_role_counts = {
        system: dict(Counter(str(row["role"]) for row in selected if row["glyph_system"] == system))
        for system in config["selection"]["system_order"]
    }
    _require(len(selected) == int(config["selection"]["expected_selected_items"]), "Selected count changed")
    _require(acquisition_index == int(config["selection"]["expected_acquired_items"]), "Acquisition count changed")
    _require(depth_index == int(config["depth_subset"]["expected_items"]), "Depth count changed")
    _require(role_counts["reserve_unrun"] == int(config["selection"]["expected_reserve_items"]), "Reserve count changed")

    for system in config["selection"]["system_order"]:
        system_rows = [row for row in selected if row["glyph_system"] == system]
        views = _available_views(system_rows[0])
        for view in views:
            values = [_view_text(row, view) for row in system_rows]
            _require(len(values) == len(set(values)), f"Non-unique selected view: {system}/{view}")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "prospective_selection_complete_zero_t11_model_forwards",
        "source": {
            "url": source_spec["url"],
            "unicode_emoji_version": parsed["version"],
            "sha256": hashlib.sha256(source).hexdigest(),
            "bytes": len(source),
            "fully_qualified_entries": len(full),
            "fully_qualified_system_counts": observed_counts,
        },
        "selection_namespace": selection_namespace,
        "reserve_namespace": reserve_namespace,
        "depth_namespace": depth_namespace,
        "role_counts": dict(role_counts),
        "system_role_counts": system_role_counts,
        "selected_item_count": len(selected),
        "acquired_item_count": acquisition_index,
        "reserve_item_count": int(role_counts["reserve_unrun"]),
        "depth_item_count": depth_index,
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "items": selected,
    }
    _write_json_once(output, payload)
    return {
        "status": "pass",
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "selected_items": len(selected),
        "acquired_items": acquisition_index,
        "reserve_items": int(role_counts["reserve_unrun"]),
        "depth_items": depth_index,
    }


def selection_items(*, acquired_only: bool = True) -> list[dict[str, Any]]:
    manifest = atlas._read_json(_root() / SELECTION_PATH)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Selection protocol mismatch")
    rows = [dict(row) for row in manifest["items"]]
    if acquired_only:
        rows = [row for row in rows if bool(row["included_in_acquisition"])]
        rows.sort(key=lambda row: int(row["acquisition_index"]))
    else:
        rows.sort(key=lambda row: int(row["selection_index"]))
    return rows


def audit_design() -> dict[str, Any]:
    config = _config()
    observed: dict[str, str] = {}
    for binding_name in ("t10_config", "t10_freeze_manifest", "t10_public_manifest", "t10_diagnostics"):
        binding = config["source_bindings"][binding_name]
        path = _root() / str(binding["path"])
        _require(path.is_file(), f"Missing T11 source binding: {binding_name}")
        actual = _sha256(path)
        _require(actual == str(binding["sha256"]), f"T11 source binding changed: {binding_name}")
        observed[path.relative_to(_root()).as_posix()] = actual
    manifest_path = _root() / SELECTION_PATH
    _require(manifest_path.is_file(), "T11 selection is absent")
    selection = atlas._read_json(manifest_path)
    _require(selection.get("status") == "prospective_selection_complete_zero_t11_model_forwards", "Selection status changed")
    _require(selection.get("model_forward_calls") == 0, "Selection used a model forward")
    all_items = selection_items(acquired_only=False)
    acquired = selection_items(acquired_only=True)
    reserve = [row for row in all_items if row["role"] == "reserve_unrun"]
    _require(len(all_items) == int(config["selection"]["expected_selected_items"]), "Selected roster changed")
    _require(
        [int(row["selection_index"]) for row in all_items] == list(range(len(all_items))),
        "Selection indices changed",
    )
    _require(
        [int(row["acquisition_index"]) for row in acquired] == list(range(len(acquired))),
        "Acquisition indices changed",
    )
    _require(
        all(not row["included_in_acquisition"] and not row["included_in_depth_subset"] for row in reserve),
        "Reserve inclusion gate changed",
    )
    for system in config["selection"]["system_order"]:
        system = str(system)
        observed_roles = Counter(
            str(row["role"]) for row in all_items if row["glyph_system"] == system
        )
        expected_roles = {
            role: int(count)
            for role, count in config["selection"]["quotas"][system].items()
            if int(count) > 0
        }
        _require(dict(observed_roles) == expected_roles, f"T11 system quota changed: {system}")
        system_rows = [row for row in all_items if row["glyph_system"] == system]
        for view in _available_views(system_rows[0]):
            texts = [_view_text(row, view) for row in system_rows]
            _require(len(texts) == len(set(texts)), f"T11 selected text view collapsed: {system}/{view}")
    depth_counts = Counter(
        str(row["glyph_system"]) for row in acquired if row["included_in_depth_subset"]
    )
    expected_depth_counts = {
        str(system): int(count)
        for system, count in config["depth_subset"]["quotas"].items()
        if int(count) > 0
    }
    _require(dict(depth_counts) == expected_depth_counts, "T11 depth quotas changed")
    present_views = sum(len(_available_views(row)) for row in acquired)
    depth_views = sum(len(_available_views(row)) for row in acquired if row["included_in_depth_subset"])
    _require(len(acquired) == int(config["selection"]["expected_acquired_items"]), "Acquired roster changed")
    _require(len(reserve) == int(config["selection"]["expected_reserve_items"]), "Reserve roster changed")
    _require(present_views == int(config["acquisition"]["expected_present_item_views"]), "Present view count changed")
    _require(depth_views == int(config["depth_subset"]["expected_present_item_views"]), "Depth view count changed")
    expected_forwards = present_views * len(config["input"]["carrier_order"])
    _require(expected_forwards == int(config["acquisition"]["expected_model_forward_calls_per_model"]), "Forward count contract changed")
    broad_vectors = (
        present_views
        * len(config["input"]["carrier_order"])
        * len(config["input"]["distance_order"])
        * len(BROAD_ENDPOINT_ORDER)
    )
    depth_vectors = (
        depth_views
        * len(config["input"]["carrier_order"])
        * len(config["input"]["distance_order"])
        * len(DEPTH_ENDPOINT_ORDER)
    )
    _require(
        broad_vectors == int(config["acquisition"]["expected_broad_readout_vectors_per_model"]),
        "T11 broad vector contract changed",
    )
    _require(
        depth_vectors == int(config["acquisition"]["expected_depth_readout_vectors_per_model"]),
        "T11 depth vector contract changed",
    )
    shard_count = int(math.ceil(len(acquired) / int(config["acquisition"]["item_shard_size"])))
    _require(shard_count == int(config["acquisition"]["expected_shards_per_model"]), "T11 shard contract changed")
    _require(tuple(config["models"]["order"]) == t10.model_roles(), "T10/T11 model roster differs")
    model_count = len(model_roles())
    _require(
        expected_forwards * model_count
        == int(config["acquisition"]["expected_total_model_forward_calls"]),
        "T11 total forward contract changed",
    )
    _require(
        (broad_vectors + depth_vectors) * model_count
        == int(config["acquisition"]["expected_total_stored_readout_vectors"]),
        "T11 total stored-vector contract changed",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "source_bindings": observed,
        "selection_manifest_sha256": _sha256(manifest_path),
        "selected_items": len(all_items),
        "acquired_items": len(acquired),
        "reserve_items": len(reserve),
        "present_item_views": present_views,
        "depth_item_views": depth_views,
        "broad_readout_vectors_per_model": broad_vectors,
        "depth_readout_vectors_per_model": depth_vectors,
        "shards_per_model": shard_count,
        "model_cells": model_count,
        "expected_total_model_forward_calls": int(config["acquisition"]["expected_total_model_forward_calls"]),
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }


def build_design_preflight(output: Path) -> dict[str, Any]:
    design = audit_design()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_preflight_complete_zero_t11_model_forwards",
        "design": design,
        "config_sha256": _sha256(_root() / CONFIG_PATH),
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "implementation_script_sha256": _sha256(Path(__file__).resolve()),
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    _write_json_once(output, payload)
    return {"status": "pass", "output": output.as_posix(), "sha256": _sha256(output)}


def _control_mapping(
    rows: Sequence[Mapping[str, Any]],
    token_ids: Mapping[int, Sequence[int]],
    *,
    role: str,
    target_view: str,
    strict_prefix: bool,
) -> dict[str, Any]:
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    row_by_index = {int(row["acquisition_index"]): row for row in rows}
    for row in rows:
        index = int(row["acquisition_index"])
        ids = [int(value) for value in token_ids[index]]
        key: tuple[Any, ...] = (str(row["glyph_system"]), len(ids))
        if strict_prefix:
            key += (ids[0],)
        groups[key].append(index)
    mapping: dict[int, int] = {}
    strata: list[dict[str, Any]] = []
    for key, indices in sorted(groups.items(), key=lambda value: tuple(str(part) for part in value[0])):
        ordered = sorted(
            indices,
            key=lambda index: _hash_text(
                f"glyphprobe-t11-v0-control:{role}:{target_view}:{int(strict_prefix)}:{row_by_index[index]['codepoint']}"
            ),
        )
        if len(ordered) >= 2:
            for position, index in enumerate(ordered):
                mapping[index] = ordered[(position + 1) % len(ordered)]
        strata.append({"key": list(key), "item_indices": ordered, "count": len(ordered)})
    _require(all(index != target for index, target in mapping.items()), "Matched control contains a self match")
    return {
        "strict_prefix": strict_prefix,
        "eligible_item_count": len(mapping),
        "total_item_count": len(rows),
        "coverage": float(len(mapping) / max(1, len(rows))),
        "mapping": [
            {"item_index": index, "wrong_target_item_index": mapping[index]}
            for index in sorted(mapping)
        ],
        "strata": strata,
    }


def _sequence_hash(rows: Sequence[Sequence[int]]) -> str:
    return atlas._sequence_sha256(rows)


def _tokenize_panel(tokenizer: Any, role: str) -> dict[str, Any]:
    config = _config()
    items = selection_items(acquired_only=True)
    raw_ids: dict[str, dict[int, list[int]]] = {view: {} for view in VIEW_ORDER}
    combined_ids: dict[str, dict[str, dict[int, list[int]]]] = {
        view: {str(carrier): {} for carrier in config["input"]["carrier_order"]}
        for view in VIEW_ORDER
    }
    item_rows: list[dict[str, Any]] = []
    for item in items:
        index = int(item["acquisition_index"])
        views: dict[str, Any] = {}
        for view in _available_views(item):
            ids = [
                int(value)
                for value in tokenizer.encode(_view_text(item, view), add_special_tokens=False)
            ]
            _require(bool(ids), f"Empty T11 tokenization: {item['codepoint']}/{view}")
            raw_ids[view][index] = ids
            views[view] = {
                "token_ids": ids,
                "token_count": len(ids),
                "first_token_id": ids[0],
            }
        item_rows.append(
            {
                "item_index": index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_system": str(item["glyph_system"]),
                "views": views,
            }
        )
    for system in config["selection"]["system_order"]:
        system_items = [item for item in items if item["glyph_system"] == system]
        if not system_items:
            continue
        for view in _available_views(system_items[0]):
            sequences = [tuple(raw_ids[view][int(item["acquisition_index"])]) for item in system_items]
            _require(len(sequences) == len(set(sequences)), f"Tokenizer collapsed T11 view: {role}/{system}/{view}")

    carrier_rows: dict[str, Any] = {}
    maximum_tokens = 0
    for carrier in config["input"]["carrier_order"]:
        carrier = str(carrier)
        spec = config["input"]["carriers"][carrier]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        unit_ids = [int(value) for value in tokenizer.encode(unit, add_special_tokens=False)]
        _require(len(unit_ids) == 1, f"T11 carrier is not one token: {role}/{carrier}")
        prefix_exact = 0
        decode_exact = 0
        case_count = 0
        for item in items:
            index = int(item["acquisition_index"])
            for view in _available_views(item):
                text = _view_text(item, view) + unit * repeats
                ids = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
                expected = raw_ids[view][index] + unit_ids * repeats
                _require(ids == expected, f"T11 carrier boundary changed: {role}/{item['codepoint']}/{view}/{carrier}")
                combined_ids[view][carrier][index] = ids
                prefix_exact += int(ids[:-repeats] == raw_ids[view][index])
                decode_exact += int(
                    tokenizer.decode(ids, clean_up_tokenization_spaces=False, skip_special_tokens=False)
                    == text
                )
                maximum_tokens = max(maximum_tokens, len(ids))
                case_count += 1
        _require(prefix_exact == case_count, f"T11 carrier prefix failure: {role}/{carrier}")
        _require(decode_exact == case_count, f"T11 carrier decode failure: {role}/{carrier}")
        carrier_rows[carrier] = {
            "unit": unit,
            "repeats": repeats,
            "token_id": unit_ids[0],
            "case_count": case_count,
            "prefix_exact_count": prefix_exact,
            "decode_exact_count": decode_exact,
        }

    controls: dict[str, Any] = {}
    depth_controls: dict[str, Any] = {}
    analysis_systems = [str(value) for value in config["analysis"]["analysis_systems"]]
    minimums = config["tokenization_controls"]["required_minimum_coverage"]
    for target_view in config["tokenization_controls"]["matched_incorrect_label_targets"]:
        target_view = str(target_view)
        controls[target_view] = {}
        depth_controls[target_view] = {}
        for system in analysis_systems:
            system_rows = [
                item
                for item in items
                if item["glyph_system"] == system and target_view in _available_views(item)
            ]
            if not system_rows:
                continue
            token_lookup = {
                int(item["acquisition_index"]): raw_ids[target_view][int(item["acquisition_index"])]
                for item in system_rows
            }
            loose = _control_mapping(
                system_rows,
                token_lookup,
                role=role,
                target_view=target_view,
                strict_prefix=False,
            )
            strict = _control_mapping(
                system_rows,
                token_lookup,
                role=role,
                target_view=target_view,
                strict_prefix=True,
            )
            required = float(minimums[system])
            _require(loose["coverage"] >= required, f"T11 matched-control coverage failed: {role}/{system}/{target_view}")
            controls[target_view][system] = {
                "required": loose,
                "strict_prefix_sensitivity": strict,
                "required_minimum_coverage": required,
            }
            depth_rows = [item for item in system_rows if bool(item["included_in_depth_subset"])]
            if depth_rows:
                depth_lookup = {
                    int(item["acquisition_index"]): raw_ids[target_view][int(item["acquisition_index"])]
                    for item in depth_rows
                }
                depth_loose = _control_mapping(
                    depth_rows,
                    depth_lookup,
                    role=role,
                    target_view=f"depth:{target_view}",
                    strict_prefix=False,
                )
                depth_strict = _control_mapping(
                    depth_rows,
                    depth_lookup,
                    role=role,
                    target_view=f"depth:{target_view}",
                    strict_prefix=True,
                )
                _require(
                    depth_loose["coverage"] >= required,
                    f"T11 depth matched-control coverage failed: {role}/{system}/{target_view}",
                )
                depth_controls[target_view][system] = {
                    "required": depth_loose,
                    "strict_prefix_sensitivity": depth_strict,
                    "required_minimum_coverage": required,
                }

    raw_hashes = {
        view: _sequence_hash(
            [raw_ids[view][index] for index in sorted(raw_ids[view])]
        )
        for view in VIEW_ORDER
    }
    combined_hashes = {
        view: {
            carrier: _sequence_hash(
                [combined_ids[view][carrier][index] for index in sorted(combined_ids[view][carrier])]
            )
            for carrier in config["input"]["carrier_order"]
        }
        for view in VIEW_ORDER
    }
    return {
        "raw_ids": raw_ids,
        "combined_ids": combined_ids,
        "receipt": {
            "item_count": len(items),
            "present_item_views": sum(len(_available_views(item)) for item in items),
            "view_order": list(VIEW_ORDER),
            "item_tokenization": item_rows,
            "ordered_sequence_sha256": {"raw": raw_hashes, "combined": combined_hashes},
            "carriers": carrier_rows,
            "maximum_combined_token_count": maximum_tokens,
            "matched_incorrect_label_controls": controls,
            "depth_matched_incorrect_label_controls": depth_controls,
        },
    }


def _runtime_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for package in ("glyphprobe", "torch", "transformers", "numpy", "PyYAML"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


def _locate_local_snapshot(role: str) -> Path:
    """Resolve one pinned snapshot from the local Hub cache without networking."""

    from huggingface_hub import snapshot_download

    spec = _model_spec(role)
    try:
        located = snapshot_download(
            repo_id=str(spec["artifact_model_id"]),
            revision=str(spec["revision"]),
            local_files_only=True,
        )
    except Exception as exc:  # pragma: no cover - depends on the host cache
        raise T11Error(f"Pinned T11 snapshot is not available locally: {role}") from exc
    snapshot = Path(located)
    _require(snapshot.is_dir(), f"Located T11 snapshot is not a directory: {role}")
    _require(snapshot.name == str(spec["revision"]), f"Located T11 revision changed: {role}")
    return snapshot


def _model_path(role: str, supplied: Path | None) -> Path:
    return supplied if supplied is not None else _locate_local_snapshot(role)


def tokenizer_preflight(role: str, model_path: Path, output: Path) -> dict[str, Any]:
    """Validate one frozen artifact and T11 tokenizer surface without weights."""

    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoConfig, AutoTokenizer

    freeze = audit_freeze()
    spec = _model_spec(role)
    snapshot = model_path.resolve()
    _require(snapshot.is_dir(), f"T11 model snapshot missing: {snapshot}")
    _require(snapshot.name == str(spec["revision"]), f"T11 revision mismatch: {role}")
    completeness = t10._validate_weight_artifact_completeness(snapshot)
    artifact = model_artifact_receipt(snapshot)
    t10_freeze = atlas._read_json(_root() / "data/manifests/semantic_atlas_cross_model_replication_v0.json")
    pinned = t10_freeze["model_artifacts"][role]
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == pinned[key], f"T11 reused artifact changed: {role}/{key}")
    architecture = AutoConfig.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    _require(str(architecture.model_type) == str(spec["expected_model_type"]), "T11 model type mismatch")
    _require(int(architecture.num_hidden_layers) == int(spec["expected_num_layers"]), "T11 layer count mismatch")
    _require(int(architecture.hidden_size) == int(spec["expected_model_dim"]), "T11 model width mismatch")
    _require(int(architecture.vocab_size) == int(spec["expected_vocab_size"]), "T11 vocabulary mismatch")
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    tokenization = _tokenize_panel(tokenizer, role)["receipt"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_and_static_artifact_preflight_pass_zero_t11_model_forwards",
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "architecture": {
            "model_type": str(architecture.model_type),
            "architectures": [str(value) for value in getattr(architecture, "architectures", [])],
            "num_hidden_layers": int(architecture.num_hidden_layers),
            "hidden_size": int(architecture.hidden_size),
            "vocab_size": int(architecture.vocab_size),
        },
        "tokenizer": {
            "class": type(tokenizer).__name__,
            "vocab_size": int(getattr(tokenizer, "vocab_size", len(tokenizer))),
            **tokenization,
        },
        "model_artifact": artifact,
        "weight_artifact_completeness": completeness,
        "runtime_versions_observed": _runtime_versions(),
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "reserve_model_forward_calls": 0,
        "scientific_result_available": False,
    }
    _write_json_once(output, payload)
    return {
        "status": "pass",
        "model_role": role,
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "present_item_views": tokenization["present_item_views"],
        "maximum_combined_token_count": tokenization["maximum_combined_token_count"],
    }


def _validate_tokenizer_receipt(path: Path, role: str) -> dict[str, Any]:
    value = atlas._read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, f"T11 tokenizer receipt protocol mismatch: {role}")
    _require(value.get("model_role") == role, f"T11 tokenizer receipt role mismatch: {role}")
    _require(
        value.get("status") == "tokenizer_and_static_artifact_preflight_pass_zero_t11_model_forwards",
        f"T11 tokenizer receipt failed: {role}",
    )
    _require(value.get("model_weights_loaded") is False, "T11 tokenizer preflight loaded weights")
    _require(value.get("model_forward_calls") == 0, "T11 tokenizer preflight used a forward")
    _require(value.get("reserve_model_forward_calls") == 0, "T11 reserve was forwarded in preflight")
    _require(value.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T11 receipt freeze mismatch")
    _require(value.get("selection_manifest_sha256") == _sha256(_root() / SELECTION_PATH), "T11 receipt selection mismatch")
    return value


def assemble_runtime_preflight(directory: Path, output: Path) -> dict[str, Any]:
    """Bind all nine zero-forward tokenizer receipts before any weight load."""

    _require(
        output.name == "aggregate.json" and output.parent.resolve() == directory.resolve(),
        "T11 aggregate preflight must be written as <directory>/aggregate.json",
    )
    freeze = audit_freeze()
    receipts: dict[str, str] = {}
    artifacts: dict[str, Any] = {}
    coverage: dict[str, Any] = {}
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(path.is_file(), f"Missing T11 tokenizer receipt: {role}")
        receipt = _validate_tokenizer_receipt(path, role)
        receipts[role] = _sha256(path)
        artifacts[role] = {
            "artifact_model_id": receipt["artifact_model_id"],
            "revision": receipt["revision"],
            **{
                key: receipt["model_artifact"][key]
                for key in ("manifest_sha256", "file_count", "total_bytes")
            },
        }
        coverage[role] = {
            target: {
                system: {
                    "required": values["required"]["coverage"],
                    "strict_prefix_sensitivity": values["strict_prefix_sensitivity"]["coverage"],
                }
                for system, values in systems.items()
            }
            for target, systems in receipt["tokenizer"]["matched_incorrect_label_controls"].items()
        }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "all_nine_tokenizer_preflights_complete_zero_t11_model_forwards",
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "model_order": list(model_roles()),
        "tokenizer_receipt_sha256": receipts,
        "model_artifacts": artifacts,
        "matched_control_coverage": coverage,
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "reserve_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    _write_json_once(output, payload)
    ledger = output.parent / "SHA256SUMS"
    _require(not ledger.exists(), f"Runtime preflight ledger exists: {ledger}")
    names = [f"{role}.json" for role in model_roles()] + [output.name]
    ledger.write_text(
        "".join(f"{_sha256(output.parent / name)}  {name}\n" for name in names),
        encoding="utf-8",
    )
    return {
        "status": "pass",
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "model_cells": len(model_roles()),
        "model_forward_calls": 0,
    }


def preflight_all(output: Path) -> dict[str, Any]:
    """Atomically build all nine zero-forward receipts from the local cache."""

    audit_freeze()
    _require(not output.exists(), f"T11 preflight output exists: {output}")
    snapshots = {role: _locate_local_snapshot(role) for role in model_roles()}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.partial-", dir=output.parent))
    for role in model_roles():
        tokenizer_preflight(role, snapshots[role], stage / f"{role}.json")
    result = assemble_runtime_preflight(stage, stage / "aggregate.json")
    stage.rename(output)
    return {
        "status": "pass",
        "output": output.as_posix(),
        "model_cells": len(model_roles()),
        "aggregate_sha256": result["sha256"],
        "model_weights_loaded": False,
        "model_forward_calls": 0,
    }


def _validate_runtime_preflight(directory: Path) -> dict[str, Any]:
    aggregate_path = directory / "aggregate.json"
    ledger_path = directory / "SHA256SUMS"
    _require(aggregate_path.is_file() and ledger_path.is_file(), "T11 aggregate preflight is incomplete")
    _validate_ledger(
        directory,
        [f"{role}.json" for role in model_roles()] + ["aggregate.json"],
    )
    aggregate = atlas._read_json(aggregate_path)
    _require(
        aggregate.get("status") == "all_nine_tokenizer_preflights_complete_zero_t11_model_forwards",
        "T11 aggregate preflight failed",
    )
    _require(tuple(aggregate["model_order"]) == model_roles(), "T11 aggregate model order changed")
    _require(aggregate.get("model_forward_calls") == 0, "T11 aggregate preflight used a forward")
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(_sha256(path) == aggregate["tokenizer_receipt_sha256"][role], "T11 aggregate receipt hash changed")
        _validate_tokenizer_receipt(path, role)
    return aggregate


def build_freeze(output: Path) -> dict[str, Any]:
    design = atlas._read_json(_root() / DESIGN_PREFLIGHT_PATH)
    _require(
        design.get("status") == "design_preflight_complete_zero_t11_model_forwards",
        "T11 design preflight is incomplete",
    )
    _require(design.get("model_forward_calls") == 0, "T11 design preflight used a forward")
    assets: dict[str, str] = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"Missing T11 frozen asset: {relative}")
        assets[relative] = _sha256(path)
    config = _config()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t11_model_forward",
        "experiment_role": config["experiment_role"],
        "question": config["question"],
        "claim_boundary": config["claim_boundary"],
        "frozen_assets": assets,
        "design_preflight_sha256": _sha256(_root() / DESIGN_PREFLIGHT_PATH),
        "selection_manifest_sha256": _sha256(_root() / SELECTION_PATH),
        "t10_model_artifacts": atlas._read_json(
            _root() / "data/manifests/semantic_atlas_cross_model_replication_v0.json"
        )["model_artifacts"],
        "model_order": list(model_roles()),
        "model_forward_calls_at_freeze": 0,
        "reserve_model_forward_calls_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
        "t10_primary_changed": False,
        "t10_rescue_authorized": False,
    }
    _write_json_once(output, payload)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
        "model_cells": len(model_roles()),
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    manifest = atlas._read_json(path)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "T11 freeze protocol mismatch")
    _require(
        manifest.get("status") == "freeze_complete_before_any_t11_model_forward",
        "T11 freeze is incomplete",
    )
    _require(manifest.get("model_forward_calls_at_freeze") == 0, "T11 freeze forward count changed")
    _require(manifest.get("reserve_model_forward_calls_at_freeze") == 0, "T11 reserve freeze gate changed")
    for relative, expected in manifest["frozen_assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"T11 frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"T11 frozen asset changed: {relative}")
    _require(_sha256(_root() / DESIGN_PREFLIGHT_PATH) == manifest["design_preflight_sha256"], "T11 design preflight changed")
    _require(_sha256(_root() / SELECTION_PATH) == manifest["selection_manifest_sha256"], "T11 selection changed")
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(manifest["frozen_assets"]),
    }


def _validate_runtime() -> dict[str, str | None]:
    import torch

    config = _config()
    versions = _runtime_versions()
    for package, expected in config["runtime"]["critical_versions"].items():
        _require(versions.get(package) == str(expected), f"T11 runtime mismatch: {package}")
    _require(torch.cuda.is_available(), "T11 CUDA is unavailable")
    _require(torch.cuda.is_bf16_supported(), "T11 CUDA BF16 is unavailable")
    _require(
        str(torch.cuda.get_device_name(0)) == str(config["runtime"]["hardware_pin"]),
        "T11 GPU identity mismatch",
    )
    return versions


def _load_model(
    role: str,
    model_path: Path,
    preflight_directory: Path,
) -> tuple[Any, Any, Any, Any, dict[str, Any], dict[str, Any]]:
    import torch
    import transformers
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoModelForCausalLM, AutoTokenizer

    aggregate = _validate_runtime_preflight(preflight_directory)
    _validate_runtime()
    spec = _model_spec(role)
    receipt_path = preflight_directory / f"{role}.json"
    receipt = _validate_tokenizer_receipt(receipt_path, role)
    artifact = model_artifact_receipt(model_path)
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == aggregate["model_artifacts"][role][key], f"T11 runtime artifact changed: {role}/{key}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    roster = _tokenize_panel(tokenizer, role)
    _require(
        roster["receipt"]["ordered_sequence_sha256"]
        == receipt["tokenizer"]["ordered_sequence_sha256"],
        "T11 runtime token sequences changed",
    )
    _require(
        roster["receipt"]["matched_incorrect_label_controls"]
        == receipt["tokenizer"]["matched_incorrect_label_controls"],
        "T11 runtime matched controls changed",
    )
    _require(
        roster["receipt"]["depth_matched_incorrect_label_controls"]
        == receipt["tokenizer"]["depth_matched_incorrect_label_controls"],
        "T11 runtime depth matched controls changed",
    )
    dtype_key = "dtype" if int(transformers.__version__.split(".", 1)[0]) >= 5 else "torch_dtype"
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=False,
        **{dtype_key: torch.bfloat16},
    )
    model.to("cuda")
    model.eval()
    _require(type(model).__name__ == str(spec["expected_model_class"]), "T11 loaded model class mismatch")
    _require(int(model.config.num_hidden_layers) == int(spec["expected_num_layers"]), "T11 loaded layer count mismatch")
    count = sum(int(parameter.numel()) for parameter in model.parameters())
    _require(count == int(spec["expected_parameter_count"]), "T11 parameter count mismatch")
    dtypes = Counter(str(parameter.dtype) for parameter in model.parameters())
    _require(set(dtypes) == {"torch.bfloat16"}, "T11 parameter dtype mismatch")
    blocks = t10._resolve_attr(model, str(spec["expected_block_path"]))
    _require(len(blocks) == int(spec["expected_num_layers"]), "T11 decoder-block roster mismatch")
    model_receipt = {
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "model_class": type(model).__name__,
        "parameter_count": count,
        "parameter_dtype_tensor_counts": dict(dtypes),
        "artifact": artifact,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "gpu": str(torch.cuda.get_device_name(0)),
        "runtime_preflight_aggregate_sha256": _sha256(preflight_directory / "aggregate.json"),
        "tokenizer_receipt_sha256": _sha256(receipt_path),
    }
    return torch, tokenizer, model, blocks[-1], model_receipt, roster


def _depth_hidden_state_indices(num_layers: int) -> tuple[int, int, int]:
    indices = tuple(int(math.floor(fraction * num_layers)) for fraction in (0.25, 0.50, 0.75))
    _require(all(1 <= index < num_layers for index in indices), "T11 depth index is outside inter-block states")
    _require(len(set(indices)) == 3, "T11 depth indices collapsed")
    return indices


def _records(roster: Mapping[str, Any]) -> list[dict[str, Any]]:
    config = _config()
    rows: list[dict[str, Any]] = []
    for item in selection_items(acquired_only=True):
        item_index = int(item["acquisition_index"])
        for view_index, view in enumerate(VIEW_ORDER):
            if view not in _available_views(item):
                continue
            raw_ids = [int(value) for value in roster["raw_ids"][view][item_index]]
            for carrier_index, carrier in enumerate(config["input"]["carrier_order"]):
                carrier = str(carrier)
                rows.append(
                    {
                        "item_index": item_index,
                        "view_index": view_index,
                        "view": view,
                        "carrier_index": carrier_index,
                        "carrier": carrier,
                        "raw_ids": raw_ids,
                        "input_ids": [
                            int(value)
                            for value in roster["combined_ids"][view][carrier][item_index]
                        ],
                    }
                )
    return rows


def _raw_tensor(value: Any) -> Any:
    return value[0] if isinstance(value, tuple) else value


def _run_one_shard(
    *,
    role: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    last_block: Any,
    model_receipt: Mapping[str, Any],
    roster: Mapping[str, Any],
    run_root: Path,
    shard_index: int,
    preflight_directory: Path,
) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    population = selection_items(acquired_only=True)
    shard_size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(population), start + shard_size)
    _require(start < stop, f"T11 shard index out of range: {shard_index}")
    shard_items = population[start:stop]
    _require(all(item["role"] != "reserve_unrun" for item in shard_items), "T11 reserve leaked into shard")
    stage, final = atlas._atomic_shard_directory(run_root, shard_index)
    intent = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "forward_may_begin_after_this_record",
        "model_role": role,
        "shard_index": shard_index,
        "item_index_start": start,
        "item_index_stop_exclusive": stop,
        "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        "reserve_items_present": False,
        "retry_policy": config["acquisition"]["incomplete_stage_policy"],
    }
    atlas._write_json(stage / "execution_intent.json", intent)
    width = int(_model_spec(role)["expected_model_dim"])
    broad = np.full(
        (len(shard_items), len(VIEW_ORDER), 2, 4, len(BROAD_ENDPOINT_ORDER), width),
        np.nan,
        dtype=np.float32,
    )
    view_mask = np.zeros((len(shard_items), len(VIEW_ORDER)), dtype=np.bool_)
    depth_local_indices = np.asarray(
        [index for index, item in enumerate(shard_items) if bool(item["included_in_depth_subset"])],
        dtype=np.int64,
    )
    depth = np.full(
        (len(depth_local_indices), len(VIEW_ORDER), 2, 4, len(DEPTH_ENDPOINT_ORDER), width),
        np.nan,
        dtype=np.float32,
    )
    depth_lookup = {int(local): position for position, local in enumerate(depth_local_indices)}
    for local, item in enumerate(shard_items):
        for view in _available_views(item):
            view_mask[local, VIEW_ORDER.index(view)] = True
    all_records = _records(roster)
    records = [row for row in all_records if start <= int(row["item_index"]) < stop]
    distances = [int(value) for value in config["input"]["distance_order"]]
    depth_indices = _depth_hidden_state_indices(int(_model_spec(role)["expected_num_layers"]))
    raw_capture: list[Any] = []

    def hook(_module: Any, _inputs: Any, value: Any) -> None:
        raw_capture.append(_raw_tensor(value))

    handle = last_block.register_forward_hook(hook)
    observations: list[dict[str, Any]] = []
    forward_calls = 0
    broad_vectors = 0
    depth_vectors = 0
    endpoint_delta_first_forward: float | None = None
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    try:
        for row in records:
            global_index = int(row["item_index"])
            local_index = global_index - start
            ids = [int(value) for value in row["input_ids"]]
            input_ids = torch.tensor([ids], dtype=torch.long, device="cuda")
            attention_mask = torch.ones_like(input_ids)
            positions = [len(row["raw_ids"]) + distance - 1 for distance in distances]
            raw_capture.clear()
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
            elapsed_ms = (time.perf_counter() - before) * 1000.0
            _require(len(raw_capture) == 1, "T11 last-block hook count mismatch")
            raw = raw_capture[0]
            returned = output.hidden_states[-1]
            _require(raw.shape == returned.shape, "T11 broad endpoint shape mismatch")
            _require(len(output.hidden_states) == int(_model_spec(role)["expected_num_layers"]) + 1, "T11 hidden-state roster mismatch")
            position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
            broad_states = torch.stack((raw, returned), dim=2)
            captured_broad = broad_states[0, position_tensor].float().cpu().numpy()
            _require(captured_broad.shape == (4, 2, width), "T11 captured broad shape mismatch")
            _require(bool(np.isfinite(captured_broad).all()), "T11 broad activation is nonfinite")
            broad[
                local_index,
                int(row["view_index"]),
                int(row["carrier_index"]),
            ] = captured_broad
            broad_vectors += 4 * len(BROAD_ENDPOINT_ORDER)
            captured_depth: np.ndarray | None = None
            if local_index in depth_lookup:
                states = [output.hidden_states[0]]
                states.extend(output.hidden_states[index] for index in depth_indices)
                states.extend((raw, returned))
                depth_states = torch.stack(tuple(states), dim=2)
                captured_depth = depth_states[0, position_tensor].float().cpu().numpy()
                _require(captured_depth.shape == (4, 6, width), "T11 captured depth shape mismatch")
                _require(bool(np.isfinite(captured_depth).all()), "T11 depth activation is nonfinite")
                depth[
                    depth_lookup[local_index],
                    int(row["view_index"]),
                    int(row["carrier_index"]),
                ] = captured_depth
                depth_vectors += 4 * len(DEPTH_ENDPOINT_ORDER)
            if endpoint_delta_first_forward is None:
                endpoint_delta_first_forward = float(torch.max(torch.abs(raw.float() - returned.float())).item())
            item = shard_items[local_index]
            observations.append(
                {
                    "item_index": global_index,
                    "source_index": int(item["source_index"]),
                    "codepoint": str(item["codepoint"]),
                    "glyph_system": str(item["glyph_system"]),
                    "view": str(row["view"]),
                    "view_index": int(row["view_index"]),
                    "carrier": str(row["carrier"]),
                    "carrier_index": int(row["carrier_index"]),
                    "raw_token_ids": [int(value) for value in row["raw_ids"]],
                    "input_token_ids": ids,
                    "readout_positions": positions,
                    "broad_activation_rms_by_distance_endpoint": np.sqrt(
                        np.mean(np.square(captured_broad, dtype=np.float64), axis=-1)
                    ).tolist(),
                    "depth_subset": local_index in depth_lookup,
                    "depth_activation_rms_by_distance_endpoint": (
                        np.sqrt(np.mean(np.square(captured_depth, dtype=np.float64), axis=-1)).tolist()
                        if captured_depth is not None
                        else None
                    ),
                    "forward_latency_ms": elapsed_ms,
                }
            )
            forward_calls += 1
            del output, raw, returned, broad_states, captured_broad
            del input_ids, attention_mask, position_tensor
            if captured_depth is not None:
                del captured_depth, depth_states, states
    finally:
        handle.remove()

    _require(bool(np.isfinite(broad[view_mask]).all()), "T11 present broad values are nonfinite")
    _require(bool(np.isnan(broad[~view_mask]).all()), "T11 absent broad values are not NaN")
    depth_mask = view_mask[depth_local_indices]
    _require(bool(np.isfinite(depth[depth_mask]).all()), "T11 present depth values are nonfinite")
    _require(bool(np.isnan(depth[~depth_mask]).all()), "T11 absent depth values are not NaN")
    np.save(stage / "broad_activations.npy", broad, allow_pickle=False)
    np.save(stage / "depth_activations.npy", depth, allow_pickle=False)
    np.save(stage / "view_mask.npy", view_mask, allow_pickle=False)
    np.save(stage / "depth_item_local_indices.npy", depth_local_indices, allow_pickle=False)
    _write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "shard_index": shard_index,
        "item_index_start": start,
        "item_index_stop_exclusive": stop,
        "item_count": len(shard_items),
        "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        "depth_item_local_indices": depth_local_indices.tolist(),
        "broad_activation_shape": list(broad.shape),
        "depth_activation_shape": list(depth.shape),
        "activation_dtype": "float32",
        "broad_axis_order": config["acquisition"]["broad_axis_order"],
        "depth_axis_order": config["acquisition"]["depth_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": distances,
        "broad_endpoint_order": list(BROAD_ENDPOINT_ORDER),
        "depth_endpoint_order": list(DEPTH_ENDPOINT_ORDER),
        "depth_hidden_state_indices": list(depth_indices),
        "unique_input_sequences": len(records),
        "model_forward_calls": forward_calls,
        "broad_readout_vectors": broad_vectors,
        "depth_readout_vectors": depth_vectors,
        "total_stored_readout_vectors": broad_vectors + depth_vectors,
        "endpoint_delta_first_forward_max_abs": endpoint_delta_first_forward,
        "fused_distance_readout": True,
        "batch_size_unique_sequences": 1,
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
        "peak_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "model": dict(model_receipt),
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "runtime_preflight_aggregate_sha256": _sha256(preflight_directory / "aggregate.json"),
        "tokenizer_receipt_sha256": _sha256(preflight_directory / f"{role}.json"),
        "outputs": {
            name: _sha256(stage / name)
            for name in (
                "execution_intent.json",
                "broad_activations.npy",
                "depth_activations.npy",
                "view_mask.npy",
                "depth_item_local_indices.npy",
                "observations.jsonl",
            )
        },
        "reserve_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_decision_authorized": False,
    }
    atlas._write_json(stage / "shard_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        (
            "execution_intent.json",
            "broad_activations.npy",
            "depth_activations.npy",
            "view_mask.npy",
            "depth_item_local_indices.npy",
            "observations.jsonl",
            "shard_receipt.json",
        ),
    )
    stage.rename(final)
    return receipt


def validate_shard(directory: Path) -> dict[str, Any]:
    config = _config()
    names = (
        "execution_intent.json",
        "broad_activations.npy",
        "depth_activations.npy",
        "view_mask.npy",
        "depth_item_local_indices.npy",
        "observations.jsonl",
        "shard_receipt.json",
        "SHA256SUMS",
    )
    for name in names:
        _require((directory / name).is_file(), f"Missing T11 shard file: {name}")
    _validate_ledger(directory, names[:-1])
    receipt = atlas._read_json(directory / "shard_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T11 shard receipt mismatch")
    role = str(receipt["model_role"])
    _require(role in model_roles(), "T11 shard role mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"T11 shard output hash mismatch: {name}")
    index = int(receipt["shard_index"])
    size = int(config["acquisition"]["item_shard_size"])
    expected_items = selection_items(acquired_only=True)[index * size : (index + 1) * size]
    _require(receipt["item_codepoints"] == [str(item["codepoint"]) for item in expected_items], "T11 shard population changed")
    width = int(_model_spec(role)["expected_model_dim"])
    broad = np.load(directory / "broad_activations.npy", mmap_mode="r", allow_pickle=False)
    depth = np.load(directory / "depth_activations.npy", mmap_mode="r", allow_pickle=False)
    view_mask = np.load(directory / "view_mask.npy", mmap_mode="r", allow_pickle=False)
    depth_indices = np.load(directory / "depth_item_local_indices.npy", allow_pickle=False)
    expected_view_mask = np.asarray(
        [[view in _available_views(item) for view in VIEW_ORDER] for item in expected_items],
        dtype=np.bool_,
    )
    expected_depth_indices = np.asarray(
        [i for i, item in enumerate(expected_items) if bool(item["included_in_depth_subset"])],
        dtype=np.int64,
    )
    _require(tuple(broad.shape) == (len(expected_items), 5, 2, 4, 2, width), "T11 broad shard shape mismatch")
    _require(tuple(depth.shape) == (len(expected_depth_indices), 5, 2, 4, 6, width), "T11 depth shard shape mismatch")
    _require(np.array_equal(view_mask, expected_view_mask), "T11 shard view mask changed")
    _require(np.array_equal(depth_indices, expected_depth_indices), "T11 shard depth indices changed")
    _require(str(broad.dtype) == "float32" and str(depth.dtype) == "float32", "T11 activation dtype changed")
    _require(bool(np.isfinite(broad[expected_view_mask]).all()), "T11 present broad shard value is nonfinite")
    _require(bool(np.isnan(broad[~expected_view_mask]).all()), "T11 absent broad shard value is not NaN")
    depth_mask = expected_view_mask[expected_depth_indices]
    _require(bool(np.isfinite(depth[depth_mask]).all()), "T11 present depth shard value is nonfinite")
    _require(bool(np.isnan(depth[~depth_mask]).all()), "T11 absent depth shard value is not NaN")
    expected_forwards = sum(len(_available_views(item)) for item in expected_items) * 2
    expected_broad_vectors = expected_forwards * 4 * 2
    expected_depth_vectors = sum(
        len(_available_views(item)) for item in expected_items if item["included_in_depth_subset"]
    ) * 2 * 4 * 6
    _require(int(receipt["model_forward_calls"]) == expected_forwards, "T11 shard forward count mismatch")
    _require(int(receipt["broad_readout_vectors"]) == expected_broad_vectors, "T11 broad vector count mismatch")
    _require(int(receipt["depth_readout_vectors"]) == expected_depth_vectors, "T11 depth vector count mismatch")
    return {
        "status": "pass",
        "model_role": role,
        "shard_index": index,
        "item_count": len(expected_items),
        "model_forward_calls": expected_forwards,
    }


def run_shards(
    role: str,
    model_path: Path,
    preflight_directory: Path,
    run_root: Path,
    shard_start: int,
    shard_stop: int | None,
) -> dict[str, Any]:
    audit_freeze()
    _validate_runtime_preflight(preflight_directory)
    config = _config()
    expected = int(config["acquisition"]["expected_shards_per_model"])
    stop = expected if shard_stop is None else shard_stop
    _require(0 <= shard_start < stop <= expected, "Invalid T11 shard range")
    run_root.mkdir(parents=True, exist_ok=True)
    _require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete T11 shard requires manual adjudication")
    _require(not (run_root / "run_receipt.json").exists(), "T11 run is already finalized")
    lock = run_root / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise T11Error("T11 run root already has a writer") from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    os.close(descriptor)
    events: list[dict[str, Any]] = []
    model = None
    status = "fail"
    try:
        pending = [
            index
            for index in range(shard_start, stop)
            if not (run_root / f"shard_{index:04d}").exists()
        ]
        for index in range(shard_start, stop):
            path = run_root / f"shard_{index:04d}"
            if path.exists():
                validate_shard(path)
        if not pending:
            status = "pass"
            return {"status": status, "message": "requested T11 shards already complete", "events": []}
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before T11 model load: {foreign}")
        torch, tokenizer, model, last_block, model_receipt, roster = _load_model(
            role, model_path, preflight_directory
        )
        for index in pending:
            foreign = atlas._foreign_gpu_pids()
            if foreign:
                raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before T11 shard {index}: {foreign}")
            receipt = _run_one_shard(
                role=role,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                last_block=last_block,
                model_receipt=model_receipt,
                roster=roster,
                run_root=run_root,
                shard_index=index,
                preflight_directory=preflight_directory,
            )
            events.append(
                {
                    key: receipt[key]
                    for key in (
                        "shard_index",
                        "item_count",
                        "model_forward_calls",
                        "broad_readout_vectors",
                        "depth_readout_vectors",
                        "elapsed_ms",
                    )
                }
            )
        status = "pass"
    except atlas.ContentionDetected as exc:
        status = "yielded_on_contention"
        events.append({"contention": str(exc)})
    finally:
        if model is not None:
            del model
            import torch

            torch.cuda.empty_cache()
        lock.unlink(missing_ok=True)
        atlas._write_json(
            run_root
            / f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}.json",
            {
                "schema_version": SCHEMA_VERSION,
                "protocol_id": PROTOCOL_ID,
                "model_role": role,
                "status": status,
                "requested_shard_start": shard_start,
                "requested_shard_stop_exclusive": stop,
                "events": events,
            },
        )
    return {"status": status, "events": events}


def finalize_run(role: str, preflight_directory: Path, run_root: Path) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    aggregate = _validate_runtime_preflight(preflight_directory)
    _require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete T11 shard blocks finalization")
    _require(not (run_root / "run_receipt.json").exists(), "T11 run is already finalized")
    receipts: list[dict[str, Any]] = []
    ledgers: dict[str, str] = {}
    for index in range(int(config["acquisition"]["expected_shards_per_model"])):
        directory = run_root / f"shard_{index:04d}"
        result = validate_shard(directory)
        _require(result["model_role"] == role, "T11 run contains another model role")
        receipts.append(atlas._read_json(directory / "shard_receipt.json"))
        ledgers[directory.name] = _sha256(directory / "SHA256SUMS")
    item_count = sum(int(row["item_count"]) for row in receipts)
    forwards = sum(int(row["model_forward_calls"]) for row in receipts)
    broad_vectors = sum(int(row["broad_readout_vectors"]) for row in receipts)
    depth_vectors = sum(int(row["depth_readout_vectors"]) for row in receipts)
    _require(item_count == int(config["selection"]["expected_acquired_items"]), "T11 finalized item count mismatch")
    _require(forwards == int(config["acquisition"]["expected_model_forward_calls_per_model"]), "T11 finalized forward count mismatch")
    _require(broad_vectors == int(config["acquisition"]["expected_broad_readout_vectors_per_model"]), "T11 finalized broad vector count mismatch")
    _require(depth_vectors == int(config["acquisition"]["expected_depth_readout_vectors_per_model"]), "T11 finalized depth vector count mismatch")
    model_receipts = {json.dumps(row["model"], sort_keys=True) for row in receipts}
    _require(len(model_receipts) == 1, "T11 model receipt changed across shards")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "runtime_preflight_aggregate_sha256": _sha256(preflight_directory / "aggregate.json"),
        "tokenizer_receipt_sha256": aggregate["tokenizer_receipt_sha256"][role],
        "item_count": item_count,
        "reserve_item_count": int(config["selection"]["expected_reserve_items"]),
        "reserve_model_forward_calls": 0,
        "unique_input_sequences": forwards,
        "model_forward_calls": forwards,
        "broad_readout_vectors": broad_vectors,
        "depth_readout_vectors": depth_vectors,
        "total_stored_readout_vectors": broad_vectors + depth_vectors,
        "shard_count": len(receipts),
        "shard_ledger_sha256": ledgers,
        "activation_dtype": "float32",
        "broad_axis_order": config["acquisition"]["broad_axis_order"],
        "depth_axis_order": config["acquisition"]["depth_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": config["input"]["distance_order"],
        "broad_endpoint_order": list(BROAD_ENDPOINT_ORDER),
        "depth_endpoint_order": list(DEPTH_ENDPOINT_ORDER),
        "model": receipts[0]["model"],
        "peak_cuda_memory_bytes": max(int(row["peak_cuda_memory_bytes"]) for row in receipts),
        "elapsed_ms": sum(float(row["elapsed_ms"]) for row in receipts),
        "acquisition_status": "complete_summary_pending",
        "intervention_calls": 0,
        "generation_calls": 0,
        "raw_activations_committed_to_git": False,
        "raw_activations_put_on_spiralshare": False,
    }
    atlas._write_json(run_root / "run_receipt.json", receipt)
    atlas._write_json(
        run_root / "SHARD_INDEX.json",
        {"protocol_id": PROTOCOL_ID, "model_role": role, "shards": ledgers},
    )
    atlas._write_ledger(run_root, ("run_receipt.json", "SHARD_INDEX.json"))
    return receipt


def validate_run(directory: Path) -> dict[str, Any]:
    for name in ("run_receipt.json", "SHARD_INDEX.json", "SHA256SUMS"):
        _require((directory / name).is_file(), f"Missing T11 run file: {name}")
    _validate_ledger(directory, ("run_receipt.json", "SHARD_INDEX.json"))
    receipt = atlas._read_json(directory / "run_receipt.json")
    shard_index = atlas._read_json(directory / "SHARD_INDEX.json")
    role = str(receipt["model_role"])
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T11 run receipt mismatch")
    _require(receipt.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T11 run freeze mismatch")
    _require(receipt.get("reserve_model_forward_calls") == 0, "T11 reserve was forwarded")
    _require(shard_index.get("protocol_id") == PROTOCOL_ID, "T11 shard index protocol mismatch")
    _require(shard_index.get("model_role") == role, "T11 shard index role mismatch")
    totals = {"item_count": 0, "model_forward_calls": 0}
    for index in range(int(_config()["acquisition"]["expected_shards_per_model"])):
        shard_name = f"shard_{index:04d}"
        result = validate_shard(directory / shard_name)
        _require(result["model_role"] == role, "T11 run role changed")
        totals["item_count"] += int(result["item_count"])
        totals["model_forward_calls"] += int(result["model_forward_calls"])
        _require(
            shard_index["shards"][shard_name]
            == _sha256(directory / shard_name / "SHA256SUMS"),
            "T11 shard ledger binding changed",
        )
    _require(
        set(shard_index["shards"])
        == {f"shard_{index:04d}" for index in range(int(_config()["acquisition"]["expected_shards_per_model"]))},
        "T11 shard index roster changed",
    )
    _require(int(receipt["item_count"]) == totals["item_count"], "T11 run item total changed")
    _require(
        int(receipt["model_forward_calls"]) == totals["model_forward_calls"],
        "T11 run forward total changed",
    )
    return {"status": "pass", "model_role": role, "receipt": receipt}


def _load_run_arrays(run_root: Path) -> dict[str, Any]:
    config = _config()
    broad_arrays: list[np.ndarray] = []
    depth_arrays: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    depth_global_indices: list[int] = []
    for index in range(int(config["acquisition"]["expected_shards_per_model"])):
        directory = run_root / f"shard_{index:04d}"
        receipt = atlas._read_json(directory / "shard_receipt.json")
        broad_arrays.append(np.load(directory / "broad_activations.npy", mmap_mode="r", allow_pickle=False))
        depth_arrays.append(np.load(directory / "depth_activations.npy", mmap_mode="r", allow_pickle=False))
        masks.append(np.load(directory / "view_mask.npy", mmap_mode="r", allow_pickle=False))
        start = int(receipt["item_index_start"])
        depth_global_indices.extend(start + int(value) for value in receipt["depth_item_local_indices"])
    broad = np.concatenate([np.asarray(value) for value in broad_arrays], axis=0)
    depth = np.concatenate([np.asarray(value) for value in depth_arrays], axis=0)
    view_mask = np.concatenate([np.asarray(value) for value in masks], axis=0)
    depth_indices = np.asarray(depth_global_indices, dtype=np.int64)
    _require(broad.shape[0] == int(config["selection"]["expected_acquired_items"]), "T11 broad run population changed")
    _require(depth.shape[0] == int(config["depth_subset"]["expected_items"]), "T11 depth run population changed")
    _require(np.array_equal(depth_indices, np.sort(depth_indices)), "T11 depth run order changed")
    return {
        "broad": broad,
        "depth": depth,
        "view_mask": view_mask,
        "depth_global_indices": depth_indices,
    }


def _center_normalize(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(values, dtype=np.float64)
    centered = array - np.mean(array, axis=0, keepdims=True)
    normalized = centered / np.maximum(np.linalg.norm(centered, axis=1, keepdims=True), 1e-12)
    return centered, normalized


def _pair_metrics(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    centered_left, normalized_left = _center_normalize(left)
    centered_right, normalized_right = _center_normalize(right)
    similarity = normalized_left @ normalized_right.T
    count = int(similarity.shape[0])
    order = np.arange(count, dtype=np.int64)
    diagonal = np.diag(similarity)
    forward = np.argmax(similarity, axis=1).astype(np.int64)
    reverse = np.argmax(similarity, axis=0).astype(np.int64)
    ranks_forward = 1 + np.sum(similarity > diagonal[:, None], axis=1)
    ranks_reverse = 1 + np.sum(similarity > diagonal[None, :], axis=0)
    top_decile_target_count = max(1, int(math.ceil(0.10 * count)))

    def retrieval_distribution(prediction: np.ndarray) -> dict[str, Any]:
        counts = np.bincount(prediction, minlength=count)
        descending = np.sort(counts)[::-1]
        return {
            "retrieved_unique_target_count": int(np.count_nonzero(counts)),
            "retrieval_breadth_fraction": float(np.count_nonzero(counts) / count),
            "top_decile_target_count": top_decile_target_count,
            "top_decile_prediction_concentration": float(
                np.sum(descending[:top_decile_target_count]) / count
            ),
            "maximum_single_target_prediction_fraction": float(np.max(counts) / count),
        }

    off_diagonal = float(
        (np.sum(similarity) - np.sum(diagonal)) / max(1, count * (count - 1))
    )
    gram_left = centered_left @ centered_left.T
    gram_right = centered_right @ centered_right.T
    denominator = math.sqrt(
        float(np.sum(np.square(gram_left))) * float(np.sum(np.square(gram_right)))
    )
    return {
        "item_count": count,
        "paired_cosine_mean": float(np.mean(diagonal)),
        "off_diagonal_cosine_mean": off_diagonal,
        "paired_minus_off_diagonal_margin": float(np.mean(diagonal) - off_diagonal),
        "top1_accuracy_forward": float(np.mean(forward == order)),
        "top1_accuracy_reverse": float(np.mean(reverse == order)),
        "mean_reciprocal_rank_forward": float(np.mean(1.0 / ranks_forward)),
        "mean_reciprocal_rank_reverse": float(np.mean(1.0 / ranks_reverse)),
        "retrieval_distribution_forward": retrieval_distribution(forward),
        "retrieval_distribution_reverse": retrieval_distribution(reverse),
        "centered_linear_cka": float(np.sum(gram_left * gram_right) / max(denominator, 1e-30)),
        "forward_prediction": forward,
        "reverse_prediction": reverse,
        "paired_cosine": diagonal,
        "similarity": similarity,
    }


def _public_pair_metrics(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in (
            "item_count",
            "paired_cosine_mean",
            "off_diagonal_cosine_mean",
            "paired_minus_off_diagonal_margin",
            "top1_accuracy_forward",
            "top1_accuracy_reverse",
            "mean_reciprocal_rank_forward",
            "mean_reciprocal_rank_reverse",
            "retrieval_distribution_forward",
            "retrieval_distribution_reverse",
            "centered_linear_cka",
        )
    }


def _local_control_mapping(
    controls: Mapping[str, Any],
    system_global_indices: Sequence[int],
) -> np.ndarray:
    local = {int(value): index for index, value in enumerate(system_global_indices)}
    mapping = np.full(len(system_global_indices), -1, dtype=np.int64)
    for row in controls["mapping"]:
        source = int(row["item_index"])
        target = int(row["wrong_target_item_index"])
        if source in local and target in local:
            mapping[local[source]] = local[target]
    _require(int(np.sum(mapping >= 0)) == int(controls["eligible_item_count"]), "T11 local control coverage changed")
    _require(bool(np.all(mapping[mapping >= 0] != np.arange(len(mapping))[mapping >= 0])), "T11 local control has self match")
    return mapping


def _matched_advantage(pair: Mapping[str, Any], mapping: np.ndarray) -> np.ndarray:
    similarity = np.asarray(pair["similarity"], dtype=np.float64)
    output = np.full(len(mapping), np.nan, dtype=np.float64)
    eligible = np.flatnonzero(mapping >= 0)
    output[eligible] = np.diag(similarity)[eligible] - similarity[eligible, mapping[eligible]]
    return output


def _bootstrap_summary(values: np.ndarray, *, seed: int, draws: int) -> dict[str, Any]:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    _require(finite.size > 0, "T11 matched margin is empty")
    rng = np.random.default_rng(seed)
    samples = np.median(
        finite[rng.integers(0, finite.size, size=(draws, finite.size))], axis=1
    )
    return {
        "eligible_item_count": int(finite.size),
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "standard_deviation": float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0,
        "positive_item_fraction": float(np.mean(finite > 0)),
        "bootstrap_draws": draws,
        "bootstrap_seed": seed,
        "bootstrap_percentile_95_interval": [
            float(np.quantile(samples, 0.025)),
            float(np.quantile(samples, 0.975)),
        ],
        "decision_authorized": False,
    }


def _system_indices(items: Sequence[Mapping[str, Any]], system: str) -> list[int]:
    return [int(item["acquisition_index"]) for item in items if item["glyph_system"] == system]


def _system_cell(
    values: np.ndarray,
    *,
    system: str,
    global_indices: Sequence[int],
    controls: Mapping[str, Any],
    seed: int,
    draws: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    available = set(_available_views(selection_items(acquired_only=True)[int(global_indices[0])]))
    view_arrays = {
        view: np.asarray(values[np.asarray(global_indices), VIEW_ORDER.index(view), :], dtype=np.float32)
        for view in available
    }
    pair_specs = {
        "glyph_unicode_name": ("glyph", "unicode_name"),
        "glyph_codepoint_literal": ("glyph", "codepoint_literal"),
    }
    if "component_name" in available:
        pair_specs.update(
            {
                "glyph_component_name": ("glyph", "component_name"),
                "decomposed_form_unicode_name": ("decomposed_form", "unicode_name"),
                "decomposed_form_component_name": ("decomposed_form", "component_name"),
            }
        )
    pairs = {
        name: _pair_metrics(view_arrays[left], view_arrays[right])
        for name, (left, right) in pair_specs.items()
    }
    item_arrays: dict[str, np.ndarray] = {}
    matched: dict[str, Any] = {}
    strict_sensitivity: dict[str, Any] = {}
    if "unicode_name" in controls and system in controls["unicode_name"]:
        mapping = _local_control_mapping(
            controls["unicode_name"][system]["required"], global_indices
        )
        item_arrays["glyph_unicode_name_matched_advantage"] = _matched_advantage(
            pairs["glyph_unicode_name"], mapping
        )
        matched["glyph_unicode_name"] = _bootstrap_summary(
            item_arrays["glyph_unicode_name_matched_advantage"], seed=seed + 1, draws=draws
        )
        if "decomposed_form_unicode_name" in pairs:
            item_arrays["decomposed_form_unicode_name_matched_advantage"] = _matched_advantage(
                pairs["decomposed_form_unicode_name"], mapping
            )
            matched["decomposed_form_unicode_name"] = _bootstrap_summary(
                item_arrays["decomposed_form_unicode_name_matched_advantage"], seed=seed + 2, draws=draws
            )
        strict_control = controls["unicode_name"][system]["strict_prefix_sensitivity"]
        strict_sensitivity["unicode_name"] = {
            "control_coverage": float(strict_control["coverage"]),
            "eligible_item_count": int(strict_control["eligible_item_count"]),
            "pairs": {},
        }
        if int(strict_control["eligible_item_count"]) > 0:
            strict_mapping = _local_control_mapping(strict_control, global_indices)
            strict_name = "strict_prefix__glyph_unicode_name_matched_advantage"
            item_arrays[strict_name] = _matched_advantage(
                pairs["glyph_unicode_name"], strict_mapping
            )
            strict_sensitivity["unicode_name"]["pairs"]["glyph_unicode_name"] = (
                _bootstrap_summary(item_arrays[strict_name], seed=seed + 31, draws=draws)
            )
            if "decomposed_form_unicode_name" in pairs:
                strict_name = "strict_prefix__decomposed_form_unicode_name_matched_advantage"
                item_arrays[strict_name] = _matched_advantage(
                    pairs["decomposed_form_unicode_name"], strict_mapping
                )
                strict_sensitivity["unicode_name"]["pairs"][
                    "decomposed_form_unicode_name"
                ] = _bootstrap_summary(item_arrays[strict_name], seed=seed + 32, draws=draws)
    if "component_name" in controls and system in controls["component_name"]:
        mapping = _local_control_mapping(
            controls["component_name"][system]["required"], global_indices
        )
        item_arrays["glyph_component_name_matched_advantage"] = _matched_advantage(
            pairs["glyph_component_name"], mapping
        )
        item_arrays["decomposed_form_component_name_matched_advantage"] = _matched_advantage(
            pairs["decomposed_form_component_name"], mapping
        )
        matched["glyph_component_name"] = _bootstrap_summary(
            item_arrays["glyph_component_name_matched_advantage"], seed=seed + 3, draws=draws
        )
        matched["decomposed_form_component_name"] = _bootstrap_summary(
            item_arrays["decomposed_form_component_name_matched_advantage"], seed=seed + 4, draws=draws
        )
        strict_control = controls["component_name"][system]["strict_prefix_sensitivity"]
        strict_sensitivity["component_name"] = {
            "control_coverage": float(strict_control["coverage"]),
            "eligible_item_count": int(strict_control["eligible_item_count"]),
            "pairs": {},
        }
        if int(strict_control["eligible_item_count"]) > 0:
            strict_mapping = _local_control_mapping(strict_control, global_indices)
            for offset, pair_name in enumerate(
                ("glyph_component_name", "decomposed_form_component_name")
            ):
                strict_name = f"strict_prefix__{pair_name}_matched_advantage"
                item_arrays[strict_name] = _matched_advantage(pairs[pair_name], strict_mapping)
                strict_sensitivity["component_name"]["pairs"][pair_name] = (
                    _bootstrap_summary(
                        item_arrays[strict_name], seed=seed + 33 + offset, draws=draws
                    )
                )
    contrasts: dict[str, Any] = {}
    if "glyph_component_name_matched_advantage" in item_arrays:
        item_arrays["lexicalization"] = (
            item_arrays["glyph_unicode_name_matched_advantage"]
            - item_arrays["glyph_component_name_matched_advantage"]
        )
        item_arrays["presentation_or_fusion"] = (
            item_arrays["glyph_unicode_name_matched_advantage"]
            - item_arrays["decomposed_form_unicode_name_matched_advantage"]
        )
        item_arrays["component_tracking"] = (
            item_arrays["decomposed_form_component_name_matched_advantage"]
            - item_arrays["glyph_component_name_matched_advantage"]
        )
        contrasts = {
            name: _bootstrap_summary(item_arrays[name], seed=seed + 10 + index, draws=draws)
            for index, name in enumerate(("lexicalization", "presentation_or_fusion", "component_tracking"))
        }
    public_pairs = {name: _public_pair_metrics(value) for name, value in pairs.items()}
    return (
        {
            "glyph_system": system,
            "item_count": len(global_indices),
            "pairs": public_pairs,
            "matched_incorrect_label_advantage": matched,
            "strict_prefix_matched_sensitivity": strict_sensitivity,
            "decomposition_contrasts": contrasts,
        },
        item_arrays,
    )


def summarize_model(
    run_root: Path,
    preflight_directory: Path,
    output: Path,
) -> dict[str, Any]:
    validated = validate_run(run_root)
    role = str(validated["model_role"])
    receipt = _validate_tokenizer_receipt(preflight_directory / f"{role}.json", role)
    controls = receipt["tokenizer"]["matched_incorrect_label_controls"]
    depth_controls = receipt["tokenizer"]["depth_matched_incorrect_label_controls"]
    arrays = _load_run_arrays(run_root)
    broad = arrays["broad"]
    depth = arrays["depth"]
    depth_global = [int(value) for value in arrays["depth_global_indices"]]
    depth_position = {value: index for index, value in enumerate(depth_global)}
    items = selection_items(acquired_only=True)
    config = _config()
    systems = [str(value) for value in config["selection"]["system_order"]]
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    draws = int(config["analysis"]["aggregation"]["bootstrap_draws"])
    seed_base = int(config["analysis"]["aggregation"]["bootstrap_seed"])
    broad_rows: list[dict[str, Any]] = []
    depth_rows: list[dict[str, Any]] = []
    item_arrays: dict[str, np.ndarray] = {}

    for endpoint_index, endpoint in enumerate(BROAD_ENDPOINT_ORDER):
        for carrier_index, carrier in enumerate(carriers):
            for distance_index, distance in enumerate(distances):
                cell = carrier_index * len(distances) + distance_index
                cell_values = broad[:, :, carrier_index, distance_index, endpoint_index, :]
                for system_index, system in enumerate(systems):
                    indices = _system_indices(items, system)
                    row_seed = seed_base + model_roles().index(role) * 100_000 + endpoint_index * 10_000 + cell * 100 + system_index * 20
                    metrics, values = _system_cell(
                        cell_values,
                        system=system,
                        global_indices=indices,
                        controls=controls,
                        seed=row_seed,
                        draws=draws,
                    )
                    row = {
                        "model_role": role,
                        "endpoint": endpoint,
                        "carrier": carrier,
                        "carrier_index": carrier_index,
                        "distance": distance,
                        "distance_index": distance_index,
                        "cell_index": cell,
                        **metrics,
                    }
                    broad_rows.append(row)
                    for name, value in values.items():
                        item_arrays[f"broad__{endpoint}__{carrier}__d{distance}__{system}__{name}"] = value

    for endpoint_index, endpoint in enumerate(DEPTH_ENDPOINT_ORDER):
        for carrier_index, carrier in enumerate(carriers):
            for distance_index, distance in enumerate(distances):
                cell = carrier_index * len(distances) + distance_index
                cell_values = depth[:, :, carrier_index, distance_index, endpoint_index, :]
                for system_index, system in enumerate(systems):
                    global_indices = [
                        int(item["acquisition_index"])
                        for item in items
                        if item["glyph_system"] == system and item["included_in_depth_subset"]
                    ]
                    if not global_indices:
                        continue
                    local_indices = [depth_position[index] for index in global_indices]
                    local_values = cell_values[np.asarray(local_indices)]
                    # _system_cell indexes its first axis by the supplied indices.
                    remapped_values = np.empty(
                        (len(items), len(VIEW_ORDER), local_values.shape[-1]), dtype=np.float32
                    )
                    remapped_values.fill(np.nan)
                    remapped_values[np.asarray(global_indices)] = local_values
                    row_seed = seed_base + model_roles().index(role) * 100_000 + 50_000 + endpoint_index * 5_000 + cell * 100 + system_index * 20
                    metrics, values = _system_cell(
                        remapped_values,
                        system=system,
                        global_indices=global_indices,
                        controls=depth_controls,
                        seed=row_seed,
                        draws=draws,
                    )
                    depth_rows.append(
                        {
                            "model_role": role,
                            "endpoint": endpoint,
                            "carrier": carrier,
                            "carrier_index": carrier_index,
                            "distance": distance,
                            "distance_index": distance_index,
                            "cell_index": cell,
                            **metrics,
                        }
                    )
                    for name, value in values.items():
                        item_arrays[f"depth__{endpoint}__{carrier}__d{distance}__{system}__{name}"] = value

    _require(not output.exists(), f"T11 summary output exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.partial-", dir=output.parent))
    _write_jsonl(stage / "broad_system_cell_metrics.jsonl", broad_rows)
    _write_jsonl(stage / "depth_system_cell_metrics.jsonl", depth_rows)
    np.savez_compressed(stage / "item_margins.npz", **item_arrays)
    summary_receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "analysis_role": "exploratory_discovery_only_model_summary",
        "run_receipt_sha256": _sha256(run_root / "run_receipt.json"),
        "tokenizer_receipt_sha256": _sha256(preflight_directory / f"{role}.json"),
        "broad_row_count": len(broad_rows),
        "depth_row_count": len(depth_rows),
        "item_margin_array_count": len(item_arrays),
        "outputs": {
            name: _sha256(stage / name)
            for name in (
                "broad_system_cell_metrics.jsonl",
                "depth_system_cell_metrics.jsonl",
                "item_margins.npz",
            )
        },
        "model_forward_calls": 0,
        "reserve_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_decision_authorized": False,
    }
    atlas._write_json(stage / "summary_receipt.json", summary_receipt)
    atlas._write_ledger(
        stage,
        (
            "broad_system_cell_metrics.jsonl",
            "depth_system_cell_metrics.jsonl",
            "item_margins.npz",
            "summary_receipt.json",
        ),
    )
    stage.rename(output)
    return summary_receipt


def validate_summary(directory: Path) -> dict[str, Any]:
    for name in (
        "broad_system_cell_metrics.jsonl",
        "depth_system_cell_metrics.jsonl",
        "item_margins.npz",
        "summary_receipt.json",
        "SHA256SUMS",
    ):
        _require((directory / name).is_file(), f"Missing T11 summary file: {name}")
    _validate_ledger(
        directory,
        (
            "broad_system_cell_metrics.jsonl",
            "depth_system_cell_metrics.jsonl",
            "item_margins.npz",
            "summary_receipt.json",
        ),
    )
    receipt = atlas._read_json(directory / "summary_receipt.json")
    role = str(receipt["model_role"])
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T11 summary receipt mismatch")
    _require(role in model_roles(), "T11 summary role mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"T11 summary hash mismatch: {name}")
    _require(receipt.get("reserve_model_forward_calls") == 0, "T11 summary reserve gate changed")
    _require(receipt.get("scientific_decision_authorized") is False, "T11 summary became decisive")
    return {"status": "pass", "model_role": role, "receipt": receipt}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _rankdata(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(array.size, dtype=np.float64)
    start = 0
    while start < array.size:
        stop = start + 1
        while stop < array.size and array[order[stop]] == array[order[start]]:
            stop += 1
        ranks[order[start:stop]] = 0.5 * (start + stop - 1) + 1.0
        start = stop
    return ranks


def _safe_spearman(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64).ravel()
    b = np.asarray(right, dtype=np.float64).ravel()
    finite = np.isfinite(a) & np.isfinite(b)
    a = a[finite]
    b = b[finite]
    if a.size < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return 0.0
    ranked_a = _rankdata(a)
    ranked_b = _rankdata(b)
    return float(np.corrcoef(ranked_a, ranked_b)[0, 1])


def _linear_cka(left: np.ndarray, right: np.ndarray) -> float:
    centered_left, _ = _center_normalize(left)
    centered_right, _ = _center_normalize(right)
    gram_left = centered_left @ centered_left.T
    gram_right = centered_right @ centered_right.T
    denominator = math.sqrt(
        float(np.sum(np.square(gram_left))) * float(np.sum(np.square(gram_right)))
    )
    return float(np.sum(gram_left * gram_right) / max(denominator, 1e-30))


def _distribution(values: Iterable[float]) -> dict[str, Any]:
    array = np.asarray(list(values), dtype=np.float64)
    array = array[np.isfinite(array)]
    _require(array.size > 0, "T11 distribution is empty")
    return {
        "count": int(array.size),
        "minimum": float(np.min(array)),
        "median": float(np.median(array)),
        "maximum": float(np.max(array)),
        "positive_fraction": float(np.mean(array > 0)),
    }


def _context_summary(values: Sequence[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    _require(array.size == 8, "T11 context grid changed")
    median = float(np.median(array))
    return {
        "cell_count": 8,
        "minimum": float(np.min(array)),
        "median": median,
        "maximum": float(np.max(array)),
        "positive_cell_fraction": float(np.mean(array > 0)),
        "median_absolute_deviation": float(np.median(np.abs(array - median))),
    }


def _aggregate_summary_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    roles = model_roles()
    systems = [str(value) for value in _config()["selection"]["system_order"]]
    endpoints = sorted({str(row["endpoint"]) for row in rows})
    for role in roles:
        output[role] = {}
        for system in systems:
            output[role][system] = {}
            for endpoint in endpoints:
                selected = [
                    row
                    for row in rows
                    if row["model_role"] == role
                    and row["glyph_system"] == system
                    and row["endpoint"] == endpoint
                ]
                if not selected:
                    continue
                selected.sort(key=lambda row: int(row["cell_index"]))
                metrics: dict[str, Any] = {}
                for name in (
                    "glyph_unicode_name",
                    "glyph_component_name",
                    "decomposed_form_unicode_name",
                    "decomposed_form_component_name",
                ):
                    values = [
                        float(row["matched_incorrect_label_advantage"][name]["median"])
                        for row in selected
                        if name in row["matched_incorrect_label_advantage"]
                    ]
                    if values:
                        metrics[f"matched_{name}"] = _context_summary(values)
                for name in ("lexicalization", "presentation_or_fusion", "component_tracking"):
                    values = [
                        float(row["decomposition_contrasts"][name]["median"])
                        for row in selected
                        if name in row["decomposition_contrasts"]
                    ]
                    if values:
                        metrics[name] = _context_summary(values)
                output[role][system][endpoint] = metrics
    return output


def _cross_model_geometry(
    run_arrays: Mapping[str, Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    systems = [str(value) for value in _config()["selection"]["system_order"]]
    for system in systems:
        indices = _system_indices(items, system)
        available = _available_views(items[indices[0]])
        pair_specs = {
            "glyph_to_unicode_name": ("glyph", "unicode_name"),
            "glyph_to_codepoint_literal": ("glyph", "codepoint_literal"),
        }
        if "component_name" in available:
            pair_specs.update(
                {
                    "glyph_to_component_name": ("glyph", "component_name"),
                    "decomposed_form_to_unicode_name": (
                        "decomposed_form",
                        "unicode_name",
                    ),
                    "decomposed_form_to_component_name": (
                        "decomposed_form",
                        "component_name",
                    ),
                }
            )
        for endpoint_index, endpoint in enumerate(BROAD_ENDPOINT_ORDER):
            for carrier_index, carrier in enumerate(("article_a", "pipe")):
                for distance_index, distance in enumerate((1, 2, 4, 8)):
                    cell = carrier_index * 4 + distance_index
                    view_values = {
                        role: {
                            view: run_arrays[role]["broad"][
                                np.asarray(indices),
                                VIEW_ORDER.index(view),
                                carrier_index,
                                distance_index,
                                endpoint_index,
                                :,
                            ]
                            for view in available
                        }
                        for role in model_roles()
                    }
                    for pair_name, (left_view, right_view) in pair_specs.items():
                        similarity_by_role = {
                            role: _pair_metrics(
                                view_values[role][left_view], view_values[role][right_view]
                            )["similarity"]
                            for role in model_roles()
                        }
                        map_correlations = [
                            _safe_spearman(
                                similarity_by_role[left], similarity_by_role[right]
                            )
                            for left_index, left in enumerate(model_roles())
                            for right in model_roles()[left_index + 1 :]
                        ]
                        rows.append(
                            {
                                "glyph_system": system,
                                "endpoint": endpoint,
                                "carrier": carrier,
                                "distance": distance,
                                "cell_index": cell,
                                "analysis_axis": "full_cross_view_cosine_map",
                                "view_or_pair": pair_name,
                                "model_pair_metric": "spearman",
                                **_distribution(map_correlations),
                            }
                        )
                    for view in available:
                        values_by_role = {
                            role: view_values[role][view]
                            for role in model_roles()
                        }
                        pair_values = [
                            _linear_cka(values_by_role[left], values_by_role[right])
                            for left_index, left in enumerate(model_roles())
                            for right in model_roles()[left_index + 1 :]
                        ]
                        rows.append(
                            {
                                "glyph_system": system,
                                "endpoint": endpoint,
                                "carrier": carrier,
                                "distance": distance,
                                "cell_index": cell,
                                "analysis_axis": "per_view_item_geometry",
                                "view_or_pair": view,
                                "model_pair_metric": "centered_linear_cka",
                                **_distribution(pair_values),
                            }
                        )
    return rows


def _item_margin_agreement(
    summary_directories: Mapping[str, Path],
) -> list[dict[str, Any]]:
    stored = {
        role: np.load(summary_directories[role] / "item_margins.npz", allow_pickle=False)
        for role in model_roles()
    }
    try:
        keys = sorted(set.intersection(*(set(value.files) for value in stored.values())))
        rows: list[dict[str, Any]] = []
        for key in keys:
            if not key.endswith("__glyph_unicode_name_matched_advantage"):
                continue
            correlations = [
                _safe_spearman(stored[left][key], stored[right][key])
                for left_index, left in enumerate(model_roles())
                for right in model_roles()[left_index + 1 :]
            ]
            rows.append({"array_key": key, **_distribution(correlations)})
        return rows
    finally:
        for value in stored.values():
            value.close()


def _analysis_metric_names() -> tuple[str, ...]:
    return (
        "matched_glyph_unicode_name",
        "matched_glyph_component_name",
        "matched_decomposed_form_unicode_name",
        "matched_decomposed_form_component_name",
        "lexicalization",
        "presentation_or_fusion",
        "component_tracking",
    )


def _row_metric_summary(row: Mapping[str, Any], metric: str) -> Mapping[str, Any] | None:
    if metric.startswith("matched_"):
        key = metric.removeprefix("matched_")
        value = row["matched_incorrect_label_advantage"].get(key)
    else:
        value = row["decomposition_contrasts"].get(metric)
    return value if isinstance(value, Mapping) else None


def _depth_trajectory_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lookup: dict[tuple[str, str, str, int, str], Mapping[str, Any]] = {}
    for row in rows:
        key = (
            str(row["model_role"]),
            str(row["glyph_system"]),
            str(row["carrier"]),
            int(row["distance"]),
            str(row["endpoint"]),
        )
        _require(key not in lookup, f"Duplicate T11 depth cell: {key}")
        lookup[key] = row

    output: list[dict[str, Any]] = []
    systems = [str(value) for value in _config()["analysis"]["analysis_systems"]]
    for role in model_roles():
        for system in systems:
            for carrier in ("article_a", "pipe"):
                for distance in (1, 2, 4, 8):
                    endpoint_rows = [
                        lookup.get((role, system, carrier, distance, endpoint))
                        for endpoint in DEPTH_ENDPOINT_ORDER
                    ]
                    if all(row is None for row in endpoint_rows):
                        continue
                    _require(
                        all(row is not None for row in endpoint_rows),
                        f"Incomplete T11 depth trajectory: {role}/{system}/{carrier}/{distance}",
                    )
                    for metric in _analysis_metric_names():
                        summaries = [
                            _row_metric_summary(row, metric)  # type: ignore[arg-type]
                            for row in endpoint_rows
                        ]
                        if all(value is None for value in summaries):
                            continue
                        _require(
                            all(value is not None for value in summaries),
                            f"Incomplete T11 depth metric: {role}/{system}/{carrier}/{distance}/{metric}",
                        )
                        trajectory: list[dict[str, Any]] = []
                        first_nonzero: dict[str, Any] | None = None
                        for endpoint, summary in zip(DEPTH_ENDPOINT_ORDER, summaries, strict=True):
                            assert summary is not None
                            interval = [
                                float(value)
                                for value in summary["bootstrap_percentile_95_interval"]
                            ]
                            direction = (
                                "positive"
                                if interval[0] > 0
                                else "negative"
                                if interval[1] < 0
                                else "includes_zero"
                            )
                            point = {
                                "endpoint": endpoint,
                                "median_item_margin": float(summary["median"]),
                                "bootstrap_percentile_95_interval": interval,
                                "interval_relation_to_zero": direction,
                            }
                            trajectory.append(point)
                            if first_nonzero is None and direction != "includes_zero":
                                first_nonzero = {
                                    "endpoint": endpoint,
                                    "direction": direction,
                                    "descriptive_only": True,
                                }
                        raw_value = trajectory[DEPTH_ENDPOINT_ORDER.index("raw_last_decoder_block_output")][
                            "median_item_margin"
                        ]
                        final_value = trajectory[DEPTH_ENDPOINT_ORDER.index("returned_final_hidden_state")][
                            "median_item_margin"
                        ]
                        output.append(
                            {
                                "model_role": role,
                                "glyph_system": system,
                                "carrier": carrier,
                                "distance": distance,
                                "cell_index": (0 if carrier == "article_a" else 4)
                                + (1, 2, 4, 8).index(distance),
                                "metric": metric,
                                "trajectory": trajectory,
                                "first_depth_with_interval_excluding_zero": first_nonzero,
                                "returned_final_minus_raw_last_block_median_delta": float(
                                    final_value - raw_value
                                ),
                                "decision_authorized": False,
                            }
                        )
    return output


def _balanced_three_way_variance(values: np.ndarray) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    _require(array.ndim == 3 and all(size >= 2 for size in array.shape), "T11 variance grid is not three-way")
    _require(bool(np.all(np.isfinite(array))), "T11 variance grid is non-finite")
    model_count, system_count, context_count = array.shape
    grand = float(np.mean(array))
    model_effect = np.mean(array, axis=(1, 2), keepdims=True) - grand
    system_effect = np.mean(array, axis=(0, 2), keepdims=True) - grand
    context_effect = np.mean(array, axis=(0, 1), keepdims=True) - grand
    model_system = (
        np.mean(array, axis=2, keepdims=True)
        - grand
        - model_effect
        - system_effect
    )
    model_context = (
        np.mean(array, axis=1, keepdims=True)
        - grand
        - model_effect
        - context_effect
    )
    system_context = (
        np.mean(array, axis=0, keepdims=True)
        - grand
        - system_effect
        - context_effect
    )
    three_way = (
        array
        - grand
        - model_effect
        - system_effect
        - context_effect
        - model_system
        - model_context
        - system_context
    )
    sums = {
        "model": float(system_count * context_count * np.sum(np.square(model_effect))),
        "glyph_system": float(model_count * context_count * np.sum(np.square(system_effect))),
        "context": float(model_count * system_count * np.sum(np.square(context_effect))),
        "model_by_glyph_system": float(context_count * np.sum(np.square(model_system))),
        "model_by_context": float(system_count * np.sum(np.square(model_context))),
        "glyph_system_by_context": float(model_count * np.sum(np.square(system_context))),
        "model_by_glyph_system_by_context": float(np.sum(np.square(three_way))),
    }
    degrees = {
        "model": model_count - 1,
        "glyph_system": system_count - 1,
        "context": context_count - 1,
        "model_by_glyph_system": (model_count - 1) * (system_count - 1),
        "model_by_context": (model_count - 1) * (context_count - 1),
        "glyph_system_by_context": (system_count - 1) * (context_count - 1),
        "model_by_glyph_system_by_context": (
            (model_count - 1) * (system_count - 1) * (context_count - 1)
        ),
    }
    total = float(np.sum(np.square(array - grand)))
    components = {
        name: {
            "sum_squares": value,
            "degrees_of_freedom": int(degrees[name]),
            "share_of_total_sum_squares": float(value / total) if total > 1e-30 else 0.0,
        }
        for name, value in sums.items()
    }
    return {
        "balanced_shape_model_by_system_by_context": list(array.shape),
        "grand_mean": grand,
        "total_sum_squares": total,
        "total_degrees_of_freedom": int(array.size - 1),
        "total_variance_zero": bool(total <= 1e-30),
        "components": components,
        "sum_squares_reconciliation_error": float(abs(sum(sums.values()) - total)),
        "descriptive_only": True,
    }


def _variance_decomposition(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    endpoint = "returned_final_hidden_state"
    contexts = [(carrier, distance) for carrier in ("article_a", "pipe") for distance in (1, 2, 4, 8)]
    systems = [str(value) for value in _config()["analysis"]["analysis_systems"]]
    selected = [row for row in rows if str(row["endpoint"]) == endpoint]
    lookup: dict[tuple[str, str, str, int], Mapping[str, Any]] = {}
    for row in selected:
        key = (
            str(row["model_role"]),
            str(row["glyph_system"]),
            str(row["carrier"]),
            int(row["distance"]),
        )
        _require(key not in lookup, f"Duplicate T11 broad cell: {key}")
        lookup[key] = row

    output: dict[str, Any] = {}
    for metric in _analysis_metric_names():
        system_arrays: list[np.ndarray] = []
        included_systems: list[str] = []
        for system in systems:
            values = np.empty((len(model_roles()), len(contexts)), dtype=np.float64)
            present = 0
            for role_index, role in enumerate(model_roles()):
                for context_index, (carrier, distance) in enumerate(contexts):
                    row = lookup.get((role, system, carrier, distance))
                    _require(row is not None, f"Missing T11 broad cell: {role}/{system}/{carrier}/{distance}")
                    summary = _row_metric_summary(row, metric)
                    if summary is None:
                        values[role_index, context_index] = np.nan
                    else:
                        values[role_index, context_index] = float(summary["median"])
                        present += 1
            if present == 0:
                continue
            _require(
                present == values.size and bool(np.all(np.isfinite(values))),
                f"Partially missing T11 variance metric: {system}/{metric}",
            )
            system_arrays.append(values)
            included_systems.append(system)
        _require(len(system_arrays) >= 2, f"Too few T11 systems for variance metric: {metric}")
        grid = np.stack(system_arrays, axis=1)
        output[metric] = {
            "endpoint": endpoint,
            "model_order": list(model_roles()),
            "glyph_system_order": included_systems,
            "context_order": [f"{carrier}:d{distance}" for carrier, distance in contexts],
            **_balanced_three_way_variance(grid),
        }
    return output


def analyze_joint(
    runs_root: Path,
    summaries_root: Path,
    output: Path,
) -> dict[str, Any]:
    audit_freeze()
    summary_directories = {role: summaries_root / role for role in model_roles()}
    run_directories = {role: runs_root / role for role in model_roles()}
    summary_hashes: dict[str, str] = {}
    run_hashes: dict[str, str] = {}
    broad_rows: list[dict[str, Any]] = []
    depth_rows: list[dict[str, Any]] = []
    run_arrays: dict[str, Mapping[str, Any]] = {}
    for role in model_roles():
        _require(validate_run(run_directories[role])["model_role"] == role, "T11 joint run role mismatch")
        _require(validate_summary(summary_directories[role])["model_role"] == role, "T11 joint summary role mismatch")
        run_hashes[role] = _sha256(run_directories[role] / "run_receipt.json")
        summary_hashes[role] = _sha256(summary_directories[role] / "summary_receipt.json")
        broad_rows.extend(_read_jsonl(summary_directories[role] / "broad_system_cell_metrics.jsonl"))
        depth_rows.extend(_read_jsonl(summary_directories[role] / "depth_system_cell_metrics.jsonl"))
        run_arrays[role] = _load_run_arrays(run_directories[role])
    broad_aggregate = _aggregate_summary_rows(broad_rows)
    depth_aggregate = _aggregate_summary_rows(depth_rows)
    geometry_rows = _cross_model_geometry(run_arrays, selection_items(acquired_only=True))
    margin_rows = _item_margin_agreement(summary_directories)
    trajectory_rows = _depth_trajectory_rows(depth_rows)
    variance = _variance_decomposition(broad_rows)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": "prospective_for_outcomes_exploratory_discovery_only_atlas",
        "claim_boundary": _config()["claim_boundary"],
        "model_order": list(model_roles()),
        "input_run_receipt_sha256": run_hashes,
        "input_summary_receipt_sha256": summary_hashes,
        "broad_model_system_context_summary": broad_aggregate,
        "depth_model_system_context_summary": depth_aggregate,
        "model_by_system_by_context_variance_decomposition": variance,
        "depth_trajectory_row_count": len(trajectory_rows),
        "cross_model_geometry_row_count": len(geometry_rows),
        "cross_model_item_margin_agreement_row_count": len(margin_rows),
        "landing_pattern_registry": _config()["landing_patterns"],
        "single_authoritative_landing_pattern_selected": False,
        "reserve_items": int(_config()["selection"]["expected_reserve_items"]),
        "reserve_model_forward_calls": 0,
        "reserve_outcomes_inspected": False,
        "t12_endpoint_frozen": False,
        "model_forward_calls": 0,
        "total_acquisition_model_forward_calls": int(_config()["acquisition"]["expected_total_model_forward_calls"]),
        "intervention_calls": 0,
        "generation_calls": 0,
        "t10_primary_changed": False,
        "t10_rescue_authorized": False,
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "tokenizer_independence_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "model_general_claim_authorized": False,
    }
    _require(not output.exists(), f"T11 joint analysis output exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.partial-", dir=output.parent))
    atlas._write_json(stage / "analysis.json", payload)
    _write_jsonl(stage / "broad_system_cell_metrics.jsonl", broad_rows)
    _write_jsonl(stage / "depth_system_cell_metrics.jsonl", depth_rows)
    _write_jsonl(stage / "depth_trajectories.jsonl", trajectory_rows)
    _write_jsonl(stage / "cross_model_geometry.jsonl", geometry_rows)
    _write_jsonl(stage / "cross_model_item_margin_agreement.jsonl", margin_rows)
    report = (
        "# T11 glyph-system decomposition atlas result\n\n"
        "This generated report is intentionally non-authoritative until the exploratory "
        "analysis is interpreted with its bilingual result document. T10 is unchanged, "
        "the T11 reserve remains unforwarded, and no semantic or causal claim is authorized.\n"
    )
    (stage / "report.md").write_text(report, encoding="utf-8")
    atlas._write_ledger(
        stage,
        (
            "analysis.json",
            "broad_system_cell_metrics.jsonl",
            "depth_system_cell_metrics.jsonl",
            "depth_trajectories.jsonl",
            "cross_model_geometry.jsonl",
            "cross_model_item_margin_agreement.jsonl",
            "report.md",
        ),
    )
    stage.rename(output)
    return payload


def validate_analysis(directory: Path) -> dict[str, Any]:
    names = (
        "analysis.json",
        "broad_system_cell_metrics.jsonl",
        "depth_system_cell_metrics.jsonl",
        "depth_trajectories.jsonl",
        "cross_model_geometry.jsonl",
        "cross_model_item_margin_agreement.jsonl",
        "report.md",
        "SHA256SUMS",
    )
    for name in names:
        _require((directory / name).is_file(), f"Missing T11 analysis file: {name}")
    _validate_ledger(directory, names[:-1])
    payload = atlas._read_json(directory / "analysis.json")
    _require(payload.get("protocol_id") == PROTOCOL_ID and payload.get("status") == "pass", "T11 analysis receipt mismatch")
    _require(payload.get("reserve_model_forward_calls") == 0, "T11 analysis opened reserve")
    _require(payload.get("reserve_outcomes_inspected") is False, "T11 reserve outcomes were inspected")
    _require(payload.get("t10_primary_changed") is False, "T11 changed T10")
    _require(payload.get("semantic_claim_authorized") is False, "T11 authorized semantics")
    _require(payload.get("causal_claim_authorized") is False, "T11 authorized causality")
    return {
        "status": "pass",
        "model_cells": len(payload["model_order"]),
        "reserve_untouched": True,
        "t10_primary_unchanged": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    selection = sub.add_parser("build-selection")
    selection.add_argument("--source", type=Path, required=True)
    selection.add_argument("--output", type=Path, default=_root() / SELECTION_PATH)
    sub.add_parser("audit-design")
    design = sub.add_parser("build-design-preflight")
    design.add_argument("--output", type=Path, default=_root() / DESIGN_PREFLIGHT_PATH)
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    sub.add_parser("audit-freeze")
    tokenizer = sub.add_parser("tokenizer-preflight")
    tokenizer.add_argument("--model-label", choices=model_roles(), required=True)
    tokenizer.add_argument("--model-path", type=Path)
    tokenizer.add_argument("--output", type=Path, required=True)
    preflight = sub.add_parser("preflight-all")
    preflight.add_argument("--output", type=Path, required=True)
    assemble = sub.add_parser("assemble-runtime-preflight")
    assemble.add_argument("--directory", type=Path, required=True)
    assemble.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--model-label", choices=model_roles(), required=True)
    run.add_argument("--model-path", type=Path)
    run.add_argument("--preflight-directory", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--shard-start", type=int, default=0)
    run.add_argument("--shard-stop", type=int)
    validate_one = sub.add_parser("validate-shard")
    validate_one.add_argument("--shard", type=Path, required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--model-label", choices=model_roles(), required=True)
    finalize.add_argument("--preflight-directory", type=Path, required=True)
    finalize.add_argument("--run", type=Path, required=True)
    validate_complete = sub.add_parser("validate-run")
    validate_complete.add_argument("--run", type=Path, required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("--run", type=Path, required=True)
    summary.add_argument("--preflight-directory", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    validate_derived = sub.add_parser("validate-summary")
    validate_derived.add_argument("--summary", type=Path, required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--runs-root", type=Path, required=True)
    analyze.add_argument("--summaries-root", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    validate_joint = sub.add_parser("validate-analysis")
    validate_joint.add_argument("--analysis", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "build-selection":
        result = build_selection(args.source, args.output)
    elif args.command == "audit-design":
        result = audit_design()
    elif args.command == "build-design-preflight":
        result = build_design_preflight(args.output)
    elif args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(
            args.model_label, _model_path(args.model_label, args.model_path), args.output
        )
    elif args.command == "preflight-all":
        result = preflight_all(args.output)
    elif args.command == "assemble-runtime-preflight":
        result = assemble_runtime_preflight(args.directory, args.output)
    elif args.command == "run":
        result = run_shards(
            args.model_label,
            _model_path(args.model_label, args.model_path),
            args.preflight_directory,
            args.output,
            args.shard_start,
            args.shard_stop,
        )
    elif args.command == "validate-shard":
        result = validate_shard(args.shard)
    elif args.command == "finalize":
        result = finalize_run(args.model_label, args.preflight_directory, args.run)
    elif args.command == "validate-run":
        result = validate_run(args.run)
    elif args.command == "summarize":
        result = summarize_model(args.run, args.preflight_directory, args.output)
    elif args.command == "validate-summary":
        result = validate_summary(args.summary)
    elif args.command == "analyze":
        result = analyze_joint(args.runs_root, args.summaries_root, args.output)
    elif args.command == "validate-analysis":
        result = validate_analysis(args.analysis)
    else:  # pragma: no cover
        raise T11Error(f"Unknown T11 command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
