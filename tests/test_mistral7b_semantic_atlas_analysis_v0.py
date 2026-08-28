from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ANALYZER = _module(
    "analyze_mistral7b_semantic_atlas_v0",
    ROOT / "scripts" / "analyze_mistral7b_semantic_atlas_v0.py",
)
VALIDATOR = _module(
    "validate_mistral7b_semantic_atlas_capture_v0",
    ROOT / "scripts" / "validate_mistral7b_semantic_atlas_capture_v0.py",
)


def test_capture_validation_grid_and_thresholds_are_fixed() -> None:
    config = yaml.safe_load((ROOT / VALIDATOR.VALIDATION_CONFIG_PATH).read_text())
    assert config["fixed_acquisition_indices"] == [0, 445, 891]
    assert config["view_order"] == ["glyph", "unicode_name", "codepoint_literal"]
    assert config["carrier_order"] == ["article_a", "pipe"]
    assert config["expected_cases"] == 18
    assert config["execution"]["reserve_forward_calls"] == 0
    assert config["thresholds"] == {
        "minimum_vector_cosine": 0.999999,
        "maximum_relative_rms_error": 0.001,
        "maximum_absolute_error": 0.125,
    }


def test_label_ids_are_order_invariant_and_dense() -> None:
    observed = ANALYZER._label_ids(["b", "a", "b", "c"])
    np.testing.assert_array_equal(observed, np.asarray([1, 0, 1, 2]))


@pytest.mark.skipif(not __import__("torch").cuda.is_available(), reason="CUDA-only metric test")
def test_cross_view_metrics_retrieve_identical_geometry() -> None:
    import torch

    rng = np.random.default_rng(7)
    one = rng.normal(size=(12, 16)).astype(np.float32)
    values = np.stack([one, one, np.roll(one, 1, axis=0)], axis=0)
    groups = np.repeat(np.arange(3), 4)
    subgroups = np.arange(12)
    metrics, diagonals = ANALYZER._cell_metrics(
        torch, values, groups, subgroups, k=3
    )
    assert metrics["pairs"]["glyph_name"]["top1_accuracy_forward"] == 1.0
    assert metrics["pairs"]["glyph_name"]["centered_linear_cka"] == pytest.approx(1.0)
    np.testing.assert_allclose(diagonals["glyph_name"], 1.0, atol=1e-6)


def test_analysis_populations_exclude_reserve_and_have_no_decision() -> None:
    assert ANALYZER.POPULATION_ORDER == (
        "calibration_prior_exposed",
        "discovery_unseen",
    )
    source = (ROOT / "scripts" / "analyze_mistral7b_semantic_atlas_v0.py").read_text()
    assert '"scientific_decision_authorized": False' in source
    assert '"confirmatory_status": False' in source
    assert '"reserved_unrun_model_inputs_forwarded": 0' in source
