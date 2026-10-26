# Full development-grid reassessment with paired matched-shape scoring

[日本語](CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.ja.md) · [Eight-input diagnostic](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_RESULTS_V0.md) · [Research sequence](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md)

2026-10-10 (JST). The user authorized the full existing-score reassessment after the eight-input diagnostic. This specification precedes its model outputs. It versions the scoring geometry, preserves every historical score, and does not introduce new scenarios, candidate texts, human labels, models, or causal interventions.

## Question and population

How do the measured goal–cue interaction, effect crossover, and candidate preference change when both candidates are evaluated at the same execution and score-normalization shape?

The population is the complete existing inventory of 24 author-defined development scenarios in six families. It is not a new confirmatory sample. Repeated cue pairs, families, contexts, and candidate formulations do not count as independent scenarios.

| Existing source | Sequence scores | Paired inputs |
| --- | ---: | ---: |
| Original emoji, including absent-cue baseline | 288 | 144 |
| Original word control | 192 | 96 |
| Two additional candidate formulations, both carriers | 768 | 384 |
| Total | **1,248** | **624** |

Of these, 1,152 sequence scores form 576 cue-bearing comparisons; the remaining 96 scores form 48 original-formulation absent-cue comparisons. The absent baseline is shared, not independently reacquired for words. There are no absent-cue scores for the two additional formulations: those 192 missing scores remain unacquired. Each of the 144 cue-bearing blocks contains four inputs: two contexts × two cue variants, for one scenario, carrier, and candidate formulation.

## Scoring version

Use the saved joint prompt/candidate token IDs directly. No tokenizer, BOS/EOS insertion, chat-template change, length normalization, response generation, or semantic relabeling is allowed.

For each paired input, right-pad its two full sequences to their common maximum length using token ID 0. Set attention-mask entries to 1 for real tokens and 0 for padding; use explicit absolute position IDs. The model remains the pinned Llama 3.2 3B BF16 eager-attention implementation, in evaluation/inference mode with no KV cache.

Normalize the common predictor rectangle `[prompt_length − 1 : common_total_length − 1]` in FP32 before gathering valid candidate-token log probabilities. Exclude padding from all sums. Preserve per-token scores, full sums, geometry, and the float32 shared-prefix predictor-logit digest/shape. This is exactly the matched-shape path tested in the prior eight-input diagnostic; it does not establish absolute FP32-level accuracy or token/position equivalence between emoji and word prompts.

Pin the prior portable CPU preflight reference and complete historical core runtime. Preserve the historical analysis and the native-versus-portable auxiliary arithmetic distinction; do not relax model-score equality to accommodate a runtime change.

## Fixed execution budget and order

1. **Beginning sentinels: 32 calls.** For each of the same eight diagnostic inputs, run original A, original B, padded A, padded B, in that order.
2. **Complete inventory: 1,248 calls.** Sort the 624 identities `(pair, carrier, block, context, cue)` lexically, with absent inputs labeled `shared_absent`; score padded A then padded B.
3. **Ending sentinels: 32 calls.** Repeat the identical beginning schedule.

Maximum: **1,312 forward attempts**, including failed attempts. Engineering sentinel calls are excluded from the 1,248 reassessed-score denominator. The run has a 900-second walltime bound and no automatic retry, resumption, precision fallback, or additional acquisition.

## Integrity and stopping rules

- Verify pinned source, specification, model files, previous raw scores, previous diagnostic records, and complete core runtime before model scoring. Compare installed `modeling_llama.py` and `masking_utils.py` SHA-256 digests to the prior diagnostic's implementation receipt before the first forward; recording the new digests alone is insufficient.
- Original sentinel token scores and sums must exactly match their historical values; shared-prefix logit digests must match the prior diagnostic. Padded sentinel scores and digests must exactly match the prior matched-shape executions. Ending sentinels must also reproduce the beginning. The 16 inventory calls that overlap the eight padded sentinel pairs must also exactly reproduce their prior and beginning values, without extra forwards. Failure stops acquisition without widening a tolerance.
- For all 624 inventory pairs, require exact shared-prefix token-logprob equality and exact predictor-logit digest/shape agreement. A numerical pair failure is retained while the bounded inventory continues, provided replay/resource checks remain valid. Do not replace a failed case or report a passing-only subset.
- Bind an occupancy observation before and after each attempted forward. Any other GPU PID, unreadable occupancy, insufficient free memory, elapsed-budget failure, or owned-memory-cap violation stops this acquisition only.
- Preserve every planned event identity after a stop, with explicit `not_run`/failed status. Distinguish complete collection, numerical equality, runtime/replay integrity, resource admission, and analytical eligibility. Missing checks never count as success.
- Require at least 12,288 MiB free before allocation and 4,096 MiB at forward boundaries. Cap the PyTorch allocator at 9,728 MiB, with a 512 MiB driver allowance. Never alter another process to obtain resources. Observations cannot exclude contention between checks.
- Write outputs exclusively to a new run directory. Do not overwrite historical or partial records.

An incomplete or failed-gate run may be analyzed for diagnostics, but it cannot replace the development results. Complete comparisons must use the same full population in both versions.

## Prespecified descriptive comparisons

Let `s(c,v) = log P(A | c,v) − log P(B | c,v)`, using each full candidate's token sum. Retain each scenario's existing author-defined orientation `eta`.

- Cue effects: `delta_p = eta [s(p,b) − s(p,a)]`, `delta_q = eta [s(q,b) − s(q,a)]`.
- Interaction: `H = delta_q − delta_p`. Report positive, zero, and negative signs separately.
- Effect crossover: `delta_p < 0 < delta_q`.
- Author-oriented input margin: `eta × C × V × s`, with `C(p/q) = −1/+1` and `V(a/b) = −1/+1`. Positive margin denotes author-label alignment, not human accuracy.
- All-four alignment: all four margins strictly positive. Retain ties explicitly.

An independent CPU analyzer will verify all records and produce old/new per-input and 144-block results; per-formulation/carrier H summaries; every H-sign, crossover, absolute-preference, and all-four transition; per-token and full-score deviations; and across-formulation stability. Report cue-bearing preferences over 576 inputs and absent preferences over 48 separately. For the original formulation only, retain absent-relative diagnostics without treating subtraction as a correction or pooling absent scores into H.

These are deterministic, descriptive remeasurements. No p-value, new inferential effect floor, equivalence threshold, or favorable-formulation selection is introduced. Shape-controlled outputs remain a distinct scoring version alongside the old version.

## What follows—and what does not

A passed complete run can establish whether the existing development findings survive this specified scoring change. It cannot establish human interpretation, candidate equivalence, new-family generalization, emoji specificity, or a causal mechanism. It cannot identify BF16 as the unique source of the prior discrepancy.

Prepare bilingual results and a model-free, executed companion notebook, with raw/source/runtime/specification hashes and all negative transitions. Keep the PDF and its scientific claims unchanged in this step. Human annotation instructions and blinding are the next design task; recruitment, external messages, new banks, causal acquisition, publication, and GitHub push are not part of this run.
