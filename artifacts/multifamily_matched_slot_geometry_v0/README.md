# Multifamily matched-slot geometry v0 evidence

[日本語](README.ja.md) · [Result document](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Frozen protocol](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md) · [Analysis repair](../../docs/MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md)

This compact bundle retains the complete two-model observational evidence for
`glyphprobe-multifamily-matched-slot-geometry-v0`.

## Result

Outcome pattern: `olmo_only_token_structured_recurrence`.

| Model | All-depth statistic | Null mean | Holm p | Decision |
|---|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.204304805 | 0.199984463 | 0.208500 | do not reject |
| OLMo 3 7B BF16 | 0.500391869 | 0.200184835 | 0.000100 | reject |

OLMo's matched slots share the exact final token across families. The positive
OLMo result is therefore token-structured observational evidence, not semantic
or tokenizer-independent recurrence.

## Contents

- `runs/gemma2_2b_4bit/`: full `50 × 5 × 2304` activation array, item rows,
  scrubbed receipt, and ledger;
- `runs/olmo3_7b_bf16/`: full `50 × 5 × 4096` activation array, item rows,
  scrubbed receipt, and ledger;
- `analysis/`: all ten fixed-depth rows, primary results, generated report, and
  ledger;
- `OLMO_TRANSFER_RECEIPT.json`: mac1 → furnace relay → mac2 byte-identity
  receipt; and
- `PUBLIC_MANIFEST.json`: size and SHA-256 for every payload member.

The first analysis serialization failure remains in
`validation/multifamily_matched_slot_geometry_v0/analysis_attempt_01_failure.json`.
The successful analysis receipt binds the separately frozen serialization-only
repair.

## Boundary

The bundle performs no intervention or generation and uses no protected target
bank. Integrity PASS is not evidence of semantic meaning, causality, backend or
node equivalence, tokenizer equivalence, confirmation, or paper-gate closure.
