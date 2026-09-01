#!/usr/bin/env python3
"""Build bounded post-outcome summaries for the completed T18 confirmation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import itertools
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ID = "glyphprobe-fresh-composite-glyph-lexical-confirmation-v0"
MODEL_ORDER = (
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
CORE_ORDER = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
)
QWEN_ORDER = (
    "qwen25_0p5b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
)
SYSTEM_ORDER = ("modifier", "zwj", "regional_flag")
DEPTH_ORDER = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
PRIMARY_DEPTHS = (0.75, 0.875, 1.0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256s(directory: Path) -> dict[str, str]:
    sums_path = directory / "SHA256SUMS"
    if not sums_path.is_file():
        raise FileNotFoundError(sums_path)
    verified: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.lstrip("*")
        if Path(name).name != name:
            raise ValueError(f"non-local SHA256SUMS entry: {name}")
        observed = _sha256(directory / name)
        if observed != expected:
            raise ValueError(f"hash mismatch for {directory / name}")
        verified[name] = observed
    return verified


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def equal_system_mean(
    rows: Sequence[Mapping[str, Any]],
    *,
    component: str,
    contrast: str,
    metric: str,
) -> float:
    system_means = []
    for system in SYSTEM_ORDER:
        values = [
            float(row[component][contrast][metric])
            for row in rows
            if row["glyph_system"] == system
        ]
        if not values:
            raise ValueError(f"missing {system} rows")
        system_means.append(float(np.mean(values)))
    return float(np.mean(system_means))


def _rows_at_depth(
    rows: Sequence[Mapping[str, Any]], depth: float
) -> list[Mapping[str, Any]]:
    selected = [row for row in rows if float(row["normalized_depth"]) == depth]
    if len(selected) != 24:
        raise ValueError(f"expected 24 rows at depth {depth}, found {len(selected)}")
    return selected


def _depth_profile(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, float]]:
    profile = []
    for depth in DEPTH_ORDER:
        selected = _rows_at_depth(rows, depth)
        profile.append(
            {
                "normalized_depth": depth,
                "english_unrestricted": equal_system_mean(
                    selected,
                    component="unrestricted",
                    contrast="english_minus_codepoint",
                    metric="top1_accuracy_forward",
                ),
                "english_primary_tokenization_matched": equal_system_mean(
                    selected,
                    component="primary_tokenization_matched",
                    contrast="english_minus_codepoint",
                    metric="top1_accuracy_forward",
                ),
                "japanese_unrestricted": equal_system_mean(
                    selected,
                    component="unrestricted",
                    contrast="japanese_minus_codepoint",
                    metric="top1_accuracy_forward",
                ),
                "japanese_secondary_tokenization_matched": equal_system_mean(
                    selected,
                    component="japanese_secondary_tokenization_matched",
                    contrast="japanese_minus_codepoint",
                    metric="top1_accuracy_forward",
                ),
            }
        )
    return profile


def _late_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    selected = [
        row for row in rows if float(row["normalized_depth"]) in PRIMARY_DEPTHS
    ]
    if len(selected) != 72:
        raise ValueError(f"expected 72 late-window rows, found {len(selected)}")
    specifications = {
        "english_unrestricted": (
            "unrestricted",
            "english_minus_codepoint",
            "top1_accuracy_forward",
        ),
        "english_primary_tokenization_matched": (
            "primary_tokenization_matched",
            "english_minus_codepoint",
            "top1_accuracy_forward",
        ),
        "japanese_unrestricted": (
            "unrestricted",
            "japanese_minus_codepoint",
            "top1_accuracy_forward",
        ),
        "japanese_secondary_tokenization_matched": (
            "japanese_secondary_tokenization_matched",
            "japanese_minus_codepoint",
            "top1_accuracy_forward",
        ),
        "english_paired_margin_unrestricted": (
            "unrestricted",
            "english_minus_codepoint",
            "paired_minus_off_diagonal_margin",
        ),
        "english_paired_margin_primary_tokenization_matched": (
            "primary_tokenization_matched",
            "english_minus_codepoint",
            "paired_minus_off_diagonal_margin",
        ),
        "english_cka_unrestricted": (
            "unrestricted",
            "english_minus_codepoint",
            "centered_linear_cka",
        ),
        "english_cka_primary_tokenization_matched": (
            "primary_tokenization_matched",
            "english_minus_codepoint",
            "centered_linear_cka",
        ),
        "english_to_japanese_top1_unrestricted": (
            "unrestricted",
            "english_japanese",
            "top1_accuracy_forward",
        ),
        "english_to_japanese_top1_secondary_tokenization_matched": (
            "japanese_secondary_tokenization_matched",
            "english_japanese",
            "top1_accuracy_forward",
        ),
    }
    return {
        name: equal_system_mean(
            selected, component=component, contrast=contrast, metric=metric
        )
        for name, (component, contrast, metric) in specifications.items()
    }


def _item_effects(path: Path) -> np.ndarray:
    effects = []
    with np.load(path, allow_pickle=False) as arrays:
        for system in SYSTEM_ORDER:
            english = arrays[f"unrestricted__{system}__english"]
            codepoint = arrays[f"unrestricted__{system}__codepoint"]
            expected = np.arange(english.shape[1])
            effects.append(
                (english == expected).mean(axis=0)
                - (codepoint == expected).mean(axis=0)
            )
    result = np.concatenate(effects)
    if result.shape != (192,):
        raise ValueError(f"expected 192 item effects, found {result.shape}")
    return result


def agreement_summary(
    effects: Mapping[str, np.ndarray], roles: Sequence[str]
) -> dict[str, Any]:
    matrix = np.stack([effects[role] for role in roles])
    positive = matrix > 0
    threshold = math.ceil(0.75 * len(roles))
    correlations = [
        float(np.corrcoef(matrix[left], matrix[right])[0, 1])
        for left, right in itertools.combinations(range(len(roles)), 2)
    ]
    equal_model_mean = matrix.mean(axis=0)
    return {
        "model_roles": list(roles),
        "positive_in_all_models": int(np.all(positive, axis=0).sum()),
        "positive_in_at_least_75_percent_of_models": int(
            (positive.sum(axis=0) >= threshold).sum()
        ),
        "positive_equal_model_mean": int((equal_model_mean > 0).sum()),
        "zero_equal_model_mean": int((equal_model_mean == 0).sum()),
        "negative_equal_model_mean": int((equal_model_mean < 0).sum()),
        "pairwise_item_effect_pearson": {
            "minimum": min(correlations),
            "median": float(np.median(correlations)),
            "maximum": max(correlations),
        },
    }


def _ordered_items(selection: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items = []
    for system in SYSTEM_ORDER:
        items.extend(
            row for row in selection["items"] if row["glyph_system"] == system
        )
    if len(items) != 192:
        raise ValueError(f"expected 192 selected items, found {len(items)}")
    return items


def build_secondary_analysis(
    *, summary_root: Path, analysis_root: Path, selection_path: Path
) -> dict[str, Any]:
    analysis_hashes = verify_sha256s(analysis_root)
    model_results = json.loads(
        (analysis_root / "model_cell_results.json").read_text(encoding="utf-8")
    )
    if set(model_results) != set(MODEL_ORDER):
        raise ValueError("analysis model roster does not match frozen T18 roster")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection["protocol_id"] != PROTOCOL_ID:
        raise ValueError("selection protocol mismatch")

    per_model: dict[str, Any] = {}
    effects: dict[str, np.ndarray] = {}
    summary_hashes: dict[str, dict[str, str]] = {}
    for role in MODEL_ORDER:
        role_root = summary_root / role
        summary_hashes[role] = verify_sha256s(role_root)
        rows = _load_jsonl(role_root / "cell_metrics.jsonl")
        if len(rows) != 216:
            raise ValueError(f"expected 216 metric rows for {role}, found {len(rows)}")
        per_model[role] = {
            "late_window": _late_metrics(rows),
            "depth_profile": _depth_profile(rows),
        }
        effects[role] = _item_effects(role_root / "primary_predictions.npz")

    ordered_items = _ordered_items(selection)
    core_matrix = np.stack([effects[role] for role in CORE_ORDER])
    universal_indices = np.where(np.all(core_matrix > 0, axis=0))[0]
    core_universal_items = [
        {
            "glyph_system": ordered_items[index]["glyph_system"],
            "glyph": ordered_items[index]["glyph"],
            "english_short_name": ordered_items[index]["english_short_name"],
            "core_item_effects": {
                role: float(core_matrix[role_index, index])
                for role_index, role in enumerate(CORE_ORDER)
            },
        }
        for index in universal_indices
    ]

    qwen_matched = [
        float(
            model_results[role]["tokenization_matched_component"][
                "observed_equal_system_equal_context_contrast"
            ]
        )
        for role in QWEN_ORDER
    ]
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "post_outcome_secondary_analysis_complete",
        "analysis_role": "descriptive_only_cannot_rescue_frozen_primary",
        "model_forward_calls": 0,
        "generation_calls": 0,
        "intervention_calls": 0,
        "claim_authorization": {
            "can_rescue_primary": False,
            "causal": False,
            "rendered_glyph_perception": False,
            "human_meaning_or_understanding": False,
            "tokenizer_independent": False,
            "scale_law": False,
            "model_population_general": False,
        },
        "source_integrity": {
            "analysis_sha256s": analysis_hashes,
            "summary_sha256s": summary_hashes,
            "selection_sha256": _sha256(selection_path),
        },
        "per_model": per_model,
        "itemwise_agreement": {
            "core_four": agreement_summary(effects, CORE_ORDER),
            "all_nine": agreement_summary(effects, MODEL_ORDER),
            "core_positive_in_all_items": core_universal_items,
            "interpretation": (
                "Aggregate recurrence does not imply a shared item roster; "
                "item-effect agreement remains descriptive and model-conditional."
            ),
        },
        "qwen_size_ordered_matched_profile": {
            "model_roles": list(QWEN_ORDER),
            "values": qwen_matched,
            "strictly_increasing": all(
                left < right for left, right in zip(qwen_matched, qwen_matched[1:])
            ),
            "scale_law_claim_authorized": False,
        },
    }


def _write_csv(path: Path, analysis: Mapping[str, Any]) -> None:
    fieldnames = (
        "model_role",
        "normalized_depth",
        "english_unrestricted",
        "english_primary_tokenization_matched",
        "japanese_unrestricted",
        "japanese_secondary_tokenization_matched",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for role in MODEL_ORDER:
            for row in analysis["per_model"][role]["depth_profile"]:
                writer.writerow({"model_role": role, **row})


def _write_svg(path: Path, analysis: Mapping[str, Any]) -> None:
    width, height = 1120, 720
    left, right, top, bottom = 95, 285, 55, 125
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [
        float(row["english_unrestricted"])
        for role in MODEL_ORDER
        for row in analysis["per_model"][role]["depth_profile"]
    ]
    y_min = min(-0.02, min(values))
    y_max = max(0.02, max(values))
    pad = max(0.005, (y_max - y_min) * 0.08)
    y_min -= pad
    y_max += pad
    colors = (
        "#0072B2",
        "#009E73",
        "#E69F00",
        "#CC79A7",
        "#56B4E9",
        "#D55E00",
        "#332288",
        "#F0A3FF",
        "#666666",
    )

    def x(value: float) -> float:
        return left + value * plot_width

    def y(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="95" y="30" font-family="sans-serif" font-size="20" font-weight="600">T18: fresh raw emoji → English short name over depth</text>',
    ]
    for tick in np.linspace(y_min, y_max, 7):
        lines.append(
            f'<line x1="{left}" x2="{left + plot_width}" y1="{y(tick):.2f}" y2="{y(tick):.2f}" stroke="#dddddd"/>'
        )
        lines.append(
            f'<text x="{left - 10}" y="{y(tick) + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick:.3f}</text>'
        )
    lines.append(
        f'<line x1="{left}" x2="{left + plot_width}" y1="{y(0):.2f}" y2="{y(0):.2f}" stroke="#222222" stroke-width="1.2"/>'
    )
    for depth in DEPTH_ORDER:
        lines.append(
            f'<line x1="{x(depth):.2f}" x2="{x(depth):.2f}" y1="{top}" y2="{top + plot_height}" stroke="#eeeeee"/>'
        )
        lines.append(
            f'<text x="{x(depth):.2f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="sans-serif" font-size="12">{depth:g}</text>'
        )
    for index, role in enumerate(MODEL_ORDER):
        curve = analysis["per_model"][role]["depth_profile"]
        points = " ".join(
            f"{x(float(row['normalized_depth'])):.2f},{y(float(row['english_unrestricted'])):.2f}"
            for row in curve
        )
        color = colors[index]
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.4"/>'
        )
        for row in curve:
            lines.append(
                f'<circle cx="{x(float(row["normalized_depth"])):.2f}" cy="{y(float(row["english_unrestricted"])):.2f}" r="2.8" fill="{color}"/>'
            )
        legend_y = top + 18 + index * 28
        lines.append(
            f'<line x1="{left + plot_width + 24}" x2="{left + plot_width + 54}" y1="{legend_y}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>'
        )
        lines.append(
            f'<text x="{left + plot_width + 62}" y="{legend_y + 4}" font-family="sans-serif" font-size="12">{html.escape(role)}</text>'
        )
    lines.extend(
        [
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 60}" text-anchor="middle" font-family="sans-serif" font-size="14">normalized decoder depth</text>',
            f'<text x="22" y="{top + plot_height / 2:.2f}" transform="rotate(-90 22 {top + plot_height / 2:.2f})" text-anchor="middle" font-family="sans-serif" font-size="14">equal-system top-1 contrast</text>',
            '<text x="95" y="700" font-family="sans-serif" font-size="11" fill="#555555">Descriptive full-depth atlas; the frozen primary uses only depths 0.75, 0.875, and 1.0.</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(output_root: Path, analysis: Mapping[str, Any]) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=False)
    analysis_path = output_root / "secondary_analysis.json"
    csv_path = output_root / "depth_curves.csv"
    svg_path = output_root / "depth_curves.svg"
    analysis_path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(csv_path, analysis)
    _write_svg(svg_path, analysis)
    hashes = {path.name: _sha256(path) for path in (analysis_path, csv_path, svg_path)}
    (output_root / "SHA256SUMS").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in hashes.items()),
        encoding="utf-8",
    )
    return {
        "status": "post_outcome_secondary_outputs_complete",
        "protocol_id": PROTOCOL_ID,
        "outputs": hashes,
        "model_forward_calls": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument(
        "--selection",
        type=Path,
        default=ROOT
        / "data/manifests/fresh_composite_glyph_lexical_confirmation_v0.json",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    analysis = build_secondary_analysis(
        summary_root=args.summary_root,
        analysis_root=args.analysis_root,
        selection_path=args.selection,
    )
    receipt = write_outputs(args.output_root, analysis)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
