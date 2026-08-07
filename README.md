# GlyphProbe

[日本語](README.ja.md) · [E2 MPS transport v2 protocol](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [v1 preflight failure](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) · [Holdout status](docs/HOLDOUT_STATUS.md) · [E2 Stage-A3 numeric-screen result](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) · [E2 Stage-A v2 result](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md) · [E1 exploratory results](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Milestone 2 results](docs/MILESTONE2_RESULTS.md) · [Baseline results](docs/RESULTS_V1.md) · [Roadmap](docs/ROADMAP.md) · [Phase I paper plan](docs/PAPER_OUTLINE.md)

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
| Milestone 2, primary-source layer 2 | +0.208363, 95% CI [0.137463, 0.276893] | Holm-adjusted p = 0.00143999; robust to the prespecified matched controls under frozen v1 |
| Milestone 2, primary-source layer 4 | -0.0329465, 95% CI [-0.0761085, 0.0110094] | Holm-adjusted p = 0.999500; unresolved under frozen v1 |
| Milestone 2, independent-source layer 2 | +0.187507, 95% CI [0.125489, 0.247659] | Holm-adjusted p = 0.00393996; robust to the prespecified matched controls under frozen v1 |
| Milestone 2, independent-source layer 4 | -0.086379, 95% CI [-0.159246, -0.016917] | Holm-adjusted p = 0.999430; unresolved under frozen v1 |
| E1 global specificity, layer 2 | 0.014752595564, 95% descriptive interval [0.002875238085, 0.027439243404] | exploratory; all five family-specific intervals included zero |
| E1 global specificity, layer 4 | 0.014887989201, 95% descriptive interval [0.003407563347, 0.019684351979] | intended negative comparator was not negative; all five family-specific intervals included zero |
| E2 Llama 3.2 3B BF16 parity | 33/60 gates passed | Stage-A v2 engineering validation failed; no scientific E2 grid was run |
| E2 machine-local median latency | 132.127833 ms → 230.138000 ms | Transformers/MPS → MLX; speed gate failed; recorded MLX speedup 0.574124367x |
| E2 Stage-A3 runtime-dtype selection | no candidate selected | FP16 and FP32 passed identity, token/determinism, zero-vector, and fidelity gates; both failed only speed |
| E2 Stage-A3 FP16 median latency | 165.0765625 ms → 322.9998125 ms | MLX/MPS fraction 1.956666698; all 10 MLX cell medians were slower |
| E2 Stage-A3 FP32 median latency | 465.013771 ms → 458.619459 ms | MLX/MPS fraction 0.986249198; approximately 1.375% lower, short of the required 5%; 4/10 MLX cell medians were slower |

The baseline fingerprint rows are descriptive outputs of one pinned model cell;
the Milestone 2 rows are frozen-v1 target-cluster results with the qualifications
summarized below. The [parity receipt](validation/mlx_gpt2_parity/receipt.json)
is explicitly marked as an engineering validation rather than a scientific
result. The [standard-run audit](validation/run_audits/colored-shapes-v1-standard-mlx--c493ae1e18743922.json)
passed 15/15 integrity checks with caveats. `causal_claim_authorized` remains
`false`. See [Results v1](docs/RESULTS_V1.md) for the baseline qualification and
negative cells.

Latency is machine-, load-, and software-dependent. Treat the receipt as the measurement, not 1.63× as a universal MLX claim.

### Milestone 2 status

Milestone 2 preflight passed and the frozen 48-target P2 bank was opened once.
The frozen v1 result is mixed: layer 2 exceeded the three prespecified
token-count and prefix-panel controls in the primary-source arm (+0.208363,
95% CI [0.137463, 0.276893], Holm p = 0.00143999) and in the independent-source
arm (+0.187507, [0.125489, 0.247659], Holm p = 0.00393996). Layer 4 was
unresolved in both arms (-0.0329465 and -0.086379, respectively).

These controls match the three-token count and panel-level 9:1 prefix structure,
not token identity. Panel C contains one declared semantic-near control, `🟥`.
The source-robustness arm reuses the same P2 targets and is not an independent
target or model replication. A separate input-binding audit passed, while a
post-hoc sensitivity analysis showed that rebuilding leave-one-group-out
prototypes inside each target-bootstrap replicate widens the intervals. It does
not overwrite the frozen v1 statuses. Both secondary diagnostics then completed
their 14,208-row grids with zero errors, zero-hook activation/logit RMS of 0, and readiness 11/11.
Their random-adjusted headline advantages were +0.751225 (suffix-matched) and
+0.601038 (prefix-homogeneous). These are not the raw separation scores used in
the paired diagnostic comparison. At 96 dimensions, the descriptive
standard-minus-diagnostic median was +0.002624 for suffix matching (20/36 cells
positive) and +0.022096 for prefix homogenization (25/36 positive). These
post-hoc diagnostics are not inferential or equivalence tests. C1 v1 was not
used by those experiments, but it is now retired after the separately recorded
research-context exposure described in [Holdout status](docs/HOLDOUT_STATUS.md).

For runtime provenance, the first matched-null A process was externally
interrupted after 798 rows under severe machine load. A sealed resume completed
the exact 14,208-row grid without duplicates, missing rows, or errors, with
zero-hook activation/logit RMS still at 0. The event is not model evidence or a general speed claim.

See [Milestone 2 results](docs/MILESTONE2_RESULTS.md) for the exact results,
analysis limitations, sensitivity intervals, and evidence links. The result is
pre-causal and does not establish semantics, mechanism, a circuit, or a
tokenization-free glyph effect.

### E1 exploratory status

The frozen token-isomorphic emoji-family screen is complete across five ten-glyph
families. Its full matched-slot transfer matrix was broadly positive at both
layers: the 25 family-pair means ranged from 0.395455 to 0.484915 at layer 2 and
from 0.602564 to 0.681909 at layer 4. The much smaller global within-family
excess was 0.014752595564 at layer 2 and 0.014887989201 at layer 4. Every one of
the ten family-specific descriptive intervals included zero.

This pattern suggests that transfer tied to the deliberately shared first and
third GPT-2 tokens dominates the small family-specific excess. It does not
support a semantic-family, tokenizer-independent, layer-specific, or causal
claim. Random-control comparison was also heterogeneous: 10/30 prespecified
family × layer × seed cells were non-positive, comprising all five families at
layer 2 seed 307 and all five at layer 4 seed 101. All 8,880 intervention rows
completed with zero errors and exact zero-hook activation/logit RMS of 0.

E1 used the already explored 24-target prestage bank. It did not open P2 or C1,
does not change the Milestone 2 classification, and does not satisfy a Phase I
paper gate. See the [E1 results](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md),
[frozen protocol](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md), and
[public evidence bundle](artifacts/emoji_family_exploratory_v1/analysis/report.md).

### E2 engineering results

The frozen Llama 3.2 3B BF16 Stage-A v2 engineering validation completed with
`status: validation_failed` and `scientific_result: false`. It passed 33/60 parity checks: tokenization and
within-backend determinism passed 10/10, exact zero-hook behavior passed 10/10,
baseline checks passed 6/10, changed-output checks passed 7/10, composite-delta
checks passed 0/10, and intervention-fidelity checks passed 0/10. All ten
activation-delta subcomparisons passed, but all composite delta checks failed
because the corresponding logit deltas did not meet the frozen thresholds.

The machine-local speed gate also failed. Aggregate median latency was
132.127833 ms for Transformers/MPS and 230.138000 ms for MLX: MLX used
1.741782892 times the latency, equivalent to the receipt's recorded
`0.574124367x` speedup. The sole specified backend change affecting numerical
semantics in v2—the BF16-to-FP32 cast immediately before NumPy export—allowed
the full validation to complete, but did not qualify MLX for this cell.

This is a negative engineering qualification only. The run accessed no study
target bank or confirmatory or causal outcome, produced no emoji-family,
semantic, causal, or cross-model result, and closes no paper gate. The v1 export
failure remains preserved. See the [complete E2 result](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md),
[frozen protocol](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md), and
[machine-readable receipt](validation/mlx_llama32_3b_bf16_parity_v2/receipt.json).
Stage A3 then screened the same pinned BF16-weight artifact with separate FP16
and FP32 runtime-compute candidates. Both candidates passed exact artifact and
parameter identity, prompt/token identity, determinism, the unchanged
zero-vector threshold, and backend-specific fidelity. Both failed only the
frozen machine-local speed requirement. FP16 recorded 165.0765625 ms for
Transformers/MPS and 322.9998125 ms for MLX; FP32 recorded 465.013771 ms and
458.619459 ms. The latter is approximately a 1.375% reduction, not the required
5%. The deterministic result was therefore
`selection.selected_runtime_dtype: null` and
`selection.decision: no_go_no_eligible_numeric_candidate`.

Stage A3 did not run full cross-backend parity, so FP32 is not qualified despite
its strong within-backend fidelity. No formal v3 validator or MLX science grid
was run or authorized, and the v2 failure remains unchanged. See the
[Stage-A3 result](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md),
[frozen numeric-screen protocol](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md), and
[atomic receipt](validation/mlx_llama32_3b_numeric_screen_v1/receipt.json).
The research owner selected a separate Transformers/MPS scientific route. Its
v1 static freeze stopped at tokenizer preflight before model-weight loading or
any forward because the audit conflated raw and contextual wrapper tokenization.
V1 is retired with [no scientific
outcome](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md). The same
50-emoji primary arm and independently centered 35-emoji token-structural
sensitivity arm are being rebound under the corrected, separately versioned
[v2 protocol](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md). This MPS-only study
does not reinterpret the MLX no-go or relax either MLX threshold.

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
| Milestone 2 results | [MILESTONE2_RESULTS.md](docs/MILESTONE2_RESULTS.md) | [MILESTONE2_RESULTS.ja.md](docs/MILESTONE2_RESULTS.ja.md) |
| Milestone 2 protocol | [MILESTONE2_PROTOCOL.md](docs/MILESTONE2_PROTOCOL.md) | [MILESTONE2_PROTOCOL.ja.md](docs/MILESTONE2_PROTOCOL.ja.md) |
| E1 exploratory results | [EMOJI_FAMILY_EXPLORATORY_RESULTS.md](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.md) | [EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md](docs/EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) |
| E1 exploratory protocol | [EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) | [EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md](docs/EMOJI_FAMILY_EXPLORATORY_PROTOCOL.ja.md) |
| E2 Stage-A3 numeric-screen results | [LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.md) | [LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_RESULTS.ja.md) |
| E2 Stage-A3 numeric-screen protocol | [LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.md) | [LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md](docs/LLAMA32_3B_MLX_NUMERIC_SCREEN_V1.ja.md) |
| E2 Stage-A v2 results | [LLAMA32_3B_MLX_VALIDATION_RESULTS.md](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.md) | [LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md](docs/LLAMA32_3B_MLX_VALIDATION_RESULTS.ja.md) |
| E2 Stage-A v2 protocol | [LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.md) | [LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md](docs/LLAMA32_3B_MLX_VALIDATION_PROTOCOL.ja.md) |
| E2 MPS transport v2 protocol | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md) |
| E2 MPS transport v1 preflight failure | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md) | [LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md](docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md) |
| Holdout status | [HOLDOUT_STATUS.md](docs/HOLDOUT_STATUS.md) | [HOLDOUT_STATUS.ja.md](docs/HOLDOUT_STATUS.ja.md) |
| Reproducibility guide | [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | [REPRODUCIBILITY.ja.md](docs/REPRODUCIBILITY.ja.md) |
| Research roadmap | [ROADMAP.md](docs/ROADMAP.md) | [ROADMAP.ja.md](docs/ROADMAP.ja.md) |
| Phase I paper plan | [PAPER_OUTLINE.md](docs/PAPER_OUTLINE.md) | [PAPER_OUTLINE.ja.md](docs/PAPER_OUTLINE.ja.md) |
| Public research note | [NOTE.md](docs/NOTE.md) | [NOTE.ja.md](docs/NOTE.ja.md) |

Machine-generated artifacts, schemas, citations, licenses, and source code are exempt from line-by-line translation. English is the controlling language for the planned Phase I paper; the repository documentation remains bilingual.

## Phase I goal

Phase I ends with an English preprint-ready paper supported by an auditable evidence package. Operational Milestone 2 is complete: layer 2 is eligible for the design of a new frozen targeted causal protocol, while layer 4 remains unresolved and is not a candidate. C1 v1 is retired and cannot serve that protocol; a new versioned bank must be prepared outside the exposed research context and kept untouched through the future causal freeze. E1 is a completed exploratory side track and does not alter that decision or close any paper gate. E2 Stage A v2 and Stage A3 remain completed negative MLX engineering qualifications. MPS transport v1 failed preflight with zero model forwards and contributes no scientific result. The corrected v2 study again uses a static manifest commit followed by a receipt-only preflight commit and does not revise the MLX outcomes. Final paper wording and supporting replication must prospectively address analyzer role binding and prototype-resampling dependence. Causal testing, independent backend or model replication, and archival evidence remain paper gates.

## Validation

```bash
pytest
python -m compileall -q src/glyphprobe
glyphprobe matrix -x configs/backend_matrix.example.yaml --dry-run
```

Run IDs bind the resolved experiment inputs, implementation, runtime dependencies, model artifact identity, and parity receipt. Resume is permitted only inside the same sealed identity.

## License and citation

GlyphProbe is released under the Apache License 2.0. See [CITATION.cff](CITATION.cff) for citation metadata.
