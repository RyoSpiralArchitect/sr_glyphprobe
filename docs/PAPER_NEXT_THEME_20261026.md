# Next-paper theme: from readable symbols to causal use

[日本語](PAPER_NEXT_THEME_20261026.ja.md) · [Prior discussion](PAPER2_DISCUSSION_NOTES_V0.md) · [T22 results](T22_CPU_LEXICAL_RESULTS_V0.md)

Status: **working research agenda, October 26, 2026**. This note interprets
existing evidence and proposes the next paper's focus. It is not a frozen
protocol, a preregistration, an execution approval, or a new experimental
result. It does not amend the already fixed T22 384-item design or the
[published preprint](https://doi.org/10.5281/zenodo.23376699).

## Proposed theme and narrow question

**From readable symbols to causal use: how local K/V changes propagate
through later computation.**

The broad motivation is to understand when information associated with an
emoji is used by a language model. The next paper should answer a smaller,
testable question first:

> Under specified interventions, how can changes in a lexical readout be
> distinguished between local value mixing, altered later computation, and
> nonlinear scoring? How dependent are those relationships on the readout reset?

This framing connects the first paper's lexical retrieval and conditional
attention-path result to the new K/V comparison. CLDR correspondence remains
an operational lexical readout, not the study's ultimate purpose or a human
semantic label. The proposed contribution is a controlled account of how an
intervention changes later computation and measured outcomes, with its
conditions made explicit. It does not assume that a semantic mechanism or a
behavioral benefit will be found.

## Evidence we can use now

| Evidence | Current result | Boundary for the next paper |
|---|---|---|
| Keyword retrieval (T19-L) | The specified emoji keyword-versus-codepoint comparison passed across nine prespecified model/tokenizer configurations, including exact four-view token-count matching. | Lexical readability does not establish human meaning, visual perception, or use in a generated response. |
| Fixed/optimized subspace interventions (T19-C/T20-C) | The tested rank-8 accounts were unsupported or uncalibratable at their primary sites. | These bounded outcomes do not reject every low-rank account. |
| Attention-path intervention after readout reset (T21-C) | On 195 items, the five prespecified margin contrasts had positive simultaneous lower bounds; absolute mean top-1 decrement and restoration were zero. | The block-21 codepoint-state reset is part of the tested computation. Ordinary-state necessity and sufficiency remain untested. |
| Explicit-report readout qualification | The reserved direct/minimal format yielded 88/96 correct, four errors and four ties; the two direct A/B mappings yielded 104/192 correct. Both fixed requirements failed. | Numerical checks passed, but the response measure was not qualified. These repeated comparisons of authored roots are not independent population samples or human semantic judgments. |
| Key/value comparison (T22 exposed-eight) | Adjusted mean margin decrements were K +0.000437, V +0.001805 and KV +0.000899; mean KV−K−V was −0.001343. | Eight previously exposed target items, not 32 independent carrier/donor observations. Descriptive, single-checkpoint, CPU BF16 evidence; no statistical winner or fresh confirmation. |
| T22 exposed-384 design | Inputs, operations, metrics and execution gates are fixed. Acquisition is unrun and execution is not admitted. | A design audit is not an acquired dataset. The reduced runner still needs implementation and validation. |

For the qualification denominators and failures, see the
[current claim boundary](../paper/CURRENT_CLAIMS_20261015.md) and
[qualification protocol](READOUT_QUALIFICATION_V1.md). The T22 result and
its independent stored-data audit are linked from the
[complete eight-item report](T22_CPU_LEXICAL_RESULTS_V0.md). That audit
reconstructs saved scores; it is not a second model acquisition or exact replay
of the historical GPU run.

### What the V-only observation does and does not tell us

At a fixed layer input, the V-only operation leaves that operation's query,
keys, mask and attention weights unchanged by construction. The exact local
weight-equality check is an implementation invariant, not a discovery that
values contain meaning independently of attention.

The informative observation is elsewhere: active-versus-neutral attention
differs in later layers. Mean headwise L1 difference was zero at block 22,
0.008635 at block 23 and 0.028619 at block 27. Changed earlier outputs can
alter later residuals and queries. This demonstrates that preserving local
weights does not preserve the entire subsequent attention trajectory.
It does **not** identify how much of the lexical effect is caused by that
later attention change; a discriminating intervention has not been run.

Likewise, the negative mean nonadditivity contrast does not localize an
interaction. Attention mixing, repeated residual updates, normalization,
cosine scoring and changes in the highest-scoring competitor can all matter.
K is not a pure routing variable and V is not a pure meaning variable.
Positive margin movement must also stay separate from top-1: T22's adjusted
top-1 decrement was zero for V and −0.0625 for K/KV, with all nonzero contrast
coming from one of the eight items.

## Three directions, ranked for the next paper

| Priority | Direction | Decisive distinction and role |
|---|---|---|
| **1 — proposed center** | Local intervention, propagated computation and metric effects | Separate single-block from multi-block operations, reference-fixed from freely evolving later attention, and state changes from the readout's nonlinearities. Compare reset-present with intact-state conditions in a separate prospective design. This most directly resolves ambiguities left by T21/T22. |
| **2 — extension after measurement qualification** | From internal changes to task outcomes | Establish a response measure that passes its own controls on new materials before interpreting an emoji task or output-linked intervention. Preserve unsupported, unknown and tied responses. Current qualification failures prohibit treating the existing scorer as a validated semantic measure. |
| **3 — generality and specificity** | Emoji versus non-emoji symbols and words | Use prospectively specified comparison panels, donors and carriers, with tokenization and effective attention exposure documented. These comparisons test the scope of an effect; they must precede any emoji-specific claim. |

The order is a choice about a tractable paper, not a judgment that symbols,
words or behavior are unimportant. A mechanism paper can end with a clear
conditional result while behavioral transfer remains open. Combining all
three into one mandatory positive claim would obscure what each test decides.

## Sequence: preserve the current design, then open a new one

1. **Close the fixed exposed-384 comparison without outcome-based selection.**
   Keep all four operations, both carriers, both donors, original ordering,
   position controls and recorded endpoints in the
   [existing design](T22_KV_EXPLORATION_CPU_V0.md). The known first eight stay
   in the panel. Implement and validate the reduced runner and bind the
   execution sources/runtime before acquisition. Before target 8, reproduce
   all 26 retained nonlegacy arrays for every original canary and the required
   alias rows exactly. Engineering failure stops interpretation; favorable
   effects cannot waive a failed check. Partial effects must not choose layers,
   conditions or exclusions. This note does not launch that work.
2. **Specify the discriminating follow-up separately.** Fix the reset-present
   and intact-state comparisons, intervention blocks, local versus multi-block
   schedules, reference-attention clamp, donors, neutral/sham operations,
   position controls, reporting units and decision criteria before its new
   outcomes. A clamp defines an additional counterfactual computation; it
   does not automatically identify a natural mediation fraction. Record any
   implementation or resource amendment before continuing rather than silently
   changing the existing protocol.
3. **Separate state-space and measurement explanations.** Predefine how to
   inspect own, donor and competitor scores, competitor identity changes,
   rank and top-1 alongside the margin. Candidate diagnostics include fixed
   linear projections and pre/post-normalization states. They need an explicit
   role and specification; a favorable post-hoc endpoint cannot replace the
   original endpoint or become confirmatory evidence.
4. **Reserve generalization and behavior for their own gates.** Newly prepared
   confirmation material, model replication, non-emoji/word controls and
   validated task outcomes are subsequent designs. A new seed, carrier or
   analysis does not make an already exposed item fresh. The 384 panel is
   exploratory, and the historical P2/C1 banks remain unavailable: do not
   reopen, reuse, tokenize or search their contents.

No new sample-size target, efficacy threshold, hypothesis family or population
interval is set here. Those belong in the later protocol, with the claim and
measurement chosen before new outcomes. The frozen 384-item study remains a
descriptive comparison, not a retroactively confirmatory test.

## Useful endings without requiring a positive result

| Pattern in later, properly designed tests | Defensible paper ending |
|---|---|
| **Propagated effect supported under the tested controls** | A local intervention changes later computation in a way that contributes to specified readouts under stated interventions. Intact-state, model and symbol scope are reported separately; no universal circuit or semantic percentage follows. |
| **Reset-only effect** | The relationship depends on the artificial readout-reset condition. The paper characterizes a conditional intervention response and its failure to transfer to the tested intact computation. |
| **Metric-only pattern at the tested readouts** | A margin pattern is localized to normalization, competition or scoring under the planned comparisons, with no supported corresponding rank/task effect. This is a measurement result, not proof that every representation change is an artifact. |
| **No supported effect, or heterogeneous/reversed effects** | The larger panel or discriminating comparison limits the eight-item observation. Report all items, uncertainty appropriate to the design, nulls and reversals. A missing row or failed numerical gate is missing evidence, not a null effect. |

These are interpretation patterns, not executable decision rules. Their
operational criteria must be specified in advance. None licenses selecting a
favorable layer, donor, operation or endpoint to force a positive narrative.

## Methodological connection and novelty boundary

Zhang and Nanda's *Towards Best Practices of Activation Patching in Language
Models: Metrics and Methods* examines how evaluation metrics and corruption
methods change patching conclusions. It motivates treating our reset,
replacement and readout choices as part of the scientific question, rather
than as neutral implementation details. This is a methodological connection,
not a claim that the present agenda has priority or established a novel
mechanism. [Primary source](https://arxiv.org/abs/2309.16042).

No model forwards, new human judgments, protected-bank inspection or new
scientific results were produced in preparing this note. The existing
published artifacts and fixed experimental sources remain unchanged.
