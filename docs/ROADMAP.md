# GlyphProbe research roadmap

[日本語](ROADMAP.ja.md) · [E2 MPS transport v2 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](HOLDOUT_STATUS.md) · [E2 Stage-A3 numeric-screen result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [E2 Stage-A3 protocol](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) · [E2 MLX validation v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [E1 exploratory results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md) · [Phase I paper plan](PAPER_OUTLINE.md)

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
  preflight; C1 v1 was not used in Milestone 2, but is now retired after the
  separately documented research-context exposure;
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

### Exploratory side track E1 — Token-isomorphic emoji-family screen

Status: complete as a bounded descriptive exploration. The public freeze at
commit `0cd4e11610e42253ead9ce9aff9f0b02474a0558` preceded all five MLX runs.

- freeze five ten-code-point blocks: `sky` (`U+1F311`–`U+1F31A`), `food`
  (`U+1F351`–`U+1F35A`), `animals` (`U+1F411`–`U+1F41A`), `transport`
  (`U+1F691`–`U+1F69A`), and `social` (`U+1F911`–`U+1F91A`);
- require every glyph to have three pinned GPT-2 tokens, with token 1 and the
  matched-slot token 3 identical across families and only token 2 changing by
  family;
- reuse only the existing first 24 prestage targets and the 16 source wrappers;
  do not read, tokenize, score, or select with P2 or C1;
- hold the run family to pinned GPT-2, MLX FP32, `resid_post` layers 2 and 4,
  strength 0.05, seeds 101/211/307, two random directions per layer, and an
  enabled zero-hook check, with neutral-direction and sign-flip arms disabled;
- layer 2 remained the primary exploratory row; the prespecified layer-4
  negative comparator was not negative;
- report the complete replicate-wise LOTO \(M_{f\leftarrow g}\) matrix, the
  within-row excess \(R_f\), and family-equal \(R_{\mathrm{global}}\), with
  data-dependent prototypes rebuilt inside 20,000 stratified target-bootstrap
  replicates and equal-target means as the primary descriptive aggregates;
- all five runs completed, producing 8,880 intervention rows with zero errors
  and exact zero-hook activation/logit RMS of 0;
- the equal-family global excess was 0.014752595564 at layer 2, with a 95%
  descriptive interval of [0.002875238085, 0.027439243404], and 0.014887989201
  at layer 4, with [0.003407563347, 0.019684351979];
- all five family-specific intervals included zero at each layer;
- the complete mean transfer matrix was broadly positive: its 25 cells ranged
  from 0.395455 to 0.484915 at layer 2 and from 0.602564 to 0.681909 at layer 4;
- 10/30 family × layer × seed cells did not exceed their random controls: all
  five families at layer 2 seed 307 and all five at layer 4 seed 101;
- publish every family and every null, negative, and heterogeneous cell without
  p-values, multiplicity decisions, or confirmatory status labels.

The [E1 exploratory protocol](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) fixes the
question, inputs, endpoints, stopping rule, and claim boundary; the
[E1 results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) publish the complete outcome.
The broadly positive transfer matrix and small family-specific excess suggest
that shared-token transfer dominates the residual within-family signal. E1 can
describe matched-slot recurrence under a controlled middle-token substitution,
but not a semantic family effect, tokenization-independent property,
layer-specific effect, robust random-control superiority, causal mechanism, or
cross-model regularity. It does not update Milestone 2, unseal C1, choose the
Milestone 3 intervention, or satisfy a Phase I paper gate.

Exit condition: met. The public bundle links the tokenizer-only preflight,
complete descriptive analysis, five compact run directories, and a root
manifest. Any hypothesis prompted by E1 requires a new public confirmatory
protocol and a new untouched target bank that is neither P2 nor C1.

### Engineering side track E2 — Llama 3.2 3B MLX cross-model transport

Status: Stage-A v2 engineering validation and the subsequent Stage-A3
runtime-dtype screen are complete. V2 remains `status: validation_failed` and
`scientific_result: false`; Stage A3 selected no eligible candidate. MLX is not
qualified for the pinned E2 scientific cell. No E2 scientific-grid forward was
run or authorized.

Version 1 was frozen by public commit
`88685bd01ab115df323e9a324d49a659c66163c7`. Its Transformers/MPS phase
completed. The MLX phase then failed on the first baseline export with:

```text
RuntimeError: Item size 2 for PEP 3118 buffer format string B does not match the dtype B item size 1.
```

The failure preceded parity comparison, the speed decision, and every
scientific endpoint. No v1 receipt was produced, and no scientific outcome was
inspected. Its [failure record](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)
remains available.

V2 changed the specified backend numerical semantics only at the MLX-to-NumPy
export bridge: native BF16 arrays were cast to `mx.float32` immediately before
NumPy export while model execution remained BF16. This allowed both isolated
worker phases to complete, with return code 0 and no simultaneous model
residency. Pinned model metadata and the complete nine-file artifact manifest
matched across backends.

- Overall parity passed 33 / 60 checks. Token IDs and within-backend determinism
  passed 10 / 10, and exact zero-hook behavior passed 10 / 10.
- Baseline checks passed 6 / 10 and changed-output checks passed 7 / 10.
- All ten activation-delta subcomparisons passed, with NRMSE
  0.014057–0.018356, cosine 0.999832–0.999901, and RMS ratio
  0.999625–1.000526. The composite delta family nevertheless passed 0 / 10
  because the corresponding logit deltas failed clearly: NRMSE
  0.580523–1.402939 and cosine -0.097707–0.816940.
- Intervention fidelity passed 0 / 10. Activation NRMSE was approximately
  0.0302–0.0341 against the frozen 0.01 threshold, while cosine was about
  0.9994 and RMS ratio remained about 1 for both backends.
- The machine-local speed gate failed. Aggregate median latency was
  132.127833 ms for Transformers/MPS and 230.138000 ms for MLX. MLX used
  1.741782892 times the latency; the recorded speedup was `0.574124367x`.
- The run did not access study target banks or confirmatory or causal outcomes.
  It produced no scientific E2 grid, emoji-family, semantic, causal,
  cross-model, or model-scale result.

The complete outcome is in the [E2 Stage-A v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md),
the fixed engineering gate is in the [protocol](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md),
and the machine-readable record is the [v2 receipt](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).
This negative engineering qualification is not a scientific negative result
and does not satisfy Phase I paper gate 5.

Stage A3 publicly froze two runtime-compute candidates over the same BF16-weight
artifact. FP16 and FP32 both passed identity, token/determinism, exact zero-vector,
and within-backend fidelity gates. Both failed the machine-local speed gate:
MLX/MPS was 1.956666698 for FP16 and 0.986249198 for FP32, while the frozen rule
required no more than 0.95. The deterministic selection was therefore `null` /
`no_go_no_eligible_numeric_candidate`. Stage A3 did not run the full
cross-backend parity families, so its strong FP32 fidelity is not a qualified
FP32 route. See the [Stage-A3 result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md),
[frozen protocol](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md), and
[receipt](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json).

The research owner selected a separate Transformers/MPS scientific freeze. It
does not qualify MLX, revise either no-go, or relax the v2 or Stage-A3
thresholds. A distinct future MLX redesign would still require its own public
engineering protocol.

Exit condition: one atomic, no-overwrite receipt binds the pinned model and
configuration identities to complete backend parity and a machine-local MLX
aggregate median latency no greater than 95% of Transformers/MPS. This exit
condition remains unmet. V2 and Stage A3 produced the required recorded failure
evidence, not a qualified MLX route. Even a later passing engineering receipt
would not by itself complete E2 or a paper gate.

### Scientific side track E2b — Llama 3.2 3B MPS emoji transport

Status: v1 failed tokenizer preflight with zero model forwards and is retired.
V2 is `freeze_pending` until its manifest commit is public. That commit
establishes the corrected static design; execution then remains
`preflight_pending` until the zero-model-forward v2 receipt is published as the
only change in a descendant commit. No scientific outcome exists yet.

- use the pinned `mlx-community/Llama-3.2-3B-bf16` artifact through raw
  Transformers on MPS with FP32 runtime parameters;
- run five separately centered and executed ten-emoji family panels as the literal `full50` primary
  arm and five independently centered seven-emoji panels (`slot_03`–`slot_09`)
  as the non-rescuing `core35` token-structural sensitivity arm;
- reuse only the 24 already explored prestage targets and 16 source wrappers;
  do not read, tokenize, score, or select with P2 or retired C1 v1;
- bind layers 5 and 11, strength 0.05, seeds 101/211/307, two random controls,
  exact zero-hook checks, and a 20,000-replicate target-stratified bootstrap;
- make `full50`, layer 5, equal-family `R_global` the sole primary row. Its
  status is `transport_criterion_met` only if the two-sided 95% percentile-bootstrap lower
  endpoint is greater than zero; every other row is secondary and cannot
  rescue that decision.

The complete design and claim boundary are in the
[E2 MPS transport v2 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md). Even a
positive primary row would support only a bounded, reused-target MPS transport
observation. It would not establish semantics, tokenizer independence,
causality, independent-target confirmation, or model-scale generality.

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
- C1 v1 is retired. Prepare a new versioned causal bank outside the exposed
  research context, and keep it untouched until the intervention, endpoint,
  controls, candidate layer, and multiplicity family are frozen publicly.

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
2. A new versioned confirmatory target set remains untouched by exploratory selection.
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

Possible Phase II directions include expansion beyond E1's five frozen emoji
blocks, multimodal tokenizers, learned feature-basis analysis,
intervention-orbit studies, and comparisons across training checkpoints. They
remain outside the current commitment until the Phase I paper is complete.
