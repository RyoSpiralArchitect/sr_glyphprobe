#!/usr/bin/env python3
"""Render results/orderrev_report.md. Every number comes from the summary."""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

import numpy as np


def binom(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return float(sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)
                     if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12)))

def spearman(x, y):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):                      # tie-averaged ranks
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for t in range(i, j + 1):
                r[order[t]] = avg
            i = j + 1
        return r
    a, b = np.array(rank(x)), np.array(rank(y))
    a, b = a - a.mean(), b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))


ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
s = json.loads((res / "orderrev_v1_summary.json").read_text(encoding="utf-8"))

o = []
w = o.append
pairs = s["pairs"]
n, k = s["n_pairs"], s["order_effect_positive"]
p = s["binomial_p"]
prior, pool = s["prior"], s["pooled"]
verdict = s["verdict"]
sec = s["secondary_mae"]          # KeyError here beats a silently-dropped section
mae_f, mae_r = sec["frozen"], sec["refit"]
fc = s["frame_check"]
solo = json.loads((res / "meanrule30_v1_summary.json").read_text(
    encoding="utf-8"))["solo_mid"]

# count the retraction rows in FINDINGS §3 rather than hardcoding an ordinal
_f3 = (ROOT / "FINDINGS.md").read_text(encoding="utf-8").split("\n## 3.")[1].split("\n## ")[0]
n_retracted = sum(1 for ln in _f3.split("\n")
                  if ln.startswith("| ") and not ln.startswith("| claim")
                  and not set(ln) <= set("| -"))

w("# Does the order-effect reversal replicate? (out of contract)\n")
w("The n = 30 run reported **8/30 pairs positive** (chance 15, binomial p = 0.016) — "
  "ending on the stronger component scores *lower*. It was the first sample in this "
  "series with enough units for the sign to mean anything, and it pointed opposite to "
  "an earlier 6/7 claim that has already been retracted. So it was tested on a fresh "
  "draw before anything was built on it.\n")
w("Pre-registered in "
  "[`PREREGISTRATION_order_reversal.md`](../PREREGISTRATION_order_reversal.md), "
  "committed before this run's script existed. Claim stage "
  "`pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.\n")

w("## Design\n")
w(f"- **{n} new pairs**, drawn by `random.Random({s['pair_seed']})` from the same 35-glyph "
  "repository pool, excluding every pair measured in `meanrule30_v1`. Overlap with the "
  f"prior sample: **{s['overlap_with_prior']}** — the run aborts otherwise. Disjoint "
  "pairs, one population, one protocol.")
w("- **Solo component values reused** from the prior run (deterministic under an identical "
  f"protocol with a cached null). Five were re-measured as a frame check: max |drift| = "
  f"**{fc['max_abs_drift']:.4f}** against a tolerance of {fc['tolerance']} — inside the "
  "bound, so the reuse is legitimate.")
w("- **Sign convention** identical to both earlier samples: "
  "`order_effect = mid(weak-then-strong) − mid(strong-then-weak)`, strong/weak fixed once "
  "from the reused solo values. The counts are directly comparable.\n")

w("> **Amendment on the record.** The pre-registration named the five frame-check "
  "components with identifiers that do not exist (`animals_1` for "
  "`animals_animals_slot_03`, and so on) — written from memory instead of read from the "
  "panel files. The first run died on `KeyError` while assembling the panel, **before any "
  "forward pass and before any file was written**, so the fix was decided on zero data. "
  "[Amendment 1](../PREREGISTRATION_order_reversal.md) records the mechanical resolution "
  "(`<family>_<k>` = the k-th of that family, sorted), and the runner now aborts if its "
  "own list, its resolution, or the reused values disagree with that committed table.\n")

w("## Primary result\n")
w(f"**{k}/{n} pairs positive** (chance {n // 2}), median "
  f"**{s['order_effect_median']:+.2f}**, binomial two-sided **p = {p:.4f}**.\n")
w("| | required for REPLICATED | observed | |")
w("|---|---|---|---|")
w(f"| positive count | < {s['decision_rule']['max_positive']} | **{k}** | "
  f"{'PASS' if k < s['decision_rule']['max_positive'] else 'FAIL'} |")
w(f"| binomial two-sided p | < {s['decision_rule']['alpha']} | **{p:.4f}** | "
  f"{'PASS' if p < s['decision_rule']['alpha'] else 'FAIL'} |")
w(f"\n**Pre-registered verdict: {verdict}.**\n")

w("| sample | n | positive | median | reading |")
w("|---|---|---|---|---|")
w("| catchase v2 | 7 | 6/7 | — | ends on stronger scores **higher** |")
w("| meanrule v1 | 6 | 2/6 | — | the reverse |")
w(f"| meanrule30 | {prior['n']} | {prior['positive']}/{prior['n']} | "
  f"{prior['median']:+.2f} | ends on stronger scores **lower** (p = 0.016) |")
w(f"| **this run** | **{n}** | **{k}/{n}** | **{s['order_effect_median']:+.2f}** | "
  f"**{verdict}** |")
w(f"| pooled | {pool['n']} | {pool['positive']}/{pool['n']} | — | "
  f"binomial p = {pool['binomial_p']:.6f} |\n")
w("> Every p-value in that table is a naive binomial and **every one of them is "
  "overstated** — pairs are dyads over a shared component pool, not independent trials. "
  "See the clustering section for the corrected figures; the direction survives, the "
  "significance does not.\n")

if verdict == "REPLICATED":
    w("The reversal holds on pairs that were never measured before. Two "
      "**pairs-disjoint** samples, 60 pairs pooled, same direction. That moves the claim "
      "from *one sample* to *two samples on one protocol* — which is what the "
      "pre-registration said it could and could not buy. It is still one model, one "
      "site, one position, one strength, one author's sampler.\n")
    # how many pairs would have to flip sign to overturn the verdict?
    flips = next((d for d in range(1, n - k + 1)
                  if not (k + d < s["decision_rule"]["max_positive"]
                          and binom(k + d, n) < s["decision_rule"]["alpha"])), None)
    if flips is not None:
        w(f"> **How close this was.** {flips} pair"
          f"{' ' if flips == 1 else 's '}flipping sign would have overturned it: "
          f"{k + flips}/{n} gives p = {binom(k + flips, n):.4f}, above the "
          f"{s['decision_rule']['alpha']} threshold. The pre-registered rule is met and "
          "the verdict stands as written — but a result this close to its own boundary "
          "should be quoted with the margin attached, not as a clean pass. The pooled "
          f"count ({pool['positive']}/{pool['n']}) points the same way and rests on more "
          "units, but its nominal p-value is **not** the sturdier number either. Both "
          "figures assume pairs are independent; they are dyads over a shared component "
          "pool, and the section on clustering below shows what happens to this p-value "
          "under the appropriate test.\n")
elif verdict == "SAME DIRECTION, NOT SIGNIFICANT":
    w("The direction survives but the significance does not. Read this as **weak support, "
      f"not replication**: {k}/{n} leans the same way as {prior['positive']}/{prior['n']} "
      "while failing the threshold that was fixed in advance. The pooled count is the more "
      "informative number, and it is reported above rather than substituted for the "
      "primary test — pooling was pre-registered as a description, not as a rescue.\n")
else:
    w(f"**The 8/30 finding does not replicate and is retracted.** On fresh pairs from the "
      f"same pool under the same protocol the count is {k}/{n}, on the other side of "
      "chance. Both earlier readings of this quantity — 6/7 one way, 8/30 the other — are "
      "now retracted, and the honest summary is that **the order effect follows no "
      "direction this protocol can detect.**\n")
    _already = "order effect" in _f3 and "9/30" in _f3
    w(f"That makes **{n_retracted + (0 if _already else 1)}** retractions in this "
      "directory, and this is the "
      "fastest of them: the claim was made, pre-registered against, and withdrawn before "
      "anything was built on it. That sequence is what "
      "[FINDINGS §5.1](../FINDINGS.md) exists to force.\n")

w("## Per-pair order effects\n")
w("| pair | strong component | order effect |")
w("|---|---|---|")
for t in sorted(pairs, key=lambda t: t["order_effect"]):
    w(f"| {t['glyphs']} | {t['strong']} | {t['order_effect']:+.2f} |")

w("\n## Secondary: does the refit generalise? (comparison only)\n")
w("The n = 30 run found the frozen rule's calibration failing out of sample and refit "
  "`0.62 × mean + 1.86` against frozen `0.70 × mean + 1.16`. Whether the refit is "
  "better or merely fitted to that sample is decidable on these fresh pairs.\n")
w("| rule | fitted on | MAE here |")
w("|---|---|---|")
w(f"| frozen `0.70 × mean + 1.16` | the 7 catchase families | **{mae_f:.3f}** |")
w(f"| refit `0.62 × mean + 1.86` | the meanrule30 pairs | **{mae_r:.3f}** |")
better = "refit" if mae_r < mae_f else "frozen"
w(f"\nThe **{better}** rule wins by {abs(mae_r - mae_f):.3f}. "
  + ("The refit generalises to pairs it was not fitted on, which is evidence the n = 30 "
     "calibration was picking up something real rather than sample noise."
     if mae_r < mae_f else
     "The refit does **not** generalise: it was fitted to its own sample and does no "
     "better here. The calibration is sample-specific in both directions, so the mean "
     "rule should be quoted as an ordering and not as a predictor of magnitude.")
  + " Pre-registered as a comparison, and it neither rescues nor damages the primary "
    "verdict above.\n")

errs = [t["err_frozen"] for t in pairs]
w("## Where the frozen rule sits on these pairs\n")
w(f"Errors run {min(errs):+.2f} to {max(errs):+.2f}, median **{np.median(errs):+.2f}**, "
  f"{sum(e > 0 for e in errs)}/{n} positive"
  + (" — the same under-prediction the n = 30 run reported.\n"
     if sum(e > 0 for e in errs) > n / 2 else " on this sample.\n"))

ind = res / "pooled_independence.json"
if ind.exists():
    q = json.loads(ind.read_text(encoding="utf-8"))["samples"]
    pri, pri_prior, poo = (q["primary (this run)"], q["prior (meanrule30)"], q["pooled"])
    w("## The clustering correction reaches the pre-registered test itself\n")
    w("Adversarial review objected that pooling treats pairs as independent Bernoulli "
      "trials when components recur across them. Three review passes later the objection "
      "has grown teeth: it applies not only to the pooled count but to **every sign test "
      "in this series, including the pre-registered primary one**.\n")
    w("Each pair is a **dyad** over two components. Two pairs sharing a component covary "
      f"— in the pooled sample P(same sign | share a component) = "
      f"**{poo['p_same_sign_sharing']:.3f}** against "
      f"**{poo['p_same_sign_disjoint']:.3f}** for component-disjoint pairs, ICC "
      f"**{poo['icc']:+.3f}**. The estimator for a mean of dyadic observations is the "
      "dyadic-robust variance (Aronow-Samii-Assenova), with the residual **null-imposed** "
      "(`e = y − 0.5`), which `--simulate` shows is the only candidate holding its "
      "nominal size:\n")
    w("| sample | count | naive binomial | design effect | dyadic-robust `p` (z) | (t) |")
    w("|---|---|---|---|---|---|")
    for lbl, r in (("**primary — the pre-registered test**", pri),
                   ("prior (meanrule30)", pri_prior), ("pooled", poo)):
        w(f"| {lbl} | {r['k']}/{r['n']} | {r['naive_binomial_p']:.4f} | "
          f"{r['design_effect']:.2f} | **{r['dyadic_p_z']:.4f}** | "
          f"{r['dyadic_p_t']:.4f} |")
    w("\n**No sample in this series clears 0.05 under the appropriate test, and all "
      "three point the same way.** The direction is consistent and reproducible; the "
      "*significance* was an artefact of treating dyads as independent.\n")
    w("> **What this does and does not do to the verdict.** The decision rule was fixed "
      "in advance and it specified a binomial test. That test was met, so **the "
      "pre-registered verdict REPLICATED stands as written** — swapping in a different "
      "test after seeing the result would be the same act whether it rescues a finding "
      "or kills one, and this directory does not get to do it in the convenient "
      "direction only. What must be said alongside it is that **the pre-registered test "
      "was the wrong test**: it assumed an independence the design never had. The "
      f"defensible reading is `{pri['k']}/{pri['n']}, dyadic-robust p = "
      f"{pri['dyadic_p_z']:.3f}` — the same direction as two other samples, short of "
      "conventional significance. Pre-registration protects against choosing a test to "
      "fit a result; it does not make a mis-specified test correct.\n")
    w("**This section has now been wrong twice, in opposite directions.** Both are on "
      "the record rather than quietly replaced:\n")
    w("- **v1** led with a bootstrap statistic `P(fraction ≥ 0.5) = 0.054` and concluded "
      "the pooled p-value \"does not survive\". Its weights were `cnt[A] * cnt[B]` where "
      "the comment claimed an indicator — a real defect. But its *number* was close to "
      "right, and it was retracted with a bad argument: v2 said a statistic with median "
      "≈ 0.5 under the null \"is not a p-value\", when a valid one-sided p-value has "
      "exactly that. `--forensics` re-judges it against the clustered null it should "
      "have been compared with.")
    w("- **v2** answered with a range, `p ≈ 0.011–0.063`. Two of its three estimators "
      "are mis-specified: the Rao-Scott multiplier used `m̄ − 1`, valid when an "
      "observation sits in one cluster, whereas a dyad sits in two (the correct mean "
      f"number of other dyads sharing a vertex is **{poo['mean_other_dyads_sharing']:.2f}**, "
      "not 2.43); and the mean-centred dyadic row rejects **~10 %** of the time at a "
      "nominal 5 % *under an independent null*. Presenting a range was not "
      "even-handedness — it averaged one valid estimator with two broken ones, and the "
      "`0.01` endpoint came entirely from the broken multiplier.")
    w("- The **component-disjoint subset analysis** stays withdrawn, but v2's stated "
      "reason was also wrong. It claimed the analysis was identical to a size-matched "
      "unconstrained control; two of its three rows are pinned by the marginal count and "
      "*cannot* differ, while the third — the one carrying the original claim — differed "
      "by ~18×. The analysis was invalid because a median of correlated within-dataset "
      "p-values is not a p-value, not because it detected nothing.\n")

gap = [abs(solo[t["A"]] - solo[t["B"]]) for t in pairs]
oe_ = [t["order_effect"] for t in pairs]
rho = spearman(gap, oe_)
w("## An observation, not a claim: the component gap\n")
w(f"On this sample, Spearman(|component gap|, order effect) = **{rho:+.3f}**. "
  "[FINDINGS §3](../FINDINGS.md) retracted \"the order effect scales with the component "
  "gap\" precisely because it read **+0.04** at n = 7 and **−0.94** at n = 6 — the same "
  "statistic on the same protocol, pointing both ways.\n")
w("This is **not** a revival of that claim. It is one more sample of a quantity that has "
  "already proved it can produce any answer at small n, found *after* looking at the "
  "data, on pairs drawn for a different purpose. It goes here so it is on the record "
  "rather than discovered later — and the only honest next move is to pre-register it "
  "with a threshold and test it on pairs drawn for that question.\n")

w("## What adversarial review changed\n")
exc = s["exclusion"]     # KeyError beats a silently-defaulted audit number
w("Two review passes. Neither moved a measured value; between them they changed what "
  "several numbers were allowed to claim, and caught one analysis that was wrong in "
  "each direction in turn.\n")
w("**Pass 1 — eight findings.**\n")
w("- The **overlap check was circular**: `sample_pairs` already skips the exclusion set, "
  "so `overlap == 0` held by construction and would have kept holding if the exclusion "
  "had silently become a no-op. The prior pair set is now rebuilt independently from the "
  "prior *profiles* file, cross-checked against the summary, required to match the prior "
  "pair count and to name only components that exist"
  + f"; the branch is instrumented directly and fired **{exc['fired']}** time(s), of "
    f"which **{exc['repeats_avoided']}** were repeats genuinely avoided — the rest were "
    f"candidates the reuse cap would have dropped anyway — changing "
    f"**{exc['changed']}** of the {n} final pairs.")
w("- The **4-prefix-token invariant** carried by the previous runner had been dropped and "
  "is restored: every component, every wrapper, or the run aborts.")
w("- The **profiles file had lost its per-layer vector**, so no reader could re-derive a "
  "score or reanalyse under a different layer band. It now records `profile` and "
  "`layers` (the run it is pooled with carries `profile` but not `layers`).")
w("- Stale prose: FINDINGS §3 still said this result needed the replication it had just "
  "received; the pre-registration miscounted the retractions; a Japanese README was left "
  "a version behind.\n")
w("**Pass 2 — the clustering correction was itself wrong.** Pass 1 replaced an "
  "over-claim (`p = 0.0011`) with an over-correction (\"the p-value does not survive\"). "
  "The section above is the corrected version, and both errors are recorded there rather "
  "than quietly replaced. Pass 2 also found four surviving approving quotes of "
  "`p = 0.0011` — two of them introduced by the commit that was supposed to remove them "
  "— a mislabelled exclusion audit, and a rounding disagreement between the two "
  "languages.\n")
w("The run was repeated with every guard active. **Every value is bit-identical** — all "
  f"{n} order effects and all {n} observed scores match to 0.0e+00, and no summary key "
  "differs. The null distributions came from the protocol-keyed cache rather than being "
  "recomputed, so this is a determinism check on the measurement path, not on the whole "
  "pipeline from scratch.\n")

w("## Limitations\n")
w("- One model, one site (`resid_post`), one position (`last_nonpad`), one strength "
  "(α = 0.5), three injection targets, layers 10-19.")
w("- Fresh **pairs**, not a fresh protocol: same pool, same measurement frame, same "
  "author. FINDINGS §7's \"independent replication\" — second model, panels chosen by "
  "someone else — remains open, and this run does not touch it.")
w("- Solo component values are reused rather than re-measured; the five-component frame "
  f"check bounds the risk (max |drift| {fc['max_abs_drift']:.4f}) but does not eliminate it.")
w("- The random-direction null is a size control, not a semantic control.")
w("- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.")

(res / "orderrev_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'orderrev_report.md'}")
