# Milestone 2 結果: トークン数・接頭構造を揃えた対照

[English](MILESTONE2_RESULTS.md) · [プロトコル](MILESTONE2_PROTOCOL.ja.md) · [ロードマップ](ROADMAP.ja.md) · [アーティファクト・マニフェスト](../artifacts/MILESTONE2_MANIFEST.json)

## 結果の要点

凍結済みv1解析の結果は、レイヤーによって分かれた。

| ソースラッパー | レイヤー | 調整済みターゲット効果の平均 | v1 bootstrap 95% CI | Holm補正済み片側p値 | 凍結済みv1判定 |
|---|---:|---:|:---:|---:|---|
| 主要ソース | 2 | +0.208363 | [0.137463, 0.276893] | 0.00143999 | 指定済みmatched controlsに対して頑健 |
| 主要ソース | 4 | -0.0329465 | [-0.0761085, 0.0110094] | 0.999500 | 未解決 |
| 独立ソース | 2 | +0.187507 | [0.125489, 0.247659] | 0.00393996 | 指定済みmatched controlsに対して頑健 |
| 独立ソース | 4 | -0.086379 | [-0.159246, -0.016917] | 0.999430 | 未解決 |

実質的な正の超過量の最小値は、`delta = 0.06`に凍結していた。v1で「頑健」と判定するには、区間下限が`0.06`を上回り、layer 2と4に対するHolm補正後も片側sign-flip p値が`0.05`未満でなければならない。Layer 4は、どちらのソース条件でも未解決である。独立ソースでは区間全体が負だが、正方向の頑健性規則にも実用的同等性の規則にも該当しないため、「効果なし」とは判定しない。

独立ソース条件で変えたのは、方向推定に使うソースラッパーだけである。48件のP2ターゲット、モデル、トークナイザー、バックエンド、レイヤー、評価量は共通している。したがって、これはソース構成に対する頑健性検査であり、独立したターゲット、バックエンド、モデルでの再現ではない。

結果を見る前の公開凍結は、commit `2be9f5be6181b24ff8ebf96ab42445d80dd936a9`である。P2のmodel forwardを開始したのは、このcommitをpushした後だった。

## 比較したもの

事前指定した6群、計48件の凍結済みP2ターゲットについて、ターゲット間で条件を識別できるかを測った。同一条件のleave-one-target-group-out prototypeに対するcosine類似度の平均から、他条件に対する平均を引く。3つのdirection seedは各ターゲット内で平均した。ターゲット単位の評価量は次のとおりである。

```text
D[t] = 色付き図形のscore[t] - median(null A[t], null B[t], null C[t])
```

10記号からなる3つのnull panelは、色付き図形パネルと、指定済みのGPT-2トークン数およびパネル単位の9対1の接頭構造を揃えている。ただし、token IDは同一ではない。完全に同じtoken ID列は同じ入力byte列へ復号されるため、別のglyph入力にはならない。Panel Cには、意味的に近い保守的対照として、参照パネルにない赤い四角`🟥`を事前申告のうえ1個だけ含めた。主要prefixに該当する非色付き記号が26個しかなく、互いに重ならない3 panelの27枠に1枠足りなかったためである。残る29件は非色付き記号である。

したがって、認められる表現は「**指定済みのトークン数・トークン接頭構造を揃えたパネルに対して頑健**」までである。「トークン化の影響を取り除いたglyph効果」とは言えない。

## 探索段階のmatched-panel比較

一度限りのP2解析に先立ち、既存の24ターゲットによる探索行列をnull panel A/B/Cと比較した。元の96次元CountSketchでは、色付き図形scoreからmatched-null 3 panelの中央値を引いたセル差の中央値は`+0.047427`だった。36個のlayer–seed–strengthセルのうち25セルが正、11セルが非正である。

これは記述的な結果に限る。36セルはターゲットと反復的な実験構造を共有しており、独立した観測ではない。また、この差は割合ではないため、「元の結果の何%をトークン化で説明できたか」は推定できない。

| CountSketch次元 | セル差の中央値 |
|---:|---:|
| 96 | +0.047427 |
| 48 | +0.040200 |
| 32 | +0.028907 |
| 24 | +0.048591 |

48、32、24次元は、保存済み96次元sketchを、同じseedのまま代数的に畳み込んだ値である。ひとつの固定seedにおける次元圧縮への感度は見られるが、CountSketchのseed感度でも、独立した再実行でもない。

## 凍結済みv1推論の限界

v1 analyzerは、固定したモデルセル、P2ターゲットのIDと群、layer・strength・seed family、完了済みrun receipt、互いに重ならないcondition ID、target単位の標本構造、Holm補正familyを検査する。ただし、重要な留保が2点ある。

第一に、4つの科学的役割はCLI引数の順序、すなわちprimary、null A、null B、null Cの順に割り当てられる。Analyzer内部の検査だけでは、各run directoryが意図した凍結済みpanelとsource configから生じたことまで暗号学的に確定しない。この空白は、別の[input-binding audit](../artifacts/milestone2/input_binding_audit.json)で補った。凍結済みpreregistration manifestとauditを根拠に、公開した全14 run、すなわち探索・P2・独立ソースの中核12 armと診断2 runについて、config-role、panel-role、source family、target bank、input path、input hashの完全一致を確認し、すべて合格している。

第二に、v1は観測済みP2 bank全体からleave-one-target-group-out prototypeを一度だけ作り、各targetの効果を計算した後、その固定済みtarget効果をbootstrapする。Bootstrap replicateごとにprototypeを作り直してはいない。したがって、v1推論は観測済みprototypeを条件としており、prototype推定に伴う再標本化依存を含まない。p値と判定は凍結済み確認出力として残し、後述する事後解析で遡って分類し直すことはしない。

## 事後的な依存感度分析

そこで別の事後解析を行った。Primary panel、null panel A/B/C、両レイヤー、3つの固定seedに同じ層別target抽出を共同で適用し、各replicate内で、すべてのleave-one-target-group-out prototypeを作り直した。

| ソースラッパー | レイヤー | 点推定 | Prototype再構築95%区間 | 同一抽出による固定prototype区間 |
|---|---:|---:|:---:|:---:|
| 主要ソース | 2 | +0.208363 | [0.099930, 0.295380] | [0.137463, 0.276893] |
| 主要ソース | 4 | -0.0329465 | [-0.099995, 0.041902] | [-0.076108, 0.011009] |
| 独立ソース | 2 | +0.187507 | [0.104210, 0.271322] | [0.125489, 0.247659] |
| 独立ソース | 4 | -0.086379 | [-0.185084, 0.007648] | [-0.159246, -0.016917] |

この方法を定めたのはP2結果の確認後であり、得られた区間は記述的な感度区間である。p値、Holm補正、実用的同等性判定、確認的statusは付与しない。固定panel、固定seed、固定group label、経験的なP2 target bankを条件とし、panel選択やseed選択の不確実性も推定していない。正確な数値と方法は、[主要ソースの感度分析receipt](../artifacts/milestone2/analyses/posthoc_dependence/p2/m2_dependence_sensitivity_receipt.json)と[独立ソースの感度分析receipt](../artifacts/milestone2/analyses/posthoc_dependence/independent_source/m2_dependence_sensitivity_receipt.json)に収録した。上記の凍結済みv1判定は上書きしない。

## 完了した二次診断

末尾tokenを揃えて中間tokenだけをずらすpanelと、色付き図形の接頭構造を全条件で均一にするpanelについて、それぞれ14,208行からなる探索gridを完走した。どちらもerrorは0件、zero-hook RMSは0、readinessは11 / 11だった。

| 診断panel | 行数 | Error | Zero-hook RMS | Readiness | Headline `emoji_fingerprint_advantage` |
|---|---:|---:|---:|---:|---:|
| 末尾token一致・中間tokenずらし | 14,208 | 0 | 0 | 11 / 11 | +0.751225 |
| 接頭構造を均一にした色付き図形 | 14,208 | 0 | 0 | 11 / 11 | +0.601038 |

このheadline値はrandom-adjustedのrun summaryである。以下のpaired comparisonで使うraw separation scoreとは別の評価量であり、同一視してはならない。

| CountSketch次元 | Standard minus suffix raw separationの中央値 | Standard minus prefix-homogeneous raw separationの中央値 |
|---:|---:|---:|
| 96 | +0.002624 | +0.022096 |
| 48 | +0.009473 | +0.023254 |
| 32 | +0.004026 | +0.011040 |
| 24 | +0.009700 | +0.025387 |

96次元では、standard minus suffixは36セル中20セル、standard minus prefixは36セル中25セルが正だった。いずれも事後的・記述的な診断であり、確認的検定でも同等性解析でもない。48、32、24次元の値は、同じseedによる代数的な畳み込みであって、sketch seed感度でも独立した再実行でもない。

実行時の来歴として、ひとつの不規則事象も残す。Matched-null Aの最初のforeground processは、マシン負荷が極端に高い最中、ledger 798行の時点で外部から中断された。Median latencyはbaselineの10.73 msに対して約309 msだった。Sealを保ったresumeによって14,208行の正確なgridを完了し、重複・欠損はなく、errorは0件、zero-hook RMSも0だった。その後のmedian latencyは約12.43 msへ戻った。これは運用上の来歴であり、モデルに関する証拠でも、一般化できる速度の主張でもない。P2、独立ソース、診断runは通常どおり完了した。

C1因果ホールドアウトは未使用のままである。モデル入力にも、結果解析にも使っていない。

## 主張の境界と次の判断

Milestone 2から言えるのは、次の限定した内容だけである。固定したGPT-2 FP32 MLX `resid_post`セルでは、layer 2が、凍結済みv1規則のもとで3つのトークン数・接頭構造matched panelを両方のsource-wrapper bankで上回った。Layer 4は通過しなかった。この結果は、glyphの意味、機構、回路、因果経路、トークン化から独立した効果、このセルを越えた一般化を確立しない。

運用上のMilestone 2は完了した。Layer 2は、未使用のC1 bankを使う、新しい対象限定型の因果プロトコルを設計できる段階に入った。Layer 4は未解決のままで、候補にはしない。C1を開く前に、候補、介入部位と操作、endpoint、対照、多重性familyをすべて凍結する。この判断で認めるのはプロトコル設計であり、因果主張ではない。

Phase Iの終点は、英語論文と日本語の公開概要のままである。論文には、レイヤーごとに分かれた結果、v1と事後感度分析それぞれの不確実性境界、完了した記述的診断、残る因果・再現ゲートをすべて記載する。最終的な確認的表現と、それを支える再現実験では、analyzerのrole bindingとprototype再標本化依存に事前に対処しなければならない。

## エビデンス一覧

- Milestone 2軽量バンドルと省略記録: [artifacts/MILESTONE2_MANIFEST.json](../artifacts/MILESTONE2_MANIFEST.json)
- 結果を見る前の公開凍結: commit `2be9f5be6181b24ff8ebf96ab42445d80dd936a9`。P2のmodel forwardはpush後に開始
- 凍結済みプロトコル: [MILESTONE2_PROTOCOL.ja.md](MILESTONE2_PROTOCOL.ja.md)
- 主要ソースv1 receipt: [m2_confirmatory_receipt.json](../artifacts/milestone2/analyses/confirmatory/p2/m2_confirmatory_receipt.json)
- 独立ソースv1 receipt: [m2_confirmatory_receipt.json](../artifacts/milestone2/analyses/confirmatory/independent_source/m2_confirmatory_receipt.json)
- 探索96次元paired comparison: [matched_panel_comparison_dim96.json](../artifacts/milestone2/analyses/exploratory/matched_panel_comparison_dim96.json)
- Input-binding audit: [input_binding_audit.json](../artifacts/milestone2/input_binding_audit.json)
- 主要ソースの事後感度分析: [receipt](../artifacts/milestone2/analyses/posthoc_dependence/p2/m2_dependence_sensitivity_receipt.json)
- 独立ソースの事後感度分析: [receipt](../artifacts/milestone2/analyses/posthoc_dependence/independent_source/m2_dependence_sensitivity_receipt.json)
- 末尾token診断の96次元paired comparison: [suffix_vs_standard_dim96.json](../artifacts/milestone2/analyses/diagnostics/suffix_vs_standard_dim96.json)
- 接頭構造均一化診断の96次元paired comparison: [prefix_homogeneous_vs_standard_dim96.json](../artifacts/milestone2/analyses/diagnostics/prefix_homogeneous_vs_standard_dim96.json)
