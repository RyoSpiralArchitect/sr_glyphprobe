# Multifamily repeated-carrier distance v0

[日本語](MULTIFAMILY_CARRIER_DISTANCE_V0.ja.md) · [T4 result](MULTIFAMILY_COMMON_SUFFIX_CARRYOVER_V0_RESULTS.md) · [Research roadmap](ROADMAP.md)

Protocol ID: `glyphprobe-multifamily-carrier-distance-v0`

## Status and narrow question

This is a prospective exploratory observational falsification protocol. Its
executable freeze begins with the first public commit containing this
English/Japanese pair, the configuration, runner/analyzer, tests, engineering
preflight, and checksum manifest. No activation outcome from this protocol may
be inspected before that commit.

T4 found matched-slot geometry at a common token one position after the glyph
in OLMo, but not in Gemma. That rules out the narrow description that the
effect exists only when the current token is the raw slot token. It does not
distinguish a short local trace from longer contextual transport.

This protocol keeps the full input and current carrier-token identity fixed,
then reads the residual stream 1, 2, 4, and 8 carrier tokens after the glyph.
It asks whether distance-1 recurrence coexists with a predeclared positive
log-distance attenuation contrast. It does not test emoji meaning or a causal
mechanism.

## Fixed panel, carriers, and positions

The unchanged T3/T4 panel contains five ordered families—sky, food, animals,
transport, and social—with ten matched Unicode-offset slots per family. No
glyph, family, or slot may be changed.

Each glyph receives two exact eight-token carriers:

| Carrier | Exact suffix text | Gemma token | Llama token | OLMo token |
|---|---|---:|---:|---:|
| `article_a` | `" a"` repeated 8 times | 476 | 264 | 264 |
| `pipe` | `" |"` repeated 8 times | 1420 | 765 | 765 |

Tokenizer-only preflight used zero model forwards and established, for all 50
items and all three models, that:

1. contextual tokenization preserves the complete raw-glyph sequence;
2. exactly eight identical carrier tokens follow it;
3. the full sequence remains unique for every glyph; and
4. exact decode returns the original glyph plus carrier text.

The readout position is `raw_token_count + distance - 1`, for fixed distances
`[1, 2, 4, 8]`. The complete eight-token input is forwarded at every distance.
Only the captured position changes. This avoids changing sequence length or
the current token across distance cells, at the cost of four independent
forwards per glyph/carrier.

Repeated tokens can themselves induce repetition-specific dynamics. The two
carrier identities reduce dependence on one token but do not remove this
limitation.

## Three fixed MLX model cells

| Role | Node | Raw panel tokenization | Precision |
|---|---|---|---|
| `gemma2_2b_4bit` | mac2 | 50 distinct atomic glyph tokens | MLX 4-bit |
| `llama32_3b_bf16` | mac2 | 47 three-token and 3 frozen two-token sequences | MLX BF16 |
| `olmo3_7b_bf16` | mac1 | exact common-prefix + family + slot factorization | MLX BF16 |

Llama 3.2 3B was selected before this run as the requested larger-model
transfer cell. Its complete raw-token roster is pinned by SHA-256 because three
glyphs merge the nominal family/slot pair. Llama and OLMo share the two carrier
token IDs, but their raw tokenization is not identical; tokenizer equivalence
is not claimed.

For each model, `resid_post` is captured at five fixed depth fractions
`[0, 0.25, 0.5, 0.75, 1]`. The protocol performs
`50 × 2 × 4 = 400` full-sequence forwards per model and 1,200 total. There is
no generation, intervention, protected-target access, or furnace compute.

The earlier Llama MLX Stage-A parity gate remains unqualified. These are native
MLX observational cells, not backend-equivalent measurements.

## Sole primary decision

At every carrier, distance, and depth, activations are arranged as family by
matched slot. After removing each family mean, the slot fraction is

\[
S_{c,d,\ell} = \frac{SS_{\mathrm{slot}}}
{SS_{\mathrm{slot}}+SS_{\mathrm{interaction}}}.
\]

The primary decision is an intersection-union test with two components:

1. **Distance-1 recurrence:** the equal-weight mean of
   \(S_{c,1,\ell}\) across both carriers and all five depths.
2. **Attenuation contrast:** the equal-weight mean across carriers and depths
   of the fixed distance weights
   `[0.375, 0.125, -0.125, -0.375]` for distances `[1, 2, 4, 8]`.

The contrast is the negative linear slope on `log2(distance)`, scaled to unit
absolute weight. A positive value supports attenuation on average; it does not
require every adjacent step to decrease and cannot establish disappearance.

The null independently permutes the ten slot labels within each non-reference
family, holding sky fixed. Every PCG64 draw uses the same four permutations
across all 40 carrier/distance/depth cells. Seed `20260830` and 19,999 draws are
fixed. Each one-sided component uses

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000.
```

The model-level intersection-union p-value is the larger component p-value, so
both components must be small. The three model-level p-values form one Holm
family at familywise alpha 0.05. No carrier, distance, depth, tail, or
cross-model magnitude comparison can replace this decision.

## Frozen outcomes and claim boundary

Named branches cover all three models, the Llama/OLMo pair, each single-model
case, other two-model combinations, and no rejection. Every branch retains the
complete profile. T4 is a frozen design motivation and descriptive reference;
its values are not pooled into the test.

A rejecting model supports only this statement: in the fixed panel, carriers,
depths, and MLX cell, distance-1 matched-slot recurrence and the fixed positive
attenuation contrast coexist. It does not show monotonic decay, disappearance,
semantic representation, causal transport, behavioral steering, tokenizer
equivalence, architecture or scale effects, backend parity, confirmation, or a
Phase I gate decision.

This experiment is deliberately cheap observational discrimination. It does
not replace tokenization-matched confirmatory controls or held-out causal work.
