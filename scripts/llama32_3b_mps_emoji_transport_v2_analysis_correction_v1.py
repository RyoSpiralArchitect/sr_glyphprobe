#!/usr/bin/env python3
"""Shared authority checks for the v2 analysis-validation correction v1.

This module is intentionally science-free.  It validates the additive
post-execution correction authority and reconstructs only the exact Rich
80-column completion-path presentation observed in the ten frozen launcher
logs.  It never loads model weights, tokenizers, intervention arrays, target
banks, or scientific result rows.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import hashlib
import json
from pathlib import Path
import re
from typing import Any


CORRECTION_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2-analysis-correction-v1"
BASE_PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2"
PARSER_CONTRACT = "rich_width80_exact_marker_plus_two_path_lines_v1"
CORRECTION_MANIFEST_PATH = Path(
    "data/manifests/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.json"
)
CORRECTION_PREFLIGHT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/analysis_correction_v1_preflight.json"
)
ANALYSIS_OUTPUT_DIR = Path(
    "runs/e2-llama32-3b-mps-emoji-transport-analysis-v2-correction-v1"
)
ANALYSIS_RECEIPT_FILENAME = "llama32_3b_mps_emoji_transport_v2_receipt.json"
BASE_BUNDLE_ROOT = Path("artifacts/llama32_3b_mps_emoji_transport_v2")
BASE_ROOT_MANIFEST_PATH = Path(
    "artifacts/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_MANIFEST.json"
)

UPSTREAM_PATHS = {
    "v2_manifest": Path("data/manifests/llama32_3b_mps_emoji_transport_v2.json"),
    "v2_tokenizer_preflight": Path(
        "artifacts/llama32_3b_mps_emoji_transport_v2/preflight/"
        "tokenization_audit_v2.json"
    ),
    "v2_attempt_receipt": Path(
        "validation/llama32_3b_mps_emoji_transport_v2/attempt_started_receipt.json"
    ),
    "v2_execution_receipt": Path(
        "validation/llama32_3b_mps_emoji_transport_v2/execution_receipt.json"
    ),
    "v2_analyzer": Path("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py"),
    "v2_builder": Path("scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py"),
    "v2_validator": Path(
        "scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py"
    ),
}
UPSTREAM_SHA256 = {
    "v2_manifest": ("018f658a3fe0b810d6512a248f3628c1bec1a238171189eb84029bbc84113b46"),
    "v2_tokenizer_preflight": (
        "22851fef18d06b740aa88117a0b801d780d063da990c039e691ef266863f2a80"
    ),
    "v2_attempt_receipt": (
        "cf89f191a45b4499654ee8fec2e85e7035689df259919378bc399e14ce78534a"
    ),
    "v2_execution_receipt": (
        "0bafb88c1487d6ec6c67dcf49a3a6134a09c117904a25c1853e79c6d3b9b273d"
    ),
    "v2_analyzer": ("1b9502771c4be7073c78b4eb16097db5f1c648724e5d8af9f076293227b44f56"),
    "v2_builder": ("c9074fa540e232cd595dd4a6ad4fa272c1580324d47b352481e3142453bf83a0"),
    "v2_validator": (
        "b6e2948ca0cd0b445df182e5fdf64bd441df4953dc9399eeeb9c573cd659c127"
    ),
}

CORRECTION_FILE_PATHS = {
    "helper": Path(
        "scripts/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
    ),
    "analyzer_adapter": Path(
        "scripts/analyze_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
    ),
    "audit": Path(
        "scripts/audit_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
    ),
    "bundle_builder": Path(
        "scripts/build_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py"
    ),
    "bundle_validator": Path(
        "scripts/validate_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py"
    ),
    "analyzer_tests": Path(
        "tests/test_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
    ),
    "bundle_tests": Path(
        "tests/test_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py"
    ),
    "protocol_en": Path(
        "docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_ANALYSIS_CORRECTION_V1.md"
    ),
    "protocol_ja": Path(
        "docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_ANALYSIS_CORRECTION_V1.ja.md"
    ),
}

ARMS = ("full50", "core35")
FAMILIES = ("sky", "food", "animals", "transport", "social")
CELL_ORDER = tuple((arm, family) for arm in ARMS for family in FAMILIES)
HEX_64 = re.compile(r"[0-9a-f]{64}")
COMMIT_40 = re.compile(r"[0-9a-f]{40}")
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:/(?:Users|home|private|tmp|Volumes)/|/var/folders/|"
    r"(?<![A-Za-z0-9])[A-Za-z]:[\\/])"
)


class AnalysisCorrectionError(RuntimeError):
    """Raised when the additive correction authority is not exact."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisCorrectionError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AnalysisCorrectionError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_object(path: Path, description: str) -> dict[str, Any]:
    candidate = Path(path)
    _require(
        candidate.is_file() and not candidate.is_symlink(),
        f"Missing or invalid {description}: {candidate}",
    )
    try:
        value = json.loads(
            candidate.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                AnalysisCorrectionError(
                    f"Non-finite JSON token in {description}: {token}"
                )
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AnalysisCorrectionError(f"Invalid {description}: {candidate}") from exc
    _require(isinstance(value, dict), f"{description} must be a JSON object")
    return value


def _binding(root: Path, relative: Path) -> dict[str, str]:
    path = root / relative
    _require(
        path.is_file() and not path.is_symlink(),
        f"Missing correction authority file: {relative}",
    )
    return {"path": relative.as_posix(), "sha256": sha256_file(path)}


def _all_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key)
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def _validate_relative_path(value: Any, description: str) -> Path:
    _require(isinstance(value, str) and value, f"Missing path: {description}")
    path = Path(value)
    _require(
        not path.is_absolute() and ".." not in path.parts,
        f"Non-relative path: {description}",
    )
    _require(path.as_posix() == value, f"Non-canonical path: {description}")
    return path


def parse_completion_wrap(
    payload: bytes,
    *,
    expected_run_dir: Path,
    expected_run_id: str,
) -> dict[str, Any]:
    """Validate the one observed Rich completion-path presentation.

    The accepted byte layout is exactly one marker-only line followed by two
    path-fragment lines.  The first fragment is exactly 80 bytes, the final
    fragment is 1..80 bytes, and the next physical line begins the top-level
    JSON report.  No generic whitespace or multiline normalization is used.
    """

    _require(isinstance(payload, bytes), "Launcher log payload must be bytes")
    resolved = Path(expected_run_dir).resolve()
    _require(resolved.is_absolute(), "Expected run directory must be absolute")
    _require(
        isinstance(expected_run_id, str)
        and expected_run_id
        and resolved.name == expected_run_id,
        "Expected run ID does not match the resolved directory basename",
    )
    expected = str(resolved).encode("utf-8")
    run_id_bytes = expected_run_id.encode("utf-8")
    _require(b"\x1b" not in payload, "ANSI escape bytes are forbidden in r1 logs")
    _require(
        expected not in payload,
        "Unwrapped completion path is already contiguous; r1 is inapplicable",
    )
    _require(
        run_id_bytes not in payload,
        "Unwrapped run ID is already contiguous; r1 is inapplicable",
    )

    lines = payload.split(b"\n")
    marker_indices = [
        index for index, line in enumerate(lines) if line == b"Complete  "
    ]
    _require(
        len(marker_indices) == 1,
        "Expected exactly one marker-only Complete record",
    )
    index = marker_indices[0]
    _require(index + 3 < len(lines), "Truncated completion record")
    first = lines[index + 1]
    second = lines[index + 2]
    following = lines[index + 3]
    _require(len(first) == 80, "First path fragment must be exactly 80 bytes")
    _require(1 <= len(second) <= 80, "Final path fragment length differs")
    _require(following == b"{", "Completion path must end before top-level JSON")
    for fragment in (first, second):
        _require(
            all(33 <= byte <= 126 for byte in fragment),
            "Path fragments contain whitespace, control, or non-ASCII bytes",
        )
    candidate = first + second
    _require(candidate == expected, "Reconstructed completion path differs")
    _require(
        Path(candidate.decode("utf-8")).name == expected_run_id,
        "Reconstructed completion run ID differs",
    )
    return {
        "parser_contract": PARSER_CONTRACT,
        "status": "accepted",
        "wrap_width": 80,
        "segment_count": 2,
        "segment_lengths": [len(first), len(second)],
        "raw_contiguous_path_match": False,
        "raw_contiguous_run_id_match": False,
    }


def validate_correction_manifest(root: Path) -> dict[str, Any]:
    """Validate the additive manifest without opening launcher logs or runs."""

    resolved_root = Path(root).resolve()
    manifest_path = resolved_root / CORRECTION_MANIFEST_PATH
    manifest = load_json_object(manifest_path, "analysis correction manifest")
    expected_keys = {
        "schema_version",
        "correction_id",
        "base_protocol_id",
        "status",
        "scope",
        "upstream",
        "correction_files",
        "launcher_logs",
        "publication",
    }
    _require(set(manifest) == expected_keys, "Correction manifest keys differ")
    _require(manifest.get("schema_version") == 1, "Correction schema differs")
    _require(manifest.get("correction_id") == CORRECTION_ID, "Correction ID differs")
    _require(
        manifest.get("base_protocol_id") == BASE_PROTOCOL_ID,
        "Base protocol ID differs",
    )
    _require(
        manifest.get("status") == "frozen_before_endpoint_computation",
        "Correction freeze status differs",
    )
    expected_scope = {
        "correction_type": "post_execution_presentation_layer_admission_fix",
        "completion_parser_contract": PARSER_CONTRACT,
        "scientific_cell_changed": False,
        "endpoint_math_changed": False,
        "bootstrap_changed": False,
        "row_contract_changed": False,
        "run_artifacts_changed": False,
        "source_logs_changed": False,
        "execution_reused": True,
        "post_execution_correction": True,
        "human_result_values_observed_before_freeze": False,
        "software_loaded_and_validated_run_arrays_before_block": True,
        "endpoint_or_bootstrap_computed_before_freeze": False,
        "analysis_output_published_before_freeze": False,
    }
    _require(manifest.get("scope") == expected_scope, "Correction scope differs")

    upstream = manifest.get("upstream")
    expected_upstream: dict[str, dict[str, str]] = {}
    for name, relative in UPSTREAM_PATHS.items():
        binding = _binding(resolved_root, relative)
        _require(
            binding["sha256"] == UPSTREAM_SHA256[name],
            f"Frozen upstream hash differs: {name}",
        )
        expected_upstream[name] = binding
    _require(upstream == expected_upstream, "Upstream authority bindings differ")

    correction_files = manifest.get("correction_files")
    expected_files = {
        name: _binding(resolved_root, relative)
        for name, relative in CORRECTION_FILE_PATHS.items()
    }
    _require(
        correction_files == expected_files,
        "Correction implementation bindings differ",
    )

    execution = load_json_object(
        resolved_root / UPSTREAM_PATHS["v2_execution_receipt"],
        "v2 execution receipt",
    )
    processes = execution.get("processes")
    logs = manifest.get("launcher_logs")
    _require(
        isinstance(processes, list)
        and isinstance(logs, list)
        and len(processes) == len(logs) == 10,
        "Launcher-log grid differs",
    )
    for index, ((arm, role), process, row) in enumerate(
        zip(CELL_ORDER, processes, logs)
    ):
        _require(
            isinstance(process, Mapping) and isinstance(row, Mapping),
            f"Invalid launcher-log row: {index}",
        )
        expected_log_path = process.get("log_path")
        expected_log_sha = process.get("log_sha256")
        run_relative = _validate_relative_path(
            row.get("expected_run_relative_path"),
            f"launcher_logs[{index}].expected_run_relative_path",
        )
        run_id = row.get("expected_run_id")
        expected_prefix = f"e2-llama32-3b-mps-{arm}-{role}-transport-v2--"
        _require(
            isinstance(run_id, str)
            and run_id == run_relative.name
            and run_id.startswith(expected_prefix),
            f"Expected run identity differs: {index}",
        )
        _require(
            dict(row)
            == {
                "index": index,
                "panel_arm": arm,
                "role": role,
                "path": expected_log_path,
                "sha256": expected_log_sha,
                "expected_run_relative_path": run_relative.as_posix(),
                "expected_run_id": run_id,
                "wrap_width": 80,
                "segment_count": 2,
            },
            f"Launcher-log binding differs: {index}",
        )
        _validate_relative_path(expected_log_path, f"launcher_logs[{index}].path")
        _require(
            isinstance(expected_log_sha, str) and HEX_64.fullmatch(expected_log_sha),
            f"Launcher-log SHA differs: {index}",
        )

    expected_publication = {
        "correction_preflight_path": CORRECTION_PREFLIGHT_PATH.as_posix(),
        "analysis_output_dir": ANALYSIS_OUTPUT_DIR.as_posix(),
        "analysis_output_receipt_filename": ANALYSIS_RECEIPT_FILENAME,
        "bundle_root": BASE_BUNDLE_ROOT.as_posix(),
        "root_manifest": BASE_ROOT_MANIFEST_PATH.as_posix(),
        "active_correction_validator": CORRECTION_FILE_PATHS[
            "bundle_validator"
        ].as_posix(),
        "analysis_output_must_be_absent_at_preflight": True,
    }
    _require(
        manifest.get("publication") == expected_publication,
        "Correction publication contract differs",
    )
    _require(
        not any(
            ABSOLUTE_PATH_PATTERN.search(value) for value in _all_strings(manifest)
        ),
        "Correction manifest contains an absolute local path",
    )
    return manifest


def validate_correction_preflight(
    root: Path, manifest: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate the generated model-free correction preflight receipt."""

    resolved_root = Path(root).resolve()
    authority = (
        validate_correction_manifest(resolved_root)
        if manifest is None
        else dict(manifest)
    )
    path = resolved_root / CORRECTION_PREFLIGHT_PATH
    receipt = load_json_object(path, "analysis correction preflight")
    expected_keys = {
        "schema_version",
        "correction_id",
        "base_protocol_id",
        "status",
        "audit_role",
        "manifest",
        "upstream_execution_receipt",
        "git_authority",
        "legacy_analyzer_attempts",
        "process_boundary",
        "completion_records",
        "summary",
        "authorization",
    }
    _require(set(receipt) == expected_keys, "Correction preflight keys differ")
    _require(receipt.get("schema_version") == 1, "Preflight schema differs")
    _require(receipt.get("correction_id") == CORRECTION_ID, "Preflight ID differs")
    _require(
        receipt.get("base_protocol_id") == BASE_PROTOCOL_ID,
        "Preflight base protocol differs",
    )
    _require(receipt.get("status") == "passed", "Correction preflight did not pass")
    _require(
        receipt.get("audit_role")
        == "model_free_post_execution_pre_endpoint_log_presentation_correction",
        "Correction audit role differs",
    )
    _require(
        receipt.get("manifest") == _binding(resolved_root, CORRECTION_MANIFEST_PATH),
        "Correction preflight manifest binding differs",
    )
    _require(
        receipt.get("upstream_execution_receipt")
        == authority["upstream"]["v2_execution_receipt"],
        "Correction preflight execution binding differs",
    )
    git_authority = receipt.get("git_authority")
    _require(isinstance(git_authority, Mapping), "Git authority is missing")
    audited_commit = git_authority.get("audited_commit")
    _require(
        isinstance(audited_commit, str)
        and COMMIT_40.fullmatch(audited_commit)
        and git_authority.get("branch") == "main"
        and git_authority.get("origin_main_commit") == audited_commit
        and git_authority.get("worktree_clean_before_publication") is True,
        "Correction preflight Git authority differs",
    )
    _require(
        receipt.get("legacy_analyzer_attempts")
        == {
            "evidence_class": "operator_attested_incident_record",
            "failed_invocation_artifacts_cryptographically_bound": False,
            "count": 2,
            "run_arrays_loaded_and_validated": True,
            "stopped_before_endpoint_construction": True,
            "stopped_before_bootstrap": True,
            "analysis_output_directory_created": False,
            "human_result_values_observed": False,
            "error": "Launcher log does not bind supplied run for full50/sky",
        },
        "Legacy analyzer incident record differs",
    )
    _require(
        receipt.get("process_boundary")
        == {
            "model_forward_count": 0,
            "tokenizer_call_count": 0,
            "run_arrays_loaded_by_preflight": False,
            "endpoint_or_bootstrap_computed_by_preflight": False,
            "scientific_result_rows_read_by_preflight": False,
            "protected_bank_content_accessed": False,
            "source_logs_changed": False,
            "run_artifacts_changed": False,
        },
        "Correction preflight process boundary differs",
    )

    records = receipt.get("completion_records")
    manifest_logs = authority.get("launcher_logs")
    _require(
        isinstance(records, list)
        and isinstance(manifest_logs, list)
        and len(records) == len(manifest_logs) == 10,
        "Correction completion-record grid differs",
    )
    for index, (record, declared) in enumerate(zip(records, manifest_logs)):
        _require(
            isinstance(record, Mapping) and isinstance(declared, Mapping),
            f"Invalid completion record: {index}",
        )
        lengths = record.get("segment_lengths")
        _require(
            isinstance(lengths, list)
            and len(lengths) == 2
            and lengths[0] == 80
            and isinstance(lengths[1], int)
            and 1 <= lengths[1] <= 80,
            f"Completion segment lengths differ: {index}",
        )
        _require(
            dict(record)
            == {
                "index": index,
                "panel_arm": declared.get("panel_arm"),
                "role": declared.get("role"),
                "log_path": declared.get("path"),
                "log_sha256": declared.get("sha256"),
                "expected_run_relative_path": declared.get(
                    "expected_run_relative_path"
                ),
                "expected_run_id": declared.get("expected_run_id"),
                "parser_contract": PARSER_CONTRACT,
                "status": "accepted",
                "wrap_width": 80,
                "segment_count": 2,
                "segment_lengths": lengths,
                "raw_contiguous_path_match": False,
                "raw_contiguous_run_id_match": False,
            },
            f"Completion record differs: {index}",
        )
    _require(
        receipt.get("summary")
        == {
            "expected_record_count": 10,
            "accepted_record_count": 10,
            "ambiguous_record_count": 0,
            "raw_contiguous_path_match_count": 0,
            "raw_contiguous_run_id_match_count": 0,
            "completion_parser_contract": PARSER_CONTRACT,
            "analysis_output_absent": True,
        },
        "Correction preflight summary differs",
    )
    _require(
        receipt.get("authorization")
        == {
            "corrected_analysis_authorized": True,
            "corrected_bundle_publication_authorized_after_analysis": True,
            "scientific_claim_strength_increased": False,
        },
        "Correction analysis authorization differs",
    )
    return receipt


def analysis_validation_correction_block(
    root: Path, *, adapter_path: Path
) -> dict[str, Any]:
    """Return the exact provenance block embedded in the analysis receipt."""

    resolved_root = Path(root).resolve()
    validate_correction_manifest(resolved_root)
    validate_correction_preflight(resolved_root)
    return {
        "correction_id": CORRECTION_ID,
        "adapter": _binding(resolved_root, adapter_path),
        "helper": _binding(resolved_root, CORRECTION_FILE_PATHS["helper"]),
        "manifest": _binding(resolved_root, CORRECTION_MANIFEST_PATH),
        "preflight": _binding(resolved_root, CORRECTION_PREFLIGHT_PATH),
        "scientific_math_changed": False,
        "endpoint_definitions_changed": False,
        "bootstrap_changed": False,
        "execution_reused": True,
        "source_logs_changed": False,
    }
