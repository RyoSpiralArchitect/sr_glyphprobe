#!/usr/bin/env python3
"""Analyze the frozen Llama-3.2-3B MPS emoji-transport experiment.

The CLI accepts ten role-bound run directories: five independently centered
full-50 family runs and five independently centered token-isomorphic core-35
family runs.  It validates the sealed run evidence and reads stored
fingerprints only.  It never loads a model or tokenizer.

The analysis evaluates the E1 leave-one-target-group-out M, R, and R_global
endpoints separately in each panel arm.  One joint 20,000-replicate
group-stratified target bootstrap is reused across both arms and both layers;
all data-dependent prototypes are rebuilt inside every replicate.  The sole
primary criterion is whether the lower 95% percentile-bootstrap bound for the
full50 layer-5 R_global endpoint is greater than zero.  Core35, layer 11, and
paired core35-minus-full50 differences are prespecified secondary descriptions.

Only the first 24 records of the fixed prestage target bank are admissible.
No confirmatory or causal holdout content is opened by this implementation.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import importlib.util
import math
import os
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import orjson
import yaml


def _import_e1_math() -> ModuleType:
    path = Path(__file__).resolve().with_name("analyze_emoji_family_exploratory_v1.py")
    spec = importlib.util.spec_from_file_location(
        "glyphprobe_frozen_e1_emoji_family_math", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import frozen E1 analyzer: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e1_math = _import_e1_math()

ANALYSIS_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1"
SCHEMA_VERSION = 1
MODEL = "mlx-community/Llama-3.2-3B-bf16"
REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
BACKEND = "transformers"
DEVICE = "mps"
DTYPE = "float32"
SITE = "resid_post"
LAYERS = (5, 11)
PRIMARY_LAYER = 5
SECONDARY_LAYER = 11
STRENGTH = 0.05
DIRECTION_SEEDS = (101, 211, 307)
DIRECTION_WRAPPER_INDICES = {
    101: (1, 2, 4, 5, 7, 8, 10, 11, 12, 13, 14, 15),
    211: (0, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15),
    307: (0, 1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 14),
}
FINGERPRINT_DIM = 96
FINGERPRINT_SEED = 8_675_309
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 20_260_808
BOOTSTRAP_CHUNK_SIZE = 128
TARGET_GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
)
TARGETS_PER_GROUP = 4
EPSILON = 1e-12
ZERO_HOOK_TOLERANCE = 1e-6

MODEL_NUM_LAYERS = 28
MODEL_DIM = 3_072
MODEL_PARAMETER_COUNT = 3_212_749_824
MODEL_ARTIFACT_FILE_COUNT = 9
MODEL_ARTIFACT_TOTAL_BYTES = 6_434_705_789
MODEL_ARTIFACT_MANIFEST_SHA256 = (
    "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
)
MODEL_VOCAB_SIZE = 128_256

FAMILY_MIDDLE_TOKEN = {
    "sky": 234,
    "food": 235,
    "animals": 238,
    "transport": 248,
    "social": 97,
}
MERGED_TOKEN_EXCEPTIONS = {
    "sky_slot_01": (9468, 102032),
    "sky_slot_02": (9468, 107569),
    "social_slot_00": (9468, 100701),
}

TARGET_PATH = Path("data/targets/prestage_targets.jsonl")
TARGET_SHA256 = "91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7"
SOURCE_PATH = Path("data/wrappers/source_wrappers.jsonl")
SOURCE_SHA256 = "310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee"
MANIFEST_PATH = Path("data/manifests/llama32_3b_mps_emoji_transport_v1.json")
E1_DEPENDENCY_PATH = Path("scripts/analyze_emoji_family_exploratory_v1.py")
PREFLIGHT_PATH = Path(
    "artifacts/llama32_3b_mps_emoji_transport_v1/preflight/tokenization_audit_v1.json"
)
EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/execution_receipt.json"
)
ATTEMPT_STARTED_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/attempt_started_receipt.json"
)
FAILED_EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/failed_execution_receipt.json"
)
LAUNCHER_LOG_PATH = Path("runs/.e2-llama32-3b-mps-transport-v1-launcher-logs")

FAMILY_ORDER = ("sky", "food", "animals", "transport", "social")
ARM_ORDER = ("full50", "core35")
ARM_DEFINITIONS: dict[str, dict[str, Any]] = {
    "full50": {
        "conditions_per_family": 10,
        "slot_indices": tuple(range(10)),
        "panel_paths": {
            "sky": Path("data/emoji_panels/e1_sky_moon.yaml"),
            "food": Path("data/emoji_panels/e1_food.yaml"),
            "animals": Path("data/emoji_panels/e1_animals.yaml"),
            "transport": Path("data/emoji_panels/e1_transport.yaml"),
            "social": Path("data/emoji_panels/e1_social.yaml"),
        },
    },
    "core35": {
        "conditions_per_family": 7,
        "slot_indices": tuple(range(3, 10)),
        "panel_paths": {
            role: Path(f"data/emoji_panels/e2_core35_{role}.yaml")
            for role in FAMILY_ORDER
        },
    },
}
for _arm_name, _definition in ARM_DEFINITIONS.items():
    _definition["config_paths"] = {
        role: Path(f"configs/e2_llama32_3b_mps_{_arm_name}_{role}_v1.yaml")
        for role in FAMILY_ORDER
    }
    _definition["run_names"] = {
        role: f"e2-llama32-3b-mps-{_arm_name}-{role}-transport-v1"
        for role in FAMILY_ORDER
    }

PRIMARY_CRITERION_ID = "H_E2_1_full50_layer5_R_global_positive"
PRIMARY_CRITERION_RULE = "ci95_lower_gt_zero"
ENDPOINT_WITHIN = e1_math.ENDPOINT_WITHIN
ENDPOINT_TRANSFER = e1_math.ENDPOINT_TRANSFER
ENDPOINT_SPECIFICITY = e1_math.ENDPOINT_SPECIFICITY
ENDPOINT_GLOBAL = e1_math.ENDPOINT_GLOBAL
ENDPOINT_PAIRED_DIFFERENCE = "paired_core35_minus_full50_R_global"

OUTPUT_FILENAMES = (
    "panel_target_scores.jsonl",
    "transfer_target_scores.jsonl",
    "family_cell_summary.jsonl",
    "transfer_cell_summary.jsonl",
    "llama32_3b_mps_emoji_transport_receipt.json",
    "report.md",
)
EXPECTED_OUTPUT_ROWS = {
    "panel_target_scores.jsonl": 480,
    "transfer_target_scores.jsonl": 1_920,
    "family_cell_summary.jsonl": 20,
    "transfer_cell_summary.jsonl": 80,
}
OUTPUT_UNIQUE_KEYS = {
    "panel_target_scores.jsonl": ["panel_arm", "family", "layer", "target_id"],
    "transfer_target_scores.jsonl": [
        "panel_arm",
        "source_family",
        "prototype_family",
        "layer",
        "target_id",
    ],
    "family_cell_summary.jsonl": ["panel_arm", "family", "layer"],
    "transfer_cell_summary.jsonl": [
        "panel_arm",
        "source_family",
        "prototype_family",
        "layer",
    ],
}
REQUIRED_RUN_FILENAMES = frozenset(
    {
        "capabilities.json",
        "cross_seed_fingerprint_summary.jsonl",
        "direction_replicates.json",
        "directions.npz",
        "fingerprint_summary.jsonl",
        "interventions.jsonl",
        "plan.json",
        "receipt.json",
        "report.md",
        "resolved_config.yaml",
        "resolved_inputs.json",
        "scalar_balance_summary.jsonl",
        "source_activations.npz",
        "source_item_metrics.jsonl",
        "source_layer_metrics.jsonl",
        "summary.json",
        "target_baselines.jsonl",
        "target_baselines.npz",
        "tokenization.jsonl",
    }
)


class TransportAnalysisError(ValueError):
    """Raised when a frozen E2 input or analysis invariant fails."""


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, option=option)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _rename_directory_no_replace(source: Path, destination: Path) -> None:
    """Atomically publish one directory while refusing an existing destination."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 0x00000001)
    else:
        raise TransportAnalysisError(
            "Atomic no-replace directory publication is unavailable on this platform"
        )
    if result != 0:
        error_number = ctypes.get_errno()
        if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
            raise TransportAnalysisError(
                "Refusing to overwrite analysis output directory"
            )
        raise TransportAnalysisError(
            f"Atomic analysis publication failed with errno {error_number}"
        )


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value, pretty=True) + b"\n")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    _atomic_write(path, b"".join(_json_bytes(dict(row)) + b"\n" for row in rows))


def _read_json_object(path: Path, description: str) -> dict[str, Any]:
    if not path.is_file():
        raise TransportAnalysisError(f"Missing {description}: {path}")
    try:
        value = orjson.loads(path.read_bytes())
    except orjson.JSONDecodeError as exc:
        raise TransportAnalysisError(f"Invalid JSON in {description}: {path}") from exc
    if not isinstance(value, dict):
        raise TransportAnalysisError(f"Expected a JSON object in {description}: {path}")
    return value


def _read_json_array(path: Path, description: str) -> list[Any]:
    if not path.is_file():
        raise TransportAnalysisError(f"Missing {description}: {path}")
    try:
        value = orjson.loads(path.read_bytes())
    except orjson.JSONDecodeError as exc:
        raise TransportAnalysisError(f"Invalid JSON in {description}: {path}") from exc
    if not isinstance(value, list):
        raise TransportAnalysisError(f"Expected a JSON array in {description}: {path}")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, Any]]:
    if not path.is_file():
        raise TransportAnalysisError(f"Missing {description}: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise TransportAnalysisError(
                    f"Invalid JSONL at {path}:{line_number}"
                ) from exc
            if not isinstance(row, dict):
                raise TransportAnalysisError(f"Expected object at {path}:{line_number}")
            rows.append(row)
    if not rows:
        raise TransportAnalysisError(f"Empty {description}: {path}")
    return rows


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _verified_repo_file(root: Path, relative: Path, expected_sha256: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_file():
        raise TransportAnalysisError(f"Missing frozen input: {relative}")
    observed = _sha256_file(path)
    if observed != expected_sha256:
        raise TransportAnalysisError(
            f"Frozen input SHA-256 mismatch for {relative}: "
            f"expected {expected_sha256}, observed {observed}"
        )
    return path


def _nested(mapping: Mapping[str, Any], path: Sequence[str]) -> Any:
    current: Any = mapping
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            raise TransportAnalysisError(f"Missing {'.'.join(path)}")
        current = current[part]
    return current


def _require_fields(
    mapping: Mapping[str, Any],
    expected: Mapping[tuple[str, ...], Any],
    description: str,
) -> None:
    for path, wanted in expected.items():
        observed = _nested(mapping, path)
        if observed != wanted or isinstance(wanted, bool) and observed is not wanted:
            raise TransportAnalysisError(
                f"{description} mismatch at {'.'.join(path)}: "
                f"expected {wanted!r}, observed {observed!r}"
            )


def _manifest_roles(
    arm_document: Mapping[str, Any], arm: str
) -> dict[str, dict[str, Any]]:
    raw = arm_document.get("roles")
    if raw is None and all(
        isinstance(arm_document.get(role), Mapping) for role in FAMILY_ORDER
    ):
        raw = {role: arm_document[role] for role in FAMILY_ORDER}
    if isinstance(raw, Mapping):
        roles = {
            str(role): dict(value)
            for role, value in raw.items()
            if isinstance(value, Mapping)
        }
    elif isinstance(raw, list):
        roles = {
            str(value.get("role")): dict(value)
            for value in raw
            if isinstance(value, Mapping) and isinstance(value.get("role"), str)
        }
    else:
        raise TransportAnalysisError(f"Manifest arm {arm} has no role bindings")
    if set(roles) != set(FAMILY_ORDER):
        raise TransportAnalysisError(f"Manifest arm {arm} family roles differ")
    return roles


def _load_fixed_authority(root: Path) -> dict[str, Any]:
    manifest_path = root / MANIFEST_PATH
    manifest = _read_json_object(manifest_path, "frozen E2 manifest")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise TransportAnalysisError("Unsupported E2 manifest schema")
    if manifest.get("protocol_id") != ANALYSIS_ID:
        raise TransportAnalysisError("E2 manifest protocol ID differs")

    analysis = manifest.get("analysis")
    if not isinstance(analysis, Mapping):
        raise TransportAnalysisError("E2 manifest has no analysis block")
    expected_analysis = {
        ("analysis_id",): ANALYSIS_ID,
        ("script_path",): Path(__file__).resolve().relative_to(root).as_posix(),
        ("script_sha256",): _sha256_file(Path(__file__).resolve()),
        ("e1_math_dependency", "path"): E1_DEPENDENCY_PATH.as_posix(),
        ("e1_math_dependency", "sha256"): _sha256_file(Path(e1_math.__file__)),
        ("bootstrap", "replicates"): BOOTSTRAP_REPLICATES,
        ("bootstrap", "seed"): BOOTSTRAP_SEED,
        ("bootstrap", "sampling_unit"): "target_prompt_cluster",
        ("bootstrap", "group_stratified"): True,
        ("bootstrap", "joint_across_arms_layers_endpoints_and_pairs"): True,
        ("bootstrap", "rebuild_loto_prototypes_inside_each_replicate"): True,
        ("primary_criterion", "id"): PRIMARY_CRITERION_ID,
        ("primary_criterion", "panel_arm"): "full50",
        ("primary_criterion", "layer"): PRIMARY_LAYER,
        ("primary_criterion", "endpoint_id"): ENDPOINT_GLOBAL,
        ("primary_criterion", "rule"): PRIMARY_CRITERION_RULE,
        ("output_filenames",): list(OUTPUT_FILENAMES),
        ("expected_output_rows",): EXPECTED_OUTPUT_ROWS,
        ("output_unique_keys",): OUTPUT_UNIQUE_KEYS,
    }
    _require_fields(analysis, expected_analysis, "E2 manifest analysis")

    fixed_cell = manifest.get("fixed_cell")
    if not isinstance(fixed_cell, Mapping):
        raise TransportAnalysisError("E2 manifest has no fixed_cell block")
    expected_fixed_cell = {
        ("mode",): "internal",
        ("backend", "kind"): BACKEND,
        ("backend", "model"): MODEL,
        ("backend", "revision"): REVISION,
        ("backend", "device"): DEVICE,
        ("backend", "dtype"): DTYPE,
        ("backend", "local_files_only"): True,
        ("backend", "add_special_tokens"): False,
        ("backend", "trust_remote_code"): False,
        ("run", "seeds"): list(DIRECTION_SEEDS),
        ("run", "resume"): False,
        ("run", "fail_fast"): True,
        ("run", "replicate_mode"): "wrapper_subsample",
        ("run", "wrapper_subsample_fraction"): 0.75,
        ("panel", "neutral_glyph"): "🟰",
        ("panel", "centroid_mode"): "panel",
        ("source", "max_wrappers"): 16,
        ("source", "anchor_position"): "last_nonpad",
        ("targets", "max_cases"): 24,
        ("targets", "calibration_cases"): 6,
        ("capture", "site"): SITE,
        ("capture", "layers"): list(LAYERS),
        ("capture", "position"): "last_nonpad",
        ("capture", "return_attentions"): False,
        ("intervention", "mode"): "activation_add",
        ("intervention", "normalization"): "rms",
        ("intervention", "strengths"): [STRENGTH],
        ("intervention", "position"): "last_nonpad",
        ("intervention", "clip", "mode"): "global_rms",
        ("intervention", "clip", "max_ratio"): 0.25,
        ("intervention", "iso_kl_enabled"): False,
        ("controls", "random_directions_per_layer"): 2,
        ("controls", "zero_direction"): True,
        ("controls", "sign_flip"): False,
        ("controls", "sign_flip_strengths"): [],
        ("controls", "label_shuffle_permutations"): 0,
        ("controls", "include_neutral_direction"): False,
        ("metrics", "top_k"): 50,
        ("metrics", "fingerprint_dim"): FINGERPRINT_DIM,
        ("metrics", "fingerprint_seed"): FINGERPRINT_SEED,
        ("metrics", "split_half_repeats"): 200,
        ("metrics", "rbo_p"): 0.9,
        ("metrics", "save_top_logit_deltas"): 32,
        ("metrics", "save_fingerprints"): True,
        ("metrics", "epsilon"): EPSILON,
        ("sae_enabled",): False,
        ("surface", "emoji_template"): "{emoji}\n{prompt}",
        ("surface", "neutral_template"): "{prompt}",
        ("surface", "system_prompt"): None,
    }
    _require_fields(fixed_cell, expected_fixed_cell, "E2 manifest fixed cell")

    shared = manifest.get("shared_inputs")
    if not isinstance(shared, Mapping):
        raise TransportAnalysisError("E2 manifest has no shared_inputs block")
    source_spec = shared.get("source")
    target_spec = shared.get("target")
    artifact_spec = shared.get("model_artifact")
    if not all(
        isinstance(value, Mapping)
        for value in (source_spec, target_spec, artifact_spec)
    ):
        raise TransportAnalysisError("E2 manifest shared inputs are incomplete")
    _require_fields(
        source_spec,
        {
            ("path",): SOURCE_PATH.as_posix(),
            ("sha256",): SOURCE_SHA256,
            ("selected_record_count",): 16,
        },
        "E2 source binding",
    )
    _require_fields(
        target_spec,
        {
            ("path",): TARGET_PATH.as_posix(),
            ("sha256",): TARGET_SHA256,
            ("selected_record_count",): len(TARGET_GROUPS) * TARGETS_PER_GROUP,
        },
        "E2 target binding",
    )
    _require_fields(
        artifact_spec,
        {
            ("file_count",): MODEL_ARTIFACT_FILE_COUNT,
            ("total_bytes",): MODEL_ARTIFACT_TOTAL_BYTES,
            ("manifest_sha256",): MODEL_ARTIFACT_MANIFEST_SHA256,
        },
        "E2 model-artifact binding",
    )

    source_path = _verified_repo_file(root, SOURCE_PATH, SOURCE_SHA256)
    target_path = _verified_repo_file(root, TARGET_PATH, TARGET_SHA256)
    wrapper_rows = _read_jsonl(source_path, "fixed source wrappers")
    if len(wrapper_rows) != 16:
        raise TransportAnalysisError("Fixed source wrapper bank must contain 16 rows")
    wrapper_ids: list[str] = []
    for row in wrapper_rows:
        wrapper_id = row.get("id")
        template = row.get("template")
        if (
            not isinstance(wrapper_id, str)
            or not wrapper_id
            or wrapper_id in wrapper_ids
            or not isinstance(template, str)
            or template.count("{emoji}") != 1
        ):
            raise TransportAnalysisError("Fixed source wrapper bank is invalid")
        wrapper_ids.append(wrapper_id)
    if source_spec.get("ordered_ids") != wrapper_ids:
        raise TransportAnalysisError("Source wrapper order differs from manifest")

    all_target_rows = _read_jsonl(target_path, "fixed prestage targets")
    if target_spec.get("file_record_count") != len(all_target_rows):
        raise TransportAnalysisError(
            "Prestage target file row count differs from manifest"
        )
    selected_count = len(TARGET_GROUPS) * TARGETS_PER_GROUP
    targets: list[dict[str, str]] = []
    seen_targets: set[str] = set()
    for row in all_target_rows[:selected_count]:
        target_id = row.get("id")
        group = row.get("group")
        if (
            not isinstance(target_id, str)
            or not target_id
            or target_id in seen_targets
            or group not in TARGET_GROUPS
        ):
            raise TransportAnalysisError("Selected prestage target grid is invalid")
        seen_targets.add(target_id)
        targets.append({"id": target_id, "group": str(group)})
    if len(targets) != selected_count:
        raise TransportAnalysisError("Exactly 24 prestage targets are required")
    counts = Counter(row["group"] for row in targets)
    if counts != Counter({group: TARGETS_PER_GROUP for group in TARGET_GROUPS}):
        raise TransportAnalysisError("Prestage target groups are not six by four")
    if target_spec.get("ordered_selected_ids") != [row["id"] for row in targets]:
        raise TransportAnalysisError("Selected target ID order differs from manifest")
    if target_spec.get("ordered_selected_groups") != [row["group"] for row in targets]:
        raise TransportAnalysisError("Selected target groups differ from manifest")

    manifest_arms = manifest.get("arms")
    if not isinstance(manifest_arms, Mapping) or set(manifest_arms) != set(ARM_ORDER):
        raise TransportAnalysisError("E2 manifest arm set differs")
    roles: dict[str, dict[str, dict[str, Any]]] = {}
    panel_documents: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for arm in ARM_ORDER:
        arm_document = manifest_arms[arm]
        if not isinstance(arm_document, Mapping):
            raise TransportAnalysisError(f"Manifest arm {arm} is not a mapping")
        definition = ARM_DEFINITIONS[arm]
        _require_fields(
            arm_document,
            {
                ("conditions_per_family",): definition["conditions_per_family"],
                ("matched_slots",): [
                    f"slot_{index:02d}" for index in definition["slot_indices"]
                ],
                ("centering",): "independent_panel_centroid",
            },
            f"E2 manifest arm {arm}",
        )
        role_specs = _manifest_roles(arm_document, arm)
        roles[arm] = {}
        for role in FAMILY_ORDER:
            row = role_specs[role]
            config_relative = definition["config_paths"][role]
            panel_relative = definition["panel_paths"][role]
            expected_binding = {
                ("role",): role,
                ("config_path",): config_relative.as_posix(),
                ("panel_path",): panel_relative.as_posix(),
                ("run_name",): definition["run_names"][role],
            }
            _require_fields(row, expected_binding, f"E2 {arm}/{role} binding")
            config_sha = row.get("config_sha256")
            panel_sha = row.get("panel_sha256")
            if not isinstance(config_sha, str) or len(config_sha) != 64:
                raise TransportAnalysisError(f"E2 {arm}/{role} config hash is invalid")
            if not isinstance(panel_sha, str) or len(panel_sha) != 64:
                raise TransportAnalysisError(f"E2 {arm}/{role} panel hash is invalid")
            config_path = _verified_repo_file(root, config_relative, config_sha)
            panel_path = _verified_repo_file(root, panel_relative, panel_sha)
            panel_document = yaml.safe_load(panel_path.read_text(encoding="utf-8"))
            items = (
                panel_document.get("items")
                if isinstance(panel_document, Mapping)
                else None
            )
            if (
                not isinstance(items, list)
                or len(items) != definition["conditions_per_family"]
            ):
                raise TransportAnalysisError(f"E2 {arm}/{role} panel size differs")
            expected_ids = tuple(
                f"{role}_slot_{index:02d}" for index in definition["slot_indices"]
            )
            if (
                tuple(item.get("id") for item in items if isinstance(item, Mapping))
                != expected_ids
            ):
                raise TransportAnalysisError(f"E2 {arm}/{role} panel IDs/order differ")
            glyphs: list[str] = []
            for slot_index, item in zip(definition["slot_indices"], items):
                if not isinstance(item, Mapping):
                    raise TransportAnalysisError(
                        f"E2 {arm}/{role} panel item is invalid"
                    )
                glyph = item.get("glyph")
                factors = item.get("factors")
                if not isinstance(glyph, str) or len(glyph) != 1:
                    raise TransportAnalysisError(
                        f"E2 {arm}/{role} glyph is not one scalar"
                    )
                if not isinstance(factors, Mapping) or (
                    factors.get("family") != role
                    or factors.get("matched_slot") != f"slot_{slot_index:02d}"
                    or factors.get("codepoint") != f"U+{ord(glyph):X}"
                ):
                    raise TransportAnalysisError(
                        f"E2 {arm}/{role} panel factors differ"
                    )
                glyphs.append(glyph)
            panel_documents[(arm, role)] = [dict(item) for item in items]
            roles[arm][role] = {
                "arm": arm,
                "role": role,
                "config": config_relative,
                "config_sha256": config_sha,
                "config_path": config_path,
                "panel": panel_relative,
                "panel_sha256": panel_sha,
                "panel_path": panel_path,
                "panel_items": [dict(item) for item in items],
                "condition_ids": expected_ids,
                "glyphs": tuple(glyphs),
                "run_name": definition["run_names"][role],
                "condition_count": definition["conditions_per_family"],
            }

    for role in FAMILY_ORDER:
        if panel_documents[("core35", role)] != panel_documents[("full50", role)][3:10]:
            raise TransportAnalysisError(
                f"Core35 {role} panel is not the exact slot_03..09 full50 subset"
            )
    return {
        "root": root,
        "manifest_path": manifest_path,
        "manifest_sha256": _sha256_file(manifest_path),
        "source_path": source_path,
        "target_path": target_path,
        "wrapper_ids": tuple(wrapper_ids),
        "targets": targets,
        "target_ids": tuple(row["id"] for row in targets),
        "target_groups": {row["id"]: row["group"] for row in targets},
        "roles": roles,
        "model_artifact": dict(artifact_spec),
        "expected_model_identity_sha256": fixed_cell.get("model_identity_sha256"),
        "expected_run_implementation_sha256": fixed_cell.get(
            "run_implementation_sha256"
        ),
        "expected_environment": fixed_cell.get("environment"),
    }


def _validate_execution_receipt(
    root: Path, authority: Mapping[str, Any]
) -> dict[str, Any]:
    path = root / EXECUTION_RECEIPT_PATH
    receipt = _read_json_object(path, "E2 execution receipt")
    expected_scalars = {
        "schema_version": 1,
        "protocol_id": ANALYSIS_ID,
        "status": "execution_complete_analysis_not_run",
        "scientific_outcomes_inspected_by_launcher": False,
        "branch": "main",
        "preflight_path": PREFLIGHT_PATH.as_posix(),
        "process_isolation": "strictly_sequential_independent_python_processes",
        "simultaneous_full_model_residency": False,
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
        "completed_process_count": 10,
        "expected_process_count": 10,
        "analysis_authorized": True,
        "failed_execution_receipt_written": False,
    }
    for field, wanted in expected_scalars.items():
        if receipt.get(field) != wanted:
            raise TransportAnalysisError(
                f"Execution receipt mismatch at {field}: "
                f"expected {wanted!r}, observed {receipt.get(field)!r}"
            )
    freeze_commit = receipt.get("freeze_commit")
    if (
        not isinstance(freeze_commit, str)
        or len(freeze_commit) != 40
        or any(character not in "0123456789abcdef" for character in freeze_commit)
    ):
        raise TransportAnalysisError("Execution receipt freeze commit is invalid")
    audited_commit = receipt.get("audited_commit")
    if (
        not isinstance(audited_commit, str)
        or len(audited_commit) != 40
        or any(character not in "0123456789abcdef" for character in audited_commit)
    ):
        raise TransportAnalysisError("Execution receipt audited commit is invalid")
    initial_namespace = receipt.get("initial_namespace_check")
    expected_namespace = {
        "resume_allowed": False,
        "run_name_count": len(ARM_ORDER) * len(FAMILY_ORDER),
        "existing_run_destination_count": 0,
        "launcher_log_namespace_preexisting": False,
    }
    if initial_namespace != expected_namespace:
        raise TransportAnalysisError("Execution receipt initial namespace differs")
    try:
        execution_started = datetime.fromisoformat(receipt["started_at"])
        execution_finished = datetime.fromisoformat(receipt["finished_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TransportAnalysisError(
            "Execution receipt timestamps are invalid"
        ) from exc
    if (
        execution_started.tzinfo is None
        or execution_finished.tzinfo is None
        or execution_started > execution_finished
    ):
        raise TransportAnalysisError("Execution receipt timestamp interval is invalid")

    failed_path = root / FAILED_EXECUTION_RECEIPT_PATH
    if os.path.lexists(failed_path):
        raise TransportAnalysisError(
            "Failed-execution receipt exists; analysis publication is forbidden"
        )
    attempt_binding = receipt.get("attempt_started_receipt")
    if not isinstance(attempt_binding, Mapping) or set(attempt_binding) != {
        "path",
        "sha256",
    }:
        raise TransportAnalysisError("Execution attempt-start binding is invalid")
    if attempt_binding.get("path") != ATTEMPT_STARTED_RECEIPT_PATH.as_posix():
        raise TransportAnalysisError("Execution attempt-start path differs")
    attempt_path = root / ATTEMPT_STARTED_RECEIPT_PATH
    if (
        not attempt_path.is_file()
        or attempt_path.is_symlink()
        or attempt_binding.get("sha256") != _sha256_file(attempt_path)
    ):
        raise TransportAnalysisError("Execution attempt-start hash differs")
    attempt = _read_json_object(attempt_path, "E2 attempt-started receipt")
    expected_attempt_keys = {
        "schema_version",
        "protocol_id",
        "status",
        "scientific_outcomes_inspected_by_launcher",
        "model_process_count_at_publication",
        "started_at",
        "git_freeze",
        "preflight",
        "manifest",
        "config_order",
        "run_names",
        "initial_namespace_check",
        "launcher_log_namespace",
        "resume_policy",
    }
    if set(attempt) != expected_attempt_keys:
        raise TransportAnalysisError("Attempt-started receipt fields differ")
    expected_attempt_scalars = {
        "schema_version": 1,
        "protocol_id": ANALYSIS_ID,
        "status": "attempt_started_no_process_launched",
        "scientific_outcomes_inspected_by_launcher": False,
        "model_process_count_at_publication": 0,
        "started_at": receipt["started_at"],
        "initial_namespace_check": expected_namespace,
        "launcher_log_namespace": LAUNCHER_LOG_PATH.as_posix(),
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
    }
    for field, wanted in expected_attempt_scalars.items():
        if attempt.get(field) != wanted:
            raise TransportAnalysisError(f"Attempt-started receipt mismatch at {field}")
    expected_git_freeze = {
        "audited_commit": audited_commit,
        "execution_commit": freeze_commit,
        "origin_main_commit": freeze_commit,
        "branch": "main",
    }
    if attempt.get("git_freeze") != expected_git_freeze:
        raise TransportAnalysisError("Attempt-started Git freeze differs")
    expected_config_order = [
        authority["roles"][arm][role]["config"].as_posix()
        for arm in ARM_ORDER
        for role in FAMILY_ORDER
    ]
    expected_run_names = [
        authority["roles"][arm][role]["run_name"]
        for arm in ARM_ORDER
        for role in FAMILY_ORDER
    ]
    if attempt.get("config_order") != expected_config_order:
        raise TransportAnalysisError("Attempt-started config order differs")
    if attempt.get("run_names") != expected_run_names:
        raise TransportAnalysisError("Attempt-started run-name order differs")
    if attempt.get("preflight") != {
        "path": PREFLIGHT_PATH.as_posix(),
        "sha256": receipt.get("preflight_sha256"),
    }:
        raise TransportAnalysisError("Attempt-started preflight binding differs")
    if attempt.get("manifest") != {
        "path": MANIFEST_PATH.as_posix(),
        "sha256": authority["manifest_sha256"],
    }:
        raise TransportAnalysisError("Attempt-started manifest binding differs")

    preflight_path = root / PREFLIGHT_PATH
    if not preflight_path.is_file() or _sha256_file(preflight_path) != receipt.get(
        "preflight_sha256"
    ):
        raise TransportAnalysisError("Execution receipt preflight hash differs")
    preflight = _read_json_object(preflight_path, "E2 tokenizer preflight")
    expected_preflight = {
        "schema_version": 1,
        "protocol_id": ANALYSIS_ID,
        "status": "passed",
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "p2_content_opened": False,
        "c1_content_opened": False,
    }
    for field, wanted in expected_preflight.items():
        if preflight.get(field) != wanted:
            raise TransportAnalysisError(f"Tokenizer preflight mismatch at {field}")
    preflight_audited_commit = preflight.get("audited_commit")
    preflight_git_authority = preflight.get("git_authority")
    if (
        preflight_audited_commit != audited_commit
        or not isinstance(preflight_git_authority, Mapping)
        or preflight_git_authority.get("audited_commit") != audited_commit
        or preflight_git_authority.get("origin_main_commit") != audited_commit
        or preflight_git_authority.get("branch") != "main"
        or preflight_git_authority.get("worktree_clean_before_publication") is not True
    ):
        raise TransportAnalysisError("Tokenizer preflight Git authority differs")
    authorization = preflight.get("authorization")
    if (
        not isinstance(authorization, Mapping)
        or authorization.get("frozen_grid_execution_authorized") is not True
    ):
        raise TransportAnalysisError(
            "Tokenizer preflight execution authorization differs"
        )
    static = preflight.get("static")
    manifest_binding = static.get("manifest") if isinstance(static, Mapping) else None
    if (
        not isinstance(manifest_binding, Mapping)
        or manifest_binding.get("path") != MANIFEST_PATH.as_posix()
        or manifest_binding.get("sha256") != authority["manifest_sha256"]
    ):
        raise TransportAnalysisError("Tokenizer preflight manifest binding differs")

    processes = receipt.get("processes")
    if not isinstance(processes, list) or len(processes) != 10:
        raise TransportAnalysisError("Execution receipt process grid differs")
    expected_pairs = [(arm, role) for arm in ARM_ORDER for role in FAMILY_ORDER]
    root_resolved = root.resolve()
    process_records: list[dict[str, Any]] = []
    for index, ((arm, role), row) in enumerate(zip(expected_pairs, processes)):
        if not isinstance(row, Mapping):
            raise TransportAnalysisError(f"Execution process {index} is invalid")
        spec = authority["roles"][arm][role]
        if (
            row.get("index") != index
            or row.get("config") != spec["config"].as_posix()
            or row.get("config_sha256") != spec["config_sha256"]
            or row.get("return_code") != 0
        ):
            raise TransportAnalysisError(f"Execution process {index} differs")
        for timestamp_field in ("started_at", "finished_at"):
            timestamp = row.get(timestamp_field)
            try:
                parsed = datetime.fromisoformat(timestamp)
            except (TypeError, ValueError) as exc:
                raise TransportAnalysisError(
                    f"Execution process {index} {timestamp_field} is invalid"
                ) from exc
            if parsed.tzinfo is None:
                raise TransportAnalysisError(
                    f"Execution process {index} {timestamp_field} has no timezone"
                )
        process_started = datetime.fromisoformat(row["started_at"])
        process_finished = datetime.fromisoformat(row["finished_at"])
        if not (
            execution_started
            <= process_started
            <= process_finished
            <= execution_finished
        ):
            raise TransportAnalysisError(
                f"Execution process {index} escapes the launcher interval"
            )
        log_relative = row.get("log_path")
        log_sha = row.get("log_sha256")
        if not isinstance(log_relative, str) or not isinstance(log_sha, str):
            raise TransportAnalysisError(
                f"Execution process {index} log binding is invalid"
            )
        log_path = (root / log_relative).resolve()
        if (
            not log_path.is_relative_to(root_resolved)
            or not log_path.is_file()
            or _sha256_file(log_path) != log_sha
        ):
            raise TransportAnalysisError(
                f"Execution process {index} log binding differs"
            )
        process_records.append(
            {
                "index": index,
                "panel_arm": arm,
                "role": role,
                "config": spec["config"].as_posix(),
                "config_sha256": spec["config_sha256"],
                "log_path": log_relative,
                "log_sha256": log_sha,
                "started_at": row.get("started_at"),
                "finished_at": row.get("finished_at"),
            }
        )
    return {
        "path": EXECUTION_RECEIPT_PATH.as_posix(),
        "sha256": _sha256_file(path),
        "freeze_commit": freeze_commit,
        "audited_commit": audited_commit,
        "attempt_started_receipt": {
            "path": ATTEMPT_STARTED_RECEIPT_PATH.as_posix(),
            "sha256": _sha256_file(attempt_path),
        },
        "failed_execution_receipt_absent": True,
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
        "initial_namespace_check": expected_namespace,
        "preflight": {
            "path": PREFLIGHT_PATH.as_posix(),
            "sha256": _sha256_file(preflight_path),
        },
        "processes": process_records,
    }


def _validate_resolved_config(
    config: Mapping[str, Any], arm: str, role: str, spec: Mapping[str, Any]
) -> None:
    expected = {
        ("schema_version",): 1,
        ("mode",): "internal",
        ("backend", "kind"): BACKEND,
        ("backend", "model"): MODEL,
        ("backend", "revision"): REVISION,
        ("backend", "device"): DEVICE,
        ("backend", "dtype"): DTYPE,
        ("backend", "local_files_only"): True,
        ("backend", "add_special_tokens"): False,
        ("backend", "trust_remote_code"): False,
        ("backend", "base_url"): None,
        ("backend", "api_key_env"): None,
        ("backend", "model_kwargs"): {},
        ("backend", "validation_receipt"): None,
        ("backend", "validation_receipt_sha256"): None,
        ("backend", "generation", "max_new_tokens"): 48,
        ("backend", "generation", "temperature"): 0.0,
        ("backend", "generation", "top_p"): 1.0,
        ("backend", "generation", "top_k"): None,
        ("backend", "generation", "do_sample"): None,
        ("backend", "generation", "logprobs"): True,
        ("backend", "generation", "top_logprobs"): 20,
        ("run", "name"): spec["run_name"],
        ("run", "output_root"): "../runs",
        ("run", "seeds"): list(DIRECTION_SEEDS),
        ("run", "deterministic_torch"): False,
        ("run", "resume"): False,
        ("run", "fail_fast"): True,
        ("run", "max_errors"): 10,
        ("run", "replicate_mode"): "wrapper_subsample",
        ("run", "wrapper_subsample_fraction"): 0.75,
        ("panel", "items"): [],
        ("panel", "neutral_glyph"): "🟰",
        ("panel", "centroid_mode"): "panel",
        ("source", "max_wrappers"): 16,
        ("source", "anchor_position"): "last_nonpad",
        ("targets", "max_cases"): 24,
        ("targets", "calibration_cases"): 6,
        ("targets", "generation_cases"): 8,
        ("capture", "site"): SITE,
        ("capture", "layers"): list(LAYERS),
        ("capture", "position"): "last_nonpad",
        ("capture", "return_attentions"): False,
        ("intervention", "mode"): "activation_add",
        ("intervention", "normalization"): "rms",
        ("intervention", "strengths"): [STRENGTH],
        ("intervention", "position"): "last_nonpad",
        ("intervention", "clip", "mode"): "global_rms",
        ("intervention", "clip", "max_ratio"): 0.25,
        ("intervention", "iso_kl", "enabled"): False,
        ("intervention", "iso_kl", "target_kl"): 0.03,
        ("intervention", "iso_kl", "tolerance"): 0.004,
        ("intervention", "iso_kl", "min_strength"): 0.001,
        ("intervention", "iso_kl", "max_strength"): 0.35,
        ("intervention", "iso_kl", "bisection_steps"): 7,
        ("intervention", "iso_kl", "per_seed"): False,
        ("controls", "random_directions_per_layer"): 2,
        ("controls", "zero_direction"): True,
        ("controls", "sign_flip"): False,
        ("controls", "sign_flip_strengths"): [],
        ("controls", "label_shuffle_permutations"): 0,
        ("controls", "include_neutral_direction"): False,
        ("metrics", "top_k"): 50,
        ("metrics", "fingerprint_dim"): FINGERPRINT_DIM,
        ("metrics", "fingerprint_seed"): FINGERPRINT_SEED,
        ("metrics", "split_half_repeats"): 200,
        ("metrics", "rbo_p"): 0.9,
        ("metrics", "save_top_logit_deltas"): 32,
        ("metrics", "save_fingerprints"): True,
        ("metrics", "epsilon"): EPSILON,
        ("sae", "enabled"): False,
        ("sae", "release"): None,
        ("sae", "sae_ids"): {},
        ("sae", "device"): "auto",
        ("sae", "top_k_features"): 32,
        ("surface", "emoji_template"): "{emoji}\n{prompt}",
        ("surface", "neutral_template"): "{prompt}",
        ("surface", "system_prompt"): None,
        ("surface", "enabled_logprobs"): True,
    }
    _require_fields(config, expected, f"Resolved config {arm}/{role}")
    path_checks = {
        ("panel", "file"): Path(spec["panel"]).name,
        ("source", "wrappers_file"): SOURCE_PATH.name,
        ("targets", "cases_file"): TARGET_PATH.name,
    }
    for path, basename in path_checks.items():
        observed = Path(str(_nested(config, path))).name
        if observed != basename:
            raise TransportAnalysisError(
                f"Resolved config {arm}/{role} path mismatch at {'.'.join(path)}"
            )


def _finite(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TransportAnalysisError(f"Invalid numeric {field}: {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise TransportAnalysisError(f"Non-finite numeric {field}")
    return result


def _validate_finite_tree(value: Any, *, field: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise TransportAnalysisError(f"Non-finite numeric {field}")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_finite_tree(item, field=f"{field}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite_tree(item, field=f"{field}[{index}]")


def _expected_raw_token_ids(role: str, condition_id: str) -> tuple[int, ...]:
    if condition_id in MERGED_TOKEN_EXCEPTIONS:
        return MERGED_TOKEN_EXCEPTIONS[condition_id]
    try:
        slot = int(condition_id.rsplit("_", 1)[1])
    except (IndexError, ValueError) as exc:
        raise TransportAnalysisError(f"Invalid condition ID: {condition_id}") from exc
    return (9468, FAMILY_MIDDLE_TOKEN[role], 239 + slot)


def _fingerprint(
    row: Mapping[str, Any], *, line_number: int, allow_zero: bool
) -> np.ndarray:
    distribution = row.get("distribution")
    value = (
        distribution.get("fingerprint") if isinstance(distribution, Mapping) else None
    )
    vector = (
        np.asarray(value, dtype=np.float64) if value is not None else np.asarray([])
    )
    if vector.ndim != 1 or vector.size != FINGERPRINT_DIM:
        raise TransportAnalysisError(
            f"Row {line_number} fingerprint must have dimension {FINGERPRINT_DIM}"
        )
    if not np.all(np.isfinite(vector)):
        raise TransportAnalysisError(f"Row {line_number} fingerprint is non-finite")
    norm = float(np.linalg.norm(vector))
    if norm <= EPSILON:
        if allow_zero:
            return vector
        raise TransportAnalysisError(f"Row {line_number} fingerprint has zero norm")
    return vector / norm


def _validate_direction_replicates(
    run_dir: Path, arm: str, role: str
) -> tuple[dict[int, tuple[int, ...]], Path]:
    path = run_dir / "direction_replicates.json"
    rows = _read_json_array(path, f"{arm}/{role} direction replicates")
    observed: dict[int, tuple[int, ...]] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise TransportAnalysisError(f"{arm}/{role} direction replicate is invalid")
        seed = int(_finite(row.get("seed"), field="direction_replicate.seed"))
        raw_indices = row.get("wrapper_indices")
        if (
            seed not in DIRECTION_SEEDS
            or seed in observed
            or not isinstance(raw_indices, list)
            or any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in raw_indices
            )
        ):
            raise TransportAnalysisError(
                f"{arm}/{role} direction replicate grid differs"
            )
        indices = tuple(raw_indices)
        if indices != DIRECTION_WRAPPER_INDICES[seed]:
            raise TransportAnalysisError(
                f"{arm}/{role} direction wrapper selection differs for seed {seed}"
            )
        observed[seed] = indices
    if observed != DIRECTION_WRAPPER_INDICES:
        raise TransportAnalysisError(f"{arm}/{role} direction replicate set differs")
    return observed, path


def _validate_scale(
    row: Mapping[str, Any], *, arm: str, role: str, zero_hook: bool
) -> None:
    scale = row.get("scale")
    if not isinstance(scale, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} scale metrics are missing")
    numeric = {
        field: _finite(scale.get(field), field=f"scale.{field}")
        for field in (
            "target_activation_rms",
            "direction_raw_rms",
            "requested_strength",
            "perturbation_rms",
            "perturbation_to_target_rms",
            "clip_scale",
        )
    }
    if numeric["target_activation_rms"] <= 0.0:
        raise TransportAnalysisError(
            f"{arm}/{role} target activation RMS is not positive"
        )
    if zero_hook:
        expected_zero = (
            "direction_raw_rms",
            "requested_strength",
            "perturbation_rms",
            "perturbation_to_target_rms",
        )
        if any(numeric[field] != 0.0 for field in expected_zero):
            raise TransportAnalysisError(f"{arm}/{role} zero-hook scale is nonzero")
    else:
        if (
            numeric["direction_raw_rms"] <= 0.0
            or numeric["requested_strength"] != STRENGTH
            or abs(numeric["perturbation_to_target_rms"] - STRENGTH) > 1e-5
            or numeric["perturbation_rms"] <= 0.0
        ):
            raise TransportAnalysisError(f"{arm}/{role} RMS intervention scale differs")
    if numeric["clip_scale"] != 1.0 or scale.get("clipped") is not False:
        raise TransportAnalysisError(f"{arm}/{role} unexpected clipping occurred")


def _validate_intervention_metrics(
    row: Mapping[str, Any], *, arm: str, role: str, zero_hook: bool
) -> None:
    """Require every configured per-intervention diagnostic and its exact shape."""

    expected_row_keys = {
        "task_id",
        "seed",
        "layer",
        "condition_type",
        "condition_id",
        "strength",
        "sign",
        "target_id",
        "calibration",
        "glyph",
        "target_index",
        "target_group",
        "direction_wrapper_indices",
        "scale",
        "activation",
        "distribution",
        "sae",
        "latency_ms",
        "peak_memory_bytes",
        "claim_stage",
    }
    if set(row) != expected_row_keys:
        missing = sorted(expected_row_keys - set(row))
        extra = sorted(set(row) - expected_row_keys)
        raise TransportAnalysisError(
            f"{arm}/{role} intervention row fields differ: "
            f"missing={missing}, extra={extra}"
        )
    task_id = row.get("task_id")
    if (
        not isinstance(task_id, str)
        or len(task_id) != 24
        or any(character not in "0123456789abcdef" for character in task_id)
    ):
        raise TransportAnalysisError(f"{arm}/{role} intervention task ID differs")
    target_index = row.get("target_index")
    if (
        isinstance(target_index, bool)
        or not isinstance(target_index, int)
        or not 0 <= target_index < 24
    ):
        raise TransportAnalysisError(f"{arm}/{role} intervention target index differs")
    latency_ms = _finite(row.get("latency_ms"), field="ledger.latency_ms")
    if latency_ms < 0.0 or row.get("peak_memory_bytes") is not None:
        raise TransportAnalysisError(
            f"{arm}/{role} MPS latency/peak-memory receipt differs"
        )
    expected_claim_stage = (
        "pre-causal-zero-hook-control" if zero_hook else "pre-causal-screen"
    )
    if row.get("claim_stage") != expected_claim_stage or row.get("sae") != {
        "enabled": False
    }:
        raise TransportAnalysisError(f"{arm}/{role} claim/SAE diagnostics differ")

    scale = row.get("scale")
    if not isinstance(scale, Mapping) or set(scale) != {
        "target_activation_rms",
        "direction_raw_rms",
        "requested_strength",
        "perturbation_rms",
        "perturbation_to_target_rms",
        "clip_scale",
        "clipped",
    }:
        raise TransportAnalysisError(f"{arm}/{role} scale diagnostic fields differ")

    activation = row.get("activation")
    activation_fields = {
        "actual_activation_delta_rms",
        "actual_to_baseline_rms",
        "intended_activation_delta_rms",
        "actual_to_intended_rms",
        "actual_intended_cosine",
        "post_activation_cosine",
    }
    if not isinstance(activation, Mapping) or set(activation) != activation_fields:
        raise TransportAnalysisError(
            f"{arm}/{role} activation diagnostic fields differ"
        )
    activation_values = {
        field: _finite(activation.get(field), field=f"activation.{field}")
        for field in activation_fields
    }
    for field in (
        "actual_activation_delta_rms",
        "actual_to_baseline_rms",
        "intended_activation_delta_rms",
        "actual_to_intended_rms",
    ):
        if activation_values[field] < 0.0:
            raise TransportAnalysisError(
                f"{arm}/{role} activation diagnostic is negative at {field}"
            )
    for field in ("actual_intended_cosine", "post_activation_cosine"):
        if not -1.000001 <= activation_values[field] <= 1.000001:
            raise TransportAnalysisError(
                f"{arm}/{role} activation cosine is out of range at {field}"
            )

    distribution = row.get("distribution")
    scalar_fields = {
        "kl_base_to_intervened",
        "kl_intervened_to_base",
        "js_divergence",
        "total_variation",
        "hellinger",
        "entropy_baseline",
        "entropy_intervened",
        "entropy_delta",
        "logit_delta_l2",
        "logit_delta_rms",
        "logit_delta_max_abs",
        "logit_cosine",
        "probability_cosine",
        "top_k_jaccard",
        "top_k_overlap_fraction",
        "rank_biased_overlap",
        "baseline_top2_margin",
        "intervened_top2_margin",
    }
    integer_fields = {
        "baseline_argmax",
        "intervened_argmax",
        "intervened_rank_of_baseline_argmax",
        "baseline_rank_of_intervened_argmax",
    }
    list_fields = {
        "top_positive_delta_ids",
        "top_positive_delta_values",
        "top_negative_delta_ids",
        "top_negative_delta_values",
        "fingerprint",
    }
    expected_distribution_fields = (
        scalar_fields | integer_fields | list_fields | {"argmax_flip"}
    )
    if (
        not isinstance(distribution, Mapping)
        or set(distribution) != expected_distribution_fields
    ):
        raise TransportAnalysisError(
            f"{arm}/{role} distribution diagnostic fields differ"
        )
    scalar_values = {
        field: _finite(distribution.get(field), field=f"distribution.{field}")
        for field in scalar_fields
    }
    bounded_zero_one = {
        "total_variation",
        "hellinger",
        "top_k_jaccard",
        "top_k_overlap_fraction",
        "rank_biased_overlap",
    }
    for field in bounded_zero_one:
        if not -1e-9 <= scalar_values[field] <= 1.000001:
            raise TransportAnalysisError(
                f"{arm}/{role} distribution diagnostic is out of range at {field}"
            )
    for field in ("logit_cosine", "probability_cosine"):
        if not -1.000001 <= scalar_values[field] <= 1.000001:
            raise TransportAnalysisError(
                f"{arm}/{role} distribution cosine is out of range at {field}"
            )
    for field in (
        "kl_base_to_intervened",
        "kl_intervened_to_base",
        "js_divergence",
        "entropy_baseline",
        "entropy_intervened",
        "logit_delta_l2",
        "logit_delta_rms",
        "logit_delta_max_abs",
        "baseline_top2_margin",
        "intervened_top2_margin",
    ):
        if scalar_values[field] < -1e-9:
            raise TransportAnalysisError(
                f"{arm}/{role} distribution diagnostic is negative at {field}"
            )
    if distribution.get("argmax_flip") is not (
        distribution.get("baseline_argmax") != distribution.get("intervened_argmax")
    ):
        raise TransportAnalysisError(f"{arm}/{role} argmax-flip diagnostic differs")
    for field in integer_fields:
        value = distribution.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise TransportAnalysisError(
                f"{arm}/{role} distribution integer differs at {field}"
            )
        lower = 1 if "rank" in field else 0
        upper = MODEL_VOCAB_SIZE if "rank" in field else MODEL_VOCAB_SIZE - 1
        if not lower <= value <= upper:
            raise TransportAnalysisError(
                f"{arm}/{role} distribution integer is out of range at {field}"
            )
    for prefix in ("top_positive_delta", "top_negative_delta"):
        ids = distribution.get(f"{prefix}_ids")
        values = distribution.get(f"{prefix}_values")
        if (
            not isinstance(ids, list)
            or len(ids) != 32
            or len(set(ids)) != 32
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value < MODEL_VOCAB_SIZE
                for value in ids
            )
            or not isinstance(values, list)
            or len(values) != 32
        ):
            raise TransportAnalysisError(
                f"{arm}/{role} {prefix} diagnostic shape differs"
            )
        numeric_values = [
            _finite(value, field=f"distribution.{prefix}_values") for value in values
        ]
        if prefix == "top_positive_delta" and any(
            first < second for first, second in zip(numeric_values, numeric_values[1:])
        ):
            raise TransportAnalysisError(
                f"{arm}/{role} positive delta diagnostics are not sorted"
            )
        if prefix == "top_negative_delta" and any(
            first > second for first, second in zip(numeric_values, numeric_values[1:])
        ):
            raise TransportAnalysisError(
                f"{arm}/{role} negative delta diagnostics are not sorted"
            )
    fingerprint = distribution.get("fingerprint")
    if not isinstance(fingerprint, list) or len(fingerprint) != FINGERPRINT_DIM:
        raise TransportAnalysisError(f"{arm}/{role} fingerprint diagnostic differs")


def _validate_npz_array(
    value: np.ndarray, *, shape: tuple[int, ...], field: str
) -> None:
    if value.shape != shape:
        raise TransportAnalysisError(
            f"{field} shape differs: expected {shape}, observed {value.shape}"
        )
    if not np.issubdtype(value.dtype, np.number) or not np.all(np.isfinite(value)):
        raise TransportAnalysisError(f"{field} is non-numeric or non-finite")


def _validate_run_inventory(
    run_dir: Path,
    arm: str,
    role: str,
    spec: Mapping[str, Any],
    authority: Mapping[str, Any],
) -> dict[str, str]:
    observed_names = {path.name for path in run_dir.iterdir() if path.is_file()}
    observed_directories = [path.name for path in run_dir.iterdir() if path.is_dir()]
    if observed_directories or observed_names != REQUIRED_RUN_FILENAMES:
        missing = sorted(REQUIRED_RUN_FILENAMES - observed_names)
        extra = sorted(observed_names - REQUIRED_RUN_FILENAMES)
        raise TransportAnalysisError(
            f"{arm}/{role} run inventory differs: missing={missing}, "
            f"extra={extra}, directories={sorted(observed_directories)}"
        )
    for name in REQUIRED_RUN_FILENAMES:
        if (run_dir / name).stat().st_size <= 0:
            raise TransportAnalysisError(f"{arm}/{role} run file is empty: {name}")

    condition_count = int(spec["condition_count"])
    plan = _read_json_object(run_dir / "plan.json", f"{arm}/{role} plan")
    emoji_calls = len(LAYERS) * len(DIRECTION_SEEDS) * condition_count * 24
    expected_plan = {
        "backend": BACKEND,
        "model": MODEL,
        "mode": "internal",
        "emoji_count": condition_count,
        "source_forward_calls": (condition_count + 1) * 16,
        "target_baseline_calls": 24,
        "emoji_intervention_calls": emoji_calls,
        "random_control_calls": 288,
        "generic_emoji_control_calls": 0,
        "zero_hook_control_calls": 48,
        "iso_kl_calibration_calls_upper_bound": 0,
        "iso_kl_evaluation_calls": 0,
        "estimated_forward_calls": (condition_count + 1) * 16
        + 24
        + emoji_calls
        + 288
        + 48,
        "resolved_layers": list(LAYERS),
        "seed_count": 3,
        "target_count": 24,
        "wrapper_count": 16,
    }
    for field, wanted in expected_plan.items():
        if plan.get(field) != wanted:
            raise TransportAnalysisError(f"{arm}/{role} plan mismatch at {field}")

    capabilities = _read_json_object(
        run_dir / "capabilities.json", f"{arm}/{role} capabilities"
    )
    if capabilities.get("backend") != BACKEND or capabilities.get("model") != MODEL:
        raise TransportAnalysisError(f"{arm}/{role} capability identity differs")
    capability_flags = capabilities.get("capabilities")
    metadata = capabilities.get("metadata")
    if not isinstance(capability_flags, Mapping) or any(
        capability_flags.get(name) is not True
        for name in (
            "tokenize",
            "forward_logits",
            "hidden_states",
            "activation_cache",
            "activation_patch",
            "deterministic_forward",
        )
    ):
        raise TransportAnalysisError(f"{arm}/{role} required capabilities differ")
    if not isinstance(metadata, Mapping) or (
        metadata.get("num_layers") != MODEL_NUM_LAYERS
        or metadata.get("d_model") != MODEL_DIM
        or metadata.get("block_path") != "model.layers"
    ):
        raise TransportAnalysisError(f"{arm}/{role} capability metadata differs")

    tokenization_rows = _read_jsonl(
        run_dir / "tokenization.jsonl", f"{arm}/{role} tokenization"
    )
    if len(tokenization_rows) != condition_count + 1:
        raise TransportAnalysisError(f"{arm}/{role} tokenization row count differs")
    for item, row in zip(spec["panel_items"], tokenization_rows[:-1]):
        expected_ids = list(_expected_raw_token_ids(role, item["id"]))
        if (
            row.get("emoji_id") != item["id"]
            or row.get("glyph") != item["glyph"]
            or row.get("raw_token_ids") != expected_ids
            or row.get("raw_token_count") != len(expected_ids)
        ):
            raise TransportAnalysisError(f"{arm}/{role} tokenization binding differs")
        wrapper_rows = row.get("wrapper_tokenization")
        if not isinstance(wrapper_rows, list) or [
            value.get("wrapper_id")
            for value in wrapper_rows
            if isinstance(value, Mapping)
        ] != list(authority["wrapper_ids"]):
            raise TransportAnalysisError(f"{arm}/{role} wrapper tokenization differs")
    neutral = tokenization_rows[-1]
    if (
        neutral.get("emoji_id") != "__neutral__"
        or neutral.get("glyph") != "🟰"
        or not isinstance(neutral.get("raw_token_ids"), list)
        or neutral.get("raw_token_count") != len(neutral["raw_token_ids"])
    ):
        raise TransportAnalysisError(f"{arm}/{role} neutral tokenization differs")

    source_items = _read_jsonl(
        run_dir / "source_item_metrics.jsonl", f"{arm}/{role} source item metrics"
    )
    source_item_keys = [(row.get("emoji_id"), row.get("layer")) for row in source_items]
    expected_source_item_keys = {
        (condition_id, layer)
        for condition_id in spec["condition_ids"]
        for layer in LAYERS
    }
    if (
        len(source_item_keys) != len(set(source_item_keys))
        or set(source_item_keys) != expected_source_item_keys
    ):
        raise TransportAnalysisError(f"{arm}/{role} source item metric grid differs")
    source_layers = _read_jsonl(
        run_dir / "source_layer_metrics.jsonl", f"{arm}/{role} source layer metrics"
    )
    if [row.get("layer") for row in source_layers] != list(LAYERS):
        raise TransportAnalysisError(f"{arm}/{role} source layer metric grid differs")

    baselines = _read_jsonl(
        run_dir / "target_baselines.jsonl", f"{arm}/{role} target baselines"
    )
    if len(baselines) != 24:
        raise TransportAnalysisError(f"{arm}/{role} target baseline count differs")
    for target_index, (target_id, row) in enumerate(
        zip(authority["target_ids"], baselines)
    ):
        if (
            row.get("target_index") != target_index
            or row.get("target_id") != target_id
            or row.get("group") != authority["target_groups"][target_id]
            or not isinstance(row.get("prompt_hash"), str)
            or len(row["prompt_hash"]) != 16
        ):
            raise TransportAnalysisError(
                f"{arm}/{role} target baseline binding differs"
            )

    scalar_rows = _read_jsonl(
        run_dir / "scalar_balance_summary.jsonl", f"{arm}/{role} scalar balance"
    )
    scalar_keys = [
        (row.get("layer"), row.get("seed"), row.get("condition_type"))
        for row in scalar_rows
    ]
    expected_scalar_keys = {
        (layer, seed, condition_type)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_type in ("emoji", "random")
    }
    if (
        len(scalar_keys) != len(set(scalar_keys))
        or set(scalar_keys) != expected_scalar_keys
    ):
        raise TransportAnalysisError(f"{arm}/{role} scalar-balance grid differs")
    for row in scalar_rows:
        expected_count = (
            condition_count * 24 if row["condition_type"] == "emoji" else 48
        )
        if (
            row.get("strength") != STRENGTH
            or row.get("record_count") != expected_count
            or _finite(
                row.get("perturbation_ratio_max_abs_error"),
                field="scalar.perturbation_ratio_max_abs_error",
            )
            > 1e-5
            or _finite(row.get("clip_fraction"), field="scalar.clip_fraction") != 0.0
        ):
            raise TransportAnalysisError(f"{arm}/{role} scalar-balance values differ")

    cross_seed_rows = _read_jsonl(
        run_dir / "cross_seed_fingerprint_summary.jsonl",
        f"{arm}/{role} cross-seed fingerprint summary",
    )
    if [row.get("layer") for row in cross_seed_rows] != list(LAYERS) or any(
        row.get("strength") != STRENGTH
        or row.get("emoji_condition_count") != condition_count
        or row.get("seed_count") != len(DIRECTION_SEEDS)
        or row.get("seed_pair_count") != 3
        for row in cross_seed_rows
    ):
        raise TransportAnalysisError(f"{arm}/{role} cross-seed summary differs")

    for description, rows in (
        ("tokenization", tokenization_rows),
        ("source_items", source_items),
        ("source_layers", source_layers),
        ("baselines", baselines),
        ("scalar_balance", scalar_rows),
        ("cross_seed", cross_seed_rows),
    ):
        _validate_finite_tree(rows, field=f"{arm}.{role}.{description}")

    with np.load(run_dir / "source_activations.npz", allow_pickle=False) as payload:
        if set(payload.files) != {"emoji", "neutral", "layers"}:
            raise TransportAnalysisError(
                f"{arm}/{role} source activation archive differs"
            )
        _validate_npz_array(
            payload["emoji"],
            shape=(condition_count, 16, len(LAYERS), MODEL_DIM),
            field=f"{arm}.{role}.source_activations.emoji",
        )
        _validate_npz_array(
            payload["neutral"],
            shape=(16, len(LAYERS), MODEL_DIM),
            field=f"{arm}.{role}.source_activations.neutral",
        )
        if payload["layers"].tolist() != list(LAYERS):
            raise TransportAnalysisError(
                f"{arm}/{role} source activation layers differ"
            )
    with np.load(run_dir / "directions.npz", allow_pickle=False) as payload:
        expected_keys = {"layers"} | {
            f"{prefix}_seed_{seed}"
            for seed in DIRECTION_SEEDS
            for prefix in ("directions", "panel_means", "generic")
        }
        if set(payload.files) != expected_keys or payload["layers"].tolist() != list(
            LAYERS
        ):
            raise TransportAnalysisError(f"{arm}/{role} direction archive differs")
        for seed in DIRECTION_SEEDS:
            for prefix, shape in (
                ("directions", (condition_count, len(LAYERS), MODEL_DIM)),
                ("panel_means", (condition_count, len(LAYERS), MODEL_DIM)),
                ("generic", (len(LAYERS), MODEL_DIM)),
            ):
                _validate_npz_array(
                    payload[f"{prefix}_seed_{seed}"],
                    shape=shape,
                    field=f"{arm}.{role}.directions.{prefix}.{seed}",
                )
    with np.load(run_dir / "target_baselines.npz", allow_pickle=False) as payload:
        if set(payload.files) != {"logits", "activations"}:
            raise TransportAnalysisError(f"{arm}/{role} baseline archive differs")
        _validate_npz_array(
            payload["logits"],
            shape=(24, MODEL_VOCAB_SIZE),
            field=f"{arm}.{role}.baselines.logits",
        )
        _validate_npz_array(
            payload["activations"],
            shape=(24, len(LAYERS), MODEL_DIM),
            field=f"{arm}.{role}.baselines.activations",
        )
    return {
        name: _sha256_file(run_dir / name) for name in sorted(REQUIRED_RUN_FILENAMES)
    }


def _validate_summary(
    run_dir: Path, arm: str, role: str, condition_count: int
) -> tuple[dict[str, Any], Path]:
    path = run_dir / "summary.json"
    summary = _read_json_object(path, f"{arm}/{role} run summary")
    emoji_rows = len(LAYERS) * len(DIRECTION_SEEDS) * condition_count * 24
    random_rows = len(LAYERS) * len(DIRECTION_SEEDS) * 2 * 24
    zero_rows = len(LAYERS) * 24
    expected = {
        "error_count": 0,
        "intervention_record_count": emoji_rows + random_rows + zero_rows,
        "random_control_count": random_rows,
        "zero_hook_control_count": zero_rows,
        "emoji_count": condition_count,
        "target_case_count": 24,
        "seed_count": len(DIRECTION_SEEDS),
        "strength_count": 1,
        "resolved_layers": list(LAYERS),
    }
    for field, wanted in expected.items():
        if summary.get(field) != wanted:
            raise TransportAnalysisError(
                f"{arm}/{role} summary mismatch at {field}: "
                f"expected {wanted!r}, observed {summary.get(field)!r}"
            )
    for field in (
        "zero_hook_max_activation_delta_rms",
        "zero_hook_max_logit_delta_rms",
    ):
        if _finite(summary.get(field), field=f"summary.{field}") > ZERO_HOOK_TOLERANCE:
            raise TransportAnalysisError(
                f"{arm}/{role} zero-hook error exceeds tolerance"
            )
    return summary, path


def _load_fingerprint_screening(
    run_dir: Path, arm: str, role: str, condition_count: int
) -> tuple[dict[tuple[int, int], dict[str, Any]], Path]:
    path = run_dir / "fingerprint_summary.jsonl"
    rows = _read_jsonl(path, f"{arm}/{role} fingerprint summary")
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    numeric_fields = (
        "emoji_same_split_cosine",
        "emoji_cross_cosine",
        "emoji_separation",
        "emoji_split_repeat_mean",
        "emoji_split_repeat_median",
        "emoji_split_repeat_ci_low",
        "emoji_split_repeat_ci_high",
        "random_same_split_cosine",
        "random_cross_cosine",
        "random_separation",
        "random_split_repeat_mean",
        "random_split_repeat_ci_low",
        "random_split_repeat_ci_high",
        "emoji_advantage_over_random",
    )
    for row in rows:
        layer = int(_finite(row.get("layer"), field="screening.layer"))
        seed = int(_finite(row.get("seed"), field="screening.seed"))
        strength = _finite(row.get("strength"), field="screening.strength")
        if layer not in LAYERS or seed not in DIRECTION_SEEDS or strength != STRENGTH:
            raise TransportAnalysisError(f"{arm}/{role} screening has an extra cell")
        key = (layer, seed)
        if key in cells:
            raise TransportAnalysisError(f"{arm}/{role} screening duplicates {key}")
        if (
            row.get("emoji_condition_count") != condition_count
            or row.get("emoji_target_count") != 24
            or row.get("random_condition_count") != 2
            or row.get("random_target_count") != 24
            or row.get("emoji_split_repeat_count") != 200
            or row.get("emoji_label_permutation_count") != 0
        ):
            raise TransportAnalysisError(f"{arm}/{role} screening counts differ")
        for forbidden in (
            "emoji_label_permutation_p",
            "emoji_label_permutation_null_mean",
            "emoji_label_permutation_null_std",
        ):
            if row.get(forbidden) is not None:
                raise TransportAnalysisError(
                    f"{arm}/{role} generated forbidden permutation statistics"
                )
        cells[key] = {
            "split_seed": int(_finite(row.get("split_seed"), field="split_seed")),
            **{field: _finite(row.get(field), field=field) for field in numeric_fields},
            "emoji_condition_count": condition_count,
            "emoji_target_count": 24,
            "emoji_split_repeat_count": 200,
            "random_condition_count": 2,
            "random_target_count": 24,
        }
    expected = {(layer, seed) for layer in LAYERS for seed in DIRECTION_SEEDS}
    if set(cells) != expected:
        raise TransportAnalysisError(f"{arm}/{role} screening grid is incomplete")
    return cells, path


def _validate_model_identity(
    receipt: Mapping[str, Any], authority: Mapping[str, Any], arm: str, role: str
) -> dict[str, Any]:
    identity = receipt.get("model_identity")
    if not isinstance(identity, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} has no model identity")
    payload = identity.get("payload")
    observed_sha = identity.get("sha256")
    if not isinstance(payload, Mapping) or observed_sha != _stable_sha256(payload):
        raise TransportAnalysisError(f"{arm}/{role} model identity hash is invalid")
    expected_identity = authority.get("expected_model_identity_sha256")
    if expected_identity is not None and observed_sha != expected_identity:
        raise TransportAnalysisError(
            f"{arm}/{role} model identity differs from manifest"
        )
    _require_fields(
        payload,
        {
            ("backend",): BACKEND,
            ("backend_class",): "TransformersBackend",
            ("model",): MODEL,
            ("revision",): REVISION,
            ("commit_hash",): REVISION,
            ("device",): DEVICE,
            ("dtype",): DTYPE,
            ("resolved_device",): DEVICE,
            ("block_path",): "model.layers",
            ("num_layers",): MODEL_NUM_LAYERS,
            ("d_model",): MODEL_DIM,
            ("parameter_count",): MODEL_PARAMETER_COUNT,
            ("model_artifact", "file_count"): MODEL_ARTIFACT_FILE_COUNT,
            ("model_artifact", "total_bytes"): MODEL_ARTIFACT_TOTAL_BYTES,
            ("model_artifact", "manifest_sha256"): MODEL_ARTIFACT_MANIFEST_SHA256,
            ("loader_metadata", "resolved_dtype"): "torch.float32",
            ("loader_metadata", "local_files_only_requested"): True,
        },
        f"{arm}/{role} model identity",
    )
    element_counts = payload.get("parameter_element_dtype_counts")
    if element_counts != {"torch.float32": MODEL_PARAMETER_COUNT}:
        raise TransportAnalysisError(
            f"{arm}/{role} runtime parameter dtype/count differs"
        )
    tensor_counts = payload.get("parameter_tensor_dtype_counts")
    if (
        not isinstance(tensor_counts, Mapping)
        or set(tensor_counts) != {"torch.float32"}
        or not isinstance(tensor_counts["torch.float32"], int)
        or tensor_counts["torch.float32"] <= 0
    ):
        raise TransportAnalysisError(f"{arm}/{role} parameter tensor dtype differs")
    return dict(identity)


def _without_runtime_noise(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _without_runtime_noise(item)
            for key, item in sorted(value.items())
            if key
            not in {
                "load_latency_ms",
                "resolved_model_path",
                "validation_receipt",
                "validation_receipt_sha256",
            }
        }
    if isinstance(value, list):
        return [_without_runtime_noise(item) for item in value]
    return value


def _validate_environment(
    receipt: Mapping[str, Any], authority: Mapping[str, Any], arm: str, role: str
) -> dict[str, Any]:
    environment = receipt.get("environment")
    if not isinstance(environment, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} environment receipt is missing")
    expected_environment = authority.get("expected_environment")
    if expected_environment is not None and environment != expected_environment:
        raise TransportAnalysisError(f"{arm}/{role} environment differs from manifest")
    python_version = environment.get("python")
    platform = environment.get("platform")
    packages = environment.get("packages")
    if not isinstance(python_version, str) or not python_version.startswith("3.13.13 "):
        raise TransportAnalysisError(f"{arm}/{role} Python version differs")
    if platform != "macOS-26.2-arm64-arm-64bit-Mach-O":
        raise TransportAnalysisError(f"{arm}/{role} platform differs")
    if environment.get("machine") != "arm64" or environment.get("processor") != "arm":
        raise TransportAnalysisError(f"{arm}/{role} machine identity differs")
    if not isinstance(packages, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} package receipt is missing")
    for package, wanted in {
        "glyphprobe": "0.1.0",
        "numpy": "2.4.4",
        "torch": "2.11.0",
        "transformers": "4.57.6",
    }.items():
        if packages.get(package) != wanted:
            raise TransportAnalysisError(
                f"{arm}/{role} package version differs for {package}"
            )
    return dict(environment)


def _load_run(
    run_dir: Path,
    arm: str,
    role: str,
    authority: Mapping[str, Any],
) -> dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    spec = authority["roles"][arm][role]
    config_path = run_dir / "resolved_config.yaml"
    if not config_path.is_file():
        raise TransportAnalysisError(f"Missing resolved config: {config_path}")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, Mapping):
        raise TransportAnalysisError(f"Resolved config is not a mapping: {config_path}")
    _validate_resolved_config(config, arm, role, spec)

    receipt_path = run_dir / "receipt.json"
    receipt = _read_json_object(receipt_path, f"{arm}/{role} run receipt")
    if (
        receipt.get("schema_version") != 1
        or receipt.get("status") != "complete"
        or receipt.get("mode") != "internal"
        or receipt.get("config_path") != spec["config"].name
        or receipt.get("summary_path") != "summary.json"
    ):
        raise TransportAnalysisError(
            f"{arm}/{role} run receipt is not an exact complete run"
        )
    run_id = receipt.get("run_id")
    run_seal = receipt.get("run_seal")
    if (
        not isinstance(run_id, str)
        or run_dir.name != run_id
        or not isinstance(run_seal, str)
        or len(run_seal) != 16
        or any(character not in "0123456789abcdef" for character in run_seal)
    ):
        raise TransportAnalysisError(f"{arm}/{role} run ID/seal differs")
    expected_hashes = {
        f"input_00:{spec['config'].name}": spec["config_sha256"],
        f"input_01:{spec['panel'].name}": spec["panel_sha256"],
        f"input_02:{SOURCE_PATH.name}": SOURCE_SHA256,
        f"input_03:{TARGET_PATH.name}": TARGET_SHA256,
    }
    if receipt.get("input_hashes") != expected_hashes:
        raise TransportAnalysisError(f"{arm}/{role} receipt input hashes differ")
    backend = receipt.get("backend")
    if not isinstance(backend, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} receipt backend is missing")
    _require_fields(
        backend,
        {
            ("kind",): BACKEND,
            ("model",): MODEL,
            ("revision",): REVISION,
            ("device",): DEVICE,
            ("dtype",): DTYPE,
            ("local_files_only",): True,
            ("add_special_tokens",): False,
            ("trust_remote_code",): False,
        },
        f"{arm}/{role} receipt backend",
    )
    implementation = receipt.get("implementation")
    if not isinstance(implementation, Mapping):
        raise TransportAnalysisError(f"{arm}/{role} implementation receipt is missing")
    expected_implementation = authority.get("expected_run_implementation_sha256")
    if (
        expected_implementation is not None
        and implementation.get("source_tree_sha256") != expected_implementation
    ):
        raise TransportAnalysisError(
            f"{arm}/{role} implementation differs from manifest"
        )
    model_identity = _validate_model_identity(receipt, authority, arm, role)
    model_receipt = receipt.get("model_receipt")
    if (
        not isinstance(model_receipt, Mapping)
        or _without_runtime_noise(model_receipt) != model_identity["payload"]
    ):
        raise TransportAnalysisError(f"{arm}/{role} model receipt/identity differ")
    environment = _validate_environment(receipt, authority, arm, role)

    resolved_inputs_path = run_dir / "resolved_inputs.json"
    resolved_inputs = _read_json_object(
        resolved_inputs_path, f"{arm}/{role} resolved inputs"
    )
    if resolved_inputs.get("panel") != spec["panel_items"]:
        raise TransportAnalysisError(f"{arm}/{role} resolved panel differs")
    if resolved_inputs.get("target_ids") != list(authority["target_ids"]):
        raise TransportAnalysisError(f"{arm}/{role} resolved targets differ")
    if resolved_inputs.get("wrapper_ids") != list(authority["wrapper_ids"]):
        raise TransportAnalysisError(f"{arm}/{role} resolved wrappers differ")

    condition_count = int(spec["condition_count"])
    run_inventory_hashes = _validate_run_inventory(run_dir, arm, role, spec, authority)
    summary, summary_path = _validate_summary(run_dir, arm, role, condition_count)
    screening, screening_path = _load_fingerprint_screening(
        run_dir, arm, role, condition_count
    )
    direction_by_seed, direction_replicates_path = _validate_direction_replicates(
        run_dir, arm, role
    )
    ledger_path = run_dir / "interventions.jsonl"
    rows = _read_jsonl(ledger_path, f"{arm}/{role} intervention ledger")
    positive_rows = len(LAYERS) * len(DIRECTION_SEEDS) * condition_count * 24
    random_rows = len(LAYERS) * len(DIRECTION_SEEDS) * 2 * 24
    zero_rows = len(LAYERS) * 24
    expected_total = positive_rows + random_rows + zero_rows
    if len(rows) != expected_total:
        raise TransportAnalysisError(
            f"{arm}/{role} ledger row count differs: expected {expected_total}, "
            f"observed {len(rows)}"
        )
    condition_counts = Counter(row.get("condition_type") for row in rows)
    expected_condition_counts = {
        "emoji": positive_rows,
        "random": random_rows,
        "zero": zero_rows,
    }
    if condition_counts != Counter(expected_condition_counts):
        raise TransportAnalysisError(f"{arm}/{role} ledger condition counts differ")

    target_ids = set(authority["target_ids"])
    target_index_by_id = {
        target_id: index for index, target_id in enumerate(authority["target_ids"])
    }
    random_counts: Counter[tuple[int, int]] = Counter()
    random_targets: dict[tuple[int, int, str], set[str]] = defaultdict(set)
    zero_by_layer: dict[int, dict[str, Any]] = {}
    vectors: dict[tuple[int, int, str, str], np.ndarray] = {}
    ledger_task_keys: list[tuple[Any, ...]] = []
    condition_to_glyph = dict(zip(spec["condition_ids"], spec["glyphs"]))
    for line_number, row in enumerate(rows, 1):
        _validate_finite_tree(row, field=f"{arm}.{role}.ledger[{line_number}]")
        condition_type = row.get("condition_type")
        if condition_type not in {"emoji", "random", "zero"}:
            raise TransportAnalysisError(
                f"{arm}/{role} ledger has unknown condition type"
            )
        _validate_intervention_metrics(
            row,
            arm=arm,
            role=role,
            zero_hook=condition_type == "zero",
        )
        layer = int(_finite(row.get("layer"), field="ledger.layer"))
        seed = int(_finite(row.get("seed"), field="ledger.seed"))
        strength = _finite(row.get("strength"), field="ledger.strength")
        target_id = row.get("target_id")
        target_group = row.get("target_group")
        if (
            layer not in LAYERS
            or target_id not in target_ids
            or target_group != authority["target_groups"][target_id]
            or row.get("target_index") != target_index_by_id[target_id]
        ):
            raise TransportAnalysisError(f"{arm}/{role} ledger target/cell differs")
        if condition_type == "emoji":
            condition_id = row.get("condition_id")
            if (
                seed not in DIRECTION_SEEDS
                or strength != STRENGTH
                or row.get("sign") != 1
                or row.get("calibration") != "rms"
                or condition_id not in condition_to_glyph
                or row.get("glyph") != condition_to_glyph[condition_id]
                or row.get("direction_wrapper_indices") != list(direction_by_seed[seed])
            ):
                raise TransportAnalysisError(f"{arm}/{role} has invalid emoji row")
            _validate_scale(row, arm=arm, role=role, zero_hook=False)
            key = (layer, seed, str(condition_id), str(target_id))
            ledger_task_keys.append(
                ("emoji", layer, seed, str(condition_id), str(target_id))
            )
            if key in vectors:
                raise TransportAnalysisError(f"{arm}/{role} duplicates emoji row {key}")
            vectors[key] = _fingerprint(row, line_number=line_number, allow_zero=False)
        elif condition_type == "random":
            condition_id = row.get("condition_id")
            if (
                seed not in DIRECTION_SEEDS
                or strength != STRENGTH
                or row.get("sign") != 1
                or row.get("calibration") != "rms"
                or condition_id not in {"random_00", "random_01"}
                or row.get("glyph") is not None
                or row.get("direction_wrapper_indices") != list(direction_by_seed[seed])
            ):
                raise TransportAnalysisError(f"{arm}/{role} has invalid random row")
            _validate_scale(row, arm=arm, role=role, zero_hook=False)
            _fingerprint(row, line_number=line_number, allow_zero=False)
            ledger_task_keys.append(
                ("random", layer, seed, str(condition_id), str(target_id))
            )
            random_counts[(layer, seed)] += 1
            key = (layer, seed, str(condition_id))
            if target_id in random_targets[key]:
                raise TransportAnalysisError(f"{arm}/{role} duplicates random target")
            random_targets[key].add(str(target_id))
        else:
            if (
                seed != DIRECTION_SEEDS[0]
                or strength != 0.0
                or row.get("sign") != 0
                or row.get("calibration") != "zero_hook"
                or row.get("condition_id") != "__zero_hook__"
                or row.get("glyph") is not None
                or row.get("direction_wrapper_indices") != []
            ):
                raise TransportAnalysisError(f"{arm}/{role} has invalid zero-hook row")
            _validate_scale(row, arm=arm, role=role, zero_hook=True)
            _fingerprint(row, line_number=line_number, allow_zero=True)
            ledger_task_keys.append(
                ("zero", layer, seed, "__zero_hook__", str(target_id))
            )
            distribution = row.get("distribution")
            activation = row.get("activation")
            if not isinstance(distribution, Mapping) or not isinstance(
                activation, Mapping
            ):
                raise TransportAnalysisError(
                    f"{arm}/{role} zero-hook metrics are missing"
                )
            logit_error = _finite(
                distribution.get("logit_delta_rms"), field="zero.logit_delta_rms"
            )
            activation_error = _finite(
                activation.get("actual_activation_delta_rms"),
                field="zero.actual_activation_delta_rms",
            )
            cell = zero_by_layer.setdefault(
                layer,
                {"target_ids": set(), "logit_errors": [], "activation_errors": []},
            )
            if target_id in cell["target_ids"]:
                raise TransportAnalysisError(
                    f"{arm}/{role} duplicates zero-hook target"
                )
            cell["target_ids"].add(str(target_id))
            cell["logit_errors"].append(logit_error)
            cell["activation_errors"].append(activation_error)

    _validate_ledger_task_keys(
        ledger_task_keys,
        spec["condition_ids"],
        authority["target_ids"],
        arm=arm,
        role=role,
    )

    expected_vector_keys = {
        (layer, seed, condition_id, target_id)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_id in spec["condition_ids"]
        for target_id in authority["target_ids"]
    }
    if set(vectors) != expected_vector_keys:
        raise TransportAnalysisError(
            f"{arm}/{role} positive fingerprint grid is incomplete"
        )
    expected_random_counts = {
        (layer, seed): 48 for layer in LAYERS for seed in DIRECTION_SEEDS
    }
    if dict(random_counts) != expected_random_counts:
        raise TransportAnalysisError(f"{arm}/{role} random-control grid is incomplete")
    expected_random_keys = {
        (layer, seed, condition_id)
        for layer in LAYERS
        for seed in DIRECTION_SEEDS
        for condition_id in ("random_00", "random_01")
    }
    if set(random_targets) != expected_random_keys or any(
        values != target_ids for values in random_targets.values()
    ):
        raise TransportAnalysisError(f"{arm}/{role} random-control targets differ")
    if set(zero_by_layer) != set(LAYERS):
        raise TransportAnalysisError(f"{arm}/{role} zero-hook grid is incomplete")
    zero_summary: dict[int, dict[str, Any]] = {}
    for layer in LAYERS:
        cell = zero_by_layer[layer]
        if cell["target_ids"] != target_ids:
            raise TransportAnalysisError(f"{arm}/{role} zero-hook targets differ")
        max_logit = max(cell["logit_errors"])
        max_activation = max(cell["activation_errors"])
        if max_logit > ZERO_HOOK_TOLERANCE or max_activation > ZERO_HOOK_TOLERANCE:
            raise TransportAnalysisError(f"{arm}/{role} zero-hook tolerance failed")
        zero_summary[layer] = {
            "row_count": 24,
            "max_logit_delta_rms": max_logit,
            "max_activation_delta_rms": max_activation,
        }
    return {
        "panel_arm": arm,
        "role": role,
        "run_dir": run_dir,
        "config_path": config_path,
        "receipt_path": receipt_path,
        "resolved_inputs_path": resolved_inputs_path,
        "summary_path": summary_path,
        "screening_path": screening_path,
        "direction_replicates_path": direction_replicates_path,
        "ledger_path": ledger_path,
        "vectors": vectors,
        "condition_ids": spec["condition_ids"],
        "screening": screening,
        "summary": summary,
        "model_identity": model_identity,
        "implementation": dict(implementation),
        "environment": environment,
        "run_inventory_hashes": run_inventory_hashes,
        "run_id": run_id,
        "run_seal": run_seal,
        "started_at": receipt.get("started_at"),
        "finished_at": receipt.get("finished_at"),
        "ledger_row_count": len(rows),
        "eligible_row_count": len(vectors),
        "condition_counts": expected_condition_counts,
        "random_cell_counts": dict(random_counts),
        "zero_summary_by_layer": zero_summary,
    }


def _group_indices(
    target_ids: Sequence[str], target_groups: Mapping[str, str]
) -> tuple[tuple[int, ...], ...]:
    groups: list[tuple[int, ...]] = []
    for group in TARGET_GROUPS:
        indices = tuple(
            index
            for index, target_id in enumerate(target_ids)
            if target_groups[target_id] == group
        )
        if len(indices) != TARGETS_PER_GROUP:
            raise TransportAnalysisError(f"Target group {group} is not size four")
        groups.append(indices)
    return tuple(groups)


def _joint_bootstrap_design(
    target_ids: Sequence[str], target_groups: Mapping[str, str]
) -> tuple[
    tuple[tuple[int, ...], ...],
    np.ndarray,
    np.ndarray,
]:
    """Build the one frozen target-resample design shared by every E2 arm."""

    group_indices = _group_indices(target_ids, target_groups)
    weights, draws = _bootstrap_weights(
        BOOTSTRAP_REPLICATES,
        BOOTSTRAP_SEED,
        len(target_ids),
        group_indices,
    )
    return group_indices, weights, draws


def _bootstrap_weights(
    replicates: int,
    seed: int,
    target_count: int,
    group_indices: Sequence[Sequence[int]],
) -> tuple[np.ndarray, np.ndarray]:
    """Delegate the joint stratified target draws to the frozen E1 analyzer."""

    try:
        return e1_math._bootstrap_weights(replicates, seed, target_count, group_indices)
    except e1_math.ExploratoryAnalysisError as exc:
        raise TransportAnalysisError(str(exc)) from exc


def _score_layer_chunk_by_seed(
    layer_vectors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> np.ndarray:
    """Return [replicate, source family, prototype family, seed, target].

    The full50 arm delegates exactly to the frozen E1 implementation.  The
    core35 arm applies the same formula with seven slots rather than E1's
    hard-coded ten-slot shape check.
    """

    if layer_vectors.ndim != 5:
        raise TransportAnalysisError("Layer tensor must be family/seed/slot/target/dim")
    family_count, seed_count, slot_count, target_count, _ = layer_vectors.shape
    if family_count != len(FAMILY_ORDER) or seed_count != len(DIRECTION_SEEDS):
        raise TransportAnalysisError("Layer tensor family/seed grid differs")
    if slot_count == ARM_DEFINITIONS["full50"]["conditions_per_family"]:
        try:
            return e1_math._score_layer_chunk_by_seed(
                layer_vectors, weights, group_indices
            )
        except e1_math.ExploratoryAnalysisError as exc:
            raise TransportAnalysisError(str(exc)) from exc
    if slot_count != ARM_DEFINITIONS["core35"]["conditions_per_family"]:
        raise TransportAnalysisError(
            "Layer tensor slot count is neither full50 nor core35"
        )
    if weights.ndim != 2 or weights.shape[1] != target_count:
        raise TransportAnalysisError("Bootstrap weights do not match target tensor")
    floating_weights = weights.astype(np.float64, copy=False)
    scores = np.empty(
        (weights.shape[0], family_count, family_count, seed_count, target_count),
        dtype=np.float64,
    )
    total_sums = np.einsum(
        "bt,fsctd->bfscd", floating_weights, layer_vectors, optimize=True
    )
    covered: set[int] = set()
    for raw_indices in group_indices:
        held = np.asarray(raw_indices, dtype=np.int64)
        covered.update(int(value) for value in held)
        held_vectors = layer_vectors[:, :, :, held, :]
        held_sums = np.einsum(
            "bh,fschd->bfscd", floating_weights[:, held], held_vectors, optimize=True
        )
        training_sums = total_sums - held_sums
        norms = np.linalg.norm(training_sums, axis=-1, keepdims=True)
        if np.any(norms <= EPSILON) or not np.all(np.isfinite(norms)):
            raise TransportAnalysisError(
                "A resampled leave-one-group-out prototype has zero/non-finite norm"
            )
        prototypes = training_sums / norms
        same_sum = np.einsum(
            "bqscd,aschd->baqsh", prototypes, held_vectors, optimize=True
        )
        all_sum = np.einsum(
            "bqsd,ashd->baqsh",
            prototypes.sum(axis=3),
            held_vectors.sum(axis=2),
            optimize=True,
        )
        scores[:, :, :, :, held] = (slot_count * same_sum - all_sum) / (
            slot_count * (slot_count - 1)
        )
    if covered != set(range(target_count)) or not np.all(np.isfinite(scores)):
        raise TransportAnalysisError(
            "Endpoint score target grid is incomplete/non-finite"
        )
    return scores


def _tensor(runs: Sequence[Mapping[str, Any]], target_ids: Sequence[str]) -> np.ndarray:
    if len(runs) != len(FAMILY_ORDER):
        raise TransportAnalysisError("An arm must contain five family runs")
    condition_count = len(runs[0]["condition_ids"])
    if any(len(run["condition_ids"]) != condition_count for run in runs):
        raise TransportAnalysisError("An arm has inconsistent panel sizes")
    tensor = np.empty(
        (
            len(FAMILY_ORDER),
            len(LAYERS),
            len(DIRECTION_SEEDS),
            condition_count,
            len(target_ids),
            FINGERPRINT_DIM,
        ),
        dtype=np.float64,
    )
    for family_index, run in enumerate(runs):
        if run["role"] != FAMILY_ORDER[family_index]:
            raise TransportAnalysisError("Family run order differs")
        for layer_index, layer in enumerate(LAYERS):
            for seed_index, seed in enumerate(DIRECTION_SEEDS):
                for slot_index, condition_id in enumerate(run["condition_ids"]):
                    for target_index, target_id in enumerate(target_ids):
                        tensor[
                            family_index,
                            layer_index,
                            seed_index,
                            slot_index,
                            target_index,
                        ] = run["vectors"][(layer, seed, condition_id, target_id)]
    return tensor


def _observed_endpoints(
    tensor: np.ndarray, group_indices: Sequence[Sequence[int]]
) -> dict[str, np.ndarray]:
    if tensor.shape[3] == ARM_DEFINITIONS["full50"]["conditions_per_family"]:
        try:
            return e1_math._observed_endpoints(tensor, group_indices)
        except e1_math.ExploratoryAnalysisError as exc:
            raise TransportAnalysisError(str(exc)) from exc
    layer_count, family_count, target_count = (
        tensor.shape[1],
        tensor.shape[0],
        tensor.shape[-2],
    )
    seed_scores = np.empty(
        (layer_count, family_count, family_count, len(DIRECTION_SEEDS), target_count),
        dtype=np.float64,
    )
    unit_weights = np.ones((1, target_count), dtype=np.int16)
    for layer_index in range(layer_count):
        seed_scores[layer_index] = _score_layer_chunk_by_seed(
            tensor[:, layer_index], unit_weights, group_indices
        )[0]
    target_matrix = seed_scores.mean(axis=3)
    within = np.stack(
        [target_matrix[:, index, index] for index in range(family_count)], axis=1
    )
    cross_median = np.stack(
        [
            np.median(
                target_matrix[:, source][
                    :,
                    np.asarray(
                        [
                            destination
                            for destination in range(family_count)
                            if destination != source
                        ]
                    ),
                    :,
                ],
                axis=1,
            )
            for source in range(family_count)
        ],
        axis=1,
    )
    specificity = within - cross_median
    return {
        "seed_scores": seed_scores,
        "target_matrix": target_matrix,
        "within": within,
        "cross_median": cross_median,
        "specificity": specificity,
        "global_specificity": specificity.mean(axis=1),
    }


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    try:
        return e1_math._weighted_mean(values, weights)
    except e1_math.ExploratoryAnalysisError as exc:
        raise TransportAnalysisError(str(exc)) from exc


def _bootstrap_endpoints(
    tensor: np.ndarray,
    weights: np.ndarray,
    draws: np.ndarray,
    group_indices: Sequence[Sequence[int]],
    *,
    chunk_size: int,
) -> dict[str, np.ndarray]:
    if tensor.shape[3] == ARM_DEFINITIONS["full50"]["conditions_per_family"]:
        try:
            return e1_math._bootstrap_endpoints(
                tensor, weights, draws, group_indices, chunk_size=chunk_size
            )
        except e1_math.ExploratoryAnalysisError as exc:
            raise TransportAnalysisError(str(exc)) from exc
    if chunk_size <= 0:
        raise TransportAnalysisError("Bootstrap chunk size must be positive")
    layer_count = tensor.shape[1]
    family_count = tensor.shape[0]
    replicates = weights.shape[0]
    matrix_means = np.empty(
        (layer_count, replicates, family_count, family_count), dtype=np.float64
    )
    specificity_means = np.empty(
        (layer_count, replicates, family_count), dtype=np.float64
    )
    global_specificity = np.empty((layer_count, replicates), dtype=np.float64)
    for layer_index in range(layer_count):
        for start in range(0, replicates, chunk_size):
            stop = min(start + chunk_size, replicates)
            seed_scores = _score_layer_chunk_by_seed(
                tensor[:, layer_index], weights[start:stop], group_indices
            )
            target_scores = seed_scores.mean(axis=3)
            matrix_means[layer_index, start:stop] = _weighted_mean(
                target_scores, weights[start:stop]
            )
            diagonal = np.stack(
                [target_scores[:, index, index] for index in range(family_count)],
                axis=1,
            )
            cross_medians = np.stack(
                [
                    np.median(
                        target_scores[:, source][
                            :,
                            np.asarray(
                                [
                                    destination
                                    for destination in range(family_count)
                                    if destination != source
                                ]
                            ),
                            :,
                        ],
                        axis=1,
                    )
                    for source in range(family_count)
                ],
                axis=1,
            )
            specificity = diagonal - cross_medians
            chunk_weights = weights[start:stop].astype(np.float64, copy=False)
            family_means = (
                np.sum(specificity * chunk_weights[:, None, :], axis=2)
                / chunk_weights.sum(axis=1)[:, None]
            )
            specificity_means[layer_index, start:stop] = family_means
            global_specificity[layer_index, start:stop] = family_means.mean(axis=1)
    return {
        "matrix_means": matrix_means,
        "specificity_means": specificity_means,
        "global_specificity": global_specificity,
    }


def _interval(values: np.ndarray) -> dict[str, float]:
    return e1_math._interval(values)


def _target_group_means(
    values: np.ndarray,
    target_ids: Sequence[str],
    target_groups: Mapping[str, str],
) -> dict[str, float]:
    if values.ndim != 1 or values.size != len(target_ids):
        raise TransportAnalysisError("Target-group summary values have invalid shape")
    return {
        group: float(
            np.mean(
                [
                    values[index]
                    for index, target_id in enumerate(target_ids)
                    if target_groups[target_id] == group
                ]
            )
        )
        for group in TARGET_GROUPS
    }


def _layer_role(arm: str, layer: int) -> str:
    if arm == "full50" and layer == PRIMARY_LAYER:
        return "primary"
    if arm == "full50" and layer == SECONDARY_LAYER:
        return "prespecified_secondary_depth_comparator"
    if arm == "core35" and layer == PRIMARY_LAYER:
        return "prespecified_secondary_token_isomorphic_sensitivity"
    if arm == "core35" and layer == SECONDARY_LAYER:
        return "prespecified_secondary_token_isomorphic_depth_comparator"
    raise TransportAnalysisError(f"Unexpected arm/layer: {arm}/{layer}")


def _assert_exact_keys(
    rows: Sequence[Mapping[str, Any]],
    fields: Sequence[str],
    expected: set[tuple[Any, ...]],
    description: str,
) -> None:
    observed = [tuple(row.get(field) for field in fields) for row in rows]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise TransportAnalysisError(f"{description} unique-key grid differs")


def _expected_ledger_task_keys(
    condition_ids: Sequence[str], target_ids: Sequence[str]
) -> set[tuple[Any, ...]]:
    return (
        {
            ("emoji", layer, seed, condition_id, target_id)
            for layer in LAYERS
            for seed in DIRECTION_SEEDS
            for condition_id in condition_ids
            for target_id in target_ids
        }
        | {
            ("random", layer, seed, condition_id, target_id)
            for layer in LAYERS
            for seed in DIRECTION_SEEDS
            for condition_id in ("random_00", "random_01")
            for target_id in target_ids
        }
        | {
            ("zero", layer, DIRECTION_SEEDS[0], "__zero_hook__", target_id)
            for layer in LAYERS
            for target_id in target_ids
        }
    )


def _validate_ledger_task_keys(
    observed: Sequence[tuple[Any, ...]],
    condition_ids: Sequence[str],
    target_ids: Sequence[str],
    *,
    arm: str,
    role: str,
) -> None:
    expected = _expected_ledger_task_keys(condition_ids, target_ids)
    if len(observed) != len(set(observed)):
        raise TransportAnalysisError(f"{arm}/{role} ledger task grid has duplicates")
    observed_set = set(observed)
    if observed_set != expected:
        missing = len(expected - observed_set)
        extra = len(observed_set - expected)
        raise TransportAnalysisError(
            f"{arm}/{role} ledger task grid differs: {missing} missing and {extra} extra"
        )


def _primary_criterion_met(interval: Mapping[str, Any]) -> bool:
    """Apply the frozen strict lower-bound rule; equality with zero does not pass."""

    low = _finite(interval.get("low"), field="primary_criterion.ci95.low")
    _finite(interval.get("high"), field="primary_criterion.ci95.high")
    return bool(low > 0.0)


def _primary_status(interval: Mapping[str, Any]) -> str:
    return (
        "transport_criterion_met"
        if _primary_criterion_met(interval)
        else "transport_criterion_not_met"
    )


def _build_arm_rows(
    arm: str,
    runs: Sequence[Mapping[str, Any]],
    authority: Mapping[str, Any],
    observed: Mapping[str, np.ndarray],
    bootstrap: Mapping[str, np.ndarray],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    target_ids = authority["target_ids"]
    target_groups = authority["target_groups"]
    panel_target_rows: list[dict[str, Any]] = []
    transfer_target_rows: list[dict[str, Any]] = []
    family_cell_rows: list[dict[str, Any]] = []
    transfer_cell_rows: list[dict[str, Any]] = []
    layer_results: list[dict[str, Any]] = []
    for layer_index, layer in enumerate(LAYERS):
        layer_role = _layer_role(arm, layer)
        target_matrix = observed["target_matrix"][layer_index]
        seed_scores = observed["seed_scores"][layer_index]
        specificity = observed["specificity"][layer_index]
        cross_median = observed["cross_median"][layer_index]
        for family_index, family in enumerate(FAMILY_ORDER):
            for target_index, target_id in enumerate(target_ids):
                panel_target_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "analysis_id": ANALYSIS_ID,
                        "panel_arm": arm,
                        "endpoint_ids": [ENDPOINT_WITHIN, ENDPOINT_SPECIFICITY],
                        "family": family,
                        "layer": layer,
                        "layer_role": layer_role,
                        "strength": STRENGTH,
                        "target_id": target_id,
                        "target_group": target_groups[target_id],
                        "within_family_M_by_direction_seed": {
                            str(seed): float(
                                seed_scores[
                                    family_index, family_index, seed_index, target_index
                                ]
                            )
                            for seed_index, seed in enumerate(DIRECTION_SEEDS)
                        },
                        "within_family_M": float(
                            observed["within"][layer_index, family_index, target_index]
                        ),
                        "cross_family_transfer_median_M": float(
                            cross_median[family_index, target_index]
                        ),
                        "family_specificity_R": float(
                            specificity[family_index, target_index]
                        ),
                    }
                )
            within_values = observed["within"][layer_index, family_index]
            specificity_values = specificity[family_index]
            controls = []
            run = runs[family_index]
            for seed in DIRECTION_SEEDS:
                controls.append(
                    {
                        "seed": seed,
                        "random_intervention_row_count": run["random_cell_counts"][
                            (layer, seed)
                        ],
                        **run["screening"][(layer, seed)],
                    }
                )
            family_cell_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "analysis_id": ANALYSIS_ID,
                    "panel_arm": arm,
                    "endpoint_ids": [ENDPOINT_WITHIN, ENDPOINT_SPECIFICITY],
                    "family": family,
                    "layer": layer,
                    "layer_role": layer_role,
                    "strength": STRENGTH,
                    "condition_count": len(run["condition_ids"]),
                    "target_count": len(target_ids),
                    "direction_seeds": list(DIRECTION_SEEDS),
                    "within_family_M_target_mean": float(np.mean(within_values)),
                    "within_family_M_target_mean_ci95": _interval(
                        bootstrap["matrix_means"][
                            layer_index, :, family_index, family_index
                        ]
                    ),
                    "within_family_M_target_median_secondary": float(
                        np.median(within_values)
                    ),
                    "within_family_M_target_group_means_secondary": _target_group_means(
                        within_values, target_ids, target_groups
                    ),
                    "cross_family_transfer_median_M_target_mean": float(
                        np.mean(cross_median[family_index])
                    ),
                    "family_specificity_R_target_mean": float(
                        np.mean(specificity_values)
                    ),
                    "family_specificity_R_target_mean_ci95": _interval(
                        bootstrap["specificity_means"][layer_index, :, family_index]
                    ),
                    "family_specificity_R_target_median_secondary": float(
                        np.median(specificity_values)
                    ),
                    "family_specificity_R_target_group_means_secondary": _target_group_means(
                        specificity_values, target_ids, target_groups
                    ),
                    "descriptive_fingerprint_controls_by_direction_seed": controls,
                    "zero_hook_control": run["zero_summary_by_layer"][layer],
                    "control_use": "descriptive_only; not endpoint observations",
                }
            )

        for source_index, source_family in enumerate(FAMILY_ORDER):
            for prototype_index, prototype_family in enumerate(FAMILY_ORDER):
                if source_index == prototype_index:
                    continue
                values = target_matrix[source_index, prototype_index]
                for target_index, target_id in enumerate(target_ids):
                    transfer_target_rows.append(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "analysis_id": ANALYSIS_ID,
                            "panel_arm": arm,
                            "endpoint_id": ENDPOINT_TRANSFER,
                            "source_family": source_family,
                            "prototype_family": prototype_family,
                            "matrix_notation": f"{source_family}<-{prototype_family}",
                            "layer": layer,
                            "layer_role": layer_role,
                            "strength": STRENGTH,
                            "target_id": target_id,
                            "target_group": target_groups[target_id],
                            "cross_family_M_by_direction_seed": {
                                str(seed): float(
                                    seed_scores[
                                        source_index,
                                        prototype_index,
                                        seed_index,
                                        target_index,
                                    ]
                                )
                                for seed_index, seed in enumerate(DIRECTION_SEEDS)
                            },
                            "cross_family_M": float(values[target_index]),
                        }
                    )
                transfer_cell_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "analysis_id": ANALYSIS_ID,
                        "panel_arm": arm,
                        "endpoint_id": ENDPOINT_TRANSFER,
                        "source_family": source_family,
                        "prototype_family": prototype_family,
                        "matrix_notation": f"{source_family}<-{prototype_family}",
                        "layer": layer,
                        "layer_role": layer_role,
                        "strength": STRENGTH,
                        "target_count": len(target_ids),
                        "direction_seeds": list(DIRECTION_SEEDS),
                        "cross_family_M_target_mean": float(np.mean(values)),
                        "cross_family_M_target_mean_ci95": _interval(
                            bootstrap["matrix_means"][
                                layer_index, :, source_index, prototype_index
                            ]
                        ),
                        "cross_family_M_target_median_secondary": float(
                            np.median(values)
                        ),
                        "cross_family_M_target_group_means_secondary": _target_group_means(
                            values, target_ids, target_groups
                        ),
                    }
                )

        matrix_cells = []
        for source_index, source_family in enumerate(FAMILY_ORDER):
            for prototype_index, prototype_family in enumerate(FAMILY_ORDER):
                values = target_matrix[source_index, prototype_index]
                matrix_cells.append(
                    {
                        "source_family": source_family,
                        "prototype_family": prototype_family,
                        "diagonal": source_index == prototype_index,
                        "target_mean": float(np.mean(values)),
                        "target_mean_ci95": _interval(
                            bootstrap["matrix_means"][
                                layer_index, :, source_index, prototype_index
                            ]
                        ),
                        "target_median_secondary": float(np.median(values)),
                    }
                )
        family_specificity = [
            {
                "family": family,
                "target_mean": float(np.mean(specificity[family_index])),
                "target_mean_ci95": _interval(
                    bootstrap["specificity_means"][layer_index, :, family_index]
                ),
                "target_median_secondary": float(np.median(specificity[family_index])),
            }
            for family_index, family in enumerate(FAMILY_ORDER)
        ]
        global_values = observed["global_specificity"][layer_index]
        layer_results.append(
            {
                "panel_arm": arm,
                "layer": layer,
                "layer_role": layer_role,
                "full_M_matrix": {
                    "row_role": "source_family_fingerprints",
                    "column_role": "prototype_family",
                    "family_order": list(FAMILY_ORDER),
                    "cells": matrix_cells,
                },
                "family_specificity_R": family_specificity,
                "equal_family_global_specificity_R_global": {
                    "target_mean": float(np.mean(global_values)),
                    "target_mean_ci95": _interval(
                        bootstrap["global_specificity"][layer_index]
                    ),
                    "target_median_secondary": float(np.median(global_values)),
                },
            }
        )
    return (
        panel_target_rows,
        transfer_target_rows,
        family_cell_rows,
        transfer_cell_rows,
        layer_results,
    )


def _input_record(
    run: Mapping[str, Any], authority: Mapping[str, Any]
) -> dict[str, Any]:
    spec = authority["roles"][run["panel_arm"]][run["role"]]
    return {
        "panel_arm": run["panel_arm"],
        "role": run["role"],
        "run_label": run["run_dir"].name,
        "fixed_config_file": spec["config"].as_posix(),
        "fixed_config_sha256": spec["config_sha256"],
        "fixed_panel_file": spec["panel"].as_posix(),
        "fixed_panel_sha256": spec["panel_sha256"],
        "interventions_sha256": _sha256_file(run["ledger_path"]),
        "resolved_config_sha256": _sha256_file(run["config_path"]),
        "run_receipt_sha256": _sha256_file(run["receipt_path"]),
        "resolved_inputs_sha256": _sha256_file(run["resolved_inputs_path"]),
        "summary_sha256": _sha256_file(run["summary_path"]),
        "fingerprint_summary_sha256": _sha256_file(run["screening_path"]),
        "direction_replicates_sha256": _sha256_file(run["direction_replicates_path"]),
        "model_identity_sha256": run["model_identity"]["sha256"],
        "run_implementation_sha256": run["implementation"].get("source_tree_sha256"),
        "environment_sha256": _stable_sha256(run["environment"]),
        "complete_run_file_inventory_sha256": _stable_sha256(
            run["run_inventory_hashes"]
        ),
        "complete_run_file_inventory": run["run_inventory_hashes"],
        "positive_emoji_row_count": run["eligible_row_count"],
        "random_control_row_count": run["condition_counts"]["random"],
        "zero_hook_row_count": run["condition_counts"]["zero"],
    }


def _format_estimate(value: float, interval: Mapping[str, float]) -> str:
    return f"{value:.6f} [{interval['low']:.6f}, {interval['high']:.6f}]"


def _render_report(
    results_by_arm: Mapping[str, Sequence[Mapping[str, Any]]],
    paired_differences: Sequence[Mapping[str, Any]],
    primary: Mapping[str, Any],
    runs: Sequence[Mapping[str, Any]],
) -> str:
    final_status = (
        "transport_criterion_met"
        if primary["criterion_met"]
        else "transport_criterion_not_met"
    )
    lines = [
        "# Llama-3.2-3B MPS emoji-transport report",
        "",
        "This stored-fingerprint analysis compares the independently centered "
        "full50 and token-isomorphic core35 panel arms on the fixed 24-target "
        "prestage bank. It is a bounded cross-model transport experiment.",
        "",
        "## Primary criterion",
        "",
        f"- ID: `{PRIMARY_CRITERION_ID}`",
        "- Rule: full50 layer-5 R_global 95% bootstrap interval lower bound > 0",
        f"- Estimate: {_format_estimate(primary['target_mean'], primary['target_mean_ci95'])}",
        f"- Criterion met: **{str(primary['criterion_met']).lower()}**",
        f"- Final status: `{final_status}`",
        "",
        "The criterion is a prespecified decision for this exploratory transport "
        "cell; it is not a confirmatory holdout or paper-gate decision.",
        "",
        "## Complete prespecified endpoint summaries",
        "",
        "Every displayed interval is the frozen joint 20,000-replicate, "
        "group-stratified target-bootstrap interval. The row family supplies "
        "fingerprints and the column family supplies the LOTO prototype.",
    ]
    for arm in ARM_ORDER:
        for row in results_by_arm[arm]:
            lines.extend(
                [
                    "",
                    f"### {arm} layer {row['layer']} — {row['layer_role']}",
                    "",
                    "#### Full M matrix",
                    "",
                    "| source \\ prototype | " + " | ".join(FAMILY_ORDER) + " |",
                    "|---|" + "---:|" * len(FAMILY_ORDER),
                ]
            )
            cells = {
                (cell["source_family"], cell["prototype_family"]): cell
                for cell in row["full_M_matrix"]["cells"]
            }
            for source_family in FAMILY_ORDER:
                estimates = []
                for prototype_family in FAMILY_ORDER:
                    cell = cells[(source_family, prototype_family)]
                    estimates.append(
                        _format_estimate(cell["target_mean"], cell["target_mean_ci95"])
                    )
                lines.append(f"| {source_family} | " + " | ".join(estimates) + " |")
            lines.extend(
                [
                    "",
                    "#### Family specificity R",
                    "",
                    "| family | target mean [95% bootstrap interval] | target median (secondary) |",
                    "|---|---:|---:|",
                ]
            )
            for family_row in row["family_specificity_R"]:
                lines.append(
                    f"| {family_row['family']} | "
                    f"{_format_estimate(family_row['target_mean'], family_row['target_mean_ci95'])} | "
                    f"{family_row['target_median_secondary']:.6f} |"
                )
            global_row = row["equal_family_global_specificity_R_global"]
            lines.extend(
                [
                    "",
                    "#### Equal-family global specificity R_global",
                    "",
                    f"- Target mean [95% bootstrap interval]: "
                    f"{_format_estimate(global_row['target_mean'], global_row['target_mean_ci95'])}",
                    f"- Target median (secondary): {global_row['target_median_secondary']:.6f}",
                ]
            )
    lines.extend(
        [
            "",
            "## Paired core35-minus-full50 descriptions",
            "",
            "Both arms use the same target-bootstrap multiplicities, while every "
            "arm's LOTO prototypes are rebuilt independently inside each replicate.",
            "",
            "| layer | paired R_global difference [95% bootstrap interval] |",
            "|---:|---:|",
        ]
    )
    for row in paired_differences:
        lines.append(
            f"| {row['layer']} | "
            f"{_format_estimate(row['target_mean_difference'], row['target_mean_difference_ci95'])} |"
        )
    lines.extend(
        [
            "",
            "## Complete random-direction screening diagnostics",
            "",
            "These 60 prespecified arm/family/layer/seed cells are descriptive "
            "integrity diagnostics and are not endpoint observations.",
            "",
            "| arm | family | layer | seed | emoji same | emoji cross | emoji separation | emoji repeat mean [95% interval] | random same | random cross | random separation | random repeat mean [95% interval] | emoji advantage | random rows |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for run in runs:
        for layer in LAYERS:
            for seed in DIRECTION_SEEDS:
                diagnostic = run["screening"][(layer, seed)]
                lines.append(
                    f"| {run['panel_arm']} | {run['role']} | {layer} | {seed} | "
                    f"{diagnostic['emoji_same_split_cosine']:.6f} | "
                    f"{diagnostic['emoji_cross_cosine']:.6f} | "
                    f"{diagnostic['emoji_separation']:.6f} | "
                    f"{diagnostic['emoji_split_repeat_mean']:.6f} "
                    f"[{diagnostic['emoji_split_repeat_ci_low']:.6f}, "
                    f"{diagnostic['emoji_split_repeat_ci_high']:.6f}] | "
                    f"{diagnostic['random_same_split_cosine']:.6f} | "
                    f"{diagnostic['random_cross_cosine']:.6f} | "
                    f"{diagnostic['random_separation']:.6f} | "
                    f"{diagnostic['random_split_repeat_mean']:.6f} "
                    f"[{diagnostic['random_split_repeat_ci_low']:.6f}, "
                    f"{diagnostic['random_split_repeat_ci_high']:.6f}] | "
                    f"{diagnostic['emoji_advantage_over_random']:.6f} | "
                    f"{run['random_cell_counts'][(layer, seed)]} |"
                )
    lines.extend(
        [
            "",
            "## Run integrity and zero-hook controls",
            "",
            "| arm | family | ledger rows | emoji fingerprints | random rows | zero rows | max zero activation RMS | max zero logit RMS |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for run in runs:
        lines.append(
            f"| {run['panel_arm']} | {run['role']} | {run['ledger_row_count']} | "
            f"{run['eligible_row_count']} | {run['condition_counts']['random']} | "
            f"{run['condition_counts']['zero']} | "
            f"{float(run['summary']['zero_hook_max_activation_delta_rms']):.10f} | "
            f"{float(run['summary']['zero_hook_max_logit_delta_rms']):.10f} |"
        )
    lines.extend(
        [
            "",
            "## Validity",
            "",
            "- Analysis input status: `valid_complete`",
            "- Required endpoint cells missing or invalid: `0`",
            "- Required random-screening cells missing or invalid: `0`",
            "- All ten exact run inventories, ledger task grids, model identities, "
            "runtime dtypes, launcher bindings, and zero-hook tolerances were "
            "validated before publication.",
            "",
            "## Claim boundary",
            "",
            "This result does not establish semantic categories, a "
            "tokenizer-independent glyph property, causal localization, mechanism, "
            "behavioral meaning, or generality beyond the pinned model, backend, "
            "panels, layers, strength, seeds, and prestage targets. Random-direction "
            "and zero-hook controls are integrity descriptions, not endpoint "
            "observations. No p-values or multiplicity-adjusted claims are produced.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_runs_against_execution(
    runs: Sequence[Mapping[str, Any]],
    execution_binding: Mapping[str, Any],
    root: Path,
) -> None:
    process_rows = execution_binding.get("processes")
    if not isinstance(process_rows, list) or len(process_rows) != len(runs):
        raise TransportAnalysisError("Execution/run binding grid differs")
    process_by_role = {
        (row.get("panel_arm"), row.get("role")): row
        for row in process_rows
        if isinstance(row, Mapping)
    }
    if len(process_by_role) != len(runs):
        raise TransportAnalysisError("Execution/run role bindings are incomplete")
    for run in runs:
        key = (run["panel_arm"], run["role"])
        process = process_by_role.get(key)
        if not isinstance(process, Mapping):
            raise TransportAnalysisError(
                f"Missing execution binding for {key[0]}/{key[1]}"
            )
        try:
            process_started = datetime.fromisoformat(process["started_at"])
            process_finished = datetime.fromisoformat(process["finished_at"])
            run_started = datetime.fromisoformat(run["started_at"])
            run_finished = datetime.fromisoformat(run["finished_at"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TransportAnalysisError(
                f"Invalid execution/run timestamps for {key[0]}/{key[1]}"
            ) from exc
        if any(
            value.tzinfo is None
            for value in (process_started, process_finished, run_started, run_finished)
        ):
            raise TransportAnalysisError(
                f"Naive execution/run timestamp for {key[0]}/{key[1]}"
            )
        if not (process_started <= run_started <= run_finished <= process_finished):
            raise TransportAnalysisError(
                f"Run timestamps escape launcher process for {key[0]}/{key[1]}"
            )
        log_path = (root / str(process["log_path"])).resolve()
        log_bytes = log_path.read_bytes()
        run_path_bytes = os.fsencode(str(run["run_dir"]))
        run_id_bytes = run["run_id"].encode("utf-8")
        if run_path_bytes not in log_bytes or run_id_bytes not in log_bytes:
            raise TransportAnalysisError(
                f"Launcher log does not bind supplied run for {key[0]}/{key[1]}"
            )


def analyze_transport(
    full50_sky_run: Path,
    full50_food_run: Path,
    full50_animals_run: Path,
    full50_transport_run: Path,
    full50_social_run: Path,
    core35_sky_run: Path,
    core35_food_run: Path,
    core35_animals_run: Path,
    core35_transport_run: Path,
    core35_social_run: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Validate ten role-bound runs and atomically publish the E2 analysis."""

    root = _repo_root()
    authority = _load_fixed_authority(root)
    execution_binding = _validate_execution_receipt(root, authority)
    run_paths = {
        "full50": {
            "sky": Path(full50_sky_run).resolve(),
            "food": Path(full50_food_run).resolve(),
            "animals": Path(full50_animals_run).resolve(),
            "transport": Path(full50_transport_run).resolve(),
            "social": Path(full50_social_run).resolve(),
        },
        "core35": {
            "sky": Path(core35_sky_run).resolve(),
            "food": Path(core35_food_run).resolve(),
            "animals": Path(core35_animals_run).resolve(),
            "transport": Path(core35_transport_run).resolve(),
            "social": Path(core35_social_run).resolve(),
        },
    }
    flat_paths = [run_paths[arm][role] for arm in ARM_ORDER for role in FAMILY_ORDER]
    if len(set(flat_paths)) != 10:
        raise TransportAnalysisError(
            "The ten arm/family roles require distinct run directories"
        )
    for arm in ARM_ORDER:
        for role in FAMILY_ORDER:
            if not run_paths[arm][role].is_dir():
                raise TransportAnalysisError(
                    f"Run directory is missing for {arm}/{role}: {run_paths[arm][role]}"
                )
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise TransportAnalysisError("Output directory must not already exist")
    if any(
        output_dir == path or output_dir.is_relative_to(path) for path in flat_paths
    ):
        raise TransportAnalysisError("Output directory cannot be inside an input run")

    runs_by_arm: dict[str, list[dict[str, Any]]] = {}
    all_runs: list[dict[str, Any]] = []
    for arm in ARM_ORDER:
        arm_runs = [
            _load_run(run_paths[arm][role], arm, role, authority)
            for role in FAMILY_ORDER
        ]
        runs_by_arm[arm] = arm_runs
        all_runs.extend(arm_runs)
    model_identities = {run["model_identity"]["sha256"] for run in all_runs}
    implementations = {
        run["implementation"].get("source_tree_sha256") for run in all_runs
    }
    environments = {_stable_sha256(run["environment"]) for run in all_runs}
    if len(model_identities) != 1:
        raise TransportAnalysisError(
            "The ten runs do not share one exact model identity"
        )
    if len(implementations) != 1 or None in implementations:
        raise TransportAnalysisError(
            "The ten runs do not share one implementation identity"
        )
    if len(environments) != 1:
        raise TransportAnalysisError("The ten runs do not share one exact environment")
    _validate_runs_against_execution(all_runs, execution_binding, root)

    target_ids = authority["target_ids"]
    group_indices, weights, draws = _joint_bootstrap_design(
        target_ids, authority["target_groups"]
    )
    observed_by_arm: dict[str, dict[str, np.ndarray]] = {}
    bootstrap_by_arm: dict[str, dict[str, np.ndarray]] = {}
    rows_by_arm: dict[str, tuple[Any, ...]] = {}
    for arm in ARM_ORDER:
        tensor = _tensor(runs_by_arm[arm], target_ids)
        observed = _observed_endpoints(tensor, group_indices)
        bootstrap = _bootstrap_endpoints(
            tensor,
            weights,
            draws,
            group_indices,
            chunk_size=BOOTSTRAP_CHUNK_SIZE,
        )
        observed_by_arm[arm] = observed
        bootstrap_by_arm[arm] = bootstrap
        rows_by_arm[arm] = _build_arm_rows(
            arm, runs_by_arm[arm], authority, observed, bootstrap
        )

    panel_targets = [row for arm in ARM_ORDER for row in rows_by_arm[arm][0]]
    transfer_targets = [row for arm in ARM_ORDER for row in rows_by_arm[arm][1]]
    family_cells = [row for arm in ARM_ORDER for row in rows_by_arm[arm][2]]
    transfer_cells = [row for arm in ARM_ORDER for row in rows_by_arm[arm][3]]
    results_by_arm = {arm: rows_by_arm[arm][4] for arm in ARM_ORDER}
    expected_panel_targets = {
        (arm, family, layer, target_id)
        for arm in ARM_ORDER
        for family in FAMILY_ORDER
        for layer in LAYERS
        for target_id in target_ids
    }
    expected_transfer_targets = {
        (arm, source, prototype, layer, target_id)
        for arm in ARM_ORDER
        for source in FAMILY_ORDER
        for prototype in FAMILY_ORDER
        if source != prototype
        for layer in LAYERS
        for target_id in target_ids
    }
    expected_family_cells = {
        (arm, family, layer)
        for arm in ARM_ORDER
        for family in FAMILY_ORDER
        for layer in LAYERS
    }
    expected_transfer_cells = {
        (arm, source, prototype, layer)
        for arm in ARM_ORDER
        for source in FAMILY_ORDER
        for prototype in FAMILY_ORDER
        if source != prototype
        for layer in LAYERS
    }
    _assert_exact_keys(
        panel_targets,
        OUTPUT_UNIQUE_KEYS["panel_target_scores.jsonl"],
        expected_panel_targets,
        "panel target scores",
    )
    _assert_exact_keys(
        transfer_targets,
        OUTPUT_UNIQUE_KEYS["transfer_target_scores.jsonl"],
        expected_transfer_targets,
        "transfer target scores",
    )
    _assert_exact_keys(
        family_cells,
        OUTPUT_UNIQUE_KEYS["family_cell_summary.jsonl"],
        expected_family_cells,
        "family cell summaries",
    )
    _assert_exact_keys(
        transfer_cells,
        OUTPUT_UNIQUE_KEYS["transfer_cell_summary.jsonl"],
        expected_transfer_cells,
        "transfer cell summaries",
    )
    observed_row_counts = {
        "panel_target_scores.jsonl": len(panel_targets),
        "transfer_target_scores.jsonl": len(transfer_targets),
        "family_cell_summary.jsonl": len(family_cells),
        "transfer_cell_summary.jsonl": len(transfer_cells),
    }
    if observed_row_counts != EXPECTED_OUTPUT_ROWS:
        raise TransportAnalysisError("Published E2 row counts differ from the freeze")

    paired_differences = []
    for layer_index, layer in enumerate(LAYERS):
        point = float(
            np.mean(observed_by_arm["core35"]["global_specificity"][layer_index])
            - np.mean(observed_by_arm["full50"]["global_specificity"][layer_index])
        )
        replicates = (
            bootstrap_by_arm["core35"]["global_specificity"][layer_index]
            - bootstrap_by_arm["full50"]["global_specificity"][layer_index]
        )
        paired_differences.append(
            {
                "endpoint_id": ENDPOINT_PAIRED_DIFFERENCE,
                "layer": layer,
                "layer_role": "prespecified_secondary_paired_sensitivity",
                "target_mean_difference": point,
                "target_mean_difference_ci95": _interval(replicates),
                "target_differences": [
                    {
                        "target_id": target_id,
                        "target_group": authority["target_groups"][target_id],
                        "core35_minus_full50_R_global": float(
                            observed_by_arm["core35"]["global_specificity"][
                                layer_index, target_index
                            ]
                            - observed_by_arm["full50"]["global_specificity"][
                                layer_index, target_index
                            ]
                        ),
                    }
                    for target_index, target_id in enumerate(target_ids)
                ],
                "direction": "core35_minus_full50",
                "interpretation": "prespecified_secondary_description",
            }
        )

    primary_layer_result = next(
        row for row in results_by_arm["full50"] if row["layer"] == PRIMARY_LAYER
    )
    primary_global = primary_layer_result["equal_family_global_specificity_R_global"]
    primary_result = {
        "id": PRIMARY_CRITERION_ID,
        "short_label": "H_E2_1",
        "rule": PRIMARY_CRITERION_RULE,
        "panel_arm": "full50",
        "layer": PRIMARY_LAYER,
        "endpoint_id": ENDPOINT_GLOBAL,
        "target_mean": primary_global["target_mean"],
        "target_mean_ci95": primary_global["target_mean_ci95"],
        "criterion_met": _primary_criterion_met(primary_global["target_mean_ci95"]),
        "hypothesis_family_size": 1,
        "multiplicity_adjustment": "none_single_element_family",
        "decision_scope": "bounded_exploratory_transport_cell",
    }
    report = _render_report(
        results_by_arm, paired_differences, primary_result, all_runs
    )

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent)
    )
    try:
        panel_target_path = staging / "panel_target_scores.jsonl"
        transfer_target_path = staging / "transfer_target_scores.jsonl"
        family_cell_path = staging / "family_cell_summary.jsonl"
        transfer_cell_path = staging / "transfer_cell_summary.jsonl"
        report_path = staging / "report.md"
        _write_jsonl(panel_target_path, panel_targets)
        _write_jsonl(transfer_target_path, transfer_targets)
        _write_jsonl(family_cell_path, family_cells)
        _write_jsonl(transfer_cell_path, transfer_cells)
        _atomic_write(report_path, report.encode("utf-8"))
        hashed_outputs = [
            {
                "filename": path.name,
                "sha256": _sha256_file(path),
                **({"row_count": count} if count is not None else {}),
            }
            for path, count in (
                (panel_target_path, len(panel_targets)),
                (transfer_target_path, len(transfer_targets)),
                (family_cell_path, len(family_cells)),
                (transfer_cell_path, len(transfer_cells)),
                (report_path, None),
            )
        ]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "analysis_id": ANALYSIS_ID,
            "status": _primary_status(primary_global["target_mean_ci95"]),
            "scientific_result": True,
            "analysis_implementation": {
                "path": Path(__file__).resolve().relative_to(root).as_posix(),
                "sha256": _sha256_file(Path(__file__).resolve()),
            },
            "e1_math_dependency": {
                "path": E1_DEPENDENCY_PATH.as_posix(),
                "sha256": _sha256_file(Path(e1_math.__file__)),
                "reuse": (
                    "full50 scoring and both-arm bootstrap draws, weighting, and "
                    "interval primitives; core35 uses the identical E1 formula "
                    "generalized only from ten to seven slots"
                ),
            },
            "manifest_binding": {
                "path": MANIFEST_PATH.as_posix(),
                "sha256": authority["manifest_sha256"],
            },
            "execution_binding": execution_binding,
            "claim_boundary": (
                "Bounded cross-model transport on the fixed 24-target prestage bank; "
                "no semantic, tokenizer-independent, causal, mechanistic, behavioral, "
                "confirmatory-holdout, or paper-gate claim is authorized."
            ),
            "fixed_cell": {
                "model": MODEL,
                "revision": REVISION,
                "model_artifact_manifest_sha256": MODEL_ARTIFACT_MANIFEST_SHA256,
                "backend": BACKEND,
                "device": DEVICE,
                "dtype": DTYPE,
                "site": SITE,
                "layers": list(LAYERS),
                "strength": STRENGTH,
                "direction_seeds": list(DIRECTION_SEEDS),
                "fingerprint_dim": FINGERPRINT_DIM,
                "fingerprint_seed": FINGERPRINT_SEED,
            },
            "data_scope": {
                "bank_role": "reused_exploratory_prestage_targets",
                "selected_first_rows": len(target_ids),
                "ordered_target_ids": list(target_ids),
                "ordered_target_groups": [
                    authority["target_groups"][target_id] for target_id in target_ids
                ],
                "p2_confirmatory_holdout_accessed": False,
                "c1_causal_holdout_accessed": False,
                "model_forward_passes_by_analyzer": 0,
                "tokenizer_calls_by_analyzer": 0,
            },
            "panel_arms": {
                arm: {
                    "family_order": list(FAMILY_ORDER),
                    "conditions_per_family": ARM_DEFINITIONS[arm][
                        "conditions_per_family"
                    ],
                    "matched_slots": [
                        f"slot_{index:02d}"
                        for index in ARM_DEFINITIONS[arm]["slot_indices"]
                    ],
                    "centering": "independent_panel_centroid",
                }
                for arm in ARM_ORDER
            },
            "endpoint_definitions": {
                ENDPOINT_WITHIN: (
                    "seed-averaged diagonal matched-slot cosine minus mean "
                    "mismatched-slot cosine"
                ),
                ENDPOINT_TRANSFER: "seed-averaged ordered off-diagonal transfer M",
                ENDPOINT_SPECIFICITY: (
                    "within-family target M minus the median target M over the four "
                    "other prototype families"
                ),
                ENDPOINT_GLOBAL: "equal-family mean R, then equal-target mean",
                ENDPOINT_PAIRED_DIFFERENCE: (
                    "core35 R_global target mean minus full50 R_global target mean"
                ),
            },
            "bootstrap": {
                "replicates": BOOTSTRAP_REPLICATES,
                "seed": BOOTSTRAP_SEED,
                "sampling_unit": "target_prompt_cluster",
                "stratification": "four targets with replacement in each of six groups",
                "joint_across_arms_layers_endpoints_and_pairs": True,
                "direction_seeds_nested_within_target": True,
                "loto_prototypes_rebuilt_inside_each_replicate": True,
                "arms_centered_and_refit_independently": True,
                "interval": "95_percentile_2.5_97.5",
            },
            "input_runs": [_input_record(run, authority) for run in all_runs],
            "identity_validation": {
                "exact_shared_model_identity_sha256": next(iter(model_identities)),
                "exact_shared_run_implementation_sha256": next(iter(implementations)),
                "exact_shared_environment_sha256": next(iter(environments)),
                "all_ten_model_identities_equal": True,
                "all_ten_run_implementations_equal": True,
                "all_ten_environments_equal": True,
                "runtime_parameter_dtype_and_count_verified": True,
            },
            "row_completeness": {
                "published_row_counts": observed_row_counts,
                "exact_unique_key_grids_verified": True,
                "finite_positive_and_random_fingerprints_verified": True,
                "finite_zero_hook_fingerprints_verified": True,
            },
            "primary_criterion": primary_result,
            "secondary_results_by_arm_and_layer": results_by_arm,
            "paired_core35_minus_full50_descriptions": paired_differences,
            "descriptive_control_boundary": {
                "random_control_cells_reported": len(ARM_ORDER)
                * len(FAMILY_ORDER)
                * len(LAYERS)
                * len(DIRECTION_SEEDS),
                "zero_hook_family_layer_cells_reported": len(ARM_ORDER)
                * len(FAMILY_ORDER)
                * len(LAYERS),
                "label_permutations_run": 0,
                "p_values_computed_by_analyzer": False,
                "random_and_zero_hook_controls_are_endpoint_observations": False,
            },
            "output_inventory": list(OUTPUT_FILENAMES),
            "hashed_outputs_excluding_self": hashed_outputs,
        }
        receipt_path = staging / "llama32_3b_mps_emoji_transport_receipt.json"
        _write_json(receipt_path, receipt)
        observed_names = {path.name for path in staging.iterdir()}
        if observed_names != set(OUTPUT_FILENAMES):
            raise TransportAnalysisError("Staged E2 output inventory differs")
        _rename_directory_no_replace(staging, output_dir)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return receipt


# A descriptive alias keeps the public API discoverable while the shorter
# analyze_transport name remains convenient for tests and callers.
analyze_llama32_3b_mps_emoji_transport = analyze_transport


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for arm in ARM_ORDER:
        for role in FAMILY_ORDER:
            parser.add_argument(f"--{arm}-{role}-run", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = analyze_transport(
            args.full50_sky_run,
            args.full50_food_run,
            args.full50_animals_run,
            args.full50_transport_run,
            args.full50_social_run,
            args.core35_sky_run,
            args.core35_food_run,
            args.core35_animals_run,
            args.core35_transport_run,
            args.core35_social_run,
            args.output_dir,
        )
    except TransportAnalysisError as exc:
        print(f"E2 analysis blocked: {exc}", file=sys.stderr)
        return 2
    print(
        f"Published {len(receipt['output_inventory'])} E2 files to "
        f"{Path(args.output_dir).resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
