# E2 Stage A3：Llama 3.2 3B MLX runtime dtype 数値screen v1の結果

[English](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [凍結済みプロトコル](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) · [Stage A v2結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md) · [機械可読レシート](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json)

## 判定

Stage A3プロトコルは、commit
`1f8a8d09d3f519add9bf4ef5a65c1c41256c67ae`で公開凍結した。その後、正式な
engineering-only screenを実行し、次の判定を得た。

- `status: engineering_screen_complete`
- `scientific_result: false`
- `selection.selected_runtime_dtype: null`
- `selection.decision: no_go_no_eligible_numeric_candidate`

固定した2つのruntime dtype candidateは、どちらも全gate合格には至らなかった。
Artifactとruntime dtypeのidentity、prompt・token identity、backend内の決定性、
zero-vector integrity、介入忠実度は両candidateとも合格した。不合格だったのは、
マシンローカルな速度gateだけである。閾値は緩和せず、別candidateへのfallbackや
自動再実行も行っていない。

Stage A v2の結果は変わらない。V2レシートは引き続き
`status: validation_failed`、`scientific_result: false`である。Stage A3は、
この失敗記録を上書きも置換もしない。

## 結果一覧

| Candidate | Token・決定性 | Zero vector | 忠実度 | Runtime dtype | 速度 | Eligible |
|---|---:|---:|---:|---:|---:|---:|
| `float16` | 合格 | 合格 | 合格 | 合格 | 不合格 | false |
| `float32` | 合格 | 合格 | 合格 | 合格 | 不合格 | false |

凍結済み規則では、すべてのgateに合格する必要がある。数値integrityに関するgateを
すべて通過しても、速度gateに不合格ならeligible candidateにはならない。

## 固定範囲と実行記録

両candidateは、同じBF16-weight artifact
`mlx-community/Llama-3.2-3B-bf16`のrevision
`60a99aaf43164077157d64bf909b7b61143c6a6d`を読み込んだ。9 fileからなるartifact
manifestの合計は6,434,705,789 bytes、SHA-256は
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`である。
異なるのはruntime compute dtypeだけで、候補は`float16`と`float32`に固定した。

両backend・両candidateで、loader resolved dtypeは指定candidateと一致した。
3,212,749,824個のmodel parameterも、すべて指定dtypeとして記録されている。
ただし、このdtype監査はnon-parameter bufferには及ばない。

実行条件は、v2と同じ5つのengineering promptと、`resid_post`のlayer 5・11を
組み合わせた10 cellである。各cellではwarm-upを2回、計測forwardを10回実施した。
4つのworkerは、隔離したsubprocessで厳密に順次実行し、すべてreturn code 0で
完了した。2つのfull modelを同時にmemoryへ置いていない。Artifact、parameter、
promptのidentityも完全に一致した。

研究用target bank、P2 outcome、C1 outcome、確認用outcome、因果outcomeには
アクセスしていない。

## 数値integrity gate

両candidateは、backend間のtoken identity、各backend内の反復token・argmaxの
完全一致、v2から変えていないzero-vector閾値、backendごとに評価した介入忠実度に
合格した。Zero-vector gateは、activation・logitの最大絶対変化が`1e-7`以下で
あることを求める。

| Candidate | Backend | 10 cellのfidelity NRMSE範囲 | 凍結済みNRMSE閾値 | Cosine gate |
|---|---|---:|---:|---:|
| `float16` | Transformers/MPS | 0.00383147–0.00436931 | <= 0.01 | 合格（>= 0.999） |
| `float16` | MLX | 0.00383590–0.00435258 | <= 0.01 | 合格（>= 0.999） |
| `float32` | Transformers/MPS | 4.633e-7–5.327e-7 | <= 0.01 | 合格（>= 0.999） |
| `float32` | MLX | 4.627e-7–5.336e-7 | <= 0.01 | 合格（>= 0.999） |

この結果が示すのは、固定したengineering probeにおいて、指定したadditionを
各backendが忠実に再現したことまでである。Transformers/MPSとMLXの完全なparityを
確立したわけではない。

Stage A3では、backend間のbaseline、changed output、activation delta、logit deltaを
調べるfull parity familyを実行していない。これらを調べるには、別に凍結したfull v3
validatorが必要だった。したがって、FP32のfidelity値が非常に小さくても、FP32 MLX
経路をqualifiedと表現してはならない。

## マシンローカルな速度gate

速度gateは、MLXのaggregate medianが、対応するTransformers/MPS medianの95%以下に
なることを求めた。

| Candidate | Transformers/MPS median | MLX median | MLX / MPS | MLXのcell中央値が遅い数 | 速度gate |
|---|---:|---:|---:|---:|---:|
| `float16` | 165.0765625 ms | 322.9998125 ms | 1.956666698 | 10 / 10 | 不合格 |
| `float32` | 465.013771 ms | 458.619459 ms | 0.986249198 | 4 / 10 | 不合格 |

FP16は、このrunのMLXで大幅に遅かった。FP32では、MLXのaggregate medianが
Transformers/MPSより約1.375%短かったが、凍結済みgateが求める短縮率は5%以上で
ある。ほぼ同等の速度であっても、この規則では合格にならない。

これらのtimingは、記録時のマシン、software stack、負荷、温度、process順、model、
prompt、計測境界に依存する。MLXとMPSの一般的な性能比較ではない。

## Selectionと主張境界

Eligible candidateが1つもなかったため、決定論的なselection ruleは
`no_go_no_eligible_numeric_candidate`を返した。この結果は、次のいずれも許可しない。

- Formal v3 validatorへ進めるFP16またはFP32の選定
- 一方のcandidateから他方へのfallback
- Formal full v3 parity validation
- MLXを使うE2科学grid
- Llamaにおけるglyph、絵文字family、意味、因果、回路、cross-modelの結果
- 科学的な負の結果
- Phase I論文gateの達成

これは、完了したnegative engineering-screen decisionであって、研究上のnegative
outcomeではない。レシートの`scientific_result: false`と
`selection_is_not_scientific_authorization: true`が、この境界を機械可読にしている。

## 次の判断

Formal v3 validatorは凍結も許可もしておらず、今回のscreenからMLX科学gridへは
進まない。現実的な選択肢は、研究責任者が改めて判断する必要がある。

1. Transformers/MPS専用の科学経路を別に凍結する。
2. 新しい公開protocolとversionの下で、将来のMLX engineering計画を別に設計する。

2番目の経路は、このscreenの再試行ではない。観測後の閾値緩和、不適格candidateの
fallback利用、engineering経路の再設計中における科学的outcomeへのアクセスは
認めない。

## 来歴

- Protocol公開freeze: `1f8a8d09d3f519add9bf4ef5a65c1c41256c67ae`
- Protocol ID: `glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`
- Receipt status: `engineering_screen_complete`
- Selection decision: `no_go_no_eligible_numeric_candidate`
- Receipt SHA-256: `02a3a0f60a1211da48ec60adce8df4fa4a44187bccb0cc610386f63df885a518`
- 凍結済みプロトコル: [`LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md`](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md)
- レシート: [`validation/mlx_llama32_3b_numeric_screen_v1/receipt.json`](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json)
