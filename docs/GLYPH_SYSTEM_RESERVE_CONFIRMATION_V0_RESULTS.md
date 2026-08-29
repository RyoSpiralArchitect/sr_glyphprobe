# Glyph-System Reserve Confirmation v0 results (T12)

[日本語](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.ja.md) · [Frozen protocol](GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0.md) · [Compact evidence](../artifacts/glyph_system_reserve_confirmation_v0/README.md) · [T11 discovery atlas](GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [Next-question map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md)

Status: **completed one-shot confirmation; neither registered hypothesis confirmed**.

T12 opened the complete, previously unforwarded 96-item ZWJ and 64-item
regional-flag reserves once. It tested the two discovery-informed hypotheses
frozen before acquisition across nine model/tokenizer cells, two carriers, and
four distances. `H_ZWJ_FUSION` was not confirmed. `H_REGIONAL_DUAL` was not
confirmed. No endpoint, practical floor, model gate, or multiplicity rule was
changed after outcomes became available.

The useful negative result is sharper than “nothing happened.” Regional
presentation/fusion had a weak directionally consistent signal—eight of nine
model summaries were positive and its unadjusted component p-value was
`0.03538`—but its global statistic was only `0.002767`, far below the frozen
`0.02` practical floor. Regional component tracking was smaller and did not
reject. ZWJ presentation/fusion was close to the unadjusted statistical
boundary (`p = 0.05496`) but its statistic was `0.000369`, also far below its
`0.005` floor. Direction alone therefore could not rescue either registered
hypothesis.

This result does not show that models lack emoji representations. It shows that
the specific T11 decomposition candidates did not reproduce at the
prespecified magnitude and cross-model consistency in their untouched reserve.

## Acquisition and provenance

The corrected freeze is commit
`ab64488dc4bd28510c353f4370cda5546bb34750`. Its manifest SHA-256 is
`38046552a26bef0eb6cdab3222f58041707616028fe89c0eb5104a84f0943738`.
The tokenizer/artifact preflight loaded no model weights and made zero reserve
forwards. Its aggregate SHA-256 is
`3a51837c6c6a149b88e05db2528b5ebd2437d50c89e8ffdcfaaee1a343bc8ee1`.

All nine frozen roles completed:

- Llama 3.2 3B base;
- Qwen 2.5 base at 0.5B, 1.5B, 3B, and 7B;
- OLMo 2 1B base;
- Gemma 2 2B instruction-tuned;
- SmolLM2 1.7B base; and
- Mistral 7B Instruct v0.3.

Each role acquired all 160 items in ten shards, with 1,088 unique model
forwards and 4,352 FP32 returned-final readout vectors. The joint acquisition
therefore contains 90 complete shards, 9,792 model forwards, and 39,168
vectors. It used zero interventions and zero generations. Raw activations
remain outside Git and SpiralShare.

The endpoint was exactly `output.hidden_states[-1]`, interpreted as the model
API's returned final hidden state after final normalization when the
implementation provides it. T12 stored neither a raw-last-block endpoint nor
intermediate depths, so no alternative endpoint can rescue the decision.

## Tokenization controls

Every primary wrong-label comparison matched the exact target-token length
inside the same glyph system and tokenizer. The minimum required-control
coverage across the registered cells was `0.979167`, above the frozen `0.75`
gate. The stricter sensitivity also matched the first target token. Its minimum
coverage was `0.729167`, above the frozen `0.70` gate.

The strict-prefix sensitivity was directionally positive for all nine ZWJ
model summaries, eight of nine regional presentation/fusion summaries, and six
of nine regional component summaries. It was a required gate but, by design,
could not rescue a failed primary control, practical floor, heterogeneity rule,
or Holm decision.

## Registered decisions

The primary statistic is the median of 72 model × context item medians. Each
elementary test used 49,999 shared within-item glyph/decomposition swaps. The
regional hypothesis is an intersection-union conjunction, so its p-value is
the maximum of its two component p-values. Holm correction covers the two
registered hypotheses at familywise alpha `0.05`.

| Registered component | Global statistic | Positive cells | Positive model summaries | Models at practical floor | Raw p |
|---|---:|---:|---:|---:|---:|
| ZWJ presentation/fusion | 0.000369 | 50/72 | 6/9 | 0/9 at 0.005 | 0.05496 |
| Regional presentation/fusion | 0.002767 | 53/72 | 8/9 | 0/9 at 0.02 | 0.03538 |
| Regional component tracking | 0.000666 | 41/72 | 5/9 | 0/9 at 0.02 | 0.12950 |

| Registered hypothesis | Combination | Raw hypothesis p | Holm-adjusted p | Confirmed |
|---|---|---:|---:|---|
| `H_ZWJ_FUSION` | one elementary test | 0.05496 | 0.10992 | no |
| `H_REGIONAL_DUAL` | max of both regional component p-values | 0.12950 | 0.12950 | no |

All three elementary tests failed the global practical floor and the
requirement that at least six of nine model summaries reach that floor. None
had a materially opposed model at its negative floor, and all passed their
strict-prefix direction gates. The failure is therefore a combination of
small magnitude, insufficient model-level practical support, and—for ZWJ and
regional component tracking—no unadjusted rejection. It is not a sign-reversal
result.

## What changed from discovery to confirmation

The comparable T11 discovery medians were `0.0142` for ZWJ
presentation/fusion, `0.0668` for regional presentation/fusion, and `0.0441`
for regional component tracking. In T12 reserve confirmation they were
`0.000369`, `0.002767`, and `0.000666`. These descriptive differences are not
a separate discovery-versus-reserve hypothesis test, but they show that the
T11 candidates did not transport at their discovery magnitude.

This is exactly the selection pressure a one-shot reserve was meant to expose.
T11 remains a useful exploratory atlas, and T12 now prevents its strongest
decomposition patterns from being promoted as confirmed cross-model
phenomena.

## Independent validation and public evidence

The independent validator does not import the T12 acquisition/analyzer module.
It rehashed the freeze, preflight, nine run receipts, and nine shard indexes. It
then reconstructed all 432 stored cell medians, reran the three 49,999-draw
randomization tests, and recomputed every practical, heterogeneity,
strict-prefix, intersection-union, and Holm decision. There were zero
mismatches.

The validation is still not an independent model replication. The compact
bundle omits raw FP32 activation arrays, so it binds but does not reconstruct
the activation-to-item-contrast step. Its rating is therefore “share with
caveats.”

Validate the Git-resident evidence with:

```bash
python scripts/validate_glyph_system_reserve_confirmation_v0_result.py \
  validate-public-bundle \
  --bundle artifacts/glyph_system_reserve_confirmation_v0
```

The primary result SHA-256 is
`1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6`.

## Claim boundary and next question

T12 closes only this reserve question. It does not establish emoji meaning,
understanding, causality, a mechanism, behavioral steering, tokenizer
independence, a scale law, instruction-tuning effects, architecture or model
generality, or independent replication. It does not change or rescue T10.

The clean next move is not to search these reserve outcomes for a favorable
layer or endpoint. It is to return to the broader original question: does an
emoji-derived intervention produce any effect that survives meaning-matched
word directions, tokenization-matched non-emoji Unicode, rare-token controls,
and norm-matched random directions? The
[T13 decision map](EMOJI_STEERING_SPECIFICITY_ATLAS_V0.md) keeps that future
work exploratory until its target banks, intervention endpoints, and
multiplicity families are separately frozen.
