#!/usr/bin/env python3
"""Canonical batch-one recapture after the batch-64 validation failure."""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import sys
from pathlib import Path
from typing import Any, Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as v0  # noqa: E402
import validate_mistral7b_semantic_atlas_capture_v0 as capture  # noqa: E402


PROTOCOL_ID = "glyphprobe-mistral7b-semantic-atlas-batch1-v1"
CONFIG_PATH = Path("configs/mistral7b_semantic_atlas_batch1_v1.yaml")
VALIDATION_CONFIG_PATH = Path(
    "configs/mistral7b_semantic_atlas_batch1_capture_validation_v1.yaml"
)
FREEZE_PATH = Path("data/manifests/mistral7b_semantic_atlas_batch1_v1.json")
BASE_CONFIG_PATH = v0.CONFIG_PATH
FROZEN_ASSETS = (
    "configs/mistral7b_semantic_atlas_batch1_v1.yaml",
    "configs/mistral7b_semantic_atlas_batch1_capture_validation_v1.yaml",
    "data/manifests/mistral7b_semantic_atlas_selection_v0.json",
    "data/manifests/mistral7b_semantic_atlas_v0.json",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md",
    "docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md",
    "scripts/mistral7b_semantic_atlas_batch1_v1.py",
    "scripts/mistral7b_semantic_atlas_v0.py",
    "scripts/validate_mistral7b_semantic_atlas_capture_v0.py",
    "tests/test_mistral7b_semantic_atlas_batch1_v1.py",
    "validation/mistral7b_semantic_atlas_v0/capture_validation_v0.json",
    "validation/mistral7b_semantic_atlas_v0/engineering_preflight.json",
)


def _spec() -> dict[str, Any]:
    return v0._read_yaml(v0._root() / CONFIG_PATH)


def merged_config() -> dict[str, Any]:
    root = v0._root()
    spec = _spec()
    v0._require(
        v0._sha256(root / BASE_CONFIG_PATH)
        == spec["source_bindings"]["base_config_sha256"],
        "Base config binding mismatch",
    )
    v0._require(
        v0._sha256(root / v0.SELECTION_PATH)
        == spec["source_bindings"]["selection_manifest_sha256"],
        "Selection binding mismatch",
    )
    v0._require(
        v0._sha256(root / Path("data/manifests/mistral7b_semantic_atlas_v0.json"))
        == spec["source_bindings"]["acquisition_freeze_manifest_sha256"],
        "Original freeze binding mismatch",
    )
    v0._require(
        v0._sha256(
            root / "validation/mistral7b_semantic_atlas_v0/capture_validation_v0.json"
        )
        == spec["source_bindings"]["failed_capture_validation_sha256"],
        "Failure receipt binding mismatch",
    )
    config = copy.deepcopy(v0._read_yaml(root / BASE_CONFIG_PATH))
    config["protocol_id"] = PROTOCOL_ID
    config["experiment_role"] = spec["experiment_role"]
    config["claim_boundary"] = spec["claim_boundary"]
    config["storage"]["batch_size_unique_sequences"] = int(
        spec["operational_overrides"]["batch_size_unique_sequences"]
    )
    config["execution_policy"]["canonical_batch_size_one"] = True
    config["execution_policy"]["source_batch64_validation_failed"] = True
    return config


@contextlib.contextmanager
def _delegated_surface() -> Iterator[None]:
    original_protocol = v0.PROTOCOL_ID
    original_config = v0.CONFIG_PATH
    original_freeze = v0.FREEZE_PATH
    original_reader = v0._read_yaml
    original_validation = capture.VALIDATION_CONFIG_PATH
    merged = merged_config()

    def delegated_reader(path: Path) -> dict[str, Any]:
        if path.resolve() == (v0._root() / CONFIG_PATH).resolve():
            return copy.deepcopy(merged)
        return original_reader(path)

    try:
        v0.PROTOCOL_ID = PROTOCOL_ID
        v0.CONFIG_PATH = CONFIG_PATH
        v0.FREEZE_PATH = FREEZE_PATH
        v0._read_yaml = delegated_reader
        capture.VALIDATION_CONFIG_PATH = VALIDATION_CONFIG_PATH
        yield
    finally:
        v0.PROTOCOL_ID = original_protocol
        v0.CONFIG_PATH = original_config
        v0.FREEZE_PATH = original_freeze
        v0._read_yaml = original_reader
        capture.VALIDATION_CONFIG_PATH = original_validation


def build_freeze(output: Path) -> dict[str, Any]:
    root = v0._root()
    config = merged_config()
    spec = _spec()
    preflight = v0._read_json(root / v0.PREFLIGHT_PATH)
    failure = v0._read_json(
        root / "validation/mistral7b_semantic_atlas_v0/capture_validation_v0.json"
    )
    v0._require(failure.get("status") == "validation_failed", "Source validation did not fail")
    v0._require(failure.get("passed_case_count") == 0, "Unexpected passing source case")
    v0._require(failure.get("reserve_forward_calls") == 0, "Source validation touched reserve")
    assets: dict[str, str] = {}
    for relative in FROZEN_ASSETS:
        path = root / relative
        v0._require(path.is_file(), f"Missing batch1 frozen asset: {relative}")
        assets[relative] = v0._sha256(path)
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "freeze_complete_before_any_t8_model_forward",
        "experiment_role": config["experiment_role"],
        "claim_boundary": config["claim_boundary"],
        "frozen_assets": assets,
        "selection_manifest_sha256": v0._sha256(root / v0.SELECTION_PATH),
        "engineering_preflight_sha256": v0._sha256(root / v0.PREFLIGHT_PATH),
        "model_artifact": preflight["model_artifact"],
        "candidate_counts": preflight["candidate_counts"],
        "source_bindings": spec["source_bindings"],
        "batch_size_unique_sequences": 1,
        "expected_model_forward_calls": int(
            spec["operational_overrides"]["expected_model_forward_calls"]
        ),
        "model_forward_calls_for_batch1_v1_at_freeze": 0,
        "prior_batch64_validation_forward_calls": int(failure["model_forward_calls"]),
        "reserved_unrun_model_inputs_forwarded_at_freeze": 0,
        "intervention_calls_at_freeze": 0,
        "generation_calls_at_freeze": 0,
        "scientific_result_available_at_freeze": False,
    }
    v0._write_json(output, payload)
    return {"status": "pass", "manifest_sha256": v0._sha256(output), "frozen_asset_count": len(assets)}


def audit_freeze() -> dict[str, Any]:
    with _delegated_surface():
        return v0.audit_freeze()


def run(model: Path, output: Path, start: int, stop: int | None) -> dict[str, Any]:
    with _delegated_surface():
        return v0.run_shards(model, output, start, stop)


def finalize(run_root: Path) -> dict[str, Any]:
    with _delegated_surface():
        receipt = v0.finalize_run(run_root)
    expected = int(_spec()["operational_overrides"]["expected_model_forward_calls"])
    v0._require(
        int(receipt["batched_model_forward_calls"]) == expected,
        "Batch1 forward count mismatch",
    )
    return receipt


def validate_capture(model: Path, run_root: Path, output: Path) -> dict[str, Any]:
    with _delegated_surface():
        return capture.validate_capture(model, run_root, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("build-freeze")
    freeze.add_argument("--output", type=Path, default=v0._root() / FREEZE_PATH)
    sub.add_parser("audit-freeze")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--model", type=Path, required=True)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--shard-start", type=int, default=0)
    run_parser.add_argument("--shard-stop", type=int)
    final = sub.add_parser("finalize")
    final.add_argument("--run", type=Path, required=True)
    validation = sub.add_parser("validate-capture")
    validation.add_argument("--model", type=Path, required=True)
    validation.add_argument("--run", type=Path, required=True)
    validation.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build-freeze":
        result = build_freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run":
        result = run(args.model, args.output, args.shard_start, args.shard_stop)
    elif args.command == "finalize":
        result = finalize(args.run)
    elif args.command == "validate-capture":
        result = validate_capture(args.model, args.run, args.output)
    else:  # pragma: no cover
        raise v0.AtlasError(f"Unknown command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
