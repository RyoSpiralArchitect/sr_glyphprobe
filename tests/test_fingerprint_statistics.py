from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np

from glyphprobe.experiment.internal import InternalExperiment


def _row(condition: str, target: str, vector: list[float], group: str = "g") -> dict:
    return {
        "condition_id": condition,
        "target_id": target,
        "target_group": group,
        "distribution": {"fingerprint": vector},
    }


def test_label_specific_fingerprint_has_low_permutation_p() -> None:
    # Build a small object without loading a backend; this method only needs metric config.
    experiment = object.__new__(InternalExperiment)
    experiment.cfg = SimpleNamespace(
        metrics=SimpleNamespace(split_half_repeats=40),
    )
    by_condition: dict[str, list[dict]] = {"a": [], "b": [], "c": []}
    bases = {
        "a": np.array([1.0, 0.0, 0.0]),
        "b": np.array([0.0, 1.0, 0.0]),
        "c": np.array([0.0, 0.0, 1.0]),
    }
    for condition, base in bases.items():
        for index in range(12):
            noise = np.array([0.0, 0.0, (index - 5.5) * 1e-4])
            by_condition[condition].append(
                _row(condition, f"t{index:02d}", (base + noise).tolist(), f"g{index % 3}")
            )
    stats = experiment._condition_fingerprint_statistics(
        by_condition,
        split_seed=13,
        permutation_count=199,
    )
    assert stats["available"] is True
    assert stats["separation"] > 0.9
    assert stats["repeat_ci_low"] > 0.8
    assert stats["permutation_p_greater_equal"] <= 0.02
