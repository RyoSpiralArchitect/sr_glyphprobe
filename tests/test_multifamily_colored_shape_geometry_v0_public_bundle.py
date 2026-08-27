from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_colored_shape_geometry_v0.py"
SPEC = importlib.util.spec_from_file_location("multifamily_colored_shape_geometry_v0_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "multifamily_colored_shape_geometry_v0"
MANIFEST = BUNDLE / "PUBLIC_MANIFEST.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_public_payload_manifest_is_exact() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload = manifest["payload"]
    expected = {
        path.relative_to(BUNDLE).as_posix()
        for path in BUNDLE.rglob("*")
        if path.is_file() and path.name not in {"PUBLIC_MANIFEST.json", "README.md", "README.ja.md"}
    }

    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert manifest["freeze_commit"] == "dc78756bd8f26ae0060463e459d5deb40c47d750"
    assert manifest["outcome_pattern"] == "no_dual_model_recurrence"
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


def test_all_three_published_generated_bundles_validate() -> None:
    gemma = MODULE.validate_run(BUNDLE / "runs" / "gemma2_2b_4bit")
    olmo = MODULE.validate_run(BUNDLE / "runs" / "olmo3_7b_bf16")
    analysis = MODULE.validate_analysis(BUNDLE / "analysis")

    assert gemma["status"] == "pass"
    assert olmo["status"] == "pass"
    assert analysis["status"] == "pass"
    assert gemma["activations"].shape == (10, 5, 2304)
    assert olmo["activations"].shape == (10, 5, 4096)


def test_primary_result_and_secondary_boundaries_are_retained() -> None:
    receipt = json.loads((BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (BUNDLE / "analysis" / "layer_statistics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]

    assert receipt["outcome_pattern"] == "no_dual_model_recurrence"
    assert receipt["phase_i_gate_closed"] is False
    assert receipt["confirmatory_status"] is False
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert receipt["protected_target_files_opened"] == 0
    assert receipt["primary_results"]["gemma2_2b_4bit"]["statistic"] == pytest.approx(
        0.114857968827293
    )
    assert receipt["primary_results"]["gemma2_2b_4bit"]["holm_adjusted_p"] == pytest.approx(
        0.11666666666666667
    )
    assert receipt["primary_results"]["olmo3_7b_bf16"]["statistic"] == pytest.approx(
        0.024628040026043373
    )
    assert receipt["primary_results"]["olmo3_7b_bf16"]["holm_adjusted_p"] == pytest.approx(
        0.275
    )
    assert all(result["holm_reject"] is False for result in receipt["primary_results"].values())
    assert len(rows) == 10
    assert sum(bool(row["is_primary"]) for row in rows) == 2
    assert all(
        bool(row["multiplicity_decision_authorized"]) is bool(row["is_primary"])
        for row in rows
    )


def test_public_bundle_records_three_point_olmo_transfer_and_has_no_local_paths() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    transfer = manifest["source_and_transfer_verification"]["olmo_transfer"]
    receipt_path = BUNDLE / transfer["receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert transfer["files_checked"] == 4
    assert transfer["source_equals_relay"] is True
    assert transfer["source_equals_destination"] is True
    assert _sha256(receipt_path) == transfer["receipt_sha256"]
    assert receipt["route"] == ["mac1_source", "furnace_relay", "mac2_destination"]
    assert receipt["files_checked"] == 4
    assert receipt["source_validator"] == "pass"
    assert receipt["destination_validator"] == "pass"
    assert all(
        entry["all_equal"]
        and len({entry["source_sha256"], entry["relay_sha256"], entry["destination_sha256"]}) == 1
        for entry in receipt["files"].values()
    )

    forbidden = ("/Users/", "/tmp/", "ryohiga", "ryospiralarchitect", "Ryos-MacBook")
    for path in BUNDLE.rglob("*"):
        if path.is_file() and path.suffix != ".npz":
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
