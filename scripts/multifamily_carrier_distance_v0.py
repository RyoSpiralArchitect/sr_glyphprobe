#!/usr/bin/env python3
"""Run the frozen multifamily repeated-carrier distance v0 study.

The protocol keeps each full input and current carrier-token identity fixed while
reading observational ``resid_post`` geometry at distances 1, 2, 4, and 8 after
the raw glyph. Slot-label permutations are synchronized across every carrier,
distance, and depth. No intervention or generation is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import shutil
import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_common_suffix_carryover_v0 as t4  # noqa: E402


frozen = t4.frozen
base = t4.base
PROTOCOL_ID = "glyphprobe-multifamily-carrier-distance-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/multifamily_carrier_distance_v0.json")
CONFIG_PATH = Path("configs/multifamily_carrier_distance_v0.yaml")
MODEL_ROLES = ("gemma2_2b_4bit", "llama32_3b_bf16", "olmo3_7b_bf16")
RUN_FILES = ("activations.npz", "observations.jsonl", "run_receipt.json")
FAILED_RUN_FILES = ("run_receipt.json",)
ANALYSIS_FILES = ("carrier_distance_layer_statistics.jsonl", "analysis_receipt.json", "report.md")


class PublishedRunFailure(RuntimeError):
    """Raised after an atomic failed-run receipt has been published."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_authority(
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    manifest = base._read_json(root / MANIFEST_PATH, "freeze manifest")
    base._require(manifest.get("schema_version") == SCHEMA_VERSION, "Manifest schema mismatch")
    base._require(manifest.get("protocol_id") == PROTOCOL_ID, "Manifest protocol mismatch")
    assets = manifest.get("frozen_assets")
    base._require(isinstance(assets, dict) and bool(assets), "Missing frozen asset ledger")
    verified: dict[str, str] = {}
    for relative, expected in sorted(assets.items()):
        path = root / str(relative)
        base._require(path.is_file(), f"Missing frozen asset: {relative}")
        observed = base._sha256_file(path)
        base._require(observed == expected, f"Frozen asset SHA-256 mismatch: {relative}")
        verified[str(relative)] = observed
    config = base._read_yaml(root / CONFIG_PATH, "frozen config")
    base._require(config.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return manifest, config, verified


def audit_freeze(root: Path | None = None) -> dict[str, Any]:
    root = _repo_root() if root is None else root.resolve()
    manifest, config, verified = _load_authority(root)
    implementation = frozen.implementation_receipt()
    expected = manifest.get("implementation")
    base._require(isinstance(expected, dict), "Missing implementation pin")
    base._require(
        implementation.get("source_tree_sha256") == expected.get("source_tree_sha256"),
        "GlyphProbe source-tree SHA-256 mismatch",
    )
    base._require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model role order mismatch")
    base._require(
        list(config["input"]["carrier_order"]) == ["article_a", "pipe"],
        "Carrier order mismatch",
    )
    base._require(
        [int(value) for value in config["input"]["distance_order"]] == [1, 2, 4, 8],
        "Distance order mismatch",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "manifest_sha256": base._sha256_file(root / MANIFEST_PATH),
        "frozen_asset_count": len(verified),
        "frozen_assets": verified,
        "implementation": implementation,
        "model_roles": list(MODEL_ROLES),
        "scientific_confirmation": False,
    }


def _panel(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    return frozen._load_panel(root, config)


def _ordered_sequence_sha256(sequences: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(
        [[int(value) for value in row] for row in sequences],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _shared_prefix_length(sequences: Sequence[Sequence[int]]) -> int:
    if not sequences:
        return 0
    width = min(len(row) for row in sequences)
    count = 0
    for index in range(width):
        if len({int(row[index]) for row in sequences}) != 1:
            break
        count += 1
    return count


def validate_raw_tokenizations(
    raw_tokenizations: Sequence[Any],
    panel_items: Sequence[Mapping[str, Any]],
    model_spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate either a T3 raw contract or Llama's pinned near-factorized roster."""

    contract = model_spec["raw_tokenization_contract"]
    kind = str(contract["kind"])
    if kind != "fixed_sequence_roster":
        return frozen.validate_tokenization_matrix(
            raw_tokenizations,
            panel_items,
            {"tokenization_contract": contract},
        )

    base._require(len(raw_tokenizations) == len(panel_items), "Raw row count mismatch")
    sequences = [tuple(int(value) for value in row.token_ids) for row in raw_tokenizations]
    histogram = Counter(len(row) for row in sequences)
    expected_histogram = {
        int(key): int(value)
        for key, value in contract["expected_item_token_count_histogram"].items()
    }
    base._require(dict(sorted(histogram.items())) == dict(sorted(expected_histogram.items())), "Raw token-count histogram mismatch")
    base._require(
        len(set(sequences)) == int(contract["expected_unique_sequence_count"]),
        "Raw unique-sequence count mismatch",
    )
    shared = _shared_prefix_length(sequences)
    base._require(
        shared >= int(contract["minimum_shared_prefix_across_panel"]),
        "Raw shared-prefix contract failed",
    )
    prefix = int(contract["shared_prefix_token_id"])
    base._require(all(row and row[0] == prefix for row in sequences), "Raw prefix token mismatch")
    observed_sha = _ordered_sequence_sha256(sequences)
    base._require(
        observed_sha == str(contract["ordered_sequence_sha256"]),
        "Raw ordered-sequence SHA-256 mismatch",
    )
    return {
        "kind": kind,
        "observed_item_token_count_histogram": {
            str(key): int(value) for key, value in sorted(histogram.items())
        },
        "unique_sequence_count": len(set(sequences)),
        "minimum_shared_prefix_across_panel": shared,
        "shared_prefix_token_id": prefix,
        "ordered_sequence_sha256": observed_sha,
        "matching_family": contract["matching_family"],
        "token_sequences": [list(row) for row in sequences],
    }


def validate_carrier_tokenizations(
    raw_tokenizations: Sequence[Any],
    carrier_tokenizations: Mapping[str, Sequence[Any]],
    panel_items: Sequence[Mapping[str, Any]],
    model_spec: Mapping[str, Any],
    input_spec: Mapping[str, Any],
    *,
    decoder: Callable[[Sequence[int]], str] | None = None,
) -> dict[str, Any]:
    """Validate raw preservation plus eight identical common carrier tokens."""

    raw_receipt = validate_raw_tokenizations(raw_tokenizations, panel_items, model_spec)
    raw_sequences = [tuple(int(value) for value in row.token_ids) for row in raw_tokenizations]
    carrier_order = [str(value) for value in input_spec["carrier_order"]]
    base._require(tuple(carrier_tokenizations) == tuple(carrier_order), "Carrier role order mismatch")
    expected_ids = {
        str(key): int(value) for key, value in model_spec["carrier_token_ids"].items()
    }
    base._require(set(expected_ids) == set(carrier_order), "Carrier-token roster mismatch")
    distances = [int(value) for value in input_spec["distance_order"]]
    base._require(distances == [1, 2, 4, 8], "Distance roster mismatch")

    carriers: dict[str, dict[str, Any]] = {}
    for carrier_id in carrier_order:
        rows = carrier_tokenizations[carrier_id]
        base._require(len(rows) == len(panel_items), f"Carrier row mismatch: {carrier_id}")
        carrier_spec = input_spec["carriers"][carrier_id]
        unit = str(carrier_spec["unit"])
        repeats = int(carrier_spec["repeats"])
        base._require(repeats == max(distances), "Carrier repeat count must equal maximum distance")
        token_id = expected_ids[carrier_id]
        sequences = [tuple(int(value) for value in row.token_ids) for row in rows]
        expected = [raw + (token_id,) * repeats for raw in raw_sequences]
        base._require(sequences == expected, f"Raw-plus-carrier contract failed: {carrier_id}")
        decoded_exact = None
        if decoder is not None:
            decoded_exact = [
                decoder(sequence) == str(item["glyph"]) + unit * repeats
                for item, sequence in zip(panel_items, sequences, strict=True)
            ]
            base._require(all(decoded_exact), f"Roundtrip contract failed: {carrier_id}")
        positions = [
            [len(raw) + distance - 1 for distance in distances]
            for raw in raw_sequences
        ]
        carriers[carrier_id] = {
            "unit": unit,
            "repeats": repeats,
            "carrier_token_id": token_id,
            "observed_combined_token_counts": sorted({len(row) for row in sequences}),
            "unique_combined_sequence_count": len(set(sequences)),
            "raw_prefix_preserved_count": sum(
                sequence[: len(raw)] == raw
                for raw, sequence in zip(raw_sequences, sequences, strict=True)
            ),
            "roundtrip_exact_count": None if decoded_exact is None else sum(decoded_exact),
            "readout_positions_by_item": positions,
            "token_sequences": [list(row) for row in sequences],
        }
    return {
        "exact_contract": input_spec["exact_contract"],
        "raw": raw_receipt,
        "carrier_order": carrier_order,
        "distance_order": distances,
        "carriers": carriers,
    }


def tokenizer_preflight(model_label: str, model_path: Path) -> dict[str, Any]:
    """Replay the exact tokenizer contract without a model forward."""

    root = _repo_root()
    _, config, _ = _load_authority(root)
    base._require(model_label in MODEL_ROLES, f"Unknown model role: {model_label}")
    model_spec = config["models"][model_label]
    panel_items = _panel(root, config)
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        model_path.resolve(),
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )

    def tokenized(text: str) -> SimpleNamespace:
        ids = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
        return SimpleNamespace(
            token_ids=ids,
            tokens=[str(value) for value in tokenizer.convert_ids_to_tokens(ids)],
        )

    raw = [tokenized(str(item["glyph"])) for item in panel_items]
    carriers = {
        carrier_id: [
            tokenized(
                str(item["glyph"])
                + str(config["input"]["carriers"][carrier_id]["unit"])
                * int(config["input"]["carriers"][carrier_id]["repeats"])
            )
            for item in panel_items
        ]
        for carrier_id in config["input"]["carrier_order"]
    }
    receipt = validate_carrier_tokenizations(
        raw,
        carriers,
        panel_items,
        model_spec,
        config["input"],
        decoder=lambda ids: tokenizer.decode(
            list(ids),
            clean_up_tokenization_spaces=False,
            skip_special_tokens=False,
        ),
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "model_label": model_label,
        "canonical_model_id": model_spec["canonical_model_id"],
        "tokenizer_class": type(tokenizer).__name__,
        "panel_items": len(panel_items),
        "tokenization": receipt,
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "protected_target_files_opened": 0,
        "scientific_result_available": False,
    }


def _decode(backend: Any, ids: Sequence[int]) -> str:
    return str(
        backend.tokenizer.decode(
            list(ids),
            clean_up_tokenization_spaces=False,
            skip_special_tokens=False,
        )
    )


def run_model(model_label: str, model_path: Path, output: Path) -> dict[str, Any]:
    """Run one role-bound carrier-distance model cell and atomically publish it."""

    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    base._require(model_label in MODEL_ROLES, f"Unknown model role: {model_label}")
    model_spec = config["models"][model_label]
    artifact_pin = manifest["model_artifacts"][model_label]
    panel_items = _panel(root, config)
    runtime = base._model_runtime_check(config)
    stage = base._new_stage(output)
    backend: Any = None
    started = time.perf_counter()
    try:
        backend = frozen.MLXBackend(
            frozen.BackendConfig(
                kind="mlx",
                model=str(model_path),
                device=str(config["runtime"]["device"]),
                dtype=str(config["runtime"]["dtype"]),
                local_files_only=bool(config["runtime"]["local_files_only"]),
                trust_remote_code=bool(config["runtime"]["trust_remote_code"]),
                add_special_tokens=bool(config["input"]["add_special_tokens"]),
            )
        )
        backend.load()
        loaded_at = time.perf_counter()
        backend_receipt = backend.model_receipt()
        artifact = backend_receipt.get("model_artifact")
        base._require(isinstance(artifact, dict), "Backend omitted model artifact receipt")
        for field in ("manifest_sha256", "file_count", "total_bytes"):
            base._require(
                artifact.get(field) == artifact_pin.get(field),
                f"Model artifact {field} mismatch",
            )
        expected_type = str(model_spec["expected_model_type"])
        base._require(backend.model_config.get("model_type") == expected_type, "Model type mismatch")
        base._require(backend.num_layers == int(model_spec["expected_num_layers"]), "Layer count mismatch")
        base._require(backend.model_dim == int(model_spec["expected_model_dim"]), "Model width mismatch")
        base._require(
            backend_receipt.get("parameter_count") == int(model_spec["expected_parameter_count"]),
            "Parameter count mismatch",
        )
        base._require(
            backend.resolved_dtype == str(model_spec["expected_resolved_dtype"]),
            "Resolved dtype mismatch",
        )
        quantized = bool(
            backend.model_config.get("quantization")
            or backend.model_config.get("quantization_config")
        )
        base._require(quantized is bool(model_spec["expected_quantized"]), "Quantization flag mismatch")

        fractions = [float(value) for value in config["layers"]["fractions"]]
        layers = base.resolve_layers(backend.num_layers, fractions)
        carrier_order = [str(value) for value in config["input"]["carrier_order"]]
        distances = [int(value) for value in config["input"]["distance_order"]]
        raw_tokenizations = [backend.tokenize(str(item["glyph"])) for item in panel_items]
        carrier_tokenizations = {
            carrier_id: [
                backend.tokenize(
                    str(item["glyph"])
                    + str(config["input"]["carriers"][carrier_id]["unit"])
                    * int(config["input"]["carriers"][carrier_id]["repeats"])
                )
                for item in panel_items
            ]
            for carrier_id in carrier_order
        }
        tokenization_receipt = validate_carrier_tokenizations(
            raw_tokenizations,
            carrier_tokenizations,
            panel_items,
            model_spec,
            config["input"],
            decoder=lambda ids: _decode(backend, ids),
        )

        activation_rows: list[np.ndarray] = []
        observations: list[dict[str, Any]] = []
        for panel_index, item in enumerate(panel_items):
            carrier_rows: list[np.ndarray] = []
            raw_ids = [int(value) for value in raw_tokenizations[panel_index].token_ids]
            for carrier_index, carrier_id in enumerate(carrier_order):
                carrier_spec = config["input"]["carriers"][carrier_id]
                text = (
                    str(item["glyph"])
                    + str(carrier_spec["unit"]) * int(carrier_spec["repeats"])
                )
                tokenized = carrier_tokenizations[carrier_id][panel_index]
                distance_rows: list[np.ndarray] = []
                for distance_index, distance in enumerate(distances):
                    position = len(raw_ids) + distance - 1
                    result = backend.forward(
                        text,
                        capture_layers=layers,
                        site=str(config["input"]["site"]),
                        position=position,
                        return_attentions=bool(config["input"]["return_attentions"]),
                    )
                    base._require(
                        [int(value) for value in result.token_ids]
                        == [int(value) for value in tokenized.token_ids],
                        f"Forward tokenization diverged: {item['id']}/{carrier_id}/{distance}",
                    )
                    base._require(
                        int(result.token_ids[position])
                        == int(model_spec["carrier_token_ids"][carrier_id]),
                        f"Readout token mismatch: {item['id']}/{carrier_id}/{distance}",
                    )
                    base._require(bool(np.isfinite(result.logits).all()), f"Nonfinite logits: {item['id']}")
                    base._require(
                        result.logits.shape == (int(model_spec["expected_vocab_size"]),),
                        f"Vocabulary/logit width mismatch: {item['id']}",
                    )
                    layer_vectors: list[np.ndarray] = []
                    layer_rms: dict[str, float] = {}
                    for layer in layers:
                        vector = np.asarray(result.activations[layer], dtype=np.float32)
                        base._require(
                            vector.shape == (backend.model_dim,),
                            f"Activation width mismatch: {item['id']}",
                        )
                        base._require(bool(np.isfinite(vector).all()), f"Nonfinite activation: {item['id']}")
                        layer_vectors.append(vector)
                        layer_rms[str(layer)] = float(
                            np.sqrt(np.mean(np.square(vector, dtype=np.float64)))
                        )
                    distance_rows.append(np.stack(layer_vectors, axis=0))
                    factors = item["factors"]
                    observations.append(
                        {
                            "panel_index": panel_index,
                            "carrier_index": carrier_index,
                            "distance_index": distance_index,
                            "carrier_id": carrier_id,
                            "distance": distance,
                            "item_id": str(item["id"]),
                            "glyph": str(item["glyph"]),
                            "family": str(factors["family"]),
                            "matched_slot": str(factors["matched_slot"]),
                            "codepoint": str(factors["codepoint"]),
                            "raw_token_ids": raw_ids,
                            "token_ids": [int(value) for value in tokenized.token_ids],
                            "token_pieces": [str(value) for value in tokenized.tokens],
                            "token_count": len(tokenized.token_ids),
                            "readout_position": position,
                            "readout_token_id": int(result.token_ids[position]),
                            "activation_rms_by_layer": layer_rms,
                            "logits_finite": True,
                            "logit_argmax": int(np.argmax(result.logits)),
                            "forward_latency_ms": float(result.latency_ms),
                            "peak_memory_bytes": int(result.peak_memory_bytes or 0),
                        }
                    )
                carrier_rows.append(np.stack(distance_rows, axis=0))
            activation_rows.append(np.stack(carrier_rows, axis=0))

        activations = np.stack(activation_rows, axis=0).astype(np.float32, copy=False)
        np.savez_compressed(
            stage / "activations.npz",
            activations=activations,
            item_ids=np.asarray([str(item["id"]) for item in panel_items], dtype=np.str_),
            carrier_ids=np.asarray(carrier_order, dtype=np.str_),
            distances=np.asarray(distances, dtype=np.int64),
            layers=np.asarray(layers, dtype=np.int64),
        )
        base._write_jsonl(stage / "observations.jsonl", observations)
        data_hashes = {
            name: base._sha256_file(stage / name)
            for name in ("activations.npz", "observations.jsonl")
        }
        run_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "experiment_role": config["experiment_role"],
            "claim_boundary": config["claim_boundary"],
            "model_label": model_label,
            "canonical_model_id": model_spec["canonical_model_id"],
            "model": {
                "model_type": expected_type,
                "num_layers": backend.num_layers,
                "model_dim": backend.model_dim,
                "parameter_count": backend_receipt["parameter_count"],
                "resolved_device": backend.resolved_device,
                "resolved_dtype": backend.resolved_dtype,
                "quantized": quantized,
                "artifact": artifact,
                "backend_receipt": base.scrub_local_paths(backend_receipt, model_path),
            },
            "runtime": runtime,
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "panel": {
                "item_ids": [str(item["id"]) for item in panel_items],
                "family_order": list(config["panel"]["family_order"]),
                "slot_order": list(config["panel"]["slot_order"]),
            },
            "tokenization": tokenization_receipt,
            "capture": {
                "site": config["input"]["site"],
                "position_rule": "raw_token_count_plus_distance_minus_one",
                "full_input_fixed_across_distances": True,
                "carrier_order": carrier_order,
                "distance_order": distances,
                "fractions": fractions,
                "layers": layers,
                "primary_scope": config["layers"]["primary_scope"],
                "array_shape": list(activations.shape),
                "array_dtype": str(activations.dtype),
            },
            "execution": {
                "model_forward_calls": len(panel_items) * len(carrier_order) * len(distances),
                "intervention_calls": 0,
                "generation_calls": 0,
                "protected_target_files_opened": 0,
                "load_elapsed_ms": (loaded_at - started) * 1000.0,
                "total_elapsed_ms_before_close": (time.perf_counter() - started) * 1000.0,
                "forward_latency_ms": [row["forward_latency_ms"] for row in observations],
                "peak_memory_bytes_max": max(row["peak_memory_bytes"] for row in observations),
                "timing_claim_authorized": False,
            },
            "outputs": data_hashes,
            "scientific_confirmation": False,
        }
        base._write_json(stage / "run_receipt.json", run_receipt)
        base._write_ledger(stage, RUN_FILES)
        backend.close()
        backend = None
        base._publish_stage(stage, output)
        return run_receipt
    except Exception as exc:
        if backend is not None:
            backend.close()
            backend = None
        failure = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "fail",
            "model_label": model_label,
            "canonical_model_id": model_spec["canonical_model_id"],
            "error_type": type(exc).__name__,
            "error_message": base.scrub_local_paths(str(exc), model_path),
            "runtime": runtime,
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "execution": {
                "intervention_calls": 0,
                "generation_calls": 0,
                "protected_target_files_opened": 0,
                "scientific_result_available": False,
            },
        }
        try:
            base._write_json(stage / "run_receipt.json", failure)
            base._write_ledger(stage, FAILED_RUN_FILES)
            base._publish_stage(stage, output)
        except Exception:
            if stage.exists():
                shutil.rmtree(stage)
            raise
        raise PublishedRunFailure(f"Failed run receipt published for {model_label}") from exc
    finally:
        if backend is not None:
            backend.close()
        if stage.exists():
            shutil.rmtree(stage)


def validate_run(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    receipt = base._read_json(directory / "run_receipt.json", "run receipt")
    status = receipt.get("status")
    base._require(status in {"pass", "fail"}, "Unknown run status")
    base._validate_ledger(directory, RUN_FILES if status == "pass" else FAILED_RUN_FILES)
    base._require(receipt.get("protocol_id") == PROTOCOL_ID, "Run protocol mismatch")
    base._require(receipt.get("model_label") in MODEL_ROLES, "Run model role mismatch")
    if status == "fail":
        return {"receipt": receipt, "status": "fail"}
    with np.load(directory / "activations.npz", allow_pickle=False) as bundle:
        base._require(
            set(bundle.files) == {"activations", "item_ids", "carrier_ids", "distances", "layers"},
            "NPZ roster mismatch",
        )
        activations = np.asarray(bundle["activations"], dtype=np.float32)
        item_ids = [str(value) for value in bundle["item_ids"].tolist()]
        carrier_ids = [str(value) for value in bundle["carrier_ids"].tolist()]
        distances = [int(value) for value in bundle["distances"].tolist()]
        layers = [int(value) for value in bundle["layers"].tolist()]
    base._require(bool(np.isfinite(activations).all()), "Nonfinite sealed activation")
    base._require(item_ids == receipt["panel"]["item_ids"], "Sealed item order mismatch")
    base._require(carrier_ids == receipt["capture"]["carrier_order"], "Carrier order mismatch")
    base._require(distances == receipt["capture"]["distance_order"], "Distance order mismatch")
    base._require(layers == receipt["capture"]["layers"], "Sealed layer order mismatch")
    base._require(list(activations.shape) == receipt["capture"]["array_shape"], "Array shape mismatch")
    observations = base._read_jsonl(directory / "observations.jsonl", "run observations")
    expected = [
        (item_id, carrier_id, distance)
        for item_id in item_ids
        for carrier_id in carrier_ids
        for distance in distances
    ]
    observed = [
        (str(row["item_id"]), str(row["carrier_id"]), int(row["distance"]))
        for row in observations
    ]
    base._require(observed == expected, "Observation item/carrier/distance order mismatch")
    return {
        "status": "pass",
        "receipt": receipt,
        "activations": activations,
        "item_ids": item_ids,
        "carrier_ids": carrier_ids,
        "distances": distances,
        "layers": layers,
        "observations": observations,
    }


def synchronized_slot_profiles(
    tensor: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return observed and synchronized randomized slot-fraction profiles."""

    values = np.asarray(tensor, dtype=np.float64)
    base._require(values.ndim == 4, "Tensor must be family x slot x profile x width")
    family_count, slot_count, profile_count, _ = values.shape
    base._require(family_count >= 2 and slot_count >= 2 and profile_count >= 1, "Invalid tensor shape")
    base._require(draws > 0, "Randomization draw count must be positive")
    base._require(bool(np.isfinite(values).all()), "Nonfinite randomization tensor")

    by_profile = np.transpose(values, (2, 0, 1, 3))
    centered = by_profile - by_profile.mean(axis=2, keepdims=True)
    denominators = np.square(centered).sum(axis=(1, 2, 3))
    base._require(bool(np.all(denominators > frozen.EPSILON)), "Degenerate randomization denominator")
    fixed_norm_term = denominators / family_count

    pair_grams: list[tuple[int, int, np.ndarray]] = []
    for left, right in itertools.combinations(range(family_count), 2):
        grams = np.einsum(
            "lsd,ltd->lst",
            centered[:, left, :, :],
            centered[:, right, :, :],
            optimize=True,
        )
        pair_grams.append((left, right, grams))

    permutations = np.empty((draws, family_count, slot_count), dtype=np.int16)
    identity = np.arange(slot_count, dtype=np.int16)
    permutations[:, 0, :] = identity
    rng = np.random.Generator(np.random.PCG64(seed))
    for draw in range(draws):
        for family in range(1, family_count):
            permutations[draw, family, :] = rng.permutation(slot_count)

    cross = np.zeros((draws, profile_count), dtype=np.float64)
    for left, right, grams in pair_grams:
        left_indices = permutations[:, left, :]
        right_indices = permutations[:, right, :]
        for profile in range(profile_count):
            cross[:, profile] += grams[profile][left_indices, right_indices].sum(axis=1)
    randomized_ss_slot = fixed_norm_term[None, :] + (2.0 / family_count) * cross
    randomized = randomized_ss_slot / denominators[None, :]
    observed = np.asarray(
        [
            frozen.factor_geometry(values[:, :, profile, :])[
                "slot_fraction_after_family_centering"
            ]
            for profile in range(profile_count)
        ],
        dtype=np.float64,
    )
    return observed, randomized


def _one_sided_summary(observed: float, randomized: np.ndarray) -> dict[str, Any]:
    null = np.asarray(randomized, dtype=np.float64)
    base._require(null.ndim == 1 and null.size > 0, "Null statistic must be one-dimensional")
    tolerance = 1e-12
    count = int(np.count_nonzero(null >= float(observed) - tolerance))
    return {
        "statistic": float(observed),
        "null_mean": float(null.mean()),
        "null_median": float(np.median(null)),
        "excess_over_null_mean": float(observed - null.mean()),
        "greater_equal_count": count,
        "raw_p": float((1 + count) / (null.size + 1)),
    }


def distance_randomization(
    tensor: np.ndarray,
    *,
    carrier_count: int,
    distance_count: int,
    depth_count: int,
    weights: Sequence[float],
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Compute the two IUT components and complete carrier/distance/depth profile."""

    values = np.asarray(tensor, dtype=np.float64)
    base._require(
        values.shape[2] == carrier_count * distance_count * depth_count,
        "Flattened profile count mismatch",
    )
    observed_flat, randomized_flat = synchronized_slot_profiles(values, draws=draws, seed=seed)
    observed = observed_flat.reshape(carrier_count, distance_count, depth_count)
    randomized = randomized_flat.reshape(draws, carrier_count, distance_count, depth_count)
    contrast = np.asarray([float(value) for value in weights], dtype=np.float64)
    base._require(contrast.shape == (distance_count,), "Distance contrast width mismatch")
    base._require(abs(float(contrast.sum())) <= 1e-12, "Distance contrast must sum to zero")

    distance1_observed = float(observed[:, 0, :].mean())
    distance1_null = randomized[:, :, 0, :].mean(axis=(1, 2))
    weighted_observed = float(np.mean(np.sum(observed * contrast[None, :, None], axis=1)))
    weighted_null = np.mean(
        np.sum(randomized * contrast[None, None, :, None], axis=2),
        axis=(1, 2),
    )
    tail_observed = float(observed[:, -1, :].mean())
    tail_null = randomized[:, :, -1, :].mean(axis=(1, 2))
    distance1 = _one_sided_summary(distance1_observed, distance1_null)
    attenuation = _one_sided_summary(weighted_observed, weighted_null)
    tail = _one_sided_summary(tail_observed, tail_null)
    return {
        "draws": draws,
        "seed": seed,
        "rng": "numpy.random.PCG64",
        "reference_family_index": 0,
        "profile_order": "carrier_major_then_distance_then_depth",
        "observed_profile": observed,
        "null_profile_mean": randomized.mean(axis=0),
        "profile_p_greater_equal": (
            1
            + np.count_nonzero(
                randomized >= observed[None, :, :, :] - 1e-12,
                axis=0,
            )
        )
        / (draws + 1),
        "distance1_component": distance1,
        "attenuation_component": attenuation,
        "distance8_tail_secondary": tail,
        "intersection_union_raw_p": max(float(distance1["raw_p"]), float(attenuation["raw_p"])),
        "distance_profile": observed.mean(axis=(0, 2)),
        "carrier_distance_profile": observed.mean(axis=2),
    }


def _outcome_pattern(primary: Mapping[str, Mapping[str, Any]]) -> str:
    rejected = {role for role in MODEL_ROLES if bool(primary[role]["holm_reject"])}
    if rejected == set(MODEL_ROLES):
        return "all_three_distance_attenuation_candidate"
    if rejected == {"llama32_3b_bf16", "olmo3_7b_bf16"}:
        return "structured_tokenizer_pair_distance_attenuation"
    if rejected == {"olmo3_7b_bf16"}:
        return "olmo_only_distance_attenuation"
    if rejected == {"llama32_3b_bf16"}:
        return "llama_only_distance_attenuation"
    if rejected == {"gemma2_2b_4bit"}:
        return "gemma_only_distance_attenuation"
    if rejected:
        return "mixed_model_distance_attenuation"
    return "no_model_distance_attenuation"


def _load_t4_reference(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    spec = config["prior_t4_reference"]
    receipt_path = (root / CONFIG_PATH.parent / str(spec["analysis_receipt"])).resolve()
    manifest_path = (root / CONFIG_PATH.parent / str(spec["public_manifest"])).resolve()
    for path in (receipt_path, manifest_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise base.ProtocolError("T4 reference escaped repository") from exc
        base._require(path.is_file(), f"Missing T4 reference: {path.name}")
    receipt = base._read_json(receipt_path, "T4 analysis receipt")
    public_manifest = base._read_json(manifest_path, "T4 public manifest")
    base._require(receipt.get("protocol_id") == spec["protocol_id"], "T4 protocol mismatch")
    base._require(receipt.get("outcome_pattern") == spec["outcome_pattern"], "T4 outcome mismatch")
    base._require(public_manifest.get("protocol_id") == spec["protocol_id"], "T4 manifest mismatch")
    base._require(public_manifest.get("status") == "pass", "T4 public manifest is not pass")
    return {
        "role": spec["role"],
        "inferential_pooling": bool(spec["inferential_pooling"]),
        "analysis_receipt_sha256": base._sha256_file(receipt_path),
        "public_manifest_sha256": base._sha256_file(manifest_path),
        "outcome_pattern": receipt["outcome_pattern"],
        "primary_results": receipt["primary_results"],
    }


def analyze_runs(run_directories: Mapping[str, Path], output: Path) -> dict[str, Any]:
    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    base._require(tuple(run_directories) == MODEL_ROLES, "Analysis model role order mismatch")
    panel_items = _panel(root, config)
    family_order = [str(value) for value in config["panel"]["family_order"]]
    slot_order = [int(value) for value in config["panel"]["slot_order"]]
    carrier_order = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    validated = {role: validate_run(run_directories[role]) for role in MODEL_ROLES}
    for role in MODEL_ROLES:
        result = validated[role]
        base._require(result["status"] == "pass", f"Cannot analyze failed role: {role}")
        receipt = result["receipt"]
        base._require(receipt["model_label"] == role, f"Role binding mismatch: {role}")
        base._require(
            receipt["freeze"]["manifest_sha256"] == audit["manifest_sha256"],
            f"Freeze manifest mismatch: {role}",
        )
        pin = manifest["model_artifacts"][role]
        for field in ("manifest_sha256", "file_count", "total_bytes"):
            base._require(
                receipt["model"]["artifact"][field] == pin[field],
                f"Artifact pin mismatch: {role}",
            )

    endpoint = config["primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    seed = int(endpoint["seed"])
    weights = [float(value) for value in endpoint["distance_contrast_weights"]]
    rows: list[dict[str, Any]] = []
    randomization_by_role: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        result = validated[role]
        tensor = frozen._factor_tensor(
            result["activations"], panel_items, family_order, slot_order
        )
        family_count, slot_count, carrier_count, distance_count, depth_count, width = tensor.shape
        flattened = tensor.reshape(
            family_count,
            slot_count,
            carrier_count * distance_count * depth_count,
            width,
        )
        randomization = distance_randomization(
            flattened,
            carrier_count=carrier_count,
            distance_count=distance_count,
            depth_count=depth_count,
            weights=weights,
            draws=draws,
            seed=seed,
        )
        randomization_by_role[role] = randomization
        for carrier_index, carrier_id in enumerate(carrier_order):
            for distance_index, distance in enumerate(distances):
                for depth_index, layer in enumerate(result["layers"]):
                    geometry = frozen.factor_geometry(
                        tensor[:, :, carrier_index, distance_index, depth_index, :]
                    )
                    matrix = tensor[:, :, carrier_index, distance_index, depth_index, :].reshape(
                        len(family_order) * len(slot_order), -1
                    )
                    rows.append(
                        {
                            "model_label": role,
                            "carrier_id": carrier_id,
                            "carrier_index": carrier_index,
                            "distance": distance,
                            "distance_index": distance_index,
                            "layer": int(layer),
                            "layer_fraction": float(
                                result["receipt"]["capture"]["fractions"][depth_index]
                            ),
                            **geometry,
                            "slot_null_mean": float(
                                randomization["null_profile_mean"][
                                    carrier_index, distance_index, depth_index
                                ]
                            ),
                            "slot_excess_over_null_mean": float(
                                geometry["slot_fraction_after_family_centering"]
                                - randomization["null_profile_mean"][
                                    carrier_index, distance_index, depth_index
                                ]
                            ),
                            "slot_randomization_p_greater_equal": float(
                                randomization["profile_p_greater_equal"][
                                    carrier_index, distance_index, depth_index
                                ]
                            ),
                            "mean_activation_rms": float(
                                np.mean(
                                    np.sqrt(
                                        np.mean(np.square(matrix, dtype=np.float64), axis=1)
                                    )
                                )
                            ),
                            "multiplicity_decision_authorized": False,
                        }
                    )

    raw_composite = {
        role: float(randomization_by_role[role]["intersection_union_raw_p"])
        for role in MODEL_ROLES
    }
    holm = base.holm_adjust(raw_composite, alpha=float(endpoint["familywise_alpha"]))
    t4_reference = _load_t4_reference(root, config)
    primary_summary: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        cell = randomization_by_role[role]
        primary_summary[role] = {
            "distance1_component": cell["distance1_component"],
            "attenuation_component": cell["attenuation_component"],
            "intersection_union_raw_p": float(cell["intersection_union_raw_p"]),
            "holm_adjusted_p": float(holm[role]["adjusted_p"]),
            "holm_reject": bool(holm[role]["reject"]),
            "distance_profile": [float(value) for value in cell["distance_profile"]],
            "carrier_distance_profile": [
                [float(value) for value in row]
                for row in cell["carrier_distance_profile"]
            ],
            "distance8_tail_secondary": cell["distance8_tail_secondary"],
        }
    pattern = _outcome_pattern(primary_summary)

    stage = base._new_stage(output)
    try:
        base._write_jsonl(stage / "carrier_distance_layer_statistics.jsonl", rows)
        input_receipts = {
            role: {
                "run_receipt_sha256": base._sha256_file(run_directories[role] / "run_receipt.json"),
                "run_ledger_sha256": base._sha256_file(run_directories[role] / "SHA256SUMS"),
            }
            for role in MODEL_ROLES
        }
        analysis_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "frozen_joint_exploratory_observational_carrier_distance_attenuation",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "inputs": input_receipts,
            "t4_reference": t4_reference,
            "primary_endpoint": endpoint,
            "primary_results": primary_summary,
            "outcome_pattern": pattern,
            "outcome_pattern_definition": config["outcome_pattern_registry"][pattern],
            "carrier_distance_layer_row_count": len(rows),
            "carrier_order": carrier_order,
            "distance_order": distances,
            "randomization_draws_per_model": draws,
            "randomization_seed": seed,
            "intervention_calls": 0,
            "generation_calls": 0,
            "protected_target_files_opened": 0,
            "confirmatory_status": False,
            "phase_i_gate_closed": False,
        }
        base._write_json(stage / "analysis_receipt.json", analysis_receipt)
        lines = [
            "# Multifamily carrier-distance v0 result\n",
            "\n",
            f"Outcome pattern: `{pattern}`.\n",
            "\n",
            "| Model | d=1 p | attenuation p | IUT p | Holm p | Reject |\n",
            "|---|---:|---:|---:|---:|---|\n",
        ]
        for role in MODEL_ROLES:
            cell = primary_summary[role]
            lines.append(
                f"| `{role}` | {cell['distance1_component']['raw_p']:.9f} | "
                f"{cell['attenuation_component']['raw_p']:.9f} | "
                f"{cell['intersection_union_raw_p']:.9f} | "
                f"{cell['holm_adjusted_p']:.9f} | {str(cell['holm_reject']).lower()} |\n"
            )
        lines.extend(
            [
                "\n",
                "The primary decision requires both distance-1 recurrence and the fixed "
                "positive log-distance contrast. It does not establish monotonic decay, "
                "disappearance, semantics, causality, tokenizer equivalence, backend "
                "equivalence, confirmation, or a Phase I gate decision.\n",
            ]
        )
        base._atomic_write(stage / "report.md", "".join(lines).encode("utf-8"))
        base._write_ledger(stage, ANALYSIS_FILES)
        base._publish_stage(stage, output)
        return analysis_receipt
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def validate_analysis(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    base._validate_ledger(directory, ANALYSIS_FILES)
    receipt = base._read_json(directory / "analysis_receipt.json", "analysis receipt")
    base._require(receipt.get("protocol_id") == PROTOCOL_ID, "Analysis protocol mismatch")
    base._require(receipt.get("status") == "pass", "Analysis status is not pass")
    rows = base._read_jsonl(
        directory / "carrier_distance_layer_statistics.jsonl",
        "carrier/distance/layer rows",
    )
    base._require(
        len(rows) == int(receipt["carrier_distance_layer_row_count"]),
        "Carrier/distance/layer row count mismatch",
    )
    base._require(
        {str(row["model_label"]) for row in rows} == set(MODEL_ROLES),
        "Analysis model roster mismatch",
    )
    base._require(
        not any(bool(row["multiplicity_decision_authorized"]) for row in rows),
        "A carrier/distance/layer decision was authorized",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "outcome_pattern": receipt["outcome_pattern"],
        "carrier_distance_layer_row_count": len(rows),
        "scientific_confirmation": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-freeze", help="Validate the public protocol freeze")

    preflight = subparsers.add_parser(
        "tokenizer-preflight", help="Replay one tokenizer-only carrier-distance contract"
    )
    preflight.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    preflight.add_argument("--model-path", type=Path, required=True)

    run = subparsers.add_parser("run", help="Run one role-bound model cell")
    run.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)

    validate_one = subparsers.add_parser("validate-run", help="Validate one sealed model run")
    validate_one.add_argument("directory", type=Path)

    analyze = subparsers.add_parser("analyze", help="Analyze all three predeclared model roles")
    analyze.add_argument("--gemma-run", type=Path, required=True)
    analyze.add_argument("--llama-run", type=Path, required=True)
    analyze.add_argument("--olmo-run", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)

    validate_joint = subparsers.add_parser("validate-analysis", help="Validate joint analysis")
    validate_joint.add_argument("directory", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "audit-freeze":
            payload = audit_freeze()
        elif args.command == "tokenizer-preflight":
            payload = tokenizer_preflight(args.model_label, args.model_path)
        elif args.command == "run":
            payload = run_model(args.model_label, args.model_path, args.output)
        elif args.command == "validate-run":
            validated = validate_run(args.directory)
            payload = {
                "status": validated["status"],
                "protocol_id": PROTOCOL_ID,
                "model_label": validated["receipt"]["model_label"],
                "array_shape": validated["receipt"].get("capture", {}).get("array_shape"),
            }
        elif args.command == "analyze":
            payload = analyze_runs(
                {
                    MODEL_ROLES[0]: args.gemma_run,
                    MODEL_ROLES[1]: args.llama_run,
                    MODEL_ROLES[2]: args.olmo_run,
                },
                args.output,
            )
        elif args.command == "validate-analysis":
            payload = validate_analysis(args.directory)
        else:  # pragma: no cover
            raise AssertionError(args.command)
        print(base._json_bytes(payload, pretty=True).decode("utf-8"))
    except (OSError, ValueError, base.ProtocolError, PublishedRunFailure) as exc:
        print(
            base._json_bytes({"status": "fail", "error": str(exc)}, pretty=True).decode(
                "utf-8"
            )
        )
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
