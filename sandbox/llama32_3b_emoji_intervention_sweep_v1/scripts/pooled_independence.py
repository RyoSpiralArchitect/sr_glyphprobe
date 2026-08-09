#!/usr/bin/env python3
"""How much does shared-component clustering inflate the pooled binomial p?

The pooled sign test treats 60 pairs as 60 independent Bernoulli trials. They are
not: every component sits in several pairs, both samples draw from one 35-glyph
pool, and strong/weak in both is assigned from a single measurement of `solo_mid`.
The pairs are disjoint; the *units* are not independent.

This script quantifies the inflation. It replaces a first attempt that was wrong
in an instructive way, and both errors are recorded here rather than deleted:

  * v1 headline was `P(bootstrap fraction >= 0.5) = 0.054`, read as "just above
    0.05, so the p-value does not survive". That statistic is **not a p-value**.
    Simulated under an independent null it has median 0.51 and does not descend
    below ~0.06 in 200 draws, so 0.054 sits *below its entire null distribution* —
    the observation was strong evidence being read as weak. `--calibrate`
    reproduces that demonstration.
  * v1 weighted each pair by `cnt[A] * cnt[B]` while its comment claimed an
    indicator. The product inflates variance well past any standard estimator.

The pairs are **dyads over components**, so the textbook estimator is the
dyadic-robust variance (Aronow-Samii-Assenova): two pairs covary iff they share a
component. It is reported next to a Rao-Scott design-effect correction and the
naive binomial, under both residual conventions, because the conventions disagree
about whether the result clears 0.05 and picking one after seeing them would be
the same error this directory keeps retracting.

No model required; runs off committed JSON.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from math import comb, erfc, sqrt
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
SEED = 20260811


def z2p(z: float) -> float:
    return float(erfc(abs(z) / sqrt(2.0)))


def binom_two_sided(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return float(sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)
                     if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12)))


def load():
    out = []
    for tag in ("meanrule30_v1", "orderrev_v1"):
        s = json.loads((res / f"{tag}_summary.json").read_text(encoding="utf-8"))
        for t in s["pairs"]:
            out.append((t["A"], t["B"], float(t["order_effect"])))
    return out


def share_matrix(A, B):
    n = len(A)
    return np.array([[len({A[i], B[i]} & {A[j], B[j]}) > 0 for j in range(n)]
                     for i in range(n)])


def dyadic_se(y, share, center):
    """Aronow-Samii-Assenova: two dyads covary iff they share a vertex."""
    e = y - center
    return float(np.sqrt((e[:, None] * e[None, :] * share).sum() / len(y) ** 2))


def calibrate(y, A, B, n_sims=200, n_boot=1500, seed=7):
    """Show that v1's `P(boot >= 0.5)` is not a p-value: simulate its null."""
    comps = sorted(set(A) | set(B))
    idx = {c: i for i, c in enumerate(comps)}
    ia = np.array([idx[a] for a in A])
    ib = np.array([idx[b] for b in B])
    rng = np.random.default_rng(seed)

    def stat(yv):
        out = []
        for _ in range(n_boot):
            cnt = np.bincount(rng.integers(0, len(comps), len(comps)),
                              minlength=len(comps))
            w = cnt[ia] * cnt[ib]                    # v1's product weighting
            if w.sum():
                out.append((w * yv).sum() / w.sum())
        return float(np.mean(np.array(out) >= 0.5))

    null = np.array([stat(rng.binomial(1, 0.5, len(y)).astype(float))
                     for _ in range(n_sims)])
    return {"n_sims": n_sims, "median": float(np.median(null)),
            "q01": float(np.quantile(null, 0.01)), "min": float(null.min()),
            "observed_v1": 0.0539,
            "calibrated_p": float(np.mean(null <= 0.0539))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subsets", type=int, default=20000)
    ap.add_argument("--calibrate", action="store_true",
                    help="simulate the null of v1's miscalibrated statistic")
    args = ap.parse_args()

    pairs = load()
    A = [a for a, b, _ in pairs]
    B = [b for a, b, _ in pairs]
    y = np.array([oe > 0 for _, _, oe in pairs], float)
    n = len(y)
    ybar = float(y.mean())
    k = int(y.sum())
    share = share_matrix(A, B)
    deg = Counter(A) + Counter(B)

    print(f"pooled: {k}/{n} positive, fraction {ybar:.4f}, "
          f"exact binomial two-sided p = {binom_two_sided(k, n):.6f}")
    print(f"{len(deg)} components, every one in >1 pair, max {max(deg.values())}; "
          f"mean pairs per component {np.mean(list(deg.values())):.2f}")

    # ---- how strong is the dependence, in the data ------------------------
    sh = [(i, j) for i in range(n) for j in range(i + 1, n) if share[i, j]]
    di = [(i, j) for i in range(n) for j in range(i + 1, n) if not share[i, j]]
    icc = float(np.corrcoef([y[i] for i, j in sh], [y[j] for i, j in sh])[0, 1])
    print(f"\nP(same sign | share a component) = "
          f"{np.mean([y[i] == y[j] for i, j in sh]):.3f}  "
          f"vs {np.mean([y[i] == y[j] for i, j in di]):.3f} for component-disjoint "
          f"pairs;  ICC = {icc:+.3f}")
    print("The clustering is real and substantial. The question is how much it costs.")

    # ---- the estimators ---------------------------------------------------
    se_naive0 = sqrt(0.25 / n)
    se_naive1 = sqrt(ybar * (1 - ybar) / n)
    se_dy_mean = dyadic_se(y, share, ybar)
    se_dy_null = dyadic_se(y, share, 0.5)
    mbar = float(np.mean(list(deg.values())))
    deff_rs = 1 + (mbar - 1) * max(icc, 0.0)
    se_rs = se_naive0 * sqrt(deff_rs)

    rows = [
        ("naive binomial, null-imposed", se_naive0, se_naive0 / se_naive0),
        ("naive binomial, plug-in", se_naive1, (se_naive1 / se_naive1)),
        ("Rao-Scott design effect", se_rs, deff_rs),
        ("dyadic-robust (ASA), e = y - ybar", se_dy_mean,
         (se_dy_mean / se_naive1) ** 2),
        ("dyadic-robust (ASA), e = y - 0.5", se_dy_null,
         (se_dy_null / se_naive0) ** 2),
    ]
    print(f"\n{'estimator':<38}{'SE':>8}{'deff':>7}{'z':>8}{'p':>9}")
    table = []
    for lbl, se, deff in rows:
        z = (ybar - 0.5) / se
        print(f"{lbl:<38}{se:>8.4f}{deff:>7.2f}{z:>+8.2f}{z2p(z):>9.4f}")
        table.append({"estimator": lbl, "se": se, "deff": float(deff),
                      "z": float(z), "p": z2p(z)})
    ps = [r["p"] for r in table if r["estimator"].startswith(("Rao", "dyadic"))]
    print(f"\nClustered corrections span p = {min(ps):.3f} to {max(ps):.3f}. "
          f"The naive {binom_two_sided(k, n):.4f} is inflated by roughly "
          f"{min(ps)/binom_two_sided(k, n):.0f}-{max(ps)/binom_two_sided(k, n):.0f}x.")

    # ---- component-disjoint subsets, WITH the control the first pass lacked
    rng = random.Random(SEED)
    def subset_stats(constrain, target=None):
        ks, sizes = [], []
        for _ in range(args.subsets):
            order = pairs[:]
            rng.shuffle(order)
            if constrain:
                used, sub = set(), []
                for a, b, oe in order:
                    if a in used or b in used:
                        continue
                    used |= {a, b}
                    sub.append(oe)
            else:
                sub = [oe for _, _, oe in order[:target]]
            sizes.append(len(sub))
            ks.append(sum(v > 0 for v in sub))
        return np.array(ks), np.array(sizes)

    kk, ss = subset_stats(True)
    TARGET = int(np.median(ss))
    ku, su = subset_stats(False, TARGET)
    fr_d, fr_u = kk / ss, ku / su
    p_d = np.array([binom_two_sided(int(a), int(b)) for a, b in zip(kk, ss)])
    p_u = np.array([binom_two_sided(int(a), int(b)) for a, b in zip(ku, su)])
    mcse = lambda v: float(np.std(v) / sqrt(len(v)))
    print(f"\ncomponent-disjoint subsets vs size-matched UNCONSTRAINED subsets "
          f"(n = {TARGET}, {args.subsets} draws each):")
    print(f"{'':22}{'disjoint':>12}{'unconstrained':>15}")
    print(f"{'median positive frac':22}{np.median(fr_d):>12.3f}{np.median(fr_u):>15.3f}")
    print(f"{'median sign-test p':22}{np.median(p_d):>12.4f}{np.median(p_u):>15.4f}")
    print(f"{'frac majority-positive':22}{np.mean(fr_d>=0.5):>12.4f}"
          f"{np.mean(fr_u>=0.5):>15.4f}   (MC SE "
          f"{mcse(fr_d>=0.5):.4f} / {mcse(fr_u>=0.5):.4f})")
    print("The two columns are near-identical: dropping 45 of 60 observations, not\n"
          "removing dependence, is what drives these numbers. This analysis therefore\n"
          "says nothing about clustering and is reported only to retract the claim\n"
          "that it did.")

    out = {
        "pooled": {"positive": k, "n": n, "fraction": ybar,
                   "binomial_p": binom_two_sided(k, n)},
        "n_components": len(deg), "max_pairs_per_component": max(deg.values()),
        "mean_pairs_per_component": mbar,
        "icc": icc,
        "p_same_sign_sharing": float(np.mean([y[i] == y[j] for i, j in sh])),
        "p_same_sign_disjoint": float(np.mean([y[i] == y[j] for i, j in di])),
        "estimators": table,
        "clustered_p_range": [min(ps), max(ps)],
        "subsets": {
            "n_draws": args.subsets, "seed": SEED, "size": TARGET,
            "disjoint": {"median_fraction": float(np.median(fr_d)),
                         "median_sign_p": float(np.median(p_d)),
                         "frac_majority_positive": float(np.mean(fr_d >= 0.5)),
                         "mc_se": mcse(fr_d >= 0.5)},
            "unconstrained": {"median_fraction": float(np.median(fr_u)),
                              "median_sign_p": float(np.median(p_u)),
                              "frac_majority_positive": float(np.mean(fr_u >= 0.5)),
                              "mc_se": mcse(fr_u >= 0.5)},
        },
    }
    if args.calibrate:
        out["v1_calibration"] = calibrate(y, A, B)
        c = out["v1_calibration"]
        print(f"\nv1's `P(boot >= 0.5)` under an independent null ({c['n_sims']} sims): "
              f"median {c['median']:.3f}, min {c['min']:.3f} -- it is not a p-value; "
              f"the observed {c['observed_v1']} sits at calibrated p = {c['calibrated_p']:.4f}")
    (res / "pooled_independence.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {res / 'pooled_independence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
