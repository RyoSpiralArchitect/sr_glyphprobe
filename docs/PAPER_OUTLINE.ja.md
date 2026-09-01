# Phase I 英語論文の構成案

[English](PAPER_OUTLINE.md) · [現在のT19ストーリー](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md) · [T19結果](T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) · [T17前史](PAPER_STORY_T17_GLYPH_NAME_V0.ja.md) · [T17深度atlas結果](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md) · [T16ストーリー](PAPER_STORY_T16_V0.ja.md) · [ロードマップ](ROADMAP.ja.md) · [T16 運用行動・因果結果](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.ja.md) · [T16 後期band結果](T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.ja.md) · [T16 完全同一UTF結果](T16_UTF_IDENTITY_MIXING_V0_RESULTS.ja.md) · [T15-B再現](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md) · [T12 reserve結果](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [T13設計図](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) · [T11探索結果](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [T10 model横断結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) · [基準実験の結果](RESULTS_V1.ja.md)

この文書は、日本語で研究設計を確認するための構成案です。Phase I の論文本体は英語で執筆します。

## 仮題

**Beyond Short Names: Cross-Model Emoji Lexical Neighborhoods Without a Simple Late-Layer Mediator**

回路発見ではなく、行動上の読み出しと因果実装が分かれた点を中心に置く。Sufficiencyが
通らなかった結果を、特定の分散回路を発見した証拠へ読み替えない。

## InterpScience 2026提出sprint

公式の[InterpScience Call for Papers](https://interpscience.github.io/cfp)では、締切を
**2026年9月1日 Anywhere on Earth**としている。Short paperは本文5ページまで、
long paperは9ページまでで、referencesとappendixはページ数に含まれない。第一候補は
long paperとし、証拠を伴う物語を時間内に綺麗に編集できない場合は5ページ版をfallbackにする。

9月1日09:00 JSTの時点で、9月1日AoEの終了までは約36時間ある。AoEはJSTより21時間遅い。
科学的な実行の背骨はT19-LとT19-Cまで完了した。残るcritical pathは原稿作業である。
Claim tableをfreezeし、検証済みsummaryへ戻れるfigureだけを作り、checksum・omission archive、
double-blind検査、fresh-eyes reviewを完了し、OpenReview上の登録を確認できる余裕を残してuploadする。
T19-Cの適応的な追加site探索は、このcritical pathに入れない。

## 現時点で守れる中心命題

現在の中心は、回路の発見ではなく、証拠階層の分離である。Atomic emojiは、literal
codepointより、正式短名と語が重ならないCLDR keywordを、凍結した9つのmodel/tokenizer
cellすべてでよく検索した。4-viewのtoken数完全一致解析でも同じだった。非emoji Unicode
記号panelでは、正式名検索はより広く見える一方、alias効果は小さく不均一だった。続く
登録済みrank 8後期component介入は、すべてのengineering controlを通過したうえで、未使用
emoji 192件に対して必要かつ十分な一次`attn_out`または`mlp_out`部位を見つけなかった。

投稿用の詳しい物語、figureの背骨、許可・不許可claim table候補は
[T19論文ストーリー](PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md)にまとめた。T16〜T18は
重要な前史とエビデンス台帳として残すが、それぞれ単独では現在の中心命題を定めない。

## T17 — 表現atlasの前史

T17-GNは、より狭く澄んだ中心候補を与えた。Raw emoji surfaceが、literal codepoint識別子より
Unicode正式名へ対応する過程を、9モデル × 9深度で追う。Name-minus-codepoint top-1点推定は、
正規化深度`0.375`以降9 / 9で正だった。一方、peakは最初のblockから`0.875`まで分かれた。
最終paired marginは9 / 9でnameを支持したが、centered linear CKAは4 / 9だけだった。
したがってglobalなname manifoldより、item固有の語彙対応を強く支持する。

論証全体とfresh population gateは[T17別案ストーリー](PAPER_STORY_T17_GLYPH_NAME_V0.ja.md)にまとめた。
292項目はT9/T10ですでに開いているため、T17は探索的である。T18が未提示表層でprospectiveな確認を
与え、T19が語彙endpointを広げて別の因果説明を検定した。T17は現在、論文の確認的な背骨ではなく、
深度trajectoryを与える前史として扱う。

## 現在のMilestone 2主張表

| 条件 | レイヤー | 凍結済みv1結果 | 事後prototype再構築感度 | 現時点での論文上の扱い |
|---|---:|---|---|---|
| 主要ソース | 2 | +0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999、頑健 | [0.099930, 0.295380] | 正の候補。事後区間を確認結果へ格上げしない |
| 主要ソース | 4 | -0.0329465、[-0.0761085, 0.0110094]、未解決 | [-0.099995, 0.041902] | 未解決の負・mixed evidence |
| 独立ソース | 2 | +0.187507、[0.125489, 0.247659]、Holm p = 0.00393996、頑健 | [0.104210, 0.271322] | source構成への頑健性。独立target/model再現ではない |
| 独立ソース | 4 | -0.086379、[-0.159246, -0.016917]、未解決 | [-0.185084, 0.007648] | 未解決の負・mixed evidence |

事後解析は、共同target bootstrapの各replicate内で、すべてのleave-one-target-group-out prototypeを作り直す。p値やstatusは付与せず、v1も上書きしない。独立ソースの正確な数値と限界は、公開済み感度分析receiptへ結び付ける。

## 現在の二次診断表

2つの診断runはいずれも14,208行を完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline `emoji_fingerprint_advantage`は、末尾token一致が+0.751225、接頭構造均一化が+0.601038だった。このheadline値は、下表のraw separation scoreとは別の評価量である。

| CountSketch次元 | Standard minus suffix raw separationの中央値 | Standard minus prefix-homogeneous raw separationの中央値 |
|---:|---:|---:|
| 96 | +0.002624 | +0.022096 |
| 48 | +0.009473 | +0.023254 |
| 32 | +0.004026 | +0.011040 |
| 24 | +0.009700 | +0.025387 |

96次元で正だったのは、suffixが20 / 36セル、prefixが25 / 36セルである。これは事後的・記述的な診断であり、推論や同等性の解析ではない。低次元値は同じseedによる代数的な畳み込みで、独立した再実行でもseed感度でもない。

## 現在のE1探索side result

E1では、10 glyphからなる5 familyについて、第1・第3 GPT-2 tokenをfamily間で
固定し、中間tokenだけを置換した。Family等重みのglobal specificityは、
layer 2で0.014752595564（95%記述区間
[0.002875238085, 0.027439243404]）、layer 4で0.014887989201
（[0.003407563347, 0.019684351979]）だった。Family別区間は、両layerの
5 familyすべてで0を含んだ。Transfer行列は広く正で、layer 2では
0.395455〜0.484915、layer 4では0.602564〜0.681909だったが、
family × layer × seedの30 cell中10 cellはrandom controlを上回らなかった。

事前指定したlayer 4のnegative comparatorはnegativeにならなかった。
したがって、許される解釈は、固定した中間token置換下で共有tokenに結び付く
matched-slot反復が見られ、family固有の上乗せは小さかった、という範囲に
限られる。意味上のfamily構造、tokenizer非依存性、layer固有性、random
controlに対する頑健な優位性、因果性は主張しない。E1は探索済みtarget
24件を再利用し、P2とC1を使っていない。Milestone 2の判定も論文gateも
更新しない。

## 現在のtokenizer control設計証拠

固定multifamily censusは、14 tokenizer entry、115 item、4 contextを、model forwardと
protected-target accessを0に保って完了した。Entryは固定surface上で7つの完全一致output
classへまとまった。Blue circleとblue squareのどちらにも、どの固定pairwise contextにも、
全classでtoken数と先頭1 tokenを同時に揃える単一fixed-panel candidateはなかった。

論文では、tokenizer別control設計の記述的な動機と、cross-tokenizer transportの限界として
のみ使える。Activation evidence、確認結果、tokenizer非依存の構造、論文gateの完了として
扱わない。後続のcross-tokenizer activation結果では、tokenizer output classごとにcontrol
setを事前に直接結び付ける。

## 現在のmultifamily観測結果

凍結済みT2では、2つのraw-glyph `resid_post` cellについて、midpointの
circle-minus-square平行性だけをprimaryにした。Gemma 2 2B 4-bitは
`T = 0.114857969`、raw `p = 0.058333333`、Holm `p = 0.116666667`。
OLMo 3 7B BF16は`T = 0.024628040`、raw・Holm `p = 0.275`だった。
どちらも棄却せず、登録済みpatternは`no_dual_model_recurrence`である。

固定深度の全10行を残すが、modelごとの非midpoint 4行には多重性判定の権限がなく、
primary layerと差し替えられない。論文では、現在のmodel-general shape-axis claimを
支持しない、範囲を限った負・mixed observational evidenceとして使える。Model family、
scale、precision、tokenizer、nodeが交絡しているため、cell差の原因は推定しない。
独立backend再現でもなく、Milestone 2や因果候補も変更しない。

## 現在のmatched-slot観測結果

別に凍結したT3では、公開済みの10 emoji × 5 familyを正確な5 × 10格子として
使った。Family平均を引いた後、slot平方和比率を固定5深度で等重み平均した値を
主統計量とした。Gemma 2 2B 4-bitでは50 glyphがすべて別々のatomic tokenであり、
`T = 0.204304805`、null平均`0.199984463`、Holm `p = 0.208500`だった。
OLMo 3 7B BF16では、5 familyが同じslotで厳密に同じ末尾tokenを使い、
`T = 0.500391869`、null平均`0.200184835`、Holm `p = 0.000100`だった。

登録済みpatternは`olmo_only_token_structured_recurrence`である。OLMoの固定深度別
slot比率は`0.994722`から`0.295828`まで下がった。深度別の5つのp値は副次的で、
all-depth endpointと差し替えられない。論文では、OLMoの結果にはtoken構造だけで
十分な代替説明が残る、tokenizer条件付きの観測evidenceとして扱う。Tokenizerの
因果性、意味、確認的結論、model scale、precision、backend、nodeの効果は推定しない。

## 現在のcommon-suffix carryover結果

結果を見る前に固定したT4では、読み出しを1 token後ろへ移した。生の絵文字token列を
厳密に保ったまま、その後ろに共通のperiodまたはnewline tokenを1個だけ加えた。主統計は
固定2文脈×5深度を等重み平均した。Gemmaは`T = 0.203443011`、null平均
`0.200044692`、Holm `p = 0.302950`だった。OLMoは`T = 0.537464703`、null平均
`0.199977865`、Holm `p = 0.000100`だった。

登録済みpatternは`olmo_only_common_suffix_carryover`である。OLMoの副次的なperiodと
newline統計は`0.538985382`と`0.535944025`だった。論文では、T3のrecurrenceが共有slot
tokenそのものを読む位置だけに閉じず、固定した両文脈で1つ後ろの共通tokenにも観測
できると記述できる。同時に、OLMoの構造化prefixからの短距離伝播だけで十分という説明を
残す。T4は意味、因果、確認、tokenizer非依存性、model-scale contrastを示さない。

## 現在のcarrier-distance結果

結果を見る前に固定したT5では、入力全体と現在位置のcarrier tokenを変えず、生の絵文字から
1、2、4、8 token後ろの同じgeometryを読み出した。唯一の主判定はmodel単位の
intersection-union testであり、距離1でのrecurrenceと、事前指定した正のlog-distance
減衰contrastの両方を要求した。Raw IUT p値はGemmaが`0.573250`、Llamaが
`0.188000`、OLMoが`0.997700`、Holm補正後は順に`1.000000`、`0.564000`、
`1.000000`だった。棄却したmodelはなく、登録済みpatternは
`no_model_distance_attenuation`である。

LlamaとOLMoの距離1成分のraw p値はいずれも`0.000050`だったが、IUTが要求する固定した
減衰成分は通らなかった。副次的な
距離8のslot比率はLlamaが`0.369105`、OLMoが`0.527099`、Gemmaが`0.204289`
だった。これらのtail値と完全なdistance × depth interactionには多重性判定の権限がない。
したがってT5が支持するのは、単純なmodel-level減衰仮説に対する範囲を限った負の結果である。
単調減衰、消失、持続時間、意味、機構、因果、確認、tokenizer非依存性、backend parity、
cross-modelの大きさ比較は示さない。LlamaのMLX Stage-A parityも未資格のままである。

## 現在のdense CUDA carrier-distance結果

T6は、T5の観測endpoint全体を、選択した4つのBF16 Transformers/CUDA cellへprospectiveに
固定した。Raw IUT p値はGemma 2 2B ITが`0.770900`、Gemma 3 4B ITが`0.845150`、
Mistral 7B Instruct v0.3が`0.469750`、Gemma 3 12B ITが`0.975750`で、Holm補正後は
すべて`1.000000`だった。登録済みpatternは`no_dense_model_distance_attenuation`である。

Mistralの距離1成分はpermutation下限`0.000050`だったが、減衰成分は`p = 0.469750`だった。
Mistralの距離8成分とGemma 3 12Bの名目的tailには、多重性判定の権限がない。RosterはT5後に
選び、4 cellはすべてinstruction-tunedで、Gemma 3 4B・12Bも選択した1 pairにすぎない。
したがってT6が加えるのはconjunctionに対する範囲を限ったdense負結果であり、確認、backend
parity、tokenizer同等性、scale効果ではない。

## 現在のMistral semantic-atlas確認結果

T8では、842件のdiscovery itemだけを見た後で、layer 31のretrieval contrastを固定した。
続くT9では、reserve forwardを一度も行う前に、決定論的に選定した`reserved_unrun` 292件すべて、2 carrier、
4距離、1つのprimary最小統計、実用下限`0.02`、共通permutation 19,999回を固定した。

Reserveにおけるglyph→Unicode正式名 top-1とglyph→codepoint top-1のcontrastの最小値は
`0.171233`で、8つすべてのcarrier-distance cellが実用下限を通過した。観測最小統計以上の
null drawは0件で、事前指定した片側p値は`0.00005`だった。Centered linear CKAは8 cell中
7 cellでglyph/nameを支持したが、`article_a`・距離8ではcontrastが`-0.007682`だった。

したがって論文では、後期深度におけるmodel固有・item-levelの正しいitem-name対応が
prospectiveに確認された、と記述できる。一方、人間が解釈する絵文字の意味、意味因果、global
geometryの一様な優位、tokenizer非依存性、behavioral relevance、model一般性とは呼ばない。

## 現在のT10 model横断再現結果

T10では、T9のpopulationとtransportを、事前に固定した9つのmodel/tokenizer cellで保った。全モデルが、
全項目成分と3 viewのtoken数を完全一致させた成分の統計的IUTを通過した。4つのcore p値はすべて
`0.00005`で、`m = 4`、`r = 3`のBonferroni部分連言p値は`0.0001`となった。

それでも登録済みの一次判定は負だった。両成分で`0.02`の実用下限を満たしたのは、Llama 3.2 3B baseと
Qwen 2.5 7B baseだけである。OLMo 2 1B baseとGemma 2 2B ITは通過せず、必要な`3/4`に対して
実用通過数は`2/4`だった。9セルのHolm familyでは、Llama 3.2 3B base、Qwen 2.5 7B base、
Mistral 7B Instruct v0.3が範囲限定セル判定を通過した。

Token数完全一致層にはtokenizerごとに281〜287項目が残り、contrastは消えなかった。これによりtoken長に
関する一つの説明は狭まるが、tokenization非依存性は確立しない。Raw-block endpoint、Qwen 4点profile、
関連Mistral-Instruct結果は記述に限る。論文では
`cross_model_replication_not_established_under_frozen_rule`を維持し、scale、tuning、意味、因果、
独立再現、model一般性を推定しない。

## 完了したT11探索拡張

T10-DはT10の負の一次判定を保ったまま、72 cellすべての正の連続margin、疎らなmodel横断item coverage、modelごとに異なるcarrier-distance profile、弱いcodepoint geometry、model依存のraw-to-final変化を示した。独立再構築では、333 shard、36 activation array、84,096 scalarを不一致ゼロで照合した。これはT11の動機にはなるが、都合のよいT10 cellを選ぶ根拠にはしない。

T11は、最初のmodel forwardより前に9-cellのglyph-system decomposition atlasを凍結し、その後、取得対象843件、477 shard、73,566 forward、982,512本のFP32 readoutをすべて取得した。別に割り当てたreserve 268件へのmodel forwardは、T11完了時点ではゼロだった。Target token長を完全一致させるwrong-label control、2 carrier×4距離の完全grid、raw last blockとreturned finalの2 endpoint、192件の正規化depth subsetを固定したまま使った。

Target token長を完全一致させる必須対照は、全systemで通過した。Returned-finalのglyph/name marginは、presentation、modifier、ZWJ、regionalの72 cellすべてで正、keycapでは65 / 72 cellで正だった。最も狭く明瞭なdecomposition候補は、ZWJの`presentation_or_fusion`である。65 / 72 cellが正で、記述区間が厳密に負のcellはなく、9 model中8 modelでcontext中央値が正だった。Regional flagでは、whole-nameとcomponentの双方に追従する第二のpatternが見えた。Modifierとkeycapのdecompositionは、範囲の限られたmixed/null結果である。

ただし、atlasはmodel依存だった。Model間のitem順位一致は弱く、一部systemではfirst-token一致層のcoverageが疎らで、size順のQwen profileも狭義単調増加は36本中8本だった。T10の救済、意味、機構、因果、scale、tuning、tokenizer非依存性、model一般性は主張しない。

## 完了したT12 one-shot reserve confirmation

T12では、reserveへの最初のforwardより前に、model family、returned-final endpoint、実用床、context rule、exact-lengthとstrict-prefix control、heterogeneity gate、2仮説のHolm familyを別途凍結した。その後、ZWJ reserve 96件とregional flag reserve 64件を9 role・8 contextですべて取得した。90 shard、9,792 forward、FP32 vector 39,168本である。

登録した仮説はどちらも確認されなかった。`H_ZWJ_FUSION`は統計量`0.000369`、未補正`p = 0.05496`、Holm `p = 0.10992`。Regional presentation/fusionは弱く正方向だった（`0.002767`、component単独`p = 0.03538`）が、regional component trackingは`0.000666`、`p = 0.12950`であり、必要なintersection-union/Holm判定も`p = 0.12950`だった。3 componentとも、実用床に達したmodel summaryは9件中0件だった。

論文では、T12を、T11の強い探索patternが減衰したprospective negative confirmationとして扱う。これは未使用reserve、実用床、model heterogeneity gateの価値を示す証拠であって、modelに絵文字表現がないという証拠ではない。Analyzerをimportしないvalidatorが432 cell中央値、49,999回検定3件、全判定gateを再計算し、不一致は0件だった。

## 完了したT13-EA探索的点推定

T13-EHでは、9 roleのsource bankと、3つのpilot modelの383,232行の介入応答を、露出済みの
source itemと公開targetに限って収集した。続くT13-EAでは、登録済みF1〜F6の点推定を完了した。
v0のexact-JS gateは、非ゼロの科学値を開く前にfail-closedした手続き上の負の結果として保存している。
別に凍結したv1 amendmentが通過したのは、primitiveの厳密なno-opと、上限を固定したfloat32 JS
round-trip residualの検査だけである。厳密なJSのゼロも、科学的結果も意味しない。

点推定が次に促すのは、絵文字に固有のsteeringという結論ではない。構造化されたsource directionが、
ターゲット固有の変化しやすさやnull directionへの依存を超えて介入応答を説明するか、というより狭い問いである。
F1〜F5は3つのpilot model、F6のsource geometryは9 roleすべてを対象とする。厳密なtoken・prefix対照、wrapper holdout、
正負のmanifold/covariance-matched null、残る6 modelでの介入応答の再現、generation endpointは未実施である。
登録済みcluster bootstrapも0 / 20,000回のままである。したがって、T13-EAに一次の有意性判定や確認判定はない。
[T13-EA結果](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md)、
[zero-gate amendment](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md)、
[compact evidence](../artifacts/emoji_steering_specificity_analysis_v0/README.ja.md)に詳細を示す。

## 研究質問

1. **RQ1 — 測定の忠実性:** 要求したRMS介入は実測値と一致し、ゼロ介入は真に無作用か。
2. **RQ2 — 指紋の再現性:** 同じグリフから別々に推定した方向は、未使用ターゲットでも似た出力差分を生むか。
3. **RQ3 — 対照との差:** その再現性は、同じノルムのランダム方向、一般絵文字方向、ラベル置換より高いか。
4. **RQ4 — 条件依存性:** 効果はレイヤー、強度、ソース方向、ターゲット群、指定済みのトークン数・接頭構造matched controlsでどう変わるか。
5. **RQ5 — 因果性:** 候補コンポーネントのアブレーションと復元で、指紋を選択的に消し、戻せるか。
6. **RQ6 — 独立再現:** どの結果が、実行backend、tokenizer、model familyをまたいで再現するか。
7. **RQ7 — 共有token間のtransfer:** トークン同型な探索panelで、matched-slot反復は中間token familyをまたいでどの程度移り、family内の残差的な上乗せはどの程度か。
8. **RQ8 — Matched-slot geometry:** 固定した5 family格子で、matched-slot activation geometryはatomic-token cellと、厳密に同じ末尾slot tokenを共有するcellの両方に再現するか。
9. **RQ9 — Common-suffix carryover:** 生の絵文字から厳密に1 token後ろの共通tokenにも、matched-slot geometryは観測できるか。
10. **RQ10 — Carrier-distance attenuation:** 共通tokenを反復する固定carrierの距離1、2、4、8で、距離1のrecurrenceと、事前指定した正のlog-distance減衰contrastは両立するか。
11. **RQ11 — Dense CUDA replication:** 固定したcarrier-distance conjunction全体は、選択した4つのdense instruction-tuned Transformers/CUDA cellでも成立するか。
12. **RQ12 — Mistral reserve confirmation:** 固定したlayer 31のglyph/name-versus-codepoint retrieval contrastは、決定論的に選定した未使用Mistral reserveの全carrier-distance cellで再現するか。
13. **RQ13 — Cross-model practical replication:** 同じreturned-final-state retrieval contrastは、token数を完全一致させた後も、固定した4 core model/tokenizer cell中3つ以上で統計条件と実用条件の両方を満たすか。
14. **RQ14 — Glyph-system decomposition:** 固定したmulti-codepoint glyph systemで、matched-label marginはwhole-sequence name、決定論的component label、decomposed formのどれに追従し、9 cellはどの正規化depthまたはfinal-norm境界で分岐するか。
15. **RQ15 — Reserve confirmation:** T11で固定したZWJ fusion候補とregional dual候補は、未使用reserve subset全体で、事前指定した統計量と実用的な大きさを再現するか。
16. **RQ16 — Source structureとgeneric susceptibility:** 構造化されたemoji source directionは、厳密なtoken・prefix対照とwrapper holdoutの後にも、baseline target susceptibilityと正負のmanifold/covariance-matched nullを超えて介入応答を予測するか。

Milestone 2はRQ4にmixedな答えを与えたが、推論上の留保が残る。T2はRQ6の狭い一部に
負・mixedな観測結果を与えたが、独立backendとclaim-matched replicationは未完了である。
RQ5も残っている。これらが未成立なら、論文の中心命題はRQ1〜RQ4に限定する。RQ7に対するE1の答えは
探索的・記述的なside resultとして扱い、確認命題や因果命題へ格上げしない。
T3はRQ8に分岐した答えを与えた。OLMoは棄却し、Gemmaは棄却しなかった。
ただし、token構造とその他のmodel-cell差が交絡しているため、この問いは観測的なままである。
T4も固定した2接尾文脈でRQ9に同じ分岐を与えた。現在tokenだけの説明は退くが、短距離の
prefix伝播は退かない。
T5はRQ10の固定したmodel-level conjunctionに負の答えを与えた。Holm補正後に両成分を
通過したmodelはない。LlamaとOLMoの距離1成分は置換下限のraw p値だったが、減衰成分は
棄却しなかった。
距離8とdistance × depthのpatternは、持続時間や特定layerの救済命題ではなく、副次記述に
とどめる。
T6もRQ11へ同じtop-levelの負回答を与えた。4 modelのIUTはHolm補正後に1つも通過しない。
Mistralでは距離1成分が再現したが、減衰成分を棄却しなかった。T6がprospectiveなのは未観測
だったT6自身のoutcomeに対してだけであり、T5の独立確認ではない。
T8/T9は、固定した判定規則の下でRQ12へ正の答えを与えた。Reserve 292件は一度だけ取得され、全
carrier-distance contrastが実用下限を超え、globalな最小統計はpermutation下限へ到達した。
これは単一model・layer内の未使用target再現であり、独立したmodel-family再現ではない。
T10は、固定した統合規則の下でRQ13へ負の答えを与えた。部分連言検定は統計的に通過し、matching後も差は
消えなかったが、実用下限を通過したcore cellは4つ中2つだけだった。これは固定rosterにおけるmixed evidenceであり、
独立再現、scale、tuning、意味、因果、model一般性ではない。
T11はRQ14に探索的・非確認的な答えを与えた。単一のlanding patternは支配せず、ZWJ fusionが最も狭い候補、regional flagが第二のdual pattern、その他のsystemはmixedまたはbounded nullだった。T12は、凍結したcombined ruleの下でRQ15へ負の答えを与えた。両候補とも確認されず、どのcomponentも実用床に達したmodel summaryはなかった。これはT10を変更せず、semantic nullにも読み替えない。
T13-EAがRQ16に与えるのは、点推定に基づく探索的な分解だけである。構造化sourceとgeneric susceptibilityを分ける必要は見えたが、matched control、正負のnull、残るmodelでの介入応答の再現、generation endpoint、登録済みbootstrapを、新しいfreezeの下で完了するまでは判定できない。

## 予定する貢献

- 内部介入と表層観測を混同しない、能力認識型の実験ハーネス
- モデル、リビジョン、dtype、介入点を固定した MLX–Transformers パリティゲート
- ゼロ介入、ランダム直交方向、符号反転、用量反応、ラベル置換を統合した前因果的スクリーニング
- シードを独立標本として数えず、ターゲットをクラスタとして扱う推論設計
- 正セルと非正セルを同時に報告する、主張境界付きの公開アーティファクト

「絵文字の意味を発見した」は貢献に含めません。

## 論文構成

### 1. Abstract

- 問題: 内部方向の解釈は、再現性とスカラー統制より先に語られがち
- 方法: 固定グリフパネル、ターゲット、ランダム対照、バックエンドパリティ
- 結果: 確認実験で事前指定した主要評価量のみ記載
- 限界: 条件依存性、トークン化、標本単位、因果性
- 結論: 成立した最小限の命題だけを一文で述べる

### 2. Introduction

- 絵文字・グリフを、小さく制御しやすい介入パネルとして使う理由
- 「意味の解釈」より「再現可能な差の有無」を先に問う理由
- 前因果的地図と因果説明の区別
- 研究質問と貢献

### 3. Related Work

- activation steering / representation engineering
- mechanistic interpretability と activation/path patching
- 方向安定性、表現幾何、出力指紋
- トークン化交絡と多言語・記号表現
- Apple silicon / MLX での再現可能な推論

先行研究は、英語原稿の着手時に改めて検索し、一次資料を中心に引用します。

### 4. Methods

- 5色 × 2形状のグリフパネル
- ソースラッパーと方向推定
- 探索段階の24ターゲットと、確認段階の凍結済み48 P2ターゲット。どちらも6群のクラスタ構造
- レイヤー 2 / 4 / 7 / 9 と3段階のRMS強度
- `resid_post` への加算介入
- CountSketchによる出力差分指紋
- ランダム方向、ゼロ、一般絵文字、符号反転、用量、ラベル置換
- 確認段階のトークン数・パネル接頭構造matched controls。Iso-KLは未実施
- 凍結済み主要評価量、target-cluster再標本化、Holm補正、prototype依存感度
- E1のtoken-isomorphic panel、全family-pair transfer、replicate内でのLOTO prototype再構築。確認仮説familyとは分離する

### 5. Backend Validation

- GPT-2リビジョンとFP32を固定
- 4種類のプロンプト長 × 4レイヤー
- トークン、基準ロジット、活性化、ゼロ・非ゼロ介入の一致条件
- 80 / 80検査結果
- エンドツーエンド速度: 17.517 ms 対 10.727 ms、1.633倍（記録時の環境・負荷条件）
- Matched-null Aのforeground processが、高負荷下で798行の時点に外部中断され、その後、重複・欠損・error・非ゼロのzero-hook RMSなしでsealを保った正確なresumeを完了したという実行時の来歴。この負荷事象を、モデルに関する証拠や一般化できる速度結果として扱わない
- この検証を別モデルや別フック点へ一般化しないこと

### 6. Results

結果は、次の順に並べます。

1. 介入量とゼロフックの忠実性
2. ソース方向の反復安定性
3. 指紋優位量の全分布
4. シード横断の再現性
5. レイヤー・強度・ターゲット群別の不均一性
6. 用量反応と符号反転
7. トークン数・接頭構造matched controlsと感度分析
8. 因果実験を行った場合は、アブレーションと復元
9. E1の全family-pair transfer行列、family固有の小さな超過、全family区間、random-controlの不均一性、成立しなかったlayer 4 negative comparator
10. T2の2つのprimary midpointと固定深度全10行。非primaryの記述的p値を確認判定と分ける
11. T3の2つのall-depth primaryと固定深度全10行。Gemmaのatomic-token条件と
    OLMoの共有末尾token条件を分け、深度別p値は副次記述とする
12. T4の2つのall-context/all-depth primary、2つの文脈summary、全20文脈×深度row。
    1 token後ろへの位置移動と、残るprefix説明を明示する
13. T5の3つのmodel-level IUTと、全120 carrier × distance × depth row。距離1、
    減衰、IUT、Holmの主判定を、副次的なtail値とdepth interactionから分ける
14. T13-EAのF1〜F6点推定を別枠の探索結果として示す。v0 zero gateのfail-closed履歴、
    v1数値amendment、3 pilotと9 source roleの範囲の違い、20,000回bootstrapの未実行を明記する

最大セルは主結果にしません。25 / 36の正セルと11 / 36の非正セルを同じ図に載せます。

Milestone 2では、探索96次元のpaired median difference `+0.047427`を記述値として示し、48 / 32 / 24次元の`+0.040200 / +0.028907 / +0.048591`は同一seedの代数的foldであってseed感度ではないと明記する。「何%を説明したか」は報告しない。

確認表には、layer 2の頑健判定とlayer 4の未解決判定を、主要ソースと独立ソースの両方について並べる。V1のCLI順序によるrole bindingと別監査、固定prototype bootstrapと事後prototype再構築感度を分けて示す。Panel Cの`🟥`、完了した末尾token診断と接頭構造均一化診断も、事後的・記述的な境界とともに省略せず示す。

E1は探索side resultとして別枠に置く。Milestone 2のstatusや因果候補を
強める根拠には使わない。

### 7. Discussion

- 再現可能な出力指紋候補が何を示し、何を示さないか
- 集約効果とセル間不均一性の両立
- トークン化、プロンプト分布、モデル固有性の可能性
- 因果実験の成否に応じた解釈
- グリフを使った制御パネルの利点と限界
- E1で見えた広いfamily間transferと小さなfamily固有超過を、共有token構造で説明できる範囲
- T2のmodel family、scale、precision、tokenizer、node交絡と、midpoint
  non-recurrenceから言える範囲
- T3のOLMo recurrenceが厳密な共有末尾token構成に沿い、深度とともに弱まること。
  2 cellの分岐からtoken因果性やscale、precision、architecture、backend、node効果は同定しない
- T4では現在tokenを共通接尾へ移してもOLMoだけが再現すること。説明をcontextual
  carryoverへ狭めるが、そのmechanism、持続距離、意味内容は同定しない
- T5では固定したrecurrence-plus-attenuation conjunctionを通過したmodelがなかったこと。
  LlamaとOLMoの距離8は記述的に高く、初期の取得層は後段より強く低下するが、どちらにも
  推論判定はなく、持続時間、単調性、永続性、選択layerの主張には使わない
- T13-EAで見えた構造化source directionとgeneric target susceptibilityの分岐、positive-only random nullの限界、
  wrapper依存、深度`0.875`の相対peakと最終深度の大きなgeneric responseの区別

### 8. Limitations

- GPT-2の単一リビジョンから始めたこと
- 標準実験をMLXだけで完走したこと
- シードは反復推定で、独立観測ではないこと
- ターゲットが設計された24件で、自然分布の無作為標本ではないこと
- 中立グリフとのトークン長差
- Milestone 2のmatched panelはtoken identityではなく、token countとパネル単位のprefix構造を揃えた対照であること
- E1ではfamily identityと中間GPT-2 tokenが完全に交絡し、第1・第3 tokenを共有しているため、意味上またはtokenizer非依存のfamily表現を同定できないこと
- T3ではmodel family、size、precision、tokenizer、nodeが同時に変わり、OLMoの共有
  末尾tokenを原因として同定できないこと
- T4の2接尾文脈は独立追試ではなく、1 tokenより先のcarryover距離を示さないこと
- T5の主判定は負であり、距離8のtail値とdistance × depth interactionは多重性判定のない
  副次結果であること。LlamaのMLX Stage-A parityも未資格であること
- T6でも固定conjunctionを通過したdense CUDA modelはないこと。Post-T5 roster、
  instruction tuning、tokenizer差、Gemma 3の1 pairだけという設計から、確認、同等性、
  scale効果を推定しないこと
- C1 v1の完全な1レコードが、実験に使われないまま研究agentの文脈へ露出したこと。Bankは廃止済みで、将来の因果実験には新しいversionのbankが必要であること
- v1 analyzerがCLI順序でroleを割り当て、別のinput-binding auditで凍結済み入力との対応を補ったこと
- v1 bootstrapがprototypeをreplicate内で再構築せず、依存対応感度分析が事後的であること
- 置換p値の有限下限と多重性
- 生台帳を公開Gitリポジトリから省略すること
- 未実施のフック点、SAE、生成、パス因果

### 9. Reproducibility and Artifact Availability

- コード、固定設定、入力、依存バージョン
- バックエンドパリティレシート
- 標準実験レシートとアーティファクト整合性監査
- 公開集約データとハッシュ付きマニフェスト
- E1のtokenizer preflight、全記述解析、5つの軽量run bundle、root manifest
- T2のGemma・OLMo activation array、observation、receipt、全10行joint analysis、
  転送検証、public manifest
- T3のGemma・OLMo activation array、observation、receipt、repair後の全10行
  joint analysis、3地点の転送検証、public manifest、および結果を見る前のrepair chain
- T4のGemma・OLMo activation array、observation、receipt、全20行joint analysis、
  3地点の転送検証、public manifest
- T5のGemma・Llama・OLMo activation array、observation、receipt、全120行joint
  analysis、検証済み転送receipt、public manifest
- T6の4 model activation array、observation、receipt、全160行joint analysis、
  lifecycle・開始gate証拠、検証済み返送receipt、public manifest
- T8/T9のdiscovery・reserve evidenceと、それに続くT10の9つのcompact prediction、全cell
  metrics、run/summary/session receipt、shard ledgerへのbinding、独立再計算、checksum付きの
  外部raw activation archive 1,212,819,072 bytes
- T11の凍結input、9つの検証済み取得summary、joint analysis、item margin・model間一致・depth trajectoryの独立再計算、compact public bundle、および省略したdense arrayをhashで結ぶ外部archive
- 省略した約74 MiB（77.3 MB）の生台帳・NPZを再生成する手順
- 英語・日本語の対文書

## 予定する図表

1. **Figure 1:** 実験フローと主張レベル
2. **Figure 2:** グリフパネル、方向推定、ターゲット介入
3. **Figure 3:** 36セルすべての指紋優位量
4. **Figure 4:** シード横断再現性とランダム方向対照
5. **Figure 5:** 用量反応、符号反転、iso-KL感度分析
6. **Figure 6:** 因果実験が成立した場合のアブレーション・復元
7. **Table 1:** 固定設定とバックエンドパリティ
8. **Table 2:** 主要評価量、区間、正・非正セル
9. **Table 3:** 追試モデルと成立・不成立範囲
10. **Figure / Supplement:** E1のlayer別5 × 5 transfer行列。確認結果とは明確に分ける
11. **Figure / Supplement:** T2のGemma・OLMo固定深度shape-axis profile。Midpointだけを
    primaryとして示し、非primaryの記述的p値を分ける
12. **Figure / Supplement:** T3のall-depth主結果と全深度profile。Gemmaのatomic-token条件と
    OLMoの共有末尾token条件を分けて示す
13. **Figure / Supplement:** T4のcommon-suffix主結果と2つの文脈×深度profile。現在tokenを
    共通化した点と、prefix構造が残る点を並べる
14. **Figure / Supplement:** T5のmodel-level IUT成分とdistance × depth profile。唯一の
    主判定と、距離8のtail・depth interactionという副次記述を分ける
15. **Figure / Supplement:** T10の9セルにおける全項目・token数一致の最小差。統計的な
    部分連言通過と、実用core count失敗を分け、Qwen ladderとraw-block endpointは副次として示す
16. **Figure / Supplement:** T11のsystem×view matched margin、decomposition contrast、retrieval breadth、正規化depth trajectory、raw-to-final変化、model間heterogeneityを探索結果として示し、将来のT12 reserve結果とは分ける

Milestone 2の主表には、主要ソースlayer 2（+0.208363、[0.137463, 0.276893]、Holm p = 0.00143999）とlayer 4（-0.0329465、[-0.0761085, 0.0110094]、未解決）、独立ソースlayer 2（+0.187507、[0.125489, 0.247659]、p = 0.00393996）とlayer 4（-0.086379、[-0.159246, -0.016917]、未解決）をすべて載せる。

## 主張の語彙

### 現段階で使用できる

- reproducible fingerprint candidate
- aggregate separation from random-direction controls
- pre-causal activation screening
- condition-dependent / heterogeneous effect
- robust to the prespecified token-count and token-prefix matched controls at layer 2 under frozen v1
- exploratory matched-slot recurrence under a fixed middle-token family substitution
- no dual-model recurrence for the frozen T2 midpoint shape-axis endpoint
- OLMo-only token-structured recurrence for the frozen T3 all-depth endpoint
- OLMo-only common-suffix carryover for the frozen T4 all-context/all-depth endpoint
- no model-level carrier-distance attenuation for the frozen T5 recurrence-plus-attenuation endpoint
- cross-model replication not established under the frozen T10 statistical-plus-practical rule
- bounded T10 model/tokenizer-cell alignment for Llama 3.2 3B base, Qwen 2.5 7B base, and Mistral 7B Instruct v0.3
- completed exploratory T11 glyph-system decomposition atlas
- completed T12 one-shot negative confirmation for the ZWJ and regional candidates
- completed T13-EA exploratory point analysis without a primary or confirmatory verdict

### 追加の証拠なしには使用しない

- semantic representation
- concept encoded by the glyph
- circuit for color or shape
- causal path
- universal or model-independent effect
- semantic emoji family, tokenizer-independent E1 effect, layer-specific E1 effect
- T2 scale effect, quantization effect, or absence of colored-shape geometry
- T3 tokenizer causality, semantic matched-slot variable, scale effect, precision effect, or node effect
- T4 semantics, causal mechanism, independent replication, or carryover beyond one token
- T5 monotonic decay, disappearance, duration, persistence, selected-layer effect, semantics, or mechanism
- T10 tokenizer independence, scale law, instruction-tuning effect, independent replication, or model generality
- T11 compositional meaning, lexicalized meaning, mechanism, tokenizer independence, or scale law
- T12 semantic null, endpoint-rescued confirmation, behavioral steering, or model generality
- T13-EA unique emoji specificity, semantic steering, scale law, or model generality

## 残る論文ゲート

- C1 v1の露出文脈の外で新しいversionの因果bankを用意し、それを開く前にlayer 2を対象とする完全な因果プロトコルを凍結する。プロトコル設計の着手だけを目的とした追加bankは求めない。
- 論文での最終的な確認表現と、それを支える再現実験では、v1のrole bindingとprototype再標本化依存に事前に対処する。
- 正負を問わず、事前指定した因果実験を少なくとも1件完了する。新しいbankを早く開かない。
- 独立backendの実装確認と、最終主張に見合う別modelまたはtokenizerでの再現を完了する。
- 完全なraw evidenceをarchiveし、checksumを付ける。
- 論文の表と図をversion管理したscriptから生成する。
- 先入観のない再現性・主張境界レビューを行う。
- 英語原稿と日本語公開概要の命題を一致させる。
- E1の記述区間にp値、確認status、layer比較の推論を後付けしない。
- T2の判定は2つのmidpointとHolm familyに限定し、Gemmaの非primary `1/120`行を
  発見や新しいprimaryへ格上げしない。
- T3の判定は2つのall-depth p値とHolm familyに限定し、10個の深度別p値を
  確認判定、新しいprimary、またはcellの救済に使わない。
- T4の判定は2つのall-context/all-depth p値とHolm familyに限定する。文脈別と全20
  文脈×深度値は副次結果で、T3は推論へ統合しない記述参照とする。
- T4の2接尾文脈を独立再現として数えない。
- 完了したT5の境界を保ち、失敗した主減衰conjunctionや副次profileから、持続時間、
  単調減衰、消失、特定distance・depthの効果を推定しない。
- 完了したT10の境界を保つ。実用下限を下げず、core cellを入れ替えず、extension cellを昇格させず、
  QwenとMistralの副次profileをscale、tuning、独立再現へ読み替えない。
- T11を探索的・model-conditionedな結果として保つ。都合のよいcellだけを選ばず、token長一致をtokenizer非依存性と言い換えない。
- T12を完了した一度限りの負の確認として保つ。実用床を下げず、model rosterを入れ替えず、regional componentの`p = 0.03538`だけを昇格させず、別endpointで救済しない。
- T13-EAの20,000回cluster bootstrapを完了し、点推定から確認判定を後付けしない。
- 厳密なtoken・prefix対照、leave-one-wrapper-out direction、正負のmanifold/covariance-matched null、
  深度`0.875`対`1.0`、残る6 modelの介入応答、generation endpointを、T13-EAの主張を強める前に新しいprotocolへ凍結する。

現段階では、完成原稿を主張しない。英語論文がPhase Iの終点である。

## 執筆開始前のチェック

- 新しいversionのbankを開く前に、layer 2の候補、介入、endpoint、対照、多重性familyを因果プロトコルへ凍結したか
- 主要評価量と多重性管理を事前固定したか
- T5では3つのmodel-level IUTとHolm familyだけを判定として扱い、carrier、distance、
  depth、tail、T4比較を副次結果のまま保ったか
- 実行したトークン数・接頭構造matched controlsと、事後的・記述的な二次診断を正確に区別したか
- 正・非正・失敗セルをすべて表に入れたか
- 論文中の数値が、公開レシートまたは集約アーティファクトへ一意にたどれるか
- 因果語の強さが、アブレーションと復元の結果を超えていないか
- 英語本文と日本語概要の命題が一致しているか
