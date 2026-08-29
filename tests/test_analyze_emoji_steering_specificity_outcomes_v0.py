from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_steering_specificity_outcomes_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_emoji_steering_specificity_outcomes_v0", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


MODEL = "synthetic_model"
TARGETS = ((0, "target-0", "group-a"), (1, "target-1", "group-b"))
DEPTHS = (0.5,)
MAGNITUDES = (0.125, 0.25, 0.5)
SEEDS = (0, 1, 2, 3)
SOURCE_OFFSETS = {
    "glyph": 5.0,
    "unicode_name": 3.0,
    "component_name": 2.0,
    "codepoint_literal": 1.0,
    "decomposed_form": 0.5,
}


def _metrics(level: float, entropy_change: float, flip: bool) -> dict[str, object]:
    return {
        "kl_baseline_to_intervened": level,
        "js_divergence": level * 2.0,
        "total_variation": level * 3.0,
        "logit_delta_rms": level * 4.0,
        "baseline_entropy": 20.0,
        "intervened_entropy": 20.0 + entropy_change,
        "argmax_flip": flip,
    }


def _synthetic_rows() -> tuple[list[dict], list[dict], list[dict]]:
    item_rows = []
    for target_index, target_id, target_group in TARGETS:
        for sign in (-1, 1):
            for view in ("glyph", "unicode_name", "decomposed_form"):
                level = 10.0 + target_index + SOURCE_OFFSETS[view] + sign * 0.25
                item_rows.append(
                    {
                        "condition_kind": "item_source_form",
                        "model": MODEL,
                        "item_index": 0,
                        "glyph_system": "zwj",
                        "view": view,
                        "target_index": target_index,
                        "target_id": target_id,
                        "target_group": target_group,
                        "depth_fraction": 0.5,
                        "magnitude": 0.25,
                        "sign": sign,
                        **_metrics(
                            level,
                            sign * SOURCE_OFFSETS[view] / 10.0,
                            view == "glyph",
                        ),
                    }
                )

    prototype_rows = []
    for target_index, target_id, target_group in TARGETS:
        for depth in DEPTHS:
            for magnitude in MAGNITUDES:
                for sign in (-1, 1):
                    for view, source_offset in SOURCE_OFFSETS.items():
                        level = (
                            10.0
                            + target_index
                            + depth
                            + 3.0 * magnitude
                            + sign * 0.25
                            + source_offset
                        )
                        prototype_rows.append(
                            {
                                "condition_kind": (
                                    "glyph_system_source_form_prototype"
                                ),
                                "model": MODEL,
                                "glyph_system": "zwj",
                                "view": view,
                                "target_index": target_index,
                                "target_id": target_id,
                                "target_group": target_group,
                                "depth_fraction": depth,
                                "magnitude": magnitude,
                                "sign": sign,
                                **_metrics(
                                    level,
                                    sign * (magnitude + source_offset / 10.0),
                                    level >= 15.0,
                                ),
                            }
                        )

    random_rows = []
    for target_index, target_id, target_group in TARGETS:
        for depth in DEPTHS:
            for magnitude in MAGNITUDES:
                for seed_index in SEEDS:
                    level = (
                        10.0 + target_index + depth + 3.0 * magnitude + seed_index * 0.5
                    )
                    random_rows.append(
                        {
                            "condition_kind": "random_direction",
                            "model": MODEL,
                            "target_index": target_index,
                            "target_id": target_id,
                            "target_group": target_group,
                            "depth_fraction": depth,
                            "magnitude": magnitude,
                            "sign": 1,
                            "seed_index": seed_index,
                            **_metrics(
                                level,
                                magnitude + seed_index / 100.0,
                                seed_index == 3,
                            ),
                        }
                    )
    return item_rows, prototype_rows, random_rows


@pytest.fixture(scope="module")
def analysis() -> dict:
    return MODULE.analyze_rows(
        *_synthetic_rows(),
        bootstrap_replicates=31,
        bootstrap_seed=731,
    )


def _find(rows: list[dict], **wanted: object) -> dict:
    matches = [
        row
        for row in rows
        if all(row.get(field) == value for field, value in wanted.items())
    ]
    assert len(matches) == 1, (wanted, len(matches))
    return matches[0]


def test_analysis_reports_every_f1_f2_f3_family_and_endpoint(analysis: dict) -> None:
    assert analysis["status"] == "exploratory_f1_f2_f3_complete"
    assert analysis["decision_status"] == (
        "no_primary_no_significance_test_no_confirmatory_verdict"
    )
    assert analysis["family_order"] == list(MODULE.FAMILY_ORDER)
    assert analysis["endpoint_order"] == list(MODULE.ENDPOINT_ORDER)
    assert list(analysis["families"]) == list(MODULE.FAMILY_ORDER)
    assert all(
        family["status"] == "exploratory_complete_family"
        for family in analysis["families"].values()
    )
    assert analysis["reporting"] == {
        "multiplicity": "descriptive_complete_family_no_significance_rescue",
        "registered_interval": "percentile_cluster_bootstrap_95",
        "executed_interval": "percentile_cluster_bootstrap_95",
        "registered_bootstrap_replicates": 20_000,
        "executed_bootstrap_replicates": 31,
        "bootstrap_seed": 731,
        "bootstrap_status": (
            "synthetic_or_development_override_not_paper_interval_gate"
        ),
        "paper_interval_gate_satisfied": False,
        "paper_interval_gate_requirement": (
            "all_registered_bootstrap_chunks_complete_and_hash_merged"
        ),
        "all_registered_families_reported": True,
        "outcome_based_family_or_cell_filtering": False,
    }


def test_f1_uses_item_and_target_paired_source_form_contrasts(analysis: dict) -> None:
    family = analysis["families"]["F1_item_source_form"]
    assert family["rows_retained"] == 12
    assert len(family["paired_contrasts"]) == 72
    assert family["contrast_denominators"] == [
        {
            "contrast": "glyph_minus_unicode_name",
            "eligible_item_count": 1,
            "production_expected_eligible_item_count": 192,
            "excluded_item_count": 0,
            "missing_value_policy": "no_imputation",
        },
        {
            "contrast": "glyph_minus_decomposed_form",
            "eligible_item_count": 1,
            "production_expected_eligible_item_count": 168,
            "excluded_item_count": 0,
            "missing_value_policy": "no_imputation",
        },
        {
            "contrast": "unicode_name_minus_decomposed_form",
            "eligible_item_count": 1,
            "production_expected_eligible_item_count": 168,
            "excluded_item_count": 0,
            "missing_value_policy": "no_imputation",
        },
    ]
    assert family["token_matching_scope"]["maximum_supported_label"] == (
        "count_signature_only"
    )
    summary = _find(
        family["summaries"],
        model=MODEL,
        glyph_system="zwj",
        contrast="glyph_minus_unicode_name",
        sign=1,
        endpoint="kl_baseline_to_intervened",
    )
    assert summary["n_rows"] == 2
    assert summary["cluster_counts"] == {"item_index": 1, "target_index": 2}
    assert summary["statistics"]["paired_difference"] == {
        "mean": 2.0,
        "median": 2.0,
        "minimum": 2.0,
        "maximum": 2.0,
        "ci95_low": 2.0,
        "ci95_high": 2.0,
    }
    overall = _find(
        family["overall_summaries"],
        model=MODEL,
        contrast="glyph_minus_unicode_name",
        sign=1,
        endpoint="kl_baseline_to_intervened",
    )
    assert overall["eligible_item_count"] == 1
    assert overall["weighting"] == "eligible_item_by_target_micro_within_model"


def test_f2_reports_surface_dose_sign_and_source_form_summaries(
    analysis: dict,
) -> None:
    family = analysis["families"]["F2_prototype_depth_dose"]
    assert family["rows_retained"] == 60
    headline = _find(
        family["headline_macro_summaries"],
        model=MODEL,
        source_form="glyph",
        depth_fraction=0.5,
        magnitude=0.25,
        sign=1,
        endpoint="kl_baseline_to_intervened",
    )
    assert headline["eligible_systems"] == ["zwj"]
    assert headline["weighting"] == (
        "eligible_system_equal_weight_macro_of_target_micro_means"
    )

    positive_dose = _find(
        family["dose_order_summaries"],
        model=MODEL,
        glyph_system="zwj",
        source_form="glyph",
        depth_fraction=0.5,
        sign=1,
        endpoint="entropy_change",
    )
    negative_dose = _find(
        family["dose_order_summaries"],
        model=MODEL,
        glyph_system="zwj",
        source_form="glyph",
        depth_fraction=0.5,
        sign=-1,
        endpoint="entropy_change",
    )
    assert positive_dose["statistics"]["ordered_non_decreasing"]["mean"] == 1.0
    assert negative_dose["statistics"]["ordered_non_decreasing"]["mean"] == 1.0

    sign = _find(
        family["sign_pair_summaries"],
        model=MODEL,
        glyph_system="zwj",
        source_form="glyph",
        depth_fraction=0.5,
        magnitude=0.25,
        endpoint="kl_baseline_to_intervened",
    )
    assert sign["statistics"]["positive_minus_negative"]["mean"] == 0.5
    assert sign["interpretation"] == "nonnegative_endpoint_orientation_asymmetry_only"
    assert "positive_plus_negative" not in sign["statistics"]
    assert {row["endpoint"] for row in family["sign_antisymmetry_summaries"]} == {
        "entropy_change"
    }

    contrast = _find(
        family["source_form_contrast_summaries"],
        model=MODEL,
        glyph_system="zwj",
        contrast="glyph_minus_unicode_name",
        depth_fraction=0.5,
        magnitude=0.25,
        sign=-1,
        endpoint="kl_baseline_to_intervened",
    )
    assert contrast["statistics"]["paired_difference"]["mean"] == 2.0


def test_f3_matches_each_prototype_to_same_target_depth_and_dose_null(
    analysis: dict,
) -> None:
    family = analysis["families"]["F3_random_null_calibration"]
    assert family["prototype_rows_retained"] == 60
    assert family["calibrated_positive_prototype_rows"] == 30
    assert family["uncalibrated_negative_prototype_rows"] == 30
    assert family["random_rows_retained"] == 24
    assert family["negative_random_orientation_acquired"] is False
    assert all(row["sign"] == 1 for row in family["prototype_calibrations"])
    quantiles = _find(
        family["random_quantiles"],
        model=MODEL,
        target_index=0,
        depth_fraction=0.5,
        magnitude=0.125,
        endpoint="kl_baseline_to_intervened",
    )
    assert quantiles["random_seed_count"] == 4
    assert quantiles["quantiles"]["q50"] == 11.625

    calibration = _find(
        family["prototype_calibrations"],
        model=MODEL,
        glyph_system="zwj",
        source_form="decomposed_form",
        target_index=0,
        depth_fraction=0.5,
        magnitude=0.125,
        sign=1,
        endpoint="kl_baseline_to_intervened",
    )
    assert calibration["random_median"] == 11.625
    assert calibration["prototype_minus_random_median"] == 0.0
    assert calibration["prototype_random_percentile"] == 0.5
    headline = _find(
        family["headline_macro_summaries"],
        model=MODEL,
        source_form="decomposed_form",
        depth_fraction=0.5,
        magnitude=0.125,
        endpoint="kl_baseline_to_intervened",
    )
    assert headline["calibrated_sign"] == 1
    assert headline["eligible_systems"] == ["zwj"]


def test_incomplete_synthetic_family_fails_closed_before_summarization() -> None:
    item_rows, prototype_rows, random_rows = _synthetic_rows()
    item_rows.pop()
    with pytest.raises(MODULE.OutcomeAnalysisError, match="Incomplete item"):
        MODULE.analyze_rows(
            item_rows,
            prototype_rows,
            random_rows,
            bootstrap_replicates=7,
        )


def test_point_estimate_mode_does_not_claim_registered_intervals() -> None:
    result = MODULE.analyze_rows(*_synthetic_rows(), bootstrap_replicates=0)
    reporting = result["reporting"]
    assert reporting["executed_bootstrap_replicates"] == 0
    assert reporting["executed_interval"] is None
    assert reporting["bootstrap_status"] == "point_estimates_only_bootstrap_pending"
    assert reporting["paper_interval_gate_satisfied"] is False
    first = result["families"]["F1_item_source_form"]["summaries"][0]
    statistic = first["statistics"]["paired_difference"]
    assert "ci95_low" not in statistic
    assert "ci95_high" not in statistic


def test_production_compaction_keeps_fixed_summaries_and_counts_details() -> None:
    result = MODULE.analyze_rows(*_synthetic_rows(), bootstrap_replicates=0)
    compact = MODULE.compact_production_output(result)
    assert compact["production_output"] == {
        "mode": "compact_fixed_summaries",
        "detailed_derived_records_written": False,
        "raw_response_ledgers_remain_sealed_authority": True,
        "all_registered_family_summaries_retained": True,
    }
    f1 = compact["families"]["F1_item_source_form"]
    assert "paired_contrasts" not in f1
    assert f1["overall_summaries"]
    assert f1["system_summaries"]
    assert f1["omitted_derived_detail"][0]["record_count"] == 72
    f2 = compact["families"]["F2_prototype_depth_dose"]
    assert "source_form_contrasts" not in f2
    assert f2["complete_surface_summaries"]
    assert f2["headline_macro_summaries"]
    f3 = compact["families"]["F3_random_null_calibration"]
    assert "prototype_calibrations" not in f3
    assert f3["calibration_summaries"]
    assert f3["headline_macro_summaries"]


def test_command_defaults_to_point_estimates() -> None:
    args = MODULE.parser().parse_args(
        [
            "--run-root",
            "/tmp/run",
            "--scientific-open-receipt",
            "/tmp/receipt.json",
            "--output",
            "/tmp/result.json",
        ]
    )
    assert args.bootstrap_replicates == 0


def test_production_output_cannot_touch_or_overwrite_run_tree(tmp_path: Path) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    receipt = tmp_path / "closeout.json"
    with pytest.raises(MODULE.OutcomeAnalysisError, match="outside the sealed"):
        MODULE.analyze_run(run_root, receipt, run_root / "analysis.json")

    existing = tmp_path / "existing.json"
    existing.write_text("preserve", encoding="utf-8")
    with pytest.raises(MODULE.OutcomeAnalysisError, match="already exists"):
        MODULE.analyze_run(run_root, receipt, existing)
    assert existing.read_text(encoding="utf-8") == "preserve"


def test_command_path_requires_scientific_open_before_ledger_reads(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    receipt = tmp_path / "inventory.json"
    receipt.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "analysis_id": MODULE.ANALYSIS_ID,
                "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
                "status": "scientific_open_closeout_complete",
                "scientific_open_authorized": False,
                "independent_hash_verification": False,
                "scientific_values_parsed": False,
                "run_root": str(run_root.resolve()),
                "roles_complete": 9,
                "roles_required": 9,
                "run_binding_root_sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(MODULE.OutcomeAnalysisError, match="not authorized"):
        MODULE.load_authorized_rows(run_root, receipt)


def test_zero_gate_precedes_every_nonzero_ledger_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    receipt_path = tmp_path / "closeout.json"
    closeout = {
        "schema_version": 1,
        "analysis_id": MODULE.ANALYSIS_ID,
        "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": "scientific_open_closeout_complete",
        "scientific_open_authorized": True,
        "independent_hash_verification": True,
        "scientific_values_parsed": False,
        "run_root": str(run_root.resolve()),
        "roles_complete": 9,
        "roles_required": 9,
        "run_binding_root_sha256": "a" * 64,
    }
    receipt_path.write_text(json.dumps(closeout), encoding="utf-8")
    events = []

    def audit(*_args):
        events.append("closeout")
        return {
            "status": "scientific_open_closeout_audit_pass",
            "scientific_values_parsed": False,
            "run_binding_root_sha256": "a" * 64,
        }

    def zero(*_args):
        events.append("zero")
        return {"status": "all_pilot_zero_controls_exact_noop"}

    def ledger(_root, _role, kind, _count):
        events.append(kind)
        return []

    monkeypatch.setattr(MODULE, "_audit_closeout_same_process", audit)
    monkeypatch.setattr(MODULE, "_verify_zero_gate_same_process", zero)
    monkeypatch.setattr(MODULE, "_load_kind_ledgers", ledger)
    monkeypatch.setattr(
        MODULE,
        "_acquisition_config",
        lambda: {"pilot": {"roles": ["synthetic_role"]}},
    )
    MODULE.load_authorized_rows(run_root, receipt_path)
    assert events == ["closeout", "zero", "item", "prototype", "random"]


def test_bootstrap_is_deterministic_and_source_names_no_protected_banks() -> None:
    records = [
        {"item": 0, "target": 0, "value": 1.0},
        {"item": 0, "target": 1, "value": 2.0},
        {"item": 1, "target": 0, "value": 3.0},
        {"item": 1, "target": 1, "value": 4.0},
    ]
    kwargs = {
        "value_fields": ("value",),
        "cluster_fields": ("item", "target"),
        "replicates": 101,
        "seed": 91,
    }
    assert MODULE._bootstrap_mean_interval(records, **kwargs) == (
        MODULE._bootstrap_mean_interval(records, **kwargs)
    )
    source = SCRIPT.read_text(encoding="utf-8")
    assert "p2_confirmatory_targets" not in source
    assert "c1_causal_holdout_targets" not in source
