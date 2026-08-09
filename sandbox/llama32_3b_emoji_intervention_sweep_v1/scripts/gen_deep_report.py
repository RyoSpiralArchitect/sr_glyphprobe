#!/usr/bin/env python3
"""Render results/deep_report.md from the deep-diagnostic outputs.

All tables are computed from the records. The surrounding prose quotes a few
numbers as literals (they are the ones the narrative is about); if you rerun
with a different panel, alpha or null size, re-read the prose as well as the
tables."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
res = ROOT / "results"
TAG = "deep_v1"

meta = json.loads((res / f"{TAG}_meta.json").read_text(encoding="utf-8"))
an = json.loads((res / f"{TAG}_analysis.json").read_text(encoding="utf-8"))
spec = json.loads((res / f"{TAG}_specificity_matrix.json").read_text(encoding="utf-8"))
p2 = [json.loads(l) for l in (res / f"{TAG}_phase2.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
sweep = {json.loads(l)["id"]: json.loads(l)
         for l in (res / "sweep_v1_glyph_summary.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}


def rank(v):
    a = np.asarray(v, float); o = a.argsort(); r = np.empty(len(a)); r[o] = np.arange(1, len(a) + 1)
    for u in np.unique(a):
        m = a == u
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def sp(x, y):
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean()
    d = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / d) if d else float("nan")


o = []
w = o.append
nn = an["phase1"]["n_null"]
A = meta["alpha"]
L0 = meta["deep_layer"]

w("# Deep diagnostic — focused panel, large controls (out of contract)\n")
w("Follow-up to [the 50-glyph sweep](report.md), targeting its two weaknesses: only 3 "
  "injection targets and only 24 random directions. See [README](../README.md) for the "
  "boundary. Claim stage `pre-causal-activation-screen`, `causal_claim_authorized: false`. "
  "No holdout bank used.\n")

w("## Run\n")
w(f"- {len(meta['panel'])} glyphs (strong / high-prompt / weak-control / ZWJ), "
  f"{len(meta['targets'])} injection targets, alpha = {A}")
ph = {p["phase"]: p for p in meta["phases_run"]}
for i in sorted(ph):
    w(f"- phase {i}: {ph[i]['rows']} rows, {ph[i]['elapsed_s']:.0f} s")
w(f"- total {meta['total_elapsed_s']:.0f} s on an M4 (MPS/FP32)\n")

# ---------------------------------------------------------------- phase 1
w("## Phase 1 — does it generalise, and at what resolution?\n")
w(f"{nn} random directions per target puts the nonparametric floor at "
  f"p = 1/{nn+1} = {1/(nn+1):.4f} (sweep_v1 could only reach 1/25 = 0.04).\n")
w("| target | entropy | top-2 margin | null median | ratio median | glyphs clearing null |")
w("|---|---|---|---|---|---|")
for t in sorted(an["phase1"]["targets"], key=lambda t: -t["entropy"]):
    w(f"| `{t['target']}` | {t['entropy']:.2f} | {t['margin']:.2f} | {t['null_median']:.4f} | "
      f"{t['ratio_median']:.2f} | **{t['clean']}/{t['n_glyphs']}** |")
w(f"\n- Spearman(entropy, glyphs clearing null) = **{an['phase1']['spearman_entropy_clean']:+.3f}**")
w(f"- Spearman(entropy, ratio median) = {an['phase1']['spearman_entropy_ratio']:+.3f}")
w(f"- Spearman(top-2 margin, ratio median) = {an['phase1']['spearman_margin_ratio']:+.3f}\n")
w("Six of twelve targets are cleared by **all 13 glyphs**. sweep_v1's \"clean only on the "
  "open-ended target\" was a target-count and null-size artefact, not a property of the "
  "effect. Detectability is a property of the *target*: sharp factual prompts "
  "(`paris`, `planet`, `freeze`) hide the effect because a random push moves them a lot too.\n")

w("| glyph | group | ratio median | clean | min p | argmax flips |")
w("|---|---|---|---|---|---|")
for g in an["phase1"]["glyphs"]:
    w(f"| {g['glyph']} `{g['id']}` | {g['group']} | **{g['ratio_median']:.2f}** | "
      f"{g['clean']}/{g['n_targets']} | {g['min_p']:.4f} | {g['flips']} |")

strong = [g for g in an["phase1"]["glyphs"] if g["group"] == "strong"]
weak = [g for g in an["phase1"]["glyphs"] if g["group"] == "weak"]
w(f"\nstrong group ratio median **{np.median([g['ratio_median'] for g in strong]):.2f}** vs "
  f"weak-control **{np.median([g['ratio_median'] for g in weak]):.2f}**. But the *binary* "
  "test saturates: the weak controls clear the null on 6-7 of 12 targets too. "
  "**Significance and effect size come apart here** — the ranking has to be read from the "
  "ratio, not from whether a cell is significant.\n")

ids = [g["id"] for g in an["phase1"]["glyphs"] if g["id"] in sweep]
_sl = str(L0) if str(L0) in next(iter(sweep.values()))["by_layer"] else None
if _sl is None:
    raise SystemExit(f"deep layer L{L0} is absent from the sweep summary "
                     f"({sorted(next(iter(sweep.values()))['by_layer'])}); "
                     "cannot compute the replication correlation")
old = [sweep[i]["by_layer"][_sl]["ratio_to_null_mean"] for i in ids]
new = [next(g["ratio_median"] for g in an["phase1"]["glyphs"] if g["id"] == i) for i in ids]
w(f"**Replication.** sweep_v1 (3 targets, 24 nulls) vs this run (12 targets, {nn} nulls), "
  f"same 13 glyphs at L{L0}: Spearman = **{sp(old, new):+.3f}**. The ordering holds; "
  "individual positions move (🚗 4.89→3.52, 🐱 3.63→4.49).\n")

# ---------------------------------------------------------------- phase 2
w("## Phase 2 — layer profile over every layer\n")
by = {}
for r in p2:
    by.setdefault(r["id"], {})[r["layer"]] = r
w("| glyph | group | peak layer | peak ratio | mid-network max (L10-19) | final layer L27 | shape |")
w("|---|---|---|---|---|---|---|")
mids, lasts = [], []
for p in an["phase2"]["profiles"]:
    prof = p["profile"]
    mid = max(prof[10:20]); last = prof[-1]
    mids.append(mid); lasts.append(last)
    shape = "**mid-peak**" if mid > last else "last-peak"
    w(f"| {p['glyph']} `{p['id']}` | {p['group']} | L{p['peak_layer']} | {p['peak_ratio']:.2f} | "
      f"{mid:.2f} | {last:.2f} | {shape} |")
w("\n> ⚠️ **Superseded by [the why-flat follow-up](whyflat_report.md).** This section "
  "originally claimed the split was exhaustive and exception-free. That was a property "
  "of *this 13-glyph panel*, which contains no intermediate cases. Across 19 glyphs the "
  "mid-network ratio is a **continuum** (2.71 → 5.66, largest gap 0.73), and the binary "
  "label is driven by the *final-layer* value rather than by mid-network engagement — it "
  "mislabels ☕ (mid 2.87, called mid-peak) and 🚢 (mid 3.72, called last-peak). Read the "
  "mid-network column, not the label.\n")
w("The split as it falls out on this panel:\n")
w("- **mid-peak** (🍺 🍕 🍣 🍔 🌍 🚗 🍜 🐶 🐱): peak at **L14-16**, ratio 3.7-5.7, "
  "falling to 1.3-2.1 by the final layer.")
w("- **last-peak** (⬛ 🥺 ⛵ 🐈‍⬛): flat 2.7-3.1 through the middle, spiking to 3.8-6.4 at L27.\n")
w("L27 is the last layer: its `resid_post` feeds the final norm and the unembedding, so a "
  "perturbation there is close to editing the logits directly. A high ratio at L27 means "
  "the direction is *token-like* (it lives where real token representations live); a high "
  "ratio at L14-16 means the direction engages the model's remaining computation. These "
  "are different claims, and ⬛'s peak ratio of 6.43 — the largest number in the whole run "
  "— is entirely of the first kind.\n")
w(f"At **L0 every glyph sits at ratio 0.05**, i.e. a real emoji direction is ~20x *less* "
  "disruptive than a matched random one at the embedding layer. Direction consistency runs "
  f"the other way: {an['phase2']['consistency_by_layer']['0']:.3f} at L0 falling to "
  f"{an['phase2']['consistency_by_layer'][str(max(int(k) for k in an['phase2']['consistency_by_layer']))]:.3f} "
  "at the last layer. Where the direction is most reproducible it does the least, and "
  "vice versa.\n")

# ---------------------------------------------------------------- phase 3
w("## Phase 3 — specificity and sign flip\n")
w("Probe words were written by hand per glyph, **not** harvested from the model's own "
  "top-boosted lists, so the diagonal is not selected-on.\n")
_pid = {k: set(v) for k, v in spec["probe_ids"].items()}
_keys = list(spec["matrix"])
_shared = {(a, b): sorted(_pid[a] & _pid[b])
           for i, a in enumerate(_keys) for b in _keys[i + 1:] if _pid[a] & _pid[b]}
_naive = _excl = 0
for _k0 in _keys:
    _v = spec["matrix"][_k0]
    _off = {k: x for k, x in _v.items() if k != _k0}
    if _v[_k0] >= max(_off.values()):
        _naive += 1
    _ok = {k: x for k, x in _off.items() if not (_pid[k] & _pid[_k0])}
    if not _ok or _v[_k0] >= max(_ok.values()):
        _excl += 1
w(f"- own probe group largest (instance level): **{_naive}/{spec['n']}**")
w(f"- own *category block* largest: **{spec['own_block_wins']}/{spec['n']}**")
w(f"- sign-flip antisymmetry `cos(probe_delta(+d), -probe_delta(-d))`: "
  f"median {spec['antisymmetry_median']:+.3f}, min {spec['antisymmetry_min']:+.3f}\n")
if _shared:
    w("\n**Probe-group overlap.** Truncating each probe word to its first token makes "
      "some hand-written groups share ids — "
      + "; ".join(f"`{a}`/`{b}` share {len(v)} of {len(_pid[a])}" for (a, b), v in _shared.items())
      + " (black cats are cats, so this is semantically right but makes an "
      "instance-level diagonal ambiguous). Excluding every competitor column that "
      f"shares a token with the row leaves the count **unchanged at {_excl}/{spec['n']}**, "
      "so the conclusion does not depend on the overlap.\n")
w("| injected | food | animal | vehicle | other | own block | margin over best other |")
w("|---|---|---|---|---|---|---|")
gmap = {g["id"]: g["glyph"] for g in an["phase1"]["glyphs"]}
for k, v in spec["block_view"].items():
    bm = v["block_means"]
    w(f"| {gmap.get(k,'')} `{k}` | {bm['food']:+.2f} | {bm['animal']:+.2f} | "
      f"{bm['vehicle']:+.2f} | {bm['other']:+.2f} | `{v['own_block']}` | "
      f"{v['own_minus_best_other']:+.2f}{' ✅' if v['win'] else ''} |")
w("\n**The direction carries a category, not an instance.** 🍣 boosts *burger* probes "
  "(+2.95) more than *sushi* probes (+1.86); 🍺 boosts *burger* (+2.30) more than *beer* "
  "(+1.40). At block level the food glyphs beat the next-best block by +1.15 to +1.65 and "
  "🚗 beats it by +1.32. The failures are informative: 🥺 (own block −0.17) and ⛵ (−0.48) "
  "carry no category signal at all, and ⛵ scores −0.48 on *vehicle* where 🚗 scores +1.27 "
  "— sharing a category with a strong glyph buys nothing.\n")
w("Antisymmetry of only ~0.63 means +d and −d are **not** mirror images at alpha = "
  f"{A}: the response is already outside the linear regime, so the probe deltas should be "
  "read as directional evidence, not as a linear readout.\n")

# ---------------------------------------------------------------- phase 4
w("## Phase 4 — does a better direction estimate help?\n")
c = an["phase4"]["median_consistency_by_n_wrappers"]
w("| extraction wrappers | " + " | ".join(c) + " |")
w("|---" * (len(c) + 1) + "|")
w("| median direction consistency | " + " | ".join(f"{v:.3f}" for v in c.values()) + " |")
w(f"\nConsistency saturates around {max(c.values()):.2f} — tripling the wrappers buys almost "
  f"nothing, and the median effect *falls* by {abs(an['phase4']['median_ratio_gain']):.2f} "
  "(cos between the 4-wrapper and 12-wrapper directions is ~0.87). Averaging more contexts "
  "trades a little effect size for generality; the strong glyphs lose "
  "(🍜 −0.37, 🐶 −0.43) and the weak controls gain (⛵ +0.31, ⬛ +0.23), which is what "
  "regression toward a context-general mean looks like. **4 wrappers was already enough.**\n")

# ---------------------------------------------------------------- limits
w("## Limitations\n")
w("- One model, one position (`last_nonpad`), one site (`resid_post`), one strength for "
  "phases 1/3/4. The layer profile is the only dimension swept exhaustively.")
w("- The category blocks are hand-drawn and one assignment is poor: 🌍 `earth` was placed "
  "in a catch-all `other` block with ⬛ and 🥺, so its block test fails even though its "
  "layer profile is squarely mid-peak. Treat the 🌍 block result as an artefact of the "
  "grouping, not a finding.")
w("- Probe groups are 6 hand-picked words each, first token of `' <word>'` only.")
w("- The random-direction null is a **size** control, not a semantic control. Beating it "
  "shows a direction is structured, not that the structure is meaning.")
w("- Non-canonical provenance (non-frozen libraries, `orjson` stand-in). Weights are "
  "byte-identical to the sealed v2 artifact; nothing else here is comparable to a "
  "canonical run.")

(res / "deep_report.md").write_text("\n".join(o) + "\n", encoding="utf-8")
print(f"wrote {res / 'deep_report.md'}")
