#!/usr/bin/env python3
"""OUT-OF-CONTRACT deep diagnostic on the glyphs that came out strongest in
sweep_v1. Focused panel, much larger controls. Four phases, each written to
disk as soon as it finishes.

Phase 1 — generalisation + resolution
    12 injection targets spanning sharp-factual .. open-ended, 256 random
    directions per target at the deep layer. sweep_v1 could only say
    "p <= 1/25"; 256 draws take that to ~1/257, and 12 targets decide whether
    the effect was really open-ended-only or just one prompt.

Phase 2 — layer profile
    every layer 0..N-1 (sweep_v1 sampled only 5/11/16), 3 targets, so the peak
    depth is measured rather than assumed.

Phase 3 — specificity + sign flip
    Does 🍕's direction boost *pizza* words more than 🍣's direction does, or is
    it a generic "food" push? Probe words are hand-specified per glyph, NOT
    harvested from the sweep's own top-boosted lists, so the diagonal is not
    selected-on. Plus a sign-flip control: injecting −d should mirror +d.

Phase 4 — direction estimate quality
    extraction wrappers 4 -> 12, and consistency measured as a function of how
    many wrappers are averaged, to see whether it saturates.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank is used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
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

# ---------------------------------------------------------------- focus panel
FOCUS = [
    # strongest on the magnitude-controlled ranking in sweep_v1
    {"id": "beer",         "glyph": "🍺",  "family": "food",      "grp": "strong"},
    {"id": "pizza",        "glyph": "🍕",  "family": "food",      "grp": "strong"},
    {"id": "sushi",        "glyph": "🍣",  "family": "food",      "grp": "strong"},
    {"id": "burger",       "glyph": "🍔",  "family": "food",      "grp": "strong"},
    {"id": "earth",        "glyph": "🌍",  "family": "nature",    "grp": "strong"},
    {"id": "car",          "glyph": "🚗",  "family": "transport", "grp": "strong"},
    {"id": "ramen",        "glyph": "🍜",  "family": "food",      "grp": "strong"},
    # top of the prompt-level ranking but only mid-pack once size is controlled
    {"id": "dog",          "glyph": "🐶",  "family": "animal",    "grp": "high_prompt"},
    {"id": "cat",          "glyph": "🐱",  "family": "animal",    "grp": "high_prompt"},
    # weak end — needed, otherwise "strong" is unfalsifiable
    {"id": "black_square", "glyph": "⬛",  "family": "symbol",    "grp": "weak"},
    {"id": "pleading",     "glyph": "🥺",  "family": "face",      "grp": "weak"},
    {"id": "sailboat",     "glyph": "⛵",  "family": "transport", "grp": "weak"},
    # multi-token ZWJ
    {"id": "black_cat",    "glyph": "🐈‍⬛", "family": "zwj",       "grp": "zwj"},
]

# 12 injection targets, deliberately spanning peaked -> flat next-token distributions
TARGETS = {
    "paris":    "The capital of France is",
    "planet":   "The largest planet in our solar system is",
    "gold":     "The chemical symbol for gold is",
    "freeze":   "Water freezes at a temperature of",
    "summer":   "The best thing about summer is",
    "animal":   "My favorite animal is",
    "sky":      "The color of the sky is",
    "citytokyo": "The largest city in Japan is",
    "thinking": "I am thinking about",
    "today":    "Today I want to",
    "reminds":  "It reminds me of",
    "tell":     "Let me tell you about",
}
PHASE2_TARGETS = ["paris", "planet", "thinking"]

WRAPPERS_12 = [
    "Today I saw a",          # the original 4 come first so a 4-wrapper
    "My favorite thing is",   # subsample reproduces sweep_v1 exactly
    "Here we have",
    "This reminds me of",
    "Look at this",
    "I just found a",
    "There was a",
    "She showed me a",
    "The picture shows a",
    "Everyone loves a",
    "I bought a",
    "Nothing beats a",
]

# hand-specified probes: independent of the sweep's own top-boosted lists
PROBES = {
    "beer":         ["beer", "Beer", "ale", "brewery", "pint", "drinking"],
    "pizza":        ["pizza", "Pizza", "slice", "pepperoni", "Italian", "cheese"],
    "sushi":        ["sushi", "Sushi", "sashimi", "Japanese", "seafood", "rice"],
    "burger":       ["burger", "Burger", "hamburger", "fries", "sandwich", "beef"],
    "earth":        ["earth", "Earth", "planet", "globe", "world", "geography"],
    "car":          ["car", "Car", "automobile", "vehicle", "driving", "engine"],
    "ramen":        ["ramen", "Ramen", "noodles", "soup", "broth", "bowl"],
    "dog":          ["dog", "Dog", "puppy", "canine", "barking", "pet"],
    "cat":          ["cat", "Cat", "kitten", "feline", "meow", "purr"],
    "black_square": ["square", "Square", "geometry", "shape", "rectangle", "black"],
    "pleading":     ["please", "Please", "sad", "begging", "cute", "emotion"],
    "sailboat":     ["sailboat", "boat", "sailing", "yacht", "harbor", "sea"],
    "black_cat":    ["cat", "black", "Halloween", "superstition", "kitten", "feline"],
}

MK = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
          save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def cosv(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def slim(d: dict) -> dict:
    return {k: v for k, v in d.items() if k != "fingerprint"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", type=int, nargs="+", default=[1, 2, 3, 4])
    ap.add_argument("--deep-layer", type=int, default=16)
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls-phase1", type=int, default=256)
    ap.add_argument("--nulls-phase2", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="deep_v1")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    print("=" * 100)
    print("OUT-OF-CONTRACT deep diagnostic — focused panel, large controls")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 100)
    print(f"panel  : {len(FOCUS)} glyphs  ({' '.join(g['glyph'] for g in FOCUS)})")
    print(f"phases : {args.phases}   alpha={A}   deep layer={args.deep_layer}")
    print("-" * 100)

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg)
    be.load()
    NL = be.num_layers
    print(f"device={getattr(be,'device',None)} num_layers={NL} model_dim={be.model_dim}")

    def fwd(prompt, layers, iv=None):
        return be.forward(prompt, capture_layers=layers, site="resid_post",
                          position="last_nonpad", intervention=iv)

    def inject(prompt, L, vec, label):
        return fwd(prompt, [L], Intervention(layer=L, vector=np.asarray(vec, np.float32),
                                             site="resid_post", position="last_nonpad",
                                             label=label))

    meta = {"claim_stage": "pre-causal-activation-screen",
            "causal_claim_authorized": False, "out_of_contract": True,
            "panel": FOCUS, "targets": TARGETS, "wrappers_12": WRAPPERS_12,
            "alpha": A, "deep_layer": args.deep_layer,
            "nulls_phase1": args.nulls_phase1, "nulls_phase2": args.nulls_phase2,
            "backend": "transformers/mps/fp32", "model_path": os.environ["SNAP"],
            "num_layers": NL, "phases_run": []}
    # a single-phase rerun must not erase the record of the other phases
    _meta_path = out / f"{args.tag}_meta.json"
    if _meta_path.exists():
        try:
            _prev = json.loads(_meta_path.read_text(encoding="utf-8"))
            meta["phases_run"] = [p for p in _prev.get("phases_run", [])
                                  if p.get("phase") not in args.phases]
        except Exception:
            pass
    t_all = time.time()

    # ---------------------------------------------------------------- helpers
    def direction(g, layers, wrappers, wrap_base):
        """mean over wrappers of (glyph-prefixed - bare) at each layer."""
        per = {L: [] for L in layers}
        for w in wrappers:
            r = fwd(f"{g}\n{w}", layers)
            for L in layers:
                per[L].append(np.asarray(r.activations[L], np.float64) - wrap_base[w][L])
        return per

    # =============================================================== PHASE 1
    if 1 in args.phases:
        t0 = time.time()
        print("\n" + "=" * 100)
        print(f"PHASE 1 — {len(TARGETS)} targets x {args.nulls_phase1} random directions "
              f"@ L{args.deep_layer}")
        print("=" * 100)
        L = args.deep_layer

        wrap4 = WRAPPERS_12[:4]
        wb = {}
        for w in wrap4:
            r = fwd(w, [L])
            wb[w] = {L: np.asarray(r.activations[L], np.float64)}

        tinfo = {}
        for name, p in TARGETS.items():
            r = fwd(p, [L])
            lg = np.asarray(r.logits, np.float64)
            pr = np.exp(lg - lg.max()); pr /= pr.sum()
            s = np.sort(lg)[::-1]
            tinfo[name] = {"prompt": p, "logits": r.logits,
                           "act": np.asarray(r.activations[L], np.float64),
                           "top1": be.tokenizer.decode([int(np.argmax(lg))]),
                           "entropy": float(-(pr * np.log(np.maximum(pr, 1e-12))).sum()),
                           "top2_margin": float(s[0] - s[1])}
        print(f"{'target':<11} {'prompt':<44} {'top-1':<12} {'entropy':>8} {'margin':>7}")
        for n, t in tinfo.items():
            print(f"{n:<11} {t['prompt'][:43]:<44} {t['top1']!r:<12} "
                  f"{t['entropy']:8.3f} {t['top2_margin']:7.3f}")

        print(f"\nbuilding null: {args.nulls_phase1} draws x {len(TARGETS)} targets ...")
        null1 = {}
        for name, t in tinfo.items():
            trms = rms(t["act"])
            vals = []
            for s in range(args.nulls_phase1):
                rng = np.random.default_rng(700_000 + s)
                d = rng.standard_normal(be.model_dim)
                v = d / rms(d) * A * trms
                r = inject(t["prompt"], L, v, f"null_s{s}")
                vals.append(distribution_metrics(t["logits"], r.logits,
                                                 **MK)["kl_base_to_intervened"])
            null1[name] = np.array(vals)
            print(f"  {name:<11} median={np.median(vals):.4f} sd={np.std(vals, ddof=1):.4f} "
                  f"max={np.max(vals):.4f}")

        rows1 = []
        print(f"\n{'g':<3} {'id':<13} {'grp':<11} " +
              " ".join(f"{n[:6]:>7}" for n in TARGETS) + "   clean/12")
        for item in FOCUS:
            per = direction(item["glyph"], [L], wrap4, wb)
            d = np.mean(per[L], axis=0)
            drms = rms(d)
            cells, clean = [], 0
            for name, t in tinfo.items():
                trms = rms(t["act"])
                v = d / max(drms, 1e-12) * A * trms
                r = inject(t["prompt"], L, v, f"{item['id']}_{name}")
                dist = distribution_metrics(t["logits"], r.logits, **MK)
                kl = dist["kl_base_to_intervened"]
                nl = null1[name]
                ex = int(np.sum(nl >= kl))
                clean += (ex == 0)
                cells.append(kl)
                rows1.append({"phase": 1, "id": item["id"], "glyph": item["glyph"],
                              "group": item["grp"], "family": item["family"],
                              "layer": L, "target": name, "alpha": A,
                              "target_entropy": t["entropy"],
                              "target_top2_margin": t["top2_margin"],
                              "kl": kl,
                              "null_median": float(np.median(nl)),
                              "null_mean": float(nl.mean()),
                              "null_sd": float(nl.std(ddof=1)),
                              "ratio_to_null_median": float(kl / max(np.median(nl), 1e-12)),
                              "n_null_ge_observed": ex,
                              "n_null": int(nl.size),
                              "p_nonparametric": float((ex + 1) / (nl.size + 1)),
                              "argmax_flip": bool(dist["argmax_flip"]),
                              "baseline_top1": t["top1"],
                              "intervened_top1": be.tokenizer.decode(
                                  [int(dist["intervened_argmax"])]),
                              "top_boosted": [[be.tokenizer.decode([int(i)]), round(float(v2), 4)]
                                              for i, v2 in zip(dist["top_positive_delta_ids"],
                                                               dist["top_positive_delta_values"])]})
            print(f"{item['glyph']:<3} {item['id']:<13} {item['grp']:<11} " +
                  " ".join(f"{c:7.4f}" for c in cells) + f"   {clean:>2}/12")

        (out / f"{args.tag}_phase1.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows1) + "\n", encoding="utf-8")
        meta["phases_run"].append({"phase": 1, "rows": len(rows1),
                                   "elapsed_s": round(time.time() - t0, 1)})
        (out / f"{args.tag}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nphase 1 done in {time.time()-t0:.0f}s -> {args.tag}_phase1.jsonl")

    # =============================================================== PHASE 2
    if 2 in args.phases:
        t0 = time.time()
        layers = list(range(NL))
        print("\n" + "=" * 100)
        print(f"PHASE 2 — layer profile, all {NL} layers x {len(PHASE2_TARGETS)} targets, "
              f"{args.nulls_phase2} nulls/cell")
        print("=" * 100)

        wrap4 = WRAPPERS_12[:4]
        wb = {}
        for w in wrap4:
            r = fwd(w, layers)
            wb[w] = {L: np.asarray(r.activations[L], np.float64) for L in layers}
        tb = {}
        for n in PHASE2_TARGETS:
            r = fwd(TARGETS[n], layers)
            tb[n] = {"logits": r.logits,
                     "act": {L: np.asarray(r.activations[L], np.float64) for L in layers}}

        print("building per-layer nulls ...")
        null2 = {}
        for L in layers:
            for n in PHASE2_TARGETS:
                trms = rms(tb[n]["act"][L])
                vals = []
                for s in range(args.nulls_phase2):
                    rng = np.random.default_rng(800_000 + 100 * L + s)
                    d = rng.standard_normal(be.model_dim)
                    v = d / rms(d) * A * trms
                    r = inject(TARGETS[n], L, v, f"null_L{L}_s{s}")
                    vals.append(distribution_metrics(tb[n]["logits"], r.logits,
                                                     **MK)["kl_base_to_intervened"])
                null2[(L, n)] = np.array(vals)

        rows2 = []
        print(f"\n{'g':<3} {'id':<13} best-L  peak ratio   ratio by layer (0..{NL-1})")
        for item in FOCUS:
            per = direction(item["glyph"], layers, wrap4, wb)
            prof = []
            for L in layers:
                d = np.mean(per[L], axis=0)
                drms = rms(d)
                cons = float(np.mean([cosv(a, b) for a, b in combinations(per[L], 2)]))
                ratios, exs, kls = [], [], []
                for n in PHASE2_TARGETS:
                    trms = rms(tb[n]["act"][L])
                    v = d / max(drms, 1e-12) * A * trms
                    r = inject(TARGETS[n], L, v, f"{item['id']}_L{L}_{n}")
                    dist = distribution_metrics(tb[n]["logits"], r.logits, **MK)
                    kl = dist["kl_base_to_intervened"]
                    nl = null2[(L, n)]
                    ratios.append(kl / max(np.median(nl), 1e-12))
                    exs.append(int(np.sum(nl >= kl)))
                    kls.append(kl)
                mr = float(np.mean(ratios))
                prof.append(mr)
                rows2.append({"phase": 2, "id": item["id"], "glyph": item["glyph"],
                              "group": item["grp"], "layer": L, "alpha": A,
                              "direction_consistency": cons, "direction_rms": drms,
                              "kl_per_target": dict(zip(PHASE2_TARGETS, map(float, kls))),
                              "ratio_mean": mr,
                              "ratio_per_target": dict(zip(PHASE2_TARGETS, map(float, ratios))),
                              "exceedance_per_target": dict(zip(PHASE2_TARGETS, exs)),
                              "n_null": args.nulls_phase2})
            bl = int(np.argmax(prof))
            spark = "".join("▁▂▃▄▅▆▇█"[min(7, int(p / max(max(prof), 1e-9) * 7.99))] for p in prof)
            print(f"{item['glyph']:<3} {item['id']:<13} L{bl:<5} {max(prof):10.2f}   {spark}")

        (out / f"{args.tag}_phase2.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows2) + "\n", encoding="utf-8")
        meta["phases_run"].append({"phase": 2, "rows": len(rows2),
                                   "elapsed_s": round(time.time() - t0, 1)})
        (out / f"{args.tag}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nphase 2 done in {time.time()-t0:.0f}s -> {args.tag}_phase2.jsonl")

    # =============================================================== PHASE 3
    if 3 in args.phases:
        t0 = time.time()
        L = args.deep_layer
        print("\n" + "=" * 100)
        print(f"PHASE 3 — cross-glyph specificity matrix + sign flip @ L{L}")
        print("=" * 100)

        probe_ids, probe_words = {}, {}
        for k, words in PROBES.items():
            ids, kept = [], []
            for w in words:
                t = be.tokenize(" " + w).token_ids
                if t:
                    ids.append(int(t[0])); kept.append(w)
            probe_ids[k] = ids
            probe_words[k] = kept
        print("probe groups (first token of ' <word>'):")
        for k in PROBES:
            print(f"  {k:<13} {probe_words[k]}")

        wrap4 = WRAPPERS_12[:4]
        wb = {}
        for w in wrap4:
            r = fwd(w, [L])
            wb[w] = {L: np.asarray(r.activations[L], np.float64)}
        tb3 = {}
        for n in PHASE2_TARGETS:
            r = fwd(TARGETS[n], [L])
            tb3[n] = {"logits": np.asarray(r.logits, np.float64),
                      "act": np.asarray(r.activations[L], np.float64)}

        rows3, matrix = [], {}
        keys = [g["id"] for g in FOCUS]
        for item in FOCUS:
            per = direction(item["glyph"], [L], wrap4, wb)
            d = np.mean(per[L], axis=0)
            drms = rms(d)
            pos_acc = {k: [] for k in keys}
            for sign in (+1, -1):
                for n in PHASE2_TARGETS:
                    trms = rms(tb3[n]["act"])
                    v = sign * d / max(drms, 1e-12) * A * trms
                    r = inject(TARGETS[n], L, v, f"{item['id']}_{n}_s{sign}")
                    delta = np.asarray(r.logits, np.float64) - tb3[n]["logits"]
                    grp = {k: float(np.mean(delta[probe_ids[k]])) for k in keys}
                    if sign > 0:
                        for k in keys:
                            pos_acc[k].append(grp[k])
                    rows3.append({"phase": 3, "id": item["id"], "glyph": item["glyph"],
                                  "group": item["grp"], "layer": L, "target": n,
                                  "sign": sign, "alpha": A,
                                  "probe_delta_by_group": grp,
                                  "kl": distribution_metrics(tb3[n]["logits"], r.logits,
                                                             **MK)["kl_base_to_intervened"]})
            matrix[item["id"]] = {k: float(np.mean(pos_acc[k])) for k in keys}

        print(f"\nspecificity matrix — mean logit delta on each probe group "
              f"(rows = injected glyph)")
        hdr = " ".join(f"{k[:6]:>7}" for k in keys)
        print(f"{'inject':<14} {hdr}   diag  best-off  margin")
        # first-token truncation can make two hand-written groups share ids
        # (black_cat and cat are both cats), which would make an instance-level
        # diagonal meaningless. Report the overlaps and exclude those competitors.
        pid = {k: set(v) for k, v in probe_ids.items()}
        shared = {(a, b): sorted(pid[a] & pid[b])
                  for i, a in enumerate(keys) for b in keys[i + 1:] if pid[a] & pid[b]}
        if shared:
            print("probe groups sharing token ids (excluded as competitors):")
            for (a, b), ids in shared.items():
                print(f"  {a} <-> {b}: {len(ids)} of {len(pid[a])}")
        diag_wins = 0
        for item in FOCUS:
            k0 = item["id"]
            vals = matrix[k0]
            off = {k: v for k, v in vals.items() if k != k0 and not (pid[k] & pid[k0])}
            if not off:
                continue
            bo = max(off.items(), key=lambda kv: kv[1])
            win = vals[k0] >= bo[1]
            diag_wins += win
            print(f"{item['glyph']} {k0:<12} " + " ".join(f"{vals[k]:7.3f}" for k in keys) +
                  f"  {vals[k0]:6.3f}  {bo[0][:8]:>8} {vals[k0]-bo[1]:+7.3f}"
                  + ("  <-- self wins" if win else ""))
        print(f"\nself-probe group is the single largest for {diag_wins}/{len(FOCUS)} glyphs")

        # The instance-level diagonal is the wrong unit if the direction carries a
        # CATEGORY rather than an instance. Test the block-diagonal too.
        BLOCKS = {"food": ["beer", "pizza", "sushi", "burger", "ramen"],
                  "animal": ["dog", "cat", "black_cat"],
                  "vehicle": ["car", "sailboat"],
                  "other": ["earth", "black_square", "pleading"]}
        blk_of = {g: b for b, gs in BLOCKS.items() for g in gs}
        print("\nblock view — mean probe delta by category block (rows = injected glyph)")
        print(f"{'inject':<14} " + " ".join(f"{b:>8}" for b in BLOCKS) +
              "   own-block  best-other  margin")
        blk_wins, blk_rows = 0, {}
        for item in FOCUS:
            k0 = item["id"]
            own = blk_of[k0]
            bm = {b: float(np.mean([matrix[k0][k] for k in gs])) for b, gs in BLOCKS.items()}
            other = {b: v for b, v in bm.items() if b != own}
            bo = max(other.items(), key=lambda kv: kv[1])
            win = bm[own] >= bo[1]
            blk_wins += win
            blk_rows[k0] = {"own_block": own, "block_means": bm,
                            "own_minus_best_other": bm[own] - bo[1], "win": bool(win)}
            print(f"{item['glyph']} {k0:<12} " + " ".join(f"{bm[b]:8.3f}" for b in BLOCKS) +
                  f"   {bm[own]:9.3f}  {bo[0]:>10} {bm[own]-bo[1]:+7.3f}" +
                  ("  <-- own block wins" if win else ""))
        print(f"\nown category block is largest for {blk_wins}/{len(FOCUS)} glyphs "
              f"(instance-level was {diag_wins}/{len(FOCUS)})")

        # sign-flip antisymmetry
        anti = []
        for item in FOCUS:
            p = [r for r in rows3 if r["id"] == item["id"] and r["sign"] > 0]
            m = [r for r in rows3 if r["id"] == item["id"] and r["sign"] < 0]
            for a, b in zip(p, m):
                x = np.array([a["probe_delta_by_group"][k] for k in keys])
                y = np.array([b["probe_delta_by_group"][k] for k in keys])
                anti.append(cosv(x, -y))
        print(f"sign-flip antisymmetry: cos(probe_delta(+d), -probe_delta(-d)) "
              f"median={np.median(anti):.4f} min={np.min(anti):.4f}")

        (out / f"{args.tag}_phase3.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows3) + "\n", encoding="utf-8")
        (out / f"{args.tag}_specificity_matrix.json").write_text(
            json.dumps({"matrix": matrix, "probe_words": probe_words,
                        "probe_ids": probe_ids, "layer": L, "alpha": A,
                        "self_wins_instance_level": int(diag_wins), "n": len(FOCUS),
                        "probe_group_overlaps": {f"{a}|{b}": v for (a, b), v in shared.items()},
                        "blocks": BLOCKS, "block_view": blk_rows,
                        "own_block_wins": int(blk_wins),
                        "antisymmetry_median": float(np.median(anti)),
                        "antisymmetry_min": float(np.min(anti))},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        meta["phases_run"].append({"phase": 3, "rows": len(rows3),
                                   "elapsed_s": round(time.time() - t0, 1)})
        (out / f"{args.tag}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nphase 3 done in {time.time()-t0:.0f}s -> {args.tag}_phase3.jsonl")

    # =============================================================== PHASE 4
    if 4 in args.phases:
        t0 = time.time()
        L = args.deep_layer
        print("\n" + "=" * 100)
        print(f"PHASE 4 — extraction wrappers 4 -> {len(WRAPPERS_12)} @ L{L}")
        print("=" * 100)

        wb = {}
        for w in WRAPPERS_12:
            r = fwd(w, [L])
            wb[w] = {L: np.asarray(r.activations[L], np.float64)}
        tb4 = {}
        for n in PHASE2_TARGETS:
            r = fwd(TARGETS[n], [L])
            tb4[n] = {"logits": r.logits, "act": np.asarray(r.activations[L], np.float64)}

        nulls4 = {}
        for n in PHASE2_TARGETS:
            trms = rms(tb4[n]["act"])
            vals = []
            for s in range(args.nulls_phase2):
                rng = np.random.default_rng(900_000 + s)
                d = rng.standard_normal(be.model_dim)
                v = d / rms(d) * A * trms
                r = inject(TARGETS[n], L, v, f"null4_s{s}")
                vals.append(distribution_metrics(tb4[n]["logits"], r.logits,
                                                 **MK)["kl_base_to_intervened"])
            nulls4[n] = np.array(vals)

        rows4 = []
        subs = [2, 4, 6, 8, 10, 12]
        print(f"\n{'g':<3} {'id':<13} " + " ".join(f"cons@{k:<2}" for k in subs) +
              "   ratio(4w)  ratio(12w)")
        for item in FOCUS:
            per = direction(item["glyph"], [L], WRAPPERS_12, wb)[L]
            cons_by_k = []
            for k in subs:
                sub = per[:k]
                cons_by_k.append(float(np.mean([cosv(a, b) for a, b in combinations(sub, 2)])))
            res = {}
            for k in (4, 12):
                d = np.mean(per[:k], axis=0)
                drms = rms(d)
                rr = []
                for n in PHASE2_TARGETS:
                    trms = rms(tb4[n]["act"])
                    v = d / max(drms, 1e-12) * A * trms
                    r = inject(TARGETS[n], L, v, f"{item['id']}_{n}_w{k}")
                    kl = distribution_metrics(tb4[n]["logits"], r.logits,
                                              **MK)["kl_base_to_intervened"]
                    rr.append(kl / max(np.median(nulls4[n]), 1e-12))
                res[k] = float(np.mean(rr))
            rows4.append({"phase": 4, "id": item["id"], "glyph": item["glyph"],
                          "group": item["grp"], "layer": L, "alpha": A,
                          "consistency_by_n_wrappers": dict(zip(map(str, subs), cons_by_k)),
                          "ratio_4_wrappers": res[4], "ratio_12_wrappers": res[12],
                          "direction_rms_4": rms(np.mean(per[:4], axis=0)),
                          "direction_rms_12": rms(np.mean(per[:12], axis=0)),
                          "cos_dir4_dir12": cosv(np.mean(per[:4], axis=0),
                                                 np.mean(per[:12], axis=0))})
            print(f"{item['glyph']:<3} {item['id']:<13} " +
                  " ".join(f"{c:7.3f}" for c in cons_by_k) +
                  f"   {res[4]:9.2f} {res[12]:11.2f}")

        (out / f"{args.tag}_phase4.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows4) + "\n", encoding="utf-8")
        meta["phases_run"].append({"phase": 4, "rows": len(rows4),
                                   "elapsed_s": round(time.time() - t0, 1)})
        print(f"\nphase 4 done in {time.time()-t0:.0f}s -> {args.tag}_phase4.jsonl")

    meta["phases_run"].sort(key=lambda p: p["phase"])
    meta["total_elapsed_s"] = round(time.time() - t_all, 1)
    (out / f"{args.tag}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\n" + "=" * 100)
    print(f"ALL DONE in {meta['total_elapsed_s']:.0f}s")
    print("=" * 100)
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
