# Glyph-System Decomposition Atlas v0 results (T11)

[日本語](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.ja.md) · [Frozen protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [Compact evidence](../artifacts/glyph_system_decomposition_v0/README.md) · [T10 result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md)

Status: **completed exploratory discovery atlas; share with caveats**.

The most defensible reading is not one universal emoji-meaning axis. Matched
glyph-to-name correspondence is broad, but the way it decomposes differs by
glyph system and model cell. Regional flags show the clearest coexistence of a
whole-sequence name relation and a component relation. ZWJ sequences show a
smaller but unusually stable fused-form advantage while remaining at least as
close to component labels as to official whole-sequence names. Modifier
sequences have broad matched alignment but nearly zero decomposition
contrasts. Keycaps are noisy at eight discovery items.

This is an exploratory atlas, not a confirmatory result. It does not establish
emoji meaning, understanding, causality, a mechanism, behavioral relevance,
tokenizer independence, a scale law, an instruction-tuning effect,
architecture or model generality, or independent replication. It cannot rescue
or alter T10.

## Acquisition and validation

The protocol was frozen at commit
`1602749815cf8007588024f89497cc5646de9f54`; its outcome-independent core hash
is `5ef2e31e7bd04f079426d84db1f3437ee2d6278ff47f587826943a5101324f94`.
All nine tokenizer and artifact preflights completed before model loading. The
aggregate preflight SHA-256 is
`16484d7fa3504ddfdd9ffefc441d3270f506dc485728b7655a5ee9c2f3c8d2ff`.

All nine frozen model/tokenizer cells completed 53 shards and 8,174 unique
forwards each. The acquisition therefore contains:

- 843 acquired items and 4,087 available item-view pairs;
- 477 complete shards;
- 73,566 model forwards;
- 588,528 broad and 393,984 depth readout vectors, or 982,512 total FP32
  vectors;
- zero interventions and zero generations.

The joint analysis added zero model forwards. The 268-item reserve received
zero model forwards and its model outcomes remain uninspected. The source
analysis ledger SHA-256 is
`8f03aa191715c96ee980fe47e9a51f85ea651c4d619d9c46af345815ea6ca07a`.

An independent validator that does not import the T11 analyzer rehashed the
analysis, preflight, and nine summary bundles. It then recomputed 32,736 stored
item-margin cell medians, 720 model-pair agreement rows, seven balanced
three-way variance decompositions, and 2,592 depth trajectories. There were
zero mismatches at a tolerance of `1e-12`.

Cross-model activation geometry was hash- and schema-checked but not rebuilt
from raw vectors: that requires the omitted approximately 9.15 GiB activation
archive. The full item-bootstrap family was not independently resampled,
although every interval used by the depth tables was reconciled. These two
limits are why the validation rating is “share with caveats,” not an
independent replication.

## Required token-length controls passed

Every required wrong-label control stayed inside an exact target-token-count
stratum. Across the nine tokenizers, minimum required coverage ranged from
`0.8750` for keycap Unicode names to `1.0000` for several system/view cells;
every required cell exceeded the frozen `0.75` gate.

The stricter sensitivity additionally matched the first target token ID. Its
coverage was intentionally ungated and sharply uneven: median coverage was
`0.1406` for atomic anchors, `0.1938` for presentation sequences, `0.7240` for
modifiers, `0.8711`--`0.8789` for ZWJ views, `0.9938`--`1.0000` for regional
flags, and `0.8750` for keycaps. It is therefore informative for ZWJ and
regional flags but low-powered for anchors and presentation sequences.

At the returned final state, the required matched glyph-to-official-name
advantage had a positive cell median in all 72 model × context cells for the
four larger multi-codepoint systems:

| Glyph system | Items | Median cell margin | Positive cells | Descriptive intervals above zero |
|---|---:|---:|---:|---:|
| Atomic anchor | 64 | 0.1134 | 72/72 | 55/72 |
| Presentation | 160 | 0.1327 | 72/72 | 71/72 |
| Modifier | 192 | 0.0548 | 72/72 | 64/72 |
| ZWJ | 256 | 0.0778 | 72/72 | 70/72 |
| Regional flag | 160 | 0.1141 | 72/72 | 64/72 |
| Keycap | 8 | 0.0909 | 65/72 | 24/72 |

The first-token sensitivity attenuated the median glyph/name advantage to
`0.0313` for presentation, `0.0119` for modifiers, and `0.0507` for ZWJ. ZWJ
still had 68/72 descriptive intervals above zero. Regional flags retained a
median of `0.1141` and 66/72 intervals above zero. Within the available matched
coverage, these results are inconsistent with the narrow account that the
entire ZWJ and regional-flag pattern is created by target token count or the
first target token. They do not establish tokenizer independence, and the
low-coverage presentation and anchor sensitivities must not be overread.

## The decomposition is system-specific

The three frozen operational contrasts use correct-label minus
token-length-matched wrong-label margins. Positive values mean:

- `lexicalization`: glyph-to-official-name exceeds glyph-to-component-name;
- `presentation_or_fusion`: glyph-to-official-name exceeds
  decomposed-form-to-official-name;
- `component_tracking`: decomposed-form-to-component-name exceeds
  glyph-to-component-name.

Returned-final-state cell distributions were:

| System | Contrast | Median | Positive cells | Interval + / − / includes 0 |
|---|---|---:|---:|---:|
| Presentation | presentation/fusion | 0.0139 | 52/72 | 25 / 3 / 44 |
| Presentation | component tracking | -0.0051 | 28/72 | 2 / 17 / 53 |
| Modifier | lexicalization | 0.0005 | 37/72 | 6 / 2 / 64 |
| Modifier | presentation/fusion | -0.0010 | 32/72 | 2 / 1 / 69 |
| Modifier | component tracking | 0.0003 | 37/72 | 9 / 4 / 59 |
| ZWJ | lexicalization | -0.0127 | 23/72 | 2 / 9 / 61 |
| ZWJ | presentation/fusion | 0.0142 | 65/72 | 31 / 0 / 41 |
| ZWJ | component tracking | -0.0040 | 26/72 | 4 / 9 / 59 |
| Regional flag | lexicalization | 0.0495 | 47/72 | 35 / 11 / 26 |
| Regional flag | presentation/fusion | 0.0668 | 59/72 | 43 / 0 / 29 |
| Regional flag | component tracking | 0.0441 | 58/72 | 36 / 3 / 33 |
| Keycap | lexicalization | 0.0030 | 38/72 | 1 / 2 / 69 |
| Keycap | presentation/fusion | -0.0090 | 33/72 | 10 / 6 / 56 |
| Keycap | component tracking | -0.0399 | 28/72 | 7 / 7 / 58 |

Presentation-sequence official and component names are identical by
construction, so their lexicalization contrast is structurally uninformative
and is omitted from the table. The modest positive presentation/fusion value
instead compares the fully-qualified form with the same scalar sequence after
removing VS15/VS16.

Modifier official and component labels contain nearly the same lexical content
with different separators, and all three contrasts are centered near zero.
This is a bounded null for decomposition contrasts, not a null for matched
glyph/name alignment.

For ZWJ sequences, the fused glyph has a small, stable advantage over the
space-separated decomposition for its official name. At the same time,
`lexicalization` and `component_tracking` are slightly negative. The clean
description is therefore a fusion-sensitive relation layered on strong
component-label affinity, not generic dominance of a lexicalized official
name.

Regional flags show the clearest dual structure. The fused flag favors the
official place name over both the ASCII two-letter decomposition and the
component label, while the ASCII decomposition favors the letter-component
label over the fused glyph. Direction still varies by model cell, so this is a
system-specific candidate rather than a model-general semantic result.

Keycap discovery has only eight items. Its large ranges and mostly
zero-including intervals support no stable decomposition pattern. The three tag
flags remain a bounded microcase with no matched-control claim.

## Model-conditioned regimes dominate pooling

The returned-final matched glyph/name margin has sizable model and system main
effects, but the operational decomposition contrasts are dominated by
interactions. Shares of balanced total sum of squares were:

| Metric | Model | System | Context | Model × system | Model × context | System × context | Three-way |
|---|---:|---:|---:|---:|---:|---:|---:|
| Matched glyph/name | 26.1% | 19.3% | 2.2% | 19.9% | 9.8% | 2.5% | 20.3% |
| Lexicalization | 2.7% | 3.5% | 1.4% | 27.4% | 10.4% | 4.1% | 50.5% |
| Presentation/fusion | 10.2% | 21.5% | 1.2% | 20.4% | 9.1% | 3.8% | 33.8% |
| Component tracking | 5.2% | 15.0% | 0.2% | 34.9% | 7.8% | 5.7% | 31.2% |

These are descriptive sums of squares, not random-effects inference. They show
why a pooled “compositional versus lexicalized” verdict would be misleading.

Cross-model agreement on which individual items have larger matched margins is
also low. The median of the 36 model-pair Spearman values, summarized again
across the eight contexts, was `0.0786` for presentation, `0.0670` for
modifiers, `0.1185` for ZWJ, `0.1158` for regional flags, and `0.0089` for
keycaps.

Per-view geometry is more shared than the cross-view mapping, and text views
are more shared than glyph views. At the returned final state, median
cross-model glyph CKA was `0.1809` for presentation, `0.2018` for modifiers,
`0.3645` for ZWJ, and `0.1941` for regional flags. The corresponding official
name values were `0.3594`, `0.3826`, `0.5347`, and `0.4059`. This continues
T10-D's descriptive observation that model divergence is strongest on the
glyph side. It does not rank models by semantic content.

Only eight of 36 system × metric profiles were strictly increasing across the
four Qwen base checkpoint sizes. This is not a scale law.

## Depth and the final-normalization boundary

The embedding readout is zero by construction because all views are followed
by the same carrier token before any contextual mixing. Matched glyph/name
intervals first excluded zero at the quarter-depth readout in 31/72
presentation trajectories, 15/72 modifier trajectories, 15/72 ZWJ
trajectories, and 17/72 regional-flag trajectories. Across all six depth
readouts, 54/72 presentation, 33/72 modifier, 63/72 ZWJ, and 60/72
regional-flag trajectories first excluded zero in the positive direction.
These are descriptive emergence locations across architecture-normalized
depth, not mechanistic sites.

The median returned-final minus raw-last-block change in the depth subset was
small: `+0.0077` for presentation glyph/name margins, `-0.0021` for modifiers,
`+0.0012` for ZWJ, and `+0.0016` for regional flags. Contrast deltas were also
near zero in aggregate. Individual model/system cells change in both
directions, but T11 does not support one pooled final-normalization effect.

## Retrieval is broad enough to analyze and still concentrated

At the returned final state, median forward top-1 glyph-to-name retrieval was
`0.0813` for presentation, `0.0365` for modifiers, `0.0488` for ZWJ, and
`0.0813` for regional flags. Median retrieval breadth was `0.4437`, `0.3958`,
`0.3438`, and `0.4375`, respectively; median top-decile concentration was
`0.5062`, `0.5677`, `0.6465`, and `0.4938`.

The atlas is therefore not explained by every query collapsing onto one name,
but retrieval remains concentrated, especially for ZWJ. Minimum top-1 is not a
T11 decision metric and cannot revise T10.

## Landing pattern and the clean next test

No single authoritative landing pattern is selected. The data support a
coexistence of:

1. broad matched glyph/name alignment after exact token-length controls;
2. a ZWJ fusion-sensitive candidate;
3. a regional-flag dual whole-sequence/component candidate;
4. model-conditioned regimes with weak item-level agreement;
5. bounded decomposition nulls for modifiers and keycaps.

If T12 is narrowed to one question, the least diffuse candidate is the ZWJ
`presentation_or_fusion` contrast at the returned final hidden state. It is
positive in 65/72 discovery cells, has no cell-level descriptive interval
strictly below zero, and has a positive eight-context median in eight of nine
model cells. Six model cells are positive in all eight contexts. The ZWJ
reserve has 96 items.

That observation does not itself freeze T12. Before any reserve forward, T12
must specify the model-cell family, practical floor, context rule,
multiplicity procedure, required and strict-prefix controls, and the exact
handling of model heterogeneity. Regional-flag component tracking is a useful
secondary option, but combining it with the ZWJ endpoint would create a wider
family and should be a deliberate design choice.

## Reproduce and audit

With the returned compact analysis, nine summary directories, and tokenizer
preflight directory available:

```bash
python scripts/validate_glyph_system_decomposition_v0_result.py \
  --analysis path/to/t11-analysis \
  --summaries-root path/to/t11-summaries \
  --preflight path/to/t11-preflight \
  --output path/to/new-independent-validation
```

The Git-resident compact bundle can be checked without external data:

```bash
python scripts/package_glyph_system_decomposition_v0_public_bundle.py validate \
  --bundle artifacts/glyph_system_decomposition_v0
```

The public manifest binds every included file, the three omitted compact
tables, the nine summary bundles, the nine run receipts, and the preflight.
Hashes provide provenance but do not reconstruct omitted raw activations.
