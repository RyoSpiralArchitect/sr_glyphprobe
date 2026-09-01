# T18 fresh composite-glyph lexical confirmation results

[日本語](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.ja.md) · [Frozen protocol](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md) · [Primary result](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/cross_model_primary_result.json) · [Independent validation](../validation/fresh_composite_glyph_lexical_confirmation_v0/independent_validation.json) · [Paper story](PAPER_STORY_T18_FRESH_LEXICAL_V0.md)

Status: **prospectively frozen primary confirmed within the registered model cells**.

## Result in one paragraph

Raw multi-codepoint emoji sequences whose exact UTF-8 surfaces had never
appeared in the frozen study repository became better item-level keys for their
English Emoji short names than for their literal `U+...` strings. All four
frozen core model/tokenizer cells passed both the unrestricted and exact
token-count-matched components, including the `0.02` practical floor. The
registered `r = 3 of 4` partial-conjunction test therefore passed at
`p = 0.0001`. Eight of all nine registered cells met the same bounded
statistical-plus-practical rule; SmolLM2 was the exception because its
unrestricted contrast was `0.017940`, below the frozen floor. The aggregate
relation was broad, but its implementation was not universal: peak depth,
global CKA, and the item roster differed substantially among models. The
bounded contribution is **exact-surface-fresh lexical binding in text-codepoint
sequence representations**, not rendered-glyph perception, pretraining
holdout, human-like meaning, or a shared mechanism.

![Fresh composite-emoji lexical trajectories](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/secondary/depth_curves.svg)

## Registered population and contrast

The panel contained 192 fixed multi-codepoint sequences: 64 modifier
sequences, 96 ZWJ sequences, and 32 regional-indicator flags. Their exact
UTF-8 surfaces were absent from all 1,429 regular blobs in Git tree
`bc114c57fb25f9d08f12bea1bdf367002506bd67` at commit
`85213ea9b493682c9198eadda5e20c5e5ab2a04d`; all 1,111 T11 identities were
also excluded. Selection preceded tokenizer measurement and every T18 model
forward.

Each model represented four textual views: the raw emoji sequence, its English
Emoji short name, its Japanese CLDR short name, and a literal space-separated
codepoint string. The primary statistic was the equal-weight mean, over three
glyph systems and 24 fixed late-window contexts, of:

```text
glyph → English short-name top-1 accuracy
minus
glyph → literal codepoint top-1 accuracy
```

The late window (`0.75`, `0.875`, `1.0` normalized depth), two carriers, four
suffix distances, model roster, primary endpoint, randomization seeds,
multiplicity rule, and stopping rule were pushed before acquisition. “Short
name” here is the Emoji 17 comment name, required to equal the English CLDR
`tts` annotation. It is not the Unicode Character Name of one scalar value.

## Frozen primary decision

For each model, 19,999 synchronized label permutations were run separately for
the unrestricted and tokenization-matched components. Their maximum was the
model-level intersection-union p-value. Both observed components also had to
reach `0.02` in the same model cell.

| Model cell | Unrestricted contrast [descriptive 95% interval] | Token-matched contrast [interval] | Matched n | Model IUT p | Bounded result |
|---|---:|---:|---:|---:|---|
| Qwen2.5 0.5B base | 0.044922 [0.017361, 0.074942] | 0.045070 [0.011746, 0.081875] | 165 | 0.00010 | pass |
| OLMo 2 1B base | 0.046947 [0.024667, 0.071110] | 0.046161 [0.021801, 0.073413] | 149 | 0.00005 | **core pass** |
| Qwen2.5 1.5B base | 0.111256 [0.076098, 0.149233] | 0.119424 [0.078206, 0.162862] | 165 | 0.00005 | pass |
| SmolLM2 1.7B base | 0.017940 [-0.002027, 0.039207] | 0.025511 [0.002188, 0.049234] | 153 | 0.00005 | practical fail |
| Gemma 2 2B IT | 0.032118 [0.017506, 0.047671] | 0.030267 [0.014239, 0.046415] | 167 | 0.00005 | **core pass** |
| Llama 3.2 3B base | 0.087529 [0.053818, 0.124855] | 0.099401 [0.058343, 0.144095] | 147 | 0.00005 | **core pass** |
| Qwen2.5 3B base | 0.122251 [0.089263, 0.158058] | 0.133049 [0.097993, 0.170353] | 165 | 0.00005 | pass |
| Qwen2.5 7B base | 0.178530 [0.139972, 0.218316] | 0.192587 [0.151318, 0.235801] | 165 | 0.00005 | **core pass** |
| Mistral 7B Instruct v0.3 | 0.231409 [0.186632, 0.278865] | 0.251458 [0.198051, 0.306757] | 144 | 0.00005 | pass |

The four core cells were Llama, Qwen 7B, OLMo, and Gemma. All four passed the
statistical and practical requirements in the same cells. The third-smallest
core IUT p-value was `0.00005`; multiplying it by two for the registered
partial-conjunction test gave `p = 0.0001`. Thus the primary did not depend on
the five secondary cells.

The intervals in the table are descriptive item bootstraps. The decision uses
the frozen synchronized randomization tests, not whether those intervals cross
zero.

## Tokenization did not remove the registered effect

The matched component retained only non-singleton strata defined by glyph
system and the exact token-count triple `(glyph, English short name,
codepoint literal)`. Coverage ranged from 144 to 167 of 192 items. Every cell
retained at least 51 modifier, 66 ZWJ, and 23 regional-flag items, above the
predeclared minima.

All four core matched contrasts exceeded `0.02`, and every one was close to or
larger than its unrestricted counterpart except Gemma and OLMo, where the
change was small. This rejects the narrow explanation that the registered
primary is wholly produced by view token-count differences. It does **not**
establish tokenizer independence: token identities, merge histories, byte
paths, and sequence structure remain different.

## Secondary multilingual result

Japanese short names were secondary and had no authority to rescue the
primary. Using the Japanese-specific token-count strata, the late-window
Japanese-minus-codepoint point estimate was positive in all nine models,
ranging from `0.017998` to `0.267982`. The unrestricted Japanese estimate was
also positive in 9/9, from `0.007957` to `0.214048`.

This makes a purely English-table lookup account less complete, but the result
is still lexical and observational. English and Japanese labels are related,
the model training corpora are unknown, and no registered Japanese inferential
family was run. The secondary result does not demonstrate language-independent
meaning.

## Shared aggregate, heterogeneous implementation

All nine unrestricted English point estimates were positive at each of the
three registered late depths, but the full trajectories did not reveal one
shared transition. One model peaked at `0.125`, five at `0.875`, and three at
the returned final state. Early-layer paths varied sharply.

The late-window paired-minus-off-diagonal margin favored English names in 9/9
models, both unrestricted and matched. Centered linear CKA favored names in
only 5/9 unrestricted cells and 3/9 matched cells. An emoji can therefore be a
better key for its own label without the complete emoji matrix globally
aligning more strongly with the complete name matrix than with the codepoint
matrix.

Item-level recurrence was sparse. Only 8 of 192 items had positive effects in
all four core models, although 143 had a positive equal-core-model mean.
Pairwise core item-effect correlations ranged from `0.0245` to `0.2035`. Across
all nine models, only 2 items were positive in every cell, while 164 had a
positive equal-model mean. The most faithful summary is therefore:

> aggregate recurrence with model-private lexical bindings.

The four Qwen matched point estimates happen to rise in checkpoint-size order
(`0.0451`, `0.1194`, `0.1330`, `0.1926`). Architecture details, data,
checkpoint identity, and parameter count are confounded, and the full depth
paths differ. No scale law is authorized.

## Completed acquisition and validation

| Audit field | Result |
|---|---:|
| Exact model/tokenizer roles | 9 / 9 |
| Items per role | 192 |
| Completed shards | 54 / 54 |
| Model forwards | 13,824 |
| FP32 readout vectors | 497,664 |
| Generation / intervention calls | 0 / 0 |
| Sum of completed acquisition receipts | 124.565 s |
| Maximum recorded peak CUDA allocation | 15,351,009,792 bytes |
| Furnace raw-run footprint | 4,788,850,288 bytes in 289 files |

The first Mistral attempt observed another user's GPU workload before shard 0
and yielded with zero Mistral scientific forwards. The same frozen role later
resumed from shard 0 and completed all six shards. The yield receipt is retained
rather than erased.

The independent validator did not import the primary analyzer. It re-scanned
the frozen 1,429-blob exposure boundary, verified selection and freeze hashes,
validated 54 immutable shards and all summary hashes, and independently
recomputed 18 randomization tests. It reproduced 4/4 core joint passes and the
partial-conjunction `p = 0.0001`. The primary analysis receipt SHA-256 is
`799cb3cc2b27c17b3b2d861a8f92d9e629963fd5b2ab085d8bc5a7282772b10c`;
the independent receipt SHA-256 is
`a81228a4a187c692ff41fff83da239a2be4de8f6de05335f7be55b4d5eb8f4ad`.

## Contribution and claim boundary

T18 closes the specific weakness left by the prior-exposed T17 atlas: the
registered late-window lexical relation recurred on a population selected by
an exact-surface repository holdout before tokenization and forward passes.
The effect also survived the registered exact token-count control in all four
core cells.

T18 does **not** establish:

- a pretraining, concept, component, family, country, or name holdout;
- visual recognition of a rendered glyph;
- human-like emoji meaning or understanding;
- tokenizer causality or tokenizer independence;
- a shared layer transition, circuit, mediator, or behavioral effect;
- instruction-tuning, parameter-scaling, architecture-general, or
  model-population effects;
- nine independent replications.

The nine cells share item identities and may share data, tokenizer ancestry,
and architecture lineage. They are registered model/tokenizer cells, not nine
independent samples from a model population.

## Next gates

T18 supports three clean follow-ups, each requiring a new freeze:

1. **Lexical breadth:** separate official short-name lookup from aliases,
   paraphrases, and independently selected multilingual labels.
2. **Emoji specificity:** compare multi-codepoint emoji with named non-emoji
   Unicode symbols under matched token and label structure.
3. **Causal localization:** contrast the eight core-consensus items with
   model-private items in the registered late window, using an untouched bank
   and preselected `attn_out` / `mlp_out` removal, addition, and restoration
   endpoints.

No favorable item, layer, or component from this completed atlas should be
promoted directly into a confirmatory causal claim.

## Evidence

- [Primary analysis receipt](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/analysis_receipt.json)
- [All nine model-cell results](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/model_cell_results.json)
- [Full depth profiles](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/depth_profiles.json)
- [Post-outcome secondary analysis](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/secondary/secondary_analysis.json)
- [Depth CSV](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/secondary/depth_curves.csv) and [SVG](../validation/fresh_composite_glyph_lexical_confirmation_v0/results/secondary/depth_curves.svg)
- [Independent validation](../validation/fresh_composite_glyph_lexical_confirmation_v0/independent_validation.json)
- [Preserved contention yield](../validation/fresh_composite_glyph_lexical_confirmation_v0/runtime_yield_receipt.json)
- Freeze manifest SHA-256:
  `4bd83f058d1226b9e3332b88ffa27db04368fcaffe34c6559228b934bb4f3eb1`
- Freeze commit: `c1c1f006edb6264d4042a53ad0e333e01ebc74ab`

The 4.79 GB raw activation run remains in the recorded furnace scratch path and
was not copied into Git.
