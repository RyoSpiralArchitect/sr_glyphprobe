#!/usr/bin/env python3
"""Create a deterministic reporting-only summary of T13-EA F1--F6.

This program performs no model inference, resampling, hypothesis testing, or
outcome-based filtering.  It verifies the committed analysis identities,
production row counts, geometry receipt hashes, and cross-file bindings before
deriving complete, systematic point-summary tables.  The registered bootstrap
remains pending and this post-outcome synthesis is not a confirmatory result.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any
import uuid


SUMMARY_ID = "glyphprobe-emoji-steering-specificity-reporting-synthesis-v0"
AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
SOURCE_ANALYSIS_ID = "glyphprobe-emoji-steering-specificity-analysis-v0"
SOURCE_PROTOCOL_ID = "glyphprobe-emoji-steering-specificity-harvest-v0"
OUTCOMES_STATUS = "exploratory_f1_f2_f3_complete_under_zero_gate_amendment_v1"
GEOMETRY_STATUS = (
    "exploratory_f4_f5_f6_point_derivation_complete_under_zero_gate_amendment_v1"
)
FAMILY_STATUS = "exploratory_complete_family"
GEOMETRY_FAMILY_STATUS = "exploratory_point_derivation_complete"
ZERO_STATUS = (
    "all_pilot_zero_controls_primitive_exact_with_bounded_float32_js_roundtrip"
)
ZERO_MODEL_STATUS = "primitive_exact_noop_with_bounded_float32_js_roundtrip"
FLOAT32_JS_TOLERANCE = 9.5367431640625e-07
ANALYZER_COMMIT = "979533f64e9b25c48d56859a83ee4931ae47cde1"
POINT_RESULTS_CLOSEOUT_STATUS = "exploratory_point_results_cross_host_closeout_complete"

ENDPOINT_ORDER = (
    "kl_baseline_to_intervened",
    "js_divergence",
    "total_variation",
    "logit_delta_rms",
    "entropy_change",
    "argmax_flip_rate",
)
FAMILY_ORDER = (
    "F1_item_source_form",
    "F2_prototype_depth_dose",
    "F3_random_null_calibration",
)
PILOT_MODELS = (
    "qwen25_0p5b_base_bf16",
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
)
ALL_MODELS = (
    "qwen25_0p5b_base_bf16",
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "qwen25_3b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
GEOMETRY_FILENAMES = (
    "zero_hook_exact_primitives_bounded_js_v1.json",
    "F4_target_sensitivity.json",
    "F5_output_direction.json",
    "F6_source_geometry.json",
    "analysis_receipt.json",
)
POINT_RESULT_FILENAMES = (
    "F4_target_sensitivity.json",
    "F5_output_direction.json",
    "F6_source_geometry.json",
    "analysis_receipt.json",
    "outcomes-v1-point.json",
    "zero_hook_exact_primitives_bounded_js_v1.json",
)

EXPECTED_COUNTS = {
    "F1.contrast_availability": 18,
    "F1.contrast_denominators": 3,
    "F1.overall_summaries": 108,
    "F1.system_summaries": 576,
    "F2.complete_surface_summaries": 24_192,
    "F2.dose_order_summaries": 8_064,
    "F2.headline_macro_summaries": 4_320,
    "F2.sign_antisymmetry_summaries": 2_016,
    "F2.sign_orientation_summaries": 12_096,
    "F2.source_form_contrast_summaries": 45_792,
    "F3.calibration_summaries": 12_096,
    "F3.headline_macro_summaries": 2_160,
    "F3.random_quantiles": 13_824,
    "zero.models": 3,
    "F4.associations": 54,
    "F4.baseline_features": 96,
    "F4.target_group_heterogeneity": 54,
    "F4.target_profiles": 1_728,
    "F5.cross_model_rank_concordance": 54,
    "F5.item_sign_pair_summaries": 51,
    "F5.prototype_sign_pair_summaries": 2_016,
    "F5.within_model_sign_pair_summaries": 2_067,
    "F6.glyph_name_decomposition_cosines": 1_152,
    "F6.depth_trajectories": 144,
    "F6.source_form_availability": 63,
    "F6.structural_missingness": 432,
    "F6.tokenizer_signature_match_summaries": 1_744,
    "F6.tokenizer_signature_strata": 14_880,
    "F6.wrapper_dispersion": 2_016,
}
EXPECTED_RETAINED_ROWS = {
    "F1.rows_retained": 105_984,
    "F2.rows_retained": 129_024,
    "F3.prototype_rows_retained": 129_024,
    "F3.random_rows_retained": 147_456,
    "F3.calibrated_positive_prototype_rows": 64_512,
    "F3.uncalibrated_negative_prototype_rows": 64_512,
    "F5.within_model_sign_pairs_each": 39_168,
    "F6.direction_mean_integrity_vectors_checked": 65_664,
}
EXACT_ZERO_PRIMITIVES = {
    "argmax_identity_no_flip_and_in_range",
    "countsketch",
    "entropy_identity",
    "kl_baseline_to_intervened",
    "logit_delta_rms",
    "top_positive_and_negative_values",
    "total_variation",
}


class ReportingSummaryError(ValueError):
    """The supplied production analyses do not satisfy the reporting contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportingSummaryError(message)


def _reject_constant(value: str) -> None:
    raise ReportingSummaryError(f"Non-finite JSON constant is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _regular_file(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError as error:
        raise ReportingSummaryError(f"Input file is missing: {path}") from error
    _require(not stat.S_ISLNK(metadata.st_mode), f"Input is a symlink: {path}")
    _require(stat.S_ISREG(metadata.st_mode), f"Input is not a regular file: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _file_binding(path: Path) -> dict[str, Any]:
    _regular_file(path)
    return {
        "bytes": path.stat().st_size,
        "filename": path.name,
        "sha256": _sha256(path),
    }


def _read_json(path: Path) -> Any:
    _regular_file(path)
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(
                handle,
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportingSummaryError(f"Cannot read JSON: {path}") from error


def _validate_finite(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_finite(item, f"{path}[{index}]")
    elif isinstance(value, float):
        _require(math.isfinite(value), f"Non-finite number: {path}")
    elif value is None or isinstance(value, (str, int, bool)):
        return
    else:
        raise ReportingSummaryError(f"Unsupported JSON value: {path}")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"Expected mapping: {label}")
    return value


def _rows(value: Any, label: str, expected: int) -> list[Mapping[str, Any]]:
    _require(isinstance(value, list), f"Expected list: {label}")
    _require(len(value) == expected, f"Unexpected row count for {label}: {len(value)}")
    for index, row in enumerate(value):
        _require(isinstance(row, Mapping), f"Non-mapping row: {label}[{index}]")
    return value


def _number(value: Any, label: str) -> float:
    _require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"Expected number: {label}",
    )
    result = float(value)
    _require(math.isfinite(result), f"Non-finite number: {label}")
    return result


def _integer(value: Any, label: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), label)
    return int(value)


def _models_and_endpoints(
    rows: Sequence[Mapping[str, Any]], expected_models: Sequence[str], label: str
) -> None:
    _require(
        {str(row.get("model")) for row in rows} == set(expected_models),
        f"Model set differs: {label}",
    )
    _require(
        {str(row.get("endpoint")) for row in rows} == set(ENDPOINT_ORDER),
        f"Endpoint set differs: {label}",
    )


def _validate_outcomes(document: Any) -> Mapping[str, Any]:
    outcomes = _mapping(document, "outcomes")
    _validate_finite(outcomes)
    _require(
        outcomes.get("analysis_id") == AMENDMENT_ID, "Outcomes analysis ID differs"
    )
    _require(
        outcomes.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Outcomes protocol ID differs",
    )
    _require(outcomes.get("status") == OUTCOMES_STATUS, "Outcomes status differs")
    _require(
        outcomes.get("decision_status")
        == "exploratory_only_no_primary_no_significance_test_no_confirmatory_verdict",
        "Outcomes decision status differs",
    )
    _require(
        tuple(outcomes.get("endpoint_order", [])) == ENDPOINT_ORDER,
        "Endpoint order differs",
    )
    _require(
        tuple(outcomes.get("family_order", [])) == FAMILY_ORDER, "Family order differs"
    )

    reporting = _mapping(outcomes.get("reporting"), "outcomes.reporting")
    _require(
        reporting.get("bootstrap_status") == "point_estimates_only_bootstrap_pending",
        "Bootstrap status differs",
    )
    _require(
        reporting.get("executed_bootstrap_replicates") == 0, "Bootstrap was executed"
    )
    _require(reporting.get("executed_interval") is None, "Unexpected interval")
    _require(
        reporting.get("registered_bootstrap_replicates") == 20_000,
        "Registered bootstrap count differs",
    )
    _require(
        reporting.get("paper_interval_gate_satisfied") is False,
        "Paper interval gate unexpectedly passed",
    )
    _require(
        reporting.get("outcome_based_family_or_cell_filtering") is False,
        "Outcome filtering was reported",
    )

    families = _mapping(outcomes.get("families"), "outcomes.families")
    _require(set(families) == set(FAMILY_ORDER), "Outcomes family roster differs")
    f1 = _mapping(families["F1_item_source_form"], "F1")
    f2 = _mapping(families["F2_prototype_depth_dose"], "F2")
    f3 = _mapping(families["F3_random_null_calibration"], "F3")
    for family_id, family in zip(FAMILY_ORDER, (f1, f2, f3), strict=True):
        _require(
            family.get("family_id") == family_id, f"Family ID differs: {family_id}"
        )
        _require(
            family.get("status") == FAMILY_STATUS, f"Family status differs: {family_id}"
        )

    f1_rows = {
        key: _rows(f1.get(key), f"F1.{key}", EXPECTED_COUNTS[f"F1.{key}"])
        for key in (
            "contrast_availability",
            "contrast_denominators",
            "overall_summaries",
            "system_summaries",
        )
    }
    _require(
        f1.get("rows_retained") == EXPECTED_RETAINED_ROWS["F1.rows_retained"],
        "F1 retained-row count differs",
    )
    token_scope = _mapping(f1.get("token_matching_scope"), "F1.token_matching_scope")
    _require(
        token_scope.get("maximum_supported_label") == "count_signature_only",
        "F1 tokenizer label differs",
    )
    _require(
        token_scope.get("token_identity_matched") is False,
        "F1 exact-token claim changed",
    )
    _require(
        token_scope.get("prefix_token_identity_matched") is False,
        "F1 prefix-token claim changed",
    )
    _models_and_endpoints(f1_rows["overall_summaries"], PILOT_MODELS, "F1 overall")

    f2_rows = {
        key: _rows(f2.get(key), f"F2.{key}", EXPECTED_COUNTS[f"F2.{key}"])
        for key in (
            "complete_surface_summaries",
            "dose_order_summaries",
            "headline_macro_summaries",
            "sign_antisymmetry_summaries",
            "sign_orientation_summaries",
            "source_form_contrast_summaries",
        )
    }
    _require(
        f2.get("rows_retained") == EXPECTED_RETAINED_ROWS["F2.rows_retained"],
        "F2 retained-row count differs",
    )
    _models_and_endpoints(f2_rows["dose_order_summaries"], PILOT_MODELS, "F2 dose")
    _require(
        {str(row.get("endpoint")) for row in f2_rows["sign_antisymmetry_summaries"]}
        == {"entropy_change"},
        "F2 entropy antisymmetry endpoint differs",
    )

    f3_rows = {
        key: _rows(f3.get(key), f"F3.{key}", EXPECTED_COUNTS[f"F3.{key}"])
        for key in (
            "calibration_summaries",
            "headline_macro_summaries",
            "random_quantiles",
        )
    }
    for key in (
        "prototype_rows_retained",
        "random_rows_retained",
        "calibrated_positive_prototype_rows",
        "uncalibrated_negative_prototype_rows",
    ):
        _require(
            f3.get(key) == EXPECTED_RETAINED_ROWS[f"F3.{key}"],
            f"F3 count differs: {key}",
        )
    _require(
        f3.get("negative_random_orientation_acquired") is False,
        "Unexpected negative random null",
    )
    _require(
        f3.get("random_null_definition")
        == "positive_orientation_isotropic_standard_normal_then_unit_rms",
        "F3 random-null definition differs",
    )
    _models_and_endpoints(
        f3_rows["headline_macro_summaries"], PILOT_MODELS, "F3 headline"
    )
    _require(
        all(
            row.get("calibrated_sign") == 1
            for row in f3_rows["headline_macro_summaries"]
        ),
        "F3 includes a non-positive calibrated sign",
    )
    return outcomes


def _validate_geometry_documents(
    documents: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    _require(
        set(documents) == set(GEOMETRY_FILENAMES), "Geometry document roster differs"
    )
    for name, document in documents.items():
        _validate_finite(document, f"geometry.{name}")

    zero = _mapping(documents[GEOMETRY_FILENAMES[0]], "zero")
    f4 = _mapping(documents[GEOMETRY_FILENAMES[1]], "F4")
    f5 = _mapping(documents[GEOMETRY_FILENAMES[2]], "F5")
    f6 = _mapping(documents[GEOMETRY_FILENAMES[3]], "F6")
    receipt = _mapping(documents[GEOMETRY_FILENAMES[4]], "receipt")
    result = {"zero": zero, "F4": f4, "F5": f5, "F6": f6, "receipt": receipt}

    _require(zero.get("amendment_id") == AMENDMENT_ID, "Zero amendment ID differs")
    _require(
        zero.get("source_analysis_id") == SOURCE_ANALYSIS_ID, "Zero analysis ID differs"
    )
    _require(
        zero.get("source_protocol_id") == SOURCE_PROTOCOL_ID, "Zero protocol ID differs"
    )
    _require(zero.get("status") == ZERO_STATUS, "Zero status differs")
    _require(zero.get("no_claim_of_exact_js") is True, "Zero receipt claims exact JS")
    _require(
        zero.get("scientific_values_opened_before_all_zero") is False,
        "Values opened before zero",
    )
    zero_models = _rows(
        zero.get("models"), "zero.models", EXPECTED_COUNTS["zero.models"]
    )
    _require(
        [row.get("model") for row in zero_models] == list(PILOT_MODELS),
        "Zero model order differs",
    )
    for row in zero_models:
        model = str(row.get("model"))
        _require(row.get("rows") == 256, f"Zero row count differs: {model}")
        _require(
            row.get("status") == ZERO_MODEL_STATUS,
            f"Zero model status differs: {model}",
        )
        grid = _mapping(row.get("grid"), f"zero grid: {model}")
        _require(
            grid.get("site_count") == 8
            and grid.get("target_count") == 32
            and grid.get("unique_site_target_cells") == 256,
            f"Zero grid differs: {model}",
        )
        primitives = _mapping(
            row.get("primitive_exact_noop"), f"zero primitives: {model}"
        )
        _require(
            set(primitives) == EXACT_ZERO_PRIMITIVES,
            f"Zero primitive roster differs: {model}",
        )
        _require(
            all(value is True for value in primitives.values()),
            f"Zero primitive failed: {model}",
        )
        residual = _mapping(row.get("js_residual"), f"zero JS: {model}")
        tolerance = _number(residual.get("tolerance"), f"zero JS tolerance: {model}")
        maximum_absolute = _number(
            residual.get("maximum_absolute"), f"zero JS maximum: {model}"
        )
        _require(
            tolerance == FLOAT32_JS_TOLERANCE, f"Zero JS tolerance differs: {model}"
        )
        _require(maximum_absolute <= tolerance, f"Zero JS bound failed: {model}")
        _require(
            _integer(residual.get("exact_zero_rows"), "zero exact rows")
            + _integer(residual.get("nonzero_rows"), "zero nonzero rows")
            == 256,
            f"Zero JS row partition differs: {model}",
        )

    for family_id, family in (
        ("F4_target_sensitivity", f4),
        ("F5_output_direction", f5),
        ("F6_source_geometry", f6),
    ):
        _require(
            family.get("family_id") == family_id,
            f"Geometry family ID differs: {family_id}",
        )
        _require(
            family.get("status") == GEOMETRY_FAMILY_STATUS,
            f"Geometry family status differs: {family_id}",
        )

    f4_rows = {
        key: _rows(f4.get(key), f"F4.{key}", EXPECTED_COUNTS[f"F4.{key}"])
        for key in (
            "associations",
            "baseline_features",
            "target_group_heterogeneity",
            "target_profiles",
        )
    }
    _models_and_endpoints(f4_rows["associations"], PILOT_MODELS, "F4 associations")
    _require(
        all(row.get("target_count") == 32 for row in f4_rows["associations"]),
        "F4 target count differs",
    )

    f5_rows = {
        key: _rows(f5.get(key), f"F5.{key}", EXPECTED_COUNTS[f"F5.{key}"])
        for key in ("cross_model_rank_concordance", "within_model_sign_pair_summaries")
    }
    _require(
        {
            str(row[key])
            for row in f5_rows["cross_model_rank_concordance"]
            for key in ("left_model", "right_model")
        }
        == set(PILOT_MODELS),
        "F5 concordance model roster differs",
    )
    _require(
        {str(row.get("endpoint")) for row in f5_rows["cross_model_rank_concordance"]}
        == set(ENDPOINT_ORDER),
        "F5 concordance endpoint roster differs",
    )
    _require(
        f5.get("raw_countsketch_or_token_id_cross_model_comparisons") == 0,
        "Forbidden F5 cross-model vectors found",
    )
    random_pair = _mapping(f5.get("random_direction_sign_pair"), "F5 random sign pair")
    _require(
        random_pair.get("status") == "unavailable", "F5 random sign-pair status differs"
    )
    sign_pairs = _mapping(f5.get("within_model_sign_pairs"), "F5 sign-pair counts")
    _require(set(sign_pairs) == set(PILOT_MODELS), "F5 sign-pair model roster differs")
    _require(
        all(
            value == EXPECTED_RETAINED_ROWS["F5.within_model_sign_pairs_each"]
            for value in sign_pairs.values()
        ),
        "F5 sign-pair count differs",
    )
    for row in f5_rows["within_model_sign_pair_summaries"]:
        count = _integer(row.get("sign_pairs"), "F5 sign_pairs")
        statistics = _mapping(row.get("statistics"), "F5 statistics")
        for key in (
            "sign_reversed_countsketch_cosine",
            "mean_swapped_top64_overlap",
            "top_tail_sign_purity",
        ):
            metric = _mapping(statistics.get(key), f"F5 {key}")
            _require(metric.get("n") == count, f"F5 metric denominator differs: {key}")
    condition_counts = {
        kind: sum(
            row.get("condition_kind") == condition_kind
            for row in f5_rows["within_model_sign_pair_summaries"]
        )
        for kind, condition_kind in (
            ("F5.item_sign_pair_summaries", "item_source_form"),
            (
                "F5.prototype_sign_pair_summaries",
                "glyph_system_source_form_prototype",
            ),
        )
    }
    _require(
        all(condition_counts[key] == EXPECTED_COUNTS[key] for key in condition_counts),
        "F5 condition-kind summary counts differ",
    )

    f6_rows = {
        key: _rows(f6.get(key), f"F6.{key}", EXPECTED_COUNTS[f"F6.{key}"])
        for key in (
            "glyph_name_decomposition_cosines",
            "depth_trajectories",
            "source_form_availability",
            "structural_missingness",
            "tokenizer_signature_match_summaries",
            "tokenizer_signature_strata",
            "wrapper_dispersion",
        )
    }
    _require(
        f6.get("direction_mean_integrity_vectors_checked")
        == EXPECTED_RETAINED_ROWS["F6.direction_mean_integrity_vectors_checked"],
        "F6 direction-integrity count differs",
    )
    _require(
        f6.get("cross_model_vector_comparison") == "forbidden_different_hidden_spaces",
        "F6 cross-model policy differs",
    )
    _require(
        {str(row.get("model")) for row in f6_rows["glyph_name_decomposition_cosines"]}
        == set(ALL_MODELS),
        "F6 model roster differs",
    )
    for row in f6_rows["tokenizer_signature_match_summaries"]:
        _require(
            row.get("scope") == "token_count_signatures_only_no_exact_token_id_claim",
            "F6 tokenizer match scope differs",
        )
        pair_cosine = _mapping(row.get("pair_cosine"), "F6 pair cosine")
        _require(
            pair_cosine.get("n") == row.get("items"), "F6 match denominator differs"
        )

    _require(
        receipt.get("amendment_id") == AMENDMENT_ID, "Receipt amendment ID differs"
    )
    _require(
        receipt.get("source_analysis_id") == SOURCE_ANALYSIS_ID,
        "Receipt analysis ID differs",
    )
    _require(
        receipt.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Receipt protocol ID differs",
    )
    _require(receipt.get("status") == GEOMETRY_STATUS, "Receipt status differs")
    _require(
        receipt.get("bootstrap_intervals_included") is False,
        "Geometry receipt includes bootstrap",
    )
    _require(
        receipt.get("raw_arrays_copied") is False, "Geometry receipt copied raw arrays"
    )
    _require(
        receipt.get("zero_hook_gate") == ZERO_MODEL_STATUS, "Receipt zero gate differs"
    )
    return result


def _validate_hashes_and_bindings(
    outcomes: Mapping[str, Any],
    geometry: Mapping[str, Mapping[str, Any]],
    geometry_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, str]:
    receipt = geometry["receipt"]
    zero = geometry["zero"]
    receipt_outputs = _mapping(receipt.get("outputs"), "receipt.outputs")
    _require(
        set(receipt_outputs) == set(GEOMETRY_FILENAMES[:-1]),
        "Receipt output roster differs",
    )
    for filename in GEOMETRY_FILENAMES[:-1]:
        registered = _mapping(receipt_outputs[filename], f"receipt output: {filename}")
        observed = geometry_bindings[filename]
        _require(
            registered.get("bytes") == observed["bytes"],
            f"Byte count differs: {filename}",
        )
        _require(
            registered.get("sha256") == observed["sha256"],
            f"SHA-256 differs: {filename}",
        )

    input_closeout = _mapping(receipt.get("input_closeout"), "receipt.input_closeout")
    authorization = _mapping(
        outcomes.get("value_open_authorization"), "outcomes authorization"
    )
    outcome_zero = _mapping(authorization.get("zero_hook_gate"), "outcomes zero gate")
    run_roots = {
        str(zero.get("run_binding_root_sha256")),
        str(input_closeout.get("external_closeout_root_sha256")),
        str(
            _mapping(
                input_closeout.get("same_process_audit"), "receipt closeout audit"
            ).get("run_binding_root_sha256")
        ),
        str(
            _mapping(
                authorization.get("same_process_closeout_audit"),
                "outcome closeout audit",
            ).get("run_binding_root_sha256")
        ),
        str(outcome_zero.get("run_binding_root_sha256")),
    }
    _require(len(run_roots) == 1, "Run-binding roots differ")
    run_binding = run_roots.pop()
    _require(len(run_binding) == 64, "Run-binding root is malformed")

    closeout_hashes = {
        str(zero.get("scientific_open_receipt_sha256")),
        str(input_closeout.get("scientific_open_receipt_sha256")),
        str(authorization.get("closeout_sha256")),
        str(
            _mapping(outcomes.get("scientific_open_receipt"), "outcomes closeout").get(
                "sha256"
            )
        ),
    }
    _require(len(closeout_hashes) == 1, "Scientific-open receipt hashes differ")
    closeout_hash = closeout_hashes.pop()
    _require(len(closeout_hash) == 64, "Scientific-open receipt hash is malformed")

    outcome_preflight = _mapping(
        authorization.get("preflight_receipt_sha256"), "outcome preflight"
    )
    receipt_preflight = _mapping(
        input_closeout.get("preflight_receipt_sha256"), "receipt preflight"
    )
    _require(
        outcome_preflight == receipt_preflight, "Preflight receipt bindings differ"
    )
    _require(set(outcome_preflight) == set(ALL_MODELS), "Preflight role roster differs")

    receipt_amendment = _mapping(receipt.get("amendment"), "receipt amendment")
    receipt_freeze = _mapping(receipt_amendment.get("freeze_audit"), "receipt freeze")
    _require(
        zero.get("amendment_config_sha256") == receipt_amendment.get("config_sha256"),
        "Amendment config hashes differ",
    )
    _require(
        zero.get("amendment_freeze_manifest_sha256")
        == receipt_freeze.get("freeze_manifest_sha256"),
        "Amendment freeze hashes differ",
    )
    _require(
        receipt_freeze.get("status") == "amendment_freeze_audit_pass",
        "Receipt freeze audit differs",
    )
    _require(
        _mapping(
            authorization.get("same_process_amendment_freeze_audit"),
            "outcome amendment audit",
        ).get("status")
        == "amendment_freeze_audit_pass",
        "Outcome freeze audit differs",
    )
    return {"closeout_sha256": closeout_hash, "run_binding_root_sha256": run_binding}


def _validate_point_results_closeout(
    document: Any,
    input_bindings: Mapping[str, Any],
    source_bindings: Mapping[str, str],
    zero: Mapping[str, Any],
) -> Mapping[str, Any]:
    closeout = _mapping(document, "point-results closeout")
    _validate_finite(closeout, "point_results_closeout")
    _require(
        closeout.get("schema_version") == 1, "Point-results closeout schema differs"
    )
    _require(
        closeout.get("analysis_id") == SOURCE_ANALYSIS_ID,
        "Point-results closeout analysis ID differs",
    )
    _require(
        closeout.get("source_protocol_id") == SOURCE_PROTOCOL_ID,
        "Point-results closeout protocol ID differs",
    )
    _require(
        closeout.get("status") == POINT_RESULTS_CLOSEOUT_STATUS,
        "Point-results closeout status differs",
    )
    _require(
        closeout.get("analyzer_commit") == ANALYZER_COMMIT,
        "Point-results analyzer commit differs",
    )
    _require(
        closeout.get("analyzer_zero_gate_amendment_id") == AMENDMENT_ID,
        "Point-results amendment ID differs",
    )
    _require(
        closeout.get("analyzer_zero_gate_amendment_manifest_sha256")
        == zero.get("amendment_freeze_manifest_sha256"),
        "Point-results amendment manifest binding differs",
    )

    bootstrap = _mapping(closeout.get("bootstrap"), "point-results bootstrap")
    _require(
        bootstrap
        == {
            "executed_replicates": 0,
            "paper_interval_gate_satisfied": False,
            "registered_replicates": 20_000,
            "status": "point_estimates_only_bootstrap_pending",
        },
        "Point-results bootstrap fields differ",
    )
    cross_host = _mapping(
        closeout.get("cross_host_verification"), "point-results cross-host verification"
    )
    _require(
        cross_host
        == {
            "files_compared": 6,
            "files_equal_by_sha256": 6,
            "local_view": "mac2 temporary analysis intake",
            "remote_authority": "furnace derived-output directory",
            "status": "all_derived_outputs_equal_by_sha256",
        },
        "Point-results cross-host verification differs",
    )
    _require(
        closeout.get("raw_arrays_copied_from_furnace") is False,
        "Point-results closeout copied raw arrays",
    )
    _require(
        closeout.get("scientific_values_parsed_after_zero_gate") is True,
        "Point-results value-open order differs",
    )
    json_validation = _mapping(
        closeout.get("json_validation"), "point-results JSON validation"
    )
    _require(
        json_validation
        == {
            "files_parsed": 6,
            "nonfinite_numeric_values": 0,
            "status": "all_derived_json_parsed_without_nonfinite_values",
        },
        "Point-results JSON validation differs",
    )
    execution = _mapping(closeout.get("execution"), "point-results execution")
    _require(
        set(execution) == {"geometry", "outcomes_point"},
        "Point-results execution roster differs",
    )
    for name, record_value in execution.items():
        record = _mapping(record_value, f"point-results execution: {name}")
        _require(
            record.get("status") == "complete",
            f"Point-results execution incomplete: {name}",
        )
        _require(
            record.get("gpu_used") is False,
            f"Point-results execution unexpectedly used GPU: {name}",
        )
        _require(
            record.get("priority") == "nice_15_idle_io",
            f"Point-results execution priority differs: {name}",
        )
        _require(
            _number(record.get("elapsed_seconds"), "point-results elapsed seconds")
            > 0.0,
            "Point-results elapsed time is invalid",
        )
        _require(
            _integer(record.get("maximum_resident_set_kib"), "point-results RSS") > 0,
            "Point-results RSS is invalid",
        )

    zero_gate = _mapping(closeout.get("zero_gate"), "point-results zero gate")
    _require(
        zero_gate
        == {
            "historical_v0_exact_js_gate_status": "failed_closed_and_preserved",
            "nonzero_scientific_values_opened_before_v1_gate": False,
            "primitive_noop_equalities": "exact",
            "v1_js_absolute_tolerance": FLOAT32_JS_TOLERANCE,
            "v1_status": "all_three_pilot_zero_controls_passed",
        },
        "Point-results zero-gate fields differ",
    )

    geometry_bindings = _mapping(
        input_bindings.get("geometry_files"), "geometry bindings"
    )
    outcomes_binding = _mapping(
        input_bindings.get("outcomes_point_json"), "outcomes binding"
    )
    actual_files = {
        str(binding["filename"]): binding for binding in geometry_bindings.values()
    }
    actual_files[str(outcomes_binding["filename"])] = outcomes_binding
    _require(
        set(actual_files) == set(POINT_RESULT_FILENAMES),
        "Point-results actual file roster differs",
    )
    registered_outputs = _mapping(closeout.get("outputs"), "point-results outputs")
    _require(
        set(registered_outputs) == set(POINT_RESULT_FILENAMES),
        "Point-results closeout file roster differs",
    )
    for filename in POINT_RESULT_FILENAMES:
        registered = _mapping(
            registered_outputs[filename], f"point-results output: {filename}"
        )
        observed = actual_files[filename]
        _require(
            registered.get("bytes") == observed.get("bytes"),
            f"Point-results byte count differs: {filename}",
        )
        _require(
            registered.get("sha256") == observed.get("sha256"),
            f"Point-results SHA-256 differs: {filename}",
        )
    total = sum(
        _integer(actual_files[name]["bytes"], f"point-results bytes: {name}")
        for name in POINT_RESULT_FILENAMES
    )
    _require(
        closeout.get("total_derived_output_bytes") == total,
        "Point-results total byte count differs",
    )

    input_closeout = _mapping(
        closeout.get("input_closeout"), "point-results input closeout"
    )
    _require(
        input_closeout.get("sha256") == source_bindings["closeout_sha256"],
        "Point-results input closeout SHA-256 differs",
    )
    _require(
        input_closeout.get("run_binding_root_sha256")
        == source_bindings["run_binding_root_sha256"],
        "Point-results run-binding root differs",
    )
    return closeout


def _mean(values: Iterable[float]) -> float:
    rows = list(values)
    _require(bool(rows), "Cannot average an empty group")
    return math.fsum(rows) / len(rows)


def _median(values: Iterable[float]) -> float:
    rows = sorted(values)
    _require(bool(rows), "Cannot take the median of an empty group")
    middle = len(rows) // 2
    if len(rows) % 2:
        return rows[middle]
    return (rows[middle - 1] + rows[middle]) / 2.0


def _weighted_metric(
    rows: Sequence[Mapping[str, Any]],
    value: Callable[[Mapping[str, Any]], float],
    weight: Callable[[Mapping[str, Any]], int],
) -> dict[str, Any]:
    values = [value(row) for row in rows]
    weights = [weight(row) for row in rows]
    _require(all(item > 0 for item in weights), "Non-positive aggregation weight")
    denominator = sum(weights)
    weighted_mean = (
        math.fsum(item * count for item, count in zip(values, weights, strict=True))
        / denominator
    )
    return {
        "cell_mean_maximum": max(values),
        "cell_mean_minimum": min(values),
        "cells": len(rows),
        "observations": denominator,
        "weighted_mean": weighted_mean,
    }


def _grouped(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str]
) -> dict[tuple[Any, ...], list[Mapping[str, Any]]]:
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


def _summarize_f1(f1: Mapping[str, Any]) -> dict[str, Any]:
    source = list(f1["overall_summaries"])
    rows: list[dict[str, Any]] = []
    for row in source:
        statistic = _mapping(
            _mapping(row["statistics"], "F1 statistics")["paired_difference"],
            "F1 paired difference",
        )
        rows.append(
            {
                "contrast": row["contrast"],
                "endpoint": row["endpoint"],
                "eligible_item_count": row["eligible_item_count"],
                "eligible_target_count": row["eligible_target_count"],
                "maximum": _number(statistic["maximum"], "F1 maximum"),
                "mean": _number(statistic["mean"], "F1 mean"),
                "median": _number(statistic["median"], "F1 median"),
                "minimum": _number(statistic["minimum"], "F1 minimum"),
                "model": row["model"],
                "n_rows": row["n_rows"],
                "sign": row["sign"],
            }
        )
    rows.sort(
        key=lambda row: (
            ENDPOINT_ORDER.index(row["endpoint"]),
            row["contrast"],
            row["model"],
            row["sign"],
        )
    )
    aggregates: list[dict[str, Any]] = []
    for (endpoint, contrast), group in sorted(
        _grouped(rows, ("endpoint", "contrast")).items(),
        key=lambda item: (ENDPOINT_ORDER.index(item[0][0]), item[0][1]),
    ):
        means = [float(row["mean"]) for row in group]
        aggregates.append(
            {
                "contrast": contrast,
                "endpoint": endpoint,
                "mean_of_model_sign_means": _mean(means),
                "mean_range": {"maximum": max(means), "minimum": min(means)},
                "negative_mean_rows": sum(value < 0.0 for value in means),
                "positive_mean_rows": sum(value > 0.0 for value in means),
                "rows": len(group),
                "zero_mean_rows": sum(value == 0.0 for value in means),
            }
        )

    system_aggregates: list[dict[str, Any]] = []
    system_rows = list(f1["system_summaries"])
    for (system, contrast, endpoint), group in sorted(
        _grouped(system_rows, ("glyph_system", "contrast", "endpoint")).items(),
        key=lambda item: (item[0][0], item[0][1], ENDPOINT_ORDER.index(item[0][2])),
    ):
        means = [
            _number(
                _mapping(
                    _mapping(row["statistics"], "F1 system statistics")[
                        "paired_difference"
                    ],
                    "F1 system paired difference",
                )["mean"],
                "F1 system mean",
            )
            for row in group
        ]
        weights = [_integer(row["n_rows"], "F1 system rows") for row in group]
        denominator = sum(weights)
        system_aggregates.append(
            {
                "contrast": contrast,
                "endpoint": endpoint,
                "glyph_system": system,
                "mean_range": {"maximum": max(means), "minimum": min(means)},
                "model_sign_cells": len(group),
                "model_sign_equal_weight_mean": _mean(means),
                "negative_mean_cells": sum(value < 0.0 for value in means),
                "paired_rows": denominator,
                "paired_row_weighted_mean": math.fsum(
                    value * weight for value, weight in zip(means, weights, strict=True)
                )
                / denominator,
                "positive_mean_cells": sum(value > 0.0 for value in means),
                "zero_mean_cells": sum(value == 0.0 for value in means),
            }
        )
    return {
        "aggregate_model_sign_counts_and_ranges": aggregates,
        "contrast_denominators": f1["contrast_denominators"],
        "overall_model_sign_rows": rows,
        "rows_retained": f1["rows_retained"],
        "system_contrast_aggregates": system_aggregates,
        "system_contrast_weighting": {
            "headline": "model_sign_cells_equal_weight",
            "paired_row_alternative": "n_rows_weighted",
        },
        "token_matching_scope": f1["token_matching_scope"],
    }


def _summarize_f2(f2: Mapping[str, Any]) -> dict[str, Any]:
    dose_rows = list(f2["dose_order_summaries"])
    dose: list[dict[str, Any]] = []
    for (model, endpoint), group in sorted(
        _grouped(dose_rows, ("model", "endpoint")).items(),
        key=lambda item: (item[0][0], ENDPOINT_ORDER.index(item[0][1])),
    ):
        summary = _weighted_metric(
            group,
            lambda row: _number(
                _mapping(
                    _mapping(row["statistics"], "F2 dose statistics")[
                        "ordered_non_decreasing"
                    ],
                    "F2 dose metric",
                )["mean"],
                "F2 dose mean",
            ),
            lambda row: _integer(row["n_rows"], "F2 dose rows"),
        )
        dose.append({"endpoint": endpoint, "model": model, **summary})

    anti_rows = list(f2["sign_antisymmetry_summaries"])
    antisymmetry: list[dict[str, Any]] = []
    for (model,), group in sorted(_grouped(anti_rows, ("model",)).items()):
        normalized = _weighted_metric(
            group,
            lambda row: _number(
                _mapping(
                    _mapping(row["statistics"], "F2 antisymmetry statistics")[
                        "normalized_antisymmetry_residual"
                    ],
                    "F2 normalized antisymmetry",
                )["mean"],
                "F2 normalized antisymmetry mean",
            ),
            lambda row: _integer(row["n_rows"], "F2 antisymmetry rows"),
        )
        signed_sum = _weighted_metric(
            group,
            lambda row: _number(
                _mapping(
                    _mapping(row["statistics"], "F2 antisymmetry statistics")[
                        "positive_plus_negative"
                    ],
                    "F2 signed sum",
                )["mean"],
                "F2 signed sum mean",
            ),
            lambda row: _integer(row["n_rows"], "F2 antisymmetry rows"),
        )
        antisymmetry.append(
            {
                "model": model,
                "normalized_antisymmetry_residual": normalized,
                "positive_plus_negative": signed_sum,
                "zero_is_perfect_normalized_antisymmetry": True,
            }
        )

    raw_depth: list[dict[str, Any]] = []
    headline_rows = list(f2["headline_macro_summaries"])
    for (model, endpoint, depth), group in sorted(
        _grouped(headline_rows, ("model", "endpoint", "depth_fraction")).items(),
        key=lambda item: (item[0][0], ENDPOINT_ORDER.index(item[0][1]), item[0][2]),
    ):
        values = [_number(row["mean"], "F2 raw headline mean") for row in group]
        raw_depth.append(
            {
                "depth_fraction": depth,
                "endpoint": endpoint,
                "headline_macro_cells": len(group),
                "maximum": max(values),
                "mean": _mean(values),
                "minimum": min(values),
                "model": model,
            }
        )

    peaks: list[dict[str, Any]] = []
    for (model, endpoint), group in sorted(
        _grouped(raw_depth, ("model", "endpoint")).items(),
        key=lambda item: (item[0][0], ENDPOINT_ORDER.index(item[0][1])),
    ):
        maximum = max(_number(row["mean"], "F2 depth mean") for row in group)
        peaks.append(
            {
                "endpoint": endpoint,
                "maximum_depth_mean": maximum,
                "model": model,
                "peak_depth_fractions": [
                    row["depth_fraction"] for row in group if row["mean"] == maximum
                ],
                "selection_rule": "maximum_equal_weight_raw_headline_macro_mean",
            }
        )
    return {
        "dose_ordering_by_model_endpoint": dose,
        "entropy_antisymmetry_by_model": antisymmetry,
        "raw_headline_mean_by_model_endpoint_depth": raw_depth,
        "raw_headline_peak_by_model_endpoint": peaks,
        "rows_retained": f2["rows_retained"],
        "weighting": {
            "dose_ordering": "target_count_weighted_over_every_registered_system_form_depth_sign_cell",
            "raw_depth": "equal_weight_over_registered_source_form_magnitude_sign_headline_system_macro_cells",
        },
    }


def _f3_aggregate(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for group_key, group in sorted(
        _grouped(rows, keys).items(),
        key=lambda item: tuple(str(value) for value in item[0]),
    ):
        percentiles = [
            _number(row["prototype_random_percentile_mean"], "F3 percentile")
            for row in group
        ]
        differences = [
            _number(row["prototype_minus_random_median_mean"], "F3 difference")
            for row in group
        ]
        output.append(
            {
                **dict(zip(keys, group_key, strict=True)),
                "cells": len(group),
                "percentile_above_half_cells": sum(
                    value > 0.5 for value in percentiles
                ),
                "percentile_below_half_cells": sum(
                    value < 0.5 for value in percentiles
                ),
                "percentile_equal_half_cells": sum(
                    value == 0.5 for value in percentiles
                ),
                "prototype_minus_random_median_mean": _mean(differences),
                "prototype_random_percentile_maximum": max(percentiles),
                "prototype_random_percentile_mean": _mean(percentiles),
                "prototype_random_percentile_minimum": min(percentiles),
            }
        )
    return output


def _summarize_f3(f3: Mapping[str, Any]) -> dict[str, Any]:
    rows = list(f3["headline_macro_summaries"])
    return {
        "by_model_endpoint": _f3_aggregate(rows, ("model", "endpoint")),
        "by_model_endpoint_depth": _f3_aggregate(
            rows, ("model", "endpoint", "depth_fraction")
        ),
        "by_source_form_endpoint": _f3_aggregate(rows, ("source_form", "endpoint")),
        "calibrated_positive_prototype_rows": f3["calibrated_positive_prototype_rows"],
        "negative_random_orientation_acquired": f3[
            "negative_random_orientation_acquired"
        ],
        "random_null_definition": f3["random_null_definition"],
        "random_rows_retained": f3["random_rows_retained"],
        "uncalibrated_negative_prototype_rows": f3[
            "uncalibrated_negative_prototype_rows"
        ],
        "weighting": "equal_weight_over_registered_system_macro_cells",
    }


def _summarize_f4(f4: Mapping[str, Any]) -> dict[str, Any]:
    associations = [
        {
            "baseline_entropy_spearman": row["baseline_entropy_spearman"],
            "baseline_top_two_logit_margin_spearman": row[
                "baseline_top_two_logit_margin_spearman"
            ],
            "condition_kind": row["condition_kind"],
            "endpoint": row["endpoint"],
            "model": row["model"],
            "target_count": row["target_count"],
        }
        for row in f4["associations"]
    ]
    associations.sort(
        key=lambda row: (
            row["model"],
            row["condition_kind"],
            ENDPOINT_ORDER.index(row["endpoint"]),
        )
    )
    ranges = [
        {
            "condition_kind": row["condition_kind"],
            "endpoint": row["endpoint"],
            "group_mean_maximum": max(row["group_means"].values()),
            "group_mean_minimum": min(row["group_means"].values()),
            "group_mean_range": row["group_mean_range"],
            "model": row["model"],
        }
        for row in f4["target_group_heterogeneity"]
    ]
    ranges.sort(
        key=lambda row: (
            row["model"],
            row["condition_kind"],
            ENDPOINT_ORDER.index(row["endpoint"]),
        )
    )
    aggregate: list[dict[str, Any]] = []
    for (model, endpoint), group in sorted(
        _grouped(ranges, ("model", "endpoint")).items(),
        key=lambda item: (item[0][0], ENDPOINT_ORDER.index(item[0][1])),
    ):
        values = [
            _number(row["group_mean_range"], "F4 target-group range") for row in group
        ]
        aggregate.append(
            {
                "condition_kinds": sorted(str(row["condition_kind"]) for row in group),
                "endpoint": endpoint,
                "maximum": max(values),
                "mean": _mean(values),
                "minimum": min(values),
                "model": model,
            }
        )
    return {
        "all_associations": associations,
        "target_group_range_aggregates_by_model_endpoint": aggregate,
        "target_group_ranges": ranges,
    }


def _summarize_f5(f5: Mapping[str, Any]) -> dict[str, Any]:
    concordance = [dict(row) for row in f5["cross_model_rank_concordance"]]
    concordance.sort(
        key=lambda row: (
            row["condition_kind"],
            ENDPOINT_ORDER.index(row["endpoint"]),
            row["left_model"],
            row["right_model"],
        )
    )
    source = list(f5["within_model_sign_pair_summaries"])

    def reversed_mean(row: Mapping[str, Any]) -> float:
        return _number(
            _mapping(
                _mapping(row["statistics"], "F5 statistics")[
                    "sign_reversed_countsketch_cosine"
                ],
                "F5 sign-reversed cosine",
            )["mean"],
            "F5 sign-reversed cosine mean",
        )

    weighted: list[dict[str, Any]] = []
    for (model, source_form, depth), group in sorted(
        _grouped(source, ("model", "source_form", "depth_fraction")).items(),
        key=lambda item: (item[0][0], item[0][1], item[0][2]),
    ):

        def metric(name: str) -> dict[str, Any]:
            return _weighted_metric(
                group,
                lambda row: _number(
                    _mapping(
                        _mapping(row["statistics"], "F5 statistics")[name], f"F5 {name}"
                    )["mean"],
                    f"F5 {name} mean",
                ),
                lambda row: _integer(row["sign_pairs"], "F5 sign pairs"),
            )

        weighted.append(
            {
                "condition_kinds": sorted(
                    {str(row["condition_kind"]) for row in group}
                ),
                "depth_fraction": depth,
                "mean_swapped_top64_overlap": metric("mean_swapped_top64_overlap"),
                "model": model,
                "sign_reversed_countsketch_cosine": metric(
                    "sign_reversed_countsketch_cosine"
                ),
                "source_form": source_form,
                "top_tail_sign_purity": metric("top_tail_sign_purity"),
            }
        )

    prototype_rows = [
        row
        for row in source
        if row["condition_kind"] == "glyph_system_source_form_prototype"
    ]

    def prototype_aggregates(keys: Sequence[str]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for group_key, group in sorted(
            _grouped(prototype_rows, keys).items(),
            key=lambda item: tuple(str(value) for value in item[0]),
        ):
            output.append(
                {
                    **dict(zip(keys, group_key, strict=True)),
                    **_weighted_metric(
                        group,
                        reversed_mean,
                        lambda row: _integer(row["sign_pairs"], "F5 sign pairs"),
                    ),
                }
            )
        return output

    negative_rows = [row for row in prototype_rows if reversed_mean(row) < 0.0]
    minimum_row = min(prototype_rows, key=reversed_mean)
    sign_cell_accounting = {
        "minimum_cell": {
            "depth_fraction": minimum_row["depth_fraction"],
            "glyph_system": minimum_row["glyph_system"],
            "magnitude": minimum_row["magnitude"],
            "mean": reversed_mean(minimum_row),
            "model": minimum_row["model"],
            "sign_pairs": minimum_row["sign_pairs"],
            "source_form": minimum_row["source_form"],
        },
        "negative_mean_cells": len(negative_rows),
        "positive_mean_cells": sum(reversed_mean(row) > 0.0 for row in prototype_rows),
        "prototype_summary_cells": len(prototype_rows),
        "zero_mean_cells": sum(reversed_mean(row) == 0.0 for row in prototype_rows),
    }
    return {
        "cross_model_rank_concordance": concordance,
        "prototype_sign_reversal": {
            "all_prototypes": prototype_aggregates(()),
            "by_depth": prototype_aggregates(("depth_fraction",)),
            "by_magnitude": prototype_aggregates(("magnitude",)),
            "by_model": prototype_aggregates(("model",)),
            "by_model_depth_magnitude": prototype_aggregates(
                ("model", "depth_fraction", "magnitude")
            ),
            "cell_sign_accounting": sign_cell_accounting,
            "weighting": "sign_pair_count_weighted_over_all_2016_registered_prototype_summary_cells",
        },
        "random_direction_sign_pair": f5["random_direction_sign_pair"],
        "weighted_sign_reversal_by_model_source_form_depth": weighted,
        "weighting": "sign_pair_count_weighted_over_all_registered_item_and_prototype_cells",
    }


def _summarize_f6(f6: Mapping[str, Any]) -> dict[str, Any]:
    pair_rows = list(f6["glyph_name_decomposition_cosines"])

    def pair_cosine(row: Mapping[str, Any]) -> float:
        return _number(_mapping(row["cosine"], "F6 cosine")["mean"], "F6 cosine mean")

    def pair_items(row: Mapping[str, Any]) -> int:
        return _integer(_mapping(row["cosine"], "F6 cosine")["n"], "F6 cosine n")

    pair_output: list[dict[str, Any]] = []
    for (model, system, pair), group in sorted(
        _grouped(pair_rows, ("model", "glyph_system", "pair")).items()
    ):
        result = _weighted_metric(
            group,
            pair_cosine,
            pair_items,
        )
        pair_output.append(
            {"glyph_system": system, "model": model, "pair": pair, **result}
        )

    pooled_pairs: list[dict[str, Any]] = []
    for (pair,), group in sorted(_grouped(pair_rows, ("pair",)).items()):
        pooled_pairs.append(
            {
                "pair": pair,
                **_weighted_metric(group, pair_cosine, pair_items),
            }
        )

    pooled_system_pairs: list[dict[str, Any]] = []
    for (system, pair), group in sorted(
        _grouped(pair_rows, ("glyph_system", "pair")).items()
    ):
        pooled_system_pairs.append(
            {
                "glyph_system": system,
                "pair": pair,
                **_weighted_metric(group, pair_cosine, pair_items),
            }
        )

    first_final_depth: list[dict[str, Any]] = []
    first_and_final_rows = [row for row in pair_rows if row["depth_index"] in {0, 7}]
    for (pair, depth), group in sorted(
        _grouped(first_and_final_rows, ("pair", "depth_index")).items()
    ):
        first_final_depth.append(
            {
                "depth_index": depth,
                "pair": pair,
                **_weighted_metric(group, pair_cosine, pair_items),
            }
        )

    depth_changes = [
        {
            "final_minus_first": row["final_minus_first"],
            "glyph_system": row["glyph_system"],
            "model": row["model"],
            "pair": row["pair"],
        }
        for row in f6["depth_trajectories"]
    ]
    depth_changes.sort(key=lambda row: (row["model"], row["glyph_system"], row["pair"]))

    model_pair_depth_changes: list[dict[str, Any]] = []
    for (model, pair), group in sorted(
        _grouped(list(f6["depth_trajectories"]), ("model", "pair")).items()
    ):
        model_pair_depth_changes.append(
            {
                "model": model,
                "pair": pair,
                **_weighted_metric(
                    group,
                    lambda row: _number(
                        _mapping(row["final_minus_first"], "F6 depth change")["mean"],
                        "F6 depth change mean",
                    ),
                    lambda row: _integer(
                        _mapping(row["final_minus_first"], "F6 depth change")["n"],
                        "F6 depth change n",
                    ),
                ),
            }
        )

    wrapper_output: list[dict[str, Any]] = []
    wrapper_rows = list(f6["wrapper_dispersion"])
    for (model, system, source_form), group in sorted(
        _grouped(wrapper_rows, ("model", "glyph_system", "source_form")).items()
    ):

        def metric(name: str) -> dict[str, Any]:
            return _weighted_metric(
                group,
                lambda row: _number(
                    _mapping(row[name], f"F6 {name}")["mean"], f"F6 {name} mean"
                ),
                lambda row: _integer(
                    _mapping(row[name], f"F6 {name}")["n"], f"F6 {name} n"
                ),
            )

        wrapper_output.append(
            {
                "glyph_system": system,
                "model": model,
                "relative_residual_rms": metric("relative_residual_rms"),
                "source_form": source_form,
                "wrapper_direction_cosine": metric("wrapper_direction_cosine"),
            }
        )

    def wrapper_aggregates(keys: Sequence[str]) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for group_key, group in sorted(
            _grouped(wrapper_rows, keys).items(),
            key=lambda item: tuple(str(value) for value in item[0]),
        ):
            record: dict[str, Any] = dict(zip(keys, group_key, strict=True))
            for metric_name in ("relative_residual_rms", "wrapper_direction_cosine"):
                record[metric_name] = _weighted_metric(
                    group,
                    lambda row, name=metric_name: _number(
                        _mapping(row[name], f"F6 {name}")["mean"],
                        f"F6 {name} mean",
                    ),
                    lambda row, name=metric_name: _integer(
                        _mapping(row[name], f"F6 {name}")["n"], f"F6 {name} n"
                    ),
                )
            output.append(record)
        return output

    match_output: list[dict[str, Any]] = []
    match_rows = list(f6["tokenizer_signature_match_summaries"])
    for (model, system, pair, matched), group in sorted(
        _grouped(
            match_rows,
            ("model", "glyph_system", "pair", "token_count_signature_exact_match"),
        ).items(),
        key=lambda item: (item[0][0], item[0][1], item[0][2], item[0][3]),
    ):
        result = _weighted_metric(
            group,
            lambda row: _number(
                _mapping(row["pair_cosine"], "F6 signature cosine")["mean"],
                "F6 signature cosine mean",
            ),
            lambda row: _integer(row["items"], "F6 signature items"),
        )
        match_output.append(
            {
                "glyph_system": system,
                "model": model,
                "pair": pair,
                "token_count_signature_exact_match": matched,
                **result,
            }
        )

    signature_pooled: list[dict[str, Any]] = []
    for (matched,), group in sorted(
        _grouped(match_rows, ("token_count_signature_exact_match",)).items()
    ):
        signature_pooled.append(
            {
                "token_count_signature_exact_match": matched,
                **_weighted_metric(
                    group,
                    lambda row: _number(
                        _mapping(row["pair_cosine"], "F6 signature cosine")["mean"],
                        "F6 signature cosine mean",
                    ),
                    lambda row: _integer(row["items"], "F6 signature items"),
                ),
            }
        )

    match_by_stratum = _grouped(
        match_rows, ("model", "glyph_system", "pair", "depth_index")
    )
    stratum_differences: list[dict[str, Any]] = []
    for (model, system, pair, depth), group in sorted(match_by_stratum.items()):
        by_match: dict[bool, Mapping[str, Any]] = {}
        for row in group:
            matched = row["token_count_signature_exact_match"]
            _require(
                isinstance(matched, bool), "F6 signature match flag is not Boolean"
            )
            _require(matched not in by_match, "Duplicate F6 match-status stratum")
            by_match[matched] = row
        if set(by_match) != {False, True}:
            continue
        matched_mean = _number(
            _mapping(by_match[True]["pair_cosine"], "F6 matched cosine")["mean"],
            "F6 matched cosine mean",
        )
        unmatched_mean = _number(
            _mapping(by_match[False]["pair_cosine"], "F6 unmatched cosine")["mean"],
            "F6 unmatched cosine mean",
        )
        stratum_differences.append(
            {
                "depth_index": depth,
                "glyph_system": system,
                "matched_items": by_match[True]["items"],
                "matched_mean": matched_mean,
                "matched_minus_unmatched": matched_mean - unmatched_mean,
                "model": model,
                "pair": pair,
                "unmatched_items": by_match[False]["items"],
                "unmatched_mean": unmatched_mean,
            }
        )

    def difference_accounting(
        rows: Sequence[Mapping[str, Any]], keys: Sequence[str]
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for group_key, group in sorted(
            _grouped(rows, keys).items(),
            key=lambda item: tuple(str(value) for value in item[0]),
        ):
            differences = [
                _number(row["matched_minus_unmatched"], "F6 stratum difference")
                for row in group
            ]
            output.append(
                {
                    **dict(zip(keys, group_key, strict=True)),
                    "comparisons": len(group),
                    "maximum": max(differences),
                    "mean": _mean(differences),
                    "median": _median(differences),
                    "minimum": min(differences),
                    "negative": sum(value < 0.0 for value in differences),
                    "positive": sum(value > 0.0 for value in differences),
                    "zero": sum(value == 0.0 for value in differences),
                }
            )
        return output

    return {
        "count_signature_matched_unmatched": match_output,
        "count_signature_pooled": signature_pooled,
        "depth_changes": depth_changes,
        "depth_change_by_model_pair": model_pair_depth_changes,
        "direction_mean_integrity_vectors_checked": f6[
            "direction_mean_integrity_vectors_checked"
        ],
        "first_final_depth_pair_cosines": first_final_depth,
        "glyph_system_pair_cosines": pooled_system_pairs,
        "pair_cosines_by_model_system": pair_output,
        "pooled_form_pair_cosines": pooled_pairs,
        "tokenizer_scope": "token_count_signatures_only_no_exact_token_id_claim",
        "tokenizer_signature_strata_records_validated": len(
            f6["tokenizer_signature_strata"]
        ),
        "within_stratum_matched_minus_unmatched": {
            "all_comparisons": stratum_differences,
            "by_pair": difference_accounting(stratum_differences, ("pair",)),
            "overall": difference_accounting(stratum_differences, ()),
            "weighting": "equal_weight_over_same_model_system_pair_depth_comparisons_with_both_count_signature_groups",
        },
        "wrapper_by_depth": wrapper_aggregates(("depth_index",)),
        "wrapper_by_model": wrapper_aggregates(("model",)),
        "weighted_wrapper_dispersion": wrapper_output,
        "weighting": "registered_item_count_weighted_over_depth_rows",
    }


def _summarize_zero(zero: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for row in zero["models"]:
        residual = row["js_residual"]
        rows.append(
            {
                "exact_js_zero_rows": residual["exact_zero_rows"],
                "js_maximum": residual["maximum"],
                "js_maximum_absolute": residual["maximum_absolute"],
                "js_minimum": residual["minimum"],
                "js_nonzero_roundtrip_rows": residual["nonzero_rows"],
                "js_tolerance": residual["tolerance"],
                "model": row["model"],
                "primitive_exact_noop": row["primitive_exact_noop"],
                "rows": row["rows"],
                "v0_exact_js_predicate_on_current_rows": row[
                    "v0_exact_js_predicate_on_current_rows"
                ],
            }
        )
    return {
        "historical_v0_exact_js_gate": zero["original_v0_exact_js_gate"],
        "js_maximum_absolute_across_models": max(
            row["js_maximum_absolute"] for row in rows
        ),
        "js_nonzero_roundtrip_rows_across_models": sum(
            row["js_nonzero_roundtrip_rows"] for row in rows
        ),
        "models": rows,
        "no_claim_of_exact_js": True,
        "status": zero["status"],
    }


def build_summary(
    outcomes_document: Any,
    geometry_documents: Mapping[str, Any],
    point_results_closeout_document: Any,
    input_bindings: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate already parsed inputs and build a deterministic point summary."""

    outcomes = _validate_outcomes(outcomes_document)
    geometry = _validate_geometry_documents(geometry_documents)
    geometry_bindings = _mapping(
        input_bindings.get("geometry_files"), "geometry bindings"
    )
    binding_roots = _validate_hashes_and_bindings(outcomes, geometry, geometry_bindings)
    _validate_point_results_closeout(
        point_results_closeout_document,
        input_bindings,
        binding_roots,
        geometry["zero"],
    )
    canonical_binding = json.dumps(
        input_bindings, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    families = _mapping(outcomes["families"], "outcome families")
    return {
        "analysis_identity": {
            "amendment_id": AMENDMENT_ID,
            "source_analysis_id": SOURCE_ANALYSIS_ID,
            "source_protocol_id": SOURCE_PROTOCOL_ID,
        },
        "bootstrap": {
            "executed_replicates": 0,
            "intervals_included": False,
            "paper_interval_gate_satisfied": False,
            "registered_replicates": 20_000,
            "status": "pending",
        },
        "claim_boundary": outcomes["claim_boundary"],
        "decision_status": "post_outcome_reporting_only_no_inferential_selection_no_confirmatory_verdict",
        "endpoint_order": list(ENDPOINT_ORDER),
        "families": {
            "F1_item_source_form": _summarize_f1(families["F1_item_source_form"]),
            "F2_prototype_depth_dose": _summarize_f2(
                families["F2_prototype_depth_dose"]
            ),
            "F3_random_null_calibration": _summarize_f3(
                families["F3_random_null_calibration"]
            ),
            "F4_target_sensitivity": _summarize_f4(geometry["F4"]),
            "F5_output_direction": _summarize_f5(geometry["F5"]),
            "F6_source_geometry": _summarize_f6(geometry["F6"]),
        },
        "input_binding_sha256": hashlib.sha256(canonical_binding).hexdigest(),
        "input_bindings": input_bindings,
        "point_results_closeout_sha256": input_bindings["point_results_closeout_json"][
            "sha256"
        ],
        "reporting_policy": {
            "all_endpoints_retained": True,
            "bootstrap_pending": True,
            "descriptive_point_synthesis_only": True,
            "inferential_selection": False,
            "post_outcome": True,
            "raw_arrays_read": False,
            "significance_tests": False,
        },
        "run_binding_root_sha256": binding_roots["run_binding_root_sha256"],
        "schema_version": 1,
        "scientific_open_receipt_sha256": binding_roots["closeout_sha256"],
        "status": "post_outcome_reporting_synthesis_complete_bootstrap_pending",
        "summary_id": SUMMARY_ID,
        "zero_control": _summarize_zero(geometry["zero"]),
    }


def summarize_paths(
    outcomes_path: Path,
    geometry_directory: Path,
    point_results_closeout_path: Path,
) -> dict[str, Any]:
    """Load, authenticate, validate, and summarize the production files."""

    _regular_file(outcomes_path)
    _require(
        geometry_directory.is_dir() and not geometry_directory.is_symlink(),
        "Geometry directory is invalid",
    )
    observed_names = sorted(path.name for path in geometry_directory.iterdir())
    _require(
        observed_names == sorted(GEOMETRY_FILENAMES),
        "Geometry directory has missing or extra entries",
    )
    outcomes_binding = _file_binding(outcomes_path)
    geometry_bindings = {
        filename: _file_binding(geometry_directory / filename)
        for filename in GEOMETRY_FILENAMES
    }
    documents = {
        filename: _read_json(geometry_directory / filename)
        for filename in GEOMETRY_FILENAMES
    }
    bindings = {
        "geometry_files": geometry_bindings,
        "outcomes_point_json": outcomes_binding,
        "point_results_closeout_json": _file_binding(point_results_closeout_path),
    }
    return build_summary(
        _read_json(outcomes_path),
        documents,
        _read_json(point_results_closeout_path),
        bindings,
    )


def write_json_exclusive(path: Path, document: Mapping[str, Any]) -> None:
    """Publish complete JSON atomically and fail if the destination exists."""

    _require(path.parent.is_dir(), f"Output parent is missing: {path.parent}")
    _require(
        not path.exists() and not path.is_symlink(), f"Output already exists: {path}"
    )
    payload = (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    stage = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    descriptor = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(stage, path, follow_symlinks=False)
        except OSError as error:
            if error.errno == errno.EEXIST:
                raise ReportingSummaryError(f"Output already exists: {path}") from error
            raise ReportingSummaryError(
                f"Atomic exclusive output failed: {path}"
            ) from error
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        try:
            stage.unlink()
        except FileNotFoundError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outcomes-point-json", type=Path, required=True)
    parser.add_argument("--geometry-directory", type=Path, required=True)
    parser.add_argument("--point-results-closeout-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    summary = summarize_paths(
        arguments.outcomes_point_json,
        arguments.geometry_directory,
        arguments.point_results_closeout_json,
    )
    write_json_exclusive(arguments.output_json, summary)
    print(
        json.dumps(
            {"output": str(arguments.output_json), "status": summary["status"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
