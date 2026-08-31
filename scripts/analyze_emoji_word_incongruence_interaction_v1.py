#!/usr/bin/env python3
"""Narrow post-open implementation repair for the T15-A frozen analysis."""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Mapping
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_emoji_word_incongruence_interaction_v0 as original  # noqa: E402


ANALYSIS_ID = "glyphprobe-emoji-word-incongruence-interaction-analysis-repair-v1"
REPAIR_MANIFEST_PATH = Path(
    "data/manifests/emoji_word_incongruence_interaction_analysis_repair_v1.json"
)
FAILURE_RECEIPT_PATH = Path(
    "validation/emoji_word_incongruence_interaction_v0/analysis_v0_failure.json"
)


class InteractionAnalysisRepairError(RuntimeError):
    """Raised when the narrow T15-A analysis repair contract is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InteractionAnalysisRepairError(message)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _a0(run_root: Path) -> dict[str, Any]:
    """Original A0 with only the frozen structural repeat assertion repaired."""
    values: dict[tuple[str, int, float, str, str], list[float]] = defaultdict(list)
    for row in original._source_rows(run_root, "source_metrics.jsonl"):
        if row["source_kind"] != "core_pair":
            continue
        key = (
            str(row["model_role"]),
            int(row["site_index"]),
            float(row["depth_fraction"]),
            str(row["axis_id"]),
            str(row["congruence"]),
        )
        values[key].append(float(row["joint_additivity_residual_rms"]))
    records = []
    bases = {key[:-1] for key in values}
    for base in sorted(bases):
        congruent = values[(*base, "congruent")]
        incongruent = values[(*base, "incongruent")]
        _require(
            len(congruent) == len(incongruent) == 16,
            "A0 repaired repeat count changed",
        )
        records.append(
            {
                "model": base[0],
                "site_index": base[1],
                "depth_fraction": base[2],
                "axis_id": base[3],
                "value": float(np.median(incongruent) - np.median(congruent)),
            }
        )
    return {
        "estimand": "median_incongruent_residual_rms_minus_median_congruent_residual_rms",
        "axis_estimands": records,
        "summary": original._summarize_records(
            records,
            cell_fields=("model", "site_index", "depth_fraction"),
            unit_field="axis_id",
            expected_units=8,
            namespace="A0",
        ),
    }


def audit_repair() -> dict[str, Any]:
    original.t15.audit_freeze()
    manifest_path = _root() / REPAIR_MANIFEST_PATH
    _require(manifest_path.is_file(), "T15-A analysis repair manifest missing")
    manifest = original._read_json(manifest_path)
    _require(manifest.get("analysis_id") == ANALYSIS_ID, "Repair analysis ID changed")
    _require(
        manifest.get("status") == "post_open_implementation_repair_frozen",
        "Repair manifest status changed",
    )
    _require(
        manifest.get("only_allowed_code_change")
        == "A0 congruence-class repeat assertion 8 to 16",
        "Repair scope changed",
    )
    for relative, expected in manifest["assets"].items():
        path = _root() / relative
        _require(path.is_file(), f"Repair asset missing: {relative}")
        _require(
            original._sha256(path) == expected,
            f"Repair asset changed: {relative}",
        )
    failure = original._read_json(_root() / FAILURE_RECEIPT_PATH)
    _require(
        failure.get("status") == "failed_closed_before_any_analysis_output"
        and failure.get("analysis_output_created") is False
        and failure.get("response_values_shown_to_researcher") is False,
        "Original analysis failure boundary changed",
    )
    return {
        "status": "pass",
        "analysis_id": ANALYSIS_ID,
        "repair_manifest_sha256": original._sha256(manifest_path),
        "only_allowed_code_change": manifest["only_allowed_code_change"],
        "estimands_changed": False,
        "families_changed": False,
        "bootstrap_changed": False,
    }


def analyze(run_root: Path, output: Path) -> dict[str, Any]:
    repair = audit_repair()
    original_analysis_id = original.ANALYSIS_ID
    original_a0 = original._a0
    original_writer = original._write_json

    def repaired_writer(path: Path, value: Mapping[str, Any]) -> None:
        augmented = dict(value)
        augmented.update(
            {
                "analysis_id": ANALYSIS_ID,
                "analysis_repair": repair,
                "post_open_implementation_repair": True,
                "estimands_changed_by_repair": False,
            }
        )
        original_writer(path, augmented)

    original.ANALYSIS_ID = ANALYSIS_ID
    original._a0 = _a0
    original._write_json = repaired_writer
    try:
        return original.analyze(run_root, output)
    finally:
        original.ANALYSIS_ID = original_analysis_id
        original._a0 = original_a0
        original._write_json = original_writer


def validate_output(path: Path) -> dict[str, Any]:
    repair = audit_repair()
    value = original._read_json(path)
    _require(value.get("analysis_id") == ANALYSIS_ID, "Repair output ID changed")
    _require(
        value.get("family_order") == list(original.FAMILIES),
        "Repair output families changed",
    )
    _require(
        value.get("analysis_repair") == repair,
        "Repair output manifest binding changed",
    )
    _require(
        value.get("confirmatory_status") is False
        and value.get("causal_claim_authorized") is False,
        "Repair output claim boundary changed",
    )
    return {
        "status": "pass",
        "analysis_id": ANALYSIS_ID,
        "analysis_output_sha256": original._sha256(path),
        "complete_families": list(original.FAMILIES),
        "post_open_implementation_repair": True,
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    subparsers = value.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit-repair")
    run = subparsers.add_parser("analyze")
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    audit = subparsers.add_parser("validate-output")
    audit.add_argument("--path", type=Path, required=True)
    return value


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-repair":
        result = audit_repair()
    elif args.command == "analyze":
        result = analyze(args.run_root, args.output)
    else:
        result = validate_output(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
