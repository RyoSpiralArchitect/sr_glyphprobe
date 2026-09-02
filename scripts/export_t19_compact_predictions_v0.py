#!/usr/bin/env python3
"""Export checksum-bound T19 prediction indices without opening model states."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

import validate_t19_compact_predictions_v0 as replay


def export(root: Path, summary_root: Path, output: Path) -> dict:
    replay.check(not output.exists(), "Output exists")
    independent = replay.read(root / replay.PREFIX / "independent_validation.json")
    replay.check(
        independent["status"] == "independent_validation_pass",
        "Prior validation missing",
    )
    specification = replay.read(
        root / "data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json"
    )
    for name in ["configs/t19_lexical_alias_unicode_control_v0.yaml"] + [
        f"{replay.PREFIX}/tokenizers/{role}.json" for role in replay.ROLES
    ]:
        replay.check(
            replay.digest(root / name) == specification["frozen_assets"][name],
            "Original specification binding differs",
        )
    models = []
    for role in replay.ROLES:
        directory = summary_root / role
        receipt_path = directory / "summary_receipt.json"
        replay.check(
            replay.digest(receipt_path) == independent["summary_receipt_sha256"][role],
            "Summary differs from published validation",
        )
        receipt = replay.read(receipt_path)
        replay.check(
            receipt["model_role"] == role and receipt["protocol_id"] == replay.PROTOCOL,
            "Summary identity differs",
        )
        for name, expected in receipt["outputs"].items():
            replay.check(
                Path(name).name == name and replay.digest(directory / name) == expected,
                "Summary payload changed",
            )
        token = replay.read(root / replay.PREFIX / "tokenizers" / f"{role}.json")[
            "tokenizer"
        ]["primary_exact_strata"]
        cells = {}
        with np.load(
            directory / "primary_predictions.npz", allow_pickle=False
        ) as values:
            replay.check(
                set(values.files) == set(receipt["prediction_shapes"]),
                "Prediction keys changed",
            )
            for ki, kind in enumerate(replay.KINDS):
                cells[kind] = {}
                for ci, component in enumerate(replay.COMPONENTS):
                    indices = (
                        list(range(55 * ki, 55 * (ki + 1)))
                        if ci == 0
                        else token["eligible_global_indices_by_kind"][kind]
                    )
                    strata = (
                        [list(range(55))]
                        if ci == 0
                        else token["eligible_local_strata_by_kind"][kind]
                    )
                    arrays = {
                        target: values[f"{component}__{kind}__{target}"]
                        for target in replay.TARGETS
                    }
                    arrays = replay.validate_predictions(arrays, len(indices))
                    replay.validate_strata(strata, len(indices))
                    for target, array in arrays.items():
                        replay.check(
                            list(array.shape)
                            == receipt["prediction_shapes"][
                                f"{component}__{kind}__{target}"
                            ],
                            "Receipt shape differs",
                        )
                    cells[kind][component] = {
                        "global_item_indices": indices,
                        "strata": strata,
                        "predictions": {
                            target: array.tolist() for target, array in arrays.items()
                        },
                    }
        models.append(
            {
                "model_role": role,
                "source_summary_receipt_json": receipt_path.read_text(),
                "source_predictions_sha256": receipt["outputs"][
                    "primary_predictions.npz"
                ],
                "cells": cells,
            }
        )
    value = {
        "schema_version": 1,
        "protocol_id": replay.PROTOCOL,
        "status": "exported_from_independently_validated_predictions",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "role_order": replay.ROLES,
        "core_roles": replay.CORE,
        "context_order": replay.CONTEXTS,
        "models": models,
        "input_sha256": {name: replay.digest(root / name) for name in replay.BINDINGS},
        "exporter_sha256": replay.digest(Path(__file__)),
        "boundary": "Fixed scalar prediction indices and strata, not raw activations or model assets.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
        handle.write("\n")
    return {
        "status": "pass",
        "models_exported": len(models),
        "compact_sha256": replay.digest(output),
        "bytes": output.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-root", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            export(args.root, args.summary_root, args.output), indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
