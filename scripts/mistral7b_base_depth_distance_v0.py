#!/usr/bin/env python3
"""Run the frozen Mistral 7B base depth-by-distance v0 study.

The endpoint was selected after the T6 dense-CUDA profiles were known.  It is
prospective only for one previously unobserved Mistral 7B v0.3 base-model cell.
The study performs observational ``resid_post`` capture only: no intervention,
generation, protected-target access, or base/instruct effect decision is made.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_dense_cuda_carrier_distance_v0 as t6  # noqa: E402


t5 = t6.t5
frozen = t6.frozen
base = t6.base
PROTOCOL_ID = "glyphprobe-mistral7b-base-depth-distance-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/mistral7b_base_depth_distance_v0.json")
CONFIG_PATH = Path("configs/mistral7b_base_depth_distance_v0.yaml")
PREFLIGHT_PATH = Path(
    "validation/mistral7b_base_depth_distance_v0/engineering_preflight.json"
)
MODEL_ROLES = ("mistral7b_base_v03",)
RUN_FILES = t5.RUN_FILES
FAILED_RUN_FILES = t5.FAILED_RUN_FILES
ANALYSIS_FILES = t5.ANALYSIS_FILES
FROZEN_ASSET_PATHS = (
    "artifacts/multifamily_dense_cuda_carrier_distance_v0/PUBLIC_MANIFEST.json",
    "artifacts/multifamily_dense_cuda_carrier_distance_v0/analysis/analysis_receipt.json",
    "artifacts/multifamily_dense_cuda_carrier_distance_v0/analysis/carrier_distance_layer_statistics.jsonl",
    "configs/mistral7b_base_depth_distance_v0.yaml",
    "data/emoji_panels/e1_animals.yaml",
    "data/emoji_panels/e1_food.yaml",
    "data/emoji_panels/e1_sky_moon.yaml",
    "data/emoji_panels/e1_social.yaml",
    "data/emoji_panels/e1_transport.yaml",
    "docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md",
    "docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md",
    "scripts/mistral7b_base_depth_distance_v0.py",
    "scripts/multifamily_carrier_distance_v0.py",
    "scripts/multifamily_dense_cuda_carrier_distance_v0.py",
    "src/glyphprobe/backends/transformers_backend.py",
    "tests/test_mistral7b_base_depth_distance_v0.py",
    "validation/mistral7b_base_depth_distance_v0/engineering_preflight.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@contextlib.contextmanager
def _delegated_t6_surface() -> Iterator[None]:
    """Bind T6's sealed CUDA runner to the single frozen base-model role."""

    replacements = {
        "PROTOCOL_ID": PROTOCOL_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "MANIFEST_PATH": MANIFEST_PATH,
        "CONFIG_PATH": CONFIG_PATH,
        "PREFLIGHT_PATH": PREFLIGHT_PATH,
        "MODEL_ROLES": MODEL_ROLES,
    }
    originals = {name: getattr(t6, name) for name in replacements}
    try:
        for name, value in replacements.items():
            setattr(t6, name, value)
        yield
    finally:
        for name, value in originals.items():
            setattr(t6, name, value)


def build_freeze_manifest() -> dict[str, Any]:
    """Bind code, protocol, zero-forward preflight, and local artifact hash."""

    root = _repo_root()
    output = root / MANIFEST_PATH
    preflight = base._read_json(root / PREFLIGHT_PATH, "engineering preflight")
    base._require(preflight.get("protocol_id") == PROTOCOL_ID, "Preflight protocol mismatch")
    base._require(preflight.get("model_forward_calls") == 0, "Preflight used a model forward")
    base._require(preflight.get("model_weights_loaded") is False, "Preflight loaded weights")
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSET_PATHS:
        path = root / relative
        base._require(path.is_file(), f"Missing frozen asset candidate: {relative}")
        assets[relative] = base._sha256_file(path)
    model_artifacts = preflight.get("model_artifacts")
    base._require(isinstance(model_artifacts, dict), "Preflight omitted model artifacts")
    base._require(tuple(model_artifacts) == MODEL_ROLES, "Preflight model order mismatch")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t7_model_forward",
        "frozen_assets": assets,
        "implementation": frozen.implementation_receipt(),
        "model_artifacts": model_artifacts,
        "engineering_preflight_sha256": base._sha256_file(root / PREFLIGHT_PATH),
        "model_forward_calls_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "protected_target_files_opened_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
    }
    base._write_json(output, payload)
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "manifest_path": MANIFEST_PATH.as_posix(),
        "manifest_sha256": base._sha256_file(output),
        "frozen_asset_count": len(assets),
        "model_roles": list(MODEL_ROLES),
    }


def audit_freeze() -> dict[str, Any]:
    with _delegated_t6_surface():
        result = t6.audit_freeze()
    preflight = base._read_json(_repo_root() / PREFLIGHT_PATH, "engineering preflight")
    base._require(preflight.get("model_forward_calls") == 0, "Preflight forward count changed")
    base._require(preflight.get("model_weights_loaded") is False, "Preflight weight gate changed")
    return result


def tokenizer_preflight(model_label: str, model_path: Path) -> dict[str, Any]:
    with _delegated_t6_surface():
        return t6.tokenizer_preflight(model_label, model_path)


def run_model(model_label: str, model_path: Path, output: Path) -> dict[str, Any]:
    with _delegated_t6_surface():
        return t6.run_model(model_label, model_path, output)


def validate_run(directory: Path) -> dict[str, Any]:
    with _delegated_t6_surface():
        return t6.validate_run(directory)


def _load_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    with _delegated_t6_surface():
        return t6._load_authority()


def _panel(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    return t6._panel(config)


def engineering_preflight(model_path: Path) -> dict[str, Any]:
    """Inspect a complete local snapshot without loading language-model weights."""

    root = _repo_root()
    config = base._read_yaml(root / CONFIG_PATH, "frozen config candidate")
    base._require(config.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    base._require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model order mismatch")
    role = MODEL_ROLES[0]
    model_spec = config["models"][role]
    snapshot = model_path.resolve()
    base._require(snapshot.is_dir(), "Model snapshot is not a directory")
    base._require(snapshot.name == str(model_spec["revision"]), "Snapshot revision directory mismatch")

    from glyphprobe.provenance import model_artifact_receipt
    from safetensors import safe_open
    from transformers import AutoConfig, AutoTokenizer

    artifact = model_artifact_receipt(snapshot)
    expected_files = [str(value) for value in model_spec["expected_artifact_files"]]
    base._require(
        sorted(artifact["files"]) == sorted(expected_files),
        "Local artifact file roster mismatch",
    )
    index = base._read_json(snapshot / "model.safetensors.index.json", "weight index")
    weight_map = index.get("weight_map")
    base._require(isinstance(weight_map, dict) and bool(weight_map), "Weight index is empty")
    shard_names = sorted({str(value) for value in weight_map.values()})
    base._require(
        shard_names == sorted(str(value) for value in model_spec["expected_weight_shards"]),
        "Weight shard roster mismatch",
    )
    metadata = index.get("metadata")
    base._require(isinstance(metadata, dict), "Weight index metadata is absent")
    index_total_size = int(metadata["total_size"])
    base._require(
        index_total_size == int(model_spec["expected_index_total_size"]),
        "Weight index total size mismatch",
    )

    observed_keys: set[str] = set()
    dtype_counts: dict[str, int] = {}
    indexed_parameter_elements = 0
    for shard_name in shard_names:
        with safe_open(snapshot / shard_name, framework="pt", device="cpu") as handle:
            for key in handle.keys():
                base._require(key not in observed_keys, "Duplicate tensor key across shards")
                observed_keys.add(key)
                tensor_slice = handle.get_slice(key)
                shape = [int(value) for value in tensor_slice.get_shape()]
                dtype = str(tensor_slice.get_dtype())
                elements = int(math.prod(shape))
                indexed_parameter_elements += elements
                dtype_counts[dtype] = dtype_counts.get(dtype, 0) + elements
    base._require(observed_keys == set(weight_map), "Safetensor keys differ from weight index")
    base._require(
        indexed_parameter_elements == int(model_spec["expected_parameter_count"]),
        "Indexed parameter count mismatch",
    )
    base._require(set(dtype_counts) == {"BF16"}, "Safetensor dtype roster mismatch")

    architecture = AutoConfig.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False
    )
    base._require(architecture.model_type == model_spec["expected_model_type"], "Model type mismatch")
    base._require(
        int(architecture.num_hidden_layers) == int(model_spec["expected_num_layers"]),
        "Layer count mismatch",
    )
    base._require(
        int(architecture.hidden_size) == int(model_spec["expected_model_dim"]),
        "Model width mismatch",
    )
    base._require(
        int(architecture.vocab_size) == int(model_spec["expected_vocab_size"]),
        "Model vocabulary mismatch",
    )

    tokenizer = AutoTokenizer.from_pretrained(
        snapshot,
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    base._require(
        int(getattr(tokenizer, "vocab_size", len(tokenizer)))
        == int(model_spec["expected_tokenizer_vocab_size"]),
        "Tokenizer vocabulary mismatch",
    )

    def tokenized(text: str) -> SimpleNamespace:
        ids = [int(value) for value in tokenizer.encode(text, add_special_tokens=False)]
        return SimpleNamespace(
            token_ids=ids,
            tokens=[str(value) for value in tokenizer.convert_ids_to_tokens(ids)],
        )

    panel_items = _panel(config)
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
    tokenization = t6.validate_carrier_tokenizations(
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

    packages = (
        "glyphprobe",
        "torch",
        "transformers",
        "numpy",
        "pydantic",
        "PyYAML",
        "orjson",
        "safetensors",
    )
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    for package, expected in config["runtime"]["critical_versions"].items():
        base._require(versions.get(package) == str(expected), f"Runtime version mismatch: {package}")
    import torch

    base._require(torch.cuda.is_available(), "CUDA is unavailable at preflight")
    base._require(torch.cuda.is_bf16_supported(), "CUDA BF16 is unsupported")
    base._require(
        str(torch.cuda.get_device_name(0)) == str(config["runtime"]["hardware_pin"]),
        "CUDA hardware identity mismatch",
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "static_preflight_pass_execution_gate_pending",
        "observed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "selection_provenance": config["selection_provenance"],
        "furnace_static_environment": {
            "host_role": "furnace",
            "gpu": str(torch.cuda.get_device_name(0)),
            "gpu_memory_total_mib": int(
                torch.cuda.get_device_properties(0).total_memory // (1024 * 1024)
            ),
            "versions": versions,
            "cuda_available": True,
            "bfloat16_supported": True,
            "local_files_only": True,
        },
        "official_model_metadata": {
            "canonical_model_id": model_spec["canonical_model_id"],
            "revision": model_spec["revision"],
            "public": True,
            "gated": False,
            "metadata_checked_with": "huggingface_hub_hf_models_info_1.27.0",
            "full_remote_storage_bytes": 28992746844,
            "full_remote_dry_run_bytes_rounded": "29.0G",
            "excluded_duplicate_files": model_spec["excluded_remote_files"],
        },
        "model_artifacts": {
            role: {
                "canonical_model_id": model_spec["canonical_model_id"],
                "revision": model_spec["revision"],
                "file_policy": model_spec["artifact_file_policy"],
                "file_names": expected_files,
                "file_count": int(artifact["file_count"]),
                "total_bytes": int(artifact["total_bytes"]),
                "manifest_sha256": str(artifact["manifest_sha256"]),
                "indexed_parameter_elements": indexed_parameter_elements,
                "indexed_parameter_dtype_elements": dtype_counts,
                "index_total_size": index_total_size,
                "model_type": architecture.model_type,
                "expected_model_class": model_spec["expected_model_class"],
                "num_hidden_layers": int(architecture.num_hidden_layers),
                "hidden_size": int(architecture.hidden_size),
                "model_vocab_size": int(architecture.vocab_size),
                "artifact_complete": True,
            }
        },
        "tokenizer_preflight": {
            "panel_items": len(panel_items),
            "contexts": ["raw", "article_a_x8", "pipe_x8"],
            role: {
                "tokenizer_class": type(tokenizer).__name__,
                "tokenizer_vocab_size": int(getattr(tokenizer, "vocab_size", len(tokenizer))),
                "raw_count_histogram": tokenization["raw"][
                    "observed_item_token_count_histogram"
                ],
                "raw_unique_sequence_count": tokenization["raw"]["unique_sequence_count"],
                "raw_shared_prefix_token_ids": tokenization["raw"]["shared_prefix_token_ids"],
                "raw_ordered_sequence_sha256": tokenization["raw"]["ordered_sequence_sha256"],
                "article_a_token_id": tokenization["carriers"]["article_a"]["carrier_token_id"],
                "article_a_combined_sequence_sha256": tokenization["carriers"]["article_a"][
                    "ordered_sequence_sha256"
                ],
                "pipe_token_id": tokenization["carriers"]["pipe"]["carrier_token_id"],
                "pipe_combined_sequence_sha256": tokenization["carriers"]["pipe"][
                    "ordered_sequence_sha256"
                ],
                "raw_prefix_preserved_per_carrier": {
                    carrier: tokenization["carriers"][carrier]["raw_prefix_preserved_count"]
                    for carrier in tokenization["carrier_order"]
                },
                "roundtrip_exact_per_carrier": {
                    carrier: tokenization["carriers"][carrier]["roundtrip_exact_count"]
                    for carrier in tokenization["carrier_order"]
                },
            },
        },
        "authorization": {
            "new_model_download_explicitly_authorized_in_current_user_thread": True,
            "furnace_experiment_continuation_explicitly_authorized": True,
        },
        "model_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "protected_target_files_opened": 0,
        "model_weights_loaded": False,
        "scientific_result_available": False,
        "machine_local_model_paths_published": False,
    }


def depth_distance_randomization(
    tensor: np.ndarray,
    *,
    weights: Sequence[float],
    early_depth_index: int,
    late_depth_indices: Sequence[int],
    draws: int,
    seed: int,
) -> dict[str, Any]:
    """Return the fixed recurrence plus early-minus-late attenuation IUT."""

    values = np.asarray(tensor, dtype=np.float64)
    base._require(values.ndim == 6, "Tensor must be family x slot x carrier x distance x depth x width")
    family_count, slot_count, carrier_count, distance_count, depth_count, width = values.shape
    base._require(family_count == 5 and slot_count == 10, "Panel shape mismatch")
    base._require(carrier_count == 2 and distance_count == 4, "Carrier/distance shape mismatch")
    base._require(depth_count == 5 and width > 0, "Depth/width shape mismatch")
    early = int(early_depth_index)
    late = tuple(int(value) for value in late_depth_indices)
    base._require(early == 0, "Early depth must be the first fixed fraction")
    base._require(late == (1, 2, 3, 4), "Late depths must be the four remaining fractions")
    contrast = np.asarray([float(value) for value in weights], dtype=np.float64)
    base._require(contrast.shape == (distance_count,), "Distance contrast width mismatch")
    base._require(abs(float(contrast.sum())) <= 1e-12, "Distance contrast must sum to zero")

    flattened = values.reshape(
        family_count,
        slot_count,
        carrier_count * distance_count * depth_count,
        width,
    )
    observed_flat, randomized_flat = t5.synchronized_slot_profiles(
        flattened, draws=draws, seed=seed
    )
    observed = observed_flat.reshape(carrier_count, distance_count, depth_count)
    randomized = randomized_flat.reshape(draws, carrier_count, distance_count, depth_count)

    distance1_observed = float(observed[:, 0, :].mean())
    distance1_null = randomized[:, :, 0, :].mean(axis=(1, 2))
    attenuation_by_depth = np.mean(
        np.sum(observed * contrast[None, :, None], axis=1), axis=0
    )
    attenuation_by_depth_null = np.mean(
        np.sum(randomized * contrast[None, None, :, None], axis=2), axis=1
    )
    interaction_observed = float(
        attenuation_by_depth[early] - attenuation_by_depth[list(late)].mean()
    )
    interaction_null = (
        attenuation_by_depth_null[:, early]
        - attenuation_by_depth_null[:, list(late)].mean(axis=1)
    )
    all_depth_observed = float(attenuation_by_depth.mean())
    all_depth_null = attenuation_by_depth_null.mean(axis=1)
    tail_observed = float(observed[:, -1, :].mean())
    tail_null = randomized[:, :, -1, :].mean(axis=(1, 2))

    recurrence = t5._one_sided_summary(distance1_observed, distance1_null)
    interaction = t5._one_sided_summary(interaction_observed, interaction_null)
    return {
        "draws": int(draws),
        "seed": int(seed),
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
        "distance1_recurrence_component": recurrence,
        "early_minus_late_attenuation_component": interaction,
        "intersection_union_raw_p": max(
            float(recurrence["raw_p"]), float(interaction["raw_p"])
        ),
        "attenuation_by_depth": [float(value) for value in attenuation_by_depth],
        "early_attenuation": float(attenuation_by_depth[early]),
        "late_mean_attenuation": float(attenuation_by_depth[list(late)].mean()),
        "all_depth_attenuation_secondary": t5._one_sided_summary(
            all_depth_observed, all_depth_null
        ),
        "distance8_tail_secondary": t5._one_sided_summary(tail_observed, tail_null),
        "distance_profile": observed.mean(axis=(0, 2)),
        "depth_distance_profile": observed.mean(axis=0).T,
        "carrier_distance_profile": observed.mean(axis=2),
    }


def _outcome_pattern(primary: Mapping[str, Any], *, alpha: float) -> str:
    recurrence = float(primary["distance1_recurrence_component"]["raw_p"]) <= alpha
    interaction = float(primary["early_minus_late_attenuation_component"]["raw_p"]) <= alpha
    if recurrence and interaction:
        return "recurrence_and_early_depth_attenuation_excess"
    if recurrence:
        return "recurrence_without_early_depth_attenuation_excess"
    if interaction:
        return "early_depth_attenuation_excess_without_recurrence"
    return "neither_primary_component"


def _load_prior_t6_reference(config: Mapping[str, Any]) -> dict[str, Any]:
    root = _repo_root()
    spec = config["prior_t6_reference"]
    paths = {
        "analysis_receipt": (root / CONFIG_PATH.parent / str(spec["analysis_receipt"])).resolve(),
        "profile_rows": (root / CONFIG_PATH.parent / str(spec["profile_rows"])).resolve(),
        "public_manifest": (root / CONFIG_PATH.parent / str(spec["public_manifest"])).resolve(),
    }
    for path in paths.values():
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise base.ProtocolError("T6 reference escaped repository") from exc
        base._require(path.is_file(), f"Missing T6 reference: {path.name}")
    receipt = base._read_json(paths["analysis_receipt"], "T6 analysis receipt")
    public = base._read_json(paths["public_manifest"], "T6 public manifest")
    base._require(receipt.get("protocol_id") == spec["protocol_id"], "T6 protocol mismatch")
    base._require(receipt.get("outcome_pattern") == spec["outcome_pattern"], "T6 outcome mismatch")
    base._require(public.get("protocol_id") == spec["protocol_id"], "T6 manifest mismatch")
    base._require(public.get("status") == "pass", "T6 public manifest is not pass")
    return {
        "role": spec["role"],
        "endpoint_selected_after_t6_profiles_known": True,
        "inferential_pooling": False,
        "analysis_receipt_sha256": base._sha256_file(paths["analysis_receipt"]),
        "profile_rows_sha256": base._sha256_file(paths["profile_rows"]),
        "public_manifest_sha256": base._sha256_file(paths["public_manifest"]),
        "outcome_pattern": receipt["outcome_pattern"],
        "mistral_instruct_primary": receipt["primary_results"]["mistral7b_instruct_v03"],
    }


def analyze_run(run_directory: Path, output: Path) -> dict[str, Any]:
    manifest, config, verified_assets = _load_authority()
    audit = audit_freeze()
    role = MODEL_ROLES[0]
    result = validate_run(run_directory)
    base._require(result["status"] == "pass", "Cannot analyze failed base-model run")
    receipt = result["receipt"]
    base._require(receipt["model_label"] == role, "Role binding mismatch")
    base._require(
        receipt["freeze"]["manifest_sha256"] == audit["manifest_sha256"],
        "Freeze manifest mismatch",
    )
    pin = manifest["model_artifacts"][role]
    for field in ("manifest_sha256", "file_count", "total_bytes"):
        base._require(receipt["model"]["artifact"][field] == pin[field], f"Artifact pin mismatch: {field}")

    panel_items = _panel(config)
    family_order = [str(value) for value in config["panel"]["family_order"]]
    slot_order = [int(value) for value in config["panel"]["slot_order"]]
    carrier_order = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    tensor = frozen._factor_tensor(result["activations"], panel_items, family_order, slot_order)
    endpoint = config["primary_endpoint"]
    randomization = depth_distance_randomization(
        tensor,
        weights=endpoint["distance_contrast_weights"],
        early_depth_index=int(endpoint["early_depth_index"]),
        late_depth_indices=endpoint["late_depth_indices"],
        draws=int(endpoint["randomization_draws"]),
        seed=int(endpoint["seed"]),
    )
    alpha = float(endpoint["alpha"])
    primary = {
        "distance1_recurrence_component": randomization["distance1_recurrence_component"],
        "early_minus_late_attenuation_component": randomization[
            "early_minus_late_attenuation_component"
        ],
        "intersection_union_raw_p": float(randomization["intersection_union_raw_p"]),
        "reject_at_alpha": bool(randomization["intersection_union_raw_p"] <= alpha),
        "attenuation_by_depth": randomization["attenuation_by_depth"],
        "early_attenuation": float(randomization["early_attenuation"]),
        "late_mean_attenuation": float(randomization["late_mean_attenuation"]),
        "all_depth_attenuation_secondary": randomization["all_depth_attenuation_secondary"],
        "distance8_tail_secondary": randomization["distance8_tail_secondary"],
        "distance_profile": [float(value) for value in randomization["distance_profile"]],
        "depth_distance_profile": [
            [float(value) for value in row] for row in randomization["depth_distance_profile"]
        ],
        "carrier_distance_profile": [
            [float(value) for value in row] for row in randomization["carrier_distance_profile"]
        ],
    }
    pattern = _outcome_pattern(primary, alpha=alpha)
    rows: list[dict[str, Any]] = []
    for carrier_index, carrier_id in enumerate(carrier_order):
        for distance_index, distance in enumerate(distances):
            for depth_index, layer in enumerate(result["layers"]):
                geometry = frozen.factor_geometry(
                    tensor[:, :, carrier_index, distance_index, depth_index, :]
                )
                rows.append(
                    {
                        "model_label": role,
                        "carrier_id": carrier_id,
                        "carrier_index": carrier_index,
                        "distance": distance,
                        "distance_index": distance_index,
                        "layer": int(layer),
                        "layer_fraction": float(receipt["capture"]["fractions"][depth_index]),
                        **geometry,
                        "slot_null_mean": float(
                            randomization["null_profile_mean"][
                                carrier_index, distance_index, depth_index
                            ]
                        ),
                        "slot_randomization_p_greater_equal": float(
                            randomization["profile_p_greater_equal"][
                                carrier_index, distance_index, depth_index
                            ]
                        ),
                        "multiplicity_decision_authorized": False,
                    }
                )

    stage = base._new_stage(output)
    try:
        base._write_jsonl(stage / "carrier_distance_layer_statistics.jsonl", rows)
        analysis_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "prospective_post_t6_selected_unseen_base_model_cell",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "input": {
                "run_receipt_sha256": base._sha256_file(run_directory / "run_receipt.json"),
                "run_ledger_sha256": base._sha256_file(run_directory / "SHA256SUMS"),
            },
            "prior_t6_reference": _load_prior_t6_reference(config),
            "primary_endpoint": endpoint,
            "primary_result": primary,
            "outcome_pattern": pattern,
            "outcome_pattern_definition": config["outcome_pattern_registry"][pattern],
            "carrier_distance_layer_row_count": len(rows),
            "carrier_order": carrier_order,
            "distance_order": distances,
            "randomization_draws": int(endpoint["randomization_draws"]),
            "randomization_seed": int(endpoint["seed"]),
            "multiplicity_adjustment": "none_one_model_one_iut",
            "intervention_calls": 0,
            "generation_calls": 0,
            "protected_target_files_opened": 0,
            "scientific_confirmation": False,
            "instruction_tuning_effect_authorized": False,
            "phase_i_gate_closed": False,
        }
        base._write_json(stage / "analysis_receipt.json", analysis_receipt)
        base._atomic_write(
            stage / "report.md",
            (
                "# Mistral 7B base depth-by-distance v0 result\n\n"
                f"Outcome pattern: `{pattern}`.\n\n"
                "| d=1 recurrence p | early-minus-late attenuation p | IUT p | Reject |\n"
                "|---:|---:|---:|---|\n"
                f"| {primary['distance1_recurrence_component']['raw_p']:.9f} | "
                f"{primary['early_minus_late_attenuation_component']['raw_p']:.9f} | "
                f"{primary['intersection_union_raw_p']:.9f} | "
                f"{str(primary['reject_at_alpha']).lower()} |\n\n"
                "This selected post-T6 cell cannot establish an instruction-tuning effect, "
                "independent confirmation, semantics, mechanism, causality, or a Phase I gate.\n"
            ).encode("utf-8"),
        )
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
        directory / "carrier_distance_layer_statistics.jsonl", "carrier/distance/layer rows"
    )
    base._require(len(rows) == int(receipt["carrier_distance_layer_row_count"]), "Row count mismatch")
    base._require({str(row["model_label"]) for row in rows} == set(MODEL_ROLES), "Model roster mismatch")
    base._require(
        not any(bool(row["multiplicity_decision_authorized"]) for row in rows),
        "A secondary row was authorized as a decision",
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
    engineering = subparsers.add_parser("engineering-preflight")
    engineering.add_argument("--model-path", type=Path, required=True)
    subparsers.add_parser("build-freeze-manifest")
    subparsers.add_parser("audit-freeze")
    preflight = subparsers.add_parser("tokenizer-preflight")
    preflight.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    preflight.add_argument("--model-path", type=Path, required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    validate_one = subparsers.add_parser("validate-run")
    validate_one.add_argument("directory", type=Path)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--run", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    validate_joint = subparsers.add_parser("validate-analysis")
    validate_joint.add_argument("directory", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "engineering-preflight":
            payload = engineering_preflight(args.model_path)
        elif args.command == "build-freeze-manifest":
            payload = build_freeze_manifest()
        elif args.command == "audit-freeze":
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
            payload = analyze_run(args.run, args.output)
        elif args.command == "validate-analysis":
            payload = validate_analysis(args.directory)
        else:  # pragma: no cover
            raise AssertionError(args.command)
        print(base._json_bytes(payload, pretty=True).decode("utf-8"))
    except (OSError, ValueError, base.ProtocolError, t5.PublishedRunFailure) as exc:
        print(base._json_bytes({"status": "fail", "error": str(exc)}, pretty=True).decode("utf-8"))
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
