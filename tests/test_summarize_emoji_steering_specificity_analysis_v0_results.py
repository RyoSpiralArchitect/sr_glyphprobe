from __future__ import annotations

import copy
import hashlib
import importlib.util
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT / "scripts" / "summarize_emoji_steering_specificity_analysis_v0_results.py"
)
SPEC = importlib.util.spec_from_file_location(
    "summarize_emoji_steering_specificity_analysis_v0_results", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _statistics(mean: float, n: int = 2) -> dict:
    return {
        "maximum": mean,
        "mean": mean,
        "median": mean,
        "minimum": mean,
        "n": n,
    }


def test_f1_retains_every_model_sign_row_and_counts_directions() -> None:
    rows = []
    for model, sign, mean in (
        ("m1", -1, 0.2),
        ("m1", 1, -0.1),
        ("m2", -1, 0.0),
        ("m2", 1, 0.4),
    ):
        rows.append(
            {
                "contrast": "glyph_minus_decomposed_form",
                "eligible_item_count": 2,
                "eligible_target_count": 2,
                "endpoint": "js_divergence",
                "model": model,
                "n_rows": 4,
                "sign": sign,
                "statistics": {"paired_difference": _statistics(mean)},
            }
        )
    result = MODULE._summarize_f1(
        {
            "contrast_denominators": [{"contrast": "synthetic"}],
            "overall_summaries": rows,
            "rows_retained": 16,
            "system_summaries": [{**row, "glyph_system": "system"} for row in rows],
            "token_matching_scope": {"maximum_supported_label": "count_signature_only"},
        }
    )
    assert len(result["overall_model_sign_rows"]) == 4
    aggregate = result["aggregate_model_sign_counts_and_ranges"][0]
    assert aggregate["positive_mean_rows"] == 2
    assert aggregate["negative_mean_rows"] == 1
    assert aggregate["zero_mean_rows"] == 1
    assert aggregate["mean_range"] == {"maximum": 0.4, "minimum": -0.1}
    system = result["system_contrast_aggregates"][0]
    assert system["model_sign_cells"] == 4
    assert system["paired_rows"] == 16
    assert system["model_sign_equal_weight_mean"] == pytest.approx(0.125)


def test_f2_uses_target_counts_for_dose_and_antisymmetry_weighting() -> None:
    dose_rows = [
        {
            "endpoint": "total_variation",
            "model": "m",
            "n_rows": 1,
            "statistics": {"ordered_non_decreasing": _statistics(0.0, 1)},
        },
        {
            "endpoint": "total_variation",
            "model": "m",
            "n_rows": 3,
            "statistics": {"ordered_non_decreasing": _statistics(1.0, 3)},
        },
    ]
    anti_rows = [
        {
            "model": "m",
            "n_rows": 1,
            "statistics": {
                "normalized_antisymmetry_residual": _statistics(1.0, 1),
                "positive_plus_negative": _statistics(0.5, 1),
            },
        },
        {
            "model": "m",
            "n_rows": 3,
            "statistics": {
                "normalized_antisymmetry_residual": _statistics(0.0, 3),
                "positive_plus_negative": _statistics(-0.5, 3),
            },
        },
    ]
    result = MODULE._summarize_f2(
        {
            "dose_order_summaries": dose_rows,
            "headline_macro_summaries": [
                {
                    "depth_fraction": 0.5,
                    "endpoint": "total_variation",
                    "mean": 0.2,
                    "model": "m",
                },
                {
                    "depth_fraction": 1.0,
                    "endpoint": "total_variation",
                    "mean": 0.4,
                    "model": "m",
                },
            ],
            "rows_retained": 8,
            "sign_antisymmetry_summaries": anti_rows,
        }
    )
    dose = result["dose_ordering_by_model_endpoint"][0]
    assert dose["weighted_mean"] == 0.75
    assert dose["observations"] == 4
    antisymmetry = result["entropy_antisymmetry_by_model"][0]
    assert antisymmetry["normalized_antisymmetry_residual"]["weighted_mean"] == 0.25
    assert antisymmetry["positive_plus_negative"]["weighted_mean"] == -0.25
    assert result["raw_headline_peak_by_model_endpoint"][0]["peak_depth_fractions"] == [
        1.0
    ]


def test_f3_outputs_model_source_form_and_depth_breakdowns_without_filtering() -> None:
    rows = []
    for model in ("m1", "m2"):
        for source_form, depth, percentile in (
            ("glyph", 0.5, 0.8),
            ("unicode_name", 1.0, 0.2),
        ):
            rows.append(
                {
                    "depth_fraction": depth,
                    "endpoint": "js_divergence",
                    "model": model,
                    "prototype_minus_random_median_mean": percentile - 0.5,
                    "prototype_random_percentile_mean": percentile,
                    "source_form": source_form,
                }
            )
    result = MODULE._summarize_f3(
        {
            "calibrated_positive_prototype_rows": 4,
            "headline_macro_summaries": rows,
            "negative_random_orientation_acquired": False,
            "random_null_definition": "positive",
            "random_rows_retained": 4,
            "uncalibrated_negative_prototype_rows": 4,
        }
    )
    assert len(result["by_model_endpoint"]) == 2
    assert len(result["by_model_endpoint_depth"]) == 4
    assert len(result["by_source_form_endpoint"]) == 2
    model = result["by_model_endpoint"][0]
    assert model["cells"] == 2
    assert model["percentile_above_half_cells"] == 1
    assert model["percentile_below_half_cells"] == 1


def test_f5_sign_reversal_is_weighted_by_sign_pair_count() -> None:
    def row(count: int, cosine: float) -> dict:
        return {
            "condition_kind": "glyph_system_source_form_prototype",
            "depth_fraction": 0.5,
            "glyph_system": "system",
            "magnitude": 0.25,
            "model": "m",
            "sign_pairs": count,
            "source_form": "glyph",
            "statistics": {
                "mean_swapped_top64_overlap": _statistics(cosine, count),
                "sign_reversed_countsketch_cosine": _statistics(cosine, count),
                "top_tail_sign_purity": _statistics(1.0, count),
            },
        }

    result = MODULE._summarize_f5(
        {
            "cross_model_rank_concordance": [],
            "random_direction_sign_pair": {"status": "unavailable"},
            "within_model_sign_pair_summaries": [row(1, -0.5), row(3, 1.0)],
        }
    )
    summary = result["weighted_sign_reversal_by_model_source_form_depth"][0]
    assert summary["sign_reversed_countsketch_cosine"]["weighted_mean"] == 0.625
    assert summary["sign_reversed_countsketch_cosine"]["observations"] == 4
    prototype = result["prototype_sign_reversal"]
    assert prototype["all_prototypes"][0]["weighted_mean"] == 0.625
    assert prototype["cell_sign_accounting"]["negative_mean_cells"] == 1
    assert prototype["cell_sign_accounting"]["minimum_cell"]["mean"] == -0.5


def test_f6_weighted_pair_wrapper_and_signature_summaries() -> None:
    pair_rows = [
        {
            "cosine": _statistics(0.0, 1),
            "depth_index": 0,
            "glyph_system": "system",
            "model": "m",
            "pair": "glyph_vs_name",
        },
        {
            "cosine": _statistics(1.0, 3),
            "depth_index": 1,
            "glyph_system": "system",
            "model": "m",
            "pair": "glyph_vs_name",
        },
    ]
    wrapper_rows = [
        {
            "depth_index": 0,
            "glyph_system": "system",
            "model": "m",
            "relative_residual_rms": _statistics(0.25, 2),
            "source_form": "glyph",
            "wrapper_direction_cosine": _statistics(0.75, 2),
        }
    ]
    match_rows = [
        {
            "depth_index": 0,
            "glyph_system": "system",
            "items": 2,
            "model": "m",
            "pair": "glyph_vs_name",
            "pair_cosine": _statistics(0.6, 2),
            "token_count_signature_exact_match": True,
        },
        {
            "depth_index": 0,
            "glyph_system": "system",
            "items": 1,
            "model": "m",
            "pair": "glyph_vs_name",
            "pair_cosine": _statistics(0.3, 1),
            "token_count_signature_exact_match": False,
        },
    ]
    result = MODULE._summarize_f6(
        {
            "depth_trajectories": [
                {
                    "final_minus_first": _statistics(1.0),
                    "glyph_system": "system",
                    "model": "m",
                    "pair": "glyph_vs_name",
                }
            ],
            "direction_mean_integrity_vectors_checked": 4,
            "glyph_name_decomposition_cosines": pair_rows,
            "tokenizer_signature_match_summaries": match_rows,
            "tokenizer_signature_strata": [{"validated": True}],
            "wrapper_dispersion": wrapper_rows,
        }
    )
    assert result["pair_cosines_by_model_system"][0]["weighted_mean"] == 0.75
    assert len(result["count_signature_matched_unmatched"]) == 2
    assert (
        result["weighted_wrapper_dispersion"][0]["wrapper_direction_cosine"][
            "weighted_mean"
        ]
        == 0.75
    )
    stratum = result["within_stratum_matched_minus_unmatched"]
    assert stratum["overall"][0]["comparisons"] == 1
    assert stratum["overall"][0]["mean"] == pytest.approx(0.3)
    assert stratum["overall"][0]["positive"] == 1


def test_hash_binding_validation_rejects_a_geometry_digest_mismatch() -> None:
    geometry_bindings = {
        name: {"bytes": 1, "filename": name, "sha256": "a" * 64}
        for name in MODULE.GEOMETRY_FILENAMES
    }
    receipt = {
        "amendment": {
            "config_sha256": "c" * 64,
            "freeze_audit": {
                "freeze_manifest_sha256": "f" * 64,
                "status": "amendment_freeze_audit_pass",
            },
        },
        "input_closeout": {
            "external_closeout_root_sha256": "r" * 64,
            "preflight_receipt_sha256": {
                model: "p" * 64 for model in MODULE.ALL_MODELS
            },
            "same_process_audit": {"run_binding_root_sha256": "r" * 64},
            "scientific_open_receipt_sha256": "s" * 64,
        },
        "outputs": {
            name: {"bytes": 1, "sha256": ("b" * 64 if index == 0 else "a" * 64)}
            for index, name in enumerate(MODULE.GEOMETRY_FILENAMES[:-1])
        },
    }
    outcomes = {
        "scientific_open_receipt": {"sha256": "s" * 64},
        "value_open_authorization": {
            "closeout_sha256": "s" * 64,
            "preflight_receipt_sha256": {
                model: "p" * 64 for model in MODULE.ALL_MODELS
            },
            "same_process_amendment_freeze_audit": {
                "status": "amendment_freeze_audit_pass"
            },
            "same_process_closeout_audit": {"run_binding_root_sha256": "r" * 64},
            "zero_hook_gate": {"run_binding_root_sha256": "r" * 64},
        },
    }
    zero = {
        "amendment_config_sha256": "c" * 64,
        "amendment_freeze_manifest_sha256": "f" * 64,
        "run_binding_root_sha256": "r" * 64,
        "scientific_open_receipt_sha256": "s" * 64,
    }
    with pytest.raises(MODULE.ReportingSummaryError, match="SHA-256"):
        MODULE._validate_hashes_and_bindings(
            outcomes,
            {"receipt": receipt, "zero": zero},
            geometry_bindings,
        )


def _point_closeout_fixture() -> tuple[dict, dict, dict, dict]:
    geometry_bindings = {
        name: {"bytes": index + 1, "filename": name, "sha256": f"{index + 1:064x}"}
        for index, name in enumerate(MODULE.GEOMETRY_FILENAMES)
    }
    outcomes_binding = {
        "bytes": 6,
        "filename": "outcomes-v1-point.json",
        "sha256": f"{6:064x}",
    }
    actual = {binding["filename"]: binding for binding in geometry_bindings.values()}
    actual[outcomes_binding["filename"]] = outcomes_binding
    closeout = {
        "analysis_id": MODULE.SOURCE_ANALYSIS_ID,
        "analyzer_commit": MODULE.ANALYZER_COMMIT,
        "analyzer_zero_gate_amendment_id": MODULE.AMENDMENT_ID,
        "analyzer_zero_gate_amendment_manifest_sha256": "f" * 64,
        "bootstrap": {
            "executed_replicates": 0,
            "paper_interval_gate_satisfied": False,
            "registered_replicates": 20_000,
            "status": "point_estimates_only_bootstrap_pending",
        },
        "cross_host_verification": {
            "files_compared": 6,
            "files_equal_by_sha256": 6,
            "local_view": "mac2 temporary analysis intake",
            "remote_authority": "furnace derived-output directory",
            "status": "all_derived_outputs_equal_by_sha256",
        },
        "execution": {
            name: {
                "elapsed_seconds": 1.0,
                "gpu_used": False,
                "maximum_resident_set_kib": 1,
                "priority": "nice_15_idle_io",
                "status": "complete",
            }
            for name in ("geometry", "outcomes_point")
        },
        "input_closeout": {
            "run_binding_root_sha256": "r" * 64,
            "sha256": "s" * 64,
        },
        "json_validation": {
            "files_parsed": 6,
            "nonfinite_numeric_values": 0,
            "status": "all_derived_json_parsed_without_nonfinite_values",
        },
        "outputs": {
            name: {"bytes": actual[name]["bytes"], "sha256": actual[name]["sha256"]}
            for name in MODULE.POINT_RESULT_FILENAMES
        },
        "raw_arrays_copied_from_furnace": False,
        "schema_version": 1,
        "scientific_values_parsed_after_zero_gate": True,
        "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": MODULE.POINT_RESULTS_CLOSEOUT_STATUS,
        "total_derived_output_bytes": sum(
            actual[name]["bytes"] for name in MODULE.POINT_RESULT_FILENAMES
        ),
        "zero_gate": {
            "historical_v0_exact_js_gate_status": "failed_closed_and_preserved",
            "nonzero_scientific_values_opened_before_v1_gate": False,
            "primitive_noop_equalities": "exact",
            "v1_js_absolute_tolerance": MODULE.FLOAT32_JS_TOLERANCE,
            "v1_status": "all_three_pilot_zero_controls_passed",
        },
    }
    bindings = {
        "geometry_files": geometry_bindings,
        "outcomes_point_json": outcomes_binding,
        "point_results_closeout_json": {
            "bytes": 10,
            "filename": "closeout.json",
            "sha256": "c" * 64,
        },
    }
    roots = {"closeout_sha256": "s" * 64, "run_binding_root_sha256": "r" * 64}
    zero = {"amendment_freeze_manifest_sha256": "f" * 64}
    return closeout, bindings, roots, zero


def test_point_results_closeout_accepts_exact_six_file_and_source_bindings() -> None:
    closeout, bindings, roots, zero = _point_closeout_fixture()
    result = MODULE._validate_point_results_closeout(closeout, bindings, roots, zero)
    assert result["total_derived_output_bytes"] == 21


def test_point_results_closeout_rejects_an_outcomes_digest_mismatch() -> None:
    closeout, bindings, roots, zero = _point_closeout_fixture()
    closeout = copy.deepcopy(closeout)
    closeout["outputs"]["outcomes-v1-point.json"]["sha256"] = "0" * 64
    with pytest.raises(MODULE.ReportingSummaryError, match="SHA-256"):
        MODULE._validate_point_results_closeout(closeout, bindings, roots, zero)


def test_point_results_closeout_rejects_run_binding_and_total_byte_mismatches() -> None:
    closeout, bindings, roots, zero = _point_closeout_fixture()
    wrong_root = copy.deepcopy(closeout)
    wrong_root["input_closeout"]["run_binding_root_sha256"] = "x" * 64
    with pytest.raises(MODULE.ReportingSummaryError, match="run-binding"):
        MODULE._validate_point_results_closeout(wrong_root, bindings, roots, zero)

    wrong_total = copy.deepcopy(closeout)
    wrong_total["total_derived_output_bytes"] += 1
    with pytest.raises(MODULE.ReportingSummaryError, match="total byte"):
        MODULE._validate_point_results_closeout(wrong_total, bindings, roots, zero)


def test_nonfinite_numbers_are_rejected() -> None:
    with pytest.raises(MODULE.ReportingSummaryError, match="Non-finite"):
        MODULE._validate_finite({"value": math.nan})


def test_exclusive_output_is_deterministic_and_never_overwritten(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    document = {"b": 2, "a": [1, 3]}
    MODULE.write_json_exclusive(first, document)
    MODULE.write_json_exclusive(second, document)
    first_bytes = first.read_bytes()
    assert first_bytes == second.read_bytes()
    assert (
        hashlib.sha256(first_bytes).hexdigest()
        == hashlib.sha256(second.read_bytes()).hexdigest()
    )
    with pytest.raises(MODULE.ReportingSummaryError, match="already exists"):
        MODULE.write_json_exclusive(first, {"different": True})
    assert first.read_bytes() == first_bytes


def test_production_expected_counts_remain_frozen() -> None:
    assert MODULE.EXPECTED_RETAINED_ROWS == {
        "F1.rows_retained": 105_984,
        "F2.rows_retained": 129_024,
        "F3.prototype_rows_retained": 129_024,
        "F3.random_rows_retained": 147_456,
        "F3.calibrated_positive_prototype_rows": 64_512,
        "F3.uncalibrated_negative_prototype_rows": 64_512,
        "F5.within_model_sign_pairs_each": 39_168,
        "F6.direction_mean_integrity_vectors_checked": 65_664,
    }
    assert MODULE.EXPECTED_COUNTS["F1.overall_summaries"] == 108
    assert MODULE.EXPECTED_COUNTS["F2.complete_surface_summaries"] == 24_192
    assert MODULE.EXPECTED_COUNTS["F3.random_quantiles"] == 13_824
    assert MODULE.EXPECTED_COUNTS["F4.target_profiles"] == 1_728
    assert MODULE.EXPECTED_COUNTS["F5.within_model_sign_pair_summaries"] == 2_067
    assert MODULE.EXPECTED_COUNTS["F6.tokenizer_signature_strata"] == 14_880
