#!/usr/bin/env python3
"""OUT-OF-CONTRACT: where does 🐈‍⬛ lose its mid-network efficacy?

The why-flat run left a clean paradox. 🐈 (mid ratio 3.96) and 🐱 (3.95) engage
the middle of the network; the ZWJ compound 🐈‍⬛ (3.09) does not, landing exactly
on ⬛ (3.00) — while its direction stays cat-shaped (cos 0.94 to 🐈 vs 0.77 to ⬛)
and the model still names it "black cat". Direction similarity and causal
efficacy come apart.

The tokenizer decomposes the compound exactly:

    🐈‍⬛  = [9468,238,230] + [102470] + [158,105,249]   =  🐈  + ZWJ + ⬛
    🐈⬛   = [9468,238,230] +            [158,105,249]   =  🐈  +       ⬛
    ⬛🐈   = [158,105,249] +             [9468,238,230]  =  ⬛  +       🐈

so the two candidate mechanisms can be separated behaviourally:

  H-ZWJ    the ZWJ joiner itself costs the efficacy
           -> 🐈⬛ (no joiner) should keep 🐈's efficacy, 🐈‍⬛ should not
  H-LAST   the final-position readout is dominated by the LAST component,
           whatever it is
           -> order is what matters: ⬛🐈 should recover cat-like efficacy and
              🐈⬛ should not, regardless of the joiner

They make opposite predictions for the reversed pair, so one run decides it.
Two more component families (🧑/🚀/🧑‍🚀 and 👩/💻/👩‍💻) test whether the answer is
about 🐈‍⬛ specifically or about composition in general.

Protocol is identical to why_flat.py (same layers, targets, alpha, null seeds),
so every number here is directly comparable to results/whyflat_report.md.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np

from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent

CAT, SQ, ZWJ = "\U0001F408", "⬛", "‍"
PERSON, ROCKET = "\U0001F9D1", "\U0001F680"
WOMAN, LAPTOP = "\U0001F469", "\U0001F4BB"

# `parts` names the components in order; `join` records how they were combined.
PANEL = [
    # --- cat family: the case under investigation ------------------------
    {"id": "cat",        "glyph": CAT,            "set": "cat", "join": "-",      "parts": []},
    {"id": "black_sq",   "glyph": SQ,             "set": "cat", "join": "-",      "parts": []},
    {"id": "cat_ZWJ_sq", "glyph": CAT + ZWJ + SQ, "set": "cat", "join": "zwj",    "parts": ["cat", "black_sq"]},
    {"id": "cat_sq",     "glyph": CAT + SQ,       "set": "cat", "join": "concat", "parts": ["cat", "black_sq"]},
    {"id": "sq_cat",     "glyph": SQ + CAT,       "set": "cat", "join": "concat", "parts": ["black_sq", "cat"]},
    {"id": "sq_ZWJ_cat", "glyph": SQ + ZWJ + CAT, "set": "cat", "join": "zwj",    "parts": ["black_sq", "cat"]},
    # --- astronaut family: both components are ordinary emoji ------------
    {"id": "person",     "glyph": PERSON,                  "set": "astro", "join": "-",      "parts": []},
    {"id": "rocket",     "glyph": ROCKET,                  "set": "astro", "join": "-",      "parts": []},
    {"id": "per_ZWJ_roc", "glyph": PERSON + ZWJ + ROCKET,  "set": "astro", "join": "zwj",    "parts": ["person", "rocket"]},
    {"id": "per_roc",    "glyph": PERSON + ROCKET,         "set": "astro", "join": "concat", "parts": ["person", "rocket"]},
    {"id": "roc_per",    "glyph": ROCKET + PERSON,         "set": "astro", "join": "concat", "parts": ["rocket", "person"]},
    # --- woman-tech family ------------------------------------------------
    {"id": "woman",      "glyph": WOMAN,                   "set": "tech", "join": "-",      "parts": []},
    {"id": "laptop",     "glyph": LAPTOP,                  "set": "tech", "join": "-",      "parts": []},
    {"id": "wom_ZWJ_lap", "glyph": WOMAN + ZWJ + LAPTOP,   "set": "tech", "join": "zwj",    "parts": ["woman", "laptop"]},
    {"id": "wom_lap",    "glyph": WOMAN + LAPTOP,          "set": "tech", "join": "concat", "parts": ["woman", "laptop"]},
    # --- anchors, to tie the scale to the previous runs -------------------
    {"id": "pizza",      "glyph": "\U0001F355",            "set": "anchor", "join": "-", "parts": []},
    {"id": "car",        "glyph": "\U0001F697",            "set": "anchor", "join": "-", "parts": []},
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="catchase_v1")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    print("=" * 104)
    print("OUT-OF-CONTRACT — where does 🐈‍⬛ lose its mid-network efficacy?")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 104)

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    NL = be.num_layers
    print(f"device={getattr(be,'device',None)} num_layers={NL} model_dim={be.model_dim}")
    layers = list(range(NL))

    # ---- token bookkeeping, and the compositional identity must actually hold
    by_id = {it["id"]: it for it in PANEL}
    print(f"\n{'id':<13} {'glyph':<5} {'join':<7} {'tok':>4}  token ids")
    bad = []
    for it in PANEL:
        ids = [int(i) for i in be.tokenize(it["glyph"]).token_ids]
        it["token_ids"] = ids
        it["n_tokens"] = len(ids)
        print(f"{it['id']:<13} {it['glyph']:<5} {it['join']:<7} {len(ids):>4}  {ids}")
    zwj_ids = [int(i) for i in be.tokenize(ZWJ).token_ids]
    for it in PANEL:
        if not it["parts"]:
            continue
        want = []
        for k, part in enumerate(it["parts"]):
            if k:
                want += zwj_ids if it["join"] == "zwj" else []
            want += by_id[part]["token_ids"]
        if want != it["token_ids"]:
            bad.append((it["id"], want, it["token_ids"]))
    if bad:
        print("\nABORT: a composite does not tokenise as its parts, so the whole "
              "decomposition argument would be false:", file=sys.stderr)
        for b in bad:
            print(f"  {b[0]}: expected {b[1]} got {b[2]}", file=sys.stderr)
        be.close()
        return 2
    print("\ncompositional identity holds for every composite "
          "(composite tokens == parts [+ ZWJ] concatenated)")

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

    # ---- nulls: same seeds as why_flat.py, so the scales are comparable
    print(f"\nbuilding per-layer nulls ({args.nulls} per layer x target) ...")
    null = {}
    for L in layers:
        for n in TARGETS:
            trms = rms(tb[n]["act"][L])
            vals = []
            for s in range(args.nulls):
                rng = np.random.default_rng(800_000 + 100 * L + s)
                d = rng.standard_normal(be.model_dim)
                v = d / rms(d) * A * trms
                r = fwd(TARGETS[n], [L],
                        Intervention(layer=L, vector=v.astype(np.float32),
                                     site="resid_post", position="last_nonpad",
                                     label="null"))
                vals.append(distribution_metrics(tb[n]["logits"], r.logits,
                                                 **MK)["kl_base_to_intervened"])
            null[(L, n)] = np.array(vals)

    rows, dirs = [], {}
    print(f"\n{'id':<13} {'glyph':<5} {'join':<7} {'tok':>4} {'peak':>5} {'mid':>6} "
          f"{'last':>6}  profile")
    for it in PANEL:
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
            cons = float(np.mean([cosv(a, b) for a, b in combinations(per[L], 2)]))
            ratios, kls, exs = [], [], []
            for n in TARGETS:
                trms = rms(tb[n]["act"][L])
                v = d / max(drms, 1e-12) * A * trms
                r = fwd(TARGETS[n], [L],
                        Intervention(layer=L, vector=v.astype(np.float32),
                                     site="resid_post", position="last_nonpad",
                                     label=f"{it['id']}_L{L}_{n}"))
                dist = distribution_metrics(tb[n]["logits"], r.logits, **MK)
                kl = dist["kl_base_to_intervened"]
                nl = null[(L, n)]
                kls.append(kl)
                ratios.append(kl / max(np.median(nl), 1e-12))
                exs.append(int(np.sum(nl >= kl)))
            prof.append(float(np.mean(ratios)))
            rows.append({"id": it["id"], "glyph": it["glyph"], "set": it["set"],
                         "join": it["join"], "parts": it["parts"],
                         "n_tokens": it["n_tokens"], "layer": L, "alpha": A,
                         "direction_consistency": cons, "direction_rms": drms,
                         "ratio_mean": prof[-1],
                         "kl_per_target": dict(zip(TARGETS, map(float, kls))),
                         "exceedance_per_target": dict(zip(TARGETS, exs)),
                         "n_null": args.nulls})
        mid_slice = prof[10:20] or prof
        it["mid"] = float(max(mid_slice))
        it["last"] = float(prof[-1])
        it["peak"] = int(np.argmax(prof))
        spark = "".join("▁▂▃▄▅▆▇█"[min(7, int(p / max(max(prof), 1e-9) * 7.99))] for p in prof)
        print(f"{it['id']:<13} {it['glyph']:<5} {it['join']:<7} {it['n_tokens']:>4} "
              f"L{it['peak']:<4} {it['mid']:6.2f} {it['last']:6.2f}  {spark}")

    # ---- the decisive comparison ------------------------------------------
    print("\n" + "=" * 104)
    print("H-ZWJ (the joiner costs it) vs H-LAST (the last component dominates)")
    print("=" * 104)
    verdicts = []
    for setname in ("cat", "astro", "tech"):
        fam = [it for it in PANEL if it["set"] == setname]
        solo = {it["id"]: it["mid"] for it in fam if not it["parts"]}
        print(f"\n[{setname}]  solo: " + "  ".join(f"{k} {v:.2f}" for k, v in solo.items()))
        print(f"  {'composite':<13} {'order':<22} {'join':<7} {'mid':>6}  "
              f"{'closer to':>10}")
        for it in fam:
            if not it["parts"]:
                continue
            order = " then ".join(it["parts"])
            near = min(solo, key=lambda k: abs(solo[k] - it["mid"]))
            verdicts.append({"set": setname, "id": it["id"], "join": it["join"],
                             "parts": it["parts"], "mid": it["mid"],
                             "last_part": it["parts"][-1], "nearest_solo": near})
            print(f"  {it['id']:<13} {order:<22} {it['join']:<7} {it['mid']:6.2f}  "
                  f"{near:>10}{'   <- matches its LAST part' if near == it['parts'][-1] else ''}")
    n_last = sum(1 for v in verdicts if v["nearest_solo"] == v["last_part"])
    print(f"\ncomposites whose mid ratio is nearest their LAST component: "
          f"{n_last}/{len(verdicts)}")

    # ---- direction cosines: does the direction follow the same rule? -------
    print("\ndirection cosine at the deep layer (L16) — composite vs its parts:")
    L16 = 16 if 16 < NL else NL - 1
    print(f"  {'composite':<13} {'cos to first':>13} {'cos to last':>12} {'margin':>8}")
    cosrows = []
    for it in PANEL:
        if not it["parts"]:
            continue
        c1 = cosv(dirs[it["id"]][L16], dirs[it["parts"][0]][L16])
        c2 = cosv(dirs[it["id"]][L16], dirs[it["parts"][-1]][L16])
        cosrows.append({"id": it["id"], "cos_first": c1, "cos_last": c2,
                        "first": it["parts"][0], "last": it["parts"][-1]})
        print(f"  {it['id']:<13} {c1:13.3f} {c2:12.3f} {c1-c2:+8.3f}"
              f"{'   direction follows FIRST' if c1 > c2 else '   direction follows LAST'}")

    (out / f"{args.tag}_profiles.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    (out / f"{args.tag}_summary.json").write_text(json.dumps({
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False, "out_of_contract": True,
        "panel": PANEL,
        "targets": TARGETS, "wrappers": WRAPPERS, "alpha": A, "nulls": args.nulls,
        "num_layers": NL, "deep_layer": L16,
        "verdicts": verdicts, "n_nearest_last": int(n_last), "n_composites": len(verdicts),
        "direction_cosines": cosrows,
        "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out / f'{args.tag}_profiles.jsonl'} ({len(rows)} rows)")
    print(f"wrote {out / f'{args.tag}_summary.json'}")
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
