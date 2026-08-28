from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_mistral7b_semantic_atlas_batch1_v1_public_bundle.py"
SPEC = importlib.util.spec_from_file_location("semantic_atlas_public_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BUNDLE = ROOT / "artifacts" / "mistral7b_semantic_atlas_batch1_v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(relative: str) -> dict[str, object]:
    value = json.loads((BUNDLE / relative).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_public_manifest_covers_the_exact_compact_payload() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    expected = {
        path.relative_to(BUNDLE).as_posix()
        for path in BUNDLE.rglob("*")
        if path.is_file()
        and path.name not in {"PUBLIC_MANIFEST.json", "README.md", "README.ja.md"}
    }

    assert manifest["protocol_id"] == MODULE.PROTOCOL_ID
    assert manifest["status"] == "pass"
    assert manifest["artifact_role"] == (
        "compact_public_evidence_without_raw_activations_or_item_rows"
    )
    assert set(manifest["files"]) == expected == set(MODULE.EXPECTED)
    for relative, entry in manifest["files"].items():
        path = BUNDLE / relative
        assert path.stat().st_size == entry["bytes"]
        assert _sha256(path) == entry["sha256"] == MODULE.EXPECTED[relative]


def test_capture_failure_and_canonical_replacement_are_both_retained() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    run = _read("run/run_receipt.json")
    failed = _read("validation/batch64_capture_validation_failure.json")
    passed = _read("validation/batch1_capture_validation_pass.json")

    assert manifest["capture_validation"] == {
        "batch1_status": "pass_18_of_18_bit_exact",
        "batch64_status": "validation_failed_0_of_18",
    }
    assert failed["status"] == "validation_failed"
    assert failed["passed_case_count"] == 0
    assert failed["minimum_vector_cosine"] == pytest.approx(0.9982442704394325)
    assert failed["maximum_relative_rms_error"] == pytest.approx(0.07898381804097139)
    assert passed["status"] == "pass"
    assert passed["passed_case_count"] == 18
    assert passed["minimum_exact_element_fraction"] == 1.0
    assert passed["maximum_absolute_error"] == 0.0
    assert passed["maximum_relative_rms_error"] == 0.0
    assert run["batched_model_forward_calls"] == 5352
    assert run["shard_count"] == 28
    assert run["causal_readout_vectors"] == 192672
    assert run["reserved_unrun_model_inputs_forwarded"] == 0


def test_headline_values_are_bound_to_the_complete_layer_summaries() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    outcome = manifest["outcome_summary"]
    layers = _read("analysis/layer_summary.json")["rows"]
    token_layers = _read("analysis/token_structure_layer_summary.json")["rows"]

    discovery31 = next(
        row
        for row in layers
        if row["population"] == "discovery_unseen" and row["layer"] == 31
    )
    glyph5 = next(
        row
        for row in token_layers
        if row["stratum"] == "glyph5_common_prefix3_all" and row["layer"] == 31
    )
    matched5 = next(
        row
        for row in token_layers
        if row["stratum"] == "glyph5_name_tokens_5_equal_view_length"
        and row["layer"] == 31
    )

    assert outcome["discovery_top1_chance"] == pytest.approx(1.0 / 842.0)
    assert outcome[
        "discovery_layer31_glyph_name_top1_equal_cell_mean"
    ] == pytest.approx(discovery31["glyph_name_paired_retrieval_top1"])
    assert outcome[
        "discovery_layer31_glyph_codepoint_top1_equal_cell_mean"
    ] == pytest.approx(discovery31["glyph_codepoint_paired_retrieval_top1"])
    assert outcome["glyph5_common_prefix_layer31_glyph_name_top1"] == pytest.approx(
        glyph5["glyph_name_top1"]
    )
    assert outcome["glyph5_name5_layer31_glyph_name_top1"] == pytest.approx(
        matched5["glyph_name_top1"]
    )
    assert matched5["item_count"] == 43


def test_analysis_and_public_surface_preserve_claim_and_data_boundaries() -> None:
    manifest = _read("PUBLIC_MANIFEST.json")
    analysis = _read("analysis/analysis_receipt.json")
    token = _read("analysis/token_structure_receipt.json")

    assert analysis["status"] == token["status"] == "pass"
    assert analysis["cell_row_count"] == 144
    assert token["cell_row_count"] == 576
    assert analysis["scientific_decision_authorized"] is False
    assert token["outcome_known_before_exact_sensitivity_design"] is True
    assert analysis["reserved_unrun_model_inputs_forwarded"] == 0
    assert token["reserved_unrun_model_inputs_forwarded"] == 0
    assert manifest["analysis"]["confirmatory_status"] is False
    assert manifest["analysis"]["phase_i_gate_closed"] is False
    assert manifest["canonical_capture"]["raw_activation_bytes_committed"] == 0

    forbidden_suffixes = {".npy", ".npz", ".safetensors"}
    forbidden_names = {"item_metrics.jsonl", "item_pair_cosines.jsonl"}
    for path in BUNDLE.rglob("*"):
        if path.is_file():
            assert path.suffix not in forbidden_suffixes
            assert path.name not in forbidden_names

    assert (ROOT / "docs" / "MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md").is_file()
    assert (
        ROOT / "docs" / "MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md"
    ).is_file()


def test_public_bundle_contains_no_machine_local_paths_or_identity_strings() -> None:
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
