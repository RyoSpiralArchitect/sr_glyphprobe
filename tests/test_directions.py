from __future__ import annotations

import numpy as np

from glyphprobe.analysis.directions import (
    build_direction_replicates,
    random_direction,
    scale_intervention,
)


def test_panel_centering_and_seed_reproducibility() -> None:
    rng = np.random.default_rng(7)
    emoji = rng.normal(size=(4, 10, 2, 8)).astype(np.float32)
    neutral = rng.normal(size=(10, 2, 8)).astype(np.float32)
    first = build_direction_replicates(
        emoji,
        neutral,
        seeds=[11, 29],
        replicate_mode="wrapper_subsample",
        wrapper_subsample_fraction=0.5,
        centroid_mode="panel",
    )
    second = build_direction_replicates(
        emoji,
        neutral,
        seeds=[11, 29],
        replicate_mode="wrapper_subsample",
        wrapper_subsample_fraction=0.5,
        centroid_mode="panel",
    )
    assert np.allclose(first[0].directions.mean(axis=0), 0.0, atol=1e-6)
    assert first[0].wrapper_indices == second[0].wrapper_indices
    assert np.array_equal(first[0].directions, second[0].directions)
    assert first[0].wrapper_indices != first[1].wrapper_indices


def test_scale_intervention_matches_rms_and_global_clip() -> None:
    direction = np.arange(1, 17, dtype=np.float32)
    target = np.linspace(-2.0, 2.0, 16, dtype=np.float32)
    perturbation, metadata = scale_intervention(
        direction,
        target,
        strength=0.10,
        normalization="rms",
        clip_mode="global_rms",
        clip_max_ratio=0.25,
    )
    assert np.isclose(metadata["perturbation_to_target_rms"], 0.10, atol=1e-6)
    assert metadata["clipped"] is False
    assert perturbation.shape == direction.shape

    _, clipped = scale_intervention(
        direction,
        target,
        strength=0.50,
        normalization="rms",
        clip_mode="global_rms",
        clip_max_ratio=0.20,
    )
    assert clipped["clipped"] is True
    assert np.isclose(clipped["perturbation_to_target_rms"], 0.20, atol=1e-6)


def test_random_control_is_outside_panel_span() -> None:
    panel = np.zeros((2, 8), dtype=np.float64)
    panel[0, 0] = 1.0
    panel[1, 1] = 1.0
    vector = random_direction(8, seed=17, remove_span=panel)
    assert abs(float(vector @ panel[0])) < 1e-6
    assert abs(float(vector @ panel[1])) < 1e-6
    assert np.isclose(np.sqrt(np.mean(vector**2)), 1.0, atol=1e-6)
