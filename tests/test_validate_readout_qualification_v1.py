"""Independent-checker tests using synthetic scores; no tokenizer/model acquisition."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


v = load("independent_readout_validator", ROOT / "scripts/validate_readout_qualification_v1.py")
# Acquisition mocks supply only fixtures and the independently checked comparison
# artifact. The validator itself imports no acquisition or analysis functions.
m = load("readout_acquisition_test_fixtures", ROOT / "tests/test_readout_qualification_v1.py")


def refresh_inventory_hashes(spec):
    spec["tokenized_inputs_sha256"] = v.object_sha(spec["inputs"])
    stripped = [{k: value for k, value in row.items() if k not in
                 ("candidates", "shared_prefix_token_count", "causal_predictor_token_count")}
                for row in spec["inputs"]]
    spec["inventory_sha256"] = v.object_sha(stripped)


@pytest.fixture(scope="module")
def specification():
    spec = m.spec.__wrapped__()
    spec.update(protocol_id=v.PROTOCOL, primary=copy.deepcopy(v.PRIMARY),
                label_robustness_gate=copy.deepcopy(v.LABEL_GATE), planned_pairs=2304,
                planned_scientific_sequence_scores=4608, planned_sentinel_forwards=32,
                planned_forward_attempts=4640, source_files={"synthetic-fixture": "0" * 64})
    for case in spec["sentinels"]:
        if case["shared_prefix_token_count"] == 0:
            for score in case["expected_scores"].values():
                score["shared_prediction_logits_sha256"] = v.EMPTY_SHA
    refresh_inventory_hashes(spec)
    return spec


def fixture_records(spec, modify=None):
    rows = m.records(spec, modify)
    for row in rows:
        if row["geometry"]["shared_prefix_token_count"] == 0:
            row["shared_prediction_logits_sha256"] = v.EMPTY_SHA
    return rows


@pytest.fixture(scope="module")
def complete(specification):
    rows = fixture_records(specification)
    return rows, m.q.analyze(specification, rows)


def test_independent_all_correct_and_supplemental_summaries(specification, complete):
    rows, saved = complete
    result = v.recompute(specification, rows, saved)
    assert result["independent_arithmetic_validation_passed"] is True
    assert result["primary_qualification_passed"] is True
    assert result["label_robustness_passed"] is True
    assert result["primary"]["correct"] == 96 and result["primary"]["all_correct_roots"] == 16
    assert result["label_robustness"]["correct"] == 192
    assert len(result["groups"]) == 24
    assert len(result["family_groups"]) == 48
    assert len(result["root_margin_summaries"]) == 384
    assert all(r["minimum_reference_signed_margin_nats"] == 1 for r in result["root_margin_summaries"])
    assert all(r["planned_pairs"] == 48 for r in result["family_groups"])
    assert result["model_forwards"] == result["tokenizer_calls"] == result["inference_tests"] == 0
    assert result["independent_reacquisition"] is False


@pytest.mark.parametrize("failure", ["wrong", "tie"])
def test_primary_failure_is_validated_not_converted_to_success(specification, failure):
    target = next(r["input_id"] for r in specification["inputs"] if r["split"] == "reserved_check" and
                  r["question_form"] == "direct" and r["answer_format"] == "minimal")
    def modify(case, event):
        return ({"correct": False} if failure == "wrong" else {"tie": True}) if case["input_id"] == target else {}
    rows = fixture_records(specification, modify)
    result = v.recompute(specification, rows, m.q.analyze(specification, rows))
    assert result["independent_arithmetic_validation_passed"]
    assert not result["primary_qualification_passed"]
    assert result["primary"]["correct"] == 95
    assert result["primary"]["all_correct_roots"] == 15
    assert result["label_robustness_passed"]
    assert min(r["minimum_reference_signed_margin_nats"] for r in result["root_margin_summaries"]) == (-1 if failure == "wrong" else 0)


def test_labels_remain_separate_from_primary(specification):
    def modify(case, event):
        return {"correct": False} if event["phase"] == "qualification" and case["answer_format"] == "letters_reversed" else {}
    rows = fixture_records(specification, modify)
    result = v.recompute(specification, rows, m.q.analyze(specification, rows))
    assert result["primary_qualification_passed"]
    assert not result["label_robustness_passed"]
    assert result["label_robustness"]["correct"] == 96


def test_unknown_reference_independently_derived_even_after_rehash(specification):
    spec = copy.deepcopy(specification)
    row = next(r for r in spec["inputs"] if r["report_state"] == "unknown" and r["question_form"] == "direct")
    row["proposition_supported"] = True
    row["expected_yes"] = True
    refresh_inventory_hashes(spec)
    with pytest.raises(ValueError, match="Logical support reference"):
        v.validate_inventory(spec)


def test_reversed_physical_label_mapping_independently_checked(specification):
    spec = copy.deepcopy(specification)
    row = next(r for r in spec["inputs"] if r["answer_format"] == "letters_reversed")
    row["answers"] = {"a": " A", "b": " B"}
    refresh_inventory_hashes(spec)
    with pytest.raises(ValueError, match="physical response mapping"):
        v.validate_inventory(spec)


def test_unknown_report_lexical_content_checked(specification):
    spec = copy.deepcopy(specification)
    row = next(r for r in spec["inputs"] if r["report_state"] == "unknown")
    row["report"] = row["positive_proposition"] + "."
    refresh_inventory_hashes(spec)
    with pytest.raises(ValueError, match="Report/question"):
        v.validate_inventory(spec)


@pytest.mark.parametrize("change", ["missing", "reorder", "not_run", "sum", "sentinel", "first_predictor", "empty_hash", "geometry"])
def test_corruption_or_missingness_fails_closed(specification, complete, change):
    rows, saved = copy.deepcopy(complete)
    pattern = ""
    if change == "missing":
        rows.pop()
        pattern = "Missing/extra"
    elif change == "reorder":
        rows[16], rows[17] = rows[17], rows[16]
        pattern = "identity/order"
    elif change == "not_run":
        rows[16].update(status="not_run", forward_attempted=False)
        pattern = "Incomplete"
    elif change == "sum":
        rows[16]["sequence_logprob_sum"] -= 0.25
        pattern = "Token sum"
    elif change == "sentinel":
        rows[-1]["shared_prediction_logits_sha256"] = "c" * 64
        pattern = "Historical sentinel"
    elif change == "first_predictor":
        target = next(r for r in rows if r["phase"] == "qualification" and r["method"] == "padded_b" and
                      r["geometry"]["shared_prefix_token_count"] == 0)
        target["causal_prediction_logits_sha256"] = "c" * 64
        pattern = "First-divergence/prefix"
    elif change == "empty_hash":
        target = next(r for r in rows if r["phase"] == "qualification" and r["geometry"]["shared_prefix_token_count"] == 0)
        target["shared_prediction_logits_sha256"] = "c" * 64
        pattern = "Empty prefix"
    elif change == "geometry":
        rows[16]["geometry"]["input_token_ids"][0] += 1
        pattern = "identity/order/geometry"
    with pytest.raises(ValueError, match=pattern):
        v.recompute(specification, rows, saved)


def test_saved_analysis_not_trusted(specification, complete):
    rows, saved = copy.deepcopy(complete)
    saved["primary"]["correct"] = 95
    with pytest.raises(ValueError, match="Saved analysis.*primary"):
        v.recompute(specification, rows, saved)


def test_saved_per_pair_margin_not_trusted(specification, complete):
    rows, saved = copy.deepcopy(complete)
    saved["pairs"][100]["s_yes_minus_no"] += 0.1
    with pytest.raises(ValueError, match="Saved analysis.*pairs"):
        v.recompute(specification, rows, saved)


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_or_nonfinite_json_rejected(text):
    with pytest.raises(ValueError):
        v.decode(text)


def write_fixture(tmp_path, specification, complete):
    rows, saved = complete
    spec_path = tmp_path / "specification.json"
    spec_path.write_text(json.dumps(specification), encoding="utf-8")
    digest = v.sha(spec_path)
    run = tmp_path / "run"
    run.mkdir()
    (run / "forwards.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    (run / "analysis.json").write_text(json.dumps(saved), encoding="utf-8")
    started = {"protocol_id": v.PROTOCOL, "specification_sha256": digest, "source_files": specification["source_files"]}
    (run / "run_started.json").write_text(json.dumps(started), encoding="utf-8")
    receipt = {**started, "status": "completed", "stop_reason": None, "numerical_gate_passed": True,
        "forward_attempts": 4640, "planned_forward_attempts": 4640, "completed_pairs": 2304,
        "status_counts": {"completed": 4640}, "primary_qualification_passed": saved["primary_qualification_passed"],
        "label_robustness_passed": saved["label_robustness_passed"],
        "artifacts": {p.name: v.sha(p) for p in run.iterdir()}}
    (run / "run_completed.json").write_text(json.dumps(receipt), encoding="utf-8")
    return spec_path, run, digest, tmp_path / "independent_validation.json"


def test_file_api_hash_binding_and_refusal_to_overwrite(tmp_path, specification, complete):
    spec_path, run, digest, output = write_fixture(tmp_path, specification, complete)
    result = v.validate_files(spec_path, run, digest, output)
    assert result["status"] == "independently_recomputed_saved_scores"
    saved = v.read(output)
    assert saved["provenance"]["forwards_sha256"] == v.sha(run / "forwards.jsonl")
    assert saved["provenance"]["specification_sha256"] == digest
    assert saved["provenance"]["all_recorded_artifact_hashes_verified"]
    with pytest.raises(ValueError, match="overwrite"):
        v.validate_files(spec_path, run, digest, output)


@pytest.mark.parametrize("corruption", ["spec_sha", "raw_hash", "path", "incomplete", "receipt_verdict"])
def test_file_api_rejects_corruption_without_output(tmp_path, specification, complete, corruption):
    spec_path, run, digest, output = write_fixture(tmp_path, specification, complete)
    if corruption == "spec_sha":
        digest = "0" * 64
    elif corruption == "raw_hash":
        with (run / "forwards.jsonl").open("a") as handle:
            handle.write("\n")
    else:
        receipt = v.read(run / "run_completed.json")
        if corruption == "path":
            receipt["artifacts"]["../escape"] = "0" * 64
        elif corruption == "incomplete":
            receipt["status"] = "stopped_or_gate_failed"
        elif corruption == "receipt_verdict":
            receipt["primary_qualification_passed"] = False
        (run / "run_completed.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError):
        v.validate_files(spec_path, run, digest, output)
    assert not output.exists()


def test_validator_has_no_acquisition_or_runner_import():
    source = (ROOT / "scripts/validate_readout_qualification_v1.py").read_text()
    assert "import torch" not in source
    assert "import transformers" not in source
    assert "import readout_qualification_v1" not in source
    assert "importlib" not in source
