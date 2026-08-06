# Milestone 2 post-hoc dependence-aware sensitivity v1

This is a **post-hoc sensitivity analysis**, not a preregistered
confirmatory analysis. It does not overwrite or reclassify the frozen v1
confirmatory statuses.

## Method

Each replicate samples eight targets with replacement inside each of the
six frozen target groups. One joint target-multiplicity vector is used for
the primary panel, null panels A/B/C, both layers, and all three fixed
direction seeds. Inside the replicate, every condition prototype is rebuilt
from the resampled targets in the other five groups. Target scores are then
recomputed, direction seeds are averaged within target, the targetwise median
of A/B/C is subtracted from the primary score, and the resulting target
effects are averaged using the replicate multiplicities.

## Results

| Layer | Point mean | Rebuilt-prototype 95% interval | Fixed-prototype 95% interval on identical draws |
|---:|---:|:---:|:---:|
| 2 | 0.18750669 | [0.10421011, 0.27132189] | [0.12548917, 0.24765946] |
| 4 | -0.08637903 | [-0.18508356, 0.00764788] | [-0.15924636, -0.01691702] |

## Limitations

- The method and all interpretation were specified after the P2 outcomes
  were available. The intervals are descriptive sensitivity intervals.
- The empirical target bank is treated as the resampling population; six
  target-group labels and fixed group sizes are conditioned on.
- Panels A/B/C and the three direction seeds are fixed, not sampled from
  broader populations. Joint resampling preserves their target alignment
  but does not quantify panel-selection or seed-selection uncertainty.
- A percentile bootstrap does not by itself justify a hypothesis-test or
  practical-equivalence decision. No p-value, Holm adjustment, or status
  is produced here.
- This analysis is pre-causal and does not establish a tokenization-free,
  semantic, mechanistic, or causal glyph effect.

The report was generated from stored fingerprints; no model forward pass
and no C1 holdout access occurred.
