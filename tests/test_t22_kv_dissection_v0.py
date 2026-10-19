"""Independent synthetic checks for the exploratory T22 adapter; no bank reader."""

from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import t21_glyph_context_path_pilot_v0 as historical  # noqa: E402
import t22_kv_dissection_v0 as t22  # noqa: E402


@pytest.fixture
def tiny_model():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.set_num_threads(1)
    torch.manual_seed(122)
    config = transformers.LlamaConfig(
        vocab_size=64,
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=28,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=64,
        attention_dropout=0.0,
    )
    config._attn_implementation = "eager"
    return torch, transformers.LlamaForCausalLM(config).eval()


def attention_inputs(torch, model, *, batch=1):
    hidden = torch.randn(1, 10, model.config.hidden_size).repeat(batch, 1, 1)
    positions = torch.arange(10).unsqueeze(0).expand(batch, -1)
    embeddings = model.model.rotary_emb(hidden, positions)
    mask = torch.full((10, 10), float("-inf")).triu(diagonal=1)[None, None]
    return hidden, embeddings, mask


def project(module, hidden, embeddings):
    from transformers.models.llama.modeling_llama import apply_rotary_pos_emb

    shape = (*hidden.shape[:-1], -1, module.head_dim)
    query = module.q_proj(hidden).view(shape).transpose(1, 2)
    key = module.k_proj(hidden).view(shape).transpose(1, 2)
    value = module.v_proj(hidden).view(shape).transpose(1, 2)
    query, key = apply_rotary_pos_emb(query, key, *embeddings)
    return query, key, value


def oracle(torch, module, query, key, value, mask):
    """Explicit GQA expansion and attention, independent of HF's eager helper."""
    groups = query.shape[1] // key.shape[1]
    expanded_key = key.repeat_interleave(groups, dim=1)
    expanded_value = value.repeat_interleave(groups, dim=1)
    logits = torch.matmul(query, expanded_key.transpose(-2, -1)) * module.scaling
    weights = torch.softmax(logits + mask, dim=-1, dtype=torch.float32).to(
        query.dtype
    )
    weighted = torch.matmul(weights, expanded_value).transpose(1, 2).contiguous()
    return module.o_proj(weighted.reshape(*weighted.shape[:2], -1)), weights


def row(operation="kv", *, condition="reset_glyph_donor"):
    return {
        "anchor": 21,
        "condition": condition,
        "distance": 4,
        "distance_index": 0,
        "position": 5,
        "glyph_length": 2,
        "donor_slot": 0,
        "operation": operation,
    }


def test_replace_kv_changes_only_requested_component_and_positions(tiny_model):
    torch, _ = tiny_model
    key = torch.arange(160, dtype=torch.float32).reshape(2, 10, 8)
    value = key + 1000
    donor_key, donor_value = key + 10000, value + 20000
    originals = [tensor.clone() for tensor in (key, value, donor_key, donor_value)]
    selected = [0, 3]
    for operation in ("none", "k", "v", "kv"):
        changed_key, changed_value = t22.replace_kv(
            key, value, donor_key, donor_value, selected, operation
        )
        expected_key, expected_value = key.clone(), value.clone()
        if operation in ("k", "kv"):
            expected_key[:, selected] = donor_key[:, selected]
        if operation in ("v", "kv"):
            expected_value[:, selected] = donor_value[:, selected]
        assert torch.equal(changed_key, expected_key)
        assert torch.equal(changed_value, expected_value)
    for original, observed in zip(
        originals, (key, value, donor_key, donor_value), strict=True
    ):
        assert torch.equal(original, observed)


@pytest.mark.parametrize("operation", ["none", "k", "v", "kv"])
def test_same_slot_and_roundtrip_are_exact_noops(tiny_model, operation):
    torch, _ = tiny_model
    key, value = torch.randn(2, 10, 8), torch.randn(2, 10, 8)
    for donor_key, donor_value, roundtrip in (
        (key, value, False),
        (key + 9, value - 11, True),
    ):
        changed_key, changed_value = t22.replace_kv(
            key, value, donor_key, donor_value, [0, 1], operation,
            roundtrip=roundtrip,
        )
        assert torch.equal(changed_key, key)
        assert torch.equal(changed_value, value)


def test_replace_kv_rejects_ambiguous_or_invalid_inputs(tiny_model):
    torch, _ = tiny_model
    key, value = torch.randn(2, 10, 8), torch.randn(2, 10, 8)
    for positions in ([0, 0], [-1], [10], [1.5]):
        with pytest.raises(ValueError):
            t22.replace_kv(key, value, key, value, positions, "kv")
    with pytest.raises(ValueError):
        t22.replace_kv(key, value, key, value, [0], "unknown")
    with pytest.raises(ValueError):
        t22.replace_kv(key, value, key[:, :-1], value, [0], "kv")
    with pytest.raises(ValueError):
        t22.replace_kv(key, value, key.double(), value, [0], "kv")
    with pytest.raises(ValueError):
        t22.replace_kv(key[0], value[0], key[0], value[0], [0], "kv")


def test_stock_path_and_close_restore_exact_forward(tiny_model):
    torch, model = tiny_model
    ids = torch.tensor([[3, 4] + [5] * 8])
    original = model.model.layers[22].self_attn.forward
    with torch.inference_mode():
        expected = model.model(
            input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
        ).last_hidden_state
    controller = t22.AttentionPath(model.model.layers)
    try:
        with torch.inference_mode():
            observed = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        assert torch.equal(expected, observed)
    finally:
        controller.close()
    assert model.model.layers[22].self_attn.forward == original


@pytest.mark.parametrize("condition,selected", [
    ("reset_glyph_donor", [0, 1]),
    ("reset_suffix_donor", [3, 4]),
])
def test_gqa_four_operations_match_oracle_and_return_actual_query_weights(
    tiny_model, condition, selected
):
    torch, model = tiny_model
    module = model.model.layers[22].self_attn
    hidden, embeddings, mask = attention_inputs(torch, model, batch=4)
    operations = ("none", "k", "v", "kv")
    with torch.inference_mode():
        query, key, value = project(module, hidden, embeddings)
        _, donor_keys, donor_values = project(module, hidden[:1] + 2, (
            embeddings[0][:1], embeddings[1][:1]
        ))
        stock_output, stock_weights = module(
            hidden_states=hidden, position_embeddings=embeddings,
            attention_mask=mask, past_key_values=None,
        )
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode = "patch"
        controller.rows = [row(op, condition=condition) for op in operations]
        controller.donor_kv = [{22: (donor_keys[0], donor_values[0])}]
        with torch.inference_mode():
            actual_output, actual_weights = module(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
            for index, operation in enumerate(operations):
                changed_key, changed_value = key[index:index + 1].clone(), value[index:index + 1].clone()
                if operation in ("k", "kv"):
                    changed_key[:, :, selected] = donor_keys[:, :, selected]
                if operation in ("v", "kv"):
                    changed_value[:, :, selected] = donor_values[:, :, selected]
                expected_output, expected_weights = oracle(
                    torch, module, query[index:index + 1], changed_key,
                    changed_value, mask,
                )
                torch.testing.assert_close(
                    actual_output[index, 5], expected_output[0, 5],
                    atol=2e-7, rtol=1e-6,
                )
                torch.testing.assert_close(
                    actual_weights[index, :, 5], expected_weights[0, :, 5],
                    atol=2e-7, rtol=1e-6,
                )
                unselected = torch.arange(10) != 5
                assert torch.equal(actual_output[index, unselected], stock_output[index, unselected])
                assert torch.equal(actual_weights[index, :, unselected], stock_weights[index, :, unselected])
                diagnostic = next(
                    entry for entry in controller.diagnostics
                    if entry["block"] == 22 and entry["row"] == index
                )
                assert diagnostic["operation"] == operation
                assert torch.equal(diagnostic["weights"], actual_weights[index, :, 5].cpu())
                assert torch.equal(diagnostic["baseline_weights"], stock_weights[index, :, 5].cpu())
        assert torch.equal(actual_weights[0], stock_weights[0])
        assert torch.equal(actual_weights[2], stock_weights[2])
        assert not torch.equal(actual_weights[1, :, 5], stock_weights[1, :, 5])
        assert not torch.equal(actual_output[2, 5], stock_output[2, 5])
        assert torch.count_nonzero(actual_weights[:, :, 5, 6:]) == 0
    finally:
        controller.close()


def test_v_only_local_weights_fixed_while_later_query_weights_can_change(tiny_model):
    torch, model = tiny_model
    hidden, embeddings, mask = attention_inputs(torch, model)
    first, second = (model.model.layers[index].self_attn for index in (22, 23))
    with torch.inference_mode():
        reference_output, _ = first(
            hidden_states=hidden, position_embeddings=embeddings,
            attention_mask=mask, past_key_values=None,
        )
        unperturbed_next = hidden + reference_output
        _, unperturbed_weights = second(
            hidden_states=unperturbed_next, position_embeddings=embeddings,
            attention_mask=mask, past_key_values=None,
        )
        donors = {}
        for block, module in ((22, first), (23, second)):
            _, donor_key, donor_value = project(module, hidden * 100, embeddings)
            donors[block] = (donor_key[0], donor_value[0])
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode, controller.rows = "patch", [row("v")]
        controller.donor_kv = [donors]
        with torch.inference_mode():
            changed_output, _ = first(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
            changed_next = hidden + changed_output
            second(
                hidden_states=changed_next, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
            reference_query, _, _ = project(second, unperturbed_next, embeddings)
            changed_query, _, _ = project(second, changed_next, embeddings)
        assert not torch.equal(reference_query[:, :, 5], changed_query[:, :, 5])
        for diagnostic in controller.diagnostics:
            assert torch.equal(diagnostic["weights"], diagnostic["baseline_weights"])
        later = next(entry for entry in controller.diagnostics if entry["block"] == 23)
        assert not torch.equal(later["weights"], unperturbed_weights[0, :, 5].cpu())
    finally:
        controller.close()


@pytest.mark.parametrize("invalid", ["mask", "cache", "training", "geometry"])
def test_adapter_rejects_unsupported_execution(tiny_model, invalid):
    torch, model = tiny_model
    hidden, embeddings, mask = attention_inputs(torch, model)
    module = model.model.layers[22].self_attn
    with torch.inference_mode():
        _, donor_key, donor_value = project(module, hidden + 2, embeddings)
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode, controller.rows = "patch", [row("kv")]
        controller.donor_kv = [{22: (donor_key[0], donor_value[0])}]
        kwargs = {
            "hidden_states": hidden,
            "position_embeddings": embeddings,
            "attention_mask": mask,
            "past_key_values": None,
        }
        if invalid == "mask":
            kwargs["attention_mask"] = None
        elif invalid == "cache":
            kwargs["past_key_values"] = object()
        elif invalid == "training":
            module.train()
        elif invalid == "geometry":
            controller.rows[0]["position"] = 6
        with pytest.raises(ValueError), torch.inference_mode():
            module(**kwargs)
    finally:
        controller.close()


@pytest.mark.parametrize("block", [0, 22])
@pytest.mark.parametrize("mode", ["idle", "capture", "patch"])
@pytest.mark.parametrize("invalid", ["future_nonreadout", "past_bias", "self_masked"])
def test_all_modes_reject_nonstandard_masks_at_every_layer(
    tiny_model, block, mode, invalid
):
    torch, model = tiny_model
    hidden, embeddings, mask = attention_inputs(torch, model)
    mask = mask.clone()
    if invalid == "future_nonreadout":
        # The selected readout's row remains causal. This leak can reach it
        # through an earlier position's K/V at the following block.
        mask[0, 0, 0, 9] = 0
    elif invalid == "past_bias":
        mask[0, 0, 5, 0] = -1
    elif invalid == "self_masked":
        mask[0, 0, 5, 5] = float("-inf")
    module = model.model.layers[block].self_attn
    with torch.inference_mode():
        _, donor_key, donor_value = project(module, hidden + 2, embeddings)
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode, controller.rows = mode, [row("v")]
        controller.donor_kv = [{block: (donor_key[0], donor_value[0])}]
        with pytest.raises(ValueError), torch.inference_mode():
            module(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
    finally:
        controller.close()


@pytest.mark.parametrize("mode", ["idle", "capture", "patch"])
def test_hf_finite_min_causal_mask_is_accepted(tiny_model, mode):
    torch, model = tiny_model
    hidden, embeddings, mask = attention_inputs(torch, model)
    mask = mask.masked_fill(~torch.isfinite(mask), torch.finfo(mask.dtype).min)
    module = model.model.layers[22].self_attn
    with torch.inference_mode():
        expected_output, expected_weights = module(
            hidden_states=hidden, position_embeddings=embeddings,
            attention_mask=mask, past_key_values=None,
        )
        _, donor_key, donor_value = project(module, hidden + 2, embeddings)
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode, controller.rows = mode, [row("v")]
        controller.donor_kv = [{22: (donor_key[0], donor_value[0])}]
        with torch.inference_mode():
            output, weights = module(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
        assert torch.equal(weights, expected_weights)
        if mode == "patch":
            assert not torch.equal(output[:, 5], expected_output[:, 5])
        else:
            assert torch.equal(output, expected_output)
    finally:
        controller.close()


def test_bf16_stock_parity_and_local_v_weight_invariance(tiny_model):
    torch, model = tiny_model
    model.to(dtype=torch.bfloat16)
    ids = torch.tensor([[3, 4] + [5] * 8])
    module = model.model.layers[22].self_attn
    hidden, _, mask = attention_inputs(torch, model)
    hidden = hidden.to(dtype=torch.bfloat16)
    embeddings = model.model.rotary_emb(hidden, torch.arange(10)[None])
    mask = mask.to(dtype=torch.bfloat16)
    with torch.inference_mode():
        stock_final = model.model(
            input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
        ).last_hidden_state
        stock_output, stock_weights = module(
            hidden_states=hidden, position_embeddings=embeddings,
            attention_mask=mask, past_key_values=None,
        )
        _, donor_key, donor_value = project(module, hidden * 20, embeddings)
    controller = t22.AttentionPath(model.model.layers)
    try:
        with torch.inference_mode():
            actual_final = model.model(
                input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False
            ).last_hidden_state
        assert torch.equal(actual_final, stock_final)
        controller.mode, controller.rows = "patch", [row("v")]
        controller.donor_kv = [{22: (donor_key[0], donor_value[0])}]
        with torch.inference_mode():
            output, weights = module(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
        assert torch.equal(weights, stock_weights)
        assert not torch.equal(output[:, 5], stock_output[:, 5])
        diagnostic = controller.diagnostics[-1]
        assert torch.equal(diagnostic["weights"], diagnostic["baseline_weights"])
    finally:
        controller.close()


def test_intervened_readout_cannot_observe_future_tokens(tiny_model):
    torch, model = tiny_model
    hidden, embeddings, mask = attention_inputs(torch, model, batch=2)
    hidden[1, 6:] = torch.randn_like(hidden[1, 6:]) * 100
    module = model.model.layers[22].self_attn
    with torch.inference_mode():
        _, donor_key, donor_value = project(module, hidden[:1] + 2, (
            embeddings[0][:1], embeddings[1][:1]
        ))
    controller = t22.AttentionPath(model.model.layers)
    try:
        controller.mode, controller.rows = "patch", [row("kv"), row("kv")]
        controller.donor_kv = [{22: (donor_key[0], donor_value[0])}]
        with torch.inference_mode():
            output, weights = module(
                hidden_states=hidden, position_embeddings=embeddings,
                attention_mask=mask, past_key_values=None,
            )
        assert torch.equal(output[0, :6], output[1, :6])
        assert torch.equal(weights[0, :, :6], weights[1, :, :6])
        assert torch.count_nonzero(weights[:, :, 5, 6:]) == 0
    finally:
        controller.close()


def historical_layout_run(torch, model, controller_type):
    controller = controller_type(model.model.layers)
    try:
        controller.mode, controller.positions = "capture", [5, 9]
        donor_kv = []
        for prefix in ([6, 7], [10, 11]):
            controller.captured_states, controller.captured_kv = {}, {}
            donor_ids = torch.tensor([prefix + [5] * 8])
            with torch.inference_mode():
                model.model(
                    input_ids=donor_ids,
                    attention_mask=torch.ones_like(donor_ids), use_cache=False,
                )
            donor_kv.append(controller.captured_kv)
        controller.captured_states, controller.captured_kv = {}, {}
        reset_ids = torch.tensor([[8, 9] + [5] * 8])
        with torch.inference_mode():
            model.model(input_ids=reset_ids, attention_mask=torch.ones_like(reset_ids), use_cache=False)
        controller.resets = controller.captured_states
        # Preserve patch_item's exact nesting and omit operation to exercise
        # the new adapter's historical default of joint K/V replacement.
        controller.rows = [
            {
                "distance": distance,
                "distance_index": distance_index,
                "anchor": anchor,
                "condition": condition,
                "donor_slot": donor,
                "glyph_length": 2,
                "position": 2 + distance - 1,
            }
            for distance_index, distance in enumerate((4, 8))
            for anchor in historical.ANCHORS
            for donor in range(2)
            for condition in historical.CONDITIONS
        ]
        assert len(controller.rows) == 88
        controller.donor_kv, controller.mode = donor_kv, "patch"
        ids = torch.tensor([[3, 4] + [5] * 8]).repeat(len(controller.rows), 1)
        with torch.inference_mode():
            observed = model.model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).last_hidden_state
            controller.neutral_path = True
            neutral = model.model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False).last_hidden_state
        for index, configuration in enumerate(controller.rows):
            if configuration["condition"] in (
                "intact", "reset", "no_op", "reset_roundtrip"
            ):
                assert torch.equal(observed[index], neutral[index])
        return observed, neutral
    finally:
        controller.close()


def test_kv_preserves_historical_batch_layout_and_exact_final_states(tiny_model):
    torch, model = tiny_model
    expected, expected_neutral = historical_layout_run(torch, model, historical.AttentionPath)
    observed, neutral = historical_layout_run(torch, model, t22.AttentionPath)
    assert torch.equal(observed, expected)
    assert torch.equal(neutral, expected_neutral)
