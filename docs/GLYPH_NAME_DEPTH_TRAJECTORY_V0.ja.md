# Glyph–Name 深度軌跡 v0（T17-GN）

[English](GLYPH_NAME_DEPTH_TRAJECTORY_V0.md) · [T9結果](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [T10結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md)

状態：**固定設計候補、T17のmodel forwardは0回**。

## 問い

T9では、Mistral 7Bの一つのcellについて、返却された最終hidden stateがraw emoji surfaceから
正しいUnicode正式名を検索する精度は、literalな`U+...` codepoint列を検索する精度より大きいことを
prospectiveに確認した。T10では固定した9 cellすべてに正の統計signalがあったが、登録済みの
モデル横断実用条件は通過しなかった。

T17-GNは、その最終層snapshotだけでは答えられない問いを立てる。

> Decoderの深さに沿って、raw emoji surfaceはいつcodepoint literalよりUnicode正式名と
> item単位で強く対応するようになるのか。その軌跡は固定model rosterで共有されるのか。

このprotocolでの「glyph」は、text tokenizerへ渡すraw Unicode emoji surfaceを指す。
Fontでrasterizeした画像をmodelへ渡すわけではないため、視覚的glyph知覚の検査ではない。

## 固定設計

- Population：すでに結果を開いたT9/T10の292項目。置換なし。
- View：raw emoji、Unicode正式名、literal `U+...` codepoint。
- Context：T10と同じ2 carrier × 4 distanceの完全grid。
- Model：T10で使った同じ9つのexact model/tokenizer revision。
- Depth：`0.0`から`1.0`まで9つの正規化深度をarchitectureごとに解決する。
- Acquisition：batch size 1。item/view/carrierごとに1 forwardし、4つのsuffix位置と9深度を
  同じforwardから読む。
- Budget：15,768 forward、567,648本のFP32 readout vector。

最終fractionのendpointはAPIが返すfinal hidden stateであり、model-final normalizationを含み得る。
中間点は解決したdecoder block後のAPI hidden stateである。両者を曖昧にまとめない。

## 固定した測定

Model、depth、carrier、distanceごとに3 viewを別々にcenterし、各rowをL2 normalizeする。
次の二pairについて、順逆top-1、順逆MRR、paired-minus-off-diagonal cosine margin、centered
linear CKAを記録する。

1. emoji ↔ Unicode正式名
2. emoji ↔ codepoint literal

Headlineの記述曲線は、nameのforward top-1正解からcodepointのforward top-1正解を引いた
item-level値を、8 contextで等weight平均したものとする。8 contextをまとめたままitemを20,000回
resampleし、記述的percentile区間を出す。初期値・最終値、peak depth、正の値が持続し始めるdepth、
depth AUC、model横断断面はすべて取得前に固定する。

## 解釈分岐

- **後期に共通して上昇**：この固定rosterに繰り返し現れる後期lexical alignment軌跡。
- **Peak depthがmodelごとに異なる**：model固有のalignment window。共通final-layer実用閾値が
  脆かった理由の候補になる。
- **早期から正または平坦**：最終層効果を「後期変換」と呼ぶのは不適切。
- **疎または逆転**：T9は一般的な深度現象ではなく、範囲限定cellの結果として残る。

どの分岐も結果である。ただし既出populationを使う探索atlasであり、新しい確認検定ではない。

## 主張境界

T17-GNが記述できるのは、固定cellにおけるraw emoji/name/codepoint geometryと深度軌跡である。
視覚的glyph知覚、人間的意味、理解、tokenizer非依存性や因果、circuit、behavior、scale law、
tuning効果、独立再現、architecture一般性、population一般性は確立しない。
