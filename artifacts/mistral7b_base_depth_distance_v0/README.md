# Public evidence: Mistral 7B base depth-by-distance v0

[日本語](README.ja.md) · [Result](../../docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0_RESULTS.md) · [Frozen protocol](../../docs/MISTRAL7B_BASE_DEPTH_DISTANCE_V0.md)

This directory contains the complete compact evidence for protocol
`glyphprobe-mistral7b-base-depth-distance-v0`, prospectively frozen at commit
`25de47a5fb4c9eaf7674d5b2fa49f0c2cf84ca8b` before any T7 model forward.

The registered outcome is
`recurrence_and_early_depth_attenuation_excess`. Both fixed components reached
the 19,999-draw permutation floor and the one-model IUT rejected. This selected
post-T6 cell is not an independent confirmation or an instruction-tuning
effect test.

## Contents

- `runs/mistral7b_base_v03/`: complete activation array, ordered observations,
  run receipt, and internal ledger;
- `analysis/`: all 40 carrier-by-distance-by-depth rows, analysis receipt,
  report, and ledger;
- `TRANSFER_RECEIPT.json`: model-download, freeze-transfer, execution-start,
  result-return, and resource-release boundaries; and
- `PUBLIC_MANIFEST.json`: exact public payload sizes and SHA-256 values.

Replay integrity checks from the repository root with:

```bash
python scripts/mistral7b_base_depth_distance_v0.py validate-run \
  artifacts/mistral7b_base_depth_distance_v0/runs/mistral7b_base_v03
python scripts/mistral7b_base_depth_distance_v0.py validate-analysis \
  artifacts/mistral7b_base_depth_distance_v0/analysis
```

Successful validation establishes byte integrity and protocol conformance. It
does not establish semantics, mechanism, causality, instruction-tuning
invariance, checkpoint equivalence, model generality, confirmation, or Phase I
gate closure.
