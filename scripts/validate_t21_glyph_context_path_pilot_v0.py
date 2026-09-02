#!/usr/bin/env python3
"""Independent CPU reconstruction of T21 pilot metrics and progression."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


CONDITIONS = [
    "intact",
    "reset",
    "intact_glyph_donor",
    "intact_suffix_donor",
    "reset_glyph_donor",
    "reset_suffix_donor",
    "reset_prefix_donor",
    "reset_prefix_restore_glyph",
    "reset_prefix_restore_suffix",
    "reset_roundtrip",
    "no_op",
]
CONTRASTS = [
    ("calibration", 1, 6),
    ("necessity_absolute", 1, 4),
    ("necessity_position_adjusted", 5, 4),
    ("rescue_absolute", 7, 6),
    ("rescue_position_adjusted", 7, 8),
]


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def norm(matrix: np.ndarray) -> np.ndarray:
    matrix = matrix.astype(np.float64)
    return matrix / np.sqrt(np.sum(matrix * matrix, axis=-1, keepdims=True))


def reconstruct_item(
    query: np.ndarray,
    alias: np.ndarray,
    codepoint: np.ndarray,
    source_alias: np.ndarray,
    source_codepoint: np.ndarray,
    donors: list[int],
) -> dict[str, np.ndarray]:
    shape = query.shape[:-1]
    flat = norm(query.reshape(-1, query.shape[-1]))
    alias_scores = flat @ norm(np.vstack([alias[None], source_alias])).T
    codepoint_scores = flat @ norm(np.vstack([codepoint[None], source_codepoint])).T
    own_alias = alias_scores[:, 0].reshape(shape)
    margin_alias = own_alias - alias_scores[:, 1:].max(axis=1).reshape(shape)
    donor_margin = np.empty(shape)
    # Query order is anchor, donor-slot, condition; gallery column zero is own item.
    for anchor in range(shape[0]):
        for slot, donor in enumerate(donors):
            start = (anchor * shape[1] + slot) * shape[2]
            donor_margin[anchor, slot] = (
                own_alias[anchor, slot]
                - alias_scores[start : start + shape[2], donor + 1]
            )
    return {
        "alias_margin": margin_alias,
        "donor_margin": donor_margin,
        "alias_top1": (alias_scores.argmax(axis=1) == 0).reshape(shape).astype(float),
        "codepoint_margin": (
            codepoint_scores[:, 0] - codepoint_scores[:, 1:].max(axis=1)
        ).reshape(shape),
        "codepoint_top1": (codepoint_scores.argmax(axis=1) == 0)
        .reshape(shape)
        .astype(float),
    }


def interval(values: np.ndarray, seed: int) -> tuple[float, float]:
    generator = np.random.default_rng(seed)
    means = np.empty(20000)
    for offset in range(0, 20000, 1000):
        rows = generator.integers(len(values), size=(1000, len(values)))
        means[offset : offset + 1000] = np.sum(values[rows], axis=1) / len(values)
    low, high = np.percentile(means, [2.5, 97.5])
    return float(low), float(high)


def validate(run_root: Path, analysis_root: Path, output: Path) -> dict:
    check(not output.exists(), "Validation output already exists")
    acquisition = read(run_root / "acquisition_receipt.json")
    specification = read(run_root / "specification.json")
    check(
        acquisition["status"] == "pilot_acquisition_complete"
        and acquisition["target_items"] == 384,
        "Incomplete pilot",
    )
    check(
        specification["reserve_access_allowed"] is False
        and acquisition["reserve_model_forwards"] == 0,
        "Reserve boundary changed",
    )
    check(specification["conditions"] == CONDITIONS, "Condition mapping changed")
    check(
        digest(run_root / "specification.json") == acquisition["specification_sha256"],
        "Specification bytes changed",
    )
    check(
        digest(run_root / "source_states.npz") == acquisition["source_states_sha256"],
        "Source states changed",
    )
    analysis = read(analysis_root / "analysis_receipt.json")
    check(
        analysis["acquisition_receipt_sha256"]
        == digest(run_root / "acquisition_receipt.json"),
        "Analysis points to another acquisition",
    )
    for filename, expected in analysis["outputs"].items():
        check(digest(analysis_root / filename) == expected, "Analysis payload changed")
    with np.load(run_root / "source_states.npz", allow_pickle=False) as values:
        source = values["states"]
    with np.load(analysis_root / "item_metrics.npz", allow_pickle=False) as values:
        reported = {name: values[name] for name in values.files}
    rebuilt = {name: np.empty_like(values) for name, values in reported.items()}
    covered = set()
    for name, receipt_hash in sorted(acquisition["chunks"].items()):
        directory = run_root / name
        check(
            digest(directory / "receipt.json") == receipt_hash, "Chunk receipt changed"
        )
        receipt = read(directory / "receipt.json")
        check(
            receipt["specification_sha256"] == acquisition["specification_sha256"],
            "Mixed chunk specification",
        )
        check(
            digest(directory / "states.npz") == receipt["states_sha256"],
            "Chunk state bytes changed",
        )
        with np.load(directory / "states.npz", allow_pickle=False) as values:
            baseline, states, indices = (
                values["baseline"],
                values["intervention"],
                values["item_indices"],
            )
        check(
            np.array_equal(indices, np.arange(receipt["start"], receipt["stop"])),
            "Changed chunk indices",
        )
        check(
            np.array_equal(states[..., 0, :], states[..., 10, :]),
            "No-op state mismatch",
        )
        check(
            np.array_equal(states[..., 1, :], states[..., 9, :]),
            "Roundtrip state mismatch",
        )
        for local, index in enumerate(indices.tolist()):
            check(index not in covered, "Duplicate target")
            covered.add(index)
            for context in range(4):
                result = reconstruct_item(
                    states[local, context],
                    baseline[local, context, 1],
                    baseline[local, context, 2],
                    source[:, context, 1],
                    source[:, context, 2],
                    specification["donor_indices"][index],
                )
                for metric, values in result.items():
                    rebuilt[metric][index, context] = values
    check(covered == set(range(384)), "Incomplete item coverage")
    errors = {
        name: float(np.max(np.abs(rebuilt[name] - reported[name]))) for name in rebuilt
    }
    check(
        all(value < 1e-10 for value in errors.values()),
        "Metric reconstruction mismatch",
    )
    result = read(analysis_root / "pilot_result.json")
    candidate_rows = []
    for anchor_index, site in enumerate(result["sites"]):
        scores = rebuilt["alias_margin"][:, [1, 3], anchor_index].sum(axis=(1, 2)) / 4
        lows = {}
        for contrast_index, (name, positive, negative) in enumerate(CONTRASTS):
            delta = scores[:, positive] - scores[:, negative]
            low, high = interval(
                delta, 2026092100 + 100 * anchor_index + contrast_index
            )
            observed = site["contrasts"][name]
            check(
                abs(observed["mean"] - delta.mean()) < 1e-10, "Contrast mean mismatch"
            )
            check(
                abs(observed["lower_95"] - low) < 1e-10
                and abs(observed["upper_95"] - high) < 1e-10,
                "Interval mismatch",
            )
            lows[name] = low
        passed = all(value > 0 for value in lows.values())
        check(passed == site["pilot_screen_pass"], "Pilot screen mismatch")
        check(
            (lows["calibration"] > 0) == site["calibration_pass"],
            "Calibration decision mismatch",
        )
        if passed:
            candidate_rows.append(
                (
                    min(value for name, value in lows.items() if name != "calibration"),
                    site["anchor"],
                )
            )
    candidate_rows.sort(key=lambda row: (-row[0], row[1]))
    selected = candidate_rows[0][1] if candidate_rows else None
    check(selected == result["candidate_anchor"], "Candidate selection mismatch")
    check(
        result["confirmatory_result"] is False
        and result["reserve_access_allowed"] is False,
        "Exploratory status changed",
    )
    receipt = {
        "status": "pass",
        "validator": Path(__file__).name,
        "validator_sha256": digest(Path(__file__)),
        "analysis_receipt_sha256": digest(analysis_root / "analysis_receipt.json"),
        "acquisition_receipt_sha256": digest(run_root / "acquisition_receipt.json"),
        "target_items_validated": 384,
        "maximum_metric_errors": errors,
        "candidate_anchor": selected,
        "reserve_model_forwards": 0,
        "claim": "independent numerical reconstruction, not a new experimental replication",
    }
    with output.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate(args.run_root, args.analysis_root, args.output),
            indent=2,
            sort_keys=True,
        )
    )
