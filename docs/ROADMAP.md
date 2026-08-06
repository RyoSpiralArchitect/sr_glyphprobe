# GlyphProbe research roadmap

[日本語](ROADMAP.ja.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md) · [Phase I paper plan](PAPER_OUTLINE.md)

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

Status: operationally complete; mixed layer-specific result; final-paper
inferential qualification remains open.

- the frozen 48-target P2 bank was opened once after public freeze and passing
  preflight; the separate 48-target C1 causal holdout remains untouched;
- the colored-shape panel was compared with three disjoint ten-symbol null
  panels matched on the prespecified GPT-2 token count and 9:1 panel-prefix
  structure;
- keep exact-token identity outside the claim: identical token IDs would decode
  to the same input bytes, so this is a matched robustness test rather than a
  tokenization-free glyph test;
- the primary family remained fixed at layers 2 and 4, strength 0.05, with
  direction seeds averaged inside each target;
- frozen v1 classified layer 2 as robust to the prespecified matched controls
  in both source-wrapper arms: +0.208363, 95% CI [0.137463, 0.276893], Holm
  p = 0.00143999 for the primary source, and +0.187507,
  [0.125489, 0.247659], p = 0.00393996 for the independent source;
- layer 4 remained unresolved in both arms: -0.0329465,
  [-0.0761085, 0.0110094], and -0.086379,
  [-0.159246, -0.016917], respectively;
- the original exploratory matrix yielded a descriptive 96-dimensional paired
  median excess of +0.047427, with 25/36 cells positive; no percent-explained
  estimate is authorized;
- keep the existing 24 targets available for implementation checks and
  diagnostics, without using either holdout bank for debugging or tuning;
- a separate role/input-binding audit passed for all 14 published runs: the 12
  core exploratory, P2, and independent-source arms plus two diagnostics;
- v1 bootstrap intervals resample fixed target effects rather than rebuilding
  prototypes. A post-hoc dependence-aware analysis rebuilt prototypes jointly
  and produced wider descriptive intervals; it assigns no p-value or status and
  does not overwrite v1;
- both 14,208-row secondary diagnostic grids completed with zero errors,
  zero-hook activation/logit RMS of 0, and readiness 11/11. Their random-adjusted headline advantages
  were +0.751225 (suffix-matched) and +0.601038 (prefix-homogeneous); these are
  not the raw separation scores used in the paired comparison;
- the descriptive standard-minus-suffix raw-separation medians at dimensions
  96/48/32/24 were +0.002624/+0.009473/+0.004026/+0.009700; the corresponding
  standard-minus-prefix values were +0.022096/+0.023254/+0.011040/+0.025387.
  At 96 dimensions, 20/36 and 25/36 cells were positive, respectively. These
  post-hoc diagnostics provide neither inference nor an equivalence decision,
  and the lower dimensions are same-seed algebraic folds;
- the first matched-null A process was externally interrupted after 798 rows
  during severe machine load. A sealed resume completed the exact grid without
  duplicates, missing rows, or errors, with zero-hook activation/logit RMS at 0. This is runtime
  provenance, not model evidence or a universal speed claim.

The frozen question and decision rule are in the [Milestone 2 protocol](MILESTONE2_PROTOCOL.md); outcomes and qualifications are in [Milestone 2 results](MILESTONE2_RESULTS.md).

Exit condition: operational execution is complete. Final-paper confirmatory
wording and any supporting replication must prospectively bind run roles to
frozen inputs and account for data-dependent prototype resampling.

### Milestone 3 — Targeted causal localization

Status: eligible for protocol design, but no causal protocol has yet been
frozen and no causal claim is authorized. Layer 2 is the only current
candidate; layer 4 remains unresolved and is not a candidate. A further
confirmatory bank is not a prerequisite to designing this protocol.

- compare `resid_pre`, `attn_out`, `mlp_out`, and `resid_post` only after model-family parity qualification;
- perform component patching and path patching around prespecified candidate layers;
- use ablation, restoration, and projection-removal interventions;
- include negative controls that should leave the candidate fingerprint unchanged;
- require held-out selective effects rather than a single large drift.
- keep C1 sealed until the intervention, endpoint, controls, candidate layer,
  and multiplicity family are frozen in a new public causal protocol.

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

Status: partly completed for Milestone 2 v1, with an open bootstrap-dependence
qualification.

- treat target prompts as principal sampling clusters;
- keep direction seeds and target splits nested rather than counting them as independent samples;
- define a primary endpoint and a small primary hypothesis family;
- use multiplicity correction appropriate to that family;
- report effect sizes, intervals, negative cells, and sensitivity analyses alongside p-values;
- distinguish the `1/1001` permutation floor from a global significance claim.
- bind scientific run roles directly to frozen configs and inputs in the next
  confirmatory analyzer, rather than relying on CLI order plus a separate audit;
- either rebuild data-dependent prototypes inside each resample or justify and
  freeze a different dependence-aware estimator before outcomes.

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

Current reading: gates 1–3 have operational evidence, but the final statistical
qualification for gate 6 remains open because the rebuilt-prototype analysis was
post-hoc. Gates 4, 5, 8, and 10 remain open. Gate 9 must be maintained on every
public documentation change. The English paper remains the Phase I endpoint;
the current repository is an evidence-bearing research release, not a finished
manuscript.

## Beyond Phase I

Possible Phase II directions include broader symbol families, multimodal tokenizers, learned feature-basis analysis, intervention-orbit studies, and comparisons across training checkpoints. They remain outside the current commitment until the Phase I paper is complete.
