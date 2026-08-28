#!/usr/bin/env python3
"""Independently validate the compact T10 result and optional raw archive.

This validator deliberately does not import the T10 acquisition/analyzer module.
It reimplements the primary retrieval statistic, randomization components,
intersection-union tests, Holm correction, and partial conjunction from the
frozen YAML contract.  Supplying ``--raw-root`` additionally verifies every
raw shard ledger, activation shape, dtype, and finite-value condition.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-semantic-atlas-cross-model-replication-v0"
CONFIG_PATH = Path("configs/semantic_atlas_cross_model_replication_v0.yaml")
TOKENIZER_RECEIPT_DIRECTORY = Path(
    "validation/semantic_atlas_cross_model_replication_v0/tokenizers"
)
PRIMARY_ENDPOINT = "returned_final_hidden_state"
SECONDARY_ENDPOINT = "raw_last_decoder_block_output"


class ValidationError(RuntimeError):
    """Raised when a bound T10 result invariant does not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_ledger(directory: Path) -> int:
    ledger = directory / "SHA256SUMS"
    require(ledger.is_file(), f"Missing ledger: {ledger}")
    checked = 0
    for raw_line in ledger.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            expected, name = raw_line.split(maxsplit=1)
        except ValueError as exc:
            raise ValidationError(f"Malformed ledger row: {raw_line!r}") from exc
        relative = Path(name.lstrip("*"))
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"Unsafe ledger path: {relative}",
        )
        path = directory / relative
        require(path.is_file(), f"Ledger target missing: {path}")
        require(sha256(path) == expected, f"Ledger digest mismatch: {path}")
        checked += 1
    return checked


def stratified_permutation(
    rng: np.random.Generator,
    item_count: int,
    strata: Sequence[Sequence[int]],
) -> np.ndarray:
    order = np.arange(item_count, dtype=np.int64)
    flattened = sorted(int(value) for group in strata for value in group)
    require(flattened == list(range(item_count)), "Matched strata do not partition items")
    require(all(len(group) >= 2 for group in strata), "Matched stratum is singleton")
    permutation = order.copy()
    for group in strata:
        indices = np.asarray(group, dtype=np.int64)
        permutation[indices] = rng.permutation(indices)
    return permutation


def randomization_component(
    name_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
    *,
    draws: int,
    seed: int,
    practical_minimum: float,
    strata: Sequence[Sequence[int]] | None,
) -> dict[str, Any]:
    require(name_predictions.shape == codepoint_predictions.shape, "Prediction shape mismatch")
    require(
        name_predictions.ndim == 2 and name_predictions.shape[0] == 8,
        "Prediction cell roster mismatch",
    )
    item_count = int(name_predictions.shape[1])
    order = np.arange(item_count, dtype=np.int64)
    name_top1 = np.mean(name_predictions == order[None, :], axis=1)
    codepoint_top1 = np.mean(codepoint_predictions == order[None, :], axis=1)
    contrasts = name_top1 - codepoint_top1
    observed = float(np.min(contrasts))
    rng = np.random.default_rng(seed)
    exceedances = 0
    if strata is not None:
        stratified_permutation(np.random.default_rng(0), item_count, strata)
    for _ in range(draws):
        permutation = (
            rng.permutation(item_count)
            if strata is None
            else stratified_permutation(rng, item_count, strata)
        )
        null_statistic = float(
            np.min(
                np.mean(name_predictions == permutation[None, :], axis=1)
                - codepoint_top1
            )
        )
        exceedances += int(null_statistic >= observed)
    return {
        "item_count": item_count,
        "contrast_by_cell": contrasts.tolist(),
        "observed_minimum_cell_contrast": observed,
        "observed_equal_cell_mean_contrast": float(np.mean(contrasts)),
        "exceedances": exceedances,
        "p_value": float((1 + exceedances) / (draws + 1)),
        "practical_pass": bool(observed >= practical_minimum),
    }


def compare_component(observed: Mapping[str, Any], reported: Mapping[str, Any]) -> None:
    for key in (
        "observed_minimum_cell_contrast",
        "observed_equal_cell_mean_contrast",
        "p_value",
    ):
        require(
            math.isclose(float(observed[key]), float(reported[key]), abs_tol=1e-15),
            f"Recomputed component differs at {key}",
        )
    require(
        int(observed["exceedances"]) == int(reported["exceedances"]),
        "Recomputed exceedance count differs",
    )
    require(
        np.allclose(
            observed["contrast_by_cell"],
            reported["contrast_by_cell"],
            atol=1e-15,
            rtol=0,
        ),
        "Recomputed cell contrasts differ",
    )


def secondary_observed(
    name_predictions: np.ndarray,
    codepoint_predictions: np.ndarray,
) -> dict[str, Any]:
    item_count = int(name_predictions.shape[1])
    order = np.arange(item_count, dtype=np.int64)
    contrasts = np.mean(name_predictions == order[None, :], axis=1) - np.mean(
        codepoint_predictions == order[None, :], axis=1
    )
    return {
        "item_count": item_count,
        "contrast_by_cell": contrasts.tolist(),
        "observed_minimum_cell_contrast": float(np.min(contrasts)),
        "observed_equal_cell_mean_contrast": float(np.mean(contrasts)),
    }


def compare_secondary(observed: Mapping[str, Any], reported: Mapping[str, Any]) -> None:
    require(int(observed["item_count"]) == int(reported["item_count"]), "Secondary item count differs")
    require(
        np.allclose(
            observed["contrast_by_cell"],
            reported["contrast_by_cell"],
            atol=1e-15,
            rtol=0,
        ),
        "Recomputed secondary cell contrasts differ",
    )
    for key in (
        "observed_minimum_cell_contrast",
        "observed_equal_cell_mean_contrast",
    ):
        require(
            math.isclose(float(observed[key]), float(reported[key]), abs_tol=1e-15),
            f"Recomputed secondary differs at {key}",
        )


def holm_adjust(raw: Mapping[str, float], alpha: float) -> dict[str, dict[str, Any]]:
    ordered = sorted(raw, key=lambda key: (float(raw[key]), key))
    count = len(ordered)
    running = 0.0
    rejected_prefix = True
    result: dict[str, dict[str, Any]] = {}
    for index, role in enumerate(ordered):
        adjusted = max(running, min(1.0, (count - index) * float(raw[role])))
        running = adjusted
        reject = rejected_prefix and float(raw[role]) <= alpha / (count - index)
        rejected_prefix = reject
        result[role] = {"adjusted_p": adjusted, "reject": reject}
    return result


def validate_raw_archive(raw_root: Path, roles: Sequence[str]) -> dict[str, Any]:
    checked_ledger_files = 0
    shard_count = 0
    activation_bytes = 0
    for role in roles:
        run_directory = raw_root / role
        checked_ledger_files += check_ledger(run_directory)
        index = read_json(run_directory / "SHARD_INDEX.json")
        require(index["model_role"] == role, f"Raw shard-index role mismatch: {role}")
        for shard_name, ledger_sha256 in index["shards"].items():
            shard_directory = run_directory / shard_name
            require(
                sha256(shard_directory / "SHA256SUMS") == ledger_sha256,
                f"Raw shard ledger binding mismatch: {role}/{shard_name}",
            )
            checked_ledger_files += check_ledger(shard_directory)
            receipt = read_json(shard_directory / "shard_receipt.json")
            activation_path = shard_directory / "activations.npy"
            activations = np.load(activation_path, mmap_mode="r", allow_pickle=False)
            require(
                list(activations.shape) == receipt["activation_shape"],
                f"Raw activation shape mismatch: {role}/{shard_name}",
            )
            require(str(activations.dtype) == "float32", "Raw activation dtype changed")
            require(bool(np.isfinite(activations).all()), "Raw activation contains nonfinite values")
            activation_bytes += activation_path.stat().st_size
            shard_count += 1
    return {
        "provided": True,
        "status": "pass",
        "model_cells": len(roles),
        "shards": shard_count,
        "ledger_targets_rehashed": checked_ledger_files,
        "activation_bytes": activation_bytes,
        "activation_dtype": "float32",
        "all_activation_values_finite": True,
    }


def validate(bundle: Path, raw_root: Path | None) -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((repository / CONFIG_PATH).read_text(encoding="utf-8"))
    require(config["protocol_id"] == PROTOCOL_ID, "Protocol config changed")
    roles = [str(value) for value in config["models"]["order"]]
    analysis_directory = bundle / "analysis"
    summaries_directory = bundle / "summaries"
    runs_directory = bundle / "runs"
    analysis_ledger_files = check_ledger(analysis_directory)
    reported = read_json(analysis_directory / "model_cell_results.json")
    cross_reported = read_json(analysis_directory / "cross_model_primary_result.json")
    analysis_receipt = read_json(analysis_directory / "analysis_receipt.json")
    freeze_sha256 = sha256(
        repository / "data/manifests/semantic_atlas_cross_model_replication_v0.json"
    )
    require(
        analysis_receipt["freeze_manifest_sha256"] == freeze_sha256,
        "Analysis freeze binding differs",
    )

    summary_ledger_files = 0
    run_ledger_files = 0
    total_forwards = 0
    total_vectors = 0
    total_shards = 0
    model_results: dict[str, Any] = {}
    draws = int(config["model_primary_endpoint"]["randomization_draws"])
    seed_base = int(config["model_primary_endpoint"]["seed_base"])
    practical_minimum = float(config["model_primary_endpoint"]["practical_minimum"])
    for role_index, role in enumerate(roles):
        run_directory = runs_directory / role
        summary_directory = summaries_directory / role
        run_ledger_files += check_ledger(run_directory)
        summary_ledger_files += check_ledger(summary_directory)
        run_receipt = read_json(run_directory / "run_receipt.json")
        summary_receipt = read_json(summary_directory / "summary_receipt.json")
        require(run_receipt["status"] == "pass", f"Run status changed: {role}")
        require(summary_receipt["status"] == "pass", f"Summary status changed: {role}")
        require(
            summary_receipt["source_run_receipt_sha256"]
            == sha256(run_directory / "run_receipt.json"),
            f"Summary/run binding differs: {role}",
        )
        require(
            analysis_receipt["input_summary_receipt_sha256"][role]
            == sha256(summary_directory / "summary_receipt.json"),
            f"Analysis/summary binding differs: {role}",
        )
        require(
            run_receipt["freeze_manifest_sha256"] == freeze_sha256
            and summary_receipt["freeze_manifest_sha256"] == freeze_sha256,
            f"Freeze binding differs: {role}",
        )
        total_forwards += int(run_receipt["model_forward_calls"])
        total_vectors += int(run_receipt["readout_vectors"])
        total_shards += int(run_receipt["shard_count"])

        token_receipt = read_json(
            repository / TOKENIZER_RECEIPT_DIRECTORY / f"{role}.json"
        )["tokenizer"]["exact_triple_strata"]
        strata = token_receipt["eligible_local_strata"]
        with np.load(summary_directory / "predictions.npz", allow_pickle=False) as stored:
            predictions = {key: np.asarray(stored[key]) for key in stored.files}
        unrestricted = randomization_component(
            predictions[f"{PRIMARY_ENDPOINT}__unrestricted__name"],
            predictions[f"{PRIMARY_ENDPOINT}__unrestricted__codepoint"],
            draws=draws,
            seed=seed_base + role_index * 10 + 1,
            practical_minimum=practical_minimum,
            strata=None,
        )
        matched = randomization_component(
            predictions[f"{PRIMARY_ENDPOINT}__matched__name"],
            predictions[f"{PRIMARY_ENDPOINT}__matched__codepoint"],
            draws=draws,
            seed=seed_base + role_index * 10 + 2,
            practical_minimum=practical_minimum,
            strata=strata,
        )
        compare_component(unrestricted, reported[role]["unrestricted_component"])
        compare_component(matched, reported[role]["tokenization_matched_component"])
        for component in ("unrestricted", "matched"):
            secondary = secondary_observed(
                predictions[f"{SECONDARY_ENDPOINT}__{component}__name"],
                predictions[f"{SECONDARY_ENDPOINT}__{component}__codepoint"],
            )
            compare_secondary(
                secondary,
                reported[role]["secondary_raw_last_block"][component],
            )
        iut_p = max(float(unrestricted["p_value"]), float(matched["p_value"]))
        practical_pass = bool(
            unrestricted["practical_pass"] and matched["practical_pass"]
        )
        require(
            math.isclose(iut_p, reported[role]["intersection_union_p_value"], abs_tol=1e-15),
            f"IUT p-value differs: {role}",
        )
        require(practical_pass == reported[role]["practical_pass"], f"Practical result differs: {role}")
        model_results[role] = {
            "unrestricted_minimum_contrast": unrestricted[
                "observed_minimum_cell_contrast"
            ],
            "tokenization_matched_minimum_contrast": matched[
                "observed_minimum_cell_contrast"
            ],
            "unrestricted_p_value": unrestricted["p_value"],
            "tokenization_matched_p_value": matched["p_value"],
            "intersection_union_p_value": iut_p,
            "matched_item_count": int(token_receipt["eligible_item_count"]),
            "practical_pass": practical_pass,
        }

    raw_iut = {
        role: float(model_results[role]["intersection_union_p_value"])
        for role in roles
    }
    holm = holm_adjust(
        raw_iut,
        float(config["bounded_model_cell_family"]["familywise_alpha"]),
    )
    bounded_pass_roles: list[str] = []
    for role in roles:
        require(
            math.isclose(
                holm[role]["adjusted_p"],
                reported[role]["holm_adjusted_p"],
                abs_tol=1e-15,
            ),
            f"Holm p-value differs: {role}",
        )
        require(holm[role]["reject"] == reported[role]["holm_reject"], f"Holm decision differs: {role}")
        bounded_pass = bool(holm[role]["reject"] and model_results[role]["practical_pass"])
        require(
            bounded_pass == reported[role]["bounded_model_cell_claim_pass"],
            f"Bounded cell result differs: {role}",
        )
        model_results[role]["holm_adjusted_p"] = holm[role]["adjusted_p"]
        model_results[role]["bounded_model_cell_claim_pass"] = bounded_pass
        if bounded_pass:
            bounded_pass_roles.append(role)

    core = [str(value) for value in config["cross_model_primary"]["core_order"]]
    rank = int(config["cross_model_primary"]["r"])
    ordered_core = sorted((raw_iut[role], role) for role in core)
    partial_p = min(1.0, (len(core) - rank + 1) * ordered_core[rank - 1][0])
    core_practical_pass_count = sum(
        int(model_results[role]["practical_pass"]) for role in core
    )
    statistical_pass = partial_p <= float(config["cross_model_primary"]["alpha"])
    practical_pass = core_practical_pass_count >= rank
    positive = bool(statistical_pass and practical_pass)
    require(math.isclose(partial_p, cross_reported["p_value"], abs_tol=1e-15), "Partial-conjunction p-value differs")
    require(core_practical_pass_count == cross_reported["core_practical_pass_count"], "Core practical count differs")
    require(positive == cross_reported["positive"], "Cross-model primary decision differs")

    raw_validation = (
        validate_raw_archive(raw_root, roles)
        if raw_root is not None
        else {"provided": False, "status": "not_checked"}
    )
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "validation_role": "independent_reimplementation_and_evidence_integrity_check",
        "freeze_manifest_sha256": freeze_sha256,
        "compact_bundle": {
            "analysis_ledger_targets_rehashed": analysis_ledger_files,
            "summary_ledger_targets_rehashed": summary_ledger_files,
            "run_ledger_targets_rehashed": run_ledger_files,
            "model_cells": len(roles),
            "total_model_forward_calls": total_forwards,
            "total_readout_vectors": total_vectors,
            "total_shards": total_shards,
        },
        "raw_archive": raw_validation,
        "model_results": model_results,
        "cross_model_primary": {
            "partial_conjunction_p_value": partial_p,
            "statistical_pass": statistical_pass,
            "core_practical_pass_count": core_practical_pass_count,
            "practical_pass": practical_pass,
            "positive": positive,
            "authorized_wording": cross_reported["authorized_wording"],
        },
        "bounded_model_cell_pass_roles": bounded_pass_roles,
        "claim_boundary": {
            "semantic_claim_authorized": False,
            "causal_claim_authorized": False,
            "scale_law_claim_authorized": False,
            "model_general_claim_authorized": False,
            "independent_replication_claim_authorized": False,
            "phase_i_gate_closed": False,
        },
        "model_forward_calls_during_validation": 0,
        "intervention_calls": 0,
        "generation_calls": 0,
        "share_readiness": "ready_with_registered_negative_primary_and_claim_boundary",
    }


def write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    require(not path.exists(), f"Output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.bundle.resolve(), args.raw_root.resolve() if args.raw_root else None)
    if args.output:
        write_json_once(args.output.resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
