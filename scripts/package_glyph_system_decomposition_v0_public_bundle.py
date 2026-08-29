#!/usr/bin/env python3
"""Build the compact public evidence bundle for the T11 glyph-system atlas."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping

import validate_glyph_system_decomposition_v0_result as validator


SCHEMA_VERSION = 1
PROTOCOL_ID = validator.PROTOCOL_ID
FREEZE_COMMIT = "1602749815cf8007588024f89497cc5646de9f54"
PROTOCOL_CORE_SHA256 = "5ef2e31e7bd04f079426d84db1f3437ee2d6278ff47f587826943a5101324f94"
INCLUDED_ANALYSIS = (
    "analysis.json",
    "cross_model_geometry.jsonl",
    "cross_model_item_margin_agreement.jsonl",
    "report.md",
)
OMITTED_ANALYSIS = (
    "broad_system_cell_metrics.jsonl",
    "depth_system_cell_metrics.jsonl",
    "depth_trajectories.jsonl",
)
INCLUDED_VALIDATION = (
    "independent_validation.json",
    "report.md",
    "SHA256SUMS",
)


def write_ledger(directory: Path, names: tuple[str, ...]) -> None:
    lines = [f"{validator.sha256(directory / name)}  {name}\n" for name in names]
    (directory / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def payload_inventory(root: Path) -> list[dict[str, Any]]:
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in {"PUBLIC_MANIFEST.json", "SHA256SUMS"}
    )
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": validator.sha256(path),
        }
        for path in files
    ]


def build_manifest(
    stage: Path,
    analysis: Path,
    validation: Path,
    analysis_entries: Mapping[str, str],
    independent: Mapping[str, Any],
) -> dict[str, Any]:
    omitted = [
        {
            "path": name,
            "bytes": (analysis / name).stat().st_size,
            "sha256": analysis_entries[name],
            "reason": "Omitted from Git public bundle; exact source hash retained.",
        }
        for name in OMITTED_ANALYSIS
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "bundle_role": "compact_exploratory_result_evidence",
        "freeze_commit": FREEZE_COMMIT,
        "protocol_core_sha256": PROTOCOL_CORE_SHA256,
        "analysis_source_sha256sums_sha256": validator.sha256(analysis / "SHA256SUMS"),
        "validation_source_sha256sums_sha256": validator.sha256(validation / "SHA256SUMS"),
        "included_payload": payload_inventory(stage),
        "omitted_analysis_payload": omitted,
        "external_input_bindings": {
            "preflight": independent["input_bindings"]["preflight"],
            "summaries": independent["input_bindings"]["summaries"],
            "run_receipt_sha256": independent["input_bindings"]["run_receipt_sha256_bound_but_external"],
            "raw_activation_archive": {
                "included": False,
                "approximate_dense_array_bytes": "9.15 GiB",
                "reason": "Raw FP32 activations remain in the furnace data archive and are not reconstructible from hashes alone.",
            },
        },
        "independent_validation": {
            "status": independent["status"],
            "overall_assessment": independent["overall_assessment"],
            "stored_item_margin_cell_medians": independent["independent_recomputations"]["stored_item_margin_cell_medians"],
            "cross_model_item_margin_agreement": independent["independent_recomputations"]["cross_model_item_margin_agreement"],
            "balanced_three_way_variance": independent["independent_recomputations"]["balanced_three_way_variance"],
            "depth_trajectories": independent["independent_recomputations"]["depth_trajectories"],
            "cross_model_geometry": independent["independent_recomputations"]["cross_model_geometry"],
        },
        "claim_boundary": independent["claim_boundary"],
        "reserve_items": 268,
        "reserve_model_forward_calls": 0,
        "reserve_outcomes_inspected": False,
        "t10_primary_changed": False,
    }


def build(
    analysis: Path,
    validation: Path,
    readme: Path,
    readme_ja: Path,
    output: Path,
) -> dict[str, Any]:
    validator.require(not output.exists(), f"Output already exists: {output}")
    analysis_entries = validator.verify_sha256sums(analysis)
    validation_entries = validator.verify_sha256sums(validation)
    validator.require(set(INCLUDED_ANALYSIS) | set(OMITTED_ANALYSIS) == set(analysis_entries), "Analysis source payload changed")
    validator.require(set(validation_entries) == {"independent_validation.json", "report.md"}, "Validation source payload changed")
    independent = validator.read_json(validation / "independent_validation.json")
    validator.require(independent["status"] == "pass", "Independent validation did not pass")
    validator.require(independent["protocol_id"] == PROTOCOL_ID, "Independent validation protocol changed")
    validator.require(readme.is_file() and readme_ja.is_file(), "Bilingual bundle README missing")

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        shutil.copyfile(readme, stage / "README.md")
        shutil.copyfile(readme_ja, stage / "README.ja.md")
        analysis_output = stage / "analysis"
        validation_output = stage / "validation"
        analysis_output.mkdir()
        validation_output.mkdir()
        for name in INCLUDED_ANALYSIS:
            shutil.copyfile(analysis / name, analysis_output / name)
        write_ledger(analysis_output, INCLUDED_ANALYSIS)
        for name in INCLUDED_VALIDATION:
            shutil.copyfile(validation / name, validation_output / name)

        manifest = build_manifest(stage, analysis, validation, analysis_entries, independent)
        validator.write_json(stage / "PUBLIC_MANIFEST.json", manifest)
        root_names = tuple(
            path.relative_to(stage).as_posix()
            for path in sorted(path for path in stage.rglob("*") if path.is_file())
        )
        write_ledger(stage, root_names)
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return validate(output)


def validate(output: Path) -> dict[str, Any]:
    entries = validator.verify_sha256sums(output)
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    }
    # Nested ledgers are payload and therefore appear in the root ledger.
    root_expected = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file() and path.relative_to(output).as_posix() != "SHA256SUMS"
    }
    validator.require(set(entries) == root_expected, "Root bundle ledger coverage changed")
    validator.require("PUBLIC_MANIFEST.json" in actual, "Public manifest missing")
    validator.verify_sha256sums(output / "analysis")
    validator.verify_sha256sums(output / "validation")
    manifest = validator.read_json(output / "PUBLIC_MANIFEST.json")
    validator.require(manifest["protocol_id"] == PROTOCOL_ID, "Bundle protocol changed")
    validator.require(manifest["freeze_commit"] == FREEZE_COMMIT, "Bundle freeze commit changed")
    validator.require(
        manifest["protocol_core_sha256"] == PROTOCOL_CORE_SHA256,
        "Bundle protocol core changed",
    )
    validator.require(
        manifest["included_payload"] == payload_inventory(output),
        "Public manifest payload inventory changed",
    )
    omitted = manifest["omitted_analysis_payload"]
    validator.require(
        [entry["path"] for entry in omitted] == list(OMITTED_ANALYSIS),
        "Public manifest omitted-analysis inventory changed",
    )
    validator.require(
        all(not (output / "analysis" / entry["path"]).exists() for entry in omitted),
        "Omitted analysis payload unexpectedly included",
    )
    validator.require(
        manifest["independent_validation"]["status"] == "pass"
        and manifest["independent_validation"]["overall_assessment"] == "share_with_caveats",
        "Independent validation boundary changed",
    )
    validator.require(manifest["reserve_model_forward_calls"] == 0, "Bundle reserve claim changed")
    validator.require(manifest["reserve_outcomes_inspected"] is False, "Bundle reserve inspection claim changed")
    validator.require(manifest["t10_primary_changed"] is False, "Bundle T10 boundary changed")
    return {
        "status": "pass",
        "payload_files": len(entries),
        "public_manifest_sha256": validator.sha256(output / "PUBLIC_MANIFEST.json"),
        "sha256sums_sha256": validator.sha256(output / "SHA256SUMS"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--analysis", type=Path, required=True)
    build_parser.add_argument("--validation", type=Path, required=True)
    build_parser.add_argument("--readme", type=Path, required=True)
    build_parser.add_argument("--readme-ja", type=Path, required=True)
    build_parser.add_argument("--output", type=Path, required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--bundle", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "build":
        result = build(args.analysis, args.validation, args.readme, args.readme_ja, args.output)
    else:
        result = validate(args.bundle)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
