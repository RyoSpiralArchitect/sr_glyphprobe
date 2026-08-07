#!/usr/bin/env python3
"""Run the corrected frozen Llama 3.2 3B MPS v2 grid sequentially.

The launcher reads no scientific output.  It requires the v2 contextual-
tokenizer preflight, starts ten independent GlyphProbe processes in the frozen
order, stops on the first non-zero exit, and publishes receipt-only execution
state.  Any interrupted or failed v2 attempt is terminal and may not resume.
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


PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2"
MODEL_ID = "mlx-community/Llama-3.2-3B-bf16"
MODEL_REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
MANIFEST_RELATIVE = Path("data/manifests/llama32_3b_mps_emoji_transport_v2.json")
PREFLIGHT_RELATIVE = Path(
    "artifacts/llama32_3b_mps_emoji_transport_v2/preflight/tokenization_audit_v2.json"
)
EXPECTED_AUDIT_ROLE = (
    "model_free_static_artifact_config_and_contextual_tokenizer_preflight"
)
EXPECTED_ENVIRONMENT = {
    "python_version": "3.13.13",
    "glyphprobe_version": "0.1.0",
    "numpy_version": "2.4.4",
    "torch_version": "2.11.0",
    "transformers_version": "4.57.6",
    "platform": "macOS-26.2-arm64-arm-64bit-Mach-O",
    "machine": "arm64",
    "torch_mps_built": True,
    "torch_mps_available": True,
}
EXPECTED_MODEL_ARTIFACT = {
    "model": MODEL_ID,
    "revision": MODEL_REVISION,
    "file_count": 9,
    "total_bytes": 6_434_705_789,
    "manifest_sha256": (
        "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
    ),
}
EXPECTED_ARCHITECTURE = {
    "config_class": "LlamaConfig",
    "num_hidden_layers": 28,
    "hidden_size": 3_072,
    "vocab_size": 128_256,
    "commit_hash": MODEL_REVISION,
    "auto_config_only": True,
}
EXECUTION_RECEIPT_RELATIVE = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/execution_receipt.json"
)
ATTEMPT_STARTED_RECEIPT_RELATIVE = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/attempt_started_receipt.json"
)
FAILED_EXECUTION_RECEIPT_RELATIVE = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/failed_execution_receipt.json"
)
LAUNCHER_LOG_RELATIVE = Path("runs/.e2-llama32-3b-mps-transport-v2-launcher-logs")
CONFIG_ORDER = tuple(
    f"configs/e2_llama32_3b_mps_{scope}_{family}_v2.yaml"
    for scope in ("full50", "core35")
    for family in ("sky", "food", "animals", "transport", "social")
)
RUN_NAMES = tuple(
    f"e2-llama32-3b-mps-{scope}-{family}-transport-v2"
    for scope in ("full50", "core35")
    for family in ("sky", "food", "animals", "transport", "social")
)
RESUME_POLICY = "forbidden_in_v2_new_versioned_freeze_required"


class ExecutionError(RuntimeError):
    """Raised when the frozen execution contract is not satisfied."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutionError(f"Cannot read JSON receipt: {path}") from exc
    if not isinstance(value, dict):
        raise ExecutionError(f"Expected JSON object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise ExecutionError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise ExecutionError(
            result.stderr.strip() or "git merge-base --is-ancestor failed"
        )
    return result.returncode == 0


def _require_mapping(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExecutionError(f"Preflight {description} is missing")
    return value


def _require_frozen_fields(
    section: dict[str, Any], expected: dict[str, Any], description: str
) -> None:
    for key, value in expected.items():
        if section.get(key) != value:
            raise ExecutionError(f"Preflight {description}.{key} differs")


def _validate_preflight(root: Path, preflight_path: Path) -> dict[str, Any]:
    preflight = _read_json(preflight_path)
    if (
        preflight.get("protocol_id") != PROTOCOL_ID
        or preflight.get("status") != "passed"
    ):
        raise ExecutionError("Frozen tokenizer/config preflight did not pass")
    if preflight.get("audit_role") != EXPECTED_AUDIT_ROLE:
        raise ExecutionError("Preflight contextual-tokenizer audit role differs")
    if preflight.get("v1_preflight_outcome") != "failed_before_any_model_forward":
        raise ExecutionError("Preflight v1 failure lineage differs")
    if preflight.get("v2_correction_scope") != "contextual_wrapper_token_profile_only":
        raise ExecutionError("Preflight v2 correction scope differs")
    if preflight.get("model_forward_count") != 0:
        raise ExecutionError("Preflight unexpectedly records a model forward")
    if preflight.get("language_model_loaded") is not False:
        raise ExecutionError("Preflight language-model load boundary differs")
    if preflight.get("scientific_outcomes_inspected") is not False:
        raise ExecutionError("Preflight scientific-outcome boundary differs")

    tokenization = _require_mapping(preflight.get("tokenization"), "tokenization")
    rules = _require_mapping(tokenization.get("rules"), "tokenization rules")
    for key in (
        "v1_raw_contract_preserved",
        "full50_exceptions_use_contextual_first_token_substitution",
        "wrapper_context_profiles_exactly_frozen",
        "wrapper_outside_tokens_identical",
        "wrapper_core_token_count_position_and_outside_isomorphic",
    ):
        if rules.get(key) is not True:
            raise ExecutionError(f"Preflight tokenization rule differs: {key}")
    if rules.get("contextual_first_token_distribution") != {"9468": 7, "11410": 9}:
        raise ExecutionError("Preflight contextual first-token distribution differs")

    audited_commit = preflight.get("audited_commit")
    if not (
        isinstance(audited_commit, str)
        and len(audited_commit) == 40
        and all(char in "0123456789abcdef" for char in audited_commit.lower())
    ):
        raise ExecutionError("Preflight audited_commit is invalid")
    git_authority = _require_mapping(preflight.get("git_authority"), "git authority")
    if (
        git_authority.get("audited_commit") != audited_commit
        or git_authority.get("origin_main_commit") != audited_commit
        or git_authority.get("branch") != "main"
        or git_authority.get("worktree_clean_before_publication") is not True
    ):
        raise ExecutionError("Preflight git authority differs")

    authorization = _require_mapping(preflight.get("authorization"), "authorization")
    if authorization.get("frozen_grid_execution_authorized") is not True:
        raise ExecutionError("Preflight does not authorize the frozen grid")

    static = _require_mapping(preflight.get("static"), "static authority")
    manifest = _require_mapping(static.get("manifest"), "manifest binding")
    if manifest.get("present") is not True:
        raise ExecutionError("Preflight manifest was not verified")
    if manifest.get("path") != MANIFEST_RELATIVE.as_posix():
        raise ExecutionError("Preflight manifest path differs")
    manifest_path = root / MANIFEST_RELATIVE
    if not manifest_path.is_file():
        raise ExecutionError(f"Frozen manifest is missing: {MANIFEST_RELATIVE}")
    if manifest_path.is_symlink():
        raise ExecutionError("Frozen manifest must not be a symlink")
    if manifest.get("sha256") != _sha256(manifest_path):
        raise ExecutionError("Preflight manifest SHA-256 differs from current file")

    environment = _require_mapping(preflight.get("environment"), "environment")
    model_artifact = _require_mapping(preflight.get("model_artifact"), "model artifact")
    architecture = _require_mapping(preflight.get("architecture"), "architecture")
    _require_frozen_fields(environment, EXPECTED_ENVIRONMENT, "environment")
    _require_frozen_fields(model_artifact, EXPECTED_MODEL_ARTIFACT, "model_artifact")
    _require_frozen_fields(architecture, EXPECTED_ARCHITECTURE, "architecture")
    return preflight


def _validate_git_freeze(root: Path, preflight: dict[str, Any]) -> dict[str, str]:
    if _git(root, "status", "--porcelain"):
        raise ExecutionError(
            "Scientific execution requires a clean public-freeze worktree"
        )
    branch = _git(root, "branch", "--show-current")
    if branch != "main":
        raise ExecutionError(f"Scientific execution requires main, observed {branch!r}")
    head = _git(root, "rev-parse", "HEAD")
    origin_commit = _git(root, "rev-parse", "origin/main")
    if head != origin_commit:
        raise ExecutionError("HEAD must equal origin/main before scientific execution")
    audited_commit = str(preflight["audited_commit"])
    if not _git_is_ancestor(root, audited_commit, head):
        raise ExecutionError("Preflight audited_commit is not an ancestor of HEAD")
    changed = {
        line.strip()
        for line in _git(
            root, "diff", "--name-only", f"{audited_commit}..{head}"
        ).splitlines()
        if line.strip()
    }
    if changed != {PREFLIGHT_RELATIVE.as_posix()}:
        raise ExecutionError(
            "Only the frozen v2 preflight receipt may change after audited_commit"
        )
    return {
        "audited_commit": audited_commit,
        "execution_commit": head,
        "origin_main_commit": origin_commit,
        "branch": branch,
    }


def _require_empty_run_namespaces(root: Path) -> dict[str, Any]:
    runs_root = root / "runs"
    collisions: dict[str, list[str]] = {}
    for run_name in RUN_NAMES:
        matches = sorted(runs_root.glob(f"{run_name}--*")) if runs_root.exists() else []
        if matches:
            collisions[run_name] = [path.name for path in matches]
    if collisions:
        joined = ", ".join(
            f"{name}: {values}" for name, values in sorted(collisions.items())
        )
        raise ExecutionError(f"Frozen run destination already exists: {joined}")
    log_dir = root / LAUNCHER_LOG_RELATIVE
    if log_dir.exists():
        raise ExecutionError(f"Launcher log namespace already exists: {log_dir}")
    return {
        "resume_allowed": False,
        "run_name_count": len(RUN_NAMES),
        "existing_run_destination_count": 0,
        "launcher_log_namespace_preexisting": False,
    }


def _atomic_no_overwrite(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ExecutionError(f"Refusing to overwrite execution receipt: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        os.unlink(temporary)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def execute(
    *, root: Path, preflight_path: Path, receipt_path: Path, python: str
) -> dict[str, Any]:
    root = root.resolve()
    preflight_path = preflight_path.resolve()
    receipt_path = receipt_path.resolve()
    expected_receipt = (root / EXECUTION_RECEIPT_RELATIVE).resolve()
    if receipt_path != expected_receipt:
        raise ExecutionError(f"Execution receipt path differs: {receipt_path}")
    attempt_path = (root / ATTEMPT_STARTED_RECEIPT_RELATIVE).resolve()
    failed_path = (root / FAILED_EXECUTION_RECEIPT_RELATIVE).resolve()
    for description, path in (
        ("execution", receipt_path),
        ("attempt-started", attempt_path),
        ("failed-execution", failed_path),
    ):
        if path.exists():
            raise ExecutionError(f"{description} receipt already exists: {path}")

    preflight = _validate_preflight(root, preflight_path)
    expected_preflight = (root / PREFLIGHT_RELATIVE).resolve()
    if preflight_path != expected_preflight:
        raise ExecutionError(f"Preflight path differs: {preflight_path}")
    git_freeze = _validate_git_freeze(root, preflight)
    namespace = _require_empty_run_namespaces(root)
    for relative in CONFIG_ORDER:
        if not (root / relative).is_file():
            raise ExecutionError(f"Missing frozen config: {relative}")

    environment = os.environ.copy()
    environment["HF_HUB_OFFLINE"] = "1"
    environment["TRANSFORMERS_OFFLINE"] = "1"
    source_path = str(root / "src")
    prior_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{source_path}{os.pathsep}{prior_pythonpath}"
        if prior_pythonpath
        else source_path
    )
    log_dir = root / LAUNCHER_LOG_RELATIVE
    log_dir.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    manifest_path = root / MANIFEST_RELATIVE
    start_payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "attempt_started_no_process_launched",
        "scientific_outcomes_inspected_by_launcher": False,
        "model_process_count_at_publication": 0,
        "started_at": started,
        "git_freeze": git_freeze,
        "preflight": {
            "path": PREFLIGHT_RELATIVE.as_posix(),
            "sha256": _sha256(preflight_path),
        },
        "manifest": {
            "path": MANIFEST_RELATIVE.as_posix(),
            "sha256": _sha256(manifest_path),
        },
        "config_order": list(CONFIG_ORDER),
        "run_names": list(RUN_NAMES),
        "initial_namespace_check": namespace,
        "launcher_log_namespace": LAUNCHER_LOG_RELATIVE.as_posix(),
        "resume_policy": RESUME_POLICY,
    }
    _atomic_no_overwrite(attempt_path, start_payload)
    attempt_binding = {
        "path": ATTEMPT_STARTED_RECEIPT_RELATIVE.as_posix(),
        "sha256": _sha256(attempt_path),
    }
    processes: list[dict[str, Any]] = []
    active_cell: dict[str, Any] | None = None
    failure_published = False

    def publish_failure(status: str, failure: dict[str, Any]) -> None:
        nonlocal failure_published
        payload = {
            "schema_version": 1,
            "protocol_id": PROTOCOL_ID,
            "status": status,
            "scientific_outcomes_inspected_by_launcher": False,
            "analysis_authorized": False,
            "success_execution_receipt_written": False,
            "attempt_started_receipt": attempt_binding,
            "started_at": started,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "git_freeze": git_freeze,
            "resume_policy": RESUME_POLICY,
            "processes": processes,
            "recorded_process_count": len(processes),
            "successful_process_count": sum(
                row.get("return_code") == 0 for row in processes
            ),
            "expected_process_count": len(CONFIG_ORDER),
            "failure": failure,
        }
        _atomic_no_overwrite(failed_path, payload)
        failure_published = True

    def active_failure(kind: str, error: BaseException) -> dict[str, Any]:
        failure: dict[str, Any] = {
            "kind": kind,
            "error_type": type(error).__name__,
            "error": repr(error),
            "active_cell": active_cell,
        }
        if active_cell is not None:
            partial_log = root / str(active_cell["log_path"])
            if partial_log.is_file():
                failure["partial_log_sha256"] = _sha256(partial_log)
                failure["partial_log_bytes"] = partial_log.stat().st_size
        return failure

    try:
        for index, relative in enumerate(CONFIG_ORDER):
            config_path = root / relative
            if not config_path.is_file():
                raise ExecutionError(f"Missing frozen config: {relative}")
            command = [python, "-m", "glyphprobe", "run", "-c", str(config_path)]
            print(f"[{index + 1}/{len(CONFIG_ORDER)}] {relative}", flush=True)
            cell_started = datetime.now(timezone.utc).isoformat()
            log_path = log_dir / f"{index:02d}-{config_path.stem}.log"
            active_cell = {
                "index": index,
                "config": relative,
                "started_at": cell_started,
                "log_path": log_path.relative_to(root).as_posix(),
            }
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
                **active_cell,
                "config_sha256": _sha256(config_path),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "return_code": result.returncode,
                "log_sha256": _sha256(log_path),
            }
            processes.append(record)
            active_cell = None
            if result.returncode != 0:
                publish_failure("execution_incomplete_process_failure", record)
                raise ExecutionError(
                    f"Frozen run failed at {relative} with return code {result.returncode}"
                )
    except KeyboardInterrupt as exc:
        publish_failure(
            "execution_incomplete_keyboard_interrupt",
            active_failure("keyboard_interrupt", exc),
        )
        raise ExecutionError("Frozen run interrupted; v2 may not resume") from exc
    except Exception as exc:
        if not failure_published:
            publish_failure(
                "execution_incomplete_launcher_exception",
                active_failure("launcher_exception", exc),
            )
        if isinstance(exc, ExecutionError):
            raise
        raise ExecutionError("Frozen launcher failed; v2 may not resume") from exc

    if failed_path.exists():
        raise ExecutionError(
            "Failed-execution receipt exists; success publication is forbidden"
        )
    payload = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "execution_complete_analysis_not_run",
        "scientific_outcomes_inspected_by_launcher": False,
        "freeze_commit": git_freeze["execution_commit"],
        "audited_commit": git_freeze["audited_commit"],
        "branch": git_freeze["branch"],
        "attempt_started_receipt": attempt_binding,
        "preflight_path": PREFLIGHT_RELATIVE.as_posix(),
        "preflight_sha256": _sha256(preflight_path),
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "process_isolation": "strictly_sequential_independent_python_processes",
        "simultaneous_full_model_residency": False,
        "resume_policy": RESUME_POLICY,
        "initial_namespace_check": namespace,
        "processes": processes,
        "completed_process_count": len(processes),
        "expected_process_count": len(CONFIG_ORDER),
        "analysis_authorized": True,
        "failed_execution_receipt_written": False,
    }
    try:
        _atomic_no_overwrite(receipt_path, payload)
    except Exception as exc:
        if not failure_published:
            publish_failure(
                "execution_complete_success_receipt_publication_failed",
                active_failure("success_receipt_publication_failure", exc),
            )
        if isinstance(exc, ExecutionError):
            raise
        raise ExecutionError("Success receipt publication failed") from exc
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--python", default=sys.executable)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repo_root.resolve()
    preflight = args.preflight or (root / PREFLIGHT_RELATIVE)
    receipt = args.receipt or (root / EXECUTION_RECEIPT_RELATIVE)
    try:
        payload = execute(
            root=root,
            preflight_path=preflight,
            receipt_path=receipt,
            python=args.python,
        )
    except ExecutionError as exc:
        print(f"execution_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
