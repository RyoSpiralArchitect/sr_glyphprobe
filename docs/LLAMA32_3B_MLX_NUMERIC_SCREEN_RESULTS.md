# E2 Stage-A3 Llama 3.2 3B MLX runtime-dtype numeric screen v1 result

[日本語](LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) · [Frozen protocol](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) · [Stage-A v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [Roadmap](ROADMAP.md) · [Machine-readable receipt](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json)

## Status and decision

The Stage-A3 protocol was publicly frozen at commit
`1f8a8d09d3f519add9bf4ef5a65c1c41256c67ae`. The formal engineering-only
screen then completed with:

- `status: engineering_screen_complete`;
- `scientific_result: false`;
- `selection.selected_runtime_dtype: null`; and
- `selection.decision: no_go_no_eligible_numeric_candidate`.

Neither fixed runtime-dtype candidate passed every prespecified gate. Both
passed artifact and runtime-dtype identity, prompt/token identity,
within-backend determinism, zero-vector integrity, and intervention fidelity.
Both failed only the machine-local speed gate. No threshold was relaxed, no
fallback candidate was promoted, and no automatic rerun was used.

The Stage-A v2 result is unchanged: its receipt remains
`status: validation_failed` and `scientific_result: false`. Stage A3 does not
rewrite or supersede that failure.

## Result at a glance

| Candidate | Tokens and determinism | Zero vector | Fidelity | Runtime dtype | Speed | Eligible |
|---|---:|---:|---:|---:|---:|---:|
| `float16` | passed | passed | passed | passed | failed | false |
| `float32` | passed | passed | passed | passed | failed | false |

The frozen rule required every gate to pass. A candidate that misses the speed
gate is ineligible even when every numerical-integrity gate passes.

## Fixed scope and completed execution

Both candidates loaded the same BF16-weight artifact,
`mlx-community/Llama-3.2-3B-bf16` at revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`. The nine-file artifact manifest
covers 6,434,705,789 bytes and has SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
Only runtime compute dtype differed: `float16` or `float32`.

For both backends and both candidates, the loader-resolved dtype matched the
requested candidate, and all 3,212,749,824 model parameters were recorded in
that dtype. This audit does not extend its dtype claim to non-parameter buffers.

The fixed workload was the same five v2 engineering prompts crossed with
`resid_post` layers 5 and 11, giving ten cells per candidate. Each cell used two
warmups and ten measured forwards per backend. The four workers ran strictly
sequentially in isolated subprocesses and all returned 0; no two full models
were resident simultaneously. Artifact, parameter, and prompt identities
matched exactly.

No study target bank, P2 outcome, C1 outcome, confirmatory outcome, or causal
outcome was accessed.

## Numerical-integrity gates

Both candidates passed exact cross-backend token identity, exact repeated token
and argmax checks within each backend, the unchanged v2 zero-vector threshold
of maximum absolute activation and logit change `<= 1e-7`, and the separate
within-backend intervention-fidelity gates.

| Candidate | Backend | Fidelity NRMSE across 10 cells | Frozen NRMSE threshold | Cosine gate |
|---|---|---:|---:|---:|
| `float16` | Transformers/MPS | 0.00383147–0.00436931 | <= 0.01 | passed (>= 0.999) |
| `float16` | MLX | 0.00383590–0.00435258 | <= 0.01 | passed (>= 0.999) |
| `float32` | Transformers/MPS | 4.633e-7–5.327e-7 | <= 0.01 | passed (>= 0.999) |
| `float32` | MLX | 4.627e-7–5.336e-7 | <= 0.01 | passed (>= 0.999) |

These results show that the specified addition was reproduced faithfully inside
each backend for these engineering probes. They do **not** establish complete
Transformers/MPS-to-MLX parity.

Stage A3 did not run the full cross-backend baseline, changed-output,
activation-delta, or logit-delta parity families. Those checks would have
required a separately frozen full v3 validator. Consequently, the strong FP32
fidelity values must not be described as a qualified FP32 MLX route.

## Machine-local speed gate

The speed gate required the MLX aggregate median to be no greater than 95% of
the corresponding Transformers/MPS median.

| Candidate | Transformers/MPS median | MLX median | MLX / MPS | Per-cell MLX medians slower | Speed gate |
|---|---:|---:|---:|---:|---:|
| `float16` | 165.0765625 ms | 322.9998125 ms | 1.956666698 | 10 / 10 | failed |
| `float32` | 465.013771 ms | 458.619459 ms | 0.986249198 | 4 / 10 | failed |

FP16 was substantially slower on MLX in this run. FP32's aggregate MLX median
was approximately 1.375% lower than the Transformers/MPS median, but the frozen
gate required at least a 5% reduction. Near parity is not a pass under that
rule.

These timings are bound to the recorded machine, software stack, load,
temperature, process order, model, prompts, and measurement boundary. They are
not a general comparison of MLX and MPS.

## Selection and claim boundary

Because neither candidate was eligible, the deterministic selection rule
returned `no_go_no_eligible_numeric_candidate`. The result authorizes none of
the following:

- selection of FP16 or FP32 for a formal v3 validator;
- fallback from one candidate to the other;
- a formal full v3 parity validation;
- an MLX E2 scientific grid;
- a Llama glyph, emoji-family, semantic, causal, circuit, or cross-model result;
- a scientific negative result; or
- completion of a Phase I paper gate.

This is a completed negative engineering-screen decision, not a negative study
outcome. The receipt's `scientific_result: false` and
`selection_is_not_scientific_authorization: true` fields make that boundary
machine-readable.

## Next decision

No formal v3 validator is frozen or authorized, and no MLX scientific grid will
follow from this screen. The realistic choices now require a new owner decision:

1. freeze a separate Transformers/MPS scientific route; or
2. design a distinct future engineering program for MLX under a new public
   protocol and version.

The second path is not a retry of this screen. It cannot relax the observed
thresholds, reuse an ineligible candidate as a fallback, or access scientific
outcomes while redesigning the engineering route.

## Provenance

- public protocol freeze: `1f8a8d09d3f519add9bf4ef5a65c1c41256c67ae`;
- protocol ID: `glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`;
- receipt status: `engineering_screen_complete`;
- selection decision: `no_go_no_eligible_numeric_candidate`;
- receipt SHA-256: `02a3a0f60a1211da48ec60adce8df4fa4a44187bccb0cc610386f63df885a518`;
- frozen protocol: [`LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md`](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md);
- receipt: [`validation/mlx_llama32_3b_numeric_screen_v1/receipt.json`](../validation/mlx_llama32_3b_numeric_screen_v1/receipt.json).
