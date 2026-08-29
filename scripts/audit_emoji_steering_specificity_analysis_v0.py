#!/usr/bin/env python3
"""Freeze and audit the outcome-blind T13-EA analysis boundary.

The inventory command deliberately never parses response-ledger rows or loads
activation/logit values.  During the T13-EH queue it may inspect only sealed
paths, receipts, byte counts, NPY headers, and optionally content-blind hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import yaml


ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
SCHEMA_VERSION = 1
CONFIG_PATH = Path("configs/emoji_steering_specificity_analysis_v0.yaml")
ACQUISITION_CONFIG_PATH = Path("configs/emoji_steering_specificity_harvest_v0.yaml")
ACQUISITION_FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_harvest_v0.json"
)
FREEZE_PATH = Path("data/manifests/emoji_steering_specificity_analysis_v0.json")
RUNTIME_PREFLIGHT_DIRECTORY = Path("validation/emoji_steering_specificity_harvest_v0")
RUNTIME_PREFLIGHT_AGGREGATE_PATH = RUNTIME_PREFLIGHT_DIRECTORY / "aggregate.json"
RUNTIME_PREFLIGHT_ROLE_PATHS = tuple(
    RUNTIME_PREFLIGHT_DIRECTORY / f"{role}.json"
    for role in (
        "qwen25_0p5b_base_bf16",
        "llama32_3b_base_bf16",
        "qwen25_7b_base_bf16",
        "olmo2_1b_base_bf16",
        "qwen25_1p5b_base_bf16",
        "smollm2_1p7b_base_bf16",
        "gemma2_2b_it_bf16",
        "qwen25_3b_base_bf16",
        "mistral7b_instruct_v03_bf16",
    )
)
FROZEN_INPUTS = (
    CONFIG_PATH,
    ACQUISITION_CONFIG_PATH,
    ACQUISITION_FREEZE_PATH,
    Path("configs/semantic_atlas_cross_model_replication_v0.yaml"),
    Path("data/manifests/glyph_system_decomposition_selection_v0.json"),
    Path("data/manifests/semantic_atlas_cross_model_replication_v0.json"),
    Path("data/targets/prestage_targets.jsonl"),
    Path("data/wrappers/source_wrappers.jsonl"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md"),
    Path("scripts/emoji_steering_specificity_harvest_v0.py"),
    Path("scripts/run_emoji_steering_specificity_harvest_v0_queue.sh"),
    Path("scripts/audit_emoji_steering_specificity_analysis_v0.py"),
    Path("scripts/analyze_emoji_steering_specificity_outcomes_v0.py"),
    Path("scripts/analyze_emoji_steering_specificity_geometry_v0.py"),
    Path("tests/test_emoji_steering_specificity_analysis_v0.py"),
    Path("tests/test_emoji_steering_specificity_harvest_v0.py"),
    Path("tests/test_analyze_emoji_steering_specificity_outcomes_v0.py"),
    Path("tests/test_analyze_emoji_steering_specificity_geometry_v0.py"),
    RUNTIME_PREFLIGHT_AGGREGATE_PATH,
    RUNTIME_PREFLIGHT_DIRECTORY / "design_preflight.json",
    *RUNTIME_PREFLIGHT_ROLE_PATHS,
)

SOURCE_OBSERVATION_ROWS = (
    280,
    320,
    320,
    312,
    320,
    320,
    272,
    256,
    304,
    304,
    320,
    320,
)
ITEM_RESPONSE_ROWS = (
    2752,
    3072,
    3072,
    3008,
    3072,
    3072,
    2688,
    2560,
    2944,
    2944,
    3072,
    3072,
)
PROTOTYPE_RESPONSE_ROWS = {
    "atomic_anchor": 4608,
    "presentation": 7680,
    "modifier": 7680,
    "zwj": 7680,
    "regional_flag": 7680,
    "keycap": 7680,
}


class AnalysisBoundaryError(RuntimeError):
    """Raised when the T13-EA outcome-blind boundary is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisBoundaryError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected YAML object: {path}")
    return value


def _read_jsonl_metadata(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            _require(
                isinstance(value, dict),
                f"Expected JSON object: {path}:{line_number}",
            )
            rows.append(value)
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_lines_sha256(lines: Iterable[str]) -> str:
    payload = "".join(f"{line}\n" for line in lines).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = path.parent / f".{path.name}.stage-{uuid.uuid4().hex}"
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _config() -> dict[str, Any]:
    value = _read_yaml(_root() / CONFIG_PATH)
    _require(value.get("analysis_id") == ANALYSIS_ID, "T13-EA analysis ID changed")
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EA source protocol changed",
    )
    return value


def _acquisition_config() -> dict[str, Any]:
    value = _read_yaml(_root() / ACQUISITION_CONFIG_PATH)
    _require(
        value.get("protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EA acquisition binding changed",
    )
    return value


def audit_design() -> dict[str, Any]:
    config = _config()
    acquisition = _acquisition_config()
    gate = config["acquisition_gate"]
    integrity = config["integrity_gate"]
    roles = [str(value) for value in gate["required_role_order"]]
    pilots = [str(value) for value in gate["pilot_roles"]]
    _require(
        roles == [str(value) for value in acquisition["models"]["order"]],
        "T13-EA role order differs from acquisition",
    )
    _require(
        pilots == [str(value) for value in acquisition["pilot"]["roles"]],
        "T13-EA pilot roles differ from acquisition",
    )
    _require(
        bool(gate["scientific_open_requires_all_roles_complete"]),
        "T13-EA must require the full queue",
    )
    _require(
        "response_ledger_metric_parsing" in gate["forbidden_during_queue"],
        "T13-EA queue blind must forbid ledger metric parsing",
    )
    _require(
        int(integrity["expected_source_shards_per_role"])
        == int(acquisition["source_bank"]["expected_shards_per_model"])
        == 12,
        "T13-EA source shard count changed",
    )
    _require(
        int(integrity["expected_response_rows_per_pilot_role"])
        == int(acquisition["pilot"]["expected_response_rows_per_model"])
        == 127_744,
        "T13-EA pilot row count changed",
    )
    _require(
        int(integrity["required_generation_calls"]) == 0,
        "T13-EA generation guard changed",
    )
    _require(
        integrity.get("exact_production_tree_schema_required") is True,
        "T13-EA exact production artifact schema gate changed",
    )
    _require(
        integrity.get("external_closeout_root_required") is True,
        "T13-EA verified closeout location gate changed",
    )
    _require(
        integrity.get("zero_hook_value_gate_runs_before_nonzero_outcome_rows") is True,
        "T13-EA zero-hook first-open gate changed",
    )
    _require(
        config["reporting"]["no_confirmatory_verdict"] is True,
        "T13-EA cannot authorize confirmation",
    )
    _require(
        config["future_confirmation"]["t13eh_observations_in_confirmatory_statistic"]
        == "forbidden",
        "T13-EA observations cannot enter T13-C",
    )
    family_ids = [str(row["id"]) for row in config["scientific_output_families"]]
    _require(
        family_ids
        == [
            "F1_item_source_form",
            "F2_prototype_depth_dose",
            "F3_random_null_calibration",
            "F4_target_sensitivity",
            "F5_output_direction",
            "F6_source_geometry",
        ],
        "T13-EA output family order changed",
    )
    return {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "design_audit_pass",
        "required_roles": roles,
        "pilot_roles": pilots,
        "scientific_output_family_ids": family_ids,
        "scientific_outcomes_read": False,
    }


def freeze(output: Path = FREEZE_PATH) -> dict[str, Any]:
    design = audit_design()
    bindings: dict[str, dict[str, Any]] = {}
    for relative in FROZEN_INPUTS:
        path = _root() / relative
        _require(path.is_file(), f"T13-EA frozen input missing: {relative}")
        bindings[str(relative)] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    manifest = {
        **design,
        "status": "freeze_complete_before_t13eh_scientific_outcome_inspection",
        "inputs": bindings,
        "queue_time_allowed_inspection": (
            "sealed paths, count fields, declared bytes, NPY headers, and optional "
            "content-blind SHA-256 only"
        ),
        "scientific_open_gate": "all_nine_roles_complete_and_independent_hash_pass",
        "claim_boundary": _config()["claim_boundary"],
    }
    _write_json(_root() / output, manifest)
    return manifest


def audit_freeze() -> dict[str, Any]:
    audit_design()
    manifest = _read_json(_root() / FREEZE_PATH)
    _require(
        manifest.get("analysis_id") == ANALYSIS_ID,
        "T13-EA freeze analysis ID changed",
    )
    _require(
        manifest.get("status")
        == "freeze_complete_before_t13eh_scientific_outcome_inspection",
        "T13-EA freeze status changed",
    )
    inputs = manifest.get("inputs")
    _require(isinstance(inputs, dict), "T13-EA frozen input bindings missing")
    _require(
        set(inputs) == {str(path) for path in FROZEN_INPUTS},
        "T13-EA frozen input roster changed",
    )
    for relative, binding in inputs.items():
        path = _root() / relative
        _require(path.is_file(), f"T13-EA frozen input missing: {relative}")
        _require(
            path.stat().st_size == int(binding["bytes"]),
            f"T13-EA size changed: {relative}",
        )
        _require(_sha256(path) == binding["sha256"], f"T13-EA hash changed: {relative}")
    return {"status": "freeze_audit_pass", "analysis_id": ANALYSIS_ID}


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _strict_int(value: Any, expected: int, message: str) -> None:
    _require(type(value) is int and value == expected, message)


def _nonnegative_number(value: Any, message: str) -> None:
    _require(
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) >= 0.0,
        message,
    )


def _exact_keys(
    value: Mapping[str, Any], expected: Iterable[str], message: str
) -> None:
    _require(set(value) == set(expected), message)


def _artifact_expectations() -> dict[str, Any]:
    """Return the frozen, outcome-independent T13-EH artifact schema."""

    analysis = _config()
    acquisition = _acquisition_config()
    binding = acquisition["source_bindings"]["t10_model_config"]
    model_path = _root() / str(binding["path"])
    _require(model_path.is_file(), "T13-EH frozen model config is missing")
    _require(
        _sha256(model_path) == str(binding["sha256"]),
        "T13-EH frozen model config hash changed",
    )
    model_config = _read_yaml(model_path)
    model_rows = model_config["models"]
    roles = tuple(
        str(value) for value in analysis["acquisition_gate"]["required_role_order"]
    )
    pilots = frozenset(
        str(value) for value in analysis["acquisition_gate"]["pilot_roles"]
    )
    model_specs: dict[str, dict[str, Any]] = {}
    for role in roles:
        row = model_rows[role]
        model_specs[role] = {
            "width": int(row["expected_model_dim"]),
            "vocab": int(row["expected_vocab_size"]),
            "layers": int(row["expected_num_layers"]),
            "artifact_model_id": str(row["artifact_model_id"]),
            "revision": str(row["revision"]),
            "model_class": str(row["expected_model_class"]),
            "parameter_count": int(row["expected_parameter_count"]),
            "batch_size": int(acquisition["models"]["batch_size"][role]),
        }
    systems = tuple(str(value) for value in acquisition["population"]["system_order"])
    prototype_rows = {
        system: int(PROTOTYPE_RESPONSE_ROWS[system]) for system in systems
    }
    pilot_response_rows = (
        sum(ITEM_RESPONSE_ROWS) + sum(prototype_rows.values()) + 8 * 6144 + 256
    )
    _require(
        pilot_response_rows
        == int(acquisition["pilot"]["expected_response_rows_per_model"])
        == int(analysis["integrity_gate"]["expected_response_rows_per_pilot_role"]),
        "T13-EH response-shard row partition changed",
    )
    return {
        "roles": roles,
        "pilots": pilots,
        "model_specs": model_specs,
        "systems": systems,
        "source_observation_rows": SOURCE_OBSERVATION_ROWS,
        "item_response_rows": ITEM_RESPONSE_ROWS,
        "prototype_response_rows": prototype_rows,
        "random_response_rows": 6144,
        "zero_response_rows": 256,
        "pilot_response_rows": pilot_response_rows,
        "source_shard_items": 16,
        "population_items": 192,
        "present_item_views": sum(SOURCE_OBSERVATION_ROWS) // 4,
        "source_forward_sequences": 36 + sum(SOURCE_OBSERVATION_ROWS),
        "top_k": int(
            acquisition["pilot"]["response_storage"][
                "top_positive_and_negative_logit_deltas"
            ]
        ),
        "sketch_dimension": int(
            acquisition["pilot"]["response_storage"]["countsketch_dimension"]
        ),
    }


def _npy(dtype: str, shape: tuple[int, ...]) -> dict[str, Any]:
    return {"format": "npy", "dtype": dtype, "shape": shape}


def _jsonl(rows: int) -> dict[str, Any]:
    return {"format": "jsonl", "rows": rows}


def _json() -> dict[str, Any]:
    return {"format": "json"}


def _response_files(rows: int, schema: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    top_k = int(schema["top_k"])
    sketch_dimension = int(schema["sketch_dimension"])
    return {
        "response_ledger.jsonl": _jsonl(rows),
        "top_positive_ids.npy": _npy("int32", (rows, top_k)),
        "top_positive_values.npy": _npy("float32", (rows, top_k)),
        "top_negative_ids.npy": _npy("int32", (rows, top_k)),
        "top_negative_values.npy": _npy("float32", (rows, top_k)),
        "countsketch.npy": _npy("float32", (rows, sketch_dimension)),
    }


def _receipt_specs(
    role: str, pilot: bool, schema: Mapping[str, Any]
) -> list[dict[str, Any]]:
    model = schema["model_specs"][role]
    width = int(model["width"])
    vocab = int(model["vocab"])
    batch_size = int(model["batch_size"])
    specs: list[dict[str, Any]] = [
        {
            "relative_directory": Path("baseline"),
            "kind": "baseline",
            "status": "baseline_complete",
            "files": {
                "wrapper_activations.npy": _npy("float32", (4, 8, width)),
                "target_activations.npy": _npy("float32", (32, 8, width)),
                "target_logits.npy": _npy("float32", (32, vocab)),
                "metadata.json": _json(),
            },
            "exact": {
                "unique_forward_sequences": 36,
                "batched_model_invocations": 33,
                "intervention_sequences": 0,
                "generation_calls": 0,
            },
        }
    ]
    source_rows = tuple(int(value) for value in schema["source_observation_rows"])
    shard_items = int(schema["source_shard_items"])
    for shard_index, observation_rows in enumerate(source_rows):
        present_views = observation_rows // 4
        specs.append(
            {
                "relative_directory": Path("source") / f"shard-{shard_index:04d}",
                "kind": "source",
                "status": "source_shard_complete",
                "files": {
                    "wrapper_deltas.npy": _npy(
                        "float32", (shard_items, 5, 4, 8, width)
                    ),
                    "directions.npy": _npy("float32", (shard_items, 5, 8, width)),
                    "view_mask.npy": _npy("bool", (shard_items, 5)),
                    "observations.jsonl": _jsonl(observation_rows),
                },
                "exact": {
                    "shard_index": shard_index,
                    "item_start": shard_index * shard_items,
                    "item_stop_exclusive": (shard_index + 1) * shard_items,
                    "present_item_views": present_views,
                    "unique_forward_sequences": observation_rows,
                    "batched_model_invocations": math.ceil(
                        observation_rows / batch_size
                    ),
                    "wrapper_delta_vectors": present_views * 4 * 8,
                    "mean_direction_vectors": present_views * 8,
                    "intervention_sequences": 0,
                    "generation_calls": 0,
                },
            }
        )
    if not pilot:
        return specs

    response_specs: list[tuple[Path, str, str, int, int]] = []
    zero_rows = int(schema["zero_response_rows"])
    response_specs.append(
        (Path("pilot/zero/all-sites"), "pilot_zero", "zero", zero_rows, zero_rows)
    )
    for shard_index, rows in enumerate(schema["item_response_rows"]):
        rows = int(rows)
        per_target = rows // 32
        invocations = 32 * math.ceil(per_target / batch_size)
        response_specs.append(
            (
                Path("pilot/item") / f"shard-{shard_index:04d}",
                "pilot_item",
                "item",
                rows,
                invocations,
            )
        )
    for system in schema["systems"]:
        rows = int(schema["prototype_response_rows"][system])
        conditions_per_group = rows // (8 * 32)
        invocations = 8 * 32 * math.ceil(conditions_per_group / batch_size)
        response_specs.append(
            (
                Path("pilot/prototype") / str(system),
                "pilot_prototype",
                "prototype",
                rows,
                invocations,
            )
        )
    random_rows = int(schema["random_response_rows"])
    for site_index in range(8):
        invocations = 32 * math.ceil((random_rows // 32) / batch_size)
        response_specs.append(
            (
                Path("pilot/random") / f"site-{site_index:02d}",
                "pilot_random",
                "random",
                random_rows,
                invocations,
            )
        )
    for relative, kind, shard_kind, rows, invocations in response_specs:
        specs.append(
            {
                "relative_directory": relative,
                "kind": kind,
                "status": "response_shard_complete",
                "files": _response_files(rows, schema),
                "exact": {
                    "shard_kind": shard_kind,
                    "shard_name": relative.name,
                    "response_rows": rows,
                    "intervention_sequences": rows,
                    "baseline_guard_sequences": invocations,
                    "batched_model_invocations": invocations,
                    "generation_calls": 0,
                },
            }
        )
    return specs


def _validate_baseline_metadata(
    path: Path, *, role: str, schema: Mapping[str, Any]
) -> None:
    value = _read_json(path)
    _exact_keys(
        value,
        (
            "wrapper_ids",
            "wrapper_token_counts",
            "target_ids",
            "target_groups",
            "target_token_counts",
            "block_indices",
            "depth_fractions",
        ),
        f"Baseline metadata fields changed: {path}",
    )
    acquisition = _acquisition_config()
    target_binding = acquisition["source_bindings"]["public_targets"]
    target_path = _root() / str(target_binding["path"])
    _require(
        target_path.is_file() and _sha256(target_path) == str(target_binding["sha256"]),
        "Frozen public-target binding changed",
    )
    target_rows = _read_jsonl_metadata(target_path)
    _require(
        len(target_rows) == int(target_binding["expected_rows"]),
        "Frozen public-target row count changed",
    )
    wrapper_binding = acquisition["source_bindings"]["source_wrappers"]
    wrapper_path = _root() / str(wrapper_binding["path"])
    _require(
        wrapper_path.is_file()
        and _sha256(wrapper_path) == str(wrapper_binding["sha256"]),
        "Frozen source-wrapper binding changed",
    )
    wrapper_rows = _read_jsonl_metadata(wrapper_path)
    _require(
        len(wrapper_rows) == int(wrapper_binding["expected_rows"]),
        "Frozen source-wrapper row count changed",
    )
    by_wrapper_id = {str(row["id"]): row for row in wrapper_rows}
    wrapper_ids = [str(item) for item in wrapper_binding["selected_ids"]]
    _require(
        all(item in by_wrapper_id for item in wrapper_ids),
        "Frozen selected source wrapper is missing",
    )
    preflight_path = RUNTIME_PREFLIGHT_DIRECTORY / f"{role}.json"
    preflight = _read_json(_root() / preflight_path)
    aggregate = _read_json(_root() / RUNTIME_PREFLIGHT_AGGREGATE_PATH)
    _require(
        aggregate.get("receipt_sha256", {}).get(role)
        == _sha256(_root() / preflight_path),
        f"Runtime preflight role binding changed: {role}",
    )
    preflight_targets = preflight.get("target_rows")
    _require(
        isinstance(preflight_targets, list) and len(preflight_targets) == 32,
        f"Runtime preflight target rows changed: {role}",
    )
    expected_target_ids = [str(row["id"]) for row in target_rows]
    expected_target_groups = [str(row["group"]) for row in target_rows]
    _require(
        [str(row.get("id")) for row in preflight_targets] == expected_target_ids
        and [str(row.get("group")) for row in preflight_targets]
        == expected_target_groups,
        f"Runtime preflight target identity changed: {role}",
    )
    expected_target_counts = [int(row["token_count"]) for row in preflight_targets]
    layers = int(schema["model_specs"][role]["layers"])
    depth_fractions = [
        float(item) for item in acquisition["depth"]["normalized_fractions"]
    ]
    block_indices = [
        max(0, int(math.floor(fraction * layers)) - 1) for fraction in depth_fractions
    ]
    _require(
        value["wrapper_ids"] == wrapper_ids,
        f"Baseline wrapper identity changed: {path}",
    )
    _require(
        isinstance(value["wrapper_token_counts"], list)
        and len(value["wrapper_token_counts"]) == 4
        and all(
            type(item) is int and item > 0 for item in value["wrapper_token_counts"]
        ),
        f"Baseline wrapper token counts changed: {path}",
    )
    _require(
        value["target_ids"] == expected_target_ids
        and value["target_groups"] == expected_target_groups
        and value["target_token_counts"] == expected_target_counts,
        f"Baseline target metadata changed: {path}",
    )
    _require(
        value["block_indices"] == block_indices
        and value["depth_fractions"] == depth_fractions,
        f"Baseline depth metadata changed: {path}",
    )


def _validate_file_header(
    path: Path,
    spec: Mapping[str, Any],
    *,
    role: str,
    schema: Mapping[str, Any],
) -> tuple[str | None, int | None]:
    if spec["format"] == "npy":
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        observed_dtype = str(array.dtype)
        observed_shape = tuple(int(value) for value in array.shape)
        del array
        _require(
            observed_dtype == str(spec["dtype"]),
            f"NPY dtype changed: {path} ({observed_dtype})",
        )
        _require(
            observed_shape == tuple(spec["shape"]),
            f"NPY shape changed: {path} ({observed_shape})",
        )
        return f"{observed_dtype}:{list(observed_shape)}", None
    if spec["format"] == "jsonl":
        observed_rows = _line_count(path)
        _require(
            observed_rows == int(spec["rows"]),
            f"JSONL row count changed: {path} ({observed_rows})",
        )
        return None, observed_rows
    _require(spec["format"] == "json", f"Unknown artifact format: {path}")
    _validate_baseline_metadata(path, role=role, schema=schema)
    return None, None


def _audit_receipt(
    path: Path,
    *,
    role: str,
    spec: Mapping[str, Any],
    schema: Mapping[str, Any],
    verify_hashes: bool,
) -> dict[str, Any]:
    receipt = _read_json(path)
    expected_exact = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": SOURCE_PROTOCOL_ID,
        "status": spec["status"],
        "model_role": role,
        **spec["exact"],
    }
    _exact_keys(
        receipt,
        (*expected_exact, "elapsed_seconds", "files"),
        f"Receipt fields changed: {path}",
    )
    for key, expected in expected_exact.items():
        if type(expected) is int:
            _strict_int(
                receipt.get(key), expected, f"Receipt field changed: {path}/{key}"
            )
        else:
            _require(
                receipt.get(key) == expected, f"Receipt field changed: {path}/{key}"
            )
    _nonnegative_number(
        receipt["elapsed_seconds"], f"Receipt elapsed time invalid: {path}"
    )
    _require(
        path.parent.resolve(strict=True).is_relative_to(
            path.parents[1].resolve(strict=True)
        ),
        f"Receipt escaped its role directory: {path}",
    )
    files = receipt.get("files")
    expected_files = spec["files"]
    _require(isinstance(files, dict), f"Missing file bindings: {path}")
    _require(set(files) == set(expected_files), f"Bound filenames changed: {path}")
    actual_names = {candidate.name for candidate in path.parent.iterdir()}
    _require(
        actual_names == {"receipt.json", *expected_files},
        f"Unbound or missing sealed artifact: {path.parent}",
    )
    declared_bytes = 0
    header_shapes: Counter[str] = Counter()
    line_counts: dict[str, int] = {}
    hashes_verified = 0
    binding_lines: list[str] = []
    canonical_files: list[dict[str, Any]] = []
    for name, file_spec in sorted(expected_files.items()):
        binding = files[name]
        _require(isinstance(binding, dict), f"Invalid binding: {path}/{name}")
        _exact_keys(
            binding, ("bytes", "sha256"), f"Binding fields changed: {path}/{name}"
        )
        candidate = path.parent / name
        _require(
            not candidate.is_symlink(), f"Symlinked artifact forbidden: {candidate}"
        )
        _require(candidate.is_file(), f"Bound file missing: {candidate}")
        _require(
            candidate.resolve(strict=True).parent == path.parent.resolve(strict=True),
            f"Bound file escaped sealed directory: {candidate}",
        )
        expected_bytes = binding["bytes"]
        _require(
            type(expected_bytes) is int and expected_bytes >= 0,
            f"Invalid byte binding: {candidate}",
        )
        _require(
            candidate.stat().st_size == int(expected_bytes),
            f"Byte count changed: {candidate}",
        )
        declared_bytes += int(expected_bytes)
        declared_sha256 = str(binding["sha256"])
        _require(_is_sha256(declared_sha256), f"Invalid SHA-256 binding: {candidate}")
        if verify_hashes:
            observed_sha256 = _sha256(candidate)
            _require(observed_sha256 == declared_sha256, f"Hash changed: {candidate}")
            hashes_verified += 1
        binding_lines.append(f"{name}\t{expected_bytes}\t{declared_sha256}")
        header, rows = _validate_file_header(
            candidate, file_spec, role=role, schema=schema
        )
        if header is not None:
            header_shapes[header] += 1
        if rows is not None:
            line_counts[name] = rows
        canonical_files.append(
            {"path": name, "bytes": int(expected_bytes), "sha256": declared_sha256}
        )
    receipt_sha256 = _sha256(path)
    canonical_files.append(
        {
            "path": "receipt.json",
            "bytes": path.stat().st_size,
            "sha256": receipt_sha256,
        }
    )
    return {
        "kind": spec["kind"],
        "declared_files": len(files),
        "declared_bytes": declared_bytes,
        "hashes_verified": hashes_verified,
        "receipt_sha256": receipt_sha256,
        "file_binding_set_sha256": _canonical_lines_sha256(binding_lines),
        "npy_header_shapes": dict(sorted(header_shapes.items())),
        "jsonl_line_counts": line_counts,
        "canonical_files": sorted(canonical_files, key=lambda row: str(row["path"])),
    }


def _expected_role_tree(
    role: str, pilot: bool, schema: Mapping[str, Any]
) -> tuple[set[Path], set[Path], list[dict[str, Any]]]:
    specs = _receipt_specs(role, pilot, schema)
    directories = {Path(role)}
    files = {Path(role) / "summary.json", Path(role) / "yield_receipt.json"}
    for spec in specs:
        relative = Path(role) / spec["relative_directory"]
        for parent in (relative, *relative.parents):
            if parent == Path("."):
                continue
            directories.add(parent)
        files.add(relative / "receipt.json")
        files.update(relative / name for name in spec["files"])
    return directories, files, specs


def _validate_tree(
    root: Path, schema: Mapping[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    allowed_directories: set[Path] = set()
    allowed_files: set[Path] = set()
    role_specs: dict[str, list[dict[str, Any]]] = {}
    for role in schema["roles"]:
        directories, files, specs = _expected_role_tree(
            role, role in schema["pilots"], schema
        )
        allowed_directories.update(directories)
        allowed_files.update(files)
        role_specs[role] = specs
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in (*directory_names, *file_names):
            candidate = current_path / name
            _require(
                not candidate.is_symlink(),
                f"Symlink forbidden in run root: {candidate}",
            )
            relative = candidate.relative_to(root)
            if candidate.is_dir():
                _require(
                    relative in allowed_directories,
                    f"Unexpected directory in run root: {relative}",
                )
            else:
                _require(
                    relative in allowed_files,
                    f"Unexpected artifact in run root: {relative}",
                )
    for role, specs in role_specs.items():
        role_directory = root / role
        if not role_directory.exists():
            continue
        _require(role_directory.is_dir(), f"Role path is not a directory: {role}")
        for spec in specs:
            directory = role_directory / spec["relative_directory"]
            if not directory.exists():
                continue
            _require(directory.is_dir(), f"Sealed path is not a directory: {directory}")
            children = list(directory.iterdir())
            if children:
                _require(
                    (directory / "receipt.json").is_file(),
                    f"Unsealed canonical artifact directory: {directory}",
                )
    return role_specs


def _aggregate_counters(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    total: Counter[str] = Counter()
    for row in rows:
        value = row[key]
        _require(isinstance(value, dict), f"Expected mapping for {key}")
        total.update({str(name): int(count) for name, count in value.items()})
    return dict(sorted(total.items()))


def _validate_summary(
    path: Path, *, role: str, pilot: bool, schema: Mapping[str, Any]
) -> dict[str, Any]:
    summary = _read_json(path)
    runtime_preflight = _read_json(_root() / RUNTIME_PREFLIGHT_AGGREGATE_PATH)
    expected_keys = (
        "schema_version",
        "protocol_id",
        "status",
        "model_role",
        "pilot_role",
        "source_shards",
        "population_items",
        "present_item_views",
        "source_forward_sequences",
        "intervention_response_rows",
        "generation_calls",
        "model_receipt",
        "freeze_manifest_sha256",
        "runtime_preflight_aggregate_sha256",
        "elapsed_seconds_this_process",
        "completed_at_utc",
    )
    _exact_keys(summary, expected_keys, f"Summary fields changed: {role}")
    expected_values = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": SOURCE_PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "pilot_role": pilot,
        "source_shards": len(schema["source_observation_rows"]),
        "population_items": int(schema["population_items"]),
        "present_item_views": int(schema["present_item_views"]),
        "source_forward_sequences": int(schema["source_forward_sequences"]),
        "intervention_response_rows": int(schema["pilot_response_rows"])
        if pilot
        else 0,
        "generation_calls": 0,
    }
    for key, expected in expected_values.items():
        if type(expected) is int:
            _strict_int(
                summary.get(key), expected, f"Summary field changed: {role}/{key}"
            )
        else:
            _require(
                summary.get(key) == expected, f"Summary field changed: {role}/{key}"
            )
    _nonnegative_number(
        summary["elapsed_seconds_this_process"], f"Summary elapsed time invalid: {role}"
    )
    try:
        completed_at = datetime.fromisoformat(str(summary["completed_at_utc"]))
    except ValueError as error:
        raise AnalysisBoundaryError(f"Summary timestamp invalid: {role}") from error
    _require(completed_at.tzinfo is not None, f"Summary timestamp is naive: {role}")
    _require(
        summary["freeze_manifest_sha256"] == _sha256(_root() / ACQUISITION_FREEZE_PATH),
        f"Summary acquisition-freeze binding changed: {role}",
    )
    _require(
        summary["runtime_preflight_aggregate_sha256"]
        == _sha256(_root() / RUNTIME_PREFLIGHT_AGGREGATE_PATH),
        f"Summary runtime-preflight binding changed: {role}",
    )
    model = schema["model_specs"][role]
    model_receipt = summary["model_receipt"]
    _require(isinstance(model_receipt, dict), f"Summary model receipt invalid: {role}")
    model_receipt_keys = (
        "model_role",
        "artifact_model_id",
        "revision",
        "model_class",
        "parameter_count",
        "parameter_dtype_tensor_counts",
        "artifact",
        "torch_version",
        "transformers_version",
        "gpu",
        "runtime_preflight_aggregate_sha256",
        "tokenizer_receipt_sha256",
    )
    _exact_keys(
        model_receipt,
        model_receipt_keys,
        f"Summary model-receipt fields changed: {role}",
    )
    expected_model_values = {
        "model_role": role,
        "artifact_model_id": model["artifact_model_id"],
        "revision": model["revision"],
        "model_class": model["model_class"],
        "parameter_count": int(model["parameter_count"]),
        "torch_version": _acquisition_config()["runtime"]["critical_versions"]["torch"],
        "transformers_version": _acquisition_config()["runtime"]["critical_versions"][
            "transformers"
        ],
        "gpu": _acquisition_config()["runtime"]["hardware_pin"],
        "runtime_preflight_aggregate_sha256": summary[
            "runtime_preflight_aggregate_sha256"
        ],
    }
    for key, expected in expected_model_values.items():
        if type(expected) is int:
            _strict_int(
                model_receipt.get(key),
                expected,
                f"Summary model-receipt field changed: {role}/{key}",
            )
        else:
            _require(
                model_receipt.get(key) == expected,
                f"Summary model-receipt field changed: {role}/{key}",
            )
    dtype_counts = model_receipt["parameter_dtype_tensor_counts"]
    _require(
        isinstance(dtype_counts, dict)
        and set(dtype_counts) == {"torch.bfloat16"}
        and type(dtype_counts["torch.bfloat16"]) is int
        and dtype_counts["torch.bfloat16"] > 0,
        f"Summary parameter dtype receipt changed: {role}",
    )
    _require(
        model_receipt["artifact"]
        == runtime_preflight.get("model_artifacts", {}).get(role),
        f"Summary artifact receipt changed: {role}",
    )
    _require(
        model_receipt["tokenizer_receipt_sha256"]
        == runtime_preflight.get("receipt_sha256", {}).get(role)
        == _sha256(_root() / RUNTIME_PREFLIGHT_DIRECTORY / f"{role}.json"),
        f"Summary tokenizer binding changed: {role}",
    )
    return summary


def _validate_yield_receipt(path: Path, *, role: str) -> dict[str, Any]:
    value = _read_json(path)
    _exact_keys(
        value,
        (
            "schema_version",
            "protocol_id",
            "status",
            "model_role",
            "boundary",
            "foreign_gpu_pids",
            "time_utc",
        ),
        f"Yield receipt fields changed: {role}",
    )
    _strict_int(
        value.get("schema_version"), SCHEMA_VERSION, f"Yield schema changed: {role}"
    )
    _require(
        value.get("protocol_id") == SOURCE_PROTOCOL_ID
        and value.get("status") == "yielded_before_new_shard_for_foreign_gpu_contention"
        and value.get("model_role") == role,
        f"Yield receipt changed: {role}",
    )
    _require(
        isinstance(value["boundary"], str) and value["boundary"],
        f"Yield boundary invalid: {role}",
    )
    _require(
        isinstance(value["foreign_gpu_pids"], list)
        and value["foreign_gpu_pids"]
        and all(type(pid) is int and pid > 0 for pid in value["foreign_gpu_pids"]),
        f"Yield PID list invalid: {role}",
    )
    try:
        observed_at = datetime.fromisoformat(str(value["time_utc"]))
    except ValueError as error:
        raise AnalysisBoundaryError(f"Yield timestamp invalid: {role}") from error
    _require(observed_at.tzinfo is not None, f"Yield timestamp is naive: {role}")
    return value


def inventory(run_root: Path, *, verify_hashes: bool = False) -> dict[str, Any]:
    audit_freeze()
    schema = _artifact_expectations()
    roles = list(schema["roles"])
    pilots = set(schema["pilots"])
    expanded_root = run_root.expanduser()
    _require(
        not expanded_root.is_symlink(), f"Symlinked run root forbidden: {run_root}"
    )
    root = expanded_root.resolve(strict=True)
    _require(root.is_dir(), f"Run root is not a directory: {root}")
    role_specs = _validate_tree(root, schema)
    role_rows: list[dict[str, Any]] = []
    canonical_file_rows: list[dict[str, Any]] = []
    canonical_allowed_paths: set[str] = set()
    for role in roles:
        role_directory = root / role
        specs = role_specs[role]
        for spec in specs:
            leaf = Path(role) / spec["relative_directory"]
            canonical_allowed_paths.add(str(leaf / "receipt.json"))
            canonical_allowed_paths.update(str(leaf / name) for name in spec["files"])
        canonical_allowed_paths.add(str(Path(role) / "summary.json"))
        canonical_allowed_paths.add(str(Path(role) / "yield_receipt.json"))
        present_specs = [
            spec
            for spec in specs
            if (role_directory / spec["relative_directory"] / "receipt.json").is_file()
        ]
        receipts = [
            role_directory / spec["relative_directory"] / "receipt.json"
            for spec in present_specs
        ]
        receipt_audits = [
            _audit_receipt(
                path,
                role=role,
                spec=spec,
                schema=schema,
                verify_hashes=verify_hashes,
            )
            for path, spec in zip(receipts, present_specs, strict=True)
        ]
        kinds = Counter(str(row["kind"]) for row in receipt_audits)
        summary_path = role_directory / "summary.json"
        summary = (
            _validate_summary(
                summary_path,
                role=role,
                pilot=role in pilots,
                schema=schema,
            )
            if summary_path.is_file()
            else None
        )
        summary_sha256 = _sha256(summary_path) if summary is not None else None
        yield_path = role_directory / "yield_receipt.json"
        yield_receipt = (
            _validate_yield_receipt(yield_path, role=role)
            if yield_path.is_file()
            else None
        )
        yield_sha256 = _sha256(yield_path) if yield_receipt is not None else None
        expected_receipts = len(specs)
        expected_kinds = {
            "baseline": 1,
            "source": 12,
        }
        if role in pilots:
            expected_kinds.update(
                {
                    "pilot_zero": 1,
                    "pilot_item": 12,
                    "pilot_prototype": 6,
                    "pilot_random": 8,
                }
            )
        complete = bool(
            summary is not None
            and len(receipts) == expected_receipts
            and dict(kinds) == expected_kinds
        )
        status = (
            "complete"
            if complete
            else "in_progress"
            if role_directory.exists()
            else "absent"
        )
        if summary is not None and not complete:
            status = "invalid_complete_boundary"
        role_binding_lines: list[str] = []
        for receipt_path, receipt_audit, spec in zip(
            receipts, receipt_audits, present_specs, strict=True
        ):
            relative = receipt_path.relative_to(role_directory)
            role_binding_lines.append(
                f"receipt\t{relative}\t{receipt_audit['receipt_sha256']}"
            )
            role_binding_lines.append(
                "bound-files\t"
                f"{relative.parent}\t{receipt_audit['file_binding_set_sha256']}"
            )
            for file_row in receipt_audit["canonical_files"]:
                canonical_file_rows.append(
                    {
                        "relative_path": str(
                            Path(role)
                            / spec["relative_directory"]
                            / str(file_row["path"])
                        ),
                        "bytes": int(file_row["bytes"]),
                        "sha256": str(file_row["sha256"]),
                    }
                )
        if summary_sha256 is not None:
            role_binding_lines.append(f"summary\tsummary.json\t{summary_sha256}")
            canonical_file_rows.append(
                {
                    "relative_path": str(Path(role) / "summary.json"),
                    "bytes": summary_path.stat().st_size,
                    "sha256": summary_sha256,
                }
            )
        if yield_sha256 is not None:
            role_binding_lines.append(
                f"yield-receipt\tyield_receipt.json\t{yield_sha256}"
            )
            canonical_file_rows.append(
                {
                    "relative_path": str(Path(role) / "yield_receipt.json"),
                    "bytes": yield_path.stat().st_size,
                    "sha256": yield_sha256,
                }
            )
        role_binding_root = _canonical_lines_sha256(sorted(role_binding_lines))
        role_rows.append(
            {
                "role": role,
                "pilot_role": role in pilots,
                "status": status,
                "summary_present": summary is not None,
                "summary_sha256": summary_sha256,
                "yield_receipt_present": yield_receipt is not None,
                "yield_receipt_sha256": yield_sha256,
                "sealed_receipts": len(receipts),
                "expected_receipts": expected_receipts,
                "receipt_kinds": dict(sorted(kinds.items())),
                "expected_receipt_kinds": dict(sorted(expected_kinds.items())),
                "incomplete_stage_directories": [],
                "declared_files": sum(
                    int(row["declared_files"]) for row in receipt_audits
                ),
                "declared_bytes": sum(
                    int(row["declared_bytes"]) for row in receipt_audits
                ),
                "hashes_verified": sum(
                    int(row["hashes_verified"]) for row in receipt_audits
                ),
                "role_binding_root_sha256": role_binding_root,
                "npy_header_shapes": _aggregate_counters(
                    receipt_audits, "npy_header_shapes"
                ),
                "scientific_values_parsed": False,
            }
        )
    completed = sum(row["status"] == "complete" for row in role_rows)
    invalid = any(row["status"] == "invalid_complete_boundary" for row in role_rows)
    all_complete = completed == len(roles) and not invalid
    scientific_open = bool(all_complete and verify_hashes)
    run_binding_root = _canonical_lines_sha256(
        f"{row['role']}\t{row['role_binding_root_sha256']}" for row in role_rows
    )
    canonical_file_rows.sort(key=lambda row: str(row["relative_path"]))
    _require(
        len({str(row["relative_path"]) for row in canonical_file_rows})
        == len(canonical_file_rows),
        "Canonical file inventory contains duplicates",
    )
    return {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "queue_complete" if all_complete else "queue_in_progress",
        "run_root": str(root),
        "roles_complete": completed,
        "roles_required": len(roles),
        "independent_hash_verification": verify_hashes,
        "run_binding_root_sha256": run_binding_root,
        "inspection_scope": (
            "sealed_paths_counts_sizes_npy_headers_and_content_blind_sha256"
            if verify_hashes
            else "sealed_paths_counts_sizes_and_npy_headers"
        ),
        "scientific_open_authorized": scientific_open,
        "scientific_open_blockers": (
            []
            if scientific_open
            else [
                *([] if all_complete else ["full_nine_role_queue_not_complete"]),
                *(
                    []
                    if verify_hashes
                    else ["independent_hash_verification_not_requested"]
                ),
            ]
        ),
        "scientific_values_parsed": False,
        "canonical_allowed_relative_paths": sorted(canonical_allowed_paths),
        "canonical_file_bindings": canonical_file_rows,
        "role_inventory": role_rows,
    }


def _closeout_payload(inventory_row: Mapping[str, Any]) -> dict[str, Any]:
    _require(
        inventory_row.get("scientific_open_authorized") is True
        and inventory_row.get("independent_hash_verification") is True
        and inventory_row.get("scientific_values_parsed") is False,
        "Verified exact-schema inventory is required for closeout",
    )
    role_rows = inventory_row["role_inventory"]
    file_rows = inventory_row["canonical_file_bindings"]
    _require(isinstance(role_rows, list), "Closeout role inventory invalid")
    _require(isinstance(file_rows, list), "Closeout file inventory invalid")
    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "scientific_open_closeout_complete",
        "scientific_open_authorized": True,
        "independent_hash_verification": True,
        "scientific_values_parsed": False,
        "analysis_freeze_sha256": _sha256(_root() / FREEZE_PATH),
        "run_root": str(inventory_row["run_root"]),
        "run_binding_root_sha256": str(inventory_row["run_binding_root_sha256"]),
        "roles_complete": int(inventory_row["roles_complete"]),
        "roles_required": int(inventory_row["roles_required"]),
        "total_verified_files": len(file_rows),
        "total_verified_bytes": sum(int(row["bytes"]) for row in file_rows),
        "role_bindings": [
            {
                "role": str(row["role"]),
                "role_binding_root_sha256": str(row["role_binding_root_sha256"]),
            }
            for row in role_rows
        ],
        "canonical_allowed_relative_paths": list(
            inventory_row["canonical_allowed_relative_paths"]
        ),
        "verified_file_bindings": list(file_rows),
    }


def write_verified_closeout(run_root: Path, output: Path) -> dict[str, Any]:
    expanded_root = run_root.expanduser()
    _require(
        not expanded_root.is_symlink(), f"Symlinked run root forbidden: {run_root}"
    )
    root = expanded_root.resolve(strict=True)
    output = output.expanduser()
    _require(
        output.parent.is_dir(),
        f"Verified closeout parent directory is missing: {output.parent}",
    )
    output_parent = output.parent.resolve(strict=True)
    resolved_output = output_parent / output.name
    _require(
        not resolved_output.is_relative_to(root),
        "Verified closeout must be stored outside the sealed run root",
    )
    _require(not resolved_output.is_symlink(), "Symlinked closeout path is forbidden")
    result = _closeout_payload(inventory(expanded_root, verify_hashes=True))
    if resolved_output.exists():
        _require(
            _read_json(resolved_output) == result,
            f"Existing closeout differs: {resolved_output}",
        )
    else:
        _write_json(resolved_output, result)
    return result


def audit_verified_closeout(run_root: Path, closeout: Path) -> dict[str, Any]:
    root = run_root.expanduser().resolve(strict=True)
    expanded_closeout = closeout.expanduser()
    _require(not expanded_closeout.is_symlink(), "Symlinked closeout path is forbidden")
    closeout_path = expanded_closeout.resolve(strict=True)
    _require(
        not closeout_path.is_relative_to(root),
        "Verified closeout must be stored outside the sealed run root",
    )
    observed = _read_json(closeout_path)
    expected = _closeout_payload(inventory(run_root, verify_hashes=True))
    _require(observed == expected, "Verified closeout no longer matches the sealed run")
    return {
        "status": "scientific_open_closeout_audit_pass",
        "analysis_id": ANALYSIS_ID,
        "run_binding_root_sha256": expected["run_binding_root_sha256"],
        "scientific_values_parsed": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design")
    frozen = sub.add_parser("freeze")
    frozen.add_argument("--output", type=Path, default=FREEZE_PATH)
    sub.add_parser("audit-freeze")
    inspect = sub.add_parser("inventory")
    inspect.add_argument("--run-root", type=Path, required=True)
    inspect.add_argument("--output", type=Path)
    inspect.add_argument("--verify-hashes", action="store_true")
    closeout = sub.add_parser("closeout")
    closeout.add_argument("--run-root", type=Path, required=True)
    closeout.add_argument("--output", type=Path, required=True)
    closeout_audit = sub.add_parser("audit-closeout")
    closeout_audit.add_argument("--run-root", type=Path, required=True)
    closeout_audit.add_argument("--closeout", type=Path, required=True)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "inventory":
        result = inventory(args.run_root, verify_hashes=args.verify_hashes)
        if args.output is not None:
            _write_json(args.output, result)
    elif args.command == "closeout":
        result = write_verified_closeout(args.run_root, args.output)
    else:
        result = audit_verified_closeout(args.run_root, args.closeout)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
