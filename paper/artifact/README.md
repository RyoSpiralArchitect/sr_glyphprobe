# GlyphProbe T19 anonymous evidence artifact v0

[日本語](README.ja.md)

This is a **compact, double-blind review artifact**, not a claim of complete
open-data reproduction. It binds the frozen T19 protocol, selected item banks,
compact results, independent-validation receipts, analysis and validator code,
paper sources, figures, and the anonymous review PDF.

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
- all four deterministic paper figures plus their input/output hash manifest;
- the T19-L selection, freeze, configuration, tokenizer preflights, compact
  observational results, and independent-validation receipt;
- the T19-C go manifest, compact component results, and independent-validation
  receipt;
- the exact executor, analyzer, and independent-validator source files needed
  to inspect how the receipts were produced;
- the minimal T9/T10/T18 bindings referenced by the T19 freeze;
- paired English/Japanese claim, license, compute, ethics, protocol, result,
  and artifact-boundary documentation; and
- Apache License 2.0 for the new code plus the Unicode License v3 notice for
  derived Unicode/CLDR rows.

`ARTIFACT_MANIFEST.json` is the machine-readable boundary. It lists every
payload path, size, and digest. `SHA256SUMS` additionally binds the manifest.

## What is deliberately excluded

- model weights, tokenizer files, caches, virtual environments, and secrets;
- T19 model-dependent activation arrays, causal source subspaces, causal
  evaluation arrays, and the full intervention ledger;
- Git metadata, repository remotes, author metadata, local absolute paths, and
  private execution-host information; and
- exploratory raw outputs that are not part of the T19 evidence denominator.

The omitted raw arrays remain bound by the included acquisition and validation
receipts but are not independently replayable from this compact package. The
archive therefore supports exact compact-result and figure audit, source-code
inspection, and manuscript verification. It does not support full
reacquisition without obtaining the upstream model assets, or raw-array
reconstruction from the compact evidence alone.

## Reproduce the compact surfaces

The integrity validator uses only the Python standard library. For the
scientific Python files, the recorded acquisition stack is in
`paper/COMPUTE_REPORT.md`; the small audit/figure environment is listed in
`requirements-audit.txt`.

Regenerate the figures in a disposable extracted copy:

```bash
python3 paper/scripts/build_figures.py
python3 scripts/validate_anonymous_artifact.py .
```

The second command passes only if regeneration is byte-identical to the frozen
figure and manifest hashes. Font and rendering-library differences can change
PDF/PNG bytes even when plotted values are the same, so a mismatch is a
rendering-parity result, not automatically a scientific discrepancy.

To compile the paper source, obtain the official NeurIPS 2026 formatting
archive whose URL and SHA-256 are recorded in `paper/README.md`, place
`neurips_2026.sty` beside `main.tex`, and run:

```bash
tectonic -X compile --outdir paper/build --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted paper/main.tex
```

The conference style file is intentionally not redistributed here. The
included PDF is the artifact's controlling rendered manuscript.

## Claim boundary

T19-L supports bounded cross-model lexical retrieval under fixed text-only
Unicode inputs and exact token-count controls. T19-C finds no frozen primary
late component that passes both registered necessity and sufficiency gates in
one Llama 3.2 3B cell. The artifact does not establish rendered-glyph
perception, human meaning, tokenizer independence, a universal manifold, a
complete circuit, a scale law, or model-population generality.
