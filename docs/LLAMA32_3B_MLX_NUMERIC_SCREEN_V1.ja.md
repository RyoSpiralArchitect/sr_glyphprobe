# E2 Stage A3 プロトコル：Llama 3.2 3B MLX runtime dtype 数値screen v1

[English](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) · [Stage A v2結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [Stage A v2プロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md)

Protocol ID: `glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`

## 状態と目的

公開freeze前の有効statusは`freeze_pending`、formal screenのstatusは`not_run`である。
英日protocol、実装、test、input identity、候補定義、選定規則、receipt schema、
no-overwriteの出力先を同じ公開commitで拘束するまで、model forwardを認めない。

公開後はprotocol statusを
`frozen_by_public_commit_containing_protocol_implementation_and_tests`とし、
version付きの出力先へ1回だけscreenを実行できる。

Stage A3は、engineering用途だけの候補screenである。`float16`と`float32`の
実行時演算dtypeについて、各backend内の数値忠実度を検査する。同時に、固定した
ローカルworkloadでMLXがTransformers/MPSより速いかを測る。Receiptの
`selection.selected_runtime_dtype`は`float16`、`float32`、`null`のいずれかとし、
選定理由は`selection.decision`へ記録する。

候補を1つ選定できた場合、別のfull v3 parity validatorを設計し、公開freezeする
段階へ進める。ただし、選定だけではMLXの適格性を認めない。E2科学gridも許可せず、
既存のvalidation結果も変更しない。

## V2の不合格判定は変えない

凍結済みStage A v2は、引き続き`status: validation_failed`、
`scientific_result: false`である。Parityは33 / 60、速度gateも不合格だった。
Stage A3によって、この結果を再検査、再採点、再分類しない。Native BF16実行は、
Stage A3の候補でもfallbackでもない。

詳しくは [v2の全結果](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md)、
[凍結済みv2プロトコル](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md)、
[v2レシート](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json) を参照する。

V2後に行った未凍結の非公式diagnosticは、backend内の介入忠実度が不合格となった
原因について、両backendで小さなBF16加算が丸められた可能性を示唆した。Hookが
介入を適用しなかった不具合とは異なるpatternだった。ただし、これは候補設計の
手掛かりにすぎない。凍結済みprotocolから得た結果ではなく、hook defectが存在しない
ことの証明でもない。Dtypeを選定せず、科学的な結果にもならない。Stage A3の
公開freeze前に得たFP16・FP32の部分的なdiagnostic値も、formal screenの結果から
除外する。

## 固定する候補

2つの候補は、同じBF16 weight artifactから開始する。異なるのは、
Transformers/MPSとMLXの両方へ明示する実行時演算dtypeだけである。

| Candidate ID | 保存weight artifact | Transformersの実行時演算 | MLXの実行時演算 |
|---|---|---|---|
| `float16` | 固定BF16 artifact | FP16 | FP16 |
| `float32` | 固定BF16 artifact | FP32 | FP32 |

Artifactは`mlx-community/Llama-3.2-3B-bf16`、immutable revisionは
`60a99aaf43164077157d64bf909b7b61143c6a6d`である。固定済みinventoryは9 file、
6,434,705,789 bytesで、manifest SHA-256は
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`である。

各backendは、このartifactを読み込み、最初の有効なforwardより前に候補dtypeを
明示的に適用する。Loaderが解決したdtypeと、model parameterのdtype別element数を
記録する。`auto`、混合dtypeへのfallback、量子化、別artifact、parameterのBF16残留を
認めない。
総parameter数は、両backendで3,212,749,824に一致しなければならない。Model
parameterは、すべて候補dtypeへ解決する。Receiptにはloader引数だけでなく、
実際のdtype別parameter数と総parameter数を記録する。RoPEの補助arrayなど、parameter
ではないbufferは、このdtype gateの監査・主張対象に含めない。そのこと自体をreceiptへ
明記する。

期待するarchitectureは、decoder 28層、hidden width 3,072、vocabulary size
128,256である。Base modelを用い、chat templateもsystem promptも使わない。
Tokenizationは`add_special_tokens: false`とする。Captureと介入は、zero-basedの
layer 5・11にある`last_nonpad`の`resid_post`へ固定する。

## 固定engineering input

Stage A3は、v2と同じ5つのengineering promptだけを使う。

| ID | 正確なUTF-8 prompt |
|---|---|
| `prompt_00` | `🌒` |
| `prompt_01` | `🐑` |
| `prompt_02` | `Mark: 🤑\nAnchor:` |
| `prompt_03` | `Continue briefly: The scientist opened the notebook and` |
| `prompt_04` | `Write a concise two-sentence explanation of why a careful scientist records every calibration setting before comparing experimental interventions.` |

`prompt_02`の`\n`は、decode後のstringに含まれる1つの改行を表す。実装では、各promptの
UTF-8 byte列とSHA-256、token ID、token数、last-nonpadding positionを固定して
記録する。公開freeze後は、prompt、byte、tokenizer設定、position、layerを変更できない。

Candidateごとのmatrixは、5 promptとlayer 5・11を組み合わせた10 cellである。

## Candidateごとに固定する介入

各candidateは、v2と同じ決定的directionと5%-RMSの構築方法を使う。ただしscaleは、
そのcandidateのTransformers/MPS baselineから導出する。`c`を`float16`または
`float32`、`a^{T,c}_{p,l}`をprompt `p`・layer `l`におけるcandidate `c`のreference
baseline activationとする。

\[
u_0=\operatorname{linspace}(-0.05,0.05,3072;\ \mathrm{float32}),\qquad
u=u_0-\operatorname{mean}(u_0;\ \mathrm{float32}),\qquad
\hat u=u/\operatorname{RMS}(u),
\]

\[
v^{c}_{p,l}=0.05\,\operatorname{RMS}(a^{T,c}_{p,l})\,\hat u.
\]

Transformers/MPSはcandidateとcellごとに、all-zero vectorと`v^{c}_{p,l}`のfloat32
byte列をserializeする。MLXはそのbyte列をそのままreplayし、注入前にSHA-256を
照合する。MLX側のbaselineからvectorを再構築、rescale、置換してはならない。
Receiptには、構築方法、reference RMS、scale、vector RMS、width、dtype、hashを
全candidate cellについて記録する。

観測activation deltaは、介入layerの`last_nonpad`で取得し、共通の比較表現へexport
した後に測る。各backendの忠実度は、指定vectorをreferenceとして別々に評価する。

## Process隔離とtiming

Candidate順は`float16`、`float32`に固定する。各candidateでは、Transformers/MPSを
先に実行し、そのprocessが終了してからMLXをloadする。2つのfull modelを同時に
memoryへ置かず、candidate間でmodel instanceを再利用しない。

各candidateについて、次の順で進める。

1. Transformers/MPS processがartifactとarchitectureのidentityを検証し、5 promptを
   tokenizeする。固定した決定性とzero-vectorの検査を行い、candidate固有vector 10件を構築する。
   Fidelityとtimingを測り、staged payloadを書いて終了する。
2. MLX processが同じidentityを独立に検証する。固定tokenとvectorをreplayし、同じ
   決定性・zero-vector・fidelity検査とtiming測定を行う。Staged payloadを書いて終了する。
3. Modelをloadしないcomparison stepが2つのpayloadを検証し、固定したeligibilityと
   selection ruleを適用して、最終receiptを構築する。

Prompt-layer-backend cellごとに、記録しないwarm-up forwardを2回、計測forwardを
10回行う。Candidateごとに、各backendで100回を計測する。Timing境界はv2と同じで、
tokenization、capture/intervention、device evaluation、synchronization、報告対象arrayの
NumPy transferを含む。Model loadは別に記録し、速度gateから除外する。

この逐次・非interleave benchmarkは、マシン、software、負荷、温度、実行順に依存する。
MLXとMPSの一般的な性能比較ではない。

## Candidate eligibility gate

`float16`と`float32`のeligibilityは別々に判定する。各candidateの10 cellすべてで、
全gateを通過しなければならない。失敗したcellを平均で打ち消さない。

運用上の前提条件もfail-closedとする。Artifactとarchitectureのidentityが完全に一致し、
両worker phaseが完了して記録され、必要なarrayとmetricがすべてfiniteでなければならない。
未申告のdtypeやfallback経路を検出した場合も不適格とする。

| Gate | 凍結済み基準 |
|---|---|
| Runtime dtype・parameter audit | loader resolved dtypeがcandidateと一致すること。各backendのparameter総数が正確に3,212,749,824であり、model parameterがすべてcandidate dtypeへ解決し、記録したdtype別countがloaded modelと一致すること |
| Prompt・token identity | backend間でprompt SHA-256、UTF-8 byte列、byte数、last-nonpadding positionが一致し、token IDが完全一致すること |
| Backend内の決定性 | 各backendで、反復token IDとargmax outputが完全一致すること |
| Zero-vector integrity | 各backendで、activation・logitの最大絶対変化が1e-7以下であること |
| Transformers/MPS介入忠実度 | 観測activation deltaと指定vectorのNRMSE <= 0.01、cosine >= 0.999 |
| MLX介入忠実度 | 観測activation deltaと指定vectorのNRMSE <= 0.01、cosine >= 0.999 |
| マシンローカル速度 | MLX aggregate median latency <= candidateのTransformers/MPS aggregate median latencyの0.95倍 |

観測activation deltaを`d`、指定vectorを`v`とすると、fidelity NRMSEは次式で計算する。

\[
\operatorname{NRMSE}(v,d)=
\frac{\sqrt{\operatorname{mean}((d-v)^2)}}
{\max(\operatorname{RMS}(v),10^{-12})}.
\]

Cosineは、flattenしたfloat64 comparison arrayで計算する。速度gateは、candidateと
backendごとに100件の計測sampleをpoolする。`m_{T,c}`と`m_{M,c}`を、それぞれ
Transformers/MPSとMLXのaggregate medianとすると、candidate `c`の合格条件は次のとおり。

\[
m_{M,c}\leq0.95m_{T,c}.
\]

Receiptには、各backendで反復したlogitの最大絶対差も記録する。ただし、この値は
diagnosticであり、Stage A3のgateではない。Backend間のbaseline、changed output、
activation delta、logit deltaのparity gateは実行しない。これらは、別に凍結するfull v3
validatorまで未実施のまま残す。Fidelityから推定したり、結果を見た後でStage A3の
selectionへ追加したりしてはならない。

## 固定selection rule

`E16`と`E32`を、上記の全gateを適用した後のeligibilityとする。

1. どちらもeligibleでなければ、`selection.selected_runtime_dtype: null`、
   `selection.decision: no_go_no_eligible_numeric_candidate`とする。
2. 片方だけeligibleなら、そのcandidateを選ぶ。
3. 両方eligibleなら、MLX aggregate median latencyを比較する。
   - 相対差`abs(m_M,16 - m_M,32) / min(m_M,16, m_M,32)`が0.01以下なら、
     `float32`を選ぶ。
   - それ以外は、MLX aggregate medianが小さいcandidateを選ぶ。

実装で固定する`selection.decision`は、次の4種類である。

- `no_go_no_eligible_numeric_candidate`
- `single_eligible_candidate`
- `both_eligible_tie_select_fp32`
- `both_eligible_select_lower_mlx_median`

Eligible candidateなしの判定は、完了した正規のengineering-screen outcomeである。
Execution errorではなく、
そのまま公開できる。Worker error、non-finite value、identity mismatch、未申告dtypeは、
該当candidateを不適格にする。Input変更や自動rerunの許可にはならない。

## Fallbackと閾値調整を認めない

Worker、candidate、screen、後続v3 validationのいずれにもcandidate間fallbackを
設けない。具体的には、次の操作を禁止する。

- `float16`から`float32`へretryすること、またはその逆
- BF16、`auto`、CPU、別model artifact、別prompt、別layerへfallbackすること
- 選定candidateが後続の凍結済みv3 validatorに失敗した際、もう一方のStage A3
  candidateを自動昇格すること
- Protocolや実装を変更した後、同じversionやreceipt destinationで再試行すること

Formal outputを確認した後で、閾値を緩和したり、candidateに有利な丸め方へ変えたり、
再調整したりはしない。非公式diagnosticをformal receiptへ昇格せず、失敗cellも
削除しない。変更が必要なら、新version・公開freeze・新しいreceipt destinationを用意する。

## Receipt、schema、atomic publication

最終receiptは、次の1 fileだけとする。

`validation/mlx_llama32_3b_numeric_screen_v1/receipt.json`

このreceiptは、2 candidateの記録と決定的selectionをまとめて保持する。凍結する
minimum contractは次のとおり。

- `schema_version: 1`
- `protocol_id: glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`
- 2 candidateの試行とmodel-free selectionを記録した後の
  `status: engineering_screen_complete`
- `scientific_result: false`
- `selection_is_not_scientific_authorization: true`
- `selection.selected_runtime_dtype: null | float16 | float32`と、実装で固定した
  `selection.decision`のreason code
- Candidateごとの`eligible`、resolved runtime dtype、artifact・implementation identity、
  backend・dtype・return code・wall timeとworker failureを含むcandidate別`process_lifecycle`
- Candidateごとの全10 `benchmark.cells`、各backendのraw `samples_ms` 10件とsummary、
  exact gate、fidelity metric、prompt UTF-8 hex・byte数、last-nonpadding position、
  failure evidence
- Validator SHA-256、`src/glyphprobe`全体のsource receipt、依存関係とmachine environment、
  固定inputとhash、閾値、timing境界、process順、data-scope宣言

実装は、完成したreceiptを最終pathと同じdirectoryのtemporary fileへserializeしてflushする。
最終pathが存在しない場合に限り、no-overwrite linkでatomicにpublishする。既存receiptの
truncate、置換、merge、overwriteを拒否する。生成済みreceiptは手で編集しない。Candidate workerの失敗は、
orchestratorが固定selectionを完了できる限りcombined receiptへ記録する。Atomic publication
より前にorchestratorが失敗した場合、最終receiptは残さず、いかなる結論も認めない。

Validator pathは`scripts/diagnose_mlx_llama32_3b_numeric_cells_v1.py`である。公開freezeは、
Git history、validator SHA-256、source receipt全体、埋め込みvalidation configのhashを使い、
このfileとtestを英日protocolへ結び付ける。Formal commandは次のとおり。

```bash
python scripts/diagnose_mlx_llama32_3b_numeric_cells_v1.py \
  --output validation/mlx_llama32_3b_numeric_screen_v1/receipt.json
```

実装が別のprotocol ID、candidate ID、field、final path、commandを使う場合、formal forward
より前に英日protocolを更新し、改めて公開freezeする。実行時に文書と実装が食い違っては
ならない。

## Data隔離と主張境界

Stage A3がアクセスできるのは、固定model artifact、tokenizer file、上記5 engineering
prompt、実装・runtime metadataだけである。P2、C1、prestage target、source-wrapper bank、
E1科学grid、その他のstudy bankや科学的outcomeを、read、list、hash、tokenize、score、
model-forward、analysisの対象にしてはならない。

このscreenから、絵文字family、意味、因果、回路、cross-model replication、model scale比較、
論文gateの結果は得られない。3つのengineering promptに含まれる公開glyphは、tokenizerと
adapter surfaceを動かすためだけに使う。

認める主張の上限は、次のとおり。

> 公開freezeした1件のマシンローカルengineering screenにおいて、選定したruntime dtypeが、
> 固定済みのbackend内fidelity、exactness、速度基準を満たした。または、どのcandidateも
> 基準を満たさなかった。

この記述にもatomic receiptが必要である。Receiptの公開前に言えるのは、公開commitの
状態に応じて、screenが凍結済みまたはpendingであることだけに限る。

## Formal v3 validationへのhandoff

`float16`または`float32`を選定できた場合、そのcandidateだけを対象とするfull v3
backend-parity validatorを準備し、公開freezeできる。V3 protocolでは、baseline、
changed output、activation delta、logit delta、zero、fidelity、identity、determinism、
speedの全gateを独立に凍結して評価する。

Stage A3 receiptは、v3 parity receiptを代替しない。科学的activation介入もE2 gridも
許可しない。科学実験へ進むには、formal v3 receiptの合格に加えて、E2の科学input、
endpoint、analysis、claim boundaryを別の公開freezeへ固定する必要がある。
`selection.selected_runtime_dtype: null`なら、このscreenはv3 candidateを作らず終了する。
