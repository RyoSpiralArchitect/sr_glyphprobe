# GlyphProbe v1 Pre-stage Run Report

**Run:** `m2-matched-null-b-exploratory-mlx--mlx--openai-community-gpt2--367e0af26c88d1fc`  
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
- Median source-direction replicate alignment: 0.9743
- Median emoji fingerprint advantage over random controls: 0.5755
- Median within-target label-permutation screening p: 0.0010
- Cross-seed fingerprint advantage over random controls: 1.0150
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: 1.0000
- Median positive/negative fingerprint antisymmetry: 0.9997
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`
- Wrapper token-count mismatch IDs: `[]`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [3]. All primary glyphs have the same raw token count.
- **PASS** `wrapper_tokenization_control`: []. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9743. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 1728. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 96, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **PASS** `strength_dose_grid`: 3. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.5755. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **PASS** `label_identity_permutation`: 0.0010. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 1.0150. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 11 of 11 gates.

## Highest fingerprint separations

- Layer 4, strength 0.100, seed 307: emoji separation 0.9254; random separation -1.3337; advantage 2.2591; label-permutation p 0.0010; repeated-split 95% interval [0.8123, 1.0042].
- Layer 2, strength 0.050, seed 211: emoji separation 1.0406; random separation 0.0291; advantage 1.0115; label-permutation p 0.0010; repeated-split 95% interval [0.7534, 1.0512].
- Layer 2, strength 0.025, seed 211: emoji separation 1.0114; random separation 0.0279; advantage 0.9835; label-permutation p 0.0010; repeated-split 95% interval [0.7195, 1.0472].
- Layer 9, strength 0.025, seed 307: emoji separation 1.0382; random separation 0.0620; advantage 0.9763; label-permutation p 0.0010; repeated-split 95% interval [1.0311, 1.0519].
- Layer 9, strength 0.050, seed 307: emoji separation 1.0429; random separation 0.0924; advantage 0.9506; label-permutation p 0.0010; repeated-split 95% interval [1.0223, 1.0462].
- Layer 4, strength 0.025, seed 211: emoji separation 0.9727; random separation 0.0263; advantage 0.9464; label-permutation p 0.0010; repeated-split 95% interval [0.7440, 0.9707].
- Layer 4, strength 0.050, seed 211: emoji separation 0.9446; random separation 0.0180; advantage 0.9266; label-permutation p 0.0010; repeated-split 95% interval [0.7123, 0.9764].
- Layer 9, strength 0.050, seed 101: emoji separation 1.0384; random separation 0.1419; advantage 0.8965; label-permutation p 0.0010; repeated-split 95% interval [1.0102, 1.0503].
- Layer 2, strength 0.100, seed 211: emoji separation 0.8961; random separation 0.0396; advantage 0.8565; label-permutation p 0.0010; repeated-split 95% interval [0.7449, 1.0538].
- Layer 9, strength 0.100, seed 307: emoji separation 1.0155; random separation 0.1780; advantage 0.8375; label-permutation p 0.0010; repeated-split 95% interval [0.9888, 1.0271].

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
