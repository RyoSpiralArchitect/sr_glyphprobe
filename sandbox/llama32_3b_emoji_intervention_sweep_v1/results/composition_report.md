# Emoji composition — what happens when two glyphs are stuck together (out of contract)

Chases the puzzle left by [the why-flat follow-up](whyflat_report.md): 🐈 (3.96) and 🐱 (3.95) engage the middle of the network, the ZWJ compound 🐈‍⬛ (3.09) does not, and its direction stays cat-shaped anyway. Three runs, one pre-registered. See [README](../README.md) for the boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.

## Summary

| question | answer | confidence |
|---|---|---|
| is the ZWJ joiner the cause? | **no** — removing it does not restore the strong component's value | solid, 3 families |
| does the composite follow its LAST component? | **no** — order shifts the value but does not set it | solid |
| does the order effect scale with the component gap? | **no relationship exists** — Spearman +0.04 on one set, **−0.94** on another | solid (as a negative) |
| what sets the composite? | **the mean of the two components** | pre-registered test passed, n = 6 |
| does the direction move with the order? | **barely** — cosine shifts stay under 0.09 while efficacy moves up to 0.94 | solid, 26 cases |

## 1 — the ZWJ joiner is not the cause

🐈‍⬛ tokenises exactly as 🐈's tokens + a ZWJ token + ⬛'s tokens, verified at run time, so the joiner can be removed and the order reversed independently.

| construction | join | order | mid-network ratio |
|---|---|---|---|
| 🐈 `cat` | - | 🐈 alone | **3.96** |
| 🐈‍⬛ `cat_ZWJ_sq` | zwj | 🐈 then ⬛ | **3.09** |
| 🐈⬛ `cat_sq` | concat | 🐈 then ⬛ | **3.31** |
| ⬛🐈 `sq_cat` | concat | ⬛ then 🐈 | **3.61** |
| ⬛‍🐈 `sq_ZWJ_cat` | zwj | ⬛ then 🐈 | **3.52** |
| ⬛ `black_sq` | - | ⬛ alone | **3.00** |

At a fixed order the joiner moves the value by **0.006 to 0.215** — the same magnitude as order effects this report treats as signal, so it is not nothing. The apparent "exactly equal" in the tech family (3.39 vs 3.39) is a 2-dp display artefact; the values are 3.3933 and 3.3870. What the data supports is narrower and still decisive for the question asked: removing the joiner leaves 🐈⬛ at 3.31, nowhere near 🐈's 3.96, so **the joiner cannot be what costs the compound its efficacy**.

## 2 — order shifts the value, but no rule predicts by how much

Seven families, both orders, bare concatenation, ordered by component gap:

| family | strong | weak | gap | ends weak | ends strong | order effect |
|---|---|---|---|---|---|---|
| twin | cat 3.96 | cat_face 3.95 | 0.01 | 4.49 | 4.50 | **+0.02** |
| astro | person 2.86 | rocket 2.73 | 0.13 | 2.87 | 2.88 | **+0.00** |
| pizcar | car 5.66 | pizza 5.32 | 0.34 | 4.38 | 4.95 | **+0.57** |
| catsq | cat 3.96 | black_sq 3.00 | 0.96 | 3.31 | 3.61 | **+0.31** |
| tech | woman 4.28 | laptop 3.16 | 1.12 | 3.39 | 3.49 | **+0.11** |
| pizsq | pizza 5.32 | black_sq 3.00 | 2.31 | 4.94 | 4.00 | **-0.94** |
| carlap | car 5.66 | laptop 3.16 | 2.50 | 4.16 | 4.36 | **+0.20** |

Ending on the stronger component scores higher in **6/7** of these families — but in only **2/6** of the six later ones, measured on the same protocol with the same sign convention. Pooled that is **8/13 against 6.5 expected by chance**. *Neither the size nor the sign of the order effect is consistent across samples.* Both are reported here as negative results:

- Spearman(gap, order effect) on these 7 families = **+0.036**
- the same statistic on the 6 *later* families = **-0.943**

**The sign of that correlation flips between two sets measured on the identical protocol.** A quantity that reads +0.04 on one sample and −0.94 on another is not a relationship; it is small-sample noise. This is recorded as a negative result — and as a warning about every other n≈6 Spearman in this directory, including the one below that passed.

> This is the second time the same mistake was caught here. The 'order effect grows with the gap' idea was originally read off **two** families (+0.30 and +0.01), stated, and then dissolved at n=7. The flip to −0.94 at n=6 confirms the retraction was right.

For completeness, the run built to test "follows the last component" reported **7/9** composites landing nearest their last part — the observation that suggested H-LAST. Section 3 explains that pattern without needing it.

## 3 — the composite tracks the MEAN of its components (pre-registered)

Re-analysing the 7 families for what *did* predict the composite gave `composite = 0.70 × mean(components) + 1.16` (Spearman +0.821, leave-one-out +0.714…+0.886, permutation p = 0.017). Post-hoc — so it was written into [`PREREGISTRATION_mean_rule.md`](../PREREGISTRATION_mean_rule.md) with its predictions and a two-part decision rule, and committed **before** the test script existed. The runner re-derives the six predictions and aborts if they disagree with that file.

| family | components | mean | predicted | observed | error |
|---|---|---|---|---|---|
| dogtea | dog + tea | 4.15 | **4.07** | 4.22 | +0.15 |
| sailthink | sailboat + thinking | 2.75 | **3.09** | 3.15 | +0.06 |
| cryheli | crying + helicopter | 3.88 | **3.88** | 4.60 | +0.72 |
| shipcof | ship + coffee | 3.29 | **3.47** | 3.86 | +0.40 |
| teacar | tea + car | 5.12 | **4.75** | 4.83 | +0.08 |
| anchorair | anchor + airplane | 3.02 | **3.27** | 2.84 | -0.43 |

| criterion | required | observed | |
|---|---|---|---|
| Spearman(predicted, observed) | ≥ 0.7 | **+0.886** | PASS |
| mean absolute error | ≤ 0.72 | **0.308** | PASS |

**Pre-registered verdict: SUPPORTED.**

Frame check: all 11 solo components reproduced their earlier values. Note the resolution — the prior values are stored to 2 dp, so any successful reproduction is bounded below 0.005 **by construction**. This check detects drift *larger* than that; it is not a 4-dp agreement.

This also answers the original puzzle. 🐈‍⬛ is weak because 🐈 (3.96) and ⬛ (3.00) average to 3.48 and the rule compresses toward the middle — not because of the joiner, and not because ⬛ comes last.

## 4 — direction and efficacy are independent

Cosines are taken against **named** components, never positional labels. (The first version of this analysis compared cos-to-first against cos-to-last; those labels swap with the order, so the column flipped even when the geometry did not. That bug is why this is stated carefully.)

| run | cases | max \|cosine shift\| | max \|efficacy shift\| |
|---|---|---|---|
| catchase v2 | 14 | 0.074 | 0.94 |
| meanrule v1 | 12 | 0.090 | 0.69 |

Reversing a pair moves the direction by at most 0.09 in cosine while moving the efficacy by up to 0.94, on a scale where the solo components span 2.73…5.66. **Two glyph strings can have near-identical residual directions and substantially different causal push.** Cosine similarity to a known direction is not evidence about that direction's effect.

## 5 — where the mean rule misses

Composite minus the mean of its components, on the fitting set:

| family | composite − component mean |
|---|---|
| twin (cat + cat_face) | +0.54 |
| astro (person + rocket) | +0.08 |
| pizcar (pizza + car) | -0.83 |
| catsq (cat + black_sq) | -0.02 |
| tech (woman + laptop) | -0.28 |
| pizsq (pizza + black_sq) | +0.31 |
| carlap (car + laptop) | -0.15 |

The two extremes are suggestive and **untested**: the twin pair 🐈🐱 (two names for the same concept) sits **above** the mean, and 🍕🚗 (two strong, unrelated concepts) sits furthest **below** it. "Alike composes additively, strong-and-different interferes" is a hypothesis this data generated, not one it tested.

## Limitations

- 13 families total, all two-component, all chosen by me; the confirmatory set shares its protocol and its author with the fitting set, so this is a replication inside one sandbox, not an independent one.
- n≈6 Spearman is demonstrably unstable here — the order-effect correlation flipped sign between sets. The mean rule passed a pre-registered test, but it carries the same sample-size fragility and should not be treated as established.
- One model, one position (`last_nonpad`), one site (`resid_post`), one strength (alpha 0.5), three injection targets.
- The random-direction null is a **size** control, not a semantic control.
- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are byte-identical to the sealed v2 artifact; nothing else here is comparable to a canonical run.
