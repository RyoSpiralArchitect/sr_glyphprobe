# E2 Stage-A3 protocol: Llama 3.2 3B MLX runtime-dtype numeric screen v1

[日本語](LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) · [Stage-A v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [Stage-A v2 protocol](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md)

Protocol ID: `glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`

## Status and purpose

Effective status before the public freeze: `freeze_pending`. Formal screen
status: `not_run`. This protocol authorizes no model forward until a public
commit binds this English/Japanese pair to the exact implementation, tests,
input identities, candidate definitions, selection rule, receipt schema, and
no-overwrite destination.

After that commit, the protocol status becomes
`frozen_by_public_commit_containing_protocol_implementation_and_tests`, and the
screen may run once at its versioned destination.

Stage A3 is an engineering-only candidate screen. It asks whether either of two
runtime compute dtypes, `float16` or `float32`, is numerically faithful within
each backend and faster in MLX than in Transformers/MPS on one fixed local
workload. The receipt's `selection.selected_runtime_dtype` is therefore
`float16`, `float32`, or `null`; the associated `selection.decision` records why.

A selected candidate may be carried into the design and public freeze of a
separate, full v3 parity validator. Selection does **not** qualify MLX, authorize
an E2 scientific grid, or revise any existing validation result.

## V2 remains failed

The frozen Stage-A v2 result remains `status: validation_failed` and
`scientific_result: false`. Its 33 / 60 parity result and failed speed gate are
not reopened, rescored, or reclassified by this protocol. Native-BF16 execution
is not a Stage-A3 candidate or fallback.

See the [complete v2 result](LLAMA32_3B_MLX_VALIDATION_RESULTS.md), the
[frozen v2 protocol](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md), and the
[v2 receipt](../validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).

After v2, unsealed informal diagnostics suggested that its within-backend
intervention-fidelity failure was localized to rounding of the small BF16
addition in both backends, rather than to a hook that failed to apply the
intervention. This observation is diagnostic guidance only. It was not produced
by a frozen protocol, does not prove that no hook defect exists, does not select
a dtype, and is not a scientific result. Any partial FP16 or FP32 diagnostic
measurement made before the Stage-A3 freeze is likewise excluded from the
formal screen result.

## Fixed candidate family

Both candidates start from the same pinned BF16 weight artifact. They differ
only in the explicit runtime compute dtype used by both Transformers/MPS and
MLX.

| Candidate ID | Stored weight artifact | Transformers runtime compute | MLX runtime compute |
|---|---|---|---|
| `float16` | pinned BF16 artifact | FP16 | FP16 |
| `float32` | pinned BF16 artifact | FP32 | FP32 |

The artifact is `mlx-community/Llama-3.2-3B-bf16` at immutable revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`. Its fixed nine-file inventory
contains 6,434,705,789 bytes and has manifest SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.

Each backend must load that exact artifact, apply the candidate dtype explicitly
before the first qualifying forward, and record the loader-resolved dtype and
model-parameter dtype element counts. `auto`,
mixed-dtype fallback, quantization, replacement artifacts, and silently retained
BF16 parameters are prohibited. The total parameter count must remain exactly
3,212,749,824 in both backends. Every model parameter must resolve to the candidate dtype;
the receipt records dtype counts and parameter counts rather than inferring them
from a loader argument. Non-parameter buffers, including precision-sensitive
auxiliary arrays such as RoPE buffers, are outside this dtype claim and are
identified as unaudited by this gate.

The expected architecture remains 28 decoder layers, hidden width 3,072, and
vocabulary size 128,256. The model is the base model, with no chat template or
system prompt. Tokenization uses `add_special_tokens: false`. Capture and
intervention use `resid_post` at `last_nonpad`, at fixed zero-based layers 5 and
11.

## Fixed engineering inputs

Stage A3 reuses the exact five engineering prompts from v2 and no others.

| ID | Exact UTF-8 prompt |
|---|---|
| `prompt_00` | `🌒` |
| `prompt_01` | `🐑` |
| `prompt_02` | `Mark: 🤑\nAnchor:` |
| `prompt_03` | `Continue briefly: The scientist opened the notebook and` |
| `prompt_04` | `Write a concise two-sentence explanation of why a careful scientist records every calibration setting before comparing experimental interventions.` |

In `prompt_02`, `\n` denotes one literal newline in the decoded string. The
implementation freezes and records each prompt's UTF-8 bytes and SHA-256,
token IDs, token count, and last-nonpadding position. A prompt, byte, tokenizer
setting, position, or layer may not be replaced after the public freeze.

The matrix contains ten prompt-layer cells per candidate: five prompts crossed
with layers 5 and 11.

## Candidate-specific fixed interventions

Each candidate uses the v2 deterministic direction and 5%-RMS construction,
but derives its scale from that candidate's Transformers/MPS baseline. Let
`c` be `float16` or `float32`, and let `a^{T,c}_{p,l}` be its reference baseline
activation for prompt `p` and layer `l`:

\[
u_0=\operatorname{linspace}(-0.05,0.05,3072;\ \mathrm{float32}),\qquad
u=u_0-\operatorname{mean}(u_0;\ \mathrm{float32}),\qquad
\hat u=u/\operatorname{RMS}(u),
\]

\[
v^{c}_{p,l}=0.05\,\operatorname{RMS}(a^{T,c}_{p,l})\,\hat u.
\]

For each candidate and cell, Transformers/MPS serializes one all-zero vector
and the float32 bytes of `v^{c}_{p,l}`. MLX must replay those exact bytes and
verify their SHA-256 before injection. MLX must not reconstruct, rescale, or
replace the vector from its own baseline. The receipt records the construction,
reference RMS, scale, vector RMS, width, dtype, and hash for every candidate
cell.

The observed activation delta is measured at the intervention layer and
`last_nonpad`, after export to the common comparison representation. The
specified vector remains the reference for the separate within-backend fidelity
checks.

## Process isolation and timing

Candidate order is fixed as `float16`, then `float32`. Within each candidate,
Transformers/MPS runs first and exits before MLX loads. No two full model
instances may be resident simultaneously, and no model instance may be reused
across candidates.

For each candidate:

1. Transformers/MPS verifies artifact and architecture identity, tokenizes the
   five prompts, performs the fixed determinism and zero-vector checks,
   constructs the ten candidate-specific vectors, evaluates fidelity, records
   timing samples, writes a staged payload, and exits.
2. MLX independently verifies the same identities, replays the fixed tokens and
   vectors, performs the same exact checks and fidelity measurement, records
   timing samples, writes a staged payload, and exits.
3. A model-free comparison step validates both staged payloads, evaluates the
   frozen eligibility and selection rules, and constructs the final receipt.

Every prompt-layer-backend cell receives two unrecorded warm-up forwards and ten
measured forwards. Each candidate therefore contributes 100 measured forwards
per backend. The timing boundary is unchanged from v2: tokenization,
capture/intervention, device evaluation, synchronization, and transfer of all
reported arrays to NumPy are included. Model loading is recorded separately and
excluded from the speed gate.

This sequential, non-interleaved benchmark is machine-, software-, load-,
temperature-, and order-specific. It is not a portable comparison of MLX and
MPS.

## Candidate eligibility gates

Eligibility is evaluated independently for `float16` and `float32`. Every gate
must pass in every one of that candidate's ten prompt-layer cells. There is no
averaging away a failed cell.

Operational prerequisites also fail closed: the complete artifact and
architecture identities must match, both worker phases must finish and be
recorded, all required arrays and metrics must be finite, and no undeclared
dtype or fallback path may occur.

| Gate | Frozen criterion |
|---|---|
| Runtime dtype and parameter audit | loader-resolved dtype equals the candidate; exactly 3,212,749,824 parameters in each backend; every model parameter resolves to the candidate dtype; recorded dtype counts agree with the loaded models |
| Prompt and token identity | prompt SHA-256, UTF-8 bytes, byte count, and last-nonpadding position match across backends; token IDs are exactly equal |
| Within-backend determinism | repeated token IDs and argmax outputs are exactly equal in each backend |
| Zero-vector integrity | maximum absolute activation and logit change <= 1e-7, separately in each backend |
| Transformers/MPS intervention fidelity | observed activation delta versus specified vector: NRMSE <= 0.01 and cosine >= 0.999 |
| MLX intervention fidelity | observed activation delta versus specified vector: NRMSE <= 0.01 and cosine >= 0.999 |
| Machine-local speed | MLX aggregate median latency <= 0.95 times the candidate's Transformers/MPS aggregate median latency |

For observed activation delta `d` and specified vector `v`, fidelity uses:

\[
\operatorname{NRMSE}(v,d)=
\frac{\sqrt{\operatorname{mean}((d-v)^2)}}
{\max(\operatorname{RMS}(v),10^{-12})}.
\]

Cosine is computed on flattened float64 comparison arrays. The speed gate pools
the 100 measured samples within one candidate and backend. If `m_{T,c}` and
`m_{M,c}` are the aggregate Transformers/MPS and MLX medians, candidate `c`
passes speed only when

\[
m_{M,c}\leq0.95m_{T,c}.
\]

The receipt records the maximum absolute repeated-logit difference for each
backend, but that value is diagnostic and not a Stage-A3 gate. The screen does
not run cross-backend baseline, changed-output, activation-delta, or logit-delta
parity gates. Those checks remain unperformed until a separately frozen full v3
validator. They must not be inferred from fidelity or added to the Stage-A3
selection after output is visible.

## Frozen selection rule

Let `E16` and `E32` denote eligibility after all gates above.

1. If neither candidate is eligible, set
   `selection.selected_runtime_dtype: null` and
   `selection.decision: no_go_no_eligible_numeric_candidate`.
2. If exactly one candidate is eligible, select that candidate.
3. If both are eligible, compare their MLX aggregate median latencies.
   - If the relative difference
     `abs(m_M,16 - m_M,32) / min(m_M,16, m_M,32)` is at most 0.01, select
     `float32`.
   - Otherwise, select the candidate with the lower MLX aggregate median.

The implementation-frozen `selection.decision` values are:

- `no_go_no_eligible_numeric_candidate`;
- `single_eligible_candidate`;
- `both_eligible_tie_select_fp32`; and
- `both_eligible_select_lower_mlx_median`.

The no-eligible-candidate decision is a complete, valid engineering-screen
outcome. It is not an execution error and must remain publishable. A worker error, non-finite value, identity
mismatch, or undeclared dtype makes that candidate ineligible; it does not
authorize altered inputs or an automatic rerun.

## No fallback and no threshold tuning

There is no candidate fallback inside a worker, candidate, screen, or later v3
validation. In particular:

- `float16` may not retry in `float32`, and `float32` may not retry in
  `float16`;
- neither candidate may fall back to BF16, `auto`, CPU, another model artifact,
  another prompt, or another layer;
- if a selected candidate later fails the separately frozen v3 validator, the
  other Stage-A3 candidate is not promoted automatically; and
- a new attempt after any protocol or implementation change requires a new
  version, public freeze, and receipt destination.

No threshold may be relaxed, rounded in a candidate's favor, or retuned after
formal output is inspected. Informal diagnostics cannot be promoted into the
formal receipt or used to remove a failed cell. Errors and negative candidates
remain visible.

## Receipt, schema, and atomic publication

The one final receipt path is:

`validation/mlx_llama32_3b_numeric_screen_v1/receipt.json`

It contains both candidate records and the deterministic selection. The frozen
minimum contract is:

- `schema_version: 1`;
- `protocol_id: glyphprobe-e2-llama32-3b-mlx-numeric-screen-v1`;
- `status: engineering_screen_complete` after both candidate attempts and the
  model-free selection step are recorded;
- `scientific_result: false`;
- `selection_is_not_scientific_authorization: true`;
- `selection.selected_runtime_dtype: null | float16 | float32` and a
  `selection.decision` reason code fixed by the implementation;
- candidate-specific `eligible` values, resolved runtime dtypes, artifact and
  implementation identities, and per-candidate `process_lifecycle` records with
  backend, dtype, return code, and wall time, including worker failures;
- all ten `benchmark.cells` per candidate with the raw ten `samples_ms` values
  per backend and their summaries, plus exact gates, fidelity metrics, prompt
  UTF-8 hex/byte counts, last-nonpadding positions, and failure evidence;
- the validator SHA-256, complete `src/glyphprobe` source receipt, dependency
  and machine environment, fixed inputs and hashes,
  thresholds, timing boundary, process order, and data-scope declarations.

The implementation serializes the complete receipt into a same-directory
temporary file, flushes it, and atomically publishes it with a no-overwrite
link only if the final destination does not exist. It must refuse to truncate,
replace, merge with, or overwrite an existing receipt. Generated receipt content is never edited by hand. A candidate worker
failure is recorded in the combined receipt when the orchestrator can still
complete the frozen selection; an orchestrator failure before valid atomic
publication leaves no final receipt and authorizes no conclusion.

The validator path is
`scripts/diagnose_mlx_llama32_3b_numeric_cells_v1.py`. The public freeze binds
that file and its tests to this bilingual protocol through Git history, the
validator SHA-256, the complete source receipt, and the embedded validation
configuration hash. The formal command is:

```bash
python scripts/diagnose_mlx_llama32_3b_numeric_cells_v1.py \
  --output validation/mlx_llama32_3b_numeric_screen_v1/receipt.json
```

If implementation uses a different protocol ID, candidate ID, field, final
path, or command, both protocol documents must be updated and publicly refrozen
before any formal forward. Documentation and implementation may not disagree at
execution time.

## Data isolation and claim boundary

Stage A3 may access only the pinned model artifact, tokenizer files, the five
engineering prompts above, and implementation/runtime metadata. It must not
read, list, hash, tokenize, score, model-forward, or analyze P2, C1, prestage
targets, source-wrapper banks, E1 scientific grids, or any other study bank or
scientific outcome.

The screen produces no emoji-family endpoint, semantic result, causal result,
circuit result, cross-model replication, model-scale comparison, or paper gate.
The public glyphs in three engineering prompts exercise tokenizer and adapter
surfaces only.

The strongest permitted claim is:

> Under one publicly frozen, machine-local engineering screen, the selected
> runtime dtype met the fixed within-backend fidelity, exactness, and speed
> criteria; or no candidate met them.

Even that statement requires the atomic receipt. Before its publication, the
only valid statement is that the screen is frozen or pending, according to the
public commit state.

## Handoff to formal v3 validation

A `float16` or `float32` selection authorizes only preparation and public freeze
of a separate full v3 backend-parity validator for that one candidate. The v3
protocol must independently freeze and evaluate its complete baseline,
changed-output, activation-delta, logit-delta, zero, fidelity, identity,
determinism, and speed gates.

The Stage-A3 receipt cannot serve as a v3 parity receipt. It does not enable
scientific activation intervention or authorize the E2 grid. Scientific work
would require a passing formal v3 receipt and a further public freeze of the E2
scientific inputs, endpoints, analysis, and claim boundary.
`selection.selected_runtime_dtype: null` ends this screen
without a v3 candidate.
