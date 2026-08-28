# Mistral 7B semantic atlas v0 解析計画

[English](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md) · [取得protocol](MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md)

状態: **取得integrityのfinalize後だが、activation値を読む前、固定recapture forward前、
記述解析前にfreeze**した。Raw atlasは既に存在するため、これは取得後の記述計画であり、
確認的preregistrationではない。

## Capture validation

取得はbatch size 64を使い、一意入力ごとに1 forwardから4つのcausal位置を読んだ。
固定engineering validationではacquisition index `[0, 445, 891]`、全3 view、両carrierを
batch size 1でrecaptureする。取得済み18列、reserve 0列である。各caseは4距離×9 layerの
全vectorを保存FP32 tensorと比較する。

1 caseが通過するには36 vector全体で次の境界をすべて満たす必要がある。

- 最小cosine `0.999999`以上
- 最大relative RMS error `0.001`以下
- 最大absolute element error `0.125`以下

18 caseすべてを要求する。これはengineering equivalenceであり、意味解釈を検証しない。

## Population

記述analyzerは既出calibration 50件と未使用discovery 842件を分けて報告する。292件の
reserveはloadもforwardもしない。結果後のitem filterは置かない。全carrier・距離・固定layerを
報告し、populationごと72 cell、計144 rowとなる。

## Centeringとpaired retrieval

各population/view/carrier/distance/layer cell内でitem方向のfeature平均を引き、各item
vectorをL2 normalizeする。glyph/name、glyph/codepoint、name/codepointの3 view pairごとに、
完全なcross-view cosine matrixを作る。

paired diagonal cosine、off-diagonal平均、そのmargin、双方向top-1 paired retrieval、双方向
mean reciprocal rank、centered linear CKAを報告する。Rankではpaired itemよりstrictly大きい
similarityだけを前順位として数えるため、完全tieには楽観的であることを明示する。

直接のsemantic-anchor contrastは、各glyph/name metricから対応するglyph/codepoint metricを
引く。これは記述値であり、閾値、p値、多重性判定、良好cell選択は認めない。

## 近傍構造

各viewでcentered cosineが近い他item 10件を取り、Unicode groupとsubgroupのneighbor purityを
有限母集団random-pair baselineとともに報告する。Calibrationも`k=10`。将来10件以下の
populationへ適用する場合だけ`k=n-1`とする。

## 完全output

Analyzerは次を保持する。

- population×carrier×distance×layerの完全144 row
- 取得item×cellごとのpaired cosine row。3 viewの正確なtoken数とUnicode labelも含む
- 固定2 carrier×4距離を等weight平均した18 layer summary。良好cellを選択しない

約3 GiBのraw atlasとitem-level解析はGit外に置く。Compact receipt、全cell row、layer
summary、validation evidence、日英結果文書は公開できる。

## 主張境界

Codepoint viewより大きなglyph/name retrievalやCKAが得られれば、semantic alignment仮説を
より鋭くできる。しかしdisentangleされたemoji意味の保存、tokenizer構造の因果的除去、
model一般化は確立しない。未使用reserveは、この記述結果から後にendpointを一つ選び、
prospectiveに評価するために残している。
