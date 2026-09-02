# GlyphProbe T19/T20/T21 anonymous evidence artifact v2

[日本語](README.ja.md)

This **compact, double-blind review artifact** links the prespecified T19/T20/T21
protocols, selected item sets, compact results, independent validation reports,
analysis and validator code, paper sources, figures, and the anonymous review
PDF. It also supports model-free replay of T21-C's simultaneous inference from
195 item-level scalar contrasts. Full raw-data replay requires additional files
listed below.

## Verify first

For the zip itself, compare its SHA-256 with the adjacent `.sha256` file. After
extracting it, run from the extracted artifact root:

```bash
python3 scripts/validate_anonymous_artifact.py .
```

The validator checks the complete entry roster, every payload SHA-256 and byte
count, `SHA256SUMS`, safe relative paths, fixed archive timestamps, forbidden
raw/model file types, and a conservative set of author-identity and local-path
tokens. A pass proves package integrity and omission policy only; it does not
prove that the scientific estimand is correct.

## What is included

- `paper/glyphprobe_t19_anonymous.pdf` and the anonymous TeX/BibTeX sources;
- all six deterministic paper figures plus their input/output hash manifest
  and boxed-label layout regression tests;
- the T19-L selection, freeze, configuration, tokenizer preflights, compact
  observational results, and independent-validation receipt;
- the T19-C go manifest, compact component results, and independent-validation
  receipt;
- the descriptive T19-C post-hoc full-state swap results;
- the T20-C configuration, selection, specification and admission manifests,
  preliminary checks, training/evaluation reports, compact results, and
  independent-validation receipt;
- the T21 pilot and separate prospective confirmation specifications, exposed-item
  canary receipts, acquisition and analysis reports, independent numerical
  validation, and all 195 confirmation items' derived scalar contrasts;
- the exact executor, analyzer, and independent-validator source files needed
  to inspect how the receipts were produced;
- the minimal T9/T10/T18 bindings referenced by the T19 freeze;
- paired English/Japanese claim, license, compute, ethics, protocol, result,
  and artifact-boundary documentation; and
- Apache License 2.0 for the new code plus the Unicode License v3 notice for
  derived Unicode/CLDR rows.

`ARTIFACT_MANIFEST.json` is the machine-readable boundary. It lists every
payload path, size, and digest. `SHA256SUMS` additionally binds the manifest.
The fixed `reproducibility_timestamp_utc` and ZIP timestamps make packaging
deterministic; they are not build or experimental-event timestamps. Actual
design, acquisition, and analysis times remain in the experimental receipts.

## What is deliberately excluded

- model weights, tokenizer files, caches, virtual environments, and secrets;
- T19/T20/T21 model-dependent activation arrays, causal source subspaces, causal
  evaluation arrays, and the full intervention ledger;
- Git metadata, repository remotes, author metadata, local absolute paths, and
  private execution-host information; and
- exploratory raw outputs that are not part of the T19 evidence denominator.

The omitted raw arrays remain bound by the included acquisition and validation
receipts but are not independently replayable from this compact package. The
archive therefore supports compact-result and figure audit, T21-C statistical
replay from derived contrasts, source-code inspection, and manuscript
verification. It does not support full
reacquisition without obtaining the upstream model assets, or raw-array
reconstruction from the compact evidence alone.

## Reproduce the compact surfaces

The integrity validator uses only the Python standard library. For the
scientific Python files, the recorded acquisition stack is in
`paper/COMPUTE_REPORT.md`; the small audit/figure environment is listed in
`requirements-audit.txt`.

Replay the T21-C five-contrast simultaneous lower bounds, verdict, and
descriptive top-1 means using NumPy alone:

```bash
python3 scripts/validate_t21_compact_inference_v0.py \
  --compact validation/t21_glyph_context_path_confirmation_v0/results/item_contrasts.json \
  --result validation/t21_glyph_context_path_confirmation_v0/results/confirmation_result.json
```

This recomputes 20,000 shared-index item bootstrap replicates. Agreement checks
the statistical calculation from the included scalars; correctness of the
model-state interventions remains a separate, receipt-bound validation.

Regenerate the figures in a disposable extracted copy:

```bash
python3 paper/scripts/build_figures.py
python3 scripts/validate_anonymous_artifact.py .
```

The second command passes only if regeneration is byte-identical to the recorded
figure and manifest hashes. Font and rendering-library differences can change
PDF/PNG bytes even when plotted values are the same, so a mismatch is a
rendering-parity result, not automatically a scientific discrepancy.

To compile the paper source, obtain the official NeurIPS 2026 formatting
archive whose URL and SHA-256 are recorded in `paper/README.md`, place
`neurips_2026.sty` beside `main.tex`, and run:

```bash
mkdir -p paper/build
SOURCE_DATE_EPOCH=1788307200 tectonic -X compile --outdir paper/build --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted paper/main.tex
```

The conference style file is intentionally not redistributed here. The
included PDF is the artifact's controlling rendered manuscript.

## Claim boundary

T19-L supports bounded cross-model lexical retrieval under fixed text-only
Unicode inputs and exact token-count controls. T19-C finds no prespecified
primary late component that passes both necessity and sufficiency criteria in
one Llama 3.2 3B configuration. T20-C returns uncalibratable at its primary
sites under the registered rule. Their full-state asymmetry motivated the
separate T21 study. T21-C supports a conditional contribution of glyph-position
keys and values to a continuous lexical-retrieval margin after a block-21
readout reset in one Llama 3.2 3B configuration. All five prespecified
simultaneous lower bounds are positive. Absolute necessity and rescue top-1
mean effects are both zero. This result does not revise the T19/T20 criteria
or establish accuracy improvement, an unconditional or emoji-specific path,
or a complete mediator. The artifact does not establish rendered-glyph
perception, human meaning, tokenizer independence, a universal manifold, a
complete circuit, a scale law, or model-population generality.
