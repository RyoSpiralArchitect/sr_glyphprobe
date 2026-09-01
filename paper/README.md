# GlyphProbe Phase I paper

[Japanese](README.ja.md) | [Frozen claim table](CLAIM_TABLE.md)

Status: **first English manuscript draft compiled and frozen; not submission-ready**.

The manuscript uses the official NeurIPS 2026 double-blind workshop style and
targets the long-paper limit for the Interpretability as a Science workshop.
The English paper is the controlling scientific text. This bilingual README
documents the build, evidence boundary, and figure contracts; it is not a
second manuscript.

## Files

- `main.tex`: anonymous English manuscript.
- `references.bib`: references used by the draft.
- `neurips_2026.sty` and `checklist_template.tex`: unmodified official
  template assets; `checklist.tex` contains conservative draft answers with the
  official questions unchanged.
- `scripts/build_figures.py`: deterministic figure builder from compact,
  validated T19 JSON summaries.
- `figures/manifest.json`: input and output SHA-256 receipts generated with the
  figures.
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: compiled review PDF.

The official formatting archive was downloaded from
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`.
Its SHA-256 is
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
Copying the style files into this directory does not imply workshop acceptance
or submission readiness.

## Build

From the repository root:

```bash
python3 paper/scripts/build_figures.py
tectonic -X compile --outdir "$PWD/paper/build" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp paper/build/main.pdf output/pdf/glyphprobe_t19_first_draft.pdf
```

Tectonic runs the BibTeX pass automatically. The Codex `latex-compile` helper
can be used instead when a full TeX Live installation is available; on the
validated Mac build it correctly detected that TeX Live was absent, so the
bundled Tectonic executable was invoked directly. The final copy is made only
after citation, page-count, text-extraction, and rendered-page checks.
`paper/build/` and `tmp/pdfs/` are intermediate surfaces.

## Frozen first-draft claim boundary

The paper leads with a dissociation. Raw atomic emoji retrieve lexically
disjoint CLDR keyword aliases better than literal codepoint strings across all
nine frozen model/tokenizer cells, including exact four-view token-count
matching. A preregistered rank-8 late-component test in one Llama 3.2 3B cell
then finds no primary `attn_out` or `mlp_out` site that is jointly necessary
and sufficient on 192 untouched evaluation emoji.

This supports bounded lexical correspondence under text-only Unicode inputs.
It does not establish rendered-glyph perception, human synonym understanding,
token-identity matching, tokenizer independence, pretraining novelty, a
universal manifold, a complete circuit, or a scale law. The auditable allowed
and excluded statements are frozen in [CLAIM_TABLE.md](CLAIM_TABLE.md).

## Figure chart contracts

The figures are static Matplotlib PDF exports. Each contract records the
question, intended takeaway, chart family, data sufficiency, renderer,
encoding, output, and QA obligation before rendering.

### Figure 1 - prospective design

- **Question:** What surfaces, lexical endpoints, controls, and data banks are
  separated by the design?
- **Takeaway:** T19-L crosses emoji and repository-text-fresh symbols with four
  text views; T19-C uses disjoint source and evaluation emoji and runs only
  after the observational gate.
- **Family / sufficiency:** annotated process schematic; all frozen arms and
  bank sizes are known.
- **Renderer / encoding:** static Matplotlib; blue for observational evidence,
  orange for causal testing, gray for controls; arrows and labels preserve
  meaning without color.
- **Output / QA:** `figures/t19_design.pdf`; verify every count and gate label
  against the frozen protocol and inspect the embedded PDF.

### Figure 2 - emoji alias effect across models

- **Question:** Is alias-minus-codepoint top-1 positive in every frozen cell,
  both unrestricted and token-count matched?
- **Takeaway:** all nine cells are positive and exceed the preregistered 0.02
  practical floor, with heterogeneous magnitudes.
- **Family / sufficiency:** paired horizontal dot plot; nine model categories
  are sufficient for exact cell-level comparison.
- **Renderer / encoding:** static Matplotlib; blue filled circles for
  unrestricted and orange open squares for matched estimates; marker shape,
  a zero line, and a dashed 0.02 line retain grayscale legibility.
- **Output / QA:** `figures/t19_model_effects.pdf`; keep the registered roster
  order, validate all 18 points against `model_cell_results.json`, and inspect
  labels and reference lines in the compiled paper.

### Figure 3 - emoji and symbol lexical boundary

- **Question:** How do alias and canonical-name effects differ between emoji
  and non-emoji Unicode symbols?
- **Takeaway:** canonical-name retrieval is broad, while alias retrieval is
  stronger and more consistent for the frozen emoji panel; the symbol contrast
  remains secondary and nonexchangeable.
- **Family / sufficiency:** two-panel paired dot plot across nine models,
  one panel per lexical endpoint.
- **Renderer / encoding:** static Matplotlib; blue circles for emoji and gray
  diamonds for symbols, with unrestricted/matched represented by filled/open
  markers and line style.
- **Output / QA:** `figures/t19_emoji_symbol_boundary.pdf`; validate all 36
  model-level values, preserve a common x-axis, label the comparison
  "registered secondary," and inspect the final caption and legend.

### Figure 4 - component-level causal test

- **Question:** Does any frozen late site have both random-adjusted necessity
  and sufficiency above the 0.02 floor?
- **Takeaway:** no site passes both components; block-27 MLP shows a secondary
  sufficiency-only asymmetry rather than a complete mediator.
- **Family / sufficiency:** two-panel horizontal interval dot plot; all six
  registered sites are shown with 95% item-bootstrap intervals.
- **Renderer / encoding:** static Matplotlib; circles for necessity, squares
  for sufficiency, dark outlines for the two primary block-24 sites, and gray
  for secondary sites.
- **Output / QA:** `figures/t19_causal_sites.pdf`; validate all 12 estimates and
  intervals against `causal_site_results.json`, display zero and 0.02
  references, and inspect the primary-site emphasis.

## Submission gaps visible in draft v0

- replace anonymous artifact prose with a double-blind archive or explicitly
  state why it is unavailable;
- resolve the current checklist's explicit `No` / `N/A` submission gaps;
- independently review all manuscript numbers against the compact receipts;
- resolve author list and acknowledgments only after the double-blind copy is
  frozen;
- upload early enough to verify the OpenReview record.
