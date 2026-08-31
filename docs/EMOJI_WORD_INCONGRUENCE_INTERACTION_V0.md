# Emoji × word incongruence interaction v0 (T15-A)

[日本語](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.ja.md) · [T14 result](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md)

## Frozen question

Does an externally labeled emoji-word incongruence produce a non-additive
hidden-state interaction whose steering response is more coherent or larger
than a structurally matched cross-axis interaction?

T15-A is exploratory. Its four-model roster and two late depths were chosen
after T14 exposed signed model/depth heterogeneity. It is not independent
confirmation.

## Why the experiment is factorial

Each concept axis contains two emoji and two words. All four cells are used.

| Temperature example | `hot` | `cold` |
|---|---|---|
| 🔥 | congruent | incongruent |
| ❄️ | incongruent | congruent |

Within an axis, every emoji and every word occurs once in each congruence
class. The interaction direction is

```text
mean(hidden state for the two incongruent cells)
− mean(hidden state for the two congruent cells)
```

Under a purely additive `emoji main effect + word main effect` representation,
the balanced contrast cancels exactly. A residual can therefore identify a
non-additive pair interaction without calling it semantic understanding.

## Frozen population and controls

Eight operational axes are fixed: temperature, affect, vertical direction,
day/night, evaluation, correctness, color, and volume. The labels are
experimenter-specified associations. They do not assert that a model encodes
those meanings.

Every core grid is repeated in both source orders and four common-suffix
wrapper folds. Three cyclic word-axis shifts create checkerboard interactions
with the same 2 × 2 structure but no privileged congruence interpretation.
These are structural cross-axis controls, not guaranteed semantically unrelated
pairs. Emoji-main and word-main contrasts inside the same joint grids are also
steered.

Source activations are read at the final token of a fixed wrapper suffix. A
model-specific tokenizer preflight must show that this final token ID is exact
within each source-order × wrapper group before the final execution freeze.
Token counts need not be identical, but emoji and word identities are exactly
balanced in the core contrast.

## Execution grid

- models: OLMo 2 1B base, Llama 3.2 3B base, Qwen 2.5 3B base, and Qwen 2.5 7B base;
- depths: normalized 0.875 and 1.0;
- magnitudes: 0.125 and 0.25, with 0.25 designated as the primary descriptive dose;
- signs: both;
- targets: all 32 public prestage targets;
- expected source sequences: 1,288 per model;
- expected steering responses: 98,368 per model and 393,472 total;
- generation calls: zero.

The pair, emoji-only, word-only, and empty-frame activations are captured in
the same syntax. Their frame-relative residual
`pair − emoji − word` supplies a separate source-level additivity diagnostic.

## Frozen analysis

The primary descriptive family compares cross-axis coherence of full-vocabulary
CountSketch response fingerprints from the true interaction directions against
the median of the three structural cross-axis controls. Target prompts are the
sampling clusters. All four models, both depths, both signs, and both doses
must remain visible.

Secondary complete families report:

- incongruent-minus-congruent joint-additivity residual magnitude;
- true-minus-control JS, total-variation, and logit-RMS response energy;
- true-minus-control source-direction RMS;
- word-main minus emoji-main response;
- source-order sensitivity;
- depth and dose heterogeneity.

Each reported target- or axis-level median receives a frozen 20,000-replicate
percentile interval. T15-A has no significance test and no confirmatory verdict.

## Clean landing patterns

- **shared non-additive interaction:** the balanced direction is source-stable
  and its steering fingerprint is more coherent than cross-axis controls;
- **cancellation or amplification:** incongruence changes response energy but
  does not create a common fingerprint;
- **word or emoji dominance:** one main-effect family consistently exceeds the
  other without a distinct interaction;
- **additive null:** the frame-relative residual and true-minus-control steering
  differences remain near zero;
- **heterogeneous regime:** sign, order, depth, or model changes the direction,
  consistent with T14's boundary map.

No landing authorizes meaning, contradiction detection, natural behavior, or
a causal circuit.

## Later causal gate

If T15-A yields a coherent candidate, T15-C must use new axes, a new untouched
target bank, and an independent model or backend role. The direct intervention
target would be the interaction-residual subspace itself: remove it from an
incongruent activation, add it to a congruent activation, and restore it after
removal. T15-A will not select a runner-up component or reuse its public targets
for that claim.
