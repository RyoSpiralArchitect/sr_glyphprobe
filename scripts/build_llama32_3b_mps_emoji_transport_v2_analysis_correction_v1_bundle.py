#!/usr/bin/env python3
"""Build the v2 bundle through the post-execution analysis correction v1.

The frozen v2 builder remains the publication implementation.  This adapter
only supplies a validated, temporary canonical view of Rich's one wrapped
``Complete`` launcher line to the v2 run-source validator and adds explicit
correction provenance to the root manifest.  Source logs and run evidence are
never rewritten.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any


CORRECTION_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2-analysis-correction-v1"
CORRECTION_MANIFEST_PATH = Path(
    "data/manifests/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.json"
)
CORRECTION_PREFLIGHT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/analysis_correction_v1_preflight.json"
)
HELPER_PATH = Path(
    "scripts/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
)
ANALYZER_ADAPTER_PATH = Path(
    "scripts/analyze_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
)
BUILDER_ADAPTER_PATH = Path(
    "scripts/build_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py"
)
VALIDATOR_ADAPTER_PATH = Path(
    "scripts/validate_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py"
)
BASE_BUILDER_PATH = Path("scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py")
BASE_VALIDATOR_PATH = Path(
    "scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py"
)
BASE_BUILDER_SHA256 = "c9074fa540e232cd595dd4a6ad4fa272c1580324d47b352481e3142453bf83a0"
BASE_VALIDATOR_SHA256 = (
    "b6e2948ca0cd0b445df182e5fdf64bd441df4953dc9399eeeb9c573cd659c127"
)
HELPER_SHA256 = "4cf3d5d78ba32120df93c1ba0a0f66c985016c84e5b71c9c1df81148590d22ca"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _import_exact(relative: Path, sha256: str, module_name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / relative
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Frozen dependency is missing or is a symlink: {relative}")
    if _sha256(path) != sha256:
        raise RuntimeError(f"Frozen dependency hash differs: {relative}")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import frozen dependency: {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


base = _import_exact(
    BASE_BUILDER_PATH,
    BASE_BUILDER_SHA256,
    "glyphprobe_frozen_llama32_3b_mps_transport_v2_bundle_builder",
)
correction = _import_exact(
    HELPER_PATH,
    HELPER_SHA256,
    "glyphprobe_frozen_llama32_3b_mps_transport_v2_analysis_correction_v1",
)

BundleBuildError = base.BundleBuildError
CELL_ORDER = base.CELL_ORDER
PROTOCOL_ID = base.PROTOCOL_ID
BUNDLE_ID = base.BUNDLE_ID
BUNDLE_ROOT = base.BUNDLE_ROOT
ROOT_MANIFEST_PATH = base.ROOT_MANIFEST_PATH
ANALYSIS_RECEIPT_FILENAME = "llama32_3b_mps_emoji_transport_v2_receipt.json"
ROOT_CORRECTION_KEY = "post_execution_analysis_validation_correction"
RECEIPT_CORRECTION_KEY = "analysis_validation_correction"
_ORIGINAL_VALIDATE_RUN_SOURCE = base._validate_run_source
_ORIGINAL_ATOMIC_WRITE_JSON = base._atomic_write_json


def _assert_correction_contract() -> None:
    expected = {
        "CORRECTION_ID": CORRECTION_ID,
        "CORRECTION_MANIFEST_PATH": CORRECTION_MANIFEST_PATH,
        "CORRECTION_PREFLIGHT_PATH": CORRECTION_PREFLIGHT_PATH,
        "ANALYSIS_RECEIPT_FILENAME": ANALYSIS_RECEIPT_FILENAME,
        "BASE_BUNDLE_ROOT": BUNDLE_ROOT,
        "BASE_ROOT_MANIFEST_PATH": ROOT_MANIFEST_PATH,
    }
    failures = [
        name for name, value in expected.items() if getattr(correction, name) != value
    ]
    if failures:
        raise RuntimeError(f"Correction helper namespace differs: {failures}")


_assert_correction_contract()


def _binding(root: Path, relative: Path) -> dict[str, str]:
    path = root / relative
    base._require(
        path.is_file() and not path.is_symlink(),
        f"missing correction dependency: {relative}",
    )
    return {"path": relative.as_posix(), "sha256": _sha256(path)}


def _pinned_binding(root: Path, relative: Path, expected_sha256: str) -> dict[str, str]:
    binding = _binding(root, relative)
    base._require(
        binding["sha256"] == expected_sha256,
        f"frozen correction dependency hash differs: {relative}",
    )
    return binding


def _validate_receipt_correction_block(root: Path, block: Any) -> dict[str, Any]:
    base._require(isinstance(block, Mapping), "analysis correction block is missing")
    expected = correction.analysis_validation_correction_block(
        root, adapter_path=ANALYZER_ADAPTER_PATH
    )
    base._require(
        dict(block) == expected,
        "analysis receipt correction block differs",
    )
    return dict(expected)


def _root_correction_block(
    root: Path, receipt_correction: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "correction_id": CORRECTION_ID,
        "base_protocol_id": PROTOCOL_ID,
        "base_bundle_id": BUNDLE_ID,
        "base_bundle_root": BUNDLE_ROOT.as_posix(),
        "base_root_manifest_path": ROOT_MANIFEST_PATH.as_posix(),
        "analysis_receipt_key": RECEIPT_CORRECTION_KEY,
        "analysis_receipt_correction": dict(receipt_correction),
        "active_publication_tooling": {
            "builder": _binding(root, BUILDER_ADAPTER_PATH),
            "validator": _binding(root, VALIDATOR_ADAPTER_PATH),
        },
        "base_publication_tooling": {
            "builder": _pinned_binding(root, BASE_BUILDER_PATH, BASE_BUILDER_SHA256),
            "validator": _pinned_binding(
                root, BASE_VALIDATOR_PATH, BASE_VALIDATOR_SHA256
            ),
        },
        "source_logs_changed": False,
        "execution_reused": True,
        "scientific_math_changed": False,
    }


def _validate_correction_authority(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Delegate exact correction manifest and preflight validation to the helper."""

    manifest = correction.validate_correction_manifest(root)
    preflight = correction.validate_correction_preflight(root, manifest)
    return manifest, preflight


def _analysis_receipt(root: Path, analysis_dir: Path) -> dict[str, Any]:
    receipt = base._load_json(
        analysis_dir / ANALYSIS_RECEIPT_FILENAME,
        "corrected v2 analysis receipt",
    )
    _validate_receipt_correction_block(root, receipt.get(RECEIPT_CORRECTION_KEY))
    return receipt


def _corrected_validate_run_source(
    root: Path,
    run_dir: Path,
    *,
    arm: str,
    family: str,
    analysis_input: Mapping[str, Any],
    process: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Validate one wrapped completion line, then expose a temporary projection."""

    receipt = base._load_json(run_dir / "receipt.json", f"{arm}/{family} run receipt")
    run_id = receipt.get("run_id")
    base._require(isinstance(run_id, str), f"{arm}/{family} run ID differs")
    log_relative = process.get("log_path")
    base._require(isinstance(log_relative, str), f"{arm}/{family} log path differs")
    relative_path = Path(log_relative)
    base._require(
        not relative_path.is_absolute()
        and ".." not in relative_path.parts
        and relative_path.as_posix() == log_relative,
        f"{arm}/{family} log path is not canonical and repository-relative",
    )
    unresolved_log = root / relative_path
    source_log = unresolved_log.resolve()
    base._require(
        source_log.is_relative_to(root.resolve())
        and unresolved_log.is_file()
        and not unresolved_log.is_symlink()
        and source_log.is_file(),
        f"{arm}/{family} source log differs",
    )
    source_bytes = source_log.read_bytes()
    base._require(
        process.get("log_sha256") == hashlib.sha256(source_bytes).hexdigest(),
        f"{arm}/{family} source log differs",
    )
    correction.parse_completion_wrap(
        source_bytes,
        expected_run_dir=run_dir.resolve(),
        expected_run_id=run_id,
    )
    canonical_bytes = b"Complete  " + str(run_dir.resolve()).encode("utf-8") + b"\n"
    descriptor, temporary = tempfile.mkstemp(prefix="glyphprobe-canonical-log-")
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        projected_process = dict(process)
        projected_process["log_path"] = str(temporary_path)
        return _ORIGINAL_VALIDATE_RUN_SOURCE(
            root,
            run_dir,
            arm=arm,
            family=family,
            analysis_input=analysis_input,
            process=projected_process,
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def build_bundle(
    root: Path,
    *,
    run_dirs: Mapping[tuple[str, str], Path],
    analysis_dir: Path,
    preflight_path: Path | None = None,
    attempt_receipt_path: Path | None = None,
    execution_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Build through the frozen v2 implementation under two scoped patches."""

    resolved_root = Path(root).resolve()
    resolved_analysis = Path(analysis_dir).resolve()
    previous_run_validator = base._validate_run_source
    previous_writer = base._atomic_write_json
    base._require(
        previous_run_validator is _ORIGINAL_VALIDATE_RUN_SOURCE
        and previous_writer is _ORIGINAL_ATOMIC_WRITE_JSON,
        "frozen base builder patch state differs before correction",
    )
    _validate_correction_authority(resolved_root)
    receipt = _analysis_receipt(resolved_root, resolved_analysis)
    receipt_correction = receipt[RECEIPT_CORRECTION_KEY]
    expected_root_block = _root_correction_block(resolved_root, receipt_correction)
    root_manifest = (resolved_root / ROOT_MANIFEST_PATH).resolve()
    writer_calls = 0

    def corrected_writer(path: Path, value: Mapping[str, Any]) -> None:
        nonlocal writer_calls
        destination = Path(path).resolve()
        if destination != root_manifest:
            _ORIGINAL_ATOMIC_WRITE_JSON(path, value)
            return
        writer_calls += 1
        base._require(writer_calls == 1, "root manifest writer called more than once")
        base._require(isinstance(value, dict), "root manifest value is not mutable")
        base._require(
            ROOT_CORRECTION_KEY not in value,
            "root manifest correction block already exists",
        )
        value[ROOT_CORRECTION_KEY] = expected_root_block
        _ORIGINAL_ATOMIC_WRITE_JSON(path, value)

    base._validate_run_source = _corrected_validate_run_source
    base._atomic_write_json = corrected_writer
    try:
        manifest = base.build_bundle(
            resolved_root,
            run_dirs=run_dirs,
            analysis_dir=resolved_analysis,
            preflight_path=preflight_path,
            attempt_receipt_path=attempt_receipt_path,
            execution_receipt_path=execution_receipt_path,
        )
    finally:
        base._validate_run_source = previous_run_validator
        base._atomic_write_json = previous_writer
    base._require(writer_calls == 1, "root manifest correction block was not written")
    base._require(
        manifest.get(ROOT_CORRECTION_KEY) == expected_root_block,
        "returned root manifest correction block differs",
    )
    return manifest


def _parser():
    return base._parser()


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
        correction.AnalysisCorrectionError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(manifest["inventory"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
