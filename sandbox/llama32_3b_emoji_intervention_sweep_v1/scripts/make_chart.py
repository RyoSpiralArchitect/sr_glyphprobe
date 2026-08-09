#!/usr/bin/env python3
"""Render the per-glyph sweep as a self-contained (CSP-safe) HTML chart.

Panel 1 — token-matched stratum: prompt-level effect (x) vs magnitude-controlled
          causal push (y). y is the ratio to the *median* of the matched
          random-direction null, so y=1 is parity with that median — NOT a
          significance threshold. The null is right-skewed; the page carries the
          nonparametric exceedance counts, which are the honest statement.
Panel 2 — token ladder: the same prompt-level effect against prefix token count,
          i.e. how much of panel 1's x axis is simply "more tokens".

Data is embedded inline (no fetch, no external asset). var() is used only
inside style attributes, never as an SVG presentation attribute.
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
    ap.add_argument("--tag", default="sweep_v1")
    ap.add_argument("--layer", default=None, help="layer for the y axis (default: deepest)")
    ap.add_argument("--out", default=str(ROOT / "chart" / "sweep_chart.html"))
    args = ap.parse_args()

    res = ROOT / "results"
    meta = json.loads((res / f"{args.tag}_meta.json").read_text(encoding="utf-8"))
    summ = json.loads((res / f"{args.tag}_summary.json").read_text(encoding="utf-8"))
    glyphs = [json.loads(l) for l in
              (res / f"{args.tag}_glyph_summary.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]

    L = args.layer or str(meta["layers"][-1])
    pa = meta["primary_alpha"]

    matched = [g for g in glyphs if g["stratum"] == "matched"]
    ladder = sorted([g for g in glyphs if g["stratum"] == "ladder"],
                    key=lambda g: g["n_prefix_tokens"])

    pts = [{"g": g["glyph"], "id": g["id"], "fam": g["family"],
            "tok": g["n_prefix_tokens"],
            "x": g["prompt_kl_mean"],
            "y": g["by_layer"][L]["ratio_to_null_mean"],
            "z": g["by_layer"][L]["z_mean"],
            "cons": g["by_layer"][L]["direction_consistency"],
            "top": [t for t, _ in g["top_boosted_deepest_layer"][:3]]}
           for g in matched]
    lad = [{"g": g["glyph"], "id": g["id"], "tok": g["n_prefix_tokens"],
            "x": g["prompt_kl_mean"],
            "y": g["by_layer"][L]["ratio_to_null_mean"]} for g in ladder]

    # ---- panel 1 geometry ---------------------------------------------------
    W, H = 900, 470
    ml, mr, mt, mb = 62, 24, 20, 46
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts] + [1.0]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    xpad = (x1 - x0) * 0.08 or 0.01
    ypad = (y1 - y0) * 0.10 or 0.1
    x0, x1 = x0 - xpad, x1 + xpad
    y0, y1 = y0 - ypad, y1 + ypad

    def px(v):
        return ml + (v - x0) / (x1 - x0) * (W - ml - mr)

    def py(v):
        return H - mb - (v - y0) / (y1 - y0) * (H - mt - mb)

    def ticks(a, b, n=5):
        step = (b - a) / n
        return [a + step * i for i in range(n + 1)]

    marks = []
    for p in pts:
        cx, cy = px(p["x"]), py(p["y"])
        tip = (f"{p['g']} {p['id']} ({p['fam']}, {p['tok']} tok)\n"
               f"prompt KL {p['x']:.4f}\nratio to null {p['y']:.2f}  z {p['z']:+.1f}\n"
               f"direction consistency {p['cons']:.3f}\n"
               f"boosts: {' '.join(repr(t) for t in p['top'])}")
        marks.append(
            f'<g class="pt"><title>{esc(tip)}</title>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="13" class="halo"/>'
            f'<text x="{cx:.1f}" y="{cy:.1f}" class="glyph">{esc(p["g"])}</text></g>')

    xt = ticks(x0, x1)
    yt = ticks(y0, y1)
    grid = "".join(
        f'<line x1="{px(t):.1f}" y1="{mt}" x2="{px(t):.1f}" y2="{H-mb}" class="grid"/>'
        f'<text x="{px(t):.1f}" y="{H-mb+18}" class="axis mid">{t:.2f}</text>' for t in xt)
    grid += "".join(
        f'<line x1="{ml}" y1="{py(t):.1f}" x2="{W-mr}" y2="{py(t):.1f}" class="grid"/>'
        f'<text x="{ml-9}" y="{py(t)+4:.1f}" class="axis end">{t:.1f}</text>' for t in yt)
    parity = (f'<line x1="{ml}" y1="{py(1.0):.1f}" x2="{W-mr}" y2="{py(1.0):.1f}" class="parity"/>'
              f'<text x="{W-mr-6}" y="{py(1.0)-7:.1f}" class="parity-lab end">'
              f'random-direction parity (ratio = 1)</text>')

    # ---- panel 2 geometry ---------------------------------------------------
    W2, H2 = 900, 250
    ml2, mr2, mt2, mb2 = 62, 24, 18, 46
    lx = [d["tok"] for d in lad] + [4]
    ly = [d["x"] for d in lad] + [summ["prompt_kl_matched"]["median"]]
    lx0, lx1 = min(lx) - 0.8, max(lx) + 0.8
    ly0, ly1 = 0.0, max(ly) * 1.12

    def px2(v):
        return ml2 + (v - lx0) / (lx1 - lx0) * (W2 - ml2 - mr2)

    def py2(v):
        return H2 - mb2 - (v - ly0) / (ly1 - ly0) * (H2 - mt2 - mb2)

    med = summ["prompt_kl_matched"]["median"]
    band = (f'<rect x="{px2(3.2):.1f}" y="{py2(summ["prompt_kl_matched"]["max"]):.1f}" '
            f'width="{px2(4.8)-px2(3.2):.1f}" '
            f'height="{py2(summ["prompt_kl_matched"]["min"])-py2(summ["prompt_kl_matched"]["max"]):.1f}" '
            f'class="band"/>'
            f'<line x1="{px2(3.2):.1f}" y1="{py2(med):.1f}" x2="{px2(4.8):.1f}" '
            f'y2="{py2(med):.1f}" class="bandmed"/>')
    def _ladder_mark(d):
        title = "{} {} — {} tokens, prompt KL {:.4f}".format(
            d["g"], d["id"], d["tok"], d["x"])
        return (f'<g class="pt"><title>{esc(title)}</title>'
                f'<circle cx="{px2(d["tok"]):.1f}" cy="{py2(d["x"]):.1f}" r="13" class="halo"/>'
                f'<text x="{px2(d["tok"]):.1f}" y="{py2(d["x"]):.1f}" class="glyph">'
                f'{esc(d["g"])}</text></g>')

    lmarks = "".join(_ladder_mark(d) for d in lad)
    lgrid = "".join(
        f'<line x1="{px2(t):.1f}" y1="{mt2}" x2="{px2(t):.1f}" y2="{H2-mb2}" class="grid"/>'
        f'<text x="{px2(t):.1f}" y="{H2-mb2+18}" class="axis mid">{t}</text>'
        for t in sorted({d["tok"] for d in lad} | {4}))
    lygrid = "".join(
        f'<line x1="{ml2}" y1="{py2(t):.1f}" x2="{W2-mr2}" y2="{py2(t):.1f}" class="grid"/>'
        f'<text x="{ml2-9}" y="{py2(t)+4:.1f}" class="axis end">{t:.1f}</text>'
        for t in [ly0 + (ly1 - ly0) * i / 4 for i in range(5)])

    rho_tok = summ["spearman_tokens_vs_prompt_kl_all"]
    rho_pair = summ["spearman_promptkl_vs_ratio_matched"]

    # every target's clear-count is looked up; none is asserted as a literal, so a
    # rerun that changes one cannot leave a stale zero next to a computed sibling
    _clear = summ["ratio_to_null_by_layer"][L]["cells_zero_exceedance_per_target"]
    clear_open = _clear.get("openended", 0)
    clear_planet = _clear.get("planet", 0)
    clear_paris = _clear.get("paris", 0)

    rows = "".join(
        f"<tr><td>{esc(g['glyph'])}</td><td>{esc(g['id'])}</td><td>{esc(g['family'])}</td>"
        f"<td class=n>{g['n_prefix_tokens']}</td>"
        f"<td class=n>{g['prompt_kl_mean']:.4f}</td>"
        f"<td class=n>{g['by_layer'][L]['ratio_to_null_mean']:.2f}</td>"
        f"<td class=n>{g['by_layer'][L]['z_mean']:+.1f}</td>"
        f"<td class=n>{g['by_layer'][L]['direction_consistency']:.3f}</td>"
        f"<td>{esc(' '.join(repr(t) for t, _ in g['top_boosted_deepest_layer'][:3]))}</td></tr>"
        for g in sorted(glyphs, key=lambda g: -g["prompt_kl_mean"]))

    html = f"""<title>Llama-3.2-3B · which emoji intervenes most?</title>
<style>
  :root {{
    color-scheme: light;
    --page:#f7f8fa; --card:#ffffff; --ink:#16181d; --mid:#5b6270; --faint:#9aa1ad;
    --line:#e3e6ec; --grid:#eef0f4; --halo:#f0f2f6; --accent:#2563eb; --warn:#b45309;
    --band:#dbeafe; --shadow:0 1px 3px rgba(16,20,30,.07),0 8px 24px rgba(16,20,30,.05);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      color-scheme: dark;
      --page:#0c0e12; --card:#14171d; --ink:#e9ecf1; --mid:#9aa2b1; --faint:#6b7484;
      --line:#242932; --grid:#1c2029; --halo:#1b1f27; --accent:#60a5fa; --warn:#fbbf24;
      --band:#1e3a5f; --shadow:0 1px 3px rgba(0,0,0,.5),0 8px 24px rgba(0,0,0,.35);
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --page:#0c0e12; --card:#14171d; --ink:#e9ecf1; --mid:#9aa2b1; --faint:#6b7484;
    --line:#242932; --grid:#1c2029; --halo:#1b1f27; --accent:#60a5fa; --warn:#fbbf24;
    --band:#1e3a5f; --shadow:0 1px 3px rgba(0,0,0,.5),0 8px 24px rgba(0,0,0,.35);
  }}
  body {{ margin:0; padding:34px 22px 60px; background:var(--page); color:var(--ink);
    font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif; }}
  .wrap {{ max-width:960px; margin:0 auto; }}
  .kicker {{ font-size:12px; letter-spacing:.11em; text-transform:uppercase;
    color:var(--accent); font-weight:700; margin-bottom:10px; }}
  h1 {{ font-size:27px; line-height:1.24; margin:0 0 12px; letter-spacing:-.018em; }}
  .lede {{ color:var(--mid); max-width:74ch; margin:0 0 8px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:16px 14px 8px; margin:22px 0; box-shadow:var(--shadow); overflow-x:auto; }}
  .cap {{ color:var(--mid); font-size:13px; padding:2px 8px 12px; }}
  svg {{ display:block; max-width:100%; height:auto; }}
  .grid {{ stroke:var(--grid); stroke-width:1; }}
  .parity {{ stroke:var(--warn); stroke-width:1.5; stroke-dasharray:5 4; }}
  .parity-lab {{ fill:var(--warn); font-size:11px; font-weight:600; }}
  .axis {{ fill:var(--faint); font-size:11px; }}
  .lab {{ fill:var(--mid); font-size:12px; font-weight:600; }}
  .mid {{ text-anchor:middle; }} .end {{ text-anchor:end; }}
  .halo {{ fill:var(--halo); stroke:var(--line); stroke-width:1; }}
  .pt:hover .halo {{ stroke:var(--accent); stroke-width:2; }}
  .glyph {{ font-size:17px; text-anchor:middle; dominant-baseline:central; }}
  .band {{ fill:var(--band); opacity:.5; }}
  .bandmed {{ stroke:var(--accent); stroke-width:1.5; }}
  table {{ border-collapse:collapse; width:100%; font-size:12.5px; }}
  th,td {{ text-align:left; padding:5px 8px; border-bottom:1px solid var(--line);
    white-space:nowrap; }}
  th {{ color:var(--mid); font-weight:600; position:sticky; top:0; background:var(--card); }}
  td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  details {{ margin-top:4px; }} summary {{ cursor:pointer; color:var(--accent);
    font-size:13px; font-weight:600; padding:6px 2px; }}
  .notes {{ color:var(--mid); font-size:13.5px; max-width:78ch; }}
  .notes b {{ color:var(--ink); }}
  .warnbox {{ border:1px solid var(--warn); border-radius:10px; padding:10px 13px;
    color:var(--mid); font-size:13px; margin:18px 0; }}
</style>
<div class="wrap">
  <div class="kicker">GlyphProbe · pre-causal screen · out-of-contract</div>
  <h1>Which emoji actually pushes Llama-3.2-3B the hardest?</h1>
  <p class="lede">Each glyph measured on its own. <b>Horizontal</b>: how much simply
  prepending it shifts the next-token distribution. <b>Vertical</b>: how hard its
  residual-stream direction pushes when re-injected at a <i>matched</i> strength
  (&alpha;&nbsp;=&nbsp;{pa} of the target activation RMS), as a ratio to the
  <i>median</i> of {meta['random_controls']} random directions of exactly the same
  size. Above the dashed line beats that median — see the caveat below for what
  that does and does not license.</p>

  <div class="warnbox"><b>Out of contract.</b> Exploratory sandbox run on the real
  bf16 weights. Not the sealed v2 experiment, no causal or semantic claim
  (<code>pre-causal-activation-screen</code>). Tokenization is controlled only inside
  the matched stratum shown here.</div>

  <div class="card">
    <svg viewBox="0 0 {W} {H}" role="img"
         aria-label="prompt-level effect versus magnitude-controlled push, token-matched emoji">
      {grid}
      {parity}
      <text x="{W/2:.0f}" y="{H-8}" class="lab mid">prompt-level effect — KL(no emoji &rarr; emoji), mean of 4 wrappers</text>
      <text x="14" y="{H/2:.0f}" class="lab mid" transform="rotate(-90 14 {H/2:.0f})">matched-strength push &divide; random-direction null MEDIAN (L{L})</text>
      {''.join(marks)}
    </svg>
    <div class="cap">{len(pts)} glyphs, every one costing exactly 4 prefix tokens —
      so nothing in this ordering is a token-count artefact. Hover for detail.</div>
  </div>

  <div class="card">
    <svg viewBox="0 0 {W2} {H2}" role="img" aria-label="prompt-level effect versus prefix token count">
      {lgrid}{lygrid}
      {band}
      <text x="{W2/2:.0f}" y="{H2-8}" class="lab mid">prefix tokens the glyph costs</text>
      <text x="14" y="{H2/2:.0f}" class="lab mid" transform="rotate(-90 14 {H2/2:.0f})">prompt-level KL</text>
      {lmarks}
    </svg>
    <div class="cap">The token ladder. Shaded band = full range of the 4-token matched
      stratum above (line = its median). Spearman(token count, prompt KL) over all
      {summ['n_glyphs']} glyphs = <b>{rho_tok:+.2f}</b>.</div>
  </div>

  <p class="notes"><b>How to read it.</b> The two axes are different questions.
  Horizontal is the everyday one — put this emoji in front of a sentence and the
  model's next-token distribution moves this much. Vertical strips out size: every
  glyph's direction is renormalised to the same RMS before injection, so height
  means "this direction is <i>special</i>", not "this direction is <i>big</i>".
  Spearman between the two axes inside the matched stratum is
  <b>{rho_pair:+.2f}</b>.</p>

  <p class="notes"><b>The vertical axis is a ratio to the null <i>median</i>, and the
  null is right-skewed.</b> The assumption-free check counts the glyphs that clear the
  null <i>outright</i> — not one of the {meta['random_controls']} matched random
  directions reached their KL. At layer {L} that is {clear_open}/{summ['n_glyphs']} on
  the open-ended target, {clear_planet}/{summ['n_glyphs']} on <code>planet</code> and
  {clear_paris}/{summ['n_glyphs']} on <code>paris</code> — and
  <b>no glyph clears it on all three targets at any layer</b>. Read the vertical
  ordering as relative, not as {len(pts)} individually significant results. The
  horizontal axis does not use the null at all and is unaffected.</p>

  <p class="notes"><b>What it does not show.</b> A pre-causal activation screen only.
  It does not establish emoji meaning, semantic families, tokenizer independence, or
  any mechanism. The random-direction null is a size control, not a semantic control:
  beating it means the direction is structured, not that the structure is "meaning".</p>

  <details>
    <summary>Full data table ({len(glyphs)} glyphs)</summary>
    <table><thead><tr><th>glyph</th><th>id</th><th>family</th><th>tok</th>
      <th>prompt KL</th><th>ratio L{L}</th><th>z</th><th>consistency</th>
      <th>top boosted tokens</th></tr></thead>
      <tbody>{rows}</tbody></table>
  </details>
</div>
"""

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")
    (ROOT / "chart" / "sweep_chart_data.json").write_text(
        json.dumps({"matched": pts, "ladder": lad, "layer": L, "alpha": pa},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {ROOT / 'chart' / 'sweep_chart_data.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
