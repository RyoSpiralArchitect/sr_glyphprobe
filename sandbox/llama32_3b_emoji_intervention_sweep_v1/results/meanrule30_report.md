# The mean rule at n = 30, on components I did not choose (out of contract)

Applies two of the four next steps from [FINDINGS §7](../FINDINGS.md): more units per statistic, and a component pool taken from the repository rather than picked by the analyst. Pre-registered in [`PREREGISTRATION_mean_rule_n30.md`](../PREREGISTRATION_mean_rule_n30.md), committed before this run's script existed. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.

## Design

- **Components**: all 35 glyphs of the repository's `e2_core35_{animals,food,sky,social,transport}` panels, assembled for earlier work. Every one costs **exactly 4 prefix tokens on every wrapper**, verified at run time — token count is constant by construction across the whole pool.
- **Pairs**: 30, drawn by `random.Random(20260809)` rejecting any component used more than twice. Both orders, bare concatenation; all 60 concatenations verified to tokenise as their two components.
- **Rule under test**, frozen at the values fitted on a *different* set: `composite = 0.7 × mean(components) + 1.16`. Nothing is re-fitted.

## Primary result

| criterion | required | observed | |
|---|---|---|---|
| Spearman(predicted, observed) | ≥ 0.7 | **+0.784** | PASS |
| mean absolute error | ≤ 0.72 | **0.409** | PASS |

**Pre-registered verdict: SUPPORTED.**

| | n = 6 (earlier) | n = 30 (here) |
|---|---|---|
| Spearman | +0.886 | **+0.784** |
| MAE | 0.308 | 0.409 |
| components chosen by | me | the repository |
| bootstrap CI | not supportable | **[+0.550, +0.907]** |
| permutation p | — | **0.0001** |

The bootstrap interval is the number FINDINGS §5.1 asked for and n = 6 could not produce. It excludes zero comfortably, but its lower bound (+0.550) sits **below the 0.7 pass threshold** — the relationship is solid, the precision is not.

## Where the rule is wrong

Refitting on this sample gives `0.62 × mean + 1.86` against the frozen `0.7 / 1.16` — reported for comparison only, never substituted. The ordering transfers; the calibration does not.

Errors run -0.31 to +1.50, median **+0.33**, with 26/30 positive — the frozen rule **under-predicts** on this pool. MAE is inside the pre-registered bound but worse than the n = 6 run (0.409 vs 0.308), which is what an out-of-sample calibration check is supposed to reveal.

| pair | mean(components) | predicted | observed | error |
|---|---|---|---|---|
| 🐚🤙 | 2.98 | 3.24 | 3.56 | +0.32 |
| 🐔🤔 | 3.18 | 3.39 | 3.40 | +0.01 |
| 🌗🤘 | 3.26 | 3.44 | 4.01 | +0.56 |
| 🐖🤗 | 3.36 | 3.51 | 3.67 | +0.16 |
| 🐖🐗 | 3.37 | 3.52 | 3.92 | +0.40 |
| 🌗🚖 | 3.40 | 3.54 | 3.92 | +0.38 |
| 🌘🤕 | 3.56 | 3.66 | 3.68 | +0.03 |
| 🐗🚙 | 3.65 | 3.71 | 4.37 | +0.66 |
| 🍖🤙 | 3.73 | 3.77 | 4.10 | +0.33 |
| 🌔🌘 | 3.83 | 3.84 | 3.96 | +0.12 |
| 🌕🌙 | 3.83 | 3.84 | 4.12 | +0.28 |
| 🍖🤗 | 3.89 | 3.88 | 4.73 | +0.85 |
| 🐔🐕 | 3.98 | 3.95 | 4.43 | +0.48 |
| 🌙🚚 | 3.99 | 3.95 | 4.28 | +0.32 |
| 🌕🚚 | 4.00 | 3.96 | 4.49 | +0.53 |
| 🐕🐘 | 4.03 | 3.98 | 4.54 | +0.55 |
| 🤔🚕 | 4.07 | 4.01 | 4.37 | +0.36 |
| 🤖🚕 | 4.12 | 4.05 | 3.94 | -0.11 |
| 🍙🌚 | 4.30 | 4.17 | 4.38 | +0.21 |
| 🚔🚖 | 4.31 | 4.18 | 5.33 | +1.16 |
| 🤕🚔 | 4.33 | 4.19 | 4.09 | -0.10 |
| 🤘🚗 | 4.37 | 4.22 | 5.72 | +1.50 |
| 🐘🍚 | 4.46 | 4.28 | 4.60 | +0.31 |
| 🍙🌔 | 4.54 | 4.34 | 4.69 | +0.35 |
| 🐙🍕 | 4.60 | 4.38 | 4.82 | +0.44 |
| 🍕🚙 | 4.70 | 4.45 | 4.57 | +0.12 |
| 🐙🚗 | 4.77 | 4.50 | 5.22 | +0.72 |
| 🤖🚘 | 4.78 | 4.51 | 4.27 | -0.23 |
| 🍗🌖 | 4.79 | 4.51 | 4.85 | +0.33 |
| 🍚🚘 | 5.96 | 5.33 | 5.02 | -0.31 |

## The order effect, finally with enough units

**8/30 pairs positive** (chance 15), median **-0.32**, binomial two-sided **p = 0.0161**.

This is the first sample in the series large enough for the sign to mean anything, and it points the **opposite way to my original claim**. The history:

| sample | n | positive | reading |
|---|---|---|---|
| catchase v2 | 7 | 6/7 | "ending on the stronger component scores higher" |
| meanrule v1 | 6 | 2/6 | the reverse |
| **this run** | **30** | **8/30** | **ending on the stronger component scores LOWER** (p = 0.016) |

The retraction in [FINDINGS §3](../FINDINGS.md) was right that the 6/7 claim did not hold. It was *too* agnostic in one respect: with 30 units the effect is not absent, it runs the other way. Treat this as a new, single-sample finding at the same evidential level the 6/7 claim once had — it needs its own replication before it is more than that.

## The same-family hunch is not supported

[Composition report §5](composition_report.md) noted that 🐈🐱 (one concept, two names) sat +0.54 above the line and 🍕🚗 (two strong unrelated concepts) −0.83 below, and flagged "alike composes additively" as an untested hypothesis. Here:

| pairs | n | median residual |
|---|---|---|
| same family | 6 | +0.44 |
| cross family | 24 | +0.33 |

Essentially no difference. The hunch is **not supported** — though 6 vs 24 is an unbalanced comparison and the same-family pairs come from only five panels, so this is weak evidence against rather than a refutation.

## Limitations

- Still one model, one site (`resid_post`), one position (`last_nonpad`), one strength (α = 0.5), three injection targets, layers 10-19.
- The component *pool* is the repository's, but the sampler, protocol and analysis are mine, and this run shares its measurement frame with the fitting set. §7's "independent replication" is still open.
- The calibration failure means the rule should be quoted as an ordering, not as a predictor of magnitude.
- The random-direction null is a size control, not a semantic control.
- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.
