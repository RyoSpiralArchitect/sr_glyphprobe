# Mistral 7B semantic atlas reserve確認 v0

[English](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md) · [Discovery結果](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md)

状態: **prospectiveに規定済み。Freeze manifestをcommitするまで実行禁止。記録上、
reserveへのmodel input forwardは0**。

## 問い

T8 discoveryで一度もmodel forwardを受けなかった決定的な292-item reserveにおいて、
後期深度のglyph/name alignment候補は再現するか。

検定するのは狭い一点だけである。Mistral 7B v0.3のlayer 31で、glyph residualから正しい
Unicode正式名をretrievalする強さが、2 carrier×4距離の完全transport grid全体でliteralな
`U+...` codepoint retrievalを上回るかを調べる。

## 固定populationと取得

Populationは、既存selectionでroleが`reserved_unrun`の全itemをsource index昇順に並べた
292件である。Freeze後の除外、置換、追加は認めない。

取得するのは、選択済みendpointに必要なものだけである。

- view: 正確なglyph、Unicode正式名、uppercase `U+...` literal
- carrier: `" a"`と`" |"`をそれぞれ8回反復
- causal readout距離: 1、2、4、8
- siteと深度: `resid_post`、layer 31のみ
- batch size: 一意sequence 1本につき1 forward
- 合計: 1,752 forward、FP32 vector 7,008本、item shard 10個

各shardは最初のforward前にintent recordを書く。完了shardは再取得しない。Partial shardが
残った場合、重複なしの実行を自動では証明できないため、そのitemを黙って再実行せず、manual
adjudicationのためprotocolを停止する。

## 単一primary endpoint

8つのcarrier×distance cellごとに、292 item間でview別にfeatureをcenterし、各rowをL2
normalizeする。Glyph rowから正式名target matrixとcodepoint target matrixを検索する。
Tieは決定的な先頭`argmax`に従う。

各cellのcontrastを次のように定義する。

`glyph→name forward top-1 accuracy - glyph→codepoint forward top-1 accuracy`

単一global statisticは、この8 contrastの最小値である。有利なcarrierや距離を選ばず、全gridを
一つのconjunction型endpointへまとめる。

片側nullは、NumPy seed `20260828`による19,999回の決定的randomizationを使う。各drawでは、
8 cellすべてに共通する一つのpermutationで正式名のitem correspondenceを入れ替え、観測された
codepoint controlと全representation matrixは固定したまま、最小contrastを再計算する。
P-valueは`(1 + exceedances) / 20,000`である。

次の両方を満たした場合だけ、outcomeを
`transport_robust_late_depth_glyph_name_alignment_confirmed`とする。

1. randomization p-valueが`0.05`以下
2. 観測された8-cell最小contrastが`0.02`以上

それ以外の完了結果は`not_confirmed_under_frozen_rule`とする。Global testは一つなので追加の
多重性補正はない。実用下限`0.02`はreserve forward前に、discoveryの最弱cell contrast
`0.080760095`の4分の1未満へ固定した。

## Secondary出力と主張境界

8 cellすべての値、reverse retrieval、mean reciprocal rank、paired cosine margin、centered
linear CKAは記述的に報告する。Primary ruleを救済したり置換したりできない。Token長stratumも
集計できるが、decisionを変更しない。

正の結果が確認するのは、固定した1 model・1 layerにおけるtransport-robustかつitem-specificな
glyph/name alignmentである。人間が読む絵文字意味、tokenization因果、因果mechanism、behavior、
model一般性、Phase I論文全体を確立しない。負の結果でも、outcome-guided redesignをせず同じ
狭い問いを閉じる。

Model-family横断再現と変則glyph探索は、このreserve結果とevidence bundleを封印した後に始める。
