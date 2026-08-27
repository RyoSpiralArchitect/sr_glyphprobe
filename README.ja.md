# GlyphProbe

[English](README.md) · [Carrier-distanceプロトコル](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) · [Common-suffix結果](docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [Matched-slot結果](docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [Multifamily geometry結果](docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [Tokenizer census結果](docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.ja.md) · [E2 MPS transport v2プロトコル](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) · [holdout状態](docs/HOLDOUT_STATUS.ja.md) · [E2 Stage A3数値screen結果](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [E2 Stage A v2結果](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [E1 探索結果](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Milestone 2 結果](docs/MILESTONE2_RESULTS.ja.md) · [基準実験の結果](docs/RESULTS_V1.ja.md) · [ロードマップ](docs/ROADMAP.ja.md) · [Phase I 論文計画](docs/PAPER_OUTLINE.ja.md)

GlyphProbe は、絵文字やグリフから作った活性化方向が、言語モデルの出力に再現可能な「指紋」を残すかを調べる研究用ハーネスです。

最初から「モデルの中で、この絵文字は何を意味するのか」とは問いません。介入量、クリッピング、ソース文、ターゲット文、ランダム方向を固定したうえで、方向ごとの差が繰り返し観測できるかを先に確かめます。

既定のパネルは、5色 × 2形状の10グリフです。

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

## 現在地

2026年8月7日時点で、次の実験セルを検証しています。

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

次の観測的な反証実験は、科学用model forwardを一度も実行する前に公開凍結した。
各入力全体と、読み出し位置にあるcarrier tokenのIDを固定し、同じ絵文字から
1、2、4、8 token後ろの`resid_post`を読む。Carrierは、`" a"`を8回繰り返した列と、
`" |"`を8回繰り返した列の2種類である。固定model roleはGemma 2 2B 4-bit、
Llama 3.2 3B BF16、OLMo 3 7B BF16で、各modelの5つの相対深度を使う。

Model-levelの主検定はintersection-union test 1件だけである。距離1での再現成分と、
事前指定したlog2距離に対する減衰contrastの両方が棄却された場合に限り、そのmodelを
棄却とする。Modelのraw p値には2成分の大きい方を使い、3 model間をHolm補正する。
この検定が捉えられるのは、固定profile上での距離1の再現と正味の減衰である。
単調減衰、距離8での消失、意味、機構、因果、tokenizer非依存性、cross-modelの
大きさ比較は示さない。役割、endpoint、permutation、outcome pattern、停止規則は
[固定protocol](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md)に定めた。科学用runと結果は未実施である。

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
- [Multifamily carrier-distance v0](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) / [English](docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md)
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

Phase I の最終成果は、検証可能なアーティファクトを伴う**英語論文または英語プレプリント**です。運用上のMilestone 2は完了し、layer 2は、新しい対象限定型の因果プロトコルを設計できる段階に入りました。Layer 4は未解決のままで、候補にはしません。C1 v1は廃止済みであり、将来の因果freezeには、露出した研究文脈の外で新しいversionのbankを用意する必要があります。E1とmultifamily tokenizer censusは探索・設計side trackであり、論文gateを閉じません。Colored-shape geometry v0は`no_dual_model_recurrence`、matched-slot geometry v0は`olmo_only_token_structured_recurrence`、common-suffix carryover v0は`olmo_only_common_suffix_carryover`で完了しました。T4によって、OLMoのT3結果を現在tokenだけで説明する記述は退きましたが、構造化された直前prefixからの短距離伝播で十分という説明は残ります。これらの観測実験は、因果、確認、tokenizer非依存性、model一般性のgateを閉じません。E2 Stage A v2とStage A3もMLX技術経路の負の資格判定として残ります。最終論文と再現実験では、analyzer role、prototype再標本化、tokenizer構造による代替説明、carryover距離を事前に扱います。因果検証、独立backendまたはmodelでの再現、完全なevidence archiveも論文gateとして残っています。

## ライセンスと引用

ライセンスは [LICENSE](LICENSE)、引用情報は [CITATION.cff](CITATION.cff) を参照してください。
