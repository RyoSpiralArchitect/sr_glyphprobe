#!/usr/bin/env python3
"""OUT-OF-CONTRACT replication of the order-effect reversal found at n = 30.

The n=30 run reported 8/30 pairs positive (chance 15, binomial p = 0.016): ending
on the STRONGER component scores LOWER. That is the first sample in this series
with enough units for the sign to mean anything, and the same quantity has read
6/7, 2/6 and 8/30 on this protocol — so it is tested on a fresh draw before
anything is built on it.

Everything that decides the outcome is fixed in
../PREREGISTRATION_order_reversal.md and committed before this script existed;
the runner re-derives it and aborts on any mismatch.

  primary   30 NEW pairs, seed 20260810, excluding every pair already measured
            REPLICATED requires  positive < 15  AND  binomial two-sided p < 0.05
  secondary MAE of the frozen rule (0.70/1.16) vs the meanrule30 refit
            (0.62/1.86) on these fresh pairs — comparison only, and explicitly
            barred from rescuing the primary verdict

Solo component values are reused from meanrule30_v1_summary.json: they are
deterministic under an identical protocol with a cached null. Five are
re-measured as a frame check and the run aborts if any drifts past 0.01.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys
import warnings
from math import comb
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nullcache import NullCache  # noqa: E402

from glyphprobe.analysis.metrics import distribution_metrics  # noqa: E402
from glyphprobe.backends.registry import create_backend  # noqa: E402
from glyphprobe.config import BackendConfig  # noqa: E402
from glyphprobe.records import Intervention  # noqa: E402

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
PREREG = ROOT / "PREREGISTRATION_order_reversal.md"
PRIOR = ROOT / "results" / "meanrule30_v1_summary.json"

PAIR_SEED, N_PAIRS, MAX_REUSE = 20260810, 30, 2
FROZEN = (0.70, 1.16)
REFIT = (0.62, 1.86)
FRAME_CHECK = ["animals_1", "food_4", "sky_2", "social_6", "transport_3"]
FRAME_TOL = 0.01
MAX_POSITIVE, ALPHA_LEVEL = 15, 0.05

WRAPPERS = ["Today I saw a", "My favorite thing is", "Here we have", "This reminds me of"]
TARGETS = {"paris": "The capital of France is",
           "planet": "The largest planet in our solar system is",
           "thinking": "I am thinking about"}
LAYERS = list(range(10, 20))
MK = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
          save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def binom_two_sided(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return float(sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(n + 1)
                     if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12)))


def load_components():
    comps = []
    for f in sorted(glob.glob(str(REPO / "data/emoji_panels/e2_core35_*.yaml"))):
        fam = Path(f).stem.replace("e2_core35_", "")
        d = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
        for it in (d["items"] if isinstance(d, dict) else d):
            comps.append({"id": f"{fam}_{it['id']}", "glyph": it["glyph"], "family": fam})
    return comps


def sample_pairs(ids, exclude):
    """Same procedure as before, new seed, and never a pair already measured."""
    rng = random.Random(PAIR_SEED)
    allp = [(i, j) for i in range(len(ids)) for j in range(i + 1, len(ids))]
    rng.shuffle(allp)
    chosen, used = [], {}
    for i, j in allp:
        if len(chosen) >= N_PAIRS:
            break
        if frozenset((ids[i], ids[j])) in exclude:
            continue
        if used.get(i, 0) >= MAX_REUSE or used.get(j, 0) >= MAX_REUSE:
            continue
        chosen.append((i, j))
        used[i] = used.get(i, 0) + 1
        used[j] = used.get(j, 0) + 1
    return chosen


def resolve_frame_check(comps):
    """`<family>_<k>` -> the k-th component of that family, 1-indexed, sorted.

    Amendment 1 to the pre-registration: the five names were written from memory
    and match no component id. The map below is total and has no free choices,
    and `check_prereg` verifies it against the committed amendment table.
    """
    fams = {}
    for c in comps:
        fams.setdefault(c["family"], []).append(c["id"])
    out = {}
    for short in FRAME_CHECK:
        fam, _, k = short.rpartition("_")
        ids = fams.get(fam, [])
        if not k.isdigit() or not 1 <= int(k) <= len(ids):
            raise SystemExit(f"ABORT: frame-check name {short!r} does not resolve")
        out[short] = ids[int(k) - 1]
    return out


def check_prereg(args, n_comp, resolved=None, solo=None):
    text = PREREG.read_text(encoding="utf-8")
    words = {"twice": 2, "once": 1}
    checks = [
        ("pair_seed", PAIR_SEED, r"random\.Random\((\d+)\)"),
        ("n_pairs", N_PAIRS, r"\*\*Pairs:\*\*\s*(\d+)"),
        ("max_reuse", MAX_REUSE, r"reuse cap of (\w+)"),
        ("max_positive", MAX_POSITIVE, r"fewer than (\d+) of 30 positive"),
        ("alpha_level", ALPHA_LEVEL, r"binomial two-sided p < ([0-9.]+)"),
        ("frame_tol", FRAME_TOL, r"more than ([0-9.]+) the run aborts"),
        ("frozen_slope", FROZEN[0], r"frozen: `([0-9.]+) × mean"),
        ("frozen_int", FROZEN[1], r"frozen: `[0-9.]+ × mean \+ ([0-9.]+)"),
        ("refit_slope", REFIT[0], r"refit from meanrule30: `([0-9.]+) × mean"),
        ("refit_int", REFIT[1], r"refit from meanrule30: `[0-9.]+ × mean \+ ([0-9.]+)"),
        ("alpha", args.alpha, r"α\s*=\s*([0-9.]+)"),
        ("nulls", args.nulls, r"([0-9]+)\s*\n?\s*random directions per \(layer, target\)"),
        ("n_components", n_comp, r"all (\d+) glyphs"),
        ("layer_lo", LAYERS[0], r"layers (\d+)-\d+"),
        ("layer_hi", LAYERS[-1], r"layers \d+-(\d+)"),
    ]
    bad = []
    for label, value, pat in checks:
        m = re.search(pat, text)
        got = None
        if m:
            raw = m.group(1)
            got = float(words[raw]) if raw in words else (
                float(raw) if re.fullmatch(r"[0-9.]+", raw) else None)
        if got is None or abs(got - float(value)) > 1e-9:
            bad.append((label, value, m.group(1) if m else "absent"))

    # the frame-check names, and the amendment's resolution of them
    names = re.search(r"frame check\*\*\s*\n?\s*\((`[^)]+`)\)", text)
    listed = re.findall(r"`([a-z]+_\d+)`", names.group(1)) if names else []
    if listed != FRAME_CHECK:
        bad.append(("frame_check_names", FRAME_CHECK, listed or "absent"))
    if resolved is not None:
        table = dict(re.findall(r"\|\s*`([a-z]+_\d+)`\s*\|\s*`(\S+)`\s*\|", text))
        for short, real in resolved.items():
            if table.get(short) != real:
                bad.append((f"amendment:{short}", real, table.get(short, "absent")))
        if solo is not None:
            for short, real in resolved.items():
                m2 = re.search(rf"\|\s*`{short}`\s*\|\s*`{re.escape(real)}`\s*\|"
                               r"\s*([0-9.]+)\s*\|", text)
                if not m2 or abs(float(m2.group(1)) - solo[real]) > 5e-4:
                    bad.append((f"amendment_mid:{short}", round(solo[real], 4),
                                m2.group(1) if m2 else "absent"))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="orderrev_v1")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / f"{args.tag}_summary.json").exists() and not args.overwrite:
        print(f"ABORT: {args.tag}_summary.json exists; pass --overwrite", file=sys.stderr)
        return 2
    A = args.alpha

    comps = load_components()
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    solo = dict(prior["solo_mid"])
    frame = resolve_frame_check(comps)
    bad = check_prereg(args, len(comps), resolved=frame, solo=solo)
    if bad:
        print("ABORT: this script disagrees with the committed pre-registration:",
              file=sys.stderr)
        for x in bad:
            print(f"  {x[0]}: script {x[1]}, pre-registered {x[2]}", file=sys.stderr)
        return 2

    seen = {frozenset((p["A"], p["B"])) for p in prior["pairs"]}
    ids = [c["id"] for c in comps]
    by_id = {c["id"]: c for c in comps}
    pairs = sample_pairs(ids, seen)
    if len(pairs) != N_PAIRS:
        print(f"ABORT: sampler produced {len(pairs)} pairs, pre-registered {N_PAIRS}",
              file=sys.stderr)
        return 2
    overlap = sum(1 for i, j in pairs if frozenset((ids[i], ids[j])) in seen)
    print("=" * 100)
    print("REPLICATION — does the order-effect reversal hold on fresh pairs?")
    print("=" * 100)
    print(f"prior sample: {prior['order_effect_positive']}/{prior['n_pairs']} positive, "
          f"median {prior['order_effect_median']:+.2f}")
    print(f"REPLICATED requires positive < {MAX_POSITIVE} AND binomial p < {ALPHA_LEVEL}")
    print(f"{len(pairs)} new pairs from random.Random({PAIR_SEED}); "
          f"overlap with the prior sample: {overlap} (must be 0)")
    print("all pre-registered constants verified against the committed file\n")
    if overlap:
        print("ABORT: pairs overlap the prior sample", file=sys.stderr)
        return 2

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    print(f"device={getattr(be,'device',None)} num_layers={be.num_layers}")

    panel = [{"id": f"{ids[x]}+{ids[y]}",
              "glyph": by_id[ids[x]]["glyph"] + by_id[ids[y]]["glyph"],
              "parts": [ids[x], ids[y]]}
             for i, j in pairs for x, y in ((i, j), (j, i))]
    panel += [{"id": f"CHECK::{short}", "glyph": by_id[real]["glyph"], "parts": []}
              for short, real in frame.items()]

    if len({it["id"] for it in panel}) != len(panel):
        print("ABORT: duplicate panel ids -- both orders would collapse onto one key",
              file=sys.stderr)
        be.close()
        return 2

    tokmap = {c["id"]: [int(t) for t in be.tokenize(c["glyph"]).token_ids] for c in comps}
    bad_cat = [it["id"] for it in panel if it["parts"]
               and tokmap[it["parts"][0]] + tokmap[it["parts"][1]]
               != [int(t) for t in be.tokenize(it["glyph"]).token_ids]]
    if bad_cat:
        print(f"ABORT: non-decomposing concatenations: {bad_cat}", file=sys.stderr)
        be.close()
        return 2
    print(f"all {len(pairs)*2} concatenations decompose")

    def fwd(p, ls, iv=None):
        return be.forward(p, capture_layers=ls, site="resid_post",
                          position="last_nonpad", intervention=iv)

    wb = {}
    for w in WRAPPERS:
        r = fwd(w, LAYERS)
        wb[w] = {L: np.asarray(r.activations[L], np.float64) for L in LAYERS}
    tb = {}
    for n, p in TARGETS.items():
        r = fwd(p, LAYERS)
        tb[n] = {"logits": r.logits,
                 "act": {L: np.asarray(r.activations[L], np.float64) for L in LAYERS}}

    nc = NullCache(out, model_path=os.environ["SNAP"], alpha=A, n=args.nulls,
                   seed_formula="800000+100*L+s",
                   stack=NullCache.stack_fingerprint(cfg), metric_kwargs=MK,
                   extra={"runner": "shared_v1"})
    print(f"\nnulls ({len(LAYERS)*len(TARGETS)} cells; cache {nc.key}) ...", flush=True)
    null = {}
    for L in LAYERS:
        for n in TARGETS:
            trms = rms(tb[n]["act"][L])

            def _build(L=L, n=n, trms=trms):
                vals = []
                for k in range(args.nulls):
                    rng = np.random.default_rng(800_000 + 100 * L + k)
                    d = rng.standard_normal(be.model_dim)
                    v = d / rms(d) * A * trms
                    r = fwd(TARGETS[n], [L],
                            Intervention(layer=L, vector=v.astype(np.float32),
                                         site="resid_post", position="last_nonpad",
                                         label="null"))
                    vals.append(distribution_metrics(tb[n]["logits"], r.logits,
                                                     **MK)["kl_base_to_intervened"])
                return vals

            null[(L, n)] = float(np.median(nc.get_or_build(
                layer=L, target_name=n, target_prompt=TARGETS[n], build=_build)))
        nc.save()
    print(f"  {nc.hits} hit / {nc.misses} miss", flush=True)

    mid, rows = {}, []
    print(f"\nmeasuring {len(panel)} glyphs ...", flush=True)
    for idx, it in enumerate(panel, 1):
        per = {L: [] for L in LAYERS}
        for w in WRAPPERS:
            r = fwd(f"{it['glyph']}\n{w}", LAYERS)
            for L in LAYERS:
                per[L].append(np.asarray(r.activations[L], np.float64) - wb[w][L])
        prof = []
        for L in LAYERS:
            d = np.mean(per[L], axis=0)
            drms = rms(d)
            ratios = []
            for n in TARGETS:
                trms = rms(tb[n]["act"][L])
                v = d / max(drms, 1e-12) * A * trms
                r = fwd(TARGETS[n], [L],
                        Intervention(layer=L, vector=v.astype(np.float32),
                                     site="resid_post", position="last_nonpad",
                                     label=f"{it['id']}_L{L}_{n}"))
                kl = distribution_metrics(tb[n]["logits"], r.logits,
                                          **MK)["kl_base_to_intervened"]
                ratios.append(kl / max(null[(L, n)], 1e-12))
            prof.append(float(np.mean(ratios)))
        mid[it["id"]] = float(max(prof))
        rows.append({"id": it["id"], "glyph": it["glyph"], "parts": it["parts"],
                     "mid": mid[it["id"]]})
        if idx % 10 == 0 or idx == len(panel):
            print(f"  {idx}/{len(panel)}", flush=True)

    # ---- frame check: reused solo values must still be the same -----------
    drift = {s_: mid[f"CHECK::{s_}"] - solo[r_] for s_, r_ in frame.items()}
    worst = max(abs(v) for v in drift.values())
    print(f"\nframe check (5 re-measured components): max |drift| = {worst:.4f} "
          f"(tolerance {FRAME_TOL})")
    for s_, d in drift.items():
        print(f"  {s_:<12} = {frame[s_]:<28} recorded {solo[frame[s_]]:.4f}  "
              f"now {mid[f'CHECK::{s_}']:.4f}  {d:+.4f}")
    if worst > FRAME_TOL:
        print("ABORT: reused solo values are not in the same frame; nothing reported.",
              file=sys.stderr)
        be.close()
        return 2

    # ---- primary ----------------------------------------------------------
    table = []
    for i, j in pairs:
        a, b = ids[i], ids[j]
        strong, weak = (a, b) if solo[a] >= solo[b] else (b, a)
        oe = mid[f"{weak}+{strong}"] - mid[f"{strong}+{weak}"]
        cm = (solo[a] + solo[b]) / 2
        obs = (mid[f"{a}+{b}"] + mid[f"{b}+{a}"]) / 2
        table.append({"A": a, "B": b, "glyphs": by_id[a]["glyph"] + by_id[b]["glyph"],
                      "strong": strong, "weak": weak, "component_mean": cm,
                      "observed": obs, "order_effect": oe,
                      "err_frozen": obs - (FROZEN[0] * cm + FROZEN[1]),
                      "err_refit": obs - (REFIT[0] * cm + REFIT[1])})
    k = sum(t["order_effect"] > 0 for t in table)
    n = len(table)
    p_bin = binom_two_sided(k, n)
    verdict = ("REPLICATED" if k < MAX_POSITIVE and p_bin < ALPHA_LEVEL
               else "SAME DIRECTION, NOT SIGNIFICANT" if k < MAX_POSITIVE
               else "NOT REPLICATED")
    med = float(np.median([t["order_effect"] for t in table]))
    print(f"\n{'pair':<9} {'strong':<14} {'order effect':>13}")
    for t in sorted(table, key=lambda t: t["order_effect"]):
        print(f"{t['glyphs']:<9} {t['strong']:<14} {t['order_effect']:+13.2f}")
    print(f"\npositive: {k}/{n} (chance {n/2:.0f})   median {med:+.2f}   "
          f"binomial two-sided p = {p_bin:.4f}")
    print(f"prior sample: {prior['order_effect_positive']}/{prior['n_pairs']}, "
          f"median {prior['order_effect_median']:+.2f}")
    kp = k + prior["order_effect_positive"]
    npool = n + prior["n_pairs"]
    print(f"pooled:   {kp}/{npool}   binomial two-sided p = "
          f"{binom_two_sided(kp, npool):.6f}")
    print(f"\nPRE-REGISTERED VERDICT: {verdict}")

    # ---- secondary (comparison only) --------------------------------------
    mae_f = float(np.mean([abs(t["err_frozen"]) for t in table]))
    mae_r = float(np.mean([abs(t["err_refit"]) for t in table]))
    print(f"\nsecondary, comparison only — MAE on these fresh pairs:")
    print(f"  frozen {FROZEN[0]}/{FROZEN[1]}: {mae_f:.3f}")
    print(f"  refit  {REFIT[0]}/{REFIT[1]}: {mae_r:.3f}   "
          f"-> {'refit generalises' if mae_r < mae_f else 'refit does NOT generalise'}")

    (out / f"{args.tag}_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "preregistration": "PREREGISTRATION_order_reversal.md",
        "pair_seed": PAIR_SEED, "n_pairs": n, "overlap_with_prior": overlap,
        "decision_rule": {"max_positive": MAX_POSITIVE, "alpha": ALPHA_LEVEL},
        "pairs": table, "order_effect_positive": k, "order_effect_median": med,
        "binomial_p": p_bin, "verdict": verdict,
        "prior": {"positive": prior["order_effect_positive"], "n": prior["n_pairs"],
                  "median": prior["order_effect_median"]},
        "pooled": {"positive": kp, "n": npool, "binomial_p": binom_two_sided(kp, npool)},
        "frame_check": {"tolerance": FRAME_TOL, "max_abs_drift": worst, "drift": drift,
                        "resolved": frame},
        "secondary_mae": {"frozen": mae_f, "refit": mae_r,
                          "frozen_coeffs": list(FROZEN), "refit_coeffs": list(REFIT)},
        "alpha": A, "nulls": args.nulls, "layers": LAYERS,
        "null_cache": nc.report(),
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
