#!/usr/bin/env python3
"""Freeze, acquire, and decide the T12 ZWJ/Regional reserve family.

T12 opens only the 96 ZWJ and 64 regional-flag items that were selected before
T11 and received zero T11 model forwards.  It stores one returned-final-state
endpoint and evaluates two prospectively frozen hypotheses.  It performs no
generation or intervention.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import tempfile
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import glyph_system_decomposition_v0 as t11  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402
import semantic_atlas_cross_model_replication_v0 as t10  # noqa: E402


PROTOCOL_ID = "glyphprobe-glyph-system-reserve-confirmation-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/glyph_system_reserve_confirmation_v0.yaml")
DESIGN_PREFLIGHT_PATH = Path(
    "validation/glyph_system_reserve_confirmation_v0/design_preflight.json"
)
FREEZE_PATH = Path("data/manifests/glyph_system_reserve_confirmation_v0.json")
VIEW_ORDER = ("glyph", "unicode_name", "component_name", "decomposed_form")
STATIC_FROZEN_ASSETS = (
    "configs/glyph_system_reserve_confirmation_v0.yaml",
    "docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md",
    "docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md",
    "scripts/glyph_system_reserve_confirmation_v0.py",
    "tests/test_glyph_system_reserve_confirmation_v0.py",
    "validation/glyph_system_reserve_confirmation_v0/design_preflight.json",
)


class T12Error(RuntimeError):
    """Raised when a frozen T12 invariant fails."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise T12Error(message)


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    _require(value.get("protocol_id") == PROTOCOL_ID, "T12 config mismatch")
    _require(tuple(value["views"]["order"]) == VIEW_ORDER, "T12 view order changed")
    _require(
        tuple(value["models"]["order"]) == tuple(t11.model_roles()),
        "T12 model roster changed",
    )
    _require(
        tuple(value["population"]["system_order"]) == ("zwj", "regional_flag"),
        "T12 system order changed",
    )
    _require(
        tuple(value["hypothesis_family"]["registered_hypothesis_order"])
        == ("H_ZWJ_FUSION", "H_REGIONAL_DUAL"),
        "T12 hypothesis order changed",
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
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
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
    _require(ledger.is_file(), f"Missing T12 ledger: {ledger}")
    observed: dict[str, str] = {}
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, name = raw.split(maxsplit=1)
        relative = Path(name.lstrip("*"))
        _require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe T12 ledger path: {relative}",
        )
        normalized = relative.as_posix()
        _require(normalized not in observed, f"Duplicate T12 ledger row: {normalized}")
        _require((directory / relative).is_file(), f"Missing T12 ledger target: {normalized}")
        _require(_sha256(directory / relative) == digest, f"T12 ledger mismatch: {normalized}")
        observed[normalized] = digest
    _require(set(observed) == set(expected_names), "T12 ledger file roster changed")
    return observed


def _audit_source_bindings() -> dict[str, str]:
    result: dict[str, str] = {}
    for name, spec in _config()["source_bindings"].items():
        path = _root() / str(spec["path"])
        _require(path.is_file(), f"Missing T12 source binding: {name}")
        observed = _sha256(path)
        _require(observed == str(spec["sha256"]), f"T12 source binding changed: {name}")
        result[str(spec["path"])] = observed
    return result


def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


def _model_spec(role: str) -> dict[str, Any]:
    _require(role in model_roles(), f"Unknown T12 model role: {role}")
    return t11._model_spec(role)


def _item_views(item: Mapping[str, Any]) -> tuple[str, ...]:
    system = str(item["glyph_system"])
    return tuple(str(value) for value in _config()["views"][system])


def confirmation_items() -> list[dict[str, Any]]:
    config = _config()
    selection_path = _root() / str(
        config["source_bindings"]["t11_selection_manifest"]["path"]
    )
    selection = atlas._read_json(selection_path)
    source_rows = [dict(row) for row in selection["items"]]
    rows: list[dict[str, Any]] = []
    for system in config["population"]["system_order"]:
        selected = [
            row
            for row in source_rows
            if row["role"] == config["population"]["source_role"]
            and row["glyph_system"] == system
        ]
        selected.sort(key=lambda row: int(row["source_index"]))
        _require(
            len(selected)
            == int(config["population"]["expected_items_by_system"][system]),
            f"T12 reserve count changed: {system}",
        )
        rows.extend(selected)
    _require(len(rows) == int(config["population"]["expected_items"]), "T12 reserve total changed")
    for index, row in enumerate(rows):
        _require(row.get("role") == "reserve_unrun", "T12 population contains a non-reserve item")
        _require(row.get("acquisition_index") is None, "T12 reserve has a T11 acquisition index")
        _require(row.get("included_in_acquisition") is False, "T12 reserve was marked acquired")
        _require(row.get("included_in_depth_subset") is False, "T12 reserve entered the T11 depth subset")
        declared = _item_views(row)
        _require(set(declared).issubset(set(row["available_views"])), "T12 view is absent from T11 item")
        row["t12_index"] = index
        row["t12_views"] = list(declared)
    return rows


def _discovery_design_audit() -> dict[str, Any]:
    config = _config()
    analysis = atlas._read_json(
        _root() / str(config["source_bindings"]["t11_analysis"]["path"])
    )
    validation = atlas._read_json(
        _root()
        / str(config["source_bindings"]["t11_independent_validation"]["path"])
    )
    basis = config["discovery_design_basis"]
    key_map = {
        "zwj_presentation_or_fusion": ("zwj", "presentation_or_fusion"),
        "regional_presentation_or_fusion": ("regional_flag", "presentation_or_fusion"),
        "regional_component_tracking": ("regional_flag", "component_tracking"),
    }
    result: dict[str, Any] = {}
    for key, (system, metric) in key_map.items():
        spec = config["hypothesis_family"]["elementary_tests"][key]
        floor = float(spec["practical_floor"])
        model_medians: list[float] = []
        for role in analysis["model_order"]:
            model_medians.append(
                float(
                    analysis["broad_model_system_context_summary"][role][system][
                        "returned_final_hidden_state"
                    ][metric]["median"]
                )
            )
        distribution = validation["returned_final_cell_distributions"][system][metric]
        expected = basis[key]
        _require(int(distribution["count"]) == int(basis["cell_count_per_contrast"]), f"T12 discovery cells changed: {key}")
        _require(abs(float(distribution["median"]) - float(expected["global_cell_median"])) < 5e-5, f"T12 discovery median changed: {key}")
        _require(round(float(distribution["positive_fraction"]) * 72) == int(expected["positive_cells"]), f"T12 positive cell count changed: {key}")
        positive_models = sum(value > 0.0 for value in model_medians)
        supporting_models = sum(value >= floor for value in model_medians)
        opposed_models = sum(value <= -floor for value in model_medians)
        _require(positive_models == int(expected["positive_model_context_medians"]), f"T12 discovery positive model count changed: {key}")
        _require(supporting_models == int(expected["models_at_or_above_t12_floor"]), f"T12 discovery support count changed: {key}")
        _require(opposed_models == int(expected["models_at_or_below_negative_t12_floor"]), f"T12 discovery opposition count changed: {key}")
        result[key] = {
            "system": system,
            "metric": metric,
            "global_cell_median": float(distribution["median"]),
            "positive_cells": int(round(float(distribution["positive_fraction"]) * 72)),
            "model_context_medians": model_medians,
            "positive_model_context_medians": positive_models,
            "models_at_or_above_t12_floor": supporting_models,
            "models_at_or_below_negative_t12_floor": opposed_models,
            "t12_practical_floor": floor,
        }
    return result


def audit_design() -> dict[str, Any]:
    config = _config()
    source_hashes = _audit_source_bindings()
    items = confirmation_items()
    present_views = sum(len(_item_views(item)) for item in items)
    forwards_per_model = present_views * len(config["input"]["carrier_order"])
    vectors_per_model = forwards_per_model * len(config["input"]["distance_order"])
    _require(present_views == int(config["acquisition"]["expected_present_item_views"]), "T12 present-view count changed")
    _require(forwards_per_model == int(config["acquisition"]["expected_model_forward_calls_per_model"]), "T12 forward count changed")
    _require(vectors_per_model == int(config["acquisition"]["expected_readout_vectors_per_model"]), "T12 vector count changed")
    _require(forwards_per_model * len(model_roles()) == int(config["acquisition"]["expected_total_model_forward_calls"]), "T12 total forward count changed")
    _require(vectors_per_model * len(model_roles()) == int(config["acquisition"]["expected_total_readout_vectors"]), "T12 total vector count changed")
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "reserve_items": len(items),
        "reserve_items_by_system": dict(Counter(str(item["glyph_system"]) for item in items)),
        "present_item_views": present_views,
        "model_cells": len(model_roles()),
        "contexts_per_model": 8,
        "model_forward_calls_per_model": forwards_per_model,
        "expected_total_model_forward_calls": forwards_per_model * len(model_roles()),
        "readout_vectors_per_model": vectors_per_model,
        "expected_total_readout_vectors": vectors_per_model * len(model_roles()),
        "source_bindings": source_hashes,
        "discovery_design_basis": _discovery_design_audit(),
        "reserve_model_forward_calls": 0,
        "model_weights_loaded": False,
        "scientific_result_available": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }


def build_design_preflight(output: Path) -> dict[str, Any]:
    design = audit_design()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "design_preflight_complete_zero_t12_reserve_model_forwards",
        "design": design,
        "config_sha256": _sha256(_root() / CONFIG_PATH),
        "reserve_model_forward_calls": 0,
        "model_weights_loaded": False,
        "scientific_result_available": False,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    _write_json_once(output, payload)
    return {"status": "pass", "output": output.as_posix(), "sha256": _sha256(output)}


def build_freeze(output: Path) -> dict[str, Any]:
    design_path = _root() / DESIGN_PREFLIGHT_PATH
    _require(design_path.is_file(), "T12 design preflight is missing")
    design = atlas._read_json(design_path)
    _require(
        design.get("status")
        == "design_preflight_complete_zero_t12_reserve_model_forwards",
        "T12 design preflight is incomplete",
    )
    _require(design.get("reserve_model_forward_calls") == 0, "T12 design preflight opened reserve")
    assets: dict[str, str] = {}
    for relative in STATIC_FROZEN_ASSETS:
        path = _root() / relative
        _require(path.is_file(), f"Missing T12 frozen asset: {relative}")
        assets[relative] = _sha256(path)
    config = _config()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t12_reserve_model_forward",
        "experiment_role": config["experiment_role"],
        "question": config["question"],
        "claim_boundary": config["claim_boundary"],
        "frozen_assets": assets,
        "source_bindings": _audit_source_bindings(),
        "design_preflight_sha256": _sha256(design_path),
        "model_order": list(model_roles()),
        "reserve_items": int(config["population"]["expected_items"]),
        "reserve_model_forward_calls_at_freeze": 0,
        "hypothesis_family": config["hypothesis_family"],
        "endpoint": config["endpoint"],
        "scientific_result_available_at_freeze": False,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "t10_primary_changed": False,
        "t10_rescue_authorized": False,
    }
    _write_json_once(output, payload)
    return {
        "status": "pass",
        "manifest_sha256": _sha256(output),
        "frozen_asset_count": len(assets),
        "reserve_model_forward_calls_at_freeze": 0,
    }


def audit_freeze() -> dict[str, Any]:
    path = _root() / FREEZE_PATH
    _require(path.is_file(), "T12 freeze manifest is missing")
    manifest = atlas._read_json(path)
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "T12 freeze protocol mismatch")
    _require(
        manifest.get("status")
        == "freeze_complete_before_any_t12_reserve_model_forward",
        "T12 freeze is incomplete",
    )
    _require(manifest.get("reserve_model_forward_calls_at_freeze") == 0, "T12 freeze records a reserve forward")
    for relative, expected in manifest["frozen_assets"].items():
        asset = _root() / relative
        _require(asset.is_file(), f"T12 frozen asset missing: {relative}")
        _require(_sha256(asset) == expected, f"T12 frozen asset changed: {relative}")
    _require(_sha256(_root() / DESIGN_PREFLIGHT_PATH) == manifest["design_preflight_sha256"], "T12 design preflight changed")
    _require(_audit_source_bindings() == manifest["source_bindings"], "T12 source bindings changed")
    return {
        "status": "pass",
        "manifest_sha256": _sha256(path),
        "frozen_asset_count": len(manifest["frozen_assets"]),
    }


def _control_mapping(
    rows: Sequence[Mapping[str, Any]],
    token_ids: Mapping[int, Sequence[int]],
    *,
    role: str,
    target_view: str,
    strict_prefix: bool,
) -> dict[str, Any]:
    config = _config()
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    row_by_index = {int(row["t12_index"]): row for row in rows}
    for row in rows:
        index = int(row["t12_index"])
        ids = [int(value) for value in token_ids[index]]
        key: tuple[Any, ...] = (str(row["glyph_system"]), len(ids))
        if strict_prefix:
            key += (ids[0],)
        groups[key].append(index)
    mapping: dict[int, int] = {}
    strata: list[dict[str, Any]] = []
    namespace = str(config["tokenization_controls"]["mapping_namespace"])
    for key, indices in sorted(groups.items(), key=lambda value: tuple(str(part) for part in value[0])):
        ordered = sorted(
            indices,
            key=lambda index: _hash_text(
                f"{namespace}:{role}:{target_view}:{int(strict_prefix)}:{row_by_index[index]['codepoint']}"
            ),
        )
        if len(ordered) >= 2:
            for position, index in enumerate(ordered):
                mapping[index] = ordered[(position + 1) % len(ordered)]
        strata.append({"key": list(key), "item_indices": ordered, "count": len(ordered)})
    _require(all(index != target for index, target in mapping.items()), "T12 matched control contains a self-match")
    return {
        "strict_prefix": strict_prefix,
        "eligible_item_count": len(mapping),
        "total_item_count": len(rows),
        "coverage": float(len(mapping) / max(1, len(rows))),
        "mapping": [
            {"t12_index": index, "wrong_target_t12_index": mapping[index]}
            for index in sorted(mapping)
        ],
        "strata": strata,
    }


def _sequence_hash(rows: Sequence[Sequence[int]]) -> str:
    return atlas._sequence_sha256(rows)


def _tokenize_panel(tokenizer: Any, role: str) -> dict[str, Any]:
    config = _config()
    items = confirmation_items()
    raw_ids: dict[str, dict[int, list[int]]] = {view: {} for view in VIEW_ORDER}
    combined_ids: dict[str, dict[str, dict[int, list[int]]]] = {
        view: {str(carrier): {} for carrier in config["input"]["carrier_order"]}
        for view in VIEW_ORDER
    }
    item_rows: list[dict[str, Any]] = []
    for item in items:
        index = int(item["t12_index"])
        views: dict[str, Any] = {}
        for view in _item_views(item):
            ids = [
                int(value)
                for value in tokenizer.encode(
                    t11._view_text(item, view), add_special_tokens=False
                )
            ]
            _require(bool(ids), f"Empty T12 tokenization: {item['codepoint']}/{view}")
            raw_ids[view][index] = ids
            views[view] = {
                "token_ids": ids,
                "token_count": len(ids),
                "first_token_id": ids[0],
            }
        item_rows.append(
            {
                "t12_index": index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_system": str(item["glyph_system"]),
                "views": views,
            }
        )
    for system in config["population"]["system_order"]:
        system_items = [item for item in items if item["glyph_system"] == system]
        for view in _item_views(system_items[0]):
            sequences = [tuple(raw_ids[view][int(item["t12_index"])]) for item in system_items]
            _require(len(sequences) == len(set(sequences)), f"Tokenizer collapsed T12 view: {role}/{system}/{view}")

    carrier_rows: dict[str, Any] = {}
    maximum_tokens = 0
    for carrier in config["input"]["carrier_order"]:
        carrier = str(carrier)
        spec = config["input"]["carriers"][carrier]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        unit_ids = [int(value) for value in tokenizer.encode(unit, add_special_tokens=False)]
        _require(len(unit_ids) == 1, f"T12 carrier is not one token: {role}/{carrier}")
        exact = 0
        decoded = 0
        cases = 0
        for item in items:
            index = int(item["t12_index"])
            for view in _item_views(item):
                text = t11._view_text(item, view) + unit * repeats
                ids = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
                expected = raw_ids[view][index] + unit_ids * repeats
                _require(ids == expected, f"T12 carrier boundary changed: {role}/{item['codepoint']}/{view}/{carrier}")
                combined_ids[view][carrier][index] = ids
                exact += int(ids[:-repeats] == raw_ids[view][index])
                decoded += int(
                    tokenizer.decode(
                        ids,
                        clean_up_tokenization_spaces=False,
                        skip_special_tokens=False,
                    )
                    == text
                )
                maximum_tokens = max(maximum_tokens, len(ids))
                cases += 1
        _require(exact == cases, f"T12 carrier prefix failure: {role}/{carrier}")
        _require(decoded == cases, f"T12 carrier decode failure: {role}/{carrier}")
        carrier_rows[carrier] = {
            "unit": unit,
            "repeats": repeats,
            "token_id": unit_ids[0],
            "case_count": cases,
            "prefix_exact_count": exact,
            "decode_exact_count": decoded,
        }

    controls: dict[str, Any] = {}
    required_minimum = float(config["tokenization_controls"]["required_minimum_coverage"])
    strict_minimum = float(config["tokenization_controls"]["strict_prefix_minimum_coverage"])
    for target_view in config["tokenization_controls"]["matched_incorrect_label_targets"]:
        target_view = str(target_view)
        controls[target_view] = {}
        for system in config["population"]["system_order"]:
            rows = [
                item
                for item in items
                if item["glyph_system"] == system and target_view in _item_views(item)
            ]
            if not rows:
                continue
            lookup = {
                int(item["t12_index"]): raw_ids[target_view][int(item["t12_index"])]
                for item in rows
            }
            required = _control_mapping(
                rows,
                lookup,
                role=role,
                target_view=target_view,
                strict_prefix=False,
            )
            strict = _control_mapping(
                rows,
                lookup,
                role=role,
                target_view=target_view,
                strict_prefix=True,
            )
            _require(required["coverage"] >= required_minimum, f"T12 required coverage failed: {role}/{system}/{target_view}")
            _require(strict["coverage"] >= strict_minimum, f"T12 strict-prefix coverage failed: {role}/{system}/{target_view}")
            controls[target_view][system] = {
                "required": required,
                "strict_prefix_sensitivity": strict,
                "required_minimum_coverage": required_minimum,
                "strict_prefix_minimum_coverage": strict_minimum,
            }

    raw_hashes = {
        view: _sequence_hash([raw_ids[view][index] for index in sorted(raw_ids[view])])
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
            "present_item_views": sum(len(_item_views(item)) for item in items),
            "view_order": list(VIEW_ORDER),
            "item_tokenization": item_rows,
            "ordered_sequence_sha256": {"raw": raw_hashes, "combined": combined_hashes},
            "carriers": carrier_rows,
            "maximum_combined_token_count": maximum_tokens,
            "matched_incorrect_label_controls": controls,
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
    return t11._locate_local_snapshot(role)


def _model_path(role: str, supplied: Path | None) -> Path:
    return supplied if supplied is not None else _locate_local_snapshot(role)


def tokenizer_preflight(role: str, model_path: Path, output: Path) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoConfig, AutoTokenizer

    freeze = audit_freeze()
    spec = _model_spec(role)
    snapshot = model_path.resolve()
    _require(snapshot.is_dir(), f"T12 model snapshot missing: {snapshot}")
    _require(snapshot.name == str(spec["revision"]), f"T12 revision mismatch: {role}")
    completeness = t10._validate_weight_artifact_completeness(snapshot)
    artifact = model_artifact_receipt(snapshot)
    t11_freeze = atlas._read_json(
        _root()
        / str(_config()["source_bindings"]["t11_freeze_manifest"]["path"])
    )
    pinned = t11_freeze["t10_model_artifacts"][role]
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == pinned[key], f"T12 reused artifact changed: {role}/{key}")
    architecture = AutoConfig.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    _require(str(architecture.model_type) == str(spec["expected_model_type"]), "T12 model type mismatch")
    _require(int(architecture.num_hidden_layers) == int(spec["expected_num_layers"]), "T12 layer count mismatch")
    _require(int(architecture.hidden_size) == int(spec["expected_model_dim"]), "T12 model width mismatch")
    _require(int(architecture.vocab_size) == int(spec["expected_vocab_size"]), "T12 vocabulary mismatch")
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    tokenization = _tokenize_panel(tokenizer, role)["receipt"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_and_static_artifact_preflight_pass_zero_t12_reserve_model_forwards",
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "selection_manifest_sha256": _sha256(
            _root()
            / str(_config()["source_bindings"]["t11_selection_manifest"]["path"])
        ),
        "architecture": {
            "model_type": str(architecture.model_type),
            "architectures": [str(value) for value in getattr(architecture, "architectures", [])],
            "num_hidden_layers": int(architecture.num_hidden_layers),
            "hidden_size": int(architecture.hidden_size),
            "vocab_size": int(architecture.vocab_size),
        },
        "tokenizer": {"class": type(tokenizer).__name__, **tokenization},
        "model_artifact": artifact,
        "weight_artifact_completeness": completeness,
        "runtime_versions_observed": _runtime_versions(),
        "model_weights_loaded": False,
        "reserve_model_forward_calls": 0,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    _write_json_once(output, payload)
    return {
        "status": "pass",
        "model_role": role,
        "output": output.as_posix(),
        "sha256": _sha256(output),
        "maximum_combined_token_count": tokenization["maximum_combined_token_count"],
    }


def _validate_tokenizer_receipt(path: Path, role: str) -> dict[str, Any]:
    value = atlas._read_json(path)
    _require(value.get("protocol_id") == PROTOCOL_ID, f"T12 tokenizer receipt protocol mismatch: {role}")
    _require(value.get("model_role") == role, f"T12 tokenizer receipt role mismatch: {role}")
    _require(
        value.get("status")
        == "tokenizer_and_static_artifact_preflight_pass_zero_t12_reserve_model_forwards",
        f"T12 tokenizer receipt failed: {role}",
    )
    _require(value.get("model_weights_loaded") is False, "T12 tokenizer preflight loaded weights")
    _require(value.get("reserve_model_forward_calls") == 0, "T12 tokenizer preflight opened reserve")
    _require(value.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T12 tokenizer freeze mismatch")
    return value


def assemble_runtime_preflight(directory: Path, output: Path) -> dict[str, Any]:
    _require(
        output.name == "aggregate.json" and output.parent.resolve() == directory.resolve(),
        "T12 aggregate must be <directory>/aggregate.json",
    )
    freeze = audit_freeze()
    receipts: dict[str, str] = {}
    artifacts: dict[str, Any] = {}
    coverage: dict[str, Any] = {}
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(path.is_file(), f"Missing T12 tokenizer receipt: {role}")
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
        "status": "all_nine_tokenizer_preflights_complete_zero_t12_reserve_model_forwards",
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "model_order": list(model_roles()),
        "tokenizer_receipt_sha256": receipts,
        "model_artifacts": artifacts,
        "matched_control_coverage": coverage,
        "model_weights_loaded": False,
        "reserve_model_forward_calls": 0,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    _write_json_once(output, payload)
    names = [f"{role}.json" for role in model_roles()] + ["aggregate.json"]
    (directory / "SHA256SUMS").write_text(
        "".join(f"{_sha256(directory / name)}  {name}\n" for name in names),
        encoding="utf-8",
    )
    return {"status": "pass", "output": output.as_posix(), "sha256": _sha256(output)}


def preflight_all(output: Path) -> dict[str, Any]:
    audit_freeze()
    _require(not output.exists(), f"T12 preflight output exists: {output}")
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
        "reserve_model_forward_calls": 0,
    }


def _validate_runtime_preflight(directory: Path) -> dict[str, Any]:
    names = [f"{role}.json" for role in model_roles()] + ["aggregate.json"]
    _validate_ledger(directory, names)
    aggregate = atlas._read_json(directory / "aggregate.json")
    _require(
        aggregate.get("status")
        == "all_nine_tokenizer_preflights_complete_zero_t12_reserve_model_forwards",
        "T12 aggregate preflight failed",
    )
    _require(tuple(aggregate["model_order"]) == model_roles(), "T12 aggregate model order changed")
    _require(aggregate.get("reserve_model_forward_calls") == 0, "T12 preflight opened reserve")
    for role in model_roles():
        path = directory / f"{role}.json"
        _require(_sha256(path) == aggregate["tokenizer_receipt_sha256"][role], "T12 aggregate receipt changed")
        _validate_tokenizer_receipt(path, role)
    return aggregate


def _load_model(
    role: str,
    model_path: Path,
    preflight_directory: Path,
) -> tuple[Any, Any, Any, dict[str, Any], dict[str, Any]]:
    import torch
    import transformers
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoModelForCausalLM, AutoTokenizer

    aggregate = _validate_runtime_preflight(preflight_directory)
    t11._validate_runtime()
    spec = _model_spec(role)
    receipt_path = preflight_directory / f"{role}.json"
    receipt = _validate_tokenizer_receipt(receipt_path, role)
    artifact = model_artifact_receipt(model_path)
    for key in ("manifest_sha256", "file_count", "total_bytes"):
        _require(artifact[key] == aggregate["model_artifacts"][role][key], f"T12 runtime artifact changed: {role}/{key}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    roster = _tokenize_panel(tokenizer, role)
    _require(roster["receipt"]["ordered_sequence_sha256"] == receipt["tokenizer"]["ordered_sequence_sha256"], "T12 runtime token sequences changed")
    _require(roster["receipt"]["matched_incorrect_label_controls"] == receipt["tokenizer"]["matched_incorrect_label_controls"], "T12 runtime controls changed")
    dtype_key = "dtype" if int(transformers.__version__.split(".", 1)[0]) >= 5 else "torch_dtype"
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=False,
        **{dtype_key: torch.bfloat16},
    )
    model.to("cuda")
    model.eval()
    _require(type(model).__name__ == str(spec["expected_model_class"]), "T12 loaded model class mismatch")
    _require(int(model.config.num_hidden_layers) == int(spec["expected_num_layers"]), "T12 loaded layer count mismatch")
    count = sum(int(parameter.numel()) for parameter in model.parameters())
    _require(count == int(spec["expected_parameter_count"]), "T12 parameter count mismatch")
    dtypes = Counter(str(parameter.dtype) for parameter in model.parameters())
    _require(set(dtypes) == {"torch.bfloat16"}, "T12 parameter dtype mismatch")
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
    return torch, tokenizer, model, model_receipt, roster


def _records(roster: Mapping[str, Any]) -> list[dict[str, Any]]:
    config = _config()
    rows: list[dict[str, Any]] = []
    for item in confirmation_items():
        index = int(item["t12_index"])
        for view_index, view in enumerate(VIEW_ORDER):
            if view not in _item_views(item):
                continue
            raw_ids = [int(value) for value in roster["raw_ids"][view][index]]
            for carrier_index, carrier in enumerate(config["input"]["carrier_order"]):
                carrier = str(carrier)
                rows.append(
                    {
                        "t12_index": index,
                        "view_index": view_index,
                        "view": view,
                        "carrier_index": carrier_index,
                        "carrier": carrier,
                        "raw_ids": raw_ids,
                        "input_ids": [
                            int(value)
                            for value in roster["combined_ids"][view][carrier][index]
                        ],
                    }
                )
    return rows


def _run_one_shard(
    *,
    role: str,
    torch: Any,
    tokenizer: Any,
    model: Any,
    model_receipt: Mapping[str, Any],
    roster: Mapping[str, Any],
    run_root: Path,
    shard_index: int,
    preflight_directory: Path,
) -> dict[str, Any]:
    del tokenizer
    config = _config()
    freeze = audit_freeze()
    population = confirmation_items()
    shard_size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(population), start + shard_size)
    _require(start < stop, f"T12 shard index out of range: {shard_index}")
    items = population[start:stop]
    stage, final = atlas._atomic_shard_directory(run_root, shard_index)
    intent = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "reserve_forward_may_begin_after_this_record",
        "model_role": role,
        "shard_index": shard_index,
        "t12_index_start": start,
        "t12_index_stop_exclusive": stop,
        "item_codepoints": [str(item["codepoint"]) for item in items],
        "source_role": "reserve_unrun",
        "retry_policy": config["acquisition"]["incomplete_stage_policy"],
    }
    atlas._write_json(stage / "execution_intent.json", intent)
    width = int(_model_spec(role)["expected_model_dim"])
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    activations = np.full(
        (len(items), len(VIEW_ORDER), len(carriers), len(distances), width),
        np.nan,
        dtype=np.float32,
    )
    view_mask = np.zeros((len(items), len(VIEW_ORDER)), dtype=np.bool_)
    for local, item in enumerate(items):
        for view in _item_views(item):
            view_mask[local, VIEW_ORDER.index(view)] = True
    records = [
        row
        for row in _records(roster)
        if start <= int(row["t12_index"]) < stop
    ]
    observations: list[dict[str, Any]] = []
    forward_calls = 0
    readout_vectors = 0
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for row in records:
        global_index = int(row["t12_index"])
        local_index = global_index - start
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
        elapsed_ms = (time.perf_counter() - before) * 1000.0
        _require(
            len(output.hidden_states) == int(_model_spec(role)["expected_num_layers"]) + 1,
            "T12 hidden-state roster mismatch",
        )
        returned = output.hidden_states[-1]
        position_tensor = torch.tensor(positions, dtype=torch.long, device="cuda")
        captured = returned[0, position_tensor].float().cpu().numpy()
        _require(captured.shape == (len(distances), width), "T12 captured shape mismatch")
        _require(bool(np.isfinite(captured).all()), "T12 captured activation is nonfinite")
        activations[
            local_index,
            int(row["view_index"]),
            int(row["carrier_index"]),
        ] = captured
        item = items[local_index]
        observations.append(
            {
                "t12_index": global_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "glyph_system": str(item["glyph_system"]),
                "source_role": str(item["role"]),
                "view": str(row["view"]),
                "view_index": int(row["view_index"]),
                "carrier": str(row["carrier"]),
                "carrier_index": int(row["carrier_index"]),
                "raw_token_ids": [int(value) for value in row["raw_ids"]],
                "input_token_ids": ids,
                "readout_positions": positions,
                "activation_rms_by_distance": np.sqrt(
                    np.mean(np.square(captured, dtype=np.float64), axis=-1)
                ).tolist(),
                "forward_latency_ms": elapsed_ms,
            }
        )
        forward_calls += 1
        readout_vectors += len(distances)
        del output, returned, captured, input_ids, attention_mask, position_tensor
    _require(bool(np.isfinite(activations[view_mask]).all()), "T12 present values are nonfinite")
    _require(bool(np.isnan(activations[~view_mask]).all()), "T12 absent values are not NaN")
    np.save(stage / "activations.npy", activations, allow_pickle=False)
    np.save(stage / "view_mask.npy", view_mask, allow_pickle=False)
    _write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "shard_index": shard_index,
        "t12_index_start": start,
        "t12_index_stop_exclusive": stop,
        "item_count": len(items),
        "item_codepoints": [str(item["codepoint"]) for item in items],
        "system_counts": dict(Counter(str(item["glyph_system"]) for item in items)),
        "activation_shape": list(activations.shape),
        "activation_dtype": "float32",
        "axis_order": config["acquisition"]["axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": carriers,
        "distance_order": distances,
        "endpoint": config["endpoint"],
        "unique_input_sequences": len(records),
        "model_forward_calls": forward_calls,
        "reserve_items_forwarded": len(items),
        "reserve_model_forward_calls": forward_calls,
        "readout_vectors": readout_vectors,
        "fused_distance_readout": True,
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
                "activations.npy",
                "view_mask.npy",
                "observations.jsonl",
            )
        },
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_decision_authorized": False,
    }
    atlas._write_json(stage / "shard_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        (
            "execution_intent.json",
            "activations.npy",
            "view_mask.npy",
            "observations.jsonl",
            "shard_receipt.json",
        ),
    )
    stage.rename(final)
    return receipt


def validate_shard(directory: Path) -> dict[str, Any]:
    config = _config()
    expected_names = (
        "execution_intent.json",
        "activations.npy",
        "view_mask.npy",
        "observations.jsonl",
        "shard_receipt.json",
    )
    _validate_ledger(directory, expected_names)
    receipt = atlas._read_json(directory / "shard_receipt.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T12 shard receipt mismatch")
    _require(receipt.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T12 shard freeze mismatch")
    for name, expected in receipt["outputs"].items():
        _require(_sha256(directory / name) == expected, f"T12 shard output mismatch: {name}")
    index = int(receipt["shard_index"])
    shard_size = int(config["acquisition"]["item_shard_size"])
    items = confirmation_items()[index * shard_size : (index + 1) * shard_size]
    _require(receipt["item_codepoints"] == [str(item["codepoint"]) for item in items], "T12 shard population changed")
    role = str(receipt["model_role"])
    expected_shape = (
        len(items),
        len(VIEW_ORDER),
        2,
        4,
        int(_model_spec(role)["expected_model_dim"]),
    )
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    mask = np.load(directory / "view_mask.npy", mmap_mode="r", allow_pickle=False)
    expected_mask = np.asarray(
        [[view in _item_views(item) for view in VIEW_ORDER] for item in items],
        dtype=np.bool_,
    )
    _require(tuple(array.shape) == expected_shape, "T12 shard shape changed")
    _require(str(array.dtype) == "float32", "T12 shard dtype changed")
    _require(np.array_equal(mask, expected_mask), "T12 shard view mask changed")
    _require(bool(np.isfinite(np.asarray(array[mask])).all()), "T12 shard has nonfinite present values")
    _require(bool(np.isnan(np.asarray(array[~mask])).all()), "T12 shard has non-NaN absent values")
    expected_forwards = sum(len(_item_views(item)) for item in items) * 2
    _require(int(receipt["model_forward_calls"]) == expected_forwards, "T12 shard forward count changed")
    _require(int(receipt["reserve_model_forward_calls"]) == expected_forwards, "T12 reserve forward count changed")
    _require(int(receipt["readout_vectors"]) == expected_forwards * 4, "T12 shard vector count changed")
    return {
        "status": "pass",
        "model_role": role,
        "shard_index": index,
        "item_count": len(items),
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
    _require(0 <= shard_start < stop <= expected, "Invalid T12 shard range")
    run_root.mkdir(parents=True, exist_ok=True)
    _require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete T12 shard requires manual adjudication")
    _require(not (run_root / "run_receipt.json").exists(), "T12 run is already finalized")
    lock = run_root / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise T12Error("T12 run root already has a writer") from exc
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
            return {"status": status, "message": "requested T12 shards already complete", "events": []}
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before T12 model load: {foreign}")
        torch, tokenizer, model, model_receipt, roster = _load_model(
            role, model_path, preflight_directory
        )
        for index in pending:
            foreign = atlas._foreign_gpu_pids()
            if foreign:
                raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before T12 shard {index}: {foreign}")
            receipt = _run_one_shard(
                role=role,
                torch=torch,
                tokenizer=tokenizer,
                model=model,
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
                        "readout_vectors",
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
    _require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete T12 shard blocks finalization")
    _require(not (run_root / "run_receipt.json").exists(), "T12 run is already finalized")
    receipts: list[dict[str, Any]] = []
    ledgers: dict[str, str] = {}
    for index in range(int(config["acquisition"]["expected_shards_per_model"])):
        directory = run_root / f"shard_{index:04d}"
        result = validate_shard(directory)
        _require(result["model_role"] == role, "T12 run contains another model role")
        receipts.append(atlas._read_json(directory / "shard_receipt.json"))
        ledgers[directory.name] = _sha256(directory / "SHA256SUMS")
    item_count = sum(int(row["item_count"]) for row in receipts)
    forwards = sum(int(row["model_forward_calls"]) for row in receipts)
    vectors = sum(int(row["readout_vectors"]) for row in receipts)
    _require(item_count == int(config["population"]["expected_items"]), "T12 finalized item count changed")
    _require(forwards == int(config["acquisition"]["expected_model_forward_calls_per_model"]), "T12 finalized forward count changed")
    _require(vectors == int(config["acquisition"]["expected_readout_vectors_per_model"]), "T12 finalized vector count changed")
    model_receipts = {json.dumps(row["model"], sort_keys=True) for row in receipts}
    _require(len(model_receipts) == 1, "T12 model receipt changed across shards")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "runtime_preflight_aggregate_sha256": _sha256(preflight_directory / "aggregate.json"),
        "tokenizer_receipt_sha256": aggregate["tokenizer_receipt_sha256"][role],
        "reserve_item_count": item_count,
        "reserve_items_forwarded": item_count,
        "reserve_model_forward_calls": forwards,
        "unique_input_sequences": forwards,
        "model_forward_calls": forwards,
        "readout_vectors": vectors,
        "shard_count": len(receipts),
        "shard_ledger_sha256": ledgers,
        "activation_dtype": "float32",
        "axis_order": config["acquisition"]["axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": config["input"]["distance_order"],
        "endpoint": config["endpoint"],
        "model": receipts[0]["model"],
        "peak_cuda_memory_bytes": max(int(row["peak_cuda_memory_bytes"]) for row in receipts),
        "elapsed_ms": sum(float(row["elapsed_ms"]) for row in receipts),
        "acquisition_status": "complete_joint_analysis_pending",
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
    _validate_ledger(directory, ("run_receipt.json", "SHARD_INDEX.json"))
    receipt = atlas._read_json(directory / "run_receipt.json")
    shard_index = atlas._read_json(directory / "SHARD_INDEX.json")
    role = str(receipt["model_role"])
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T12 run receipt mismatch")
    _require(receipt.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T12 run freeze mismatch")
    totals = {"items": 0, "forwards": 0, "vectors": 0}
    for index in range(int(_config()["acquisition"]["expected_shards_per_model"])):
        name = f"shard_{index:04d}"
        result = validate_shard(directory / name)
        _require(result["model_role"] == role, "T12 run role changed")
        row = atlas._read_json(directory / name / "shard_receipt.json")
        totals["items"] += int(row["item_count"])
        totals["forwards"] += int(row["model_forward_calls"])
        totals["vectors"] += int(row["readout_vectors"])
        _require(shard_index["shards"][name] == _sha256(directory / name / "SHA256SUMS"), "T12 shard ledger binding changed")
    _require(int(receipt["reserve_item_count"]) == totals["items"], "T12 run item total changed")
    _require(int(receipt["model_forward_calls"]) == totals["forwards"], "T12 run forward total changed")
    _require(int(receipt["readout_vectors"]) == totals["vectors"], "T12 run vector total changed")
    return {"status": "pass", "model_role": role, "receipt": receipt}


def _load_run_arrays(run_root: Path) -> tuple[np.ndarray, np.ndarray]:
    arrays: list[np.ndarray] = []
    masks: list[np.ndarray] = []
    for index in range(int(_config()["acquisition"]["expected_shards_per_model"])):
        directory = run_root / f"shard_{index:04d}"
        arrays.append(np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False))
        masks.append(np.load(directory / "view_mask.npy", mmap_mode="r", allow_pickle=False))
    return np.concatenate(arrays, axis=0), np.concatenate(masks, axis=0)


def _center_normalize(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64)
    result = result - np.mean(result, axis=-1, keepdims=True)
    denominator = np.linalg.norm(result, axis=-1, keepdims=True)
    _require(bool(np.all(denominator > 1e-12)), "T12 activation norm collapsed")
    return result / denominator


def _mapping_dict(control: Mapping[str, Any]) -> dict[int, int]:
    result = {
        int(row["t12_index"]): int(row["wrong_target_t12_index"])
        for row in control["mapping"]
    }
    _require(all(index != target for index, target in result.items()), "T12 analysis control self-match")
    return result


def _elementary_contrast(
    activations: np.ndarray,
    preflight_receipt: Mapping[str, Any],
    elementary_name: str,
    control_name: str,
) -> tuple[np.ndarray, list[int]]:
    config = _config()
    spec = config["hypothesis_family"]["elementary_tests"][elementary_name]
    system = str(spec["system"])
    items = confirmation_items()
    global_indices = [
        int(item["t12_index"]) for item in items if item["glyph_system"] == system
    ]
    local_by_global = {global_index: local for local, global_index in enumerate(global_indices)}
    positive_view = VIEW_ORDER.index(str(spec["query_positive"]))
    negative_view = VIEW_ORDER.index(str(spec["query_negative"]))
    target_view_name = str(spec["target"])
    target_view = VIEW_ORDER.index(target_view_name)
    positive = _center_normalize(activations[global_indices, positive_view])
    negative = _center_normalize(activations[global_indices, negative_view])
    target = _center_normalize(activations[global_indices, target_view])
    controls = preflight_receipt["tokenizer"]["matched_incorrect_label_controls"]
    control = controls[target_view_name][system][control_name]
    mapping = _mapping_dict(control)
    result = np.full((2, 4, len(global_indices)), np.nan, dtype=np.float64)
    for global_index, wrong_global_index in mapping.items():
        _require(global_index in local_by_global and wrong_global_index in local_by_global, "T12 control crossed systems")
        local = local_by_global[global_index]
        wrong_local = local_by_global[wrong_global_index]
        positive_correct = np.sum(positive[local] * target[local], axis=-1)
        positive_wrong = np.sum(positive[local] * target[wrong_local], axis=-1)
        negative_correct = np.sum(negative[local] * target[local], axis=-1)
        negative_wrong = np.sum(negative[local] * target[wrong_local], axis=-1)
        result[:, :, local] = (
            (positive_correct - positive_wrong)
            - (negative_correct - negative_wrong)
        )
    expected_coverage = float(control["coverage"])
    observed_coverage = float(np.sum(np.isfinite(result[0, 0])) / len(global_indices))
    _require(abs(observed_coverage - expected_coverage) <= 1e-12, "T12 analysis coverage changed")
    return result, global_indices


def _descriptive_summary(values: np.ndarray) -> dict[str, Any]:
    _require(values.ndim == 3, "T12 contrast tensor rank changed")
    _require(values.shape[:2] == (len(model_roles()), 8), "T12 contrast cell grid changed")
    cell_medians = np.nanmedian(values, axis=2)
    _require(bool(np.isfinite(cell_medians).all()), "T12 cell median is nonfinite")
    model_medians = np.median(cell_medians, axis=1)
    return {
        "global_statistic": float(np.median(cell_medians)),
        "cell_medians": cell_medians.tolist(),
        "model_context_medians": model_medians.tolist(),
        "positive_cell_count": int(np.sum(cell_medians > 0.0)),
        "positive_model_count": int(np.sum(model_medians > 0.0)),
        "minimum_cell_median": float(np.min(cell_medians)),
        "maximum_cell_median": float(np.max(cell_medians)),
    }


def shared_item_swap_randomization_test(
    values: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    summary = _descriptive_summary(values)
    observed = float(summary["global_statistic"])
    rng = np.random.default_rng(seed)
    null_statistics = np.empty(draws, dtype=np.float64)
    exceedances = 0
    written = 0
    chunk_size = 256
    while written < draws:
        count = min(chunk_size, draws - written)
        signs = (
            rng.integers(0, 2, size=(count, values.shape[2]), dtype=np.int8) * 2 - 1
        ).astype(np.float64)
        signed = values[None, :, :, :] * signs[:, None, None, :]
        cell_medians = np.nanmedian(signed, axis=3)
        statistics = np.median(cell_medians, axis=(1, 2))
        null_statistics[written : written + count] = statistics
        exceedances += int(np.sum(statistics >= observed))
        written += count
    p_value = float((1 + exceedances) / (draws + 1))
    return {
        **summary,
        "randomization_draws": draws,
        "randomization_seed": seed,
        "exceedances": exceedances,
        "p_value": p_value,
        "null_statistic_quantiles": {
            str(quantile): float(np.quantile(null_statistics, quantile))
            for quantile in (0.0, 0.5, 0.95, 0.975, 0.99, 1.0)
        },
        "randomization_null": "shared_within_item_swap_of_glyph_and_decomposed_query_forms",
    }


def _elementary_gate(
    primary: Mapping[str, Any],
    strict: Mapping[str, Any],
    *,
    practical_floor: float,
) -> dict[str, Any]:
    gates = _config()["hypothesis_family"]
    heterogeneity = gates["heterogeneity_gate"]
    strict_spec = gates["strict_prefix_gate"]
    model_medians = np.asarray(primary["model_context_medians"], dtype=np.float64)
    strict_model_medians = np.asarray(strict["model_context_medians"], dtype=np.float64)
    supporting = int(np.sum(model_medians >= practical_floor))
    opposed = int(np.sum(model_medians <= -practical_floor))
    strict_supporting = int(np.sum(strict_model_medians > 0.0))
    checks = {
        "global_practical_floor": bool(float(primary["global_statistic"]) >= practical_floor),
        "minimum_supporting_models": bool(
            supporting
            >= int(heterogeneity["minimum_models_at_or_above_practical_floor"])
        ),
        "maximum_materially_opposed_models": bool(
            opposed
            <= int(heterogeneity["maximum_models_at_or_below_negative_practical_floor"])
        ),
        "strict_prefix_global_positive": bool(float(strict["global_statistic"]) > 0.0),
        "strict_prefix_minimum_positive_models": bool(
            strict_supporting
            >= int(strict_spec["minimum_models_with_positive_context_median"])
        ),
    }
    return {
        "all_nonmultiplicity_gates_pass": bool(all(checks.values())),
        "checks": checks,
        "practical_floor": practical_floor,
        "supporting_model_count": supporting,
        "materially_opposed_model_count": opposed,
        "strict_prefix_positive_model_count": strict_supporting,
    }


def holm_correction(
    p_values: Mapping[str, float],
    *,
    alpha: float,
    hypothesis_order: Sequence[str],
) -> dict[str, Any]:
    _require(set(p_values) == set(hypothesis_order), "T12 Holm family changed")
    position = {name: index for index, name in enumerate(hypothesis_order)}
    ordered = sorted(p_values, key=lambda name: (float(p_values[name]), position[name]))
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    rejected: dict[str, bool] = {name: False for name in ordered}
    still_rejecting = True
    rows: list[dict[str, Any]] = []
    for rank, name in enumerate(ordered):
        multiplier = count - rank
        running = max(running, min(1.0, multiplier * float(p_values[name])))
        adjusted[name] = running
        threshold = alpha / multiplier
        reject = bool(still_rejecting and float(p_values[name]) <= threshold)
        rejected[name] = reject
        if not reject:
            still_rejecting = False
        rows.append(
            {
                "rank": rank + 1,
                "hypothesis": name,
                "raw_p_value": float(p_values[name]),
                "holm_threshold": threshold,
                "holm_adjusted_p_value": running,
                "rejected": reject,
            }
        )
    return {
        "method": "holm",
        "familywise_alpha": alpha,
        "family_size": count,
        "ordered_tests": rows,
        "adjusted_p_values": adjusted,
        "rejected": rejected,
    }


def analyze_joint(
    runs_root: Path,
    preflight_directory: Path,
    output: Path,
) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    _validate_runtime_preflight(preflight_directory)
    _require(not output.exists(), f"T12 analysis output exists: {output}")
    elementary_specs = config["hypothesis_family"]["elementary_tests"]
    system_sizes = {
        system: int(config["population"]["expected_items_by_system"][system])
        for system in config["population"]["system_order"]
    }
    tensors: dict[str, dict[str, np.ndarray]] = {
        control: {
            name: np.full(
                (len(model_roles()), 8, system_sizes[str(spec["system"])]),
                np.nan,
                dtype=np.float64,
            )
            for name, spec in elementary_specs.items()
        }
        for control in ("required", "strict_prefix_sensitivity")
    }
    context_order = [
        {"carrier": carrier, "distance": int(distance)}
        for carrier in config["input"]["carrier_order"]
        for distance in config["input"]["distance_order"]
    ]
    cell_rows: list[dict[str, Any]] = []
    run_receipt_hashes: dict[str, str] = {}
    total_forwards = 0
    for model_index, role in enumerate(model_roles()):
        run_root = runs_root / role
        validated = validate_run(run_root)
        run_receipt = validated["receipt"]
        run_receipt_hashes[role] = _sha256(run_root / "run_receipt.json")
        total_forwards += int(run_receipt["model_forward_calls"])
        activations, view_mask = _load_run_arrays(run_root)
        expected_mask = np.asarray(
            [[view in _item_views(item) for view in VIEW_ORDER] for item in confirmation_items()],
            dtype=np.bool_,
        )
        _require(np.array_equal(view_mask, expected_mask), f"T12 analysis mask changed: {role}")
        preflight_receipt = _validate_tokenizer_receipt(
            preflight_directory / f"{role}.json", role
        )
        for elementary_name in elementary_specs:
            for control_name in tensors:
                values, global_indices = _elementary_contrast(
                    activations,
                    preflight_receipt,
                    elementary_name,
                    control_name,
                )
                tensors[control_name][elementary_name][model_index] = values.reshape(
                    8, len(global_indices)
                )
                for context_index, context in enumerate(context_order):
                    vector = values.reshape(8, len(global_indices))[context_index]
                    eligible = np.flatnonzero(np.isfinite(vector))
                    cell_rows.append(
                        {
                            "model_role": role,
                            "model_index": model_index,
                            "elementary_test": elementary_name,
                            "system": str(elementary_specs[elementary_name]["system"]),
                            "control": control_name,
                            "context_index": context_index,
                            **context,
                            "eligible_item_count": int(len(eligible)),
                            "eligible_t12_indices": [global_indices[int(index)] for index in eligible],
                            "item_contrasts": [float(vector[int(index)]) for index in eligible],
                            "cell_median": float(np.median(vector[eligible])),
                        }
                    )
        del activations, view_mask

    _require(total_forwards == int(config["acquisition"]["expected_total_model_forward_calls"]), "T12 analysis forward total changed")
    elementary_results: dict[str, Any] = {}
    for elementary_name, spec in elementary_specs.items():
        primary = shared_item_swap_randomization_test(
            tensors["required"][elementary_name],
            draws=int(config["hypothesis_family"]["randomization_draws"]),
            seed=int(spec["randomization_seed"]),
        )
        strict = _descriptive_summary(tensors["strict_prefix_sensitivity"][elementary_name])
        gate = _elementary_gate(
            primary,
            strict,
            practical_floor=float(spec["practical_floor"]),
        )
        elementary_results[elementary_name] = {
            "specification": spec,
            "required_control": primary,
            "strict_prefix_sensitivity": strict,
            "gate": gate,
        }

    hypothesis_p_values = {
        "H_ZWJ_FUSION": float(
            elementary_results["zwj_presentation_or_fusion"]["required_control"]["p_value"]
        ),
        "H_REGIONAL_DUAL": max(
            float(
                elementary_results["regional_presentation_or_fusion"]["required_control"]["p_value"]
            ),
            float(
                elementary_results["regional_component_tracking"]["required_control"]["p_value"]
            ),
        ),
    }
    hypothesis_order = [
        str(value)
        for value in config["hypothesis_family"]["registered_hypothesis_order"]
    ]
    holm = holm_correction(
        hypothesis_p_values,
        alpha=float(config["hypothesis_family"]["familywise_alpha"]),
        hypothesis_order=hypothesis_order,
    )
    hypothesis_results: dict[str, Any] = {}
    for hypothesis in hypothesis_order:
        components = [
            str(value)
            for value in config["hypothesis_family"]["registered_hypotheses"][hypothesis][
                "required_elementary_tests"
            ]
        ]
        component_gates = {
            name: bool(
                elementary_results[name]["gate"]["all_nonmultiplicity_gates_pass"]
            )
            for name in components
        }
        confirmed = bool(holm["rejected"][hypothesis] and all(component_gates.values()))
        hypothesis_results[hypothesis] = {
            "required_elementary_tests": components,
            "elementary_gate_pass": component_gates,
            "intersection_union": hypothesis == "H_REGIONAL_DUAL",
            "raw_hypothesis_p_value": hypothesis_p_values[hypothesis],
            "holm_adjusted_p_value": holm["adjusted_p_values"][hypothesis],
            "holm_rejected": holm["rejected"][hypothesis],
            "confirmed": confirmed,
        }
    confirmed = [name for name in hypothesis_order if hypothesis_results[name]["confirmed"]]
    if len(confirmed) == 2:
        outcome_pattern = "both_zwj_fusion_and_regional_dual_confirmed"
    elif confirmed == ["H_ZWJ_FUSION"]:
        outcome_pattern = "zwj_fusion_only_confirmed"
    elif confirmed == ["H_REGIONAL_DUAL"]:
        outcome_pattern = "regional_dual_only_confirmed"
    else:
        outcome_pattern = "neither_registered_hypothesis_confirmed"
    primary_result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": config["analysis"]["analysis_role"],
        "outcome_pattern": outcome_pattern,
        "reserve_question_closed": True,
        "hypothesis_family": {
            "name": config["hypothesis_family"]["family_name"],
            "registered_hypothesis_order": hypothesis_order,
            "regional_combination": config["hypothesis_family"]["regional_combination"],
            "familywise_alpha": float(config["hypothesis_family"]["familywise_alpha"]),
        },
        "context_order": context_order,
        "model_order": list(model_roles()),
        "elementary_results": elementary_results,
        "hypothesis_results": hypothesis_results,
        "holm": holm,
        "confirmed_hypotheses": confirmed,
        "claim_boundary": config["claim_boundary"],
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "behavioral_steering_claim_authorized": False,
        "tokenizer_independence_claim_authorized": False,
        "model_general_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "t10_primary_changed": False,
        "t10_rescue_authorized": False,
    }
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    stage.mkdir(parents=True)
    _write_jsonl(stage / "cell_item_contrasts.jsonl", cell_rows)
    atlas._write_json(stage / "primary_result.json", primary_result)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": config["analysis"]["analysis_role"],
        "outcome_pattern": outcome_pattern,
        "reserve_question_closed": True,
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "runtime_preflight_aggregate_sha256": _sha256(preflight_directory / "aggregate.json"),
        "input_run_receipt_sha256": run_receipt_hashes,
        "reserve_items": int(config["population"]["expected_items"]),
        "acquisition_model_forward_calls": total_forwards,
        "analysis_model_forward_calls": 0,
        "cell_item_contrast_rows": len(cell_rows),
        "primary_result_sha256": _sha256(stage / "primary_result.json"),
        "confirmed_hypotheses": confirmed,
        "intervention_calls": 0,
        "generation_calls": 0,
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "behavioral_steering_claim_authorized": False,
        "model_general_claim_authorized": False,
    }
    atlas._write_json(stage / "analysis_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        ("cell_item_contrasts.jsonl", "primary_result.json", "analysis_receipt.json"),
    )
    stage.rename(output)
    return receipt


def validate_analysis(directory: Path) -> dict[str, Any]:
    _validate_ledger(
        directory,
        ("cell_item_contrasts.jsonl", "primary_result.json", "analysis_receipt.json"),
    )
    receipt = atlas._read_json(directory / "analysis_receipt.json")
    primary = atlas._read_json(directory / "primary_result.json")
    _require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "T12 analysis receipt mismatch")
    _require(primary.get("protocol_id") == PROTOCOL_ID and primary.get("status") == "pass", "T12 primary result mismatch")
    _require(receipt.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "T12 analysis freeze mismatch")
    _require(receipt.get("primary_result_sha256") == _sha256(directory / "primary_result.json"), "T12 primary result hash changed")
    _require(primary.get("reserve_question_closed") is True, "T12 reserve question is not closed")
    _require(set(primary["hypothesis_results"]) == {"H_ZWJ_FUSION", "H_REGIONAL_DUAL"}, "T12 hypothesis result roster changed")
    observed_p = {
        name: float(row["raw_hypothesis_p_value"])
        for name, row in primary["hypothesis_results"].items()
    }
    recomputed = holm_correction(
        observed_p,
        alpha=float(_config()["hypothesis_family"]["familywise_alpha"]),
        hypothesis_order=_config()["hypothesis_family"]["registered_hypothesis_order"],
    )
    _require(recomputed == primary["holm"], "T12 stored Holm result changed")
    _require(receipt.get("semantic_claim_authorized") is False, "T12 authorized a semantic claim")
    _require(receipt.get("causal_claim_authorized") is False, "T12 authorized a causal claim")
    _require(receipt.get("behavioral_steering_claim_authorized") is False, "T12 authorized behavioral steering")
    _require(receipt.get("model_general_claim_authorized") is False, "T12 authorized model generality")
    rows = [
        json.loads(line)
        for line in (directory / "cell_item_contrasts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _require(len(rows) == int(receipt["cell_item_contrast_rows"]), "T12 analysis row count changed")
    _require(len(rows) == 3 * 2 * 9 * 8, "T12 analysis cell family changed")
    return {
        "status": "pass",
        "outcome_pattern": primary["outcome_pattern"],
        "confirmed_hypotheses": primary["confirmed_hypotheses"],
        "cell_item_contrast_rows": len(rows),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
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
    analyze = sub.add_parser("analyze")
    analyze.add_argument("--runs-root", type=Path, required=True)
    analyze.add_argument("--preflight-directory", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    validate_joint = sub.add_parser("validate-analysis")
    validate_joint.add_argument("--analysis", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "build-design-preflight":
        result = build_design_preflight(args.output)
    elif args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(
            args.model_label,
            _model_path(args.model_label, args.model_path),
            args.output,
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
        result = finalize_run(
            args.model_label, args.preflight_directory, args.run
        )
    elif args.command == "validate-run":
        result = validate_run(args.run)
    elif args.command == "analyze":
        result = analyze_joint(
            args.runs_root, args.preflight_directory, args.output
        )
    elif args.command == "validate-analysis":
        result = validate_analysis(args.analysis)
    else:  # pragma: no cover
        raise T12Error(f"Unknown T12 command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
