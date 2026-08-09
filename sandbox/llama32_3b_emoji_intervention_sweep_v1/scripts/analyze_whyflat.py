#!/usr/bin/env python3
"""Analyse the why-flat follow-up.

Correction to the run script: its H1 verdict used the binary shape label
(mid-network max > final-layer value). That label is driven by the FINAL-layer
value, which varies for reasons unrelated to mid-network engagement — it
mislabels ☕ (mid 2.87, called MID-PEAK) and 🚢 (mid 3.72, called last-peak).
The quantity that actually answers "does this direction engage the middle of
the network" is the ABSOLUTE mid-network ratio, so everything here uses that.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
TAG = "whyflat_v1"

rows = [json.loads(l) for l in (res / f"{TAG}_phase2.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
name = [json.loads(l) for l in (res / f"{TAG}_phase1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
hyp = json.loads((res / f"{TAG}_hypotheses.json").read_text(encoding="utf-8"))
know = {r["id"]: r for r in name}

prof = defaultdict(dict)
info = {}
for r in rows:
    prof[r["id"]][r["layer"]] = r["ratio_mean"]
    info[r["id"]] = r
layers = sorted({r["layer"] for r in rows})


def rank(v):
    a = np.asarray(v, float); o = a.argsort(); rr = np.empty(len(a)); rr[o] = np.arange(1, len(a) + 1)
    for u in np.unique(a):
        m = a == u
        if m.sum() > 1:
            rr[m] = rr[m].mean()
    return rr


def sp(x, y):
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


rec = []
for gid, p in prof.items():
    seq = [p[L] for L in layers]
    rec.append({"id": gid, "glyph": info[gid]["glyph"], "grp": info[gid]["grp"],
                "sem": info[gid]["sem"], "pair": info[gid]["pair"],
                "utf8_lead": info[gid]["utf8_lead"], "n_tokens": info[gid]["n_tokens"],
                "mid": float(max(seq[10:20])), "last": float(seq[-1]),
                "peak_layer": int(np.argmax(seq)),
                "p_concept": know[gid]["p_concept_mean"]})
rec.sort(key=lambda r: r["mid"])

W = 96
print("=" * W)
print("WHY ARE SOME GLYPHS FLAT THROUGH THE MIDDLE? — corrected analysis")
print("=" * W)
print("Ranked by ABSOLUTE mid-network ratio (max over L10-19), the quantity that")
print("answers the question. The run script's binary shape label is shown for")
print("comparison — note where the two disagree.\n")
print(f"{'#':>3} {'g':<4} {'id':<11} {'cls':<4} {'sem':<9} {'mid':>6} {'last':>6} "
      f"{'peakL':>6} {'P(concept)':>11}  {'binary label':<12}")
for i, r in enumerate(rec, 1):
    lab = "MID-PEAK" if r["mid"] > r["last"] else "last-peak"
    flag = ""
    print(f"{i:>3} {r['glyph']:<4} {r['id']:<11} {r['grp']:<4} {r['sem']:<9} "
          f"{r['mid']:6.2f} {r['last']:6.2f} L{r['peak_layer']:<5} {r['p_concept']:11.4f}  {lab:<12}{flag}")

mids = [r["mid"] for r in rec]
gaps = [(mids[i + 1] - mids[i], i) for i in range(len(mids) - 1)]
gap, gi = max(gaps)
lo = rec[:gi + 1]
hi = rec[gi + 1:]
print(f"\nlargest gap in the sorted mid values: {mids[gi]:.2f} -> {mids[gi+1]:.2f} "
      f"(gap {gap:.2f}), splitting {len(lo)} low / {len(hi)} high")
print(f"  LOW  ({len(lo)}): " + " ".join(f"{r['glyph']}" for r in lo))
print(f"  HIGH ({len(hi)}): " + " ".join(f"{r['glyph']}" for r in hi))

print("\nbyte class vs that split:")
for grp in ("E2", "F0", "ZWJ"):
    l = [r for r in lo if r["grp"] == grp]
    h = [r for r in hi if r["grp"] == grp]
    print(f"  {grp:<4} low {len(l):>2} ({' '.join(r['glyph'] for r in l)})   "
          f"high {len(h):>2} ({' '.join(r['glyph'] for r in h)})")

is_e2 = [1 if r["grp"] == "E2" else 0 for r in rec]
print(f"\nSpearman(is 3-byte E2, mid ratio)   = {sp(is_e2, [r['mid'] for r in rec]):+.3f}")
print(f"Spearman(P(concept),  mid ratio)   = {sp([r['p_concept'] for r in rec], [r['mid'] for r in rec]):+.3f}")
print(f"Spearman(n_tokens,    mid ratio)   = {sp([r['n_tokens'] for r in rec], [r['mid'] for r in rec]):+.3f}")

print("\nH1 — near-synonym pairs, on the mid ratio (not the binary label):")
by_pair = defaultdict(list)
for r in rec:
    if r["pair"] != "-":
        by_pair[r["pair"]].append(r)
print(f"  {'pair':<8} {'E2':<22} {'F0':<22} {'F0/E2':>7}")
ratios = []
for pname, ms in by_pair.items():
    e2 = [m for m in ms if m["grp"] == "E2"]
    f0 = [m for m in ms if m["grp"] == "F0"]
    for a in e2:
        for b in f0:
            q = b["mid"] / a["mid"]
            ratios.append(q)
            print(f"  {pname:<8} {a['glyph']} {a['id']:<12}{a['mid']:5.2f}  "
                  f"{b['glyph']} {b['id']:<12}{b['mid']:5.2f}  {q:7.2f}"
                  f"{'  F0 higher' if q > 1.05 else '  ~equal' if q > 0.95 else '  E2 higher'}")
print(f"  median F0/E2 = {np.median(ratios):.2f}  ({sum(q>1.05 for q in ratios)}/{len(ratios)} pairs F0 higher)")

print("\nH2 — 🐈‍⬛ direction vs its parts (cosine, by layer):")
print(f"  {'layer':>5} {'cos to 🐈':>10} {'cos to ⬛':>10} {'margin':>8}")
for h in hyp["h2_zwj"]:
    print(f"  {h['layer']:>5} {h['cos_cat_plain']:10.3f} {h['cos_black_sq']:10.3f} "
          f"{h['cos_cat_plain']-h['cos_black_sq']:+8.3f}")
cats = {r["id"]: r["mid"] for r in rec if r["id"] in ("black_cat", "cat_plain", "cat_face", "black_sq")}
print(f"  but mid ratios:  🐈 {cats['cat_plain']:.2f}   🐱 {cats['cat_face']:.2f}   "
      f"🐈‍⬛ {cats['black_cat']:.2f}   ⬛ {cats['black_sq']:.2f}")

out = {"ranked": rec, "split": {"gap": gap, "low": [r["id"] for r in lo], "high": [r["id"] for r in hi]},
       "spearman_e2_mid": sp(is_e2, [r["mid"] for r in rec]),
       "spearman_pconcept_mid": sp([r["p_concept"] for r in rec], [r["mid"] for r in rec]),
       "spearman_ntokens_mid": sp([r["n_tokens"] for r in rec], [r["mid"] for r in rec]),
       "pair_ratios_median": float(np.median(ratios)),
       "h2_zwj": hyp["h2_zwj"]}
(res / f"{TAG}_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nwrote {res / f'{TAG}_analysis.json'}")
