"""CPU reacquisition engineering checks; only synthetic model forwards."""

import copy
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import t22_kv_cpu_canary_v0 as cpu


@pytest.fixture
def tiny():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.set_num_threads(1)
    torch.manual_seed(2201)
    config = transformers.LlamaConfig(vocab_size=64, hidden_size=16,
                                     intermediate_size=32, num_hidden_layers=28,
                                     num_attention_heads=4, num_key_value_heads=2,
                                     max_position_embeddings=64, attention_dropout=0.0)
    config._attn_implementation = "eager"
    return torch, transformers.LlamaForCausalLM(config).eval()


def token_row(prefix):
    raw = {"glyph": list(prefix), "codepoint_literal": [12, 13, 14], "alias_label": [15]}
    return {"raw": raw, "sequences": {
        carrier: {view: ids + [carrier_id] * 8 for view, ids in raw.items()}
        for carrier, carrier_id in (("pipe", 5), ("article_a", 9))
    }}


def inputs():
    return token_row([3, 4]), [token_row([6, 7]), token_row([10, 11])]


@pytest.mark.parametrize("dtype", ["float32", "bfloat16"])
def test_cpu_full_item_parity_and_actual_attention_diagnostics(tiny, dtype):
    torch, model = tiny
    model.to(dtype=getattr(torch, dtype))
    tokens, donors = inputs()
    originals = [layer.self_attn.forward for layer in model.model.layers]
    result = cpu.run_item(torch, model, tokens, donors)
    assert all(result["checks"].values())
    assert result["forward_calls"] == 30
    assert result["sequence_forwards"] == 786
    assert result["peak_rss_bytes"] > 0
    arrays = result["arrays"]
    rows = cpu.extension_rows(2)
    for carrier in cpu.CARRIERS:
        assert np.array_equal(arrays[f"{carrier}_legacy_historical"], arrays[f"{carrier}_legacy_t22"])
        assert np.array_equal(arrays[f"{carrier}_legacy_historical_neutral"], arrays[f"{carrier}_legacy_t22_neutral"])
        assert arrays[f"{carrier}_extension"].shape == (16, 16)
        weights = arrays[f"{carrier}_attention_weights"]
        baseline = arrays[f"{carrier}_attention_baseline_weights"]
        assert weights.shape == (2, 6, 16, 4, 10)
        for row_index, row in enumerate(rows):
            if row["operation"] in ("none", "v"):
                assert np.array_equal(weights[0, :, row_index], baseline[0, :, row_index])
            if row["operation"] == "none":
                assert np.array_equal(arrays[f"{carrier}_extension"][row_index], arrays[f"{carrier}_extension_neutral"][row_index])
        assert np.array_equal(weights[1], baseline[1])
        selected = arrays[f"{carrier}_attention_selected_mask"]
        mass = arrays[f"{carrier}_attention_selected_mass"]
        assert not selected[1].any()
        assert np.array_equal(mass, (weights * selected[..., None, :]).sum(axis=-1))
        assert arrays[f"{carrier}_donor_keys"].shape == (2, 6, 2, 10, 4)
    assert all(layer.self_attn.forward == original for layer, original in zip(model.model.layers, originals, strict=True))


def test_full_state_mismatch_blocks_extension_and_restores_hooks(tiny, monkeypatch):
    torch, model = tiny
    tokens, donors = inputs()
    originals = [layer.self_attn.forward for layer in model.model.layers]
    original_patch = cpu._patch

    def corrupt(*args, **kwargs):
        active, neutral = original_patch(*args, **kwargs)
        if isinstance(args[1], cpu.t22.AttentionPath):
            active = active.clone()
            active[0, 0, 0] += 1
        return active, neutral

    monkeypatch.setattr(cpu, "_patch", corrupt)
    with pytest.raises(ValueError, match="full-state equality"):
        cpu.run_item(torch, model, tokens, donors)
    assert all(layer.self_attn.forward == original for layer, original in zip(model.model.layers, originals, strict=True))


@pytest.mark.parametrize("mutation", ["donor_count", "donor_length", "sequence", "training"])
def test_invalid_inputs_fail_before_forward(tiny, mutation, monkeypatch):
    torch, model = tiny
    tokens, donors = inputs()
    if mutation == "donor_count":
        donors.pop()
    elif mutation == "donor_length":
        donors[0]["raw"]["glyph"].append(3)
    elif mutation == "sequence":
        tokens["sequences"]["pipe"]["glyph"].pop()
    else:
        model.train()
    monkeypatch.setattr(model.model, "forward", lambda **kwargs: pytest.fail("Unexpected forward"))
    with pytest.raises(ValueError):
        cpu.run_item(torch, model, tokens, donors)


def test_original_exposed_inputs_and_cpu_specification_are_separate():
    exposed = cpu.exposed_inputs()
    specification = cpu._specification(exposed, exposed["model_artifact"], {"device": "cpu"}, 1)
    assert len(specification["target_tokens"]) == 1
    assert specification["target_tokens"][0] == exposed["target_tokens"][0]
    assert specification["donor_indices"] == exposed["donor_indices"][:1]
    assert len(specification["source_tokens"]) == 128
    assert specification["scientific_result"] is False
    assert specification["historical_gpu_replay"] is False
    assert specification["historical_gpu_acquisition_gate_changed"] is False
    assert len(cpu.legacy_rows(2)) == 88
    assert len(cpu.extension_rows(2)) == 16
    assert "tests/test_t22_kv_cpu_canary_v0.py" in specification["source_sha256"]
    with pytest.raises(ValueError):
        cpu._specification(exposed, {}, {}, 2)


def test_changed_exposed_canary_is_rejected(tmp_path, monkeypatch):
    value = cpu.exposed_inputs()
    value["target_tokens"][0]["raw"]["glyph"][0] += 1
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(value))
    monkeypatch.setattr(cpu.t22, "CANARY_SPEC", changed)
    with pytest.raises(ValueError, match="original exposed canary"):
        cpu.exposed_inputs()


def test_exact_model_manifest_is_required(tmp_path, monkeypatch):
    import glyphprobe.provenance

    expected = {"file_count": 9, "manifest_sha256": "bound"}
    monkeypatch.setattr(glyphprobe.provenance, "model_artifact_receipt", lambda path: {**expected, "extra": True})
    with pytest.raises(ValueError, match="Exact nine-file"):
        cpu._validate_model_artifact(tmp_path, {"model_artifact": expected})


def write_chunk(path, item_index=0):
    path.mkdir()
    tokens, _ = inputs()
    dimensions = {"layers": 28, "hidden_size": 16, "attention_heads": 4, "kv_heads": 2, "head_dim": 4}
    specification = {"protocol_id": cpu.PROTOCOL, "target_count": 1,
                     "target_tokens": [tokens], "model_dimensions": dimensions}
    cpu.historical.write_json(path.parent / "specification.json", specification)
    specification_hash = cpu.historical.sha256(path.parent / "specification.json")
    schema = cpu._array_schema(tokens, dimensions)
    values = {name: np.zeros(meta["shape"], dtype=meta["dtype"]) for name, meta in schema.items()}
    for carrier in cpu.CARRIERS:
        for index, row in enumerate(cpu.extension_rows(2)):
            positions = cpu.historical.foreign_positions(row["condition"], 2, 8)
            values[f"{carrier}_attention_selected_mask"][0, :, index, list(positions)] = True
    np.savez_compressed(path / "states.npz", **values)
    receipt = {"protocol_id": cpu.PROTOCOL, "item_index": item_index,
               "specification_sha256": specification_hash,
               "states_sha256": cpu.historical.sha256(path / "states.npz"),
               "checks": {name: True for name in cpu.ENGINEERING_CHECKS},
               "arrays": schema, "scientific_result": False, "historical_gpu_replay": False,
               "protected_bank_reads": 0, "generation_calls": 0}
    cpu.historical.write_json(path / "receipt.json", receipt)
    return receipt, specification_hash


def test_chunk_resume_checks_hash_identity_and_metadata(tmp_path):
    path = tmp_path / "item_0000"
    expected, specification_hash = write_chunk(path)
    assert cpu.verify_item(path, specification_hash, 0) == expected
    with pytest.raises(ValueError, match="specification"):
        cpu.verify_item(path, "other", 0)
    with pytest.raises(ValueError, match="identity"):
        cpu.verify_item(path, specification_hash, 1)
    with (path / "states.npz").open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError, match="arrays changed"):
        cpu.verify_item(path, specification_hash, 0)


@pytest.mark.parametrize("field", ["checks", "arrays", "scientific_result", "historical_gpu_replay"])
def test_chunk_rejects_partial_checks_schema_or_claim_changes(tmp_path, field):
    path = tmp_path / "item_0000"
    receipt, specification_hash = write_chunk(path)
    if field == "checks":
        receipt[field] = {"passed": True}
    elif field == "arrays":
        receipt[field].pop(next(iter(receipt[field])))
    else:
        receipt[field] = True
    (path / "receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        cpu.verify_item(path, specification_hash, 0)


def test_run_rejects_existing_output_invalid_items_and_model_nested_output(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(FileExistsError):
        cpu.run(tmp_path / "model", output)
    with pytest.raises(ValueError, match="first-item"):
        cpu.run(tmp_path / "model", tmp_path / "new", items=2)
    with pytest.raises(ValueError, match="outside"):
        cpu.run(tmp_path, tmp_path / "nested")
    with pytest.raises(ValueError, match="Threads"):
        cpu.run(tmp_path / "model", tmp_path / "new", threads=0)


def test_changed_source_cannot_complete_or_resume(monkeypatch):
    monkeypatch.setattr(cpu, "source_hashes", lambda: {"runner": "new"})
    with pytest.raises(ValueError, match="source changed"):
        cpu._check_sources({"source_sha256": {"runner": "old"}})


def test_run_real_workflow_with_mocked_pinned_tiny_model(tiny, tmp_path, monkeypatch):
    """Exercise atomic persistence and completed-run rejection without a model fetch."""
    torch, model = tiny
    import transformers

    model.to(dtype=torch.bfloat16)
    tokens, donors = inputs()
    exposed = {"target_tokens": [copy.deepcopy(tokens) for _ in range(8)],
               "source_tokens": donors,
               "donor_indices": [[0, 1] for _ in range(8)],
               "model_artifact": {"total_bytes": 123}}
    monkeypatch.setattr(cpu, "exposed_inputs", lambda: copy.deepcopy(exposed))
    monkeypatch.setattr(cpu, "_runtime", lambda *args: {"device": "cpu", "threads": args[2]})
    monkeypatch.setattr(cpu, "_validate_model_artifact", lambda *args: exposed["model_artifact"])
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", lambda *args, **kwargs: model)
    expected = {"layers": 28, "hidden_size": 16, "parameters": sum(p.numel() for p in model.parameters())}
    monkeypatch.setattr(cpu.historical, "config", lambda: {"model": expected})
    monkeypatch.setattr(cpu, "MODEL_DIMENSIONS", {"layers": 28, "hidden_size": 16, "attention_heads": 4,
                                               "kv_heads": 2, "head_dim": 4})
    with monkeypatch.context() as changed:
        changed.setattr(cpu, "MODEL_DIMENSIONS", {**cpu.MODEL_DIMENSIONS, "head_dim": 8})
        changed.setattr(cpu, "run_item", lambda *args: pytest.fail("Geometry mismatch must fail before forwards"))
        with pytest.raises(ValueError, match="attention geometry"):
            cpu.run(tmp_path / "model", tmp_path / "bad-geometry")
    output = tmp_path / "run"
    result = cpu.run(tmp_path / "model", output)
    assert result["status"] == "cpu_engineering_timing_pilot_complete"
    specification_hash = cpu.historical.sha256(output / "specification.json")
    chunk = cpu.verify_item(output / "item_0000", specification_hash, 0)
    assert all(chunk["checks"].values())
    acquisition = json.loads((output / "acquisition_receipt.json").read_text())
    assert acquisition["scientific_result"] is False
    assert acquisition["historical_gpu_replay"] is False
    assert acquisition["lexical_effect_estimated"] is False
    assert acquisition["forward_calls_across_items"] == 30
    with pytest.raises(ValueError, match="Completed runs"):
        cpu.run(tmp_path / "model", output, resume=True)
    # Interrupted after item persistence: a retry validates and skips that item.
    (output / "acquisition_receipt.json").unlink()
    monkeypatch.setattr(cpu, "run_item", lambda *args: pytest.fail("Completed item was rerun"))
    assert cpu.run(tmp_path / "model", output, resume=True)["status"] == result["status"]
    (output / "acquisition_receipt.json").unlink()
    with pytest.raises(ValueError, match="identical inputs/code/model/runtime"):
        cpu.run(tmp_path / "model", output, threads=2, resume=True)
    with (output / "item_0000/states.npz").open("ab") as handle:
        handle.write(b"changed")
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", lambda *args, **kwargs: pytest.fail("Corrupt output must fail before model load"))
    with pytest.raises(ValueError, match="arrays changed"):
        cpu.run(tmp_path / "model", output, resume=True)
