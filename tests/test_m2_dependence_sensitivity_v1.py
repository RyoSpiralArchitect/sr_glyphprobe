from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / "scripts"
    / "analyze_m2_dependence_sensitivity_v1.py"
)
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location(
    "analyze_m2_dependence_sensitivity_v1_script", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


GROUP_INDICES = ((0, 1), (2, 3), (4, 5))


def _unit(vector: np.ndarray) -> np.ndarray:
    return vector / np.linalg.norm(vector)


def _synthetic_layer_vectors() -> np.ndarray:
    """Return [panel, seed, condition, target, dim] nondegenerate fixtures."""

    rng = np.random.default_rng(71)
    panel_count, seed_count, condition_count, target_count, dimension = 4, 2, 3, 6, 8
    vectors = np.empty(
        (panel_count, seed_count, condition_count, target_count, dimension),
        dtype=np.float64,
    )
    condition_axes = np.eye(dimension, dtype=np.float64)[:condition_count]
    for panel in range(panel_count):
        for seed in range(seed_count):
            for condition in range(condition_count):
                for target in range(target_count):
                    # Target-specific terms make the resampled prototypes vary.
                    # Panel-specific mixing gives a nonzero primary-minus-null endpoint.
                    signal = (1.2 - 0.18 * panel) * condition_axes[condition]
                    target_term = rng.normal(size=dimension) * (0.22 + 0.04 * panel)
                    target_term[(target + panel) % dimension] += 0.16 * (target + 1)
                    seed_term = np.zeros(dimension)
                    seed_term[(condition + seed + panel) % dimension] = 0.07
                    vectors[panel, seed, condition, target] = _unit(
                        signal + target_term + seed_term
                    )
    return vectors


def _scalar_rebuilt_mean(
    vectors: np.ndarray,
    weights: np.ndarray,
    group_indices: tuple[tuple[int, ...], ...] = GROUP_INDICES,
) -> float:
    panel_count, seed_count, condition_count, target_count, _ = vectors.shape
    target_group = {
        target: group
        for group, indices in enumerate(group_indices)
        for target in indices
    }
    scores = np.empty((panel_count, target_count), dtype=np.float64)
    for panel in range(panel_count):
        for target in range(target_count):
            group = target_group[target]
            training = [
                other for other in range(target_count) if target_group[other] != group
            ]
            seed_scores: list[float] = []
            for seed in range(seed_count):
                prototypes: list[np.ndarray] = []
                for condition in range(condition_count):
                    prototype_sum = sum(
                        weights[other] * vectors[panel, seed, condition, other]
                        for other in training
                    )
                    prototypes.append(_unit(prototype_sum))
                same: list[float] = []
                cross: list[float] = []
                for condition in range(condition_count):
                    fingerprint = vectors[panel, seed, condition, target]
                    same.append(float(fingerprint @ prototypes[condition]))
                    cross.extend(
                        float(fingerprint @ prototypes[other_condition])
                        for other_condition in range(condition_count)
                        if other_condition != condition
                    )
                seed_scores.append(float(np.mean(same) - np.mean(cross)))
            scores[panel, target] = float(np.mean(seed_scores))
    effects = scores[0] - np.median(scores[1:4], axis=0)
    return float(weights @ effects / weights.sum())


def test_vectorized_refit_matches_scalar_rebuild() -> None:
    vectors = _synthetic_layer_vectors()
    weights = np.asarray(
        [
            [2, 0, 0, 2, 1, 1],
            [0, 2, 1, 1, 2, 0],
            [1, 1, 2, 0, 0, 2],
        ],
        dtype=np.int16,
    )

    observed = MODULE._score_layer_chunk(vectors, weights, GROUP_INDICES)
    expected = np.asarray(
        [_scalar_rebuilt_mean(vectors, row, GROUP_INDICES) for row in weights]
    )

    assert observed == pytest.approx(expected, abs=2e-13)


def test_joint_panel_resampling_cancels_identical_panels() -> None:
    one_panel = _synthetic_layer_vectors()[0]
    identical_panels = np.stack([one_panel, one_panel, one_panel, one_panel], axis=0)
    weights = np.asarray(
        [
            [2, 0, 0, 2, 1, 1],
            [0, 2, 1, 1, 2, 0],
            [1, 1, 2, 0, 0, 2],
        ],
        dtype=np.int16,
    )

    observed = MODULE._score_layer_chunk(identical_panels, weights, GROUP_INDICES)

    assert observed == pytest.approx(np.zeros(weights.shape[0]), abs=2e-15)


def test_refitting_prototypes_changes_the_fixed_score_bootstrap() -> None:
    vectors = _synthetic_layer_vectors()
    weights = MODULE._stratified_bootstrap_weights(
        replicates=199,
        seed=812,
        target_count=6,
        group_indices=GROUP_INDICES,
    )
    rebuilt = MODULE._score_layer_chunk(vectors, weights, GROUP_INDICES)
    point_weights = np.ones(6, dtype=np.int16)

    # Fixed-score resampling holds each target's observed-sample endpoint fixed.
    # Obtain those six effects by selecting one evaluation target at a time while
    # keeping unit weights for prototype construction.
    point_scores = np.empty(6, dtype=np.float64)
    for target in range(6):
        # Recover target effects through the same scalar reference construction.
        panel_count, seed_count, condition_count, target_count, _ = vectors.shape
        target_group = {
            member: group
            for group, indices in enumerate(GROUP_INDICES)
            for member in indices
        }
        panel_scores = np.empty(panel_count, dtype=np.float64)
        for panel in range(panel_count):
            within_seed: list[float] = []
            for seed in range(seed_count):
                training = [
                    other
                    for other in range(target_count)
                    if target_group[other] != target_group[target]
                ]
                prototypes = [
                    _unit(
                        sum(
                            point_weights[other]
                            * vectors[panel, seed, condition, other]
                            for other in training
                        )
                    )
                    for condition in range(condition_count)
                ]
                same = [
                    float(vectors[panel, seed, condition, target] @ prototypes[condition])
                    for condition in range(condition_count)
                ]
                cross = [
                    float(vectors[panel, seed, condition, target] @ prototypes[other])
                    for condition in range(condition_count)
                    for other in range(condition_count)
                    if other != condition
                ]
                within_seed.append(float(np.mean(same) - np.mean(cross)))
            panel_scores[panel] = float(np.mean(within_seed))
        point_scores[target] = panel_scores[0] - float(np.median(panel_scores[1:]))
    fixed = weights @ point_scores / weights.sum(axis=1)

    assert np.max(np.abs(rebuilt - fixed)) > 1e-3
    assert not np.allclose(np.std(rebuilt), np.std(fixed), rtol=1e-3, atol=1e-5)


def test_bootstrap_weights_are_stratified_reproducible_and_joint() -> None:
    first = MODULE._stratified_bootstrap_weights(
        replicates=31,
        seed=20260806,
        target_count=6,
        group_indices=GROUP_INDICES,
    )
    second = MODULE._stratified_bootstrap_weights(
        replicates=31,
        seed=20260806,
        target_count=6,
        group_indices=GROUP_INDICES,
    )

    assert np.array_equal(first, second)
    assert np.all(first[:, [0, 1]].sum(axis=1) == 2)
    assert np.all(first[:, [2, 3]].sum(axis=1) == 2)
    assert np.all(first[:, [4, 5]].sum(axis=1) == 2)
    # The analyzer creates one matrix and passes it to all panels/layers/seeds;
    # there is no panel or seed axis on the multiplicities themselves.
    assert first.shape == (31, 6)
