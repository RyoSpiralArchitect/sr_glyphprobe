#!/usr/bin/env python3
"""Recompute bounded T10 diagnostics without changing the frozen T10 result.

The script uses the Git-resident compact bundle for item/cell diagnostics and,
when a raw run directory is supplied, independently reconstructs every stored
retrieval prediction and computes cross-model representational geometry.  The
output is descriptive and retrospective.  It cannot rescue, replace, or
reinterpret T10's registered primary decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr


PROTOCOL_ID = "glyphprobe-semantic-atlas-cross-model-diagnostics-v1"
T10_PROTOCOL_ID = "glyphprobe-semantic-atlas-cross-model-replication-v0"
PRIMARY_ENDPOINT = "returned_final_hidden_state"
RAW_ENDPOINT = "raw_last_decoder_block_output"
VIEW_ORDER = ("glyph", "unicode_name", "codepoint_literal")
PAIR_ORDER = (("glyph_name", 0, 1), ("glyph_codepoint", 0, 2))
ENDPOINT_ORDER = (PRIMARY_ENDPOINT, RAW_ENDPOINT)
CARRIER_ORDER = ("article_a", "pipe")
DISTANCE_ORDER = (1, 2, 4, 8)


class DiagnosticError(RuntimeError):
    """Raised when a bound input or diagnostic invariant fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def safe_spearman(left: Sequence[float], right: Sequence[float]) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    require(a.shape == b.shape and a.ndim == 1, "Spearman inputs differ")
    if a.size < 2 or np.all(a == a[0]) or np.all(b == b[0]):
        return 0.0
    value = float(spearmanr(a, b).statistic)
    return value if math.isfinite(value) else 0.0


def quantiles(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=np.float64)
    require(array.size > 0, "Cannot summarize an empty diagnostic")
    return {
        "minimum": float(np.min(array)),
        "median": float(np.median(array)),
        "maximum": float(np.max(array)),
    }


def centered_normalized(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    array = np.asarray(values, dtype=np.float64)
    centered = array - np.mean(array, axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    normalized = centered / np.maximum(norms, 1e-12)
    return centered, normalized


def linear_cka(left: np.ndarray, right: np.ndarray) -> float:
    a, _ = centered_normalized(left)
    b, _ = centered_normalized(right)
    gram_a = a @ a.T
    gram_b = b @ b.T
    denominator = math.sqrt(
        float(np.sum(np.square(gram_a))) * float(np.sum(np.square(gram_b)))
    )
    return float(np.sum(gram_a * gram_b) / max(denominator, 1e-30))


def retrieval_metrics(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    _, a = centered_normalized(left)
    _, b = centered_normalized(right)
    similarity = a @ b.T
    count = int(similarity.shape[0])
    order = np.arange(count, dtype=np.int64)
    diagonal = np.diag(similarity)
    predictions = np.argmax(similarity, axis=1).astype(np.int64)
    ranks = 1 + np.sum(similarity > diagonal[:, None], axis=1)
    off_diagonal = float(
        (np.sum(similarity) - np.sum(diagonal)) / max(1, count * (count - 1))
    )
    return {
        "prediction": predictions,
        "top1": float(np.mean(predictions == order)),
        "mrr": float(np.mean(1.0 / ranks)),
        "paired_cosine": diagonal,
        "paired_cosine_mean": float(np.mean(diagonal)),
        "off_diagonal_cosine_mean": off_diagonal,
        "paired_minus_off_diagonal_margin": float(np.mean(diagonal) - off_diagonal),
        "similarity": similarity,
        "cka": linear_cka(left, right),
    }


def anova_profile_shares(profile: Sequence[float]) -> dict[str, float]:
    values = np.asarray(profile, dtype=np.float64).reshape(2, 4)
    grand = float(np.mean(values))
    carrier = 4.0 * float(np.sum(np.square(np.mean(values, axis=1) - grand)))
    distance = 2.0 * float(np.sum(np.square(np.mean(values, axis=0) - grand)))
    total = float(np.sum(np.square(values - grand)))
    interaction = max(0.0, total - carrier - distance)
    denominator = max(total, 1e-30)
    return {
        "carrier": carrier / denominator,
        "distance": distance / denominator,
        "interaction": interaction / denominator,
    }


def _check_ledger(directory: Path) -> int:
    ledger = directory / "SHA256SUMS"
    require(ledger.is_file(), f"Missing ledger: {ledger}")
    count = 0
    for raw in ledger.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        expected, name = raw.split(maxsplit=1)
        relative = Path(name.lstrip("*"))
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe ledger entry: {relative}",
        )
        path = directory / relative
        require(path.is_file(), f"Ledger target missing: {path}")
        require(sha256(path) == expected, f"Ledger mismatch: {path}")
        count += 1
    return count


def _model_roles(bundle: Path) -> tuple[str, ...]:
    receipt = read_json(bundle / "analysis" / "analysis_receipt.json")
    require(receipt.get("protocol_id") == T10_PROTOCOL_ID, "T10 receipt mismatch")
    roles = tuple(str(value) for value in receipt["model_order"])
    require(len(roles) == 9, "T10 model roster changed")
    return roles


def _cell_rows(bundle: Path, role: str) -> list[dict[str, Any]]:
    rows = read_jsonl(bundle / "summaries" / role / "cell_metrics.jsonl")
    require(len(rows) == 16, f"T10 cell row count changed: {role}")
    return rows


def _ordered_rows(rows: Sequence[Mapping[str, Any]], endpoint: str) -> list[Mapping[str, Any]]:
    lookup = {
        (str(row["endpoint"]), str(row["carrier"]), int(row["distance"])): row
        for row in rows
    }
    return [
        lookup[(endpoint, carrier, distance)]
        for carrier in CARRIER_ORDER
        for distance in DISTANCE_ORDER
    ]


def _compact_diagnostics(bundle: Path, roles: Sequence[str], selection: Path) -> dict[str, Any]:
    primary = read_json(bundle / "analysis" / "cross_model_primary_result.json")
    model_results = read_json(bundle / "analysis" / "model_cell_results.json")
    selection_rows = read_json(selection)["candidates"]
    items = [row for row in selection_rows if str(row["role"]) == "reserved_unrun"]
    items.sort(key=lambda row: int(row["source_index"]))
    require(len(items) == 292, "T10 item population changed")
    item_groups = [str(row["group"]) for row in items]

    profile_by_role: dict[str, list[float]] = {}
    item_advantage_by_role: dict[str, np.ndarray] = {}
    item_hits_by_role: dict[str, np.ndarray] = {}
    concentration: dict[str, Any] = {}
    endpoint_profile_correlations: dict[str, float] = {}
    metric_means: dict[str, dict[str, float]] = {}
    codepoint_zero_cells = 0

    for role in roles:
        rows = _cell_rows(bundle, role)
        final_rows = _ordered_rows(rows, PRIMARY_ENDPOINT)
        raw_rows = _ordered_rows(rows, RAW_ENDPOINT)
        profile = [
            float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["top1_accuracy_forward"])
            for row in final_rows
        ]
        raw_profile = [
            float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["top1_accuracy_forward"])
            for row in raw_rows
        ]
        profile_by_role[role] = profile
        endpoint_profile_correlations[role] = safe_spearman(profile, raw_profile)
        with np.load(bundle / "summaries" / role / "predictions.npz", allow_pickle=False) as stored:
            name = np.asarray(stored[f"{PRIMARY_ENDPOINT}__unrestricted__name"])
            codepoint = np.asarray(stored[f"{PRIMARY_ENDPOINT}__unrestricted__codepoint"])
        order = np.arange(name.shape[1], dtype=np.int64)
        name_correct = name == order[None, :]
        codepoint_correct = codepoint == order[None, :]
        hits = np.sum(name_correct, axis=0)
        advantage = np.mean(name_correct.astype(np.int8) - codepoint_correct.astype(np.int8), axis=0)
        item_hits_by_role[role] = hits
        item_advantage_by_role[role] = advantage
        total = int(np.sum(hits))
        top_count = int(math.ceil(0.10 * hits.size))
        concentration[role] = {
            "items_with_at_least_one_name_hit": int(np.count_nonzero(hits)),
            "name_hit_events": total,
            "top_ceil_10_percent_item_count": top_count,
            "top_ceil_10_percent_share_of_name_hits": float(
                np.sum(np.sort(hits)[::-1][:top_count]) / max(total, 1)
            ),
        }
        names = [float(row["unrestricted"]["pairs"]["glyph_name"]["top1_accuracy_forward"]) for row in final_rows]
        codes = [float(row["unrestricted"]["pairs"]["glyph_codepoint"]["top1_accuracy_forward"]) for row in final_rows]
        mrr = [float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["mean_reciprocal_rank_forward"]) for row in final_rows]
        margin = [float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["paired_minus_off_diagonal_margin"]) for row in final_rows]
        cka = [float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["centered_linear_cka"]) for row in final_rows]
        codepoint_zero_cells += sum(value == 0.0 for value in codes)
        metric_means[role] = {
            "name_top1_mean": float(np.mean(names)),
            "codepoint_top1_mean": float(np.mean(codes)),
            "top1_contrast_minimum": float(np.min(np.asarray(names) - np.asarray(codes))),
            "mrr_contrast_median": float(np.median(mrr)),
            "margin_contrast_mean": float(np.mean(margin)),
            "cka_contrast_mean": float(np.mean(cka)),
            "positive_top1_cells": int(np.sum((np.asarray(names) - np.asarray(codes)) > 0)),
            "positive_mrr_cells": int(np.sum(np.asarray(mrr) > 0)),
            "positive_margin_cells": int(np.sum(np.asarray(margin) > 0)),
            "positive_cka_cells": int(np.sum(np.asarray(cka) > 0)),
        }

    profile_correlations = [
        safe_spearman(profile_by_role[left], profile_by_role[right])
        for left, right in combinations(roles, 2)
    ]
    shares = [anova_profile_shares(profile_by_role[role]) for role in roles]
    advantage_correlations = [
        safe_spearman(item_advantage_by_role[left], item_advantage_by_role[right])
        for left, right in combinations(roles, 2)
    ]
    breadth = np.sum(
        np.stack([item_hits_by_role[role] > 0 for role in roles], axis=0), axis=0
    )
    group_values: dict[str, list[float]] = {}
    for group in sorted(set(item_groups)):
        indices = [index for index, value in enumerate(item_groups) if value == group]
        values = [
            float(item_advantage_by_role[role][index])
            for role in roles
            for index in indices
        ]
        group_values[group] = values

    qwen = (
        "qwen25_0p5b_base_bf16",
        "qwen25_1p5b_base_bf16",
        "qwen25_3b_base_bf16",
        "qwen25_7b_base_bf16",
    )
    qwen_advantage = np.stack([item_advantage_by_role[role] for role in qwen], axis=0)
    qwen_item_rhos = np.asarray(
        [
            float(spearmanr((0.5, 1.5, 3.0, 7.0), qwen_advantage[:, index]).statistic)
            for index in range(292)
            if not np.all(qwen_advantage[:, index] == qwen_advantage[0, index])
        ],
        dtype=np.float64,
    )
    qwen_item_rhos = qwen_item_rhos[np.isfinite(qwen_item_rhos)]
    rank_top1 = [metric_means[role]["top1_contrast_minimum"] for role in roles]

    discrete_cells: dict[str, Any] = {}
    for role in roles:
        result = model_results[role]
        full = result["unrestricted_component"]["contrast_by_cell"]
        matched = result["tokenization_matched_component"]["contrast_by_cell"]
        discrete_cells[role] = {
            "unrestricted_minimum": float(min(full)),
            "tokenization_matched_minimum": float(min(matched)),
            "unrestricted_cells_at_or_above_0p02": int(np.sum(np.asarray(full) >= 0.02)),
            "tokenization_matched_cells_at_or_above_0p02": int(np.sum(np.asarray(matched) >= 0.02)),
            "practical_pass": bool(result["practical_pass"]),
        }

    return {
        "registered_primary_unchanged": {
            "authorized_wording": primary["authorized_wording"],
            "partial_conjunction_p_value": float(primary["p_value"]),
            "core_practical_pass_count": int(primary["core_practical_pass_count"]),
            "positive": bool(primary["positive"]),
            "practical_floor": 0.02,
            "floor_as_net_correct_items_at_n_292": 6,
            "model_cell_discreteness": discrete_cells,
        },
        "carrier_distance_heterogeneity": {
            "cross_model_profile_spearman": quantiles(profile_correlations),
            "median_sum_of_squares_share": {
                key: float(np.median([row[key] for row in shares]))
                for key in ("carrier", "distance", "interaction")
            },
        },
        "item_support": {
            "by_model": concentration,
            "cross_model_item_advantage_spearman": quantiles(advantage_correlations),
            "items_hit_by_at_least_one_model": int(np.sum(breadth >= 1)),
            "items_hit_by_at_least_six_models": int(np.sum(breadth >= 6)),
            "items_hit_by_all_nine_models": int(np.sum(breadth == 9)),
            "unicode_group_mean_item_advantage": {
                group: float(np.mean(values)) for group, values in group_values.items()
            },
        },
        "qwen_size_profile": {
            "model_order": list(qwen),
            "minimum_top1_contrast": [
                float(model_results[role]["unrestricted_component"]["observed_minimum_cell_contrast"])
                for role in qwen
            ],
            "strictly_increasing_items": int(np.sum(np.all(np.diff(qwen_advantage, axis=0) > 0, axis=0))),
            "nondecreasing_items": int(np.sum(np.all(np.diff(qwen_advantage, axis=0) >= 0, axis=0))),
            "finite_item_spearman_count": int(qwen_item_rhos.size),
            "positive_finite_item_spearman_share": float(np.mean(qwen_item_rhos > 0)),
            "median_finite_item_spearman": float(np.median(qwen_item_rhos)),
            "scale_law_claim_authorized": False,
        },
        "metric_convergence_and_divergence": {
            "all_72_top1_contrasts_positive": all(
                metric_means[role]["positive_top1_cells"] == 8 for role in roles
            ),
            "all_72_mrr_contrasts_positive": all(
                metric_means[role]["positive_mrr_cells"] == 8 for role in roles
            ),
            "all_72_margin_contrasts_positive": all(
                metric_means[role]["positive_margin_cells"] == 8 for role in roles
            ),
            "positive_cka_cell_count": int(sum(metric_means[role]["positive_cka_cells"] for role in roles)),
            "cross_model_rank_spearman": {
                "top1_minimum_vs_median_mrr": safe_spearman(
                    rank_top1, [metric_means[role]["mrr_contrast_median"] for role in roles]
                ),
                "top1_minimum_vs_mean_margin": safe_spearman(
                    rank_top1, [metric_means[role]["margin_contrast_mean"] for role in roles]
                ),
                "top1_minimum_vs_mean_cka": safe_spearman(
                    rank_top1, [metric_means[role]["cka_contrast_mean"] for role in roles]
                ),
            },
            "model_means": metric_means,
        },
        "name_vs_codepoint": {
            "mean_name_top1_over_72_cells": float(np.mean([metric_means[role]["name_top1_mean"] for role in roles])),
            "mean_codepoint_top1_over_72_cells": float(np.mean([metric_means[role]["codepoint_top1_mean"] for role in roles])),
            "codepoint_zero_cells": int(codepoint_zero_cells),
            "cell_count": 72,
            "codepoint_is_sufficient_as_sole_t11_negative_control": False,
        },
        "final_vs_raw_profile": {
            "top1_contrast_profile_spearman_by_model": endpoint_profile_correlations,
        },
    }


def _raw_arrays(raw_runs: Path, role: str, expected_shards: int = 37) -> np.ndarray:
    directory = raw_runs / role
    _check_ledger(directory)
    index = read_json(directory / "SHARD_INDEX.json")
    require(index["model_role"] == role, f"Raw role mismatch: {role}")
    require(len(index["shards"]) == expected_shards, f"Raw shard count changed: {role}")
    arrays: list[np.ndarray] = []
    for shard_name, expected in sorted(index["shards"].items()):
        shard = directory / shard_name
        require(sha256(shard / "SHA256SUMS") == expected, "Raw shard ledger changed")
        _check_ledger(shard)
        value = np.load(shard / "activations.npy", mmap_mode="r", allow_pickle=False)
        require(value.ndim == 6 and value.shape[1:5] == (3, 2, 4, 2), "Raw shape changed")
        require(str(value.dtype) == "float32", "Raw dtype changed")
        require(bool(np.isfinite(value).all()), "Raw activation is nonfinite")
        arrays.append(np.asarray(value))
    combined = np.concatenate(arrays, axis=0)
    require(combined.shape[0] == 292, f"Raw item count changed: {role}")
    return combined


def _token_count_rows(repo_root: Path, roles: Sequence[str]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for role in roles:
        path = repo_root / "validation" / "semantic_atlas_cross_model_replication_v0" / "tokenizers" / f"{role}.json"
        receipt = read_json(path)
        result[role] = list(receipt["tokenizer"]["item_token_counts"])
    return result


def _raw_diagnostics(
    bundle: Path,
    raw_runs: Path,
    roles: Sequence[str],
    repo_root: Path,
) -> dict[str, Any]:
    arrays = {role: _raw_arrays(raw_runs, role) for role in roles}
    run_ledger_sha256 = {
        role: sha256(raw_runs / role / "SHA256SUMS") for role in roles
    }
    activation_bytes = sum(
        (raw_runs / role / shard / "activations.npy").stat().st_size
        for role in roles
        for shard in read_json(raw_runs / role / "SHARD_INDEX.json")["shards"]
    )
    prediction_mismatches = 0
    compared_prediction_values = 0
    max_top1_error = 0.0
    final_raw_cka_by_role: dict[str, list[float]] = {role: [] for role in roles}
    geometry: dict[tuple[str, int, int, int], np.ndarray] = {}
    cosine_maps: dict[tuple[str, int], np.ndarray] = {}
    paired_cosines: dict[tuple[str, int], np.ndarray] = {}

    for role in roles:
        rows = _cell_rows(bundle, role)
        with np.load(bundle / "summaries" / role / "predictions.npz", allow_pickle=False) as compact_file:
            compact = {key: np.asarray(compact_file[key]) for key in compact_file.files}
        for endpoint_index, endpoint in enumerate(ENDPOINT_ORDER):
            stored_name: list[np.ndarray] = []
            stored_code: list[np.ndarray] = []
            for carrier_index, carrier in enumerate(CARRIER_ORDER):
                for distance_index, distance in enumerate(DISTANCE_ORDER):
                    values = arrays[role][:, :, carrier_index, distance_index, endpoint_index, :]
                    name = retrieval_metrics(values[:, 0, :], values[:, 1, :])
                    code = retrieval_metrics(values[:, 0, :], values[:, 2, :])
                    stored_name.append(name["prediction"])
                    stored_code.append(code["prediction"])
                    row = next(
                        value
                        for value in rows
                        if value["endpoint"] == endpoint
                        and value["carrier"] == carrier
                        and int(value["distance"]) == distance
                    )
                    observed = float(name["top1"] - code["top1"])
                    reported = float(row["unrestricted"]["glyph_name_minus_glyph_codepoint"]["top1_accuracy_forward"])
                    max_top1_error = max(max_top1_error, abs(observed - reported))
                    cell = carrier_index * 4 + distance_index
                    for view_index in range(3):
                        geometry[(role, endpoint_index, cell, view_index)] = values[:, view_index, :]
                    if endpoint_index == 0:
                        cosine_maps[(role, cell)] = np.asarray(name["similarity"], dtype=np.float32)
                        paired_cosines[(role, cell)] = np.asarray(name["paired_cosine"], dtype=np.float32)
            reconstructed = {
                f"{endpoint}__unrestricted__name": np.stack(stored_name),
                f"{endpoint}__unrestricted__codepoint": np.stack(stored_code),
            }
            for key, value in reconstructed.items():
                expected = compact[key]
                prediction_mismatches += int(np.sum(value != expected))
                compared_prediction_values += int(value.size)
        for cell in range(8):
            for view_index in range(3):
                final_raw_cka_by_role[role].append(
                    linear_cka(
                        geometry[(role, 0, cell, view_index)],
                        geometry[(role, 1, cell, view_index)],
                    )
                )

    pair_geometry: dict[str, list[float]] = {
        "glyph_final": [],
        "glyph_raw": [],
        "unicode_name_final": [],
        "unicode_name_raw": [],
        "codepoint_final": [],
        "codepoint_raw": [],
    }
    qwen_roles = {
        "qwen25_0p5b_base_bf16",
        "qwen25_1p5b_base_bf16",
        "qwen25_3b_base_bf16",
        "qwen25_7b_base_bf16",
    }
    pair_geometry_medians = {key: [] for key in pair_geometry}
    qwen_pair_geometry = {key: [] for key in pair_geometry}
    qwen_pair_geometry_medians = {key: [] for key in pair_geometry}
    map_agreements: list[float] = []
    paired_agreements: list[float] = []
    pair_glyph_cka: dict[tuple[str, str], float] = {}
    for left, right in combinations(roles, 2):
        glyph_values: list[float] = []
        for endpoint_index, endpoint_label in enumerate(("final", "raw")):
            for view_index, view_label in enumerate(("glyph", "unicode_name", "codepoint")):
                key = f"{view_label}_{endpoint_label}"
                context_values: list[float] = []
                for cell in range(8):
                    value = linear_cka(
                        geometry[(left, endpoint_index, cell, view_index)],
                        geometry[(right, endpoint_index, cell, view_index)],
                    )
                    pair_geometry[key].append(value)
                    context_values.append(value)
                    if left in qwen_roles and right in qwen_roles:
                        qwen_pair_geometry[key].append(value)
                    if endpoint_index == 0 and view_index == 0:
                        glyph_values.append(value)
                pair_geometry_medians[key].append(float(np.median(context_values)))
                if left in qwen_roles and right in qwen_roles:
                    qwen_pair_geometry_medians[key].append(float(np.median(context_values)))
        pair_glyph_cka[(left, right)] = float(np.mean(glyph_values))
        for cell in range(8):
            map_agreements.append(
                safe_spearman(cosine_maps[(left, cell)].ravel(), cosine_maps[(right, cell)].ravel())
            )
            paired_agreements.append(
                safe_spearman(paired_cosines[(left, cell)], paired_cosines[(right, cell)])
            )

    token_rows = _token_count_rows(repo_root, roles)
    glyph_equal: list[float] = []
    triple_equal: list[float] = []
    glyph_cka: list[float] = []
    token_count_hit_rho: dict[str, float] = {}
    for left, right in combinations(roles, 2):
        left_counts = token_rows[left]
        right_counts = token_rows[right]
        glyph_equal.append(float(np.mean([
            a["token_counts"]["glyph"] == b["token_counts"]["glyph"]
            for a, b in zip(left_counts, right_counts, strict=True)
        ])))
        triple_equal.append(float(np.mean([
            a["exact_stratum_key"] == b["exact_stratum_key"]
            for a, b in zip(left_counts, right_counts, strict=True)
        ])))
        glyph_cka.append(pair_glyph_cka[(left, right)])
    for role in roles:
        counts = [int(row["token_counts"]["glyph"]) for row in token_rows[role]]
        with np.load(bundle / "summaries" / role / "predictions.npz", allow_pickle=False) as stored:
            name = np.asarray(stored[f"{PRIMARY_ENDPOINT}__unrestricted__name"])
        hits = np.sum(name == np.arange(292)[None, :], axis=0)
        token_count_hit_rho[role] = safe_spearman(counts, hits)

    return {
        "raw_archive_validation": {
            "status": "pass",
            "raw_root_basename": raw_runs.name,
            "model_cells": len(roles),
            "shards": 37 * len(roles),
            "activation_bytes": int(activation_bytes),
            "run_ledger_sha256_by_model": run_ledger_sha256,
            "prediction_arrays_reconstructed": len(roles) * len(ENDPOINT_ORDER) * 2,
            "prediction_values_compared": compared_prediction_values,
            "prediction_mismatches": prediction_mismatches,
            "maximum_top1_contrast_absolute_error": max_top1_error,
        },
        "final_norm_boundary": {
            "within_model_final_vs_raw_linear_cka_median": {
                role: float(np.median(values)) for role, values in final_raw_cka_by_role.items()
            },
        },
        "cross_model_item_geometry": {
            key: {
                "all_pair_context_values": quantiles(values),
                "pair_medians_over_eight_contexts": quantiles(pair_geometry_medians[key]),
            }
            for key, values in pair_geometry.items()
        },
        "qwen_family_item_geometry": {
            key: {
                "all_pair_context_values": quantiles(values),
                "pair_medians_over_eight_contexts": quantiles(qwen_pair_geometry_medians[key]),
            }
            for key, values in qwen_pair_geometry.items()
        },
        "cross_model_glyph_name_map_agreement": quantiles(map_agreements),
        "cross_model_paired_item_cosine_agreement": quantiles(paired_agreements),
        "tokenization_associations": {
            "pairwise_glyph_token_count_equality_vs_glyph_cka_spearman": safe_spearman(glyph_equal, glyph_cka),
            "pairwise_exact_triple_equality_vs_glyph_cka_spearman": safe_spearman(triple_equal, glyph_cka),
            "within_model_glyph_token_count_vs_name_hits_spearman": token_count_hit_rho,
            "causal_or_tokenizer_independence_claim_authorized": False,
        },
    }


def _report(payload: Mapping[str, Any]) -> str:
    compact = payload["compact_diagnostics"]
    primary = compact["registered_primary_unchanged"]
    heterogeneity = compact["carrier_distance_heterogeneity"]
    support = compact["item_support"]
    raw = payload.get("raw_diagnostics")
    lines = [
        "# T10 cross-model diagnostic analysis v1\n\n",
        "Status: **retrospective descriptive analysis; T10 primary unchanged**.\n\n",
        f"The registered outcome remains `{primary['authorized_wording']}`. The statistical partial-conjunction p-value was `{primary['partial_conjunction_p_value']:.4g}`, while only `{primary['core_practical_pass_count']}/4` core cells met the frozen practical rule. At 292 items, the `0.02` floor is a six-net-item boundary.\n\n",
        "## What the finer analysis changes\n\n",
        f"Carrier-distance profiles are not shared across models: pairwise profile Spearman correlations have median `{heterogeneity['cross_model_profile_spearman']['median']:.3f}` and range `{heterogeneity['cross_model_profile_spearman']['minimum']:.3f}` to `{heterogeneity['cross_model_profile_spearman']['maximum']:.3f}`. Median variance shares are `{heterogeneity['median_sum_of_squares_share']['carrier']:.3f}` carrier, `{heterogeneity['median_sum_of_squares_share']['distance']:.3f}` distance, and `{heterogeneity['median_sum_of_squares_share']['interaction']:.3f}` interaction.\n\n",
        f"Name retrieval is also concentrated in different items. At least one model retrieves `{support['items_hit_by_at_least_one_model']}/292` items in one or more contexts, only `{support['items_hit_by_at_least_six_models']}` are hit by six or more models, and none are hit by all nine.\n\n",
        "All 72 final-endpoint cells have positive top-1, MRR, and paired-margin name-versus-codepoint contrasts, but CKA does not share that universal direction. Codepoint top-1 is zero in "
        f"`{compact['name_vs_codepoint']['codepoint_zero_cells']}/72` cells, so codepoint text is retained as a weak comparator rather than T11's sole negative control.\n\n",
        "## Consequence for T11\n\n",
        "T11 should use continuous item-level matched-label margins, breadth, context stability, raw/final-norm change, and cross-model geometry. Minimum top-1 remains secondary. T11 is a new exploratory lane and cannot lower T10's floor, replace its core roster, or retroactively rescue its primary.\n",
    ]
    if raw is not None:
        validation = raw["raw_archive_validation"]
        geometry = raw["cross_model_item_geometry"]
        lines.extend(
            [
                "\n## Raw reconstruction\n\n",
                f"The raw archive reconstructed `{validation['prediction_arrays_reconstructed']}` prediction arrays with `{validation['prediction_mismatches']}` mismatches. The maximum absolute top-1 contrast error was `{validation['maximum_top1_contrast_absolute_error']:.3e}`.\n\n",
                f"Across model-pair medians over the eight contexts, median item-geometry CKA is `{geometry['glyph_final']['pair_medians_over_eight_contexts']['median']:.3f}` for final glyph states, `{geometry['unicode_name_final']['pair_medians_over_eight_contexts']['median']:.3f}` for names, and `{geometry['codepoint_final']['pair_medians_over_eight_contexts']['median']:.3f}` for codepoint text. The largest cross-model divergence is therefore on the glyph side, descriptively.\n",
            ]
        )
    return "".join(lines)


def write_bundle(
    *,
    bundle: Path,
    selection: Path,
    output: Path,
    raw_runs: Path | None,
    repo_root: Path,
) -> dict[str, Any]:
    require(not output.exists(), f"Output already exists: {output}")
    roles = _model_roles(bundle)
    compact_targets = 0
    for directory in [bundle / "analysis", *[bundle / "summaries" / role for role in roles]]:
        compact_targets += _check_ledger(directory)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "analysis_role": "retrospective_descriptive_t10_diagnostic_t10_primary_unchanged",
        "t10_bundle": {
            "path": bundle.as_posix(),
            "public_manifest_sha256": sha256(bundle / "PUBLIC_MANIFEST.json"),
            "ledger_targets_rehashed": compact_targets,
        },
        "selection_manifest_sha256": sha256(selection),
        "implementation_script_sha256": sha256(Path(__file__).resolve()),
        "model_order": list(roles),
        "compact_diagnostics": _compact_diagnostics(bundle, roles, selection),
        "raw_archive_provided": raw_runs is not None,
        "t10_primary_changed": False,
        "t10_rescue_authorized": False,
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "tokenizer_independence_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "model_general_claim_authorized": False,
        "model_forward_calls": 0,
        "generation_calls": 0,
        "intervention_calls": 0,
    }
    if raw_runs is not None:
        payload["raw_diagnostics"] = _raw_diagnostics(
            bundle, raw_runs, roles, repo_root
        )
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.partial-", dir=output.parent))
    try:
        (stage / "diagnostics.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (stage / "report.md").write_text(_report(payload), encoding="utf-8")
        ledger_lines = [
            f"{sha256(stage / name)}  {name}\n" for name in ("diagnostics.json", "report.md")
        ]
        (stage / "SHA256SUMS").write_text("".join(ledger_lines), encoding="utf-8")
        stage.rename(output)
    except Exception:
        raise
    return {
        "status": "pass",
        "output": output.as_posix(),
        "diagnostics_sha256": sha256(output / "diagnostics.json"),
        "raw_archive_validated": raw_runs is not None,
    }


def validate_bundle(output: Path) -> dict[str, Any]:
    checked = _check_ledger(output)
    payload = read_json(output / "diagnostics.json")
    require(payload.get("protocol_id") == PROTOCOL_ID, "Diagnostic protocol mismatch")
    require(payload.get("status") == "pass", "Diagnostic did not pass")
    require(payload.get("t10_primary_changed") is False, "T10 primary was changed")
    require(payload.get("t10_rescue_authorized") is False, "T10 rescue became authorized")
    raw = payload.get("raw_diagnostics")
    if payload.get("raw_archive_provided"):
        require(raw is not None, "Raw diagnostic payload is absent")
        require(raw["raw_archive_validation"]["prediction_mismatches"] == 0, "Raw predictions differ")
    return {
        "status": "pass",
        "ledger_targets_rehashed": checked,
        "raw_archive_validated": bool(payload.get("raw_archive_provided")),
        "registered_primary_unchanged": True,
    }


def _parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument(
        "--bundle",
        type=Path,
        default=root / "artifacts" / "semantic_atlas_cross_model_replication_v0",
    )
    analyze.add_argument(
        "--selection",
        type=Path,
        default=root / "data" / "manifests" / "mistral7b_semantic_atlas_selection_v0.json",
    )
    analyze.add_argument("--raw-runs", type=Path)
    analyze.add_argument("--output", type=Path, required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = _parser().parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.command == "analyze":
        result = write_bundle(
            bundle=args.bundle,
            selection=args.selection,
            output=args.output,
            raw_runs=args.raw_runs,
            repo_root=root,
        )
    elif args.command == "validate":
        result = validate_bundle(args.output)
    else:  # pragma: no cover
        raise DiagnosticError(f"Unknown command: {args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
