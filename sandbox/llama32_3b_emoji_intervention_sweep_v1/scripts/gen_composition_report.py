#!/usr/bin/env python3
"""Render results/composition_report.md from the cat-chase and mean-rule runs.

All tables are computed from the records. The prose quotes a few of them as
literals; re-read it if you rerun with a different panel.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"

v1 = json.loads((res / "catchase_v1_summary.json").read_text(encoding="utf-8"))
v2 = json.loads((res / "catchase_v2_summary.json").read_text(encoding="utf-8"))
mr = json.loads((res / "meanrule_v1_summary.json").read_text(encoding="utf-8"))

o = []
w = o.append
m1 = {p["id"]: p for p in v1["panel"]}
m2 = {p["id"]: p["mid"] for p in v2["panel"]}

w("# Emoji composition — what happens when two glyphs are stuck together "
  "(out of contract)\n")
w("Chases the puzzle left by [the why-flat follow-up](whyflat_report.md): 🐈 (3.96) "
  "and 🐱 (3.95) engage the middle of the network, the ZWJ compound 🐈‍⬛ (3.09) does "
  "not, and its direction stays cat-shaped anyway. Three runs, one pre-registered. "
  "See [README](../README.md) for the boundary. Claim stage "
  "`pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.\n")

w("## Summary\n")
w("| question | answer | confidence |")
w("|---|---|---|")
w("| is the ZWJ joiner the cause? | **no** — removing it does not restore the strong "
  "component's value | solid, 3 families |")
w("| does the composite follow its LAST component? | **no** — order shifts the value "
  "but does not set it | solid |")
w("| does the order effect scale with the component gap? | **no relationship exists** "
  "— Spearman +0.04 on one set, **−0.94** on another | solid (as a negative) |")
w("| what sets the composite? | **the mean of the two components** | pre-registered "
  "test passed, n = 6 |")
w("| does the direction move with the order? | **barely** — cosine shifts stay under "
  "0.09 while efficacy moves up to 0.94 | solid, 26 cases |\n")

# ---------------------------------------------------------------- ZWJ
w("## 1 — the ZWJ joiner is not the cause\n")
w("🐈‍⬛ tokenises exactly as 🐈's tokens + a ZWJ token + ⬛'s tokens, verified at run "
  "time, so the joiner can be removed and the order reversed independently.\n")
w("| construction | join | order | mid-network ratio |")
w("|---|---|---|---|")
for cid, join, order in (("cat", "-", "🐈 alone"), ("cat_ZWJ_sq", "zwj", "🐈 then ⬛"),
                         ("cat_sq", "concat", "🐈 then ⬛"),
                         ("sq_cat", "concat", "⬛ then 🐈"),
                         ("sq_ZWJ_cat", "zwj", "⬛ then 🐈"),
                         ("black_sq", "-", "⬛ alone")):
    w(f"| {m1[cid]['glyph']} `{cid}` | {join} | {order} | **{m1[cid]['mid']:.2f}** |")
w("\nAt a fixed order the joiner moves the value by **0.006 to 0.215** — the same "
  "magnitude as order effects this report treats as signal, so it is not nothing. The "
  "apparent \"exactly equal\" in the tech family (3.39 vs 3.39) is a 2-dp display "
  "artefact; the values are 3.3933 and 3.3870. What the data supports is narrower and "
  "still decisive for the question asked: removing the joiner leaves 🐈⬛ at 3.31, "
  "nowhere near 🐈's 3.96, so **the joiner cannot be what costs the compound its "
  "efficacy**.\n")

# ---------------------------------------------------------------- order
w("## 2 — order shifts the value, but no rule predicts by how much\n")
w("Seven families, both orders, bare concatenation, ordered by component gap:\n")
w("| family | strong | weak | gap | ends weak | ends strong | order effect |")
w("|---|---|---|---|---|---|---|")
for f in v2["family_table"]:
    w(f"| {f['family']} | {f['strong']} {f['mid_strong']:.2f} | "
      f"{f['weak']} {f['mid_weak']:.2f} | {f['gap']:.2f} | {f['ends_weak']:.2f} | "
      f"{f['ends_strong']:.2f} | **{f['order_effect']:+.2f}** |")
_a = [f["order_effect"] for f in v2["family_table"]]
_b = [f["order_effect"] for f in mr["families"]]
_pa, _pb = sum(x > 0 for x in _a), sum(x > 0 for x in _b)
w(f"\nEnding on the stronger component scores higher in **{_pa}/{len(_a)}** of these "
  f"families — but in only **{_pb}/{len(_b)}** of the six later ones, measured on the "
  f"same protocol with the same sign convention. Pooled that is "
  f"**{_pa+_pb}/{len(_a)+len(_b)} against {(len(_a)+len(_b))/2:.1f} expected by "
  "chance**. *Neither the size nor the sign of the order effect is consistent across "
  "samples.* Both are reported here as negative results:\n")
w(f"- Spearman(gap, order effect) on these 7 families = **"
  f"{v2['spearman_gap_vs_order_effect']:+.3f}**")
gaps = [abs(mr["solo_prior"][f["A"]] - mr["solo_prior"][f["B"]]) for f in mr["families"]]
oeff = [f["order_effect"] for f in mr["families"]]


def sp(x, y):
    def rk(v):
        a = np.asarray(v, float); s = a.argsort(); r = np.empty(len(a))
        r[s] = np.arange(1, len(a) + 1)
        for u in np.unique(a):
            k = a == u
            if k.sum() > 1:
                r[k] = r[k].mean()
        return r
    rx, ry = rk(x) - rk(x).mean(), rk(y) - rk(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


w(f"- the same statistic on the 6 *later* families = **{sp(gaps, oeff):+.3f}**\n")
w("**The sign of that correlation flips between two sets measured on the identical "
  "protocol.** A quantity that reads +0.04 on one sample and −0.94 on another is not a "
  "relationship; it is small-sample noise. This is recorded as a negative result — and "
  "as a warning about every other n≈6 Spearman in this directory, including the one "
  "below that passed.\n")
w("> This is the second time the same mistake was caught here. The 'order effect grows "
  "with the gap' idea was originally read off **two** families (+0.30 and +0.01), stated, "
  "and then dissolved at n=7. The flip to −0.94 at n=6 confirms the retraction was "
  "right.\n")

# ---------------------------------------------------------------- mean rule
w(f"For completeness, the run built to test \"follows the last component\" reported "
  f"**{v1['n_nearest_last']}/{v1['n_composites']}** composites landing nearest their last "
  "part — the observation that suggested H-LAST. Section 3 explains that pattern without "
  "needing it.\n")
w("## 3 — the composite tracks the MEAN of its components (pre-registered)\n")
w("Re-analysing the 7 families for what *did* predict the composite gave "
  "`composite = 0.70 × mean(components) + 1.16` (Spearman +0.821, leave-one-out "
  "+0.714…+0.886, permutation p = 0.017). Post-hoc — so it was written into "
  "[`PREREGISTRATION_mean_rule.md`](../PREREGISTRATION_mean_rule.md) with its "
  "predictions and a two-part decision rule, and committed **before** the test script "
  "existed. The runner re-derives the six predictions and aborts if they disagree with "
  "that file.\n")
w("| family | components | mean | predicted | observed | error |")
w("|---|---|---|---|---|---|")
for f in mr["families"]:
    w(f"| {f['family']} | {f['A']} + {f['B']} | {f['component_mean']:.2f} | "
      f"**{f['predicted']:.2f}** | {f['observed']:.2f} | {f['error']:+.2f} |")
w(f"\n| criterion | required | observed | |")
w("|---|---|---|---|")
_ok_rho = mr["spearman_pred_obs"] >= mr["decision_rule"]["min_spearman"]
_ok_mae = mr["mae"] <= mr["decision_rule"]["max_mae"]
w(f"| Spearman(predicted, observed) | ≥ {mr['decision_rule']['min_spearman']} | "
  f"**{mr['spearman_pred_obs']:+.3f}** | {'PASS' if _ok_rho else 'FAIL'} |")
w(f"| mean absolute error | ≤ {mr['decision_rule']['max_mae']} | "
  f"**{mr['mae']:.3f}** | {'PASS' if _ok_mae else 'FAIL'} |")
w(f"\n**Pre-registered verdict: {mr['verdict']}.**\n")
w(f"Frame check: all {len(mr['solo_prior'])} solo components reproduced their earlier "
  "values. Note the resolution — the prior values are stored to 2 dp, so any successful "
  "reproduction is bounded below 0.005 **by construction**. This check detects drift "
  "*larger* than that; it is not a 4-dp agreement.\n")
w("This also answers the original puzzle. 🐈‍⬛ is weak because 🐈 (3.96) and ⬛ (3.00) "
  "average to 3.48 and the rule compresses toward the middle — not because of the "
  "joiner, and not because ⬛ comes last.\n")

# ---------------------------------------------------------------- geometry
w("## 4 — direction and efficacy are independent\n")
w("Cosines are taken against **named** components, never positional labels. (The first "
  "version of this analysis compared cos-to-first against cos-to-last; those labels swap "
  "with the order, so the column flipped even when the geometry did not. That bug is "
  "why this is stated carefully.)\n")
w(f"| run | cases | max \\|cosine shift\\| | max \\|efficacy shift\\| |")
w("|---|---|---|---|")
w(f"| catchase v2 | {len(v2['fixed_frame_cosines'])} | "
  f"{v2['max_abs_cosine_shift']:.3f} | {v2['max_abs_efficacy_shift']:.2f} |")
w(f"| meanrule v1 | {len(mr['families'])*2} | {mr['max_abs_cosine_shift']:.3f} | "
  f"{max(abs(f['order_effect']) for f in mr['families']):.2f} |")
w("\nReversing a pair moves the direction by at most 0.09 in cosine while moving the "
  "efficacy by up to 0.94, on a scale where the solo components span "
  f"{min(v2['solo_mid'].values()):.2f}…{max(v2['solo_mid'].values()):.2f}. "
  "**Two glyph strings can have near-identical residual directions and substantially "
  "different causal push.** Cosine similarity to a known direction is not evidence "
  "about that direction's effect.\n")

# ---------------------------------------------------------------- residuals
w("## 5 — where the mean rule misses\n")
w("Composite minus the mean of its components, on the fitting set:\n")
w("| family | composite − component mean |")
w("|---|---|")
for fam, a, b in v2["families"]:
    cm = (v2["solo_mid"][a] + v2["solo_mid"][b]) / 2
    comp = (m2[f"{fam}__{a}_{b}"] + m2[f"{fam}__{b}_{a}"]) / 2
    w(f"| {fam} ({a} + {b}) | {comp - cm:+.2f} |")
w("\nThe two extremes are suggestive and **untested**: the twin pair 🐈🐱 (two names for "
  "the same concept) sits **above** the mean, and 🍕🚗 (two strong, unrelated concepts) "
  "sits furthest **below** it. \"Alike composes additively, strong-and-different "
  "interferes\" is a hypothesis this data generated, not one it tested.\n")

w("## Limitations\n")
w("- 13 families total, all two-component, all chosen by me; the confirmatory set shares "
  "its protocol and its author with the fitting set, so this is a replication inside one "
  "sandbox, not an independent one.")
w("- n≈6 Spearman is demonstrably unstable here — the order-effect correlation flipped "
  "sign between sets. The mean rule passed a pre-registered test, but it carries the same "
  "sample-size fragility and should not be treated as established.")
w("- One model, one position (`last_nonpad`), one site (`resid_post`), one strength "
  "(alpha 0.5), three injection targets.")
w("- The random-direction null is a **size** control, not a semantic control.")
w("- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are "
  "byte-identical to the sealed v2 artifact; nothing else here is comparable to a "
  "canonical run.")

(res / "composition_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'composition_report.md'}")
