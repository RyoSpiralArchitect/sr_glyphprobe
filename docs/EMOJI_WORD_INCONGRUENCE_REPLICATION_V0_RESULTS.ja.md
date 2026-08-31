# 絵文字 × 言葉のprospective再現 v0 結果（T15-B）

[English](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md) · [凍結protocol](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md) · [Closeout](../validation/emoji_word_incongruence_replication_v0/t15b_closeout.json)

## 一段落でまとめると

T15-Bでは、T15-Aで見つかった狭いresponse-shape候補が、事前に凍結した
再現条件を通過した。8軸、48件のtarget prompt、2つのmodel roleをすべて
入れ替え、各true interactionを7通りすべてのnon-self cross-axis
checkerboardと比較した。Magnitude `0.25`におけるtarget-levelのR1中央値は、
SmolLM2 1.7B baseで`+0.020422`（95% target-bootstrap区間
`[0.012887, 0.031510]`）、Mistral 7B Instruct v0.3で`+0.060397`
（`[0.056621, 0.062194]`）だった。事前に定めた二modelのintersection ruleと、
modelごとの片側Bonferroni alpha `0.025`のもとで、両方の下限が0を上回った。
ただし、結果は一様ではない。一次doseをmodel × depth × signに分けると、正の
区間は8本中6本で、残り2本はmixedだった。Source強度、response energy、
主効果、語順、depth、doseにも不均一性が残る。今回再現したのは、運用上の
*response shape*の差である。絵文字の意味理解、矛盾検出、自然な振る舞い、
因果回路、tokenizer非依存性、instruction tuning不変性、scale law、model母集団
への一般化は、いずれも主張しない。

| 凍結した範囲 | 完了した結果 |
|---|---:|
| Model role | 2 / 2完了 |
| 新しい軸 | 8 |
| 新しいtarget prompt | 48 |
| Cross-axis shift | non-self 7通りすべて |
| Source sequence | 4,624 |
| Steering response行 | 491,712 |
| Depth × dose × sign | 2 × 2 × 2 |
| Generation call | 0 |
| Bootstrap | 各中央値につきtargetまたはaxis clusterを20,000回再標本化 |

全run監査は`complete_closed_to_adaptive_selection`、analysis validatorは
`replication_gate=support`を返した。

## 事前に凍結した一次再現gate

元になったのはT15-AのA1である。8本のtrue interaction方向が語彙全体へ
生じさせるresponseのCountSketch cosine coherenceから、構造を揃えた
cross-axis controlのcoherence中央値を引く。T15-Bではcontrolを3つの循環shift
から、7つのnon-self shiftすべてへ広げた。

Magnitude `0.25`で、modelとtargetごとに2つの後期depthと2つのsteering signを
中央値でまとめる。その48個のtarget値をbootstrap unitとした。Model間の値は、
判定のためにpoolしていない。

| Model | Target中央値 | 95% bootstrap区間 | 0より大きいtarget | 凍結gate |
|---|---:|:---:|---:|:---:|
| SmolLM2 1.7B base | +0.020422 | [0.012887, 0.031510] | 37 / 48 | pass |
| Mistral 7B Instruct v0.3 | +0.060397 | [0.056621, 0.062194] | 47 / 48 | pass |

凍結した判定規則では、両modelの2.5 percentile下限が0を上回る必要があった。
両方が条件を満たしたため、intersection判定は`support`となった。T15-Bで
多重性を考慮した再現判定は、このR1だけである。

## Cellごとの結果も隠さない

Depthとsignをまとめる方法はmodel実行前に凍結していた。ただし、個々のcellを
消してよいわけではない。

| Model | Depth | Sign | A1 true − all-cross中央値 | 95%区間 |
|---|---:|---:|---:|:---:|
| Mistral 7B Instruct v0.3 | 0.875 | − | +0.102173 | [0.093549, 0.111754] |
| Mistral 7B Instruct v0.3 | 0.875 | + | +0.076474 | [0.062852, 0.086544] |
| Mistral 7B Instruct v0.3 | 1.0 | − | +0.007967 | [−0.002336, 0.014047] |
| Mistral 7B Instruct v0.3 | 1.0 | + | +0.041554 | [0.037379, 0.051341] |
| SmolLM2 1.7B base | 0.875 | − | +0.015849 | [−0.007899, 0.029780] |
| SmolLM2 1.7B base | 0.875 | + | +0.053125 | [0.028179, 0.088221] |
| SmolLM2 1.7B base | 1.0 | − | +0.015325 | [0.004155, 0.024472] |
| SmolLM2 1.7B base | 1.0 | + | +0.014716 | [0.000623, 0.028019] |

正の区間は6本、mixedは2本だった。2つのdoseをすべて含めると、A1の16区間は
正10本、mixed 5本、負1本となる。したがって、T15-Bで再現したのは
target-levelでpoolした候補であり、T15-Aの16 / 16というcell-levelの見え方
そのものではない。

## 二次familyが解釈を狭める

A0は、個々のincongruent pairとcongruent pairのjoint-additivity residual強度を
比べる。A3は、balanced true方向のsource RMSとcross-axis方向のsource RMSを
比べる。どちらもmodel × depthの4区間すべてがmixedだった。繰り返し現れた
response shapeは、source interaction vectorが一律に強いことや、個々の
incongruent residualが共通して大きいことだけでは説明できない。

次の表は、一次doseにおける固定済み診断の区間数である。0に触れる区間と0を
またぐ区間をmixedにまとめた。

| Familyとendpoint | 正 | 負 | Mixed | 合計 |
|---|---:|---:|---:|---:|
| A0 incongruent − congruent source residual | 0 | 0 | 4 | 4 |
| A3 true − cross source RMS | 0 | 0 | 4 | 4 |
| A2 true − cross response, JS | 4 | 1 | 3 | 8 |
| A2 true − cross response, total variation | 3 | 1 | 4 | 8 |
| A2 true − cross response, logit RMS | 6 | 2 | 0 | 8 |
| A2 true − cross response, entropy change | 2 | 2 | 4 | 8 |
| A4 word-main − emoji-main, JS | 6 | 0 | 2 | 8 |
| A4 word-main − emoji-main, logit RMS | 2 | 6 | 0 | 8 |
| A5 emoji→word − word→emoji, JS | 6 | 1 | 1 | 8 |
| A5 emoji→word − word→emoji, entropy change | 4 | 4 | 0 | 8 |
| A6 final − late depth（一次dose） | 0 | 2 | 2 | 4 |
| A6 dose `0.25 − 0.125` | 3 | 3 | 2 | 8 |

Argmax flipは、一次doseのA2、A4、A5の8 cellすべてでmixedだった。普遍的な
energy増加、word優位、emoji優位、特定のsource orderの勝利、最終depthの優位、
単調なdose則は得られていない。

## 手続き上の境界

Runtimeでは2回、model weightのload前かつT15-Bのmodel forward前にfail closed
した。1回目は、隔離したdependency targetにinstalled-package metadataがない
ことを検出した。2回目は、過去のT13 tokenizer receiptを新しいT15-B target
helperで検証してしまうloader境界の不具合を検出した。どちらもruntime preflight
receiptに残している。修復では、過去のmodel load中だけ元のT13 target helperを
使い、capture前にT15-B helperへ戻した。回帰testを追加し、最終freezeも作り直した。
この時点では、科学的なoutcomeはまだ存在していなかった。

そのfreeze後、SmolLM2とMistralはそれぞれ245,856 response行を完走した。両roleの
監査が通るまで、科学値は開かなかった。最初の完全analysisは、post-openの
科学code修復なしでoutput validatorを通過した。

## 落とし所とpaper gate

T15-Bの落とし所は、**cell heterogeneityを伴う、運用上のresponse-shape候補の
prospective holdout再現**である。T15-Aの軸、target bank、model roleを入れ替え、
cross-axis controlも強化した。この狭い候補については、Phase I gate 5の
「少なくとも1つの独立model再現」を満たしたと読める。

またR1には、target clusterを単位としたbootstrapと、事前固定した二modelの
多重性規則がある。ただしpaper全体の統計資格は、manuscriptのclaim tableを凍結し、
探索familyを一次主張へ混ぜないところまで終えて初めて閉じる。
`confirmatory_status`はfalseのままであり、意味や因果の主張も許可しない。

## 次のgate

T15-Cの設計には進める。ただし、T15-Bとは別の因果実験として扱う必要がある。
きれいに閉じるには、次を事前に固定する。

- prospectiveに定義したinteraction-residual subspace
- さらに別の未使用target bank
- necessity、sufficiency、restorationの各intervention
- sham、explicit-zero check、positive control
- T15-Bの結果からrunner-upのmodel、depth、sign、dose、axis、endpoint、controlを
  選んで救済しない規則

次の中心的な問いは、A1がもう一度現れるかではない。事前に定義したinteraction
subspaceを除去・追加・復元したとき、response-shape coherenceが予測どおりに
変わるかである。

## Evidence anchor

| Evidence | Anchor |
|---|---|
| Protocol freeze | commit `fb325a1` |
| Analysis compatibility test | commit `f835999` |
| Tokenizer binding | commit `9869129` |
| Model forward前のloader境界修復 | commit `8c658f6` |
| 最終execution freeze | commit `966ea30`; manifest SHA-256 `b56a68b3aa7d8e890a9121d009e517f17329abd92c346304d3558eff1fb61f1a` |
| Design preflight | [design_preflight.json](../validation/emoji_word_incongruence_replication_v0/design_preflight.json), SHA-256 `0e584024dbe57ebfb094cebb984160c1b6e75c7883b57014a0df9638c249ae74` |
| Tokenizer preflight | [tokenizer_preflight.json](../validation/emoji_word_incongruence_replication_v0/tokenizer_preflight.json), SHA-256 `2c28af5eb89c6184eaa4d8309d8c34bb45d48483342b32b72076ede412663f38` |
| Model forward前のfailure | [runtime_preflight_failures_v0.json](../validation/emoji_word_incongruence_replication_v0/runtime_preflight_failures_v0.json) |
| 完全aggregate | Furnace path `/home/ryospiralarchitect/scratch/glyphprobe-t15b-analysis-966ea30/analysis.json`; SHA-256 `f0c98942943addcc9713283b2cb54491d16a0232711db39fc0d51d0536b4edfd` |
| Run root | `/home/ryospiralarchitect/scratch/glyphprobe-t15b-runs-966ea30` |
| Compact result | [t15b_closeout.json](../validation/emoji_word_incongruence_replication_v0/t15b_closeout.json), SHA-256 `70c5b9194bd7c0e685dbf51a3ad83f258125c6cd7ebc4fd0f185821a32cf8187` |

完全aggregateとraw ledgerは、記録したfurnace pathに置いている。Hashは同一性を
示すが、compact closeoutだけではevidence archiveのdeposit gateは閉じない。
