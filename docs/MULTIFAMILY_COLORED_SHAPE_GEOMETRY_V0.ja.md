# Multifamily colored-shape geometry v0

[English](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md) · [Tokenizer census結果](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

Protocol ID: `glyphprobe-multifamily-colored-shape-geometry-v0`

## Status

これはprospectiveに固定する探索的activation protocolである。この英日文書、config、
runner/analyzer、test、checksum manifestを含む最初の公開commitから、実行可能なfreezeが
始まる。それ以前のmodel forwardはengineering capability probeに限り、本実験の観測には
含めない。

問うのは狭い一点である。5色にまたがる共通のcircle-minus-square方向が、Llamaではない
事前指定2 model cellで再び現れるか。Emojiの意味、behavior、因果、circuit、backend
parity、node性能、量子化同等性、確認的な論文claimは検証しない。

## なぜ次にこのcellを行うか

完了したtokenizer censusから、一つのuniversalなprefix-matched controlをtokenizer family
間でそのまま運べないことが分かった。一方で、異なる二つの固定control regimeが得られた。

- Gemma 2では、10個の色付きshapeが別々のatomic tokenになる。1 tokenという長さと
  single-code-point Unicode constructionは揃うが、異なるglyphがatomic token prefixを
  共有することはできない。
- OLMo 3では、10 itemがすべて3 tokenで、同じvocabulary内で少なくとも先頭1 tokenを
  共有する。

この二つは別regimeとして報告する。Cross-model recurrenceは、各cellで独立に符号と
exact-test decisionが再現するかだけで判断し、幅、precision、tokenizer、nodeをまたいだ
effect magnitudeの直接比較は行わない。

## 固定model cell

| Role | Model artifact | Runtime | Structural control |
|---|---|---|---|
| `gemma2_2b_4bit` | `mlx-community/gemma-2-2b-4bit` | mac2、MLX、4-bit | atomic、1 token、同じUnicode construction |
| `olmo3_7b_bf16` | sealed local OLMo 3 7B artifact | mac1、MLX、BF16 | 3 token、shared prefix、同じUnicode construction |

両model artifactは、path非依存の全file manifest hashで固定する。Manifestは正確な
GlyphProbe source-tree hashと全protocol assetも結び付ける。Local filesystem pathは
runtime入力であり、公開receiptへ残してはならない。

Clean runtimeはMLX 0.31.1、MLX-LM 0.31.2、Transformers 4.57.6に固定する。
MLX-LM 0.31.2の配布metadataはTransformers 5以上を要求する一方、このpreflight済み
combinationはimportでき、両modelで有限値のengineering captureを1件ずつ完了した。
この不一致は全receiptに残し、qualified backend比較とは呼ばない。

## 固定panelとcapture

既存の順序付き10-item colored-shape panelを変更せず使う。5色（`brown`、`orange`、
`green`、`blue`、`purple`）と2 shape（`circle`、`square`）のcrossである。
Special tokenを加えずraw glyphをforwardし、itemの最終tokenで`resid_post`を捕捉する。

Activationを見ず、次の式で5層を決める。

```text
min(num_layers - 1, floor(fraction * num_layers))
fractions = [0, 0.25, 0.5, 0.75, 1]
```

Gemma 2では`[0, 6, 13, 19, 25]`、OLMo 3では`[0, 8, 16, 24, 31]`になる。
一次解析は`0.5` layerだけで、残る4層は記述用である。結果を見て一次層と交換しない。

## Primary endpointとexact null

色\(c\)について、

\[
d_c = h(\text{circle}_c)-h(\text{square}_c)
\]

とする。\(h\)はprimary layerにおけるraw glyphの`resid_post` vectorである。各\(d_c\)を
L2 normalizeし、5方向のoff-diagonal pairwise cosine 10件の平均をprimary statistic
\(T\)とする。値が大きいほど、色をまたぐcircle-minus-square axisが平行である。

Square側のcolor labelを全置換する（`5! = 120`）。One-sided exact valueは次である。

```text
p = count(T_permuted >= T_observed) / 120
```

事前指定した2 model cellのp-valueを一つのfamilyとし、familywise alpha 0.05でHolm補正
する。他のlayerやsecondary statisticには確認的decisionを与えない。

## 事前登録する結果pattern

- **Dual-model recurrence candidate:** 両primary effectが正で、両Holm decisionがreject。
- **Gemma-only heterogeneity:** Gemmaだけreject。
- **OLMo-only heterogeneity:** OLMoだけreject。
- **Opposite-sign heterogeneity:** primary statisticの符号が異なる。
- **No dual-model recurrence:** より強いpatternがどれも該当しない。

最も強いpatternでも観測的candidateに留まる。この2-cell設計ではmodel family、scale、
precision/quantization、tokenizer構造、nodeが交絡している。

## Secondary outputとengineering provenance

固定5層すべてについて、shape-axis parallelism、panel中心化後のcross-shape color pairing、
activation RMS、token ID/count/prefix診断、有限値checkを報告する。Load時間、first-forward
時間、peak memoryはengineering provenanceに限る。Full logitsは保持せず、有限性とargmaxを
記録する。Intervention、generation、protected target、holdout bankは開かない。

各model runはactivation array、item別観測、pathをscrubしたreceipt、SHA-256台帳を、
directoryのatomic renameで公開する。Joint analysisはendpoint計算前に両bundleを再検証する。
Passing ledgerはintegrityとreplayabilityの証拠であり、科学的な確認ではない。
