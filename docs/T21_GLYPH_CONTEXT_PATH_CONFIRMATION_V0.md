# T21-C: Prospective glyph-position path confirmation

[日本語](T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.ja.md) | [Pilot protocol](T21_GLYPH_CONTEXT_PATH_PILOT_V0.md)

## Question and scope

After replacing a readout residual with its codepoint-view counterpart, do later
attention messages from glyph positions contribute to the corresponding-keyword
cosine margin? T21-C tests one candidate, **block 21**, selected by the previously
specified T21 pilot rule on 384 already evaluated T20 items. The original T19
and T20 primary endpoints and verdicts remain unchanged.

This protocol and its implementation are committed before the remaining 195
items are reconstructed or tokenized. They will then be recorded in an exact
input specification before any confirmation model forward. This is an internal,
timestamped prospective specification, not registration with an external registry.

## Population and protected inputs

Take **all 195 remaining emoji** from the original 954-item, globally unique
CLDR-keyword matching after excluding the 375 T19 and 384 T20 items. There is no
effect-based sampling, optional sample-size increase, or post-outcome exclusion.
Order by the Unicode source index. Reuse the 128 T19 source items for fixed
distractors and deterministic, token-count-matched donors. “Unused” refers only
to these experimental evaluations; it makes no pretraining-novelty claim.

Reconstruct only the emoji matching from the pinned emoji-test and CLDR sources.
Reserve the 55 already-recorded symbol aliases, verify the original candidate
census, and require identical aliases for **all 759 previously used emoji**.
The old repository-wide text-exposure scanner and both old selection builders
are prohibited because they read retired protected target banks. No historical
text-surface audit is repeated, and no new text-freshness claim is made.
Selection-count, allocation, tokenization, or donor mismatches stop admission;
they never silently shrink the 195-item population.

## Intervention and measurement

Use the identical Llama 3.2 3B BF16 artifact, model runtime, post-RoPE key/value
replacement, codepoint residual reset, same-slot neutral references, two donors,
and fixed 129-choice keyword gallery as the pilot. Replace only messages used
by each readout query at blocks strictly after the anchor. Other queries are
unmodified by that local attention intervention; downstream computation may
naturally transmit the intervention's effect.

Primary observations average the pipe and article carriers at **distance 8**,
and both donors, **within each target item**. Thus the inferential sample size
is 195, not the number of condition/context/donor rows. Block 24 and distance 4
are acquired with the unchanged batch layout as secondary diagnostics; they
cannot replace the primary candidate. Equal-count suffix controls match the
number of positions, not their attention mass, position, or semantic content.

Let E(condition) be its keyword margin minus the neutral-path margin in the
same batch slot, with the readout reset preserved. The five primary contrasts
are:

| Contrast | Definition |
| --- | --- |
| Calibration | E(reset) − E(all-prefix donor) |
| Absolute decrement | E(reset) − E(glyph donor) |
| Position-adjusted decrement | E(suffix donor) − E(glyph donor) |
| Absolute restoration | E(prefix donor, own glyph restored) − E(all-prefix donor) |
| Position-adjusted restoration | E(prefix donor, own glyph restored) − E(prefix donor, own suffix restored) |

All restoration/replacement conditions in this table include the readout reset.
The contrasts share conditions and are correlated; they are not five independent
replications. The absolute unit is cosine margin, **not accuracy percentage
points**. Ratios to the mean full-prefix decrement will be reported descriptively;
that reference is neither a universal ceiling nor an explained-variance measure.
There is no claim of a practically large behavioral effect or minimum useful
steering strength. Top-1 retrieval is a separate secondary endpoint.

## Multiplicity and decision

Compute **one-sided, simultaneous 95% lower bounds for all five means** using
20,000 item-bootstrap draws and seed 2026092201. The same resampled item indices
are used for every contrast. For draw b and contrast j, calculate
z(b,j) = (mean(b,j) − mean(j)) / SE(b,j), with sample-standard-deviation / sqrt(n).
The critical value is the linear-interpolated 95th percentile of max_j z(b,j).
The simultaneous lower bound is mean(j) − critical × SE(j). Degenerate standard
errors stop inference. This single-step studentized maximum construction uses
joint dependence; no stepdown procedure is implemented. See the general
resampling framework of [Romano and Wolf (2005)](https://doi.org/10.1198/016214504000000539).

A positive result requires complete engineering validation and **all five lower
bounds > 0**. If calibration fails, the pathway test is unresolved. If calibration
passes but a route contrast fails, this specified joint path claim is unsupported.
There is no early efficacy stopping, anchor substitution, or secondary-endpoint
promotion. Coverage is approximate, conditional on this fixed source pool and
an item-resampling model. The remaining 195 form an eligibility-defined census;
these intervals do not justify generalization to every emoji, language, model,
or arbitrary donor population.

## Pilot-only precision and quality assessment

Before any reserve access, the 384-item pilot was independently reconstructed
with zero differences in all saved metrics. At anchor 21, both carriers and both
token-length strata have positive mean primary contrasts. Removing the largest
5% of item effects leaves every pooled mean positive. These are descriptive
sensitivity checks, not extra confirmatory tests or exclusion rules.

Using the empirical pilot covariance and a pilot-fixed simultaneous critical
value, 5,000 simulated cohorts of size 195 pass the joint directional criterion
in 99.9% of draws at the pilot means, 98.98% after subtracting one pilot standard
error from each mean, and 60.5% at half the pilot means. These are conditional
planning estimates, potentially optimistic after candidate selection, not
guarantees of power. The confirmation recomputes its own critical value.
All available unused items are included; this assessment does not tune n or
the test threshold. The numerical report is
`validation/t21_glyph_context_path_pilot_v0/results/precision_and_quality_report.json`.

## Execution and publication gate

First publish the design/code and run the new orchestration on the original
eight exposed canary targets. Require bit-exact replay of the original canary
states, stock-attention parity, and exact same-slot no-op/roundtrip controls.
Only then reconstruct/tokenize the 195 items, record/publish their specification,
and allow one complete confirmation acquisition. GPU contention causes a
cooperative yield, never termination of another workload. Only an identical
incomplete run may resume. Errors retain their receipts; a scientific change
after reserve exposure cannot be presented as the original confirmation.

Independent CPU reconstruction must agree on metrics, intervals, and verdict
before a manuscript addition. Keep the Table-6-corrected submission PDF available
throughout. A positive result supports a **conditional late-attention message
contribution to lexical similarity in this model and intervention**. It does not
identify a unique semantic circuit, establish emoji specificity, demonstrate
behavioral steering, or convert the earlier component-local negative results
into positives.
