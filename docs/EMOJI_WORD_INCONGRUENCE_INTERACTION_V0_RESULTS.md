# Emoji × word incongruence interaction v0 result (T15-A)

[日本語](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.ja.md) · [Frozen protocol](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md) · [Closeout](../validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json)

## Result in one paragraph

The frozen T15-A grid found a shared **response-fingerprint candidate**, not
evidence that the models understand contradiction. At the primary dose, the
balanced within-axis interaction direction produced more coherent
full-vocabulary response shapes than the median of three structurally matched
cross-axis interactions in all 16 model × depth × sign cells; every
20,000-replicate target-bootstrap interval was entirely above zero. This was
not a generic increase in response energy: JS, total variation, logit RMS,
entropy, and argmax-flip contrasts were heterogeneous. Nor was there a common
positive incongruent-minus-congruent excess in individual joint-additivity
residual magnitude. The bounded interpretation is therefore that the frozen
experimenter-labeled pairings induce unusually reusable *shapes* of
next-token-distribution change across axes. T15-A is exploratory, uses public
targets and an outcome-informed model/depth roster, and authorizes no claim of
meaning, contradiction detection, natural behavior, causal circuitry,
tokenizer independence, scale, or model-population generality.

| Fixed scope | Completed result |
|---|---:|
| Model roles | 4/4 complete |
| Source sequences | 5,152 |
| Steering-response rows | 393,472 |
| Public targets | 32 |
| Axes | 8 |
| Depths × doses × signs | 2 × 2 × 2 |
| Generation calls | 0 |
| Bootstrap schedule | 20,000 target- or axis-cluster replicates per reported median |

The run audit is `complete_closed_to_adaptive_selection`. The analysis is a
complete seven-family exploratory analysis with no significance test and no
confirmatory verdict.

## Primary response-fingerprint family

For each target, A1 first reduces four wrapper folds and two source orders by a
coordinatewise median. It then computes pairwise CountSketch cosine coherence
across the eight true interaction axes and subtracts the median coherence of
the three cyclic cross-axis controls. The table reports the target-level
median at the frozen primary magnitude `0.25`. “True” and “cross” are shown as
separate target medians; their difference need not equal the median of paired
target differences. Intervals resample the 32 targets 20,000 times.

| Model | Depth | Sign | True | Cross | True − cross | 95% interval | Targets > 0 |
|---|---:|---:|---:|---:|---:|:---:|---:|
| Llama 3.2 3B base | 0.875 | − | 0.471595 | 0.290370 | +0.155243 | [0.141315, 0.198899] | 32/32 |
| Llama 3.2 3B base | 0.875 | + | 0.389174 | 0.150823 | +0.231919 | [0.224002, 0.238301] | 32/32 |
| Llama 3.2 3B base | 1.0 | − | 0.364638 | 0.130069 | +0.232216 | [0.227864, 0.235742] | 32/32 |
| Llama 3.2 3B base | 1.0 | + | 0.347363 | 0.093193 | +0.255624 | [0.249632, 0.259629] | 32/32 |
| OLMo 2 1B base | 0.875 | − | 0.195736 | 0.036709 | +0.062355 | [0.007663, 0.203024] | 22/32 |
| OLMo 2 1B base | 0.875 | + | 0.266686 | 0.096175 | +0.122757 | [0.044837, 0.341355] | 26/32 |
| OLMo 2 1B base | 1.0 | − | 0.137302 | 0.088485 | +0.050162 | [0.025334, 0.112551] | 23/32 |
| OLMo 2 1B base | 1.0 | + | 0.517765 | 0.104452 | +0.397596 | [0.363295, 0.419672] | 32/32 |
| Qwen 2.5 3B base | 0.875 | − | 0.571834 | 0.171156 | +0.411275 | [0.362851, 0.439045] | 32/32 |
| Qwen 2.5 3B base | 0.875 | + | 0.515728 | 0.120726 | +0.389015 | [0.365101, 0.407404] | 32/32 |
| Qwen 2.5 3B base | 1.0 | − | 0.364208 | 0.080717 | +0.290625 | [0.282621, 0.296236] | 32/32 |
| Qwen 2.5 3B base | 1.0 | + | 0.403310 | 0.144780 | +0.257903 | [0.248553, 0.266084] | 32/32 |
| Qwen 2.5 7B base | 0.875 | − | 0.440099 | 0.152445 | +0.263563 | [0.202882, 0.330396] | 29/32 |
| Qwen 2.5 7B base | 0.875 | + | 0.471418 | 0.377342 | +0.161788 | [0.046407, 0.214518] | 22/32 |
| Qwen 2.5 7B base | 1.0 | − | 0.263618 | 0.087359 | +0.176893 | [0.158664, 0.182732] | 32/32 |
| Qwen 2.5 7B base | 1.0 | + | 0.268406 | 0.090104 | +0.184350 | [0.170690, 0.200865] | 32/32 |

All primary A1 intervals are descriptively positive. None of the true or
cross-axis vectors entering the cosine calculations was zero. This is a
particularly clean recurrence of response *shape*, but it is not a
multiplicity-adjusted significance result and does not convert the public
targets into a confirmatory bank.

## Source diagnostics narrow the interpretation

A0 asks whether individual incongruent pairs have larger frame-relative
`pair − emoji − word` residual RMS than congruent pairs. A3 instead asks
whether the balanced true interaction direction has greater source RMS than
the matched cross-axis directions. Each interval resamples the eight axes.

| Model | Depth | A0 incongruent − congruent residual RMS | A3 true − cross direction RMS |
|---|---:|:---:|:---:|
| Llama 3.2 3B base | 0.875 | −0.000898 [−0.006287, 0.001590] | +0.009549 [0.003003, 0.012452] |
| Llama 3.2 3B base | 1.0 | −0.002096 [−0.010420, 0.001454] | +0.021266 [0.005608, 0.027678] |
| OLMo 2 1B base | 0.875 | −0.001376 [−0.003758, −0.000035] | +0.001366 [−0.001213, 0.003739] |
| OLMo 2 1B base | 1.0 | −0.006660 [−0.011792, −0.002203] | +0.004937 [−0.001378, 0.008668] |
| Qwen 2.5 3B base | 0.875 | +0.003849 [−0.023329, 0.037773] | +0.065395 [0.027668, 0.074031] |
| Qwen 2.5 3B base | 1.0 | −0.002306 [−0.106844, 0.024530] | +0.123474 [0.046869, 0.170550] |
| Qwen 2.5 7B base | 0.875 | +0.008598 [−0.030837, 0.027171] | +0.103704 [0.054355, 0.160173] |
| Qwen 2.5 7B base | 1.0 | −0.136574 [−0.223462, 0.070531] | +0.284244 [0.141480, 0.421626] |

A0 has zero positive intervals, two negative intervals, and six mixed
intervals. There is no common positive excess in the magnitude of individual
pair residuals. A3 is positive in six of eight cells and mixed in both OLMo
cells. Thus the strongest shared fact is A1 response coherence; source strength
supports it in Llama and Qwen but is not a universal explanation.

## Energy, main effects, and order do not supply an easy alternative

The following counts classify the 16 primary-dose model × depth × sign
intervals. “Mixed” includes intervals touching or spanning zero.

| Family and endpoint | Positive | Negative | Mixed | Total |
|---|---:|---:|---:|---:|
| A2 true − cross response, JS | 8 | 3 | 5 | 16 |
| A2 true − cross response, total variation | 6 | 3 | 7 | 16 |
| A2 true − cross response, logit RMS | 9 | 5 | 2 | 16 |
| A2 true − cross response, entropy change | 7 | 6 | 3 | 16 |
| A2 true − cross response, argmax flip | 0 | 0 | 16 | 16 |
| A4 word-main − emoji-main, JS | 8 | 5 | 3 | 16 |
| A4 word-main − emoji-main, total variation | 5 | 6 | 5 | 16 |
| A4 word-main − emoji-main, logit RMS | 4 | 9 | 3 | 16 |
| A5 emoji→word − word→emoji, JS | 3 | 6 | 7 | 16 |
| A5 emoji→word − word→emoji, logit RMS | 7 | 6 | 3 | 16 |

The A1 recurrence therefore cannot be summarized as “true interactions are
always stronger,” “words dominate emoji,” “emoji dominate words,” or “one
source order wins.” The argmax endpoint is also uninformative at this dose:
all A2, A4, and A5 argmax-flip medians have intervals at zero.

## Depth and dose remain heterogeneous

At magnitude `0.25`, the final-minus-late A1 depth contrast is positive in four
cells, negative in three, and mixed in one. Llama is positive for both signs;
Qwen 2.5 3B is negative for both; OLMo and Qwen 2.5 7B split by sign. Across
all 16 depth × sign cells, the `0.25 − 0.125` dose contrast is negative in nine,
positive in one, and mixed in six. The only positive dose interval is OLMo
depth 1.0, positive sign (`+0.027062`, interval `[0.007392, 0.074544]`).

Higher dose does not monotonically strengthen coherence, and later depth does
not move every model in the same direction. This rules out a dose law or scale
law from the present grid.

## Post-open implementation repair

The original frozen v0 analyzer failed closed in A0 before producing an
analysis file or printing model values. It asserted eight repeats per
congruence class, while the frozen factorial contains two cells × two source
orders × four wrappers = 16. The process had read response values before the
assertion, so the repair is explicitly post-open.

The versioned v1 repair changed only that structural assertion from 8 to 16.
It did not change any estimand, family, endpoint, model, depth, dose, sign,
target, axis, control shift, aggregation, bootstrap seed, bootstrap count, or
claim boundary. The preserved failure receipt and repair manifest make this
procedural limitation part of the result rather than hiding it.

## Landing and next gate

T15-A lands as an **exploratory, shared non-additive response-fingerprint
candidate**. The true balanced pairings create vocabulary-response shapes that
recur across operational axes more strongly than checkerboard controls, even
when response energy, main-effect dominance, and order effects vary. That is a
useful causal target, not a semantic conclusion.

No same-bank rescue or component search follows from this result. A prospective
T15-C would require:

- new operational axes not used to define this candidate;
- a new untouched target bank;
- an independent model or backend role;
- a frozen interaction-residual subspace intervention;
- necessity, sufficiency, and restoration tests fixed before outcome access.

Until those conditions are met, `confirmatory_status`,
`semantic_understanding_claim_authorized`, and `causal_claim_authorized` all
remain false. T15-A closes no Phase I paper gate.

## Evidence anchors

| Evidence | Anchor |
|---|---|
| Frozen protocol | commit `b48b1c9` |
| Runtime-helper contract checks | commit `d10e6b4` |
| Final execution freeze | commit `72add92`; manifest SHA-256 `d528276748997331c0864b7af1b5bbd75b74d7f771f4d94b7f5ae868d0b6030d` |
| Tokenizer preflight | [tokenizer_preflight.json](../validation/emoji_word_incongruence_interaction_v0/tokenizer_preflight.json), SHA-256 `e68a40571cc3271b74aae0034bb3eba3bfaea668373975405726a7223c9d164d` |
| Preserved v0 failure | [analysis_v0_failure.json](../validation/emoji_word_incongruence_interaction_v0/analysis_v0_failure.json) |
| Analysis repair | commit `ea658b9`; manifest SHA-256 `d72cb667a0f0d1a37936a88d56a0b6640d9f7f34fe85e1b8faafd70fde3803d8` |
| Complete repaired aggregate | Furnace path `/home/ryospiralarchitect/scratch/glyphprobe-t15-analysis-repair-v1-ea658b9/analysis.json`; SHA-256 `f089b31fbea245ad9fe4e5727c7dc618fa38e79bc27474c76ef435bd51fec5fe` |
| Run root | `/home/ryospiralarchitect/scratch/glyphprobe-t15-runs-72add92-r2` |
| Compact result | [t15a_closeout.json](../validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json), SHA-256 `d9ad4842177448501acdf2800349f50c92cceac3ccc2a6526a7fc8bceb160f87` |

The complete aggregate and raw ledgers remain outside the repository at the
recorded furnace paths. Their hashes establish identity; the compact closeout
does not replace the still-open archival-deposit gate.
