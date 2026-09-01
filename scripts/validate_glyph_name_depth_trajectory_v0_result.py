#!/usr/bin/env python3
"""Independently validate the compact T17-GN result against T10."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


PROTOCOL_ID = "glyphprobe-glyph-name-depth-trajectory-v0"
EXPECTED_ANALYSIS_SHA256 = (
    "ed615103d85608893caf207c856a01922a4e744c6f9713f0293aa223bf8139e4"
)
EXPECTED_CURVE_CSV_SHA256 = (
    "806780db8d74e06f038e32820c355d8ef54733530aab59ed2777137dabcd2098"
)
EXPECTED_FIGURE_SHA256 = (
    "0733cd392fd856f2874629403b500bb813fc6105be9ee8365ac88c10c3f43428"
)
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
DEPTHS = (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)
EXPECTED_PEAK_COUNTS = {"0": 2, "0.125": 1, "0.75": 1, "0.875": 5}


class ValidationError(RuntimeError):
    """Raised when compact T17-GN evidence is inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def _close(first: float, second: float) -> bool:
    return abs(float(first) - float(second)) <= 1e-15


def validate(
    *,
    analysis_path: Path,
    curve_csv_path: Path,
    figure_path: Path,
    t10_model_results_path: Path,
    output: Path,
) -> dict[str, Any]:
    _require(
        _sha256(analysis_path) == EXPECTED_ANALYSIS_SHA256, "Analysis hash mismatch"
    )
    _require(
        _sha256(curve_csv_path) == EXPECTED_CURVE_CSV_SHA256, "Curve CSV hash mismatch"
    )
    _require(_sha256(figure_path) == EXPECTED_FIGURE_SHA256, "Figure hash mismatch")
    analysis = _read_json(analysis_path)
    t10 = _read_json(t10_model_results_path)
    _require(analysis.get("protocol_id") == PROTOCOL_ID, "Protocol mismatch")
    _require(
        analysis.get("status") == "glyph_name_depth_trajectory_analysis_complete",
        "Analysis incomplete",
    )
    _require(tuple(analysis["model_order"]) == MODEL_ORDER, "Model order mismatch")
    _require(
        tuple(float(value) for value in analysis["normalized_depth_fractions"])
        == DEPTHS,
        "Depth roster mismatch",
    )
    _require(set(analysis["results"]) == set(MODEL_ORDER), "Result roster mismatch")
    audit = analysis["audit"]
    _require(audit["status"] == "all_nine_roles_complete", "Run audit incomplete")
    _require(int(audit["roles_complete"]) == 9, "Role count mismatch")
    _require(int(audit["shards_complete"]) == 90, "Shard count mismatch")
    _require(int(audit["model_forward_calls"]) == 15_768, "Forward count mismatch")
    _require(int(audit["readout_vectors"]) == 567_648, "Readout count mismatch")
    _require(int(audit["intervention_calls"]) == 0, "Unexpected intervention")
    _require(int(audit["generation_calls"]) == 0, "Unexpected generation")

    final_replay: dict[str, Any] = {}
    peak_counts: dict[str, int] = {}
    final_margin_positive = 0
    final_cka_positive = 0
    for role in MODEL_ORDER:
        result = analysis["results"][role]
        curve = result["depth_curve"]
        _require(len(curve) == 9, f"Depth row count mismatch: {role}")
        _require(
            [float(row["normalized_depth"]) for row in curve] == list(DEPTHS),
            f"Depth order mismatch: {role}",
        )
        cells = result["cell_metrics"]
        _require(len(cells) == 72, f"Cell count mismatch: {role}")
        final_cells = [row for row in cells if float(row["normalized_depth"]) == 1.0]
        _require(len(final_cells) == 8, f"Final context count mismatch: {role}")
        observed_full = [
            float(
                row["unrestricted"]["glyph_name_minus_glyph_codepoint"][
                    "top1_accuracy_forward"
                ]
            )
            for row in final_cells
        ]
        observed_matched = [
            float(
                row["tokenization_matched"]["glyph_name_minus_glyph_codepoint"][
                    "top1_accuracy_forward"
                ]
            )
            for row in final_cells
        ]
        expected_full = [
            float(value)
            for value in t10[role]["unrestricted_component"]["contrast_by_cell"]
        ]
        expected_matched = [
            float(value)
            for value in t10[role]["tokenization_matched_component"]["contrast_by_cell"]
        ]
        _require(
            all(
                _close(a, b) for a, b in zip(observed_full, expected_full, strict=True)
            ),
            f"T10 full replay mismatch: {role}",
        )
        _require(
            all(
                _close(a, b)
                for a, b in zip(observed_matched, expected_matched, strict=True)
            ),
            f"T10 matched replay mismatch: {role}",
        )
        final = curve[-1]
        _require(
            _close(
                final["headline_top1_contrast_mean"],
                t10[role]["unrestricted_component"][
                    "observed_equal_cell_mean_contrast"
                ],
            ),
            f"T10 full mean mismatch: {role}",
        )
        _require(
            _close(
                final["headline_top1_contrast_minimum_context"],
                t10[role]["unrestricted_component"]["observed_minimum_cell_contrast"],
            ),
            f"T10 full minimum mismatch: {role}",
        )
        _require(
            _close(
                final["tokenization_matched_top1_contrast_mean"],
                t10[role]["tokenization_matched_component"][
                    "observed_equal_cell_mean_contrast"
                ],
            ),
            f"T10 matched mean mismatch: {role}",
        )
        _require(
            float(final["bootstrap_95_percent_interval"][0]) > 0.0,
            f"Final bootstrap lower not positive: {role}",
        )
        final_margin_positive += float(final["paired_margin_contrast_mean"]) > 0.0
        final_cka_positive += float(final["centered_linear_cka_contrast_mean"]) > 0.0
        peak = f"{float(result['trajectory']['peak_normalized_depth']):g}"
        peak_counts[peak] = peak_counts.get(peak, 0) + 1
        final_replay[role] = {
            "unrestricted_cell_contrasts_exact": True,
            "tokenization_matched_cell_contrasts_exact": True,
            "final_mean": float(final["headline_top1_contrast_mean"]),
            "final_minimum_context": float(
                final["headline_top1_contrast_minimum_context"]
            ),
            "peak_normalized_depth": float(
                result["trajectory"]["peak_normalized_depth"]
            ),
        }
    _require(peak_counts == EXPECTED_PEAK_COUNTS, "Peak-depth distribution mismatch")
    _require(final_margin_positive == 9, "Final paired-margin contrast count mismatch")
    _require(final_cka_positive == 4, "Final CKA contrast count mismatch")

    cross = {
        float(row["normalized_depth"]): row
        for row in analysis["cross_model_depth_profile"]
    }
    _require(set(cross) == set(DEPTHS), "Cross-model depth roster mismatch")
    _require(
        int(cross[0.375]["positive_model_count"]) == 9,
        "Nine-model point convergence depth changed",
    )
    for depth in (0.5, 0.75, 0.875, 1.0):
        _require(
            int(cross[depth]["bootstrap_lower_positive_model_count"]) == 9,
            f"Nine-model interval convergence changed: {depth}",
        )
    for depth in (0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0):
        _require(
            int(cross[depth]["tokenization_matched_positive_model_count"]) == 9,
            f"Matched convergence changed: {depth}",
        )

    with curve_csv_path.open(encoding="utf-8", newline="") as handle:
        curve_rows = list(csv.DictReader(handle))
    _require(len(curve_rows) == 81, "Curve CSV row count mismatch")
    svg = figure_path.read_text(encoding="utf-8")
    _require(svg.count("<polyline ") == 9, "Figure model curve count mismatch")
    _require(svg.count("<circle ") == 81, "Figure point count mismatch")

    boundaries = (
        "confirmatory_claim_authorized",
        "rendered_glyph_perception_claim_authorized",
        "emoji_meaning_claim_authorized",
        "tokenizer_independent_claim_authorized",
        "causal_or_behavioral_claim_authorized",
        "model_population_generality_claim_authorized",
    )
    _require(
        all(analysis[key] is False for key in boundaries), "Claim boundary changed"
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "independent_compact_validation_pass",
        "analysis_sha256": EXPECTED_ANALYSIS_SHA256,
        "curve_csv_sha256": EXPECTED_CURVE_CSV_SHA256,
        "figure_sha256": EXPECTED_FIGURE_SHA256,
        "source_t10_model_results_sha256": _sha256(t10_model_results_path),
        "run_audit": {
            key: audit[key]
            for key in (
                "roles_complete",
                "shards_complete",
                "model_forward_calls",
                "readout_vectors",
                "elapsed_seconds",
                "maximum_peak_cuda_memory_bytes",
                "intervention_calls",
                "generation_calls",
            )
        },
        "t10_final_depth_exact_replay": final_replay,
        "headline_checks": {
            "all_nine_point_estimates_positive_from_depth_0p375": True,
            "all_nine_bootstrap_lowers_positive_at_depths": [0.5, 0.75, 0.875, 1.0],
            "all_nine_token_matched_point_estimates_positive_from_depth_0p25": True,
            "peak_depth_model_counts": peak_counts,
            "final_paired_margin_positive_model_count": final_margin_positive,
            "final_cka_contrast_positive_model_count": final_cka_positive,
        },
        "curve_csv_rows": len(curve_rows),
        "figure_model_curves": 9,
        "figure_points": 81,
        "claim_boundaries_all_false": list(boundaries),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis",
        type=Path,
        default=root
        / "validation/glyph_name_depth_trajectory_v0/results/analysis.json",
    )
    parser.add_argument(
        "--curve-csv",
        type=Path,
        default=root
        / "validation/glyph_name_depth_trajectory_v0/results/depth_curves.csv",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=root
        / "validation/glyph_name_depth_trajectory_v0/results/depth_curves.svg",
    )
    parser.add_argument(
        "--t10-model-results",
        type=Path,
        default=root
        / "artifacts/semantic_atlas_cross_model_replication_v0/analysis/model_cell_results.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root
        / "validation/glyph_name_depth_trajectory_v0/independent_validation.json",
    )
    args = parser.parse_args()
    result = validate(
        analysis_path=args.analysis,
        curve_csv_path=args.curve_csv,
        figure_path=args.figure,
        t10_model_results_path=args.t10_model_results,
        output=args.output,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
