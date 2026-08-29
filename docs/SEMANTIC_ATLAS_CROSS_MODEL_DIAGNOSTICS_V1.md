# Semantic Atlas Cross-Model Diagnostics v1 (T10-D)

[日本語](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.ja.md) · [T10 result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [T10 protocol](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md)

Status: **completed retrospective diagnostic; T10 primary unchanged**.

T10-D asks what kind of heterogeneity sits underneath T10's registered negative
cross-model decision. It uses no new model forward. The committed analyzer
rehashes the compact T10 bundle and, when the returned raw archive is supplied,
reconstructs every retrieval prediction directly from FP32 activations.

## The decision that does not change

T10 remains
`cross_model_replication_not_established_under_frozen_rule`. Its statistical
partial-conjunction test passed at `p = 0.0001`, but only two of four core cells
met both frozen practical floors. This analysis does not lower the `0.02`
floor, replace a core model, promote an extension model, or let the raw
last-block endpoint rescue the registered final-state endpoint.

At `n = 292`, a top-1 contrast of `0.02` is a discrete boundary of six net
correct items in every carrier-distance cell. Gemma and OLMo each passed seven
of eight unrestricted cells; their weakest cells contained five and four net
correct items, respectively. That explains why a smooth positive profile can
still fail the frozen minimum-cell rule. It does not make the failure an error.

## Context profiles are model-specific

The eight-cell carrier-distance contrast profiles do not share one common
bottleneck. Across 36 model pairs, their Spearman correlations have median
`-0.162`, ranging from `-0.755` to `0.610`. Across models, the median shares of
within-profile sum of squares are:

- carrier: `0.198`;
- distance: `0.266`;
- carrier-by-distance interaction: `0.299`.

The weakest cell therefore cannot be chosen once and treated as a universal
context. T11 must retain the full fixed context grid and summarize stability,
not select a favorable carrier or distance after seeing outcomes.

## Support is broad in aggregate and concentrated within models

Name retrieval succeeds at least once for 233 of 292 items when all nine
models and eight contexts are pooled. Only 14 items succeed in at least six
models, and no item succeeds in all nine. Pairwise item-advantage correlations
have median `0.133` and range from `-0.063` to `0.327`.

Within-model concentration is substantial. The top ceiling-10% of items
accounts for `0.374` of Mistral-Instruct's name hits, but `0.841` for Llama,
`0.973` for OLMo, and all of SmolLM2's hits. A single minimum top-1 value hides
this breadth-versus-concentration distinction.

## Retrieval metrics agree more than geometry does

All 72 returned-final-state cells have positive glyph/name-minus-codepoint
top-1, MRR, and paired-minus-off-diagonal margin contrasts. Centered linear CKA
is positive in only 33 of 72 cells. Across the nine model cells, the ranking of
minimum top-1 contrast correlates `0.971` with median MRR contrast, `0.802` with
mean paired-margin contrast, and `0.810` with mean CKA contrast. CKA therefore
contains related but non-equivalent information.

Codepoint text is also a weak comparator: mean name top-1 is `0.0738`, mean
codepoint top-1 is `0.00566`, and codepoint top-1 is zero in 13 of 72 cells.
T11 retains codepoint text as one view but adds system- and tokenizer-matched
incorrect-name controls. Codepoint text is not its sole negative control.

## The Qwen profile is not a scale law

The four aggregate Qwen minimum contrasts increase in checkpoint-size order:
`0.00685`, `0.01370`, `0.01712`, and `0.02397`. At item level, however, only
three of 292 trajectories are strictly increasing. Among the 182 items with a
finite four-point Spearman coefficient, the median is `0.632` and `72.5%` are
positive. Size remains confounded with each released checkpoint. The profile
is useful for T11 stratification, not for a scale-law claim.

## Raw reconstruction and the final-norm boundary

The analyzer revalidated 333 raw shards, reconstructed 36 full prediction
arrays, and compared 84,096 prediction values with the compact bundle. There
were zero mismatches. The maximum absolute top-1 contrast error was
`1.51e-08`.

Final-versus-raw within-model item-geometry CKA has median `0.836` for Gemma and
`0.893` for Qwen 3B, versus `0.939`–`0.980` for the other seven cells. The
eight-cell final/raw top-1 profile correlation is `-0.335` for Qwen 0.5B but
`0.847`–`0.957` for Gemma, Llama, Mistral, OLMo, and Qwen 7B. Final
normalization is therefore a real, model-conditioned analysis boundary rather
than a naming detail.

Across model pairs, the median of each pair's eight final-state item-geometry
CKAs is `0.132` for glyphs, `0.362` for Unicode names, and `0.423` for codepoint
text. The most pronounced cross-model divergence is on the glyph side. This is
a descriptive representational result, not evidence that one model has more or
less emoji meaning.

## What T10-D authorizes for T11

T10-D supports a new exploratory design with:

- continuous, item-level matched-label cosine margins and MRR;
- retrieval breadth and concentration, not only a cell minimum;
- all two-carrier by four-distance contexts with a stability summary;
- raw last-block and returned-final-state endpoints in every item;
- a frozen, structure-balanced subset for normalized-depth trajectories;
- cross-model item geometry separated by glyph system and text view.

It authorizes no semantic, causal, tokenizer-independence, scale, tuning, or
model-general claim. T11 must remain a new lane and leave T10 intact.

## Reproduce

From the repository root, with the returned T10 raw run directories available:

```bash
python scripts/analyze_semantic_atlas_cross_model_diagnostics_v1.py analyze \
  --raw-runs path/to/glyphprobe-t10-runs-8673bc51 \
  --output path/to/new-diagnostic-output

python scripts/analyze_semantic_atlas_cross_model_diagnostics_v1.py validate \
  --output path/to/new-diagnostic-output
```

The compact, hash-bound output is in
[`artifacts/semantic_atlas_cross_model_diagnostics_v1/`](../artifacts/semantic_atlas_cross_model_diagnostics_v1/README.md).
