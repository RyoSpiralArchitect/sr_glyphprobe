# E2 Llama 3.2 3B MPS emoji-transport protocol v2

[日本語](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) · [v1 preflight failure](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](HOLDOUT_STATUS.md) · [Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol and analysis ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`

## Status and purpose

Status is `freeze_pending` until a public static-freeze commit binds this
English/Japanese pair, the ten v2 configurations, panel bindings, v2 preflight,
launcher, analyzer, publication tools, tests, exact environment/model artifact,
and checksum manifest. From that clean pushed commit, a zero-model-forward
preflight must publish
`artifacts/llama32_3b_mps_emoji_transport_v2/preflight/tokenization_audit_v2.json`
as the only changed file in a descendant commit. Execution remains
`preflight_pending` until that receipt passes and is public.

V2 asks the same bounded question as v1: whether E1's matched-slot output
fingerprint structure appears in one pinned Llama 3.2 3B Transformers/MPS FP32
cell, with a separately centered tokenizer-isomorphic 35-glyph sensitivity arm.
The study is outcome-bearing but exploratory because it reuses 24 targets that
were already explored.

## V1 failure and the only permitted v2 change

V1 stopped at zero-model-forward tokenizer preflight. It loaded no language
model weights, created no run, and produced no scientific outcome. Its frozen
audit incorrectly required contextual wrapper token IDs and offsets to equal
raw-glyph tokenization even when a first token jointly covered the preceding
space and emoji. The complete disposition is frozen in the [v1 failure
record](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md).

V2 changes only:

- the tokenizer audit, which now distinguishes raw and exact contextual
  tokenization;
- all protocol, manifest, configuration, run, receipt, analysis, log, and
  publication namespaces, which end in v2.

The model, artifact revision, arithmetic, panels, targets, wrappers, layers,
site, strength, seeds, controls, fingerprint settings, execution order,
bootstrap, endpoint, decision rule, and claim boundary remain unchanged. This
is fixed before the first model forward and may not be revised after outcomes.

## Fixed model and environment

| Field | Frozen value |
|---|---|
| Model | `mlx-community/Llama-3.2-3B-bf16` |
| Revision | `60a99aaf43164077157d64bf909b7b61143c6a6d` |
| Architecture | Llama, 28 layers, width 3072, vocabulary 128256 |
| Parameter count | 3,212,749,824 |
| Backend | raw Transformers |
| Device | MPS |
| Runtime parameter dtype | FP32, verified before first forward |
| Tokenizer surface | no special tokens, chat template, or system prompt |
| Network | Hugging Face and Transformers offline |

The local model snapshot must contain exactly 9 files and 6,434,705,789 bytes,
with path-independent manifest SHA-256
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
The execution environment is Python 3.13.13, GlyphProbe 0.1.0, NumPy 2.4.4,
PyTorch 2.11.0, Transformers 4.57.6, and macOS 26.2 on arm64. Any difference
requires another versioned freeze.

The earlier MLX Stage A3 no-go is unchanged. V2 is a separately versioned
Transformers/MPS study, not an MLX fallback or reinterpretation.

## Fixed inputs and holdout boundary

- Targets are exactly the ordered first 24 records of
  [`prestage_targets.jsonl`](../data/targets/prestage_targets.jsonl): four each
  from six fixed target groups.
- Source contexts are exactly all 16 ordered records of
  [`source_wrappers.jsonl`](../data/wrappers/source_wrappers.jsonl).
- P2 and retired C1 v1 are outside the executable, preflight, and analysis
  surface. V2 must not read, sample, tokenize, model-forward, score, or select
  with them.

The complete prestage hash is
`91ec5138c31ba56aede5f94d11a43b460385015237f437d933a55be3bc775ad7`;
the selected first-24 slice hash is
`26d42a9be61d9b6a28acf18f18b9b1d771f0f4531b3a576112ba0f6add76713b`;
and the wrapper hash is
`310af508fbe1dd218cb72552d614c812d5afc2bca34165433036f1058a20bdee`.

## Fixed panel arms

| Arm | Slots | Glyphs | Role |
|---|---|---:|---|
| `full50` | `slot_00`–`slot_09` | 50 | sole primary arm |
| `core35` | `slot_03`–`slot_09` | 35 | non-rescuing tokenizer-structural sensitivity arm |

The five families are `sky`, `food`, `animals`, `transport`, and `social`.
Each family is a separate process and is centered over its own active panel.
`core35` is the exact seven-slot subset of `full50`; it is recentered and its
random-control span is rebuilt independently rather than subset after running.

## Corrected and frozen tokenizer contract

The raw-glyph contract remains unchanged:

- 47 of 50 full-panel glyphs have `[9468, m_k, r_j]`;
- family-middle tokens are `234`, `235`, `238`, `248`, and `97` in fixed family
  order;
- ordinary slot suffixes for `slot_00`–`slot_09` are `239`–`248`;
- the three two-token exceptions are fixed exactly as recorded by preflight;
- all 35 core glyphs have `[9468, m_k, r_j]`, with shared suffixes `242`–`248`.

Contextual source-wrapper tokenization is frozen separately. The expected first
token is `11410` for wrappers `w01`, `w03`, `w04`, `w06`, `w10`, `w12`, `w13`,
`w14`, and `w15`; it is `9468` for `w02`, `w05`, `w07`, `w08`, `w09`, `w11`,
and `w16`. The preflight binds the complete wrapper IDs, not these abbreviations.

For a wrapper-first token of `11410`, the first token offset must cover exactly
the immediately preceding space plus the emoji interval; remaining overlapping
tokens cover exactly the emoji interval. For `9468`, every overlapping token
covers exactly the emoji interval. For every core item, the contextual span must
be exactly `[wrapper_first, family_middle, slot_suffix]`. For full50, contextual
IDs must equal the raw profile with only its first `9468` replaced by the
wrapper-first token. Within each wrapper, core positions and total token counts
must be constant, full-panel exception counts must follow the frozen rule, and
the outside-token sequence must be identical across all 50 glyphs. Decoded
round trips, anchors, code points, UTF-8 bytes, and all 800 wrapper profiles are
recorded. Any mismatch blocks execution.

This is tokenizer-isomorphic only for the pinned tokenizer and construction.
Family identity remains confounded with the middle token, so v2 does not remove
tokenization as an explanation.

## Fixed intervention cell

| Component | Frozen value |
|---|---|
| Mode/site | internal activation addition at `resid_post` |
| Layers | `[5, 11]` |
| Position | `last_nonpad` for source, capture, and intervention |
| Strength/normalization | `0.05`, RMS |
| Clip | global RMS, ratio at most `0.25` |
| Direction seeds | `[101, 211, 307]` |
| Direction replicate | 12 of 16 wrappers, fixed 0.75 subsample |
| Random controls | 2 per layer and seed, outside active panel span |
| Zero hook | once per target and layer; exact integrity check |
| Disabled | sign flip, label shuffle, neutral direction, iso-KL, SAE, generation |
| Fingerprint | 96-dimensional CountSketch, seed `8675309` |
| Diagnostics | top-k 50, RBO 0.90, split-half 200, top deltas 32 |
| Run policy | `resume: false`, fail fast; no v2 restart |

Layer 5 is the sole primary layer; layer 11 is a prespecified secondary depth
comparator. Seeds are nested repeated direction estimates, not independent
observations.

## Exact execution counts

| Arm | Source | Baseline | Glyph | Random | Zero | Ledger rows | Total forwards |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full50` | 880 | 120 | 7,200 | 1,440 | 240 | 8,880 | 9,880 |
| `core35` | 640 | 120 | 5,040 | 1,440 | 240 | 6,720 | 7,480 |
| Total | 1,520 | 240 | 12,240 | 2,880 | 480 | 15,600 | 17,360 |

All ten cells run in separate sequential Python processes in this order:
`full50` then `core35`; within each arm, `sky`, `food`, `animals`, `transport`,
`social`. Intermediate outcomes are not inspected. A caught failure writes a
no-overwrite failure receipt and no success receipt. An interruption retires v2
as incomplete; it is never resumed, repaired, or selectively rerun.

## Fixed analysis and primary decision

Stored 96-dimensional fingerprints are analyzed with E1's leave-one-target-
group-out prototype procedure. For each target and source family, `M` is the
matched-family similarity, `R` subtracts the median of the four mismatched
prototype-family similarities, and `R_global` is the equal-family mean of `R`.

The sole primary row is:

- arm `full50`;
- layer 5;
- endpoint equal-family `R_global`;
- status `transport_criterion_met` only when the lower endpoint of the
  two-sided 95% percentile interval is strictly greater than zero.

The bootstrap uses 20,000 replicates with seed `20260808`. It resamples four
target prompts inside each of six groups using one joint schedule across arms,
layers, endpoints, and paired differences. Every replicate rebuilds all
data-dependent leave-one-group-out prototypes. Direction seeds remain nested
and averaged.

Secondary, non-rescuing outputs are core35 layer 5, both layer-11 arms, all
family-specific rows, complete transfer matrices, random/zero controls, target
and target-group descriptions, and the paired descriptive `core35 - full50`
difference. The paired difference is not a fraction explained by tokenization.

The six fixed analysis outputs are:

- `panel_target_scores.jsonl` — 480 rows;
- `transfer_target_scores.jsonl` — 1,920 rows;
- `family_cell_summary.jsonl` — 20 rows;
- `transfer_cell_summary.jsonl` — 80 rows;
- `llama32_3b_mps_emoji_transport_v2_receipt.json`;
- `report.md`.

Invalid or incomplete evidence blocks analysis publication and primary status.

## Receipt and publication contract

The launcher writes no-overwrite receipts under
`validation/llama32_3b_mps_emoji_transport_v2/`. Before the first process it
writes `attempt_started_receipt.json`; a complete grid writes
`execution_receipt.json`; a caught failure writes
`failed_execution_receipt.json`. The success receipt must hash-bind the start
receipt and require the failure receipt to be absent.

The public evidence root is
[`artifacts/llama32_3b_mps_emoji_transport_v2/`](../artifacts/llama32_3b_mps_emoji_transport_v2/).
The freeze manifest is
[`data/manifests/llama32_3b_mps_emoji_transport_v2.json`](../data/manifests/llama32_3b_mps_emoji_transport_v2.json).
Local run directories retain all 19 files. The compact Git bundle copies 15
validated files per run and omits raw `interventions.jsonl`,
`source_activations.npz`, `directions.npz`, and `target_baselines.npz`. Its root
manifest records hashes, byte counts, and row or array metadata for every
omitted file and binds every public member. Nothing is overwritten.

## Claim boundary

The strongest possible positive statement is a prospectively frozen,
Transformers/MPS-only Llama 3.2 3B FP32-runtime matched-slot output-fingerprint
transport observation on 24 reused exploratory targets, with a separately
centered tokenizer-isomorphic sensitivity arm.

Even a positive primary row does not establish emoji meaning, semantic
families, tokenizer independence, an independent target confirmation, causal
localization, generation behavior, backend-isolated replication, or a model-
scale effect. V2 does not update C1, authorize a causal claim, or close a Phase I
paper gate by itself. A negative or invalid result is published under the same
boundary.
