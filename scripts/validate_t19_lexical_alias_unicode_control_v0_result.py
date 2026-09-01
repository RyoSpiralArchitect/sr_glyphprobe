#!/usr/bin/env python3
"""Independent validator for the T19-L lexical-alias result."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-t19-lexical-alias-unicode-control-v0"
MODEL_ROLES = (
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
CORE_ROLES = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
)
KIND_ORDER = ("emoji", "symbol")
COMPONENT_ORDER = ("unrestricted", "matched")
VIEW_COUNT = 4
CARRIER_COUNT = 2
DISTANCE_COUNT = 4
DEPTH_COUNT = 9
ITEM_COUNT = 110
SHARD_COUNT = 5


class ValidationError(RuntimeError):
    """Raised when independent reconstruction disagrees with stored evidence."""


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


def stratified_permutation(
    rng: np.random.Generator,
    item_count: int,
    strata: Sequence[Sequence[int]],
) -> np.ndarray:
    flattened = sorted(int(value) for group in strata for value in group)
    require(flattened == list(range(item_count)), "Matched strata do not partition items")
    require(all(len(group) >= 2 for group in strata), "Matched stratum is singleton")
    mapping = np.arange(item_count, dtype=np.int64)
    for group in strata:
        indices = np.asarray(group, dtype=np.int64)
        mapping[indices] = rng.permutation(indices)
    return mapping


def effect(
    alias_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
) -> float:
    require(
        alias_predictions.shape == codepoint_predictions.shape
        and alias_predictions.shape[0] == 24,
        "Primary prediction shape changed",
    )
    identity = np.arange(alias_predictions.shape[1], dtype=np.int64)
    return float(
        np.mean(alias_predictions == identity[None, :])
        - np.mean(codepoint_predictions == identity[None, :])
    )


def randomization_test(
    alias_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
    strata: Sequence[Sequence[int]],
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    observed = effect(alias_predictions, codepoint_predictions)
    count = alias_predictions.shape[1]
    identity = np.arange(count, dtype=np.int64)
    fixed_codepoint = float(
        np.mean(codepoint_predictions == identity[None, :])
    )
    rng = np.random.default_rng(seed)
    exceedances = 0
    null_sum = 0.0
    null_sumsq = 0.0
    for _draw in range(draws):
        mapping = stratified_permutation(rng, count, strata)
        statistic = float(
            np.mean(alias_predictions == mapping[None, :]) - fixed_codepoint
        )
        exceedances += int(statistic >= observed - 1e-15)
        null_sum += statistic
        null_sumsq += statistic * statistic
    null_mean = null_sum / draws
    return {
        "observed": observed,
        "exceedances": exceedances,
        "p_value_one_sided": (1 + exceedances) / (draws + 1),
        "null_mean": null_mean,
        "null_sd": math.sqrt(max(0.0, null_sumsq / draws - null_mean * null_mean)),
    }


def holm(
    rows: Sequence[Mapping[str, Any]],
    alpha: float,
) -> dict[str, dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (float(row["model_iut_p"]), str(row["model_role"])),
    )
    still_rejecting = True
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(ordered):
        threshold = alpha / (len(ordered) - index)
        reject = still_rejecting and float(row["model_iut_p"]) <= threshold
        still_rejecting = bool(reject)
        result[str(row["model_role"])] = {
            "rank": index + 1,
            "threshold": threshold,
            "reject": bool(reject and row["practical_pass"]),
        }
    return result


def partial_conjunction(values: Mapping[str, float], r: int) -> dict[str, Any]:
    ordered = sorted((float(value), role) for role, value in values.items())
    require(1 <= r <= len(ordered), "Invalid partial-conjunction rank")
    rth = ordered[r - 1]
    return {
        "rth_role": rth[1],
        "rth_p": rth[0],
        "p_value": min(1.0, (len(ordered) - r + 1) * rth[0]),
    }


def _validate_runs(
    run_root: Path,
    widths: Mapping[str, int],
    summary_receipt_hashes: Mapping[str, str],
) -> dict[str, Any]:
    role_receipts: dict[str, str] = {}
    total_forwards = 0
    total_vectors = 0
    for role in MODEL_ROLES:
        role_directory = run_root / role
        role_receipt = read_json(role_directory / "role_receipt.json")
        require(
            role_receipt.get("protocol_id") == PROTOCOL_ID
            and role_receipt.get("model_role") == role,
            f"Run receipt mismatch: {role}",
        )
        require(
            role_receipt.get("runtime_t18_token_sequences_match_frozen_preflight")
            is True,
            f"Runtime tokenizer was not admitted: {role}",
        )
        require(int(role_receipt["model_forward_calls"]) == 880, "Role forward count changed")
        require(int(role_receipt["readout_vectors"]) == 31_680, "Role vector count changed")
        role_hash = sha256(role_directory / "role_receipt.json")
        role_receipts[role] = role_hash
        total_forwards += int(role_receipt["model_forward_calls"])
        total_vectors += int(role_receipt["readout_vectors"])
        for shard_index in range(SHARD_COUNT):
            shard = role_directory / f"shard_{shard_index:04d}"
            receipt = read_json(shard / "receipt.json")
            require(receipt.get("protocol_id") == PROTOCOL_ID, "Shard protocol changed")
            for name, expected in receipt["outputs"].items():
                require(sha256(shard / name) == expected, f"Shard output changed: {role}/{shard_index}/{name}")
            start = shard_index * 22
            count = min(22, ITEM_COUNT - start)
            array = np.load(shard / "activations.npy", mmap_mode="r", allow_pickle=False)
            require(
                array.shape
                == (
                    count,
                    VIEW_COUNT,
                    CARRIER_COUNT,
                    DISTANCE_COUNT,
                    DEPTH_COUNT,
                    int(widths[role]),
                ),
                f"Shard shape changed: {role}/{shard_index}",
            )
            require(array.dtype == np.float32, "Shard dtype changed")
    require(total_forwards == 7_920, "Total forward count changed")
    require(total_vectors == 285_120, "Total vector count changed")
    return {
        "role_receipt_sha256": role_receipts,
        "summary_receipt_sha256": dict(summary_receipt_hashes),
        "total_model_forward_calls": total_forwards,
        "total_readout_vectors": total_vectors,
        "raw_shards_rehashed": len(MODEL_ROLES) * SHARD_COUNT,
    }


def validate(
    root: Path,
    summary_root: Path,
    analysis: Path,
    run_root: Path | None,
) -> dict[str, Any]:
    config_path = root / "configs/t19_lexical_alias_unicode_control_v0.yaml"
    selection_path = root / "data/manifests/t19_lexical_alias_unicode_control_v0.json"
    freeze_path = root / "data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    selection = read_json(selection_path)
    freeze = read_json(freeze_path)
    require(config["protocol_id"] == PROTOCOL_ID, "Config protocol changed")
    require(selection["protocol_id"] == PROTOCOL_ID, "Selection protocol changed")
    require(freeze["protocol_id"] == PROTOCOL_ID, "Freeze protocol changed")
    require(
        freeze["status"] == "final_execution_freeze_zero_t19_model_forwards_or_interventions",
        "Freeze status changed",
    )
    require(int(freeze["model_forwards_at_freeze"]) == 0, "Freeze contains forwards")
    require(int(freeze["intervention_calls_at_freeze"]) == 0, "Freeze contains interventions")
    require(sha256(selection_path) == freeze["selection_manifest_sha256"], "Selection binding changed")
    for relative, expected in freeze["frozen_assets"].items():
        path = root / relative
        require(path.is_file() and sha256(path) == expected, f"Frozen asset changed: {relative}")

    observational = sorted(
        selection["observational_items"], key=lambda row: int(row["selection_index"])
    )
    source = sorted(selection["causal_source_items"], key=lambda row: int(row["bank_index"]))
    evaluation = sorted(selection["causal_eval_items"], key=lambda row: int(row["bank_index"]))
    require(len(observational) == 110 and len(source) == 128 and len(evaluation) == 192, "Bank count changed")
    require(Counter(row["kind"] for row in observational) == Counter({"emoji": 55, "symbol": 55}), "Observational balance changed")
    all_items = [*observational, *source, *evaluation]
    require(len({row["codepoint"] for row in all_items}) == 430, "Bank identities overlap")
    require(len({row["alias_label"] for row in all_items}) == 430, "Bank aliases overlap")

    t10_config = yaml.safe_load(
        (root / "configs/semantic_atlas_cross_model_replication_v0.yaml").read_text(encoding="utf-8")
    )
    widths = {
        role: int(t10_config["models"][role]["expected_model_dim"])
        for role in MODEL_ROLES
    }
    summary_receipt_hashes: dict[str, str] = {}
    reconstructed: list[dict[str, Any]] = []
    stored_models_value = read_json(analysis / "model_cell_results.json")
    stored_models = {
        str(row["model_role"]): row for row in stored_models_value["models"]
    }
    require(tuple(stored_models) == MODEL_ROLES, "Stored model order changed")
    endpoint = config["model_primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    seed_base = int(endpoint["seed_base"])
    practical_floor = float(endpoint["practical_minimum"])
    tests = 0
    for role_index, role in enumerate(MODEL_ROLES):
        directory = summary_root / role
        receipt = read_json(directory / "summary_receipt.json")
        require(
            receipt.get("protocol_id") == PROTOCOL_ID
            and receipt.get("model_role") == role,
            f"Summary receipt mismatch: {role}",
        )
        for name, expected in receipt["outputs"].items():
            require(sha256(directory / name) == expected, f"Summary output changed: {role}/{name}")
        summary_receipt_hashes[role] = sha256(directory / "summary_receipt.json")
        tokenizer = read_json(
            root / "validation/t19_lexical_alias_unicode_control_v0/tokenizers" / f"{role}.json"
        )["tokenizer"]
        with np.load(directory / "primary_predictions.npz", allow_pickle=False) as values:
            predictions = {name: np.asarray(values[name]) for name in values.files}
        stored = stored_models[role]
        kinds: dict[str, Any] = {}
        for kind_index, kind in enumerate(KIND_ORDER):
            components: dict[str, Any] = {}
            for component_index, component in enumerate(COMPONENT_ORDER):
                alias = predictions[f"{component}__{kind}__alias"]
                canonical = predictions[f"{component}__{kind}__canonical"]
                codepoint = predictions[f"{component}__{kind}__codepoint"]
                if component == "unrestricted":
                    strata = [list(range(alias.shape[1]))]
                else:
                    strata = tokenizer["primary_exact_strata"]["eligible_local_strata_by_kind"][kind]
                result = randomization_test(
                    alias,
                    codepoint,
                    strata,
                    draws=draws,
                    seed=seed_base + role_index * 100 + kind_index * 10 + component_index,
                )
                tests += 1
                expected = stored["kind_components"][kind][component]
                for actual_value, expected_value, label in (
                    (result["observed"], expected["alias_minus_codepoint_top1"], "effect"),
                    (effect(canonical, codepoint), expected["canonical_minus_codepoint_top1"], "canonical effect"),
                    (result["p_value_one_sided"], expected["randomization"]["p_value_one_sided"], "p value"),
                    (result["null_mean"], expected["randomization"]["null_mean"], "null mean"),
                    (result["null_sd"], expected["randomization"]["null_sd"], "null sd"),
                ):
                    require(
                        math.isclose(float(actual_value), float(expected_value), rel_tol=0.0, abs_tol=1e-15),
                        f"{role}/{kind}/{component} {label} changed",
                    )
                require(
                    result["exceedances"] == int(expected["randomization"]["exceedances"]),
                    f"{role}/{kind}/{component} exceedances changed",
                )
                components[component] = result
            kinds[kind] = components
        emoji = kinds["emoji"]
        iut = max(
            float(emoji["unrestricted"]["p_value_one_sided"]),
            float(emoji["matched"]["p_value_one_sided"]),
        )
        practical = all(
            float(emoji[component]["observed"]) >= practical_floor
            for component in COMPONENT_ORDER
        )
        require(math.isclose(iut, float(stored["model_iut_p"]), rel_tol=0.0, abs_tol=1e-15), f"Model IUT changed: {role}")
        require(practical == bool(stored["practical_pass"]), f"Practical decision changed: {role}")
        reconstructed.append(
            {
                "model_role": role,
                "model_iut_p": iut,
                "practical_pass": practical,
                "model_positive": bool(iut <= float(endpoint["alpha"]) and practical),
            }
        )

    adjusted = holm(reconstructed, float(endpoint["alpha"]))
    for row in reconstructed:
        role = str(row["model_role"])
        stored = stored_models[role]
        require(row["model_positive"] == bool(stored["model_positive"]), f"Model decision changed: {role}")
        require(adjusted[role]["rank"] == int(stored["holm_rank"]), f"Holm rank changed: {role}")
        require(math.isclose(adjusted[role]["threshold"], float(stored["holm_threshold"]), rel_tol=0.0, abs_tol=1e-15), f"Holm threshold changed: {role}")
        require(adjusted[role]["reject"] == bool(stored["holm_reject"]), f"Holm decision changed: {role}")

    core_values = {
        role: float(next(row["model_iut_p"] for row in reconstructed if row["model_role"] == role))
        for role in CORE_ROLES
    }
    partial = partial_conjunction(core_values, int(config["cross_model_primary"]["r"]))
    core_positive = sum(
        bool(row["model_positive"])
        for row in reconstructed
        if row["model_role"] in CORE_ROLES
    )
    cross_positive = bool(
        partial["p_value"] <= float(config["cross_model_primary"]["alpha"])
        and core_positive >= int(config["cross_model_primary"]["r"])
    )
    stored_cross = read_json(analysis / "cross_model_primary_result.json")["cross_model_primary"]
    require(math.isclose(partial["p_value"], float(stored_cross["partial_conjunction_p"]), rel_tol=0.0, abs_tol=1e-15), "Partial-conjunction p changed")
    require(core_positive == int(stored_cross["core_model_positive_count"]), "Core positive count changed")
    require(cross_positive == bool(stored_cross["positive"]), "Cross-model decision changed")

    analysis_receipt = read_json(analysis / "analysis_receipt.json")
    require(analysis_receipt["protocol_id"] == PROTOCOL_ID, "Analysis protocol changed")
    for name, expected in analysis_receipt["outputs"].items():
        require(sha256(analysis / name) == expected, f"Analysis output changed: {name}")
    depth = read_json(analysis / "depth_profiles.json")
    require(len(depth["rows"]) == len(MODEL_ROLES) * DEPTH_COUNT * CARRIER_COUNT * DISTANCE_COUNT * len(KIND_ORDER), "Depth row count changed")

    run_validation: dict[str, Any] = {
        "performed": False,
        "reason": "run_root_not_supplied",
    }
    if run_root is not None:
        run_validation = {
            "performed": True,
            **_validate_runs(run_root, widths, summary_receipt_hashes),
        }
        for role in MODEL_ROLES:
            summary_receipt = read_json(summary_root / role / "summary_receipt.json")
            require(
                summary_receipt["source_role_receipt_sha256"]
                == run_validation["role_receipt_sha256"][role],
                f"Summary/run binding changed: {role}",
            )

    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "independent_validation_pass",
        "selection_manifest_sha256": sha256(selection_path),
        "freeze_manifest_sha256": sha256(freeze_path),
        "summary_receipt_sha256": summary_receipt_hashes,
        "analysis_receipt_sha256": sha256(analysis / "analysis_receipt.json"),
        "analysis_output_sha256": dict(analysis_receipt["outputs"]),
        "run_validation": run_validation,
        "recomputed_randomization_tests": tests,
        "randomization_draws_per_test": draws,
        "partial_conjunction_p": partial["p_value"],
        "core_positive_count": core_positive,
        "positive": cross_positive,
        "causal_go_gate_open": cross_positive,
        "raw_activations_committed_to_git": False,
        "claim_boundary": config["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--summary-root", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = validate(
        args.root.resolve(),
        args.summary_root,
        args.analysis,
        args.run_root,
    )
    require(not args.output.exists(), f"Validation output exists: {args.output}")
    write_json(args.output, value)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
