# Mistral 7B base depth-by-distance v0 結果

[English](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) · [固定protocol](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md) · [T6結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [公開証拠](../artifacts/mistral7b_base_depth_distance_v0/README.ja.md) · [ロードマップ](ROADMAP.ja.md)

## 状態

固定したMistral 7B v0.3 base-modelの400 forward cellと、19,999 drawのanalysisは完了した。
登録済みoutcomeは次のとおりである。

```text
recurrence_and_early_depth_attenuation_excess
```

片側検定の両成分がpermutation下限に達し、1つのintersection-union testはalpha 0.05で
棄却された。これは、選択済みだが未観測だった1つのbase-model cellにおいて、固定した
深度依存profileを支持するprospective evidenceである。ModelとendpointはT6を見た後に
選んだため、独立確認ではなく、instruction tuning効果も同定しない。

## 唯一の主判定

Criterion Aは、両carrier・全5深度を等重み平均した距離1のmatched-slot fractionである。
Criterion Bでは、まず各深度で固定距離contrast
`[0.375, 0.125, -0.125, -0.375]`を計算し、深度0の値から後続4深度の平均を引く。
IUT p値は2成分の大きい方である。

| 成分 | 統計量 | Null平均 | Null超過 | Raw p |
|---|---:|---:|---:|---:|
| 距離1 recurrence | 0.377524026 | 0.199970302 | +0.177553724 | 0.000050 |
| Early-minus-late attenuation | 0.149104068 | 0.000111606 | +0.148992462 | 0.000050 |
| Intersection-union判定 | — | — | — | **0.000050** |

19,999 randomizationと観測配置では、`0.000050`が到達可能な最小p値であり、それ以上の
精度を意味しない。判定には両成分が必要で、結果確認後のlayer選択は使っていない。

元のT6 all-depth attenuation contrastも、登録済み副次値として残した。統計量は負
`-0.005273805`、raw `p = 0.874750`だった。つまり、今回の正の結果は固定した深度
interactionに限られ、失敗済みall-depth endpointの救済ではない。

## 固定した深度×距離profile

各cellは`" a"`と`" |"`の2 carrierを平均している。Attenuation列は各深度の4距離へ
固定weightを適用した値である。

| Fraction | Layer | 距離1 | 距離2 | 距離4 | 距離8 | Attenuation |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.841332583 | 0.726544742 | 0.606268804 | 0.577399364 | +0.114009450 |
| 0.25 | 8 | 0.351050392 | 0.490319560 | 0.473210701 | 0.459639655 | -0.038582366 |
| 0.50 | 16 | 0.260152003 | 0.366929984 | 0.385665647 | 0.374902352 | -0.045373339 |
| 0.75 | 24 | 0.223453811 | 0.319257335 | 0.327746893 | 0.311487528 | -0.034073839 |
| 1.00 | 31 | 0.211631342 | 0.277450668 | 0.286026770 | 0.268369787 | -0.022348929 |

深度0 attenuationは`+0.114009450`、後続4深度の平均は`-0.035094618`で、事前指定した
差は`+0.149104068`だった。

全深度を平均した距離profileは`[0.377524026, 0.436100458, 0.415783763,
0.398359737]`である。距離8は同期nullより高く、副次raw `p = 0.000050`に達したが、
tailに独立した判定権限はない。T7は単調な持続や持続時間閾値を示さない。

## T6 Mistral Instructとの記述的な関係

BaseとT6 Instruct cellは、観測tokenizer列、architecture次元、距離、carrier、readout layerを
共有する。T6 InstructのprofileはT7設計の動機としてすでに見ていたため、次の比較は
結果選択後の記述である。

| Fraction | Base attenuation | T6 Instruct attenuation |
|---:|---:|---:|
| 0.00 | +0.114009450 | +0.114377892 |
| 0.25 | -0.038582366 | -0.034050106 |
| 0.50 | -0.045373339 | -0.036292177 |
| 0.75 | -0.034073839 | -0.026802768 |
| 1.00 | -0.022348929 | -0.013872223 |
| Early minus later mean | +0.149104068 | +0.142132210 |

20個のdepth × distance cellに対する記述的Pearson相関は`0.996785730`、平均絶対差は
`0.011953404`、RMSEは`0.015478703`、最大絶対差は`0.040097243`だった。同等性margin、
pair test、独立checkpoint標本は固定していない。したがって、instruction tuningが無影響、
checkpointが同等、profileが一般的、という結論には使えない。

## Carrier profile

Carrier別の値は副次で、各rowは5深度を平均している。

| Carrier | 距離1 | 距離2 | 距離4 | 距離8 |
|---|---:|---:|---:|---:|
| `" a"`の反復 | 0.383700975 | 0.451806423 | 0.411254790 | 0.372560341 |
| `" |"`の反復 | 0.371347077 | 0.420394492 | 0.420312735 | 0.424159133 |

特に距離8でcarrier差が見えるが、どちらも別個には選択・検定していない。

## 整合性と実行

- 公開prospective freezeはcommit
  `25de47a5fb4c9eaf7674d5b2fa49f0c2cf84ca8b`、manifest SHA-256は
  `495f323589d150ce3429035cb47694988eb33f7f7b97a7d58526cfc35ed03493`。
- 公開modelは`mistralai/Mistral-7B-v0.3`、revision
  `caa1feb0e54d415e2df31207e5f4e273e33509b1`。重複consolidated weightを除いた12-file
  artifactはmanifest SHA-256
  `1ee90f904de614fd2e1088e9e978fa5b9d36d1a855807764fb8f91cacfd8d05e`と一致した。
- Zero-forward preflightは7,248,023,552 elementすべてがBF16であること、model次元、
  tokenizer/carrier roster全体を検証した。
- Runは400 forward・2,000 vector、shape `50 × 2 × 4 × 5 × 4096`。介入、生成、
  protected-target callは0。
- Compute直前の炉はfreeで、run後も10 MiB、utilization 0%、compute process 0へ戻った。
- 炉側validator 2つ、返送SHA-256 ledger 2つ、mac2側validator 2つがすべて合格した。
  Compact activation arrayと40 profile rowを完全公開する。

## 主張境界と次の判断

T7は、選択したbase checkpointにおいて、固定したearly-versus-later depth profileの再現を
支持する。T6の形が1つのInstruct checkpointだけの特異性だった、という狭い説明は弱くなる。
ただし、関連する2 checkpointがなぜ似るかは切り分けない。Tokenizer factorizationと
architectureを共有し、weightにも系譜関係がある。

絵文字意味、memory変数、回路、因果、instruction-tuning不変性、tokenizer因果、backend・
node同等性、model-family一般性、独立確認、Phase I paper gateは示さない。隣接するMistral
checkpointをさらに増やす価値は低い。次の綺麗な観測controlは、長さ・prefix・carrier・
readout位置を保ったまま、family間の共有slot identityを実際のtoken列で壊す構成である。
因果分岐へ進むなら、介入とcontrolを別protocolで先に固定する必要がある。
