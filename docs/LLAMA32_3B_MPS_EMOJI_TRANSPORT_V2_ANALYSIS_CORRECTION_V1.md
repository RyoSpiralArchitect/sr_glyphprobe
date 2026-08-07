# Llama 3.2 3B MPS Emoji Transport V2: Analysis Correction V1

[日本語](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_ANALYSIS_CORRECTION_V1.ja.md) · [V2 protocol](LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md)

## Status and scope

- Correction ID: `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2-analysis-correction-v1`
- Stage: post-execution, pre-endpoint correction
- Scope: the completion-path parser used for analysis admission only
- Permitted correction evidence: analyzer source and launcher-log presentation
- Scientific result values observed by a human before this correction: none
- Results reported in this document: none

This document freezes a narrow correction for a presentation-layer mismatch. It does not revise the V2 experiment, its inputs, its mathematics, or its claim class.

## Operator-attested incident record

The details of the two failed analyzer invocations below are an operator attestation. They are not cryptographically bound to saved failed-invocation commands, terminal logs, or timestamps. The completed execution receipt and the original launcher logs are separately hash-bound evidence.

The frozen V2 execution grid completed successfully: all 10 of 10 cells remain execution-valid. Execution validity means that the frozen execution evidence for every cell is complete and internally consistent. It is not a statement about an endpoint value or scientific success.

The analyzer was then invoked twice. In both invocations, the program loaded and validated the run arrays, but stopped at the launcher-log binding check. Neither invocation reached endpoint construction or bootstrap computation, and neither produced analysis output.

The machine-level load is not human outcome exposure. No endpoint, control statistic, interval, bootstrap value, or other result value was printed for or inspected by a human during either failed invocation.

| Event | State | Human result-value exposure |
|---|---|---|
| Frozen V2 execution | 10/10 cells execution-valid | No analysis result implied |
| Analyzer invocation 1 | Stopped before endpoint construction and bootstrap | No result values shown |
| Analyzer invocation 2 | Stopped at the same admission check | No result values shown |
| Correction selection | Based only on source control flow and log presentation | No metric- or outcome-based selection |

## Root cause

Rich used an 80-column presentation width for the non-TTY launcher output. A long run-directory path after the `Complete` marker was therefore wrapped across two physical log lines. The existing admission check searched for the expected unwrapped path as one contiguous byte sequence. The path was semantically present, but that byte sequence could not occur after Rich inserted the presentation newline.

This failure occurred after execution but before endpoint construction or bootstrap computation. It is a log-presentation mismatch, not evidence of corrupt run arrays and not evidence for or against the experimental hypothesis.

## Why this correction is admissible

The correction was chosen from two non-outcome observations only:

1. source control flow shows that admission failed before endpoint construction and bootstrap; and
2. the launcher log shows an 80-column Rich wrap inside the completion path.

No metric values, endpoint values, control comparisons, protected-bank contents, or bootstrap results were consulted when selecting the correction. The correction must be frozen before a corrected analysis is run. Any change motivated by later result values requires a new, explicitly labeled protocol and cannot be folded into this correction.

## Frozen two-line parser

The correction permits one parser and no general log normalization. For each expected resolved run-directory path `P`, apply the following contract to the launcher log while preserving every byte and every physical line boundary:

```text
line[i]     = "Complete  "
line[i + 1] = fragment_1  # exactly 80 bytes
line[i + 2] = fragment_2  # 1..80 bytes
line[i + 3] = "{"         # generated top-level report begins
candidate   = fragment_1 + fragment_2
accept      iff exactly one marker-only line exists,
                candidate == P,
                basename(candidate) == expected_run_id, and
                neither P nor expected_run_id occurs as contiguous bytes
                anywhere in the raw log
```

The two fragments are concatenated without inserting, deleting, or normalizing whitespace or path separators. The marker is a separate physical line. Nothing is trimmed from either fragment, and both fragment lines must be immediately adjacent to the marker and to each other. An ANSI escape byte anywhere in the launcher log is rejected rather than removed.

The parser fails closed if any of the following holds:

- the count of physical lines exactly equal to the marker-only `Complete  ` record is not one;
- the two path fragments are not the two lines immediately after that marker, or the following line is not exactly `{`;
- the first fragment is not exactly 80 bytes or the second is not between 1 and 80 bytes;
- the expected path or expected run ID already occurs as a contiguous byte string anywhere in the raw log;
- the reconstructed path differs from the expected resolved path by even one character;
- the reconstructed basename disagrees with the expected run ID;
- an ANSI escape byte occurs anywhere in the raw log; or
- whitespace, a control byte, or a non-ASCII byte occurs in either path fragment.

The parser must not use basename-only matching, substring matching, fuzzy matching, unrestricted whitespace folding, unrestricted multiline joining, or path discovery from the filesystem. It reconstructs one already expected path from one exact two-line presentation record.

Parser acceptance is only the correction-layer admission step. All delegated original V2 provenance checks must subsequently pass; any failure in that chain also rejects the corrected analysis.

## Unchanged V2 evidence and mathematics

The following remain byte-for-byte unchanged:

- all original V2 launcher logs and run directories;
- all run arrays, receipts, run IDs, and row ordering;
- the original V2 freeze manifest and its digests; and
- every frozen configuration and experimental input.

The correction also leaves the mathematical contract unchanged, including endpoint definitions, estimands, aggregation, controls, random seeds, bootstrap specification, decision rules, and reporting gates. It cannot add, remove, reorder, repair, or re-run a V2 cell.

## Additive correction artifacts

Implementation must be additive. The correction layer consists only of the following artifacts:

1. this paired English/Japanese correction protocol;
2. a correction manifest that binds the protocol, the immutable V2 manifest digest, and every statically frozen correction file other than the manifest itself; the later preflight receipt is bound downstream;
3. a shared authority helper containing the exact parser and manifest/preflight validation;
4. a model-free audit that publishes the correction preflight receipt after evaluating all 10 expected paths without constructing endpoints or running bootstrap;
5. an analyzer adapter that performs the corrected admission binding, delegates all scientific calculations to the frozen base analyzer, and adds `analysis_validation_correction` provenance to the analysis receipt;
6. a bundle-builder adapter that applies the same admission correction, delegates evidence checks and publication logic to the frozen base builder, and adds `post_execution_analysis_validation_correction` provenance to the root manifest;
7. a final validator adapter that validates the immutable base provenance, active correction provenance, and delegated base-validator result; and
8. focused tests for the analyzer/audit layer and bundle layer.

No original V2 file may be edited, replaced, regenerated, or relabeled as part of this correction.

## Base and active implementation provenance

The corrected evidence chain, distributed across the analysis receipt, correction manifest/preflight, and root publication manifest, must distinguish immutable base implementations from the additive adapters actually invoked. The relevant bindings are organized as follows:

```text
analysis receipt
  analysis_implementation                 -> base analyzer {path, sha256}
  manifest_binding                        -> V2 freeze manifest {path, sha256}
  analysis_validation_correction.adapter  -> active analyzer adapter {path, sha256}
  analysis_validation_correction.manifest -> correction manifest {path, sha256}
  analysis_validation_correction.preflight-> correction preflight {path, sha256}

correction manifest / preflight
  scope.completion_parser_contract         = "rich_width80_exact_marker_plus_two_path_lines_v1"

root publication manifest
  tooling                                  -> base builder and validator
  post_execution_analysis_validation_correction.base_publication_tooling
                                           -> base builder and validator {path, sha256}
  post_execution_analysis_validation_correction.active_publication_tooling
                                           -> active builder and validator {path, sha256}
```

The adapters must never overwrite or impersonate the base implementations, or be reported as the base. The active validator must reject the bundle if any expected hash, path, parser identifier, 10/10 preflight result, correction block, or delegated base-validation result is missing or mismatched.

## Corrected-analysis procedure

1. Freeze and hash the paired protocol, shared helper/parser, audit, three adapters, and focused tests; then freeze the correction manifest that binds those files and the base V2 authority.
2. Run the correction preflight against the 10 original launcher logs and 10 already expected run paths. It must report exactly 10 accepted records and no ambiguity.
3. Run the analyzer through the active adapter. All non-presentation checks and all scientific calculations remain those of the frozen base implementation.
4. Build the public evidence bundle through the active bundle-builder adapter. It must delegate to the frozen base builder and add the correction provenance block to the root manifest.
5. Run the active validator and retain its report identifying both base and active provenance.
6. Publish the public bundle and result claims only if every base check and every correction check passes.

Any failure leaves the analysis invalid/incomplete. It must not be converted into a partial result, and no primary-status claim may be published.

## Claim boundary

This post-execution parser amendment can restore access to the already-frozen scientific analysis path; it cannot strengthen the study design. Any corrected output remains a bounded exploratory transport result on the frozen V2 target set.

In particular, this correction does not establish tokenizer independence, semantic specificity, causal control, a mechanism, behavioral transfer, cross-model generalization, or a confirmatory paper gate. The 10/10 statement applies only to execution validity. The audit documents that parser selection was not based on human-inspected result values; it does not turn the V2 target set into a new holdout.

Positive, null, mixed, and inconclusive corrected outcomes must be reported under the same frozen rules.
