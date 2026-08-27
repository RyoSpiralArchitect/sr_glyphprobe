#!/usr/bin/env python3
"""Run and analyze the frozen multifamily matched-slot geometry v0 study.

This is one coherent protocol surface for two observational MLX cells. It
audits the public freeze, validates the exact tokenizer regime, captures only
resid_post activations for the fixed 5x10 panel, performs the synchronized
within-family slot-label randomization, applies the two-test Holm correction,
and seals every output with SHA-256. It never intervenes, generates text, or
opens a target bank.
"""

from __future__ import annotations

import argparse
import itertools
import math
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_colored_shape_geometry_v0 as base  # noqa: E402

from glyphprobe.backends.mlx_backend import MLXBackend  # noqa: E402
from glyphprobe.config import BackendConfig  # noqa: E402
from glyphprobe.provenance import implementation_receipt  # noqa: E402


PROTOCOL_ID = "glyphprobe-multifamily-matched-slot-geometry-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/multifamily_matched_slot_geometry_v0.json")
CONFIG_PATH = Path("configs/multifamily_matched_slot_geometry_v0.yaml")
MODEL_ROLES = ("gemma2_2b_4bit", "olmo3_7b_bf16")
RUN_FILES = ("activations.npz", "observations.jsonl", "run_receipt.json")
FAILED_RUN_FILES = ("run_receipt.json",)
ANALYSIS_FILES = ("layer_statistics.jsonl", "analysis_receipt.json", "report.md")
EPSILON = 1e-12


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
    implementation = implementation_receipt()
    expected = manifest.get("implementation")
    base._require(isinstance(expected, dict), "Missing implementation pin")
    base._require(
        implementation.get("source_tree_sha256") == expected.get("source_tree_sha256"),
        "GlyphProbe source-tree SHA-256 mismatch",
    )
    base._require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model role order mismatch")
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


def _load_panel(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    panel = config["panel"]
    family_order = [str(value) for value in panel["family_order"]]
    slot_order = [int(value) for value in panel["slot_order"]]
    expected_per_family = int(panel["expected_items_per_family"])
    base._require(len(slot_order) == expected_per_family, "Slot count mismatch")
    base._require(slot_order == list(range(expected_per_family)), "Slots must be consecutive")
    sources = panel["sources"]
    base._require(set(sources) == set(family_order), "Panel source roster mismatch")

    combined: list[dict[str, Any]] = []
    low_bits_by_slot: dict[int, int] = {}
    for family in family_order:
        source = (root / CONFIG_PATH.parent / str(sources[family])).resolve()
        try:
            source.relative_to(root)
        except ValueError as exc:
            raise base.ProtocolError(f"Panel source escaped repository: {family}") from exc
        payload = base._read_yaml(source, f"{family} panel")
        rows = payload.get("items")
        base._require(isinstance(rows, list), f"Panel rows missing: {family}")
        base._require(len(rows) == expected_per_family, f"Panel count mismatch: {family}")
        codepoints: list[int] = []
        for slot, item in zip(slot_order, rows, strict=True):
            base._require(isinstance(item, dict), f"Invalid panel row: {family}/{slot}")
            expected_id = f"{family}_slot_{slot:02d}"
            base._require(item.get("id") == expected_id, f"Panel ID mismatch: {expected_id}")
            glyph = item.get("glyph")
            factors = item.get("factors")
            base._require(isinstance(glyph, str) and len(glyph) == 1, f"Glyph mismatch: {expected_id}")
            base._require(isinstance(factors, dict), f"Factor mapping missing: {expected_id}")
            base._require(factors.get("family") == family, f"Family factor mismatch: {expected_id}")
            base._require(
                factors.get("matched_slot") == f"slot_{slot:02d}",
                f"Slot factor mismatch: {expected_id}",
            )
            codepoint = ord(glyph)
            base._require(
                factors.get("codepoint") == f"U+{codepoint:04X}",
                f"Codepoint factor mismatch: {expected_id}",
            )
            low_bits = codepoint & 0x3F
            if slot in low_bits_by_slot:
                base._require(low_bits_by_slot[slot] == low_bits, f"Matched low bits differ: {slot}")
            else:
                low_bits_by_slot[slot] = low_bits
            codepoints.append(codepoint)
            combined.append(dict(item))
        base._require(
            codepoints == list(range(codepoints[0], codepoints[0] + expected_per_family)),
            f"Codepoints are not consecutive: {family}",
        )

    base._require(len(combined) == int(panel["expected_total_items"]), "Total panel count mismatch")
    base._require(
        len({str(item["id"]) for item in combined}) == len(combined),
        "Duplicate panel item ID",
    )
    return combined


def validate_tokenization_matrix(
    tokenizations: Sequence[Any],
    panel_items: Sequence[Mapping[str, Any]],
    model_spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate one predeclared tokenizer regime without loading model weights."""

    base._require(len(tokenizations) == len(panel_items), "Tokenization/panel row mismatch")
    contract = model_spec["tokenization_contract"]
    expected_count = int(contract["expected_item_token_count"])
    sequences = [tuple(int(value) for value in row.token_ids) for row in tokenizations]
    base._require(all(len(row) == expected_count for row in sequences), "Token-count contract failed")
    base._require(
        len(set(sequences)) == int(contract["expected_unique_sequence_count"]),
        "Unique token-sequence contract failed",
    )
    minimum_prefix = base.minimum_shared_prefix(sequences)
    base._require(
        minimum_prefix >= int(contract["minimum_shared_prefix_across_panel"]),
        "Shared-prefix contract failed",
    )

    family_order = []
    slot_order = []
    for item in panel_items:
        factors = item["factors"]
        family = str(factors["family"])
        slot = int(str(factors["matched_slot"]).removeprefix("slot_"))
        family_order.append(family)
        slot_order.append(slot)

    kind = str(contract["kind"])
    if kind == "distinct_atomic_tokens":
        base._require(expected_count == 1, "Atomic contract must use one token")
    elif kind == "exact_prefix_family_slot_factorization":
        prefix = int(contract["shared_prefix_token_id"])
        family_ids = {str(key): int(value) for key, value in contract["family_token_ids"].items()}
        slot_ids = [int(value) for value in contract["slot_token_ids"]]
        for item, sequence, family, slot in zip(
            panel_items, sequences, family_order, slot_order, strict=True
        ):
            expected = (prefix, family_ids[family], slot_ids[slot])
            base._require(sequence == expected, f"Exact token factorization failed: {item['id']}")
    else:
        raise base.ProtocolError(f"Unknown tokenization contract kind: {kind}")

    return {
        "kind": kind,
        "expected_item_token_count": expected_count,
        "observed_item_token_counts": sorted({len(row) for row in sequences}),
        "unique_sequence_count": len(set(sequences)),
        "minimum_shared_prefix_across_panel": minimum_prefix,
        "matching_family": contract["matching_family"],
        "token_sequences": [list(row) for row in sequences],
    }


def factor_geometry(matrix: np.ndarray) -> dict[str, float]:
    """Two-way no-replication geometry for a family x slot x width tensor."""

    values = np.asarray(matrix, dtype=np.float64)
    base._require(values.ndim == 3, "Factor matrix must be family x slot x width")
    family_count, slot_count, _ = values.shape
    base._require(family_count >= 2 and slot_count >= 2, "Factor grid is too small")
    base._require(bool(np.isfinite(values).all()), "Nonfinite factor matrix")

    grand = values.mean(axis=(0, 1))
    family_means = values.mean(axis=1)
    slot_means = values.mean(axis=0)
    interaction = (
        values
        - family_means[:, None, :]
        - slot_means[None, :, :]
        + grand[None, None, :]
    )
    centered = values - grand[None, None, :]
    ss_total = float(np.square(centered).sum())
    ss_family = float(slot_count * np.square(family_means - grand[None, :]).sum())
    ss_slot = float(family_count * np.square(slot_means - grand[None, :]).sum())
    ss_interaction = float(np.square(interaction).sum())
    base._require(ss_total > EPSILON, "Degenerate total centered sum of squares")
    tolerance = max(1e-8, 1e-10 * ss_total)
    base._require(
        abs(ss_total - ss_family - ss_slot - ss_interaction) <= tolerance,
        "Factor sum-of-squares decomposition failed",
    )
    slot_denominator = ss_slot + ss_interaction
    family_denominator = ss_family + ss_interaction
    base._require(slot_denominator > EPSILON, "Degenerate within-family sum of squares")
    base._require(family_denominator > EPSILON, "Degenerate within-slot sum of squares")
    return {
        "ss_total": ss_total,
        "ss_family": ss_family,
        "ss_slot": ss_slot,
        "ss_interaction": ss_interaction,
        "slot_fraction_after_family_centering": ss_slot / slot_denominator,
        "family_fraction_after_slot_centering": ss_family / family_denominator,
        "interaction_fraction_of_total": ss_interaction / ss_total,
    }


def synchronized_slot_randomization(
    tensor: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Randomize slot labels within family using one draw across all depths."""

    values = np.asarray(tensor, dtype=np.float64)
    base._require(values.ndim == 4, "Tensor must be family x slot x depth x width")
    family_count, slot_count, depth_count, _ = values.shape
    base._require(family_count >= 2 and slot_count >= 2 and depth_count >= 1, "Invalid tensor shape")
    base._require(draws > 0, "Randomization draw count must be positive")
    base._require(bool(np.isfinite(values).all()), "Nonfinite randomization tensor")

    by_depth = np.transpose(values, (2, 0, 1, 3))
    centered = by_depth - by_depth.mean(axis=2, keepdims=True)
    denominators = np.square(centered).sum(axis=(1, 2, 3))
    base._require(bool(np.all(denominators > EPSILON)), "Degenerate randomization denominator")
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

    cross = np.zeros((draws, depth_count), dtype=np.float64)
    for left, right, grams in pair_grams:
        left_indices = permutations[:, left, :]
        right_indices = permutations[:, right, :]
        for depth in range(depth_count):
            cross[:, depth] += grams[depth][left_indices, right_indices].sum(axis=1)
    randomized_ss_slot = fixed_norm_term[None, :] + (2.0 / family_count) * cross
    randomized_profile = randomized_ss_slot / denominators[None, :]

    observed_profile = np.asarray(
        [
            factor_geometry(values[:, :, depth, :])["slot_fraction_after_family_centering"]
            for depth in range(depth_count)
        ],
        dtype=np.float64,
    )
    observed_omnibus = float(observed_profile.mean())
    null_omnibus = randomized_profile.mean(axis=1)
    tolerance = 1e-12
    omnibus_exceedances = int(np.count_nonzero(null_omnibus >= observed_omnibus - tolerance))
    per_depth_exceedances = np.count_nonzero(
        randomized_profile >= observed_profile[None, :] - tolerance,
        axis=0,
    )
    denominator = draws + 1
    return {
        "draws": draws,
        "seed": seed,
        "rng": "numpy.random.PCG64",
        "reference_family_index": 0,
        "observed_depth_profile": [float(value) for value in observed_profile],
        "observed_omnibus": observed_omnibus,
        "null_omnibus_mean": float(null_omnibus.mean()),
        "null_omnibus_median": float(np.median(null_omnibus)),
        "null_omnibus_minimum": float(null_omnibus.min()),
        "null_omnibus_maximum": float(null_omnibus.max()),
        "omnibus_excess_over_null_mean": observed_omnibus - float(null_omnibus.mean()),
        "omnibus_greater_equal_count": omnibus_exceedances,
        "omnibus_p_greater_equal": float((1 + omnibus_exceedances) / denominator),
        "per_depth_null_mean": [float(value) for value in randomized_profile.mean(axis=0)],
        "per_depth_greater_equal_count": [int(value) for value in per_depth_exceedances],
        "per_depth_p_greater_equal": [
            float((1 + int(value)) / denominator) for value in per_depth_exceedances
        ],
    }


def run_model(model_label: str, model_path: Path, output: Path) -> dict[str, Any]:
    """Run one role-bound model cell and atomically publish its sealed bundle."""

    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    base._require(model_label in MODEL_ROLES, f"Unknown model role: {model_label}")
    model_spec = config["models"][model_label]
    artifact_pin = manifest["model_artifacts"][model_label]
    panel_items = _load_panel(root, config)
    runtime = base._model_runtime_check(config)
    stage = base._new_stage(output)
    backend: MLXBackend | None = None
    started = time.perf_counter()
    try:
        backend = MLXBackend(
            BackendConfig(
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
            base._require(artifact.get(field) == artifact_pin.get(field), f"Model artifact {field} mismatch")

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
        tokenizations = [backend.tokenize(str(item["glyph"])) for item in panel_items]
        tokenization_receipt = validate_tokenization_matrix(tokenizations, panel_items, model_spec)

        activation_rows: list[np.ndarray] = []
        observations: list[dict[str, Any]] = []
        for panel_index, (item, tokenized) in enumerate(zip(panel_items, tokenizations, strict=True)):
            result = backend.forward(
                str(item["glyph"]),
                capture_layers=layers,
                site=str(config["input"]["site"]),
                position=str(config["input"]["position"]),
                return_attentions=bool(config["input"]["return_attentions"]),
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
                base._require(vector.shape == (backend.model_dim,), f"Activation width mismatch: {item['id']}")
                base._require(bool(np.isfinite(vector).all()), f"Nonfinite activation: {item['id']}")
                layer_vectors.append(vector)
                layer_rms[str(layer)] = float(np.sqrt(np.mean(np.square(vector, dtype=np.float64))))
            activation_rows.append(np.stack(layer_vectors, axis=0))
            factors = item["factors"]
            observations.append(
                {
                    "panel_index": panel_index,
                    "item_id": str(item["id"]),
                    "glyph": str(item["glyph"]),
                    "family": str(factors["family"]),
                    "matched_slot": str(factors["matched_slot"]),
                    "codepoint": str(factors["codepoint"]),
                    "token_ids": [int(value) for value in tokenized.token_ids],
                    "token_pieces": [str(value) for value in tokenized.tokens],
                    "token_count": len(tokenized.token_ids),
                    "activation_rms_by_layer": layer_rms,
                    "logits_finite": True,
                    "logit_argmax": int(np.argmax(result.logits)),
                    "forward_latency_ms": float(result.latency_ms),
                    "peak_memory_bytes": int(result.peak_memory_bytes or 0),
                }
            )

        activations = np.stack(activation_rows, axis=0).astype(np.float32, copy=False)
        np.savez_compressed(
            stage / "activations.npz",
            activations=activations,
            item_ids=np.asarray([str(item["id"]) for item in panel_items], dtype=np.str_),
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
            "tokenization": {
                "context_id": config["input"]["context_id"],
                "add_special_tokens": config["input"]["add_special_tokens"],
                **tokenization_receipt,
            },
            "capture": {
                "site": config["input"]["site"],
                "position": config["input"]["position"],
                "fractions": fractions,
                "layers": layers,
                "primary_scope": config["layers"]["primary_scope"],
                "array_shape": list(activations.shape),
                "array_dtype": str(activations.dtype),
            },
            "execution": {
                "model_forward_calls": len(panel_items),
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
        base._require(set(bundle.files) == {"activations", "item_ids", "layers"}, "NPZ roster mismatch")
        activations = np.asarray(bundle["activations"], dtype=np.float32)
        item_ids = [str(value) for value in bundle["item_ids"].tolist()]
        layers = [int(value) for value in bundle["layers"].tolist()]
    base._require(bool(np.isfinite(activations).all()), "Nonfinite sealed activation")
    base._require(item_ids == receipt["panel"]["item_ids"], "Sealed item order mismatch")
    base._require(layers == receipt["capture"]["layers"], "Sealed layer order mismatch")
    base._require(list(activations.shape) == receipt["capture"]["array_shape"], "Array shape mismatch")
    observations = base._read_jsonl(directory / "observations.jsonl", "run observations")
    base._require(len(observations) == len(item_ids), "Observation row count mismatch")
    base._require(
        [str(row["item_id"]) for row in observations] == item_ids,
        "Observation item order mismatch",
    )
    return {
        "status": "pass",
        "receipt": receipt,
        "activations": activations,
        "item_ids": item_ids,
        "layers": layers,
        "observations": observations,
    }


def _factor_tensor(
    activations: np.ndarray,
    panel_items: Sequence[Mapping[str, Any]],
    family_order: Sequence[str],
    slot_order: Sequence[int],
) -> np.ndarray:
    index = {str(item["id"]): position for position, item in enumerate(panel_items)}
    rows: list[np.ndarray] = []
    for family in family_order:
        rows.append(
            np.stack(
                [activations[index[f"{family}_slot_{slot:02d}"]] for slot in slot_order],
                axis=0,
            )
        )
    return np.stack(rows, axis=0)


def _outcome_pattern(primary: Mapping[str, Mapping[str, Any]]) -> str:
    left = primary[MODEL_ROLES[0]]
    right = primary[MODEL_ROLES[1]]
    left_excess = float(left["excess_over_null_mean"])
    right_excess = float(right["excess_over_null_mean"])
    if left_excess * right_excess < 0.0:
        return "opposite_null_centered_direction"
    if bool(left["holm_reject"]) and bool(right["holm_reject"]) and min(left_excess, right_excess) > 0:
        return "dual_model_slot_recurrence_candidate"
    if bool(left["holm_reject"]) and not bool(right["holm_reject"]):
        return "gemma_only_heterogeneity"
    if bool(right["holm_reject"]) and not bool(left["holm_reject"]):
        return "olmo_only_token_structured_recurrence"
    return "no_dual_model_slot_recurrence"


def analyze_runs(run_directories: Mapping[str, Path], output: Path) -> dict[str, Any]:
    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    base._require(tuple(run_directories) == MODEL_ROLES, "Analysis model role order mismatch")
    panel_items = _load_panel(root, config)
    family_order = [str(value) for value in config["panel"]["family_order"]]
    slot_order = [int(value) for value in config["panel"]["slot_order"]]
    validated = {role: validate_run(run_directories[role]) for role in MODEL_ROLES}
    for role in MODEL_ROLES:
        base._require(validated[role]["status"] == "pass", f"Cannot analyze failed role: {role}")
        receipt = validated[role]["receipt"]
        base._require(receipt["model_label"] == role, f"Role binding mismatch: {role}")
        base._require(
            receipt["freeze"]["manifest_sha256"] == audit["manifest_sha256"],
            f"Freeze manifest mismatch: {role}",
        )
        pin = manifest["model_artifacts"][role]
        for field in ("manifest_sha256", "file_count", "total_bytes"):
            base._require(receipt["model"]["artifact"][field] == pin[field], f"Artifact pin mismatch: {role}")

    endpoint = config["primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    seed = int(endpoint["seed"])
    layer_rows: list[dict[str, Any]] = []
    randomization_by_role: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        result = validated[role]
        tensor = _factor_tensor(
            result["activations"], panel_items, family_order, slot_order
        )
        randomization = synchronized_slot_randomization(tensor, draws=draws, seed=seed)
        randomization_by_role[role] = randomization
        for depth_position, layer in enumerate(result["layers"]):
            geometry = factor_geometry(tensor[:, :, depth_position, :])
            matrix = tensor[:, :, depth_position, :].reshape(
                len(family_order) * len(slot_order), -1
            )
            layer_rows.append(
                {
                    "model_label": role,
                    "layer": int(layer),
                    "layer_fraction": float(result["receipt"]["capture"]["fractions"][depth_position]),
                    **geometry,
                    "slot_null_mean": float(randomization["per_depth_null_mean"][depth_position]),
                    "slot_excess_over_null_mean": float(
                        geometry["slot_fraction_after_family_centering"]
                        - randomization["per_depth_null_mean"][depth_position]
                    ),
                    "slot_randomization_p_greater_equal": float(
                        randomization["per_depth_p_greater_equal"][depth_position]
                    ),
                    "mean_activation_rms": float(
                        np.mean(np.sqrt(np.mean(np.square(matrix, dtype=np.float64), axis=1)))
                    ),
                    "multiplicity_decision_authorized": False,
                }
            )

    holm = base.holm_adjust(
        {
            role: float(randomization_by_role[role]["omnibus_p_greater_equal"])
            for role in MODEL_ROLES
        },
        alpha=float(endpoint["familywise_alpha"]),
    )
    primary_summary: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        cell = randomization_by_role[role]
        primary_summary[role] = {
            "statistic": float(cell["observed_omnibus"]),
            "null_mean": float(cell["null_omnibus_mean"]),
            "excess_over_null_mean": float(cell["omnibus_excess_over_null_mean"]),
            "raw_p": float(cell["omnibus_p_greater_equal"]),
            "holm_adjusted_p": float(holm[role]["adjusted_p"]),
            "holm_reject": bool(holm[role]["reject"]),
            "depth_profile": list(cell["observed_depth_profile"]),
        }
    pattern = _outcome_pattern(primary_summary)

    stage = base._new_stage(output)
    try:
        base._write_jsonl(stage / "layer_statistics.jsonl", layer_rows)
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
            "analysis_role": "frozen_joint_exploratory_observational_matched_slot_geometry",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "inputs": input_receipts,
            "primary_endpoint": endpoint,
            "primary_results": primary_summary,
            "outcome_pattern": pattern,
            "outcome_pattern_definition": config["outcome_pattern_registry"][pattern],
            "layer_row_count": len(layer_rows),
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
            "# Multifamily matched-slot geometry v0 result\n",
            "\n",
            f"Outcome pattern: `{pattern}`.\n",
            "\n",
            "| Model | All-depth slot fraction | Null mean | Excess | Raw p | Holm p | Reject |\n",
            "|---|---:|---:|---:|---:|---:|---|\n",
        ]
        for role in MODEL_ROLES:
            cell = primary_summary[role]
            lines.append(
                f"| `{role}` | {cell['statistic']:.9f} | {cell['null_mean']:.9f} | "
                f"{cell['excess_over_null_mean']:.9f} | {cell['raw_p']:.9f} | "
                f"{cell['holm_adjusted_p']:.9f} | {str(cell['holm_reject']).lower()} |\n"
            )
        lines.extend(
            [
                "\n",
                "This is a frozen observational exploratory result about the fixed "
                "Unicode/tokenizer slot layout. It is not a semantic, causal, parity, "
                "node-performance, quantization-equivalence, tokenizer-equivalence, "
                "confirmatory, or Phase I gate result.\n",
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
    rows = base._read_jsonl(directory / "layer_statistics.jsonl", "layer statistics")
    base._require(len(rows) == int(receipt["layer_row_count"]), "Layer row count mismatch")
    base._require(
        {str(row["model_label"]) for row in rows} == set(MODEL_ROLES),
        "Analysis model roster mismatch",
    )
    base._require(
        not any(bool(row["multiplicity_decision_authorized"]) for row in rows),
        "A per-layer decision was authorized",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "outcome_pattern": receipt["outcome_pattern"],
        "layer_row_count": len(rows),
        "scientific_confirmation": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-freeze", help="Validate the public protocol freeze")

    run = subparsers.add_parser("run", help="Run one role-bound model cell")
    run.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)

    validate_one = subparsers.add_parser("validate-run", help="Validate one sealed model run")
    validate_one.add_argument("directory", type=Path)

    analyze = subparsers.add_parser("analyze", help="Analyze both predeclared model roles")
    analyze.add_argument("--gemma-run", type=Path, required=True)
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
        elif args.command == "run":
            payload = run_model(args.model_label, args.model_path, args.output)
        elif args.command == "validate-run":
            payload = validate_run(args.directory)
        elif args.command == "analyze":
            payload = analyze_runs(
                {
                    MODEL_ROLES[0]: args.gemma_run,
                    MODEL_ROLES[1]: args.olmo_run,
                },
                args.output,
            )
        elif args.command == "validate-analysis":
            payload = validate_analysis(args.directory)
        else:  # pragma: no cover
            raise base.ProtocolError(f"Unknown command: {args.command}")
        print(base._json_bytes(payload, pretty=True).decode("utf-8"))
    except (base.ProtocolError, OSError, ValueError) as exc:
        print(base._json_bytes({"status": "fail", "error": str(exc)}, pretty=True).decode("utf-8"))
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
