# 事前因果段階のメトリク・マップ

[English](METRICS.md)

GlyphProbe では、介入の大きさ、出力分布の変位量、fingerprint の方向を分けて扱う。
どの単一指標も、意味や因果性のスコアではない。

## トークン化とソースの整合

`tokenization.jsonl` は、各 glyph の code point、UTF-8 byte、生の token ID、固定済み wrapper ごとの
正確な token ID と個数を記録する。readiness は、primary panel の生 glyph の token 数と、wrapper ごの
合計 token 数の一致を別々に確認する。個数が同じでも同値な tokenization とは限らないため、
全 token ID を証拠に残す。

## ソース表現

`source_item_metrics.jsonl` は glyph ごとの activation RMS、wrapper 間のばらつき、方向 replicate の整合度を
記録する。`source_layer_metrics.jsonl` は、pairwise cosine geometry、effective rank、バランスされた
color × shape 分解、対応する circle-minus-square の平行性を記録する。

source seed は wrapper subset から得た反復推定である。独立した target 観測ではないため、
有意性の主張で独立サンプルとして数えない。

## 介入 fidelity と scalar balance

各 condition は、指定 strength、実現した摂動 RMS、target RMS に対する比、clip scale、clip hit、
実際の activation 差分、意図した方向と実際の方向の cosine、介入後 activation cosine を保存する。
明示的な zero-vector condition により、hook 自体が activation と logits のいずれも変えないことを確認する。

`scalar_balance_summary.jsonl` は、これらを emoji、generic-emoji、random direction に分けて集計する。
さらに output KL と logit-delta magnitude のばらつきも記録する。内部 RMS が等しいことは、下流の変位量が
等しいことを意味しない。iso-KL は、実際に有効化され、許容誤差内に収まった場合だけ用いる。

## 分布変位

次 token 分布の各比較には、forward/reverse KL、Jensen–Shannon divergence、total variation、
Hellinger distance、entropy change、logit-delta norm、ranking overlap、argmax movement、margin、正負の上位 token ID が
含まれる。これらが記述するのは変位であり、意味ではない。

## Fingerprint

全 logit delta を固定 seed で CountSketch し、単位長さに正規化する。そのため fingerprint 統計は主に
方向を比較する。scalar displacement は別のメトリクに残す。

`fingerprint_summary.jsonl` は、決定論的な held-out half、反復する group-stratified half-split、
target 内の label permutation、random-direction separation、output-space の color × shape 分解を含む。

`cross_seed_fingerprint_summary.jsonl` は、別々に推定した source direction 間で同じ glyph を比較する。
random label は seed ごとに再生成し、cross-seed null とする。最大のセルや中央値だけでなく、セル全体の分布と
cluster 化された target 構造を報告する。有限回の permutation で得た p 値はスクリーニング指標であり、
permutation 回数で下限が決まる。多重性補正済みの global test ではない。

## 局所線形性と dose

`sign_flip_summary.jsonl` は正負の介入を比較する。完全な局所奇対称性では、fingerprint cosine は
`-1` に近づき、antisymmetry は `1` に近づく。

`dose_response_summary.jsonl` は KL、total variation、logit-delta RMS について、隣接 dose 間の非減少率と
最後と最初の差を記録する。テストした dose での単調性は局所的証拠にすぎず、グリッド外の線形性を
保証しない。

## バックエンドのパリティと速度

MLX validator は、正確な token ID、baseline/介入後の logits と `resid_post` activation、zero-hook 差分、
介入 fidelity、argmax 一致、logit/activation 差分の normalized RMSE、cosine、RMS ratio を比較する。
差分の magnitude gate により、方向は合っているが大きさが間違っている介入を不合格にできる。

speed gate では、固定済みの prompt length × layer 行列に対し、同期させた end-to-end `backend.forward` を
交互に実行する。tokenization、capture/介入、device evaluation、NumPy transfer を含む。これは 1 台のマシン上の
バックエンド選択指標であり、一般的な throughput benchmark ではない。

## 任意の SAE map

明示的に設定した場合、baseline/介入後 activation を対応付けた SAELens SAE で encode/decode する。
feature activity、reconstruction error、explained variance、上位 feature ID、top-feature Jaccard を記録する。SAE を
層番号から推測しない。未実施の SAE arm は null result ではなく、証拠の欠落である。
