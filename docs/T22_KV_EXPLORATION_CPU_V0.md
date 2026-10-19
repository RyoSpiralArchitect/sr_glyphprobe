# T22: fixed design for the exposed-384 CPU K/V exploration

[日本語](T22_KV_EXPLORATION_CPU_V0.ja.md) | [Paper 2 discussion](PAPER2_DISCUSSION_NOTES_V0.md) | [Eight-item results](T22_CPU_LEXICAL_RESULTS_V0.md)

Status: **design and inputs frozen; execution not admitted; 384-item acquisition
unrun**, 2026-10-20 JST. The first eight T22 outcomes were already known when
this design was written. This is prospective for the new 384-item acquisition,
not a claim of blinded design or a preregistered confirmation. The candidate,
operations, donors, gallery, and target panel were selected in the earlier
[decision memo](T22_KV_DISSECTION_FIRST_STEP_V0.md) before these outcomes.

## Population and unchanged question

Retain all 384 originally evaluated T20/T21 pilot items in original order:
68 two-token and 316 three-token glyphs. Retain the 128 original source items
(22 two-token, 106 three-token), each target's two original token-count-matched
donors, and the original alias-token sequences. The eight previous T22 items
are indices 0–7 and remain in the 384-item summaries; none is excluded because
its outcome is known or inconvenient. These 384 items are exposed, not a new
confirmatory population. The historical p2/c1 v1 banks and old allocation
scanners are not used.

The question remains how K-only, V-only, and joint KV replacement affect the
conditioned lexical readout, and whether their contrasts are additive. Retain
block-21 same-item codepoint residual reset, intervention blocks 22–27,
distance 8, pipe/article-a carriers, and glyph/equal-count-suffix positions.
Only the readout query receives substituted donor tensors. Keys are post-RoPE;
values are the unrotated value tensors. V's local attention weights must remain
unchanged at each layer's own input; later queries/attention may differ.

Each carrier has the original 16 extension rows in operation → position →
donor order: `none, k, v, kv` × `glyph, suffix` × donor slots `0, 1`.
Active and neutral runs have identical batch shape and row slots. Neutral
disables the donor substitution while retaining the reset. Keep this batch
shape for the smaller and larger glyph token counts; no mixed-length padding.

## Acquisition contract and the engineering change

The existing eight-item implementation repeatedly runs the historical 88-row
layout to establish old/new adapter parity. Its mean total item time was
951.81 seconds, of which 771.64 seconds came from those legacy forwards.
The 384-item design retains the 16-row measurement layout and every local
invariant, but does not repeat the legacy 88-row comparison for every target.
This is an execution change motivated by measured timing, not by effect size.
The reduced runner has **not yet been implemented or timed**.

The exact proposed forward schedule, per target and carrier, is:

1. Stock glyph, adapter-idle glyph, donor-0 capture, donor-1 capture, and
   codepoint reset capture, each with one sequence.
2. Active 16-row extension batch, then its neutral 16-row companion.
3. After closing the intervention hooks, a complete stock-glyph replay and
   the target alias forward, each with one sequence. Require full stock-state
   equality before accepting the alias.

This gives 18 calls / 78 sequence forwards per target. Reacquiring the 128
source aliases in both carriers adds 256 single-sequence calls. The planned
total is **7,168 calls / 30,208 sequence forwards**, with no generation,
training, tokenizer invocation, codepoint gallery, or restoration experiment.
No old readout or alias is substituted for a new acquisition result.

Persist all 26 nonlegacy arrays from the original canary schema per item:
stock/codepoint states, reset captures, donor K/V, active/neutral readouts,
actual/local-baseline attention weights, position masks, and attention masses.
Persist target/source alias rows, all checks, counts, timing, and content hashes.
Old full hidden-state comparisons not saved in that schema remain historical
acquisition assertions; they cannot be reconstructed from a receipt alone.

Before processing target 8, the new runner must exactly match the original
CPU canary's **all 26 persisted nonlegacy arrays for each of indices 0–7** and
all eight target alias rows, including both carriers. The 128 two-carrier
source alias rows must also exactly match their archived CPU acquisition.
These eight targets belong to the 384 run, so their calls are already included
in the budget. This is an arithmetic/implementation gate, never an effect-sign
gate. Failure stops acquisition and interpretation; it cannot be waived by a
favorable effect. The historical RTX 5090 replay is a separate unperformed check.

The model remains `mlx-community/Llama-3.2-3B-bf16`, revision
`60a99aaf43164077157d64bf909b7b61143c6a6d`, manifest
`dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
Require the nine-file manifest before and after acquisition, Torch 2.13.0+cpu,
Transformers 5.15.0, NumPy 2.5.4, BF16 eager attention, four CPU threads,
one interop thread, seed 2026092100, no cache/quantization/remote code, and one
model process. Bind the actual Python/platform/attention-implementation details
in the future execution manifest and require compatible exact replay.

## Metrics, aggregation, and reporting fixed before the new run

Read the final-normalized last carrier token. Use float64 L2-normalized cosine
against own alias first and the unchanged 128 source aliases. Own-first argmax
breaks top-1 ties; rank is one plus the number of strictly larger competitor
scores. Maximum-competitor ties use the first source in original order.
Save all scores with shape `[384, 2 carriers, 2 active/neutral, 16 rows, 129]`:
**24,576 scored rows and 3,170,304 cosines**.

Compute `E = active - identical-slot neutral` for each scalar metric before
averaging. For each target and operation X:

- Adjusted decrement: `Delta_X = mean_carrier,donor(E_suffix,X - E_glyph,X)`.
- Absolute glyph decrement: `-mean_carrier,donor(E_glyph,X)`.
- Nonadditivity: `Delta_KV - Delta_K - Delta_V`.

A positive adjusted margin decrement means glyph replacement reduces own
versus maximum-competitor margin more than suffix replacement. Show reference,
K, V, and KV together. The **target item is the unit, n = 384**. Carrier/donor
repetition does not yield 1,536 independent items. Preserve their separate
rows and do not average hidden states before scoring.

Retain own cosine, maximum-competitor cosine and identity, own-minus-competitor
margin, matched-donor cosine and margin, own rank, and own-first top-1. Numeric
effect summaries comprise all item values, mean, median, sample SD (`ddof=1`),
range, positive/zero/negative counts, and empirical 2.5/25/50/75/97.5 percentiles
(`numpy.quantile`, `method="linear"`). Quantiles describe between-item spread;
they are **not confidence intervals**. Competitor IDs are categorical, not a
numeric effect endpoint; keep identities and transitions. Rank/top-1 results
must not be inferred from the sign of a cosine-margin mean.

The all-384 comparison is the main descriptive account. Separately show both
carriers and the two glyph-token-count groups as diagnostics, retaining every
operation and fixed donor. These strata do not define new tests or permit
selection. There are no p-values, population intervals, practical-effect
thresholds, a statistical winner, or a confirmatory verdict. New layers,
donors, metrics, or exclusions cannot be chosen using partial outcomes.

Decompose margin exactly into own minus maximum-competitor terms. Save the
actual and local-baseline attention by block/head, active-versus-neutral
headwise L1 distances, and glyph/suffix attention mass. Check reference effects
and local V attention equality exactly; use `1e-12` only as the independent
float64 arithmetic reconstruction tolerance, not an efficacy threshold.
An independently implemented saved-array and metric audit must pass before
scientific interpretation. Do not issue partial effect summaries while the
384-item panel is incomplete. Progress reports may contain engineering status,
item counts, timings, memory, and failures.

## Execution budget, pause, and recovery

The required 14 pre-alias calls per item correspond to existing measured stages
whose mean total was 136.53 seconds per canary item. Scaling their mean to 384
and adding an alias-time proxy gives **about 14.8 hours**; scaling the slowest
canary item gives **about 21.7 hours**. Repeating the full old engineering layout
would give about **101.7 hours** by the same calculation. These are planning
scenarios, not a timing run of the new implementation or confidence bounds.
The alias proxy scales the measured 288-forward elapsed time by 1,792/288,
including its old load/final-manifest overhead. New item shapes, resources,
model loading, filesystem work, and validation may change wall time.

Fix a cumulative active-time ceiling of 48 hours, at most 8 active hours per
invocation, process RSS below 20 GiB, at least 20 GiB free disk at start/resume,
and at most 10 GiB of run artifacts. The execution implementation must enforce
these limits, checkpoint at item boundaries, and record interrupted time in
an execution ledger. Resolve unknown interrupted active time before resuming.
A budget/resource pause preserves completed chunks and is not a scientific
failure, completion, or reason to drop items. Record any budget amendment
before continuing, without examining partial effects.

Only identical incomplete work can resume: same design, executable sources,
runtime, model, inputs, and batch layout; rehash every committed chunk. Use
exclusive run ownership and atomic item publication. Completed work is immutable.
Hash/runtime mismatch, nonfinite states, or parity/invariant failure stops
scientific interpretation and requires diagnosis. Repairs require a new version
and explicit evidence compatibility; never edit old receipts or frozen sources.

## What this freeze does and does not admit

The [specification tool](../scripts/t22_kv_exploration_spec_v0.py) reads only
explicitly pinned historical specifications, receipts, source files, and
content hashes of archived replay arrays. It does not inspect lexical scores,
retokenize, select a new panel, download a model, or run model forwards.
It freezes exact tokens, donors, row order, metrics, runtime requirements,
resource policy, and timing-derived estimates. Its audit recomputes this design
deterministically; it is not an independent experimental replication.

The design deliberately reports `execution_admission.admitted=false` with
null new-runner and analysis hashes. Before any 384-run acquisition, implement
and validate those executables, then publish an execution manifest binding
their exact hashes to this design and the actual runtime. The first-eight
replay gate must pass before target 8. A design freeze alone must never be
treated as permission to run an unvalidated reduced implementation.
Execution not admitted means these technical checks are incomplete; it does
not mean another user approval is pending.

From the repository root, use unused output paths:

```bash
python3 scripts/t22_kv_exploration_spec_v0.py validate \
  --output validation/t22_kv_exploration_cpu_v0/design_validation.json
python3 scripts/t22_kv_exploration_spec_v0.py freeze \
  --validation validation/t22_kv_exploration_cpu_v0/design_validation.json \
  --output validation/t22_kv_exploration_cpu_v0/specification.json
```

Audit an existing freeze with its externally recorded SHA-256:

```bash
python3 scripts/t22_kv_exploration_spec_v0.py audit \
  --specification validation/t22_kv_exploration_cpu_v0/specification.json \
  --expected-sha256 RECORDED_SPECIFICATION_SHA256 \
  --output /tmp/t22-384-design-audit-NEW.json
```

The [design validation](../validation/t22_kv_exploration_cpu_v0/design_validation.json),
[frozen specification](../validation/t22_kv_exploration_cpu_v0/specification.json),
and [design audit](../validation/t22_kv_exploration_cpu_v0/design_audit.json)
record this stage. K/V semantic separation, emoji specificity, intact-context
necessity/sufficiency, behavior, and fresh confirmation remain unestablished.
