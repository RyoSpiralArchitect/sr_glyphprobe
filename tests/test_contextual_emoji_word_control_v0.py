"""Synthetic word-control checks; no pretrained downloads or GPU execution."""
import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/contextual_emoji_word_control_v0.py"
module_spec = importlib.util.spec_from_file_location("word_control", SCRIPT)
word = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(word)


def block(eta=1):
    return {"block_id": "synthetic", "family": "synthetic", "eta": eta,
        "context_p": "First goal {emoji}. Answer:", "context_q": "Second goal {emoji}. Answer:",
        "emoji_a": "A", "emoji_b": "B", "candidate_a": " yes", "candidate_b": " no",
        "planned_word_alternatives": {"a": "hot", "b": "cold"},
        "orientation": {"context_p": {"emoji_a": "a" if eta == 1 else "b", "emoji_b": "b" if eta == 1 else "a"},
                        "context_q": {"emoji_a": "b" if eta == 1 else "a", "emoji_b": "a" if eta == 1 else "b"}}}


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(char) for char in text]

    def decode(self, values, clean_up_tokenization_spaces=False):
        return "".join(chr(value) for value in values)

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        assert return_offsets_mapping
        return {"input_ids": self.encode(text), "offset_mapping": [(i, i + 1) for i in range(len(text))]}


def encoded_cells(row=None):
    return [word.encode_cell(CharacterTokenizer(), cell, {"max_input_tokens": 512, "max_candidate_tokens": 64})
            for cell in word.planned_cells([row or block()])]


def scored(scores, eta=1):
    rows = encoded_cells(block(eta))
    for row in rows:
        row["status"] = "completed"
        row["sequence_logprob_sum"] = scores[row["context"]][row["variant"]] - 10 if row["candidate"] == "a" else -10
    return rows


def test_real_grid_is_exactly_192_without_new_absent_or_changed_candidates():
    path = ROOT / "data/contextual_emoji_development_v0.jsonl"
    before = word.sha256(path)
    blocks = word.baseline.load_blocks(path, 24)
    original = copy.deepcopy(blocks)
    cells = word.planned_cells(blocks)
    assert len(cells) == len({cell["cell_id"] for cell in cells}) == 192
    assert {cell["variant"] for cell in cells} == {"a", "b"}
    lookup = {row["block_id"]: row for row in blocks}
    for cell in cells:
        row = lookup[cell["block_id"]]
        assert cell["prompt"] == row[f"context_{cell['context']}"].replace("{emoji}", row["planned_word_alternatives"][cell["variant"]])
        assert cell["continuation"] == row[f"candidate_{cell['candidate']}"]
        assert cell["carrier_kind"] == "word"
    assert blocks == original and word.sha256(path) == before == word.INPUT_SHA
    assert word.sha256(word.BASELINE_PATH) == word.COMPARATOR_SHA["baseline_runner"]


def test_generic_carrier_tokenization_exactly_matches_baseline_algorithm():
    row = block()
    transformed = copy.deepcopy(row)
    transformed.update(emoji_a="hot", emoji_b="cold")
    expected_cells = [cell for cell in word.baseline.planned_cells([transformed]) if cell["variant"] != "absent"]
    actual_cells = encoded_cells(row)
    for source, actual in zip(expected_cells, actual_cells, strict=True):
        expected = word.baseline.encode_cell(CharacterTokenizer(), source, {"max_input_tokens": 512, "max_candidate_tokens": 64})
        for key in ("input_token_ids", "candidate_token_ids", "prompt_token_ids", "prompt", "continuation"):
            assert actual[key] == expected[key]
        assert actual["carrier_token_positions"] == expected["emoji_token_positions"]
        assert not any(key.startswith("emoji_") for key in actual)


def test_boundary_failure_retains_word_cell():
    class Retokenizer(CharacterTokenizer):
        def encode(self, text, add_special_tokens=False):
            result = super().encode(text, add_special_tokens)
            return [999] + result[1:] if text.endswith(" yes") else result
    cell = word.encode_cell(Retokenizer(), word.planned_cells([block()])[0], {"max_input_tokens": 512, "max_candidate_tokens": 64})
    assert cell["status"] == "failed_preflight"
    assert cell["error"] == "candidate_boundary_retokenized_prompt"
    assert cell["carrier_surface"] == "hot"


def test_interaction_crossover_and_absolute_alignment_distinct():
    scores = {"p": {"a": 2, "b": -2}, "q": {"a": -2, "b": 2}}
    result = word.aggregate([block()], scored(scores))
    row = result["blocks"][0]
    assert row["H"] == 8 and row["delta_p"] == -4 and row["delta_q"] == 4
    assert row["intended_delta_crossover"] and row["all_four_author_aligned"]
    assert result["absolute_author_aligned_count"] == 4
    assert result["positive_H_count"] == result["intended_delta_crossover_count"] == 1
    assert result["planned_population_equal_family_mean_H"] == 8
    assert result["denominator"]["planned_cells"] == 8


def test_eta_tracks_candidate_label_reversal_without_counterbalance_claim():
    scores = {"p": {"a": 2, "b": -2}, "q": {"a": -2, "b": 2}}
    reversed_scores = {c: {v: -s for v, s in values.items()} for c, values in scores.items()}
    expected = word.aggregate([block()], scored(scores))
    result = word.aggregate([block(-1)], scored(reversed_scores, -1))
    for key in ("positive_H_count", "absolute_author_aligned_count", "planned_population_equal_family_mean_H"):
        assert result[key] == expected[key]


def test_positive_H_does_not_imply_crossover_or_all_correct():
    result = word.aggregate([block()], scored({"p": {"a": 2, "b": 1}, "q": {"a": 2, "b": 3}}))
    assert result["blocks"][0]["H"] == 2
    assert result["blocks"][0]["intended_delta_crossover"] is True
    assert result["absolute_author_aligned_count"] == 2
    assert result["all_four_author_aligned_block_count"] == 0
    result = word.aggregate([block()], scored({"p": {"a": 3, "b": 1}, "q": {"a": 2, "b": 1}}))
    assert result["positive_H_count"] == 1 and result["intended_delta_crossover_count"] == 0


def test_ties_not_aligned_and_failed_cells_not_imputed():
    rows = scored({"p": {"a": 0, "b": 0}, "q": {"a": 0, "b": 0}})
    result = word.aggregate([block()], rows)
    assert result["absolute_author_aligned_count"] == 0 and result["positive_H_count"] == 0
    rows[0]["status"] = "failed"
    result = word.aggregate([block()], rows)
    assert result["blocks"][0]["H"] is None
    assert result["planned_population_equal_family_mean_H"] is None
    assert result["family_denominators"]["synthetic"]["full_family_mean_H"] is None
    assert result["denominator"]["available_absolute_author_alignment_conditions"] == 3
    assert result["incomplete_population_warning"]


def test_duplicate_or_extra_cells_rejected():
    rows = scored({"p": {"a": 1, "b": 0}, "q": {"a": 0, "b": 1}})
    with pytest.raises(ValueError, match="Duplicate"):
        word.aggregate([block()], rows + rows[:1])
    rows[0]["cell_id"] = "unexpected"
    with pytest.raises(ValueError, match="Unexpected"):
        word.aggregate([block()], rows)


def test_family_population_mean_missing_if_one_block_missing():
    one, two = block(), block()
    two["block_id"], two["family"] = "other", "other"
    rows = scored({"p": {"a": 2, "b": -2}, "q": {"a": -2, "b": 2}})
    result = word.aggregate([one, two], rows)
    assert result["planned_population_equal_family_mean_H"] is None
    assert result["denominator"]["incomplete_blocks"] == 1
    assert result["family_denominators"]["other"]["full_family_mean_H"] is None


@pytest.mark.parametrize("stdout,returncode", [("88\n", 0), ("N/A\n", 0), ("", 1)])
def test_contention_or_unreadable_gpu_query_fails_closed(monkeypatch, stdout, returncode):
    monkeypatch.setattr(word.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=stdout, returncode=returncode))
    with pytest.raises(ValueError):
        word.gpu_guard(own_pid=77)


def test_gpu_guard_permits_only_current_pid_without_any_kill(monkeypatch):
    commands = []
    def observed(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(stdout="77\n", returncode=0)
    monkeypatch.setattr(word.subprocess, "run", observed)
    assert word.gpu_guard(own_pid=77)["other_compute_pids"] == []
    assert len(commands) == 1 and commands[0][0] == "nvidia-smi"


def test_setup_failure_keeps_full_denominator_and_never_scores(tmp_path, monkeypatch):
    spec = {"cells": encoded_cells(), "blocks": [block()], "source": {}, "model_artifact": {}, "comparators": {},
            "config": {"budget": {"walltime_seconds": 20}}}
    source = tmp_path / "spec.json"
    word.json_write(source, spec)
    monkeypatch.setattr(word, "verify_specification", lambda path: spec)
    monkeypatch.setattr(word, "gpu_guard", lambda: (_ for _ in ()).throw(ValueError("other PID")))
    result = word.run(source, tmp_path / "run")
    assert result["status"] == "partial_or_failed"
    assert result["progress"]["forward_calls_attempted"] == 0
    assert result["denominator"]["cell_status_counts"] == {"not_run": 8}
    assert len((tmp_path / "run/cells.jsonl").read_text().splitlines()) == 8


def test_contention_before_next_cell_stops_only_own_acquisition(tmp_path, monkeypatch):
    spec = {"cells": encoded_cells(), "blocks": [block()], "source": {}, "model_artifact": {}, "comparators": {},
            "config": {"budget": {"walltime_seconds": 20}}}
    source = tmp_path / "spec.json"
    word.json_write(source, spec)
    monkeypatch.setattr(word, "verify_specification", lambda path: spec)
    monkeypatch.setattr(word, "model_load", lambda spec: (None, None, {}))
    checks = []
    def guard():
        checks.append(1)
        if len(checks) == 3:
            raise ValueError("other PID detected")
        return {"other_compute_pids": []}
    monkeypatch.setattr(word, "gpu_guard", guard)
    monkeypatch.setattr(word.baseline, "score_cell", lambda torch, model, cell, device:
        {"candidate_token_logprobs": [-1.0] * cell["candidate_token_count"], "sequence_logprob_sum": -float(cell["candidate_token_count"])})
    result = word.run(source, tmp_path / "run")
    assert result["progress"]["forward_calls_attempted"] == 1
    assert result["progress"]["scorer_calls_attempted"] == 2
    assert result["denominator"]["cell_status_counts"] == {"completed": 1, "failed": 1, "not_run": 6}


def test_bound_source_change_rejected_before_config_or_model(tmp_path):
    changed = tmp_path / "source.py"
    changed.write_text("changed")
    spec = {"protocol_id": word.PROTOCOL, "schema_version": 1,
        "status": "development_preflight_zero_model_forwards", "claim_ceiling": word.CLAIM_CEILING,
        "confirmatory": False, "intervention_executed": False, "route_instrumented": False,
        "source": {"files": {"runner": {"path": str(changed), "sha256": "0" * 64}}}}
    path = tmp_path / "spec.json"
    word.json_write(path, spec)
    with pytest.raises(ValueError, match="Bound source changed"):
        word.verify_specification(path)


def test_comparator_change_rejected(tmp_path):
    path = tmp_path / "old.json"
    path.write_text("{}")
    cfg = {"comparators": {key: {"path": str(path), "sha256": pin} for key, pin in word.COMPARATOR_SHA.items()}}
    with pytest.raises(ValueError, match="Comparator changed"):
        word.comparators(cfg)


def test_actual_config_has_no_expanded_budget():
    cfg = word.config_read(ROOT / "configs/contextual_emoji_word_control_v0.json")
    assert cfg["budget"]["max_sequences"] == 192
    assert cfg["inputs"]["sha256"] == word.INPUT_SHA


def test_reused_score_function_remains_exact_baseline_implementation():
    assert word.baseline.score_cell.__name__ == "score_cell"
    assert word.sha256(word.BASELINE_PATH) == word.COMPARATOR_SHA["baseline_runner"]


def test_runtime_identity_compares_actual_baseline_before_forward():
    path = ROOT / "validation/contextual_emoji_output_pilot_v0/full288/runtime.json"
    assert word.sha256(path) == word.COMPARATOR_SHA["baseline_runtime"]
    previous = word.json_read(path)
    word.verify_runtime_identity(copy.deepcopy(previous), previous)
    for key in ("torch", "cuda", "device", "model_forward_source_sha256", "attention_forward_source_sha256"):
        changed = copy.deepcopy(previous)
        changed[key] = "changed"
        with pytest.raises(ValueError, match="runtime identity mismatch"):
            word.verify_runtime_identity(changed, previous)
    changed = copy.deepcopy(previous)
    changed["model_config"]["num_hidden_layers"] += 1
    with pytest.raises(ValueError, match="model dimension mismatch"):
        word.verify_runtime_identity(changed, previous)
