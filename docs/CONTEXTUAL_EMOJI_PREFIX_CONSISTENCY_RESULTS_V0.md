# Matched-shape scoring removes the observed prefix discrepancy on eight inputs

[日本語](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_RESULTS_V0.ja.md) · [Protocol](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_V0.md) · [CPU preflight addendum](CONTEXTUAL_EMOJI_PREFIX_PREFLIGHT_ADDENDUM_V0.md) · [Next-study sequence](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

2026-10-07 (JST). **The bounded engineering gate passed: 56/56 forwards, eight existing paired inputs.** Original scores reproduced exactly; repeated calls agreed; paired, matched-shape executions had identical shared-prefix predictor-logit digests and selected-token log probabilities on all eight inputs. This qualifies the tested scoring geometry for broader validation. No scientific sample was added and no block-level result was updated.

## 1. What was tested

The panel contains three decision-sensitive block cases, the largest saved prefix discrepancy, and four deterministic length/carrier controls. Selection used already observed results. It does not estimate the prevalence of numerical discrepancies.

Each input received original A/B scoring twice, common-length padded A/B scoring, and a prompt-plus-shared-prefix execution. Original calls used the historical BF16 eager-attention runtime. Padded calls specified real-token positions and padding masks, and normalized the same FP32 predictor rectangle before selecting valid continuation scores. The prefix-only call used another tensor shape and was a descriptive comparison.

The [initial preflight refusal and explicit CPU replay revision](CONTEXTUAL_EMOJI_PREFIX_PREFLIGHT_ADDENDUM_V0.md) preceded all model calls. Initial commit `d725960` made zero forwards. Acquisition commit `41ff805` used specification `751a81c0…`. The revision changed one auxiliary CPU arithmetic definition, with six exact parent-to-reference value changes recorded separately. The Linux native replay retained seven differences from the parent. Neither count concerns model probabilities; no model comparison tolerance was introduced.

## 2. Separate gates and denominators

| Check | Observed result |
| --- | --- |
| Planned / attempted / completed forwards | 56 / 56 / 56 |
| Historical original-score parity | 32/32 calls, exact per-token values and sums |
| Repeated original A/B calls | 16/16 comparisons, exact scores and shared-logit digests |
| Matched-shape shared-prefix log probabilities | 8/8 paired inputs, exactly equal |
| Matched-shape shared predictor-logit digests/shapes | 8/8 paired inputs, exactly equal |
| Original versus padded preferred candidate | Unchanged on 8/8 inputs; no ties |
| Padded versus prefix-only shared-token probabilities | Different on 8/8 inputs; descriptive cross-shape comparison |
| Full historical core runtime | Exact JSON equality |
| New scientific observations / recomputed block H | 0 / none |

The independent checker reconstructs identities, predictor positions, masks, normalization geometry, sums, comparisons, and resource boundaries without importing the acquisition runner. Logits themselves were not archived: equality is recorded by the runner's hashes, shapes, and selected-token probabilities, not by an independent forward.

## 3. Scores can move even when the preferred candidate does not

Let `s = log P(A | prompt) − log P(B | prompt)`, summed over each complete candidate. Values below are rounded for display; raw records retain full precision. The saved prefix column is the difference of shared-prefix sums, not a single-token maximum. The padded prefix difference is exactly zero in every row.

| Pair / carrier / block / context / cue | Saved prefix difference | Original s | Padded s |
| --- | ---: | ---: | ---: |
| original / emoji / affect_01 / p / b | +0.018725 | +0.010518 | +0.062433 |
| explicit_negation / emoji / affect_03 / q / b | −0.056777 | +0.429805 | +0.482039 |
| adjective_pair / emoji / thermal_04 / p / b | +0.082370 | −2.544021 | −2.563891 |
| original / emoji / thermal_04 / p / a | +0.187710 | +1.867091 | +1.656820 |
| original / emoji / completion_02 / p / a | 0 | −1.122747 | −1.122747 |
| original / word / completion_02 / p / a | 0 | −0.297513 | −0.297513 |
| adjective_pair / emoji / affect_01 / p / a | +0.064435 | +1.723096 | +1.773870 |
| adjective_pair / word / affect_01 / p / a | 0 | +1.150312 | +1.155262 |

The largest observed `|s_padded − s_original|` is **0.2102706432 nats**. The largest original-to-padded single-candidate token-logprob difference is **0.1302242279 nats**. The independently shaped prefix-only execution differs from padded prefix token log probabilities by up to **0.0535953045 nats** on this panel.

The last row is informative: zero historical prefix residual does not imply zero whole-score shape sensitivity. Likewise, equal-length controls retain their original paired scores but differ from the separately shaped prefix-only execution. Agreement must be evaluated for the actual execution being proposed.

For original emoji `affect_01/p/b`, the earlier saved-score tail-only diagnostic changed `s` from +0.010518 to −0.008207. Matched-shape full scoring instead gives +0.062433. **Subtracting a saved prefix residual is not a substitute for re-executing at controlled shape.** The full continuation's probabilities can also depend on execution geometry.

## 4. Interpretation and paper boundary

On this deliberately selected panel, controlling model and normalization shape together, with explicit positions and masks, eliminated the shared-prefix discrepancy. Exact original replay and repetition make unexplained run-to-run drift a less plausible account of these particular observations. The combined execution change does not isolate a specific kernel, BF16 operation, or mask component. There is no FP32 reference or proof of absolute probability accuracy.

No H, effect-crossover, or all-four-alignment verdict can be reconstructed from one selected input per affected block. The prior tail-only audit's preserved H signs also do not establish H stability under the new full-scoring geometry. The existing 24 scenarios remain exploratory, author-labeled development material; no human interpretation, candidate equivalence, new-family generalization, or emoji-specific mechanism has been validated here.

Possible manuscript supplement wording:

> In an outcome-selected eight-input numerical diagnostic, 32 original-condition evaluations reproduced saved token scores exactly, and repeated evaluations agreed. Matching candidate execution and score-normalization shapes, with explicit positions and padding masks, yielded identical shared-prefix logit digests and token probabilities in all eight pairs. Full candidate-score differences shifted by up to 0.2103 nats without changing the preferred candidate on this panel. This diagnostic motivates versioned full-grid reassessment; it does not revise the reported behavioral or causal results.

This belongs in measurement validation or a supplement. It is not the paper's central claim about emoji meaning.

## 5. Resource and reproducibility record

The run completed in **16.1465 seconds**, including model preparation. Peak PyTorch allocated/reserved memory was **6,179.4 / 6,230 MiB**; maximum observed process memory was **6,906 MiB**. There were **116** occupancy checks, including **112** individually bound pre/post-forward checks, all allowed. Minimum observed free VRAM was **25,186 MiB**. No peer PID was observed at those boundaries; activity between checks and effects on peer throughput remain unmeasured. The interactive post-exit status check showed 10 MiB used and no compute process; that snapshot is separate from the archived run checks.

The independent checker passed. The companion notebook executed all three code cells on the Mac using saved records only. No new model downloads, tokenizer calls, generated responses, protected-bank reads, training, publication, or GitHub push occurred. The PDF remains unchanged, SHA-256 `43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898`.

Artifacts:

- [Independent validation](../validation/contextual_emoji_prefix_consistency_v0/portable_preflight/independent_validation.json), SHA-256 `4592c2d6af4ded9af5cbeff98363e958cdb90f2ed81a2e4a795b4768fbaf338b`.
- [Per-forward records](../validation/contextual_emoji_prefix_consistency_v0/portable_preflight/run56/forwards.jsonl), SHA-256 `09a8a4ca0296677017376299b85edf65ce1e1d1f405b5a69cc5213e4f769b4e0`.
- [Specification](../validation/contextual_emoji_prefix_consistency_v0/portable_preflight/specification.json), SHA-256 `751a81c07b518adf2359ffa4f65235c2ca5b41a3f8c75fee0450477e5419e8de`.
- [Executed notebook](../notebooks/contextual_emoji_prefix_consistency_v0.ipynb), SHA-256 `68e869a9390896fefaca97e2ce83494b090fdd9661c55ffff0933771507ff294`.

## 6. The next bounded decision

Before replacing any development numbers, specify a new full-scoring version and reassess the complete intended inventory, retaining the old version alongside it. The existing inventory has **1,248 sequence scores: 1,152 crossed plus 96 absent-cue scores**, corresponding to 624 candidate pairs rather than 1,248 independent scenarios. Its scope and any sentinel repeats must be specified before execution; the 56-call authorization does not launch this follow-up.

Then continue the agreed sequence: independent human interpretation/candidate validation, genuinely new scenario families, and output-linked natural-state causal tests. Annotation instructions and blinding can be prepared on CPU without consuming an untouched bank. Broad model scaling would not resolve these measurement and task-validity questions.
