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
| pooled | 60 | 17/60 | — | binomial p = 0.001066 |

The reversal holds on pairs that were never measured before. Two independent samples, 60 pairs pooled, same direction. That moves the claim from *one sample* to *two samples on one protocol* — which is what the pre-registration said it could and could not buy. It is still one model, one site, one position, one strength, one author's sampler.

> **How close this was.** 1 pair flipping sign would have overturned it: 10/30 gives p = 0.0987, above the 0.05 threshold. The pre-registered rule is met and the verdict stands as written — but a result this close to its own boundary should be quoted with the margin attached, not as a clean pass. The pooled count (17/60, p = 0.0011) is the sturdier number, and it was pre-registered as a description rather than as the test.

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

## Limitations

- One model, one site (`resid_post`), one position (`last_nonpad`), one strength (α = 0.5), three injection targets, layers 10-19.
- Fresh **pairs**, not a fresh protocol: same pool, same measurement frame, same author. FINDINGS §7's "independent replication" — second model, panels chosen by someone else — remains open, and this run does not touch it.
- Solo component values are reused rather than re-measured; the five-component frame check bounds the risk (max |drift| 0.0000) but does not eliminate it.
- The random-direction null is a size control, not a semantic control.
- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.
