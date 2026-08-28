# Semantic atlas model横断再現 v0 結果

[English](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [固定プロトコル](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md) · [証拠](../artifacts/semantic_atlas_cross_model_replication_v0/README.ja.md)

状態：**固定した判定規則の下では、モデル横断再現は確立しなかった**。

一次判定の統計条件は通過したが、事前に固定した実用条件を満たさなかった。Bonferroni部分連言検定の
p値は`0.0001`だった。一方、全項目成分とtoken数完全一致成分の両方で、8セル最小差が`0.02`以上に
なったコアmodel/tokenizerセルは4つ中2つだけだった。必要数は3つである。したがって、全モデルセルの
IUTが統計的に有意でも、一次判定は負となる。

## 固定後の取得

Freeze commit `7002db63a23b5a66ababa3033631268fe899b2cd` とmanifest SHA-256
`8673bc51490460b3e8908f766b592169942bf6a7e88d292c50b427e5283f34a4` は、候補モデルへの
forwardを一度も行う前にpushした。取得条件は、T9の292項目、glyph/name/codepointの3 view、
2 carrier、4距離、batch size 1をそのまま保った。一次endpointは
`output.hidden_states[-1]` が返す最終norm後のhidden stateである。Rawな最終decoder block出力は、
一次判定を救済できない副次endpointとして、同じforward内で取得した。

9つのexact revisionは、各セル37 shard、1,752 forwardをすべて完了した。合計は333 shard、
15,768 model forward、FP32 readout 126,144本である。Interventionとgenerationは0回だった。
Qwen 0.5Bの最初の試行では、別のGPU processを検出したため、モデルをloadする前にyieldした。この試行の
forwardは0回で、GPUが空いたことを確認してから取得を再開した。

| Model cell | 取得時間（秒） | CUDA peak（GB） | Forward | Readout |
|---|---:|---:|---:|---:|
| Llama 3.2 3B base | 14.198 | 6.467 | 1,752 | 14,016 |
| Qwen 2.5 7B base | 22.345 | 15.318 | 1,752 | 14,016 |
| OLMo 2 1B base | 9.076 | 3.008 | 1,752 | 14,016 |
| Gemma 2 2B IT | 15.397 | 5.281 | 1,752 | 14,016 |
| Qwen 2.5 0.5B base | 10.929 | 1.035 | 1,752 | 14,016 |
| Qwen 2.5 1.5B base | 12.136 | 3.128 | 1,752 | 14,016 |
| Qwen 2.5 3B base | 15.392 | 6.326 | 1,752 | 14,016 |
| SmolLM2 1.7B base | 10.122 | 3.460 | 1,752 | 14,016 |
| Mistral 7B Instruct v0.3 | 23.827 | 14.535 | 1,752 | 14,016 |

これらは単一のfurnace環境における取得receiptであり、モデル間・backend間の速度benchmarkではない。

## 固定したモデルセル判定

各成分の統計量は、2 carrier×4距離の完全gridにおける次の差の最小値である。

`glyph→Unicode正式名 top-1 - glyph→U+codepoint top-1`

各モデルセルのp値には、全項目randomizationとtoken数一致randomizationの大きい方を採用する。
実用条件は、両成分の観測最小値がともに`0.02`以上であること。9つのIUT p値を一つのHolm familyとし、
Holm条件と実用条件の両方を通過したセルだけを、範囲を限定したセル単位の通過とする。

| Model cell | 役割 | Matched n | 全項目の最小差 | 一致成分の最小差 | IUT p | Holm p | 実用条件 | 限定セル判定 |
|---|---|---:|---:|---:|---:|---:|---|---|
| Llama 3.2 3B base | core | 281 | 0.027397 | 0.032028 | 0.000050 | 0.000450 | pass | pass |
| Qwen 2.5 7B base | core | 284 | 0.023973 | 0.024648 | 0.000050 | 0.000450 | pass | pass |
| OLMo 2 1B base | core | 281 | 0.013699 | 0.021352 | 0.000050 | 0.000450 | fail | fail |
| Gemma 2 2B IT | core | 284 | 0.017123 | 0.017606 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 0.5B base | extension | 284 | 0.006849 | 0.007042 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 1.5B base | extension | 284 | 0.013699 | 0.014085 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 3B base | extension | 284 | 0.017123 | 0.017606 | 0.000050 | 0.000450 | fail | fail |
| SmolLM2 1.7B base | extension | 287 | 0.006849 | 0.003484 | 0.000100 | 0.000450 | fail | fail |
| Mistral 7B Instruct v0.3 | extension | 285 | 0.202055 | 0.203509 | 0.000050 | 0.000450 | pass | pass |

限定セル判定を通過したのは、Llama 3.2 3B base、Qwen 2.5 7B base、Mistral 7B Instruct
v0.3である。Extensionセルは、唯一のモデル横断一次判定を救済できない。

## モデル横断の一次判定

固定した4つのcore cellは、Llama 3.2 3B base、Qwen 2.5 7B base、OLMo 2 1B base、
Gemma 2 2B ITである。4つのIUT p値はすべて`0.00005`だった。したがって、登録済みの
`m = 4`、`r = 3`のBonferroni部分連言検定は、`2 × 0.00005 = 0.0001`となり、統計条件を通過した。

実用条件を通過したのはLlamaとQwenだけだった。OLMoは全項目成分が`0.013699`、Gemmaは両成分が
`0.017123`と`0.017606`で、固定下限を下回った。このため実用通過数は必要な`3/4`に届かず、`2/4`だった。
統合した一次判定は、次の負の結果となる。

`cross_model_replication_not_established_under_frozen_rule`

この分岐も結果そのものであり、観測後に閾値を動かす理由にはしない。

## Tokenization一致で何が変わったか

`(glyph token数, name token数, codepoint token数)` が完全に同じ非singleton層には、tokenizerごとに
292件中281〜287件が残った。Matching後も観測alignmentは消えなかった。9つの一致成分はすべて統計的に
有意であり、最小差の「一致成分−全項目成分」は`-0.003365`〜`+0.007654`、中央値は`+0.000482`だった。

したがって、「T10のretrieval差は、token数が揃っていない層だけで全て生じた」という狭い説明は退く。
ただし、tokenization非依存性が示されたわけではない。Token identity、語彙設計、tokenizerの系譜、学習data、
architecture差は統制していない。

## 登録済みの副次endpoint

Endpoint感度を調べるため、rawな最終decoder block出力も取得した。この副次endpointには判定権限がなく、
一次結果を救済できない。

| Model cell | Raw-block全項目の最小差 | Raw-block一致成分の最小差 |
|---|---:|---:|
| Llama 3.2 3B base | 0.023973 | 0.021352 |
| Qwen 2.5 7B base | 0.020548 | 0.021127 |
| OLMo 2 1B base | 0.013699 | 0.014235 |
| Gemma 2 2B IT | 0.010274 | 0.007042 |
| Qwen 2.5 0.5B base | 0.020548 | 0.021127 |
| Qwen 2.5 1.5B base | 0.027397 | 0.028169 |
| Qwen 2.5 3B base | 0.034247 | 0.035211 |
| SmolLM2 1.7B base | 0.000000 | 0.000000 |
| Mistral 7B Instruct v0.3 | 0.195205 | 0.196491 |

最終normによる最小差の変化は、モデルによって正負が異なった。この副次profileは、返却された最終stateと
raw block出力を同じendpointとして扱わず、名称と取得位置を明示する必要があることを示す。

## 記述的なモデルprofile

固定したQwen base系列では、一次endpointの最小差がモデルサイズとともに単調に増えた。

| Qwen size | 全項目の最小差 | 一致成分の最小差 |
|---|---:|---:|
| 0.5B | 0.006849 | 0.007042 |
| 1.5B | 0.013699 | 0.014085 |
| 3B | 0.017123 | 0.017606 |
| 7B | 0.023973 | 0.024648 |

これは登録済みの副次的な4点profileに限られる。Model sizeは各release checkpointと交絡しており、T10は
scale lawを同定する設計ではない。

Mistral 7B Instruct v0.3は、`0.202055`と`0.203509`で限定セル判定を通過した。既知のT9
Mistral 7B base anchorは`0.171233`だったが、両checkpointは関連しており、tuning効果を比較するように
割り当てた対照ではない。この差からinstruction tuning効果や独立再現は主張しない。

## 独立検証と証拠の方針

T10 analyzerをimportしない独立validatorで、compact bundleと返送済みraw archiveを再ハッシュした。
333個のactivation配列についてshape、FP32 dtype、有限値を確認し、18成分のrandomization、9つのIUT、
Holm補正、部分連言検定を再計算した。公開結果と完全に一致した。再ハッシュ対象はraw ledger 1,350件、
summary 27件、compact run 18件、analysis 4件である。

Git内のcompact bundleには、判定を再現できるprediction、完全なcell metrics、receipt、session記録、
shard ledgerへのbinding、analysis出力、独立検証結果を収録する。Raw activation 1,212,819,072 bytesと
model cacheはGit外に保持する。

## 主張境界と次のlane

T10が支持するのは、3つの範囲限定model/tokenizerセルにおけるalignmentと、固定規則の下での負の
モデル横断一次判定である。絵文字の意味、意味分解、因果、mechanism、behavioral relevance、
tokenization非依存性、scale law、instruction tuning効果、独立再現、architecture一般性、普遍的な
model一般性は確立しない。Phase Iの因果gateや独立再現gateも閉じない。

T11はqueueのまま未着手である。後続の変則glyph探索はexploratoryと明記し、T10の固定population、閾値、
model roster、結果を遡って変更してはならない。
