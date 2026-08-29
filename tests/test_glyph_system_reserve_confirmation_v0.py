from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "glyph_system_reserve_confirmation_v0.py"
SPEC = importlib.util.spec_from_file_location("glyph_system_reserve_confirmation_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_design_uses_only_complete_unforwarded_zwj_and_regional_reserves() -> None:
    items = MODULE.confirmation_items()
    assert len(items) == 160
    assert [item["t12_index"] for item in items] == list(range(160))
    assert sum(item["glyph_system"] == "zwj" for item in items) == 96
    assert sum(item["glyph_system"] == "regional_flag" for item in items) == 64
    assert all(item["role"] == "reserve_unrun" for item in items)
    assert all(item["acquisition_index"] is None for item in items)
    assert all(item["included_in_acquisition"] is False for item in items)
    assert all(item["included_in_depth_subset"] is False for item in items)
    assert all(item["t12_views"] == ["glyph", "unicode_name", "decomposed_form"] for item in items[:96])
    assert all(
        item["t12_views"]
        == ["glyph", "unicode_name", "component_name", "decomposed_form"]
        for item in items[96:]
    )


def test_design_audit_binds_cost_and_zero_forward_boundary() -> None:
    audit = MODULE.audit_design()
    assert audit["status"] == "pass"
    assert audit["reserve_items"] == 160
    assert audit["present_item_views"] == 544
    assert audit["model_cells"] == 9
    assert audit["model_forward_calls_per_model"] == 1088
    assert audit["expected_total_model_forward_calls"] == 9792
    assert audit["readout_vectors_per_model"] == 4352
    assert audit["expected_total_readout_vectors"] == 39168
    assert audit["reserve_model_forward_calls"] == 0
    assert audit["model_weights_loaded"] is False
    assert audit["scientific_result_available"] is False
    assert audit["intervention_calls"] == 0
    assert audit["generation_calls"] == 0


def test_discovery_basis_and_practical_floors_are_bound() -> None:
    audit = MODULE.audit_design()["discovery_design_basis"]
    assert audit["zwj_presentation_or_fusion"]["positive_cells"] == 65
    assert audit["zwj_presentation_or_fusion"]["models_at_or_above_t12_floor"] == 8
    assert audit["regional_presentation_or_fusion"]["positive_cells"] == 59
    assert audit["regional_presentation_or_fusion"]["models_at_or_above_t12_floor"] == 6
    assert audit["regional_component_tracking"]["positive_cells"] == 58
    assert audit["regional_component_tracking"]["models_at_or_above_t12_floor"] == 6
    assert audit["regional_component_tracking"]["models_at_or_below_negative_t12_floor"] == 1


def test_protocol_has_one_endpoint_and_a_two_hypothesis_family() -> None:
    config = MODULE._config()
    assert config["endpoint"]["name"] == "returned_final_hidden_state"
    assert config["endpoint"]["raw_last_block_stored"] is False
    assert config["endpoint"]["intermediate_depths_stored"] is False
    family = config["hypothesis_family"]
    assert family["registered_hypothesis_order"] == [
        "H_ZWJ_FUSION",
        "H_REGIONAL_DUAL",
    ]
    assert family["registered_hypotheses"]["H_REGIONAL_DUAL"][
        "required_elementary_tests"
    ] == [
        "regional_presentation_or_fusion",
        "regional_component_tracking",
    ]
    assert family["regional_combination"] == "intersection_union_max_component_p_value"
    assert family["correction"] == "holm_over_two_registered_hypotheses"
    assert family["heterogeneity_gate"]["minimum_models_at_or_above_practical_floor"] == 6
    assert family["heterogeneity_gate"]["maximum_models_at_or_below_negative_practical_floor"] == 1


def test_runtime_pin_matches_t11_and_pre_execution_correction_is_zero_forward() -> None:
    config = MODULE._config()
    t11_config = MODULE.t11._config()
    assert config["runtime"]["critical_versions"] == t11_config["runtime"][
        "critical_versions"
    ]
    correction = config["pre_execution_correction"]
    assert correction["superseded_freeze_commit"] == (
        "7b49d801b49d52052f0b3d73021a628d77a9986b"
    )
    assert correction["t12_reserve_model_forward_calls_before_correction"] == 0


def test_control_mapping_is_deterministic_stratified_and_has_no_self_match() -> None:
    rows = [
        {"t12_index": index, "glyph_system": "zwj", "codepoint": f"X{index}"}
        for index in range(6)
    ]
    token_ids = {
        0: [10, 1],
        1: [10, 2],
        2: [11, 3],
        3: [11, 4],
        4: [12],
        5: [13],
    }
    first = MODULE._control_mapping(
        rows,
        token_ids,
        role="synthetic",
        target_view="unicode_name",
        strict_prefix=False,
    )
    second = MODULE._control_mapping(
        rows,
        token_ids,
        role="synthetic",
        target_view="unicode_name",
        strict_prefix=False,
    )
    strict = MODULE._control_mapping(
        rows,
        token_ids,
        role="synthetic",
        target_view="unicode_name",
        strict_prefix=True,
    )
    assert first == second
    assert first["coverage"] == 1.0
    assert strict["coverage"] == 4 / 6
    assert all(
        row["t12_index"] != row["wrong_target_t12_index"]
        for row in first["mapping"]
    )
    for row in first["mapping"]:
        assert len(token_ids[row["t12_index"]]) == len(
            token_ids[row["wrong_target_t12_index"]]
        )
    for row in strict["mapping"]:
        left = token_ids[row["t12_index"]]
        right = token_ids[row["wrong_target_t12_index"]]
        assert (len(left), left[0]) == (len(right), right[0])


def test_shared_item_swap_randomization_and_nonmultiplicity_gates() -> None:
    magnitudes = np.linspace(0.005, 0.055, 31, dtype=np.float64)
    values = np.broadcast_to(magnitudes, (9, 8, 31)).copy()
    primary = MODULE.shared_item_swap_randomization_test(
        values, draws=1999, seed=17
    )
    strict = MODULE._descriptive_summary(values * 0.5)
    gate = MODULE._elementary_gate(primary, strict, practical_floor=0.02)
    assert primary["global_statistic"] >= 0.02
    assert primary["p_value"] <= 0.01
    assert gate["all_nonmultiplicity_gates_pass"] is True
    assert gate["supporting_model_count"] == 9
    assert gate["materially_opposed_model_count"] == 0
    assert gate["strict_prefix_positive_model_count"] == 9


def test_gate_fails_when_pooling_hides_model_heterogeneity() -> None:
    model_medians = [0.03, 0.03, 0.03, 0.03, 0.03, 0.0, 0.0, -0.03, -0.03]
    primary = {
        "global_statistic": 0.025,
        "model_context_medians": model_medians,
    }
    strict = {
        "global_statistic": 0.01,
        "model_context_medians": [0.01] * 9,
    }
    gate = MODULE._elementary_gate(primary, strict, practical_floor=0.02)
    assert gate["all_nonmultiplicity_gates_pass"] is False
    assert gate["supporting_model_count"] == 5
    assert gate["materially_opposed_model_count"] == 2


def test_regional_intersection_union_uses_the_weaker_component() -> None:
    component_p_values = {
        "regional_presentation_or_fusion": 0.001,
        "regional_component_tracking": 0.20,
    }
    regional_p = max(component_p_values.values())
    holm = MODULE.holm_correction(
        {"H_ZWJ_FUSION": 0.001, "H_REGIONAL_DUAL": regional_p},
        alpha=0.05,
        hypothesis_order=["H_ZWJ_FUSION", "H_REGIONAL_DUAL"],
    )
    assert regional_p == 0.20
    assert holm["rejected"]["H_ZWJ_FUSION"] is True
    assert holm["rejected"]["H_REGIONAL_DUAL"] is False


def test_holm_adjustment_is_monotone_and_order_stable() -> None:
    result = MODULE.holm_correction(
        {"H_ZWJ_FUSION": 0.02, "H_REGIONAL_DUAL": 0.03},
        alpha=0.05,
        hypothesis_order=["H_ZWJ_FUSION", "H_REGIONAL_DUAL"],
    )
    assert result["adjusted_p_values"] == {
        "H_ZWJ_FUSION": 0.04,
        "H_REGIONAL_DUAL": 0.04,
    }
    assert result["rejected"] == {
        "H_ZWJ_FUSION": True,
        "H_REGIONAL_DUAL": True,
    }


def test_bilingual_protocol_and_claim_boundaries_are_present() -> None:
    english = (ROOT / "docs" / "GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md").read_text(
        encoding="utf-8"
    )
    japanese = (
        ROOT / "docs" / "GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "H_ZWJ_FUSION" in text
        assert "H_REGIONAL_DUAL" in text
        assert "9,792" in text
        assert "Holm" in text
        assert "tokenizer independence" in text or "tokenizer independence" in text.lower()
    assert "[日本語]" in english
    assert "[English]" in japanese


def test_design_preflight_writer_records_zero_reserve_forwards(tmp_path: Path) -> None:
    output = tmp_path / "design.json"
    result = MODULE.build_design_preflight(output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "pass"
    assert payload["status"] == "design_preflight_complete_zero_t12_reserve_model_forwards"
    assert payload["reserve_model_forward_calls"] == 0
    assert payload["model_weights_loaded"] is False
    assert payload["scientific_result_available"] is False
