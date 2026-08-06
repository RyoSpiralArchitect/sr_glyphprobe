from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from glyphprobe.analysis.metrics import countsketch


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "analyze_countsketch_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("countsketch_sensitivity_script", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.mark.parametrize("target_dim", [48, 32, 24])
def test_fold_matches_direct_same_seed_countsketch(target_dim: int) -> None:
    rng = np.random.default_rng(20260806)
    raw = rng.normal(size=50_257)
    seed = 8_675_309
    stored = countsketch(raw, 96, seed)

    folded = MODULE.fold_normalized_countsketch(
        stored, target_dim, source_seed=seed
    )
    direct = countsketch(raw, target_dim, seed)

    np.testing.assert_allclose(folded, direct, rtol=2e-6, atol=2e-7)
    assert np.linalg.norm(folded) == pytest.approx(1.0, abs=2e-7)


def test_fold_zero_vector_remains_zero() -> None:
    folded = MODULE.fold_normalized_countsketch(
        np.zeros(96), 32, source_seed=11
    )
    np.testing.assert_array_equal(folded, np.zeros(32, dtype=np.float32))


def test_fold_rejects_new_seed_and_non_divisor_dimension() -> None:
    with pytest.raises(MODULE.SensitivityError, match="new CountSketch seed"):
        MODULE.fold_normalized_countsketch(
            np.ones(96), 48, source_seed=11, target_seed=12
        )
    with pytest.raises(MODULE.SensitivityError, match="not a divisor"):
        MODULE.fold_normalized_countsketch(np.ones(96), 40, source_seed=11)


def test_recompute_summary_accepts_compact_per_target_rows() -> None:
    rows: list[dict] = []
    seed = 17
    for condition_index, condition_id in enumerate(("a", "b", "c")):
        for target_index in range(8):
            raw = np.zeros(257)
            raw[condition_index * 31 + target_index] = 1.0
            raw[200 + target_index] = 0.01
            rows.append(
                {
                    "layer": 2,
                    "strength": 0.05,
                    "seed": 101,
                    "condition_type": "emoji",
                    "condition_id": condition_id,
                    "target_id": f"t{target_index}",
                    "target_group": f"g{target_index % 2}",
                    "fingerprint": countsketch(raw, 96, seed).tolist(),
                }
            )
    for condition_index, condition_id in enumerate(("r0", "r1")):
        for target_index in range(8):
            raw = np.ones(257) * (condition_index + 1)
            raw[target_index] += 0.001
            rows.append(
                {
                    "layer": 2,
                    "strength": 0.05,
                    "seed": 101,
                    "condition_type": "random",
                    "condition_id": condition_id,
                    "target_id": f"t{target_index}",
                    "target_group": f"g{target_index % 2}",
                    "fingerprint": countsketch(raw, 96, seed).tolist(),
                }
            )

    compact = MODULE.compact_fingerprint_rows(rows)
    folded = MODULE.fold_rows(compact, 48, source_seed=seed)
    summaries = MODULE.recompute_fingerprint_summaries(
        folded,
        fingerprint_seed=seed,
        fingerprint_dim=48,
        split_half_repeats=5,
        label_permutations=9,
    )

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary["fingerprint_dim"] == 48
    assert summary["emoji_condition_count"] == 3
    assert summary["emoji_target_count"] == 8
    assert summary["emoji_split_repeat_count"] == 5
    assert summary["emoji_label_permutation_count"] == 9
    assert np.isfinite(summary["emoji_advantage_over_random"])


def test_aggregate_summary_rows_are_rejected_as_not_refoldable() -> None:
    rows = [
        {
            "layer": 2,
            "strength": 0.05,
            "seed": 101,
            "condition_type": "emoji",
            "condition_id": "panel",
            "target_id": "aggregate",
            "emoji_advantage_over_random": 0.5,
        }
    ]
    with pytest.raises(MODULE.SensitivityError, match="cannot be refolded"):
        MODULE.compact_fingerprint_rows(rows)


def test_matched_panel_report_is_paired_and_descriptive(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    null_a = tmp_path / "null-a"
    null_b = tmp_path / "null-b"
    cells = [(2, 0.05, 101), (4, 0.05, 101)]

    def rows(values: list[float]) -> list[dict]:
        return [
            {
                "layer": key[0],
                "strength": key[1],
                "seed": key[2],
                "emoji_separation": value,
                "emoji_advantage_over_random": value,
            }
            for key, value in zip(cells, values)
        ]

    _write_jsonl(primary / "fingerprint_summary.jsonl", rows([0.8, 0.2]))
    _write_jsonl(null_a / "fingerprint_summary.jsonl", rows([0.3, 0.4]))
    _write_jsonl(null_b / "fingerprint_summary.jsonl", rows([0.5, 0.2]))

    report = MODULE.build_matched_panel_report(primary, [null_a, null_b])

    first, second = report["cells"]
    assert first["matched_null_median"] == pytest.approx(0.4)
    assert first["additive_delta_primary_minus_null_median"] == pytest.approx(0.4)
    assert first["primary_midrank_percentile_within_matched_nulls"] == 1.0
    assert first["relative_attenuation_null_over_primary"] == pytest.approx(0.5)
    assert first["sign_preserved_after_subtraction"] is True
    assert second["additive_delta_primary_minus_null_median"] == pytest.approx(-0.1)
    assert second["sign_reversal_after_subtraction"] is True
    assert report["independence_boundary"]["cells_treated_as_independent_samples"] is False
    assert report["independence_boundary"]["inferential_statistics_across_cells"] is False
    assert "p_value" not in report["descriptive_summary"]


def test_matched_panel_report_requires_identical_cells(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    null = tmp_path / "null"
    _write_jsonl(
        primary / "fingerprint_summary.jsonl",
        [
            {
                "layer": 2,
                "strength": 0.05,
                "seed": 101,
                "emoji_separation": 0.5,
                "emoji_advantage_over_random": 0.5,
            }
        ],
    )
    _write_jsonl(
        null / "fingerprint_summary.jsonl",
        [
            {
                "layer": 4,
                "strength": 0.05,
                "seed": 101,
                "emoji_separation": 0.2,
                "emoji_advantage_over_random": 0.2,
            }
        ],
    )

    with pytest.raises(MODULE.SensitivityError, match="do not match"):
        MODULE.build_matched_panel_report(primary, [null])
