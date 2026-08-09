#!/usr/bin/env python3
"""OUT-OF-CONTRACT per-glyph intervention sweep on the real bf16 Llama-3.2-3B
(transformers / MPS / FP32 — the same weights and backend as the sealed v2
cell, but NOT the v2 experiment and not a reproduction of it).

Question
--------
Taking each emoji ONE AT A TIME: how much does it actually move the model, and
is that because its direction is *special* or merely *large*?

Two quantities are recorded per glyph, and they answer different things.

A. prompt-level effect  (`prompt_kl`)
   KL( p(next | W)  ||  p(next | "<g>\\n" + W) ), averaged over wrappers W.
   "How much does simply prepending this emoji disturb the model?"
   Big dynamic range, but confounded by token count and token rarity.

B. magnitude-controlled causal push  (`injection_kl`)
   1. direction, averaged over EXTRACT_WRAPPERS so it is not one context's quirk
          d_g(L) = mean_i [ resid_post(L, "<g>\\n<W_i>") - resid_post(L, "<W_i>") ]
      captured at last_nonpad. The mean pairwise cosine of the per-wrapper
      deltas is stored as `direction_consistency`: a glyph whose direction only
      exists in one context shows up as a low value.
   2. RMS-matched injection into HELD-OUT targets (disjoint from the wrappers)
          v = d_g(L) / rms(d_g(L)) * alpha * rms(a_target(L))
      Every glyph is injected at the SAME perturbation-to-activation RMS ratio
      (= alpha), so a glyph with a bigger raw direction gets no free advantage.
   3. 介入量 = KL(baseline || intervened) over the next-token distribution,
      from the project's own analysis.metrics.distribution_metrics.

Controls
--------
zero-hook   v = 0 -> KL must be exactly 0.0 (the hook is a true no-op)
random dirs N gaussian directions, identically RMS-matched, per
            (layer, target, alpha) -> null KL; every glyph gets a z-score and
            an exceedance count against that null
dose        several alphas -> per-glyph KL dose monotonicity
tokens      the `matched` panel stratum is token-length matched (every glyph
            costs exactly 4 prefix tokens), so a within-stratum ranking is not
            a token-count artefact; the `ladder` stratum spans 2..16 prefix
            tokens precisely to measure what token count alone buys

Numerics note
-------------
numpy on macOS/Accelerate raises spurious "divide by zero / overflow / invalid
value encountered in matmul" RuntimeWarnings on large float64 dot products.
Verified spurious for this data: all activations and logits are finite and
`a @ b` is bit-identical to pure-Python summation (relative error exactly 0.0).
The filter below suppresses only that message.

Writes only inside this sandbox directory. Touches no runs/, no artifacts/,
no validation/, no data/manifests/, no sealed v2 receipt.
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
import yaml

from glyphprobe.analysis.metrics import activation_delta_metrics, distribution_metrics
from glyphprobe.backends.registry import create_backend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention

warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

EXTRACT_WRAPPERS = [
    "Today I saw a",
    "My favorite thing is",
    "Here we have",
    "This reminds me of",
]

INJECT_TARGETS = {
    "paris": "The capital of France is",
    "planet": "The largest planet in our solar system is",
    "openended": "I am thinking about",
}

METRIC_KW = dict(top_k=10, rbo_p=0.9, fingerprint_dim=96, fingerprint_seed=1234,
                 save_top_deltas=5, eps=1e-12)


def rms(x) -> float:
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


def cos(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def decode_deltas(backend, ids, values) -> list[list]:
    out = []
    for i, v in zip(ids, values):
        try:
            tok = backend.tokenizer.decode([int(i)])
        except Exception:
            tok = f"<{int(i)}>"
        out.append([tok, round(float(v), 4)])
    return out


def slim(dist: dict) -> dict:
    """Everything except the 96-d fingerprint (kept out to keep files small)."""
    return {k: v for k, v in dist.items() if k != "fingerprint"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", type=int, nargs="+", default=[5, 11, 16])
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.1, 0.5, 1.0])
    ap.add_argument("--primary-alpha", type=float, default=0.5)
    ap.add_argument("--random-controls", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None, help="first N glyphs (smoke)")
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default="sweep_v1")
    args = ap.parse_args()

    panel = yaml.safe_load((ROOT / "panel" / "sweep_panel_v1.yaml").read_text(encoding="utf-8"))
    glyphs = ([dict(r, stratum="matched") for r in panel["matched"]]
              + [dict(r, stratum="ladder") for r in panel["ladder"]])
    if args.limit:
        glyphs = glyphs[: args.limit]

    tnames = list(INJECT_TARGETS)
    pa = args.primary_alpha

    print("=" * 104)
    print("GlyphProbe OUT-OF-CONTRACT per-glyph intervention sweep")
    print("real bf16 Llama-3.2-3B | transformers/MPS/FP32 | pre-causal activation screen")
    print("=" * 104)
    print(f"extract wrappers : {EXTRACT_WRAPPERS}")
    print(f"inject targets   : {list(INJECT_TARGETS.values())}")
    print(f"layers {args.layers} | alphas {args.alphas} (primary {pa}) | "
          f"{len(glyphs)} glyphs | {args.random_controls} random controls")
    print("-" * 104)

    cfg = BackendConfig(kind="transformers", model=os.environ["SNAP"], revision=None,
                        device="mps", dtype="float32", local_files_only=True,
                        add_special_tokens=False, trust_remote_code=False)
    backend = create_backend(cfg)
    backend.load()
    print(f"device={getattr(backend,'device',None)} num_layers={backend.num_layers} "
          f"model_dim={backend.model_dim}")

    def fwd(prompt, layers, intervention=None):
        return backend.forward(prompt, capture_layers=layers, site="resid_post",
                               position="last_nonpad", intervention=intervention)

    # ---- baselines ----------------------------------------------------------
    wrap_base, wrap_ntok = {}, {}
    for w in EXTRACT_WRAPPERS:
        r = fwd(w, args.layers)
        wrap_base[w] = {"act": {L: np.asarray(r.activations[L], dtype=np.float64)
                                for L in args.layers},
                        "logits": r.logits}
        wrap_ntok[w] = len(r.token_ids)

    tgt_base, tgt_top1 = {}, {}
    for name, prompt in INJECT_TARGETS.items():
        r = fwd(prompt, args.layers)
        tgt_base[name] = {"act": {L: np.asarray(r.activations[L], dtype=np.float64)
                                  for L in args.layers},
                          "logits": r.logits}
        tgt_top1[name] = backend.tokenizer.decode([int(np.argmax(r.logits))])
        print(f"target {name:<10} {prompt!r:<46} {len(r.token_ids)} tok  "
              f"top-1 {tgt_top1[name]!r}")
    print("-" * 104)

    rows: list[dict] = []
    t0 = time.time()

    def inject(name, L, vec, label):
        return fwd(INJECT_TARGETS[name], [L],
                   Intervention(layer=L, vector=np.asarray(vec, dtype=np.float32),
                                site="resid_post", position="last_nonpad", label=label))

    def measure(name, L, vec, r):
        return (distribution_metrics(tgt_base[name]["logits"], r.logits, **METRIC_KW),
                activation_delta_metrics(tgt_base[name]["act"][L], r.activations[L], vec))

    # ---- control: zero hook -------------------------------------------------
    print("control | zero-hook (KL must be exactly 0.0)")
    zero_ok = True
    for L in args.layers:
        z = np.zeros(backend.model_dim, dtype=np.float32)
        parts = []
        for name in tnames:
            r = inject(name, L, z, "zero_hook_control")
            dist, act = measure(name, L, z, r)
            kl = dist["kl_base_to_intervened"]
            zero_ok &= (kl == 0.0)
            parts.append(f"{name}={kl:.1e}")
            rows.append({"kind": "control_zero", "id": "zero_hook", "glyph": None,
                         "family": "control", "stratum": "control", "layer": L,
                         "target": name, "alpha": 0.0,
                         "activation": act, "distribution": slim(dist)})
        print(f"  L{L:<2} " + "  ".join(parts) + ("   OK" if zero_ok else "   NON-ZERO!"))

    # ---- control: random directions per (layer, target, alpha) --------------
    print(f"control | {args.random_controls} random directions per (layer, target, alpha)")
    null: dict[tuple[int, str, float], list[float]] = {}
    for L in args.layers:
        for a in args.alphas:
            parts = []
            for name in tnames:
                tgt_rms = rms(tgt_base[name]["act"][L])
                vals = []
                for s in range(args.random_controls):
                    rng = np.random.default_rng(90_000 + 1000 * L + s)
                    draw = rng.standard_normal(backend.model_dim)
                    vec = draw / rms(draw) * a * tgt_rms
                    r = inject(name, L, vec, f"random_s{s}")
                    dist, act = measure(name, L, vec, r)
                    vals.append(dist["kl_base_to_intervened"])
                    rows.append({"kind": "control_random", "id": f"random_s{s}",
                                 "glyph": None, "family": "control", "stratum": "control",
                                 "layer": L, "target": name, "alpha": a,
                                 "seed": 90_000 + 1000 * L + s,
                                 "scale": {"target_activation_rms": tgt_rms,
                                           "perturbation_rms": rms(vec),
                                           "perturbation_to_target_rms": rms(vec) / tgt_rms},
                                 "activation": act, "distribution": slim(dist)})
                null[(L, name, a)] = vals
                parts.append(f"{name} med={np.median(vals):.4f}")
            print(f"  L{L:<2} a={a:<4} " + " | ".join(parts))
    print("-" * 104)

    # ---- per-glyph sweep ----------------------------------------------------
    kh = " ".join(f"{'L'+str(L):>8}" for L in args.layers)
    print(f"{'#':>3} {'g':<3} {'id':<13} {'fam':<9} {'tok':>3} {'promptKL':>9} "
          f"{kh}  {'best/null':>9} {'cons':>5}  top-boosted")
    mismatches = []
    for i, item in enumerate(glyphs, 1):
        g = item["glyph"]

        # --- extraction over wrappers (also gives the prompt-level effect) ---
        deltas = {L: [] for L in args.layers}
        prompt_kls, prompt_rel = [], {L: [] for L in args.layers}
        n_prefix = None
        for w in EXTRACT_WRAPPERS:
            r = fwd(f"{g}\n{w}", args.layers)
            npx = len(r.token_ids) - wrap_ntok[w]
            n_prefix = npx if n_prefix is None else n_prefix
            pd = distribution_metrics(wrap_base[w]["logits"], r.logits, **METRIC_KW)
            prompt_kls.append(pd["kl_base_to_intervened"])
            for L in args.layers:
                d = np.asarray(r.activations[L], dtype=np.float64) - wrap_base[w]["act"][L]
                deltas[L].append(d)
                prompt_rel[L].append(float(np.linalg.norm(d)
                                           / (np.linalg.norm(wrap_base[w]["act"][L]) + 1e-12)))
        if n_prefix != item["n_prefix_tokens"]:
            mismatches.append((item["id"], item["n_prefix_tokens"], n_prefix))
        prompt_kl = float(np.mean(prompt_kls))

        show, ratio_by_layer = [], []
        boosted_show = []
        for L in args.layers:
            per_w = deltas[L]
            consistency = float(np.mean([cos(x, y) for x, y in combinations(per_w, 2)]))
            d_vec = np.mean(per_w, axis=0)
            d_rms = rms(d_vec)

            rows.append({"kind": "glyph_direction", "id": item["id"], "glyph": g,
                         "family": item["family"], "stratum": item["stratum"],
                         "layer": L, "n_prefix_tokens": n_prefix,
                         "direction_consistency": consistency,
                         "direction_rms": d_rms,
                         "prompt_kl_mean": prompt_kl,
                         "prompt_kl_per_wrapper": [float(v) for v in prompt_kls],
                         "prompt_rel_delta_mean": float(np.mean(prompt_rel[L])),
                         "prompt_rel_delta_per_wrapper": prompt_rel[L]})

            kl_primary, dose_by_target = [], []
            for name in tnames:
                tgt_rms = rms(tgt_base[name]["act"][L])
                per_alpha = []
                for a in args.alphas:
                    vec = d_vec / max(d_rms, 1e-12) * a * tgt_rms
                    r = inject(name, L, vec, f"{item['id']}_L{L}_{name}_a{a}")
                    dist, act = measure(name, L, vec, r)
                    kl = dist["kl_base_to_intervened"]
                    per_alpha.append(kl)

                    nulls = np.array(null[(L, name, a)])
                    boosted = decode_deltas(backend, dist["top_positive_delta_ids"],
                                            dist["top_positive_delta_values"])
                    if a == pa and L == args.layers[-1] and name == "paris":
                        boosted_show = boosted
                    if a == pa:
                        kl_primary.append(kl)

                    rows.append({
                        "kind": "glyph_injection", "id": item["id"], "glyph": g,
                        "family": item["family"], "stratum": item["stratum"],
                        "layer": L, "target": name, "alpha": a,
                        "n_prefix_tokens": n_prefix,
                        "direction_consistency": consistency,
                        "prompt_kl_mean": prompt_kl,
                        "scale": {"target_activation_rms": tgt_rms,
                                  "direction_raw_rms": d_rms,
                                  "requested_strength": a,
                                  "perturbation_rms": rms(vec),
                                  "perturbation_to_target_rms": rms(vec) / tgt_rms},
                        "null": {"mean": float(nulls.mean()),
                                 "sd": float(nulls.std(ddof=1)),
                                 "median": float(np.median(nulls)),
                                 "z": float((kl - nulls.mean()) / max(nulls.std(ddof=1), 1e-12)),
                                 "ratio_to_null_median": float(kl / max(np.median(nulls), 1e-12)),
                                 "n_null_ge_observed": int(np.sum(nulls >= kl)),
                                 "n_null": int(nulls.size)},
                        "activation": act,
                        "distribution": slim(dist),
                        "baseline_top1": tgt_top1[name],
                        "intervened_top1": backend.tokenizer.decode(
                            [int(dist["intervened_argmax"])]),
                        "top_boosted": boosted,
                        "top_suppressed": decode_deltas(
                            backend, dist["top_negative_delta_ids"],
                            dist["top_negative_delta_values"]),
                        "latency_ms": r.latency_ms})

                dose_by_target.append(all(x < y for x, y in zip(per_alpha, per_alpha[1:])))

            mean_primary = float(np.mean(kl_primary))
            null_med = float(np.median([np.median(null[(L, n, pa)]) for n in tnames]))
            show.append(mean_primary)
            ratio_by_layer.append(mean_primary / max(null_med, 1e-12))

        best = int(np.argmax(ratio_by_layer))
        kl_str = " ".join(f"{v:8.4f}" for v in show)
        cons_best = float(np.mean([cos(x, y)
                                   for x, y in combinations(deltas[args.layers[best]], 2)]))
        top3 = " ".join(repr(t) for t, _ in boosted_show[:3])
        print(f"{i:>3} {g:<3} {item['id']:<13} {item['family']:<9} {n_prefix:>3} "
              f"{prompt_kl:9.4f} {kl_str}  {ratio_by_layer[best]:9.2f} {cons_best:5.2f}  {top3}")

    dt = time.time() - t0
    print("-" * 104)
    print("panel token counts: " + ("ALL MATCH" if not mismatches else f"MISMATCH {mismatches}"))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = out_dir / f"{args.tag}_records.jsonl"
    with rec.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "claim_stage": "pre-causal-activation-screen",
        "causal_claim_authorized": False,
        "out_of_contract": True,
        "extract_wrappers": EXTRACT_WRAPPERS,
        "inject_targets": INJECT_TARGETS,
        "target_baseline_top1": tgt_top1,
        "layers": args.layers, "alphas": args.alphas, "primary_alpha": pa,
        "random_controls": args.random_controls,
        "n_glyphs": len(glyphs), "n_records": len(rows),
        "zero_hook_exact_noop": bool(zero_ok),
        "null_kl": {f"L{L}_{n}_a{a}": {"median": float(np.median(null[(L, n, a)])),
                                       "mean": float(np.mean(null[(L, n, a)])),
                                       "sd": float(np.std(null[(L, n, a)], ddof=1)),
                                       "max": float(np.max(null[(L, n, a)])),
                                       "n": len(null[(L, n, a)])}
                    for L in args.layers for n in tnames for a in args.alphas},
        "panel_token_mismatches": mismatches,
        "elapsed_s": round(dt, 1),
        "backend": "transformers/mps/fp32",
        "model_path": os.environ["SNAP"],
        "numerics_note": ("macOS/Accelerate emits spurious matmul FPE RuntimeWarnings; "
                          "verified spurious (all values finite, a@b bit-identical to "
                          "pure-Python summation)"),
    }
    (out_dir / f"{args.tag}_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"records : {rec} ({len(rows)} rows)")
    print(f"meta    : {out_dir / f'{args.tag}_meta.json'}")
    print(f"elapsed : {dt:.0f}s")
    print("=" * 104)
    backend.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
