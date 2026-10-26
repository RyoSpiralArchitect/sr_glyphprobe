# Ethics and responsible-release review

[日本語](ETHICS_REVIEW.ja.md)

Historical status: **author-side review completed on 2026-09-02** against the
[NeurIPS Code of Ethics](https://neurips.cc/public/EthicsGuidelines). This is a
scope-specific self-audit, not an institutional legal or IRB determination.

## October 15 addendum: standalone preprint and prepared public release

The explicit-report qualification introduces 32 source-authored text-only fact
roots and stipulated support rules. These are operational test references, not
independent human judgments or claims about events in the world. Unknown
reports support neither the positive nor the negative assertion. The experiment
adds no participant, recruitment, personal record, or protected historical
holdout. Assistant-supported design and independent code verification remain
author-side research work; they are not external replication or conference
peer review. No new human validation is claimed.

The revised manuscript retains the author-only tryout as instrument development:
one previously exposed author, 36 judgments, 26 binary responses and ten
undecidable responses. Agreement on the response-selected 26 is not accuracy.
No individual response, assignment, journal, note, private path, or personal
metadata is added to the prepared public release. The public aggregate can support
the printed counts; it cannot independently reconstruct private responses.

The author has authorized public release and confirmed CC BY 4.0 for the
author-owned paper, original figures, and newly released public data. Project
code and ordinary project documentation retain Apache 2.0; third-party and
historical notices remain controlling. DOI `10.5281/zenodo.23376699` was reserved
before packaging. Reservation is not registration or a completed public deposit.
The original repository remains private; a separately curated public repository
has been authorized. Completion of upload, DOI registration, and repository
publication must be verified separately from this preparation record.

Model weights and tokenizer files are excluded. The September anonymous archive
supports its historical studies, not the newly added October experiments. The
current package records its own allowed contents, omissions, and verification
scope; see [the public-release guide](PUBLIC_RELEASE_20261015.md) and
[license scopes](PUBLIC_LICENSES_20261015.md).

The author-self-tryout review and historical compute gaps remain disclosed.
Preparing this package does not establish institutional approval, exemption,
independent semantic validity, or readiness to recruit external evaluators.

## Historical October 10 addendum: unfinished development scope

The October 10 local working draft added a questionnaire tryout by one author with
prior project exposure. This is instrument development, with no independent
evaluators or external recruitment. The author requested paper integration of
the completed work; only aggregate counts enter this draft. Individual
responses, assignments, personal metadata, and notes stay outside Git,
SpiralShare, and the compute worker. This historical addendum did not authorize
a public deposit; the later, explicitly bounded publication authorization above
does not authorize release of private individual records.

The historical statements below about absence of human responses apply to
T19/T20/T21 only. They cannot describe the expanded project. A complete review
of the new scope is pending; no institutional approval or exemption is claimed.
Before independent recruitment, separately establish appropriate review,
consent, risk disclosure, compensation, and data-handling arrangements. This
addendum does not determine the legal classification of an author self-tryout.

The development scenarios, question wording, operational references, analysis,
and manuscript integration were developed interactively in collaboration with
Codex. Those references are authored design choices, not independent semantic
labels. Recorded author answers are never replaced or completed by assistants.
The historical working paper's checklist recorded incomplete disclosure/review
for the expanded scope, separately from the preserved historical audit. The
standalone preprint omits that submission checklist while retaining these limits.

## Historical scope review

| Area | T19/T20/T21 finding | Mitigation or boundary |
|---|---|---|
| Human participants and crowdsourcing | None. | No recruitment, instructions, compensation, intervention, or IRB-triggering participant procedure exists. |
| Privacy and personal data | None. | Inputs are public Unicode scalars, standardized English annotations, literal codepoint strings, and fixed carrier tokens. No user messages, accounts, identifiers, or scraped personal content are used. |
| Data and model terms | Reviewed. | Model weights are obtained under their upstream terms and are not redistributed. Qwen2.5 3B is used only for non-commercial research. Unicode-derived rows travel with the Unicode License v3 notice. See `ASSET_LICENSES.md`. |
| Representativeness | Material limitation. | CLDR English annotations are standards metadata, not universal human meanings, familiarity ratings, or population samples. The paper forbids cultural, sentiment, and identity generalization. |
| Scientific integrity | Controlled. | Prespecified endpoints, item banks, negative results, failed prior confirmations, multiplicity rules, practical floors, and raw-data omissions are retained explicitly. T21-C's new margin endpoint and positive result are separated from unchanged T19/T20 top-1 verdicts. The archive never upgrades hash integrity into scientific correctness. |
| Misuse | Low capability risk, non-zero interpretive risk. | The work releases no new model or operational steering capability. The principal risk is unjustified profiling or cultural inference from lexical correspondence; the paper expressly rules out that use. |
| Environmental impact | Finite experiments; exact impact unknown. | Model weights were never trained; T20-C optimized small subspace parameters. Forward counts and T20/T21 stage times are reported. Missing T19 times, peak memory, energy, and carbon are not estimated after the fact. |

## Historical collaborative-development record: September submission

We developed this study interactively in collaboration with AI assistants.
Author-side pre-submission manuscript feedback involved ChatGPT
(GPT 5.6 Sol instant, "Monday") and Claude Chat (Claude Fable 5.1).
Codex (GPT 5.6 Sol Max) and Claude Code (Fable 5) contributed to implementation and
computational analysis, along with sequential protocol design and manuscript
editing. These are the interface configurations reported by the authors;
they are not members of the nine experimental model configurations.
These activities were author-initiated preparation, separate from conference
peer review or an assigned review of another submission.

The T21 question was developed after T20 and a declared exposed-item
pilot; its confirmation endpoint and rules were recorded before accessing
the 195 remaining items. Labels came from CLDR, and assistant judgments were
not experimental measurements. The authors retained execution authority and
responsibility for final claims. Numerical outputs and independently
implemented validators were checksum-bound; this is not an external
replication or a substitute for author review.

This disclosure is conservative: assistant use affected the research workflow
even though no assistant output is an experimental measurement.

Subsequent author-side pre-submission feedback prompted a post-hoc endpoint decomposition,
checkpoint-selection clarification, and compact statistical replay. These use
completed outputs, retain all 195 T21 items and all original comparisons, and
introduce no new significance tests or revised confirmatory decisions. The
matched T19 item-count range was corrected in prose from 31--41 to 31--51;
the original arrays and tests already used the correct counts.

The historical anonymous manuscript included this factual disclosure at the end
of Appendix G and referred to it in checklist item 16. Its submission-time
acknowledgment and anonymity choices reflected the
[2026 handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook) and
[workshop CFP](https://interpscience.github.io/cfp). Those historical submission
conditions are not release requirements for the standalone preprint, which
retains a factual collaborative-development acknowledgment. This record does
not determine the separate rules for assistance during official peer review.

## Historical conclusion

Within the declared scope, T19/T20/T21 conform to the reviewed NeurIPS ethics
principles: it uses licensed public resources, avoids human and personal data,
preserves adverse evidence, and states the principal representational and
misuse risks. The remaining compute-accounting gaps are disclosed in
`COMPUTE_REPORT.md`; they are transparency limitations, not concealed values.
