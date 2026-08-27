# Multifamily matched-slot geometry v0 evidence

[English](README.md) · [結果文書](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [固定protocol](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) · [Analysis repair](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.ja.md)

`glyphprobe-multifamily-matched-slot-geometry-v0`の2 model観測evidenceを省略せず
収録したcompact bundleです。

## 結果

Outcome pattern: `olmo_only_token_structured_recurrence`。

| Model | All-depth統計量 | Null平均 | Holm p | 判定 |
|---|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.204304805 | 0.199984463 | 0.208500 | 棄却しない |
| OLMo 3 7B BF16 | 0.500391869 | 0.200184835 | 0.000100 | 棄却する |

OLMoでは、同じmatched slotがfamilyをまたいで厳密に同じ末尾tokenを共有します。
したがって、OLMoの正の結果はtoken構造に沿う観測evidenceであり、意味上または
tokenizer非依存の再現ではありません。

## 内容

- `runs/gemma2_2b_4bit/`: `50 × 5 × 2304`の全activation array、item row、
  scrub済みreceipt、ledger
- `runs/olmo3_7b_bf16/`: `50 × 5 × 4096`の全activation array、item row、
  scrub済みreceipt、ledger
- `analysis/`: 固定した全10深度row、主結果、生成report、ledger
- `OLMO_TRANSFER_RECEIPT.json`: mac1 → furnace relay → mac2のbyte一致receipt
- `PUBLIC_MANIFEST.json`: 全payloadのsizeとSHA-256

最初のanalysis serialization failureは
`validation/multifamily_matched_slot_geometry_v0/analysis_attempt_01_failure.json`に
残しています。成功したanalysis receiptは、別途公開freezeしたserialization-only
repairを参照します。

## 境界

このbundleはinterventionもgenerationも行わず、protected target bankも使いません。
IntegrityのPASSは、意味、因果、backend/node同等性、tokenizer同等性、確認、論文gate
達成の証拠ではありません。
