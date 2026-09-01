"""Fast, model-free contract tests for the T20-C protocol assets."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import t19_lexical_alias_unicode_control_v0 as t19  # noqa: E402
import t19_lexical_alias_component_causal_v0 as t19c  # noqa: E402
import t20_lexical_alias_optimized_subspace_causal_v0 as t20  # noqa: E402
import validate_t20_lexical_alias_optimized_subspace_causal_v0_result as t20v  # noqa: E402


def test_config_matches_frozen_constants() -> None:
    config = t20._config()
    sites = tuple((str(row["site"]), int(row["block_index"])) for row in config["sites"]["order"])
    primary = tuple((str(row["site"]), int(row["block_index"])) for row in config["sites"]["primary"])
    assert sites == t20.SITE_ORDER == t20v.SITE_ORDER
    assert primary == t20.PRIMARY_SITES == t20v.PRIMARY_SITES
    assert int(config["subspace"]["rank"]) == 8
    assert float(config["primary_decision"]["practical_minimum_each"]) == 0.02
    assert float(config["primary_decision"]["ceiling_positive_control"]["informative_minimum"]) == 0.06
    contexts = tuple((str(carrier), int(distance)) for carrier in config["input"]["carrier_order"] for distance in config["input"]["distance_order"])
    assert sorted(contexts) == sorted(t20.CONTEXT_ORDER)
    assert tuple(config["evaluation"]["glyph_condition_order"]) == t20.GLYPH_CONDITION_ORDER
    assert tuple(config["evaluation"]["codepoint_condition_order"]) == t20.CODEPOINT_CONDITION_ORDER


def test_fresh_selection_is_disjoint_and_complete() -> None:
    fresh = t20.fresh_items()
    config = t20._config()
    assert len(fresh) == int(config["population"]["fresh_eval_emoji_items"])
    manifest = t19._selection_manifest()
    t19_codepoints = {str(row["codepoint"]) for key in ("observational_items", "causal_source_items", "causal_eval_items") for row in manifest[key]}
    t19_aliases = {str(row["alias_label"]) for key in ("observational_items", "causal_source_items", "causal_eval_items") for row in manifest[key]}
    fresh_codepoints = [str(row["codepoint"]) for row in fresh]
    fresh_aliases = [str(row["alias_label"]) for row in fresh]
    assert len(set(fresh_codepoints)) == len(fresh)
    assert len(set(fresh_aliases)) == len(fresh)
    assert not set(fresh_codepoints) & t19_codepoints
    assert not set(fresh_aliases) & t19_aliases
    for row in fresh:
        assert t19._words(str(row["canonical_label"])).isdisjoint(t19._words(str(row["alias_label"])))
        assert row["bank_role"] == "t20_causal_fresh_eval"


def test_hits_by_context_reconstructs_identity_advantage() -> None:
    rng = np.random.default_rng(7)
    items, contexts, width = 24, 4, 16
    alias_targets = rng.normal(size=(items, contexts, width))
    codepoint_targets = rng.normal(size=(items, contexts, width))
    queries = alias_targets + 0.05 * rng.normal(size=(items, contexts, width))
    alias_hits, codepoint_hits = t20._hits_by_context(queries, alias_targets, codepoint_targets)
    validator_alias, validator_codepoint = t20v.hits_by_context(queries, alias_targets, codepoint_targets)
    assert np.allclose(alias_hits, validator_alias)
    assert np.allclose(codepoint_hits, validator_codepoint)
    assert float(np.mean(alias_hits)) > 0.9
    assert float(np.mean(codepoint_hits)) < 0.3


def test_validator_rederives_runner_subspace_construction() -> None:
    rng = np.random.default_rng(11)
    glyph = rng.normal(size=(32, 48)).astype(np.float32)
    alias = rng.normal(size=(32, 48)).astype(np.float32)
    learned, random_basis, mean = t19c._source_subspace(glyph, alias, 8, 2026091000)
    validator_learned, validator_random, validator_mean = t20v.rederive_svd_and_random(glyph, alias, 8, 2026091000)
    assert t20v.subspace_distance(learned.astype(np.float64), validator_learned.astype(np.float64)) < 1e-6
    assert t20v.subspace_distance(random_basis.astype(np.float64), validator_random.astype(np.float64)) < 1e-6
    assert float(np.max(np.abs(mean - validator_mean))) < 1e-6


def test_sign_flip_and_bootstrap_are_deterministic() -> None:
    values = np.asarray([0.25, 0.0, 0.25, -0.25, 0.5, 0.25, 0.0, 0.25], dtype=np.float64)
    first = t20v.sign_flip(values, draws=999, seed=123)
    second = t20v.sign_flip(values, draws=999, seed=123)
    assert first == second
    runner = t19c._sign_flip(values, draws=999, seed=123)
    assert first["p_value_one_sided"] == runner["p_value_one_sided"]
    interval = t20v.bootstrap(values, replicates=500, seed=321)
    runner_interval = t19c._bootstrap(values, replicates=500, seed=321)
    assert interval["lower_95"] == runner_interval["lower_95"]


def test_go_cannot_open_without_validated_t19_analysis(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        t20.admit_go(tmp_path, tmp_path / "go.json")


def test_train_split_is_deterministic_partition() -> None:
    train, val = t20._train_split(128, 96)
    train_again, val_again = t20._train_split(128, 96)
    assert np.array_equal(train, train_again)
    assert np.array_equal(val, val_again)
    assert len(train) == 96 and len(val) == 32
    assert not set(train.tolist()) & set(val.tolist())
    assert sorted([*train.tolist(), *val.tolist()]) == list(range(128))
