#!/usr/bin/env python3
"""OUT-OF-CONTRACT: is the order effect systematic, and does the DIRECTION move
with it?

cat_chase.py established two things and broke one of its own metrics.

  established  the ZWJ joiner is not what costs the compound its efficacy:
               removing it leaves 🐈⬛ at 3.31, nowhere near 🐈's 3.96. (The
               joiner is not *nothing* — it moves the value by 0.006 to 0.215,
               the same size as effects treated as signal elsewhere — it just
               cannot explain the gap this run is chasing.)
  established  ORDER moves the efficacy when the two components differ
               (🐈⬛ 3.31 -> ⬛🐈 3.61) and not when they are alike
               (🧑🚀 2.87 -> 🚀🧑 2.88)
  broken       its "direction follows FIRST/LAST" column compared cos-to-first
               against cos-to-last. Those labels swap when the order swaps, so
               the column flips even when the geometry does not. Re-expressed in
               a FIXED frame, cos(composite, 🐈) is 0.944 / 0.944 / 0.949 / 0.944
               across all four cat composites — the direction barely moves while
               the efficacy moves 16%.

So this run does two things.

1. SYSTEMATIC TEST. Seven two-component families whose component gap spans
   0.01 .. 2.50, each in both orders, all bare concatenations (the joiner is
   settled, so dropping it doubles the usable n per family). If the order effect
   is real and graded, it should grow with the gap; the twin family 🐈/🐱
   (gap 0.01) is the control that must show no effect.

2. FIXED-FRAME GEOMETRY. Every cosine is reported against a NAMED component, so
   nothing depends on positional labels, and the order-sensitivity of the
   direction is measured directly as cos(A-then-B, X) - cos(B-then-A, X) for the
   same X.

Every solo component is re-measured in-run rather than carried over, so the
whole comparison lives in one frame. Null seeds match why_flat.py and
cat_chase.py, so the numbers stay comparable to both.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nullcache import NullCache  # noqa: E402

from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent

G = {
    "cat": "\U0001F408", "cat_face": "\U0001F431", "black_sq": "⬛",
    "pizza": "\U0001F355", "car": "\U0001F697", "woman": "\U0001F469",
    "laptop": "\U0001F4BB", "person": "\U0001F9D1", "rocket": "\U0001F680",
}

# (family, component A, component B) — both orders are built from these
FAMILIES = [
    ("twin",   "cat",   "cat_face"),   # gap ~0.01  -> the control
    ("astro",  "person", "rocket"),    # gap ~0.13
    ("pizcar", "pizza", "car"),        # gap ~0.34
    ("catsq",  "cat",   "black_sq"),   # gap ~0.96  (reproduces cat_chase v1)
    ("tech",   "woman", "laptop"),     # gap ~1.12  <- the missing third point
    ("pizsq",  "pizza", "black_sq"),   # gap ~2.32
    ("carlap", "car",   "laptop"),     # gap ~2.50
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
    if len(x) < 3:
        return float("nan")
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="catchase_v2")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    panel = [{"id": k, "glyph": v, "kind": "solo", "parts": []} for k, v in G.items()]
    for fam, a, b in FAMILIES:
        panel.append({"id": f"{fam}__{a}_{b}", "glyph": G[a] + G[b],
                      "kind": "pair", "family": fam, "parts": [a, b]})
        panel.append({"id": f"{fam}__{b}_{a}", "glyph": G[b] + G[a],
                      "kind": "pair", "family": fam, "parts": [b, a]})

    print("=" * 104)
    print("OUT-OF-CONTRACT — is the composition order effect systematic?")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 104)
    print(f"{len(panel)} glyphs = {len(G)} solo components + "
          f"{len(FAMILIES)} families x 2 orders")

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    NL = be.num_layers
    layers = list(range(NL))
    print(f"device={getattr(be,'device',None)} num_layers={NL} model_dim={be.model_dim}")

    # composition must be exact, or the whole argument dissolves
    tok = {k: [int(i) for i in be.tokenize(v).token_ids] for k, v in G.items()}
    bad = []
    for it in panel:
        ids = [int(i) for i in be.tokenize(it["glyph"]).token_ids]
        it["token_ids"] = ids
        it["n_tokens"] = len(ids)
        if it["parts"]:
            want = tok[it["parts"][0]] + tok[it["parts"][1]]
            if want != ids:
                bad.append((it["id"], want, ids))
    if bad:
        print("\nABORT: a pair does not tokenise as its two parts concatenated:",
              file=sys.stderr)
        for x in bad:
            print(f"  {x[0]}: expected {x[1]} got {x[2]}", file=sys.stderr)
        be.close()
        return 2
    print("compositional identity holds for all "
          f"{sum(1 for it in panel if it['parts'])} pairs")

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
    print(f"\n{'id':<22} {'glyph':<5} {'tok':>4} {'mid':>6} {'last':>6} {'peak':>5}")
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
                         "n_tokens": it["n_tokens"], "layer": L, "alpha": A,
                         "ratio_mean": prof[-1]})
        mid_slice = prof[10:20] or prof
        mid[it["id"]] = float(max(mid_slice))
        it["mid"] = mid[it["id"]]
        it["last"] = float(prof[-1])
        it["peak"] = int(np.argmax(prof))
        print(f"{it['id']:<22} {it['glyph']:<5} {it['n_tokens']:>4} "
              f"{it['mid']:6.2f} {it['last']:6.2f} L{it['peak']:<4}")

    # ---------------- the systematic test --------------------------------
    print("\n" + "=" * 104)
    print("Does the order effect grow with the component gap?")
    print("=" * 104)
    print(f"{'family':<8} {'strong':<10} {'weak':<10} {'gap':>6} "
          f"{'ends weak':>10} {'ends strong':>12} {'order effect':>13}")
    fam_rows = []
    for fam, a, b in FAMILIES:
        sa, sb = mid[a], mid[b]
        strong, weak = (a, b) if sa >= sb else (b, a)
        gap = abs(sa - sb)
        ends_strong = mid[f"{fam}__{weak}_{strong}"]   # weak first, strong last
        ends_weak = mid[f"{fam}__{strong}_{weak}"]     # strong first, weak last
        eff = ends_strong - ends_weak
        fam_rows.append({"family": fam, "strong": strong, "weak": weak,
                         "mid_strong": mid[strong], "mid_weak": mid[weak],
                         "gap": gap, "ends_strong": ends_strong,
                         "ends_weak": ends_weak, "order_effect": eff})
        print(f"{fam:<8} {strong:<10} {weak:<10} {gap:6.2f} "
              f"{ends_weak:10.2f} {ends_strong:12.2f} {eff:+13.2f}")
    gaps = [f["gap"] for f in fam_rows]
    effs = [f["order_effect"] for f in fam_rows]
    rho = spearman(gaps, effs)
    print(f"\nSpearman(component gap, order effect) over {len(fam_rows)} families = "
          f"{rho:+.3f}")
    print(f"families where ending on the STRONGER component scores higher: "
          f"{sum(1 for e in effs if e > 0)}/{len(effs)}")

    # ---------------- fixed-frame geometry --------------------------------
    print("\n" + "=" * 104)
    print("Does the DIRECTION move with the order? (fixed frame — cosines are to")
    print("NAMED components, so nothing depends on positional labels)")
    print("=" * 104)
    L16 = 16 if 16 < NL else NL - 1
    print(f"{'family':<8} {'component':<10} {'cos in A-then-B':>16} "
          f"{'cos in B-then-A':>16} {'shift':>8}   (efficacy shift {'':>0})")
    geo = []
    _eff_by_family = {f["family"]: f["order_effect"] for f in fam_rows}
    for fam, a, b in FAMILIES:
        ab, ba = f"{fam}__{a}_{b}", f"{fam}__{b}_{a}"
        # use the SAME convention as family_table (ends_strong - ends_weak); the
        # declaration-order difference mid[ba]-mid[ab] flips sign whenever the
        # second-declared component is the stronger one
        eff = _eff_by_family[fam]
        for comp in (a, b):
            c_ab = cosv(dirs[ab][L16], dirs[comp][L16])
            c_ba = cosv(dirs[ba][L16], dirs[comp][L16])
            geo.append({"family": fam, "component": comp, "cos_AB": c_ab,
                        "cos_BA": c_ba, "cos_shift": c_ba - c_ab,
                        "efficacy_shift": eff})
            print(f"{fam:<8} {comp:<10} {c_ab:16.3f} {c_ba:16.3f} "
                  f"{c_ba-c_ab:+8.3f}   {eff:+.2f}")
    max_cos_shift = max(abs(g["cos_shift"]) for g in geo)
    max_eff_shift = max(abs(f["order_effect"]) for f in fam_rows)
    print(f"\nlargest |cosine shift| across all families: {max_cos_shift:.3f}")
    print(f"largest |efficacy shift|:                   {max_eff_shift:.2f} "
          f"(on a scale where the solo components span "
          f"{min(mid[k] for k in G):.2f}..{max(mid[k] for k in G):.2f})")

    (out / f"{args.tag}_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "panel": panel, "families": FAMILIES, "targets": TARGETS,
        "wrappers": WRAPPERS, "alpha": A, "nulls": args.nulls,
        "num_layers": NL, "deep_layer": L16,
        "solo_mid": {k: mid[k] for k in G},
        "family_table": fam_rows,
        "spearman_gap_vs_order_effect": rho,
        "n_families_ending_strong_higher": int(sum(1 for e in effs if e > 0)),
        "fixed_frame_cosines": geo,
        "max_abs_cosine_shift": max_cos_shift,
        "max_abs_efficacy_shift": max_eff_shift,
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_profiles.jsonl'} ({len(rows)} rows)")
    print(f"wrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
