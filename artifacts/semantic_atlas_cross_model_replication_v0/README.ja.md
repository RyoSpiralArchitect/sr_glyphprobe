# Semantic atlas model横断再現 v0 evidence

[English](README.md) · [結果](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [固定プロトコル](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.ja.md)

このcompact bundleは、事前に固定して完了したT10の9セル再現実験を記録する。登録済みのモデル横断一次判定は、
`cross_model_replication_not_established_under_frozen_rule`という負の結果だった。統計的な部分連言検定は
`p = 0.0001`で通過したが、実用条件を満たしたcore cellは4つ中2つにとどまり、必要な3つに届かなかった。

Bundleには次を収録する。

- 一次・副次analysisの完全な出力
- モデルごとのcompactなpredictionと全cell metrics
- Run、summary、session、shard ledgerへのbinding
- 機械可読な独立検証結果
- Raw activationとmodel weightは収録しない

9 runの合計は333 shard、15,768 model forward、FP32 readout 126,144本である。外部raw archiveには
activation 1,212,819,072 bytesを保持する。独立validatorはraw ledger対象1,350件を再ハッシュし、全activation
配列を検査したうえで、randomization、IUT、Holm補正、部分連言検定を正確に再現した。

Git内のevidenceは、modelを実行せず次のコマンドで再検証できる。

```bash
python scripts/validate_semantic_atlas_cross_model_replication_v0_result.py \
  --bundle artifacts/semantic_atlas_cross_model_replication_v0
```

外部raw archiveも検証する場合は、`--raw-root path/to/glyphprobe-t10-runs-8673bc51`を追加する。
この検証でmodel forward、intervention、generationは行わない。

3 viewのtoken数を完全一致させても観測差は消えなかったが、tokenization非依存性を示すものではない。
T10は、意味、因果、scale law、tuning効果、独立再現、architecture一般性、model一般性、Phase I gateの
主張を認めない。
