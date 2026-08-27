#!/usr/bin/env python3
"""Run the frozen multifamily common-suffix carryover v0 study.

The protocol moves the readout from each glyph's final token to one of two
exact common one-token suffixes. It captures observational ``resid_post``
geometry only, synchronizes the slot-label null across both contexts and all
fixed depths, and keeps the earlier raw-glyph T3 result descriptive.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_matched_slot_geometry_v0 as frozen  # noqa: E402


base = frozen.base
PROTOCOL_ID = "glyphprobe-multifamily-common-suffix-carryover-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/multifamily_common_suffix_carryover_v0.json")
CONFIG_PATH = Path("configs/multifamily_common_suffix_carryover_v0.yaml")
MODEL_ROLES = frozen.MODEL_ROLES
RUN_FILES = ("activations.npz", "observations.jsonl", "run_receipt.json")
FAILED_RUN_FILES = ("run_receipt.json",)
ANALYSIS_FILES = ("context_layer_statistics.jsonl", "analysis_receipt.json", "report.md")


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
        list(config["input"]["context_order"]) == ["period", "newline"],
        "Context order mismatch",
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


def _raw_contract_spec(model_spec: Mapping[str, Any]) -> dict[str, Any]:
    return {"tokenization_contract": model_spec["raw_tokenization_contract"]}


def validate_context_tokenizations(
    raw_tokenizations: Sequence[Any],
    context_tokenizations: Mapping[str, Sequence[Any]],
    panel_items: Sequence[Mapping[str, Any]],
    model_spec: Mapping[str, Any],
    input_spec: Mapping[str, Any],
    *,
    decoder: Callable[[Sequence[int]], str] | None = None,
) -> dict[str, Any]:
    """Validate raw preservation plus one exact common suffix token."""

    raw_receipt = frozen.validate_tokenization_matrix(
        raw_tokenizations,
        panel_items,
        _raw_contract_spec(model_spec),
    )
    raw_sequences = [tuple(int(value) for value in row.token_ids) for row in raw_tokenizations]
    context_order = [str(value) for value in input_spec["context_order"]]
    base._require(tuple(context_tokenizations) == tuple(context_order), "Context role order mismatch")
    expected_suffix_ids = {
        str(key): int(value) for key, value in model_spec["suffix_token_ids"].items()
    }
    base._require(set(expected_suffix_ids) == set(context_order), "Suffix-token roster mismatch")

    contexts: dict[str, dict[str, Any]] = {}
    for context_id in context_order:
        rows = context_tokenizations[context_id]
        base._require(len(rows) == len(panel_items), f"Context row mismatch: {context_id}")
        suffix = str(input_spec["contexts"][context_id]["suffix"])
        expected_suffix = expected_suffix_ids[context_id]
        sequences = [tuple(int(value) for value in row.token_ids) for row in rows]
        expected = [raw + (expected_suffix,) for raw in raw_sequences]
        base._require(sequences == expected, f"Raw-plus-suffix contract failed: {context_id}")
        decoded_exact = None
        if decoder is not None:
            decoded_exact = [
                decoder(sequence) == str(item["glyph"]) + suffix
                for item, sequence in zip(panel_items, sequences, strict=True)
            ]
            base._require(all(decoded_exact), f"Roundtrip contract failed: {context_id}")
        contexts[context_id] = {
            "suffix": suffix,
            "suffix_token_id": expected_suffix,
            "combined_token_count": len(sequences[0]),
            "observed_combined_token_counts": sorted({len(row) for row in sequences}),
            "unique_combined_sequence_count": len(set(sequences)),
            "raw_prefix_preserved_count": sum(
                sequence[: len(raw)] == raw
                for raw, sequence in zip(raw_sequences, sequences, strict=True)
            ),
            "roundtrip_exact_count": None if decoded_exact is None else sum(decoded_exact),
            "token_sequences": [list(row) for row in sequences],
        }
    return {
        "exact_contract": input_spec["exact_contract"],
        "raw": raw_receipt,
        "context_order": context_order,
        "contexts": contexts,
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
    contexts = {
        context_id: [
            tokenized(str(config["input"]["contexts"][context_id]["template"]).format(glyph=item["glyph"]))
            for item in panel_items
        ]
        for context_id in config["input"]["context_order"]
    }
    receipt = validate_context_tokenizations(
        raw,
        contexts,
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
    """Run one role-bound common-suffix model cell and atomically publish it."""

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
        context_order = [str(value) for value in config["input"]["context_order"]]
        raw_tokenizations = [backend.tokenize(str(item["glyph"])) for item in panel_items]
        context_tokenizations = {
            context_id: [
                backend.tokenize(
                    str(config["input"]["contexts"][context_id]["template"]).format(
                        glyph=item["glyph"]
                    )
                )
                for item in panel_items
            ]
            for context_id in context_order
        }
        tokenization_receipt = validate_context_tokenizations(
            raw_tokenizations,
            context_tokenizations,
            panel_items,
            model_spec,
            config["input"],
            decoder=lambda ids: _decode(backend, ids),
        )

        activation_rows: list[np.ndarray] = []
        observations: list[dict[str, Any]] = []
        for panel_index, item in enumerate(panel_items):
            context_rows: list[np.ndarray] = []
            for context_index, context_id in enumerate(context_order):
                text = str(config["input"]["contexts"][context_id]["template"]).format(
                    glyph=item["glyph"]
                )
                tokenized = context_tokenizations[context_id][panel_index]
                result = backend.forward(
                    text,
                    capture_layers=layers,
                    site=str(config["input"]["site"]),
                    position=str(config["input"]["position"]),
                    return_attentions=bool(config["input"]["return_attentions"]),
                )
                base._require(
                    [int(value) for value in result.token_ids]
                    == [int(value) for value in tokenized.token_ids],
                    f"Forward tokenization diverged from preflight: {item['id']}/{context_id}",
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
                context_rows.append(np.stack(layer_vectors, axis=0))
                factors = item["factors"]
                observations.append(
                    {
                        "panel_index": panel_index,
                        "context_index": context_index,
                        "context_id": context_id,
                        "item_id": str(item["id"]),
                        "glyph": str(item["glyph"]),
                        "family": str(factors["family"]),
                        "matched_slot": str(factors["matched_slot"]),
                        "codepoint": str(factors["codepoint"]),
                        "raw_token_ids": [int(value) for value in raw_tokenizations[panel_index].token_ids],
                        "token_ids": [int(value) for value in tokenized.token_ids],
                        "token_pieces": [str(value) for value in tokenized.tokens],
                        "token_count": len(tokenized.token_ids),
                        "suffix_token_id": int(tokenized.token_ids[-1]),
                        "activation_rms_by_layer": layer_rms,
                        "logits_finite": True,
                        "logit_argmax": int(np.argmax(result.logits)),
                        "forward_latency_ms": float(result.latency_ms),
                        "peak_memory_bytes": int(result.peak_memory_bytes or 0),
                    }
                )
            activation_rows.append(np.stack(context_rows, axis=0))

        activations = np.stack(activation_rows, axis=0).astype(np.float32, copy=False)
        np.savez_compressed(
            stage / "activations.npz",
            activations=activations,
            item_ids=np.asarray([str(item["id"]) for item in panel_items], dtype=np.str_),
            context_ids=np.asarray(context_order, dtype=np.str_),
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
                "position": config["input"]["position"],
                "context_order": context_order,
                "fractions": fractions,
                "layers": layers,
                "primary_scope": config["layers"]["primary_scope"],
                "array_shape": list(activations.shape),
                "array_dtype": str(activations.dtype),
            },
            "execution": {
                "model_forward_calls": len(panel_items) * len(context_order),
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
            set(bundle.files) == {"activations", "item_ids", "context_ids", "layers"},
            "NPZ roster mismatch",
        )
        activations = np.asarray(bundle["activations"], dtype=np.float32)
        item_ids = [str(value) for value in bundle["item_ids"].tolist()]
        context_ids = [str(value) for value in bundle["context_ids"].tolist()]
        layers = [int(value) for value in bundle["layers"].tolist()]
    base._require(bool(np.isfinite(activations).all()), "Nonfinite sealed activation")
    base._require(item_ids == receipt["panel"]["item_ids"], "Sealed item order mismatch")
    base._require(context_ids == receipt["capture"]["context_order"], "Context order mismatch")
    base._require(layers == receipt["capture"]["layers"], "Sealed layer order mismatch")
    base._require(list(activations.shape) == receipt["capture"]["array_shape"], "Array shape mismatch")
    observations = base._read_jsonl(directory / "observations.jsonl", "run observations")
    expected_pairs = [(item_id, context_id) for item_id in item_ids for context_id in context_ids]
    observed_pairs = [(str(row["item_id"]), str(row["context_id"])) for row in observations]
    base._require(observed_pairs == expected_pairs, "Observation item/context order mismatch")
    return {
        "status": "pass",
        "receipt": receipt,
        "activations": activations,
        "item_ids": item_ids,
        "context_ids": context_ids,
        "layers": layers,
        "observations": observations,
    }


def synchronized_context_depth_randomization(
    tensor: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Use one family-wise slot permutation across contexts and depths."""

    values = np.asarray(tensor, dtype=np.float64)
    base._require(values.ndim == 5, "Tensor must be context x family x slot x depth x width")
    context_count, family_count, slot_count, depth_count, width = values.shape
    combined = np.transpose(values, (1, 2, 0, 3, 4)).reshape(
        family_count,
        slot_count,
        context_count * depth_count,
        width,
    )
    overall = frozen.synchronized_slot_randomization(combined, draws=draws, seed=seed)
    by_context = [
        frozen.synchronized_slot_randomization(values[index], draws=draws, seed=seed)
        for index in range(context_count)
    ]
    return {
        "overall": overall,
        "by_context": by_context,
        "profile_order": "context_major_then_depth",
        "context_count": context_count,
        "depth_count": depth_count,
    }


def _outcome_pattern(primary: Mapping[str, Mapping[str, Any]]) -> str:
    left = primary[MODEL_ROLES[0]]
    right = primary[MODEL_ROLES[1]]
    left_excess = float(left["excess_over_null_mean"])
    right_excess = float(right["excess_over_null_mean"])
    if left_excess * right_excess < 0.0:
        return "opposite_null_centered_direction"
    if bool(left["holm_reject"]) and bool(right["holm_reject"]) and min(left_excess, right_excess) > 0:
        return "dual_model_common_suffix_recurrence_candidate"
    if (
        bool(left["holm_reject"])
        and not bool(right["holm_reject"])
        and left_excess > 0.0
    ):
        return "gemma_only_common_suffix_heterogeneity"
    if (
        bool(right["holm_reject"])
        and not bool(left["holm_reject"])
        and right_excess > 0.0
    ):
        return "olmo_only_common_suffix_carryover"
    return "no_common_suffix_slot_recurrence"


def _load_t3_reference(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    spec = config["raw_t3_reference"]
    receipt_path = (root / CONFIG_PATH.parent / str(spec["analysis_receipt"])).resolve()
    manifest_path = (root / CONFIG_PATH.parent / str(spec["public_manifest"])).resolve()
    for path in (receipt_path, manifest_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise base.ProtocolError("T3 reference escaped repository") from exc
        base._require(path.is_file(), f"Missing T3 reference: {path.name}")
    receipt = base._read_json(receipt_path, "T3 analysis receipt")
    public_manifest = base._read_json(manifest_path, "T3 public manifest")
    base._require(receipt.get("protocol_id") == spec["protocol_id"], "T3 protocol mismatch")
    base._require(receipt.get("outcome_pattern") == spec["outcome_pattern"], "T3 outcome mismatch")
    base._require(public_manifest.get("protocol_id") == spec["protocol_id"], "T3 manifest mismatch")
    base._require(public_manifest.get("status") == "pass", "T3 public manifest is not pass")
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
    context_order = [str(value) for value in config["input"]["context_order"]]
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
    rows: list[dict[str, Any]] = []
    randomization_by_role: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        result = validated[role]
        tensors = np.stack(
            [
                frozen._factor_tensor(
                    result["activations"][:, context_index, :, :],
                    panel_items,
                    family_order,
                    slot_order,
                )
                for context_index in range(len(context_order))
            ],
            axis=0,
        )
        randomization = synchronized_context_depth_randomization(tensors, draws=draws, seed=seed)
        randomization_by_role[role] = randomization
        depth_count = len(result["layers"])
        for context_index, context_id in enumerate(context_order):
            secondary_context = randomization["by_context"][context_index]
            for depth_position, layer in enumerate(result["layers"]):
                flat_position = context_index * depth_count + depth_position
                geometry = frozen.factor_geometry(tensors[context_index, :, :, depth_position, :])
                matrix = tensors[context_index, :, :, depth_position, :].reshape(
                    len(family_order) * len(slot_order), -1
                )
                rows.append(
                    {
                        "model_label": role,
                        "context_id": context_id,
                        "context_index": context_index,
                        "layer": int(layer),
                        "layer_fraction": float(
                            result["receipt"]["capture"]["fractions"][depth_position]
                        ),
                        **geometry,
                        "slot_null_mean": float(
                            randomization["overall"]["per_depth_null_mean"][flat_position]
                        ),
                        "slot_excess_over_null_mean": float(
                            geometry["slot_fraction_after_family_centering"]
                            - randomization["overall"]["per_depth_null_mean"][flat_position]
                        ),
                        "slot_randomization_p_greater_equal": float(
                            randomization["overall"]["per_depth_p_greater_equal"][flat_position]
                        ),
                        "context_all_depth_statistic": float(secondary_context["observed_omnibus"]),
                        "context_all_depth_p_secondary": float(
                            secondary_context["omnibus_p_greater_equal"]
                        ),
                        "mean_activation_rms": float(
                            np.mean(np.sqrt(np.mean(np.square(matrix, dtype=np.float64), axis=1)))
                        ),
                        "multiplicity_decision_authorized": False,
                    }
                )

    holm = base.holm_adjust(
        {
            role: float(randomization_by_role[role]["overall"]["omnibus_p_greater_equal"])
            for role in MODEL_ROLES
        },
        alpha=float(endpoint["familywise_alpha"]),
    )
    t3_reference = _load_t3_reference(root, config)
    primary_summary: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        cell = randomization_by_role[role]
        overall = cell["overall"]
        raw = t3_reference["primary_results"][role]
        context_summaries = {
            context_id: {
                "statistic": float(cell["by_context"][index]["observed_omnibus"]),
                "null_mean": float(cell["by_context"][index]["null_omnibus_mean"]),
                "excess_over_null_mean": float(
                    cell["by_context"][index]["omnibus_excess_over_null_mean"]
                ),
                "raw_p_secondary": float(
                    cell["by_context"][index]["omnibus_p_greater_equal"]
                ),
                "depth_profile": list(cell["by_context"][index]["observed_depth_profile"]),
                "multiplicity_decision_authorized": False,
            }
            for index, context_id in enumerate(context_order)
        }
        primary_summary[role] = {
            "statistic": float(overall["observed_omnibus"]),
            "null_mean": float(overall["null_omnibus_mean"]),
            "excess_over_null_mean": float(overall["omnibus_excess_over_null_mean"]),
            "raw_p": float(overall["omnibus_p_greater_equal"]),
            "holm_adjusted_p": float(holm[role]["adjusted_p"]),
            "holm_reject": bool(holm[role]["reject"]),
            "context_depth_profile": list(overall["observed_depth_profile"]),
            "context_summaries_secondary": context_summaries,
            "t3_raw_reference_descriptive": {
                "statistic": float(raw["statistic"]),
                "null_mean": float(raw["null_mean"]),
                "excess_over_null_mean": float(raw["excess_over_null_mean"]),
                "suffix_minus_raw_statistic": float(
                    overall["observed_omnibus"] - float(raw["statistic"])
                ),
                "inferential_pooling": False,
            },
        }
    pattern = _outcome_pattern(primary_summary)

    stage = base._new_stage(output)
    try:
        base._write_jsonl(stage / "context_layer_statistics.jsonl", rows)
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
            "analysis_role": "frozen_joint_exploratory_observational_common_suffix_carryover",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "inputs": input_receipts,
            "t3_raw_reference": t3_reference,
            "primary_endpoint": endpoint,
            "primary_results": primary_summary,
            "outcome_pattern": pattern,
            "outcome_pattern_definition": config["outcome_pattern_registry"][pattern],
            "context_layer_row_count": len(rows),
            "context_order": context_order,
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
            "# Multifamily common-suffix carryover v0 result\n",
            "\n",
            f"Outcome pattern: `{pattern}`.\n",
            "\n",
            "| Model | Two-context all-depth statistic | Null mean | Excess | Raw p | Holm p | Reject |\n",
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
                "This frozen observational endpoint reads both exact common suffix "
                "tokens. T3 raw-glyph values are descriptive references only. The "
                "result is not semantic, causal, confirmatory, tokenizer-equivalent, "
                "backend-equivalent, or a Phase I gate decision.\n",
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
    rows = base._read_jsonl(directory / "context_layer_statistics.jsonl", "context/layer rows")
    base._require(
        len(rows) == int(receipt["context_layer_row_count"]),
        "Context/layer row count mismatch",
    )
    base._require(
        {str(row["model_label"]) for row in rows} == set(MODEL_ROLES),
        "Analysis model roster mismatch",
    )
    base._require(
        not any(bool(row["multiplicity_decision_authorized"]) for row in rows),
        "A context/layer decision was authorized",
    )
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "outcome_pattern": receipt["outcome_pattern"],
        "context_layer_row_count": len(rows),
        "scientific_confirmation": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-freeze", help="Validate the public protocol freeze")

    preflight = subparsers.add_parser(
        "tokenizer-preflight", help="Replay one tokenizer-only common-suffix contract"
    )
    preflight.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    preflight.add_argument("--model-path", type=Path, required=True)

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
