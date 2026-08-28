# Public evidence: multifamily carrier-distance v0

[日本語](README.ja.md) · [Result](../../docs/MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Frozen protocol](../../docs/MULTIFAMILY_CARRIER_DISTANCE_V0.md)

This directory contains the complete compact evidence for protocol
`glyphprobe-multifamily-carrier-distance-v0`, frozen at commit
`e0043c6af6a397ca229900fa5a0b4aa134d242b8`.

The predeclared outcome is `no_model_distance_attenuation`. Gemma did not show
distance-1 recurrence. Llama and OLMo did, but neither passed the fixed positive
log-distance attenuation component. No model-level intersection-union test
survived Holm correction.

## Contents

- `runs/`: complete activation arrays, ordered observations, receipts, and
  internal ledgers for Gemma, Llama, and OLMo;
- `analysis/`: all 120 carrier-by-distance-by-depth rows, joint receipt, report,
  and ledger;
- `TRANSFER_RECEIPT.json`: exact freeze-package and OLMo-return transfer
  equality across mac1, the furnace relay, and mac2, with no furnace GPU
  compute; and
- `PUBLIC_MANIFEST.json`: exact public payload sizes and SHA-256 values.

From the repository root, replay integrity checks with:

```bash
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/gemma2_2b_4bit
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/llama32_3b_bf16
python scripts/multifamily_carrier_distance_v0.py validate-run \
  artifacts/multifamily_carrier_distance_v0/runs/olmo3_7b_bf16
python scripts/multifamily_carrier_distance_v0.py validate-analysis \
  artifacts/multifamily_carrier_distance_v0/analysis
```

Successful validation establishes byte integrity and protocol conformance. It
does not establish monotonic decay, persistence duration, semantics, a causal
mechanism, tokenizer independence, backend or node equivalence, confirmation,
or Phase I gate closure.
