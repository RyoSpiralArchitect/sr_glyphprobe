# E2 Stage-A protocol: Llama 3.2 3B MLX engineering validation

[日本語](LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) · [Research roadmap](ROADMAP.md) · [E1 exploratory protocol](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md)

Protocol ID: `glyphprobe-e2-llama32-3b-mlx-engineering-validation-v1`

## Status and purpose

Protocol status after publication:
`frozen_by_public_commit_containing_this_protocol`. Execution status:
`validation_pending`. Stage: engineering validation.

The frozen status becomes effective only when the public commit containing this
protocol and its executable validator is available. Before that publication,
the effective status is `freeze_pending`, and no validation forward is
authorized.

This protocol freezes the backend-parity and machine-local speed gate for a
prospective E2 cross-model transport side track. It asks only whether one exact
Llama 3.2 3B BF16 artifact can run the required `resid_post` intervention cell
through MLX with acceptably close outputs to Transformers/MPS and at least 5%
lower aggregate median forward latency on the validation machine.

No validation forward is authorized by this protocol until one public commit
binds this English/Japanese pair to the validator, its tests, the fixed
validation inputs and thresholds, and the implementation identity. A passing
receipt may select MLX for the pinned E2 cell only. It is not a scientific
result, a cross-model replication, or evidence about emoji representations.

## Pinned candidate cell

The validator must use exactly the following candidate:

- model artifact: `mlx-community/Llama-3.2-3B-bf16`;
- immutable revision:
  `60a99aaf43164077157d64bf909b7b61143c6a6d`;
- model role: base model, not an instruction-tuned or chat-templated variant;
- arithmetic: native BF16 model execution in both backends;
- reference backend: Transformers on MPS;
- candidate backend: MLX on the Apple GPU;
- expected architecture metadata: 28 decoder layers, hidden width 3,072, and
  vocabulary size 128,256;
- tokenizer behavior: `add_special_tokens: false`, with no chat template or
  system prompt;
- capture and intervention site: `resid_post`;
- capture and intervention position: `last_nonpad`;
- fixed intervention layers: `[5, 11]`.

The frozen local artifact inventory contains 9 files totaling 6,434,705,789
bytes. Its manifest SHA-256 is
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
This inventory was computed from tokenizer and weight files without loading or
forwarding the model. Both backend stages must independently reproduce this
exact inventory and manifest identity before their validation work qualifies.

Architecture metadata is an invariant, not a value to repair at runtime. The
validator fails closed if the loaded artifact disagrees with any expected
value, if the two backends do not resolve the same model width or layer count,
or if either backend cannot expose the two fixed `resid_post` sites.

The layer indices are resolved once from relative decoder depths `[0.2, 0.4]`
using

\[
\operatorname{layer}(d)=\operatorname{round}(d(N-1)),
\]

with zero-based indexing and `N = 28`. This gives layers 5 and 11. The indices
must not be reselected in response to validation or scientific outcomes.

## Fixed synthetic inputs

The validation inputs are fixed engineering probes. Three use public glyphs
from the E1 panel solely to exercise the tokenizer and adapter surfaces, but
none is an E1 endpoint/grid case. They use no target or source-wrapper bank and
are not P2 inputs, C1 inputs, or scientific outcome inputs.

| ID | Exact UTF-8 prompt | Engineering coverage |
|---|---|---|
| `prompt_00` | `🌒` | short emoji surface with the anticipated merged-token case |
| `prompt_01` | `🐑` | short emoji surface with the anticipated three-token case |
| `prompt_02` | `Mark: 🤑\nAnchor:` | emoji embedded in a short text wrapper |
| `prompt_03` | `Continue briefly: The scientist opened the notebook and` | medium text surface |
| `prompt_04` | `Write a concise two-sentence explanation of why a careful scientist records every calibration setting before comparing experimental interventions.` | long calibration surface |

In `prompt_02`, `\n` denotes one literal newline byte sequence in the decoded
string. The validator records each prompt's UTF-8 SHA-256, token IDs, token
count, and last-nonpadding position. Exact token-ID equality across the two
backends is a gate. These prompts may not be replaced after a failure without a
new protocol version and a new public freeze.

## Fixed interventions

Each prompt-layer case uses two float32 intervention vectors of width 3,072:

1. an all-zero vector; and
2. one deterministic direction whose RMS is 5% of the Transformers/MPS
   baseline `resid_post` RMS for that exact prompt and layer.

Let

\[
u_0=\operatorname{linspace}(-0.05,0.05,3072;\ \mathrm{float32}),\qquad
u=u_0-\operatorname{mean}(u_0;\ \mathrm{float32}),\qquad
\hat u=u/\operatorname{RMS}(u),
\]

and let `a^T_{p,l}` be the Transformers/MPS baseline activation at
`last_nonpad` for prompt `p` and layer `l`. The nonzero vector is

\[
v_{p,l}=0.05\,\operatorname{RMS}(a^{T}_{p,l})\,\hat u.
\]

The reference stage serializes the byte-identical float32 `v_{p,l}` in the
intervention plan and records the Transformers/MPS baseline RMS, derived scale,
and vector SHA-256. The MLX stage replays that serialized vector and must
recompute the same byte-level SHA-256 before injection. It must not reconstruct
or rescale the vector from the MLX baseline. The receipt records the
construction, reference activation RMS, derived scale, vector RMS, width,
dtype, and content hash for every prompt-layer case. This mirrors E2's
relative-RMS strength contract while retaining a single reference vector for
backend comparison.

## Sequential, process-isolated comparison

The two full models must not be resident together. Validation proceeds in a
fixed order:

1. a Transformers/MPS process loads the pinned artifact, verifies metadata and
   tokenization, captures the baseline, zero-vector, and nonzero-vector outputs,
   constructs the reference-scaled vectors, records timing samples, writes a
   staged comparison payload, and exits;
2. after the reference process has exited and released its model state, an MLX
   process loads the same pinned artifact and revision, verifies the same
   invariants, replays the exact prompts and serialized float32 vectors,
   verifies their exact hashes before injection, records its outputs and timing
   samples, writes a second staged payload, and exits;
3. a comparison step verifies both staged identities and evaluates the fixed
   parity and speed gates without loading either model.

Each prompt-layer-backend cell receives two unrecorded warm-up forwards followed
by ten measured forwards. With five prompts and two layers, each backend
contributes 100 measured samples. The forward timing includes tokenization,
capture/intervention, device evaluation, and transfer of the reported arrays to
NumPy. Model-load latency is recorded separately and is not part of the speed
gate.

This schedule is deliberately sequential and non-interleaved so that a 24 GiB
machine need not hold two approximately 6.4 GB weight sets simultaneously. Its
timing comparison is machine-specific and may be affected by temperature,
memory pressure, and phase order. It is an engineering selection gate, not a
portable MLX performance claim.

## Fixed parity gates

For a reference array `x` and candidate array `y`, define

\[
\operatorname{NRMSE}(x,y)=
\frac{\sqrt{\operatorname{mean}((y-x)^2)}}
{\max(\operatorname{RMS}(x),10^{-12})}.
\]

Cosine similarity is computed on flattened float64 comparison arrays. RMS ratio
means `MLX RMS / Transformers RMS` for cross-backend deltas. Every check below
must pass for every fixed prompt-layer case; there is no averaging away a
failed parity case.

| Check | Frozen criterion |
|---|---|
| Tokenization | exact token-ID equality |
| Baseline logits | NRMSE <= 0.02, cosine >= 0.999, and exact argmax equality |
| Baseline captured activations | NRMSE <= 0.02 and cosine >= 0.999 at each fixed layer |
| Changed logits | NRMSE <= 0.02, cosine >= 0.999, and exact argmax equality |
| Changed activation at the intervention layer | NRMSE <= 0.02 and cosine >= 0.999 |
| Logit delta | NRMSE <= 0.05, cosine >= 0.99, RMS ratio in [0.95, 1.05] |
| Activation delta | NRMSE <= 0.02, cosine >= 0.999, RMS ratio in [0.98, 1.02] |
| Intervention fidelity, separately in both backends | observed activation delta versus specified vector: NRMSE <= 0.01 and cosine >= 0.999 |
| Zero-vector integrity, separately in both backends | maximum absolute logit or captured-activation change <= 1e-7 |

Baseline and changed logits are compared over the complete vocabulary. No
threshold may be loosened, and no prompt or layer may be removed, after any
validation output is inspected. A code defect may be corrected only with a
versioned validator and a newly frozen receipt destination; the failed receipt
remains visible.

## Fixed speed gate

The aggregate distribution pools the 100 measured forward samples for each
backend over the fixed prompt-by-layer matrix. Let `m_T` and `m_M` be the
Transformers/MPS and MLX aggregate medians. The speed gate is

\[
m_M \le 0.95m_T.
\]

Cell-level and aggregate median, mean, minimum, and 95th-percentile latency are
published, along with the sample counts and model-load times. Passing this gate
means only that MLX is selected for the pinned local E2 cell. Failing it does
not invalidate parity; it means the planned scientific grid is not authorized
to claim this MLX engineering qualification under v1.

## Receipt, identity, and no-overwrite rule

The final receipt path is
`validation/mlx_llama32_3b_bf16_parity/receipt.json`. Before publication, the
receipt must bind at least:

- the protocol ID and frozen validation configuration identity;
- the exact model name and revision; the frozen 9-file, 6,434,705,789-byte
  artifact inventory and its manifest SHA-256; all model-file hashes; the
  tokenizer identity; and the stable model identities observed by both
  backends;
- the validator SHA-256 and complete `src/glyphprobe` implementation receipt;
- Python, dependency, OS, hardware, device, and arithmetic metadata;
- fixed prompt hashes and token IDs;
- layer derivation, intervention-vector metadata and hashes, all thresholds,
  warm-up/repeat counts, and timing method;
- every prompt-layer measurement, every individual gate result, the aggregate
  speed result, and any failure or deviation.

The validator writes a complete candidate receipt in a staging location,
verifies its schema and identities, then atomically renames it into the final
path only if that path does not exist. It must never truncate or overwrite an
existing receipt. Any rerun requires a new versioned destination or explicit
archival of the prior immutable receipt. Generated receipts are never edited by
hand.

The only passing status is `validated_mlx_selected`, requiring both complete
parity and the speed gate. Otherwise the status is `validation_failed`, MLX is
not selected for an E2 scientific run under this protocol, and all available
failure evidence is retained.

## Scientific boundary and prospective E2 handoff

Stage A produces no emoji-family endpoint and inspects no research outcome. It
must not read, hash, tokenize, model-forward, or analyze either the P2
confirmatory bank or the C1 causal bank. A passing receipt authorizes only the
next public freeze of E2 scientific inputs and analysis; it does not authorize
a result claim by itself.

The prospective E2 scientific freeze will retain the original 50 E1 emoji as
the primary literal panel and prespecify slots 03--09 across all five families
as a 35-glyph token-structural sensitivity panel. It will reuse the same 24
already explored prestage targets and the same 16 source wrappers. P2 and C1
remain untouched. The tokenizer audit, exact run configuration, endpoints,
analysis code, and manifest must be frozen publicly before E2 scientific model
forwards begin.

Even if that later grid completes, the E2 cell differs from E1 simultaneously
in model weights, tokenizer, vocabulary, architecture, and arithmetic dtype.
It therefore cannot isolate model scale, attribute a difference to any one of
those factors, or by itself establish a scale effect. Stage A is not a
replication; a later E2 result can at most be reported as a bounded cross-model
transport observation under its own frozen protocol and claim boundary.
