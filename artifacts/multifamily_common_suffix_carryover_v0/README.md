# Public evidence: multifamily common-suffix carryover v0

[日本語](README.ja.md) · [Result](../../docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Frozen protocol](../../docs/MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md)

This directory contains the complete compact evidence for protocol
`glyphprobe-multifamily-common-suffix-carryover-v0`, frozen at commit
`868f3be36e10bc6acd7e44caaf916b4e1ede84b9`.

The predeclared outcome is `olmo_only_common_suffix_carryover`. Gemma did not
reject the two-context all-depth null (`T = 0.203443011`, Holm `p = 0.30295`).
OLMo did (`T = 0.537464703`, Holm `p = 0.0001`). The OLMo structure remains
observable one common token after the raw glyph in both fixed contexts. This is
observational short-range carryover, not semantic or causal evidence.

## Contents

- `runs/gemma2_2b_4bit/` and `runs/olmo3_7b_bf16/`: complete activation arrays,
  ordered observations, run receipts, and internal ledgers;
- `analysis/`: all 20 context-by-depth rows, joint receipt, report, and ledger;
- `OLMO_TRANSFER_RECEIPT.json`: individual file equality across mac1, the
  furnace relay archive, and mac2, with no furnace GPU compute;
- `PUBLIC_MANIFEST.json`: exact public payload sizes and SHA-256 values.

From the repository root, replay integrity checks with:

```bash
python scripts/multifamily_common_suffix_carryover_v0.py validate-run \
  artifacts/multifamily_common_suffix_carryover_v0/runs/gemma2_2b_4bit
python scripts/multifamily_common_suffix_carryover_v0.py validate-run \
  artifacts/multifamily_common_suffix_carryover_v0/runs/olmo3_7b_bf16
python scripts/multifamily_common_suffix_carryover_v0.py validate-analysis \
  artifacts/multifamily_common_suffix_carryover_v0/analysis
```

Successful validation establishes byte integrity and protocol conformance. It
does not establish semantics, a causal mechanism, tokenizer independence,
model or node equivalence, confirmation, or Phase I gate closure.
