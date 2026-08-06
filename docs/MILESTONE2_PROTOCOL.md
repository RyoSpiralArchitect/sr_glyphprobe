# Milestone 2 confirmatory protocol

[Japanese / 日本語](MILESTONE2_PROTOCOL.ja.md) · [Roadmap](ROADMAP.md) · [Scientific contract](SCIENTIFIC_CONTRACT.md)

Protocol ID: `glyphprobe-m2-tokenization-controls-v1`

Freeze state: prepared before any Milestone 2 model forward or outcome inspection. The first public Git commit containing this file, the frozen-bank manifest, the control manifest, the exact configs, and the analysis code is the protocol freeze event. Frozen v1 files are never overwritten; a revision requires a new protocol ID and versioned filenames.

## Confirmatory question

Does the colored-shape panel retain greater cross-target output-fingerprint identifiability than fixed control panels matched on the prespecified GPT-2 token-count and token-prefix features?

This experiment does not attempt to create a different glyph with an identical GPT-2 token sequence. GPT-2 token IDs decode to a fixed byte string, so exact token-identity matching would reproduce the same input. The authorized conclusion is therefore robustness, or lack of robustness, to the prespecified token-count and prefix controls. It is not a tokenization-free glyph effect.

## Frozen data roles

| Bank | Role | Authorized use |
|---|---|---|
| Existing first 24 `prestage_targets` | Exploratory | control implementation, diagnostics, CountSketch sensitivity, and later intervention-site exploration |
| `p2_confirmatory_targets_v1` | One-shot P2 confirmation | the primary endpoint defined below; never adapter debugging, threshold tuning, or site selection |
| `c1_causal_holdout_targets_v1` | Future C1 confirmation | only the final causal test after the intervention and decision rule are frozen |
| Existing `source_wrappers` | Primary P2 source procedure | target-generalization confirmation conditional on the published source procedure |
| `milestone2_independent_source_wrappers_v1` | Source robustness | a separately reported robustness arm; never pooled with target clusters as extra observations |

The two holdout banks contain 48 targets each: eight targets in each of six groups (`continuation`, `factual`, `reasoning`, `procedural`, `classification`, and `planning`). Their exact hashes and prohibited uses are recorded in `data/manifests/milestone2_frozen_banks_v1.json`.

## Fixed panels and diagnostics

The primary colored-shape panel has ten conditions. Nine raw token sequences begin with `[8582, 253]`; `blue_circle` begins with `[8582, 242]`. Every primary glyph has three raw GPT-2 tokens.

The primary matched-control family consists of three disjoint ten-symbol panels:

- `m2_null_prefix_9x253_1x242_a`;
- `m2_null_prefix_9x253_1x242_b`;
- `m2_null_prefix_9x253_1x242_c`.

Each panel has the same 9:1 prefix-stratum count as the colored panel, the same number of conditions, three raw tokens per symbol, and sealed wrapper-tokenization checks. The eligible dominant-prefix universe contains only 26 non-colored symbols after the reference glyphs and neutral control are excluded, but three disjoint panels require 27 slots. Panel C therefore includes one prespecified semantic-near control, the nonreference red square `🟥`; the other 29 panel entries are non-colored symbols. This conservative exception is recorded before outcomes rather than hidden or replaced after inspection.

Candidate generation, filtering, and assignment use tokenizer output, Unicode metadata, and wrapper structure only. Activations, logits, generations, and prior cell magnitudes are prohibited selection inputs.

Two diagnostic panels are secondary:

- `m2_suffix_matched_middle_236` preserves each primary condition's first and last token IDs while replacing the middle token;
- `m2_colored_shapes_prefix_10x253` replaces the blue pair with the yellow pair so all ten colored-shape conditions share `[8582, 253]`.

These diagnostics cannot replace the three-panel matched-null family in the primary endpoint.

## Fixed model cell

- model: `openai-community/gpt2`;
- revision: `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
- backend: qualified MLX/MLX-LM path;
- dtype: FP32;
- intervention site: full-sequence `resid_post`;
- primary layers: 2 and 4;
- primary strength: 0.05 target-activation RMS;
- direction seeds: 101, 211, and 307, treated as repeated estimates inside each target;
- fingerprint: sealed 96-dimensional CountSketch with seed 8675309.

The one-shot primary runs are fixed by `configs/m2_p2_primary_mlx.yaml` and the three `configs/m2_p2_matched_null_{a,b,c}_mlx.yaml` files. They execute only layers 2 and 4 at strength 0.05, plus the zero-hook check. The separately reported source-robustness arm is fixed by the four corresponding `*_independent_source_mlx.yaml` files. These reduced matrices prevent secondary cells from becoming an implicit rescue search on the P2 bank.

Layers 7 and 9, strengths 0.025 and 0.10, individual glyphs, the two diagnostic panels, random controls, and generic-glyph directions remain exploratory or secondary. They are not executed by the one-shot P2 configs and cannot rescue a failed primary family.

The two primary layers were chosen from the published exploratory map. This is permitted because the P2 bank was not used for that choice. Layer heterogeneity is a warning, not supporting evidence: layer 2 seed 307 and layer 4 seed 101 were negative at every exploratory strength.

## Primary target-level endpoint

Let `f[p,c,t,s]` be the unit-normalized 96-dimensional fingerprint for panel `p`, condition `c`, target `t`, and direction seed `s` at a fixed layer and strength.

For each target group `g`, construct a condition prototype using only targets outside that group:

```text
q[p,c,-g,s] = unit_mean({f[p,c,u,s] : group(u) != g})
```

The leave-one-group-out identification score for target `t` is:

```text
S[p,t,s] = mean_c cosine(f[p,c,t,s], q[p,c,-group(t),s])
           - mean_{c != d} cosine(f[p,c,t,s], q[p,d,-group(t),s])
```

Direction seeds are averaged within a target; they do not increase sample size:

```text
S[p,t] = mean_s S[p,t,s]
```

The primary adjusted target effect is:

```text
D[t] = S[colored_shapes,t]
       - median_b S[matched_null_b,t],  b in {a,b,c}
```

There are 48 target-cluster observations per primary layer. Glyphs, direction seeds, split repetitions, null panels, and CountSketch dimensions are not independent observations.

## Confirmatory inference

- estimand: the mean of `D[t]` across the 48 P2 targets;
- uncertainty: percentile cluster bootstrap with 20,000 replicates, resampling eight targets with replacement inside each of the six fixed groups;
- bootstrap seed: 20260806;
- minimally meaningful excess (`delta`): 0.06 fingerprint-separation units, chosen before matched-control outcomes as approximately 10% of the published exploratory median advantage;
- primary family: layer 2 at strength 0.05 and layer 4 at strength 0.05;
- multiplicity: Holm family-wise correction at alpha 0.05 across those two hypotheses;
- permutation screen: 100,000 paired sign-flip draws of `D[t] - delta`, seed 20260807; this is secondary to the interval estimate.

A primary layer is **robust to the prespecified matched controls** only if its 95% bootstrap lower bound exceeds `delta` and its one-sided Holm-adjusted permutation p-value is below 0.05.

A layer is **practically equivalent to the matched-null ensemble** only if its full 95% interval lies inside `[-delta, delta]`. Every other outcome is **unresolved**. Failure to reject is never relabeled as proof that tokenization caused the exploratory result.

The descriptive 36-cell table reports the primary value, matched-null median, additive difference, null-panel percentile, sign change, and lower-dimensional CountSketch sensitivity. The 36 cells are correlated and receive no pooled p-value or independent-sample interpretation.

## Candidate and holdout gates

Only a primary layer that passes the P2 rule may enter targeted causal localization. Source robustness must be reported separately using the frozen independent wrapper bank. A source-robust result preserves the adjusted-effect sign and does not cross the practical-equivalence region under the same fixed analysis; source wrapper replicates remain nested measurements.

`resid_pre`, `attn_out`, and `mlp_out` may be explored on the existing 24 targets after model-family parity is qualified. That exploration must not inspect C1 outcomes. Before opening the C1 bank, the intervention site, candidate layer, strength, patch/ablation operation, negative controls, endpoint, and multiplicity family must be frozen in a new C1 protocol.

## CountSketch and backend sensitivity

The 96-dimensional fingerprint is primary. With the same hash seed, dimensions 48, 32, and 24 can be reconstructed exactly by folding the stored 96 buckets and renormalizing. They are secondary sensitivity analyses and do not add observations. A different CountSketch seed or a dimension that does not divide 96 requires new full-vocabulary logit deltas or new forward passes.

TransformerLens reproduction is an independent backend implementation check, not an independent model-family replication. It must first pass exact token-ID, BOS policy, baseline-logit, activation, zero-hook, and non-zero intervention parity for the fixed cell. Confirmatory targets are prohibited for adapter debugging.

## Stopping and reporting

The P2 bank is opened once after the protocol, manifests, configs, and analysis implementation pass tests. All primary, negative, heterogeneous, equivalent, and unresolved results are published together. No symbol, target, source wrapper, layer, strength, CountSketch setting, or endpoint is replaced after outcome inspection within protocol v1.

A clean negative or mixed result completes this Milestone 2 question if the frozen experiment and evidence archive remain identifiable and reproducible.
