# Multifamily matched-slot geometry v0 results

[日本語](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md) · [Analysis repair](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md) · [Public evidence](../artifacts/multifamily_matched_slot_geometry_v0/README.md) · [Research roadmap](ROADMAP.md)

## Status

Both role-bound MLX runs and the repaired joint analysis are complete. The
predeclared outcome pattern is:

```text
olmo_only_token_structured_recurrence
```

Gemma did not reject the all-depth matched-slot null. OLMo rejected after Holm
correction, but OLMo's exact tokenizer contract gives every matched slot the
same final token across all five families. The result is therefore consistent
with a token-structured explanation and does not support tokenizer-independent
or semantic recurrence.

## Primary all-depth result

The primary statistic is the equal-depth mean of the slot sum-of-squares
fraction after family centering. Its synchronized null independently permutes
slot labels within each family for 19,999 fixed PCG64 draws. The two model-level
p-values form one Holm family.

| Model | Observed | Null mean | Excess | Raw p | Holm p | Reject |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.204304805 | 0.199984463 | +0.004320342 | 0.208500 | 0.208500 | no |
| OLMo 3 7B BF16 | 0.500391869 | 0.200184835 | +0.300207034 | 0.000050 | 0.000100 | yes |

The OLMo p-value reached the minimum attainable value for 19,999 random draws
plus the observed arrangement. No stronger precision is implied.

## Complete fixed-depth profile

Per-depth p-values are secondary. They carry no multiplicity-adjusted decision
and cannot replace the all-depth primary endpoint.

| Model | Fraction | Layer | Slot fraction | Null mean | Excess | Secondary p |
|---|---:|---:|---:|---:|---:|---:|
| Gemma | 0.00 | 0 | 0.193842 | 0.200009 | -0.006167 | 0.970150 |
| Gemma | 0.25 | 6 | 0.203212 | 0.199994 | +0.003218 | 0.252800 |
| Gemma | 0.50 | 13 | 0.211557 | 0.199991 | +0.011567 | 0.084350 |
| Gemma | 0.75 | 19 | 0.203293 | 0.199962 | +0.003331 | 0.262800 |
| Gemma | 1.00 | 25 | 0.209620 | 0.199967 | +0.009653 | 0.278400 |
| OLMo | 0.00 | 0 | 0.994722 | 0.200455 | +0.794267 | 0.000050 |
| OLMo | 0.25 | 8 | 0.461325 | 0.200172 | +0.261152 | 0.000050 |
| OLMo | 0.50 | 16 | 0.413424 | 0.200134 | +0.213290 | 0.000050 |
| OLMo | 0.75 | 24 | 0.336661 | 0.200084 | +0.136577 | 0.000050 |
| OLMo | 1.00 | 31 | 0.295828 | 0.200079 | +0.095749 | 0.000050 |

The OLMo slot fraction decreases sharply with depth but remains above its fixed
null at every reported depth. This is a descriptive persistence profile, not a
claim that a semantic slot variable is transformed or retained by a mechanism.

## Tokenizer-conditioned interpretation

The outcome follows the strongest tokenizer-side prediction:

- Gemma encodes the 50 glyphs as 50 distinct atomic tokens. Its omnibus result
  did not recur beyond the randomized matched-slot baseline.
- OLMo encodes every glyph as `[9468, family_token, slot_token]`. Its final
  slot token is identical across families, and its matched-slot geometry is
  strong at the earliest fixed depth and weakens across the stack.

This contrast makes a tokenizer-structural account sufficient for the positive
OLMo result. It does not prove that token identity caused the geometry because
model family, width, precision/quantization, and node differ simultaneously.
It also does not prove that Gemma lacks all glyph or Unicode geometry; it only
fails the frozen all-depth endpoint on this panel.

## Integrity and the analysis repair

- The public protocol freeze was commit
  `ae928b840e6164c89e9c4c71d5e41ceb8de3dfaa`.
- Gemma produced a `50 × 5 × 2304` activation array; OLMo produced
  `50 × 5 × 4096`.
- Each run made 50 model forwards and zero intervention, generation, or
  protected-target calls.
- Both run ledgers and the joint analysis validator passed.
- The four OLMo files matched at mac1, the furnace relay, and mac2. Furnace GPU
  compute was not used.

The first joint-analysis attempt failed before publication because YAML parsed
the key `null` as Python `None`, which JSON cannot use as a mapping key. No
analysis value was printed or inspected. Commit
`7f9184d9adb1bf6487a5e262f2fcdace90f68608` publicly froze a
serialization-only repair before the successful rerun. It maps that one key to
the string `"null"` and changes no input, statistic, randomization, seed, draw
count, p-value, multiplicity rule, outcome registry, or report row.

## Claim boundary

The strongest permitted description is **observational matched-slot recurrence
in the OLMo cell under an exact shared final-token construction, without
recurrence in the Gemma all-depth omnibus**.

This result does not establish emoji meaning, semantic families, a
tokenizer-independent glyph property, a causal mechanism, backend parity,
model-scale or quantization effects, node effects, confirmation, or a Phase I
paper gate. Complete negative and positive rows are retained without selecting
a favorable family or depth.
