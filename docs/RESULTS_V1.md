# GlyphProbe v1 results

[日本語](RESULTS_V1.ja.md) · [README](../README.md) · [Roadmap](ROADMAP.md)

## Result in one sentence

In one pinned GPT-2 FP32 `resid_post` cell, glyph-derived activation additions produced a reproducible output-fingerprint candidate under the bundled controls, while substantial cell-level heterogeneity and unresolved tokenization confounds keep the result strictly pre-causal.

This document reports what the current artifacts support. It does not assign semantic meaning to a direction, locate a circuit, or establish a causal path.

## Evidence boundary

| Item | Fixed scope |
|---|---|
| Model | `openai-community/gpt2` |
| Revision | `607a30d783dfa663caf39e06633721c8d4cfcd7e` |
| Backend used for the standard run | MLX/MLX-LM on Apple silicon |
| Precision | FP32 |
| Intervention object | full-sequence decoder-block `resid_post` addition |
| Layers | 2, 4, 7, 9 |
| Primary glyphs | 10, balanced as 5 colors × 2 shapes |
| Target prompts | 24, four in each of six groups |
| Source wrappers | 16 |
| Direction-estimation seeds | 3 |
| Positive strengths | 0.025, 0.05, 0.10 target-activation RMS |
| Full standard records | 14,208 |

The full pipeline was executed on MLX. Cross-backend parity was checked on a predefined adapter-level matrix, not by duplicating all 14,208 records on Transformers/MPS.

## MLX qualification

The [MLX parity receipt](../validation/mlx_gpt2_parity/receipt.json) covers four prompt lengths and the four standard layers, producing 16 prompt–layer cells and 80 checks in total.

The 80/80 passing gates cover:

- exact tokenizer ID equality;
- baseline logits and exact baseline argmax;
- baseline `resid_post` activations at all four capture layers;
- exact zero-hook no-op behavior;
- changed activations and logits after a fixed non-zero intervention;
- logit-delta NRMSE, cosine, and RMS-ratio gates;
- actual activation-delta fidelity to the injected vector.

The receipt's synchronized end-to-end benchmark includes tokenization, capture or intervention, lazy-device evaluation, and NumPy transfer. In the recorded environment and load state, aggregate median latency was 17.517 ms for Transformers/MPS and 10.727 ms for MLX, a 1.633× speedup. This is a cell-specific engineering measurement, not a general claim about MLX, PyTorch, other models, or other sequence lengths.

Any change to model, revision, dtype, quantization, component site, or implementation invalidates this qualification until a new receipt is generated.

## Standard-run integrity

The standard run completed and recorded:

- 14,208 intervention/control rows, matching the plan;
- 11,520 primary-glyph rows;
- 864 generic-glyph rows;
- 1,728 panel-span-orthogonal random-control rows;
- 96 explicit zero-hook rows;
- no recorded errors;
- 14,208 unique, recomputable task IDs;
- exact zero-hook activation and logit RMS deltas of 0;
- 11/11 pre-causal readiness gates passed.

The [artifact audit](../validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json) passed 15/15 checks. It independently recomputed the headline metrics and checked input and implementation hashes, row counts, task IDs, required fields, finite values, target uniqueness, token counts, and readiness consistency.

## Headline measurements

| Measurement | Value |
|---|---:|
| Median source-direction replicate alignment | 0.9705 |
| Median held-out glyph fingerprint advantage | 0.6075 |
| Median cross-seed fingerprint advantage | 0.9308 |
| Median maximum scalar mismatch | `1.39 × 10⁻¹⁷` |
| Median KL dose monotonicity | 1.0000 |
| Median sign antisymmetry | 0.9997 |
| Median within-target permutation screening p | `1/1001` |

The fingerprint advantage compares same-glyph held-out similarity against cross-glyph and random-direction controls. It is not a measure of glyph meaning.

## Heterogeneity is part of the result

The median alone is incomplete. Of the 36 layer–seed–strength cells, 25 were positive and 11 were non-positive.

| Layer | Median advantage | Minimum | Maximum |
|---:|---:|---:|---:|
| 2 | 0.8680 | -0.8471 | 1.0106 |
| 4 | 0.6139 | -1.2188 | 2.5023 |
| 7 | 0.3649 | -0.6243 | 1.0147 |
| 9 | 0.4201 | -1.0632 | 0.8186 |

Every layer median was positive, but no layer was uniformly positive. The largest positive row is not used as the headline because random-control separation is broad. The predefined three-IQR diagnostic flagged no extreme rows, and no cell was excluded. The robust descriptive headline is the across-cell median together with the positive rate and full range. All 12 cross-seed layer–strength aggregates were positive, but that aggregation does not turn source-direction seeds into independent observations.

## Permutation screen

All 36 cells reached the finite Monte Carlo floor of `1/1001`. This indicates that the observed label assignment was extreme relative to the particular within-target permutation screen used here. It is **not** a multiplicity-corrected global significance result, does not account for every researcher degree of freedom, and does not establish semantic or causal interpretation.

A confirmatory analysis must predefine a smaller hypothesis family, treat target prompts as sampling clusters, and report family-wise or false-discovery control as appropriate.

## Tokenization qualification

All ten primary glyphs tokenize to three tokens, and the sealed source wrappers preserve primary-glyph length balance. However:

- the ten primary token sequences are distinct;
- the blue-circle sequence has a different middle-token pattern from the other primary sequences;
- the neutral `·` glyph is one token rather than three.

The run therefore controls primary token count but does not isolate a tokenization-free visual or semantic factor. The neutral comparison in particular contains a token-length asymmetry. A follow-up should add length- and token-prefix-matched controls and, where possible, cross-tokenizer or byte-level constructions.

## What passed readiness means

Passing 11/11 gates means the artifact is internally consistent enough to justify a targeted causal follow-up. It does not mean that all cells were positive, that the glyph factors were decoded, or that a mechanism was identified. The generated summary explicitly records:

```text
causal_claim_authorized: false
stage: pre-causal-readiness-only
```

## What was not run

- iso-KL calibration;
- SAELens feature analysis;
- sequence generation outcomes;
- `resid_pre`, `attn_out`, or `mlp_out` intervention matrices;
- component or path patching;
- ablation and restoration;
- checkpoint-emergence analysis;
- cross-model replication;
- a full 14,208-row Transformers/MPS duplicate.

These are missing measurements, not null results.

## Public artifact policy

The compact repository evidence package retains receipts, summaries, reports, compact metric tables, and a file manifest. It intentionally omits the approximately 74 MiB (77.3 MB) raw `interventions.jsonl` ledger and model-dependent NPZ arrays. Consequently, the public snapshot supports inspection of reported aggregates but is not the complete paper-grade archive. The sealed full run must be retained or deposited separately before archival publication.

## Authorized conclusion

The current artifacts support this limited statement:

> Under one pinned GPT-2 FP32 `resid_post` setup, the tested glyph-derived directions produced a reproducible output-fingerprint candidate across held-out prompts and separately estimated source directions, relative to the bundled controls.

They do not support claims about semantic meaning, a model-internal glyph concept, a specific circuit, a causal path, universality across models, or downstream generation behavior.
