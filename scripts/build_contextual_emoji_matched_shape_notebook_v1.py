#!/usr/bin/env python3
"""Build and execute a saved-record, bilingual matched-shape reassessment notebook."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import textwrap

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager


def build(root, specification, run_dir, report_path):
    root = root.resolve()
    relative = [p.resolve().relative_to(root).as_posix() for p in (specification, run_dir, report_path)]
    report = json.loads(report_path.read_text())
    pin = hashlib.sha256(report_path.read_bytes()).hexdigest()
    cells = []
    def md(text):
        cells.append(nbformat.v4.new_markdown_cell(textwrap.dedent(text).strip()))
    def code(text):
        cells.append(nbformat.v4.new_code_cell(textwrap.dedent(text).strip()))

    md(f"""
    # Paired matched-shape scoring / 候補の形状をそろえた再採点

    ## tl;dr

    Saved result status: **{report['status']}**.
    Complete bounded gate passed: **{report['bounded_numerical_gate_passed']}**.
    保存済みの結果と検査状況を下のセルで独立に再計算する。

    The intended grid contains 1,248 existing sequence scores, 624 candidate pairs,
    and 24 author-defined development scenarios. The additional 64 sentinel calls
    are engineering checks. This notebook adds no model calls or new scenarios.
    再評価対象は既存1,248スコア・624候補組・24開発課題。再現確認64回とは分ける。
    このnotebookはモデルを呼ばず、標本を追加しない。

    [Protocol / English](../docs/CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.md) ·
    [仕様 / 日本語](../docs/CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.ja.md)
    """)
    md("""
    ## Context & Methods

    Compare old full-candidate logprob sums with paired right-padded scoring,
    using the same model/runtime and a common FP32 normalization rectangle.
    Preserve original and matched-shape scores side by side. Separate numerical,
    runtime, resource, and scientific-interpretation gates.
    元の全文採点と、候補組ごとに実行・正規化形状をそろえた採点を併記する。
    数値、実行環境、資源、科学的解釈をそれぞれ別に確認する。

    ### Key Assumptions

    These are exposed development scenarios, with author-defined labels and
    unvalidated candidate equivalence. All-four alignment is not human accuracy.
    Matching prefix hashes does not prove absolute probability accuracy or a
    BF16-specific cause. Word/emoji prompt geometry remains unmatched.
    著者ラベルと候補文の同等性は人による検証前。全4条件一致を正答率とは呼ばない。
    接頭列の一致から絶対精度やBF16固有の原因は証明できず、carrier間の位置差も残る。

    Run from the repository root or a descendant with Python 3. Code cells use
    only the standard library. Building/executing the notebook additionally needs
    nbformat, nbclient, ipykernel, and jupyter-client; versions are in metadata.
    リポジトリ内からPython 3で実行する。解析セルは標準ライブラリのみを使う。
    """)
    md("## Data\n\n### 1. Verify and replay receipts / 記録を照合して再検算")
    code(f"""
    from pathlib import Path
    import hashlib, importlib.util, json
    root = next(p for p in [Path.cwd(), *Path.cwd().parents]
                if (p / "scripts/analyze_contextual_emoji_matched_shape_v1.py").is_file())
    specification, run_dir, report_path = [root / p for p in {relative!r}]
    assert hashlib.sha256(report_path.read_bytes()).hexdigest() == {pin!r}
    report = json.loads(report_path.read_text())
    checker = root / "scripts/analyze_contextual_emoji_matched_shape_v1.py"
    assert hashlib.sha256(checker.read_bytes()).hexdigest() == report["provenance"]["checker_sha256"]
    module_spec = importlib.util.spec_from_file_location("matched_shape_checker", checker)
    validation = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(validation)
    rebuilt = validation.analyze(specification, run_dir, root)
    assert rebuilt == report
    print("Independent full receipt and analysis replay: PASS")
    print("Status:", report["status"])
    """)
    md("## Results\n\n### 2. Keep the gates separate / 検査ごとの結果")
    code("""
    for key in ("bounded_numerical_gate_passed", "numerical_gate_passed",
                "resource_gate_passed", "score_equalities_gate_passed",
                "full_runtime_identity_matches_historical", "implementation_identity_matches_prior_panel"):
        print(key, report[key])
    print("Counts:", json.dumps(report["counts"], indent=2))
    print("Resources:", json.dumps(report["resource_validation"], indent=2))
    assert report["counts"]["actual_forward_attempts"] <= 1312
    assert report["new_scientific_n"] == 0
    analysis = report["analysis"]
    complete = analysis["status"] == "complete_descriptive_development_grid"
    print("Analytical status:", analysis["status"])
    """)
    md("### 3. Formulation/carrier summaries / 候補組・carrier別の新旧比較")
    code("""
    if complete:
        assert analysis["sequence_scores"] == 1248 and analysis["input_pairs"] == 624
        assert analysis["crossed_inputs"] == 576 and analysis["shared_absent_inputs"] == 48
        assert len(analysis["block_tables"]) == 144
        for row in analysis["per_pair_carrier"]:
            print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    else:
        print("Incomplete grid: full-population comparisons are unavailable.")
    """)
    md("### 4. Every decision transition / 判定が動いた箇所")
    code("""
    if complete:
        print("Transition counts:", json.dumps(analysis["transition_counts"], indent=2))
        print("Maximum absolute crossed s change:", analysis["maximum_absolute_crossed_s_change"])
        print("Maximum absolute H change:", analysis["maximum_absolute_H_change"])
        for outcome, rows in analysis["transitions"].items():
            print(outcome, "changed rows:", len(rows), "(first 12 shown; all retained in JSON)")
            for row in rows[:12]:
                print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    else:
        print("No complete-grid transition claims.")
    """)
    md("### 5. Stability and absent-cue coverage / 安定性と対照の分母")
    code("""
    if complete:
        print("Across-formulation stability:", json.dumps(analysis["all_pair_stability"], indent=2))
        print("Absent coverage:", json.dumps(analysis["absent_coverage"], indent=2))
        print("Old nonzero prefix residuals:", analysis["old_nonzero_prefix_residuals"])
        print("All new 624 prefix residuals zero:", analysis["all_624_prefix_residuals_zero"])
        assert len(analysis["shared_absent_diagnostics"]) == 48
    print("Eligible as a separately versioned full-grid score record:",
          analysis["eligible_for_versioned_score_replacement"])
    """)
    md("""
    ## Takeaways

    Use the executed comparisons to distinguish numerical sensitivity from
    stable development findings. A failed resource, replay, or prefix gate stays
    failed even if all scientific rows were collected. No inference about new
    scenarios, human interpretation, emoji specificity, or causality follows here.
    実行済みの比較から、数値に敏感な判定と保たれた開発知見を分ける。取得が完了しても
    資源・再現・接頭列の条件に不合格なら採用しない。新課題、人の意味理解、emoji特異性、
    因果性についての検証にはならない。

    Next: specify blind human interpretation and candidate-equivalence assessment
    before new-family confirmation or natural-state causal acquisition.
    次は人による盲検評価の設計。未使用課題や自然状態の因果取得は、その後の段階である。
    """)
    notebook = nbformat.v4.new_notebook(cells=cells)
    notebook.metadata.update(
        kernelspec={"name": "python3", "display_name": "Python 3", "language": "python"},
        glyphprobe={"report_sha256": pin, "model_forwards": 0, "tokenizer_calls": 0,
                    "analysis_network_calls": 0, "kernel_transport": "ipc",
                    "presentation_dependencies": {k: importlib.metadata.version(k)
                        for k in ("nbformat", "nbclient", "ipykernel", "jupyter-client")}})
    return notebook


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "specification", "run-dir", "report", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite notebook")
    notebook = build(args.root, args.specification, args.run_dir, args.report)
    manager = KernelManager(kernel_name="python3", transport="ipc")
    try:
        NotebookClient(notebook, km=manager, timeout=120,
            resources={"metadata": {"path": str(args.root.resolve())}}).execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    nbformat.validate(notebook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)
    print(json.dumps({"notebook": str(args.output), "executed_code_cells":
                      sum(c.cell_type == "code" for c in notebook.cells),
                      "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
