# Author-pilot analysis: description before comparison

[日本語](CONTEXTUAL_EMOJI_AUTHOR_PILOT_ANALYSIS_V0.ja.md) · [Collection protocol](CONTEXTUAL_EMOJI_AUTHOR_PILOT_V0.md)

2026-10-10. This document describes the local analysis workflow, not participant outcomes. Human responses, free text, derived item tables, reports, exposure receipts, and the executed notebook stay outside Git in a private analysis directory. They must not be silently promoted to public artifacts or human-gold labels.

## Ordered stages

1. After batch finalization, run `scripts/analyze_contextual_emoji_author_pilot_v0.py describe` with explicit `--package`, `--journal`, `--handoff`, and private `--output` paths. This stage opens the participant payload and journal, not the two keys or model outputs. It checks the public handoff hashes and replays the bound server's event validation through a read-only descriptor, without changing the journal or server.
2. Read the resulting local `phase_one_summary.json` and `phase_one_items.json`. Write a paired `PHASE_ONE.md` / `PHASE_ONE.ja.md` interpretation, preserving all recorded categories, notes, missingness, and uncertainties. Do not recode responses toward the authored expectation.
3. Run the same script's `seal --output <private-directory>` command. It creates an exclusive-write hash record of the two data files and two notes. Do not modify these files after comparison access.
4. Only after explicit authorization, record a separate local comparison-exposure event bound to that seal. Distinguish assistant access, participant-visible feedback, and actual participant reading; one does not prove the others.
5. Run `scripts/compare_contextual_emoji_author_pilot_v0.py` with `--output`, `--package`, and `--handoff`. It refuses altered pre-key notes or unbound exposure, verifies the original package/keys, and joins only the actually assigned views to the pinned matched-shape model records. Exact prompt/candidate strings, display-order mappings, join uniqueness, and raw score arithmetic must agree.
6. Execute a private companion notebook top-to-bottom to reproduce both stages and verify that source records remain unchanged. Re-execution after reveal does not recreate analyst blinding. Keep interpretations before and after key access as separate records.

These are local CPU operations with no model/tokenizer/generation calls. Re-running a command must not overwrite an earlier analysis; inspect an existing result or create an explicitly versioned output when a change is needed. Keep the collection protocol and interface files unchanged because the response journal binds their hashes.

## Denominators and limits

Report planned, assigned, completed-including-abstention, eligible non-abstaining, binary-choice subset, and missing counts separately. The binary subset is selected by the recorded response category; it is not a representative sample and does not replace the full denominator. A model given two candidate sequences has no corresponding Both/Neither/Ambiguous/Unclear option. Neither authored-label agreement nor model agreement is independent semantic accuracy.

Retain zero-count categories and missing optional recognition/naturalness fields. Treat session wall time as elapsed time, not measured active effort. Saved actions do not establish item-view histories. Keep self-reported exposure and known prior involvement separately, without inferring independence from one self-report.

Group summaries by carrier, response formulation, or family are descriptive development diagnostics. They do not establish carrier effects, candidate equivalence, causal mechanisms, inter-rater reliability, or generalization. Do not choose thresholds, exclusions, or inferential tests from observed agreement. Any clarification from the rater after comparison is a dated amendment, never an overwrite of the original response.

## Synthetic-only checks

The description tests cover complete category accounting, missing optional fields, revision preservation, finalization, duplicate/orphan records, temporal ordering, exclusive writes, and required pre-key notes. Comparison tests cover reversed display order, non-binary preservation, ties, duplicate/missing joins, literal text, raw scores, key mappings, and unchanged inputs. The existing generator/server tests remain part of the regression check. Tests contain synthetic data only.
