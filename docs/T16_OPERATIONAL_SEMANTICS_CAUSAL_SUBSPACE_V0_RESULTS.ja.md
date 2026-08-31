# T16 運用的意味課題と因果サブスペースの結果

[English](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.md) · [固定済みプロトコル](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0.ja.md) · [closeout](../validation/t16_operational_semantics_causal_subspace_v0/closeout.json)

## 結果の要約

行動実験は、固定した4つのモデル×課題ゲートをすべて通過した。新しい8軸を使い、
Gemma 2 2B ITとMistral 7B Instruct v0.3のどちらでも、絵文字に対応づけた語を
選ぶ課題と、絵文字と語の一致・不一致を見分ける課題が成立した。一方、因果実験は
通過しなかった。T15-Bで再現したinteraction方向から構造的な交絡成分を除いても、
明示的な不一致判断は、登録した仮説と逆向きに動いた。Treatment、sufficiency、
necessityの中央値はいずれも非正である。つまり、絵文字と語の対応は行動上読み出せるが、
T15-Bの応答指紋を、そのまま明示的な整合性判断の因果実装とは呼べない。

## 行動実験

標本単位は意味軸である。各セルは8軸を使い、軸単位のbootstrapを20,000回、
8軸の厳密な片側sign-flip検定を行った。Bonferroni補正後のalphaは`0.0125`である。

| モデル | 固定課題 | 軸中央値 | 95%区間 | 厳密p値 | 二択正答率 | 判定 |
|---|---|---:|:---:|---:|---:|---|
| Gemma 2 2B IT | 意味選択 | 9.156250 | [8.781250, 10.031250] | 0.00390625 | 0.953125 | 通過 |
| Gemma 2 2B IT | 整合性判断 | 5.828125 | [3.062500, 6.750000] | 0.00390625 | 0.761719 | 通過 |
| Mistral 7B Instruct v0.3 | 意味選択 | 14.531250 | [13.625000, 15.531250] | 0.00390625 | 0.937500 | 通過 |
| Mistral 7B Instruct v0.3 | 整合性判断 | 6.843750 | [3.937500, 8.343750] | 0.00390625 | 0.753906 | 通過 |

応答768行はすべて揃っている。2つのモデルroleが完了するまで行動結果は開かず、
生成も行っていない。この結果が支えるのは、固定した二択形式での関連づけと
整合性判断だけである。絵文字を制約なく理解したとも、自然言語一般の矛盾を検出したとも
言えない。

## 因果残差サブスペース

Mistral T15-Bの正規化深度`0.875`と`1.0`の方向から、同じ絵文字軸に属する
7つのcross-axis interactionと、絵文字・語の主効果が張る空間を除いた。
登録済みゲートは、treatment、sufficiency、necessityの3成分すべてが正であることを
求めていた。

| 評価量 | 軸中央値 | 95%区間 | 厳密な片側p値 | 判定 |
|---|---:|:---:|---:|---|
| treatment | -0.148438 | [-0.281250, -0.015625] | 0.9921875 | 不通過 |
| sufficiency | -0.085938 | [-0.125000, -0.062500] | 1.0000000 | 不通過 |
| necessity | -0.054688 | [-0.195312, 0.000000] | 0.9921875 | 不通過 |

介入前の二択正答率は`0.609375`だった。因果応答5,376行はすべて揃い、
zero hookの最大logit誤差は厳密に`0`、full vectorの最大復元RMS誤差は
`3.0351459960619062e-18`である。

ここでは、符号そのものが重要になる。単に検出力が足りず、0付近に留まったのではない。
固定したsource方向は、運用上の不一致endpointを登録仮説と反対へ動かした。
したがって、T15-Bの次トークン応答指紋は、そのendpointの範囲では再現するものの、
「整合性判断の回路」と読み替えることはできない。

## Fail-closedで残した修復履歴

最初の因果runでは、21件の介入batchと1件のplain batchをzero guardで比較していた。
この不整合を検出し、科学的な因果結果を開く前に停止した。記録は
[failure receipt](../validation/t16_operational_semantics_causal_subspace_v0/causal_zero_guard_failure_v0.json)
に残している。修復したのはplain側のbatch shapeだけである。別manifestで凍結した後に
再実行し、zeroと復元の両ゲートを通過した。

## 主張の境界

T16-OSCが支えるのは、固定した2つのinstruction-tuned model cellにおける、
二択形式の関連づけと整合性判断である。また、登録したT15-B残差サブスペースが、
固定した向きのまま明示的な不一致endpointを実装するという仮説は支持されなかった。
制約のない意味理解、自然言語一般の矛盾検出、tokenizer非依存性、固有または完全な回路、
モデル母集団への一般化は主張しない。

## エビデンス

- [行動解析](../validation/t16_operational_semantics_causal_subspace_v0/results/behavior_analysis.json)、SHA-256 `d479e413db5eda8f8df2c7cfde32375c078af6c95b0759a71459ee063f7e8dec`
- [因果解析](../validation/t16_operational_semantics_causal_subspace_v0/results/causal_analysis.json)、SHA-256 `86cd6dede2164d5fec3e7a7c128e0de0c313bf80c168d3ecb5f9c516941ca5f8`
- [Closeout](../validation/t16_operational_semantics_causal_subspace_v0/closeout.json)：炉上のrun root、receipt hash、manifest、修復境界を収録

生の応答ledgerとactivation arrayは、記録済みの炉上scratch rootに残している。
Gitにはコピーしていない。
