# Public evidence: multifamily dense CUDA carrier-distance v0

[日本語](README.ja.md) · [Result](../../docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0_RESULTS.md) · [Frozen protocol](../../docs/MULTIFAMILY_DENSE_CUDA_CARRIER_DISTANCE_V0.md)

This directory contains the complete compact evidence for protocol
`glyphprobe-multifamily-dense-cuda-carrier-distance-v0`, prospectively frozen
at commit `5e2f4984486b5e5dc87b93f656d6e00bc8718baa` before any T6 model forward.

The predeclared outcome is `no_dense_model_distance_attenuation`. None of the
four model-level intersection-union tests survived Holm correction. Mistral 7B
showed a strong distance-1 recurrence component, but it did not pass the fixed
positive log-distance attenuation component.

## Contents

- `runs/`: complete activation arrays, ordered observations, receipts, and
  internal ledgers for Gemma 2 2B IT, Gemma 3 4B IT, Mistral 7B Instruct v0.3,
  and Gemma 3 12B IT;
- `analysis/`: all 160 carrier-by-distance-by-depth rows, joint receipt, report,
  and ledger;
- `TRANSFER_RECEIPT.json`: the frozen-source transfer, natural lifecycle start
  gate, furnace-to-mac2 return, and byte-verification boundary; and
- `PUBLIC_MANIFEST.json`: exact public payload sizes and SHA-256 values.

From the repository root, replay integrity checks with:

```bash
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma2_2b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma3_4b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/mistral7b_instruct_v03
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-run \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/runs/gemma3_12b_it
python scripts/multifamily_dense_cuda_carrier_distance_v0.py validate-analysis \
  artifacts/multifamily_dense_cuda_carrier_distance_v0/analysis
```

Successful validation establishes byte integrity and protocol conformance. It
does not establish monotonic decay, persistence duration, semantics, a causal
mechanism, tokenizer equivalence or causality, backend or node equivalence,
model-scale or precision effects, confirmation, or Phase I gate closure.
