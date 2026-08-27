# Multifamily matched-slot geometry v0

[日本語](MULTIFAMILY_MATCHED_SLOT_GEOMETRY_V0.ja.md) · [E1 results](EMOJI_FAMILY_EXPLORATORY_RESULTS.md) · [Tokenizer census](MULTIFAMILY_TOKENIZER_CENSUS_V0_RESULTS.md) · [Research roadmap](ROADMAP.md)

Protocol ID: `glyphprobe-multifamily-matched-slot-geometry-v0`

## Status and question

This is a prospective exploratory observational protocol. Its executable freeze
starts with the first public commit that contains this English/Japanese pair,
the configuration, runner/analyzer, tests, engineering preflight, and checksum
manifest. No activation outcome from this protocol may be inspected before that
commit. Earlier tokenizer-only work used zero model forwards and is design
evidence rather than an outcome.

The narrow question is whether the same ten-position layout recurs across five
fixed emoji families at five fixed depths in two very different tokenizer
regimes. The study does not test emoji meaning. It does not ask whether sky,
food, animal, transport, or social concepts are represented semantically.

## Fixed 5 by 10 panel

The existing E1 panel is reused without adding or removing a glyph. Each family
is one consecutive ten-code-point block, and the final hexadecimal position is
matched across families.

| Family | Ordered code points | Glyphs |
|---|---|---|
| sky | U+1F311–U+1F31A | 🌑 🌒 🌓 🌔 🌕 🌖 🌗 🌘 🌙 🌚 |
| food | U+1F351–U+1F35A | 🍑 🍒 🍓 🍔 🍕 🍖 🍗 🍘 🍙 🍚 |
| animals | U+1F411–U+1F41A | 🐑 🐒 🐓 🐔 🐕 🐖 🐗 🐘 🐙 🐚 |
| transport | U+1F691–U+1F69A | 🚑 🚒 🚓 🚔 🚕 🚖 🚗 🚘 🚙 🚚 |
| social | U+1F911–U+1F91A | 🤑 🤒 🤓 🤔 🤕 🤖 🤗 🤘 🤙 🤚 |

The shared position is called a **matched slot**. It is a Unicode/tokenizer
construction, not a semantic label.

## Two deliberately different tokenizer regimes

The completed census and a tokenizer-only replay established the following
fixed contracts before any activation capture:

- Gemma 2 maps all 50 glyphs to 50 distinct one-token sequences. There is no
  shared token position across families.
- OLMo 3 maps every glyph to exactly three tokens:
  `[9468, family_token, slot_token]`. The family token is fixed within a row of
  the panel, and the slot token is fixed within a column. All 50 sequences are
  unique and decode back to the original glyph.

These regimes are not equivalent. OLMo slot recurrence can be explained by the
identical final token. Gemma recurrence, if observed, can still reflect learned
token embeddings, tokenizer vocabulary construction, Unicode regularity, model
architecture, quantization, or their interactions. A dual result is therefore
only an observational cross-regime candidate.

## Fixed model cells and capture

| Role | Model artifact | Runtime | Token contract |
|---|---|---|---|
| `gemma2_2b_4bit` | `mlx-community/gemma-2-2b-4bit` | mac2, MLX, 4-bit | 50 distinct atomic tokens |
| `olmo3_7b_bf16` | sealed local OLMo 3 7B artifact | mac1, MLX, BF16 | exact prefix × family × slot tokenization |

Both artifacts are pinned by path-independent full-file manifests. Each raw
glyph is forwarded without special tokens. `resid_post` is captured at the
last item token at fractions `[0, 0.25, 0.5, 0.75, 1]`, resolved as
`min(num_layers - 1, floor(fraction * num_layers))`. This gives layers
`[0, 6, 13, 19, 25]` for Gemma and `[0, 8, 16, 24, 31]` for OLMo.

## Primary all-depth endpoint

At one depth, let \(h_{f,s}\) be the activation for family \(f\) and matched
slot \(s\). First remove the mean activation of each family. The remaining sum
of squares decomposes into a shared slot main effect and a family-by-slot
interaction:

\[
T_\ell = \frac{SS_{\text{slot},\ell}}
{SS_{\text{slot},\ell}+SS_{\text{interaction},\ell}}.
\]

The model-level primary statistic is the equal-weight mean of \(T_\ell\) over
all five fixed depths. No depth can replace another after outcomes are visible.

The randomization null independently permutes the ten slot labels within each
family. Sky is held fixed because a common simultaneous permutation changes no
pairing. The other four family permutations are sampled with NumPy PCG64 seed
`20260828`; the same draw is used at every depth. There are 19,999 draws, and

```text
p = (1 + count(T_randomized >= T_observed)) / 20,000.
```

The two model-level p-values form one Holm family at familywise alpha 0.05.
Per-depth statistics and p-values are secondary descriptions and authorize no
decision.

## Frozen outcome patterns

- **Dual-model slot-recurrence candidate:** both observed-minus-null-mean
  excesses are positive and both Holm decisions reject.
- **Gemma-only heterogeneity:** only the atomic Gemma cell rejects.
- **OLMo-only token-structured recurrence:** only OLMo rejects; its shared final
  slot token is an expected sufficient explanation.
- **Opposite null-centered direction:** the two excesses have opposite signs.
- **No dual-model slot recurrence:** no stronger pattern applies.

Every pattern retains all model, family, and depth rows. None permits selecting
a favorable layer, family, or alternative endpoint.

## Secondary outputs and claim boundary

The complete fixed-depth slot profile, family main-effect fraction, interaction
fraction, activation RMS, exact token sequences, finite-value checks, and
engineering timing/memory provenance are retained. Timing is not a speed claim.

This study performs no intervention, generation, target-bank access, behavioral
evaluation, or causal test. It cannot establish semantic families, a
tokenizer-independent glyph property, model-scale effects, quantization
effects, node effects, backend parity, confirmation, or a Phase I paper gate.
Passing manifests and checksums establish integrity and replayability only.
