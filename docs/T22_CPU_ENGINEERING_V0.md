# T22 CPU engineering path

[日本語](T22_CPU_ENGINEERING_V0.ja.md) | [Initial K/V decision](T22_KV_DISSECTION_FIRST_STEP_V0.md)

Status: **CPU reacquisition path; historical GPU replay remains a separate
blocked operation**. This extends the earlier availability assessment without
changing any T19/T20/T21 result, gate, or saved receipt. Engineering parity is
not evidence of an emoji lexical effect.

Subsequent status: the separate [eight-item lexical analysis](T22_CPU_LEXICAL_RESULTS_V0.md)
is complete. This document records the engineering stage and its boundaries.
The eight parent arrays and receipts are now also archived at
`validation/t22_cpu_engineering_v0/canary/` for portable numerical auditing.

## What the repository preserves

The T21 pilot specification fixes the model
`mlx-community/Llama-3.2-3B-bf16` at revision
`60a99aaf43164077157d64bf909b7b61143c6a6d` and all nine model files' sizes
and SHA-256 values. Their total size is 6,434,705,789 bytes and the manifest
SHA-256 is `dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`.
The fixed token sequences and two donors for each exposed canary item are
also preserved. No protected target-bank scan or fresh-item selection is needed.

T21's original `source_states.npz` and canary `states.npz` are not tracked.
Their acquisition receipts bind hashes; hashes do not reconstruct the arrays.
Other studies do include NPZ files in the repository, and those must not be
confused with the omitted T21 arrays.

## Current access and CPU resources

The user-supplied SSH destination is a private LAN address. A strict-host-key,
batch-mode connection from this cloud returned **Connection refused**, before
authentication or host-key verification. The named known-hosts file is absent
here. The machine's default SSH include also has an ownership problem; the
connection test used an empty client configuration while retaining explicit
`StrictHostKeyChecking=yes`. No host-key check was disabled and no system
configuration was changed. This result does not determine whether the server
is reachable from the user's own LAN.

Hugging Face HTTPS initially returned proxy CONNECT 403. After the user
published the environment, the pinned download succeeded, including the
`us.aws.cdn.hf.co` redirect. The current saved network policy is unrestricted;
this is an observed user setting, not a change made by the downloader.
No model-authentication failure was observed and no new secret was needed.

The CPU has five visible EPYC 9V74 cores with AVX512_BF16; its CPU quota is
four cores and Torch reports MKLDNN available. The memory limit is 32 GiB.
The real BF16 checkpoint has loaded successfully. The fixed-item timing pilot
completed all nine engineering checks in 1,915.38 seconds of item computation
(31.92 minutes); the invocation took 2,008.07 seconds including model-manifest
checks and loading. Peak process RSS was 6,159,065,088 bytes (5.74 GiB).
The first historical 88-row active forward took 271.21 seconds. The subsequent
eight-item acquisition completed in 7,709.64 seconds (2 hours 8 minutes 30 seconds),
with peak RSS 6,195,048,448 bytes (5.77 GiB), faster than the initial four-to-five-hour
estimate. These are observed current-instance timings, not future runtime guarantees.
Keep Torch 2.13.0+cpu, Transformers 5.15.0, eager attention, no quantization,
and no remote code. Do not install CPU Torch into the original GPU environment.

## Download and verify the pinned artifact

After network access is applied, run from `/workspace/sr_glyphprobe`:

```bash
.venv/bin/python scripts/fetch_t22_pinned_model_v0.py \
  --output /workspace/models/llama32_3b_bf16_t21
```

The current instance already holds all nine verified files at that path.
For a fresh download, `scripts/fetch_t22_pinned_model_ranges_v0.py` accepts the
same `--output` and uses up to four HTTPS range requests concurrently. It
requires exact range responses and the same final whole-file hashes before
publishing each file; incomplete response bodies get bounded retries. Its
range cache is outside the immutable model directory.

The downloader requests only the nine files at the exact revision. Every file
is checked against its recorded size and SHA-256 before publication, and the
complete directory must match the original manifest. It preserves unknown
existing files, rejects insecure redirects, and does not disable TLS or checksum
verification. Verified files can be reused after an interrupted download;
unverified partial files are not model inputs. A proxy failure does not establish
missing Hugging Face credentials.

## CPU canary and timing

```bash
.venv/bin/python scripts/t22_kv_cpu_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_timing_v0 --items 1 --threads 4
```

The timing item is fixed as original exposed canary item zero. It is not
chosen by outcome. Use the same CPU model to compare stock eager attention,
the historical adapter, and the T22 adapter. Require exact old/new final and
neutral states in the original 88-row layout (both anchors, both distances,
two donors, all 11 conditions), plus exact same-slot no-op and roundtrip.
Acquire the four-operation glyph/suffix comparison in a separate 16-row batch
at anchor 21, distance 8, with its own same-slot neutral companion. Save actual
attention weights and mass diagnostics.

Only after this engineering/timing check, run all eight exposed items in a
separate output directory:

```bash
.venv/bin/python scripts/t22_kv_cpu_canary_v0.py run \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output runs/t22_cpu_canary_v0 --items 8 --threads 4
```

Item chunks are hash-bound and completed outputs are immutable. Use `--resume`
only for identical incomplete work. Do not resume a one-item completed timing
run as an eight-item run. Report measured per-stage times and peak RSS before
estimating the full cost. Effect signs never decide whether engineering work
continues. Runtime and adapter parity are checked before interpreting any data.

This path **reacquires CPU engineering evidence**. It cannot establish bit-exact
agreement with the original RTX 5090 run without its arrays and compatible
runtime. It also does not calculate lexical effects: those require reacquiring
the full fixed 128-source alias gallery and target alias baselines on CPU.
Do not substitute another gallery, promote the eight items to confirmation,
or relax the historical GPU gate. The larger 384-item K/V exploration remains
a subsequent, separately specified acquisition.

## Validation boundary

From the repository root, reproduce the complete source-bound check with an
unused output path:

```bash
.venv/bin/python scripts/validate_t22_cpu_engineering_v0.py \
  --output /tmp/t22-cpu-synthetic-validation.json
```

The recorded current-instance result is
[`synthetic_validation.json`](../validation/t22_cpu_engineering_v0/synthetic_validation.json).

Byte-stream tests exercise downloader integrity without network/model access.
The CPU runner is validated against tiny random models, including its exact
legacy layout and output/resume provenance. A tiny-model timing is not a
3B-checkpoint timing. Real checkpoint loading and the fixed one-item timing
pilot have passed. The pilot's acquisition receipt SHA-256 is
`c49a18f5a756bf5dc4c2cc4056776ac25bf6cba1a7d8ef7a22aeb7027bd0f120`.
An independent audit rehashed all nine model files and checked all 34 saved
arrays; see [the audit receipt](../validation/t22_cpu_engineering_v0/timing_independent_validation.json).
The eight-item CPU canary and its independent audit **completed successfully**
at 2026-10-20 05:06 JST. All nine engineering checks passed for each of eight
items. The audit rechecked all 272 persisted arrays; acquisition used 240 model
forwards (6,288 sequence forwards) and 576 nonreadout attention checks.
The canary contains six three-token and two two-token glyphs. No item was selected
or dropped based on an effect.

Preserved evidence:

- [Acquisition receipt](../validation/t22_cpu_engineering_v0/canary_acquisition_receipt.json),
  SHA-256 `27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901`.
- [Independent audit](../validation/t22_cpu_engineering_v0/canary_independent_validation.json),
  SHA-256 `d6a73eea7845e47fe373b259ab1cb472a7cd3452f2519290a44fc84e93c5b952`.
- [Frozen specification](../validation/t22_cpu_engineering_v0/canary_specification.json)
  and unchanged per-item receipts in `validation/t22_cpu_engineering_v0/canary_item_receipts/`.

These are byte-identical copies of generated evidence; raw arrays remain in
`runs/t22_cpu_canary_v0/`. The supervisor status is `complete`. Hashes from the
supervisor through the audit, acquisition, item receipts, and raw NPZ files were
rechecked when recording completion. The eight-item audit did not separately
rehash model files; the acquisition verified them before and after the run,
and the earlier timing-item independent audit rehashed all nine files.

This completed engineering validation. At that stage, lexical effects,
historical GPU parity, and semantic or mechanistic conclusions were unestablished.
The subsequent fixed 128-source alias gallery and target alias acquisition on
the same CPU runtime enabled the separate descriptive
[lexical results](T22_CPU_LEXICAL_RESULTS_V0.md); historical GPU parity and
semantic or mechanistic conclusions remain unestablished.

After a completed run, independently audit its persisted arrays and provenance:

```bash
.venv/bin/python scripts/validate_t22_cpu_acquisition_v0.py \
  --run runs/t22_cpu_timing_v0 --expected-items 1 \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --output /tmp/t22-cpu-timing-independent-NEW.json
```

The independent audit uses NumPy without importing the acquisition runner or
Torch. It rechecks all 34 arrays per item, saved readout equality, local V-only
attention equality, geometry, and exact mass reconstruction. Full hidden tensors,
stock/idle comparison pairs, donor-capture comparison pairs, and nonreadout
attention outputs are not all persisted. Their full-state assertions therefore
remain source-bound acquisition-time checks rather than independent rechecks.

## Managed long run

The current supervisor independently checks the completed timing run, launches
the unchanged eight-item CPU protocol, and independently audits that completed
run. It aborts on a subprocess failure or a bound source change. Logs and
atomic status updates are under `runs/t22_cpu_orchestration_v0/`; the acquisition
is under `runs/t22_cpu_canary_v0/`. Inspect `status.json` and its `active_log`.
Only `status=complete` plus a passing final audit establishes completion.

For a new, unused output and state directory, the managed command is:

```bash
.venv/bin/python -u scripts/run_t22_cpu_canary_after_timing_v0.py \
  --model-path /workspace/models/llama32_3b_bf16_t21 \
  --timing-run runs/t22_cpu_timing_v0 \
  --canary-run runs/t22_cpu_canary_NEW \
  --state-dir runs/t22_cpu_orchestration_NEW
```

Do not launch a duplicate while a supervisor or acquisition process is alive.
The optional `--timing-pid` and `--timing-start-ticks` must be supplied together
when watching a still-running timing process. With neither, a completed timing
receipt is required before any work can start. The supervisor does not expand
the one-item run or reuse its arrays as an eight-item receipt.

If the machine restarts, live processes are not restored by an environment
snapshot. After confirming no acquisition is running, resume only an identical
incomplete eight-item run with the original runner and `--resume`, then execute
the independent validator with `--expected-items 8` and a new report filename.
Completed runs are immutable. The startup instructions preserve this recovery
path; they must never silently launch a second long run.
