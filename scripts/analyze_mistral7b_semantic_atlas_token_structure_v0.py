#!/usr/bin/env python3
"""Post-outcome token-structure sensitivity for the batch-one semantic atlas."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_mistral7b_semantic_atlas_batch1_v1 as canonical  # noqa: E402
import analyze_mistral7b_semantic_atlas_v0 as metrics  # noqa: E402


EXPECTED_PREFIX3 = (29473, 1011, 930)
EXPECTED_STRATUM_COUNTS = {
    "glyph5_common_prefix3_all": 760,
    "glyph5_name_tokens_1": 105,
    "glyph5_name_tokens_2": 257,
    "glyph5_name_tokens_3": 213,
    "glyph5_name_tokens_4": 111,
    "glyph5_name_tokens_5_equal_view_length": 43,
    "glyph5_codepoint_tokens_6": 180,
    "glyph5_codepoint_tokens_7": 573,
}


def _strata(acquired: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    base = [
        index
        for index, item in enumerate(acquired)
        if item["role"] == "discovery_unseen"
        and int(item["token_count"]) == 5
        and tuple(int(value) for value in item["token_ids"][:3]) == EXPECTED_PREFIX3
    ]
    values: dict[str, list[int]] = {"glyph5_common_prefix3_all": base}
    for token_count in range(1, 6):
        suffix = (
            "5_equal_view_length" if token_count == 5 else str(token_count)
        )
        values[f"glyph5_name_tokens_{suffix}"] = [
            index for index in base if int(acquired[index]["name_token_count"]) == token_count
        ]
    for token_count in (6, 7):
        values[f"glyph5_codepoint_tokens_{token_count}"] = [
            index
            for index in base
            if int(acquired[index]["codepoint_token_count"]) == token_count
        ]
    observed = {name: len(indices) for name, indices in values.items()}
    canonical.batch1.v0._require(
        observed == EXPECTED_STRATUM_COUNTS,
        f"Token stratum counts changed: {observed}",
    )
    return {name: np.asarray(indices, dtype=np.int64) for name, indices in values.items()}


def analyze(run_root: Path, output: Path, *, knn_k: int = 10) -> dict[str, Any]:
    import torch

    root = canonical.batch1.v0._root()
    validation = canonical.batch1.v0._read_json(root / canonical.VALIDATION_PATH)
    canonical.batch1.v0._require(
        canonical.batch1.v0._sha256(root / canonical.VALIDATION_PATH)
        == canonical.EXPECTED_VALIDATION_SHA256,
        "Canonical validation binding mismatch",
    )
    canonical.batch1.v0._require(validation.get("status") == "pass", "Canonical capture failed")
    with canonical.batch1._delegated_surface():
        atlas = canonical.batch1.v0
        atlas.audit_freeze()
        config = atlas._read_yaml(root / atlas.CONFIG_PATH)
        selection = atlas._read_json(root / atlas.SELECTION_PATH)
        source_receipt = atlas._read_json(run_root / "run_receipt.json")
        atlas._require(source_receipt.get("status") == "pass", "Source run is not finalized")
        atlas._require(source_receipt.get("reserved_unrun_model_inputs_forwarded") == 0, "Reserve boundary failed")
        for index in range(int(config["storage"]["expected_shards"])):
            atlas.validate_shard(run_root / f"shard_{index:04d}", config=config)
        foreign = atlas._foreign_gpu_pids()
        if foreign:
            raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before sensitivity: {foreign}")
        acquired = atlas._selection_rows(selection, acquired_only=True)
        strata = _strata(acquired)
        arrays = [
            np.load(
                run_root / f"shard_{index:04d}" / "activations.npy",
                mmap_mode="r",
                allow_pickle=False,
            )
            for index in range(int(config["storage"]["expected_shards"]))
        ]
        carriers = [str(value) for value in config["input"]["carrier_order"]]
        distances = [int(value) for value in config["input"]["distance_order"]]
        layers = [int(value) for value in config["layers"]["expected_resolved_layers"]]
        torch.set_float32_matmul_precision("highest")
        rows: list[dict[str, Any]] = []
        aggregates: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
        for carrier_index, carrier in enumerate(carriers):
            for distance_index, distance in enumerate(distances):
                for layer_index, layer in enumerate(layers):
                    if atlas._foreign_gpu_pids():
                        raise atlas.ContentionDetected(
                            "Foreign GPU compute PID appeared during sensitivity"
                        )
                    all_values = np.concatenate(
                        [
                            np.asarray(
                                array[
                                    :,
                                    :,
                                    carrier_index,
                                    distance_index,
                                    layer_index,
                                    :,
                                ]
                            )
                            for array in arrays
                        ],
                        axis=0,
                    )
                    for stratum, indices in strata.items():
                        items = [acquired[int(index)] for index in indices]
                        values = np.transpose(all_values[indices], (1, 0, 2))
                        group_ids = metrics._label_ids(
                            [str(item["group"]) for item in items]
                        )
                        subgroup_ids = metrics._label_ids(
                            [str(item["subgroup"]) for item in items]
                        )
                        cell, _ = metrics._cell_metrics(
                            torch,
                            values,
                            group_ids,
                            subgroup_ids,
                            k=min(knn_k, len(indices) - 1),
                        )
                        row = {
                            "stratum": stratum,
                            "item_count": len(indices),
                            "carrier": carrier,
                            "distance": distance,
                            "layer": layer,
                            **cell,
                        }
                        rows.append(row)
                        aggregates[(stratum, layer)].append(row)
                    del all_values
        layer_rows: list[dict[str, Any]] = []
        for stratum in EXPECTED_STRATUM_COUNTS:
            for layer in layers:
                selected = aggregates[(stratum, layer)]
                layer_rows.append(
                    {
                        "stratum": stratum,
                        "item_count": EXPECTED_STRATUM_COUNTS[stratum],
                        "layer": layer,
                        "equal_weight_cell_count": len(selected),
                        "chance_top1": 1.0 / EXPECTED_STRATUM_COUNTS[stratum],
                        "glyph_name_top1": float(
                            np.mean(
                                [
                                    row["pairs"]["glyph_name"][
                                        "top1_accuracy_forward"
                                    ]
                                    for row in selected
                                ]
                            )
                        ),
                        "glyph_codepoint_top1": float(
                            np.mean(
                                [
                                    row["pairs"]["glyph_codepoint"][
                                        "top1_accuracy_forward"
                                    ]
                                    for row in selected
                                ]
                            )
                        ),
                        "glyph_name_cka": float(
                            np.mean(
                                [
                                    row["pairs"]["glyph_name"][
                                        "centered_linear_cka"
                                    ]
                                    for row in selected
                                ]
                            )
                        ),
                        "glyph_codepoint_cka": float(
                            np.mean(
                                [
                                    row["pairs"]["glyph_codepoint"][
                                        "centered_linear_cka"
                                    ]
                                    for row in selected
                                ]
                            )
                        ),
                    }
                )
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    canonical.batch1.v0._require(not output.exists(), "Sensitivity output exists")
    stage.mkdir(parents=True)
    try:
        canonical.batch1.v0._write_jsonl(stage / "cell_metrics.jsonl", rows)
        canonical.batch1.v0._write_json(
            stage / "layer_summary.json", {"schema_version": 1, "rows": layer_rows}
        )
        receipt = {
            "schema_version": 1,
            "protocol_id": canonical.batch1.PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "post_outcome_token_structure_sensitivity_no_decision",
            "outcome_known_before_exact_sensitivity_design": True,
            "stratum_counts": EXPECTED_STRATUM_COUNTS,
            "common_glyph_token_count": 5,
            "common_glyph_prefix3": list(EXPECTED_PREFIX3),
            "minimum_prespecified_stratum_size": 20,
            "cell_row_count": len(rows),
            "layer_summary_row_count": len(layer_rows),
            "source_run_receipt_sha256": canonical.batch1.v0._sha256(
                run_root / "run_receipt.json"
            ),
            "capture_validation_sha256": canonical.EXPECTED_VALIDATION_SHA256,
            "reserved_unrun_model_inputs_forwarded": 0,
            "model_forward_calls": 0,
            "intervention_calls": 0,
            "generation_calls": 0,
            "scientific_decision_authorized": False,
            "confirmatory_status": False,
            "phase_i_gate_closed": False,
        }
        canonical.batch1.v0._write_json(stage / "analysis_receipt.json", receipt)
        canonical.batch1.v0._write_ledger(
            stage,
            ("cell_metrics.jsonl", "layer_summary.json", "analysis_receipt.json"),
        )
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--knn-k", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(analyze(args.run, args.output, knn_k=args.knn_k), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
