#!/usr/bin/env python3
"""Run the frozen four-panel Llama 3.2 3B Instruct M2 bridge v0.

The launcher validates the public tokenizer-only preflight, clean Git authority,
and the exact local model artifact, creates a fixed non-user-specific runtime
alias, then runs four isolated GlyphProbe processes sequentially. It never reads
scientific outputs. A failure or interruption retires v0; resume is forbidden.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "glyphprobe-llama32-3b-instruct-mps-m2-bridge-v0"
MODEL_ALIAS = Path("/private/tmp/glyphprobe-llama32-3b-instruct-v0")
MODEL_MANIFEST_SHA256 = "c698f962b8587e2c38dcb86e344928aa5db3c7386e160230d493fcaf9166ecf6"
STATIC_MANIFEST = Path("data/manifests/llama32_3b_instruct_mps_m2_bridge_v0.json")
PREFLIGHT = Path("validation/llama32_3b_instruct_mps_m2_bridge_v0/preflight.json")
ATTEMPT_RECEIPT = Path("validation/llama32_3b_instruct_mps_m2_bridge_v0/attempt_started.json")
EXECUTION_RECEIPT = Path("validation/llama32_3b_instruct_mps_m2_bridge_v0/execution.json")
FAILURE_RECEIPT = Path("validation/llama32_3b_instruct_mps_m2_bridge_v0/failure.json")
LOG_ROOT = Path("runs/.llama32-3b-instruct-mps-m2-bridge-v0-logs")
CONFIG_ORDER = (
    Path("configs/llama32_3b_instruct_mps_m2_primary_v0.yaml"),
    Path("configs/llama32_3b_instruct_mps_m2_null_a_v0.yaml"),
    Path("configs/llama32_3b_instruct_mps_m2_null_b_v0.yaml"),
    Path("configs/llama32_3b_instruct_mps_m2_null_c_v0.yaml"),
)
RUN_NAMES = (
    "llama32-3b-instruct-mps-m2-primary-v0",
    "llama32-3b-instruct-mps-m2-null-a-v0",
    "llama32-3b-instruct-mps-m2-null-b-v0",
    "llama32-3b-instruct-mps-m2-null-c-v0",
)


class ExecutionError(RuntimeError):
    """Raised when frozen execution cannot proceed exactly."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _model_artifact(path: Path) -> dict[str, Any]:
    path = path.resolve()
    _require(path.is_dir(), "Model artifact path is not a directory")
    files: dict[str, dict[str, Any]] = {}
    total = 0
    for candidate in sorted(value for value in path.rglob("*") if value.is_file()):
        _require(not candidate.is_symlink(), f"Model file must not be a symlink: {candidate.name}")
        size = candidate.stat().st_size
        total += size
        files[candidate.relative_to(path).as_posix()] = {
            "bytes": size,
            "sha256": _sha256_file(candidate),
        }
    _require(files, "Model artifact contains no files")
    return {
        "file_count": len(files),
        "total_bytes": total,
        "manifest_sha256": _stable_hash(files),
        "files": files,
    }


def _read_json(path: Path) -> dict[str, Any]:
    _require(path.is_file() and not path.is_symlink(), f"Missing JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ExecutionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    _require(result.returncode in (0, 1), "git merge-base failed")
    return result.returncode == 0


def _validate_git(root: Path, preflight: dict[str, Any]) -> dict[str, str]:
    _require(not _git(root, "status", "--porcelain"), "Execution worktree must be clean")
    branch = _git(root, "branch", "--show-current")
    _require(branch == "main", f"Execution requires main, observed {branch!r}")
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    _require(head == origin, "HEAD must equal origin/main")
    audited = str(preflight["git_authority"]["audited_commit"])
    _require(_git_is_ancestor(root, audited, head), "Audited commit is not an ancestor")
    changed = {
        row.strip()
        for row in _git(root, "diff", "--name-only", f"{audited}..{head}").splitlines()
        if row.strip()
    }
    _require(changed == {PREFLIGHT.as_posix()}, "Only the preflight receipt may follow the audited commit")
    return {
        "audited_commit": audited,
        "execution_commit": head,
        "origin_main_commit": origin,
        "branch": branch,
    }


def _validate_preflight(root: Path) -> dict[str, Any]:
    preflight_path = root / PREFLIGHT
    receipt = _read_json(preflight_path)
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Preflight protocol differs")
    _require(receipt.get("status") == "passed", "Preflight did not pass")
    _require(receipt.get("authorization", {}).get("frozen_grid_execution_authorized") is True, "Preflight does not authorize execution")
    _require(receipt.get("claim_boundary", {}).get("model_forward_count") == 0, "Preflight records a model forward")
    _require(receipt.get("claim_boundary", {}).get("scientific_outcomes_inspected") is False, "Preflight outcome boundary differs")
    _require(receipt.get("claim_boundary", {}).get("protected_p2_or_c1_accessed") is False, "Preflight protected-bank boundary differs")
    manifest_path = root / STATIC_MANIFEST
    _require(receipt.get("static_manifest", {}).get("sha256") == _sha256_file(manifest_path), "Static manifest binding differs")
    return receipt


def _validate_namespaces(root: Path) -> None:
    for relative in (ATTEMPT_RECEIPT, EXECUTION_RECEIPT, FAILURE_RECEIPT, LOG_ROOT):
        _require(not (root / relative).exists(), f"Frozen namespace already exists: {relative}")
    runs_root = root / "runs"
    for name in RUN_NAMES:
        matches = list(runs_root.glob(f"{name}--*")) if runs_root.exists() else []
        _require(not matches, f"Run namespace already exists for {name}")


def _ensure_model_alias(model_path: Path) -> dict[str, Any]:
    model_path = model_path.resolve()
    artifact = _model_artifact(model_path)
    _require(artifact["manifest_sha256"] == MODEL_MANIFEST_SHA256, "Model artifact manifest differs")
    if os.path.lexists(MODEL_ALIAS):
        _require(MODEL_ALIAS.is_symlink(), f"Model alias exists and is not a symlink: {MODEL_ALIAS}")
        _require(MODEL_ALIAS.resolve() == model_path, "Model alias points to another artifact")
        created = False
    else:
        MODEL_ALIAS.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(model_path, MODEL_ALIAS, target_is_directory=True)
        created = True
    alias_artifact = _model_artifact(MODEL_ALIAS)
    _require(alias_artifact == artifact, "Model alias artifact differs")
    return {
        "model_path_recorded": False,
        "runtime_alias": str(MODEL_ALIAS),
        "alias_created_by_launcher": created,
        "artifact": artifact,
    }


def _atomic_write_no_overwrite(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.exists(), f"Refusing to overwrite receipt: {path}")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def execute(root: Path, model_path: Path, python: str) -> dict[str, Any]:
    root = root.resolve()
    _require(root.is_dir(), "Repository root is missing")
    preflight = _validate_preflight(root)
    git_authority = _validate_git(root, preflight)
    _validate_namespaces(root)
    for config in CONFIG_ORDER:
        _require((root / config).is_file(), f"Missing config: {config}")
    model = _ensure_model_alias(model_path)

    started = datetime.now(timezone.utc).isoformat()
    log_root = root / LOG_ROOT
    log_root.mkdir(parents=True, exist_ok=False)
    attempt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "attempt_started_no_model_process_launched",
        "started_at": started,
        "git_authority": git_authority,
        "preflight": {"path": PREFLIGHT.as_posix(), "sha256": _sha256_file(root / PREFLIGHT)},
        "static_manifest": {"path": STATIC_MANIFEST.as_posix(), "sha256": _sha256_file(root / STATIC_MANIFEST)},
        "model": model,
        "config_order": [path.as_posix() for path in CONFIG_ORDER],
        "run_names": list(RUN_NAMES),
        "model_process_count": 0,
        "scientific_outcomes_inspected_by_launcher": False,
        "resume_policy": "forbidden_new_versioned_freeze_required",
        "operational_context": {
            "concurrent_chatgpt_gui_allowed": True,
            "speed_claim_authorized": False,
            "load_average_at_start": list(os.getloadavg()),
        },
    }
    _atomic_write_no_overwrite(root / ATTEMPT_RECEIPT, attempt)
    attempt_binding = {"path": ATTEMPT_RECEIPT.as_posix(), "sha256": _sha256_file(root / ATTEMPT_RECEIPT)}

    environment = os.environ.copy()
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_ENABLE_MPS_FALLBACK": "0",
        }
    )
    source_root = str(root / "src")
    prior_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{source_root}{os.pathsep}{prior_pythonpath}" if prior_pythonpath else source_root
    )
    processes: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None

    def publish_failure(status: str, failure: dict[str, Any]) -> None:
        if (root / FAILURE_RECEIPT).exists():
            return
        _atomic_write_no_overwrite(
            root / FAILURE_RECEIPT,
            {
                "schema_version": 1,
                "protocol_id": PROTOCOL_ID,
                "status": status,
                "analysis_authorized": False,
                "resume_policy": "forbidden_new_versioned_freeze_required",
                "scientific_outcomes_inspected_by_launcher": False,
                "attempt": attempt_binding,
                "started_at": started,
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "processes": processes,
                "failure": failure,
            },
        )

    try:
        for index, config in enumerate(CONFIG_ORDER):
            log_path = log_root / f"{index:02d}-{config.stem}.log"
            active = {
                "index": index,
                "config": config.as_posix(),
                "config_sha256": _sha256_file(root / config),
                "log_path": log_path.relative_to(root).as_posix(),
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"[{index + 1}/{len(CONFIG_ORDER)}] {config}", flush=True)
            command = [python, "-m", "glyphprobe", "run", "-c", str(root / config)]
            with log_path.open("xb") as log_handle:
                result = subprocess.run(
                    command,
                    cwd=root,
                    env=environment,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            record = {
                **active,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "return_code": result.returncode,
                "log_sha256": _sha256_file(log_path),
                "log_bytes": log_path.stat().st_size,
            }
            processes.append(record)
            active = None
            if result.returncode != 0:
                publish_failure("execution_incomplete_process_failure", record)
                raise ExecutionError(f"Process failed for {config} with code {result.returncode}")
    except KeyboardInterrupt as exc:
        publish_failure(
            "execution_incomplete_keyboard_interrupt",
            {"error_type": type(exc).__name__, "active": active},
        )
        raise ExecutionError("Execution interrupted; v0 may not resume") from exc
    except Exception as exc:
        if not (root / FAILURE_RECEIPT).exists():
            publish_failure(
                "execution_incomplete_launcher_exception",
                {"error_type": type(exc).__name__, "error": repr(exc), "active": active},
            )
        if isinstance(exc, ExecutionError):
            raise
        raise ExecutionError("Launcher failed; v0 may not resume") from exc

    _require(not (root / FAILURE_RECEIPT).exists(), "Failure receipt blocks success")
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "execution_complete_analysis_not_run",
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "git_authority": git_authority,
        "attempt": attempt_binding,
        "model_artifact_manifest_sha256": MODEL_MANIFEST_SHA256,
        "model_path_recorded": False,
        "process_isolation": "four_strictly_sequential_python_processes",
        "simultaneous_full_model_residency": False,
        "completed_process_count": len(processes),
        "expected_process_count": len(CONFIG_ORDER),
        "processes": processes,
        "scientific_outcomes_inspected_by_launcher": False,
        "analysis_authorized": True,
        "speed_claim_authorized": False,
        "resume_policy": "forbidden_new_versioned_freeze_required",
    }
    _atomic_write_no_overwrite(root / EXECUTION_RECEIPT, receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = execute(args.repo_root, args.model_path, args.python)
    except (ExecutionError, OSError, ValueError) as exc:
        print(f"execution_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "status": receipt["status"],
                "completed_process_count": receipt["completed_process_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
