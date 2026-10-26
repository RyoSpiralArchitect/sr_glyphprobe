#!/usr/bin/env python3
"""Export allowlisted aggregates for the local working draft, without raw answers.

Reads completed records; performs no model, tokenizer, network, or GPU calls.
Private inputs stay outside Git. Outputs are new, versioned files, not a release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import compare_contextual_emoji_two_track_author_v1 as comparison
import diagnose_contextual_emoji_two_track_readout_v1 as diagnostic

PROBES = ("local_match", "message_reading", "outcome_evidence")
LABELS = ("Property match", "Message interpretation", "Outcome evidence")
MATCHED_SHA = "8557d04e77b6c095022b3d97d5404024b1f7be8d1a101a93a6e54ebdcd4d2e35"


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def human_aggregate(phase, compared, joined):
    """Explicit projection; never export arbitrary source keys or item records."""
    rows = []
    for probe in PROBES:
        counts = phase["by_probe"][probe]
        row = next(r for r in compared["human_by_probe"] if r["probe"] == probe)
        require(row["human_status_counts"] == counts, "Human summaries disagree")
        require(sum(counts.values()) == row["judgments"], "Human denominator differs")
        rows.append({
            "probe": probe,
            "yes": counts["yes"], "no": counts["no"],
            "undecidable": counts["undecidable"],
            "abstain": counts["abstain"], "missing": counts["missing"],
            "judgments": row["judgments"],
            "comparable_binary": row["comparable_binary"],
            "same_question_agreement": row["agreement_positive_question"],
        })
    overall = compared["human_overall"]
    require(sum(r["judgments"] for r in rows) == overall["judgments"], "Lost judgments")
    require(len(joined) == overall["judgments"], "Joined denominator differs")
    rule_matches = sum(r["model_positive_truth"] is (r["probe"] == "local_match") for r in joined)
    return {
        "participants": 1, "independent_evaluators": 0,
        "status": "previously_exposed_author_instrument_development",
        "scenes": overall["scenes"], "judgments": overall["judgments"],
        "by_probe": rows,
        "binary": overall["comparable_binary"],
        "same_question_agreement": overall["agreement_positive_question"],
        "posthoc_question_type_constant_matches": rule_matches,
        "posthoc_question_type_constant_denominator": len(joined),
        "selected_polarity_inconsistent": overall["polarity_inconsistent_selected_questions"],
        "response_recoding": False,
    }


def build(private_analysis, package):
    completion = read(private_analysis / "analysis_completion.json")
    for name, expected in completion["artifacts"].items():
        require(Path(name).name == name, "Unsafe private artifact path")
        require(sha(private_analysis / name) == expected, "Private artifact changed: " + name)
    for name, expected in completion["source_files"].items():
        require(sha(ROOT / name) == expected, "Analysis source changed")
    compared, artifacts = comparison.compare(private_analysis, package, write=False)
    for name, expected in artifacts.items():
        require(read(private_analysis / name) == expected, "Saved comparison differs: " + name)
    token, _ = diagnostic.saved_run()
    require(token == read(private_analysis / "secondary_token_diagnostic.json"), "Token diagnostic differs")

    matched_path = ROOT / "validation/contextual_emoji_matched_shape_v1/independent_analysis.json"
    require(sha(matched_path) == MATCHED_SHA, "Matched-shape analysis changed")
    matched = read(matched_path)
    require(matched["numerical_gate_passed"] and matched["analysis"]["all_624_prefix_residuals_zero"],
            "Matched-shape qualification failed")
    folder = ROOT / "validation/contextual_emoji_two_track_v1"
    run = read(folder / "run3296/run_completed.json")
    matched_rows = [{"pair": r["pair_id"], "carrier": r["carrier"],
                     "scenarios": r["blocks"], "inputs": r["inputs"],
                     "mean_interaction_nats": r["new"]["H"]["mean"],
                     "positive_interaction": r["new"]["H_positive_blocks"],
                     "effect_crossover": r["new"]["effect_crossover_blocks"],
                     "all_four_author_aligned": r["new"]["all_four_aligned_blocks"]}
                    for r in matched["analysis"]["per_pair_carrier"]]
    return {
        "schema_version": 1, "revision": "2026-10-10",
        "status": "unfinished_local_working_draft_aggregate_only",
        "publication": False, "new_model_forwards": 0,
        "new_independent_scenarios": 0, "population_inference": False,
        "human": human_aggregate(read(private_analysis / "phase_one_summary.json"),
                                 compared, artifacts["comparison_items.json"]),
        "matched_shape": {
            "scientific_pairs": 624, "scientific_sequences": 1248,
            "forward_calls_including_sentinels": 1312,
            "all_common_prefixes_exact": True, "by_formulation_carrier": matched_rows,
            "stability": [{"carrier": r["carrier"], "scenarios": r["blocks"],
                           "inputs": r["inputs"], **r["new"]}
                          for r in matched["analysis"]["all_pair_stability"]],
        },
        "two_track": {
            "scenarios": compared["model_inventory"]["scenarios"],
            "candidate_pairs": compared["model_inventory"]["candidate_pairs"],
            "sequence_scores": run["forward_attempts"] - 32,
            "forward_calls_including_sentinels": run["forward_attempts"],
            "numerical_gate_passed": run["numerical_gate_passed"],
            "primary_ties": compared["model_inventory"]["ties"],
            "polarity": compared["polarity_overall"],
            "by_carrier_probe_polarity": compared["model_by_carrier_probe_polarity"],
            "anchors": compared["model_anchor_by_type_polarity"],
            "context_cue_contrasts": compared["context_cue_contrast_by_carrier_probe_polarity"],
            "elapsed_seconds": run["elapsed_seconds"],
            "peak_torch_memory_mib": run["peak_torch_memory_mib"],
        },
        "secondary_token_diagnostic": {
            "primary_estimator_changed": False,
            "decomposition": token["decomposition"],
            "polarity": token["answer_token_polarity"],
            "anchors": token["answer_token_anchors"],
        },
        "provenance": {
            "private_completion_sha256": sha(private_analysis / "analysis_completion.json"),
            "matched_shape_analysis_sha256": MATCHED_SHA,
            "two_track_model_files": comparison.MODEL_FILES,
            "exporter_sha256": sha(__file__),
        },
        "privacy_boundary": "Only aggregate counts exported; no item assignments, answers, notes, timestamps, or private paths. Not a public-release authorization.",
    }


def tables(summary):
    lines = ["% Generated by build_development_summary_20261010.py; do not edit.",
             r"\begin{table}[H]", r"\centering\small",
             r"\begin{tabular}{llrrrr}", r"\toprule",
             r"Formulation & Cue & Mean $H$ & $H>0$ & Crossover & All four \\",
             r"\midrule"]
    names = {"original": "Scenario-specific", "explicit_negation": "Explicit negation", "adjective_pair": "Adjective pair"}
    for row in summary["matched_shape"]["by_formulation_carrier"]:
        lines.append(f"{names[row['pair']]} & {row['carrier'].title()} & {row['mean_interaction_nats']:.4f} & {row['positive_interaction']}/24 & {row['effect_crossover']}/24 & {row['all_four_author_aligned']}/24 " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{Matched-execution response scoring on the same 24 development scenarios. $H$ is an author-oriented context--cue interaction in nats. Crossover requires the expected reversal of the cue effect. All four requires author-aligned choices in every crossed input; authored labels are not independent human judgments.}",
              r"\label{tab:development-formulations}", r"\end{table}",
              r"\begin{table}[H]", r"\centering\small", r"\begin{tabular}{lrrrrr}", r"\toprule",
              r"Question & Yes & No & Undecidable & Binary & Agreement \\", r"\midrule"]
    for label, row in zip(LABELS, summary["human"]["by_probe"]):
        lines.append(f"{label} & {row['yes']} & {row['no']} & {row['undecidable']} & {row['comparable_binary']}/{row['judgments']} & {row['same_question_agreement']}/{row['comparable_binary']} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              r"\caption{One previously exposed author's development tryout: 24 scenes, 36 judgments, no missing answers or abstentions. Agreement uses the exact positive-worded question and binary human judgments only. It is response-selected agreement, not accuracy; undecidable responses remain separate.}",
              r"\label{tab:development-author}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-analysis", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists() and not args.tables.exists(), "Existing outputs preserved")
    result = build(args.private_analysis, args.package)
    for path in (args.output, args.tables):
        path.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    with args.tables.open("x") as stream:
        stream.write(tables(result))
    print(json.dumps({"status": result["status"], "human_judgments": result["human"]["judgments"],
                      "model_pairs": result["two_track"]["candidate_pairs"], "new_model_forwards": 0}))


if __name__ == "__main__":
    main()
