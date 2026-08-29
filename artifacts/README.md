# Public evidence bundle

[日本語](README.ja.md)

This directory contains the compact, path-scrubbed evidence selected for the GlyphProbe research releases.

- `mlx_gpt2_parity/receipt.json` records the pinned GPT-2 FP32 MLX-versus-Transformers/MPS parity and speed gate.
- `v1_standard_mlx/` contains the completed run receipt, summaries, compact diagnostic tables, report, and independent artifact audit.
- `MANIFEST.json` binds every included file by SHA-256 and records the hashes of the large local artifacts omitted from Git.
- `milestone2/` contains the frozen protocol evidence, exact input-binding audit,
  compact exploratory, confirmatory, and secondary-diagnostic run artifacts,
  the confirmatory analyses, and post-hoc sensitivity analyses.
- `MILESTONE2_MANIFEST.json` binds the compact Milestone 2 bundle and records
  completed diagnostics and omitted raw files.
- `milestone2/analyses/posthoc_dependence/p2/` and
  `milestone2/analyses/posthoc_dependence/independent_source/` contain the
  separate analysis that rebuilds leave-one-target-group-out prototypes inside
  every target-bootstrap replicate.
- `milestone2/analyses/diagnostics/` contains the suffix-matched and
  prefix-homogeneous paired comparisons and same-seed dimension folds.
- `emoji_family_exploratory_v1/` contains the E1 tokenizer preflight, complete
  descriptive analysis, and 15 compact files for each of five family runs.
- `EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json` binds all 82 E1 payload members by
  SHA-256 and inventories the omitted raw ledgers and arrays. With this root
  manifest, the public E1 artifact contains 83 files.
- `multifamily_tokenizer_census_v0/` contains the verified post-hoc descriptive
  aggregate, collection receipt, compact checksum ledger, and the three source
  node path-scrubbed receipt and summary copies. Each node has a public
  `SHA256SUMS` and a distinctly named original-source `SOURCE_SHA256SUMS`. The
  raw JSONL tables are omitted but bound by exact hashes and row counts.
- `multifamily_colored_shape_geometry_v0/` contains both complete compact
  activation runs, all ten fixed-depth analysis rows, the two-cell exact-test
  decision, three-point OLMo transfer verification, and a public payload
  manifest. No raw array from this study is omitted.
- `semantic_atlas_cross_model_replication_v0/` contains T10's nine compact
  prediction sets, all primary and secondary cell metrics, run/summary/session
  receipts, nested raw-shard ledger bindings, independent validation, and a
  public manifest. Raw activations and model weights remain outside Git.
- `glyph_system_decomposition_v0/` contains T11's compact joint analysis,
  cross-model geometry and agreement tables, an independent recomputation of
  item margins, agreement, variance, and depth trajectories, bilingual reading
  guides, and checksum-bound manifests. The dense activation arrays remain
  outside Git.
- `glyph_system_reserve_confirmation_v0/` contains T12's frozen design,
  nine tokenizer preflights, nine run receipts and shard indexes, 432
  item-contrast rows, the two-hypothesis joint decision, and an independent
  recomputation of all stored statistics and gates. Raw activations remain
  outside Git and SpiralShare.
- `emoji_steering_specificity_analysis_v0/` contains T13-EA's deterministic
  F1–F6 reporting synthesis, bilingual reading guide, public manifest, and
  checksum ledger. The six 104,583,753-byte derived source outputs and the
  4,535,141,572-byte furnace archive remain outside Git; raw arrays were not
  copied to Git or SpiralShare.
- `llama32_3b_mps_emoji_transport_v2/` is the separately versioned E2 MPS
  evidence root. At static freeze it contains only its bilingual orientation;
  no analysis tree means no valid scientific result has been published.
- `../validation/llama32_3b_mps_emoji_transport_v1/preflight_failure_receipt.json`
  records the retired v1 tokenizer-preflight failure. It occurred before model
  weight loading or any model forward and is not scientific outcome evidence.

The legacy v1 bundle omits one 77,327,172-byte condition ledger and three NPZ arrays, as recorded in `MANIFEST.json`. Separately, `MILESTONE2_MANIFEST.json` records 58 omitted large local files across 14 runs, including condition ledgers and model-dependent NPZ arrays, plus two 20,000-replicate bootstrap tables. Their hashes bind the audited local artifacts but cannot reconstruct them. Reproduce the applicable run or analysis to recover the complete data.

## Multifamily tokenizer census reading

The census completed all 14 frozen tokenizer entries and grouped them into
seven exact output classes on the fixed 115-item, four-context surface. It found
no single fixed-panel candidate for either blue circle or blue square that
matched both token count and a one-token prefix across every output class in
any fixed pairwise context. This is tokenizer-only, post-hoc descriptive
control-design evidence. It does not update Milestone 2, establish
tokenizer-independent structure, or close a paper gate. See the [full bounded
result](../docs/MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md).

## Multifamily colored-shape geometry reading

The frozen Gemma 2 2B 4-bit and OLMo 3 7B BF16 midpoint tests both failed to
reject after the predeclared two-cell Holm correction. Gemma produced
`T = 0.114857969`, adjusted `p = 0.116666667`; OLMo produced
`T = 0.024628040`, adjusted `p = 0.275`. The registered outcome is
`no_dual_model_recurrence`.

All eight non-primary layer rows remain visible but have no multiplicity
decision. Model family, scale, precision, tokenizer, and node are confounded,
so this is bounded negative/mixed observational evidence rather than a scale,
quantization, model-general, semantic, or causal result. See the [complete T2
result](../docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md).

## Semantic-atlas cross-model reading

T10 completed all nine frozen model/tokenizer cells. The four-core statistical
partial conjunction passed (`p = 0.0001`), but only two core cells met the
registered practical floor in both unrestricted and exact-token-count-matched
components. The primary outcome is therefore
`cross_model_replication_not_established_under_frozen_rule`.

The independent validator reproduced all component tests, IUTs, Holm values,
and the partial conjunction, and rehashed 1,350 external raw-ledger targets.
Exact token-count matching did not erase the contrast, but T10 does not
establish tokenizer independence, scale, tuning, semantics, causality,
independent replication, or model generality. See the [complete T10 result](../docs/SEMANTIC_ATLAS_CROSS_MODEL_REPLICATION_V0_RESULTS.md).

## T11 glyph-system decomposition reading

T11 completed all nine frozen model/tokenizer cells: 477 shards, 73,566 model
forwards, and 982,512 FP32 readout vectors. Every required exact
target-token-length control passed, while the separately assigned 268-item
reserve was unforwarded at T11 completion. Returned-final glyph/name margins were positive
in all 72 cells for presentation, modifier, ZWJ, and regional systems and in
65/72 keycap cells.

The narrowest follow-up candidate is the ZWJ `presentation_or_fusion` contrast,
positive in 65/72 cells. Regional flags showed a secondary dual whole-name and
component pattern. Cross-model item agreement was weak, strict first-token
coverage was sparse for some systems, and only 8/36 ordered Qwen profiles were
strictly increasing. The public bundle therefore supports an exploratory,
model-conditioned atlas—not semantics, causality, tokenizer independence, a
scale law, tuning, or model generality. The independent validator reports
`share_with_caveats`; it fully recomputes stored item margins, agreement,
variance decompositions, and depth trajectories, while geometry is
hash/schema-checked because its recomputation requires the omitted dense
arrays. See the [complete T11 result](../docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md).

## T12 reserve-confirmation reading

T12 separately froze and acquired the complete ZWJ (96 items) and regional-flag
(64 items) reserve subsets across all nine roles and eight contexts. All 90
shards, 9,792 model forwards, and 39,168 FP32 returned-final vectors completed.
Neither registered hypothesis was confirmed.

ZWJ presentation/fusion had statistic `0.000369`, raw `p = 0.05496`, and Holm
`p = 0.10992`. Regional presentation/fusion was directionally weak
(`0.002767`, component `p = 0.03538`), but component tracking was `0.000666`,
`p = 0.12950`; the regional intersection-union/Holm result was therefore
`p = 0.12950`. No model summary reached any frozen practical floor. The
independent validator reconstructed all 432 cell medians, reran the three
49,999-draw tests, and recomputed every gate with zero mismatches.

The bundle is rated `share_with_caveats`: omitted raw activations are hash-bound
but not independently reconstructed. This is a one-shot negative confirmation,
not a semantic null, causal result, behavioral-steering result, tokenizer-
independent effect, scale law, or model-general claim. See the [complete T12
result](../docs/GLYPH_SYSTEM_RESERVE_CONFIRMATION_V0_RESULTS.md).

## T13-EA specificity-analysis reading

T13-EA completed the registered F1–F6 exploratory point analysis. The
three-model intervention pilot shows structured, depth- and system-dependent
source-form effects, but the signal is not glyph-unique: Unicode names,
decomposed forms, and codepoint literals can also separate from the limited
positive-isotropic null. Generic target fragility, large wrapper variation,
and count-signature-only tokenizer evidence remain competing explanations.

The original exact-JS zero gate failed closed before nonzero scientific values
were opened. That failure is preserved separately from a later bounded-float32
JS amendment. The compact summary reproduces the reported point aggregates and
authenticates all six source outputs, but it does not include intervals. The
registered bootstrap remains at 0/20,000, and exact token/prefix controls,
signed matched nulls, untouched confirmation targets, remaining-model response
replication, and generation endpoints remain open. See the [complete T13-EA
result](../docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md).

## Milestone 2 reading

Frozen v1 classified layer 2 as robust to the prespecified token-count and
prefix-panel matched controls in the primary-source arm (+0.208363, 95% CI
[0.137463, 0.276893], Holm p = 0.00143999) and independent-source arm
(+0.187507, [0.125489, 0.247659], p = 0.00393996). Layer 4 was unresolved in
both arms (-0.0329465, [-0.0761085, 0.0110094], and -0.086379,
[-0.159246, -0.016917]). See [Milestone 2 results](../docs/MILESTONE2_RESULTS.md).

The controls match token count and panel-level prefix structure, not token
identity; panel C includes the declared `🟥` semantic-near control. The v1
analyzer assigns panel roles from CLI order, so the separate
`milestone2/input_binding_audit.json` provides exact frozen role binding. Its
bootstrap also resamples fixed target effects rather than rebuilding prototypes.
The post-hoc sensitivity receipts address the latter dependence descriptively,
assign no confirmatory status, and do not overwrite v1.

The exploratory 96-dimensional paired median difference was +0.047427, with
25/36 cells positive. Its 48/32/24-dimensional values (+0.040200/+0.028907/
+0.048591) are same-seed algebraic folds, not sketch-seed sensitivity. No
percent-explained estimate is authorized. The suffix and prefix-homogeneous
diagnostics each completed 14,208 rows with zero errors, zero-hook activation/logit RMS of 0,
and readiness 11/11. Their random-adjusted headline advantages were +0.751225
and +0.601038, respectively; these are not the raw separation scores below.
The descriptive standard-minus-suffix medians at dimensions 96/48/32/24 were
+0.002624/+0.009473/+0.004026/+0.009700, while the standard-minus-prefix values
were +0.022096/+0.023254/+0.011040/+0.025387. At 96 dimensions, 20/36 and
25/36 cells were positive, respectively. These are post-hoc descriptive
diagnostics, not inference or equivalence tests; the lower dimensions are
same-seed algebraic folds.

For runtime provenance, the first matched-null A foreground process was
externally interrupted after 798 ledger rows during severe machine load. A
sealed resume completed the exact 14,208-row grid without duplicates, missing
rows, or errors, with zero-hook activation/logit RMS at 0. This event is not model evidence or a
universal speed claim. P2, independent-source, and diagnostic runs completed
normally. Milestone 2 did not use C1 v1, but the bank is now retired after the
separately documented research-context exposure.

These artifacts support a reproducible pre-causal activation-screening
candidate and a mixed Milestone 2 control result. They do not establish glyph
semantics, a mechanism, a circuit, a causal path, or a tokenization-free effect.
Operational Milestone 2 is complete, and layer 2 is eligible for targeted
causal-protocol design with a future new versioned bank; layer 4 remains
unresolved. See [Holdout status](../docs/HOLDOUT_STATUS.md).

## E1 exploratory reading

The [complete E1 result](../docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md) reports a
token-isomorphic five-family side experiment frozen at commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558`. The complete mean transfer matrix
was broadly positive at both layers, while the family-equal within-family excess
was small: 0.014752595564 at layer 2, with a 95% descriptive interval of
[0.002875238085, 0.027439243404], and 0.014887989201 at layer 4, with
[0.003407563347, 0.019684351979]. Every family-specific interval included zero
at both layers. The prespecified layer-4 negative comparator was not negative.

Random-control comparison was heterogeneous. Ten of 30 family × layer × seed
cells were non-positive: all five families at layer 2 seed 307 and all five at
layer 4 seed 101. This does not support robust superiority over random controls.
The bounded interpretation is exploratory matched-slot recurrence under a fixed
middle-token family substitution, with shared-token transfer dominating the
small family-specific excess.

The bundle validator passes with 82/82 public payload members and five verified role
bindings. It found no hash mismatch or local absolute path and validated the
manifest declaration that P2 and C1 were outside the fixed E1 input surface;
this is not an independent proof of process history. The bundle contains
1,237,638 payload bytes, including 39 JSONL files with 1,635 compact rows. With
the root manifest it contains 83 files and 1,303,644 bytes. The manifest SHA-256
is `c22989ebc9ccaaf5f4652624d61ea11e2a9df4f2148a7886daf50c2fc3e4f53f`. It inventories
20 omitted raw files totaling 74,618,134 bytes, including all 8,880 intervention
rows, by hash, row count, and array shape as applicable. Those omissions cannot
be reconstructed from hashes.

The evidence is organized as follows:

- [root manifest](EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json);
- [tokenizer-only preflight](emoji_family_exploratory_v1/preflight/tokenization_audit_v1.json);
- [analysis report and machine-readable outputs](emoji_family_exploratory_v1/analysis/report.md);
- [five compact run directories](emoji_family_exploratory_v1/runs/).

E1 computes no p-values or confirmatory status. It does not establish emoji
semantics, tokenizer independence, layer specificity, a mechanism, a causal
path, or cross-model regularity. It does not update Milestone 2, unseal C1, or
satisfy a Phase I paper gate.
