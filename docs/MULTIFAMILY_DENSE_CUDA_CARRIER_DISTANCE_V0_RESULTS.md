# Multifamily dense CUDA carrier-distance v0 results

[日本語](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md) · [T5 results](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Public evidence](../artifacts/multifamily_dense_cuda_carrier_distance_v0/README.md) · [Research roadmap](ROADMAP.md)

## Status

All four role-bound BF16 Transformers/CUDA runs and the frozen joint analysis
are complete. The predeclared outcome pattern is:

```text
no_dense_model_distance_attenuation
```

None of the four model-level intersection-union tests survived Holm correction.
Gemma 2 2B IT, Gemma 3 4B IT, and Gemma 3 12B IT did not reject the
distance-1 component. Mistral 7B Instruct v0.3 strongly rejected that component,
but did not reject the fixed positive log-distance attenuation component.

This is a clean negative result for T6's fixed recurrence-plus-attenuation
conjunction. It is not evidence that every layer or carrier lacks attenuation.

## Sole primary decision

For each model, criterion A is the equal-weight matched-slot fraction at
distance 1. Criterion B is the fixed contrast with weights
`[0.375, 0.125, -0.125, -0.375]` over distances `[1, 2, 4, 8]`. The model raw
p-value is `max(p_A, p_B)`, requiring both components to reject. The four model
raw p-values form one Holm family.

| Model | Distance-1 statistic | Distance-1 null | A raw p | Attenuation statistic | Attenuation null | B raw p | IUT raw p | Holm p | Reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Gemma 2 2B IT | 0.193651440 | 0.200026712 | 0.765300 | -0.002917767 | -0.000010763 | 0.770900 | 0.770900 | 1.000000 | no |
| Gemma 3 4B IT | 0.188406654 | 0.199900049 | 0.753000 | -0.011727577 | +0.000054641 | 0.845150 | 0.845150 | 1.000000 | no |
| Mistral 7B Instruct v0.3 | 0.384482548 | 0.199919677 | 0.000050 | +0.000672124 | -0.000043576 | 0.469750 | 0.469750 | 1.000000 | no |
| Gemma 3 12B IT | 0.183050961 | 0.199966981 | 0.825800 | -0.021082592 | -0.000052892 | 0.975750 | 0.975750 | 1.000000 | no |

The `0.000050` value is the minimum attainable with 19,999 permutations plus
the observed arrangement. It does not imply greater precision. Mistral's
attenuation contrast was slightly positive but non-significant. Both Gemma 3
contrasts had the opposite sign from the preregistered attenuation direction.

## Fixed distance profiles

These values average both carriers and all five fixed depths. They are
secondary descriptions and cannot replace the intersection-union decision.

| Model | Distance 1 | Distance 2 | Distance 4 | Distance 8 | Distance-8 secondary raw p |
|---|---:|---:|---:|---:|---:|
| Gemma 2 2B IT | 0.193651440 | 0.195496670 | 0.201573016 | 0.199406704 | 0.507350 |
| Gemma 3 4B IT | 0.188406654 | 0.205419840 | 0.210326645 | 0.218044590 | 0.188000 |
| Mistral 7B Instruct v0.3 | 0.384482548 | 0.424695499 | 0.393637011 | 0.393043048 | 0.000050 |
| Gemma 3 12B IT | 0.183050961 | 0.182362620 | 0.192866008 | 0.235770077 | 0.040450 |

Mistral remains descriptively far above the approximate `0.2` matched null at
distance 8. Gemma 3 12B also has a nominal distance-8 secondary p-value below
0.05. Neither tail value has an authorized multiplicity decision, and neither
is promoted to a finding. T6 does not establish monotonic persistence, a
duration threshold, or a causal memory mechanism.

## Carrier-specific profiles

Carrier rows are secondary. The full eight-token input is identical across the
four readout positions within each row.

| Model | Carrier | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---|---|---:|---:|---:|---:|
| Gemma 2 2B IT | repeated `" a"` | 0.193942238 | 0.195153619 | 0.202303842 | 0.196795220 |
| Gemma 2 2B IT | repeated `" |"` | 0.193360641 | 0.195839721 | 0.200842190 | 0.202018188 |
| Gemma 3 4B IT | repeated `" a"` | 0.180378195 | 0.216307034 | 0.156518699 | 0.184858562 |
| Gemma 3 4B IT | repeated `" |"` | 0.196435112 | 0.194532646 | 0.264134591 | 0.251230617 |
| Mistral 7B Instruct v0.3 | repeated `" a"` | 0.385470450 | 0.422491524 | 0.377625207 | 0.357273678 |
| Mistral 7B Instruct v0.3 | repeated `" |"` | 0.383494646 | 0.426899475 | 0.409648814 | 0.428812418 |
| Gemma 3 12B IT | repeated `" a"` | 0.189024470 | 0.178709143 | 0.199290295 | 0.260436081 |
| Gemma 3 12B IT | repeated `" |"` | 0.177077452 | 0.186016098 | 0.186441720 | 0.211104072 |

The carrier heterogeneity is visible but was not a primary contrast. Selecting
one carrier after seeing these values would not repair the failed conjunction.

## Distance by fixed depth

Each cell below averages the two carriers. All 80 values are secondary; the
public JSONL retains all 160 carrier-by-distance-by-depth rows and their
synchronized-null summaries.

### Gemma 2 2B IT

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.178408896 | 0.177829872 | 0.182219945 | 0.178008921 |
| 0.25 | 6 | 0.196489263 | 0.205349978 | 0.204058820 | 0.199496270 |
| 0.50 | 13 | 0.199276470 | 0.204185129 | 0.210253852 | 0.208743632 |
| 0.75 | 19 | 0.200012065 | 0.201508110 | 0.207531567 | 0.206843388 |
| 1.00 | 25 | 0.194070505 | 0.188610260 | 0.203800895 | 0.203941309 |

### Gemma 3 4B IT

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.208975752 | 0.221441832 | 0.191555699 | 0.199838396 |
| 0.25 | 8 | 0.185275609 | 0.258003841 | 0.324944730 | 0.337349991 |
| 0.50 | 17 | 0.181698088 | 0.190836943 | 0.195496968 | 0.166173881 |
| 0.75 | 25 | 0.189398911 | 0.186508348 | 0.185494081 | 0.178661841 |
| 1.00 | 33 | 0.176684910 | 0.170308238 | 0.154141746 | 0.208198840 |

### Mistral 7B Instruct v0.3

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.836365849 | 0.723139096 | 0.602677623 | 0.571511962 |
| 0.25 | 8 | 0.354806832 | 0.467365680 | 0.458334036 | 0.448617661 |
| 0.50 | 16 | 0.274185730 | 0.353431252 | 0.345568404 | 0.373585819 |
| 0.75 | 24 | 0.233429276 | 0.307482822 | 0.297952151 | 0.308080214 |
| 1.00 | 31 | 0.223625055 | 0.272058647 | 0.263652839 | 0.263419584 |

### Gemma 3 12B IT

| Fraction | Layer | Distance 1 | Distance 2 | Distance 4 | Distance 8 |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.222637362 | 0.201772776 | 0.187882197 | 0.174324369 |
| 0.25 | 12 | 0.184419588 | 0.200908226 | 0.194565696 | 0.206043671 |
| 0.50 | 24 | 0.174331769 | 0.186055128 | 0.174721814 | 0.255386295 |
| 0.75 | 36 | 0.179400665 | 0.189049205 | 0.206966252 | 0.337316831 |
| 1.00 | 47 | 0.154465420 | 0.134027768 | 0.200194079 | 0.205779217 |

Mistral's first captured layer declines with distance while its later fixed
depths are flatter or rise. Gemma 3 4B and 12B show different non-monotone
depth profiles despite their shared observed tokenizer roster. These are
post-outcome descriptions. They do not establish reconstitution by a component
or a model-scale effect; either claim needs a new prospective interaction or
matched-pair protocol.

## Relation to T5

T5 also ended with no model passing the same fixed model-level conjunction.
Mistral's T6 profile descriptively resembles the elevated distance profiles in
T5's multi-token Llama and OLMo cells, while all three Gemma T6 cells stay much
closer to the matched null in the aggregate. The roster was selected after T5,
all T6 models are instruction-tuned, and T6 uses Transformers/CUDA rather than
the T5 MLX cells. The studies are therefore not pooled and T6 is not an
independent confirmation or a backend-parity test.

Gemma 3 4B and 12B share the same observed tokenizer roster, but one pair with
two selected parameter counts is not a scale sample. Their non-rejections do
not authorize a scale trend or an equivalence claim.

## Integrity, execution, and lifecycle gate

- The public freeze is commit
  `5e2f4984486b5e5dc87b93f656d6e00bc8718baa`; its manifest SHA-256 is
  `997389551df07922e8dcacfffa93a97a2ffb97a9da23e2e86fbc64c73a829f06`.
- The four arrays have shapes `50 × 2 × 4 × 5 × 2304`,
  `50 × 2 × 4 × 5 × 2560`, `50 × 2 × 4 × 5 × 4096`, and
  `50 × 2 × 4 × 5 × 3840` in frozen role order.
- Each model made 400 forward calls; the total was 1,600. Intervention,
  generation, and protected-target calls were all zero.
- All four run validators, all five returned SHA-256 ledgers, and the 160-row
  joint analysis validator passed. The GPU was released after each model and
  was free again after the final run.
- Immediately before compute, the furnace was observed free and the current
  `resource:furnace` notice surfaced at a natural receiver-owned Codex `Stop`
  boundary on mac2. Metadata was inspected; content was not retrieved, and no
  reply, commitment, or six-session delivery is claimed.
- The complete compressed activations, observations, receipts, ledgers,
  analysis, transfer receipt, and public manifest are published.

## Claim boundary and next decision

T6 rejects no model under its sole primary intersection-union family. It does
not show that recurrence disappears, that all layers share one decay law, or
that an emoji meaning is stored across eight tokens. It does not identify a
mechanism, circuit, architecture effect, scale effect, precision effect,
tokenizer effect, node effect, backend-equivalent result, confirmation, or
Phase I paper-gate closure.

The dense breadth option is now sufficiently sampled for this endpoint. The
clean next observational choice is a separately frozen same-artifact control
that breaks the shared slot structure while preserving carrier and readout
positions, or a prospectively fixed distance-by-depth interaction replication.
Neither may select Mistral, Gemma 3 12B's tail, or a favorable depth as a new
primary endpoint after viewing T6. Tokenization-matched controls and an untouched
confirmatory target set remain the higher-level Phase I priorities before a
causal claim.
