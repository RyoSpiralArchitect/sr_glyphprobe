# Paper 2 discussion notes: from a conditional path effect to K/V dissection

[日本語](PAPER2_DISCUSSION_NOTES_V0.ja.md) | [T22 results](T22_CPU_LEXICAL_RESULTS_V0.md) | [Paper 1 final audit](POST_REVIEW_EVIDENCE_RESULTS_V0.md)

Status: **retrospective interpretation and research agenda, 2026-10-20 JST**.
This note was written after observing the eight-item T22 CPU results. It is
not a preregistration, a new confirmation, or a revision of Paper 1's verdicts.
Future entries should record their date, evidence, interpretation, alternatives,
and next discriminating measurement separately.

## 1. What Paper 1 leaves open

Paper 1 moves from lexical retrieval to a narrowly conditioned intervention.
T19's nine-configuration comparison supports lexical structure under its
matched controls, but does not establish a semantic mediator. The tested
rank-8 T19/T20 mediation accounts were unsupported or uncalibratable in their
specified tests; this does not rule out every other subspace or mechanism.

T21-C provides the positive intervention result: after replacing the readout
residual at block 21 with the same item's codepoint-view state, donor K+V
replacement at later glyph positions changes lexical cosine margin. All 195
eligible remaining items were retained. Adjusted decrement/restoration means
were **0.002326 / 0.002267**, with positive simultaneous lower bounds in the
original five-contrast family. Absolute mean top-1 decrement/restoration were
both **zero**. The subsequent own-keyword/competitor decomposition was
descriptive and did not create additional confirmatory tests.

| Remaining question | What the existing evidence cannot decide |
|---|---|
| Keys, values, and their joint effect | T21 changes K and V together; it cannot allocate the margin change between those intervention factors. |
| Own alignment versus competition | A margin change can reflect the own alias, the strongest competitor, or both; competitor identity can also change. |
| Induced versus ordinary computation | The codepoint residual reset is part of the estimand. Necessity or sufficiency in an intact natural context was not tested. |
| Position versus matched exposure | Equal token counts do not equalize attention mass, semantic content, or every positional property. |
| Symbol specificity | The same path intervention has not been compared with a non-emoji symbol panel. |
| Readout versus behavior | Fixed-gallery cosine, retrieval rank, and generated behavior are different outcomes; the latter was not measured. |
| Generality and fresh confirmation | One checkpoint, fixed donors/gallery, and two carriers do not define a universal mechanism. The original matched pool has no unused items remaining. |

The historical p2 and c1 v1 banks remain protected and unavailable for new
design or confirmation. A new confirmatory population must be prepared and
reserved separately; neither the eight canary items nor the already evaluated
384-item panel becomes fresh through a new analysis.

## 2. The framing for Paper 2

Working question: **How do local key/value interventions reshape lexical
readout and downstream attention under a fixed readout-state intervention?**

The initial contribution is a controlled decomposition of interventions and
their measurable consequences. It does not begin by assigning “routing” to
K and “meaning” to V. At a fixed layer input, V-only replacement preserves
the attention weights used at that layer. The altered attention output can
change the next layer's residual and query, and hence later attention. K-only
replacement changes how values are mixed; the information in those values
still matters. Neither factor is an isolated psychological variable.

Even a single attention head is jointly dependent on its weights and values.
At a fixed query, changing weights from a0 to a1 and values from v0 to v1
introduces the cross term `(a1 - a0) @ (v1 - v0)`. Multiple intervened layers,
residual updates, normalization, cosine scoring, and taking a maximum over
competitors add further dependencies. Thus `Delta_KV - Delta_K - Delta_V`
is a useful descriptive nonadditivity contrast, not an identified biological
or semantic interaction, nor a percentage of meaning carried by values.

The paper should connect three levels without collapsing them: local
intervention correctness; changes in saved attention and readout states;
and any subsequently tested task outcome. A result at one level does not
automatically establish the next.

## 3. Why this was the first experiment

The [initial decision memo](T22_KV_DISSECTION_FIRST_STEP_V0.md) chose a
reference / K-only / V-only / joint-KV comparison. This removes one ambiguity
in T21 while retaining its block-21 reset, blocks 22–27, distance 8, pipe and
article-a carriers, two predetermined token-count-matched donors, and
glyph-versus-equal-count-suffix comparison. Replacement is query-local:
only the readout query receives the substituted donor tensors.

The original eight exposed canary inputs were used to establish engineering
parity before interpretation. Because historical GPU arrays were unavailable,
the CPU run reacquired the pinned Llama 3.2 3B BF16 checkpoint. Same-CPU stock,
legacy-adapter, neutral, no-op, roundtrip, and off-target checks passed; this
does not establish exact replay of the historical RTX 5090 run.

The [lexical protocol](T22_CPU_LEXICAL_CANARY_V0.md) then froze the scoring
choices before inspecting lexical outcomes. It retained the own alias plus
the original 128 source aliases, reacquiring these states on the same CPU
runtime. Active and neutral outputs use identical batch slots. For each item:

`E = active - neutral`

`Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)`

Positive margin Delta means glyph replacement reduces the own-versus-best-
competitor margin more than suffix replacement. The absolute glyph decrement
is separately `-mean(E_glyph,X)`. The sample has **eight target items**, not
32 independent carrier/donor observations. No p-value, population confidence
interval, efficacy threshold, or winning operation was specified.

## 4. The first reading, and the alternatives it leaves alive

| Operation | Mean adjusted margin decrement | Item sample SD | Item range |
|---|---:|---:|---:|
| Reference | 0 | 0 | 0 to 0 |
| K | +0.000437 | 0.001765 | −0.002796 to +0.002813 |
| V | +0.001805 | 0.003647 | −0.003502 to +0.009042 |
| KV | +0.000899 | 0.004175 | −0.007956 to +0.005689 |

**Observation.** V-only replacement changes the lexical readout in this
conditioned computation. Every nonreference operation has six positive and
two negative item contrasts. The mean nonadditivity contrast is **−0.001343**
(sample SD 0.001894; range −0.003930 to +0.001195).

**Reading.** The joint-KV result is not numerically reconstructed by adding
the separate K and V contrasts on these eight items. V has the largest sample
mean, but this is not evidence of a population ordering or a reason to choose
V as the next experiment's sole condition. Item heterogeneity and the fixed
donor/gallery choices remain consequential alternatives to a general account.
Nonadditivity could arise within attention, across later layers, or in the
nonlinear scoring operation; this comparison does not localize it.

**Observation.** For V, adjusted own-cosine and max-competitor components are
+0.001094 and −0.000711; their difference is the +0.001805 margin contrast.
K's corresponding components are −0.009472 / −0.009909, and KV's are
−0.008112 / −0.009010. These are position-adjusted contrasts, not raw cosine
changes. Adjusted top-1 decrement is −0.0625 for K/KV and zero for V; all
nonzero top-1 contrast comes from item 4. Positive mean margin decrement
therefore does not imply a corresponding top-1 loss.

**Reading.** A one-dimensional “own keyword removed” story is incomplete.
Both alignment and competition must remain visible, including the changing
strongest competitor. The discrete fixed-gallery result also provides no
evidence of generated behavioral benefit.

**Observation.** Local V-only attention weights are exactly unchanged at each
layer's own input. Yet the mean active-versus-neutral headwise attention L1
distance is 0 at block 22, 0.008635 at block 23, and 0.028619 at block 27.

**Reading.** The downstream-query qualification is observed, not merely a
theoretical caveat. V-only preserves a local weighting operation, not the
whole later attention trajectory. A reference-attention clamp could test a
different counterfactual, but has not been run and would itself alter the
computation being studied.

## 5. The next measurement and what would change the account

The next empirical step remains the **384-item exploratory comparison on
already evaluated items**, retaining all four operations and the frozen
candidate, donors, gallery, and position controls. It has **not run**. The
eight-item signs must not select, cancel, or retune it. Before acquisition,
publish its exact CPU specification, aggregation, diagnostics, and execution
budget; record any engineering-driven amendment before outcomes are inspected.
No numerical population decision threshold is supplied by this retrospective note.

The larger panel can show whether the observed signs, dispersion, competition
patterns, and nonadditivity recur more broadly within that exposed panel.
Near-zero or reversed patterns must be retained and would weaken the
eight-item reading. Even stable positive results would remain conditional
exploratory evidence, not semantic transport or fresh confirmation.

Later proposals need separate prospective designs:

| Proposal, currently unrun | Distinction it could help test |
|---|---|
| Clamp later attention to a stated reference; separate intervention blocks | Direct local value mixing versus propagated changes in later computation, conditional on the clamp. |
| Preserve own/competitor/donor scores and inspect attention mass across controls | Relative alignment versus competition, and unequal effective exposure under token-count matching. |
| Compare intact and reset-conditioned computations | Dependence on the artificial residual-reset context. |
| Matched non-emoji symbols, alternative carriers/donors, and a newly reserved bank | Symbol specificity and generality beyond this exposed panel. |
| Predefined rank and generated-task outcomes | Whether geometric movement has a measurable operational consequence. |

These are questions for design, not claims that the current experiment has
answered them. In particular, observed downstream attention differences alone
do not identify how much of the lexical effect they mediate.

## 6. Evidence trail and reproducibility

Use the [engineering record](T22_CPU_ENGINEERING_V0.md),
[frozen lexical protocol](T22_CPU_LEXICAL_CANARY_V0.md), and
[complete results](T22_CPU_LEXICAL_RESULTS_V0.md) for implementation details,
all eight item values, acquisition counts, hashes, and model/runtime pins.
The initial proposal and lexical protocol retain their pre-acquisition status
wording as historical documents; the results and this note carry current status.

The PR preserves the eight engineering-parent NPZ files and alias/score
archives, with byte-identical receipts. The independent NumPy-only audit
recomputes 66,048 cosines over 512 rows, all paired contrasts, summaries,
CSV alignment, and attention diagnostics. It does not repeat the model
forwards or the full tensors omitted at acquisition. Portable replay commands
are in the results document. Numerical reconstruction is an audit of one
acquisition, not an independent scientific replication.

## 7. Design entry — 2026-10-20 JST

The [384-item CPU design](T22_KV_EXPLORATION_CPU_V0.md) now fixes the original
384 targets, 128 sources, donors, all four operations, aggregation, diagnostics,
and resource policy. The earlier eight stay in the panel and are explicitly
marked as having known T22 outcomes. No condition was chosen by their signs.

Timing receipts motivated retaining the 16-row measurement while removing
the repeated 88-row legacy comparison from the proposed production schedule.
That reduced runner is not implemented or admitted yet: it must exactly replay
all 26 nonlegacy arrays for each of the original eight items and the alias
rows before target 8. The approximately 14.8/21.7-hour mean/slowest-item timing
scenarios are extrapolations, not measured new-runner performance.
The frozen design has no new model forwards; an execution manifest binding
validated runner/analysis hashes and runtime must precede acquisition.

Frozen specification SHA-256:
`b3d18ec4fac4588ca784c6caea6fbb03a2703deec7e503a60e690a540d14c19c`.
The source-bound design suite passed 22 tests with zero skips; the deterministic
input/design audit passed. These checks admit the design artifact, not a model run.
