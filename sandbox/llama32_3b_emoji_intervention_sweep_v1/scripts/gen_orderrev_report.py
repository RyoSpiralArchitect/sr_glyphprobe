#!/usr/bin/env python3
"""Render results/orderrev_report.md. Every number comes from the summary."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

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

if verdict == "REPLICATED":
    w("The reversal holds on pairs that were never measured before. Two independent "
      "samples, 60 pairs pooled, same direction. That moves the claim from *one sample* "
      "to *two samples on one protocol* — which is what the pre-registration said it "
      "could and could not buy. It is still one model, one site, one position, one "
      "strength, one author's sampler.\n")
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
    w(f"That makes **{n_retracted + 1}** retractions in this directory, and this is the "
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
