# Claim boundary for the October 15 revised preprint

[日本語](CURRENT_CLAIMS_20261015.ja.md) · [Revision notes](REVISION_NOTES_20261015.md) · [Historical claims](CLAIM_TABLE.md)

Status: prepared public release with author-confirmed licenses and reserved DOI
`10.5281/zenodo.23376699`; public deposit and DOI registration are not asserted
by this preparation record. Historical results are preserved. The October 10
[working-claims record](WORKING_CLAIMS_20261010.md) remains a dated record;
this document supplies the boundary for the expanded revision.

## What each evidence layer supports

| Evidence | Allowed statement | Excluded inference |
| --- | --- | --- |
| Historical lexical retrieval: 55 emoji, 55 symbols, nine model/tokenizer configurations | Word-disjoint CLDR-keyword retrieval exceeds the codepoint comparison under the specified analysis, including exact four-view token-count matching; the four-model partial-conjunction primary has p = 0.0027. | Human meaning, visual glyph perception, token-identity control, independence from tokenization, or ordinary response behavior. |
| Historical component and path interventions | The tested rank-8 accounts lack the specified support within their calibration limits. Glyph-position messages contribute to keyword cosine margin under a specified readout-reset intervention. | Every possible rank-8 account is false, a complete circuit is established, or the same route drives ordinary generated responses. |
| Contextual matched execution: 24 reused scenarios, six families, 624 candidate pairs | Emoji interactions are positive across three formulations in 22/24 scenarios, and words in 23/24; complete authored-choice alignment across formulations is 0/24 for either carrier. Absolute polarity changes on 55/96 emoji and 56/96 word inputs. | Independent replication, increased scenario N, an emoji-specific advantage, or semantic accuracy. |
| Author-only instrument tryout: one exposed author, 36 judgments | There are 26 binary and ten undecidable responses. Agreement with model choices is 16/26 on a response-selected subset. A post-result question-type constant rule reproduces all 36 selected model choices. | Independent human labels, accuracy, population answerability, or evidence that the interface improved causally. |
| Earlier polarity and completion controls: 1,632 candidate pairs | 710/816 wording pairs have inconsistent implied truth. All 48 positive-worded accurate-completion controls prefer No. The answer-token diagnostic changes 103 non-tied signs and produces 191 ties, while the same 48 controls still prefer No. | A general inability of Llama or language models to understand negation, a neural explanation, or a valid post-hoc replacement estimator. |
| New explicit-report qualification: 32 roots, 2,304 pairs, 4,640 forwards | Acquisition and independent saved-score checks are complete. Direct/minimal answers give 88/96 correct with four wrong and four tied; only 8/16 reserved roots are wholly correct. Direct A/B mappings give 104/192 correct with 69 wrong and 19 tied. Both fixed qualification requirements fail. | Treating unknown as explicitly false, counting repeated comparisons as independent tasks, selecting the best format after observing results, or declaring semantic validity from numerical acceptance. |

The contextual author aggregate contains no individual assignments, answers,
notes, private paths, or participant metadata. Recomputing that public aggregate
is not independent verification of the private response records. No new
participant or human validation is added by the text-only qualification.

## Qualification decision boundary

The specification precedes scores and fixes both decisions. The primary is
direct/minimal Yes–No correctness on all 96 reserved-check cases with zero ties,
including all six cases for each of 16 roots. The separate label-robustness
criterion requires all 192 direct-question cases under both A/B mappings to
be correct. Passing one does not pass the other. Constant No attains 2/3 raw
accuracy on direct support queries and 1/2 class-balanced accuracy; matching
that baseline cannot qualify the measurement.

The run completed every planned row with zero missing pairs. Numerical
acceptance and the independent arithmetic check passed; qualification status
is **not qualified**. The primary reaches 0.9375 class-balanced accuracy but
does not meet its all-correct requirement. Its four errors and three of its
ties occur when a positive report is queried with a negative assertion. The
remaining tie is an unknown report queried with a positive assertion.
Explicitly negative reports give 32/32 correct under this primary format.
This pattern does not establish a general failure to understand negation.
BF16-path ties remain in the denominator; other compute precisions were not
compared.

## Complete question/answer comparison

Each correctness denominator is 96; parentheses contain ties. Root success
requires all six report–assertion combinations. These are descriptive counts,
not independent population estimates.

| Question | Answer encoding | Development correct (ties) | Reserved correct (ties) | Reserved balanced accuracy | Reserved complete roots / 16 |
| --- | --- | ---: | ---: | ---: | ---: |
| Direct | Full sentence | 79 (0) | 75 (0) | 0.71094 | 0 |
| Direct | Minimal Yes/No | 88 (6) | 88 (4) | 0.93750 | 8 |
| Direct | A = Yes | 50 (6) | 45 (15) | 0.58594 | 0 |
| Direct | A = No | 59 (2) | 59 (4) | 0.46094 | 0 |
| Nested true | Full sentence | 80 (0) | 74 (0) | 0.70313 | 0 |
| Nested true | Minimal Yes/No | 75 (16) | 65 (16) | 0.75781 | 3 |
| Nested true | A = Yes | 56 (17) | 60 (14) | 0.66406 | 1 |
| Nested true | A = No | 41 (9) | 34 (21) | 0.29688 | 0 |
| Nested false | Full sentence | 18 (0) | 24 (0) | 0.32031 | 0 |
| Nested false | Minimal Yes/No | 36 (12) | 57 (4) | 0.44531 | 0 |
| Nested false | A = Yes | 38 (14) | 39 (12) | 0.34375 | 0 |
| Nested false | A = No | 36 (15) | 30 (34) | 0.42188 | 0 |

For the direct reserved comparison, the two decoded letter mappings are both
correct on 14/96 cases, inconsistent on 64/96, and tied in at least one mapping
on 18/96. The 104/192 requirement counts the two answers per case separately;
14/96 instead requires both answers to be correct. These denominators are not
interchangeable. The [checked projection](generated/readout_qualification_20261015/summary.json)
retains exact values, all report-state and family strata, root margins, and
the separate first-divergent-token diagnostic.

For reserved direct/full-sentence answers, scoring only the first divergent
token gives 63/96 correct and 12 ties; including the period resolves all 12
ties correctly, giving 75/96. Minimal answers' 88/96 is therefore not a
demonstrated benefit of removing the period: the answer prefix and response
instructions also differ. For nested-false/minimal answers, 57/96 is below
the constant-Yes reference of 64/96, with class-balanced accuracy 0.44531.
Raw correctness across different question polarities should not obscure their
different answer prevalences.

The four template/domain families and their development/reserved division are
source-authored, not a random population sample. Every format is reported.
All results are finite-set and configuration-specific: one pinned Llama 3.2
3B base checkpoint, instruction wording, and continuation scorer. Full-sequence
and first-divergent-token scores remain distinct. No population p-value or
confidence interval is added. No post-result format change replaces the fixed
primary criterion.

Exact prefix equality, sentinel replay, artifact hashes, complete scheduling,
and independent code reconstruction establish their respective numerical and
provenance checks. They do not establish semantic validity, hardware-independent
exactness, or external replication. The failed qualification retains the
limitation and completes the prespecified finite experiment. The different
scores across answer formats do not establish a causal repair of the earlier
48-control failure: the current reports and task instructions are also new.

## Open scientific and release questions

The study separates lexical correspondence, conditional internal intervention,
and the measurement of response behavior. CLDR correspondence does not stand
in for human semantics. The current experiments do not establish an emoji-specific
behavioral mechanism. Independent evaluators and new materials, contextual
replication on another model, and output-linked interventions in ordinary model
states remain separate unexecuted steps.

The prepared package and its validation are distinct from completed public
release. The author confirmed CC BY 4.0 for the author-owned paper, original
figures, and new public data. Code and ordinary documentation retain Apache 2.0;
third-party and historical notices are unchanged. DOI `10.5281/zenodo.23376699`
is reserved, not registered by this preparation record. The original repository
remains private; a separately curated public repository is authorized. Completed
deposit, repository publication, and conference acceptance are not claimed here.
See [the public-release guide](PUBLIC_RELEASE_20261015.md) and
[license scopes](PUBLIC_LICENSES_20261015.md).
