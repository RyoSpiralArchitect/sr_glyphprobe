#!/usr/bin/env python3
"""Aggregate the per-glyph intervention sweep into a ranking, and separate the
part of "介入量" that is a token-count artefact from the part that is not.

Reads  results/<tag>_records.jsonl + <tag>_meta.json
Writes results/<tag>_glyph_summary.jsonl, <tag>_summary.json, report.md
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def rank(values: list[float]) -> np.ndarray:
    """Average ranks, ties shared."""
    a = np.asarray(values, dtype=np.float64)
    order = a.argsort()
    r = np.empty(len(a), dtype=np.float64)
    r[order] = np.arange(1, len(a) + 1, dtype=np.float64)
    # average ties
    for v in np.unique(a):
        m = a == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x: list[float], y: list[float]) -> float:
    if len(x) < 3:
        return float("nan")
    rx, ry = rank(x), rank(y)
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    den = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / den) if den > 0 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="sweep_v1")
    ap.add_argument("--results", default=str(ROOT / "results"))
    args = ap.parse_args()

    res = Path(args.results)
    meta = json.loads((res / f"{args.tag}_meta.json").read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in (res / f"{args.tag}_records.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]

    layers = meta["layers"]
    alphas = meta["alphas"]
    pa = meta["primary_alpha"]
    targets = list(meta["inject_targets"])

    direction = defaultdict(dict)   # id -> layer -> row
    inject = defaultdict(lambda: defaultdict(dict))  # id -> (layer,target) -> alpha -> row
    info = {}
    for r in rows:
        if r["kind"] == "glyph_direction":
            direction[r["id"]][r["layer"]] = r
            info[r["id"]] = {k: r[k] for k in
                             ("glyph", "family", "stratum", "n_prefix_tokens")}
        elif r["kind"] == "glyph_injection":
            inject[r["id"]][(r["layer"], r["target"])][r["alpha"]] = r

    summary = []
    for gid, per_layer in direction.items():
        d0 = per_layer[layers[0]]
        rec = {"id": gid, **info[gid],
               "prompt_kl_mean": d0["prompt_kl_mean"],
               "prompt_kl_per_wrapper": d0["prompt_kl_per_wrapper"],
               "by_layer": {}}
        for L in layers:
            kl_pa, ratios, zs, mono, exceed = [], [], [], [], []
            for t in targets:
                cell = inject[gid][(L, t)]
                row_pa = cell[pa]
                kl_pa.append(row_pa["distribution"]["kl_base_to_intervened"])
                ratios.append(row_pa["null"]["ratio_to_null_median"])
                zs.append(row_pa["null"]["z"])
                exceed.append(row_pa["null"]["n_null_ge_observed"])
                seq = [cell[a]["distribution"]["kl_base_to_intervened"] for a in alphas]
                mono.append(all(x < y for x, y in zip(seq, seq[1:])))
            rec["by_layer"][str(L)] = {
                "direction_consistency": per_layer[L]["direction_consistency"],
                "direction_rms": per_layer[L]["direction_rms"],
                "prompt_rel_delta_mean": per_layer[L]["prompt_rel_delta_mean"],
                "injection_kl_mean": float(np.mean(kl_pa)),
                "injection_kl_per_target": dict(zip(targets, map(float, kl_pa))),
                "ratio_to_null_mean": float(np.mean(ratios)),
                "z_mean": float(np.mean(zs)),
                # nonparametric: how many of the N random-direction draws reached or
                # beat this glyph. 0 on every target is the only clean statement;
                # the null is right-skewed, so z is an effect size, NOT a p-value.
                "n_null_ge_observed_per_target": dict(zip(targets, map(int, exceed))),
                "max_exceedance_across_targets": int(max(exceed)),
                "clean_all_targets": bool(max(exceed) == 0),
                "dose_monotonic_all_targets": bool(all(mono)),
            }
        best_L = max(layers, key=lambda L: rec["by_layer"][str(L)]["ratio_to_null_mean"])
        rec["best_layer_by_ratio"] = best_L
        rec["best_ratio"] = rec["by_layer"][str(best_L)]["ratio_to_null_mean"]
        top = inject[gid][(layers[-1], targets[0])][pa]
        rec["top_boosted_deepest_layer"] = top["top_boosted"][:5]
        rec["top_suppressed_deepest_layer"] = top["top_suppressed"][:5]
        rec["argmax_flip_any"] = any(
            inject[gid][(L, t)][a]["distribution"]["argmax_flip"]
            for L in layers for t in targets for a in alphas)
        summary.append(rec)

    summary.sort(key=lambda r: -r["prompt_kl_mean"])

    matched = [r for r in summary if r["stratum"] == "matched"]
    ladder = [r for r in summary if r["stratum"] == "ladder"]
    allg = summary

    def col(rs, f):
        return [f(r) for r in rs]

    deepest = str(layers[-1])
    stats = {
        "n_glyphs": len(allg), "n_matched": len(matched), "n_ladder": len(ladder),
        "primary_alpha": pa, "layers": layers,
        "zero_hook_exact_noop": meta["zero_hook_exact_noop"],
        "dose_monotonic_fraction": float(np.mean([
            r["by_layer"][str(L)]["dose_monotonic_all_targets"]
            for r in allg for L in layers])),
        "spearman_tokens_vs_prompt_kl_all": spearman(
            col(allg, lambda r: r["n_prefix_tokens"]), col(allg, lambda r: r["prompt_kl_mean"])),
        "spearman_tokens_vs_ratio_all": spearman(
            col(allg, lambda r: r["n_prefix_tokens"]), col(allg, lambda r: r["best_ratio"])),
        "spearman_promptkl_vs_ratio_matched": spearman(
            col(matched, lambda r: r["prompt_kl_mean"]),
            col(matched, lambda r: r["best_ratio"])),
        "prompt_kl_matched": {
            "min": float(np.min(col(matched, lambda r: r["prompt_kl_mean"]))),
            "median": float(np.median(col(matched, lambda r: r["prompt_kl_mean"]))),
            "max": float(np.max(col(matched, lambda r: r["prompt_kl_mean"]))),
        },
        "ratio_to_null_by_layer": {
            str(L): {
                "matched_median": float(np.median(
                    col(matched, lambda r: r["by_layer"][str(L)]["ratio_to_null_mean"]))),
                "matched_frac_above_null_median": float(np.mean(
                    [r["by_layer"][str(L)]["ratio_to_null_mean"] > 1.0 for r in matched])),
                "consistency_median": float(np.median(
                    col(matched, lambda r: r["by_layer"][str(L)]["direction_consistency"]))),
                # the honest, nonparametric version
                "glyphs_clean_all_targets": int(sum(
                    r["by_layer"][str(L)]["clean_all_targets"] for r in allg)),
                "cells_zero_exceedance": int(sum(
                    v == 0 for r in allg
                    for v in r["by_layer"][str(L)]["n_null_ge_observed_per_target"].values())),
                "n_cells": len(allg) * len(targets),
                "cells_zero_exceedance_per_target": {
                    t: int(sum(r["by_layer"][str(L)]["n_null_ge_observed_per_target"][t] == 0
                               for r in allg)) for t in targets},
            } for L in layers},
        "family_medians_matched": {},
        "ladder_token_ladder": [
            {"glyph": r["glyph"], "id": r["id"], "tokens": r["n_prefix_tokens"],
             "prompt_kl": r["prompt_kl_mean"], "best_ratio": r["best_ratio"]}
            for r in sorted(ladder, key=lambda r: r["n_prefix_tokens"])],
    }
    fam = defaultdict(list)
    for r in matched:
        fam[r["family"]].append(r)
    for f, rs in sorted(fam.items()):
        stats["family_medians_matched"][f] = {
            "n": len(rs),
            "prompt_kl_median": float(np.median(col(rs, lambda r: r["prompt_kl_mean"]))),
            "ratio_median": float(np.median(col(rs, lambda r: r["best_ratio"]))),
        }

    with (res / f"{args.tag}_glyph_summary.jsonl").open("w", encoding="utf-8") as fh:
        for r in summary:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (res / f"{args.tag}_summary.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- console report -----------------------------------------------------
    w = 100
    print("=" * w)
    print("PER-GLYPH INTERVENTION SWEEP — ranking")
    print("=" * w)
    print(f"zero-hook exact no-op: {stats['zero_hook_exact_noop']}   "
          f"dose-monotonic cells: {stats['dose_monotonic_fraction']*100:.0f}%")
    print(f"Spearman(token count, prompt KL)  all glyphs = "
          f"{stats['spearman_tokens_vs_prompt_kl_all']:+.3f}")
    print(f"Spearman(token count, ratio-to-null) all      = "
          f"{stats['spearman_tokens_vs_ratio_all']:+.3f}")
    print(f"Spearman(prompt KL, ratio-to-null) matched    = "
          f"{stats['spearman_promptkl_vs_ratio_matched']:+.3f}")
    print("-" * w)

    print(f"\nA. TOKEN-MATCHED stratum ({len(matched)} glyphs, all exactly 4 prefix tokens)")
    print("   ranked by prompt-level KL — token count CANNOT explain this ordering")
    print(f"   {'#':>3} {'g':<3} {'id':<13} {'fam':<9} {'promptKL':>9} "
          f"{'ratioL'+deepest:>9} {'cons':>6}  top-boosted")
    for i, r in enumerate(matched, 1):
        b = r["by_layer"][deepest]
        top3 = " ".join(repr(t) for t, _ in r["top_boosted_deepest_layer"][:3])
        print(f"   {i:>3} {r['glyph']:<3} {r['id']:<13} {r['family']:<9} "
              f"{r['prompt_kl_mean']:9.4f} {b['ratio_to_null_mean']:9.2f} "
              f"{b['direction_consistency']:6.3f}  {top3}")

    print(f"\nB. same stratum re-ranked by MAGNITUDE-CONTROLLED push "
          f"(ratio to random-direction null, best layer, alpha={pa})")
    print(f"   {'#':>3} {'g':<3} {'id':<13} {'fam':<9} {'ratio':>7} {'layer':>5} "
          f"{'z':>7} {'promptKL':>9}")
    for i, r in enumerate(sorted(matched, key=lambda r: -r["best_ratio"]), 1):
        L = str(r["best_layer_by_ratio"])
        print(f"   {i:>3} {r['glyph']:<3} {r['id']:<13} {r['family']:<9} "
              f"{r['best_ratio']:7.2f} {L:>5} {r['by_layer'][L]['z_mean']:7.2f} "
              f"{r['prompt_kl_mean']:9.4f}")

    print(f"\nC. TOKEN LADDER — what token count alone buys ({len(ladder)} glyphs)")
    print(f"   {'g':<3} {'id':<13} {'tok':>4} {'promptKL':>9} {'ratio':>7}")
    for r in stats["ladder_token_ladder"]:
        rr = next(x for x in ladder if x["id"] == r["id"])
        print(f"   {rr['glyph']:<3} {r['id']:<13} {r['tokens']:>4} "
              f"{r['prompt_kl']:9.4f} {r['best_ratio']:7.2f}")

    print("\nD. by layer — ratio uses the null MEDIAN; exceedance is the nonparametric truth")
    print(f"   {'layer':>5} {'ratio med':>10} {'consist':>8} {'cells 0-exceed':>15} "
          f"{'clean all 3':>12}  per-target 0-exceed")
    for L in layers:
        s = stats["ratio_to_null_by_layer"][str(L)]
        per = " ".join(f"{t}={v}/{len(allg)}"
                       for t, v in s["cells_zero_exceedance_per_target"].items())
        print(f"   {L:>5} {s['matched_median']:10.2f} {s['consistency_median']:8.3f} "
              f"{s['cells_zero_exceedance']:>7}/{s['n_cells']:<7} "
              f"{s['glyphs_clean_all_targets']:>7}/{len(allg):<4}  {per}")
    print("   (a cell is '0-exceed' when none of the "
          f"{meta['random_controls']} random directions reached its KL;")
    print("    the null is right-skewed, so z is an effect size, not a p-value)")

    print("\nE. by family (token-matched stratum)")
    print(f"   {'family':<10} {'n':>3} {'promptKL med':>13} {'ratio med':>10}")
    for f, s in sorted(stats["family_medians_matched"].items(),
                       key=lambda kv: -kv[1]["prompt_kl_median"]):
        print(f"   {f:<10} {s['n']:>3} {s['prompt_kl_median']:13.4f} {s['ratio_median']:10.2f}")
    print("=" * w)
    print(f"wrote {res / f'{args.tag}_glyph_summary.jsonl'}")
    print(f"wrote {res / f'{args.tag}_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
