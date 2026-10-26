"""Synthetic scoring/state-machine checks; no pretrained models or target banks."""

import importlib.util
import math
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/contextual_emoji_output_pilot_v0.py"
module_spec = importlib.util.spec_from_file_location("contextual_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(pilot)


def block(eta=1):
    return {
        "block_id": "synthetic-01", "family": "synthetic", "eta": eta,
        "design_status": "author_defined_development",
        "interpretation_status": "unvalidated_author_defined",
        "context_p": "First context {emoji}. Answer:",
        "context_q": "Second context {emoji}. Answer:",
        "emoji_a": "A", "emoji_b": "B", "candidate_a": " yes", "candidate_b": " no",
    }


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(char) for char in text]

    def decode(self, values, clean_up_tokenization_spaces=False):
        return "".join(chr(value) for value in values)

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        assert return_offsets_mapping is True
        return {"input_ids": self.encode(text, add_special_tokens),
                "offset_mapping": [(index, index + 1) for index in range(len(text))]}


def encoded_cells():
    return [pilot.encode_cell(CharacterTokenizer(), row, {"max_input_tokens": 512, "max_candidate_tokens": 64})
            for row in pilot.planned_cells([block()])]


def test_complete_grid_contains_twelve_unique_cells_and_absent_controls():
    cells = pilot.planned_cells([block()])
    assert len(cells) == len({row["cell_id"] for row in cells}) == 12
    assert sum(row["variant"] == "absent" for row in cells) == 4
    assert {row["context"] for row in cells} == {"p", "q"}
    assert all("{emoji}" not in row["prompt"] for row in cells)


def test_joint_tokenization_scores_the_entire_candidate():
    cell = encoded_cells()[0]
    assert cell["status"] == "ready"
    assert cell["candidate_token_count"] == len(" yes")
    assert cell["candidate_token_ids"] == [ord(char) for char in " yes"]
    assert cell["input_token_ids"] == cell["prompt_token_ids"] + cell["candidate_token_ids"]
    assert cell["emoji_token_count"] == 1
    assert cell["emoji_tokens_cross_span_boundary"] is False
    assert cell["first_candidate_predictor_position"] == cell["prompt_token_count"] - 1


def test_absent_token_span_is_empty_without_imputing_a_replacement_token():
    absent = next(row for row in encoded_cells() if row["variant"] == "absent")
    assert absent["emoji_token_count"] == 0
    assert absent["emoji_token_positions"] == []
    assert absent["emoji_char_start"] == absent["emoji_char_end"]


def test_overlapping_candidate_prefix_events_are_reported_not_normalized():
    row = block()
    row["candidate_b"] = row["candidate_a"] + " indeed"
    cells = [pilot.encode_cell(CharacterTokenizer(), item, {"max_input_tokens": 512, "max_candidate_tokens": 64})
             for item in pilot.planned_cells([row])]
    diagnostics = pilot.token_diagnostics(cells)
    assert len(diagnostics) == 6
    assert all(item["candidate_a_is_token_prefix_of_b"] for item in diagnostics)
    assert all(item["candidate_event"] == "fixed_continuation_prefix_no_eos_not_normalized_choice" for item in diagnostics)


def test_retokenized_boundary_is_preserved_as_failed_preflight():
    class Retokenizer(CharacterTokenizer):
        def encode(self, text, add_special_tokens=False):
            result = super().encode(text, add_special_tokens)
            return [999] + result[1:] if text.endswith(" yes") else result
    cell = pilot.encode_cell(Retokenizer(), pilot.planned_cells([block()])[0], {"max_input_tokens": 512, "max_candidate_tokens": 64})
    assert cell["status"] == "failed_preflight"
    assert cell["error"] == "candidate_boundary_retokenized_prompt"
    assert cell["cell_id"] == "synthetic-01:p:a:a"


@pytest.mark.parametrize("field,value", [("max_input_tokens", 3), ("max_candidate_tokens", 1)])
def test_token_budget_failure_is_not_silently_dropped(field, value):
    budget = {"max_input_tokens": 512, "max_candidate_tokens": 64, field: value}
    row = pilot.encode_cell(CharacterTokenizer(), pilot.planned_cells([block()])[0], budget)
    assert row["status"] == "failed_preflight"
    assert "budget_exceeded" in row["error"]


def fake_score(cell):
    values = [-0.3] * cell["candidate_token_count"]
    return {"candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values)}


def test_partial_smoke_preserves_all_planned_records():
    emitted = []
    rows, progress = pilot.execute_cells(encoded_cells(), fake_score, emitted.append, 100, limit_cells=3)
    assert rows == emitted and len(rows) == 12
    assert [row["status"] for row in rows[:3]] == ["completed"] * 3
    assert [row["status"] for row in rows[3:]] == ["not_run"] * 9
    assert progress["forward_calls_attempted"] == 3
    summary = pilot.aggregate([block()], rows)
    assert summary["denominator"]["incomplete_blocks"] == 1
    assert summary["complete_block_mean_H"] is None
    assert summary["planned_population_equal_family_mean_H"] is None
    assert summary["family_denominators"]["synthetic"]["full_family_mean_H"] is None


def test_exception_stops_remaining_cells_but_retains_failed_denominator():
    def failure(cell):
        raise RuntimeError("synthetic failure")
    rows, progress = pilot.execute_cells(encoded_cells(), failure, lambda row: None, 100)
    assert rows[0]["status"] == "failed"
    assert all(row["status"] == "not_run" for row in rows[1:])
    assert progress["forward_calls_attempted"] == 1
    assert len(rows) == 12


def test_keyboard_interrupt_is_recorded_without_losing_unexecuted_cells():
    def interrupted(cell):
        raise KeyboardInterrupt()
    rows, progress = pilot.execute_cells(encoded_cells(), interrupted, lambda row: None, 100)
    assert rows[0]["status"] == "failed"
    assert rows[0]["error_type"] == "KeyboardInterrupt"
    assert len(rows) == 12


def test_invalid_or_normalized_scores_fail_closed():
    def normalized(cell):
        value = fake_score(cell)
        value["sequence_logprob_sum"] /= cell["candidate_token_count"]
        return value
    rows, _ = pilot.execute_cells(encoded_cells(), normalized, lambda row: None, 100)
    assert rows[0]["status"] == "failed"
    assert "not the token sum" in rows[0]["error"]


def test_deadline_stops_before_any_new_forward():
    rows, progress = pilot.execute_cells(encoded_cells(), fake_score, lambda row: None, 0)
    assert all(row["status"] == "not_run" for row in rows)
    assert progress["forward_calls_attempted"] == 0


def results_with_scores(scores, eta=1):
    rows = encoded_cells()
    for row in rows:
        row["status"] = "completed"
        row["eta"] = eta
        row["sequence_logprob_sum"] = scores[row["context"]][row["variant"]] - 10 if row["candidate"] == "a" else -10
    return rows


def test_crossed_interaction_sign_and_candidate_counterbalance():
    scores = {"p": {"a": 2, "b": -2, "absent": 0}, "q": {"a": -2, "b": 2, "absent": 0}}
    result = pilot.aggregate([block()], results_with_scores(scores))["blocks"][0]
    assert result["delta_p"] == -4 and result["delta_q"] == 4 and result["H"] == 8
    assert result["intended_delta_crossover"] is True
    reversed_scores = {c: {v: -s for v, s in variants.items()} for c, variants in scores.items()}
    reversed_result = pilot.aggregate([block(-1)], results_with_scores(reversed_scores, -1))["blocks"][0]
    assert reversed_result["H"] == result["H"]
    assert reversed_result["intended_delta_crossover"] is True


def test_positive_interaction_is_not_mislabeled_as_crossover():
    scores = {"p": {"a": 0, "b": -2, "absent": 0}, "q": {"a": 0, "b": -1, "absent": 0}}
    result = pilot.aggregate([block()], results_with_scores(scores))["blocks"][0]
    assert result["H"] == 1
    assert result["intended_delta_crossover"] is False


def test_absent_failure_preserves_main_interaction_but_not_complete_case_mean():
    scores = {"p": {"a": 2, "b": -2, "absent": 0}, "q": {"a": -2, "b": 2, "absent": 0}}
    rows = results_with_scores(scores)
    next(row for row in rows if row["variant"] == "absent")["status"] = "failed"
    summary = pilot.aggregate([block()], rows)
    assert summary["blocks"][0]["H"] == 8
    assert summary["blocks"][0]["status"] == "incomplete"
    assert summary["complete_block_mean_H"] is None
    assert summary["semantic_claim_supported"] is False
    assert summary["route_instrumented"] is False


def test_protected_bank_name_and_symlink_are_rejected_before_read(tmp_path):
    target = tmp_path / "p2_confirmatory_targets_v1.jsonl"
    with pytest.raises(ValueError, match="Protected"):
        pilot.sha256(target)
    link = tmp_path / "innocent.jsonl"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="Protected"):
        pilot.json_read(link)


def test_receipts_never_overwrite(tmp_path):
    path = tmp_path / "receipt.json"
    pilot.json_write(path, {"value": 1})
    with pytest.raises(FileExistsError):
        pilot.json_write(path, {"value": 2})
    assert pilot.json_read(path) == {"value": 1}


@pytest.mark.parametrize("pin", [None, "", "0" * 63, "g" * 64])
def test_config_requires_an_intended_model_artifact_pin(tmp_path, pin):
    value = {
        "protocol_id": pilot.PROTOCOL, "scoring": pilot.SCORE_RULE,
        "model": {"local_files_only": True, "download": False, "dtype": "bf16",
                  "artifact_manifest_sha256": pin},
    }
    path = tmp_path / "config.json"
    pilot.json_write(path, value)
    with pytest.raises(ValueError, match="artifact_manifest_sha256"):
        pilot.config_read(path)


def test_setup_failure_retains_all_cells_and_local_specification(tmp_path, monkeypatch):
    spec = {
        "cells": encoded_cells(), "blocks": [block()], "source": {}, "model_artifact": {},
        "config": {"budget": {"walltime_seconds": 20}},
    }
    source = tmp_path / "spec.json"
    pilot.json_write(source, spec)
    monkeypatch.setattr(pilot, "verify_specification", lambda path: spec)
    def fail_setup(specification, device):
        raise RuntimeError("synthetic setup failure; no model loaded")
    monkeypatch.setattr(pilot, "model_load", fail_setup)
    output = tmp_path / "run"
    final = pilot.run(source, output)
    assert final["status"] == "partial_or_failed"
    assert final["progress"]["forward_calls_attempted"] == 0
    assert final["denominator"]["cell_status_counts"] == {"not_run": 12}
    assert final["denominator"]["planned_cells"] == 12
    assert pilot.json_read(output / "specification.json") == spec
    assert len((output / "cells.jsonl").read_text().splitlines()) == 12
    assert final["route_instrumented"] is False


def test_all_token_scoring_uses_preceding_logits_and_sum_not_mean():
    torch = pytest.importorskip("torch")
    logits = torch.zeros((1, 5, 7), dtype=torch.float32)
    ids = [1, 2, 3, 4, 5]
    logits[0, 1, 3] = 1
    logits[0, 2, 4] = 2
    logits[0, 3, 5] = 3
    logits[0, 4, 0] = 100  # The final position is not a candidate predictor.
    observed = pilot.score_logits(logits, ids, 2)
    expected = [math.log(math.exp(x) / (math.exp(x) + 6)) for x in (1, 2, 3)]
    assert observed == pytest.approx(expected, abs=1e-6)
    assert len(observed) == 3


def test_random_tiny_llama_scores_match_stock_cross_entropy_without_download():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.set_num_threads(1)
    torch.manual_seed(37)
    cfg = transformers.LlamaConfig(vocab_size=32, hidden_size=16, intermediate_size=32,
                                   num_hidden_layers=2, num_attention_heads=2,
                                   num_key_value_heads=1, max_position_embeddings=32)
    cfg._attn_implementation = "eager"
    model = transformers.LlamaForCausalLM(cfg).eval()
    ids = [1, 3, 5, 7, 9, 11]
    inputs = torch.tensor([ids])
    with torch.inference_mode():
        logits = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False).logits
    actual = pilot.score_logits(logits, ids, 3)
    expected = -torch.nn.functional.cross_entropy(logits[0, 2:5].float(), inputs[0, 3:6], reduction="none")
    assert actual == pytest.approx(expected.tolist(), abs=1e-7)
    assert len(actual) == 3
    assert math.fsum(actual) == pytest.approx(float(expected.double().sum()), abs=1e-7)
    prefix_scores = []
    with torch.inference_mode():
        for index in range(3, len(ids)):
            prefix = inputs[:, :index]
            next_logits = model(input_ids=prefix, attention_mask=torch.ones_like(prefix), use_cache=False).logits[0, -1].float()
            prefix_scores.append(float(torch.log_softmax(next_logits, -1)[ids[index]]))
    assert actual == pytest.approx(prefix_scores, abs=1e-6)


def test_main_module_import_is_lazy_and_does_not_load_a_model():
    assert "transformers" not in pilot.__dict__
    assert "torch" not in pilot.__dict__
