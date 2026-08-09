# Does the order-effect reversal replicate? (out of contract)

The n = 30 run reported **8/30 pairs positive** (chance 15, binomial p = 0.016) — ending on the stronger component scores *lower*. It was the first sample in this series with enough units for the sign to mean anything, and it pointed opposite to an earlier 6/7 claim that has already been retracted. So it was tested on a fresh draw before anything was built on it.

Pre-registered in [`PREREGISTRATION_order_reversal.md`](../PREREGISTRATION_order_reversal.md), committed before this run's script existed. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.

## Design

- **30 new pairs**, drawn by `random.Random(20260810)` from the same 35-glyph repository pool, excluding every pair measured in `meanrule30_v1`. Overlap with the prior sample: **0** — the run aborts otherwise. Disjoint pairs, one population, one protocol.
- **Solo component values reused** from the prior run (deterministic under an identical protocol with a cached null). Five were re-measured as a frame check: max |drift| = **0.0000** against a tolerance of 0.01 — inside the bound, so the reuse is legitimate.
- **Sign convention** identical to both earlier samples: `order_effect = mid(weak-then-strong) − mid(strong-then-weak)`, strong/weak fixed once from the reused solo values. The counts are directly comparable.

> **Amendment on the record.** The pre-registration named the five frame-check components with identifiers that do not exist (`animals_1` for `animals_animals_slot_03`, and so on) — written from memory instead of read from the panel files. The first run died on `KeyError` while assembling the panel, **before any forward pass and before any file was written**, so the fix was decided on zero data. [Amendment 1](../PREREGISTRATION_order_reversal.md) records the mechanical resolution (`<family>_<k>` = the k-th of that family, sorted), and the runner now aborts if its own list, its resolution, or the reused values disagree with that committed table.

## Primary result

**9/30 pairs positive** (chance 15), median **-0.26**, binomial two-sided **p = 0.0428**.

| | required for REPLICATED | observed | |
|---|---|---|---|
| positive count | < 15 | **9** | PASS |
| binomial two-sided p | < 0.05 | **0.0428** | PASS |

**Pre-registered verdict: REPLICATED.**

| sample | n | positive | median | reading |
|---|---|---|---|---|
| catchase v2 | 7 | 6/7 | — | ends on stronger scores **higher** |
| meanrule v1 | 6 | 2/6 | — | the reverse |
| meanrule30 | 30 | 8/30 | -0.32 | ends on stronger scores **lower** (p = 0.016) |
| **this run** | **30** | **9/30** | **-0.26** | **REPLICATED** |
| pooled | 60 | 17/60 | — | binomial p = 0.001066 — **but see the clustering section: this p-value assumes an independence the design does not have** |

The reversal holds on pairs that were never measured before. Two **pairs-disjoint** samples, 60 pairs pooled, same direction. That moves the claim from *one sample* to *two samples on one protocol* — which is what the pre-registration said it could and could not buy. It is still one model, one site, one position, one strength, one author's sampler.

> **How close this was.** 1 pair flipping sign would have overturned it: 10/30 gives p = 0.0987, above the 0.05 threshold. The pre-registered rule is met and the verdict stands as written — but a result this close to its own boundary should be quoted with the margin attached, not as a clean pass. The pooled count (17/60) points the same way and rests on more units, but its nominal p-value is **not** the sturdier number either — see the clustering section below.

## Per-pair order effects

| pair | strong component | order effect |
|---|---|---|
| 🌖🚗 | transport_transport_slot_06 | -1.22 |
| 🐕🚘 | transport_transport_slot_07 | -1.18 |
| 🚕🚙 | transport_transport_slot_04 | -1.06 |
| 🍕🤙 | food_food_slot_04 | -0.98 |
| 🍘🤔 | food_food_slot_07 | -0.93 |
| 🐗🚘 | transport_transport_slot_07 | -0.91 |
| 🍘🤘 | food_food_slot_07 | -0.81 |
| 🍗🌗 | food_food_slot_06 | -0.81 |
| 🌗🚗 | transport_transport_slot_06 | -0.75 |
| 🍗🤙 | food_food_slot_06 | -0.74 |
| 🍔🌙 | food_food_slot_03 | -0.59 |
| 🚔🚕 | transport_transport_slot_04 | -0.59 |
| 🍕🌘 | food_food_slot_04 | -0.49 |
| 🌙🤗 | sky_sky_slot_08 | -0.32 |
| 🐙🤘 | animals_animals_slot_08 | -0.29 |
| 🐔🤚 | animals_animals_slot_03 | -0.24 |
| 🌕🤖 | sky_sky_slot_04 | -0.21 |
| 🤚🚚 | transport_transport_slot_09 | -0.12 |
| 🌘🤖 | sky_sky_slot_07 | -0.12 |
| 🍚🚚 | food_food_slot_09 | -0.10 |
| 🐖🐚 | animals_animals_slot_05 | -0.07 |
| 🍔🍖 | food_food_slot_03 | +0.05 |
| 🐘🚖 | animals_animals_slot_07 | +0.06 |
| 🐖🤕 | animals_animals_slot_05 | +0.10 |
| 🍚🌚 | food_food_slot_09 | +0.19 |
| 🐚🤕 | social_social_slot_04 | +0.19 |
| 🐗🌚 | sky_sky_slot_09 | +0.22 |
| 🐕🤔 | animals_animals_slot_04 | +0.47 |
| 🍖🚔 | transport_transport_slot_03 | +0.62 |
| 🌕🚙 | transport_transport_slot_08 | +0.82 |

## Secondary: does the refit generalise? (comparison only)

The n = 30 run found the frozen rule's calibration failing out of sample and refit `0.62 × mean + 1.86` against frozen `0.70 × mean + 1.16`. Whether the refit is better or merely fitted to that sample is decidable on these fresh pairs.

| rule | fitted on | MAE here |
|---|---|---|
| frozen `0.70 × mean + 1.16` | the 7 catchase families | **0.410** |
| refit `0.62 × mean + 1.86` | the meanrule30 pairs | **0.309** |

The **refit** rule wins by 0.101. The refit generalises to pairs it was not fitted on, which is evidence the n = 30 calibration was picking up something real rather than sample noise. Pre-registered as a comparison, and it neither rescues nor damages the primary verdict above.

## Where the frozen rule sits on these pairs

Errors run -0.46 to +1.10, median **+0.31**, 25/30 positive — the same under-prediction the n = 30 run reported.

## The pooled p-value is inflated by shared components

Adversarial review objected — correctly — that pooling treats 60 pairs as 60 independent Bernoulli trials when all 35 components appear in more than one pair (up to 4), both samples draw from one 35-glyph pool, and strong/weak in both is assigned from a single measurement of `solo_mid`. The pairs are disjoint; the **units are not independent**. Two sensitivity analyses ([`scripts/pooled_independence.py`](../scripts/pooled_independence.py)):

| analysis | positive fraction | verdict on the direction |
|---|---|---|
| maximal **component-disjoint** subsets (median n = 15, 2000 draws) | median **0.267**, 90 % [0.188, 0.400] | only **0.25 %** of subsets go the other way |
| **component-level bootstrap** (20000 resamples) | **0.284**, 95 % CI [0.077, 0.543] | P(fraction ≥ 0.5) = **0.054** |

The two schemes disagree about strength, and that disagreement is the point. Under component-disjoint subsets — where every pair is a genuinely independent unit — the direction is robust: the positive fraction never approaches a majority. But those subsets hold only ~15 pairs, so the median sign test reads p = 0.118 and just 21 % reach p < 0.05. The bootstrap's interval touches 0.5 outright.

> **So: the direction survives clustering; the p-value does not.** Quote the pooled count as 17/60 with this caveat attached — **not** as p = 0.0011, which assumes an independence the design does not have. The bootstrap scheme matters too: mine requires *both* of a pair's components to be drawn, which is deliberately harsh. A gentler scheme gives a tighter interval — reported here in its conservative form on purpose.

## An observation, not a claim: the component gap

On this sample, Spearman(|component gap|, order effect) = **-0.664**. [FINDINGS §3](../FINDINGS.md) retracted "the order effect scales with the component gap" precisely because it read **+0.04** at n = 7 and **−0.94** at n = 6 — the same statistic on the same protocol, pointing both ways.

This is **not** a revival of that claim. It is one more sample of a quantity that has already proved it can produce any answer at small n, found *after* looking at the data, on pairs drawn for a different purpose. It goes here so it is on the record rather than discovered later — and the only honest next move is to pre-register it with a threshold and test it on pairs drawn for that question.

## What adversarial review changed

Review found eight defects. None moved a number; the two that mattered most were about what the numbers were allowed to claim.

- The **overlap check was circular**: `sample_pairs` already skips the exclusion set, so `overlap == 0` held by construction and would have kept holding if the exclusion had silently become a no-op. The prior pair set is now rebuilt independently from the prior *profiles* file, cross-checked against the summary, required to match the prior pair count and to name only components that exist. The run now reports what the exclusion bought: **1 draw rejected** that would otherwise have repeated a measured pair.
- The **pooled p-value assumed independence the design does not have** — the section above is the result.
- The **4-prefix-token invariant** carried by the previous runner had been dropped and is restored: all 35 components, every wrapper, or the run aborts.
- The **profiles file had lost its per-layer vector**, so no reader could re-derive a score or reanalyse under a different layer band. It now records `profile` and `layers`, as the run it is pooled with does.
- Two stale sentences (FINDINGS §3 still said this result needed a replication; the pre-registration miscounted the retractions) and a Japanese README left at twelve runs. [Amendment 2](../PREREGISTRATION_order_reversal.md) records the corrections, including the traceback that Amendment 1 cited from a gitignored log.

The run was then repeated end to end with the strengthened guards. **Every value is bit-identical** — all 30 order effects and all 30 observed scores match to 0.0e+00, and no key in the summary differs. Taken with the frame check's 0.0000 drift, the measurement is exactly reproducible on this machine.

## Limitations

- One model, one site (`resid_post`), one position (`last_nonpad`), one strength (α = 0.5), three injection targets, layers 10-19.
- Fresh **pairs**, not a fresh protocol: same pool, same measurement frame, same author. FINDINGS §7's "independent replication" — second model, panels chosen by someone else — remains open, and this run does not touch it.
- Solo component values are reused rather than re-measured; the five-component frame check bounds the risk (max |drift| 0.0000) but does not eliminate it.
- The random-direction null is a size control, not a semantic control.
- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.
