"""Source-only review repairs; never open protected banks or private records."""

import importlib.util
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


def source_inventory():
    source = ROOT / "scripts/contextual_emoji_two_track_v1.py"
    spec = importlib.util.spec_from_file_location("two_track_paper_examples", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # inventory() reads only the named, checksum-bound public development file.
    return module, {row["input_id"]: row for row in module.inventory()}


def displayed_prompts():
    text = (PAPER / "contextual_input_examples_20261015.tex").read_text()
    blocks = re.findall(
        r"% exact-input: (\S+)\n\\begin\{contextinput\}\n(.*?)\n\\end\{contextinput\}",
        text,
        flags=re.DOTALL,
    )
    assert len(blocks) == 7 and len({key for key, _ in blocks}) == 7
    prompts = {}
    for key, block in blocks:
        # Codepoint spellings are explicitly declared display substitutions.
        decoded = block.replace("U+1F525", "\U0001f525").replace("U+1F9CA", "\U0001f9ca")
        prompts[key] = decoded.replace("\\\\\n", "\n")
    return text, prompts


def test_displayed_inputs_are_exact_public_source_prompts():
    _, inventory = source_inventory()
    text, prompts = displayed_prompts()
    for key, displayed in prompts.items():
        assert displayed == inventory[key]["prompt"]
        assert inventory[key]["answers"] == {
            "a": " The answer is yes.",
            "b": " The answer is no.",
        }
    assert r"\verb| The answer is yes.|" in text
    assert r"\verb| The answer is no.|" in text
    assert "never their codepoint spellings" in text
    assert "not from a participant packet" in text


def test_full_cross_word_alternatives_and_question_reversals_match_source():
    module, inventory = source_inventory()
    text, prompts = displayed_prompts()
    source = module.sources()[0]
    assert source["block_id"] == "thermal_01"
    assert source["planned_word_alternatives"] == {"a": "hot", "b": "cold"}
    assert r"\texttt{hot}" in text and r"\texttt{cold}" in text
    for context in ("p", "q"):
        for cue in ("a", "b"):
            key = f"thermal_01::{context}::emoji::{cue}::message_reading::positive"
            assert key in prompts
            word_key = key.replace("::emoji::", "::word::")
            assert prompts[key].replace(
                source[f"emoji_{cue}"], source["planned_word_alternatives"][cue]
            ) == inventory[word_key]["prompt"]
            assert prompts[key].replace("Is it true that", "Is it false that") == (
                inventory[key.replace("::positive", "::negative")]["prompt"]
            )


def test_complete_report_polarities_are_identical_except_question_reversal():
    _, prompts = displayed_prompts()
    positive = "thermal_01::p::complete_report::outcome_evidence::positive"
    negative = positive.replace("::positive", "::negative")
    assert prompts[positive].replace("Is it true that", "Is it false that") == prompts[negative]
    assert prompts[positive].startswith(
        "For this question, assume this report is accurate: Mira has warmed up.\n"
    )


def test_bootstrap_decision_roles_are_distinguished():
    main = (PAPER / "main.tex").read_text()
    assert "its primary decision uses the randomization\ntests above" in main
    assert "subsequent causal designs also use bootstrap lower bounds" in main


def test_reader_facing_swap_tables_do_not_claim_upper_bounds():
    main = (PAPER / "main.tex").read_text()
    table_blocks = re.findall(r"\\begin\{table\}.*?\\end\{table\}", main, flags=re.DOTALL)
    selected = [table for table in table_blocks if r"\label{tab:posthoc}" in table or r"\label{tab:t20}" in table]
    assert len(selected) == 2
    for table in selected:
        assert "ceiling" not in table.lower()
        assert "swap" in table and "upper" in table
    # Historical protocol vocabulary remains traceable, without claiming a bound.
    assert r"historical protocol calls these swaps \emph{ceilings}" in main


def test_working_status_and_examples_integration_are_explicit():
    main = (PAPER / "main.tex").read_text()
    contextual = (PAPER / "contextual_development_20261010.tex").read_text()
    assert "Revised preprint, October 15, 2026" in main
    assert "Independent preprint. CC BY 4.0." in main
    assert "Public release is deferred until the new study is complete" not in main
    assert "https://doi.org/10.5281/zenodo.23376699" in main
    assert "landing page records the\ndeposit status" in main
    assert "not a complete evidence package for this revision" in main
    assert r"\input{contextual_input_examples_20261015.tex}" in contextual


def test_release_license_and_inference_replay_boundaries_are_explicit():
    main = (PAPER / "main.tex").read_text()
    assert "project-authored public data under\nCC BY 4.0" in main
    assert "Project code remains Apache-2.0" in main
    assert "Third-party materials retain\ntheir original licenses and notices" in main
    assert "T19-C and T20-C provide compact site-level summaries" in main
    assert "does not support independent recomputation of their\nitem-level resampling and decision statistics" in main
    assert "T19-L prediction indices and exact strata allow model-free\nstatistical replay" in main
    assert "not independent reconstruction of GPU logits" in main
