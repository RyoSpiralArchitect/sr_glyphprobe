#!/usr/bin/env python3
"""Render results/order_report.md from the two stability panels.

All tables are computed from the records.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
an = json.loads((res / "orderstab_v1_summary.json").read_text(encoding="utf-8"))
ft = json.loads((res / "foodtype_v1_summary.json").read_text(encoding="utf-8"))
GL = {"pizza": "🍕", "burger": "🍔", "car": "🚗", "black_sq": "⬛", "white_sq": "⬜",
      "sushi": "🍣", "ramen": "🍜", "beer": "🍺", "dog": "🐶", "rainbow": "🌈"}

o = []
w = o.append
conds = list(an["order_effect_table"][0]["order_effects"])

w("# Chasing the one reversed family — and not finding a rule (out of contract)\n")
w("[The composition report](composition_report.md) left one family running the wrong "
  "way: 🍕⬛ scored 4.94 and ⬛🍕 scored 4.00, an order effect of **−0.94** where six of "
  "the other seven families were positive. The obvious move is to explain it. These two "
  "runs check first whether there is anything to explain, and then whether it "
  "generalises. See [README](../README.md) for the boundary. Claim stage "
  "`pre-causal-activation-screen`, `causal_claim_authorized: false`. No holdout bank.\n")

w("## Method — why not re-seed the null\n")
w("The injection KL is fully deterministic; the null only enters as a denominator that "
  "**both orders of a pair share** at a given (layer, target). Re-seeding therefore "
  "rescales an order effect but can barely move its sign — it is not an independent "
  "sample. The two places genuine sampling variability enters are the direction estimate "
  "and the readout, so those are varied instead:\n")
w("| | set A | set B |")
w("|---|---|---|")
w(f"| extraction wrappers | {', '.join(repr(x) for x in an['wrapper_sets']['A'])} | "
  f"{', '.join(repr(x) for x in an['wrapper_sets']['B'])} |")
w(f"| injection targets | {', '.join(repr(x) for x in an['target_sets']['A'].values())} | "
  f"{', '.join(repr(x) for x in an['target_sets']['B'].values())} |")
w(f"\n2 × 2 = four independent estimates of each order effect, at layers "
  f"{an['layers'][0]}-{an['layers'][-1]} (`mid` is the max over exactly that band).\n")

for tag, data, title, pred in (
        ("A", an, "Panel 1 — does the 🍕⬛ sign survive?",
         "the sign will NOT be stable"),
        ("B", ft, "Panel 2 — is \"food + black square\" a type?",
         "if it is a type, all three new foods should be negative like 🍕⬛ and 🍔⬛, "
         "and the two non-food controls should not")):
    w(f"## {title}\n")
    w(f"*Stated before the run: {pred}.*\n")
    w("| pair | strong | weak | " + " | ".join(conds) + " | positive | sign |")
    w("|---|---|---|" + "---|" * (len(conds) + 2))
    for t in data["order_effect_table"]:
        effs = " | ".join(f"{t['order_effects'][c]:+.2f}" for c in conds)
        a_g, b_g = GL.get(t["A"], t["A"]), GL.get(t["B"], t["B"])
        strong = t["A"] if t["order_effects"] else t["A"]
        w(f"| {a_g}{b_g} `{t['pair']}` | {t['A']} | {t['B']} | {effs} | "
          f"{t['n_positive']}/{t['n_conditions']} | "
          f"{'**STABLE**' if t['sign_stable'] else 'flips'} |")
    w(f"\nSign stable across all four conditions: "
      f"**{data['n_sign_stable']}/{data['n_pairs']}**.\n")

pz = next(t for t in an["order_effect_table"] if t["pair"] == "pizsq")
bu = next(t for t in an["order_effect_table"] if t["pair"] == "bursq")
su = next(t for t in ft["order_effect_table"] if t["pair"] == "sussq")
w("## What the two panels say together\n")
w(f"**Panel 1 refuted my prediction.** 🍕⬛ holds its negative sign in all four "
  f"conditions ({pz['n_positive']}/{pz['n_conditions']} positive) and 🍔⬛ agrees "
  f"({bu['n_positive']}/{bu['n_conditions']}). Two of the four pairs are stable, so the "
  "anomaly is not simply one draw from a noisy quantity — there is something there.\n")
w(f"**Panel 2 refuted the type.** 🍣⬛ is stable in the *opposite* direction "
  f"({su['n_positive']}/{su['n_conditions']} positive), and the other two foods flip "
  f"({', '.join(t['pair'] + ' ' + str(t['n_positive']) + '/4' for t in ft['order_effect_table'] if t['pair'] in ('ramsq', 'beesq'))}). "
  "The non-food controls flip too, at 3/4 each — indistinguishable from the foods. So "
  "the negative sign belongs to **🍕 and 🍔 specifically**, not to food.\n")
w("Put together: individual glyph pairs can carry a reproducible order preference, but "
  "it does not follow the component gap, it does not follow semantic category, and it is "
  "not shared even within one category. **No general rule survives.** The magnitude is "
  f"not stable either — 🍕⬛ ranges {min(pz['order_effects'].values()):+.2f} to "
  f"{max(pz['order_effects'].values()):+.2f} across the four conditions "
  f"(spread {pz['range']:.2f}); only the sign is preserved.\n")

w("## Scale caveat\n")
w("The absolute mid ratios move a lot with the target set — 🍕 reads "
  + " / ".join(f"{an['mid'][k]:.2f}" for k in sorted(an["mid"]) if k.startswith("pizza|"))
  + " across the four conditions. Mid ratios are comparable **within** a condition only. "
  "Order effects are within-condition differences, which cancels most of that, and is "
  "why they are the quantity reported here.\n")

w("## Limitations\n")
w("- Nine pairs across two panels, all two-component, all chosen by me; four conditions "
  "that share one model, one layer band, one strength and one site.")
w("- \"Stable across four conditions\" is a weak bar: with a genuinely 50/50 sign, one "
  "pair in eight would look stable by chance, and nine pairs were tested.")
w("- The pairs that are stable have no explanation here. Recording that they reproduce "
  "is not the same as knowing why.")
w("- The random-direction null is a **size** control, not a semantic control.")
w("- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are "
  "byte-identical to the sealed v2 artifact; nothing else here is comparable to a "
  "canonical run.")

(res / "order_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'order_report.md'}")
