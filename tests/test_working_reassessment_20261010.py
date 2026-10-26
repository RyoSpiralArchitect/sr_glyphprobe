"""Read-only paper/count checks; private response fixtures are never opened."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper/scripts/build_development_summary_20261010.py"
spec = importlib.util.spec_from_file_location("working_export", SOURCE)
export = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)


def summary():
    return json.loads((ROOT / "validation/contextual_emoji_working_revision_20261010/summary.json").read_text())


def test_export_has_only_aggregate_human_fields():
    d = summary()
    assert d["human"]["participants"] == 1
    assert d["human"]["independent_evaluators"] == 0
    assert d["new_independent_scenarios"] == 0
    assert not d["publication"] and not d["population_inference"]
    assert d["new_model_forwards"] == 0
    excluded = {"input_id", "id", "display_item", "prompt", "question", "human_status",
                "assignment", "note", "setup_self_report", "pseudonym", "created_at_utc"}
    def visit(value):
        if isinstance(value, dict):
            assert not (set(value) & excluded)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str):
            assert "/Users/" not in value and "/home/" not in value
    visit(d)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == d["provenance"]["exporter_sha256"]


def test_human_denominators_and_uncertainty_are_retained():
    h = summary()["human"]
    assert h["scenes"] == 24 and h["judgments"] == 36
    assert sum(r["judgments"] for r in h["by_probe"]) == 36
    assert sum(r["undecidable"] for r in h["by_probe"]) == 10
    assert sum(r["yes"] + r["no"] for r in h["by_probe"]) == h["binary"] == 26
    assert sum(r["same_question_agreement"] for r in h["by_probe"]) == h["same_question_agreement"] == 16
    assert all(r["abstain"] == r["missing"] == 0 for r in h["by_probe"])
    assert h["posthoc_question_type_constant_matches"] == h["posthoc_question_type_constant_denominator"] == 36
    assert not h["response_recoding"]


def test_raw_model_polarities_recomputed_without_private_join():
    folder = ROOT / "validation/contextual_emoji_two_track_v1"
    scores = {}
    for line in (folder / "run3296/forwards.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r["phase"] == "development":
            key = r["input_id"], r["method"]
            assert key not in scores
            scores[key] = math.fsum(r["candidate_token_logprobs"])
    cases = json.loads((folder / "specification.json").read_text())["inputs"]
    truth_pairs = {}
    complete_positive_no = 0
    for c in cases:
        s = scores[c["input_id"], "padded_a"] - scores[c["input_id"], "padded_b"]
        assert s != 0
        stem = c["input_id"].rsplit("::", 1)[0]
        truth_pairs.setdefault(stem, {})[c["polarity"]] = s > 0 if c["polarity"] == "positive" else s < 0
        if c["cue"] == "complete_report" and c["polarity"] == "positive":
            complete_positive_no += s < 0
    assert len(cases) == 1632 and len(scores) == 3264 and len(truth_pairs) == 816
    assert all(set(p) == {"positive", "negative"} for p in truth_pairs.values())
    inconsistent = sum(p["positive"] != p["negative"] for p in truth_pairs.values())
    assert inconsistent == summary()["two_track"]["polarity"]["inconsistent"] == 710
    assert complete_positive_no == 48


def test_generated_tables_match_the_export_exactly():
    path = ROOT / "paper/generated/contextual_development_tables_20261010.tex"
    assert path.read_text() == export.tables(summary())


def test_manuscript_model_tables_match_all_reported_rows():
    d = summary()["two_track"]
    tex = (ROOT / "paper/contextual_development_20261010.tex").read_text()
    labels = {"local_match": "Property match", "message_reading": "Message interpretation", "outcome_evidence": "Outcome evidence"}
    for probe, label in labels.items():
        chosen = "literal_yes" if probe == "local_match" else "literal_no"
        rows = [next(r for r in d["by_carrier_probe_polarity"] if r["probe"] == probe and r["polarity"] == "positive" and r["carrier"] == carrier)
                for carrier in ("emoji", "word", "absent")]
        fragment = " & ".join(f"{r[chosen]}/{r['candidate_pairs']}" for r in rows)
        assert fragment in tex
        contrasts = [next(r for r in d["context_cue_contrasts"] if r["probe"] == probe and r["carrier"] == carrier and r["polarity"] == polarity)
                     for carrier in ("emoji", "word") for polarity in ("positive", "negative")]
        formatted = [f"${r['mean']:.3f}$" if r["mean"] < 0 else f"{r['mean']:.3f}" for r in contrasts]
        assert label + " & " + " & ".join(formatted) in tex


def test_primary_estimator_and_secondary_ties_are_preserved():
    d = summary()["secondary_token_diagnostic"]
    assert not d["primary_estimator_changed"]
    assert d["decomposition"]["sign_reversals_excluding_ties"] == 103
    assert d["decomposition"]["answer_token_ties"] == 191
    assert d["polarity"] == {"consistent": 78, "inconsistent": 553, "polarity_pairs": 816, "tie": 185}


def test_historical_pdf_preserved_and_successor_scoped():
    previous = ROOT / "output/pdf/glyphprobe_post_review_20261007.pdf"
    assert hashlib.sha256(previous.read_bytes()).hexdigest() == "43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898"
    main = (ROOT / "paper/main.tex").read_text()
    # The Oct 10 PDF remains the immutable working draft; the current source
    # now explicitly identifies the locally prepared Oct 15 successor.
    assert "Revised preprint, October 15, 2026" in main
    assert "10.5281/zenodo.23376699" in main
    assert "its landing page records the" in main
    assert "710/816" in main and "previously exposed" in main
    assert "Effects on ordinary model\nresponses remain untested" not in main
    assert "The study uses no human participants" not in main
    for name in ("CONTEXTUAL_EMOJI_REASSESSMENT_20261010",):
        assert (ROOT / "docs" / (name + ".md")).exists()
        assert (ROOT / "docs" / (name + ".ja.md")).exists()


def synthetic_sources():
    counts = {"yes": 1, "no": 1, "undecidable": 1, "missing": 1, "abstain": 1}
    phase = {"by_probe": {p: dict(counts) for p in export.PROBES}, "private_note": "never export"}
    rows = [{"probe": p, "human_status_counts": dict(counts), "judgments": 5,
             "comparable_binary": 2, "agreement_positive_question": 1} for p in export.PROBES]
    compared = {"human_by_probe": rows, "human_overall": {"judgments": 15, "scenes": 10,
                "comparable_binary": 6, "agreement_positive_question": 3,
                "polarity_inconsistent_selected_questions": 10}, "private_note": "never export"}
    joined = [{"probe": p, "model_positive_truth": True, "private_note": "never export"}
              for p in export.PROBES for _ in range(5)]
    return phase, compared, joined


def test_projection_keeps_missing_and_abstention_without_private_passthrough():
    result = export.human_aggregate(*synthetic_sources())
    assert all(r["missing"] == r["abstain"] == r["undecidable"] == 1 for r in result["by_probe"])
    assert "private_note" not in json.dumps(result)


def test_projection_rejects_disagreeing_denominators():
    p, c, j = synthetic_sources()
    changed = copy.deepcopy(c)
    changed["human_by_probe"][0]["judgments"] += 1
    with pytest.raises(ValueError, match="denominator"):
        export.human_aggregate(p, changed, j)
