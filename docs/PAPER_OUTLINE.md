# Phase I paper outline

[日本語](PAPER_OUTLINE.ja.md) · [Roadmap](ROADMAP.md) · [Current results](RESULTS_V1.md)

## Working title

**From Glyph Directions to Output Fingerprints: A Controlled Pre-Causal Study in GPT-2**

The Phase I manuscript will be written in English. A Japanese public summary will accompany the preprint, but the English manuscript is the controlling scientific text.

## Proposed central claim

Under a pinned GPT-2 FP32 setup, controlled additions of glyph-derived `resid_post` directions can produce reproducible, direction-specific next-token distribution fingerprints across held-out prompts and separately estimated source directions. The source of this reproducibility, its relationship to tokenization, and any semantic or circuit-level interpretation remain unresolved until targeted causal and replication experiments are complete.

This wording is provisional. It must narrow or change if confirmatory results do not support it.

## Research questions

1. Do glyph-derived activation directions produce output fingerprints that repeat across held-out target prompts?
2. Do those fingerprints repeat across separately estimated source directions?
3. Do they exceed matched random-direction and generic-glyph controls under scalar-balanced intervention?
4. Which observed effects survive tokenization-matched controls?
5. Can a prespecified component or path intervention selectively remove and restore the candidate effect?
6. Which results replicate across execution backends, tokenizers, or model families?

Questions 1–3 are exploratory baseline questions. Questions 4–6 are required before the paper freezes a stronger claim.

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

- frozen target set and primary endpoint;
- token-length- and token-prefix-matched controls;
- prespecified null families;
- cluster-aware uncertainty and multiplicity correction;
- sensitivity analyses that retain all cells.

### 6. Targeted causal experiments

- prespecified component-site comparison;
- patch, ablate, and restore candidate paths;
- selectivity and null predictions;
- held-out confirmation;
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
6. Tokenization-control and causal-intervention results.

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
| The effect is independent of tokenization | not supported | matched controls and replication |
| A particular component or path causes the effect | not tested | targeted patch/ablate/restore experiment |
| The directions encode human-readable glyph meaning | not tested and not implied | would require an independently justified semantic assay |
| The result generalizes across models | not tested | cross-model replication |
| The result changes generated behavior | not tested | sealed generation experiment |

## Statistical commitments

- The principal observational units are target prompts.
- Source-direction seeds, target splits, and strengths are repeated or nested measurements, not extra independent prompts.
- The primary endpoint and hypothesis family will be frozen before confirmatory execution.
- The paper will report effect sizes and uncertainty, not only p-values.
- The `1/1001` exploratory permutation floor will not be presented as a multiplicity-corrected global result.
- Negative and non-positive cells will remain visible.

## Reproducibility package

The preprint package should contain or point to:

- exact source revision and source-tree hash;
- model revision and model-file manifest;
- parity and standard-run receipts;
- resolved inputs and configs;
- complete raw intervention ledger and required arrays;
- compact public summaries and omission manifest;
- artifact-audit receipt;
- versioned analysis and figure-generation scripts;
- English manuscript, supplementary material, and Japanese public summary.

The current compact repository omits the approximately 74 MiB (77.3 MB) raw intervention ledger and model-dependent NPZ arrays. That is acceptable for code review, but not sufficient as the final archival evidence package.
