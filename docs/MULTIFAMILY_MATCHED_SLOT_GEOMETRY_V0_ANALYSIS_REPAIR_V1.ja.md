# Matched-slot geometry v0 analysis repair v1

[English](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md) · [凍結済みv0 protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md)

Repair ID: `glyphprobe-multifamily-matched-slot-geometry-v0-analysis-repair-v1`

## なぜrepairが必要か

最初のjoint analysisは、analysis receiptを書き出す段階で
`TypeError: Dict key must be str`により停止しました。凍結済みYAMLで`null`と
書いたmapping keyが、Pythonでは`None`として解釈されたためです。process内では
v0の統計量、randomization、Holm補正、結果patternまで計算されましたが、output
directoryは公開されず、解析値も表示・閲覧していません。

このrepairを実行する前に、失敗内容と、すでにsealされた両run bundleの正確なhashを
公開記録へ固定します。

## 許可する変更

変更するのはJSON書き出し境界だけです。mapping keyの`None`を文字列`"null"`として
保存します。もともと文字列だったkeyと、すべてのleaf valueは変更しません。生成する
analysis receiptには、repair IDとrepair manifest hashを記録します。

次の要素は変更しません。

- 両modelのactivation arrayとrun receipt
- 5×10 panelとmodel role
- 固定5深度
- 平方和に基づく統計量
- family内slot labelを用いる同期randomization
- 19,999 draws、PCG64 seed `20260828`、p値の式
- 2検定のHolm familyとalpha
- 結果pattern registry
- reportの行と科学的主張の境界

Wrapperは凍結済みv0 analyzerをimportして、そのまま実行します。解析前に、公開repair
manifest、元のfreeze、両run bundle各4 fileのhashを検証します。これは結果に合わせた
解析変更ではなく、結果を見る前に固定するserialization repairです。

## 主張の境界

Repaired bundleのPASSが示すのは、事前指定したv0解析を固定inputからJSON化し、hashで
sealできたことです。観測実験を、意味、因果、確認、tokenizer同等性、Phase I論文gateの
結果へ強めるものではありません。
