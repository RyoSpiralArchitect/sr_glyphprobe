# GlyphProbe v1 Pre-stage Run Report

**Run:** `m2-matched-null-c-exploratory-mlx--mlx--openai-community-gpt2--78505d4abbaea3bb`  
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
- Median source-direction replicate alignment: 0.9708
- Median emoji fingerprint advantage over random controls: 0.5384
- Median within-target label-permutation screening p: 0.0010
- Cross-seed fingerprint advantage over random controls: 0.9125
- Median maximum RMS-ratio matching error: 0.00000000
- Median KL dose monotonicity: 1.0000
- Median positive/negative fingerprint antisymmetry: 0.9996
- Maximum zero-hook logit-delta RMS: 0.0000000000
- Maximum zero-hook activation-delta RMS: 0.0000000000
- Raw glyph token counts: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`
- Wrapper token-count mismatch IDs: `[]`
- SAE analysis enabled: `False`
- Iso-KL calibration enabled: `False`

## Readiness gates

- **PASS** `tokenization_control`: [3]. All primary glyphs have the same raw token count.
- **PASS** `wrapper_tokenization_control`: []. Each sealed source wrapper has the same total token count across primary glyphs.
- **PASS** `source_direction_stability`: 0.9708. Median source-direction replicate alignment >= 0.50.
- **PASS** `target_case_count`: 24. At least 16 target prompt records are present.
- **PASS** `random_direction_control`: 1728. At least one random-direction control record is present.
- **PASS** `zero_hook_noop`: {'count': 96, 'max_logit_delta_rms': 0.0, 'max_activation_delta_rms': 0.0}. An explicit zero-vector hook changes neither the patched activation nor logits beyond 1e-6 RMS.
- **PASS** `strength_dose_grid`: 3. At least three positive strengths for dose-response inspection.
- **PASS** `scalar_strength_match`: 0.0000. Median maximum achieved-RMS-ratio error <= 1e-5.
- **PASS** `fingerprint_reproducibility`: 0.5384. Same-emoji held-out fingerprint similarity exceeds cross-emoji/random controls.
- **PASS** `label_identity_permutation`: 0.0010. Median within-target label-shuffle screening p-value <= 0.05; this is a screening flag, not a multiplicity-corrected global test.
- **PASS** `cross_seed_output_stability`: 0.9125. Same-glyph cross-seed fingerprint separation exceeds the random-direction null.

Passed 11 of 11 gates.

## Highest fingerprint separations

- Layer 4, strength 0.100, seed 307: emoji separation 0.6425; random separation -1.3859; advantage 2.0284; label-permutation p 0.0030; repeated-split 95% interval [0.6329, 0.9433].
- Layer 9, strength 0.050, seed 101: emoji separation 1.0085; random separation -0.3872; advantage 1.3957; label-permutation p 0.0010; repeated-split 95% interval [0.9787, 1.0694].
- Layer 2, strength 0.100, seed 101: emoji separation 1.0278; random separation 0.0242; advantage 1.0035; label-permutation p 0.0010; repeated-split 95% interval [0.7852, 1.0564].
- Layer 2, strength 0.025, seed 101: emoji separation 1.0211; random separation 0.0325; advantage 0.9886; label-permutation p 0.0010; repeated-split 95% interval [0.8826, 1.0819].
- Layer 7, strength 0.025, seed 307: emoji separation 1.0437; random separation 0.0894; advantage 0.9543; label-permutation p 0.0010; repeated-split 95% interval [0.9147, 1.0523].
- Layer 4, strength 0.100, seed 211: emoji separation 0.9657; random separation 0.0180; advantage 0.9476; label-permutation p 0.0010; repeated-split 95% interval [0.7370, 0.9918].
- Layer 2, strength 0.050, seed 101: emoji separation 0.9179; random separation 0.0148; advantage 0.9031; label-permutation p 0.0010; repeated-split 95% interval [0.8245, 1.0747].
- Layer 7, strength 0.050, seed 307: emoji separation 1.0353; random separation 0.1390; advantage 0.8962; label-permutation p 0.0010; repeated-split 95% interval [0.8917, 1.0413].
- Layer 2, strength 0.100, seed 211: emoji separation 0.9018; random separation 0.0261; advantage 0.8757; label-permutation p 0.0010; repeated-split 95% interval [0.7655, 1.0589].
- Layer 2, strength 0.050, seed 211: emoji separation 0.8891; random separation 0.0275; advantage 0.8615; label-permutation p 0.0010; repeated-split 95% interval [0.8100, 1.0672].

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
