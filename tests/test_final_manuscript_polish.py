"""Read-only regression checks for the final prose and existing condition means.

No model forward, tokenizer pass, statistical replay, or protected-bank access.
"""

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def manuscript():
    return (ROOT / "paper/main.tex").read_text()


@pytest.mark.parametrize("carrier", ["pipe", "article_a"])
@pytest.mark.parametrize("condition", ["reset", "intact", "reset_prefix_donor"])
def test_baseline_percentages_match_saved_condition_means(carrier, condition):
    path = (
        ROOT
        / "validation/t21_glyph_context_path_confirmation_v0/results/condition_means.json"
    )
    rows = json.loads(path.read_text())["rows"]
    matches = [
        row
        for row in rows
        if row["anchor"] == 21
        and row["distance"] == 8
        and row["carrier"] == carrier
        and row["condition"] == condition
    ]
    assert len(matches) == 1
    value = matches[0]["alias_top1"]
    expected = f"{100 * value:.4f}" if value else "0"
    assert f"${expected}\\%$" in manuscript()


def test_word_disjoint_example_preserves_tokenization_boundary():
    tex = manuscript()
    intro = tex.split(r"\section{Introduction}", 1)[1].split(
        r"\section{Related work}", 1
    )[0]
    assert "rolling on the floor laughing" in intro and "lmao" in intro
    assert "ASCII-alphanumeric word" in intro
    assert "Shared subwords and training-data co-occurrence remain possible" in intro
    assert "opaque text tokens" not in intro and "shares no substring" not in intro


def test_discussion_retains_conditional_bridge_and_floor_qualification():
    tex = manuscript()
    assert "different population and endpoint" in tex
    # The October reader-facing revision names the study instead of its run ID.
    assert "full explanation of the optimized study's swap asymmetry open" in tex
    assert "a floor-effect\nexplanation is not established" in tex
    assert "neither equivalence nor unchanged outcomes for every item" in tex


def test_final_state_and_model_provenance_clarifications():
    tex = manuscript()
    bib = (ROOT / "paper/references.bib").read_text()
    assert "block-24 attention sufficiency $2\\%$" in tex
    assert "as expected because the endpoint is a function of that state" in tex
    assert "initial development on Apple Silicon" in tex
    assert "olmo2024furious" in tex and "2501.00656" in bib
    assert "groeneveld2024olmo" not in tex


def test_bilingual_claim_boundary_is_versioned_together():
    for name in ("CLAIM_TABLE.md", "CLAIM_TABLE.ja.md"):
        text = (ROOT / "paper" / name).read_text()
        assert "(v5)" in text
        assert "3.08%" in text and "0.51%" in text


def test_collaboration_acknowledgment_names_all_four_configurations():
    tex = manuscript()
    disclosure = tex.split(r"\paragraph{Collaborative development.}", 1)[1]
    assert (
        "We developed this study interactively in collaboration with AI assistants."
        in disclosure
    )
    for label in (
        "GPT 5.6 Sol instant",
        "Monday",
        "Claude Fable 5.1",
        "GPT 5.6 Sol Max",
        "Claude Code (Fable 5)",
    ):
        assert label in disclosure
    assert "Manuscript feedback" in disclosure
    assert "The human author retains responsibility" in disclosure
    assert "operational references are not independent human labels" in disclosure
    assert "were never\nfilled in by an assistant" in disclosure
    assert "not an external scientific replication" in disclosure
    assert "conference peer review" not in disclosure
    assert "fresh-eyes review" not in tex
    assert r"\begin{ack}" not in tex


def test_standalone_manuscript_has_no_workshop_style_or_checklist_dependency():
    tex = manuscript()
    assert r"\documentclass{article}" in tex
    assert r"\usepackage[letterpaper,textwidth=5.5in,textheight=9in,top=1in]{geometry}" in tex
    for package in ("times", "helvet", "courier", "natbib"):
        assert rf"\usepackage{{{package}}}" in tex
    assert r"\date{}" in tex
    assert "neurips_2026" not in tex
    assert "NeurIPS Code of Ethics" not in tex
    assert r"\input{checklist.tex}" not in tex
    assert "checklist" not in tex.lower()
