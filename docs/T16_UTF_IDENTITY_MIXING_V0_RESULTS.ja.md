# T16 完全同一UTF・family混合・系列長の結果

[English](T16_UTF_IDENTITY_MIXING_V0_RESULTS.md) · [固定済みプロトコル](T16_UTF_IDENTITY_MIXING_V0.ja.md) · [closeout](../validation/t16_utf_identity_mixing_v0/closeout.json)

## 結果の要約

完全に同じ文字列の反復と、Unicode構成familyの多様性は、2つのモデルで異なる
隠れ状態幾何として現れた。`n=1`では、完全同一反復・同一family内混合・family横断混合が、
byte列もprompt rowも同一になり、すべての変位指標が厳密に0だった。
`n=2,4,8,16`では、family横断混合から同一family内混合を引いた値が、
8つのモデル×深度セルですべて正になった。層化bootstrap区間も、全セルで0を上回る。
ただし深度方向には単調ではない。Gemmaでは中盤から後半にかけて拡大し、最終blockで
大きく縮んだ。Mistralでは、完全同一反復の成長が弱まった後期・最終blockでも、
family横断混合の上乗せが残った。これはtokenizer経路を条件とした探索的な幾何結果であり、
Unicode構成や意味をtokenizerから独立に分解した結果ではない。

## 主要な記述集約

各principal unitでは`n=2,4,8,16`を平均した。区間は6つのUnicode構成familyで
層化した20,000回bootstrapによる。

| モデル | 深度 | Block | 完全同一反復の成長 | 同一family内の上乗せ | Family横断の上乗せ | 横断−同一family、95%区間 |
|---|---:|---:|---:|---:|---:|:---:|
| Gemma 2 2B IT | 0.25 | 5 | 0.036007 | 0.012968 | 0.031494 | 0.012005 [0.010682, 0.015212] |
| Gemma 2 2B IT | 0.50 | 12 | 0.116261 | 0.072632 | 0.122892 | 0.046260 [0.041255, 0.054119] |
| Gemma 2 2B IT | 0.75 | 18 | 0.130213 | 0.090632 | 0.129563 | 0.041057 [0.031462, 0.047299] |
| Gemma 2 2B IT | 1.00 | 25 | 0.019195 | 0.016435 | 0.023182 | 0.007419 [0.005687, 0.008589] |
| Mistral 7B Instruct v0.3 | 0.25 | 7 | 0.048883 | 0.021029 | 0.045706 | 0.022963 [0.018296, 0.025429] |
| Mistral 7B Instruct v0.3 | 0.50 | 15 | 0.084063 | 0.044994 | 0.084425 | 0.035101 [0.031685, 0.042528] |
| Mistral 7B Instruct v0.3 | 0.75 | 23 | 0.049622 | 0.045185 | 0.094574 | 0.047833 [0.036481, 0.054128] |
| Mistral 7B Instruct v0.3 | 1.00 | 31 | 0.030167 | 0.031511 | 0.083574 | 0.037238 [0.030508, 0.048114] |

最も安定した記述パターンは、横断−同一familyの符号が全セルで揃った点にある。
モデルごとの隠れ状態空間は絶対尺度を共有しないため、値の大きさをそのままモデル間で
比較しない。

## 系列長との関係

次の表は、各`n`における横断−同一family変位の中央値である。`n=1`はすべて厳密に0のため
省略した。

| モデル | 深度 | n=2 | n=4 | n=8 | n=16 |
|---|---:|---:|---:|---:|---:|
| Gemma 2 2B IT | 0.25 | 0.008515 | 0.012286 | 0.011385 | 0.017612 |
| Gemma 2 2B IT | 0.50 | 0.023081 | 0.041424 | 0.056152 | 0.067126 |
| Gemma 2 2B IT | 0.75 | 0.025857 | 0.036361 | 0.036586 | 0.055121 |
| Gemma 2 2B IT | 1.00 | 0.004342 | 0.004519 | 0.009375 | 0.012308 |
| Mistral 7B Instruct v0.3 | 0.25 | 0.013342 | 0.021231 | 0.024394 | 0.029137 |
| Mistral 7B Instruct v0.3 | 0.50 | 0.021747 | 0.029631 | 0.048098 | 0.050151 |
| Mistral 7B Instruct v0.3 | 0.75 | 0.022110 | 0.039887 | 0.063671 | 0.059660 |
| Mistral 7B Instruct v0.3 | 1.00 | 0.017050 | 0.027637 | 0.049026 | 0.053152 |

系列が長くなるほど上乗せは概して増えたが、すべてのセルで厳密に単調だったわけではない。
そのため、登録済みの主要集約では最大の`n`を選ばず、0でない4つの系列長を平均している。

## 完全同一性で揃えたもの

Panelは、単一scalar、VS16付きpresentation sequence、skin-tone modifier、ZWJ、
regional-indicator flag、digit keycapという6つの構成familyから、完全一致する文字列を
4件ずつ固定した。`clone_exact_utf`はanchorをbyte単位でそのまま反復する。
同一family内混合とfamily横断混合も、先頭には同じanchorを置いた。`n=1`では3条件を
同じcapture済みpromptへ割り当てている。2モデルを合わせると、factorial recordは2,880行、
unique promptは2,496件で、生成呼び出しは0だった。

## Tokenizationの境界

完全同一反復のarmでUTF列を揃えても、混合arm間のtokenizer経路までは揃わない。
深度ごとのtoken数完全一致subsetは、Gemmaで同一family内256 pair、family横断52 pair、
Mistralで152 pairと20 pairだった。Family横断subsetは疎で、系列長によっては4 pairしかなく、
`n=16`には該当pairがない。そこでも距離が0でないことは感度確認として記述できるが、
独立検定でも、主要結果を救済する解析でもない。

したがって主張できるのは、観測したtokenizer経路のもとで、完全同一反復、同一構成内の
多様性、構成横断の多様性を分けて記述できたことまでである。Unicode構成familyそのものが
因果的に符号化されている、token identityを揃えても効果が残る、意味幾何を捉えた、とは
言えない。

## エビデンス

- [Compact analysis](../validation/t16_utf_identity_mixing_v0/results/analysis.json)、SHA-256 `4e388d505a39d91e8c8bfc5c69127878e5484ab904e39d5a5d9ba5b66f658b1b`
- [Tokenizer preflight](../validation/t16_utf_identity_mixing_v0/tokenizer_preflight.json)
- [Closeout](../validation/t16_utf_identity_mixing_v0/closeout.json)：2モデルのreceipt hashと厳密な`n=1`不変条件を収録

生のactivation arrayは記録済みの炉上scratch rootに残し、Gitにはコピーしていない。
