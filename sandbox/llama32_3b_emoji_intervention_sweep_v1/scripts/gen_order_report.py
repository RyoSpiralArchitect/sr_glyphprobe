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


def recompute(data):
    """Order effects under ONE fixed convention per pair.

    Both summaries were produced by a runner that re-decided strong/weak inside
    the condition loop. black_sq outranks its partner in some conditions and not
    others, so those cells were measured in a mirrored frame. Everything below is
    recomputed as mid[strong-last] - mid[strong-first] with `strong` fixed from
    the first condition, and `rank_flips` records where the runner would have
    mirrored it.
    """
    mid = data["mid"]
    cs = list(data["order_effect_table"][0]["order_effects"])
    out = []
    for t in data["order_effect_table"]:
        a, b = t["A"], t["B"]
        ref = cs[0]
        strong, weak = ((a, b) if mid[f"{a}|{ref.replace('/', '|')}"]
                        >= mid[f"{b}|{ref.replace('/', '|')}"] else (b, a))
        eff = {}
        flips = []
        for c in cs:
            k = c.replace("/", "|")
            eff[c] = (mid[f"{t['pair']}__{weak}_{strong}|{k}"]
                      - mid[f"{t['pair']}__{strong}_{weak}|{k}"])
            if (mid[f"{a}|{k}"] >= mid[f"{b}|{k}"]) != (strong == a):
                flips.append(c)
        npos = sum(v > 0 for v in eff.values())
        out.append({**t, "strong": strong, "weak": weak, "order_effects": eff,
                    "n_positive": npos, "n_conditions": len(cs),
                    "sign_stable": npos in (0, len(cs)),
                    "range": max(eff.values()) - min(eff.values()),
                    "rank_flips": flips})
    return out, cs


an["order_effect_table"], conds_an = recompute(an)
ft["order_effect_table"], conds_ft = recompute(ft)
assert conds_an == conds_ft, (conds_an, conds_ft)
for d in (an, ft):
    d["n_sign_stable"] = sum(t["sign_stable"] for t in d["order_effect_table"])
GL = {"pizza": "🍕", "burger": "🍔", "car": "🚗", "black_sq": "⬛", "white_sq": "⬜",
      "sushi": "🍣", "ramen": "🍜", "beer": "🍺", "dog": "🐶", "rainbow": "🌈"}

o = []
w = o.append
conds = conds_an

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
        note = (" ⚠" if t["rank_flips"] else "")
        w(f"| {a_g}{b_g} `{t['pair']}` | {t['strong']} | {t['weak']}{note} | {effs} | "
          f"{t['n_positive']}/{t['n_conditions']} | "
          f"{'**STABLE**' if t['sign_stable'] else 'flips'} |")
    fl = [t for t in data["order_effect_table"] if t["rank_flips"]]
    if fl:
        w("\n⚠ = the two components swap rank in " +
          ", ".join(f"`{t['pair']}` ({', '.join(t['rank_flips'])})" for t in fl) +
          ". A positive order effect always means *ends on the component that is "
          "stronger in the first condition*; the runner originally re-decided this "
          "per condition, which mirrored those cells. Everything here uses the "
          "fixed convention.")
    w(f"\nSign stable across all four conditions: "
      f"**{data['n_sign_stable']}/{data['n_pairs']}**.\n")

pz = next(t for t in an["order_effect_table"] if t["pair"] == "pizsq")
bu = next(t for t in an["order_effect_table"] if t["pair"] == "bursq")
su = next(t for t in ft["order_effect_table"] if t["pair"] == "sussq")
w("## What the two panels say together\n")
_ftab = {t["pair"]: t for t in ft["order_effect_table"]}
_foods = [_ftab[k] for k in ("sussq", "ramsq", "beesq")]
_ctrls = [_ftab[k] for k in ("dogsq", "rainsq")]
w(f"**Panel 1 refuted my prediction.** 🍕⬛ holds its sign in all four conditions "
  f"({pz['n_positive']}/{pz['n_conditions']} positive) and 🍔⬛ agrees "
  f"({bu['n_positive']}/{bu['n_conditions']}). {an['n_sign_stable']} of "
  f"{an['n_pairs']} pairs are sign-stable, so the anomaly is not one draw from a "
  "noisy quantity — there is something there.\n")
w("**Panel 2 refuted the type.** The three foods do not agree with each other: "
  + ", ".join(f"`{t['pair']}` {t['n_positive']}/{t['n_conditions']}" for t in _foods)
  + ". And the two non-food controls are "
  + ", ".join(f"`{t['pair']}` {t['n_positive']}/{t['n_conditions']}" for t in _ctrls)
  + f" — {'both sign-stable' if all(t['sign_stable'] for t in _ctrls) else 'mixed'}, "
  "i.e. the controls behave at least as consistently as the foods do. Whatever "
  "🍕⬛ and 🍔⬛ have, **food does not predict it**.\n")
w("Put together: an individual pair can carry a reproducible order preference, but it "
  "follows neither the component gap, nor semantic category, nor other members of its "
  "own category — and non-food pairs are just as capable of being stable. **No general "
  "rule survives.** The magnitude is not stable either — 🍕⬛ ranges "
  f"{min(pz['order_effects'].values()):+.2f} to "
  f"{max(pz['order_effects'].values()):+.2f} (spread {pz['range']:.2f}); only the sign "
  "is preserved.\n")
w("> **Correction.** The first version of this report said the non-food controls "
  "\"flip at 3/4 — indistinguishable from the foods\". That came from a runner that "
  "re-decided which component was *strong* inside the condition loop; ⬛ outranks its "
  "partner in `WB/TA` but not elsewhere, so those cells were measured in a mirrored "
  "frame. Under one fixed convention the controls are sign-stable, not flipping. The "
  "conclusion that food is not the type is unchanged — the reason is different.\n")
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
