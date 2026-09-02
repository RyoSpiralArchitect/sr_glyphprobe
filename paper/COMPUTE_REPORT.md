# Compute report

[日本語](COMPUTE_REPORT.ja.md)

Status: **compact T19/T20/T21 accounting complete; T19 acquisition duration and
memory accounting incomplete**. No model weights were trained or fine-tuned;
T20-C trained only 3072-by-8 subspace parameters per site.

## Recorded execution environment

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
| T19-C post-hoc ceiling (descriptive) | 2,304 model forward calls; 2,304 intervention rows | none | Computed after the registered decision; labeled post-hoc; cannot change the recorded outcome. |
| T20-C training | 384 capture forward calls; 33,048 batched training passes (gradients reach only the rank-8 subspace parameters); recorded stage duration 14.7 min | validation scoring on 32 held-out source items | Source-bank forwards only; zero evaluation forwards at admission re-verified. |
| T20-C evaluation | 32,256 model forward calls; 124,416 intervention rows; recorded stage duration 7.3 min | 99,999 sign flips and 20,000 item-bootstrap replicates for each of 18 component tests | All nine engineering gates exact; the independent validator re-derived every value and both registered verdicts. |

The T19/T20 forward counts describe calls under the specified batch-size-one protocol,
not FLOPs. The causal intervention rows are not additional training examples.
The experiment issued no generation calls.

## T21 acquisition accounting

| Stage | Target items | Batched calls | Sequence forwards | Recorded wall time |
| --- | ---: | ---: | ---: | ---: |
| Original exposed-item canary | 8 | 850 | 3,634 | 19.48 s |
| Exposed-item pilot | 384 | 4,610 | 138,242 | 218.87 s |
| Confirmation-runner canary, same exposed items | 8 | 850 | 3,634 | 19.73 s |
| Prospective confirmation | 195 | 2,720 | 70,580 | 118.50 s |

These counts include source capture and stock-attention parity checks.
Intervention forwards use 88 rows per carrier; each has a same-slot neutral
forward. The canaries repeat existing items and do not increase the scientific
sample size. No new model assets, model-weight training, or generation were
needed. Wall times include loading, acquisition, and output work, not just
GPU kernels. T21 peak memory and energy use were not recorded.

Primary confirmation inference uses 20,000 shared-index item-bootstrap draws.
Independent reconstruction also rederives the intervals from the retained
states. The anonymous package includes 195 item-level scalar contrasts and a
NumPy-only statistical validator; raw model-state replay remains a separate
step requiring omitted arrays.

## Post-review CPU audit

The 2026-09-02 review pass used retained outputs only, on the same Linux worker
with NumPy 2.5.2. T21 reconstruction used a four-thread BLAS/OpenMP cap; the
T19 replay used a two-thread cap. It reconstructed 13 T21 chunks and ten metric
arrays, exported all 195 items' margin components, replayed all 36 T19
randomization tests and 36 bootstrap intervals, and reconstructed 27 T20
training histories and nine checkpoint choices. This added zero model
forwards, generation calls, and component significance tests. No GPU compute
was requested. Per-stage CPU timing and peak memory were not separately
instrumented, so no speedup or total-compute estimate is claimed.

The T19 compact predictions, T20 selection audit, and T21 descriptive
decomposition are included from archive v3 onward; raw states remain excluded.

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
