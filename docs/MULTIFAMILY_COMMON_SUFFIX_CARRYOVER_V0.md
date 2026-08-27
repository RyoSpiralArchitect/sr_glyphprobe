# Multifamily common-suffix carryover v0

[日本語](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0.ja.md) · [T3 protocol](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.md) · [T3 result](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0_RESULTS.md) · [Research roadmap](ROADMAP.md)

Protocol ID: `glyphprobe-multifamily-common-suffix-carryover-v0`

## Status and narrow question

This is a prospective exploratory observational falsification protocol. Its
executable freeze begins with the first public commit containing this
English/Japanese pair, the configuration, runner/analyzer, tests, engineering
preflight, and checksum manifest. No activation outcome from this protocol may
be inspected before that commit.

T3 read `resid_post` at each raw glyph's final token. OLMo rejected the fixed
matched-slot null, while Gemma did not. In OLMo, however, glyphs in the same
slot share the exact final token. That token is a sufficient local explanation
for T3 and does not support a semantic or causal interpretation.

This protocol moves the readout exactly one token later. It asks whether the
same fixed ten-slot layout remains detectable at a common suffix token whose
identity is identical for all 50 glyphs. Persistence would be evidence of
one-token contextual carryover in this assay. Disappearance would localize the
T3 recurrence to the raw glyph/current-token position at the tested depths.
Neither result tests emoji meaning.

## Fixed inputs and two suffix contexts

The T3 panel is reused unchanged: five consecutive ten-code-point families,
ordered as sky, food, animals, transport, and social, with slots 0 through 9.
No glyph, family, or slot may be added, removed, or reordered.

Each glyph appears in two predeclared contexts:

| Context | Exact text | Gemma suffix token | OLMo suffix token |
|---|---|---:|---:|
| `period` | `glyph + "."` | 235265 | 13 |
| `newline` | `glyph + "\n"` | 108 | 198 |

The contexts were selected before activation capture. They guard against a
single punctuation choice dominating the result; they are not treated as
independent replications.

A tokenizer-only preflight used zero model forwards and established the exact
contract for all 50 items in both models and both contexts:

1. tokenizing the contextualized text preserves the complete raw-glyph token
   sequence as an exact prefix;
2. exactly one context-specific suffix token is appended;
3. that suffix token is identical across all 50 items within a model/context;
4. all 50 combined sequences remain distinct; and
5. decoding returns the exact original glyph plus suffix.

Thus Gemma inputs contain two tokens and OLMo inputs contain four. The models'
raw tokenization regimes remain deliberately different. In particular, the
OLMo family and slot tokens still occur immediately before the common suffix.

## Fixed model cells and capture

| Role | Artifact and node | Raw glyph tokens | Readout token |
|---|---|---|---|
| `gemma2_2b_4bit` | pinned `mlx-community/gemma-2-2b-4bit`, mac2, MLX 4-bit | 50 distinct atomic tokens | common period or newline token |
| `olmo3_7b_bf16` | pinned local OLMo 3 7B, mac1, MLX BF16 | `[9468, family_token, slot_token]` | common period or newline token |

No special token is added. For every item/context pair, `resid_post` at
`last_nonpad` is captured at fixed depth fractions
`[0, 0.25, 0.5, 0.75, 1]`, resolved as
`min(num_layers - 1, floor(fraction * num_layers))`. This yields 100 forward
calls per model and five activation vectors per call. There is no generation,
intervention, protected-target access, or outcome-guided layer selection.

## Sole primary endpoint

For context (c), depth (\ell), family (f), and matched slot (s), let
(h_{c,f,s,\ell}) be the common-suffix activation. At each context/depth cell,
the family mean is removed and the residual sum of squares is decomposed into a
shared slot main effect and family-by-slot interaction:

\[
T_{c,\ell} = \frac{SS_{\mathrm{slot},c,\ell}}
{SS_{\mathrm{slot},c,\ell}+SS_{\mathrm{interaction},c,\ell}}.
\]

The model-level primary statistic is the equal-weight mean of
(T_{c,\ell}) over both fixed contexts and all five fixed depths. Neither a
context nor a depth may replace this omnibus after outcomes are visible.

The null independently permutes the ten slot labels within each family, with
sky held fixed. Each PCG64 draw uses the same four family permutations across
all ten context/depth cells. Seed `20260829` and 19,999 draws are fixed, with

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000.
```

The two model-level p-values form one Holm family at familywise alpha 0.05.
Context-specific, depth-specific, and context-by-depth values are secondary
descriptions only and authorize no multiplicity decision. T3 raw-glyph
statistics are frozen descriptive references and are not pooled into this
test.

## Frozen outcome patterns

- **Dual-model common-suffix recurrence candidate:** both positive
  observed-minus-null excesses survive Holm correction.
- **Gemma-only common-suffix heterogeneity:** only Gemma has a positive excess
  that survives Holm correction; model family, tokenizer, quantization, scale,
  and node remain inseparable.
- **OLMo-only common-suffix carryover:** only OLMo has a positive excess that
  survives Holm correction; the matched-slot structure persists one token into
  context in this assay.
- **Opposite null-centered direction:** the two model excesses have opposite
  signs.
- **No common-suffix slot recurrence:** no stronger predeclared pattern applies.

All branches retain both contexts, all depths, both models, and the complete
negative or mixed evidence. No favorable subcell may be promoted to the primary
claim.

## Claim boundary

Persistence at a common suffix is still observational. It may reflect local
token identity, attention to the immediately preceding glyph tokens, residual
stream dynamics, architecture, tokenizer construction, quantization, scale,
node, or interactions among them. It does not establish semantics, a causal
mechanism, tokenizer independence, model-scale effects, backend parity, or
behavioral steering.

This protocol is not the tokenization-matched confirmatory control set and does
not close a Phase I paper gate. Checksums and successful replay establish
integrity and provenance only.
