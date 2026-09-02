#!/usr/bin/env python3
"""Independently check the compact T21 descriptive decomposition (NumPy only)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(decomposition: dict, original: dict) -> dict:
    check(
        decomposition["status"] == "posthoc_descriptive_decomposition",
        "Diagnostic status changed",
    )
    check(
        decomposition["new_significance_tests"]
        == decomposition["new_model_forwards"]
        == 0,
        "Scope changed",
    )
    check(
        decomposition["target_items"] == original["target_items"] == 195,
        "Population differs",
    )
    for key in (
        "anchor",
        "context_indices",
        "donors_averaged_per_item",
        "contrast_order",
    ):
        check(decomposition[key] == original[key], "Aggregation differs")
    for payload in (decomposition, original):
        check(
            [r["item_index"] for r in payload["rows"]] == list(range(195)),
            "Duplicate or missing item",
        )
    components = {
        key: np.asarray([r[key] for r in decomposition["rows"]], dtype=float)
        for key in ("own_keyword", "maximum_competitor", "donor_keyword")
    }
    check(
        all(x.shape == (195, 5) and np.isfinite(x).all() for x in components.values()),
        "Invalid component",
    )
    margin = np.asarray(
        [r["alias_margin_contrasts"] for r in original["rows"]], dtype=float
    )
    check(
        margin.shape == (195, 5) and np.isfinite(margin).all(),
        "Invalid original margin",
    )
    errors = [
        float(
            np.max(
                np.abs(
                    components["own_keyword"]
                    - components["maximum_competitor"]
                    - margin
                )
            )
        )
    ]
    for j, name in enumerate(original["contrast_order"]):
        for key, values in {**components, "margin": margin}.items():
            # Explicit Python sum provides a separate aggregation path.
            mean = sum(float(row[j]) for row in values) / 195
            errors.append(abs(mean - decomposition["means"][name][key]))
    check(max(errors) < 1e-10, "Decomposition reconstruction differs")
    return {
        "status": "pass",
        "items_checked": 195,
        "contrasts_checked": 5,
        "maximum_numeric_error": max(errors),
        "boundary": "Checks compact scalar identities and means; raw-state provenance is a separate receipt.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decomposition", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    value = json.loads(args.decomposition.read_text())
    original_hash = hashlib.sha256(args.original.read_bytes()).hexdigest()
    check(
        value["original_compact_sha256"] == original_hash,
        "Original scalar binding differs",
    )
    result = verify(value, json.loads(args.original.read_text()))
    result.update(
        decomposition_sha256=hashlib.sha256(
            args.decomposition.read_bytes()
        ).hexdigest(),
        original_compact_sha256=original_hash,
        validator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
