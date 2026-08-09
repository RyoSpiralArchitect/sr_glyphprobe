#!/usr/bin/env python3
"""Render results/whyflat_report.md.

All tables are computed from the records; the prose quotes a handful of them as
literals. Re-read the prose too if you rerun with a different panel."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
TAG = "whyflat_v1"

meta = json.loads((res / f"{TAG}_meta.json").read_text(encoding="utf-8"))
an = json.loads((res / f"{TAG}_analysis.json").read_text(encoding="utf-8"))
p1 = [json.loads(l) for l in (res / f"{TAG}_phase1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
deep = json.loads((res / "deep_v1_analysis.json").read_text(encoding="utf-8"))

o = []
w = o.append
rec = an["ranked"]
by_id = {r["id"]: r for r in rec}
know = {r["id"]: r for r in p1}

w("# Why are some glyphs flat through the middle of the network? (out of contract)\n")
w("Follow-up to [the deep diagnostic](deep_report.md), which found ⬛ 🥺 ⛵ 🐈‍⬛ to be the "
  "only glyphs without a mid-network peak. Negative cases are where a mechanism usually "
  "shows itself, so this run takes those four apart. See [README](../README.md) for the "
  "boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. "
  "No holdout bank used.\n")

w("## Design\n")
w(f"{len(meta['panel'])} glyphs, {meta['num_layers']} layers, {len(meta['targets'])} injection "
  f"targets, alpha = {meta['alpha']}, {meta['nulls']} random directions per (layer, target). "
  "The panel is built around **near-synonym pairs that differ in UTF-8 byte class** "
  "(⛵/🚢, ☕/🍵, ⬛/🟥, ✈️/🚁), the **ZWJ decomposition set** (🐈‍⬛ / 🐈 / 🐱 / ⬛), an "
  "**emotion set** (🥺 / 😢 / 😭 / 🤔) and three anchors known to peak mid-network "
  "(🍕 🚗 🐶).\n")

w("Three hypotheses, each made falsifiable:\n")
w("| | hypothesis | test | verdict |")
w("|---|---|---|---|")
w("| **H1** | it is the UTF-8 byte class, not the meaning | near-synonym pairs differing only in encoding | **partly supported** |")
w("| **H2** | 🐈‍⬛'s direction is dominated by its ⬛ tail | cosine of 🐈‍⬛'s direction to 🐈 vs ⬛, per layer | **refuted (but a new puzzle)** |")
w("| **H3** | the model has no concept for these glyphs | ask it to name them | **refuted** |")

w("\n## Metric correction\n")
w("The run script classified profiles with a binary label (mid-network max > final-layer "
  "value). **That label is wrong for this question**: it is driven by the final-layer "
  "value, which varies for reasons unrelated to mid-network engagement. It calls ☕ a "
  f"mid-peak (mid {by_id['coffee']['mid']:.2f}) and 🚢 a last-peak (mid {by_id['ship']['mid']:.2f}) — "
  "i.e. it ranks a weaker glyph above a stronger one. Everything below uses the "
  "**absolute mid-network ratio** (max over L10-19), which is what actually answers "
  "\"does this direction engage the middle of the network\". `scripts/analyze_whyflat.py` "
  "carries the same note.\n")

# ------------------------------------------------------------------ H3
w("## H3 — does the model even know these glyphs? Refuted.\n")
w("| glyph | id | P(concept) | best rank | greedy continuation of \"The emoji &lt;g&gt; is a picture of a\" |")
w("|---|---|---|---|---|")
for r in sorted(p1, key=lambda r: -r["p_concept_mean"]):
    w(f"| {r['glyph']} | `{r['id']}` | {r['p_concept_mean']:.4f} | {r['rank_concept_best']} | "
      f"`{r['greedy_continuation']}` |")
w("\nEvery glyph's correct concept is the **top-1 or top-2** next token, the four flat ones "
  "included: ⬛ continues `' black square with a white border. It'`, 🐈‍⬛ continues "
  "`' black cat with a white face and a'`. The model knows them. "
  f"Spearman(P(concept), mid ratio) = **{an['spearman_pconcept_mid']:+.3f}** — a weak "
  "association, nowhere near an explanation.\n")

# ------------------------------------------------------------------ ranking
w("## The picture that replaces the binary split\n")
w("| # | glyph | id | byte class | semantic | mid (L10-19) | final L27 | peak layer |")
w("|---|---|---|---|---|---|---|---|")
for i, r in enumerate(rec, 1):
    w(f"| {i} | {r['glyph']} | `{r['id']}` | {r['grp']} | {r['sem']} | **{r['mid']:.2f}** | "
      f"{r['last']:.2f} | L{r['peak_layer']} |")
mids = [r["mid"] for r in rec]
w(f"\nThe mid-network ratio is a **continuum** from {min(mids):.2f} to {max(mids):.2f}; the "
  f"largest gap anywhere in the sorted list is only {an['split']['gap']:.2f}. "
  "**This overturns the deep diagnostic's claim that the panel splits cleanly with no "
  "exceptions** — that was a property of a 13-glyph panel with no intermediate cases, not "
  "of the model.\n")

# ------------------------------------------------------------------ H1
w("## H1 — UTF-8 byte class. Partly supported.\n")
w("3-byte glyphs (U+26xx / U+2Bxx, the legacy dingbat and geometric-shape blocks, leading "
  "byte-token 158) versus 4-byte emoji-plane glyphs (leading byte-token 9468):\n")
w("| pair | 3-byte (E2) | mid | 4-byte (F0) | mid | F0/E2 |")
w("|---|---|---|---|---|---|")
pairs = {}
for r in rec:
    if r["pair"] != "-":
        pairs.setdefault(r["pair"], []).append(r)
qs = []
for pname, ms in pairs.items():
    e2 = [m for m in ms if m["grp"] == "E2"]
    f0 = [m for m in ms if m["grp"] == "F0"]
    for a in e2:
        for b in f0:
            q = b["mid"] / a["mid"]; qs.append(q)
            w(f"| {pname} | {a['glyph']} `{a['id']}` | {a['mid']:.2f} | {b['glyph']} "
              f"`{b['id']}` | {b['mid']:.2f} | **{q:.2f}** |")
w(f"\nThree of four pairs put the 4-byte member higher (median {np.median(qs):.2f}x). The "
  "exception is the **abstract** pair — two featureless squares, where both sit at the "
  "floor (⬛ 3.00, 🟥 2.96). Overall "
  f"Spearman(is 3-byte, mid ratio) = **{an['spearman_e2_mid']:+.3f}**, and "
  f"Spearman(token count, mid ratio) = {an['spearman_ntokens_mid']:+.3f}, so this is not "
  "token count in disguise.\n")
_bp = pairs.get("boat", [])
_be = next((m for m in _bp if m["grp"] == "E2"), None)
_bf = next((m for m in _bp if m["grp"] == "F0"), None)
boat_ratio = (_bf["mid"] / _be["mid"]) if (_be and _bf) else float("nan")
e2_all = [r for r in rec if r["grp"] == "E2"]
w(f"All {len(e2_all)} 3-byte glyphs (⛵ ☕ ⚓ ⬛ ✈️) land in the bottom half; none reaches "
  "the top. But three 4-byte glyphs (🥺 🤔 🟥) are just as low, so being 3-byte looks "
  "**sufficient but not necessary** for a weak mid-network effect on this panel.\n")
w("The most likely reading is that byte class is a *proxy*: the U+26xx/U+2Bxx blocks are "
  "full of abstract symbols, and abstractness is doing part of the work. The pairs argue "
  "against that being the whole story — ⛵ and 🚢 are both concrete boats and still differ "
  f"{boat_ratio:.2f}x — but four loose near-synonyms is thin evidence. Treat H1 as "
  "suggestive.\n")

# ------------------------------------------------------------------ H2
w("## H2 — is 🐈‍⬛ dragged down by its ⬛ tail? Refuted, and it leaves a better puzzle.\n")
w("🐈‍⬛ tokenises as `[9468, 238, 230] + [102470] + [158, 105, 249]` — literally 🐈's tokens, "
  "ZWJ, then ⬛'s tokens. But its residual direction stays on the cat side at every depth:\n")
w("| layer | cos(🐈‍⬛, 🐈) | cos(🐈‍⬛, ⬛) | margin |")
w("|---|---|---|---|")
for h in an["h2_zwj"]:
    w(f"| {h['layer']} | {h['cos_cat_plain']:.3f} | {h['cos_black_sq']:.3f} | "
      f"{h['cos_cat_plain']-h['cos_black_sq']:+.3f} |")
c = {k: by_id[k]["mid"] for k in ("cat_plain", "cat_face", "black_cat", "black_sq")}
w(f"\nThe margin *widens* with depth (+0.00 at L0 to "
  f"{an['h2_zwj'][-1]['cos_cat_plain']-an['h2_zwj'][-1]['cos_black_sq']:+.3f} at the last "
  "layer). So the direction is not being replaced by ⬛'s.\n")
w("And yet the efficacy — the mid-network ratio — collapses to exactly ⬛'s level:\n")
w("| 🐈 cat | 🐱 cat face | 🐈‍⬛ black cat | ⬛ black square |")
w("|---|---|---|---|")
w(f"| **{c['cat_plain']:.2f}** | **{c['cat_face']:.2f}** | **{c['black_cat']:.2f}** | "
  f"**{c['black_sq']:.2f}** |")
w("\n**Both plain cats engage the middle of the network; the ZWJ compound does not, even "
  "though its direction is still cat-shaped and the model still names it \"black cat\".** "
  "Direction similarity and causal efficacy come apart. Whatever ZWJ composition costs, it "
  "is not \"the direction becomes the last component\".\n")
w("Next step for this: extract the direction at each *token position* of 🐈‍⬛ (the 🐈 tokens, "
  "the ZWJ token, the ⬛ tokens) instead of only at `last_nonpad` of the wrapper, and see "
  "where the efficacy is lost.\n")

# ------------------------------------------------------------------ other
w("## Other things this run settles\n")
w(f"- **Not \"emotions are flat\".** 😢 ({by_id['crying']['mid']:.2f}) and 😭 "
  f"({by_id['sob']['mid']:.2f}) peak mid-network; 🥺 ({by_id['pleading']['mid']:.2f}) and 🤔 "
  f"({by_id['thinking']['mid']:.2f}) do not. Within one semantic family the spread is "
  f"{by_id['crying']['mid']/by_id['pleading']['mid']:.1f}x.")
w(f"- **Not token count.** Spearman(n_tokens, mid ratio) = {an['spearman_ntokens_mid']:+.3f}.")
w("- **Replication.** ⛵, ⬛, 🥺, 🐈‍⬛, 🍕 and 🚗 reproduce their deep-diagnostic mid and "
  "final values exactly (same seeds, same config), so the two runs are directly comparable.")

w("\n## Limitations\n")
w("- Four near-synonym pairs is thin, and the synonyms are loose (⛵ sailboat vs 🚢 "
  "passenger ship; ☕ coffee vs 🍵 tea; ✈️ aeroplane vs 🚁 helicopter). Training-set "
  "frequency is uncontrolled and is a live alternative explanation for every H1 result.")
w("- `P(concept)` uses a different hand-written word list per glyph, so the absolute "
  "probabilities are not strictly comparable across glyphs; the rank (1 or 2 for all 19) "
  "is the robust part.")
w("- One model, one position (`last_nonpad`), one site (`resid_post`), one strength.")
w("- The random-direction null is a **size** control, not a semantic control.")
w("- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). The weights are "
  "byte-identical to the sealed v2 artifact; nothing else here is comparable to a "
  "canonical run.")

(res / "whyflat_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'whyflat_report.md'}")
