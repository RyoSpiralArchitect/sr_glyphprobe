# From lexical retrieval to contextual interpretation: a working reassessment

[日本語](CONTEXTUAL_EMOJI_REASSESSMENT_20261010.ja.md) · [Working paper](../paper/README.md) · [Claim boundary](../paper/WORKING_CLAIMS_20261010.md)

October 10, 2026. **Unfinished research synthesis; local draft only.**
This note consolidates completed measurements and the author tryout before
choosing the next research question. It launches no experiment and changes no
past response, protocol, or confirmatory decision. No external release or push
is included. Individual author-response records remain private.

## 1. Where the study stands

Our original question concerns the role of emoji information inside a language
model and its influence on responses. We now have evidence at three different
levels, with different strengths:

1. **Lexical information is readable.** The historical cross-model retrieval
   study establishes an item-wise relation to word-disjoint CLDR keywords under
   its controls. CLDR is the operational endpoint of that study, not a complete
   definition of emoji meaning or the research programme's ultimate goal.
2. **A conditional internal contribution is measurable.** The attention-path
   test changes keyword cosine margins after readout replacement. The tested
   rank-8 explanations remain unsupported. The path has not been connected to
   ordinary response choices; its absolute top-1 effect means are zero.
3. **Context changes output scores, while interpretation of those scores remains
   unsettled.** The new tasks remove CLDR targets and score actual continuation
   probabilities. Wording, question polarity, and explicit-evidence controls
   reveal why these quantities cannot yet serve as validated meaning judgments.

The current contribution is a bounded empirical sequence and its measurement
boundaries. A stronger general contribution would explain **when a contextual
score interaction warrants an interpretation-level claim**, then demonstrate
that distinction on independently qualified material. We have not completed
that last step. Calling the current work an emoji-understanding benchmark or a
demonstrated steering method would move ahead of the evidence.

## 2. The evidence trail, with descriptive names

| Stage | What changed | What remains open |
| --- | --- | --- |
| Cross-model keyword retrieval | Established controlled lexical correspondence across the nine named configurations. | Human interpretation, ordinary responses, training-data co-occurrence. |
| Low-rank and conditional attention tests | Bounded two subspace accounts and identified a post-reset margin contribution. | Natural-state output causality and emoji specificity of that route. |
| Context-by-cue continuation scoring | Crossed goals with emoji and word alternatives on 24 authored scenarios in six families. | The meaning and comparability of authored continuations. |
| Candidate wording and execution-shape checks | Separated interaction, effect crossover, and absolute response choice; obtained exact common-prefix equality for all 624 rescored pairs. | Semantic validity does not follow from numerical consistency. |
| Author tryout and three-question development | Separated property match, conveyed interpretation, and evidence for an outcome. | Independent human judgments and the clarity of the evidence question. |
| Question-polarity and evidence-control analysis | Exposed failures of the current model/prompt/readout combination. | Which alternative format, if any, measures the intended construct. |

The [earlier research note](CONTEXTUAL_EMOJI_MEASUREMENT_RESEARCH_NOTE_V0.md)
remains an historical analysis. Its unresolved common-prefix issue and its
pre-correction contextual counts are superseded, for this inventory, by the
[matched-execution analysis](CONTEXTUAL_EMOJI_MATCHED_SHAPE_RESULTS_V1.md).
This is a new scoring version on the same data design, not fresh scientific N.
The [two-track protocol](CONTEXTUAL_EMOJI_TWO_TRACK_V1.md) and
[analysis guide](CONTEXTUAL_EMOJI_TWO_TRACK_V1_ANALYSIS.md) retain their original
collection and private-analysis boundaries; this note authorizes no changes to them.

## 3. A robust distinction: interaction, crossover, and choice

For each context and cue, the first output study scores a fixed pair of complete
continuations. The author-oriented difference of cue effects between two
contexts is H. Positive H, a reversal of the cue effect in the expected direction,
and author-aligned choices in all four inputs are successively stronger conditions.
Neither of the first two guarantees the last.

These are the **matched-execution** results used in the working paper:

| Formulation | Cue | Mean H (nats) | H positive / 24 | Crossover / 24 | All four author-aligned / 24 |
| --- | --- | ---: | ---: | ---: | ---: |
| Scenario-specific | Emoji | 1.3286 | 23 | 13 | 0 |
| Scenario-specific | Word | 2.2694 | 23 | 18 | 3 |
| Explicit negation | Emoji | 1.2329 | 23 | 12 | 1 |
| Explicit negation | Word | 1.6349 | 23 | 18 | 4 |
| Adjective pair | Emoji | 1.3695 | 24 | 15 | 2 |
| Adjective pair | Word | 2.2984 | 24 | 21 | 5 |

Across all three formulations, positive interaction persists for 22/24 emoji
and 23/24 word scenarios. Absolute candidate polarity varies on 55/96 emoji
and 56/96 word inputs. **No scenario satisfies all-four author alignment in
every formulation for either carrier (0/24 each).** Authored alignment is not
human accuracy. Words have larger mean H here, but differ in explicitness and
token/position geometry; these numbers do not rank semantic understanding.

The exact four-score decomposition explains the logical separation: offsets and
context main effects can move absolute preferences while leaving H unchanged.
It does not identify a neural cause or prove that an offset is a pretrained
answer prior. Repeated formulations remain measurements of the same 24 scenarios.

## 4. What the author tryout adds

The revised workbench distinguishes an accurately reported property from a
naturalistic message's interpretation and from evidence that a wider outcome
has occurred. One previously exposed author saw one condition per scenario:
12 bounded scenes and 12 naturalistic scenes, balanced across emoji and words.
The latter each contain two questions, giving 36 judgments on 24 scenes.

| Question | Yes | No | Undecidable | Binary | Same-question human/model agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Property match | 7 | 5 | 0 | 12/12 | 7/12 |
| Message interpretation | 3 | 6 | 3 | 9/12 | 6/9 |
| Outcome evidence | 2 | 3 | 7 | 5/12 | 3/5 |

There are no missing answers or abstentions. The ten undecidable judgments are
retained. Overall agreement is 16/26 on a response-selected binary subset.
The model had only forced Yes/No candidates, without the human assessability
option. Every one of the 36 selected model choices also follows a post-result
constant rule: Yes for property match, No for both other question types.
Agreement alone therefore provides little evidence of shared interpretation.

The bounded task is answerable for this author, which is useful for interface
development. Literal word repetition and explicit property assumptions can also
make it easy without measuring contextual sense resolution. The naturalistic
questions may mix conveyed meaning, event truth, and evidential sufficiency.
The response counts locate this difficulty; they do not determine its cause.
Question revision changes some constructs as well as wording, including visible
expression versus affect. No causal improvement over the first tryout is claimed.

The human-only reading was recorded before the current assignment/model join.
Prior project exposure remains known. This ordering preserves the analysis
trail but cannot create independent blinding retrospectively. The working
manuscript includes only aggregate results, not individual answers or notes.

## 5. The model readout needs qualification

The full two-track acquisition reuses all 24 scenarios with two contexts,
emoji/word/absent cues, three questions, and two question polarities. It adds
explicit accurate-completion and unknown-outcome controls: 1,632 candidate
pairs, 3,264 sequence scores, and 32 historical repeat checks (3,296 forwards).
All common answer prefixes agree exactly; the repeats and complete inventory
pass the numerical checks. No free text was generated.

| Positive-worded question | Emoji | Word | Absent cue |
| --- | ---: | ---: | ---: |
| Property match: Yes | 94/96 | 95/96 | 48/48 |
| Message interpretation: No | 94/96 | 90/96 | 46/48 |
| Outcome evidence: No | 95/96 | 93/96 | 48/48 |

Among 816 true/false wording pairs, 106 imply consistent truth and **710 imply
inconsistent truth**, with no primary-score ties. In the explicit accurate
completion controls, both positive and negative wording prefer No in 48/48
cases. Scoring the negated question against the authored reference alone would
give a misleading impression of success.

The continuous interaction also depends on wording. For message interpretation,
mean interaction is +0.392 nats for emoji and +0.829 for words with positive
questions, but −0.086 and −0.224 after normalizing negative questions to the
same truth direction. Positive contrasts occur on 23/24 and 24/24 scenarios
under the first wording, and 7/24 for each carrier under the second.

These observations delimit **this base checkpoint, prompt, and scoring format**.
They do not show that a whole model family cannot understand negation. Nested
questions, base-model completion preferences, answer vocabulary, and the intended
construct are candidate explanations that have not been separately manipulated.

The period after the answer token contributes to the full sequence score.
A post-result token-only diagnostic changes 103 non-tied signs and introduces
191 ties out of 1,632 candidate pairs. Its polarity counts are 78 consistent,
553 inconsistent, and 185 pairs with a tie. All 48 positive completion controls
still prefer No. Dropping punctuation does not qualify the measurement; the
original full-sequence estimator stays primary, and ties stay in the record.

## 6. Reconsidering the direction

Three possible paper shapes are worth keeping open:

| Direction | Central contribution | Present readiness | Missing evidence |
| --- | --- | --- | --- |
| A. Bounded lexical and causal study | What lexical readability and the specified interventions establish about text-only emoji representations. | The historical evidence is retained; the contextual extension can be a clearly separate limitation-driven development section. | Reader-facing framing and eventual release audit; no new positive result is required to describe existing findings honestly. |
| B. Measurement study of contextual cue effects | Distinguish a context-sensitive likelihood contrast from a validated interpretation and decision. | The separation and control failures are observed; a general methodological claim is still provisional. | A qualified instrument, independently assessed new materials, and robustness beyond one repeated inventory and one checkpoint. |
| C. Output-linked emoji mechanism | Identify an internal contribution to a meaningful contextual response in natural model states. | A research objective, not a current result. | B's qualification, new confirmation materials, calibrated bidirectional interventions, and comparable word/symbol controls. |

**Working choice:** preserve A as the paper's evidential core, develop B as the
immediate research question, and keep C as the mechanistic goal. This avoids
making the contextual extension carry a semantic claim it cannot yet support.
The current title is retained provisionally; changing the title to a broad
emoji-meaning or steering claim would be premature.

The most useful next question is narrower than “Can we obtain another effect?”:

> Can a qualified response measure distinguish what a cue conveys in context
> from whether it satisfies a goal and whether an event actually occurred?

A stable cue meaning combined with a changing goal already suffices to produce
the observed interaction. To study genuine contextual interpretation, a future
design should distinguish that case from a change in the reading of the same
cue. Independent judgments would establish the intended distinction. A later
cue-replacement or internal intervention could then ask whether the response
depends on that information. None of these steps is treated as completed here.

## 7. Smallest next steps, still proposals

1. **Clarify the question for people.** In a small separate exercise, distinguish
   reported property, conveyed meaning, completed event, and sufficient evidence.
   Use explicit complete/incomplete/unknown practice examples. Keep uncertainty
   available; reducing undecidability is not itself the objective. Exact word
   matching should remain a check, with paraphrases as a separate challenge.
2. **Qualify the model format independently of emoji effects.** Compare a short
   direct question with the current nested question on simple text-only controls.
   Retain opposite proposition wordings, answer-label/mapping swaps, both sides
   of completion controls, and constant-response comparators. If model or tuning
   changes, separate those factors from the prompt change.
3. **Specify a fresh check only after development.** Decide scoring, practical
   pass criteria, treatment of ties and uncertainty, unit of analysis, and the
   main contrast before checking unused materials. Failed controls keep a format
   in development. Existing 24-scenario effects must not choose favorable families.
4. **Then decide whether to pursue contextual interpretation or mechanism.** New
   scenario/template families and independent evaluators support the first;
   natural-state intervention and a qualified output endpoint support the second.
   Sample size and model expansion follow that choice, not precede it.

No thresholds or sample sizes for these proposals are fixed by this note.
There is no new acquisition, participant recruitment, GPU reservation, or model
download. A larger sample of the current instrument would improve estimates of
its present behavior while leaving the interpretation problem in place.

## 8. Paper integration, reproducibility, and privacy

The working manuscript preserves the four historical experiments, adds a short
development subsection to Discussion, and places detailed methods and tables
in Appendix H. It updates the earlier absolute statements that response scores
were untested and that the whole project involved no human responses. Free
generation, independent semantic validation, and output-linked causality remain
untested. The September and October 7 PDFs and the anonymous archive are preserved.

The [aggregate summary](../validation/contextual_emoji_working_revision_20261010/summary.json)
records the exact denominators and provenance. The export reconstructs all
two-track scores, joins, and token diagnostics from completed records, checks
the private completion digests, and projects only allowed aggregates. Generated
paper tables use that summary. Individual responses, assignments, personal
metadata, and notes are excluded from the repository and shared compute.
No independent assessor or external replication is implied by code verification.

The two-track acquisition took 638.745 seconds, with peak Torch reserved memory
of 6,318 MiB on the recorded RTX 5090. These are acquisition figures, not the
cost of this writing session, and do not repair historical missing compute
records. This synthesis and its checks use saved records on the local CPU.

Validation disposition: **suitable for a caveated local working draft**.
Numerical reproducibility and document quality can be checked now. Semantic
measurement validity, independent human confirmation, a new mechanistic result,
and public-release readiness remain open.
