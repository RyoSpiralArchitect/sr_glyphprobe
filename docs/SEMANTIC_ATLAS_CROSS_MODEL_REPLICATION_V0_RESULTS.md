# Semantic atlas cross-model replication v0 results

[日本語](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.ja.md) · [Frozen protocol](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md) · [Evidence](../artifacts/semantic_atlas_cross_model_replication_v0/README.md)

Status: **cross-model replication was not established under the frozen rule**.

The statistical part of the primary passed, but the registered practical part
did not. The Bonferroni partial-conjunction p-value was `0.0001`; however, only
two of the four core model/tokenizer cells cleared the `0.02` minimum contrast
in both the unrestricted and exact-token-count-matched components. The frozen
rule required at least three. The primary outcome is therefore negative even
though every model-cell IUT was statistically significant.

## Frozen acquisition

Freeze commit `7002db63a23b5a66ababa3033631268fe899b2cd` and manifest SHA-256
`8673bc51490460b3e8908f766b592169942bf6a7e88d292c50b427e5283f34a4`
were pushed before any selected-model forward. The acquisition retained T9's
292 items, glyph/name/codepoint views, two carriers, four distances, and
batch-one execution. The primary endpoint was the final normalized hidden state
returned by `output.hidden_states[-1]`; the raw last decoder-block output was
captured in the same forward as a non-rescuing secondary.

All nine exact model revisions completed 37 shards and 1,752 forward calls per
cell. In aggregate, T10 produced 333 shards, 15,768 model forward calls, and
126,144 FP32 readout vectors. There were no interventions or generations. One
attempt yielded before loading Qwen 0.5B when a foreign GPU process was present;
it performed zero forwards. Acquisition resumed only after the GPU was free.

| Model cell | Acquisition (s) | Peak CUDA (GB) | Forwards | Readouts |
|---|---:|---:|---:|---:|
| Llama 3.2 3B base | 14.198 | 6.467 | 1,752 | 14,016 |
| Qwen 2.5 7B base | 22.345 | 15.318 | 1,752 | 14,016 |
| OLMo 2 1B base | 9.076 | 3.008 | 1,752 | 14,016 |
| Gemma 2 2B IT | 15.397 | 5.281 | 1,752 | 14,016 |
| Qwen 2.5 0.5B base | 10.929 | 1.035 | 1,752 | 14,016 |
| Qwen 2.5 1.5B base | 12.136 | 3.128 | 1,752 | 14,016 |
| Qwen 2.5 3B base | 15.392 | 6.326 | 1,752 | 14,016 |
| SmolLM2 1.7B base | 10.122 | 3.460 | 1,752 | 14,016 |
| Mistral 7B Instruct v0.3 | 23.827 | 14.535 | 1,752 | 14,016 |

These timings are acquisition receipts on one furnace runtime, not a model or
backend speed benchmark.

## Registered model-cell results

For each component, the statistic is the minimum over the complete two-carrier
by four-distance grid of:

`glyph→official-name top-1 - glyph→U+codepoint top-1`.

Each model-cell p-value is the maximum of the unrestricted and matched
randomization p-values. A practical pass requires both observed minima to be at
least `0.02`. The nine IUT p-values form one Holm family; a bounded cell passes
only when both the Holm and practical rules pass.

| Model cell | Role | Matched n | Unrestricted min | Matched min | IUT p | Holm p | Practical | Bounded cell |
|---|---|---:|---:|---:|---:|---:|---|---|
| Llama 3.2 3B base | core | 281 | 0.027397 | 0.032028 | 0.000050 | 0.000450 | pass | pass |
| Qwen 2.5 7B base | core | 284 | 0.023973 | 0.024648 | 0.000050 | 0.000450 | pass | pass |
| OLMo 2 1B base | core | 281 | 0.013699 | 0.021352 | 0.000050 | 0.000450 | fail | fail |
| Gemma 2 2B IT | core | 284 | 0.017123 | 0.017606 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 0.5B base | extension | 284 | 0.006849 | 0.007042 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 1.5B base | extension | 284 | 0.013699 | 0.014085 | 0.000050 | 0.000450 | fail | fail |
| Qwen 2.5 3B base | extension | 284 | 0.017123 | 0.017606 | 0.000050 | 0.000450 | fail | fail |
| SmolLM2 1.7B base | extension | 287 | 0.006849 | 0.003484 | 0.000100 | 0.000450 | fail | fail |
| Mistral 7B Instruct v0.3 | extension | 285 | 0.202055 | 0.203509 | 0.000050 | 0.000450 | pass | pass |

The bounded passes are therefore Llama 3.2 3B base, Qwen 2.5 7B base, and
Mistral 7B Instruct v0.3. The extension cells cannot rescue the sole
cross-model primary.

## Cross-model decision

The four frozen core cells were Llama 3.2 3B base, Qwen 2.5 7B base, OLMo 2 1B
base, and Gemma 2 2B IT. All four IUT p-values were `0.00005`, so the registered
`r = 3` of `m = 4` Bonferroni partial conjunction was
`2 × 0.00005 = 0.0001` and passed statistically.

Only Llama and Qwen cleared the practical rule. OLMo missed it in the
unrestricted component (`0.013699`), and Gemma missed it in both components
(`0.017123` and `0.017606`). Thus the practical count was `2/4`, below the
required `3/4`, and the combined primary was negative:

`cross_model_replication_not_established_under_frozen_rule`.

This split is intentional evidence, not a threshold to revise after seeing the
result.

## What tokenization matching changed

Exact `(glyph tokens, name tokens, codepoint tokens)` non-singleton strata
retained 281--287 of 292 items per tokenizer. Matching did not erase the
observed alignment: all nine matched components remained statistically
significant, and the matched-minus-unrestricted change in the minimum contrast
ranged from `-0.003365` to `+0.007654`, with median `+0.000482`.

This rules out the narrow account that the entire T10 retrieval contrast is
created by unmatched token-count strata. It does not establish tokenization
independence. Token identity, vocabulary construction, tokenizer ancestry,
training data, and other architecture differences remain uncontrolled.

## Registered secondary endpoint

The raw last decoder-block output was captured to audit endpoint sensitivity.
It had no decision authority and cannot rescue the primary.

| Model cell | Raw-block unrestricted min | Raw-block matched min |
|---|---:|---:|
| Llama 3.2 3B base | 0.023973 | 0.021352 |
| Qwen 2.5 7B base | 0.020548 | 0.021127 |
| OLMo 2 1B base | 0.013699 | 0.014235 |
| Gemma 2 2B IT | 0.010274 | 0.007042 |
| Qwen 2.5 0.5B base | 0.020548 | 0.021127 |
| Qwen 2.5 1.5B base | 0.027397 | 0.028169 |
| Qwen 2.5 3B base | 0.034247 | 0.035211 |
| SmolLM2 1.7B base | 0.000000 | 0.000000 |
| Mistral 7B Instruct v0.3 | 0.195205 | 0.196491 |

Final normalization changes the minimum contrast in both directions across
models. The secondary profile therefore supports precise endpoint naming and
argues against silently treating the returned final state and raw block output
as interchangeable.

## Descriptive model profiles

The frozen Qwen base ladder had monotonically increasing primary minima:

| Qwen size | Unrestricted min | Matched min |
|---|---:|---:|
| 0.5B | 0.006849 | 0.007042 |
| 1.5B | 0.013699 | 0.014085 |
| 3B | 0.017123 | 0.017606 |
| 7B | 0.023973 | 0.024648 |

This four-point profile is registered secondary evidence only. Model size is
confounded with each released checkpoint, and T10 was not designed to identify
a scale law.

Mistral 7B Instruct v0.3 passed its bounded cell with minima `0.202055` and
`0.203509`. The known T9 Mistral 7B base anchor was `0.171233`, but the two
checkpoints are related and were not assigned as a controlled tuning contrast.
The difference does not establish an instruction-tuning effect or independent
replication.

## Independent validation and evidence policy

An independent validator that does not import the T10 analyzer rehashed the
compact bundle and the returned raw archive, checked all 333 activation arrays
for shape, FP32 dtype, and finite values, and recomputed all 18 randomization
components, nine IUTs, Holm correction, and the partial conjunction. It matched
the published result exactly. In total, 1,350 raw-ledger targets, 27 summary
targets, 18 compact run targets, and four analysis targets were rehashed.

The compact Git bundle contains predictions sufficient to reproduce the
decision, complete cell metrics, receipts, session records, nested shard-ledger
bindings, analysis outputs, and the independent validation result. The
1,212,819,072 bytes of raw activations remain outside Git, as do model caches.

## Claim boundary and next lane

T10 supports three bounded model/tokenizer-cell alignment statements and a
negative cross-model primary under its frozen rule. It does not establish emoji
meaning, semantic decomposition, causality, a mechanism, behavioral relevance,
tokenizer independence, a scale law, an instruction-tuning effect, independent
replication, architecture generality, or universal model generality. It closes
no Phase I causal or independent-replication gate.

T11 remains queued and untouched. Any later unusual-glyph exploration must be
labeled exploratory and cannot alter T10's frozen population, thresholds,
model roster, or result.
