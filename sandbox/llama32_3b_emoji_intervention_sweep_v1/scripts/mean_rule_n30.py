#!/usr/bin/env python3
"""OUT-OF-CONTRACT confirmatory test of the composition mean rule at n = 30.

Everything that decides the outcome — the rule, both coefficients, both
thresholds, the component pool, the sampler seed and the additional statistics —
is fixed in ../PREREGISTRATION_mean_rule_n30.md and committed before this script
existed. The runner re-derives all of it and aborts on any mismatch.

    composite_mid_mean = 0.70 * mean(component_mid) + 1.16
    SUPPORTED requires  Spearman(pred, obs) >= 0.70  AND  MAE <= 0.72

Components are the repository's own e2_core35 panels (35 glyphs, every one
exactly 4 prefix tokens), and the 30 pairs are drawn by random.Random(20260809)
rejecting any component used more than twice — so neither the pool nor the
pairing is a choice of mine. Protocol matches every earlier run, so the null
cache carries over and the numbers stay comparable.

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
PREREG = ROOT / "PREREGISTRATION_mean_rule_n30.md"

SLOPE, INTERCEPT = 0.70, 1.16
MIN_SPEARMAN, MAX_MAE = 0.70, 0.72
PAIR_SEED, N_PAIRS, MAX_REUSE = 20260809, 30, 2

WRAPPERS = ["Today I saw a", "My favorite thing is", "Here we have", "This reminds me of"]
TARGETS = {"paris": "The capital of France is",
           "planet": "The largest planet in our solar system is",
           "thinking": "I am thinking about"}
LAYERS = list(range(10, 20))
MK = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
          save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def rank(v):
    a = np.asarray(v, float)
    o = a.argsort()
    r = np.empty(len(a))
    r[o] = np.arange(1, len(a) + 1)
    for u in np.unique(a):
        m = a == u
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(x, y):
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


def load_components():
    comps = []
    for f in sorted(glob.glob(str(REPO / "data/emoji_panels/e2_core35_*.yaml"))):
        fam = Path(f).stem.replace("e2_core35_", "")
        d = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
        for it in (d["items"] if isinstance(d, dict) else d):
            comps.append({"id": f"{fam}_{it['id']}", "glyph": it["glyph"], "family": fam})
    return comps


def sample_pairs(n_comp):
    rng = random.Random(PAIR_SEED)
    allp = [(i, j) for i in range(n_comp) for j in range(i + 1, n_comp)]
    rng.shuffle(allp)
    chosen, used = [], {}
    for i, j in allp:
        if len(chosen) >= N_PAIRS:
            break
        if used.get(i, 0) >= MAX_REUSE or used.get(j, 0) >= MAX_REUSE:
            continue
        chosen.append((i, j))
        used[i] = used.get(i, 0) + 1
        used[j] = used.get(j, 0) + 1
    return chosen


def check_prereg():
    """Everything that decides the outcome must match the committed file."""
    text = PREREG.read_text(encoding="utf-8")
    checks = [
        ("slope", SLOPE, r"composite_mid_mean\s*=\s*([0-9.]+)\s*\*"),
        ("intercept", INTERCEPT, r"mean\(component_mid\)\s*\+\s*([0-9.]+)"),
        ("min_spearman", MIN_SPEARMAN, r"Spearman\(pred, obs\)\s*>=\s*([0-9.]+)"),
        ("max_mae", MAX_MAE, r"mean\(\|obs - pred\|\)\s*<=\s*([0-9.]+)"),
        ("pair_seed", PAIR_SEED, r"random\.Random\((\d+)\)"),
        ("n_pairs", N_PAIRS, r"\*\*Pairs:\*\*\s*(\d+)"),
    ]
    bad = []
    for label, value, pat in checks:
        m = re.search(pat, text)
        if not m or abs(float(m.group(1)) - float(value)) > 1e-9:
            bad.append((label, value, m.group(1) if m else "absent"))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="meanrule30_v1")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / f"{args.tag}_summary.json").exists() and not args.overwrite:
        print(f"ABORT: {args.tag}_summary.json exists; pass --overwrite", file=sys.stderr)
        return 2
    A = args.alpha

    bad = check_prereg()
    if bad:
        print("ABORT: this script disagrees with the committed pre-registration, "
              "so the test would not be confirmatory:", file=sys.stderr)
        for x in bad:
            print(f"  {x[0]}: script {x[1]}, pre-registered {x[2]}", file=sys.stderr)
        return 2

    comps = load_components()
    pairs = sample_pairs(len(comps))
    print("=" * 100)
    print("CONFIRMATORY TEST — composition mean rule at n = 30")
    print("=" * 100)
    print(f"rule: composite = {SLOPE} * mean(components) + {INTERCEPT}   "
          f"pass requires Spearman >= {MIN_SPEARMAN} AND MAE <= {MAX_MAE}")
    print(f"pool: {len(comps)} glyphs from the repo's e2_core35 panels; "
          f"{len(pairs)} pairs from random.Random({PAIR_SEED})")
    print("rule, thresholds, seed and pair count all verified against the "
          "committed pre-registration\n")

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    print(f"device={getattr(be,'device',None)} num_layers={be.num_layers} "
          f"model_dim={be.model_dim}")

    panel = [dict(c, kind="solo", parts=[]) for c in comps]
    for i, j in pairs:
        a, b = comps[i], comps[j]
        for x, y in ((a, b), (b, a)):
            panel.append({"id": f"{x['id']}+{y['id']}", "glyph": x["glyph"] + y["glyph"],
                          "kind": "pair", "parts": [x["id"], y["id"]]})

    tok = {}
    n_pref = {}
    wl = {w: len(be.tokenize(w).token_ids) for w in WRAPPERS}
    for c in comps:
        tok[c["id"]] = [int(t) for t in be.tokenize(c["glyph"]).token_ids]
        n_pref[c["id"]] = {w: len(be.tokenize(f"{c['glyph']}\n{w}").token_ids) - wl[w]
                           for w in WRAPPERS}
    bad_tok = [c["id"] for c in comps if len(set(n_pref[c["id"]].values())) != 1
               or next(iter(n_pref[c["id"]].values())) != 4]
    bad_cat = [it["id"] for it in panel if it["parts"]
               and tok[it["parts"][0]] + tok[it["parts"][1]]
               != [int(t) for t in be.tokenize(it["glyph"]).token_ids]]
    if bad_tok or bad_cat:
        print(f"ABORT: token check failed. not-4-tokens={bad_tok} "
              f"non-decomposing={bad_cat}", file=sys.stderr)
        be.close()
        return 2
    print(f"all {len(comps)} components are exactly 4 prefix tokens on every wrapper; "
          f"all {len(pairs)*2} concatenations decompose")

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
        print(f"  nulls: layer {L} done", flush=True)

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
        rows.append({"id": it["id"], "glyph": it["glyph"], "kind": it["kind"],
                     "parts": it["parts"], "mid": mid[it["id"]], "profile": prof})
        if idx % 10 == 0 or idx == len(panel):
            print(f"  {idx}/{len(panel)} glyphs", flush=True)

    # ---- primary test -----------------------------------------------------
    P, O, table = [], [], []
    for i, j in pairs:
        a, b = comps[i]["id"], comps[j]["id"]
        cm = (mid[a] + mid[b]) / 2
        pred = SLOPE * cm + INTERCEPT
        ab, ba = mid[f"{a}+{b}"], mid[f"{b}+{a}"]
        obs = (ab + ba) / 2
        strong, weak = (a, b) if mid[a] >= mid[b] else (b, a)
        P.append(pred)
        O.append(obs)
        table.append({"A": a, "B": b, "glyphs": comps[i]["glyph"] + comps[j]["glyph"],
                      "mid_A": mid[a], "mid_B": mid[b], "component_mean": cm,
                      "predicted": pred, "observed": obs, "error": obs - pred,
                      "mid_AB": ab, "mid_BA": ba,
                      "order_effect": mid[f"{weak}+{strong}"] - mid[f"{strong}+{weak}"],
                      "same_family": comps[i]["family"] == comps[j]["family"]})
    rho = spearman(P, O)
    mae = float(np.mean([abs(o - p) for o, p in zip(O, P)]))
    ok_rho, ok_mae = rho >= MIN_SPEARMAN, mae <= MAX_MAE
    verdict = ("SUPPORTED" if ok_rho and ok_mae
               else "ORDINAL ONLY" if ok_rho else "NOT SUPPORTED")

    print(f"\n{'pair':<10} {'mean':>6} {'pred':>6} {'obs':>6} {'err':>7} {'order':>7}")
    for t in sorted(table, key=lambda t: t["component_mean"]):
        print(f"{t['glyphs']:<10} {t['component_mean']:6.2f} {t['predicted']:6.2f} "
              f"{t['observed']:6.2f} {t['error']:+7.2f} {t['order_effect']:+7.2f}")
    print(f"\nSpearman(pred, obs) = {rho:+.3f}  (needs >= {MIN_SPEARMAN})  "
          f"{'PASS' if ok_rho else 'FAIL'}")
    print(f"MAE                 = {mae:.3f}   (needs <= {MAX_MAE})  "
          f"{'PASS' if ok_mae else 'FAIL'}")
    print(f"\nPRE-REGISTERED VERDICT: {verdict}")

    # ---- pre-specified additional statistics ------------------------------
    rng = np.random.default_rng(11)
    perm = sum(1 for _ in range(10000)
               if spearman(list(rng.permutation(P)), O) >= rho)
    p_perm = (perm + 1) / 10001
    boots = []
    n = len(P)
    for _ in range(10000):
        idx = rng.integers(0, n, n)
        boots.append(spearman([P[k] for k in idx], [O[k] for k in idx]))
    lo, hi = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))
    fit_slope, fit_int = np.polyfit([t["component_mean"] for t in table], O, 1)
    oeff = [t["order_effect"] for t in table]
    same = [t for t in table if t["same_family"]]
    diff = [t for t in table if not t["same_family"]]
    print(f"\npermutation p (one-sided, 10k)   = {p_perm:.4f}")
    print(f"bootstrap 95% CI on Spearman     = [{lo:+.3f}, {hi:+.3f}]")
    print(f"refit (comparison only)          = {fit_slope:.2f} * mean + {fit_int:.2f}  "
          f"(frozen rule: {SLOPE} / {INTERCEPT})")
    print(f"order effect positive            = {sum(e > 0 for e in oeff)}/{len(oeff)} "
          f"(chance {len(oeff)/2:.1f}); median {np.median(oeff):+.2f}")
    if same:
        print(f"residual, same-family pairs      = {np.median([t['error'] for t in same]):+.2f} "
              f"(n={len(same)})")
    print(f"residual, cross-family pairs     = {np.median([t['error'] for t in diff]):+.2f} "
          f"(n={len(diff)})")

    (out / f"{args.tag}_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "preregistration": "PREREGISTRATION_mean_rule_n30.md",
        "rule": {"slope": SLOPE, "intercept": INTERCEPT},
        "decision_rule": {"min_spearman": MIN_SPEARMAN, "max_mae": MAX_MAE},
        "pair_seed": PAIR_SEED, "n_pairs": len(pairs),
        "component_pool": [c["id"] for c in comps],
        "pairs": table, "spearman_pred_obs": rho, "mae": mae,
        "verdict": verdict, "passed": bool(ok_rho and ok_mae),
        "permutation_p": p_perm, "bootstrap_ci": [lo, hi],
        "refit_slope": float(fit_slope), "refit_intercept": float(fit_int),
        "order_effect_positive": int(sum(e > 0 for e in oeff)),
        "order_effect_median": float(np.median(oeff)),
        "residual_same_family_median": (float(np.median([t["error"] for t in same]))
                                        if same else None),
        "residual_cross_family_median": float(np.median([t["error"] for t in diff])),
        "solo_mid": {c["id"]: mid[c["id"]] for c in comps},
        "alpha": A, "nulls": args.nulls, "layers": LAYERS,
        "null_cache": nc.report(),
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
