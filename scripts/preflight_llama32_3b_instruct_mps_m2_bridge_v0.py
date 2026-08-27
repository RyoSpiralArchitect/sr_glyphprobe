#!/usr/bin/env python3
"""Zero-model-forward public preflight for the Llama M2 bridge v0."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any

import numpy
import orjson
import pydantic
import torch
import transformers
import yaml


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "glyphprobe-llama32-3b-instruct-mps-m2-bridge-v0"
MANIFEST_PATH = ROOT / "data" / "manifests" / "llama32_3b_instruct_mps_m2_bridge_v0.json"
DEFAULT_OUTPUT = ROOT / "validation" / "llama32_3b_instruct_mps_m2_bridge_v0" / "preflight.json"
MODEL_REVISION = "0cb88a4f764b7a12671c53f0838cd831a0843b95"
EXPECTED_ENVIRONMENT = {
    "python_version": "3.11.14",
    "platform": "macOS-26.4.1-arm64-arm-64bit",
    "machine": "arm64",
    "numpy_version": "2.4.4",
    "orjson_version": "3.11.9",
    "pydantic_version": "2.12.5",
    "torch_version": "2.11.0",
    "transformers_version": "4.57.6",
    "torch_mps_built": True,
    "torch_mps_available": True,
}
FORBIDDEN_NAMES = {
    "p2_confirmatory_targets_v1.jsonl",
    "c1_confirmatory_targets_v1.jsonl",
    "c1_causal_holdout_targets_v1.jsonl",
}


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = _load_module(
    "glyphprobe_llama_m2_bridge_analyzer_v0",
    ROOT / "scripts" / "analyze_llama32_3b_instruct_mps_m2_bridge_v0.py",
)
LAUNCHER = _load_module(
    "glyphprobe_llama_m2_bridge_launcher_v0",
    ROOT / "scripts" / "run_llama32_3b_instruct_mps_m2_bridge_v0.py",
)
TOKEN_AUDIT = _load_module(
    "glyphprobe_llama_m2_token_audit_v0",
    ROOT / "scripts" / "audit_llama32_m2_control_transfer_tokenizer_v0.py",
)
MANIFEST_BUILDER = _load_module(
    "glyphprobe_llama_m2_manifest_builder_v0",
    ROOT / "scripts" / "build_llama32_3b_instruct_mps_m2_bridge_v0_manifest.py",
)


class PreflightError(RuntimeError):
    """Raised when a frozen preflight invariant fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise PreflightError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_authority() -> dict[str, Any]:
    _require(not _git("status", "--porcelain"), "Preflight requires a clean worktree")
    branch = _git("branch", "--show-current")
    _require(branch == "main", f"Preflight requires main, observed {branch!r}")
    head = _git("rev-parse", "HEAD")
    origin = _git("rev-parse", "origin/main")
    _require(head == origin, "Preflight HEAD must equal origin/main")
    return {
        "audited_commit": head,
        "origin_main_commit": origin,
        "branch": branch,
        "worktree_clean": True,
    }


def _validate_manifest() -> dict[str, Any]:
    _require(MANIFEST_PATH.is_file() and not MANIFEST_PATH.is_symlink(), "Static manifest missing")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Manifest protocol differs")
    _require(manifest.get("status") == "static_freeze_model_forward_not_authorized_until_public_preflight", "Manifest status differs")
    _require(
        manifest == MANIFEST_BUILDER.build_manifest(ROOT),
        "Static manifest does not equal the result of the committed builder",
    )
    files = manifest.get("static_files")
    _require(isinstance(files, dict) and files, "Static file map missing")
    for relative, expected in files.items():
        _require(Path(relative).name not in FORBIDDEN_NAMES, "Protected target entered manifest")
        path = (ROOT / relative).resolve()
        _require(ROOT in path.parents and path.is_file() and not path.is_symlink(), f"Static file missing: {relative}")
        _require(path.stat().st_size == expected["bytes"], f"Static byte count differs: {relative}")
        _require(_sha256_file(path) == expected["sha256"], f"Static hash differs: {relative}")
    return manifest


def _environment() -> dict[str, Any]:
    observed = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "numpy_version": numpy.__version__,
        "orjson_version": orjson.__version__,
        "pydantic_version": pydantic.__version__,
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "torch_mps_built": torch.backends.mps.is_built(),
        "torch_mps_available": torch.backends.mps.is_available(),
    }
    _require(observed == EXPECTED_ENVIRONMENT, f"Environment differs: {observed}")
    return observed


def _validate_configs() -> dict[str, Any]:
    configs: dict[str, Any] = {}
    signatures: list[dict[str, Any]] = []
    for role in ANALYZER.ROLE_ORDER:
        path = ANALYZER.CONFIG_PATHS[role]
        text = path.read_text(encoding="utf-8")
        _require(not any(name in text for name in FORBIDDEN_NAMES), f"Protected target referenced: {role}")
        value = yaml.safe_load(text)
        _require(isinstance(value, dict), f"Config invalid: {role}")
        ANALYZER._validate_config(value, role)
        signatures.append(ANALYZER._common_config_signature(value))
        configs[role] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": _sha256_file(path),
            "panel_path": value["panel"]["file"],
            "run_name": value["run"]["name"],
        }
    _require(all(row == signatures[0] for row in signatures[1:]), "Four configs differ outside panel/run identity")
    target_groups, target_ids = ANALYZER._target_authority()
    _require(len(target_ids) == 24 and len(target_groups) == 24, "Target authority differs")
    _require(_sha256_file(ANALYZER.WRAPPER_PATH) == ANALYZER.WRAPPER_SHA256, "Wrapper hash differs")
    return {
        "configs": configs,
        "target_count": 24,
        "target_slice_sha256": ANALYZER.TARGET_FIRST24_SHA256,
        "wrapper_count": 16,
        "wrapper_sha256": ANALYZER.WRAPPER_SHA256,
    }


def _validate_model_and_tokenizer(model_path: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    model_path = model_path.resolve()
    artifact = LAUNCHER._model_artifact(model_path)
    expected = manifest["model_artifact"]
    for key in ("file_count", "total_bytes", "manifest_sha256", "files"):
        _require(artifact[key] == expected[key], f"Model artifact {key} differs")
    from transformers import AutoConfig, AutoTokenizer

    config = AutoConfig.from_pretrained(
        model_path,
        revision=MODEL_REVISION,
        local_files_only=True,
        trust_remote_code=False,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        revision=MODEL_REVISION,
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    architecture = {
        "config_class": type(config).__name__,
        "model_type": config.model_type,
        "num_hidden_layers": int(config.num_hidden_layers),
        "hidden_size": int(config.hidden_size),
        "intermediate_size": int(config.intermediate_size),
        "num_attention_heads": int(config.num_attention_heads),
        "num_key_value_heads": int(config.num_key_value_heads),
        "vocab_size": int(config.vocab_size),
        "auto_config_only": True,
    }
    _require(
        architecture
        == {
            "config_class": "LlamaConfig",
            "model_type": "llama",
            "num_hidden_layers": 28,
            "hidden_size": 3072,
            "intermediate_size": 8192,
            "num_attention_heads": 24,
            "num_key_value_heads": 8,
            "vocab_size": 128256,
            "auto_config_only": True,
        },
        f"Architecture differs: {architecture}",
    )
    tokenizer_record = {
        "class": type(tokenizer).__name__,
        "is_fast": bool(tokenizer.is_fast),
        "vocab_size": int(tokenizer.vocab_size),
        "length": len(tokenizer),
        "bos_token_id": tokenizer.bos_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
    }
    _require(
        tokenizer_record
        == {
            "class": "PreTrainedTokenizerFast",
            "is_fast": True,
            "vocab_size": 128000,
            "length": 128256,
            "bos_token_id": 128000,
            "eos_token_id": 128009,
            "pad_token_id": None,
        },
        f"Tokenizer identity differs: {tokenizer_record}",
    )
    return {
        "artifact": artifact,
        "model_path_recorded": False,
        "architecture": architecture,
        "tokenizer": tokenizer_record,
        "language_model_loaded": False,
    }, tokenizer


def _validate_control_suite(tokenizer: Any) -> dict[str, Any]:
    wrappers = TOKEN_AUDIT._load_wrappers(ANALYZER.WRAPPER_PATH, 16)
    reference_items = TOKEN_AUDIT._load_panel(
        ANALYZER.PANEL_PATHS["primary"], "colored_shapes"
    )
    reference = TOKEN_AUDIT._summary(
        tokenizer, "colored_shapes", reference_items, wrappers
    )
    comparisons: dict[str, Any] = {}
    for role in ("null_a", "null_b", "null_c"):
        panel_id = {
            "null_a": "llama32_m2_null_minimum_overlap_a_v2",
            "null_b": "llama32_m2_null_minimum_overlap_b_v2",
            "null_c": "llama32_m2_null_minimum_overlap_c_v2",
        }[role]
        panel = TOKEN_AUDIT._summary(
            tokenizer,
            panel_id,
            TOKEN_AUDIT._load_panel(ANALYZER.PANEL_PATHS[role], panel_id),
            wrappers,
        )
        comparison = TOKEN_AUDIT._compare_summaries(reference, panel)
        _require(comparison["transfer_gate_pass"] is True, f"Tokenizer control gate failed: {role}")
        comparisons[role] = comparison
    design_path = ROOT / "validation" / "llama32_3b_instruct_m2_control_design_v2" / "design_receipt.json"
    design = json.loads(design_path.read_text(encoding="utf-8"))
    _require(design.get("all_three_generated_panels_match") is True, "Design receipt gate differs")
    _require(design.get("overlap", {}).get("attains_theoretical_minimum") is True, "Minimum-overlap proof differs")
    _require(design.get("overlap", {}).get("attained_reused_placements") == 2, "Reuse count differs")
    return {
        "reference_profiles_sha256": reference["profiles_sha256"],
        "all_three_raw_and_16_wrapper_gates_pass": True,
        "comparisons": comparisons,
        "design_receipt": {
            "path": design_path.relative_to(ROOT).as_posix(),
            "sha256": _sha256_file(design_path),
            "attained_reused_placements": 2,
            "independent_control_panels": False,
        },
    }


def _atomic_write_no_overwrite(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _require(not path.exists(), f"Refusing to overwrite preflight: {path}")
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


def run_preflight(model_path: Path, output: Path) -> dict[str, Any]:
    output = output.resolve()
    _require(output == DEFAULT_OUTPUT.resolve(), "Preflight output path differs")
    git_authority = _git_authority()
    manifest = _validate_manifest()
    environment = _environment()
    static = _validate_configs()
    model, tokenizer = _validate_model_and_tokenizer(model_path, manifest)
    controls = _validate_control_suite(tokenizer)
    receipt = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "passed",
        "git_authority": git_authority,
        "static_manifest": {
            "path": MANIFEST_PATH.relative_to(ROOT).as_posix(),
            "sha256": _sha256_file(MANIFEST_PATH),
            "static_file_count": manifest["static_file_count"],
            "all_hashes_verified": True,
        },
        "environment": environment,
        "static_grid": static,
        "model": model,
        "tokenizer_controls": controls,
        "authorization": {
            "frozen_grid_execution_authorized": True,
            "analysis_authorized_only_after_four_complete_runs": True,
            "resume_authorized": False,
        },
        "claim_boundary": {
            "tokenizer_only_preflight": True,
            "language_model_loaded": False,
            "model_forward_count": 0,
            "scientific_outcomes_inspected": False,
            "protected_p2_or_c1_accessed": False,
            "independent_confirmation": False,
            "scale_curve": False,
            "speed_claim_authorized": False,
        },
    }
    _atomic_write_no_overwrite(output, receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        receipt = run_preflight(args.model_path, args.output)
    except (PreflightError, OSError, ValueError) as exc:
        print(f"preflight_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "protocol_id": PROTOCOL_ID,
                "status": receipt["status"],
                "model_forward_count": receipt["claim_boundary"]["model_forward_count"],
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
