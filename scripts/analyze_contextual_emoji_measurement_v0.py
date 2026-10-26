#!/usr/bin/env python3
"""Post hoc, CPU-only identities and diagnostics from pinned saved GlyphProbe scores.

No model/tokenizer imports, probability reexecution, downloads, or remote calls.
The complete fixed development grid is required; this analyzer never drops rows.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import statistics
import sys

PROTOCOL = "glyphprobe-contextual-emoji-measurement-v0"
SAVED_ANALYSIS_SHA256 = "1512f4ad613a4d9d20473c1a33af326412299c3a7f3a0d031551716ca753c719"
PAIR_IDS = ("original", "explicit_negation", "adjective_pair")
CARRIERS = ("emoji", "word")
COEFFICIENTS = ("b0", "bC", "bV", "bCV")
THRESHOLDS = (0.0, 0.1, 0.5, 1.0)
CONTEXT = {"p": -1, "q": 1}
CUE = {"a": -1, "b": 1}
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
TOLERANCE = 1e-11  # Arithmetic identities only; never relaxed acquisition parity.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    require(type(value) in (int, float) and math.isfinite(value), "Nonfinite or nonnumeric score")
    return value


def close(left, right):
    return math.isclose(left, right, rel_tol=TOLERANCE, abs_tol=TOLERANCE)


def mean(values):
    values = list(values)
    require(bool(values), "Empty denominator")
    return math.fsum(values) / len(values)


def safe(path):
    path = Path(path)
    require(path.name not in PROTECTED and path.resolve().name not in PROTECTED, "Protected historical bank")
    return path.resolve()


def digest(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    return json.loads(safe(path).read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=invalid)


def decompose(s, eta):
    """Exact saturated 2x2 expansion, with explicit finite-grid validation."""
    require(type(eta) is int and eta in (-1, 1), "Invalid eta")
    require(set(s) == set(CONTEXT) and all(set(s[c]) == set(CUE) for c in CONTEXT), "Incomplete 2x2 score grid")
    t = {c: {v: eta * finite(s[c][v]) for v in CUE} for c in CONTEXT}
    cells = [(c, v) for c in CONTEXT for v in CUE]
    coeff = {
        "b0": mean(t[c][v] for c, v in cells),
        "bC": mean(CONTEXT[c] * t[c][v] for c, v in cells),
        "bV": mean(CUE[v] * t[c][v] for c, v in cells),
        "bCV": mean(CONTEXT[c] * CUE[v] * t[c][v] for c, v in cells),
    }
    reconstructed = {c: {v: coeff["b0"] + coeff["bC"] * CONTEXT[c] + coeff["bV"] * CUE[v]
                        + coeff["bCV"] * CONTEXT[c] * CUE[v] for v in CUE} for c in CONTEXT}
    margins = {c: {v: CONTEXT[c] * CUE[v] * t[c][v] for v in CUE} for c in CONTEXT}
    delta_p = eta * (s["p"]["b"] - s["p"]["a"])
    delta_q = eta * (s["q"]["b"] - s["q"]["a"])
    h = delta_q - delta_p
    crossover = delta_p < 0 < delta_q
    coefficient_crossover = coeff["bCV"] > abs(coeff["bV"])
    min_margin = min(margins[c][v] for c, v in cells)
    errors = [abs(t[c][v] - reconstructed[c][v]) for c, v in cells]
    require(all(close(t[c][v], reconstructed[c][v]) for c, v in cells), "2x2 reconstruction failed")
    require(close(h, 4 * coeff["bCV"]) and close(h, math.fsum(margins[c][v] for c, v in cells)), "Interaction identity failed")
    require(crossover == coefficient_crossover, "Crossover identity failed at numerical boundary")
    return {"t": t, "coefficients": coeff, "reconstructed_t": reconstructed,
        "maximum_reconstruction_absolute_error": max(errors), "H": h,
        "H_equals_four_bCV": True, "H_equals_sum_signed_margins": True,
        "author_signed_margins": margins, "minimum_author_signed_margin": min_margin,
        "aligned_inputs": sum(margins[c][v] > 0 for c, v in cells),
        "tied_inputs": sum(margins[c][v] == 0 for c, v in cells),
        "all_four_aligned": min_margin > 0, "effect_crossover": crossover,
        "crossover_equivalence_verified": True,
        "crossover_margin": coeff["bCV"] - abs(coeff["bV"])}


def shifted_score(s, absent):
    require(set(absent) == set(CONTEXT), "Incomplete absent context grid")
    return {c: {v: finite(s[c][v]) - finite(absent[c]) for v in CUE} for c in CONTEXT}


def coefficient_change(first, second):
    delta = {k: finite(second["coefficients"][k]) - finite(first["coefficients"][k]) for k in COEFFICIENTS}
    energies = {k: value * value for k, value in delta.items()}
    energy = math.fsum(energies.values())
    cell_energy = mean((second["t"][c][v] - first["t"][c][v]) ** 2 for c in CONTEXT for v in CUE)
    require(close(energy, cell_energy), "Orthogonal squared-shift identity failed")
    return {"coefficient_differences": delta, "squared_shift_energy_by_coefficient": energies,
        "mean_squared_cell_shift": cell_energy,
        "energy_shares": {k: value / energy if energy else None for k, value in energies.items()},
        "zero_shift": energy == 0,
        "interpretation": "orthogonal_squared_change_decomposition_not_causal_explained_fraction"}


def threshold_flips(first, second, threshold):
    finite(threshold)
    require(threshold >= 0, "Negative flip threshold")
    cells = [(c, v) for c in CONTEXT for v in CUE]
    eligible = [(c, v) for c, v in cells if abs(first["t"][c][v]) >= threshold and abs(second["t"][c][v]) >= threshold]
    return {"threshold": threshold, "available_inputs": 4, "eligible_inputs": len(eligible),
        "strict_sign_flips": sum(first["t"][c][v] * second["t"][c][v] < 0 for c, v in eligible),
        "eligible_inputs_with_tie": sum(first["t"][c][v] == 0 or second["t"][c][v] == 0 for c, v in eligible)}


def build_decompositions(block_reports, blocks):
    require(len(blocks) == 24 and len({b["block_id"] for b in blocks}) == 24, "Expected 24 distinct scenarios")
    families = Counter(b["family"] for b in blocks)
    require(len(families) == 6 and set(families.values()) == {4}, "Expected six four-scenario families")
    lookup = {b["block_id"]: b for b in blocks}
    expected = {(p, c, b) for p in PAIR_IDS for c in CARRIERS for b in lookup}
    seen, output = set(), []
    for row in block_reports:
        key = row["pair_id"], row["carrier"], row["block_id"]
        require(key in expected and key not in seen, "Unexpected or duplicate decomposition row")
        seen.add(key)
        block = lookup[row["block_id"]]
        require(row["complete"] is True and row["family"] == block["family"], "Missing/changed scenario data")
        result = decompose(row["s"], block["eta"])
        require(close(result["H"], finite(row["H"])) and result["all_four_aligned"] == row["all_four_aligned"]
                and result["effect_crossover"] == row["effect_crossover"], "Saved block summary differs")
        output.append({**{k: row[k] for k in ("pair_id", "carrier", "block_id", "family")}, "eta": block["eta"], **result})
    require(seen == expected, "Incomplete fixed 144-table grid")
    return output


def summarize(decompositions, blocks):
    indexed = {(r["pair_id"], r["carrier"], r["block_id"]): r for r in decompositions}
    families = sorted({b["family"] for b in blocks})
    per_pair, leave_out = {}, []
    for pair in PAIR_IDS:
        per_pair[pair] = {}
        for carrier in CARRIERS:
            rr = [indexed[pair, carrier, b["block_id"]] for b in blocks]
            per_pair[pair][carrier] = {
                "blocks": 24, "inputs": 96, "mean_H": mean(r["H"] for r in rr),
                "H_positive_blocks": sum(r["H"] > 0 for r in rr),
                "H_negative_blocks": sum(r["H"] < 0 for r in rr),
                "H_zero_blocks": sum(r["H"] == 0 for r in rr),
                "effect_crossover_blocks": sum(r["effect_crossover"] for r in rr),
                "all_four_aligned_blocks": sum(r["all_four_aligned"] for r in rr),
                "aligned_inputs": sum(r["aligned_inputs"] for r in rr),
                "tied_inputs": sum(r["tied_inputs"] for r in rr),
                "aligned_inputs_per_block_histogram": dict(sorted(Counter(r["aligned_inputs"] for r in rr).items())),
                "mean_minimum_signed_margin": mean(r["minimum_author_signed_margin"] for r in rr),
                "coefficient_means": {k: mean(r["coefficients"][k] for r in rr) for k in COEFFICIENTS},
                "coefficient_median_absolute_values": {k: statistics.median(abs(r["coefficients"][k]) for r in rr) for k in COEFFICIENTS}}
            for family in families:
                retained = [r for r in rr if r["family"] != family]
                require(len(retained) == 20, "Leave-family-out denominator changed")
                leave_out.append({"pair_id": pair, "carrier": carrier, "omitted_family": family,
                    "retained_families": [f for f in families if f != family], "retained_blocks": 20,
                    "mean_H": mean(r["H"] for r in retained)})
    stability, stability_summaries = [], {}
    for carrier in CARRIERS:
        counts = Counter()
        carrier_rows = []
        for b in blocks:
            rr = [indexed[p, carrier, b["block_id"]] for p in PAIR_IDS]
            states = []
            for c in CONTEXT:
                for v in CUE:
                    margins = [r["author_signed_margins"][c][v] for r in rr]
                    classification = ("stable_correct" if min(margins) > 0 else "stable_wrong" if max(margins) < 0
                        else "stable_tie" if all(value == 0 for value in margins) else "mixed")
                    counts[classification] += 1
                    counts["inputs_with_any_tie"] += any(value == 0 for value in margins)
                    states.append({"context": c, "cue": v, "margins_by_pair": margins, "class": classification})
            minimum = min(r["minimum_author_signed_margin"] for r in rr)
            record = {"carrier": carrier, "block_id": b["block_id"], "family": b["family"],
                "H_by_pair": [r["H"] for r in rr], "H_positive_all_pairs": all(r["H"] > 0 for r in rr),
                "effect_crossover_all_pairs": all(r["effect_crossover"] for r in rr),
                "minimum_margin_across_all_pairs_and_inputs": minimum, "all_four_aligned_all_pairs": minimum > 0,
                "input_states": states}
            stability.append(record)
            carrier_rows.append(record)
        stability_summaries[carrier] = {"blocks": 24, "inputs": 96,
            **{k: counts[k] for k in ("stable_correct", "stable_wrong", "stable_tie", "mixed", "inputs_with_any_tie")},
            "H_positive_all_pairs_blocks": sum(r["H_positive_all_pairs"] for r in carrier_rows),
            "effect_crossover_all_pairs_blocks": sum(r["effect_crossover_all_pairs"] for r in carrier_rows),
            "all_four_aligned_all_pairs_blocks": sum(r["all_four_aligned_all_pairs"] for r in carrier_rows),
            "mean_minimum_margin_across_pairs": mean(r["minimum_margin_across_all_pairs_and_inputs"] for r in carrier_rows)}
    changes, pairwise = [], []
    for carrier in CARRIERS:
        for first, second in itertools.combinations(PAIR_IDS, 2):
            cc, flips = [], []
            for b in blocks:
                x, y = (indexed[p, carrier, b["block_id"]] for p in (first, second))
                change = {"carrier": carrier, "block_id": b["block_id"], "pair_from": first, "pair_to": second,
                    **coefficient_change(x, y)}
                cc.append(change)
                changes.append(change)
                flips.append([threshold_flips(x, y, threshold) for threshold in THRESHOLDS])
            energies = {k: math.fsum(r["squared_shift_energy_by_coefficient"][k] for r in cc) for k in COEFFICIENTS}
            total_energy = math.fsum(energies.values())
            pairwise.append({"carrier": carrier, "pair_from": first, "pair_to": second, "blocks": 24, "inputs": 96,
                "mean_absolute_coefficient_changes": {k: mean(abs(r["coefficient_differences"][k]) for r in cc) for k in COEFFICIENTS},
                "pooled_squared_shift_energies": energies,
                "pooled_energy_shares": {k: value / total_energy if total_energy else None for k, value in energies.items()},
                "thresholded_flips": [{"threshold": threshold, **{k: sum(f[i][k] for f in flips)
                    for k in ("available_inputs", "eligible_inputs", "strict_sign_flips", "eligible_inputs_with_tie")}}
                    for i, threshold in enumerate(THRESHOLDS)]})
    return {"per_pair": per_pair, "all_pair_stability": stability, "all_pair_stability_summary": stability_summaries,
        "pairwise_wording_changes": pairwise, "coefficient_change_rows": changes,
        "leave_one_family_out": leave_out,
        "energy_share_interpretation": "Algebraic squared score-change shares; not causal explained fractions or population variance attribution.",
        "leave_one_family_out_interpretation": "All six omissions retained as descriptive sensitivity; no independent replication or uncertainty estimate."}


def absent_diagnostics(emoji_rows, blocks, decompositions, scorer):
    lookup = {b["block_id"]: b for b in blocks}
    expected = {(b, c, k) for b in lookup for c in CONTEXT for k in CUE}
    absent = {}
    for r in emoji_rows:
        if r["variant"] != "absent":
            continue
        key = r["block_id"], r["context"], r["candidate"]
        require(key in expected and key not in absent and r["status"] == "completed", "Invalid/duplicate/unrun absent cell")
        b = lookup[r["block_id"]]
        require(r["prompt"] == b[f"context_{r['context']}"].replace("{emoji}", "") and
            r["continuation"] == b[f"candidate_{r['candidate']}"] and r["eta"] == b["eta"], "Changed absent stimulus")
        absent[key] = scorer(r)
    require(set(absent) == expected, "Incomplete original-only 96-cell absent grid")
    output = []
    for r in decompositions:
        if r["pair_id"] != "original":
            continue
        b = lookup[r["block_id"]]
        reference = {c: absent[b["block_id"], c, "a"] - absent[b["block_id"], c, "b"] for c in CONTEXT}
        s = {c: {v: b["eta"] * r["t"][c][v] for v in CUE} for c in CONTEXT}
        adjusted = decompose(shifted_score(s, reference), b["eta"])
        require(close(adjusted["H"], r["H"]) and all(close(adjusted["coefficients"][k], r["coefficients"][k]) for k in ("bV", "bCV")),
            "Absent-relative interaction invariance failed")
        output.append({"carrier": r["carrier"], "block_id": b["block_id"], "family": b["family"],
            "absent_s_by_context": reference, "H_invariance_verified": True,
            "raw_to_relative_strict_sign_flips": sum(r["t"][c][v] * adjusted["t"][c][v] < 0 for c in CONTEXT for v in CUE),
            "relative_decomposition": adjusted})
    return {"pair_id": "original", "unique_absent_sequence_scores": 96,
        "additional_pair_absent_scores": "not_acquired_not_imputed", "rows": output,
        "per_carrier": {carrier: {"inputs": 96,
            "aligned_inputs": sum(r["relative_decomposition"]["aligned_inputs"] for r in output if r["carrier"] == carrier),
            "tied_inputs": sum(r["relative_decomposition"]["tied_inputs"] for r in output if r["carrier"] == carrier),
            "all_four_aligned_blocks": sum(r["relative_decomposition"]["all_four_aligned"] for r in output if r["carrier"] == carrier),
            "raw_to_relative_strict_sign_flips": sum(r["raw_to_relative_strict_sign_flips"] for r in output if r["carrier"] == carrier)} for carrier in CARRIERS},
        "interpretation": "A different cue-relative response-score estimand; not corrected accuracy, a pure prior, or a causal attribution. H is invariant by construction."}


def token_prefix_split(a, b, scorer):
    require(a["status"] == b["status"] == "completed", "Unrun prefix cell")
    require(a["prompt"] == b["prompt"] and a["prompt_token_ids"] == b["prompt_token_ids"], "Different candidate conditioning prompts")
    totals = [scorer(r) for r in (a, b)]
    ids = [r["candidate_token_ids"] for r in (a, b)]
    require(all(len(ids[i]) == len(r["candidate_token_logprobs"]) == r["candidate_token_count"] and ids[i]
                and all(type(t) is int and t >= 0 for t in ids[i]) for i, r in enumerate((a, b))), "Invalid candidate token sequence")
    length = 0
    for x, y in zip(*ids):
        if x != y:
            break
        length += 1
    prefix = math.fsum(a["candidate_token_logprobs"][:length]) - math.fsum(b["candidate_token_logprobs"][:length])
    tail = math.fsum(a["candidate_token_logprobs"][length:]) - math.fsum(b["candidate_token_logprobs"][length:])
    total = totals[0] - totals[1]
    require(close(total, prefix + tail), "Prefix/tail additive identity failed")
    return {"shared_prefix_token_count": length, "shared_prefix_token_ids": ids[0][:length],
        "s_prefix": prefix, "s_tail": tail, "s_total": total,
        "prefix_per_token_probability_residuals": [x - y for x, y in zip(a["candidate_token_logprobs"][:length], b["candidate_token_logprobs"][:length])]}


def prefix_diagnostics(new, emoji, word, decompositions, scorer):
    indexed = {}
    for carrier, old in (("emoji", emoji), ("word", word)):
        for r in old:
            if r["variant"] not in CUE:
                continue
            key = "original", carrier, r["block_id"], r["context"], r["variant"], r["candidate"]
            require(key not in indexed, "Duplicate original prefix cell")
            indexed[key] = r
    for r in new:
        key = r["pair_id"], r["carrier_kind"], r["block_id"], r["context"], r["variant"], r["candidate"]
        require(key not in indexed, "Duplicate additional prefix cell")
        indexed[key] = r
    require(len(indexed) == 1152, "Prefix denominator changed")
    output, inputs = [], []
    for r in decompositions:
        scores = {"prefix": {c: {} for c in CONTEXT}, "tail": {c: {} for c in CONTEXT}}
        for c in CONTEXT:
            for v in CUE:
                base = r["pair_id"], r["carrier"], r["block_id"], c, v
                split = token_prefix_split(indexed[(*base, "a")], indexed[(*base, "b")], scorer)
                inputs.append({"pair_id": r["pair_id"], "carrier": r["carrier"], "block_id": r["block_id"], "context": c, "cue": v, **split})
                for part in scores:
                    scores[part][c][v] = split[f"s_{part}"]
        parts = {part: decompose(s, r["eta"]) for part, s in scores.items()}
        require(close(r["H"], parts["prefix"]["H"] + parts["tail"]["H"]), "Prefix/tail H identity failed")
        output.append({"pair_id": r["pair_id"], "carrier": r["carrier"], "block_id": r["block_id"],
            "H_total": r["H"], "H_prefix": parts["prefix"]["H"], "H_tail": parts["tail"]["H"],
            "H_additivity_verified": True})
    return {"input_splits": inputs, "block_H_splits": output,
        "maximum_absolute_prefix_s_residual": max(abs(r["s_prefix"]) for r in inputs),
        "maximum_absolute_prefix_H_residual": max(abs(r["H_prefix"]) for r in output),
        "nonzero_prefix_s_residual_inputs": sum(r["s_prefix"] != 0 for r in inputs),
        "interpretation": "Exact shared token-ID prefix within the same input/candidate pair only. Remaining tails have no asserted semantic or positional alignment. Saved prefix probability residuals are retained, not set to zero; their computational source has not been isolated."}


def load_existing_analyzer(root, expected_sha256):
    path = root / "scripts/summarize_contextual_emoji_candidate_wording_v0.py"
    require(digest(path) == expected_sha256, "Existing independent-analyzer source differs")
    spec = importlib.util.spec_from_file_location("glyphprobe_saved_wording_analysis", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def analyze(root, run_dir, specification):
    root, run_dir, specification = safe(root), safe(run_dir), safe(specification)
    saved_path = run_dir / "independent_analysis.json"
    require(digest(saved_path) == SAVED_ANALYSIS_SHA256, "Saved independent-analysis pin differs")
    saved = read(saved_path)
    existing, existing_path = load_existing_analyzer(root, saved["analyzer_sha256"])
    recomputed = existing.analyze(run_dir, specification, root)
    require(recomputed == saved, "Exact independent-analysis recomputation differs")
    require(saved["new_cell_status_counts"] == {"completed": 768} and saved["parity_status_counts"] == {"completed": 384}
            and saved["historical_384_cell_exact_parity"] is True, "Fixed complete acquisition required")
    spec = existing.read(specification)
    raw_paths = {name: root / spec["config"]["references"][name]["path"] for name in ("emoji_cells", "word_cells")}
    emoji, word = (existing.rows(raw_paths[name]) for name in ("emoji_cells", "word_cells"))
    new = existing.rows(run_dir / "cells.jsonl")
    decompositions = build_decompositions(saved["blocks"], spec["blocks"])
    inputs = {"specification": specification, "saved_independent_analysis": saved_path,
        "independent_analyzer_source": existing_path,
        **{name: root / spec["config"]["references"][name]["path"] for name in existing.PINS},
        "candidate_panel": root / spec["config"]["candidate_panel"]["path"],
        **{name: run_dir / name for name in ("cells.jsonl", "parity.jsonl", "run_started.json", "run_completed.json", "runtime.json", "placement.json", "occupancy_checks.json")}}
    report = {"protocol_id": PROTOCOL, "status": "complete_posthoc_saved_score_analysis", "posthoc": True,
        "confirmatory": False, "inferential_statistics": False, "new_model_forwards": 0, "model_loaded": False,
        "tokenizer_loaded": False, "probabilities_reexecuted": False, "remote_calls": 0,
        "human_validated_labels": False, "causal_attribution": False,
        "provenance": {"analyzer_sha256": digest(Path(__file__)), "exact_saved_analysis_recomputation": True,
            "inputs": {name: {"path": str(path.relative_to(root)) if path.is_relative_to(root) else str(path), "sha256": digest(path)} for name, path in inputs.items()}},
        "denominators": {"development_scenarios": 24, "families": 6, "candidate_pairs": 3, "carriers": 2,
            "decomposition_tables": 144, "crossed_candidate_comparison_inputs": 576,
            "unique_scientific_sequence_scores": 1248, "unique_crossed_sequence_scores": 1152,
            "historical_crossed_sequence_scores": 384, "additional_wording_sequence_scores": 768,
            "original_absent_sequence_scores": 96, "new_pair_absent_sequence_scores": 0,
            "engineering_historical_parity_forwards_excluded_from_scientific_n": 384,
            "wording_acquisition_total_forward_attempts_including_parity": 1152,
            "missing_scientific_sequence_scores": 0,
            "note": "Unique scientific cell identities across three acquisitions, not independent observations; repeated candidates and engineering parity do not increase the 24-scenario sample."},
        "definitions": {"C": {"p": -1, "q": 1}, "V": {"a": -1, "b": 1}, "t": "eta * (log P(A|input) - log P(B|input))",
            "expansion": "t = b0 + bC*C + bV*V + bCV*C*V", "H": "4*bCV = sum(C*V*t)",
            "crossover": "bCV > abs(bV)", "all_four_author_aligned": "min(C*V*t) > 0",
            "units": "natural-log sequence-probability differences; no length normalization",
            "identity_check_tolerance": TOLERANCE, "historical_probability_parity_tolerance": 0,
            "flip_thresholds": list(THRESHOLDS), "threshold_interpretation": "Both absolute t values must reach the threshold; zero is a tie, never a strict sign flip.",
            "b0_interpretation": "Average of four contextual cue-bearing scores, not a context-free language prior."},
        "decompositions": decompositions, **summarize(decompositions, spec["blocks"]),
        "original_absent_relative": absent_diagnostics(emoji, spec["blocks"], decompositions, existing.total),
        "candidate_prefix_tail": prefix_diagnostics(new, emoji, word, decompositions, existing.total)}
    return report


def write_output(path, report):
    destination = safe(path)
    require(not destination.exists(), "Refusing to overwrite existing output")
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(not safe(args.output).exists(), "Refusing to overwrite existing output")
        report = analyze(args.root, args.run_dir, args.specification)
        write_output(args.output, report)
        print(json.dumps({"status": report["status"], "new_model_forwards": 0,
            "decomposition_tables": len(report["decompositions"]), "output_sha256": digest(args.output)}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, OverflowError) as error:
        print(json.dumps({"status": "analysis_failed", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
