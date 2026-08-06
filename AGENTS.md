# Repository documentation and research rules

## Bilingual documentation / 日英二言語ドキュメント

Every user-facing prose document must be maintained as an English/Japanese pair.
The English file uses the ordinary `.md` name; the Japanese file inserts `.ja`
before the extension. For example, `README.md` pairs with `README.ja.md`, and
`docs/BACKENDS.md` pairs with `docs/BACKENDS.ja.md`.

利用者向けの文章ドキュメントは、英語版と日本語版を必ずペアで管理する。
英語版は通常の `.md`、日本語版は拡張子の直前に `.ja` を入れる。
例: `README.md` / `README.ja.md`、`docs/BACKENDS.md` / `docs/BACKENDS.ja.md`。

- Update both members of a pair in the same change.
- Keep claims, numbers, caveats, commands, and links semantically aligned.
- English is the source language for the Phase I paper, but not a reason to let
  the Japanese repository documentation drift.
- Pair navigation links should appear near the top of each prose document.

- ペアの両方を同じ変更で更新する。
- 主張、数値、留意点、コマンド、リンクの意味を一致させる。
- Phase I 論文は英語でまとめるが、それを理由に日本語ドキュメントを
  古いままにしない。
- 各文章の冒頭付近に、対応する言語版へのリンクを置く。

Exceptions are source code, tests, schemas, configuration/data files, licenses,
citations, generated machine-readable artifacts, generated human-readable run
reports, `TREE.txt`, and this file.

例外は、ソースコード、テスト、スキーマ、設定・データ、ライセンス、引用情報、
自動生成された機械可読アーティファクト、自動生成された人間可読の run report、
`TREE.txt`、および本ファイルとする。

## Research claim boundary / 研究主張の境界

Keep observations, screening statistics, and causal or semantic interpretations
separate. A successful pre-causal readiness receipt permits the next targeted
experiment; it does not establish meaning, mechanism, or causality. Do not edit
generated receipts by hand. Regenerate them and update every pinned hash.

観測結果、スクリーニング統計、因果・意味・機構の解釈を分離する。
事前因果段階のレディネス検証を通過しても、許されるのは次の限定的な実験へ
進むことだけである。意味、機構、因果性が確立したとはみなさない。
生成済み receipt は手作業で書き換えず、再生成して対応する固定 SHA-256 も更新する。

## Phase I goal / Phase I の目標

Phase I ends with a reproducible, falsifiable English-language paper. The paper
must bind its reported cells to configuration, source, dependency/runtime,
model-artifact, and validation receipts, and must state negative results and
unexecuted controls explicitly.

Phase I の到達点は、再現可能で反証可能な英語論文である。論文で報告する実験セルは、
設定、ソース、依存関係とランタイム、モデル・アーティファクト、検証 receipt に結び付ける。
負の結果と未実施の対照実験も明記する。

## Frozen holdouts / 凍結ホールドアウト

Treat `data/targets/p2_confirmatory_targets_v1.jsonl` as a one-shot Milestone 2
confirmatory bank. Do not use it for implementation debugging, control design,
threshold tuning, layer or strength selection, or intervention-site exploration.
It may be opened only by the exact frozen P2 configs after the public protocol
freeze and all preflight checks pass.

`data/targets/c1_causal_holdout_targets_v1.jsonl` is stricter: do not pass it to
any model, tokenizer-driven selection process, or outcome analysis until a new
C1 causal protocol has frozen the intervention, endpoint, controls, and
multiplicity family. Structural hash/schema checks that do not inspect model
outcomes are allowed. Never overwrite either v1 bank.

`data/targets/p2_confirmatory_targets_v1.jsonl` は、Milestone 2 で一度だけ使う
確認用bankとして扱う。実装debug、対照設計、閾値調整、layer・strength選択、
介入点探索には使わない。公開プロトコルの凍結後、すべての事前検査を通過した
場合に限り、凍結済みP2 configから開くことができる。

`data/targets/c1_causal_holdout_targets_v1.jsonl` にはさらに厳しい制約を置く。
介入、endpoint、対照、多重性familyを新しいC1因果プロトコルで凍結するまで、
モデル入力、tokenizerを用いた選別、結果解析に使わない。モデル結果を見ない
構造・hash・schema検査だけは許可する。どちらのv1 bankも上書きしない。
