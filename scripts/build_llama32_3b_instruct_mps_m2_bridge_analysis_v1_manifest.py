#!/usr/bin/env python3
"""Build the no-overwrite outcome-blind analysis-correction v1 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ID = "glyphprobe-llama32-3b-instruct-mps-m2-bridge-analysis-v1"
DEFAULT_OUTPUT = (
    ROOT
    / "data"
    / "manifests"
    / "llama32_3b_instruct_mps_m2_bridge_analysis_v1.json"
)
EXECUTION_RECEIPT = (
    "validation/llama32_3b_instruct_mps_m2_bridge_v0/execution.json"
)
EXECUTION_SHA256 = "1d872ae1474422f743f1bf92433fcefb159cc512355a6bc4ddd99f65656638e2"
FORBIDDEN = {
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
}
FIXED_PATHS = (
    "AGENTS.md",
    "pyproject.toml",
    "configs/llama32_3b_instruct_mps_m2_primary_v0.yaml",
    "configs/llama32_3b_instruct_mps_m2_null_a_v0.yaml",
    "configs/llama32_3b_instruct_mps_m2_null_b_v0.yaml",
    "configs/llama32_3b_instruct_mps_m2_null_c_v0.yaml",
    "data/emoji_panels/colored_shapes.yaml",
    "data/emoji_panels/llama32_m2_matched_null_a_v2.yaml",
    "data/emoji_panels/llama32_m2_matched_null_b_v2.yaml",
    "data/emoji_panels/llama32_m2_matched_null_c_v2.yaml",
    "data/manifests/llama32_3b_instruct_mps_m2_bridge_v0.json",
    "data/targets/prestage_targets.jsonl",
    "data/wrappers/source_wrappers.jsonl",
    "docs/LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.md",
    "docs/LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.ja.md",
    "scripts/analyze_llama32_3b_instruct_mps_m2_bridge_v0.py",
    "scripts/analyze_llama32_3b_instruct_mps_m2_bridge_v1.py",
    "scripts/analyze_m2_confirmatory.py",
    "scripts/analyze_m2_dependence_sensitivity_v1.py",
    "scripts/build_llama32_3b_instruct_mps_m2_bridge_analysis_v1_manifest.py",
    "tests/test_llama32_3b_instruct_mps_m2_bridge_analysis_v1.py",
    "validation/llama32_3b_instruct_mps_m2_bridge_v0/preflight.json",
    "validation/llama32_3b_instruct_mps_m2_bridge_v0/attempt_started.json",
    EXECUTION_RECEIPT,
    "validation/llama32_3b_instruct_mps_m2_bridge_v0/analysis_v0_failure.json",
)


class ManifestError(RuntimeError):
    """Raised when the analysis correction cannot be frozen exactly."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _sha256(path: Path) -> str:
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


def build_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    paths = set(FIXED_PATHS)
    _require(not paths & FORBIDDEN, "Protected target path entered analysis manifest")
    files: dict[str, dict[str, Any]] = {}
    for relative in sorted(paths):
        path = root / relative
        _require(path.is_file() and not path.is_symlink(), f"Missing static file: {relative}")
        files[relative] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}

    execution_path = root / EXECUTION_RECEIPT
    _require(_sha256(execution_path) == EXECUTION_SHA256, "Execution receipt hash differs")
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    _require(execution.get("status") == "execution_complete_analysis_not_run", "Execution status differs")
    _require(execution.get("analysis_authorized") is True, "Execution does not authorize analysis")
    _require(execution.get("completed_process_count") == 4, "Execution count differs")
    _require(execution.get("expected_process_count") == 4, "Expected count differs")

    return {
        "schema_version": 1,
        "analysis_id": ANALYSIS_ID,
        "status": "outcome_blind_analysis_correction_v1_frozen",
        "correction": {
            "v0_status": "failed_closed_before_scientific_outcome_read",
            "v0_error": "Frozen config differs for primary:capture.layers",
            "v0_failure_stage": "first_panel_resolved_config_validation",
            "only_semantic_change": (
                "validate normalized depth specs [0.2, 0.4] in resolved_config; "
                "continue validating resolved layers [5, 11] from run summary"
            ),
            "scientific_outcomes_seen_before_v1_freeze": False,
        },
        "unchanged_estimand": {
            "layers": [5, 11],
            "normalized_depth_specs": [0.2, 0.4],
            "primary_layer": 5,
            "non_rescuing_layer": 11,
            "strength": 0.05,
            "direction_seeds": [101, 211, 307],
            "ensemble_endpoint": "primary minus targetwise median of null A/B/C",
            "mandatory_sensitivity": "primary minus fully disjoint null A",
            "bootstrap_replicates": 20000,
            "bootstrap_seed": 20260828,
            "delta": 0.06,
            "criterion": "both layer-5 rebuilt-prototype 95% lower bounds strictly exceed delta",
        },
        "execution_receipt": {
            "path": EXECUTION_RECEIPT,
            "sha256": EXECUTION_SHA256,
            "analysis_authorized": True,
            "completed_process_count": 4,
        },
        "claim_boundary": {
            "exploratory": True,
            "independent_confirmation": False,
            "scale_curve": False,
            "model_forward_count_at_freeze": 0,
            "protected_p2_or_c1_accessed": False,
        },
        "static_files": files,
        "static_file_count": len(files),
        "static_files_manifest_sha256": _stable_hash(files),
        "forbidden_paths_absent": sorted(FORBIDDEN),
    }


def _write_no_overwrite(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.exists(), f"Refusing to overwrite manifest: {path}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(args.root)
    _write_no_overwrite(args.output.resolve(), manifest)
    print(json.dumps({"analysis_id": ANALYSIS_ID, "static_file_count": manifest["static_file_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
