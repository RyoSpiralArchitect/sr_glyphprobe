#!/usr/bin/env python3
"""Render results/report.md from the sweep records.

All tables are computed from the records. A few sentences of surrounding prose
name specific targets/layers as literals; re-read them if you rerun with a
different panel, alpha or null size."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
meta = json.loads((res / "sweep_v1_meta.json").read_text())
summ = json.loads((res / "sweep_v1_summary.json").read_text())
gs = [json.loads(l) for l in (res / "sweep_v1_glyph_summary.jsonl").read_text().splitlines() if l.strip()]

L = str(meta["layers"][-1])
pa = meta["primary_alpha"]
matched = [g for g in gs if g["stratum"] == "matched"]
ladder = sorted([g for g in gs if g["stratum"] == "ladder"], key=lambda g: g["n_prefix_tokens"])

out = []
w = out.append
w("# Per-glyph emoji intervention sweep — results (out of contract)\n")
w("Generated from `sweep_v1_records.jsonl` by `scripts/analyze_sweep.py`. "
  "See [README](../README.md) for method and boundary. "
  "Claim stage: `pre-causal-activation-screen`, `causal_claim_authorized: false`.\n")

w("## Run\n")
w(f"- {meta['n_glyphs']} glyphs, {meta['n_records']:,} records, {meta['elapsed_s']:.0f} s "
  f"(M4, MPS/FP32)")
w(f"- layers {meta['layers']}, alphas {meta['alphas']} (primary {pa}), "
  f"{meta['random_controls']} random-direction controls per (layer, target, alpha)")
w(f"- extraction wrappers: {', '.join(repr(x) for x in meta['extract_wrappers'])}")
w(f"- injection targets: " + ", ".join(f"`{v}` (top-1 `{meta['target_baseline_top1'][k]}`)"
                                       for k, v in meta["inject_targets"].items()))
w(f"- zero-hook exact no-op: **{meta['zero_hook_exact_noop']}**; "
  f"dose-monotonic cells: **{summ['dose_monotonic_fraction']*100:.0f}%**\n")

w("## Correlations\n")
w("| relationship | Spearman ρ |")
w("|---|---|")
w(f"| prefix token count vs prompt-level KL (all {summ['n_glyphs']}) | "
  f"**{summ['spearman_tokens_vs_prompt_kl_all']:+.3f}** |")
w(f"| prefix token count vs ratio-to-null (all {summ['n_glyphs']}) | "
  f"**{summ['spearman_tokens_vs_ratio_all']:+.3f}** |")
w(f"| prompt-level KL vs ratio-to-null (matched stratum) | "
  f"**{summ['spearman_promptkl_vs_ratio_matched']:+.3f}** |\n")

w(f"## A. Token-matched stratum — full ranking by prompt-level effect "
  f"({len(matched)} glyphs, all exactly 4 prefix tokens)\n")
w(f"| # | glyph | id | family | prompt KL | ratio L{L} | z | consistency | top boosted |")
w("|---|---|---|---|---|---|---|---|---|")
for i, g in enumerate(matched, 1):
    b = g["by_layer"][L]
    tb = " ".join(f"`{t}`" for t, _ in g["top_boosted_deepest_layer"][:3])
    w(f"| {i} | {g['glyph']} | {g['id']} | {g['family']} | {g['prompt_kl_mean']:.4f} | "
      f"{b['ratio_to_null_mean']:.2f} | {b['z_mean']:+.1f} | "
      f"{b['direction_consistency']:.3f} | {tb} |")

w(f"\n## B. Same stratum ranked by magnitude-controlled push (ratio to random-direction "
  f"null, layer {L}, alpha={pa})\n")
w("| # | glyph | id | family | ratio | z | prompt KL |")
w("|---|---|---|---|---|---|---|")
for i, g in enumerate(sorted(matched, key=lambda g: -g["by_layer"][L]["ratio_to_null_mean"]), 1):
    b = g["by_layer"][L]
    w(f"| {i} | {g['glyph']} | {g['id']} | {g['family']} | {b['ratio_to_null_mean']:.2f} | "
      f"{b['z_mean']:+.1f} | {g['prompt_kl_mean']:.4f} |")

w("\n## C. Token ladder — what token count alone buys\n")
w(f"Shaded reference: the 4-token matched stratum spans "
  f"{summ['prompt_kl_matched']['min']:.4f} … {summ['prompt_kl_matched']['max']:.4f} "
  f"(median {summ['prompt_kl_matched']['median']:.4f}).\n")
w(f"| glyph | id | prefix tokens | prompt KL | ratio L{L} | top boosted |")
w("|---|---|---|---|---|---|")
for g in ladder:
    b = g["by_layer"][L]
    tb = " ".join(f"`{t}`" for t, _ in g["top_boosted_deepest_layer"][:3])
    w(f"| {g['glyph']} | {g['id']} | {g['n_prefix_tokens']} | {g['prompt_kl_mean']:.4f} | "
      f"{b['ratio_to_null_mean']:.2f} | {tb} |")

w("\n## D. Layer structure\n")
w("`ratio` is against the null **median**. The nonparametric column is the honest one: "
  f"a cell is *0-exceed* when **none** of the {meta['random_controls']} random directions "
  "reached that glyph's KL. The null is right-skewed (mean > median), so the `z` column "
  "elsewhere is a standardized effect size, **not** a p-value.\n")
w("| layer | ratio (median) | consistency (median) | cells 0-exceed | glyphs clean on all 3 targets | 0-exceed per target |")
w("|---|---|---|---|---|---|")
for lay in meta["layers"]:
    s = summ["ratio_to_null_by_layer"][str(lay)]
    per = ", ".join(f"{t} {v}/{summ['n_glyphs']}"
                    for t, v in s["cells_zero_exceedance_per_target"].items())
    w(f"| {lay} | {s['matched_median']:.2f} | {s['consistency_median']:.3f} | "
      f"{s['cells_zero_exceedance']}/{s['n_cells']} | "
      f"**{s['glyphs_clean_all_targets']}/{summ['n_glyphs']}** | {per} |")
_any_clean = any(summ["ratio_to_null_by_layer"][str(lay)]["glyphs_clean_all_targets"]
                 for lay in meta["layers"])
w("\n**" + ("No glyph clears" if not _any_clean else "Some glyphs clear")
  + " the null on all three targets at any layer.** The magnitude-controlled "
  "effect is clean only on the open-ended target at layers 11 and 16 (where the null is "
  "tightest), partly on `planet` at layer 16, and never on `paris`. Section B's ranking is "
  "therefore a *relative* ordering, carried mostly by the open-ended target — not a set of "
  "individually significant results.")

w("\n## E. Family (token-matched stratum)\n")
w("| family | n | prompt KL (median) | ratio (median) |")
w("|---|---|---|---|")
for f, s in sorted(summ["family_medians_matched"].items(),
                   key=lambda kv: -kv[1]["prompt_kl_median"]):
    w(f"| {f} | {s['n']} | {s['prompt_kl_median']:.4f} | {s['ratio_median']:.2f} |")

w("\n## Null distributions\n")
w("| cell | median | mean | sd | max |")
w("|---|---|---|---|---|")
for k, v in meta["null_kl"].items():
    if k.endswith(f"a{pa}"):
        w(f"| {k} | {v['median']:.4f} | {v['mean']:.4f} | {v['sd']:.4f} | {v['max']:.4f} |")

w("\n---\n")
w("The random-direction null is a **size** control, not a semantic control. "
  "Beating it shows a direction is structured; it does not show the structure is meaning. "
  "No causal or semantic claim is authorized by this screen.")

(res / "report.md").write_text("\n".join(out) + "\n", encoding="utf-8")
_text = "\n".join(out)
print(f"wrote {res / 'report.md'} ({len(_text):,} chars)")
