from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class DirectionReplicate:
    seed: int
    wrapper_indices: list[int]
    directions: np.ndarray  # [emoji, layer, d_model]
    panel_means: np.ndarray  # [emoji, layer, d_model]
    generic_emoji_direction: np.ndarray  # [layer, d_model]


def rms(vector: np.ndarray, *, axis: int | tuple[int, ...] | None = None) -> np.ndarray:
    return np.sqrt(np.mean(np.square(vector, dtype=np.float64), axis=axis))


def l2(vector: np.ndarray, *, axis: int | tuple[int, ...] | None = None) -> np.ndarray:
    return np.sqrt(np.sum(np.square(vector, dtype=np.float64), axis=axis))


def normalize_vector(vector: np.ndarray, mode: str = "rms", eps: float = 1e-12) -> np.ndarray:
    value = np.asarray(vector, dtype=np.float64)
    if mode == "none":
        return value.copy()
    denom = float(rms(value) if mode == "rms" else l2(value))
    if denom <= eps:
        return np.zeros_like(value)
    return value / denom


def build_direction_replicates(
    emoji_activations: np.ndarray,
    neutral_activations: np.ndarray,
    *,
    seeds: list[int],
    replicate_mode: str,
    wrapper_subsample_fraction: float,
    centroid_mode: str,
) -> list[DirectionReplicate]:
    """Construct panel-centered directions from source activation tensors.

    Args:
        emoji_activations: ``[emoji, wrapper, layer, d_model]``.
        neutral_activations: ``[wrapper, layer, d_model]``.
    """
    acts = np.asarray(emoji_activations, dtype=np.float64)
    neutral = np.asarray(neutral_activations, dtype=np.float64)
    if acts.ndim != 4 or neutral.ndim != 3:
        raise ValueError("Unexpected activation tensor rank")
    if acts.shape[1:] != neutral.shape:
        raise ValueError("Emoji and neutral activation shapes are inconsistent")
    n_wrappers = acts.shape[1]
    n_select = max(2, int(round(wrapper_subsample_fraction * n_wrappers)))
    n_select = min(n_select, n_wrappers)
    output: list[DirectionReplicate] = []
    for seed in seeds:
        if replicate_mode == "full_direction":
            indices = np.arange(n_wrappers)
        elif replicate_mode == "wrapper_subsample":
            rng = np.random.default_rng(seed)
            indices = np.sort(rng.choice(n_wrappers, size=n_select, replace=False))
        else:
            raise ValueError(f"Unknown replicate mode: {replicate_mode}")
        panel_means = acts[:, indices, :, :].mean(axis=1)
        neutral_mean = neutral[indices, :, :].mean(axis=0)
        panel_centroid = panel_means.mean(axis=0)
        if centroid_mode == "panel":
            directions = panel_means - panel_centroid[None, :, :]
        elif centroid_mode == "neutral":
            directions = panel_means - neutral_mean[None, :, :]
        elif centroid_mode == "none":
            directions = panel_means.copy()
        else:
            raise ValueError(f"Unknown centroid mode: {centroid_mode}")
        generic = panel_centroid - neutral_mean
        output.append(
            DirectionReplicate(
                seed=seed,
                wrapper_indices=[int(value) for value in indices],
                directions=directions.astype(np.float32),
                panel_means=panel_means.astype(np.float32),
                generic_emoji_direction=generic.astype(np.float32),
            )
        )
    return output


def scale_intervention(
    direction: np.ndarray,
    target_activation: np.ndarray,
    *,
    strength: float,
    normalization: str,
    clip_mode: str,
    clip_max_ratio: float,
    eps: float = 1e-12,
) -> tuple[np.ndarray, dict[str, float | bool]]:
    unit = normalize_vector(direction, normalization, eps=eps)
    target_rms = float(rms(np.asarray(target_activation, dtype=np.float64)))
    raw = unit * (strength * target_rms)
    raw_rms = float(rms(raw))
    clipped = False
    clip_scale = 1.0
    if clip_mode == "global_rms":
        max_rms = clip_max_ratio * target_rms
        if raw_rms > max_rms > eps:
            clip_scale = max_rms / raw_rms
            raw = raw * clip_scale
            clipped = True
    elif clip_mode != "none":
        raise ValueError(f"Unknown clip mode: {clip_mode}")
    achieved_rms = float(rms(raw))
    return raw.astype(np.float32), {
        "target_activation_rms": target_rms,
        "direction_raw_rms": float(rms(direction)),
        "requested_strength": float(strength),
        "perturbation_rms": achieved_rms,
        "perturbation_to_target_rms": achieved_rms / max(target_rms, eps),
        "clip_scale": float(clip_scale),
        "clipped": clipped,
    }


def random_direction(
    d_model: int,
    *,
    seed: int,
    remove_span: np.ndarray | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vector = rng.normal(size=d_model)
    if remove_span is not None and remove_span.size:
        basis = np.asarray(remove_span, dtype=np.float64)
        if basis.ndim == 1:
            basis = basis[None, :]
        # SVD gives an orthonormal row-space basis and is stable for collinear panel directions.
        _, singular, vh = np.linalg.svd(basis, full_matrices=False)
        keep = singular > max(singular[0] * 1e-8, 1e-12) if singular.size else []
        if np.any(keep):
            q = vh[np.asarray(keep)]
            vector = vector - q.T @ (q @ vector)
    return normalize_vector(vector, "rms").astype(np.float32)
