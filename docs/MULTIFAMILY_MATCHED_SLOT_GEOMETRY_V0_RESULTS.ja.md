# Multifamily matched-slot geometry v0 結果

[English](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [固定protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) · [Analysis repair](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md) · [公開evidence](../artifacts/multifamily_matched_slot_geometry_v0/README.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

## 状態

Roleを固定したMLX run 2本と、repair後のjoint analysisを完了しました。事前に
定めた結果patternは次のとおりです。

```text
olmo_only_token_structured_recurrence
```

Gemmaは、固定5深度をまとめたmatched-slot nullを棄却しませんでした。OLMoは
Holm補正後も棄却しました。ただし、OLMoでは同じmatched slotを持つ5 familyが
厳密に同じ末尾tokenを共有します。そのため、この結果はtoken構造で説明でき、
tokenizer非依存の再現や意味上の再現を支持しません。

## 主結果：固定5深度のomnibus

主統計は、family平均を引いたあとのslot平方和比率を、固定5深度で同じ重みで
平均した値です。Nullは、family内のslot labelを独立に並べ替える19,999回の
同期randomizationです。PCG64のseedは固定し、2つのmodel-level p値を一つの
Holm familyとして扱いました。

| Model | 観測値 | Null平均 | 超過 | Raw p | Holm p | 棄却 |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.204304805 | 0.199984463 | +0.004320342 | 0.208500 | 0.208500 | しない |
| OLMo 3 7B BF16 | 0.500391869 | 0.200184835 | +0.300207034 | 0.000050 | 0.000100 | する |

OLMoのraw p値は、19,999回のrandom drawと観測配置を用いるこの設計で取り得る
最小値です。それ以上の精度を意味しません。

## 固定した全深度のprofile

深度別p値は副次記述です。多重性を補正した判定権はなく、all-depthの主endpointと
差し替えることもできません。

| Model | Fraction | Layer | Slot比率 | Null平均 | 超過 | 副次p値 |
|---|---:|---:|---:|---:|---:|---:|
| Gemma | 0.00 | 0 | 0.193842 | 0.200009 | -0.006167 | 0.970150 |
| Gemma | 0.25 | 6 | 0.203212 | 0.199994 | +0.003218 | 0.252800 |
| Gemma | 0.50 | 13 | 0.211557 | 0.199991 | +0.011567 | 0.084350 |
| Gemma | 0.75 | 19 | 0.203293 | 0.199962 | +0.003331 | 0.262800 |
| Gemma | 1.00 | 25 | 0.209620 | 0.199967 | +0.009653 | 0.278400 |
| OLMo | 0.00 | 0 | 0.994722 | 0.200455 | +0.794267 | 0.000050 |
| OLMo | 0.25 | 8 | 0.461325 | 0.200172 | +0.261152 | 0.000050 |
| OLMo | 0.50 | 16 | 0.413424 | 0.200134 | +0.213290 | 0.000050 |
| OLMo | 0.75 | 24 | 0.336661 | 0.200084 | +0.136577 | 0.000050 |
| OLMo | 1.00 | 31 | 0.295828 | 0.200079 | +0.095749 | 0.000050 |

OLMoのslot比率は深くなるほど大きく下がりますが、固定した全深度でnullを上回り
ました。これは記述的な持続profileであり、意味を持つslot変数が機構によって変換・
保持されることを示すものではありません。

## Tokenizer条件に沿った解釈

結果は、tokenizer側から最も強く予測できる分岐に沿いました。

- Gemmaでは50 glyphが互いに異なる50個のatomic tokenになります。固定した
  all-depth omnibusは、並べ替えたmatched-slot baselineを超えて再現しませんでした。
- OLMoでは全glyphが`[9468, family_token, slot_token]`になります。familyをまたいで
  同じ末尾slot tokenを共有し、最初の固定深度で非常に強いmatched-slot geometryが
  見られ、その後は深さとともに弱まりました。

したがって、OLMoの正の結果にはtoken構造だけで十分な説明が残ります。ただし、
model family、width、precision/quantization、nodeも同時に異なるため、token identityが
geometryを因果的に生んだとは証明できません。また、GemmaにglyphやUnicodeのgeometryが
一切ないとも言えません。このpanelの固定all-depth endpointを通らなかった、という
範囲に限られます。

## Integrityとanalysis repair

- 公開protocol freezeはcommit
  `ae928b840e6164c89e9c4c71d5e41ceb8de3dfaa`です。
- Activation arrayはGemmaが`50 × 5 × 2304`、OLMoが`50 × 5 × 4096`です。
- 各runはmodel forward 50回、intervention、generation、protected-target callは0回です。
- 両run ledgerとjoint analysis validatorはPASSしました。
- OLMoの4 fileはmac1、furnace relay、mac2の三地点でhash一致しました。炉のGPU
  computeは使っていません。

最初のjoint-analysis attemptは、YAMLの`null` keyがPythonの`None`として解釈され、
JSON mapping keyに使えなかったため、公開前に停止しました。解析値は表示・閲覧して
いません。成功runの前に、commit
`7f9184d9adb1bf6487a5e262f2fcdace90f68608`でserialization-only repairを公開freeze
しました。変更はそのkeyを文字列`"null"`にする一点だけで、input、統計量、
randomization、seed、draw数、p値、多重性補正、結果registry、report行は変えていません。

## 主張の境界

許される最も強い記述は、**同じ末尾tokenを厳密に共有するOLMo cellでは観測的な
matched-slot recurrenceがあり、Gemmaのall-depth omnibusでは再現しなかった**、です。

絵文字の意味、意味family、tokenizer非依存のglyph特性、因果mechanism、backend parity、
model scaleやquantizationの効果、node差、確認的結論、Phase I論文gateは示しません。
都合のよいfamilyやdepthを選ばず、正負を含む全行を残しています。
