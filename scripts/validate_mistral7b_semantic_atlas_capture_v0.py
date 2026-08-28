#!/usr/bin/env python3
"""Prospective batch-1 recapture validation for the semantic atlas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


VALIDATION_CONFIG_PATH = Path(
    "configs/mistral7b_semantic_atlas_capture_validation_v0.yaml"
)


def validate_capture(model_path: Path, run_root: Path, output: Path) -> dict[str, Any]:
    root = atlas._root()
    freeze = atlas.audit_freeze()
    config = atlas._read_yaml(root / atlas.CONFIG_PATH)
    spec = atlas._read_yaml(root / VALIDATION_CONFIG_PATH)
    selection = atlas._read_json(root / atlas.SELECTION_PATH)
    final_receipt = atlas._read_json(run_root / "run_receipt.json")
    atlas._require(final_receipt.get("status") == "pass", "Atlas run is not finalized")
    atlas._require(
        final_receipt.get("freeze_manifest_sha256") == freeze["manifest_sha256"],
        "Atlas run freeze mismatch",
    )
    atlas._require(spec["source_protocol_id"] == atlas.PROTOCOL_ID, "Validation source mismatch")
    atlas._require(spec["view_order"] == list(atlas.VIEW_ORDER), "Validation view order mismatch")
    atlas._require(spec["carrier_order"] == config["input"]["carrier_order"], "Carrier order mismatch")
    atlas._require(spec["distance_order"] == config["input"]["distance_order"], "Distance order mismatch")
    atlas._require(spec["layers"] == config["layers"]["expected_resolved_layers"], "Layer order mismatch")
    foreign = atlas._foreign_gpu_pids()
    if foreign:
        raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before recapture: {foreign}")
    torch, tokenizer, model, model_receipt = atlas._load_model(model_path, config)
    acquired = atlas._selection_rows(selection, acquired_only=True)
    layers = [int(value) for value in spec["layers"]]
    distances = [int(value) for value in spec["distance_order"]]
    thresholds = spec["thresholds"]
    rows: list[dict[str, Any]] = []
    try:
        for acquisition_index in spec["fixed_acquisition_indices"]:
            item = acquired[int(acquisition_index)]
            atlas._require(item["role"] != "reserved_unrun", "Validation selected reserve")
            shard_index = int(acquisition_index) // int(config["storage"]["item_shard_size"])
            item_offset = int(acquisition_index) % int(config["storage"]["item_shard_size"])
            stored = np.load(
                run_root / f"shard_{shard_index:04d}" / "activations.npy",
                mmap_mode="r",
                allow_pickle=False,
            )
            for view_index, view in enumerate(atlas.VIEW_ORDER):
                raw_ids = atlas._stored_view_ids(item, view)
                for carrier_index, carrier in enumerate(spec["carrier_order"]):
                    carrier_spec = config["input"]["carriers"][carrier]
                    input_ids = raw_ids + [int(carrier_spec["expected_token_id"])] * int(
                        carrier_spec["repeats"]
                    )
                    tensor = torch.tensor([input_ids], dtype=torch.long, device="cuda")
                    mask = torch.ones_like(tensor)
                    with torch.inference_mode():
                        result = model(
                            input_ids=tensor,
                            attention_mask=mask,
                            use_cache=False,
                            output_hidden_states=True,
                            return_dict=True,
                        )
                    selected = torch.stack(
                        [result.hidden_states[layer + 1][0] for layer in layers], dim=1
                    )
                    positions = torch.tensor(
                        [len(raw_ids) + distance - 1 for distance in distances],
                        dtype=torch.long,
                        device="cuda",
                    )
                    observed = selected[positions].float().cpu().numpy()
                    expected = np.asarray(
                        stored[item_offset, view_index, carrier_index], dtype=np.float32
                    )
                    delta = observed.astype(np.float64) - expected.astype(np.float64)
                    maximum_absolute_error = float(np.max(np.abs(delta)))
                    rms_delta = np.sqrt(np.mean(np.square(delta), axis=-1))
                    rms_expected = np.sqrt(
                        np.mean(np.square(expected, dtype=np.float64), axis=-1)
                    )
                    relative_rms = rms_delta / np.maximum(rms_expected, 1e-12)
                    dot = np.sum(
                        observed.astype(np.float64) * expected.astype(np.float64), axis=-1
                    )
                    norms = np.linalg.norm(observed.astype(np.float64), axis=-1) * np.linalg.norm(
                        expected.astype(np.float64), axis=-1
                    )
                    cosines = dot / np.maximum(norms, 1e-30)
                    minimum_cosine = float(np.min(cosines))
                    maximum_relative_rms = float(np.max(relative_rms))
                    passed = bool(
                        minimum_cosine >= float(thresholds["minimum_vector_cosine"])
                        and maximum_relative_rms
                        <= float(thresholds["maximum_relative_rms_error"])
                        and maximum_absolute_error <= float(thresholds["maximum_absolute_error"])
                    )
                    rows.append(
                        {
                            "acquisition_index": int(acquisition_index),
                            "codepoint": str(item["codepoint"]),
                            "role": str(item["role"]),
                            "view": view,
                            "carrier": carrier,
                            "minimum_vector_cosine": minimum_cosine,
                            "maximum_relative_rms_error": maximum_relative_rms,
                            "maximum_absolute_error": maximum_absolute_error,
                            "exact_element_fraction": float(np.mean(observed == expected)),
                            "pass": passed,
                        }
                    )
                    del result, selected, positions, observed, tensor, mask
    finally:
        del model
        torch.cuda.empty_cache()
    atlas._require(len(rows) == int(spec["expected_cases"]), "Validation case count mismatch")
    payload = {
        "schema_version": 1,
        "protocol_id": spec["protocol_id"],
        "source_protocol_id": atlas.PROTOCOL_ID,
        "status": "pass" if all(row["pass"] for row in rows) else "validation_failed",
        "claim_boundary": spec["claim_boundary"],
        "thresholds": thresholds,
        "fixed_acquisition_indices": spec["fixed_acquisition_indices"],
        "case_count": len(rows),
        "passed_case_count": sum(bool(row["pass"]) for row in rows),
        "minimum_vector_cosine": min(row["minimum_vector_cosine"] for row in rows),
        "maximum_relative_rms_error": max(row["maximum_relative_rms_error"] for row in rows),
        "maximum_absolute_error": max(row["maximum_absolute_error"] for row in rows),
        "minimum_exact_element_fraction": min(row["exact_element_fraction"] for row in rows),
        "model_forward_calls": len(rows),
        "reserve_forward_calls": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "model": model_receipt,
        "freeze_manifest_sha256": freeze["manifest_sha256"],
        "source_run_receipt_sha256": atlas._sha256(run_root / "run_receipt.json"),
        "cases": rows,
    }
    atlas._write_json(output, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            validate_capture(args.model, args.run, args.output),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
