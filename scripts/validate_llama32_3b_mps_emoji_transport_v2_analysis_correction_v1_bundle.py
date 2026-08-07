#!/usr/bin/env python3
"""Validate the v2 public bundle plus analysis correction v1 provenance.

Correction authority and active adapter hashes are checked first.  The frozen
standalone v2 validator then remains the base validator for the complete public
evidence tree.  This adapter never consults local raw run evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
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
    BASE_VALIDATOR_PATH,
    BASE_VALIDATOR_SHA256,
    "glyphprobe_frozen_llama32_3b_mps_transport_v2_bundle_validator",
)
correction = _import_exact(
    HELPER_PATH,
    HELPER_SHA256,
    "glyphprobe_frozen_llama32_3b_mps_transport_v2_analysis_correction_v1_validator",
)

BundleValidationError = base.BundleValidationError
PROTOCOL_ID = base.PROTOCOL_ID
BUNDLE_ID = base.BUNDLE_ID
BUNDLE_ROOT = base.BUNDLE_ROOT
ROOT_MANIFEST_PATH = base.ROOT_MANIFEST_PATH
ANALYSIS_RECEIPT_FILENAME = "llama32_3b_mps_emoji_transport_v2_receipt.json"
ROOT_CORRECTION_KEY = "post_execution_analysis_validation_correction"
RECEIPT_CORRECTION_KEY = "analysis_validation_correction"


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
    manifest = correction.validate_correction_manifest(root)
    preflight = correction.validate_correction_preflight(root, manifest)
    return manifest, preflight


def _validate_correction_blocks(root: Path) -> dict[str, Any]:
    manifest = base._load_json(
        root / ROOT_MANIFEST_PATH,
        "root publication manifest with correction",
    )
    receipt = base._load_json(
        root / BUNDLE_ROOT / "analysis" / ANALYSIS_RECEIPT_FILENAME,
        "public corrected analysis receipt",
    )
    receipt_block = _validate_receipt_correction_block(
        root, receipt.get(RECEIPT_CORRECTION_KEY)
    )
    expected_root = _root_correction_block(root, receipt_block)
    base._require(
        manifest.get(ROOT_CORRECTION_KEY) == expected_root,
        "root manifest correction block differs",
    )
    base._require(
        manifest.get("tooling")
        == {
            "builder_path": BASE_BUILDER_PATH.as_posix(),
            "builder_sha256": BASE_BUILDER_SHA256,
            "validator_path": BASE_VALIDATOR_PATH.as_posix(),
            "validator_sha256": BASE_VALIDATOR_SHA256,
        },
        "base tooling block no longer identifies the delegated v2 implementation",
    )
    return expected_root


def validate_bundle(root: Path) -> dict[str, Any]:
    """Validate correction authority, active provenance, then all v2 evidence."""

    resolved_root = Path(root).resolve()
    _validate_correction_authority(resolved_root)
    root_block = _validate_correction_blocks(resolved_root)
    report = base.validate_bundle(resolved_root)
    report["correction_revision"] = CORRECTION_ID
    report["analysis_validation_correction"] = "pass"
    report["active_bundle_validator"] = root_block["active_publication_tooling"][
        "validator"
    ]
    report["base_bundle_validator"] = root_block["base_publication_tooling"][
        "validator"
    ]
    return report


def _parser():
    return base._parser()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = validate_bundle(args.root)
    except (
        BundleValidationError,
        correction.AnalysisCorrectionError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
