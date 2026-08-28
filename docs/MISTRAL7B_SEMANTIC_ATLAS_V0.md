# Mistral 7B semantic atlas v0

[日本語](MISTRAL7B_SEMANTIC_ATLAS_V0.ja.md) · [T7 results](MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) · [Roadmap](ROADMAP.md)

Status: **prospective acquisition freeze; zero T8 model forwards**. This
document defines a reusable observational dataset. It does not define a
confirmatory semantic endpoint.

## Motivation

T7 passed its fixed one-model intersection-union test, but its five families
were consecutive Unicode blocks. On the pinned Mistral tokenizer, 49 of 50
glyphs factor almost exactly into a common prefix, a block/family token, and a
within-block token. The matched-slot recurrence can therefore have a sufficient
token-structural explanation. Relabeling those same 50 slots is not a new
control: it is the synchronized within-family permutation null already used by
T7.

T8 changes the scale and the observable. It acquires three input views for a
large standards-defined emoji population so later analyses can compare a glyph
against its human-readable name and against an arbitrary codepoint literal.
The raw activation atlas is intentionally richer than any one current
hypothesis.

## Population and untouched reserve

The pinned source is Unicode Emoji 17.0 `emoji-test.txt`. The tokenizer-only
census keeps all 1,184 fully-qualified single-codepoint entries. It loads no
model weights and performs no model forward.

The old E1 panel contributes 50 `calibration_prior_exposed` items. The other
1,134 items are split before any activation is observed by SHA-256 of the
uppercase codepoint under namespace `glyphprobe-t8-v0`: remainder zero modulo
four is `reserved_unrun`; the other three remainders are `discovery_unseen`.
The resulting fixed counts are:

- 50 calibration-prior-exposed items;
- 842 discovery-unseen items;
- 292 reserved-unrun items.

T8 acquisition runs the first two roles, 892 items total. The 292-item reserve
must receive zero model forwards until a later confirmatory analysis protocol
is frozen without viewing reserve activations. Tokenizer-only inspection is not
a model forward and is already hash-bound in the selection manifest.

## Three fixed views

Every acquired item has exactly three strings:

1. the exact single-codepoint glyph;
2. the exact Unicode name in the pinned source;
3. the literal uppercase `U+...` codepoint.

The name view is a semantic-language anchor, while the codepoint literal is an
identity-bearing but semantically arbitrary textual comparator. Neither is a
perfect control. Exact token IDs and lengths are retained for all three views,
so subsequent work can stratify or residualize token structure without
reconstructing it after outcomes are known.

## Fixed acquisition grid

The model is
`mistralai/Mistral-7B-v0.3@caa1feb0e54d415e2df31207e5f4e273e33509b1`,
loaded from the already verified 12-file BF16 artifact on the furnace. The grid
uses:

- views: glyph, Unicode name, codepoint literal;
- carriers: eight `" a"` tokens and eight `" |"` tokens;
- distances: 1, 2, 4, and 8 carrier tokens after the view;
- `resid_post` layers: `[0, 4, 8, 12, 16, 20, 24, 28, 31]`;
- activation storage: FP32;
- axis order: item × view × carrier × distance × layer × width.

This is 5,352 unique input sequences and 192,672 stored 4,096-dimensional
vectors. One causal forward contains all four readout positions for a fixed
item/view/carrier string. Reading those positions together is exactly the same
causal input as forwarding that unchanged string four times, apart from normal
backend numerical reproducibility. The runner therefore uses 64 unique
sequences per batch and expects about 84 batched model calls rather than 21,408
redundant single-position calls.

No intervention, sampling, generation, protected target, or reserve input is
used.

## Contention-safe storage

Acquired items are frozen in source order and divided into 28 operational
shards of at most 32 items. A complete shard contains an FP32 `.npy` tensor,
JSONL observations, a receipt, and SHA-256 ledger; publication is atomic. The
runner checks for a foreign GPU compute PID before model loading and before
every next shard. If contention appears, it releases the model, retains only
complete hash-valid shards, and a later invocation skips validated shards.

Shard boundaries carry no scientific meaning and cannot be selected from
outcomes. All 28 are required before finalization. The approximately 3 GiB raw
atlas stays outside Git; Git receives only the frozen protocol and compact
receipts/summaries.

## Descriptive options, not decisions

The acquisition preserves enough information for several prespecified but
non-decisional summaries: paired cross-view retrieval, glyph–name versus
glyph–codepoint alignment, centered linear CKA, representational-distance
correlation, Unicode group/subgroup neighborhood purity, and exact token-length
strata. These summaries may help choose a later analysis, but none is a primary
T8 endpoint and none can convert discovery data into confirmation.

The clean next gate is to define one endpoint and multiplicity family using
only calibration/discovery data, freeze it, and then perform the first model
forwards on the 292-item reserve. Until then, this atlas supports exploratory
semantic decomposition only.

## Claim boundary

Successful acquisition establishes that a fixed, provenance-bound,
contention-resumable activation dataset exists for one model and runtime. Even
an appealing glyph–name pattern would not by itself identify semantic content,
tokenizer causality, a mechanism, behavior, architecture generality, or a Phase
I paper gate. Negative and heterogeneous patterns are retained at the same
granularity.
