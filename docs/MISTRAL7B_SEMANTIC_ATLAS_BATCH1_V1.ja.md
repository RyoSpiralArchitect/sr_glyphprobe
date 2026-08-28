# Mistral 7B semantic atlas batch-one v1

[English](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md) · [元の取得](MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md) · [解析計画](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md)

状態: **replacement取得をprospectiveにfreezeし、batch-one v1 forwardは0**。

元のbatch-64 atlasは28 shardを完了したが、独立に固定したbatch-one recapture validationは
18/18 caseで不合格だった。最悪caseは最小vector cosine `0.998244270`、relative RMS error
`0.078983818`、最大absolute error `2.5`で、閾値`0.999999`、`0.001`、`0.125`を満たさない。
後期residual stateで無視できないBF16 batch-shape数値感度があることと整合する。結果を見た後に
閾値を緩めて修復してはいけない。

そこでv1は、同じ取得済み892 item、3 view、2 carrier、融合した4 causal距離、9 layer、
FP32 export、source順、28 item shardをbatch size 1でそのまま繰り返す。科学inputは変えず、
model callは5,352回。Batch-64 dataと失敗receiptは数値感度artifactとして保持し、黙って
置換しない。

その後、同じ固定acquisition index `[0, 445, 891]`、全view、両carrierをbatch oneで
独立に再取得し、同じ18-case閾値で検証する。18/18が通過して初めて、v1を既に固定した
記述analyzerのcanonical inputにできる。

292件のreserveはforward 0のまま。V1はengineering repairであり、新しい意味endpoint、
独立確認、paper gateの結果ではない。
