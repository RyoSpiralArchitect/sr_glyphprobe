#!/usr/bin/env python3
"""OUT-OF-CONTRACT confirmatory test of the composition mean rule.

The rule, the six confirmatory families, the predicted values and the decision
rule were all fixed in ../PREREGISTRATION_mean_rule.md and committed before this
script existed. Nothing here may be tuned after seeing the outcome; the
predictions and thresholds below are copied from that file verbatim and are
checked against it at start-up.

Rule under test (fitted post-hoc on catchase_v2's 7 families):

    composite_mid_mean = 0.70 * mean(component_mid) + 1.16      residual sd 0.36

Decision (both must hold):

    Spearman(pred, obs) >= 0.70
    mean(|obs - pred|)  <= 0.72

Protocol is identical to why_flat.py / cat_chase*.py — same null seeds, targets,
alpha, wrappers and all 28 layers — so every number is comparable to those runs.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nullcache import NullCache  # noqa: E402

from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent
PREREG = ROOT / "PREREGISTRATION_mean_rule.md"

SLOPE, INTERCEPT, RESID_SD = 0.70, 1.16, 0.36
MIN_SPEARMAN, MAX_MAE = 0.70, 0.72

G = {
    "dog": "\U0001F436", "tea": "\U0001F375", "sailboat": "⛵",
    "thinking": "\U0001F914", "crying": "\U0001F622", "helicopter": "\U0001F681",
    "ship": "\U0001F6A2", "coffee": "☕", "car": "\U0001F697",
    "anchor": "⚓", "airplane": "✈️",
}

# solo mid ratios measured earlier on the identical protocol; the predictions in
# the pre-registration were computed from exactly these
PRIOR_SOLO = {"dog": 3.71, "tea": 4.59, "sailboat": 2.75, "thinking": 2.76,
              "crying": 4.22, "helicopter": 3.55, "ship": 3.72, "coffee": 2.87,
              "car": 5.66, "anchor": 2.99, "airplane": 3.05}

FAMILIES = [
    ("dogtea", "dog", "tea"),
    ("sailthink", "sailboat", "thinking"),
    ("cryheli", "crying", "helicopter"),
    ("shipcof", "ship", "coffee"),
    ("teacar", "tea", "car"),
    ("anchorair", "anchor", "airplane"),
]

WRAPPERS = ["Today I saw a", "My favorite thing is", "Here we have", "This reminds me of"]
TARGETS = {"paris": "The capital of France is",
           "planet": "The largest planet in our solar system is",
           "thinking": "I am thinking about"}

MK = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
          save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def cosv(a, b) -> float:
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="meanrule_v1")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    # ---- the predictions must match the committed pre-registration ---------
    pred = {f: SLOPE * ((PRIOR_SOLO[a] + PRIOR_SOLO[b]) / 2) + INTERCEPT
            for f, a, b in FAMILIES}
    text = PREREG.read_text(encoding="utf-8")
    mismatch = []
    # the pre-registered values are written to 2 dp, so allow a hair over half a
    # unit in the last place; 0.005 exactly is a knife edge that some families
    # land on (dogtea's 4.065 vs the printed 4.07 differs by 0.005 - 1e-16)
    TOL = 0.0051
    for f, _, _ in FAMILIES:
        m = re.search(rf"\|\s*{f}\s*\|.*?\|\s*\*\*([0-9.]+)\*\*\s*\|", text)
        if not m or abs(float(m.group(1)) - pred[f]) > TOL:
            mismatch.append((f, pred[f], m.group(1) if m else "absent"))
    # the thresholds decide the outcome, so they must be pinned to the committed
    # file as tightly as the predictions are — otherwise the half of the
    # pre-registration that matters could be loosened after seeing the result
    for label, value, pattern in (
            ("MIN_SPEARMAN", MIN_SPEARMAN, r"Spearman\(pred, obs\)\s*>=\s*([0-9.]+)"),
            ("MAX_MAE", MAX_MAE, r"mean\(\|obs - pred\|\)\s*<=\s*([0-9.]+)")):
        m = re.search(pattern, text)
        if not m or abs(float(m.group(1)) - value) > 1e-9:
            mismatch.append((label, value, m.group(1) if m else "absent"))
    for label, value, pattern in (
            ("SLOPE", SLOPE, r"composite_mid_mean\s*=\s*([0-9.]+)\s*\*"),
            ("INTERCEPT", INTERCEPT, r"mean\(component_mid\)\s*\+\s*([0-9.]+)")):
        m = re.search(pattern, text)
        if not m or abs(float(m.group(1)) - value) > 1e-9:
            mismatch.append((label, value, m.group(1) if m else "absent"))
    if mismatch:
        print("ABORT: this script's predictions do not match the committed "
              "pre-registration, so the test would not be confirmatory:",
              file=sys.stderr)
        for x in mismatch:
            print(f"  {x[0]}: computed {x[1]:.2f}, pre-registered {x[2]}", file=sys.stderr)
        return 2
    print("=" * 100)
    print("CONFIRMATORY TEST — composition mean rule")
    print("=" * 100)
    print(f"rule: composite = {SLOPE} * mean(components) + {INTERCEPT}  "
          f"(residual sd {RESID_SD})")
    print(f"pass requires Spearman >= {MIN_SPEARMAN} AND MAE <= {MAX_MAE}")
    print(f"all {len(FAMILIES)} predictions, both thresholds and both rule\n    coefficients verified against the committed pre-registration\n")

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    NL = be.num_layers
    layers = list(range(NL))
    print(f"device={getattr(be,'device',None)} num_layers={NL} model_dim={be.model_dim}")

    panel = [{"id": k, "glyph": v, "kind": "solo", "parts": []} for k, v in G.items()]
    for f, a, b in FAMILIES:
        panel.append({"id": f"{f}__{a}_{b}", "glyph": G[a] + G[b], "kind": "pair",
                      "family": f, "parts": [a, b]})
        panel.append({"id": f"{f}__{b}_{a}", "glyph": G[b] + G[a], "kind": "pair",
                      "family": f, "parts": [b, a]})

    tok = {k: [int(i) for i in be.tokenize(v).token_ids] for k, v in G.items()}
    bad = []
    for it in panel:
        ids = [int(i) for i in be.tokenize(it["glyph"]).token_ids]
        it["token_ids"] = ids
        it["n_tokens"] = len(ids)
        if it["parts"] and tok[it["parts"][0]] + tok[it["parts"][1]] != ids:
            bad.append(it["id"])
    if bad:
        print(f"ABORT: pairs do not tokenise as their parts concatenated: {bad}",
              file=sys.stderr)
        be.close()
        return 2
    print(f"compositional identity holds for all {len(FAMILIES)*2} pairs")

    def fwd(p, ls, iv=None):
        return be.forward(p, capture_layers=ls, site="resid_post",
                          position="last_nonpad", intervention=iv)

    wb = {}
    for w in WRAPPERS:
        r = fwd(w, layers)
        wb[w] = {L: np.asarray(r.activations[L], np.float64) for L in layers}
    tb = {}
    for n, p in TARGETS.items():
        r = fwd(p, layers)
        tb[n] = {"logits": r.logits,
                 "act": {L: np.asarray(r.activations[L], np.float64) for L in layers}}

    nc = NullCache(out, model_path=os.environ["SNAP"], alpha=A,
                   n=args.nulls, seed_formula="800000+100*L+s",
                   stack=NullCache.stack_fingerprint(cfg),
                   metric_kwargs=MK,
                   extra={"runner": "shared_v1"})
    print(f"building per-layer nulls ({len(layers)*len(TARGETS)} cells; "
          f"cache {nc.key}) ...", flush=True)
    null = {}
    for _i, L in enumerate(layers, 1):
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
                                         site="resid_post",
                                         position="last_nonpad", label="null"))
                    vals.append(distribution_metrics(tb[n]["logits"], r.logits,
                                                     **MK)["kl_base_to_intervened"])
                return vals
    
            null[(L, n)] = np.array(nc.get_or_build(
                layer=L, target_name=n, target_prompt=TARGETS[n], build=_build))
        print(f"  nulls: layer {L} done ({_i}/{len(layers)})", flush=True)
        nc.save()
    nc.save()

    rows, dirs, mid = [], {}, {}
    print(f"\n{'id':<22} {'glyph':<5} {'tok':>4} {'mid':>6} {'prior':>7} {'delta':>7}")
    for it in panel:
        per = {L: [] for L in layers}
        for w in WRAPPERS:
            r = fwd(f"{it['glyph']}\n{w}", layers)
            for L in layers:
                per[L].append(np.asarray(r.activations[L], np.float64) - wb[w][L])
        dirs[it["id"]] = {L: np.mean(per[L], axis=0) for L in layers}
        prof = []
        for L in layers:
            d = dirs[it["id"]][L]
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
                ratios.append(kl / max(np.median(null[(L, n)]), 1e-12))
            prof.append(float(np.mean(ratios)))
            rows.append({"id": it["id"], "glyph": it["glyph"], "kind": it["kind"],
                         "family": it.get("family"), "parts": it["parts"],
                         "layer": L, "alpha": A, "ratio_mean": prof[-1]})
        mid[it["id"]] = float(max(prof[10:20] or prof))
        it["mid"] = mid[it["id"]]
        pr = PRIOR_SOLO.get(it["id"])
        extra = (f"{pr:7.2f} {mid[it['id']]-pr:+7.2f}" if pr is not None else " " * 15)
        print(f"{it['id']:<22} {it['glyph']:<5} {it['n_tokens']:>4} "
              f"{mid[it['id']]:6.2f} {extra}")

    # ---- frame check (secondary, cannot rescue a failed primary) ----------
    drift = {k: mid[k] - PRIOR_SOLO[k] for k in PRIOR_SOLO}
    worst = max(drift.items(), key=lambda kv: abs(kv[1]))
    print(f"\nframe check — solo components vs their prior values: "
          f"max |drift| = {abs(worst[1]):.2f} on {worst[0]}")

    # ---- primary decision -------------------------------------------------
    print("\n" + "=" * 100)
    print("PRIMARY TEST")
    print("=" * 100)
    print(f"{'family':<11} {'mean(comp)':>11} {'predicted':>10} {'observed':>9} "
          f"{'error':>7} {'order eff':>10}")
    P, O, table = [], [], []
    for f, a, b in FAMILIES:
        ab, ba = mid[f"{f}__{a}_{b}"], mid[f"{f}__{b}_{a}"]
        obs = (ab + ba) / 2
        cmean = (PRIOR_SOLO[a] + PRIOR_SOLO[b]) / 2
        strong, weak = (a, b) if PRIOR_SOLO[a] >= PRIOR_SOLO[b] else (b, a)
        oeff = mid[f"{f}__{weak}_{strong}"] - mid[f"{f}__{strong}_{weak}"]
        P.append(pred[f]); O.append(obs)
        table.append({"family": f, "A": a, "B": b, "component_mean": cmean,
                      "predicted": pred[f], "observed": obs,
                      "error": obs - pred[f], "mid_AB": ab, "mid_BA": ba,
                      "order_effect": oeff})
        print(f"{f:<11} {cmean:11.2f} {pred[f]:10.2f} {obs:9.2f} "
              f"{obs-pred[f]:+7.2f} {oeff:+10.2f}")
    rho = spearman(P, O)
    mae = float(np.mean([abs(o - p) for o, p in zip(O, P)]))
    ok_rho, ok_mae = rho >= MIN_SPEARMAN, mae <= MAX_MAE
    passed = ok_rho and ok_mae
    print(f"\nSpearman(pred, obs) = {rho:+.3f}   (needs >= {MIN_SPEARMAN})  "
          f"{'PASS' if ok_rho else 'FAIL'}")
    print(f"MAE                 = {mae:.3f}    (needs <= {MAX_MAE})  "
          f"{'PASS' if ok_mae else 'FAIL'}")
    verdict = ("SUPPORTED" if passed else
               "ORDINAL ONLY" if ok_rho else "NOT SUPPORTED")
    print(f"\nPRE-REGISTERED VERDICT: {verdict}")

    # ---- secondary observations ------------------------------------------
    L16 = 16 if 16 < NL else NL - 1
    shifts = []
    for f, a, b in FAMILIES:
        ab, ba = f"{f}__{a}_{b}", f"{f}__{b}_{a}"
        for comp in (a, b):
            shifts.append(abs(cosv(dirs[ba][L16], dirs[comp][L16])
                              - cosv(dirs[ab][L16], dirs[comp][L16])))
    oeffs = [t["order_effect"] for t in table]
    print(f"\nsecondary: max |cosine shift| = {max(shifts):.3f}; "
          f"max |order effect| = {max(abs(e) for e in oeffs):.2f}")
    print(f"secondary: Spearman(component gap, order effect) = "
          f"{spearman([abs(PRIOR_SOLO[a]-PRIOR_SOLO[b]) for _, a, b in FAMILIES], oeffs):+.3f}")

    prof_path = out / f"{args.tag}_profiles.jsonl"
    prof_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"\nwrote {prof_path} ({len(rows)} rows)")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "preregistration": "PREREGISTRATION_mean_rule.md",
        "rule": {"slope": SLOPE, "intercept": INTERCEPT, "residual_sd": RESID_SD},
        "decision_rule": {"min_spearman": MIN_SPEARMAN, "max_mae": MAX_MAE},
        "families": table, "spearman_pred_obs": rho, "mae": mae,
        "verdict": verdict, "passed": bool(passed),
        "solo_observed": {k: mid[k] for k in G},
        "solo_prior": PRIOR_SOLO, "solo_drift": drift,
        "max_abs_cosine_shift": float(max(shifts)),
        "panel": panel, "alpha": A, "nulls": args.nulls, "num_layers": NL,
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
