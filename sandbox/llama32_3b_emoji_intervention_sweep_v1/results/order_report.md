# Chasing the one reversed family — and not finding a rule (out of contract)

[The composition report](composition_report.md) left one family running the wrong way: 🍕⬛ scored 4.94 and ⬛🍕 scored 4.00, an order effect of **−0.94** where six of the other seven families were positive. The obvious move is to explain it. These two runs check first whether there is anything to explain, and then whether it generalises. See [README](../README.md) for the boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.

## Method — why not re-seed the null

The injection KL is fully deterministic; the null only enters as a denominator that **both orders of a pair share** at a given (layer, target). Re-seeding therefore rescales an order effect but can barely move its sign — it is not an independent sample. The two places genuine sampling variability enters are the direction estimate and the readout, so those are varied instead:

| | set A | set B |
|---|---|---|
| extraction wrappers | 'Today I saw a', 'My favorite thing is', 'Here we have', 'This reminds me of' | 'Look at this', 'I just found a', 'There was a', 'Everyone loves a' |
| injection targets | 'The capital of France is', 'The largest planet in our solar system is', 'I am thinking about' | 'The best thing about summer is', 'Let me tell you about', 'The chemical symbol for gold is' |

2 × 2 = four independent estimates of each order effect, at layers 10-19 (`mid` is the max over exactly that band).

## Panel 1 — does the 🍕⬛ sign survive?

*Stated before the run: the sign will NOT be stable.*

| pair | strong | weak | WA/TA | WA/TB | WB/TA | WB/TB | positive | sign |
|---|---|---|---|---|---|---|---|---|
| 🍕⬛ `pizsq` | pizza | black_sq | -0.94 | -1.09 | -0.70 | -0.03 | 0/4 | **STABLE** |
| 🍔⬛ `bursq` | burger | black_sq | -0.35 | -0.11 | -0.20 | -0.35 | 0/4 | **STABLE** |
| 🚗⬛ `carsq` | car | black_sq | -0.02 | +0.51 | +0.64 | +0.03 | 3/4 | flips |
| 🍕⬜ `pizwht` | pizza | white_sq | -0.35 | -0.45 | -0.52 | +0.46 | 1/4 | flips |

Sign stable across all four conditions: **2/4**.

## Panel 2 — is "food + black square" a type?

*Stated before the run: if it is a type, all three new foods should be negative like 🍕⬛ and 🍔⬛, and the two non-food controls should not.*

| pair | strong | weak | WA/TA | WA/TB | WB/TA | WB/TB | positive | sign |
|---|---|---|---|---|---|---|---|---|
| 🍣⬛ `sussq` | sushi | black_sq | +0.70 | +1.28 | +0.16 | +1.02 | 4/4 | **STABLE** |
| 🍜⬛ `ramsq` | ramen | black_sq ⚠ | +0.48 | +0.04 | +0.34 | -0.11 | 3/4 | flips |
| 🍺⬛ `beesq` | beer | black_sq | +0.01 | -0.46 | -0.29 | -0.67 | 1/4 | flips |
| 🐶⬛ `dogsq` | dog | black_sq ⚠ | +0.17 | +0.43 | +0.09 | +1.07 | 4/4 | **STABLE** |
| 🌈⬛ `rainsq` | rainbow | black_sq ⚠ | +0.07 | +0.38 | +0.13 | +1.13 | 4/4 | **STABLE** |

⚠ = the two components swap rank in `ramsq` (WB/TA), `dogsq` (WB/TA), `rainsq` (WB/TA). A positive order effect always means *ends on the component that is stronger in the first condition*; the runner originally re-decided this per condition, which mirrored those cells. Everything here uses the fixed convention.

Sign stable across all four conditions: **3/5**.

## What the two panels say together

**Panel 1 refuted my prediction.** 🍕⬛ holds its sign in all four conditions (0/4 positive) and 🍔⬛ agrees (0/4). 2 of 4 pairs are sign-stable, so the anomaly is not one draw from a noisy quantity — there is something there.

**Panel 2 refuted the type.** The three foods do not agree with each other: `sussq` 4/4, `ramsq` 3/4, `beesq` 1/4. And the two non-food controls are `dogsq` 4/4, `rainsq` 4/4 — both sign-stable, i.e. the controls behave at least as consistently as the foods do. Whatever 🍕⬛ and 🍔⬛ have, **food does not predict it**.

Put together: an individual pair can carry a reproducible order preference, but it follows neither the component gap, nor semantic category, nor other members of its own category — and non-food pairs are just as capable of being stable. **No general rule survives.** The magnitude is not stable either — 🍕⬛ ranges -1.09 to -0.03 (spread 1.06); only the sign is preserved.

> **Correction.** The first version of this report said the non-food controls "flip at 3/4 — indistinguishable from the foods". That came from a runner that re-decided which component was *strong* inside the condition loop; ⬛ outranks its partner in `WB/TA` but not elsewhere, so those cells were measured in a mirrored frame. Under one fixed convention the controls are sign-stable, not flipping. The conclusion that food is not the type is unchanged — the reason is different.

## Scale caveat

The absolute mid ratios move a lot with the target set — 🍕 reads 5.32 / 6.76 / 4.54 / 6.17 across the four conditions. Mid ratios are comparable **within** a condition only. Order effects are within-condition differences, which cancels most of that, and is why they are the quantity reported here.

## Limitations

- Nine pairs across two panels, all two-component, all chosen by me; four conditions that share one model, one layer band, one strength and one site.
- "Stable across four conditions" is a weak bar: with a genuinely 50/50 sign, one pair in eight would look stable by chance, and nine pairs were tested.
- The pairs that are stable have no explanation here. Recording that they reproduce is not the same as knowing why.
- The random-direction null is a **size** control, not a semantic control.
- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are byte-identical to the sealed v2 artifact; nothing else here is comparable to a canonical run.
