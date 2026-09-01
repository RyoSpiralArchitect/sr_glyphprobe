from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_t19_lexical_alias_component_causal_v0_result.py"
SPEC = importlib.util.spec_from_file_location("validate_t19_causal", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_retrieval_reconstructs_identity_advantage() -> None:
    rng = np.random.default_rng(13)
    targets = rng.normal(size=(32, 24))
    distractors = np.roll(targets, 1, axis=0)
    values, metrics = MODULE.retrieval_item_values(targets, targets, distractors)
    assert np.all(values == 1.0)
    assert metrics["alias_top1"] == 1.0
    assert metrics["codepoint_top1"] == 0.0
    assert metrics["alias_minus_codepoint_top1"] == 1.0


def test_sign_flip_and_bootstrap_are_deterministic() -> None:
    values = np.ones(32, dtype=np.float64)
    first = MODULE.sign_flip(values, draws=999, seed=4)
    second = MODULE.sign_flip(values, draws=999, seed=4)
    assert first == second
    assert first["observed"] == 1.0
    assert first["p_value_one_sided"] <= 0.01
    interval = MODULE.bootstrap(values, replicates=1_000, seed=5)
    assert interval["lower_95"] == 1.0
    assert interval["upper_95"] == 1.0


def test_bank_hash_is_order_and_content_sensitive() -> None:
    rows = [{"bank_index": 0, "glyph": "a"}, {"bank_index": 1, "glyph": "b"}]
    assert MODULE.bank_hash(rows) == MODULE.bank_hash([dict(row) for row in rows])
    assert MODULE.bank_hash(rows) != MODULE.bank_hash(list(reversed(rows)))
