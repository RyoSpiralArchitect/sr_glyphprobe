# T14-X expansion and T14-C causal result

[日本語](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.ja.md) · [T14-X protocol](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md) · [T14-X analysis](EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.md) · [T14-C protocol](EMOJI_STEERING_CAUSAL_PATH_V0.md)

## Result in one paragraph

T14-X found a stable but **signed and model/depth-dependent** response-anisotropy regime, not a universal emoji-strength effect. All 12 model-by-depth JS intervals excluded zero, but nine were positive and three were negative. T14-C then prospectively localized one Llama 3.2 3B component and tested it once on a new untouched 192-target bank. The selected `mlp_out` block 24 passed every engineering control, but the registered treatment, necessity, and sufficiency intersection-union test did not reject. This is a completed negative causal result: the operational structured-versus-null response exists weakly on the new targets, but the selected component is not supported as its necessary and sufficient mediator.

| Stage | Fixed scope | Result |
|---|---:|---|
| T14-X acquisition | 6 base-model roles × 2 late depths | 559,488 response rows; 6/6 roles complete; 0 generation calls |
| T14-XA analysis | 7 complete exploratory families | 3,060 summary cells; 20,000 target-bootstrap replicates per cell |
| T14-C localization | 8 candidate sites + positive and sham controls | 25,600 records; `mlp_out` block 24 selected by the frozen rule |
| T14-C C1 v2 confirmation | 192 untouched targets, 12 strata | 15,360 records; causal IUT non-rejecting |

## The expansion found a signed regime

The X1 headline compares structured glyph prototypes with the pooled covariance-matched null at each model and depth. The sampling unit is the target prompt. Values below are median target-level JS differences with 20,000-replicate 95% bootstrap intervals.

| Model | Depth | Median JS excess | 95% interval | Sign class |
|---|---:|---:|:---:|---|
| Llama 3.2 3B base | 0.875 | +0.002838 | [0.001758, 0.003755] | positive |
| Llama 3.2 3B base | 1.0 | +0.006457 | [0.003712, 0.009787] | positive |
| OLMo 2 1B base | 0.875 | +0.006478 | [0.004045, 0.014886] | positive |
| OLMo 2 1B base | 1.0 | +0.008591 | [0.005243, 0.013730] | positive |
| Qwen 2.5 0.5B base | 0.875 | +0.010018 | [0.007638, 0.014669] | positive |
| Qwen 2.5 0.5B base | 1.0 | +0.009669 | [0.005644, 0.012085] | positive |
| Qwen 2.5 1.5B base | 0.875 | +0.001924 | [0.001399, 0.002638] | positive |
| Qwen 2.5 1.5B base | 1.0 | -0.011136 | [-0.013932, -0.007894] | negative |
| Qwen 2.5 3B base | 0.875 | -0.004870 | [-0.007635, -0.003734] | negative |
| Qwen 2.5 3B base | 1.0 | -0.010316 | [-0.013234, -0.006414] | negative |
| Qwen 2.5 7B base | 0.875 | +0.003066 | [0.002187, 0.003748] | positive |
| Qwen 2.5 7B base | 1.0 | +0.004370 | [0.003056, 0.006184] | positive |

The Qwen series is visibly non-monotonic: 0.5B is positive, 1.5B changes sign at the final depth, 3B is negative at both depths, and 7B is positive again. That pattern rules out a monotone scale reading of this grid. KL and total variation have the same nine-positive/three-negative interval classification, while argmax flips are mostly mixed. The stable result is therefore continuous distributional anisotropy, not a universal behavioral flip.

## The broader decomposition prevents a glyph-privilege claim

The complete JS families remained heterogeneous.

| Family | Positive | Negative | Mixed | Total |
|---|---:|---:|---:|---:|
| X1 structured vs covariance null | 9 | 3 | 0 | 12 |
| X2 glyph-system decomposition | 51 | 15 | 6 | 72 |
| X3 prototype source-form specificity | 89 | 104 | 71 | 264 |
| X4 item source-form specificity | 43 | 64 | 25 | 132 |
| X5 final-minus-late depth | 2 | 1 | 3 | 6 |
| X6 covariance-null family sensitivity | 6 | 3 | 3 | 12 |
| X7 sign orientation | 7 | 2 | 3 | 12 |

In the Llama 3.2 3B depth-0.875 cell later used for causal design, all six glyph systems were positive against the covariance null: atomic anchor `0.002406`, keycap `0.001110`, modifier `0.003731`, presentation `0.002654`, regional flag `0.002596`, and ZWJ `0.003665`. That supports using the cell as a broad operational response candidate. It does not make glyph surface form uniquely privileged. The X3 and X4 source-form contrasts contain more negative than positive intervals overall; modifier and ZWJ include strong glyph-over-name cases, while keycap glyph versus decomposed form can reverse.

Null construction and intervention sign also matter. X6 and X7 are not uniformly positive, which is why T14-C retained both covariance-null families and both signs instead of selecting the favorable side.

## The causal test closed negatively

T14-C was frozen before T14-X outcome access. The fixed Llama 3.2 3B cell used a `resid_post` block-23 intervention at depth 0.875 and magnitude 0.25. Localization compared `attn_out` and `mlp_out` at blocks 24–27 on the 32 public targets. The frozen selector ranked eligible sites by median target-level structured-minus-null necessity excess and selected `mlp_out` block 24 with score `0.0002628335`.

The localization controls passed:

- explicit-zero maximum JS was exactly `0`;
- restoration maximum JS and logit RMS were exactly `0`;
- the positive control had median necessity drop `0.01016544`;
- the upstream sham had median absolute necessity drop `0`.

Only after the selected-site manifest was committed was the C1 v2 bank materialized. It contained 192 untouched targets in 12 fixed strata. No target prompt bodies are stored in the public closeout. The one-shot confirmation used treatment, necessity, sufficiency, and restoration paths for 80 signed conditions per target.

| Registered component | Point estimate | 95% target bootstrap interval | One-sided sign-flip p | Practical floor | Pass |
|---|---:|:---:|---:|---:|---|
| Treatment | +0.00172230 | [0.00151002, 0.00190555] | 0.00001 | 0.0020 | no |
| Necessity | -0.00057689 | [-0.00061168, -0.00052984] | 1.0 | 0.0005 | no |
| Sufficiency | +0.00002126 | [0.00001144, 0.00003608] | 0.00001 | 0.0005 | no |

The treatment contrast is positive and stable, but it misses the prespecified practical floor. Necessity is stably negative rather than positive, and sufficiency is positive but about an order of magnitude below its floor. Because the registered claim was an intersection-union test, failure of any component is enough; here all three component rules fail. `confirmatory_claim_authorized` remains `false`.

This result must not be rescued by selecting the next site, lowering a floor, choosing a model subset, or changing the endpoint. A distributed, redundant, or suppressive downstream route is now a reasonable future hypothesis, but it was not tested by this protocol.

## Paper-gate update

- Phase I gate 4 is now complete: a targeted causal experiment finished under a public freeze, with a negative result.
- T14-X supplies broad exploratory boundary mapping, but not an independent confirmatory replication or a scale law; gate 5 remains open.
- T14-C uses target-cluster bootstrap and a fixed 99,999-draw paired sign-flip test, but the paper-wide statistical qualification still has to integrate all claim families.
- The full raw evidence archive and fresh-eyes paper review remain open. English and Japanese public documentation remain paired.

The clean next scientific move is not a same-bank rescue. It is to finish the paper claim table and archive, then—if pursued as future work—freeze a new multi-site or path-level intervention with a new untouched bank and an independent model or backend replication.

## Evidence anchors

| Evidence | Anchor |
|---|---|
| T14-X execution freeze | commit `14408a3` |
| T14-C causal freeze | commit `ff643ea`; manifest SHA-256 `9f3058c347cd1202ba12bf873b9896e919c7f8d2fde51028655c45c9c6c3a372` |
| T14-XA analysis freeze | commit `143e1be`; manifest SHA-256 `7f5403246aa23779d33922d9294e3556e7a35757cd62fc8185a5681feb3de6e2` |
| Selected-site binding | commit `2d11cb6`; manifest SHA-256 `9876695b24765e94d5eb1f5f42d394aecf42724da1c98d7f732efbe40d8c2240` |
| T14-XA full result | SHA-256 `cd012355867b32800a4815b20ade08d2738a5b0248418e8addd7f8283fa060a5` |
| Localization summary | SHA-256 `dd75ec378bd420dff7bb4e566a4b574c57fbe6437c1e581bce1cd74071f8e4ca` |
| C1 v2 bank / receipt | SHA-256 `6611a9fb1720a2bc55613c8e9ee12c290577f0a610ec1e8ccf98d39a2291c7fd` / `b42f96aa12c8f9b47eb683d6c61588d8a571f74829e66f5c7823b2d84ba7d613` |
| Confirmation summary | SHA-256 `8e6ed50eb1afa40d98144e04ff8092ca6ba7e3d2a23ee5c103ba26cdb2f41f12` |
| Exact causal analysis | [c1_v2_result.json](../validation/emoji_steering_causal_path_v0/c1_v2_result.json), SHA-256 `3ec6fa99a4ca161a9b3f6d1a7981940b7eb2a9860fa3272e031e2f35084a9f7a` |
| Combined closeout | [t14_closeout.json](../validation/emoji_steering_causal_path_v0/t14_closeout.json) |

The complete T14-XA result and raw run ledgers remain on the furnace at the paths recorded in the compact closeout. A repository closeout records their hashes; it is not a substitute for the still-open archival deposit gate.
