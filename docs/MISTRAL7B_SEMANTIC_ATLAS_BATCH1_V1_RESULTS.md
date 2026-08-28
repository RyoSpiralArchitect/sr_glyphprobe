# Mistral 7B semantic atlas batch-one v1 results

[日本語](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.ja.md) · [Protocol](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md) · [Analysis plan](MISTRAL7B_SEMANTIC_ATLAS_V0_ANALYSIS.md) · [Evidence](../artifacts/mistral7b_semantic_atlas_batch1_v1/README.md)

Status: **complete descriptive result — late-depth glyph/name alignment
candidate**. No confirmatory decision or semantic-causal claim is authorized.

## Acquisition and the failed fast path

The Unicode Emoji 17.0 tokenizer census fixed 1,184 fully-qualified
single-codepoint entries: 50 prior-exposed calibration items, 842 unseen
discovery items, and 292 deterministic `reserved_unrun` items. Acquisition used
the first two roles only.

The initial batch-64 run completed 28 shards, 5,352 unique input sequences, 84
batched calls, and 192,672 stored vectors. Its prospectively frozen batch-one
recapture check failed all 18 cases. The worst minimum cosine was `0.998244270`,
maximum relative RMS error was `0.078983818`, and maximum absolute element error
was `2.5`. Thresholds were not relaxed.

The replacement v1 repeated the exact 892-item grid at batch size one. It made
5,352 model calls, produced the same 192,672 FP32 vectors in 28 shards, and used
73.524 seconds of summed shard execution time. All hashes, shapes, and finite
checks passed. The independently repeated 18-case validation was bit-exact:
minimum exact-element fraction `1.0`, maximum absolute and relative RMS error
`0`. The failed fast-path data and receipt are retained.

No reserve item was forwarded in acquisition, validation, or analysis.

## Complete discovery depth profile

Each row is the equal-weight mean over two carriers and four distances for all
842 discovery items. Top-1 chance is `1/842 = 0.001188`.

| Layer | Glyph→name top-1 | Glyph→codepoint top-1 | Glyph/name CKA | Glyph/codepoint CKA | Glyph group purity | Glyph subgroup purity |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.002375 | 0.001930 | 0.011634 | 0.108158 | 0.244908 | 0.064430 |
| 4 | 0.009204 | 0.001336 | 0.073398 | 0.155903 | 0.477524 | 0.188213 |
| 8 | 0.059382 | 0.001188 | 0.135795 | 0.182633 | 0.626262 | 0.280151 |
| 12 | 0.048991 | 0.001336 | 0.142839 | 0.146591 | 0.627999 | 0.282185 |
| 16 | 0.069626 | 0.001336 | 0.147049 | 0.117451 | 0.630686 | 0.291375 |
| 20 | 0.106295 | 0.001039 | 0.141629 | 0.098568 | 0.614415 | 0.290350 |
| 24 | 0.128711 | 0.001188 | 0.146506 | 0.083033 | 0.614133 | 0.296823 |
| 28 | 0.127672 | 0.001633 | 0.159395 | 0.083007 | 0.616033 | 0.297298 |
| 31 | **0.136580** | **0.001188** | **0.206788** | **0.082973** | **0.627197** | **0.309991** |

At layer 31, glyph→name top-1 is about 115 times chance, while
glyph→codepoint remains at chance. Reverse name→glyph top-1 is `0.152761` and
forward mean reciprocal rank is `0.214288`. Glyph Unicode-group neighbor purity
is `0.627197` versus a random-pair baseline of `0.131441`; subgroup purity is
`0.309991` versus `0.016110`. Codepoint literals also carry some group structure
(`0.2975` group purity at layer 31), so category purity alone is not a semantic
control. The paired item retrieval is the sharper contrast.

The eight layer-31 glyph→name cells range from `0.081948` to `0.201900`; all are
well above chance. The full carrier/distance grid is published rather than
selecting the best cell.

## Token-structure sensitivity

This exact sensitivity was designed after the headline was known and is
therefore post-outcome. It restricts discovery to 760 glyphs with exactly five
tokens and the identical prefix `[29473, 1011, 930]`.

| Layer-31 stratum | n | Chance | Glyph→name | Glyph→codepoint | Glyph/name CKA | Glyph/codepoint CKA |
|---|---:|---:|---:|---:|---:|---:|
| Common-prefix five-token glyphs | 760 | 0.001316 | 0.150658 | 0.001151 | 0.201920 | 0.057993 |
| Name tokens = 1 | 105 | 0.009524 | 0.402381 | 0.008333 | 0.2911 | 0.1193 |
| Name tokens = 2 | 257 | 0.003891 | 0.267023 | 0.002918 | 0.2570 | 0.0742 |
| Name tokens = 3 | 213 | 0.004695 | 0.236502 | 0.004695 | 0.2742 | 0.0861 |
| Name tokens = 4 | 111 | 0.009009 | 0.257883 | 0.013514 | 0.3678 | 0.1160 |
| **Name tokens = 5 (glyph/name length matched)** | **43** | **0.023256** | **0.351744** | **0.031977** | **0.459196** | **0.121558** |
| Codepoint tokens = 6 | 180 | 0.005556 | 0.159722 | 0.006250 | 0.1495 | 0.1612 |
| Codepoint tokens = 7 | 573 | 0.001745 | 0.188482 | 0.000873 | 0.2576 | 0.0627 |

The broad retrieval contrast therefore survives fixed glyph length, fixed
glyph prefix, and every name-length stratum with at least 20 items. It also
survives the 43-item equal glyph/name token-count subset. There is no discovery
subset with all three view lengths equal, and token identity remains different,
so this is not a fully token-isomorphic control.

## Batch-shape sensitivity

Although batch-64 failed vector-level equivalence, its discovery aggregate
profile was close to batch-one: across the nine layer summaries, the maximum
absolute difference was `0.000742` for glyph/name top-1, `0.000445` for
glyph/codepoint top-1, and `0.000260` for glyph/name CKA. This does not rescue
the failed capture gate; it shows that the descriptive aggregate shape is less
sensitive than individual late residual vectors.

## Interpretation and next gate

The result narrows a simple codepoint-identity or glyph-token-length account.
Across a large unseen set, later residual states align each glyph with its
official name far more than with its `U+...` literal, and the alignment remains
visible under strong tokenizer strata.

It still does not show that a disentangled semantic variable has been found.
Official names and emoji categories are human labels; Unicode ordering,
training co-occurrence, tokenizer identity, and correlated lexical features
remain possible contributors. All analysis is observational in one model.

The clean next step is now unusually concrete: use only calibration/discovery
evidence to freeze one reserve endpoint—likely a complete, multiplicity-bounded
late-depth glyph/name-versus-codepoint retrieval contrast—then forward the 292
reserved items exactly once. Until that happens, this is an exploratory
candidate and closes no Phase I gate.
