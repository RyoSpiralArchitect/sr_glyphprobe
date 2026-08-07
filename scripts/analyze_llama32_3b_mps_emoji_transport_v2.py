#!/usr/bin/env python3
"""Analyze the frozen Llama-3.2-3B MPS emoji-transport v2 experiment.

V2 changes only the preflight implementation and versioned evidence namespace.
The endpoint, bootstrap, scoring, control, row, and primary-decision definitions
are the frozen v1 definitions. This adapter imports the unchanged v1 analyzer,
binds it to v2 authority, and records the exact v1 implementation dependency in
the v2 receipt. It never loads a model or tokenizer.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence


V1_ANALYZER_SHA256 = "c6ea226da99f974298859b63fa34f2769548f452ee79fb5d63755d99eb510b90"
E1_ANALYZER_SHA256 = "0f40dde0880bf8aaffa0224d0d0363a9127b00f99f8b99fe35395762c9d4bef4"


def _import_v1_analyzer() -> ModuleType:
    path = (
        Path(__file__)
        .resolve()
        .with_name("analyze_llama32_3b_mps_emoji_transport_v1.py")
    )
    e1_path = path.with_name("analyze_emoji_family_exploratory_v1.py")
    if _sha256_file(path) != V1_ANALYZER_SHA256:
        raise RuntimeError("Frozen v1 analyzer dependency hash differs")
    if _sha256_file(e1_path) != E1_ANALYZER_SHA256:
        raise RuntimeError("Frozen E1 analyzer dependency hash differs")
    spec = importlib.util.spec_from_file_location(
        "glyphprobe_frozen_llama32_3b_mps_emoji_transport_v1", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import frozen v1 analyzer: {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


v1 = _import_v1_analyzer()

ANALYSIS_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2"
V1_ANALYSIS_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1"
MANIFEST_ID = "llama32_3b_mps_emoji_transport_v2"
MANIFEST_PATH = Path("data/manifests/llama32_3b_mps_emoji_transport_v2.json")
PREFLIGHT_PATH = Path(
    "artifacts/llama32_3b_mps_emoji_transport_v2/preflight/tokenization_audit_v2.json"
)
EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/execution_receipt.json"
)
ATTEMPT_STARTED_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/attempt_started_receipt.json"
)
FAILED_EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/failed_execution_receipt.json"
)
LAUNCHER_LOG_PATH = Path("runs/.e2-llama32-3b-mps-transport-v2-launcher-logs")
RESUME_POLICY = "forbidden_in_v2_new_versioned_freeze_required"
V1_RESUME_POLICY = "forbidden_in_v1_new_versioned_freeze_required"
V1_ANALYZER_PATH = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v1.py")
V1_ANALYZER_ABSOLUTE_PATH = Path(v1.__file__).resolve()
E1_ANALYZER_PATH = Path("scripts/analyze_emoji_family_exploratory_v1.py")
E1_ANALYZER_ABSOLUTE_PATH = Path(v1.e1_math.__file__).resolve()
V1_OUTPUT_RECEIPT_FILENAME = "llama32_3b_mps_emoji_transport_receipt.json"
OUTPUT_RECEIPT_FILENAME = "llama32_3b_mps_emoji_transport_v2_receipt.json"
PREFLIGHT_AUDIT_ROLE = (
    "model_free_static_artifact_config_and_contextual_tokenizer_preflight"
)
V1_PREFLIGHT_OUTCOME = "failed_before_any_model_forward"
V2_CORRECTION_SCOPE = "contextual_wrapper_token_profile_only"

FAMILY_ORDER = v1.FAMILY_ORDER
ARM_ORDER = v1.ARM_ORDER
ARM_DEFINITIONS = copy.deepcopy(v1.ARM_DEFINITIONS)
for _arm, _definition in ARM_DEFINITIONS.items():
    _definition["config_paths"] = {
        role: Path(f"configs/e2_llama32_3b_mps_{_arm}_{role}_v2.yaml")
        for role in FAMILY_ORDER
    }
    _definition["run_names"] = {
        role: f"e2-llama32-3b-mps-{_arm}-{role}-transport-v2" for role in FAMILY_ORDER
    }

OUTPUT_FILENAMES = tuple(
    OUTPUT_RECEIPT_FILENAME if name == V1_OUTPUT_RECEIPT_FILENAME else name
    for name in v1.OUTPUT_FILENAMES
)

TransportAnalysisError = v1.TransportAnalysisError

_ORIGINAL_V1_LOAD_FIXED_AUTHORITY = v1._load_fixed_authority
_ORIGINAL_V1_VALIDATE_EXECUTION_RECEIPT = v1._validate_execution_receipt
_ORIGINAL_V1_READ_JSON_OBJECT = v1._read_json_object
_ORIGINAL_V1_WRITE_JSON = v1._write_json


def _v1_dependency_record() -> dict[str, str]:
    return {
        "path": V1_ANALYZER_PATH.as_posix(),
        "sha256": V1_ANALYZER_SHA256,
    }


def _load_fixed_authority_v2(root: Path) -> dict[str, Any]:
    """Load v2 authority and require its exact unchanged-v1 dependency."""

    root = Path(root).resolve()
    authority = _ORIGINAL_V1_LOAD_FIXED_AUTHORITY(root)
    manifest = _ORIGINAL_V1_READ_JSON_OBJECT(
        root / MANIFEST_PATH, "frozen E2 v2 manifest"
    )
    if manifest.get("manifest_id") != MANIFEST_ID:
        raise TransportAnalysisError("E2 v2 manifest ID differs")
    analysis = manifest.get("analysis")
    dependency = (
        analysis.get("v1_analysis_dependency")
        if isinstance(analysis, Mapping)
        else None
    )
    if dependency != _v1_dependency_record():
        raise TransportAnalysisError("E2 v2 manifest v1 analysis dependency differs")
    authority["v1_analysis_dependency"] = _v1_dependency_record()
    return authority


def _validate_execution_receipt_v2(
    root: Path, authority: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate raw v2 policy, then reuse every unchanged v1 chain check."""

    root = Path(root).resolve()
    execution_path = root / EXECUTION_RECEIPT_PATH
    attempt_path = root / ATTEMPT_STARTED_RECEIPT_PATH
    preflight_path = root / PREFLIGHT_PATH
    if os.path.lexists(root / FAILED_EXECUTION_RECEIPT_PATH):
        raise TransportAnalysisError(
            "Failed-execution receipt exists; v2 analysis publication is forbidden"
        )
    receipt = _ORIGINAL_V1_READ_JSON_OBJECT(execution_path, "E2 v2 execution receipt")
    attempt = _ORIGINAL_V1_READ_JSON_OBJECT(
        attempt_path, "E2 v2 attempt-started receipt"
    )
    preflight = _ORIGINAL_V1_READ_JSON_OBJECT(
        preflight_path, "E2 v2 tokenizer preflight"
    )
    if (
        receipt.get("protocol_id") != ANALYSIS_ID
        or attempt.get("protocol_id") != ANALYSIS_ID
        or preflight.get("protocol_id") != ANALYSIS_ID
    ):
        raise TransportAnalysisError("E2 v2 receipt protocol binding differs")
    if (
        preflight.get("audit_role") != PREFLIGHT_AUDIT_ROLE
        or preflight.get("v1_preflight_outcome") != V1_PREFLIGHT_OUTCOME
        or preflight.get("v2_correction_scope") != V2_CORRECTION_SCOPE
    ):
        raise TransportAnalysisError("E2 v2 preflight implementation binding differs")
    tokenization = preflight.get("tokenization")
    rules = tokenization.get("rules") if isinstance(tokenization, Mapping) else None
    expected_rules = {
        "v1_raw_contract_preserved": True,
        "wrapper_context_profiles_exactly_frozen": True,
        "full50_exceptions_use_contextual_first_token_substitution": True,
        "wrapper_outside_tokens_identical": True,
        "wrapper_core_token_count_position_and_outside_isomorphic": True,
        "contextual_first_token_distribution": {"9468": 7, "11410": 9},
    }
    if not isinstance(rules, Mapping) or any(
        rules.get(field) != wanted for field, wanted in expected_rules.items()
    ):
        raise TransportAnalysisError("E2 v2 contextual tokenizer rules differ")
    authorization = preflight.get("authorization")
    if (
        not isinstance(authorization, Mapping)
        or authorization.get("frozen_grid_execution_authorized") is not True
    ):
        raise TransportAnalysisError("E2 v2 execution authorization differs")
    if receipt.get("resume_policy") != RESUME_POLICY:
        raise TransportAnalysisError("E2 v2 execution resume policy differs")
    if attempt.get("resume_policy") != RESUME_POLICY:
        raise TransportAnalysisError("E2 v2 attempt resume policy differs")
    if receipt.get("preflight_path") != PREFLIGHT_PATH.as_posix():
        raise TransportAnalysisError("E2 v2 execution preflight path differs")
    attempt_binding = receipt.get("attempt_started_receipt")
    if (
        not isinstance(attempt_binding, Mapping)
        or attempt_binding.get("path") != ATTEMPT_STARTED_RECEIPT_PATH.as_posix()
    ):
        raise TransportAnalysisError("E2 v2 attempt-start binding differs")
    for field, expected_path in (
        ("preflight", PREFLIGHT_PATH),
        ("manifest", MANIFEST_PATH),
    ):
        binding = attempt.get(field)
        if (
            not isinstance(binding, Mapping)
            or binding.get("path") != expected_path.as_posix()
        ):
            raise TransportAnalysisError(f"E2 v2 attempt {field} path binding differs")

    original_reader = v1._read_json_object

    def normalized_reader(path: Path, description: str) -> dict[str, Any]:
        value = _ORIGINAL_V1_READ_JSON_OBJECT(path, description)
        resolved = Path(path).resolve()
        if resolved in {execution_path.resolve(), attempt_path.resolve()}:
            value = dict(value)
            value["resume_policy"] = V1_RESUME_POLICY
        return value

    v1._read_json_object = normalized_reader
    try:
        binding = _ORIGINAL_V1_VALIDATE_EXECUTION_RECEIPT(root, authority)
    finally:
        v1._read_json_object = original_reader
    binding["resume_policy"] = RESUME_POLICY
    binding["versioned_protocol_id"] = ANALYSIS_ID
    return binding


def _write_json_v2(path: Path, value: Any) -> None:
    """Redirect the hard-coded v1 receipt name and add reuse provenance."""

    destination = Path(path)
    if (
        destination.name == V1_OUTPUT_RECEIPT_FILENAME
        and isinstance(value, dict)
        and value.get("analysis_id") == ANALYSIS_ID
    ):
        destination = destination.with_name(OUTPUT_RECEIPT_FILENAME)
        value["v1_analysis_dependency"] = _v1_dependency_record()
        value["version_transition"] = {
            "predecessor_protocol_id": V1_ANALYSIS_ID,
            "scope": "preflight_implementation_and_version_namespace_only",
            "endpoint_math_changed": False,
            "bootstrap_changed": False,
            "primary_criterion_changed": False,
            "row_contracts_changed": False,
        }
    _ORIGINAL_V1_WRITE_JSON(destination, value)


def _install_v2_adapter() -> None:
    """Bind the private v1 module instance to v2 without editing v1 on disk."""

    v1.__file__ = str(Path(__file__).resolve())
    v1.ANALYSIS_ID = ANALYSIS_ID
    v1.MANIFEST_PATH = MANIFEST_PATH
    v1.PREFLIGHT_PATH = PREFLIGHT_PATH
    v1.EXECUTION_RECEIPT_PATH = EXECUTION_RECEIPT_PATH
    v1.ATTEMPT_STARTED_RECEIPT_PATH = ATTEMPT_STARTED_RECEIPT_PATH
    v1.FAILED_EXECUTION_RECEIPT_PATH = FAILED_EXECUTION_RECEIPT_PATH
    v1.LAUNCHER_LOG_PATH = LAUNCHER_LOG_PATH
    v1.ARM_DEFINITIONS = ARM_DEFINITIONS
    v1.OUTPUT_FILENAMES = OUTPUT_FILENAMES
    v1._load_fixed_authority = _load_fixed_authority_v2
    v1._validate_execution_receipt = _validate_execution_receipt_v2
    v1._write_json = _write_json_v2


_install_v2_adapter()

# Publicly expose the frozen definition primitives for focused equivalence tests.
BOOTSTRAP_REPLICATES = v1.BOOTSTRAP_REPLICATES
BOOTSTRAP_SEED = v1.BOOTSTRAP_SEED
PRIMARY_CRITERION_ID = v1.PRIMARY_CRITERION_ID
PRIMARY_CRITERION_RULE = v1.PRIMARY_CRITERION_RULE
PRIMARY_LAYER = v1.PRIMARY_LAYER
LAYERS = v1.LAYERS
DIRECTION_SEEDS = v1.DIRECTION_SEEDS
EXPECTED_OUTPUT_ROWS = v1.EXPECTED_OUTPUT_ROWS
OUTPUT_UNIQUE_KEYS = v1.OUTPUT_UNIQUE_KEYS
_bootstrap_weights = v1._bootstrap_weights
_score_layer_chunk_by_seed = v1._score_layer_chunk_by_seed
_observed_endpoints = v1._observed_endpoints
_bootstrap_endpoints = v1._bootstrap_endpoints
_primary_criterion_met = v1._primary_criterion_met
_primary_status = v1._primary_status
_expected_ledger_task_keys = v1._expected_ledger_task_keys
_validate_ledger_task_keys = v1._validate_ledger_task_keys
_rename_directory_no_replace = v1._rename_directory_no_replace


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
    """Validate ten v2 role-bound runs and atomically publish v1-identical math."""

    return v1.analyze_transport(
        full50_sky_run,
        full50_food_run,
        full50_animals_run,
        full50_transport_run,
        full50_social_run,
        core35_sky_run,
        core35_food_run,
        core35_animals_run,
        core35_transport_run,
        core35_social_run,
        output_dir,
    )


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
        print(f"E2 v2 analysis blocked: {exc}", file=sys.stderr)
        return 2
    print(
        f"Published {len(receipt['output_inventory'])} E2 v2 files to "
        f"{Path(args.output_dir).resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
