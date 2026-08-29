# T11 glyph-system decomposition atlas evidence

[日本語](README.ja.md) · [Interpretation](../../docs/GLYPH_SYSTEM_DECOMPOSITION_V0_RESULTS.md) · [Frozen protocol](../../docs/GLYPH_SYSTEM_DECOMPOSITION_V0.md)

This directory contains the compact public evidence for the completed T11
discovery atlas. The result is exploratory and is assessed as **share with
caveats**. It does not alter T10 and does not authorize a semantic, causal,
tokenizer-independent, scale-law, tuning, architecture-general, or
model-general claim.

## What is included

- `analysis/analysis.json` contains the nine-cell context summaries, input
  receipt bindings, variance decompositions, and claim-boundary flags.
- `analysis/cross_model_geometry.jsonl` contains 1,040 descriptive geometry
  rows.
- `analysis/cross_model_item_margin_agreement.jsonl` contains 720 model-pair
  item-margin agreement rows.
- `validation/independent_validation.json` contains the independently rebuilt
  headline tables and input bindings.
- Both subdirectories and the bundle root have SHA-256 ledgers.
- `PUBLIC_MANIFEST.json` inventories the included payload, omitted compact
  tables, external summary/run bindings, and the raw-archive omission.

The independent validator recomputed 32,736 stored item-margin cell medians,
720 cross-model agreement rows, seven balanced variance decompositions, and
2,592 depth trajectories with zero mismatches. Cross-model activation geometry
was hash- and schema-checked but was not independently reconstructed because
that requires the omitted raw activation archive.

## What is omitted

The 1,008-row broad cell table, 2,592-row depth cell table, and 2,592-row depth
trajectory table are omitted from Git but retained by exact hash and byte count
in the public manifest. The nine per-model item-margin NPZ files, acquisition
runs, model caches, and approximately 9.15 GiB of dense FP32 activations remain
outside Git. Hashes bind those inputs but cannot reconstruct omitted data.

The public bundle is therefore sufficient to audit the reported aggregate
patterns and the independent compact validation, not to independently rebuild
the activation-geometry rows from raw vectors.

## Frozen boundary

T11 used 843 acquired items and 73,566 model forwards across the same nine
model/tokenizer cells frozen for T10. The analysis itself performed zero model
forwards. All 268 reserve items remain unforwarded and their model outcomes
remain uninspected. A later T12 must freeze one endpoint and multiplicity
family before any reserve outcome is opened.
