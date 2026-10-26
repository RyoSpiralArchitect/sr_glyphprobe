# Portable CPU preflight for the shared-prefix diagnostic

[日本語](CONTEXTUAL_EMOJI_PREFIX_PREFLIGHT_ADDENDUM_V0.ja.md) · [Original protocol](CONTEXTUAL_EMOJI_PREFIX_CONSISTENCY_V0.md)

2026-10-07 (JST). This addendum changes a CPU reference representation before any model forward. It leaves the eight selected inputs, seven-call schedule, 56-attempt limit, BF16 runtime, resource limits, and zero-tolerance model comparisons unchanged.

## Initial refusal

Commit `d725960` prepared specification SHA-256 `28c164b6e9cc0dfc1dae11b2c11ff84118f6d7f289c2122999d1cae9ac0253d7`. Its Furnace invocation stopped during whole-report CPU recomputation, before creating the run directory, importing the model runtime, allocating model memory, or attempting a forward. This is a zero-forward preflight refusal, not a failed model observation.

The Linux recomputation differed from the saved Mac analysis at seven `coefficient_change_rows/*/mean_squared_cell_shift` fields: row indices 10, 32, 45, 75, 84, 85, and 94. Each difference was one binary64 ULP. The native expression was an average of four squared differences computed with `** 2`. Every other report field agreed, including the candidate-prefix inventory and all H values. The exact low-level cause was not isolated.

## Explicit new reference

Schema version 2 uses a separate `measurement_portable_replay.json`. It reconstructs the same auxiliary field in all 144 coefficient-change rows as `math.fsum(d * d for d in four_differences) / 4`. It retains the full analysis, the parent hashes, the replay-source hash, and the exact parent-to-reference changed values. The parent analysis and analyzer remain unchanged.

The revised check requires:

- Pinned parent analysis, analyzer, raw records, and acquisition sources.
- Native parent differences confined to the declared auxiliary field; differences elsewhere are refused.
- Exact equality of the complete deterministic replay from raw records and the deterministic replay of the pinned parent.
- Exact equality of the full replay artifact and its pinned reference. No numerical tolerance is introduced.
- The same selected inputs and exact original model-score/runtime comparisons as before.

This is a versioned arithmetic-definition change for a CPU bookkeeping quantity, not evidence that the old model scores are repaired. Native host differences are retained in the run's provenance. The new specification lives under `validation/contextual_emoji_prefix_consistency_v0/portable_preflight/`; the initial specification remains at its original path and is reproducible with its original commit.

No model outcomes were available when making this change. A second preflight invocation after this repair does not increase the 56 model-attempt budget. A later model-gate failure will remain a failure; no precision sweep or full-grid rerun is authorized by this addendum.
