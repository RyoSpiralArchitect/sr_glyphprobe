# Glyph-System Decomposition Atlas v0（T11）

[English](GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [完了した探索結果](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [T10-D診断](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md) · [T10結果](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [ロードマップ](ROADMAP.ja.md)

状態：**探索protocolを凍結済み。取得とdiscovery解析は完了**。

この文書は、outcomeを見る前に固定したprotocolを保存する。公開freeze時点ではT11 model forwardはゼロだった。73,566-forwardのdiscovery atlas完了結果と、未forwardのまま保ったreserve 268件は、[T11結果](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md)に分けて報告する。

T11で問うのは、次の一点である。

> glyph→名前対応は、glyphの合成構造、表示形式、whole-sequenceの語彙化のどれに追従し、固定したmodel/tokenizer cellは、どの正規化depthまたはfinal normalization境界で分岐するか。

変則的なmulti-codepoint glyph systemを直接調べる最初のlaneである。Activation outcomeに対してはprospectiveだが、確認的一次検定を持たない探索研究として扱う。T10の救済、意味や理解、因果、機構、behavior、tokenizer非依存性、scale law、instruction-tuning効果、model一般性は、いずれも主張しない。

## なぜT11ではobservableを変えるのか

T10の登録済みモデル横断一次判定は負のままである。一方、T10-Dでは、72セルすべてに正の連続retrieval marginがあり、carrier-distanceのbottleneckはmodelごとに異なり、item coverageは大きく偏り、codepoint比較は弱く、final norm境界の変化もmodel依存であることがわかった。さらに、292項目におけるT10の最小セル下限`0.02`は、正味6件という離散的な規則だった。

そこでT11では、最小top-1をT10との比較用の副次指標に下げる。主に見るのは、item-levelの連続matched-label margin、MRR、breadthと集中度、文脈安定性、geometry、depth trajectory、rawからfinalへの変化である。T10を読み替えるのではなく、新しいpopulationで別の問いを立てる。

## 固定sourceと決定論的なsystem分類

Population sourceは、Unicode Emoji 17.0の`emoji-test.txt`だけを使う。

- URL：`https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt`
- bytes：`669,326`
- SHA-256：`1d8a944f88d7952f7ef7c5167fef3c67995bcae24543949710231b03a201acda`
- fully-qualified entry：`3,944`

固定classifierで分けると、single-codepoint 1,184件のほかに、presentation selector sequence 207件、単純modifier sequence 665件、ZWJ sequence 1,614件、regional-indicator flag 259件、keycap 12件、tag flag 3件がある。

選定には、三つの固定namespace下でSHA-256順位を使う。System内sampling用、reserve割当用、depth subset用である。Tokenizer outcomeもactivation outcomeも選定に入らない。

## 固定populationと未開封reserve

選定した1,111項目は次のとおりである。

| System | 既露出anchor | T11 discovery | T11 reserve |
|---|---:|---:|---:|
| Single-codepoint atomic anchor | 64 | 0 | 0 |
| Presentation selector | 0 | 160 | 40 |
| Simple modifier | 0 | 192 | 64 |
| ZWJ composition | 0 | 256 | 96 |
| Regional-indicator flag | 0 | 160 | 64 |
| Keycap | 0 | 8 | 4 |
| Tag flag | 0 | 3 | 0 |
| **合計** | **64** | **779** | **268** |

64件のatomic anchorは、3 viewのcalibratorである。Unicode Emoji 17.0のsingle-codepoint項目は、すべてT8またはT9でforward済みなので、`calibration_prior_exposed`と明記し、新しいevidenceとは呼ばない。Flagsを除くUnicode 8 groupから8項目ずつ選ぶ。

T11で取得するのは843項目、つまり64 anchorと、未使用だったmulti-codepoint discovery 779件である。Reserve 268件の識別子とsource metadataは、選定manifestに公開した状態で固定する。ここでいう「未開封」はinput文字列を隠すという意味ではない。Tokenizer上の共変量は確認してよいが、T11ではmodel forwardもmodel outcomeの観測もゼロを保つ。Discovery解析後、T12で一つのendpointとmultiplicity familyを凍結してから、初めてreserveのmodel outcomeを開く。

## 固定した5 view

変則systemの各項目には、五つの文字列を持たせる。

1. `glyph`：fully-qualified Unicode sequenceそのもの
2. `unicode_name`：固定sourceのUnicode名
3. `component_name`：決定論的に構成したcomponent label
4. `codepoint_literal`：大文字`U+...`のsequence
5. `decomposed_form`：決定論的な非融合形または表示変更形

Atomic anchorはglyph、Unicode名、codepoint literalの三つだけを使う。存在しないviewを文字列の複製や創作で埋めず、明示的maskとNaNで表す。

`component_name`は標準aliasでもsemantic ground truthでもない。可能な限り固定emoji-testのcomponent名を使い、該当名がないscalarだけ、小文字化したUnicode character nameへfallbackする。ZWJ componentは`" + "`で結び、modifierではbaseとmodifierを別々に名付け、regional indicatorはletter labelへ変換する。

`decomposed_form`はsystemごとに一つの規則へ固定する。

- presentation pairではVS15/VS16を除く
- baseとmodifierの間にspaceを入れる
- 他のscalarを保ったままZWJをspaceへ置換する
- regional indicatorを2文字のASCIIへ変換する
- keycapはbaseの記号または数字だけを残す
- tag flagはtag letterを小文字ASCIIへ変換する

各analysis system内で、利用可能なviewはUnicode textとしても各model cellのtoken sequenceとしても一意でなければならない。失敗したcellはmodel load前に停止し、項目の削除やrepairは行わない。

## Token長を揃えた誤名control

Codepoint textは弱い比較対象として残すが、唯一の負対照にはしない。Model/tokenizer、glyph system、target viewごとに、target token数が完全一致する層の内部で、決定論的なwrong-label mappingを作る。Singletonでない各層をhash順に並べて一つ巡回させるため、自分自身のlabelには対応しない。同じ規則をdepth subset内でも独立に作る。

Distributional analysisを行う全systemで、必須control coverageは`0.75`以上とする。Target先頭token IDまで一致させる厳しいsensitivity mappingも記録するが、coverage gateは設けず、必須mappingの代わりには使わない。Coverage検査はmodel weightをloadする前に完了する。Outcomeを見てmapping、層、項目、thresholdを変えることは禁止する。

Tag flagは3項目だけのbounded microcaseである。固定viewとfinal endpointは取得するが、distributional claimもmatched-control claimも行わない。

## 固定transportと文脈grid

T10で使った9 cellを、outcomeによるmodel選択なしでそのまま使う。

- Llama 3.2 3B base
- Qwen 2.5 baseの0.5B、1.5B、3B、7B
- OLMo 2 1B base
- Gemma 2 2B Instruct
- SmolLM2 1.7B base
- Mistral 7B Instruct v0.3

正確なrevisionとartifact manifestはT10 freezeから継承する。Architecture、size、tokenizer、corpus、tuningは交絡したままである。9 cellすべてを再利用することで、pairingを保ち、T10で良かったmodelだけを選ぶことも避ける。

各viewでは、一tokenのcarrier `" a"`と`" |"`をそれぞれ8回続け、距離1、2、4、8を読む。Carrier追加後のtoken列は、raw view token IDに同一carrier IDが8個続く形でなければならない。一つのbatch-one forwardから4位置を読む。Runnerはmodel load前と各shard開始前に、別のGPU computeがないか検査する。

CUDA/BF16の炉laneを使うのは、T10と同じmodel artifactとAPI endpoint semanticsを保つためである。別系統のMLX engineering laneとは結果を混ぜない。

## Broad endpointと正規化depth subset

取得対象843項目では、同じforwardから二つのendpointを保存する。

1. Forward hookで取るraw最終decoder block出力
2. `output.hidden_states[-1]`、つまりAPIが返すfinal hidden state

後者は多くの実装でfinal norm後である。二つをまとめて`resid_post`と呼ぶと、T10-Dで見えたmodel依存の境界を消してしまう。

T11 forwardより前に、192項目のdepth subsetを固定する。Atomic anchor 24件（8 groupから3件ずつ）、presentation 24件、modifier 40件、ZWJ 56件、regional flag 40件、keycap 8件である。同じforwardから、次を保存する。

- embedding output
- `floor(0.25L)`、`floor(0.50L)`、`floor(0.75L)` block後のinter-block state
- raw最終block出力
- 返却final state

これは正規化したAPI depth fractionであり、architectureごとのinter-block stateが機構的に同じsiteだとはみなさない。

## Cost、shard、storage

取得対象843項目には、利用可能なitem-view pairが4,087組ある。Carrierが二つなので、1 modelあたり8,174 unique forward、9 modelで73,566 forwardとなる。Broad atlasは1 modelあたり65,392本、固定depth subsetは43,776本を保存し、9 model合計では982,512本のFP32 vectorとなる。

1 modelを最大16項目の53 shardへ分け、全体で477 shardとする。完了shardはatomicに公開し、再取得しない。Partial stageは手動判定が必要である。Atomic viewの非存在を表すNaN slotも含むdense `.npy`は、metadataを除いて約9.15 GiBになる。Raw dataは炉のdata archiveにだけ置き、GitにもSpiralShareにも載せない。

## 探索analysisの契約

T11には一次仮説検定を置かない。System、model、endpoint、carrier、distanceごとに、次を報告する。

- paired cosine、top-1、MRR、paired-minus-off-diagonal margin、linear CKA
- correct labelとtoken長matched wrong labelのitem margin差
- retrieval breadthと集中度
- 8文脈における符号割合、範囲、median absolute deviation
- median marginの記述的item bootstrap区間
- raw→final変化と固定depth trajectory
- model横断のview別item-geometry CKA、cosine-map agreement、item-margin agreement

Retrieval breadthは、top-1で到達したtargetの種類数を、そのsystemのtarget数で割った値とする。Top-decile concentrationは、予測回数が多い上位`ceil(0.10n)`件のtargetへ、全予測の何割が集中したかを表す。どちらも順方向と逆方向を記録する。Targetの先頭token IDまで揃えた厳しいmappingは、coverageがゼロの場合も含め、必須controlとは分けてsensitivity結果として残す。

返却final stateの各連続marginについては、model、glyph system、8個のcarrier-distance文脈による、釣り合った三要因の平方和分解も行う。すべての二要因interactionと三要因residualを残すが、これはheterogeneityを記述するための集計であり、random-effects modelによる推論ではない。Depthの各cellでは、記述的bootstrap区間が初めてゼロを外れたdepthがあれば記録し、returned finalとraw last blockのmedian差も併記する。

問いを操作化するcontrol-adjusted contrastは三つである。

- `lexicalization`：glyph→公式名advantage − glyph→component名advantage
- `presentation_or_fusion`：glyph→公式名advantage − decomposed form→公式名advantage
- `component_tracking`：decomposed form→component名advantage − glyph→component名advantage

いずれも操作的contrastであり、意味そのものを直接測る値ではない。最小top-1は副次に限り、T10の改訂には使わない。

## 事前に用意した着地点

綺麗な着地点として、compositional candidate、whole-sequence lexicalization candidate、presentation/final-norm境界、model-conditioned atlas、matched control後のtokenizer-structural account、broad bounded nullの六つを残す。Analyzerは各分岐に関係するevidenceを記録するが、権威的な科学結論を自動選択しない。

正のT12 claimへ進むなら、reserve 268件をforwardする前に新しいfreezeが必要である。Broad nullなら、T8〜T10のalignmentは変則glyph systemへ広がらなかったという境界として残す。

## 炉での実行順序

最初にcommit済みfreezeを監査する。炉では、model forwardゼロのまま9件のtokenizer/artifact preflightを行い、aggregate preflightでhashを束ねる。もう一度contensionを確認してから、resumable acquisitionへ進む。

```bash
python scripts/glyph_system_decomposition_v0.py audit-freeze

python scripts/glyph_system_decomposition_v0.py preflight-all \
  --output <preflight-dir>

python scripts/glyph_system_decomposition_v0.py run \
  --model-label <role> \
  --preflight-directory <preflight-dir> --output <runs-root>/<role>

python scripts/glyph_system_decomposition_v0.py finalize \
  --model-label <role> --preflight-directory <preflight-dir> \
  --run <runs-root>/<role>

python scripts/glyph_system_decomposition_v0.py summarize \
  --run <runs-root>/<role> --preflight-directory <preflight-dir> \
  --output <summaries-root>/<role>

python scripts/glyph_system_decomposition_v0.py analyze \
  --runs-root <runs-root> --summaries-root <summaries-root> \
  --output <analysis-dir>

python scripts/glyph_system_decomposition_v0.py validate-analysis \
  --analysis <analysis-dir>
```

Remote compute直前にはoperatorが`spiral status`を実行し、競合があればyieldする。`run`には`--shard-start`と`--shard-stop`を指定でき、再実行時には完了shardを検証してskipする。Runner自身も完了shardの境界でyieldする。`preflight-all`と`run`は、local Hugging Face cacheに存在する固定revisionだけを解決し、downloadは行わない。Cache配置が標準と異なる場合は、single-cell commandへ明示的な`--model-path`を渡せるが、weightをloadする前に9件すべてのreceiptをaggregateする条件は変わらない。
