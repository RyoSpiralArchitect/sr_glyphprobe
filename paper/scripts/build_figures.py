#!/usr/bin/env python3
"""Build manuscript figures from checksum-bound compact T19 summaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "figures"
MODEL_SOURCE = (
    ROOT
    / "validation"
    / "t19_lexical_alias_unicode_control_v0"
    / "results"
    / "model_cell_results.json"
)
CAUSAL_SOURCE = (
    ROOT
    / "validation"
    / "t19_lexical_alias_component_causal_v0"
    / "results"
    / "causal_site_results.json"
)
T20_SOURCE = (
    ROOT
    / "validation"
    / "t20_lexical_alias_optimized_subspace_causal_v0"
    / "results"
    / "causal_site_results.json"
)
T20_SITE_ORDER = [
    (21, "resid_out"),
    (24, "resid_out"),
    (27, "resid_out"),
    (21, "attn_out"),
    (21, "mlp_out"),
    (24, "attn_out"),
    (24, "mlp_out"),
    (27, "attn_out"),
    (27, "mlp_out"),
]

MODEL_ORDER = [
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
]

MODEL_LABEL = {
    "qwen25_0p5b_base_bf16": "Qwen2.5 0.5B",
    "olmo2_1b_base_bf16": "OLMo 2 1B",
    "qwen25_1p5b_base_bf16": "Qwen2.5 1.5B",
    "smollm2_1p7b_base_bf16": "SmolLM2 1.7B",
    "gemma2_2b_it_bf16": "Gemma 2 2B IT",
    "llama32_3b_base_bf16": "Llama 3.2 3B",
    "qwen25_3b_base_bf16": "Qwen2.5 3B",
    "qwen25_7b_base_bf16": "Qwen2.5 7B",
    "mistral7b_instruct_v03_bf16": "Mistral 7B Inst.",
}

BLUE = "#2468A2"
ORANGE = "#D17C1F"
DARK = "#243447"
GRAY = "#75808A"
LIGHT_GRAY = "#D5DADE"
PALE_BLUE = "#EAF2F8"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    outputs: list[Path] = []
    metadata = {
        "Title": stem,
        "Author": "Anonymous",
        "Creator": "GlyphProbe paper/scripts/build_figures.py",
        "CreationDate": None,
        "ModDate": None,
    }
    pdf_path = OUT / f"{stem}.pdf"
    png_path = OUT / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight", metadata=metadata)
    fig.savefig(png_path, bbox_inches="tight", dpi=220)
    plt.close(fig)
    outputs.extend([pdf_path, png_path])
    return outputs


def validate_models(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("protocol_id") != "glyphprobe-t19-lexical-alias-unicode-control-v0":
        raise ValueError("Unexpected T19-L protocol id")
    models = payload.get("models")
    if not isinstance(models, list) or len(models) != 9:
        raise ValueError("Expected exactly nine T19-L model cells")
    by_role = {row["model_role"]: row for row in models}
    if set(by_role) != set(MODEL_ORDER):
        raise ValueError("T19-L model roster differs from the frozen figure roster")
    ordered = [by_role[role] for role in MODEL_ORDER]
    for row in ordered:
        if not row.get("model_positive") or not row.get("practical_pass"):
            raise ValueError(f"Unexpected failed model cell: {row['model_role']}")
        for component in ("unrestricted", "matched"):
            effect = row["kind_components"]["emoji"][component][
                "alias_minus_codepoint_top1"
            ]
            if effect < 0.02:
                raise ValueError(
                    f"Frozen practical floor not met: {row['model_role']} {component}"
                )
    return ordered


def validate_causal(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("protocol_id") != "glyphprobe-t19-lexical-alias-component-causal-v0":
        raise ValueError("Unexpected T19-C protocol id")
    sites = payload.get("sites")
    if not isinstance(sites, list) or len(sites) != 6:
        raise ValueError("Expected exactly six T19-C sites")
    observed = [(row["block_index"], row["site"]) for row in sites]
    expected = [
        (21, "attn_out"),
        (21, "mlp_out"),
        (24, "attn_out"),
        (24, "mlp_out"),
        (27, "attn_out"),
        (27, "mlp_out"),
    ]
    if observed != expected:
        raise ValueError("T19-C site order differs from the frozen roster")
    if any(not row["engineering"]["pass"] for row in sites):
        raise ValueError("A T19-C engineering gate is not exact")
    if any(row["practical_and_interval_pass"] for row in sites):
        raise ValueError("A site unexpectedly passes the joint causal rule")
    return sites


def validate_t20(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("protocol_id") != "glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0":
        raise ValueError("Unexpected T20-C protocol id")
    sites = payload.get("sites")
    if not isinstance(sites, list) or len(sites) != 9:
        raise ValueError("Expected exactly nine T20-C sites")
    observed = [(row["block_index"], row["site"]) for row in sites]
    if observed != T20_SITE_ORDER:
        raise ValueError("T20-C site order differs from the frozen roster")
    if any(not row["engineering"]["pass"] for row in sites):
        raise ValueError("A T20-C engineering gate is not exact")
    return sites


def build_t20_ceilings(sites: list[dict[str, Any]]) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.4), sharey=True, sharex=True)
    site_word = {"resid_out": "resid", "attn_out": "attn", "mlp_out": "MLP"}
    labels = [
        f"B{row['block_index']} {site_word[row['site']]}"
        + (" *" if row["primary_site"] else "")
        for row in sites
    ]
    y = list(range(len(sites)))
    attainable = float(
        sites[0]["baseline_glyph"]["alias_top1"]
        - sites[0]["baseline_codepoint"]["alias_top1"]
    )
    panels = [
        ("necessity", "necessity_ceiling", "Keyword necessity (adjusted)", "o"),
        ("sufficiency", "sufficiency_ceiling", "Keyword sufficiency (adjusted)", "s"),
    ]
    for ax, (prefix, ceiling_key, title, marker) in zip(axes, panels):
        for pos, row in zip(y, sites):
            if row["primary_site"]:
                ax.axhspan(pos - 0.43, pos + 0.43, color=PALE_BLUE, zorder=0)
            effect = row[f"{prefix}_adjusted_effect"]
            interval = row[f"{prefix}_interval"]
            color = DARK if row["primary_site"] else GRAY
            ax.errorbar(
                [effect],
                [pos],
                xerr=[
                    [effect - interval["lower_95"]],
                    [interval["upper_95"] - effect],
                ],
                fmt=marker,
                color=color,
                ecolor=color,
                markerfacecolor=ORANGE if prefix == "sufficiency" else BLUE,
                markeredgecolor=color,
                markeredgewidth=1.0,
                markersize=5.0,
                elinewidth=1.1,
                capsize=2,
                zorder=3,
            )
            ax.scatter(
                [row[ceiling_key]],
                [pos],
                marker=">",
                s=42,
                facecolor="white",
                edgecolor=ORANGE if prefix == "sufficiency" else BLUE,
                linewidth=1.3,
                zorder=4,
            )
        ax.axvline(0.0, color=DARK, linewidth=0.8)
        ax.axvline(0.02, color=GRAY, linewidth=0.9, linestyle="--")
        ax.axvline(0.06, color=GRAY, linewidth=0.9, linestyle=":")
        ax.axvline(attainable, color=ORANGE, linewidth=0.9, linestyle="-.", alpha=0.7)
        ax.set_title(title)
        ax.set_xlabel("Keyword top-1 effect")
        ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
        ax.set_xlim(-0.014, 0.068)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[1].text(0.0605, 8.35, "0.06 min.", color=GRAY, fontsize=6.5, rotation=90, va="bottom")
    axes[1].text(attainable + 0.001, 8.35, "attainable", color=ORANGE, fontsize=6.5, rotation=90, va="bottom")
    handles = [
        plt.Line2D([], [], marker="o", color=DARK, markerfacecolor=BLUE, linestyle="none", label="Optimized rank-8 (adjusted)"),
        plt.Line2D([], [], marker=">", color=ORANGE, markerfacecolor="white", linestyle="none", label="Full-interchange ceiling"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), frameon=False, ncol=2)
    fig.suptitle("Registered T20-C effects and ceilings (384 fresh emoji, 4 contexts)", y=0.995)
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    return save_figure(fig, "t20_causal_ceilings")


def build_design() -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.15, 2.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.5)
    ax.axis("off")

    def box(x: float, y: float, w: float, h: float, text: str, color: str) -> None:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            linewidth=1.1,
            edgecolor=color,
            facecolor="white",
        )
        ax.add_patch(patch)
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            color=DARK,
            fontsize=7.7,
        )

    def arrow(x1: float, y1: float, x2: float, y2: float, color: str = GRAY) -> None:
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.0,
                color=color,
                zorder=0,
            )
        )

    ax.text(0.2, 4.15, "Observational arm (T19-L)", weight="bold", color=BLUE)
    box(0.2, 2.7, 1.55, 0.9, "55 atomic\nemoji", BLUE)
    box(0.2, 1.25, 1.55, 0.9, "55 non-emoji\nsymbols", GRAY)
    box(
        2.35,
        1.72,
        2.2,
        1.45,
        "Four text views\nraw | official name\nkeyword | codepoint",
        BLUE,
    )
    box(5.15, 1.72, 2.1, 1.45, "24 contexts/item\n9 depths\nlate-window top-1", BLUE)
    box(7.85, 1.72, 2.05, 1.45, "Unrestricted +\nmatched-count\nIUT", BLUE)
    box(10.45, 1.72, 1.3, 1.45, "r = 3/4\ncross-model\nrule", BLUE)
    arrow(1.75, 3.15, 2.35, 2.72)
    arrow(1.75, 1.7, 2.35, 2.14)
    arrow(4.55, 2.45, 5.15, 2.45)
    arrow(7.25, 2.45, 7.85, 2.45)
    arrow(9.9, 2.45, 10.45, 2.45)

    box(0.2, 0.15, 1.55, 0.78, "Causal arm\n(T19-C)", ORANGE)
    box(2.35, 0.15, 2.2, 0.78, "128 source emoji\nrank-8 subspace", ORANGE)
    box(5.15, 0.15, 2.1, 0.78, "192 held-out emoji\nno T19-L evaluation", ORANGE)
    box(7.85, 0.15, 2.05, 0.78, "6 late sites\nnecessity +\nsufficiency", ORANGE)
    box(10.45, 0.15, 1.3, 0.78, "joint\n0.02 floor", ORANGE)
    arrow(1.75, 0.54, 2.35, 0.54, ORANGE)
    arrow(4.55, 0.54, 5.15, 0.54, ORANGE)
    arrow(7.25, 0.54, 7.85, 0.54, ORANGE)
    arrow(9.9, 0.54, 10.45, 0.54, ORANGE)
    arrow(11.1, 1.72, 11.1, 0.93, ORANGE)
    ax.text(
        9.95,
        1.28,
        "run only after\ncriterion is met",
        ha="center",
        va="center",
        fontsize=7,
        color=ORANGE,
    )

    return save_figure(fig, "t19_design")


def build_lineage() -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.15, 2.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    stages = [
        (
            0.15,
            "Token structure",
            "T1 census\nT2 shape geometry\nT3 matched slots\nT4 suffix carryover",
            GRAY,
        ),
        (
            2.55,
            "Persistence",
            "T5 distance profile\nT6 dense replication\nT7 depth interaction",
            GRAY,
        ),
        (
            4.95,
            "Lexical endpoint",
            "T8 semantic atlas\nT9 held-out reserve\nT10 cross-model test",
            BLUE,
        ),
        (
            7.35,
            "Boundary tests",
            "T11--T12 glyph systems\nT13 source/target\nT14--T16 interventions\nT17--T18 depth",
            BLUE,
        ),
        (
            9.75,
            "Gated causal chain",
            "T19-L lexical test\nT19-C conditional test\nT20-C calibrated\nfollow-up",
            ORANGE,
        ),
    ]
    width = 2.0
    for x, title, body, color in stages:
        ax.text(
            x + width / 2,
            2.72,
            title,
            ha="center",
            va="center",
            weight="bold",
            color=color,
            fontsize=7.5,
        )
        patch = FancyBboxPatch(
            (x, 0.68),
            width,
            1.72,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            linewidth=1.1,
            edgecolor=color,
            facecolor="white",
        )
        ax.add_patch(patch)
        ax.text(
            x + width / 2,
            1.54,
            body,
            ha="center",
            va="center",
            color=DARK,
            fontsize=7.0,
            linespacing=1.25,
        )

    for left in (2.15, 4.55, 6.95, 9.35):
        ax.add_patch(
            FancyArrowPatch(
                (left, 1.54),
                (left + 0.36, 1.54),
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=1.0,
                color=GRAY,
            )
        )
    ax.text(
        6.0,
        0.24,
        "Decision lineage only; earlier stages do not enter the T19-L primary denominator",
        ha="center",
        va="center",
        color=DARK,
        fontsize=7.2,
    )
    return save_figure(fig, "t19_lineage")


def build_model_effects(models: list[dict[str, Any]]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.9, 3.75))
    positions = list(range(len(models)))
    y_u = [y + 0.13 for y in positions]
    y_m = [y - 0.13 for y in positions]

    def values(component: str) -> tuple[list[float], list[float], list[float]]:
        points, low, high = [], [], []
        for row in models:
            cell = row["kind_components"]["emoji"][component]
            point = cell["alias_minus_codepoint_top1"]
            interval = cell["descriptive_interval"]
            points.append(point)
            low.append(point - interval["lower_95"])
            high.append(interval["upper_95"] - point)
        return points, low, high

    u, u_low, u_high = values("unrestricted")
    m, m_low, m_high = values("matched")
    ax.errorbar(
        u,
        y_u,
        xerr=[u_low, u_high],
        fmt="o",
        color=BLUE,
        ecolor=BLUE,
        markerfacecolor=BLUE,
        markeredgecolor="white",
        markeredgewidth=0.5,
        markersize=5.5,
        elinewidth=1.0,
        capsize=2,
        label="Unrestricted",
        zorder=3,
    )
    ax.errorbar(
        m,
        y_m,
        xerr=[m_low, m_high],
        fmt="s",
        color=ORANGE,
        ecolor=ORANGE,
        markerfacecolor="white",
        markeredgecolor=ORANGE,
        markeredgewidth=1.2,
        markersize=5.0,
        elinewidth=1.0,
        capsize=2,
        label="Token-count matched",
        zorder=3,
    )
    for y, a, b in zip(positions, u, m):
        ax.plot([a, b], [y + 0.11, y - 0.11], color=LIGHT_GRAY, linewidth=0.7, zorder=1)
    ax.axvline(0.0, color=DARK, linewidth=0.8)
    ax.axvline(0.02, color=GRAY, linewidth=0.9, linestyle="--")
    ax.text(0.022, -0.72, "0.02 floor", color=GRAY, fontsize=7, ha="left")
    ax.set_yticks(positions, [MODEL_LABEL[row["model_role"]] for row in models])
    ax.invert_yaxis()
    ax.set_xlim(-0.01, 0.315)
    ax.set_xlabel("Emoji keyword minus codepoint top-1")
    ax.set_title("Cross-model emoji keyword retrieval")
    ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        frameon=False,
        ncol=2,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return save_figure(fig, "t19_model_effects")


def build_emoji_symbol_boundary(models: list[dict[str, Any]]) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 4.45), sharey=True, sharex=True)
    y = list(range(len(models)))
    endpoint_specs = [
        ("alias_minus_codepoint_top1", "CLDR keyword"),
        ("canonical_minus_codepoint_top1", "Official name"),
    ]
    offsets = {
        ("emoji", "unrestricted"): 0.24,
        ("emoji", "matched"): 0.08,
        ("symbol", "unrestricted"): -0.08,
        ("symbol", "matched"): -0.24,
    }
    styles = {
        ("emoji", "unrestricted"): (BLUE, "o", BLUE, "Emoji U"),
        ("emoji", "matched"): (BLUE, "o", "white", "Emoji M"),
        ("symbol", "unrestricted"): (GRAY, "D", GRAY, "Symbol U"),
        ("symbol", "matched"): (GRAY, "D", "white", "Symbol M"),
    }

    for ax, (metric, title) in zip(axes, endpoint_specs):
        for kind in ("emoji", "symbol"):
            for component in ("unrestricted", "matched"):
                color, marker, face, label = styles[(kind, component)]
                values = [
                    row["kind_components"][kind][component][metric] for row in models
                ]
                ax.scatter(
                    values,
                    [pos + offsets[(kind, component)] for pos in y],
                    s=27,
                    marker=marker,
                    facecolor=face,
                    edgecolor=color,
                    linewidth=1.0,
                    label=label,
                    zorder=3,
                )
        ax.axvline(0.0, color=DARK, linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("Top-1 difference vs. codepoint")
        ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
        ax.set_xlim(-0.10, 0.535)
    axes[0].set_yticks(y, [MODEL_LABEL[row["model_role"]] for row in models])
    axes[0].invert_yaxis()
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.01),
        frameon=False,
        ncol=4,
        columnspacing=1.2,
    )
    fig.suptitle("Emoji-symbol lexical boundary (registered secondary)", y=0.995)
    fig.tight_layout(rect=(0, 0.08, 1, 0.965))
    return save_figure(fig, "t19_emoji_symbol_boundary")


def build_causal_sites(sites: list[dict[str, Any]]) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.55), sharey=True, sharex=True)
    labels = [
        f"B{row['block_index']} {'attn' if row['site'] == 'attn_out' else 'MLP'}"
        + (" *" if row["primary_site"] else "")
        for row in sites
    ]
    y = list(range(len(sites)))
    components = [
        ("necessity", "Random-adjusted necessity", "o"),
        ("sufficiency", "Random-adjusted sufficiency", "s"),
    ]

    for ax, (prefix, title, marker) in zip(axes, components):
        for pos, row in zip(y, sites):
            if row["primary_site"]:
                ax.axhspan(pos - 0.43, pos + 0.43, color=PALE_BLUE, zorder=0)
            effect = row[f"{prefix}_adjusted_effect"]
            interval = row[f"{prefix}_interval"]
            color = DARK if row["primary_site"] else GRAY
            ax.errorbar(
                [effect],
                [pos],
                xerr=[
                    [effect - interval["lower_95"]],
                    [interval["upper_95"] - effect],
                ],
                fmt=marker,
                color=color,
                ecolor=color,
                markerfacecolor=ORANGE if prefix == "sufficiency" else BLUE,
                markeredgecolor=color,
                markeredgewidth=1.0,
                markersize=5.5,
                elinewidth=1.1,
                capsize=2,
                zorder=3,
            )
        ax.axvline(0.0, color=DARK, linewidth=0.8)
        ax.axvline(0.02, color=GRAY, linewidth=0.9, linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("Adjusted top-1 effect")
        ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
        ax.set_xlim(-0.06, 0.13)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    fig.suptitle("Prespecified component-level causal tests", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return save_figure(fig, "t19_causal_sites")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    model_payload = load_json(MODEL_SOURCE)
    causal_payload = load_json(CAUSAL_SOURCE)
    t20_payload = load_json(T20_SOURCE)
    models = validate_models(model_payload)
    sites = validate_causal(causal_payload)
    t20_sites = validate_t20(t20_payload)

    outputs: list[Path] = []
    outputs.extend(build_design())
    outputs.extend(build_lineage())
    outputs.extend(build_model_effects(models))
    outputs.extend(build_emoji_symbol_boundary(models))
    outputs.extend(build_causal_sites(sites))
    outputs.extend(build_t20_ceilings(t20_sites))

    manifest = {
        "schema_version": 1,
        "builder": "paper/scripts/build_figures.py",
        "contracts": "paper/README.md#figure-chart-contracts",
        "inputs": [
            {
                "path": MODEL_SOURCE.relative_to(ROOT).as_posix(),
                "sha256": sha256(MODEL_SOURCE),
            },
            {
                "path": CAUSAL_SOURCE.relative_to(ROOT).as_posix(),
                "sha256": sha256(CAUSAL_SOURCE),
            },
            {
                "path": T20_SOURCE.relative_to(ROOT).as_posix(),
                "sha256": sha256(T20_SOURCE),
            },
        ],
        "outputs": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
            for path in sorted(outputs)
        ],
    }
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
