#!/usr/bin/env python3
"""Freeze, acquire, summarize, and decide T10 cross-model replication.

The selected-model runner is batch-one, observational, and resumable only at
completed item-shard boundaries. It captures the exact API-level final hidden
state used by T9 and, in the same forward, the raw output of the last decoder
block. The latter is a registered secondary and cannot rescue the primary.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import sys
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

import mistral7b_semantic_atlas_reserve_confirmation_v0 as t9  # noqa: E402
import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


PROTOCOL_ID = "glyphprobe-semantic-atlas-cross-model-replication-v0"
CONFIG_PATH = Path("configs/semantic_atlas_cross_model_replication_v0.yaml")
PREFLIGHT_DIRECTORY = Path(
    "validation/semantic_atlas_cross_model_replication_v0"
)
PREFLIGHT_PATH = PREFLIGHT_DIRECTORY / "engineering_preflight.json"
ENDPOINT_AUDIT_PATH = PREFLIGHT_DIRECTORY / "endpoint_semantics_audit.json"
FREEZE_PATH = Path("data/manifests/semantic_atlas_cross_model_replication_v0.json")
VIEW_ORDER = ("glyph", "unicode_name", "codepoint_literal")
PAIR_ORDER = (("glyph_name", 0, 1), ("glyph_codepoint", 0, 2))
ENDPOINT_ORDER = ("returned_final_hidden_state", "raw_last_decoder_block_output")
STATIC_FROZEN_ASSETS = (
    "configs/semantic_atlas_cross_model_replication_v0.yaml",
    "data/manifests/mistral7b_semantic_atlas_selection_v0.json",
    "data/manifests/mistral7b_semantic_atlas_reserve_confirmation_v0.json",
    "artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/run/run_receipt.json",
    "artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/analysis/primary_result.json",
    "artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/analysis/analysis_receipt.json",
    "docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md",
    "docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md",
    "scripts/semantic_atlas_cross_model_replication_v0.py",
    "tests/test_semantic_atlas_cross_model_replication_v0.py",
    "validation/semantic_atlas_cross_model_replication_v0/endpoint_semantics_audit.json",
    "validation/semantic_atlas_cross_model_replication_v0/engineering_preflight.json",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config() -> dict[str, Any]:
    value = atlas._read_yaml(_root() / CONFIG_PATH)
    atlas._require(value.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return value


def model_roles() -> tuple[str, ...]:
    return tuple(str(value) for value in _config()["models"]["order"])


def _model_spec(role: str) -> dict[str, Any]:
    config = _config()
    atlas._require(role in model_roles(), f"Unknown model role: {role}")
    value = config["models"].get(role)
    atlas._require(isinstance(value, dict), f"Missing model spec: {role}")
    return dict(value)


def items() -> list[dict[str, Any]]:
    rows = t9.confirmation_items()
    config = _config()
    atlas._require(
        len(rows) == int(config["population"]["expected_items"]),
        "T10 population changed",
    )
    atlas._require(
        [int(row["source_index"]) for row in rows]
        == sorted(int(row["source_index"]) for row in rows),
        "T10 population order changed",
    )
    return rows


def _source_pairs(config: Mapping[str, Any]) -> list[tuple[Path, str]]:
    bindings = config["source_bindings"]
    names = (
        "population_manifest",
        "t9_freeze_manifest",
        "t9_run_receipt",
        "t9_primary_result",
        "t9_analysis_receipt",
    )
    return [
        (_root() / str(bindings[name]), str(bindings[f"{name}_sha256"]))
        for name in names
    ]


def audit_design() -> dict[str, Any]:
    config = _config()
    observed: dict[str, str] = {}
    for path, expected in _source_pairs(config):
        atlas._require(path.is_file(), f"Bound source missing: {path.name}")
        actual = atlas._sha256(path)
        atlas._require(actual == expected, f"Bound source changed: {path.name}")
        observed[path.relative_to(_root()).as_posix()] = actual
    primary = atlas._read_json(
        _root() / str(config["source_bindings"]["t9_primary_result"])
    )
    atlas._require(
        primary.get("alignment_confirmed") is True,
        "T9 design motivation binding changed",
    )
    atlas._require(
        int(primary.get("item_count", -1)) == len(items()),
        "T9/T10 population count mismatch",
    )
    atlas._require(
        tuple(config["endpoints"]["order"]) == ENDPOINT_ORDER,
        "Endpoint order changed",
    )
    atlas._require(len(model_roles()) == 9, "T10 model roster changed")
    atlas._require(
        tuple(config["cross_model_primary"]["core_order"])
        == tuple(config["models"]["core"]),
        "Core model order mismatch",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "population_items": len(items()),
        "model_cells": len(model_roles()),
        "core_cells": len(config["models"]["core"]),
        "source_bindings": observed,
        "t9_outcome_known_before_design": True,
        "t10_candidate_model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
    }


def _runtime_versions() -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for package in ("glyphprobe", "torch", "transformers", "numpy", "PyYAML"):
        try:
            values[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            values[package] = None
    return values


def _resolve_attr(value: Any, dotted: str) -> Any:
    current = value
    for component in dotted.split("."):
        atlas._require(hasattr(current, component), f"Missing model path: {dotted}")
        current = getattr(current, component)
    return current


def _sequence_hash(rows: Sequence[Sequence[int]]) -> str:
    return atlas._sequence_sha256(rows)


def _validate_weight_artifact_completeness(snapshot: Path) -> dict[str, Any]:
    """Fail closed when a Hub snapshot omits an index-referenced weight shard."""

    weight_paths = sorted(
        {
            path
            for pattern in ("*.safetensors", "pytorch_model*.bin")
            for path in snapshot.rglob(pattern)
            if path.is_file()
        }
    )
    atlas._require(weight_paths, "Model snapshot contains no weight artifact")
    atlas._require(
        all(path.stat().st_size > 0 for path in weight_paths),
        "Model snapshot contains an empty weight artifact",
    )
    index_rows: list[dict[str, Any]] = []
    referenced: set[str] = set()
    for index_path in sorted(snapshot.rglob("*.index.json")):
        payload = atlas._read_json(index_path)
        weight_map = payload.get("weight_map")
        atlas._require(
            isinstance(weight_map, dict) and weight_map,
            f"Weight index has no weight_map: {index_path.name}",
        )
        names = sorted({str(value) for value in weight_map.values()})
        for name in names:
            relative = Path(name)
            atlas._require(
                not relative.is_absolute() and ".." not in relative.parts,
                f"Unsafe weight-index path: {name}",
            )
            atlas._require(
                (snapshot / relative).is_file(),
                f"Weight index references a missing shard: {name}",
            )
            atlas._require(
                (snapshot / relative).stat().st_size > 0,
                f"Weight index references an empty shard: {name}",
            )
            referenced.add(relative.as_posix())
        index_rows.append(
            {
                "index": index_path.relative_to(snapshot).as_posix(),
                "referenced_weight_files": names,
            }
        )
    return {
        "weight_file_count": len(weight_paths),
        "weight_total_bytes": sum(path.stat().st_size for path in weight_paths),
        "index_file_count": len(index_rows),
        "index_referenced_weight_file_count": len(referenced),
        "indexes": index_rows,
    }


def _tokenize_roster(tokenizer: Any, config: Mapping[str, Any]) -> dict[str, Any]:
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
                    atlas._view_text(item, view), add_special_tokens=False
                )
            ]
            atlas._require(raw, f"Empty tokenization: {item['codepoint']}/{view}")
            raw_by_view[view].append(raw)
            lengths[view] = len(raw)
        item_rows.append(
            {
                "item_index": item_index,
                "source_index": int(item["source_index"]),
                "codepoint": str(item["codepoint"]),
                "token_counts": lengths,
                "exact_stratum_key": [lengths[view] for view in VIEW_ORDER],
            }
        )
    for view in VIEW_ORDER:
        atlas._require(
            len({tuple(row) for row in raw_by_view[view]}) == len(population),
            f"Non-unique view token sequence: {view}",
        )
    carrier_rows: dict[str, Any] = {}
    maximum_tokens = 0
    for carrier in config["input"]["carrier_order"]:
        carrier = str(carrier)
        spec = config["input"]["carriers"][carrier]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        unit_ids = [
            int(value)
            for value in tokenizer.encode(unit, add_special_tokens=False)
        ]
        atlas._require(len(unit_ids) == 1, f"Carrier is not one token: {carrier}")
        prefix_exact = 0
        decode_exact = 0
        for view in VIEW_ORDER:
            for item_index, item in enumerate(population):
                text = atlas._view_text(item, view) + unit * repeats
                ids = [
                    int(value)
                    for value in tokenizer.encode(text, add_special_tokens=False)
                ]
                expected = raw_by_view[view][item_index] + unit_ids * repeats
                atlas._require(
                    ids == expected,
                    f"Carrier boundary changed: {item['codepoint']}/{view}/{carrier}",
                )
                combined[view][carrier].append(ids)
                prefix_exact += int(ids[: -repeats] == raw_by_view[view][item_index])
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
        atlas._require(prefix_exact == expected_cases, f"Prefix check failed: {carrier}")
        atlas._require(decode_exact == expected_cases, f"Decode check failed: {carrier}")
        carrier_rows[carrier] = {
            "unit": unit,
            "repeats": repeats,
            "token_id": unit_ids[0],
            "prefix_exact_count": prefix_exact,
            "decode_exact_count": decode_exact,
        }
    strata: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for row in item_rows:
        key = tuple(int(value) for value in row["exact_stratum_key"])
        strata[key].append(int(row["item_index"]))
    eligible_strata = [indices for indices in strata.values() if len(indices) >= 2]
    eligible_indices = sorted(index for group in eligible_strata for index in group)
    eligible_lookup = {global_index: local for local, global_index in enumerate(eligible_indices)}
    local_groups = [
        [eligible_lookup[index] for index in group]
        for _, group in sorted(strata.items())
        if len(group) >= 2
    ]
    atlas._require(
        len(eligible_indices)
        >= int(config["tokenization_guardrail"]["minimum_eligible_items"]),
        "Exact-stratum coverage fell below the frozen minimum",
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
                "raw": {
                    view: _sequence_hash(raw_by_view[view]) for view in VIEW_ORDER
                },
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
            "exact_triple_strata": {
                "stratum_count": len(strata),
                "eligible_stratum_count": len(eligible_strata),
                "eligible_item_count": len(eligible_indices),
                "excluded_singleton_item_count": len(population) - len(eligible_indices),
                "eligible_global_indices": eligible_indices,
                "eligible_local_strata": local_groups,
                "strata": [
                    {"key": list(key), "item_indices": indices, "count": len(indices)}
                    for key, indices in sorted(strata.items())
                ],
            },
        },
    }


def tokenizer_preflight(role: str, model_path: Path, output: Path) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoConfig, AutoTokenizer

    config = _config()
    audit_design()
    spec = _model_spec(role)
    snapshot = model_path.resolve()
    atlas._require(snapshot.is_dir(), f"Model snapshot missing: {snapshot}")
    atlas._require(snapshot.name == str(spec["revision"]), "Snapshot revision mismatch")
    weight_completeness = _validate_weight_artifact_completeness(snapshot)
    architecture = AutoConfig.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    atlas._require(
        str(architecture.model_type) == str(spec["expected_model_type"]),
        "Model type mismatch",
    )
    atlas._require(
        int(architecture.num_hidden_layers) == int(spec["expected_num_layers"]),
        "Layer count mismatch",
    )
    atlas._require(
        int(architecture.hidden_size) == int(spec["expected_model_dim"]),
        "Hidden width mismatch",
    )
    atlas._require(
        int(architecture.vocab_size) == int(spec["expected_vocab_size"]),
        "Model vocab mismatch",
    )
    architectures = [str(value) for value in getattr(architecture, "architectures", [])]
    atlas._require(
        str(spec["expected_model_class"]) in architectures,
        "Configured model class is absent from architecture metadata",
    )
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    tokenization = _tokenize_roster(tokenizer, config)["receipt"]
    artifact = model_artifact_receipt(snapshot)
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "tokenizer_and_static_artifact_preflight_pass_zero_model_forwards",
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "architecture": {
            "model_type": str(architecture.model_type),
            "architectures": architectures,
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
        "weight_artifact_completeness": weight_completeness,
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    atlas._require(not output.exists(), f"Preflight already exists: {output}")
    atlas._write_json(output, payload)
    return {
        "status": "pass",
        "model_role": role,
        "output": output.as_posix(),
        "sha256": atlas._sha256(output),
        "eligible_items": tokenization["exact_triple_strata"]["eligible_item_count"],
        "artifact_manifest_sha256": artifact["manifest_sha256"],
    }


def endpoint_semantics_audit(output: Path) -> dict[str, Any]:
    """Record why the T9 API endpoint is not raw final-block resid_post."""

    import torch
    import transformers
    from transformers import MistralConfig, MistralForCausalLM

    torch.manual_seed(20260829)
    tiny = MistralForCausalLM(
        MistralConfig(
            vocab_size=64,
            hidden_size=32,
            intermediate_size=64,
            num_hidden_layers=2,
            num_attention_heads=4,
            num_key_value_heads=2,
            max_position_embeddings=64,
        )
    ).eval()
    captured: list[Any] = []

    def hook(_module: Any, _inputs: Any, value: Any) -> None:
        captured.append(value[0] if isinstance(value, tuple) else value)

    handle = tiny.model.layers[-1].register_forward_hook(hook)
    with torch.inference_mode():
        result = tiny(
            input_ids=torch.tensor([[1, 2, 3, 4]], dtype=torch.long),
            use_cache=False,
            output_hidden_states=True,
            return_dict=True,
        )
    handle.remove()
    atlas._require(len(captured) == 1, "Synthetic hook count mismatch")
    raw = captured[0]
    returned = result.hidden_states[-1]
    normalized = tiny.model.norm(raw)
    returned_vs_raw = float(torch.max(torch.abs(returned - raw)).item())
    returned_vs_norm = float(torch.max(torch.abs(returned - normalized)).item())
    atlas._require(returned_vs_raw > 0.0, "Synthetic final norm was unexpectedly identity")
    atlas._require(returned_vs_norm == 0.0, "Returned state did not equal final norm")
    source = (_root() / "scripts/mistral7b_semantic_atlas_reserve_confirmation_v0.py").read_text(
        encoding="utf-8"
    )
    atlas._require(
        "output.hidden_states[layer + 1]" in source,
        "T9 endpoint source expression changed",
    )
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "audit_role": "synthetic_endpoint_semantics_no_candidate_model_or_population_forward",
        "synthetic_model": "random_tiny_mistral_two_layers",
        "synthetic_token_count": 4,
        "returned_hidden_state_count": len(result.hidden_states),
        "returned_vs_raw_last_block_max_abs": returned_vs_raw,
        "returned_vs_explicit_final_norm_max_abs": returned_vs_norm,
        "t9_source_expression": "output.hidden_states[layer + 1] at layer 31",
        "t10_primary_expression": "output.hidden_states[-1]",
        "t10_secondary_expression": "last decoder block forward-hook output",
        "interpretation": "t9_api_endpoint_is_returned_final_normalized_state_not_raw_last_block_output",
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "candidate_model_weights_loaded": False,
        "candidate_population_model_forward_calls": 0,
        "synthetic_model_forward_calls": 1,
        "intervention_calls": 0,
        "generation_calls": 0,
    }
    atlas._require(not output.exists(), f"Endpoint audit already exists: {output}")
    atlas._write_json(output, payload)
    return {"status": "pass", "output": output.as_posix(), "sha256": atlas._sha256(output)}


def _receipt_path(role: str) -> Path:
    return _root() / PREFLIGHT_DIRECTORY / "tokenizers" / f"{role}.json"


def assemble_preflight(output: Path) -> dict[str, Any]:
    config = _config()
    design = audit_design()
    endpoint = atlas._read_json(_root() / ENDPOINT_AUDIT_PATH)
    atlas._require(endpoint.get("status") == "pass", "Endpoint audit did not pass")
    receipts: dict[str, Any] = {}
    artifacts: dict[str, Any] = {}
    tokenizers: dict[str, Any] = {}
    for role in model_roles():
        path = _receipt_path(role)
        atlas._require(path.is_file(), f"Missing tokenizer receipt: {role}")
        receipt = atlas._read_json(path)
        atlas._require(receipt.get("protocol_id") == PROTOCOL_ID, "Receipt protocol mismatch")
        atlas._require(receipt.get("model_role") == role, "Receipt role mismatch")
        atlas._require(receipt.get("model_forward_calls") == 0, "Preflight used model forward")
        atlas._require(receipt.get("model_weights_loaded") is False, "Preflight loaded weights")
        spec = _model_spec(role)
        atlas._require(receipt.get("revision") == spec["revision"], "Receipt revision mismatch")
        eligible = int(receipt["tokenizer"]["exact_triple_strata"]["eligible_item_count"])
        atlas._require(
            eligible >= int(config["tokenization_guardrail"]["minimum_eligible_items"]),
            f"Matched coverage too small: {role}",
        )
        receipt_hash = atlas._sha256(path)
        receipts[role] = receipt_hash
        artifacts[role] = {
            "artifact_model_id": receipt["artifact_model_id"],
            "revision": receipt["revision"],
            **{
                key: receipt["model_artifact"][key]
                for key in ("manifest_sha256", "file_count", "total_bytes")
            },
        }
        tokenizers[role] = {
            "receipt_sha256": receipt_hash,
            "class": receipt["tokenizer"]["class"],
            "vocab_size": receipt["tokenizer"]["vocab_size"],
            "ordered_sequence_sha256": receipt["tokenizer"]["ordered_sequence_sha256"],
            "carriers": receipt["tokenizer"]["carriers"],
            "exact_triple_strata": {
                key: receipt["tokenizer"]["exact_triple_strata"][key]
                for key in (
                    "stratum_count",
                    "eligible_stratum_count",
                    "eligible_item_count",
                    "excluded_singleton_item_count",
                )
            },
        }
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "engineering_preflight_complete_zero_t10_candidate_forwards",
        "design_audit": design,
        "endpoint_semantics_audit_sha256": atlas._sha256(_root() / ENDPOINT_AUDIT_PATH),
        "model_order": list(model_roles()),
        "tokenizer_receipts": receipts,
        "model_artifacts": artifacts,
        "tokenizers": tokenizers,
        "model_weights_loaded": False,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_result_available": False,
    }
    atlas._require(not output.exists(), f"Engineering preflight exists: {output}")
    atlas._write_json(output, payload)
    return {"status": "pass", "output": output.as_posix(), "sha256": atlas._sha256(output)}


def _frozen_assets() -> tuple[str, ...]:
    receipt_paths = tuple(
        (PREFLIGHT_DIRECTORY / "tokenizers" / f"{role}.json").as_posix()
        for role in model_roles()
    )
    return STATIC_FROZEN_ASSETS + receipt_paths


def build_freeze(output: Path) -> dict[str, Any]:
    config = _config()
    preflight = atlas._read_json(_root() / PREFLIGHT_PATH)
    atlas._require(
        preflight.get("status")
        == "engineering_preflight_complete_zero_t10_candidate_forwards",
        "Engineering preflight is incomplete",
    )
    atlas._require(preflight.get("model_forward_calls") == 0, "Preflight forward count changed")
    assets: dict[str, str] = {}
    for relative in _frozen_assets():
        path = _root() / relative
        atlas._require(path.is_file(), f"Missing frozen asset: {relative}")
        assets[relative] = atlas._sha256(path)
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t10_candidate_model_forward",
        "experiment_role": config["experiment_role"],
        "claim_boundary": config["claim_boundary"],
        "frozen_assets": assets,
        "engineering_preflight_sha256": atlas._sha256(_root() / PREFLIGHT_PATH),
        "model_artifacts": preflight["model_artifacts"],
        "tokenizers": preflight["tokenizers"],
        "model_forward_calls_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
    }
    atlas._require(not output.exists(), f"Freeze manifest exists: {output}")
    atlas._write_json(output, payload)
    return {
        "status": "pass",
        "manifest_sha256": atlas._sha256(output),
        "frozen_asset_count": len(assets),
        "model_cells": len(model_roles()),
    }


def audit_freeze() -> dict[str, Any]:
    manifest = atlas._read_json(_root() / FREEZE_PATH)
    atlas._require(manifest.get("protocol_id") == PROTOCOL_ID, "Freeze protocol mismatch")
    atlas._require(
        manifest.get("status") == "freeze_complete_before_any_t10_candidate_model_forward",
        "Freeze is incomplete",
    )
    for relative, expected in manifest["frozen_assets"].items():
        path = _root() / relative
        atlas._require(path.is_file(), f"Frozen asset missing: {relative}")
        atlas._require(atlas._sha256(path) == expected, f"Frozen asset changed: {relative}")
    atlas._require(
        atlas._sha256(_root() / PREFLIGHT_PATH)
        == manifest["engineering_preflight_sha256"],
        "Engineering preflight changed",
    )
    return {
        "status": "pass",
        "manifest_sha256": atlas._sha256(_root() / FREEZE_PATH),
        "frozen_asset_count": len(manifest["frozen_assets"]),
    }


def _validate_runtime(config: Mapping[str, Any]) -> dict[str, Any]:
    import torch

    versions = _runtime_versions()
    for package, expected in config["runtime"]["critical_versions"].items():
        atlas._require(versions.get(package) == str(expected), f"Runtime version mismatch: {package}")
    atlas._require(torch.cuda.is_available(), "CUDA unavailable")
    atlas._require(torch.cuda.is_bf16_supported(), "CUDA BF16 unavailable")
    atlas._require(
        str(torch.cuda.get_device_name(0)) == str(config["runtime"]["hardware_pin"]),
        "GPU identity mismatch",
    )
    return versions


def _load_model(role: str, model_path: Path) -> tuple[Any, Any, Any, Any, dict[str, Any], dict[str, Any]]:
    import torch
    import transformers
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoModelForCausalLM, AutoTokenizer

    config = _config()
    spec = _model_spec(role)
    freeze = atlas._read_json(_root() / FREEZE_PATH)
    pinned = freeze["model_artifacts"][role]
    artifact = model_artifact_receipt(model_path)
    for field in ("manifest_sha256", "file_count", "total_bytes"):
        atlas._require(artifact[field] == pinned[field], f"Model artifact changed: {role}/{field}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    roster = _tokenize_roster(tokenizer, config)
    receipt = atlas._read_json(_receipt_path(role))
    atlas._require(
        roster["receipt"]["ordered_sequence_sha256"]
        == receipt["tokenizer"]["ordered_sequence_sha256"],
        "Runtime token sequences changed",
    )
    dtype_key = "dtype" if int(transformers.__version__.split(".", 1)[0]) >= 5 else "torch_dtype"
    kwargs = {
        "local_files_only": True,
        "trust_remote_code": False,
        dtype_key: torch.bfloat16,
    }
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.to("cuda")
    model.eval()
    atlas._require(type(model).__name__ == spec["expected_model_class"], "Loaded model class mismatch")
    atlas._require(int(model.config.num_hidden_layers) == int(spec["expected_num_layers"]), "Loaded layer count mismatch")
    count = sum(int(parameter.numel()) for parameter in model.parameters())
    atlas._require(count == int(spec["expected_parameter_count"]), "Parameter count mismatch")
    parameter_dtypes = Counter(str(parameter.dtype) for parameter in model.parameters())
    atlas._require(set(parameter_dtypes) == {"torch.bfloat16"}, "Loaded parameter dtype mismatch")
    blocks = _resolve_attr(model, str(spec["expected_block_path"]))
    atlas._require(len(blocks) == int(spec["expected_num_layers"]), "Decoder block roster mismatch")
    model_receipt = {
        "model_role": role,
        "artifact_model_id": spec["artifact_model_id"],
        "revision": spec["revision"],
        "model_class": type(model).__name__,
        "parameter_count": count,
        "parameter_dtype_tensor_counts": dict(parameter_dtypes),
        "artifact": artifact,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "gpu": str(torch.cuda.get_device_name(0)),
    }
    return torch, tokenizer, model, blocks[-1], model_receipt, roster


def _records(roster: Mapping[str, Any], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item_index, _item in enumerate(items()):
        for view_index, view in enumerate(VIEW_ORDER):
            raw_ids = [int(value) for value in roster["raw_ids"][view][item_index]]
            for carrier_index, carrier in enumerate(config["input"]["carrier_order"]):
                carrier = str(carrier)
                ids = [
                    int(value)
                    for value in roster["combined_ids"][view][carrier][item_index]
                ]
                rows.append(
                    {
                        "item_offset": item_index,
                        "view_index": view_index,
                        "view": view,
                        "carrier_index": carrier_index,
                        "carrier": carrier,
                        "raw_ids": raw_ids,
                        "input_ids": ids,
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
) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    population = items()
    shard_size = int(config["acquisition"]["item_shard_size"])
    start = shard_index * shard_size
    stop = min(len(population), start + shard_size)
    atlas._require(start < stop, f"Shard index out of range: {shard_index}")
    shard_items = population[start:stop]
    stage, final = atlas._atomic_shard_directory(run_root, shard_index)
    intent = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "forward_may_begin_after_this_record",
        "model_role": role,
        "shard_index": shard_index,
        "item_index_start": start,
        "item_index_stop_exclusive": stop,
        "item_codepoints": [str(item["codepoint"]) for item in shard_items],
        "retry_policy": config["acquisition"]["incomplete_stage_policy"],
    }
    atlas._write_json(stage / "execution_intent.json", intent)
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    width = int(_model_spec(role)["expected_model_dim"])
    activations = np.empty(
        (len(shard_items), 3, 2, 4, 2, width), dtype=np.float32
    )
    all_records = _records(roster, config)
    records = [
        {**row, "item_offset": int(row["item_offset"]) - start}
        for row in all_records
        if start <= int(row["item_offset"]) < stop
    ]
    atlas._require(
        int(config["acquisition"]["batch_size_unique_sequences"]) == 1,
        "T10 batch size must remain one",
    )
    pad_id = tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 0
    observations: list[dict[str, Any]] = []
    raw_capture: list[Any] = []

    def hook(_module: Any, _inputs: Any, value: Any) -> None:
        raw_capture.append(_raw_tensor(value))

    handle = last_block.register_forward_hook(hook)
    forward_calls = 0
    endpoint_delta_max_abs: float | None = None
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    try:
        for row in records:
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
            atlas._require(len(raw_capture) == 1, "Last-block hook count mismatch")
            primary = output.hidden_states[-1]
            raw = raw_capture[0]
            atlas._require(primary.shape == raw.shape, "Endpoint shape mismatch")
            atlas._require(
                int(primary.shape[-1]) == width,
                "Endpoint width mismatch",
            )
            selected = torch.stack((primary, raw), dim=2)
            position_tensor = torch.tensor([positions], dtype=torch.long, device="cuda")
            batch_tensor = torch.arange(1, device="cuda")[:, None]
            captured = selected[batch_tensor, position_tensor].float().cpu().numpy()[0]
            atlas._require(captured.shape == (4, 2, width), "Captured endpoint shape mismatch")
            atlas._require(bool(np.isfinite(captured).all()), "Nonfinite activation")
            if endpoint_delta_max_abs is None:
                endpoint_delta_max_abs = float(
                    torch.max(torch.abs(primary.float() - raw.float())).item()
                )
            local_index = int(row["item_offset"])
            activations[
                local_index,
                int(row["view_index"]),
                int(row["carrier_index"]),
            ] = captured
            item = shard_items[local_index]
            observations.append(
                {
                    "item_index": start + local_index,
                    "source_index": int(item["source_index"]),
                    "codepoint": str(item["codepoint"]),
                    "glyph": str(item["glyph"]),
                    "name": str(item["name"]),
                    "view": str(row["view"]),
                    "view_index": int(row["view_index"]),
                    "carrier": str(row["carrier"]),
                    "carrier_index": int(row["carrier_index"]),
                    "raw_token_ids": [int(value) for value in row["raw_ids"]],
                    "input_token_ids": ids,
                    "readout_positions": positions,
                    "activation_rms_by_distance_endpoint": np.sqrt(
                        np.mean(np.square(captured, dtype=np.float64), axis=-1)
                    ).tolist(),
                    "forward_latency_ms": elapsed_ms,
                }
            )
            forward_calls += 1
            del output, primary, raw, selected, captured
            del input_ids, attention_mask, position_tensor, batch_tensor
    finally:
        handle.remove()
    atlas._require(bool(np.isfinite(activations).all()), "Shard activation is nonfinite")
    np.save(stage / "activations.npy", activations, allow_pickle=False)
    atlas._write_jsonl(stage / "observations.jsonl", observations)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
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
        "carrier_order": carriers,
        "distance_order": distances,
        "endpoint_order": list(ENDPOINT_ORDER),
        "unique_input_sequences": len(records),
        "model_forward_calls": forward_calls,
        "readout_vectors": int(np.prod(activations.shape[:-1])),
        "endpoint_delta_first_forward_max_abs": endpoint_delta_max_abs,
        "fused_distance_readout": True,
        "batch_size_unique_sequences": 1,
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
        "peak_cuda_memory_bytes": int(torch.cuda.max_memory_allocated()),
        "model": model_receipt,
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "outputs": {
            "execution_intent.json": atlas._sha256(stage / "execution_intent.json"),
            "activations.npy": atlas._sha256(stage / "activations.npy"),
            "observations.jsonl": atlas._sha256(stage / "observations.jsonl"),
        },
        "intervention_calls": 0,
        "generation_calls": 0,
        "scientific_decision_authorized": False,
    }
    atlas._write_json(stage / "shard_receipt.json", receipt)
    atlas._write_ledger(
        stage,
        ("execution_intent.json", "activations.npy", "observations.jsonl", "shard_receipt.json"),
    )
    stage.rename(final)
    return receipt


def validate_shard(directory: Path) -> dict[str, Any]:
    config = _config()
    names = ("execution_intent.json", "activations.npy", "observations.jsonl", "shard_receipt.json", "SHA256SUMS")
    for name in names:
        atlas._require((directory / name).is_file(), f"Missing shard file: {name}")
    receipt = atlas._read_json(directory / "shard_receipt.json")
    role = str(receipt["model_role"])
    atlas._require(role in model_roles(), "Shard role mismatch")
    atlas._require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "Shard receipt mismatch")
    for name, expected in receipt["outputs"].items():
        atlas._require(atlas._sha256(directory / name) == expected, f"Shard hash mismatch: {name}")
    index = int(receipt["shard_index"])
    size = int(config["acquisition"]["item_shard_size"])
    expected_items = items()[index * size : (index + 1) * size]
    atlas._require(receipt["item_codepoints"] == [str(item["codepoint"]) for item in expected_items], "Shard population changed")
    array = np.load(directory / "activations.npy", mmap_mode="r", allow_pickle=False)
    expected_shape = (len(expected_items), 3, 2, 4, 2, int(_model_spec(role)["expected_model_dim"]))
    atlas._require(tuple(array.shape) == expected_shape, "Shard activation shape mismatch")
    atlas._require(str(array.dtype) == "float32", "Shard activation dtype mismatch")
    atlas._require(bool(np.isfinite(np.asarray(array)).all()), "Shard is nonfinite")
    expected_forwards = len(expected_items) * 3 * 2
    atlas._require(int(receipt["model_forward_calls"]) == expected_forwards, "Shard forward count mismatch")
    return {"status": "pass", "model_role": role, "shard_index": index, "item_count": len(expected_items)}


def run_shards(role: str, model_path: Path, run_root: Path, shard_start: int, shard_stop: int | None) -> dict[str, Any]:
    audit_freeze()
    config = _config()
    _validate_runtime(config)
    expected = int(config["acquisition"]["expected_shards_per_model"])
    stop = expected if shard_stop is None else shard_stop
    atlas._require(0 <= shard_start < stop <= expected, "Invalid shard range")
    run_root.mkdir(parents=True, exist_ok=True)
    atlas._require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete shard stage requires manual adjudication")
    atlas._require(not (run_root / "run_receipt.json").exists(), "Run already finalized")
    lock = run_root / ".writer.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise atlas.AtlasError("Run root already has a writer") from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
    os.close(descriptor)
    events: list[dict[str, Any]] = []
    model = None
    status = "fail"
    try:
        pending = [index for index in range(shard_start, stop) if not (run_root / f"shard_{index:04d}").exists()]
        for index in range(shard_start, stop):
            path = run_root / f"shard_{index:04d}"
            if path.exists():
                validate_shard(path)
        if not pending:
            status = "pass"
            return {"status": status, "message": "requested shards already complete", "events": []}
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before model load: {foreign}")
        torch, tokenizer, model, last_block, model_receipt, roster = _load_model(role, model_path)
        for index in pending:
            foreign = atlas._foreign_gpu_pids()
            if foreign:
                raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before shard {index}: {foreign}")
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
            )
            events.append({key: receipt[key] for key in ("shard_index", "item_count", "model_forward_calls", "elapsed_ms")})
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
            run_root / f"session_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}.json",
            {
                "schema_version": 1,
                "protocol_id": PROTOCOL_ID,
                "model_role": role,
                "status": status,
                "requested_shard_start": shard_start,
                "requested_shard_stop_exclusive": stop,
                "events": events,
            },
        )
    return {"status": status, "events": events}


def finalize_run(role: str, run_root: Path) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    atlas._require(not list(run_root.glob(".shard_*.partial-*")), "Incomplete shard stage blocks finalization")
    atlas._require(not (run_root / "run_receipt.json").exists(), "Run already finalized")
    receipts: list[dict[str, Any]] = []
    ledgers: dict[str, str] = {}
    for index in range(int(config["acquisition"]["expected_shards_per_model"])):
        directory = run_root / f"shard_{index:04d}"
        result = validate_shard(directory)
        atlas._require(result["model_role"] == role, "Run contains another model role")
        receipt = atlas._read_json(directory / "shard_receipt.json")
        receipts.append(receipt)
        ledgers[directory.name] = atlas._sha256(directory / "SHA256SUMS")
    item_count = sum(int(row["item_count"]) for row in receipts)
    forward_calls = sum(int(row["model_forward_calls"]) for row in receipts)
    vectors = sum(int(row["readout_vectors"]) for row in receipts)
    atlas._require(item_count == len(items()), "Final item count mismatch")
    atlas._require(forward_calls == int(config["acquisition"]["expected_model_forward_calls_per_model"]), "Final forward count mismatch")
    atlas._require(vectors == int(config["acquisition"]["expected_readout_vectors_per_model"]), "Final vector count mismatch")
    model_receipts = {json.dumps(row["model"], sort_keys=True) for row in receipts}
    atlas._require(len(model_receipts) == 1, "Model receipt changed across shards")
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "item_count": item_count,
        "unique_input_sequences": forward_calls,
        "model_forward_calls": forward_calls,
        "readout_vectors": vectors,
        "shard_count": len(receipts),
        "shard_ledger_sha256": ledgers,
        "activation_dtype": "float32",
        "axis_order": config["acquisition"]["activation_axis_order"],
        "view_order": list(VIEW_ORDER),
        "carrier_order": config["input"]["carrier_order"],
        "distance_order": config["input"]["distance_order"],
        "endpoint_order": list(ENDPOINT_ORDER),
        "model": receipts[0]["model"],
        "peak_cuda_memory_bytes": max(int(row["peak_cuda_memory_bytes"]) for row in receipts),
        "elapsed_ms": sum(float(row["elapsed_ms"]) for row in receipts),
        "acquisition_status": "complete_summary_pending",
        "intervention_calls": 0,
        "generation_calls": 0,
        "raw_activations_committed_to_git": False,
    }
    atlas._write_json(run_root / "run_receipt.json", receipt)
    atlas._write_json(run_root / "SHARD_INDEX.json", {"protocol_id": PROTOCOL_ID, "model_role": role, "shards": ledgers})
    atlas._write_ledger(run_root, ("run_receipt.json", "SHARD_INDEX.json"))
    return receipt


def validate_run(directory: Path) -> dict[str, Any]:
    for name in ("run_receipt.json", "SHARD_INDEX.json", "SHA256SUMS"):
        atlas._require((directory / name).is_file(), f"Missing run file: {name}")
    receipt = atlas._read_json(directory / "run_receipt.json")
    role = str(receipt["model_role"])
    atlas._require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "Run receipt mismatch")
    atlas._require(receipt.get("freeze_manifest_sha256") == audit_freeze()["manifest_sha256"], "Run freeze mismatch")
    for index in range(int(_config()["acquisition"]["expected_shards_per_model"])):
        result = validate_shard(directory / f"shard_{index:04d}")
        atlas._require(result["model_role"] == role, "Run role mismatch")
    return {"status": "pass", "model_role": role, "receipt": receipt}


def _pair_metrics(torch: Any, left: Any, right: Any) -> tuple[dict[str, float], np.ndarray, np.ndarray]:
    similarity = left @ right.T
    count = int(similarity.shape[0])
    order = torch.arange(count, device=similarity.device)
    diagonal = torch.diagonal(similarity)
    forward = similarity.argmax(dim=1)
    reverse = similarity.argmax(dim=0)
    ranks_forward = 1 + (similarity > diagonal[:, None]).sum(dim=1)
    ranks_reverse = 1 + (similarity > diagonal[None, :]).sum(dim=0)
    off_diagonal = (similarity.sum() - diagonal.sum()) / max(1, count * (count - 1))
    return (
        {
            "paired_cosine_mean": float(diagonal.mean().item()),
            "off_diagonal_cosine_mean": float(off_diagonal.item()),
            "paired_minus_off_diagonal_margin": float((diagonal.mean() - off_diagonal).item()),
            "top1_accuracy_forward": float((forward == order).float().mean().item()),
            "top1_accuracy_reverse": float((reverse == order).float().mean().item()),
            "mean_reciprocal_rank_forward": float((1.0 / ranks_forward.float()).mean().item()),
            "mean_reciprocal_rank_reverse": float((1.0 / ranks_reverse.float()).mean().item()),
        },
        forward.detach().cpu().numpy(),
        reverse.detach().cpu().numpy(),
    )


def _cell_metrics(torch: Any, values: np.ndarray, device: str) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    tensor = torch.from_numpy(np.asarray(values, dtype=np.float32)).to(device)
    centered = tensor - tensor.mean(dim=1, keepdim=True)
    normalized = torch.nn.functional.normalize(centered, p=2, dim=-1, eps=1e-12)
    grams = [centered[index] @ centered[index].T for index in range(3)]
    pairs: dict[str, Any] = {}
    predictions: dict[str, np.ndarray] = {}
    for name, left, right in PAIR_ORDER:
        metrics, forward, _reverse = _pair_metrics(torch, normalized[left], normalized[right])
        denominator = torch.sqrt(torch.sum(grams[left].square()) * torch.sum(grams[right].square()))
        metrics["centered_linear_cka"] = float((torch.sum(grams[left] * grams[right]) / torch.clamp(denominator, min=1e-30)).item())
        pairs[name] = metrics
        predictions[name] = forward
    return {"pairs": pairs, "glyph_name_minus_glyph_codepoint": {key: float(pairs["glyph_name"][key] - pairs["glyph_codepoint"][key]) for key in pairs["glyph_name"]}}, predictions["glyph_name"], predictions["glyph_codepoint"]


def summarize_model(run_root: Path, output: Path, device: str) -> dict[str, Any]:
    import torch

    validated = validate_run(run_root)
    role = str(validated["model_role"])
    if device == "cuda":
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before summary: {foreign}")
    token_receipt = atlas._read_json(_receipt_path(role))["tokenizer"]
    eligible = [int(value) for value in token_receipt["exact_triple_strata"]["eligible_global_indices"]]
    arrays = [
        np.load(run_root / f"shard_{index:04d}" / "activations.npy", mmap_mode="r", allow_pickle=False)
        for index in range(int(_config()["acquisition"]["expected_shards_per_model"]))
    ]
    config = _config()
    metrics_rows: list[dict[str, Any]] = []
    prediction_arrays: dict[str, np.ndarray] = {}
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    for endpoint_index, endpoint in enumerate(ENDPOINT_ORDER):
        full_name: list[np.ndarray] = []
        full_codepoint: list[np.ndarray] = []
        matched_name: list[np.ndarray] = []
        matched_codepoint: list[np.ndarray] = []
        for carrier_index, carrier in enumerate(carriers):
            for distance_index, distance in enumerate(distances):
                all_values = np.concatenate(
                    [np.asarray(array[:, :, carrier_index, distance_index, endpoint_index, :]) for array in arrays],
                    axis=0,
                )
                values = np.transpose(all_values, (1, 0, 2))
                full_metrics, name_prediction, codepoint_prediction = _cell_metrics(torch, values, device)
                matched_values = values[:, eligible, :]
                matched_metrics, matched_name_prediction, matched_codepoint_prediction = _cell_metrics(torch, matched_values, device)
                full_name.append(name_prediction)
                full_codepoint.append(codepoint_prediction)
                matched_name.append(matched_name_prediction)
                matched_codepoint.append(matched_codepoint_prediction)
                metrics_rows.append(
                    {
                        "model_role": role,
                        "endpoint": endpoint,
                        "endpoint_decision_authorized": endpoint == ENDPOINT_ORDER[0],
                        "carrier": carrier,
                        "carrier_index": carrier_index,
                        "distance": distance,
                        "distance_index": distance_index,
                        "unrestricted": {"item_count": len(items()), **full_metrics},
                        "tokenization_matched": {"item_count": len(eligible), **matched_metrics},
                    }
                )
                del all_values, values, matched_values
        prediction_arrays[f"{endpoint}__unrestricted__name"] = np.stack(full_name)
        prediction_arrays[f"{endpoint}__unrestricted__codepoint"] = np.stack(full_codepoint)
        prediction_arrays[f"{endpoint}__matched__name"] = np.stack(matched_name)
        prediction_arrays[f"{endpoint}__matched__codepoint"] = np.stack(matched_codepoint)
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    atlas._require(not output.exists(), f"Summary output exists: {output}")
    stage.mkdir(parents=True)
    np.savez_compressed(stage / "predictions.npz", **prediction_arrays)
    atlas._write_jsonl(stage / "cell_metrics.jsonl", metrics_rows)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "model_role": role,
        "analysis_role": "per_model_fixed_endpoint_prediction_summary",
        "source_run_receipt_sha256": atlas._sha256(run_root / "run_receipt.json"),
        "freeze_manifest_sha256": audit_freeze()["manifest_sha256"],
        "item_count": len(items()),
        "matched_item_count": len(eligible),
        "cell_count_per_endpoint": 8,
        "endpoint_order": list(ENDPOINT_ORDER),
        "summary_device": device,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "secondary_endpoint_decision_authorized": False,
        "outputs": {
            "predictions.npz": atlas._sha256(stage / "predictions.npz"),
            "cell_metrics.jsonl": atlas._sha256(stage / "cell_metrics.jsonl"),
        },
    }
    atlas._write_json(stage / "summary_receipt.json", receipt)
    atlas._write_ledger(stage, ("predictions.npz", "cell_metrics.jsonl", "summary_receipt.json"))
    stage.rename(output)
    if device == "cuda":
        torch.cuda.empty_cache()
    return receipt


def validate_summary(directory: Path) -> dict[str, Any]:
    for name in ("predictions.npz", "cell_metrics.jsonl", "summary_receipt.json", "SHA256SUMS"):
        atlas._require((directory / name).is_file(), f"Missing summary file: {name}")
    receipt = atlas._read_json(directory / "summary_receipt.json")
    role = str(receipt["model_role"])
    atlas._require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "Summary receipt mismatch")
    for name, expected in receipt["outputs"].items():
        atlas._require(atlas._sha256(directory / name) == expected, f"Summary output changed: {name}")
    with np.load(directory / "predictions.npz", allow_pickle=False) as values:
        for endpoint in ENDPOINT_ORDER:
            for component, count in (("unrestricted", len(items())), ("matched", int(receipt["matched_item_count"]))):
                for target in ("name", "codepoint"):
                    key = f"{endpoint}__{component}__{target}"
                    atlas._require(values[key].shape == (8, count), f"Prediction shape changed: {key}")
    return {"status": "pass", "model_role": role, "receipt": receipt}


def stratified_permutation(
    rng: np.random.Generator,
    item_count: int,
    strata: Sequence[Sequence[int]],
) -> np.ndarray:
    order = np.arange(item_count, dtype=np.int64)
    flattened = sorted(int(value) for group in strata for value in group)
    atlas._require(flattened == list(range(item_count)), "Matched strata do not partition items")
    atlas._require(all(len(group) >= 2 for group in strata), "Matched stratum is singleton")
    permutation = order.copy()
    for group in strata:
        indices = np.asarray(group, dtype=np.int64)
        permutation[indices] = rng.permutation(indices)
    return permutation


def randomization_test(
    name_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
    *,
    draws: int,
    seed: int,
    practical_minimum: float,
    strata: Sequence[Sequence[int]] | None,
) -> dict[str, Any]:
    atlas._require(name_predictions.shape == codepoint_predictions.shape, "Prediction shape mismatch")
    atlas._require(name_predictions.ndim == 2 and name_predictions.shape[0] == 8, "Prediction cell roster mismatch")
    item_count = int(name_predictions.shape[1])
    order = np.arange(item_count, dtype=np.int64)
    name_top1 = np.mean(name_predictions == order[None, :], axis=1)
    codepoint_top1 = np.mean(codepoint_predictions == order[None, :], axis=1)
    contrasts = name_top1 - codepoint_top1
    observed = float(np.min(contrasts))
    rng = np.random.default_rng(seed)
    null_values = np.empty(draws, dtype=np.float64)
    exceedances = 0
    if strata is not None:
        stratified_permutation(np.random.default_rng(0), item_count, strata)
    for draw in range(draws):
        if strata is None:
            permutation = rng.permutation(item_count)
        else:
            permutation = stratified_permutation(rng, item_count, strata)
        permuted_name = np.mean(name_predictions == permutation[None, :], axis=1)
        statistic = float(np.min(permuted_name - codepoint_top1))
        null_values[draw] = statistic
        exceedances += int(statistic >= observed)
    return {
        "item_count": item_count,
        "cell_count": 8,
        "name_top1_by_cell": name_top1.tolist(),
        "codepoint_top1_by_cell": codepoint_top1.tolist(),
        "contrast_by_cell": contrasts.tolist(),
        "observed_minimum_cell_contrast": observed,
        "observed_equal_cell_mean_contrast": float(np.mean(contrasts)),
        "practical_minimum": practical_minimum,
        "practical_pass": bool(observed >= practical_minimum),
        "randomization_draws": draws,
        "randomization_seed": seed,
        "exceedances": exceedances,
        "p_value": float((1 + exceedances) / (draws + 1)),
        "null_statistic_quantiles": {
            str(q): float(np.quantile(null_values, q)) for q in (0.0, 0.5, 0.95, 0.99, 1.0)
        },
    }


def holm_adjust(raw: Mapping[str, float], alpha: float) -> dict[str, dict[str, Any]]:
    ordered = sorted(raw, key=lambda key: (float(raw[key]), key))
    count = len(ordered)
    running = 0.0
    adjusted: dict[str, float] = {}
    rejected_prefix = True
    rejected: dict[str, bool] = {}
    for index, key in enumerate(ordered):
        value = min(1.0, (count - index) * float(raw[key]))
        running = max(running, value)
        adjusted[key] = running
        threshold = alpha / (count - index)
        this_reject = rejected_prefix and float(raw[key]) <= threshold
        rejected[key] = this_reject
        rejected_prefix = this_reject
    return {
        key: {
            "raw_p": float(raw[key]),
            "adjusted_p": float(adjusted[key]),
            "reject": bool(rejected[key]),
        }
        for key in raw
    }


def partial_conjunction(core_p: Mapping[str, float], r: int) -> dict[str, Any]:
    ordered = sorted((float(value), key) for key, value in core_p.items())
    m = len(ordered)
    atlas._require(1 <= r <= m, "Invalid partial-conjunction rank")
    rth = ordered[r - 1]
    p_value = min(1.0, (m - r + 1) * rth[0])
    return {
        "m": m,
        "r": r,
        "ordered_model_iut_p_values": [
            {"model_role": key, "p_value": value} for value, key in ordered
        ],
        "rth_smallest_model_role": rth[1],
        "rth_smallest_model_iut_p": rth[0],
        "multiplier": m - r + 1,
        "p_value": p_value,
    }


def _secondary_observed(predictions: Mapping[str, np.ndarray], role: str) -> dict[str, Any]:
    receipt = atlas._read_json(_receipt_path(role))["tokenizer"]
    results: dict[str, Any] = {}
    for component in ("unrestricted", "matched"):
        name = predictions[f"{ENDPOINT_ORDER[1]}__{component}__name"]
        codepoint = predictions[f"{ENDPOINT_ORDER[1]}__{component}__codepoint"]
        order = np.arange(name.shape[1], dtype=np.int64)
        contrasts = np.mean(name == order[None, :], axis=1) - np.mean(
            codepoint == order[None, :], axis=1
        )
        results[component] = {
            "item_count": int(name.shape[1]),
            "contrast_by_cell": contrasts.tolist(),
            "observed_minimum_cell_contrast": float(np.min(contrasts)),
            "observed_equal_cell_mean_contrast": float(np.mean(contrasts)),
            "decision_authorized": False,
        }
    results["matched_eligible_item_count"] = int(
        receipt["exact_triple_strata"]["eligible_item_count"]
    )
    return results


def analyze_summaries(summary_directories: Mapping[str, Path], output: Path) -> dict[str, Any]:
    config = _config()
    freeze = audit_freeze()
    atlas._require(tuple(summary_directories) == model_roles(), "Summary role order mismatch")
    endpoint = config["model_primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    floor = float(endpoint["practical_minimum"])
    seed_base = int(endpoint["seed_base"])
    model_results: dict[str, Any] = {}
    summary_hashes: dict[str, str] = {}
    for role_index, role in enumerate(model_roles()):
        directory = summary_directories[role]
        validated = validate_summary(directory)
        atlas._require(validated["model_role"] == role, "Summary role binding mismatch")
        summary_hashes[role] = atlas._sha256(directory / "summary_receipt.json")
        token_receipt = atlas._read_json(_receipt_path(role))["tokenizer"]
        strata = token_receipt["exact_triple_strata"]["eligible_local_strata"]
        with np.load(directory / "predictions.npz", allow_pickle=False) as stored:
            predictions = {key: np.asarray(stored[key]) for key in stored.files}
        primary_endpoint = ENDPOINT_ORDER[0]
        unrestricted = randomization_test(
            predictions[f"{primary_endpoint}__unrestricted__name"],
            predictions[f"{primary_endpoint}__unrestricted__codepoint"],
            draws=draws,
            seed=seed_base + role_index * 10 + 1,
            practical_minimum=floor,
            strata=None,
        )
        matched = randomization_test(
            predictions[f"{primary_endpoint}__matched__name"],
            predictions[f"{primary_endpoint}__matched__codepoint"],
            draws=draws,
            seed=seed_base + role_index * 10 + 2,
            practical_minimum=floor,
            strata=strata,
        )
        iut_p = max(float(unrestricted["p_value"]), float(matched["p_value"]))
        practical_pass = bool(unrestricted["practical_pass"] and matched["practical_pass"])
        model_results[role] = {
            "model_role": role,
            "selection_role": _model_spec(role)["selection_role"],
            "unrestricted_component": unrestricted,
            "tokenization_matched_component": matched,
            "intersection_union_p_value": iut_p,
            "practical_pass": practical_pass,
            "raw_model_cell_pass": bool(iut_p <= float(endpoint["alpha"]) and practical_pass),
            "secondary_raw_last_block": _secondary_observed(predictions, role),
        }
    raw_iut = {role: float(model_results[role]["intersection_union_p_value"]) for role in model_roles()}
    holm = holm_adjust(raw_iut, float(config["bounded_model_cell_family"]["familywise_alpha"]))
    for role in model_roles():
        model_results[role]["holm_adjusted_p"] = holm[role]["adjusted_p"]
        model_results[role]["holm_reject"] = holm[role]["reject"]
        model_results[role]["bounded_model_cell_claim_pass"] = bool(
            holm[role]["reject"] and model_results[role]["practical_pass"]
        )
    core = [str(value) for value in config["cross_model_primary"]["core_order"]]
    partial = partial_conjunction(
        {role: raw_iut[role] for role in core},
        int(config["cross_model_primary"]["r"]),
    )
    core_practical_count = sum(int(model_results[role]["practical_pass"]) for role in core)
    statistical_pass = bool(partial["p_value"] <= float(config["cross_model_primary"]["alpha"]))
    practical_pass = bool(core_practical_count >= int(config["cross_model_primary"]["r"]))
    positive = bool(statistical_pass and practical_pass)
    pattern = (
        "at_least_three_of_four_core_cells_replicate"
        if positive
        else "cross_model_replication_not_established"
    )
    cross_primary = {
        **partial,
        "core_order": core,
        "core_practical_pass_count": core_practical_count,
        "statistical_pass": statistical_pass,
        "practical_pass": practical_pass,
        "positive": positive,
        "outcome_pattern": pattern,
        "authorized_wording": (
            config["cross_model_primary"]["authorized_positive_wording"]
            if positive
            else "cross_model_replication_not_established_under_frozen_rule"
        ),
    }
    t9_primary = atlas._read_json(_root() / str(config["source_bindings"]["t9_primary_result"]))
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    atlas._require(not output.exists(), f"Analysis output exists: {output}")
    stage.mkdir(parents=True)
    atlas._write_json(stage / "cross_model_primary_result.json", cross_primary)
    atlas._write_json(stage / "model_cell_results.json", model_results)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": "prospectively_frozen_cross_model_tokenizer_cell_replication",
        "claim_boundary": config["claim_boundary"],
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "input_summary_receipt_sha256": summary_hashes,
        "model_order": list(model_roles()),
        "core_order": core,
        "cross_model_primary": cross_primary,
        "model_cell_results": model_results,
        "holm_family_size": len(model_roles()),
        "randomization_draws_per_model_component": draws,
        "known_t9_descriptive_anchor": {
            "model": "mistralai/Mistral-7B-v0.3",
            "observed_minimum_cell_contrast": t9_primary["observed_minimum_cell_contrast"],
            "p_value": t9_primary["p_value"],
            "inferential_pooling": False,
        },
        "outcome_pattern": pattern,
        "outcome_pattern_definition": config["outcome_registry"][pattern],
        "model_forward_calls": 0,
        "total_acquisition_model_forward_calls": int(config["acquisition"]["expected_total_model_forward_calls"]),
        "intervention_calls": 0,
        "generation_calls": 0,
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "model_general_claim_authorized": False,
        "independent_replication_claim_authorized": False,
        "phase_i_gate_closed": False,
    }
    atlas._write_json(stage / "analysis_receipt.json", receipt)
    lines = [
        "# Semantic atlas cross-model replication v0 result\n\n",
        f"Outcome: `{pattern}`.\n\n",
        "| Model cell | Unrestricted p | Matched p | IUT p | Holm p | Practical | Bounded cell |\n",
        "|---|---:|---:|---:|---:|---|---|\n",
    ]
    for role in model_roles():
        row = model_results[role]
        lines.append(
            f"| `{role}` | {row['unrestricted_component']['p_value']:.7f} | "
            f"{row['tokenization_matched_component']['p_value']:.7f} | "
            f"{row['intersection_union_p_value']:.7f} | {row['holm_adjusted_p']:.7f} | "
            f"{str(row['practical_pass']).lower()} | {str(row['bounded_model_cell_claim_pass']).lower()} |\n"
        )
    lines.extend(
        [
            "\n",
            f"Core partial-conjunction p: `{partial['p_value']:.7f}`; practical core passes: "
            f"`{core_practical_count}/4`.\n\n",
            "This result concerns frozen model/tokenizer cells and official Unicode item-name "
            "retrieval. It does not establish emoji semantics, causality, independence, a scale "
            "law, or model generality.\n",
        ]
    )
    (stage / "report.md").write_text("".join(lines), encoding="utf-8")
    atlas._write_ledger(
        stage,
        ("cross_model_primary_result.json", "model_cell_results.json", "analysis_receipt.json", "report.md"),
    )
    stage.rename(output)
    return receipt


def validate_analysis(directory: Path) -> dict[str, Any]:
    names = ("cross_model_primary_result.json", "model_cell_results.json", "analysis_receipt.json", "report.md", "SHA256SUMS")
    for name in names:
        atlas._require((directory / name).is_file(), f"Missing analysis file: {name}")
    receipt = atlas._read_json(directory / "analysis_receipt.json")
    atlas._require(receipt.get("protocol_id") == PROTOCOL_ID and receipt.get("status") == "pass", "Analysis receipt mismatch")
    atlas._require(tuple(receipt["model_order"]) == model_roles(), "Analysis model order changed")
    atlas._require(receipt.get("secondary_endpoint_decision_authorized", False) is False, "Secondary endpoint became authoritative")
    atlas._require(receipt.get("semantic_claim_authorized") is False, "Semantic claim was authorized")
    atlas._require(receipt.get("model_general_claim_authorized") is False, "Model-general claim was authorized")
    return {"status": "pass", "outcome_pattern": receipt["outcome_pattern"], "cross_model_primary": receipt["cross_model_primary"]}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design")
    endpoint = sub.add_parser("endpoint-audit")
    endpoint.add_argument("--output", type=Path, default=_root() / ENDPOINT_AUDIT_PATH)
    tokenizer = sub.add_parser("tokenizer-preflight")
    tokenizer.add_argument("--model-label", choices=model_roles(), required=True)
    tokenizer.add_argument("--model-path", type=Path, required=True)
    tokenizer.add_argument("--output", type=Path, required=True)
    assemble = sub.add_parser("assemble-preflight")
    assemble.add_argument("--output", type=Path, default=_root() / PREFLIGHT_PATH)
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=_root() / FREEZE_PATH)
    sub.add_parser("audit-freeze")
    run = sub.add_parser("run")
    run.add_argument("--model-label", choices=model_roles(), required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--shard-start", type=int, default=0)
    run.add_argument("--shard-stop", type=int)
    validate_one = sub.add_parser("validate-shard")
    validate_one.add_argument("--shard", type=Path, required=True)
    finalize = sub.add_parser("finalize")
    finalize.add_argument("--model-label", choices=model_roles(), required=True)
    finalize.add_argument("--run", type=Path, required=True)
    validate_complete = sub.add_parser("validate-run")
    validate_complete.add_argument("--run", type=Path, required=True)
    summary = sub.add_parser("summarize")
    summary.add_argument("--run", type=Path, required=True)
    summary.add_argument("--output", type=Path, required=True)
    summary.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    validate_derived = sub.add_parser("validate-summary")
    validate_derived.add_argument("--summary", type=Path, required=True)
    analyze = sub.add_parser("analyze")
    for role in model_roles():
        analyze.add_argument(f"--{role.replace('_', '-')}-summary", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    validate_joint = sub.add_parser("validate-analysis")
    validate_joint.add_argument("--analysis", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "endpoint-audit":
        result = endpoint_semantics_audit(args.output)
    elif args.command == "tokenizer-preflight":
        result = tokenizer_preflight(args.model_label, args.model_path, args.output)
    elif args.command == "assemble-preflight":
        result = assemble_preflight(args.output)
    elif args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run":
        result = run_shards(args.model_label, args.model_path, args.output, args.shard_start, args.shard_stop)
    elif args.command == "validate-shard":
        result = validate_shard(args.shard)
    elif args.command == "finalize":
        result = finalize_run(args.model_label, args.run)
    elif args.command == "validate-run":
        result = validate_run(args.run)
    elif args.command == "summarize":
        result = summarize_model(args.run, args.output, args.device)
    elif args.command == "validate-summary":
        result = validate_summary(args.summary)
    elif args.command == "analyze":
        directories = {
            role: getattr(args, f"{role}_summary") for role in model_roles()
        }
        result = analyze_summaries(directories, args.output)
    elif args.command == "validate-analysis":
        result = validate_analysis(args.analysis)
    else:  # pragma: no cover
        raise atlas.AtlasError(f"Unknown command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
