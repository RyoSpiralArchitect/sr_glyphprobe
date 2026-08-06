# Milestone 2 confirmatory analysis report

Analysis ID: `glyphprobe-m2-tokenization-controls-v1`

## Primary results

| Layer | Mean adjusted target effect | 95% stratified bootstrap CI | Raw sign-flip p | Holm-adjusted p | Status |
|---:|---:|:---:|---:|---:|:---|
| 2 | 0.20836302 | [0.13746333, 0.27689337] | 0.0007199928 | 0.0014399856 | robust to the prespecified matched controls |
| 4 | -0.03294653 | [-0.07610848, 0.01100937] | 0.9995 | 0.9995 | unresolved |

The minimally meaningful excess is `delta = 0.06`. The interval is a percentile cluster bootstrap that resamples targets within each of the six frozen groups. The one-sided sign-flip screen is applied to `D[t] - delta`; Holm correction covers the two primary layers.

## Evidence hashes

| Role | Intervention ledger SHA-256 | Resolved config SHA-256 | Run receipt SHA-256 | Resolved inputs SHA-256 |
|:---|:---|:---|:---|:---|
| primary_colored_shapes | `a331800295f1a9a8ca03f5b857d88f5e5be5f4bc73ef8ed8834fdc867b52a371` | `f514cfffb2b73d1447ca890be1b043ec886f85cd9158155c0c56cbd381f46303` | `c9caa07ca90a9683950bb2c64372324a71b8bae977ecf527ec51553190844d74` | `3b8a103ce192baffc888238c62ffc0ff34a04572aa783cbe79ede9b680ac2318` |
| matched_null_a | `d89750921c2c20fa02924e6d205d93c6a6c6a42d82558103b6a43a4026de0658` | `98108dcea51737c58549f50fe44754acec2ecc35cb0477cf1773b0e3558c2b69` | `8274766dd6ed8c7f56e17865a9d9e058c99ce73877b97268ce95cf6b430603bf` | `fe5b80907f61bb90a75b8eaed09a71cd29f83fe92ee20ae3d91b4e71d152caf5` |
| matched_null_b | `31751cacf0216f73e6ab77f1c3bdc5195ff2a622849ad22a4406bde1ee8cde6d` | `51bb1d28ccccca3a7147ac9a59b23e8e8d6f797e7cf0a2aa95fecb42ec9df819` | `9fa1a1d7a8a452ad8f4c64a1d6562ef7944607ec79dc0a1f2b237eb7a9b085a1` | `51e89f33d3ce3ae8b5bcc3aebe514e9fc656e8ac50f19963d9e688bb1a715b84` |
| matched_null_c | `f4d97cfe87e6ddb0b194aa5dd4a95a5590748fc29111aa74c48f5d7d2465db31` | `0d495fd75f26b8524426ce203c2d01457ca6d4ce86e830c196cdf1b37a5d6ba7` | `8095bce184a48e7c92f56d54ec32847c2dfec5b38438f1b27b76f9bde0f0e28d` | `be77056b9e80445ec32827e7c39f14497c6a89f60903bb34f2a62f011df536c2` |

Target effects: `0879a504b5b922a7682107f65f19872bcd4f0469f5606b9a7410ccea352e5320` (96 layer-target rows).

## Independence and claim boundaries

- The effective observation unit is a target. Direction seeds are averaged within each target and do not increase sample size.
- Conditions, null panels, bootstrap replicates, and sign-flip draws are not independent observations.
- A robust result supports robustness only to the prespecified token-count and token-prefix matched controls. It is not a tokenization-free, semantic, mechanistic, or causal glyph effect.
- Practical equivalence is restricted to this endpoint, margin, frozen bank, and matched-null ensemble. It does not prove that tokenization caused the exploratory result.
- Failure to pass either rule remains unresolved and is not evidence of absence.

This report is generated from the frozen ledgers. Do not edit it by hand.
