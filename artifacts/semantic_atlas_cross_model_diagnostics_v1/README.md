# T10 cross-model diagnostic evidence v1

[日本語](README.ja.md) · [Interpretation](../../docs/SEMANTIC_ATLAS_CROSS_MODEL_DIAGNOSTICS_V1.md)

This directory contains the compact, generated T10-D diagnostic output. It was
computed with zero new model forwards from the Git-resident T10 bundle and the
returned 333-shard FP32 archive.

- `diagnostics.json` contains machine-readable diagnostics, input hashes, raw
  run-ledger hashes, reconstruction checks, and claim-boundary flags.
- `report.md` is the generated short report.
- `SHA256SUMS` binds both generated files.

The output reconstructs 36 prediction arrays and 84,096 prediction values with
zero mismatches. It is retrospective and descriptive. The registered T10
primary remains negative under its frozen combined rule.
