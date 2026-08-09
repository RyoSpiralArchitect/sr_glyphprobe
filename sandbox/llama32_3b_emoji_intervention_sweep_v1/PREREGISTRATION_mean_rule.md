# Pre-registration — the composition "mean rule"

**Written and committed before the confirmatory run existed.** The git history is
the evidence: this file's commit precedes `scripts/mean_rule_test.py` and
`results/meanrule_v1_*`. Out of contract, sandbox only, no holdout bank.

## Why this document exists

The rule below was found by **post-hoc re-analysis**. `cat_chase2.py` was built to
test a *different* hypothesis (that the composition order effect grows with the
component gap). That hypothesis failed — Spearman(gap, order effect) = **+0.036**
over 7 families. Looking again at the same data for something that *did* explain
the composite values produced the mean rule.

A relationship found that way is a hypothesis, not a result, and I had already
made the equivalent mistake once in this project: I read "order effect grows with
the gap" off **two** families and stated it, and it dissolved at n = 7. So this
one gets written down and tested on families that did not shape it.

## The rule being tested

Fitted on the 7 families of `catchase_v2` (twin, astro, pizcar, catsq, tech,
pizsq, carlap), where every glyph is a bare two-component concatenation and
`mid` is the mid-network ratio (max over L10-19) at alpha = 0.5:

```
composite_mid_mean  =  0.70 * mean(component_mid)  +  1.16
```

Supporting statistics on the fitting set (all post-hoc, all n = 7):

| statistic | value |
|---|---|
| Spearman(mean of components, mean of the two composites) | +0.821 |
| leave-one-out Spearman range | +0.714 … +0.886 |
| Pearson r | +0.853 |
| residual sd | 0.36 |
| permutation test, 10 000 shuffles, one-sided | p = 0.017 |

For contrast, on the same 7 families the *order* effect was Spearman +0.036 with
the gap, i.e. the thing this run is **not** about.

## Confirmatory set — six families that did not shape the rule

None of these pairs appears in the fitting set. Component solo values come from
`why_flat` / `catchase` runs on the **identical** protocol (same null seeds
`800_000 + 100*L + s`, same three targets, same alpha, same four wrappers, all 28
layers); `catchase_v2` re-measured several of them and reproduced them exactly
(🐈 3.96, 🍕 5.32, 🚗 5.66), so the frame is shared.

Both orders of each pair are run; the prediction is for the **mean of the two
orders**, because the rule is about composition, not order.

| family | A | mid(A) | B | mid(B) | mean | **predicted composite mean** |
|---|---|---|---|---|---|---|
| dogtea | 🐶 dog | 3.71 | 🍵 tea | 4.59 | 4.15 | **4.07** |
| sailthink | ⛵ sailboat | 2.75 | 🤔 thinking | 2.76 | 2.75 | **3.09** |
| cryheli | 😢 crying | 4.22 | 🚁 helicopter | 3.55 | 3.88 | **3.88** |
| shipcof | 🚢 ship | 3.72 | ☕ coffee | 2.87 | 3.29 | **3.47** |
| teacar | 🍵 tea | 4.59 | 🚗 car | 5.66 | 5.12 | **4.75** |
| anchorair | ⚓ anchor | 2.99 | ✈️ airplane | 3.05 | 3.02 | **3.27** |

Component means span 2.75 … 5.12, so the rule is being asked to extrapolate
across most of its fitted range rather than interpolate at one point.

## Decision rule, fixed in advance

Let `pred` be the six predicted values above and `obs` the six observed composite
means. The rule is **supported** only if **both** hold:

1. `Spearman(pred, obs) >= 0.70`
2. `mean(|obs - pred|) <= 0.72` (two residual sd of the fit)

Anything else counts as **not supported**, and will be reported as such. In
particular:

- Spearman >= 0.70 but MAE > 0.72 -> the *ordering* survives, the *calibration*
  does not; report as "ordinal only".
- Spearman < 0.70 -> the rule failed, full stop. It will be reported as a failed
  post-hoc hypothesis, not quietly dropped.

## Secondary checks (not part of the decision rule)

Recorded but explicitly **not** allowed to rescue a failed primary test:

- do the re-measured solo components reproduce their prior values (frame check)?
- does the order effect stay near zero on these six families too?
- do the fixed-frame cosine shifts stay far below the efficacy shifts, as they
  did on all 14 previous cases (max 0.074 vs 0.94)?
- residual pattern: the fitting set showed same-concept pairs above the line
  (🐈🐱 +0.54) and strong-and-different pairs below it (🍕🚗 −0.83); does that
  show up again?

## What this cannot establish

Six families, components chosen by me, one model, one position, one site, one
strength, and the confirmatory set shares its protocol and its author with the
fitting set. A pass makes the rule worth taking seriously inside this sandbox.
It does not make it a property of language models, and no causal or semantic
claim is authorized either way (`pre-causal-activation-screen`,
`causal_claim_authorized: false`).
