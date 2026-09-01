# GlyphProbe T19 manuscript fresh-eyes review

## Receiver task

Act as an independent, skeptical workshop reviewer. Read the supplied anonymous
PDF first, without relying on the internal project history. Then consult the
TeX source, frozen claim table, checklist, and compact T19 result note only to
verify details.

Return a review in plain Markdown with these sections:

1. `Verdict and one-sentence contribution`
2. `Major concerns` (ranked; distinguish scientific validity from exposition)
3. `Minor concerns`
4. `Claim-boundary audit` (what is supported, overclaimed, or underspecified)
5. `Fresh-eyes continuity audit` (especially whether T19-L/T19-C and the
   Appendix lineage are understandable without prior project context)
6. `Double-blind and checklist audit`
7. `Highest-value edits before submission` (at most eight, concrete)

Do not edit files, run experiments, browse for new evidence, or infer missing
measurements. Treat absent raw arrays, exact wall-clock time, and peak-memory
receipts as explicit gaps. A positive observational result and a negative
causal gate are separate evidence; do not turn either into a mechanism claim.

## Frozen review snapshot

- Source branch: `codex/t19-lexical-symbol-causal-v0`
- Source commit before this revision: `e9fd37a0150413e0b9985d6f8cf4477b32698d8e`
- PDF SHA-256: `cd7e0dcf8f1f72459f100e0252b3e058e05512bc6fceba2eefc9f77daa3a2582`
- TeX SHA-256: `cc3214d0144d5e17593f4c65cf79bd64ee8bcb1da2b31607229301b1986e49f4`
- Claim-table SHA-256: `514088e48a47ccf334fb38c4e18663c13df4182411acf2d22695a4814f721bb0`
- Checklist SHA-256: `459f58b087c6dad4e5f2b6b08fc161ada16e9d6bdbc8c834888f1660bd7d02a9`

## Scope boundary

The request is review only. Capsule materialization is not permission to
modify the source checkout, publish artifacts, or start additional compute.
