# Prospective emoji × word incongruence replication v0 (T15-B)

[日本語](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md) · [T15-A result](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md)

## Frozen question

T15-A found a response-fingerprint coherence excess in all 16 primary
model × depth × sign cells. Does that operational effect recur when the axes,
targets, and model roles are all replaced?

T15-B is a prospective holdout replication of that narrow response-shape
candidate. It is not a test of whether a model understands emoji, words, or
contradiction.

## What is replaced

Nothing from the T15-A scientific population is reused.

- eight new, mostly descriptive axes: speed, size, openness, weight, moisture,
  texture, distance, and fullness;
- 16 new emoji and 16 new words;
- a new 48-prompt synthetic continuation bank, frozen as six groups of eight;
- two model roles absent from T15-A: SmolLM2 1.7B base and Mistral 7B
  Instruct v0.3.

The model roster is fixed for boundary coverage, not sampled from a model
population. One role is a compact base checkpoint; the other is a distinct 7B
architecture with instruction tuning. A result shared by both would still not
establish architecture or instruction-tuning invariance.

## Factorial contrast and stronger controls

Each axis retains the balanced 2 × 2 emoji × word grid. Every emoji and every
word appears equally often in the congruent and incongruent classes, so an
additive emoji-main-plus-word-main representation cancels from the interaction
contrast.

T15-A used three cyclic cross-axis shifts. T15-B retains all seven non-self
shifts. Every emoji axis is therefore paired with every other word axis under
the same checkerboard structure. The `positive` and `negative` names are
arbitrary pole labels, not valence labels. Using mostly descriptive axes and
all cross-axis partners directly tests whether the T15-A recurrence depended
on a favorable evaluative orientation or selected control pairing.

Both source orders and all four wrapper folds remain. The same two late depths,
two doses, both steering signs, zero-hook checks, emoji-main controls, and
word-main controls remain visible.

## Frozen execution grid

- model roles: 2;
- new axes: 8;
- untouched targets: 48;
- source prompts: 2,312 per model;
- source-metric rows: 4,096 per model;
- direction-catalog rows: 1,280 per model;
- steering-response rows: 245,856 per model and 491,712 total;
- depths × doses × signs: 2 × 2 × 2;
- cross-axis shifts: 7;
- generation calls: 0.

Target activation RMS is reacquired from the new bank inside T15-B. No public
T15-A target baseline is reused. Prompt bodies remain in the frozen Git bank;
external runtime receipts contain IDs and hashes rather than prompt bodies.

## Primary replication gate

The source statistic is the T15-A A1 estimand: full-vocabulary CountSketch
response coherence across the eight true interaction axes minus the median
coherence across structural cross-axis controls.

At magnitude `0.25`, T15-B first computes the paired A1 value for each target,
depth, and sign. For each model and target, it then takes the median over the
two depths and two signs. The 48 target-level values are the bootstrap units.

Replication support requires the 2.5th percentile of the frozen 20,000-draw
target bootstrap to exceed zero for **both** model roles. This is a two-model
intersection rule with one-sided Bonferroni alpha `0.025` per model and family
alpha at most `0.05`. Models are not pooled for the decision. All cell-level
results and the complete secondary families remain reportable regardless of
the gate.

## Clean landing patterns

- **gate passes in both models:** the operational response-shape candidate
  prospectively generalizes to the replaced axes and target bank in both frozen
  roles;
- **one-model boundary:** the effect recurs only in one frozen role and remains
  model-conditional;
- **axis/control collapse:** exhaustive cross-axis controls absorb the T15-A
  excess;
- **target collapse:** the effect does not survive the new continuation bank;
- **signed or depth heterogeneity:** pooled results hide opposing cells, which
  remain visible and block a stronger claim.

No landing authorizes a semantic, behavioral, causal-circuit, tokenizer,
scale-law, or model-population claim.

## T15-C remains separate

T15-B does not intervene on an inferred interaction subspace. Only after it
closes may T15-C freeze necessity, sufficiency, and restoration tests on a
prospectively defined interaction-residual subspace. T15-C may not rescue a
negative T15-B result by selecting a runner-up component from these outcomes.

## Pre-outcome status

This document, the panel, target bank, implementation, tests, tokenizer
receipts, and final manifest must be committed before the first T15-B model
forward. Scientific values remain closed until both frozen model roles pass
the complete run audit.
