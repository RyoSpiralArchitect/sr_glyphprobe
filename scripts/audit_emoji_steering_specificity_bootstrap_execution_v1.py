#!/usr/bin/env python3
"""Freeze and audit the post-outcome T13-EA bootstrap execution v1.

The design and freeze audits read repository-resident configuration, prose,
code, hashes, and the outcome-free estimand roster.  They verify the byte hash
of the public point summary but never parse its scientific values.  Production
value access belongs only to the separately invoked bundle-preparation path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
from types import ModuleType
from typing import Any, Mapping
import uuid

import yaml


EXECUTION_ID = "glyphprobe-emoji-steering-specificity-bootstrap-execution-v1"
SOURCE_ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
CONFIG_PATH = Path("configs/emoji_steering_specificity_bootstrap_execution_v1.yaml")
ROSTER_PATH = Path("configs/emoji_steering_specificity_bootstrap_estimands_v1.json")
FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_bootstrap_execution_v1.json"
)
EXECUTOR_PATH = Path("scripts/run_emoji_steering_specificity_bootstrap_v1.py")

FROZEN_INPUTS = (
    Path("configs/emoji_steering_specificity_analysis_v0.yaml"),
    Path("artifacts/emoji_steering_specificity_analysis_v0/reporting_summary_v0.json"),
    Path(
        "validation/emoji_steering_specificity_analysis_v0/"
        "point_results_closeout_979533f.json"
    ),
    Path("scripts/analyze_emoji_steering_specificity_outcomes_v0.py"),
    Path("scripts/analyze_emoji_steering_specificity_outcomes_v1.py"),
    Path("scripts/summarize_emoji_steering_specificity_analysis_v0_results.py"),
    CONFIG_PATH,
    ROSTER_PATH,
    Path("docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md"),
    EXECUTOR_PATH,
    Path("scripts/audit_emoji_steering_specificity_bootstrap_execution_v1.py"),
    Path("tests/test_emoji_steering_specificity_bootstrap_execution_v1.py"),
)

EXPECTED_SOURCE_BINDINGS = {
    "analysis_config": (
        "configs/emoji_steering_specificity_analysis_v0.yaml",
        8849,
        "eafa4e435a1a003397ef9ce488a399503e3931f2ae1857d9b3d8614b988e5ce8",
    ),
    "point_reporting_summary": (
        "artifacts/emoji_steering_specificity_analysis_v0/reporting_summary_v0.json",
        1_127_906,
        "097934b191660106167164e2f60f18edafc7fe148db55760466b525aa74c6d06",
    ),
    "point_results_closeout": (
        "validation/emoji_steering_specificity_analysis_v0/"
        "point_results_closeout_979533f.json",
        3_411,
        "95e5eaee979a7930ba43879e47cfb4bf9bb28cd93b4761e7e1e531e69f934e41",
    ),
    "outcomes_v0_analyzer": (
        "scripts/analyze_emoji_steering_specificity_outcomes_v0.py",
        65_546,
        "6331b323693c5c9cca53a0d7e175d52d03ba9452c9c59061db457becc38d2693",
    ),
    "outcomes_v1_wrapper": (
        "scripts/analyze_emoji_steering_specificity_outcomes_v1.py",
        17_675,
        "cc0951be92902b6bc466d69cdb24aa457b04e38bee025eab2a9003ff9a405763",
    ),
}


class BootstrapFreezeError(RuntimeError):
    """Raised when the post-outcome execution freeze differs or is incomplete."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BootstrapFreezeError(message)


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _write_json_new(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"Refusing to overwrite freeze manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = path.parent / f".{path.name}.stage-{uuid.uuid4().hex}"
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as error:
        temporary.unlink()
        raise BootstrapFreezeError(
            f"Refusing to overwrite freeze manifest: {path}"
        ) from error
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.unlink()


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    _require(spec is not None and spec.loader is not None, f"Cannot load: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_design() -> dict[str, Any]:
    """Validate the frozen design without parsing any scientific point value."""

    root = _root()
    config = _read_yaml(root / CONFIG_PATH)
    _require(config.get("execution_id") == EXECUTION_ID, "Execution ID changed")
    _require(
        config.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Source analysis ID changed",
    )
    _require(
        config.get("source_amendment_id") == SOURCE_AMENDMENT_ID,
        "Source amendment ID changed",
    )
    _require(
        config.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Source protocol ID changed",
    )
    _require(
        config.get("status_at_freeze")
        == "post_outcome_computational_amendment_frozen_before_bootstrap_execution",
        "Freeze status changed",
    )
    _require(
        config.get("scientific_outcomes_seen_before_this_freeze") is True,
        "Post-outcome status was hidden",
    )
    _require(
        config.get("bootstrap_replicates_executed_at_freeze") == 0,
        "Freeze records executed bootstrap replicates",
    )

    registered = config.get("registered_bootstrap")
    _require(isinstance(registered, dict), "Registered bootstrap missing")
    _require(
        registered.get("replicates") == 20_000
        and registered.get("seed") == 2_026_082_913
        and registered.get("quantiles") == [0.025, 0.975]
        and registered.get("quantile_method") == "linear_h_equals_n_minus_1_times_q",
        "Registered bootstrap changed",
    )
    schedule = config.get("chunk_schedule")
    _require(isinstance(schedule, dict), "Chunk schedule missing")
    _require(
        schedule.get("chunk_size") == 200
        and schedule.get("chunk_count") == 100
        and schedule.get("first_replicate_id") == 0
        and schedule.get("last_replicate_id") == 19_999
        and schedule.get("sentinel_replicate_ids") == [0, 9_999, 19_999],
        "Chunk coverage changed",
    )

    source_bindings = config.get("source_bindings")
    _require(isinstance(source_bindings, dict), "Source bindings missing")
    _require(
        set(source_bindings) == set(EXPECTED_SOURCE_BINDINGS), "Source roster changed"
    )
    for name, (relative, byte_count, sha256) in EXPECTED_SOURCE_BINDINGS.items():
        binding = source_bindings[name]
        _require(
            binding == {"path": relative, "bytes": byte_count, "sha256": sha256},
            f"Configured source binding changed: {name}",
        )
        source = root / relative
        _require(source.is_file(), f"Bound source missing: {relative}")
        _require(
            source.stat().st_size == byte_count,
            f"Bound source size changed: {relative}",
        )
        _require(_sha256(source) == sha256, f"Bound source hash changed: {relative}")

    original = _read_yaml(root / "configs/emoji_steering_specificity_analysis_v0.yaml")
    reporting = original.get("reporting")
    _require(isinstance(reporting, dict), "Original reporting contract missing")
    _require(
        reporting.get("bootstrap_replicates") == 20_000
        and reporting.get("bootstrap_seed") == 2_026_082_913
        and reporting.get("bootstrap_scope")
        == "registered_high_level_estimands_not_every_raw_surface_cell"
        and reporting.get("paper_interval_gate")
        == "all_registered_bootstrap_chunks_complete_and_hash_merged",
        "Original registered bootstrap changed",
    )

    executor = _load_module(
        root / EXECUTOR_PATH,
        "glyphprobe_t13ea_bootstrap_executor_for_freeze_audit",
    )
    roster = _read_json(root / ROSTER_PATH)
    expected_roster = executor.roster_document()
    _require(roster == expected_roster, "Estimand roster differs")
    _require(roster.get("estimand_count") == 600, "Estimand count changed")
    _require(
        roster.get("family_counts")
        == {
            "F1_item_source_form": 108,
            "F2_prototype_depth_dose": 168,
            "F3_random_null_calibration": 324,
        },
        "Estimand family counts changed",
    )
    estimands = roster.get("estimands")
    _require(isinstance(estimands, list), "Estimand rows missing")
    identifiers = [row.get("estimand_id") for row in estimands]
    _require(len(identifiers) == len(set(identifiers)) == 600, "Estimand IDs differ")
    _require(
        [row.get("index") for row in estimands] == list(range(600)),
        "Estimand indices differ",
    )

    sampler = config.get("sampler")
    _require(isinstance(sampler, dict), "Sampler contract missing")
    _require(
        sampler.get("algorithm") == "sha256_counter_uint64_unbiased_rejection",
        "Sampler algorithm changed",
    )
    target_schedule = sampler.get("target_schedule")
    _require(
        isinstance(target_schedule, dict)
        and target_schedule.get("population_size") == 32
        and target_schedule.get("draws_per_replicate") == 32,
        "Target schedule changed",
    )

    bundle = config.get("bundle_and_outputs")
    _require(isinstance(bundle, dict), "Bundle contract missing")
    _require(
        bundle.get("bundle_point_replay")
        == "all_600_observed_values_must_match_the_bound_public_summary"
        and float(bundle.get("bundle_point_tolerance")) == 1.0e-12
        and bundle.get("raw_arrays_to_git_or_spiralshare") == "forbidden",
        "Bundle boundary changed",
    )
    execution_state = config.get("execution_state_at_freeze")
    _require(
        execution_state
        == {
            "production_bundle_prepared": False,
            "production_chunks_completed": 0,
            "production_replicates_completed": 0,
            "merged_intervals_written": False,
            "paper_interval_gate_satisfied": False,
        },
        "Freeze execution state changed",
    )

    source = (root / EXECUTOR_PATH).read_text(encoding="utf-8")
    _require(
        "p2_confirmatory_targets" not in source, "Executor names protected P2 bank"
    )
    _require(
        "c1_causal_holdout_targets" not in source, "Executor names protected C1 bank"
    )
    _require("significance_test" in source, "Executor claim boundary missing")
    return {
        "status": "bootstrap_execution_design_audit_pass",
        "execution_id": EXECUTION_ID,
        "estimand_count": 600,
        "replicates": 20_000,
        "chunk_count": 100,
        "scientific_values_parsed_by_auditor": False,
        "scientific_outcomes_seen_before_freeze": True,
    }


def freeze(output: Path = FREEZE_PATH) -> dict[str, Any]:
    """Write the no-overwrite freeze manifest after the full design audit."""

    audit_design()
    root = _root()
    roster = [str(path) for path in FROZEN_INPUTS]
    inputs: dict[str, Any] = {}
    for relative in FROZEN_INPUTS:
        source = root / relative
        _require(source.is_file(), f"Frozen input missing: {relative}")
        inputs[str(relative)] = {
            "bytes": source.stat().st_size,
            "sha256": _sha256(source),
        }
    manifest = {
        "schema_version": 1,
        "execution_id": EXECUTION_ID,
        "source_analysis_id": SOURCE_ANALYSIS_ID,
        "source_amendment_id": SOURCE_AMENDMENT_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "freeze_complete_post_outcome_before_bootstrap_execution",
        "claim_boundary": _read_yaml(root / CONFIG_PATH)["claim_boundary"],
        "scientific_outcomes_seen_before_freeze": True,
        "scientific_values_parsed_by_freeze_auditor": False,
        "production_bundle_prepared": False,
        "production_chunks_completed": 0,
        "production_replicates_completed": 0,
        "merged_intervals_written": False,
        "paper_interval_gate_satisfied": False,
        "estimand_count": 600,
        "registered_bootstrap_replicates": 20_000,
        "chunk_count": 100,
        "input_roster": roster,
        "inputs": inputs,
    }
    destination = output if output.is_absolute() else root / output
    _write_json_new(destination, manifest)
    return {
        "status": manifest["status"],
        "execution_id": EXECUTION_ID,
        "input_count": len(roster),
        "manifest": str(destination),
        "manifest_sha256": _sha256(destination),
        "scientific_values_parsed_by_auditor": False,
    }


def audit_freeze(manifest_path: Path = FREEZE_PATH) -> dict[str, Any]:
    """Verify the complete frozen roster, byte counts, and SHA-256 values."""

    audit_design()
    root = _root()
    path = manifest_path if manifest_path.is_absolute() else root / manifest_path
    manifest = _read_json(path)
    _require(manifest.get("schema_version") == 1, "Freeze schema changed")
    _require(
        manifest.get("execution_id") == EXECUTION_ID, "Freeze execution ID changed"
    )
    _require(
        manifest.get("source_analysis_id") == SOURCE_ANALYSIS_ID
        and manifest.get("source_amendment_id") == SOURCE_AMENDMENT_ID
        and manifest.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Freeze lineage changed",
    )
    _require(
        manifest.get("status")
        == "freeze_complete_post_outcome_before_bootstrap_execution",
        "Freeze status changed",
    )
    _require(
        manifest.get("scientific_outcomes_seen_before_freeze") is True
        and manifest.get("scientific_values_parsed_by_freeze_auditor") is False,
        "Freeze outcome boundary changed",
    )
    _require(
        manifest.get("production_bundle_prepared") is False
        and manifest.get("production_chunks_completed") == 0
        and manifest.get("production_replicates_completed") == 0
        and manifest.get("merged_intervals_written") is False
        and manifest.get("paper_interval_gate_satisfied") is False,
        "Freeze execution state changed",
    )
    expected_roster = [str(path) for path in FROZEN_INPUTS]
    _require(
        manifest.get("input_roster") == expected_roster, "Freeze roster order changed"
    )
    inputs = manifest.get("inputs")
    _require(isinstance(inputs, dict), "Freeze bindings missing")
    _require(set(inputs) == set(expected_roster), "Freeze binding roster changed")
    for relative in expected_roster:
        binding = inputs[relative]
        _require(
            isinstance(binding, dict) and set(binding) == {"bytes", "sha256"},
            f"Freeze binding schema changed: {relative}",
        )
        _require(_is_sha256(binding["sha256"]), f"Invalid SHA-256: {relative}")
        source = root / relative
        _require(source.is_file(), f"Frozen source missing: {relative}")
        _require(
            source.stat().st_size == int(binding["bytes"]), f"Size changed: {relative}"
        )
        _require(_sha256(source) == binding["sha256"], f"Hash changed: {relative}")
    return {
        "status": "bootstrap_execution_freeze_audit_pass",
        "execution_id": EXECUTION_ID,
        "input_count": len(expected_roster),
        "estimand_count": 600,
        "registered_bootstrap_replicates": 20_000,
        "scientific_values_parsed_by_auditor": False,
        "scientific_outcomes_seen_before_freeze": True,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-design")
    frozen = subparsers.add_parser("freeze")
    frozen.add_argument("--output", type=Path, default=FREEZE_PATH)
    audit = subparsers.add_parser("audit-freeze")
    audit.add_argument("--manifest", type=Path, default=FREEZE_PATH)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        value = audit_design()
    elif args.command == "freeze":
        value = freeze(args.output)
    else:
        value = audit_freeze(args.manifest)
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
