# Post-review evidence plan v0

[Japanese](POST_REVIEW_EVIDENCE_PLAN_V0.ja.md)

Written on 2026-09-02, before the new decomposition is computed. This is a
**post-hoc diagnostic and reproducibility audit**, following review of the
completed T19/T20/T21 experiments. It is not a new prospective confirmation.
The existing protocols, eligibility rules, statistical decisions, and result
receipts remain unchanged. No new model forwards or target selection are allowed.

## 1. T20 selection and training diagnostics

Reconstruct all 27 site/seed checkpoint choices from the saved training history.
Within a seed, select the first checkpoint attaining the largest validation
score; across seeds, select the largest score and break ties by the lowest seed.
Report the selected checkpoint separately from step 600. A recorded training
loss is the pre-update minibatch loss in that iteration, whereas the saved
basis follows the update. Neither value is a full-training-set measurement of
the returned basis. Preserve the registered uncalibratable primary verdicts.

## 2. T21 margin decomposition

Use all 195 confirmation items, the original block-21 anchor, both distance-8
carriers, both predetermined donors, the unchanged 128-item source gallery,
and all five original contrasts. Reconstruct from the saved states:

- own-keyword cosine;
- largest source-keyword cosine;
- injected donor-keyword cosine, as a diagnostic of gallery competition.

Use one 129-column similarity calculation, with the target's own keyword in
column zero, as in the original measurement. Subtract each condition's own
neutral reference at the identical batch slot before averaging within items.
Apply the original contrast operators separately to each component. Verify
itemwise that the own-keyword contrast minus the largest-competitor contrast
equals the original margin contrast, within a numerical tolerance of `1e-10`.
Also reconstruct the original margin, donor-margin, and top-1 arrays at all
saved contexts and anchors; require agreement within `1e-10`, with exact top-1
agreement. Validate source, specification, chunk, and analysis checksums first.

Report descriptive component means for every original contrast. Do not add
component significance tests, outcome-based item exclusions, model/anchor
selection, new thresholds, or a second confirmatory verdict. The maximum
competitor can change identity between conditions: this decomposition is an
identity of the endpoint, not a mediation analysis separating biological or
computational mechanisms. Donor similarity is not an additive third component.

## 3. T19 model-free statistical replay

Export the existing primary prediction indices, exact local strata, and item
orders to compact JSON. Check each source summary against the previously
published independent-validation hash and its prediction-file checksum. Retain
all nine configurations, both glyph kinds, both components, and all 24 primary
contexts; do not reconstruct hidden states or tokenize any bank.

A separate NumPy-only program will recompute the 36 randomization tests,
20,000-replicate descriptive intervals, model intersection--union values,
effect-size checks, Holm decisions, and the four-core partial-conjunction
result. Match the original seeds and draw order. Explain `1/n` as the uniform
guessing benchmark; the matched randomization expectation depends on each
prediction's membership in the target's stratum.

## 4. Presentation and delivery

After numerical checks, update the English paper and paired repository
documentation. Give T21 a compact main-text explanation/figure, retaining the
full five-contrast table and any descriptive decomposition in the appendix.
Preserve the nine-page main-text limit. Produce a new anonymous archive version
with compact replay inputs and validators; retain earlier archive versions.
Validate the extracted archive and inspect the rendered submission PDF.

The two retired historical target banks remain unopened. All new work uses
already authorized, completed T19/T20/T21 outputs. Checksums establish identity,
not correctness; numerical reconstruction is a separate check.
