# Multifamily common-suffix carryover v0 result

Outcome pattern: `olmo_only_common_suffix_carryover`.

| Model | Two-context all-depth statistic | Null mean | Excess | Raw p | Holm p | Reject |
|---|---:|---:|---:|---:|---:|---|
| `gemma2_2b_4bit` | 0.203443011 | 0.200044692 | 0.003398319 | 0.302950000 | 0.302950000 | false |
| `olmo3_7b_bf16` | 0.537464703 | 0.199977865 | 0.337486838 | 0.000050000 | 0.000100000 | true |

This frozen observational endpoint reads both exact common suffix tokens. T3 raw-glyph values are descriptive references only. The result is not semantic, causal, confirmatory, tokenizer-equivalent, backend-equivalent, or a Phase I gate decision.
