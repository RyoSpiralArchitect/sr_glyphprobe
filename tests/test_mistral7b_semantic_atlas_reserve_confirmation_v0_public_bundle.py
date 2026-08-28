from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "scripts"
    / "build_mistral7b_semantic_atlas_reserve_confirmation_v0_public_bundle.py"
)
SPEC = importlib.util.spec_from_file_location(
    "reserve_confirmation_public_bundle", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "mistral7b_semantic_atlas_reserve_confirmation_v0"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(relative: str) -> dict[str, object]:
    value = json.loads((BUNDLE / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_manifest_covers_exact_compact_payload() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    expected = {
        path.relative_to(BUNDLE).as_posix()
        for path in BUNDLE.rglob("*")
        if path.is_file()
        and path.name not in {"PUBLIC_MANIFEST.json", "README.md", "README.ja.md"}
    }

    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert manifest["outcome_pattern"] == MODULE.OUTCOME
    assert manifest["status"] == "pass"
    assert set(manifest["files"]) == expected == set(MODULE.EXPECTED)
    for relative, entry in manifest["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"] == MODULE.EXPECTED[relative]


def test_freeze_precedes_complete_single_use_acquisition() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    run = _read("run/run_receipt.json")
    session = _read("run/session_receipt.json")
    execution = _read("validation/execution_receipt.json")

    assert manifest["freeze"]["commit"] == ("952b89d1c1d8a0aa023f40b617432653581a5a85")
    assert manifest["freeze"]["reserve_model_inputs_forwarded_at_freeze"] == 0
    assert run["reserve_items"] == run["reserved_items_forwarded"] == 292
    assert run["model_forward_calls"] == run["reserved_model_inputs_forwarded"] == 1752
    assert run["causal_readout_vectors"] == 7008
    assert run["shard_count"] == 10
    assert len(session["events"]) == 10
    assert sum(event["item_count"] for event in session["events"]) == 292
    assert execution["execution"]["partial_shards"] == 0
    assert (
        execution["execution_start_gate"]["competing_compute_process_observed"] is False
    )
    assert execution["execution_start_gate"]["model_downloaded_for_this_run"] is False
    assert (
        execution["result_return"]["all_source_ledgers_verified_at_destination"] is True
    )


def test_frozen_primary_passes_without_secondary_rescue() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    primary = _read("analysis/primary_result.json")
    analysis = _read("analysis/analysis_receipt.json")
    cells = [
        json.loads(line)
        for line in (BUNDLE / "analysis/cell_metrics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert len(cells) == 8
    contrasts = [
        row["pairs"]["glyph_name"]["top1_accuracy_forward"]
        - row["pairs"]["glyph_codepoint"]["top1_accuracy_forward"]
        for row in cells
    ]
    assert min(contrasts) == pytest.approx(0.17123288288712502)
    assert primary["observed_minimum_cell_contrast"] == pytest.approx(
        0.17123287671232876
    )
    assert primary["observed_equal_cell_mean_contrast"] == pytest.approx(
        0.2320205479452055
    )
    assert primary["practical_minimum"] == 0.02
    assert primary["randomization_draws"] == 19999
    assert primary["randomization_seed"] == 20260828
    assert primary["exceedances"] == 0
    assert primary["p_value"] == 0.00005
    assert primary["alignment_confirmed"] is True
    assert analysis["confirmatory_status"] is True
    assert analysis["t8_reserve_question_closed"] is True
    assert manifest["primary"]["alignment_confirmed"] is True


def test_claim_and_raw_data_boundaries_remain_closed() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    claims = manifest["claim_boundary"]

    assert claims["confirmatory_alignment_claim_authorized"] is True
    assert claims["semantic_claim_authorized"] is False
    assert claims["causal_claim_authorized"] is False
    assert claims["tokenizer_independent_claim_authorized"] is False
    assert claims["model_general_claim_authorized"] is False
    assert claims["phase_i_gate_closed"] is False
    assert manifest["raw_data_policy"]["raw_activations_in_git"] is False
    assert manifest["raw_data_policy"]["item_retrieval_outcomes_in_git"] is False
    assert not list(BUNDLE.rglob("*.npy"))
    assert not list(BUNDLE.rglob("item_retrieval_outcomes.jsonl"))

    assert (
        ROOT / "docs" / "MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md"
    ).is_file()
    assert (
        ROOT / "docs" / "MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md"
    ).is_file()


def test_public_bundle_has_no_machine_local_paths_or_identity_strings() -> None:
    forbidden = (
        "/Users/",
        "/home/",
        "/tmp/",
        "ryohiga",
        "ryospiralarchitect",
        "Ryos-MacBook",
    )
    for path in BUNDLE.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
