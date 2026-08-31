from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_word_incongruence_interaction_v0.py"
SPEC = importlib.util.spec_from_file_location("t15_interaction_analysis", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _metrics(value: float) -> dict[str, object]:
    return {
        "kl_baseline_to_intervened": value,
        "js_divergence": value,
        "total_variation": value,
        "logit_delta_rms": value,
        "baseline_entropy": 1.0,
        "intervened_entropy": 1.0 + value,
        "argmax_flip": value > 0.5,
    }


def test_endpoint_transforms_and_bootstrap_are_deterministic() -> None:
    row = _metrics(0.25)
    assert MODULE.endpoint_value(row, "entropy_change") == pytest.approx(0.25)
    assert MODULE.endpoint_value(row, "argmax_flip_rate") == 0.0
    values = [index / 100 for index in range(32)]
    first = MODULE.unit_summary(
        values,
        expected_units=32,
        replicates=200,
        seed=11,
    )
    second = MODULE.unit_summary(
        values,
        expected_units=32,
        replicates=200,
        seed=11,
    )
    assert first == second
    assert first["unit_rows"] == 32
    assert first["bootstrap_replicates"] == 200


def test_pairwise_fingerprint_cosine_has_frozen_zero_policy() -> None:
    identical = np.ones((8, 16), dtype=np.float32)
    value, zero_count = MODULE._pairwise_cosine_median(identical)
    assert value == pytest.approx(1.0)
    assert zero_count == 0

    orthogonal = np.eye(8, dtype=np.float32)
    value, zero_count = MODULE._pairwise_cosine_median(orthogonal)
    assert value == pytest.approx(0.0)
    assert zero_count == 0

    orthogonal[0] = 0
    value, zero_count = MODULE._pairwise_cosine_median(orthogonal)
    assert value == pytest.approx(0.0)
    assert zero_count == 1


def test_paired_response_family_retains_all_targets_and_endpoints() -> None:
    left = {}
    right = {}
    for target_index in range(32):
        key = ("synthetic", 6, 0.875, f"target-{target_index:02d}", 0.25, 1)
        left[key] = {endpoint: float(target_index + 1) for endpoint in MODULE.ENDPOINTS}
        right[key] = {endpoint: float(target_index) for endpoint in MODULE.ENDPOINTS}
    result = MODULE._paired_response_family(
        left,
        right,
        family="synthetic",
        estimand="left_minus_right",
    )
    assert len(result["target_estimands"]) == 32 * len(MODULE.ENDPOINTS)
    assert len(result["summary"]) == len(MODULE.ENDPOINTS)
    assert all(row["median"] == pytest.approx(1.0) for row in result["summary"])


def test_depth_and_dose_family_is_complete_without_selection() -> None:
    rows = []
    for role_index, role in enumerate(MODULE.t15.model_roles()):
        for site_index in MODULE.t15.SITE_INDICES:
            for target in MODULE.t15.targets():
                for magnitude in (0.125, 0.25):
                    for sign in (-1, 1):
                        rows.append(
                            {
                                "model": role,
                                "site_index": site_index,
                                "target_id": target["id"],
                                "magnitude": magnitude,
                                "sign": sign,
                                "value": role_index
                                + site_index * 0.01
                                + magnitude
                                + sign * 0.001,
                            }
                        )
    result = MODULE._a6({"target_estimands": rows})
    assert len(result["depth_target_estimands"]) == 4 * 32 * 2
    assert len(result["dose_target_estimands"]) == 4 * 2 * 32 * 2
    assert len(result["depth_summary"]) == 4 * 2
    assert len(result["dose_summary"]) == 4 * 2 * 2


def test_production_open_order_is_fail_closed_in_source() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    function = source[
        source.index("def analyze(") : source.index("def validate_output(")
    ]
    assert function.index("t15.audit_run(run_root)") < function.index("_a0(run_root)")
    assert function.index("t15.audit_run(run_root)") < function.index("_a1(run_root)")
    assert "complete T15-A run" in source


def test_analysis_declares_all_frozen_families_and_claim_limits() -> None:
    config = MODULE.t15._config()["analysis"]
    assert tuple(config["required_complete_families"]) == MODULE.FAMILIES
    assert config["bootstrap_replicates"] == 20_000
    assert config["significance_tests"] == "none_exploratory_descriptive_only"
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"confirmatory_status": False' in source
    assert '"causal_claim_authorized": False' in source
