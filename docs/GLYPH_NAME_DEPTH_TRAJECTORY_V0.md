# Glyph–Name Depth Trajectory v0 (T17-GN)

[日本語](GLYPH_NAME_DEPTH_TRAJECTORY_V0.ja.md) · [T9 result](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0_RESULTS.md) · [T10 result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md)

Status: **fixed design candidate; zero T17 model forwards**.

## Question

T9 prospectively confirmed that one Mistral 7B cell retrieved the correct
official Unicode name from a raw emoji surface much more accurately than it
retrieved the literal `U+...` codepoint string at the returned final hidden
state. T10 found a positive statistical signal in all nine frozen cells, but
its preregistered cross-model practical rule failed.

T17-GN asks what those final-layer snapshots do not answer:

> Across decoder depth, when does a raw emoji surface become more
> item-aligned with its official Unicode name than with its literal codepoint
> string, and is that trajectory shared across the frozen model roster?

“Glyph” in this protocol means the raw Unicode emoji surface supplied to a
text tokenizer. No model receives a rasterized font rendering, so the study
does not test visual glyph perception.

## Fixed design

- Population: the already exposed 292 T9/T10 items, without replacement.
- Views: raw emoji, official Unicode name, literal `U+...` codepoint.
- Context: the exact T10 two-carrier × four-distance grid.
- Models: the same nine exact model/tokenizer revisions used by T10.
- Depth: nine normalized fractions from `0.0` through `1.0`, resolved separately
  for each architecture.
- Acquisition: batch size one; one forward per item/view/carrier sequence; four
  suffix positions and all nine depths are read from that forward.
- Budget: 15,768 forwards and 567,648 FP32 readout vectors.

At the final fraction, the endpoint is the API-returned final hidden state and
may include final normalization. Intermediate points are the API hidden state
after the resolved decoder block. Endpoint names remain explicit.

## Frozen measurements

For each model, depth, carrier, and distance, the three view matrices are
centered separately and each row is L2-normalized. T17-GN records forward and
reverse top-1 retrieval, forward and reverse MRR, paired-minus-off-diagonal
cosine margin, and centered linear CKA for:

1. emoji ↔ official name;
2. emoji ↔ codepoint literal.

The headline descriptive curve is the equal-context mean of item-level
forward top-1 correctness for name minus codepoint. Items, with all eight
contexts kept together, are resampled 20,000 times for descriptive percentile
intervals. Initial/final values, peak depth, sustained-positive depth, depth
AUC, and model cross-sections are all fixed before acquisition.

## Interpretation branches

- **Late, shared rise:** evidence for a recurring late lexical-alignment
  trajectory in this fixed roster.
- **Different peak depths:** a model-specific alignment window, which would
  help explain why one shared final-layer practical threshold was brittle.
- **Early or flat advantage:** the final-layer effect is not well described as
  a late transformation.
- **Sparse or reversed trajectories:** T9 remains a bounded cell-specific
  result rather than a general depth phenomenon.

Every branch is informative. This is an exploratory trajectory atlas on a
prior-exposed population, not a new confirmatory test.

## Claim boundary

T17-GN can describe raw-emoji/name/codepoint geometry and its depth trajectory
in the fixed cells. It cannot establish rendered-glyph perception, human
meaning, understanding, tokenizer independence or causality, a circuit,
behavior, scale law, tuning effects, independent replication, architecture
generality, or population generality.
