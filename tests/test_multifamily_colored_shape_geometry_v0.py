from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_colored_shape_geometry_v0.py"
SPEC = importlib.util.spec_from_file_location("multifamily_colored_shape_geometry_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_frozen_layer_fraction_resolution() -> None:
    assert MODULE.resolve_layers(26, [0.0, 0.25, 0.5, 0.75, 1.0]) == [0, 6, 13, 19, 25]
    assert MODULE.resolve_layers(32, [0.0, 0.25, 0.5, 0.75, 1.0]) == [0, 8, 16, 24, 31]


def test_exact_shape_axis_null_has_unique_identity_for_parallel_fixture() -> None:
    color_basis = np.eye(5, 6, dtype=np.float64) * 2.0
    shape_axis = np.zeros((5, 6), dtype=np.float64)
    shape_axis[:, -1] = 1.0
    circles = color_basis + shape_axis / 2.0
    squares = color_basis - shape_axis / 2.0

    result = MODULE.exhaustive_shape_axis_test(circles, squares)

    assert result["statistic"] == pytest.approx(1.0)
    assert result["permutation_count"] == 120
    assert result["greater_equal_count"] == 1
    assert result["p_greater_equal"] == pytest.approx(1.0 / 120.0)


def test_shape_axis_rejects_a_degenerate_difference() -> None:
    circles = np.eye(5, dtype=np.float64)
    squares = circles.copy()
    with pytest.raises(MODULE.ProtocolError, match="Degenerate"):
        MODULE.shape_axis_statistic(circles, squares)


def test_holm_family_is_fixed_to_two_named_cells() -> None:
    result = MODULE.holm_adjust(
        {"gemma2_2b_4bit": 1.0 / 120.0, "olmo3_7b_bf16": 0.04},
        alpha=0.05,
    )
    assert result["gemma2_2b_4bit"]["adjusted_p"] == pytest.approx(1.0 / 60.0)
    assert result["gemma2_2b_4bit"]["reject"] is True
    assert result["olmo3_7b_bf16"]["adjusted_p"] == pytest.approx(0.04)
    assert result["olmo3_7b_bf16"]["reject"] is True


def test_shared_prefix_diagnostic() -> None:
    assert MODULE.shared_prefix_length([1, 2, 3], [1, 2, 9]) == 2
    assert MODULE.minimum_shared_prefix([[1, 2, 3], [1, 2, 4], [1, 7, 8]]) == 1


def test_scrub_local_paths_removes_model_and_home() -> None:
    model = Path.home() / "private-model"
    value = {
        "model": str(model),
        "nested": [str(Path.home() / "other"), "local/olmo3-1025-7b"],
    }
    scrubbed = MODULE.scrub_local_paths(value, model)
    serialized = repr(scrubbed)
    assert str(Path.home()) not in serialized
    assert "<LOCAL_MODEL_ARTIFACT>" in serialized
    assert "local/olmo3-1025-7b" in serialized


def test_public_freeze_audits_and_forbids_claim_expansion() -> None:
    audit = MODULE.audit_freeze(ROOT)
    assert audit["status"] == "pass"
    assert audit["model_roles"] == ["gemma2_2b_4bit", "olmo3_7b_bf16"]

    _, config, _ = MODULE._load_authority(ROOT)
    assert config["input"]["context_id"] == "raw"
    assert config["primary_endpoint"]["permutations"] == 120
    assert config["primary_endpoint"]["multiplicity"] == "holm"
    assert "activation_intervention" in config["forbidden_actions"]
    assert "protected_target_access" in config["forbidden_actions"]
    assert config["failure_policy"]["prohibit_layer_or_panel_reselection_after_outcomes"] is True
