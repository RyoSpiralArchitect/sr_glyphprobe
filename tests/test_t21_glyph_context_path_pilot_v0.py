"""Synthetic and exposed-metadata checks; never open a reserve collection."""

from pathlib import Path
import sys

import numpy as np
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import t21_glyph_context_path_pilot_v0 as pilot  # noqa: E402
import validate_t21_glyph_context_path_pilot_v0 as independent  # noqa: E402


def test_config_has_no_reserve_authority():
    cfg = pilot.config()
    assert cfg["population"]["confirmatory_reserve_access"] is False
    assert (
        cfg["pilot_progression"]["confirmatory_execution_allowed_by_pilot_alone"]
        is False
    )
    assert cfg["intervention"]["conditions"] == list(pilot.CONDITIONS)
    assert cfg["population"]["target_count"] == 384


@pytest.mark.parametrize("length,distance", [(2, 4), (3, 4), (2, 8), (3, 8)])
def test_position_controls_are_disjoint_and_count_matched(length, distance):
    groups = pilot.position_groups(length, distance)
    assert len(groups["glyph"]) == len(groups["suffix"]) == length
    assert not set(groups["glyph"]) & set(groups["suffix"])
    assert max(groups["prefix"]) < length + distance - 1
    for condition in pilot.CONDITIONS:
        assert set(pilot.foreign_positions(condition, length, distance)) <= set(
            groups["prefix"]
        )


def test_distance_eight_avoids_degenerate_restore_controls():
    assert pilot.foreign_positions(
        "reset_prefix_restore_glyph", 3, 4
    ) == pilot.foreign_positions("reset_suffix_donor", 3, 4)
    assert pilot.foreign_positions(
        "reset_prefix_restore_glyph", 3, 8
    ) != pilot.foreign_positions("reset_suffix_donor", 3, 8)
    with pytest.raises(ValueError):
        pilot.position_groups(3, 1)
    with pytest.raises(ValueError):
        pilot.foreign_positions("unknown", 3, 8)


def test_donor_selection_is_deterministic_disjoint_and_length_matched():
    target = [{"codepoint": "A"}, {"codepoint": "B"}]
    tokens = [{"raw": {"glyph": [1, 2]}}, {"raw": {"glyph": [1, 2, 3]}}]
    source = [tokens[0], tokens[1], tokens[0], tokens[1]]
    donors = pilot.choose_donors(target, tokens, source)
    assert donors == pilot.choose_donors(target, tokens, source)
    assert set(donors[0]) == {0, 2}
    assert set(donors[1]) == {1, 3}


def test_continuous_metrics_match_independent_reconstruction():
    rng = np.random.default_rng(24)
    states = rng.normal(size=(5, 2, 2, 11, 16))
    alias, codepoint = rng.normal(size=(5, 16)), rng.normal(size=(5, 16))
    source_alias, source_codepoint = (
        rng.normal(size=(128, 16)),
        rng.normal(size=(128, 16)),
    )
    donors = np.asarray([[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]])
    result = pilot.score_states(
        states, alias, codepoint, source_alias, source_codepoint, donors
    )
    for index in range(5):
        expected = independent.reconstruct_item(
            states[index],
            alias[index],
            codepoint[index],
            source_alias,
            source_codepoint,
            donors[index].tolist(),
        )
        for metric in pilot.METRICS:
            np.testing.assert_allclose(
                result[metric][index], expected[metric], atol=1e-12
            )


def test_equal_vectors_tie_break_to_own_item():
    states = np.ones((2, 2, 2, 11, 8))
    own = np.ones((2, 8))
    source = np.ones((128, 8))
    scores = pilot.score_states(
        states, own, own, source, source, np.asarray([[0, 1], [2, 3]])
    )
    np.testing.assert_allclose(scores["alias_margin"], 0, atol=1e-12)
    assert np.all(scores["alias_top1"] == 1)
    with pytest.raises(ValueError):
        pilot.normalize(np.zeros((2, 8)))


def test_bootstrap_resamples_items_not_contexts():
    values = np.arange(16) / 16
    result = pilot.bootstrap_summary(values, seed=2026092100)
    low, high = independent.interval(values, 2026092100)
    assert result["lower_95"] == low and result["upper_95"] == high


def test_failed_screen_keeps_reserve_closed():
    values = np.zeros((24, 4, 2, 2, 11))
    result = pilot.pilot_decision({"alias_margin_effect": values}, replicates=500)
    assert result["candidate_anchor"] is None
    assert result["reserve_access_allowed"] is False
    assert not any(row["pilot_screen_pass"] for row in result["sites"])


def test_passing_screen_only_permits_a_new_protocol():
    values = np.zeros((24, 4, 2, 2, 11))
    levels = {
        "reset": 1.0,
        "reset_glyph_donor": 0.1,
        "reset_suffix_donor": 0.9,
        "reset_prefix_donor": 0.0,
        "reset_prefix_restore_glyph": 0.8,
        "reset_prefix_restore_suffix": 0.2,
    }
    for condition, level in levels.items():
        values[..., pilot.CONDITIONS.index(condition)] = level
    result = pilot.pilot_decision({"alias_margin_effect": values}, replicates=500)
    assert result["candidate_anchor"] == 21
    assert result["next_step"] == "prepare_separate_prospective_protocol"
    assert result["reserve_access_allowed"] is False
    assert result["confirmatory_result"] is False


def test_receipts_never_overwrite(tmp_path):
    path = tmp_path / "receipt.json"
    pilot.write_json(path, {"complete": True})
    with pytest.raises(FileExistsError):
        pilot.write_json(path, {"complete": False})
    assert pilot.read_json(path) == {"complete": True}


@pytest.fixture
def tiny_model():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.set_num_threads(1)
    torch.manual_seed(121)
    cfg = transformers.LlamaConfig(
        vocab_size=64,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=28,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=64,
        attention_dropout=0.0,
    )
    cfg._attn_implementation = "eager"
    model = transformers.LlamaForCausalLM(cfg).eval()
    return torch, model


def test_attention_adapter_exact_stock_parity(tiny_model):
    torch, model = tiny_model
    ids = torch.tensor([[3, 4] + [5] * 8])
    with torch.inference_mode():
        expected = model.model(
            input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
        ).last_hidden_state
    controller = pilot.AttentionPath(model.model.layers)
    try:
        with torch.inference_mode():
            observed = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        assert torch.equal(expected, observed)
    finally:
        controller.close()


def test_query_only_intervention_and_roundtrip_on_tiny_model(tiny_model):
    torch, model = tiny_model
    controller = pilot.AttentionPath(model.model.layers)
    try:
        controller.mode = "capture"
        controller.positions = [5, 9]
        donor_ids = torch.tensor([[6, 7] + [5] * 8])
        with torch.inference_mode():
            model.model(
                input_ids=donor_ids,
                attention_mask=torch.ones_like(donor_ids),
                use_cache=False,
            )
        donor_kv = controller.captured_kv
        reset_ids = torch.tensor([[8, 9] + [5] * 8])
        controller.captured_states, controller.captured_kv = {}, {}
        with torch.inference_mode():
            model.model(
                input_ids=reset_ids,
                attention_mask=torch.ones_like(reset_ids),
                use_cache=False,
            )
        controller.resets = controller.captured_states
        conditions = [
            "reset",
            "reset_roundtrip",
            "reset_glyph_donor",
            "intact",
            "no_op",
        ]
        controller.rows = [
            {
                "anchor": 21,
                "condition": condition,
                "distance": 4,
                "distance_index": 0,
                "position": 5,
                "glyph_length": 2,
                "donor_slot": 0,
            }
            for condition in conditions
        ]
        controller.donor_kv = [donor_kv]
        controller.mode = "patch"
        ids = torch.tensor([[3, 4] + [5] * 8]).repeat(len(conditions), 1)
        with torch.inference_mode():
            final = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        controller.neutral_path = True
        with torch.inference_mode():
            reference = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        for row in (0, 1, 3, 4):
            assert torch.equal(final[row], reference[row])
        assert torch.equal(final[2, :5], reference[2, :5])
        assert not torch.equal(final[2, 5], reference[2, 5])
        assert controller.offtarget_checks == 12
    finally:
        controller.close()


def test_future_tokens_cannot_affect_readout(tiny_model):
    torch, model = tiny_model
    ids = torch.tensor([[3, 4] + [5] * 8, [3, 4] + [5] * 4 + [11] * 4])
    controller = pilot.AttentionPath(model.model.layers)
    try:
        with torch.inference_mode():
            final = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        assert torch.equal(final[0, :6], final[1, :6])
    finally:
        controller.close()
