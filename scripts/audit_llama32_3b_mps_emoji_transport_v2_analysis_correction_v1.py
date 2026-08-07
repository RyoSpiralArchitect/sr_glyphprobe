#!/usr/bin/env python3
"""Publish the model-free preflight for v2 analysis correction v1.

The audit verifies the clean pushed Git state, the additive manifest and its
exact frozen upstream hashes, all ten execution-receipt-bound launcher logs,
and the exact Rich two-fragment completion-path presentation.  It does not
open run files, result rows, target content, model weights, or tokenizers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any


HELPER_PATH = Path(
    "scripts/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
)
HELPER_SHA256 = "4cf3d5d78ba32120df93c1ba0a0f66c985016c84e5b71c9c1df81148590d22ca"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _import_helper(path: Path) -> ModuleType:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Correction helper is missing or a symlink: {path}")
    if _sha256(path) != HELPER_SHA256:
        raise RuntimeError("Frozen correction helper hash differs")
    spec = importlib.util.spec_from_file_location(
        "glyphprobe_llama32_3b_mps_emoji_transport_v2_correction_v1_audit_helper",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import the frozen correction helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
correction = _import_helper(_SOURCE_ROOT / HELPER_PATH)
AnalysisCorrectionError = correction.AnalysisCorrectionError


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisCorrectionError(message)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AnalysisCorrectionError(
            result.stderr.strip() or f"git {' '.join(args)} failed"
        )
    return result.stdout.strip()


def collect_git_authority(root: Path) -> dict[str, Any]:
    """Require one clean, pushed main commit before preflight publication."""

    resolved_root = Path(root).resolve()
    _require(
        not _git(resolved_root, "status", "--porcelain"),
        "Audit requires a clean worktree",
    )
    branch = _git(resolved_root, "branch", "--show-current")
    _require(branch == "main", f"Audit requires main, observed {branch!r}")
    head = _git(resolved_root, "rev-parse", "HEAD")
    origin = _git(resolved_root, "rev-parse", "origin/main")
    _require(head == origin, "Audit HEAD must equal origin/main")
    _require(
        correction.COMMIT_40.fullmatch(head) is not None,
        "Audit commit must be a full SHA-1",
    )
    return {
        "audited_commit": head,
        "branch": branch,
        "origin_main_commit": origin,
        "worktree_clean_before_publication": True,
    }


def _safe_repo_path(root: Path, value: Any, description: str) -> tuple[Path, Path]:
    _require(isinstance(value, str) and value, f"Missing path: {description}")
    relative = Path(value)
    _require(
        not relative.is_absolute()
        and ".." not in relative.parts
        and relative.as_posix() == value,
        f"Unsafe path: {description}",
    )
    unresolved = root / relative
    _require(not unresolved.is_symlink(), f"Symlink forbidden: {description}")
    resolved = unresolved.resolve()
    _require(resolved.is_relative_to(root), f"Path escapes repository: {description}")
    return relative, resolved


def _completion_records(
    root: Path, manifest: Mapping[str, Any]
) -> list[dict[str, Any]]:
    rows = manifest.get("launcher_logs")
    _require(isinstance(rows, list) and len(rows) == 10, "Expected ten launcher logs")
    records: list[dict[str, Any]] = []
    seen_logs: set[Path] = set()
    seen_runs: set[Path] = set()
    seen_run_ids: set[str] = set()
    for index, row in enumerate(rows):
        _require(isinstance(row, Mapping), f"Invalid launcher-log row: {index}")
        log_relative, log_path = _safe_repo_path(
            root, row.get("path"), f"launcher_logs[{index}].path"
        )
        run_relative, run_path = _safe_repo_path(
            root,
            row.get("expected_run_relative_path"),
            f"launcher_logs[{index}].expected_run_relative_path",
        )
        run_id = row.get("expected_run_id")
        _require(
            log_path.is_file() and not log_path.is_symlink(),
            f"Launcher log is missing: {log_relative}",
        )
        _require(
            run_path.is_dir() and not run_path.is_symlink(),
            f"Expected run directory is missing: {run_relative}",
        )
        _require(
            isinstance(run_id, str) and run_id == run_path.name,
            f"Run ID/path binding differs: {index}",
        )
        log_payload = log_path.read_bytes()
        _require(
            isinstance(row.get("sha256"), str)
            and hashlib.sha256(log_payload).hexdigest() == row["sha256"],
            f"Launcher log hash differs: {index}",
        )
        _require(log_path not in seen_logs, f"Duplicate launcher log: {index}")
        _require(run_path not in seen_runs, f"Duplicate expected run path: {index}")
        _require(run_id not in seen_run_ids, f"Duplicate expected run ID: {index}")
        seen_logs.add(log_path)
        seen_runs.add(run_path)
        seen_run_ids.add(run_id)
        parsed = correction.parse_completion_wrap(
            log_payload,
            expected_run_dir=run_path,
            expected_run_id=run_id,
        )
        records.append(
            {
                "index": index,
                "panel_arm": row.get("panel_arm"),
                "role": row.get("role"),
                "log_path": log_relative.as_posix(),
                "log_sha256": row.get("sha256"),
                "expected_run_relative_path": run_relative.as_posix(),
                "expected_run_id": run_id,
                **parsed,
            }
        )
    _require(
        len(seen_logs) == len(seen_runs) == len(seen_run_ids) == 10,
        "Completion-record identities are not unique",
    )
    return records


def build_preflight(
    root: Path,
    *,
    git_authority: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate science-free evidence and assemble the exact receipt payload."""

    resolved_root = Path(root).resolve()
    manifest = correction.validate_correction_manifest(resolved_root)
    analysis_output = resolved_root / correction.ANALYSIS_OUTPUT_DIR
    _require(
        not os.path.lexists(analysis_output),
        "Corrected analysis output already exists; preflight is no longer admissible",
    )
    authority = (
        collect_git_authority(resolved_root)
        if git_authority is None
        else dict(git_authority)
    )
    records = _completion_records(resolved_root, manifest)
    report = {
        "schema_version": 1,
        "correction_id": correction.CORRECTION_ID,
        "base_protocol_id": correction.BASE_PROTOCOL_ID,
        "status": "passed",
        "audit_role": (
            "model_free_post_execution_pre_endpoint_log_presentation_correction"
        ),
        "manifest": {
            "path": correction.CORRECTION_MANIFEST_PATH.as_posix(),
            "sha256": _sha256(resolved_root / correction.CORRECTION_MANIFEST_PATH),
        },
        "upstream_execution_receipt": manifest["upstream"]["v2_execution_receipt"],
        "git_authority": authority,
        "legacy_analyzer_attempts": {
            "evidence_class": "operator_attested_incident_record",
            "failed_invocation_artifacts_cryptographically_bound": False,
            "count": 2,
            "run_arrays_loaded_and_validated": True,
            "stopped_before_endpoint_construction": True,
            "stopped_before_bootstrap": True,
            "analysis_output_directory_created": False,
            "human_result_values_observed": False,
            "error": "Launcher log does not bind supplied run for full50/sky",
        },
        "process_boundary": {
            "model_forward_count": 0,
            "tokenizer_call_count": 0,
            "run_arrays_loaded_by_preflight": False,
            "endpoint_or_bootstrap_computed_by_preflight": False,
            "scientific_result_rows_read_by_preflight": False,
            "protected_bank_content_accessed": False,
            "source_logs_changed": False,
            "run_artifacts_changed": False,
        },
        "completion_records": records,
        "summary": {
            "expected_record_count": 10,
            "accepted_record_count": len(records),
            "ambiguous_record_count": 0,
            "raw_contiguous_path_match_count": 0,
            "raw_contiguous_run_id_match_count": 0,
            "completion_parser_contract": correction.PARSER_CONTRACT,
            "analysis_output_absent": True,
        },
        "authorization": {
            "corrected_analysis_authorized": True,
            "corrected_bundle_publication_authorized_after_analysis": True,
            "scientific_claim_strength_increased": False,
        },
    }
    return manifest, report


def atomic_no_overwrite(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically publish canonical JSON while refusing an existing target."""

    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as exc:
            raise AnalysisCorrectionError(
                f"Refusing to overwrite correction preflight: {destination}"
            ) from exc
        os.unlink(temporary)
        try:
            directory = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def audit_and_publish(root: Path) -> dict[str, Any]:
    """Build, atomically publish, and independently revalidate the preflight."""

    resolved_root = Path(root).resolve()
    manifest, report = build_preflight(resolved_root)
    output = resolved_root / correction.CORRECTION_PREFLIGHT_PATH
    atomic_no_overwrite(output, report)
    correction.validate_correction_preflight(resolved_root, manifest)
    return report


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = audit_and_publish(args.repo_root)
    except (AnalysisCorrectionError, OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
