from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_multifamily_matched_slot_geometry_v0_repair_v1.py"
SPEC = importlib.util.spec_from_file_location("matched_slot_public_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REPAIR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPAIR)
FROZEN = REPAIR.frozen

BUNDLE = ROOT / "artifacts" / "multifamily_matched_slot_geometry_v0"
MANIFEST = BUNDLE / "PUBLIC_MANIFEST.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_public_payload_manifest_is_exact() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload = manifest["payload"]
    expected = {
        path.relative_to(BUNDLE).as_posix()
        for path in BUNDLE.rglob("*")
        if path.is_file()
        and path.name not in {"PUBLIC_MANIFEST.json", "README.md", "README.ja.md"}
    }

    assert manifest["protocol_id"] == FROZEN.PROTOCOL_ID
    assert manifest["freeze_commit"] == "ae928b840e6164c89e9c4c71d5e41ceb8de3dfaa"
    assert manifest["outcome_pattern"] == "olmo_only_token_structured_recurrence"
    assert manifest["scientific_confirmation"] is False
    assert payload["file_count"] == 13
    assert set(payload["files"]) == expected
    assert payload["total_bytes"] == sum(
        int(entry["bytes"]) for entry in payload["files"].values()
    )

    for relative, entry in payload["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"]


def test_published_runs_and_repaired_analysis_validate() -> None:
    gemma = FROZEN.validate_run(BUNDLE / "runs" / "gemma2_2b_4bit")
    olmo = FROZEN.validate_run(BUNDLE / "runs" / "olmo3_7b_bf16")
    analysis = REPAIR.validate_repaired_analysis(BUNDLE / "analysis")

    assert gemma["status"] == "pass"
    assert olmo["status"] == "pass"
    assert analysis["status"] == "pass"
    assert analysis["repair_id"] == REPAIR.REPAIR_ID
    assert analysis["scientific_choices_changed"] is False
    assert gemma["activations"].shape == (50, 5, 2304)
    assert olmo["activations"].shape == (50, 5, 4096)


def test_primary_split_and_secondary_boundaries_are_retained() -> None:
    receipt = json.loads(
        (BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8")
    )
    rows = [
        json.loads(line)
        for line in (BUNDLE / "analysis" / "layer_statistics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    assert receipt["outcome_pattern"] == "olmo_only_token_structured_recurrence"
    assert receipt["phase_i_gate_closed"] is False
    assert receipt["confirmatory_status"] is False
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert receipt["protected_target_files_opened"] == 0

    gemma = receipt["primary_results"]["gemma2_2b_4bit"]
    assert gemma["statistic"] == pytest.approx(0.20430480497215972)
    assert gemma["null_mean"] == pytest.approx(0.19998446280655024)
    assert gemma["holm_adjusted_p"] == pytest.approx(0.2085)
    assert gemma["holm_reject"] is False

    olmo = receipt["primary_results"]["olmo3_7b_bf16"]
    assert olmo["statistic"] == pytest.approx(0.5003918689177909)
    assert olmo["null_mean"] == pytest.approx(0.20018483520628658)
    assert olmo["holm_adjusted_p"] == pytest.approx(0.0001)
    assert olmo["holm_reject"] is True
    assert olmo["depth_profile"] == pytest.approx(
        [
            0.9947218881765565,
            0.4613245544477011,
            0.4134240981408787,
            0.33666082351610443,
            0.2958279803077132,
        ]
    )

    assert len(rows) == 10
    assert not any(bool(row["multiplicity_decision_authorized"]) for row in rows)


def test_public_analysis_binds_the_frozen_serialization_only_repair() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repair = manifest["analysis_repair"]
    receipt = json.loads(
        (BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8")
    )["analysis_serialization_repair"]

    assert repair["repair_id"] == REPAIR.REPAIR_ID == receipt["repair_id"]
    assert repair["change_scope"] == "json_mapping_key_normalization_only"
    assert repair["repair_manifest_sha256"] == receipt["repair_manifest_sha256"]
    assert repair["scientific_choices_changed"] is False
    assert receipt["scientific_choices_changed"] is False


def test_public_bundle_records_three_point_olmo_transfer_and_has_no_local_paths() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    transfer = manifest["source_and_transfer_verification"]["olmo_transfer"]
    receipt_path = BUNDLE / transfer["receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert transfer["files_checked"] == 4
    assert transfer["source_equals_relay"] is True
    assert transfer["source_equals_destination"] is True
    assert transfer["compute_used_on_relay"] is False
    assert _sha256(receipt_path) == transfer["receipt_sha256"]
    assert receipt["source_node"] == "mac1"
    assert receipt["relay_node"] == "furnace"
    assert receipt["destination_node"] == "mac2"
    assert receipt["compute_used_on_relay"] is False
    assert len(receipt["files"]) == 4

    olmo_payload = manifest["payload"]["files"]
    for name, entry in receipt["files"].items():
        assert entry["source_match"] is True
        assert entry["relay_match"] is True
        assert entry["destination_match"] is True
        assert entry["sha256"] == olmo_payload[f"runs/olmo3_7b_bf16/{name}"]["sha256"]

    forbidden = ("/Users/", "/private/tmp/", "/tmp/", "ryohiga", "ryospiralarchitect")
    for path in BUNDLE.rglob("*"):
        if path.is_file() and path.suffix != ".npz":
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
