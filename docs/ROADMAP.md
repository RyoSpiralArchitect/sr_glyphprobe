# GlyphProbe research roadmap

[日本語](ROADMAP.ja.md) · [Current results](RESULTS_V1.md) · [Milestone 2 protocol](MILESTONE2_PROTOCOL.md) · [Phase I paper plan](PAPER_OUTLINE.md)

## Destination

Phase I ends with an English preprint-ready paper and an auditable evidence package. The current pinned GPT-2 MLX run is the baseline map for that phase, not its final claim.

Repository-authored public documentation is maintained in both English and Japanese throughout Phase I. English is the controlling language for the paper; Japanese companion documents keep the research process accessible and reviewable.

## Research sequence

### Milestone 1 — Reproducible screening baseline

Status: completed for one pinned GPT-2 FP32 `resid_post` cell.

- seal panel, wrappers, targets, strengths, layers, and controls;
- validate MLX against Transformers/MPS for the exact model cell;
- run the standard 14,208-record matrix;
- audit row counts, provenance, zero-hook behavior, scalar balance, and headline recomputation;
- publish positive, negative, and heterogeneous cells together.

Exit condition: an internally consistent pre-causal candidate exists. This milestone does not authorize semantic or causal language.

### Milestone 2 — Tokenization and null strengthening

Status: protocol frozen; preflight pending. No Milestone 2 model outcomes have
been inspected or claimed.

- use the frozen 48-target P2 bank once for confirmation, while preserving the
  separate 48-target C1 bank for the future final causal test;
- compare the colored-shape panel with three disjoint ten-symbol null panels
  matched on the prespecified GPT-2 token count and 9:1 token-prefix structure;
- keep exact-token identity outside the claim: identical token IDs would decode
  to the same input bytes, so this is a matched robustness test rather than a
  tokenization-free glyph test;
- hold the primary family fixed at layers 2 and 4, strength 0.05, with direction
  seeds treated as repeated estimates inside each target;
- estimate the primary effect over 48 target-prompt clusters, using
  leave-one-group-out prototypes, stratified target-cluster bootstrap intervals,
  and Holm correction across the two primary layers;
- keep the existing 24 targets available for implementation checks and
  diagnostics, without using either holdout bank for debugging or tuning;
- complete manifest, configuration, analysis-code, and test preflight before the
  one-shot P2 bank is opened.

The exact question, endpoint, decision rule, stopping rule, and prohibited uses
are fixed in the [Milestone 2 confirmatory protocol](MILESTONE2_PROTOCOL.md).
The freeze takes effect in the first public commit containing that protocol and
its bound manifests, configs, and analysis code. P2 remains unopened until that
public freeze exists and every preflight check passes.

Exit condition: the confirmatory effect cannot be explained by the currently identified token-length or token-prefix asymmetries alone.

### Milestone 3 — Targeted causal localization

Status: planned.

- compare `resid_pre`, `attn_out`, `mlp_out`, and `resid_post` only after model-family parity qualification;
- perform component patching and path patching around prespecified candidate layers;
- use ablation, restoration, and projection-removal interventions;
- include negative controls that should leave the candidate fingerprint unchanged;
- require held-out selective effects rather than a single large drift.

Exit condition: a prespecified intervention selectively changes the candidate effect and survives matched controls. Until then, `causal_claim_authorized` remains false.

### Milestone 4 — Replication and boundary mapping

Status: planned.

- repeat the confirmatory cell in raw Transformers or TransformerLens, not only adapter-level parity;
- replicate across at least one additional model family and tokenizer;
- examine checkpoint emergence where weight histories are available;
- test robustness across prompt domains and target-template families;
- separate architecture-specific observations from cross-model regularities.

Exit condition: the paper can state clearly which findings replicate and which remain GPT-2-specific.

### Milestone 5 — Confirmatory statistics

Status: planned.

- treat target prompts as principal sampling clusters;
- keep direction seeds and target splits nested rather than counting them as independent samples;
- define a primary endpoint and a small primary hypothesis family;
- use multiplicity correction appropriate to that family;
- report effect sizes, intervals, negative cells, and sensitivity analyses alongside p-values;
- distinguish the `1/1001` permutation floor from a global significance claim.

Exit condition: the statistical analysis matches the sampling structure and can be rerun from frozen artifacts.

### Milestone 6 — English paper and archival release

Status: Phase I goal.

- freeze the English manuscript claim table before polishing the narrative;
- produce all main figures and tables directly from versioned analysis scripts;
- publish model, revision, tokenizer, environment, implementation, and input receipts;
- archive the complete raw ledger and required arrays, or document a reproducible governed-access route;
- release a compact repository package with checksums and explicit omission records;
- complete internal falsification review and an independent reproduction attempt;
- publish the English preprint with a Japanese public summary.

Exit condition: every paper claim points to a sealed artifact, every important caveat appears in the abstract or limitations, and an independent reader can reproduce the analysis without reconstructing missing evidence.

## Phase I paper gates

The manuscript does not advance from draft to preprint until all of the following are true:

1. The exact primary hypothesis and claim boundary are frozen.
2. A confirmatory target set remains untouched by exploratory selection.
3. Tokenization-matched controls are complete.
4. At least one targeted causal experiment is complete, whether positive or negative.
5. At least one independent backend or model replication is complete.
6. Cluster-aware, multiplicity-aware statistics are reported.
7. Negative and heterogeneous cells remain visible in the main paper or supplement.
8. The complete evidence archive is deposited and checksummed.
9. English and Japanese repository documentation are synchronized.
10. The English paper receives a fresh-eyes reproducibility and claim-boundary review.

These gates do not predetermine a positive paper. A carefully bounded negative or mixed result is a valid Phase I outcome if the experiment is identifiable and the artifacts are complete.

## Beyond Phase I

Possible Phase II directions include broader symbol families, multimodal tokenizers, learned feature-basis analysis, intervention-orbit studies, and comparisons across training checkpoints. They remain outside the current commitment until the Phase I paper is complete.
