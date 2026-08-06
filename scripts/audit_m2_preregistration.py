#!/usr/bin/env python3
"""Fail-closed audit for the frozen Milestone 2 preregistration bundle.

The preregistration manifest is intentionally a flat table of repository-
relative paths and SHA-256 digests.  This audit accepts exactly the frozen
Milestone 2 surface declared below, verifies every byte digest, and then checks
the eight one-shot P2 configs against their prespecified execution contract.
It does not load a tokenizer or a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

import yaml


AUDIT_ID = "glyphprobe-m2-preregistration-audit-v1"
EXPECTED_MANIFEST_ID = "milestone2_preregistration_v1"
EXPECTED_PROTOCOL_ID = "glyphprobe-m2-tokenization-controls-v1"
DEFAULT_MANIFEST_PATH = Path("data/manifests/milestone2_preregistration_v1.json")

EXPECTED_MODEL_ID = "openai-community/gpt2"
EXPECTED_MODEL_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
EXPECTED_VALIDATION_RECEIPT = "../validation/mlx_gpt2_parity/receipt.json"
EXPECTED_VALIDATION_RECEIPT_SHA256 = (
    "98c3873a1ec6166aeae0fbb5d9abcd587eb1b3996726912ab963ff35ee497679"
)
EXPECTED_P2_TARGETS = "../data/targets/p2_confirmatory_targets_v1.jsonl"
PRIMARY_SOURCE_WRAPPERS = "../data/wrappers/source_wrappers.jsonl"
INDEPENDENT_SOURCE_WRAPPERS = (
    "../data/wrappers/milestone2_independent_source_wrappers_v1.jsonl"
)


REQUIRED_FROZEN_PATHS: tuple[str, ...] = (
    "docs/MILESTONE2_PROTOCOL.md",
    "docs/MILESTONE2_PROTOCOL.ja.md",
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
    "data/wrappers/milestone2_independent_source_wrappers_v1.jsonl",
    "data/manifests/milestone2_frozen_banks_v1.json",
    "data/tokenization_controls/manifest.json",
    "data/tokenization_controls/manifest.sha256",
    "data/tokenization_controls/audit_receipt_v1.json",
    "data/targets/prestage_targets.jsonl",
    "data/wrappers/source_wrappers.jsonl",
    "data/emoji_panels/colored_shapes.yaml",
    "data/emoji_panels/m2_matched_null_a.yaml",
    "data/emoji_panels/m2_matched_null_b.yaml",
    "data/emoji_panels/m2_matched_null_c.yaml",
    "data/emoji_panels/m2_suffix_matched_middle_shift.yaml",
    "data/emoji_panels/m2_prefix_homogeneous_colored_shapes.yaml",
    "configs/m2_matched_null_a_mlx.yaml",
    "configs/m2_matched_null_b_mlx.yaml",
    "configs/m2_matched_null_c_mlx.yaml",
    "configs/m2_suffix_matched_middle_shift_mlx.yaml",
    "configs/m2_prefix_homogeneous_colored_shapes_mlx.yaml",
    "configs/m2_p2_primary_mlx.yaml",
    "configs/m2_p2_matched_null_a_mlx.yaml",
    "configs/m2_p2_matched_null_b_mlx.yaml",
    "configs/m2_p2_matched_null_c_mlx.yaml",
    "configs/m2_p2_primary_independent_source_mlx.yaml",
    "configs/m2_p2_matched_null_a_independent_source_mlx.yaml",
    "configs/m2_p2_matched_null_b_independent_source_mlx.yaml",
    "configs/m2_p2_matched_null_c_independent_source_mlx.yaml",
    "scripts/analyze_m2_confirmatory.py",
    "scripts/analyze_countsketch_sensitivity.py",
    "scripts/audit_m2_tokenization_controls.py",
    "scripts/audit_m2_preregistration.py",
    "validation/mlx_gpt2_parity/receipt.json",
)


P2_CONFIG_CONTRACTS: dict[str, dict[str, str]] = {
    "configs/m2_p2_primary_mlx.yaml": {
        "panel": "../data/emoji_panels/colored_shapes.yaml",
        "source": PRIMARY_SOURCE_WRAPPERS,
        "arm": "primary",
    },
    "configs/m2_p2_matched_null_a_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_a.yaml",
        "source": PRIMARY_SOURCE_WRAPPERS,
        "arm": "matched_null_a",
    },
    "configs/m2_p2_matched_null_b_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_b.yaml",
        "source": PRIMARY_SOURCE_WRAPPERS,
        "arm": "matched_null_b",
    },
    "configs/m2_p2_matched_null_c_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_c.yaml",
        "source": PRIMARY_SOURCE_WRAPPERS,
        "arm": "matched_null_c",
    },
    "configs/m2_p2_primary_independent_source_mlx.yaml": {
        "panel": "../data/emoji_panels/colored_shapes.yaml",
        "source": INDEPENDENT_SOURCE_WRAPPERS,
        "arm": "primary_independent_source",
    },
    "configs/m2_p2_matched_null_a_independent_source_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_a.yaml",
        "source": INDEPENDENT_SOURCE_WRAPPERS,
        "arm": "matched_null_a_independent_source",
    },
    "configs/m2_p2_matched_null_b_independent_source_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_b.yaml",
        "source": INDEPENDENT_SOURCE_WRAPPERS,
        "arm": "matched_null_b_independent_source",
    },
    "configs/m2_p2_matched_null_c_independent_source_mlx.yaml": {
        "panel": "../data/emoji_panels/m2_matched_null_c.yaml",
        "source": INDEPENDENT_SOURCE_WRAPPERS,
        "arm": "matched_null_c_independent_source",
    },
}


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_C1_REFERENCE_RE = re.compile(r"(?i)(?:^|[^a-z0-9])c1(?:[^a-z0-9]|$)|c1_causal")


class PreregistrationAuditError(RuntimeError):
    """Raised when any preregistration invariant fails."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise PreregistrationAuditError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreregistrationAuditError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_repo_relative_path(value: Any) -> str:
    """Return one canonical POSIX repository path or fail closed."""

    _require(isinstance(value, str) and bool(value), "manifest path must be a string")
    _require("\\" not in value, f"manifest path must use POSIX separators: {value!r}")
    pure = PurePosixPath(value)
    _require(not pure.is_absolute(), f"absolute manifest path is forbidden: {value!r}")
    _require(value == pure.as_posix(), f"manifest path is not canonical: {value!r}")
    _require(
        all(part not in {"", ".", ".."} for part in pure.parts),
        f"manifest path contains an unsafe segment: {value!r}",
    )
    return value


def _resolve_within_repo(root: Path, relative_path: str) -> Path:
    root = root.resolve()
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PreregistrationAuditError(
            f"path resolves outside the repository: {relative_path}"
        ) from exc
    return path


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreregistrationAuditError(f"cannot read {label} as JSON: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def validate_manifest_file_table(
    root: Path,
    manifest: Mapping[str, Any],
    *,
    required_paths: Iterable[str] = REQUIRED_FROZEN_PATHS,
) -> list[dict[str, str]]:
    """Validate the exact path set and byte digests in a manifest file table.

    ``required_paths`` exists to make this core validator independently unit-
    testable without fabricating the complete preregistration tree.
    """

    raw_files = manifest.get("files")
    _require(isinstance(raw_files, list), "manifest.files must be a list")
    expected = tuple(required_paths)
    _require(len(set(expected)) == len(expected), "internal required path set is not unique")

    seen: set[str] = set()
    records: list[tuple[str, str]] = []
    for index, record in enumerate(raw_files):
        _require(isinstance(record, dict), f"manifest.files[{index}] must be an object")
        path_value = _safe_repo_relative_path(record.get("path"))
        _require(path_value not in seen, f"duplicate manifest path: {path_value}")
        seen.add(path_value)
        expected_sha = record.get("sha256")
        _require(
            isinstance(expected_sha, str) and bool(_SHA256_RE.fullmatch(expected_sha)),
            f"invalid lowercase SHA-256 for {path_value}",
        )
        records.append((path_value, expected_sha))

    expected_set = set(expected)
    actual_set = {path for path, _ in records}
    missing = sorted(expected_set - actual_set)
    unexpected = sorted(actual_set - expected_set)
    _require(
        not missing and not unexpected,
        "manifest frozen path set mismatch: "
        f"missing={missing or []}, unexpected={unexpected or []}",
    )

    verified: list[dict[str, str]] = []
    for relative_path, expected_sha in records:
        path = _resolve_within_repo(root, relative_path)
        _require(path.is_file(), f"missing frozen file: {relative_path}")
        actual_sha = _sha256(path)
        _require(
            actual_sha == expected_sha,
            f"SHA-256 mismatch for {relative_path}: expected {expected_sha}, got {actual_sha}",
        )
        verified.append(
            {
                "path": relative_path,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
            }
        )
    return sorted(verified, key=lambda row: row["path"])


def _load_unique_yaml(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw_text = path.read_text(encoding="utf-8")
        value = yaml.load(raw_text, Loader=_UniqueKeyLoader)
    except PreregistrationAuditError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PreregistrationAuditError(f"cannot read YAML config {path}: {exc}") from exc
    _require(isinstance(value, dict), f"YAML config must be a mapping: {path}")
    return value, raw_text


def _nested_value(value: Mapping[str, Any], dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        _require(
            isinstance(current, Mapping) and part in current,
            f"missing P2 config field: {dotted_path}",
        )
        current = current[part]
    return current


def _typed_equal(actual: Any, expected: Any) -> bool:
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, int):
        return isinstance(actual, int) and not isinstance(actual, bool) and actual == expected
    if isinstance(expected, float):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and float(actual) == expected
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _typed_equal(left, right) for left, right in zip(actual, expected)
        )
    return type(actual) is type(expected) and actual == expected


def _expect(config: Mapping[str, Any], dotted_path: str, expected: Any, *, label: str) -> None:
    actual = _nested_value(config, dotted_path)
    _require(
        _typed_equal(actual, expected),
        f"{label}: expected {dotted_path}={expected!r}, got {actual!r}",
    )


def validate_p2_config_document(
    config: Mapping[str, Any],
    raw_text: str,
    contract: Mapping[str, str],
    *,
    label: str,
) -> dict[str, Any]:
    """Validate one parsed P2 YAML document without touching model artifacts."""

    _require(
        _C1_REFERENCE_RE.search(raw_text) is None,
        f"{label}: a C1 reference is forbidden in a P2 config",
    )
    expectations: tuple[tuple[str, Any], ...] = (
        ("schema_version", 1),
        ("mode", "internal"),
        ("backend.kind", "mlx"),
        ("backend.model", EXPECTED_MODEL_ID),
        ("backend.revision", EXPECTED_MODEL_REVISION),
        ("backend.device", "gpu"),
        ("backend.dtype", "float32"),
        ("backend.local_files_only", True),
        ("backend.validation_receipt", EXPECTED_VALIDATION_RECEIPT),
        ("backend.validation_receipt_sha256", EXPECTED_VALIDATION_RECEIPT_SHA256),
        ("run.seeds", [101, 211, 307]),
        ("run.replicate_mode", "wrapper_subsample"),
        ("run.wrapper_subsample_fraction", 0.75),
        ("panel.file", contract["panel"]),
        ("panel.neutral_glyph", "🟰"),
        ("panel.centroid_mode", "panel"),
        ("source.wrappers_file", contract["source"]),
        ("source.max_wrappers", 16),
        ("targets.cases_file", EXPECTED_P2_TARGETS),
        ("targets.max_cases", 48),
        ("targets.calibration_cases", 12),
        ("capture.site", "resid_post"),
        ("capture.layers", [2, 4]),
        ("intervention.normalization", "rms"),
        ("intervention.strengths", [0.05]),
        ("intervention.clip.mode", "global_rms"),
        ("intervention.clip.max_ratio", 0.25),
        ("intervention.iso_kl.enabled", False),
        ("controls.random_directions_per_layer", 0),
        ("controls.zero_direction", True),
        ("controls.sign_flip", False),
        ("controls.sign_flip_strengths", []),
        ("controls.label_shuffle_permutations", 0),
        ("controls.include_neutral_direction", False),
        ("metrics.fingerprint_dim", 96),
        ("metrics.fingerprint_seed", 8_675_309),
        ("metrics.split_half_repeats", 1),
        ("surface.emoji_template", "{emoji}\n{prompt}"),
        ("surface.neutral_template", "{prompt}"),
    )
    for dotted_path, expected in expectations:
        _expect(config, dotted_path, expected, label=label)

    return {
        "path": label,
        "arm": contract["arm"],
        "panel": contract["panel"],
        "source": contract["source"],
        "targets": EXPECTED_P2_TARGETS,
        "layers": [2, 4],
        "strengths": [0.05],
        "seeds": [101, 211, 307],
    }


def _resolve_config_reference(root: Path, config_path: Path, value: str, *, label: str) -> Path:
    root = root.resolve()
    referenced = (config_path.parent / value).resolve()
    try:
        referenced.relative_to(root)
    except ValueError as exc:
        raise PreregistrationAuditError(
            f"{label}: config reference leaves the repository: {value}"
        ) from exc
    _require(referenced.is_file(), f"{label}: referenced file does not exist: {value}")
    return referenced


def _validate_mlx_receipt(root: Path, config_path: Path, config: Mapping[str, Any]) -> str:
    label = config_path.relative_to(root.resolve()).as_posix()
    receipt_value = _nested_value(config, "backend.validation_receipt")
    _require(isinstance(receipt_value, str), f"{label}: validation receipt path is not a string")
    receipt_path = _resolve_config_reference(root, config_path, receipt_value, label=label)
    receipt_sha = _sha256(receipt_path)
    _require(
        receipt_sha == EXPECTED_VALIDATION_RECEIPT_SHA256,
        f"{label}: MLX validation receipt digest mismatch",
    )
    receipt = _load_json_object(receipt_path, label="MLX validation receipt")
    _require(receipt.get("status") == "validated_mlx_selected", "MLX receipt is not validated")
    _require(receipt.get("model") == EXPECTED_MODEL_ID, "MLX receipt model mismatch")
    _require(receipt.get("revision") == EXPECTED_MODEL_REVISION, "MLX receipt revision mismatch")
    _require(receipt.get("dtype") == "float32", "MLX receipt dtype mismatch")
    return receipt_sha


def _validate_p2_configs(root: Path) -> list[dict[str, Any]]:
    root = root.resolve()
    reports: list[dict[str, Any]] = []
    receipt_shas: set[str] = set()
    for relative_path, contract in P2_CONFIG_CONTRACTS.items():
        config_path = _resolve_within_repo(root, relative_path)
        _require(config_path.is_file(), f"missing P2 config: {relative_path}")
        config, raw_text = _load_unique_yaml(config_path)
        report = validate_p2_config_document(
            config,
            raw_text,
            contract,
            label=relative_path,
        )
        for field in ("panel.file", "source.wrappers_file", "targets.cases_file"):
            value = _nested_value(config, field)
            _require(isinstance(value, str), f"{relative_path}: {field} must be a string")
            _resolve_config_reference(root, config_path, value, label=relative_path)
        receipt_shas.add(_validate_mlx_receipt(root, config_path, config))
        reports.append(report)
    _require(
        receipt_shas == {EXPECTED_VALIDATION_RECEIPT_SHA256},
        "P2 configs do not share the one pinned MLX validation receipt",
    )
    return reports


def audit_preregistration(
    root: Path,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    """Audit the frozen manifest, all listed bytes, and all eight P2 configs."""

    root = root.resolve()
    manifest_relative = _safe_repo_relative_path(manifest_path.as_posix())
    resolved_manifest = _resolve_within_repo(root, manifest_relative)
    _require(resolved_manifest.is_file(), f"missing preregistration manifest: {manifest_relative}")
    manifest = _load_json_object(resolved_manifest, label="preregistration manifest")
    _require(manifest.get("schema_version") == 1, "unsupported preregistration schema")
    _require(
        manifest.get("manifest_id") == EXPECTED_MANIFEST_ID,
        "unexpected preregistration manifest ID",
    )
    _require(
        manifest.get("protocol_id") == EXPECTED_PROTOCOL_ID,
        "unexpected preregistration protocol ID",
    )
    _require(manifest.get("hash_algorithm") == "sha256", "hash algorithm must be sha256")

    verified_files = validate_manifest_file_table(root, manifest)
    config_reports = _validate_p2_configs(root)
    return {
        "schema_version": 1,
        "audit_id": AUDIT_ID,
        "status": "pass",
        "manifest_path": manifest_relative,
        "manifest_sha256": _sha256(resolved_manifest),
        "manifest_id": EXPECTED_MANIFEST_ID,
        "protocol_id": EXPECTED_PROTOCOL_ID,
        "hash_algorithm": "sha256",
        "frozen_file_count": len(verified_files),
        "p2_config_count": len(config_reports),
        "mlx_validation_receipt_sha256": EXPECTED_VALIDATION_RECEIPT_SHA256,
        "verified_files": verified_files,
        "p2_configs": config_reports,
        "model_or_tokenizer_loaded": False,
    }


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _emit(value: Mapping[str, Any], output: Path | None) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
    print(payload)
    if output is not None:
        _atomic_write_json(output, value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: inferred from this script).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Canonical repository-relative preregistration manifest path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for an atomic copy of the JSON audit receipt.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = audit_preregistration(args.root, args.manifest)
    except (PreregistrationAuditError, OSError, UnicodeError, ValueError) as exc:
        failure = {
            "schema_version": 1,
            "audit_id": AUDIT_ID,
            "status": "fail",
            "manifest_path": args.manifest.as_posix(),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "model_or_tokenizer_loaded": False,
        }
        _emit(failure, args.output)
        return 1
    _emit(report, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
