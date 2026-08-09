# Pre-registration — the mean rule at n = 30, on components I did not choose

**Written and committed before the confirmatory run existed.** The git history is
the evidence: this file's commit precedes `scripts/mean_rule_n30.py` and any
`results/meanrule30_*`. Out of contract, sandbox only, no holdout bank.

## Why this run

[`FINDINGS.md`](FINDINGS.md) §5.1 records the dominant limitation of everything
before it: **n ≈ 6 Spearman is not a measurement.** The same statistic on the
same protocol read +0.04 on one sample and −0.94 on another. The mean rule
passed a pre-registered test — but at n = 6, with the same fragility, and
§2.4 says so.

§7 lists the two fixes this run applies together:

- **more units per statistic** — 30 pairs instead of 6, enough for a rank
  correlation to mean something and for a permutation test to have resolution;
- **components not chosen by the analyst** — the pool is the repository's own
  `data/emoji_panels/e2_core35_*.yaml`, assembled for earlier work, and the 30
  pairs are drawn from it by a seeded sampler, not by me.

It does **not** fix the other two §7 items: this is still one model, one site,
one position, one strength, and I still wrote the sampler. It is a stronger test
of the same rule, not an independent replication.

## The rule under test — unchanged, and fitted elsewhere

Fitted post-hoc on the 7 `catchase_v2` families, confirmed at n = 6 in
[`PREREGISTRATION_mean_rule.md`](PREREGISTRATION_mean_rule.md):

```
composite_mid_mean  =  0.70 * mean(component_mid)  +  1.16
```

Both coefficients are frozen at those values. This is an **out-of-sample** test:
no component of this run's pool appears in the fitting set, and nothing is
re-fitted.

## Panel, fixed in advance

- **Components:** all 35 glyphs of `e2_core35_{animals,food,sky,social,transport}`.
  Every one costs exactly **4 prefix tokens**, verified against the tokenizer, so
  token count is constant by construction across the whole pool.
- **Pairs:** 30, drawn by `random.Random(20260809)` from the 595 unordered pairs,
  rejecting any draw that would use a component more than twice. Result: 32
  distinct components, max reuse 2, 24 of 30 cross-family.
- **Orders:** both, bare concatenation. The ZWJ joiner is settled
  ([composition report](results/composition_report.md) §1), so dropping it
  doubles the usable evidence per pair.
- **Composition check:** all 60 concatenations tokenise exactly as their two
  components concatenated, verified before this file was written; the runner
  re-verifies and exits 2 otherwise.
- **Protocol:** identical to every previous run — layers 10-19 (`mid` is the max
  over exactly that band), α = 0.5, 24 random directions per (layer, target),
  the same three injection targets and four extraction wrappers, same null
  seeds.

## Decision rule, fixed in advance

Let `pred_k = 0.70 * mean(component_mid) + 1.16` and `obs_k` the mean of the two
orders, over the 30 pairs. The rule is **supported** only if **both** hold:

1. `Spearman(pred, obs) >= 0.70`
2. `mean(|obs - pred|) <= 0.72`

Identical thresholds to the n = 6 test, so the two are directly comparable.

Outcomes and how each will be reported:

| result | verdict | reported as |
|---|---|---|
| both hold | **SUPPORTED** | the rule survives a 5× larger sample on components I did not pick |
| Spearman holds, MAE fails | **ORDINAL ONLY** | the ordering generalises, the calibration (slope 0.70, intercept 1.16) does not |
| Spearman fails | **NOT SUPPORTED** | the n = 6 pass was sample-size luck, reported as such and §2.4 of FINDINGS retracted |

**A miss will be reported, not quietly dropped.** Seven claims have already been
retracted in this directory; an eighth is not a problem.

## Additional statistics, specified now so they cannot be chosen later

Reported whichever way the decision goes; **none of them may rescue a failed
primary test**:

- permutation test on the Spearman, 10 000 shuffles, one-sided;
- bootstrap 95 % CI on the Spearman, 10 000 resamples — the quantity n = 6 could
  not support, and the direct answer to §5.1;
- least-squares refit of slope and intercept **reported for comparison only**,
  never substituted for the frozen rule;
- residual vs component-mean, to test the untested hunch in
  [composition report](results/composition_report.md) §5 that same-concept pairs
  sit above the line and strong-and-different pairs below it;
- the order effect per pair, and the fraction of pairs whose sign matches
  "ends on the stronger component" — at n = 30 this finally has enough units to
  say something, after reading 6/7 and 2/6 on two earlier samples.

## What this cannot establish

One model, one site, one position, one strength, three injection targets. The
components come from the repository rather than from me, but the sampler, the
protocol and the analysis are still mine, and the confirmatory set shares its
measurement frame with the fitting set. A pass makes the rule worth taking
seriously inside this sandbox and worth testing on a second model. It does not
make it a property of language models, and no causal or semantic claim is
authorised either way (`pre-causal-activation-screen`,
`causal_claim_authorized: false`).
