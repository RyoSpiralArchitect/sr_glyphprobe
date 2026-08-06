#!/usr/bin/env python3
"""Build the compact, deterministic public E1 evidence bundle.

Only the five explicitly named E1 run directories and the fixed E1 analysis
directory are read. The four large raw files in each run are inventoried but
never copied. P2 and C1 target-bank contents are outside this script's input
surface and are never opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

import numpy as np
import yaml


BUNDLE_ID = "emoji_family_exploratory_v1_public_evidence"
FREEZE_COMMIT = "0cd4e11610e42253ead9ce9aff9f0b02474a0558"
FREEZE_MANIFEST_PATH = Path("data/manifests/emoji_family_exploratory_v1.json")
FREEZE_MANIFEST_SHA256 = (
    "9fb96d5808dc298cbd47ca3586e0f00f793ce23e6627ef7705016f02e1c1d583"
)
ANALYZER_PATH = Path("scripts/analyze_emoji_family_exploratory_v1.py")
ANALYZER_SHA256 = "0f40dde0880bf8aaffa0224d0d0363a9127b00f99f8b99fe35395762c9d4bef4"
PREFLIGHT_PATH = Path(
    "artifacts/emoji_family_exploratory_v1/preflight/tokenization_audit_v1.json"
)
PREFLIGHT_SHA256 = "28cd1cd2487d1e11978308bcd77b64a90b2f2d5cfe08103361bbd7dbbcd3418d"
BUNDLE_ROOT = Path("artifacts/emoji_family_exploratory_v1")
MANIFEST_PATH = Path("artifacts/EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json")
ANALYSIS_SOURCE = Path("runs/e1-token-isomorphic-emoji-family-analysis-v1")
BUILDER_PATH = Path("scripts/build_emoji_family_exploratory_v1_bundle.py")
VALIDATOR_PATH = Path("scripts/validate_emoji_family_exploratory_v1_bundle.py")

ROLE_RUNS = {
    "sky": Path(
        "runs/e1-sky-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--39a274120fa8e6a1"
    ),
    "food": Path(
        "runs/e1-food-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--ec228b7a9eb2d540"
    ),
    "animals": Path(
        "runs/e1-animals-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--c1872402b746bcc1"
    ),
    "transport": Path(
        "runs/e1-transport-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--afdbe7e855f85a8d"
    ),
    "social": Path(
        "runs/e1-social-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--1a535759124aaaf5"
    ),
}

RUN_PUBLIC_FILES = (
    "capabilities.json",
    "cross_seed_fingerprint_summary.jsonl",
    "direction_replicates.json",
    "fingerprint_summary.jsonl",
    "plan.json",
    "receipt.json",
    "report.md",
    "resolved_config.yaml",
    "resolved_inputs.json",
    "scalar_balance_summary.jsonl",
    "source_item_metrics.jsonl",
    "source_layer_metrics.jsonl",
    "summary.json",
    "target_baselines.jsonl",
    "tokenization.jsonl",
)
RUN_OMITTED_FILES = (
    "interventions.jsonl",
    "target_baselines.npz",
    "source_activations.npz",
    "directions.npz",
)
ANALYSIS_FILES = (
    "family_target_scores.jsonl",
    "transfer_target_scores.jsonl",
    "family_cell_summary.jsonl",
    "transfer_cell_summary.jsonl",
    "emoji_family_exploratory_receipt.json",
    "report.md",
)
ANALYSIS_EXPECTED_ROWS = {
    "family_target_scores.jsonl": 240,
    "transfer_target_scores.jsonl": 960,
    "family_cell_summary.jsonl": 10,
    "transfer_cell_summary.jsonl": 40,
}
EXCLUDED_CONTENT = (
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
)
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s\"']+"),
    re.compile(r"/home/[^\s\"']+"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"']+"),
)


class BundleBuildError(RuntimeError):
    """Raised when the E1 source evidence violates the public bundle contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleBuildError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs
    )


def _jsonl_row_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            json.loads(line, object_pairs_hook=_reject_duplicate_pairs)
            count += 1
    return count


def _format_for(path: Path) -> str:
    if path.suffix == ".jsonl":
        return "jsonl"
    if path.suffix == ".json":
        return "json"
    if path.suffix in {".yaml", ".yml"}:
        return "yaml"
    if path.suffix == ".md":
        return "markdown"
    if path.suffix == ".npz":
        return "npz"
    raise BundleBuildError(f"unsupported evidence format: {path}")


def _public_file_metadata(root: Path, path: Path) -> dict[str, Any]:
    _require(path.is_file(), f"missing public evidence member: {path}")
    file_format = _format_for(path)
    if file_format == "json":
        _load_json(path)
    elif file_format == "jsonl":
        row_count: int | None = _jsonl_row_count(path)
    elif file_format == "yaml":
        yaml.safe_load(path.read_text(encoding="utf-8"))
    if file_format != "jsonl":
        row_count = None
    return {
        "path": path.relative_to(root).as_posix(),
        "format": file_format,
        "bytes": path.stat().st_size,
        "row_count": row_count,
        "sha256": _sha256(path),
    }


def _array_inventory(path: Path) -> tuple[list[dict[str, Any]], int]:
    arrays: list[dict[str, Any]] = []
    vector_rows = 0
    with np.load(path, allow_pickle=False) as archive:
        for name in sorted(archive.files):
            value = archive[name]
            elements = int(value.size)
            arrays.append(
                {
                    "name": name,
                    "shape": [int(item) for item in value.shape],
                    "dtype": str(value.dtype),
                    "elements": elements,
                    "uncompressed_bytes": int(value.nbytes),
                }
            )
            if value.ndim >= 2:
                vector_rows += int(np.prod(value.shape[:-1], dtype=np.int64))
    return arrays, vector_rows


def _omitted_file_metadata(root: Path, source: Path) -> dict[str, Any]:
    _require(source.is_file(), f"missing omitted source evidence: {source}")
    name = source.name
    metadata: dict[str, Any] = {
        "source_path": source.relative_to(root).as_posix(),
        "public_copy_path": None,
        "omitted_reason": "large_raw_replay_payload",
        "format": _format_for(source),
        "bytes": source.stat().st_size,
        "sha256": _sha256(source),
    }
    if name == "interventions.jsonl":
        metadata.update(
            {
                "row_count": _jsonl_row_count(source),
                "row_count_basis": "nonblank JSONL records",
            }
        )
        return metadata

    arrays, stored_vector_rows = _array_inventory(source)
    by_name = {item["name"]: item for item in arrays}
    if name == "target_baselines.npz":
        _require(
            by_name["activations"]["shape"][0] == by_name["logits"]["shape"][0],
            f"unaligned target baseline arrays: {source}",
        )
        row_count = int(by_name["logits"]["shape"][0])
        basis = "target prompt records shared by activations and logits"
    elif name == "source_activations.npz":
        emoji_shape = by_name["emoji"]["shape"]
        neutral_shape = by_name["neutral"]["shape"]
        row_count = int(emoji_shape[0] * emoji_shape[1] + neutral_shape[0])
        basis = "source forwards: emoji conditions times wrappers plus neutral wrappers"
    elif name == "directions.npz":
        direction_arrays = [
            item
            for item in arrays
            if item["name"].startswith(("directions_seed_", "generic_seed_"))
        ]
        row_count = sum(
            int(np.prod(item["shape"][:-1], dtype=np.int64))
            for item in direction_arrays
        )
        basis = "intervention direction vectors across seeds, conditions, and layers"
    else:  # pragma: no cover - guarded by the fixed omission tuple
        raise BundleBuildError(f"unexpected omitted archive: {source}")
    metadata.update(
        {
            "row_count": row_count,
            "row_count_basis": basis,
            "stored_vector_row_count": stored_vector_rows,
            "array_count": len(arrays),
            "arrays": arrays,
        }
    )
    return metadata


def _scan_absolute_paths(paths: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for pattern in ABSOLUTE_PATH_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(
                        {
                            "path": path.as_posix(),
                            "line": line_number,
                            "match": match.group(0),
                        }
                    )
    return findings


def _copy_exact(source: Path, destination: Path) -> None:
    _require(source.is_file(), f"missing E1 source evidence: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_sha = _sha256(source)
    if os.path.lexists(destination):
        _require(
            destination.is_file() and not destination.is_symlink(),
            f"existing public member is not a regular file: {destination}",
        )
        _require(
            destination.stat().st_size == source.stat().st_size
            and _sha256(destination) == expected_sha,
            f"refusing to overwrite non-identical public member: {destination}",
        )
        return

    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        shutil.copyfile(source, temporary_path)
        _require(
            temporary_path.stat().st_size == source.stat().st_size
            and _sha256(temporary_path) == expected_sha,
            f"staged copy digest differs: {source}",
        )
        try:
            os.link(temporary_path, destination)
        except FileExistsError:
            _require(
                destination.is_file()
                and not destination.is_symlink()
                and destination.stat().st_size == source.stat().st_size
                and _sha256(destination) == expected_sha,
                f"concurrent non-identical public member: {destination}",
            )
    finally:
        temporary_path.unlink(missing_ok=True)


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    expected_bytes = text.encode("utf-8")
    if os.path.lexists(path):
        _require(
            path.is_file() and not path.is_symlink(),
            f"existing manifest is not a regular file: {path}",
        )
        _require(
            path.read_bytes() == expected_bytes,
            f"refusing to overwrite non-identical public manifest: {path}",
        )
        return
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            _require(
                path.is_file()
                and not path.is_symlink()
                and path.read_bytes() == expected_bytes,
                f"concurrent non-identical public manifest: {path}",
            )
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build_bundle(root: Path) -> dict[str, Any]:
    root = root.resolve()
    freeze_manifest_path = root / FREEZE_MANIFEST_PATH
    _require(
        _sha256(freeze_manifest_path) == FREEZE_MANIFEST_SHA256,
        "frozen E1 manifest digest differs",
    )
    freeze_manifest = _load_json(freeze_manifest_path)
    _require(
        _sha256(root / ANALYZER_PATH) == ANALYZER_SHA256, "analyzer digest differs"
    )
    _require(
        _sha256(root / PREFLIGHT_PATH) == PREFLIGHT_SHA256, "preflight digest differs"
    )
    _require((root / BUILDER_PATH).is_file(), "bundle builder is missing")
    _require((root / VALIDATOR_PATH).is_file(), "bundle validator is missing")

    panel_by_role = {item["role"]: item for item in freeze_manifest["panels"]}
    role_binding_by_role = {
        item["role"]: item for item in freeze_manifest["role_bindings"]
    }
    expected_roles = list(ROLE_RUNS)
    _require(
        list(panel_by_role) == expected_roles,
        "frozen panel role order differs from the public bundle",
    )
    _require(
        set(role_binding_by_role) == set(expected_roles),
        "frozen role binding set differs",
    )

    public_paths: list[Path] = []
    run_evidence: list[dict[str, Any]] = []
    for role, source_relative in ROLE_RUNS.items():
        source_dir = root / source_relative
        destination_dir = root / BUNDLE_ROOT / "runs" / role
        _require(source_dir.is_dir(), f"missing E1 run directory: {source_relative}")
        if destination_dir.exists():
            unexpected = {
                path.name
                for path in destination_dir.iterdir()
                if path.name not in RUN_PUBLIC_FILES
            }
            _require(
                not unexpected,
                f"unexpected files in {destination_dir}: {sorted(unexpected)}",
            )
        included: list[dict[str, Any]] = []
        for filename in RUN_PUBLIC_FILES:
            source = source_dir / filename
            destination = destination_dir / filename
            _copy_exact(source, destination)
            public_paths.append(destination)
            included.append(_public_file_metadata(root, destination))

        omitted = [
            _omitted_file_metadata(root, source_dir / filename)
            for filename in RUN_OMITTED_FILES
        ]
        _require(
            all(
                not (destination_dir / filename).exists()
                for filename in RUN_OMITTED_FILES
            ),
            f"large raw file leaked into public bundle: {role}",
        )

        plan = _load_json(destination_dir / "plan.json")
        summary = _load_json(destination_dir / "summary.json")
        receipt = _load_json(destination_dir / "receipt.json")
        resolved_inputs = _load_json(destination_dir / "resolved_inputs.json")
        panel_spec = panel_by_role[role]
        binding = role_binding_by_role[role]
        _require(plan["estimated_forward_calls"] == 1976, f"{role}: plan differs")
        _require(summary["intervention_record_count"] == 1776, f"{role}: rows differ")
        _require(
            next(
                item
                for item in omitted
                if item["source_path"].endswith("interventions.jsonl")
            )["row_count"]
            == 1776,
            f"{role}: omitted intervention row count differs",
        )
        _require(
            [item["id"] for item in resolved_inputs["panel"]]
            == [
                f"{panel_spec['factor_family']}_slot_{index:02d}" for index in range(10)
            ],
            f"{role}: resolved panel IDs differ",
        )
        expected_input_hashes = {
            binding["config_sha256"],
            binding["panel_sha256"],
            binding["source_sha256"],
            binding["target_sha256"],
            binding["parity_sha256"],
        }
        _require(
            set(receipt["input_hashes"].values()) == expected_input_hashes,
            f"{role}: receipt input hashes differ from frozen binding",
        )
        run_evidence.append(
            {
                "role": role,
                "source_run_path": source_relative.as_posix(),
                "run_name": panel_spec["run_name"],
                "role_binding": binding,
                "public_directory": (BUNDLE_ROOT / "runs" / role).as_posix(),
                "included_files": included,
                "omitted_raw_files": omitted,
                "included_file_count": len(included),
                "omitted_raw_file_count": len(omitted),
                "planned_forward_calls": int(plan["estimated_forward_calls"]),
                "intervention_row_count": int(summary["intervention_record_count"]),
            }
        )

    analysis_destination = root / BUNDLE_ROOT / "analysis"
    if analysis_destination.exists():
        unexpected = {
            path.name
            for path in analysis_destination.iterdir()
            if path.name not in ANALYSIS_FILES
        }
        _require(
            not unexpected,
            f"unexpected files in {analysis_destination}: {sorted(unexpected)}",
        )
    analysis_files: list[dict[str, Any]] = []
    for filename in ANALYSIS_FILES:
        source = root / ANALYSIS_SOURCE / filename
        destination = analysis_destination / filename
        _copy_exact(source, destination)
        public_paths.append(destination)
        metadata = _public_file_metadata(root, destination)
        if filename in ANALYSIS_EXPECTED_ROWS:
            _require(
                metadata["row_count"] == ANALYSIS_EXPECTED_ROWS[filename],
                f"analysis row count differs: {filename}",
            )
        analysis_files.append(metadata)

    family_cells = []
    family_cell_path = analysis_destination / "family_cell_summary.jsonl"
    with family_cell_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                family_cells.append(
                    json.loads(line, object_pairs_hook=_reject_duplicate_pairs)
                )
    random_control_values = [
        {
            "family": cell["family"],
            "layer": int(cell["layer"]),
            "seed": int(control["seed"]),
            "emoji_advantage_over_random": float(
                control["emoji_advantage_over_random"]
            ),
        }
        for cell in family_cells
        for control in cell["descriptive_fingerprint_controls_by_direction_seed"]
    ]
    random_nonpositive_count = sum(
        item["emoji_advantage_over_random"] <= 0.0 for item in random_control_values
    )
    _require(len(random_control_values) == 30, "random control cell count differs")
    _require(
        random_nonpositive_count == 10,
        "random-control nonpositive count differs from independent outcome review",
    )
    analysis_receipt = _load_json(
        analysis_destination / "emoji_family_exploratory_receipt.json"
    )
    analysis_hashes = {
        Path(item["path"]).name: item["sha256"] for item in analysis_files
    }

    preflight_path = root / PREFLIGHT_PATH
    public_paths.append(preflight_path)
    preflight_metadata = _public_file_metadata(root, preflight_path)
    findings = _scan_absolute_paths(public_paths)
    _require(not findings, f"absolute filesystem paths found: {findings[:3]}")

    all_public_metadata = [preflight_metadata, *analysis_files]
    for run in run_evidence:
        all_public_metadata.extend(run["included_files"])
    omitted_metadata = [
        item for run in run_evidence for item in run["omitted_raw_files"]
    ]
    jsonl_public = [item for item in all_public_metadata if item["format"] == "jsonl"]
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "bundle_id": BUNDLE_ID,
        "status": "complete_validated_public_evidence",
        "freeze": {
            "public_freeze_commit": FREEZE_COMMIT,
            "manifest_path": FREEZE_MANIFEST_PATH.as_posix(),
            "manifest_sha256": FREEZE_MANIFEST_SHA256,
            "prepared_before_e1_model_forward": True,
            "e1_model_forward_executed_after_freeze": True,
            "claim_boundary": freeze_manifest["claim_boundary"],
        },
        "claim_boundary": analysis_receipt["claim_boundary"],
        "analysis": {
            "source_run_path": ANALYSIS_SOURCE.as_posix(),
            "public_directory": (BUNDLE_ROOT / "analysis").as_posix(),
            "implementation_path": ANALYZER_PATH.as_posix(),
            "implementation_sha256": ANALYZER_SHA256,
            "files": analysis_files,
            "output_sha256": analysis_hashes,
            "file_count": len(analysis_files),
            "expected_jsonl_rows": ANALYSIS_EXPECTED_ROWS,
            "independent_outcome_review": {
                "status": "pass",
                "same_input_reanalysis_byte_identical": True,
                "byte_identical_file_count": 6,
            },
            "descriptive_random_control_summary": {
                "metric": "emoji_advantage_over_random",
                "comparison": "less_than_or_equal_to_zero",
                "nonpositive_cell_count": random_nonpositive_count,
                "reported_cell_count": len(random_control_values),
                "fraction_nonpositive": random_nonpositive_count
                / len(random_control_values),
                "endpoint_observations": False,
                "use": "descriptive_integrity_screen_only",
            },
        },
        "preflight": preflight_metadata,
        "runs": run_evidence,
        "absolute_path_scrub": {
            "policy": "fail closed on user-home or drive-qualified filesystem paths; evidence bytes are otherwise unchanged",
            "files_scanned": len(public_paths),
            "match_count": 0,
            "transformed_file_count": 0,
        },
        "excluded_content_access": {
            "paths": list(EXCLUDED_CONTENT),
            "content_opened_or_read": False,
            "content_hashed": False,
            "content_tokenized": False,
            "model_forward_count": 0,
            "verification_scope": "declaration only; excluded bank files are outside the fixed E1 build input surface",
        },
        "inventory": {
            "public_member_scope": (
                "payload files under artifacts/emoji_family_exploratory_v1; "
                "the root manifest is excluded from member byte totals"
            ),
            "role_count": len(run_evidence),
            "analysis_file_count": len(analysis_files),
            "per_role_included_file_count": len(RUN_PUBLIC_FILES),
            "public_member_file_count": len(all_public_metadata),
            "public_file_count_including_root_manifest": len(all_public_metadata) + 1,
            "public_member_total_bytes": sum(
                item["bytes"] for item in all_public_metadata
            ),
            "public_jsonl_file_count": len(jsonl_public),
            "public_jsonl_row_count": sum(item["row_count"] for item in jsonl_public),
            "omitted_raw_file_count": len(omitted_metadata),
            "omitted_raw_total_bytes": sum(item["bytes"] for item in omitted_metadata),
            "omitted_intervention_jsonl_rows": sum(
                item["row_count"]
                for item in omitted_metadata
                if item["format"] == "jsonl"
            ),
        },
        "tooling": {
            "builder_path": BUILDER_PATH.as_posix(),
            "builder_sha256": _sha256(root / BUILDER_PATH),
            "validator_path": VALIDATOR_PATH.as_posix(),
            "validator_sha256": _sha256(root / VALIDATOR_PATH),
        },
    }
    serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    _require(
        not any(pattern.search(serialized) for pattern in ABSOLUTE_PATH_PATTERNS),
        "manifest would contain an absolute filesystem path",
    )
    _atomic_write_json(root / MANIFEST_PATH, manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    manifest = build_bundle(args.root)
    print(json.dumps(manifest["inventory"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
