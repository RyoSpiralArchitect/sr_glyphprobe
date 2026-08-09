#!/usr/bin/env python3
"""OUT-OF-CONTRACT: is the 🍕⬛ sign reversal a phenomenon or a coincidence?

`catchase_v2` found one family whose order effect ran the other way: 🍕⬛ scored
4.94 and ⬛🍕 scored 4.00, an order effect of −0.94 where six of the other seven
families were positive. The obvious next move is to explain it. This run checks
first whether there is anything to explain.

Why not just change the null seed. The injection KL is fully deterministic — no
RNG touches it — and the null only enters as the denominator, shared by both
orders of a pair at a given (layer, target). Re-seeding therefore rescales an
order effect but can barely flip its sign. It is not an independent sample of
the phenomenon.

The two places genuine sampling variability enters are the direction estimate
and the readout, so those are what this varies:

    wrapper set A / B   4 disjoint contexts each -> independent estimates of d_g
    target set  A / B   3 injection prompts each -> independent readouts

2 x 2 = four conditions, and each is a fresh estimate of the same order effect.
Four pairs are measured, all of the same shape as the anomaly (a strong concrete
glyph combined with a featureless square), so a sibling pattern would show up:

    🍕 / ⬛   the original anomaly
    🍔 / ⬛   another strong food + the same square
    🚗 / ⬛   a strong vehicle + the same square
    🍕 / ⬜   the same pizza + a different square

STATED BEFORE RUNNING: I expect the sign NOT to be stable across the four
conditions. The order effect has already flipped its correlation with the
component gap (+0.04 -> −0.94) and its own sign (6/7 -> 2/6) between samples, so
the most likely reading of the −0.94 is that it is one draw from a noisy
quantity, not a mechanism. If instead the sign holds in all four conditions and
the siblings agree, that prediction is wrong and there is something to chase.

Only layers 10-19 are computed: `mid` is defined as the maximum over exactly
that band, so the rest of the profile is not needed and the run stays short.
Null seeds match the earlier runs.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np

from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent

G = {"pizza": "\U0001F355", "burger": "\U0001F354", "car": "\U0001F697",
     "black_sq": "⬛", "white_sq": "⬜"}

PAIRS = [
    ("pizsq", "pizza", "black_sq"),      # the anomaly
    ("bursq", "burger", "black_sq"),     # sibling: another strong food
    ("carsq", "car", "black_sq"),        # sibling: a strong vehicle
    ("pizwht", "pizza", "white_sq"),     # sibling: the same food, other square
]

WRAPPER_SETS = {
    "A": ["Today I saw a", "My favorite thing is", "Here we have", "This reminds me of"],
    "B": ["Look at this", "I just found a", "There was a", "Everyone loves a"],
}
TARGET_SETS = {
    "A": {"paris": "The capital of France is",
          "planet": "The largest planet in our solar system is",
          "thinking": "I am thinking about"},
    "B": {"summer": "The best thing about summer is",
          "tell": "Let me tell you about",
          "gold": "The chemical symbol for gold is"},
}

LAYERS = list(range(10, 20))          # `mid` is the max over exactly this band
MK = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
          save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="orderstab_v1")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    panel = [{"id": k, "glyph": v, "parts": []} for k, v in G.items()]
    for name, a, b in PAIRS:
        panel.append({"id": f"{name}__{a}_{b}", "glyph": G[a] + G[b], "parts": [a, b]})
        panel.append({"id": f"{name}__{b}_{a}", "glyph": G[b] + G[a], "parts": [b, a]})

    print("=" * 100)
    print("OUT-OF-CONTRACT — is the 🍕⬛ order-effect sign reversal stable?")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 100)
    print(f"{len(panel)} glyphs, layers {LAYERS[0]}-{LAYERS[-1]}, "
          f"{len(WRAPPER_SETS)} wrapper sets x {len(TARGET_SETS)} target sets = "
          f"{len(WRAPPER_SETS)*len(TARGET_SETS)} conditions")
    print("PREDICTION STATED BEFORE THE RUN: the sign will NOT be stable.\n")

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    print(f"device={getattr(be,'device',None)} num_layers={be.num_layers} "
          f"model_dim={be.model_dim}")

    tok = {k: [int(i) for i in be.tokenize(v).token_ids] for k, v in G.items()}
    bad = [it["id"] for it in panel if it["parts"]
           and tok[it["parts"][0]] + tok[it["parts"][1]]
           != [int(i) for i in be.tokenize(it["glyph"]).token_ids]]
    if bad:
        print(f"ABORT: pairs do not tokenise as their parts concatenated: {bad}",
              file=sys.stderr)
        be.close()
        return 2
    print(f"compositional identity holds for all {len(PAIRS)*2} pairs")

    def fwd(p, ls, iv=None):
        return be.forward(p, capture_layers=ls, site="resid_post",
                          position="last_nonpad", intervention=iv)

    # ---- directions: one per (glyph, wrapper set) --------------------------
    wbase = {}
    for ws, wraps in WRAPPER_SETS.items():
        for w in wraps:
            r = fwd(w, LAYERS)
            wbase[w] = {L: np.asarray(r.activations[L], np.float64) for L in LAYERS}
    dirs = {}
    for it in panel:
        for ws, wraps in WRAPPER_SETS.items():
            per = {L: [] for L in LAYERS}
            for w in wraps:
                r = fwd(f"{it['glyph']}\n{w}", LAYERS)
                for L in LAYERS:
                    per[L].append(np.asarray(r.activations[L], np.float64) - wbase[w][L])
            dirs[(it["id"], ws)] = {L: np.mean(per[L], axis=0) for L in LAYERS}
    print(f"extracted {len(dirs)} directions "
          f"({len(panel)} glyphs x {len(WRAPPER_SETS)} wrapper sets)")

    # ---- baselines and nulls: one per (target set, target) -----------------
    tb, null = {}, {}
    for ts, tgts in TARGET_SETS.items():
        for n, p in tgts.items():
            r = fwd(p, LAYERS)
            tb[(ts, n)] = {"logits": r.logits,
                           "act": {L: np.asarray(r.activations[L], np.float64)
                                   for L in LAYERS}}
    print(f"building nulls ({args.nulls} per layer x target, "
          f"{len(LAYERS)*sum(len(t) for t in TARGET_SETS.values())} cells) ...")
    for ts, tgts in TARGET_SETS.items():
        for n, p in tgts.items():
            for L in LAYERS:
                trms = rms(tb[(ts, n)]["act"][L])
                vals = []
                for s in range(args.nulls):
                    rng = np.random.default_rng(800_000 + 100 * L + s)
                    d = rng.standard_normal(be.model_dim)
                    v = d / rms(d) * A * trms
                    r = fwd(p, [L], Intervention(layer=L, vector=v.astype(np.float32),
                                                 site="resid_post",
                                                 position="last_nonpad", label="null"))
                    vals.append(distribution_metrics(tb[(ts, n)]["logits"], r.logits,
                                                    **MK)["kl_base_to_intervened"])
                null[(ts, n, L)] = float(np.median(vals))

    # ---- mid ratio per (glyph, wrapper set, target set) --------------------
    mid, rows = {}, []
    for it in panel:
        for ws in WRAPPER_SETS:
            for ts, tgts in TARGET_SETS.items():
                prof = []
                for L in LAYERS:
                    d = dirs[(it["id"], ws)][L]
                    drms = rms(d)
                    ratios = []
                    for n, p in tgts.items():
                        trms = rms(tb[(ts, n)]["act"][L])
                        v = d / max(drms, 1e-12) * A * trms
                        r = fwd(p, [L], Intervention(layer=L, vector=v.astype(np.float32),
                                                     site="resid_post",
                                                     position="last_nonpad",
                                                     label=f"{it['id']}_{L}_{n}"))
                        kl = distribution_metrics(tb[(ts, n)]["logits"], r.logits,
                                                  **MK)["kl_base_to_intervened"]
                        ratios.append(kl / max(null[(ts, n, L)], 1e-12))
                    prof.append(float(np.mean(ratios)))
                mid[(it["id"], ws, ts)] = float(max(prof))
                rows.append({"id": it["id"], "glyph": it["glyph"], "parts": it["parts"],
                             "wrapper_set": ws, "target_set": ts,
                             "mid": mid[(it["id"], ws, ts)],
                             "profile": prof, "layers": LAYERS})

    conds = [(ws, ts) for ws in WRAPPER_SETS for ts in TARGET_SETS]
    print(f"\n{'glyph':<22} " + " ".join(f"{'W'+ws+'/T'+ts:>8}" for ws, ts in conds))
    for it in panel:
        print(f"{it['id']:<22} " +
              " ".join(f"{mid[(it['id'], ws, ts)]:8.2f}" for ws, ts in conds))

    # ---- the question -----------------------------------------------------
    print("\n" + "=" * 100)
    print("ORDER EFFECT (ends on stronger − ends on weaker) PER CONDITION")
    print("=" * 100)
    print(f"{'pair':<9} {'strong':<10} {'weak':<10} " +
          " ".join(f"{'W'+ws+'/T'+ts:>9}" for ws, ts in conds) + f" {'signs':>7}")
    table = []
    for name, a, b in PAIRS:
        effs = []
        for ws, ts in conds:
            sa, sb = mid[(a, ws, ts)], mid[(b, ws, ts)]
            strong, weak = (a, b) if sa >= sb else (b, a)
            effs.append(mid[(f"{name}__{weak}_{strong}", ws, ts)]
                        - mid[(f"{name}__{strong}_{weak}", ws, ts)])
        npos = sum(e > 0 for e in effs)
        stable = npos in (0, len(effs))
        table.append({"pair": name, "A": a, "B": b,
                      "order_effects": dict(zip([f"W{w}/T{t}" for w, t in conds], effs)),
                      "n_positive": npos, "n_conditions": len(effs),
                      "sign_stable": bool(stable),
                      "range": float(max(effs) - min(effs))})
        print(f"{name:<9} {a:<10} {b:<10} " + " ".join(f"{e:+9.2f}" for e in effs) +
              f" {npos}/{len(effs)}" + ("  STABLE" if stable else "  FLIPS"))

    n_stable = sum(t["sign_stable"] for t in table)
    print(f"\npairs whose order-effect sign is stable across all "
          f"{len(conds)} conditions: **{n_stable}/{len(table)}**")
    piz = next(t for t in table if t["pair"] == "pizsq")
    print(f"the original anomaly (pizsq): {piz['n_positive']}/{piz['n_conditions']} "
          f"positive, spread {piz['range']:.2f} "
          f"-> {'sign holds' if piz['sign_stable'] else 'SIGN DOES NOT HOLD'}")
    print(f"\nPREDICTION WAS: the sign will NOT be stable.  "
          f"OUTCOME: {'prediction wrong, signs are stable' if n_stable == len(table) else 'prediction held for at least one pair'}")

    (out / f"{args.tag}_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "stated_prediction": "the order-effect sign will NOT be stable across conditions",
        "pairs": PAIRS, "wrapper_sets": WRAPPER_SETS, "target_sets": TARGET_SETS,
        "layers": LAYERS, "alpha": A, "nulls": args.nulls,
        "mid": {f"{k[0]}|W{k[1]}|T{k[2]}": v for k, v in mid.items()},
        "order_effect_table": table, "n_sign_stable": int(n_stable),
        "n_pairs": len(table),
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_profiles.jsonl'} ({len(rows)} rows)")
    print(f"wrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
