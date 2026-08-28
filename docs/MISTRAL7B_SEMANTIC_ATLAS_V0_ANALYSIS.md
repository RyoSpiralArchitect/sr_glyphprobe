# Mistral 7B semantic atlas v0 analysis plan

[日本語](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.ja.md) · [Acquisition protocol](MISTRAL7B_SEMANTIC_ATLAS_V0.md)

Status: **frozen after acquisition integrity finalization but before inspecting
activation values, before the fixed recapture forwards, and before descriptive
analysis**. Because the raw atlas already exists, this is a post-acquisition
descriptive plan, not a confirmatory preregistration.

## Capture validation

The acquisition used batch size 64 and read four causal positions from each
unique input forward. A fixed engineering validation recaptures acquisition
indices `[0, 445, 891]`, all three views, and both carriers at batch size one.
This is 18 acquired sequences and zero reserve sequences. Every case compares
all four distances and nine layers against the stored FP32 tensor.

A case passes only when all 36 vectors satisfy the aggregate case bounds:

- minimum cosine at least `0.999999`;
- maximum relative RMS error at most `0.001`;
- maximum absolute element error at most `0.125`.

All 18 cases must pass. This is an engineering equivalence check. It does not
validate any semantic interpretation.

## Populations

The descriptive analyzer reports the 50 prior-exposed calibration items and
842 unseen discovery items separately. It never loads or forwards the 292-item
reserve. There is no post-outcome item filtering. Every carrier, distance, and
fixed layer is reported, giving 72 cells per population and 144 cell rows.

## Centering and paired retrieval

Within each population/view/carrier/distance/layer cell, subtract the
feature-wise mean across items, then L2-normalize every item vector. For each of
the three view pairs—glyph/name, glyph/codepoint, and name/codepoint—form the
complete cross-view cosine matrix.

Report paired diagonal cosine, off-diagonal mean, their margin, top-1 paired
retrieval in both directions, mean reciprocal rank in both directions, and
centered linear CKA. A rank counts only strictly greater similarities ahead of
the paired item; exact ties are therefore optimistic and disclosed.

The direct semantic-anchor contrast is the glyph/name metric minus the matching
glyph/codepoint metric. It is descriptive: no threshold, p-value, multiplicity
decision, or favorable-cell selection is authorized.

## Neighborhood structure

For each view separately, find the ten nearest other items by centered cosine.
Report Unicode group and subgroup neighbor purity with the corresponding
finite-population random-pair baselines. Calibration uses `k=10` as well; if a
future population has ten or fewer items, `k` becomes `n-1`.

## Complete outputs

The analyzer retains:

- 144 complete population-by-carrier-by-distance-by-layer rows;
- one paired-cosine row per acquired item and cell, including all three exact
  token counts and Unicode labels; and
- 18 equal-weight layer summaries, averaging the fixed two carriers and four
  distances without selecting a favorable cell.

The raw approximately 3 GiB atlas and item-level analysis stay outside Git.
Compact receipts, all cell rows, layer summaries, validation evidence, and
bilingual results may be published.

## Claim boundary

Large glyph/name retrieval or CKA relative to the codepoint view would make a
semantic-alignment hypothesis sharper. It would not establish that the model
stores a disentangled emoji meaning, that tokenizer structure is causally
removed, or that the effect generalizes. The untouched reserve exists so one
later endpoint can be chosen from these descriptive results and evaluated
prospectively.
