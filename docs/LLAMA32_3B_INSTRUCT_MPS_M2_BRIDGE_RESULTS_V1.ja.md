# Llama 3.2 3B Instruct M2 bridge results v1

[English](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_RESULTS_V1.md) · [Protocol](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.ja.md) · [Analysis correction](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.ja.md) · [機械可読receipt](../artifacts/milestone2/analyses/exploratory/llama32_3b_instruct_mps_m2_bridge_analysis_v1/analysis_receipt.json)

## 結果

事前指定したexploratory bridge criterionは**成立しなかった**。

| Layer | Endpoint | Mean | Two-sided 95% bootstrap interval | Lower bound > 0.06 |
|---:|---|---:|:---:|:---:|
| 5 | Primary minus null A/B/C median | -0.02043 | [-0.04346, 0.00792] | No |
| 5 | Primary minus fully disjoint null A | -0.01571 | [-0.04172, 0.01497] | No |
| 11 | Primary minus null A/B/C median | 0.02285 | [0.00506, 0.04423] | No |
| 11 | Primary minus fully disjoint null A | 0.05532 | [0.03292, 0.07948] | No |

Primary ruleは、layer 5の2つのlower boundが両方ともpractical threshold 0.06を
上回ることを要求した。Layer 5のpoint estimateは両方ともわずかにnegativeで、intervalは
zeroを含んだ。Layer 11にはpositiveなsecondary estimateがあったが、両lower boundは0.06
未満であり、layer 11は事前にnon-rescuingと定めていた。p-valueやconfirmatory labelは
割り当てない。

## 解釈

これはtested cellに対するcleanなnegative transfer resultである。利用可能な範囲で最も
強いtokenizer-structural matchingを施しても、GPT-2 Milestone 2のadvantageは、固定した
Llama 3.2 3B Instruct Transformers/MPS BF16 setupのnormalized depth 0.20では再現しなかった。

Layer 11 patternは救済ではなく、新しいhypothesisとして有用である。Model familyまたは
depthに依存する位置の移動があるかもしれない。ただし、この結果を見てlayer 11を選び、
そのままcausal workへ進んではならない。将来のtestでは、新しいtarget上でこのhypothesisを
freezeするか、model size、instruction tuning、tokenizer、backend、数値精度をmatched cellで
切り分ける必要がある。

この結果は、元のGPT-2 observationがtokenizationだけだったことも、glyph-conditioned
geometryが存在しないことも示さない。指定したmatched control下で、3B transfer claimが
成立しなかったことを示す。

## Integrityとcorrection record

4本の独立model processはresumeなしで完了した。その後analysis v0は、normalized depth
specification `[0.2, 0.4]`とresolved layer index `[5, 11]`を混同したため、最初のstored-config
validationで停止した。Run receipt、summary、intervention ledgerは開いておらず、analysis
outputも作らなかった。

Analysis correction v1はoutcomeを読む前に公開commitした。Score、bootstrap、endpoint、
threshold、decision ruleはv0とbyte-for-byteまたは定数として同一で、stored-config表現の
checkだけを変更した。成功したanalysisは、公開commit `af3e198`、すべてのstatic hash、
exact four-process execution receipt、20,000 bootstrap row、48 target effect rowを検証した。

P2と廃止済みC1にはアクセスしていない。Target 24件は使用済みprestage targetなので、
本結果はexploratoryのままで、independent confirmationでもscale curveでもない。不可避な
null-panel間の2 overlapは今後も必ず開示する。
