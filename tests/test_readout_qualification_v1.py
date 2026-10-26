"""CPU-only mocks; these tests never load a real tokenizer/model or use CUDA."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("readout_qualification_test", ROOT / "scripts/readout_qualification_v1.py")
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)


class Tokenizer:
    def encode(self, text, add_special_tokens=True):
        assert add_special_tokens is True
        if "\nAnswer:" in text:
            prompt, answer = text.rsplit("\nAnswer:", 1)
            # All artificial prompt identities stay short, unlike character encoding.
            ids = [1, int(hashlib.sha256(prompt.encode()).hexdigest()[:6], 16) % 100000, 2]
            tails = {"": [], " Yes": [3], " No": [4], " A": [5], " B": [6],
                     " The answer is yes.": [7, 8, 9, 10], " The answer is no.": [7, 8, 11, 10]}
            return ids + tails[answer]
        raise AssertionError("Unexpected tokenizer input")


def mock_score(case, event, correct=True, tie=False):
    candidate = event["method"][-1]
    n = case["shared_prefix_token_count"]
    length = len(case["candidates"][candidate]["candidate_token_ids"])
    expected = case.get("expected_yes", True)
    winner = "a" if expected else "b"
    if not correct:
        winner = "b" if winner == "a" else "a"
    values = [-1.0] * length
    values[n] = -1.0 if tie or candidate == winner else -2.0
    geometry = event["geometry"]
    result = {"candidate_token_logprobs": values, "sequence_logprob_sum": sum(values),
              "shared_prediction_logits_sha256": "a" * 64, "shared_prediction_logits_shape": [n, 128256],
              "shared_prediction_logits_dtype": "float32", "logits_hash_byte_order": "little",
              "normalization_rectangle_shape": [geometry["normalization_stop"]-geometry["normalization_start"], 128256],
              "elapsed_seconds": 0.0}
    if event["phase"] == "qualification":
        result.update(causal_prediction_logits_sha256="b" * 64, causal_prediction_logits_shape=[n+1, 128256],
                      causal_prediction_logits_dtype="float32")
    return result


@pytest.fixture(scope="module")
def spec():
    inputs = q.tokenize_inventory(Tokenizer())
    sentinels = []
    for i in range(8):
        case = copy.deepcopy(inputs[i * 4])
        case["input_id"] = f"sentinel_{i}"
        case["expected_scores"] = {}
        for method in ("padded_a", "padded_b"):
            event = {"method": method, "phase": "begin", "geometry": q.prefix.call_geometry(case, method)}
            case["expected_scores"][method] = mock_score(case, event)
        sentinels.append(case)
    return {"inputs": inputs, "sentinels": sentinels}


def records(spec, modify=None):
    cases = {r["input_id"]: r for r in spec["inputs"] + spec["sentinels"]}
    result = []
    for event in q.plans(spec):
        case = cases[event["input_id"]]
        options = modify(case, event) if modify else {}
        result.append({**event, "status": "completed", "forward_attempted": True, **mock_score(case, event, **options)})
    return result


def test_inventory_balanced_and_new():
    rows = q.inventory()
    assert len(rows) == 2304
    assert len({r["input_id"] for r in rows}) == 2304
    roots = q.roots()
    assert len(roots) == 32
    assert q.Counter(r["split"] for r in roots) == {"development": 16, "reserved_check": 16}
    assert set(q.Counter(r["family"] for r in roots).values()) == {8}
    assert len({r["positive_proposition"] for r in roots}) == 32
    assert {r["family"] for r in roots if r["split"] == "development"}.isdisjoint(
        {r["family"] for r in roots if r["split"] == "reserved_check"})


def test_unknown_does_not_support_either_proposition():
    for row in q.inventory():
        if row["report_state"] == "unknown":
            assert row["proposition_supported"] is False
            assert row["expected_yes"] == (row["question_form"] == "nested_false")
        else:
            assert row["proposition_supported"] == (row["report_state"] == row["query_polarity"])


def test_negative_report_is_positive_evidence_for_negative_proposition():
    rows = [r for r in q.inventory() if r["report_state"] == "negative" and r["query_polarity"] == "negative"]
    assert len(rows) == 384
    assert all(r["expected_yes"] == (r["question_form"] != "nested_false") for r in rows)


def test_letter_order_fixed_and_candidate_semantics_reversed():
    normal, a = q.response_format("letters_normal")
    reverse, b = q.response_format("letters_reversed")
    assert normal.index("A means") < normal.index("B means")
    assert reverse.index("A means") < reverse.index("B means")
    assert a == {"a": " A", "b": " B"}
    assert b == {"a": " B", "b": " A"}


def test_tokenization_allows_empty_shared_but_requires_predictor(spec):
    q.validate_inputs(spec["inputs"])
    minimal = next(r for r in spec["inputs"] if r["answer_format"] == "minimal")
    assert minimal["shared_prefix_token_count"] == 0
    assert minimal["causal_predictor_token_count"] == 1
    assert q.plans(spec)[16]["phase"] == "qualification"
    assert len(q.plans(spec)) == 4640


def test_tokenization_boundary_failure():
    class Bad(Tokenizer):
        def encode(self, text, add_special_tokens=True):
            result = super().encode(text, add_special_tokens)
            if not text.endswith("\nAnswer:"):
                result[0] += 1
            return result
    with pytest.raises(ValueError, match="boundary"):
        q.tokenize_inventory(Bad())


@pytest.mark.parametrize("field", ["prompt", "expected_yes", "question_form"])
def test_design_tampering_rejected(spec, field):
    inputs = copy.deepcopy(spec["inputs"])
    inputs[0][field] = "tampered"
    with pytest.raises(ValueError, match="prompt/design"):
        q.validate_inputs(inputs)


def test_token_boundary_and_span_tampering_rejected(spec):
    inputs = copy.deepcopy(spec["inputs"])
    inputs[0]["causal_predictor_token_count"] += 1
    with pytest.raises(ValueError, match="predictor span"):
        q.validate_inputs(inputs)


def test_all_correct_passes_primary_and_independent_label_gate(spec):
    analysis = q.analyze(spec, records(spec))
    assert analysis["numerical_gate_passed"]
    assert analysis["primary_qualification_passed"]
    assert analysis["label_robustness_passed"]
    assert analysis["primary"]["correct"] == 96
    assert analysis["primary"]["all_correct_roots"] == 16
    assert analysis["primary"]["constant_no_accuracy"] == 2/3
    assert analysis["label_robustness"]["correct"] == 192
    assert analysis["nested_false_direct_polarity_consistency"]["consistent"] == 768
    assert analysis["label_mapping_consistency"]["consistent"] == 576


@pytest.mark.parametrize("failure", ["wrong", "tie"])
def test_one_primary_failure_fails_strictly(spec, failure):
    target = next(r["input_id"] for r in spec["inputs"] if r["split"] == "reserved_check" and
                  r["question_form"] == "direct" and r["answer_format"] == "minimal")
    def modify(case, event):
        return ({"correct": False} if failure == "wrong" else {"tie": True}) if case["input_id"] == target else {}
    analysis = q.analyze(spec, records(spec, modify))
    assert analysis["numerical_gate_passed"]
    assert not analysis["primary_qualification_passed"]
    assert analysis["primary"]["correct"] == 95
    assert analysis["primary"]["all_correct_roots"] == 15
    assert analysis["label_robustness_passed"]


def test_labels_cannot_replace_primary_and_primary_does_not_imply_labels(spec):
    def modify(case, event):
        return {"correct": False} if case.get("answer_format") == "letters_reversed" and event["phase"] == "qualification" else {}
    analysis = q.analyze(spec, records(spec, modify))
    assert analysis["primary_qualification_passed"]
    assert not analysis["label_robustness_passed"]
    assert analysis["label_robustness"]["correct"] == 96


def test_empty_shared_prefix_cannot_pass_vacuously(spec):
    rows = records(spec)
    target = next(row for row in rows if row["phase"] == "qualification" and row["method"] == "padded_b" and
                  row["geometry"]["shared_prefix_token_count"] == 0)
    target["causal_prediction_logits_sha256"] = "c" * 64
    analysis = q.analyze(spec, rows)
    assert not analysis["numerical_gate_passed"]
    pair = next(p for p in analysis["pairs"] if p["input_id"] == target["input_id"])
    assert pair["shared_prefix_logprobs_exact"] is True
    assert pair["causal_predictors_exact"] is False


def test_missing_predictor_receipt_rejected(spec):
    rows = records(spec)
    del rows[16]["causal_prediction_logits_sha256"]
    with pytest.raises(KeyError):
        q.analyze(spec, rows)


def test_decomposition_raw_scores_preserved(spec):
    analysis = q.analyze(spec, records(spec))
    assert all(p["s_shared_prefix"] == 0 and p["decomposition_residual"] == 0 for p in analysis["pairs"])
    assert all(p["s_yes_minus_no"] == p["s_first_divergent_token"] for p in analysis["pairs"])
    assert all(len(p["candidate_token_logprobs"]["yes"]) >= 1 for p in analysis["pairs"])


def test_peer_before_forward_keeps_entire_missing_denominator(spec):
    emitted = []
    def refuse(_):
        raise ValueError("Other GPU PID present")
    rows, attempts, error = q.execute(spec, mock_score, refuse, lambda _: None, emitted.append, lambda: None)
    assert len(rows) == len(emitted) == 4640 and attempts == 0
    assert all(r["status"] == "not_run" for r in rows)
    analysis = q.analyze(spec, rows)
    assert analysis["completed_pairs"] == 0
    assert analysis["primary"]["planned_pairs"] == analysis["primary"]["missing_pairs"] == 96
    assert not analysis["primary_qualification_passed"]
    assert "Other GPU PID" in error


def test_post_forward_contention_preserves_completed_row_but_fails_gate(spec):
    def refuse(_):
        raise ValueError("peer after forward")
    rows, attempts, _ = q.execute(spec, mock_score, lambda _: None, refuse, lambda _: None, lambda: None)
    assert attempts == 1 and rows[0]["status"] == "completed"
    assert "boundary_error_after_score" in rows[0]
    assert all(r["status"] == "not_run" for r in rows[1:])
    assert not q.analyze(spec, rows)["numerical_gate_passed"]


def test_after_guard_runs_when_scorer_raises(spec):
    calls = []
    def crash(*_):
        raise RuntimeError("score failure")
    rows, attempts, _ = q.execute(spec, crash, lambda _: None, calls.append, lambda _: None, lambda: None)
    assert attempts == 1 and len(calls) == 1 and rows[0]["status"] == "failed"
    assert len(rows) == 4640
    assert not q.analyze(spec, rows)["numerical_gate_passed"]


@pytest.mark.parametrize("signum", [signal.SIGALRM, signal.SIGINT])
def test_interrupt_during_emission_preserves_exactly_all_planned_rows(spec, signum):
    emitted = []
    original = signal.getsignal(signum)
    def emit(row):
        # Real pending POSIX signal, not an artificial emit exception: it may
        # only take effect after the persisted row and in-memory append agree.
        if not emitted:
            signal.raise_signal(signum)
        emitted.append(json.loads(json.dumps(row)))
    rows, attempts, error = q.execute(spec, mock_score, lambda _: None, lambda _: None, emit, lambda: None)
    assert rows == emitted
    assert len(rows) == 4640 and len({r["event_id"] for r in rows}) == 4640
    assert attempts == 1 and rows[0]["status"] == "completed"
    assert all(r["status"] == "not_run" for r in rows[1:])
    assert error and ("TimeoutError" if signum == signal.SIGALRM else "KeyboardInterrupt") in error
    assert signal.getsignal(signum) == original
    assert not q.analyze(spec, rows)["numerical_gate_passed"]


def test_interrupt_in_forward_is_orderly_and_retains_after_guard(spec):
    after = []
    def score(*_):
        signal.raise_signal(signal.SIGINT)
        raise AssertionError("Signal should interrupt the forward")
    rows, attempts, error = q.execute(spec, score, lambda _: None, after.append, lambda _: None, lambda: None)
    assert len(rows) == 4640 and attempts == 1 and len(after) == 1
    assert rows[0]["status"] == "failed" and all(r["status"] == "not_run" for r in rows[1:])
    assert "KeyboardInterrupt" in error


def test_missing_row_or_geometry_tamper_rejected(spec):
    rows = records(spec)
    with pytest.raises(ValueError, match="Missing planned"):
        q.analyze(spec, rows[:-1])
    rows[16]["geometry"] = dict(rows[16]["geometry"], total_length=999)
    with pytest.raises(ValueError, match="geometry"):
        q.analyze(spec, rows)


def test_changed_sentinel_fails_gate(spec):
    rows = records(spec)
    rows[-1]["shared_prediction_logits_sha256"] = "d" * 64
    analysis = q.analyze(spec, rows)
    assert not analysis["sentinels_exact"]
    assert not analysis["primary_qualification_passed"]


def test_external_specification_pin_and_no_overwrite(tmp_path):
    path = tmp_path / "spec.json"
    q.write(path, {"example": 1})
    with pytest.raises(ValueError, match="Externally pinned"):
        q.verify(path, "0" * 64)
    with pytest.raises(FileExistsError):
        q.write(path, {})
    with pytest.raises(ValueError, match="externally retained"):
        q.run(path, tmp_path / "out", None)
    assert not (tmp_path / "out").exists()


def test_primary_metadata_fixed_and_source_docs_pinned():
    assert q.PRIMARY["required_correct"] == 96
    assert q.LABEL_GATE["required_correct"] == 192
    assert q.MAX_FORWARDS == 4640 and q.WALL_SECONDS == 1800
    pins = q.sources()
    assert "docs/READOUT_QUALIFICATION_V1.md" in pins
    assert "docs/READOUT_QUALIFICATION_V1.ja.md" in pins


def test_geometry_same_even_for_unequal_candidate_lengths(spec):
    case = copy.deepcopy(spec["inputs"][1])
    case["candidates"]["b"]["input_token_ids"].append(12)
    case["candidates"]["b"]["candidate_token_ids"].append(12)
    a, b = [q.prefix.call_geometry(case, method) for method in ("padded_a", "padded_b")]
    assert a["total_length"] == b["total_length"]
    assert a["normalization_start"] == b["normalization_start"]
    assert a["normalization_stop"] == b["normalization_stop"]
    assert a["attention_mask"][-1] == 0 and b["attention_mask"][-1] == 1


def test_cpu_tensor_score_checks_first_predictor_without_extra_forward(spec):
    torch = pytest.importorskip("torch")
    calls = []
    class Model:
        def __call__(self, input_ids, attention_mask, position_ids, use_cache):
            calls.append((input_ids.clone(), attention_mask.clone(), position_ids.clone(), use_cache))
            length = input_ids.shape[1]
            # A causal toy function: position t depends only on IDs at/before t.
            cumulative = input_ids.cumsum(dim=1).float()
            logits = cumulative[:, :, None] * torch.arange(16).float()[None, None, :] / 100000.0
            return SimpleNamespace(logits=logits)
    case = spec["inputs"][1]
    scores = []
    for method in ("padded_a", "padded_b"):
        event = {"method": method, "phase": "qualification", "geometry": q.prefix.call_geometry(case, method)}
        score = q.score_call(torch, Model(), None, case, event, "cpu")
        q.validate_score(score, event)
        scores.append(score)
    assert len(calls) == 2
    assert scores[0]["causal_prediction_logits_shape"] == [1, 16]
    assert scores[0]["causal_prediction_logits_sha256"] == scores[1]["causal_prediction_logits_sha256"]
    assert scores[0]["shared_prediction_logits_shape"] == [0, 16]
