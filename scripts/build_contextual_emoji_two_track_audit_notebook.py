#!/usr/bin/env python3
"""Build a model-free, choice-concealing receipt notebook using nbformat."""
import argparse
from pathlib import Path
import nbformat as nb

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('Notebook exists; preserve the earlier artifact')
    book=nb.v4.new_notebook()
    book.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
    book.cells=[
        nb.v4.new_markdown_cell('# Two-track development acquisition: mechanical audit\n\n## tl;dr\n\nThis notebook checks all planned model forwards without displaying model choices. It does not read human responses. The saved completion receipt is independently recalculated below.\n\n二系列の開発取得を全行検査する。モデルの回答傾向は表示せず、人の回答も読まない。'),
        nb.v4.new_markdown_cell('## Context & Methods\n\n24 reused scenarios, six families, 1,632 candidate pairs, 3,264 candidate sequences and 32 exact-replay sentinels.\n\n### Key Assumptions\n\nEqual-shape numerical consistency is an engineering condition, not semantic or causal validation. Revised stimuli do not add independent scenario N. No claim of independent human validation follows. The independent validator reconstructs padding geometry and token sums from raw records rather than trusting the runner verdict.'),
        nb.v4.new_code_cell('from pathlib import Path\nimport importlib.util\nimport json\n\nroot = Path.cwd().resolve()\nif not (root / "scripts/audit_contextual_emoji_two_track_v1.py").exists():\n    raise ValueError("Execute with the repository root as the working directory")\npath = root / "scripts/audit_contextual_emoji_two_track_v1.py"\nloader = importlib.util.spec_from_file_location("two_track_receipt_audit", path)\nauditor = importlib.util.module_from_spec(loader)\nloader.loader.exec_module(auditor)'),
        nb.v4.new_markdown_cell('## Data\n\nThe saved tokenization specification, raw forwards, source/runtime digests and occupancy receipts are the only inputs. Private participant files and human judgments are excluded.\n\n入力は保存済みのモデル取得仕様・生の採点・実装と環境のハッシュ・占有確認のみ。'),
        nb.v4.new_code_cell('folder = root / "validation/contextual_emoji_two_track_v1"\nspecification = folder / "specification.json"\nrun = folder / "run3296"\nsaved = json.loads((folder / "mechanical_audit.json").read_text())\nfresh = auditor.audit(specification, run, root)\nassert {k:v for k,v in fresh.items() if k != "created_at_utc"} == {k:v for k,v in saved.items() if k != "created_at_utc"}\nprint("Independent audit exactly reproduced (apart from the execution timestamp).")'),
        nb.v4.new_markdown_cell('## Results\n\nOnly acquisition completeness and numerical checks are printed; interpretation summaries remain undisclosed before the next author tryout.'),
        nb.v4.new_code_cell('visible = ["assessment", "forward_rows", "token_sums_checked", "complete_pairs", "exact_prefix_pairs", "exact_historical_sentinel_scores", "guarded_before_after_every_attempt", "all_resource_observations_allowed", "independent_scenarios", "new_independent_scenarios", "model_choice_summaries_disclosed", "human_responses_read"]\nprint(json.dumps({key:fresh[key] for key in visible}, indent=2))\nassert fresh["numerical_gate_passed"]\nassert fresh["new_independent_scenarios"] == fresh["human_responses_read"] == 0'),
        nb.v4.new_markdown_cell('## Takeaways\n\nIf all assertions pass, the bounded acquisition is mechanically qualified. The author workbench remains a post-disclosure development pilot. Independent evaluators and independently prepared scenario families are still needed before human-validity or confirmatory claims.\n\n全検査の通過は取得の機械的な整合性を示す。人の意味判断の妥当性や確認的な成功は、まだ示さない。')
    ]
    nb.validate(book)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:
        nb.write(book,f)

if __name__=='__main__':
    main()
