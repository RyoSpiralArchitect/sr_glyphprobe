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

## Amendment 2 — corrections raised by adversarial review (2026-08-09)

Filed after the primary result was known. Items (a) and (b) are defects in this
file's own prose and change no design element, decision rule or reported number.
Item (c) is different and is flagged as such: it records changes made to the
**runner** after the result was known. Those changes strengthened guards without
altering any measurement — the run was repeated with all of them active and every
value came back bit-identical — but they are post-hoc changes to the instrument
and belong on the record as that, not as prose corrections.

**(a) The traceback cited in Amendment 1 cannot be checked against any commit.**
Amendment 1 rests its "decided on zero data" claim on
`results/orderrev_v1_console.log`, but `.gitignore` excludes `*.log`, so no
reviewer can open it — and the file has since been overwritten by the successful
run, so it no longer exists in any form. Quoting it here is therefore the only
record, and the quotation carries an important caveat: **its line numbers and
variable names match no committed revision of the script.** The crash happened in
a working-tree version that was never committed (the first commit of
`order_reversal.py`, `8d19d1a`, already contains the Amendment 1 fix), which is
why it refers to a variable `cid` that appears in no commit. A reviewer cannot
verify this traceback; they can only note that it is consistent with the
`KeyError: 'animals_1'` that Amendment 1 describes, and that the commit order
(pre-registration `d1896cc`, then amendment `b923b3d`, then script `8d19d1a`) is
independently checkable and does corroborate the sequence.

```
device=mps num_layers=28
Traceback (most recent call last):
  File ".../scripts/order_reversal.py", line 373, in <module>
    sys.exit(main())
  File ".../scripts/order_reversal.py", line 206, in main
    panel += [{"id": f"CHECK::{cid}", "glyph": by_id[cid]["glyph"], "parts": []}
                                               ~~~~~^^^^^
KeyError: 'animals_1'
```

`device=mps num_layers=28` is printed immediately after the weights load and
immediately before panel assembly. Everything that measures anything — the
concatenation check, the wrapper and target forward passes, the null build, the
per-glyph loop — comes after the failing line, and `orderrev_v1_summary.json` did
not exist. The claim stands; it is now checkable.

**(b) The retraction count above is wrong.** The "Primary hypothesis" section
says "Eight claims have already been retracted in this directory; a ninth is not
a problem." [FINDINGS §3](FINDINGS.md) lists **seven**, so a further retraction
would have been the eighth. The error is in this file only — no script, report or
verdict reads that number, and the report generator counts the rows in FINDINGS
rather than trusting a written ordinal.

**(c) What review changed in the runner, after the result was known.** Guards
were strengthened and the run repeated; every value came back bit-identical,
which is stated in the report as a determinism check rather than as a new result.

- The overlap check was **circular** — `sample_pairs` already skips everything in
  the exclusion set, so `overlap == 0` was true by construction and would have
  stayed true had the exclusion silently become a no-op. The set is now rebuilt
  independently from the prior *profiles* file, cross-checked against the
  summary, required to match the prior run's pair count, required to name only
  components that exist in the pool, and the run now reports how many draws the
  exclusion actually rejected (1).
- The **4-prefix-token invariant** carried by the previous runner had been
  dropped. It is restored: all 35 components must cost exactly 4 prefix tokens on
  every wrapper or the run aborts.
- The exclusion audit was **mislabelled**. It reported "1 draw rejected", which
  was the count of *unconstrained* draws that happened to land in the exclusion
  set — not the number of times the exclusion branch fired. `sample_pairs` is now
  instrumented directly: the branch fires **5** times, and **2** of the 30 final
  pairs differ from the unconstrained draw. Both numbers are written into the
  summary so no report has to hardcode them.
- The profiles file recorded only `mid`, losing the per-layer vector the prior
  run stored, so no reader could re-derive a score or reanalyse under a different
  layer aggregation. It now records `profile` and `layers` (the prior run's file
  carries `profile` but not `layers`).

## Amendment 3 — the clustering correction was itself wrong (2026-08-09)

A second adversarial review found that Amendment 2's headline caveat over-corrected
the very error it was fixing, and it is retracted here.

The caveat led with a bootstrap statistic `P(fraction >= 0.5) = 0.054`, read it as
"just above 0.05", and concluded that the pooled p-value "does not survive"
clustering. **That statistic is not a p-value.** Simulated under an independent
null it has median 0.51 and did not fall below ~0.06 in 200 draws, so the observed
0.054 sat below its entire null distribution — strong evidence read as weak. Its
weights were also `cnt[A] * cnt[B]` where the code comment claimed an indicator,
inflating the variance past any standard estimator.

The companion "component-disjoint subsets" analysis is withdrawn outright. Against
the control it never had — unconstrained subsets of the same size — it is
identical (median positive fraction 0.267 either way, median sign-test p 0.1185
either way). It measured the cost of discarding 45 of 60 observations, not the
cost of dependence.

Corrected: these pairs are dyads over components, so the estimator is a
dyadic-robust variance (Aronow-Samii-Assenova), reported beside a Rao-Scott
design effect under both residual conventions. Clustered p spans **0.011 to
0.063**, against a naive 0.0011 — inflated 10-60x, straddling 0.05, not
annihilated. The clustering objection was right; both of this file's attempts to
quantify it were wrong, in opposite directions.

## Amendment 4 — the pre-registered test was mis-specified (2026-08-09)

A third adversarial review found that Amendment 3's correction was itself wrong,
and that the underlying objection reaches further than any earlier amendment
admitted: **it invalidates the primary test registered in this file.**

### What the decision rule got wrong

The rule above fixes a binomial test on 30 pairs. A binomial test assumes
independent trials. These pairs are **dyads** over a 35-component pool: components
recur across pairs, and two pairs sharing a component covary (pooled ICC +0.306,
P(same sign | share a component) 0.718 against 0.574 for disjoint pairs). The
design never had the independence the test assumes.

Under the dyadic-robust variance (Aronow-Samii-Assenova) with a null-imposed
residual — the only candidate that holds its nominal size in simulation, where
the mean-centred alternative rejects ~10 % at a nominal 5 % under an *independent*
null:

| sample | count | registered test | dyadic-robust p |
|---|---|---|---|
| **primary, this file's test** | 9/30 | 0.0428 (PASS) | **0.070** |
| prior (meanrule30) | 8/30 | 0.0161 | 0.066 |
| pooled | 17/60 | 0.0011 | 0.063 |

**No sample in the series clears 0.05 under the appropriate test. All three point
the same way.**

### What happens to the verdict

**REPLICATED stands as pre-registered.** The rule was fixed before the data
existed, it was applied as written, and it was met. Substituting a different test
after seeing the result is the same act whether it rescues a finding or kills one,
and a pre-registration that may be overridden whenever its author later prefers a
different analysis is not a pre-registration. The verdict is what the registered
rule returned.

**And the registered rule was the wrong rule.** Both sentences are true and
neither cancels the other. Pre-registration protects against choosing a test to
fit a result; it does not make a mis-specified test correct. Everything downstream
should quote **`9/30, dyadic-robust p = 0.07`** — a direction reproduced on three
samples, short of conventional significance — not `p = 0.043`.

The claim that survives is weaker and better specified than the one this file set
out to test: *ending on the stronger component scores lower, consistently in sign
across three samples of 30, 30 and 60 pairs, with no single sample reaching
conventional significance once component clustering is handled.*

### Two failed corrections, on the record

Amendments 2 and 3 both tried to quantify this objection and both got it wrong,
in opposite directions:

- **Amendment 2** answered with `P(bootstrap fraction >= 0.5) = 0.054` read as
  "just above 0.05", concluding the evidence did not survive. Its weighting was
  `cnt[A]*cnt[B]` where the comment claimed an indicator — a real defect — but its
  number was close to right.
- **Amendment 3** retracted that with a bad argument: it called a statistic whose
  null median is ~0.5 "not a p-value", which is precisely what a valid one-sided
  p-value looks like. It then substituted a **range**, `p ~ 0.011-0.063`, across
  three estimators of which two are mis-specified — a Rao-Scott multiplier of
  `m-1` (valid when an observation sits in one cluster; a dyad sits in two, and
  the correct mean number of other dyads sharing a vertex is 5.20, not 2.43), and
  the invalid mean-centred dyadic variance. The `0.01` endpoint came entirely from
  the broken multiplier.

The pattern is worth naming, because it cost three passes: each correction was
made in the direction of whichever criticism arrived last, without simulating the
estimator being installed. `scripts/pooled_independence.py --simulate` now does
that, and it is the reason this amendment states one number instead of a range.
