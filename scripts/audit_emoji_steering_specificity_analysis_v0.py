#!/usr/bin/env python3
"""Freeze and audit the outcome-blind T13-EA analysis boundary.

The inventory command deliberately never parses response-ledger rows or loads
activation/logit values.  During the T13-EH queue it may inspect only sealed
paths, receipts, byte counts, NPY headers, and optionally content-blind hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import yaml


ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
CONFIG_PATH = Path("configs/emoji_steering_specificity_analysis_v0.yaml")
ACQUISITION_CONFIG_PATH = Path("configs/emoji_steering_specificity_harvest_v0.yaml")
ACQUISITION_FREEZE_PATH = Path(
    "data/manifests/emoji_steering_specificity_harvest_v0.json"
)
FREEZE_PATH = Path("data/manifests/emoji_steering_specificity_analysis_v0.json")
FROZEN_INPUTS = (
    CONFIG_PATH,
    ACQUISITION_CONFIG_PATH,
    ACQUISITION_FREEZE_PATH,
    Path("scripts/audit_emoji_steering_specificity_analysis_v0.py"),
    Path("tests/test_emoji_steering_specificity_analysis_v0.py"),
)


class AnalysisBoundaryError(RuntimeError):
    """Raised when the T13-EA outcome-blind boundary is violated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AnalysisBoundaryError(message)


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


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temporary = path.parent / f".{path.name}.stage-{uuid.uuid4().hex}"
    with temporary.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _config() -> dict[str, Any]:
    value = _read_yaml(_root() / CONFIG_PATH)
    _require(value.get("analysis_id") == ANALYSIS_ID, "T13-EA analysis ID changed")
    _require(
        value.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EA source protocol changed",
    )
    return value


def _acquisition_config() -> dict[str, Any]:
    value = _read_yaml(_root() / ACQUISITION_CONFIG_PATH)
    _require(
        value.get("protocol_id") == SOURCE_PROTOCOL_ID,
        "T13-EA acquisition binding changed",
    )
    return value


def audit_design() -> dict[str, Any]:
    config = _config()
    acquisition = _acquisition_config()
    gate = config["acquisition_gate"]
    integrity = config["integrity_gate"]
    roles = [str(value) for value in gate["required_role_order"]]
    pilots = [str(value) for value in gate["pilot_roles"]]
    _require(
        roles == [str(value) for value in acquisition["models"]["order"]],
        "T13-EA role order differs from acquisition",
    )
    _require(
        pilots == [str(value) for value in acquisition["pilot"]["roles"]],
        "T13-EA pilot roles differ from acquisition",
    )
    _require(
        bool(gate["scientific_open_requires_all_roles_complete"]),
        "T13-EA must require the full queue",
    )
    _require(
        "response_ledger_metric_parsing" in gate["forbidden_during_queue"],
        "T13-EA queue blind must forbid ledger metric parsing",
    )
    _require(
        int(integrity["expected_source_shards_per_role"])
        == int(acquisition["source_bank"]["expected_shards_per_model"])
        == 12,
        "T13-EA source shard count changed",
    )
    _require(
        int(integrity["expected_response_rows_per_pilot_role"])
        == int(acquisition["pilot"]["expected_response_rows_per_model"])
        == 127_744,
        "T13-EA pilot row count changed",
    )
    _require(
        int(integrity["required_generation_calls"]) == 0,
        "T13-EA generation guard changed",
    )
    _require(
        config["reporting"]["no_confirmatory_verdict"] is True,
        "T13-EA cannot authorize confirmation",
    )
    _require(
        config["future_confirmation"]["t13eh_observations_in_confirmatory_statistic"]
        == "forbidden",
        "T13-EA observations cannot enter T13-C",
    )
    family_ids = [str(row["id"]) for row in config["scientific_output_families"]]
    _require(
        family_ids
        == [
            "F1_item_source_form",
            "F2_prototype_depth_dose",
            "F3_random_null_calibration",
            "F4_target_sensitivity",
            "F5_output_direction",
            "F6_source_geometry",
        ],
        "T13-EA output family order changed",
    )
    return {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "status": "design_audit_pass",
        "required_roles": roles,
        "pilot_roles": pilots,
        "scientific_output_family_ids": family_ids,
        "scientific_outcomes_read": False,
    }


def freeze(output: Path = FREEZE_PATH) -> dict[str, Any]:
    design = audit_design()
    bindings: dict[str, dict[str, Any]] = {}
    for relative in FROZEN_INPUTS:
        path = _root() / relative
        _require(path.is_file(), f"T13-EA frozen input missing: {relative}")
        bindings[str(relative)] = {
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
    manifest = {
        **design,
        "status": "freeze_complete_before_t13eh_scientific_outcome_inspection",
        "inputs": bindings,
        "queue_time_allowed_inspection": (
            "sealed paths, count fields, declared bytes, NPY headers, and optional "
            "content-blind SHA-256 only"
        ),
        "scientific_open_gate": "all_nine_roles_complete_and_independent_hash_pass",
        "claim_boundary": _config()["claim_boundary"],
    }
    _write_json(_root() / output, manifest)
    return manifest


def audit_freeze() -> dict[str, Any]:
    audit_design()
    manifest = _read_json(_root() / FREEZE_PATH)
    _require(
        manifest.get("analysis_id") == ANALYSIS_ID,
        "T13-EA freeze analysis ID changed",
    )
    _require(
        manifest.get("status")
        == "freeze_complete_before_t13eh_scientific_outcome_inspection",
        "T13-EA freeze status changed",
    )
    for relative, binding in manifest["inputs"].items():
        path = _root() / relative
        _require(path.is_file(), f"T13-EA frozen input missing: {relative}")
        _require(
            path.stat().st_size == int(binding["bytes"]),
            f"T13-EA size changed: {relative}",
        )
        _require(_sha256(path) == binding["sha256"], f"T13-EA hash changed: {relative}")
    return {"status": "freeze_audit_pass", "analysis_id": ANALYSIS_ID}


def _is_hidden_stage(path: Path, role_directory: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(role_directory).parts)


def _sealed_receipts(role_directory: Path) -> list[Path]:
    if not role_directory.is_dir():
        return []
    return sorted(
        path
        for path in role_directory.rglob("receipt.json")
        if not _is_hidden_stage(path, role_directory)
    )


def _receipt_kind(path: Path, role_directory: Path) -> str:
    relative = path.parent.relative_to(role_directory)
    parts = relative.parts
    if parts == ("baseline",):
        return "baseline"
    if len(parts) == 2 and parts[0] == "source":
        return "source"
    if len(parts) == 3 and parts[0] == "pilot":
        return f"pilot_{parts[1]}"
    return "unexpected"


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _audit_receipt(
    path: Path,
    *,
    role: str,
    verify_hashes: bool,
) -> dict[str, Any]:
    receipt = _read_json(path)
    _require(
        receipt.get("protocol_id") == SOURCE_PROTOCOL_ID, f"Protocol mismatch: {path}"
    )
    _require(receipt.get("model_role") == role, f"Role mismatch: {path}")
    _require(
        int(receipt.get("generation_calls", -1)) == 0,
        f"Generation count changed: {path}",
    )
    files = receipt.get("files")
    _require(isinstance(files, dict) and files, f"Missing file bindings: {path}")
    declared_bytes = 0
    header_shapes: Counter[str] = Counter()
    line_counts: dict[str, int] = {}
    hashes_verified = 0
    for name, binding in sorted(files.items()):
        _require(isinstance(binding, dict), f"Invalid binding: {path}/{name}")
        candidate = path.parent / str(name)
        _require(candidate.is_file(), f"Bound file missing: {candidate}")
        expected_bytes = int(binding["bytes"])
        _require(
            candidate.stat().st_size == expected_bytes,
            f"Byte count changed: {candidate}",
        )
        declared_bytes += expected_bytes
        if verify_hashes:
            _require(
                _sha256(candidate) == str(binding["sha256"]),
                f"Hash changed: {candidate}",
            )
            hashes_verified += 1
        if candidate.suffix == ".npy":
            array = np.load(candidate, mmap_mode="r", allow_pickle=False)
            header_shapes[f"{array.dtype}:{list(array.shape)}"] += 1
            del array
        elif candidate.name.endswith(".jsonl"):
            line_counts[candidate.name] = _line_count(candidate)
    if "response_rows" in receipt and "response_ledger.jsonl" in line_counts:
        _require(
            line_counts["response_ledger.jsonl"] == int(receipt["response_rows"]),
            f"Response ledger count changed: {path.parent}",
        )
    return {
        "kind": receipt.get("status"),
        "declared_files": len(files),
        "declared_bytes": declared_bytes,
        "hashes_verified": hashes_verified,
        "npy_header_shapes": dict(sorted(header_shapes.items())),
        "jsonl_line_counts": line_counts,
    }


def _stage_directories(role_directory: Path) -> list[str]:
    if not role_directory.is_dir():
        return []
    return sorted(
        str(path.relative_to(role_directory))
        for path in role_directory.rglob("*")
        if path.is_dir() and path.name.startswith(".") and ".stage-" in path.name
    )


def _aggregate_counters(rows: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    total: Counter[str] = Counter()
    for row in rows:
        value = row[key]
        _require(isinstance(value, dict), f"Expected mapping for {key}")
        total.update({str(name): int(count) for name, count in value.items()})
    return dict(sorted(total.items()))


def inventory(run_root: Path, *, verify_hashes: bool = False) -> dict[str, Any]:
    audit_freeze()
    config = _config()
    gate = config["acquisition_gate"]
    integrity = config["integrity_gate"]
    roles = [str(value) for value in gate["required_role_order"]]
    pilots = {str(value) for value in gate["pilot_roles"]}
    root = run_root.expanduser().resolve(strict=True)
    role_rows: list[dict[str, Any]] = []
    for role in roles:
        role_directory = root / role
        receipts = _sealed_receipts(role_directory)
        kinds = Counter(_receipt_kind(path, role_directory) for path in receipts)
        receipt_audits = [
            _audit_receipt(path, role=role, verify_hashes=verify_hashes)
            for path in receipts
        ]
        summary_path = role_directory / "summary.json"
        summary = _read_json(summary_path) if summary_path.is_file() else None
        stages = _stage_directories(role_directory)
        expected_receipts = int(
            integrity[
                "expected_receipts_per_pilot_role"
                if role in pilots
                else "expected_receipts_per_nonpilot_role"
            ]
        )
        expected_kinds = {
            "baseline": 1,
            "source": int(integrity["expected_source_shards_per_role"]),
        }
        if role in pilots:
            expected_kinds.update(
                {
                    "pilot_zero": 1,
                    "pilot_item": 12,
                    "pilot_prototype": 6,
                    "pilot_random": 8,
                }
            )
        if summary is not None:
            _require(
                summary.get("protocol_id") == SOURCE_PROTOCOL_ID,
                f"Summary protocol changed: {role}",
            )
            _require(summary.get("model_role") == role, f"Summary role changed: {role}")
            _require(
                summary.get("status") == "role_complete", f"Summary incomplete: {role}"
            )
            _require(
                int(summary.get("generation_calls", -1)) == 0,
                f"Summary generation changed: {role}",
            )
            _require(
                int(summary.get("source_shards", -1))
                == int(integrity["expected_source_shards_per_role"]),
                f"Summary source shard count changed: {role}",
            )
            _require(
                int(summary.get("source_forward_sequences", -1))
                == int(integrity["expected_source_forward_sequences_per_role"]),
                f"Summary source sequence count changed: {role}",
            )
            expected_response_rows = (
                int(integrity["expected_response_rows_per_pilot_role"])
                if role in pilots
                else 0
            )
            _require(
                int(summary.get("intervention_response_rows", -1))
                == expected_response_rows,
                f"Summary response row count changed: {role}",
            )
        complete = bool(
            summary is not None
            and len(receipts) == expected_receipts
            and dict(kinds) == expected_kinds
            and not stages
        )
        status = (
            "complete"
            if complete
            else "in_progress"
            if role_directory.exists()
            else "absent"
        )
        if summary is not None and not complete:
            status = "invalid_complete_boundary"
        role_rows.append(
            {
                "role": role,
                "pilot_role": role in pilots,
                "status": status,
                "summary_present": summary is not None,
                "summary_sha256": _sha256(summary_path)
                if summary is not None
                else None,
                "sealed_receipts": len(receipts),
                "expected_receipts": expected_receipts,
                "receipt_kinds": dict(sorted(kinds.items())),
                "expected_receipt_kinds": dict(sorted(expected_kinds.items())),
                "incomplete_stage_directories": stages,
                "declared_files": sum(
                    int(row["declared_files"]) for row in receipt_audits
                ),
                "declared_bytes": sum(
                    int(row["declared_bytes"]) for row in receipt_audits
                ),
                "hashes_verified": sum(
                    int(row["hashes_verified"]) for row in receipt_audits
                ),
                "npy_header_shapes": _aggregate_counters(
                    receipt_audits, "npy_header_shapes"
                ),
                "scientific_values_parsed": False,
            }
        )
    completed = sum(row["status"] == "complete" for row in role_rows)
    invalid = any(row["status"] == "invalid_complete_boundary" for row in role_rows)
    all_complete = completed == len(roles) and not invalid
    scientific_open = bool(all_complete and verify_hashes)
    return {
        "analysis_id": ANALYSIS_ID,
        "source_protocol_id": SOURCE_PROTOCOL_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "queue_complete" if all_complete else "queue_in_progress",
        "run_root": str(root),
        "roles_complete": completed,
        "roles_required": len(roles),
        "independent_hash_verification": verify_hashes,
        "inspection_scope": (
            "sealed_paths_counts_sizes_npy_headers_and_content_blind_sha256"
            if verify_hashes
            else "sealed_paths_counts_sizes_and_npy_headers"
        ),
        "scientific_open_authorized": scientific_open,
        "scientific_open_blockers": (
            []
            if scientific_open
            else [
                *([] if all_complete else ["full_nine_role_queue_not_complete"]),
                *(
                    []
                    if verify_hashes
                    else ["independent_hash_verification_not_requested"]
                ),
            ]
        ),
        "scientific_values_parsed": False,
        "role_inventory": role_rows,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("audit-design")
    frozen = sub.add_parser("freeze")
    frozen.add_argument("--output", type=Path, default=FREEZE_PATH)
    sub.add_parser("audit-freeze")
    inspect = sub.add_parser("inventory")
    inspect.add_argument("--run-root", type=Path, required=True)
    inspect.add_argument("--output", type=Path)
    inspect.add_argument("--verify-hashes", action="store_true")
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "audit-design":
        result = audit_design()
    elif args.command == "freeze":
        result = freeze(args.output)
    elif args.command == "audit-freeze":
        result = audit_freeze()
    else:
        result = inventory(args.run_root, verify_hashes=args.verify_hashes)
        if args.output is not None:
            _write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
