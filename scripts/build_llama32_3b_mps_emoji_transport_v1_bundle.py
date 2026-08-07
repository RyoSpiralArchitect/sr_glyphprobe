#!/usr/bin/env python3
"""Build the compact public E2 Llama-3.2-3B transport evidence bundle.

The builder accepts the ten completed run directories in the frozen
arm/family order and one completed six-file analysis directory.  It copies
only the 15 non-large files from each exact 19-file run.  The four large raw
files remain local and are represented by checksums plus JSONL or NPZ
inventories.  Confirmatory and causal holdout banks are outside this script's
input surface and are never opened, read, hashed, or tokenized.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any

import numpy as np
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
FAILED_EXECUTION_RECEIPT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v1/failed_execution_receipt.json"
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
    "source_activations.npz",
    "directions.npz",
    "target_baselines.npz",
)
RUN_ALL_FILES = frozenset((*RUN_PUBLIC_FILES, *RUN_OMITTED_FILES))

ANALYSIS_FILES = (
    "panel_target_scores.jsonl",
    "transfer_target_scores.jsonl",
    "family_cell_summary.jsonl",
    "transfer_cell_summary.jsonl",
    "llama32_3b_mps_emoji_transport_receipt.json",
    "report.md",
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


class BundleBuildError(RuntimeError):
    """Raised when local E2 evidence violates the compact bundle contract."""


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
    _require(isinstance(value, dict), f"{description} is not a JSON object: {path}")
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
                f"non-object JSONL row in {description}: {path}:{line_number}",
            )
            rows.append(value)
    _require(rows, f"empty {description}: {path}")
    return rows


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


def _validate_text_file(path: Path, file_format: str) -> int | None:
    if file_format == "json":
        _load_json(path, "JSON evidence")
        return None
    if file_format == "jsonl":
        return len(_load_jsonl(path, "JSONL evidence"))
    if file_format == "yaml":
        yaml.safe_load(path.read_text(encoding="utf-8"))
        return None
    if file_format == "markdown":
        path.read_text(encoding="utf-8")
        return None
    raise BundleBuildError(f"cannot validate textual evidence format: {file_format}")


def _public_file_metadata(root: Path, path: Path) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(), f"missing public member: {path}")
    file_format = _format_for(path)
    _require(file_format != "npz", f"large NPZ must not be public: {path}")
    row_count = _validate_text_file(path, file_format)
    return {
        "path": path.relative_to(root).as_posix(),
        "format": file_format,
        "bytes": path.stat().st_size,
        "row_count": row_count,
        "sha256": _sha256(path),
    }


def _array_inventory(path: Path) -> list[dict[str, Any]]:
    arrays: list[dict[str, Any]] = []
    with np.load(path, allow_pickle=False) as archive:
        for key in sorted(archive.files):
            value = archive[key]
            _require(
                np.issubdtype(value.dtype, np.number),
                f"non-numeric omitted array: {path}:{key}",
            )
            _require(
                np.all(np.isfinite(value)), f"non-finite omitted array: {path}:{key}"
            )
            arrays.append(
                {
                    "key": key,
                    "shape": [int(item) for item in value.shape],
                    "dtype": str(value.dtype),
                    "elements": int(value.size),
                    "uncompressed_bytes": int(value.nbytes),
                }
            )
    return arrays


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
    raise BundleBuildError(f"unexpected omitted NPZ: {filename}")


def _omitted_file_metadata(
    source: Path, *, run_label: str, condition_count: int, expected_ledger_rows: int
) -> dict[str, Any]:
    _require(
        source.is_file() and not source.is_symlink(),
        f"missing omitted source evidence: {source}",
    )
    metadata: dict[str, Any] = {
        "local_run_label": run_label,
        "filename": source.name,
        "public_copy_path": None,
        "omitted_reason": "large_raw_replay_payload",
        "format": _format_for(source),
        "bytes": source.stat().st_size,
        "sha256": _sha256(source),
    }
    if source.name == "interventions.jsonl":
        row_count = len(_load_jsonl(source, "omitted intervention ledger"))
        _require(
            row_count == expected_ledger_rows,
            f"omitted intervention row count differs: {source}",
        )
        metadata.update(
            {
                "row_count": row_count,
                "row_count_basis": "nonblank JSONL object records",
            }
        )
        return metadata

    arrays = _array_inventory(source)
    observed_layout = {item["key"]: (item["shape"], item["dtype"]) for item in arrays}
    expected_layout = _expected_npz_layout(source.name, condition_count)
    _require(
        observed_layout == expected_layout, f"omitted NPZ layout differs: {source}"
    )
    if "layers" in observed_layout:
        with np.load(source, allow_pickle=False) as archive:
            _require(
                archive["layers"].tolist() == list(LAYERS),
                f"omitted NPZ layer values differ: {source}",
            )
    metadata.update({"array_count": len(arrays), "arrays": arrays})
    return metadata


def _scan_absolute_paths(paths: Sequence[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            for pattern in ABSOLUTE_PATH_PATTERNS:
                for match in pattern.finditer(line):
                    findings.append(
                        {
                            "path": path.as_posix(),
                            "line": line_number,
                            "match": match.group(0),
                        }
                    )
    return findings


def _copy_exact(source: Path, destination: Path) -> None:
    _require(source.is_file() and not source.is_symlink(), f"missing source: {source}")
    if source.resolve() == destination.resolve():
        return
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


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
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


def _exact_directory(
    path: Path, expected_files: frozenset[str], description: str
) -> None:
    _require(path.is_dir() and not path.is_symlink(), f"missing {description}: {path}")
    entries = list(path.iterdir())
    _require(
        all(entry.is_file() and not entry.is_symlink() for entry in entries),
        f"{description} contains a directory or symlink: {path}",
    )
    observed = {entry.name for entry in entries}
    _require(
        observed == expected_files,
        f"{description} inventory differs: missing={sorted(expected_files - observed)}, "
        f"extra={sorted(observed - expected_files)}",
    )


def _finite_tree(value: Any, description: str) -> None:
    if isinstance(value, float):
        _require(math.isfinite(value), f"non-finite number in {description}")
    elif isinstance(value, Mapping):
        for item in value.values():
            _finite_tree(item, description)
    elif isinstance(value, list):
        for item in value:
            _finite_tree(item, description)


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
        isinstance(digest, str) and HEX_64.fullmatch(digest),
        f"invalid hash: {relative}",
    )
    return digest


def _validate_freeze_and_preflight(
    root: Path, preflight_path: Path
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    freeze_path = root / FREEZE_MANIFEST_PATH
    freeze = _load_json(freeze_path, "freeze manifest")
    _require(freeze.get("schema_version") == 1, "freeze manifest schema differs")
    _require(freeze.get("protocol_id") == PROTOCOL_ID, "freeze protocol differs")
    _require(
        not any(path in json.dumps(freeze) for path in EXCLUDED_CONTENT),
        "freeze manifest names a protected bank",
    )
    freeze_sha = _sha256(freeze_path)
    for tooling_path in (
        ANALYZER_PATH,
        BUILDER_PATH,
        VALIDATOR_PATH,
        *PUBLIC_README_PATHS,
    ):
        _require(
            _manifest_declared_hash(freeze, tooling_path)
            == _sha256(root / tooling_path),
            f"freeze tooling hash differs: {tooling_path}",
        )

    _require(
        preflight_path.resolve() == (root / PREFLIGHT_PATH).resolve(),
        "preflight path differs",
    )
    preflight = _load_json(preflight_path, "tokenizer preflight")
    expected = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "passed",
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "p2_content_opened": False,
        "c1_content_opened": False,
    }
    for key, wanted in expected.items():
        _require(preflight.get(key) == wanted, f"preflight {key} differs")
    static = preflight.get("static")
    binding = static.get("manifest") if isinstance(static, Mapping) else None
    _require(
        isinstance(binding, Mapping)
        and binding.get("path") == FREEZE_MANIFEST_PATH.as_posix()
        and binding.get("sha256") == freeze_sha,
        "preflight freeze-manifest binding differs",
    )
    return freeze, freeze_sha, preflight


def _parse_timestamp(value: Any, description: str) -> datetime:
    _require(isinstance(value, str), f"missing timestamp: {description}")
    parsed = datetime.fromisoformat(value)
    _require(parsed.tzinfo is not None, f"naive timestamp: {description}")
    return parsed


def _validate_execution_chain(
    root: Path,
    *,
    attempt_path: Path,
    execution_path: Path,
    freeze_sha: str,
    preflight_sha: str,
    preflight: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    _require(
        attempt_path.resolve() == (root / ATTEMPT_RECEIPT_PATH).resolve(),
        "attempt-started receipt path differs",
    )
    _require(
        execution_path.resolve() == (root / EXECUTION_RECEIPT_PATH).resolve(),
        "execution receipt path differs",
    )
    _require(
        not os.path.lexists(root / FAILED_EXECUTION_RECEIPT_PATH),
        "failed-execution receipt exists; public success bundle is forbidden",
    )
    attempt = _load_json(attempt_path, "attempt-started receipt")
    execution = _load_json(execution_path, "success execution receipt")
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
    _require(set(attempt) == expected_attempt_keys, "attempt-started fields differ")
    expected_execution_keys = {
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
    }
    _require(
        set(execution) == expected_execution_keys, "success execution fields differ"
    )
    namespace = {
        "resume_allowed": False,
        "run_name_count": 10,
        "existing_run_destination_count": 0,
        "launcher_log_namespace_preexisting": False,
    }
    expected_attempt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "attempt_started_no_process_launched",
        "scientific_outcomes_inspected_by_launcher": False,
        "model_process_count_at_publication": 0,
        "config_order": list(CONFIG_ORDER),
        "run_names": list(RUN_NAMES),
        "initial_namespace_check": namespace,
        "launcher_log_namespace": "runs/.e2-llama32-3b-mps-transport-v1-launcher-logs",
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
    }
    for key, wanted in expected_attempt.items():
        _require(attempt.get(key) == wanted, f"attempt-started {key} differs")
    _require(
        attempt.get("preflight")
        == {"path": PREFLIGHT_PATH.as_posix(), "sha256": preflight_sha},
        "attempt-started preflight binding differs",
    )
    _require(
        attempt.get("manifest")
        == {"path": FREEZE_MANIFEST_PATH.as_posix(), "sha256": freeze_sha},
        "attempt-started freeze binding differs",
    )
    expected_execution = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "execution_complete_analysis_not_run",
        "scientific_outcomes_inspected_by_launcher": False,
        "branch": "main",
        "preflight_path": PREFLIGHT_PATH.as_posix(),
        "preflight_sha256": preflight_sha,
        "process_isolation": "strictly_sequential_independent_python_processes",
        "simultaneous_full_model_residency": False,
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
        "initial_namespace_check": namespace,
        "completed_process_count": 10,
        "expected_process_count": 10,
        "analysis_authorized": True,
        "failed_execution_receipt_written": False,
    }
    for key, wanted in expected_execution.items():
        _require(execution.get(key) == wanted, f"execution {key} differs")
    _require(
        execution.get("attempt_started_receipt")
        == {"path": ATTEMPT_RECEIPT_PATH.as_posix(), "sha256": _sha256(attempt_path)},
        "execution attempt-start binding differs",
    )
    started = _parse_timestamp(execution.get("started_at"), "execution.started_at")
    finished = _parse_timestamp(execution.get("finished_at"), "execution.finished_at")
    _require(started <= finished, "execution timestamp interval differs")
    _require(
        attempt.get("started_at") == execution.get("started_at"),
        "attempt start time differs",
    )
    git_freeze = attempt.get("git_freeze")
    _require(isinstance(git_freeze, Mapping), "attempt Git freeze is missing")
    _require(
        execution.get("audited_commit") == git_freeze.get("audited_commit")
        and execution.get("freeze_commit") == git_freeze.get("execution_commit")
        and git_freeze.get("origin_main_commit") == git_freeze.get("execution_commit")
        and git_freeze.get("branch") == "main",
        "execution Git freeze chain differs",
    )
    preflight_git = preflight.get("git_authority")
    _require(
        preflight.get("audited_commit") == execution.get("audited_commit")
        and isinstance(preflight_git, Mapping)
        and preflight_git.get("audited_commit") == execution.get("audited_commit")
        and preflight_git.get("origin_main_commit") == execution.get("audited_commit")
        and preflight_git.get("branch") == "main"
        and preflight_git.get("worktree_clean_before_publication") is True,
        "preflight/execution Git authority differs",
    )
    processes = execution.get("processes")
    _require(
        isinstance(processes, list) and len(processes) == 10,
        "execution process grid differs",
    )
    launcher_logs: list[dict[str, Any]] = []
    for index, (config, row) in enumerate(zip(CONFIG_ORDER, processes)):
        _require(isinstance(row, Mapping), f"invalid execution process {index}")
        _require(
            row.get("index") == index
            and row.get("config") == config
            and row.get("config_sha256") == _sha256(root / config)
            and row.get("return_code") == 0,
            f"execution process {index} differs",
        )
        process_started = _parse_timestamp(
            row.get("started_at"), f"process[{index}].started_at"
        )
        process_finished = _parse_timestamp(
            row.get("finished_at"), f"process[{index}].finished_at"
        )
        _require(
            started <= process_started <= process_finished <= finished,
            f"execution process {index} timestamp interval differs",
        )
        log_relative = row.get("log_path")
        _require(
            isinstance(log_relative, str), f"execution process {index} log path differs"
        )
        log_path = (root / log_relative).resolve()
        _require(
            log_path.is_relative_to(root)
            and log_path.is_file()
            and not log_path.is_symlink()
            and log_path.stat().st_size > 0
            and row.get("log_sha256") == _sha256(log_path),
            f"execution process {index} log binding differs",
        )
        launcher_logs.append(
            {
                "path": log_relative,
                "public_copy_path": None,
                "omitted_reason": "launcher_log_contains_local_run_path",
                "bytes": log_path.stat().st_size,
                "sha256": row["log_sha256"],
            }
        )
    return attempt, execution, launcher_logs


def _validate_analysis(
    analysis_dir: Path,
    *,
    freeze_sha: str,
    execution_sha: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[dict[str, Any]]]]:
    _exact_directory(analysis_dir, frozenset(ANALYSIS_FILES), "analysis directory")
    rows_by_name: dict[str, list[dict[str, Any]]] = {}
    for filename, expected_rows in ANALYSIS_EXPECTED_ROWS.items():
        rows = _load_jsonl(analysis_dir / filename, f"analysis {filename}")
        _require(len(rows) == expected_rows, f"analysis row count differs: {filename}")
        keys = ANALYSIS_UNIQUE_KEYS[filename]
        observed = [tuple(row.get(key) for key in keys) for row in rows]
        _require(
            len(observed) == len(set(observed)), f"duplicate analysis key: {filename}"
        )
        rows_by_name[filename] = rows
    receipt = _load_json(
        analysis_dir / "llama32_3b_mps_emoji_transport_receipt.json",
        "analysis receipt",
    )
    _require(
        receipt.get("schema_version") == 1
        and receipt.get("analysis_id") == PROTOCOL_ID
        and receipt.get("status")
        in {"transport_criterion_met", "transport_criterion_not_met"}
        and receipt.get("scientific_result") is True,
        "analysis receipt status differs",
    )
    _require(
        receipt.get("analysis_implementation")
        == {
            "path": ANALYZER_PATH.as_posix(),
            "sha256": _sha256(Path(__file__).resolve().parents[1] / ANALYZER_PATH),
        },
        "analysis implementation binding differs",
    )
    _require(
        receipt.get("manifest_binding")
        == {"path": FREEZE_MANIFEST_PATH.as_posix(), "sha256": freeze_sha},
        "analysis freeze-manifest binding differs",
    )
    execution_binding = receipt.get("execution_binding")
    _require(
        isinstance(execution_binding, Mapping)
        and execution_binding.get("path") == EXECUTION_RECEIPT_PATH.as_posix()
        and execution_binding.get("sha256") == execution_sha,
        "analysis execution binding differs",
    )
    data_scope = receipt.get("data_scope")
    _require(
        isinstance(data_scope, Mapping)
        and data_scope.get("p2_confirmatory_holdout_accessed") is False
        and data_scope.get("c1_causal_holdout_accessed") is False
        and data_scope.get("model_forward_passes_by_analyzer") == 0
        and data_scope.get("tokenizer_calls_by_analyzer") == 0,
        "analysis protected-data boundary differs",
    )
    target_ids = data_scope.get("ordered_target_ids")
    _require(
        isinstance(target_ids, list)
        and len(target_ids) == 24
        and len(set(target_ids)) == 24
        and all(isinstance(value, str) and value for value in target_ids),
        "analysis target ID grid differs",
    )
    expected_grids = {
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
    for filename, expected in expected_grids.items():
        keys = ANALYSIS_UNIQUE_KEYS[filename]
        actual = {tuple(row.get(key) for key in keys) for row in rows_by_name[filename]}
        _require(actual == expected, f"analysis key grid differs: {filename}")
        _finite_tree(rows_by_name[filename], filename)
    _require(
        receipt.get("row_completeness", {}).get("published_row_counts")
        == ANALYSIS_EXPECTED_ROWS,
        "analysis receipt row completeness differs",
    )
    _require(
        receipt.get("output_inventory") == list(ANALYSIS_FILES),
        "analysis output inventory differs",
    )
    hashed_outputs = receipt.get("hashed_outputs_excluding_self")
    expected_hashed_outputs = {
        filename: _sha256(analysis_dir / filename)
        for filename in ANALYSIS_FILES
        if filename != "llama32_3b_mps_emoji_transport_receipt.json"
    }
    _require(isinstance(hashed_outputs, list), "analysis output hash list is missing")
    observed_hashed_outputs = {
        row.get("filename"): row.get("sha256")
        for row in hashed_outputs
        if isinstance(row, Mapping)
    }
    _require(
        len(observed_hashed_outputs) == len(hashed_outputs) == 5
        and observed_hashed_outputs == expected_hashed_outputs,
        "analysis output hashes differ",
    )
    return [], receipt, rows_by_name


def _validate_run_source(
    root: Path,
    run_dir: Path,
    *,
    arm: str,
    family: str,
    analysis_input: Mapping[str, Any],
    process: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    _exact_directory(run_dir, RUN_ALL_FILES, f"{arm}/{family} run")
    expected_parent = (root / "runs").resolve()
    _require(
        run_dir.resolve().parent == expected_parent,
        f"{arm}/{family} run is outside repo runs",
    )
    receipt = _load_json(run_dir / "receipt.json", f"{arm}/{family} run receipt")
    _require(
        receipt.get("status") == "complete"
        and receipt.get("mode") == "internal"
        and receipt.get("run_id") == run_dir.name
        and receipt.get("config_path")
        == Path(CONFIG_ORDER[CELL_ORDER.index((arm, family))]).name,
        f"{arm}/{family} run receipt differs",
    )
    _require(
        isinstance(receipt.get("run_seal"), str) and len(receipt["run_seal"]) == 16,
        f"{arm}/{family} run seal differs",
    )
    _require(
        run_dir.name.startswith(f"{RUN_NAMES[CELL_ORDER.index((arm, family))]}--"),
        f"{arm}/{family} run name differs",
    )
    plan = _load_json(run_dir / "plan.json", f"{arm}/{family} plan")
    summary = _load_json(run_dir / "summary.json", f"{arm}/{family} summary")
    resolved_inputs = _load_json(
        run_dir / "resolved_inputs.json", f"{arm}/{family} resolved inputs"
    )
    condition_count = CONDITION_COUNTS[arm]
    _require(
        plan.get("estimated_forward_calls") == EXPECTED_FORWARD_CALLS[arm]
        and summary.get("intervention_record_count") == EXPECTED_LEDGER_ROWS[arm]
        and len(resolved_inputs.get("panel", [])) == condition_count
        and len(resolved_inputs.get("target_ids", [])) == 24
        and len(resolved_inputs.get("wrapper_ids", [])) == 16,
        f"{arm}/{family} run count contract differs",
    )
    _require(
        analysis_input.get("panel_arm") == arm
        and analysis_input.get("role") == family
        and analysis_input.get("run_label") == run_dir.name,
        f"{arm}/{family} analysis input role binding differs",
    )
    inventory = analysis_input.get("complete_run_file_inventory")
    _require(
        isinstance(inventory, Mapping) and set(inventory) == RUN_ALL_FILES,
        f"{arm}/{family} analysis run inventory differs",
    )
    actual_hashes = {
        filename: _sha256(run_dir / filename) for filename in RUN_ALL_FILES
    }
    _require(
        dict(inventory) == actual_hashes, f"{arm}/{family} analysis run hashes differ"
    )
    log_path = (root / str(process.get("log_path"))).resolve()
    log_bytes = log_path.read_bytes()
    _require(
        str(run_dir.resolve()).encode("utf-8") in log_bytes
        and run_dir.name.encode("utf-8") in log_bytes,
        f"{arm}/{family} launcher log does not bind run",
    )

    included: list[dict[str, Any]] = []
    destination_dir = root / BUNDLE_ROOT / "runs" / arm / family
    if destination_dir.exists():
        _require(
            destination_dir.is_dir() and not destination_dir.is_symlink(),
            f"invalid public run directory: {destination_dir}",
        )
        observed = {path.name for path in destination_dir.iterdir()}
        _require(
            observed <= set(RUN_PUBLIC_FILES),
            f"unexpected public run member: {arm}/{family}",
        )
    for filename in RUN_PUBLIC_FILES:
        destination = destination_dir / filename
        _copy_exact(run_dir / filename, destination)
        included.append(_public_file_metadata(root, destination))
    omitted = [
        _omitted_file_metadata(
            run_dir / filename,
            run_label=run_dir.name,
            condition_count=condition_count,
            expected_ledger_rows=EXPECTED_LEDGER_ROWS[arm],
        )
        for filename in RUN_OMITTED_FILES
    ]
    _require(
        all(
            not os.path.lexists(destination_dir / filename)
            for filename in RUN_OMITTED_FILES
        ),
        f"large raw file leaked into public bundle: {arm}/{family}",
    )
    return included, omitted, receipt


def build_bundle(
    root: Path,
    *,
    run_dirs: Mapping[tuple[str, str], Path],
    analysis_dir: Path,
    preflight_path: Path | None = None,
    attempt_receipt_path: Path | None = None,
    execution_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Validate local evidence and publish one idempotent compact bundle."""

    root = root.resolve()
    _require(set(run_dirs) == set(CELL_ORDER), "ten run role bindings differ")
    resolved_runs = {key: Path(value).resolve() for key, value in run_dirs.items()}
    _require(
        len(set(resolved_runs.values())) == 10,
        "ten distinct run directories are required",
    )
    preflight_source = Path(preflight_path or (root / PREFLIGHT_PATH)).resolve()
    attempt_source = Path(
        attempt_receipt_path or (root / ATTEMPT_RECEIPT_PATH)
    ).resolve()
    execution_source = Path(
        execution_receipt_path or (root / EXECUTION_RECEIPT_PATH)
    ).resolve()
    analysis_source = Path(analysis_dir).resolve()

    freeze, freeze_sha, preflight = _validate_freeze_and_preflight(
        root, preflight_source
    )
    attempt, execution, launcher_logs = _validate_execution_chain(
        root,
        attempt_path=attempt_source,
        execution_path=execution_source,
        freeze_sha=freeze_sha,
        preflight_sha=_sha256(preflight_source),
        preflight=preflight,
    )
    _, analysis_receipt, _ = _validate_analysis(
        analysis_source,
        freeze_sha=freeze_sha,
        execution_sha=_sha256(execution_source),
    )
    analysis_inputs = analysis_receipt.get("input_runs")
    _require(
        isinstance(analysis_inputs, list) and len(analysis_inputs) == 10,
        "analysis input run grid differs",
    )
    expected_roles = list(CELL_ORDER)
    observed_roles = [
        (row.get("panel_arm"), row.get("role"))
        for row in analysis_inputs
        if isinstance(row, Mapping)
    ]
    _require(observed_roles == expected_roles, "analysis input run order differs")

    processes = execution["processes"]
    run_records: list[dict[str, Any]] = []
    public_paths: list[Path] = []
    omitted_records: list[dict[str, Any]] = []
    for index, (arm, family) in enumerate(CELL_ORDER):
        included, omitted, receipt = _validate_run_source(
            root,
            resolved_runs[(arm, family)],
            arm=arm,
            family=family,
            analysis_input=analysis_inputs[index],
            process=processes[index],
        )
        public_paths.extend(root / item["path"] for item in included)
        omitted_records.extend(omitted)
        run_records.append(
            {
                "panel_arm": arm,
                "family": family,
                "run_label": resolved_runs[(arm, family)].name,
                "run_seal": receipt["run_seal"],
                "public_directory": (BUNDLE_ROOT / "runs" / arm / family).as_posix(),
                "included_file_count": len(included),
                "included_files": included,
                "omitted_raw_file_count": len(omitted),
                "omitted_raw_files": omitted,
                "planned_forward_calls": EXPECTED_FORWARD_CALLS[arm],
                "intervention_row_count": EXPECTED_LEDGER_ROWS[arm],
            }
        )
    _require(
        sum(
            item["row_count"]
            for item in omitted_records
            if item["filename"] == "interventions.jsonl"
        )
        == EXPECTED_TOTAL_LEDGER_ROWS,
        "total omitted intervention ledger rows differ",
    )

    analysis_destination = root / BUNDLE_ROOT / "analysis"
    analysis_metadata: list[dict[str, Any]] = []
    for filename in ANALYSIS_FILES:
        destination = analysis_destination / filename
        _copy_exact(analysis_source / filename, destination)
        metadata = _public_file_metadata(root, destination)
        if filename in ANALYSIS_EXPECTED_ROWS:
            _require(
                metadata["row_count"] == ANALYSIS_EXPECTED_ROWS[filename],
                f"published analysis row count differs: {filename}",
            )
        public_paths.append(destination)
        analysis_metadata.append(metadata)

    _copy_exact(preflight_source, root / PREFLIGHT_PATH)
    _copy_exact(attempt_source, root / PUBLIC_ATTEMPT_RECEIPT_PATH)
    _copy_exact(execution_source, root / PUBLIC_EXECUTION_RECEIPT_PATH)
    preflight_metadata = _public_file_metadata(root, root / PREFLIGHT_PATH)
    attempt_metadata = _public_file_metadata(root, root / PUBLIC_ATTEMPT_RECEIPT_PATH)
    execution_metadata = _public_file_metadata(
        root, root / PUBLIC_EXECUTION_RECEIPT_PATH
    )
    public_paths.extend(
        [
            root / PREFLIGHT_PATH,
            root / PUBLIC_ATTEMPT_RECEIPT_PATH,
            root / PUBLIC_EXECUTION_RECEIPT_PATH,
        ]
    )

    documentation_metadata: list[dict[str, Any]] = []
    for relative in PUBLIC_README_PATHS:
        path = root / relative
        _require(
            _manifest_declared_hash(freeze, relative) == _sha256(path),
            f"freeze public README hash differs: {relative}",
        )
        metadata = _public_file_metadata(root, path)
        documentation_metadata.append(metadata)
        public_paths.append(path)

    findings = _scan_absolute_paths(public_paths)
    _require(
        not findings,
        f"absolute filesystem paths found in public evidence: {findings[:3]}",
    )
    all_public_metadata = [
        preflight_metadata,
        attempt_metadata,
        execution_metadata,
        *documentation_metadata,
        *analysis_metadata,
        *(item for run in run_records for item in run["included_files"]),
    ]
    public_jsonl = [item for item in all_public_metadata if item["format"] == "jsonl"]
    analysis_hashes = {
        Path(item["path"]).name: item["sha256"] for item in analysis_metadata
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "bundle_id": BUNDLE_ID,
        "protocol_id": PROTOCOL_ID,
        "status": "complete_validated_public_evidence",
        "scientific_outcome_interpreted_by_builder": False,
        "freeze": {
            "manifest_path": FREEZE_MANIFEST_PATH.as_posix(),
            "manifest_sha256": freeze_sha,
            "audited_commit": execution["audited_commit"],
            "execution_commit": execution["freeze_commit"],
            "prepared_before_model_forward": True,
        },
        "preflight": preflight_metadata,
        "execution": {
            "attempt_started_receipt": attempt_metadata,
            "success_execution_receipt": execution_metadata,
            "failed_execution_receipt_absent": True,
            "launcher_logs_publicly_omitted": launcher_logs,
        },
        "documentation": {
            "language_order": ["en", "ja"],
            "files": documentation_metadata,
            "file_count": 2,
        },
        "analysis": {
            "public_directory": (BUNDLE_ROOT / "analysis").as_posix(),
            "implementation_path": ANALYZER_PATH.as_posix(),
            "implementation_sha256": _sha256(root / ANALYZER_PATH),
            "files": analysis_metadata,
            "file_count": len(analysis_metadata),
            "expected_jsonl_rows": ANALYSIS_EXPECTED_ROWS,
            "output_sha256": analysis_hashes,
            "analysis_status_copied_without_interpretation": analysis_receipt["status"],
        },
        "runs": run_records,
        "absolute_path_scan": {
            "policy": "fail closed on home, temporary, volume, or drive-qualified filesystem paths; evidence bytes are unchanged",
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
            "verification_scope": "declaration only; protected banks are outside builder and validator input surfaces",
        },
        "inventory": {
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
            "public_member_file_count": len(all_public_metadata),
            "public_file_count_including_root_manifest": len(all_public_metadata) + 1,
            "public_member_total_bytes": sum(
                item["bytes"] for item in all_public_metadata
            ),
            "public_jsonl_file_count": len(public_jsonl),
            "public_jsonl_row_count": sum(item["row_count"] for item in public_jsonl),
            "omitted_raw_file_count": len(omitted_records),
            "omitted_raw_total_bytes": sum(item["bytes"] for item in omitted_records),
            "omitted_intervention_jsonl_rows": EXPECTED_TOTAL_LEDGER_ROWS,
            "omitted_launcher_log_file_count": len(launcher_logs),
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
        "root manifest would contain an absolute filesystem path",
    )
    _require(
        not any(path in serialized for path in EXCLUDED_CONTENT)
        or manifest["excluded_content_access"]["paths"] == list(EXCLUDED_CONTENT),
        "protected-bank declaration differs",
    )
    _atomic_write_json(root / ROOT_MANIFEST_PATH, manifest)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    for arm, family in CELL_ORDER:
        parser.add_argument(f"--{arm}-{family}-run", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--attempt-started-receipt", type=Path)
    parser.add_argument("--execution-receipt", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    run_dirs = {
        (arm, family): getattr(args, f"{arm}_{family}_run")
        for arm, family in CELL_ORDER
    }
    try:
        manifest = build_bundle(
            args.root,
            run_dirs=run_dirs,
            analysis_dir=args.analysis_dir,
            preflight_path=args.preflight,
            attempt_receipt_path=args.attempt_started_receipt,
            execution_receipt_path=args.execution_receipt,
        )
    except (
        BundleBuildError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(manifest["inventory"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
