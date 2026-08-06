# GlyphProbe

[日本語](README.ja.md) · [Results](docs/RESULTS_V1.md) · [Milestone 2 protocol](docs/MILESTONE2_PROTOCOL.md) · [Roadmap](docs/ROADMAP.md) · [Phase I paper plan](docs/PAPER_OUTLINE.md)

GlyphProbe is an auditable research harness for one deliberately narrow question:

> When source construction, intervention magnitude, clipping, prompts, and random controls are fixed, do different emoji- or glyph-derived activation directions leave reproducible, direction-specific fingerprints in a language model's next-token distribution?

The default panel is a balanced `5 colors × 2 shapes` grid:

```text
🟤 🟫   🟠 🟧   🟢 🟩   🔵 🟦   🟣 🟪
```

GlyphProbe starts with blind numerical screening. It does **not** infer what a glyph means to a model, identify a circuit, or establish a causal path. A reproducible fingerprint is a candidate for sharper causal experiments, not their conclusion.

## Current evidence snapshot

The first standard MLX cell uses the pinned `openai-community/gpt2` revision `607a30d783dfa663caf39e06633721c8d4cfcd7e`, FP32, and full-sequence `resid_post` addition at layers 2, 4, 7, and 9.

| Check | Current result | Scope |
|---|---:|---|
| Transformers/MPS ↔ MLX parity | 80/80 gates passed | 4 prompt lengths × 4 standard layers; tokenizer, baseline activation/logit, zero-hook, and fixed-intervention checks |
| Synchronized end-to-end median latency | 17.52 ms → 10.73 ms | 1.63× in the recorded environment; tokenization, capture/intervention, evaluation, and NumPy transfer included |
| Standard MLX intervention records | 14,208; 0 errors | 10 glyphs, 24 target prompts, 3 direction seeds, 3 strengths, 4 layers |
| Readiness gates | 11/11 | pre-causal readiness only |
| Median held-out fingerprint advantage | 0.608 | 25/36 layer–seed–strength cells were positive; 11/36 were not |
| Median cross-seed fingerprint advantage | 0.931 | seeds are repeated direction estimates, not independent observations |

These numbers are descriptive outputs of one pinned model cell. The [parity receipt](validation/mlx_gpt2_parity/receipt.json) is explicitly marked as an engineering validation rather than a scientific result. The [standard-run audit](validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json) passed 15/15 integrity checks with caveats. The run authorizes targeted follow-up design only; `causal_claim_authorized` remains `false`. See [Results v1](docs/RESULTS_V1.md) for the complete qualification and negative cells.

Latency is machine-, load-, and software-dependent. Treat the receipt as the measurement, not 1.63× as a universal MLX claim.

### Milestone 2 status

The tokenization-matched control protocol is frozen and preflight is pending;
no Milestone 2 model outcome is reported yet. A one-shot 48-target P2
confirmatory bank and a separate 48-target C1 causal holdout bank are frozen.
The primary comparison uses three disjoint ten-symbol null panels matched to the
colored-shape panel on GPT-2 token count and its 9:1 token-prefix structure.
Layers 2 and 4 at strength 0.05 are the fixed primary family, and inference is
performed over target-prompt clusters rather than treating glyphs or direction
seeds as independent observations.

The P2 bank remains unopened until the protocol and its bound manifests,
configs, analysis code, and tests are present in the public freeze commit and
all preflight checks pass. The C1 bank is reserved for a later causal protocol.
See the [Milestone 2 confirmatory protocol](docs/MILESTONE2_PROTOCOL.md) for the
endpoint, decision rule, and prohibited uses.

## Install

GlyphProbe requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Choose the execution path you need:

```bash
# Apple silicon
pip install -e '.[mlx,torch,dev]'

# Raw Hugging Face Transformers
pip install -e '.[torch,dev]'

# TransformerLens
pip install -e '.[lens,dev]'

# TransformerLens + SAELens
pip install -e '.[sae,dev]'

# OpenAI-compatible serving controls
pip install -e '.[server,dev]'
```

Initialize a self-contained experiment workspace:

```bash
glyphprobe init ./glyphprobe-experiment
cd glyphprobe-experiment
```

The copied workspace contains versioned configs, the panel, source wrappers, target cases, and backend-matrix examples.

## Closed-loop smoke test

The deterministic mock backend verifies joins and artifact generation without downloading a model:

```bash
glyphprobe plan -c configs/v1_smoke.yaml --num-layers 8
glyphprobe run  -c configs/v1_smoke.yaml
```

Mock output is plumbing evidence only. It must not be cited as model evidence.

## Reproduce the pinned MLX cell

The standard config is offline-first and already binds the scientific run to the checked-in parity-receipt hash:

```bash
glyphprobe inspect -c configs/v1_mlx_standard.yaml
glyphprobe plan -c configs/v1_mlx_standard.yaml --load-model
glyphprobe run -c configs/v1_mlx_standard.yaml
```

To requalify after changing backend code or the model cell, return from the starter workspace to the repository checkout root and write a candidate receipt without overwriting the pinned one:

```bash
cd ..  # repository checkout root
python scripts/validate_mlx_gpt2_parity.py \
  --output validation/mlx_gpt2_parity/receipt.candidate.json
shasum -a 256 validation/mlx_gpt2_parity/receipt.candidate.json
```

Promote a passing candidate and update `validation_receipt_sha256` in both standard configs as one reviewed change. A newly generated receipt contains fresh timing samples, so its SHA-256 is expected to differ even when all gates pass.

The validation scope is intentionally narrow:

- model: `openai-community/gpt2` at the pinned revision above;
- dtype: FP32;
- site: full-sequence `resid_post`;
- standard layers: 2, 4, 7, and 9;
- prompt-length buckets: 3, 9, 10, and 22 tokens in the recorded receipt;
- intervention: a sealed fixed FP32 vector, plus exact zero-hook checks.

Changing the model, revision, dtype, quantization, component site, or implementation creates a new experimental cell and requires a new parity receipt. MLX support does not make MLX and PyTorch outputs generally interchangeable.

## Other execution paths

TransformerLens remains the canonical named-hook path:

```bash
glyphprobe run -c configs/v1_standard.yaml \
  --backend lens \
  --model openai-community/gpt2 \
  --device cuda \
  --dtype float32
```

Raw Transformers uses conservative model-family module discovery:

```bash
glyphprobe run -c configs/v1_standard.yaml \
  --backend transformers \
  --model openai-community/gpt2 \
  --device cuda \
  --dtype float32
```

OpenAI-compatible adapters (`vllm`, `llamacpp`, `ollama`, `lmstudio`, and `openai`) provide surface controls. Standard serving APIs do not expose residual streams, so these runs are stamped `surface-observational-only` and cannot substitute for activation intervention.

## What the standard matrix controls

- panel-centroid removal and a neutral-glyph source baseline;
- separately estimated wrapper-subset direction seeds;
- norm-matched random directions projected outside the panel-direction span;
- exact zero-vector hook controls;
- three positive RMS strengths, global RMS clipping, and sign flips;
- repeated group-stratified target splits;
- within-target glyph-label permutations;
- cross-seed output-fingerprint comparisons;
- token IDs, Unicode code points, UTF-8 bytes, and wrapper token counts.

Full-vocabulary logit deltas are compressed into deterministic, unit-normalized CountSketch fingerprints. These are comparison objects, not semantic labels.

## Read the artifacts conservatively

The current standard result is heterogeneous. The median fingerprint advantage is positive, and every layer median is positive, but 11 of 36 layer–seed–strength cells are non-positive. The primary glyphs are length-balanced at three tokens each, yet token identities differ; the neutral `·` control is one token, and the blue-circle token sequence has a distinct middle token. The permutation screen reaches the finite floor `1/1001` in all 36 cells, but those values are not multiplicity-corrected global significance tests.

Target prompts are the principal sampling clusters. Direction seeds remain nested repeated estimates and must not be counted as independent observations. Iso-KL, SAE, generation, other hook sites, path patching, and cross-model replication were not run in this cell.

The compact public evidence package omits the approximately 74 MiB (77.3 MB) raw `interventions.jsonl` ledger and model-dependent NPZ arrays. Published summaries and manifests identify what was retained or omitted; a paper-grade release must preserve or archive the complete sealed run separately.

## Documentation

Project-authored public documentation is maintained in English and Japanese:

| Topic | English | Japanese |
|---|---|---|
| Scientific contract | [SCIENTIFIC_CONTRACT.md](docs/SCIENTIFIC_CONTRACT.md) | [SCIENTIFIC_CONTRACT.ja.md](docs/SCIENTIFIC_CONTRACT.ja.md) |
| Backend boundaries | [BACKENDS.md](docs/BACKENDS.md) | [BACKENDS.ja.md](docs/BACKENDS.ja.md) |
| Metrics | [METRICS.md](docs/METRICS.md) | [METRICS.ja.md](docs/METRICS.ja.md) |
| Current results | [RESULTS_V1.md](docs/RESULTS_V1.md) | [RESULTS_V1.ja.md](docs/RESULTS_V1.ja.md) |
| Milestone 2 protocol | [MILESTONE2_PROTOCOL.md](docs/MILESTONE2_PROTOCOL.md) | [MILESTONE2_PROTOCOL.ja.md](docs/MILESTONE2_PROTOCOL.ja.md) |
| Research roadmap | [ROADMAP.md](docs/ROADMAP.md) | [ROADMAP.ja.md](docs/ROADMAP.ja.md) |
| Phase I paper plan | [PAPER_OUTLINE.md](docs/PAPER_OUTLINE.md) | [PAPER_OUTLINE.ja.md](docs/PAPER_OUTLINE.ja.md) |
| Public research note | [NOTE.md](docs/NOTE.md) | [NOTE.ja.md](docs/NOTE.ja.md) |

Machine-generated artifacts, schemas, citations, licenses, and source code are exempt from line-by-line translation. English is the controlling language for the planned Phase I paper; the repository documentation remains bilingual.

## Phase I goal

Phase I ends with an English preprint-ready paper supported by an auditable evidence package. The present standard run is a baseline result, not the endpoint. The [roadmap](docs/ROADMAP.md) requires targeted causal tests, confirmatory statistics at the target-prompt cluster level, stronger tokenization controls, and replication before the paper's claims can be frozen.

## Validation

```bash
pytest
python -m compileall -q src/glyphprobe
glyphprobe matrix -x configs/backend_matrix.example.yaml --dry-run
```

Run IDs bind the resolved experiment inputs, implementation, runtime dependencies, model artifact identity, and parity receipt. Resume is permitted only inside the same sealed identity.

## License and citation

GlyphProbe is released under the Apache License 2.0. See [CITATION.cff](CITATION.cff) for citation metadata.
