# E2 Stage-A v2プロトコル: Llama 3.2 3B MLX engineering validation

[English](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md) · [研究ロードマップ](ROADMAP.ja.md) · [E1探索プロトコル](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md)

プロトコルID: `glyphprobe-e2-llama32-3b-mlx-engineering-validation-v2`

## 状態と目的

公開後のprotocol status:
`frozen_by_public_commit_containing_this_protocol`。Execution status:
`validation_pending`。Stage: engineering validation。

このfrozen statusが有効になるのは、公開commitがこの英日文書とv2の実装・検証
codeを結び付けた時点である。公開前の実効statusは`freeze_pending`であり、v2の
validation forwardは認めない。

このプロトコルは、E2のcross-model transport side trackに先立ち、backend
parityとマシン内速度のgateを固定する。対象は、1つの固定済みLlama 3.2
3B BF16 artifactについて、必要な`resid_post`介入cellをMLXで実行したとき、
Transformers/MPSに十分近い出力が得られ、かつ検証機でforward latencyの集約中央
値が少なくとも5%短いか、というengineering上の問いだけである。

英日文書、validatorとそのtest、固定した検証inputと閾値、実装identityを次の
公開commitで結び付けるまで、v2のvalidation forwardは認めない。合格receiptで
選択できるのは、固定済みE2 cellに対するMLXだけである。これは科学的結果でも、
cross-model replicationでも、絵文字表現に関する証拠でもない。

## V1の試行記録とv2で変更する一点

V1は、公開commit `88685bd01ab115df323e9a324d49a659c66163c7`で
凍結した。その後にengineering validationを試行し、Transformers/MPS phaseは
完了したが、MLX phaseは最初のbaseline exportで停止した。正確なerrorは次の
とおりである。

```text
RuntimeError: Item size 2 for PEP 3118 buffer format string B does not match the dtype B item size 1.
```

この技術的失敗は、parity比較、speed判定、科学的endpointのいずれよりも前に
発生した。V1ではreceiptを生成せず、E2用backendも選択せず、科学的outcomeも
確認していない。したがって、正負どちらのmodel結果にも当たらない。

この試行の機械可読な記録は
[`attempt_01_failure.json`](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)
に保存する。

V2で変更するengineering処理は1点だけである。MLXのBF16 arrayを、NumPyへ
exportする直前に`mx.float32`へcastする。Model実行はnative BF16のまま維持する。
固定model artifactとrevision、artifact inventory、prompt、layer、閾値、
intervention vectorの構築方法とbyte列、warm-up・計測回数、timing境界、process順、
receipt rule、科学的な境界はv1から変更しない。V1のfreezeと失敗した試行は公開履歴
として残し、v2で上書きも再解釈もしない。

この修正により、hash対象である`src/glyphprobe` treeは変わる。そのため、過去の
MLX parity receiptは現在のcheckoutを認定しない。GPT-2とE1の既存証拠は、元の
implementation commitへ結び付けた履歴として維持し、書き換えない。現在のsourceで
新しくrunする場合は、versionを分けた新しいreceiptを必要とする。

## 固定する候補cell

Validatorは、次の候補だけを使用する。

- model artifact: `mlx-community/Llama-3.2-3B-bf16`
- immutable revision:
  `60a99aaf43164077157d64bf909b7b61143c6a6d`
- model role: base model。Instruction-tuned variantやchat templateは用いない。
- 演算: 両backendともmodelをnative BF16で実行する。
- reference backend: MPS上のTransformers
- candidate backend: Apple GPU上のMLX
- 期待するarchitecture metadata: decoder 28層、hidden width 3,072、
  vocabulary size 128,256
- tokenizer動作: `add_special_tokens: false`。Chat templateもsystem promptも
  用いない。
- capture/intervention site: `resid_post`
- capture/intervention position: `last_nonpad`
- 固定intervention layer: `[5, 11]`

固定済みlocal artifact inventoryは9 file、合計6,434,705,789 byteである。Manifest
SHA-256は
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`。
このinventoryはtokenizer fileとweight fileだけから算出しており、modelのloadも
forwardも行っていない。両backend stageは、それぞれvalidationに入る前に、この
inventoryとmanifest identityを完全に再現しなければならない。

Architecture metadataはinvariantであり、実行時に補正する対象ではない。読み込んだ
artifactが期待値のいずれかと異なる場合、両backendのmodel widthまたはlayer数が
一致しない場合、あるいはいずれかのbackendから固定した2つの`resid_post` siteを
取得できない場合、validatorはfail closedとする。

Layer indexは、相対的なdecoder depth `[0.2, 0.4]`から次式によって1回だけ決める。

\[
\operatorname{layer}(d)=\operatorname{round}(d(N-1)).
\]

0始まりのindexと`N = 28`を用いると、layer 5と11になる。Validationまたは科学的
結果に応じてindexを選び直してはならない。

## 固定するsynthetic input

検証inputは固定済みのengineering probeである。そのうち3件では、tokenizerと
adapter surfaceを確認する目的に限って、公開済みE1 panelのglyphを使う。ただし、
いずれもE1のendpoint/grid caseではない。Target bankとsource-wrapper bankは使わず、
P2 input、C1 input、科学的outcome inputのいずれにも該当しない。

| ID | UTF-8 promptの正確な内容 | Engineering上のcoverage |
|---|---|---|
| `prompt_00` | `🌒` | mergeが予想される短い絵文字surface |
| `prompt_01` | `🐑` | 3 tokenが予想される短い絵文字surface |
| `prompt_02` | `Mark: 🤑\nAnchor:` | 短いtext wrapperへ埋め込んだ絵文字 |
| `prompt_03` | `Continue briefly: The scientist opened the notebook and` | 中程度の長さのtext surface |
| `prompt_04` | `Write a concise two-sentence explanation of why a careful scientist records every calibration setting before comparing experimental interventions.` | 長いcalibration surface |

`prompt_02`の`\n`は、decode後のstringに含まれる1つのliteral newline byte列を
表す。Validatorは、各promptについてUTF-8 SHA-256、token ID、token数、最後の
nonpadding位置を記録する。両backend間でtoken IDが完全一致することをgateとする。
Failureの確認後にpromptを交換するには、新しいprotocol versionと公開freezeが必要に
なる。

## 固定するintervention

各prompt-layer caseで、width 3,072のfloat32 intervention vectorを2つ使う。

1. 全要素が0のvector
2. RMSが、そのpromptとlayerにおけるTransformers/MPS baselineの`resid_post`
   RMSの5%となる、1つの決定論的direction

次のように定義する。

\[
u_0=\operatorname{linspace}(-0.05,0.05,3072;\ \mathrm{float32}),\qquad
u=u_0-\operatorname{mean}(u_0;\ \mathrm{float32}),\qquad
\hat u=u/\operatorname{RMS}(u).
\]

Prompt `p`、layer `l`の`last_nonpad`におけるTransformers/MPS baseline
activationを`a^T_{p,l}`とすると、非ゼロvectorは次のとおりである。

\[
v_{p,l}=0.05\,\operatorname{RMS}(a^{T}_{p,l})\,\hat u.
\]

Reference stageは、byte単位で同一のfloat32 `v_{p,l}`をintervention planへserialize
し、Transformers/MPS baseline RMS、そこから導出したscale、vector SHA-256を記録
する。MLX stageでは、そのserialize済みvectorをreplayし、注入前にbyte-level
SHA-256を再計算して一致を確認する。MLX baselineからvectorを再構築したり、rescale
したりしてはならない。Receiptには、構築方法、reference activation RMS、導出scale、
vector RMS、width、dtype、各prompt-layer caseのcontent hashを記録する。Backend比較
のreference vectorを1つに保ちながら、E2のrelative-RMS strength contractを反映する
ためである。

## 逐次・process-isolated比較

2つのmodel全体を同時にmemoryへ置いてはならない。Validationは次の固定順で行う。

1. Transformers/MPS processが、固定artifactを読み込み、metadataとtokenizationを
   検証し、baseline、zero-vector、nonzero-vectorの出力をcaptureする。さらに
   reference-scaled vectorを構築し、timing sampleを記録して、staging用の比較
   payloadを書き出した後、終了する。
2. Reference processが終了してmodel stateを解放した後、MLX processが同じ固定
   artifactとrevisionを読み込む。同じinvariantを検証し、同一promptとserialize済み
   float32 vectorをreplayする。注入前にexact hashを確認し、報告対象のBF16 arrayを
   NumPyへexportする直前に`mx.float32`へcastする。出力とtiming sampleを別の
   staging payloadへ書き出した後、終了する。
3. 比較stepは、modelを読み込まずに両staging identityを検証し、固定済みparity
   gateとspeed gateを評価する。

各prompt-layer-backend cellでは、記録しないwarm-up forwardを2回行った後、10回
を計測する。5 promptと2 layerなので、各backendから100 sampleを得る。Forward
timingには、tokenization、capture/intervention、device evaluation、報告対象array
のNumPyへの転送を含める。V2のexport castも、この変更しないtiming境界の内側で
行う。Model load latencyは別に記録し、speed gateには含めない。

このscheduleは意図的に逐次かつnon-interleavedとし、24 GiBのメモリを備えた
machineで約6.4 GBのweight setを2つ同時に保持しなくてよいようにする。Timing比較は
machine-specificであり、温度、memory pressure、phase順序の影響を受ける可能性がある。これは
engineering selection gateであって、一般化可能なMLX性能主張ではない。

## 固定するparity gate

Reference array `x`とcandidate array `y`について、次のように定義する。

\[
\operatorname{NRMSE}(x,y)=
\frac{\sqrt{\operatorname{mean}((y-x)^2)}}
{\max(\operatorname{RMS}(x),10^{-12})}.
\]

Cosine similarityは、flattenしたfloat64 comparison arrayで計算する。RMS ratioは、
cross-backend deltaにおける`MLX RMS / Transformers RMS`を表す。次のcheckは、固定
したすべてのprompt-layer caseで、それぞれ合格しなければならない。Parity failureを
平均で打ち消してはならない。

| Check | 固定criterion |
|---|---|
| Tokenization | token IDの完全一致 |
| Baseline logits | NRMSE <= 0.02、cosine >= 0.999、argmaxの完全一致 |
| Baseline captured activations | 各固定layerでNRMSE <= 0.02、cosine >= 0.999 |
| Changed logits | NRMSE <= 0.02、cosine >= 0.999、argmaxの完全一致 |
| Intervention layerのchanged activation | NRMSE <= 0.02、cosine >= 0.999 |
| Logit delta | NRMSE <= 0.05、cosine >= 0.99、RMS ratio [0.95, 1.05] |
| Activation delta | NRMSE <= 0.02、cosine >= 0.999、RMS ratio [0.98, 1.02] |
| Intervention fidelity（各backendを別々に評価） | 観測activation deltaと指定vectorの比較で、NRMSE <= 0.01、cosine >= 0.999 |
| Zero-vector integrity（各backendを別々に評価） | logitまたはcaptured activationの最大絶対変化 <= 1e-7 |

Baselineとchanged logitsはvocabulary全体で比較する。Validation出力を1つでも確認
した後は、閾値を緩めたり、promptやlayerを除いたりしてはならない。Code defectを
修正する場合も、versionを更新したprotocolと新たに凍結したreceipt destinationを
用いる。既存のfailure evidenceは残し、v1でreceiptが生成されなかったことも明記する。

## 固定するspeed gate

各backendについて、固定prompt × layer行列で計測した100件のforward sampleを
poolし、aggregate distributionを作る。Transformers/MPSとMLXの集約中央値を
`m_T`、`m_M`とすると、speed gateは次のとおりである。

\[
m_M \le 0.95m_T.
\]

Cell別・aggregate別のmedian、mean、minimum、95 percentile latencyに加えて、
sample数とmodel load timeを公開する。このgateの合格が意味するのは、固定した
local E2 cellにMLXを選ぶことだけである。不合格でもparity自体は無効にならないが、
予定する科学的gridについて、v2のMLX engineering qualificationを主張することは
認めない。

## Receipt、identity、no-overwrite rule

最終receipt pathは
`validation/mlx_llama32_3b_bf16_parity_v2/receipt.json`とする。V1のpathとは
分離する。V1ではreceiptが生成されなかったため、v2からv1 destinationへreceiptを
新規作成したり、後から補ったりしてはならない。公開前に、receiptは少なくとも次を
結び付ける。

- protocol IDと固定validation configuration identity
- 正確なmodel名とrevision、固定済み9-file・6,434,705,789-byteのartifact inventory
  とそのmanifest SHA-256、全model file hash、tokenizer identity、両backendが観測
  したstable model identity
- validatorのSHA-256と`src/glyphprobe`全体のimplementation receipt
- Python、dependency、OS、hardware、device、arithmetic metadata
- 固定promptのhashとtoken ID
- layer導出、intervention vectorのmetadataとhash、全閾値、warm-up/repeat数、
  timing method
- prompt-layerごとの全measurement、個別gateの結果、aggregate speedの結果、
  failureまたはdeviation

Validatorは、完成したcandidate receiptをstaging locationへ書き、schemaとidentityを
検証した後、最終pathが存在しない場合に限ってatomic renameする。既存receiptを
truncateまたはoverwriteしてはならない。再実行には、新しいversion付きdestination
を用いるか、以前のimmutable receiptを明示的にarchiveする必要がある。生成receipt
を手作業で編集しない。

合格statusは`validated_mlx_selected`だけであり、完全なparityとspeed gateの両方を
必要とする。それ以外は`validation_failed`とし、このprotocolに基づくE2 scientific
runにはMLXを選ばず、利用可能なfailure evidenceをすべて残す。

## 科学的な境界と今後のE2 handoff

Stage Aではemoji-family endpointを生成せず、研究outcomeも調べない。P2 confirmatory
bankとC1 causal bankに対しては、読み込み、hash、tokenize、model forward、解析の
いずれも行ってはならない。合格receiptが認めるのは、次のE2科学inputと解析を
公開freezeすることだけであり、それ自体は結果主張を認めない。

今後のE2科学freezeでは、E1の元の50絵文字をprimary literal panelとして維持し、
5 familyすべてのslot 03--09を35 glyphのtoken-structural sensitivity panelとして
事前指定する。すでに探索に使った同じ24件のprestage targetと、同じ16件のsource
wrapperを再利用する。P2とC1は未使用のまま保つ。Tokenizer audit、正確なrun
configuration、endpoint、解析code、manifestを、E2科学model forwardより前に
公開freezeしなければならない。

その後のgridが完了しても、E2 cellはE1と比べて、model weight、tokenizer、
vocabulary、architecture、arithmetic dtypeが同時に異なる。したがってmodel scaleを
単独で識別できず、差をこれらの要因のどれか1つへ帰属できず、それ自体でscale
effectを確立することもできない。Stage Aはreplicationではない。今後のE2結果に
認められる上限は、独自の凍結protocolと主張境界の下での、範囲を限定した
cross-model transport observationである。
