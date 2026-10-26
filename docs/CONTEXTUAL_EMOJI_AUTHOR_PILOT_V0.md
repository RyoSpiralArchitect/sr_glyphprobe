# Protocol: author self-evaluation pilot v0

[日本語](CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.ja.md) · [Human-validation outline](CONTEXTUAL_EMOJI_HUMAN_VALIDATION_DRAFT_V0.md)

2026-10-10 (JST). **Status: protocol prepared only.** The author has volunteered as the sole initial rater. This document does not attest that an assessment package or interface has been handed off, that concealment has been verified, or that any human response has been collected. The default scope is 24 interpretation items; a different size requires a revised, frozen protocol before the first response. No actual stimuli or answer mappings are included here.

## 1. Purpose and claim boundary

This is a voluntary, local **author self-evaluation development pilot**, not independent human validation, a confirmatory test, or an estimate of population performance. The existing 24 authored scenarios and aggregate model outcomes have previously been discussed. Concealing labels and scores during this pilot cannot remove that history. Record authorship, prior involvement, prior outcome exposure, and item recognition rather than describing the author as blind or independent.

The pilot asks whether the author, when judging an individual displayed item without an answer key or score feedback, finds the intended response distinction interpretable and the language usable. It can expose ambiguity, wording problems, and procedural defects. It cannot establish independent semantic validity, inter-rater agreement, carrier equivalence, causality, or generalization to new families. Authored labels are expectations to compare later, not independent human ground truth.

Only the initial single-item interpretation phase is in scope. Formulation-equivalence and emoji/word comparison panels are deferred and must not be exported or displayed during this phase. Independent raters and a genuinely new independently prepared family bank remain OPEN. Historical protected banks remain closed.

## 2. Frozen inventory and allocation

Use only the existing development-scenario and candidate-panel inputs. Before collection, the package manifest must pin their exact paths, versions, and SHA-256 hashes. Model-score artifacts are not selection inputs. Do not create new scenarios, paraphrase the English stimulus text, select favorable cases, or replace a case because its expected/model outcome is inconvenient.

The default inventory is the existing 24 unique scenarios: six families with four scenarios each. Select one of the existing context p/q × cue a/b views for each scenario so that the four combinations occur exactly once within each family. Each scenario appears once, with one carrier and one candidate formulation. There are no absent-cue items in v0; no conclusion about absent cues follows from this pilot.

Freeze one constrained-random assignment before the first response:

| Margin | Required count |
| --- | --- |
| Unique scenarios | 24; four context × cue cells per family |
| Carrier | 12 emoji and 12 word |
| Candidate formulation | Eight items for each of the three existing response-pair formulations |
| Carrier × formulation | Four items in each of the six cells |
| Response display order | 12 canonical-order and 12 reversed-order items |

Randomize presentation order and assignments within these constraints with a recorded seed and algorithm version. Use source inventory and prespecified margins, not authored answer labels or model outcomes, to select the schedule; retain the first feasible schedule under the frozen algorithm. Record the remaining family/context/cue cross-tabulations without claiming that all higher-order interactions are balanced. If the inventory or allocation cannot satisfy the requirements, stop before collection and revise the protocol explicitly; do not silently drop, duplicate, or substitute items. “Outcome-independent allocation” refers only to this scheduling procedure, not to the exposed development materials or the author's knowledge.

The English goal/message and response text must remain exactly as supplied by the pinned sources. An English/Japanese toggle may change instructions and interface labels only, never translate or alter the stimulus text. Preserve the participant-payload hash binding those exact item texts and the instruction language attached to each saved action. Unsaved language switches are not recorded; this is not a complete display-language history.

## 3. Concealment and pre-response freeze

Freeze three objects and record their hashes before accepting the first human response:

1. **Participant payload:** opaque display IDs, exact stimulus text, displayed response texts, and the permitted participant controls/instructions only.
2. **Authored-label key:** the unchanged source-defined expectations/orientations and their source correspondence. Do not revise labels in response to the pilot.
3. **Assignment/order key:** the correspondence between opaque IDs and source scenarios, families, context/cue/carrier/formulation, presentation order, and response-order mapping, including the randomization receipt.

The two keys and model results must remain outside the HTTP-served allowlist and outside the participant payload, client state, URLs, downloadable participant exports, and participant-visible logs or metadata. Before handoff, verify the actual served files/endpoints and responses; a protocol statement alone is not evidence of concealment. A participant-facing “no answers shown” claim requires that check. Record package/instruction versions and the three hashes in a separate manifest without publishing the secret mappings to the participant view.

This is procedural score/label concealment, not protection against the repository owner deliberately opening local keys. The author should not inspect keys, model results, prior result discussions, or comparison panels from the start of the rating session until the whole interpretation batch is finalized. Emoji versus word, actual wording, familiar scenarios, and remembered expectations cannot be hidden. Do not describe those visible features as blinded.

## 4. Participant instructions

Read the displayed goal/message and both responses. Judge only what that displayed material supports, without trying to recover an author's intended answer or predict a model. A response can be fluent without following the message. There is no requirement to choose one response, and uncertainty is a valid judgment.

Choose one interpretation response:

| Choice | Meaning |
| --- | --- |
| First | The first response follows the displayed goal/message and the second does not. |
| Second | The second response follows the displayed goal/message and the first does not. |
| Both | Both responses are acceptable under the same reading of the displayed material. |
| Neither | The material is sufficiently understandable to judge, but neither response is acceptable under that reading. |
| Ambiguous | More than one reasonable reading of the material leads to different judgments about which response is acceptable. |
| Unclear | You cannot understand the material or decide how to judge it well enough to give one of the preceding answers. |
| Abstain | You prefer not to provide an interpretation judgment for this item. No reason is required. |

If more than one reading changes your choice, use Ambiguous rather than Both; Both is for accepting both under the same reading. If you can understand the message and reject both responses, use Neither rather than Unclear. These are response definitions, not instructions to resolve a particular item toward an expected answer. An optional note may explain your reading, uncertainty, wording concern, or other observation; it is never required.

For each item, recognition may also be recorded as **yes / no / uncertain**, meaning whether you remember this scenario or its response alternatives from prior work. Do not look anything up to answer. A primary interpretation response can be saved without a recognition answer; retain that field as missing, not “no” or “uncertain.” Recognition is remembered-exposure self-report, not proof of actual item viewing. At the session level, self-report English comprehension confidence as **comfortable / sometimes difficult / difficult / prefer not to say** (`comfortable`, `sometimes_difficult`, `difficult`, `prefer_not_to_say`). This is descriptive exposure/context information, not an eligibility cutoff or a reason to discard an inconvenient response.

After the interpretation choice, optional separate naturalness judgments may be entered for the prompt, first response, and second response: **good** (understandable, no noticeable wording problem), **awkward** (understandable but unnatural or clumsy wording), or **unclear** (not understandable enough to assess). These judgments concern language, not whether a response follows the goal. Leaving them blank records missing optional data and does not invalidate the interpretation choice.

No scored examples or answer-directed practice items are part of v0. Interface-only demonstrations, if needed, must not expose development stimuli or expected answers and must be logged as an instruction revision before collection.

## 5. Session, edits, and finalization

Permit pause/resume and voluntary discontinuation. Keep the frozen assignment on resume; do not rerandomize based on completed answers. Before finalization, the author may revisit and change ratings. Retain the original value, each changed value, and edit time in an append-only event journal, with an optional reason; do not silently overwrite history. Record batch start and saved actions, not item-display telemetry. Actual item presentations and revisits are **UNMEASURED**: a batch start or saved response does not establish when, how often, or whether every item was viewed. Preserve remembered exposure through recognition self-report without upgrading it to observed viewing history.

Finalization applies to the **whole 24-item interpretation batch**, not to individual items. Show the number answered, abstained, and missing before a deliberate finalization action. Permit finalization with explicit missing entries; do not force guesses or replace blanks with abstentions. Freeze the finalized snapshot and journal hash. Later corrections must be separate dated amendments/adjudications, never replacements for raw or finalized records.

Provide no per-item correctness, labels, scores, running agreement, or model-outcome feedback before finalization. Finalization must not automatically reveal answers or results either. Any later result comparison or label reveal requires a separate explicit request and must be recorded as an exposure event. Ratings collected after such exposure are not feedback-naive. A future comparison panel cannot retroactively make these ratings independent.

## 6. Records, privacy, and reporting

Use one pseudonymous rater ID with role `author`. Preserve protocol/instruction/item/source/assignment versions, the three object hashes, batch-start and saved-action/edit history, instruction language at each saved action, raw interpretation choice, optional note, recognition, English-confidence self-report, optional naturalness fields, missingness, session status, finalization status, and any subsequent reported exposure/amendment. Pin the protocol and served interface/instruction assets before the first response and bind the journal to those versions; do not silently resume existing ratings under changed instructions. Actual item views/revisits and unsaved language switches remain UNMEASURED. Keep the raw judgment separate from any later authored-label comparison or adjudication.

Operate locally, bind any assessment server to loopback only, and use no analytics or external rating service. Store human responses and journals outside Git-tracked/public artifact paths; do not commit, upload, or publicly release them. Do not collect contact details or other unnecessary identifying data. Before handoff, identify the local response location and explain how to pause, stop, and request deletion. No external recruitment, compensation arrangement, ethics approval, or compliance determination is asserted by this protocol.

Report planned → assigned → completed → eligible counts with definitions and reasons. Planned is 24 under this version; assigned is the frozen activated schedule; completed is an item with a recorded interpretation choice, including explicit Abstain; eligible for descriptive interpretation-category counts is a completed non-Abstain response. Show all seven response categories and missing entries against the full planned denominator as well. Recognition/English confidence and missing optional naturalness do not exclude items. A stopped or partly completed pilot remains a partial pilot.

Report raw author-response counts/distributions and item-level concerns; retain both uncertainty categories, abstentions, missingness, and disagreements with authored expectations. Do not calculate inter-rater reliability with one rater, call repeated formulations independent scenarios, infer population accuracy, or set label-agreement thresholds after seeing ratings. The 24 scenarios are nested in six authored families, not 24 independent families. Any future thresholds, revised materials, expanded allocation, independent-rater study, or independent-family study require a separately versioned plan.

## 7. Handoff gate

Before the first human response, verify and record: source inventory/pins; exact allocation margins and randomization receipt; unchanged English text; the three frozen object hashes; permitted served payload and inaccessible keys/results; no feedback or automatic answer reveal; pause/resume, edit journal, explicit missing-data finalization, and local response storage. No placeholder hash or unverified interface assertion passes this gate. Until the actual package/interface handoff and these checks are recorded, this document remains **prepared protocol only**, not a launched or validated pilot.
