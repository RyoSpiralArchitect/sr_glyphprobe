"""Synthetic wording tests; no pretrained model, tokenizer, or GPU."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


runner = module("contextual_emoji_candidate_wording_v0")
analysis = module("summarize_contextual_emoji_candidate_wording_v0")
CONFIG = ROOT / "configs/contextual_emoji_candidate_wording_v0.json"


def design():
    return runner.design(CONFIG)


def ready_spec():
    spec = design()
    spec["status"] = "tokenized_preflight_zero_model_forwards"
    spec["model_artifact"] = runner.read(Path(spec["source_files"]["emoji_spec"]["path"]))["model_artifact"]
    for c in spec["cells"]:
        c.update(status="ready", prompt_token_ids=[1, 2], candidate_token_ids=[3, 4],
                 input_token_ids=[1, 2, 3, 4], prompt_token_count=2, candidate_token_count=2)
    return spec


def synthetic_scores(cells):
    result = deepcopy(cells)
    for row in result:
        diagonal = (row["context"], row["variant"]) in (("p", "a"), ("q", "b"))
        scale = 2 if row.get("carrier_kind") == "word" else 1
        s = row["eta"] * (2 if diagonal else -2) * scale
        value = -20 + s / 2 if row["candidate"] == "a" else -20 - s / 2
        row.update(status="completed", candidate_token_count=2,
                   candidate_token_logprobs=[value / 2, value / 2], sequence_logprob_sum=value)
    return result


def fixture():
    spec = design()
    emoji = runner.base.planned_cells(spec["blocks"])
    word = runner.word.planned_cells(spec["blocks"])
    return spec, synthetic_scores(spec["cells"]), synthetic_scores(emoji), synthetic_scores(word)


def test_fixed_grid_preserves_all_blocks_and_original_orientation():
    spec = design()
    assert spec["model_forwards"] == 0 and not spec["execution_ready"]
    assert len(spec["cells"]) == len({c["cell_id"] for c in spec["cells"]}) == 768
    assert {c["variant"] for c in spec["cells"]} == {"a", "b"}
    assert {c["pair_id"] for c in spec["cells"]} == set(runner.PAIRS[1:])
    assert {c["carrier_kind"] for c in spec["cells"]} == {"emoji", "word"}
    for b in spec["blocks"]:
        for pair in spec["candidate_panel"]["additional_pairs"]:
            choices = runner.candidates(b, spec["candidate_panel"], pair["pair_id"])
            assert choices["a" if b["eta"] == 1 else "b"] == pair["positive"]
    parity = runner.parity_cells(spec)
    assert len(parity) == 384 and all(c["status"] == "ready" for c in parity)
    assert max(len(c["input_token_ids"]) for c in parity) <= 96


def test_synthetic_interaction_and_candidate_stability():
    spec, new, emoji, word = fixture()
    result = analysis.calculate(spec["blocks"], spec["candidate_panel"], new, emoji, word)
    for pair in runner.PAIRS:
        for carrier, expected in (("emoji", 8), ("word", 16)):
            r = result["per_pair"][pair][carrier]
            assert r["full_population_mean_H"] == expected
            assert r["positive_H_blocks"] == r["effect_crossover_blocks"] == r["all_four_aligned_blocks"] == 24
            assert r["aligned_inputs"] == 96
    assert all(r["range_H"] == 0 and r["H_sign_class"] == "all_positive" for r in result["stability"])
    assert all(r["mean_word_minus_emoji"] == 8 for r in result["paired_contrasts"])


def test_missing_cell_preserves_denominator_and_nulls_full_estimate():
    spec, new, emoji, word = fixture()
    new[0].update(status="not_run")
    new[0].pop("candidate_token_logprobs")
    new[0].pop("sequence_logprob_sum")
    result = analysis.calculate(spec["blocks"], spec["candidate_panel"], new, emoji, word)
    assert result["new_cell_status_counts"] == {"not_run": 1, "completed": 767}
    assert result["full_population_equal_pair_mean_H"]["emoji"] is None
    assert result["full_population_equal_pair_mean_H"]["word"] == 16


@pytest.mark.parametrize("mutation", ["duplicate", "sum", "nan", "prompt", "candidate", "eta", "unknown_carrier"])
def test_independent_analysis_rejects_mutations(mutation):
    spec, new, emoji, word = fixture()
    if mutation == "duplicate":
        new[1] = deepcopy(new[0])
    elif mutation == "sum":
        new[0]["sequence_logprob_sum"] += 1
    elif mutation == "nan":
        new[0]["candidate_token_logprobs"][0] = float("nan")
    elif mutation in ("prompt", "candidate", "eta"):
        new[0][mutation] = "changed"
    else:
        new[0]["carrier_kind"] = "unknown"
    with pytest.raises((ValueError, KeyError)):
        analysis.calculate(spec["blocks"], spec["candidate_panel"], new, emoji, word)


def mock_run(tmp_path, monkeypatch, failure=None):
    spec = ready_spec()
    source = tmp_path / "spec.json"
    runner.write(source, spec)
    monkeypatch.setattr(runner, "verify_spec", lambda _: spec)
    policy = spec["config"]["compute_policy"]
    observation = {"free_mib": 8000, "minimum_free_mib_applied": 4096, "own_process_mib": 1000,
                   "observed_peer_pids": policy["allowed_peer_pids"], "allowed_peer_pids": policy["allowed_peer_pids"]}
    monkeypatch.setattr(runner.shared, "guard", lambda *a, **kw: observation)
    released = []
    stager = SimpleNamespace(before_call=lambda: observation, release=lambda: released.append(True))
    torch = SimpleNamespace(cuda=SimpleNamespace(max_memory_allocated=lambda: 1000 * 2**20,
                                                max_memory_reserved=lambda: 1200 * 2**20))
    runtime = runner.read(Path(spec["source_files"]["runtime"]["path"]))
    if failure == "setup":
        def fail(_):
            raise ValueError("synthetic setup failure")
        monkeypatch.setattr(runner, "load_model", fail)
    else:
        monkeypatch.setattr(runner, "load_model", lambda _: (torch, None, runtime, stager))
    calls = []
    def score(_torch, _model, cell, _device):
        calls.append(cell["pair_id"])
        if cell["pair_id"] == "original":
            values = list(cell["reference_logprobs"])
            if failure == "parity":
                values[0] -= 0.01
            return {"candidate_token_logprobs": values, "sequence_logprob_sum": runner.base.math.fsum(values)}
        if failure == "candidate":
            raise RuntimeError("synthetic CUDA failure")
        return {"candidate_token_logprobs": [-1., -1.], "sequence_logprob_sum": -2.}
    monkeypatch.setattr(runner.base, "score_cell", score)
    directory = tmp_path / "run"
    result = runner.run(source, directory)
    return result, directory, source, calls, released


@pytest.mark.parametrize("failure,parity,new,attempts", [
    ("setup", {"not_run": 384}, {"not_run": 768}, 0),
    ("parity", {"failed": 1, "not_run": 383}, {"not_run": 768}, 1),
    ("candidate", {"completed": 384}, {"failed": 1, "not_run": 767}, 385),
    (None, {"completed": 384}, {"completed": 768}, 1152)])
def test_parity_gate_and_full_missingness_receipts(tmp_path, monkeypatch, failure, parity, new, attempts):
    result, directory, source, calls, released = mock_run(tmp_path, monkeypatch, failure)
    assert result["parity_status_counts"] == parity
    assert result["cell_status_counts"] == new
    assert result["total_model_forward_attempts"] == len(calls) == attempts
    assert len((directory / "cells.jsonl").read_text().splitlines()) == 768
    assert len((directory / "parity.jsonl").read_text().splitlines()) == 384
    assert bool(released) == (failure != "setup")
    report = analysis.analyze(directory, source, ROOT)
    assert report["historical_384_cell_exact_parity"] == (failure not in ("setup", "parity"))
    assert report["model_forwards"] == 0  # The analyzer itself never executes models.


def test_new_data_cannot_be_admitted_without_parity(tmp_path, monkeypatch):
    _, directory, source, _, _ = mock_run(tmp_path, monkeypatch)
    receipt = json.loads((directory / "run_completed.json").read_text())
    receipt["parity_passed"] = False
    (directory / "run_completed.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="parity"):
        analysis.analyze(directory, source, ROOT)


def test_nonfinite_and_duplicate_json_rejected():
    for value in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
        with pytest.raises(ValueError):
            analysis.decode(value)


def test_complete_runtime_comparison_uses_saved_json_key_types():
    historical = analysis.read(ROOT / "validation/contextual_emoji_output_pilot_v0/full288/runtime.json")
    current = deepcopy(historical)
    current["model_config"]["id2label"] = {int(k): v for k, v in historical["model_config"]["id2label"].items()}
    assert current != historical
    assert runner.verify_core_runtime(current, historical) == historical
    for key in historical:
        changed = deepcopy(current)
        changed[key] = "changed"
        with pytest.raises(ValueError, match="runtime identity"):
            runner.verify_core_runtime(changed, historical)
    current["model_config"]["id2label"][0] = "changed"
    with pytest.raises(ValueError):
        runner.verify_core_runtime(current, historical)
