# Multifamily colored-shape geometry v0 results

[日本語](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.ja.md) · [Frozen protocol](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md) · [Public evidence](../artifacts/multifamily_colored_shape_geometry_v0/README.md) · [Research roadmap](ROADMAP.md)

- Protocol ID: `glyphprobe-multifamily-colored-shape-geometry-v0`
- Freeze commit: `dc78756bd8f26ae0060463e459d5deb40c47d750`
- Outcome pattern: `no_dual_model_recurrence`

## Result in one sentence

The frozen midpoint test did not identify a shared circle-minus-square axis in
both predeclared model cells: Gemma 2 2B 4-bit produced a positive but
non-rejecting result after Holm correction, while OLMo 3 7B BF16 produced a
smaller positive result that also did not reject.

This is a complete negative/mixed outcome under the frozen rule. It is not
evidence that colored-shape geometry is absent, and it does not establish
semantics, mechanism, causality, backend parity, quantization equivalence, or a
model-scale effect.

## Frozen primary results

For each color, the endpoint forms the L2-normalized direction
`resid_post(circle) - resid_post(square)` at the predeclared midpoint layer and
averages the ten off-diagonal cosines among the five directions. The square
color labels are exhaustively permuted, including the identity pairing. The two
model-cell p-values form one Holm family at familywise alpha 0.05.

| Model role | Token regime | Primary layer | Parallelism | Exact count / 120 | Raw p | Holm p | Reject |
|---|---|---:|---:|---:|---:|---:|---|
| `gemma2_2b_4bit` | ten distinct atomic one-token glyphs | 13 / 26 | 0.114857969 | 7 | 0.058333333 | 0.116666667 | no |
| `olmo3_7b_bf16` | equal three-token spans, shared prefix | 16 / 32 | 0.024628040 | 33 | 0.275000000 | 0.275000000 | no |

Neither model cell rejected after the prespecified correction. The stronger
predeclared patterns—dual recurrence, Gemma-only rejection, OLMo-only
rejection, and opposite signs—therefore did not apply. The registered fallback,
`no_dual_model_recurrence`, was selected without replacing the primary layer.

## Complete fixed-depth profile

The four non-midpoint layers are descriptive. Their exact p-values are retained
to make the outcome auditable, but they carry no multiplicity decision and
cannot replace the primary layer after inspection.

| Model | Depth fraction | Layer | Parallelism | Exact p | Matched-color cross-shape excess | Decision status |
|---|---:|---:|---:|---:|---:|---|
| Gemma 2 2B 4-bit | 0.00 | 0 | 0.242416497 | 0.008333333 | 0.219694236 | descriptive only |
| Gemma 2 2B 4-bit | 0.25 | 6 | 0.175126893 | 0.008333333 | 0.251123238 | descriptive only |
| Gemma 2 2B 4-bit | 0.50 | 13 | 0.114857969 | 0.058333333 | 0.162412883 | primary; Holm did not reject |
| Gemma 2 2B 4-bit | 0.75 | 19 | 0.186448879 | 0.016666667 | 0.211163629 | descriptive only |
| Gemma 2 2B 4-bit | 1.00 | 25 | 0.203435852 | 0.016666667 | 0.284060541 | descriptive only |
| OLMo 3 7B BF16 | 0.00 | 0 | 0.035562068 | 0.991666667 | -0.021358138 | descriptive only |
| OLMo 3 7B BF16 | 0.25 | 8 | 0.027411455 | 0.316666667 | 0.020318093 | descriptive only |
| OLMo 3 7B BF16 | 0.50 | 16 | 0.024628040 | 0.275000000 | 0.054966885 | primary; Holm did not reject |
| OLMo 3 7B BF16 | 0.75 | 24 | 0.030455476 | 0.266666667 | 0.110482586 | descriptive only |
| OLMo 3 7B BF16 | 1.00 | 31 | 0.012424917 | 0.166666667 | 0.171737014 | descriptive only |

Gemma's non-primary rows include the minimum exhaustive p-value of `1/120` at
two fixed depths. Those rows were not in the primary family and were seen only
after the midpoint rule had been frozen; treating them as discoveries would be
post-outcome layer selection. OLMo's matched-color cross-shape excess increases
descriptively with depth even though the common circle-minus-square axis does
not strengthen. This separates two geometric summaries, but it does not by
itself identify a color or shape representation.

## Execution and integrity

Both scientific runs occurred after the public freeze and used the same pinned
implementation tree (`f8d7407ecc4bb5d40e000446e655af139d231fc45f11df732e59582f48c252aa`):

- Gemma: ten model forwards, activation array shape `10 × 5 × 2304`;
- OLMo: ten model forwards, activation array shape `10 × 5 × 4096`;
- generation calls: zero;
- intervention calls: zero;
- protected-target files opened: zero; and
- nonfinite activation values: zero.

Each run bundle passed its sealed-ledger validator at the source node. The OLMo
bundle was transferred from mac1 through the furnace relay to mac2. All four
file hashes matched at the source, relay, and destination, and the destination
bundle passed the validator again. The joint analyzer then revalidated both
roles, model manifests, the protocol freeze, input ledgers, item order, layer
order, shapes, and finite values before computing the endpoint. The final
analysis validator passed with ten retained layer rows.

The public evidence includes both activation arrays because the complete bundle
is only about 0.71 MB before its orientation and manifest files. It contains no
local absolute path, host address, credential, generated text, intervention
ledger, or protected target. The thirteen generated payload files total
`711469` bytes and are bound by public-manifest SHA-256
`f7e3a5fb9458e25cc0a58df1c3076ad4b5470caf9d544d2102081eee13c75ac1`.

## What this changes

This result closes T2 as an executed observational side track, not as a positive
cross-model replication. It provides direct evidence against using the current
two-cell design to claim a model-general shape axis. It also prevents a raw
Gemma midpoint value near the nominal threshold from being promoted after the
OLMo result and Holm family are considered.

The study does **not** isolate why the cells differ. Model family, parameter
count, quantization/precision, tokenizer structure, and node all change
together. Raw effect magnitudes therefore cannot be read as a scale curve or a
quantization effect.

Operational Milestone 2 remains unchanged. Its GPT-2 layer-2 candidate may
still enter a separately frozen causal protocol; T2 neither selects a new layer
for that protocol nor closes the causal, independent-backend, confirmatory, or
archive paper gates.

## Next options, not a new freeze

The outcome leaves three clean follow-up routes. None is selected or frozen by
this document.

1. **Deconfound the two cells.** Add one same-family or same-artifact contrast,
   such as Gemma 2 BF16 versus Gemma 2 4-bit, before interpreting a precision or
   scale difference.
2. **Broaden emoji families without layer fishing.** Reuse the already public
   animal, food, moon/sky, social, and transport panels for tokenizer-only
   feasibility first, then freeze a family-level endpoint or an all-depth
   omnibus rule before any new activation outcome is opened.
3. **Replicate the endpoint independently.** Reimplement the exact fixed panel,
   role binding, and exhaustive null in a qualified non-MLX backend or a new
   model cell. A replication must preserve negative rows and must not inherit
   Gemma's descriptive layer peaks as primary choices.

The next protocol should answer one of these questions rather than combine all
three. That keeps a negative result interpretable and prevents model breadth,
emoji breadth, and depth selection from becoming one inseparable search.

## Claim boundary

Supported wording:

> In a frozen observational raw-glyph `resid_post` study, the prespecified
> midpoint circle-minus-square parallelism endpoint did not recur with a
> Holm-corrected rejection in both a Gemma 2 2B 4-bit atomic-token cell and an
> OLMo 3 7B BF16 prefix-matched cell.

Unsupported wording includes: colored shapes have no shared geometry; the
effect disappears at 7B; quantization creates the Gemma value; OLMo encodes
color instead of shape; MLX is qualified against another backend; or a causal
glyph mechanism was found.
