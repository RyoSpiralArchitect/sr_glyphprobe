#!/usr/bin/env python3
"""Post-hoc, CPU-only decomposition of the completed T21-C margin endpoint."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION = ROOT / "validation/t21_glyph_context_path_confirmation_v0"
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
ORDER = [
    "calibration",
    "necessity_absolute",
    "necessity_position_adjusted",
    "rescue_absolute",
    "rescue_position_adjusted",
]
PAIRS = [(1, 6), (1, 4), (5, 4), (7, 6), (7, 8)]
COMPONENTS = ["own_keyword", "maximum_competitor", "donor_keyword"]
METRICS = [
    "alias_margin",
    "donor_margin",
    "alias_top1",
    "codepoint_margin",
    "codepoint_top1",
]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    scale = np.sqrt(np.sum(x * x, axis=-1, keepdims=True))
    check(np.isfinite(x).all() and bool((scale > 1e-12).all()), "Invalid state")
    return x / scale


def score(
    query: np.ndarray, own: np.ndarray, source: np.ndarray, donors: list[int]
) -> dict:
    """One item/context: anchor x donor slot x condition, with a 129-column gallery."""
    shape = query.shape[:-1]
    check(shape == (2, 2, 11), "Query layout changed")
    flat = normalize(query.reshape(-1, query.shape[-1]))
    result = {}
    for index, name in ((1, "alias"), (2, "codepoint")):
        gallery = normalize(np.vstack([own[index], source[:, index]]))
        similarities = (flat @ gallery.T).reshape(*shape, 129)
        maximum = similarities[..., 1:].max(axis=-1)
        result[name + "_margin"] = similarities[..., 0] - maximum
        result[name + "_top1"] = (similarities.argmax(axis=-1) == 0).astype(float)
        if name == "alias":
            result["own_keyword"] = similarities[..., 0]
            result["maximum_competitor"] = maximum
            donor = np.empty(shape)
            for slot, source_index in enumerate(donors):
                donor[:, slot] = similarities[:, slot, :, source_index + 1]
            result["donor_keyword"] = donor
            result["donor_margin"] = similarities[..., 0] - donor
    return result


def contrast(x: np.ndarray) -> np.ndarray:
    check(x.shape == (195, 4, 2, 2, 11), "Endpoint shape changed")
    values = x[:, [1, 3], 0].mean(axis=(1, 2))
    return np.column_stack([values[:, a] - values[:, b] for a, b in PAIRS])


def run(run_root: Path, analysis_root: Path, output: Path) -> dict:
    check(not output.exists(), "Output exists; choose a new directory")
    acquisition = read(run_root / "acquisition_receipt.json")
    analysis = read(analysis_root / "analysis_receipt.json")
    spec = read(run_root / "specification.json")
    for directory, name, published in (
        (
            run_root,
            "acquisition_receipt.json",
            CONFIRMATION / "results/acquisition_receipt.json",
        ),
        (
            analysis_root,
            "analysis_receipt.json",
            CONFIRMATION / "results/analysis_receipt.json",
        ),
        (
            run_root,
            "specification.json",
            CONFIRMATION / "confirmation_specification.json",
        ),
    ):
        check(
            digest(directory / name) == digest(published),
            "Published input binding differs",
        )
    check(
        acquisition["target_items"] == spec["target_count"] == 195, "Population differs"
    )
    check(
        spec["conditions"] == CONDITIONS and spec["anchors"] == [21, 24],
        "Layout changed",
    )
    check(
        spec["contexts"]
        == [["pipe", 4], ["pipe", 8], ["article_a", 4], ["article_a", 8]],
        "Contexts changed",
    )
    check(
        analysis["acquisition_receipt_sha256"]
        == digest(run_root / "acquisition_receipt.json"),
        "Analysis source differs",
    )
    check(
        acquisition["specification_sha256"]
        == analysis["specification_sha256"]
        == digest(run_root / "specification.json"),
        "Specification differs",
    )
    check(
        digest(run_root / "source_states.npz") == acquisition["source_states_sha256"],
        "Source states changed",
    )
    for name, expected in analysis["outputs"].items():
        check(
            Path(name).name == name and digest(analysis_root / name) == expected,
            "Analysis payload changed",
        )
    with np.load(run_root / "source_states.npz", allow_pickle=False) as values:
        source = values["states"]
    check(source.shape == (128, 4, 3, 3072), "Source layout changed")
    with np.load(analysis_root / "item_metrics.npz", allow_pickle=False) as values:
        reported = {name: values[name] for name in values.files}
    expected_metrics = set(METRICS) | {name + "_effect" for name in METRICS}
    check(set(reported) == expected_metrics, "Saved metric set changed")
    check(
        all(
            x.shape == (195, 4, 2, 2, 11) and np.isfinite(x).all()
            for x in reported.values()
        ),
        "Invalid saved metrics",
    )
    effects = {name: np.empty((195, 4, 2, 2, 11)) for name in COMPONENTS}
    errors = dict.fromkeys(sorted(reported), 0.0)
    covered = set()
    for name, expected_hash in sorted(acquisition["chunks"].items()):
        check(Path(name).name == name, "Unsafe chunk name")
        directory = run_root / name
        check(
            digest(directory / "receipt.json") == expected_hash, "Chunk receipt changed"
        )
        receipt = read(directory / "receipt.json")
        check(
            receipt["specification_sha256"] == acquisition["specification_sha256"],
            "Mixed specification",
        )
        check(
            digest(directory / "states.npz") == receipt["states_sha256"],
            "Chunk states changed",
        )
        with np.load(directory / "states.npz", allow_pickle=False) as values:
            indices, baseline = values["item_indices"], values["baseline"]
            actual, neutral = values["intervention"], values["neutral_reference"]
        check(
            np.array_equal(indices, np.arange(receipt["start"], receipt["stop"])),
            "Chunk indices changed",
        )
        n = len(indices)
        check(baseline.shape == (n, 4, 3, 3072), "Baseline layout changed")
        check(
            actual.shape == neutral.shape == (n, 4, 2, 2, 11, 3072),
            "State layout changed",
        )
        for condition in (0, 1, 9, 10):
            check(
                np.array_equal(actual[..., condition, :], neutral[..., condition, :]),
                "Neutral engineering control differs",
            )
        for local, index in enumerate(indices.tolist()):
            check(
                index not in covered and 0 <= index < 195, "Duplicate or invalid item"
            )
            covered.add(index)
            donors = spec["donor_indices"][index]
            check(
                len(set(donors)) == 2 and all(0 <= d < 128 for d in donors),
                "Invalid donors",
            )
            for context in range(4):
                observed = score(
                    actual[local, context],
                    baseline[local, context],
                    source[:, context],
                    donors,
                )
                reference = score(
                    neutral[local, context],
                    baseline[local, context],
                    source[:, context],
                    donors,
                )
                for component in COMPONENTS:
                    effects[component][index, context] = (
                        observed[component] - reference[component]
                    )
                for metric in METRICS:
                    for key, x in (
                        (metric, observed[metric]),
                        (metric + "_effect", observed[metric] - reference[metric]),
                    ):
                        saved = reported[key][index, context]
                        error = float(np.max(np.abs(x - saved)))
                        errors[key] = max(errors[key], error)
                        check(error < 1e-10, "Raw-state reconstruction differs")
                        if "top1" in key:
                            check(np.array_equal(x, saved), "Top-1 differs")
        print(json.dumps({"chunk": name, "items_checked": len(covered)}), flush=True)
    check(covered == set(range(195)), "Incomplete coverage")
    components = {name: contrast(x) for name, x in effects.items()}
    original = contrast(reported["alias_margin_effect"])
    difference = components["own_keyword"] - components["maximum_competitor"]
    identity_error = float(np.max(np.abs(difference - original)))
    check(identity_error < 1e-10, "Margin identity differs")
    compact = read(CONFIRMATION / "results/item_contrasts.json")
    compact_original = np.asarray(
        [r["alias_margin_contrasts"] for r in compact["rows"]]
    )
    check(
        np.max(np.abs(compact_original - original)) < 1e-10,
        "Published scalar contrasts differ",
    )
    created = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": 1,
        "status": "posthoc_descriptive_decomposition",
        "created_at_utc": created,
        "target_items": 195,
        "anchor": 21,
        "context_indices": [1, 3],
        "donors_averaged_per_item": 2,
        "contrast_order": ORDER,
        "component_order": COMPONENTS,
        "component_units": "cosine",
        "identity": "margin = own_keyword - maximum_competitor",
        "new_model_forwards": 0,
        "new_significance_tests": 0,
        "original_compact_sha256": digest(CONFIRMATION / "results/item_contrasts.json"),
        "rows": [
            {"item_index": i, **{name: x[i].tolist() for name, x in components.items()}}
            for i in range(195)
        ],
        "means": {
            name: {
                component: float(x[:, j].mean()) for component, x in components.items()
            }
            | {"margin": float(original[:, j].mean())}
            for j, name in enumerate(ORDER)
        },
        "boundary": (
            "Descriptive endpoint identity on already evaluated confirmation items; "
            "no new confirmatory test. Maximum competitor identity may vary. "
            "Donor cosine is a diagnostic, not a third additive term."
        ),
    }
    output.mkdir(parents=True)
    write(output / "decomposition.json", payload)
    receipt = {
        "status": "pass",
        "created_at_utc": created,
        "items_checked": 195,
        "chunks_checked": len(acquisition["chunks"]),
        "metric_reconstruction_errors": errors,
        "maximum_margin_identity_error": identity_error,
        "top1_exact": True,
        "acquisition_receipt_sha256": digest(run_root / "acquisition_receipt.json"),
        "analysis_receipt_sha256": digest(analysis_root / "analysis_receipt.json"),
        "source_states_sha256": acquisition["source_states_sha256"],
        "specification_sha256": acquisition["specification_sha256"],
        "source_script_sha256": digest(Path(__file__)),
        "plan_sha256": digest(ROOT / "docs/POST_REVIEW_EVIDENCE_PLAN_V0.md"),
        "decomposition_sha256": digest(output / "decomposition.json"),
        "scientific_decisions_changed": False,
    }
    write(output / "reconstruction_receipt.json", receipt)
    return {
        "status": "pass",
        "means": payload["means"],
        "maximum_margin_identity_error": identity_error,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.run_root, args.analysis_root, args.output),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
