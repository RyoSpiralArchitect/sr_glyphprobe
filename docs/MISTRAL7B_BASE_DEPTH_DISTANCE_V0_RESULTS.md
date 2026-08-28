# Mistral 7B base depth-by-distance v0 results

[日本語](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.ja.md) · [Frozen protocol](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md) · [T6 results](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Public evidence](../artifacts/mistral7b_base_depth_distance_v0/README.md) · [Roadmap](ROADMAP.md)

## Status

The frozen 400-forward Mistral 7B v0.3 base-model cell and its 19,999-draw
analysis are complete. The registered outcome is:

```text
recurrence_and_early_depth_attenuation_excess
```

Both one-sided components reached the finite permutation floor, so the single
intersection-union test rejected at alpha 0.05. This is prospective evidence
for the fixed depth-dependent profile in one selected, previously unobserved
base-model cell. The model and endpoint were chosen after T6, so this is not an
independent confirmation and does not identify an instruction-tuning effect.

## Sole primary decision

Criterion A is the equal-weight distance-1 matched-slot fraction over both
carriers and all five depths. Criterion B first computes the fixed distance
contrast `[0.375, 0.125, -0.125, -0.375]` at every depth, then subtracts the
mean of the four later-depth contrasts from the depth-0 contrast. The IUT
p-value is the larger component p-value.

| Component | Statistic | Null mean | Excess over null | Raw p |
|---|---:|---:|---:|---:|
| Distance-1 recurrence | 0.377524026 | 0.199970302 | +0.177553724 | 0.000050 |
| Early-minus-late attenuation | 0.149104068 | 0.000111606 | +0.148992462 | 0.000050 |
| Intersection-union decision | — | — | — | **0.000050** |

With 19,999 randomizations plus the observed arrangement, `0.000050` is the
minimum attainable p-value. It does not support precision beyond that floor.
The decision requires both components and uses no post-outcome layer choice.

The original T6 all-depth attenuation contrast is retained as a registered
secondary output. It was negative (`-0.005273805`, raw `p = 0.874750`). Thus
the positive result is specifically the frozen depth interaction, not a rescue
of the failed all-depth attenuation endpoint.

## Fixed depth-by-distance profile

Each cell averages the repeated `" a"` and `" |"` carriers. The attenuation
column applies the frozen distance weights within that depth.

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 | Attenuation |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.841332583 | 0.726544742 | 0.606268804 | 0.577399364 | +0.114009450 |
| 0.25 | 8 | 0.351050392 | 0.490319560 | 0.473210701 | 0.459639655 | -0.038582366 |
| 0.50 | 16 | 0.260152003 | 0.366929984 | 0.385665647 | 0.374902352 | -0.045373339 |
| 0.75 | 24 | 0.223453811 | 0.319257335 | 0.327746893 | 0.311487528 | -0.034073839 |
| 1.00 | 31 | 0.211631342 | 0.277450668 | 0.286026770 | 0.268369787 | -0.022348929 |

Depth-0 attenuation was `+0.114009450`; the later-depth mean was
`-0.035094618`. Their prespecified difference was `+0.149104068`.

The all-depth distance profile was `[0.377524026, 0.436100458, 0.415783763,
0.398359737]`. Distance 8 remained above the synchronized null and reached a
secondary raw `p = 0.000050`, but the tail has no separate decision authority.
T7 does not establish monotonic persistence or a duration threshold.

## Descriptive relation to T6 Mistral Instruct

The base and T6 Instruct cells use the same observed tokenizer sequences,
architecture dimensions, distances, carriers, and readout layers. The T6
Instruct depth profile motivated T7 and was already known, so the comparison
below is descriptive and post-selection.

| Fraction | Base attenuation | T6 Instruct attenuation |
|---:|---:|---:|
| 0.00 | +0.114009450 | +0.114377892 |
| 0.25 | -0.038582366 | -0.034050106 |
| 0.50 | -0.045373339 | -0.036292177 |
| 0.75 | -0.034073839 | -0.026802768 |
| 1.00 | -0.022348929 | -0.013872223 |
| Early minus later mean | +0.149104068 | +0.142132210 |

Across the 20 depth-by-distance cells, the descriptive Pearson correlation was
`0.996785730`, mean absolute difference was `0.011953404`, RMSE was
`0.015478703`, and maximum absolute difference was `0.040097243`. No
equivalence margin, paired hypothesis test, or independent checkpoint sample
was frozen. These numbers cannot establish that instruction tuning has no
effect, that the checkpoints are equivalent, or that the profile is general.

## Carrier profile

Carrier-specific values are secondary. Each row averages all five depths.

| Carrier | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---|---:|---:|---:|---:|
| repeated `" a"` | 0.383700975 | 0.451806423 | 0.411254790 | 0.372560341 |
| repeated `" |"` | 0.371347077 | 0.420394492 | 0.420312735 | 0.424159133 |

The carriers differ descriptively, especially at distance 8, but neither was
selected or tested separately.

## Integrity and execution

- The public prospective freeze is commit
  `25de47a5fb4c9eaf7674d5b2fa49f0c2cf84ca8b`; its manifest SHA-256 is
  `495f323589d150ce3429035cb47694988eb33f7f7b97a7d58526cfc35ed03493`.
- The public model is `mistralai/Mistral-7B-v0.3` at revision
  `caa1feb0e54d415e2df31207e5f4e273e33509b1`. The selected 12-file local
  artifact excluded the duplicate consolidated weight and matched manifest
  SHA-256 `1ee90f904de614fd2e1088e9e978fa5b9d36d1a855807764fb8f91cacfd8d05e`.
- The zero-forward preflight verified all 7,248,023,552 indexed elements as
  BF16, the exact model dimensions, and the complete tokenizer/carrier roster.
- The run made 400 forwards and captured 2,000 vectors with shape
  `50 × 2 × 4 × 5 × 4096`. Intervention, generation, and protected-target
  calls were zero.
- The furnace was free immediately before compute and returned to 10 MiB,
  0% utilization, with no compute process after the run.
- Both furnace validators, both returned SHA-256 ledgers, and both mac2
  validators passed. The compact activation array and all 40 profile rows are
  published.

## Claim boundary and next decision

T7 supports recurrence of the fixed early-versus-later depth profile in the
selected base checkpoint. It narrows the earlier account that T6's shape was a
peculiarity of the one Instruct checkpoint, but it does not isolate why the two
related checkpoints are similar. Their tokenizer factorization and
architecture are shared, and their weights are related.

The result does not establish emoji semantics, a memory variable, a circuit,
causality, instruction-tuning invariance, tokenizer causality, backend or node
equivalence, model-family generality, independent confirmation, or a Phase I
paper gate. More adjacent Mistral checkpoints would add little. The clean next
observational control is an actual token-sequence construction that breaks
cross-family shared slot identity while preserving lengths, prefixes,
carriers, and readout positions; the clean next causal branch must separately
freeze an intervention and its controls.
