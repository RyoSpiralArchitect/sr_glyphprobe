# E1 token-isomorphic emoji-family exploratory report

This report publishes the complete prespecified five-family lattice. All estimates are descriptive and use only positive-strength RMS emoji fingerprints from the fixed MLX FP32 cell.

The strongest permitted interpretation is exploratory matched-slot fingerprint recurrence under a fixed middle-token family substitution in one pinned GPT-2 MLX FP32 intervention cell. Family identity remains perfectly confounded with the family-middle token.

## Fixed analysis

- Families: sky, food, animals, transport, social
- Layers: 2 (primary exploratory), 4 (prespecified secondary negative comparator)
- Direction seeds nested within target: 101, 211, 307
- Targets: 24, four in each of six fixed groups
- Bootstrap: 20,000 joint group-stratified target resamples, seed 20260808; all LOTO prototypes rebuilt inside every replicate
- Interval notation below: observed target mean [2.5th, 97.5th bootstrap percentiles]

## Layer 2: primary exploratory

### Complete M matrix

Rows are source-family fingerprints; columns are prototype families. Diagonal cells are within-family M and off-diagonal cells are ordered cross-family matched-slot transfer M.

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.476026 [0.362522, 0.580340] | 0.484915 [0.358770, 0.593179] | 0.450468 [0.342285, 0.565842] | 0.484103 [0.343088, 0.577355] | 0.458144 [0.345743, 0.573996] |
| food | 0.468883 [0.354435, 0.582531] | 0.482684 [0.346910, 0.604612] | 0.441429 [0.326873, 0.568829] | 0.470659 [0.326841, 0.569480] | 0.448881 [0.332661, 0.575109] |
| animals | 0.430329 [0.326861, 0.541072] | 0.443816 [0.320610, 0.558829] | 0.426832 [0.313707, 0.548953] | 0.434263 [0.303237, 0.532146] | 0.422365 [0.318075, 0.544005] |
| transport | 0.431020 [0.317956, 0.540486] | 0.434920 [0.308955, 0.545458] | 0.395455 [0.294270, 0.516777] | 0.478736 [0.318884, 0.588609] | 0.405605 [0.297981, 0.525625] |
| social | 0.442553 [0.332601, 0.556103] | 0.453080 [0.327460, 0.569421] | 0.431997 [0.322690, 0.549774] | 0.452717 [0.311569, 0.553373] | 0.435189 [0.326431, 0.555524] |

### Family specificity R

For each target, R is its within-family M minus the median of its four off-diagonal prototype-family M values.

| family | target mean R [95% bootstrap interval] | target median (secondary) |
|---|---:|---:|
| sky | 0.008588 [-0.014893, 0.038753] | 0.014093 |
| food | 0.023749 [-0.014597, 0.052447] | 0.022765 |
| animals | -0.011182 [-0.042184, 0.052737] | 0.012075 |
| transport | 0.064934 [-0.017747, 0.086572] | 0.099840 |
| social | -0.012326 [-0.032422, 0.028139] | -0.005395 |

Equal-family global R: **0.014753 [0.002875, 0.027439]**.

## Layer 4: prespecified secondary negative comparator

### Complete M matrix

Rows are source-family fingerprints; columns are prototype families. Diagonal cells are within-family M and off-diagonal cells are ordered cross-family matched-slot transfer M.

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.659063 [0.530977, 0.736122] | 0.640399 [0.509917, 0.733700] | 0.642212 [0.531427, 0.725629] | 0.637573 [0.506335, 0.728334] | 0.613301 [0.480492, 0.716054] |
| food | 0.659563 [0.524487, 0.745117] | 0.669187 [0.517761, 0.772593] | 0.650004 [0.527903, 0.747417] | 0.669574 [0.515635, 0.767665] | 0.635669 [0.490181, 0.747573] |
| animals | 0.646314 [0.516031, 0.727783] | 0.632649 [0.493341, 0.734658] | 0.633404 [0.517598, 0.724452] | 0.633389 [0.488670, 0.733309] | 0.606434 [0.470726, 0.715402] |
| transport | 0.655011 [0.532231, 0.737172] | 0.668793 [0.523922, 0.769278] | 0.648537 [0.531385, 0.745023] | 0.681909 [0.527975, 0.781473] | 0.634021 [0.497968, 0.743577] |
| social | 0.631855 [0.508810, 0.711762] | 0.629910 [0.496527, 0.727785] | 0.619736 [0.509664, 0.708470] | 0.629083 [0.492834, 0.722616] | 0.602564 [0.473922, 0.706733] |

### Family specificity R

For each target, R is its within-family M minus the median of its four off-diagonal prototype-family M values.

| family | target mean R [95% bootstrap interval] | target median (secondary) |
|---|---:|---:|
| sky | 0.029825 [-0.018879, 0.047807] | 0.058611 |
| food | 0.023159 [-0.007451, 0.043930] | 0.038054 |
| animals | 0.009492 [-0.017226, 0.039138] | 0.022713 |
| transport | 0.034787 [-0.017567, 0.059454] | 0.054501 |
| social | -0.022823 [-0.043273, 0.003103] | -0.031843 |

Equal-family global R: **0.014888 [0.003408, 0.019684]**.

## Descriptive controls and integrity

Every family-by-layer-by-direction-seed random-control separation and emoji advantage-over-random value is retained in `family_cell_summary.jsonl`. No label permutations were run, and this analyzer computes no p-values. The random controls are descriptive screens, not E1 endpoint observations.

| family | intervention rows | emoji rows used | random rows | zero-hook rows | max zero activation RMS | max zero logit RMS |
|---|---:|---:|---:|---:|---:|---:|
| sky | 1776 | 1440 | 288 | 48 | 0.0000000000 | 0.0000000000 |
| food | 1776 | 1440 | 288 | 48 | 0.0000000000 | 0.0000000000 |
| animals | 1776 | 1440 | 288 | 48 | 0.0000000000 | 0.0000000000 |
| transport | 1776 | 1440 | 288 | 48 | 0.0000000000 | 0.0000000000 |
| social | 1776 | 1440 | 288 | 48 | 0.0000000000 | 0.0000000000 |

## Claim boundary

This exploration does not establish semantic categories, a tokenizer-independent glyph property, causal localization, cross-model generality, backend replication, or behavioral meaning. It produces no significance, equivalence, multiplicity, selection, confirmation, robustness, or paper-gate decision.
