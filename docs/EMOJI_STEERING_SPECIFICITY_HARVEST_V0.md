# Emoji Steering Specificity Harvest v0 — T13-EH protocol

[日本語](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.ja.md) · [T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T12 result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [Roadmap](ROADMAP.md)

Protocol ID: `glyphprobe-emoji-steering-specificity-harvest-v0`

Freeze-time status: **static protocol; zero T13-EH model forwards before the
manifest was created**. Runtime progress belongs to hash-bound role receipts,
not to this narrative document.

T13-EH makes a resource-ordering decision, not a scientific decision. It
acquires the GPU-dependent tensors now and defers analysis, visualization,
multiplicity choices, and paper writing to CPU or MPS. The acquisition has no
primary hypothesis, practical floor, or confirmatory verdict.

## Why acquire before writing

The furnace window can close for reasons unrelated to GlyphProbe. Model
forwards are the least portable part of the next study; most geometry,
matching, resampling, plotting, and writing can be performed later on either
Mac. A fixed, reusable response tensor therefore has greater option value than
one quickly chosen figure.

Resource availability may change only queue order, batch size, and completed
shard boundaries. It cannot change the item population, model roster, source
forms, wrappers, targets, depths, signs, strengths, endpoints, or stopping
rule. No intermediate scientific outcome is inspected while the queue runs.

## Relationship to T11 and T12

T13-EH uses exactly the 192-item T11 depth population. Every item was already
forwarded in T11. It does not consume the remaining unused T11 presentation,
modifier, or keycap reserves. The complete T12 ZWJ and regional reserves are
not used to select T13-EH items or endpoints.

The study does not reopen T12. T12's registered hypotheses remain unconfirmed.
T13-EH is a new exploratory source-form and intervention harvest motivated by
the broader question that T12 leaves open.

## Fixed population and public targets

The population contains 192 items in ascending frozen T11 depth index:

| glyph system | items |
|---|---:|
| atomic anchor | 24 |
| presentation sequence | 24 |
| modifier sequence | 40 |
| ZWJ sequence | 56 |
| regional flag | 40 |
| keycap | 8 |

All available T11 forms are retained: glyph, official Unicode name,
deterministic component name, codepoint literal, and deterministic decomposed
form. Atomic anchors have three forms; the other systems have five. This gives
912 item-form rows.

The target set is all 32 already public rows in `prestage_targets.jsonl`, in
file order. T13-EH must not open, tokenize, forward, or score P2 or retired C1
v1. It performs no generation.

## Fixed source bank

Four already public wrappers are selected before outcomes:

- `w01_mark_anchor`
- `w04_token_state`
- `w10_sequence_continuation`
- `w15_observation_inference`

For each item form and depth, the stored wrapper delta is the raw decoder-block
output at the wrapper's last token with the source prefix minus the same bare
wrapper output. The mean direction is the equal-wrapper average of the four
deltas. The eight normalized depth fractions are
`[0.125, 0.25, 0.375, 0.50, 0.625, 0.75, 0.875, 1.0]`, mapped to
`max(0, floor(fraction × num_layers) - 1)`.

All nine T10–T12 model/tokenizer roles acquire the source bank and all 32 target
baselines. Per model this stores:

- 29,184 full FP32 wrapper-delta vectors;
- 7,296 full FP32 mean-direction vectors;
- 256 full FP32 target-activation vectors; and
- 32 complete FP32 baseline next-token logit vectors.

Across nine models the source bank contains 330,624 stored activation vectors.
It requires 33,156 unique forward sequences, evaluated in resource-sized
batches without changing the sequence population.

## Fixed three-model intervention pilot

The pilot roles were chosen before outcomes to cover a small base model, a
3B-class base model, and a 7B-class base model:

1. `qwen25_0p5b_base_bf16`
2. `llama32_3b_base_bf16`
3. `qwen25_7b_base_bf16`

Every intervention is added at the target's last token at the selected raw
decoder-block output. A direction is normalized to unit RMS and multiplied by
`signed magnitude × target activation RMS`.

The pilot has four complete grids per model:

| grid | fixed scope | rows/model |
|---|---|---:|
| item source form | 552 glyph/name/decomposed directions × 32 targets × two signs at depth 0.50 and magnitude 0.25 | 35,328 |
| system-form prototype | 28 unit-item-balanced prototypes × 8 depths × 3 magnitudes × 2 signs × 32 targets | 43,008 |
| random null | 64 deterministic isotropic draws × 8 depths × 3 magnitudes × 32 targets | 49,152 |
| zero hook | 8 depths × 32 targets, exact no-op required | 256 |
| **total** | complete fixed pilot | **127,744** |

The three-role response tensor therefore contains 383,232 intervention rows.
Each batched intervention call carries its own zero-vector guard row so that
the comparison baseline uses the same target, batch shape, and numerical path.

## Stored response surface

For every intervention row the ledger records condition identity, item or
prototype provenance, source form, system, target, depth, block, magnitude,
sign, KL divergence, Jensen–Shannon divergence, total variation, baseline and
intervened entropy, logit-delta RMS, and top-1 change.

To preserve future analysis options without storing hundreds of thousands of
full-vocabulary logit vectors, each row also stores:

- the 64 largest positive logit deltas;
- the 64 largest negative logit deltas; and
- a deterministic 256-dimensional CountSketch of the complete logit-delta
  vector.

The complete baseline logits are stored once per target and model. Raw source
and response arrays stay on the furnace. They are hash-bound but are not
committed to Git or placed on SpiralShare.

## Resume and contention policy

Source acquisition is split into twelve 16-item shards per model. Pilot item
responses use the same twelve shards; prototype responses are split by glyph
system and random controls by depth. Every completed shard is immutable and
validated before the next starts.

An incomplete staging directory requires manual adjudication. It is never
silently deleted or treated as complete. The runner checks for foreign GPU
processes before model load and before each new shard. If contention appears,
it writes a yield receipt and exits with code 75 without starting another
shard. It never pauses, kills, or modifies another workload.

A role may receive an explicit host-local model path when the same pinned
snapshot lives outside the default cache. The path grants no identity by
itself: the runner accepts it only when file count, total bytes, and artifact
manifest hash exactly match the T10 binding and the committed tokenizer
receipt.

## Later CPU/MPS work

No outcome analysis is part of acquisition. After the GPU queue closes, the
stored tensors can support:

- tokenizer-signature-matched source-form comparisons;
- item, system, target, depth, model, dose, and sign heterogeneity;
- positive/negative antisymmetry and nonlinear dose diagnostics;
- target entropy and top-two-margin sensitivity;
- top-delta and CountSketch semantic-probe exploration; and
- bounded supplementary figures or a future-work selection rule.

Any later T13-C confirmation must create a new untouched target bank and a new
freeze. T13-EH observations cannot enter its test statistic.

## Claim boundary

T13-EH is an exploratory acquisition-only dataset. Even a visually striking or
cross-model-consistent pattern cannot by itself establish emoji meaning,
understanding, unique emoji specificity, a causal mechanism, behavioral
steering, tokenizer independence, a scale law, an instruction-tuning effect,
architecture or model-population generality, or independent replication. Null,
heterogeneous, and failed shards are retained under the same boundary.
