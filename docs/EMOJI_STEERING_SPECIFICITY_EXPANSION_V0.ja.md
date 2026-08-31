# Emoji Steering Specificity Expansion v0

[English](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md) ·
[T13-EA結果](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) ·
[科学的契約](SCIENTIFIC_CONTRACT.ja.md)

Protocol ID: `glyphprobe-emoji-steering-specificity-expansion-v0`  
実験label: **T14-X**

## 目的

T13-EAでは、structured source directionがpositive isotropic directionより
大きなnext-token分布変化を作ることが多く、とくにnormalized depth 0.875
付近で差が大きかった。T14-Xはtargeted causal claimへ進む前に、この観測を
広げて局在化する。

T14-Xでは、6つのbase-model role、すでに公開・探索済みのT13 source item
全192件、公開target全32件、depth 0.875と1.0、介入の正負、4つのrotating
wrapper holdout、2種類のdeterministic signed source-covariance nullを固定する。
完全gridは **559,488 intervention rows** である。

## 何を母数として増やすか

T13の20,000 bootstrap replicateは既存dataの不確実性を細かくするが、独立な
観測を増やすものではない。T14-Xでは実験上のsupportを増やす。

- intervention roleを3 checkpointから6 checkpointへ拡張する。
- 192 source itemすべてを2つのlate depthで介入する。
- 4-fold leave-one-wrapper-out prototypeでwrapper依存性を測る。
- positive-only isotropic calibrationを、source residual covarianceから作る
  signed nullへ置き換える。

Target、source item、wrapper、sign、depth、model roleは別levelとして扱う。
反復directionやsignを独立promptとして数えない。

## 固定grid

| Arm | 1 modelあたり | 6 model合計 |
|---|---:|---:|
| Item/source-form late-depth grid | 70,656 | 423,936 |
| Leave-one-wrapper-out prototype | 14,336 | 86,016 |
| Signed source-covariance null | 8,192 | 49,152 |
| 明示的zero hook | 64 | 384 |
| **合計** | **93,248** | **559,488** |

Model rosterはQwen 2.5 0.5B、OLMo 2 1B、Qwen 2.5 1.5B、Llama 3.2 3B、
Qwen 2.5 3B、Qwen 2.5 7Bである。T13のsource-bank artifactとruntime
receiptをそのままbindする。Parameter幅は記述的構造にすぎず、architecture、
tokenizer、sizeは交絡している。

## Nullの構成

Model、depth、held-out wrapperごとに、残り3 wrapperから利用可能な
system/view prototypeをすべて作り直す。各item directionをunit-RMS化し、
対応するprototypeを引いてcenterする。有限なresidualをpoolしたmatrixから、
次の2種類を生成する。

1. deterministic Gaussian coefficient combination
2. deterministic Rademacher coefficient combination

各familyはwrapper fold・depthごとに8 seedを持ち、正負を明示的に実行する。
これはsystem/view meanを除いたsource由来covarianceを持つ方向に対して、
structured responseが上回るかを調べるcontrolである。Tokenization independenceや
semantic specificityを証明するものではない。

## 実行と停止規則

最初のmodel load前にfreeze manifestをauditする。再利用する各T13 source roleは
hashを含めて完全検証する。各roleはnonzero shardより前にzero-hook shardを実行
する。完成済みshardは検証だけを行い、上書きしない。Foreign GPU contentionが
現れた場合は他workloadを妨害せずyieldする。

科学的outcomeを開くのは、6 roleと固定shardがすべて完成した後に限る。負、混合、
heterogeneousなcellも含め、全model、system、item、view、target、sign、nullを残す。

## 因果実験へのhandoff

T14-Xの完全結果は、公開・探索済みinputだけを使う別の凍結済みlocalization
selectorへ渡してよい。そのselectorは、後続patch/ablate/restore実験のために
model、injection depth、downstream componentをそれぞれ1つだけbindする。
Retired C1 v1と将来のC1 v2 bankはT14-Xの外側に置く。C1 v2は、因果operation、
endpoint、control、多重性規則、componentが完全に凍結されるまで生成もopenも
しない。

## 主張境界

T14-Xは探索実験である。Emoji meaning、unique emoji specificity、因果component・
path、generation behavior、tokenizer independence、scale law、model populationへの
一般化、independent replicationは確立しない。負またはheterogeneousな結果も
完全なT14-X結果であり、後続の因果設計を制約する。
