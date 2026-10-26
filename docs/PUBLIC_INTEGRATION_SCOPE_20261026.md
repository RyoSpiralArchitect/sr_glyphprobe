# Public integration scope — October 26, 2026

[日本語](PUBLIC_INTEGRATION_SCOPE_20261026.ja.md)

## Purpose and status

This note defines the October 26 integration scope for `sr_glyphprobe`.
The original repository is currently public. The author has chosen to keep it
public and integrate only material reviewed for that audience. This is a scope
record, not a statement that tests, push, merge, or a new scientific study have
completed. Their outcomes must be recorded separately.

The October 15 preprint remains version 1.0.0 at
[Zenodo](https://doi.org/10.5281/zenodo.23376699). Its immutable PDF, archive,
preparation manifests, and scientific decisions are not revised by this
integration. A proposal for the next paper is not a new confirmed result.

## Included categories

- Reviewed research implementation, synthetic tests, authored development
  inputs, and paired English/Japanese research notes.
- The already published preprint and reproducibility package, with their
  original checksums and license scopes.
- Public evidence projections and aggregate reports within their documented
  scope. Their availability does not imply that omitted raw records are public
  or that every historical experiment can be independently replayed.

Only explicitly selected paths are added. The unpublished development branch's
commit history is not imported wholesale. The actual staged-file list and
commit identify the precise integration; this category list is not an
authorization to add other files later.

## Excluded categories

- Individual author responses, assignments, concealed-label packets, journals,
  and other private participant records.
- Retired/protected holdout-bank contents, which are not reopened or reused.
- Raw machine-specific runtime/source-location records, process and GPU
  occupancy snapshots, and operational handoff instructions.
- Model/tokenizer assets, environments, caches, credentials, and local build
  or browser working files.
- Unreviewed notebooks, binary artifacts, and historical intermediate bundles.

Real machine paths are not removed by editing a generated receipt in place.
Where portability is needed, an explicit public projection must be produced
with a binding to its source records. The published qualification package
already supplies such projections. Its original preparation status remains
historical metadata, distinct from later publication and integration records.

## Validation boundaries

The local targeted regression run completed with **618 passed, 52 skipped and
72 subtests passed**. Forty-six skips explicitly require excluded archive
material; six retain the existing saved-acquisition availability guard. They
are not passes. `tests/conftest.py` maps only the affected tests, without
changing frozen scientific runners or their tests. Passing
`--require-archive-evidence` disables the new missing-archive skips and lets
the original checks fail normally when their prerequisites are absent.

The public package passed its standard-library-only integrity and saved-score
replay. A separate local Tectonic 0.17.0 build produced 36 pages with no
overfull boxes or unresolved references; underfull warnings remain. The
published PDF and archive remain byte-identical, and all T22 source, design
and evidence paths match the integration base. The
[generated audit](../validation/public_integration_20261026/audit.json) binds
selected files, test-output and build-log hashes. It does not assert a remote
push, merge, new scientific acquisition or new visual page review.

The 30 selected historical machine-science/aggregate files are deliberately
partial: omitted specifications and runtime records prevent complete-run
revalidation. Their original bytes and conclusions are retained. The
immutable `artifacts/public_release_20261015/` package provides the separate,
fully specified public saved-score replay route.

Synthetic tests and source checks can validate implementation properties without
access to private acquisition material. Tests requiring excluded historical
runtime or raw-run files must be reported as unavailable in the public scope;
they must not be made to pass by silently importing those files or weakening
their checks. A passing public saved-score replay establishes package integrity
and recorded-score arithmetic, not a new model acquisition or human validation.

The complete explicit-report qualification recorded 4,640 forward attempts and
passed numerical checks. Its prespecified direct/minimal and answer-label
requirements both failed. Those negative scientific outcomes remain separate
from software-test success.

This review concerns the newly selected integration. It is not a certification
of every file, commit, external artifact, or historical permission already
present in the public repository.
