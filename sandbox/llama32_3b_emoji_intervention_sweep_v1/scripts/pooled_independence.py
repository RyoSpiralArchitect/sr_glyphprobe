#!/usr/bin/env python3
"""Does the pooled 17/60 survive the fact that pairs share components?

Adversarial review, correctly, objected that the pooled binomial treats 60 pairs
as 60 independent Bernoulli trials when the reuse cap of 2 puts most components
into two pairs each, both samples draw from one 35-glyph pool, and strong/weak in
both is assigned from a single measurement of `solo_mid`. The pairs are disjoint;
the *units* are not independent.

Two sensitivity analyses, both on committed data, no model required:

  1. maximal component-disjoint subsets -- every pair in a subset shares no
     component with any other, so the sign test on it is unimpeachable. Reported
     as a distribution over many random maximal subsets, since the subset is not
     unique.
  2. component-level bootstrap -- resample components with replacement and weight
     each pair by how often its components were drawn.

Neither replaces the pre-registered primary test. They bound how much the pooled
p-value was inflated by the clustering.
"""
from __future__ import annotations

import json
import random
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
N_SUBSETS, N_BOOT, SEED = 2000, 20000, 20260811


def binom_two_sided(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return float(sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)
                     if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12)))


def load():
    out = []
    for tag in ("meanrule30_v1", "orderrev_v1"):
        s = json.loads((res / f"{tag}_summary.json").read_text(encoding="utf-8"))
        for t in s["pairs"]:
            out.append((t["A"], t["B"], float(t["order_effect"]), tag))
    return out


def main() -> int:
    pairs = load()
    n = len(pairs)
    k = sum(oe > 0 for _, _, oe, _ in pairs)
    print(f"pooled: {k}/{n} positive, binomial two-sided p = {binom_two_sided(k, n):.6f}")
    comps = {c for a, b, _, _ in pairs for c in (a, b)}
    reuse = {c: sum(c in (a, b) for a, b, _, _ in pairs) for c in comps}
    print(f"{len(comps)} distinct components; "
          f"{sum(v > 1 for v in reuse.values())} appear in more than one pair "
          f"(max {max(reuse.values())})")

    # ---- 1. maximal component-disjoint subsets ---------------------------
    rng = random.Random(SEED)
    sizes, ks, ps = [], [], []
    for _ in range(N_SUBSETS):
        order = pairs[:]
        rng.shuffle(order)
        used, sub = set(), []
        for a, b, oe, _ in order:
            if a in used or b in used:
                continue
            used |= {a, b}
            sub.append(oe)
        sizes.append(len(sub))
        ks.append(sum(v > 0 for v in sub))
        ps.append(binom_two_sided(ks[-1], len(sub)))
    sizes, ks, ps = np.array(sizes), np.array(ks), np.array(ps)
    frac = ks / sizes
    print(f"\ncomponent-disjoint subsets ({N_SUBSETS} draws): "
          f"size {sizes.min()}-{sizes.max()} (median {int(np.median(sizes))})")
    print(f"  positive fraction : median {np.median(frac):.3f}, "
          f"90% range [{np.quantile(frac, 0.05):.3f}, {np.quantile(frac, 0.95):.3f}]")
    print(f"  sign-test p       : median {np.median(ps):.4f}, "
          f"{100 * np.mean(ps < 0.05):.1f}% of subsets reach p < 0.05")
    print(f"  subsets with a majority positive (i.e. against the effect): "
          f"{100 * np.mean(frac >= 0.5):.2f}%")

    # ---- 2. component-level bootstrap ------------------------------------
    nprng = np.random.default_rng(SEED)
    clist = sorted(comps)
    idx = {c: i for i, c in enumerate(clist)}
    A = np.array([idx[a] for a, b, _, _ in pairs])
    B = np.array([idx[b] for a, b, _, _ in pairs])
    pos = np.array([oe > 0 for _, _, oe, _ in pairs], float)
    boot = []
    for _ in range(N_BOOT):
        draw = nprng.integers(0, len(clist), len(clist))
        cnt = np.bincount(draw, minlength=len(clist))
        wgt = cnt[A] * cnt[B]                      # pair present iff both drawn
        if wgt.sum() == 0:
            continue
        boot.append(float((wgt * pos).sum() / wgt.sum()))
    boot = np.array(boot)
    print(f"\ncomponent-level bootstrap ({len(boot)} resamples):")
    print(f"  positive fraction : {boot.mean():.3f}, "
          f"95% CI [{np.quantile(boot, 0.025):.3f}, {np.quantile(boot, 0.975):.3f}]")
    print(f"  P(fraction >= 0.5) = {np.mean(boot >= 0.5):.4f}")

    summary = {
        "pooled": {"positive": k, "n": n, "binomial_p": binom_two_sided(k, n)},
        "n_components": len(comps),
        "components_in_multiple_pairs": sum(v > 1 for v in reuse.values()),
        "disjoint_subsets": {
            "n_draws": N_SUBSETS, "seed": SEED,
            "size_median": int(np.median(sizes)),
            "positive_fraction_median": float(np.median(frac)),
            "positive_fraction_q05": float(np.quantile(frac, 0.05)),
            "positive_fraction_q95": float(np.quantile(frac, 0.95)),
            "sign_test_p_median": float(np.median(ps)),
            "frac_subsets_p_lt_05": float(np.mean(ps < 0.05)),
            "frac_subsets_majority_positive": float(np.mean(frac >= 0.5)),
        },
        "component_bootstrap": {
            "n_resamples": int(len(boot)), "seed": SEED,
            "mean": float(boot.mean()),
            "ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
            "p_ge_half": float(np.mean(boot >= 0.5)),
        },
    }
    (res / "pooled_independence.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nwrote {res / 'pooled_independence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
