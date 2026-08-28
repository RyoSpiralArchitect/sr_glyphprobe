# Mistral 7B semantic atlas reserve確認 v0 結果

[English](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md) · [固定protocol](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md) · [Evidence](../artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0/README.ja.md)

状態: **固定した判定規則の下で確認**。

Outcome: `transport_robust_late_depth_glyph_name_alignment_confirmed`。

これにより、T8で設定した単一のreserve questionは閉じた。ただし、人間が解釈する絵文字の意味、因果mechanism、
tokenization非依存性、behavior、model一般性は確立しない。

## Prospective境界と取得

Endpoint、全population、randomization seed、実用下限、positive/negative ruleは、reserveへの
model forward前にfreeze commit `952b89d`へ固定した。Freeze manifestのSHA-256は
`a678213ad79f3fced9c6cffe502b38e16b49a517cdf9d18ba75ef855a8efcc58`である。

決定論的に選定したreserve 292件すべてを、protocolのcanonical batch-one経路で一度だけ取得した。
Model callは1,752回、layer 31のFP32 vectorは7,008本、完了shardは10個。Partial shard、
intervention、generation、item置換、結果後のcell選択はいずれも0だった。

## 固定primary result

Primary statisticは、2 carrier×4距離の全cellにおける次のcontrastの最小値だった。

`glyph→Unicode正式名 top-1 - glyph→U+codepoint top-1`

観測最小値は**`0.171233`**で、固定した実用下限`0.02`を上回った。等cell平均contrastは
`0.232021`。共通permutation null 19,999回のうち、観測最小統計以上は0回だった。
したがって事前指定p-valueは**`(1 + 0) / 20,000 = 0.00005`**。Positive ruleの2条件を
ともに通過した。

292-item target poolにおけるtop-1 chanceは`1/292 = 0.003425`である。

| Carrier | Distance | Glyph→name top-1 | Glyph→codepoint top-1 | Primary contrast | Glyph/name CKA | Glyph/codepoint CKA | CKA contrast |
|---|---:|---:|---:|---:|---:|---:|---:|
| `article_a` | 1 | 0.325342 | 0.003425 | 0.321918 | 0.402636 | 0.140630 | 0.262006 |
| `article_a` | 2 | 0.294521 | 0.010274 | 0.284247 | 0.303822 | 0.116169 | 0.187653 |
| `article_a` | 4 | 0.229452 | 0.000000 | 0.229452 | 0.234156 | 0.133755 | 0.100402 |
| `article_a` | 8 | 0.222603 | 0.000000 | 0.222603 | 0.136162 | 0.143844 | -0.007682 |
| `pipe` | 1 | 0.191781 | 0.003425 | 0.188356 | 0.292647 | 0.096938 | 0.195709 |
| `pipe` | 2 | 0.178082 | 0.006849 | **0.171233** | 0.245628 | 0.070903 | 0.174725 |
| `pipe` | 4 | 0.212329 | 0.003425 | 0.208904 | 0.263791 | 0.074354 | 0.189437 |
| `pipe` | 8 | 0.229452 | 0.000000 | 0.229452 | 0.235708 | 0.075553 | 0.160155 |

8つのprimary retrieval contrastはすべて実用下限を上回った。正式名top-1は`0.178082`〜
`0.325342`、codepoint top-1は`0`〜`0.010274`だった。

## 再現関係とsecondary境界

Discoveryの最小contrastは`0.080760`、等cell平均は`0.135392`だった。未使用reserveは、方向と
完全gridでの頑健性を減衰なく再現した。ただしreserveの数値がより大きいことを、発達trendや
別のeffectとは解釈しない。Discoveryとreserveは、決定論的に選定した異なるitem集合だからである。

Primary resultはitem-level retrievalに限定される。Centered linear CKAは8 cell中7 cellで
glyph/nameが高かったが、`article_a`・距離8のcontrastは`-0.007682`だった。CKAはsecondaryで、
判定を左右しない。この不均一性により主張境界が明確になる。支持されたclaimはtransport cellをまたぐ
正しいitem-name対応であって、すべてのglobal geometry metricの一様な優位ではない。

## 閉じたclaimと次のstep

T8は今後、prospectiveに確認されたmodel固有の後期深度glyph/name alignment結果と記述できる。
`confirmatory_status`と`t8_reserve_question_closed`はともにtrueである。

一方、意味因果、因果局在化、tokenizer非依存性、behavioral relevance、model一般性はfalseの
まま。T8単独でPhase I全体のgateが閉じたとはしない。

次の研究laneはclaim-matchedなmodel横断再現である。その再現を固定・記録した後で、変則glyph systemと
representation shiftの探索modeへ戻る。
