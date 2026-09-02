# Post-review evidence results v0

[Japanese](POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md) | [Diagnostic plan](POST_REVIEW_EVIDENCE_PLAN_V0.md)

The review fixes were completed using retained T19/T20/T21 outputs on
2026-09-02. Computation used the Linux worker's CPU; model forwards, generation,
new item selection, and changes to the registered decisions were all zero.
Compact outputs were checked after transfer to the manuscript host. The two
retired historical target banks were not opened.

## T20: which basis was evaluated?

All 27 training histories and nine site-level seed choices were reconstructed.
Validation was measured every 50 steps. The first best checkpoint was retained
within each seed; the best seed then won, with ties resolved by the lowest seed.

| Primary residual site | Selected seed | Selected step | Recorded loss at selected iteration | Recorded step-600 loss |
| --- | ---: | ---: | ---: | ---: |
| Block 21 | 0 | 350 | 1.234684 | 0.647579 |
| Block 24 | 0 | 50 | 3.884068 | 1.254739 |

These are pre-update minibatch sufficiency losses; each saved basis follows
the corresponding update. The step-600 loss is a training-trajectory
diagnostic, not an evaluation of the selected basis on the full training set.
The manuscript now states both stages of selection. Both primary verdicts
remain **uncalibratable under the original rule**.

Evidence: `validation/post_review_evidence_v0/t20_checkpoint_selection.json`.

## T21: what changes inside the margin?

The new computation rehashed all 13 chunks and reconstructed all ten original
metric arrays exactly on the acquisition platform. Keyword and codepoint
top-1 arrays matched bit for bit. The maximum error in the itemwise additive
identity below was `4.17e-17`.

For each original contrast operator D, applied after same-slot neutral
subtraction and within-item averaging,

`D(margin) = D(own-keyword cosine) - D(maximum source-keyword cosine)`.

All 195 items, the original block-21 anchor, both distance-8 carriers, both
predetermined donors, and all five original contrasts are retained.

| Contrast | Own keyword | Maximum competitor | Margin | Donor keyword (diagnostic) |
| --- | ---: | ---: | ---: | ---: |
| Full-prefix calibration | +0.011980 | +0.003054 | +0.008926 | -0.003177 |
| Glyph decrement | +0.001046 | -0.002376 | +0.003422 | -0.005442 |
| Position-adjusted decrement | +0.002428 | +0.000103 | +0.002326 | -0.001913 |
| Glyph restoration | +0.008955 | +0.005238 | +0.003717 | +0.003039 |
| Position-adjusted restoration | +0.004402 | +0.002135 | +0.002267 | +0.000653 |

The positive own-keyword shifts in the two position-adjusted contrasts are
partially offset by increased maximum-competitor cosine. The absolute
decrement additionally reflects increased competition under donor injection.
This explains why the margin alone should not be called own-keyword similarity.
The donor keyword belongs to the source gallery; its cosine is a diagnostic,
not an additive third term. The maximum competitor can change identity.

This decomposition is **post-hoc and descriptive**, with no new significance
tests or confirmatory verdict. The existing simultaneous lower bounds apply
to the original margins, not the newly separated components. The original
zero mean absolute decrement/restoration top-1 effects remain unchanged.
The identity does not establish independently separable mediators, a complete
circuit, emoji specificity, or behavioral steering.

Evidence: `validation/t21_margin_decomposition_v0/` contains scalar rows,
the raw-state reconstruction receipt, and a separate compact identity check.

## T19: model-free replay and the matched null

The compact export preserves all nine configurations, both glyph kinds, both
components, all 24 primary contexts, exact prediction indices, and local
strata. Each original summary and prediction file matched its published
independent-validation checksum. The separate NumPy-only program reproduced:

- all 36 randomization tests, with 19,999 draws per test;
- all 36 descriptive intervals, with 20,000 bootstrap draws per interval;
- model intersection--union values, practical floors, and Holm decisions;
- four positive core configurations and partial-conjunction `p = 0.0027`.

The largest difference from the published numerical results was **zero**.
The compact predictions occupy 370,695 bytes and require no model assets.
They support statistical replay, not reconstruction of hidden states.

The uniform-guessing benchmark over an n-item gallery is `1/n`. In the matched
randomization, query i instead has null hit probability `1/size(stratum(i))`
when its prediction lies in the same stratum, and zero otherwise. Average this
probability over contexts and items to obtain the conditional keyword null
rate. The codepoint term is fixed throughout randomization. For Llama, the
matched keyword null rate is `0.066500`, versus uniform guessing `0.032258`.
The original tests already used the correct within-stratum permutation.

The replay also corrects a manuscript denominator typo: matched emoji counts
range from **31 to 51**, including Gemma's 51, rather than 31 to 41. The
prediction shapes, retained items, and tests themselves were correct.

| Configuration | Matched emoji |
| --- | ---: |
| Qwen2.5 0.5B | 35 |
| OLMo 2 1B | 31 |
| Qwen2.5 1.5B | 35 |
| SmolLM2 1.7B | 41 |
| Gemma 2 2B IT | 51 |
| Llama 3.2 3B | 31 |
| Qwen2.5 3B | 35 |
| Qwen2.5 7B | 35 |
| Mistral 7B Inst. | 38 |

Evidence: `validation/t19_lexical_alias_unicode_control_v0/compact_v0/`.

## Reproduce the compact checks

Run from the repository or extracted anonymous-artifact root:

```bash
python3 scripts/validate_t19_compact_predictions_v0.py \
  --compact validation/t19_lexical_alias_unicode_control_v0/compact_v0/predictions.json
python3 scripts/validate_t21_margin_decomposition_v0.py \
  --decomposition validation/t21_margin_decomposition_v0/decomposition.json \
  --original validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json
```

The existing T21 simultaneous-inference replay remains a separate check.
Raw-state reconstruction additionally requires the omitted saved arrays.
