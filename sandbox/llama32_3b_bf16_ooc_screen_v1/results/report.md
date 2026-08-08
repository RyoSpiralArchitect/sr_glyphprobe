# GlyphProbe v1 Pre-stage Run Report

**Run:** `scaled-llama3b-bf16-transformers-ooc--transformers--Users-ryospiralarchitect-.hf_home-hub-mo--80bc6b167cdb5728`  
**Backend:** `transformers`  
**Model:** `/Users/ryospiralarchitect/.hf_home/hub/models--mlx-community--Llama-3.2-3B-bf16/snapshots/60a99aaf43164077157d64bf909b7b61143c6a6d`  
**Stage:** `pre-causal-activation-screen`  
**Causal claim authorized:** `False`  
**Implementation hash:** `f8d7407ecc4bb5d40e000446e655af139d231fc45f11df732e59582f48c252aa`

The report is deliberately a pre-stage map. Stable differences may justify sharper causal tests, but they do not identify a semantic mechanism by themselves.

## Run scale

- Emoji/glyphs: 10
- Source wrappers: 16
- Target cases: 24
- Replicate seeds: 3
- Intervention or observation records: 7104
- Errors: 0

## Principal pre-stage diagnostics

- Resolved layers: `[5, 11]`
- Median source-direction replicate alignment: 0.9353
- Median emoji fingerprint advantage over random controls: 0.0075
- Median within-target label-permutation screening p: 0.0050
- Cross-seed fingerprint advantage over random controls: 0.9952
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: 1.0000
- Median positive/negative fingerprint antisymmetry: 0.9947
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`
- Wrapper token-count mismatch IDs: `['w01_mark_anchor', 'w03_pipe_next', 'w04_token_state', 'w06_binary_result', 'w10_sequence_continuation', 'w12_list_next', 'w13_left_right', 'w14_codepoint_text', 'w15_observation_inference']`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [3]. All primary glyphs have the same raw token count.
- **HOLD** `wrapper_tokenization_control`: ['w01_mark_anchor', 'w03_pipe_next', 'w04_token_state', 'w06_binary_result', 'w10_sequence_continuation', 'w12_list_next', 'w13_left_right', 'w14_codepoint_text', 'w15_observation_inference']. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9353. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 864. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 48, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **PASS** `strength_dose_grid`: 3. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.0075. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **PASS** `label_identity_permutation`: 0.0050. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 0.9952. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 10 of 11 gates.

## Highest fingerprint separations

- Layer 11, strength 0.025, seed 307: emoji separation 0.9287; random separation 0.5386; advantage 0.3901; label-permutation p 0.0050; repeated-split 95% interval [0.8836, 0.9519].
- Layer 11, strength 0.050, seed 307: emoji separation 0.9428; random separation 0.5539; advantage 0.3889; label-permutation p 0.0050; repeated-split 95% interval [0.8928, 0.9513].
- Layer 11, strength 0.100, seed 307: emoji separation 0.9251; random separation 0.5690; advantage 0.3561; label-permutation p 0.0050; repeated-split 95% interval [0.8850, 0.9512].
- Layer 11, strength 0.050, seed 101: emoji separation 0.9513; random separation 0.6186; advantage 0.3326; label-permutation p 0.0050; repeated-split 95% interval [0.9120, 0.9666].
- Layer 11, strength 0.100, seed 101: emoji separation 0.9480; random separation 0.6248; advantage 0.3233; label-permutation p 0.0050; repeated-split 95% interval [0.9028, 0.9636].
- Layer 11, strength 0.025, seed 101: emoji separation 0.9397; random separation 0.6193; advantage 0.3204; label-permutation p 0.0050; repeated-split 95% interval [0.9052, 0.9659].
- Layer 5, strength 0.025, seed 307: emoji separation 0.6553; random separation 0.5122; advantage 0.1431; label-permutation p 0.0050; repeated-split 95% interval [0.5719, 0.6832].
- Layer 5, strength 0.050, seed 307: emoji separation 0.6497; random separation 0.5095; advantage 0.1402; label-permutation p 0.0050; repeated-split 95% interval [0.5636, 0.6737].
- Layer 5, strength 0.100, seed 307: emoji separation 0.6747; random separation 0.5937; advantage 0.0810; label-permutation p 0.0050; repeated-split 95% interval [0.5635, 0.6808].
- Layer 11, strength 0.100, seed 211: emoji separation 0.9148; random separation 0.9808; advantage -0.0659; label-permutation p 0.0050; repeated-split 95% interval [0.8713, 0.9298].

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
