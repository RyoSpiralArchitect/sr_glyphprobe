# Mistral 7B semantic atlas reserve確認 v0 evidence

[English](README.md) · [結果](../../docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [固定protocol](../../docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md)

このcompact bundleは、freeze、single-use 292-item reserve取得、完全8-cell解析、固定した
randomization判定、furnace実行receipt、結果返送時の検証を結びつける。

Runはcanonical batch-one forward 1,752回で、layer 31のFP32 vector 7,008本を10個の
完了shardへ保存した。Partial shard、intervention、generationは0。固定primary ruleは通過した。
Glyph/name minus glyph/codepoint top-1 contrastの8-cell最小値は`0.171233`、実用下限は`0.02`。
共通permutation 19,999回のうち観測統計以上は0回で、`p = 0.00005`だった。

Raw activation約111 MBと292件のitem-level retrieval rowはGit外に保持する。このbundleには、
run/session receipt、完全8-cell metrics、primary result、execution/return receipt、exact hashを残す。

このevidenceが裏付けるのは、固定model、layer、transport gridにおける確認的alignment claimである。
意味、因果、tokenizer非依存性、model一般性、Phase I全体のclaimは認めない。
