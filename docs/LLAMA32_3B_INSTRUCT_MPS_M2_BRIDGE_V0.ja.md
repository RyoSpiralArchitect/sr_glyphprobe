# Llama 3.2 3B Instruct M2 bridge v0

[English](LLAMA32_3B_INSTRUCT_MPS_M2_BRIDGE_V0.md) · [Milestone 2 protocol](MILESTONE2_PROTOCOL.ja.md) · [Scale option space](SCALE_FALSIFICATION_OPTION_SPACE.ja.md)

Protocol ID: `glyphprobe-llama32-3b-instruct-mps-m2-bridge-v0`

## 状態と問い

現在の状態は`static_freeze_pending_publication`である。Static manifestをcommitして
pushし、その公開commitからzero-forward preflightが通り、さらにpreflight receiptだけを
後続commitとして公開するまでは、このstudyのlanguage-model forwardを許可しない。

この限定的bridgeでは、GPT-2 Milestone 2で観測したcolored-shape優位が、有限なLlama
input inventoryの範囲でtokenizer構造を可能な限り厳密に揃えたとき、固定した1つの
Llama 3.2 3B Instruct Transformers/MPS BF16 cellでも現れるかを問う。これはscale curve
ではない。GPT-2からはmodel lineage、tokenizer、instruction tuning、backend、数値精度が
同時に変わる。

Targetは、すでに探索で使った`prestage_targets`先頭24件である。したがって、最初の
outcomeより前にgridとdecision ruleをfreezeしても、このstudyは探索的である。P2と
廃止済みC1は、実行、preflight、analysisの全input surfaceから除外する。

## Tokenizer情報だけによるcontrol構築

元のGPT-2 control panelは、固定Llama tokenizerへそのまま移せなかった。

- panel Aはrawおよび16件すべてのcontextual wrapper matching checkを通過した。
- panel Bの`🟁`は3 tokenではなく2 tokenだった。
- panel Cの`🟥`も3 tokenではなく2 tokenだった。

Model outcomeを見る前に、次の2つの探索を結果非依存で使い切った。

1. 固定symbol range内の3,264 scalarを、category、Unicode name、round-trip、3-token、
   `[9468,253]` prefixでfilterした探索。
2. `[9468,253]`の後ろにbase vocabularyの128,000 final-token IDをすべて昇順に補い、
   1 emoji graphemeかつexact re-encodingに限定した探索。

どちらにも未使用候補は0件だった。そのため、元のcompatible poolにはdominant-prefix
glyphが25種類しかなく、必要な27 slotを完全disjointに埋めることはできない。
Pigeonhole principleにより、最低2 placementの再利用が不可避である。

v2 constructionは、固定したcyclic donor ruleでこの下限を達成した。

- panel Aから、compatible scalarの最小値`🟀`（`U+1F7C0`）をpanel Bへ貸す。
- panel Bから、compatible scalarの最小値`🟄`（`U+1F7C4`）をpanel Cへ貸す。

最終的なpairwise overlapはA–B = 1、A–C = 0、B–C = 1である。3 panelはいずれも、
item数、rawの3-token/prefix histogram、16 wrapperすべてのfull structural histogramで
colored-shape panelと一致する。ただし3つの独立panelではない。解釈ではこの依存を
必ず保持する。

## 固定modelとruntime

| Field | Frozen value |
|---|---|
| Model | `meta-llama/Llama-3.2-3B-Instruct` |
| Revision | `0cb88a4f764b7a12671c53f0838cd831a0843b95` |
| Artifact | 8 files、6,434,691,515 bytes、manifest `c698f962…ecf6` |
| Architecture | 28 layers、width 3072、3,212,749,824 parameters |
| Backend | raw Transformers on MPS |
| Runtime dtype | BF16 |
| Network | Hugging Face / Transformers offline |
| Runtime alias | `/private/tmp/glyphprobe-llama32-3b-instruct-v0` |

Launcherはpath-independentなartifact manifest全体を検証した後にだけ、user名を含まない
固定aliasをsymlinkとして作る。実際の保存pathはreceiptに記録しない。同一artifactの
synthetic screenでは、この3B checkpointに対してMPSがMLXより速かったが、
intervention-delta parityは完全ではなかった。そのため本studyはMPSを使うが、backendや
速度に関する主張はしない。

実行中もChatGPT、Codex、WindowServerは動作してよい。これはlatencyや失敗riskを変え得るが、
事前指定したestimandは変えない。このrunのtiming値をperformance claimへ使ってはならない。

## 固定した4-panel grid

中間outcomeを見ず、次の順序で4 processを実行する。

1. colored-shape primary panel
2. minimum-overlap null A
3. minimum-overlap null B
4. minimum-overlap null C

各processは共通して次を使う。

- source wrapper 16件すべてと、探索済みprestage target先頭24件。6 groupから各4件。
- normalized depth `0.20`と`0.40`。28-layer modelではlayer 5と11に解決される。
- `resid_post`、`last_nonpad`、RMS正規化strength `0.05`。
- direction seed 101、211、307。seedはtarget内で平均する。
- layerごとにrandom direction 8本とexact zero-hook control。
- sign flip、neutral direction、label shuffle、SAE、iso-KL、generationは無効。
- seed 8675309の96-dimensional CountSketch fingerprint。

各runは逐次・独立processである。Resumeは禁止する。失敗または中断時はfailure receiptを
公開し、選択的rerunをせずv0を廃止する。

## Freeze済み探索endpoint

Panel、layer、target、seedごとに、Milestone 2と同じleave-one-target-group-out
condition-identification scoreを使う。Bootstrapの各replicateは、6 groupのそれぞれで
target 4件をreplacementありで共同resampleし、他の5 groupからpanel/condition prototypeを
すべて再構築する。Direction seedは独立観測ではなくnested estimateである。

Layer 5では次の2 endpointを必須とする。

```text
D_ensemble[t] = S_primary[t] - median(S_A[t], S_B[t], S_C[t])
D_A[t]        = S_primary[t] - S_A[t]
```

`D_A`は完全disjointなpanel Aだけを使う感度解析である。Layer 5で、両方のtwo-sided 95%
percentile bootstrap下限が、既存Milestone 2のpractical threshold `delta = 0.06`を厳密に
上回った場合にだけ、primary exploratory statusを
`exploratory_bridge_pattern_observed`とする。Bootstrapは20,000 replicate、seed 20260828。

Layer 11は事前指定したsecondary comparatorであり、layer 5を救済できない。Random-control
run summary、target-group description、個別glyph、その他すべてはsecondaryである。
p-value、多重性調整済みstatus、equivalence status、confirmatory labelは出さない。

## Claim boundaryと落とし所

Primary statusがpositiveでも、許される最強の表現は次に限る。

> 事前にfreezeした1つのLlama 3.2 3B Instruct Transformers/MPS BF16 cellにおいて、
> 24件の再利用探索target上で、colored-shapeのtarget-identification scoreが、
> minimum-overlap tokenizer-matched ensembleと完全disjointなpanel-A感度解析の両方を上回った。

Criterionを通らなければ、tested estimandにおけるcleanなnegative bridgeである。Layer 11だけの
effectも、layer 11がnon-rescuingなのでnegativeとして扱う。

どちらの結果も、monotonic scaling、tokenizer independence、emoji semantics、内部circuit、
causal localization、generation behavior、独立target generalizationを示さない。Null panel間の
2 overlapは常に明記する。

## 公開と実行の順序

1. このprotocol、日本語pair、configs、panels、scripts、tests、negative-search receipts、
   static manifestをcommitしてpushする。
2. mac1のcleanなisolated worktreeでzero-model-forward preflightを実行する。
3. Receiptをhash検証して回収し、post-freeze唯一のfileとしてcommitし、再度pushする。
4. Isolated worktreeをその公開commitへ更新し、中間outcomeを読まず4 cellを順次実行する。
5. Execution receiptが許可した後にだけ、freeze済みanalyzerを一度実行する。
