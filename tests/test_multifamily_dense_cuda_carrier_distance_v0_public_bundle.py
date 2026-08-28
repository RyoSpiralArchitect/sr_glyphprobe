from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_dense_cuda_carrier_distance_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "multifamily_dense_cuda_carrier_distance_v0_bundle", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "multifamily_dense_cuda_carrier_distance_v0"
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
    assert manifest["freeze_commit"] == "5e2f4984486b5e5dc87b93f656d6e00bc8718baa"
    assert manifest["outcome_pattern"] == "no_dense_model_distance_attenuation"
    assert manifest["scientific_confirmation"] is False
    assert payload["file_count"] == 21
    assert set(payload["files"]) == expected
    assert payload["total_bytes"] == sum(
        int(entry["bytes"]) for entry in payload["files"].values()
    )

    for relative, entry in payload["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"]


def test_all_five_published_generated_bundles_validate() -> None:
    expected_shapes = {
        "gemma2_2b_it": (50, 2, 4, 5, 2304),
        "gemma3_4b_it": (50, 2, 4, 5, 2560),
        "mistral7b_instruct_v03": (50, 2, 4, 5, 4096),
        "gemma3_12b_it": (50, 2, 4, 5, 3840),
    }
    for model_label, expected_shape in expected_shapes.items():
        result = MODULE.validate_run(BUNDLE / "runs" / model_label)
        assert result["status"] == "pass"
        assert result["activations"].shape == expected_shape

    analysis = MODULE.validate_analysis(BUNDLE / "analysis")
    assert analysis["status"] == "pass"
    assert analysis["outcome_pattern"] == "no_dense_model_distance_attenuation"
    assert analysis["carrier_distance_layer_row_count"] == 160


def test_primary_result_and_secondary_boundaries_are_retained() -> None:
    receipt = json.loads(
        (BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8")
    )
    primary = receipt["primary_results"]

    assert receipt["outcome_pattern"] == "no_dense_model_distance_attenuation"
    assert receipt["phase_i_gate_closed"] is False
    assert receipt["confirmatory_status"] is False
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert receipt["protected_target_files_opened"] == 0
    assert primary["mistral7b_instruct_v03"]["distance1_component"][
        "raw_p"
    ] == pytest.approx(0.00005)
    assert primary["mistral7b_instruct_v03"]["attenuation_component"][
        "raw_p"
    ] == pytest.approx(0.46975)
    assert primary["gemma3_12b_it"]["distance8_tail_secondary"][
        "raw_p"
    ] == pytest.approx(0.04045)
    assert all(result["holm_adjusted_p"] == 1.0 for result in primary.values())
    assert all(result["holm_reject"] is False for result in primary.values())


def test_public_bundle_records_lifecycle_and_return_boundaries_without_local_paths() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    verification = manifest["source_gate_and_transfer_verification"]
    transfer_path = BUNDLE / verification["transfer"]["receipt"]
    transfer = json.loads(transfer_path.read_text(encoding="utf-8"))

    assert _sha256(transfer_path) == verification["transfer"]["receipt_sha256"]
    assert transfer["execution_start_gate"][
        "furnace_status_rechecked_immediately_before_compute"
    ] is True
    assert transfer["execution_start_gate"]["competing_compute_process_observed"] is False
    lifecycle = transfer["execution_start_gate"][
        "natural_receiver_owned_lifecycle_surface"
    ]
    assert lifecycle["canonical_thread"] == "resource:furnace"
    assert lifecycle["hook_event"] == "Stop"
    assert lifecycle["message_content_retrieved"] is False
    assert lifecycle["reply_observed"] is False
    assert lifecycle["commitment_observed"] is False
    assert lifecycle["six_task_local_deliveries_claimed"] is False
    assert transfer["result_return_transfer"]["payload_files_checked"] == 15
    assert transfer["result_return_transfer"][
        "all_source_ledgers_verified_at_destination"
    ] is True

    forbidden = ("/Users/", "/tmp/", "ryohiga", "ryospiralarchitect", "Ryos-MacBook")
    for path in BUNDLE.rglob("*"):
        if path.is_file() and path.suffix != ".npz":
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
