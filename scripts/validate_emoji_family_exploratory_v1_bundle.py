#!/usr/bin/env python3
"""Validate the compact public E1 evidence bundle without reading raw holdouts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable

import yaml


BUNDLE_ID = "emoji_family_exploratory_v1_public_evidence"
MANIFEST_PATH = Path("artifacts/EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json")
BUNDLE_ROOT = Path("artifacts/emoji_family_exploratory_v1")
BUILDER_PATH = Path("scripts/build_emoji_family_exploratory_v1_bundle.py")
VALIDATOR_PATH = Path("scripts/validate_emoji_family_exploratory_v1_bundle.py")
FREEZE_COMMIT = "0cd4e11610e42253ead9ce9aff9f0b02474a0558"
FREEZE_MANIFEST_PATH = Path("data/manifests/emoji_family_exploratory_v1.json")
FREEZE_MANIFEST_SHA256 = (
    "9fb96d5808dc298cbd47ca3586e0f00f793ce23e6627ef7705016f02e1c1d583"
)
ANALYZER_SHA256 = "0f40dde0880bf8aaffa0224d0d0363a9127b00f99f8b99fe35395762c9d4bef4"
PREFLIGHT_SHA256 = "28cd1cd2487d1e11978308bcd77b64a90b2f2d5cfe08103361bbd7dbbcd3418d"
ROLES = ("sky", "food", "animals", "transport", "social")
LAYERS = (2, 4)
RUN_PUBLIC_FILES = {
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
}
RUN_OMITTED_ROWS = {
    "interventions.jsonl": 1776,
    "target_baselines.npz": 24,
    "source_activations.npz": 176,
    "directions.npz": 66,
}
ANALYSIS_SHA256 = {
    "emoji_family_exploratory_receipt.json": (
        "a2357d27432f7e4dd2a6fd4ca663d6afd737f6c8e298b80d03dadc0f2a3f2847"
    ),
    "family_cell_summary.jsonl": (
        "c201193061975a894b39fed0d6abe48de206ce998c9b0e97c124202b3b2797d7"
    ),
    "family_target_scores.jsonl": (
        "8e178248d6133ccefe4421abf4738d83ae24a3383d36f01a6f3cb3070e07b12b"
    ),
    "report.md": ("50124b5caa72f079fa508a0f73c8509c81b0e9b99c61e528a456402ccd0c7cb5"),
    "transfer_cell_summary.jsonl": (
        "c7311130dbdddc75085b6af74e71823f87c3fd907963e508c64041b4fb294607"
    ),
    "transfer_target_scores.jsonl": (
        "dc2260da76eb00134aace810873632cec96ef4af8bc20c57c783c347aa571495"
    ),
}
ANALYSIS_ROWS = {
    "family_target_scores.jsonl": 240,
    "transfer_target_scores.jsonl": 960,
    "family_cell_summary.jsonl": 10,
    "transfer_cell_summary.jsonl": 40,
}
ANALYSIS_UNIQUE_KEYS = {
    "family_target_scores.jsonl": ("family", "layer", "target_id"),
    "transfer_target_scores.jsonl": (
        "source_family",
        "prototype_family",
        "layer",
        "target_id",
    ),
    "family_cell_summary.jsonl": ("family", "layer"),
    "transfer_cell_summary.jsonl": (
        "source_family",
        "prototype_family",
        "layer",
    ),
}
EXCLUDED_CONTENT = (
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
)
ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"/(?:Users|home|private|tmp|Volumes)/[^\s\"']+"),
    re.compile(r"/var/folders/[^\s\"']+"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"']+"),
)


class BundleValidationError(RuntimeError):
    """Raised when public E1 evidence fails closed validation."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BundleValidationError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        _require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line, object_pairs_hook=_reject_duplicate_pairs)
            _require(
                isinstance(value, dict), f"non-object JSONL row: {path}:{line_number}"
            )
            rows.append(value)
    return rows


def _safe_public_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    _require(not candidate.is_absolute(), f"absolute manifest path: {relative}")
    resolved_root = root.resolve()
    resolved_bundle = (resolved_root / BUNDLE_ROOT).resolve()
    resolved = (resolved_root / candidate).resolve()
    _require(
        resolved.is_relative_to(resolved_bundle),
        f"public member escapes E1 bundle root: {relative}",
    )
    _require(
        not (resolved_root / candidate).is_symlink(), f"symlink member: {relative}"
    )
    return resolved


def _scan_absolute_paths(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    findings = 0
    for pattern in ABSOLUTE_PATH_PATTERNS:
        findings += len(pattern.findall(text))
    return findings


def _verify_public_member(
    root: Path, metadata: dict[str, Any]
) -> tuple[Path, list[dict[str, Any]] | None]:
    path = _safe_public_path(root, metadata["path"])
    _require(path.is_file(), f"missing public member: {metadata['path']}")
    _require(path.stat().st_size == metadata["bytes"], f"byte count differs: {path}")
    _require(_sha256(path) == metadata["sha256"], f"digest differs: {path}")
    file_format = metadata["format"]
    rows: list[dict[str, Any]] | None = None
    if file_format == "json":
        _load_json(path)
        _require(metadata["row_count"] is None, f"JSON row count must be null: {path}")
    elif file_format == "jsonl":
        rows = _load_jsonl(path)
        _require(len(rows) == metadata["row_count"], f"JSONL row count differs: {path}")
    elif file_format == "yaml":
        yaml.safe_load(path.read_text(encoding="utf-8"))
        _require(metadata["row_count"] is None, f"YAML row count must be null: {path}")
    elif file_format == "markdown":
        path.read_text(encoding="utf-8")
        _require(
            metadata["row_count"] is None, f"Markdown row count must be null: {path}"
        )
    else:
        raise BundleValidationError(f"unsupported public format: {file_format}")
    _require(_scan_absolute_paths(path) == 0, f"absolute path leak: {path}")
    return path, rows


def _validate_excluded_declaration(manifest: dict[str, Any]) -> dict[str, Any]:
    declaration = manifest.get("excluded_content_access")
    _require(isinstance(declaration, dict), "excluded-content declaration missing")
    _require(
        declaration.get("paths") == list(EXCLUDED_CONTENT),
        "excluded-content path declaration differs",
    )
    for key in ("content_opened_or_read", "content_hashed", "content_tokenized"):
        _require(declaration.get(key) is False, f"excluded-content {key} differs")
    _require(
        declaration.get("model_forward_count") == 0,
        "excluded-content model-forward declaration differs",
    )
    return declaration


def _flatten_public_metadata(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    output = [manifest["preflight"], *manifest["analysis"]["files"]]
    for run in manifest["runs"]:
        output.extend(run["included_files"])
    return output


def _validate_analysis_grids(
    rows_by_name: dict[str, list[dict[str, Any]]], target_ids: list[str]
) -> None:
    for filename, keys in ANALYSIS_UNIQUE_KEYS.items():
        rows = rows_by_name[filename]
        observed = [tuple(row[key] for key in keys) for row in rows]
        _require(
            len(observed) == len(set(observed)), f"duplicate analysis key: {filename}"
        )

    family_target_expected = {
        (role, layer, target_id)
        for role in ROLES
        for layer in LAYERS
        for target_id in target_ids
    }
    family_target_actual = {
        (row["family"], int(row["layer"]), row["target_id"])
        for row in rows_by_name["family_target_scores.jsonl"]
    }
    _require(
        family_target_actual == family_target_expected, "family target grid differs"
    )

    transfer_target_expected = {
        (source, prototype, layer, target_id)
        for source in ROLES
        for prototype in ROLES
        if prototype != source
        for layer in LAYERS
        for target_id in target_ids
    }
    transfer_target_actual = {
        (
            row["source_family"],
            row["prototype_family"],
            int(row["layer"]),
            row["target_id"],
        )
        for row in rows_by_name["transfer_target_scores.jsonl"]
    }
    _require(
        transfer_target_actual == transfer_target_expected,
        "transfer target grid differs",
    )

    family_cell_expected = {(role, layer) for role in ROLES for layer in LAYERS}
    family_cell_actual = {
        (row["family"], int(row["layer"]))
        for row in rows_by_name["family_cell_summary.jsonl"]
    }
    _require(family_cell_actual == family_cell_expected, "family cell grid differs")

    transfer_cell_expected = {
        (source, prototype, layer)
        for source in ROLES
        for prototype in ROLES
        if prototype != source
        for layer in LAYERS
    }
    transfer_cell_actual = {
        (row["source_family"], row["prototype_family"], int(row["layer"]))
        for row in rows_by_name["transfer_cell_summary.jsonl"]
    }
    _require(
        transfer_cell_actual == transfer_cell_expected, "transfer cell grid differs"
    )


def _metadata_by_name(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        name = Path(item["path"]).name
        _require(name not in result, f"duplicate evidence filename: {name}")
        result[name] = item
    return result


def validate_bundle(root: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = root / MANIFEST_PATH
    _require(manifest_path.is_file(), f"missing bundle manifest: {MANIFEST_PATH}")
    manifest_sha = _sha256(manifest_path)
    manifest = _load_json(manifest_path)
    _require(manifest.get("schema_version") == 1, "bundle schema differs")
    _require(manifest.get("bundle_id") == BUNDLE_ID, "bundle ID differs")
    _require(
        manifest.get("status") == "complete_validated_public_evidence",
        "bundle status differs",
    )
    _require(
        manifest.get("tooling")
        == {
            "builder_path": BUILDER_PATH.as_posix(),
            "builder_sha256": _sha256(root / BUILDER_PATH),
            "validator_path": VALIDATOR_PATH.as_posix(),
            "validator_sha256": _sha256(root / VALIDATOR_PATH),
        },
        "bundle tooling binding differs",
    )
    freeze = manifest["freeze"]
    _require(freeze["public_freeze_commit"] == FREEZE_COMMIT, "freeze commit differs")
    _require(
        freeze["manifest_path"] == FREEZE_MANIFEST_PATH.as_posix(),
        "freeze manifest path differs",
    )
    _require(
        freeze["manifest_sha256"] == FREEZE_MANIFEST_SHA256,
        "freeze manifest declaration differs",
    )
    _require(
        freeze["prepared_before_e1_model_forward"] is True
        and freeze["e1_model_forward_executed_after_freeze"] is True,
        "freeze/forward ordering declaration differs",
    )
    freeze_manifest_path = root / FREEZE_MANIFEST_PATH
    _require(
        _sha256(freeze_manifest_path) == FREEZE_MANIFEST_SHA256,
        "frozen E1 manifest file digest differs",
    )
    freeze_manifest = _load_json(freeze_manifest_path)

    _validate_excluded_declaration(manifest)
    public_metadata = _flatten_public_metadata(manifest)
    _require(len(public_metadata) == 82, "public member count differs")
    public_paths = [item["path"] for item in public_metadata]
    _require(
        len(public_paths) == len(set(public_paths)), "duplicate public member path"
    )

    actual_paths: set[str] = set()
    bundle_path = root / BUNDLE_ROOT
    for path in bundle_path.rglob("*"):
        _require(not path.is_symlink(), f"symlink in public bundle: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    _require(actual_paths == set(public_paths), "public bundle tree inventory differs")

    rows_by_path: dict[str, list[dict[str, Any]]] = {}
    for metadata in public_metadata:
        _, rows = _verify_public_member(root, metadata)
        if rows is not None:
            rows_by_path[metadata["path"]] = rows
    _require(
        _scan_absolute_paths(manifest_path) == 0, "absolute path in bundle manifest"
    )

    analysis = manifest["analysis"]
    _require(analysis["implementation_sha256"] == ANALYZER_SHA256, "analyzer differs")
    _require(analysis["file_count"] == 6, "analysis file count differs")
    _require(analysis["expected_jsonl_rows"] == ANALYSIS_ROWS, "analysis rows differ")
    _require(analysis["output_sha256"] == ANALYSIS_SHA256, "analysis hash map differs")
    analysis_by_name = _metadata_by_name(analysis["files"])
    _require(set(analysis_by_name) == set(ANALYSIS_SHA256), "analysis outputs differ")
    for filename, expected_sha in ANALYSIS_SHA256.items():
        _require(
            analysis_by_name[filename]["sha256"] == expected_sha,
            f"analysis output digest declaration differs: {filename}",
        )
    review = analysis["independent_outcome_review"]
    _require(
        review
        == {
            "status": "pass",
            "same_input_reanalysis_byte_identical": True,
            "byte_identical_file_count": 6,
        },
        "independent outcome review declaration differs",
    )
    random_summary = analysis["descriptive_random_control_summary"]
    _require(
        random_summary["nonpositive_cell_count"] == 10
        and random_summary["reported_cell_count"] == 30
        and random_summary["endpoint_observations"] is False,
        "random-control summary differs",
    )

    analysis_rows_by_name = {
        filename: rows_by_path[analysis_by_name[filename]["path"]]
        for filename in ANALYSIS_ROWS
    }
    target_ids = freeze_manifest["shared_inputs"]["target"]["ordered_selected_ids"]
    _require(len(target_ids) == 24, "fixed target count differs")
    _validate_analysis_grids(analysis_rows_by_name, target_ids)
    random_values = [
        control["emoji_advantage_over_random"]
        for row in analysis_rows_by_name["family_cell_summary.jsonl"]
        for control in row["descriptive_fingerprint_controls_by_direction_seed"]
    ]
    _require(len(random_values) == 30, "random-control values are incomplete")
    _require(
        sum(value <= 0.0 for value in random_values) == 10,
        "random-control nonpositive count does not replay",
    )

    analysis_receipt = _load_json(
        root / analysis_by_name["emoji_family_exploratory_receipt.json"]["path"]
    )
    _require(
        analysis_receipt["manifest_binding"]
        == {
            "path": FREEZE_MANIFEST_PATH.as_posix(),
            "sha256": FREEZE_MANIFEST_SHA256,
        },
        "analysis receipt manifest binding differs",
    )
    _require(
        analysis_receipt["analysis_implementation"]["sha256"] == ANALYZER_SHA256,
        "analysis receipt implementation differs",
    )
    _require(
        analysis_receipt["row_completeness"]["published_row_counts"] == ANALYSIS_ROWS,
        "analysis receipt row counts differ",
    )

    freeze_bindings = {item["role"]: item for item in freeze_manifest["role_bindings"]}
    receipt_inputs = {item["role"]: item for item in analysis_receipt["input_runs"]}
    runs = manifest["runs"]
    _require([run["role"] for run in runs] == list(ROLES), "run role order differs")
    for run in runs:
        role = run["role"]
        _require(
            run["role_binding"] == freeze_bindings[role], f"{role}: binding differs"
        )
        _require(run["included_file_count"] == 15, f"{role}: included count differs")
        _require(run["omitted_raw_file_count"] == 4, f"{role}: omitted count differs")
        included_by_name = _metadata_by_name(run["included_files"])
        _require(set(included_by_name) == RUN_PUBLIC_FILES, f"{role}: files differ")
        omitted_by_name = {
            Path(item["source_path"]).name: item for item in run["omitted_raw_files"]
        }
        _require(
            set(omitted_by_name) == set(RUN_OMITTED_ROWS),
            f"{role}: omitted file set differs",
        )
        for filename, expected_rows in RUN_OMITTED_ROWS.items():
            item = omitted_by_name[filename]
            _require(item["public_copy_path"] is None, f"{role}: raw copy declared")
            _require(item["row_count"] == expected_rows, f"{role}: raw rows differ")
            _require(item["bytes"] > 0, f"{role}: raw bytes missing")
            _require(
                isinstance(item["sha256"], str) and len(item["sha256"]) == 64,
                f"{role}: raw digest missing",
            )
            _require(
                not (root / BUNDLE_ROOT / "runs" / role / filename).exists(),
                f"{role}: omitted raw file is public",
            )

        input_receipt = receipt_inputs[role]
        _require(
            input_receipt["interventions_sha256"]
            == omitted_by_name["interventions.jsonl"]["sha256"],
            f"{role}: omitted interventions digest differs from analysis receipt",
        )
        receipt_hash_pairs = {
            "fingerprint_summary.jsonl": "fingerprint_summary_sha256",
            "resolved_config.yaml": "resolved_config_sha256",
            "resolved_inputs.json": "resolved_inputs_sha256",
            "receipt.json": "run_receipt_sha256",
            "summary.json": "summary_sha256",
        }
        for filename, receipt_key in receipt_hash_pairs.items():
            _require(
                included_by_name[filename]["sha256"] == input_receipt[receipt_key],
                f"{role}: {filename} differs from analysis receipt",
            )

        plan = _load_json(root / included_by_name["plan.json"]["path"])
        summary = _load_json(root / included_by_name["summary.json"]["path"])
        resolved_inputs = _load_json(
            root / included_by_name["resolved_inputs.json"]["path"]
        )
        _require(
            plan["estimated_forward_calls"] == run["planned_forward_calls"] == 1976,
            f"{role}: planned calls differ",
        )
        _require(
            summary["intervention_record_count"]
            == run["intervention_row_count"]
            == 1776,
            f"{role}: intervention rows differ",
        )
        _require(len(resolved_inputs["panel"]) == 10, f"{role}: panel count differs")
        _require(
            resolved_inputs["target_ids"] == target_ids, f"{role}: target IDs differ"
        )
        _require(
            resolved_inputs["wrapper_ids"]
            == freeze_manifest["shared_inputs"]["source"]["ordered_ids"],
            f"{role}: wrapper IDs differ",
        )

    preflight = manifest["preflight"]
    _require(preflight["sha256"] == PREFLIGHT_SHA256, "preflight digest differs")
    preflight_receipt = _load_json(root / preflight["path"])
    _require(preflight_receipt["status"] == "pass", "preflight status differs")
    _require(
        preflight_receipt["manifest_sha256"] == FREEZE_MANIFEST_SHA256,
        "preflight manifest binding differs",
    )
    _require(
        preflight_receipt["language_model_loaded"] is False
        and preflight_receipt["model_forward_executed"] is False,
        "preflight is not tokenizer-only",
    )

    inventory = manifest["inventory"]
    jsonl_items = [item for item in public_metadata if item["format"] == "jsonl"]
    omitted_items = [item for run in runs for item in run["omitted_raw_files"]]
    expected_inventory = {
        "public_member_scope": (
            "payload files under artifacts/emoji_family_exploratory_v1; "
            "the root manifest is excluded from member byte totals"
        ),
        "role_count": 5,
        "analysis_file_count": 6,
        "per_role_included_file_count": 15,
        "public_member_file_count": len(public_metadata),
        "public_file_count_including_root_manifest": len(public_metadata) + 1,
        "public_member_total_bytes": sum(item["bytes"] for item in public_metadata),
        "public_jsonl_file_count": len(jsonl_items),
        "public_jsonl_row_count": sum(item["row_count"] for item in jsonl_items),
        "omitted_raw_file_count": len(omitted_items),
        "omitted_raw_total_bytes": sum(item["bytes"] for item in omitted_items),
        "omitted_intervention_jsonl_rows": sum(
            item["row_count"] for item in omitted_items if item["format"] == "jsonl"
        ),
    }
    _require(inventory == expected_inventory, "root inventory totals differ")
    _require(
        manifest["absolute_path_scrub"]
        == {
            "policy": "fail closed on user-home or drive-qualified filesystem paths; evidence bytes are otherwise unchanged",
            "files_scanned": 82,
            "match_count": 0,
            "transformed_file_count": 0,
        },
        "absolute-path scrub declaration differs",
    )

    return {
        "schema_version": 1,
        "status": "pass",
        "bundle_id": BUNDLE_ID,
        "manifest_path": MANIFEST_PATH.as_posix(),
        "manifest_sha256": manifest_sha,
        "freeze_commit": FREEZE_COMMIT,
        "freeze_manifest_sha256": FREEZE_MANIFEST_SHA256,
        "analysis_output_sha256": ANALYSIS_SHA256,
        "analysis_jsonl_rows": ANALYSIS_ROWS,
        "independent_outcome_review": review,
        "descriptive_random_controls": random_summary,
        "roles_verified": list(ROLES),
        "role_bindings_verified": len(runs),
        "absolute_path_match_count": 0,
        "p2_c1_content_accessed": False,
        "public_inventory": inventory,
        "root_manifest_bytes": manifest_path.stat().st_size,
        "public_total_bytes_including_root_manifest": (
            inventory["public_member_total_bytes"] + manifest_path.stat().st_size
        ),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = validate_bundle(args.root)
    except (
        BundleValidationError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
