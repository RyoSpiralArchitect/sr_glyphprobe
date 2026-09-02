#!/usr/bin/env python3
"""Replay all T19-L primary-window statistics from compact indices (NumPy only)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np


PROTOCOL = "glyphprobe-t19-lexical-alias-unicode-control-v0"
PREFIX = "validation/t19_lexical_alias_unicode_control_v0"
ROLES = [
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
]
CORE = [
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
]
KINDS = ["emoji", "symbol"]
COMPONENTS = ["unrestricted", "matched"]
TARGETS = ["alias", "canonical", "codepoint"]
BINDINGS = [
    "configs/t19_lexical_alias_unicode_control_v0.yaml",
    "data/manifests/t19_lexical_alias_unicode_control_v0.json",
    "data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json",
    f"{PREFIX}/independent_validation.json",
    f"{PREFIX}/results/model_cell_results.json",
    f"{PREFIX}/results/cross_model_primary_result.json",
] + [f"{PREFIX}/tokenizers/{role}.json" for role in ROLES]
CONTEXTS = [
    [depth, carrier, distance]
    for depth in (0.75, 0.875, 1.0)
    for carrier in ("article_a", "pipe")
    for distance in (1, 2, 4, 8)
]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_predictions(predictions: dict, n: int) -> dict[str, np.ndarray]:
    check(set(predictions) == set(TARGETS), "Prediction target set changed")
    arrays = {key: np.asarray(value) for key, value in predictions.items()}
    for value in arrays.values():
        check(value.shape == (24, n), "Prediction shape changed")
        check(
            np.issubdtype(value.dtype, np.integer),
            "Prediction indices are not integers",
        )
        check(bool(((value >= 0) & (value < n)).all()), "Prediction index out of range")
    return arrays


def validate_strata(strata: list[list[int]], n: int) -> None:
    check(all(len(s) >= 2 for s in strata), "Singleton or empty stratum")
    check(all(type(i) is int for s in strata for i in s), "Noninteger stratum index")
    check(
        sorted(i for s in strata for i in s) == list(range(n)),
        "Strata do not partition items",
    )


def exact_null_keyword_rate(predictions: np.ndarray, strata: list[list[int]]) -> float:
    n = predictions.shape[1]
    validate_strata(strata, n)
    membership = np.empty(n, dtype=int)
    sizes = np.empty(n, dtype=float)
    for k, group in enumerate(strata):
        membership[group] = k
        sizes[group] = len(group)
    return float(
        np.mean((membership[predictions] == membership[None, :]) / sizes[None, :])
    )


def replay_component(predictions: dict, strata: list[list[int]], seed: int) -> dict:
    alias, canonical, codepoint = (predictions[k] for k in TARGETS)
    n = alias.shape[1]
    validate_strata(strata, n)
    identity = np.arange(n)
    hits = {name: value == identity[None, :] for name, value in predictions.items()}
    item = hits["alias"].mean(axis=0) - hits["codepoint"].mean(axis=0)
    official = hits["canonical"].mean(axis=0) - hits["codepoint"].mean(axis=0)
    observed = float(item.mean())
    fixed_codepoint = float(hits["codepoint"].mean())
    rng = np.random.default_rng(seed)
    exceedances, null_sum, null_sumsq = 0, 0.0, 0.0
    groups = [np.asarray(s) for s in strata]
    for _ in range(19999):
        mapping = identity.copy()
        for group in groups:
            mapping[group] = rng.permutation(group)
        value = float(np.mean(alias == mapping[None, :]) - fixed_codepoint)
        exceedances += int(value >= observed - 1e-15)
        null_sum += value
        null_sumsq += value * value
    mean = null_sum / 19999
    rng = np.random.default_rng(seed + 1000)
    boot = np.empty(20000)
    for start in range(0, 20000, 500):
        boot[start : start + 500] = item[rng.integers(n, size=(500, n))].mean(axis=1)
    exact = exact_null_keyword_rate(alias, strata)
    return {
        "item_count": n,
        "alias_minus_codepoint_top1": observed,
        "canonical_minus_codepoint_top1": float(official.mean()),
        "alias_minus_canonical_top1": float((item - official).mean()),
        "randomization": {
            "draws": 19999,
            "seed": seed,
            "observed": observed,
            "exceedances": exceedances,
            "p_value_one_sided": (exceedances + 1) / 20000,
            "null_mean": mean,
            "null_sd": math.sqrt(max(0, null_sumsq / 19999 - mean * mean)),
        },
        "descriptive_interval": {
            "replicates": 20000,
            "seed": seed + 1000,
            "lower_95": float(np.quantile(boot, 0.025)),
            "upper_95": float(np.quantile(boot, 0.975)),
            "bootstrap_mean": float(boot.mean()),
        },
        "null_benchmarks": {
            "uniform_gallery_guessing_rate": 1 / n,
            "exact_conditional_keyword_null_rate": exact,
            "fixed_codepoint_top1": fixed_codepoint,
            "exact_conditional_effect_null_mean": exact - fixed_codepoint,
            "observed_keyword_top1": float(hits["alias"].mean()),
        },
    }


def verify(compact: dict, root: Path) -> dict:
    check(compact["protocol_id"] == PROTOCOL, "Protocol changed")
    check(
        compact["role_order"] == ROLES and compact["core_roles"] == CORE,
        "Roster changed",
    )
    check(compact["context_order"] == CONTEXTS, "Context order changed")
    check(
        [r["model_role"] for r in compact["models"]] == ROLES,
        "Missing or duplicate model",
    )
    check(set(compact["input_sha256"]) == set(BINDINGS), "Input binding set changed")
    for name in BINDINGS:
        check(
            digest(root / name) == compact["input_sha256"][name], "Input bytes changed"
        )
    independent = read(root / PREFIX / "independent_validation.json")
    expected_models = read(root / PREFIX / "results/model_cell_results.json")["models"]
    check(
        [r["model_role"] for r in expected_models] == ROLES, "Published roster changed"
    )
    errors = []

    def equal_number(actual, expected):
        error = abs(float(actual) - float(expected))
        check(
            math.isfinite(error) and error < 1e-12, "Numerical reconstruction differs"
        )
        errors.append(error)

    rebuilt = []
    for role_index, (model, expected) in enumerate(
        zip(compact["models"], expected_models, strict=True)
    ):
        role = model["model_role"]
        receipt_text = model["source_summary_receipt_json"]
        receipt_hash = hashlib.sha256(receipt_text.encode("utf-8")).hexdigest()
        check(
            receipt_hash == independent["summary_receipt_sha256"][role],
            "Original summary binding differs",
        )
        receipt = json.loads(receipt_text)
        check(
            receipt["model_role"] == role and receipt["protocol_id"] == PROTOCOL,
            "Summary identity differs",
        )
        check(
            model["source_predictions_sha256"]
            == receipt["outputs"]["primary_predictions.npz"],
            "Prediction provenance differs",
        )
        token = read(root / PREFIX / "tokenizers" / f"{role}.json")["tokenizer"][
            "primary_exact_strata"
        ]
        check(set(model["cells"]) == set(KINDS), "Glyph kinds changed")
        kinds = {}
        for ki, kind in enumerate(KINDS):
            check(set(model["cells"][kind]) == set(COMPONENTS), "Component set changed")
            components = {}
            for ci, component in enumerate(COMPONENTS):
                cell = model["cells"][kind][component]
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
                check(
                    cell["global_item_indices"] == indices and cell["strata"] == strata,
                    "Item order or strata changed",
                )
                arrays = validate_predictions(cell["predictions"], len(indices))
                actual = replay_component(
                    arrays, strata, 2026090200 + role_index * 100 + ki * 10 + ci
                )
                saved = expected["kind_components"][kind][component]
                for key in (
                    "item_count",
                    "alias_minus_codepoint_top1",
                    "canonical_minus_codepoint_top1",
                    "alias_minus_canonical_top1",
                ):
                    equal_number(actual[key], saved[key])
                for section in ("randomization", "descriptive_interval"):
                    check(
                        set(actual[section]) == set(saved[section]),
                        "Statistic schema differs",
                    )
                    for key in actual[section]:
                        equal_number(actual[section][key], saved[section][key])
                components[component] = actual
            kinds[kind] = components
        iut = max(
            kinds["emoji"][c]["randomization"]["p_value_one_sided"] for c in COMPONENTS
        )
        practical = all(
            kinds["emoji"][c]["alias_minus_codepoint_top1"] >= 0.02 for c in COMPONENTS
        )
        positive = iut <= 0.05 and practical
        equal_number(iut, expected["model_iut_p"])
        check(
            practical == expected["practical_pass"]
            and positive == expected["model_positive"],
            "Model decision differs",
        )
        for component in COMPONENTS:
            equal_number(
                kinds["emoji"][component]["alias_minus_codepoint_top1"]
                - kinds["symbol"][component]["alias_minus_codepoint_top1"],
                expected["emoji_minus_symbol_alias_codepoint_difference"][component],
            )
        rebuilt.append(
            {
                "model_role": role,
                "model_iut_p": iut,
                "practical_pass": practical,
                "model_positive": positive,
                "kind_components": kinds,
            }
        )
        print(json.dumps({"model_role": role, "four_tests_replayed": True}), flush=True)
    by_role = {r["model_role"]: r for r in expected_models}
    still_rejecting = True
    for rank, model in enumerate(
        sorted(rebuilt, key=lambda r: (r["model_iut_p"], r["model_role"])), 1
    ):
        threshold = 0.05 / (10 - rank)
        still_rejecting = still_rejecting and model["model_iut_p"] <= threshold
        expected = by_role[model["model_role"]]
        equal_number(rank, expected["holm_rank"])
        equal_number(threshold, expected["holm_threshold"])
        check(
            (still_rejecting and model["practical_pass"]) == expected["holm_reject"],
            "Holm decision differs",
        )
    core = [r for r in rebuilt if r["model_role"] in CORE]
    p = min(1, 2 * sorted(r["model_iut_p"] for r in core)[2])
    positive_count = sum(r["model_positive"] for r in core)
    saved = read(root / PREFIX / "results/cross_model_primary_result.json")[
        "cross_model_primary"
    ]
    equal_number(p, saved["partial_conjunction_p"])
    equal_number(positive_count, saved["core_model_positive_count"])
    check(saved["core_roles"] == CORE, "Core order differs")
    for key, actual in {
        "statistical_pass": p <= 0.05,
        "practical_pass": positive_count >= 3,
        "positive": p <= 0.05 and positive_count >= 3,
        "causal_go_gate_open": p <= 0.05 and positive_count >= 3,
    }.items():
        check(actual == saved[key], "Cross-model decision differs")
    return {
        "status": "pass",
        "randomization_tests_replayed": 36,
        "randomization_draws_per_test": 19999,
        "bootstrap_intervals_replayed": 36,
        "bootstrap_replicates_per_interval": 20000,
        "maximum_numeric_error": max(errors),
        "partial_conjunction_p": p,
        "core_positive_count": positive_count,
        "all_nine_positive": all(r["model_positive"] for r in rebuilt),
        "models": rebuilt,
        "boundary": "Statistical replay from fixed prediction indices; hidden-state and tokenizer acquisition are separate checks.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compact", type=Path, required=True)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(read(args.compact), args.root)
    result.update(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        compact_sha256=digest(args.compact),
        validator_sha256=digest(Path(__file__)),
        numpy_version=np.__version__,
    )
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k != "models"}, indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
