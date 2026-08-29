#!/usr/bin/env python3
"""Independently validate and package the T12 reserve confirmation result.

This module deliberately does not import the acquisition or analysis module.  It
reconstructs the registered statistics from the stored item-level contrasts,
checks the preflight and acquisition receipts, and can seal a compact public
bundle that omits raw activations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


SCHEMA_VERSION = 1
PROTOCOL_ID = "glyphprobe-glyph-system-reserve-confirmation-v0"
FREEZE_COMMIT = "ab64488dc4bd28510c353f4370cda5546bb34750"
EXPECTED_FREEZE_MANIFEST_SHA256 = (
    "38046552a26bef0eb6cdab3222f58041707616028fe89c0eb5104a84f0943738"
)
EXPECTED_RUNTIME_PREFLIGHT_SHA256 = (
    "3a51837c6c6a149b88e05db2528b5ebd2437d50c89e8ffdcfaaee1a343bc8ee1"
)
EXPECTED_PRIMARY_RESULT_SHA256 = (
    "1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6"
)
MODEL_ORDER = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
    "qwen25_0p5b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "qwen25_3b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
ELEMENTARY_ORDER = (
    "zwj_presentation_or_fusion",
    "regional_presentation_or_fusion",
    "regional_component_tracking",
)
CONTROL_ORDER = ("required", "strict_prefix_sensitivity")
SYSTEM_T12_INDICES = {
    "zwj": tuple(range(0, 96)),
    "regional_flag": tuple(range(96, 160)),
}
ANALYSIS_FILES = (
    "cell_item_contrasts.jsonl",
    "primary_result.json",
    "analysis_receipt.json",
)
PREFLIGHT_FILES = tuple(f"{role}.json" for role in MODEL_ORDER) + ("aggregate.json",)
RUN_FILES = ("run_receipt.json", "SHARD_INDEX.json")
VALIDATION_FILES = ("independent_validation.json", "report.md")
FLOAT_ATOL = 1e-12


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_ledger(directory: Path) -> dict[str, str]:
    ledger = directory / "SHA256SUMS"
    require(ledger.is_file(), f"Missing ledger: {ledger}")
    entries: dict[str, str] = {}
    for raw_line in ledger.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        digest, separator, relative = raw_line.partition("  ")
        require(separator == "  ", f"Malformed ledger row: {raw_line!r}")
        path = Path(relative)
        require(
            not path.is_absolute() and ".." not in path.parts,
            f"Unsafe ledger path: {relative}",
        )
        require(relative not in entries, f"Duplicate ledger path: {relative}")
        require(
            len(digest) == 64 and all(char in "0123456789abcdef" for char in digest),
            f"Malformed SHA-256: {digest}",
        )
        entries[relative] = digest
    return entries


def validate_ledger(
    directory: Path,
    expected: Sequence[str] | None = None,
) -> dict[str, str]:
    entries = parse_ledger(directory)
    if expected is not None:
        require(set(entries) == set(expected), f"Ledger payload changed: {directory}")
    for relative, expected_digest in entries.items():
        path = directory / relative
        require(path.is_file(), f"Ledger file missing: {path}")
        require(sha256(path) == expected_digest, f"Hash mismatch: {path}")
    return entries


def write_ledger(directory: Path, relative_paths: Sequence[str]) -> None:
    lines = [f"{sha256(directory / name)}  {name}\n" for name in relative_paths]
    (directory / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def require_float_equal(actual: float, expected: float, label: str) -> None:
    require(
        bool(np.isclose(actual, expected, rtol=0.0, atol=FLOAT_ATOL)),
        f"{label} changed: {actual!r} != {expected!r}",
    )


def descriptive_summary(values: np.ndarray) -> dict[str, Any]:
    require(values.ndim == 3, "Contrast tensor rank changed")
    require(values.shape[:2] == (9, 8), "Contrast cell grid changed")
    cell_medians = np.nanmedian(values, axis=2)
    require(bool(np.isfinite(cell_medians).all()), "Nonfinite cell median")
    model_medians = np.median(cell_medians, axis=1)
    return {
        "global_statistic": float(np.median(cell_medians)),
        "cell_medians": cell_medians,
        "model_context_medians": model_medians,
        "positive_cell_count": int(np.sum(cell_medians > 0.0)),
        "positive_model_count": int(np.sum(model_medians > 0.0)),
        "minimum_cell_median": float(np.min(cell_medians)),
        "maximum_cell_median": float(np.max(cell_medians)),
    }


def shared_item_swap_randomization_test(
    values: np.ndarray,
    *,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    summary = descriptive_summary(values)
    observed = float(summary["global_statistic"])
    rng = np.random.default_rng(seed)
    null_statistics = np.empty(draws, dtype=np.float64)
    exceedances = 0
    written = 0
    while written < draws:
        count = min(256, draws - written)
        signs = (
            rng.integers(0, 2, size=(count, values.shape[2]), dtype=np.int8) * 2 - 1
        ).astype(np.float64)
        signed = values[None, :, :, :] * signs[:, None, None, :]
        cell_medians = np.nanmedian(signed, axis=3)
        statistics = np.median(cell_medians, axis=(1, 2))
        null_statistics[written : written + count] = statistics
        exceedances += int(np.sum(statistics >= observed))
        written += count
    return {
        **summary,
        "randomization_draws": draws,
        "randomization_seed": seed,
        "exceedances": exceedances,
        "p_value": float((1 + exceedances) / (draws + 1)),
        "null_statistic_quantiles": {
            str(quantile): float(np.quantile(null_statistics, quantile))
            for quantile in (0.0, 0.5, 0.95, 0.975, 0.99, 1.0)
        },
    }


def holm_correction(
    p_values: Mapping[str, float],
    *,
    alpha: float,
    hypothesis_order: Sequence[str],
) -> dict[str, Any]:
    require(set(p_values) == set(hypothesis_order), "Holm family changed")
    position = {name: index for index, name in enumerate(hypothesis_order)}
    ordered = sorted(p_values, key=lambda name: (p_values[name], position[name]))
    count = len(ordered)
    adjusted: dict[str, float] = {}
    rejected: dict[str, bool] = {name: False for name in ordered}
    rows: list[dict[str, Any]] = []
    running = 0.0
    still_rejecting = True
    for zero_rank, name in enumerate(ordered):
        multiplier = count - zero_rank
        running = max(running, min(1.0, multiplier * float(p_values[name])))
        threshold = alpha / multiplier
        reject = bool(still_rejecting and p_values[name] <= threshold)
        rejected[name] = reject
        if not reject:
            still_rejecting = False
        adjusted[name] = running
        rows.append(
            {
                "rank": zero_rank + 1,
                "hypothesis": name,
                "raw_p_value": float(p_values[name]),
                "holm_threshold": threshold,
                "holm_adjusted_p_value": running,
                "rejected": reject,
            }
        )
    return {
        "method": "holm",
        "familywise_alpha": alpha,
        "family_size": count,
        "ordered_tests": rows,
        "adjusted_p_values": adjusted,
        "rejected": rejected,
    }


def compare_summary(
    recomputed: Mapping[str, Any],
    stored: Mapping[str, Any],
    label: str,
) -> None:
    scalar_fields = (
        "global_statistic",
        "minimum_cell_median",
        "maximum_cell_median",
    )
    integer_fields = ("positive_cell_count", "positive_model_count")
    for field in scalar_fields:
        require_float_equal(
            float(recomputed[field]),
            float(stored[field]),
            f"{label}.{field}",
        )
    for field in integer_fields:
        require(
            int(recomputed[field]) == int(stored[field]),
            f"{label}.{field} changed",
        )
    require(
        bool(
            np.allclose(
                np.asarray(recomputed["cell_medians"]),
                np.asarray(stored["cell_medians"]),
                rtol=0.0,
                atol=FLOAT_ATOL,
            )
        ),
        f"{label}.cell_medians changed",
    )
    require(
        bool(
            np.allclose(
                np.asarray(recomputed["model_context_medians"]),
                np.asarray(stored["model_context_medians"]),
                rtol=0.0,
                atol=FLOAT_ATOL,
            )
        ),
        f"{label}.model_context_medians changed",
    )


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(all(isinstance(row, dict) for row in rows), "Non-object analysis row")
    return rows


def reconstruct_tensors(
    rows: Sequence[Mapping[str, Any]],
    elementary_specs: Mapping[str, Any],
) -> dict[str, dict[str, np.ndarray]]:
    tensors: dict[str, dict[str, np.ndarray]] = {}
    expected_keys: set[tuple[str, str, int, int]] = set()
    for elementary in ELEMENTARY_ORDER:
        system = str(elementary_specs[elementary]["system"])
        size = len(SYSTEM_T12_INDICES[system])
        tensors[elementary] = {
            control: np.full((9, 8, size), np.nan, dtype=np.float64)
            for control in CONTROL_ORDER
        }
        for control in CONTROL_ORDER:
            for model_index in range(9):
                for context_index in range(8):
                    expected_keys.add((elementary, control, model_index, context_index))

    observed_keys: set[tuple[str, str, int, int]] = set()
    for row in rows:
        elementary = str(row["elementary_test"])
        control = str(row["control"])
        model_index = int(row["model_index"])
        context_index = int(row["context_index"])
        key = (elementary, control, model_index, context_index)
        require(key in expected_keys, f"Unexpected analysis row: {key}")
        require(key not in observed_keys, f"Duplicate analysis row: {key}")
        observed_keys.add(key)
        require(
            row["model_role"] == MODEL_ORDER[model_index],
            f"Model order changed: {key}",
        )
        system = str(elementary_specs[elementary]["system"])
        require(row["system"] == system, f"System changed: {key}")
        indices = [int(value) for value in row["eligible_t12_indices"]]
        values = np.asarray(row["item_contrasts"], dtype=np.float64)
        require(len(indices) == len(values), f"Item/value count changed: {key}")
        require(
            len(indices) == int(row["eligible_item_count"]),
            f"Eligible count changed: {key}",
        )
        require(indices == sorted(set(indices)), f"Eligible item order changed: {key}")
        global_indices = SYSTEM_T12_INDICES[system]
        offset = global_indices[0]
        require(
            all(index in global_indices for index in indices),
            f"Cross-system T12 index: {key}",
        )
        tensor = tensors[elementary][control]
        tensor[model_index, context_index, np.asarray(indices) - offset] = values
        require_float_equal(
            float(np.median(values)),
            float(row["cell_median"]),
            f"stored cell median {key}",
        )
    require(observed_keys == expected_keys, "Analysis row grid is incomplete")
    return tensors


def recompute_gate(
    required: Mapping[str, Any],
    strict: Mapping[str, Any],
    practical_floor: float,
) -> dict[str, Any]:
    model_medians = np.asarray(required["model_context_medians"], dtype=np.float64)
    strict_model_medians = np.asarray(strict["model_context_medians"], dtype=np.float64)
    supporting = int(np.sum(model_medians >= practical_floor))
    opposed = int(np.sum(model_medians <= -practical_floor))
    strict_supporting = int(np.sum(strict_model_medians > 0.0))
    checks = {
        "global_practical_floor": bool(
            float(required["global_statistic"]) >= practical_floor
        ),
        "minimum_supporting_models": supporting >= 6,
        "maximum_materially_opposed_models": opposed <= 1,
        "strict_prefix_global_positive": bool(float(strict["global_statistic"]) > 0.0),
        "strict_prefix_minimum_positive_models": strict_supporting >= 6,
    }
    return {
        "all_nonmultiplicity_gates_pass": bool(all(checks.values())),
        "checks": checks,
        "practical_floor": practical_floor,
        "supporting_model_count": supporting,
        "materially_opposed_model_count": opposed,
        "strict_prefix_positive_model_count": strict_supporting,
    }


def validate_receipts(
    analysis: Path,
    preflight: Path,
    runs_root: Path,
    freeze_manifest: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    require(
        sha256(freeze_manifest) == EXPECTED_FREEZE_MANIFEST_SHA256,
        "Freeze manifest hash changed",
    )
    freeze = read_json(freeze_manifest)
    require(freeze["protocol_id"] == PROTOCOL_ID, "Freeze protocol changed")
    require(tuple(freeze["model_order"]) == MODEL_ORDER, "Freeze model order changed")
    validate_ledger(analysis, ANALYSIS_FILES)
    validate_ledger(preflight, PREFLIGHT_FILES)
    require(
        sha256(preflight / "aggregate.json") == EXPECTED_RUNTIME_PREFLIGHT_SHA256,
        "Runtime preflight aggregate hash changed",
    )
    aggregate = read_json(preflight / "aggregate.json")
    require(aggregate["protocol_id"] == PROTOCOL_ID, "Preflight protocol changed")
    require(tuple(aggregate["model_order"]) == MODEL_ORDER, "Preflight roster changed")
    require(aggregate["model_weights_loaded"] is False, "Preflight loaded weights")
    require(
        int(aggregate["reserve_model_forward_calls"]) == 0,
        "Preflight forwarded reserve",
    )

    analysis_receipt = read_json(analysis / "analysis_receipt.json")
    primary = read_json(analysis / "primary_result.json")
    require(primary["protocol_id"] == PROTOCOL_ID, "Primary protocol changed")
    require(primary["status"] == "pass", "Primary status changed")
    require(tuple(primary["model_order"]) == MODEL_ORDER, "Primary roster changed")
    require(
        sha256(analysis / "primary_result.json") == EXPECTED_PRIMARY_RESULT_SHA256,
        "Primary result hash changed",
    )
    require(
        analysis_receipt["primary_result_sha256"] == EXPECTED_PRIMARY_RESULT_SHA256,
        "Analysis receipt primary binding changed",
    )
    require(
        analysis_receipt["freeze_manifest_sha256"] == EXPECTED_FREEZE_MANIFEST_SHA256,
        "Analysis receipt freeze binding changed",
    )
    require(
        analysis_receipt["runtime_preflight_aggregate_sha256"]
        == EXPECTED_RUNTIME_PREFLIGHT_SHA256,
        "Analysis receipt preflight binding changed",
    )

    total_forwards = 0
    total_vectors = 0
    for role in MODEL_ORDER:
        run_root = runs_root / role
        validate_ledger(run_root, RUN_FILES)
        receipt = read_json(run_root / "run_receipt.json")
        shard_index = read_json(run_root / "SHARD_INDEX.json")
        require(receipt["protocol_id"] == PROTOCOL_ID, f"Run protocol changed: {role}")
        require(receipt["model_role"] == role, f"Run role changed: {role}")
        require(receipt["status"] == "pass", f"Run did not pass: {role}")
        require(
            int(receipt["reserve_items_forwarded"]) == 160, f"Run items changed: {role}"
        )
        require(
            int(receipt["model_forward_calls"]) == 1088, f"Run forwards changed: {role}"
        )
        require(int(receipt["readout_vectors"]) == 4352, f"Run vectors changed: {role}")
        require(int(receipt["generation_calls"]) == 0, f"Generation occurred: {role}")
        require(
            int(receipt["intervention_calls"]) == 0, f"Intervention occurred: {role}"
        )
        require(
            receipt["raw_activations_committed_to_git"] is False,
            f"Raw activation Git flag changed: {role}",
        )
        require(
            receipt["raw_activations_put_on_spiralshare"] is False,
            f"Raw activation share flag changed: {role}",
        )
        require(
            receipt["freeze_manifest_sha256"] == EXPECTED_FREEZE_MANIFEST_SHA256,
            f"Run freeze binding changed: {role}",
        )
        require(
            receipt["runtime_preflight_aggregate_sha256"]
            == EXPECTED_RUNTIME_PREFLIGHT_SHA256,
            f"Run preflight binding changed: {role}",
        )
        require(
            sha256(preflight / f"{role}.json") == receipt["tokenizer_receipt_sha256"],
            f"Tokenizer receipt binding changed: {role}",
        )
        require(shard_index["model_role"] == role, f"Shard role changed: {role}")
        require(
            shard_index["shards"] == receipt["shard_ledger_sha256"],
            f"Shard ledger binding changed: {role}",
        )
        require(len(shard_index["shards"]) == 10, f"Shard count changed: {role}")
        require(
            sha256(run_root / "run_receipt.json")
            == analysis_receipt["input_run_receipt_sha256"][role],
            f"Analysis run binding changed: {role}",
        )
        total_forwards += int(receipt["model_forward_calls"])
        total_vectors += int(receipt["readout_vectors"])
    require(total_forwards == 9792, "Joint forward total changed")
    require(total_vectors == 39168, "Joint vector total changed")
    require(
        int(analysis_receipt["acquisition_model_forward_calls"]) == total_forwards,
        "Analysis receipt forward total changed",
    )
    return freeze, primary, analysis_receipt


def validate_result(
    analysis: Path,
    preflight: Path,
    runs_root: Path,
    freeze_manifest: Path,
    output: Path,
) -> dict[str, Any]:
    require(not output.exists(), f"Output already exists: {output}")
    freeze, primary, analysis_receipt = validate_receipts(
        analysis, preflight, runs_root, freeze_manifest
    )
    rows = load_rows(analysis / "cell_item_contrasts.jsonl")
    require(len(rows) == 432, "Stored item-contrast row count changed")
    elementary_specs = freeze["hypothesis_family"]["elementary_tests"]
    require(set(elementary_specs) == set(ELEMENTARY_ORDER), "Elementary family changed")
    tensors = reconstruct_tensors(rows, elementary_specs)

    recomputed_required: dict[str, dict[str, Any]] = {}
    recomputed_strict: dict[str, dict[str, Any]] = {}
    recomputed_gates: dict[str, dict[str, Any]] = {}
    for elementary in ELEMENTARY_ORDER:
        specification = elementary_specs[elementary]
        required_result = shared_item_swap_randomization_test(
            tensors[elementary]["required"],
            draws=int(freeze["hypothesis_family"]["randomization_draws"]),
            seed=int(specification["randomization_seed"]),
        )
        strict_result = descriptive_summary(
            tensors[elementary]["strict_prefix_sensitivity"]
        )
        gate = recompute_gate(
            required_result,
            strict_result,
            float(specification["practical_floor"]),
        )
        stored = primary["elementary_results"][elementary]
        compare_summary(required_result, stored["required_control"], elementary)
        compare_summary(
            strict_result,
            stored["strict_prefix_sensitivity"],
            f"{elementary}.strict",
        )
        require(
            int(required_result["exceedances"])
            == int(stored["required_control"]["exceedances"]),
            f"{elementary} exceedances changed",
        )
        require_float_equal(
            float(required_result["p_value"]),
            float(stored["required_control"]["p_value"]),
            f"{elementary}.p_value",
        )
        for quantile, value in required_result["null_statistic_quantiles"].items():
            require_float_equal(
                float(value),
                float(stored["required_control"]["null_statistic_quantiles"][quantile]),
                f"{elementary}.null_quantile.{quantile}",
            )
        require(gate == stored["gate"], f"{elementary} gate changed")
        recomputed_required[elementary] = required_result
        recomputed_strict[elementary] = strict_result
        recomputed_gates[elementary] = gate

    p_values = {
        "H_ZWJ_FUSION": recomputed_required["zwj_presentation_or_fusion"]["p_value"],
        "H_REGIONAL_DUAL": max(
            recomputed_required["regional_presentation_or_fusion"]["p_value"],
            recomputed_required["regional_component_tracking"]["p_value"],
        ),
    }
    hypothesis_order = tuple(freeze["hypothesis_family"]["registered_hypothesis_order"])
    holm = holm_correction(
        p_values,
        alpha=float(freeze["hypothesis_family"]["familywise_alpha"]),
        hypothesis_order=hypothesis_order,
    )
    require(holm == primary["holm"], "Holm result changed")
    confirmed: list[str] = []
    for hypothesis in hypothesis_order:
        components = freeze["hypothesis_family"]["registered_hypotheses"][hypothesis][
            "required_elementary_tests"
        ]
        is_confirmed = bool(
            holm["rejected"][hypothesis]
            and all(
                recomputed_gates[component]["all_nonmultiplicity_gates_pass"]
                for component in components
            )
        )
        require(
            is_confirmed == primary["hypothesis_results"][hypothesis]["confirmed"],
            f"Confirmation status changed: {hypothesis}",
        )
        if is_confirmed:
            confirmed.append(hypothesis)
    require(confirmed == primary["confirmed_hypotheses"], "Confirmed family changed")
    require(not confirmed, "Unexpected T12 confirmation")
    require(
        primary["outcome_pattern"] == "neither_registered_hypothesis_confirmed",
        "T12 outcome pattern changed",
    )

    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "pass",
        "overall_assessment": "share_with_caveats",
        "outcome_pattern": primary["outcome_pattern"],
        "confirmed_hypotheses": confirmed,
        "independent_recomputations": {
            "stored_item_contrast_rows": {"recomputed": 432, "mismatches": 0},
            "stored_cell_medians": {"recomputed": 432, "mismatches": 0},
            "shared_item_swap_randomization_tests": {
                "recomputed": 3,
                "draws_each": 49999,
                "mismatches": 0,
            },
            "practical_and_heterogeneity_gates": {
                "recomputed": 3,
                "mismatches": 0,
            },
            "registered_hypotheses_and_holm": {
                "recomputed": 2,
                "mismatches": 0,
            },
            "raw_activation_to_item_contrast_derivation": {
                "recomputed": False,
                "reason": "Raw FP32 activations are intentionally omitted from the compact public evidence.",
            },
        },
        "input_bindings": {
            "freeze_commit": FREEZE_COMMIT,
            "freeze_manifest_sha256": sha256(freeze_manifest),
            "runtime_preflight_aggregate_sha256": sha256(preflight / "aggregate.json"),
            "analysis_sha256sums_sha256": sha256(analysis / "SHA256SUMS"),
            "primary_result_sha256": sha256(analysis / "primary_result.json"),
            "run_receipt_sha256": analysis_receipt["input_run_receipt_sha256"],
        },
        "acquisition": {
            "reserve_items": 160,
            "models": 9,
            "contexts_per_model": 8,
            "model_forward_calls": 9792,
            "readout_vectors": 39168,
            "intervention_calls": 0,
            "generation_calls": 0,
        },
        "claim_boundary": primary["claim_boundary"],
        "semantic_claim_authorized": False,
        "causal_claim_authorized": False,
        "behavioral_steering_claim_authorized": False,
        "model_general_claim_authorized": False,
        "t10_primary_changed": False,
    }
    output.mkdir(parents=True)
    write_json(output / "independent_validation.json", result)
    report = "\n".join(
        (
            "# T12 independent validation report",
            "",
            "Status: **PASS with caveats**.",
            "",
            "The validator did not import the T12 acquisition/analyzer module. It rehashed the frozen manifest, runtime preflight, nine run receipts, nine shard indexes, and joint analysis. It independently reconstructed 432 stored cell medians, reran all three 49,999-draw shared-item swap tests, and recomputed the practical-floor, model-heterogeneity, strict-prefix, intersection-union, and Holm decisions with zero mismatches.",
            "",
            "Neither registered hypothesis was confirmed. The compact inputs omit raw FP32 activations, so the activation-to-item-contrast derivation was hash-bound but not independently recomputed. This is validation of the stored inferential path, not independent model replication.",
            "",
        )
    )
    (output / "report.md").write_text(report, encoding="utf-8")
    write_ledger(output, VALIDATION_FILES)
    return result


def payload_inventory(root: Path) -> list[dict[str, Any]]:
    excluded = {"PUBLIC_MANIFEST.json", "SHA256SUMS"}
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(path for path in root.rglob("*") if path.is_file())
        if path.relative_to(root).as_posix() not in excluded
    ]


def seal_public_bundle(
    source: Path,
    validation: Path,
    readme: Path,
    readme_ja: Path,
    freeze_manifest: Path,
    config: Path,
    design_preflight: Path,
    output: Path,
) -> dict[str, Any]:
    require(not output.exists(), f"Output already exists: {output}")
    require(readme.is_file() and readme_ja.is_file(), "Bilingual README missing")
    validate_receipts(
        source / "analysis",
        source / "preflight",
        source / "runs",
        freeze_manifest,
    )
    validate_ledger(validation, VALIDATION_FILES)
    independent = read_json(validation / "independent_validation.json")
    require(independent["status"] == "pass", "Independent validation failed")

    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        shutil.copyfile(readme, stage / "README.md")
        shutil.copyfile(readme_ja, stage / "README.ja.md")
        for name in ("analysis", "preflight", "runs"):
            shutil.copytree(source / name, stage / name)
        shutil.copytree(validation, stage / "validation")
        freeze_root = stage / "freeze"
        freeze_root.mkdir()
        shutil.copyfile(freeze_manifest, freeze_root / "manifest.json")
        shutil.copyfile(config, freeze_root / "config.yaml")
        shutil.copyfile(design_preflight, freeze_root / "design_preflight.json")
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "bundle_role": "compact_one_shot_confirmation_result_evidence",
            "freeze_commit": FREEZE_COMMIT,
            "freeze_manifest_sha256": EXPECTED_FREEZE_MANIFEST_SHA256,
            "runtime_preflight_aggregate_sha256": EXPECTED_RUNTIME_PREFLIGHT_SHA256,
            "primary_result_sha256": EXPECTED_PRIMARY_RESULT_SHA256,
            "outcome_pattern": "neither_registered_hypothesis_confirmed",
            "confirmed_hypotheses": [],
            "included_payload": payload_inventory(stage),
            "omitted_payload": {
                "raw_fp32_activations": {
                    "included": False,
                    "reason": "Raw activations stay in the furnace research archive and are not committed or placed on SpiralShare.",
                },
                "per_shard_observations_and_intents": {
                    "included": False,
                    "reason": "The nine run receipts and shard-ledger hashes bind the omitted acquisition payload.",
                },
                "model_artifacts": {
                    "included": False,
                    "reason": "Pinned revisions and artifact manifests are recorded in preflight and run receipts.",
                },
            },
            "independent_validation": {
                "status": independent["status"],
                "overall_assessment": independent["overall_assessment"],
                "recomputations": independent["independent_recomputations"],
            },
            "claim_boundary": independent["claim_boundary"],
            "semantic_claim_authorized": False,
            "causal_claim_authorized": False,
            "behavioral_steering_claim_authorized": False,
            "model_general_claim_authorized": False,
            "t10_primary_changed": False,
        }
        write_json(stage / "PUBLIC_MANIFEST.json", manifest)
        root_files = tuple(
            path.relative_to(stage).as_posix()
            for path in sorted(path for path in stage.rglob("*") if path.is_file())
        )
        write_ledger(stage, root_files)
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return validate_public_bundle(output)


def validate_public_bundle(bundle: Path) -> dict[str, Any]:
    entries = validate_ledger(bundle)
    actual = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file() and path.relative_to(bundle).as_posix() != "SHA256SUMS"
    }
    require(set(entries) == actual, "Public root ledger is incomplete")
    require((bundle / "README.md").is_file(), "English public README missing")
    require((bundle / "README.ja.md").is_file(), "Japanese public README missing")
    validate_ledger(bundle / "analysis", ANALYSIS_FILES)
    validate_ledger(bundle / "preflight", PREFLIGHT_FILES)
    for role in MODEL_ORDER:
        validate_ledger(bundle / "runs" / role, RUN_FILES)
    validate_ledger(bundle / "validation", VALIDATION_FILES)
    manifest = read_json(bundle / "PUBLIC_MANIFEST.json")
    primary = read_json(bundle / "analysis" / "primary_result.json")
    independent = read_json(bundle / "validation" / "independent_validation.json")
    require(manifest["protocol_id"] == PROTOCOL_ID, "Public protocol changed")
    require(manifest["confirmed_hypotheses"] == [], "Public confirmation changed")
    require(
        manifest["outcome_pattern"] == "neither_registered_hypothesis_confirmed",
        "Public outcome changed",
    )
    require(
        manifest["primary_result_sha256"]
        == sha256(bundle / "analysis" / "primary_result.json"),
        "Public primary binding changed",
    )
    require(primary["confirmed_hypotheses"] == [], "Primary confirmation changed")
    require(independent["status"] == "pass", "Public validation did not pass")
    for field in (
        "semantic_claim_authorized",
        "causal_claim_authorized",
        "behavioral_steering_claim_authorized",
        "model_general_claim_authorized",
    ):
        require(manifest[field] is False, f"Public bundle authorized {field}")
    inventory = {row["path"]: row for row in manifest["included_payload"]}
    inventory_expected = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file()
        and path.relative_to(bundle).as_posix()
        not in {"PUBLIC_MANIFEST.json", "SHA256SUMS"}
    }
    require(set(inventory) == inventory_expected, "Public inventory changed")
    for relative, row in inventory.items():
        path = bundle / relative
        require(path.stat().st_size == int(row["bytes"]), f"Size changed: {relative}")
        require(sha256(path) == row["sha256"], f"Inventory hash changed: {relative}")
    return {
        "status": "pass",
        "outcome_pattern": manifest["outcome_pattern"],
        "confirmed_hypotheses": [],
        "payload_files": len(entries),
        "primary_result_sha256": manifest["primary_result_sha256"],
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    result = sub.add_parser("validate-result")
    result.add_argument("--analysis", type=Path, required=True)
    result.add_argument("--preflight", type=Path, required=True)
    result.add_argument("--runs-root", type=Path, required=True)
    result.add_argument("--freeze-manifest", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    seal = sub.add_parser("seal-public-bundle")
    seal.add_argument("--source", type=Path, required=True)
    seal.add_argument("--validation", type=Path, required=True)
    seal.add_argument("--readme", type=Path, required=True)
    seal.add_argument("--readme-ja", type=Path, required=True)
    seal.add_argument("--freeze-manifest", type=Path, required=True)
    seal.add_argument("--config", type=Path, required=True)
    seal.add_argument("--design-preflight", type=Path, required=True)
    seal.add_argument("--output", type=Path, required=True)
    public = sub.add_parser("validate-public-bundle")
    public.add_argument("--bundle", type=Path, required=True)
    return root


def main() -> None:
    args = parser().parse_args()
    if args.command == "validate-result":
        value = validate_result(
            args.analysis,
            args.preflight,
            args.runs_root,
            args.freeze_manifest,
            args.output,
        )
    elif args.command == "seal-public-bundle":
        value = seal_public_bundle(
            args.source,
            args.validation,
            args.readme,
            args.readme_ja,
            args.freeze_manifest,
            args.config,
            args.design_preflight,
            args.output,
        )
    else:
        value = validate_public_bundle(args.bundle)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
