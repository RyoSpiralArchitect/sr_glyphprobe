#!/usr/bin/env python3
"""Build the no-overwrite static manifest for the Llama M2 bridge v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "glyphprobe-llama32-3b-instruct-mps-m2-bridge-v0"
DEFAULT_OUTPUT = ROOT / "data" / "manifests" / "llama32_3b_instruct_mps_m2_bridge_v0.json"
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
    "configs/llama32_3b_instruct_m2_control_transfer_tokenizer_v0.yaml",
    "configs/llama32_3b_instruct_m2_control_design_v0.yaml",
    "configs/llama32_3b_instruct_m2_control_design_v1.yaml",
    "configs/llama32_3b_instruct_m2_control_design_v2.yaml",
    "data/emoji_panels/colored_shapes.yaml",
    "data/emoji_panels/llama32_m2_matched_null_a_v2.yaml",
    "data/emoji_panels/llama32_m2_matched_null_b_v2.yaml",
    "data/emoji_panels/llama32_m2_matched_null_c_v2.yaml",
    "data/targets/prestage_targets.jsonl",
    "data/wrappers/source_wrappers.jsonl",
    "docs/LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.md",
    "docs/LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.ja.md",
    "scripts/analyze_llama32_3b_instruct_mps_m2_bridge_v0.py",
    "scripts/analyze_m2_confirmatory.py",
    "scripts/analyze_m2_dependence_sensitivity_v1.py",
    "scripts/audit_llama32_m2_control_transfer_tokenizer_v0.py",
    "scripts/build_llama32_3b_instruct_mps_m2_bridge_v0_manifest.py",
    "scripts/design_llama32_m2_controls_tokenizer_v0.py",
    "scripts/design_llama32_m2_controls_tokenizer_v1.py",
    "scripts/design_llama32_m2_controls_tokenizer_v2.py",
    "scripts/preflight_llama32_3b_instruct_mps_m2_bridge_v0.py",
    "scripts/run_llama32_3b_instruct_mps_m2_bridge_v0.py",
    "tests/test_audit_llama32_m2_control_transfer_tokenizer_v0.py",
    "tests/test_design_llama32_m2_controls_tokenizer_v0.py",
    "tests/test_design_llama32_m2_controls_tokenizer_v1.py",
    "tests/test_design_llama32_m2_controls_tokenizer_v2.py",
    "tests/test_llama32_3b_instruct_mps_m2_bridge_v0.py",
    "validation/llama32_3b_instruct_m2_control_transfer_tokenizer_v0/receipt.json",
    "validation/llama32_3b_instruct_m2_control_design_v0/design_receipt.json",
    "validation/llama32_3b_instruct_m2_control_design_v1/design_receipt.json",
    "validation/llama32_3b_instruct_m2_control_design_v2/design_receipt.json",
)
MODEL_FILES = {
    "config.json": {"bytes": 878, "sha256": "39fb36dc5416f445ebc4e71cb71fbcf6727e80a35836d8ba1a1474c318467b7a"},
    "generation.json": {"bytes": 189, "sha256": "88effbb63300dbbc7390143fbbdd9d9fa50587b37e8bfd16c8c90d4970a74a36"},
    "model-00001-of-00002.safetensors": {"bytes": 4965799096, "sha256": "13cbd6d16e927a0c5bad54102514e6e18b4a47b3a6eb911e39d678d328d19f55"},
    "model-00002-of-00002.safetensors": {"bytes": 1459729952, "sha256": "7b770216613ac5c34d7c54bdff1fa616bc4e338a9d0b20af6303e48c295ee23c"},
    "model.safetensors.index.json": {"bytes": 20919, "sha256": "0a57c30afc07c81610ae7fe013bea3b9d50365f9a8145ae98e8714220f3d7c7c"},
    "special_tokens_map.json": {"bytes": 296, "sha256": "6f38c73729248f6c127296386e3cdde96e254636cc58b4169d3fd32328d9a8ec"},
    "tokenizer.json": {"bytes": 9085657, "sha256": "79e3e522635f3171300913bb421464a87de6222182a0570b9b2ccba2a964b2b4"},
    "tokenizer_config.json": {"bytes": 54528, "sha256": "9823dcfdc1121869029da45192238e85cf44f0b232a6d9dc20e4fe6f4242a14e"},
}


class ManifestError(RuntimeError):
    """Raised when the static freeze cannot be built exactly."""


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
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_manifest(root: Path) -> dict[str, Any]:
    root = root.resolve()
    paths = set(FIXED_PATHS)
    paths.update(
        path.relative_to(root).as_posix()
        for path in (root / "src" / "glyphprobe").rglob("*.py")
        if path.is_file()
    )
    _require(not paths & FORBIDDEN, "Protected target path entered static manifest")
    files: dict[str, dict[str, Any]] = {}
    for relative in sorted(paths):
        path = root / relative
        _require(path.is_file() and not path.is_symlink(), f"Missing static file: {relative}")
        files[relative] = {"bytes": path.stat().st_size, "sha256": _sha256(path)}
    model_manifest = _stable_hash(MODEL_FILES)
    _require(
        model_manifest == "c698f962b8587e2c38dcb86e344928aa5db3c7386e160230d493fcaf9166ecf6",
        "Pinned model file manifest hash differs",
    )
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "static_freeze_model_forward_not_authorized_until_public_preflight",
        "claim_boundary": {
            "exploratory_bridge": True,
            "reused_prestage_targets": True,
            "independent_confirmation": False,
            "scale_curve": False,
            "model_forward_count_at_manifest_build": 0,
            "protected_p2_or_c1_accessed": False,
        },
        "grid": {
            "roles": ["primary", "null_a", "null_b", "null_c"],
            "normalized_depths": [0.2, 0.4],
            "resolved_layers_for_28_layer_model": [5, 11],
            "strength": 0.05,
            "direction_seeds": [101, 211, 307],
            "random_directions_per_layer": 8,
            "targets": "first 24 reused prestage targets",
            "wrappers": 16,
            "backend": "transformers/mps",
            "runtime_dtype": "bfloat16",
        },
        "analysis": {
            "primary_layer": 5,
            "non_rescuing_layer": 11,
            "ensemble_endpoint": "primary minus targetwise median of null A/B/C",
            "mandatory_sensitivity": "primary minus fully disjoint null A",
            "bootstrap_replicates": 20000,
            "bootstrap_seed": 20260828,
            "delta": 0.06,
            "criterion": "both layer-5 rebuilt-prototype 95% lower bounds strictly exceed delta",
            "confirmatory_status_authorized": False,
        },
        "model_artifact": {
            "model": "meta-llama/Llama-3.2-3B-Instruct",
            "revision": "0cb88a4f764b7a12671c53f0838cd831a0843b95",
            "runtime_alias": "/private/tmp/glyphprobe-llama32-3b-instruct-v0",
            "file_count": len(MODEL_FILES),
            "total_bytes": sum(row["bytes"] for row in MODEL_FILES.values()),
            "manifest_sha256": model_manifest,
            "files": MODEL_FILES,
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
    print(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "static_file_count": manifest["static_file_count"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
