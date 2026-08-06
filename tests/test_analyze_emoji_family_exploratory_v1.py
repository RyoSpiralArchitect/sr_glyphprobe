from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from typing import Any

import numpy as np
import orjson
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_family_exploratory_v1.py"
SPEC = importlib.util.spec_from_file_location("analyze_emoji_family_exploratory_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _groups() -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(range(group * 4, group * 4 + 4)) for group in range(6))


def _vectors(*, identical_families: bool = False) -> np.ndarray:
    rng = np.random.default_rng(1701)
    vectors = rng.normal(size=(5, 3, 10, 24, 16))
    vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
    if identical_families:
        vectors = np.repeat(vectors[:1], 5, axis=0)
    return vectors


def _direct_score(
    vectors: np.ndarray,
    weights: np.ndarray,
    *,
    source: int,
    prototype: int,
    seed: int,
    target: int,
) -> float:
    held_group = next(group for group in _groups() if target in group)
    training = [index for index in range(24) if index not in held_group]
    prototypes = []
    for slot in range(10):
        total = sum(
            weights[index] * vectors[prototype, seed, slot, index]
            for index in training
        )
        prototypes.append(total / np.linalg.norm(total))
    prototype_matrix = np.stack(prototypes)
    evaluation = vectors[source, seed, :, target]
    cosine_matrix = evaluation @ prototype_matrix.T
    diagonal = np.diag(cosine_matrix)
    mismatched = (cosine_matrix.sum(axis=1) - diagonal) / 9.0
    return float(np.mean(diagonal - mismatched))


def _screening(seed: int) -> dict[str, Any]:
    return {
        "split_seed": seed + 1000,
        "emoji_same_split_cosine": 0.8,
        "emoji_cross_cosine": 0.2,
        "emoji_separation": 0.6,
        "emoji_split_repeat_mean": 0.59,
        "emoji_split_repeat_median": 0.6,
        "emoji_split_repeat_ci_low": 0.5,
        "emoji_split_repeat_ci_high": 0.7,
        "random_same_split_cosine": 0.4,
        "random_cross_cosine": 0.2,
        "random_separation": 0.2,
        "random_split_repeat_mean": 0.19,
        "random_split_repeat_ci_low": 0.1,
        "random_split_repeat_ci_high": 0.3,
        "emoji_advantage_over_random": 0.4,
        "emoji_condition_count": 10,
        "emoji_target_count": 24,
        "emoji_split_repeat_count": 200,
        "random_condition_count": 2,
        "random_target_count": 24,
    }


def test_vectorized_score_matches_direct_weighted_loto_definition() -> None:
    vectors = _vectors()
    weights, _ = MODULE._bootstrap_weights(3, 91, 24, _groups())
    scores = MODULE._score_layer_chunk_by_seed(vectors, weights, _groups())

    for replicate, source, prototype, seed, target in (
        (0, 0, 0, 0, 0),
        (1, 2, 4, 1, 7),
        (2, 4, 1, 2, 23),
    ):
        expected = _direct_score(
            vectors,
            weights[replicate],
            source=source,
            prototype=prototype,
            seed=seed,
            target=target,
        )
        assert scores[replicate, source, prototype, seed, target] == pytest.approx(
            expected, abs=1e-12
        )


def test_bootstrap_is_joint_stratified_and_deterministic() -> None:
    weights_a, draws_a = MODULE._bootstrap_weights(31, 20260808, 24, _groups())
    weights_b, draws_b = MODULE._bootstrap_weights(31, 20260808, 24, _groups())
    assert np.array_equal(weights_a, weights_b)
    assert np.array_equal(draws_a, draws_b)
    assert np.all(weights_a.sum(axis=1) == 24)
    for group in _groups():
        assert np.all(weights_a[:, group].sum(axis=1) == 4)


def test_public_analysis_path_has_no_bootstrap_override() -> None:
    parameters = inspect.signature(MODULE.analyze_exploratory).parameters
    assert "bootstrap_replicates" not in parameters
    assert "bootstrap_seed" not in parameters
    assert "bootstrap_chunk_size" not in parameters
    assert MODULE.BOOTSTRAP_REPLICATES == 20_000
    assert MODULE.BOOTSTRAP_SEED == 20_260_808


def test_identical_family_fingerprints_cancel_family_specificity() -> None:
    layer = _vectors(identical_families=True)
    tensor = np.stack([layer, layer], axis=1)
    observed = MODULE._observed_endpoints(tensor, _groups())
    assert np.max(np.abs(observed["specificity"])) < 1e-12
    assert np.max(np.abs(observed["global_specificity"])) < 1e-12

    weights, draws = MODULE._bootstrap_weights(9, 34, 24, _groups())
    bootstrap = MODULE._bootstrap_endpoints(
        tensor, weights, draws, _groups(), chunk_size=4
    )
    assert np.max(np.abs(bootstrap["specificity_means"])) < 1e-12
    assert np.max(np.abs(bootstrap["global_specificity"])) < 1e-12


def test_public_row_grids_are_complete_and_controls_are_nested_by_seed() -> None:
    layer = _vectors()
    tensor = np.stack([layer, np.roll(layer, 1, axis=-1)], axis=1)
    observed = MODULE._observed_endpoints(tensor, _groups())
    weights, draws = MODULE._bootstrap_weights(7, 55, 24, _groups())
    bootstrap = MODULE._bootstrap_endpoints(
        tensor, weights, draws, _groups(), chunk_size=3
    )
    target_ids = tuple(f"target_{index:02d}" for index in range(24))
    target_groups = {
        target_id: MODULE.TARGET_GROUPS[index // 4]
        for index, target_id in enumerate(target_ids)
    }
    authority = {"target_ids": target_ids, "target_groups": target_groups}
    runs = []
    for family in MODULE.FAMILY_ORDER:
        runs.append(
            {
                "role": family,
                "screening": {
                    (layer_id, seed): _screening(seed)
                    for layer_id in MODULE.LAYERS
                    for seed in MODULE.DIRECTION_SEEDS
                },
                "random_cell_counts": {
                    (layer_id, seed): 48
                    for layer_id in MODULE.LAYERS
                    for seed in MODULE.DIRECTION_SEEDS
                },
                "zero_summary_by_layer": {
                    layer_id: {
                        "row_count": 24,
                        "max_logit_delta_rms": 0.0,
                        "max_activation_delta_rms": 0.0,
                    }
                    for layer_id in MODULE.LAYERS
                },
            }
        )

    family_targets, transfers, family_cells, transfer_cells, layers = MODULE._build_rows(
        runs, authority, observed, bootstrap
    )
    assert [len(family_targets), len(transfers), len(family_cells), len(transfer_cells)] == [
        240,
        960,
        10,
        40,
    ]
    assert len(layers) == 2
    assert all(len(row["descriptive_fingerprint_controls_by_direction_seed"]) == 3 for row in family_cells)
    assert all(
        "emoji_label_permutation_p"
        not in control
        for row in family_cells
        for control in row["descriptive_fingerprint_controls_by_direction_seed"]
    )
    assert all(len(layer_row["full_M_matrix"]["cells"]) == 25 for layer_row in layers)


def test_current_fixed_configs_pass_complete_resolved_validation() -> None:
    for role in MODULE.FAMILY_ORDER:
        config_path = ROOT / MODULE.ROLE_SPECS[role]["config"]
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        MODULE._validate_resolved_config(config, role)


def test_resolved_config_fails_closed_on_endpoint_setting_change() -> None:
    config_path = ROOT / MODULE.ROLE_SPECS["sky"]["config"]
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["metrics"]["fingerprint_seed"] += 1
    with pytest.raises(MODULE.ExploratoryAnalysisError, match="fingerprint_seed"):
        MODULE._validate_resolved_config(config, "sky")


def test_screening_loader_rejects_any_generated_permutation_statistic(
    tmp_path: Path,
) -> None:
    rows = []
    for layer in MODULE.LAYERS:
        for seed in MODULE.DIRECTION_SEEDS:
            row = {
                "layer": layer,
                "seed": seed,
                "strength": MODULE.STRENGTH,
                **_screening(seed),
                "emoji_label_permutation_p": None,
                "emoji_label_permutation_null_mean": None,
                "emoji_label_permutation_null_std": None,
                "emoji_label_permutation_count": 0,
            }
            rows.append(row)
    path = tmp_path / "fingerprint_summary.jsonl"
    path.write_bytes(b"".join(orjson.dumps(row) + b"\n" for row in rows))
    cells, observed_path = MODULE._load_fingerprint_screening(tmp_path, "sky")
    assert observed_path == path
    assert len(cells) == 6
    assert all("emoji_label_permutation_p" not in cell for cell in cells.values())

    rows[0]["emoji_label_permutation_p"] = 0.5
    path.write_bytes(b"".join(orjson.dumps(row) + b"\n" for row in rows))
    with pytest.raises(MODULE.ExploratoryAnalysisError, match="forbidden permutation"):
        MODULE._load_fingerprint_screening(tmp_path, "sky")
