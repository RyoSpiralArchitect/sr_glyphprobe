# Matched-shape reassessment: score interaction persists, response selection remains wording-sensitive

[日本語](CONTEXTUAL_EMOJI_MATCHED_SHAPE_RESULTS_V1.ja.md) · [Specified procedure](CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.md) · [Human-validation draft](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.md) · [Next study](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

2026-10-10 (JST). **Completed development-data reassessment; independent numerical validation passed.** This study remeasures the existing 24 authored scenarios in six families. It adds no independent scenarios, human judgments, models, or causal interventions. The paper PDF has not been changed.

## 1. What this closes

All **1,248 existing candidate-sequence scores** were reacquired using the same execution and score-normalization shape within each candidate pair. Together with 64 beginning/end replay checks, the run completed **1,312/1,312** forward attempts in 263.22 seconds. Independent CPU analysis verified the complete records and all specified gates. The companion notebook executed all five code cells and reproduced the entire analysis JSON exactly, without model calls.

The shared-prefix predictor-logit digests and token log probabilities agree exactly on **624/624 pairs**. Old nonzero prefix residuals occurred in 355/576 cue-bearing pairs and 17/48 shared absent-cue pairs; the new counts are zero in both populations. Historical, beginning/end, and the 16 overlapping inventory/sentinel scores also satisfy the specified exact replay checks.

This closes the specified complete-grid consistency check. Absolute probability accuracy, a BF16-specific explanation, human interpretation, and generalization remain separate questions. The new record is eligible as a separately versioned score source; historical records are preserved.

## 2. Population, measurement, and the meaning of a positive interaction

The inventory contains 576 cue-bearing paired inputs and 48 shared absent-cue paired inputs. Each pair has two scored candidate sequences. The cue-bearing comparisons form 144 tables: 24 scenarios × two carriers (emoji/word) × three response formulations. Each table has two contexts × two cue variants. Engineering replay checks and repeated formulations do not increase scientific N.

The formulations are the original scenario-specific alternatives (`original`), “This meets my goal.” / “This does not meet my goal.” (`explicit_negation`), and “This is suitable for my goal.” / “This is unsuitable for my goal.” (`adjective_pair`). Saved leading spaces and token IDs were preserved. Their semantic equivalence has not been independently established.

Let `s = log P(A) − log P(B)` for complete continuations. With the previously authored orientation `eta`, define `delta_p = eta[s(p,b) − s(p,a)]`, `delta_q = eta[s(q,b) − s(q,a)]`, and `H = delta_q − delta_p`. **H > 0** measures a direction of interaction; **effect crossover** requires `delta_p < 0 < delta_q`. **All-four alignment** requires the more probable candidate to match the author's intended label in every context/cue condition. These are three different properties. No human accuracy is measured.

Both candidates were right-padded to their common maximum length, with explicit masks/positions and common FP32 score normalization, under the pinned Llama 3.2 3B BF16 eager runtime. Prompt geometry between emoji and words remains unmatched. The [procedure](CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.md) records the exact implementation and admission criteria.

## 3. Old → matched-shape results

Every count below uses the same full population in both scoring versions. H means use nats and four-decimal rounding; exact values are retained in the analysis artifact.

| Response formulation | Carrier | Mean H | H > 0 /24 | Effect crossover /24 | All-four alignment /24 | Aligned inputs /96 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Original alternatives | Emoji | 1.3123 → 1.3286 | 23 → 23 | 12 → 13 | 0 → 0 | 54 → 52 |
| Original alternatives | Word | 2.2505 → 2.2694 | 23 → 23 | 18 → 18 | 3 → 3 | 60 → 60 |
| Explicit negation | Emoji | 1.1960 → 1.2329 | 19 → 23 | 10 → 12 | 2 → 1 | 54 → 52 |
| Explicit negation | Word | 1.6120 → 1.6349 | 22 → 23 | 18 → 18 | 4 → 4 | 62 → 62 |
| Adjective alternatives | Emoji | 1.3160 → 1.3695 | 24 → 24 | 14 → 15 | 2 → 2 | 55 → 55 |
| Adjective alternatives | Word | 2.3119 → 2.2984 | 24 → 24 | 19 → 21 | 5 → 5 | 60 → 60 |

There are no cue-bearing candidate ties in either version. The maximum absolute change in a cue-bearing candidate-score difference is **0.297257 nats**; the maximum absolute change in H is **0.518245 nats**. The small mean change in `s` across inputs, 0.000138 nats, does not bound local decision changes.

Across the three formulations, the separation is particularly clear:

| Property | Emoji, old → new | Word, old → new |
| --- | ---: | ---: |
| H > 0 in all three formulations, /24 scenarios | 19 → 22 | 22 → 23 |
| Effect crossover in all three, /24 scenarios | 6 → 8 | 13 → 14 |
| All-four alignment in all three, /24 scenarios | 0 → 0 | 0 → 0 |
| Preferred A/B polarity varies across formulations, /96 inputs | 52 → 55 | 56 → 56 |

The last row records polarity under the authored candidate mapping, not an independently validated disagreement in meaning. Positive interaction is frequent in both carriers; reliable selection across formulations remains unsupported on these materials. The counts do not establish carrier equivalence or emoji-specific superiority.

## 4. Every changed decision is retained

The old prefix-subtraction sensitivity left all 144 H signs unchanged. Actual matched-shape re-execution changes **5/144 H signs**, **6/144 effect-crossover decisions**, **1/144 all-four decisions**, and **4/576 cue-bearing candidate choices**. Shared absent-cue preferences change in **0/48** cases. Prefix subtraction and full re-execution are different analyses.

All five H changes are negative → positive and occur with explicit negation:

| Carrier / scenario | Old H | New H |
| --- | ---: | ---: |
| Emoji / direction_02 | −0.270887 | 0.014315 |
| Emoji / sound_01 | −0.011982 | 0.001149 |
| Emoji / thermal_01 | −0.016952 | 0.023331 |
| Emoji / weather_02 | −0.125323 | 0.112871 |
| Word / direction_01 | −0.054867 | 0.034587 |

These sign transitions are descriptive, including values very close to zero. No practical-effect threshold or significance test was added after observing them.

All six crossover transitions are false → true: original emoji `thermal_02`; explicit-negation emoji `affect_03` and `weather_02`; adjective emoji `thermal_04`; adjective word `affect_03` and `direction_02`.

The single all-four loss is explicit-negation emoji `direction_04`. Its minimum author-oriented margin changes from **0.030719 to −0.049289 nats**; it retains positive H and effect crossover. This is a concrete case in which both interaction summaries coexist with failed complete response alignment.

| Changed input (formulation / carrier / scenario / context / cue) | Old s | New s |
| --- | ---: | ---: |
| Explicit negation / emoji / direction_04 / p / a | −0.030719 | 0.049289 |
| Explicit negation / emoji / direction_04 / q / b | −0.046844 | 0.033603 |
| Original / emoji / affect_04 / q / b | −0.154943 | 0.039089 |
| Original / emoji / completion_01 / q / b | 0.024856 | −0.109558 |

All four changed choices lose author-label alignment. No case was discarded or replaced. Per-token changes, all 624 input records, all 144 old/new tables, and every transition are available in the machine-readable analysis.

## 5. Remaining controls and interpretation

The original formulation contributes 96 unique absent-cue scores (48 pairs), shared across the two carriers. They support 48 scenario/carrier baseline-relative tables without duplicating the absent sample. **The 192 absent-cue scores for the additional formulations remain unacquired.** Context-specific baseline subtraction leaves H algebraically unchanged and does not validate the deleted-message baseline as semantically neutral.

The useful development finding is now more specific: **the separation between contextual score interaction and consistent response selection survives this complete matched-shape reassessment.** Numerical geometry changed several threshold decisions, so the old values should not be silently reused. At the same time, the persistent cross-formulation instability calls for an independent assessment of the task and response alternatives.

The run does not determine whether that instability reflects alternative meanings, linguistic naturalness, candidate priors, task misunderstanding, or another mechanism. It establishes neither an emoji sense change nor a causal route. The observed word/emoji comparison also retains information-content and token/position differences. No inferential p-values, new sample, or paper-level causal claim were produced here.

Next, resolve the [human-validation draft](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.md): rater independence and language competence, coverage and assignment, blinded interpretation versus separate equivalence/carrier comparisons, response options, disagreement handling, and participation arrangements. Retrospective ratings remain retrospective. Only after that should a genuinely new-family study and a separately specified natural-state intervention be considered. No recruitment or external annotation service was started.

## 6. Resource and reproducibility record

Execution code/specification were committed as `538a087` before the first model call. Complete core runtime and installed model/masking-source identities match the prior diagnostic. There were no downloads, tokenizer calls, generation calls, or retries. The run used 6,230 MiB peak PyTorch reserved memory; the highest sampled own-process GPU memory was 6,906 MiB. All 2,628 resource observations were allowed, including 2,624 forward-boundary checks. Minimum observed free memory was 25,186 MiB. This does not measure peer impact or exclude activity between checks. After completion, `spiral status` showed no compute processes.

The new runner/checker tests passed (38 tests); the broader targeted regression suite passed with **211 tests and 66 subtests** ([JUnit receipt](../validation/contextual_emoji_matched_shape_v1/regression_tests.xml)). The executed notebook verifies the entire report and source hashes on replay. This is an engineering validation of this recorded runtime/geometry, not a general guarantee across devices or scoring backends.

| Artifact | SHA-256 |
| --- | --- |
| [Specification](../validation/contextual_emoji_matched_shape_v1/specification.json) | `63e16fc7e60079032eade81a9cc599a1cea1b2db287373b077d08f078d162ecf` |
| [Forward records](../validation/contextual_emoji_matched_shape_v1/run1312/forwards.jsonl) | `5bc84713d6305e0dff80898bb57d60d54d2c9ef01ab45b11f9158d59df8e5706` |
| [Completion record](../validation/contextual_emoji_matched_shape_v1/run1312/run_completed.json) | `7220f5ffed086b703087e46d1afbc350c215511f7fa31ee5e8c179057b5307b8` |
| [Independent analysis](../validation/contextual_emoji_matched_shape_v1/independent_analysis.json) | `8557d04e77b6c095022b3d97d5404024b1f7be8d1a101a93a6e54ebdcd4d2e35` |
| [Executed bilingual notebook](../notebooks/contextual_emoji_matched_shape_v1.ipynb) | `bcdc5e1c6a532f0656e65ac42287b9af179636a19d808e1b633eedeec558d57e` |

Specification, forward-record, and completion hashes were checked against the Furnace copies after transfer. The completion record binds raw runtime/implementation/resource files; the analysis binds its checker and all source inputs. Historical artifacts and the PDF remain unchanged. No GitHub push or public release is part of this step.
