#!/usr/bin/env python3
"""Build and execute the bilingual, CPU-only saved-score research companion.

Optional presentation dependencies: nbformat, nbclient, ipykernel.
The scientific analyzer itself remains standard-library-only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import textwrap

import nbformat
from nbclient import NotebookClient

ANALYSIS_SHA256 = "806400d78608cc2999f9480d3b82b24a45fd4739f85f52d82a21f3f7cb4b39e8"


def build():
    cells = []

    def md(source):
        cells.append(nbformat.v4.new_markdown_cell(textwrap.dedent(source).strip()))

    def code(source):
        cells.append(nbformat.v4.new_code_cell(textwrap.dedent(source).strip()))

    md("""
    # Contextual cue interactions and response choices / 文脈的な交互作用と応答選択

    ## tl;dr

    Saved-score, post-hoc analysis, 2026-10-07. No model, tokenizer, or GPU calls.
    保存済みスコアの事後解析。モデル・tokenizer・GPUを呼ばない。

    Positive interaction across all three pairs: emoji 19/24, word 22/24.
    All-four author alignment across all pairs: 0/24 for both carriers.
    Polarity varies across pairs on 52/96 emoji and 56/96 word inputs.
    全候補組でH正でも、全入力で安定した著者ラベル一致は保証されない。

    Shared-prefix score residuals occur in 355/576 comparisons; their cause remains
    unresolved. Tail-only sensitivity preserves all 144 H signs, while several
    near-boundary decisions change. This is a numerical-consistency gate for future
    work, not a repaired scoring method.
    共通接頭列の数値差は未解決。残りの部分だけを見る診断でも全H符号は保たれるが、
    境界付近の判定は変わる。採点の修復とは扱わない。

    [Research note / English](../docs/CONTEXTUAL_EMOJI_MEASUREMENT_RESEARCH_NOTE_V0.md) ·
    [研究ノート / 日本語](../docs/CONTEXTUAL_EMOJI_MEASUREMENT_RESEARCH_NOTE_V0.ja.md)
    """)
    md("""
    ## Context & Methods

    Reconstruct the fixed 24-scenario, six-family development grid from pinned raw
    scores and the prior independent analysis. 1,248 scientific sequence scores
    include 1,152 crossed and 96 absent-cue scores; 384 parity forwards are engineering
    repeats. No population inference or fresh confirmation is performed.
    24開発課題・6課題群を再構成。1,248スコアと独立課題数を区別し、384再現検査は除く。

    ### Key Assumptions

    Author labels and candidate equivalence have no independent human validation.
    Repeated cue pairs/families are not independent replications. Candidate pairs
    change vocabulary, length, morphology, and specificity together. Full-sequence
    scores remain primary. The factorial expansion is an identity, not causal
    component attribution. No protected historical bank is read.
    著者ラベル・候補同等性は未検証。語彙・長さなどが同時に変わる。分解は恒等式であり
    因果同定ではない。保護された過去のbankは読み込まない。

    Run with a Python 3 kernel from the repository root or its `notebooks/` directory.
    Code cells require only the standard library. Building/executing this artifact
    uses `nbformat`, `nbclient`, and `ipykernel`; exact presentation versions are
    stored in notebook metadata. No credentials or remote services are required.
    repo直下かnotebooks/でPython 3 kernelから全セルを順に実行できる。
    """)
    md("""
    ## Data

    ### 1. Locate the repository and verify the analysis digest / 解析記録を照合
    """)
    code(f"""
    from pathlib import Path
    import hashlib, importlib.util, json, math, sys
    roots = [Path.cwd(), *Path.cwd().parents]
    root = next(p for p in roots if (p / "scripts/analyze_contextual_emoji_measurement_v0.py").is_file())
    analysis_path = root / "validation/contextual_emoji_measurement_v0/analysis.json"
    actual_sha = hashlib.sha256(analysis_path.read_bytes()).hexdigest()
    assert actual_sha == {ANALYSIS_SHA256!r}
    report = json.loads(analysis_path.read_text())
    print("Analysis SHA-256:", actual_sha)
    print("Status:", report["status"], "| new forwards:", report["new_model_forwards"])
    """)
    md("### 2. Recompute from raw records / rawから再計算")
    code("""
    source = root / "scripts/analyze_contextual_emoji_measurement_v0.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == report["provenance"]["analyzer_sha256"]
    module_spec = importlib.util.spec_from_file_location("measurement", source)
    measurement = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(measurement)
    run_dir = root / "validation/contextual_emoji_candidate_wording_v0/runtime_fix/shared_trial"
    specification = run_dir.parent / "specification.json"
    rebuilt = measurement.analyze(root, run_dir, specification)
    assert json.loads(json.dumps(rebuilt)) == report
    assert len(report["decompositions"]) == 144
    assert report["denominators"]["missing_scientific_sequence_scores"] == 0
    print("Full raw/spec/runtime/parity recomputation: PASS")
    for key in ("development_scenarios", "families", "unique_scientific_sequence_scores",
                "unique_crossed_sequence_scores", "original_absent_sequence_scores",
                "engineering_historical_parity_forwards_excluded_from_scientific_n"):
        print(key, report["denominators"][key])
    """)
    md("""
    ## Results

    ### 3. Interaction, crossover, and absolute choice / 異なる3指標

    H = 4 bCV = sum of four author-oriented margins. Crossover iff bCV > |bV|.
    All-four alignment iff minimum margin > 0. This last condition is stronger.
    著者ラベル方向の平均marginはH/4と同じ量。独立の補強証拠に数えない。
    """)
    code("""
    print("pair | carrier | mean H | H+ | crossover | aligned/96 | all-four/24")
    for pair in measurement.PAIR_IDS:
        for carrier in measurement.CARRIERS:
            row = report["per_pair"][pair][carrier]
            print(pair, carrier, round(row["mean_H"], 4), row["H_positive_blocks"],
                  row["effect_crossover_blocks"], row["aligned_inputs"], row["all_four_aligned_blocks"], sep=" | ")
    assert all(d["maximum_reconstruction_absolute_error"] <= 1e-11 for d in report["decompositions"])
    print("144 four-score identities: PASS")
    """)
    md("### 4. Track the same inputs across all pairs / 入力単位の安定性")
    code("""
    for carrier, row in report["all_pair_stability_summary"].items():
        print(carrier, {"H_positive_all_pairs/24": row["H_positive_all_pairs_blocks"],
                        "crossover_all_pairs/24": row["effect_crossover_all_pairs_blocks"],
                        "all_four_all_pairs/24": row["all_four_aligned_all_pairs_blocks"],
                        "always_author_aligned/96": row["stable_correct"],
                        "always_author_misaligned/96": row["stable_wrong"],
                        "variable_polarity/96": row["mixed"]})
    assert all(row["all_four_aligned_all_pairs_blocks"] == 0 for row in report["all_pair_stability_summary"].values())
    """)
    md("""
    ### 5. Response offset, coefficient changes, and margin thresholds / 係数変化

    b0 is the observed table-wide offset, not an identified pretraining prior.
    Squared-change shares are algebraic accounting, not causal explained fractions.
    Thresholds are post-hoc descriptive filters, never study eligibility rules.
    共通ずれを純粋なpriorと同定しない。閾値を事後的な適格性規則にしない。
    """)
    code("""
    print("carrier | comparison | mean absolute change [b0,bC,bV,bCV] | flips/eligible at 1 nat")
    for row in report["pairwise_wording_changes"]:
        threshold = next(t for t in row["thresholded_flips"] if t["threshold"] == 1)
        print(row["carrier"], row["pair_from"] + " -> " + row["pair_to"],
              [round(row["mean_absolute_coefficient_changes"][k], 4) for k in measurement.COEFFICIENTS],
              f'{threshold["strict_sign_flips"]}/{threshold["eligible_inputs"]}', sep=" | ")
    """)
    md("### 6. Omit each family in turn / 課題群ごとの感度（母集団推論ではない）")
    code("""
    assert len(report["leave_one_family_out"]) == 36
    for pair in measurement.PAIR_IDS:
        for carrier in measurement.CARRIERS:
            values = [r["mean_H"] for r in report["leave_one_family_out"]
                      if r["pair_id"] == pair and r["carrier"] == carrier]
            assert len(values) == 6
            print(pair, carrier, "six-omission mean H range:", round(min(values), 4), round(max(values), 4))
    print("All 36 means positive:", all(r["mean_H"] > 0 for r in report["leave_one_family_out"]))
    """)
    md("""
    ### 7. Original absent-cue relative scores / 手がかりなしとの相対量

    Subtracting s(context, absent) leaves H and bV unchanged by algebra.
    The new margin is a different estimand, not corrected accuracy.
    差し引きでHは変わらない。候補選択の別の評価量として扱う。
    """)
    code("""
    for carrier, row in report["original_absent_relative"]["per_carrier"].items():
        original = report["per_pair"]["original"][carrier]
        print(carrier, "aligned raw -> relative:", original["aligned_inputs"], row["aligned_inputs"],
              "| all-four:", original["all_four_aligned_blocks"], row["all_four_aligned_blocks"],
              "| polarity changes:", row["raw_to_relative_strict_sign_flips"])
    assert all(r["H_invariance_verified"] for r in report["original_absent_relative"]["rows"])
    """)
    md("""
    ### 8. Shared-prefix numerical issue / 共通接頭列の数値差

    Prefix and tail add exactly, but shared-prefix probabilities differ for some
    separate full-sequence executions. Cause unresolved; do not zero them silently.
    接頭列と残りの加算性を確認する。原因は未同定で、差を勝手に0にしない。
    """)
    code("""
    prefix = report["candidate_prefix_tail"]
    print("Nonzero prefix residuals:", prefix["nonzero_prefix_s_residual_inputs"], "/", len(prefix["input_splits"]))
    print("Maximum absolute prefix s:", prefix["maximum_absolute_prefix_s_residual"])
    print("Maximum absolute prefix H:", prefix["maximum_absolute_prefix_H_residual"])
    h_changes = sum((r["H_total"] > 0) != (r["H_tail"] > 0) for r in prefix["block_H_splits"])
    assert h_changes == 0
    print("H sign changes under saved-score tail diagnostic:", h_changes, "/ 144")
    """)
    md("### 9. Reconcile length and decision changes / 長さとの対応・判定変化を再集計")
    code("""
    raw_index = {}
    source_specs = [("original", "emoji", root / report["provenance"]["inputs"]["emoji_cells"]["path"]),
                    ("original", "word", root / report["provenance"]["inputs"]["word_cells"]["path"]),
                    (None, None, run_dir / "cells.jsonl")]
    for pair, carrier, path in source_specs:
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["variant"] not in ("a", "b"):
                continue
            key = (pair or row["pair_id"], carrier or row["carrier_kind"], row["block_id"],
                   row["context"], row["variant"], row["candidate"])
            assert key not in raw_index
            raw_index[key] = row
    assert len(raw_index) == 1152
    length_groups = {"equal": {"pairs": 0, "nonzero": 0}, "unequal": {"pairs": 0, "nonzero": 0}}
    splits = {}
    for row in prefix["input_splits"]:
        key = (row["pair_id"], row["carrier"], row["block_id"], row["context"], row["cue"])
        a, b = [raw_index[(*key, c)] for c in ("a", "b")]
        group = "equal" if a["candidate_token_count"] == b["candidate_token_count"] else "unequal"
        length_groups[group]["pairs"] += 1
        length_groups[group]["nonzero"] += row["s_prefix"] != 0
        splits[key] = row
    changes = {"absolute_preference": 0, "crossover": 0, "all_four_alignment": 0, "H_sign": 0}
    decision_cases = []
    for row in report["decompositions"]:
        key = (row["pair_id"], row["carrier"], row["block_id"])
        tail_s = {c: {v: splits[(*key, c, v)]["s_tail"] for v in ("a", "b")} for c in ("p", "q")}
        tail = measurement.decompose(tail_s, row["eta"])
        flips = sum(splits[(*key, c, v)]["s_total"] * tail_s[c][v] < 0 for c in ("p", "q") for v in ("a", "b"))
        changes["absolute_preference"] += flips
        differences = {"crossover": row["effect_crossover"] != tail["effect_crossover"],
                       "all_four_alignment": row["all_four_aligned"] != tail["all_four_aligned"],
                       "H_sign": (row["H"] > 0) != (tail["H"] > 0)}
        for name, changed in differences.items():
            changes[name] += changed
        if flips or any(differences.values()):
            decision_cases.append({"case": key, "preference_flips": flips, **differences})
    assert length_groups == {"equal": {"pairs": 56, "nonzero": 0}, "unequal": {"pairs": 520, "nonzero": 355}}
    assert changes == {"absolute_preference": 1, "crossover": 2, "all_four_alignment": 1, "H_sign": 0}
    print("Length groups:", json.dumps(length_groups, sort_keys=True))
    print("Decision changes (input denominator 576; block denominator 144):", changes)
    for case in decision_cases:
        print(case)
    """)
    md("""
    ## Takeaways

    Arithmetic validation passed on the complete saved grid. Share with caveats:
    semantic labels, candidate equivalence, and cross-shape numerical consistency
    remain open. Positive H alone cannot establish reliable interpretation selection.
    全保存データの計算を検証した。意味的ラベル・候補同等性・形状間の数値整合性は未解決。

    Next: a bounded numerical diagnostic, independent human validation, genuinely
    new families with a prespecified endpoint, then natural-state bidirectional
    interventions with word and positional controls. No new GPU acquisition was
    launched by this notebook. Candidate length association is not proof of a
    BF16 cause; tail-only scoring is not an accuracy repair.
    次は小さな数値診断、人による検証、新課題群、その後に通常状態の因果検査。

    [Next plan / English](../docs/CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md) ·
    [次の計画 / 日本語](../docs/CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.ja.md)
    """)
    for i, cell in enumerate(cells):
        cell["id"] = f"measurement-{i:02d}"
    return nbformat.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0]},
        "glyphprobe": {"analysis_sha256": ANALYSIS_SHA256, "new_model_forwards": 0,
            "execution": "nbclient_top_to_bottom", "posthoc": True,
            "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "presentation_dependencies": {name: importlib.metadata.version(name)
                                           for name in ("nbformat", "nbclient", "ipykernel")}}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Refusing to overwrite an existing notebook; use a new output path")
    notebook = build()
    nbformat.validate(notebook)
    NotebookClient(notebook, timeout=120, kernel_name="python3", allow_errors=False,
                   resources={"metadata": {"path": str(args.root.resolve())}}).execute()
    nbformat.validate(notebook)
    code_cells = [c for c in notebook.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in code_cells)
    assert not any(o.output_type == "error" for c in code_cells for o in c.outputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)
    print(json.dumps({"status": "executed_top_to_bottom", "code_cells": len(code_cells),
        "new_model_forwards": 0, "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
