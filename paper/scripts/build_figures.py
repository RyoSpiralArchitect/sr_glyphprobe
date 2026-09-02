#!/usr/bin/env python3
"""Build manuscript figures from checksum-bound compact T19/T20/T21 summaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerTuple
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.text import Text


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
T21_SOURCE = (
    ROOT
    / "validation/t21_glyph_context_path_confirmation_v0/results/confirmation_result.json"
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
    validate_interval_bounds(fig)
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


def validate_interval_bounds(fig: plt.Figure) -> None:
    """Reject confidence intervals clipped by a manually chosen axis range."""
    for ax in fig.axes:
        lower, upper = sorted(ax.get_xlim())
        for container in ax.containers:
            if not getattr(container, "has_xerr", False):
                continue
            for collection in container.lines[2]:
                for segment in collection.get_segments():
                    if any(not lower <= point[0] <= upper for point in segment):
                        raise ValueError(
                            "Confidence interval extends beyond the x-axis"
                        )


def validate_box_labels(
    fig: plt.Figure,
    labels: list[tuple[FancyBboxPatch, Text]],
    minimum_padding_points: float = 3.0,
) -> None:
    """Fail before export if a diagram label touches or escapes its box."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for patch, label in labels:
        box_bounds = patch.get_window_extent(renderer)
        text_bounds = label.get_window_extent(renderer)
        padding = (
            min(
                text_bounds.x0 - box_bounds.x0,
                box_bounds.x1 - text_bounds.x1,
                text_bounds.y0 - box_bounds.y0,
                box_bounds.y1 - text_bounds.y1,
            )
            * 72
            / fig.dpi
        )
        if padding < minimum_padding_points:
            raise ValueError(
                f"Diagram label has {padding:.2f} pt padding; "
                f"requires {minimum_padding_points:.2f} pt: {label.get_text()!r}"
            )


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
    if (
        payload.get("protocol_id")
        != "glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0"
    ):
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
        ("necessity", "necessity_ceiling", "Keyword necessity", "o"),
        ("sufficiency", "sufficiency_ceiling", "Keyword sufficiency", "s"),
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
        if prefix == "sufficiency":
            ax.axvline(0.06, color=GRAY, linewidth=0.9, linestyle=":")
        ax.axvline(attainable, color=GRAY, linewidth=0.9, linestyle="-.")
        ax.set_title(title)
        ax.set_xlabel("Keyword top-1 effect")
        ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
        ax.set_xlim(-0.014, 0.068)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[1].text(
        0.0605, 8.35, "0.06 min.", color=GRAY, fontsize=7, rotation=90, va="bottom"
    )
    axes[1].text(
        attainable + 0.001,
        8.35,
        "baseline gap",
        color=GRAY,
        fontsize=7,
        rotation=90,
        va="bottom",
    )
    handles = [
        (
            plt.Line2D(
                [], [], marker="o", color=DARK, markerfacecolor=BLUE, linestyle="none"
            ),
            plt.Line2D(
                [], [], marker="s", color=DARK, markerfacecolor=ORANGE, linestyle="none"
            ),
        ),
        plt.Line2D(
            [], [], marker=">", color=DARK, markerfacecolor="white", linestyle="none"
        ),
    ]
    fig.legend(
        handles=handles,
        labels=["Optimized rank-8 (random-adjusted)", "Full-state swap"],
        handler_map={tuple: HandlerTuple(ndivide=None)},
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
        frameon=False,
        ncol=2,
    )
    fig.suptitle(
        "T20-C: optimized effects and full-state swaps (384 emoji, 4 contexts)", y=0.995
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    return save_figure(fig, "t20_causal_ceilings")


def build_t21_path_summary() -> list[Path]:
    payload = load_json(T21_SOURCE)
    if (
        payload["protocol_id"] != "glyphprobe-t21-glyph-context-path-confirmation-v0"
        or payload["target_items"] != 195
        or payload["candidate_anchor"] != 21
        or payload["primary"]["replicates"] != 20000
    ):
        raise ValueError("T21 population, anchor, or inference changed")
    fig = plt.figure(figsize=(7.15, 3.05))
    diagram = fig.add_axes((0.02, 0.65, 0.96, 0.24))
    diagram.set(xlim=(0, 3.2), ylim=(0, 1))
    diagram.axis("off")
    boxes = []
    words = [
        "Readout residual reset\nSame-item codepoint state\nAfter block 21",
        "Later attention K/V\nDonor G / S / prefix swaps\nBlocks 22–27 · readout only",
        "Final keyword margin\nOwn minus best source cosine\n195 items · 128 competitors",
    ]
    for start, text in zip((0.02, 1.11, 2.20), words, strict=True):
        patch = FancyBboxPatch(
            (start, 0.03),
            0.96,
            0.94,
            boxstyle="round,pad=0.015,rounding_size=0.035",
            facecolor="white",
            edgecolor=DARK,
            linewidth=1.0,
        )
        diagram.add_patch(patch)
        label = diagram.text(
            start + 0.48, 0.50, text, ha="center", va="center", fontsize=8.1, color=DARK
        )
        boxes.append((patch, label))
    for start in (0.98, 2.07):
        diagram.add_patch(
            FancyArrowPatch(
                (start, 0.5),
                (start + 0.13, 0.5),
                arrowstyle="-|>",
                mutation_scale=9,
                color=GRAY,
                linewidth=1.0,
            )
        )
    fig.text(
        0.5,
        0.597,
        "G: glyph positions   S: equal-count suffix positions   Same-slot neutral references",
        ha="center",
        fontsize=8.0,
        color=DARK,
    )
    fig.text(
        0.34,
        0.536,
        "Mean and simultaneous one-sided 95% lower bound",
        fontsize=8.0,
        color=DARK,
    )
    ax = fig.add_axes((0.34, 0.155, 0.62, 0.345))
    names = [
        "calibration",
        "necessity_absolute",
        "necessity_position_adjusted",
        "rescue_absolute",
        "rescue_position_adjusted",
    ]
    labels = [
        "Full-prefix calibration",
        "Glyph decrement",
        "Adjusted decrement",
        "Glyph restoration",
        "Adjusted restoration",
    ]
    colors = [GRAY, BLUE, BLUE, ORANGE, ORANGE]
    markers = ["D", "o", "o", "s", "s"]
    for position, name, color, marker in zip(
        range(4, -1, -1), names, colors, markers, strict=True
    ):
        row = payload["primary"]["contrasts"][name]
        mean, lower = row["mean"], row["lower_simultaneous_95"]
        if not 0 < lower <= mean:
            raise ValueError("T21 plotted lower bound changed")
        ax.errorbar(
            [mean],
            [position],
            xerr=[[mean - lower], [0]],
            fmt=marker,
            color=color,
            markerfacecolor=color,
            markeredgecolor=DARK,
            markeredgewidth=0.7,
            markersize=4.8,
            elinewidth=1.2,
            capsize=2.5,
        )
    ax.set_yticks(range(4, -1, -1), labels)
    ax.set_ylim(-0.55, 4.55)
    ax.set_xlim(0, 0.0105)
    ax.set_xticks([0, 0.002, 0.004, 0.006, 0.008, 0.010])
    ax.set_xlabel("Cosine-margin contrast", labelpad=3)
    ax.tick_params(axis="y", length=0, pad=7)
    ax.grid(axis="x", color="#E7EAED", linewidth=0.6)
    fig.suptitle(
        "T21-C: readout-specific path test and five contrasts",
        y=0.99,
        fontsize=10,
        color=DARK,
    )
    validate_box_labels(fig, boxes)
    return save_figure(fig, "t21_path_summary")


def build_design() -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.15, 2.9))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.5)
    ax.axis("off")
    labels: list[tuple[FancyBboxPatch, Text]] = []

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
        label = ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            color=DARK,
            fontsize=7.7,
        )
        labels.append((patch, label))

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
    box(0.2, 1.25, 1.55, 0.9, "55 symbols\n(non-emoji)", GRAY)
    box(
        2.35,
        1.645,
        2.2,
        1.6,
        "Four views\nraw glyph\nofficial name\nCLDR keyword\nU+... spelling",
        BLUE,
    )
    box(5.15, 1.72, 2.1, 1.45, "24 contexts/item\n9 depths\nlate top-1", BLUE)
    box(7.85, 1.72, 2.05, 1.45, "Unrestricted +\nmatched-count\nIUT", BLUE)
    box(10.45, 1.72, 1.3, 1.45, "r = 3/4\nmodel\nrule", BLUE)
    arrow(1.75, 3.15, 2.35, 2.72)
    arrow(1.75, 1.7, 2.35, 2.14)
    arrow(4.55, 2.45, 5.15, 2.45)
    arrow(7.25, 2.45, 7.85, 2.45)
    arrow(9.9, 2.45, 10.45, 2.45)

    box(0.2, 0.065, 1.55, 0.95, "Causal arm\n(T19-C)", ORANGE)
    box(2.35, 0.065, 2.2, 0.95, "128 source emoji\nrank-8 subspace", ORANGE)
    box(5.15, 0.065, 2.1, 0.95, "192 held-out\nemoji", ORANGE)
    box(7.85, 0.065, 2.05, 0.95, "6 late sites\nnecessity +\nsufficiency", ORANGE)
    box(10.45, 0.065, 1.3, 0.95, "joint\n0.02 floor", ORANGE)
    arrow(1.75, 0.54, 2.35, 0.54, ORANGE)
    arrow(4.55, 0.54, 5.15, 0.54, ORANGE)
    arrow(7.25, 0.54, 7.85, 0.54, ORANGE)
    arrow(9.9, 0.54, 10.45, 0.54, ORANGE)
    arrow(11.1, 1.72, 11.1, 1.015, ORANGE)
    ax.text(
        9.95,
        1.28,
        "run only after\ncriterion is met",
        ha="center",
        va="center",
        fontsize=7,
        color=ORANGE,
    )

    validate_box_labels(fig, labels)
    return save_figure(fig, "t19_design")


def build_lineage() -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.15, 2.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    labels: list[tuple[FancyBboxPatch, Text]] = []

    stages = [
        (
            0.15,
            "Token\nstructure",
            "T1 census\nT2 geometry\nT3 matched slots\nT4 carryover",
            GRAY,
        ),
        (
            2.55,
            "Persistence",
            "T5 distance\nT6 replication\nT7 depth",
            GRAY,
        ),
        (
            4.95,
            "Lexical\nretrieval",
            "T8 atlas\nT9 reserve\nT10 cross-model",
            BLUE,
        ),
        (
            7.35,
            "Boundary\ntests",
            "T11–T12 systems\nT13 specificity\nT14–T16 causal\nT17–T18 depth",
            BLUE,
        ),
        (
            9.75,
            "Lexical +\ncausal tests",
            "T19-L retrieval\nT19-C rank-8\nT20-C optimized\n+ full swaps",
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
        label = ax.text(
            x + width / 2,
            1.54,
            body,
            ha="center",
            va="center",
            color=DARK,
            fontsize=7.0,
            linespacing=1.25,
        )
        labels.append((patch, label))

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
        "Earlier studies motivate the design; only T19-L enters the lexical primary test",
        ha="center",
        va="center",
        color=DARK,
        fontsize=7.2,
    )
    validate_box_labels(fig, labels)
    return save_figure(fig, "t19_lineage")


def build_model_effects(models: list[dict[str, Any]]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.9, 3.45))
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
    lower_bounds = [
        point - error
        for points, errors in ((u, u_low), (m, m_low))
        for point, error in zip(points, errors)
    ]
    upper_bounds = [
        point + error
        for points, errors in ((u, u_high), (m, m_high))
        for point, error in zip(points, errors)
    ]
    ax.set_xlim(min(0.0, *lower_bounds) - 0.01, max(0.02, *upper_bounds) + 0.015)
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
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.95), sharey=True, sharex=True)
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
    outputs.extend(build_t21_path_summary())

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
            {
                "path": T21_SOURCE.relative_to(ROOT).as_posix(),
                "sha256": sha256(T21_SOURCE),
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
