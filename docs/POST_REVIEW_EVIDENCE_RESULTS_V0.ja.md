# 査読後の証拠補強結果 v0

[English](POST_REVIEW_EVIDENCE_RESULTS_V0.md) | [診断計画](POST_REVIEW_EVIDENCE_PLAN_V0.ja.md)

2026-09-02、保存済みのT19/T20/T21出力を使って査読指摘に対応した。再計算はLinux側の
CPUで行い、モデル実行・生成・新しい項目の選択・登録済み判定の変更はいずれも0だった。
小さな結果ファイルは原稿側へ転送した後も照合した。使用を終えた二つの歴史的target
bankは開いていない。

## T20: 実際に評価した基底はどれか

全27訓練履歴と9サイトのseed選択を再構成した。50ステップごとにvalidationを測り、
各seed内では最高値を最初に達成した時点を採用する。その後、seed間の最高値を選び、
同点なら小さいseedを採用していた。

| 主要residualサイト | 採用seed | 採用step | 採用反復で記録した損失 | step 600の記録損失 |
| --- | ---: | ---: | ---: | ---: |
| Block 21 | 0 | 350 | 1.234684 | 0.647579 |
| Block 24 | 0 | 50 | 3.884068 | 1.254739 |

これらは更新前のミニバッチsufficiency損失で、基底を保存したのは更新後である。
step 600の損失は訓練経過の診断であり、採用基底を訓練集合全体で測った値ではない。
論文に二段階の選択規則を記述した。両主要サイトの判定は、**元の規則でuncalibratable**
のままである。

証拠: `validation/post_review_evidence_v0/t20_checkpoint_selection.json`。

## T21: マージンの中で何が変わるか

全13 chunkのhashを照合し、元の10種類の指標配列を実験実行側で厳密に再構成した。
keywordとcodepointのtop-1もbit単位で一致した。下の加法的恒等式の項目別最大誤差は
`4.17e-17`だった。

同じbatch位置のneutral参照を引き、項目内で平均した後の元の対比演算Dに対して、

`D(margin) = D(自項目keywordのコサイン) - D(source keywordの最大コサイン)`。

195項目すべて、元のblock 21、距離8の両carrier、指定済みの両donor、元の5対比を保った。

| 対比 | 自項目keyword | 最大競合 | マージン | Donor keyword（診断） |
| --- | ---: | ---: | ---: | ---: |
| 全prefixによる較正 | +0.011980 | +0.003054 | +0.008926 | -0.003177 |
| Glyph低下 | +0.001046 | -0.002376 | +0.003422 | -0.005442 |
| 位置対照との差の低下 | +0.002428 | +0.000103 | +0.002326 | -0.001913 |
| Glyph回復 | +0.008955 | +0.005238 | +0.003717 | +0.003039 |
| 位置対照との差の回復 | +0.004402 | +0.002135 | +0.002267 | +0.000653 |

位置対照との差をとった両対比では、自項目keywordへの正の変化が、最大競合のコサイン
増加によって部分的に相殺されていた。絶対的な低下には、donor注入に伴う競合の増加も
寄与する。したがってマージン単独を「自項目keywordの類似度」と呼ぶべきではない。
Donor keywordはsource galleryに含まれ、そのコサインは加算可能な第三成分ではなく
診断指標である。最大競合となる項目は条件間で変わり得る。

この分解は**事後的・記述的**で、新しい有意差検定や確認判定を追加しない。
既存の同時下限は元のマージンに対するもので、新たに分けた成分には適用しない。
絶対的な低下・回復における元の平均top-1効果0も不変である。
この恒等式は、独立したmediator、完全な回路、絵文字固有性、行動的steeringを示さない。

証拠: `validation/t21_margin_decomposition_v0/` に成分のscalar行、raw状態からの再構成
記録、独立したコンパクトな恒等式検証を保存した。

## T19: モデル不要の再計算とmatched帰無分布

コンパクトな出力には全9構成、両glyph種、両component、全24主要文脈、正確な予測index
と局所stratumを含めた。元のsummaryと予測ファイルを、公開済み独立検証のchecksumと
照合した。別のNumPyのみのプログラムで次を再現した。

- 36のrandomization検定すべて（各19,999回）。
- 36の記述的区間すべて（各20,000回のbootstrap）。
- モデルのintersection--union値、効果量条件、Holm判定。
- 主要4構成の肯定とpartial-conjunction `p = 0.0027`。

公開済み数値との最大差は**0**だった。予測indexのファイルは370,695 bytesで、モデル
資産を必要としない。統計の再計算を支え、隠れ状態そのものの再構成とは区別する。

n項目のgalleryから一様に当て推量する基準は`1/n`である。一方matched randomization
では、予測先が対象項目と同じstratumに属するとき帰無の正答確率は
`1/size(stratum(i))`となり、それ以外は0となる。これを文脈と項目で平均すると条件付き
keyword帰無正答率になる。codepoint項はrandomization中も固定する。Llamaではmatched
keyword帰無正答率は`0.066500`で、一様当て推量の`0.032258`とは異なる。
元の検定は既に正しいstratum内置換を使っていた。

この再計算で、原稿の項目数範囲の誤記も見つけた。Matched emojiはGemmaの51を含む
**31–51項目**で、31–41ではない。予測配列の形状、採用項目、検定自体は正しかった。

| 構成 | Matched emoji数 |
| --- | ---: |
| Qwen2.5 0.5B | 35 |
| OLMo 2 1B | 31 |
| Qwen2.5 1.5B | 35 |
| SmolLM2 1.7B | 41 |
| Gemma 2 2B IT | 51 |
| Llama 3.2 3B | 31 |
| Qwen2.5 3B | 35 |
| Qwen2.5 7B | 35 |
| Mistral 7B Inst. | 38 |

証拠: `validation/t19_lexical_alias_unicode_control_v0/compact_v0/`。

## コンパクトな検証の再実行

Repoまたは展開した匿名artifactのrootで実行する。

```bash
python3 scripts/validate_t19_compact_predictions_v0.py \
  --compact validation/t19_lexical_alias_unicode_control_v0/compact_v0/predictions.json
python3 scripts/validate_t21_margin_decomposition_v0.py \
  --decomposition validation/t21_margin_decomposition_v0/decomposition.json \
  --original validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json
```

既存のT21同時推論の再計算は別途保つ。Raw状態の再構成には、省略された保存配列が必要。
