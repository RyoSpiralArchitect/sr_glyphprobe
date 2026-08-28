from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_mistral7b_semantic_atlas_batch1_v1.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_mistral7b_semantic_atlas_batch1_v1", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_wrapper_binds_passing_bit_exact_capture_validation() -> None:
    path = ROOT / MODULE.VALIDATION_PATH
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert MODULE.batch1.v0._sha256(path) == MODULE.EXPECTED_VALIDATION_SHA256
    assert receipt["status"] == "pass"
    assert receipt["passed_case_count"] == 18
    assert receipt["minimum_exact_element_fraction"] == 1.0
    assert receipt["maximum_absolute_error"] == 0.0
    assert receipt["reserve_forward_calls"] == 0


def test_wrapper_reuses_frozen_analyzer_formulas() -> None:
    assert MODULE.analyzer.POPULATION_ORDER == (
        "calibration_prior_exposed",
        "discovery_unseen",
    )
    assert MODULE.analyzer.PAIR_ORDER == (
        ("glyph_name", 0, 1),
        ("glyph_codepoint", 0, 2),
        ("name_codepoint", 1, 2),
    )
