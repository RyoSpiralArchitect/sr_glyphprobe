#!/usr/bin/env python3
"""Self-contained (CSP-safe) chart for the deep diagnostic.

Panel 1 — target grid: which of the 12 injection targets each glyph clears the
          random-direction null on, ordered by baseline entropy. Shows that the
          "open-ended only" impression from sweep_v1 was a target-count artefact
          and that detectability tracks the target, not the glyph.
Panel 2 — layer profile: ratio-to-null across every layer, so the peak depth is
          read off rather than assumed.
Panel 3 — specificity heat map: does a glyph's direction boost its own probe
          words, or its whole category's?

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


def ramp(v: float, lo: float, hi: float) -> str:
    """Diverging blue(-) .. neutral .. amber(+); returns an explicit rgb()."""
    if hi == lo:
        t = 0.5
    else:
        t = (v - lo) / (hi - lo)
    t = max(0.0, min(1.0, t))
    # 0 -> blue, 0.5 -> near background, 1 -> amber
    if t < 0.5:
        k = t / 0.5
        r = int(37 + (245 - 37) * k)
        g = int(99 + (246 - 99) * k)
        b = int(235 + (250 - 235) * k)
    else:
        k = (t - 0.5) / 0.5
        r = int(245 + (180 - 245) * k)
        g = int(246 + (83 - 246) * k)
        b = int(250 + (9 - 250) * k)
    return f"rgb({r},{g},{b})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="deep_v1")
    ap.add_argument("--out", default=str(ROOT / "chart" / "deep_chart.html"))
    args = ap.parse_args()

    res = ROOT / "results"
    meta = json.loads((res / f"{args.tag}_meta.json").read_text(encoding="utf-8"))
    an = json.loads((res / f"{args.tag}_analysis.json").read_text(encoding="utf-8"))
    p1rows = [json.loads(l) for l in
              (res / f"{args.tag}_phase1.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]

    A = meta["alpha"]
    L0 = meta["deep_layer"]
    nn = an["phase1"]["n_null"]

    # ---------------- panel 1: glyph x target grid --------------------------
    tgts = sorted(an["phase1"]["targets"], key=lambda t: -t["entropy"])
    tnames = [t["target"] for t in tgts]
    glyph_order = [g["id"] for g in an["phase1"]["glyphs"]]
    ginfo = {g["id"]: g for g in an["phase1"]["glyphs"]}
    cell = {(r["id"], r["target"]): r for r in p1rows}

    cw, ch = 52, 26
    gx0, gy0 = 132, 96
    W1 = gx0 + cw * len(tnames) + 96
    H1 = gy0 + ch * len(glyph_order) + 40

    ratios = [cell[(g, t)]["ratio_to_null_median"] for g in glyph_order for t in tnames]
    lo, hi = min(ratios), max(ratios)

    parts = []
    for j, t in enumerate(tnames):
        x = gx0 + cw * j + cw / 2
        ti = next(v for v in tgts if v["target"] == t)
        parts.append(f'<text x="{x:.0f}" y="{gy0-40}" class="colhead mid" '
                     f'transform="rotate(-36 {x:.0f} {gy0-40})">{esc(t)}</text>')
        parts.append(f'<text x="{x:.0f}" y="{gy0-14}" class="tiny mid">'
                     f'H={ti["entropy"]:.1f}</text>')
    for i, gid in enumerate(glyph_order):
        y = gy0 + ch * i
        g = ginfo[gid]
        parts.append(f'<text x="26" y="{y+ch/2+5:.0f}" class="glyphlab">{esc(g["glyph"])}</text>')
        parts.append(f'<text x="52" y="{y+ch/2+4:.0f}" class="rowlab">{esc(gid)}</text>')
        for j, t in enumerate(tnames):
            c = cell[(gid, t)]
            x = gx0 + cw * j
            clean = c["n_null_ge_observed"] == 0
            parts.append(
                f'<g><title>{esc(g["glyph"] + " " + gid + " on " + t)}\n'
                f'KL {c["kl"]:.4f}  ratio {c["ratio_to_null_median"]:.2f}\n'
                f'{c["n_null_ge_observed"]}/{nn} random directions reached it '
                f'(p={c["p_nonparametric"]:.4f})</title>'
                f'<rect x="{x+1}" y="{y+1}" width="{cw-2}" height="{ch-2}" rx="3" '
                f'style="fill:{ramp(c["ratio_to_null_median"], lo, hi)}"/>'
                f'<text x="{x+cw/2:.0f}" y="{y+ch/2+4:.0f}" class="cellv mid"'
                f'{" style=\"font-weight:700\"" if clean else ""}>'
                f'{c["ratio_to_null_median"]:.1f}</text></g>')
        parts.append(f'<text x="{gx0+cw*len(tnames)+12}" y="{y+ch/2+4:.0f}" class="rowlab">'
                     f'{g["clean"]}/{g["n_targets"]} clean</text>')

    # ---------------- panel 2: layer profiles -------------------------------
    panel2 = ""
    if "phase2" in an:
        prof = an["phase2"]["profiles"]
        NL = len(prof[0]["profile"])
        W2, H2 = 900, 380
        m2 = (58, 150, 18, 44)  # l, r, t, b
        allv = [v for p in prof for v in p["profile"]]
        ymax = max(allv) * 1.06
        def px2(L): return m2[0] + L / (NL - 1) * (W2 - m2[0] - m2[1])
        def py2(v): return H2 - m2[3] - v / ymax * (H2 - m2[2] - m2[3])
        gp = []
        for t in range(0, int(ymax) + 1, max(1, int(ymax) // 5)):
            gp.append(f'<line x1="{m2[0]}" y1="{py2(t):.1f}" x2="{W2-m2[1]}" y2="{py2(t):.1f}" '
                      f'class="grid"/><text x="{m2[0]-8}" y="{py2(t)+4:.1f}" class="axis end">{t}</text>')
        for L in range(0, NL, 4):
            gp.append(f'<text x="{px2(L):.0f}" y="{H2-m2[3]+18}" class="axis mid">{L}</text>')
        gp.append(f'<line x1="{m2[0]}" y1="{py2(1.0):.1f}" x2="{W2-m2[1]}" y2="{py2(1.0):.1f}" '
                  f'class="parity"/>')
        GRPC = {"strong": "#f59e0b", "high_prompt": "#2563eb", "weak": "#94a3b8",
                "zwj": "#10b981"}
        for p in sorted(prof, key=lambda p: -max(p["profile"])):
            d = " ".join(f"{px2(L):.1f},{py2(v):.1f}" for L, v in enumerate(p["profile"]))
            col = GRPC.get(p["group"], "#888")
            gp.append(f'<polyline points="{d}" class="prof" style="stroke:{col}"><title>'
                      f'{esc(p["glyph"] + " " + p["id"])} — peak L{p["peak_layer"]} '
                      f'ratio {p["peak_ratio"]:.2f}</title></polyline>')
        # end labels: de-overlap by pushing apart to a minimum vertical spacing
        lab = sorted(((py2(p["profile"][-1]), p) for p in prof), key=lambda t: t[0])
        SP = 13.0
        ys = [t[0] for t in lab]
        for i in range(1, len(ys)):
            if ys[i] - ys[i - 1] < SP:
                ys[i] = ys[i - 1] + SP
        overflow = ys[-1] - (H2 - m2[3])
        if overflow > 0:
            ys = [y - overflow for y in ys]
        for y, (y_true, p) in zip(ys, lab):
            col = GRPC.get(p["group"], "#888")
            xa = px2(NL - 1)
            gp.append(f'<polyline points="{xa:.1f},{y_true:.1f} {xa+9:.1f},{y:.1f} '
                      f'{xa+15:.1f},{y:.1f}" class="leader" style="stroke:{col}"/>')
            gp.append(f'<text x="{xa+19:.0f}" y="{y+3.5:.1f}" class="proflab" '
                      f'style="fill:{col}">{esc(p["glyph"])} {esc(p["id"])} '
                      f'(L{p["peak_layer"]})</text>')
        panel2 = f"""
  <div class="card">
    <svg viewBox="0 0 {W2} {H2}" role="img" aria-label="ratio to null across all layers">
      {''.join(gp)}
      <text x="{(W2-m2[1])/2:.0f}" y="{H2-6}" class="lab mid">layer (resid_post)</text>
      <text x="13" y="{H2/2:.0f}" class="lab mid" transform="rotate(-90 13 {H2/2:.0f})">ratio to null median</text>
    </svg>
    <div class="cap">Every layer 0..{NL-1}, mean over 3 targets. Peak layer median =
      <b>L{an['phase2']['peak_layer_median']}</b>. Dashed line = parity with the null median.
      sweep_v1 only sampled L5/L11/L16.</div>
  </div>"""

    # ---------------- panel 3: specificity ----------------------------------
    panel3 = ""
    spec_p = res / f"{args.tag}_specificity_matrix.json"
    if spec_p.exists():
        sm = json.loads(spec_p.read_text(encoding="utf-8"))
        M = sm["matrix"]
        keys = list(M.keys())
        gmap = {g["id"]: g["glyph"] for g in an["phase1"]["glyphs"]}
        vals = [v for r in M.values() for v in r.values()]
        lo3, hi3 = min(vals), max(vals)
        c3, r3 = 54, 26
        x0, y0 = 128, 104
        W3 = x0 + c3 * len(keys) + 20
        H3 = y0 + r3 * len(keys) + 36
        q = []
        for j, k in enumerate(keys):
            x = x0 + c3 * j + c3 / 2
            q.append(f'<text x="{x:.0f}" y="{y0-12}" class="colhead mid" '
                     f'transform="rotate(-40 {x:.0f} {y0-12})">{esc(k)}</text>')
        for i, ki in enumerate(keys):
            y = y0 + r3 * i
            q.append(f'<text x="24" y="{y+r3/2+5:.0f}" class="glyphlab">{esc(gmap.get(ki,""))}</text>')
            q.append(f'<text x="50" y="{y+r3/2+4:.0f}" class="rowlab">{esc(ki)}</text>')
            for j, kj in enumerate(keys):
                v = M[ki][kj]
                x = x0 + c3 * j
                q.append(f'<g><title>inject {esc(ki)} -> probe group {esc(kj)}: '
                         f'{v:+.3f} mean logit delta</title>'
                         f'<rect x="{x+1}" y="{y+1}" width="{c3-2}" height="{r3-2}" rx="3" '
                         f'style="fill:{ramp(v, lo3, hi3)}"/>'
                         f'<text x="{x+c3/2:.0f}" y="{y+r3/2+4:.0f}" class="cellv mid"'
                         f'{" style=\"font-weight:700\"" if ki==kj else ""}>{v:+.1f}</text></g>')
        panel3 = f"""
  <div class="card">
    <svg viewBox="0 0 {W3} {H3}" role="img" aria-label="cross-glyph specificity matrix">{''.join(q)}
      <text x="{W3/2:.0f}" y="{H3-8}" class="lab mid">probe word group &rarr;</text>
    </svg>
    <div class="cap">Mean logit delta on each hand-specified probe group when a glyph's own
      direction is injected (rows). Probe words were written by hand, <b>not</b> harvested
      from the model's own top-boosted lists, so the diagonal is not selected-on.
      Own probe group is largest for <b>{sm['self_wins_instance_level']}/{sm['n']}</b> glyphs;
      own <i>category block</i> is largest for <b>{sm['own_block_wins']}/{sm['n']}</b>.</div>
  </div>"""

    rho_e = an["phase1"]["spearman_entropy_clean"]

    html = f"""<title>Llama-3.2-3B · emoji intervention — deep diagnostic</title>
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
  .wrap {{ max-width:980px; margin:0 auto; }}
  .kicker {{ font-size:12px; letter-spacing:.11em; text-transform:uppercase;
    color:var(--accent); font-weight:700; margin-bottom:10px; }}
  h1 {{ font-size:27px; line-height:1.24; margin:0 0 12px; letter-spacing:-.018em; }}
  h2 {{ font-size:17px; margin:30px 0 4px; }}
  .lede, .notes {{ color:var(--mid); max-width:76ch; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
    padding:14px 12px 6px; margin:16px 0 22px; box-shadow:var(--shadow); overflow-x:auto; }}
  .cap {{ color:var(--mid); font-size:13px; padding:4px 8px 12px; }}
  svg {{ display:block; max-width:100%; height:auto; }}
  .grid {{ stroke:var(--grid); stroke-width:1; }}
  .parity {{ stroke:var(--warn); stroke-width:1.5; stroke-dasharray:5 4; }}
  .axis {{ fill:var(--faint); font-size:11px; }}
  .tiny {{ fill:var(--faint); font-size:9.5px; }}
  .lab {{ fill:var(--mid); font-size:12px; font-weight:600; }}
  .colhead {{ fill:var(--mid); font-size:11px; font-weight:600; text-anchor:middle; }}
  .rowlab {{ fill:var(--mid); font-size:11px; }}
  .glyphlab {{ font-size:16px; }}
  .cellv {{ fill:#16181d; font-size:10.5px; }}
  .mid {{ text-anchor:middle; }} .end {{ text-anchor:end; }}
  .prof {{ fill:none; stroke-width:1.7; opacity:.85; }}
  .prof:hover {{ stroke-width:3.4; opacity:1; }}
  .proflab {{ font-size:10px; }}
  .leader {{ fill:none; stroke-width:1; opacity:.5; }}
  .warnbox {{ border:1px solid var(--warn); border-radius:10px; padding:10px 13px;
    color:var(--mid); font-size:13px; margin:18px 0; }}
  b {{ color:var(--ink); }}
</style>
<div class="wrap">
  <div class="kicker">GlyphProbe · pre-causal screen · out-of-contract · deep diagnostic</div>
  <h1>Does the emoji-direction effect survive more targets and a bigger null?</h1>
  <p class="lede">The first sweep could only say the magnitude-controlled push was clean
  on one of three targets, against {24} random directions. This run takes the focused
  panel to <b>12 targets</b> and <b>{nn} random directions each</b>, then reads the layer
  profile and the specificity off the same weights.</p>

  <div class="warnbox"><b>Out of contract.</b> Exploratory sandbox run on the real bf16
  weights. Not the sealed v2 experiment, no causal or semantic claim
  (<code>pre-causal-activation-screen</code>). No holdout bank is used.</div>

  <h2>1 · It generalises — and detectability belongs to the target, not the glyph</h2>
  <p class="notes">Ratio to the null median per cell; <b>bold</b> = none of the {nn}
  random directions reached it (p = {1/(nn+1):.4f}, the floor). Targets are ordered by
  baseline entropy. Spearman(entropy, number of glyphs clearing the null) =
  <b>{rho_e:+.2f}</b> — sharp factual prompts hide the effect because a random push moves
  them a lot too.</p>
  <div class="card">
    <svg viewBox="0 0 {W1} {H1}" role="img" aria-label="glyph by target ratio grid">
      {''.join(parts)}
    </svg>
    <div class="cap">13 glyphs &times; 12 targets at L{L0}, &alpha;={A}.
      The weak controls (⬛ 🥺 ⛵) clear the null on just as many targets as the strong
      glyphs — the binary test saturates, so the ranking has to be read from the ratio,
      not from significance.</div>
  </div>
  {panel2}
  <h2>3 · What the direction is specific to</h2>
  {panel3}
  <p class="notes"><b>What this does not show.</b> A pre-causal activation screen.
  The random-direction null is a size control, not a semantic control. Beating it means a
  direction is structured, not that the structure is meaning.</p>
</div>
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
