#!/usr/bin/env python3
"""OUT-OF-CONTRACT capture demo on the REAL bf16 Llama-3.2-3B via the project's
transformers backend on MPS/FP32 (the same backend the sealed v2 uses). No
intervention here — just resid_post capture, emoji vs neutral. Mirrors the 4-bit
MLX demo so the two are directly comparable. Touches no runs/, no v2 receipts.
"""
from __future__ import annotations

import json
import os

import numpy as np

from glyphprobe.config import BackendConfig
from glyphprobe.backends.registry import create_backend

MODEL_PATH = os.environ["SNAP"]
CAPTURE_LAYERS = [2, 4, 5, 8, 11, 16, 24]
TARGET = "The capital of France is"
EMOJIS = [("🚀", "transport"), ("🍎", "food"), ("🐶", "animal")]


def cos(a, b):
    a = a.astype(np.float64); b = b.astype(np.float64)
    with np.errstate(all="ignore"):
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def topk(backend, logits, k=5):
    idx = np.argsort(logits)[::-1][:k]
    out = []
    for i in idx:
        try:
            tok = backend.tokenizer.decode([int(i)])
        except Exception:
            tok = f"<{int(i)}>"
        out.append((repr(tok), round(float(logits[i]), 2)))
    return out


def main() -> int:
    print("=" * 76)
    print("GlyphProbe resid_post capture — REAL bf16 Llama-3.2-3B, transformers/MPS/FP32")
    print("(OUT OF CONTRACT smoke — same weights & backend as sealed v2, not v2)")
    print("=" * 76)
    cfg = BackendConfig(
        kind="transformers", model=MODEL_PATH, revision=None,
        device="mps", dtype="float32", local_files_only=True,
        add_special_tokens=False, trust_remote_code=False,
    )
    backend = create_backend(cfg)
    backend.load()
    caps = backend.capabilities()
    enabled = sorted(c.value for c, on in caps.capabilities.items() if on)
    print(f"device={getattr(backend,'device',None)} | num_layers={backend.num_layers} "
          f"| model_dim={backend.model_dim}")
    print(f"capabilities (on): {enabled}")
    print(f"ACTIVATION_PATCH available: {'activation_patch' in enabled}  "
          "(transformers backend enables it unconditionally)")
    print("-" * 76)

    fr0 = backend.forward(TARGET, capture_layers=CAPTURE_LAYERS, site="resid_post",
                          position="last_nonpad")
    print(f"neutral: {TARGET!r}")
    print(f"  tokens: {fr0.tokens}")
    print(f"  next-token top5: {topk(backend, fr0.logits)}")
    print(f"  latency: {fr0.latency_ms:.0f} ms")
    print("-" * 76)

    summary = {"model_path": MODEL_PATH, "backend": "transformers/mps/fp32",
               "target": TARGET, "capture_layers": CAPTURE_LAYERS, "arms": []}
    for glyph, fam in EMOJIS:
        prompt = f"{glyph}\n{TARGET}"
        fr = backend.forward(prompt, capture_layers=CAPTURE_LAYERS, site="resid_post",
                             position="last_nonpad")
        print(f"emoji {glyph} ({fam})  prompt={prompt!r}")
        print(f"  next-token top5: {topk(backend, fr.logits)}")
        per = {}
        for L in CAPTURE_LAYERS:
            a = fr.activations[L]; b = fr0.activations[L]
            c = cos(a, b)
            rel = float(np.linalg.norm(a.astype(np.float64) - b.astype(np.float64))
                        / (np.linalg.norm(b.astype(np.float64)) + 1e-12))
            per[L] = {"cos": round(c, 4), "rel_delta": round(rel, 4)}
            tag = "  <- v2 layer" if L in (5, 11) else ""
            print(f"    L{L:<2} cos={c:+.4f}  rel|Δ|={rel:.4f}{tag}")
        summary["arms"].append({"glyph": glyph, "family": fam, "layers": per})
        print("-" * 76)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "capture_bf16_summary.json")
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("summary written:", out)
    print("=" * 76)
    print("OK: real bf16 Llama-3B captured via transformers/MPS/FP32, offline.")
    backend.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
