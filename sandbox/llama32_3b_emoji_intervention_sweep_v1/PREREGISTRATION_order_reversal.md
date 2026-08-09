# Pre-registration — replicating my own newest claim before building on it

**Written and committed before the confirmatory run existed.** The git history is
the evidence: this file's commit precedes `scripts/order_reversal.py` and any
`results/orderrev_*`. Out of contract, sandbox only, no holdout bank.

## Why this run

The [n = 30 report](results/meanrule30_report.md) produced a new claim:

> **8/30 pairs positive** where chance is 15, binomial two-sided **p = 0.016**,
> median order effect **−0.32**. Ending on the *stronger* component scores
> **lower**.

I flagged it there as "a new single-sample finding at exactly the evidential
level the 6/7 claim once had, needing its own replication". That is not a
formality. The order effect has now been read three ways on this same protocol:

| sample | n | positive | reading |
|---|---|---|---|
| catchase v2 | 7 | 6/7 | ends-on-stronger scores **higher** |
| meanrule v1 | 6 | 2/6 | the reverse |
| meanrule30 | 30 | 8/30 | ends-on-stronger scores **lower** (p = 0.016) |

[FINDINGS §5.1](FINDINGS.md) says small samples here did not merely add noise,
they got the *direction* wrong. The 8/30 result is the first with enough units to
be worth believing — which is exactly why it should be tested before anything is
built on it, rather than after.

A second question rides along at no extra cost. The n = 30 run found the frozen
rule's **calibration** fails out of sample (refit `0.62 × mean + 1.86` against
frozen `0.70 × mean + 1.16`, under-predicting on 26 of 30). Whether the refit is
genuinely better, or just fitted to that sample, is decidable on fresh pairs.

## Design, fixed in advance

- **Pool:** unchanged — all 35 glyphs of the repository's `e2_core35_*` panels,
  every one exactly 4 prefix tokens.
- **Pairs:** 30 new ones, drawn by `random.Random(20260810)` — a different seed —
  with the same reuse cap of 2, and **excluding every pair measured in
  `meanrule30_v1`**. Disjoint pairs from the same population.
- **Solo components:** reused from `meanrule30_v1_summary.json`. They are
  deterministic under an identical protocol with a cached null, so re-measuring
  all 35 would only burn compute. **Five are re-measured as a frame check**
  (`animals_1`, `food_4`, `sky_2`, `social_6`, `transport_3`); if any differs
  from its recorded value by more than 0.01 the run aborts and nothing is
  reported.
- **Protocol:** identical to every earlier run — layers 10-19, α = 0.5, 24
  random directions per (layer, target), same wrappers, targets and null seeds.
- **Sign convention:** `order_effect = mid(weak-then-strong) − mid(strong-then-weak)`,
  with strong/weak fixed once from the reused solo values. Identical to
  `cat_chase2.py` and `mean_rule_n30.py`, so the counts are directly comparable.

## Primary hypothesis and decision rule

**H:** the reversal replicates — ending on the stronger component scores lower.

**Predicted:** fewer than 15 of 30 positive, in the same direction as 8/30.

| result | verdict |
|---|---|
| positive count < 15 **and** binomial two-sided p < 0.05 | **REPLICATED** |
| positive count < 15, p ≥ 0.05 | **SAME DIRECTION, NOT SIGNIFICANT** |
| positive count ≥ 15 | **NOT REPLICATED** — the 8/30 finding is retracted |

A non-replication will be reported and the claim retracted from FINDINGS §3.
Eight claims have already been retracted in this directory; a ninth is not a
problem, and retracting my *newest* one is the point of running this.

Pooling the two samples (60 pairs) will also be reported, since both are drawn
from one population under one protocol.

## Secondary question, specified now

Does the refit beat the frozen rule out of sample? On these 30 fresh pairs,
compute MAE for both:

- frozen: `0.70 × mean + 1.16`
- refit from meanrule30: `0.62 × mean + 1.86`

**Reported as a comparison, not as a decision.** The refit was fitted on the
first 30 pairs, so a win here is evidence it generalises; a loss means the
calibration is sample-specific in both directions. Neither outcome changes the
primary verdict, and neither may be used to rescue it.

## What this cannot establish

Same model, same site, same position, same strength, same three targets, same
component pool, same author. This tests whether the 8/30 result survives a fresh
draw of pairs — not whether it survives a different model, tokenizer or prompt
set. A replication here raises the claim from "one sample" to "two samples on one
protocol", which is still a long way from a property of language models. No
causal or semantic claim is authorised either way
(`pre-causal-activation-screen`, `causal_claim_authorized: false`).

## Amendment 1 — the frame-check identifiers were written wrong (2026-08-09)

**Filed before any measurement existed, and committed before the rerun.**

The section above names the five frame-check components as `animals_1`,
`food_4`, `sky_2`, `social_6`, `transport_3`. **No component has those
identifiers.** The pool's real ids are `animals_animals_slot_03`,
`food_food_slot_06`, and so on — I wrote the shorthand from memory instead of
reading the panel files, and the first run died on `KeyError: 'animals_1'`
while assembling the panel.

**Nothing had been measured when it died.** The traceback in
`results/orderrev_v1_console.log` lands immediately after `device=mps
num_layers=28` — before the concatenation check, before the first forward pass,
and before any file was written. `orderrev_v1_summary.json` did not exist. So
this amendment is decided on zero data, which is the only condition under which
amending a pre-registration is honest.

**Resolution, mechanical and stated in full:** `<family>_<k>` denotes the k-th
component of that family, 1-indexed, in the sorted order the loader already
uses. Every family holds exactly 7 glyphs at contiguous slots 03-09, so the map
is total and has no free choices:

| as written | resolves to | recorded `mid` |
|---|---|---|
| `animals_1` | `animals_animals_slot_03` | 3.6062 |
| `food_4` | `food_food_slot_06` | 5.5314 |
| `sky_2` | `sky_sky_slot_04` | 3.8401 |
| `social_6` | `social_social_slot_08` | 2.8690 |
| `transport_3` | `transport_transport_slot_05` | 3.3492 |

The runner now parses these five names out of *this file* and aborts if its own
list disagrees, so the shorthand can no longer drift from what is registered.

**What this does not touch.** The frame check is a sanity check on reused solo
values, not a hypothesis test: it can only abort the run, never change a
verdict. The pairs, the seed, the exclusion set, the decision rule, the
tolerance and the secondary comparison are all unchanged, and the recorded
values in the table above are read from the *prior* run, not from anything
measured here.
