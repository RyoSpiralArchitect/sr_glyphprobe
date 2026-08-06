from __future__ import annotations

from typing import Any

import numpy as np


def softmax(logits: np.ndarray) -> np.ndarray:
    values = np.asarray(logits, dtype=np.float64)
    shifted = values - np.max(values)
    exp = np.exp(shifted)
    return exp / exp.sum()


def entropy(probabilities: np.ndarray, eps: float = 1e-12) -> float:
    p = np.asarray(probabilities, dtype=np.float64)
    return -float(np.sum(p * np.log(np.maximum(p, eps))))


def cosine(a: np.ndarray, b: np.ndarray, eps: float = 1e-12) -> float:
    x = np.asarray(a, dtype=np.float64).ravel()
    y = np.asarray(b, dtype=np.float64).ravel()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(np.dot(x, y) / denom) if denom > eps else 0.0


def top_indices(values: np.ndarray, k: int) -> np.ndarray:
    array = np.asarray(values)
    k = min(max(int(k), 1), array.size)
    selected = np.argpartition(array, -k)[-k:]
    return selected[np.argsort(array[selected])[::-1]]


def rank_biased_overlap(first: np.ndarray, second: np.ndarray, p: float = 0.9) -> float:
    a = [int(value) for value in first]
    b = [int(value) for value in second]
    depth = min(len(a), len(b))
    if depth == 0:
        return 0.0
    seen_a: set[int] = set()
    seen_b: set[int] = set()
    weighted = 0.0
    overlap = 0
    for d in range(1, depth + 1):
        seen_a.add(a[d - 1])
        seen_b.add(b[d - 1])
        overlap = len(seen_a & seen_b)
        weighted += (overlap / d) * (p ** (d - 1))
    return float((1 - p) * weighted + (overlap / depth) * (p**depth))


def countsketch(values: np.ndarray, dim: int, seed: int) -> np.ndarray:
    vector = np.asarray(values, dtype=np.float64).ravel()
    indices = np.arange(vector.size, dtype=np.uint64)
    with np.errstate(over="ignore"):
        hashed = indices * np.uint64(11400714819323198485) + np.uint64(seed)
        mixed = hashed ^ (hashed >> np.uint64(33))
        buckets = np.asarray(mixed % np.uint64(dim), dtype=np.int64)
        signs = np.where(((mixed >> np.uint64(63)) & np.uint64(1)) == 0, 1.0, -1.0)
    sketch = np.bincount(buckets, weights=vector * signs, minlength=dim).astype(np.float64)
    norm = np.linalg.norm(sketch)
    return (sketch / norm if norm > 1e-12 else sketch).astype(np.float32)


def distribution_metrics(
    baseline_logits: np.ndarray,
    intervened_logits: np.ndarray,
    *,
    top_k: int,
    rbo_p: float,
    fingerprint_dim: int,
    fingerprint_seed: int,
    save_top_deltas: int,
    eps: float = 1e-12,
) -> dict[str, Any]:
    base = np.asarray(baseline_logits, dtype=np.float64)
    changed = np.asarray(intervened_logits, dtype=np.float64)
    if base.shape != changed.shape or base.ndim != 1:
        raise ValueError("Logits must be same-shaped vectors")
    p = softmax(base)
    q = softmax(changed)
    m = 0.5 * (p + q)
    delta = changed - base
    base_top = top_indices(base, top_k)
    changed_top = top_indices(changed, top_k)
    base_set = set(int(v) for v in base_top)
    changed_set = set(int(v) for v in changed_top)
    positive = top_indices(delta, save_top_deltas)
    negative = top_indices(-delta, save_top_deltas)
    base_argmax = int(np.argmax(base))
    changed_argmax = int(np.argmax(changed))
    changed_rank_of_base = int(np.sum(changed > changed[base_argmax]) + 1)
    base_rank_of_changed = int(np.sum(base > base[changed_argmax]) + 1)
    base_sorted = np.partition(base, -2)[-2:]
    changed_sorted = np.partition(changed, -2)[-2:]
    return {
        "kl_base_to_intervened": float(np.sum(p * (np.log(np.maximum(p, eps)) - np.log(np.maximum(q, eps))))),
        "kl_intervened_to_base": float(np.sum(q * (np.log(np.maximum(q, eps)) - np.log(np.maximum(p, eps))))),
        "js_divergence": 0.5
        * float(
            np.sum(p * (np.log(np.maximum(p, eps)) - np.log(np.maximum(m, eps))))
            + np.sum(q * (np.log(np.maximum(q, eps)) - np.log(np.maximum(m, eps))))
        ),
        "total_variation": 0.5 * float(np.abs(p - q).sum()),
        "hellinger": float(np.sqrt(0.5 * np.square(np.sqrt(p) - np.sqrt(q)).sum())),
        "entropy_baseline": entropy(p, eps),
        "entropy_intervened": entropy(q, eps),
        "entropy_delta": entropy(q, eps) - entropy(p, eps),
        "logit_delta_l2": float(np.linalg.norm(delta)),
        "logit_delta_rms": float(np.sqrt(np.mean(delta**2))),
        "logit_delta_max_abs": float(np.max(np.abs(delta))),
        "logit_cosine": cosine(base, changed, eps),
        "probability_cosine": cosine(p, q, eps),
        "top_k_jaccard": float(len(base_set & changed_set) / max(len(base_set | changed_set), 1)),
        "top_k_overlap_fraction": float(len(base_set & changed_set) / max(len(base_set), 1)),
        "rank_biased_overlap": rank_biased_overlap(base_top, changed_top, rbo_p),
        "argmax_flip": base_argmax != changed_argmax,
        "baseline_argmax": base_argmax,
        "intervened_argmax": changed_argmax,
        "intervened_rank_of_baseline_argmax": changed_rank_of_base,
        "baseline_rank_of_intervened_argmax": base_rank_of_changed,
        "baseline_top2_margin": float(np.max(base_sorted) - np.min(base_sorted)),
        "intervened_top2_margin": float(np.max(changed_sorted) - np.min(changed_sorted)),
        "top_positive_delta_ids": [int(v) for v in positive],
        "top_positive_delta_values": [float(delta[v]) for v in positive],
        "top_negative_delta_ids": [int(v) for v in negative],
        "top_negative_delta_values": [float(delta[v]) for v in negative],
        "fingerprint": countsketch(delta, fingerprint_dim, fingerprint_seed).tolist(),
    }


def activation_delta_metrics(
    baseline: np.ndarray,
    intervened: np.ndarray,
    intended_delta: np.ndarray,
    eps: float = 1e-12,
) -> dict[str, float]:
    base = np.asarray(baseline, dtype=np.float64)
    changed = np.asarray(intervened, dtype=np.float64)
    intended = np.asarray(intended_delta, dtype=np.float64)
    actual = changed - base
    base_rms = float(np.sqrt(np.mean(base**2)))
    actual_rms = float(np.sqrt(np.mean(actual**2)))
    intended_rms = float(np.sqrt(np.mean(intended**2)))
    return {
        "actual_activation_delta_rms": actual_rms,
        "actual_to_baseline_rms": actual_rms / max(base_rms, eps),
        "intended_activation_delta_rms": intended_rms,
        "actual_to_intended_rms": actual_rms / max(intended_rms, eps),
        "actual_intended_cosine": cosine(actual, intended, eps),
        "post_activation_cosine": cosine(base, changed, eps),
    }


def logprob_dict_metrics(
    baseline: dict[str, float], intervened: dict[str, float], eps: float = 1e-12
) -> dict[str, float | bool]:
    if not baseline or not intervened:
        return {"available": False}
    vocabulary = sorted(set(baseline) | set(intervened))
    p_raw = np.array([np.exp(baseline.get(token, -100.0)) for token in vocabulary])
    q_raw = np.array([np.exp(intervened.get(token, -100.0)) for token in vocabulary])
    p = p_raw / max(p_raw.sum(), eps)
    q = q_raw / max(q_raw.sum(), eps)
    return {
        "available": True,
        "truncated_support_size": len(vocabulary),
        "truncated_total_variation": 0.5 * float(np.abs(p - q).sum()),
        "truncated_js": distribution_metrics(
            np.log(np.maximum(p, eps)),
            np.log(np.maximum(q, eps)),
            top_k=min(20, len(vocabulary)),
            rbo_p=0.9,
            fingerprint_dim=min(32, max(len(vocabulary), 1)),
            fingerprint_seed=17,
            save_top_deltas=min(10, len(vocabulary)),
        )["js_divergence"],
    }
