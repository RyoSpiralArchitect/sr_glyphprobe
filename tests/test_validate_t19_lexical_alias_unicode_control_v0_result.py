from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_t19_lexical_alias_unicode_control_v0_result.py"
SPEC = importlib.util.spec_from_file_location("validate_t19", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_stratified_permutation_is_a_partition_preserving_bijection() -> None:
    rng = np.random.default_rng(3)
    strata = [[0, 2], [1, 3, 4]]
    mapping = MODULE.stratified_permutation(rng, 5, strata)
    assert sorted(mapping.tolist()) == list(range(5))
    assert set(mapping[[0, 2]]) == {0, 2}
    assert set(mapping[[1, 3, 4]]) == {1, 3, 4}


def test_randomization_reconstructs_a_strong_identity_effect() -> None:
    alias = np.tile(np.arange(8), (24, 1))
    codepoint = np.tile(np.roll(np.arange(8), 1), (24, 1))
    first = MODULE.randomization_test(
        alias,
        codepoint,
        [list(range(8))],
        draws=31,
        seed=9,
    )
    second = MODULE.randomization_test(
        alias,
        codepoint,
        [list(range(8))],
        draws=31,
        seed=9,
    )
    assert first == second
    assert first["observed"] == 1.0
    assert first["p_value_one_sided"] >= 1 / 32


def test_holm_and_partial_conjunction_are_independent_helpers() -> None:
    rows = [
        {"model_role": "a", "model_iut_p": 0.001, "practical_pass": True},
        {"model_role": "b", "model_iut_p": 0.02, "practical_pass": True},
        {"model_role": "c", "model_iut_p": 0.9, "practical_pass": True},
    ]
    adjusted = MODULE.holm(rows, 0.05)
    assert adjusted["a"]["reject"] is True
    assert adjusted["b"]["reject"] is True
    assert adjusted["c"]["reject"] is False
    partial = MODULE.partial_conjunction(
        {"a": 0.001, "b": 0.01, "c": 0.02, "d": 0.9},
        r=3,
    )
    assert partial["rth_p"] == 0.02
    assert partial["p_value"] == 0.04
