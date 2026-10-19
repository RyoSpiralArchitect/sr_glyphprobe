# T22 CPU lexical comparison of the exposed eight

[日本語](T22_CPU_LEXICAL_CANARY_V0.ja.md) | [Completed engineering](T22_CPU_ENGINEERING_V0.md)

Status: implementation and pre-acquisition specification. The eight-item engineering
run completed; no lexical scores from it have been inspected when writing this
protocol. This is a descriptive comparison of those eight exposed items. It is
not a confirmation, efficacy screen, or substitute for the 384-item exploration.
The larger exploration must not be selected, cancelled, or retuned using these
eight effect signs. Historical T19/T20/T21 evidence and source remain unchanged.

## Fixed inputs and additional acquisition

Reuse only `runs/t22_cpu_canary_v0/`, acquisition SHA-256
`27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901`.
Its eight items retain the block-21 codepoint reset, distance 8, pipe/article-a
carriers, two predetermined token-count-matched donors, glyph/equal-count-suffix
positions, and K/V/KV/reference operations at blocks 22–27. The original 16-row
extension batch and every identical-slot neutral readout are preserved.

Acquire the original frozen alias-label token sequences for all 128 source
gallery items and all eight target items. Use the same pinned nine-file 3B model,
Torch 2.13.0+cpu, Transformers 5.15.0, BF16, eager attention, four CPU threads,
one interop thread, no padding, cache, quantization, tokenizer, or remote code.
Each forward has batch size one. Read the last carrier token after final norm,
matching T21 distance-8 alias readouts. Before capturing each target alias,
require exact replay of its complete stored stock glyph hidden states in both
carriers. There are 272 alias and 16 stock-check forwards, 288 total; no new
intervention forward is needed. No target bank is read or scanned.

The source-bound synthetic validation must pass before `prepare` freezes inputs,
source/test/document hashes, runtime, engineering audit, and metric definitions.
Require an independent audit of the completed engineering parent. Verify the
complete model manifest before and after acquisition. Save every two-carrier
alias row with a hash-bound receipt. Resume only identical incomplete acquisition;
completed acquisitions are immutable. Source or stock-replay mismatch stops work
before any scientific interpretation.

## Metrics and contrasts fixed before scoring

Use float64 L2 normalization and one 129-column matrix product for each readout
batch: own alias first, then the original 128 source aliases in original order.
Ties favor the own alias, matching T21. Score active and identical-slot neutral
rows separately without averaging states first. Keep all cosine scores and:

- own-alias cosine, strongest-competitor cosine and its fixed source index;
- margin = own cosine minus strongest-competitor cosine;
- own-versus-matched-donor cosine margin, own rank, and own-first top-1.

For every metric, first compute `E = active - neutral` in each original row.
For operation X, the position-adjusted decrement is
`Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)` within each target.
Positive margin Delta means a greater margin reduction for glyph than suffix
replacement. Also retain the absolute glyph decrement `-mean(E_glyph,X)`.
Show reference, K, V, and KV together, and report the descriptive interaction
`Delta_KV - Delta_K - Delta_V`. Decompose margin Delta exactly into own-cosine
Delta minus max-competitor-cosine Delta. Do not interpret ratios as mechanistic
percentages. The reference operation must have exactly zero margin effect.

Report all eight item values, the mean, median, sample SD, and range. The item
is the aggregation unit; two carriers and two donors do not create 32 items.
No population confidence interval, p-value, decision threshold, or winning
operation is declared. Save per-carrier/per-donor contrasts and all 512 scored
active/neutral rows so averaging cannot hide heterogeneous directions.

Retain the engineering run's complete per-layer/head attention arrays by their
bound hashes. Summarize active-versus-neutral weight L1 differences and
glyph/suffix attention-mass changes by block. Check V/reference against each
layer's local baseline, separately from its neutral run: local V weights are
identical, but changed later queries may change downstream routing. K is not
pure routing and V is not pure semantics. Codepoint-gallery metrics, restoration,
generation behavior, emoji specificity, and historical GPU parity are outside
this acquisition and remain unmeasured here.

## Commands

Run from `/workspace/sr_glyphprobe`; output names must be unused:

```bash
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py validate \
  --output validation/t22_cpu_lexical_canary_v0/synthetic_validation.json
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py prepare \
  --canary runs/t22_cpu_canary_v0 \
  --validation validation/t22_cpu_lexical_canary_v0/synthetic_validation.json \
  --output runs/t22_cpu_lexical_canary_v0
.venv/bin/python -u scripts/t22_cpu_lexical_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_lexical_canary_v0
.venv/bin/python scripts/t22_cpu_lexical_canary_v0.py analyze \
  --acquisition runs/t22_cpu_lexical_canary_v0 \
  --output runs/t22_cpu_lexical_analysis_v0
```

After a confirmed interruption with no live acquisition, use the same `run`
command plus `--resume`. Never edit frozen source files to resume; any repair
requires a new version and explicit evidence compatibility. Analysis writes raw
scores/contrasts, a CSV, attention diagnostics, a result receipt, and a generated
report. Actual results will be recorded separately without modifying this
source-bound pre-scoring protocol.
