from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "t16_operational_semantics_causal_subspace_v0.py"
SPEC = importlib.util.spec_from_file_location("t16_osc", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_design_and_factorial_counts() -> None:
    result = MODULE.audit_design()
    assert result["status"] == "design_pass_zero_t16_model_forwards"
    assert result["model_forwards"] == 0
    assert result["counts"] == {
        "meaning_choice_rows_per_model": 128,
        "congruence_judgment_rows_per_model": 256,
        "causal_target_rows": 128,
        "causal_conditions_per_target_per_site": 21,
        "causal_response_rows": 5376,
    }


def test_behavior_grid_is_counterbalanced() -> None:
    for task, expected in (("meaning_choice", 128), ("congruence_judgment", 256)):
        rows = MODULE._behavior_records(task)
        assert len(rows) == expected
        assert {row["answer_mapping"] for row in rows} == set(MODULE.MAPPINGS)
        for axis in MODULE._axes():
            selected = [row for row in rows if row["axis_id"] == axis["id"]]
            labels = [row["correct_label"] for row in selected]
            assert labels.count("A") == labels.count("B")


def test_causal_condition_roster_and_restoration() -> None:
    width = 16
    full = np.arange(1, width + 1, dtype=np.float32)
    residual = full * np.float32(0.4)
    projection = full - residual
    vectors = {"full": full, "residual": residual, "projection": projection}
    for shift in range(1, 8):
        vectors[f"cross_{shift}"] = np.roll(full, shift)
    metadata, values = MODULE._condition_vectors(vectors, 0.25)
    assert len(metadata) == values.shape[0] == 21
    assert np.array_equal(values[0], np.zeros(width, dtype=np.float32))
    assert {row["condition_kind"] for row in metadata} == {
        "zero",
        "full",
        "residual",
        "projection",
        "cross",
    }


def test_exact_sign_flip_has_256_assignments() -> None:
    values = np.ones(8, dtype=np.float64)
    assert MODULE._exact_sign_flip_p(values) == 1 / 256


def test_repair_changes_only_matched_zero_guard_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "_matched_plain_logits" in source
    assert "len(injections)" in source
    assert "scientific_causal_outcomes_opened_before_repair" in source
