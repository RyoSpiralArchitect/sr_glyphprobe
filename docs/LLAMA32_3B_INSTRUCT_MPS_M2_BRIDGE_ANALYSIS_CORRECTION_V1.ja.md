# Llama 3.2 3B Instruct M2 bridge analysis correction v1

[English](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_ANALYSIS_CORRECTION_V1.md) · [元のbridge freeze](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.ja.md)

Analysis ID: `glyphprobe-llama32-3b-instruct-mps-m2-bridge-analysis-v1`

## Version付き修正が必要な理由

固定した4本のmodel processはすべて正常終了し、execution receiptはanalysisを
許可した。その後、analysis v0の最初の呼び出しが
`Frozen config differs for primary:capture.layers`でfail-closedした。

停止位置は、最初のpanelの`resolved_config.yaml`検証である。このfileは正しく
normalized depth specification `[0.2, 0.4]`を保持し、実layer `[5, 11]`はrun summaryへ
別に記録される。Analysis v0は、誤って両方の場所に`[5, 11]`を要求していた。

失敗前にanalyzerが到達したのは、公開prestage authority input、panel/wrapper hash、
primary resolved configだけである。Run receipt、run summary、intervention ledgerは開いて
いない。Analysis directoryは作成されず、科学的decisionも割り当てていない。P2と
廃止済みC1にはアクセスしていない。

Analysis v0の再利用や黙った編集は禁止する。この文書とv1 manifestにより、科学的
outcomeを読む前に新しいanalysis versionをfreezeする。

## 唯一の修正

Analysis v1は次だけを変更する。

- 各`resolved_config.yaml`では`[0.2, 0.4]`を検証する。
- 各run summaryでは、引き続き`[5, 11]`を必須とする。

Model run、target slice、panel、score、leave-one-target-group-out prototype、joint
stratified bootstrap、2 endpoint、20,000 replicate、seed、practical threshold、
layer 11のnon-rescuing ruleは変更しない。V1 analyzerはoutcome artifactを開く前に、
commit済みstatic-file manifest、exact execution receipt、cleanな公開`main` worktreeも
検証する。

## Claim boundary

得られるdecisionは、再利用したprestage target 24件上のexploratory bridgeのままである。
Positiveでもnegativeでも、scale curve、tokenizer independence、emoji semantics、causal
localization、generation behavior、独立target generalizationは示さない。Analysis中のmodel
forwardは0回で、confirmatory P2/C1 bankはinputではない。
