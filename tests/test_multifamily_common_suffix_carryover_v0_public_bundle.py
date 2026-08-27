from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_common_suffix_carryover_v0.py"
SPEC = importlib.util.spec_from_file_location("common_suffix_public_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "multifamily_common_suffix_carryover_v0"
MANIFEST = BUNDLE / "PUBLIC_MANIFEST.json"
FREEZE_COMMIT = "868f3be36e10bc6acd7e44caaf916b4e1ede84b9"


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
    assert manifest["freeze_commit"] == FREEZE_COMMIT
    assert manifest["outcome_pattern"] == "olmo_only_common_suffix_carryover"
    assert manifest["scientific_confirmation"] is False
    assert payload["file_count"] == 13
    assert set(payload["files"]) == expected
    assert payload["total_bytes"] == sum(
        int(entry["bytes"]) for entry in payload["files"].values()
    )
    for relative, entry in payload["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == int(entry["bytes"])
        assert _sha256(path) == entry["sha256"]


def test_published_runs_and_analysis_validate() -> None:
    gemma = MODULE.validate_run(BUNDLE / "runs" / "gemma2_2b_4bit")
    olmo = MODULE.validate_run(BUNDLE / "runs" / "olmo3_7b_bf16")
    analysis = MODULE.validate_analysis(BUNDLE / "analysis")
    assert gemma["status"] == "pass"
    assert olmo["status"] == "pass"
    assert analysis["status"] == "pass"
    assert gemma["activations"].shape == (50, 2, 5, 2304)
    assert olmo["activations"].shape == (50, 2, 5, 4096)
    assert analysis["context_layer_row_count"] == 20


def test_primary_split_contexts_and_t3_boundary_are_retained() -> None:
    receipt = json.loads(
        (BUNDLE / "analysis" / "analysis_receipt.json").read_text(encoding="utf-8")
    )
    rows = [
        json.loads(line)
        for line in (BUNDLE / "analysis" / "context_layer_statistics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    assert receipt["outcome_pattern"] == "olmo_only_common_suffix_carryover"
    assert receipt["phase_i_gate_closed"] is False
    assert receipt["confirmatory_status"] is False
    assert receipt["intervention_calls"] == 0
    assert receipt["generation_calls"] == 0
    assert receipt["protected_target_files_opened"] == 0

    gemma = receipt["primary_results"]["gemma2_2b_4bit"]
    assert gemma["statistic"] == pytest.approx(0.2034430108801077)
    assert gemma["null_mean"] == pytest.approx(0.20004469225443833)
    assert gemma["holm_adjusted_p"] == pytest.approx(0.30295)
    assert gemma["holm_reject"] is False

    olmo = receipt["primary_results"]["olmo3_7b_bf16"]
    assert olmo["statistic"] == pytest.approx(0.5374647032135664)
    assert olmo["null_mean"] == pytest.approx(0.19997786498147516)
    assert olmo["holm_adjusted_p"] == pytest.approx(0.0001)
    assert olmo["holm_reject"] is True
    assert olmo["context_summaries_secondary"]["period"]["statistic"] == pytest.approx(
        0.5389853818610971
    )
    assert olmo["context_summaries_secondary"]["newline"]["statistic"] == pytest.approx(
        0.5359440245660356
    )
    assert olmo["t3_raw_reference_descriptive"]["inferential_pooling"] is False
    assert len(rows) == 20
    assert {row["context_id"] for row in rows} == {"period", "newline"}
    assert not any(bool(row["multiplicity_decision_authorized"]) for row in rows)


def test_public_bundle_records_three_point_transfer_without_furnace_compute() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    transfer = manifest["source_and_transfer_verification"]["olmo_transfer"]
    receipt_path = BUNDLE / transfer["receipt"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert transfer["files_checked"] == 4
    assert transfer["source_equals_relay_archive"] is True
    assert transfer["source_equals_destination"] is True
    assert transfer["compute_used_on_relay"] is False
    assert _sha256(receipt_path) == transfer["receipt_sha256"]
    assert receipt["source_node"] == "mac1"
    assert receipt["relay_node"] == "furnace"
    assert receipt["destination_node"] == "mac2"
    assert receipt["compute_used_on_relay"] is False
    assert len(receipt["files"]) == 4
    for name, entry in receipt["files"].items():
        assert entry["source_match"] is True
        assert entry["relay_archive_member_match"] is True
        assert entry["destination_match"] is True
        assert entry["sha256"] == manifest["payload"]["files"][
            f"runs/olmo3_7b_bf16/{name}"
        ]["sha256"]


def test_public_bundle_has_no_local_paths_or_identity_strings() -> None:
    forbidden = ("/Users/", "/private/tmp/", "/tmp/", "ryohiga", "ryospiralarchitect")
    for path in BUNDLE.rglob("*"):
        if path.is_file() and path.suffix != ".npz":
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
