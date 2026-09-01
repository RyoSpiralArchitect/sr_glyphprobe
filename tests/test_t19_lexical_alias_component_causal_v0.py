from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import t19_lexical_alias_component_causal_v0 as causal  # noqa: E402


def test_causal_design_and_tokenizer_preflight_are_fail_closed() -> None:
    design = causal.audit_design()
    assert design["status"] == "causal_design_pass_zero_source_or_eval_forwards"
    assert design["source_rows"] == 128
    assert design["evaluation_rows"] == 192
    assert design["subspace_rank"] == 8
    assert design["causal_go_gate_open"] is False
    assert design["source_model_forwards"] == 0
    assert design["evaluation_model_forwards"] == 0
    receipt = json.loads(
        (ROOT / causal.TOKENIZER_PREFLIGHT_PATH).read_text(encoding="utf-8")
    )
    assert receipt["status"] == "causal_tokenizer_preflight_pass_zero_source_or_eval_forwards"
    assert receipt["t10_reference_surface_sequence_equivalence"] is True
    assert receipt["source_bank"]["rows"] == 128
    assert receipt["evaluation_bank"]["rows"] == 192
    assert receipt["source_model_forwards"] == 0
    assert receipt["evaluation_model_forwards"] == 0


def test_source_subspaces_are_deterministic_orthogonal_and_in_source_span() -> None:
    rng = np.random.default_rng(29)
    glyph = rng.normal(size=(32, 48))
    transform = rng.normal(size=(48, 48))
    alias = glyph @ transform + 0.05 * rng.normal(size=(32, 48))
    learned, control, mean = causal._source_subspace(glyph, alias, rank=4, seed=31)
    learned_again, control_again, mean_again = causal._source_subspace(
        glyph,
        alias,
        rank=4,
        seed=31,
    )
    assert np.array_equal(learned, learned_again)
    assert np.array_equal(control, control_again)
    assert np.array_equal(mean, mean_again)
    assert np.max(np.abs(learned.T @ learned - np.eye(4))) < 2e-6
    assert np.max(np.abs(control.T @ control - np.eye(4))) < 2e-6
    assert np.max(np.abs(learned.T @ control)) < 2e-6
    centered_source = np.concatenate((glyph - glyph.mean(0), alias - alias.mean(0)))
    source_projector = np.linalg.pinv(centered_source) @ centered_source
    assert np.max(np.abs(source_projector @ control - control)) < 2e-5


def test_projection_is_idempotent_and_reconstruction_is_exact() -> None:
    rng = np.random.default_rng(7)
    basis, _ = np.linalg.qr(rng.normal(size=(16, 4)), mode="reduced")
    value = rng.normal(size=16)
    projected = causal._project(value, basis)
    assert np.allclose(causal._project(projected, basis), projected)
    removed = value - projected
    restored = removed + projected
    assert np.allclose(restored, value)
    assert np.max(np.abs(basis.T @ removed)) < 1e-12


def test_retrieval_and_sign_flip_effect_direction() -> None:
    rng = np.random.default_rng(11)
    targets = rng.normal(size=(32, 24))
    distractors = np.roll(targets, 1, axis=0)
    observed, item_values, metrics = causal._retrieval_item_values(
        targets,
        targets,
        distractors,
    )
    assert observed == 1.0
    assert np.all(item_values == 1.0)
    assert metrics == {
        "alias_top1": 1.0,
        "codepoint_top1": 0.0,
        "alias_minus_codepoint_top1": 1.0,
    }
    test = causal._sign_flip(item_values, draws=999, seed=5)
    assert test["observed"] == 1.0
    assert test["p_value_one_sided"] <= 0.01


def test_causal_go_cannot_open_without_observational_admission() -> None:
    if (ROOT / causal.GO_MANIFEST_PATH).exists():
        pytest.skip("Causal go exists after observational admission")
    with pytest.raises((FileNotFoundError, causal.T19CausalError)):
        causal.audit_go()
