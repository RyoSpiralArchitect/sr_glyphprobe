from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_word_incongruence_interaction_v1.py"
SPEC = importlib.util.spec_from_file_location("t15_interaction_analysis_repair", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_a0_repair_accepts_exact_frozen_repeat_count(monkeypatch) -> None:
    rows = []
    for axis in MODULE.original.t15.axes():
        for congruence, value in (("congruent", 1.0), ("incongruent", 2.0)):
            for _ in range(16):
                rows.append(
                    {
                        "source_kind": "core_pair",
                        "model_role": "synthetic_model",
                        "site_index": 6,
                        "depth_fraction": 0.875,
                        "axis_id": axis["id"],
                        "congruence": congruence,
                        "joint_additivity_residual_rms": value,
                    }
                )
    monkeypatch.setattr(MODULE.original, "_source_rows", lambda *_: rows)
    result = MODULE._a0(Path("unused"))
    assert len(result["axis_estimands"]) == 8
    assert len(result["summary"]) == 1
    assert result["summary"][0]["median"] == pytest.approx(1.0)


def test_repair_preserves_every_frozen_analysis_choice() -> None:
    assert MODULE.original.FAMILIES == (
        "A0_joint_additivity_residual_incongruent_minus_congruent",
        "A1_shared_response_fingerprint_true_minus_cross_axis_null",
        "A2_response_energy_true_minus_cross_axis_null",
        "A3_source_direction_rms_true_minus_cross_axis_null",
        "A4_word_minus_emoji_main_response",
        "A5_source_order_sensitivity",
        "A6_depth_and_dose_heterogeneity",
    )
    config = MODULE.original.t15._config()["analysis"]
    assert config["bootstrap_replicates"] == 20_000
    assert config["bootstrap_seed"] == 2026090201
    assert config["significance_tests"] == "none_exploratory_descriptive_only"
    source = SCRIPT.read_text(encoding="utf-8")
    assert "== 16" in source
    assert "original._a0 = _a0" in source
    assert "estimands_changed_by_repair" in source


def test_failure_receipt_records_no_output_or_researcher_values() -> None:
    failure = MODULE.original._read_json(ROOT / MODULE.FAILURE_RECEIPT_PATH)
    assert failure["status"] == "failed_closed_before_any_analysis_output"
    assert failure["analysis_output_created"] is False
    assert failure["model_values_printed"] == 0
    assert failure["response_values_shown_to_researcher"] is False
    assert "8 to 16" in failure["repair_boundary"]
