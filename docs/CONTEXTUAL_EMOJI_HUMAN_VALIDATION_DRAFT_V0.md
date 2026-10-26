# Draft: human validation of contextual cues and response alternatives

[日本語](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.ja.md) · [Research sequence](CONTEXTUAL_EMOJI_MEASUREMENT_NEXT_PLAN_V0.md) · [Scoring reassessment](CONTEXTUAL_EMOJI_MATCHED_SHAPE_V1.md)

**Public-integration note, October 26, 2026:** this dated note retains the original
study status. References to excluded handoffs, notebooks, specifications or
runtime records concern the author's local archive; the public checkout does
not supply a complete historical run. See the
[public integration scope](PUBLIC_INTEGRATION_SCOPE_20261026.md).

**Later preparation update (2026-10-10):** the [24-item author-pilot protocol](CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.md) resolves the first-stage instrument and allocation. The local-archive handoff record, `CONTEXTUAL_EMOJI_AUTHOR_PILOT_HANDOFF_V0.md`, documents a prepared local package/interface and its zero-response check. The text below retains the earlier design-stage status; independent-rater and comparison-panel choices remain open.

2026-10-10 (JST). **Design outline; not registered or launched.** The initial outline preceded inspection of the matched-shape run's outcomes. After those outcomes were discussed, the author volunteered to perform the first assessment, with the assistant preparing concealed materials. This role decision is recorded below; no judgments have been collected and no stimuli exported. The choices marked **OPEN** require resolution before data collection.

## 1. The question and the two populations

Do independent readers interpret the goal and cue as the authored task assumes, and do the candidate formulations express comparable response alternatives?

- **Retrospective development validation:** assess the existing 24 scenarios in six families. Model outcomes have already been inspected. Human judgments may support or reject the materials; they cannot make this population confirmatory.
- **Later independent-family study:** an independent custodian would prepare a new versioned bank outside the exposed research context, using the adopted human-validation rules. New names or paraphrases of the existing six templates do not create independent families. The protected historical banks remain closed.

Model probabilities, author-defined orientation, and human judgments are separate records. AI drafting or critique cannot supply independent human labels. A computational consistency pass does not validate meaning or candidate equivalence.

### First stage: author assessment with concealed scores and labels

The initial planned assessor is **one research author**, who has already seen the research discussion and aggregate model outcomes. The assistant prepares the presentation and retains the correspondence key; the author supplies the judgments. Call this an **author development pilot with score/label concealment**, not independent human validation or a fully blinded study. No independent third-party rater is yet arranged. One author's responses cannot estimate inter-rater agreement or close the independent-validation gate.

For this pilot, adopt the following preparation constraints before showing any items:

- Show only neutral display IDs, the task text, response alternatives, and rating controls. Withhold model scores and ranks, intended labels, original experiment/item IDs, selection reasons, and the mapping from displayed alternatives to their original identities. The actual emoji/word text remains visible; cue type, repeated materials, and the author's prior knowledge cannot be concealed or undone.
- Fix the item inventory, presentation order, and counterbalanced response order before collecting judgments, without selecting or arranging items by model success. Version and hash three separate objects before the first rating: participant materials, the original answer/orientation key, and the assignment/order key. Keep the seed and keys out of participant materials; preserve the original labels even if subsequent judgments disagree. Actual coverage, allocation, and repetitions remain **OPEN**.
- Do not ship a concealed answer key inside HTML, JavaScript, hidden fields, downloadable metadata, or an accompanying participant file. The participant export must use an allowlist and be checked for leakage before delivery. This prevents accidental exposure; it is not a security guarantee against the owner inspecting their own research files.
- Collect interpretation judgments first. Show no item-level correctness, model agreement, hints, or interim result summaries before that phase's responses are finalized. Lock the responses before revealing equivalence/carrier comparison panels or conducting any answer comparison. Later corrections or adjudication remain separate records, with reasons.
- Record prior involvement, remembered items, repeated exposure, uncertainty, abstention, and incomplete responses. Keep ambiguous or contrary judgments. Repeated variants seen by one author are not independent ratings. Panel ordering reduces additional exposure; it does not erase carryover or make later comparisons independent.

This stage can identify confusing instructions, ambiguity, or candidate differences and guide material revision. It does not provide population-level human accuracy or independent confirmation of a favorable model result. Subsequent independent assessment remains a separate design and recruitment decision.

## 2. Separate judgment tasks and their blinding

| Task | Information shown | Judgment requested |
| --- | --- | --- |
| Interpretation and choice | One goal/message with one response pair, with response order counterbalanced | Which response follows? First / second / both / neither / ambiguous / unclear; optional explanation |
| Naturalness | The same prompt and each response separately identifiable | Comprehensibility and naturalness of the prompt and of each continuation, without equating fluency with correctness |
| Formulation equivalence | A separate comparison panel with the contextual material needed to compare response pairs | Whether the alternatives preserve the same distinction; any difference in meaning, scope, negation, or appropriateness; uncertain is allowed |
| Carrier information | A separate panel comparing the relevant emoji and word messages in context | Whether they provide comparable task-relevant information, and what is gained, lost, or uncertain |

Interpretation raters must not see model scores, intervention outcomes, author-intended answers, experiment IDs, or a side-by-side display of all response formulations that reveals the intended mapping. Use neutral display IDs and retain the response-order key separately.

Equivalence and carrier panels necessarily reveal comparisons hidden from the interpretation task. Keep their assignments or collection sessions separate; do not present their judgments as fully blind single-input interpretation. Whether the panels use different people, or an explicitly ordered design that prevents prior comparison exposure, is **OPEN**. Track prior exposure rather than assuming blinding survived.

The distinction between “ambiguous” (multiple plausible readings) and “unclear” (unable to understand or judge) needs plain-language instructions. Naturalness scales, equivalence response options, instructions, and illustrative practice items are **OPEN**. Do not train raters toward author-preferred answers.

## 3. Sequence before collection

1. Decide the population and view coverage, including how absent-cue materials enter. Inventory planned units by scenario, family, carrier, context, cue, and formulation. Missing model scores are not human judgments and are not imputed.
2. Set eligibility, assignment, counterbalancing, blinding, raw-record fields, missingness treatment, and the analysis/adjudication rules below. Save a dated version before collecting ratings.
3. Check that instructions and interface are understandable. Decide **before** any such check whether it is a development pilot and whether its participants/items can enter the later assessment. Preserve resulting revisions and exposure history.
4. For the author pilot, collect self-evaluation responses under the concealment constraints above. For the later independent-rater track, collect independent judgments without sharing earlier raters' answers. In both tracks, retain refusals, incomplete responses, and deviations from the intended assignment; do not pool the tracks as independent raters.
5. Summarize response distributions and disagreement under the specified rules. Any later adjudication is a separate record with reasons, not a replacement for raw judgments.
6. Decide which development claims and materials remain defensible. Revisions receive new versions. Choose the later candidate panel and independent-family design before new model outcomes, retaining the development decisions that informed them.

## 4. Decisions still OPEN

| Decision | What must be settled |
| --- | --- |
| Raters and independence | First pilot: one volunteered author, explicitly non-independent. Later independent raters: number, recruitment route, prior involvement/exposure, and independence criteria remain OPEN |
| Language competence | Relevant English comprehension criteria, emoji familiarity, and how eligibility is established without selecting for desired answers |
| Coverage and allocation | Which views/pairs are judged, ratings per unit, family/carrier balance, repeated-item exposure, and response-order counterbalancing |
| Logistics | Compensation, participation information, privacy/data retention, and a practical way to decline or withdraw |
| Instruments | Exact instructions, response options/scales, practice materials, and the distinct equivalence/carrier panels |
| Analysis | Agreement/disagreement summaries, eligibility thresholds if any, incomplete/ambiguous responses, adjudication, and any uncertainty or multiplicity treatment |
| Next population | Independent custodian, genuinely new families, practical effect target, and eventual sample allocation |

Only the first pilot's assessor role and count are established. Independent-rater count, agreement thresholds, exclusion rules, compensation commitments, and approval/compliance claims remain unresolved. Resolve the choices before observing the judgments used to evaluate them; do not tune cutoffs to preserve a favorable model result.

## 5. Records, denominators, and outcomes

Use pseudonymous rater IDs and versioned item/instruction IDs. Retain task type, assignment, shown response order, raw response, optional explanation, missingness/abstention, relevant exposure, and any later adjudication. Keep any identifying contact information separate from analysis artifacts.

Report **planned → assigned → completed → eligible** counts, with reasons for differences, both overall and by task/population. Retain the full intended denominator alongside any rule-defined subset. Multiple judgments or formulations of one scenario do not increase the number of independent scenarios. No majority-only deletion of disagreement is implied.

- Interpretations and formulations supported: proceed to a separately specified independent-family test; retrospective ratings remain retrospective.
- Persistent ambiguity, unnatural candidates, or inequivalent formulations: retain a measurement-sensitivity result, revise development materials, and evaluate the revision explicitly.
- Mixed judgments: report the uncertainty and competing readings; do not translate unresolved cases into “human accuracy” or a causal endpoint.

The author has volunteered for the concealed-material pilot; no item delivery or rating collection has begun. External recruitment/messages, annotation services, new bank acquisition, model execution, manuscript claim changes, and public release remain outside this preparation step. The next deliverable is a resolved, versioned pilot protocol and a blank recording schema after the remaining choices are settled.
