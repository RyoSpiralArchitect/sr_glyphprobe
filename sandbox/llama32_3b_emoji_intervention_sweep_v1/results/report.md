# Per-glyph emoji intervention sweep — results (out of contract)

Generated from `sweep_v1_records.jsonl` by `scripts/analyze_sweep.py`. See [README](../README.md) for method and boundary. Claim stage: `pre-causal-activation-screen`, `causal_claim_authorized: false`.

## Run

- 50 glyphs, 2,157 records, 359 s (M4, MPS/FP32)
- layers [5, 11, 16], alphas [0.1, 0.5, 1.0] (primary 0.5), 24 random-direction controls per (layer, target, alpha)
- extraction wrappers: 'Today I saw a', 'My favorite thing is', 'Here we have', 'This reminds me of'
- injection targets: `The capital of France is` (top-1 ` Paris`), `The largest planet in our solar system is` (top-1 ` Jupiter`), `I am thinking about` (top-1 ` the`)
- zero-hook exact no-op: **True**; dose-monotonic cells: **100%**

## Correlations

| relationship | Spearman ρ |
|---|---|
| prefix token count vs prompt-level KL (all 50) | **+0.063** |
| prefix token count vs ratio-to-null (all 50) | **-0.078** |
| prompt-level KL vs ratio-to-null (matched stratum) | **+0.550** |

## A. Token-matched stratum — full ranking by prompt-level effect (38 glyphs, all exactly 4 prefix tokens)

| # | glyph | id | family | prompt KL | ratio L16 | z | consistency | top boosted |
|---|---|---|---|---|---|---|---|---|
| 1 | 🐶 | dog | animal | 0.5861 | 3.52 | +7.8 | 0.293 | ` Animals` ` Animal` ` dogs` |
| 2 | 🐱 | cat | animal | 0.5470 | 3.63 | +8.2 | 0.297 | ` Animals` ` Animal` ` dogs` |
| 3 | 🍕 | pizza | food | 0.4997 | 5.67 | +16.2 | 0.335 | ` yummy` ` delicious` ` pizza` |
| 4 | 🍔 | burger | food | 0.4871 | 5.19 | +13.3 | 0.324 | ` steak` ` pizza` ` sandwiches` |
| 5 | 🍜 | ramen | food | 0.4771 | 4.85 | +12.1 | 0.321 | ` steak` ` pizza` ` sandwiches` |
| 6 | 🚗 | car | transport | 0.4684 | 4.89 | +11.7 | 0.305 | ` Automobile` ` Vehicles` ` cars` |
| 7 | 🍣 | sushi | food | 0.4669 | 5.63 | +14.3 | 0.327 | ` steak` ` seafood` ` Steak` |
| 8 | 🍺 | beer | food | 0.4604 | 5.74 | +14.2 | 0.271 | ` steak` ` FOOD` ` Steak` |
| 9 | 🐢 | turtle | animal | 0.4573 | 3.36 | +6.6 | 0.253 | ` Animals` ` Animal` ` animals` |
| 10 | 🌈 | rainbow | nature | 0.4532 | 4.54 | +10.0 | 0.277 | ` Magical` ` COLOR` ` Cute` |
| 11 | 🦁 | lion | animal | 0.4515 | 3.38 | +5.9 | 0.229 | ` �` ` Animals` `�` |
| 12 | 🐻 | bear | animal | 0.4451 | 3.77 | +7.8 | 0.278 | ` Animals` ` Animal` ` animals` |
| 13 | 🚂 | locomotive | transport | 0.4305 | 3.75 | +7.0 | 0.225 | ` �` ` �` `�` |
| 14 | 🦊 | fox | animal | 0.4303 | 3.96 | +7.3 | 0.283 | ` �` ` �` ` �` |
| 15 | 🌸 | blossom | nature | 0.4212 | 4.40 | +9.9 | 0.267 | ` Magical` ` Gorgeous` ` ❤` |
| 16 | 🦋 | butterfly | animal | 0.4209 | 4.19 | +8.5 | 0.277 | ` ❤` ` �` ` �` |
| 17 | 🚲 | bicycle | transport | 0.4133 | 2.93 | +5.2 | 0.282 | ` �` ` Vehicles` ` �` |
| 18 | 🍎 | apple | food | 0.4078 | 4.53 | +9.8 | 0.260 | ` FOOD` ` Cute` ` ❤` |
| 19 | 🌊 | wave | nature | 0.3862 | 3.56 | +6.5 | 0.243 | ` �` `️` `�` |
| 20 | 🌙 | moon | nature | 0.3861 | 4.23 | +8.9 | 0.242 | ` candle` ` Magical` ` Lights` |
| 21 | 🔵 | blue_circle | symbol | 0.3831 | 3.75 | +6.4 | 0.249 | ` �` ` �` `�` |
| 22 | ♻️ | recycle | symbol | 0.3627 | 3.89 | +7.2 | 0.264 | ` �` ` �` ` �` |
| 23 | 🔥 | fire | nature | 0.3540 | 3.34 | +6.1 | 0.310 | ` �` ` Delicious` `�` |
| 24 | 🌍 | earth | nature | 0.3534 | 5.10 | +12.4 | 0.206 | ` LOC` ` Muse` ` Few` |
| 25 | 🥑 | avocado | food | 0.3492 | 4.29 | +9.7 | 0.295 | ` Delicious` ` pizza` ` yummy` |
| 26 | 🚁 | helicopter | transport | 0.3346 | 3.59 | +6.7 | 0.251 | ` Vehicles` ` �` ` LOC` |
| 27 | 🤯 | mindblown | face | 0.3301 | 3.59 | +5.9 | 0.316 | ` �` ` �` ` �` |
| 28 | 🔴 | red_circle | symbol | 0.3089 | 3.85 | +6.9 | 0.218 | ` pakistan` ` �` ` �` |
| 29 | 🚀 | rocket | transport | 0.3083 | 2.94 | +5.3 | 0.295 | ` �` ` �` ` �` |
| 30 | 🛸 | ufo | transport | 0.3077 | 3.54 | +6.3 | 0.279 | ` �` ` Cute` ` �` |
| 31 | 🟢 | green_circle | symbol | 0.2993 | 3.79 | +6.6 | 0.279 | `�` `�` ` �` |
| 32 | ⚡ | lightning | nature | 0.2834 | 3.30 | +5.0 | 0.238 | ` �` ` �` ` �` |
| 33 | 🥺 | pleading | face | 0.2776 | 2.56 | +4.2 | 0.305 | ` india` ` indian` ` pakistan` |
| 34 | 🤔 | thinking | face | 0.2755 | 2.93 | +4.4 | 0.289 | ` �` ` �` ` �` |
| 35 | 🆗 | ok_button | symbol | 0.2596 | 3.51 | +5.9 | 0.232 | ` pakistan` ` Few` ` india` |
| 36 | ⬜ | white_square | symbol | 0.2565 | 3.76 | +7.5 | 0.339 | ` geometry` ` �` ` Geometry` |
| 37 | ⛵ | sailboat | transport | 0.1871 | 3.01 | +4.6 | 0.209 | ` �` ` �` ` �` |
| 38 | ⬛ | black_square | symbol | 0.1503 | 3.28 | +5.1 | 0.244 | ` �` ` �` `�` |

## B. Same stratum ranked by magnitude-controlled push (ratio to random-direction null, layer 16, alpha=0.5)

| # | glyph | id | family | ratio | z | prompt KL |
|---|---|---|---|---|---|---|
| 1 | 🍺 | beer | food | 5.74 | +14.2 | 0.4604 |
| 2 | 🍕 | pizza | food | 5.67 | +16.2 | 0.4997 |
| 3 | 🍣 | sushi | food | 5.63 | +14.3 | 0.4669 |
| 4 | 🍔 | burger | food | 5.19 | +13.3 | 0.4871 |
| 5 | 🌍 | earth | nature | 5.10 | +12.4 | 0.3534 |
| 6 | 🚗 | car | transport | 4.89 | +11.7 | 0.4684 |
| 7 | 🍜 | ramen | food | 4.85 | +12.1 | 0.4771 |
| 8 | 🌈 | rainbow | nature | 4.54 | +10.0 | 0.4532 |
| 9 | 🍎 | apple | food | 4.53 | +9.8 | 0.4078 |
| 10 | 🌸 | blossom | nature | 4.40 | +9.9 | 0.4212 |
| 11 | 🥑 | avocado | food | 4.29 | +9.7 | 0.3492 |
| 12 | 🌙 | moon | nature | 4.23 | +8.9 | 0.3861 |
| 13 | 🦋 | butterfly | animal | 4.19 | +8.5 | 0.4209 |
| 14 | 🦊 | fox | animal | 3.96 | +7.3 | 0.4303 |
| 15 | ♻️ | recycle | symbol | 3.89 | +7.2 | 0.3627 |
| 16 | 🔴 | red_circle | symbol | 3.85 | +6.9 | 0.3089 |
| 17 | 🟢 | green_circle | symbol | 3.79 | +6.6 | 0.2993 |
| 18 | 🐻 | bear | animal | 3.77 | +7.8 | 0.4451 |
| 19 | ⬜ | white_square | symbol | 3.76 | +7.5 | 0.2565 |
| 20 | 🔵 | blue_circle | symbol | 3.75 | +6.4 | 0.3831 |
| 21 | 🚂 | locomotive | transport | 3.75 | +7.0 | 0.4305 |
| 22 | 🐱 | cat | animal | 3.63 | +8.2 | 0.5470 |
| 23 | 🤯 | mindblown | face | 3.59 | +5.9 | 0.3301 |
| 24 | 🚁 | helicopter | transport | 3.59 | +6.7 | 0.3346 |
| 25 | 🌊 | wave | nature | 3.56 | +6.5 | 0.3862 |
| 26 | 🛸 | ufo | transport | 3.54 | +6.3 | 0.3077 |
| 27 | 🐶 | dog | animal | 3.52 | +7.8 | 0.5861 |
| 28 | 🆗 | ok_button | symbol | 3.51 | +5.9 | 0.2596 |
| 29 | 🦁 | lion | animal | 3.38 | +5.9 | 0.4515 |
| 30 | 🐢 | turtle | animal | 3.36 | +6.6 | 0.4573 |
| 31 | 🔥 | fire | nature | 3.34 | +6.1 | 0.3540 |
| 32 | ⚡ | lightning | nature | 3.30 | +5.0 | 0.2834 |
| 33 | ⬛ | black_square | symbol | 3.28 | +5.1 | 0.1503 |
| 34 | ⛵ | sailboat | transport | 3.01 | +4.6 | 0.1871 |
| 35 | 🚀 | rocket | transport | 2.94 | +5.3 | 0.3083 |
| 36 | 🤔 | thinking | face | 2.93 | +4.4 | 0.2755 |
| 37 | 🚲 | bicycle | transport | 2.93 | +5.2 | 0.4133 |
| 38 | 🥺 | pleading | face | 2.56 | +4.2 | 0.2776 |

## C. Token ladder — what token count alone buys

Shaded reference: the 4-token matched stratum spans 0.1503 … 0.5861 (median 0.3862).

| glyph | id | prefix tokens | prompt KL | ratio L16 | top boosted |
|---|---|---|---|---|---|
| ★ | star_outline | 2 | 0.2827 | 4.28 | ` japan` ` Japanese` ` japanese` |
| → | arrow_right | 2 | 0.1485 | 3.17 | ` wikipedia` ` list` ` List` |
| 😀 | grinning | 3 | 0.3727 | 3.37 | ` pakistan` ` indian` ` Cute` |
| ☕ | coffee | 3 | 0.3078 | 3.19 | ` Cute` ` �` ` ❤` |
| ⚠️ | warning | 5 | 0.2317 | 3.37 | ` �` ` �` `�` |
| 1️⃣ | keycap_one | 6 | 0.1675 | 3.38 | ` �` ` �` ` �` |
| 🇯🇵 | flag_jp | 7 | 0.4132 | 3.98 | ` japan` ` Japan` ` Japanese` |
| 👩‍💻 | woman_tech | 7 | 0.3734 | 3.42 | ` Software` ` Programming` ` �` |
| 🐈‍⬛ | black_cat | 8 | 0.3856 | 2.92 | ` �` ` �` ` Animals` |
| 🧑‍🚀 | astronaut | 8 | 0.3102 | 2.83 | ` �` ` �` ` �` |
| 🏳️‍🌈 | flag_rainbow | 9 | 0.4469 | 3.47 | ` Diversity` ` diversity` ` Minority` |
| 👨‍👩‍👧‍👦 | family_four | 16 | 0.3532 | 3.98 | ` Family` ` Kids` ` kids` |

## D. Layer structure

`ratio` is against the null **median**. The nonparametric column is the honest one: a cell is *0-exceed* when **none** of the 24 random directions reached that glyph's KL. The null is right-skewed (mean > median), so the `z` column elsewhere is a standardized effect size, **not** a p-value.

| layer | ratio (median) | consistency (median) | cells 0-exceed | glyphs clean on all 3 targets | 0-exceed per target |
|---|---|---|---|---|---|
| 5 | 2.22 | 0.161 | 0/150 | **0/50** | paris 0/50, planet 0/50, openended 0/50 |
| 11 | 1.82 | 0.233 | 50/150 | **0/50** | paris 0/50, planet 0/50, openended 50/50 |
| 16 | 3.76 | 0.278 | 77/150 | **0/50** | paris 0/50, planet 27/50, openended 50/50 |

**No glyph clears the null on all three targets at any layer.** The magnitude-controlled effect is clean only on the open-ended target at layers 11 and 16 (where the null is tightest), partly on `planet` at layer 16, and never on `paris`. Section B's ranking is therefore a *relative* ordering, carried mostly by the open-ended target — not a set of individually significant results.

## E. Family (token-matched stratum)

| family | n | prompt KL (median) | ratio (median) |
|---|---|---|---|
| food | 7 | 0.4669 | 5.19 |
| animal | 7 | 0.4515 | 3.63 |
| nature | 7 | 0.3861 | 4.23 |
| transport | 7 | 0.3346 | 3.54 |
| symbol | 7 | 0.2993 | 3.76 |
| face | 3 | 0.2776 | 2.93 |

## Null distributions

| cell | median | mean | sd | max |
|---|---|---|---|---|
| L5_paris_a0.5 | 0.0264 | 0.0324 | 0.0308 | 0.1422 |
| L5_planet_a0.5 | 0.0063 | 0.0141 | 0.0218 | 0.1083 |
| L5_openended_a0.5 | 0.0073 | 0.0092 | 0.0057 | 0.0311 |
| L11_paris_a0.5 | 0.0282 | 0.0399 | 0.0318 | 0.1286 |
| L11_planet_a0.5 | 0.0238 | 0.0357 | 0.0376 | 0.1734 |
| L11_openended_a0.5 | 0.0096 | 0.0112 | 0.0048 | 0.0246 |
| L16_paris_a0.5 | 0.0418 | 0.0624 | 0.0432 | 0.2160 |
| L16_planet_a0.5 | 0.0661 | 0.0904 | 0.0519 | 0.2179 |
| L16_openended_a0.5 | 0.0383 | 0.0397 | 0.0079 | 0.0534 |

---

The random-direction null is a **size** control, not a semantic control. Beating it shows a direction is structured; it does not show the structure is meaning. No causal or semantic claim is authorized by this screen.
