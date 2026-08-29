# T10モデル横断診断 evidence v1

[English](README.md) · [解釈](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md)

このdirectoryには、生成済みのcompactなT10-D診断outputを置く。Git内のT10 bundleと、返送済み333-shard FP32 archiveから計算しており、新しいmodel forwardはゼロである。

- `diagnostics.json`：機械可読の診断値、input hash、raw run ledger hash、再構成検査、claim boundary flag
- `report.md`：自動生成した短いreport
- `SHA256SUMS`：二つの生成fileを固定するledger

36本のprediction array、84,096個のprediction値を再構成し、不一致はゼロだった。この解析は事後的・記述的であり、凍結済みの統合規則におけるT10一次判定は負のままである。
