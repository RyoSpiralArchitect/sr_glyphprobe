# Llama-3.2-3B — per-glyph emoji intervention sweep (v1)

[日本語](README.ja.md) · [Scientific contract](../../docs/SCIENTIFIC_CONTRACT.md) · [Sealed v2 protocol](../../docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md) · [Sibling OOC screen](../llama32_3b_bf16_ooc_screen_v1/README.md)

> ## ⚠️ OUT OF CONTRACT — this is NOT the sealed v2 experiment
> Everything in this directory is an **exploratory, out-of-contract** run,
> deliberately quarantined under `sandbox/`. It touches nothing in `artifacts/`,
> `validation/`, `data/manifests/`, `runs/`, or the sealed v2 receipts, and it does
> **not** update, confirm, weaken, or reinterpret
> `glyphprobe-e2-llama32-3b-mps-emoji-transport-v2`. It uses no holdout bank
> (neither P2 nor C1); the panel is assembled from public, already-explored glyphs.

## The question

Take each emoji **one at a time** and ask how much it actually moves the model —
then find out whether the answer is about the *emoji* or merely about *token count*.

Two quantities are measured per glyph, and they deliberately answer different things.

| | what it asks | how |
|---|---|---|
| **A. prompt-level effect** | "put this emoji in front of a sentence — how far does the next-token distribution move?" | `KL( p(next \| W) ‖ p(next \| "<g>\n"+W) )`, averaged over 4 wrappers |
| **B. magnitude-controlled push** | "…and is that because its direction is *special*, or just *big*?" | extract the glyph's residual direction, renormalise every glyph to the **same** RMS, inject it into held-out prompts, measure KL |

**B** is the honest version of "介入量": because every direction is rescaled to
`alpha × rms(target activation)` before injection, a glyph with a large raw
direction gets no free advantage. The score reported is the ratio to a
**matched random-direction null** — above 1.0 means the direction beats a random
direction of exactly the same size.

## Method

```
direction   d_g(L) = mean_i [ resid_post(L, "<g>\n<W_i>") − resid_post(L, "<W_i>") ]
            over 4 extraction wrappers, at last_nonpad
injection   v = d_g(L) / rms(d_g(L)) · alpha · rms(a_target(L))     (activation_add)
score       KL(baseline ‖ intervened) over the next-token distribution
```

- **Extraction wrappers** (4): `Today I saw a` · `My favorite thing is` · `Here we have` · `This reminds me of`
- **Injection targets** (3, disjoint from the wrappers): `The capital of France is` (top-1 ` Paris`) · `The largest planet in our solar system is` (` Jupiter`) · `I am thinking about` (` the`)
- **Layers** `[5, 11, 16]` · **strengths** `alpha ∈ {0.1, 0.5, 1.0}` (primary `0.5`) · **24 random-direction controls** per (layer, target, alpha)
- **Panel**: 50 glyphs in two strata — `matched` (38 glyphs, **every one costing exactly 4 prefix tokens**, recomputed against *every* extraction wrapper at run time; the runner aborts rather than emit an unmatched stratum) and `ladder` (12 glyphs spanning **2…16** prefix tokens)
- 2,157 records, 359 s on an M4 (MPS / FP32)

All metrics come from the project's own `glyphprobe.analysis.metrics`
(`distribution_metrics`, `activation_delta_metrics`), so they are computed by the
same code as the sealed work.

### Measurement gates (all pass)

| gate | result |
|---|---|
| zero-hook is an exact no-op | KL **exactly 0.0** in all 9 (layer × target) cells |
| KL dose monotonicity | **100%** of glyph × layer cells strictly increasing over `alpha` |
| RMS strength matching | max \|actual − requested\| = **2.2e-16** over all 1,350 injections |
| the model received exactly the intended perturbation | `actual/intended RMS` = **1.000000** (min = max) and `cos(actual, intended)` = **1.000000** |
| panel token counts | all 50 match the surveyed values |
| the primary strength perturbs without breaking the computation | **0 top-1 flips** in the 300 factual-target cells at `alpha = 0.5` (` Paris` and ` Jupiter` always preserved) |

The only `alpha = 0.5` flips (44) are on the open-ended target at layer 16, whose
baseline top-2 margin is just 0.49 logits — a near-tie between ` the` and ` a` /
` making`, not a broken computation. At `alpha = 1.0` the factual targets do start
to flip, which is why `0.5` is the primary operating point.

## Results

### 1. Token count does **not** explain the ranking

This is the headline. The tokenization confound that `HOLD`s elsewhere in this
project is simply not what is driving these numbers:

| correlation | Spearman ρ |
|---|---|
| prefix token count vs prompt-level effect (all 50) | **+0.06** |
| prefix token count vs magnitude-controlled push (all 50) | **−0.08** |

The 2-token `★` and the 16-token 👨‍👩‍👧‍👦 land inside the same band as the
4-token stratum. Whatever is being measured, it is not "more tokens".

### 2. Ranking — prompt-level effect (38 token-matched glyphs)

| rank | glyph | prompt KL | | rank | glyph | prompt KL |
|---|---|---|---|---|---|---|
| 1 | 🐶 dog | **0.586** | | 34 | 🤔 thinking | 0.276 |
| 2 | 🐱 cat | 0.547 | | 35 | 🆗 ok_button | 0.260 |
| 3 | 🍕 pizza | 0.500 | | 36 | ⬜ white_square | 0.257 |
| 4 | 🍔 burger | 0.487 | | 37 | ⛵ sailboat | 0.187 |
| 5 | 🍜 ramen | 0.477 | | 38 | ⬛ black_square | **0.150** |

Median 0.386. Animals and food occupy the top; featureless geometric symbols the
bottom — a ~3.9× spread with token count held exactly constant.

### 3. Ranking — magnitude-controlled push (ratio to random-direction null, L16)

| rank | glyph | ratio | z |
|---|---|---|---|
| 1 | 🍺 beer | **5.74** | +14.2 |
| 2 | 🍕 pizza | 5.67 | +16.2 |
| 3 | 🍣 sushi | 5.63 | +14.3 |
| 4 | 🍔 burger | 5.19 | +13.3 |
| 5 | 🌍 earth | 5.10 | +12.4 |
| … | | | |
| 27 | 🐶 dog | 3.52 | +7.8 |
| 38 | 🥺 pleading | 2.56 | +4.2 |

**Food sweeps the top five when size is controlled for.** The two rankings agree
only moderately (ρ = **+0.55**): 🐶 and 🐱 dominate the prompt-level ranking but
sit mid-pack here — they move the model a lot, yet their directions are not
unusually *efficient*. Food directions punch well above their weight.

> ⚠️ **Read this ranking as relative, not as a set of significant results.** The
> ratio is against the null *median*, and the null is right-skewed. The
> nonparametric check (below) shows the effect is only clean on one of the three
> targets — and the `z` column is a standardized effect size against a
> non-Gaussian null, **not** a p-value.

### 4. Layer structure, and how much of §3 actually clears the null

A cell is *0-exceed* when **none** of the 24 random directions reached that
glyph's KL — the only assumption-free statement available here.

| layer | ratio (median) | consistency | cells 0-exceed | glyphs clean on all 3 targets | 0-exceed per target |
|---|---|---|---|---|---|
| 5 | 2.22 | 0.161 | 0/150 | **0/50** | paris 0, planet 0, open 0 |
| 11 | **1.82** | 0.233 | 50/150 | **0/50** | paris 0, planet 0, open **50** |
| **16** | **3.76** | 0.278 | 77/150 | **0/50** | paris 0, planet 27, open **50** |

**No glyph clears the null on all three targets at any layer.** The
magnitude-controlled effect is clean only on the open-ended target (`I am
thinking about`, where the null is tightest — sd 0.008 vs 0.043 for `paris`),
partly on `planet` at layer 16, and never on `paris`. So §3 is a real *ordering*
carried mostly by one target, not 38 individually significant findings. The
prompt-level result (§1, §2) does not depend on the null at all and is unaffected.

Layer 16 is where emoji directions push hardest, and **layer 11 is the weakest**.
Worth flagging: the [sibling OOC screen](../llama32_3b_bf16_ooc_screen_v1/README.md)
found layer 11 to be the *best* depth for fingerprint *separation*. Different
question, different answer — separability and causal push do not rank layers the
same way. Direction consistency (mean pairwise cosine of the four per-wrapper
deltas) rises monotonically with depth: the deeper the layer, the more portable
the emoji direction is across contexts. It is still only ~0.28, so most of any
single context's delta is context, not glyph.

### 5. Family effects (token-matched stratum)

| family | n | prompt KL (med) | ratio (med) |
|---|---|---|---|
| food | 7 | 0.467 | **5.19** |
| animal | 7 | 0.452 | 3.63 |
| nature | 7 | 0.386 | 4.23 |
| transport | 7 | 0.335 | 3.54 |
| symbol | 7 | 0.299 | 3.76 |
| face | 3 | 0.278 | 2.93 |

### 6. What the injected directions push toward

Qualitatively the most striking part. Injecting a glyph's direction into
`The capital of France is` boosts tokens that are recognisably about that glyph:

| glyph | top boosted tokens |
|---|---|
| 🍕 pizza | `' yummy'` `' delicious'` `' pizza'` |
| 🚗 car | `' Automobile'` `' Vehicles'` `' cars'` |
| 🐶 / 🐱 / 🐻 / 🐢 | `' Animals'` `' Animal'` `' animals'` |
| 🥑 avocado | `' Delicious'` `' pizza'` `' yummy'` |
| 🌈 rainbow | `' Magical'` `' COLOR'` `' Cute'` |
| ⬜ white_square | `' geometry'` `' Geometry'` |
| 🇯🇵 flag_jp | `' japan'` `' Japan'` `' Japanese'` |
| 👩‍💻 woman_tech | `' Software'` `' Programming'` |
| 🏳️‍🌈 flag_rainbow | `' Diversity'` `' diversity'` `' Minority'` |
| 👨‍👩‍👧‍👦 family_four | `' Family'` `' Kids'` `' kids'` |
| 🐈‍⬛ black_cat | `' Animals'` (+ emoji byte fragments) |

A recurring second pattern: for many glyphs (🔥 🌊 ⚡ 🚀 🚂 🤯 …) the top boosted
IDs are **partial-UTF-8 emoji byte fragments**, i.e. the direction is partly
"emit an emoji" rather than "emit this concept".

**This is a description of what the screen produced, not a semantic claim.** The
random-direction null is a *size* control, not a semantic control. Beating it
shows the direction is structured; it does not show the structure is meaning.

## Deep diagnostic (follow-up run)

The sweep above has two weaknesses: only 3 injection targets, and only 24 random
directions in the null. A focused follow-up on 13 glyphs — the strongest, the
top-of-prompt-ranking pair, three weak controls, and 🐈‍⬛ — takes those to **12
targets** and **256 random directions each**, sweeps **every layer**, and adds a
specificity test. Full numbers in [`results/deep_report.md`](results/deep_report.md),
chart in [`chart/deep_chart.html`](chart/deep_chart.html).

**1. It generalises; §4's "one target only" was an artefact.** Six of the twelve
targets are cleared by all 13 glyphs, at the nonparametric floor p = 1/257 =
0.0039. Detectability belongs to the *target*, not the glyph:
Spearman(baseline entropy, glyphs clearing the null) = **+0.70**. Sharp factual
prompts hide the effect because a random push moves them a lot too. The
sweep's ranking replicates (Spearman **+0.75** against the 12-target run).

**2. But significance and effect size come apart.** The weak controls
(⬛ 🥺 ⛵) clear the null on 6-7 of 12 targets — exactly as many as 🍕 and 🍺.
The binary test saturates. Strong-group ratio median 4.36 vs weak-control 3.09:
the ordering lives in the ratio, not in whether a cell is significant.

**3. The layer profile splits this panel in two.**

> ⚠️ **Superseded — see [the why-flat follow-up](#why-are-some-glyphs-flat-follow-up).**
> This section originally said the split was "exhaustive and has no exceptions".
> That was wrong: it was a property of *this 13-glyph panel*, which happens to
> contain no intermediate cases. Widening to 19 glyphs turns the mid-network
> ratio into a **continuum** (2.71 → 5.66, largest gap only 0.73), and the
> binary mid-peak/last-peak label turns out to be driven by the *final-layer*
> value rather than by mid-network engagement — it mislabels ☕ and 🚢.

| shape | glyphs | mid-network max (L10-19) | final layer L27 |
|---|---|---|---|
| **mid-peak** | 🍺 🍕 🍣 🍔 🌍 🚗 🍜 🐶 🐱 | **3.7 – 5.7** (peak L14-16) | 1.3 – 2.1 |
| last-peak | ⬛ 🥺 ⛵ 🐈‍⬛ | 2.7 – 3.1 | **3.8 – 6.4** |

L27's `resid_post` feeds the unembedding almost directly, so a spike there means
"this direction is token-like", while a bump at L14-16 means it engages the
remaining computation. ⬛'s peak ratio of 6.43 is the largest number in the run
and is entirely of the first kind. At **L0 every glyph sits at ratio 0.05** — a
real emoji direction is ~20× *less* disruptive than a matched random one at the
embedding layer, while direction consistency runs the opposite way (0.93 at L0,
0.43 at L27). Where the direction is most reproducible it does the least.

**4. The direction carries a category, not an instance.** With hand-written
probe words (not harvested from the model's own outputs, so the diagonal is not
selected-on): own probe group wins for only **4/13** glyphs, but own *category
block* wins for **10/13**. 🍣 boosts *burger* words (+2.95) more than *sushi*
words (+1.86). The failures are informative — ⛵ scores **−0.48** on `vehicle`
where 🚗 scores **+1.27**, so sharing a category with a strong glyph buys nothing.

**5. Caveats this run produced.** Sign-flip antisymmetry is only ~0.63, so at
α = 0.5 the response is already outside the linear regime. Tripling the
extraction wrappers (4 → 12) saturates consistency at ~0.4 and *lowers* the
median effect — 4 wrappers were already enough. And one block assignment is bad:
🌍 was put in a catch-all `other` block, so its block test fails despite a
textbook mid-peak profile; that is a grouping artefact, not a finding.

## Why are some glyphs flat? (follow-up)

The deep run's four flat glyphs (⬛ 🥺 ⛵ 🐈‍⬛) are the interesting case — negative
results are where a mechanism shows itself. A 19-glyph panel built around
**near-synonym pairs differing in UTF-8 byte class** (⛵/🚢, ☕/🍵, ⬛/🟥, ✈️/🚁),
a **ZWJ decomposition set** (🐈‍⬛ / 🐈 / 🐱 / ⬛) and an **emotion set**
(🥺 / 😢 / 😭 / 🤔) tests three hypotheses. Full numbers in
[`results/whyflat_report.md`](results/whyflat_report.md).

**All three are refuted or only partly supported — and the run overturns a claim
made above.**

| | hypothesis | verdict |
|---|---|---|
| H3 | the model has no concept for these glyphs | **refuted** — all 19 glyphs' correct concept is the top-1 or top-2 next token; ⬛ → `' black square with a white border'`, 🐈‍⬛ → `' black cat with a white face'` |
| H2 | 🐈‍⬛'s direction is dominated by its ⬛ tail | **refuted** — `cos(🐈‍⬛, 🐈) = 0.94` vs `cos(🐈‍⬛, ⬛) = 0.77` at L27, cat-side at every depth, margin *widening* with depth |
| H1 | it is the UTF-8 byte class, not the meaning | **partly** — Spearman(is 3-byte, mid ratio) = **−0.50**; 3 of 4 near-synonym pairs put the 4-byte member higher (median 1.26×); the exception is the abstract pair |

**⚠️ This supersedes §3 of the deep diagnostic above.** Across 19 glyphs the
mid-network ratio is a **continuum** (2.71 → 5.66, largest gap 0.73), not a clean
two-way split — the split was a property of a 13-glyph panel containing no
intermediate cases. The binary mid-peak/last-peak label is also the wrong metric:
it is driven by the *final-layer* value, and it ranks ☕ (mid 2.87) above 🚢
(mid 3.72). The absolute mid-network ratio is used throughout the follow-up.

**The best remaining puzzle.** 🐈 (3.96) and 🐱 (3.95) both engage the middle of
the network; 🐈‍⬛ (3.09) does not, landing exactly on ⬛ (3.00) — while its
*direction* stays cat-shaped and the model still names it "black cat".
**Direction similarity and causal efficacy come apart.** Whatever ZWJ composition
costs, it is not "the direction becomes the last component". The next step is to
extract the direction at each *token position* of 🐈‍⬛ rather than only at the
wrapper's `last_nonpad`, and find where the efficacy is lost.

Two other things it settles: it is **not** "emotions are flat" (😢 4.22 and
😭 4.19 peak mid-network while 🥺 2.71 and 🤔 2.76 do not — a 1.6× spread inside
one family), and it is **not** token count (Spearman = −0.02).

## Composition: what happens when two glyphs are stuck together

Chasing the why-flat puzzle (🐈 3.96 and 🐱 3.95 engage the middle of the network,
the ZWJ compound 🐈‍⬛ 3.09 does not) across three more runs, one of them
**pre-registered**. Full numbers in
[`results/composition_report.md`](results/composition_report.md), pre-registration
in [`PREREGISTRATION_mean_rule.md`](PREREGISTRATION_mean_rule.md).

🐈‍⬛ tokenises exactly as 🐈's tokens + ZWJ + ⬛'s tokens, so the joiner can be
removed and the order reversed independently.

| | verdict |
|---|---|
| **the ZWJ joiner** | **not what costs the compound its efficacy.** Removing it leaves 🐈⬛ at 3.31, nowhere near 🐈's 3.96. It is not *nothing* though — it moves the value by 0.006–0.215, and the "👩‍💻 3.39 vs 👩💻 3.39" equality is a 2-dp artefact (3.3933 vs 3.3870) |
| **"the last component wins"** | **no.** Order shifts the value (🐈⬛ 3.31 → ⬛🐈 3.61), but **neither its size nor its sign is consistent**: ending on the stronger part scores higher in 6/7 families of one set and only 2/6 of the next — 8/13 pooled, against 6.5 expected by chance |
| **order effect ∝ component gap** | **no such relationship.** Spearman **+0.04** on 7 families, **−0.94** on 6 more, same protocol. A statistic that flips sign between samples is noise |
| **what sets the composite** | **the mean of its components** — `composite ≈ 0.70 × mean + 1.16`, and 🐈‍⬛ is weak simply because 🐈 (3.96) and ⬛ (3.00) average to 3.48 |
| **direction vs efficacy** | **independent.** Across 26 cases, reversing a pair moves the cosine by ≤ **0.09** while moving the efficacy by up to **0.94** |

**The mean rule was found post-hoc**, after the order hypothesis failed — so it
was written down with its six predictions and a two-part decision rule, committed
before the test script existed (the runner aborts if its predictions disagree
with the committed file), and then tested on six families that did not shape it:

| criterion | required | observed | |
|---|---|---|---|
| Spearman(predicted, observed) | ≥ 0.70 | **+0.886** | PASS |
| mean absolute error | ≤ 0.72 | **0.308** | PASS |

All 11 solo components reproduced their earlier values. Note the resolution: the
prior values are stored to 2 dp, so a successful reproduction is bounded below
0.005 **by construction** — this detects drift larger than that, and is not a
4-dp agreement.

**Read the negative results as the more reliable ones.** The order effect flips
both its correlation with the component gap (+0.04 → −0.94) and its own sign
(6/7 → 2/6) between two samples of the same protocol. That is a direct
demonstration that n≈6 statistics are unstable here — which applies to the mean
rule too, pre-registered or not. What is solid is that the joiner cannot explain
the compound's weakness, and the direction/efficacy independence (26 cases).

## Chasing the one reversed family — and not finding a rule

The composition report left one family running backwards (🍕⬛ 4.94 vs ⬛🍕 4.00,
order effect **−0.94**). Two runs check whether there is anything to explain, and
whether it generalises. Full numbers in
[`results/order_report.md`](results/order_report.md).

Method note: re-seeding the null would not have tested this. The injection KL is
deterministic and the null is a denominator **shared by both orders**, so
re-seeding rescales an order effect without moving its sign. The two places real
sampling variability enters are varied instead — the extraction wrappers and the
injection targets — giving 2 × 2 = four independent estimates of each pair.

| panel | prediction stated first | outcome |
|---|---|---|
| does 🍕⬛'s sign survive? | it will **not** be stable | **prediction wrong.** 🍕⬛ is 0/4 positive across all four conditions and 🍔⬛ agrees (0/4). 🚗⬛ and 🍕⬜ flip |
| is "food + black square" a type? | if it is, the three new foods go negative and the two non-food controls do not | **no type.** The foods disagree with each other (🍣⬛ 4/4, 🍜⬛ 3/4, 🍺⬛ 1/4) and the non-food controls are *both* sign-stable (🐶⬛ 4/4, 🌈⬛ 4/4) — at least as consistent as the foods |

So an individual pair can carry a reproducible order preference, but it follows
**neither the component gap, nor semantic category, nor even other members of its
own category** — and non-food pairs are just as capable of being stable. Whatever
🍕⬛ and 🍔⬛ have, food does not predict it. No general rule survives, and the
magnitude is not stable either — 🍕⬛ ranges −1.09 to −0.03 across conditions;
only the sign is preserved.

**Correction.** The first version of this section said the controls "flip at 3/4
— indistinguishable from the foods". That came from a runner that re-decided
which component counted as *strong* inside the condition loop, so the cells where
⬛ outranked its partner were measured in a mirrored frame. Under one fixed
convention both controls are sign-stable. The conclusion is unchanged; the reason
is different.

Worth stating plainly: "stable across four conditions" is a weak bar. With a
genuinely 50/50 sign one pair in eight looks stable by chance, and nine pairs
were tested here.

## What this is NOT

- **Not** the sealed v2 experiment, and not a reproduction of it.
- **Not** a causal or semantic claim. The records are stamped
  `pre-causal-activation-screen`, `causal_claim_authorized: false`.
- **Not** a tokenizer-independence result. Token count is controlled *within* the
  matched stratum and *measured* across the ladder — that is much stronger than
  the sealed work's `wrapper_tokenization_control` HOLD, but it is still one
  panel, one model, one position (`last_nonpad`), and three targets.
- **Not** canonical provenance: non-frozen library versions and an `orjson`
  stand-in, so any receipt hashes here are not comparable to canonical runs.

## Environment & provenance

- **Weights: identical to the sealed v2 artifact** — `mlx-community/Llama-3.2-3B-bf16`
  @ `60a99aaf…`, `manifest_sha256 dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4`,
  verified by the sibling sandbox's `verify_bf16.py`.
- Python 3.12.6 / torch 2.12.1 / transformers 5.13.0 / numpy 2.2.3 (the freeze is
  3.13.13 / 2.11.0 / 4.57.6 / 2.4.4 — hence not a v2 reproduction).
- Shims reused from `../llama32_3b_bf16_ooc_screen_v1/scripts/shim/` via
  `PYTHONPATH` only; nothing on disk is patched.
- `PYTHONNOUSERSITE=1` disables the machine's user-site numpy/torch monkey-patch
  layer, so numerics are unpatched.
- **Numerics note.** numpy on macOS/Accelerate raises spurious
  `divide by zero / overflow / invalid value encountered in matmul`
  RuntimeWarnings on large float64 dot products. Verified spurious for this data:
  all activations and logits are finite and `a @ b` is **bit-identical** to
  pure-Python summation (relative error exactly 0.0). Only that message is filtered.

## Reproduce

Run from this directory. Requires the bf16 model in your HF cache and
`glyphprobe[torch]` importable.

```sh
export HF_HOME=~/.hf_home
export SNAP=$HF_HOME/hub/models--mlx-community--Llama-3.2-3B-bf16/snapshots/60a99aaf43164077157d64bf909b7b61143c6a6d
SHIM=../llama32_3b_bf16_ooc_screen_v1/scripts/shim

# ~6 min on an M4 (2,157 records)
PYTHONNOUSERSITE=1 PYTHONPATH=$SHIM:../../src SNAP=$SNAP \
  python3 scripts/sweep_emoji_intervention.py \
    --layers 5 11 16 --alphas 0.1 0.5 1.0 --primary-alpha 0.5 --random-controls 24

PYTHONNOUSERSITE=1 PYTHONPATH=$SHIM:../../src python3 scripts/analyze_sweep.py
PYTHONNOUSERSITE=1 python3 scripts/make_chart.py
```

`--limit N` restricts the sweep to the first N glyphs for a fast sanity check.

## Contents

```
panel/     sweep_panel_v1.yaml                  — 50 glyphs, matched + ladder strata
scripts/   sweep_emoji_intervention.py          — the 50-glyph sweep
           analyze_sweep.py                     — ranking, strata, correlations
           deep_diagnose.py                     — 4-phase deep diagnostic (13 glyphs)
           analyze_deep.py                      — deep-run analysis
           gen_report.py, gen_deep_report.py    — results/*.md from the records
           make_chart.py, make_deep_chart.py    — self-contained CSP-safe charts
           why_flat.py                          — why-flat follow-up (19 glyphs)
           analyze_whyflat.py                   — corrected continuous analysis
           cat_chase.py, cat_chase2.py          — composition: ZWJ vs order
           mean_rule_test.py                    — PRE-REGISTERED confirmatory test
           gen_composition_report.py            — results/composition_report.md
chart/     sweep_chart.html, sweep_chart_data.json, deep_chart.html, whyflat_chart.html
results/   report.md, deep_report.md, whyflat_report.md,
           composition_report.md                — full tables
           sweep_v1_*.jsonl/.json               — 50-glyph sweep records
           deep_v1_phase{1,2,3,4}.jsonl         — deep-run records
           deep_v1_specificity_matrix.json, deep_v1_analysis.json
           whyflat_v1_phase{1,2}.jsonl, _hypotheses.json, _analysis.json
           catchase_v{1,2}_*.json(l), meanrule_v1_*.json(l)
           *_meta.json

Console logs (`*_console.log`, `analysis_*.log`) are produced by every run but are
covered by the repo-wide `*.log` gitignore rule, so they are not committed. Rerun
the commands above to regenerate them.
```

Raw activation arrays are not stored — the records keep the derived metrics only, verified by the fact that no committed file holds a per-layer vector.
Regenerate everything with the commands above.
