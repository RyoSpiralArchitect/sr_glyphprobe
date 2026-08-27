# Multifamily colored-shape geometry v0

[日本語](MULTIFAMILY_COLORED_SHAPE_GEOMETRY_V0.ja.md) · [Tokenizer census results](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [Research roadmap](ROADMAP.md)

Protocol ID: `glyphprobe-multifamily-colored-shape-geometry-v0`

## Status

This is a prospective, frozen exploratory activation protocol. Its executable
freeze begins with the first public commit containing this English/Japanese
pair, the configuration, runner/analyzer, tests, and checksum manifest. Model
forwards performed before that commit are engineering capability probes only
and are not observations in this experiment.

The experiment asks a narrow question: does a common circle-minus-square
direction recur across five colors in two predeclared, non-Llama model cells?
It does not test emoji meaning, behavior, causality, a circuit, backend parity,
node performance, quantization equivalence, or a confirmatory paper claim.

## Why this cell comes next

The completed tokenizer census showed that one universal prefix-matched control
cannot be carried unchanged across tokenizer families. It also identified two
useful but different fixed control regimes:

- Gemma 2 encodes all ten colored shapes as distinct atomic tokens. Its panel
  is matched on one-token length and single-code-point Unicode construction,
  but a different glyph cannot share the atomic token prefix.
- OLMo 3 encodes the ten items with equal three-token spans and at least one
  shared leading token within its vocabulary.

The regimes are reported separately. A cross-model recurrence is based only on
the sign and exact-test decision recurring independently; raw effect magnitudes
are not compared across widths, precisions, tokenizers, or nodes.

## Frozen cells

| Role | Model artifact | Runtime | Structural control |
|---|---|---|---|
| `gemma2_2b_4bit` | `mlx-community/gemma-2-2b-4bit` | mac2, MLX, 4-bit | atomic, one token, same Unicode construction |
| `olmo3_7b_bf16` | sealed local OLMo 3 7B artifact | mac1, MLX, BF16 | three tokens, shared prefix, same Unicode construction |

Both model artifacts are pinned by path-independent full-file manifest hashes.
The manifest also binds the exact GlyphProbe source-tree hash and all frozen
protocol assets. Local filesystem paths are runtime inputs and must not appear
in published receipts.

The clean runtime is fixed to MLX 0.31.1, MLX-LM 0.31.2, and Transformers
4.57.6. MLX-LM 0.31.2 declares Transformers 5 or newer even though this
preflight-qualified combination imports and completed one finite engineering
capture on each model. The mismatch is retained in every receipt and prevents
calling this a qualified backend comparison.

## Frozen panel and capture

The existing ordered ten-item colored-shape panel is used unchanged: five
colors (`brown`, `orange`, `green`, `blue`, `purple`) crossed with two shapes
(`circle`, `square`). Each raw glyph is forwarded with no special tokens.
`resid_post` is captured at the final item token.

Five layers are resolved without looking at activations:

```text
min(num_layers - 1, floor(fraction * num_layers))
fractions = [0, 0.25, 0.5, 0.75, 1]
```

This yields `[0, 6, 13, 19, 25]` for Gemma 2 and
`[0, 8, 16, 24, 31]` for OLMo 3. Only the `0.5` layer is primary; the other
four layers are descriptive and cannot replace it after outcomes are known.

## Primary endpoint and exact null

For color \(c\), define

\[
d_c = h(\text{circle}_c)-h(\text{square}_c),
\]

where \(h\) is the raw-glyph `resid_post` vector at the primary layer. Each
\(d_c\) is L2-normalized. The primary statistic \(T\) is the mean of the ten
off-diagonal pairwise cosines among the five directions. Larger values mean a
more parallel circle-minus-square axis across colors.

The square color labels are exhaustively permuted (`5! = 120`). The one-sided
exact value is

```text
p = count(T_permuted >= T_observed) / 120
```

The two predeclared model-cell p-values form one family and receive Holm
correction at familywise alpha 0.05. No other layer or secondary statistic
receives a confirmatory decision.

## Predeclared outcome patterns

- **Dual-model recurrence candidate:** both primary effects are positive and
  both Holm-adjusted decisions reject.
- **Gemma-only heterogeneity:** only Gemma rejects.
- **OLMo-only heterogeneity:** only OLMo rejects.
- **Opposite-sign heterogeneity:** the primary signs differ.
- **No dual-model recurrence:** no stronger pattern applies.

Even the strongest pattern remains an observational candidate. Model family,
scale, precision/quantization, tokenizer structure, and node are confounded in
this two-cell design.

## Secondary and engineering outputs

All five fixed layers report shape-axis parallelism, centered cross-shape color
pairing, activation RMS, token IDs/counts/prefix diagnostics, and finite-value
checks. Load time, first-forward time, and peak memory are engineering
provenance only. Full logits are not retained; their finiteness and argmax are
recorded. No intervention, generation, protected target, or held-out bank is
opened.

Every model run publishes activation arrays, per-item observations, a scrubbed
receipt, and SHA-256 ledger by atomic directory rename. The joint analysis
revalidates both bundles before computing any endpoint. A passing ledger proves
integrity and replayability, not scientific confirmation.
