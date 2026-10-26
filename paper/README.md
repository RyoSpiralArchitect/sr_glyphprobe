# GlyphProbe Phase I paper

[Japanese](README.ja.md) | [Current claims](CURRENT_CLAIMS_20261015.md) | [Revision notes](REVISION_NOTES_20261015.md) | [Historical claims](CLAIM_TABLE.md)

Status, 2026-10-26: **standalone preprint version 1.0.0 remains the published
October 15 version; the original research repository is now public**.
[Current PDF](../output/pdf/glyphprobe_preprint_20261015.pdf) ·
[Public-release guide](PUBLIC_RELEASE_20261015.md) ·
[License scope](PUBLIC_LICENSES_20261015.md) ·
[Fresh-eye review and response](FORK_REVIEW_PUBLICATION_20261015.md).
The [Zenodo record and DOI `10.5281/zenodo.23376699`](https://zenodo.org/records/23376699)
are public, with an open version 1.0.0 preprint dated October 15, 2026.
The curated [sr_glyphprobe-public repository](https://github.com/RyoSpiralArchitect/sr_glyphprobe-public)
remains available. The original [sr_glyphprobe repository](https://github.com/RyoSpiralArchitect/sr_glyphprobe)
is also **public**. Its October 26 integration adds reviewed research files
without importing the unpublished development history wholesale. See the
[integration scope](../docs/PUBLIC_INTEGRATION_SCOPE_20261026.md) and
[next-paper theme](../docs/PAPER_NEXT_THEME_20261026.md). The latter is a research
proposal, not a new result or an amendment to the fixed T22 384-item design.
Individual author answers, assignments, protected holdouts, operational handoffs
and raw machine-specific runtime records are excluded from this integration.
This scoped review does not certify every prior commit or artifact.
The archive and its manifests retain their pre-publication preparation metadata
unchanged. The Zenodo record and this live README report the separately verified
publication; the preparation records are not rewritten retrospectively.
The September manuscript and anonymous archive are retained as historical artifacts;
they do not cover the October contextual or readout-qualification results.
See the [descriptive experiment guide](EXPERIMENT_GUIDE.md) and
[revision and release plan](../docs/POST_REVIEW_REVISION_20261007.md).
The revised PDF retains the historical results, contextual response measurements,
and aggregate results from an author-only tryout. A new, prospectively specified
text-only qualification tests the measurement on explicit reports before further
emoji interpretation. Historical confirmation, contextual development, and
finite-set readout qualification have separate claim boundaries. Independent
semantic validation and output-linked causality remain open. See the
[research reassessment](../docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.md).
The author has approved CC BY 4.0 for the current paper, its original figures,
and newly released public data; code and ordinary project documentation retain
Apache 2.0. Third-party and historical notices remain in force. The
[public-release guide](PUBLIC_RELEASE_20261015.md) distinguishes preparation from
publication and specifies the evidence included and omitted.

This preprint was revised in response to reviewer feedback from the NeurIPS 2026
workshop **Interpretability as a Science (InterpScience)**. It is not an accepted
workshop or proceedings paper.

The October 15 qualification completed **4,640/4,640 forwards** and passed numerical
and independent saved-score checks. Its prespecified scientific requirements
were not met: direct/minimal answers were correct on **88/96** reserved cases
(four incorrect, four tied; eight of 16 roots completely correct), and the two
direct-question A/B mappings were correct on **104/192** cases with 19 ties.
All formats, failures, and denominators remain in the paper and public projection.
This closes the specified finite experiment without qualifying the readout for
semantic or ordinary-output causal claims.

The current manuscript uses standard `article`, `geometry`, Times text fonts,
and `natbib`; it does not load the NeurIPS style or submission checklist.
The concise factual collaboration acknowledgment retains the roles and
provenance limitations without conference-policy boilerplate. This formatting
and release revision changes no scientific result and claims no conference acceptance.
The English paper is the controlling scientific text. This bilingual README
documents the build, evidence boundary, and figure contracts; it is not a
second manuscript.

## Files

- `main.tex`: author-named English standalone preprint.
- `references.bib`: references used by the draft.
- `neurips_2026.sty`, `checklist_template.tex`, and `checklist.tex`: preserved
  historical workshop assets; none is a dependency of the current manuscript.
- `scripts/build_figures.py`: deterministic figure builder from compact,
  validated T19/T20/T21 JSON summaries.
- `scripts/build_anonymous_artifact.py` and
  `scripts/validate_anonymous_artifact.py`: whitelist-only deterministic
  archive builder and independent integrity/identity-boundary validator.
- `figures/manifest.json`: input and output SHA-256 receipts generated with the
  figures.
- `ASSET_LICENSES.*`, `COMPUTE_REPORT.*`, and `ETHICS_REVIEW.*`: paired
  English/Japanese submission audits.
- `contextual_development_20261010.tex`: descriptive contextual measurement appendix.
- `contextual_input_examples_20261015.tex`: complete public prompt and candidate examples.
- `readout_qualification_20261015.tex`: explicit-report qualification design and results.
- `generated/contextual_development_tables_20261010.tex`: aggregate-only tables,
  generated by `scripts/build_development_summary_20261010.py`; never edit by hand.
- `../validation/contextual_emoji_working_revision_20261010/summary.json`:
  rechecked aggregates and provenance; individual author records are excluded.
- `../output/pdf/glyphprobe_preprint_20261015.pdf`: exact published standalone preprint.
- `../output/pdf/glyphprobe_t19_first_draft.pdf`: preserved September review PDF.
- `../artifacts/public_release_20261015/historical/glyphprobe_t19_anonymous_evidence_v4.zip`:
  byte-preserved September compact artifact inside the public payload.
- `PUBLIC_RELEASE_20261015.md` and `PUBLIC_LICENSES_20261015.md`: current
  release scope, license grant, exclusions, and portable replay instructions.
- `../output/artifacts/glyphprobe_public_release_20261015_v2.zip`: exact archive for
  published version 1.0.0, with its preparation records unchanged.
- `../artifacts/public_release_20261015/`: unchanged extracted public payload;
  its exact roster is bound by `ARTIFACT_MANIFEST.json` and `SHA256SUMS`.
- `../artifacts/public_release_20261015/evidence/readout_qualification_v1/specification.public.json`:
  portable public input and execution projection, paired with complete saved
  scores and projection bindings in the same directory.
- `RELEASE_CANDIDATE_20261015.md`: historical guide whose original build/replay
  paths require the local acquisition archive; it is not the public replay entry point.

Intermediate October 7/10/15 PDFs and the earlier candidate ZIP are not included
in this integration. The raw qualification specification/run directory and
machine-specific acquisition records are also excluded. Historical references
to those paths describe the author's local archive, not missing prerequisites
that a public reader should reconstruct or bypass. Use the public projections
and verification command below. Other selected scientific files are partial
evidence, not a complete-run numerical replay bundle.

The historical official formatting archive was downloaded from
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`.
Its SHA-256 is
`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
Copying the style files into this directory does not imply workshop acceptance
or submission readiness.

The September submission used `dblblindworkshop`; the earlier October candidate
used `preprint`. The current standalone paper uses neither mode or style and
contains no submission checklist. The historical style file itself remains
unchanged. Historical PDF and archive files are not rebuilt by the commands below.

## Build

From the repository root:

```bash
tectonic -X compile \
  --outdir "$PWD/paper/build/public_preprint_20261015" --outfmt pdf \
  --keep-logs --keep-intermediates --untrusted "$PWD/paper/main.tex"
cp -n paper/build/public_preprint_20261015/main.pdf output/pdf/glyphprobe_preprint_20261015.pdf
```

Tectonic runs the BibTeX pass automatically. On the validated Mac, invoke the
bundled executable directly or select `--compiler tectonic` in the Codex
`latex-compile` helper. Its automatic mode flags bibliography tooling for
TeX Live, which is absent on this host. The final copy is made only
after citation, page-count, text-extraction, and rendered-page checks.
`paper/build/` and `tmp/pdfs/` are intermediate surfaces.

Historical figures are retained unchanged. The checked public aggregate and
generated tables suffice to build this paper. Regenerating individual human
counts requires records excluded from the public scope and is not part of
these instructions. Do not import those records, raw runtime files or operator
handoffs to make a historical full-run test pass.

## Public saved-score verification

From the repository root, Python's standard library is sufficient:

```bash
python3 -B artifacts/public_release_20261015/paper/scripts/build_public_release_20261015.py \
  verify artifacts/public_release_20261015
```

This checks the immutable payload roster/hashes and recomputes the complete
4,640 saved qualification records with two arithmetic implementations. It does
not perform model forwards or independently reconstruct GPU logits. It cannot
replay individual human answers or every historical causal state array.
`publication_verified: false` is intentional: package integrity and saved-score
arithmetic are separate from the live [DOI record](https://doi.org/10.5281/zenodo.23376699).
Do not change the package's preparation metadata to match later publication.
The [published ZIP](../output/artifacts/glyphprobe_public_release_20261015_v2.zip)
has SHA-256 `36959018915a13b988d83b7db13b9e3bb91b6e3a660649cbc8a270340b68f409`.

## Recorded October 15 standalone validation

The standalone PDF has **36 pages**. The October 15 record reports **231 targeted
tests passed**, with no overfull boxes or undefined references. These are
historical checks, not a report that this suite ran during the October 26
integration. The unchanged
[public document-validation record](../artifacts/public_release_20261015/evidence/document_validation.public.json)
binds the checks to PDF SHA-256
`9f9a34b578b8eeec6dd8f08994fa348ea050d5477c3387663cc885d9cd30d673`.
These local document and test checks do not establish publication, successful
scientific qualification, or independent semantic validation.

## Historical validation records

The checks and hashes in this section belong to preserved earlier PDFs and
archives. They do not validate a new standalone PDF or establish publication.
Current packaging and verification instructions are in
[PUBLIC_RELEASE_20261015.md](PUBLIC_RELEASE_20261015.md).

Earlier October 15 candidate checks: 35 pages; main text ends on page 11; Appendix I
occupies pages 29--32 and adds Tables 15--16. All **198 targeted tests** pass
with zero failures, errors, or skips. Compilation has no overfull boxes or
undefined references/citations; underfull spacing warnings remain. Every page
was inspected in contact sheets, with detailed checks of the revised text,
input examples, reference-swap tables, and new result tables. The last layout
adjustment changed only pages 31 and 34; both were re-inspected, and the other
33 page renders remained byte-identical. The candidate-era local document receipt
(`validation/revised_preprint_20261015/document_validation_v2.json`, not included here)
separates document checks from the failed scientific qualification and from
publication. PDF SHA-256:
`8f9f5cc873470b9fcbfed6649adda3a0cfb7cba4dc0c3d7f9cdfcd9c744ce43e`.
The version-specific local package
(`glyphprobe_revised_preprint_20261015_candidate_v2.zip`, not included here)
is distinct from the historical archive below; its manifest and replay command
are described in the [release guide](RELEASE_CANDIDATE_20261015.md).
The original 189-test receipt is retained. The final suite adds nine packaging
regressions for macOS temporary directories without changing scientific inputs,
scores, or the PDF.
The v2 archive was extracted into a separate temporary directory and verified
using only the extracted files and Python's standard library: both saved-score
implementations agree, with no model forwards. Archive SHA-256:
`8048e9178479d3109e77fb082ab8dda8956b0fcf489644f307da139813fd94ee`.
That candidate remains a preserved local artifact; the current release uses the
separate standalone PDF. The failed qualification is retained in both.

Historical October 10 draft checks: 29 pages; main text ends on page 11; Appendix H
occupies pages 24--26. Four added tables retain the matched-execution results,
author-answer denominators, model preferences, and question-polarity contrasts.
All 65 targeted tests pass with zero failures, errors, or skips. Compilation has
no overfull boxes or undefined references/citations; underfull spacing warnings
remain. All page layouts were inspected, with full-size checks of changed text
and tables. The local document receipt
(`validation/contextual_emoji_working_revision_20261010/document_validation.json`, not included here)
separates these checks from semantic and release readiness. PDF SHA-256:
`7ade305ceaea7eaffb9a67b8cce8f301f425e95163e98344a758a834f8879abd`.

The preserved October 7 revision introduced four descriptive experiment names, a common
input/readout example, token-count matching clarification, the provenance and
limits of the 0.02 floor and block indices, and saved-summary threshold/depth
sensitivity. It corrects language that could imply already demonstrated
behavioral effects. Historical numerical decisions are unchanged. The sections
below describing v3/v4/v5 archive checks concern the September submission,
not a newly rebuilt anonymous package.

Archived October 7 PDF check: 25 pages; main text ends on page 10. Compilation reports
no overfull boxes or undefined references. All pages were visually checked;
after the final pagination change, reference/appendix page bodies were
pixel-identical to the inspected render, and the changed main-text pages were
checked again. The 21 existing figure/evidence checks pass. PDF SHA-256:
`43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898`.
These checks precede the new experimental model forwards and establish document
quality only. At that historical check, no new deposit had occurred.

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

## Historical prespecified claim boundary

This section records the September studies and artifact versions. Current
contextual-development and readout-qualification claims are bounded separately
in [CURRENT_CLAIMS_20261015.md](CURRENT_CLAIMS_20261015.md).

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

Revision v5 retains the separately specified T21-C result on 195 further items:
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
Raw-state validation remains separate. Archives v1, v2, and v3 are historical
local-archive versions, not added by this integration; the archive validator
accepts all four versions. The unchanged v4 is included in the public payload.

The v4 archive contains the final reader-facing revision. The abstract states
the lexical question first, and the introduction uses the prespecified
U+1F923 / `lmao` pair to illustrate the design. Word disjointness concerns
official-name/keyword words; it does not exclude shared subwords or training
co-occurrence. T20's swap asymmetry motivates T21 without establishing
redundant coding or a complete explanation across their different populations
and endpoints. Final-block full-state replacement is an expected consistency
check, and the block-24 attention `2%` is explicitly a sufficiency effect.

Saved T21 condition means supply post-reset baseline accuracy of `3.08%`
(pipe) and `0.51%` (article carrier), at block 21 and distance 8 on all 195
items. These rates motivate a sensitivity caveat, not a demonstrated floor
effect or equivalence claim. The OLMo 2 citation and Apple Silicon origin of
the Llama mirror are clarified. This revision adds no model runs or statistical
replays and changes no experimental result. Read-only regression tests bind
the reported percentages to the existing condition means.

The final Appendix G disclosure names the author-reported ChatGPT and Claude
Chat configurations for author-side pre-submission feedback, and Codex and
Claude Code configurations for implementation and analysis. It also retains
protocol-design and editing involvement. This activity is explicitly separated
from conference peer review. Checklist item 16 points to the disclosure;
the anonymous submission contains no acknowledgments section. See the
[paired ethics disclosure](ETHICS_REVIEW.md).

Final local checks for revision v5: the PDF has 23 pages, with the main text
ending on page 9 and references beginning on page 10. All pages were inspected
after rendering; no clipped labels, overfull boxes, or undefined citations were
found. The selected manuscript, figure-layout, and table regression tests pass
(29 tests). These are document and packaging checks, not new scientific runs
or confirmation of OpenReview submission.

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
  gap at block 27, an expected endpoint-consistency check.
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

## Historical submission boundary

The following records the September submission-time answers and workflow, not
requirements for the current standalone release. The present manuscript has no
workshop checklist. Its release state and scope are documented above.

- the reproducibility-disclosure answer is `Yes`: the protocol, exact model
  revisions, selections, training settings, seeds, and analysis code support
  reacquisition from the referenced checkpoints;
- open access and compute remain `No`: the compact artifact omits raw arrays
  and the full intervention ledger, and exact T19 acquisition duration/peak
  memory are absent from the submitted records;
- resolve author list and acknowledgments only after the double-blind copy is
  finalized;
- upload early enough to verify the OpenReview record.

The historical paper answered **No**, not **N/A**, to open access to data and code. The
official checklist reserves N/A for papers without experiments requiring
code. The new archive closes the anonymous compact-audit and documentation
gaps, but not exact raw replay. A planned full public release after review does
not change the submission-time answer. License, ethics, new-asset
documentation, and conservative LLM-assistance declaration are now complete.
