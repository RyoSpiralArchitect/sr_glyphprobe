# Multifamily colored-shape geometry v0 結果

[English](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) · [固定プロトコル](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md) · [公開エビデンス](../artifacts/multifamily_colored_shape_geometry_v0/README.ja.md) · [研究ロードマップ](ROADMAP.ja.md)

- プロトコルID: `glyphprobe-multifamily-colored-shape-geometry-v0`
- 固定commit: `dc78756bd8f26ae0060463e459d5deb40c47d750`
- 結果pattern: `no_dual_model_recurrence`

## 一文でまとめると

事前に指定したmidpointでは、circle-minus-square方向の共通軸を2つのmodel cellに
またがって確認できなかった。Gemma 2 2B 4-bitは正の値だったものの、Holm補正後は
棄却せず、OLMo 3 7B BF16も、より小さな正の値で棄却しなかった。

凍結済み規則に照らせば、これで負・mixed outcomeとして完了である。ただし、色付き図形の
geometryが存在しないことを示す結果ではない。意味、機構、因果性、backend parity、
quantization同等性、scale効果も確立しない。

## 凍結済みprimary結果

色ごとに、事前指定したmidpoint layerの
`resid_post(circle) - resid_post(square)`をL2正規化し、5方向の非対角cosine
10組を平均した。Square側の色labelは、identity pairingを含む全120通りへ置換した。
2つのmodel-cell p値を一つのHolm familyとし、familywise alphaは0.05である。

| Model role | Token条件 | Primary layer | 平行性 | Exact count / 120 | Raw p | Holm p | 棄却 |
|---|---|---:|---:|---:|---:|---:|---|
| `gemma2_2b_4bit` | 10 glyphすべてが別のatomic 1 token | 13 / 26 | 0.114857969 | 7 | 0.058333333 | 0.116666667 | なし |
| `olmo3_7b_bf16` | すべて3 token、shared prefixあり | 16 / 32 | 0.024628040 | 33 | 0.275000000 | 0.275000000 | なし |

指定した補正後は、どちらも棄却しなかった。より強い事前登録patternである
dual recurrence、Gemmaだけの棄却、OLMoだけの棄却、異符号のいずれにも当てはまらない。
Primary layerを差し替えず、登録済みのfallback `no_dual_model_recurrence`を採用した。

## 固定5深度の全結果

Midpoint以外の4 layerは記述用である。監査できるようexact p値も残すが、多重性に関する
判定権限はなく、結果を見た後でprimary layerの代わりにはできない。

| Model | Depth fraction | Layer | 平行性 | Exact p | 同色cross-shape超過 | 判定上の扱い |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.00 | 0 | 0.242416497 | 0.008333333 | 0.219694236 | 記述のみ |
| Gemma 2 2B 4-bit | 0.25 | 6 | 0.175126893 | 0.008333333 | 0.251123238 | 記述のみ |
| Gemma 2 2B 4-bit | 0.50 | 13 | 0.114857969 | 0.058333333 | 0.162412883 | Primary、Holm棄却なし |
| Gemma 2 2B 4-bit | 0.75 | 19 | 0.186448879 | 0.016666667 | 0.211163629 | 記述のみ |
| Gemma 2 2B 4-bit | 1.00 | 25 | 0.203435852 | 0.016666667 | 0.284060541 | 記述のみ |
| OLMo 3 7B BF16 | 0.00 | 0 | 0.035562068 | 0.991666667 | -0.021358138 | 記述のみ |
| OLMo 3 7B BF16 | 0.25 | 8 | 0.027411455 | 0.316666667 | 0.020318093 | 記述のみ |
| OLMo 3 7B BF16 | 0.50 | 16 | 0.024628040 | 0.275000000 | 0.054966885 | Primary、Holm棄却なし |
| OLMo 3 7B BF16 | 0.75 | 24 | 0.030455476 | 0.266666667 | 0.110482586 | 記述のみ |
| OLMo 3 7B BF16 | 1.00 | 31 | 0.012424917 | 0.166666667 | 0.171737014 | 記述のみ |

Gemmaの非primary行には、2つの固定深度で全置換検定の下限`1/120`が現れた。ただし、
これらはprimary familyの外にあり、midpoint規則を固定した後で初めて見た値である。
発見として扱えば、outcomeを見てlayerを選んだことになる。OLMoでは、共通の
circle-minus-square軸は強まらない一方、同色cross-shape超過が深度とともに記述的に
増えた。2つのgeometry要約が異なる動きをしたとは言えるが、color表現やshape表現を
同定したわけではない。

## 実行と完全性

科学runは2本とも公開freezeの後に実行し、同じ固定implementation tree
（`f8d7407ecc4bb5d40e000446e655af139d231fc45f11df732e59582f48c252aa`）を使った。

- Gemma: model forward 10回、activation arrayは`10 × 5 × 2304`
- OLMo: model forward 10回、activation arrayは`10 × 5 × 4096`
- generation call: 0
- intervention call: 0
- protected-target fileの参照: 0
- 非有限activation: 0

各run bundleは、生成元nodeでsealed ledger validatorを通過した。OLMo bundleは
mac1からfurnaceを中継してmac2へ移した。4 fileすべてのhashが生成元・中継先・到着先で
一致し、到着後のvalidatorにも再度合格した。Joint analyzerは、両role、model manifest、
protocol freeze、input ledger、item順、layer順、array shape、有限値を再検証してから
endpointを計算した。最終analysisも、10 layer行を残した状態でvalidatorを通過している。

公開bundleは、向き付け用文書とmanifestを除いて約0.71 MBに収まるため、2本のactivation
arrayも収録した。Local absolute path、host address、credential、生成文、介入ledger、
protected targetは含まない。生成payloadは13 file・`711469` byteで、public manifestの
SHA-256は`f7e3a5fb9458e25cc0a58df1c3076ad4b5470caf9d544d2102081eee13c75ac1`である。

## この結果で変わること

T2は、実行済みの観測side trackとして完了した。正のcross-model replicationとして
完了したわけではない。少なくとも現在の2-cell設計から、modelをまたぐ共通shape axisを
主張することはできない。また、Gemmaのmidpoint値だけをnominal threshold付近の結果として
持ち上げず、OLMoの結果とHolm familyを含めて読む必要がある。

Cell間の違いの原因は分離できていない。Model family、parameter数、quantization/precision、
tokenizer構造、nodeが同時に変わっている。したがって、raw effect magnitudeをscale curveや
quantization効果として解釈しない。

運用上のMilestone 2も変更しない。GPT-2 layer 2候補について、別に凍結する因果プロトコルを
設計することはできるが、T2から新しいlayerを選ばない。因果、独立backend、確認、archiveの
各paper gateも閉じない。

## 次の選択肢――まだ新しいfreezeではない

この結果から、次の3経路をきれいに分けられる。この文書では、どれも選択・固定しない。

1. **2 cellの交絡をほどく。** たとえばGemma 2 BF16とGemma 2 4-bitのように、
   同じfamilyまたは同じartifactに近いcontrastを1本加えてから、precision差やscale差を考える。
2. **Layerを後付けで選ばず、emoji familyを広げる。** すでに公開済みのanimals、food、
   moon/sky、social、transport panelについて、まずtokenizer-onlyの実行可能性を調べる。
   Activationを開く前に、family-level endpointか全深度omnibus ruleを固定する。
3. **Endpointを独立に再実装する。** 同じ固定panel、role binding、全置換nullを、
   適格な非MLX backendまたは別model cellで再現する。負の行も残し、Gemmaの記述的な
   layer peakを新しいprimaryにしない。

次のprotocolでは、このうち一つだけを主問とする。Model breadth、emoji breadth、depth選択を
同時に動かさなければ、次も負だったときに、何が不成立だったのかを読み取れる。

## 主張境界

使用できる表現:

> 凍結済みのraw-glyph `resid_post`観測研究では、事前指定したmidpointの
> circle-minus-square平行性endpointは、Gemma 2 2B 4-bit atomic-token cellと
> OLMo 3 7B BF16 prefix-matched cellの両方で、Holm補正後の棄却としては再現しなかった。

使用しない表現: 色付き図形に共通geometryはない、7Bで効果が消えた、quantizationが
Gemmaの値を作った、OLMoはshapeではなくcolorを符号化する、MLXは別backendに対して
適格である、glyphの因果mechanismを発見した。
