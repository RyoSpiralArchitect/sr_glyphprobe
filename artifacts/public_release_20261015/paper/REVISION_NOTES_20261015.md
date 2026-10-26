# October 15 revision record

[日本語](REVISION_NOTES_20261015.ja.md) · [Current claims](CURRENT_CLAIMS_20261015.md) · [Public release](PUBLIC_RELEASE_20261015.md)

This revised preprint follows the workshop submission and subsequent author-side
review. It does not claim workshop acceptance, a conference proceedings paper,
or external replication. Historical PDFs, evidence archives, numerical results,
and the October 10 working-claims record are retained unchanged. The present
revision is prepared for authorized public release. DOI `10.5281/zenodo.23376699`
was reserved before packaging; this record does not assert completed public
deposit or DOI registration.

## Four review repairs

| Issue | Revision | What remains bounded |
| --- | --- | --- |
| The September archive could appear to support the entire revised manuscript. | Separate historical T19/T20/T21 evidence from the October development and new explicit-report qualification; prepare a version-specific, allowlisted local package. | A manifest verifies the identified files. It does not establish scientific validity or reconstruct omitted private responses or raw historical model states. |
| Contextual inputs were too abbreviated to make the measurement intelligible. | Add complete public prompt and candidate examples, crossing scenario, emoji, and word controls and showing explicit completion checks. | Examples explain the procedure; they are not new experimental observations or private questionnaire disclosures. |
| The account of uncertainty mixed descriptive and decision-making intervals. | State separately that T19-L bootstrap intervals are descriptive; fixed- and optimized-subspace decisions also require bootstrap lower bounds above their floors; the attention-path test uses its specified simultaneous one-sided bounds. | Historical tests, multiplicity rules, thresholds, and verdicts are unchanged. |
| “Ceiling” suggested an unproved universal intervention bound. | Describe the relevant comparisons as full-state reference swaps. | These comparisons characterize the tested replacement; they do not bound every possible intervention. |

The input examples have source checks against public scenario definitions and
the public candidate inventory. Wording repairs do not change observed values.
Manuscript compilation, layout inspection, code tests, and numerical acceptance
remain distinct checks.

## Substantive follow-up: qualify the readout before interpreting emoji

The contextual development experiment found failures on accurate-completion
controls, so another emoji panel would leave the measurement question unresolved.
The new explicit-report experiment holds the stipulated fact and queried
proposition fixed while varying question embedding and answer encoding.
It uses no emoji or CLDR label and needs no inferred human meaning.

The [protocol](../docs/READOUT_QUALIFICATION_V1.md) was recorded before model
scores: 32 roots in four authored families, two development families and two
reserved-check families, three report states, two asserted polarities, three
question forms, and four answer formats. This produces 2,304 candidate pairs,
4,608 scientific sequence forwards, and 32 historical sentinel forwards.
The fixed primary asks whether direct/minimal Yes–No is correct on every one
of 96 reserved-check cases. A separate requirement asks whether both explicit
A/B mappings are correct on all 192 reserved-check cases. Ties and missing
rows remain visible. These are finite-set operational criteria, not population
accuracy thresholds or externally registered confirmatory tests.

The prepared specification SHA-256 is
`5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f`.
It binds inputs, logical references, mappings, source, runtime, model artifact,
and the execution schedule. All **4,640 forwards / 2,304 pairs** completed, with
zero missing pairs. Numerical checks passed and the separate saved-score
implementation agreed. The primary criterion failed: **88/96** correct,
four incorrect, four tied, and **8/16** roots correct on all six cases.
Class-balanced accuracy is 0.9375. The direct A/B requirement also failed:
**104/192** correct, 69 incorrect, 19 tied, and no completely correct root.

For the same reserved roots, minimal-answer correctness changes from 88/96
under the direct question to 65/96 under nested-true and 57/96 under
nested-false questions. Direct full-sentence answers give 75/96, while direct
A/B answers give 45/96 with A meaning Yes and 59/96 with A meaning No.
The complete 12-condition comparison for each split is retained in
[the current claims](CURRENT_CLAIMS_20261015.md) and
[the checked projection](generated/readout_qualification_20261015/summary.json).
No format was selected retrospectively to replace a failed primary measure.

The first-divergent-token diagnostic for direct/full-sentence reserved answers
is 63/96 correct with 12 ties; the final period resolves those ties correctly
to give 75/96. The minimal format's 88/96 cannot be attributed to period
removal because its prefix and response instructions also change. Moreover,
nested-false/minimal's 57/96 is below constant Yes (64/96), with class-balanced
accuracy 0.44531. These diagnostics preserve the question-specific baselines
and do not replace the primary scorer.

The contribution of this follow-up is a bounded measurement result: failures
persist on explicit text-only reports under numerically matched scoring, and
the readout varies with question structure and answer encoding. It does not
attribute the variation to a neural mechanism or establish an emoji effect.
The finite experiment is complete; ordinary-output semantic and causal claims
remain unqualified. The earlier experiments retain their original scope.

## What this version does not resolve

The author-only tryout remains developmental: one previously exposed author,
36 judgments, 26 binary answers, and ten undecidable answers. Its response-selected
agreement is not semantic accuracy. The historical lexical and conditional
attention-message results remain separate from ordinary response behavior.
Independent semantic evaluation, cross-model contextual replication, and
natural-state output causality require separate designs and evidence.

The author authorized public release and confirmed CC BY 4.0 for the
author-owned paper, original figures, and newly released public data. Code and
ordinary documentation retain Apache 2.0; third-party and historical notices
remain unchanged. The prepared package excludes private responses, participant
metadata, protected historical banks, model weights, tokenizer files, and
unapproved upstream template redistribution. The original repository remains
private; a separately curated public repository is authorized. Public deposit,
DOI registration, and repository publication are verified separately from this
preparation record. See the paired
[ethics](ETHICS_REVIEW.md), [compute](COMPUTE_REPORT.md), and
[release](PUBLIC_RELEASE_20261015.md) records and
[license scopes](PUBLIC_LICENSES_20261015.md).
