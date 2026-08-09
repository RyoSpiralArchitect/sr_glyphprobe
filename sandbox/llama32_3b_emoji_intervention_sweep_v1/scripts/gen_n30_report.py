#!/usr/bin/env python3
"""Render results/meanrule30_report.md. All tables computed from the records."""
from __future__ import annotations

import json
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
s = json.loads((res / "meanrule30_v1_summary.json").read_text(encoding="utf-8"))
old = json.loads((res / "meanrule_v1_summary.json").read_text(encoding="utf-8"))

o = []
w = o.append
pairs = s["pairs"]
n = s["n_pairs"]
k = s["order_effect_positive"]
lo, hi = s["bootstrap_ci"]
ok_rho = s["spearman_pred_obs"] >= s["decision_rule"]["min_spearman"]
ok_mae = s["mae"] <= s["decision_rule"]["max_mae"]


def binom_two_sided(k, n, p=0.5):
    pk = comb(n, k) * p**k * (1 - p)**(n - k)
    return sum(comb(n, i) * p**i * (1 - p)**(n - i)
               for i in range(n + 1)
               if comb(n, i) * p**i * (1 - p)**(n - i) <= pk * (1 + 1e-12))


w("# The mean rule at n = 30, on components I did not choose (out of contract)\n")
w("Applies two of the four next steps from [FINDINGS §7](../FINDINGS.md): more units "
  "per statistic, and a component pool taken from the repository rather than picked by "
  "the analyst. Pre-registered in "
  "[`PREREGISTRATION_mean_rule_n30.md`](../PREREGISTRATION_mean_rule_n30.md), committed "
  "before this run's script existed. Claim stage `pre-causal-activation-screen`, "
  "`causal_claim_authorized: false`. No holdout bank.\n")

w("## Design\n")
w(f"- **Components**: all {len(s['component_pool'])} glyphs of the repository's "
  "`e2_core35_{animals,food,sky,social,transport}` panels, assembled for earlier work. "
  "Every one costs **exactly 4 prefix tokens on every wrapper**, verified at run time — "
  "token count is constant by construction across the whole pool.")
w(f"- **Pairs**: {n}, drawn by `random.Random({s['pair_seed']})` rejecting any component "
  "used more than twice. Both orders, bare concatenation; all 60 concatenations verified "
  "to tokenise as their two components.")
w(f"- **Rule under test**, frozen at the values fitted on a *different* set: "
  f"`composite = {s['rule']['slope']} × mean(components) + {s['rule']['intercept']}`. "
  "Nothing is re-fitted.\n")

w("## Primary result\n")
w("| criterion | required | observed | |")
w("|---|---|---|---|")
w(f"| Spearman(predicted, observed) | ≥ {s['decision_rule']['min_spearman']} | "
  f"**{s['spearman_pred_obs']:+.3f}** | {'PASS' if ok_rho else 'FAIL'} |")
w(f"| mean absolute error | ≤ {s['decision_rule']['max_mae']} | **{s['mae']:.3f}** | "
  f"{'PASS' if ok_mae else 'FAIL'} |")
w(f"\n**Pre-registered verdict: {s['verdict']}.**\n")
w("| | n = 6 (earlier) | n = 30 (here) |")
w("|---|---|---|")
w(f"| Spearman | +{old['spearman_pred_obs']:.3f} | **+{s['spearman_pred_obs']:.3f}** |")
w(f"| MAE | {old['mae']:.3f} | {s['mae']:.3f} |")
w("| components chosen by | me | the repository |")
w("| bootstrap CI | not supportable | "
  f"**[{lo:+.3f}, {hi:+.3f}]** |")
w(f"| permutation p | — | **{s['permutation_p']:.4f}** |")
w("\nThe bootstrap interval is the number FINDINGS §5.1 asked for and n = 6 could not "
  f"produce. It excludes zero comfortably, but its lower bound ({lo:+.3f}) sits **below "
  f"the {s['decision_rule']['min_spearman']} pass threshold** — the relationship is "
  "solid, the precision is not.\n")

w("## Where the rule is wrong\n")
w(f"Refitting on this sample gives `{s['refit_slope']:.2f} × mean + "
  f"{s['refit_intercept']:.2f}` against the frozen `{s['rule']['slope']} / "
  f"{s['rule']['intercept']}` — reported for comparison only, never substituted. The "
  "ordering transfers; the calibration does not.\n")
errs = [p["error"] for p in pairs]
w(f"Errors run {min(errs):+.2f} to {max(errs):+.2f}, median **{np.median(errs):+.2f}**, "
  f"with {sum(e > 0 for e in errs)}/{n} positive — the frozen rule **under-predicts** on "
  "this pool. MAE is inside the pre-registered bound but worse than the n = 6 run "
  f"({s['mae']:.3f} vs {old['mae']:.3f}), which is what an out-of-sample calibration "
  "check is supposed to reveal.\n")

w("| pair | mean(components) | predicted | observed | error |")
w("|---|---|---|---|---|")
for t in sorted(pairs, key=lambda t: t["component_mean"]):
    w(f"| {t['glyphs']} | {t['component_mean']:.2f} | {t['predicted']:.2f} | "
      f"{t['observed']:.2f} | {t['error']:+.2f} |")

w("\n## The order effect, finally with enough units\n")
p_bin = binom_two_sided(k, n)
w(f"**{k}/{n} pairs positive** (chance {n/2:.0f}), median "
  f"**{s['order_effect_median']:+.2f}**, binomial two-sided **p = {p_bin:.4f}**.\n")
w("This is the first sample in the series large enough for the sign to mean anything, "
  "and it points the **opposite way to my original claim**. The history:\n")
w("| sample | n | positive | reading |")
w("|---|---|---|---|")
w("| catchase v2 | 7 | 6/7 | \"ending on the stronger component scores higher\" |")
w("| meanrule v1 | 6 | 2/6 | the reverse |")
w(f"| **this run** | **{n}** | **{k}/{n}** | **ending on the stronger component scores "
  f"LOWER** (p = {p_bin:.3f}) |")
w("\nThe retraction in [FINDINGS §3](../FINDINGS.md) was right that the 6/7 claim did not "
  "hold. It was *too* agnostic in one respect: with 30 units the effect is not absent, it "
  "runs the other way. Treat this as a new, single-sample finding at the same evidential "
  "level the 6/7 claim once had — it needs its own replication before it is more than "
  "that.\n")

same = [t for t in pairs if t["same_family"]]
diff = [t for t in pairs if not t["same_family"]]
w("## The same-family hunch is not supported\n")
w(f"[Composition report §5](composition_report.md) noted that 🐈🐱 (one concept, two "
  "names) sat +0.54 above the line and 🍕🚗 (two strong unrelated concepts) −0.83 below, "
  "and flagged \"alike composes additively\" as an untested hypothesis. Here:\n")
w("| pairs | n | median residual |")
w("|---|---|---|")
w(f"| same family | {len(same)} | {np.median([t['error'] for t in same]):+.2f} |")
w(f"| cross family | {len(diff)} | {np.median([t['error'] for t in diff]):+.2f} |")
w("\nEssentially no difference. The hunch is **not supported** — though 6 vs 24 is an "
  "unbalanced comparison and the same-family pairs come from only five panels, so this "
  "is weak evidence against rather than a refutation.\n")

w("## Limitations\n")
w("- Still one model, one site (`resid_post`), one position (`last_nonpad`), one "
  "strength (α = 0.5), three injection targets, layers 10-19.")
w("- The component *pool* is the repository's, but the sampler, protocol and analysis "
  "are mine, and this run shares its measurement frame with the fitting set. §7's "
  "\"independent replication\" is still open.")
w("- The calibration failure means the rule should be quoted as an ordering, not as a "
  "predictor of magnitude.")
w("- The random-direction null is a size control, not a semantic control.")
w("- Non-canonical provenance: unpinned libraries and an `orjson` stand-in.")

(res / "meanrule30_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'meanrule30_report.md'}")
