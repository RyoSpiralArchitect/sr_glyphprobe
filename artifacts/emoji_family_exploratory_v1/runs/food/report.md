# GlyphProbe v1 Pre-stage Run Report

**Run:** `e1-food-token-isomorphic-exploratory-mlx--mlx--openai-community-gpt2--ec228b7a9eb2d540`  
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
- Median source-direction replicate alignment: 0.9749
- Median emoji fingerprint advantage over random controls: 0.8435
- Median within-target label-permutation screening p: n/a
- Cross-seed fingerprint advantage over random controls: 1.0728
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
- **PASS** `source_direction_stability`: 0.9749. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 288. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 48, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **HOLD** `strength_dose_grid`: 1. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.8435. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **HOLD** `label_identity_permutation`: n/a. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 1.0728. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 9 of 11 gates.

## Highest fingerprint separations

- Layer 4, strength 0.050, seed 211: emoji separation 0.9466; random separation 0.0179; advantage 0.9286; label-permutation p n/a; repeated-split 95% interval [0.9537, 1.0611].
- Layer 2, strength 0.050, seed 211: emoji separation 0.9197; random separation 0.0405; advantage 0.8792; label-permutation p n/a; repeated-split 95% interval [0.6619, 1.0028].
- Layer 4, strength 0.050, seed 307: emoji separation 1.0414; random separation 0.1959; advantage 0.8455; label-permutation p n/a; repeated-split 95% interval [0.8177, 1.0574].
- Layer 2, strength 0.050, seed 101: emoji separation 0.8471; random separation 0.0057; advantage 0.8415; label-permutation p n/a; repeated-split 95% interval [0.6818, 0.9631].
- Layer 4, strength 0.050, seed 101: emoji separation 1.0356; random separation 1.9570; advantage -0.9213; label-permutation p n/a; repeated-split 95% interval [0.8387, 1.0559].
- Layer 2, strength 0.050, seed 307: emoji separation 0.8662; random separation 1.8678; advantage -1.0016; label-permutation p n/a; repeated-split 95% interval [0.8145, 1.0357].

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
