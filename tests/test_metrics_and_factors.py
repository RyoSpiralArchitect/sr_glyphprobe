from __future__ import annotations

import numpy as np
import pytest

from glyphprobe.analysis.factors import balanced_two_factor_decomposition
from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.config import EmojiItem


def test_distribution_identity_metrics() -> None:
    logits = np.array([0.1, 1.0, -0.2, 0.4], dtype=np.float64)
    result = distribution_metrics(
        logits,
        logits.copy(),
        top_k=4,
        rbo_p=0.9,
        fingerprint_dim=8,
        fingerprint_seed=3,
        save_top_deltas=2,
    )
    assert result["kl_base_to_intervened"] == 0.0
    assert result["js_divergence"] == 0.0
    assert result["total_variation"] == 0.0
    assert result["argmax_flip"] is False
    assert result["top_k_jaccard"] == 1.0
    assert np.allclose(result["fingerprint"], 0.0)


def test_balanced_factor_energy_closes() -> None:
    items = [
        EmojiItem(id="r_c", glyph="a", factors={"color": "red", "shape": "circle"}),
        EmojiItem(id="r_s", glyph="b", factors={"color": "red", "shape": "square"}),
        EmojiItem(id="b_c", glyph="c", factors={"color": "blue", "shape": "circle"}),
        EmojiItem(id="b_s", glyph="d", factors={"color": "blue", "shape": "square"}),
    ]
    # Orthogonal color and shape effects, no interaction.
    vectors = np.array(
        [
            [1.0, 1.0],
            [1.0, -1.0],
            [-1.0, 1.0],
            [-1.0, -1.0],
        ]
    )
    result = balanced_two_factor_decomposition(vectors, items)
    assert result["available"] is True
    assert np.isclose(result["energy_closure"], 1.0)
    assert np.isclose(result["interaction_energy_fraction"], 0.0)
    assert result["max_reconstruction_error"] < 1e-12


def test_readiness_rejects_wrapper_token_count_mismatch() -> None:
    from glyphprobe.analysis.readiness import build_readiness_report

    report = build_readiness_report(
        {
            "glyph_token_counts": [1, 1],
            "wrapper_count": 2,
            "wrapper_token_count_mismatch_count": 1,
            "wrapper_token_count_mismatch_ids": ["w02"],
        }
    )
    check = next(
        row for row in report["checks"] if row["id"] == "wrapper_tokenization_control"
    )
    assert check["pass"] is False
    assert check["value"] == ["w02"]


def _passing_readiness_summary() -> dict[str, object]:
    return {
        "glyph_token_counts": [3, 3],
        "wrapper_count": 2,
        "wrapper_token_count_mismatch_count": 0,
        "wrapper_token_count_mismatch_ids": [],
        "median_direction_replicate_alignment": 0.75,
        "target_case_count": 16,
        "random_control_count": 1,
        "zero_hook_control_count": 1,
        "zero_hook_max_logit_delta_rms": 0.0,
        "zero_hook_max_activation_delta_rms": 0.0,
        "strength_count": 3,
        "median_emoji_perturbation_ratio_max_abs_error": 0.0,
        "emoji_fingerprint_advantage": 0.1,
        "median_emoji_label_permutation_p": 0.05,
        "cross_seed_fingerprint_advantage": 0.1,
    }


def _readiness_check(report: dict, check_id: str) -> dict:
    return next(row for row in report["checks"] if row["id"] == check_id)


def test_readiness_count_criteria_match_implemented_global_gates() -> None:
    from glyphprobe.analysis.readiness import build_readiness_report

    report = build_readiness_report(_passing_readiness_summary())
    assert report["passed"] == report["total"] == 11

    target = _readiness_check(report, "target_case_count")
    assert target["pass"] is True
    assert target["criterion"] == "At least 16 target prompt records are present."

    random = _readiness_check(report, "random_direction_control")
    assert random["pass"] is True
    assert random["criterion"] == (
        "At least one random-direction control record is present."
    )

    below_target = _passing_readiness_summary()
    below_target["target_case_count"] = 15
    assert _readiness_check(
        build_readiness_report(below_target), "target_case_count"
    )["pass"] is False

    no_random = _passing_readiness_summary()
    no_random["random_control_count"] = 0
    assert _readiness_check(
        build_readiness_report(no_random), "random_direction_control"
    )["pass"] is False


@pytest.mark.parametrize(
    ("missing_key", "check_id"),
    [
        ("wrapper_count", "wrapper_tokenization_control"),
        ("wrapper_token_count_mismatch_count", "wrapper_tokenization_control"),
        ("zero_hook_control_count", "zero_hook_noop"),
        ("zero_hook_max_logit_delta_rms", "zero_hook_noop"),
        ("zero_hook_max_activation_delta_rms", "zero_hook_noop"),
        (
            "median_emoji_perturbation_ratio_max_abs_error",
            "scalar_strength_match",
        ),
    ],
)
def test_readiness_missing_measurements_fail_closed(
    missing_key: str, check_id: str
) -> None:
    from glyphprobe.analysis.readiness import build_readiness_report

    summary = _passing_readiness_summary()
    summary.pop(missing_key)
    assert _readiness_check(build_readiness_report(summary), check_id)["pass"] is False


@pytest.mark.parametrize(
    ("invalid_key", "check_id"),
    [
        ("zero_hook_max_logit_delta_rms", "zero_hook_noop"),
        ("zero_hook_max_activation_delta_rms", "zero_hook_noop"),
        (
            "median_emoji_perturbation_ratio_max_abs_error",
            "scalar_strength_match",
        ),
    ],
)
def test_readiness_nonfinite_measurements_fail_closed(
    invalid_key: str, check_id: str
) -> None:
    from glyphprobe.analysis.readiness import build_readiness_report

    summary = _passing_readiness_summary()
    summary[invalid_key] = float("nan")
    assert _readiness_check(build_readiness_report(summary), check_id)["pass"] is False


def test_readiness_wrapper_control_requires_positive_wrapper_count() -> None:
    from glyphprobe.analysis.readiness import build_readiness_report

    summary = _passing_readiness_summary()
    summary["wrapper_count"] = 0
    assert _readiness_check(
        build_readiness_report(summary), "wrapper_tokenization_control"
    )["pass"] is False
