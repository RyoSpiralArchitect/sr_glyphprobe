from __future__ import annotations

import math
from numbers import Integral, Real
from typing import Any


def _finite_real(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, Real):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _nonnegative_count(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, Integral):
        return None
    result = int(value)
    return result if result >= 0 else None


def build_readiness_report(summary: dict[str, Any]) -> dict[str, Any]:
    """Translate pre-stage diagnostics into explicit gates, never a causal verdict."""
    token_counts = summary.get("glyph_token_counts", [])
    primary_token_count = (
        isinstance(token_counts, list)
        and bool(token_counts)
        and all(
            (count := _nonnegative_count(value)) is not None and count > 0
            for value in token_counts
        )
        and len(set(token_counts)) == 1
    )
    wrapper_count = _nonnegative_count(summary.get("wrapper_count"))
    wrapper_mismatch_count = _nonnegative_count(
        summary.get("wrapper_token_count_mismatch_count")
    )
    target_case_count = _nonnegative_count(summary.get("target_case_count"))
    random_control_count = _nonnegative_count(summary.get("random_control_count"))
    zero_hook_control_count = _nonnegative_count(
        summary.get("zero_hook_control_count")
    )
    zero_hook_logit_delta = _finite_real(
        summary.get("zero_hook_max_logit_delta_rms")
    )
    zero_hook_activation_delta = _finite_real(
        summary.get("zero_hook_max_activation_delta_rms")
    )
    strength_count = _nonnegative_count(summary.get("strength_count"))
    scalar_strength_error = _finite_real(
        summary.get("median_emoji_perturbation_ratio_max_abs_error")
    )
    direction_alignment = _finite_real(
        summary.get("median_direction_replicate_alignment")
    )
    fingerprint_advantage = _finite_real(summary.get("emoji_fingerprint_advantage"))
    permutation_p = _finite_real(summary.get("median_emoji_label_permutation_p"))
    cross_seed_advantage = _finite_real(
        summary.get("cross_seed_fingerprint_advantage")
    )
    checks = [
        {
            "id": "tokenization_control",
            "pass": primary_token_count,
            "value": sorted(set(token_counts)),
            "criterion": "All primary glyphs have the same raw token count.",
        },
        {
            "id": "wrapper_tokenization_control",
            "pass": (
                wrapper_count is not None
                and wrapper_count > 0
                and wrapper_mismatch_count == 0
            ),
            "value": summary.get("wrapper_token_count_mismatch_ids", []),
            "criterion": "Each sealed source wrapper has the same total token count across primary glyphs.",
        },
        {
            "id": "source_direction_stability",
            "pass": direction_alignment is not None and direction_alignment >= 0.50,
            "value": summary.get("median_direction_replicate_alignment"),
            "criterion": "Median source-direction replicate alignment >= 0.50.",
        },
        {
            "id": "target_case_count",
            "pass": target_case_count is not None and target_case_count >= 16,
            "value": summary.get("target_case_count", 0),
            "criterion": "At least 16 target prompt records are present.",
        },
        {
            "id": "random_direction_control",
            "pass": random_control_count is not None and random_control_count > 0,
            "value": summary.get("random_control_count", 0),
            "criterion": "At least one random-direction control record is present.",
        },
        {
            "id": "zero_hook_noop",
            "pass": (
                zero_hook_control_count is not None
                and zero_hook_control_count > 0
                and zero_hook_logit_delta is not None
                and 0.0 <= zero_hook_logit_delta <= 1e-6
                and zero_hook_activation_delta is not None
                and 0.0 <= zero_hook_activation_delta <= 1e-6
            ),
            "value": {
                "count": summary.get("zero_hook_control_count", 0),
                "max_logit_delta_rms": summary.get("zero_hook_max_logit_delta_rms"),
                "max_activation_delta_rms": summary.get(
                    "zero_hook_max_activation_delta_rms"
                ),
            },
            "criterion": "An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.",
        },
        {
            "id": "strength_dose_grid",
            "pass": strength_count is not None and strength_count >= 3,
            "value": summary.get("strength_count", 0),
            "criterion": "At least three positive strengths for dose-response inspection.",
        },
        {
            "id": "scalar_strength_match",
            "pass": (
                scalar_strength_error is not None
                and 0.0 <= scalar_strength_error <= 1e-5
            ),
            "value": summary.get("median_emoji_perturbation_ratio_max_abs_error"),
            "criterion": "Median maximum achieved-RMS-ratio error <= 1e-5.",
        },
        {
            "id": "fingerprint_reproducibility",
            "pass": fingerprint_advantage is not None and fingerprint_advantage > 0.0,
            "value": summary.get("emoji_fingerprint_advantage"),
            "criterion": "Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.",
        },
        {
            "id": "label_identity_permutation",
            "pass": (
                permutation_p is not None and 0.0 <= permutation_p <= 0.05
            ),
            "value": summary.get("median_emoji_label_permutation_p"),
            "criterion": (
                "Median within-target label-shuffle screening p-value <= 0.05; "
                "this is a screening flag, not a multiplicity-corrected global test."
            ),
        },
        {
            "id": "cross_seed_output_stability",
            "pass": cross_seed_advantage is not None and cross_seed_advantage > 0.0,
            "value": summary.get("cross_seed_fingerprint_advantage"),
            "criterion": "Same-glyph cross-seed fingerprint separation exceeds the random-direction null.",
        },
    ]
    return {
        "stage": "pre-causal-readiness-only",
        "causal_claim_authorized": False,
        "checks": checks,
        "passed": sum(bool(check["pass"]) for check in checks),
        "total": len(checks),
        "warning": (
            "Passing these gates supports escalation to targeted patching and path-level tests; "
            "it does not establish a semantic or mechanistic causal interpretation."
        ),
    }
