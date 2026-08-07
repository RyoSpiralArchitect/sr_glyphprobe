# Phase I paper outline

[日本語](PAPER_OUTLINE.ja.md) · [Roadmap](ROADMAP.md) · [E2 MPS transport protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1.md) · [Holdout status](HOLDOUT_STATUS.md) · [E1 exploratory results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md)

## Working title

**From Glyph Directions to Output Fingerprints: A Controlled Pre-Causal Study in GPT-2**

The Phase I manuscript will be written in English. A Japanese public summary will accompany the preprint, but the English manuscript is the controlling scientific text.

## Proposed central claim

Under a pinned GPT-2 FP32 MLX `resid_post` setup, the layer-2 colored-shape fingerprint score retained a positive excess over three prespecified token-count and prefix-panel matched controls on a frozen 48-target bank under two source-wrapper constructions. Frozen v1 classified both layer-2 arms as robust to those controls; layer 4 was unresolved in both arms. This is a mixed pre-causal result, not a tokenization-free, semantic, mechanistic, or model-general claim.

This wording is provisional. The v1 role-binding and fixed-prototype bootstrap qualifications must be resolved prospectively before the manuscript freezes its final confirmatory claim.

## Current Milestone 2 claim table

| Arm | Layer | Frozen v1 result | Post-hoc rebuilt-prototype sensitivity | Manuscript treatment now |
|---|---:|---|---|---|
| primary source | 2 | +0.208363; 95% CI [0.137463, 0.276893]; Holm p = 0.00143999; robust | [0.099930, 0.295380] | positive candidate; do not upgrade post-hoc interval to confirmation |
| primary source | 4 | -0.0329465; [-0.0761085, 0.0110094]; unresolved | [-0.099995, 0.041902] | unresolved negative/mixed evidence |
| independent source | 2 | +0.187507; [0.125489, 0.247659]; Holm p = 0.00393996; robust | [0.104210, 0.271322] | source-construction robustness, not independent target/model replication |
| independent source | 4 | -0.086379; [-0.159246, -0.016917]; unresolved | [-0.185084, 0.007648] | unresolved negative/mixed evidence |

The post-hoc analysis rebuilds all leave-one-target-group-out prototypes inside each joint target-bootstrap replicate. It assigns no p-value or status and does not overwrite v1. Exact independent-source values and limitations remain tied to the published sensitivity receipts.

## Current secondary-diagnostic table

Both 14,208-row diagnostic runs completed with zero errors, zero-hook activation/logit RMS of 0, and readiness 11/11. Their random-adjusted headline `emoji_fingerprint_advantage` values were +0.751225 for suffix matching and +0.601038 for prefix homogenization. These headline values are not the raw separation scores in the table below.

| CountSketch dimension | Standard minus suffix raw separation, median | Standard minus prefix-homogeneous raw separation, median |
|---:|---:|---:|
| 96 | +0.002624 | +0.022096 |
| 48 | +0.009473 | +0.023254 |
| 32 | +0.004026 | +0.011040 |
| 24 | +0.009700 | +0.025387 |

At 96 dimensions, 20/36 suffix cells and 25/36 prefix cells were positive. These are post-hoc descriptive diagnostics, not inference or equivalence analyses. The lower-dimensional values are same-seed algebraic folds, not independent reruns or seed sensitivity.

## Current E1 exploratory side result

E1 held the first and third GPT-2 tokens fixed across five ten-glyph families
and varied only the family-middle token. The equal-family global specificity was
0.014752595564 at layer 2 (95% descriptive interval
[0.002875238085, 0.027439243404]) and 0.014887989201 at layer 4
([0.003407563347, 0.019684351979]). All five family-specific intervals included
zero at each layer. The full transfer matrix was broadly positive—0.395455 to
0.484915 at layer 2 and 0.602564 to 0.681909 at layer 4—while 10/30
family × layer × seed cells did not exceed random controls.

The planned negative comparator at layer 4 was not negative. The bounded
interpretation is therefore shared-token matched-slot recurrence with a small
family-specific excess, not semantic family structure, tokenizer independence,
layer specificity, robust random-control superiority, or causality. E1 reused
24 exploratory prestage targets, did not touch P2 or C1, does not update the
Milestone 2 result, and does not satisfy a paper gate.

## Research questions

1. Do glyph-derived activation directions produce output fingerprints that repeat across held-out target prompts?
2. Do those fingerprints repeat across separately estimated source directions?
3. Do they exceed matched random-direction and generic-glyph controls under scalar-balanced intervention?
4. Which observed effects survive the prespecified token-count and prefix-panel matched controls?
5. Can a prespecified component or path intervention selectively remove and restore the candidate effect?
6. Which results replicate across execution backends, tokenizers, or model families?
7. In a token-isomorphic exploratory panel, how much matched-slot recurrence transfers across middle-token families, and how large is the residual within-family excess?

Questions 1–3 are exploratory baseline questions. Milestone 2 gives a mixed answer to question 4, subject to the open inferential qualifications. Questions 5–6 remain required before the paper freezes a stronger claim.
Question 7 is answered only descriptively by E1 and is not promoted to a
confirmatory or causal research question.

## Planned paper structure

### Abstract

- state the narrow intervention question;
- name the pinned model, precision, and hook object;
- summarize confirmatory effect sizes and negative cells;
- state the tokenization, causal, and generalization limits directly;
- avoid semantic-language shorthand.

### 1. Introduction

- motivate glyphs as compact, auditable intervention probes;
- distinguish reproducible geometry from interpretation;
- explain why intervention magnitude, random controls, target clustering, and tokenization must be explicit;
- list contributions and non-claims.

### 2. Experimental contract

- balanced 5-color × 2-shape panel;
- source wrappers and panel-centering construction;
- target groups and held-out splits;
- RMS-normalized intervention and global clipping;
- random, generic-glyph, zero-hook, dose, sign-flip, and permutation controls;
- target prompts as sampling clusters; direction seeds as nested repeated estimates.

### 3. Backend qualification and provenance

- pinned model revision and artifact hashes;
- Transformers/MPS ↔ MLX tokenizer, activation, logit, zero-hook, and fixed-intervention parity;
- 4 prompt lengths × 4 layers, 80/80 qualification gates;
- synchronized end-to-end latency: 17.517 ms for Transformers/MPS versus
  10.727 ms for MLX, or 1.633× in the recorded environment and load state;
- runtime provenance for the externally interrupted matched-null A foreground
  process: 798 rows under severe load, followed by an exact sealed resume with
  no duplicates, missing rows, or errors, with zero-hook activation/logit RMS at 0; do not treat
  the load event as model evidence or a universal speed result;
- sealed run identity, dependency identity, and resume safeguards.

The parity receipt is an engineering result and must not be counted as an independent scientific replication.

### 4. Exploratory baseline results

- standard-run integrity and zero-hook no-op;
- direction replicate alignment;
- held-out fingerprint advantage;
- cross-seed fingerprint advantage;
- scalar balance, dose monotonicity, and sign antisymmetry;
- all negative and heterogeneous cells;
- finite permutation floor and its limited interpretation;
- tokenization audit.

### 5. Confirmatory controls

- one-shot frozen 48-target P2 set and target-cluster endpoint;
- three token-count and panel-prefix matched null families, explicitly not token-identity matched;
- declared `🟥` semantic-near entry in panel C;
- layer-2 robust and layer-4 unresolved frozen-v1 results from both source-wrapper arms;
- descriptive exploratory paired median difference of +0.047427 (25/36 positive), without a percent-explained interpretation;
- same-seed 48/32/24-dimensional algebraic folds, clearly separated from CountSketch-seed sensitivity;
- analyzer role binding by CLI order and the separate passing input-binding audit;
- fixed-prototype v1 bootstrap versus the post-hoc rebuilt-prototype sensitivity;
- completed suffix and prefix-homogeneous diagnostics, reported as post-hoc
  descriptive comparisons rather than inference or equivalence tests.
- E1 as a clearly separated exploratory side analysis: complete five-family
  transfer matrices, small global excess, family intervals crossing zero,
  heterogeneous random controls, and a failed layer-4 negative comparator;
- do not use E1 to select the causal layer or strengthen the Milestone 2 status.

### 6. Targeted causal experiments

- carry layer 2, but not unresolved layer 4, into a newly frozen targeted causal protocol;
- prespecified component-site comparison;
- patch, ablate, and restore candidate paths;
- selectivity and null predictions;
- held-out confirmation;
- retire C1 v1 and prepare a new versioned causal bank outside the exposed
  research context; keep the replacement untouched until the complete causal
  protocol and multiplicity family are public and frozen;
- explicit update of `causal_claim_authorized` based on results.

### 7. Replication

- duplicate confirmatory matrix in a second internal backend;
- additional tokenizer or model family;
- agreement and disagreement table;
- architecture-specific boundary conditions.

### 8. Discussion and limitations

- what a reproducible fingerprint does and does not establish;
- tokenization and model-family dependence;
- next-token outcomes versus generation behavior;
- compressed CountSketch fingerprints versus full-vocabulary interpretation;
- exploratory selection, cluster count, and statistical power;
- absent SAE, iso-KL, or generation evidence where still missing.
- E1 family identity is exactly confounded with the middle GPT-2 token, while
  the first and third tokens are shared; its transfer pattern cannot establish
  a semantic or tokenizer-independent family representation.
- one complete C1 v1 record was exposed in a research-agent context without
  experimental use; the bank is retired, and future causal work requires a new
  versioned bank.

### 9. Reproducibility statement

- code, configs, revisions, hashes, and environment;
- raw-ledger archival location;
- compact public evidence manifest and omitted files;
- exact commands for parity, run, audit, and figure generation.

## Planned main figures

1. Experimental flow from sealed glyph sources to held-out output fingerprints.
2. Layer × strength fingerprint advantage with every seed shown.
3. Same-glyph, cross-glyph, and random-control distributions by layer.
4. Cross-seed reproducibility with target-cluster uncertainty.
5. Dose and sign-flip diagnostics.
6. Token-count/prefix-panel control results, fixed- versus rebuilt-prototype uncertainty, and any later causal intervention.
7. E1 source-family × prototype-family transfer matrices at layers 2 and 4,
   labeled exploratory and separated from the confirmatory claim family.

## Planned main tables

1. Model, tokenizer, backend, software, and artifact identity.
2. Parity qualification gates and latency scope.
3. Standard-run integrity and control counts.
4. Confirmatory effect sizes, intervals, and adjusted p-values.
5. Negative results, failed gates, and missing measurements.
6. Cross-backend and cross-model replication.

## Claim table

| Claim | Baseline status | Requirement before final paper |
|---|---|---|
| Pinned MLX cell matches the defined Transformers/MPS parity tolerances | supported, 80/80 | preserve receipt and repeat after relevant implementation changes |
| A pre-causal fingerprint candidate exists in the standard cell | supported descriptively | frozen confirmatory targets and cluster-aware inference |
| The effect is uniform across cells | not supported | no repair required; report heterogeneity |
| Layer 2 exceeds the prespecified token-count and prefix-panel matched controls | supported by frozen v1 in both source-wrapper arms; post-hoc dependence sensitivity is directionally consistent | prospectively resolve role binding and prototype-resampling dependence before final confirmatory wording |
| Layer 4 exceeds those controls | not supported; unresolved in both arms | retain as a main mixed/negative result |
| Token-isomorphic E1 families show matched-slot transfer | supported descriptively in one pinned cell; global excess is small, all family intervals include zero, and random-control cells are heterogeneous | retain as an exploratory side result; require a new frozen protocol and untouched bank for any focused confirmation |
| The effect is independent of tokenization | not supported | token-identity matching is impossible for a distinct GPT-2 byte input; make only the bounded matched-panel claim |
| A particular component or path causes the effect | not tested | targeted patch/ablate/restore experiment |
| The directions encode human-readable glyph meaning | not tested and not implied | would require an independently justified semantic assay |
| The result generalizes across models | not tested | cross-model replication |
| The result changes generated behavior | not tested | sealed generation experiment |

## Statistical commitments

- The principal observational units are target prompts.
- Source-direction seeds, target splits, and strengths are repeated or nested measurements, not extra independent prompts.
- The Milestone 2 v1 endpoint and layer family were frozen before P2 execution.
- Frozen-v1 inference and post-hoc rebuilt-prototype sensitivity will be labeled separately; the latter supplies no p-value or status.
- Any confirmatory analysis used in final-paper wording or replication will bind run roles directly to frozen configs and inputs and handle data-dependent prototype uncertainty prospectively.
- The paper will report effect sizes and uncertainty, not only p-values.
- The `1/1001` exploratory permutation floor will not be presented as a multiplicity-corrected global result.
- Negative and non-positive cells will remain visible.
- E1 intervals remain descriptive; no p-value, multiplicity decision,
  confirmatory status, or layer-comparison inference will be retrofitted.

## Remaining paper gates

- prepare a new versioned causal bank outside the C1 v1 exposure context, then
  freeze the complete targeted layer-2 causal protocol before opening it; no
  additional bank is required merely to begin protocol design;
- address v1 role binding and prototype-resampling dependence prospectively in
  final-paper confirmatory wording and supporting replication;
- complete at least one prespecified targeted causal experiment, positive or negative, without opening the replacement bank early;
- complete an independent backend implementation check and at least one model or tokenizer replication appropriate to the final claim;
- archive the complete raw evidence and checksum it;
- generate paper tables and figures from versioned scripts;
- run a fresh-eyes reproducibility and claim-boundary review;
- keep the English manuscript and Japanese public summary propositionally aligned.

No full manuscript is claimed at this stage. The English paper remains the Phase I endpoint.

## Reproducibility package

The preprint package should contain or point to:

- exact source revision and source-tree hash;
- model revision and model-file manifest;
- parity and standard-run receipts;
- resolved inputs and configs;
- complete raw intervention ledger and required arrays;
- compact public summaries and omission manifest;
- the E1 tokenizer preflight, complete descriptive analysis, five compact run
  bundles, and root hash manifest;
- artifact-audit receipt;
- versioned analysis and figure-generation scripts;
- English manuscript, supplementary material, and Japanese public summary.

The current compact repository omits the approximately 74 MiB (77.3 MB) raw intervention ledger and model-dependent NPZ arrays. That is acceptable for code review, but not sufficient as the final archival evidence package.
