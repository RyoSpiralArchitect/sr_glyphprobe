# E2 Stage A v2：Llama 3.2 3B MLX 技術検証の結果

[English](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [凍結済みプロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) · [ロードマップ](ROADMAP.ja.md) · [機械可読レシート](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json)

## 判定

V2プロトコルと、そこで許可した技術変更は、commit
`dc84ac19e06ef7a0fd7dcd77fdce4b484b192e57`で凍結した。その後、
Transformers/MPSとMLXを隔離して検証し、最後まで実行した。記録された
レシートの判定は`status: validation_failed`、`scientific_result: false`である。

したがって、**固定したE2科学セルにはMLXを採用しない**。これは、技術経路の
不適格判定であって、グリフや絵文字についての科学的な負の結果ではない。
E2の科学gridは実行していない。

V1の記録もそのまま残す。V1はcommit
`88685bd01ab115df323e9a324d49a659c66163c7`で凍結し、Transformers/MPS phaseを
完了した後、MLXの最初のbaseline exportで次のerrorを出して停止した。

```text
RuntimeError: Item size 2 for PEP 3118 buffer format string B does not match the dtype B item size 1.
```

V1ではレシートを生成せず、科学的な結果も確認していない。
[失敗記録](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)は
そのまま保存している。V2で指定した
バックエンドの数値挙動に影響する変更は、export bridgeだけである。Native BF16の
MLX arrayをNumPyへ渡す直前に`mx.float32`へcastし、model実行自体はBF16のまま
保った。

## 結果一覧

| 凍結済みgate family | 合格数 | 判定 |
|---|---:|---|
| Parity全体 | 33 / 60 | 不合格 |
| Token ID・反復argmax・決定性 | 10 / 10 | 合格 |
| Baseline activation・logit | 6 / 10 | 不合格 |
| 厳密なzero-hook | 10 / 10 | 合格 |
| 介入後のactivation・logit | 7 / 10 | 不合格 |
| 介入差分 | 0 / 10 | 不合格 |
| Backend内の介入忠実度 | 0 / 10 | 不合格 |
| マシンローカルな速度gate | false | 不合格 |

総合判定には、凍結済みの全gate合格規則を使った。一部の検査に合格しても、
不合格のparity familyや速度gateを上書きしない。

## 実行完了とidentity検査

レシートは、`mlx-community/Llama-3.2-3B-bf16`のrevision
`60a99aaf43164077157d64bf909b7b61143c6a6d`、native BF16、`resid_post`、layer
5・11、固定済みengineering prompt、固定済み介入vectorを一体で拘束する。
Transformers/MPSとMLXは、隔離したsubprocessで順番に最後まで実行し、どちらも
return code 0だった。両モデルを同時にメモリへ常駐させていない。

固定したmodel metadataと、全9 fileのartifact manifestはbackend間で一致した。
Manifestの合計は6,434,705,789 bytes、SHA-256は
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`である。
Backend固有のstable-identity hashが同一だとは主張しない。

Stage Aでは、研究用target bank、確認用outcome、因果outcomeのいずれにも
アクセスしていない。

## 一致した項目

Tokenizationと決定性の10検査はすべて合格した。Token IDはbackend間で一致し、
反復実行したtoken IDとargmax出力も同一だった。各backend内で反復したlogitの
最大絶対差は0である。厳密なzero-hook検査も10件すべて合格した。

Backend間の介入差分では、activation側の比較が10件すべて閾値を満たした。

| Activation差分の指標 | 10 cellの範囲 | 凍結済み閾値 |
|---|---:|---:|
| NRMSE | 0.014057–0.018356 | ≤ 0.02 |
| Cosine similarity | 0.999832–0.999901 | ≥ 0.999 |
| RMS ratio | 0.999625–1.000526 | 0.98–1.02 |

この検査が示すのは、固定したengineering probeでactivation差分が狭い数値範囲で
一致したことだけである。Parity gate全体の合格を意味しない。

## 一致しなかった項目

対応するlogit差分は明確に閾値を外れた。

| Logit差分の指標 | 10 cellの範囲 | 凍結済み閾値 |
|---|---:|---:|
| NRMSE | 0.580523–1.402939 | ≤ 0.05 |
| Cosine similarity | -0.097707–0.816940 | ≥ 0.99 |
| RMS ratio | 0.882575–1.408769 | 0.95–1.05 |

凍結済みの差分gateでは、activationとlogitの両方に合格する必要がある。このため、
activation単独では10 / 10でも、介入差分の総合結果は0 / 10となった。

Backend内の介入忠実度も10 cellすべてで不合格だった。Activation NRMSEは、
Transformers/MPSで0.030175–0.034029、MLXで0.030222–0.034148となり、固定した
閾値0.01を上回った。両backendともcosine similarityは約0.9994、RMS ratioは
約1である。レシートだけから、この不一致を科学的mechanismへ結び付けたり、原因を
単一の実装へ特定したりはできない。Baseline familyは6 / 10、介入後output familyは
7 / 10にとどまった。

## 速度

同期benchmarkは、10組のprompt-layer cellを対象にした。各cellでwarm-upを2回、
計測を10回行い、backendごとに100回のforwardを測定した。

| Backend | Aggregate median latency |
|---|---:|
| Transformers/MPS | 132.127833 ms |
| MLX | 230.138000 ms |

MLXの中央値はTransformers/MPSの`1.741782892`倍の時間を要した。レシートに記録した
speedupは`0.574124367x`で、速度gateは`false`である。このgateは、MLX latencyが
Transformers/MPSの95%以下であることを求めていた。10件のcellすべてでMLXの
中央値が遅かった。この測定は、マシン、負荷、software、model、計測境界に依存する。
MLX全般の性能を示すものではない。

## 科学的な主張境界

このレシートから言えるのは、固定したLlama 3.2 3B BF16 MLX経路が、指定済みの
backend parity gateと速度gateを満たさなかったことだけである。

次のいずれも示さない。

- E2科学gridの結果
- 絵文字familyや意味についての結果
- 因果や回路についての結果
- modelをまたぐ再現
- model scale効果の証拠
- Phase I論文gateの達成

検証失敗を、科学的な負の結果へ読み替えてはならない。検査したのは技術経路であり、
研究仮説ではない。

## 次の選択

性質の異なる2つの経路が残っている。どちらを採るかは、まだ決めていない。

1. E2 transport研究について、Transformers/MPS専用の科学プロトコルを別に凍結する。
2. MLX v3の診断・最適化プロトコルを新しく凍結し、科学的outcomeへアクセスする前に、
   新しいengineering validationを再実行する。

本書では、どちらも推奨しない。V2の閾値は固定したまま残し、結果を見た後で緩めたり
調整したりしない。選択は研究責任者の判断待ちである。

## 来歴

- V2 freeze commit: `dc84ac19e06ef7a0fd7dcd77fdce4b484b192e57`
- Protocol ID: `glyphprobe-e2-llama32-3b-mlx-engineering-validation-v2`
- Receipt status: `validation_failed`
- Receipt SHA-256: `4ede081c129d9a4733b661dcab7452e5a0ae4e8e90c6bc5890817d500cca4468`
- V1 failure record: [`attempt_01_failure.json`](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)
- Receipt: [`validation/mlx_llama32_3b_bf16_parity_v2/receipt.json`](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json)
