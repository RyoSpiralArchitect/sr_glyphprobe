"""Post-review diagnostics do not alter the original scientific decisions."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_t20_first_best_checkpoint_matches_saved_selection():
    value = json.loads(
        (
            ROOT
            / "validation/t20_lexical_alias_optimized_subspace_causal_v0/results/training_receipt.json"
        ).read_text()
    )
    result = module("audit_t20_checkpoint_selection_v0").audit(value)
    rows = {(r["block_index"], r["site"]): r for r in result["selected_sites"]}
    assert result["histories_reconstructed"] == 27
    assert rows[21, "resid_out"]["selected_step"] == 350
    assert rows[24, "resid_out"]["selected_step"] == 50
    value["training_receipts"][3]["selected_seed"] = 2
    with pytest.raises(ValueError, match="Selected seed"):
        module("audit_t20_checkpoint_selection_v0").audit(value)


def test_t21_components_reconstruct_direct_cosines():
    builder = module("decompose_t21_margin_v0")
    rng = np.random.default_rng(731)
    query = rng.normal(size=(2, 2, 11, 12))
    own = rng.normal(size=(3, 12))
    source = rng.normal(size=(128, 3, 12))
    result = builder.score(query, own, source, [4, 7])
    for anchor in range(2):
        for slot, donor in enumerate([4, 7]):
            for condition in range(11):
                q = query[anchor, slot, condition]
                own_cos = np.dot(q, own[1]) / (
                    np.linalg.norm(q) * np.linalg.norm(own[1])
                )
                source_cos = [
                    np.dot(q, x) / (np.linalg.norm(q) * np.linalg.norm(x))
                    for x in source[:, 1]
                ]
                loc = anchor, slot, condition
                assert result["own_keyword"][loc] == pytest.approx(own_cos)
                assert result["maximum_competitor"][loc] == pytest.approx(
                    max(source_cos)
                )
                assert result["donor_keyword"][loc] == pytest.approx(source_cos[donor])
                assert result["alias_margin"][loc] == pytest.approx(
                    own_cos - max(source_cos)
                )


def test_t21_decomposition_checker_rejects_changed_identity():
    original = json.loads(
        (
            ROOT
            / "validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json"
        ).read_text()
    )
    x = np.array([row["alias_margin_contrasts"] for row in original["rows"]])
    components = {
        "own_keyword": 0.4 * x,
        "maximum_competitor": -0.6 * x,
        "donor_keyword": np.zeros_like(x),
    }
    payload = {
        key: original[key]
        for key in (
            "target_items",
            "anchor",
            "context_indices",
            "donors_averaged_per_item",
            "contrast_order",
        )
    }
    payload.update(
        status="posthoc_descriptive_decomposition",
        new_significance_tests=0,
        new_model_forwards=0,
    )
    payload["rows"] = [
        {
            "item_index": i,
            **{key: value[i].tolist() for key, value in components.items()},
        }
        for i in range(195)
    ]
    payload["means"] = {
        name: {
            key: float(value[:, j].mean())
            for key, value in {**components, "margin": x}.items()
        }
        for j, name in enumerate(original["contrast_order"])
    }
    validator = module("validate_t21_margin_decomposition_v0")
    assert validator.verify(payload, original)["status"] == "pass"
    changed = copy.deepcopy(payload)
    changed["rows"][0]["own_keyword"][0] += 0.01
    with pytest.raises(ValueError, match="reconstruction"):
        validator.verify(changed, original)
    changed = copy.deepcopy(payload)
    changed["rows"][0]["item_index"] = 1
    with pytest.raises(ValueError, match="Duplicate"):
        validator.verify(changed, original)


def test_t19_conditional_null_depends_on_prediction_strata():
    replay = module("validate_t19_compact_predictions_v0")
    # All predictions stay in each target's two-item stratum: null hit rate 1/2.
    inside = np.tile([1, 0, 3, 2], (24, 1))
    assert replay.exact_null_keyword_rate(inside, [[0, 1], [2, 3]]) == 0.5
    # All predictions leave the target's stratum: null hit rate zero, not 1/4.
    outside = np.tile([2, 3, 0, 1], (24, 1))
    assert replay.exact_null_keyword_rate(outside, [[0, 1], [2, 3]]) == 0
    assert replay.exact_null_keyword_rate(outside, [[0, 1, 2, 3]]) == 0.25
    with pytest.raises(ValueError, match="partition"):
        replay.validate_strata([[0, 1], [1, 3]], 4)


def test_t19_paper_matched_counts_match_all_nine_compact_cells():
    compact = json.loads(
        (
            ROOT
            / "validation/t19_lexical_alias_unicode_control_v0/compact_v0/predictions.json"
        ).read_text()
    )
    replay = module("validate_t19_compact_predictions_v0")
    assert compact["role_order"] == replay.ROLES
    counts = []
    for model in compact["models"]:
        cell = model["cells"]["emoji"]["matched"]
        n = len(cell["global_item_indices"])
        replay.validate_predictions(cell["predictions"], n)
        replay.validate_strata(cell["strata"], n)
        counts.append(n)
    assert counts == [35, 31, 35, 41, 51, 31, 35, 35, 38]
    manuscript = (ROOT / "paper/main.tex").read_text()
    assert "$n=31$--$51$" in manuscript
    assert "Gemma 2 2B IT & 51 &" in manuscript


def test_paper_decomposition_retains_all_means_and_posthoc_scope():
    payload = json.loads(
        (ROOT / "validation/t21_margin_decomposition_v0/decomposition.json").read_text()
    )
    manuscript = (ROOT / "paper/main.tex").read_text()
    section = manuscript.split(r"\paragraph{Post-hoc margin decomposition.}", 1)[1]
    section = section.split(r"\section{Execution, licensing", 1)[0]
    assert "No new significance" in section
    assert "bounds above apply only to the" in section
    assert len(payload["means"]) == 5
    for means in payload["means"].values():
        for value in means.values():
            assert f"{value:+.6f}" in section


@pytest.mark.parametrize("value", [-1, 55, 1.5])
def test_t19_invalid_prediction_indices_are_rejected(value):
    replay = module("validate_t19_compact_predictions_v0")
    predictions = {
        key: np.zeros((24, 55), dtype=int).tolist() for key in replay.TARGETS
    }
    predictions["alias"][0][0] = value
    with pytest.raises(ValueError, match="Prediction"):
        replay.validate_predictions(predictions, 55)
