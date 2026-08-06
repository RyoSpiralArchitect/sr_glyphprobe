#!/usr/bin/env python3
"""Build the compact, fail-closed Milestone 2 public evidence bundle.

The builder never runs a model.  It copies the established compact 17-file
run surface when each file was produced, records protocol-disabled compact
tables explicitly, and hashes the large ledgers/NPZ arrays that stay local.
Exploratory matched controls are required.  The P2 target family and the
independent-source family are optional but all-or-none.  The two frozen
secondary diagnostics are always accounted for as executed or unexecuted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import yaml


COMPACT_RUN_FILES = (
    "capabilities.json",
    "cross_seed_fingerprint_summary.jsonl",
    "direction_replicates.json",
    "dose_response_summary.jsonl",
    "fingerprint_summary.jsonl",
    "plan.json",
    "receipt.json",
    "report.md",
    "resolved_config.yaml",
    "resolved_inputs.json",
    "scalar_balance_summary.jsonl",
    "sign_flip_summary.jsonl",
    "source_item_metrics.jsonl",
    "source_layer_metrics.jsonl",
    "summary.json",
    "target_baselines.jsonl",
    "tokenization.jsonl",
)

PROTOCOL_DISABLED_COMPACT_FILES = frozenset(
    {"dose_response_summary.jsonl", "sign_flip_summary.jsonl"}
)
OMITTED_LARGE_FILES = (
    "interventions.jsonl",
    "directions.npz",
    "source_activations.npz",
    "target_baselines.npz",
)
RUN_ROLES = ("primary", "matched_null_a", "matched_null_b", "matched_null_c")
CONFIRMATORY_FAMILIES = ("p2", "independent_source")
DIAGNOSTIC_IDS = (
    "suffix_matched_middle_shift",
    "prefix_homogeneous_colored_shapes",
)
EXPECTED_PANEL_FILES = {
    "primary": "colored_shapes.yaml",
    "matched_null_a": "m2_matched_null_a.yaml",
    "matched_null_b": "m2_matched_null_b.yaml",
    "matched_null_c": "m2_matched_null_c.yaml",
    "suffix_matched_middle_shift": "m2_suffix_matched_middle_shift.yaml",
    "prefix_homogeneous_colored_shapes": "m2_prefix_homogeneous_colored_shapes.yaml",
}
EXPECTED_SOURCE_FILES = {
    "p2": "source_wrappers.jsonl",
    "independent_source": "milestone2_independent_source_wrappers_v1.jsonl",
}
EXPLORATORY_CONFIG_FILES = {
    "primary": "configs/v1_mlx_standard.yaml",
    "matched_null_a": "configs/m2_matched_null_a_mlx.yaml",
    "matched_null_b": "configs/m2_matched_null_b_mlx.yaml",
    "matched_null_c": "configs/m2_matched_null_c_mlx.yaml",
}
DIAGNOSTIC_CONFIG_FILES = {
    "suffix_matched_middle_shift": "configs/m2_suffix_matched_middle_shift_mlx.yaml",
    "prefix_homogeneous_colored_shapes": "configs/m2_prefix_homogeneous_colored_shapes_mlx.yaml",
}
EXPLORATORY_ANALYSIS_DIMS = (96, 48, 32, 24)
EXPLORATORY_FOLD_DIMS = (48, 32, 24)
FINGERPRINT_SOURCE_DIM = 96
FINGERPRINT_SEED = 8_675_309
FINGERPRINT_CELL_COUNT = 36
PROTOCOL_ID = "glyphprobe-m2-tokenization-controls-v1"
CLAIM_BOUNDARY = "pre-causal-activation-screen"
DEPENDENCE_ANALYSIS_ID = "glyphprobe-m2-posthoc-dependence-sensitivity-v1"
DEPENDENCE_ANALYZER_FILE = "analyze_m2_dependence_sensitivity_v1.py"
FROZEN_CONFIRMATORY_ANALYZER_FILE = "analyze_m2_confirmatory.py"
DEPENDENCE_BOOTSTRAP_ROWS = 20_000
PINNED_PREREGISTRATION_MANIFEST_SHA256 = (
    "2beb2e6547c3ac3022356f6c6345f33e7eebf255a458f7febc51a826d0357bf5"
)
PINNED_PREREGISTRATION_AUDIT_SHA256 = (
    "015df5ad0d8bbeb6c01505e53a09833241079957d871420fc5cf42ff02683f48"
)
PINNED_PARITY_RECEIPT_SHA256 = (
    "98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679"
)

_URI_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9+.-]*):/{2,}[^\s\"'<>()[\]]*")
_POSIX_ABSOLUTE_RE = re.compile(r"(?<![A-Za-z0-9_./\\])/(?!/)(?=[^\s/])")
_POSIX_DOUBLE_SLASH_RE = re.compile(r"(?<![A-Za-z0-9_./\\])//(?=[^/\s]+/[^/\s]+)")
_WINDOWS_DRIVE_ABSOLUTE_RE = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]+(?=[^\\/\s])"
)
_WINDOWS_UNC_ABSOLUTE_RE = re.compile(r"(?<!\\)\\\\[^\\/\s]+[\\/][^\\/\s]+")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ConfirmatoryFamily:
    runs: Mapping[str, Path]
    analysis_dir: Path


@dataclass(frozen=True)
class InputBinding:
    authority: str
    config_path: str
    expected_inputs: Mapping[str, str]


@dataclass(frozen=True)
class RunEvidence:
    run_id: str
    run_seal: str
    compact_files: tuple[Path, ...]
    not_produced_compact_files: Mapping[str, str]
    omitted_large_files: Mapping[str, Mapping[str, Any]]
    file_sha256: Mapping[str, str]
    input_binding: InputBinding


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_receipt(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": _sha256(path)}


def _jsonl_receipt(path: Path) -> dict[str, Any]:
    digest = hashlib.sha256()
    row_count = 0
    with path.open("rb") as handle:
        for line in handle:
            digest.update(line)
            if line.strip():
                row_count += 1
    return {
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "row_count": row_count,
    }


def _iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(key)
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item)


def _text_fragments(path: Path, text: str) -> Iterator[str]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        yield from _iter_strings(json.loads(text))
    elif suffix == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                yield from _iter_strings(json.loads(line))
    elif suffix in {".yaml", ".yml"}:
        for document in yaml.safe_load_all(text):
            yield from _iter_strings(document)
    else:
        yield text


def _contains_local_absolute_path(text: str) -> bool:
    if text.strip() == "/" or re.fullmatch(r"[A-Za-z]:[\\/]+", text.strip()):
        return True

    file_uri_found = False

    def mask_uri(match: re.Match[str]) -> str:
        nonlocal file_uri_found
        if match.group(1).lower() == "file":
            file_uri_found = True
        return " " * len(match.group(0))

    without_portable_uris = _URI_RE.sub(mask_uri, text)
    if file_uri_found:
        return True
    return any(
        pattern.search(without_portable_uris) is not None
        for pattern in (
            _POSIX_ABSOLUTE_RE,
            _POSIX_DOUBLE_SLASH_RE,
            _WINDOWS_DRIVE_ABSOLUTE_RE,
            _WINDOWS_UNC_ABSOLUTE_RE,
        )
    )


def _assert_public_safe(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing to publish a symlink: {path}")
    if path.suffix.lower() not in {".json", ".jsonl", ".md", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8")
    if any(
        _contains_local_absolute_path(fragment)
        for fragment in _text_fragments(path, text)
    ):
        raise ValueError(f"Refusing to publish a local absolute path from {path}")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _nested(value: Mapping[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            raise ValueError(f"Missing required configuration field: {'.'.join(keys)}")
        current = current[key]
    return current


def _validate_roles(runs: Mapping[str, Path], label: str) -> None:
    observed = set(runs)
    expected = set(RUN_ROLES)
    if observed != expected:
        raise ValueError(
            f"{label} must provide exactly {list(RUN_ROLES)}; "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )
    resolved = [Path(runs[role]).resolve() for role in RUN_ROLES]
    if len(set(resolved)) != len(resolved):
        raise ValueError(f"{label} run directories must be distinct")


def _relative_repo_path(repo_root: Path, path: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"{label} resolves outside the preregistration repository: {path}"
        ) from exc


def _load_preregistration_authority(
    *,
    preregistration_manifest: Path,
    preregistration_audit: Path,
    parity_sha256: str,
) -> tuple[Path, dict[str, str], dict[str, dict[str, Any]], str, str]:
    manifest_path = Path(preregistration_manifest).resolve()
    audit_path = Path(preregistration_audit).resolve()
    _assert_public_safe(manifest_path)
    _assert_public_safe(audit_path)
    manifest = _load_json_object(manifest_path, "Milestone 2 preregistration manifest")
    audit = _load_json_object(audit_path, "Milestone 2 preregistration audit")
    manifest_sha256 = _sha256(manifest_path)
    audit_sha256 = _sha256(audit_path)
    if manifest_sha256 != PINNED_PREREGISTRATION_MANIFEST_SHA256:
        raise ValueError("Supplied preregistration manifest is not the pinned public v1 freeze")
    if audit_sha256 != PINNED_PREREGISTRATION_AUDIT_SHA256:
        raise ValueError("Supplied preregistration audit is not the pinned public v1 audit")
    if manifest.get("manifest_id") != "milestone2_preregistration_v1":
        raise ValueError("Unexpected Milestone 2 preregistration manifest ID")
    if manifest.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Preregistration manifest protocol ID mismatch")
    if audit.get("status") != "pass" or audit.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Preregistration audit must have status pass for protocol v1")
    if audit.get("manifest_sha256") != manifest_sha256:
        raise ValueError("Preregistration audit does not bind the supplied manifest")
    if audit.get("mlx_validation_receipt_sha256") != parity_sha256:
        raise ValueError("Preregistration audit does not bind the supplied parity receipt")

    # The frozen manifest is at data/manifests/<name>.json.  Resolve all frozen
    # paths against its repository root, then verify the current bytes before
    # using any hash as role-binding authority.
    repo_root = manifest_path.parents[2]
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise ValueError("Preregistration manifest must contain frozen files")
    frozen_files: dict[str, str] = {}
    for row in raw_files:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("path"), str)
            or not isinstance(row.get("sha256"), str)
            or _SHA256_RE.fullmatch(row["sha256"]) is None
        ):
            raise ValueError("Malformed frozen file row in preregistration manifest")
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Frozen manifest path must be repository-relative: {relative}")
        key = relative.as_posix()
        if key in frozen_files:
            raise ValueError(f"Duplicate frozen path in preregistration manifest: {key}")
        source = repo_root / relative
        if not source.is_file() or _sha256(source) != row["sha256"]:
            raise ValueError(f"Frozen preregistration file hash mismatch: {key}")
        frozen_files[key] = row["sha256"]

    if frozen_files.get("validation/mlx_gpt2_parity/receipt.json") != parity_sha256:
        raise ValueError("Frozen manifest parity hash does not match supplied receipt")
    p2_rows = audit.get("p2_configs")
    if not isinstance(p2_rows, list) or len(p2_rows) != 8:
        raise ValueError("Preregistration audit must bind exactly eight P2 configs")
    arm_mapping: dict[str, dict[str, Any]] = {}
    for row in p2_rows:
        if not isinstance(row, dict) or not isinstance(row.get("arm"), str):
            raise ValueError("Malformed P2 arm mapping in preregistration audit")
        if row["arm"] in arm_mapping:
            raise ValueError(f"Duplicate P2 arm in preregistration audit: {row['arm']}")
        arm_mapping[row["arm"]] = row
    return repo_root, frozen_files, arm_mapping, manifest_sha256, audit_sha256


def _config_reference(
    *, repo_root: Path, config_path: Path, raw_reference: Any, label: str
) -> str:
    if not isinstance(raw_reference, str) or not raw_reference:
        raise ValueError(f"Frozen config has no valid {label} path: {config_path}")
    return _relative_repo_path(repo_root, config_path.parent / raw_reference, label)


def _input_binding_for_config(
    *,
    repo_root: Path,
    frozen_files: Mapping[str, str],
    config_relative: str,
    parity_sha256: str,
    authority: str,
    audited_arm: Mapping[str, Any] | None = None,
) -> InputBinding:
    config_path = repo_root / config_relative
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Frozen config must be a mapping: {config_path}")
    panel_relative = _config_reference(
        repo_root=repo_root,
        config_path=config_path,
        raw_reference=_nested(config, "panel", "file"),
        label="panel",
    )
    source_relative = _config_reference(
        repo_root=repo_root,
        config_path=config_path,
        raw_reference=_nested(config, "source", "wrappers_file"),
        label="source wrapper",
    )
    target_relative = _config_reference(
        repo_root=repo_root,
        config_path=config_path,
        raw_reference=_nested(config, "targets", "cases_file"),
        label="target bank",
    )
    if audited_arm is not None:
        expected_audit = {
            "path": config_relative,
            "panel": str(_nested(config, "panel", "file")),
            "source": str(_nested(config, "source", "wrappers_file")),
            "targets": str(_nested(config, "targets", "cases_file")),
        }
        observed_audit = {key: audited_arm.get(key) for key in expected_audit}
        if observed_audit != expected_audit:
            raise ValueError(
                f"Preregistration arm mapping disagrees with frozen config {config_relative}"
            )

    config_sha256 = frozen_files.get(config_relative)
    if config_sha256 is None:
        if config_relative != "configs/v1_mlx_standard.yaml":
            raise ValueError(
                "Config is not frozen by the preregistration manifest: "
                f"{config_relative}"
            )
        config_sha256 = _sha256(config_path)
    expected_references = (
        ("input_00", config_relative, config_sha256),
        ("input_01", "validation/mlx_gpt2_parity/receipt.json", parity_sha256),
        ("input_02", panel_relative, frozen_files.get(panel_relative)),
        ("input_03", source_relative, frozen_files.get(source_relative)),
        ("input_04", target_relative, frozen_files.get(target_relative)),
    )
    expected_inputs: dict[str, str] = {}
    for position, relative, expected_sha256 in expected_references:
        if expected_sha256 is None:
            raise ValueError(
                f"Run input is not frozen by the preregistration manifest: {relative}"
            )
        source = repo_root / relative
        if not source.is_file() or _sha256(source) != expected_sha256:
            raise ValueError(f"Run input hash does not match frozen bytes: {relative}")
        expected_inputs[f"{position}:{source.name}"] = expected_sha256
    return InputBinding(
        authority=authority,
        config_path=config_relative,
        expected_inputs=expected_inputs,
    )


def _validate_run(
    run_dir: Path,
    *,
    role: str,
    parity_sha256: str,
    input_binding: InputBinding,
    expected_source_file: str | None = None,
) -> RunEvidence:
    run_dir = Path(run_dir).resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(run_dir)
    receipt_path = run_dir / "receipt.json"
    summary_path = run_dir / "summary.json"
    config_path = run_dir / "resolved_config.yaml"
    receipt = _load_json_object(receipt_path, "run receipt")
    summary = _load_json_object(summary_path, "run summary")
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Resolved config must be a mapping: {config_path}")

    if receipt.get("status") != "complete":
        raise ValueError(f"Run receipt status must be complete: {run_dir}")
    run_id = receipt.get("run_id")
    if not isinstance(run_id, str) or run_dir.name != run_id:
        raise ValueError(f"Run directory name must match receipt run_id: {run_dir}")
    run_seal = receipt.get("run_seal")
    if not isinstance(run_seal, str) or not re.fullmatch(r"[0-9a-f]{16}", run_seal):
        raise ValueError(f"Run receipt must contain a 16-hex run_seal: {run_dir}")
    if receipt.get("claim_boundary") != CLAIM_BOUNDARY:
        raise ValueError(f"Run receipt claim boundary must remain pre-causal: {run_dir}")
    if not isinstance(receipt.get("finished_at"), str) or not receipt["finished_at"]:
        raise ValueError(f"Completed run receipt must contain finished_at: {run_dir}")
    if summary.get("causal_claim_authorized") is not False:
        raise ValueError(f"Run summary must keep causal_claim_authorized false: {run_dir}")
    if type(summary.get("error_count")) is not int or summary["error_count"] != 0:
        raise ValueError(f"Run summary error_count must be exactly zero: {run_dir}")
    if (run_dir / "errors.jsonl").exists():
        raise ValueError(f"Refusing to publish a run with errors.jsonl: {run_dir}")

    backend = receipt.get("backend")
    input_hashes = receipt.get("input_hashes")
    parity_validation = (receipt.get("model_receipt") or {}).get("parity_validation")
    if not isinstance(backend, dict) or backend.get("validation_receipt_sha256") != parity_sha256:
        raise ValueError(f"Run backend does not bind the supplied parity receipt: {run_dir}")
    if (
        not isinstance(input_hashes, dict)
        or list(input_hashes.values()).count(parity_sha256) != 1
    ):
        raise ValueError(f"Run input hashes must bind one supplied parity receipt: {run_dir}")
    if (
        not isinstance(parity_validation, dict)
        or parity_validation.get("validated") is not True
        or parity_validation.get("receipt_sha256") != parity_sha256
    ):
        raise ValueError(f"Run model receipt does not bind validated parity: {run_dir}")
    if input_hashes != dict(input_binding.expected_inputs):
        raise ValueError(
            f"Run input_00..04 paths/hashes do not match the preregistered arm mapping: {run_dir}"
        )
    if receipt.get("config_path") != Path(input_binding.config_path).name:
        raise ValueError(f"Run receipt config_path does not match its bound arm: {run_dir}")

    expected_panel = EXPECTED_PANEL_FILES[role]
    observed_panel = Path(str(_nested(config, "panel", "file"))).name
    if observed_panel != expected_panel:
        raise ValueError(
            f"Run role {role} requires panel {expected_panel}, observed {observed_panel}"
        )
    if expected_source_file is not None:
        observed_source = Path(str(_nested(config, "source", "wrappers_file"))).name
        if observed_source != expected_source_file:
            raise ValueError(
                f"Run family requires source {expected_source_file}, observed {observed_source}"
            )

    missing: dict[str, str] = {}
    compact_paths: list[Path] = []
    strengths = _nested(config, "intervention", "strengths")
    sign_flip = _nested(config, "controls", "sign_flip")
    for name in COMPACT_RUN_FILES:
        path = run_dir / name
        if path.is_file():
            _assert_public_safe(path)
            compact_paths.append(path)
            continue
        if name == "dose_response_summary.jsonl" and (
            not isinstance(strengths, list) or len([x for x in strengths if float(x) > 0]) < 3
        ):
            missing[name] = (
                "not produced because the frozen run has fewer than three positive strengths"
            )
            continue
        if name == "sign_flip_summary.jsonl" and sign_flip is False:
            missing[name] = (
                "not produced because sign-flip controls are disabled in the frozen config"
            )
            continue
        raise FileNotFoundError(path)

    omitted: dict[str, Mapping[str, Any]] = {}
    file_sha256 = {path.name: _sha256(path) for path in compact_paths}
    for name in OMITTED_LARGE_FILES:
        path = run_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        receipt_value = _jsonl_receipt(path) if path.suffix == ".jsonl" else _file_receipt(path)
        omitted[name] = receipt_value
        file_sha256[name] = str(receipt_value["sha256"])

    intervention_count = summary.get("intervention_record_count")
    ledger_count = omitted["interventions.jsonl"]["row_count"]
    if type(intervention_count) is not int or intervention_count != ledger_count:
        raise ValueError(
            f"Run summary intervention count does not match the local ledger: {run_dir}"
        )

    return RunEvidence(
        run_id=run_id,
        run_seal=run_seal,
        compact_files=tuple(compact_paths),
        not_produced_compact_files=missing,
        omitted_large_files=omitted,
        file_sha256=file_sha256,
        input_binding=input_binding,
    )


def _expected_exploratory_analysis_files() -> tuple[Path, ...]:
    paths = [
        Path(f"matched_panel_comparison_dim{dimension}.json")
        for dimension in EXPLORATORY_ANALYSIS_DIMS
    ]
    for role in ("baseline", "matched-null-a", "matched-null-b", "matched-null-c"):
        paths.append(Path(role) / "countsketch_sensitivity.json")
        paths.extend(
            Path(role) / f"fingerprint_summary.folded-{dimension}.jsonl"
            for dimension in EXPLORATORY_FOLD_DIMS
        )
    return tuple(paths)


def _validate_exploratory_analysis(
    analysis_dir: Path, runs: Mapping[str, RunEvidence]
) -> tuple[Path, ...]:
    analysis_dir = Path(analysis_dir).resolve()
    paths = tuple(analysis_dir / relative for relative in _expected_exploratory_analysis_files())
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        _assert_public_safe(path)

    analysis_roles = {
        "baseline": "primary",
        "matched-null-a": "matched_null_a",
        "matched-null-b": "matched_null_b",
        "matched-null-c": "matched_null_c",
    }
    folded_hashes: dict[int, dict[str, str]] = {
        dimension: {} for dimension in EXPLORATORY_FOLD_DIMS
    }
    for directory_name, role in analysis_roles.items():
        receipt_path = analysis_dir / directory_name / "countsketch_sensitivity.json"
        receipt = _load_json_object(receipt_path, "CountSketch sensitivity receipt")
        if receipt.get("analysis") != "same-seed-divisor-countsketch-fold":
            raise ValueError(f"Unexpected CountSketch analysis identity: {receipt_path}")
        input_record = receipt.get("input")
        if (
            not isinstance(input_record, dict)
            or input_record.get("run_label") != runs[role].run_id
        ):
            raise ValueError(f"CountSketch receipt run label mismatch: {receipt_path}")
        if input_record.get("rows_sha256") != runs[role].file_sha256["interventions.jsonl"]:
            raise ValueError(f"CountSketch receipt ledger hash mismatch: {receipt_path}")
        outputs = receipt.get("outputs")
        if not isinstance(outputs, list) or len(outputs) != len(EXPLORATORY_FOLD_DIMS):
            raise ValueError(f"CountSketch receipt must bind three folded outputs: {receipt_path}")
        observed_dims: set[int] = set()
        for output in outputs:
            if not isinstance(output, dict) or type(output.get("target_dim")) is not int:
                raise ValueError(f"Malformed CountSketch output receipt: {receipt_path}")
            dimension = output["target_dim"]
            observed_dims.add(dimension)
            summary_path = analysis_dir / directory_name / str(output.get("summary_file"))
            if summary_path.parent != analysis_dir / directory_name:
                raise ValueError(f"CountSketch summary path must be local: {receipt_path}")
            if output.get("summary_sha256") != _sha256(summary_path):
                raise ValueError(f"CountSketch folded summary hash mismatch: {summary_path}")
            folded_hashes[dimension][role] = str(output["summary_sha256"])
        if observed_dims != set(EXPLORATORY_FOLD_DIMS):
            raise ValueError(f"CountSketch target dimensions mismatch: {receipt_path}")

    for dimension in EXPLORATORY_ANALYSIS_DIMS:
        comparison_path = analysis_dir / f"matched_panel_comparison_dim{dimension}.json"
        comparison = _load_json_object(comparison_path, "matched-panel comparison")
        if comparison.get("analysis") != "paired-cell-matched-panel-comparison":
            raise ValueError(f"Unexpected matched-panel analysis identity: {comparison_path}")
        sources = comparison.get("sources")
        if not isinstance(sources, dict):
            raise ValueError(f"Matched-panel comparison has no sources: {comparison_path}")
        primary = sources.get("primary")
        nulls = sources.get("matched_nulls")
        if not isinstance(primary, dict) or not isinstance(nulls, list) or len(nulls) != 3:
            raise ValueError(f"Matched-panel comparison sources are malformed: {comparison_path}")
        source_rows = [primary, *nulls]
        expected_roles = RUN_ROLES
        for role, source in zip(expected_roles, source_rows):
            expected_label = (
                runs[role].run_id
                if dimension == 96
                else {
                    "primary": "baseline",
                    "matched_null_a": "matched-null-a",
                    "matched_null_b": "matched-null-b",
                    "matched_null_c": "matched-null-c",
                }[role]
            )
            if not isinstance(source, dict) or source.get("run_label") != expected_label:
                raise ValueError(f"Matched-panel comparison run label mismatch: {comparison_path}")
            expected_sha = (
                runs[role].file_sha256["fingerprint_summary.jsonl"]
                if dimension == 96
                else folded_hashes[dimension][role]
            )
            if source.get("sha256") != expected_sha:
                raise ValueError(
                    f"Matched-panel comparison source hash mismatch: {comparison_path}"
                )
    return paths


def _validate_fold_receipt(
    *,
    directory: Path,
    run: RunEvidence,
    expected_run_label: str,
) -> dict[int, str]:
    receipt_path = directory / "countsketch_sensitivity.json"
    receipt = _load_json_object(receipt_path, "CountSketch sensitivity receipt")
    if receipt.get("analysis") != "same-seed-divisor-countsketch-fold":
        raise ValueError(f"Unexpected CountSketch analysis identity: {receipt_path}")
    input_record = receipt.get("input")
    if (
        not isinstance(input_record, dict)
        or input_record.get("run_label") != expected_run_label
        or input_record.get("rows_file") != "interventions.jsonl"
        or input_record.get("rows_sha256") != run.file_sha256["interventions.jsonl"]
    ):
        raise ValueError(f"CountSketch receipt run/ledger binding mismatch: {receipt_path}")
    if (
        receipt.get("source_dim") != FINGERPRINT_SOURCE_DIM
        or receipt.get("source_seed") != FINGERPRINT_SEED
        or receipt.get("target_seed") != FINGERPRINT_SEED
    ):
        raise ValueError(f"CountSketch receipt dimension/seed mismatch: {receipt_path}")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != len(EXPLORATORY_FOLD_DIMS):
        raise ValueError(f"CountSketch receipt must bind three folded outputs: {receipt_path}")
    hashes: dict[int, str] = {}
    for output in outputs:
        if not isinstance(output, dict) or type(output.get("target_dim")) is not int:
            raise ValueError(f"Malformed CountSketch output receipt: {receipt_path}")
        dimension = output["target_dim"]
        expected_name = f"fingerprint_summary.folded-{dimension}.jsonl"
        summary_path = directory / str(output.get("summary_file"))
        if (
            dimension not in EXPLORATORY_FOLD_DIMS
            or output.get("summary_file") != expected_name
            or summary_path.parent != directory
            or output.get("cell_count") != FINGERPRINT_CELL_COUNT
            or not summary_path.is_file()
        ):
            raise ValueError(f"CountSketch folded output mapping mismatch: {receipt_path}")
        summary_receipt = _jsonl_receipt(summary_path)
        if (
            summary_receipt["row_count"] != FINGERPRINT_CELL_COUNT
            or output.get("summary_sha256") != summary_receipt["sha256"]
        ):
            raise ValueError(f"CountSketch folded summary hash/count mismatch: {summary_path}")
        hashes[dimension] = str(summary_receipt["sha256"])
    if set(hashes) != set(EXPLORATORY_FOLD_DIMS):
        raise ValueError(f"CountSketch target dimensions mismatch: {receipt_path}")
    return hashes


def _expected_diagnostic_analysis_files() -> tuple[Path, ...]:
    paths = [
        Path(f"suffix_vs_standard_dim{dimension}.json")
        for dimension in EXPLORATORY_ANALYSIS_DIMS
    ]
    paths.extend(
        Path(f"prefix_homogeneous_vs_standard_dim{dimension}.json")
        for dimension in EXPLORATORY_ANALYSIS_DIMS
    )
    for directory in ("suffix", "prefix"):
        paths.append(Path(directory) / "countsketch_sensitivity.json")
        paths.extend(
            Path(directory) / f"fingerprint_summary.folded-{dimension}.jsonl"
            for dimension in EXPLORATORY_FOLD_DIMS
        )
    return tuple(paths)


def _validate_diagnostic_analysis(
    analysis_dir: Path,
    *,
    exploratory_analysis_dir: Path,
    standard_run: RunEvidence,
    diagnostic_runs: Mapping[str, RunEvidence],
) -> tuple[Path, ...]:
    analysis_dir = Path(analysis_dir).resolve()
    exploratory_analysis_dir = Path(exploratory_analysis_dir).resolve()
    paths = tuple(
        analysis_dir / relative for relative in _expected_diagnostic_analysis_files()
    )
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        _assert_public_safe(path)

    standard_hashes = _validate_fold_receipt(
        directory=exploratory_analysis_dir / "baseline",
        run=standard_run,
        expected_run_label=standard_run.run_id,
    )
    diagnostic_spec = {
        "suffix": {
            "run_role": "suffix_matched_middle_shift",
            "comparison_stem": "suffix_vs_standard",
        },
        "prefix": {
            "run_role": "prefix_homogeneous_colored_shapes",
            "comparison_stem": "prefix_homogeneous_vs_standard",
        },
    }
    for directory_name, spec in diagnostic_spec.items():
        run = diagnostic_runs[str(spec["run_role"])]
        folded_hashes = _validate_fold_receipt(
            directory=analysis_dir / directory_name,
            run=run,
            expected_run_label=run.run_id,
        )
        for dimension in EXPLORATORY_ANALYSIS_DIMS:
            comparison_path = analysis_dir / (
                f"{spec['comparison_stem']}_dim{dimension}.json"
            )
            comparison = _load_json_object(
                comparison_path, "diagnostic matched-panel comparison"
            )
            if comparison.get("analysis") != "paired-cell-matched-panel-comparison":
                raise ValueError(
                    f"Unexpected diagnostic comparison identity: {comparison_path}"
                )
            cells = comparison.get("cells")
            descriptive = comparison.get("descriptive_summary")
            if (
                not isinstance(cells, list)
                or len(cells) != FINGERPRINT_CELL_COUNT
                or not isinstance(descriptive, dict)
                or descriptive.get("cell_count") != FINGERPRINT_CELL_COUNT
            ):
                raise ValueError(
                    f"Diagnostic comparison must contain 36 cells: {comparison_path}"
                )
            sources = comparison.get("sources")
            primary = sources.get("primary") if isinstance(sources, dict) else None
            nulls = sources.get("matched_nulls") if isinstance(sources, dict) else None
            if (
                not isinstance(primary, dict)
                or not isinstance(nulls, list)
                or len(nulls) != 1
                or not isinstance(nulls[0], dict)
            ):
                raise ValueError(
                    f"Diagnostic comparison sources are malformed: {comparison_path}"
                )
            if dimension == FINGERPRINT_SOURCE_DIM:
                expected_primary = {
                    "run_label": standard_run.run_id,
                    "summary_file": "fingerprint_summary.jsonl",
                    "sha256": standard_run.file_sha256["fingerprint_summary.jsonl"],
                }
                expected_diagnostic = {
                    "run_label": run.run_id,
                    "summary_file": "fingerprint_summary.jsonl",
                    "sha256": run.file_sha256["fingerprint_summary.jsonl"],
                }
            else:
                summary_file = f"fingerprint_summary.folded-{dimension}.jsonl"
                expected_primary = {
                    "run_label": "baseline",
                    "summary_file": summary_file,
                    "sha256": standard_hashes[dimension],
                }
                expected_diagnostic = {
                    "run_label": directory_name,
                    "summary_file": summary_file,
                    "sha256": folded_hashes[dimension],
                }
            observed_primary = {
                key: primary.get(key) for key in ("run_label", "summary_file", "sha256")
            }
            observed_diagnostic = {
                key: nulls[0].get(key)
                for key in ("run_label", "summary_file", "sha256")
            }
            if (
                observed_primary != expected_primary
                or observed_diagnostic != expected_diagnostic
            ):
                raise ValueError(
                    f"Diagnostic comparison source hash mismatch: {comparison_path}"
                )
    return paths


def _validate_confirmatory_analysis(
    analysis_dir: Path, runs: Mapping[str, RunEvidence]
) -> tuple[Path, ...]:
    analysis_dir = Path(analysis_dir).resolve()
    receipt_path = analysis_dir / "m2_confirmatory_receipt.json"
    effects_path = analysis_dir / "m2_target_effects.jsonl"
    report_path = analysis_dir / "m2_confirmatory_report.md"
    paths = (receipt_path, effects_path, report_path)
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        _assert_public_safe(path)
    receipt = _load_json_object(receipt_path, "confirmatory analysis receipt")
    if receipt.get("protocol_id") != PROTOCOL_ID or receipt.get("protocol_conformant") is not True:
        raise ValueError(f"Confirmatory analysis must conform to protocol v1: {receipt_path}")
    inputs = receipt.get("inputs")
    expected_roles = (
        "primary_colored_shapes",
        "matched_null_a",
        "matched_null_b",
        "matched_null_c",
    )
    if not isinstance(inputs, list) or len(inputs) != len(expected_roles):
        raise ValueError(f"Confirmatory analysis must bind four run inputs: {receipt_path}")
    for role, panel_role, input_record in zip(RUN_ROLES, expected_roles, inputs):
        if not isinstance(input_record, dict) or input_record.get("panel_role") != panel_role:
            raise ValueError(f"Confirmatory panel role mismatch: {receipt_path}")
        if input_record.get("run_label") != runs[role].run_id:
            raise ValueError(f"Confirmatory run label mismatch: {receipt_path}")
        checks = {
            "interventions_sha256": "interventions.jsonl",
            "resolved_config_sha256": "resolved_config.yaml",
            "run_receipt_sha256": "receipt.json",
            "resolved_inputs_sha256": "resolved_inputs.json",
        }
        for field, filename in checks.items():
            if input_record.get(field) != runs[role].file_sha256[filename]:
                raise ValueError(f"Confirmatory {field} mismatch: {receipt_path}")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError(f"Confirmatory receipt has no outputs: {receipt_path}")
    effects_receipt = outputs.get("target_effects")
    report_receipt = outputs.get("report")
    if (
        not isinstance(effects_receipt, dict)
        or effects_receipt.get("file") != effects_path.name
        or effects_receipt.get("sha256") != _sha256(effects_path)
        or effects_receipt.get("row_count") != _jsonl_receipt(effects_path)["row_count"]
    ):
        raise ValueError(f"Confirmatory target-effects receipt mismatch: {receipt_path}")
    if (
        not isinstance(report_receipt, dict)
        or report_receipt.get("file") != report_path.name
        or report_receipt.get("sha256") != _sha256(report_path)
    ):
        raise ValueError(f"Confirmatory report receipt mismatch: {receipt_path}")
    return paths


def _result_contains_inferential_claim(value: Any) -> bool:
    """Reject p-values or assigned statuses from the post-hoc result payload."""

    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if (
                lowered in {"p", "pvalue", "p-value", "p_value", "status"}
                or "p_values" in lowered
                or "p-values" in lowered
            ):
                return True
            if _result_contains_inferential_claim(item):
                return True
    elif isinstance(value, list):
        return any(_result_contains_inferential_claim(item) for item in value)
    return False


def _validate_dependence_sensitivity(
    analysis_dir: Path,
    runs: Mapping[str, RunEvidence],
    *,
    repo_root: Path,
    frozen_files: Mapping[str, str],
) -> tuple[tuple[Path, Path], dict[str, Any]]:
    analysis_dir = Path(analysis_dir).resolve()
    receipt_path = analysis_dir / "m2_dependence_sensitivity_receipt.json"
    report_path = analysis_dir / "m2_dependence_sensitivity_report.md"
    bootstrap_path = analysis_dir / "m2_dependence_sensitivity_bootstrap.jsonl"
    for path in (receipt_path, report_path, bootstrap_path):
        if not path.is_file():
            raise FileNotFoundError(path)
        _assert_public_safe(path)
    receipt = _load_json_object(receipt_path, "dependence sensitivity receipt")
    if receipt.get("analysis_id") != DEPENDENCE_ANALYSIS_ID:
        raise ValueError(f"Unexpected dependence sensitivity analysis ID: {receipt_path}")
    if receipt.get("post_hoc") is not True:
        raise ValueError(f"Dependence sensitivity must declare post_hoc true: {receipt_path}")
    if receipt.get("protocol_conformant") is not False:
        raise ValueError(
            f"Dependence sensitivity must declare protocol_conformant false: {receipt_path}"
        )
    if receipt.get("overwrites_frozen_v1_status") is not False:
        raise ValueError(
            "Dependence sensitivity must not overwrite frozen v1 status: "
            f"{receipt_path}"
        )

    parameters = receipt.get("parameters")
    if (
        not isinstance(parameters, dict)
        or type(parameters.get("bootstrap_replicates")) is not int
        or parameters["bootstrap_replicates"] != DEPENDENCE_BOOTSTRAP_ROWS
    ):
        raise ValueError(
            f"Dependence sensitivity must use 20,000 bootstrap replicates: {receipt_path}"
        )
    boundary = receipt.get("inference_boundary")
    required_false_flags = (
        "p_values_computed",
        "multiplicity_adjustment_computed",
        "confirmatory_status_computed",
        "practical_equivalence_status_computed",
    )
    if not isinstance(boundary, dict) or any(
        boundary.get(flag) is not False for flag in required_false_flags
    ):
        raise ValueError(
            f"Dependence sensitivity must compute no p-value or status: {receipt_path}"
        )
    results = receipt.get("results")
    if (
        not isinstance(results, list)
        or len(results) != 2
        or any(
            not isinstance(result, dict)
            or result.get("confirmatory_status_assigned") is not False
            or _result_contains_inferential_claim(
                {
                    key: value
                    for key, value in result.items()
                    if key != "confirmatory_status_assigned"
                }
            )
            for result in results
        )
    ):
        raise ValueError(
            f"Dependence sensitivity results must assign no p-value or status: {receipt_path}"
        )

    inputs = receipt.get("inputs")
    expected_roles = (
        "primary_colored_shapes",
        "matched_null_a",
        "matched_null_b",
        "matched_null_c",
    )
    if not isinstance(inputs, list) or len(inputs) != len(expected_roles):
        raise ValueError(f"Dependence sensitivity must bind four run inputs: {receipt_path}")
    for role, panel_role, input_record in zip(RUN_ROLES, expected_roles, inputs):
        if not isinstance(input_record, dict) or input_record.get("panel_role") != panel_role:
            raise ValueError(f"Dependence sensitivity panel role mismatch: {receipt_path}")
        if input_record.get("run_label") != runs[role].run_id:
            raise ValueError(f"Dependence sensitivity run label mismatch: {receipt_path}")
        checks = {
            "interventions_sha256": "interventions.jsonl",
            "resolved_config_sha256": "resolved_config.yaml",
            "run_receipt_sha256": "receipt.json",
            "resolved_inputs_sha256": "resolved_inputs.json",
        }
        for field, filename in checks.items():
            if input_record.get(field) != runs[role].file_sha256[filename]:
                raise ValueError(f"Dependence sensitivity {field} mismatch: {receipt_path}")

    validation = receipt.get("validation")
    analyzer_path = repo_root / "scripts" / DEPENDENCE_ANALYZER_FILE
    frozen_analyzer_relative = f"scripts/{FROZEN_CONFIRMATORY_ANALYZER_FILE}"
    if not analyzer_path.is_file():
        raise FileNotFoundError(analyzer_path)
    if not isinstance(validation, dict):
        raise ValueError(f"Dependence sensitivity validation is missing: {receipt_path}")
    if (
        validation.get("analyzer_file") != DEPENDENCE_ANALYZER_FILE
        or validation.get("analyzer_sha256") != _sha256(analyzer_path)
        or validation.get("frozen_v1_analyzer_dependency_file")
        != FROZEN_CONFIRMATORY_ANALYZER_FILE
        or validation.get("frozen_v1_analyzer_dependency_sha256")
        != frozen_files.get(frozen_analyzer_relative)
        or validation.get("strict_frozen_p2_evidence_validation") is not True
        or validation.get("model_forward_passes") != 0
        or validation.get("c1_holdout_accessed") is not False
    ):
        raise ValueError(
            f"Dependence sensitivity analyzer/validation binding mismatch: {receipt_path}"
        )

    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise ValueError(f"Dependence sensitivity outputs are missing: {receipt_path}")
    report_receipt = outputs.get("report")
    bootstrap_receipt = outputs.get("bootstrap_layer_means")
    observed_bootstrap = _jsonl_receipt(bootstrap_path)
    if (
        not isinstance(report_receipt, dict)
        or report_receipt.get("file") != report_path.name
        or report_receipt.get("sha256") != _sha256(report_path)
    ):
        raise ValueError(f"Dependence sensitivity report hash mismatch: {receipt_path}")
    if (
        not isinstance(bootstrap_receipt, dict)
        or bootstrap_receipt.get("file") != bootstrap_path.name
        or bootstrap_receipt.get("sha256") != observed_bootstrap["sha256"]
        or bootstrap_receipt.get("row_count") != DEPENDENCE_BOOTSTRAP_ROWS
        or observed_bootstrap["row_count"] != DEPENDENCE_BOOTSTRAP_ROWS
    ):
        raise ValueError(
            f"Dependence sensitivity bootstrap must bind exactly 20,000 rows: {receipt_path}"
        )
    return (receipt_path, report_path), observed_bootstrap


def _copy_file(
    source: Path,
    destination: Path,
    copied: dict[str, dict[str, Any]],
    root: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    relative = destination.relative_to(root).as_posix()
    copied[relative] = _file_receipt(destination)


def build(
    *,
    exploratory_runs: Mapping[str, Path],
    exploratory_analysis_dir: Path,
    parity_receipt: Path,
    preregistration_manifest: Path,
    preregistration_audit: Path,
    output_dir: Path,
    manifest_path: Path,
    confirmatory_families: Mapping[str, ConfirmatoryFamily] | None = None,
    dependence_sensitivity_dirs: Mapping[str, Path] | None = None,
    diagnostic_runs: Mapping[str, Path] | None = None,
    diagnostic_analysis_dir: Path | None = None,
    unexecuted_diagnostics: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate all supplied evidence before publishing a compact M2 bundle."""

    _validate_roles(exploratory_runs, "exploratory controls")
    confirmatory_families = dict(confirmatory_families or {})
    dependence_sensitivity_dirs = dict(dependence_sensitivity_dirs or {})
    diagnostic_runs = dict(diagnostic_runs or {})
    unexecuted_diagnostics = dict(unexecuted_diagnostics or {})
    unknown_families = sorted(set(confirmatory_families) - set(CONFIRMATORY_FAMILIES))
    if unknown_families:
        raise ValueError(f"Unknown confirmatory families: {unknown_families}")
    unknown_sensitivity_families = sorted(
        set(dependence_sensitivity_dirs) - set(CONFIRMATORY_FAMILIES)
    )
    if unknown_sensitivity_families:
        raise ValueError(
            f"Unknown dependence sensitivity families: {unknown_sensitivity_families}"
        )
    orphan_sensitivity_families = sorted(
        set(dependence_sensitivity_dirs) - set(confirmatory_families)
    )
    if orphan_sensitivity_families:
        raise ValueError(
            "Dependence sensitivity requires its complete confirmatory family: "
            f"{orphan_sensitivity_families}"
        )
    unknown_diagnostics = sorted(
        (set(diagnostic_runs) | set(unexecuted_diagnostics)) - set(DIAGNOSTIC_IDS)
    )
    if unknown_diagnostics:
        raise ValueError(f"Unknown diagnostics: {unknown_diagnostics}")
    if diagnostic_runs and set(diagnostic_runs) != set(DIAGNOSTIC_IDS):
        raise ValueError(
            "Diagnostic publication requires both frozen diagnostic runs together"
        )
    if diagnostic_runs and diagnostic_analysis_dir is None:
        raise ValueError(
            "--diagnostic-analysis-dir is required when diagnostic runs are supplied"
        )
    if not diagnostic_runs and diagnostic_analysis_dir is not None:
        raise ValueError(
            "--diagnostic-analysis-dir requires both frozen diagnostic runs"
        )
    overlap = sorted(set(diagnostic_runs) & set(unexecuted_diagnostics))
    if overlap:
        raise ValueError(f"Diagnostics cannot be both executed and unexecuted: {overlap}")

    parity_receipt = Path(parity_receipt).resolve()
    if not parity_receipt.is_file():
        raise FileNotFoundError(parity_receipt)
    _assert_public_safe(parity_receipt)
    parity_sha256 = _sha256(parity_receipt)
    if not _SHA256_RE.fullmatch(parity_sha256):
        raise ValueError("Could not compute a valid parity receipt SHA-256")
    if parity_sha256 != PINNED_PARITY_RECEIPT_SHA256:
        raise ValueError("Supplied parity receipt is not the protocol-pinned MLX receipt")

    (
        repo_root,
        frozen_files,
        p2_arm_mapping,
        preregistration_manifest_sha256,
        preregistration_audit_sha256,
    ) = _load_preregistration_authority(
        preregistration_manifest=preregistration_manifest,
        preregistration_audit=preregistration_audit,
        parity_sha256=parity_sha256,
    )

    input_bindings: dict[str, dict[str, InputBinding]] = {"exploratory": {}}
    for role, config_relative in EXPLORATORY_CONFIG_FILES.items():
        input_bindings["exploratory"][role] = _input_binding_for_config(
            repo_root=repo_root,
            frozen_files=frozen_files,
            config_relative=config_relative,
            parity_sha256=parity_sha256,
            authority=(
                "legacy published exploratory config plus preregistration-frozen inputs"
                if role == "primary"
                else "milestone2_preregistration_v1"
            ),
        )

    validated_runs: dict[str, dict[str, RunEvidence]] = {"exploratory": {}}
    for role in RUN_ROLES:
        validated_runs["exploratory"][role] = _validate_run(
            exploratory_runs[role],
            role=role,
            parity_sha256=parity_sha256,
            input_binding=input_bindings["exploratory"][role],
        )
    exploratory_analysis_paths = _validate_exploratory_analysis(
        exploratory_analysis_dir, validated_runs["exploratory"]
    )

    confirmatory_analysis_paths: dict[str, tuple[Path, ...]] = {}
    for family_name, family in confirmatory_families.items():
        _validate_roles(family.runs, f"confirmatory family {family_name}")
        validated_runs[family_name] = {}
        input_bindings[family_name] = {}
        for role in RUN_ROLES:
            arm = role if family_name == "p2" else f"{role}_independent_source"
            audited_arm = p2_arm_mapping.get(arm)
            if audited_arm is None or not isinstance(audited_arm.get("path"), str):
                raise ValueError(f"Preregistration audit has no exact mapping for arm {arm}")
            input_binding = _input_binding_for_config(
                repo_root=repo_root,
                frozen_files=frozen_files,
                config_relative=audited_arm["path"],
                parity_sha256=parity_sha256,
                authority="milestone2_preregistration_audit_v1",
                audited_arm=audited_arm,
            )
            input_bindings[family_name][role] = input_binding
            validated_runs[family_name][role] = _validate_run(
                family.runs[role],
                role=role,
                parity_sha256=parity_sha256,
                input_binding=input_binding,
                expected_source_file=EXPECTED_SOURCE_FILES[family_name],
            )
        confirmatory_analysis_paths[family_name] = _validate_confirmatory_analysis(
            family.analysis_dir, validated_runs[family_name]
        )

    dependence_sensitivity_paths: dict[str, tuple[Path, Path]] = {}
    dependence_sensitivity_omissions: dict[str, dict[str, Any]] = {}
    for family_name, analysis_dir in dependence_sensitivity_dirs.items():
        paths, bootstrap_receipt = _validate_dependence_sensitivity(
            analysis_dir,
            validated_runs[family_name],
            repo_root=repo_root,
            frozen_files=frozen_files,
        )
        dependence_sensitivity_paths[family_name] = paths
        dependence_sensitivity_omissions[family_name] = bootstrap_receipt

    validated_diagnostics: dict[str, RunEvidence] = {}
    for diagnostic_id, run_dir in diagnostic_runs.items():
        input_binding = _input_binding_for_config(
            repo_root=repo_root,
            frozen_files=frozen_files,
            config_relative=DIAGNOSTIC_CONFIG_FILES[diagnostic_id],
            parity_sha256=parity_sha256,
            authority="milestone2_preregistration_v1",
        )
        validated_diagnostics[diagnostic_id] = _validate_run(
            run_dir,
            role=diagnostic_id,
            parity_sha256=parity_sha256,
            input_binding=input_binding,
        )
    diagnostic_analysis_paths: tuple[Path, ...] = ()
    if diagnostic_analysis_dir is not None:
        diagnostic_analysis_paths = _validate_diagnostic_analysis(
            diagnostic_analysis_dir,
            exploratory_analysis_dir=exploratory_analysis_dir,
            standard_run=validated_runs["exploratory"]["primary"],
            diagnostic_runs=validated_diagnostics,
        )

    all_run_ids = [
        evidence.run_id
        for family in validated_runs.values()
        for evidence in family.values()
    ] + [evidence.run_id for evidence in validated_diagnostics.values()]
    if len(all_run_ids) != len(set(all_run_ids)):
        raise ValueError("Every bundle role must refer to a distinct run_id")

    output_dir = Path(output_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    if output_dir.exists():
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    if manifest_path.exists():
        raise FileExistsError(f"Manifest already exists: {manifest_path}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.", dir=output_dir.parent))
    temporary_manifest: Path | None = None
    try:
        copied: dict[str, dict[str, Any]] = {}
        omitted: dict[str, dict[str, Any]] = {}
        run_manifest: dict[str, Any] = {}
        _copy_file(
            parity_receipt,
            staging / "validation" / "mlx_gpt2_parity" / "receipt.json",
            copied,
            staging,
        )
        _copy_file(
            Path(preregistration_manifest).resolve(),
            staging / "protocol" / "milestone2_preregistration_v1.json",
            copied,
            staging,
        )
        _copy_file(
            Path(preregistration_audit).resolve(),
            staging / "protocol" / "milestone2_preregistration_audit_v1.json",
            copied,
            staging,
        )

        for family_name, family_runs in validated_runs.items():
            family_rows: dict[str, Any] = {}
            family_path = (
                "exploratory"
                if family_name == "exploratory"
                else f"confirmatory/{family_name}"
            )
            for role, evidence in family_runs.items():
                run_output = staging / "runs" / family_path / role
                for source in evidence.compact_files:
                    _copy_file(source, run_output / source.name, copied, staging)
                for filename, receipt_value in evidence.omitted_large_files.items():
                    omitted[f"runs/{family_path}/{role}/{filename}"] = dict(receipt_value)
                family_rows[role] = {
                    "run_id": evidence.run_id,
                    "run_seal": evidence.run_seal,
                    "compact_file_count": len(evidence.compact_files),
                    "not_produced_compact_files": dict(evidence.not_produced_compact_files),
                }
            run_manifest[family_name] = {"status": "complete", "runs": family_rows}

        exploratory_analysis_dir = Path(exploratory_analysis_dir).resolve()
        for source in exploratory_analysis_paths:
            relative = source.relative_to(exploratory_analysis_dir)
            _copy_file(source, staging / "analyses" / "exploratory" / relative, copied, staging)
        for family_name, paths in confirmatory_analysis_paths.items():
            analysis_dir = Path(confirmatory_families[family_name].analysis_dir).resolve()
            for source in paths:
                _copy_file(
                    source,
                    staging
                    / "analyses"
                    / "confirmatory"
                    / family_name
                    / source.relative_to(analysis_dir),
                    copied,
                    staging,
                )

        posthoc_dependence_manifest: dict[str, Any] = {}
        for family_name in CONFIRMATORY_FAMILIES:
            paths = dependence_sensitivity_paths.get(family_name)
            if paths is None:
                posthoc_dependence_manifest[family_name] = {
                    "status": "unexecuted",
                    "reason": (
                        "post-hoc dependence sensitivity not supplied to the bundler; "
                        "no analysis is claimed"
                    ),
                }
                continue
            analysis_dir = Path(dependence_sensitivity_dirs[family_name]).resolve()
            for source in paths:
                _copy_file(
                    source,
                    staging
                    / "analyses"
                    / "posthoc_dependence"
                    / family_name
                    / source.relative_to(analysis_dir),
                    copied,
                    staging,
                )
            bootstrap_name = "m2_dependence_sensitivity_bootstrap.jsonl"
            omission_key = (
                f"analyses/posthoc_dependence/{family_name}/{bootstrap_name}"
            )
            omitted[omission_key] = dict(
                dependence_sensitivity_omissions[family_name]
            )
            posthoc_dependence_manifest[family_name] = {
                "status": "complete",
                "post_hoc": True,
                "protocol_conformant": False,
                "overwrites_frozen_v1_status": False,
                "included_files": [path.name for path in paths],
                "omitted_bootstrap": {
                    "file": omission_key,
                    **dict(dependence_sensitivity_omissions[family_name]),
                },
            }

        for family_name in CONFIRMATORY_FAMILIES:
            if family_name not in run_manifest:
                run_manifest[family_name] = {
                    "status": "unexecuted",
                    "reason": "family not supplied to the bundler; no execution is claimed",
                }

        diagnostics_manifest: dict[str, Any] = {}
        for diagnostic_id in DIAGNOSTIC_IDS:
            evidence = validated_diagnostics.get(diagnostic_id)
            if evidence is None:
                reason = unexecuted_diagnostics.get(
                    diagnostic_id,
                    "diagnostic run not supplied to the bundler; no execution is claimed",
                )
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError(
                        "Unexecuted diagnostic reason must be non-empty: "
                        f"{diagnostic_id}"
                    )
                diagnostics_manifest[diagnostic_id] = {
                    "status": "unexecuted",
                    "reason": reason.strip(),
                }
                continue
            run_output = staging / "runs" / "diagnostics" / diagnostic_id
            for source in evidence.compact_files:
                _copy_file(source, run_output / source.name, copied, staging)
            for filename, receipt_value in evidence.omitted_large_files.items():
                omitted[f"runs/diagnostics/{diagnostic_id}/{filename}"] = dict(receipt_value)
            diagnostics_manifest[diagnostic_id] = {
                "status": "complete",
                "run_id": evidence.run_id,
                "run_seal": evidence.run_seal,
                "compact_file_count": len(evidence.compact_files),
                "not_produced_compact_files": dict(evidence.not_produced_compact_files),
            }

        diagnostic_analysis_manifest: dict[str, Any]
        if diagnostic_analysis_paths:
            assert diagnostic_analysis_dir is not None
            analysis_dir = Path(diagnostic_analysis_dir).resolve()
            for source in diagnostic_analysis_paths:
                _copy_file(
                    source,
                    staging
                    / "analyses"
                    / "diagnostics"
                    / source.relative_to(analysis_dir),
                    copied,
                    staging,
                )
            diagnostic_analysis_manifest = {
                "status": "complete",
                "file_count": len(diagnostic_analysis_paths),
                "source_dimension": FINGERPRINT_SOURCE_DIM,
                "folded_dimensions": list(EXPLORATORY_FOLD_DIMS),
                "fingerprint_seed": FINGERPRINT_SEED,
                "cell_count_per_comparison": FINGERPRINT_CELL_COUNT,
                "run_roles": list(DIAGNOSTIC_IDS),
            }
        else:
            diagnostic_analysis_manifest = {
                "status": "unexecuted",
                "reason": (
                    "diagnostic analysis directory not supplied; no diagnostic "
                    "analysis is claimed"
                ),
            }

        binding_rows: list[dict[str, Any]] = []
        for family_name, family_runs in validated_runs.items():
            for role, evidence in family_runs.items():
                binding_rows.append(
                    {
                        "family": family_name,
                        "role": role,
                        "run_id": evidence.run_id,
                        "authority": evidence.input_binding.authority,
                        "config_path": evidence.input_binding.config_path,
                        "input_hashes": dict(evidence.input_binding.expected_inputs),
                        "exact_input_00_through_04_match": True,
                    }
                )
        for diagnostic_id, evidence in validated_diagnostics.items():
            binding_rows.append(
                {
                    "family": "diagnostic",
                    "role": diagnostic_id,
                    "run_id": evidence.run_id,
                    "authority": evidence.input_binding.authority,
                    "config_path": evidence.input_binding.config_path,
                    "input_hashes": dict(evidence.input_binding.expected_inputs),
                    "exact_input_00_through_04_match": True,
                }
            )
        binding_audit = {
            "schema_version": 1,
            "audit_id": "glyphprobe-m2-public-bundle-input-binding-v1",
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "preregistration_manifest_sha256": preregistration_manifest_sha256,
            "preregistration_audit_sha256": preregistration_audit_sha256,
            "parity_receipt_sha256": parity_sha256,
            "run_count": len(binding_rows),
            "checks": {
                "exact_input_key_set": True,
                "exact_input_paths": True,
                "exact_input_hashes": True,
                "config_role_mapping": True,
                "panel_role_mapping": True,
                "source_family_mapping": True,
                "target_bank_mapping": True,
            },
            "runs": sorted(binding_rows, key=lambda row: (row["family"], row["role"])),
        }
        binding_path = staging / "input_binding_audit.json"
        binding_path.write_text(
            json.dumps(binding_audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _assert_public_safe(binding_path)
        copied["input_binding_audit.json"] = _file_receipt(binding_path)
        binding_receipt = {
            "file": "input_binding_audit.json",
            "sha256": copied["input_binding_audit.json"]["sha256"],
            "run_count": len(binding_rows),
            "status": "pass",
        }

        manifest = {
            "schema_version": 1,
            "bundle": "glyphprobe-milestone2-public-compact",
            "protocol_id": PROTOCOL_ID,
            "claim_boundary": CLAIM_BOUNDARY,
            "causal_claim_authorized": False,
            "artifact_root": output_dir.name,
            "path_safety": "verified_no_local_absolute_paths",
            "parity_receipt_sha256": parity_sha256,
            "preregistration_manifest_sha256": preregistration_manifest_sha256,
            "preregistration_audit_sha256": preregistration_audit_sha256,
            "input_binding_audit": binding_receipt,
            "families": {
                "exploratory": run_manifest["exploratory"],
                "p2": run_manifest["p2"],
                "independent_source": run_manifest["independent_source"],
            },
            "posthoc_dependence": posthoc_dependence_manifest,
            "diagnostics": diagnostics_manifest,
            "diagnostic_analysis": diagnostic_analysis_manifest,
            "included_files": dict(sorted(copied.items())),
            "omitted_large_local_files": dict(sorted(omitted.items())),
            "omission_reason": (
                "Condition ledgers, post-hoc bootstrap distributions, and numeric NPZ "
                "arrays are excluded from Git because of size. Their byte counts, row "
                "counts where applicable, and SHA-256 hashes bind the audited local "
                "evidence but cannot reconstruct omitted data."
            ),
        }
        payload = json.dumps(
            manifest, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8") + b"\n"
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{manifest_path.name}.", dir=manifest_path.parent
        )
        temporary_manifest = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        staging.rename(output_dir)
        temporary_manifest.replace(manifest_path)
        temporary_manifest = None
        return manifest
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if temporary_manifest is not None and temporary_manifest.exists():
            temporary_manifest.unlink()
        raise


def _family_from_cli(
    *,
    name: str,
    primary: Path | None,
    nulls: Sequence[Path] | None,
    analysis_dir: Path | None,
) -> ConfirmatoryFamily | None:
    supplied = (primary is not None, nulls is not None, analysis_dir is not None)
    if not any(supplied):
        return None
    if not all(supplied):
        raise ValueError(
            f"{name} is all-or-none: supply primary run, three matched-null runs, and analysis dir"
        )
    assert primary is not None and nulls is not None and analysis_dir is not None
    return ConfirmatoryFamily(
        runs=dict(zip(RUN_ROLES, (primary, *nulls))),
        analysis_dir=analysis_dir,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exploratory-primary-run", type=Path, required=True)
    parser.add_argument(
        "--exploratory-matched-null-runs",
        type=Path,
        nargs=3,
        metavar=("NULL_A", "NULL_B", "NULL_C"),
        required=True,
    )
    parser.add_argument("--exploratory-analysis-dir", type=Path, required=True)
    parser.add_argument("--parity-receipt", type=Path, required=True)
    parser.add_argument(
        "--preregistration-manifest",
        type=Path,
        default=Path("data/manifests/milestone2_preregistration_v1.json"),
    )
    parser.add_argument(
        "--preregistration-audit",
        type=Path,
        default=Path("data/manifests/milestone2_preregistration_audit_v1.json"),
    )
    for prefix in ("p2", "independent-source"):
        parser.add_argument(f"--{prefix}-primary-run", type=Path)
        parser.add_argument(
            f"--{prefix}-matched-null-runs",
            type=Path,
            nargs=3,
            metavar=("NULL_A", "NULL_B", "NULL_C"),
        )
        parser.add_argument(f"--{prefix}-analysis-dir", type=Path)
    parser.add_argument("--p2-dependence-sensitivity-dir", type=Path)
    parser.add_argument(
        "--independent-source-dependence-sensitivity-dir",
        type=Path,
    )
    parser.add_argument("--suffix-diagnostic-run", type=Path)
    parser.add_argument("--prefix-diagnostic-run", type=Path)
    parser.add_argument("--diagnostic-analysis-dir", type=Path)
    parser.add_argument(
        "--unexecuted-suffix-reason",
        default="secondary suffix diagnostic was not executed",
    )
    parser.add_argument(
        "--unexecuted-prefix-reason",
        default="secondary prefix-homogeneous diagnostic was not executed",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("artifacts/MILESTONE2_MANIFEST.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        families: dict[str, ConfirmatoryFamily] = {}
        p2 = _family_from_cli(
            name="p2",
            primary=args.p2_primary_run,
            nulls=args.p2_matched_null_runs,
            analysis_dir=args.p2_analysis_dir,
        )
        independent_source = _family_from_cli(
            name="independent-source",
            primary=args.independent_source_primary_run,
            nulls=args.independent_source_matched_null_runs,
            analysis_dir=args.independent_source_analysis_dir,
        )
        if p2 is not None:
            families["p2"] = p2
        if independent_source is not None:
            families["independent_source"] = independent_source
        dependence_sensitivity_dirs = {
            key: value
            for key, value in {
                "p2": args.p2_dependence_sensitivity_dir,
                "independent_source": (
                    args.independent_source_dependence_sensitivity_dir
                ),
            }.items()
            if value is not None
        }
        diagnostics = {
            key: value
            for key, value in {
                "suffix_matched_middle_shift": args.suffix_diagnostic_run,
                "prefix_homogeneous_colored_shapes": args.prefix_diagnostic_run,
            }.items()
            if value is not None
        }
        reasons = {
            key: value
            for key, value in {
                "suffix_matched_middle_shift": args.unexecuted_suffix_reason,
                "prefix_homogeneous_colored_shapes": args.unexecuted_prefix_reason,
            }.items()
            if key not in diagnostics
        }
        manifest = build(
            exploratory_runs=dict(
                zip(
                    RUN_ROLES,
                    (
                        args.exploratory_primary_run,
                        *args.exploratory_matched_null_runs,
                    ),
                )
            ),
            exploratory_analysis_dir=args.exploratory_analysis_dir,
            parity_receipt=args.parity_receipt,
            preregistration_manifest=args.preregistration_manifest,
            preregistration_audit=args.preregistration_audit,
            output_dir=args.output_dir,
            manifest_path=args.manifest_path,
            confirmatory_families=families,
            dependence_sensitivity_dirs=dependence_sensitivity_dirs,
            diagnostic_runs=diagnostics,
            diagnostic_analysis_dir=args.diagnostic_analysis_dir,
            unexecuted_diagnostics=reasons,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        ValueError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        parser = _build_parser()
        parser.error(str(exc))
    print(f"included={len(manifest['included_files'])}")
    print(f"omitted={len(manifest['omitted_large_local_files'])}")
    print(f"manifest={Path(args.manifest_path).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
