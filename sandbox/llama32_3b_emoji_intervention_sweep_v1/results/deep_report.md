# Deep diagnostic — focused panel, large controls (out of contract)

Follow-up to [the 50-glyph sweep](report.md), targeting its two weaknesses: only 3 injection targets and only 24 random directions. See [README](../README.md) for the boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank used.

## Run

- 13 glyphs (strong / high-prompt / weak-control / ZWJ), 12 injection targets, alpha = 0.5
- phase 1: 156 rows, 522 s
- phase 2: 364 rows, 649 s
- phase 3: 78 rows, 39 s
- phase 4: 13 rows, 78 s
- total 1287 s on an M4 (MPS/FP32)

## Phase 1 — does it generalise, and at what resolution?

256 random directions per target puts the nonparametric floor at p = 1/257 = 0.0039 (sweep_v1 could only reach 1/25 = 0.04).

| target | entropy | top-2 margin | null median | ratio median | glyphs clearing null |
|---|---|---|---|---|---|
| `thinking` | 5.57 | 0.49 | 0.0398 | 6.95 | **13/13** |
| `sky` | 5.15 | 0.73 | 0.0556 | 2.83 | **10/13** |
| `tell` | 4.74 | 0.54 | 0.0386 | 5.70 | **13/13** |
| `reminds` | 4.43 | 0.62 | 0.0255 | 4.29 | **13/13** |
| `summer` | 4.12 | 0.52 | 0.0749 | 3.03 | **13/13** |
| `today` | 3.58 | 0.34 | 0.0345 | 5.74 | **13/13** |
| `paris` | 2.81 | 2.21 | 0.0505 | 2.75 | **0/13** |
| `animal` | 2.70 | 0.40 | 0.0584 | 3.63 | **1/13** |
| `planet` | 2.54 | 2.77 | 0.0674 | 3.26 | **0/13** |
| `freeze` | 2.24 | 1.45 | 0.0343 | 3.91 | **0/13** |
| `citytokyo` | 1.42 | 3.32 | 0.0212 | 3.73 | **7/13** |
| `gold` | 1.13 | 2.69 | 0.0222 | 5.16 | **1/13** |

- Spearman(entropy, glyphs clearing null) = **+0.695**
- Spearman(entropy, ratio median) = +0.147
- Spearman(top-2 margin, ratio median) = -0.385

Six of twelve targets are cleared by **all 13 glyphs**. sweep_v1's "clean only on the open-ended target" was a target-count and null-size artefact, not a property of the effect. Detectability is a property of the *target*: sharp factual prompts (`paris`, `planet`, `freeze`) hide the effect because a random push moves them a lot too.

| glyph | group | ratio median | clean | min p | argmax flips |
|---|---|---|---|---|---|
| 🍕 `pizza` | strong | **4.83** | 6/12 | 0.0039 | 2 |
| 🍣 `sushi` | strong | **4.66** | 7/12 | 0.0039 | 2 |
| 🍜 `ramen` | strong | **4.64** | 6/12 | 0.0039 | 2 |
| 🐱 `cat` | high_prompt | **4.49** | 7/12 | 0.0039 | 2 |
| 🍺 `beer` | strong | **4.36** | 7/12 | 0.0039 | 2 |
| 🍔 `burger` | strong | **4.17** | 6/12 | 0.0039 | 2 |
| 🌍 `earth` | strong | **4.03** | 6/12 | 0.0039 | 1 |
| 🐶 `dog` | high_prompt | **3.95** | 7/12 | 0.0039 | 2 |
| 🐈‍⬛ `black_cat` | zwj | **3.64** | 7/12 | 0.0039 | 2 |
| 🚗 `car` | strong | **3.52** | 6/12 | 0.0039 | 2 |
| ⬛ `black_square` | weak | **3.38** | 6/12 | 0.0039 | 2 |
| 🥺 `pleading` | weak | **3.09** | 7/12 | 0.0039 | 2 |
| ⛵ `sailboat` | weak | **2.97** | 6/12 | 0.0039 | 2 |

strong group ratio median **4.36** vs weak-control **3.09**. But the *binary* test saturates: the weak controls clear the null on 6-7 of 12 targets too. **Significance and effect size come apart here** — the ranking has to be read from the ratio, not from whether a cell is significant.

**Replication.** sweep_v1 (3 targets, 24 nulls) vs this run (12 targets, 256 nulls), same 13 glyphs at L16: Spearman = **+0.753**. The ordering holds; individual positions move (🚗 4.89→3.52, 🐱 3.63→4.49).

## Phase 2 — layer profile over every layer

| glyph | group | peak layer | peak ratio | mid-network max (L10-19) | final layer L27 | shape |
|---|---|---|---|---|---|---|
| 🍺 `beer` | strong | L16 | 5.16 | 5.16 | 1.43 | **mid-peak** |
| 🍕 `pizza` | strong | L15 | 5.32 | 5.32 | 1.74 | **mid-peak** |
| 🍣 `sushi` | strong | L16 | 5.20 | 5.20 | 1.26 | **mid-peak** |
| 🍔 `burger` | strong | L16 | 4.70 | 4.70 | 1.56 | **mid-peak** |
| 🌍 `earth` | strong | L14 | 5.25 | 5.25 | 2.05 | **mid-peak** |
| 🚗 `car` | strong | L14 | 5.66 | 5.66 | 1.32 | **mid-peak** |
| 🍜 `ramen` | strong | L16 | 4.40 | 4.40 | 1.27 | **mid-peak** |
| 🐶 `dog` | high_prompt | L14 | 3.71 | 3.71 | 1.51 | **mid-peak** |
| 🐱 `cat` | high_prompt | L14 | 3.95 | 3.95 | 1.64 | **mid-peak** |
| ⬛ `black_square` | weak | L27 | 6.43 | 3.00 | 6.43 | last-peak |
| 🥺 `pleading` | weak | L27 | 3.90 | 2.71 | 3.90 | last-peak |
| ⛵ `sailboat` | weak | L27 | 5.38 | 2.75 | 5.38 | last-peak |
| 🐈‍⬛ `black_cat` | zwj | L27 | 3.82 | 3.09 | 3.82 | last-peak |

> ⚠️ **Superseded by [the why-flat follow-up](whyflat_report.md).** This section originally claimed the split was exhaustive and exception-free. That was a property of *this 13-glyph panel*, which contains no intermediate cases. Across 19 glyphs the mid-network ratio is a **continuum** (2.71 → 5.66, largest gap 0.73), and the binary label is driven by the *final-layer* value rather than by mid-network engagement — it mislabels ☕ (mid 2.87, called mid-peak) and 🚢 (mid 3.72, called last-peak). Read the mid-network column, not the label.

The split as it falls out on this panel:

- **mid-peak** (🍺 🍕 🍣 🍔 🌍 🚗 🍜 🐶 🐱): peak at **L14-16**, ratio 3.7-5.7, falling to 1.3-2.1 by the final layer.
- **last-peak** (⬛ 🥺 ⛵ 🐈‍⬛): flat 2.7-3.1 through the middle, spiking to 3.8-6.4 at L27.

L27 is the last layer: its `resid_post` feeds the final norm and the unembedding, so a perturbation there is close to editing the logits directly. A high ratio at L27 means the direction is *token-like* (it lives where real token representations live); a high ratio at L14-16 means the direction engages the model's remaining computation. These are different claims, and ⬛'s peak ratio of 6.43 — the largest number in the whole run — is entirely of the first kind.

At **L0 every glyph sits at ratio 0.05**, i.e. a real emoji direction is ~20x *less* disruptive than a matched random one at the embedding layer. Direction consistency runs the other way: 0.930 at L0 falling to 0.432 at the last layer. Where the direction is most reproducible it does the least, and vice versa.

## Phase 3 — specificity and sign flip

Probe words were written by hand per glyph, **not** harvested from the model's own top-boosted lists, so the diagonal is not selected-on.

- own probe group largest (instance level): **4/13**
- own *category block* largest: **10/13**
- sign-flip antisymmetry `cos(probe_delta(+d), -probe_delta(-d))`: median +0.633, min -0.362


**Probe-group overlap.** Truncating each probe word to its first token makes some hand-written groups share ids — `cat`/`black_cat` share 3 of 6; `black_square`/`black_cat` share 1 of 6 (black cats are cats, so this is semantically right but makes an instance-level diagonal ambiguous). Excluding every competitor column that shares a token with the row leaves the count **unchanged at 4/13**, so the conclusion does not depend on the overlap.

| injected | food | animal | vehicle | other | own block | margin over best other |
|---|---|---|---|---|---|---|
| 🍺 `beer` | +1.66 | +0.49 | +0.09 | -0.14 | `food` | +1.18 ✅ |
| 🍕 `pizza` | +1.86 | +0.21 | -0.74 | -0.18 | `food` | +1.65 ✅ |
| 🍣 `sushi` | +2.06 | +0.62 | -0.18 | -0.25 | `food` | +1.44 ✅ |
| 🍔 `burger` | +2.02 | +0.46 | -0.55 | -0.09 | `food` | +1.56 ✅ |
| 🌍 `earth` | +0.43 | +0.22 | +0.34 | +0.24 | `other` | -0.19 |
| 🚗 `car` | -0.44 | -0.04 | +1.27 | -0.32 | `vehicle` | +1.32 ✅ |
| 🍜 `ramen` | +1.97 | +0.82 | -0.63 | -0.07 | `food` | +1.15 ✅ |
| 🐶 `dog` | +0.01 | +1.55 | -0.71 | +0.14 | `animal` | +1.40 ✅ |
| 🐱 `cat` | +0.22 | +1.71 | -0.67 | +0.13 | `animal` | +1.48 ✅ |
| ⬛ `black_square` | +0.15 | +0.25 | -0.38 | +0.29 | `other` | +0.04 ✅ |
| 🥺 `pleading` | +0.24 | +0.03 | -0.83 | -0.17 | `other` | -0.40 |
| ⛵ `sailboat` | -0.04 | +0.24 | -0.48 | +0.17 | `vehicle` | -0.72 |
| 🐈‍⬛ `black_cat` | +0.05 | +0.84 | -0.74 | +0.09 | `animal` | +0.75 ✅ |

**The direction carries a category, not an instance.** 🍣 boosts *burger* probes (+2.95) more than *sushi* probes (+1.86); 🍺 boosts *burger* (+2.30) more than *beer* (+1.40). At block level the food glyphs beat the next-best block by +1.15 to +1.65 and 🚗 beats it by +1.32. The failures are informative: 🥺 (own block −0.17) and ⛵ (−0.48) carry no category signal at all, and ⛵ scores −0.48 on *vehicle* where 🚗 scores +1.27 — sharing a category with a strong glyph buys nothing.

Antisymmetry of only ~0.63 means +d and −d are **not** mirror images at alpha = 0.5: the response is already outside the linear regime, so the probe deltas should be read as directional evidence, not as a linear readout.

## Phase 4 — does a better direction estimate help?

| extraction wrappers | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|
| median direction consistency | 0.265 | 0.299 | 0.349 | 0.343 | 0.351 | 0.364 |

Consistency saturates around 0.36 — tripling the wrappers buys almost nothing, and the median effect *falls* by 0.18 (cos between the 4-wrapper and 12-wrapper directions is ~0.87). Averaging more contexts trades a little effect size for generality; the strong glyphs lose (🍜 −0.37, 🐶 −0.43) and the weak controls gain (⛵ +0.31, ⬛ +0.23), which is what regression toward a context-general mean looks like. **4 wrappers was already enough.**

## Limitations

- One model, one position (`last_nonpad`), one site (`resid_post`), one strength for phases 1/3/4. The layer profile is the only dimension swept exhaustively.
- The category blocks are hand-drawn and one assignment is poor: 🌍 `earth` was placed in a catch-all `other` block with ⬛ and 🥺, so its block test fails even though its layer profile is squarely mid-peak. Treat the 🌍 block result as an artefact of the grouping, not a finding.
- Probe groups are 6 hand-picked words each, first token of `' <word>'` only.
- The random-direction null is a **size** control, not a semantic control. Beating it shows a direction is structured, not that the structure is meaning.
- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are byte-identical to the sealed v2 artifact; nothing else here is comparable to a canonical run.
