# Reproducibility guide

[Japanese / 日本語](REPRODUCIBILITY.ja.md)

This guide reproduces the released MLX validation, standard pre-causal matrix,
and E1 exploratory side track. It does not promise identical wall-clock timing
on different hardware.

## 1. Prepare the environment

Use Apple silicon with MLX Metal available for the MLX cell. Python 3.11–3.13 is
supported by the package metadata.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[mlx,torch,dev]'
python -m pytest
```

Run every command in this guide from the repository checkout root.

The test count changes as the release grows. Record the collected and passing
count from the exact revision you test. The MLX scientific path additionally
requires the live model/backend validation below; deterministic adapter tests do
not replace it.

## 2. Make the pinned model revision available

The shipped MLX cell uses:

```text
model: openai-community/gpt2
revision: 607a30d783dfa663caf39e06633721c8d4cfcd7e
dtype: float32
site: resid_post
```

`configs/v1_mlx_standard.yaml` sets `local_files_only: true`. Populate the exact
Hugging Face snapshot before running offline. The backend hashes the resolved
model artifact as a path-independent file manifest. A name or revision string by
itself is not complete model provenance.

## 3. Reproduce the backend parity and speed gate

```bash
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

The canonical `receipt.json` SHA-256 is pinned in
`backend.validation_receipt_sha256` in the standard configuration. A candidate
will normally have a different hash because timing and receipt metadata are new.
Review the full candidate, then promote it to `receipt.json` and update the hash
in both the source and packaged copies of the configuration as one reviewed
change. Do not hand-edit either receipt.

Activation patching remains unavailable unless the receipt passes and its hash,
source-tree identity, stable model identity, model, revision, dtype, and site
match the loaded backend. The speed gate requires the aggregate MLX median to be
at least 5% lower than Transformers/MPS on the sealed matrix.

## 4. Inspect and run the standard matrix

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

Paths inside a configuration are resolved relative to that configuration file,
including the validation receipt path. The standard cell fixes the panel,
wrappers, targets, seeds, strengths, layers, controls, model revision, receipt,
and receipt hash. Keep the resolved configuration and plan with the run.

## 5. Understand the run seal

For a successfully loaded backend, the run ID is derived from a seal over:

- resolved configuration, panel, wrappers, and targets;
- ordered SHA-256 receipts for the configuration, parity receipt, and data files;
- the installed GlyphProbe Python source-tree hash;
- the dependency/runtime environment receipt; and
- a stable loaded-model identity containing the path-independent model-artifact
  manifest while excluding path and load-time noise.

The backend is loaded before the run directory is selected. Resume therefore
cannot silently reuse records from another dependency/runtime or model artifact
while rewriting a fresh receipt. A seal change produces a different run ID. If a
directory already contains a mismatching receipt, resume is refused.

Receipts use portable input labels, path-free model locators, and run IDs instead
of local directories by construction. Preserve that invariant: an absolute local
path is a publication blocker. Fix the emitter and regenerate the receipt rather
than sanitizing a sealed artifact after the fact.

## 6. Validate the complete run

```bash
python scripts/validate_standard_run_artifacts.py \
  path/to/run-directory \
  --output validation/run_audits/run-audit.json
```

The validator recomputes input and implementation bindings, planned and observed
record counts, unique deterministic task IDs, required fields, finite core
metrics, target/tokenization profiles, headline summaries, and readiness. Keep
the full distribution of fingerprint cells and every caveat. A 15/15 audit and
11/11 readiness permit escalation to finer tests; they do not authorize a causal
or semantic conclusion.

## 7. Build the compact public evidence bundle

```bash
python scripts/build_public_artifact_bundle.py \
  --run-dir path/to/run-directory \
  --parity-receipt validation/mlx_gpt2_parity/receipt.json \
  --audit-receipt validation/run_audits/run-audit.json \
  --output-dir path/to/public-artifacts
```

The builder refuses text artifacts containing any local POSIX or Windows absolute
path or `file://` URI, copies the compact summaries, and emits a manifest with hashes for included
files and omitted large ledgers/arrays. Omission hashes attest local files but do
not make them reconstructable; archive the full sealed run separately for a
paper-grade release.

## 8. Reproduce and validate the E1 exploratory side track

First rerun the tokenizer-only preflight and compare its deterministic receipt
with the frozen one:

```bash
python scripts/audit_e1_token_isomorphic_panels.py \
  --output /tmp/e1-tokenization-audit.candidate.json
```

After making the pinned GPT-2 snapshot available, inspect, plan, and run each of
the five frozen configurations:

```bash
glyphprobe run -c configs/e1_sky_moon_mlx.yaml
glyphprobe run -c configs/e1_food_mlx.yaml
glyphprobe run -c configs/e1_animals_mlx.yaml
glyphprobe run -c configs/e1_transport_mlx.yaml
glyphprobe run -c configs/e1_social_mlx.yaml
```

The analyzer binds every scientific role to its expected config, panel, source,
target file, and hashes. Use five complete sealed run directories and a new,
absent output directory:

```bash
python scripts/analyze_emoji_family_exploratory_v1.py \
  --sky-run path/to/sky-run \
  --food-run path/to/food-run \
  --animals-run path/to/animals-run \
  --transport-run path/to/transport-run \
  --social-run path/to/social-run \
  --output-dir path/to/new-analysis-directory
```

Build and independently validate the compact public bundle from the exact
frozen local runs and analysis:

```bash
python scripts/build_emoji_family_exploratory_v1_bundle.py
python scripts/validate_emoji_family_exploratory_v1_bundle.py
```

Separate from its root manifest, the published payload contains 82 hash-bound
members: the tokenizer preflight, six analysis outputs, and 15 compact files for
each of five runs.
The validator checks the 240/960/10/40 analysis row grids, role bindings,
absence of local absolute paths, and the declared non-access to P2 and C1. The
hash-bound published receipts and summaries record zero errors and exact
zero-hook behavior; those two fields are not independently recomputed by this
validator. The compact run directories deliberately omit the raw intervention
ledgers and model-dependent arrays. Their hashes document the omission, but the
compact bundle alone cannot regenerate the analysis; keep or archive the
complete sealed local runs.

E1 intervals are descriptive. Reproduction does not turn them into p-values,
confirmatory statuses, semantic evidence, tokenizer-independent effects, or a
causal result. See the [frozen protocol](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md)
and [complete result](EMOJI_FAMILY_EXPLORATORY_RESULTS.md).

## Machine-specific quantities

Wall-clock latency, load time, peak device memory, dependency and OS versions,
hardware-specific kernels, and timestamps belong in receipts. Local filesystem
paths do not. Do not normalize runtime quantities away to force identical run IDs
or benchmark values across different machines.
