# Mistral 7B semantic atlas reserve confirmation v0

[日本語](MISTRAL7B_SEMANTIC_ATLAS_RESERVE_CONFIRMATION_V0.ja.md) · [Discovery result](MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md)

Status: **prospectively specified; execution is forbidden until the freeze
manifest is committed. Zero reserve model inputs have been forwarded in the
recorded atlas lineage**.

## Question

Does the late-depth glyph/name alignment candidate reproduce in the 292-item
deterministic reserve that received no model forward during T8 discovery?

This protocol tests one narrow statement: at Mistral 7B v0.3 layer 31, correct
official-name retrieval from glyph residuals exceeds literal `U+...` codepoint
retrieval across the complete two-carrier by four-distance transport grid.

## Fixed population and acquisition

The population is every item whose pre-existing selection role is
`reserved_unrun`, ordered by ascending source index. There are 292 items. No
item may be replaced, excluded, or added after the freeze.

Only the already selected endpoint is acquired:

- views: exact glyph, official Unicode name, and uppercase `U+...` literal;
- carriers: `" a"` and `" |"`, each repeated eight times;
- causal readout distances: 1, 2, 4, and 8;
- site and depth: `resid_post`, layer 31 only;
- batch size: one unique sequence per forward; and
- expected total: 1,752 forwards and 7,008 FP32 vectors in ten item shards.

Each shard writes an intent record before its first forward. Completed shards
are never reacquired. A partial shard means that duplicate-free execution can
no longer be inferred automatically; the protocol then stops for manual
adjudication rather than silently rerunning those items.

## Single primary endpoint

For each of the eight carrier-distance cells, features are centered across the
292 items separately by view and then row-L2 normalized. Glyph rows query the
official-name and codepoint target matrices. Ties follow deterministic first
`argmax` behavior.

Let each cell contrast be:

`glyph→name forward top-1 accuracy - glyph→codepoint forward top-1 accuracy`.

The single global statistic is the minimum of these eight contrasts. This
avoids selecting a favorable carrier or distance and turns the full grid into
one conjunction-like endpoint.

The one-sided null uses 19,999 deterministic randomizations with NumPy seed
`20260828`. Each draw applies one common random permutation of official-name
item correspondence across all eight cells, retains the observed codepoint
control, and recomputes the minimum contrast. The p-value is
`(1 + exceedances) / 20,000`.

The outcome is
`transport_robust_late_depth_glyph_name_alignment_confirmed` only when both:

1. the randomization p-value is at most `0.05`; and
2. the observed minimum eight-cell contrast is at least `0.02`.

Every other complete result is
`not_confirmed_under_frozen_rule`. This is one global test, so there is no
additional multiplicity correction. The `0.02` practical floor was fixed below
one quarter of the weakest discovery-cell contrast (`0.080760095`) before any
reserve forward.

## Secondary outputs and claim boundary

All eight cell values, reverse retrieval, mean reciprocal rank, paired cosine
margin, and centered linear CKA are reported descriptively. They cannot rescue
or replace the primary rule. Token-length strata may be tabulated but cannot
alter the decision.

A positive result confirms a transport-robust, item-specific glyph/name
alignment in one frozen model and layer. It does not establish human-readable
emoji meaning, tokenization causality, a causal mechanism, behavior, model
generality, or an entire Phase I paper claim. A negative result closes the same
narrow question without outcome-guided redesign.

Model-family replication and unusual-glyph exploration begin only after this
reserve result and its evidence bundle are sealed.
