"""Check panel identity, fixed comparisons, and refusal of altered design evidence."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("design384", ROOT / "scripts/t22_kv_exploration_spec_v0.py")
d = importlib.util.module_from_spec(loader)
loader.loader.exec_module(d)


@pytest.fixture
def inputs():
    return d.read(ROOT / d.PILOT), d.read(ROOT / d.PARENT / "specification.json")


def test_original_exposed_panel_is_retained_with_known_overlap(inputs):
    pilot, canary = inputs
    assert d.input_geometry(pilot, canary) == {"target": {"2": 68, "3": 316},
                                             "source": {"2": 22, "3": 106}}
    policy = d.design()["population"]
    assert policy["previous_T22_outcomes_known_indices"] == list(range(8))
    assert not policy["exclude_previous_eight"] and not policy["fresh_confirmation"]


@pytest.mark.parametrize("mutation,error", [
    ("reorder", "original item order"), ("overlap", "eight-item overlap"),
    ("duplicate_alias", "overlapping alias_label"), ("donor_duplicate", "donor pair"),
    ("donor_type", "donor pair"), ("token_type", "token ID"),
    ("carrier", "Carrier differs"), ("reserve", "reserve access"),
])
def test_input_changes_cannot_silently_redefine_population(inputs, mutation, error):
    pilot, canary = inputs
    if mutation == "reorder":
        pilot["target_tokens"][10], pilot["target_tokens"][11] = pilot["target_tokens"][11], pilot["target_tokens"][10]
    elif mutation == "overlap":
        canary["donor_indices"][0].reverse()
    elif mutation == "duplicate_alias":
        for view in ["raw", "sequences"]:
            if view == "raw":
                pilot["target_tokens"][10][view]["alias_label"] = pilot["target_tokens"][11][view]["alias_label"]
            else:
                for carrier in d.CARRIERS:
                    pilot["target_tokens"][10][view][carrier]["alias_label"] = pilot["target_tokens"][11][view][carrier]["alias_label"]
    elif mutation == "donor_duplicate":
        pilot["donor_indices"][10] = [0, 0]
    elif mutation == "donor_type":
        pilot["donor_indices"][10] = [True, 2]
    elif mutation == "token_type":
        pilot["target_tokens"][10]["raw"]["glyph"][0] = True
        for carrier in d.CARRIERS:
            pilot["target_tokens"][10]["sequences"][carrier]["glyph"][0] = True
    elif mutation == "carrier":
        pilot["target_tokens"][10]["sequences"]["pipe"]["glyph"][-1] += 1
    else:
        pilot["reserve_access_allowed"] = True
    with pytest.raises(ValueError, match=error):
        d.input_geometry(pilot, canary)


@pytest.mark.parametrize("length", [2, 3])
def test_layout_preserves_all_four_operations_and_same_slot_geometry(length):
    rows = d.row_layout(length)
    assert len(rows) == 16
    assert [(r["operation"], r["position"], r["donor_slot"]) for r in rows] == [
        (o, p, i) for o in ("none", "k", "v", "kv") for p in ("glyph", "suffix") for i in (0, 1)]
    for row in rows:
        assert len(row["selected_positions"]) == length
        assert max(row["selected_positions"]) < row["readout_position"]
        assert row["anchor"] == 21 and row["distance"] == 8
        if row["position"] == "glyph":
            assert row["selected_positions"] == list(range(length))
        else:
            assert row["selected_positions"] == list(range(7, 7 + length))


def test_call_budget_counts_batch_sequences_not_only_calls():
    acq = d.design()["acquisition"]
    assert len(acq["per_target_per_carrier"]) == 9
    assert acq["per_target_calls"] == 2 * 9
    assert acq["per_target_sequences"] == 2 * (7 + 16 + 16)
    assert acq["total_calls"] == 384 * 18 + 128 * 2 == 7168
    assert acq["total_sequences"] == 384 * 78 + 128 * 2 == 30208
    analysis = d.design()["analysis"]
    assert analysis["scored_rows"] == 384 * 2 * 2 * 16
    assert analysis["cosines"] == analysis["scored_rows"] * 129
    assert not analysis["population_intervals"] and not analysis["hypothesis_tests"]
    assert not analysis["winner_selection"] and analysis["no_partial_effect_report"]


def test_timing_estimate_and_input_freeze_do_not_admit_unimplemented_runner():
    pilot, _, _, _, budget = d.bound_inputs(ROOT)
    assert len(pilot["target_tokens"]) == 384
    assert budget["projected_hours_mean"] == pytest.approx(14.764806574180936, rel=1e-12)
    assert 21 < budget["projected_hours_slowest_canary_scenario"] < 22
    assert 101 < budget["repeat_full_engineering_projected_hours"] < 102
    gate = d.design()["execution_admission"]
    assert gate["admitted"] is False and gate["runner_source_sha256"] is None
    assert gate["analysis_source_sha256"] is None


@pytest.fixture
def mirror(tmp_path):
    payload = d.payload(ROOT)
    for name in set(payload["source_sha256"]) | set(payload["evidence_sha256"]):
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    validation = tmp_path / "validation/design-test.json"
    xml = validation.with_suffix(".junit.xml")
    xml.write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>')
    d.write(validation, {"protocol_id": d.PROTOCOL, "status": "pass", "source_sha256": d.source_hashes(tmp_path),
                         "test_counts": {"tests": 1, "failures": 0, "errors": 0, "skipped": 0},
                         "collected": 1, "exit_code": 0, "junit_sha256": d.sha(xml)})
    return tmp_path, validation, tmp_path / "specification.json"


def test_freeze_and_audit_work_at_relocated_root_without_models(mirror):
    root, validation, output = mirror
    result = d.freeze(root, validation, output)
    assert result["acquisition_admitted"] is False
    audit = d.audit(root, output, result["specification_sha256"])
    assert audit["status"] == "pass" and audit["target_items"] == 384
    assert audit["model_forwards"] == 0 and audit["protected_bank_reads"] == 0
    with pytest.raises(ValueError, match="already exists"):
        d.freeze(root, validation, output)


@pytest.mark.parametrize("target,error", [
    ("pilot", "Historical evidence changed"), ("array", "Changed replay array"),
    ("source", "Historical bound source changed"),
])
def test_corrupt_historical_inputs_or_replay_evidence_are_rejected(mirror, target, error):
    root, _, _ = mirror
    path = {"pilot": d.PILOT, "array": d.PARENT + "/item_0000/states.npz",
            "source": "scripts/t22_kv_dissection_v0.py"}[target]
    with (root / path).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match=error):
        d.bound_inputs(root)


def test_design_or_validation_change_invalidates_frozen_identity(mirror):
    root, validation, output = mirror
    frozen = d.freeze(root, validation, output)
    stored = d.read(output)
    stored["design"]["analysis"]["winner_selection"] = True
    output.write_text(json.dumps(stored))
    with pytest.raises(ValueError, match="pinned specification changed"):
        d.audit(root, output, frozen["specification_sha256"])
    with pytest.raises(ValueError, match="Frozen design mismatch"):
        d.audit(root, output, d.sha(output))


@pytest.mark.parametrize("field,value", [("tests", 0), ("skipped", 1), ("failures", 1)])
def test_incomplete_test_receipt_cannot_freeze(mirror, field, value):
    root, validation, output = mirror
    receipt = d.read(validation)
    receipt["test_counts"][field] = value
    validation.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="Incomplete test validation"):
        d.freeze(root, validation, output)


def test_tool_never_opens_target_banks_or_outcome_reports(monkeypatch):
    real_open = Path.open
    forbidden = ("data/targets/", "results/result.json", "results/metrics.npz", "rows.csv")

    def guarded(path, *args, **kwargs):
        assert not any(name in str(path) for name in forbidden)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    assert d.payload(ROOT)["new_384_acquisition_model_forwards"] == 0
