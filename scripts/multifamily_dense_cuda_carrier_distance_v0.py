#!/usr/bin/env python3
"""Run the frozen post-T5 dense CUDA carrier-distance v0 study.

The study reuses T5's fixed 5 x 10 public emoji panel, two repeated-token
carriers, distances 1/2/4/8, five depth fractions, and model-level
recurrence-plus-attenuation intersection-union endpoint.  It adds four
prospectively frozen dense Transformers/CUDA cells.  No intervention,
generation, protected target, or cross-model magnitude decision is used.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_carrier_distance_v0 as t5  # noqa: E402

from glyphprobe.backends.transformers_backend import TransformersBackend  # noqa: E402
from glyphprobe.config import BackendConfig  # noqa: E402


frozen = t5.frozen
base = t5.base
PROTOCOL_ID = "glyphprobe-multifamily-dense-cuda-carrier-distance-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/multifamily_dense_cuda_carrier_distance_v0.json")
CONFIG_PATH = Path("configs/multifamily_dense_cuda_carrier_distance_v0.yaml")
PREFLIGHT_PATH = Path(
    "validation/multifamily_dense_cuda_carrier_distance_v0/engineering_preflight.json"
)
MODEL_ROLES = (
    "gemma2_2b_it",
    "gemma3_4b_it",
    "mistral7b_instruct_v03",
    "gemma3_12b_it",
)
RUN_FILES = t5.RUN_FILES
FAILED_RUN_FILES = t5.FAILED_RUN_FILES
ANALYSIS_FILES = t5.ANALYSIS_FILES
FROZEN_ASSET_PATHS = (
    "artifacts/multifamily_carrier_distance_v0/PUBLIC_MANIFEST.json",
    "artifacts/multifamily_carrier_distance_v0/analysis/analysis_receipt.json",
    "configs/multifamily_dense_cuda_carrier_distance_v0.yaml",
    "data/emoji_panels/e1_animals.yaml",
    "data/emoji_panels/e1_food.yaml",
    "data/emoji_panels/e1_sky_moon.yaml",
    "data/emoji_panels/e1_social.yaml",
    "data/emoji_panels/e1_transport.yaml",
    "docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md",
    "docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md",
    "scripts/multifamily_carrier_distance_v0.py",
    "scripts/multifamily_dense_cuda_carrier_distance_v0.py",
    "src/glyphprobe/backends/transformers_backend.py",
    "tests/test_multifamily_dense_cuda_carrier_distance_v0.py",
    "validation/multifamily_dense_cuda_carrier_distance_v0/engineering_preflight.json",
)


class DenseCudaTransformersBackend(TransformersBackend):
    """Transformers adapter with explicit Gemma 3 text-block discovery."""

    _BLOCK_PATHS = ("model.language_model.layers", *TransformersBackend._BLOCK_PATHS)

    def __init__(self, delegated_config: Any):
        translated = BackendConfig(
            kind="transformers",
            model=str(delegated_config.model),
            revision=delegated_config.revision,
            device=str(delegated_config.device),
            dtype=str(delegated_config.dtype),
            trust_remote_code=bool(delegated_config.trust_remote_code),
            local_files_only=bool(delegated_config.local_files_only),
            add_special_tokens=bool(delegated_config.add_special_tokens),
        )
        super().__init__(translated)
        self.model_config: dict[str, Any] = {}
        self.resolved_device = str(translated.device)
        self.resolved_dtype = "unloaded"

    def load(self) -> None:
        super().load()
        config = self.model.config
        self.model_config = dict(config.to_dict())
        text_config = getattr(config, "text_config", None)
        if self._d_model is None and getattr(text_config, "hidden_size", None) is not None:
            self._d_model = int(text_config.hidden_size)
        self.resolved_device = str(self.device)
        self.resolved_dtype = str(next(self.model.parameters()).dtype)
        base._require(self.resolved_device == "cuda", "Dense T6 backend did not resolve CUDA")
        base._require(bool(self.torch.cuda.is_available()), "CUDA is not available")
        manifest = base._read_json(_repo_root() / MANIFEST_PATH, "freeze manifest")
        artifact_sha = str((self.model_artifact or {}).get("manifest_sha256"))
        matches = [
            role
            for role in MODEL_ROLES
            if str(manifest["model_artifacts"][role]["manifest_sha256"]) == artifact_sha
        ]
        base._require(len(matches) == 1, "Loaded artifact does not bind one frozen T6 role")
        frozen_config = base._read_yaml(_repo_root() / CONFIG_PATH, "frozen config")
        model_spec = frozen_config["models"][matches[0]]
        base._require(
            type(self.model).__name__ == str(model_spec["expected_model_class"]),
            "Resolved model class mismatch",
        )
        base._require(
            self.block_path == str(model_spec["expected_block_path"]),
            "Resolved decoder-block path mismatch",
        )
        base._require(
            int(getattr(self.tokenizer, "vocab_size", len(self.tokenizer)))
            == int(model_spec["expected_tokenizer_vocab_size"]),
            "Tokenizer vocabulary mismatch",
        )
        base._require(
            str(self.torch.cuda.get_device_name(0))
            == str(frozen_config["runtime"]["hardware_pin"]),
            "CUDA device identity mismatch",
        )

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        receipt.update(
            {
                "resolved_dtype": self.resolved_dtype,
                "torch_version": str(getattr(self.torch, "__version__", "unknown")),
                "cuda_available": bool(self.torch.cuda.is_available()),
                "cuda_device_name": (
                    str(self.torch.cuda.get_device_name(0))
                    if self.torch.cuda.is_available()
                    else None
                ),
            }
        )
        return receipt

    def close(self) -> None:
        torch = self.torch
        self.blocks = []
        self.model = None
        self.tokenizer = None
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
        self._loaded = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _json_sequence_sha256(sequences: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(
        [[int(value) for value in row] for row in sequences],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _shared_prefix(sequences: Sequence[Sequence[int]]) -> list[int]:
    if not sequences:
        return []
    result: list[int] = []
    for index in range(min(len(row) for row in sequences)):
        values = {int(row[index]) for row in sequences}
        if len(values) != 1:
            break
        result.append(values.pop())
    return result


def validate_raw_tokenizations(
    raw_tokenizations: Sequence[Any],
    panel_items: Sequence[Mapping[str, Any]],
    model_spec: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an exact ordered tokenizer roster without loading model weights."""

    contract = model_spec["raw_tokenization_contract"]
    base._require(len(raw_tokenizations) == len(panel_items), "Raw row count mismatch")
    sequences = [tuple(int(value) for value in row.token_ids) for row in raw_tokenizations]
    histogram = Counter(len(row) for row in sequences)
    expected_histogram = {
        int(key): int(value)
        for key, value in contract["expected_item_token_count_histogram"].items()
    }
    base._require(
        dict(sorted(histogram.items())) == dict(sorted(expected_histogram.items())),
        "Raw token-count histogram mismatch",
    )
    base._require(
        len(set(sequences)) == int(contract["expected_unique_sequence_count"]),
        "Raw unique-sequence count mismatch",
    )
    prefix = _shared_prefix(sequences)
    expected_prefix = [int(value) for value in contract["shared_prefix_token_ids"]]
    base._require(prefix == expected_prefix, "Raw shared-prefix contract failed")
    observed_sha = _json_sequence_sha256(sequences)
    base._require(
        observed_sha == str(contract["ordered_sequence_sha256"]),
        "Raw ordered-sequence SHA-256 mismatch",
    )
    return {
        "kind": "exact_ordered_sequence_roster",
        "observed_item_token_count_histogram": {
            str(key): int(value) for key, value in sorted(histogram.items())
        },
        "unique_sequence_count": len(set(sequences)),
        "shared_prefix_token_ids": prefix,
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
    decoder: Any | None = None,
) -> dict[str, Any]:
    """Validate raw preservation and two exact eight-token carrier tails."""

    raw_receipt = validate_raw_tokenizations(raw_tokenizations, panel_items, model_spec)
    raw_sequences = [tuple(int(value) for value in row.token_ids) for row in raw_tokenizations]
    carrier_order = [str(value) for value in input_spec["carrier_order"]]
    base._require(tuple(carrier_tokenizations) == tuple(carrier_order), "Carrier role order mismatch")
    expected_ids = {
        str(key): int(value) for key, value in model_spec["carrier_token_ids"].items()
    }
    expected_hashes = {
        str(key): str(value)
        for key, value in model_spec["combined_sequence_sha256"].items()
    }
    base._require(set(expected_ids) == set(carrier_order), "Carrier-token roster mismatch")
    distances = [int(value) for value in input_spec["distance_order"]]
    base._require(distances == [1, 2, 4, 8], "Distance roster mismatch")
    carriers: dict[str, dict[str, Any]] = {}
    for carrier_id in carrier_order:
        rows = carrier_tokenizations[carrier_id]
        base._require(len(rows) == len(panel_items), f"Carrier row mismatch: {carrier_id}")
        spec = input_spec["carriers"][carrier_id]
        unit = str(spec["unit"])
        repeats = int(spec["repeats"])
        base._require(repeats == 8, "Carrier repeat count mismatch")
        token_id = expected_ids[carrier_id]
        sequences = [tuple(int(value) for value in row.token_ids) for row in rows]
        expected = [raw + (token_id,) * repeats for raw in raw_sequences]
        base._require(sequences == expected, f"Raw-plus-carrier contract failed: {carrier_id}")
        observed_sha = _json_sequence_sha256(sequences)
        base._require(observed_sha == expected_hashes[carrier_id], "Combined sequence hash mismatch")
        decoded_exact: list[bool] | None = None
        if decoder is not None:
            decoded_exact = [
                decoder(sequence) == str(item["glyph"]) + unit * repeats
                for item, sequence in zip(panel_items, sequences, strict=True)
            ]
            base._require(all(decoded_exact), f"Roundtrip contract failed: {carrier_id}")
        carriers[carrier_id] = {
            "unit": unit,
            "repeats": repeats,
            "carrier_token_id": token_id,
            "ordered_sequence_sha256": observed_sha,
            "observed_combined_token_count_histogram": {
                str(key): int(value)
                for key, value in sorted(Counter(len(row) for row in sequences).items())
            },
            "unique_combined_sequence_count": len(set(sequences)),
            "raw_prefix_preserved_count": sum(
                sequence[: len(raw)] == raw
                for raw, sequence in zip(raw_sequences, sequences, strict=True)
            ),
            "roundtrip_exact_count": None if decoded_exact is None else sum(decoded_exact),
            "readout_positions_by_item": [
                [len(raw) + distance - 1 for distance in distances]
                for raw in raw_sequences
            ],
            "token_sequences": [list(row) for row in sequences],
        }
    return {
        "exact_contract": input_spec["exact_contract"],
        "raw": raw_receipt,
        "carrier_order": carrier_order,
        "distance_order": distances,
        "carriers": carriers,
    }


def _runtime_check(config: Mapping[str, Any]) -> dict[str, Any]:
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
    return {
        "versions": versions,
        "backend": "transformers",
        "device_requested": config["runtime"]["device"],
        "dtype_requested": config["runtime"]["dtype"],
        "sitecustomize_loaded": "sitecustomize" in sys.modules,
        "user_site_on_sys_path": any(".local/lib" in item for item in sys.path),
    }


@contextlib.contextmanager
def _delegated_t5_surface() -> Iterator[None]:
    """Temporarily bind T5's sealed run machinery to this new protocol."""

    replacements = {
        "PROTOCOL_ID": PROTOCOL_ID,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "MANIFEST_PATH": MANIFEST_PATH,
        "CONFIG_PATH": CONFIG_PATH,
        "MODEL_ROLES": MODEL_ROLES,
        "validate_raw_tokenizations": validate_raw_tokenizations,
        "validate_carrier_tokenizations": validate_carrier_tokenizations,
    }
    originals = {name: getattr(t5, name) for name in replacements}
    original_backend = t5.frozen.MLXBackend
    original_runtime = t5.base._model_runtime_check
    try:
        for name, value in replacements.items():
            setattr(t5, name, value)
        t5.frozen.MLXBackend = DenseCudaTransformersBackend
        t5.base._model_runtime_check = _runtime_check
        yield
    finally:
        for name, value in originals.items():
            setattr(t5, name, value)
        t5.frozen.MLXBackend = original_backend
        t5.base._model_runtime_check = original_runtime


def build_freeze_manifest() -> dict[str, Any]:
    """Build the prospective freeze manifest from already inspected static assets."""

    root = _repo_root()
    output = root / MANIFEST_PATH
    preflight = base._read_json(root / PREFLIGHT_PATH, "engineering preflight")
    base._require(preflight.get("protocol_id") == PROTOCOL_ID, "Preflight protocol mismatch")
    base._require(preflight.get("model_forward_calls") == 0, "Preflight used a model forward")
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
        "status": "freeze_complete_before_any_t6_model_forward",
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
    with _delegated_t5_surface():
        result = t5.audit_freeze()
    preflight = base._read_json(_repo_root() / PREFLIGHT_PATH, "engineering preflight")
    base._require(preflight.get("model_forward_calls") == 0, "Preflight forward count changed")
    return result


def tokenizer_preflight(model_label: str, model_path: Path) -> dict[str, Any]:
    with _delegated_t5_surface():
        return t5.tokenizer_preflight(model_label, model_path)


def run_model(model_label: str, model_path: Path, output: Path) -> dict[str, Any]:
    with _delegated_t5_surface():
        return t5.run_model(model_label, model_path, output)


def validate_run(directory: Path) -> dict[str, Any]:
    with _delegated_t5_surface():
        return t5.validate_run(directory)


def _load_authority() -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    with _delegated_t5_surface():
        return t5._load_authority(_repo_root())


def _panel(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    return frozen._load_panel(_repo_root(), config)


def _load_prior_t5_reference(config: Mapping[str, Any]) -> dict[str, Any]:
    root = _repo_root()
    spec = config["prior_t5_reference"]
    receipt_path = (root / CONFIG_PATH.parent / str(spec["analysis_receipt"])).resolve()
    manifest_path = (root / CONFIG_PATH.parent / str(spec["public_manifest"])).resolve()
    for path in (receipt_path, manifest_path):
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise base.ProtocolError("T5 reference escaped repository") from exc
        base._require(path.is_file(), f"Missing T5 reference: {path.name}")
    receipt = base._read_json(receipt_path, "T5 analysis receipt")
    public_manifest = base._read_json(manifest_path, "T5 public manifest")
    base._require(receipt.get("protocol_id") == spec["protocol_id"], "T5 protocol mismatch")
    base._require(receipt.get("outcome_pattern") == spec["outcome_pattern"], "T5 outcome mismatch")
    base._require(public_manifest.get("protocol_id") == spec["protocol_id"], "T5 manifest mismatch")
    base._require(public_manifest.get("status") == "pass", "T5 manifest is not pass")
    return {
        "role": spec["role"],
        "inferential_pooling": bool(spec["inferential_pooling"]),
        "analysis_receipt_sha256": base._sha256_file(receipt_path),
        "public_manifest_sha256": base._sha256_file(manifest_path),
        "outcome_pattern": receipt["outcome_pattern"],
        "primary_results": receipt["primary_results"],
    }


def _outcome_pattern(primary: Mapping[str, Mapping[str, Any]]) -> str:
    rejected = {role for role in MODEL_ROLES if bool(primary[role]["holm_reject"])}
    if rejected == set(MODEL_ROLES):
        return "all_four_dense_distance_attenuation_candidate"
    if rejected == {"gemma3_4b_it", "gemma3_12b_it"}:
        return "gemma3_size_pair_distance_attenuation"
    if rejected == {"gemma3_12b_it"}:
        return "gemma3_12b_only_distance_attenuation"
    if rejected:
        return "mixed_dense_model_distance_attenuation"
    return "no_dense_model_distance_attenuation"


def analyze_runs(run_directories: Mapping[str, Path], output: Path) -> dict[str, Any]:
    manifest, config, verified_assets = _load_authority()
    audit = audit_freeze()
    base._require(tuple(run_directories) == MODEL_ROLES, "Analysis model role order mismatch")
    panel_items = _panel(config)
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
            f"Freeze mismatch: {role}",
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
        tensor = frozen._factor_tensor(result["activations"], panel_items, family_order, slot_order)
        family_count, slot_count, carrier_count, distance_count, depth_count, width = tensor.shape
        flattened = tensor.reshape(
            family_count,
            slot_count,
            carrier_count * distance_count * depth_count,
            width,
        )
        randomization = t5.distance_randomization(
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

    raw_iut = {
        role: float(randomization_by_role[role]["intersection_union_raw_p"])
        for role in MODEL_ROLES
    }
    holm = base.holm_adjust(raw_iut, alpha=float(endpoint["familywise_alpha"]))
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
                "run_receipt_sha256": base._sha256_file(
                    run_directories[role] / "run_receipt.json"
                ),
                "run_ledger_sha256": base._sha256_file(run_directories[role] / "SHA256SUMS"),
            }
            for role in MODEL_ROLES
        }
        analysis_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "frozen_post_t5_dense_cuda_carrier_distance_replication",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "inputs": input_receipts,
            "prior_t5_reference": _load_prior_t5_reference(config),
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
            "# Multifamily dense CUDA carrier-distance v0 result\n\n",
            f"Outcome pattern: `{pattern}`.\n\n",
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
                "The decision requires both distance-1 recurrence and the fixed positive "
                "log-distance contrast. This post-T5 exploratory CUDA family does not "
                "establish scale effects, base/instruct equivalence, backend parity, "
                "semantics, causality, confirmation, monotonicity, or duration.\n",
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
    for role in MODEL_ROLES:
        analyze.add_argument(f"--{role.replace('_', '-')}-run", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)
    validate_joint = subparsers.add_parser("validate-analysis")
    validate_joint.add_argument("directory", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "build-freeze-manifest":
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
            payload = analyze_runs(
                {
                    role: getattr(args, f"{role}_run")
                    for role in MODEL_ROLES
                },
                args.output,
            )
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
