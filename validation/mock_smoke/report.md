# GlyphProbe v1 Pre-stage Run Report

**Run:** `glyphprobe-v1-smoke--mock--glyphprobe-mock-64d--19a5d40d5d537277`  
**Backend:** `mock`  
**Model:** `glyphprobe/mock-64d`  
**Stage:** `pre-causal-activation-screen`  
**Causal claim authorized:** `False`  
**Implementation hash:** `798b81559b0f2392248dd43d28d97e02039a49aa8459ba33c62dd7962c65e96d`

The report is deliberately a pre-stage map. Stable differences may justify sharper causal tests, but they do not identify a semantic mechanism by themselves.

## Run scale

- Emoji/glyphs: 10
- Source wrappers: 6
- Target cases: 6
- Replicate seeds: 2
- Intervention or observation records: 1314
- Errors: 0

## Principal pre-stage diagnostics

- Resolved layers: `[2, 4, 5]`
- Median source-direction replicate alignment: 0.9938
- Median emoji fingerprint advantage over random controls: 0.1319
- Median within-target label-permutation screening p: 0.0099
- Cross-seed fingerprint advantage over random controls: 1.0684
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: 1.0000
- Median positive/negative fingerprint antisymmetry: 1.0000
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[1, 1, 1, 1, 1, 1, 1, 1, 1, 1]`
- Wrapper token-count mismatch IDs: `[]`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [1]. All primary glyphs have the same raw token count.
- **PASS** `wrapper_tokenization_control`: []. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9938. Median source-direction replicate alignment >= 0.50.
- **HOLD** `target_case_count`: 6. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 144. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 18, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **HOLD** `strength_dose_grid`: 2. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.1319. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **PASS** `label_identity_permutation`: 0.0099. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 1.0684. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 9 of 11 gates.

## Highest fingerprint separations

- Layer 5, strength 0.030, seed 211: emoji separation 1.1057; random separation 0.6781; advantage 0.4276; label-permutation p 0.0099; repeated-split 95% interval [1.1057, 1.1057].
- Layer 5, strength 0.080, seed 211: emoji separation 1.1057; random separation 0.6784; advantage 0.4273; label-permutation p 0.0099; repeated-split 95% interval [1.1057, 1.1057].
- Layer 4, strength 0.080, seed 211: emoji separation 1.1068; random separation 0.7580; advantage 0.3488; label-permutation p 0.0099; repeated-split 95% interval [1.1068, 1.1068].
- Layer 4, strength 0.030, seed 211: emoji separation 1.1068; random separation 0.7583; advantage 0.3485; label-permutation p 0.0099; repeated-split 95% interval [1.1068, 1.1068].
- Layer 4, strength 0.080, seed 101: emoji separation 1.1072; random separation 0.8796; advantage 0.2276; label-permutation p 0.0099; repeated-split 95% interval [1.1072, 1.1073].
- Layer 4, strength 0.030, seed 101: emoji separation 1.1073; random separation 0.8797; advantage 0.2275; label-permutation p 0.0099; repeated-split 95% interval [1.1072, 1.1073].
- Layer 5, strength 0.080, seed 101: emoji separation 1.1071; random separation 1.0708; advantage 0.0363; label-permutation p 0.0099; repeated-split 95% interval [1.1071, 1.1071].
- Layer 5, strength 0.030, seed 101: emoji separation 1.1071; random separation 1.0711; advantage 0.0360; label-permutation p 0.0099; repeated-split 95% interval [1.1071, 1.1071].
- Layer 2, strength 0.030, seed 101: emoji separation 1.1086; random separation 1.0897; advantage 0.0189; label-permutation p 0.0099; repeated-split 95% interval [1.1086, 1.1087].
- Layer 2, strength 0.080, seed 101: emoji separation 1.1086; random separation 1.0902; advantage 0.0185; label-permutation p 0.0099; repeated-split 95% interval [1.1086, 1.1087].

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
