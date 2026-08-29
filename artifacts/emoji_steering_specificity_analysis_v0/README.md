# T13-EA emoji-steering specificity point evidence

[日本語](README.ja.md) · [Point results](../../docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) · [Frozen analysis contract](../../docs/EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md) · [Zero-gate amendment](../../docs/EMOJI_STEERING_SPECIFICITY_ZERO_GATE_AMENDMENT_V1.md)

Status: **completed exploratory point evidence; share with caveats; registered
bootstrap pending at 0/20,000**.

This directory contains the compact public evidence for T13-EA. The main
result is structured but not emoji-unique intervention geometry: source-form
effects vary with depth, dose, target, model, and glyph system; generic target
susceptibility, wrapper dependence, and the limited positive-isotropic null
remain competing explanations. No semantic, mechanistic, behavioral, or
confirmatory conclusion is authorized.

## Included evidence

- `reporting_summary_v0.json` is a deterministic, reporting-only synthesis of
  the complete F1–F6 point outputs. It retains every endpoint and systematic
  aggregation needed to reproduce the numerical headlines in the result
  document, together with explicit weights and denominators.
- `PUBLIC_MANIFEST.json` inventories the included summary, the six omitted
  source outputs, the omitted furnace archive, and the claim boundary.
- `SHA256SUMS` binds the four public bundle files.
- The generating
  [`summarize_emoji_steering_specificity_analysis_v0_results.py`](../../scripts/summarize_emoji_steering_specificity_analysis_v0_results.py)
  validates frozen IDs and statuses, exact production row counts, finite
  numbers, amendment and closeout bindings, and the source file bytes and
  SHA-256 values before producing output. It performs no model inference,
  bootstrap, significance test, or outcome-based filtering.

The summary is 1,127,906 bytes with SHA-256
`097934b191660106167164e2f60f18edafc7fe148db55760466b525aa74c6d06`.
An independent destination produced identical bytes.

## Omitted evidence

The six authenticated source outputs total 104,583,753 bytes. They remain
outside Git but are individually bound in both the public manifest and the
summary. The furnace-side acquisition archive contains 1,161 verified files
and 4,535,141,572 bytes; raw arrays were not copied to Git or SpiralShare.

Hashes establish identity with the reviewed data but cannot reconstruct an
omitted file. This bundle can reproduce the reported aggregate point values
from the authenticated derived outputs; it cannot independently rebuild those
outputs from raw activations.

## Zero-gate history

The original exact-JS gate failed closed before any nonzero scientific value
was opened and wrote no analysis output. That failure remains preserved. A
separate numerical amendment was frozen before the exact live residual
magnitude was inspected. Under the amendment, primitive no-op quantities
remained exact and only the float32-derived JS round-trip value used the fixed
bound `8 * eps(float32)`. Passing that gate is not scientific evidence and is
not a claim of exact JS.

## Reproduction

With authenticated copies of the six omitted source outputs:

```bash
python3 scripts/summarize_emoji_steering_specificity_analysis_v0_results.py \
  --outcomes-point-json /path/to/outcomes-v1-point.json \
  --geometry-directory /path/to/geometry-v1 \
  --point-results-closeout-json \
    validation/emoji_steering_specificity_analysis_v0/point_results_closeout_979533f.json \
  --output-json /path/to/new-reporting-summary.json
```

The output path must not already exist. To verify this public bundle on macOS:

```bash
cd artifacts/emoji_steering_specificity_analysis_v0
shasum -a 256 -c SHA256SUMS
```

## Frozen boundary

All intervals remain absent. The registered 20,000-replicate cluster
bootstrap has not been executed, and the current one-shot analyzer is not yet
a frozen deterministic high-level chunk-and-merge contract. The paper interval
gate remains closed. Exact token-ID/prefix controls, wrapper holdout, signed
matched nulls, an untouched target bank, remaining-model response replication,
and generation endpoints also remain unexecuted.
