# Emoji Steering Specificity Expansion v0

[Japanese / 日本語](EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md) ·
[T13-EA results](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) ·
[Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol ID: `glyphprobe-emoji-steering-specificity-expansion-v0`  
Experiment label: **T14-X**

Freeze note: the initial zero-forward manifest was superseded before any T14-X
model forward solely to make the contention-yield receipt T14-X-owned instead
of reusing the T13 protocol identifier. No scientific design field changed.

## Purpose

T13-EA found that structured source directions often produce larger
next-token-distribution changes than positive isotropic directions, especially
near normalized depth 0.875. T14-X expands that observation before any targeted
causal claim is attempted.

T14-X fixes six base-model roles, all 192 already exposed T13 source items, all
32 public targets, depths 0.875 and 1.0, both intervention signs, four rotating
wrapper holdouts, and two deterministic signed source-covariance null families.
The complete grid contains **559,488 intervention rows**.

## Why this increases the useful sample

The 20,000 T13 bootstrap replicates refine uncertainty for the existing data;
they do not create new independent observations. T14-X instead increases the
experimental support:

- intervention roles expand from three to six base checkpoints;
- all 192 source items are intervened at both late depths;
- wrapper dependence is measured by four leave-one-wrapper-out prototypes;
- positive-only isotropic calibration is replaced by signed nulls drawn from
  the observed source-direction residual covariance.

Targets, source items, wrappers, signs, depths, and model roles remain distinct
levels. Repeated directions and signs are not counted as independent prompts.

## Frozen grid

| Arm | Rows per model | Six-model rows |
|---|---:|---:|
| Item/source-form late-depth grid | 70,656 | 423,936 |
| Leave-one-wrapper-out prototypes | 14,336 | 86,016 |
| Signed source-covariance nulls | 8,192 | 49,152 |
| Explicit zero hooks | 64 | 384 |
| **Total** | **93,248** | **559,488** |

The model roster is Qwen 2.5 0.5B, OLMo 2 1B, Qwen 2.5 1.5B, Llama 3.2 3B,
Qwen 2.5 3B, and Qwen 2.5 7B, using the exact T13 source-bank artifacts and
runtime receipts. The apparent parameter range is descriptive; architecture,
tokenizer, and size are confounded.

## Null construction

For each model, depth, and held-out wrapper, T14-X rebuilds every available
system/view prototype from the other three wrappers. Each item direction is
unit-RMS normalized and centered on its corresponding prototype. The pooled
finite residual matrix defines two null generators:

1. deterministic Gaussian coefficient combinations; and
2. deterministic Rademacher coefficient combinations.

Each family contributes eight seeds per wrapper fold and depth. Both signs are
run explicitly. These controls test whether the structured response exceeds
directions with source-derived covariance while removing the system/view mean.
They do not prove tokenization independence or semantic specificity.

## Execution and stopping

The frozen manifest must audit before the first model load. The complete T13
source role and its hashes must validate before reuse. Every role runs an
explicit zero-hook shard before nonzero intervention shards. Existing complete
shards validate and are never overwritten. Foreign GPU contention causes a
cooperative yield rather than interference.

Scientific outcome inspection begins only after all six roles and all frozen
shards are complete. Every model, system, item, view, target, sign, and null
cell remains visible, including negative and heterogeneous results.

## Causal handoff

T14-X is allowed to inform a separately frozen localization selector using only
public/exposed inputs. That selector may bind exactly one model, injection
depth, and downstream component for a later patch/ablate/restore experiment.
The retired C1 v1 bank and any future C1 v2 bank are outside T14-X. A replacement
bank must remain ungenerated and unopened until the complete causal operation,
endpoint, controls, multiplicity rule, and selected component are frozen.

## Claim boundary

T14-X is exploratory. It cannot establish emoji meaning, unique emoji
specificity, a causal component or path, generated behavior, tokenizer
independence, a scale law, model-population generality, or independent
replication. A clean negative or heterogeneous result remains a complete T14-X
result and constrains the later causal design.
