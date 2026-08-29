# Emoji Steering Specificity Analysis v0 — 点推定結果

[English](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) ·
[解析計画](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md) ·
[取得プロトコル](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) ·
[ゼロゲート修正](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md) ·
[コンパクト証跡](../artifacts/emoji_steering_specificity_analysis_v0/README.ja.md)

状態: **探索的な点推定解析は完了。注意事項を添えれば共有可能。論文用の区間推定ゲートは未通過**
（`completed exploratory point analysis; share with caveats; paper interval gate pending`）。

## 技術的な要約

T13-EAでは、構造を持つ一方でglyphだけには閉じない介入効果が見えた。
source-form directionはdepth 0.875付近で正方向のisotropic nullから分かれやすく、
正負の介入が出力空間で互いに逆向きになる傾向も、最終blockに近づくほど強くなる。
ただし、こうした傾向はglyph入力に限られない。Unicode name、decomposed form、
codepoint literalにも、同じ後段の優位が現れる。

分解表現についても、結論は一枚ではない。glyphとdecomposed formのsource directionは、
modifier、presentation sequence、ZWJ sequenceで強く揃う。一方、keycapとregional flagでは
近さが大きく落ちる。さらに、unit RMSへ揃えた介入では、glyphの方がdecomposed formより
非負endpointを大きく動かす傾向があるものの、その差を主に担うのはkeycapとregional flagで、
model・system・signによっては消失または反転する。

emoji固有の機構と呼べない理由は、少なくとも三つある。

1. targetのtop-two marginは、random directionでもargmax flipを強く予測する。
2. wrapper間のばらつきが、平均source directionに対して大きい。
3. tokenizer preflightで比較できるのはcount signatureまでで、token IDやprefixの完全一致ではない。

したがって、現段階で支えられる主張は限定的である。**構造を持つsource directionには、
限られた正方向isotropic nullに対して、depth・dose・target・model・glyph systemに依存する
介入幾何がある**。モデルがemoji意味に固有の機構を持つ、とまでは言えない。

## 取得範囲と完全性

固定済みの[T13-EHプロトコル](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md)は、6種類の
glyph systemに属する192 item、利用可能な912 item-form、公開済みの32 target、8 depth、
3 magnitudeを含む。item armとprototype armは正負の両signを持つが、random armは正方向のみ。
source bankは9 model/tokenizer roleから取得し、次の3 base modelで介入pilotも完了した。

- `qwen25_0p5b_base_bf16`
- `llama32_3b_base_bf16`
- `qwen25_7b_base_bf16`

pilotは合計383,232介入rowからなる。内訳はitem form 105,984、prototype 129,024、
random 147,456、zero hook 768である。generationは行っておらず、endpointは
next-token distributionだけを測っている。

| 完全性の検査 | 証跡 | 結果 |
|---|---:|---|
| 必須role | 9 / 9 | 通過 |
| receipt file | 198 | 通過 |
| receiptに結び付いたpayload | 954 | 通過 |
| summaryを含む検証済みfile | 1,161 | 通過 |
| 独立にhashを再計算したbyte | 4,535,141,572 | 通過 |
| run-binding root | `c0316c2c1b939ae831a3421c296d7eff4acd79a18747ac41eb04053ce0a88acf` | 固定済み |
| furnaceとMacで一致した派生出力 | 6 / 6 SHA-256一致 | 通過 |
| furnaceから複製したraw array | 0 | 通過 |

科学的な値を開く前に、同じanalyzer process内でfreeze、preflight binding、external closeoutを
再検証した。F4–F6では、想定したcomposite keyの重複は0件。F5のnested countも、宣言済みの
sign-pair denominatorとすべて一致した。主要な数値summaryにnullやnon-finiteはない。
F6の欠損432件は、24 atomic anchorにcomponent formとdecomposed formが存在しないという
構造的欠損を、9 model分だけ数えた値と一致する。

## v0の失敗と、別に固定したv1ゲート

当初のv0は、zero controlの`js_divergence`に厳密な0を求め、そこでfail closedした。
これは破棄した予備runではなく、手続き上の負の結果として保存している。

| 段階 | 起きたこと | 非zeroの科学値を開いたか | 取り扱い |
|---|---|---:|---|
| 過去のv0 | zero-control JSの厳密一致に失敗 | いいえ | 失敗を保存。解析出力なし |
| 修正のfreeze | live residualの厳密な大きさを見る前に、float32由来の上限を固定 | いいえ | v0とは別の事後修正 |
| v1 zero gate | 原始量は厳密なno-op、JSは`abs(JS) <= 8 * eps(float32)`を満たした | 3 roleすべてが通るまでzero rowのみ | 非zero解析を許可 |

過去のfailure receiptには、失敗値の大きさも該当model roleも記録されていない。この二点は
不明のまま扱う。現在のrowを後から旧predicateへ当てると3 pilot roleすべてが失敗するが、
これはcounterfactualな診断であり、過去の失敗roleを特定するものではない。

v1の上限は`9.5367431640625e-07`。観測されたJS round-trip residualの最大絶対値は、
Qwen 0.5Bで`3.657e-08`、Llama 3Bで`1.745e-08`、Qwen 7Bで`4.214e-08`だった。
KL、total variation、logit-delta RMS、entropy、argmax、top-tail value、CountSketchは、
原始量として厳密なno-opを保った。v1はJSの厳密な0を主張せず、科学的な効果を示すものでもない。

## F1 — item source-form contrast

F1はdepth 0.50、magnitude 0.25に固定した105,984のitem × target pairを保持する。
glyph–nameは192 item、decomposed formを含むcontrastは168 non-atomic itemを使い、
欠けたformは補完していない。

glyph minus decomposed formでは、四つの連続な非負endpointが、全model × sign summaryで正だった。

| Model | KL（sign間の範囲） | JS | TV | Logit RMS | Argmax flip |
|---|---:|---:|---:|---:|---:|
| Llama 3B | +0.003943–+0.004324 | +0.000979–+0.001024 | +0.006509–+0.006544 | +0.009605–+0.010849 | +0.002976–+0.021577 |
| Qwen 0.5B | +0.000792–+0.002714 | +0.000331–+0.000498 | +0.000691–+0.002465 | +0.002524–+0.015047 | +0.002232–+0.008185 |
| Qwen 7B | +0.004102–+0.006799 | +0.000954–+0.001733 | +0.006355–+0.010485 | +0.032531–+0.048901 | −0.006510–+0.006324 |

ただし、systemごとに見ると一様ではない。次の表はglyph minus decomposed formについて、
3 model × 2 signから得た6 summaryの単純平均を示す。

| Glyph system | KL | JS | TV | Logit RMS |
|---|---:|---:|---:|---:|
| keycap | +0.008386 | +0.002047 | +0.013085 | +0.018676 |
| modifier | −0.000841 | −0.000212 | −0.001708 | +0.002970 |
| presentation | +0.003381 | +0.000810 | +0.004964 | +0.016861 |
| regional flag | +0.009604 | +0.002352 | +0.014755 | +0.039275 |
| ZWJ | +0.002431 | +0.000591 | +0.003209 | +0.019659 |

aggregateを押し上げているのは、とくにregional flagとkeycapである。modifierではKL、JS、TVが
わずかに負になる。またQwen 7Bの正signでは、glyph minus Unicode nameが五つの非負endpoint
すべてで反転した。F1が示すのは、介入scaleを揃えたときの異質なorientation effectであって、
source formの普遍的な順位ではない。

## F2 — prototypeのdepth × dose surface

129,024 rowをすべて残したprototype surfaceでは、非負endpointのdose orderingが高い。
下表は、固定した3 doseがnondecreasingになったtargetの割合を平均した値である。

| Model | KL | JS | TV | Logit RMS | Argmax flip | Entropy change |
|---|---:|---:|---:|---:|---:|---:|
| Llama 3B | 0.9920 | 0.9919 | 0.9841 | 0.9983 | 0.9911 | 0.3096 |
| Qwen 0.5B | 0.9945 | 0.9943 | 0.9820 | 0.9985 | 0.9916 | 0.3094 |
| Qwen 7B | 0.9773 | 0.9771 | 0.9466 | 0.9681 | 0.9976 | 0.3131 |

rawの非負効果は、Llama 3BとQwen 7Bではdepth 1.0で最大になる。Qwen 0.5Bは、
argmax flipを除いて0.875が最大で、flipだけは1.0で最大だった。entropy changeには明瞭な
dose orderingもantisymmetryもない。0を完全なantisymmetryとするnormalized residualの平均は、
Llama 3Bで0.549、Qwen 0.5Bで0.642、Qwen 7Bで0.629だった。

## F3 — 正方向isotropic randomとの較正

F3は、正signのprototypeだけを、同じmodel・target・normalized depth・magnitudeにある
64本の決定論的なunit-RMS isotropic directionと比べる。負signのprototypeには、対応する
random nullがない。

正方向random distribution内でのprototype percentile平均は次の通り。

| Model | KL | JS | TV | Logit RMS | Argmax flip |
|---|---:|---:|---:|---:|---:|
| Llama 3B | 0.8081 | 0.8095 | 0.7754 | 0.8370 | 0.5246 |
| Qwen 0.5B | 0.6819 | 0.6858 | 0.6536 | 0.6876 | 0.5162 |
| Qwen 7B | 0.7488 | 0.7497 | 0.6869 | 0.7002 | 0.5084 |

KL、JS、TVの相対的なpeakは、3 modelともdepth 0.875に現れる。そのときのKL/JS/TV
percentileは、Llama 3Bで0.968/0.970/0.913、Qwen 0.5Bで0.918/0.922/0.869、
Qwen 7Bで0.969/0.970/0.884。ところがdepth 1.0では、raw responseが大きいにもかかわらず、
Qwen 0.5Bは0.476/0.508/0.519、Qwen 7Bは0.450/0.470/0.432まで下がる。
したがって、raw effectの最終層peakをspecificityのpeakとは読めない。

argmax flipのpercentileはrandom median付近に留まる。0.875の優位もglyphだけではなく、
複数のsource formに現れる。このnullで区別できるのは、構造化されたdirectionと一般的な
isotropic directionまでであり、emoji glyphと構造化されたtextを切り分けることはできない。

## F4 — target sensitivity

F4では、介入gridごとに32 targetのresponse profileへ縮約した。固定stratumのsource比較ではなく、
targetの感受性を見るためのpooled diagnosticである。

| Baseline feature → endpoint | 同じ向きだったcell | Spearmanの範囲 | 読み方 |
|---|---:|---:|---|
| top-two logit margin → argmax-flip rate | 9 / 9で負 | −0.960〜−0.668 | baseline判断が接近しているほど反転しやすい |
| baseline entropy → entropy change | 9 / 9で負 | −0.854〜−0.364 | target stateへの依存とceiling effect |

どちらの関係もrandom-direction条件で残る。target group間の幅も大きいが、上位groupは
modelやendpointで入れ替わる。安定しているのは一般的なtarget susceptibilityで、
glyph specificityではない。

## F5 — output direction

F5のCountSketchとtop-token tailは、同じmodel内だけで比較した。64,512 prototype sign pairにおける
`cos(S+, -S-)`の加重平均は0.658。

| Slice | sign-reversed CountSketch cosine |
|---|---:|
| Llama 3B | 0.731 |
| Qwen 0.5B | 0.664 |
| Qwen 7B | 0.580 |
| depth 0.125（model pooled） | 0.415 |
| depth 1.0（model pooled） | 0.946 |
| magnitude 0.125（model pooled） | 0.764 |
| magnitude 0.25（model pooled） | 0.731 |
| magnitude 0.50（model pooled） | 0.479 |

depthとともに高まり、高doseで崩れる点は、局所線形性の仮説と整合する。readoutに近い介入ほど
符号反転が保たれ、早い層や大きな介入ほど非線形な計算を通る、という見方である。ただし、
これは候補となる説明にすぎない。2,016 prototype summary cellのうち11 cellでは、
sign-reversed cosineの平均自体が負だった。多くはQwenのhigh-dose cellで、最小値は
Qwen 7Bのkeycap/decomposed form、depth 0.25、magnitude 0.50における−0.369である。

modelをまたぐtarget-rank concordanceも一様ではない。Spearmanの中央値は、Qwen 0.5B–Qwen 7Bで
0.480、Llama 3B–Qwen 0.5Bで0.391、Llama 3B–Qwen 7Bで0.240だった。
raw sketch coordinateやtoken IDはmodel間で比較していない。sign-reversed cosineは元のcosineを
代数的に反転した値で、独立した第二の証拠ではない。また、sign-matched random controlもない。

## F6 — source geometry

F6は9 roleのsource bankを監査する。保存された65,664本のmean directionはすべて、
4 wrapper deltaから独立に再計算した平均と一致した。

| 同一model内のsource-form pair | item加重cosine |
|---|---:|
| glyph ↔ decomposed form | 0.844 |
| glyph ↔ Unicode name | 0.599 |
| Unicode name ↔ decomposed form | 0.586 |

decomposed formを含むpairからは、このformが構造上存在しない24 atomic anchorを除いている。
glyph–nameの母集団は192 itemすべてである。

glyph–decomposed alignmentはsystemによって大きく違う。

| System | Cosine |
|---|---:|
| ZWJ | 0.940 |
| modifier | 0.926 |
| presentation | 0.902 |
| keycap | 0.646 |
| regional flag | 0.633 |

最初と最後の登録depthを比べると、glyph–decomposedは0.885から0.769、glyph–nameは
0.701から0.407、name–decomposedは0.686から0.423へ下がる。Gemma 2Bだけは一貫した例外で、
final-minus-firstが順に+0.026、+0.120、+0.149となった。残る8 model roleは、利用可能な
すべてのpairについてmodel平均が負である。

wrapper依存も小さくない。wrapper-to-direction cosineのmodel平均は0.597〜0.667、
wrapper residual RMSをmean-direction RMSで割った値は1.115〜1.348。depth方向ではU字を描き、
cosineは最初の0.719から中盤の約0.596まで下がり、最後は0.704へ戻る。

count-signature matched summaryのpooled cosineは0.748、unmatchedは0.662だった。ただし、
この差には構成比の影響がある。同じmodel/system/pair/depthにmatchとunmatchの両方がある592組では、
差の中央値は+0.0118に留まり、204組は負。glyph–decomposedに限ると平均差は−0.0099だった。
token countだけで全体を説明することはできないが、exact tokenizationはまだ未検証である。

## 分解表現から組み立てられる、現時点で最も強い筋

六つのfamilyをつなぐと、次の三段階が見えてくる。

1. **source geometryの共有。** 見た目の構成を明示的に持つsystem、とくにmodifier、
   presentation sequence、ZWJ sequenceでは、glyphと決定論的なdecompositionが近い。
2. **残るorientation差。** unit RMSに揃えても、glyphはdecomposed formよりnext-token distributionを
   やや大きく動かすことがある。差が目立つのはregional flagとkeycapで、modifierや一部の
   Qwen 7B cellでは弱まるか反転する。
3. **後段のstructured-direction gain。** 複数のsource formがdepth 0.875付近で正方向isotropic nullを
   上回る一方、最終層ではraw effectが大きくてもrelative calibrationが落ちる場合がある。

この筋が扱うのは、構造を持つsource directionと、それがresidual streamへ入る位置である。
semantic decomposition、tokenization、wrapper context、文字列の構造、その他の共有特徴は、
まだ切り分けられていない。

## 負の結果と異質性

- KL、JS、TV、RMSよりも、argmax flipのrandom較正は弱く、random median付近に留まった。
- 二つのQwen roleでは、raw effectが最大になる最終層と、random-relative specificityのpeakが一致しない。
- entropy changeには、明瞭なdose orderingもscalar antisymmetryもなかった。
- glyph–decomposed outcome contrastはsystem依存で、modifierはaggregateの向きに従わない。
- Qwen 7Bの正signでは、glyph–name orderingが反転した。
- prototypeのoutput directionには、平均しても符号反転しないcellが11件あった。
- modelをまたぐtarget rankingは一貫していない。
- F6の主なdepth trendは、Gemma 2Bだけが逆向きだった。
- wrapper residual variationは、mean direction RMSと同程度以上だった。
- count-signature matchingは、一様なgeometry shiftを作らなかった。

これらは論文執筆前に除くcellではなく、そのまま残す結果である。

## データ品質と検証状況

| Gate | 判定 | 意味 |
|---|---|---|
| 固定済みacquisitionの完全性 | **PASS** | 9 roleと登録artifactをすべて検証 |
| set内のschema・grain・hash | **PASS** | exact binding、想定済みの構造的欠損、検査したcompact tableでkey重複なし |
| furnace–Mac間の派生出力 | **PASS** | 6 / 6 fileがSHA-256で一致 |
| 過去のv0 exact-JS gate | **FAIL（保存）** | 非zeroを開く前にfail closedした手続き上の負の結果 |
| 別に固定したv1 primitive-no-op / bounded-JS gate | **PASS** | 原始量は厳密、JSはalgorithm由来の上限内。exact JSではない |
| 全familyの点推定 | **PASS** | outcomeによる救済や除外なしでF1–F6を出力 |
| 登録済みの区間推定 | **PENDING** | bootstrapは0 / 20,000 replicate |
| exact token / prefix matching | **未達** | preflightが持つのはcount signatureまで |
| 行動・確認・外的妥当性 | **未確立** | 公開target、3 pilot、generationなし、未使用targetでの確認なし |

注意事項を明示した探索報告と、次の識別実験を選ぶ材料としては使える。ただし、論文用の
区間推定やconfirmatory conclusionに進める状態ではない。

## Bootstrapと論文ゲート

ここまでの値はすべてpoint estimateである。登録済みのpercentile cluster bootstrapは、
seed `2026082913`で20,000 replicateを要求するが、実行数は0。現在のone-shot CLIは、
決定論的な高位のchunk-and-merge contractとしては、まだfreezeされていない。まず実行契約を固定し、
すべての登録chunkを完了して、決定論的なhash mergeを通す必要がある。それまではpaper interval gateを
閉じたままとする。点推定を見たあとで、family、cell population、endpoint、resampling ruleを
選び直すことはできない。

## 主張できない範囲

- **Exact token:** 比較できるのはraw token countとadded-count signatureまで。token IDとprefix identityは未比較。
- **Wrapper:** source directionは4 public wrapperの平均だが、wrapper invarianceは未確立。
- **Random control:** unit-RMSの正方向isotropic nullのみ。負方向、activation covariance、
  activation manifold、orthogonalized nullはない。
- **Text control:** token条件を揃えたordinary textやnon-emoji Unicode対照はない。
- **Target:** 32 targetはすべて公開済みで、未使用の確認用bankではない。
- **Model:** F1–F5は3 base-model pilot。F6は9 roleだが、hidden coordinateやvocabulary coordinateを
  model間で直接比較していない。
- **Scale:** source directionをunit RMSへ正規化しているため、自然なencoding strengthは比較できない。
- **Behavior:** 測ったのはnext-token distributionだけで、generationやdownstream task behaviorは未評価。

したがって、T13-EAからemoji meaning、emoji固有性、機構、tokenizer independence、scale law、
model populationへの一般化、behavioral steering、独立再現、confirmatory verdictは導けない。

## 次に行う識別実験

1. emoji、decomposed form、ordinary text、non-emoji Unicodeについて、exact token IDとprefixを
   揃えたcontrolを、新しいoutcomeを取る前にfreezeする。
2. 同じmodel・target・depth・dose stratumへ、正負random、covariance-matched null、
   activation-manifold-matched nullを追加する。
3. 4 wrapperのうち3本でdirectionを作り、残る1本で評価するwrapper holdoutを、holdoutを回しながら行う。
4. depth 0.875と1.0の分離を、狭いdepth gridとrelative-to-null endpointを事前登録して検証する。
5. Gemmaのtrajectoryをbase/instruct pairと別sizeで再現してから、architectureやtuningへ帰属する。
6. T13-Cでは未使用target bankを確保し、primary endpointとmultiplicity familyを先に宣言する。
7. representationとnull controlを通過したあとで、generation-levelのbehavioral endpointを追加する。

## コンパクト証跡

最終的なindexは
[`artifacts/emoji_steering_specificity_analysis_v0/README.ja.md`](../artifacts/emoji_steering_specificity_analysis_v0/README.ja.md)
へ置く。point-results closeoutが結び付ける現在の派生出力は次の通り。

| 派生file | SHA-256 |
|---|---|
| `outcomes-v1-point.json` | `df0ddc58c8e98d6ca0c763cd7bc71821a10af4dad84cda5a92822abf8ecfd615` |
| `zero_hook_exact_primitives_bounded_js_v1.json` | `51a3beddbc5342aefea8be9f37ecdb7d870074056db3686ac220685c985c75de` |
| `analysis_receipt.json` | `c69f93706b20f0ddc70688aa1819376523049dd91dd2918c7c88d90c5dab7c58` |
| `F4_target_sensitivity.json` | `e7d8a1a3c4e781fced9ab2f8080f16d1b00d2516ffb2f8353c563df7a2b63ec9` |
| `F5_output_direction.json` | `e6eee30b93b61cd812f122385d78c53d82ac9cd7b30c76e0fb9daa8218d840cb` |
| `F6_source_geometry.json` | `f00f8a7b27976cf9d1cd51f97bee1c66a6d27cccb22b6cc3ffb3871fa9107916` |

repository側のprovenanceは、
[input closeout](../validation/emoji_steering_specificity_analysis_v0/glyphprobe-t13ea-closeout-7fedd40.json)、
[過去のv0 failure receipt](../validation/emoji_steering_specificity_analysis_v0/zero_gate_v0_failure_receipt.json)、
[point-results closeout](../validation/emoji_steering_specificity_analysis_v0/point_results_closeout_979533f.json)
に残してある。analyzer commitは`979533f64e9b25c48d56859a83ee4931ae47cde1`。
