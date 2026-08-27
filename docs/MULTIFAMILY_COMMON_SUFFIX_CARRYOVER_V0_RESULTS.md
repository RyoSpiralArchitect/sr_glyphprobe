# Multifamily common-suffix carryover v0 results

[日本語](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md) · [T3 raw-glyph result](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Public evidence](../artifacts/multifamily_common_suffix_carryover_v0/README.md) · [Research roadmap](ROADMAP.md)

## Status

Both role-bound MLX runs and the frozen joint analysis are complete. The
predeclared outcome pattern is:

```text
olmo_only_common_suffix_carryover
```

Gemma did not reject the two-context, all-depth matched-slot null. OLMo did
reject after Holm correction. The OLMo recurrence therefore survives moving
the readout from the shared raw slot token to a common token exactly one
position later. This rules out a strictly current-token-only description of
the T3 observation, but it does not rule out local propagation from the
immediately preceding tokenizer structure.

## Primary result

The primary statistic is the equal-weight mean of the slot sum-of-squares
fraction after family centering across two fixed suffix contexts and five fixed
depths. One synchronized within-family slot permutation is reused across all
ten cells for each of 19,999 PCG64 draws. The two model-level p-values form one
Holm family.

| Model | Observed | Null mean | Excess | Raw p | Holm p | Reject |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.203443011 | 0.200044692 | +0.003398319 | 0.302950 | 0.302950 | no |
| OLMo 3 7B BF16 | 0.537464703 | 0.199977865 | +0.337486838 | 0.000050 | 0.000100 | yes |

The OLMo raw p-value is the minimum attainable value for 19,999 draws plus the
observed arrangement. No stronger precision is implied. The result remains
exploratory and observational; `confirmatory_status` and `phase_i_gate_closed`
are both false in the sealed receipt.

## Both suffix contexts

Context-specific values are secondary and do not carry separate multiplicity
decisions. The same randomization design was used for each descriptive
summary.

| Model | Context | Five-depth statistic | Null mean | Excess | Secondary p |
|---|---|---:|---:|---:|---:|
| Gemma | period | 0.199064943 | 0.200039599 | -0.000974656 | 0.542250 |
| Gemma | newline | 0.207821079 | 0.200049785 | +0.007771293 | 0.191650 |
| OLMo | period | 0.538985382 | 0.199989386 | +0.338995995 | 0.000050 |
| OLMo | newline | 0.535944025 | 0.199966344 | +0.335977681 | 0.000050 |

The near agreement between OLMo period and newline makes a single suffix-token
choice an implausible sole explanation. The two contexts are nevertheless not
independent replications: they use the same glyph panel, model artifact,
depths, and synchronized null.

## Complete fixed context-by-depth profile

Every row below is secondary. No context or depth may replace the primary
omnibus.

| Model | Context | Fraction | Layer | Slot fraction | Null mean | Excess | Secondary p |
|---|---|---:|---:|---:|---:|---:|---:|
| Gemma | period | 0.00 | 0 | 0.174106 | 0.200096 | -0.025989 | 0.994100 |
| Gemma | period | 0.25 | 6 | 0.207494 | 0.199951 | +0.007543 | 0.180350 |
| Gemma | period | 0.50 | 13 | 0.217654 | 0.200035 | +0.017619 | 0.085050 |
| Gemma | period | 0.75 | 19 | 0.202483 | 0.200045 | +0.002438 | 0.382850 |
| Gemma | period | 1.00 | 25 | 0.193587 | 0.200071 | -0.006484 | 0.660600 |
| Gemma | newline | 0.00 | 0 | 0.185929 | 0.200002 | -0.014072 | 0.855750 |
| Gemma | newline | 0.25 | 6 | 0.209157 | 0.200088 | +0.009069 | 0.172800 |
| Gemma | newline | 0.50 | 13 | 0.221039 | 0.200075 | +0.020964 | 0.109900 |
| Gemma | newline | 0.75 | 19 | 0.210167 | 0.200140 | +0.010027 | 0.204850 |
| Gemma | newline | 1.00 | 25 | 0.212813 | 0.199944 | +0.012868 | 0.217500 |
| OLMo | period | 0.00 | 0 | 0.990924 | 0.199897 | +0.791026 | 0.000050 |
| OLMo | period | 0.25 | 8 | 0.686897 | 0.199972 | +0.486926 | 0.000050 |
| OLMo | period | 0.50 | 16 | 0.441446 | 0.200022 | +0.241424 | 0.000050 |
| OLMo | period | 0.75 | 24 | 0.294227 | 0.200050 | +0.094177 | 0.000050 |
| OLMo | period | 1.00 | 31 | 0.281434 | 0.200007 | +0.081427 | 0.000050 |
| OLMo | newline | 0.00 | 0 | 0.984778 | 0.199868 | +0.784910 | 0.000050 |
| OLMo | newline | 0.25 | 8 | 0.678584 | 0.199961 | +0.478623 | 0.000050 |
| OLMo | newline | 0.50 | 16 | 0.423447 | 0.199977 | +0.223469 | 0.000050 |
| OLMo | newline | 0.75 | 24 | 0.316141 | 0.200029 | +0.116112 | 0.000050 |
| OLMo | newline | 1.00 | 31 | 0.276770 | 0.199997 | +0.076773 | 0.000050 |

OLMo is near-perfect at the first captured block output in both contexts and
then declines across the stack while remaining above the fixed null. This is a
descriptive depth profile, not evidence that a semantic variable is being
carried by a specific mechanism.

## What changed from T3

T3 read the raw glyph's final token. OLMo's raw tokenization was exactly
`[9468, family_token, slot_token]`, so the same matched slot had the same
current token across families. T4 appends either a period or newline and reads
the common suffix token instead. The current token is now identical for all 50
items within each context, while the complete raw glyph sequence remains in
the immediate prefix.

| Model | T3 raw-glyph statistic | T4 common-suffix statistic | T4 minus T3 |
|---|---:|---:|---:|
| Gemma | 0.204304805 | 0.203443011 | -0.000861794 |
| OLMo | 0.500391869 | 0.537464703 | +0.037072834 |

These differences are descriptive only. T3 and T4 were not pooled into one
inferential test, and T4 was not designed to test an increase over T3.

The strongest warranted update is therefore narrow: **OLMo's matched-slot
geometry is not confined to reading the slot token itself; it is observable one
common token later in both fixed contexts.** An account based on short-range
token-sequence propagation remains sufficient. Gemma remains near its matched
null under both the raw and common-suffix assays.

## Integrity and transfer

- The public protocol freeze is commit
  `868f3be36e10bc6acd7e44caaf916b4e1ede84b9`.
- Gemma produced a `50 × 2 × 5 × 2304` array; OLMo produced
  `50 × 2 × 5 × 4096`.
- Each run made 100 model forwards and zero intervention, generation, or
  protected-target calls.
- Both run validators and the joint analysis validator passed.
- The four OLMo run files matched individually at mac1, inside the furnace
  relay archive, and at mac2. Furnace GPU compute was not used.
- The complete compact arrays, observations, receipts, analysis, checksums,
  and transfer receipt are published.

## Claim boundary and next decision

This result does not establish emoji semantics, tokenizer independence, a
causal mechanism, model-scale or precision effects, node effects, backend
parity, behavioral steering, confirmation, or a Phase I paper gate. Gemma and
OLMo differ in tokenizer, architecture, size, precision, and node.

The result supports a cheap next falsification before intervention: freeze a
distance-decay carrier assay that reads the same common token after several
matched carrier distances. Persistence versus rapid decay would separate a
strictly one-token-local account from a longer contextual trace. That assay
would still be observational and must not replace the tokenization-matched
confirmatory controls required by Milestone 2.
