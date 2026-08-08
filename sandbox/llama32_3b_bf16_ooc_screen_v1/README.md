# Llama-3.2-3B bf16 — out-of-contract emoji fingerprint screen (v1)

[日本語](README.ja.md) · [Scientific contract](../../docs/SCIENTIFIC_CONTRACT.md) · [Sealed v2 protocol](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [Holdout status](../../docs/HOLDOUT_STATUS.md)

> ## ⚠️ OUT OF CONTRACT — this is NOT the sealed v2 experiment
> Everything in this directory is an **exploratory, out-of-contract** run. It is
> deliberately quarantined under `sandbox/` and is **not** part of the frozen
> scientific record. It touches nothing in `artifacts/`, `validation/`,
> `data/manifests/`, or the sealed v2 receipts, and it does **not** update,
> confirm, weaken, or reinterpret `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`.

## What this is

A scaled exploratory run of the GlyphProbe **internal intervention harness** on
the real, non-quantized **bf16 Llama-3.2-3B**, via the `transformers` backend on
Apple MPS in **FP32** — the same backend and weights the sealed v2 cell uses. It
was run to *see the real model run end-to-end through our own tooling* and to
produce a pre-causal activation screen, nothing more.

- Panel: `colored_shapes` (10 glyphs, has color×shape factor structure)
- 24 pre-stage targets · 16 source wrappers · 3 seeds · 3 strengths
- Layers `[5, 11]` (the same depths as v2, used here out of contract)
- 7,104 intervention/observation records, 0 errors, ~27 min on an M4 (MPS/FP32)

## What this is NOT

- **Not** the sealed v2 experiment, and not a reproduction of it (see *Environment*).
- **Not** a causal or semantic claim. The harness itself stamps this
  `pre-causal-activation-screen`, `Causal claim authorized: False`. Stable
  separations may justify sharper causal tests; they do not identify a mechanism
  or "emoji meaning."
- **Not** tokenizer-controlled: the source wrappers are not token-length matched
  across glyphs (`wrapper_tokenization_control` HOLDs), so tokenization remains a
  live confound.
- **Not** canonical provenance: run under non-frozen library versions and with an
  `orjson` stand-in (see below), so any receipt hashes here are **not** comparable
  to canonical GlyphProbe runs.

## Result summary (see `results/report.md`)

Readiness gates: **10 / 11 PASS** (only `wrapper_tokenization_control` HOLDs — a
property of the wrapper/panel data, not a knob).

| diagnostic | value |
|---|---|
| source-direction replicate stability | 0.9353 |
| zero-hook no-op (logit & activation Δ RMS) | exactly 0.0 |
| scalar RMS-ratio match error | ~1e-17 |
| KL dose monotonicity | 1.000 |
| sign-flip antisymmetry | 0.9947 |
| cross-seed fingerprint stability | 0.9952 |
| within-target label-permutation p (all cells) | 0.005 |

Emoji vs random-direction fingerprint **separation** (higher = more separable):

| layer | emoji (median) | random control (median) | advantage |
|---|---|---|---|
| **11** | 0.929 | 0.619 | **+0.32** |
| 5 | 0.654 | 0.790 | **−0.17** |

So the emoji-conditioned direction is more separable than a matched random
direction **at layer 11, but not at layer 5**, where the (seed-noisy) random
control usually wins. The `fingerprint_reproducibility` gate passes only
marginally (all-cell median advantage +0.0075) and is carried entirely by
layer 11.

## The chart

`chart/fp_chart.html` is a self-contained (CSP-safe) dumbbell chart of all 18
cells (layer × strength × seed), emoji ● vs random-control ○, grouped by layer,
with 95% split-half CIs, hover tooltips, a data table, and light/dark themes.
Its data is `chart/fp_chart_data.json` (derived from `results/fingerprint_summary.jsonl`).

## Environment & provenance

- **Weights: identical to the sealed v2 artifact.** `scripts/verify_bf16.py`
  recomputes the project's own `model_artifact_receipt` and confirms
  `mlx-community/Llama-3.2-3B-bf16` @ `60a99aaf…` = 9 files, 6,434,705,789 bytes,
  `manifest_sha256 dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`
  — byte-for-byte the frozen v2 model. All 254 parameter tensors run as `float32`.
- **Libraries differ from the freeze** (hence not a v2 reproduction): this ran on
  Python 3.12.6 / torch 2.12.1 / transformers 5.13.0 / numpy 2.2.3, whereas v2 is
  frozen at 3.13.13 / 2.11.0 / 4.57.6 / 2.4.4.
- **Shims** (`scripts/shim/`, used only via `PYTHONPATH`, nothing on disk patched):
  - `orjson.py` — a stdlib-`json` stand-in, because `orjson` is absent from the
    clean interpreter. Byte-equivalent for the ASCII manifest (the verify hash
    matches), but treat all other emitted hashes as non-canonical.
  - `sitecustomize.py` — makes transformers ≥5.13 tolerate mlx-lm's string-keyed
    tokenizer registration (only relevant to the MLX path).
- Runs used `PYTHONNOUSERSITE=1` to disable the machine's user-site
  "Spiralton" numpy/torch monkey-patch layer, so numerics are unpatched.

## Reproduce

Run from this directory (`sandbox/llama32_3b_bf16_ooc_screen_v1/`). Requires the
bf16 model in your HF cache and the `glyphprobe[torch]` deps importable.

```sh
export HF_HOME=~/.hf_home           # wherever the model is / should be cached
SNAP=$HF_HOME/hub/models--mlx-community--Llama-3.2-3B-bf16/snapshots/60a99aaf43164077157d64bf909b7b61143c6a6d

# 0) one-time download (lifts offline only for the fetch)
PYTHONNOUSERSITE=1 PSYCHOID_NET_GUARD=0 HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 \
  python3 -c "from huggingface_hub import snapshot_download as s; print(s('mlx-community/Llama-3.2-3B-bf16', revision='60a99aaf43164077157d64bf909b7b61143c6a6d'))"

# 1) verify the weights are identical to the frozen v2 artifact
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src SNAP=$SNAP \
  python3 scripts/verify_bf16.py

# 2) resid_post capture demo (emoji vs neutral)
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src SNAP=$SNAP \
  python3 scripts/capture_llama3b_bf16_transformers.py

# 3) the full scaled internal screen (writes to ../../../runs, gitignored)
PYTHONNOUSERSITE=1 PYTHONPATH=scripts/shim:../../src \
  python3 -m glyphprobe run -c configs/scaled_llama_bf16_transformers.yaml
```

`configs/smoke_llama_bf16_transformers.yaml` is a fast (1-seed, 1-strength) sanity variant.

## Contents

```
chart/     fp_chart.html, fp_chart_data.json      — the visualization + its data
scripts/   verify_bf16.py, capture_llama3b_bf16_transformers.py, shim/
configs/   scaled_… (produced the chart), smoke_… (fast sanity)
results/   report.md, summary.json, fingerprint_summary.jsonl, capture_bf16_summary.json
```

Raw run arrays (`*.npz`, `interventions.jsonl`) are intentionally **omitted** —
they are large and carry non-canonical provenance; regenerate them with step 3.
