# Shared-prefix scoring consistency: an eight-input diagnostic

[日本語](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_V0.ja.md) · [Motivation and next-study sequence](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md)

2026-10-07 (JST). This is an engineering diagnostic on already observed development inputs. The user authorized proceeding with the next-study sequence. This document fixes the first acquisition before new model scores: **eight paired inputs, seven forwards per input, maximum 56 attempts**. It authorizes no scientific sample expansion, precision sweep, automatic retry, or causal experiment.

## Question

The saved-score audit found nonzero A/B common-prefix log-score differences on 355/576 paired inputs. All occur among 520 unequal-length pairs; 56 equal-length pairs have zero differences. Identical causal histories should determine the same mathematical next-token distribution. This diagnostic asks whether fixing both model-execution and score-normalization shapes makes shared-prefix predictions identical under the recorded BF16 implementation.

The test separates three quantities: exact historical replay, exact repeated-call reproducibility, and agreement between different candidates' shared prefixes at matched execution shape. Cross-shape prefix-only differences are descriptive. The experiment cannot isolate BF16 rounding from every kernel or mask implementation choice.

## Fixed selection rule

An identity is `(pair_id, carrier, block_id, context, cue)` with ordinary lexical tuple ordering. Use the saved measurement analysis, SHA-256 `806400d78608cc2999f9480d3b82b24a45fd4739f85f52d82a21f3f7cb4b39e8`.

1. Select the largest absolute saved prefix-score residual in each of these block cases: original/emoji/affect_01, explicit_negation/emoji/affect_03, adjective_pair/emoji/thermal_04. Break ties by identity.
2. Select the largest absolute residual over the full recorded inventory, breaking ties by identity.
3. Add the lexicographically first unused identity in each stratum: equal-length emoji, equal-length word, unequal-length emoji, unequal-length word.
4. Deduplicate exact identities. If necessary, cycle the same four control strata and take the first unused identity until there are eight distinct inputs. Preserve selection roles and order.

The resulting panel is known from existing data; it was selected to diagnose the numerical issue, not estimate prevalence or confirm an emoji effect.

| Role | Pair | Carrier | Block | Context / cue | Full token lengths A / B |
| --- | --- | --- | --- | --- | ---: |
| Decision-case maximum | original | emoji | affect_01 | p / b | 36 / 38 |
| Decision-case maximum | explicit_negation | emoji | affect_03 | q / b | 34 / 36 |
| Decision-case maximum | adjective_pair | emoji | thermal_04 | p / b | 36 / 35 |
| Global maximum | original | emoji | thermal_04 | p / a | 35 / 34 |
| Equal-length control | original | emoji | completion_02 | p / a | 38 / 38 |
| Equal-length control | original | word | completion_02 | p / a | 37 / 37 |
| Unequal-length control | adjective_pair | emoji | affect_01 | p / a | 37 / 38 |
| Unequal-length control | adjective_pair | word | affect_01 | p / a | 36 / 37 |

No overlap requires filling in this panel. Saved prompt/candidate token IDs are used directly, with no tokenization, new stimuli, EOS/BOS insertion, or chat-template change.

## Seven calls per paired input

| Calls | Execution | Purpose |
| --- | --- | --- |
| 1–4 | Original A, original B, repeat A, repeat B | Exact historical per-token/sequence parity and repeated-call agreement |
| 5–6 | A and B right-padded to their common maximum total length | Same model shape, real-token positions, and score-normalization shape |
| 7 | Prompt plus common candidate prefix only | A separately shaped causal-history comparison, not an assumed exact oracle |

Original calls preserve the recorded forward arguments, including implicit positions, all-ones padding mask, no KV cache, evaluation/inference mode, and the original candidate-length FP32 normalization slice. They must match all historical candidate token log probabilities and their sum exactly. A mismatch stops this acquisition and records the unrun denominator.

Padded calls use valid token ID 0 only in right-padding positions, a mask of 1 on real tokens and 0 on padding, and explicit absolute position IDs. Padding is excluded from all scores. Both candidate executions normalize the same rectangle of predictor positions in FP32 before gathering and retaining each candidate's valid scores. This matters: equal model-input length alone would still leave different scoring shapes if the original candidate-length slice were retained.

For every call, record the shared-prefix predictor-logit tensor's shape, dtype, and digest, alongside valid per-token log probabilities and full candidate sums. The common-prefix comparison covers the positions predicting the common candidate tokens; the final shared token is predicted from its preceding history. Logit equality and selected-token log-probability equality are separate checks.

## Decision rules specified before execution

- **Historical parity:** exact equality of every original-call token score and sequence sum to its saved value. Repeated new results alone do not establish historical parity.
- **Repeated original execution:** exact equality between each candidate's two original calls. No nonzero tolerance is introduced.
- **Matched-shape prefix:** exact equality of the shared predictor-logit digests/shapes and shared token-logprob vectors for padded A and B. Assess this across all eight pairs; a failure stays a failure. Complete the bounded panel after historical parity passes, rather than searching for passing cases.
- **Cross-shape comparison:** report original versus padded and prefix-only discrepancies, including candidate-score polarity changes, without a pass threshold. No FP32 or scientific-effect tolerance is invented from these observations.
- **Block-level scientific verdicts:** unavailable. One input per selected block cannot update H, crossover, or all-four alignment. All four inputs would be required, and the three affected blocks alone would require 12 paired inputs / 84 calls with this schedule, before separate controls.

Passing the prefix test qualifies a proposed scoring geometry for broader validation. It does not replace the existing scientific scores or demonstrate that the full 1,248-score inventory has been repaired. Any change to masks, positions, padding, runtime, precision, or scoring geometry receives a new scoring version and complete relevant-grid assessment before paper numbers change.

## Resource and provenance boundaries

Use the existing Llama 3.2 3B BF16 files and historical runtime only. The model manifest is `dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`. No model download, quantization, training, external inference service, or protected bank is involved.

Furnace execution uses an isolated checkout. Immediately before allocation and every forward, inspect GPU process/memory state. Any other GPU PID or unreadable occupancy stops our acquisition; never stop or alter the other workload. Require at least 12 GiB free before allocation and 4 GiB before each forward, with a 9,728 MiB allocator cap plus 512 MiB driver allowance, and a 600-second run budget. These limits can reject a run; they are not widened after failure. A resource snapshot is not a reservation, so contention remains possible between checks.

Bind input/specification/source digests and compare the complete JSON-normalized historical core runtime. Record current model/mask source-file digests separately. Keep 56 planned row identities even when execution is partial. Write start, runtime, occupancy, per-call results, and completion records exclusively; never overwrite or silently resume a run.

## Interpretation and next step

If matched-shape shared prefixes agree, a shape-controlled scoring variant becomes a concrete candidate for full development-grid validation. This supports an execution-geometry explanation on the diagnostic panel; identifying a specific arithmetic kernel or dtype mechanism requires additional tests.

If agreement fails, preserve the failure and inspect the exact logits, masking, and normalization path. A separately budgeted FP32 comparison may then be appropriate. Either outcome leaves human label/candidate validation, independent scenario confirmation, and natural-state causal tests as distinct later stages.

The submitted/post-review PDF and all historical scores remain unchanged. Results will be reported separately, including a zero-forward or partial result if the acquisition gates do not pass.
