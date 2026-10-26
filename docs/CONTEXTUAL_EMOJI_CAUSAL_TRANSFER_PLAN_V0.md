# When does emoji information change a model's response?

[日本語](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.ja.md)

Status: **design option only; not preregistered, not frozen, not executed**.
Prepared 2026-10-07. This document proposes an independent successor study. It
does not authorize a model run, change a historical verdict, or supply a
confirmation dataset. No new model results are reported.

## One proposed contribution

Test whether emoji information changes an ordinary model response distribution
in a context-dependent way, and whether a specified attention route from emoji
positions causally contributes to that change. Use natural-language response
candidates independent of CLDR labels, a natural-state starting point, and the
model's ordinary output head. The target is a bounded route contribution, not a
complete circuit, human-like understanding, or knowledge independent of
training-data co-occurrence.

[T21](T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md) established a conditional contribution
to keyword cosine margin after a codepoint-view readout reset. Its absolute
glyph-message decrement and restoration had zero mean top-1 effects. The
proposed advance is output-linked intervention without that reset, not another
version of keyword retrieval.

Context-dependent emoji disambiguation itself is not a new contribution:
[EMODIS](https://arxiv.org/abs/2511.07193) already describes a benchmark with
ambiguous emoji-containing sentences, contrasting disambiguating contexts, and
contextual questions. Its arXiv abstract and AAAI2026 acceptance note were
verified for this plan; its full methods and data have not been audited here.
The potential distinction is the proposed mechanistic, output-linked test, not
priority for contextual emoji evaluation. This is not a completed novelty review.

## Crossed stimuli and an independent validity gate

Each scenario block `i` contains two contexts `c0, c1`, two emoji `e0, e1`, and a
finite, balanced set of paired natural-language continuations `Aij, Bij`, where
`j = 1,...,J`. The same continuation strings are scored in all four crossed
inputs. A same-context emoji replacement alone cannot establish context
dependence. Both the context and the emoji contrast must be retained.

Write contexts and continuations without deriving them from CLDR labels or
model-generated outcome preferences. Balance candidate counts and plausible
wording; use a small fixed paraphrase set rather than selecting the most
favorable wording later. Report per-pair results as well as the fixed aggregate.
Counterbalance response wording and experimental presentation where applicable.
Keep emoji-omitted inputs as a diagnostic of how much the text alone determines
the answer. Neither a favorable context-only score nor a weak model score is a
post-hoc reason to remove a confirmation block.

Before a semantic claim, obtain independent human judgments for all four inputs
and the context-only controls. A proposed minimum is three raters who did not
author the scenario and cannot see model outputs, conditions' intended labels,
or intervention results. They assess naturalness and which continuation is
supported, with `ambiguous`, `both`, and `neither` available. Freeze an agreement
rule before annotation; retain disagreement, uncertainty, and the full
planned/annotated/eligible denominator. Publish both the eligible subset and
coverage. Do not force uncertain cases into binary gold labels.

Human judgments must support the intended crossed contrast, not merely one
context's preferred answer. Fix each block's orientation `eta_i` in `{−1,+1}`
from that independent contrast before any model screening. Without this gate,
the labels are **development labels only**, and the endpoint describes response
preferences relative to author-specified candidates, not validated human
interpretation. Human agreement does not prove a shared internal meaning.

## Exact proposed output contrasts

For input `x_i(c,e)` and a candidate continuation `y` with `T_y` tokens, define
the ordinary teacher-forced sequence log probability in natural-log units:

```text
ell_i(y | c,e) = sum[t=1..T_y] log P(y_t | x_i(c,e), y_<t)
s_i(c,e)      = mean[j=1..J] {ell_i(Aij | c,e) − ell_i(Bij | c,e)}
Delta_i(c)    = s_i(c,e1) − s_i(c,e0)
H_i           = eta_i * {Delta_i(c1) − Delta_i(c0)}
```

The primary scoring rule sums **all candidate-token log probabilities**; it is
not post-hoc length-normalized, reduced to a convenient first token, or replaced
by a favorable candidate subset. Freeze prompt boundaries, tokenizer handling,
chat/base formatting, candidate punctuation, EOS inclusion, and `J` before
confirmation. Candidate length and token-count diagnostics remain visible.
The same alternatives across cells help distinguish the interaction from
additive candidate or context preferences; they do not remove every lexical
confound. Report all four `s` cells and both `Delta` values: an interaction alone
does not identify which emoji drives it.

The behavioral estimand is the mean of `H_i` under the frozen population and
family-weighting rule. Accuracy, choice flips, individual token contributions,
and unnormalized candidate probabilities are secondary diagnostics. A positive
interaction is a non-additive response effect, not by itself evidence of a
particular representation or circuit.

## Natural-state route exchange

Start both inputs from their ordinary, unmodified forward pass. Within each
context, use the other emoji variant as the donor. Match emoji-span token count
and token positions within each model; exclude incompatible pairs by a frozen,
outcome-blind tokenizer rule and report their denominator. The primary exchange
replaces post-RoPE keys and values at the emoji source positions, using a fixed
layer window and head set. Do not reset a residual stream or patch a CLDR view.

A proposed route `G` includes those source positions to all causally subsequent
query positions in that window, including the prefix and the teacher-forced
positions that predict continuation tokens. Freeze the exact query scope and
cache implementation before confirmation; do not silently switch between a
last-prefix-token route and an all-answer-token route. Donor source states come
from the same-context opposite-emoji input, without access to a desired answer
at the source positions. No desired-answer residual state is injected.

Write `s_i^(a<-b,G)(c)` for the ordinary output score when receiver emoji `ea`
uses donor emoji `eb` on route `G`. The two directions remain separate:

```text
p_i^+(c,G) = s_i^(0<-1,G)(c) − s_i(c,e0)
p_i^−(c,G) = s_i(c,e1) − s_i^(1<-0,G)(c)
K_i^d(G)   = eta_i * {p_i^d(c1,G) − p_i^d(c0,G)}, d in {+,−}
Kadj_i^d   = K_i^d(G) − K_i^d(C)
```

Here `C` is a separately fixed non-emoji-position control route using the same
exchange direction and receiver conditions. Positive `K` means the exchange
carries the human-oriented context interaction in the predicted direction;
`Kadj` asks whether that contribution exceeds this particular positional
control. It is not a fraction mediated. Do not divide by a small or
sign-changing clean/corrupt gap to manufacture a recovery percentage.

The proposed within-model success family is positive practical behavioral
effect `mean(H)`, positive practical route effects in **both** directions
`mean(K^+(G)), mean(K^−(G))`, and positive adjusted contrasts in both directions.
Require unadjusted effects too: a positive difference between two negative
effects is not successful transfer. Freeze practical effect thresholds and the
simultaneous inference rule before confirmation. These correlated contrasts
are one conjunctive test, not five replications. The present document does not
set thresholds or declare any criterion passed.

## Controls and competing explanations

- Engineering: disabled hooks, same-state donor exchanges, restore/replay, and
  exact batch geometry. Establish tolerances before outcome inspection. A
  numerical pass is not scientific evidence.
- Position controls: same-count non-emoji spans, with attention mass, source
  distance, and message norms recorded. Select control rules using pilot data,
  not confirmation effects. A pre-emoji span identical across donors is a
  no-op control, not a strong competing information route. Post-emoji spans may
  already contain emoji information; their effects are informative alternatives,
  not automatically artifacts. Matching count alone is insufficient, and
  residual mismatch must be reported.
- Generic-carrier controls: parallel crossed tasks using ordinary words and
  non-emoji symbols, matched as far as possible on communicative function,
  behavioral headroom, span count, and position. Apply the same route method.
  Strong emoji effects with similar word/symbol effects support a shared
  mechanism that handles emoji, not an emoji-specific mechanism. Any claimed
  emoji excess needs an explicit between-carrier interaction and uncertainty,
  not separate significance/non-significance judgments.
- Calibration: broad-route/full-state natural-donor exchanges and intact-input
  contrasts establish whether the selected endpoint/site is informative. Such
  exchanges are references, not proven upper bounds. Report generic fluency or
  unrelated-answer degradation rather than mistaking broad damage for semantic
  transfer.
- Mechanism: a fixed emoji identity in K/V plus context-sensitive receiver Q can
  generate contextual effects. K/V exchange therefore does not establish that
  emoji positions store context-specific semantics. Separate K and V exchanges
  are secondary unless independently frozen as a new primary question.

Natural donor states and an unmodified starting pass do not guarantee that the
patched hybrid state is on-distribution. The intervention tests a specified
counterfactual computation; it does not identify a unique mediator or all
indirect routes. Metric and corruption choices require particular care:
[Zhang and Nanda](https://arxiv.org/abs/2309.16042) report that these choices can
change patching conclusions, and
[Heimersheim and Nanda](https://arxiv.org/abs/2404.15255) discuss interpretation
and metric pitfalls. Only their abstracts were checked for this design note;
implementation requires reviewing the relevant full methods.

## Small pilot, then independently frozen confirmation

1. Use 24–32 scenario blocks across several development families. This is a
   debugging and design pilot, not confirmation. Begin with one already-present
   3B checkpoint; pin the exact artifact, tokenizer, runtime, and prompt mode
   before execution. Do not download or run a model under this document alone.
2. Limit site exploration, for example to at most three declared layer windows,
   and choose at most one primary window by a recorded pilot-only rule. Keep
   both transfer directions and all planned control cells, including failures.
   Test annotation feasibility, natural baseline headroom, position matching,
   route calibration, and variance across families. If these gates fail, revise
   development materials rather than consuming confirmation data.
3. Freeze the first model's confirmation design independently of its new
   targets. Derive the confirmation size from pilot family-level variance,
   desired precision/power, practical effect thresholds, and a fixed budget.
   At least 20 new context/template families is a proposed starting constraint,
   **not a locked sample size or power guarantee**. More paraphrases within a
   few families are not a substitute for new families.
4. Specify a second-family 7B replication separately. Pin its exact checkpoint
   and tokenizer, repeat necessary engineering/pilot checks on development
   material, then independently freeze its intervention rule before any
   confirmation forward. Do not assume a normalized layer number identifies
   an equivalent mechanism. A second-family replication tests the phenomenon,
   not identical circuitry. Do not pool models to rescue a failed replication.

Use family-aware inference and freeze how family and emoji reuse are handled.
If emoji IDs repeat across families, model/resample that dependence or restrict
the claim to the finite tested emoji inventory. Report family-level effects,
all planned/completed/failed cells, and uncertainty. The exact estimator,
resampling method, multiplicity family, and missing-data rule remain open
decisions to resolve before registration.

No confirmation stimulus may be kept, dropped, reworded, or assigned to a
favorable layer on the basis of model output. Human and tokenizer eligibility
rules must be frozen in advance. An independent custodian should prepare and
seal the new confirmation bank; exposure for debugging retires that bank from
an untouched-confirmation claim. No adaptive stopping on significance is
proposed. If the required sample size exceeds budget, narrow the claim or keep
the study exploratory.

## Freshness, exploratory extensions, and outcome branches

The prior matched pool contained 954 eligible emoji and is exhausted by the
reported T19/T20/T21 allocations. New contexts are not new emoji, new
pretraining exposure, or a fresh glyph holdout. A successor must distinguish
new context families from reused emoji and explicitly reserve any newly
constructed population. Historical protected target banks remain untouched;
they are not sources for stimuli, debugging, or design tuning.

Same-token, cross-context state transport is an optional **exploratory
secondary**: move the same emoji's state between contexts into a common
receiver. It requires generic word/symbol carrier controls, position alignment,
and controls for copying surrounding context. Success would not by itself
show that the emoji stores meaning rather than generic context information.
Do not promote this extension after seeing the main outcome.

| Outcome | Allowed conclusion / next step |
| --- | --- |
| Human validity gate fails or is absent | Development-label analysis only; improve independent annotation before a semantic claim. |
| No practical natural crossed interaction | No supported contextual emoji effect on this endpoint/population; inspect the stimulus hypothesis without screening confirmation for winners. |
| Natural interaction but uninformative calibration | Site/endpoint uncalibratable; not evidence that no relevant representation exists. |
| Natural interaction, informative calibration, no directional route effect | The specified route account is unsupported; alternative or redundant routes remain possible. |
| Directional shifts accompanied by broad damage or no advantage over position controls | Specific route interpretation is unresolved; do not relabel generic disruption as meaning transfer. |
| Route contribution with comparable generic-carrier effects | Evidence for a shared contextual information route that also processes emoji, not an emoji-unique mechanism. |
| Success in one model or exposed templates only | Bound the result to that model/population; no cross-family or held-out-family success claim. |
| Both independent model confirmations meet frozen gates | Support the specified context-dependent, output-linked route contribution across two tested configurations; retain all representation and co-occurrence caveats. |

Before any run, the unresolved decisions are the author/annotator workflow,
exact model artifacts, stimulus and family inventory, practical effect floors,
route/control masks, donor rules, sample-size calculation, and inference plan.
Only a later explicit protocol and execution decision can freeze these choices.
