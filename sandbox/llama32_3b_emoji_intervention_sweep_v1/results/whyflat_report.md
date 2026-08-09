# Why are some glyphs flat through the middle of the network? (out of contract)

Follow-up to [the deep diagnostic](deep_report.md), which found ⬛ 🥺 ⛵ 🐈‍⬛ to be the only glyphs without a mid-network peak. Negative cases are where a mechanism usually shows itself, so this run takes those four apart. See [README](../README.md) for the boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank used.

## Design

19 glyphs, 28 layers, 3 injection targets, alpha = 0.5, 24 random directions per (layer, target). The panel is built around **near-synonym pairs that differ in UTF-8 byte class** (⛵/🚢, ☕/🍵, ⬛/🟥, ✈️/🚁), the **ZWJ decomposition set** (🐈‍⬛ / 🐈 / 🐱 / ⬛), an **emotion set** (🥺 / 😢 / 😭 / 🤔) and three anchors known to peak mid-network (🍕 🚗 🐶).

Three hypotheses, each made falsifiable:

| | hypothesis | test | verdict |
|---|---|---|---|
| **H1** | it is the UTF-8 byte class, not the meaning | near-synonym pairs differing only in encoding | **partly supported** |
| **H2** | 🐈‍⬛'s direction is dominated by its ⬛ tail | cosine of 🐈‍⬛'s direction to 🐈 vs ⬛, per layer | **refuted (but a new puzzle)** |
| **H3** | the model has no concept for these glyphs | ask it to name them | **refuted** |

## Metric correction

The run script classified profiles with a binary label (mid-network max > final-layer value). **That label is wrong for this question**: it is driven by the final-layer value, which varies for reasons unrelated to mid-network engagement. It calls ☕ a mid-peak (mid 2.87) and 🚢 a last-peak (mid 3.72) — i.e. it ranks a weaker glyph above a stronger one. Everything below uses the **absolute mid-network ratio** (max over L10-19), which is what actually answers "does this direction engage the middle of the network". `scripts/analyze_whyflat.py` carries the same note.

## H3 — does the model even know these glyphs? Refuted.

| glyph | id | P(concept) | best rank | greedy continuation of "The emoji &lt;g&gt; is a picture of a" |
|---|---|---|---|---|
| 🟥 | `red_sq` | 0.5170 | 1 | ` red traffic light. It is also known` |
| 🚗 | `car` | 0.4959 | 1 | ` car, which shows the direction of travel` |
| 🐶 | `dog` | 0.4312 | 1 | ` dog, which shows a happy face.` |
| 🐱 | `cat_face` | 0.3531 | 1 | ` cat, which looks like a small domestic` |
| ☕ | `coffee` | 0.3189 | 1 | ` coffee cup. It is used to represent` |
| 🍕 | `pizza` | 0.3172 | 1 | ` pizza, which is a flat round bread` |
| ✈️ | `airplane` | 0.3144 | 1 | ` plane. It is used to represent a` |
| 🚁 | `helicopter` | 0.2851 | 1 | ` helicopter. It can be used to represent` |
| 🐈 | `cat_plain` | 0.2444 | 1 | ` cat, which looks like a black and` |
| 🐈‍⬛ | `black_cat` | 0.2420 | 1 | ` black cat with a white face and a` |
| 🚢 | `ship` | 0.1992 | 1 | ` ship. It is also known as the` |
| 😢 | `crying` | 0.1526 | 1 | ` weeping face. It is used to` |
| 🍵 | `tea` | 0.1171 | 1 | ` cup of coffee with cream and sugar.` |
| ⛵ | `sailboat` | 0.1108 | 1 | ` ship. It can be used to represent` |
| ⬛ | `black_sq` | 0.1057 | 1 | ` black square with a white border. It` |
| 😭 | `sob` | 0.0938 | 2 | ` weeping face. It is used to` |
| 🥺 | `pleading` | 0.0800 | 2 | ` person with their hands on their face,` |
| ⚓ | `anchor` | 0.0608 | 1 | ` sailor’s anchor. It is used to` |
| 🤔 | `thinking` | 0.0598 | 2 | ` person with a confused face. It is` |

Every glyph's correct concept is the **top-1 or top-2** next token, the four flat ones included: ⬛ continues `' black square with a white border. It'`, 🐈‍⬛ continues `' black cat with a white face and a'`. The model knows them. Spearman(P(concept), mid ratio) = **+0.337** — a weak association, nowhere near an explanation.

## The picture that replaces the binary split

| # | glyph | id | byte class | semantic | mid (L10-19) | final L27 | peak layer |
|---|---|---|---|---|---|---|---|
| 1 | 🥺 | `pleading` | F0 | emotion | **2.71** | 3.90 | L27 |
| 2 | ⛵ | `sailboat` | E2 | vehicle | **2.75** | 5.38 | L27 |
| 3 | 🤔 | `thinking` | F0 | emotion | **2.76** | 4.94 | L27 |
| 4 | ☕ | `coffee` | E2 | food | **2.87** | 2.40 | L16 |
| 5 | 🟥 | `red_sq` | F0 | abstract | **2.96** | 3.68 | L27 |
| 6 | ⚓ | `anchor` | E2 | object | **2.99** | 4.14 | L27 |
| 7 | ⬛ | `black_sq` | E2 | abstract | **3.00** | 6.43 | L27 |
| 8 | ✈️ | `airplane` | E2 | vehicle | **3.05** | 3.14 | L27 |
| 9 | 🐈‍⬛ | `black_cat` | ZWJ | animal | **3.09** | 3.82 | L27 |
| 10 | 🚁 | `helicopter` | F0 | vehicle | **3.55** | 2.44 | L14 |
| 11 | 🐶 | `dog` | F0 | animal | **3.71** | 1.51 | L14 |
| 12 | 🚢 | `ship` | F0 | vehicle | **3.72** | 4.03 | L27 |
| 13 | 🐱 | `cat_face` | F0 | animal | **3.95** | 1.64 | L14 |
| 14 | 🐈 | `cat_plain` | F0 | animal | **3.96** | 2.65 | L15 |
| 15 | 😭 | `sob` | F0 | emotion | **4.19** | 1.65 | L17 |
| 16 | 😢 | `crying` | F0 | emotion | **4.22** | 1.68 | L19 |
| 17 | 🍵 | `tea` | F0 | food | **4.59** | 1.35 | L15 |
| 18 | 🍕 | `pizza` | F0 | food | **5.32** | 1.74 | L15 |
| 19 | 🚗 | `car` | F0 | vehicle | **5.66** | 1.32 | L14 |

The mid-network ratio is a **continuum** from 2.71 to 5.66; the largest gap anywhere in the sorted list is only 0.73. **This overturns the deep diagnostic's claim that the panel splits cleanly with no exceptions** — that was a property of a 13-glyph panel with no intermediate cases, not of the model.

## H1 — UTF-8 byte class. Partly supported.

3-byte glyphs (U+26xx / U+2Bxx, the legacy dingbat and geometric-shape blocks, leading byte-token 158) versus 4-byte emoji-plane glyphs (leading byte-token 9468):

| pair | 3-byte (E2) | mid | 4-byte (F0) | mid | F0/E2 |
|---|---|---|---|---|---|
| boat | ⛵ `sailboat` | 2.75 | 🚢 `ship` | 3.72 | **1.35** |
| drink | ☕ `coffee` | 2.87 | 🍵 `tea` | 4.59 | **1.60** |
| square | ⬛ `black_sq` | 3.00 | 🟥 `red_sq` | 2.96 | **0.99** |
| air | ✈️ `airplane` | 3.05 | 🚁 `helicopter` | 3.55 | **1.16** |

Three of four pairs put the 4-byte member higher (median 1.26x). The exception is the **abstract** pair — two featureless squares, where both sit at the floor (⬛ 3.00, 🟥 2.96). Overall Spearman(is 3-byte, mid ratio) = **-0.502**, and Spearman(token count, mid ratio) = -0.017, so this is not token count in disguise.

All 5 3-byte glyphs (⛵ ☕ ⚓ ⬛ ✈️) land in the bottom half; none reaches the top. But three 4-byte glyphs (🥺 🤔 🟥) are just as low, so being 3-byte looks **sufficient but not necessary** for a weak mid-network effect on this panel.

The most likely reading is that byte class is a *proxy*: the U+26xx/U+2Bxx blocks are full of abstract symbols, and abstractness is doing part of the work. The pairs argue against that being the whole story — ⛵ and 🚢 are both concrete boats and still differ 1.35x — but four loose near-synonyms is thin evidence. Treat H1 as suggestive.

## H2 — is 🐈‍⬛ dragged down by its ⬛ tail? Refuted, and it leaves a better puzzle.

🐈‍⬛ tokenises as `[9468, 238, 230] + [102470] + [158, 105, 249]` — literally 🐈's tokens, ZWJ, then ⬛'s tokens. But its residual direction stays on the cat side at every depth:

| layer | cos(🐈‍⬛, 🐈) | cos(🐈‍⬛, ⬛) | margin |
|---|---|---|---|
| 0 | 1.000 | 1.000 | +0.000 |
| 2 | 0.985 | 0.972 | +0.014 |
| 5 | 0.973 | 0.915 | +0.058 |
| 8 | 0.956 | 0.880 | +0.077 |
| 11 | 0.954 | 0.872 | +0.083 |
| 14 | 0.949 | 0.852 | +0.097 |
| 16 | 0.944 | 0.843 | +0.102 |
| 20 | 0.947 | 0.807 | +0.140 |
| 24 | 0.947 | 0.796 | +0.152 |
| 27 | 0.942 | 0.765 | +0.177 |

The margin *widens* with depth (+0.00 at L0 to +0.177 at the last layer). So the direction is not being replaced by ⬛'s.

And yet the efficacy — the mid-network ratio — collapses to exactly ⬛'s level:

| 🐈 cat | 🐱 cat face | 🐈‍⬛ black cat | ⬛ black square |
|---|---|---|---|
| **3.96** | **3.95** | **3.09** | **3.00** |

**Both plain cats engage the middle of the network; the ZWJ compound does not, even though its direction is still cat-shaped and the model still names it "black cat".** Direction similarity and causal efficacy come apart. Whatever ZWJ composition costs, it is not "the direction becomes the last component".

Next step for this: extract the direction at each *token position* of 🐈‍⬛ (the 🐈 tokens, the ZWJ token, the ⬛ tokens) instead of only at `last_nonpad` of the wrapper, and see where the efficacy is lost.

## Other things this run settles

- **Not "emotions are flat".** 😢 (4.22) and 😭 (4.19) peak mid-network; 🥺 (2.71) and 🤔 (2.76) do not. Within one semantic family the spread is 1.6x.
- **Not token count.** Spearman(n_tokens, mid ratio) = -0.017.
- **Replication.** ⛵, ⬛, 🥺, 🐈‍⬛, 🍕 and 🚗 reproduce their deep-diagnostic mid and final values exactly (same seeds, same config), so the two runs are directly comparable.

## Limitations

- Four near-synonym pairs is thin, and the synonyms are loose (⛵ sailboat vs 🚢 passenger ship; ☕ coffee vs 🍵 tea; ✈️ aeroplane vs 🚁 helicopter). Training-set frequency is uncontrolled and is a live alternative explanation for every H1 result.
- `P(concept)` uses a different hand-written word list per glyph, so the absolute probabilities are not strictly comparable across glyphs; the rank (1 or 2 for all 19) is the robust part.
- One model, one position (`last_nonpad`), one site (`resid_post`), one strength.
- The random-direction null is a **size** control, not a semantic control.
- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). The weights are byte-identical to the sealed v2 artifact; nothing else here is comparable to a canonical run.
