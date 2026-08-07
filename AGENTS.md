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

`data/targets/p2_confirmatory_targets_v1.jsonl` was the one-shot confirmatory bank
used by Milestone 2. That one-shot use is complete. Preserve it as historical
evidence; do not reopen or reuse it for implementation debugging, control
design, threshold tuning, layer or strength selection, intervention-site
exploration, confirmation, or causality. Only content-blind file existence,
size, and hash checks are allowed.

`data/targets/c1_causal_holdout_targets_v1.jsonl` is retired from future
confirmatory or causal use. On 2026-08-07, one complete C1 record was exposed to
a research-agent context by an over-broad repository search. No experimental
model forward, tokenizer pass, or outcome analysis used it, but the bank can no
longer be described as fully untouched. Preserve the file as historical
evidence; do not read, sample, tokenize, model-forward, or analyze it. Only
content-blind file existence, size, and hash checks are allowed. A future C1
experiment requires a new versioned bank prepared outside the exposed research
context. Never overwrite either v1 bank.

`data/targets/p2_confirmatory_targets_v1.jsonl` は、Milestone 2で使用済みの
一度限りの確認用bankである。その使用は完了した。歴史的証拠として保存し、
実装debug、対照設計、閾値調整、layer・strength選択、介入点探索、確認、
因果実験のいずれにも再度開いたり再利用したりしない。内容を見ないfile存在、
size、hash検査だけを許可する。

`data/targets/c1_causal_holdout_targets_v1.jsonl` は、今後の確認・因果実験には
使用しない。2026-08-07、リポジトリ検索の範囲が広すぎたため、C1の完全な1レコードが
研究agentの文脈へ表示された。実験modelのforward、tokenizer処理、outcome解析には
使っていないが、このbankを完全な未露出とは呼べない。Fileは歴史的証拠として保存し、
読み込み、sampling、tokenize、model forward、解析を禁止する。内容を見ないfile存在、
size、hash検査だけを許可する。将来のC1実験では、露出した研究文脈の外で新しいversionの
bankを作る。どちらのv1 bankも上書きしない。
