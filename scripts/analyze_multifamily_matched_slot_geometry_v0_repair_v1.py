#!/usr/bin/env python3
"""Serialization-only repair for matched-slot geometry v0 joint analysis.

The frozen v0 analyzer computed its statistics but could not serialize the raw
YAML primary-endpoint mapping because the key ``null`` became Python ``None``.
This wrapper binds the two already sealed run bundles, reuses the frozen v0
analyzer without changing its mathematics, and converts mapping keys to JSON
strings only at the analysis-receipt write boundary.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import multifamily_matched_slot_geometry_v0 as frozen  # noqa: E402


REPAIR_ID = "glyphprobe-multifamily-matched-slot-geometry-v0-analysis-repair-v1"
REPAIR_MANIFEST_PATH = Path(
    "data/manifests/multifamily_matched_slot_geometry_v0_analysis_repair_v1.json"
)
INPUT_FILES = ("activations.npz", "observations.jsonl", "run_receipt.json", "SHA256SUMS")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_json_mapping_keys(value: Any) -> Any:
    """Recursively normalize mapping keys without changing leaf values."""

    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if key is None:
                text_key = "null"
            elif isinstance(key, str):
                text_key = key
            else:
                raise frozen.base.ProtocolError(
                    f"Unsupported non-string JSON mapping key: {type(key).__name__}"
                )
            frozen.base._require(text_key not in normalized, f"Normalized key collision: {text_key}")
            normalized[text_key] = normalize_json_mapping_keys(item)
        return normalized
    if isinstance(value, list):
        return [normalize_json_mapping_keys(item) for item in value]
    if isinstance(value, tuple):
        return [normalize_json_mapping_keys(item) for item in value]
    return value


def audit_repair(root: Path | None = None) -> dict[str, Any]:
    root = _repo_root() if root is None else root.resolve()
    manifest = frozen.base._read_json(root / REPAIR_MANIFEST_PATH, "repair manifest")
    frozen.base._require(manifest.get("repair_id") == REPAIR_ID, "Repair manifest ID mismatch")
    assets = manifest.get("frozen_assets")
    frozen.base._require(isinstance(assets, dict) and bool(assets), "Repair asset ledger missing")
    verified: dict[str, str] = {}
    for relative, expected in sorted(assets.items()):
        path = root / str(relative)
        frozen.base._require(path.is_file(), f"Missing repair asset: {relative}")
        observed = frozen.base._sha256_file(path)
        frozen.base._require(observed == expected, f"Repair asset SHA-256 mismatch: {relative}")
        verified[str(relative)] = observed
    frozen_audit = frozen.audit_freeze(root)
    frozen.base._require(
        frozen_audit["manifest_sha256"] == manifest["frozen_protocol_manifest_sha256"],
        "Frozen protocol manifest binding mismatch",
    )
    return {
        "status": "pass",
        "repair_id": REPAIR_ID,
        "repair_manifest_sha256": frozen.base._sha256_file(root / REPAIR_MANIFEST_PATH),
        "frozen_protocol_manifest_sha256": frozen_audit["manifest_sha256"],
        "frozen_asset_count": len(verified),
        "frozen_assets": verified,
        "change_scope": manifest["change_scope"],
        "scientific_choices_changed": False,
    }


def _validate_bound_run(
    directory: Path,
    role: str,
    expected_hashes: Mapping[str, str],
) -> None:
    result = frozen.validate_run(directory)
    frozen.base._require(result["status"] == "pass", f"Bound run failed validation: {role}")
    frozen.base._require(result["receipt"]["model_label"] == role, f"Bound run role mismatch: {role}")
    frozen.base._require(set(expected_hashes) == set(INPUT_FILES), f"Input hash roster mismatch: {role}")
    for name in INPUT_FILES:
        observed = frozen.base._sha256_file(directory / name)
        frozen.base._require(observed == expected_hashes[name], f"Bound input SHA-256 mismatch: {role}/{name}")


def run_repaired_analysis(
    gemma_run: Path,
    olmo_run: Path,
    output: Path,
) -> dict[str, Any]:
    root = _repo_root()
    audit = audit_repair(root)
    manifest = frozen.base._read_json(root / REPAIR_MANIFEST_PATH, "repair manifest")
    run_directories = {
        frozen.MODEL_ROLES[0]: gemma_run.resolve(),
        frozen.MODEL_ROLES[1]: olmo_run.resolve(),
    }
    for role in frozen.MODEL_ROLES:
        _validate_bound_run(run_directories[role], role, manifest["input_runs"][role])
    frozen.base._require(not output.exists(), f"Output already exists: {output}")

    original_write_json = frozen.base._write_json

    def repaired_write_json(path: Path, value: Any) -> None:
        normalized = normalize_json_mapping_keys(value)
        if path.name == "analysis_receipt.json":
            frozen.base._require(isinstance(normalized, dict), "Analysis receipt is not a mapping")
            normalized["analysis_serialization_repair"] = {
                "repair_id": REPAIR_ID,
                "repair_manifest_sha256": audit["repair_manifest_sha256"],
                "change_scope": manifest["change_scope"],
                "scientific_choices_changed": False,
            }
        original_write_json(path, normalized)

    frozen.base._write_json = repaired_write_json
    try:
        receipt = frozen.analyze_runs(run_directories, output)
    finally:
        frozen.base._write_json = original_write_json

    validated = frozen.validate_analysis(output)
    frozen.base._require(validated["status"] == "pass", "Repaired analysis failed validation")
    published = frozen.base._read_json(output / "analysis_receipt.json", "repaired analysis receipt")
    binding = published.get("analysis_serialization_repair")
    frozen.base._require(isinstance(binding, dict), "Repair binding missing from analysis receipt")
    frozen.base._require(binding.get("repair_id") == REPAIR_ID, "Published repair ID mismatch")
    return normalize_json_mapping_keys(published)


def validate_repaired_analysis(directory: Path) -> dict[str, Any]:
    audit = audit_repair()
    validated = frozen.validate_analysis(directory)
    receipt = frozen.base._read_json(directory / "analysis_receipt.json", "repaired analysis receipt")
    binding = receipt.get("analysis_serialization_repair")
    frozen.base._require(isinstance(binding, dict), "Repair binding missing")
    frozen.base._require(binding.get("repair_id") == REPAIR_ID, "Repair ID mismatch")
    frozen.base._require(
        binding.get("repair_manifest_sha256") == audit["repair_manifest_sha256"],
        "Repair manifest binding mismatch",
    )
    return {
        **validated,
        "repair_id": REPAIR_ID,
        "repair_manifest_sha256": audit["repair_manifest_sha256"],
        "scientific_choices_changed": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-repair", help="Validate the public repair freeze")
    run = subparsers.add_parser("run", help="Run the serialization-only repaired analysis")
    run.add_argument("--gemma-run", type=Path, required=True)
    run.add_argument("--olmo-run", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    validate = subparsers.add_parser("validate", help="Validate a repaired analysis bundle")
    validate.add_argument("directory", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "audit-repair":
            payload = audit_repair()
        elif args.command == "run":
            payload = run_repaired_analysis(args.gemma_run, args.olmo_run, args.output)
        elif args.command == "validate":
            payload = validate_repaired_analysis(args.directory)
        else:  # pragma: no cover
            raise frozen.base.ProtocolError(f"Unknown command: {args.command}")
        print(frozen.base._json_bytes(payload, pretty=True).decode("utf-8"))
    except (frozen.base.ProtocolError, OSError, ValueError) as exc:
        print(
            frozen.base._json_bytes({"status": "fail", "error": str(exc)}, pretty=True).decode(
                "utf-8"
            )
        )
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
