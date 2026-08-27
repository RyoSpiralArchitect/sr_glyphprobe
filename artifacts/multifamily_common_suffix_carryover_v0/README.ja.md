# 公開evidence: multifamily common-suffix carryover v0

[English](README.md) · [結果](../../docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [固定protocol](../../docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md)

このdirectoryには、commit
`868f3be36e10bc6acd7e44caaf916b4e1ede84b9`で固定したprotocol
`glyphprobe-multifamily-common-suffix-carryover-v0`のcompactな全evidenceを収録します。

事前に定めた結果の型は`olmo_only_common_suffix_carryover`です。2文脈×全深度nullは、
Gemmaでは棄却されず（`T = 0.203443011`、Holm `p = 0.30295`）、OLMoでは棄却されました
（`T = 0.537464703`、Holm `p = 0.0001`）。OLMoの構造は、固定した両文脈で、生の絵文字
から1つ後ろの共通token上にも残ります。これは観測的な短距離carryoverであり、意味や
因果の証拠ではありません。

## 内容

- `runs/gemma2_2b_4bit/`と`runs/olmo3_7b_bf16/`: 全activation array、順序付き
  observation、run receipt、内部ledger
- `analysis/`: 全20文脈×深度row、合同receipt、report、ledger
- `OLMO_TRANSFER_RECEIPT.json`: mac1、furnace relay archive、mac2の個別file一致。
  furnace GPU計算は不使用
- `PUBLIC_MANIFEST.json`: 公開payloadの正確なbyte数とSHA-256

Repository rootから次のようにintegrityを再検証できます。

```bash
python scripts/multifamily_common_suffix_carryover_v0.py validate-run \
  artifacts/multifamily_common_suffix_carryover_v0/runs/gemma2_2b_4bit
python scripts/multifamily_common_suffix_carryover_v0.py validate-run \
  artifacts/multifamily_common_suffix_carryover_v0/runs/olmo3_7b_bf16
python scripts/multifamily_common_suffix_carryover_v0.py validate-analysis \
  artifacts/multifamily_common_suffix_carryover_v0/analysis
```

ValidatorのPASSが示すのは、byte integrityとprotocol準拠です。意味、因果mechanism、
tokenizer非依存性、model/node同等性、確認的結論、Phase I gate達成は示しません。
