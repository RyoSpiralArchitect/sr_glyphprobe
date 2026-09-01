#!/usr/bin/env python3
"""Independent validator for the conditional T19-C component intervention."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-t19-lexical-alias-component-causal-v0"
PARENT_PROTOCOL_ID = "glyphprobe-t19-lexical-alias-unicode-control-v0"
ROLE = "llama32_3b_base_bf16"
SITE_ORDER = (
    ("attn_out", 21),
    ("mlp_out", 21),
    ("attn_out", 24),
    ("mlp_out", 24),
    ("attn_out", 27),
    ("mlp_out", 27),
)
PRIMARY_SITES = (("attn_out", 24), ("mlp_out", 24))


class ValidationError(RuntimeError):
    """Raised when independent causal reconstruction disagrees with evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def bank_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(
        list(rows), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized(value: np.ndarray) -> np.ndarray:
    centered = np.asarray(value, dtype=np.float64) - np.mean(
        value, axis=0, keepdims=True
    )
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    require(bool(np.all(norms > 0)), "Zero centered row norm")
    return centered / norms


def retrieval_item_values(
    query: np.ndarray,
    alias_target: np.ndarray,
    codepoint_target: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    query_value = normalized(query)
    alias_value = normalized(alias_target)
    codepoint_value = normalized(codepoint_target)
    identity = np.arange(len(query_value))
    alias_predictions = np.argmax(query_value @ alias_value.T, axis=1)
    codepoint_predictions = np.argmax(query_value @ codepoint_value.T, axis=1)
    item_values = (
        (alias_predictions == identity).astype(np.float64)
        - (codepoint_predictions == identity).astype(np.float64)
    )
    return item_values, {
        "alias_top1": float(np.mean(alias_predictions == identity)),
        "codepoint_top1": float(np.mean(codepoint_predictions == identity)),
        "alias_minus_codepoint_top1": float(np.mean(item_values)),
    }


def sign_flip(values: np.ndarray, *, draws: int, seed: int) -> dict[str, Any]:
    observed = float(np.mean(values))
    rng = np.random.default_rng(seed)
    exceedances = 0
    for start in range(0, draws, 2000):
        stop = min(draws, start + 2000)
        signs = rng.integers(
            0,
            2,
            size=(stop - start, len(values)),
            dtype=np.int8,
        ) * 2 - 1
        statistics = np.mean(signs * values[None, :], axis=1)
        exceedances += int(np.sum(statistics >= observed - 1e-15))
    return {
        "draws": draws,
        "seed": seed,
        "observed": observed,
        "exceedances": exceedances,
        "p_value_one_sided": (1 + exceedances) / (draws + 1),
    }


def bootstrap(values: np.ndarray, *, replicates: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 500):
        stop = min(replicates, start + 500)
        indices = rng.integers(
            0,
            len(values),
            size=(stop - start, len(values)),
        )
        draws[start:stop] = np.mean(values[indices], axis=1)
    return {
        "replicates": replicates,
        "seed": seed,
        "lower_95": float(np.quantile(draws, 0.025)),
        "upper_95": float(np.quantile(draws, 0.975)),
        "bootstrap_mean": float(np.mean(draws)),
    }


def assert_close(actual: float, expected: float, message: str) -> None:
    require(
        math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-15),
        message,
    )


def assert_mapping_close(
    actual: Mapping[str, float],
    expected: Mapping[str, float],
    message: str,
) -> None:
    require(set(actual) == set(expected), f"{message} keys changed")
    for key in actual:
        assert_close(actual[key], expected[key], f"{message}/{key} changed")


def validate(
    root: Path,
    source_root: Path,
    evaluation_root: Path,
    analysis: Path,
) -> dict[str, Any]:
    config = yaml.safe_load(
        (root / "configs/t19_lexical_alias_unicode_control_v0.yaml").read_text(
            encoding="utf-8"
        )
    )
    selection = read_json(
        root / "data/manifests/t19_lexical_alias_unicode_control_v0.json"
    )
    go_path = root / "data/manifests/t19_lexical_alias_component_causal_v0_go.json"
    go = read_json(go_path)
    require(config["protocol_id"] == PARENT_PROTOCOL_ID, "Parent config changed")
    require(go["protocol_id"] == PROTOCOL_ID, "Go protocol changed")
    require(
        go["status"] == "causal_go_admitted_before_source_or_eval_forwards",
        "Go status changed",
    )
    require(int(go["source_model_forwards_at_go"]) == 0, "Go contains source forwards")
    require(int(go["evaluation_model_forwards_at_go"]) == 0, "Go contains eval forwards")
    require(int(go["intervention_calls_at_go"]) == 0, "Go contains interventions")
    require(
        sha256(root / "scripts/t19_lexical_alias_component_causal_v0.py")
        == go["causal_executor_analyzer_sha256"],
        "Causal executor changed after go",
    )
    source_bank = sorted(
        selection["causal_source_items"], key=lambda row: int(row["bank_index"])
    )
    evaluation_bank = sorted(
        selection["causal_eval_items"], key=lambda row: int(row["bank_index"])
    )
    require(len(source_bank) == 128 and len(evaluation_bank) == 192, "Causal bank count changed")
    require(bank_hash(source_bank) == go["source_bank_sha256"], "Source bank binding changed")
    require(bank_hash(evaluation_bank) == go["evaluation_bank_sha256"], "Evaluation bank binding changed")
    require(
        not {row["codepoint"] for row in source_bank}.intersection(
            row["codepoint"] for row in evaluation_bank
        ),
        "Causal banks overlap",
    )

    source_receipt_path = source_root / "source_receipt.json"
    source_receipt = read_json(source_receipt_path)
    require(source_receipt["protocol_id"] == PROTOCOL_ID, "Source protocol changed")
    require(source_receipt["status"] == "causal_source_subspaces_complete", "Source incomplete")
    require(source_receipt["go_manifest_sha256"] == sha256(go_path), "Source/go binding changed")
    require(int(source_receipt["model_forward_calls"]) == 256, "Source forward count changed")
    require(int(source_receipt["intervention_calls"]) == 0, "Source contains interventions")
    for name, expected in source_receipt["outputs"].items():
        require(sha256(source_root / name) == expected, f"Source output changed: {name}")
    with np.load(source_root / "subspaces.npz", allow_pickle=False) as values:
        learned = np.asarray(values["learned"], dtype=np.float32)
        random_control = np.asarray(values["random_control"], dtype=np.float32)
        glyph_means = np.asarray(values["glyph_means"], dtype=np.float32)
    require(learned.shape == random_control.shape == (6, 3072, 8), "Subspace shape changed")
    require(glyph_means.shape == (6, 3072), "Source mean shape changed")
    for site_index in range(6):
        require(
            float(np.max(np.abs(learned[site_index].T @ learned[site_index] - np.eye(8)))) < 2e-5,
            "Learned subspace is not orthonormal",
        )
        require(
            float(np.max(np.abs(random_control[site_index].T @ random_control[site_index] - np.eye(8)))) < 2e-5,
            "Control subspace is not orthonormal",
        )
        require(
            float(np.max(np.abs(learned[site_index].T @ random_control[site_index]))) < 2e-5,
            "Learned and control subspaces overlap",
        )

    evaluation_receipt_path = evaluation_root / "evaluation_receipt.json"
    evaluation_receipt = read_json(evaluation_receipt_path)
    require(evaluation_receipt["protocol_id"] == PROTOCOL_ID, "Evaluation protocol changed")
    require(evaluation_receipt["status"] == "causal_evaluation_complete_sealed", "Evaluation incomplete")
    require(
        evaluation_receipt["source_receipt_sha256"] == sha256(source_receipt_path),
        "Evaluation/source binding changed",
    )
    require(evaluation_receipt["go_manifest_sha256"] == sha256(go_path), "Evaluation/go binding changed")
    require(int(evaluation_receipt["model_forward_calls"]) == 2_880, "Evaluation forward count changed")
    require(int(evaluation_receipt["intervention_rows"]) == 8_064, "Intervention row count changed")
    for name, expected in evaluation_receipt["outputs"].items():
        require(sha256(evaluation_root / name) == expected, f"Evaluation output changed: {name}")
    with np.load(evaluation_root / "evaluation_states.npz", allow_pickle=False) as values:
        targets = np.asarray(values["baseline_targets"], dtype=np.float32)
        queries = np.asarray(values["baseline_queries"], dtype=np.float32)
        components = np.asarray(values["baseline_components"], dtype=np.float32)
        glyph_conditions = np.asarray(values["glyph_conditions"], dtype=np.float32)
        codepoint_conditions = np.asarray(values["codepoint_conditions"], dtype=np.float32)
    require(targets.shape == queries.shape == (192, 2, 3072), "Baseline shape changed")
    require(components.shape == (6, 192, 2, 3072), "Component shape changed")
    require(glyph_conditions.shape == (6, 192, 4, 3072), "Glyph condition shape changed")
    require(codepoint_conditions.shape == (6, 192, 3, 3072), "Codepoint condition shape changed")

    stored_site_value = read_json(analysis / "causal_site_results.json")
    stored_sites = {
        (str(row["site"]), int(row["block_index"])): row
        for row in stored_site_value["sites"]
    }
    require(tuple(stored_sites) == SITE_ORDER, "Stored causal site order changed")
    alias_target = targets[:, 0]
    codepoint_target = targets[:, 1]
    base_glyph_items, base_glyph_metrics = retrieval_item_values(
        queries[:, 0], alias_target, codepoint_target
    )
    base_codepoint_items, base_codepoint_metrics = retrieval_item_values(
        queries[:, 1], alias_target, codepoint_target
    )
    del base_glyph_items, base_codepoint_items
    draws = 99_999
    replicates = 20_000
    practical = float(
        config["causal_followup"]["primary_decision"]["practical_minimum_each"]
    )
    reconstructed: list[dict[str, Any]] = []
    for site_index, key in enumerate(SITE_ORDER):
        stored = stored_sites[key]
        zero_glyph_items, zero_glyph_metrics = retrieval_item_values(
            glyph_conditions[site_index, :, 0], alias_target, codepoint_target
        )
        necessity_items, necessity_metrics = retrieval_item_values(
            glyph_conditions[site_index, :, 1], alias_target, codepoint_target
        )
        random_necessity_items, random_necessity_metrics = retrieval_item_values(
            glyph_conditions[site_index, :, 2], alias_target, codepoint_target
        )
        restoration_items, restoration_metrics = retrieval_item_values(
            glyph_conditions[site_index, :, 3], alias_target, codepoint_target
        )
        zero_codepoint_items, zero_codepoint_metrics = retrieval_item_values(
            codepoint_conditions[site_index, :, 0], alias_target, codepoint_target
        )
        sufficiency_items, sufficiency_metrics = retrieval_item_values(
            codepoint_conditions[site_index, :, 1], alias_target, codepoint_target
        )
        random_sufficiency_items, random_sufficiency_metrics = retrieval_item_values(
            codepoint_conditions[site_index, :, 2], alias_target, codepoint_target
        )
        del zero_glyph_items, restoration_items, zero_codepoint_items
        necessity_adjusted = random_necessity_items - necessity_items
        sufficiency_adjusted = sufficiency_items - random_sufficiency_items
        necessity_test = sign_flip(
            necessity_adjusted,
            draws=draws,
            seed=2026090400 + site_index * 10,
        )
        sufficiency_test = sign_flip(
            sufficiency_adjusted,
            draws=draws,
            seed=2026090401 + site_index * 10,
        )
        necessity_interval = bootstrap(
            necessity_adjusted,
            replicates=replicates,
            seed=2026090500 + site_index * 10,
        )
        sufficiency_interval = bootstrap(
            sufficiency_adjusted,
            replicates=replicates,
            seed=2026090501 + site_index * 10,
        )
        assert_mapping_close(base_glyph_metrics, stored["baseline_glyph"], f"{key} baseline glyph")
        assert_mapping_close(base_codepoint_metrics, stored["baseline_codepoint"], f"{key} baseline codepoint")
        condition_metrics = {
            "zero_glyph": zero_glyph_metrics,
            "necessity": necessity_metrics,
            "random_necessity": random_necessity_metrics,
            "restoration": restoration_metrics,
            "zero_codepoint": zero_codepoint_metrics,
            "sufficiency": sufficiency_metrics,
            "random_sufficiency": random_sufficiency_metrics,
        }
        for condition, metrics in condition_metrics.items():
            assert_mapping_close(metrics, stored["conditions"][condition], f"{key}/{condition}")
        assert_mapping_close(necessity_test, stored["necessity_test"], f"{key}/necessity test")
        assert_mapping_close(sufficiency_test, stored["sufficiency_test"], f"{key}/sufficiency test")
        assert_mapping_close(necessity_interval, stored["necessity_interval"], f"{key}/necessity interval")
        assert_mapping_close(sufficiency_interval, stored["sufficiency_interval"], f"{key}/sufficiency interval")
        necessity_effect = float(np.mean(necessity_adjusted))
        sufficiency_effect = float(np.mean(sufficiency_adjusted))
        assert_close(necessity_effect, stored["necessity_adjusted_effect"], f"{key} necessity effect changed")
        assert_close(sufficiency_effect, stored["sufficiency_adjusted_effect"], f"{key} sufficiency effect changed")
        zero_glyph_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, 0] - queries[:, 0]) ** 2)))
        zero_codepoint_rms = float(np.sqrt(np.mean((codepoint_conditions[site_index, :, 0] - queries[:, 1]) ** 2)))
        restoration_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, 3] - queries[:, 0]) ** 2)))
        engineering = {
            "zero_glyph_final_rms": zero_glyph_rms,
            "zero_codepoint_final_rms": zero_codepoint_rms,
            "restoration_final_rms": restoration_rms,
            "pass": max(zero_glyph_rms, zero_codepoint_rms, restoration_rms) <= 1e-6,
        }
        for name in (
            "zero_glyph_final_rms",
            "zero_codepoint_final_rms",
            "restoration_final_rms",
        ):
            assert_close(engineering[name], stored["engineering"][name], f"{key}/{name} changed")
        require(engineering["pass"] == bool(stored["engineering"]["pass"]), f"{key} engineering decision changed")
        site_iut_p = max(
            float(necessity_test["p_value_one_sided"]),
            float(sufficiency_test["p_value_one_sided"]),
        )
        practical_pass = bool(
            necessity_effect >= practical
            and sufficiency_effect >= practical
            and necessity_interval["lower_95"] > practical
            and sufficiency_interval["lower_95"] > practical
        )
        assert_close(site_iut_p, stored["site_iut_p"], f"{key} IUT changed")
        require(practical_pass == bool(stored["practical_and_interval_pass"]), f"{key} practical decision changed")
        reconstructed.append(
            {
                "site": key[0],
                "block_index": key[1],
                "primary_site": key in PRIMARY_SITES,
                "site_iut_p": site_iut_p,
                "practical_pass": practical_pass,
                "engineering_pass": engineering["pass"],
            }
        )

    primary_rows = sorted(
        (row for row in reconstructed if row["primary_site"]),
        key=lambda row: (float(row["site_iut_p"]), str(row["site"])),
    )
    still_rejecting = True
    for index, row in enumerate(primary_rows):
        threshold = 0.05 / (len(primary_rows) - index)
        reject = still_rejecting and float(row["site_iut_p"]) <= threshold
        still_rejecting = bool(reject)
        row["holm_threshold"] = threshold
        row["positive"] = bool(
            reject and row["practical_pass"] and row["engineering_pass"]
        )
    positive_sites = [
        f"{row['site']}:{row['block_index']}" for row in primary_rows if row["positive"]
    ]
    primary_result = read_json(analysis / "causal_primary_result.json")
    require(primary_result["protocol_id"] == PROTOCOL_ID, "Primary protocol changed")
    require(positive_sites == primary_result["positive_sites"], "Positive site list changed")
    require(bool(positive_sites) == bool(primary_result["positive"]), "Primary decision changed")
    stored_primary = {
        (str(row["site"]), int(row["block_index"])): row
        for row in primary_result["primary_sites"]
    }
    for row in primary_rows:
        key = (str(row["site"]), int(row["block_index"]))
        assert_close(row["holm_threshold"], stored_primary[key]["holm_threshold"], f"{key} Holm threshold changed")
        require(row["positive"] == bool(stored_primary[key]["positive"]), f"{key} primary decision changed")

    analysis_receipt_path = analysis / "analysis_receipt.json"
    analysis_receipt = read_json(analysis_receipt_path)
    require(analysis_receipt["protocol_id"] == PROTOCOL_ID, "Analysis protocol changed")
    require(
        analysis_receipt["evaluation_receipt_sha256"]
        == sha256(evaluation_receipt_path),
        "Analysis/evaluation binding changed",
    )
    for name, expected in analysis_receipt["outputs"].items():
        require(sha256(analysis / name) == expected, f"Analysis output changed: {name}")
    require(bool(positive_sites) == bool(analysis_receipt["primary_positive"]), "Analysis decision changed")
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "independent_causal_validation_pass",
        "go_manifest_sha256": sha256(go_path),
        "source_receipt_sha256": sha256(source_receipt_path),
        "evaluation_receipt_sha256": sha256(evaluation_receipt_path),
        "analysis_receipt_sha256": sha256(analysis_receipt_path),
        "analysis_output_sha256": dict(analysis_receipt["outputs"]),
        "source_model_forward_calls": int(source_receipt["model_forward_calls"]),
        "evaluation_model_forward_calls": int(evaluation_receipt["model_forward_calls"]),
        "intervention_rows": int(evaluation_receipt["intervention_rows"]),
        "recomputed_sign_flip_tests": len(SITE_ORDER) * 2,
        "sign_flip_draws_per_test": draws,
        "recomputed_bootstrap_intervals": len(SITE_ORDER) * 2,
        "bootstrap_replicates_per_interval": replicates,
        "engineering_controls_passed": sum(
            bool(row["engineering_pass"]) for row in reconstructed
        ),
        "primary_positive": bool(positive_sites),
        "positive_sites": positive_sites,
        "claim_boundary": config["claim_boundary"],
        "raw_activations_committed_to_git": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = validate(
        args.root.resolve(),
        args.source_root,
        args.evaluation_root,
        args.analysis,
    )
    require(not args.output.exists(), f"Validation output exists: {args.output}")
    write_json(args.output, value)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
