# Mistral semantic atlas token構造感度 v0

[English](MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.md) · [Canonical batch-one protocol](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md)

状態: **outcome後に設計した感度解析**。完全discovery headlineを見た後にこの正確な
層別を記述したため、結果は確認的ではなく、未使用reserve testの代わりにもならない。

Discovery 842件中760 glyphは、Mistralで厳密に5 token、先頭3 token IDも
`[29473, 1011, 930]`で共通する。この最大stratumではglyph token数の変動を除き、長い
共通prefixも固定できる。全72固定cellのcross-view記述metricを次で再計算する。

- 共通prefixを持つ5-token glyph全760件
- name token数1–5のstratum（105、257、213、111、43件）
- codepoint token数6/7のstratum（180、573件）

Name token数5の43件ではglyph/name token数も等しい。Discoveryには3 viewすべてのtoken
数が等しいitemがないため、完全な3-view token-isomorphic controlとは呼ばない。20件未満の
stratumは、この感度解析前に固定したtokenizer-only size ruleで除外する。

全stratum、layer、carrier、distanceを保持する。p値、閾値、多重性判定、良好stratum選択は
置かない。Codepoint retrievalに対するglyph/name retrievalが残れば単純なglyph長説明は
狭まるが、token identityを除去せず、意味を因果的に確立せず、paper gateも閉じない。
