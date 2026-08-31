# T16 後期分散bandの結果

[English](T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.md) · [固定済みプロトコル](T16_DISTRIBUTED_LATE_BAND_V0.ja.md) · [closeout](../validation/t16_distributed_late_band_v0/closeout.json)

## 結果の要約

事前に固定した後期8成分bandは、joint mediation gateを通過しなかった。
Llama 3.2 3Bで、block 24〜27の`attn_out`と`mlp_out`をtreatment時の値から
baseline時の値へ戻すと、T14 treatment効果のうち実用上無視できない正の成分が失われた。
ところが、同じ8成分を未介入runへ移植しても効果は再現しなかった。Treatment自体も、
固定した実用下限に届いていない。したがって、この実験が示すのは、移植条件では
十分でないnecessity成分である。局在した絵文字回路や完全な回路ではない。

## 固定済みjoint test

| IUT成分 | Target中央値 | 95%区間 | 実用下限 | 片側p値 | 判定 |
|---|---:|:---:|---:|---:|---|
| treatment | 0.001716701 | [0.001476628, 0.001895659] | 0.002000000 | 0.000010 | 下限未達 |
| necessity | 0.000870887 | [0.000754687, 0.001012641] | 0.000500000 | 0.000010 | 通過 |
| sufficiency | -0.000146485 | [-0.000183541, -0.000091606] | 0.000500000 | 1.000000 | 不通過 |

Intersection-union判定は`joint_late_band_iut_non_rejecting`である。
Necessity成分が正でも、不通過だったsufficiencyとtreatmentを補うことはできない。

## 実行と対照

- モデルはLlama 3.2 3B。T14介入は`resid_post` block 23に加えた。
- Joint bandはblock 24、25、26、27の`attn_out`と`mlp_out`、計8成分。
- 新しいtarget bankは12層、192行。拘束済みの旧bankとの完全一致promptは0件。
- 応答は15,360行。
- Explicit zeroの最大JSは`0`。
- 復元時の最大JS誤差とlogit RMS誤差は、どちらも`0`。
- 拘束済みT14 upstream shamは通過。

Band全体を結果確認前に固定している。結果を見てからmoduleを順位づけしたり、外したり、
選び直したりしていない。

## 解釈

後期bandは、T14効果の伝播に必要な情報を運んでいる可能性がある。Baseline時の値へ戻すと、
treatmentが弱まったためである。しかし、未介入の軌道へ移しただけでは効果を再現できず、
より強い意味での自律的な媒介経路とは言えない。Band外の分散状態、より早い残差状態との
経路依存な相互作用、または固定した実用下限より小さいendpoint効果が候補として残る。
いずれも次の仮説であり、このbankから得た結論ではない。

## 主張の境界

個別成分の必要性、最小band、固有経路、完全な回路、絵文字の意味、生成挙動、
tokenizer非依存性、モデル一般性は示していない。同じbankを使ったsubset探索は、
結果を見た後の救済になるため行わない。

## エビデンス

- [Compact analysis](../validation/t16_distributed_late_band_v0/results/analysis.json)、SHA-256 `4f7687feae462efd91845b0c58b80a596134e3dc5cfcf7ee9936a0b5e85f666f`
- [Closeout](../validation/t16_distributed_late_band_v0/closeout.json)：target bankとrun receiptのhashを収録

生のledgerは記録済みの炉上scratch rootに残しており、Gitにはコピーしていない。
