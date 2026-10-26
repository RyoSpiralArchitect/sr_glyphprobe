# Compute report

[日本語](COMPUTE_REPORT.ja.md)

Status, October 15: **new readout acquisition complete; historical compact
T19/T20/T21 accounting retained; T19 acquisition duration and memory accounting
incomplete**. No model weights were trained or fine-tuned;
T20-C trained only 3072-by-8 subspace parameters per site.

## Historical recorded execution environment

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
| T19-C post-hoc full-state reference swap (descriptive) | 2,304 model forward calls; 2,304 intervention rows | none | Computed after the registered decision; labeled post-hoc; cannot change the recorded outcome or establish a universal upper bound. |
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

## October 10 working-draft extension

The contextual matched-execution inventory rescored 624 candidate pairs
(1,248 scientific sequence scores plus 64 historical checks: 1,312 forwards).
The subsequent two-track development acquisition completed 1,632 candidate
pairs (3,264 sequences plus 32 checks: 3,296 forwards). The latter took
638.744943 seconds on the recorded RTX 5090, with peak Torch allocated/reserved
memory of 6,195.231/6,318 MiB. Both stages reuse 24 scenarios and six families;
neither increases independent scenario N. They use Llama 3.2 3B base BF16 via
Transformers/CUDA with eager attention. No weights are trained and no free
generation occurs.

The [working-draft aggregate](../validation/contextual_emoji_working_revision_20261010/summary.json)
binds these counts to completed records. The October 10 note/manuscript update
recalculates saved data locally and adds zero model forwards, tokenizer calls,
or GPU work. Its writing/CPU time is not separately instrumented. These figures
are not an accounting of the entire contextual development programme and do
not fill historical timing, memory, energy, or carbon gaps.

## October 15 explicit-report qualification

The [prospective specification](../docs/READOUT_QUALIFICATION_V1.md) fixes
32 new text-only roots in four authored families, split into 16 development and
16 reserved-check roots. Three report states, two asserted polarities, three
question forms, and four answer formats give 2,304 candidate pairs: 4,608
scientific sequence forwards plus 32 historical sentinel forwards, or 4,640
planned forwards. These repeated conditions do not constitute 2,304 independent
tasks. The model, runtime, and complete tokenized inventory are bound by the
[prepared specification](../validation/readout_qualification_v1/specification.json),
SHA-256 `5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f`.

Execution uses the already cached `mlx-community/Llama-3.2-3B-bf16` checkpoint,
revision `60a99aaf43164077157d64bf909b7b61143c6a6d`, through Transformers/CUDA
BF16 with eager attention. The mirror's name does not imply MLX execution.
No model download, weight training, free generation, private author record, or
protected historical holdout is part of this acquisition. The historical
exact-logit scorer is required for sentinel comparability; no managed runtime
is changed to accommodate it.

The fixed limits were 1,800 seconds, 9,728 MiB Torch allocator memory plus a
512 MiB driver allowance, and no concurrent foreign GPU process. Occupancy is
checked at forward boundaries; stopping preserves the planned/completed/missing
denominators.

The acquisition completed all **4,640/4,640 forwards and 2,304/2,304 pairs**,
with zero missing pairs, in **889.365958 seconds** (approximately 14.82 minutes).
Recorded peak Torch allocated/reserved memory was **6,195.228/6,312 MiB**.
These are run wall time and allocator measurements, not kernel-only timing,
whole-system peak memory, energy, or carbon estimates. Download, weight-training,
and free-generation counts are zero. The run stopped normally without a
contention stop or automatic retry.

The [completion record](../validation/readout_qualification_v1/run4640/run_completed.json)
reports numerical acceptance. The [separate arithmetic validator](../validation/readout_qualification_v1/independent_validation.json)
reconstructs all 4,640 scheduled rows and 2,304 pairs from saved scores, with
zero model forwards and tokenizer calls. It agrees with both failed finite-set
qualification decisions; numerical acceptance is not qualification success.
The [manuscript projection](generated/readout_qualification_20261015/summary.json)
retains every split/form group, report-state strata, ties, and root summaries.
CPU verification and writing time were not separately instrumented. Historical
compute omissions remain unchanged.

## Known omissions

The compact T19 receipts do **not** preserve acquisition wall-clock duration,
peak CUDA memory, CPU model, system RAM, raw scratch storage, or energy use.
They also do not aggregate the compute consumed by the exploratory T9--T18
studies that motivated T19. Earlier T10 engineering receipts contain some
per-model timings and peak-memory values, but substituting them for T19 would
be an unsupported estimate because the input and readout workloads differ.

For this reason the historical NeurIPS submission's compute-resources checklist
answer was **No**. The standalone preprint omits that submission checklist;
these compute-accounting gaps remain. This report supplies the exact facts
that are available and marks the smallest missing evidence rather than
reconstructing duration or memory after the run.
