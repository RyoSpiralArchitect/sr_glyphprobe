#!/usr/bin/env python3
"""Freeze and audit the post-failure T13-EA zero-gate amendment.

This auditor reads only repository-resident protocol documents, manifests, and
receipts. It never opens the sealed run or any scientific response value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml


AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
SOURCE_ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
SOURCE_ANALYSIS_COMMIT = "7fedd4001bf3b127f3039bd2b4ec1b40d186edef"
STATUS_AT_FREEZE = (
    "post_failure_nonadaptive_numerical_amendment_before_live_js_residual_"
    "magnitude_inspection"
)
SCHEMA_VERSION = 1

CONFIG_PATH = Path("configs/emoji_steering_specificity_zero_gate_amendment_v1.yaml")
SOURCE_FREEZE_PATH = Path("data/manifests/emoji_steering_specificity_analysis_v0.json")
SOURCE_FREEZE_SHA256 = (
    "91c7f96cfd5fcb0026a304bcc8981b51e49090cb4fdebae15987ce3c53fa89dc"
)
CLOSEOUT_PATH = Path(
    "validation/emoji_steering_specificity_analysis_v0/"
    "glyphprobe-t13ea-closeout-7fedd40.json"
)
CLOSEOUT_SHA256 = "bc821f2f80b46c7c50d02cc5943010c6df9a8b91c144bfcca98d4ae0104dcb6b"
FAILURE_RECEIPT_PATH = Path(
    "validation/emoji_steering_specificity_analysis_v0/"
    "zero_gate_v0_failure_receipt.json"
)
FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_zero_gate_amendment_v1.json"
)

FLOAT32_EPSILON_MULTIPLIER = 8
MAXIMUM_ABSOLUTE_JS = float(FLOAT32_EPSILON_MULTIPLIER * np.finfo(np.float32).eps)

EXACT_PRIMITIVES = [
    "kl_baseline_to_intervened_equals_zero",
    "total_variation_equals_zero",
    "logit_delta_rms_equals_zero",
    "baseline_entropy_equals_intervened_entropy",
    "baseline_argmax_equals_intervened_argmax",
    "argmax_flip_is_false",
    "top_positive_values_equal_zero",
    "top_negative_values_equal_zero",
    "countsketch_equals_zero",
    "top_positive_ids_in_vocab",
    "top_negative_ids_in_vocab",
    "baseline_argmax_id_in_vocab",
    "intervened_argmax_id_in_vocab",
]

FROZEN_INPUTS = (
    SOURCE_FREEZE_PATH,
    CLOSEOUT_PATH,
    FAILURE_RECEIPT_PATH,
    CONFIG_PATH,
    Path("docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md"),
    Path("docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md"),
    Path("scripts/analyze_emoji_steering_specificity_geometry_v1.py"),
    Path("scripts/analyze_emoji_steering_specificity_outcomes_v1.py"),
    Path("tests/test_analyze_emoji_steering_specificity_geometry_v1.py"),
    Path("tests/test_analyze_emoji_steering_specificity_outcomes_v1.py"),
    Path("scripts/audit_emoji_steering_specificity_zero_gate_amendment_v1.py"),
    Path("tests/test_emoji_steering_specificity_zero_gate_amendment_v1.py"),
)

FAILURE_RECEIPT_KEYS = {
    "analysis_output_written",
    "closeout_receipt",
    "exact_failed_value_recorded",
    "failure_field",
    "failure_observation_scope",
    "nonzero_scientific_values_opened",
    "original_analysis_commit",
    "original_analysis_freeze",
    "preserved_as_negative_procedural_result",
    "receipt_id",
    "schema_version",
    "status",
}


class AmendmentBoundaryError(RuntimeError):
    """Raised when the zero-gate amendment boundary is incomplete or changed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AmendmentBoundaryError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _read_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected YAML object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _write_json_new(path: Path, value: Mapping[str, Any]) -> None:
    _require(not path.exists(), f"Refusing to overwrite amendment freeze: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = path.parent / f".{path.name}.stage-{uuid.uuid4().hex}"
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as error:
        temporary.unlink()
        raise AmendmentBoundaryError(
            f"Refusing to overwrite amendment freeze: {path}"
        ) from error
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    temporary.unlink()


def _check_repository_binding(relative: Path, expected_sha256: str) -> None:
    path = _root() / relative
    _require(path.is_file(), f"Required amendment source is missing: {relative}")
    _require(_sha256(path) == expected_sha256, f"Source hash changed: {relative}")


def _config() -> dict[str, Any]:
    config = _read_yaml(_root() / CONFIG_PATH)
    _require(config.get("amendment_id") == AMENDMENT_ID, "Amendment ID changed")
    _require(
        config.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Source analysis ID changed",
    )
    _require(
        config.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Source protocol ID changed",
    )
    _require(
        config.get("status_at_freeze") == STATUS_AT_FREEZE,
        "Amendment freeze status changed",
    )
    _require(config.get("amendment_scope") == "zero_control_gate_only", "Scope changed")
    return config


def _audit_failure_receipt(config: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _read_json(_root() / FAILURE_RECEIPT_PATH)
    _require(set(receipt) == FAILURE_RECEIPT_KEYS, "Failure receipt schema changed")
    _require(receipt.get("schema_version") == 1, "Failure receipt version changed")
    _require(
        receipt.get("receipt_id") == "glyphprobe-t13ea-zero-gate-v0-failure",
        "Failure receipt ID changed",
    )
    _require(
        receipt.get("status")
        == "v0_zero_gate_failed_closed_before_nonzero_scientific_open",
        "Failure receipt status changed",
    )
    _require(receipt.get("failure_field") == "js_divergence", "Failure field changed")
    _require(
        receipt.get("failure_observation_scope") == "zero_control_gate_only",
        "Failure observation scope changed",
    )
    _require(
        receipt.get("original_analysis_commit") == SOURCE_ANALYSIS_COMMIT,
        "Original analysis commit changed",
    )
    _require(
        receipt.get("analysis_output_written") is False, "Failed output was written"
    )
    _require(
        receipt.get("nonzero_scientific_values_opened") is False,
        "Nonzero scientific value read recorded",
    )
    _require(
        receipt.get("exact_failed_value_recorded") is False,
        "Exact failed JS value entered the receipt",
    )
    _require(
        receipt.get("preserved_as_negative_procedural_result") is True,
        "Original failed gate was not preserved",
    )
    _require(
        receipt.get("original_analysis_freeze")
        == {"path": str(SOURCE_FREEZE_PATH), "sha256": SOURCE_FREEZE_SHA256},
        "Failure receipt source freeze binding changed",
    )
    _require(
        receipt.get("closeout_receipt")
        == {"path": str(CLOSEOUT_PATH), "sha256": CLOSEOUT_SHA256},
        "Failure receipt closeout binding changed",
    )
    provenance = config["provenance"]
    _require(
        provenance["failure_receipt"]["path"] == str(FAILURE_RECEIPT_PATH),
        "Config failure receipt path changed",
    )
    return receipt


def audit_design() -> dict[str, Any]:
    """Audit the numerical amendment without opening any sealed-run value."""

    config = _config()
    _check_repository_binding(SOURCE_FREEZE_PATH, SOURCE_FREEZE_SHA256)
    _check_repository_binding(CLOSEOUT_PATH, CLOSEOUT_SHA256)

    provenance = config["provenance"]
    _require(
        provenance["original_analysis_commit"] == SOURCE_ANALYSIS_COMMIT,
        "Config source commit changed",
    )
    _require(
        provenance["original_analysis_freeze"]
        == {"path": str(SOURCE_FREEZE_PATH), "sha256": SOURCE_FREEZE_SHA256},
        "Config source freeze binding changed",
    )
    _require(
        provenance["verified_closeout"]
        == {"path": str(CLOSEOUT_PATH), "sha256": CLOSEOUT_SHA256},
        "Config closeout binding changed",
    )
    _require(
        provenance["failure_observation_scope"] == "zero_control_field_identity_only",
        "Failure observation scope became broader",
    )
    _require(
        provenance["exact_live_js_residual_magnitude_inspected_before_freeze"] is False,
        "Exact failed JS magnitude was inspected before freeze",
    )
    _require(
        provenance["nonzero_scientific_values_opened_before_freeze"] is False,
        "Nonzero scientific values were opened before amendment freeze",
    )
    _require(
        provenance["analysis_output_written_by_failed_v0_attempt"] is False,
        "Failed v0 analysis output was written",
    )

    source_freeze = _read_json(_root() / SOURCE_FREEZE_PATH)
    _require(
        source_freeze.get("analysis_id") == SOURCE_ANALYSIS_ID
        and source_freeze.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Original analysis freeze identity changed",
    )
    _require(
        source_freeze.get("status")
        == "freeze_complete_before_t13eh_scientific_outcome_inspection"
        and source_freeze.get("scientific_outcomes_read") is False,
        "Original analysis freeze boundary changed",
    )
    closeout = _read_json(_root() / CLOSEOUT_PATH)
    _require(
        closeout.get("analysis_id") == SOURCE_ANALYSIS_ID
        and closeout.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Closeout identity changed",
    )
    _require(
        closeout.get("status") == "scientific_open_closeout_complete"
        and closeout.get("independent_hash_verification") is True
        and closeout.get("scientific_open_authorized") is True
        and closeout.get("scientific_values_parsed") is False,
        "Closeout boundary changed",
    )
    _require(_is_sha256(closeout.get("run_binding_root_sha256")), "Run binding missing")

    _audit_failure_receipt(config)

    basis = config["nonadaptive_basis"]
    _require(
        basis["classification"] == "post_failure_nonadaptive_numerical_amendment",
        "Amendment classification changed",
    )
    _require(
        basis["trigger_known_before_freeze"] == "js_divergence_exact_equality_failed",
        "Amendment trigger changed",
    )
    _require(
        basis["observed_residual_magnitude_used_to_choose_bound"] is False,
        "Observed JS residual was used to choose the bound",
    )
    _require(
        basis["bound_source"] == "fixed_float32_operation_chain_allowance",
        "JS bound source changed",
    )

    gate = config["corrected_zero_gate"]
    _require(gate["exact_primitives"] == EXACT_PRIMITIVES, "Exact primitives changed")
    js = gate["js_divergence"]
    _require(
        js["policy"] == "bounded_float32_log_exp_roundtrip_residual",
        "JS residual policy changed",
    )
    _require(
        js["float32_epsilon_multiplier"] == FLOAT32_EPSILON_MULTIPLIER,
        "Float32 epsilon multiplier changed",
    )
    _require(
        float(js["maximum_absolute"]) == MAXIMUM_ABSOLUTE_JS,
        "Float32 JS bound changed",
    )
    _require(js["two_sided"] is True, "JS bound must be two-sided")
    _require(js["finite_required"] is True, "JS residual must be finite")
    _require(
        js["label"] == "derived_float32_roundtrip_residual_not_exact",
        "JS reporting label changed",
    )
    _require(
        gate["any_exact_primitive_failure"] == "fail_closed", "Primitive fail policy"
    )
    _require(gate["any_js_bound_failure"] == "fail_closed", "JS fail policy changed")
    _require(
        gate["nonzero_open_before_full_gate"] == "forbidden",
        "Early nonzero open became allowed",
    )
    _require(
        config["reporting"]["preserve_v0_gate_failure_as_negative_procedural_result"]
        is True,
        "Original failure is no longer retained",
    )
    _require(
        config["reporting"]["report_exact_js_residual_as_exact_zero"] == "forbidden",
        "JS residual may not be called exact zero",
    )

    return {
        "amendment_id": AMENDMENT_ID,
        "source_analysis_id": SOURCE_ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "design_audit_pass_post_failure_nonadaptive",
        "failure_field_known": "js_divergence",
        "exact_live_js_residual_magnitude_inspected": False,
        "nonzero_scientific_values_opened": False,
        "analysis_output_written_by_failed_v0_attempt": False,
        "maximum_absolute_js": MAXIMUM_ABSOLUTE_JS,
        "bound_expression": "8 * numpy.finfo(numpy.float32).eps",
        "scientific_values_parsed_by_auditor": False,
    }


def freeze(output: Path = FREEZE_PATH) -> dict[str, Any]:
    """Write the amendment manifest after every roster file is integrated."""

    design = audit_design()
    bindings: dict[str, dict[str, Any]] = {}
    for relative in FROZEN_INPUTS:
        path = _root() / relative
        _require(path.is_file(), f"Amendment frozen input missing: {relative}")
        bindings[str(relative)] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    manifest = {
        **design,
        "schema_version": SCHEMA_VERSION,
        "status": (
            "freeze_complete_post_failure_nonadaptive_before_live_js_residual_"
            "magnitude_inspection"
        ),
        "input_roster": [str(path) for path in FROZEN_INPUTS],
        "inputs": bindings,
        "claim_boundary": _config()["claim_boundary"],
        "scientific_open_rule": (
            "all exact primitive zero-control checks and the frozen two-sided "
            "float32 JS bound must pass before any nonzero scientific value opens"
        ),
    }
    output_path = output if output.is_absolute() else _root() / output
    _write_json_new(output_path, manifest)
    return manifest


def audit_freeze(manifest_path: Path = FREEZE_PATH) -> dict[str, Any]:
    """Verify the exact manifest roster, sizes, and SHA-256 bindings."""

    audit_design()
    path = manifest_path if manifest_path.is_absolute() else _root() / manifest_path
    manifest = _read_json(path)
    _require(manifest.get("schema_version") == SCHEMA_VERSION, "Freeze version changed")
    _require(manifest.get("amendment_id") == AMENDMENT_ID, "Freeze amendment changed")
    _require(
        manifest.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Freeze source analysis changed",
    )
    _require(
        manifest.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Freeze source protocol changed",
    )
    _require(
        manifest.get("status")
        == (
            "freeze_complete_post_failure_nonadaptive_before_live_js_residual_"
            "magnitude_inspection"
        ),
        "Freeze status changed",
    )
    expected_roster = [str(value) for value in FROZEN_INPUTS]
    _require(
        manifest.get("input_roster") == expected_roster, "Freeze roster order changed"
    )
    inputs = manifest.get("inputs")
    _require(isinstance(inputs, dict), "Freeze bindings missing")
    _require(set(inputs) == set(expected_roster), "Freeze input roster changed")
    for relative in expected_roster:
        binding = inputs[relative]
        _require(
            isinstance(binding, dict) and set(binding) == {"bytes", "sha256"},
            f"Freeze binding schema changed: {relative}",
        )
        _require(_is_sha256(binding["sha256"]), f"Invalid SHA-256: {relative}")
        source = _root() / relative
        _require(source.is_file(), f"Frozen input missing: {relative}")
        _require(
            source.stat().st_size == int(binding["bytes"]),
            f"Frozen input size changed: {relative}",
        )
        _require(
            _sha256(source) == binding["sha256"],
            f"Frozen input hash changed: {relative}",
        )
    _require(
        manifest.get("exact_live_js_residual_magnitude_inspected") is False,
        "Freeze records exact live JS inspection",
    )
    _require(
        manifest.get("nonzero_scientific_values_opened") is False,
        "Freeze records a nonzero scientific read",
    )
    _require(
        manifest.get("scientific_values_parsed_by_auditor") is False,
        "Freeze auditor parsed scientific values",
    )
    _require(
        float(manifest.get("maximum_absolute_js")) == MAXIMUM_ABSOLUTE_JS,
        "Freeze JS bound changed",
    )
    return {
        "status": "amendment_freeze_audit_pass",
        "amendment_id": AMENDMENT_ID,
        "input_count": len(expected_roster),
        "scientific_values_parsed_by_auditor": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design")
    frozen = sub.add_parser("freeze")
    frozen.add_argument("--output", type=Path, default=FREEZE_PATH)
    audit = sub.add_parser("audit-freeze")
    audit.add_argument("--manifest", type=Path, default=FREEZE_PATH)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "freeze":
        result = freeze(args.output)
    else:
        result = audit_freeze(args.manifest)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
