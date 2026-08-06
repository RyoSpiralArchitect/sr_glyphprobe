# E1 token-isomorphic emoji-family exploratory results

[日本語](EMOJI_FAMILY_EXPLORATORY_RESULTS.ja.md) · [Frozen protocol](EMOJI_FAMILY_EXPLORATORY_PROTOCOL.md) · [Research roadmap](ROADMAP.md) · [Public evidence](../artifacts/emoji_family_exploratory_v1/analysis/report.md)

## Status and scope

E1 is complete as a bounded descriptive exploration. Commit
`0cd4e11610e42253ead9ce9aff9f0b02474a0558` froze the protocol, panels,
configs, tokenizer preflight, endpoints, and analyzer before the five MLX runs.
The experiment asks whether matched-slot output-fingerprint separation recurs
across five emoji blocks when the pinned GPT-2 token sequence changes only at
the family-middle token.

This is not a Milestone 2 confirmation or a C1 causal experiment. It uses the
24 previously explored prestage targets. P2 and C1 were not opened, read,
tokenized, scored, sampled, or sent to a model for E1.

Bundle-level publication validation: **passed**. The independent validator
verified all 82 public payload members and five role bindings, found no hash
mismatch or local absolute path, and validated the manifest declaration that
P2 and C1 stayed outside the fixed E1 input surface. This declaration does not
independently prove process history. The root manifest is the 83rd public file.

## Result at a glance

| Quantity | Layer 2, primary exploratory | Layer 4, prespecified negative comparator |
|---|---:|---:|
| Equal-family global specificity, \(R_{\mathrm{global}}\) | 0.014752595564 [0.002875238085, 0.027439243404] | 0.014887989201 [0.003407563347, 0.019684351979] |
| Family-specific \(R_f\) intervals containing zero | 5 / 5 | 5 / 5 |
| Range of the 25 mean \(M_{f\leftarrow g}\) cells | 0.395455–0.484915 | 0.602564–0.681909 |

Brackets are 95% descriptive bootstrap percentile intervals. They are not
p-value-based confidence decisions. E1 computes no p-values, multiplicity
decisions, equivalence decisions, selection rule, or confirmatory status.

The full \(M\) matrices were broadly positive, including their off-diagonal
transfer cells. The family-specific excess \(R\) was much smaller. This pattern
suggests that recurrence tied to the deliberately shared first and third GPT-2
tokens dominates the small residual within-family excess. It does not identify
a semantic family representation.

Layer 4 did not behave as the intended negative comparator: its global \(R\)
was positive and nearly the same size as layer 2. E1 therefore supplies no
layer-specific claim.

## Fixed design

The five reporting IDs are `sky`, `food`, `animals`, `transport`, and `social`.
Each contains ten consecutive Unicode scalars. At matched slot \(j\), every raw
glyph tokenization has the form

```text
[8582, family_middle_token, shared_slot_suffix_token]
```

Only the middle token differs by family. Family identity is therefore perfectly
confounded with that token. The first and third token IDs are deliberately
shared across families, so off-diagonal transfer can arise from shared token
structure alone.

The fixed execution cell used:

- `openai-community/gpt2` revision
  `607a30d783dfa663caf39e06633721c8d4cfcd7e`;
- MLX FP32, `resid_post`, layers 2 and 4, strength 0.05;
- direction seeds 101, 211, and 307, nested within each target;
- all 16 source wrappers and the first 24 prestage targets, four in each of six
  fixed groups;
- two random directions per layer and an exact zero-hook control;
- no neutral-direction arm, sign flip, label permutation, SAE, or iso-KL arm.

For each source family \(f\), prototype family \(g\), and target \(t\),
\(M_{f\leftarrow g,t}\) is the seed-averaged matched-slot cosine minus the mean
cosine to the nine mismatched slots. The family-specific excess is

\[
R_{f,t}=M_{f\leftarrow f,t}-\operatorname{median}_{g\ne f}M_{f\leftarrow g,t}.
\]

The primary descriptive aggregate is the arithmetic mean over the 24 targets.
The global value gives each family equal weight. All intervals use 20,000 joint,
group-stratified target-bootstrap replicates. Every replicate rebuilds all
data-dependent leave-one-target-group-out prototypes; the same resample is used
across families, layers, endpoints, and ordered family pairs.

## Complete family-specific results

Every family-level interval includes zero at both layers.

### Layer 2

| Family | Mean \(R_f\) | 95% descriptive interval | Target median, secondary |
|---|---:|---:|---:|
| sky | 0.008588 | [-0.014893, 0.038753] | 0.014093 |
| food | 0.023749 | [-0.014597, 0.052447] | 0.022765 |
| animals | -0.011182 | [-0.042184, 0.052737] | 0.012075 |
| transport | 0.064934 | [-0.017747, 0.086572] | 0.099840 |
| social | -0.012326 | [-0.032422, 0.028139] | -0.005395 |

### Layer 4

| Family | Mean \(R_f\) | 95% descriptive interval | Target median, secondary |
|---|---:|---:|---:|
| sky | 0.029825 | [-0.018879, 0.047807] | 0.058611 |
| food | 0.023159 | [-0.007451, 0.043930] | 0.038054 |
| animals | 0.009492 | [-0.017226, 0.039138] | 0.022713 |
| transport | 0.034787 | [-0.017567, 0.059454] | 0.054501 |
| social | -0.022823 | [-0.043273, 0.003103] | -0.031843 |

## Complete mean transfer matrices

Rows are source-family fingerprints; columns are prototype families. Diagonal
cells are within-family \(M\), while off-diagonal cells measure ordered
matched-slot transfer. Full cell intervals and target-level rows remain in the
[analysis report](../artifacts/emoji_family_exploratory_v1/analysis/report.md)
and JSONL files.

### Layer 2

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.476026 | 0.484915 | 0.450468 | 0.484103 | 0.458144 |
| food | 0.468883 | 0.482684 | 0.441429 | 0.470659 | 0.448881 |
| animals | 0.430329 | 0.443816 | 0.426832 | 0.434263 | 0.422365 |
| transport | 0.431020 | 0.434920 | 0.395455 | 0.478736 | 0.405605 |
| social | 0.442553 | 0.453080 | 0.431997 | 0.452717 | 0.435189 |

### Layer 4

| source \ prototype | sky | food | animals | transport | social |
|---|---:|---:|---:|---:|---:|
| sky | 0.659063 | 0.640399 | 0.642212 | 0.637573 | 0.613301 |
| food | 0.659563 | 0.669187 | 0.650004 | 0.669574 | 0.635669 |
| animals | 0.646314 | 0.632649 | 0.633404 | 0.633389 | 0.606434 |
| transport | 0.655011 | 0.668793 | 0.648537 | 0.681909 | 0.634021 |
| social | 0.631855 | 0.629910 | 0.619736 | 0.629083 | 0.602564 |

The diagonal is not uniformly the largest entry in its row. This is why the
broadly positive \(M\) lattice is evidence of recurrence and transfer, not of
family-specific separation.

## Random controls and heterogeneity

Ten of the 30 family × layer × direction-seed cells had
`emoji_advantage_over_random <= 0`:

- layer 2, seed 307: all five families;
- layer 4, seed 101: all five families.

The remaining 20 cells do not authorize a robust-superiority claim. The exact
cross-family seed pattern shows that the random-control comparison is
heterogeneous at the prespecified cell level; seeds remain repeated direction
estimates, not independent observations.

## Completeness and provenance

- Five run receipts report `complete`, with 1,776 intervention rows per family.
- All 8,880 intervention rows are present: 7,200 emoji, 1,440 random-control,
  and 240 zero-hook rows.
- Error count is zero in every run. Maximum zero-hook activation and logit RMS
  are both exactly 0.
- The five receipt durations sum to 321.236315 seconds. This is machine-specific
  runtime provenance, not a general MLX speed result.
- Published analysis grids contain 240 family-target rows, 960 ordered-transfer
  target rows, 10 family summaries, and 40 off-diagonal transfer summaries.

The compact evidence is organized under:

- [root E1 manifest](../artifacts/EMOJI_FAMILY_EXPLORATORY_V1_MANIFEST.json);
- [tokenizer-only preflight](../artifacts/emoji_family_exploratory_v1/preflight/tokenization_audit_v1.json);
- [analysis outputs](../artifacts/emoji_family_exploratory_v1/analysis/);
- [five compact run directories](../artifacts/emoji_family_exploratory_v1/runs/).

## Claim boundary

The strongest permitted positive description is **exploratory matched-slot
fingerprint recurrence under a fixed middle-token family substitution in one
pinned GPT-2 MLX FP32 intervention cell**.

E1 does not establish:

- semantic emoji families or human-readable meaning;
- a tokenizer-independent glyph property;
- a layer-specific effect;
- random-control superiority that is robust across the fixed seeds;
- causal localization, a component, or a path;
- cross-model or independent-backend replication;
- behavioral or generation effects; or
- significance, equivalence, confirmation, robustness, or a Phase I paper gate.

E1 does not update the Milestone 2 classification, select a C1 intervention, or
unseal C1. A focused hypothesis derived from E1 would require a new public
protocol and a new untouched target bank that is neither P2 nor C1.
