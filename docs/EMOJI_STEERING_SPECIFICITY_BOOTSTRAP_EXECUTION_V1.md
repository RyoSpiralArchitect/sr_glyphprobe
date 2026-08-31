# T13-EA Bootstrap Execution v1

[日本語](EMOJI_STEERING_SPECIFICITY_BOOTSTRAP_EXECUTION_V1.ja.md) · [Point results](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0_RESULTS.md) · [Original analysis contract](EMOJI_STEERING_SPECIFICITY_ANALYSIS_V0.md)

Status: **post-outcome computational amendment frozen; production bootstrap not yet executed**.

This contract makes the registered 20,000-replicate T13-EA bootstrap
executable in deterministic chunks. It freezes the exact high-level estimand
roster, replicate-to-draw mapping, chunk boundaries, merge order, integrity
receipts, and failure gates. At freeze time, the production bundle does not
exist, no production chunk has run, and the count remains **0 / 20,000**.

## Why this is a separate amendment

The prospective T13-EA contract fixed the family-level resampling units,
20,000 replicates, seed `2026082913`, pointwise 95% percentile intervals, and a
complete hash-merge gate. It did not enumerate the exact marginalization rows
or define a chunk-order-independent random schedule. The earlier one-shot
analyzer also bootstraps many fine surface summaries while leaving the public
high-level macro rows without aligned replicate intervals.

Point outcomes were already visible when this implementation gap was closed.
The amendment is therefore explicitly post-outcome. It does not claim that the
exact 600-row roster was prospectively registered. Instead, it applies one
mechanical rule: copy every model and endpoint row from the fixed public
high-level reporting synthesis, without filtering by sign, depth, effect size,
direction, or apparent interest.

Completed intervals will remain descriptive and exploratory. They cannot
create a primary hypothesis, significance decision, confirmation, emoji-
specific mechanism, semantic interpretation, tokenizer independence, scale
law, or model-population generality.

## Frozen estimand roster

The machine-readable roster is
[`configs/emoji_steering_specificity_bootstrap_estimands_v1.json`](../configs/emoji_steering_specificity_bootstrap_estimands_v1.json).
It contains exactly 600 unique, indexed estimands.

| Family | Rows | Included high-level estimands |
|---|---:|---|
| F1 item source form | 108 | Every model × contrast × sign × endpoint paired-difference mean |
| F2 prototype depth/dose | 168 | Every model × endpoint × depth raw macro mean; every model × endpoint dose-ordering mean; both model-level entropy antisymmetry diagnostics |
| F3 random calibration | 324 | Both random-relative metrics for every model × endpoint × depth and every model × endpoint depth-average |
| **Total** | **600** | No outcome-selected subset |

The complete fine-grained F1–F3 point tables remain part of the released point
analysis. They are not deleted or hidden. They simply do not receive
retroactively selected intervals under this high-level bootstrap roster.

## Resampling schedule

Replicate IDs are the integers `0` through `19999`. The run contains 100 fixed
chunks of 200 contiguous replicates:

- `chunk-0000`: `[0, 200)`
- `chunk-0001`: `[200, 400)`
- …
- `chunk-0099`: `[19800, 20000)`

Every draw is produced by an explicit counter-based SHA-256 sampler with
unbiased rejection. A draw depends on the frozen seed, namespace, replicate
ID, draw index, and rejection-attempt index. It does not depend on which chunk
runs first, which process runs it, or how many chunks run in parallel.

One 32-target schedule is shared across F1, F2, F3, all endpoints, and all
three models. F1 has two item schedules: one over all 192 items for
glyph-minus-name, and one over the 168 decomposition-eligible items shared by
the two decomposition contrasts. F3 resamples 64 random seed indices within
each model and normalized depth; that draw is shared across targets,
magnitudes, endpoints, systems, and source forms.

## Frozen point functions

### F1

Within each model, contrast, sign, and endpoint, the statistic is the paired
eligible-item × target micro mean. Independent item and target multiplicities
form the two-way pigeonhole weight. Source forms stay paired.

### F2

The raw depth statistic gives each source form equal weight, then gives each
eligible system within that form equal weight. Magnitudes and signs are also
equally weighted. The dose statistic first computes the target-level
ordered-nondecreasing indicator, then averages every registered system-form-
depth-sign cell. Entropy antisymmetry averages the signed sum and normalized
residual over every registered system-form-depth-magnitude cell.

### F3

Each replicate computes the exact median of the resampled 64-seed multiset and
the midrank against that same multiset. Source forms receive equal weight;
eligible systems are equal within source form; magnitudes are equal; and the
model-overall rows give the eight depths equal weight. Negative prototype arms
still have no sign-matched random null and are not inserted into F3.

## Bundle boundary

The one-time `prepare` stage re-runs the existing scientific-open closeout,
preflight bindings, and amended zero gate before reading response ledgers. It
then writes only the scalar item/target populations needed by the 600
estimands. The bundle must replay all 600 public point values within an
absolute tolerance of `1e-12`; otherwise it fails before any bootstrap chunk
runs.

The bundle contains no activation arrays, raw logits, model weights, cache,
prompt text, target text, or protected target bank. It must stay outside the
Git worktree. Any transfer of the derived bundle or chunks requires complete
file hashes after scientific open. Raw activation/logit arrays remain
forbidden on Git and SpiralShare.

## Cross-runtime sentinel

Each chunk also recomputes replicate IDs `0`, `9999`, and `19999`. Their full
600-value vectors are hashed together. The merge accepts chunks from different
runtime fingerprints only when every sentinel hash is bit-identical. Thus a
Mac and furnace may share chunk work only after their actual numerical path
agrees; configuration similarity alone is not enough.

## Merge and failure gates

The merge accepts exactly `chunk-0000` through `chunk-0099`, with no missing,
extra, duplicate, or overlapping replicate. It verifies the freeze, execution
config, estimand roster, bundle manifest, each file hash, each semantic payload
hash, exact replicate ranges, finite values, and one common sentinel hash.

Intervals use the frozen linear percentile rule
`h = (n - 1) q` at `q = 0.025` and `0.975`. A partial merge never emits an
interval receipt. Existing output paths are never overwritten.

The successful merge receipt may set the computational paper-interval gate to
true. It must simultaneously record that the exact roster was frozen after
point outcomes and that the confirmatory gate remains false.

## Frozen commands

Audit the repository freeze:

```bash
python3 scripts/audit_emoji_steering_specificity_bootstrap_execution_v1.py audit-freeze
```

Prepare the compact production bundle after resolving the live furnace paths:

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py prepare \
  --run-root /absolute/path/to/sealed-t13eh \
  --scientific-open-receipt /absolute/path/to/scientific-open-closeout.json \
  --preflight-directory validation/emoji_steering_specificity_harvest_v0 \
  --output /absolute/path/to/t13ea-bootstrap-v1-bundle
```

Run one assigned chunk; a scheduler may assign every integer from 0 through
99 in any order:

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py run-chunk \
  --bundle /absolute/path/to/t13ea-bootstrap-v1-bundle \
  --output-root /absolute/path/to/t13ea-bootstrap-v1-chunks \
  --chunk-id 0
```

Merge only after all 100 chunk receipts exist:

```bash
python3 scripts/run_emoji_steering_specificity_bootstrap_v1.py merge \
  --bundle /absolute/path/to/t13ea-bootstrap-v1-bundle \
  --chunks-root /absolute/path/to/t13ea-bootstrap-v1-chunks \
  --output /absolute/path/to/t13ea-bootstrap-v1-merge
```

These commands are frozen execution instructions, not evidence that the
production run has occurred.
