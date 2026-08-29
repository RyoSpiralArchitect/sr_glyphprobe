from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "audit_emoji_steering_specificity_analysis_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_emoji_steering_specificity_analysis_v0", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


SYSTEMS = (
    "atomic_anchor",
    "presentation",
    "modifier",
    "zwj",
    "regional_flag",
    "keycap",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _receipt(directory: Path, role: str, status: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = np.asarray([[1.0, 2.0]], dtype=np.float32)
    np.save(directory / "payload.npy", payload, allow_pickle=False)
    path = directory / "payload.npy"
    _write_json(
        directory / "receipt.json",
        {
            "protocol_id": MODULE.SOURCE_PROTOCOL_ID,
            "model_role": role,
            "status": status,
            "generation_calls": 0,
            "files": {
                "payload.npy": {
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
            },
        },
    )


def _complete_role(root: Path, role: str, pilot: bool) -> None:
    role_root = root / role
    _receipt(role_root / "baseline", role, "baseline_complete")
    for index in range(12):
        _receipt(
            role_root / "source" / f"shard-{index:04d}",
            role,
            "source_shard_complete",
        )
    if pilot:
        _receipt(
            role_root / "pilot" / "zero" / "all-sites",
            role,
            "response_shard_complete",
        )
        for index in range(12):
            _receipt(
                role_root / "pilot" / "item" / f"shard-{index:04d}",
                role,
                "response_shard_complete",
            )
        for system in SYSTEMS:
            _receipt(
                role_root / "pilot" / "prototype" / system,
                role,
                "response_shard_complete",
            )
        for index in range(8):
            _receipt(
                role_root / "pilot" / "random" / f"site-{index:02d}",
                role,
                "response_shard_complete",
            )
    _write_json(
        role_root / "summary.json",
        {
            "protocol_id": MODULE.SOURCE_PROTOCOL_ID,
            "status": "role_complete",
            "model_role": role,
            "pilot_role": pilot,
            "source_shards": 12,
            "source_forward_sequences": 3684,
            "intervention_response_rows": 127_744 if pilot else 0,
            "generation_calls": 0,
        },
    )


def _complete_run(root: Path) -> None:
    design = MODULE.audit_design()
    pilots = set(design["pilot_roles"])
    for role in design["required_roles"]:
        _complete_role(root, role, role in pilots)


def test_design_fixes_complete_exploratory_family_and_queue_blind() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "design_audit_pass"
    assert len(design["required_roles"]) == 9
    assert len(design["pilot_roles"]) == 3
    assert design["scientific_output_family_ids"] == [
        "F1_item_source_form",
        "F2_prototype_depth_dose",
        "F3_random_null_calibration",
        "F4_target_sensitivity",
        "F5_output_direction",
        "F6_source_geometry",
    ]
    assert design["scientific_outcomes_read"] is False


def test_inventory_stays_closed_without_full_queue(tmp_path: Path) -> None:
    role = MODULE.audit_design()["required_roles"][0]
    _receipt(tmp_path / role / "baseline", role, "baseline_complete")
    result = MODULE.inventory(tmp_path)
    assert result["status"] == "queue_in_progress"
    assert result["roles_complete"] == 0
    assert result["scientific_open_authorized"] is False
    assert result["scientific_values_parsed"] is False
    assert result["created_at_utc"].endswith("+00:00")
    assert result["inspection_scope"] == "sealed_paths_counts_sizes_and_npy_headers"
    assert "full_nine_role_queue_not_complete" in result["scientific_open_blockers"]


def test_complete_inventory_requires_independent_hash_pass(tmp_path: Path) -> None:
    _complete_run(tmp_path)
    content_blind = MODULE.inventory(tmp_path)
    assert content_blind["status"] == "queue_complete"
    assert content_blind["roles_complete"] == 9
    assert content_blind["scientific_open_authorized"] is False
    assert content_blind["role_inventory"][0]["sealed_receipts"] == 40
    assert content_blind["role_inventory"][3]["sealed_receipts"] == 13
    assert all(
        row["scientific_values_parsed"] is False
        for row in content_blind["role_inventory"]
    )

    verified = MODULE.inventory(tmp_path, verify_hashes=True)
    assert verified["scientific_open_authorized"] is True
    assert verified["scientific_open_blockers"] == []
    assert all(row["hashes_verified"] > 0 for row in verified["role_inventory"])


def test_hash_verification_fails_closed_on_same_size_mutation(tmp_path: Path) -> None:
    _complete_run(tmp_path)
    role = MODULE.audit_design()["required_roles"][0]
    payload = tmp_path / role / "baseline" / "payload.npy"
    value = bytearray(payload.read_bytes())
    value[-1] ^= 1
    payload.write_bytes(value)
    unverified = MODULE.inventory(tmp_path)
    assert unverified["scientific_open_authorized"] is False
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Hash changed"):
        MODULE.inventory(tmp_path, verify_hashes=True)


def test_freeze_manifest_is_current() -> None:
    assert MODULE.audit_freeze() == {
        "status": "freeze_audit_pass",
        "analysis_id": MODULE.ANALYSIS_ID,
    }
