# Mistral 7B semantic atlas batch-one v1 結果

[English](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md) · [Protocol](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.ja.md) · [解析計画](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md) · [Evidence](../artifacts/mistral7b_semantic_atlas_batch1_v1/README.ja.md)

状態: **記述結果として完了 — 後期深度glyph/name alignment候補**。確認判定も
意味因果の主張も認めない。

## 取得と失敗した高速経路

Unicode Emoji 17.0 tokenizer censusはfully-qualified単一codepoint 1,184件を固定した。
既出calibration 50件、未使用discovery 842件、決定的な`reserved_unrun` 292件である。
取得したのは前二者だけ。

最初のbatch-64 runは28 shard、一意入力5,352本、84 batched call、保存vector 192,672本を
完了した。しかし事前固定したbatch-one recaptureは18/18 caseで失敗した。最悪の最小
cosineは`0.998244270`、最大relative RMS errorは`0.078983818`、最大absolute element
errorは`2.5`。結果後に閾値を緩めなかった。

Replacement v1は同じ892-item gridをbatch size 1で再取得した。5,352 model call、
192,672本のFP32 vector、28 shardで、shard実行時間の合計は73.524秒。全hash、shape、
finite検査が通過した。独立な固定18-case再取得はbit-exactで、最小exact-element fraction
`1.0`、最大absolute/RMS errorはいずれも`0`。失敗した高速dataとreceiptも保持する。

取得、validation、解析のどこでもreserve forwardは0件だった。

## Discoveryの完全深度profile

各rowはdiscovery 842件について、2 carrier×4距離を等weight平均した値。Top-1 chanceは
`1/842 = 0.001188`。

| Layer | Glyph→name top-1 | Glyph→codepoint top-1 | Glyph/name CKA | Glyph/codepoint CKA | Glyph group purity | Glyph subgroup purity |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.002375 | 0.001930 | 0.011634 | 0.108158 | 0.244908 | 0.064430 |
| 4 | 0.009204 | 0.001336 | 0.073398 | 0.155903 | 0.477524 | 0.188213 |
| 8 | 0.059382 | 0.001188 | 0.135795 | 0.182633 | 0.626262 | 0.280151 |
| 12 | 0.048991 | 0.001336 | 0.142839 | 0.146591 | 0.627999 | 0.282185 |
| 16 | 0.069626 | 0.001336 | 0.147049 | 0.117451 | 0.630686 | 0.291375 |
| 20 | 0.106295 | 0.001039 | 0.141629 | 0.098568 | 0.614415 | 0.290350 |
| 24 | 0.128711 | 0.001188 | 0.146506 | 0.083033 | 0.614133 | 0.296823 |
| 28 | 0.127672 | 0.001633 | 0.159395 | 0.083007 | 0.616033 | 0.297298 |
| 31 | **0.136580** | **0.001188** | **0.206788** | **0.082973** | **0.627197** | **0.309991** |

Layer 31のglyph→name top-1はchanceの約115倍だが、glyph→codepointはchanceに留まる。
逆方向name→glyph top-1は`0.152761`、forward MRRは`0.214288`。GlyphのUnicode group
neighbor purityは`0.627197`、random-pair baselineは`0.131441`。Subgroupは`0.309991`
対`0.016110`だった。Codepoint literalにもlayer 31でgroup構造`0.2975`があるため、category
purityだけは意味controlにならない。Item単位のpaired retrievalの方が鋭いcontrastである。

Layer 31の8つのglyph→name cellは`0.081948`〜`0.201900`で、すべてchanceを大きく上回る。
最良cellを選ばず、carrier×distance全gridを公開する。

## Token構造感度

正確な感度設計はheadlineを見た後なのでpost-outcomeである。Discoveryを、厳密に5 token、
prefix `[29473, 1011, 930]`も共通する760 glyphへ限定した。

| Layer-31 stratum | n | Chance | Glyph→name | Glyph→codepoint | Glyph/name CKA | Glyph/codepoint CKA |
|---|---:|---:|---:|---:|---:|---:|
| 共通prefix 5-token glyph | 760 | 0.001316 | 0.150658 | 0.001151 | 0.201920 | 0.057993 |
| Name token = 1 | 105 | 0.009524 | 0.402381 | 0.008333 | 0.2911 | 0.1193 |
| Name token = 2 | 257 | 0.003891 | 0.267023 | 0.002918 | 0.2570 | 0.0742 |
| Name token = 3 | 213 | 0.004695 | 0.236502 | 0.004695 | 0.2742 | 0.0861 |
| Name token = 4 | 111 | 0.009009 | 0.257883 | 0.013514 | 0.3678 | 0.1160 |
| **Name token = 5（glyph/name長一致）** | **43** | **0.023256** | **0.351744** | **0.031977** | **0.459196** | **0.121558** |
| Codepoint token = 6 | 180 | 0.005556 | 0.159722 | 0.006250 | 0.1495 | 0.1612 |
| Codepoint token = 7 | 573 | 0.001745 | 0.188482 | 0.000873 | 0.2576 | 0.0627 |

したがって大きなretrieval contrastは、glyph長固定、glyph prefix固定、20件以上の全name長
stratumで残った。Glyph/name token数がともに5の43件でも残る。ただし3 viewすべての長さが
等しいdiscovery subsetはなく、token identityも異なるので、完全token-isomorphic controlではない。

## Batch-shape感度

Batch-64はvector-level equivalenceに失敗したが、discovery aggregate profileはbatch-oneに
近かった。9 layer summaryにおける最大絶対差はglyph/name top-1が`0.000742`、
glyph/codepoint top-1が`0.000445`、glyph/name CKAが`0.000260`。これは失敗gateを救済せず、
individual late vectorよりaggregate shapeの感度が低いことを示すだけである。

## 解釈と次のgate

結果は単純なcodepoint identityまたはglyph token長だけの説明を狭める。大きな未使用集合で、
後期residual stateは各glyphを`U+...` literalより正式名へ強く対応させ、そのalignmentは
強いtokenizer層別でも残った。

それでもdisentangleされた意味変数を発見したとは言えない。正式名とemoji categoryは人間の
labelであり、Unicode順序、training co-occurrence、tokenizer identity、相関するlexical featureが
寄与し得る。解析は1 modelの観測だけである。

次の綺麗なstepは具体化した。Calibration/discoveryだけから、完全かつ多重性を限定した
後期深度glyph/name-versus-codepoint retrieval endpointを一つfreezeし、292件のreserveを
一度だけforwardする。それまでは探索候補であり、Phase I gateは閉じない。
