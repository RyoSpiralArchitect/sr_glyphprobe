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

The legacy v1 bundle omits one 77,327,172-byte condition ledger and three NPZ arrays, as recorded in `MANIFEST.json`. Separately, `MILESTONE2_MANIFEST.json` records 58 omitted large local files across 14 runs, including condition ledgers and model-dependent NPZ arrays, plus two 20,000-replicate bootstrap tables. Their hashes bind the audited local artifacts but cannot reconstruct them. Reproduce the applicable run or analysis to recover the complete data.

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
normally. C1 remains untouched.

These artifacts support a reproducible pre-causal activation-screening
candidate and a mixed Milestone 2 control result. They do not establish glyph
semantics, a mechanism, a circuit, a causal path, or a tokenization-free effect.
Operational Milestone 2 is complete, and layer 2 is eligible for targeted
causal-protocol design using untouched C1; layer 4 remains unresolved.
