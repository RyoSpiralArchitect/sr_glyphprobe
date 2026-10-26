# Revised-preprint release candidate

[日本語](RELEASE_CANDIDATE_20261015.ja.md)

This guide specifies a **local publication candidate**, not a public deposit.
No DOI is reserved or registered by its builder. Publication, author metadata,
and final licenses require a separate author decision. An earlier submission
received feedback from the NeurIPS 2026 Workshop Interpretability as a Science;
the revised preprint is not an accepted conference or proceedings paper.

## Current paper and evidence boundary

The candidate puts the current PDF at `paper/revised_preprint.pdf`. The exact
roster, sizes, SHA-256 values, privacy-check classes and provisional license
classifications are generated in `ARTIFACT_MANIFEST.json` **only when the build
actually succeeds**. `SHA256SUMS` also binds that manifest. No numbers in this
guide anticipate the new experiment's outcome.

| Evidence surface | Included | Reproduction boundary |
|---|---|---|
| Current manuscript | PDF; current TeX/BibTeX and referenced figure PDFs; compute, ethics and descriptive experiment guides | Inspect the current paper and rebuild after obtaining the separately identified official style and a suitable TeX runtime. Packaging does not itself certify PDF/source correspondence or layout. |
| Historical lexical and causal studies | Unchanged September compact evidence archive, explicitly under `historical/` | Its existing instructions support T19 primary-window inference from prediction indices and T21 inference from saved contrasts. Full activations/intervention arrays and checkpoint files are absent. The nested paper is historical, not the current PDF. |
| Contextual development | Public authored scenario inventory, two-track design/runner source, exact examples in the manuscript, and the October 10 aggregate summary/tables | The public source reconstructs the authored input grid. Aggregate tables can be inspected, but this candidate does not contain all earlier model-token scores. Reacquisition requires upstream checkpoints, the historical runtime and additional pinned acquisition receipts. |
| Author tryout | Previously exported aggregate counts only | Individual answers, assignments, notes and private packets are absent. Response-selected agreement is not independent accuracy, and item-level recomputation from these public aggregates is impossible. |
| Explicit-report readout qualification | Prespecified logical inputs, token IDs, all scheduled per-token score records, recorded equality checks, CPU analysis, source hashes and portable dependency receipts | Recompute statistics and recorded numerical gates from saved scores without a model. This is not independent reconstruction of the original GPU logits or a guarantee of bitwise model reacquisition. All failed, missing and tied cells remain represented. |

The legacy archive is accepted only at SHA-256
`33cadc408d550781454aa95aa5af7ea2f1c62a1411d2cabaaf9ac561afe1a84e`.
The new builder hashes it as an opaque, previously validated historical file;
it neither extracts its banks nor represents this as a fresh content audit.

## New-run portable projection

The files in `evidence/readout_qualification_v1/` are explicit-field projections,
not edited experimental originals:

- `specification.public.json`: complete logical cases, development/reserved-check
  split, expected labels, exact prompts/continuations and token IDs; minimal
  historical sentinel cases and expected scores needed for replay.
- `forwards.public.jsonl`: every scheduled event, execution status, geometry,
  per-candidate token log probabilities, sums, and predictor-equality hashes.
- `analysis.public.json`: the exact CPU replay of saved scores; it retains
  unsuccessful qualification and incomplete numerical status when applicable.
- `independent_validation.public.json`: a second arithmetic implementation checks
  the public inputs, reference rule, schedule, recorded equality gates, sums and
  summaries. It imports neither acquisition nor its analysis. An explicit
  adapter compares its results on original and projected data; validator-code
  and projected-file hashes are recorded. Incomplete or numerically failed runs
  are marked not evaluable, never certified by that complete-run checker.
- `run_summary.public.json`: bounded compute totals and status. A boolean retains
  whether a run-level execution/source-binding failure occurred; potentially
  host-identifying error text is omitted, not silently treated as success.
- `runtime_dependencies.public.json`: package/Python versions, scoring settings,
  model-file hashes and implementation-source hashes, without local paths or
  model/tokenizer bytes.
- `projection_binding.json`: original specification/run-file hashes and the
  acquisition source hashes. This maps the projection to locally retained raw
  receipts without publishing their machine paths, process records or errors.

The builder requires the specification digest retained before execution, verifies
raw run-file hashes, source bindings and inventory, then requires identical
analyses before and after projection, including the separate implementation when
its complete-run conditions hold. It never modifies raw
receipts. It reads no private participant material and performs no model forward,
tokenizer call, download, GPU operation or network upload.

## Build locally

Use a new, nonexistent output path. The following is an invocation template,
not a claim that these files or a completed candidate already exist:

```bash
python3 -B paper/scripts/build_release_candidate_20261015.py build \
  --pdf output/pdf/glyphprobe_revised_preprint_20261015.pdf \
  --specification validation/readout_qualification_v1/specification.json \
  --expected-specification-sha256 5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f \
  --run-directory validation/readout_qualification_v1/run4640 \
  --output output/artifacts/glyphprobe_revised_preprint_20261015_candidate_v2.zip
```

The v2 package repairs verification in macOS system temporary directories;
the paper and experimental scores are unchanged. Existing candidate archives
are preserved. Choose another unused output name when rebuilding.

The builder needs Python and `pypdf` for PDF privacy inspection. It refuses
missing inputs, changed bindings, existing output, unsafe paths, private packet
identifiers, secret-like strings and local filesystem/network paths in the
projected payload. Exact allowlists and literal, bounded TeX dependencies are
used; the repository is never archived wholesale. The scanner is a conservative
mechanical check, not a substitute for the author's final privacy and rights
review. Named authorship and explicitly fictional stimulus characters are
intentional; this is not an anonymous-review package.

ZIP timestamps are fixed to October 15, 2026 solely for deterministic packaging.
They are not experimental event or public-deposit timestamps. Identical payloads
produce identical archives in the same compression runtime. Original source and
receipt timestamps are not rewritten.

## Verify and replay the extracted candidate

Before creating any extra files inside the extracted directory, run from its
root:

```bash
python3 -B paper/scripts/build_release_candidate_20261015.py verify .
```

This checks the complete file roster, byte counts and digests and replays the
qualification analysis and its separate arithmetic implementation using only
Python's standard library. The two implementations are
`scripts/readout_qualification_v1.py` and
`scripts/validate_readout_qualification_v1.py`; the public-file adapter is in the
packager. The raw checker CLI expects original file names and receipts, so the
command above is the supported entry point for the public projection. A pass concerns
package integrity and saved-score calculations; it cannot establish semantic
validity, independent human confirmation or an unobserved mechanism. The
historical archive has its own separate verifier and replay instructions.

## License and privacy eligibility

| Asset | Treatment in this candidate |
|---|---|
| Current paper and paper-specific figures | **CC BY 4.0 proposed; author confirmation pending.** The builder does not grant or change that license. An earlier submission's license is not silently applied to every new file. |
| Project code and ordinary project documentation | Existing repository Apache License 2.0; complete `LICENSE` retained. |
| New derived score records and public authored inventories | Proposed release terms still require author confirmation; no upstream checkpoint rights are inferred. |
| Unicode/CLDR-derived historical material | Existing Unicode License v3 notice retained alongside the historical package; `paper/UNICODE_LICENSE.txt` also included. |
| NeurIPS formatting style | Not redistributed because a separate redistribution permission is not established here. `DEPENDENCIES.json` records the official archive URL, archive digest and exact local style digest. Obtain the style separately. |
| Model/tokenizer weights and library installations | Never included. Identifiers, file hashes and version requirements are provenance, not a license to redistribute upstream assets. |
| Private participant records | Never read or copied. No formal IRB approval, exemption or broader consent is asserted by packaging. |

Before any public deposit, review the final PDF, confirm authorship and licenses,
check the correspondence between every reported result and included evidence,
and retain the stated limitations for excluded data. Any later DOI metadata must
describe this as a revised preprint. A DOI is an identifier, not acceptance or
independent peer-review approval.
