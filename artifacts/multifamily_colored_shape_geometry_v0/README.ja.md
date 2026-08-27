# Multifamily colored-shape geometry v0 公開エビデンス

[English](README.md) · [全結果](../../docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [固定プロトコル](../../docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md)

このdirectoryには、commit `dc78756bd8f26ae0060463e459d5deb40c47d750`で固定した
`glyphprobe-multifamily-colored-shape-geometry-v0`の軽量な全エビデンスを収録する。

## 内容

- `runs/gemma2_2b_4bit/`: raw glyphのforward 10回と、sealed
  `10 × 5 × 2304` activation array
- `runs/olmo3_7b_bf16/`: raw glyphのforward 10回と、sealed
  `10 × 5 × 4096` activation array
- `analysis/`: 固定5深度×2 modelの全10行、2-cell primary判定、compact report、
  sealed checksum ledger
- `OLMO_TRANSFER_RECEIPT.json`: 4 fileの生成元・relay・到着先hash
- `PUBLIC_MANIFEST.json`: 生成エビデンス13 fileのhash・sizeと、転送・検証status

Runとanalysisの各directoryには、それぞれ`SHA256SUMS`がある。OLMo directoryは、
joint analysisより前にmac1、furnace relay、mac2の3地点でbyte単位の一致を確認した。
このdirectoryへ収録した後も、3 bundleすべてが凍結済みvalidatorに合格している。

Primary outcomeは`no_dual_model_recurrence`である。Gemmaのmidpointは正だったが、
Holm補正後は棄却しなかった（`T = 0.114857969`、調整済み`p = 0.116666667`）。
OLMoも棄却しなかった（`T = 0.024628040`、調整済み`p = 0.275`）。
非primary layerは記述に限る。

このbundleが示すのは、観測cellの完全性と再実行可能性である。意味、機構、因果性、
backend parity、quantization同等性、scale効果、科学的確認は確立しない。
