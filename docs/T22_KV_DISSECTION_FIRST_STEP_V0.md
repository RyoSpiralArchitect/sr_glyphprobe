# T22-E proposal: separate keys and values before extending the path claim

[日本語](T22_KV_DISSECTION_FIRST_STEP_V0.ja.md) | [T21 result](T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md) | [Final evidence audit](POST_REVIEW_EVIDENCE_RESULTS_V0.md)

Status: **decision memo with implemented synthetic engineering checks,
2026-10-19; not a frozen confirmation protocol**. No T22 real-item model
acquisition has run. The current paper,
T19/T20/T21 decisions, and historical evidence remain unchanged.

## Decision and motivation

The first step is a **key-only / value-only intervention canary**, followed by
a bounded exploratory comparison on already evaluated items if engineering
checks pass. Ask: after the same block-21 codepoint readout reset, can changing
glyph-position values without directly replacing keys change lexical margin,
and how does that compare with key-only and joint key/value replacement?

T21-C establishes a conditional margin contribution, not a retrieval-accuracy
gain. Its adjusted decrement/restoration means are 0.002326/0.002267; both
absolute mean top-1 effects are zero. The final audit decomposed margin into
own-keyword and maximum-competitor shifts, without new confirmatory tests.
The implementation still replaces keys and values together. Thus it leaves
open whether the measured perturbation depends on changing local attention
weights, the vectors being weighted, or their interaction.

This question precedes a larger symbol-panel comparison or a new generation
task: it changes one intervention factor while retaining T21's readout and
context. Those alternatives remain useful follow-ups; neither resolves this
particular ambiguity in the joint replacement.

## Smallest concrete deliverable

Implement a separate exploratory adapter and test it first with synthetic tiny
Llama inputs. Do not rewrite the historical T21 adapter or receipts. Its local
intervention has four settings:

| Setting | Replaced at selected past positions |
| --- | --- |
| Reference | Neither keys nor values |
| K | Post-RoPE keys only |
| V | Values only |
| KV | Both, reproducing T21's operation |

Use the same target and donor tensors to verify the four settings at a single
attention operation. V-only must preserve its input query, keys, mask, and
attention weights; K-only must preserve its input values. Require stock-path
parity, same-slot no-op and donor-then-original roundtrip, unchanged self/future
K/V, and unchanged non-readout attention outputs. Preserve GQA head handling,
RoPE positions, and the causal mask. Record the actual weights used by the
patched computation, rather than returning baseline weights as diagnostics.

These are **local** invariants. With interventions at several blocks, changed
readout states can change later queries and attention weights even in V-only.
Do not describe that experiment as holding the entire route fixed, or equate
K with pure routing and V with pure semantic content. A later experiment that
clamps reference attention weights would answer a different, additionally
conditioned question.

After synthetic checks, use exactly the eight already exposed T21 canary
targets. Retain the original checkpoint/revision, BF16 runtime, block-21 reset,
blocks 22–27, two distance-8 carriers, two predetermined token-count-matched
donors, gallery, and same-slot neutral references. Preserve the historical KV
batch layout for replay; acquire extension conditions separately. Check both
glyph and equal-count suffix positions. Historical output replay requires
access to the original arrays and compatible runtime; a receipt alone is not
an array-level replay. Version all new outputs outside historical directories.

## Exploratory measurement after the engineering gate

Use the 384 already evaluated T20 pilot items, with the fixed 128-item source
donor/gallery pool. Freeze the exact specification and runner hash before this
new acquisition. Do not select layers, donors, or items using new outcomes.
Keep anchor 21, distance 8, both carriers, and both donors. Average within
target item; repeated conditions and contexts do not increase the item count.
No new untouched-population inference follows from this reuse.

For each operation X in K, V, KV, let M be the original own-keyword cosine
minus maximum fixed-gallery competitor cosine, after its same-slot neutral
reference subtraction. Report the exploratory position-adjusted decrement:

`Delta_X = mean_item[M(suffix replacement X) - M(glyph replacement X)]`.

Show K, V, and KV together, with itemwise uncertainty and
`Delta_KV - Delta_K - Delta_V` as a descriptive nonadditivity contrast. Do not
interpret ratios as mechanistic percentages or assume additive mediators.
Also retain absolute decrements, own-keyword cosine, maximum competitor
cosine and identity, own-versus-donor margin, top-1, and actual per-layer/head
attention mass. These diagnose donor-directed changes and altered competition;
they do not independently establish semantic transport. Do not promote a
secondary endpoint after inspecting results. Restoration and behavioral tasks
are outside this first exploratory comparison.

## Stop/go and the next decision

- Engineering failure or KV replay mismatch: stop scientific interpretation;
  diagnose numerical/runtime or adapter differences first.
- Engineering pass: complete the prespecified exploratory panel regardless of
  the first eight effect signs. Eight canary items are not an efficacy screen.
- V-only effects: motivate a separately specified value-path test, while
  retaining the downstream-routing qualification above.
- Predominantly K-only or nonadditive effects: prioritize attention-weight and
  donor-compatibility controls before a content-path interpretation.
- Small or imprecise effects: report that limit; do not substitute a favorable
  layer or endpoint. The exploratory memo supplies no confirmatory verdict.

Before any confirmation, define a new eligible population and development /
evaluation split, practical effect threshold, sample size, multiplicity, and
decision rule. The original 954-item matching has no unused remainder: T21's
195 items are now exposed. A new seed or carrier does not make an item unused.
Never reopen the historical P2 or retired C1 target banks; do not invoke old
selection/exposure scanners that read them. Non-emoji path controls remain
necessary before claiming emoji specificity; rank or behavioral tests remain
necessary before claiming a corresponding performance benefit.

## Evidence checked in this task and execution boundary

The CPU compact T21 replay passed on all 195 items and 20,000 bootstrap draws,
with maximum numeric error 0. The five-contrast margin decomposition replay
passed with maximum error 4.163336342344337e-17. These check retained scalar
evidence, not raw-state acquisition or a second scientific replication.

The separate adapter is implemented in
[`t22_kv_dissection_v0.py`](../scripts/t22_kv_dissection_v0.py). It reuses T21's
capture/reset hooks without changing historical source. Its tests use random
tiny Llama models, an independent GQA attention calculation, and CPU FP32/BF16.
They cover operation isolation, actual returned weights, full causal masks,
non-readout outputs, stock parity, roundtrip, and legacy KV layout parity.
V-only locally preserves attention weights while later queries may change.
None of these synthetic results measures emoji lexical effects.

The source-bound engineering receipt is generated at
[`synthetic_validation.json`](../validation/t22_kv_dissection_v0/synthetic_validation.json).
The eight exposed inputs are fixed in
[`canary_specification.json`](../validation/t22_kv_dissection_v0/canary_specification.json);
this specifies inputs and does not admit or execute acquisition.
[`runtime_preflight.json`](../validation/t22_kv_dissection_v0/runtime_preflight.json)
records the missing real-model prerequisites.

To reproduce from the repository root (choose unused output paths):

```bash
.venv/bin/python -m pip install --no-cache-dir 'torch==2.13.0+cpu' \
  --index-url https://download.pytorch.org/whl/cpu
.venv/bin/python -m pip install --no-cache-dir 'transformers==5.15.0'
.venv/bin/python scripts/validate_t22_kv_dissection_v0.py \
  --output /tmp/t22-synthetic-validation.json
.venv/bin/python scripts/t22_kv_dissection_v0.py prepare-canary \
  --output /tmp/t22-canary-specification.json
.venv/bin/python scripts/t22_kv_dissection_v0.py preflight \
  --output /tmp/t22-runtime-preflight.json
```

The validator rejects skipped/incomplete suites and source changes during
validation; inherited pytest selection options cannot turn a subset into a
pass. Receipts/specifications never overwrite existing files. Preflight exits
2 when prerequisites are missing, without model forwards. A supplied historical
canary must match the original receipt and validate all source/chunk hashes;
finite arrays or a JSON receipt alone do not satisfy that check.

This instance now has Torch 2.13.0+cpu and Transformers 5.15.0. It has no GPU
device, local Llama checkpoint, or original canary raw arrays available in the
inspected workspace/cache locations. T21's GPU runtime was Torch 2.13.0+cu132,
Transformers 5.15.0, BF16 on RTX 5090. CPU synthetic validation is complete;
historical checkpoint replay, real eight-item canary acquisition, and the
384-item exploratory comparison are **unrun**. The real-model canary driver is
not yet implemented; it must enforce the specified gates when those resources
are available. Do not describe this artifact as an end-to-end experiment run.
