# GlyphProbe Phase I paper

[Japanese](README.ja.md) | [Claims and evidence](CLAIM_TABLE.md)

Status: **anonymous manuscript and compact evidence archive built and
validated; OpenReview upload not performed**.

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
  validated T19/T20/T21 JSON summaries.
- `scripts/build_anonymous_artifact.py` and
  `scripts/validate_anonymous_artifact.py`: whitelist-only deterministic
  archive builder and independent integrity/identity-boundary validator.
- `figures/manifest.json`: input and output SHA-256 receipts generated with the
  figures.
- `ASSET_LICENSES.*`, `COMPUTE_REPORT.*`, and `ETHICS_REVIEW.*`: paired
  English/Japanese submission audits.
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: compiled review PDF.
- `../output/artifacts/glyphprobe_t19_anonymous_evidence_v3.zip`: standalone
  anonymous compact artifact, with adjacent receipt and SHA-256.

The official formatting archive was downloaded from
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`.
Its SHA-256 is
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
Copying the style files into this directory does not imply workshop acceptance
or submission readiness.

The unmodified style sets the requested `dblblindworkshop` option and records
the workshop title. In anonymous submission mode, the official 2026 style
nevertheless hard-codes a main-conference footer; only its final-mode footer
uses the track name. The build log confirms that this local
`neurips_2026.sty` is loaded. We preserve the official asset unchanged rather
than patching the footer.

## Build

From the repository root:

```bash
python3 paper/scripts/build_figures.py
SOURCE_DATE_EPOCH=1788307200 tectonic -X compile \
  --outdir "$PWD/paper/build" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp paper/build/main.pdf output/pdf/glyphprobe_t19_first_draft.pdf
python3 paper/scripts/build_anonymous_artifact.py
python3 paper/scripts/validate_anonymous_artifact.py \
  output/artifacts/glyphprobe_t19_anonymous_evidence_v3.zip
```

Tectonic runs the BibTeX pass automatically. On the validated Mac, invoke the
bundled executable directly or select `--compiler tectonic` in the Codex
`latex-compile` helper. Its automatic mode flags bibliography tooling for
TeX Live, which is absent on this host. The final copy is made only
after citation, page-count, text-extraction, and rendered-page checks.
`paper/build/` and `tmp/pdfs/` are intermediate surfaces.

Manuscript prose uses reader-facing terms such as *prespecified protocol*,
*evaluation set*, and *execution records*. Technical filenames, registered
protocols, and scientific receipts retain their original identifiers and
hashes. Boxed diagrams have a minimum 3-point text inset, checked at 72, 100,
and 220 dpi by `tests/test_paper_figure_layout.py`; the final PDF also requires
visual inspection. These checks preserve legibility without reducing type size.
Interval plots also reject axis ranges that clip a reported interval; Figure 2
derives its limits from all 18 intervals, including Mistral's matched upper
bound of 0.3531.

Table 6 labels all seven secondary sites explicitly. All nine sites were
evaluated; the two prespecified primary sites alone receive primary verdicts.
The labels do not add tests or change any numerical result.

## Prespecified claim boundary

The T19 design reports two conditionally linked results. Raw atomic emoji retrieve lexically
disjoint CLDR keyword aliases better than literal codepoint strings across all
nine prespecified model/tokenizer configurations, including exact four-view token-count
matching. A preregistered rank-8 late-component test in one Llama 3.2 3B configuration
then finds no primary `attn_out` or `mlp_out` site that is jointly necessary
and sufficient on 192 evaluation emoji held out from T19-L. Their surfaces may
have appeared in studies before T19.

This supports bounded lexical correspondence under text-only Unicode inputs.
It does not establish rendered-glyph perception, human synonym understanding,
token-identity matching, tokenizer independence, pretraining novelty, a
universal manifold, a complete circuit, or a scale law. The auditable allowed
and excluded statements are fixed in [CLAIM_TABLE.md](CLAIM_TABLE.md).

The separately specified T20-C follow-up tests optimized rank-8 subspaces on
384 additional emoji in four contexts. Its full-state swap controls yield
uncalibratable verdicts at both primary sites. The measured depth-dependent
asymmetry motivates a recovery-pathway hypothesis; those swaps alone do not
identify that pathway or exclude all possible subspaces.

Revision v4 retains the separately specified T21-C result on 195 further items:
glyph-position messages after a codepoint-view readout reset contribute to
keyword cosine margin beyond equal-count suffix controls. All five
simultaneous one-sided 95% lower bounds are positive. Absolute glyph-message
decrement and restoration have zero mean keyword top-1 effects. The
384-item pilot and 195-item confirmation are distinct, and all historical
T19/T20 results, thresholds, and input checksums remain unchanged. See the
[paired result report](../docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md).

The v3 anonymous archive adds T19 prediction indices for model-free replay of
all 36 primary-window tests and descriptive intervals, the T20 checkpoint
selection audit, and T21's post-hoc own/competitor margin decomposition. The
decomposition is descriptive and changes no confirmatory verdict. It retains
the 195 original scalar contrast rows and their simultaneous-inference replay.
Matched T19 emoji counts are corrected to 31--51 (Gemma: 51); the underlying
computations were already correct. See the [post-review evidence report](../docs/POST_REVIEW_EVIDENCE_RESULTS_V0.md).
Raw-state validation remains separate. Both v1 and v2 remain available, and
the archive validator accepts all three versions.

The manuscript now defines `T19-L` at first use as the lexical observational
arm and `T19-C` as the conditional component-causal arm. Appendix A gives the
short exploration-to-confirmation lineage from the early steering screen
through T21-C. Earlier exploratory and failed-confirmation results explain why
the final controls exist; they are not added to the T19-L evidence denominator.

## Figure chart contracts

The figures are static Matplotlib PDF exports. Each contract records the
question, intended takeaway, chart family, data sufficiency, renderer,
encoding, output, and QA obligation before rendering.

### Figure 1 - prospective design

- **Question:** What surfaces, lexical endpoints, controls, and item sets are
  separated by the design?
- **Takeaway:** T19-L crosses emoji and repository-text-fresh symbols with four
  text views; T19-C uses disjoint source and evaluation emoji and runs only
  after the observational criterion is met.
- **Family / sufficiency:** annotated process schematic; all prespecified arms
  and item-set sizes are known.
- **Renderer / encoding:** static Matplotlib; blue for observational evidence,
  orange for causal testing, gray for controls; arrows and labels preserve
  meaning without color.
- **Output / QA:** `figures/t19_design.pdf`; verify every count and criterion
  label against the prespecified protocol and inspect the embedded PDF.

### Figure 2 - emoji alias effect across models

- **Question:** Is keyword-minus-codepoint top-1 positive in every prespecified configuration,
  both unrestricted and token-count matched?
- **Takeaway:** all nine configurations are positive and exceed the registered 0.02
  effect-size floor, with heterogeneous magnitudes.
- **Family / sufficiency:** paired horizontal dot plot; nine model categories
  are sufficient for exact configuration-level comparison.
- **Renderer / encoding:** static Matplotlib; blue filled circles for
  unrestricted and orange open squares for matched estimates; marker shape,
  a zero line, and a dashed 0.02 line retain grayscale legibility.
- **Output / QA:** `figures/t19_model_effects.pdf`; keep the registered roster
  order, validate all 18 points against `model_cell_results.json`, and inspect
  labels and reference lines in the compiled paper.

### Figure 6 (Appendix C) - emoji and symbol lexical boundary

- **Question:** How do keyword and official-name effects differ between emoji
  and non-emoji Unicode symbols?
- **Takeaway:** official-name retrieval is broad, while keyword retrieval is
  stronger and more consistent for the prespecified emoji panel; the symbol contrast
  remains secondary and nonexchangeable.
- **Family / sufficiency:** two-panel paired dot plot across nine models,
  one panel per lexical endpoint.
- **Renderer / encoding:** static Matplotlib; blue circles for emoji and gray
  diamonds for symbols, with unrestricted/matched represented by filled/open
  markers and line style.
- **Output / QA:** `figures/t19_emoji_symbol_boundary.pdf`; validate all 36
  model-level values, preserve a common x-axis, label the comparison
  "registered secondary," and inspect the final caption and legend.

### Figure 3 - optimized subspaces and full-state controls

- **Question:** How do the optimized rank-8 effects compare with complete
  state replacement at each of the nine T20-C sites?
- **Takeaway:** the primary sites fail the registered calibration requirement;
  full-state effects are asymmetric at blocks 21/24 and reproduce the baseline
  gap at block 27.
- **Family / sufficiency:** paired horizontal interval plots of all nine sites,
  with 384 evaluation emoji and four contexts per item.
- **Renderer / encoding:** circles for necessity, squares for sufficiency,
  open triangles for full swaps, and shaded primary rows. The dashed line is
  0.02, the dash-dotted line is the 0.0332 baseline gap, and the dotted 0.06
  line applies only to the sufficiency calibration.
- **Output / QA:** `figures/t20_causal_ceilings.pdf`; preserve every recorded
  estimate and interval, distinguish adjusted subspace effects from unadjusted
  swap effects, and check the legend and vertical reference lines in the PDF.

### Figure 4 - conditional glyph-position message test

- **Question:** What is replaced in T21-C, and how large are its five specified
  cosine-margin contrasts?
- **Takeaway:** after a block-21 readout reset, glyph-position disruption and
  restoration exceed equal-count suffix controls on 195 items. This is a
  conditional margin effect, with zero mean absolute top-1 effects.
- **Family / sufficiency:** a three-step schematic above five one-sided
  interval marks; all five original contrasts remain visible.
- **Renderer / encoding:** static Matplotlib, circles for decrement, squares
  for restoration, and a neutral calibration diamond. Segments run from each
  simultaneous one-sided 95% lower bound to its mean; they are not two-sided
  confidence intervals. Two carriers and two donors are averaged within items.
- **Output / QA:** `figures/t21_path_summary.pdf`; source only the original
  `confirmation_result.json`, check all five bounds, preserve a zero reference,
  and test 3-point box insets at three resolutions. The secondary symbol plot
  moves to Appendix C so the main text remains within nine pages.

### Figure 5 - exploration-to-confirmation lineage

- **Question:** Which earlier results changed the design that became T19?
- **Takeaway:** token-structure and persistence studies narrowed the endpoint;
  later lexical and causal studies motivated the two-arm design. Earlier
  stages do not enter the T19-L primary evidence denominator.
- **Family / sufficiency:** annotated decision lineage; the five grouped stages
  summarize T1--T20 without treating the sequence as evidence accumulation.
- **Renderer / encoding:** static Matplotlib; gray for token/persistence
  diagnostics, blue for lexical/boundary studies, and orange for the T19/T20 tests.
- **Output / QA:** `figures/t19_lineage.pdf`; verify every study label against
  Appendix A and inspect all box labels and arrows in the compiled paper.

### Figure 7 (Appendix D) - component-level causal test

- **Question:** Does any prespecified late site have both random-adjusted necessity
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

## Remaining submission boundary

- the reproducibility-disclosure answer is `Yes`: the protocol, exact model
  revisions, selections, training settings, seeds, and analysis code support
  reacquisition from the referenced checkpoints;
- open access and compute remain `No`: the compact artifact omits raw arrays
  and the full intervention ledger, and exact T19 acquisition duration/peak
  memory are absent from the submitted records;
- resolve author list and acknowledgments only after the double-blind copy is
  finalized;
- upload early enough to verify the OpenReview record.

The paper answers **No**, not **N/A**, to open access to data and code. The
official checklist reserves N/A for papers without experiments requiring
code. The new archive closes the anonymous compact-audit and documentation
gaps, but not exact raw replay. A planned full public release after review does
not change the submission-time answer. License, ethics, new-asset
documentation, and conservative LLM-assistance declaration are now complete.
