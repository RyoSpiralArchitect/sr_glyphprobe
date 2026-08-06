# Changelog

[Japanese / 日本語](CHANGELOG.ja.md)

## Unreleased — MLX acceleration and provenance hardening

- Added an Apple-silicon MLX-LM backend for full-sequence `resid_post` capture and
  activation intervention.
- Made unsupported MLX sites, attention output, generation, unsafe custom model
  arguments, and explicit dtype conversion of quantized models fail closed.
- Gated MLX activation patch capability on a SHA-256-pinned, same-model receipt
  that matches status, revision, dtype, site, current implementation, stable model
  identity, parity checks, and speed gate.
- Enforced the receipt's validated intervention-layer set at runtime while leaving
  capture-only calls and the private parity probe explicitly separate.
- Added a pinned GPT-2 FP32 parity validator with exact token, activation, logit,
  zero-hook, intervention-direction, intervention-magnitude, and synchronized
  end-to-end speed checks.
- Added path-independent model-artifact manifests and moved run-directory
  selection after backend load.
- Extended the run seal with dependency/runtime and stable loaded-model identity,
  preventing resume across runtime or model-manifest changes.
- Resolved the MLX validation receipt relative to its configuration file, matching
  the path semantics of panel, wrapper, and target inputs.
- Added `configs/v1_mlx_standard.yaml`, packaged starter resources, an MLX optional
  dependency group, and a complete-run artifact validator.
- Made readiness checks fail closed on missing or non-finite measurements and
  aligned every displayed criterion with the condition actually evaluated.
- Added a fail-closed compact public-bundle builder with included/omitted file
  hashes, cross-platform absolute-path rejection, and run/audit/parity coherence
  checks before any file is copied.
- Made failed artifact audits set `scientific_result: false` consistently with
  their status and decision.
- Validated the standard MLX matrix with 14,208 records, zero errors, 11/11
  readiness, and a separate 15/15 artifact audit with explicit caveats.
- Added frozen token-isomorphic E1 panels for five ten-emoji families, a
  tokenizer-only preflight, five role-bound MLX configs, and a dependence-aware
  descriptive analyzer that rebuilds LOTO prototypes inside each bootstrap.
- Completed all five E1 runs: 8,880 intervention rows, zero errors, and exact
  zero-hook activation/logit RMS of 0. The result showed broadly positive
  cross-family transfer, small family-specific excess, and heterogeneous random
  controls; it carries no p-value, confirmatory status, semantic, layer-specific,
  tokenizer-independent, or causal claim.
- Added a fail-closed E1 public-bundle builder and independent validator. The
  validated manifest binds 82 public payload members, inventories 20 omitted raw files,
  rejects local absolute paths, and records that P2 and C1 content was not used.
- Expanded the test suite for Milestone 2, E1 preflight, analysis, publication,
  and validation without hard-coding a revision-dependent test count.
- Established paired English/Japanese public documentation and the Phase I goal
  of a reproducible, falsifiable English-language paper.

## 0.1.0

Initial sealed pre-causal harness.

- Added the balanced 10-glyph color × shape panel.
- Added raw Transformers, TransformerLens, and deterministic mock backends.
- Added OpenAI-compatible adapters for vLLM, llama.cpp, Ollama, LM Studio, and
  generic endpoints.
- Added explicit capability receipts and surface-only fallback boundaries.
- Added wrapper-resampled direction replicates, panel centering, generic-emoji
  separation, RMS strength matching, global RMS clipping, sign flips, and random
  panel-span-orthogonal controls.
- Added distribution, activation, geometry, factor, fingerprint, latency,
  tokenization, and optional SAELens measurements.
- Added repeated group-stratified split-halves, within-target label permutations,
  cross-seed fingerprints, scalar-balance tables, dose response, sign-flip
  symmetry, and explicit zero-hook diagnostics.
- Added deterministic task IDs, resumable JSONL runs, input hashes, planning,
  backend/model matrices, and Markdown reports.
- Added a canonical component-site matrix for `resid_pre`, `attn_out`, `mlp_out`,
  and `resid_post`, plus exact per-wrapper tokenization receipts.
- Added packaged starter resources through `glyphprobe init` and sealed the
  installed Python source-tree hash into each run ID.
