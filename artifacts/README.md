# Public evidence bundle

[日本語](README.ja.md)

This directory contains the compact, path-scrubbed evidence selected for the first GlyphProbe release.

- `mlx_gpt2_parity/receipt.json` records the pinned GPT-2 FP32 MLX-versus-Transformers/MPS parity and speed gate.
- `v1_standard_mlx/` contains the completed run receipt, summaries, compact diagnostic tables, report, and independent artifact audit.
- `MANIFEST.json` binds every included file by SHA-256 and records the hashes of the large local artifacts omitted from Git.

The 77,327,172-byte condition ledger and three NPZ arrays are not included. Their hashes attest which local artifacts were audited; hashes cannot reconstruct missing data. Reproduce the run to obtain the complete ledger.

These artifacts support a reproducible pre-causal activation-screening candidate. They do not establish glyph semantics, a circuit, or a causal path.
