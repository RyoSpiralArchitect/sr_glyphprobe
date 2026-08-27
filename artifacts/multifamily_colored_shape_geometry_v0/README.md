# Multifamily colored-shape geometry v0 evidence

[日本語](README.ja.md) · [Full result](../../docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0_RESULTS.md) · [Frozen protocol](../../docs/MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.md)

This directory is the complete compact evidence bundle for protocol
`glyphprobe-multifamily-colored-shape-geometry-v0`, frozen at commit
`dc78756bd8f26ae0060463e459d5deb40c47d750`.

## Contents

- `runs/gemma2_2b_4bit/`: ten raw-glyph forwards and the sealed
  `10 × 5 × 2304` activation array;
- `runs/olmo3_7b_bf16/`: ten raw-glyph forwards and the sealed
  `10 × 5 × 4096` activation array;
- `analysis/`: all ten fixed-depth rows, the two-cell primary decision, a
  compact report, and a sealed checksum ledger; and
- `OLMO_TRANSFER_RECEIPT.json`: the four source, relay, and destination hashes;
  and
- `PUBLIC_MANIFEST.json`: hashes and sizes for all thirteen generated evidence
  files, plus the transfer and validation status.

Every run and analysis directory has its own `SHA256SUMS`. The OLMo directory
was verified byte-for-byte at mac1, the furnace relay, and mac2 before joint
analysis. All three generated bundles passed the frozen validators after
publication into this directory.

The primary outcome is `no_dual_model_recurrence`: Gemma's midpoint result was
positive but did not reject after Holm correction (`T = 0.114857969`, adjusted
`p = 0.116666667`), and OLMo also did not reject (`T = 0.024628040`, adjusted
`p = 0.275`). Non-primary layers are descriptive only.

The bundle proves integrity and replayability of this observational cell. It
does not establish semantics, mechanism, causality, backend parity,
quantization equivalence, a scale effect, or scientific confirmation.
