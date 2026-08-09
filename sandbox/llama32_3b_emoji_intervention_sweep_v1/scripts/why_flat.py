#!/usr/bin/env python3
"""OUT-OF-CONTRACT follow-up: why do ⬛ 🥺 ⛵ 🐈‍⬛ have no mid-network peak?

The deep diagnostic split the panel with no exceptions: nine glyphs peak at
L14-16, four are flat through the middle and only spike at the final layer.
Three hypotheses, each made falsifiable here.

H1  ENCODING, not meaning.
    A retrospective check on sweep_v1 found that glyphs whose UTF-8 encoding is
    3 bytes (U+26xx / U+2Bxx — the legacy dingbat and geometric-shape blocks,
    tokenised with leading byte-token 158) score far below the 4-byte emoji-plane
    glyphs (leading byte-token 9468): prompt-KL median 0.257 vs 0.397,
    Spearman(is_3byte, prompt_KL) = -0.55, and -0.48 inside the token-length
    matched stratum, so it is NOT token count. Three of the four flat glyphs are
    3-byte (⬛, ⛵) or end in the 3-byte tokens of ⬛ (🐈‍⬛).
    -> Test with NEAR-SYNONYM PAIRS that differ only in byte class:
         ⛵ U+26F5 vs 🚢 U+1F6A2      (both: boat)
         ☕ U+2615 vs 🍵 U+1F375      (both: hot drink in a cup)
         ⬛ U+2B1B vs 🟥 U+1F7E5      (both: a filled square)
         ✈️ U+2708 vs 🚁 U+1F681      (both: aircraft)
    If H1 holds, the E2 member of each pair is flat and the F0 member peaks.

H2  ZWJ INHERITANCE.
    🐈‍⬛ tokenises as [9468,238,230] + [102470] + [158,105,249], i.e. literally
    🐈's tokens + ZWJ + ⬛'s tokens. Its direction may be dominated by the ⬛ tail.
    -> Test by comparing the direction of 🐈‍⬛ against 🐈, 🐱 and ⬛ layer by layer.

H3  NO CONCEPT ATTACHED.
    The model may simply not know these glyphs.
    -> Test by asking it: greedy continuation of naming prompts, plus the
       probability it assigns to the correct concept word.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no sealed v2 receipt. No holdout bank.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nullcache import NullCache  # noqa: E402

from glyphprobe.analysis.metrics import distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

ROOT = Path(__file__).resolve().parent.parent

# pair = near-synonym pairs differing in UTF-8 byte class; role marks the H1 test
PANEL = [
    # --- H1 near-synonym pairs -------------------------------------------
    {"id": "sailboat",  "glyph": "⛵",  "pair": "boat",   "grp": "E2", "sem": "vehicle"},
    {"id": "ship",      "glyph": "🚢",  "pair": "boat",   "grp": "F0", "sem": "vehicle"},
    {"id": "coffee",    "glyph": "☕",  "pair": "drink",  "grp": "E2", "sem": "food"},
    {"id": "tea",       "glyph": "🍵",  "pair": "drink",  "grp": "F0", "sem": "food"},
    {"id": "black_sq",  "glyph": "⬛",  "pair": "square", "grp": "E2", "sem": "abstract"},
    {"id": "red_sq",    "glyph": "🟥",  "pair": "square", "grp": "F0", "sem": "abstract"},
    {"id": "airplane",  "glyph": "✈️",  "pair": "air",    "grp": "E2", "sem": "vehicle"},
    {"id": "helicopter", "glyph": "🚁", "pair": "air",    "grp": "F0", "sem": "vehicle"},
    {"id": "anchor",    "glyph": "⚓",  "pair": "-",      "grp": "E2", "sem": "object"},
    # --- H2 ZWJ decomposition --------------------------------------------
    {"id": "black_cat", "glyph": "🐈‍⬛", "pair": "-",     "grp": "ZWJ", "sem": "animal"},
    {"id": "cat_plain", "glyph": "🐈",  "pair": "-",      "grp": "F0", "sem": "animal"},
    {"id": "cat_face",  "glyph": "🐱",  "pair": "-",      "grp": "F0", "sem": "animal"},
    # --- the one flat glyph that is NOT 3-byte, plus emotion comparisons --
    {"id": "pleading",  "glyph": "🥺",  "pair": "cry",    "grp": "F0", "sem": "emotion"},
    {"id": "crying",    "glyph": "😢",  "pair": "cry",    "grp": "F0", "sem": "emotion"},
    {"id": "sob",       "glyph": "😭",  "pair": "cry",    "grp": "F0", "sem": "emotion"},
    {"id": "thinking",  "glyph": "🤔",  "pair": "-",      "grp": "F0", "sem": "emotion"},
    # --- anchors known to be mid-peak ------------------------------------
    {"id": "pizza",     "glyph": "🍕",  "pair": "-",      "grp": "F0", "sem": "food"},
    {"id": "car",       "glyph": "🚗",  "pair": "-",      "grp": "F0", "sem": "vehicle"},
    {"id": "dog",       "glyph": "🐶",  "pair": "-",      "grp": "F0", "sem": "animal"},
]

CONCEPTS = {
    "sailboat": ["sail", "boat", "ship", "sailing"],
    "ship": ["ship", "boat", "cruise", "sail"],
    "coffee": ["coffee", "cup", "mug", "hot"],
    "tea": ["tea", "cup", "mug", "green"],
    "black_sq": ["black", "square", "dark"],
    "red_sq": ["red", "square"],
    "airplane": ["plane", "airplane", "air", "flight"],
    "helicopter": ["helicopter", "chopper", "hel"],
    "anchor": ["anchor", "boat", "ship"],
    "black_cat": ["black", "cat", "kitten"],
    "cat_plain": ["cat", "kitten", "feline"],
    "cat_face": ["cat", "kitten", "feline"],
    "pleading": ["sad", "pleading", "begging", "puppy", "cute"],
    "crying": ["crying", "sad", "tear", "cry"],
    "sob": ["crying", "sobbing", "sad", "cry"],
    "thinking": ["thinking", "thought", "think", "confused"],
    "pizza": ["pizza", "slice", "food"],
    "car": ["car", "vehicle", "automobile"],
    "dog": ["dog", "puppy", "canine"],
}

NAME_PROMPTS = [
    "The emoji {g} is a picture of a",
    "Q: What does this emoji show? {g}\nA: It shows a",
    "{g} — this symbol represents a",
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
    a = np.asarray(a, np.float64); b = np.asarray(b, np.float64)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def softmax(x):
    x = np.asarray(x, np.float64); x = x - x.max()
    e = np.exp(x); return e / e.sum()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", type=int, nargs="+", default=[1, 2],
                    choices=[1, 2], help="1 = concept probe, 2 = layer profile")
    ap.add_argument("--alpha", type=float, default=0.5)
    ap.add_argument("--nulls", type=int, default=24)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="whyflat_v1")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    A = args.alpha

    print("=" * 104)
    print("OUT-OF-CONTRACT — why are ⬛ 🥺 ⛵ 🐈‍⬛ flat through the middle of the network?")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 104)

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    be = create_backend(cfg); be.load()
    NL = be.num_layers
    print(f"device={getattr(be,'device',None)} num_layers={NL} model_dim={be.model_dim}")

    def fwd(p, layers, iv=None):
        return be.forward(p, capture_layers=layers, site="resid_post",
                          position="last_nonpad", intervention=iv)

    # record byte class straight from the encoding, not assumed
    for it in PANEL:
        b = it["glyph"].encode("utf-8")
        it["utf8_lead"] = f"{b[0]:02x}"
        it["utf8_len"] = len(b)
        ids = be.tokenize(it["glyph"]).token_ids
        it["token_ids"] = [int(i) for i in ids]
        it["n_tokens"] = len(ids)

    meta = {"claim_stage": "pre-causal-activation-screen", "causal_claim_authorized": False,
            "out_of_contract": True, "panel": PANEL, "targets": TARGETS,
            "wrappers": WRAPPERS, "alpha": A, "nulls": args.nulls,
            "num_layers": NL, "backend": "transformers/mps/fp32",
            "model_path": os.environ["SNAP"], "phases_run": []}
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

    # ================================================== PHASE 1 — does it know?
    if 1 in args.phases:
        t0 = time.time()
        print("\n" + "=" * 104)
        print("PHASE 1 — H3: does the model have a concept for this glyph?")
        print("=" * 104)
        rows1 = []
        retokenised = False
        print(f"{'g':<4} {'id':<11} {'cls':<4} {'ntok':>4} {'P(concept)':>11} {'rank':>6}  "
              f"greedy continuation of \"The emoji <g> is a picture of a\"")
        for it in PANEL:
            g = it["glyph"]
            probs, ranks = [], []
            for tmpl in NAME_PROMPTS:
                r = fwd(tmpl.format(g=g), [])
                p = softmax(r.logits)
                best_p, best_r = 0.0, 10**9
                for wrd in CONCEPTS[it["id"]]:
                    tid = be.tokenize(" " + wrd).token_ids
                    if not tid:
                        continue
                    i = int(tid[0])
                    best_p = max(best_p, float(p[i]))
                    best_r = min(best_r, int((p > p[i]).sum() + 1))
                probs.append(best_p); ranks.append(best_r)
            # greedy continuation for legibility
            prompt = NAME_PROMPTS[0].format(g=g)
            # decode-then-re-encode would let BPE re-merge the boundary, so the
            # string would not be the model's actual greedy path. Extend the token
            # sequence itself and only decode at the end.
            base_ids = list(be.tokenize(prompt).token_ids)
            cont_ids: list[int] = []
            for _ in range(8):
                so_far = be.tokenizer.decode(base_ids + cont_ids)
                nxt = int(np.argmax(fwd(so_far, []).logits))
                if be.tokenize(so_far).token_ids != base_ids + cont_ids:
                    retokenised = True
                cont_ids.append(nxt)
            cont = be.tokenizer.decode(cont_ids)
            rows1.append({"phase": 1, **{k: it[k] for k in
                                         ("id", "glyph", "grp", "sem", "pair",
                                          "utf8_lead", "utf8_len", "n_tokens")},
                          "p_concept_mean": float(np.mean(probs)),
                          "p_concept_per_prompt": probs,
                          "rank_concept_best": int(min(ranks)),
                          "greedy_continuation": cont})
            print(f"{g:<4} {it['id']:<11} {it['grp']:<4} {it['n_tokens']:>4} "
                  f"{np.mean(probs):11.4f} {min(ranks):>6}  {cont!r}")
        if retokenised:
            print("NOTE: at least one greedy step round-tripped to a different token "
                  "sequence; treat those continuations as indicative only.")
        (out / f"{args.tag}_phase1.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows1) + "\n", encoding="utf-8")
        meta["phases_run"].append({"phase": 1, "rows": len(rows1),
                                   "elapsed_s": round(time.time() - t0, 1)})
        (out / f"{args.tag}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nphase 1 done in {time.time()-t0:.0f}s")

    # ================================================== PHASE 2 — layer profile
    if 2 in args.phases:
        t0 = time.time()
        layers = list(range(NL))
        print("\n" + "=" * 104)
        print(f"PHASE 2 — H1/H2: layer profile, all {NL} layers x {len(TARGETS)} targets")
        print("=" * 104)
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

        rows2, dirs = [], {}
        print(f"\n{'g':<4} {'id':<11} {'cls':<4} {'peak':>5} {'peakR':>6} {'midR':>6} "
              f"{'lastR':>6}  {'shape':<10} profile")
        for it in PANEL:
            per = {L: [] for L in layers}
            for w in WRAPPERS:
                r = fwd(f"{it['glyph']}\n{w}", layers)
                for L in layers:
                    per[L].append(np.asarray(r.activations[L], np.float64) - wb[w][L])
            dirs[it["id"]] = {L: np.mean(per[L], axis=0) for L in layers}
            prof = []
            for L in layers:
                d = dirs[it["id"]][L]; drms = rms(d)
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
                    kls.append(kl); ratios.append(kl / max(np.median(nl), 1e-12))
                    exs.append(int(np.sum(nl >= kl)))
                mr = float(np.mean(ratios)); prof.append(mr)
                rows2.append({"phase": 2, "id": it["id"], "glyph": it["glyph"],
                              "grp": it["grp"], "sem": it["sem"], "pair": it["pair"],
                              "utf8_lead": it["utf8_lead"], "n_tokens": it["n_tokens"],
                              "layer": L, "alpha": A, "direction_consistency": cons,
                              "direction_rms": drms, "ratio_mean": mr,
                              "kl_per_target": dict(zip(TARGETS, map(float, kls))),
                              "exceedance_per_target": dict(zip(TARGETS, exs))})
            mid_slice = prof[10:20] or prof            # small models have no L10-19
            mid = max(mid_slice); last = prof[-1]; pk = int(np.argmax(prof))
            shape = "MID-PEAK" if mid > last else "last-peak"
            spark = "".join("▁▂▃▄▅▆▇█"[min(7, int(p / max(max(prof), 1e-9) * 7.99))] for p in prof)
            print(f"{it['glyph']:<4} {it['id']:<11} {it['grp']:<4} L{pk:<4} {max(prof):6.2f} "
                  f"{mid:6.2f} {last:6.2f}  {shape:<10} {spark}")

        (out / f"{args.tag}_phase2.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows2) + "\n", encoding="utf-8")
        # direction vectors are not persisted: nothing downstream reads them, the
        # H2 cosines below are saved in *_hypotheses.json, and the README states
        # that raw arrays are not stored.

        # ---- H1 pair verdicts ----
        prof_by = {}
        for r in rows2:
            prof_by.setdefault(r["id"], {})[r["layer"]] = r["ratio_mean"]
        print("\nH1 — near-synonym pairs differing only in UTF-8 byte class:")
        print(f"{'pair':<8} {'E2 glyph':<22} {'F0 glyph':<22} verdict")
        pairs = {}
        for it in PANEL:
            if it["pair"] != "-":
                pairs.setdefault(it["pair"], []).append(it)
        h1 = []
        for pname, members in pairs.items():
            e2 = [m for m in members if m["grp"] == "E2"]
            f0 = [m for m in members if m["grp"] == "F0"]
            if not (e2 and f0):
                continue
            for a in e2:
                for b in f0:
                    pa = [prof_by[a["id"]][L] for L in layers]
                    pb = [prof_by[b["id"]][L] for L in layers]
                    sa = "MID" if max(pa[10:20]) > pa[-1] else "LAST"
                    sb = "MID" if max(pb[10:20]) > pb[-1] else "LAST"
                    ok = (sa == "LAST" and sb == "MID")
                    h1.append({"pair": pname, "e2": a["id"], "f0": b["id"],
                               "e2_shape": sa, "f0_shape": sb,
                               "e2_mid": max(pa[10:20]), "f0_mid": max(pb[10:20]),
                               "supports_h1": bool(ok)})
                    print(f"{pname:<8} {a['glyph']} {a['id']:<12}{sa:<6} "
                          f"{b['glyph']} {b['id']:<12}{sb:<6} "
                          f"{'H1 supported' if ok else 'H1 NOT supported'}")

        # ---- H2 ZWJ decomposition ----
        print("\nH2 — is 🐈‍⬛'s direction closer to 🐈 or to ⬛?")
        h2 = []
        if all(k in dirs for k in ("black_cat", "cat_plain", "black_sq", "cat_face")):
            print(f"{'layer':>5} {'cos(bcat,cat)':>14} {'cos(bcat,blacksq)':>18} "
                  f"{'cos(bcat,catface)':>18}  closer to")
            probe_layers = sorted({L for L in (0, 2, 5, 8, 11, 14, 16, 20, 24, NL - 1)
                                   if 0 <= L < NL})
            for L in probe_layers:
                c1 = cosv(dirs["black_cat"][L], dirs["cat_plain"][L])
                c2 = cosv(dirs["black_cat"][L], dirs["black_sq"][L])
                c3 = cosv(dirs["black_cat"][L], dirs["cat_face"][L])
                h2.append({"layer": L, "cos_cat_plain": c1, "cos_black_sq": c2,
                           "cos_cat_face": c3, "closer": "cat" if c1 > c2 else "black_square"})
                print(f"{L:>5} {c1:14.3f} {c2:18.3f} {c3:18.3f}  "
                      f"{'🐈 cat' if c1 > c2 else '⬛ black_square'}")

        (out / f"{args.tag}_hypotheses.json").write_text(
            json.dumps({"h1_pairs": h1, "h2_zwj": h2}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        meta["phases_run"].append({"phase": 2, "rows": len(rows2),
                                   "elapsed_s": round(time.time() - t0, 1)})
        (out / f"{args.tag}_meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\nphase 2 done in {time.time()-t0:.0f}s")

    meta["phases_run"].sort(key=lambda p: p["phase"])
    meta["total_elapsed_s"] = round(time.time() - t_all, 1)
    (out / f"{args.tag}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("\n" + "=" * 104)
    print(f"ALL DONE in {meta['total_elapsed_s']:.0f}s")
    print("=" * 104)
    be.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
