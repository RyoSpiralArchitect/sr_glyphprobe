#!/usr/bin/env python3
"""Analyse the four deep-diagnostic phases.

Phase 1 asks the question sweep_v1 could not answer: the magnitude-controlled
effect was clean only on the one open-ended target — is that a property of
open-endedness (high baseline entropy / small top-2 margin) or was it that one
prompt? With 12 targets spanning entropy 1.1..5.6 and 256 nulls each, the
answer is a correlation, not a guess.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def rank(v):
    a = np.asarray(v, dtype=np.float64)
    o = a.argsort()
    r = np.empty(len(a))
    r[o] = np.arange(1, len(a) + 1)
    for u in np.unique(a):
        m = a == u
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x, y):
    if len(x) < 3:
        return float("nan")
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def load(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="deep_v1")
    ap.add_argument("--results", default=str(ROOT / "results"))
    args = ap.parse_args()
    res = Path(args.results)
    meta = json.loads((res / f"{args.tag}_meta.json").read_text(encoding="utf-8"))
    out = {"tag": args.tag}
    W = 100

    # ------------------------------------------------------------- PHASE 1
    p1 = res / f"{args.tag}_phase1.jsonl"
    if p1.exists():
        rows = load(p1)
        n_null = rows[0]["n_null"]
        print("=" * W)
        print(f"PHASE 1 — generalisation across {len({r['target'] for r in rows})} targets, "
              f"{n_null} random directions each")
        print("=" * W)

        by_t = defaultdict(list)
        for r in rows:
            by_t[r["target"]].append(r)
        glyphs = sorted({r["id"] for r in rows})
        n_g = len(glyphs)

        print(f"{'target':<11} {'entropy':>8} {'margin':>7} {'null med':>9} "
              f"{'ratio med':>10} {'clean':>7} {'min p':>8}")
        trow = []
        for t, rs in sorted(by_t.items(), key=lambda kv: -kv[1][0]["target_entropy"]):
            clean = sum(r["n_null_ge_observed"] == 0 for r in rs)
            ratios = [r["ratio_to_null_median"] for r in rs]
            trow.append({"target": t, "entropy": rs[0]["target_entropy"],
                         "margin": rs[0]["target_top2_margin"],
                         "null_median": rs[0]["null_median"],
                         "ratio_median": float(np.median(ratios)),
                         "clean": clean, "n_glyphs": len(rs),
                         "min_p": min(r["p_nonparametric"] for r in rs)})
            print(f"{t:<11} {rs[0]['target_entropy']:8.3f} {rs[0]['target_top2_margin']:7.3f} "
                  f"{rs[0]['null_median']:9.4f} {np.median(ratios):10.2f} "
                  f"{clean:>4}/{len(rs):<2} {min(r['p_nonparametric'] for r in rs):8.4f}")

        rho_ent = spearman([t["entropy"] for t in trow], [t["ratio_median"] for t in trow])
        rho_mar = spearman([t["margin"] for t in trow], [t["ratio_median"] for t in trow])
        rho_ent_c = spearman([t["entropy"] for t in trow], [t["clean"] for t in trow])
        print(f"\nSpearman(target entropy, ratio median) = {rho_ent:+.3f}")
        print(f"Spearman(top-2 margin,   ratio median) = {rho_mar:+.3f}")
        print(f"Spearman(target entropy, #clean glyphs) = {rho_ent_c:+.3f}")

        print(f"\nper glyph across all {len(by_t)} targets:")
        print(f"{'g':<3} {'id':<13} {'grp':<11} {'ratio med':>10} {'clean/12':>9} "
              f"{'min p':>8} {'flips':>6}")
        by_g = defaultdict(list)
        for r in rows:
            by_g[r["id"]].append(r)
        grow = []
        for gid, rs in sorted(by_g.items(), key=lambda kv: -np.median(
                [x["ratio_to_null_median"] for x in kv[1]])):
            clean = sum(r["n_null_ge_observed"] == 0 for r in rs)
            rm = float(np.median([r["ratio_to_null_median"] for r in rs]))
            mp = min(r["p_nonparametric"] for r in rs)
            grow.append({"id": gid, "glyph": rs[0]["glyph"], "group": rs[0]["group"],
                         "ratio_median": rm, "clean": clean, "n_targets": len(rs),
                         "min_p": mp,
                         "flips": sum(r["argmax_flip"] for r in rs)})
            print(f"{rs[0]['glyph']:<3} {gid:<13} {rs[0]['group']:<11} {rm:10.2f} "
                  f"{clean:>5}/{len(rs):<3} {mp:8.4f} {sum(r['argmax_flip'] for r in rs):>6}")

        strong = [g for g in grow if g["group"] in ("strong",)]
        weak = [g for g in grow if g["group"] == "weak"]
        print(f"\nstrong group ratio median = "
              f"{np.median([g['ratio_median'] for g in strong]):.2f}  "
              f"(clean {sum(g['clean'] for g in strong)}/{sum(g['n_targets'] for g in strong)})")
        print(f"weak   group ratio median = "
              f"{np.median([g['ratio_median'] for g in weak]):.2f}  "
              f"(clean {sum(g['clean'] for g in weak)}/{sum(g['n_targets'] for g in weak)})")
        out["phase1"] = {"targets": trow, "glyphs": grow,
                         "spearman_entropy_ratio": rho_ent,
                         "spearman_margin_ratio": rho_mar,
                         "spearman_entropy_clean": rho_ent_c,
                         "n_null": n_null}

    # ------------------------------------------------------------- PHASE 2
    p2 = res / f"{args.tag}_phase2.jsonl"
    if p2.exists():
        rows = load(p2)
        print("\n" + "=" * W)
        print("PHASE 2 — layer profile")
        print("=" * W)
        layers = sorted({r["layer"] for r in rows})
        by_g = defaultdict(dict)
        for r in rows:
            by_g[r["id"]][r["layer"]] = r
        print(f"{'g':<3} {'id':<13} {'grp':<11} {'peak L':>7} {'peak ratio':>11} "
              f"{'ratio@16':>9} {'cons@peak':>10}")
        prof = []
        for gid, d in by_g.items():
            rs = [d[L]["ratio_mean"] for L in layers]
            pk = layers[int(np.argmax(rs))]
            prof.append({"id": gid, "glyph": d[layers[0]]["glyph"],
                         "group": d[layers[0]]["group"],
                         "peak_layer": pk, "peak_ratio": float(max(rs)),
                         "ratio_at_16": float(d[16]["ratio_mean"]) if 16 in d else None,
                         "consistency_at_peak": d[pk]["direction_consistency"],
                         "profile": [float(x) for x in rs]})
            print(f"{d[layers[0]]['glyph']:<3} {gid:<13} {d[layers[0]]['group']:<11} "
                  f"{pk:>7} {max(rs):11.2f} "
                  f"{(d[16]['ratio_mean'] if 16 in d else float('nan')):9.2f} "
                  f"{d[pk]['direction_consistency']:10.3f}")
        pks = [p["peak_layer"] for p in prof]
        print(f"\npeak layer: median {int(np.median(pks))}, range {min(pks)}..{max(pks)}")
        cons = {L: float(np.median([by_g[g][L]["direction_consistency"] for g in by_g]))
                for L in layers}
        best = max(cons, key=cons.get)
        print(f"direction consistency peaks at L{best} ({cons[best]:.3f}); "
              f"L0={cons[layers[0]]:.3f} L{layers[-1]}={cons[layers[-1]]:.3f}")
        out["phase2"] = {"profiles": prof, "consistency_by_layer": cons,
                         "peak_layer_median": int(np.median(pks))}

    # ------------------------------------------------------------- PHASE 3
    p3 = res / f"{args.tag}_specificity_matrix.json"
    if p3.exists():
        m = json.loads(p3.read_text(encoding="utf-8"))
        print("\n" + "=" * W)
        print("PHASE 3 — specificity")
        print("=" * W)
        print(f"instance-level self-probe wins : {m['self_wins_instance_level']}/{m['n']}")
        print(f"category-block wins            : {m['own_block_wins']}/{m['n']}")
        print(f"sign-flip antisymmetry         : median {m['antisymmetry_median']:+.3f}, "
              f"min {m['antisymmetry_min']:+.3f}")
        out["phase3"] = {k: m[k] for k in
                         ("self_wins_instance_level", "own_block_wins", "n",
                          "antisymmetry_median", "antisymmetry_min")}

    # ------------------------------------------------------------- PHASE 4
    p4 = res / f"{args.tag}_phase4.jsonl"
    if p4.exists():
        rows = load(p4)
        print("\n" + "=" * W)
        print("PHASE 4 — direction estimate quality (4 -> 12 extraction wrappers)")
        print("=" * W)
        ks = sorted(rows[0]["consistency_by_n_wrappers"], key=int)
        print(f"{'g':<3} {'id':<13} " + " ".join(f"{'c@'+k:>7}" for k in ks) +
              f" {'ratio4':>8} {'ratio12':>8} {'gain':>7} {'cos(d4,d12)':>12}")
        gains = []
        for r in rows:
            g = r["ratio_12_wrappers"] - r["ratio_4_wrappers"]
            gains.append(g)
            print(f"{r['glyph']:<3} {r['id']:<13} " +
                  " ".join(f"{r['consistency_by_n_wrappers'][k]:7.3f}" for k in ks) +
                  f" {r['ratio_4_wrappers']:8.2f} {r['ratio_12_wrappers']:8.2f} "
                  f"{g:+7.2f} {r['cos_dir4_dir12']:12.3f}")
        cbyk = {k: float(np.median([r["consistency_by_n_wrappers"][k] for r in rows]))
                for k in ks}
        print(f"\nmedian consistency by #wrappers: " +
              "  ".join(f"{k}:{v:.3f}" for k, v in cbyk.items()))
        print(f"median ratio gain 4->12 wrappers: {np.median(gains):+.2f}")
        out["phase4"] = {"median_consistency_by_n_wrappers": cbyk,
                         "median_ratio_gain": float(np.median(gains)),
                         "rows": rows}

    (res / f"{args.tag}_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + "=" * W)
    print(f"wrote {res / f'{args.tag}_analysis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
