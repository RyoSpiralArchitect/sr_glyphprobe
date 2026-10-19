"""Independent cosine oracle, paired contrast algebra, stock gate and provenance."""
import contextlib
import csv
import importlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
lex = importlib.import_module("t22_cpu_lexical_canary_v0")


def test_full_129_column_cosines_match_scalar_oracle():
    rng = np.random.default_rng(22002)
    states, own, source = rng.normal(size=(16, 7)), rng.normal(size=7), rng.normal(size=(128, 7))
    result = lex.score_rows(states, own, source, [42, 6])

    def cosine(a, b):
        return math.fsum(float(x) * float(y) for x, y in zip(a, b)) / math.sqrt(
            math.fsum(float(x) ** 2 for x in a) * math.fsum(float(x) ** 2 for x in b))

    expected = np.array([[cosine(q, a) for a in [own, *source]] for q in states])
    np.testing.assert_allclose(result["scores"], expected, rtol=0, atol=4e-16)
    np.testing.assert_allclose(result["alias_margin"], expected[:, 0] - expected[:, 1:].max(axis=-1), atol=5e-16)
    np.testing.assert_array_equal(result["competitor_index"], expected[:, 1:].argmax(axis=-1))
    np.testing.assert_allclose(result["donor_margin"], [expected[i, 0] - expected[i, [43, 7][i % 2]] for i in range(16)], atol=5e-16)


def test_own_first_tie_and_competitor_identity_are_explicit():
    v = np.array([1., 0., 0.])
    result = lex.score_rows(np.tile(v, (16, 1)), v, np.tile(v, (128, 1)), [0, 1])
    assert np.array_equal(result["alias_top1"], np.ones(16))
    assert np.array_equal(result["own_rank"], np.ones(16))
    assert np.array_equal(result["competitor_index"], np.zeros(16))
    assert np.array_equal(result["alias_margin"], np.zeros(16))


def test_positive_scale_does_not_change_cosine_metric():
    rng = np.random.default_rng(22003)
    q, own, source = rng.normal(size=(16, 4)), rng.normal(size=4), rng.normal(size=(128, 4))
    a = lex.score_rows(q, own, source, [0, 127])
    b = lex.score_rows(q * 2, own * 8, source * 4, [0, 127])
    np.testing.assert_array_equal(a["scores"], b["scores"])


@pytest.mark.parametrize("value", [np.zeros((2, 3)), np.full((2, 3), np.nan), np.full((2, 3), np.inf)])
def test_invalid_cosine_vectors_fail(value):
    with pytest.raises(ValueError, match="cosine"):
        lex.normalize(value)


def test_invalid_gallery_or_donor_is_rejected():
    q = np.ones((16, 3))
    with pytest.raises(ValueError, match="geometry"):
        lex.score_rows(q, np.ones(3), np.ones((127, 3)), [0, 1])
    with pytest.raises(ValueError, match="donor"):
        lex.score_rows(q, np.ones(3), np.ones((128, 3)), [0, 128])


def test_same_slot_subtraction_precedes_position_and_context_aggregation():
    neutral = np.arange(8 * 2 * 16, dtype=float).reshape(8, 2, 16) * 100
    effects = np.zeros((8, 2, 4, 2, 2))
    for i in range(8):
        effects[i, :, 1, 0] = -2 - i
        effects[i, :, 1, 1] = -.5
        effects[i, 1, 1, 1] = -.25
    out = lex.item_contrasts(neutral + effects.reshape(8, 2, 16), neutral)
    expected = 1.625 + np.arange(8)
    np.testing.assert_array_equal(out["adjusted_per_item"][:, 1], expected)
    np.testing.assert_array_equal(out["absolute_glyph_decrement_per_item"][:, 1], 2 + np.arange(8))
    assert out["position_adjusted_by_carrier_donor"].shape == (8, 2, 4, 2)
    assert lex.describe(expected)["n_items"] == 8
    assert lex.describe(expected)["mean"] == float(expected.mean())


def test_margin_decomposes_into_own_minus_competitor_after_pairing():
    rng = np.random.default_rng(22004)
    own, comp = rng.normal(size=(2, 8, 2, 16)), rng.normal(size=(2, 8, 2, 16))
    margin = lex.item_contrasts(own[0] - comp[0], own[1] - comp[1])["adjusted_per_item"]
    d_own = lex.item_contrasts(*own)["adjusted_per_item"]
    d_comp = lex.item_contrasts(*comp)["adjusted_per_item"]
    np.testing.assert_allclose(margin, d_own - d_comp, atol=1e-15)


def test_more_contexts_do_not_inflate_item_count():
    with pytest.raises(ValueError, match="eight"):
        lex.describe(np.zeros(32))
    with pytest.raises(ValueError, match="geometry"):
        lex.item_contrasts(np.zeros((8, 4, 16)), np.zeros((8, 4, 16)))


@pytest.fixture
def tiny():
    import torch
    from transformers import LlamaConfig, LlamaForCausalLM
    torch.set_num_threads(1)
    torch.manual_seed(22005)
    cfg = LlamaConfig(vocab_size=64, hidden_size=16, intermediate_size=32,
                      num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2,
                      attention_dropout=0.0)
    cfg._attn_implementation = "eager"
    model = LlamaForCausalLM(cfg).to(dtype=torch.bfloat16).eval()
    tokens = {"sequences": {c: {"glyph": [2, 3] + [token] * 8,
                               "alias_label": [4] + [token] * 8}
                            for c, token in zip(lex.CARRIERS, (5, 6))}}
    expected = {}
    with torch.inference_mode():
        for c in lex.CARRIERS:
            x = torch.tensor([tokens["sequences"][c]["glyph"]])
            expected[f"{c}_stock_hidden"] = model.model(input_ids=x, attention_mask=torch.ones_like(x),
                use_cache=False, return_dict=True).last_hidden_state[0].float().numpy().copy()
    return torch, model, tokens, expected


def test_alias_capture_replays_full_stock_and_preserves_bf16(tiny):
    torch, model, tokens, expected = tiny
    values, calls = lex.acquire_alias_row(torch, model, tokens, expected)
    assert values.shape == (2, 16) and values.dtype == np.float32 and calls == 4
    assert ((values.view(np.uint32) & 65535) == 0).all()
    _, calls = lex.acquire_alias_row(torch, model, tokens)
    assert calls == 2


def test_stock_gate_catches_nonreadout_hidden_mismatch(tiny):
    torch, model, tokens, expected = tiny
    expected["pipe_stock_hidden"][0, 0] += 1
    with pytest.raises(ValueError, match="Full stock glyph replay"):
        lex.acquire_alias_row(torch, model, tokens, expected)


def save_alias_row(path, value, group, index, spec_hash):
    path.mkdir(parents=True)
    np.savez_compressed(path / "states.npz", alias=value)
    lex.write(path / "receipt.json", {"specification_sha256": spec_hash,
        "group": group, "index": index, "forward_calls": 4 if group == "target" else 2,
        "stock_glyph_full_state_replayed": group == "target", "states_sha256": lex.sha(path / "states.npz")})


def test_row_resume_rejects_changed_arrays_and_specification(tmp_path):
    values = np.ones((2, 4), np.float32)
    save_alias_row(tmp_path / "row", values, "target", 0, "fixed")
    lex.verify_row(tmp_path / "row", "fixed", 4, "target", 0)
    with pytest.raises(ValueError, match="identity"):
        lex.verify_row(tmp_path / "row", "different", 4, "target", 0)
    np.savez_compressed(tmp_path / "row/states.npz", alias=values * 2)
    with pytest.raises(ValueError, match="arrays changed"):
        lex.verify_row(tmp_path / "row", "fixed", 4, "target", 0)


@pytest.fixture
def synthetic_analysis(tmp_path, monkeypatch):
    acquisition = tmp_path / "acquisition"
    acquisition.mkdir()
    lex.write(acquisition / "specification.json", {"synthetic": True})
    spec_hash = lex.sha(acquisition / "specification.json")
    spec = {"width": 4, "donor_indices": [[0, 1] for _ in range(8)]}
    monkeypatch.setattr(lex, "load_spec", lambda root: spec)
    monkeypatch.setattr(lex, "source_hashes", lambda: {})
    targets = np.zeros((8, 2, 4), np.float32)
    targets[..., 0] = 1
    sources = np.zeros((128, 2, 4), np.float32)
    sources[..., 1] = 1
    chunks = {}
    for group, values in (("target", targets), ("source", sources)):
        for i, value in enumerate(values):
            path = acquisition / "aliases" / f"{group}_{i:04d}"
            save_alias_row(path, value, group, i, spec_hash)
            chunks[path.name] = lex.sha(path / "receipt.json")
    np.savez_compressed(acquisition / "gallery.npz", target_alias=targets, source_alias=sources)
    lex.write(acquisition / "acquisition_receipt.json", {"status": "alias_acquisition_complete",
        "specification_sha256": spec_hash, "gallery_sha256": lex.sha(acquisition / "gallery.npz"), "chunks": chunks})
    parent = {}
    for carrier in lex.CARRIERS:
        active = np.zeros((16, 4), np.float32)
        active[:, 0] = 1
        for op, glyph in enumerate((0, .5, 1, 1.5)):
            active[op * 4:op * 4 + 2, 1] = glyph
            active[op * 4 + 2:op * 4 + 4, 1] = 0 if op == 0 else .125
        neutral = np.zeros_like(active)
        neutral[:, 0] = 1
        parent[f"{carrier}_extension"] = active
        parent[f"{carrier}_extension_neutral"] = neutral
        for label in ("weights", "baseline_weights"):
            parent[f"{carrier}_attention_{label}"] = np.zeros((2, 6, 16, 2, 10), np.float32)
        for label in ("glyph_mass", "suffix_mass"):
            parent[f"{carrier}_attention_{label}"] = np.zeros((2, 6, 16, 2), np.float32)

    @contextlib.contextmanager
    def parent_arrays(spec, index):
        yield parent

    monkeypatch.setattr(lex, "parent_arrays", parent_arrays)
    return acquisition, tmp_path / "analysis"


def test_full_analysis_pairs_rows_decomposes_and_keeps_all_eight(synthetic_analysis):
    acquisition, output = synthetic_analysis
    result = lex.analyze(acquisition, output)
    assert result["status"] == "descriptive_analysis_complete"
    assert result["target_items"] == 8 and result["scored_rows"] == 512
    assert result["hypothesis_tests"] is False and result["efficacy_screen"] is False
    assert result["max_decomposition_error"] < 1e-12
    suffix_margin = (1 - .125) / math.sqrt(1 + .125 ** 2)
    expected = [0] + [suffix_margin - (1 - x) / math.sqrt(1 + x*x) for x in (.5, 1, 1.5)]
    np.testing.assert_allclose(result["itemwise_adjusted_margin"], np.tile(expected, (8, 1)), atol=2e-16)
    assert result["nonadditivity"]["mean"] == pytest.approx(expected[3] - expected[1] - expected[2])
    with (output / "rows.csv").open() as stream:
        assert len(list(csv.DictReader(stream))) == 512
    with np.load(output / "metrics.npz") as arrays:
        assert arrays["scores"].shape == (8, 2, 2, 16, 129)
    for name, expected_sha in result["artifacts_sha256"].items():
        assert lex.sha(output / name) == expected_sha


def test_changed_gallery_prevents_analysis_output(synthetic_analysis):
    acquisition, output = synthetic_analysis
    with (acquisition / "gallery.npz").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="Gallery changed"):
        lex.analyze(acquisition, output)
    assert not output.exists()


def test_frozen_sources_are_enforced_before_forward(monkeypatch):
    monkeypatch.setattr(lex, "source_hashes", lambda: {"source": "changed"})
    with pytest.raises(ValueError, match="Frozen source"):
        lex.check_sources({"source_sha256": {"source": "original"}})
