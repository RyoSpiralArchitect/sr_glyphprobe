# Milestone 2 confirmatory analysis report

Analysis ID: `glyphprobe-m2-tokenization-controls-v1`

## Primary results

| Layer | Mean adjusted target effect | 95% stratified bootstrap CI | Raw sign-flip p | Holm-adjusted p | Status |
|---:|---:|:---:|---:|---:|:---|
| 2 | 0.18750669 | [0.12548917, 0.24765946] | 0.0019699803 | 0.0039399606 | robust to the prespecified matched controls |
| 4 | -0.08637903 | [-0.15924636, -0.01691702] | 0.99943001 | 0.99943001 | unresolved |

The minimally meaningful excess is `delta = 0.06`. The interval is a percentile cluster bootstrap that resamples targets within each of the six frozen groups. The one-sided sign-flip screen is applied to `D[t] - delta`; Holm correction covers the two primary layers.

## Evidence hashes

| Role | Intervention ledger SHA-256 | Resolved config SHA-256 | Run receipt SHA-256 | Resolved inputs SHA-256 |
|:---|:---|:---|:---|:---|
| primary_colored_shapes | `56e535819b3a63cc173df1a4b7442fc5c2e7a8c24cf699153d1e55cd17f96361` | `b0453d7725e319ca3f78d6c66350db854619a910adcccabcdf1f8d83f9991838` | `ee7a73b37fc29fd5b131bbfde6820e4766440c04b334f47b4796d8da4542d9b0` | `58cec5b5f957bc1c9fa45a84b6c5ca561aa893e76dcb53d9d984f87f8462c737` |
| matched_null_a | `8a7d6f4d94035be5e4b2da4c2339c6b2c006f3f623cc2cd0d8fa1ebebef1088c` | `38fa29079b9802b2a45cef095dfae937ffddf4d941e7179f801ce97b10271b57` | `6c7aa59e9a060df7615cddda68261c1cf9dd1df1ea8ca5747ac0e1160496d205` | `d12d17529f099732957e19d41bfb89e31685a4ed30d9444bb8a9501314cc1d66` |
| matched_null_b | `c1f82f4e4186e62b7caaa521ead87e4a1ab59dd4ef6ecd15cff5cbcbc2505ab6` | `9d0308103edf7de6a822fdce1b457abe2dfd4a5f110a918d27f2e0bff878accd` | `874594af91451b7c35267cfbf403be0562d356389fb03b068b3d96b0f633ef54` | `41289b09a1021565b38a087a8c9447e89f142ece0a4f29f754ef78c2ab131010` |
| matched_null_c | `19a2fd9341a067215e281c4eff9a243e4ec0cee3dd7464051703112a6c75a9dc` | `7315fd07e494c6a80dc9e66b0bdfa45a61ba6bde48ce3b0aec0305cbdeaa863f` | `f9359215cd4450283aaffec7ccef72d9d7581cfdb9aec3157562367ef1c6251b` | `513971fc104e6139ab7f337a0608dd219dc52360ec64597dedbe7406f8b0f296` |

Target effects: `124511bb57e2254b1ca3ca0437ac40aa274ac11a3439bc3022ce126ae34a7dd7` (96 layer-target rows).

## Independence and claim boundaries

- The effective observation unit is a target. Direction seeds are averaged within each target and do not increase sample size.
- Conditions, null panels, bootstrap replicates, and sign-flip draws are not independent observations.
- A robust result supports robustness only to the prespecified token-count and token-prefix matched controls. It is not a tokenization-free, semantic, mechanistic, or causal glyph effect.
- Practical equivalence is restricted to this endpoint, margin, frozen bank, and matched-null ensemble. It does not prove that tokenization caused the exploratory result.
- Failure to pass either rule remains unresolved and is not evidence of absence.

This report is generated from the frozen ledgers. Do not edit it by hand.
