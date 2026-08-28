#!/usr/bin/env python3
"""Post-acquisition descriptive cross-view analysis for semantic atlas v0."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import mistral7b_semantic_atlas_v0 as atlas  # noqa: E402


PAIR_ORDER = (
    ("glyph_name", 0, 1),
    ("glyph_codepoint", 0, 2),
    ("name_codepoint", 1, 2),
)
POPULATION_ORDER = ("calibration_prior_exposed", "discovery_unseen")


def _label_ids(values: Sequence[str]) -> np.ndarray:
    mapping = {value: index for index, value in enumerate(sorted(set(values)))}
    return np.asarray([mapping[value] for value in values], dtype=np.int64)


def _pair_metrics(
    torch: Any,
    centered: Any,
    normalized: Any,
    centered_grams: Sequence[Any],
    left: int,
    right: int,
) -> tuple[dict[str, float], Any]:
    similarity = normalized[left] @ normalized[right].T
    diagonal = torch.diagonal(similarity)
    count = int(similarity.shape[0])
    order = torch.arange(count, device=similarity.device)
    ranks_forward = 1 + (similarity > diagonal[:, None]).sum(dim=1)
    ranks_reverse = 1 + (similarity > diagonal[None, :]).sum(dim=0)
    off_diagonal = (similarity.sum() - diagonal.sum()) / max(1, count * (count - 1))
    left_gram = centered_grams[left]
    right_gram = centered_grams[right]
    cka_denominator = torch.sqrt(torch.sum(left_gram.square()) * torch.sum(right_gram.square()))
    cka = torch.sum(left_gram * right_gram) / torch.clamp(cka_denominator, min=1e-30)
    metrics = {
        "paired_cosine_mean": float(diagonal.mean().item()),
        "off_diagonal_cosine_mean": float(off_diagonal.item()),
        "paired_minus_off_diagonal_margin": float((diagonal.mean() - off_diagonal).item()),
        "top1_accuracy_forward": float((similarity.argmax(dim=1) == order).float().mean().item()),
        "top1_accuracy_reverse": float((similarity.argmax(dim=0) == order).float().mean().item()),
        "mean_reciprocal_rank_forward": float((1.0 / ranks_forward.float()).mean().item()),
        "mean_reciprocal_rank_reverse": float((1.0 / ranks_reverse.float()).mean().item()),
        "centered_linear_cka": float(cka.item()),
    }
    return metrics, diagonal.detach().cpu()


def _view_metrics(
    torch: Any,
    similarity: Any,
    labels: Any,
    subgroup_labels: Any,
    k: int,
) -> dict[str, float]:
    similarity = similarity.clone()
    similarity.fill_diagonal_(-float("inf"))
    neighbors = torch.topk(similarity, k=k, dim=1, largest=True, sorted=False).indices
    group_purity = (labels[neighbors] == labels[:, None]).float().mean()
    subgroup_purity = (subgroup_labels[neighbors] == subgroup_labels[:, None]).float().mean()
    count = int(labels.shape[0])
    group_counts = torch.bincount(labels)
    subgroup_counts = torch.bincount(subgroup_labels)
    group_chance = (group_counts[labels] - 1).float().mean() / max(1, count - 1)
    subgroup_chance = (subgroup_counts[subgroup_labels] - 1).float().mean() / max(
        1, count - 1
    )
    return {
        "knn_k": k,
        "group_neighbor_purity": float(group_purity.item()),
        "group_random_pair_baseline": float(group_chance.item()),
        "subgroup_neighbor_purity": float(subgroup_purity.item()),
        "subgroup_random_pair_baseline": float(subgroup_chance.item()),
    }


def _cell_metrics(
    torch: Any,
    values: np.ndarray,
    group_ids: np.ndarray,
    subgroup_ids: np.ndarray,
    *,
    k: int,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    tensor = torch.from_numpy(np.asarray(values, dtype=np.float32)).to("cuda")
    centered = tensor - tensor.mean(dim=1, keepdim=True)
    normalized = torch.nn.functional.normalize(centered, p=2, dim=-1, eps=1e-12)
    centered_grams = [centered[index] @ centered[index].T for index in range(3)]
    normalized_grams = [normalized[index] @ normalized[index].T for index in range(3)]
    groups = torch.from_numpy(group_ids).to("cuda")
    subgroups = torch.from_numpy(subgroup_ids).to("cuda")
    pair_results: dict[str, Any] = {}
    diagonals: dict[str, np.ndarray] = {}
    for name, left, right in PAIR_ORDER:
        metrics, diagonal = _pair_metrics(
            torch, centered, normalized, centered_grams, left, right
        )
        pair_results[name] = metrics
        diagonals[name] = diagonal.numpy()
    view_results = {
        view: _view_metrics(
            torch, normalized_grams[index], groups, subgroups, k
        )
        for index, view in enumerate(atlas.VIEW_ORDER)
    }
    rms = torch.sqrt(torch.mean(tensor.square(), dim=-1)).mean(dim=1)
    result = {
        "pairs": pair_results,
        "views": view_results,
        "mean_activation_rms_by_view": {
            view: float(rms[index].item()) for index, view in enumerate(atlas.VIEW_ORDER)
        },
        "glyph_name_minus_glyph_codepoint": {
            key: float(pair_results["glyph_name"][key] - pair_results["glyph_codepoint"][key])
            for key in (
                "paired_cosine_mean",
                "paired_minus_off_diagonal_margin",
                "top1_accuracy_forward",
                "top1_accuracy_reverse",
                "mean_reciprocal_rank_forward",
                "mean_reciprocal_rank_reverse",
                "centered_linear_cka",
            )
        },
    }
    del tensor, centered, normalized, groups, subgroups
    return result, diagonals


def analyze(run_root: Path, output: Path, *, knn_k: int = 10) -> dict[str, Any]:
    import torch

    atlas.audit_freeze()
    config = atlas._read_yaml(atlas._root() / atlas.CONFIG_PATH)
    selection = atlas._read_json(atlas._root() / atlas.SELECTION_PATH)
    source_receipt = atlas._read_json(run_root / "run_receipt.json")
    atlas._require(source_receipt.get("status") == "pass", "Source run not finalized")
    atlas._require(source_receipt.get("reserved_unrun_model_inputs_forwarded") == 0, "Reserve boundary failed")
    for index in range(int(config["storage"]["expected_shards"])):
        atlas.validate_shard(run_root / f"shard_{index:04d}", config=config)
    foreign = atlas._foreign_gpu_pids()
    if foreign:
        raise atlas.ContentionDetected(f"Foreign GPU compute PIDs before analysis: {foreign}")
    torch.set_float32_matmul_precision("highest")
    acquired = atlas._selection_rows(selection, acquired_only=True)
    arrays = [
        np.load(run_root / f"shard_{index:04d}" / "activations.npy", mmap_mode="r", allow_pickle=False)
        for index in range(int(config["storage"]["expected_shards"]))
    ]
    population_indices = {
        role: np.asarray(
            [index for index, item in enumerate(acquired) if item["role"] == role],
            dtype=np.int64,
        )
        for role in POPULATION_ORDER
    }
    population_metadata: dict[str, dict[str, Any]] = {}
    for role, indices in population_indices.items():
        items = [acquired[int(index)] for index in indices]
        population_metadata[role] = {
            "indices": indices,
            "items": items,
            "group_ids": _label_ids([str(item["group"]) for item in items]),
            "subgroup_ids": _label_ids([str(item["subgroup"]) for item in items]),
        }
    cell_rows: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []
    aggregate: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    carriers = [str(value) for value in config["input"]["carrier_order"]]
    distances = [int(value) for value in config["input"]["distance_order"]]
    layers = [int(value) for value in config["layers"]["expected_resolved_layers"]]
    for carrier_index, carrier in enumerate(carriers):
        for distance_index, distance in enumerate(distances):
            for layer_index, layer in enumerate(layers):
                if atlas._foreign_gpu_pids():
                    raise atlas.ContentionDetected("Foreign GPU compute PID appeared during analysis")
                all_values = np.concatenate(
                    [np.asarray(array[:, :, carrier_index, distance_index, layer_index, :]) for array in arrays],
                    axis=0,
                )
                for population in POPULATION_ORDER:
                    metadata = population_metadata[population]
                    indices = metadata["indices"]
                    values = np.transpose(all_values[indices], (1, 0, 2))
                    metrics, diagonals = _cell_metrics(
                        torch,
                        values,
                        metadata["group_ids"],
                        metadata["subgroup_ids"],
                        k=min(knn_k, len(indices) - 1),
                    )
                    row = {
                        "population": population,
                        "item_count": len(indices),
                        "carrier": carrier,
                        "carrier_index": carrier_index,
                        "distance": distance,
                        "distance_index": distance_index,
                        "layer": layer,
                        "layer_index": layer_index,
                        **metrics,
                    }
                    cell_rows.append(row)
                    aggregate[(population, layer)].append(row)
                    for local_index, item in enumerate(metadata["items"]):
                        item_rows.append(
                            {
                                "population": population,
                                "acquisition_index": int(item["acquisition_index"]),
                                "codepoint": str(item["codepoint"]),
                                "glyph": str(item["glyph"]),
                                "name": str(item["name"]),
                                "group": str(item["group"]),
                                "subgroup": str(item["subgroup"]),
                                "glyph_token_count": int(item["token_count"]),
                                "name_token_count": int(item["name_token_count"]),
                                "codepoint_token_count": int(item["codepoint_token_count"]),
                                "carrier": carrier,
                                "distance": distance,
                                "layer": layer,
                                "glyph_name_paired_cosine": float(diagonals["glyph_name"][local_index]),
                                "glyph_codepoint_paired_cosine": float(diagonals["glyph_codepoint"][local_index]),
                                "name_codepoint_paired_cosine": float(diagonals["name_codepoint"][local_index]),
                            }
                        )
                del all_values
    layer_rows: list[dict[str, Any]] = []
    for population in POPULATION_ORDER:
        for layer in layers:
            rows = aggregate[(population, layer)]
            layer_rows.append(
                {
                    "population": population,
                    "layer": layer,
                    "equal_weight_cell_count": len(rows),
                    "glyph_name_paired_retrieval_top1": float(
                        np.mean([row["pairs"]["glyph_name"]["top1_accuracy_forward"] for row in rows])
                    ),
                    "glyph_codepoint_paired_retrieval_top1": float(
                        np.mean([row["pairs"]["glyph_codepoint"]["top1_accuracy_forward"] for row in rows])
                    ),
                    "glyph_name_minus_codepoint_top1": float(
                        np.mean([row["glyph_name_minus_glyph_codepoint"]["top1_accuracy_forward"] for row in rows])
                    ),
                    "glyph_name_centered_linear_cka": float(
                        np.mean([row["pairs"]["glyph_name"]["centered_linear_cka"] for row in rows])
                    ),
                    "glyph_codepoint_centered_linear_cka": float(
                        np.mean([row["pairs"]["glyph_codepoint"]["centered_linear_cka"] for row in rows])
                    ),
                    "glyph_name_minus_codepoint_cka": float(
                        np.mean([row["glyph_name_minus_glyph_codepoint"]["centered_linear_cka"] for row in rows])
                    ),
                    "glyph_group_neighbor_purity": float(
                        np.mean([row["views"]["glyph"]["group_neighbor_purity"] for row in rows])
                    ),
                    "glyph_subgroup_neighbor_purity": float(
                        np.mean([row["views"]["glyph"]["subgroup_neighbor_purity"] for row in rows])
                    ),
                }
            )
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    atlas._require(not output.exists(), "Analysis output already exists")
    stage.mkdir(parents=True)
    try:
        atlas._write_jsonl(stage / "cell_metrics.jsonl", cell_rows)
        atlas._write_jsonl(stage / "item_pair_cosines.jsonl", item_rows)
        atlas._write_json(stage / "layer_summary.json", {"schema_version": 1, "rows": layer_rows})
        receipt = {
            "schema_version": 1,
            "protocol_id": atlas.PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "post_acquisition_descriptive_no_decision",
            "population_order": list(POPULATION_ORDER),
            "population_counts": {
                role: len(population_indices[role]) for role in POPULATION_ORDER
            },
            "cell_row_count": len(cell_rows),
            "item_row_count": len(item_rows),
            "layer_summary_row_count": len(layer_rows),
            "knn_k": knn_k,
            "view_order": list(atlas.VIEW_ORDER),
            "pair_order": [name for name, _, _ in PAIR_ORDER],
            "centering": "subtract_feature_mean_across_items_separately_per_view_population_cell",
            "cosine_normalization": "row_l2_after_centering",
            "retrieval_tie_rule": "strictly_greater_similarity_determines_rank",
            "layer_summary_weighting": "equal_weight_over_two_carriers_and_four_distances",
            "source_run_receipt_sha256": atlas._sha256(run_root / "run_receipt.json"),
            "reserved_unrun_model_inputs_forwarded": 0,
            "model_forward_calls": 0,
            "intervention_calls": 0,
            "generation_calls": 0,
            "scientific_decision_authorized": False,
            "confirmatory_status": False,
            "phase_i_gate_closed": False,
        }
        atlas._write_json(stage / "analysis_receipt.json", receipt)
        names = (
            "cell_metrics.jsonl",
            "item_pair_cosines.jsonl",
            "layer_summary.json",
            "analysis_receipt.json",
        )
        atlas._write_ledger(stage, names)
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
