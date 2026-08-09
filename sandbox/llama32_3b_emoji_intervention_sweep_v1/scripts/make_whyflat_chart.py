#!/usr/bin/env python3
"""Self-contained (CSP-safe) chart for the why-flat follow-up.

Panel 1 — the continuum that replaces the deep run's binary split: every glyph's
          absolute mid-network ratio, coloured by UTF-8 byte class, with the
          near-synonym pairs joined so the H1 comparison is read directly.
Panel 2 — the cat paradox: 🐈‍⬛'s direction stays cat-shaped at every depth, yet
          its mid-network efficacy sits on ⬛.

Data embedded inline. var() only inside style attributes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="whyflat_v1")
    ap.add_argument("--out", default=str(ROOT / "chart" / "whyflat_chart.html"))
    args = ap.parse_args()
    res = ROOT / "results"
    meta = json.loads((res / f"{args.tag}_meta.json").read_text(encoding="utf-8"))
    an = json.loads((res / f"{args.tag}_analysis.json").read_text(encoding="utf-8"))
    p1 = {r["id"]: r for r in
          (json.loads(l) for l in
           (res / f"{args.tag}_phase1.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}

    rec = an["ranked"]
    by = {r["id"]: r for r in rec}
    COL = {"E2": "#b45309", "F0": "#2563eb", "ZWJ": "#059669"}

    # ---------------- panel 1: the continuum -------------------------------
    W, H = 900, 470
    ml, mr, mt, mb = 150, 130, 26, 52
    lo, hi = min(r["mid"] for r in rec), max(r["mid"] for r in rec)
    x0, x1 = 2.4, hi * 1.03
    rowh = (H - mt - mb) / len(rec)

    def px(v):
        return ml + (v - x0) / (x1 - x0) * (W - ml - mr)

    g = []
    for t in [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5]:
        g.append(f'<line x1="{px(t):.1f}" y1="{mt}" x2="{px(t):.1f}" y2="{H-mb}" class="grid"/>'
                 f'<text x="{px(t):.1f}" y="{H-mb+18}" class="axis mid">{t:.1f}</text>')

    ypos = {}
    for i, r in enumerate(rec):
        y = mt + rowh * i + rowh / 2
        ypos[r["id"]] = y
        col = COL.get(r["grp"], "#888")
        tip = (f"{r['glyph']} {r['id']} ({r['grp']}, {r['sem']})\n"
               f"mid-network ratio {r['mid']:.2f}   final layer {r['last']:.2f}\n"
               f"peak layer L{r['peak_layer']}   P(concept) {r['p_concept']:.3f}\n"
               f"names it: {p1[r['id']]['greedy_continuation']}")
        g.append(f'<g class="row"><title>{esc(tip)}</title>'
                 f'<line x1="{px(x0):.1f}" y1="{y:.1f}" x2="{px(r["mid"]):.1f}" y2="{y:.1f}" '
                 f'class="stem" style="stroke:{col}"/>'
                 f'<circle cx="{px(r["mid"]):.1f}" cy="{y:.1f}" r="5.5" style="fill:{col}"/>'
                 f'<text x="{ml-34}" y="{y+5:.1f}" class="gl">{esc(r["glyph"])}</text>'
                 f'<text x="{ml-52}" y="{y+4:.1f}" class="rl end">{esc(r["id"])}</text>'
                 f'<text x="{px(r["mid"])+11:.1f}" y="{y+4:.1f}" class="val">{r["mid"]:.2f}</text>'
                 f'</g>')

    # pair connectors
    pairs = {}
    for r in rec:
        if r["pair"] != "-":
            pairs.setdefault(r["pair"], []).append(r)
    for pname, ms in pairs.items():
        e2 = [m for m in ms if m["grp"] == "E2"]
        f0 = [m for m in ms if m["grp"] == "F0"]
        for a in e2:
            for b in f0:
                xa, ya = px(a["mid"]), ypos[a["id"]]
                xb, yb = px(b["mid"]), ypos[b["id"]]
                mx = max(xa, xb) + 46
                g.append(f'<path d="M{xa:.1f},{ya:.1f} C{mx:.1f},{ya:.1f} {mx:.1f},{yb:.1f} '
                         f'{xb:.1f},{yb:.1f}" class="pair"><title>'
                         f'{esc(pname)}: {esc(a["glyph"])} {a["mid"]:.2f} vs '
                         f'{esc(b["glyph"])} {b["mid"]:.2f} ({b["mid"]/a["mid"]:.2f}x)'
                         f'</title></path>')

    # ---------------- panel 2: the cat paradox -----------------------------
    W2, H2 = 900, 300
    m2 = (58, 210, 22, 46)
    zz = an["h2_zwj"]
    NL = meta["num_layers"]

    def px2(L):
        return m2[0] + L / (NL - 1) * (W2 - m2[0] - m2[1])

    def py2(v):
        return H2 - m2[3] - (v - 0.70) / (1.02 - 0.70) * (H2 - m2[2] - m2[3])

    q = []
    for t in [0.7, 0.8, 0.9, 1.0]:
        q.append(f'<line x1="{m2[0]}" y1="{py2(t):.1f}" x2="{W2-m2[1]}" y2="{py2(t):.1f}" '
                 f'class="grid"/><text x="{m2[0]-8}" y="{py2(t)+4:.1f}" class="axis end">{t:.1f}</text>')
    for L in range(0, NL, 4):
        q.append(f'<text x="{px2(L):.0f}" y="{H2-m2[3]+18}" class="axis mid">{L}</text>')
    # curves, with the legend parked at the lower-left so it cannot collide with
    # the bar group on the right
    for li, (key, col, lab) in enumerate((("cos_cat_plain", "#059669", "cos(🐈‍⬛, 🐈)"),
                                          ("cos_cat_face", "#2563eb", "cos(🐈‍⬛, 🐱)"),
                                          ("cos_black_sq", "#b45309", "cos(🐈‍⬛, ⬛)"))):
        pts = " ".join(f"{px2(h['layer']):.1f},{py2(h[key]):.1f}" for h in zz)
        q.append(f'<polyline points="{pts}" class="curve" style="stroke:{col}"/>')
        ly = H2 - m2[3] - 12 - li * 15
        q.append(f'<line x1="{m2[0]+14}" y1="{ly-4:.0f}" x2="{m2[0]+34}" y2="{ly-4:.0f}" '
                 f'class="curve" style="stroke:{col}"/>'
                 f'<text x="{m2[0]+40}" y="{ly:.0f}" class="curvelab" style="fill:{col}">'
                 f'{lab} &rarr; {zz[-1][key]:.2f} at L{NL-1}</text>')

    cats = [("cat_plain", "🐈"), ("cat_face", "🐱"), ("black_cat", "🐈‍⬛"), ("black_sq", "⬛")]
    bx0, bw, bh = W2 - m2[1] + 8, 44, 118
    bmax = max(by[k]["mid"] for k, _ in cats)
    for i, (k, gl) in enumerate(cats):
        v = by[k]["mid"]
        x = bx0 + i * (bw + 4)
        hgt = v / bmax * bh
        col = "#059669" if k in ("cat_plain", "cat_face") else ("#b45309" if k == "black_sq" else "#7c3aed")
        q.append(f'<g><title>{esc(gl)} mid-network ratio {v:.2f}</title>'
                 f'<rect x="{x:.0f}" y="{H2-m2[3]-hgt-24:.0f}" width="{bw}" height="{hgt:.0f}" '
                 f'rx="3" style="fill:{col}"/>'
                 f'<text x="{x+bw/2:.0f}" y="{H2-m2[3]-hgt-30:.0f}" class="val mid">{v:.2f}</text>'
                 f'<text x="{x+bw/2:.0f}" y="{H2-m2[3]-8:.0f}" class="gl mid">{esc(gl)}</text></g>')
    q.append(f'<text x="{bx0+2*(bw+4):.0f}" y="{mt+4}" class="lab mid">mid-network ratio</text>')

    html = f"""<title>Llama-3.2-3B · why are some glyphs flat?</title>
<style>
  :root {{
    color-scheme: light;
    --page:#f7f8fa; --card:#fff; --ink:#16181d; --mid:#5b6270; --faint:#9aa1ad;
    --line:#e3e6ec; --grid:#eef0f4; --accent:#2563eb; --warn:#b45309;
    --shadow:0 1px 3px rgba(16,20,30,.07),0 8px 24px rgba(16,20,30,.05);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      color-scheme: dark;
      --page:#0c0e12; --card:#14171d; --ink:#e9ecf1; --mid:#9aa2b1; --faint:#6b7484;
      --line:#242932; --grid:#1c2029; --accent:#60a5fa; --warn:#fbbf24;
      --shadow:0 1px 3px rgba(0,0,0,.5),0 8px 24px rgba(0,0,0,.35);
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --page:#0c0e12; --card:#14171d; --ink:#e9ecf1; --mid:#9aa2b1; --faint:#6b7484;
    --line:#242932; --grid:#1c2029; --accent:#60a5fa; --warn:#fbbf24;
    --shadow:0 1px 3px rgba(0,0,0,.5),0 8px 24px rgba(0,0,0,.35);
  }}
  body {{ margin:0; padding:34px 22px 60px; background:var(--page); color:var(--ink);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif; }}
  .wrap {{ max-width:960px; margin:0 auto; }}
  .kicker {{ font-size:12px; letter-spacing:.11em; text-transform:uppercase;
    color:var(--accent); font-weight:700; margin-bottom:10px; }}
  h1 {{ font-size:27px; line-height:1.24; margin:0 0 12px; letter-spacing:-.018em; }}
  h2 {{ font-size:17px; margin:30px 0 6px; }}
  .lede, .notes {{ color:var(--mid); max-width:76ch; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:14px 12px 6px; margin:14px 0 22px; box-shadow:var(--shadow); overflow-x:auto; }}
  .cap {{ color:var(--mid); font-size:13px; padding:4px 8px 12px; }}
  svg {{ display:block; max-width:100%; height:auto; }}
  .grid {{ stroke:var(--grid); stroke-width:1; }}
  .stem {{ stroke-width:2; opacity:.5; }}
  .pair {{ fill:none; stroke:var(--faint); stroke-width:1.2; stroke-dasharray:3 3; opacity:.75; }}
  .curve {{ fill:none; stroke-width:2.2; }}
  .curvelab {{ font-size:11px; font-weight:600; }}
  .axis {{ fill:var(--faint); font-size:11px; }}
  .lab {{ fill:var(--mid); font-size:12px; font-weight:600; }}
  .rl {{ fill:var(--mid); font-size:11.5px; }}
  .gl {{ font-size:16px; }}
  .val {{ fill:var(--ink); font-size:11px; font-variant-numeric:tabular-nums; }}
  .mid {{ text-anchor:middle; }} .end {{ text-anchor:end; }}
  .row:hover .stem {{ opacity:1; stroke-width:3.5; }}
  .warnbox {{ border:1px solid var(--warn); border-radius:10px; padding:10px 13px;
    color:var(--mid); font-size:13px; margin:18px 0; }}
  b {{ color:var(--ink); }}
  .key {{ font-size:12.5px; color:var(--mid); padding:0 8px 10px; }}
  .sw {{ display:inline-block; width:10px; height:10px; border-radius:2px;
    margin:0 5px 0 14px; vertical-align:baseline; }}
</style>
<div class="wrap">
  <div class="kicker">GlyphProbe · pre-causal screen · out-of-contract · follow-up</div>
  <h1>Why are ⬛ 🥺 ⛵ 🐈‍⬛ flat through the middle of the network?</h1>
  <p class="lede">Three hypotheses, all falsifiable. Two are refuted outright, one
  survives only partly — and the run overturns the earlier claim that the panel splits
  cleanly in two.</p>

  <div class="warnbox"><b>Out of contract.</b> Exploratory sandbox run on the real bf16
  weights. Not the sealed v2 experiment, no causal or semantic claim
  (<code>pre-causal-activation-screen</code>). No holdout bank.</div>

  <h2>1 · A continuum, not a split</h2>
  <p class="notes">Absolute mid-network ratio (max over L10-19) — how hard a glyph's
  direction pushes where the model still has computation left to do. Dashed arcs join the
  <b>near-synonym pairs that differ only in UTF-8 byte class</b>. Spearman(is 3-byte,
  mid ratio) = <b>{an['spearman_e2_mid']:+.2f}</b>.</p>
  <div class="card">
    <div class="key"><span class="sw" style="background:{COL['E2']}"></span>3-byte (U+26xx/2Bxx)
      <span class="sw" style="background:{COL['F0']}"></span>4-byte (emoji planes)
      <span class="sw" style="background:{COL['ZWJ']}"></span>ZWJ compound</div>
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="mid-network ratio per glyph">
      {''.join(g)}
      <text x="{(W-mr+ml)/2:.0f}" y="{H-8}" class="lab mid">mid-network ratio (max over L10-19)</text>
    </svg>
    <div class="cap">Range {lo:.2f} → {hi:.2f}; the largest gap anywhere in the sorted list is
      only <b>{an['split']['gap']:.2f}</b>. The deep run's "no exceptions" two-way split was a
      property of a 13-glyph panel with no intermediate cases.</div>
  </div>

  <h2>2 · The cat paradox</h2>
  <p class="notes">🐈‍⬛ tokenises as 🐈's tokens + ZWJ + ⬛'s tokens. Its direction stays on
  the <b>cat</b> side at every depth — and the margin widens with depth — yet its
  mid-network efficacy lands exactly on <b>⬛</b>. Direction similarity and causal efficacy
  come apart.</p>
  <div class="card">
    <svg viewBox="0 0 {W2} {H2}" role="img" aria-label="black cat direction cosines by layer">
      {''.join(q)}
      <text x="{(W2-m2[1]+m2[0])/2:.0f}" y="{H2-6}" class="lab mid">layer (resid_post)</text>
      <text x="13" y="{H2/2:.0f}" class="lab mid" transform="rotate(-90 13 {H2/2:.0f})">cosine</text>
    </svg>
    <div class="cap">Left: cosine of 🐈‍⬛'s direction to each part, per layer. Right: the
      mid-network ratio each glyph actually achieves.</div>
  </div>

  <p class="notes"><b>What this does not show.</b> A pre-causal activation screen. Four
  near-synonym pairs is thin evidence and the synonyms are loose (⛵ sailboat vs 🚢
  passenger ship, ☕ coffee vs 🍵 tea, ✈️ aeroplane vs 🚁 helicopter); training-set frequency
  is uncontrolled and remains a live alternative explanation. The random-direction null is
  a size control, not a semantic control.</p>
</div>
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
