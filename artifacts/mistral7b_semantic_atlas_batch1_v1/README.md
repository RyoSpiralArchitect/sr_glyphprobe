# Mistral 7B semantic atlas batch-one v1 evidence

[日本語](README.ja.md) · [Results](../../docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1_RESULTS.md) · [Protocol](../../docs/MISTRAL7B_SEMANTIC_ATLAS_BATCH1_V1.md)

This compact bundle binds the canonical 892-item batch-one acquisition,
bit-exact capture validation, complete 144-cell descriptive analysis, failed
batch-64 validation, aggregate batch-shape sensitivity, and 576-cell
token-structure sensitivity.

The canonical run contains 5,352 model forwards and 192,672 FP32 residual
vectors over three views, two carriers, four distances, and nine layers. All 28
raw shards validated. The fixed 18-case batch-one recapture was bit-exact. The
292-item reserve received zero model forwards.

Raw activations (~3 GiB) and 64,224 item-level analysis rows are intentionally
outside Git. This bundle retains the run/session receipts, both capture
validation receipts, all aggregate cell rows, layer summaries, and their exact
hashes. `PUBLIC_MANIFEST.json` is the machine-readable entry point.

The evidence supports an exploratory late-depth glyph/name alignment candidate,
not semantic causality, a mechanism, confirmation, model generality, or a Phase
I paper gate.
