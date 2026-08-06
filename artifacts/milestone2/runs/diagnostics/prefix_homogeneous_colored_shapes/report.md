# GlyphProbe v1 Pre-stage Run Report

**Run:** `m2-prefix-homogeneous-colored-shapes-exploratory-mlx--mlx--openai-community-gpt2--7fdfb6b7f642986e`  
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
- Intervention or observation records: 14208
- Errors: 0

## Principal pre-stage diagnostics

- Resolved layers: `[2, 4, 7, 9]`
- Median source-direction replicate alignment: 0.9709
- Median emoji fingerprint advantage over random controls: 0.6010
- Median within-target label-permutation screening p: 0.0010
- Cross-seed fingerprint advantage over random controls: 0.8852
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: 1.0000
- Median positive/negative fingerprint antisymmetry: 0.9995
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`
- Wrapper token-count mismatch IDs: `[]`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [3]. All primary glyphs have the same raw token count.
- **PASS** `wrapper_tokenization_control`: []. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9709. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 1728. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 96, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **PASS** `strength_dose_grid`: 3. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.6010. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **PASS** `label_identity_permutation`: 0.0010. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 0.8852. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 11 of 11 gates.

## Highest fingerprint separations

- Layer 4, strength 0.100, seed 307: emoji separation 0.9655; random separation -1.3837; advantage 2.3492; label-permutation p 0.0010; repeated-split 95% interval [0.9129, 0.9915].
- Layer 4, strength 0.025, seed 211: emoji separation 0.9765; random separation 0.0452; advantage 0.9313; label-permutation p 0.0010; repeated-split 95% interval [0.8602, 1.0188].
- Layer 9, strength 0.050, seed 307: emoji separation 1.0904; random separation 0.1621; advantage 0.9283; label-permutation p 0.0010; repeated-split 95% interval [1.0358, 1.0960].
- Layer 9, strength 0.025, seed 307: emoji separation 1.0454; random separation 0.1218; advantage 0.9237; label-permutation p 0.0010; repeated-split 95% interval [1.0554, 1.0999].
- Layer 7, strength 0.025, seed 307: emoji separation 1.0940; random separation 0.1767; advantage 0.9173; label-permutation p 0.0010; repeated-split 95% interval [1.0565, 1.1006].
- Layer 4, strength 0.050, seed 211: emoji separation 0.9189; random separation 0.0293; advantage 0.8895; label-permutation p 0.0010; repeated-split 95% interval [0.7887, 0.9897].
- Layer 7, strength 0.050, seed 307: emoji separation 1.0857; random separation 0.2160; advantage 0.8697; label-permutation p 0.0010; repeated-split 95% interval [1.0290, 1.0985].
- Layer 4, strength 0.100, seed 211: emoji separation 0.8454; random separation 0.0205; advantage 0.8249; label-permutation p 0.0010; repeated-split 95% interval [0.7554, 0.9542].
- Layer 9, strength 0.050, seed 101: emoji separation 1.0672; random separation 0.2806; advantage 0.7865; label-permutation p 0.0010; repeated-split 95% interval [0.9303, 1.0770].
- Layer 4, strength 0.050, seed 307: emoji separation 0.9918; random separation 0.2426; advantage 0.7492; label-permutation p 0.0010; repeated-split 95% interval [0.9196, 1.0150].

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
