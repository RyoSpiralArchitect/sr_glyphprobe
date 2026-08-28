from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mistral7b_base_depth_distance_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "mistral7b_base_depth_distance_v0_bundle", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "mistral7b_base_depth_distance_v0"
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

    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert manifest["freeze_commit"] == "25de47a5fb4c9eaf7674d5b2fa49f0c2cf84ca8b"
    assert manifest["outcome_pattern"] == (
        "recurrence_and_early_depth_attenuation_excess"
    )
    assert manifest["scientific_confirmation"] is False
    assert manifest["instruction_tuning_effect_authorized"] is False
    assert payload["file_count"] == 9
    assert set(payload["files"]) == expected
    assert payload["total_bytes"] == sum(
        int(entry["bytes"]) for entry in payload["files"].values()
    )

    for relative, entry in payload["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"]


def test_published_run_and_analysis_validate() -> None:
    run = MODULE.validate_run(BUNDLE / "runs" / "mistral7b_base_v03")
    assert run["status"] == "pass"
    assert run["activations"].shape == (50, 2, 4, 5, 4096)

    analysis = MODULE.validate_analysis(BUNDLE / "analysis")
    assert analysis["status"] == "pass"
    assert analysis["outcome_pattern"] == (
        "recurrence_and_early_depth_attenuation_excess"
    )
    assert analysis["carrier_distance_layer_row_count"] == 40


def test_primary_result_and_claim_boundaries_are_retained() -> None:
    receipt = json.loads(
        (BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8")
    )
    primary = receipt["primary_result"]

    assert receipt["outcome_pattern"] == (
        "recurrence_and_early_depth_attenuation_excess"
    )
    assert receipt["scientific_confirmation"] is False
    assert receipt["instruction_tuning_effect_authorized"] is False
    assert receipt["phase_i_gate_closed"] is False
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert receipt["protected_target_files_opened"] == 0
    assert primary["distance1_recurrence_component"]["statistic"] == pytest.approx(
        0.37752402613924974
    )
    assert primary["distance1_recurrence_component"]["raw_p"] == pytest.approx(0.00005)
    assert primary["early_minus_late_attenuation_component"][
        "statistic"
    ] == pytest.approx(0.14910406790191197)
    assert primary["early_minus_late_attenuation_component"]["raw_p"] == pytest.approx(
        0.00005
    )
    assert primary["intersection_union_raw_p"] == pytest.approx(0.00005)
    assert primary["reject_at_alpha"] is True
    assert primary["all_depth_attenuation_secondary"]["raw_p"] == pytest.approx(
        0.87475
    )


def test_descriptive_instruct_comparison_does_not_claim_equivalence() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    comparison = manifest["descriptive_t6_instruct_comparison"]
    assert comparison["inferential_pooling"] is False
    assert comparison["equivalence_decision_authorized"] is False
    assert comparison["depth_distance_cell_count"] == 20
    assert comparison["pearson_correlation"] == pytest.approx(0.9967857296884247)
    assert comparison["mean_absolute_difference"] == pytest.approx(
        0.01195340385574908
    )


def test_transfer_and_public_text_preserve_operational_boundaries() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verification = manifest["source_gate_and_transfer_verification"]
    transfer_path = BUNDLE / verification["transfer"]["receipt"]
    transfer = json.loads(transfer_path.read_text(encoding="utf-8"))

    assert _sha256(transfer_path) == verification["transfer"]["receipt_sha256"]
    assert transfer["freeze"]["model_forward_calls_before_freeze_commit"] == 0
    assert transfer["execution_start_gate"][
        "furnace_status_rechecked_immediately_before_compute"
    ] is True
    assert transfer["execution_start_gate"]["competing_compute_process_observed"] is False
    assert transfer["execution_start_gate"][
        "fresh_attention_notification_used_as_execution_authority"
    ] is False
    assert transfer["execution_start_gate"]["notification_content_retrieved_for_t7_start"] is False
    assert transfer["execution_start_gate"]["notification_reply_observed_for_t7_start"] is False
    assert transfer["execution_start_gate"]["notification_commitment_observed_for_t7_start"] is False
    assert transfer["execution_start_gate"]["six_task_local_deliveries_claimed"] is False
    assert transfer["execution"]["model_forward_calls"] == 400
    assert transfer["execution"]["intervention_calls"] == 0
    assert transfer["execution"]["generation_calls"] == 0
    assert transfer["execution"]["protected_target_files_opened"] == 0
    assert transfer["result_return_transfer"][
        "all_source_ledgers_verified_at_destination"
    ] is True
    assert transfer["post_execution_resource_state"]["furnace_released"] is True

    forbidden = (
        "/Users/",
        "/home/",
        "/tmp/",
        "ryohiga",
        "ryospiralarchitect",
        "Ryos-MacBook",
    )
    for path in BUNDLE.rglob("*"):
        if path.is_file() and path.suffix != ".npz":
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
