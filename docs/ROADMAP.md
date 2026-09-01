# GlyphProbe research roadmap

[Mistral base depth-distance results](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) · [Mistral base depth-distance protocol](MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md)

[T18 fresh lexical result](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md) · [T18 paper story](PAPER_STORY_T18_FRESH_LEXICAL_V0.md) · [T17 glyph–name result](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) · [T15-B prospective replication result](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md)

[日本語](ROADMAP.ja.md) · [T15-A emoji × word result](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md) · [T15-A protocol](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md) · [T14-X / T14-C result](EMOJI_STEERING_T14_X_T14_C_RESULTS_V0.md) · [T13-EH acquisition protocol](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) · [T12 reserve result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T11 exploratory result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T11 frozen protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.md) · [T10 diagnostics](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md) · [T10 cross-model result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [Dense CUDA results](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Carrier-distance results](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md) · [Carrier-distance protocol](MULTIFAMILY_CARRIER_DISTANCE_V0.md) · [Common-suffix results](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Matched-slot results](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Multifamily geometry results](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) · [Tokenizer census results](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [E2 MPS transport v2 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](HOLDOUT_STATUS.md) · [E2 Stage-A3 numeric-screen result](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [E2 Stage-A3 protocol](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) · [E2 MLX validation v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [E1 exploratory results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md) · [Phase I paper plan](PAPER_OUTLINE.md)

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

### Control-design side track T1 — Multifamily tokenizer census

Status: complete as a frozen tokenizer-only census and post-hoc descriptive
aggregate. It is design evidence, not a scientific activation result.

- complete all 14 locally available tokenizer roster entries across mac1,
  mac2, and furnace with zero model forwards and zero protected-target access;
- retain all 115 fixed items, four contexts, 6,440 tokenization rows, and
  19,665 pairwise rows;
- treat the seven exact output classes as fixed-surface equivalence only, with
  five cross-node reproduction groups;
- record that only six items have invariant raw token count across all seven
  classes and that the family ZWJ item spans 7–20 raw tokens;
- record that neither blue circle nor blue square has one fixed-panel candidate
  matching both token count and a one-token prefix across every output class in
  any fixed pairwise context; and
- keep the result post hoc and descriptive: it does not update Milestone 2,
  select a layer, establish tokenizer-independent structure, or close a paper
  gate.

The [T1 result](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) and [frozen
protocol](MULTIFAMILY_TOKENIZER_CENSUS_V0.md) imply that future cross-tokenizer
activation cells must freeze controls separately per tokenizer output class.
Atomic-token cases need a declared alternative structural match rather than a
prefix rule relaxed after outcomes are visible.

Exit condition: met for the census. A later matched-control activation study is
a new protocol with its own untouched targets, endpoint, hypothesis family,
and multiplicity rule.

### Observational side track T2 — Multifamily colored-shape geometry

Status: complete as a frozen observational negative/mixed result. The
predeclared outcome is `no_dual_model_recurrence`.

- bind one unchanged ten-item colored-shape panel to Gemma 2 2B 4-bit and
  OLMo 3 7B BF16, without reusing the Llama outcome to select a layer;
- use the Gemma atomic one-token construction match and the OLMo equal-count,
  shared-prefix construction match as distinct declared control families;
- capture raw-glyph `resid_post` at five depth fractions selected by formula,
  with only the midpoint layer primary;
- test mean circle-minus-square direction parallelism across five colors with
  all 120 square-label permutations;
- treat the two model-cell tests as one Holm-corrected family and retain all
  four secondary layers regardless of sign; and
- perform no intervention, generation, protected-target access, cross-model
  magnitude comparison, or post-outcome layer replacement;
- retain the primary Gemma midpoint result (`T = 0.114857969`, raw
  `p = 0.058333333`, Holm `p = 0.116666667`) and OLMo midpoint result
  (`T = 0.024628040`, raw/Holm `p = 0.275`) without rejection; and
- publish both complete activation arrays, all ten fixed-depth rows, source and
  relay hash evidence, and passing run and analysis validators.

The [T2 result](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) and [complete
freeze](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md) preserve the non-primary
Gemma rows with smaller descriptive p-values without promoting them. Model
family, scale, precision/quantization, tokenizer structure, and node remain
confounded, so the two raw magnitudes are not a scale or quantization contrast.

Exit condition: met. Both role-bound run bundles and the joint exact analysis
are published with checksums. This side track does not replace the causal gate
or an independent backend replication.

The five-family breadth branch was selected prospectively as T3. The remaining
same-family precision contrast and independent implementation remain future
options rather than post-outcome rescue analyses.

### Observational side track T3 — Five-family matched-slot geometry

Status: complete with `olmo_only_token_structured_recurrence`.

- bind the unchanged E1 sky, food, animals, transport, and social panels into
  one 5 × 10 crossed design;
- require Gemma's 50 distinct atomic tokens and OLMo's exact
  `[shared_prefix, family_token, slot_token]` factorization before forwarding;
- capture the same five formula-selected depth fractions in both model roles;
- remove each family mean and use the shared-slot sum-of-squares fraction as
  the per-depth statistic;
- average all five fixed depths as the only model-level primary endpoint;
- synchronize 19,999 independent within-family slot-label randomizations
  across depth and Holm-correct the two model-level tests;
- retain all ten depth rows without granting any one depth a decision; and
- record the failed first receipt serialization and freeze a key-normalization-
  only repair before rerunning analysis.

Gemma produced `T = 0.204304805` against null mean `0.199984463` (Holm
`p = 0.2085`) and did not reject. OLMo produced `T = 0.500391869` against
`0.200184835` (Holm `p = 0.0001`) and rejected. OLMo's slot fraction fell from
`0.994722` to `0.295828` across the fixed profile but remained above the null
at every depth. Those depth rows are secondary.

The [T3 result](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md), [frozen
protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md), and [analysis
repair](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_ANALYSIS_REPAIR_V1.md) keep the
tokenizer-conditioned interpretation explicit. The exact shared OLMo suffix
token is a sufficient explanation for its recurrence; model family, scale,
precision, and node remain confounded, so the result is not a causal tokenizer
contrast or semantic effect.

Exit condition: met. The one-token common-suffix falsification was selected
prospectively as T4 and completed below. Same-artifact token/precision
deconfounding and an independent exact implementation remain future options.
T3 does not close a Phase I gate or select a causal layer.

### Observational side track T4 — Common-suffix carryover

Status: complete with `olmo_only_common_suffix_carryover`.

- reuse the unchanged T3 panel, two model artifacts, five depth fractions, and
  model-role binding;
- append either an exact period or newline token to every glyph, with all 50
  raw token sequences preserved as exact prefixes plus one common suffix token;
- read `resid_post` at the suffix rather than the glyph's own final token;
- use the equal-weight mean over both contexts and all five depths as the sole
  model-level endpoint;
- synchronize each of 19,999 within-family slot permutations across all ten
  context/depth cells and Holm-correct the two model-level tests; and
- bind the T3 statistics as descriptive references without inferential pooling.

Gemma produced `T = 0.203443011` against null mean `0.200044692` (Holm
`p = 0.30295`) and did not reject. OLMo produced `T = 0.537464703` against
`0.199977865` (Holm `p = 0.0001`) and rejected. Its secondary period and newline
statistics were closely aligned at `0.538985382` and `0.535944025`. OLMo's
matched-slot geometry is therefore observable one common token later in both
fixed contexts, while Gemma remains near the null.

The [T4 result](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md), [frozen
protocol](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.md), and [public
evidence](../artifacts/multifamily_common_suffix_carryover_v0/README.md) retain
all 20 rows and the full compact arrays. The result rules out a strictly
current-token-only description of T3 but not short-range propagation from the
immediately preceding structured token sequence. It is not semantic, causal,
confirmatory, tokenizer-independent, or a cross-model magnitude contrast.

Exit condition: met. A prospectively frozen carrier-distance decay assay is a
useful cheap next falsification before intervention, but it must remain a side
track and cannot replace the tokenization-matched confirmatory controls or
close a Phase I gate.

### Observational side track T5 — Carrier-distance profile

Status: complete with `no_model_distance_attenuation`.

- keep the complete input and current carrier-token identity fixed while moving
  the readout to distances 1, 2, 4, and 8 after each glyph;
- use two exact eight-token carriers, repeated `" a"` and repeated `" |"`, and
  reject any model cell whose tokenizer does not preserve either repeated-token
  contract exactly;
- run five fixed depth fractions in Gemma 2 2B 4-bit, Llama 3.2 3B BF16, and
  OLMo 3 7B BF16 roles, with 400 forward calls per model and no intervention,
  generation, or protected-target access;
- require both a distance-1 recurrence component and a prespecified
  log2-distance attenuation component through one intersection-union test per
  model; and
- use the larger component p-value as the model raw p-value, then Holm-correct
  across the three model roles with 19,999 synchronized within-family
  permutations per model.

The design distinguishes recurrence with net attenuation across the fixed
profile from persistence without the prespecified attenuation contrast. It
does not establish monotonic decay, disappearance by distance 8, semantic
content, mechanism, causality, tokenizer independence, or direct cross-model
magnitude equivalence. Llama's earlier Stage-A parity failure remains in force;
this MLX cell is an observational within-artifact result only.

Gemma's distance-1 component remained near its null. Llama and OLMo each had a
distance-1 component raw `p = 0.00005`, but their attenuation components did not reject
(`p = 0.188` and `0.9977`). Their model IUT/Holm p-values were `0.564` and
`1.0`; Gemma's was also `1.0`. The fixed outcome is therefore
`no_model_distance_attenuation`.

Llama and OLMo remain descriptively elevated at distance 8, while their first
captured layers decline and later fixed depths are flatter or rise. That
depth-by-distance heterogeneity is secondary and cannot replace the failed
model-level endpoint. A new interaction replication or a same-artifact control
that breaks shared slot structure would require a separate prospective freeze.

Exit condition: met. The [complete result](MULTIFAMILY_CARRIER_DISTANCE_V0_RESULTS.md),
three sealed runs, 120-row joint analysis, transfer receipt, and public manifest
are published. T5 remains outside the Phase I gate and T4 remains a descriptive
reference only.

### Observational side track T6 — Dense CUDA carrier-distance replication

Status: complete with `no_dense_model_distance_attenuation`. The prospective
freeze contained zero T6 model forwards; the natural lifecycle and free-furnace
start gates were subsequently met before execution.

- preserve T5's exact public panel, repeated `" a"` and `" |"` carriers,
  distances 1/2/4/8, five depth fractions, IUT, 19,999-draw randomization, and
  model-level Holm decision scope;
- run four complete local BF16 Transformers/CUDA artifacts in separate
  processes: Gemma 2 2B IT, Gemma 3 4B IT, Mistral 7B Instruct v0.3, and Gemma
  3 12B IT;
- bind the three observed tokenizer output classes and every full-file model
  artifact before the first model load;
- retain 400 forwards per model, 1,600 total, with zero intervention,
  generation, behavior scoring, or protected-target access; and
- keep T5 as a descriptive design reference with no inferential pooling.

The roster was selected after T5 from locally complete furnace artifacts. All
four cells are instruction-tuned. The 2B–12B labels and the tokenizer-identical
Gemma 3 4B/12B pair are descriptive design structure, not an authorized scale
sample or base/instruct comparison. The four model IUTs form one Holm family;
all carrier, distance, depth, tail, pair, and timing outputs remain secondary.

The first model load requires a newly free `spiral status` and a natural
receiver-owned lifecycle surface for the fresh `resource:furnace` notice.
Canonical replication, watcher arrival, and an OS popup do not satisfy the
lifecycle gate. No probe, trust bypass, or interruption may manufacture it.

No model-level IUT survived Holm. Mistral rejected the distance-1 component at
the permutation floor (`p = 0.00005`) but not the attenuation component
(`p = 0.46975`). The other three cells did not reject distance 1. Mistral's
distance-8 component and Gemma 3 12B's nominal tail are secondary and remain
unpromoted. The Gemma 3 pair does not identify a scale trend.

Exit condition: met. The [complete result](MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md),
four sealed runs, 160-row joint analysis, transfer receipt, and public manifest
are published. T6 does not close a causal, confirmatory, tokenizer-independent,
backend-parity, model-general, or scale paper gate. Further model breadth is
deprioritized in favor of a separately frozen structure-breaking control or
distance-by-depth interaction, while the main Phase I path retains
tokenization-matched controls and an untouched confirmatory target set.

### Observational side track T7 — Mistral base depth-by-distance

Status: complete with `recurrence_and_early_depth_attenuation_excess`. The
endpoint was frozen and pushed before any T7 model forward, after T6 had exposed
the Mistral Instruct profile. It is prospective only for the previously unseen
Mistral 7B v0.3 base-model outcomes.

- retain T6's public 50-item panel, two carriers, distances 1/2/4/8, five depth
  fractions, synchronized within-family slot randomization, and 400-forward
  observational boundary;
- replace the failed all-depth decay conjunction with one fixed IUT requiring
  both distance-1 recurrence and positive early-depth attenuation minus the
  mean of the four later depths;
- use fixed distance weights `[0.375, 0.125, -0.125, -0.375]`, 19,999 PCG64
  draws, seed `2026082801`, and one-model decision scope with no multiplicity
  adjustment; and
- retain zero intervention, generation, behavior scoring, and protected-target
  access.

Distance-1 recurrence was `0.377524026` and the fixed early-minus-late
interaction was `0.149104068`; both one-sided raw p-values reached the
`0.00005` permutation floor, so the IUT rejected. Depth-0 attenuation was
`+0.114009450`, while the later-depth mean was `-0.035094618`. The original
all-depth attenuation remained negative and non-rejecting (`p = 0.87475`).

The 20 base-model depth-by-distance cells were descriptively close to the known
T6 Instruct profile (`r = 0.996785730`, MAE `0.011953404`). This is not an
equivalence test or an instruction-tuning contrast: the model and endpoint were
selected after T6, the checkpoints are related, and only one new model cell was
run. It is therefore not independent confirmation and does not authorize
semantic, causal, scale, tokenizer-independent, backend-parity, or Phase I gate
claims.

Exit condition: met. The [complete result](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md),
sealed 400-forward run, 40-row analysis, transfer receipt, and public manifest
are published. A later structure-breaking control or genuinely independent
replication requires a new prospective freeze; T7 does not displace the main
tokenization-matched-control and untouched-confirmatory-set priorities.

### Observational side track T8 — Mistral semantic atlas

Status: descriptive high-n atlas complete; its untouched reserve was later
opened only under the frozen T9 confirmation protocol.

- The zero-forward census fixed all 1,184 fully-qualified single-codepoint
  Unicode Emoji 17.0 entries: 50 prior-exposed calibration items, 842
  prospectively hash-selected discovery items, and 292 `reserved_unrun` items.
- The initial batch-64 acquisition completed the 892-item grid but failed the
  frozen batch-one recapture gate 0/18. The thresholds were retained and the
  failed data remain part of the record.
- The exact grid was recaptured canonically at batch size one: 5,352 model
  calls, 28 validated FP32 shards, and 192,672 residual vectors across glyph,
  Unicode-name, and `U+...` views, two carriers, four distances, and nine depths.
  A separate 18-case repeat was bit-exact.
- On 842 discovery items, equal-cell layer-31 glyph-to-name top-1 retrieval was
  `0.136580` against chance `0.001188`; glyph-to-codepoint retrieval was
  `0.001188`. All eight layer-31 carrier-by-distance glyph/name cells remained
  above chance.
- A post-outcome sensitivity retained the contrast among 760 five-token glyphs
  with one common three-token prefix and among 43 items with equal glyph/name
  token counts. It is not a fully token-isomorphic control.

The atlas had no primary semantic decision. Its complete descriptive analysis
includes cross-view retrieval/alignment, CKA correspondence, Unicode
group/subgroup neighborhood purity, carrier/distance cells, and token-structure
strata. It narrows simple codepoint-identity and glyph-length accounts but does
not identify a disentangled semantic variable.

Exit condition: met. All 28 canonical shards validated, the failed fast path and
bit-exact canonical validation are retained, and a compact public evidence
bundle is published. T9 subsequently froze one endpoint and multiplicity rule
from calibration/discovery evidence before forwarding the 292-item reserve.

### Confirmatory side track T9 — single-use semantic-atlas reserve

Status: complete —
`transport_robust_late_depth_glyph_name_alignment_confirmed`. T9 used all 292
deterministic `reserved_unrun` items exactly once to close the narrow late-depth
glyph/name alignment question.

- acquire only layer 31 with the existing three views, two carriers, and four
  distances at canonical batch size one;
- use one primary statistic: the minimum across all eight cells of
  glyph-to-name minus glyph-to-codepoint forward top-1 retrieval;
- require a one-sided common-permutation p-value at most `0.05` and a minimum
  cell contrast of at least `0.02`; and
- report every complete outcome as either confirmed or not confirmed under the
  frozen rule, without a secondary rescue.

The observed minimum eight-cell contrast was `0.171233` against the frozen
`0.02` floor. Zero of 19,999 common-permutation draws reached it, yielding
`p = 0.00005`. T9 therefore confirms only a model- and layer-specific
observational alignment on an untouched target set. It does not establish
semantic causality, a mechanism, behavior, tokenization independence, model
generality, or the whole Phase I claim. The complete result and compact evidence
bundle are published.

### Completed T10 — semantic-atlas cross-model replication

Status: complete —
`cross_model_replication_not_established_under_frozen_rule`.

T10 kept the T9 population and transport fixed across nine model/tokenizer
cells. Each model was tested with an unrestricted 292-item component and a
component whose official-name permutation was restricted within the exact
triple `(glyph, name, codepoint)` token-count strata. All nine IUTs were
statistically significant; the four core p-values were each `0.00005`, and the
registered `r = 3` of `m = 4` partial conjunction passed with `p = 0.0001`.

The combined primary was nevertheless negative because only Llama 3.2 3B base
and Qwen 2.5 7B base cleared the `0.02` practical floor in both components;
three core cells were required. The exact matched strata retained 281--287
items and did not erase the contrast, but this does not establish tokenizer
independence. Across the full nine-cell Holm family, Llama 3.2 3B base, Qwen
2.5 7B base, and Mistral 7B Instruct v0.3 passed the bounded statistical-plus-
practical cell rule.

The primary endpoint remains the final normalized hidden state returned in
`output.hidden_states[-1]`. The raw final decoder-block endpoint, monotone
four-point Qwen size profile, and related Mistral-Instruct checkpoint remain
descriptive. They cannot establish scale, tuning, semantic, causal,
independent-replication, or model-general claims. The complete result,
independent recomputation, and compact evidence are published. See the [result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md)
and [frozen protocol](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0.md).

### Completed T10-D — non-rescuing diagnostic decomposition

Status: complete; the registered T10 primary remains negative.

T10-D reconstructed 333 raw shards, 36 activation arrays, and 84,096 derived
scalar values with zero mismatches. Continuous glyph/name margins were positive
in all 72 cells, but item coverage was sparse across models, carrier-distance
profiles were model-specific, codepoint geometry was weak, and the raw-to-final
boundary varied by model. No item was a top-1 hit in all nine models. These
facts motivate a system-level decomposition question without selecting a
favorable T10 cell. See the [diagnostic report](SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md).

### Completed T11 — unusual-glyph decomposition atlas

Status: complete as an exploratory discovery atlas. Its reserve was unforwarded
at T11 completion; T12 later opened the complete 160-item ZWJ/regional subset
under a separate one-shot freeze.

T11 acquired all 843 fixed discovery items across nine model/tokenizer cells:
73,566 forwards in 477 resumable shards and 982,512 FP32 readout vectors. The
exact target-token-length wrong-label controls passed for every required
system. Returned-final glyph/name margins were positive in all 72 cells for
presentation, modifier, ZWJ, and regional systems, and in 65/72 keycap cells.
Strict first-token coverage was much lower for atomic and presentation systems,
so the exact-length result is not tokenizer independence.

The clearest narrow follow-up is the returned-final ZWJ
`presentation_or_fusion` contrast: 65/72 cells were positive, no cell had a
strictly negative descriptive interval, and eight of nine model-level context
medians were positive. Regional flags also showed positive whole-name and
component contrasts. In contrast, modifier and keycap decompositions were
bounded mixed/null patterns, cross-model item agreement was weak, and only
8/36 ordered Qwen profiles were strictly increasing. T11 therefore supports a
model-conditioned decomposition atlas, not a single landing pattern or a
semantic, causal, tokenizer-independent, scale, tuning, or model-general claim.

See the [result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md), [compact
evidence](../artifacts/glyph_system_decomposition_v0/README.md), and [frozen
protocol](GLYPH_SYSTEM_DECOMPOSITION_V0.md).

### Completed T12 — ZWJ and regional reserve confirmation

Status: complete; neither registered hypothesis was confirmed.

T12 froze two hypotheses before any reserve forward: ZWJ fused-form advantage
and a regional dual conjunction requiring both presentation/fusion and
component tracking. It then acquired every previously unforwarded ZWJ reserve
item (96) and regional-flag reserve item (64) across the same nine roles, two
carriers, and four distances. All 90 shards, 9,792 model forwards, and 39,168
returned-final FP32 vectors completed with zero intervention and generation
calls.

`H_ZWJ_FUSION` had statistic `0.000369`, raw `p = 0.05496`, and Holm
`p = 0.10992`. Regional presentation/fusion had statistic `0.002767` and
component `p = 0.03538`, but regional component tracking was `0.000666` with
`p = 0.12950`; the intersection-union/Holm decision was therefore
`p = 0.12950`. No model summary reached any registered practical floor. Both
hypotheses remain unconfirmed without alternate-endpoint rescue.

An analyzer-independent validator recomputed all 432 cell medians, three
49,999-draw shared-item swap tests, practical and heterogeneity gates, the
regional conjunction, and Holm correction with zero mismatches. T12 closes the
reserve question but establishes no emoji meaning, mechanism, causality,
behavioral steering, tokenizer independence, scale law, or model generality.
See the [complete result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) and
[compact evidence](../artifacts/glyph_system_reserve_confirmation_v0/README.md).

### Completed T13-EH harvest, T13-EA point analysis, and bootstrap execution freeze

Status: the harvest and registered F1–F6 point analysis are complete. The
post-outcome execution amendment now freezes 600 high-level estimands, 100
deterministic chunks, a counter-based resampling schedule, cross-runtime
sentinels, and a fail-closed merge. Production remains at 0/20,000. T13-C is
still a design space and is not authorized for confirmatory execution.

T13-EH front-loaded the GPU-only work while the furnace was available. It used
the already exposed 192-item T11 depth population, all 32 public prestage
targets, eight normalized depths, and all nine frozen model roles. All nine
roles completed the source bank; three prespecified base roles additionally
completed 383,232 intervention-response rows. No protected bank was opened.

T13-EA then completed the registered exploratory point analysis. F1–F5 use the
three pilot models; F6 uses all nine source roles. The original exact-JS zero
gate remains a preserved fail-closed procedural result. A separately frozen
v1 amendment passed the exact primitive no-op checks plus a bounded float32 JS
round-trip check before nonzero values were opened. Passing that numerical gate
is not a scientific result and does not claim exact JS. See the [point-analysis
result](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md), [zero-gate
amendment](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md), and [compact
evidence](../artifacts/emoji_steering_specificity_analysis_v0/README.md).

The [bootstrap execution v1 contract](EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.md)
closes the remaining computational ambiguity without presenting the exact
600-row marginalization roster as prospective. A bundle must replay all 600
public point values before any chunk can run. Mixed Mac/furnace chunks may be
merged only when three fixed sentinel replicate vectors are bit-identical.
This is execution readiness, not evidence that an interval has been computed.

T13's next broad question was whether structured source directions explain
intervention response beyond generic target susceptibility and null-direction
dependence. The discriminating design should combine exact token/prefix
controls, leave-one-wrapper-out directions, positive and negative
manifold/covariance-matched nulls, a frozen depth-0.875-versus-1.0 contrast,
response replication in the remaining six models, and generation endpoints.
The registered cluster bootstrap must finish before interval claims. Any later
confirmation requires a new untouched target bank outside the exposed research
context and cannot reuse T12 outcomes, P2, or retired C1 v1. Representation
geometry and behavioral intervention remain separate lanes. The competing
explanations and clean landing patterns remain in the [T13 decision
map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md). T14-X and T14-C have now executed
one frozen realization of that transition; their signed exploratory result and
negative selected-site causal result are reported separately below.

### Milestone 3 — Targeted causal localization

Status: complete with a negative selected-site intersection-union result. The
targeted-causal paper gate is closed, but no positive causal claim is authorized.

- T14-C was publicly frozen before T14-X outcome access;
- localization compared eight fixed `attn_out` / `mlp_out` sites at blocks
  24–27, plus a positive control and upstream sham, on 32 public targets;
- the frozen selector chose `mlp_out` block 24 before C1 v2 materialization;
- the new bank contained 192 untouched targets in 12 fixed strata;
- all explicit-zero, restoration, positive-control, and sham engineering gates
  passed;
- the treatment estimate was positive but below its floor, necessity was
  negative, and sufficiency was far below its floor, so the causal IUT did not
  reject;
- no alternate site, floor, endpoint, model subset, or rescue analysis may be
  promoted from this search.

Exit condition: completed as a valid negative causal experiment.
`causal_claim_authorized` remains `false`. Any multi-site or path-level follow-up
requires a new protocol and a new untouched bank.

### Completed T15-A — Emoji × word incongruence interaction

Status: complete as an exploratory seven-family result. It supplies a shared
non-additive response-fingerprint candidate and closes no Phase I paper gate.

T15-A balanced two emoji and two words within each of eight operational axes,
used both source orders and four wrappers, and compared the resulting
interaction direction with three structurally matched cross-axis checkerboards.
Four base models, two late depths, two doses, both signs, and all 32 public
targets produced 393,472 steering-response rows with zero generation calls.

At the primary dose, all 16 model × depth × sign A1 intervals were positive:
true within-axis interaction directions produced more coherent
full-vocabulary response fingerprints than the cross-axis controls. The
secondary families narrow that result. Individual joint-additivity residual
magnitude had zero positive intervals; response energy, word-versus-emoji main
effects, order, depth, and dose were heterogeneous. The recurring quantity is
therefore response shape, not a universal energy increase or behavioral flip.

The v0 analyzer failed closed on an incorrect A0 repeat assertion after reading
response values but before producing an output or printing model values. The
versioned post-open v1 repair changed only `8` to `16`; all estimands, endpoint
families, bootstrap schedules, and claim boundaries were unchanged. This
procedural limitation is part of the public result.

T15-A remains outcome-informed by T14 and uses public targets. It does not
authorize meaning, contradiction detection, causal, tokenizer-independent,
scale, or model-general claims. Any T15-C must use new axes, a new untouched
target bank, an independent model or backend, and prospectively frozen
necessity, sufficiency, and restoration tests on the interaction-residual
subspace. See the [result](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0_RESULTS.md),
[protocol](EMOJI_WORD_INCONGRUENCE_INTERACTION_V0.md), and [compact
closeout](../validation/emoji_word_incongruence_interaction_v0/t15a_closeout.json).

### Completed T15-B — Prospective emoji × word replication

Status: complete with support for the frozen two-model replication gate. It
satisfies Phase I gate 5 for the narrow T15-A operational response-shape
candidate, while authorizing no semantic or causal claim.

T15-B replaced all eight axes, all 48 target prompts, and both model roles.
SmolLM2 1.7B base and Mistral 7B Instruct v0.3 each completed 245,856 response
rows. Every true interaction was compared with all seven non-self cross-axis
checkerboards, strengthening T15-A's three-shift null family.

At magnitude `0.25`, the frozen R1 target median was `+0.020422` in SmolLM2
with interval `[0.012887, 0.031510]`, and `+0.060397` in Mistral with
`[0.056621, 0.062194]`. Both lower bounds exceeded zero under the predeclared
two-model intersection rule and one-sided Bonferroni alpha `0.025` per model.

The cell-level result remained heterogeneous: six of eight separate
primary-dose model × depth × sign intervals were positive and two were mixed.
A0 and A3 source diagnostics were mixed in all four model × depth cells;
response energy, main effects, order, depth, and dose also varied. The supported
quantity is a target-level operational response-shape contrast, not meaning,
contradiction detection, a behavioral effect, tokenizer independence,
instruction-tuning invariance, scale, or model-population generality.

The claim-specific R1 analysis is target-cluster and multiplicity aware.
Paper-wide statistical qualification remains open until the manuscript claim
table is frozen. See the [result](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md),
[protocol](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md), and [compact
closeout](../validation/emoji_word_incongruence_replication_v0/t15b_closeout.json).

### Completed T16 — Operational behavior, causal boundaries, and exact UTF

Status: all three frozen T16 lanes are complete. The behavioral lane supports
operational association and congruence; both causal lanes remain negative or
mixed under their registered conjunctions; the UTF lane is exploratory and
tokenizer-conditional.

- T16-OSC completed 768 behavioral rows across Gemma 2 2B IT and Mistral 7B
  Instruct v0.3. All four model-by-task gates passed. Meaning-choice accuracy
  was `0.953125` and `0.937500`; congruence accuracy was `0.761719` and
  `0.753906`.
- The Mistral T15-B residual-subspace lane completed 5,376 rows after a
  separately frozen batch-shape-only zero-guard repair. Treatment,
  sufficiency, and necessity medians were `-0.148438`, `-0.085938`, and
  `-0.054688`; the causal gate was not supported.
- T16-DP jointly patched eight late components over Llama blocks 24–27 on a
  fresh 192-target bank. Necessity passed at `+0.000871`, but sufficiency was
  `-0.000146` and treatment missed its `0.002` floor. The joint IUT did not
  reject.
- T16-UTF completed 2,880 factorial records across two models, six Unicode
  construction families, four depths, and five sequence lengths. `n=1` was an
  exact shared-prompt zero control. Cross-minus-within displacement intervals
  were positive in all eight model-by-depth cells, conditional on the recorded
  tokenizer paths.
- The exploratory T16-UTF-X1 side track expanded this surface to 515,808
  records, nine fixed model/tokenizer cells, 19 lengths through `n=500`, six
  order variants, five separators, and three anchor positions. Primary and
  `n=500` cross-minus-within were positive in all 36 model-by-depth cells.
  Exact-token-multiset order controls made contiguous blocking the largest
  order displacement in all 72 model-by-depth-by-family cells. The length
  curves were non-monotonic and do not authorize a scale law.
- Preserve the mechanistic dissociation: operational behavior, a replicated
  response fingerprint, and a sufficient causal mediator are not the same
  empirical object.
- Do not run an adaptive subset rescue on either causal bank. Any new
  localization study needs a new bank, a new freeze, and an endpoint chosen
  without inspecting these outcomes.

The [T16 paper story](PAPER_STORY_T16_V0.md) remains the stronger confirmatory
writing spine until a fresh glyph–name population is opened.
T16-UTF-X1 belongs in the appendix or repository evidence unless space permits
a short order-control result in the body. The next critical path is manuscript
claim freeze, figure generation from committed compact analyses, archive
checksums, and a fresh-eyes claim-boundary review—not another outcome-driven
furnace search.

### Completed T17-GN — Raw emoji to Unicode-name depth atlas

Status: complete as a frozen exploratory atlas on the prior-exposed T9/T10
population; it is not independent confirmation.

- T17-GN held the 292 items, three views, two carriers, four distances, and
  nine exact model/tokenizer cells fixed while expanding the returned-final
  endpoint to nine normalized depths.
- All 90 shards completed: 15,768 forwards and 567,648 FP32 readouts, with no
  generation or intervention.
- The equal-context official-name-minus-codepoint forward top-1 estimate was
  positive in all nine models from depth `0.375` through the final state.
  Token-count-matched point estimates were positive in all nine from `0.25`.
- The trajectory did not support one universal late transition. Peak depth was
  the first block in two models, `0.125` in one, `0.75` in one, and `0.875` in
  five.
- At the final state, paired item margins favored names in 9/9 models, while
  centered linear CKA favored names in only 4/9. Preserve this local-retrieval
  versus global-geometry dissociation.
- Independent validation exactly replayed every T10 returned-final
  unrestricted and token-count-matched carrier-by-distance contrast. It does
  not change T10's registered negative practical verdict.

The [T17 result](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) and
[candidate story](PAPER_STORY_T17_GLYPH_NAME_V0.md) define the bounded reading.
T16 Unicode-construction studies remain confound controls rather than proof of
visual glyph perception.

### Completed T18 — Fresh composite-glyph lexical confirmation

Status: the prospectively frozen primary is supported within the registered
model/tokenizer cells.

- T18 selected 192 multi-codepoint sequences before tokenizer measurement.
  Their exact UTF-8 surfaces were absent from the complete frozen 1,429-blob
  study tree, and every T11 identity was excluded.
- All 54 shards completed: 13,824 model forwards and 497,664 FP32 readouts,
  with zero generation and intervention calls.
- All four core cells passed both unrestricted and exact token-count-matched
  tests and both `0.02` practical floors. The registered `r = 3 of 4`
  partial-conjunction p-value was `0.0001`.
- Eight of nine registered cells met the full bounded rule. SmolLM2 was the
  exception because its unrestricted estimate, `0.017940`, missed the
  practical floor despite its small randomization p-value.
- Japanese-specific token-matched point estimates were positive in 9/9 as a
  non-rescuing secondary result.
- The internal path was heterogeneous: matched CKA favored names in only 3/9,
  only 8/192 items were positive in all four core cells, and peak depth varied.
- An analyzer-independent validator re-scanned the exposure boundary and
  independently recomputed all 18 randomization tests with no discrepancy.

The [T18 result](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0_RESULTS.md),
[paper story](PAPER_STORY_T18_FRESH_LEXICAL_V0.md), and
[frozen protocol](FRESH_COMPOSITE_GLYPH_LEXICAL_CONFIRMATION_V0.md) define the
claim boundary. T18 supports exact-surface-fresh lexical binding in the frozen
cells. It does not establish a pretraining holdout, rendered-glyph perception,
human meaning, tokenizer independence, a shared mechanism, or a scale law.

### Next T19 gate — Lexical breadth, symbol specificity, then causality

Status: option space only; no T19 population, endpoint, causal site, or
hypothesis family is frozen.

- Cross raw emoji with the official short name, a preselected alias or concise
  paraphrase, Japanese label, and literal codepoint identifier.
- Add named non-emoji Unicode symbols under matched token and label structure
  to test whether the relation is emoji-specific or a broader named-symbol
  phenomenon.
- Freeze one small primary contrast that separates official-label lookup from
  broader lexical-neighborhood retrieval. Multilingual and system profiles
  remain secondary unless separately powered and registered.
- Preserve an untouched evaluation bank for a later removal, addition, and
  restoration experiment. T18 consensus and model-private items may define
  prespecified strata, but must not select the sole favorable causal site.
- Compare late `attn_out` and `mlp_out` only after fixing a site-selection rule
  that does not reuse the largest T18 cell or depth as confirmatory evidence.

### Milestone 4 — Replication and boundary mapping

Status: the T15-A operational response-shape candidate now has a prospective
independent-model replication; broader architecture and tokenizer boundary
mapping remains planned.

- repeat the confirmatory cell in raw Transformers or TransformerLens, not only adapter-level parity;
- replicate across at least one additional model family and tokenizer;
- examine checkpoint emergence where weight histories are available;
- test robustness across prompt domains and target-template families;
- separate architecture-specific observations from cross-model regularities.
- test the frozen T13-EA response predictions in the six roles that currently
  contribute source geometry but not the full intervention-response surface.
- preserve T14-X's signed six-model, two-depth result: 9/12 headline JS
  intervals were positive and 3/12 negative, with a non-monotonic Qwen profile;
- do not promote that exploratory breadth to a scale law or independent
  confirmatory replication.
- retain T15-B's supported two-model intersection decision as the prospective
  replication of T15-A's response-shape candidate;
- keep its 6/8 positive and 2/8 mixed primary-dose cells visible, and do not
  promote two deliberately selected models to a model-population claim;
- treat T15-C as a separate causal lane with a new untouched bank, not as an
  adaptive extension or rescue of T15-B.

Exit condition: the paper can state clearly which findings replicate and which remain GPT-2-specific.

### Milestone 5 — Confirmatory statistics

Status: T14-C and T15-B now have claim-specific target-cluster analyses;
T15-B R1 also has a frozen model-level multiplicity rule. Paper-wide
qualification remains open.

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
- complete the registered T13-EA 20,000-replicate cluster bootstrap before
  promoting any point estimate to an interval-based paper statement.
- retain the T14-C 20,000-replicate target bootstrap and fixed 99,999-draw
  paired sign-flip result without selecting a replacement site after its
  non-rejection.
- retain T15-A's complete A0–A6 families and post-open repair disclosure; its
  percentile intervals are descriptive and may not be promoted to a primary
  multiplicity-adjusted claim.
- retain T15-B R1 as the only multiplicity-qualified replication decision in
  that experiment; its A0–A6 cell intervals remain secondary diagnostics.

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

Current reading: gates 1–3 have GPT-2-specific operational evidence, but the
multifamily tokenizer census does not extend gate 3 across tokenizers. Any such
extension needs separately frozen, tokenizer-specific control panels. T2 is a
completed first observational use of two such regimes; neither predeclared
midpoint cell rejected after Holm correction, so it records bounded negative/
mixed cross-model evidence and does not close the causal or independent-
replication gates. T3 then used the five-family matched-slot factorial and
found OLMo-only recurrence under an exact shared final-token construction;
Gemma's atomic-token omnibus did not reject. T4 then moved the readout to a
common token one position later and again found OLMo-only recurrence in both
fixed suffix contexts. This rejects a strictly current-token-only description
but leaves short-range propagation from OLMo's structured prefix sufficient.
T2–T4 are not causal tokenizer contrasts, independent replications, or semantic
results and close no paper gate. T5 and T6 rejected no registered model-level
distance-attenuation conjunction. T7 then prospectively rejected the fixed
distance-1 plus early-minus-late depth IUT in one selected Mistral base cell,
but its post-T6 endpoint/model selection and related Instruct reference prevent
independent-confirmation or instruction-tuning claims. T5–T7 therefore sharpen
the depth-dependent observational account without closing gates 4 or 5. T8/T9
then added a separate claim-specific prospective confirmation: one endpoint was
frozen before a deterministic 292-item reserve was forwarded, and its single
global minimum-cell randomization test passed. This supplies clean Mistral-
specific evidence for gates 1, 2, 6, and 7, but it is neither independent-model
replication nor semantic or causal evidence. T10 subsequently preserved that
population and transport across nine frozen cells. Exact token-count matching
did not erase the contrast, and the statistical partial conjunction passed,
but only two of four core cells met the practical floor. T10 therefore records
a claim-matched, mixed cross-model result rather than independent replication,
scale, tuning, semantic, or model-general evidence; it does not close gate 5.
T10-D preserves that decision. T11 completed its exploratory discovery atlas.
T12 then opened only the frozen 96-item ZWJ and 64-item regional reserve subsets
under a separate one-shot protocol; neither registered hypothesis was
confirmed. This is a completed negative confirmation, not a paper-gate closure
for semantics, causality, or model generality. T13-EH adds an exploratory,
acquisition-only tensor surface over exposed items and public targets. It does
not close a paper gate. T14-X then completed a separately frozen six-model,
two-depth expansion: all 12 headline JS intervals excluded zero, but the signed
pattern was 9 positive and 3 negative and the Qwen profile was non-monotonic.
It is exploratory boundary mapping, not independent confirmation or a scale
law. T14-C was frozen before that outcome was opened, selected `mlp_out` block
24 on public targets, and tested it once on a new untouched 192-target bank.
All engineering controls passed, but the treatment, necessity, and sufficiency
IUT did not reject. Gate 4 is therefore complete with a negative result; no
causal mediator claim or adaptive second-site search is authorized.
T15-A then completed a separately frozen four-model emoji × word factorial.
Its primary response-fingerprint intervals were positive in all 16
model × depth × sign cells, while source-residual magnitude, response energy,
main effects, order, depth, and dose remained heterogeneous. The result is an
exploratory interaction-fingerprint candidate. Public targets, outcome-informed
role selection, descriptive intervals, and the disclosed post-open
implementation repair prevent it from closing gates 1, 2, 5, or 6.
T15-B then replaced every axis, target, and model role before outcome access,
used all seven non-self cross-axis controls, and supported its frozen
two-model R1 intersection rule. This satisfies gate 5 for the narrow
operational response-shape candidate. Its claim-specific target-cluster and
multiplicity qualification strengthens gate 6, but the paper-wide claim table
still requires a separate freeze.
Final paper-wide qualification for gate 6 remains open because the rebuilt
GPT-2 prototype analysis was post hoc. Gates 8 and 10 remain open. Gate 9 must be
maintained on every public documentation change. The English paper remains the
Phase I endpoint; the current repository is an evidence-bearing research
release, not a finished manuscript.

## Beyond Phase I

Possible Phase II directions include expansion beyond E1's five frozen emoji
blocks, multimodal tokenizers, learned feature-basis analysis,
intervention-orbit studies, and comparisons across training checkpoints. They
remain outside the current commitment until the Phase I paper is complete.
