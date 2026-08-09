# Per-glyph emoji intervention in Llama-3.2-3B: what survived twelve runs

**Status: out of contract.** Exploratory sandbox work on the real bf16 weights.
Not the sealed v2 experiment; it touches nothing in `artifacts/`, `validation/`,
`data/manifests/`, `runs/` or the sealed receipts, uses no holdout bank, and
authorises no causal or semantic claim (`pre-causal-activation-screen`,
`causal_claim_authorized: false`). Weights are byte-identical to the sealed v2
artifact (`manifest_sha256 dc5b61a2…`); library versions are not the frozen set,
so no receipt here is comparable to a canonical run.

[日本語版](FINDINGS.ja.md) · [README](README.md) · reports:
[sweep](results/report.md) · [deep](results/deep_report.md) ·
[why-flat](results/whyflat_report.md) · [composition](results/composition_report.md) ·
[order](results/order_report.md) · [n=30](results/meanrule30_report.md)

---

## 1. Question and measure

Taking each emoji **one at a time**: how much does it move the model, and is
that about the *emoji* or about *token count*?

Two quantities, deliberately answering different things.

**A — prompt-level effect.** `KL( p(next | W) ‖ p(next | "<g>\n" + W) )`,
averaged over wrapper contexts `W`. "Put this glyph in front of a sentence; how
far does the next-token distribution move?" Large dynamic range, but confounded
by token count and token rarity.

**B — magnitude-controlled push.** Extract the glyph's residual direction,
renormalise **every** glyph to the same RMS, inject into held-out prompts:

```
direction   d_g(L) = mean_i [ resid_post(L, "<g>\n<W_i>") − resid_post(L, "<W_i>") ]
injection   v      = d_g(L) / rms(d_g(L)) · α · rms(a_target(L))     (activation_add)
score       KL(baseline ‖ intervened),  reported as a ratio to a matched
            random-direction null
```

B is the honest form of "how much does this glyph intervene": because every
direction is rescaled to `α · rms(target activation)` before injection, a glyph
with a large raw direction gets no free advantage. All metrics come from the
project's own `glyphprobe.analysis.metrics`, i.e. the same code path as the
sealed work.

**Operating point.** α = 0.5, chosen from a dose probe: KL scales as α² in the
linear regime, so the glyph/null *ratio* is α-invariant there; α = 2.0 flips
argmax on 6/6 probe glyphs (the computation breaks), α = 0.5 flips **0** of 300
factual-target cells. `mid` = the maximum ratio over layers 10–19.

**Measurement gates, all passed.** Zero-hook is an exact no-op (KL identically
0.0 in every cell); dose monotonicity 100 % of glyph × layer cells; RMS matching
to 2.2 × 10⁻¹⁶ over 1,350 injections; the model receives exactly the intended
perturbation (`actual/intended RMS` = 1.000000, `cos(actual, intended)` =
1.000000).

---

## 2. What survived

### 2.1 Token count does not explain intervention magnitude

| relationship | Spearman ρ |
|---|---|
| prefix token count vs prompt-level effect (50 glyphs) | **+0.06** |
| prefix token count vs magnitude-controlled push (50 glyphs) | **−0.08** |

The panel was built as two strata: 38 glyphs costing **exactly 4 prefix tokens**
each, and a ladder spanning **2–16** tokens. The 2-token `★` and the 16-token
👨‍👩‍👧‍👦 land inside the same band as the matched stratum. Within the matched
stratum the prompt-level effect still spans **3.9×** (🐶 0.586 → ⬛ 0.150) with
token count held exactly constant.

This is a stronger control than the `wrapper_tokenization_control` HOLD carried
by the sealed work, and it is the most robust result here: it rests on 50 glyphs
and does not depend on the null at all.

### 2.2 Direction similarity and causal efficacy are independent

Across **26 composite cases**, reversing the order of a two-glyph string moves
the fixed-frame cosine to a named component by at most **0.09**, while moving
the efficacy by up to **0.94** — on a scale where solo components span 2.73–5.66.

| run | cases | max \|cosine shift\| | max \|efficacy shift\| |
|---|---|---|---|
| catchase v2 | 14 | 0.074 | 0.94 |
| meanrule v1 | 12 | 0.090 | 0.69 |

**Two glyph strings can have near-identical residual directions and
substantially different causal push.** Cosine similarity to a known direction is
not evidence about that direction's effect. This is the finding with the most
cases behind it and the one I would defend hardest.

### 2.3 The ZWJ joiner is not what costs a compound its efficacy

🐈‍⬛ tokenises **exactly** as 🐈's tokens + a ZWJ token + ⬛'s tokens (asserted at
run time; the runners exit 2 otherwise), so the joiner can be removed and the
order reversed independently.

| | joined | bare | difference |
|---|---|---|---|
| 👩 then 💻 | 3.3933 | 3.3870 | 0.006 |
| 🐈 then ⬛ | 3.090 | 3.305 | 0.215 |
| ⬛ then 🐈 | 3.516 | 3.615 | 0.099 |

Removing the joiner leaves 🐈⬛ at 3.31, nowhere near 🐈's 3.96. The joiner is
*not* nothing — 0.006 to 0.215 is the same magnitude as order effects treated as
signal elsewhere — but it cannot be the cause.

### 2.4 A composite tracks the mean of its components (pre-registered)

Found **post-hoc** while re-analysing a failed hypothesis, so it was written
into [`PREREGISTRATION_mean_rule.md`](PREREGISTRATION_mean_rule.md) with six
predictions and a two-part decision rule and committed **before the test script
existed** (`65e0307`: one file, no script, no data). The runner re-derives the
predictions, thresholds and rule coefficients at start-up and aborts on any
mismatch.

```
composite_mid ≈ 0.70 · mean(component_mid) + 1.16
```

| criterion | required | observed | |
|---|---|---|---|
| Spearman(predicted, observed) | ≥ 0.70 | **+0.886** | PASS |
| mean absolute error | ≤ 0.72 | **0.308** | PASS |

All 11 solo components reproduced their earlier values (resolution note: priors
are stored to 2 dp, so a successful reproduction is bounded below 0.005 *by
construction*). This also answers the puzzle that started the chase: **🐈‍⬛ is
weak because 🐈 (3.96) and ⬛ (3.00) average to 3.48** — not the joiner, not the
order.

**Re-tested at n = 30** on 30 pairs drawn by a seeded sampler from the
repository's own `e2_core35` panels — a pool I did not choose, every glyph
exactly 4 prefix tokens — with the coefficients still frozen
([report](results/meanrule30_report.md),
[pre-registration](PREREGISTRATION_mean_rule_n30.md)):

| | n = 6 | n = 30 |
|---|---|---|
| Spearman | +0.886 | **+0.784** (PASS) |
| MAE | 0.308 | 0.409 (PASS) |
| bootstrap 95 % CI | not supportable | **[+0.550, +0.907]** |
| permutation p | — | **0.0001** |

The interval is the quantity §5.1 said n ≈ 6 could not produce. It excludes zero
comfortably — **the ordering is real** — but its lower bound sits *below* the
0.70 pass threshold, and refitting gives `0.62 × mean + 1.86` against the frozen
`0.70 / 1.16`, with the rule under-predicting on **26 of 30** pairs. **Quote it as an ordering,
not as a predictor of magnitude.**

And read "SUPPORTED" narrowly: `pred` is a strictly increasing affine map of
`mean`, so `Spearman(pred, obs)` is *identical* for any positive slope and any
intercept (verified: 0.70/1.16, 1.0/0.0 and 0.31/99.0 all give +0.784205). That
leg tests **"the mean of the component scores ranks the composites"**, not the
fitted rule. Only the MAE leg touches the coefficients — and it is the leg that
degrades out of sample.

### 2.5 Injected directions boost recognisable tokens

Qualitative, and the most immediately legible result. Injecting a glyph's
direction into `The capital of France is`:

| glyph | top boosted tokens |
|---|---|
| 🍕 | `' yummy'` `' delicious'` `' pizza'` |
| 🚗 | `' Automobile'` `' Vehicles'` `' cars'` |
| 🐶 🐱 🐻 🐢 | `' Animals'` `' Animal'` `' animals'` |
| 🇯🇵 | `' japan'` `' Japan'` `' Japanese'` |
| 👩‍💻 | `' Software'` `' Programming'` |
| 🏳️‍🌈 | `' Diversity'` `' Minority'` |
| 👨‍👩‍👧‍👦 | `' Family'` `' Kids'` |

A second pattern: for many glyphs (🔥 🌊 ⚡ 🚀 🚂 🤯) the top boosted ids are
**partial-UTF-8 emoji byte fragments** — the direction partly carries "emit an
emoji" rather than "emit this concept".

The direction carries a **category, not an instance**: with hand-written probe
words (not harvested from the model's own outputs), the own probe group wins for
only **4/13** glyphs but the own *category block* wins for **10/13**. 🍣 boosts
*burger* words (+2.95) more than *sushi* words (+1.86).

**This is a description of what the screen produced, not a semantic claim.** The
random-direction null is a **size** control, not a semantic control: beating it
shows a direction is structured, not that the structure is meaning.

---

## 3. What did not survive

Seven claims were stated and then retracted. Three were caught by adversarial
review, four by my own follow-up measurements.

| claim | how it died |
|---|---|
| "every glyph beats the random null" | true of the null *median*; nonparametrically **no glyph clears all three targets at any layer** |
| "the layer profile splits the panel with no exceptions" | property of a 13-glyph panel with no intermediate cases; across 19 glyphs the mid ratio is a **continuum** (2.71 → 5.66, largest gap 0.73) |
| "the direction follows the last component" | an artefact of comparing cos-to-*first* against cos-to-*last*: those labels swap with the order, so the column flipped when the geometry did not |
| "the order effect scales with the component gap" | read off **two** families; Spearman **+0.04** at n = 7, **−0.94** at n = 6 |
| "the order effect's sign is consistent (6/7)" | the confirmatory set was **2/6** the other way; 8/13 pooled against 6.5 expected by chance. **Superseded at n = 30 — see below** |
| "joined and bare score the same (3.39 vs 3.39)" | a 2-dp display artefact; the values are 3.3933 and 3.3870 |
| "the non-food controls flip — indistinguishable from the foods" | a per-condition strong/weak convention had mirrored three cells; under a fixed convention **both controls are stable** |

**One retraction was itself too agnostic.** At n = 30 the order effect is not
absent — it runs the *opposite* way to the original claim: **8/30 pairs positive**
where chance is 15 (binomial two-sided **p = 0.016**), median **−0.32**. Ending on
the *stronger* component scores **lower**. The 6/7 claim deserved retraction and
the 8/13 pooled reading was the right call on the evidence then; with five times
the units the effect reappears with the sign flipped. This is a new
single-sample finding at exactly the evidential level the 6/7 claim once had, and
it needs its own replication before it is more than that.

A confound found late and disclosed rather than buried: **UTF-8 byte class**
correlates with the prompt-level ranking (Spearman **−0.55**, and **−0.48**
*within* the token-matched stratum, so it is not token count). Every 3-byte
U+26xx/U+2Bxx glyph in the why-flat panel sits in the bottom half. Being 3-byte
looks sufficient but not necessary for a weak effect; the likeliest reading is
that byte class is a proxy for abstractness, and the near-synonym pairs
(⛵/🚢 1.35×, ☕/🍵 1.60×, ✈️/🚁 1.16×, ⬛/🟥 0.99×) argue that is not the whole
story — but four loose synonyms is thin evidence.

---

## 4. Discussion

**The order effect is real per pair and empty as a rule.** 🍕⬛ holds a negative
order effect across four independent conditions (two disjoint wrapper sets × two
disjoint target sets) and 🍔⬛ agrees. But 🍣⬛ is stable in the *opposite*
direction, 🍜⬛ and 🍺⬛ flip, and the non-food controls 🐶⬛ and 🌈⬛ are *both*
stable. So an individual pair can carry a reproducible preference that follows
neither the component gap, nor semantic category, nor other members of its own
category. Only the sign is ever preserved — 🍕⬛ ranges −1.09 to −0.03 across
conditions. **What is stable is not what is explicable.**

**Detectability belongs to the target, not the glyph.**
`Spearman(baseline entropy of the injection prompt, number of glyphs clearing
the null) = +0.70`. Sharp factual prompts (` Paris`, ` Jupiter`) hide the effect
because a *random* push also moves them a lot; the null is wide there
(sd 0.043) and narrow on open-ended prompts (sd 0.008). Reporting a result on
one prompt therefore says as much about the prompt as about the glyph — which is
exactly the trap the first sweep fell into.

**Significance and effect size come apart.** The weak controls clear the null on
6–7 of 12 targets, the same as 🍕 and 🍺. The binary test saturates; the ordering
lives in the ratio. Reporting "p < 0.05 on N cells" would have been true and
uninformative.

**Depth structure.** Emoji directions push hardest at **L14–L16** and the effect
falls to near-parity by the final layer for semantically rich glyphs. At **L0
every glyph sits at ratio 0.05** — a real emoji direction is ~20× *less*
disruptive than a matched random one at the embedding layer, presumably because
it lies on the token-embedding manifold the model handles gracefully. Direction
consistency across contexts runs the other way (0.93 at L0 → 0.43 at L27):
**where the direction is most reproducible it does the least.** A high ratio at
the last layer means only that the direction is *token-like*; a bump at L14–16
means it engages remaining computation. Notably, the sibling OOC screen found
**L11** best for fingerprint *separation* while L11 is the *weakest* depth for
causal push — separability and efficacy do not rank layers the same way.

**Composition compresses.** The fitted rule has slope 0.70 < 1, so composites
are pulled toward the middle. Residuals are suggestive and untested: the twin
pair 🐈🐱 (two names for one concept) sits **+0.54 above** the line, 🍕🚗 (two
strong unrelated concepts) **−0.83 below**. "Alike composes additively,
strong-and-different interferes" is a hypothesis this data *generated*.

---

## 5. Methodological lessons

These cost the most and generalise furthest.

1. **n ≈ 6 Spearman is not a measurement.** The same statistic on the same
   protocol read +0.04 and −0.94 on two samples. Any rank correlation over
   fewer than ~10 units in this setting should be treated as a hypothesis
   generator only — including the mean rule that *passed* its pre-registered
   test. **Confirmed constructively at n = 30**: the *ordering* claim survives
   with a bootstrap CI of [+0.55, +0.91], and the order effect — which read 6/7 then
   2/6 — resolves to 8/30 with the sign reversed. Small samples here did not
   merely add noise; they got the direction wrong.
2. **A clean binary split is usually a panel property.** "No exceptions" held
   over 13 glyphs and dissolved at 19. Before claiming a dichotomy, add the
   cases that would sit between the groups.
3. **Check the metric before the mechanism.** Two conclusions were reversed by
   metric bugs — a label that swapped with the condition, and a strong/weak
   assignment re-decided inside a loop — not by the data. Both produced
   plausible, publishable-looking patterns.
4. **Verify a phenomenon exists before explaining it.** The stability test on
   🍕⬛ was designed to make the anomaly disappear; it survived, which is the
   only reason chasing it was justified. Three earlier "explanations" were
   fitted to patterns that later evaporated.
5. **Pre-register when the hypothesis is post-hoc, and pin the thresholds too.**
   The first version of the guard checked the predicted *values* but not the
   pass/fail *thresholds* — i.e. the half that decides the outcome was editable
   after seeing the result.
6. **Re-seeding a shared denominator is not an independent sample.** The null
   enters as a denominator both orders share, so re-seeding rescales an order
   effect without moving its sign. Vary what actually carries sampling
   variability: the direction estimate and the readout.

---

## 6. Limitations

- One model (Llama-3.2-3B bf16), one site (`resid_post`), one position
  (`last_nonpad`), one primary strength (α = 0.5).
- All panels were assembled by me; the confirmatory sets share protocol and
  author with the exploratory ones. This is replication inside one sandbox, not
  independent replication.
- 13 composition families and 9 order pairs, all two-component. "Stable across
  four conditions" is a weak bar: with a genuinely 50/50 sign, one pair in eight
  looks stable by chance, and nine were tested.
- The random-direction null is a size control, not a semantic control.
- Non-canonical provenance: non-frozen library versions and an `orjson`
  stand-in, so receipt hashes here are not comparable to canonical runs.
- Numerics note: numpy on macOS/Accelerate raises spurious
  `divide by zero / overflow / invalid value encountered in matmul` warnings on
  large float64 dot products. Verified spurious — all activations and logits are
  finite and `a @ b` is bit-identical to pure-Python summation.

## 7. What a next study should do

- **Independent replication**: a second model, and panels chosen by someone
  other than the analyst.
- ~~**More units per statistic**~~ — done: 30 pairs, see
  [`results/meanrule30_report.md`](results/meanrule30_report.md). Next: the
  calibration failure (slope 0.70 → 0.62 refit) needs its own study.
- **Token-position resolution**: extract the direction at each token position of
  a compound rather than only at the wrapper's `last_nonpad`, to locate where
  composition costs efficacy.
- **Causal follow-through**: everything here is a pre-causal activation screen.
  The mid-network peak at L14–16 is where a real causal test (path patching,
  head/MLP attribution) would go.
