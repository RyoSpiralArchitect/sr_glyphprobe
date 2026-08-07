#!/usr/bin/env python3
"""Model-free, fail-closed preflight for the frozen E2 MPS grid.

This program reads only the explicitly bound public protocol inputs.  It never
loads a language model and never opens either protected target bank.  It checks
the cached snapshot bytes, AutoConfig architecture, host environment, and exact
tokenizer surface after validating the mandatory freeze manifest.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

import yaml


PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1"
MANIFEST_ID = "llama32_3b_mps_emoji_transport_v1"
MODEL_ID = "mlx-community/Llama-3.2-3B-bf16"
MODEL_REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
TOKENIZER_CLASS = "PreTrainedTokenizerFast"
TOKENIZER_BASE_VOCAB_SIZE = 128_000
TOKENIZER_LENGTH = 128_256
MODEL_LAYER_COUNT = 28
MODEL_WIDTH = 3_072
MODEL_VOCAB_SIZE = 128_256
MODEL_ARTIFACT_FILE_COUNT = 9
MODEL_ARTIFACT_TOTAL_BYTES = 6_434_705_789
MODEL_ARTIFACT_MANIFEST_SHA256 = (
    "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
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
    "file_count": MODEL_ARTIFACT_FILE_COUNT,
    "total_bytes": MODEL_ARTIFACT_TOTAL_BYTES,
    "manifest_sha256": MODEL_ARTIFACT_MANIFEST_SHA256,
}
EXPECTED_ARCHITECTURE = {
    "config_class": "LlamaConfig",
    "num_hidden_layers": MODEL_LAYER_COUNT,
    "hidden_size": MODEL_WIDTH,
    "vocab_size": MODEL_VOCAB_SIZE,
}

MANIFEST_RELATIVE = Path("data/manifests/llama32_3b_mps_emoji_transport_v1.json")
DEFAULT_OUTPUT_RELATIVE = Path(
    "artifacts/llama32_3b_mps_emoji_transport_v1/preflight/tokenization_audit_v1.json"
)
TARGET_RELATIVE = Path("data/targets/prestage_targets.jsonl")
SOURCE_RELATIVE = Path("data/wrappers/source_wrappers.jsonl")
TARGET_SHA256 = "91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7"
TARGET_FIRST24_SHA256 = (
    "26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b"
)
SOURCE_SHA256 = "310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee"

FORBIDDEN_TARGET_PATHS = {
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
}
FORBIDDEN_TARGET_NAMES = {Path(value).name for value in FORBIDDEN_TARGET_PATHS}

FAMILY_ORDER = ("sky", "food", "animals", "transport", "social")
SCOPE_ORDER = ("full50", "core35")
FAMILY_MIDDLE_TOKEN = {
    "sky": 234,
    "food": 235,
    "animals": 238,
    "transport": 248,
    "social": 97,
}
FULL_PANEL_PATHS = {
    "sky": Path("data/emoji_panels/e1_sky_moon.yaml"),
    "food": Path("data/emoji_panels/e1_food.yaml"),
    "animals": Path("data/emoji_panels/e1_animals.yaml"),
    "transport": Path("data/emoji_panels/e1_transport.yaml"),
    "social": Path("data/emoji_panels/e1_social.yaml"),
}
FULL_PANEL_SHA256 = {
    "sky": "811b0850574004bd56c9eb6419e814b273d02d13a97b815938095f66f3c1e1e1",
    "food": "6fb16ccf141b2dabb33dfe9d20913568d2a294285c9bc7f8f8063c197280e7a3",
    "animals": "2455d8de88af37fed0925c4df93f3914fba6abb275a05907198baaca2a7954b5",
    "transport": "784dbba21328757db97a8ff65e310cf15707b178d37b11fce033e47832c5d67f",
    "social": "b43ba3290c499c248c2bc034af0d3454463fcf5e5d4d64e5fab4fd62ee5cf1a6",
}
CORE_PANEL_PATHS = {
    family: Path(f"data/emoji_panels/e2_core35_{family}.yaml")
    for family in FAMILY_ORDER
}
CONFIG_PATHS = {
    (scope, family): Path(f"configs/e2_llama32_3b_mps_{scope}_{family}_v1.yaml")
    for scope in SCOPE_ORDER
    for family in FAMILY_ORDER
}
CRITICAL_FILE_PATHS = (
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.md"),
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.ja.md"),
    Path("docs/HOLDOUT_STATUS.md"),
    Path("docs/HOLDOUT_STATUS.ja.md"),
    Path("validation/holdout_exposure_incidents/2026-08-07-repository-search.json"),
    Path("scripts/audit_llama32_3b_mps_emoji_transport_v1.py"),
    Path("scripts/run_llama32_3b_mps_emoji_transport_v1.py"),
    Path("scripts/analyze_llama32_3b_mps_emoji_transport_v1.py"),
    Path("scripts/build_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    Path("scripts/validate_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    Path("scripts/analyze_emoji_family_exploratory_v1.py"),
    Path("src/glyphprobe/backends/transformers_backend.py"),
    Path("tests/test_analyze_llama32_3b_mps_emoji_transport_v1.py"),
    Path("tests/test_llama32_3b_mps_emoji_transport_v1.py"),
    Path("tests/test_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    Path("tests/test_transformers_explicit_dtype_guard.py"),
    Path("artifacts/llama32_3b_mps_emoji_transport_v1/README.md"),
    Path("artifacts/llama32_3b_mps_emoji_transport_v1/README.ja.md"),
    Path("pyproject.toml"),
)
ANALYZER_RELATIVE = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v1.py")
E1_MATH_RELATIVE = Path("scripts/analyze_emoji_family_exploratory_v1.py")

MERGED_TOKEN_EXCEPTIONS = {
    "sky_slot_01": (9468, 102032),
    "sky_slot_02": (9468, 107569),
    "social_slot_00": (9468, 100701),
}
EXPECTED_FIRST_TOKEN = 9468

TARGET_IDS = (
    "cont_01",
    "cont_02",
    "cont_03",
    "cont_04",
    "fact_01",
    "fact_02",
    "fact_03",
    "fact_04",
    "reason_01",
    "reason_02",
    "reason_03",
    "reason_04",
    "proc_01",
    "proc_02",
    "proc_03",
    "proc_04",
    "class_01",
    "class_02",
    "class_03",
    "class_04",
    "plan_01",
    "plan_02",
    "plan_03",
    "plan_04",
)
TARGET_GROUPS = (
    *("continuation",) * 4,
    *("factual",) * 4,
    *("reasoning",) * 4,
    *("procedural",) * 4,
    *("classification",) * 4,
    *("planning",) * 4,
)
WRAPPER_IDS = tuple(
    [
        "w01_mark_anchor",
        "w02_bracket_continue",
        "w03_pipe_next",
        "w04_token_state",
        "w05_begin_end",
        "w06_binary_result",
        "w07_symbol_following",
        "w08_pair_q",
        "w09_input_response",
        "w10_sequence_continuation",
        "w11_field_anchor",
        "w12_list_next",
        "w13_left_right",
        "w14_codepoint_text",
        "w15_observation_inference",
        "w16_slot_completion",
    ]
)


class AuditError(RuntimeError):
    """Raised when a frozen preflight invariant is not satisfied."""


@dataclass(frozen=True)
class StaticAuthority:
    root: Path
    panels: dict[str, dict[str, list[dict[str, Any]]]]
    wrappers: list[dict[str, Any]]
    report: dict[str, Any]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AuditError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def collect_git_authority(root: Path) -> dict[str, Any]:
    """Bind the clean pushed commit whose manifest surface was audited."""
    root = root.resolve()
    dirty = _git(root, "status", "--porcelain")
    _require(not dirty, "Preflight requires a clean worktree")
    branch = _git(root, "branch", "--show-current")
    _require(branch == "main", f"Preflight requires main, observed {branch!r}")
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    _require(head == origin, "Preflight HEAD must equal origin/main")
    _require(
        len(head) == 40 and all(char in "0123456789abcdef" for char in head.lower()),
        "Preflight git commit is not a full SHA-1",
    )
    return {
        "audited_commit": head,
        "branch": branch,
        "origin_main_commit": origin,
        "worktree_clean_before_publication": True,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _model_artifact_receipt(root: Path) -> dict[str, Any]:
    """Hash a cached snapshot without resolving its path into the blob store."""
    _require(root.is_dir(), "Pinned model snapshot directory is missing")
    files: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for path in sorted(
        candidate for candidate in root.rglob("*") if candidate.is_file()
    ):
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        files[relative] = {"bytes": size, "sha256": _sha256(path)}
    _require(bool(files), "Pinned model snapshot contains no files")
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "manifest_sha256": _stable_hash(files),
        "files": files,
    }


def _collect_environment() -> dict[str, Any]:
    try:
        import torch
    except ImportError as exc:
        raise AuditError("torch is required for the MPS environment audit") from exc

    def distribution_version(name: str) -> str:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise AuditError(f"Required distribution is not installed: {name}") from exc

    return {
        "python_version": platform.python_version(),
        "glyphprobe_version": distribution_version("glyphprobe"),
        "numpy_version": distribution_version("numpy"),
        "torch_version": distribution_version("torch"),
        "transformers_version": distribution_version("transformers"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "torch_mps_built": bool(torch.backends.mps.is_built()),
        "torch_mps_available": bool(torch.backends.mps.is_available()),
    }


def _locate_model_snapshot() -> Path:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        from transformers.utils import cached_file
    except ImportError as exc:
        raise AuditError("transformers is required for the artifact audit") from exc
    try:
        cached_config = cached_file(
            MODEL_ID,
            "config.json",
            revision=MODEL_REVISION,
            local_files_only=True,
        )
    except Exception as exc:
        raise AuditError("Pinned model snapshot is not available locally") from exc
    _require(bool(cached_config), "Pinned model config is not available locally")
    config_path = Path(str(cached_config))
    _require(config_path.is_file(), "Pinned cached config is not a file")
    snapshot = config_path.parent
    _require(
        snapshot.name == MODEL_REVISION,
        f"Cached snapshot revision differs: {snapshot.name}",
    )
    return snapshot


def _load_config_metadata() -> dict[str, Any]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        from transformers import AutoConfig
    except ImportError as exc:
        raise AuditError("transformers is required for the architecture audit") from exc
    try:
        config = AutoConfig.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            local_files_only=True,
            trust_remote_code=False,
        )
    except Exception as exc:
        raise AuditError("Cannot load the pinned local AutoConfig") from exc
    return {
        "config_class": type(config).__name__,
        "num_hidden_layers": int(getattr(config, "num_hidden_layers", -1)),
        "hidden_size": int(getattr(config, "hidden_size", -1)),
        "vocab_size": int(getattr(config, "vocab_size", -1)),
        "commit_hash": getattr(config, "_commit_hash", None),
        "auto_config_only": True,
    }


def _validate_runtime_authority(runtime: Mapping[str, Any]) -> None:
    for section, expected in (
        ("environment", EXPECTED_ENVIRONMENT),
        ("model_artifact", EXPECTED_MODEL_ARTIFACT),
        ("architecture", EXPECTED_ARCHITECTURE),
    ):
        observed = runtime.get(section)
        _require(isinstance(observed, Mapping), f"Runtime {section} is missing")
        for key, value in expected.items():
            _require(
                observed.get(key) == value,
                f"Runtime {section}.{key} differs: {observed.get(key)!r}",
            )
    architecture = runtime["architecture"]
    _require(
        architecture.get("commit_hash") == MODEL_REVISION,
        "AutoConfig commit hash differs",
    )
    _require(
        architecture.get("auto_config_only") is True,
        "Architecture was not collected through AutoConfig only",
    )
    _require(runtime.get("language_model_loaded") is False, "Language model was loaded")
    _require(runtime.get("model_forward_count") == 0, "Model forward count is not zero")


def _validate_git_authority(git_authority: Mapping[str, Any]) -> None:
    audited_commit = git_authority.get("audited_commit")
    _require(
        isinstance(audited_commit, str)
        and len(audited_commit) == 40
        and all(char in "0123456789abcdef" for char in audited_commit.lower()),
        "Git authority audited_commit is invalid",
    )
    _require(git_authority.get("branch") == "main", "Git authority branch differs")
    _require(
        git_authority.get("origin_main_commit") == audited_commit,
        "Git authority origin/main differs",
    )
    _require(
        git_authority.get("worktree_clean_before_publication") is True,
        "Git authority worktree was not clean",
    )


def audit_runtime_authority() -> dict[str, Any]:
    """Verify the frozen host, cached files, and config without loading weights."""
    environment = _collect_environment()
    snapshot = _locate_model_snapshot()
    artifact = {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        **_model_artifact_receipt(snapshot),
    }
    architecture = _load_config_metadata()
    runtime = {
        "environment": environment,
        "model_artifact": artifact,
        "architecture": architecture,
        "language_model_loaded": False,
        "model_forward_count": 0,
        "runtime_parameter_dtype_measured": False,
        "runtime_parameter_dtype_measurement_stage": (
            "backend_load_pre_forward_and_run_receipt"
        ),
    }
    _validate_runtime_authority(runtime)
    return runtime


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")


def _selected_lines_sha256(path: Path, count: int) -> str:
    with path.open("rb") as handle:
        lines = [line for line in handle if line.strip()]
    _require(len(lines) >= count, f"{path.name} has fewer than {count} rows")
    return hashlib.sha256(b"".join(lines[:count])).hexdigest()


def _read_jsonl(path: Path, description: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditError(
                    f"Invalid JSON in {description} at line {line_number}"
                ) from exc
            _require(
                isinstance(value, dict),
                f"Expected an object in {description} at line {line_number}",
            )
            rows.append(value)
    return rows


def _read_yaml(path: Path, description: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AuditError(f"Cannot read {description}: {path.name}") from exc
    _require(isinstance(value, dict), f"Expected a mapping in {description}")
    return value


def _read_json_object(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read {description}: {path.name}") from exc
    _require(isinstance(value, dict), f"Expected an object in {description}")
    return value


def _contains_forbidden_path(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.replace("\\", "/")
        return any(
            normalized == path
            or normalized.endswith(f"/{path}")
            or Path(normalized).name in FORBIDDEN_TARGET_NAMES
            for path in FORBIDDEN_TARGET_PATHS
        )
    if isinstance(value, Mapping):
        return any(_contains_forbidden_path(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_path(item) for item in value)
    return False


def _panel_items(path: Path, family: str, slots: Sequence[int]) -> list[dict[str, Any]]:
    document = _read_yaml(path, f"{family} panel")
    values = document.get("items")
    _require(isinstance(values, list), f"{family} panel has no item list")
    _require(len(values) == len(slots), f"{family} panel item count differs")
    output: list[dict[str, Any]] = []
    for item, slot in zip(values, slots):
        _require(isinstance(item, dict), f"{family} slot {slot} is not a mapping")
        expected_id = f"{family}_slot_{slot:02d}"
        glyph = item.get("glyph")
        factors = item.get("factors")
        _require(
            item.get("id") == expected_id, f"Unexpected panel ID: {item.get('id')}"
        )
        _require(
            isinstance(glyph, str) and len(glyph) == 1, f"Invalid glyph: {expected_id}"
        )
        _require(
            isinstance(factors, dict)
            and factors.get("family") == family
            and factors.get("matched_slot") == f"slot_{slot:02d}"
            and factors.get("codepoint") == f"U+{ord(glyph):04X}",
            f"Factor binding differs for {expected_id}",
        )
        _require(
            isinstance(item.get("labels"), list), f"Labels differ for {expected_id}"
        )
        output.append(item)
    return output


def _nested(mapping: Mapping[str, Any], *path: str) -> Any:
    value: Any = mapping
    for part in path:
        _require(
            isinstance(value, Mapping) and part in value, f"Missing {'.'.join(path)}"
        )
        value = value[part]
    return value


def _expected_plan(condition_count: int) -> dict[str, int]:
    source = (condition_count + 1) * 16
    baseline = 24
    emoji = condition_count * 2 * 24 * 3
    random = 2 * 2 * 24 * 3
    zero = 2 * 24
    return {
        "source": source,
        "target_baseline": baseline,
        "emoji_intervention": emoji,
        "random_control": random,
        "zero_hook_control": zero,
        "total": source + baseline + emoji + random + zero,
        "intervention_rows": emoji + random + zero,
    }


def _expected_config(scope: str, family: str) -> dict[str, Any]:
    panel = FULL_PANEL_PATHS[family] if scope == "full50" else CORE_PANEL_PATHS[family]
    return {
        "schema_version": 1,
        "mode": "internal",
        "backend": {
            "kind": "transformers",
            "model": MODEL_ID,
            "revision": MODEL_REVISION,
            "device": "mps",
            "dtype": "float32",
            "local_files_only": True,
            "add_special_tokens": False,
            "trust_remote_code": False,
        },
        "run": {
            "name": f"e2-llama32-3b-mps-{scope}-{family}-transport-v1",
            "output_root": "../runs",
            "seeds": [101, 211, 307],
            "resume": False,
            "fail_fast": True,
            "replicate_mode": "wrapper_subsample",
            "wrapper_subsample_fraction": 0.75,
        },
        "panel": {
            "file": f"../{panel.as_posix()}",
            "neutral_glyph": "🟰",
            "centroid_mode": "panel",
        },
        "source": {
            "wrappers_file": "../data/wrappers/source_wrappers.jsonl",
            "max_wrappers": 16,
            "anchor_position": "last_nonpad",
        },
        "targets": {
            "cases_file": "../data/targets/prestage_targets.jsonl",
            "max_cases": 24,
            "calibration_cases": 6,
        },
        "capture": {
            "site": "resid_post",
            "layers": [5, 11],
            "position": "last_nonpad",
            "return_attentions": False,
        },
        "intervention": {
            "mode": "activation_add",
            "normalization": "rms",
            "strengths": [0.05],
            "position": "last_nonpad",
            "clip": {"mode": "global_rms", "max_ratio": 0.25},
            "iso_kl": {"enabled": False},
        },
        "controls": {
            "random_directions_per_layer": 2,
            "zero_direction": True,
            "sign_flip": False,
            "sign_flip_strengths": [],
            "label_shuffle_permutations": 0,
            "include_neutral_direction": False,
        },
        "metrics": {
            "top_k": 50,
            "fingerprint_dim": 96,
            "fingerprint_seed": 8_675_309,
            "split_half_repeats": 200,
            "rbo_p": 0.9,
            "save_top_logit_deltas": 32,
            "save_fingerprints": True,
            "epsilon": 1e-12,
        },
        "sae": {"enabled": False},
        "surface": {
            "emoji_template": "{emoji}\n{prompt}",
            "neutral_template": "{prompt}",
            "system_prompt": None,
        },
    }


def _portable_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _manifest_arm_rows(arms: Any, scope: str) -> dict[str, Mapping[str, Any]]:
    _require(isinstance(arms, Mapping), "Manifest arms must be a mapping")
    values = arms.get(scope)
    if isinstance(values, Mapping):
        rows = {
            str(family): row
            for family, row in values.items()
            if isinstance(row, Mapping)
        }
    elif isinstance(values, list):
        rows = {
            str(row.get("family", row.get("role"))): row
            for row in values
            if isinstance(row, Mapping)
        }
    else:
        raise AuditError(f"Manifest has no {scope} arm")
    _require(set(rows) == set(FAMILY_ORDER), f"Manifest {scope} family roles differ")
    return rows


def _binding_path(row: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if isinstance(value, str):
            return value
        if isinstance(value, Mapping) and isinstance(value.get("path"), str):
            return str(value["path"])
    return None


def _validate_manifest(
    root: Path,
    manifest_path: Path,
    expected_input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    expected_manifest_path = root / MANIFEST_RELATIVE
    _require(not manifest_path.is_symlink(), "Freeze manifest must not be a symlink")
    _require(
        manifest_path.resolve() == expected_manifest_path.resolve(),
        f"Freeze manifest path differs: {_portable_relative(manifest_path, root)}",
    )
    _require(manifest_path.is_file(), f"Missing manifest: {manifest_path.name}")
    manifest = _read_json_object(manifest_path, "E2 manifest")
    _require(manifest.get("schema_version") == 1, "Manifest schema differs")
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Manifest protocol ID differs")
    if "manifest_id" in manifest:
        _require(manifest["manifest_id"] == MANIFEST_ID, "Manifest ID differs")
    _require(
        not _contains_forbidden_path(manifest),
        "Protected target appears in manifest",
    )

    for section, expected in (
        ("environment", EXPECTED_ENVIRONMENT),
        ("model_artifact", EXPECTED_MODEL_ARTIFACT),
        ("architecture", EXPECTED_ARCHITECTURE),
    ):
        declared_section = manifest.get(section)
        _require(
            isinstance(declared_section, Mapping),
            f"Manifest {section} binding is missing",
        )
        for key, value in expected.items():
            _require(
                declared_section.get(key) == value,
                f"Manifest {section}.{key} differs",
            )

    files = manifest.get("files")
    _require(isinstance(files, list) and files, "Manifest files list is empty")
    declared: dict[str, str] = {}
    verified: list[dict[str, Any]] = []
    root_resolved = root.resolve()
    for index, row in enumerate(files):
        _require(isinstance(row, Mapping), f"Manifest file row {index} is invalid")
        relative = row.get("path")
        expected = row.get("sha256")
        _require(isinstance(relative, str), f"Manifest file row {index} has no path")
        _require(
            isinstance(expected, str)
            and len(expected) == 64
            and all(char in "0123456789abcdef" for char in expected.lower()),
            f"Manifest file row {index} has an invalid SHA-256",
        )
        pure = PurePosixPath(relative)
        _require(
            not pure.is_absolute() and ".." not in pure.parts,
            f"Unsafe manifest path: {relative}",
        )
        normalized = pure.as_posix()
        _require(
            normalized not in FORBIDDEN_TARGET_PATHS
            and pure.name not in FORBIDDEN_TARGET_NAMES,
            f"Protected target must not be a manifest file input: {normalized}",
        )
        _require(normalized not in declared, f"Duplicate manifest path: {normalized}")
        path = root / normalized
        _require(
            not path.is_symlink(), f"Manifest file must not be a symlink: {normalized}"
        )
        _require(path.is_file(), f"Missing manifest file: {normalized}")
        _require(
            path.resolve().is_relative_to(root_resolved),
            f"Manifest file escapes the repository: {normalized}",
        )
        actual = _sha256(path)
        _require(actual == expected.lower(), f"Manifest SHA-256 mismatch: {normalized}")
        declared[normalized] = actual
        verified.append(
            {"path": normalized, "sha256": actual, "bytes": path.stat().st_size}
        )

    for relative, actual in expected_input_hashes.items():
        _require(
            relative in declared, f"Manifest does not bind required input: {relative}"
        )
        _require(
            declared[relative] == actual, f"Manifest input hash differs: {relative}"
        )

    shared = manifest.get("shared_inputs")
    _require(isinstance(shared, Mapping), "Manifest shared_inputs is missing")
    shared_rows = [row for row in shared.values() if isinstance(row, Mapping)]
    for relative, actual in (
        (TARGET_RELATIVE.as_posix(), TARGET_SHA256),
        (SOURCE_RELATIVE.as_posix(), SOURCE_SHA256),
    ):
        matches = [
            row for row in shared_rows if _binding_path(row, "path", "file") == relative
        ]
        _require(
            len(matches) == 1, f"Manifest shared input binding differs: {relative}"
        )
        declared_hash = matches[0].get("sha256", matches[0].get("file_sha256"))
        _require(
            declared_hash == actual, f"Manifest shared input SHA differs: {relative}"
        )

    arms = manifest.get("arms")
    for scope in SCOPE_ORDER:
        for family, row in _manifest_arm_rows(arms, scope).items():
            expected_config = CONFIG_PATHS[(scope, family)].as_posix()
            expected_panel = (
                FULL_PANEL_PATHS[family]
                if scope == "full50"
                else CORE_PANEL_PATHS[family]
            ).as_posix()
            _require(
                _binding_path(row, "config_path", "config") == expected_config,
                f"Manifest config role differs for {scope}/{family}",
            )
            _require(
                _binding_path(row, "panel_path", "panel") == expected_panel,
                f"Manifest panel role differs for {scope}/{family}",
            )

    fixed = manifest.get("fixed_cell")
    _require(isinstance(fixed, Mapping), "Manifest fixed_cell is missing")
    backend = fixed.get("backend")
    _require(isinstance(backend, Mapping), "Manifest fixed backend is missing")
    for key, value in {
        "kind": "transformers",
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "device": "mps",
        "dtype": "float32",
    }.items():
        _require(backend.get(key) == value, f"Manifest fixed backend {key} differs")
    layers = fixed.get("layers", fixed.get("capture_layers"))
    if layers is None and isinstance(fixed.get("capture"), Mapping):
        layers = fixed["capture"].get("layers")
    _require(layers == [5, 11], "Manifest fixed layers differ")
    _require(
        isinstance(manifest.get("analysis"), Mapping),
        "Manifest analysis binding is missing",
    )
    analysis = manifest["analysis"]
    _require(
        analysis.get("analysis_id") == PROTOCOL_ID,
        "Manifest analysis ID differs",
    )
    _require(
        analysis.get("script_path") == ANALYZER_RELATIVE.as_posix(),
        "Manifest analyzer path differs",
    )
    _require(
        analysis.get("script_sha256") == declared[ANALYZER_RELATIVE.as_posix()],
        "Manifest analyzer SHA-256 differs",
    )
    dependency = analysis.get("e1_math_dependency")
    _require(
        isinstance(dependency, Mapping),
        "Manifest E1 math dependency binding is missing",
    )
    _require(
        dependency.get("path") == E1_MATH_RELATIVE.as_posix(),
        "Manifest E1 math dependency path differs",
    )
    _require(
        dependency.get("sha256") == declared[E1_MATH_RELATIVE.as_posix()],
        "Manifest E1 math dependency SHA-256 differs",
    )

    return {
        "present": True,
        "path": _portable_relative(manifest_path, root),
        "sha256": _sha256(manifest_path),
        "verified_file_count": len(verified),
        "verified_files": verified,
    }


def load_static_authority(
    root: Path,
    *,
    manifest_path: Path | None = None,
) -> StaticAuthority:
    root = root.resolve()
    target_path = root / TARGET_RELATIVE
    source_path = root / SOURCE_RELATIVE
    _require(target_path.is_file(), "Missing prestage target file")
    _require(source_path.is_file(), "Missing source-wrapper file")
    _require(_sha256(target_path) == TARGET_SHA256, "Prestage target SHA-256 differs")
    _require(_sha256(source_path) == SOURCE_SHA256, "Source-wrapper SHA-256 differs")
    _require(
        _selected_lines_sha256(target_path, 24) == TARGET_FIRST24_SHA256,
        "First-24 prestage slice SHA-256 differs",
    )

    target_rows = _read_jsonl(target_path, "prestage targets")
    _require(len(target_rows) == 32, "Prestage target row count differs")
    selected_targets = target_rows[:24]
    _require(
        tuple(row.get("id") for row in selected_targets) == TARGET_IDS,
        "First-24 prestage target IDs differ",
    )
    _require(
        tuple(row.get("group") for row in selected_targets) == TARGET_GROUPS,
        "First-24 prestage target groups differ",
    )
    _require(
        all(
            isinstance(row.get("prompt"), str) and row["prompt"]
            for row in selected_targets
        ),
        "A selected prestage target has no prompt",
    )

    wrappers = _read_jsonl(source_path, "source wrappers")
    _require(len(wrappers) == 16, "Source-wrapper row count differs")
    _require(
        tuple(row.get("id") for row in wrappers) == WRAPPER_IDS, "Wrapper IDs differ"
    )
    _require(
        all(
            isinstance(row.get("template"), str)
            and row["template"].count("{emoji}") == 1
            for row in wrappers
        ),
        "A source wrapper does not contain exactly one emoji placeholder",
    )

    panels: dict[str, dict[str, list[dict[str, Any]]]] = {
        scope: {} for scope in SCOPE_ORDER
    }
    panel_records: list[dict[str, Any]] = []
    for family in FAMILY_ORDER:
        full_path = root / FULL_PANEL_PATHS[family]
        core_path = root / CORE_PANEL_PATHS[family]
        _require(full_path.is_file(), f"Missing full panel: {family}")
        _require(core_path.is_file(), f"Missing core panel: {family}")
        _require(
            _sha256(full_path) == FULL_PANEL_SHA256[family],
            f"Frozen full panel SHA-256 differs: {family}",
        )
        full_items = _panel_items(full_path, family, range(10))
        core_items = _panel_items(core_path, family, range(3, 10))
        _require(
            core_items == full_items[3:10],
            f"Core panel is not an exact subset: {family}",
        )
        panels["full50"][family] = full_items
        panels["core35"][family] = core_items
        panel_records.extend(
            [
                {
                    "scope": "full50",
                    "family": family,
                    "path": FULL_PANEL_PATHS[family].as_posix(),
                    "sha256": _sha256(full_path),
                    "item_count": 10,
                },
                {
                    "scope": "core35",
                    "family": family,
                    "path": CORE_PANEL_PATHS[family].as_posix(),
                    "sha256": _sha256(core_path),
                    "item_count": 7,
                },
            ]
        )

    all_full_glyphs = [
        item["glyph"] for family in FAMILY_ORDER for item in panels["full50"][family]
    ]
    _require(
        len(all_full_glyphs) == len(set(all_full_glyphs)) == 50, "Full glyphs overlap"
    )
    all_core_glyphs = [
        item["glyph"] for family in FAMILY_ORDER for item in panels["core35"][family]
    ]
    _require(
        len(all_core_glyphs) == len(set(all_core_glyphs)) == 35, "Core glyphs overlap"
    )

    config_records: list[dict[str, Any]] = []
    required_hashes: dict[str, str] = {
        TARGET_RELATIVE.as_posix(): TARGET_SHA256,
        SOURCE_RELATIVE.as_posix(): SOURCE_SHA256,
    }
    for row in panel_records:
        required_hashes[row["path"]] = row["sha256"]
    for scope in SCOPE_ORDER:
        condition_count = 10 if scope == "full50" else 7
        for family in FAMILY_ORDER:
            relative = CONFIG_PATHS[(scope, family)]
            path = root / relative
            _require(path.is_file(), f"Missing frozen config: {relative}")
            config = _read_yaml(path, f"{scope}/{family} config")
            _require(
                not _contains_forbidden_path(config),
                f"Config names a protected bank: {relative}",
            )
            _require(
                config == _expected_config(scope, family), f"Config differs: {relative}"
            )
            digest = _sha256(path)
            required_hashes[relative.as_posix()] = digest
            config_records.append(
                {
                    "scope": scope,
                    "family": family,
                    "path": relative.as_posix(),
                    "sha256": digest,
                    "run_name": _nested(config, "run", "name"),
                    "panel_path": (
                        FULL_PANEL_PATHS[family]
                        if scope == "full50"
                        else CORE_PANEL_PATHS[family]
                    ).as_posix(),
                    "expected_calls": _expected_plan(condition_count),
                }
            )

    critical_records: list[dict[str, Any]] = []
    for relative in CRITICAL_FILE_PATHS:
        path = root / relative
        _require(path.is_file(), f"Missing critical freeze file: {relative}")
        _require(
            not path.is_symlink(), f"Critical freeze file is a symlink: {relative}"
        )
        digest = _sha256(path)
        required_hashes[relative.as_posix()] = digest
        critical_records.append(
            {
                "path": relative.as_posix(),
                "sha256": digest,
                "bytes": path.stat().st_size,
            }
        )

    manifest_report: dict[str, Any] = {"present": False}
    if manifest_path is not None:
        manifest_report = _validate_manifest(root, manifest_path, required_hashes)

    report = {
        "config_count": len(config_records),
        "configs": config_records,
        "panel_count": len(panel_records),
        "panels": panel_records,
        "critical_file_count": len(critical_records),
        "critical_files": critical_records,
        "shared_inputs": {
            "target": {
                "path": TARGET_RELATIVE.as_posix(),
                "file_sha256": TARGET_SHA256,
                "file_record_count": len(target_rows),
                "selected_record_count": 24,
                "selected_slice_sha256": TARGET_FIRST24_SHA256,
                "ordered_ids": list(TARGET_IDS),
                "ordered_groups": list(TARGET_GROUPS),
                "prompt_sha256": [
                    hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
                    for row in selected_targets
                ],
            },
            "source": {
                "path": SOURCE_RELATIVE.as_posix(),
                "file_sha256": SOURCE_SHA256,
                "file_record_count": len(wrappers),
                "selected_record_count": 16,
                "selected_slice_sha256": SOURCE_SHA256,
                "ordered_ids": list(WRAPPER_IDS),
                "template_sha256": [
                    hashlib.sha256(row["template"].encode("utf-8")).hexdigest()
                    for row in wrappers
                ],
            },
        },
        "planned_counts": {
            "full50": {
                "per_family": _expected_plan(10),
                "all_families_forward_calls": 9_880,
                "all_families_intervention_rows": 8_880,
            },
            "core35": {
                "per_family": _expected_plan(7),
                "all_families_forward_calls": 7_480,
                "all_families_intervention_rows": 6_720,
            },
            "combined_forward_calls": 17_360,
            "combined_intervention_rows": 15_600,
        },
        "manifest": manifest_report,
        "protected_banks": {
            "paths": sorted(FORBIDDEN_TARGET_PATHS),
            "content_opened": False,
            "tokenized": False,
            "model_forward_count": 0,
        },
    }
    return StaticAuthority(root=root, panels=panels, wrappers=wrappers, report=report)


def _expected_raw_ids(item_id: str) -> tuple[int, ...]:
    if item_id in MERGED_TOKEN_EXCEPTIONS:
        return MERGED_TOKEN_EXCEPTIONS[item_id]
    family, raw_slot = item_id.rsplit("_slot_", 1)
    slot = int(raw_slot)
    return (EXPECTED_FIRST_TOKEN, FAMILY_MIDDLE_TOKEN[family], 239 + slot)


def _tokenize(tokenizer: Any, text: str) -> tuple[list[int], list[tuple[int, int]]]:
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_attention_mask=False,
        return_offsets_mapping=True,
    )
    ids = encoded.get("input_ids")
    offsets = encoded.get("offset_mapping")
    _require(
        isinstance(ids, list) and all(isinstance(value, int) for value in ids),
        "Tokenizer returned invalid IDs",
    )
    _require(
        isinstance(offsets, list) and len(offsets) == len(ids),
        "Tokenizer returned invalid offsets",
    )
    normalized: list[tuple[int, int]] = []
    for value in offsets:
        _require(
            isinstance(value, (list, tuple)) and len(value) == 2, "Invalid token offset"
        )
        normalized.append((int(value[0]), int(value[1])))
    try:
        decoded = tokenizer.decode(
            ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
    except TypeError:
        decoded = tokenizer.decode(ids, skip_special_tokens=False)
    _require(decoded == text, "Tokenizer decoded round trip differs")
    return [int(value) for value in ids], normalized


def _tokenizer_identity(tokenizer: Any) -> dict[str, Any]:
    class_name = type(tokenizer).__name__
    _require(class_name == TOKENIZER_CLASS, f"Tokenizer class differs: {class_name}")
    _require(bool(getattr(tokenizer, "is_fast", False)), "Tokenizer must be fast")
    _require(
        int(getattr(tokenizer, "vocab_size", -1)) == TOKENIZER_BASE_VOCAB_SIZE,
        "Tokenizer base vocabulary differs",
    )
    _require(len(tokenizer) == TOKENIZER_LENGTH, "Tokenizer total vocabulary differs")
    return {
        "model": MODEL_ID,
        "revision": MODEL_REVISION,
        "class": class_name,
        "is_fast": True,
        "base_vocab_size": TOKENIZER_BASE_VOCAB_SIZE,
        "total_length": TOKENIZER_LENGTH,
        "local_files_only": True,
        "add_special_tokens": False,
    }


def audit_tokenizer(tokenizer: Any, authority: StaticAuthority) -> dict[str, Any]:
    identity = _tokenizer_identity(tokenizer)
    items = [
        item for family in FAMILY_ORDER for item in authority.panels["full50"][family]
    ]
    core_ids = {
        item["id"]
        for family in FAMILY_ORDER
        for item in authority.panels["core35"][family]
    }
    raw_records: list[dict[str, Any]] = []
    raw_ids: dict[str, tuple[int, ...]] = {}
    for item in items:
        ids, offsets = _tokenize(tokenizer, item["glyph"])
        expected = _expected_raw_ids(item["id"])
        _require(tuple(ids) == expected, f"Raw token IDs differ for {item['id']}")
        _require(
            offsets == [(0, 1)] * len(ids),
            f"Raw token offsets differ for {item['id']}",
        )
        raw_ids[item["id"]] = tuple(ids)
        raw_records.append(
            {
                "id": item["id"],
                "glyph": item["glyph"],
                "scope": "core35" if item["id"] in core_ids else "full50_only",
                "token_ids": ids,
                "token_count": len(ids),
                "merged_exception": item["id"] in MERGED_TOKEN_EXCEPTIONS,
                "decoded_round_trip_verified": True,
                "utf8_hex": item["glyph"].encode("utf-8").hex(),
                "codepoint": f"U+{ord(item['glyph']):04X}",
            }
        )

    _require(
        sum(len(value) == 3 for value in raw_ids.values()) == 47,
        "Expected 47 three-token glyphs",
    )
    _require(
        sum(len(value) == 2 for value in raw_ids.values()) == 3,
        "Expected three merged glyphs",
    )
    _require(
        all(len(raw_ids[item_id]) == 3 for item_id in core_ids),
        "Core35 is not three-token",
    )

    wrapper_records: list[dict[str, Any]] = []
    for wrapper in authority.wrappers:
        profiles: list[dict[str, Any]] = []
        outside_reference: tuple[int, ...] | None = None
        core_counts: set[int] = set()
        core_positions: set[tuple[int, ...]] = set()
        ordinary_count: int | None = None
        for item in items:
            text = wrapper["template"].format(emoji=item["glyph"])
            ids, offsets = _tokenize(tokenizer, text)
            start = text.index(item["glyph"])
            stop = start + 1
            positions = tuple(
                index
                for index, (left, right) in enumerate(offsets)
                if left < stop and right > start
            )
            _require(positions, f"No emoji token span for {wrapper['id']}/{item['id']}")
            _require(
                all(offsets[index] == (start, stop) for index in positions),
                f"Emoji token offset crosses wrapper text for {wrapper['id']}/{item['id']}",
            )
            span_ids = tuple(ids[index] for index in positions)
            _require(
                span_ids == raw_ids[item["id"]],
                f"Wrapped emoji tokens differ for {wrapper['id']}/{item['id']}",
            )
            outside = tuple(
                value for index, value in enumerate(ids) if index not in positions
            )
            if outside_reference is None:
                outside_reference = outside
            _require(
                outside == outside_reference,
                f"Outside wrapper tokens vary at {wrapper['id']}/{item['id']}",
            )
            if item["id"] not in MERGED_TOKEN_EXCEPTIONS and ordinary_count is None:
                ordinary_count = len(ids)
            if item["id"] in core_ids:
                core_counts.add(len(ids))
                core_positions.add(positions)
            profiles.append(
                {
                    "item_id": item["id"],
                    "token_count": len(ids),
                    "emoji_token_positions": list(positions),
                    "emoji_token_ids": list(span_ids),
                    "last_nonpad_position": len(ids) - 1,
                    "decoded_round_trip_verified": True,
                    "outside_token_ids_sha256": hashlib.sha256(
                        json.dumps(outside).encode("utf-8")
                    ).hexdigest(),
                }
            )
        _require(ordinary_count is not None, f"No ordinary profile for {wrapper['id']}")
        for profile in profiles:
            expected_count = ordinary_count - (
                1 if profile["item_id"] in MERGED_TOKEN_EXCEPTIONS else 0
            )
            _require(
                profile["token_count"] == expected_count,
                f"Wrapper token-count rule differs for {wrapper['id']}/{profile['item_id']}",
            )
        _require(len(core_counts) == 1, f"Core wrapper counts differ: {wrapper['id']}")
        _require(
            len(core_positions) == 1, f"Core wrapper positions differ: {wrapper['id']}"
        )
        wrapper_records.append(
            {
                "wrapper_id": wrapper["id"],
                "ordinary_token_count": ordinary_count,
                "merged_exception_token_count": ordinary_count - 1,
                "core35_token_count": next(iter(core_counts)),
                "core35_emoji_token_positions": list(next(iter(core_positions))),
                "outside_tokens_identical_across_full50": True,
                "profiles": profiles,
            }
        )

    return {
        "identity": identity,
        "raw": raw_records,
        "wrappers": wrapper_records,
        "rules": {
            "full50_raw_token_count_distribution": {"2": 3, "3": 47},
            "merged_exceptions": {
                key: list(value) for key, value in MERGED_TOKEN_EXCEPTIONS.items()
            },
            "core35_item_count": 35,
            "core35_exact_form": "[9468, family_middle_token, 239 + slot]",
            "core35_slots": list(range(3, 10)),
            "core35_suffix_tokens": list(range(242, 249)),
            "family_middle_tokens": FAMILY_MIDDLE_TOKEN,
            "wrapper_outside_tokens_identical": True,
            "wrapper_core_token_count_and_position_isomorphic": True,
            "decoded_round_trips_verified": True,
        },
        "counts": {
            "raw_glyphs_verified": 50,
            "full50_wrapper_profiles_verified": 800,
            "core35_wrapper_profiles_verified": 560,
            "wrapper_count": 16,
        },
    }


def _assemble_report(
    authority: StaticAuthority,
    *,
    tokenizer: Any,
    runtime_authority: Mapping[str, Any],
    git_authority: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_runtime_authority(runtime_authority)
    _validate_git_authority(git_authority)
    tokenization = audit_tokenizer(tokenizer, authority)
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "passed",
        "audit_role": "model_free_static_artifact_config_and_tokenizer_preflight",
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "p2_content_opened": False,
        "c1_content_opened": False,
        "audited_commit": git_authority["audited_commit"],
        "git_authority": dict(git_authority),
        "environment": dict(runtime_authority["environment"]),
        "model_artifact": dict(runtime_authority["model_artifact"]),
        "architecture": dict(runtime_authority["architecture"]),
        "runtime_parameter_dtype": {
            "measured_in_preflight": False,
            "measurement_stage": runtime_authority[
                "runtime_parameter_dtype_measurement_stage"
            ],
        },
        "static": authority.report,
        "tokenization": tokenization,
        "authorization": {
            "frozen_grid_execution_authorized": True,
            "analysis_authorized_before_grid_completion": False,
            "p2_use_authorized": False,
            "c1_use_authorized": False,
            "causal_claim_authorized": False,
        },
        "claim_boundary": (
            "Environment/artifact/configuration/tokenizer qualification for one "
            "frozen exploratory Transformers/MPS transport grid; no language model "
            "is loaded and no semantic, mechanistic, causal, confirmatory, or "
            "cross-model result is produced."
        ),
    }


def audit_suite(
    root: Path,
    *,
    tokenizer: Any,
    runtime_authority: Mapping[str, Any],
    git_authority: Mapping[str, Any],
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    authority = load_static_authority(root, manifest_path=manifest_path)
    return _assemble_report(
        authority,
        tokenizer=tokenizer,
        runtime_authority=runtime_authority,
        git_authority=git_authority,
    )


def _load_pinned_tokenizer() -> Any:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise AuditError(
            "transformers is required for the tokenizer-only audit"
        ) from exc
    return AutoTokenizer.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_files_only=True,
        trust_remote_code=False,
    )


def atomic_no_overwrite(path: Path, payload: Mapping[str, Any]) -> None:
    """Publish complete JSON atomically without replacing an existing receipt."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_json_bytes(dict(payload)))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise AuditError(
                f"Refusing to overwrite preflight receipt: {path.name}"
            ) from exc
        os.unlink(temporary)
        try:
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    parser.add_argument(
        "--manifest",
        type=Path,
        help=(f"frozen protocol manifest (defaults to {MANIFEST_RELATIVE.as_posix()})"),
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repo_root.resolve()
    manifest = args.manifest or MANIFEST_RELATIVE
    if not manifest.is_absolute():
        manifest = root / manifest
    output = args.output or (root / DEFAULT_OUTPUT_RELATIVE)
    if not output.is_absolute():
        output = root / output
    try:
        # Static authority is deliberately resolved before importing Transformers.
        authority = load_static_authority(root, manifest_path=manifest)
        git_authority = collect_git_authority(root)
        runtime_authority = audit_runtime_authority()
        tokenizer = _load_pinned_tokenizer()
        report = _assemble_report(
            authority,
            tokenizer=tokenizer,
            runtime_authority=runtime_authority,
            git_authority=git_authority,
        )
        atomic_no_overwrite(output, report)
    except AuditError as exc:
        print(f"audit_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"status": "passed", "output": _portable_relative(output, root)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
