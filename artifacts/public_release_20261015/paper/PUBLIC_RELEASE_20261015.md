# Standalone preprint and evidence release

[日本語](PUBLIC_RELEASE_20261015.ja.md)

This package prepares the revised standalone preprint **Beyond Short Names:
Emoji Keyword Retrieval across Models and Bounded Causal Tests** for public
release. The current PDF is `paper/preprint.pdf`; the current source starts at
`paper/main.tex`. The paper uses standard LaTeX packages, without the workshop
style or its submission checklist. This preprint was revised in response to
reviewer feedback from the NeurIPS 2026 workshop *Interpretability as a Science*
(InterpScience). It is not an accepted workshop or proceedings paper.

The author confirmed CC BY 4.0 for the author-owned paper, paper-specific
figures, and newly released public data. Code and ordinary project documentation
retain Apache 2.0; third-party and historical notices remain in effect. See
[the scope-specific license guide](PUBLIC_LICENSES_20261015.md). A license does
not imply verification of scientific claims.

`prepared_public_release` describes a locally assembled package. It does not
assert a Zenodo deposit, DOI registration, public Git repository, or peer-review
acceptance. A public record and its externally observed identifier must be
reported separately after publication. No public Git URL is assumed here.

## Evidence and limits of replay

| Evidence | Included material | Supported check and boundary |
|---|---|---|
| Current paper | PDF, literal TeX/BibTeX dependencies and figure PDFs; current claims and revision notes | Read the standalone paper and rebuild with a suitable TeX installation. If supplied, the document-validation receipt is bound to the exact PDF SHA-256. Packaging is not a substitute for visual inspection. |
| Historical lexical retrieval (T19-L) | Unchanged September compact archive, under `historical/` | Its documented replay reconstructs primary-window inference from saved prediction indices. This is not a fresh model evaluation or reconstruction of all activations. |
| Historical rank-8 and optimized-subspace tests (T19-C/T20-C) | Summaries and selected diagnostics in the historical archive | Summary inspection only; the archive does not contain every raw intervention/state array needed for a complete independent causal rerun. |
| Historical conditional attention-path test (T21-C) | Saved contrasts and margin components in the historical archive | Its documented inference replay uses saved contrasts. Natural-state mediation and independent GPU-logit reacquisition are not established. |
| Contextual development | Public authored scenario inventory, wording, two-track source, exact manuscript examples, aggregate tables | Reconstruct authored inputs and inspect aggregate outputs. Not all earlier per-token scores or acquisition receipts are included. |
| Author tryouts | Previously exported aggregate counts | No individual answers, assignments, notes, or private packets. Response-selected agreement is not independent accuracy; item-level human replay is unavailable. |
| Explicit-report readout qualification | Logical inputs, token IDs, all 4,640 scheduled score records, numerical-equality hashes, analysis, source/runtime bindings | Replay saved-score statistics and recorded gates using two separate arithmetic implementations. This does not reacquire or independently reconstruct GPU logits. Negative outcomes and ties are retained. |

The nested historical archive is retained byte-for-byte at SHA-256
`33cadc408d550781454aa95aa5af7ea2f1c62a1411d2cabaaf9ac561afe1a84e`.
Its paper and checklist are historical artifacts, not the current manuscript.
The release builder hashes this archive without extracting or newly inspecting
its contents. Historical notices are not replaced by the new data grant.

## Portable readout records

`evidence/readout_qualification_v1/` contains explicit-field public projections:
`specification.public.json`, `forwards.public.jsonl`, `analysis.public.json`,
`independent_validation.public.json`, `run_summary.public.json`,
`runtime_dependencies.public.json`, and `projection_binding.json`.
The projections retain complete scheduled cases, prompts, continuations, token
IDs, status, scores, reference labels, failed qualifications, and ties. They omit
machine paths, process metadata, and potentially identifying exception text;
run-level execution/source-binding failure remains an explicit boolean.

The builder checks the specification digest retained before execution, all raw
run hashes and source bindings, and equal analyses before and after projection.
The second arithmetic implementation is checked on both forms when its
complete-run numerical conditions hold. No raw receipts are edited. No model
forward, tokenizer operation, download, or upload occurs during packaging.

## Local build

Run in the source repository with Python and `pypdf` available. Use a previously
nonexistent output path; existing archives are never overwritten. The optional
document-validation receipt must bind the exact new standalone PDF. Omit that
option if no corresponding validation exists; never reuse a candidate-era PDF
receipt for another PDF.

```bash
python3 -B paper/scripts/build_public_release_20261015.py build \
  --pdf output/pdf/glyphprobe_preprint_20261015.pdf \
  --specification validation/readout_qualification_v1/specification.json \
  --expected-specification-sha256 5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f \
  --run-directory validation/readout_qualification_v1/run4640 \
  --author-license-confirmed \
  --output output/artifacts/glyphprobe_public_release_20261015.zip
```

Optional `--document-validation FILE` includes the checked receipt at
`evidence/document_validation.public.json`. Optional `--metadata FILE` includes
operator-confirmed public metadata. If it contains a DOI, it must identify an
externally reserved DOI with `doi_status_at_preparation: "reserved_not_registered"`
(or the compact `doi_state: "reserved"`); this option neither
reserves nor verifies an identifier and never represents the deposit as public.
The builder's return value is a local integrity receipt, not publication proof.

`ARTIFACT_MANIFEST.json` records exact files, sizes, hashes, license categories,
privacy-check classes, and the non-published preparation state. `SHA256SUMS`
also binds the manifest. Exact allowlists and literal TeX dependencies avoid
copying the whole private repository. PDF text, metadata, annotations, and
bytes receive conservative mechanical scans; author privacy/rights review is
still necessary. This is a named-author public preprint, not an anonymous file.

ZIP timestamps are fixed solely for reproducibility, not to assert the time of
an experiment or public deposit. Model/tokenizer files, private participant
records, installations, caches, and credentials are excluded.

## Verify after extraction

From the extracted package root, before adding files there:

```bash
python3 -B paper/scripts/build_public_release_20261015.py verify .
```

Verification uses Python's standard library only, checks the exact roster and
hashes, checks the current manuscript's standalone dependencies, and replays
the new qualification scores in both arithmetic implementations. The older
candidate builder is included solely as an unchanged utility dependency; its
old license and publication-status defaults do not govern this package.

The historical archive has separate documented replay commands. Successful
checks establish package integrity and saved-score arithmetic, not semantic
validity, independent human confirmation, or an unobserved causal mechanism.

