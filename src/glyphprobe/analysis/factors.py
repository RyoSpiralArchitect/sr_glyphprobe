from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from glyphprobe.config import EmojiItem


def cosine(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    x = np.asarray(a, dtype=np.float64).ravel()
    y = np.asarray(b, dtype=np.float64).ravel()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(np.dot(x, y) / denom) if denom > eps else 0.0


def pairwise_cosine(vectors: np.ndarray) -> np.ndarray:
    values = np.asarray(vectors, dtype=np.float64)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    normalized = values / np.maximum(norms, 1e-12)
    return normalized @ normalized.T


def effective_rank(vectors: np.ndarray, eps: float = 1e-12) -> float:
    values = np.asarray(vectors, dtype=np.float64)
    singular = np.linalg.svd(values, compute_uv=False)
    energy = singular**2
    total = float(energy.sum())
    if total <= eps:
        return 0.0
    p = energy / total
    entropy = -float(np.sum(p * np.log(np.maximum(p, eps))))
    return float(np.exp(entropy))


def balanced_two_factor_decomposition(
    vectors: np.ndarray,
    items: list[EmojiItem],
    *,
    factor_a: str = "color",
    factor_b: str = "shape",
) -> dict[str, Any]:
    """Exact ANOVA-style vector decomposition for a complete balanced panel."""
    values = np.asarray(vectors, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != len(items):
        raise ValueError("vectors must be [items, dimensions]")
    levels_a = sorted({item.factors.get(factor_a, "") for item in items})
    levels_b = sorted({item.factors.get(factor_b, "") for item in items})
    if "" in levels_a or "" in levels_b:
        return {"available": False, "reason": "missing factor labels"}
    cells: dict[tuple[str, str], int] = {}
    for index, item in enumerate(items):
        key = (item.factors[factor_a], item.factors[factor_b])
        if key in cells:
            return {"available": False, "reason": "duplicate factor cell"}
        cells[key] = index
    expected = {(a, b) for a in levels_a for b in levels_b}
    if set(cells) != expected:
        return {"available": False, "reason": "panel is not a complete factorial grid"}

    grand = values.mean(axis=0)
    effect_a: dict[str, np.ndarray] = {}
    effect_b: dict[str, np.ndarray] = {}
    for a in levels_a:
        effect_a[a] = np.mean([values[cells[(a, b)]] for b in levels_b], axis=0) - grand
    for b in levels_b:
        effect_b[b] = np.mean([values[cells[(a, b)]] for a in levels_a], axis=0) - grand
    interactions: dict[tuple[str, str], np.ndarray] = {}
    residuals: list[np.ndarray] = []
    for a in levels_a:
        for b in levels_b:
            interaction = values[cells[(a, b)]] - grand - effect_a[a] - effect_b[b]
            interactions[(a, b)] = interaction
            residuals.append(interaction)

    centered = values - grand
    total_energy = float(np.square(centered).sum())
    # Balanced-design multiplicities are required for comparable sums of squares.
    energy_a = float(len(levels_b) * sum(np.square(v).sum() for v in effect_a.values()))
    energy_b = float(len(levels_a) * sum(np.square(v).sum() for v in effect_b.values()))
    energy_interaction = float(sum(np.square(v).sum() for v in residuals))
    denom = max(total_energy, 1e-12)
    reconstruction_error = max(
        float(
            np.max(
                [
                    np.abs(
                        values[cells[(a, b)]]
                        - (grand + effect_a[a] + effect_b[b] + interactions[(a, b)])
                    ).max()
                    for a in levels_a
                    for b in levels_b
                ]
            )
        ),
        0.0,
    )
    return {
        "available": True,
        "factor_a": factor_a,
        "factor_b": factor_b,
        "levels_a": levels_a,
        "levels_b": levels_b,
        "total_centered_energy": total_energy,
        "factor_a_energy_fraction": energy_a / denom,
        "factor_b_energy_fraction": energy_b / denom,
        "interaction_energy_fraction": energy_interaction / denom,
        "energy_closure": (energy_a + energy_b + energy_interaction) / denom,
        "max_reconstruction_error": reconstruction_error,
        "effect_a_pairwise_cosine": pairwise_cosine(np.stack(list(effect_a.values()))).tolist(),
        "effect_b_pairwise_cosine": pairwise_cosine(np.stack(list(effect_b.values()))).tolist(),
    }


def representation_records(
    emoji_activations: np.ndarray,
    directions_by_seed: dict[int, np.ndarray],
    items: list[EmojiItem],
    layers: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    acts = np.asarray(emoji_activations, dtype=np.float64)
    per_item: list[dict[str, Any]] = []
    per_layer: list[dict[str, Any]] = []
    for layer_idx, layer in enumerate(layers):
        means = acts[:, :, layer_idx, :].mean(axis=1)
        matrix = pairwise_cosine(means)
        per_layer.append(
            {
                "layer": layer,
                "kind": "source_panel_geometry",
                "effective_rank": effective_rank(means - means.mean(axis=0)),
                "mean_off_diagonal_cosine": float(
                    (matrix.sum() - np.trace(matrix)) / max(matrix.size - len(matrix), 1)
                ),
                "pairwise_cosine": matrix.tolist(),
                "factor_decomposition": balanced_two_factor_decomposition(means, items),
            }
        )
        for emoji_idx, item in enumerate(items):
            wrapper_vectors = acts[emoji_idx, :, layer_idx, :]
            wrapper_mean = wrapper_vectors.mean(axis=0)
            centered = wrapper_vectors - wrapper_mean
            split_cosines: list[float] = []
            for seed, directions in directions_by_seed.items():
                del seed
                split_cosines.append(cosine(directions[emoji_idx, layer_idx], wrapper_mean - means.mean(axis=0)))
            per_item.append(
                {
                    "emoji_id": item.id,
                    "glyph": item.glyph,
                    "layer": layer,
                    "source_mean_rms": float(np.sqrt(np.mean(wrapper_mean**2))),
                    "wrapper_dispersion_rms": float(np.sqrt(np.mean(centered**2))),
                    "direction_replicate_alignment_mean": float(np.mean(split_cosines)),
                    "direction_replicate_alignment_min": float(np.min(split_cosines)),
                }
            )
    return per_item, per_layer


def same_label_parallelism(
    directions: np.ndarray,
    items: list[EmojiItem],
    *,
    subtract_factor: str,
    compare_factor: str,
) -> dict[str, Any]:
    """Compare pairwise differences across matched levels, e.g. circle-square by color."""
    values = np.asarray(directions, dtype=np.float64)
    groups: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
    for item, vector in zip(items, values):
        a = item.factors.get(subtract_factor)
        b = item.factors.get(compare_factor)
        if a is not None and b is not None:
            groups[b][a] = vector
    subtract_levels = sorted({key for group in groups.values() for key in group})
    if len(subtract_levels) != 2:
        return {"available": False, "reason": f"{subtract_factor} needs exactly two levels"}
    deltas: list[np.ndarray] = []
    labels: list[str] = []
    first, second = subtract_levels
    for label, group in sorted(groups.items()):
        if first in group and second in group:
            deltas.append(group[first] - group[second])
            labels.append(label)
    if len(deltas) < 2:
        return {"available": False, "reason": "insufficient matched pairs"}
    matrix = pairwise_cosine(np.stack(deltas))
    return {
        "available": True,
        "contrast": f"{first}-{second}",
        "matched_levels": labels,
        "pairwise_cosine": matrix.tolist(),
        "mean_off_diagonal_cosine": float(
            (matrix.sum() - np.trace(matrix)) / max(matrix.size - len(matrix), 1)
        ),
    }
