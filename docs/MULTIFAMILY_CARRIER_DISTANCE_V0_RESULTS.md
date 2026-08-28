# Multifamily carrier-distance v0 results

[日本語](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_CARRIER_DISTANCE_V0.md) · [T4 common-suffix result](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Public evidence](../artifacts/multifamily_carrier_distance_v0/README.md) · [Research roadmap](ROADMAP.md)

## Status

All three role-bound MLX runs and the frozen joint analysis are complete. The
predeclared outcome pattern is:

```text
no_model_distance_attenuation
```

Gemma did not reject the distance-1 recurrence component. Llama and OLMo both
showed strong distance-1 matched-slot recurrence, but neither passed the
prespecified attenuation component. Therefore no model-level
intersection-union test survived Holm correction.

This is a clean negative result for the fixed hypothesis that distance-1
recurrence coexists with a positive equal-weight log-distance attenuation
contrast. It is not evidence that all layers or carriers lack attenuation.

## Sole primary decision

For each model, criterion A is the equal-weight matched-slot fraction at
distance 1. Criterion B is the fixed contrast with weights
`[0.375, 0.125, -0.125, -0.375]` over distances `[1, 2, 4, 8]`. The model raw
p-value is `max(p_A, p_B)`, requiring both components to reject. The three
model raw p-values form one Holm family.

| Model | Distance-1 statistic | Distance-1 null | A raw p | Attenuation statistic | Attenuation null | B raw p | IUT raw p | Holm p | Reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.200656830 | 0.199977044 | 0.443100 | -0.000633858 | -0.000021797 | 0.573250 | 0.573250 | 1.000000 | no |
| Llama 3.2 3B BF16 | 0.379308324 | 0.200031314 | 0.000050 | +0.006117042 | +0.000013437 | 0.188000 | 0.188000 | 0.564000 | no |
| OLMo 3 7B BF16 | 0.480237964 | 0.200022223 | 0.000050 | -0.016777622 | +0.000027680 | 0.997700 | 0.997700 | 1.000000 | no |

The `0.000050` values are the minimum attainable with 19,999 permutations plus
the observed arrangement. They do not imply greater precision. Llama's
attenuation contrast was positive but not significant. OLMo's contrast had the
opposite sign from the preregistered attenuation direction.

## Fixed distance profiles

These values average both carriers and all five fixed depths. They are
secondary descriptions and cannot replace the intersection-union decision.

| Model | Distance 1 | Distance 2 | Distance 4 | Distance 8 | Distance-8 secondary raw p |
|---|---:|---:|---:|---:|---:|
| Gemma 2 2B 4-bit | 0.200656830 | 0.211302569 | 0.205476462 | 0.204289154 | 0.328350 |
| Llama 3.2 3B BF16 | 0.379308324 | 0.414182232 | 0.395855983 | 0.369104963 | 0.000050 |
| OLMo 3 7B BF16 | 0.480237964 | 0.519478926 | 0.513115946 | 0.527099283 | 0.000050 |

Llama and OLMo remain descriptively far above the approximate `0.2` matched
null at distance 8. The tail p-values have no separate multiplicity decision,
so they are not promoted to additional findings. The warranted update is that
the prespecified rapid-decay account failed; the data do not authorize a claim
of monotonic persistence, a duration threshold, or a causal memory mechanism.

## Carrier-specific profiles

Carrier rows are secondary. The full eight-token input is identical across
the four readout positions within each row.

| Model | Carrier | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---|---|---:|---:|---:|---:|
| Gemma | repeated `" a"` | 0.199310675 | 0.207914984 | 0.200147733 | 0.198540848 |
| Gemma | repeated `" |"` | 0.202002984 | 0.214690153 | 0.210805191 | 0.210037461 |
| Llama | repeated `" a"` | 0.387362659 | 0.404269609 | 0.408233188 | 0.400877013 |
| Llama | repeated `" |"` | 0.371253990 | 0.424094856 | 0.383478779 | 0.337332913 |
| OLMo | repeated `" a"` | 0.468668767 | 0.503575959 | 0.512291839 | 0.560264051 |
| OLMo | repeated `" |"` | 0.491807162 | 0.535381894 | 0.513940053 | 0.493934516 |

The carrier dependence is visibly heterogeneous, especially for OLMo. It was
not a primary contrast and cannot be used to select one carrier after seeing
the result.

## Distance by fixed depth

Each cell below averages the two carriers. All 60 values are secondary; the
public JSONL retains the complete 120 carrier-by-distance-by-depth rows and
their synchronized-null summaries.

### Gemma 2 2B 4-bit

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.178653037 | 0.185198569 | 0.191889945 | 0.196528011 |
| 0.25 | 6 | 0.200540704 | 0.211932778 | 0.200889113 | 0.200956821 |
| 0.50 | 13 | 0.220397107 | 0.223517922 | 0.218197119 | 0.216934929 |
| 0.75 | 19 | 0.217150119 | 0.217704005 | 0.221299018 | 0.211852204 |
| 1.00 | 25 | 0.186543181 | 0.218159569 | 0.195107114 | 0.195173807 |

### Llama 3.2 3B BF16

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.663051102 | 0.605736836 | 0.500824704 | 0.454247578 |
| 0.25 | 7 | 0.354715394 | 0.456325946 | 0.485361405 | 0.433449983 |
| 0.50 | 14 | 0.314013477 | 0.373443544 | 0.381871373 | 0.353489288 |
| 0.75 | 21 | 0.282346056 | 0.320819845 | 0.310297711 | 0.304232304 |
| 1.00 | 27 | 0.282415593 | 0.314584991 | 0.300924725 | 0.300105663 |

### OLMo 3 7B BF16

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.962477562 | 0.889281337 | 0.835146968 | 0.813777154 |
| 0.25 | 8 | 0.503025433 | 0.564197250 | 0.560168419 | 0.605952378 |
| 0.50 | 16 | 0.380462384 | 0.456923039 | 0.471856214 | 0.506012477 |
| 0.75 | 24 | 0.283704004 | 0.360400149 | 0.369754437 | 0.373642888 |
| 1.00 | 31 | 0.271520439 | 0.326592857 | 0.328653692 | 0.336111519 |

The first captured layer declines with distance in both Llama and OLMo, while
later fixed depths are flatter or rise. That depth-by-distance heterogeneity is
post-outcome and descriptive. It does not rescue the failed model-level
attenuation endpoint or establish reconstitution by a particular component.
A future interaction test would require a new prospective freeze.

## Relation to T4

T4 showed OLMo matched-slot recurrence exactly one common token after the raw
glyph in period and newline contexts. T5 changes both the carrier construction
and the full input length, then reads fixed positions inside that unchanged
eight-token input. T4 is therefore a design motivation and descriptive
reference only; its values are not pooled with T5.

Gemma again stays near its matched null. Llama, added prospectively in T5,
shows distance-1 recurrence and a persistent descriptive profile, but its
earlier Stage-A backend-parity gate remains unqualified. OLMo does not follow
the prespecified attenuation contrast. A structured-prefix propagation account
remains sufficient for both structured-tokenizer cells.

## Integrity and transfer

- The public freeze is commit
  `e0043c6af6a397ca229900fa5a0b4aa134d242b8`.
- Gemma, Llama, and OLMo produced arrays of shape
  `50 × 2 × 4 × 5 × 2304`, `50 × 2 × 4 × 5 × 3072`, and
  `50 × 2 × 4 × 5 × 4096`, respectively.
- Each model made 400 forward calls; the total was 1,200. Intervention,
  generation, and protected-target calls were all zero.
- All three run validators and the joint 120-row analysis validator passed.
- The frozen source archive matched across mac2, the furnace relay, and mac1.
  The returned OLMo archive and all four sealed files matched across mac1, the
  furnace relay archive, and mac2. Furnace GPU compute was not used.
- Complete compressed activations, observations, receipts, ledgers, analysis,
  transfer receipt, and public manifest are published.

## Claim boundary and next decision

T5 rejects no model under its sole primary intersection-union family. It does
not show that recurrence disappears, that all layers share one decay law, or
that an emoji meaning is stored across eight tokens. It does not identify a
mechanism, circuit, architecture effect, scale effect, precision effect,
tokenizer effect, node effect, backend-equivalent result, confirmation, or
Phase I paper-gate closure.

The most informative next observational option is not another larger glyph
panel. It is a separately frozen depth-by-distance interaction replication,
or a same-artifact control that breaks the shared slot structure while
preserving the carrier and readout positions. Either option must preserve the
negative T5 model-level result and must not select a favorable layer from this
profile as a new primary endpoint.
