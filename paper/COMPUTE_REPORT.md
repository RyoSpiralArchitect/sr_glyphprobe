# Compute report

[日本語](COMPUTE_REPORT.ja.md)

Status: **compact T19 accounting complete; acquisition duration and memory
accounting incomplete**. No model was trained or fine-tuned.

## Frozen execution environment

| Field | Recorded value |
|---|---|
| Worker | One CUDA-capable Linux worker |
| GPU | NVIDIA GeForce RTX 5090 |
| Backend | Transformers / CUDA |
| Activation and model compute dtype | BF16 model execution; stored activation arrays were `float32` |
| PyTorch | `2.13.0+cu132` |
| Transformers | `5.15.0` |
| NumPy | `2.5.2` |
| PyYAML | `6.0.3` |
| Remote code | disabled (`trust_remote_code: false`) |
| Model cache | local-only; nine pinned artifacts |

The exact model identifiers, 40-character revisions, expected layer counts,
widths, and parameter counts are in
`configs/semantic_atlas_cross_model_replication_v0.yaml`. The identifier of the
Llama mirror does not describe the execution backend: its frozen safetensors
were loaded through Transformers/CUDA.

## T19 work accounting

| Stage | Model work | Statistical work | What the receipt establishes |
|---|---:|---:|---|
| T19-L observational acquisition | 7,920 batch-one model forward calls; 285,120 readout vectors; 45 sealed shards | none during acquisition | Exact count and shape reconstruction passed in the independent validator. |
| T19-L analysis | 0 model forwards; 0 interventions | 19,999 randomization draws and 20,000 item-bootstrap replicates per registered component | Compact analysis elapsed time: 6.7235 s. This is analysis time only, not acquisition time. |
| T19-C source construction | 256 model forward calls | rank-8 QR/SVD construction at six sites | Source and evaluation banks were disjoint; source work preceded no evaluation intervention. |
| T19-C evaluation | 2,880 model forward calls; 8,064 intervention rows | 99,999 sign flips and 20,000 item-bootstrap replicates for each of 12 component tests | All six engineering gates and all 12 statistical reconstructions passed the independent validator. |

The forward counts describe calls under the frozen batch-size-one protocol,
not FLOPs. The causal intervention rows are not additional training examples.
The experiment issued no generation calls.

## Known omissions

The compact T19 receipts do **not** preserve acquisition wall-clock duration,
peak CUDA memory, CPU model, system RAM, raw scratch storage, or energy use.
They also do not aggregate the compute consumed by the exploratory T9--T18
studies that motivated T19. Earlier T10 engineering receipts contain some
per-model timings and peak-memory values, but substituting them for T19 would
be an unsupported estimate because the input and readout workloads differ.

For this reason the NeurIPS compute-resources checklist answer remains
**No**. This report supplies the exact facts that are available and marks the
smallest missing evidence rather than reconstructing duration or memory after
the run.
