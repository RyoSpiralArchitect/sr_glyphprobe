# GlyphProbe 研究ロードマップ

[Mistral base深度×距離結果](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) · [Mistral base深度×距離protocol](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.ja.md)

[English](ROADMAP.md) · [Dense CUDA結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Carrier-distance結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Carrier-distanceプロトコル](MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) · [Common-suffix結果](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [Matched-slot結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [Multifamily geometry結果](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [Tokenizer census結果](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [E2 MPS transport v2プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [holdout状態](HOLDOUT_STATUS.ja.md) · [E2 Stage A3数値screen結果](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [E2 Stage A3プロトコル](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) · [E2 MLX validation v2結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) · [基準実験の結果](RESULTS_V1.ja.md) · [Phase I 論文計画](PAPER_OUTLINE.ja.md)

## 到達点

Phase I の到達点は、英語プレプリントとして公開できる論文と、監査可能な証拠一式です。現在固定しているGPT-2 MLX runは、そのための基準地図であり、最終的な主張ではありません。

Phase Iを通して、リポジトリで作成する公開文書は英語版と日本語版を対にして管理します。論文は英語版を正文とし、日本語の併記文書によって、研究過程を読みやすく、検証しやすい状態に保ちます。

## 研究の順序

### Milestone 1 — 再現可能なスクリーニング基準

状態: 固定済みのGPT-2 FP32 `resid_post`セル1件について完了。

- パネル、ラッパー、ターゲット、強度、レイヤー、対照を固定する。
- 対象モデルセルに限って、MLXをTransformers/MPSと照合する。
- 14,208レコードの標準行列を実行する。
- 行数、来歴、ゼロ介入、スカラー量の均衡、主要集約値の再計算を監査する。
- 正のセル、負のセル、不均一なセルをまとめて公開する。

終了条件: 内部整合性のある前因果的候補が得られていること。この段階では、意味や因果を示す表現は認めない。

### Milestone 2 — トークン化対照とnull対照の強化

状態: 運用上は完了。結果はレイヤーごとに分かれ、論文での最終的な推論上の位置づけは未確定。

- 公開凍結と事前検査の合格後、48件のP2バンクを一度だけ開いた。C1 v1はMilestone 2では使わなかったが、別に記録した研究文脈への露出により、現在は廃止済みである。
- 色付き図形パネルを、指定済みのGPT-2トークン数と、パネル単位の9対1の接頭構造を揃えた、互いに重ならない10記号のnull対照パネル3組と比較した。
- token IDを完全に一致させる対照は主張の範囲外とする。同じtoken ID列は同じ入力byte列へ復号されるため、ここで行うのはトークン化の影響を除去したglyph試験ではなく、指定済み対照に対する頑健性試験である。
- 主要仮説はlayer 2とlayer 4、strength 0.05に固定し、direction seedは各target内で平均した。
- 凍結済みv1では、layer 2が両方のsource-wrapper条件で指定済みmatched controlsに対して頑健と判定された。主要ソースは+0.208363、95% CI [0.137463, 0.276893]、Holm p = 0.00143999。独立ソースは+0.187507、[0.125489, 0.247659]、p = 0.00393996だった。
- Layer 4は両条件とも未解決だった。主要ソースは-0.0329465、[-0.0761085, 0.0110094]。独立ソースは-0.086379、[-0.159246, -0.016917]である。
- 元の探索行列では、96次元のpaired median excessが記述的に+0.047427、正セルは25 / 36だった。「何%を説明したか」という推定には使わない。
- 公開した全14 run、すなわち探索・P2・独立ソースの中核12 armと診断2 runについて、別のrole/input-binding auditが合格した。
- v1のbootstrap区間は固定済みtarget効果を再標本化し、各replicateでprototypeを作り直さない。Prototypeを共同で再構築する事後感度分析では区間が広がったが、p値やstatusは付与せず、v1判定も上書きしない。
- 2つの二次診断はいずれも14,208行のgridを完走し、errorは0件、zero-hook RMSは0、readinessは11 / 11だった。Random-adjustedのheadline優位量は、末尾token一致で+0.751225、接頭構造均一化で+0.601038だった。これはpaired comparisonのraw separation scoreとは別の評価量である。
- 96 / 48 / 32 / 24次元における記述的なstandard-minus-suffix raw-separation中央値は、+0.002624 / +0.009473 / +0.004026 / +0.009700。Standard-minus-prefixは、+0.022096 / +0.023254 / +0.011040 / +0.025387だった。96次元で正だったのは、それぞれ20 / 36セルと25 / 36セルである。この事後診断は推論も同等性判定も与えず、低次元値は同じseedによる代数的な畳み込みである。
- Matched-null Aの最初のprocessは、マシン負荷が極端に高い最中、798行で外部から中断された。Sealを保ったresumeによって、重複・欠損・error・非ゼロのzero-hook RMSなしで正確なgridを完了した。これは実行時の来歴であり、モデルに関する証拠でも、一般化できる速度の主張でもない。

凍結済みの問いと判定規則は [Milestone 2 プロトコル](MILESTONE2_PROTOCOL.ja.md)、結果と留保は [Milestone 2 結果](MILESTONE2_RESULTS.ja.md) に記録した。

終了条件: 運用上の実行は完了した。論文での最終的な確認表現と、それを支える再現実験では、run roleを凍結済みinputへ事前に直接結び付け、データ依存prototypeの再標本化を扱う。

### 探索side track E1 — トークン同型な絵文字familyのスクリーニング

状態: 範囲を限定した記述的探索として完了。公開commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558`で実行条件を凍結した後、
5本のMLX runを実施した。

- 10 code pointからなる5 blockを固定する。`sky`（`U+1F311`–`U+1F31A`）、`food`（`U+1F351`–`U+1F35A`）、`animals`（`U+1F411`–`U+1F41A`）、`transport`（`U+1F691`–`U+1F69A`）、`social`（`U+1F911`–`U+1F91A`）である。
- 各glyphを固定GPT-2で3 tokenとし、family間では第1 tokenと対応slotの第3 tokenを一致させ、第2 tokenだけをfamilyごとに変える。
- 既存`prestage_targets`の先頭24件と16件のsource wrapperだけを再利用する。P2とC1は、読み込み、tokenize、score、選択のいずれにも使わない。
- Run familyは、固定GPT-2、MLX FP32、`resid_post`のlayer 2・4、strength 0.05、seed 101 / 211 / 307、各layerのrandom direction 2本に限定する。Zero-hook checkは有効、neutral-direction armとsign-flip armは無効とする。
- Layer 2をprimary exploratory rowとした。事前指定したlayer 4のnegative comparatorは、結果としてnegativeにならなかった。
- ReplicateごとにLOTO prototypeを作り直し、\(M_{f\leftarrow g}\)行列全体、within-row超過量\(R_f\)、family等重みの\(R_{\mathrm{global}}\)を報告する。Primary descriptive aggregateはtarget等重みの平均とし、データ依存prototypeは、target groupで層化した20,000回のbootstrap内でも毎回再構築する。
- 5本のrunは全8,880介入行を完走した。Errorは0件で、zero-hookのactivation/logit RMSは正確に0だった。
- Family等重みのglobal超過量は、layer 2で0.014752595564、95%記述区間[0.002875238085, 0.027439243404]、layer 4で0.014887989201、[0.003407563347, 0.019684351979]だった。
- Family別区間は、両layerの5 familyすべてで0を含んだ。
- 平均transfer行列は広く正だった。25 cellの範囲はlayer 2で0.395455〜0.484915、layer 4で0.602564〜0.681909だった。
- Family × layer × seedの30 cell中10 cellはrandom controlを上回らなかった。Layer 2のseed 307とlayer 4のseed 101で、それぞれ5 familyすべてが該当した。
- 凍結後は全familyを公開し、null、負、不均一なcellも残す。P値、多重性判定、確認的status labelは付けない。

[E1 探索プロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md)では、問い、input、endpoint、停止規則、主張境界を定め、[E1 探索結果](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md)では全結果を公開した。広く正のtransfer行列と小さなfamily固有超過は、共有tokenによるtransferが残差的なwithin-family信号より支配的であることを示唆する。E1で記述できるのは、統制した中間token置換の下でのmatched-slot反復までである。意味上のfamily効果、tokenization非依存の性質、layer固有の効果、random controlに対する頑健な優位性、因果mechanism、modelをまたぐ規則性は主張しない。Milestone 2の判定を更新せず、C1を開かず、Milestone 3の介入も選ばず、Phase I論文gateも満たさない。

終了条件: 達成。公開bundleは、tokenizer-only preflight、全記述解析、5つの軽量run directory、root manifestを結び付けている。E1から新しい仮説を立てる場合は、P2でもC1でもない未使用target bankを用意し、新しい確認プロトコルを先に公開する。

### Engineering side track E2 — Llama 3.2 3B MLX cross-model transport

状態: Stage A v2の技術検証と、それに続くStage A3のruntime dtype screenは完了した。
V2は引き続き`status: validation_failed`、`scientific_result: false`であり、
Stage A3でもeligible candidateは選ばれなかった。固定したE2科学セルにはMLXを
採用しない。E2科学gridのforwardは、実行も許可もしていない。

V1は、公開commit `88685bd01ab115df323e9a324d49a659c66163c7`で凍結した。
Transformers/MPS phaseは完了したが、MLX phaseは最初のbaseline exportで次の
errorを出して停止した。

```text
RuntimeError: Item size 2 for PEP 3118 buffer format string B does not match the dtype B item size 1.
```

この技術的失敗は、parity比較、speed判定、科学的endpointのいずれよりも前に
発生した。V1ではreceiptを生成せず、科学的outcomeも確認していない。
[失敗記録](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)は
そのまま残す。

V2で指定したバックエンドの数値挙動に影響する変更は、MLX-to-NumPy export bridge
だけである。Native BF16 arrayをNumPyへ渡す直前に`mx.float32`へcastし、model
実行はBF16のまま保った。これにより、隔離した2つのworker phaseはどちらもreturn
code 0で完了した。両モデルを同時にメモリへ常駐させていない。固定したmodel metadataと
全9 fileのartifact manifestはbackend間で一致した。

- Parity全体は60件中33件が合格した。Token IDとbackend内の決定性は10 / 10、
  厳密なzero-hookは10 / 10が合格した。
- Baselineは6 / 10、介入後outputは7 / 10が合格した。
- Activation差分だけなら10件すべてが合格した。NRMSEは0.014057–0.018356、
  cosineは0.999832–0.999901、RMS ratioは0.999625–1.000526である。しかし、
  対応するlogit差分が明確に不合格だったため、複合差分は0 / 10となった。
  Logit差分のNRMSEは0.580523–1.402939、cosineは-0.097707–0.816940だった。
- 介入忠実度は0 / 10だった。Activation NRMSEは、固定した閾値0.01に対して
  約0.0302–0.0341だった。両backendともcosineは約0.9994、RMS ratioは約1である。
- マシンローカルな速度gateも不合格だった。Aggregate median latencyは、
  Transformers/MPSが132.127833 ms、MLXが230.138000 msである。MLXは
  1.741782892倍の時間を要し、記録したspeedupは`0.574124367x`だった。
- 研究用target bank、確認用outcome、因果outcomeにはアクセスしていない。
  E2科学grid、絵文字family、意味、因果、modelをまたぐ再現、model scaleの結果は
  得ていない。

全結果は [E2 Stage A v2結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md)、固定した
engineering gateは [プロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md)、機械可読の
記録は [v2レシート](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json) に示す。
この技術経路の不適格判定は、科学的な負の結果ではなく、Phase I論文gate 5も満たさない。

Stage A3では、同じBF16-weight artifactに対して、2つのruntime compute candidateを
公開凍結した。FP16とFP32はどちらも、identity、token・決定性、厳密なzero vector、
backend内の介入忠実度に合格した。一方、マシンローカルな速度gateには不合格だった。
MLX/MPSはFP16で1.956666698、FP32で0.986249198。凍結済み規則は0.95以下を求めていた。
したがって、決定論的な選定結果は`null` / `no_go_no_eligible_numeric_candidate`である。
Stage A3はbackend間のfull parity familyを実行していないため、FP32の忠実度が高くても、
FP32経路を適格とは扱わない。詳細は [Stage A3結果](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md)、
[凍結済みプロトコル](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md)、
[レシート](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json) に記録した。

研究責任者は、Transformers/MPS専用の科学経路を別に選択した。これはMLXを適格にせず、2つのno-goを書き換えず、v2とStage A3の閾値も緩和しない。将来MLXを再設計する場合は、別の公開engineeringプロトコルが必要である。

終了条件: 固定model/configuration identityを、完全なbackend parityおよび
Transformers/MPSの95%以下となるmachine-localなMLX aggregate median latencyへ
結び付けたatomic・no-overwrite receiptを1件作る。現時点では未達である。
V2とStage A3が残したのは、要件を満たさないことを示すfailure evidenceであり、MLX経路の適格性ではない。
将来engineering receiptが合格しても、それだけではE2も論文gateも完了しない。

### 科学side track E2b — Llama 3.2 3B MPS絵文字transport

状態: v1はmodel forward 0回のtokenizer preflight failureで廃止した。V2はmanifest commitが公開されるまでは`freeze_pending`とする。そのcommitで修正済みstatic designを固定した後も、model forwardを伴わないv2 preflight receiptだけを変更した子commitとして公開するまでは`preflight_pending`であり、実行しない。科学的outcomeはまだ存在しない。

- 固定した`mlx-community/Llama-3.2-3B-bf16` artifactを、raw Transformers、MPS、FP32 runtime parameterで使う。
- 10絵文字の5 family panelを`full50` primary armとし、`slot_03`〜`slot_09`の7絵文字panelを5本別々にcenteringする`core35` token-structure感度armとする。
- すでに探索したprestage target 24件とsource wrapper 16件だけを再利用する。P2と廃止済みC1 v1は、read、tokenize、score、selectのいずれにも使わない。
- Layer 5と11、strength 0.05、seed 101 / 211 / 307、random control 2本、厳密なzero-hook検査、target groupで層化した20,000回bootstrapを固定する。
- `full50`のlayer 5におけるfamily等重み`R_global`を唯一のprimary rowとする。両側95% percentile bootstrap区間の下端が0より大きいときだけ`transport_criterion_met`とする。その他のrowはsecondaryで、primary判定を救済しない。

完全な設計と主張境界は[E2 MPS transport v2プロトコル](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md)に示す。Primary rowが正でも、探索済みtargetを再利用したMPS上の限定transport観測である。意味、tokenizer非依存性、因果、独立targetでの確認、model scaleへの一般化は確立しない。

### Control設計side track T1 — Multifamily tokenizer census

状態: 固定tokenizer-only censusと事後記述集計として完了した。設計証拠であり、
activationの科学的結果ではない。

- mac1、mac2、furnaceで、local利用可能tokenizer 14 entryをすべて完了し、model
  forwardとprotected-target accessを0に保った。
- 固定115 item、4 context、tokenization 6,440行、pairwise 19,665行をすべて残した。
- 7つの完全一致output classは固定surfaceだけの同値classとして扱い、そのうち5 groupが
  node間で再現した。
- 7 classすべてでraw token数が不変なのは6 itemだけで、family ZWJ itemはraw
  7〜20 tokenだった。
- Blue circleとblue squareのどちらにも、どの固定pairwise contextにも、全output classで
  token数と先頭1 tokenを同時に揃える単一fixed-panel candidateがないことを記録した。
- 結果は事後的・記述的に保つ。Milestone 2を更新せず、layerを選ばず、tokenizer非依存の
  構造を確立せず、論文gateも閉じない。

[T1結果](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md)と[固定プロトコル](MULTIFAMILY_TOKENIZER_CENSUS_V0.ja.md)から、将来のcross-tokenizer activation cellでは、tokenizer output classごとにcontrolを別々にfreezeする必要がある。Atomic-tokenの場合は、outcomeを見た後にprefix ruleを緩めず、代替のstructural matchを事前申告する。

終了条件: Censusについては達成した。後続のmatched-control activation studyは、独自の未使用target、endpoint、hypothesis family、多重性ruleを持つ新しいprotocolとする。

### 観測side track T2 — Multifamily colored-shape geometry

状態: 凍結済みの観測的な負・mixed resultとして完了した。事前登録した結果patternは
`no_dual_model_recurrence`である。

- 変更しない10-item colored-shape panelをGemma 2 2B 4-bitとOLMo 3 7B BF16へ
  結び付け、Llamaのoutcomeからlayerを選ばない。
- Gemmaのatomic 1-token construction matchと、OLMoのequal-count・shared-prefix
  construction matchを、別々に申告したcontrol familyとして使う。
- 式だけで決める5つのdepth fractionにおいてraw-glyph `resid_post`を捕捉し、
  midpoint layerだけをprimaryにする。
- 5色のcircle-minus-square方向の平均平行性を、square labelの全120置換で検定する。
- 2 model-cell testを一つのHolm familyとして扱い、残る4 layerは符号にかかわらず残す。
- Intervention、generation、protected-target access、cross-model magnitude比較、
  outcome後のlayer差し替えを行わない。
- Gemmaのprimary midpoint（`T = 0.114857969`、raw `p = 0.058333333`、
  Holm `p = 0.116666667`）とOLMoのprimary midpoint（`T = 0.024628040`、
  raw・Holm `p = 0.275`）を、どちらも棄却なしとして残した。
- 2本のactivation array、固定深度の全10行、生成元・relayのhash証拠、合格したrun・
  analysis validatorを公開した。

[T2結果](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md)と
[完全なfreeze](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md)には、Gemmaの
非primary layerに現れた小さな記述的p値も、格上げせずに残している。Model family、scale、
precision/quantization、tokenizer構造、nodeは交絡したままで、2つのraw magnitudeを
scale差やquantization差とは読めない。

終了条件: 達成した。Role-bound run 2本とjoint exact analysisをchecksum付きで公開した。
このside trackは、因果gateも独立backend再現も置き換えない。

この分岐から、5 familyへ広げる案をT3として結果を見る前に選んだ。同じartifactに
近いprecision contrastと独立実装は、結果を救済する解析ではなく、今後の候補として残す。

### 観測side track T3 — 5 family matched-slot geometry

状態: `olmo_only_token_structured_recurrence`として完了した。

- E1のsky、food、animals、transport、social panelを変更せず、5×10のcrossed designに
  結び付ける。
- Forward前に、Gemmaの50個の固有atomic tokenと、OLMoの厳密な
  `[shared_prefix, family_token, slot_token]`分解を要求する。
- 両model roleで、式だけから選ぶ同じ5 depth fractionをcaptureする。
- Family平均を引き、共有slotの平方和比率を深度ごとの統計量にする。
- 固定5深度の等重み平均だけをmodel-level primary endpointにする。
- Family内slot labelの独立randomization 19,999回を全深度で同期し、2 model-level testを
  Holm補正する。
- 深度別10行をすべて残し、どの深度にも判定権を与えない。
- 最初のreceipt serialization failureを記録し、key normalizationだけのrepairを結果の
  再解析前に公開freezeする。

Gemmaは`T = 0.204304805`、null平均`0.199984463`、Holm `p = 0.2085`で棄却しなかった。
OLMoは`T = 0.500391869`、null平均`0.200184835`、Holm `p = 0.0001`で棄却した。
OLMoのslot比率は固定profile上で`0.994722`から`0.295828`へ下がったが、全深度でnullを
上回った。深度別の値は副次記述である。

[T3結果](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md)、[固定protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md)、[analysis repair](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md)では、tokenizer条件に沿う解釈を明示した。OLMoが厳密に共有する末尾tokenだけで再現を説明できる。Model family、scale、precision、nodeは交絡したままであり、tokenizerの因果contrastでも意味効果でもない。

終了条件: 達成した。1 token後ろの共通接尾で反証する案をT4として結果を見る前に選び、
次節のとおり完了した。同じartifactに近いtoken/precision deconfoundと、同じendpointの
独立実装は今後の候補として残る。T3はPhase I gateを閉じず、因果layerも選ばない。

### 観測side track T4 — 共通接尾tokenへのcarryover

状態: `olmo_only_common_suffix_carryover`として完了した。

- T3のpanel、2つのmodel artifact、5 depth fraction、model roleを変更せず再利用する。
- 全絵文字へperiodまたはnewlineを加え、生token列全体を厳密なprefixとして保ったまま、
  1個の共通接尾tokenだけを追加する。
- 絵文字自身の末尾ではなく、その共通接尾tokenの`resid_post`を読む。
- 固定2文脈×5深度の等重み平均だけをmodel-level endpointにする。
- Family内slotの19,999 permutationを10個すべての文脈×深度セルで同期し、2つの
  model-level testをHolm補正する。
- T3統計は記述参照として固定し、推論には統合しない。

Gemmaは`T = 0.203443011`、null平均`0.200044692`、Holm `p = 0.30295`で棄却しなかった。
OLMoは`T = 0.537464703`、null平均`0.199977865`、Holm `p = 0.0001`で棄却した。
OLMoの副次的なperiodとnewline統計は`0.538985382`と`0.535944025`で近かった。したがって
OLMoのmatched-slot geometryは、固定した両文脈で1つ後ろの共通tokenにも観測でき、
Gemmaはnull付近に残った。

[T4結果](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md)、[固定protocol](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md)、[公開evidence](../artifacts/multifamily_common_suffix_carryover_v0/README.ja.md)には、全20 rowとcompactな全arrayを残す。T3を現在tokenだけで説明する記述は退くが、直前の構造化token列から短距離で伝わるだけという説明は残る。意味、因果、確認、tokenizer非依存性、cross-model magnitude contrastは示さない。

終了条件: 達成した。介入前の安価な次の反証として、事前固定したcarrier-distance decay
assayが有用である。ただしside trackに留め、tokenization-matched確認controlの代替にも、
Phase I gateのclosureにも使わない。

### 観測side track T5 — Carrier-distance profile

状態: `no_model_distance_attenuation`として完了した。

- 入力全体と読み出し位置のcarrier token IDを固定したまま、各絵文字から1、2、4、8
  token後ろへ読み出し位置を動かす。
- `" a"`と`" |"`をそれぞれ8回繰り返す2種類のcarrierを使い、tokenizerが同一tokenの
  反復という契約を厳密に満たさないmodel cellは実行しない。
- Gemma 2 2B 4-bit、Llama 3.2 3B BF16、OLMo 3 7B BF16の固定roleで5つの相対深度を
  調べる。各modelは400 forwardで、介入、生成、保護targetへのアクセスは行わない。
- Modelごとに、距離1の再現成分と、事前指定したlog2距離に対する減衰成分の両方を
  intersection-union testで要求する。
- 2成分のp値の大きい方をmodelのraw p値とし、modelごとにfamily内で同期した19,999
  permutationを使ったうえで、3つのmodel role間をHolm補正する。

この設計は、固定profile上で正味の減衰を伴う再現と、指定した減衰contrastを伴わない
持続を分ける。単調減衰、距離8での消失、意味内容、機構、因果、tokenizer非依存性、
cross-modelの大きさの同等性は示さない。LlamaのStage A parity failureは有効なままで、
このMLX cellが認めるのはartifact内の観測結果だけである。

Gemmaの距離1成分はnull付近だった。LlamaとOLMoの距離1成分のraw p値は、いずれも
`0.00005`だったが、減衰成分は棄却しなかった（`p = 0.188`と`0.9977`）。Model IUT/Holm p値は
Llamaが`0.564`、OLMoが`1.0`で、Gemmaも`1.0`だった。固定outcomeは
`no_model_distance_attenuation`である。

LlamaとOLMoは距離8でも記述的には高い。最初の捕捉layerは距離とともに下がる一方、
後半の固定深度は平坦または上昇する。この距離×深度の不均一性は副次結果であり、失敗した
model-level endpointと差し替えられない。Interactionの追試や、共有slot構造だけを壊す
same-artifact controlには、別の事前凍結が必要になる。

終了条件: 達成した。[全結果](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md)、3つのsealed
run、120 rowのjoint analysis、transfer receipt、public manifestを公開する。T5はPhase I
gateの外に置き、T4は記述参照としてのみ使う。

### 観測side track T6 — Dense CUDA carrier-distance replication

状態: `no_dense_model_distance_attenuation`として完了した。Prospective freeze時点の
T6 model forwardは0であり、その後、自然なlifecycleとfree-furnaceの開始gateを満たして
実行した。

- T5の公開panel、`" a"`と`" |"`の反復carrier、距離1・2・4・8、5つの相対深度、
  IUT、19,999 draw randomization、model-level Holm判定を変えない。
- 炉に完全なlocal artifactがあるGemma 2 2B IT、Gemma 3 4B IT、Mistral 7B
  Instruct v0.3、Gemma 3 12B ITを、BF16 Transformers/CUDAで別process実行する。
- 観測した3つのtokenizer output classと、各modelの全file artifactを最初のmodel loadより
  前に固定する。
- 1 model 400 forward、合計1,600 forwardとし、介入、生成、behavior scoring、
  protected-target accessは0に保つ。
- T5は記述的な設計参照に限定し、推論へ統合しない。

RosterはT5の結果を見た後、炉に完備されたartifactから選んだ。4 cellはすべて
instruction-tunedである。2Bから12Bというlabelと、tokenizerが同一のGemma 3 4B・12B
pairは記述的な設計構造であり、scale標本やbase/instruct比較ではない。4つのmodel IUTを
1つのHolm familyで扱い、carrier、distance、depth、tail、pair、timingは副次結果にする。

最初のmodel loadには、直前の`spiral status`で炉が空いていることと、新しい
`resource:furnace`通知がreceiver-ownedな自然task lifecycleでsurfaceすることの両方を
要求する。Canonical replication、watcher到着、OS popupだけでは後者を満たさない。
Probe、trust bypass、interruptで証跡を作らない。

Holm補正後に通過したmodel-level IUTはない。Mistralは距離1成分をpermutation下限
（`p = 0.00005`）で棄却したが、減衰成分は棄却しなかった（`p = 0.46975`）。他の3 cellは
距離1を棄却していない。Mistralの距離8成分とGemma 3 12Bの名目的tailは副次結果のまま
格上げしない。Gemma 3 pairからscale trendも推定しない。

終了条件: 達成した。[全結果](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md)、
4つのsealed run、160 row joint analysis、transfer receipt、public manifestを公開する。
T6単独では因果、確認、tokenizer非依存性、backend parity、model一般性、scaleの論文gateを
閉じない。Model幅の追加は優先度を下げ、別に凍結するstructure-breaking controlまたは
距離×深度interactionへ移る。Phase I本線ではtokenization-matched controlsと未使用の
confirmatory target setを優先する。

### 観測side track T7 — Mistral base 深度×距離

状態: `recurrence_and_early_depth_attenuation_excess`として完了した。T6でMistral
Instructのprofileを観測した後、T7 model forwardを1回も行う前にendpointを固定してpushした。
Prospectiveなのは、それまで未観測だったMistral 7B v0.3 base modelのoutcomeに対してだけである。

- T6の公開50-item panel、2 carrier、距離1・2・4・8、5つの相対深度、family内で同期した
  slot randomization、400-forwardの観測境界を保つ。
- 失敗した全深度decay conjunctionの代わりに、距離1の反復と、初期深度の減衰から後期4深度の
  平均減衰を引いた正のinteractionを同時に要求する1つのIUTを固定する。
- 距離weight `[0.375, 0.125, -0.125, -0.375]`、19,999 PCG64 draw、seed
  `2026082801`を使い、1 modelの判定scopeには多重性補正を置かない。
- 介入、生成、behavior scoring、protected-target accessは0に保つ。

距離1の反復統計は`0.377524026`、固定した初期−後期深度interactionは`0.149104068`で、
片側raw p値はいずれもpermutation下限`0.00005`に達し、IUTは棄却した。深度0の減衰は
`+0.114009450`、後期深度の平均は`-0.035094618`だった。元の全深度減衰は負で、棄却
しなかった（`p = 0.87475`）。

Base modelの20個の深度×距離cellは、既知のT6 Instruct profileと記述的には近かった
（`r = 0.996785730`、MAE `0.011953404`）。これは同等性検定でもinstruction tuningのcontrast
でもない。ModelとendpointはT6後に選び、checkpointは関連しており、新しいmodel cellは1つだけ
だからである。独立確認ではなく、意味、因果、scale、tokenizer非依存性、backend parity、
Phase I gateのclaimを認めない。

終了条件: 達成した。[全結果](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md)、sealed
400-forward run、40-row analysis、transfer receipt、public manifestを公開する。将来の
structure-breaking controlまたは真に独立した追試には新しいprospective freezeが必要である。
T7は、tokenization-matched controlsと未使用confirmatory setという本線の優先順位を変えない。

### Milestone 3 — 対象を絞った因果局在化

状態: プロトコル設計へ進める。ただし、因果プロトコルはまだ凍結しておらず、因果主張も認めない。現時点の候補はlayer 2だけで、layer 4は未解決のため候補にしない。別の確認用bankは、このプロトコル設計に着手するための前提条件ではない。

- モデル系列ごとのparity確認後に限り、`resid_pre`、`attn_out`、`mlp_out`、`resid_post`を比較する。
- 事前指定した候補レイヤー周辺で、component patchingとpath patchingを行う。
- ablation、restoration、projection-removal介入を用いる。
- 候補fingerprintを変えないはずのnegative controlを含める。
- 一度の大きなdriftではなく、holdout上での選択的効果を要求する。
- C1 v1は廃止済みである。露出した研究文脈の外で新しいversionの因果bankを作り、介入、endpoint、対照、候補layer、多重性familyを公開凍結するまで未使用に保つ。

終了条件: 事前指定した介入が候補効果を選択的に変え、matched controlsを通過すること。それまでは`causal_claim_authorized`を`false`のまま保つ。

### Milestone 4 — 再現と適用境界の把握

状態: 計画中。

- adapter-level parityだけでなく、raw TransformersまたはTransformerLensで確認セルを再実行する。
- 少なくとも1つの別model familyとtokenizerで再現を試みる。
- weight履歴を利用できる場合は、checkpoint間での出現時期を調べる。
- prompt domainとtarget template familyをまたいで頑健性を検証する。
- architecture固有の観測と、modelをまたぐ規則性を分ける。

終了条件: 何が再現し、何がGPT-2固有のままかを論文で明確に述べられること。

### Milestone 5 — 確認的統計

状態: Milestone 2 v1について一部完了。ただし、bootstrap依存の扱いは未確定。

- target promptを主要な標本clusterとして扱う。
- direction seedとtarget splitは入れ子の反復とし、独立標本として数えない。
- primary endpointと、小さく限定したprimary hypothesis familyを定義する。
- そのfamilyに適した多重性補正を用いる。
- p値と併せて、効果量、区間、負のセル、感度分析を報告する。
- `1/1001`の置換下限と、全体有意性の主張を区別する。
- 次の確認analyzerでは、CLI順序と別監査に頼らず、科学的なrun roleを凍結済みconfigとinputへ直接結び付ける。
- データから推定するprototypeは各再標本内で作り直すか、別の依存対応estimatorを結果確認前に根拠とともに凍結する。

終了条件: 標本構造に合った統計解析を、凍結済みartifactから再実行できること。

### Milestone 6 — 英語論文とアーカイブ公開

状態: Phase Iの目標。

- 文章を磨く前に、英語論文の主張表を凍結する。
- 主要な図表を、バージョン管理した解析scriptから直接生成する。
- model、revision、tokenizer、environment、implementation、inputのreceiptを公開する。
- 完全なraw ledgerと必要なarrayを保管する。難しい場合は、統制された再現可能なアクセス方法を文書化する。
- checksumと省略記録を明記した、コンパクトなrepository packageを公開する。
- 内部の反証レビューと、独立した再現試行を完了する。
- 英語プレプリントと日本語の公開概要を発表する。

終了条件: 論文の各主張が凍結済みartifactを参照し、重要な留保がabstractまたはLimitationsに現れ、独立した読者が欠けた証拠を推測で補わずに解析を再現できること。

## Phase I 論文のゲート

次の条件をすべて満たすまで、論文をdraftからpreprintへ進めません。

1. primary hypothesisと主張境界を正確に凍結する。
2. 新しいversionの確認用target setを探索的な選択に触れさせない。
3. トークン化を揃えた対照実験を完了する。
4. 正負を問わず、対象を絞った因果実験を少なくとも1件完了する。
5. 独立したbackendまたはmodelでの再現を少なくとも1件完了する。
6. cluster構造と多重性を反映した統計を報告する。
7. 負のセルと不均一なセルを、本文または補足で見える状態に保つ。
8. 完全な証拠archiveを保管し、checksumを付ける。
9. リポジトリの英語・日本語文書を同期する。
10. 英語論文について、先入観のない再現性・主張境界レビューを行う。

これらのゲートは、正の結果を前提にしていません。実験の識別可能性とartifactの完全性を保てるなら、境界を明確にした負の結果やmixed resultも、Phase Iの妥当な到達点です。

現時点では、ゲート1〜3にGPT-2固有の実行上の根拠がある。ただし、multifamily tokenizer censusはゲート3をtokenizer間へ拡張しない。その拡張には、tokenizerごとに別々に凍結したcontrol panelが必要である。T2は2つのregimeを観測的に使い、事前指定したmidpointはいずれもHolm補正後に棄却しなかった。T3では5 familyのmatched-slot factorialを使い、同じ末尾tokenを厳密に共有するOLMoだけが再現し、Gemmaのatomic-token omnibusは棄却しなかった。T4では読み出しを1つ後ろの共通tokenへ移し、固定した両接尾文脈でもOLMoだけが再現した。これにより現在tokenだけの説明は退くが、OLMoの構造化prefixからの短距離伝播で十分という説明は残る。T2〜T4はtokenizerの因果contrast、独立再現、意味効果ではなく、論文gateを閉じない。T5とT6では登録済みmodel-level距離減衰conjunctionを棄却したmodelがなかった。T7では、選択したMistral base cellの固定した距離1＋初期−後期深度IUTをprospectiveに棄却したが、T6後のendpoint・model選択と関連Instruct参照により、独立確認やinstruction tuning効果は主張できない。T5〜T7は深度依存の観測記述を鋭くするが、gate 4・5は閉じない。また、prototype再構築解析が事後的だったため、ゲート6の最終的な統計資格は未確定である。ゲート4、5、8、10は未完了。ゲート9は、公開文書を更新するたびに維持する。英語論文がPhase Iの終点であり、現在のリポジトリはエビデンスを伴う研究リリースであって、完成原稿ではない。

## Phase I より先の候補

Phase IIでは、E1で固定した5つの絵文字blockを超える拡張、multimodal tokenizer、学習済みfeature basisの解析、intervention orbit、training checkpoint間の比較などが候補になる。Phase I論文が完了するまでは、現在の実施範囲に含めない。
