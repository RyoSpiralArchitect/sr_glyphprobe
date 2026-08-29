# T13-EA Zero-Gate Numerical Amendment v1

This document freezes a narrow numerical amendment to the T13-EA zero-control
gate. It does not revise the scientific analysis plan.

## Why an amendment exists

The original v0 analyzer required exact zero for four scalar endpoints,
including Jensen-Shannon (JS) divergence. That attempt failed closed on the JS
field before any nonzero scientific value was opened. It wrote no analysis
output. The failure remains recorded as a negative procedural result in
`validation/emoji_steering_specificity_analysis_v0/zero_gate_v0_failure_receipt.json`.

Only the identity of the failing field was used to prepare this amendment. The
exact live residual magnitude was not inspected or used to select a threshold.

## What changes

The v1 gate continues to require exact equality for every primitive no-op:

- KL divergence, total variation, and logit-delta RMS are exactly zero.
- Baseline and intervened entropy are exactly equal.
- Baseline and intervened argmax IDs are exactly equal and in range.
- `argmax_flip` is false.
- Positive-tail values, negative-tail values, and CountSketch are exactly zero.
- Positive-tail and negative-tail token IDs are valid vocabulary IDs.

JS divergence is treated differently because it is derived through the
float32 `log_softmax -> exp -> mean -> log` path. Even when both logits are
identical, the `log(exp(logp))` round trip need not reproduce `logp` bit for
bit. The amended rule therefore requires a finite, two-sided residual with

```text
abs(js_divergence) <= 8 * finfo(float32).eps
                   = 9.5367431640625e-07
```

This is an algorithm-derived float32 allowance fixed before inspection of the
exact failed live residual. It is not an empirical tolerance fitted to the run.
The JS value must be reported as a derived float32 round-trip residual, never
as exact zero.

## What does not change

The sealed run, external closeout, six output families, estimands, resampling
contract, controls, and interpretation limits remain unchanged. The analyzer
must still:

1. re-audit the external closeout in the same process;
2. open only the zero-control ledgers and arrays first;
3. pass every exact primitive check and the bounded JS check;
4. authorize nonzero scientific reads only after the full gate passes; and
5. refuse to overwrite an existing analysis output.

Any failure remains fail-closed.

## Claim boundary

Passing v1 means only that the zero-hook control is consistent with an exact
primitive no-op and the prospectively frozen float32 JS residual allowance. It
does not establish a scientific effect, repair a scientific null, or weaken any
T13-EA interpretation limit.

The original v0 failure and the v1 result must be reported separately. A later
scientific result cannot erase the failed exact-equality gate.

## Freeze boundary

The amendment manifest is
`data/manifests/emoji_steering_specificity_zero_gate_amendment_v1.json`. Its
exact roster binds:

- the original v0 analysis manifest;
- the verified external closeout receipt;
- the v0 failure receipt;
- this configuration and both language versions of this document;
- the v1 geometry and outcome analyzer wrappers and their tests; and
- the amendment auditor and its tests.

The manifest is generated only after all roster files have been integrated.
