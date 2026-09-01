# Phase I paper outline

[日本語](PAPER_OUTLINE.ja.md) · [T17 alternative story](PAPER_STORY_T17_GLYPH_NAME_V0.md) · [T17 depth-atlas result](GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS.md) · [Current T16 story](PAPER_STORY_T16_V0.md) · [Roadmap](ROADMAP.md) · [T16 operational and causal result](T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS.md) · [T16 late-band result](T16_DISTRIBUTED_LATE_BAND_V0_RESULTS.md) · [T16 exact-UTF result](T16_UTF_IDENTITY_MIXING_V0_RESULTS.md) · [T15-B replication](EMOJI_WORD_INCONGRUENCE_REPLICATION_V0_RESULTS.md) · [T12 reserve result](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md) · [T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) · [T11 exploratory result](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [T10 cross-model result](SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md) · [Milestone 2 results](MILESTONE2_RESULTS.md) · [Baseline results](RESULTS_V1.md)

## Working title

**Behaviorally Legible, Mechanistically Unresolved: Separating Emoji Fingerprints, Congruence, and Causal Mediation**

The Phase I manuscript will be written in English. A Japanese public summary will accompany the preprint, but the English manuscript is the controlling scientific text.

## InterpScience 2026 submission sprint

The official [InterpScience call for papers](https://interpscience.github.io/cfp)
lists **September 1, 2026, Anywhere on Earth** as the deadline. It allows short
papers up to five pages and long papers up to nine pages, excluding references
and appendix. The working target is a long paper; the five-page format remains
a fallback if the evidence-bearing narrative cannot be edited cleanly in time.

Internal schedule:

- **August 29:** freeze the scientific core at T12; land its bilingual result,
  independent validation, public evidence, and figure/table inputs.
- **August 30:** produce the first complete English draft, prioritizing methods,
  T10–T12 results, limitations, and the negative-result narrative.
- **August 31:** freeze claims and figures, run reproducibility and double-blind
  checks, and move all unvalidated T13 material to future work.
- **September 1 JST:** upload and verify the submission rather than relying on
  the final AoE hours.

T13-C is not on the critical path. A bounded T13 exploratory panel may be added
only if it is complete and independently validated before the August 31 paper
freeze; otherwise the decision map is the future-work contribution.

## Proposed central claim

The current paper centers a separation rather than a circuit discovery.
Emoji-word response fingerprints recur prospectively, and frozen two-choice
association and congruence judgments succeed in two instruction-tuned models.
The tested T15-B residual subspace nevertheless moves explicit mismatch
judgment oppositely to its registered causal prediction, while a separate
eight-component late band passes necessity but fails sufficiency and the full
mediation gate. Exact-UTF controls add a tokenizer-conditional geometry result,
not a semantic or tokenizer-independent claim.

The detailed submission-ready narrative, five-page fallback, figure spine, and
allowed/disallowed claim table now live in [T16 paper story v0](PAPER_STORY_T16_V0.md).
The older sections below remain an evidence registry and historical design
record; they no longer define the manuscript's lead claim by themselves.

## T17 alternative representation spine

T17-GN now offers a narrower alternative lead: trace a raw emoji surface to
its official Unicode name relative to its literal codepoint identifier across
nine models and nine depths. The name-minus-codepoint top-1 estimate is
positive in all nine models from normalized depth `0.375`, but peak depths
range from the first block to `0.875`. Final paired margins favor names in 9/9
models while centered linear CKA does so in 4/9. This supports item-specific
lexical correspondence more strongly than a global name manifold.

The complete argument and its fresh-population gate live in the
[T17 alternative story](PAPER_STORY_T17_GLYPH_NAME_V0.md). Because the 292
items were exposed in T9/T10, T17 is exploratory. Until a new label population
is prospectively confirmed, the T16 behavior/causality dissociation remains
the stronger confirmatory spine and T17 is either an alternative atlas paper
or a compact representation section.

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

## Current tokenizer-control design evidence

The frozen multifamily census completed 14 tokenizer entries over 115 items and
four contexts with zero model forwards and zero protected-target access. The
entries formed seven exact output classes on that fixed surface. Neither blue
circle nor blue square had one fixed-panel candidate matching both token count
and a one-token prefix across every class in any fixed pairwise context.

The manuscript may use this as descriptive motivation for tokenizer-specific
control design and as a limitation on cross-tokenizer transport. It must not
present the census as activation evidence, confirmation, tokenizer-independent
structure, or completion of a paper gate. Any later cross-tokenizer activation
result must bind its control set prospectively per tokenizer output class.

## Current multifamily observational result

The frozen T2 study tested one midpoint circle-minus-square parallelism endpoint
in two predeclared raw-glyph `resid_post` cells. Gemma 2 2B 4-bit produced
`T = 0.114857969`, raw `p = 0.058333333`, and Holm `p = 0.116666667`. OLMo 3
7B BF16 produced `T = 0.024628040` and raw/Holm `p = 0.275`. Neither rejected,
so the registered pattern is `no_dual_model_recurrence`.

All ten fixed-depth rows remain available, but the four non-midpoint rows per
model have no multiplicity decision and cannot replace the primary layer. The
paper may use T2 as bounded negative/mixed observational evidence against the
current model-general shape-axis claim. It must not infer a scale,
quantization, tokenizer, node, or model-family cause because those factors are
confounded. T2 is not an independent-backend replication and does not change
Milestone 2 or the causal candidate.

## Current matched-slot observational result

The separately frozen T3 study used the five public ten-emoji families as an
exact 5 × 10 factorial. After family centering, its primary statistic was the
equal-depth mean slot sum-of-squares fraction across five fixed depths. Gemma 2
2B 4-bit, where all 50 glyphs are distinct atomic tokens, produced
`T = 0.204304805`, null mean `0.199984463`, and Holm `p = 0.208500`. OLMo 3
7B BF16, where each family reuses the exact final slot token, produced
`T = 0.500391869`, null mean `0.200184835`, and Holm `p = 0.000100`.

The registered pattern is `olmo_only_token_structured_recurrence`. OLMo's
fixed-depth slot fraction declined from `0.994722` to `0.295828`; the five
per-depth p-values are secondary and cannot replace the all-depth endpoint.
The paper may present this as tokenizer-conditioned observational evidence:
shared token structure is a sufficient alternative explanation for the OLMo
result. It must not infer tokenizer causality, semantics, confirmation, or a
model-scale, precision, backend, or node effect from the two confounded cells.

## Current common-suffix carryover result

The prospectively frozen T4 study moved the readout one token later. Every raw
glyph sequence was preserved exactly and followed by either one common period
token or one common newline token. The primary statistic averaged both fixed
contexts and all five fixed depths. Gemma produced `T = 0.203443011`, null mean
`0.200044692`, and Holm `p = 0.302950`. OLMo produced `T = 0.537464703`, null
mean `0.199977865`, and Holm `p = 0.000100`.

The registered pattern is `olmo_only_common_suffix_carryover`. OLMo's
secondary period and newline statistics were `0.538985382` and `0.535944025`.
The paper may state that T3 recurrence is not confined to reading the shared
slot token itself and remains observable one common token later in both fixed
contexts. It must also state that short-range propagation from OLMo's
structured prefix remains a sufficient explanation. T4 is not semantic,
causal, confirmatory, tokenizer-independent, or a model-scale contrast.

## Current carrier-distance result

The prospectively frozen T5 study kept the complete input and current carrier
token fixed while reading the same geometry at distances 1, 2, 4, and 8 after
the raw glyph. Its only primary decision was a model-level intersection-union
test requiring both distance-1 recurrence and a positive fixed log-distance
attenuation contrast. The three raw IUT p-values were `0.573250` for Gemma,
`0.188000` for Llama, and `0.997700` for OLMo; their Holm-adjusted values were
`1.000000`, `0.564000`, and `1.000000`. No model rejected, so the registered
pattern is `no_model_distance_attenuation`.

Llama and OLMo each had a distance-1 component raw p-value of `0.000050`, but
neither passed the fixed attenuation component required by the IUT. Their descriptive distance-8 slot fractions
were `0.369105` and `0.527099`; Gemma's was `0.204289`. These tail values and
the complete distance-by-depth interaction are secondary and carry no
multiplicity decision. T5 therefore supports a bounded negative result for the
simple model-level attenuation hypothesis, not monotonic decay, disappearance,
duration, persistence, semantics, mechanism, causality, confirmation,
tokenizer independence, backend parity, or direct cross-model magnitude
comparison. Llama's MLX Stage-A parity also remains unqualified.

## Current dense CUDA carrier-distance result

T6 prospectively retained T5's full observational endpoint in four selected
BF16 Transformers/CUDA cells. The raw IUT p-values were `0.770900` for Gemma 2
2B IT, `0.845150` for Gemma 3 4B IT, `0.469750` for Mistral 7B Instruct v0.3,
and `0.975750` for Gemma 3 12B IT; all Holm-adjusted values were `1.000000`.
The registered pattern is `no_dense_model_distance_attenuation`.

Mistral's distance-1 component was at the `0.000050` permutation floor, but its
attenuation component was `p = 0.469750`. Its distance-8 component and Gemma 3
12B's nominal tail are secondary, without an authorized multiplicity decision.
The roster was selected after T5, all four cells are instruction-tuned, and the
Gemma 3 4B/12B pair is only one selected pair. T6 therefore adds a bounded dense
negative replication of the conjunction, not confirmation, backend parity,
tokenizer equivalence, or a scale effect.

## Current Mistral semantic-atlas confirmation result

T8 selected a fixed layer-31 retrieval contrast after inspecting only its 842
discovery items. T9 then froze all 292 deterministic `reserved_unrun` items,
two carriers, four distances, one primary minimum statistic, a `0.02`
practical floor, and 19,999 common permutations before any reserve forward.

The reserve minimum glyph-to-official-name minus glyph-to-codepoint top-1
contrast was `0.171233`; every one of the eight carrier-distance cells cleared
the floor. No null draw reached the observed minimum, giving the prespecified
one-sided `p = 0.00005`. Centered linear CKA favored glyph/name in seven of
eight cells, with a `-0.007682` contrast at `article_a`, distance 8.

The paper may therefore describe prospectively confirmed, model-specific,
item-level correct-name alignment at late depth. It may not call this human
emoji meaning, semantic causality, uniform global-geometry superiority,
tokenizer independence, behavioral relevance, or model generality.

## Current T10 cross-model replication result

T10 held the T9 population and transport fixed across nine prospectively
frozen model/tokenizer cells. Every model passed the statistical IUT between
the unrestricted and exact three-view token-count-matched components. The four
core p-values were each `0.00005`, so the `r = 3` of `m = 4` Bonferroni partial
conjunction passed with `p = 0.0001`.

The registered primary was still negative. Only Llama 3.2 3B base and Qwen 2.5
7B base met the `0.02` practical minimum in both components; OLMo 2 1B base and
Gemma 2 2B IT did not, leaving `2/4` practical core passes where `3/4` were
required. Across the nine-cell Holm family, the bounded passes were Llama 3.2
3B base, Qwen 2.5 7B base, and Mistral 7B Instruct v0.3.

Exact token-count matching retained 281--287 items per tokenizer and did not
erase the contrast. This narrows one token-length account but does not establish
tokenizer independence. The raw-block endpoint, four-point Qwen profile, and
related Mistral-Instruct result are descriptive only. The paper must preserve
the registered wording
`cross_model_replication_not_established_under_frozen_rule` and must not infer
scale, tuning, semantics, causality, independent replication, or model
generality.

## Completed T11 exploratory extension

T10-D preserves the negative T10 primary while showing positive continuous
margins in all 72 cells, sparse cross-model item coverage, model-specific
carrier-distance profiles, weak codepoint geometry, and model-conditioned
raw-to-final changes. Its independent reconstruction checked 333 shards, 36
activation arrays, and 84,096 scalar values with zero mismatches. These facts
motivate T11 but do not select a favorable T10 cell.

T11 froze a nine-cell glyph-system decomposition atlas before any T11 model
forward. It then completed all 843 acquisition items, 477 shards, 73,566
forwards, and 982,512 FP32 readout vectors. Its separately assigned 268-item
reserve had zero model forwards at T11 completion. The atlas includes exact token-length
wrong-label controls, a complete two-carrier by four-distance grid,
raw-last-block and returned-final endpoints, and a fixed 192-item
normalized-depth subset.

Every required exact target-token-length control passed. Returned-final
glyph/name margins were positive in all 72 cells for presentation, modifier,
ZWJ, and regional systems and in 65/72 keycap cells. The strongest narrow
decomposition candidate was ZWJ `presentation_or_fusion`: 65/72 cells were
positive, no descriptive interval was strictly negative, and eight of nine
model-level context medians were positive. Regional flags showed a secondary
dual whole-name/component pattern. Modifier and keycap decompositions were
bounded mixed/null results.

The atlas remains model-conditioned: cross-model item agreement was weak,
strict first-token coverage was sparse for some systems, and only 8/36 ordered
Qwen profiles were strictly increasing. It cannot rescue T10 or establish
semantics, mechanism, causality, scale, tuning, tokenizer independence, or
model generality.

## Completed T12 one-shot reserve confirmation

T12 separately froze the model family, returned-final endpoint, practical
floors, context rule, exact-length and strict-prefix controls, heterogeneity
gates, and two-hypothesis Holm family before opening any reserve item. It then
acquired the complete ZWJ reserve (96 items) and regional-flag reserve (64
items) across all nine roles and eight contexts: 90 shards, 9,792 forwards, and
39,168 FP32 vectors.

Neither registered hypothesis was confirmed. `H_ZWJ_FUSION` had statistic
`0.000369`, raw `p = 0.05496`, and Holm `p = 0.10992`. Regional
presentation/fusion was weakly directional (`0.002767`, component
`p = 0.03538`), but regional component tracking was `0.000666`,
`p = 0.12950`; the required intersection-union/Holm decision was therefore
`p = 0.12950`. All three components missed their practical floor, with zero of
nine model summaries reaching it.

The manuscript should present T12 as a prospective negative confirmation that
attenuates the strongest T11 discovery patterns. It is evidence for the value
of untouched reserves, practical floors, and model-heterogeneity gates, not
evidence that models lack emoji representations. An analyzer-independent
validator recomputed 432 cell medians, all three 49,999-draw tests, and every
decision gate with zero mismatches.

## Completed T13-EA exploratory point analysis

T13-EH completed the nine-role source bank and the three-pilot, 383,232-row
intervention surface over exposed source items and public targets. T13-EA then
completed the registered F1–F6 point analysis. Its historical v0 exact-JS gate
remains a preserved fail-closed procedural result; the separate v1 amendment
passed exact primitive no-op checks plus a bounded float32 JS round-trip check.
That amendment neither claims exact JS nor supplies scientific evidence.

The point estimates support a narrower organizing question than unique emoji
specificity: when do structured source directions explain intervention response
beyond generic target susceptibility and null-direction dependence? F1–F5 use
three pilot models, while F6 source geometry spans all nine roles. Exact
token/prefix matching, wrapper holdout, signed manifold/covariance-matched
nulls, response replication in the remaining six models, and generation
endpoints are still absent. The registered cluster bootstrap remains at
0/20,000. T13-EA therefore has no primary significance decision or
confirmatory verdict. See the [result](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md),
[zero-gate amendment](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md),
and [compact evidence](../artifacts/emoji_steering_specificity_analysis_v0/README.md).

## Research questions

1. Do glyph-derived activation directions produce output fingerprints that repeat across held-out target prompts?
2. Do those fingerprints repeat across separately estimated source directions?
3. Do they exceed matched random-direction and generic-glyph controls under scalar-balanced intervention?
4. Which observed effects survive the prespecified token-count and prefix-panel matched controls?
5. Can a prespecified component or path intervention selectively remove and restore the candidate effect?
6. Which results replicate across execution backends, tokenizers, or model families?
7. In a token-isomorphic exploratory panel, how much matched-slot recurrence transfers across middle-token families, and how large is the residual within-family excess?
8. In a frozen five-family grid, does matched-slot activation geometry recur in an atomic-token cell and in a cell with an exact shared final slot token?
9. Does the matched-slot geometry remain observable at a common token exactly one position after the raw glyph?
10. Across fixed distances 1, 2, 4, and 8 in repeated common-token carriers, does distance-1 recurrence coexist with a prespecified positive log-distance attenuation contrast?
11. Does that complete fixed carrier-distance conjunction recur in four selected dense instruction-tuned Transformers/CUDA cells?
12. Does the fixed layer-31 glyph/name-versus-codepoint retrieval contrast reproduce across every carrier-distance cell in a deterministic untouched Mistral reserve?
13. Does that same returned-final-state retrieval contrast meet both the statistical and practical replication rules in at least three of four frozen core model/tokenizer cells after exact token-count matching?
14. Across frozen multi-codepoint glyph systems, do matched-label margins track whole-sequence names, deterministic component labels, or decomposed forms, and at which normalized depth or final-norm boundary do the nine cells diverge?
15. Do the frozen T11 ZWJ fusion and regional dual candidates reproduce at prespecified statistical and practical magnitude in their complete untouched reserve subsets?
16. Do structured emoji-source directions predict intervention response beyond baseline target susceptibility and signed, manifold/covariance-matched null directions after exact token/prefix and wrapper-holdout controls?

Questions 1–3 are exploratory baseline questions. Milestone 2 gives a mixed answer to question 4, subject to the open inferential qualifications. T2 gives a bounded negative/mixed observational answer to one narrow part of question 6, but independent-backend and claim-matched replication remain required before the paper freezes a stronger claim. Question 5 remains open.
Question 7 is answered only descriptively by E1 and is not promoted to a
confirmatory or causal research question.
T3 gives a split answer to question 8: OLMo rejected and Gemma did not. The
question remains observational because token structure is confounded with the
other model-cell differences.
T4 gives the same split answer to question 9 across two fixed suffix contexts.
It rules out a strictly current-token-only description, not short-range prefix
propagation.
T5 gives a negative answer to the fixed model-level conjunction in question 10:
no model passed both components after Holm correction. Llama and OLMo had
distance-1 component raw p-values at the permutation floor, but their
attenuation components did not reject. Distance-8 and
distance-by-depth patterns remain secondary descriptions rather than rescued
duration or layer-specific claims.
T6 gives the same top-level negative answer to question 11: none of its four
model IUTs passed Holm. Mistral's distance-1 component recurred, but its
attenuation component did not reject. T6 is prospective only for its own unseen
outcomes and is not independent confirmation of T5.
T8/T9 give a positive answer to question 12 under the frozen rule. All 292
reserve items were acquired once, and every carrier-distance contrast exceeded
the practical floor while the global minimum statistic reached the permutation
floor. This is untouched-target replication within one model and layer, not
independent model-family replication.
T10 gives a negative answer to question 13 under its frozen combined rule. The
partial conjunction passed statistically, and matching did not erase the
contrast, but only two of four core cells passed the practical floor. The
result is mixed evidence across a fixed roster, not an independent-replication,
scale, tuning, semantic, causal, or model-general claim.
T11 gives an exploratory, non-confirmatory answer to question 14: no single
landing pattern dominates. ZWJ fusion is the strongest narrow candidate,
regional flags show a secondary dual pattern, and other systems remain mixed
or bounded nulls. T12 gives a negative answer to question 15 under its frozen
combined rules: neither candidate was confirmed, and no component reached its
practical floor in any model summary. This closes the reserve question without
changing T10 or converting the result into a semantic null.
T13-EA gives only a point-estimate, exploratory decomposition of question 16.
It motivates the structured-source-versus-generic-susceptibility distinction,
but cannot decide it until the matched controls, signed nulls, remaining-model
response replication, generation endpoints, and registered bootstrap are
complete under a new freeze.

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
- T13-EA F1–F6 point estimates as a separate exploratory block, with the v0
  fail-closed zero-gate history, v1 numerical amendment, three-pilot versus
  nine-source-role scope, and pending 20,000-replicate bootstrap explicit.

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

- report T2 as a frozen two-cell non-recurrence result, with all fixed depths
  and its family/scale/precision/tokenizer/node confounding visible;
- report T3 as a separately frozen five-family matched-slot result: Gemma
  non-rejection and OLMo rejection under an exact shared-final-token contract,
  with all fixed depths and the confounded cell differences visible;
- report T4 as a separately frozen common-suffix carryover result: Gemma
  non-rejection and OLMo rejection across the fixed period/newline omnibus,
  with all 20 context-by-depth rows visible;
- report T5 as a separately frozen three-model carrier-distance result: no
  model passed the recurrence-plus-attenuation IUT, with all 120
  carrier-by-distance-by-depth rows visible and no subcell promoted;
- report T6 as a separately frozen four-model dense CUDA result: no model
  passed the same conjunction, with all 160 rows visible, Mistral's component
  split retained, and no scale, tail, or depth subcell promoted;
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
- T13-EA structured source directions versus generic target susceptibility,
  positive-only random-null limits, wrapper dependence, and the distinction
  between a depth-0.875 relative peak and larger generic final-depth response.
- E1 family identity is exactly confounded with the middle GPT-2 token, while
  the first and third tokens are shared; its transfer pattern cannot establish
  a semantic or tokenizer-independent family representation.
- T3's OLMo recurrence follows an exact shared final-token construction and
  weakens with depth; the cross-cell split cannot identify token causality or a
  scale, precision, architecture, backend, or node effect.
- T4 moves the current token to a common suffix and still finds OLMo-only
  recurrence; this narrows the account to contextual carryover but does not
  identify its mechanism, duration, or semantic content.
- T5 rejects no model under the fixed recurrence-plus-attenuation conjunction.
  Llama and OLMo remain descriptively elevated at distance 8, while early
  captured depths decline more than later depths; neither observation has an
  inferential decision or licenses a duration, monotonicity, persistence, or
  selected-layer claim.
- Llama's observational T5 cell does not qualify MLX parity; backend agreement
  remains an engineering gate rather than an inferred property of the result.
- T6 repeats the negative conjunction across four selected dense CUDA cells,
  but the post-T5 roster, instruction tuning, tokenizer differences, and single
  Gemma 3 pair prevent confirmation, equivalence, or scale inference.
- one complete C1 v1 record was exposed in a research-agent context without
  experimental use; the bank is retired, and future causal work requires a new
  versioned bank.

### 9. Reproducibility statement

- code, configs, revisions, hashes, and environment;
- raw-ledger archival location;
- compact public evidence manifest and omitted files;
- exact commands for parity, run, audit, and figure generation.
- complete T3 arrays, rows, repaired analysis, transfer receipt, and public
  manifest, with the pre-outcome serialization-repair chain retained.
- complete T4 arrays, all 20 rows, joint analysis, three-point transfer
  receipt, and public manifest.
- complete T5 arrays for all three models, all 120
  carrier-by-distance-by-depth rows, joint analysis, verified transfer receipt,
  and public manifest.
- complete T6 arrays for all four models, all 160 rows, joint analysis,
  lifecycle/start-gate evidence, verified return receipt, and public manifest.
- T8/T9 discovery and reserve evidence, followed by T10's nine compact
  prediction sets, complete cell metrics, run/summary/session receipts,
  nested shard-ledger bindings, independent recomputation, and checksummed
  external 1,212,819,072-byte raw-activation archive.

## Planned main figures

1. Experimental flow from sealed glyph sources to held-out output fingerprints.
2. Layer × strength fingerprint advantage with every seed shown.
3. Same-glyph, cross-glyph, and random-control distributions by layer.
4. Cross-seed reproducibility with target-cluster uncertainty.
5. Dose and sign-flip diagnostics.
6. Token-count/prefix-panel control results, fixed- versus rebuilt-prototype uncertainty, and any later causal intervention.
7. E1 source-family × prototype-family transfer matrices at layers 2 and 4,
   labeled exploratory and separated from the confirmatory claim family.
8. T2 fixed-depth shape-axis profile for Gemma and OLMo, with only the midpoint
   marked primary and the two Holm decisions shown separately from descriptive
   layer p-values.
9. T3 all-depth matched-slot primary result and full depth profiles, separating
   the Gemma atomic-token and OLMo shared-final-token contracts.
10. T4 common-suffix primary result and both context-by-depth profiles,
    emphasizing the one-token position shift and the remaining prefix account.
11. T5 model-level IUT components and complete distance-by-depth profiles,
    separating the sole primary decisions from descriptive distance-8 tails and
    depth interactions.
12. T10 unrestricted-versus-matched minimum contrasts for all nine cells,
    separating the statistical partial conjunction from the failed practical
    core-count rule; the Qwen ladder and raw-block endpoint remain secondary.
13. T11 system-by-view matched margins, decomposition contrasts, retrieval
    breadth, normalized-depth trajectories, raw-to-final changes, and
    cross-model heterogeneity, labeled exploratory and separated from any later
    T12 reserve result.

## Planned main tables

1. Model, tokenizer, backend, software, and artifact identity.
2. Parity qualification gates and latency scope.
3. Standard-run integrity and control counts.
4. Confirmatory effect sizes, intervals, and adjusted p-values.
5. Negative results, failed gates, and missing measurements.
6. Cross-backend and cross-model replication.
7. T2 primary and all fixed-depth observational results, labeled negative/mixed
   and non-confirmatory.
8. T3 primary model-level statistics and all fixed-depth rows, labeled
   tokenizer-conditioned and observational.
9. T4 primary model-level statistics, both context summaries, and all 20
   context-by-depth rows, labeled carryover and observational.
10. T5 distance-1, attenuation, IUT, and Holm results for all three models plus
    all 120 secondary rows, labeled exploratory, observational, and
    non-confirmatory.
11. T10 model-cell minima, IUT and Holm values, core partial conjunction,
    practical core count, matched item coverage, and explicit negative primary.
12. T11 required and strict token-control coverage, system-level cell counts,
    decomposition contrasts, and model-conditioned heterogeneity.

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
| The exact T2 midpoint shape axis recurs across Gemma and OLMo | not supported; neither cell rejected after Holm correction | retain as bounded negative/mixed observational evidence; do not replace the midpoint or attribute the difference to scale |
| Matched-slot geometry recurs in both T3 tokenizer regimes | not supported; OLMo rejected but Gemma did not | retain the registered `olmo_only_token_structured_recurrence` split and its token-structured alternative explanation |
| OLMo T3 recurrence proves tokenizer causality or emoji meaning | not supported | require a causally identified near-matched tokenizer or token intervention; do not infer it from the two confounded cells |
| OLMo T3 recurrence is confined to reading the shared slot token itself | not supported by T4; it remains observable one common token later in both fixed contexts | report `olmo_only_common_suffix_carryover`; T5 is now complete and does not support the fixed model-level attenuation hypothesis |
| T4 common-suffix carryover proves semantics or a causal mechanism | not supported | require identified interventions and near-matched controls; short-range structured-prefix propagation remains sufficient |
| Matched-slot recurrence follows the fixed simple carrier-distance attenuation profile | not supported; no T5 model passed the recurrence-plus-attenuation IUT after Holm correction | retain `no_model_distance_attenuation` as a bounded negative result; do not replace the primary with a distance, carrier, or depth subcell |
| Llama or OLMo distance-8 values prove persistence, duration, meaning, or mechanism | not supported; tail and depth-interaction values are secondary without multiplicity decisions | require a new prospectively powered duration or mechanism assay and independent backend qualification |
| The T9 returned-final-state item/name alignment meets the frozen cross-model replication rule | not established by T10; the statistical partial conjunction passed, but only two of four core cells met the practical floor | preserve the negative primary; require a newly justified independent replication for any stronger final claim |
| Exact token-count matching removes the T10 item/name contrast | not supported; all nine matched components remained significant and close to the unrestricted minima | retain the bounded token-count result without calling it tokenizer independence |
| The monotone T10 Qwen profile establishes a scale law | not supported; four checkpoint cells are descriptive and size remains confounded | require a dedicated size-identification design |
| T11 establishes whether emoji meaning is compositional or lexicalized | not established; the completed atlas has system-specific, model-conditioned operational contrasts rather than one semantic landing pattern | report the discovery atlas as exploratory and T12 as its separate negative confirmation |
| T12 confirms ZWJ fusion or a regional dual structure | not supported; both registered hypotheses failed, and all components missed their practical floors | preserve the one-shot negative result; do not rescue it with another endpoint, layer, or reserve subset |
| T13-EA establishes unique emoji steering specificity | not supported; exploratory point estimates mix source-form structure, target susceptibility, wrapper effects, and incomplete null controls | finish the registered bootstrap and run a newly frozen matched-control, signed-null, wrapper-holdout, cross-model response design |
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
- T11 system, view, context, endpoint, depth, metric, and model choices remain
  fixed; discovery outcomes cannot repair them. T12 opened only its frozen ZWJ
  and regional subsets once, and its negative decision cannot be rescued by an
  alternate endpoint, threshold, model subset, or post-hoc family.
- T13-EA remains point-estimate exploratory evidence. Its registered
  20,000-replicate cluster bootstrap must complete before interval-based paper
  wording, and no cell may be promoted into a confirmatory verdict.
- E1 intervals remain descriptive; no p-value, multiplicity decision,
  confirmatory status, or layer-comparison inference will be retrofitted.
- T2's two midpoint p-values and Holm family remain the only authorized
  decisions for that protocol. The eight non-primary rows remain descriptive,
  including Gemma rows at the exhaustive `1/120` floor.
- T3's two all-depth p-values and Holm family remain its only authorized
  decisions. All ten per-depth p-values are secondary, with no multiplicity
  decision and no authority to replace the primary endpoint.
- T4's two all-context, all-depth p-values and Holm family remain its only
  authorized decisions. Context-specific and all 20 context-by-depth values are
  secondary, and T3 is a descriptive reference without inferential pooling.
- T5's three model-level IUT p-values and their Holm family remain its only
  authorized decisions. The distance-1 and attenuation component p-values are
  constituent gates; all carrier-, distance-, depth-, tail-, and T4-comparison
  values are secondary and cannot replace the conjunction.
- T10's sole cross-model decision combines the four-core partial conjunction
  with the `3/4` practical count. The nine model IUTs and Holm family authorize
  only bounded cell statements; extension cells, the raw-block endpoint, Qwen
  ladder, and related Mistral-Instruct comparison cannot rescue the primary.

## Remaining paper gates

- prepare a new versioned causal bank outside the C1 v1 exposure context, then
  freeze the complete targeted layer-2 causal protocol before opening it; no
  additional bank is required merely to begin protocol design;
- address v1 role binding and prototype-resampling dependence prospectively in
  final-paper confirmatory wording and supporting replication;
- complete at least one prespecified targeted causal experiment, positive or negative, without opening the replacement bank early;
- complete the T13-EA 20,000-replicate cluster bootstrap and retain its
  no-primary, no-confirmatory status;
- freeze exact token/prefix controls, leave-one-wrapper-out directions, signed
  manifold/covariance-matched nulls, the depth-0.875-versus-1.0 contrast, the
  six-model response replication, and generation endpoints before using them
  to strengthen the T13-EA story;
- complete an independent backend implementation check and at least one model or tokenizer replication appropriate to the final claim;
- archive the complete raw evidence and checksum it;
- generate paper tables and figures from versioned scripts;
- run a fresh-eyes reproducibility and claim-boundary review;
- keep the English manuscript and Japanese public summary propositionally aligned.
- preserve the T3 tokenizer-conditioned interpretation; do not relabel its
  secondary depth profile as confirmation or use it to rescue either cell.
- preserve the T4 carryover boundary; do not treat its two suffix contexts as
  independent replications.
- preserve the completed T5 boundary: do not infer duration, monotonic decay,
  disappearance, or a selected distance/depth effect from its failed primary
  attenuation conjunction or its secondary profiles.
- preserve the completed T10 boundary: do not lower the practical floor,
  replace a core cell, promote an extension cell, or relabel the Qwen and
  Mistral secondary profiles as scale, tuning, or independent replication.
- preserve T11 as exploratory and model-conditioned; do not select only
  favorable cells or relabel exact-length matching as tokenizer independence.
- preserve T12 as a completed one-shot negative confirmation; do not lower its
  practical floors, replace its model roster, promote the regional component
  `p = 0.03538` alone, or add an endpoint rescue.

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
- the complete T2 Gemma and OLMo activation arrays, observations, receipts,
  ten-row joint analysis, transfer verification, and public manifest;
- the complete T3 Gemma and OLMo activation arrays, observations, receipts,
  ten-row repaired joint analysis, three-node transfer verification, and public
  manifest;
- the complete T4 Gemma and OLMo activation arrays, observations, receipts,
  20-row joint analysis, three-point transfer verification, and public
  manifest;
- the complete T5 Gemma, Llama, and OLMo activation arrays, observations,
  receipts, 120-row joint analysis, verified transfer receipt, and public
  manifest;
- the T11 frozen inputs, nine validated acquisition summaries, joint analysis,
  independent item-margin/agreement/depth recomputation, compact public bundle,
  and an external checksum-bound archive for omitted dense arrays;
- the T12 freeze, nine run/shard receipts, 432 item-contrast rows, joint primary
  result, independent randomization/gate recomputation, and compact public
  bundle with omitted raw activations bound by checksum;
- artifact-audit receipt;
- versioned analysis and figure-generation scripts;
- English manuscript, supplementary material, and Japanese public summary.

The current compact repository omits the approximately 74 MiB (77.3 MB) raw
baseline intervention ledger and its model-dependent NPZ arrays. The compact
T5 activation arrays are included in its public evidence bundle. The remaining
omission is acceptable for code review, but not sufficient as the final
archival evidence package.
