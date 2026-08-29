# Emoji Steering Specificity Analysis v0 — Point Results

[日本語](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.ja.md) ·
[Analysis contract](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md) ·
[Acquisition protocol](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) ·
[Zero-gate amendment](EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md) ·
[Compact evidence index](../artifacts/emoji_steering_specificity_analysis_v0/README.md)

Status: **completed exploratory point analysis; share with caveats; paper
interval gate pending**.

## Technical summary

T13-EA finds a structured but non-unique intervention signal. Source-form
directions often separate from the positive isotropic null near depth 0.875,
and positive/negative interventions become more nearly opposite in output
space near the final block. These patterns are not confined to glyph input:
Unicode names, decomposed forms, and codepoint literals can show the same
late-depth calibration advantage.

The strongest decomposition result is correspondingly qualified. Glyph and
decomposed-form source directions are highly aligned for modifiers,
presentation sequences, and ZWJ sequences, but much less aligned for keycaps
and regional flags. Under fixed unit-RMS interventions, glyph directions tend
to produce larger nonnegative response endpoints than decomposed forms, yet
that difference is driven mainly by keycaps and regional flags and reverses or
vanishes in some model/system/sign cells.

Three observations prevent a unique emoji-mechanism claim:

1. target top-two margin strongly predicts argmax flips even for random
   directions;
2. wrapper-to-wrapper variation is large relative to the mean source
   direction; and
3. the stored tokenizer preflight supports count-signature comparisons, not
   exact token-ID or prefix matching.

The defensible result is therefore narrower: **structured source directions
show depth-, dose-, target-, model-, and glyph-system-dependent intervention
geometry relative to a limited positive isotropic null**. This is not evidence
that a model has a unique emoji-meaning mechanism.

## Acquisition and integrity

The fixed [T13-EH protocol](EMOJI_STEERING_SPECIFICITY_HARVEST_V0.md) contains
192 items from six glyph systems, 912 available item-form rows, 32 public
targets, eight normalized depths, three intervention magnitudes, and two signs
for the item and prototype arms. The random arm has positive orientation only.
Nine model/tokenizer roles contributed source banks; three base-model roles
also contributed the intervention pilot:

- `qwen25_0p5b_base_bf16`
- `llama32_3b_base_bf16`
- `qwen25_7b_base_bf16`

The pilot contains 383,232 intervention rows: 105,984 item-form rows, 129,024
prototype rows, 147,456 random rows, and 768 zero-hook rows. No generation was
performed; response endpoints concern the next-token distribution.

| Integrity check | Evidence | Result |
|---|---:|---|
| Required roles | 9 / 9 | pass |
| Receipt files | 198 | pass |
| Receipt-bound payload files | 954 | pass |
| All verified files, including summaries | 1,161 | pass |
| Independently hashed bytes | 4,535,141,572 | pass |
| Run-binding root | `c0316c2c1b939ae831a3421c296d7eff4acd79a18747ac41eb04053ce0a88acf` | bound |
| Derived outputs equal across furnace and Mac views | 6 / 6 SHA-256 matches | pass |
| Raw arrays copied from the furnace | 0 | pass |

All scientific values remained closed until the same analyzer process audited
the committed freeze, preflight bindings, and complete external closeout. The
expected composite keys were unique in F4–F6, nested F5 counts matched their
declared sign-pair denominators, and core numerical summaries were finite.
The 432 missing F6 form rows exactly match the frozen structural absence of
component and decomposed forms for 24 atomic anchors across nine models.

## Historical v0 failure and the separate v1 gate

The original v0 exact-JS gate failed closed on `js_divergence`. This is a
preserved procedural failure, not a discarded preliminary run.

| Stage | What happened | Scientific values opened? | Disposition |
|---|---|---:|---|
| Historical v0 | Exact equality failed on the zero-control JS field | no | failure retained; no analysis output written |
| Amendment freeze | A float32 algorithmic allowance was fixed before the exact live residual magnitude was inspected | no | separate post-failure amendment |
| v1 zero gate | Primitive no-op quantities remained exact; JS satisfied `abs(JS) <= 8 * eps(float32)` | zero rows only until all three roles passed | nonzero analysis authorized |

The historical failure receipt did not record the exact failed magnitude or
the responsible model role. Those facts must remain unknown. A later
counterfactual check shows that the current rows from all three pilot roles
would fail the old exact-JS predicate, but this does not identify what happened
in the historical attempt.

The amended threshold is `9.5367431640625e-07`. Observed maximum absolute JS
round-trip residuals were `3.657e-08` for Qwen 0.5B, `1.745e-08` for Llama 3B,
and `4.214e-08` for Qwen 7B. KL, total variation, logit-delta RMS, entropy
identity, argmax identity, top-tail values, and CountSketch remained exact
primitive no-ops. The v1 result does **not** claim exact JS and is not a
scientific effect.

## F1 — Item source-form contrasts

F1 retains 105,984 paired item × target rows at depth 0.50 and magnitude 0.25.
Glyph–name contrasts use all 192 items; contrasts involving decomposed forms
use 168 non-atomic items. No missing form is imputed.

For glyph minus decomposed form, the four continuous nonnegative endpoints are
positive in every model × sign summary:

| Model | KL range over signs | JS range | TV range | Logit-RMS range | Argmax-flip range |
|---|---:|---:|---:|---:|---:|
| Llama 3B | +0.003943–+0.004324 | +0.000979–+0.001024 | +0.006509–+0.006544 | +0.009605–+0.010849 | +0.002976–+0.021577 |
| Qwen 0.5B | +0.000792–+0.002714 | +0.000331–+0.000498 | +0.000691–+0.002465 | +0.002524–+0.015047 | +0.002232–+0.008185 |
| Qwen 7B | +0.004102–+0.006799 | +0.000954–+0.001733 | +0.006355–+0.010485 | +0.032531–+0.048901 | −0.006510–+0.006324 |

The system-level pattern is not uniform. The following values average the six
model × sign summaries for glyph minus decomposed form:

| Glyph system | KL | JS | TV | Logit RMS |
|---|---:|---:|---:|---:|
| keycap | +0.008386 | +0.002047 | +0.013085 | +0.018676 |
| modifier | −0.000841 | −0.000212 | −0.001708 | +0.002970 |
| presentation | +0.003381 | +0.000810 | +0.004964 | +0.016861 |
| regional flag | +0.009604 | +0.002352 | +0.014755 | +0.039275 |
| ZWJ | +0.002431 | +0.000591 | +0.003209 | +0.019659 |

Thus the positive aggregate is driven especially by regional flags and
keycaps, while modifiers are slightly negative on KL, JS, and TV. Glyph minus
Unicode name also reverses for Qwen 7B under the positive sign across all five
nonnegative endpoints. F1 supports heterogeneous orientation effects under
the imposed intervention scale, not a universal ordering of source forms.

## F2 — Prototype depth and dose surface

The complete 129,024-row prototype surface shows highly regular dose ordering
for nonnegative endpoints, but not for signed entropy change. Each value below
is the mean target fraction for which the three frozen doses are
nondecreasing.

| Model | KL | JS | TV | Logit RMS | Argmax flip | Entropy change |
|---|---:|---:|---:|---:|---:|---:|
| Llama 3B | 0.9920 | 0.9919 | 0.9841 | 0.9983 | 0.9911 | 0.3096 |
| Qwen 0.5B | 0.9945 | 0.9943 | 0.9820 | 0.9985 | 0.9916 | 0.3094 |
| Qwen 7B | 0.9773 | 0.9771 | 0.9466 | 0.9681 | 0.9976 | 0.3131 |

Raw nonnegative effects peak at depth 1.0 for Llama 3B and Qwen 7B. Qwen 0.5B
peaks at depth 0.875 except for argmax flips, which peak at 1.0. Signed entropy
change is neither dose ordered nor strongly antisymmetric: its mean normalized
antisymmetry residual, where zero is perfect, is 0.549, 0.642, and 0.629 for
Llama 3B, Qwen 0.5B, and Qwen 7B respectively.

## F3 — Positive isotropic random calibration

F3 compares only positive prototype orientations with 64 deterministic,
unit-RMS positive isotropic directions at the same model, target, normalized
depth, and magnitude. It does not calibrate negative prototypes.

Mean prototype percentiles within the positive random distribution are:

| Model | KL | JS | TV | Logit RMS | Argmax flip |
|---|---:|---:|---:|---:|---:|
| Llama 3B | 0.8081 | 0.8095 | 0.7754 | 0.8370 | 0.5246 |
| Qwen 0.5B | 0.6819 | 0.6858 | 0.6536 | 0.6876 | 0.5162 |
| Qwen 7B | 0.7488 | 0.7497 | 0.6869 | 0.7002 | 0.5084 |

KL, JS, and TV calibration peaks at depth 0.875 in all three models. At that
depth the KL/JS/TV percentiles are 0.968/0.970/0.913 for Llama 3B,
0.918/0.922/0.869 for Qwen 0.5B, and 0.969/0.970/0.884 for Qwen 7B. Despite
large raw final-depth responses, Qwen 0.5B falls to 0.476/0.508/0.519 and Qwen
7B to 0.450/0.470/0.432 at depth 1.0. The late raw peak therefore cannot be
read as a specificity peak.

Argmax-flip percentiles remain near the random median. Moreover, the depth
0.875 advantage appears across several source forms, not only glyphs. The
fixed positive isotropic null distinguishes structured directions from generic
isotropic directions; it does not isolate emoji glyphs from structured text.

## F4 — Target sensitivity

F4 first reduces each intervention grid to a 32-target response profile. It is
a pooled sensitivity diagnostic, not a fixed-stratum source comparison.

| Baseline feature → endpoint | Cells with the same direction | Spearman range | Interpretation |
|---|---:|---:|---|
| Top-two logit margin → argmax-flip rate | 9 / 9 negative | −0.960 to −0.668 | close baseline decisions flip more readily |
| Baseline entropy → entropy change | 9 / 9 negative | −0.854 to −0.364 | strong target-state dependence / ceiling behavior |

Both relationships persist in the random-direction condition. Target-group
ranges are also substantial but their leading groups change by model and
endpoint. The stable finding is generic target susceptibility, not glyph
specificity.

## F5 — Output direction

F5 compares CountSketch and top-token tails only within a model. Across 64,512
prototype sign pairs, the weighted mean `cos(S+, -S-)` is 0.658.

| Slice | Sign-reversed CountSketch cosine |
|---|---:|
| Llama 3B | 0.731 |
| Qwen 0.5B | 0.664 |
| Qwen 7B | 0.580 |
| depth 0.125, models pooled | 0.415 |
| depth 1.0, models pooled | 0.946 |
| magnitude 0.125, models pooled | 0.764 |
| magnitude 0.25, models pooled | 0.731 |
| magnitude 0.50, models pooled | 0.479 |

This depth increase and high-dose degradation are consistent with a local
linearity hypothesis: interventions near the readout preserve opposite signs,
whereas earlier or larger interventions pass through more nonlinear
computation. It is only a candidate explanation. Eleven of 2,016 prototype
summary cells have a negative mean sign-reversed cosine, concentrated in
high-dose Qwen cells; the minimum is −0.369 for Qwen 7B keycap/decomposed form
at depth 0.25 and magnitude 0.50.

Cross-model target-rank concordance is modest and heterogeneous. Median
Spearman is 0.480 for Qwen 0.5B versus Qwen 7B, 0.391 for Llama 3B versus Qwen
0.5B, and 0.240 for Llama 3B versus Qwen 7B. Raw sketch coordinates and token
IDs are never compared across models. The sign-reversed cosine is the algebraic
sign reversal of the original cosine, not independent evidence, and there is
no sign-matched random control.

## F6 — Source geometry

F6 audits the nine-role source bank. All 65,664 stored mean directions equal
the independently recomputed mean of their four wrapper deltas.

| Within-model source-form pair | Item-weighted cosine |
|---|---:|
| glyph ↔ decomposed form | 0.844 |
| glyph ↔ Unicode name | 0.599 |
| Unicode name ↔ decomposed form | 0.586 |

Pairs involving decomposed form exclude the 24 atomic anchors for which that
form is structurally unavailable; the glyph–name population includes all 192
items.

The glyph–decomposed alignment varies sharply by glyph system:

| System | Cosine |
|---|---:|
| ZWJ | 0.940 |
| modifier | 0.926 |
| presentation | 0.902 |
| keycap | 0.646 |
| regional flag | 0.633 |

Across models, glyph–decomposed, glyph–name, and name–decomposed cosines fall
from 0.885 to 0.769, 0.701 to 0.407, and 0.686 to 0.423 between the first and
last registered depths. Gemma 2B is the coherent exception: its corresponding
final-minus-first changes are +0.026, +0.120, and +0.149. The other eight
model roles have negative model-level changes for all available pairs.

Wrapper dependence is material. Mean wrapper-to-direction cosine ranges from
0.597 to 0.667 across models, while wrapper residual RMS divided by mean-
direction RMS ranges from 1.115 to 1.348. Wrapper agreement is U-shaped over
depth: cosine is 0.719 at the first depth, falls to about 0.596 in the middle,
and returns to 0.704 at the final depth.

Count-signature-matched pair summaries have a pooled cosine of 0.748 versus
0.662 for unmatched summaries. This pooled difference is compositionally
confounded. Among 592 same-model/system/pair/depth comparisons containing both
groups, the matched-minus-unmatched median is only +0.0118; 204 comparisons are
negative, and the glyph–decomposed mean difference is −0.0099. Token count
alone is not a uniform explanation, but exact tokenization remains untested.

## Strongest decomposition story

The six families support a three-part exploratory account:

1. **Shared source geometry.** Glyph and deterministic decomposition
   directions are often close for systems whose visible form is explicitly
   compositional, especially modifiers, presentation sequences, and ZWJ
   sequences.
2. **Residual orientation difference.** After unit-RMS normalization, glyph
   interventions often induce somewhat larger nonnegative next-token changes
   than decomposed interventions, especially for regional flags and keycaps.
   The ordering is not universal and is weak or reversed for modifiers and
   selected Qwen 7B cells.
3. **Late structured-direction gain.** Several source forms rise above the
   positive isotropic null near depth 0.875, while final-layer raw effects can
   remain large even when relative calibration collapses.

This account concerns structured source directions and where they enter the
residual stream. It does not distinguish semantic decomposition from
tokenization, wrapper context, orthographic structure, or another shared
feature of the source strings.

## Negative and heterogeneous findings

- Argmax-flip calibration is near the isotropic random median despite clearer
  KL, JS, TV, and RMS separation.
- The final layer maximizes many raw effects but not random-relative
  specificity in the two Qwen roles.
- Entropy change has weak dose ordering and poor scalar antisymmetry.
- The glyph–decomposed outcome contrast is system dependent; modifiers do not
  follow the aggregate positive direction.
- Qwen 7B reverses glyph–name ordering under the positive sign.
- Eleven prototype output-direction cells fail even mean sign reversal.
- Cross-model target rankings are not uniformly stable.
- Gemma 2B reverses the dominant depth-separation trend in F6.
- Wrapper residual variation is at least as large as the mean direction RMS.
- Count-signature matching does not produce a uniform geometry shift.

These are retained results, not cells to be removed before paper writing.

## Data-quality and validation rating

| Gate | Rating | Meaning |
|---|---|---|
| Frozen acquisition completeness | **PASS** | all nine roles and registered artifacts verified |
| Within-set schema, grain, and hash integrity | **PASS** | exact bindings, expected structural missingness, no detected key duplication in inspected compact tables |
| Furnace-to-Mac derived-output equality | **PASS** | 6 / 6 files match by SHA-256 |
| Historical v0 exact-JS gate | **FAIL, preserved** | fail-closed procedural result before nonzero open |
| Separate v1 primitive-no-op / bounded-JS gate | **PASS** | exact primitives plus algorithm-derived JS allowance; not exact JS |
| Complete-family point derivation | **PASS** | F1–F6 reported without outcome-based rescue |
| Registered uncertainty intervals | **PENDING** | 0 / 20,000 bootstrap replicates executed |
| Exact-token and prefix matching | **NOT ESTABLISHED** | preflight stores count signatures only |
| Behavioral, confirmatory, and external validity | **NOT ESTABLISHED** | public targets, three intervention pilots, no generation, no untouched confirmation |

The data are suitable for a caveated exploratory report and for choosing the
next discriminating experiment. They are not yet suitable for paper-facing
interval claims or a confirmatory conclusion.

## Bootstrap and paper gate

All reported values are point estimates. The registered percentile cluster
bootstrap requires 20,000 replicates with seed `2026082913`; none has been
executed. The present one-shot CLI is not yet a frozen deterministic
high-level chunk-and-merge contract. The paper interval gate remains closed
until that execution contract is frozen, every registered chunk is complete,
and the deterministic hash merge passes. Point inspection cannot retroactively
change the registered family, cell population, endpoint, or resampling rule.

## Claim limits

- **Exact tokens:** only raw token counts and added-count signatures are
  available. Exact token IDs and prefix identity were not matched.
- **Wrappers:** each source direction averages four public wrappers, but
  wrapper variation remains large. Wrapper invariance was not established.
- **Random controls:** the null is positive-orientation isotropic and unit-RMS
  matched. There is no negative, activation-covariance-matched,
  activation-manifold-matched, or orthogonalized null.
- **Text controls:** no matched ordinary-text or non-emoji Unicode control is
  present.
- **Targets:** all 32 targets were already public. They are not an untouched
  confirmatory bank.
- **Models:** F1–F5 use three base-model pilots. F6 uses nine source-bank roles,
  but raw hidden or vocabulary coordinates are never compared across models.
- **Scale:** unit-RMS intervention normalization removes natural source
  strength. Results concern orientation under the imposed scale.
- **Behavior:** only next-token distributions were measured; no generation or
  downstream task behavior was evaluated.

Accordingly, T13-EA does not establish emoji meaning, unique emoji
specificity, a mechanism, tokenizer independence, a scale law, model-
population generality, behavioral steering, independent replication, or a
confirmatory verdict.

## Next discriminating experiments

1. Freeze exact token-ID and prefix-matched emoji, decomposed, ordinary-text,
   and non-emoji Unicode controls before collecting new outcomes.
2. Add positive and negative random directions, plus covariance- and
   activation-manifold-matched nulls, at the same model/target/depth/dose
   strata.
3. Use wrapper holdout: estimate a direction from three wrappers and evaluate
   the fourth, rotating the held-out wrapper without reselection.
4. Resolve the depth-0.875 versus depth-1.0 split with a preregistered narrow
   depth grid and relative-to-null endpoint.
5. Replicate the Gemma trajectory with a base/instruction-tuned pair and an
   additional size before attributing it to architecture or tuning.
6. Reserve a new untouched target bank and predeclare a primary endpoint and
   multiplicity family for T13-C.
7. Only after the representation and null controls pass, add generation-level
   behavioral endpoints.

## Compact evidence bindings

The eventual compact evidence index is
[`artifacts/emoji_steering_specificity_analysis_v0/README.md`](../artifacts/emoji_steering_specificity_analysis_v0/README.md).
The point-results closeout binds the present derived outputs as follows:

| Derived file | SHA-256 |
|---|---|
| `outcomes-v1-point.json` | `df0ddc58c8e98d6ca0c763cd7bc71821a10af4dad84cda5a92822abf8ecfd615` |
| `zero_hook_exact_primitives_bounded_js_v1.json` | `51a3beddbc5342aefea8be9f37ecdb7d870074056db3686ac220685c985c75de` |
| `analysis_receipt.json` | `c69f93706b20f0ddc70688aa1819376523049dd91dd2918c7c88d90c5dab7c58` |
| `F4_target_sensitivity.json` | `e7d8a1a3c4e781fced9ab2f8080f16d1b00d2516ffb2f8353c563df7a2b63ec9` |
| `F5_output_direction.json` | `e6eee30b93b61cd812f122385d78c53d82ac9cd7b30c76e0fb9daa8218d840cb` |
| `F6_source_geometry.json` | `f00f8a7b27976cf9d1cd51f97bee1c66a6d27cccb22b6cc3ffb3871fa9107916` |

Repository-level provenance is retained in the
[input closeout](../validation/emoji_steering_specificity_analysis_v0/glyphprobe-t13ea-closeout-7fedd40.json),
[historical v0 failure receipt](../validation/emoji_steering_specificity_analysis_v0/zero_gate_v0_failure_receipt.json),
and [point-results closeout](../validation/emoji_steering_specificity_analysis_v0/point_results_closeout_979533f.json).
The analyzer commit is `979533f64e9b25c48d56859a83ee4931ae47cde1`.
