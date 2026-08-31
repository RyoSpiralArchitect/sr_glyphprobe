from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load(
    ROOT / "scripts" / "run_emoji_steering_specificity_bootstrap_v1.py",
    "run_emoji_steering_specificity_bootstrap_v1_test",
)
V0 = _load(
    ROOT / "scripts" / "analyze_emoji_steering_specificity_outcomes_v0.py",
    "analyze_emoji_steering_specificity_outcomes_v0_bootstrap_test",
)
SUMMARIZER = _load(
    ROOT / "scripts" / "summarize_emoji_steering_specificity_analysis_v0_results.py",
    "summarize_emoji_steering_specificity_analysis_v0_bootstrap_test",
)
AUDITOR = _load(
    ROOT / "scripts" / "audit_emoji_steering_specificity_bootstrap_execution_v1.py",
    "audit_emoji_steering_specificity_bootstrap_execution_v1_test",
)


MODEL = "synthetic_model"
TARGETS = ((0, "target-0", "group-a"), (1, "target-1", "group-b"))
MAGNITUDES = (0.125, 0.25, 0.5)
RANDOM_SEEDS = (0, 1, 2, 3)
SOURCE_OFFSETS = {
    "glyph": 5.0,
    "unicode_name": 3.0,
    "component_name": 2.0,
    "codepoint_literal": 1.0,
    "decomposed_form": 0.5,
}


def _metrics(level: float, entropy_change: float, flip: bool) -> dict[str, object]:
    return {
        "kl_baseline_to_intervened": level,
        "js_divergence": level * 2.0,
        "total_variation": level * 3.0,
        "logit_delta_rms": level * 4.0,
        "baseline_entropy": 20.0,
        "intervened_entropy": 20.0 + entropy_change,
        "argmax_flip": flip,
    }


def _synthetic_rows() -> tuple[list[dict], list[dict], list[dict]]:
    item_rows: list[dict] = []
    for target_index, target_id, target_group in TARGETS:
        for sign in (-1, 1):
            for view in ("glyph", "unicode_name", "decomposed_form"):
                level = 10.0 + target_index + SOURCE_OFFSETS[view] + sign * 0.25
                item_rows.append(
                    {
                        "condition_kind": "item_source_form",
                        "model": MODEL,
                        "item_index": 0,
                        "glyph_system": "zwj",
                        "view": view,
                        "target_index": target_index,
                        "target_id": target_id,
                        "target_group": target_group,
                        "depth_fraction": 0.5,
                        "magnitude": 0.25,
                        "sign": sign,
                        **_metrics(
                            level,
                            sign * SOURCE_OFFSETS[view] / 10.0,
                            view == "glyph",
                        ),
                    }
                )

    prototype_rows: list[dict] = []
    for target_index, target_id, target_group in TARGETS:
        for magnitude in MAGNITUDES:
            for sign in (-1, 1):
                for view, source_offset in SOURCE_OFFSETS.items():
                    level = (
                        10.0
                        + target_index
                        + 0.5
                        + 3.0 * magnitude
                        + sign * 0.25
                        + source_offset
                    )
                    prototype_rows.append(
                        {
                            "condition_kind": "glyph_system_source_form_prototype",
                            "model": MODEL,
                            "glyph_system": "zwj",
                            "view": view,
                            "target_index": target_index,
                            "target_id": target_id,
                            "target_group": target_group,
                            "depth_fraction": 0.5,
                            "magnitude": magnitude,
                            "sign": sign,
                            **_metrics(
                                level,
                                sign * (magnitude + source_offset / 10.0),
                                level >= 15.0,
                            ),
                        }
                    )

    random_rows: list[dict] = []
    for target_index, target_id, target_group in TARGETS:
        for magnitude in MAGNITUDES:
            for seed_index in RANDOM_SEEDS:
                level = 10.0 + target_index + 0.5 + 3.0 * magnitude + seed_index * 0.5
                random_rows.append(
                    {
                        "condition_kind": "random_direction",
                        "model": MODEL,
                        "target_index": target_index,
                        "target_id": target_id,
                        "target_group": target_group,
                        "depth_fraction": 0.5,
                        "magnitude": magnitude,
                        "sign": 1,
                        "seed_index": seed_index,
                        **_metrics(
                            level,
                            magnitude + seed_index / 100.0,
                            seed_index == 3,
                        ),
                    }
                )
    return item_rows, prototype_rows, random_rows


def _bundle():
    return MODULE.build_bundle_arrays(
        *_synthetic_rows(), endpoint_values=V0.endpoint_values, models=[MODEL]
    )


def _dynamic_expected_point_vector(analysis: dict, metadata: dict) -> np.ndarray:
    families = analysis["families"]
    summary = {
        "F1_item_source_form": SUMMARIZER._summarize_f1(
            families["F1_item_source_form"]
        ),
        "F2_prototype_depth_dose": SUMMARIZER._summarize_f2(
            families["F2_prototype_depth_dose"]
        ),
        "F3_random_null_calibration": SUMMARIZER._summarize_f3(
            families["F3_random_null_calibration"]
        ),
    }
    roster = MODULE.generate_estimand_roster(metadata["models"], metadata["depths"])
    values: list[float] = []
    for estimand in roster:
        factors = estimand["factors"]
        table = estimand["table"]
        metric = estimand["metric"]
        if table == "overall_model_sign":
            keys = ("model", "contrast", "sign", "endpoint")
            rows = summary["F1_item_source_form"]["overall_model_sign_rows"]
            value = next(
                row for row in rows if all(row[key] == factors[key] for key in keys)
            )["mean"]
        elif table == "raw_headline_by_model_endpoint_depth":
            keys = ("model", "endpoint", "depth_fraction")
            rows = summary["F2_prototype_depth_dose"][
                "raw_headline_mean_by_model_endpoint_depth"
            ]
            value = next(
                row for row in rows if all(row[key] == factors[key] for key in keys)
            )["mean"]
        elif table == "dose_ordering_by_model_endpoint":
            keys = ("model", "endpoint")
            rows = summary["F2_prototype_depth_dose"]["dose_ordering_by_model_endpoint"]
            value = next(
                row for row in rows if all(row[key] == factors[key] for key in keys)
            )["weighted_mean"]
        elif table == "entropy_antisymmetry_by_model":
            row = next(
                row
                for row in summary["F2_prototype_depth_dose"][
                    "entropy_antisymmetry_by_model"
                ]
                if row["model"] == factors["model"]
            )
            value = row[metric]["weighted_mean"]
        elif table == "by_model_endpoint_depth":
            keys = ("model", "endpoint", "depth_fraction")
            rows = summary["F3_random_null_calibration"]["by_model_endpoint_depth"]
            value = next(
                row for row in rows if all(row[key] == factors[key] for key in keys)
            )[metric]
        else:
            assert table == "by_model_endpoint"
            keys = ("model", "endpoint")
            rows = summary["F3_random_null_calibration"]["by_model_endpoint"]
            value = next(
                row for row in rows if all(row[key] == factors[key] for key in keys)
            )[metric]
        values.append(float(value))
    return np.asarray(values, dtype=np.float64)


def test_frozen_roster_is_complete_systematic_and_unique() -> None:
    document = MODULE.roster_document()
    assert document["estimand_count"] == 600
    assert document["family_counts"] == MODULE.EXPECTED_FAMILY_COUNTS
    rows = document["estimands"]
    assert [row["index"] for row in rows] == list(range(600))
    assert len({row["estimand_id"] for row in rows}) == 600
    assert {row["factors"].get("model") for row in rows} == set(MODULE.PILOT_MODELS)
    assert {
        row["factors"].get("endpoint") for row in rows if "endpoint" in row["factors"]
    } == set(MODULE.ENDPOINT_ORDER)


def test_compact_bundle_exactly_replays_existing_high_level_point_functions() -> None:
    rows = _synthetic_rows()
    analysis = V0.analyze_rows(*rows, bootstrap_replicates=0)
    arrays, metadata = MODULE.build_bundle_arrays(
        *rows, endpoint_values=V0.endpoint_values, models=[MODEL]
    )
    observed = MODULE.observed_values(arrays, metadata)
    expected = _dynamic_expected_point_vector(analysis, metadata)
    assert len(observed) == len(MODULE.generate_estimand_roster([MODEL], [0.5]))
    np.testing.assert_allclose(observed, expected, rtol=0.0, atol=1.0e-12)


def test_counter_sampler_is_deterministic_unbiased_by_construction_and_namespaced() -> (
    None
):
    first = MODULE._counter_sample_counts(
        seed=91,
        namespace="example/a",
        replicate_id=7,
        population_size=168,
    )
    second = MODULE._counter_sample_counts(
        seed=91,
        namespace="example/a",
        replicate_id=7,
        population_size=168,
    )
    other = MODULE._counter_sample_counts(
        seed=91,
        namespace="example/b",
        replicate_id=7,
        population_size=168,
    )
    assert np.array_equal(first, second)
    assert not np.array_equal(first, other)
    assert first.dtype == np.int64
    assert first.shape == (168,)
    assert int(first.sum()) == 168
    assert bool((first >= 0).all())


def test_chunking_and_schedule_order_do_not_change_replicate_vectors() -> None:
    arrays, metadata = _bundle()
    forward = MODULE.compute_chunk_matrix(arrays, metadata, [0, 1, 2])
    split = np.vstack(
        (
            MODULE.compute_chunk_matrix(arrays, metadata, [0]),
            MODULE.compute_chunk_matrix(arrays, metadata, [1, 2]),
        )
    )
    reverse = MODULE.compute_chunk_matrix(arrays, metadata, [2, 1, 0])
    assert np.array_equal(forward, split)
    assert np.array_equal(forward, reverse[::-1])
    assert MODULE._vector_block_sha256([0, 1, 2], forward) == (
        MODULE._vector_block_sha256([0, 1, 2], split)
    )


def test_resampled_median_uses_the_exact_draw_multiset() -> None:
    values = np.asarray([[1.0, 4.0, 7.0, 10.0]])
    counts = np.asarray([0, 2, 0, 2])
    result = MODULE._resampled_median(values, counts)
    assert result.tolist() == [7.0]
    odd = MODULE._resampled_median(values, np.asarray([0, 2, 1, 0]))
    assert odd.tolist() == [4.0]


def test_linear_quantile_rule_is_explicit_and_not_a_runtime_default() -> None:
    values = np.arange(20, dtype=np.float64).reshape(10, 2)
    q = MODULE._linear_quantile(values, 0.25)
    expected = np.asarray([4.5, 5.5])
    assert np.array_equal(q, expected)


def test_partial_merge_fails_before_any_interval_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chunks = tmp_path / "chunks"
    chunks.mkdir()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    output = tmp_path / "merge"
    monkeypatch.setattr(
        MODULE,
        "_audit_freeze",
        lambda: {"status": "bootstrap_execution_freeze_audit_pass"},
    )
    monkeypatch.setattr(MODULE, "_load_roster", lambda: MODULE.roster_document())
    monkeypatch.setattr(
        MODULE,
        "load_bundle",
        lambda _path: (
            {"observed_values": np.zeros(600)},
            {},
            "a" * 64,
        ),
    )
    with pytest.raises(
        MODULE.BootstrapExecutionError, match="incomplete or has extras"
    ):
        MODULE.merge_chunks(bundle=bundle, chunks_root=chunks, output=output)
    assert not output.exists()


def test_freeze_manifest_tamper_is_rejected(tmp_path: Path) -> None:
    source = ROOT / MODULE.FREEZE_PATH
    if not source.exists():
        pytest.skip("Freeze manifest is generated after implementation validation")
    document = json.loads(source.read_text(encoding="utf-8"))
    first = document["input_roster"][0]
    document["inputs"][first]["sha256"] = "0" * 64
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(AUDITOR.BootstrapFreezeError, match="Hash changed"):
        AUDITOR.audit_freeze(tampered)


def test_freeze_auditor_never_parses_scientific_values() -> None:
    result = AUDITOR.audit_design()
    assert result == {
        "status": "bootstrap_execution_design_audit_pass",
        "execution_id": MODULE.EXECUTION_ID,
        "estimand_count": 600,
        "replicates": 20_000,
        "chunk_count": 100,
        "scientific_values_parsed_by_auditor": False,
        "scientific_outcomes_seen_before_freeze": True,
    }
