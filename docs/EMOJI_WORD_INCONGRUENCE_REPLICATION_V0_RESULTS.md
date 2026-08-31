# Prospective emoji × word incongruence replication v0 result (T15-B)

[日本語](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.ja.md) · [Frozen protocol](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md) · [Closeout](../validation/emoji_word_incongruence_replication_v0/t15b_closeout.json)

## Result in one paragraph

T15-B **supported the prospectively frozen replication gate** for the narrow
response-shape candidate discovered in T15-A. All eight axes, all 48 target
prompts, and both model roles were replaced, and every true interaction was
compared with all seven non-self cross-axis checkerboards. At magnitude
`0.25`, the frozen target-level R1 median was `+0.020422` in SmolLM2 1.7B base
(95% target-bootstrap interval `[0.012887, 0.031510]`) and `+0.060397` in
Mistral 7B Instruct v0.3 (`[0.056621, 0.062194]`). Both lower bounds exceeded
zero under the predeclared two-model intersection rule with one-sided
Bonferroni alpha `0.025` per model. The result is not uniform: only six of the
eight separate primary-dose model × depth × sign intervals were positive and
two were mixed. Source-strength, response-energy, main-effect, order, depth,
and dose diagnostics also remained heterogeneous. The supported claim is
therefore a prospective recurrence of an operational *response-shape*
contrast—not emoji meaning, contradiction detection, natural behavior, a
causal circuit, tokenizer independence, instruction-tuning invariance, a scale
law, or model-population generality.

| Frozen scope | Completed result |
|---|---:|
| Model roles | 2/2 complete |
| New axes | 8 |
| New target prompts | 48 |
| Cross-axis shifts | all 7 non-self shifts |
| Source sequences | 4,624 |
| Steering-response rows | 491,712 |
| Depths × doses × signs | 2 × 2 × 2 |
| Generation calls | 0 |
| Bootstrap schedule | 20,000 target or axis-cluster replicates per reported median |

The complete run audit returned
`complete_closed_to_adaptive_selection`, and the analysis validator returned
`replication_gate=support`.

## Frozen primary replication gate

The source family is T15-A's A1 statistic: full-vocabulary CountSketch
response coherence across the eight true interaction axes minus the median
coherence across the structural cross-axis controls. T15-B strengthened the
null family from three cyclic shifts to all seven non-self shifts.

For each model and target at magnitude `0.25`, R1 takes the median of A1 over
the two frozen late depths and two steering signs. The 48 resulting target
values are the bootstrap units. Models are not pooled for the decision.

| Model | Target median | 95% bootstrap interval | Targets > 0 | Frozen gate |
|---|---:|:---:|---:|:---:|
| SmolLM2 1.7B base | +0.020422 | [0.012887, 0.031510] | 37/48 | pass |
| Mistral 7B Instruct v0.3 | +0.060397 | [0.056621, 0.062194] | 47/48 | pass |

The frozen decision required both 2.5th-percentile lower bounds to exceed zero.
Both passed, so the intersection decision is `support`. This is the only
multiplicity-qualified replication decision in T15-B.

## The separate cells remain visible

Pooling depth and sign was frozen before model execution. It must not hide the
cell-level pattern:

| Model | Depth | Sign | A1 true − all-cross median | 95% interval |
|---|---:|---:|---:|:---:|
| Mistral 7B Instruct v0.3 | 0.875 | − | +0.102173 | [0.093549, 0.111754] |
| Mistral 7B Instruct v0.3 | 0.875 | + | +0.076474 | [0.062852, 0.086544] |
| Mistral 7B Instruct v0.3 | 1.0 | − | +0.007967 | [−0.002336, 0.014047] |
| Mistral 7B Instruct v0.3 | 1.0 | + | +0.041554 | [0.037379, 0.051341] |
| SmolLM2 1.7B base | 0.875 | − | +0.015849 | [−0.007899, 0.029780] |
| SmolLM2 1.7B base | 0.875 | + | +0.053125 | [0.028179, 0.088221] |
| SmolLM2 1.7B base | 1.0 | − | +0.015325 | [0.004155, 0.024472] |
| SmolLM2 1.7B base | 1.0 | + | +0.014716 | [0.000623, 0.028019] |

Six intervals are positive and two are mixed. Across both doses, ten of the 16
A1 intervals are positive, five are mixed, and one is negative. T15-B therefore
replicates the pooled target-level candidate, not T15-A's stronger-looking
16/16 cell pattern.

## Secondary families narrow the result

A0 compares individual incongruent and congruent joint-additivity residual
magnitude. A3 compares the source RMS of the balanced true direction with the
cross-axis directions. All four model × depth intervals were mixed in both
families. The recurring response shape is therefore not explained by a
uniformly larger source interaction vector or a common positive excess in
individual incongruent residual magnitude.

The primary-dose interval counts below retain the other fixed diagnostics.
“Mixed” includes intervals touching or spanning zero.

| Family and endpoint | Positive | Negative | Mixed | Total |
|---|---:|---:|---:|---:|
| A0 incongruent − congruent source residual | 0 | 0 | 4 | 4 |
| A3 true − cross source RMS | 0 | 0 | 4 | 4 |
| A2 true − cross response, JS | 4 | 1 | 3 | 8 |
| A2 true − cross response, total variation | 3 | 1 | 4 | 8 |
| A2 true − cross response, logit RMS | 6 | 2 | 0 | 8 |
| A2 true − cross response, entropy change | 2 | 2 | 4 | 8 |
| A4 word-main − emoji-main, JS | 6 | 0 | 2 | 8 |
| A4 word-main − emoji-main, logit RMS | 2 | 6 | 0 | 8 |
| A5 emoji→word − word→emoji, JS | 6 | 1 | 1 | 8 |
| A5 emoji→word − word→emoji, entropy change | 4 | 4 | 0 | 8 |
| A6 final − late depth at primary dose | 0 | 2 | 2 | 4 |
| A6 dose `0.25 − 0.125` | 3 | 3 | 2 | 8 |

Argmax-flip intervals were mixed in all eight primary-dose A2, A4, and A5
cells. There is no universal energy increase, word dominance, emoji dominance,
source-order winner, late-depth advantage, or monotone dose law.

## Procedural boundary

Two runtime attempts failed before model weight loading and before any T15-B
model forward. The first exposed missing installed-package metadata in the
isolated dependency target. The second exposed a loader-boundary bug: a
historical T13 tokenizer receipt was being checked against the new T15-B target
helper. Both failures are preserved in the runtime preflight receipt. The
repair isolated the original T13 target helper during historical model loading,
restored the T15-B helper before capture, added a regression test, and generated
a new final freeze. No scientific outcome existed when the repair was made.

After that freeze, SmolLM2 and Mistral each completed exactly 245,856 response
rows. Scientific values remained closed until the two-role audit passed. The
first complete analysis passed its output validator without a post-open
scientific-code repair.

## Landing and paper-gate reading

T15-B lands as **prospective holdout support for an operational response-shape
candidate with cell heterogeneity**. It replaces T15-A's axes, target bank, and
model roles while strengthening the cross-axis controls. This satisfies Phase I
gate 5's requirement for at least one independent-model replication of this
narrow candidate.

T15-B also supplies a claim-specific target-cluster bootstrap and a frozen
two-model multiplicity rule for R1. Paper-wide statistical qualification still
depends on freezing the manuscript claim table and keeping exploratory families
out of the primary claim. `confirmatory_status` remains false, and no semantic
or causal claim is authorized.

## Next gate

T15-C may now be designed, but it remains a separate causal experiment. A clean
version must:

- freeze a prospectively defined interaction-residual subspace;
- use another untouched target bank;
- predeclare necessity, sufficiency, and restoration interventions;
- retain fixed shams, explicit-zero checks, and positive controls;
- forbid selecting a runner-up model, depth, sign, dose, axis, endpoint, or
  control from T15-B outcomes.

The most informative immediate question is no longer whether A1 recurs. It is
whether removing, adding, and restoring the prospectively defined interaction
subspace changes that response-shape coherence in the predicted direction.

## Evidence anchors

| Evidence | Anchor |
|---|---|
| Protocol freeze | commit `fb325a1` |
| Analysis-compatibility checks | commit `f835999` |
| Tokenizer binding | commit `9869129` |
| Pre-forward loader-boundary repair | commit `8c658f6` |
| Final execution freeze | commit `966ea30`; manifest SHA-256 `b56a68b3aa7d8e890a9121d009e517f17329abd92c346304d3558eff1fb61f1a` |
| Design preflight | [design_preflight.json](../validation/emoji_word_incongruence_replication_v0/design_preflight.json), SHA-256 `0e584024dbe57ebfb094cebb984160c1b6e75c7883b57014a0df9638c249ae74` |
| Tokenizer preflight | [tokenizer_preflight.json](../validation/emoji_word_incongruence_replication_v0/tokenizer_preflight.json), SHA-256 `2c28af5eb89c6184eaa4d8309d8c34bb45d48483342b32b72076ede412663f38` |
| Preserved pre-forward failures | [runtime_preflight_failures_v0.json](../validation/emoji_word_incongruence_replication_v0/runtime_preflight_failures_v0.json) |
| Complete aggregate | Furnace path `/home/ryospiralarchitect/scratch/glyphprobe-t15b-analysis-966ea30/analysis.json`; SHA-256 `f0c98942943addcc9713283b2cb54491d16a0232711db39fc0d51d0536b4edfd` |
| Run root | `/home/ryospiralarchitect/scratch/glyphprobe-t15b-runs-966ea30` |
| Compact result | [t15b_closeout.json](../validation/emoji_word_incongruence_replication_v0/t15b_closeout.json), SHA-256 `70c5b9194bd7c0e685dbf51a3ad83f258125c6cd7ebc4fd0f185821a32cf8187` |

The complete aggregate and raw ledgers remain outside the repository at the
recorded furnace paths. Their hashes establish identity; the compact closeout
does not close the evidence-archive deposit gate.
