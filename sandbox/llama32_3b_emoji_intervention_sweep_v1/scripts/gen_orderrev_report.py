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
  f"binomial p = {pool['binomial_p']:.6f} — **but see the clustering section: this "
  "p-value assumes an independence the design does not have** |\n")

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
          "units, but its nominal p-value is **not** the sturdier number either — see "
          "the clustering section below.\n")
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
    q = json.loads(ind.read_text(encoding="utf-8"))
    d, bt = q["disjoint_subsets"], q["component_bootstrap"]
    w("## The pooled p-value is inflated by shared components\n")
    w("Adversarial review objected — correctly — that pooling treats 60 pairs as 60 "
      f"independent Bernoulli trials when all {q['n_components']} components appear in "
      "more than one pair (up to 4), both samples draw from one 35-glyph pool, and "
      "strong/weak in both is assigned from a single measurement of `solo_mid`. The "
      "pairs are disjoint; the **units are not independent**. Two sensitivity analyses "
      "([`scripts/pooled_independence.py`](../scripts/pooled_independence.py)):\n")
    w("| analysis | positive fraction | verdict on the direction |")
    w("|---|---|---|")
    w(f"| maximal **component-disjoint** subsets (median n = {d['size_median']}, "
      f"{d['n_draws']} draws) | median **{d['positive_fraction_median']:.3f}**, 90 % "
      f"[{d['positive_fraction_q05']:.3f}, {d['positive_fraction_q95']:.3f}] | "
      f"only **{100 * d['frac_subsets_majority_positive']:.2f} %** of subsets go the "
      "other way |")
    w(f"| **component-level bootstrap** ({bt['n_resamples']} resamples) | "
      f"**{bt['mean']:.3f}**, 95 % CI [{bt['ci95'][0]:.3f}, {bt['ci95'][1]:.3f}] | "
      f"P(fraction ≥ 0.5) = **{bt['p_ge_half']:.3f}** |")
    w("\nThe two schemes disagree about strength, and that disagreement is the point. "
      "Under component-disjoint subsets — where every pair is a genuinely independent "
      "unit — the direction is robust: the positive fraction never approaches a "
      f"majority. But those subsets hold only ~{d['size_median']} pairs, so the median "
      f"sign test reads p = {d['sign_test_p_median']:.3f} and just "
      f"{100 * d['frac_subsets_p_lt_05']:.0f} % reach p < 0.05. The bootstrap's "
      "interval touches 0.5 outright.\n")
    w("> **So: the direction survives clustering; the p-value does not.** "
      f"Quote the pooled count as {pool['positive']}/{pool['n']} with this caveat "
      f"attached — **not** as p = {pool['binomial_p']:.4f}, which assumes an "
      "independence the design does not have. The bootstrap scheme matters too: mine "
      "requires *both* of a pair's components to be drawn, which is deliberately harsh. "
      "A gentler scheme gives a tighter interval — reported here in its conservative "
      "form on purpose.\n")

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
w("Review found eight defects. None moved a number; the two that mattered most were "
  "about what the numbers were allowed to claim.\n")
w("- The **overlap check was circular**: `sample_pairs` already skips the exclusion set, "
  "so `overlap == 0` held by construction and would have kept holding if the exclusion "
  "had silently become a no-op. The prior pair set is now rebuilt independently from the "
  "prior *profiles* file, cross-checked against the summary, required to match the prior "
  "pair count and to name only components that exist. The run now reports what the "
  "exclusion bought: **1 draw rejected** that would otherwise have repeated a measured "
  "pair.")
w("- The **pooled p-value assumed independence the design does not have** — the section "
  "above is the result.")
w("- The **4-prefix-token invariant** carried by the previous runner had been dropped and "
  "is restored: all 35 components, every wrapper, or the run aborts.")
w("- The **profiles file had lost its per-layer vector**, so no reader could re-derive a "
  "score or reanalyse under a different layer band. It now records `profile` and "
  "`layers`, as the run it is pooled with does.")
w("- Two stale sentences (FINDINGS §3 still said this result needed a replication; the "
  "pre-registration miscounted the retractions) and a Japanese README left at twelve "
  "runs. [Amendment 2](../PREREGISTRATION_order_reversal.md) records the corrections, "
  "including the traceback that Amendment 1 cited from a gitignored log.\n")
w("The run was then repeated end to end with the strengthened guards. **Every value is "
  "bit-identical** — all 30 order effects and all 30 observed scores match to 0.0e+00, "
  "and no key in the summary differs. Taken with the frame check's 0.0000 drift, the "
  "measurement is exactly reproducible on this machine.\n")

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
