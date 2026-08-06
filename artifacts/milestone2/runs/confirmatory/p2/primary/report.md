# GlyphProbe v1 Pre-stage Run Report

**Run:** `m2-p2-primary-colored-shapes-mlx--mlx--openai-community-gpt2--db21c21c4395d944`  
**Backend:** `mlx`  
**Model:** `openai-community/gpt2`  
**Stage:** `pre-causal-activation-screen`  
**Causal claim authorized:** `False`  
**Implementation hash:** `798b81559b0f2392248dd43d28d97e02039a49aa8459ba33c62dd7962c65e96d`

The report is deliberately a pre-stage map. Stable differences may justify sharper causal tests, but they do not identify a semantic mechanism by themselves.

## Run scale

- Emoji/glyphs: 10
- Source wrappers: 16
- Target cases: 48
- Replicate seeds: 3
- Intervention or observation records: 2976
- Errors: 0

## Principal pre-stage diagnostics

- Resolved layers: `[2, 4]`
- Median source-direction replicate alignment: 0.9768
- Median emoji fingerprint advantage over random controls: n/a
- Median within-target label-permutation screening p: n/a
- Cross-seed fingerprint advantage over random controls: n/a
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
- **PASS** `source_direction_stability`: 0.9768. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 48. At least 16 target prompt records are present.
- **HOLD** `random_direction_control`: 0. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 96, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **HOLD** `strength_dose_grid`: 1. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **HOLD** `fingerprint_reproducibility`: n/a. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **HOLD** `label_identity_permutation`: n/a. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **HOLD** `cross_seed_output_stability`: n/a. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 6 of 11 gates.

## Highest fingerprint separations

- Layer 2, strength 0.050, seed 101: emoji separation 0.9684; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [1.0463, 1.0463].
- Layer 2, strength 0.050, seed 211: emoji separation 1.0550; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [1.0459, 1.0459].
- Layer 2, strength 0.050, seed 307: emoji separation 1.0406; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [0.9648, 0.9648].
- Layer 4, strength 0.050, seed 101: emoji separation 0.9052; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [1.0544, 1.0544].
- Layer 4, strength 0.050, seed 211: emoji separation 0.9866; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [1.0388, 1.0388].
- Layer 4, strength 0.050, seed 307: emoji separation 1.0145; random separation n/a; advantage n/a; label-permutation p n/a; repeated-split 95% interval [1.0737, 1.0737].

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
