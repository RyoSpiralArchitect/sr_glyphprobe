# E2 Llama 3.2 3B MPS emoji-transport protocol v1

[日本語](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.ja.md) · [E1 protocol](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) · [MLX numeric-screen result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [Holdout status](HOLDOUT_STATUS.md) · [Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol and analysis ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v1`

## Status and purpose

This document prospectively fixes a bounded Llama 3.2 3B emoji-transport study on the Transformers/MPS route. It asks whether the matched-slot output-fingerprint structure defined in E1 appears in one pinned larger-model cell, and whether the result is descriptively stable in a separately centered tokenizer-isomorphic sensitivity arm.

The scientific choices below must be public before the first study model forward. Freezing has two explicit stages. First, one public static-freeze commit binds this English/Japanese pair to the ten configurations, ten panel bindings, fixed analyzer, tests, exact environment and model artifact, preflight expectations, and checksum manifest; before that commit, status is `freeze_pending`. Second, the zero-model-forward tokenizer preflight must run from that clean pushed commit and its receipt must be published as the only changed file in a descendant commit. Execution remains `preflight_pending` until that receipt passes and is public. No other design, code, documentation, or input change is allowed between the static-freeze commit and execution.

This is an outcome-bearing but exploratory transport study. The 24 targets were already used in prior exploration. The study is not an independent-target confirmation, a causal experiment, a semantic test, or a clean isolation of model scale, tokenizer, architecture, backend, or arithmetic effects.

## Route selection and relationship to the MLX no-go

The preceding Stage-A3 engineering screen selected no MLX runtime dtype because both frozen candidates failed its machine-local speed gate. The present route is therefore specified as a new, separately versioned Transformers/MPS FP32 scientific cell under the two-stage freeze above. It is not an MLX fallback, a relaxation of the failed speed threshold, or a reinterpretation of the MLX result.

Stage A3 observed strong within-backend FP32 intervention fidelity on its engineering prompts, but it did not run the complete cross-backend parity families. This protocol neither promotes that observation to MLX qualification nor invokes MLX during the scientific grid. A future MLX study would require a new versioned engineering and scientific protocol.

## Fixed model, artifact, and runtime

| Field | Frozen value |
|---|---|
| Backend | `transformers` |
| Model | `mlx-community/Llama-3.2-3B-bf16` |
| Revision | `60a99aaf43164077157d64bf909b7b61143c6a6d` |
| Stored weight dtype | BF16 |
| Runtime parameter dtype | FP32 (`float32`) |
| Device | Apple Metal Performance Shaders (`mps`) |
| Loading | `local_files_only: true`, `trust_remote_code: false` |
| Tokenizer surface | `add_special_tokens: false`; no chat template or system prompt |
| Architecture identity | 28 layers, width 3,072, vocabulary 128,256, parameters 3,212,749,824 |
| Artifact identity | 9 files, 6,434,705,789 bytes |
| Artifact-manifest SHA-256 | `dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4` |

Runtime FP32 does not add information absent from the stored BF16 weights. Results must be described as a BF16 artifact evaluated with FP32 runtime parameters, not as an original FP32-weight model.

The executable freeze must also bind the exact environment used for execution. The qualified local reference environment is Python 3.13.13, `glyphprobe` 0.1.0, NumPy 2.4.4, PyTorch 2.11.0, Transformers 4.57.6, and macOS 26.2 on arm64. Any package, OS, hardware, model-file, or tokenizer-file difference requires a new versioned cell unless the public freeze explicitly binds that difference before outcomes are accessed. The final receipt records the complete environment, MPS availability, model-file hashes, tokenizer identity, resolved parameter dtype, and source-tree hash.

## Fixed data roles and holdout boundary

- Targets are exactly the first 24 ordered records of [`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl): four targets in each of `continuation`, `factual`, `reasoning`, `procedural`, `classification`, and `planning`.
- The selected targets are reused exploratory targets. They must never be called untouched, held out, or confirmatory.
- Records after the first 24 in that file are outside this protocol.
- Source contexts are exactly all 16 ordered records of [`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl).
- P2 and C1 are outside the executable and analysis surface. They must not be read, sampled, tokenized, model-forwarded, scored, or used for selection in this study.
- C1 v1 is retired after a research-context search exposure; it is not an untouched bank. The governing records are [Holdout status](HOLDOUT_STATUS.md) and the [machine-readable incident record](../validation/holdout_exposure_incidents/2026-08-07-repository-search.json).

The complete prestage file SHA-256 is `91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7`; the ordered first-24 selection SHA-256 is `26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b`; and the 16-wrapper file SHA-256 is `310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee`.

The freeze manifest binds ordered target IDs, group labels, ordered wrapper IDs, exact file hashes, and row limits. Appending records to either source file must not enlarge the study.

## Two separately centered arms

The two arms are separate executions, not one run followed by filtering.

| Arm | Active slots per family | Glyph count | Panel source | Role |
|---|---:|---:|---|---|
| `full50` | `slot_00`--`slot_09` | 50 | the five existing E1 10-glyph panels | Primary literal panel |
| `core35` | `slot_03`--`slot_09` | 35 | the five fixed E2 7-glyph panels | Tokenizer-isomorphic sensitivity arm |

The family order is `sky`, `food`, `animals`, `transport`, `social`. Family names are registry labels, not semantic variables established by the experiment.

The five `full50` configurations are:

- [`e2_llama32_3b_mps_full50_sky_v1.yaml`](../configs/e2_llama32_3b_mps_full50_sky_v1.yaml)
- [`e2_llama32_3b_mps_full50_food_v1.yaml`](../configs/e2_llama32_3b_mps_full50_food_v1.yaml)
- [`e2_llama32_3b_mps_full50_animals_v1.yaml`](../configs/e2_llama32_3b_mps_full50_animals_v1.yaml)
- [`e2_llama32_3b_mps_full50_transport_v1.yaml`](../configs/e2_llama32_3b_mps_full50_transport_v1.yaml)
- [`e2_llama32_3b_mps_full50_social_v1.yaml`](../configs/e2_llama32_3b_mps_full50_social_v1.yaml)

The five `core35` configurations are:

- [`e2_llama32_3b_mps_core35_sky_v1.yaml`](../configs/e2_llama32_3b_mps_core35_sky_v1.yaml)
- [`e2_llama32_3b_mps_core35_food_v1.yaml`](../configs/e2_llama32_3b_mps_core35_food_v1.yaml)
- [`e2_llama32_3b_mps_core35_animals_v1.yaml`](../configs/e2_llama32_3b_mps_core35_animals_v1.yaml)
- [`e2_llama32_3b_mps_core35_transport_v1.yaml`](../configs/e2_llama32_3b_mps_core35_transport_v1.yaml)
- [`e2_llama32_3b_mps_core35_social_v1.yaml`](../configs/e2_llama32_3b_mps_core35_social_v1.yaml)

### Llama tokenizer contract

The no-special-token raw glyph audit must verify the following exact contract before any study model forward:

- 47 of the 50 `full50` glyphs have three-token form `[9468, m_k, r_j]`;
- the family middle tokens (m_k), in fixed family order, are `234`, `235`, `238`, `248`, and `97`;
- for slots `00`--`09`, the ordinary third tokens (r_j) are `239`--`248`;
- the three two-token `full50` exceptions are `🌒 -> [9468, 102032]`, `🌓 -> [9468, 107569]`, and `🤑 -> [9468, 100701]`; and
- all 35 `core35` glyphs have exact form `[9468, m_k, r_j]`, with slots `03`--`09` using the shared third tokens `242`--`248`.

The audit also records code points, UTF-8 bytes, decoded round trips, raw token IDs, and each source-wrapper position profile. It fails closed on any mismatch, including a family-dependent wrapper token count, anchor, intervention position, or outside token.

The `core35` arm is tokenizer-isomorphic only for this pinned tokenizer and input construction. It does not remove tokenization as an explanation: family and middle-token identity remain confounded, while the first and matched third tokens are deliberately shared.

### Separate panel centering

For each arm, family, layer, and direction seed, the seed selects 12 of the 16 wrappers without replacement under the fixed `wrapper_subsample` implementation. Let \(\bar h_{a,k,j,s,l}\) be the source activation mean for arm \(a\), family \(k\), slot \(j\), seed \(s\), and layer \(l\). The intervention direction is

\[
d_{a,k,j,s,l}=\bar h_{a,k,j,s,l}-\frac{1}{|J_a|}\sum_{u\in J_a}\bar h_{a,k,u,s,l}.
\]

Thus `full50` centers each family over ten glyphs, while `core35` centers it anew over seven glyphs. Random directions are also generated against, and projected outside, the active arm's panel-direction span. A `core35` result may not be produced by subsetting `full50` fingerprints, directions, or random controls after execution.

The configured neutral glyph is `🟰`. Because `centroid_mode` is `panel`, it contributes to the source inventory and generic-emoji bookkeeping but is not the intervention centroid and its generic direction is not executed.

## Exact intervention and measurement cell

All ten configurations share the following cell:

| Component | Frozen value |
|---|---|
| Mode | internal activation intervention |
| Capture/intervention site | `resid_post` |
| Layers | `[5, 11]` |
| Position | `last_nonpad` for source anchor, capture, and intervention |
| Actual internal inputs | source: each fixed wrapper with `{emoji}` replaced by the glyph or `🟰`; target: the raw target `{prompt}` |
| Configured surface-only fields | emoji `{emoji}\n{prompt}`, neutral `{prompt}`, `system_prompt: null`; unused in internal mode |
| Attention capture | false |
| Operation | activation addition |
| Direction normalization | RMS |
| Strength | `0.05` only |
| Clipping | global RMS, maximum perturbation/target RMS ratio `0.25` |
| Direction seeds | `[101, 211, 307]` |
| Replicate rule | `wrapper_subsample`, fraction `0.75` = 12 of 16 wrappers |
| Run behavior | `resume: false`, `fail_fast: true`, `deterministic_torch: false`, resolved `max_errors: 10` |
| Random controls | 2 per layer and seed, projected outside the active panel span |
| Zero hook | enabled once per target and layer; integrity only |
| Disabled controls | sign flip, label shuffle, neutral direction, iso-KL, SAE |
| Output fingerprint | 96 dimensions, CountSketch seed `8675309`, saved |
| Distribution summaries | top-k `50`, RBO `p=0.90`, top logit deltas `32`, epsilon `1e-12` |
| Split-half diagnostic | 200 repeats |
| Generation | absent |

`targets.calibration_cases` remains resolved as 6, but iso-KL is disabled, so it creates no calibration forwards or endpoint. Layer 5 is the sole primary layer. Layer 11 is a prespecified secondary depth comparator, not a negative control. No other site, layer, strength, seed, fingerprint dimension, tokenizer, prompt surface, or generation setting is permitted in v1.

## Exact execution counts

Counts are fixed by the panels and cell above.

| Arm | Source forwards | Target baselines | Glyph interventions | Random controls | Zero hooks | Intervention-ledger rows | Total forwards |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full50` | 880 | 120 | 7,200 | 1,440 | 240 | 8,880 | 9,880 |
| `core35` | 640 | 120 | 5,040 | 1,440 | 240 | 6,720 | 7,480 |
| Total | 1,520 | 240 | 12,240 | 2,880 | 480 | 15,600 | 17,360 |

Per family, `full50` requires 1,976 forwards and 1,776 intervention rows; `core35` requires 1,496 forwards and 1,344 intervention rows. The grid consists of all ten family-by-arm runs. Missing, duplicate, or extra calls invalidate completeness; they do not authorize an adjusted denominator.

## Endpoint definitions

Let \(a\in\{\texttt{full50},\texttt{core35}\}\), let \(J_a\) be its ten or seven ordered slots, and let \(f_{a,k,j,t,s,l}\) be the unit-normalized 96-dimensional CountSketch of intervened-minus-baseline logits for arm \(a\), family \(k\), slot \(j\), target \(t\), direction seed \(s\), and layer \(l\). Let \(c(t)\) be the fixed target group.

Every prototype is leave-one-target-group-out (LOTO):

\[
q_{a,k,j,-c,s,l}=\operatorname{unit\_mean}
\{f_{a,k,j,u,s,l}:c(u)\ne c\}.
\]

For evaluation family \(f\) and prototype family \(g\), the matched-slot score is

\[
M_{a,f\leftarrow g,t,s,l}=\frac{1}{|J_a|}\sum_{j\in J_a}
\left[
\cos(f_{a,f,j,t,s,l},q_{a,g,j,-c(t),s,l})
-\frac{1}{|J_a|-1}\sum_{u\in J_a,u\ne j}
\cos(f_{a,f,j,t,s,l},q_{a,g,u,-c(t),s,l})
\right].
\]

The mismatch divisor is therefore 9 for `full50` and 6 for `core35`. Average the three direction seeds within each target:

\[
\bar M_{a,f\leftarrow g,t,l}=\frac{1}{3}\sum_s M_{a,f\leftarrow g,t,s,l}.
\]

Define family-specific excess over ordered cross-family transfer and the family-equal global value as

\[
R_{a,f,t,l}=\bar M_{a,f\leftarrow f,t,l}
-\operatorname{median}_{g\ne f}\bar M_{a,f\leftarrow g,t,l},
\qquad
R_{a,\mathrm{global},t,l}=\frac{1}{5}\sum_f R_{a,f,t,l}.
\]

Every reported target aggregate is the equal-target arithmetic mean over the 24 fixed targets. Direction seeds are repeated estimates nested inside a target, not independent observations. Families receive equal weight in \(R_{\mathrm{global}}\). Target medians and target-group means are secondary descriptions only.

## One-element primary criterion

The primary hypothesis family contains exactly one element:

`H_E2_1_full50_layer5_R_global_positive` (short label `H_E2_1`): the equal-target mean of \(R_{\mathrm{full50},\mathrm{global},t,5}\) is greater than zero.

The criterion is met only if the lower endpoint of its prespecified two-sided 95% percentile bootstrap interval is strictly greater than zero. Because the primary family has size one, no multiplicity correction is applied. The only allowed valid-complete statuses are:

- `transport_criterion_met`; or
- `transport_criterion_not_met`.

Neither status means `confirmed`, `robust`, `significant`, semantic, or causal. An invalid or incomplete grid receives no primary status.

## Bootstrap and paired analysis

Use exactly 20,000 stratified target-bootstrap replicates with seed `20260808`. Within each replicate, sample four targets with replacement inside each of the six fixed target groups. Reuse the same sampled target indices across both arms, all families, both layers, every endpoint, and every ordered family pair.

All data-dependent LOTO prototypes must be rebuilt inside every replicate from that replicate's resampled non-held-out groups. Reusing full-data prototypes inside the bootstrap is prohibited. Direction seeds remain nested within target and are averaged; they are not resampled or counted as independent units.

For every published cell, report the observed equal-target mean and the 2.5th and 97.5th percentiles of the 20,000 replicate means. The same paired replicates produce the descriptive target-level `core35 - full50` difference. That difference has no decision threshold and may not be called a fraction explained by tokenization.

## Required secondary and control outputs

The following are mandatory and non-rescuing:

1. `core35`, layer 5: \(R_{\mathrm{global}}\), all five \(R_f\), and the complete 5-by-5 \(M\) matrix.
2. Both arms, layer 11: the same outputs as a secondary depth comparator.
3. Both arms and both layers: every family-specific \(R_f\), every diagonal within-family \(M\), and all 20 ordered off-diagonal transfer cells.
4. The paired `core35 - full50` target-level difference for \(R_{\mathrm{global}}\), reported descriptively only.
5. Every arm-by-family-by-layer-by-seed random-control cell: 60 cells and 2,880 rows in total, retaining both random directions and all 24 target rows.
6. Every zero-hook row and per-run/per-layer maximum activation/logit delta RMS. Each of the 20 run/layer cells must have both maxima `<= 1e-6`; all 480 rows remain in the run artifacts, while every maximum and pass/fail value remains in the analysis receipt.
7. Direction wrapper selections, direction/scalar-balance summaries, perturbation-to-target RMS, clipping incidence, run errors, duplicate/missing task checks, and all configured distribution diagnostics.

The `core35` arm cannot rescue the `full50` primary criterion, and layer 11 cannot rescue layer 5. No favorable family, seed, random-control comparison, or target group may be promoted into the primary family. Secondary intervals are descriptive and receive no multiplicity-adjusted status.

## Preflight, execution, and stopping rules

Before the first model forward, a no-overwrite preflight must verify the public
freeze, fixed-source identity, ten configuration and panel hashes, ordered
targets and wrappers, tokenizer contract, complete local model-artifact hash,
AutoConfig architecture, frozen software environment, MPS availability,
requested FP32/MPS cell, implementation and analyzer hashes, and expected
counts. It loads no language-model weights and executes no forward. Each later
backend load must then verify every parameter's actual FP32 dtype before its
first forward. The launcher additionally requires a clean `main` worktree with
`HEAD == origin/main`, a preflight-audited ancestor whose only later tracked
change is the fixed preflight receipt, and no pre-existing run or launcher-log
namespace for any of the ten cells. Any failure stops the study before
scientific execution.

All ten configurations must run regardless of intermediate outcomes. The frozen order is `full50` then `core35`, with `sky`, `food`, `animals`, `transport`, and `social` inside each arm. Each configuration runs in a separate, strictly sequential Python process; two full models are never resident simultaneously. Outcome analysis begins only after all ten run receipts and ledgers are sealed. There is no outcome-based, wall-clock, speed-based, or convenience stopping rule. A hardware-safety or thermal interruption is treated as a technical interruption and recorded.

Immediately before the first process, the launcher publishes an immutable,
no-overwrite attempt-start receipt that binds the preflight, manifest, Git
authority, empty namespaces, cell order, and start time. A successful execution
receipt must bind that receipt by path and SHA-256. A catchable process failure
or interruption instead writes a separate no-overwrite failure receipt and
does not write the success receipt. An abrupt termination still leaves the
attempt-start receipt and unique launcher namespace as the incomplete marker.

A technical interruption does not resume v1. The partial evidence is retained
and marked incomplete. Any fresh attempt requires a new protocol version,
manifest, and destination frozen before execution; it may not overwrite or
reuse v1 rows. No result-triggered rerun, MLX fallback, replacement input,
threshold tuning, extra layer, extra strength, extra seed, new endpoint, or
selective exclusion is allowed.

Any code, configuration, panel, target, wrapper, tokenizer, model, environment,
or analysis change requires a new protocol version and destination. A
zero-hook threshold failure is an integrity failure. If integrity or
completeness fails, primary-status and analysis publication are blocked; the
run and launcher evidence remains preserved and is labelled invalid or
incomplete. Do not repair the v1 scientific record after inspecting outcomes.

## Artifact publication and no-overwrite contract

The public evidence root is [`artifacts/llama32_3b_mps_emoji_transport_v1/`](../artifacts/llama32_3b_mps_emoji_transport_v1/) with `preflight/`, `runs/`, and `analysis/` subdirectories. The tokenizer preflight is fixed at `preflight/tokenization_audit_v1.json`; the freeze manifest is [`data/manifests/llama32_3b_mps_emoji_transport_v1.json`](../data/manifests/llama32_3b_mps_emoji_transport_v1.json); and the launcher writes the future no-overwrite execution receipt to `validation/llama32_3b_mps_emoji_transport_v1/execution_receipt.json`. The ten local run directories must retain their complete receipts, resolved configurations and inputs, tokenizer records, plans, direction replicates, target baselines, raw intervention ledgers, fingerprint and scalar-balance summaries, reports, errors, and deviation records.

The Git-hosted bundle is compact by design. It copies every validated
non-large run file and the complete analysis, but omits each run's raw
`interventions.jsonl`, `source_activations.npz`, `directions.npz`, and
`target_baselines.npz`. A no-overwrite root manifest must bind every public
member and inventory every omitted local file by SHA-256, byte count, and
row count or array key/shape/dtype. These hashes prove which local artifacts
were analyzed but cannot reconstruct omitted data; exact reproduction remains
required for full replay.

The fixed analyzer publishes exactly these analysis files:

| File | Required rows or role | Unique key |
|---|---:|---|
| `panel_target_scores.jsonl` | 480 | `panel_arm`, family, layer, target ID |
| `transfer_target_scores.jsonl` | 1,920 | `panel_arm`, source family, prototype family, layer, target ID |
| `family_cell_summary.jsonl` | 20 | `panel_arm`, family, layer |
| `transfer_cell_summary.jsonl` | 80 | `panel_arm`, source family, prototype family, layer |
| `llama32_3b_mps_emoji_transport_receipt.json` | complete machine-readable decision and provenance | one receipt |
| `report.md` | for a valid complete grid, all primary, secondary, null, negative, and heterogeneous results; invalid or incomplete grids publish no analysis report | one report |

The 480 panel-target rows contain the five diagonal family cells for both arms, both layers, and 24 targets. The 1,920 transfer-target rows contain all 20 ordered off-diagonal pairs over the same arm/layer/target grid. Together they reconstruct every 5-by-5 matrix.

The publication manifest binds the bilingual protocol, ten panels/configurations, tokenizer preflight, analyzer, tests, source tree, model and environment identities, all ten run payloads, six analysis outputs, all deviations and errors, and every file checksum. Generated receipts and final analysis outputs are created in staging, schema- and identity-checked, and atomically renamed only when the final destination does not exist. They are never hand-edited, truncated, or overwritten. A rerun uses a new versioned destination.

## Claim boundary

If the primary criterion is met, the strongest permitted wording is:

> A prospectively frozen, Transformers/MPS-only Llama 3.2 3B FP32-runtime cell produced matched-slot output-fingerprint transport on 24 reused exploratory targets, with a separately centered tokenizer-isomorphic 35-glyph sensitivity arm.

If it is not met, the strongest permitted wording is:

> A prospectively frozen, Transformers/MPS-only Llama 3.2 3B FP32-runtime cell did not meet the prespecified matched-slot output-fingerprint transport criterion on 24 reused exploratory targets; the separately centered tokenizer-isomorphic 35-glyph arm remained a non-rescuing sensitivity analysis.

Even a positive result does not establish emoji semantics, semantic families, tokenizer independence, a family-independent glyph representation, independent-target confirmation, causal localization, generation behavior, backend-isolated replication, or a model-scale effect. E1 and E2 differ simultaneously in weights, tokenizer, vocabulary, architecture, backend, and arithmetic. The two E2 arms also differ in glyph composition, panel centering, mismatch set, and random-control span. Their difference is therefore not a tokenization-explained fraction. Because the arms share targets and wrappers, they are paired sensitivity analyses, not independent replications.

This study does not update C1 status, authorize a causal claim, or by itself close the Phase I replication or causality gates. All limitations, including C1 v1 retirement, remain in the final English paper and its evidence package.
