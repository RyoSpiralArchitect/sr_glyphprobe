# T10 cross-model diagnostic analysis v1

Status: **retrospective descriptive analysis; T10 primary unchanged**.

The registered outcome remains `cross_model_replication_not_established_under_frozen_rule`. The statistical partial-conjunction p-value was `0.0001`, while only `2/4` core cells met the frozen practical rule. At 292 items, the `0.02` floor is a six-net-item boundary.

## What the finer analysis changes

Carrier-distance profiles are not shared across models: pairwise profile Spearman correlations have median `-0.162` and range `-0.755` to `0.610`. Median variance shares are `0.198` carrier, `0.266` distance, and `0.299` interaction.

Name retrieval is also concentrated in different items. At least one model retrieves `233/292` items in one or more contexts, only `14` are hit by six or more models, and none are hit by all nine.

All 72 final-endpoint cells have positive top-1, MRR, and paired-margin name-versus-codepoint contrasts, but CKA does not share that universal direction. Codepoint top-1 is zero in `13/72` cells, so codepoint text is retained as a weak comparator rather than T11's sole negative control.

## Consequence for T11

T11 should use continuous item-level matched-label margins, breadth, context stability, raw/final-norm change, and cross-model geometry. Minimum top-1 remains secondary. T11 is a new exploratory lane and cannot lower T10's floor, replace its core roster, or retroactively rescue its primary.

## Raw reconstruction

The raw archive reconstructed `36` prediction arrays with `0` mismatches. The maximum absolute top-1 contrast error was `1.505e-08`.

Across model-pair medians over the eight contexts, median item-geometry CKA is `0.132` for final glyph states, `0.362` for names, and `0.423` for codepoint text. The largest cross-model divergence is therefore on the glyph side, descriptively.
