# E2 Stage-A v2 Llama 3.2 3B MLX engineering validation result

[日本語](LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) · [Frozen protocol](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md) · [Roadmap](ROADMAP.md) · [Machine-readable receipt](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json)

## Status and decision

The v2 protocol and its one allowed technical change were frozen at commit
`dc84ac19e06ef7a0fd7dcd77fdce4b484b192e57`. The isolated
Transformers/MPS-to-MLX validation then completed, and the recorded receipt
reports `status: validation_failed` and `scientific_result: false`.

MLX is therefore **not qualified for the pinned E2 scientific cell**. This is a
negative engineering qualification, not a scientific result about glyphs or
emoji. No E2 scientific grid was run.

The v1 record remains intact. It was frozen at commit
`88685bd01ab115df323e9a324d49a659c66163c7`, completed its Transformers/MPS
phase, and stopped at the first MLX baseline export with:

```text
RuntimeError: Item size 2 for PEP 3118 buffer format string B does not match the dtype B item size 1.
```

V1 produced no receipt and no scientific outcome; its
[failure record](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json)
is retained. The sole specified backend
change affecting numerical semantics in v2 was the export bridge: native MLX
BF16 arrays are cast to `mx.float32` immediately before NumPy export. Model
execution remains BF16.

## Result at a glance

| Frozen gate family | Passed | Result |
|---|---:|---|
| All parity checks | 33 / 60 | failed |
| Token IDs, repeated argmax, and determinism | 10 / 10 | passed |
| Baseline activation and logits | 6 / 10 | failed |
| Exact zero-hook behavior | 10 / 10 | passed |
| Changed activation and logits | 7 / 10 | failed |
| Intervention deltas | 0 / 10 | failed |
| Within-backend intervention fidelity | 0 / 10 | failed |
| Machine-local speed gate | false | failed |

The aggregate status follows the frozen all-gates rule. Passing subsets do not
override a failed parity family or the failed speed gate.

## Completed execution and identity checks

The receipt binds the run to `mlx-community/Llama-3.2-3B-bf16` revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`, native BF16, `resid_post`, layers
5 and 11, and the sealed engineering prompts and intervention vector. The
Transformers and MLX phases completed sequentially in isolated subprocesses,
both with return code 0; the two models were never resident at the same time.

Pinned model metadata and the complete nine-file artifact manifest matched
across backends. The manifest covers 6,434,705,789 bytes and has SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
Backend-specific stable-identity hashes are not asserted to be equal.

The Stage-A process did not access the study target banks, confirmatory outcomes,
or causal outcomes.

## What matched

All ten tokenization and determinism checks passed. Token IDs matched across
backends, repeated token IDs and argmax outputs were identical, and the maximum
absolute repeated-logit difference within each backend was 0. All ten exact
zero-hook checks also passed.

The activation part of every cross-backend intervention-delta comparison passed:

| Activation-delta metric | Range across 10 cells | Frozen threshold |
|---|---:|---:|
| NRMSE | 0.014057–0.018356 | ≤ 0.02 |
| Cosine similarity | 0.999832–0.999901 | ≥ 0.999 |
| RMS ratio | 0.999625–1.000526 | 0.98–1.02 |

These checks establish a narrow numerical match for the activation delta under
the sealed engineering probes. They do not establish the complete parity gate.

## Where parity failed

The corresponding logit deltas failed clearly:

| Logit-delta metric | Range across 10 cells | Frozen threshold |
|---|---:|---:|
| NRMSE | 0.580523–1.402939 | ≤ 0.05 |
| Cosine similarity | -0.097707–0.816940 | ≥ 0.99 |
| RMS ratio | 0.882575–1.408769 | 0.95–1.05 |

Because the frozen delta gate requires both activation and logit components to
pass, the intervention-delta result is 0 / 10 despite the 10 / 10 activation
subcomponent result.

The within-backend intervention-fidelity check also failed in all ten cells. Its
activation NRMSE was 0.030175–0.034029 for Transformers/MPS and
0.030222–0.034148 for MLX, above the fixed 0.01 threshold. Cosine similarity was
approximately 0.9994 and RMS ratio remained approximately 1 for both backends.
The receipt localizes neither failure to a scientific mechanism nor to a single
implementation cause. The baseline and changed-output families also remained
incomplete at 6 / 10 and 7 / 10.

## Speed result

The synchronized benchmark used ten prompt-layer cells, two warmups and ten
measured repeats per cell, for 100 measured forwards per backend.

| Backend | Aggregate median latency |
|---|---:|
| Transformers/MPS | 132.127833 ms |
| MLX | 230.138000 ms |

MLX took `1.741782892` times the Transformers/MPS median latency. The receipt's
recorded speedup is `0.574124367x`, and the speed gate is `false`; it required
MLX latency to be at most 95% of the Transformers/MPS latency. All ten per-cell
MLX medians were slower. These are machine-, load-, software-, model-, and
measurement-boundary-specific measurements, not a general MLX performance
claim.

## Scientific boundary

This receipt supports only the following conclusion: the frozen Llama 3.2 3B
BF16 MLX route did not satisfy the specified backend-parity and speed gates.

It provides no:

- E2 scientific-grid result;
- emoji-family or semantic result;
- causal or circuit result;
- cross-model replication;
- evidence for a model-scale effect; or
- Phase I paper gate.

The failed validation must not be converted into a scientific negative result.
It tested an engineering route, not the study hypothesis.

## Next decision

Two non-equivalent paths remain, and neither has been selected:

1. create a separate Transformers/MPS scientific freeze for the E2 transport
   study; or
2. create a new MLX v3 diagnostic and optimization freeze, then rerun a newly
   sealed engineering validation before any scientific outcome is accessed.

This document makes no recommendation between them. The v2 thresholds remain
fixed; they will not be relaxed or retuned after seeing the result. The choice is
pending the research owner's decision.

## Provenance

- frozen v2 commit: `dc84ac19e06ef7a0fd7dcd77fdce4b484b192e57`;
- protocol ID: `glyphprobe-e2-llama32-3b-mlx-engineering-validation-v2`;
- receipt status: `validation_failed`;
- receipt SHA-256: `4ede081c129d9a4733b661dcab7452e5a0ae4e8e90c6bc5890817d500cca4468`;
- v1 failure record: [`attempt_01_failure.json`](../validation/mlx_llama32_3b_bf16_parity/attempt_01_failure.json);
- receipt: [`validation/mlx_llama32_3b_bf16_parity_v2/receipt.json`](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).
