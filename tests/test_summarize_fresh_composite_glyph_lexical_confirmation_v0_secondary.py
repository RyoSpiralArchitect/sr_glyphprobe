from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import summarize_fresh_composite_glyph_lexical_confirmation_v0_secondary as secondary  # noqa: E402


def test_equal_system_mean_does_not_weight_larger_system_more() -> None:
    rows = []
    for system, count, value in (
        ("modifier", 1, 0.0),
        ("zwj", 7, 0.0),
        ("regional_flag", 2, 0.9),
    ):
        for _ in range(count):
            rows.append(
                {
                    "glyph_system": system,
                    "component": {"contrast": {"metric": value}},
                }
            )
    observed = secondary.equal_system_mean(
        rows, component="component", contrast="contrast", metric="metric"
    )
    assert observed == 0.3


def test_agreement_summary_counts_model_conditional_recurrence() -> None:
    effects = {
        "a": np.array([1.0, 1.0, -1.0, 0.0]),
        "b": np.array([1.0, -1.0, -1.0, 0.0]),
        "c": np.array([1.0, 1.0, 1.0, 0.0]),
        "d": np.array([1.0, 1.0, -1.0, 0.0]),
    }
    result = secondary.agreement_summary(effects, ("a", "b", "c", "d"))
    assert result["positive_in_all_models"] == 1
    assert result["positive_in_at_least_75_percent_of_models"] == 2
    assert result["positive_equal_model_mean"] == 2
    assert result["zero_equal_model_mean"] == 1
    assert result["negative_equal_model_mean"] == 1
