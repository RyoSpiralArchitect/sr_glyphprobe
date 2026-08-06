# GlyphProbe v1 Pre-stage Run Report

**Run:** `e1-animals-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--c1872402b746bcc1`  
**Backend:** `mlx`  
**Model:** `openai-community/gpt2`  
**Stage:** `pre-causal-activation-screen`  
**Causal claim authorized:** `False`  
**Implementation hash:** `798b81559b0f2392248dd43d28d97e02039a49aa8459ba33c62dd7962c65e96d`

The report is deliberately a pre-stage map. Stable differences may justify sharper causal tests, but they do not identify a semantic mechanism by themselves.

## Run scale

- Emoji/glyphs: 10
- Source wrappers: 16
- Target cases: 24
- Replicate seeds: 3
- Intervention or observation records: 1776
- Errors: 0

## Principal pre-stage diagnostics

- Resolved layers: `[2, 4]`
- Median source-direction replicate alignment: 0.9746
- Median emoji fingerprint advantage over random controls: 0.7686
- Median within-target label-permutation screening p: n/a
- Cross-seed fingerprint advantage over random controls: 1.0099
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: n/a
- Median positive/negative fingerprint antisymmetry: n/a
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`
- Wrapper token-count mismatch IDs: `[]`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [3]. All primary glyphs have the same raw token count.
- **PASS** `wrapper_tokenization_control`: []. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9746. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 288. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 48, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **HOLD** `strength_dose_grid`: 1. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.7686. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **HOLD** `label_identity_permutation`: n/a. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 1.0099. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 9 of 11 gates.

## Highest fingerprint separations

- Layer 4, strength 0.050, seed 211: emoji separation 1.0049; random separation 0.0166; advantage 0.9883; label-permutation p n/a; repeated-split 95% interval [0.9122, 1.0649].
- Layer 4, strength 0.050, seed 307: emoji separation 1.0034; random separation 0.1614; advantage 0.8420; label-permutation p n/a; repeated-split 95% interval [0.7274, 1.0111].
- Layer 2, strength 0.050, seed 211: emoji separation 0.8970; random separation 0.0592; advantage 0.8377; label-permutation p n/a; repeated-split 95% interval [0.6292, 1.0140].
- Layer 2, strength 0.050, seed 101: emoji separation 0.6977; random separation -0.0018; advantage 0.6995; label-permutation p n/a; repeated-split 95% interval [0.5630, 0.9388].
- Layer 4, strength 0.050, seed 101: emoji separation 1.0434; random separation 1.9518; advantage -0.9084; label-permutation p n/a; repeated-split 95% interval [0.9554, 1.0639].
- Layer 2, strength 0.050, seed 307: emoji separation 0.8176; random separation 1.8607; advantage -1.0431; label-permutation p n/a; repeated-split 95% interval [0.6705, 1.0063].

## Artifact map

- `receipt.json`: model, backend, capability, hashes, and environment receipt
- `resolved_config.yaml`: sealed experiment configuration
- `plan.json`: estimated run matrix before execution
- `tokenization.jsonl`: raw glyph tokenization audit when locally available
- `source_activations.npz` and `directions.npz`: source-stage tensors
- `interventions.jsonl` or `surface_observations.jsonl`: condition-level records
- `fingerprint_summary.jsonl`: held-out target, random-control, factor, and permutation diagnostics
- `scalar_balance_summary.jsonl`: achieved intervention magnitude and output-displacement balance
- `dose_response_summary.jsonl`: monotonicity across the positive strength grid
- `sign_flip_summary.jsonl`: positive/negative local antisymmetry diagnostics
- `cross_seed_fingerprint_summary.jsonl`: output fingerprint stability across source-direction seeds
- `summary.json`: machine-readable pre-stage result
