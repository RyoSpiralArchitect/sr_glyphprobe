# GlyphProbe

[T19 語彙・因果結果](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) · [T19 論文ストーリー](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md) · [T19 凍結protocol](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md) · [T18 未提示表層の語彙対応結果](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md) · [T18 論文ストーリー](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md) · [T18 凍結protocol](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md) · [T17 深度atlas結果](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md) · [T16 論文ストーリー](docs/PAPER_STORY_T16_V0.ja.md) · [T16 運用行動・因果結果](docs/T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.ja.md) · [T16 後期分散band結果](docs/T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.ja.md) · [T16 完全同一UTF混合結果](docs/T16_UTF_IDENTITY_MIXING_V0_RESULTS.ja.md) · [T16-UTF-X1 系列長・並び方ストレステスト](docs/T16_UTF_SCALE_VARIANTS_V1_RESULTS.ja.md)

[English](README.md) · [T15-B prospective再現結果](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md) · [T15-B protocol](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md) · [T15-A 絵文字 × 言葉の結果](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md) · [T15-A protocol](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md) · [T14-X / T14-C結果](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md) · [T13-EA bootstrap実行freeze](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md) · [T13-EH収集protocol](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) · [T12 reserve結果](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [T13の問いの設計図](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) · [T11探索結果](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [T11凍結protocol](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) · [T10診断](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md) · [T10 model横断結果](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [Mistral base深度×距離結果](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) · [Dense CUDA結果](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Carrier-distance結果](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Carrier-distanceプロトコル](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) · [Common-suffix結果](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [Matched-slot結果](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [Multifamily geometry結果](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [Tokenizer census結果](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [E2 MPS transport v2プロトコル](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [holdout状態](docs/HOLDOUT_STATUS.ja.md) · [E2 Stage A3数値screen結果](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [E2 Stage-A v2結果](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [E1 探索結果](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) · [基準実験の結果](docs/RESULTS_V1.ja.md) · [ロードマップ](docs/ROADMAP.ja.md) · [Phase I 論文計画](docs/PAPER_OUTLINE.ja.md)

GlyphProbe は、絵文字やグリフから作った活性化方向が、言語モデルの出力に再現可能な「指紋」を残すかを調べる研究用ハーネスです。

最初から「モデルの中で、この絵文字は何を意味するのか」とは問いません。介入量、クリッピング、ソース文、ターゲット文、ランダム方向を固定したうえで、方向ごとの差が繰り返し観測できるかを先に確かめます。

既定のパネルは、5色 × 2形状の10グリフです。

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

## 現在地

最初の基準実験では、次のcellを検証しました。

- モデル: `openai-community/gpt2`
- リビジョン: `607a30d783dfa663caf39e06633721c8d4cfcd7e`
- 数値形式: FP32
- 介入点: `resid_post`
- 標準レイヤー: 2 / 4 / 7 / 9
- 実行基盤: Apple silicon 上の MLX

MLX は、同じモデル名だから採用したわけではありません。固定した4種類のプロンプト長 × 4レイヤーで Transformers/MPS と比較し、トークン列、基準ロジット、活性化、ゼロ介入、非ゼロ介入を検査しました。80項目すべてが合格し、記録時のエンドツーエンド中央値は 17.517 ms から 10.727 ms に短縮しました（1.633倍）。この検証が認めるのは、上記セルでのバックエンド同等性と、その実行環境・負荷条件での速度差だけです。

続いて MLX で標準スクリーニングを実行し、14,208件の介入レコードをエラーなしで完了しました。前因果的レディネス検査は11 / 11項目、アーティファクト整合性監査は15 / 15項目が合格しています。なお、この全パイプラインを Transformers/MPS でも重ねて実行したわけではありません。主な集約値は次のとおりです。

| 指標 | 値 |
|---|---:|
| ソース方向の反復一致度（中央値） | 0.9705 |
| 絵文字指紋のランダム方向に対する優位量（中央値） | 0.6075 |
| シードをまたぐ指紋優位量（中央値） | 0.9308 |
| KL用量反応の単調性（中央値） | 1.0000 |
| 符号反転の反対称性（中央値） | 0.9997 |
| ゼロ介入による活性化・ロジット変化 | 0.0 |

ただし、36セルのうち優位量が正だったのは25セルで、11セルは非正でした。集約値が正でも、効果が一様に出たわけではありません。現在の結果は、追試に値する**前因果的な指紋候補**です。絵文字の意味、意味表現、回路、因果経路の証明ではありません。

詳しい結果と留保は [実験結果](docs/RESULTS_V1.ja.md)、次の研究段階は [ロードマップ](docs/ROADMAP.ja.md) を参照してください。

### T16の現在地

T16では、再現した応答指紋を、行動・因果・文字列幾何の三方向から分けて検証した。

| 問い | 完了した結果 | 最大限許される読み方 |
|---|---|---|
| 絵文字と語の対応を二択で読めるか | GemmaとMistralの意味選択・整合性判断、計4 gateがすべて通過。正答率は0.754〜0.953 | 固定した二択形式での関連づけと整合性判断 |
| T15-Bの指紋が明示的な不一致判断を因果的に実装するか | Treatment -0.148438、sufficiency -0.085938、necessity -0.054688。Gate不通過 | そのsubspaceを整合性回路とは呼べない |
| 後期の分散bandが媒介するか | Necessity +0.000871は通過。Sufficiency -0.000146は不通過、treatmentは実用下限未達 | 必要成分はあるが、移植条件では十分でない |
| 完全同一UTF反復とfamily混合は分かれるか | `n=1`は厳密に同一。横断−同一family区間は8 / 8 model-depth cellで正 | Tokenizer経路を条件とした探索的な幾何 |
| 長さ・並び方・anchor位置を大幅に広げても残るか | 9 model/tokenizer cell、515,808件。主要集約と`n=500`は36 / 36 cellで正。完全token-multiset order対照ではblockedが72 / 72 cellで最大 | 長系列でも残るtokenizer条件付き幾何。Scale則やtokenizer非依存なUnicode構造ではない |

中心に置くべきなのは、「行動は読み出せるが、その指紋を同じ因果対象とはみなせない」
という分離である。詳しくは[T16論文ストーリー](docs/PAPER_STORY_T16_V0.ja.md)と、
[運用行動・因果結果](docs/T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.ja.md)、
[後期band結果](docs/T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.ja.md)、
[完全同一UTF結果](docs/T16_UTF_IDENTITY_MIXING_V0_RESULTS.ja.md)、
[系列長・並び方ストレステスト](docs/T16_UTF_SCALE_VARIANTS_V1_RESULTS.ja.md)にまとめた。

### T19 語彙の幅とcomponent因果の現在地

T19-Lでは、atomic emoji 55件と非emoji Unicode記号55件を、正式label、正式名と
語が重ならないalias、literal codepointと交差させた。9つの凍結済みmodel/tokenizer
cellすべてで、emojiのalias-minus-codepoint検索差がunrestrictedと4-viewのtoken数
完全一致解析の両方で正だった。Core 4 cellは全件、登録したpartial conjunctionを
通過し（`p = 0.0027`）、9 / 9 cellすべてがmodel IUTと実用下限`0.02`を満たした。
記号のalias効果は小さく不均一だった。Emoji-minus-symbol点推定は9 / 9 cellで正だったが、
この比較は登録済み二次結果である。

条件付きで実施したT19-Cでは、128件のsource emojiからrank 8のglyph–alias subspaceを
学習し、Llama 3.2 3Bの未使用emoji 192件で検定した。6部位すべてでzero-hookとrestorationは
厳密に一致したが、一次のblock 24 `attn_out`と`mlp_out`は、どちらもnecessityと
sufficiencyのintersectionを通過しなかった。したがって、支持できるのはtoken数を揃えた
CLDR語彙対応までであり、登録した単純な後期component mediatorは棄却された。描画知覚、
同義語理解、普遍manifold、完全な回路は示していない。詳しくは[全結果](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md)、
[論文ストーリー](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md)、
[凍結protocol](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md)に示す。

### T18 未提示の複合glyphに対する語彙対応確認

T18では、raw Unicode列がliteralな`U+...`列より英語のEmoji短名をよく検索するかを、
研究内で未提示だった複合絵文字192件でprospectiveに調べた。Population、9つの
model/tokenizer cell、後期window、token数一致層、多重性rule、実用下限は、結果を
開く前にpushしている。

54 shard、13,824 forward、497,664 readoutを完走した。登録済みの「core 4 cell中3以上」
というpartial conjunctionは`p = 0.0001`で通過。実際にはcore 4 cellすべてが、
unrestrictedとtoken数完全一致の両方で統計条件と実用下限`0.02`を満たした。9 cell全体では
8 cellが同じruleを通過した。日本語matched差は二次結果として9 / 9で正だった。一方、
matched CKAが正だったのは3 / 9で、4 coreすべてで正のitemは192件中8件だけだった。

したがって、許される読み方は「未提示表層に対するitem-specificな語彙結合が、modelごとに
異なる実装で集約的に再現した」までである。事前学習holdout、描画glyphの知覚、意味理解、
共通mechanism、scale lawではない。詳しくは[全結果](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md)、
[論文ストーリー](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md)、
[凍結protocol](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md)に示す。

### T17 glyph–name深度atlasの現在地

T17ではraw emoji surfaceへ戻り、292項目それぞれをUnicode正式名とliteral codepoint識別子に
対応づけ、9つのexact model/tokenizer cell、9つの正規化深度で追跡した。2 carrier ×
4 distanceを等しくまとめたname-minus-codepoint top-1点推定は、`0.375`以降9 / 9モデルで正だった。
Token数を完全一致させた層でも、`0.25`以降は9 / 9で正である。

ただし、全model共通の後期転換ではなかった。2モデルは最初のblock、1モデルは`0.125`、
1モデルは`0.75`、5モデルは`0.875`でpeakになった。最終状態のpaired item marginは9 / 9で
nameを支持した一方、空間全体を見るcentered linear CKAは4 / 9だけが同方向だった。
したがって守れる貢献は、**item固有の語彙対応は広く収束するが、その立ち上がりはmodel固有で、
globalな意味manifoldの整列は必要としない**、である。項目はT9/T10ですでに開いているため、
このatlasは探索的である。詳しくは[全結果](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md)と
[論文ストーリー候補](docs/PAPER_STORY_T17_GLYPH_NAME_V0.ja.md)に示す。

### Milestone 2 の現在地

事前検査を通過した後、凍結済み48件のP2バンクを一度だけ開いた。v1の結果は、レイヤーによって分かれている。

| ソースラッパー | レイヤー | 調整済み効果 | 95% CI | Holm補正済みp値 | v1判定 |
|---|---:|---:|:---:|---:|---|
| 主要ソース | 2 | +0.208363 | [0.137463, 0.276893] | 0.00143999 | 指定済みmatched controlsに対して頑健 |
| 主要ソース | 4 | -0.0329465 | [-0.0761085, 0.0110094] | 0.999500 | 未解決 |
| 独立ソース | 2 | +0.187507 | [0.125489, 0.247659] | 0.00393996 | 指定済みmatched controlsに対して頑健 |
| 独立ソース | 4 | -0.086379 | [-0.159246, -0.016917] | 0.999430 | 未解決 |

3つの対照パネルで揃えたのは、3トークンという長さと、パネル単位の9対1の接頭構造である。token IDそのものは同じではない。Panel Cには、事前申告した意味的に近い対照`🟥`を1個含む。独立ソース条件は同じP2ターゲットを再利用しており、独立ターゲットや別モデルでの再現ではない。

別に行ったinput-binding auditは合格した。一方、target bootstrapの各replicateでleave-one-group-out prototypeを作り直す事後感度分析では、区間が広がった。この事後解析は、凍結済みv1判定を上書きしない。その後、2つの二次診断はいずれも14,208行のgridを完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、末尾token一致で+0.751225、接頭構造均一化で+0.601038である。これはpaired診断で使うraw separation scoreとは別の評価量である。96次元における記述的なstandard-minus-diagnostic中央値は、末尾token一致が+0.002624（36セル中20セルが正）、接頭構造均一化が+0.022096（36セル中25セルが正）だった。これらの事後診断は、推論や同等性の検定ではない。C1 v1はこれらの実験には使わなかったが、別に記録した研究文脈への露出により、現在は廃止している。詳細は[holdout状態](docs/HOLDOUT_STATUS.ja.md)に示す。

実行時の来歴として、matched-null Aの最初のprocessは、マシン負荷が極端に高い最中、798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで14,208行の正確なgridを完了した。この事象は、モデルに関する証拠でも、一般化できる速度の主張でもない。

正確な結果、解析上の留保、感度区間、エビデンスへのリンクは [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) にまとめた。この結果は前因果段階にあり、意味、機構、回路、因果経路、トークン化から独立したglyph効果を確立しない。

### E1探索の現在地

トークン同型な5つの絵文字familyを調べるE1は完了した。Family pair 25組の
平均transfer値は広く正で、layer 2では0.395455〜0.484915、layer 4では
0.602564〜0.681909だった。一方、family内で上乗せされたglobalな超過量は
小さかった。

| 指標 | Layer 2（primary exploratory） | Layer 4（事前指定したnegative comparator） |
|---|---:|---:|
| Family等重みのglobal specificity | 0.014752595564、95%記述区間[0.002875238085, 0.027439243404] | 0.014887989201、[0.003407563347, 0.019684351979] |
| 0を含むfamily別区間 | 5 / 5 | 5 / 5 |
| 平均transfer値25件の範囲 | 0.395455〜0.484915 | 0.602564〜0.681909 |

この結果は、意図的に共通化したGPT-2の第1・第3 tokenによるtransferが
支配的で、family固有の上乗せは小さいことを示唆する。意味上のfamily、
tokenizer非依存性、layer固有性、因果性の証拠ではない。Random controlとの
比較も不均一で、family × layer × seedの30 cell中10 cellが非正だった。
内訳はlayer 2のseed 307で5 familyすべて、layer 4のseed 101で5 family
すべてである。全8,880介入行はerror 0で完了し、zero-hookの
activation/logit RMSは正確に0だった。

E1が使ったのは、すでに探索済みのprestage target 24件だけである。P2とC1は
使っておらず、Milestone 2の判定もPhase Iの論文gateも更新しない。全結果は
[E1探索結果](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md)、設計は
[凍結済みプロトコル](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md)、公開物は
[E1 evidence bundle](artifacts/emoji_family_exploratory_v1/analysis/report.md)
を参照してほしい。

### Multifamily tokenizer censusの現在地

固定したtokenizer-only censusは、mac1、mac2、furnaceにあった14 roster entryを
すべて完了した。固定文字列115件、context 4種、tokenization 6,440行、pairwise
19,665行で、model forwardとprotected target accessはいずれも0だった。14 artifactは
固定surface上で7つの完全一致output classへまとまり、そのうち5 classはnode間で
完全に再現した。

7 classすべてでraw token数が同じだった文字列は6件だけだった。最大rangeはfamily
ZWJ sequenceの13 tokenである。Blue circleとblue squareのどちらにも、raw、先頭space、
glyph-promptのいずれのcontextにも、全7 classでtoken数と先頭1 tokenを同時に揃える
単一candidateは固定panel内になかった。既存ASCII controlにも、全class共通の
equal-count candidateはなかった。

したがって、次のcontrol panelはtokenizerごとに別々にfreezeする必要がある。この結果は
tokenization交絡を取り除かず、Milestone 2も更新せず、layerも選ばず、tokenizer非依存の
構造も確立しない。詳細は[記述結果](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md)、
[固定プロトコル](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md)、
[検証済みcompact aggregate](artifacts/multifamily_tokenizer_census_v0/aggregate.json)に示す。

### Multifamily colored-shape geometry v0の現在地

公開freezeの後に、role-bound run 2本とjoint exact analysisを完了した。事前指定した
midpointでは、Gemma 2 2B 4-bitが平行性`0.114857969`（raw p = `0.058333333`、
Holm p = `0.116666667`）、OLMo 3 7B BF16が`0.024628040`（raw・Holm p =
`0.275`）だった。どちらも棄却せず、事前登録した結果patternは
`no_dual_model_recurrence`となった。

固定5深度×2 modelの全10行を公開し、Gemmaの非midpoint行に現れた小さな記述的p値を
primaryへ格上げしていない。両runともgeneration、intervention、protected-target accessは
0である。小型bundleにはactivation arrayも収録し、生成元・relay・到着先のhashとjoint
analysis validatorはすべて一致・合格した。完了したのは観測side trackであり、因果、確認、
backend parity、quantization、scale、model一般性の主張ではない。詳細は[全結果](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md)、
[固定プロトコル](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md)、
[公開エビデンス](artifacts/multifamily_colored_shape_geometry_v0/README.ja.md)に示す。

### Multifamily matched-slot geometry v0の現在地

固定した5 family × 10 slotの観測実験を、同じGemma/OLMo roleで完了した。Gemmaの
all-depth slot比率は`0.204304805`、randomization null平均は`0.199984463`、Holm
pは`0.2085`だった。OLMoは`0.500391869`、null平均`0.200184835`、Holm p
`0.0001`だった。事前に定めたpatternは`olmo_only_token_structured_recurrence`である。

これは設計が区別しようとしたtokenizer条件どおりの分岐である。Gemmaは互いに異なる
50個のatomic tokenを使い、OLMoは厳密に
`[shared_prefix, family_token, shared_slot_token]`となる。したがってOLMoの結果には
共有tokenだけで十分な説明が残り、意味上またはtokenizer非依存の再現は示さない。
全結果、最初のserialization failure、結果を見る前に固定したserialization-only repairは、
[結果文書](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md)と
[公開evidence](artifacts/multifamily_matched_slot_geometry_v0/README.ja.md)に残している。

### Multifamily common-suffix carryover v0の現在地

事前に固定したfollow-upでは、生の絵文字から1 token後ろにperiodまたはnewlineを置き、
その共通tokenで読み出した。Gemmaの2文脈×全深度統計は`0.203443011`、null平均は
`0.200044692`、Holm pは`0.30295`だった。OLMoは`0.537464703`、null平均
`0.199977865`、Holm p `0.0001`だった。事前に定めたpatternは
`olmo_only_common_suffix_carryover`である。

OLMoの副次的な文脈別統計はperiod `0.538985382`、newline `0.535944025`と近かった。
したがってshared-slot geometryは、slot tokenそのものを読む位置だけに閉じず、1つ後ろの
共通tokenでも観測できる。ただし、直前のtoken構造が短距離で伝わるだけという説明は
十分に残る。意味、因果、確認、tokenizer非依存のevidenceではない。詳細は[全結果](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md)、
[固定protocol](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md)、[公開evidence](artifacts/multifamily_common_suffix_carryover_v0/README.ja.md)に示す。

### Multifamily carrier-distance v0の現在地

事前固定した観測的な反証実験は完了した。入力全体と現在位置のcarrier token IDを固定し、
`" a"`と`" |"`の反復列の中で、同じ絵文字から1、2、4、8 token後ろの`resid_post`を
読んだ。唯一の主判定では、model-level intersection-union testごとに、距離1の再現と
正の固定log距離減衰contrastの両方を要求した。

Gemmaの距離1成分はnull付近だった。LlamaとOLMoの距離1成分のraw p値は、いずれも
permutation下限`0.00005`だったが、減衰p値はそれぞれ`0.188`と`0.9977`だった。Gemma、Llama、
OLMoのIUT/Holm p値は`1.0`、`0.564`、`1.0`となり、outcomeは
`no_model_distance_attenuation`である。距離8の記述profileはLlamaで`0.369105`、
OLMoで`0.527099`と高いが、tail rowには独立した多重性判定がない。単調な持続、
持続時間の閾値、意味、機構、因果、tokenizer非依存性、cross-modelの大きさ比較は示さない。
LlamaのStage A parity failureも有効なままである。詳細は[全結果](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md)、
[固定protocol](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md)、[公開evidence](artifacts/multifamily_carrier_distance_v0/README.ja.md)に示す。

### Dense CUDA carrier-distance T6の現在地

Post-T5の4 cell BF16 Transformers/CUDA replicationは、
`no_dense_model_distance_attenuation`として完了した。Gemma 2 2B IT、Gemma 3 4B IT、
Gemma 3 12B ITは距離1成分を棄却しなかった。Mistral 7B Instruct v0.3はpermutation下限
`0.00005`で棄却したが、固定した減衰成分のp値は`0.46975`だった。4 modelをまとめた
Holm familyで通過したmodel-level IUTはない。

4本の400-forward runと160 row analysisはすべて検証に合格し、介入、生成、protected-target
callは0だった。開始gateは、炉が空いていることの再確認と、receiver-ownedな自然な
`resource:furnace` Codex `Stop` surfaceで満たした。T5とは統合せず、scale、tokenizer、
backend、意味、因果、確認のclaimも認めない。詳細は[全結果](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md)、
[固定protocol](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md)、[公開evidence](artifacts/multifamily_dense_cuda_carrier_distance_v0/README.ja.md)に示す。

### Mistral 7B base 深度×距離 T7の現在地

T6後にendpointを固定し、それまで未観測だったMistral 7B v0.3 base modelを実行した。
距離1の反復統計は`0.377524026`、固定した初期深度−後期深度の減衰interactionは
`0.149104068`で、片側raw p値はいずれもpermutation下限`0.00005`に達した。
単一のintersection-union testは棄却した。深度0の減衰は`+0.114009450`、後期4深度の
平均は`-0.035094618`だった。

Base modelの20個の深度×距離cellは、既知だったT6 Instruct profileと記述的には近かった
（`r = 0.996785730`）。ただしmodelとendpointはT6を見た後に選んでおり、2 checkpointは
関連している。同等性、instruction tuningの効果、独立確認、意味、因果、Phase I gateの
claimは認めない。詳細は[全結果](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md)、
[固定protocol](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md)、[公開evidence](artifacts/mistral7b_base_depth_distance_v0/README.ja.md)に示す。

### Mistral 7B semantic atlas T8の現在地

T8は大規模な観測atlasとして始まった。最初のbatch-64取得は
固定batch-one equivalenceを0/18で失敗したため、閾値を変えず、同じ892-item gridを
batch size 1でcanonicalに再取得した。28 shard、FP32 vector 192,672本はすべて検証に通り、
独立18-case repeatはbit-exactだった。

未使用discovery 842件で、layer 31の等cell glyph→正式名top-1 retrievalは`0.136580`、
chanceは`0.001188`。Glyph→`U+...`は`0.001188`だった。このcontrastは、共通3-token
prefixを持つ5-token glyph 760件と、glyph/name token数が等しい43件でも残った。このdiscovery
解析は記述的かつ一部post-outcomeだった。その後、reserve forward前にlayer 31のendpointを
一つfreezeし、292件すべてを一度だけ取得した。8 cellのglyph/name minus glyph/codepoint
top-1 contrast最小値は`0.171233`、実用下限は`0.02`、共通permutation p-valueは`0.00005`。
これにより、T8で設定したalignmentに関する狭い問いは、このmodelでprospectiveに確認され、閉じた。ただし
意味因果やmodel一般性ではない。詳細は[確認結果](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md)、
[固定protocol](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md)、[公開evidence](artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/README.ja.md)に示す。

### Semantic atlas T10の現在地

T10は、`cross_model_replication_not_established_under_frozen_rule`という登録済みの負の結果で完了した。9つのexact model/tokenizer cellすべてで、T9と同じ292項目、3 view、2 carrier、4距離、batch size 1を取得した。合計は333 shard、15,768 model forward、FP32 readout 126,144本である。

全モデルセルのIUTは、全項目成分と3 viewのtoken数を完全一致させた成分を比較したうえで統計的に有意だった。4つのcore p値はすべて`0.00005`で、Bonferroni部分連言p値は`0.0001`。しかし、両成分で`0.02`の実用下限を通過したcore cellはLlama 3.2 3B baseとQwen 2.5 7B baseの2つだけで、必要な3つに届かなかった。9セル全体のHolm＋実用条件を通過したのは、この2つとMistral 7B Instruct v0.3である。

実装監査では、T8/T9のendpointの呼び方も修正した。`output.hidden_states[-1]` はrawな最終decoder block出力ではなく、modelが返す最終norm後のhidden stateである。T10では、このAPI endpointを一次として維持し、raw block出力は一次を救済できない副次として同時取得した。Token数完全一致層には281〜287項目が残り、matching後も差は消えなかった。ただし、tokenization非依存性は確立しない。単調なQwen 4点profileと関連Mistral-Instruct cellも記述に限り、scaleやtuning効果を主張しない。詳しくは[全結果](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md)、[固定protocol](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md)、[compact evidence](artifacts/semantic_atlas_cross_model_replication_v0/README.ja.md)に示す。

### T10診断、T11探索、T12確認、T13-EA解析の現在地

T10-DはT10の負の一次判定を変えず、raw activationから導くmetricを再構築した。333 shard、36 array、84,096 scalarを照合し、不一致はゼロだった。連続glyph/name marginは72 model-context cellすべてで正だった一方、item coverageは大きく偏り、carrier-distance profile、codepoint geometry、rawからfinalへの変化はいずれもmodel依存だった。9 modelすべてでtop-1 hitになったitemはない。これは次の設計を鋭くする診断であり、T10の救済ではない。

T11では、凍結した9モデルのdiscovery atlasを完走した。477 shard、73,566 model forward、982,512本のFP32 readoutを取得し、T11完了時点ではreserveへのforwardはゼロだった。Target token長を完全一致させる必須対照は全systemで通過した。Returned-finalのglyph/name marginは、presentation、modifier、ZWJ、regionalの72 cellすべてで正、keycapでは65 / 72 cellで正だった。最も明瞭な狭い候補は、65 / 72 cellで正だったZWJの`presentation_or_fusion` contrastだった。Regional flagでは、whole-nameとcomponentの両方に追従するmixed patternが見えた。一方、model間のitem順位一致は弱く、size順のQwen profileで狭義単調増加したのは36本中8本だけだった。Atomicとpresentationではfirst-token一致層のcoverageも疎らである。したがって、T11は探索atlasであり、意味、因果、tokenizer非依存性、scale、tuning、model一般性の結果ではない。詳しくは[T11結果](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md)、[compact evidence](artifacts/glyph_system_decomposition_v0/README.ja.md)、[凍結protocol](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md)に示す。

T12では、その後、ZWJ 96件とregional flag 64件のreserve subset全体を、同じ9 role・8 contextで別途凍結して一度だけ開いた。全9,792 forwardとreturned-final vector 39,168本が完走した。登録した仮説はどちらも確認されなかった。ZWJは統計量`0.000369`、未補正`p = 0.05496`、Holm `p = 0.10992`。Regional presentation/fusionは弱く正方向だった（`0.002767`、component単独`p = 0.03538`）が、regional component trackingは`0.000666`、`p = 0.12950`で、dual IUT/Holm判定も`p = 0.12950`となった。3 componentとも実用床に届いたmodelは0件だった。Analyzerをimportしないvalidatorが432 cell中央値、49,999回検定3件、全gateを再構築し、不一致は0件である。[T12結果](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md)、[compact evidence](artifacts/glyph_system_reserve_confirmation_v0/README.ja.md)、[T13の設計図](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md)に示す。

T13-EHでは、露出済みのT11 depth population 192項目と公開済みprestage target
32件を対象に、GPU依存の収集を完了した。固定9 roleのsource bankと、事前指定した
base 3 roleの383,232行の応答面は、いずれも欠損なく揃っている。続くT13-EAでは、
登録済みのF1〜F6を点推定まで実行した。v0のexact-JS zero gateは、非ゼロの科学値を開く前に
fail-closedした記録として保存している。別に凍結したv1 amendmentが通過したのは、primitiveの厳密な
no-opと、上限を固定したfloat32 JS round-trip residualの検査だけである。

点推定から次に問うべきなのは、構造化されたsource directionが、ターゲット固有の変化しやすさや
null directionへの依存を超えて介入応答を説明するかである。この結果は、絵文字に固有の意味、
機構、行動、scale、model一般性を確立しない。登録済みcluster bootstrapは0 / 20,000回のままで、
T13-EAに一次仮説、有意性判定、確認判定はない。結果を見た後の実装追補として、600本の高位estimand、
200回×100 chunk、counter方式の抽出列、cross-runtime sentinel、fail-closed mergeまでは凍結した。
本番replicateはまだ実行していない。詳細は[T13-EA結果](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md)、
[bootstrap実行freeze](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md)、
[zero-gate amendment](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md)、
[compact evidence](artifacts/emoji_steering_specificity_analysis_v0/README.ja.md)、
[T13-EH protocol](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md)に示す。

### T14-X拡張とT14-C因果closeout

T14-Xでは、Llama 3.2 3B、OLMo 2 1B、Qwen 2.5の4 sizeについて、depth
0.875と1.0の応答559,488行を完走した。Headlineのstructured-minus-covariance-null
JS区間12本はすべて0を含まなかったが、符号は正9本・負3本だった。Qwenは非単調で、
0.5Bが正、1.5Bがfinal depthで符号反転、3Bが両depthで負、7Bが再び正となった。
Source form、null family、符号による分解も不均一であり、これは普遍的なglyph特権や
scale lawではなく、探索的な応答異方性regimeである。

T14-Cは、そのoutcomeを開く前に凍結した。固定selectorは公開32 target上の候補8部位から、
Llama 3.2 3Bの`mlp_out` block 24を選んだ。その後に新しいC1 v2 bank 192件を物質化し、
一度だけ使った。Zero、restoration、positive control、upstream shamのengineering gateは
すべて通過した。登録済みtreatmentは`0.00172230`で実用床`0.002`未満、necessityは
`-0.00057689`、sufficiencyは`0.00002126`で実用床`0.0005`未満だった。したがってIUTは
非棄却である。この負の結果によって対象を絞った因果paper gateは完了したが、
`confirmatory_claim_authorized: false`は維持する。詳細は[英日結果文書](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md)に示す。

### T15-A 絵文字 × 言葉の不一致interaction

T15-Aでは、OLMo 2 1B、Llama 3.2 3B、Qwen 2.5 3B、Qwen 2.5 7Bの
base model 4種について、steering応答393,472行を完走した。凍結時に一次と定めたdoseでは、
軸内で均衡させたinteraction方向の全語彙応答fingerprintが、構造を揃えた3つのcross-axis
interactionよりも高いcoherenceを示した。Model × depth × signの16 cellすべてで差は正となり、
20,000回のtarget bootstrap区間も全件で0を上回った。

ただし、強さが一様に増えたわけではない。個々のincongruent pairにおけるadditivity残差には
共通の正の超過がなく、JS、total variation、logit RMS、entropy、argmax flip、word / emoji
主効果、source order、depth、doseの各familyも不均一だった。したがって、結果は探索的な
非加算応答の「形」の候補として扱う。絵文字の意味、矛盾検出、行動、因果回路の証拠ではない。
元のanalyzerは反復数を8と16で取り違えてfail closedし、versionを分けたpost-open repairでは
そのassertionだけを修正した。Estimandとbootstrapは変えていない。詳細は[英日結果文書](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md)、
[凍結protocol](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md)、
[compact closeout](validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json)に示す。

### T15-B prospective holdout再現

T15-Bでは、8軸、48件のtarget、2つのmodel roleをすべて入れ替え、各true
interactionを7通りすべてのnon-self cross-axis controlと比較した。凍結したR1は、
target内で2つのdepthと2つのsignをまとめる一方、model間はpoolしない。SmolLM2
1.7B baseのtarget中央値は`+0.020422`、区間は`[0.012887, 0.031510]`だった。
Mistral 7B Instruct v0.3は`+0.060397`、`[0.056621, 0.062194]`だった。両modelの
下限が事前規定した片側Bonferroni条件を満たし、二modelのintersection判定は
`support`となった。

ただし、普遍的なcell効果ではない。一次doseのmodel × depth × signを個別に見ると、
正の区間は8本中6本、mixedは2本だった。A0とA3のsource診断は4 cellすべてmixedで、
energy、主効果、語順、depth、doseも不均一である。したがってT15-Bは、運用上の
response-shape候補を別modelで再現した結果であり、意味、矛盾検出、行動、因果回路の
証拠ではない。詳細は[英日結果文書](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md)、
[凍結protocol](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md)、
[compact closeout](validation/emoji_word_incongruence_replication_v0/t15b_closeout.json)に示す。

### E2 技術検証の結果

固定したLlama 3.2 3B BF16のStage A v2技術検証は、最後まで実行したうえで
`status: validation_failed`、`scientific_result: false`となった。Parity検査の
合格数は33 / 60である。
Tokenizationとbackend内の決定性は10 / 10、厳密なzero-hookは10 / 10が合格した。
一方、baselineは6 / 10、介入後outputは7 / 10、複合的な介入差分は0 / 10、
介入忠実度は0 / 10だった。Activation差分だけを見れば10件すべてが閾値内だったが、
対応するlogit差分が凍結済み閾値を満たさず、複合差分gateは全件不合格となった。

マシンローカルな速度gateも不合格だった。Aggregate median latencyは、
Transformers/MPSが132.127833 ms、MLXが230.138000 msである。MLXは
1.741782892倍の時間を要し、レシートに記録したspeedupは`0.574124367x`だった。
V2で指定したバックエンドの数値挙動に影響する変更、すなわちNumPy export直前の
BF16-to-FP32 castによって検証自体は完走したが、このcellへのMLX採用条件は
満たさなかった。

これは技術経路の不適格判定に限られる。研究用target bank、確認用outcome、因果outcome
にはアクセスせず、E2科学gridも実行していない。絵文字family、意味、因果、modelを
またぐ再現の結果ではなく、論文gateも閉じない。V1のexport失敗記録はそのまま残す。
詳細は [E2の全結果](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md)、
[凍結済みプロトコル](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md)、
[機械可読レシート](validation/mlx_llama32_3b_bf16_parity_v2/receipt.json) にまとめた。
続くStage A3では、同じBF16-weight artifactを使い、runtime compute dtypeだけを
FP16とFP32に分けて検査した。両candidateとも、artifact・parameter identity、
prompt・token identity、決定性、v2から変えていないzero-vector閾値、backend別の
介入忠実度には合格した。不合格だったのは、マシンローカルな速度要件だけである。
FP16のaggregate medianはTransformers/MPSが165.0765625 ms、MLXが322.9998125 ms。
FP32は465.013771 msと458.619459 msだった。FP32のMLXは約1.375%短かったが、
要件の5%には届かなかった。決定論的な判定は
`selection.selected_runtime_dtype: null`、
`selection.decision: no_go_no_eligible_numeric_candidate`である。

Stage A3ではbackend間のfull parityを実行していない。したがって、backend内の
fidelityが高いFP32もqualifiedとは表現できない。Formal v3 validatorとMLX科学gridは、
実行も許可もしていない。V2の不合格判定も変わらない。詳細は
[Stage A3結果](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md)、
[凍結済み数値screenプロトコル](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md)、
[atomic receipt](validation/mlx_llama32_3b_numeric_screen_v1/receipt.json)にまとめた。
研究責任者は、Transformers/MPS専用の科学経路を別に選択した。V1のstatic freezeは、raw tokenizationとwrapper内のcontextual tokenizationをauditが混同したため、model weightの読み込みもforwardも行う前にpreflightで停止した。V1は[科学的outcomeなしで廃止](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md)している。同じ50絵文字primary armと、独立にcenteringする35絵文字token-structure感度armを、修正済みの別versionである[v2プロトコル](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md)へ改めて固定する。MLXのno-goを読み替えず、どちらのMLX閾値も緩和しない。

## インストール

Python 3.11 以降を使います。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Apple silicon の MLX 経路を使う場合:

```bash
pip install -e '.[mlx,torch,dev]'
```

TransformerLens、SAELens、ローカル推論サーバー向けの依存関係は [英語版README](README.md) にまとまっています。

## まず動かす

モデルをダウンロードせず、決定論的な模擬バックエンドで一周できます。

```bash
glyphprobe init ./glyphprobe-experiment
cd glyphprobe-experiment
glyphprobe plan -c configs/v1_smoke.yaml --num-layers 8
glyphprobe run  -c configs/v1_smoke.yaml
```

模擬バックエンドは配線検査専用です。そこで得た数値を研究結果には使いません。

## MLX の標準セルを再現する

標準設定には、合格済みレシートのSHA-256があらかじめ固定されています。まずは、そのレシートを使ってパネルと計画を確認し、標準実験を実行します。

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

backend実装やモデルセルを変えて再検証するときは、starter workspace から repository checkout の root へ戻り、固定済みレシートを上書きせず候補ファイルへ出力します。

```bash
cd ..  # repository checkout root
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

候補が合格したら、固定レシートと2つの標準configにある `validation_receipt_sha256` を、同じレビュー単位で更新します。速度サンプルは毎回新しく記録されるため、全ゲートが合格してもSHA-256は変わります。

モデル、リビジョン、dtype、量子化、介入点を変えた場合は別の実験セルです。新しい一致検証なしに、今回のレシートを流用しないでください。

## 読み方の約束

- 主な観測単位はターゲットプロンプトです。3つのシードはソース方向の反復推定であり、独立した観測個体ではありません。
- 一次グリフはすべて3トークンですが、トークンIDは同一ではありません。`blue_circle` は中間トークンの接頭パターンが異なり、中立グリフ `·` は1トークンです。
- ラベル置換は36 / 36セルが `p = 1/1001` に達しましたが、これは1,000回置換で到達できる有限の下限です。多重比較を補正した全体有意性ではありません。
- iso-KL、SAE、生成評価、`resid_pre`、`attn_out`、`mlp_out`、パスパッチングは、今回の標準実験では未実施です。
- 公開リポジトリには、再確認しやすい要約、監査結果、ハッシュ付きマニフェストを収録します。約74 MiB（77.3 MB）の生の介入台帳とNPZは含めません。ローカルで再実行すれば生成されます。

## 文書

- [科学的な契約](docs/SCIENTIFIC_CONTRACT.ja.md) / [English](docs/SCIENTIFIC_CONTRACT.md)
- [バックエンド境界](docs/BACKENDS.ja.md) / [English](docs/BACKENDS.md)
- [指標の定義](docs/METRICS.ja.md) / [English](docs/METRICS.md)
- [v1 実験結果](docs/RESULTS_V1.ja.md) / [English](docs/RESULTS_V1.md)
- [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) / [English](docs/MILESTONE2_RESULTS.md)
- [Milestone 2 確認実験プロトコル](docs/MILESTONE2_PROTOCOL.ja.md) / [English](docs/MILESTONE2_PROTOCOL.md)
- [E1 探索結果](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) / [English](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md)
- [E1 探索プロトコル](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) / [English](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md)
- [Multifamily tokenizer census結果](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md)
- [Multifamily tokenizer censusプロトコル](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md) / [English](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0.md)
- [Multifamily colored-shape geometry v0結果](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md)
- [Multifamily colored-shape geometry v0](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md) / [English](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md)
- [Multifamily matched-slot geometry v0結果](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md)
- [Multifamily matched-slot geometry v0](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) / [English](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md)
- [Matched-slot analysis repair v1](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md) / [English](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md)
- [Multifamily common-suffix carryover v0結果](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md)
- [Multifamily common-suffix carryover v0](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md) / [English](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md)
- [Multifamily carrier-distance v0結果](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md)
- [Multifamily carrier-distance v0](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) / [English](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md)
- [Multifamily dense CUDA carrier-distance v0結果](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) / [English](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md)
- [Multifamily dense CUDA carrier-distance v0](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.ja.md) / [English](docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md)
- [Mistral 7B base 深度×距離 v0結果](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) / [English](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md)
- [Mistral 7B base 深度×距離 v0](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md) / [English](docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md)
- [Mistral 7B semantic atlas v0](docs/MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_V0.md)
- [Mistral 7B semantic atlas batch-one v1結果](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md)
- [Mistral 7B semantic atlas batch-one v1](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md)
- [Mistral 7B semantic atlas解析計画](docs/MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md)
- [Mistral 7B semantic atlas token感度](docs/MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_TOKEN_STRUCTURE_V0.md)
- [Mistral 7B semantic atlas reserve確認 v0結果](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md)
- [Mistral 7B semantic atlas reserve確認 v0](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md) / [English](docs/MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.md)
- [Semantic atlas model横断再現 v0結果](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) / [English](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md)
- [Semantic atlas model横断再現 v0](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md) / [English](docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md)
- [Semantic atlas model横断診断 v1](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md) / [English](docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md)
- [Glyph-system decomposition atlas v0結果（T11）](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) / [English](docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md)
- [Glyph-system decomposition atlas v0（T11）](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.ja.md) / [English](docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md)
- [Glyph-system reserve confirmation v0結果（T12）](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) / [English](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md)
- [Glyph-system reserve confirmation v0（T12）](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.ja.md) / [English](docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md)
- [Glyph–name深度trajectory結果（T17）](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.ja.md) / [English](docs/GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md)
- [未提示の複合glyph確認protocol（T18）](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md) / [English](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md)
- [未提示の複合glyph確認結果（T18）](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md) / [English](docs/FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md)
- [T18 未提示表層の論文ストーリー](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.ja.md) / [English](docs/PAPER_STORY_T18_FRESH_LEXICAL_V0.md)
- [T19 語彙alias・Unicode記号対照protocol](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md) / [English](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md)
- [T19 語彙・component因果結果](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md) / [English](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md)
- [T19 語彙近傍の論文ストーリー](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md) / [English](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md)
- [Emoji steering specificity atlas v0（T13設計図）](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md)
- [Emoji steering specificity harvest v0（T13-EH）](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md)
- [Emoji steering specificity analysis v0（T13-EA）](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md)
- [Emoji steering specificity analysis v0結果](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md)
- [Emoji steering specificity bootstrap実行 v1](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md)
- [Emoji steering specificity zero-gate amendment v1](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.ja.md) / [English](docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md)
- [Emoji steering specificity compact evidence](artifacts/emoji_steering_specificity_analysis_v0/README.ja.md) / [English](artifacts/emoji_steering_specificity_analysis_v0/README.md)
- [T14-X拡張とT14-C因果結果](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md) / [English](docs/EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md)
- [絵文字 × 言葉の不一致interaction v0 protocol（T15-A）](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md) / [English](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md)
- [絵文字 × 言葉の不一致interaction v0結果（T15-A）](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md) / [English](docs/EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md)
- [絵文字 × 言葉のprospective再現 v0 protocol（T15-B）](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md) / [English](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md)
- [絵文字 × 言葉のprospective再現 v0結果（T15-B）](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md) / [English](docs/EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md)
- [E2 Stage A3 数値screen結果](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) / [English](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md)
- [E2 Stage A3 数値screenプロトコル](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) / [English](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md)
- [E2 Stage A v2 結果](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) / [English](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md)
- [E2 Stage A v2 プロトコル](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) / [English](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md)
- [E2 MPS transport v2プロトコル](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) / [English](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md)
- [E2 MPS transport v1 preflight failure](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) / [English](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md)
- [holdout状態](docs/HOLDOUT_STATUS.ja.md) / [English](docs/HOLDOUT_STATUS.md)
- [再現性ガイド](docs/REPRODUCIBILITY.ja.md) / [English](docs/REPRODUCIBILITY.md)
- [研究ロードマップ](docs/ROADMAP.ja.md) / [English](docs/ROADMAP.md)
- [英語論文の構成案](docs/PAPER_OUTLINE.ja.md) / [English](docs/PAPER_OUTLINE.md)
- [公開研究ノート](docs/NOTE.ja.md) / [English](docs/NOTE.md)

公開向けの手書き文書は、原則として英語版と日本語版を対にします。ライセンス、引用情報、スキーマ、機械生成レシート、コード内コメントは対象外です。

## Phase I のゴール

Phase Iの最終成果は、検証可能なartifactを伴う**英語論文または英語プレプリント**である。T18は未提示表層に対するprospective確認を与えた。T19は、正式短名から語彙的に独立したCLDR keywordへendpointを広げた9 / 9 cellの観測結果、非emoji Unicode記号による境界、登録済みrank 8後期component仮説の妥当な陰性因果結果を一つの論文の背骨へまとめた。T15-Bは別の運用response-shape候補に対するprospective再現として残る。これらを足し合わせても、意味、完全mediator、普遍回路、tokenizer非依存性、scale、tuning不変性、model母集団への一般化にはならない。未完了なのは、manuscript claim tableのfreeze、完全なchecksum archive、先入観のない再現性reviewである。正確な境界は[T19ストーリー](docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md)、[T19結果](docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md)、[ロードマップ](docs/ROADMAP.ja.md)に示す。

T12も、別に凍結した一度限りの設計で完了した。許される結論は、ZWJ fusion候補とregional dual候補のどちらも、登録済みの統計＋実用ruleを満たさなかったことまでである。T10の一次判定は変わらない。T13-EHは、露出済み項目と公開targetを使う凍結済みの探索的収集を完了したが、T12の判定も論文gateも変えない。T13-Cには新しい未使用bankと別freezeが必要だった。後続のT14-Cはその条件を満たしたが、T13へ遡って確認statusを与えない。

T13-EAは、その探索的な点推定まで完了した。一次判定や確認判定は置かず、登録済みcluster
bootstrapも0 / 20,000回のままである。T14-Xでは別に、6 modelの拡張応答gridを完走し、符号を持つ
非単調なmodel×depth regimeを観測した。続くT14-Cは、新しい未使用bank上で、事前規定した1つの
選択部位因果実験を完了した。IUTは非棄却だったため、Phase I gate 4は負の結果として閉じる。
同じ探索から別部位を昇格させない。続くT15-Aでは、均衡させた4 modelのinteraction gridを完走し、一次のresponse-coherence区間は16 / 16で正、二次familyは不均一だった。探索結果にとどまり、その時点では論文gateを閉じなかった。
続くT15-Bでは、軸、target、model roleをprospectiveに入れ替え、凍結済みR1の
二model intersection ruleを通過した。この狭い運用候補についてgate 5は満たした。
Paper全体の統計資格、完全archive、fresh-eyes reviewは未完了である。

## ライセンスと引用

ライセンスは [LICENSE](LICENSE)、引用情報は [CITATION.cff](CITATION.cff) を参照してください。
