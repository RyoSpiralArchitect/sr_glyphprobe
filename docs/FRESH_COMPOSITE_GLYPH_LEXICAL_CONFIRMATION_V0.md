# Fresh composite-glyph lexical confirmation v0

Status: **prospective design; zero T18 model forwards at freeze**.

Japanese companion: [FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.ja.md)

## Research question

T17 found a late-layer raw-emoji advantage over literal codepoint strings when retrieving English Emoji short names, but its 292 items had already been used in T9 and T10. T18 asks the narrower prospective question:

> On exact emoji surfaces that this repository has never presented to a model, does the late-layer representation of the raw Unicode sequence retrieve its English Emoji short name better than its literal `U+...` spelling?

This is a lexical-alignment test. It does not test rasterized glyph perception or prove that a model understands an emoji.

## What “fresh” means

Freshness is frozen before tokenization or any T18 forward.

- The exposure boundary is the complete 1,429-blob Git tree `bc114c57fb25f9d08f12bea1bdf367002506bd67` at commit `85213ea9b493682c9198eadda5e20c5e5ab2a04d`.
- A selected glyph's exact UTF-8 byte sequence occurs in none of those blobs.
- Every identity in the complete 1,111-item T11 selection is excluded, including its discovery and reserve roles.
- Only multi-codepoint sequences introduced by Emoji 13.1 or earlier are eligible.

This is an **exact-surface, repository-relative holdout**. Components, canonical families, concepts, names, and country identities can be related to prior items. The panel is not a pretraining holdout or a semantic-concept holdout.

## Frozen population

The panel contains 192 unique sequences:

| Glyph system | Items |
|---|---:|
| Modifier sequence | 64 |
| ZWJ sequence | 96 |
| Regional-indicator flag | 32 |

Skin-tone modifiers are removed only to define a canonical family. One surface is selected per family. Within each system, a SHA-256 rule chooses the family representative, then a deterministic subgroup round robin chooses the quota. Final order follows the Emoji 17 source index. Tokenizer measurements do not choose the population.

The source and labels are pinned to:

- [Unicode Emoji 17 `emoji-test.txt`](https://www.unicode.org/Public/17.0.0/emoji/emoji-test.txt), SHA-256 `1d8a944f88d7952f7ef7c5167fef3c67995bcae24543949710231b03a201acda`;
- [CLDR JSON 48.2.0](https://github.com/unicode-org/cldr-json/tree/48.2.0), with separately pinned English, Japanese, base, and derived annotation files.

## Four text views

Each item has four unique text views:

1. `glyph`: the raw Unicode codepoint sequence;
2. `english_short_name`: the Emoji 17 comment name, required to equal CLDR English `tts`;
3. `japanese_short_name`: CLDR Japanese `tts`;
4. `codepoint_literal`: uppercase, space-separated `U+...` values.

The two carriers (`" a"` and `" |"`, each repeated eight times), four suffix distances (`1, 2, 4, 8`), batch size one, and boundary checks are inherited from T10/T17. No chat template or special token is added.

## Depth collection and primary window

All nine normalized depths are collected:

`0, .125, .25, .375, .5, .625, .75, .875, 1.0`.

The primary window is fixed to `.75, .875, 1.0` because the prior-exposed T17 atlas showed the most consistent cross-model advantage there. This outcome-informed depth choice was made before any T18 activation was observed. All other depths remain secondary and cannot replace the primary window.

## Primary endpoint

For each model, depth, carrier, distance, and glyph system:

1. center each view separately across items in that glyph system;
2. L2-normalize every row;
3. perform forward top-1 item retrieval from the glyph view to the English short-name view;
4. repeat retrieval from glyph to the literal codepoint view;
5. subtract codepoint accuracy from English-name accuracy.

The model statistic is the equal-weight mean over three glyph systems and all 24 fixed late-window contexts. Candidate sets are formed separately within each glyph system, so the 96-item ZWJ stratum cannot dominate merely because it is larger.

Two components must both pass:

- **unrestricted:** all frozen items;
- **tokenization matched:** only non-singleton strata keyed by glyph system and exact `(glyph, English name, codepoint literal)` token counts.

For each component, 19,999 synchronized label permutations give `(1 + exceedances) / 20,000`. The English-name correspondence is permuted; the codepoint result remains observed and fixed. The model-level p-value is the maximum of the two component p-values. Both observed statistics must also reach the frozen practical floor `0.02`.

Tokenizer-only candidate preflight admits at least 144 matched items in every cell. The worst per-system counts are 51 modifier, 66 ZWJ, and 23 regional-flag items, above the frozen minima of 128 total and 20 per system. Every candidate tokenizer exactly replays all T10 reference sequences. The exact tokenizer bundled with each frozen model is still required to reproduce the T18 sequence hashes before its first forward.

## Cross-model decision and multiplicity

The sole cross-model primary reuses T10's four core cells:

- Llama 3.2 3B base;
- Qwen 2.5 7B base;
- OLMo 2 1B base;
- Gemma 2 2B IT.

The frozen partial-conjunction rule asks whether at least three of four core cells pass. Its Bonferroni partial-conjunction p-value is `(4 - 3 + 1)` times the third-smallest model IUT p-value, capped at one. In addition, at least three of the same core cells must each have model IUT `p <= 0.05` and pass both practical floors. This intersection rule prevents statistical support in one set of cells and practical support in another from producing a positive decision. The other five cells form a secondary nine-cell family with Holm correction and cannot rescue the primary.

The cells are not described as independent replications: they share item identities, likely training data, tokenizer ancestry, and architecture families.

## Secondary atlas

The following outputs are descriptive and cannot rescue the primary:

- Japanese short-name alignment;
- all nine depth trajectories;
- modifier, ZWJ, and regional-flag profiles;
- English-Japanese alignment;
- forward/reverse top-1, MRR, paired margin, and centered linear CKA;
- token-count histograms and matched coverage;
- Qwen size profiles and engineering metrics.

The English/Japanese contrast can help distinguish a surface-to-lexical association from an English-only label convention, but it does not by itself establish language-independent meaning.

## Outcome branches

- **Primary positive:** report exact-surface-fresh English short-name alignment in at least three of four frozen core cells. Do not call it glyph perception or understanding.
- **Unrestricted positive, matched negative:** tokenization remains a sufficient alternative explanation; retain the negative confirmatory conclusion.
- **English positive, Japanese weak:** report English-label localization and treat multilingual transfer as unresolved.
- **Both languages positive:** report multilingual lexical alignment as secondary evidence only.
- **System heterogeneity:** retain all systems and the equal-system primary; do not promote a favorable system.
- **Primary negative:** retain the complete atlas as a bounded failure to generalize from the prior-exposed T17 population.

## Execution gates

Before a model forward:

1. build and audit the public-source selection;
2. write the zero-forward design receipt;
3. run all nine tokenizer-only preflights;
4. assemble the engineering preflight;
5. freeze the config, code, tests, bilingual docs, selection, tokenizer receipts, and source bindings;
6. commit and push the freeze to `origin/main`;
7. recheck furnace availability;
8. load the exact frozen model artifact and require its T18 token sequence hashes to match the frozen preflight.

The acquisition is 13,824 model forwards and 497,664 stored readout vectors. Completed 32-item shards are immutable. Foreign GPU contention yields before the next shard. Activations remain in furnace scratch and are not committed to Git.

## Commands

```bash
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py audit-selection
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py audit-freeze --require-pushed
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py run-role \
  --model-label MODEL_ROLE --model-path MODEL_SNAPSHOT --output-root RUN_ROOT
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py summarize-role \
  --model-label MODEL_ROLE --output-root RUN_ROOT --summary-root SUMMARY_ROOT
python scripts/fresh_composite_glyph_lexical_confirmation_v0.py analyze \
  --summary-root SUMMARY_ROOT --output ANALYSIS_ROOT
```

The YAML config and JSON freeze manifest are authoritative when prose and executable checks differ.
