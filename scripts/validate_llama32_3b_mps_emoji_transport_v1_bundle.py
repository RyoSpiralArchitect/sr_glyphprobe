#!/usr/bin/env python3
"""Validate the compact public E2 transport bundle without local raw evidence.

Validation is intentionally limited to the frozen manifest, public payload
tree, root publication manifest, and the two bundle scripts.  It never opens,
reads, hashes, or tokenizes the P2 confirmatory or C1 causal holdout banks, and
it does not revisit omitted files under ``runs/``.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

import yaml


PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1"
BUNDLE_ID = "llama32_3b_mps_emoji_transport_v1_public_evidence"
BUNDLE_ROOT = Path("artifacts/llama32_3b_mps_emoji_transport_v1")
ROOT_MANIFEST_PATH = Path("artifacts/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_MANIFEST.json")
FREEZE_MANIFEST_PATH = Path("data/manifests/llama32_3b_mps_emoji_transport_v1.json")
PREFLIGHT_PATH = BUNDLE_ROOT / "preflight/tokenization_audit_v1.json"
ATTEMPT_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/attempt_started_receipt.json"
)
EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/execution_receipt.json"
)
PUBLIC_ATTEMPT_RECEIPT_PATH = BUNDLE_ROOT / "execution/attempt_started_receipt.json"
PUBLIC_EXECUTION_RECEIPT_PATH = BUNDLE_ROOT / "execution/execution_receipt.json"
ANALYZER_PATH = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v1.py")
BUILDER_PATH = Path("scripts/build_llama32_3b_mps_emoji_transport_v1_bundle.py")
VALIDATOR_PATH = Path("scripts/validate_llama32_3b_mps_emoji_transport_v1_bundle.py")
PUBLIC_README_PATHS = (BUNDLE_ROOT / "README.md", BUNDLE_ROOT / "README.ja.md")

ARMS = ("full50", "core35")
FAMILIES = ("sky", "food", "animals", "transport", "social")
LAYERS = (5, 11)
DIRECTION_SEEDS = (101, 211, 307)
CELL_ORDER = tuple((arm, family) for arm in ARMS for family in FAMILIES)
CONFIG_ORDER = tuple(
    f"configs/e2_llama32_3b_mps_{arm}_{family}_v1.yaml" for arm, family in CELL_ORDER
)
RUN_NAMES = tuple(
    f"e2-llama32-3b-mps-{arm}-{family}-transport-v1" for arm, family in CELL_ORDER
)
CONDITION_COUNTS = {"full50": 10, "core35": 7}
EXPECTED_FORWARD_CALLS = {"full50": 1_976, "core35": 1_496}
EXPECTED_LEDGER_ROWS = {"full50": 1_776, "core35": 1_344}
EXPECTED_TOTAL_LEDGER_ROWS = 15_600
MODEL_DIM = 3_072
VOCAB_SIZE = 128_256

RUN_PUBLIC_FILES = frozenset(
    {
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
)
RUN_OMITTED_FILES = frozenset(
    {
        "interventions.jsonl",
        "source_activations.npz",
        "directions.npz",
        "target_baselines.npz",
    }
)
RUN_ALL_FILES = RUN_PUBLIC_FILES | RUN_OMITTED_FILES

ANALYSIS_FILES = frozenset(
    {
        "panel_target_scores.jsonl",
        "transfer_target_scores.jsonl",
        "family_cell_summary.jsonl",
        "transfer_cell_summary.jsonl",
        "llama32_3b_mps_emoji_transport_receipt.json",
        "report.md",
    }
)
ANALYSIS_EXPECTED_ROWS = {
    "panel_target_scores.jsonl": 480,
    "transfer_target_scores.jsonl": 1_920,
    "family_cell_summary.jsonl": 20,
    "transfer_cell_summary.jsonl": 80,
}
ANALYSIS_UNIQUE_KEYS = {
    "panel_target_scores.jsonl": (
        "panel_arm",
        "family",
        "layer",
        "target_id",
    ),
    "transfer_target_scores.jsonl": (
        "panel_arm",
        "source_family",
        "prototype_family",
        "layer",
        "target_id",
    ),
    "family_cell_summary.jsonl": ("panel_arm", "family", "layer"),
    "transfer_cell_summary.jsonl": (
        "panel_arm",
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
HEX_64 = re.compile(r"[0-9a-f]{64}")


class BundleValidationError(RuntimeError):
    """Raised when compact public E2 evidence fails closed validation."""


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


def _load_json(path: Path, description: str) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(), f"missing {description}: {path}")
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs
    )
    _require(isinstance(value, dict), f"{description} is not a JSON object")
    return value


def _load_jsonl(path: Path, description: str) -> list[dict[str, Any]]:
    _require(path.is_file() and not path.is_symlink(), f"missing {description}: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line, object_pairs_hook=_reject_duplicate_pairs)
            _require(
                isinstance(value, dict),
                f"non-object JSONL row: {path}:{line_number}",
            )
            rows.append(value)
    _require(rows, f"empty {description}: {path}")
    return rows


def _finite_tree(value: Any, description: str) -> None:
    if isinstance(value, float):
        _require(math.isfinite(value), f"non-finite number in {description}")
    elif isinstance(value, Mapping):
        for item in value.values():
            _finite_tree(item, description)
    elif isinstance(value, list):
        for item in value:
            _finite_tree(item, description)


def _safe_public_path(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    _require(
        not candidate.is_absolute() and ".." not in candidate.parts,
        f"unsafe public path: {relative}",
    )
    resolved_root = root.resolve()
    resolved_bundle = (resolved_root / BUNDLE_ROOT).resolve()
    unresolved = resolved_root / candidate
    resolved = unresolved.resolve()
    _require(
        resolved.is_relative_to(resolved_bundle),
        f"public member escapes E2 bundle root: {relative}",
    )
    current = unresolved
    while current != resolved_root:
        _require(not current.is_symlink(), f"symlink in public path: {relative}")
        current = current.parent
    return resolved


def _scan_absolute_paths(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return sum(len(pattern.findall(text)) for pattern in ABSOLUTE_PATH_PATTERNS)


def _verify_public_member(
    root: Path, metadata: Mapping[str, Any]
) -> tuple[Path, list[dict[str, Any]] | None]:
    _require(
        set(metadata) == {"path", "format", "bytes", "row_count", "sha256"},
        "public member metadata fields differ",
    )
    relative = metadata.get("path")
    _require(isinstance(relative, str), "public member path is invalid")
    path = _safe_public_path(root, relative)
    _require(path.is_file(), f"missing public member: {relative}")
    _require(
        isinstance(metadata.get("bytes"), int)
        and metadata["bytes"] > 0
        and path.stat().st_size == metadata["bytes"],
        f"byte count differs: {path}",
    )
    digest = metadata.get("sha256")
    _require(
        isinstance(digest, str)
        and HEX_64.fullmatch(digest) is not None
        and _sha256(path) == digest,
        f"digest differs: {path}",
    )
    file_format = metadata.get("format")
    rows: list[dict[str, Any]] | None = None
    if file_format == "json":
        _load_json(path, "public JSON member")
        _require(metadata.get("row_count") is None, f"JSON row count differs: {path}")
    elif file_format == "jsonl":
        rows = _load_jsonl(path, "public JSONL member")
        _require(
            len(rows) == metadata.get("row_count"), f"JSONL row count differs: {path}"
        )
    elif file_format == "yaml":
        yaml.safe_load(path.read_text(encoding="utf-8"))
        _require(metadata.get("row_count") is None, f"YAML row count differs: {path}")
    elif file_format == "markdown":
        path.read_text(encoding="utf-8")
        _require(
            metadata.get("row_count") is None, f"Markdown row count differs: {path}"
        )
    else:
        raise BundleValidationError(f"unsupported public format: {file_format}")
    _require(_scan_absolute_paths(path) == 0, f"absolute path leak: {path}")
    return path, rows


def _metadata_by_name(
    items: Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for item in items:
        path = item.get("path")
        _require(isinstance(path, str), "public metadata path differs")
        name = Path(path).name
        _require(name not in output, f"duplicate evidence filename: {name}")
        output[name] = item
    return output


def _flatten_public_metadata(manifest: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    execution = manifest.get("execution")
    analysis = manifest.get("analysis")
    runs = manifest.get("runs")
    _require(isinstance(execution, Mapping), "execution publication block is missing")
    _require(isinstance(analysis, Mapping), "analysis publication block is missing")
    _require(isinstance(runs, list), "run publication block is missing")
    output: list[Mapping[str, Any]] = [manifest["preflight"]]
    output.extend(
        [
            execution["attempt_started_receipt"],
            execution["success_execution_receipt"],
        ]
    )
    documentation = manifest.get("documentation")
    _require(isinstance(documentation, Mapping), "documentation block is missing")
    output.extend(documentation["files"])
    output.extend(analysis["files"])
    for run in runs:
        _require(isinstance(run, Mapping), "invalid run publication row")
        output.extend(run["included_files"])
    return output


def _manifest_declared_hash(manifest: Mapping[str, Any], relative: Path) -> str:
    files = manifest.get("files")
    _require(isinstance(files, list), "freeze manifest files list is missing")
    matches = [
        row
        for row in files
        if isinstance(row, Mapping) and row.get("path") == relative.as_posix()
    ]
    _require(len(matches) == 1, f"freeze manifest does not bind {relative}")
    digest = matches[0].get("sha256")
    _require(
        isinstance(digest, str) and HEX_64.fullmatch(digest) is not None,
        f"freeze manifest hash differs: {relative}",
    )
    return digest


def _expected_npz_layout(
    filename: str, condition_count: int
) -> dict[str, tuple[list[int], str]]:
    if filename == "source_activations.npz":
        return {
            "emoji": ([condition_count, 16, 2, MODEL_DIM], "float32"),
            "layers": ([2], "int64"),
            "neutral": ([16, 2, MODEL_DIM], "float32"),
        }
    if filename == "target_baselines.npz":
        return {
            "activations": ([24, 2, MODEL_DIM], "float32"),
            "logits": ([24, VOCAB_SIZE], "float32"),
        }
    if filename == "directions.npz":
        layout: dict[str, tuple[list[int], str]] = {"layers": ([2], "int64")}
        for seed in DIRECTION_SEEDS:
            layout[f"directions_seed_{seed}"] = (
                [condition_count, 2, MODEL_DIM],
                "float32",
            )
            layout[f"panel_means_seed_{seed}"] = (
                [condition_count, 2, MODEL_DIM],
                "float32",
            )
            layout[f"generic_seed_{seed}"] = ([2, MODEL_DIM], "float32")
        return layout
    raise BundleValidationError(f"unexpected omitted NPZ: {filename}")


def _validate_omitted_record(
    record: Mapping[str, Any], *, arm: str, run_label: str
) -> None:
    filename = record.get("filename")
    _require(filename in RUN_OMITTED_FILES, f"unexpected omitted file: {filename}")
    _require(
        record.get("local_run_label") == run_label
        and record.get("public_copy_path") is None
        and record.get("omitted_reason") == "large_raw_replay_payload"
        and isinstance(record.get("bytes"), int)
        and record["bytes"] > 0
        and isinstance(record.get("sha256"), str)
        and HEX_64.fullmatch(record["sha256"]) is not None,
        f"invalid omitted metadata: {arm}/{filename}",
    )
    if filename == "interventions.jsonl":
        _require(
            set(record)
            == {
                "local_run_label",
                "filename",
                "public_copy_path",
                "omitted_reason",
                "format",
                "bytes",
                "sha256",
                "row_count",
                "row_count_basis",
            }
            and record.get("format") == "jsonl"
            and record.get("row_count") == EXPECTED_LEDGER_ROWS[arm]
            and record.get("row_count_basis") == "nonblank JSONL object records",
            f"omitted ledger metadata differs: {arm}",
        )
        return
    _require(
        set(record)
        == {
            "local_run_label",
            "filename",
            "public_copy_path",
            "omitted_reason",
            "format",
            "bytes",
            "sha256",
            "array_count",
            "arrays",
        }
        and record.get("format") == "npz",
        f"omitted NPZ metadata differs: {arm}/{filename}",
    )
    arrays = record.get("arrays")
    _require(isinstance(arrays, list), f"omitted NPZ arrays differ: {arm}/{filename}")
    expected = _expected_npz_layout(str(filename), CONDITION_COUNTS[arm])
    observed: dict[str, tuple[list[int], str]] = {}
    for item in arrays:
        _require(
            isinstance(item, Mapping)
            and set(item)
            == {"key", "shape", "dtype", "elements", "uncompressed_bytes"},
            f"omitted array metadata fields differ: {arm}/{filename}",
        )
        key = item.get("key")
        shape = item.get("shape")
        dtype = item.get("dtype")
        _require(
            isinstance(key, str)
            and key not in observed
            and isinstance(shape, list)
            and all(isinstance(value, int) and value >= 0 for value in shape)
            and isinstance(dtype, str),
            f"omitted array identity differs: {arm}/{filename}",
        )
        elements = math.prod(shape)
        expected_itemsize = 8 if dtype == "int64" else 4 if dtype == "float32" else -1
        _require(
            item.get("elements") == elements
            and item.get("uncompressed_bytes") == elements * expected_itemsize,
            f"omitted array size differs: {arm}/{filename}:{key}",
        )
        observed[key] = (shape, dtype)
    _require(
        record.get("array_count") == len(arrays) and observed == expected,
        f"omitted NPZ layout differs: {arm}/{filename}",
    )


def _validate_excluded_declaration(manifest: Mapping[str, Any]) -> None:
    declaration = manifest.get("excluded_content_access")
    _require(isinstance(declaration, Mapping), "excluded-content declaration missing")
    _require(
        declaration.get("paths") == list(EXCLUDED_CONTENT), "excluded paths differ"
    )
    for key in ("content_opened_or_read", "content_hashed", "content_tokenized"):
        _require(declaration.get(key) is False, f"excluded-content {key} differs")
    _require(
        declaration.get("model_forward_count") == 0,
        "excluded-content forward count differs",
    )


def _validate_analysis_grids(
    rows_by_name: Mapping[str, list[dict[str, Any]]], target_ids: Sequence[str]
) -> None:
    expected = {
        "panel_target_scores.jsonl": {
            (arm, family, layer, target_id)
            for arm in ARMS
            for family in FAMILIES
            for layer in LAYERS
            for target_id in target_ids
        },
        "transfer_target_scores.jsonl": {
            (arm, source, prototype, layer, target_id)
            for arm in ARMS
            for source in FAMILIES
            for prototype in FAMILIES
            if source != prototype
            for layer in LAYERS
            for target_id in target_ids
        },
        "family_cell_summary.jsonl": {
            (arm, family, layer)
            for arm in ARMS
            for family in FAMILIES
            for layer in LAYERS
        },
        "transfer_cell_summary.jsonl": {
            (arm, source, prototype, layer)
            for arm in ARMS
            for source in FAMILIES
            for prototype in FAMILIES
            if source != prototype
            for layer in LAYERS
        },
    }
    for filename, wanted in expected.items():
        keys = ANALYSIS_UNIQUE_KEYS[filename]
        rows = rows_by_name[filename]
        observed = [tuple(row.get(key) for key in keys) for row in rows]
        _require(
            len(observed) == len(set(observed)) and set(observed) == wanted,
            f"analysis unique-key grid differs: {filename}",
        )
        _finite_tree(rows, filename)


def validate_bundle(root: Path) -> dict[str, Any]:
    """Validate one already-built public E2 evidence tree."""

    root = root.resolve()
    manifest_path = root / ROOT_MANIFEST_PATH
    manifest = _load_json(manifest_path, "root publication manifest")
    manifest_sha = _sha256(manifest_path)
    _require(manifest.get("schema_version") == 1, "publication schema differs")
    _require(manifest.get("bundle_id") == BUNDLE_ID, "bundle ID differs")
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "protocol ID differs")
    _require(
        manifest.get("status") == "complete_validated_public_evidence"
        and manifest.get("scientific_outcome_interpreted_by_builder") is False,
        "publication status differs",
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
    freeze = manifest.get("freeze")
    _require(isinstance(freeze, Mapping), "publication freeze block is missing")
    freeze_path = root / FREEZE_MANIFEST_PATH
    freeze_sha = _sha256(freeze_path)
    _require(
        freeze.get("manifest_path") == FREEZE_MANIFEST_PATH.as_posix()
        and freeze.get("manifest_sha256") == freeze_sha
        and freeze.get("prepared_before_model_forward") is True,
        "publication freeze binding differs",
    )
    freeze_manifest = _load_json(freeze_path, "freeze manifest")
    _require(
        freeze_manifest.get("schema_version") == 1
        and freeze_manifest.get("protocol_id") == PROTOCOL_ID,
        "freeze manifest identity differs",
    )
    _require(
        not any(path in json.dumps(freeze_manifest) for path in EXCLUDED_CONTENT),
        "freeze manifest names a protected bank",
    )
    for tooling_path in (
        ANALYZER_PATH,
        BUILDER_PATH,
        VALIDATOR_PATH,
        *PUBLIC_README_PATHS,
    ):
        _require(
            _manifest_declared_hash(freeze_manifest, tooling_path)
            == _sha256(root / tooling_path),
            f"freeze tooling/documentation hash differs: {tooling_path}",
        )
    _validate_excluded_declaration(manifest)

    public_metadata = _flatten_public_metadata(manifest)
    _require(len(public_metadata) == 161, "public member count differs")
    public_paths = [item.get("path") for item in public_metadata]
    _require(
        all(isinstance(path, str) for path in public_paths)
        and len(public_paths) == len(set(public_paths)),
        "duplicate or invalid public member path",
    )
    actual_paths: set[str] = set()
    bundle_path = root / BUNDLE_ROOT
    _require(
        bundle_path.is_dir() and not bundle_path.is_symlink(),
        "public bundle root differs",
    )
    for path in bundle_path.rglob("*"):
        _require(not path.is_symlink(), f"symlink in public bundle: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    _require(actual_paths == set(public_paths), "public bundle tree inventory differs")

    rows_by_path: dict[str, list[dict[str, Any]]] = {}
    for metadata in public_metadata:
        _, rows = _verify_public_member(root, metadata)
        if rows is not None:
            rows_by_path[str(metadata["path"])] = rows
    _require(_scan_absolute_paths(manifest_path) == 0, "absolute path in root manifest")

    documentation = manifest["documentation"]
    _require(
        documentation.get("language_order") == ["en", "ja"]
        and documentation.get("file_count") == 2,
        "public documentation declaration differs",
    )
    documentation_by_name = _metadata_by_name(documentation["files"])
    _require(
        set(documentation_by_name) == {"README.md", "README.ja.md"},
        "public README pair differs",
    )
    _require(
        [item["path"] for item in documentation["files"]]
        == [path.as_posix() for path in PUBLIC_README_PATHS],
        "public README order differs",
    )
    for relative in PUBLIC_README_PATHS:
        metadata = documentation_by_name[relative.name]
        _require(
            metadata["path"] == relative.as_posix()
            and metadata["sha256"]
            == _manifest_declared_hash(freeze_manifest, relative),
            f"public README freeze binding differs: {relative}",
        )

    preflight_metadata = manifest.get("preflight")
    _require(
        isinstance(preflight_metadata, Mapping)
        and preflight_metadata.get("path") == PREFLIGHT_PATH.as_posix(),
        "public preflight path differs",
    )
    preflight = _load_json(root / PREFLIGHT_PATH, "public preflight")
    _require(
        preflight.get("schema_version") == 1
        and preflight.get("protocol_id") == PROTOCOL_ID
        and preflight.get("status") == "passed"
        and preflight.get("model_forward_count") == 0
        and preflight.get("language_model_loaded") is False
        and preflight.get("scientific_outcomes_inspected") is False
        and preflight.get("p2_content_opened") is False
        and preflight.get("c1_content_opened") is False,
        "public preflight status differs",
    )
    static = preflight.get("static")
    freeze_binding = static.get("manifest") if isinstance(static, Mapping) else None
    _require(
        isinstance(freeze_binding, Mapping)
        and freeze_binding.get("path") == FREEZE_MANIFEST_PATH.as_posix()
        and freeze_binding.get("sha256") == freeze_sha,
        "public preflight freeze binding differs",
    )

    execution_block = manifest["execution"]
    _require(
        execution_block.get("failed_execution_receipt_absent") is True,
        "failed-execution declaration differs",
    )
    attempt_metadata = execution_block["attempt_started_receipt"]
    success_metadata = execution_block["success_execution_receipt"]
    _require(
        attempt_metadata.get("path") == PUBLIC_ATTEMPT_RECEIPT_PATH.as_posix()
        and success_metadata.get("path") == PUBLIC_EXECUTION_RECEIPT_PATH.as_posix(),
        "public execution receipt paths differ",
    )
    attempt = _load_json(root / PUBLIC_ATTEMPT_RECEIPT_PATH, "public attempt receipt")
    success = _load_json(root / PUBLIC_EXECUTION_RECEIPT_PATH, "public success receipt")
    _require(
        set(attempt)
        == {
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
        },
        "public attempt fields differ",
    )
    _require(
        set(success)
        == {
            "schema_version",
            "protocol_id",
            "status",
            "scientific_outcomes_inspected_by_launcher",
            "freeze_commit",
            "audited_commit",
            "branch",
            "attempt_started_receipt",
            "preflight_path",
            "preflight_sha256",
            "started_at",
            "finished_at",
            "process_isolation",
            "simultaneous_full_model_residency",
            "resume_policy",
            "initial_namespace_check",
            "processes",
            "completed_process_count",
            "expected_process_count",
            "analysis_authorized",
            "failed_execution_receipt_written",
        },
        "public success fields differ",
    )
    namespace = {
        "resume_allowed": False,
        "run_name_count": 10,
        "existing_run_destination_count": 0,
        "launcher_log_namespace_preexisting": False,
    }
    _require(
        attempt.get("schema_version") == 1
        and attempt.get("protocol_id") == PROTOCOL_ID
        and attempt.get("status") == "attempt_started_no_process_launched"
        and attempt.get("scientific_outcomes_inspected_by_launcher") is False
        and attempt.get("model_process_count_at_publication") == 0
        and attempt.get("config_order") == list(CONFIG_ORDER)
        and attempt.get("run_names") == list(RUN_NAMES)
        and attempt.get("initial_namespace_check") == namespace
        and attempt.get("resume_policy")
        == "forbidden_in_v1_new_versioned_freeze_required",
        "public attempt receipt differs",
    )
    _require(
        attempt.get("preflight")
        == {"path": PREFLIGHT_PATH.as_posix(), "sha256": preflight_metadata["sha256"]}
        and attempt.get("manifest")
        == {"path": FREEZE_MANIFEST_PATH.as_posix(), "sha256": freeze_sha},
        "public attempt authority chain differs",
    )
    preflight_git = preflight.get("git_authority")
    _require(
        preflight.get("audited_commit") == success.get("audited_commit")
        and isinstance(preflight_git, Mapping)
        and preflight_git.get("audited_commit") == success.get("audited_commit")
        and preflight_git.get("origin_main_commit") == success.get("audited_commit")
        and preflight_git.get("branch") == "main"
        and preflight_git.get("worktree_clean_before_publication") is True,
        "public preflight/execution Git authority differs",
    )
    _require(
        success.get("schema_version") == 1
        and success.get("protocol_id") == PROTOCOL_ID
        and success.get("status") == "execution_complete_analysis_not_run"
        and success.get("scientific_outcomes_inspected_by_launcher") is False
        and success.get("analysis_authorized") is True
        and success.get("failed_execution_receipt_written") is False
        and success.get("completed_process_count") == 10
        and success.get("expected_process_count") == 10
        and success.get("initial_namespace_check") == namespace
        and success.get("attempt_started_receipt")
        == {
            "path": ATTEMPT_RECEIPT_PATH.as_posix(),
            "sha256": attempt_metadata["sha256"],
        },
        "public success receipt differs",
    )
    git_freeze = attempt.get("git_freeze")
    _require(
        isinstance(git_freeze, Mapping)
        and success.get("audited_commit")
        == freeze.get("audited_commit")
        == git_freeze.get("audited_commit")
        and success.get("freeze_commit")
        == freeze.get("execution_commit")
        == git_freeze.get("execution_commit")
        and git_freeze.get("origin_main_commit") == git_freeze.get("execution_commit")
        and git_freeze.get("branch") == success.get("branch") == "main",
        "public Git freeze chain differs",
    )
    processes = success.get("processes")
    _require(
        isinstance(processes, list) and len(processes) == 10,
        "public process grid differs",
    )
    log_inventory = execution_block.get("launcher_logs_publicly_omitted")
    _require(
        isinstance(log_inventory, list) and len(log_inventory) == 10,
        "launcher-log inventory differs",
    )
    for index, (config, process, log_item) in enumerate(
        zip(CONFIG_ORDER, processes, log_inventory)
    ):
        _require(
            isinstance(process, Mapping)
            and process.get("index") == index
            and process.get("config") == config
            and process.get("config_sha256")
            == _manifest_declared_hash(freeze_manifest, Path(config))
            == _sha256(root / config)
            and process.get("return_code") == 0,
            f"public process row differs: {index}",
        )
        _require(
            isinstance(log_item, Mapping)
            and log_item.get("path") == process.get("log_path")
            and log_item.get("sha256") == process.get("log_sha256")
            and log_item.get("public_copy_path") is None
            and log_item.get("omitted_reason") == "launcher_log_contains_local_run_path"
            and isinstance(log_item.get("bytes"), int)
            and log_item["bytes"] > 0,
            f"launcher-log metadata differs: {index}",
        )

    analysis_block = manifest["analysis"]
    _require(
        analysis_block.get("implementation_path") == ANALYZER_PATH.as_posix()
        and analysis_block.get("implementation_sha256") == _sha256(root / ANALYZER_PATH)
        and analysis_block.get("file_count") == 6
        and analysis_block.get("expected_jsonl_rows") == ANALYSIS_EXPECTED_ROWS,
        "public analysis binding differs",
    )
    analysis_by_name = _metadata_by_name(analysis_block["files"])
    _require(set(analysis_by_name) == ANALYSIS_FILES, "analysis file inventory differs")
    _require(
        analysis_block.get("output_sha256")
        == {name: analysis_by_name[name]["sha256"] for name in sorted(ANALYSIS_FILES)},
        "analysis output hash map differs",
    )
    rows_by_name = {
        name: rows_by_path[str(analysis_by_name[name]["path"])]
        for name in ANALYSIS_EXPECTED_ROWS
    }
    for name, expected_rows in ANALYSIS_EXPECTED_ROWS.items():
        _require(
            len(rows_by_name[name]) == expected_rows, f"analysis rows differ: {name}"
        )
    analysis_receipt = _load_json(
        root / analysis_by_name["llama32_3b_mps_emoji_transport_receipt.json"]["path"],
        "public analysis receipt",
    )
    _require(
        analysis_receipt.get("schema_version") == 1
        and analysis_receipt.get("analysis_id") == PROTOCOL_ID
        and analysis_receipt.get("status")
        in {"transport_criterion_met", "transport_criterion_not_met"}
        and analysis_block.get("analysis_status_copied_without_interpretation")
        == analysis_receipt.get("status"),
        "public analysis status differs",
    )
    _require(
        analysis_receipt.get("analysis_implementation")
        == {
            "path": ANALYZER_PATH.as_posix(),
            "sha256": _sha256(root / ANALYZER_PATH),
        }
        and analysis_receipt.get("output_inventory")
        == [
            "panel_target_scores.jsonl",
            "transfer_target_scores.jsonl",
            "family_cell_summary.jsonl",
            "transfer_cell_summary.jsonl",
            "llama32_3b_mps_emoji_transport_receipt.json",
            "report.md",
        ],
        "public analysis implementation/output inventory differs",
    )
    hashed_outputs = analysis_receipt.get("hashed_outputs_excluding_self")
    _require(
        isinstance(hashed_outputs, list) and len(hashed_outputs) == 5,
        "analysis output hash list differs",
    )
    expected_hashed_outputs = {
        name: analysis_by_name[name]["sha256"]
        for name in ANALYSIS_FILES
        if name != "llama32_3b_mps_emoji_transport_receipt.json"
    }
    observed_hashed_outputs = {
        row.get("filename"): row.get("sha256")
        for row in hashed_outputs
        if isinstance(row, Mapping)
    }
    _require(
        len(observed_hashed_outputs) == 5
        and observed_hashed_outputs == expected_hashed_outputs,
        "public analysis output hashes differ",
    )
    _require(
        analysis_receipt.get("manifest_binding")
        == {"path": FREEZE_MANIFEST_PATH.as_posix(), "sha256": freeze_sha}
        and analysis_receipt.get("execution_binding", {}).get("path")
        == EXECUTION_RECEIPT_PATH.as_posix()
        and analysis_receipt.get("execution_binding", {}).get("sha256")
        == success_metadata["sha256"]
        and analysis_receipt.get("row_completeness", {}).get("published_row_counts")
        == ANALYSIS_EXPECTED_ROWS,
        "public analysis authority chain differs",
    )
    data_scope = analysis_receipt.get("data_scope")
    _require(
        isinstance(data_scope, Mapping)
        and data_scope.get("p2_confirmatory_holdout_accessed") is False
        and data_scope.get("c1_causal_holdout_accessed") is False,
        "public analysis protected-data boundary differs",
    )
    _require(
        data_scope.get("model_forward_passes_by_analyzer") == 0
        and data_scope.get("tokenizer_calls_by_analyzer") == 0,
        "public analysis execution boundary differs",
    )
    target_ids = data_scope.get("ordered_target_ids")
    _require(
        isinstance(target_ids, list)
        and len(target_ids) == 24
        and len(set(target_ids)) == 24,
        "public target ID grid differs",
    )
    _validate_analysis_grids(rows_by_name, target_ids)

    input_runs = analysis_receipt.get("input_runs")
    runs = manifest.get("runs")
    _require(
        isinstance(input_runs, list)
        and isinstance(runs, list)
        and len(input_runs) == len(runs) == 10,
        "public run grid differs",
    )
    omitted_total_rows = 0
    omitted_total_files = 0
    for index, ((arm, family), run, input_run) in enumerate(
        zip(CELL_ORDER, runs, input_runs)
    ):
        _require(
            isinstance(run, Mapping) and isinstance(input_run, Mapping),
            f"invalid run row: {index}",
        )
        run_label = run.get("run_label")
        _require(
            run.get("panel_arm") == input_run.get("panel_arm") == arm
            and run.get("family") == input_run.get("role") == family
            and run_label == input_run.get("run_label")
            and isinstance(run_label, str)
            and run_label.startswith(f"{RUN_NAMES[index]}--")
            and run.get("included_file_count") == 15
            and run.get("omitted_raw_file_count") == 4
            and run.get("planned_forward_calls") == EXPECTED_FORWARD_CALLS[arm]
            and run.get("intervention_row_count") == EXPECTED_LEDGER_ROWS[arm],
            f"public run role/count binding differs: {arm}/{family}",
        )
        public_directory = BUNDLE_ROOT / "runs" / arm / family
        _require(
            run.get("public_directory") == public_directory.as_posix(),
            f"public run path differs: {arm}/{family}",
        )
        included_by_name = _metadata_by_name(run["included_files"])
        _require(
            set(included_by_name) == RUN_PUBLIC_FILES,
            f"included run files differ: {arm}/{family}",
        )
        _require(
            all(
                Path(metadata["path"]).parent == public_directory
                for metadata in included_by_name.values()
            ),
            f"included run paths cross role directories: {arm}/{family}",
        )
        omitted = run.get("omitted_raw_files")
        _require(
            isinstance(omitted, list) and len(omitted) == 4,
            f"omitted run files differ: {arm}/{family}",
        )
        omitted_by_name = {
            item.get("filename"): item for item in omitted if isinstance(item, Mapping)
        }
        _require(
            set(omitted_by_name) == RUN_OMITTED_FILES,
            f"omitted file set differs: {arm}/{family}",
        )
        for record in omitted:
            _validate_omitted_record(record, arm=arm, run_label=str(run_label))
            omitted_total_files += 1
            if record.get("filename") == "interventions.jsonl":
                omitted_total_rows += int(record["row_count"])
        _require(
            all(
                not (root / public_directory / name).exists()
                for name in RUN_OMITTED_FILES
            ),
            f"omitted raw file is public: {arm}/{family}",
        )
        complete_inventory = input_run.get("complete_run_file_inventory")
        _require(
            isinstance(complete_inventory, Mapping)
            and set(complete_inventory) == RUN_ALL_FILES,
            f"analysis run inventory differs: {arm}/{family}",
        )
        for name, metadata in included_by_name.items():
            _require(
                metadata["sha256"] == complete_inventory[name],
                f"included run hash differs from analysis: {arm}/{family}/{name}",
            )
        for name, metadata in omitted_by_name.items():
            _require(
                metadata["sha256"] == complete_inventory[name],
                f"omitted run hash differs from analysis: {arm}/{family}/{name}",
            )
        plan = _load_json(
            root / included_by_name["plan.json"]["path"], "public run plan"
        )
        summary = _load_json(
            root / included_by_name["summary.json"]["path"], "public run summary"
        )
        receipt = _load_json(
            root / included_by_name["receipt.json"]["path"], "public run receipt"
        )
        resolved_inputs = _load_json(
            root / included_by_name["resolved_inputs.json"]["path"],
            "public resolved inputs",
        )
        _require(
            plan.get("estimated_forward_calls") == EXPECTED_FORWARD_CALLS[arm]
            and summary.get("intervention_record_count") == EXPECTED_LEDGER_ROWS[arm]
            and receipt.get("status") == "complete"
            and receipt.get("run_id") == run_label
            and receipt.get("run_seal") == run.get("run_seal")
            and len(resolved_inputs.get("panel", [])) == CONDITION_COUNTS[arm]
            and len(resolved_inputs.get("target_ids", [])) == 24
            and len(resolved_inputs.get("wrapper_ids", [])) == 16,
            f"public run payload differs: {arm}/{family}",
        )
    _require(
        omitted_total_files == 40 and omitted_total_rows == EXPECTED_TOTAL_LEDGER_ROWS,
        "omitted raw totals differ",
    )

    inventory = manifest.get("inventory")
    _require(isinstance(inventory, Mapping), "root inventory is missing")
    jsonl_items = [item for item in public_metadata if item["format"] == "jsonl"]
    omitted_items = [item for run in runs for item in run["omitted_raw_files"]]
    expected_inventory = {
        "public_member_scope": (
            "payload files under artifacts/llama32_3b_mps_emoji_transport_v1; "
            "the root manifest is excluded from member byte totals"
        ),
        "run_count": 10,
        "analysis_file_count": 6,
        "execution_receipt_file_count": 2,
        "preflight_file_count": 1,
        "documentation_file_count": 2,
        "per_run_included_file_count": 15,
        "public_member_file_count": 161,
        "public_file_count_including_root_manifest": 162,
        "public_member_total_bytes": sum(item["bytes"] for item in public_metadata),
        "public_jsonl_file_count": len(jsonl_items),
        "public_jsonl_row_count": sum(item["row_count"] for item in jsonl_items),
        "omitted_raw_file_count": len(omitted_items),
        "omitted_raw_total_bytes": sum(item["bytes"] for item in omitted_items),
        "omitted_intervention_jsonl_rows": EXPECTED_TOTAL_LEDGER_ROWS,
        "omitted_launcher_log_file_count": 10,
    }
    _require(dict(inventory) == expected_inventory, "root inventory totals differ")
    _require(
        manifest.get("absolute_path_scan")
        == {
            "policy": "fail closed on home, temporary, volume, or drive-qualified filesystem paths; evidence bytes are unchanged",
            "files_scanned": 161,
            "match_count": 0,
            "transformed_file_count": 0,
        },
        "absolute-path scan declaration differs",
    )
    return {
        "schema_version": 1,
        "status": "pass",
        "bundle_id": BUNDLE_ID,
        "protocol_id": PROTOCOL_ID,
        "manifest_path": ROOT_MANIFEST_PATH.as_posix(),
        "manifest_sha256": manifest_sha,
        "freeze_manifest_sha256": freeze_sha,
        "analysis_status_copied_without_interpretation": analysis_receipt["status"],
        "analysis_jsonl_rows": ANALYSIS_EXPECTED_ROWS,
        "runs_verified": 10,
        "public_members_verified": 161,
        "omitted_raw_files_inventoried": 40,
        "omitted_intervention_jsonl_rows": EXPECTED_TOTAL_LEDGER_ROWS,
        "absolute_path_match_count": 0,
        "p2_c1_content_accessed": False,
        "public_inventory": dict(inventory),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
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
