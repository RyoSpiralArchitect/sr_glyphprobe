# Emoji Steering Specificity Expansion Analysis v0

[Japanese / 日本語](EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.ja.md) ·
[T14-X acquisition](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md) ·
[T14-C causal path](EMOJI_STEERING_CAUSAL_PATH_V0.md)

Protocol ID: `glyphprobe-emoji-steering-specificity-expansion-analysis-v0`  
Experiment label: **T14-XA**

T14-XA fixes the complete exploratory analysis before any T14-X scientific
value is opened. The acquisition must first validate all six models and all
559,488 response records. Partial-model inspection is forbidden.

## Headline estimand

For every model, depth, target, and endpoint, T14-XA takes the median response
over the 48 signed glyph-view wrapper-holdout system prototypes and subtracts
the median response over the 128 signed source-covariance nulls. The principal
unit is the target prompt, so the reported population statistic is the median
of 32 target-level differences—not a row-level pseudo-replicated mean.
Because primitive argmax-flip rows are binary, that endpoint alone uses a mean
within target before the same target-level median; all other endpoints use the
within-target median.

## Complete families

The same fixed executable must report all seven families:

1. overall structured glyph prototypes versus covariance nulls;
2. that contrast separately for all six glyph systems;
3. glyph prototype versus every available non-glyph prototype source form;
4. matched item-level glyph versus Unicode-name and decomposed-form directions;
5. depth 0.875 versus depth 1.0 for the headline target estimand;
6. Gaussian versus Rademacher covariance-null sensitivity; and
7. positive versus negative structured-direction orientation.

Every table includes all six models, both depths, all endpoints, negative or
mixed cells, and a target-cluster 20,000-replicate percentile interval. These
intervals are descriptive stability summaries; T14-XA runs no significance
test and has no confirmatory decision rule.

## Scientific-open boundary

The analyzer first audits its own freeze, then calls the T14-X six-role run
auditor. Only after both pass may it read scalar response ledgers. It never
loads prompts, activation banks, tokenizers, models, top-k logit arrays, or
CountSketch values. A failed or incomplete run remains closed.

## Claim boundary

T14-XA may show that the frozen target set exhibits a stable and cross-model
structured-versus-null response pattern. It cannot by itself establish emoji
meaning, understanding, a unique circuit, causality, tokenizer independence,
architecture or model-population generality, or a scale law. T14-C is the
separate causal gate.
