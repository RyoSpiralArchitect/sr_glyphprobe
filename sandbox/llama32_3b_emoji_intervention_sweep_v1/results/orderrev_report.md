# Does the order-effect reversal replicate? (out of contract)

The n = 30 run reported **8/30 pairs positive** (chance 15, naive binomial p = 0.016 — dyadic-robust 0.066, see below) — ending on the stronger component scores *lower*. It was the first sample in this series with enough units for the sign to mean anything, and it pointed opposite to an earlier 6/7 claim that has already been retracted. So it was tested on a fresh draw before anything was built on it.

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

> Every p-value in that table is a naive binomial and **every one of them is overstated** — pairs are dyads over a shared component pool, not independent trials. See the clustering section for the corrected figures; the direction survives, the significance does not.

The reversal holds on pairs that were never measured before. Two **pairs-disjoint** samples, 60 pairs pooled, same direction. That moves the claim from *one sample* to *two samples on one protocol* — which is what the pre-registration said it could and could not buy. It is still one model, one site, one position, one strength, one author's sampler.

> **How close this was.** 1 pair flipping sign would have overturned it: 10/30 gives p = 0.0987, above the 0.05 threshold. The pre-registered rule is met and the verdict stands as written — but a result this close to its own boundary should be quoted with the margin attached, not as a clean pass. The pooled count (17/60) points the same way and rests on more units, but its nominal p-value is **not** the sturdier number either. Both figures assume pairs are independent; they are dyads over a shared component pool, and the section on clustering below shows what happens to this p-value under the appropriate test.

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

## The clustering correction reaches the pre-registered test itself

Adversarial review objected that pooling treats pairs as independent Bernoulli trials when components recur across them. Three review passes later the objection has grown teeth: it applies not only to the pooled count but to **every sign test in this series, including the pre-registered primary one**.

Each pair is a **dyad** over two components. Two pairs sharing a component covary — in the pooled sample P(same sign | share a component) = **0.718** against **0.574** for component-disjoint pairs, ICC **+0.306**. The estimator for a mean of dyadic observations is the dyadic-robust variance (Aronow-Samii-Assenova), with the residual **null-imposed** (`e = y − 0.5`), which `--simulate` shows is the only candidate holding its nominal size:

| sample | count | naive binomial | design effect | dyadic-robust `p` (z) | (t) |
|---|---|---|---|---|---|
| **primary — the pre-registered test** | 9/30 | 0.0428 | 1.47 | **0.0704** | 0.0798 |
| prior (meanrule30) | 8/30 | 0.0161 | 1.93 | **0.0660** | 0.0756 |
| pooled | 17/60 | 0.0011 | 3.27 | **0.0633** | 0.0720 |

**No sample in this series clears 0.05 under the appropriate test, and all three point the same way.** The direction is consistent and reproducible; the *significance* was an artefact of treating dyads as independent.

> **What this does and does not do to the verdict.** The decision rule was fixed in advance and it specified a binomial test. That test was met, so **the pre-registered verdict REPLICATED stands as written** — swapping in a different test after seeing the result would be the same act whether it rescues a finding or kills one, and this directory does not get to do it in the convenient direction only. What must be said alongside it is that **the pre-registered test was the wrong test**: it assumed an independence the design never had. The defensible reading is `9/30, dyadic-robust p = 0.070` — the same direction as two other samples, short of conventional significance. Pre-registration protects against choosing a test to fit a result; it does not make a mis-specified test correct.

**This section has now been wrong twice, in opposite directions.** Both are on the record rather than quietly replaced:

- **v1** led with a bootstrap statistic `P(fraction ≥ 0.5) = 0.054` and concluded the pooled p-value "does not survive". Its weights were `cnt[A] * cnt[B]` where the comment claimed an indicator — a real defect. But its *number* was close to right, and it was retracted with a bad argument: v2 said a statistic with median ≈ 0.5 under the null "is not a p-value", when a valid one-sided p-value has exactly that. `--forensics` re-judges it against the clustered null it should have been compared with.
- **v2** answered with a range, `p ≈ 0.011–0.063`. Two of its three estimators are mis-specified: the Rao-Scott multiplier used `m̄ − 1`, valid when an observation sits in one cluster, whereas a dyad sits in two (the correct mean number of other dyads sharing a vertex is **5.20**, not 2.43); and the mean-centred dyadic row rejects **~10 %** of the time at a nominal 5 % *under an independent null*. Presenting a range was not even-handedness — it averaged one valid estimator with two broken ones, and the `0.01` endpoint came entirely from the broken multiplier.
- The **component-disjoint subset analysis** stays withdrawn, but v2's stated reason was also wrong. It claimed the analysis was identical to a size-matched unconstrained control; two of its three rows are pinned by the marginal count and *cannot* differ, while the third — the one carrying the original claim — differed by ~18×. The analysis was invalid because a median of correlated within-dataset p-values is not a p-value, not because it detected nothing.

## An observation, not a claim: the component gap

On this sample, Spearman(|component gap|, order effect) = **-0.664**. [FINDINGS §3](../FINDINGS.md) retracted "the order effect scales with the component gap" precisely because it read **+0.04** at n = 7 and **−0.94** at n = 6 — the same statistic on the same protocol, pointing both ways.

This is **not** a revival of that claim. It is one more sample of a quantity that has already proved it can produce any answer at small n, found *after* looking at the data, on pairs drawn for a different purpose. It goes here so it is on the record rather than discovered later — and the only honest next move is to pre-register it with a threshold and test it on pairs drawn for that question.

## What adversarial review changed

Three review passes. None moved a measured value; between them they changed what several numbers were allowed to claim, and caught one analysis that was wrong in each direction in turn.

**Pass 1 — eight findings.**

- The **overlap check was circular**: `sample_pairs` already skips the exclusion set, so `overlap == 0` held by construction and would have kept holding if the exclusion had silently become a no-op. The prior pair set is now rebuilt independently from the prior *profiles* file, cross-checked against the summary, required to match the prior pair count and to name only components that exist; the branch is instrumented directly and fired **5** time(s), of which **1** were repeats genuinely avoided — the rest were candidates the reuse cap would have dropped anyway — changing **2** of the 30 final pairs.
- The **4-prefix-token invariant** carried by the previous runner had been dropped and is restored: every component, every wrapper, or the run aborts.
- The **profiles file had lost its per-layer vector**, so no reader could re-derive a score or reanalyse under a different layer band. It now records `profile` and `layers` (the run it is pooled with carries `profile` but not `layers`).
- Stale prose: FINDINGS §3 still said this result needed the replication it had just received; the pre-registration miscounted the retractions; a Japanese README was left a version behind.

**Pass 2 — the clustering correction was itself wrong.** Pass 1 replaced an over-claim (`p = 0.0011`) with an over-correction ("the p-value does not survive"). The section above is the corrected version, and both errors are recorded there rather than quietly replaced. Pass 2 also found four surviving approving quotes of `p = 0.0011` — two of them introduced by the commit that was supposed to remove them — a mislabelled exclusion audit, and a rounding disagreement between the two languages.

The run was repeated with every guard active. **Every value is bit-identical** — all 30 order effects and all 30 observed scores match to 0.0e+00, and no summary key differs. The null distributions came from the protocol-keyed cache rather than being recomputed, so this is a determinism check on the measurement path, not on the whole pipeline from scratch.

## Limitations

- One model, one site (`resid_post`), one position (`last_nonpad`), one strength (α = 0.5), three injection targets, layers 10-19.
- Fresh **pairs**, not a fresh protocol: same pool, same measurement frame, same author. FINDINGS §7's "independent replication" — second model, panels chosen by someone else — remains open, and this run does not touch it.
- Solo component values are reused rather than re-measured; the five-component frame check bounds the risk (max |drift| 0.0000) but does not eliminate it.
- The random-direction null is a size control, not a semantic control.
- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.
