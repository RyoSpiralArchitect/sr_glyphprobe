from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import t21_path_inference_v0 as stats


def sample():
    rng = np.random.default_rng(731)
    return rng.normal(0.4, 1.0, (150, 5)) + rng.normal(0, 0.3, (150, 1))


def test_simultaneous_reproducible_shift_and_scale():
    x = sample()
    a = stats.simultaneous_lower(x, replicates=1000, seed=3)
    assert a == stats.simultaneous_lower(x, replicates=1000, seed=3)
    b = stats.simultaneous_lower(x + 2, replicates=1000, seed=3)
    c = stats.simultaneous_lower(x * 7, replicates=1000, seed=3)
    for name in stats.NAMES:
        av = a["contrasts"][name]["lower_simultaneous_95"]
        assert b["contrasts"][name]["lower_simultaneous_95"] == pytest.approx(av + 2)
        assert c["contrasts"][name]["lower_simultaneous_95"] == pytest.approx(av * 7)


def test_degenerate_and_nonfinite_fail_closed():
    with pytest.raises(ValueError, match="Degenerate"):
        stats.simultaneous_lower(np.ones((100, 5)), replicates=100)
    x = sample()
    x[0, 0] = np.nan
    with pytest.raises(ValueError, match="Invalid"):
        stats.simultaneous_lower(x, replicates=100)


def test_item_aggregation_and_condition_order():
    x = np.zeros((3, 4, 2, 2, 11))
    x[:, [1, 3], 0, :, 4] = -2
    x[:, [1, 3], 0, :, 6] = -5
    x[:, [1, 3], 0, :, 7] = -1
    out = stats.contrast_matrix(x)
    np.testing.assert_array_equal(out, np.tile([5, 2, 2, 4, -1], (3, 1)))


def test_shared_indices_preserve_identical_endpoint_dependence():
    x = np.repeat(sample()[:, :1], 5, axis=1)
    result = stats.simultaneous_lower(x, replicates=1000)
    lower = [r["lower_simultaneous_95"] for r in result["contrasts"].values()]
    assert max(lower) - min(lower) < 1e-12


def test_planning_is_monotone_in_effect_assumption():
    result = stats.planning_power(sample(), 2.1, cohorts=500)
    p = result["all_five_pass_probability"]
    assert p["pilot_mean"] >= p["pilot_mean_minus_one_pilot_se"]
    assert p["pilot_mean"] >= p["half_pilot_mean"]
