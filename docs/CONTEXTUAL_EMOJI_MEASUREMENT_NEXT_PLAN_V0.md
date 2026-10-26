# Next study: validate the output measurement, then test its route

[日本語](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.ja.md) · [Research note](CONTEXTUAL_EMOJI_MEASUREMENT_RESEARCH_NOTE_V0.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

**Author-pilot preparation update (2026-10-10):** the [24-item protocol](CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.md) and local-archive handoff `CONTEXTUAL_EMOJI_AUTHOR_PILOT_HANDOFF_V0.md` now resolve the first author-assessment step described below. The handoff check recorded zero real responses. Independent validation and the later research branches remain open; this update adds no scientific result.

Created 2026-10-07; execution status updated 2026-10-10. **Design options, not a registration or execution order.** This document records a sequence and decision branches after the candidate-wording results. The authorized eight-input numerical diagnostic and the subsequent matched-shape reassessment of all 1,248 existing sequence scores are now complete (Section 2). These are the same 24 authored development scenarios and six families, with no increase in scientific N. Human annotation recruitment, new-family acquisition, causal acquisition, and external submission remain unlaunched. The next step is to resolve the open human-validation choices in Section 3.

## 1. The one question to advance

Does a human-validated goal–cue relation produce a reproducible output interaction across a fixed response panel and genuinely new scenario families?

Track absolute candidate preference and its wording stability as distinct outcomes. The eventual causal question is whether a specified internal route contributes to that validated output effect in the model's ordinary state. Emoji-specific effects require an explicit comparison with other carriers under comparable conditions.

For now, keep the current interpretation: goal compatibility with a status cue. A change of emoji sense is a separate task that requires independently established interpretations. Increasing model size or the number of paraphrases does not resolve that distinction.

## 2. Numerical-consistency gate: a bounded prerequisite

The 2026-10-07 CPU audit of the historical scoring version found nonzero common-prefix log-score residuals in 355/576 candidate comparisons. All 355 occur among 520 unequal-length pairs; the 56 equal-length pairs have zero residual. Shape-dependent arithmetic is plausible, but neither BF16 nor the masking/runtime path has been isolated as the cause. The original fully resident scores already contain the issue; exact staged replay does not test it away.

Removing the prefix contribution descriptively changes 1/576 absolute preferences, 2/144 crossover decisions, and 1/144 all-four-alignment decisions, while preserving all 144 H signs. Tail-only scoring does not repair potential numerical differences in the remaining tokens.

### Historical diagnostic panel: executed 2026-10-07

The following retains the panel design and decision rules used before execution.

Before execution, list and hash eight existing paired inputs:

- One paired input from each of the three decision-changing block cases, selected by a recorded engineering rule.
- The maximum-prefix-residual input.
- Four equal/unequal-length controls selected by a recorded engineering rule, without searching for favorable scientific outcomes.

The three decision-changing **block cases** are original emoji `affect_01`, explicit-negation emoji `affect_03`, and adjective emoji `thermal_04`. Deduplicate input identities and use a prespecified equal/unequal-length control ordering to fill any overlap, retaining eight distinct inputs. Full replay of these three blocks needs 12 paired inputs, or 84 forwards under the seven-call schedule below, before separate maximum-residual/control inputs. The eight-input screen diagnoses shared-prefix arithmetic only. If decisions themselves are to be re-evaluated, explicitly expand and budget the full blocks before execution. Do not infer a repaired block from one repaired input.

For each of eight selected inputs:

1. Repeat each original BF16 candidate execution twice: four forwards.
2. Score both candidates at a common padded tensor length, using explicit padding masks and identical prefix positions: two forwards.
3. Score the shared candidate prefix once under its own causal history: one forward.

This screen costs **56 forwards**, excluding setup checks. Require exact reproducibility of identical executions and exact same-shape shared-prefix agreement. Specify any cross-shape/FP32 tolerance and the maximum acceptable effect on endpoint decisions before executing; do not enlarge tolerances after a failure. The separately scored prefix may have another shape, so preserve and examine its discrepancy rather than silently treating it as an exact oracle.

If the issue remains, inspect the actual pinned model's causal-mask implementation and consider a small FP32 repeat, subject to memory and workload permission. Changes to runtime, precision, padding, masks, position IDs, or scoring/execution geometry create a new scoring version. Preserve old receipts and reassess the complete affected grid before making new paper-level numerical claims. Failure closes the route to causal acquisition until the scoring issue is understood sufficiently for the intended effect scale.

**2026-10-07 execution update:** the [fixed eight-input diagnostic](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_RESULTS_V0.md) completed 56/56 forwards and passed independent validation. Historical and repeated scores agreed exactly; matched-shape shared prefixes agreed on all eight pairs. Full candidate-score differences moved by up to 0.2103 nats without preference flips on this selected panel. The [CPU preflight revision](CONTEXTUAL_EMOJI_PREFIX_PREFLIGHT_ADDENDUM_V0.md) preserves the zero-forward initial refusal separately. At that point, only the small-panel check was closed; the full-grid reassessment and human/scenario/causal gates remained open.

### Full-grid execution update: completed 2026-10-10

The [matched-shape scoring reassessment](CONTEXTUAL_EMOJI_MATCHED_SHAPE_RESULTS_V1.md) completed **1,312/1,312 forwards: 1,248 existing scientific sequence scores plus 64 engineering sentinel repeats**. Independent validation passed the runtime, installed implementation, replay, resource, and numerical gates. All **624/624 candidate-input pairs** have exactly matching shared-prefix probabilities and predictor-logit hashes; the 16 scientific calls overlapping the sentinel inputs also reproduce their prior padded scores exactly. The 96 original absent-cue scores are retained once as a shared baseline. The 192 absent-cue scores missing for the new wordings were not added.

Compared with the historical scoring version, candidate preference changed in **4/576 cue-bearing inputs** and H sign in **5/144 block tables**. The old tail-only calculation above is a separate diagnostic, not this full-candidate reassessment. Under the new scoring version, H is positive across all three candidate pairs in **22/24 emoji scenarios and 23/24 word scenarios**, while all-four-input alignment across all three pairs remains **0/24 for both carriers**. The completed gate supports using the versioned scores for this development analysis. It neither establishes a numerical ground truth across precisions nor validates human interpretation, candidate equivalence, generalization, or a causal route.

## 3. Validate the task before enlarging the model study

**Current next step (2026-10-10):** resolve the `OPEN` choices in the [human-validation draft](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.md), then fix the instructions, allocation, and eligibility rules before recruitment or rating collection. The draft is preparation material; no human judgments have been acquired or inferred from the completed model run.

The author subsequently volunteered as the first assessor, with the assistant preparing materials that conceal scores, labels, and original identifiers. This first stage is an **author development pilot**, with prior research exposure retained in the record. It does not substitute for independent human validation. Pilot coverage, rating instruments, and response-finalization rules must be fixed before item delivery; no ratings have begun.

Write annotation instructions and eligibility rules before collecting ratings. Independent raters should be blind to model scores, intervention outcomes, and intended labels. Separately collect:

- Which continuation follows from the goal and message, with **both / neither / ambiguous / unclear** available.
- Naturalness and comprehensibility of the prompt and each continuation.
- Whether the different candidate pairs express the same intended alternatives.
- Whether word and emoji cues provide comparable information for this task.

Counterbalance candidate display order and record rater IDs, raw judgments, disagreement, abstentions, and planned/annotated/eligible counts. Set adjudication rules and agreement/eligibility thresholds before ratings; these are still open design choices, not numbers to infer from model success. LLM drafting or review is not a substitute for independent human labels.

Retrospective ratings can validate or reject the development materials. They cannot make the already-exposed 24 scenarios confirmatory. If meanings or candidate equivalence fail, revise development materials while preserving the original study as a measurement-sensitivity result.

## 4. Separate the candidate controls

Use development data to decide a small fixed panel, then stop adapting it to model outcomes. Possible axes are affirmative alternatives, explicit negation, and morphological negation. Match syntax/length where natural language permits, with independent equivalence judgments.

Keep three questions separate:

1. Do the cues have comparable meaning/function?
2. Do the candidate formulations preserve the task alternatives?
3. Do token counts, cue spans, and continuation-predictor positions match for the specific tokenizer?

Equal token counts do not establish the first two. Avoid filler padding added solely to make the counts agree. Apply token/position eligibility before scoring outcomes, retain unmatched denominators and exclusions, and report the full intended population alongside the eligible subset. A counterbalanced response-label format is a possible separate diagnostic; it changes the output task and cannot silently replace natural-continuation scoring.

The **192 missing absent-cue scores** for the new pairs are optional. They extend cue-relative diagnostics but leave H unchanged under context-specific subtraction. The empty-message baseline also changes geometry. A semantically neutral, natural baseline would require separate validation and a distinct estimand; do not pool it with deletion.

## 5. New families for an independent behavioral test

Have an independent custodian prepare a new versioned bank outside the exposed research context. Do not reopen the protected historical banks. New families must differ beyond names or paraphrases of the same six templates. Track semantic domain, cue pair, template family, scenario, and response pair; reused glyphs limit any claim to the tested inventory unless their dependence is handled explicitly.

Before model scoring, specify:

- The validated candidate panel and its weights; no post-hoc best-pair selection.
- The primary interaction estimand, practical effect floor, direction, and population.
- Separate secondary preference/crossover/minimum-margin outcomes and their multiplicity treatment.
- Numerical consistency, human validity, token/position eligibility, missingness, and stopping rules.
- Family/cue clustering and an inference or precision procedure justified for the actual allocation.
- Which choices were made from development results and which data remained untouched.

The current equal-three-pair average is descriptive. It is not automatically the next primary endpoint. Choose the next endpoint to match the validated task, and specify how consistent formulation effects must be before interpreting an average.

No sample size is fixed here. Use desired precision/practical effect and family/cue dependence to determine the allocation. More responses within one template cannot substitute for independent families. If an independent bank cannot be arranged, report the next results as development rather than inventing freshness.

## 6. Natural-state causal study, after the preceding gates

Retain the detailed [natural-state transfer plan](CONTEXTUAL_EMOJI_CAUSAL_TRANSFER_PLAN_V0.md). The new entry conditions are computational consistency and a validated, stable candidate panel. Before launch, complete its remaining site, eligibility, and allocation choices; the current document does not authorize an automatic experiment.

The plan exchanges cue-position post-RoPE K/V messages in both directions, with all intended subsequent queries specified, including continuation tokens. It keeps the recipient's ordinary state, avoids an answer-derived donor, and measures the output endpoint established above. Use the same procedure for words.

Require informative broad-route calibration, same-state/no-op replay, positional controls, and both unadjusted directional effects in addition to contrasts against controls. A positive difference between two negative effects does not constitute successful transfer. A broad intervention is a calibration condition, not an assumed upper bound; dividing by unstable H is not a primary test.

Even a successful cue-route exchange is compatible with fixed cue information interacting with context-sensitive queries. Distinguishing context-conditioned information at cue positions from later use of a stable cue requires its own intervention. Keep that rival explanation visible rather than redefining a route effect as emoji sense change.

## 7. Transparent provisional budgets

Let N be scenarios and J candidate pairs. Each scenario has two contexts. There are four cue-bearing variants (two emoji, two word) plus one shared absent condition; each input has two scored candidates.

| Allocation | Count | Example N = 24, J = 3 |
| --- | ---: | ---: |
| Clean emoji + word + shared absent scores | 20NJ | 1,440 |
| Three-rater input-pair judgments | 30NJ | 2,160 |
| One intervention regime, two carriers and both directions | 16NJ | 1,152 |
| Four regimes: route, position, calibration, same-state | 64NJ | 4,608 |
| Clean scores plus four regimes | 84NJ | 6,048 |

Annotation counts exclude separate naturalness/equivalence items. Intervention counts exclude donor-cache construction, implementation checks, failed/retried forwards, and additional control variants. These are accounting examples, **not sample-size recommendations, power calculations, timing forecasts, or permission to consume a GPU**. Numerical-consistency diagnostics have their own engineering denominator.

During occupancy, continue CPU analysis, annotation preparation, and paper work. Any later shared-GPU proposal needs a fresh resource check and bounded memory/impact conditions. The previous brief Aether overlap does not establish safe sustained co-execution.

## 8. Outcomes worth publishing

| Next result | Defensible conclusion and next action |
| --- | --- |
| Numerical consistency unresolved | Publish/retain the audit and sensitivity; defer stronger model claims and interventions |
| Human interpretations or candidate equivalence fail | Development measurement study; repair materials without consuming confirmation |
| New-family interaction fails or depends strongly on wording | Bounded negative generalization/sensitivity result; stop favorable-wording search |
| Interaction repeats but choices remain unstable | Contextual modulation of scores; keep reliable interpretation selection open |
| Emoji and words show comparable behavior | Comparable contextual cue effects; shared computation remains a hypothesis, with no demonstrated emoji-specific advantage |
| Behavioral effect holds but causal calibration fails | Tested intervention is uncalibratable; no conclusion that mechanisms are absent |
| Calibration works and the selected route fails | Bounded route-negative result; new-site exploration gets a new label and allocation |
| Route passes on independent material | Specified output-linked contribution; next allocate a separate second-model replication |

Three coherent paper forms follow: a **measurement-separation study**, a **shared contextual-cue mechanism study**, or a **bounded negative causal study with positive behavioral interaction**. Their value comes from discriminating explanations, not from securing a positive emoji-specific effect.

## 9. Deliverables and decision log

Completed through 2026-10-10: paired research notes, hash-bound CPU decomposition, replayable numerical analyses, the eight-input diagnostic, the full 1,248-score matched-shape reassessment with independent validation, and this updated options document. The submitted/post-review PDF remains unchanged.

The full-grid scope and sentinel-repeat schedule have been resolved and executed; no cross-shape accuracy tolerance was inferred. Next choices needing explicit resolution: human recruitment, rater allocation, agreement/eligibility and adjudication rules in the [human-validation draft](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.md); the validated candidate panel; an independent bank custodian; practical floor and family-level sample allocation; causal site/control details. The order remains **human validation → new-family behavioral test → natural-state causal study**, with each later step conditional on its preceding gates. No human, new-family, or causal acquisition has begun. Remaining choices are open research decisions, not missing results to fill with inferred consent.

A later manuscript integration should update the ordinary-output status, retain the exploratory label, add the response-sensitivity limitation, and preserve the original negative causal results. Public release remains a separate step after the user decides the evidence is ready. No DOI service or submission is selected by this plan.
