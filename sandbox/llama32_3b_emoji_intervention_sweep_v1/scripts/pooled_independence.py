#!/usr/bin/env python3
"""Component clustering breaks every binomial test in this series, including the
pre-registered one.

The sign tests here treat pairs as independent Bernoulli trials. They are not:
each pair is a **dyad** over two components, components recur across pairs, both
samples come from one 35-glyph pool, and strong/weak in every sample is assigned
from a single measurement of `solo_mid`. Two pairs sharing a component covary.

The estimator for a mean of dyadic observations is the dyadic-robust variance
(Aronow-Samii-Assenova): two dyads covary iff they share a vertex,

    V(ybar) = (1/n^2) * sum_ij  1{i,j share a component} * e_i e_j

and for testing H0: p = 0.5 the residual must be **null-imposed**, e = y - 0.5.
That is not a stylistic choice, it is the difference between a valid test and an
invalid one: with e = y - ybar the same deviation that drives the numerator also
deflates the denominator, and `--simulate` shows it rejecting ~10 % of the time
at a nominal 5 % **under an independent null**. The null-imposed version sits at
nominal size.

This file has been wrong twice, in opposite directions, and both are recorded
rather than deleted:

  v1  led with `P(bootstrap fraction >= 0.5) = 0.054` and concluded the pooled
      p-value "does not survive". Its weights were `cnt[A]*cnt[B]` where the
      comment claimed an indicator -- a real defect. But its *number* was close
      to right, and the argument later used to retract it was wrong (see
      `--forensics`).
  v2  answered with a range, `p ~ 0.011-0.063`, spanning three estimators. Two
      of the three are mis-specified: the Rao-Scott multiplier assumed each
      observation sits in one cluster when each dyad sits in two, and the
      mean-centred dyadic row is the invalid test above. Presenting a range was
      not even-handedness, it was averaging a valid estimator with two broken
      ones.

Runs off committed JSON; no model required.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from math import comb, erfc, sqrt
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
SAMPLES = {"primary (this run)": ["orderrev_v1"],
           "prior (meanrule30)": ["meanrule30_v1"],
           "pooled": ["meanrule30_v1", "orderrev_v1"]}


def z2p(z: float) -> float:
    return float(erfc(abs(z) / sqrt(2.0)))


def t2p(z: float, df: int) -> float:
    """Two-sided Student-t tail, integrated directly to avoid a scipy dependency."""
    x = np.linspace(abs(z), abs(z) + 60.0, 300001)
    from math import lgamma, log, pi
    logc = lgamma((df + 1) / 2) - lgamma(df / 2) - 0.5 * log(df * pi)
    dens = np.exp(logc - (df + 1) / 2 * np.log1p(x ** 2 / df))
    return float(2 * np.trapezoid(dens, x)) if hasattr(np, "trapezoid") \
        else float(2 * np.trapz(dens, x))


def binom_two_sided(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return float(sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)
                     if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12)))


def load(tags):
    out = []
    for tag in tags:
        s = json.loads((res / f"{tag}_summary.json").read_text(encoding="utf-8"))
        for t in s["pairs"]:
            out.append((t["A"], t["B"], float(t["order_effect"])))
    return out


def share_matrix(A, B):
    n = len(A)
    return np.array([[len({A[i], B[i]} & {A[j], B[j]}) > 0 for j in range(n)]
                     for i in range(n)])


def dyadic_var(y, share, center):
    """ASA dyadic-robust variance of the mean. The quadratic form is not PSD, so
    a negative estimate is possible and is reported rather than square-rooted."""
    e = y - center
    return float((e[:, None] * e[None, :] * share).sum() / len(y) ** 2)


def analyse(pairs):
    A = [a for a, b, _ in pairs]
    B = [b for a, b, _ in pairs]
    y = np.array([oe > 0 for _, _, oe in pairs], float)
    n = len(y)
    ybar = float(y.mean())
    k = int(y.sum())
    share = share_matrix(A, B)
    G = len(set(A) | set(B))
    kbar = float((share.sum() - n) / n)          # mean OTHER dyads sharing a vertex
    sh = [(i, j) for i in range(n) for j in range(i + 1, n) if share[i, j]]
    di = [(i, j) for i in range(n) for j in range(i + 1, n) if not share[i, j]]
    icc = float(np.corrcoef([y[i] for i, j in sh], [y[j] for i, j in sh])[0, 1])

    v_null = dyadic_var(y, share, 0.5)
    v_mean = dyadic_var(y, share, ybar)
    se = sqrt(v_null) if v_null > 0 else float("nan")
    z = (ybar - 0.5) / se if se == se and se > 0 else float("nan")
    naive = binom_two_sided(k, n)
    return {
        "k": k, "n": n, "fraction": ybar, "n_components": G,
        "mean_other_dyads_sharing": kbar, "icc": icc,
        "p_same_sign_sharing": float(np.mean([y[i] == y[j] for i, j in sh])),
        "p_same_sign_disjoint": float(np.mean([y[i] == y[j] for i, j in di])),
        "naive_binomial_p": naive,
        "dyadic_se": se, "dyadic_z": z,
        "dyadic_p_z": z2p(z), "dyadic_p_t": t2p(z, G - 1), "t_df": G - 1,
        "design_effect": float(v_null / (0.25 / n)),
        "inflation_vs_naive": float(z2p(z) / naive),
        "variance_negative": v_null <= 0,
        "mean_centred_se_FOR_REFERENCE_ONLY": sqrt(v_mean) if v_mean > 0 else None,
    }


def simulate(pairs, sd, n_sims, seed=3):
    """Actual size of each candidate test, under a vertex-random-effects null."""
    A = [a for a, b, _ in pairs]
    B = [b for a, b, _ in pairs]
    n = len(A)
    share = share_matrix(A, B)
    comps = sorted(set(A) | set(B))
    ci = {c: i for i, c in enumerate(comps)}
    ia = np.array([ci[a] for a in A])
    ib = np.array([ci[b] for b in B])
    deg = Counter(A) + Counter(B)
    mbar = float(np.mean(list(deg.values())))
    kbar = float((share.sum() - n) / n)
    rng = np.random.default_rng(seed)
    hits = Counter()
    iccs = []
    for _ in range(n_sims):
        u = rng.normal(0, sd, len(comps))
        y = (rng.random(n) < 1 / (1 + np.exp(-(u[ia] + u[ib])))).astype(float)
        yb = y.mean()
        sh = [(i, j) for i in range(n) for j in range(i + 1, n) if share[i, j]]
        v1 = np.array([y[i] for i, j in sh])
        v2 = np.array([y[j] for i, j in sh])
        icc = 0.0 if v1.std() == 0 or v2.std() == 0 else float(np.corrcoef(v1, v2)[0, 1])
        iccs.append(icc)
        se0 = sqrt(0.25 / n)
        vm = dyadic_var(y, share, yb)
        vn = dyadic_var(y, share, 0.5)
        cands = {
            "naive exact binomial": None,
            "Rao-Scott, (mbar-1) [v2]": se0 * sqrt(1 + (mbar - 1) * max(icc, 0)),
            "Rao-Scott, Kbar": se0 * sqrt(1 + kbar * max(icc, 0)),
            "dyadic, e = y - ybar [v2]": sqrt(vm) if vm > 0 else None,
            "dyadic, e = y - 0.5": sqrt(vn) if vn > 0 else None,
        }
        if binom_two_sided(int(y.sum()), n) < 0.05:
            hits["naive exact binomial"] += 1
        for lbl, se in cands.items():
            if se:
                if z2p((yb - 0.5) / se) < 0.05:
                    hits[lbl] += 1
    return {k: v / n_sims for k, v in hits.items()}, float(np.mean(iccs))


def forensics(pairs, n_sims, n_boot, seed=11):
    """v1's bootstrap statistic, under the null it should have been judged against."""
    A = [a for a, b, _ in pairs]
    B = [b for a, b, _ in pairs]
    n = len(A)
    comps = sorted(set(A) | set(B))
    ci = {c: i for i, c in enumerate(comps)}
    ia = np.array([ci[a] for a in A])
    ib = np.array([ci[b] for b in B])
    rng = np.random.default_rng(seed)

    def stat(yv):
        out = []
        for _ in range(n_boot):
            cnt = np.bincount(rng.integers(0, len(comps), len(comps)),
                              minlength=len(comps))
            w = cnt[ia] * cnt[ib]
            if w.sum():
                out.append((w * yv).sum() / w.sum())
        return float(np.mean(np.array(out) >= 0.5))

    out = {}
    for sd, lbl in ((0.0, "independent"), (1.15, "clustered")):
        null = []
        for _ in range(n_sims):
            u = rng.normal(0, sd, len(comps))
            y = (rng.random(n) < 1 / (1 + np.exp(-(u[ia] + u[ib])))).astype(float)
            null.append(stat(y))
        null = np.array(null)
        out[lbl] = {"n_sims": n_sims, "median": float(np.median(null)),
                    "min": float(null.min()),
                    "p_le_v1": float(np.mean(null <= 0.0539))}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", type=int, default=0,
                    help="size simulation with this many draws per null (e.g. 4000)")
    ap.add_argument("--forensics", type=int, default=0,
                    help="re-judge v1's statistic against N draws of each null")
    args = ap.parse_args()

    out = {"samples": {}}
    print(f"{'sample':<22}{'k/n':>8}{'naive p':>10}{'ICC':>7}{'Kbar':>6}"
          f"{'deff':>7}{'dyadic p (z)':>14}{'(t)':>8}")
    for lbl, tags in SAMPLES.items():
        r = analyse(load(tags))
        out["samples"][lbl] = r
        print(f"{lbl:<22}{f'{r['k']}/{r['n']}':>8}{r['naive_binomial_p']:>10.4f}"
              f"{r['icc']:>+7.3f}{r['mean_other_dyads_sharing']:>6.2f}"
              f"{r['design_effect']:>7.2f}{r['dyadic_p_z']:>14.4f}{r['dyadic_p_t']:>8.4f}")

    pool = out["samples"]["pooled"]
    print(f"\nPooled: P(same sign | share a component) = "
          f"{pool['p_same_sign_sharing']:.3f} vs "
          f"{pool['p_same_sign_disjoint']:.3f} disjoint, ICC {pool['icc']:+.3f}.")
    print("Under the dyadic-robust test NO sample in this series clears 0.05, and all")
    print("three point the same way. The direction is consistent; the significance was")
    print(f"an artefact of treating dyads as independent (inflation "
          f"{min(r['inflation_vs_naive'] for r in out['samples'].values()):.0f}-"
          f"{max(r['inflation_vs_naive'] for r in out['samples'].values()):.0f}x).")

    if args.simulate:
        print(f"\nactual size at nominal 0.05 ({args.simulate} draws per null):")
        out["size_simulation"] = {}
        hdr = None
        for sd, lbl in ((0.0, "independent"), (1.15, "clustered")):
            rej, icc = simulate(load(SAMPLES["pooled"]), sd, args.simulate)
            out["size_simulation"][lbl] = {"sd": sd, "mean_icc": icc, "rejection": rej}
            if hdr is None:
                hdr = list(rej)
                print(f"{'null':<14}{'ICC':>6}" + "".join(f"{h[:26]:>28}" for h in hdr))
            print(f"{lbl:<14}{icc:>6.2f}" + "".join(f"{rej[h]:>28.3f}" for h in hdr))
        print("-> only `dyadic, e = y - 0.5` holds its nominal size under both nulls.")

    if args.forensics:
        out["v1_forensics"] = forensics(load(SAMPLES["pooled"]), args.forensics, 1200)
        print(f"\nv1's `P(boot >= 0.5)`, re-judged ({args.forensics} draws per null):")
        for lbl, d in out["v1_forensics"].items():
            print(f"  {lbl:<12} median {d['median']:.3f}  min {d['min']:.4f}  "
                  f"P(<= 0.0539) = {d['p_le_v1']:.4f}")
        print("-> v2 called this 'not a p-value' because its median was ~0.5. A valid")
        print("   one-sided p-value HAS median 0.5; that argument was wrong. v1's real")
        print("   defect was the weighting, and its number was close to right.")

    (res / "pooled_independence.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwrote {res / 'pooled_independence.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
