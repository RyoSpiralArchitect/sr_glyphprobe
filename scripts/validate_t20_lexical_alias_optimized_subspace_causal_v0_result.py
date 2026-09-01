#!/usr/bin/env python3
"""Independent validator for the T20-C optimized-subspace causal result.

Imports only numpy, yaml, and the standard library. It does not import the
runner; every reported statistic is re-derived from the sealed arrays with
independent implementations and compared against the committed JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-t20-lexical-alias-optimized-subspace-causal-v0"
SITE_ORDER = (
    ("resid_out", 21),
    ("resid_out", 24),
    ("resid_out", 27),
    ("attn_out", 21),
    ("mlp_out", 21),
    ("attn_out", 24),
    ("mlp_out", 24),
    ("attn_out", 27),
    ("mlp_out", 27),
)
PRIMARY_SITES = (("resid_out", 21), ("resid_out", 24))
GLYPH_CONDITION_ORDER = (
    "zero_hook",
    "necessity_optimized",
    "necessity_random",
    "necessity_svd",
    "restoration_optimized",
    "full_interchange_codepoint",
)
CODEPOINT_CONDITION_ORDER = (
    "zero_hook",
    "sufficiency_optimized",
    "sufficiency_random",
    "sufficiency_svd",
    "full_interchange_glyph",
)
SIGN_FLIP_SEED_BASE = (2026091100, 2026091101)
BOOTSTRAP_SEED_BASE = (2026091200, 2026091201)


class T20ValidationError(RuntimeError):
    """Raised when the recorded T20 result cannot be reproduced."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise T20ValidationError(message)


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


def bank_hash(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = json.dumps(list(rows), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assert_close(observed: float, expected: float, label: str, *, tolerance: float = 1e-9) -> None:
    require(abs(float(observed) - float(expected)) <= tolerance, f"Mismatch at {label}: {observed} != {expected}")


def normalized(value: np.ndarray) -> np.ndarray:
    centered = np.asarray(value, dtype=np.float64) - np.mean(value, axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    require(bool(np.all(norms > 0)), "Zero row norm during validation")
    return centered / norms


def hits_by_context(queries: np.ndarray, alias_targets: np.ndarray, codepoint_targets: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    items, contexts, _ = queries.shape
    alias_hits = np.zeros((items, contexts), dtype=np.float64)
    codepoint_hits = np.zeros((items, contexts), dtype=np.float64)
    order = np.arange(items)
    for context in range(contexts):
        q = normalized(queries[:, context])
        alias = normalized(alias_targets[:, context])
        codepoint = normalized(codepoint_targets[:, context])
        alias_hits[:, context] = (np.argmax(q @ alias.T, axis=1) == order).astype(np.float64)
        codepoint_hits[:, context] = (np.argmax(q @ codepoint.T, axis=1) == order).astype(np.float64)
    return alias_hits.mean(axis=1), codepoint_hits.mean(axis=1)


def sign_flip(values: np.ndarray, *, draws: int, seed: int) -> dict[str, float]:
    observed = float(np.mean(values))
    rng = np.random.default_rng(seed)
    exceedances = 0
    for start in range(0, draws, 2000):
        stop = min(draws, start + 2000)
        signs = rng.integers(0, 2, size=(stop - start, len(values)), dtype=np.int8) * 2 - 1
        statistics = np.mean(signs * values[None, :], axis=1)
        exceedances += int(np.sum(statistics >= observed - 1e-15))
    return {"observed": observed, "p_value_one_sided": (1 + exceedances) / (draws + 1)}


def bootstrap(values: np.ndarray, *, replicates: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=np.float64)
    for start in range(0, replicates, 500):
        stop = min(replicates, start + 500)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        draws[start:stop] = np.mean(values[indices], axis=1)
    return {"lower_95": float(np.quantile(draws, 0.025)), "upper_95": float(np.quantile(draws, 0.975))}


def rederive_svd_and_random(glyph: np.ndarray, alias: np.ndarray, rank: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    def row_normalized(value: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mean = np.mean(value, axis=0, dtype=np.float64)
        centered = np.asarray(value, dtype=np.float64) - mean
        norms = np.linalg.norm(centered, axis=1, keepdims=True)
        require(bool(np.all(norms > 0)), "Zero source row norm during validation")
        return centered / norms, mean.astype(np.float32)

    g, mean_g = row_normalized(glyph)
    a, _mean_a = row_normalized(alias)
    qg, rg = np.linalg.qr(g.T, mode="reduced")
    qa, ra = np.linalg.qr(a.T, mode="reduced")
    u_small, _singular, _right = np.linalg.svd(rg @ ra.T, full_matrices=False)
    learned = qg @ u_small[:, :rank]
    learned, _ = np.linalg.qr(learned, mode="reduced")
    combined = np.concatenate((g, a), axis=0)
    source_span, source_singular, _ = np.linalg.svd(combined.T, full_matrices=False)
    tolerance = source_singular[0] * max(combined.shape) * np.finfo(np.float64).eps
    source_span = source_span[:, source_singular > tolerance]
    rng = np.random.default_rng(seed)
    candidate = source_span @ rng.normal(size=(source_span.shape[1], rank * 2))
    candidate = candidate - learned @ (learned.T @ candidate)
    random_basis, _ = np.linalg.qr(candidate, mode="reduced")
    return learned[:, :rank].astype(np.float32), random_basis[:, :rank].astype(np.float32), mean_g


def subspace_distance(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.max(np.abs(left @ left.T - right @ right.T)))


def validate(
    *, repository: Path, training_root: Path, evaluation_root: Path, analysis_root: Path, output: Path | None
) -> dict[str, Any]:
    config = yaml.safe_load((repository / "configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml").read_text(encoding="utf-8"))
    require(config["protocol_id"] == PROTOCOL_ID, "Config protocol mismatch")
    decision = config["primary_decision"]
    practical = float(decision["practical_minimum_each"])
    ceiling_minimum = float(decision["ceiling_positive_control"]["informative_minimum"])
    draws = int(decision["sign_flip_draws"])
    replicates = int(decision["bootstrap_replicates"])

    go = read_json(repository / "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_go.json")
    require(go["protocol_id"] == PROTOCOL_ID and go["status"] == "t20_go_admitted_before_source_or_eval_forwards", "Go manifest mismatch")
    for key in ("source_model_forwards_at_go", "evaluation_model_forwards_at_go", "intervention_calls_at_go"):
        require(int(go[key]) == 0, f"Go counter nonzero: {key}")
    executor = repository / "scripts/t20_lexical_alias_optimized_subspace_causal_v0.py"
    require(sha256(executor) == go["causal_executor_analyzer_sha256"], "Executor changed after go")
    freeze = read_json(repository / "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_freeze.json")
    require(freeze["protocol_id"] == PROTOCOL_ID, "Freeze manifest mismatch")
    require(go["t20_freeze_manifest_sha256"] == sha256(repository / "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_freeze.json"), "Go freeze binding mismatch")

    selection = read_json(repository / "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0.json")
    fresh = sorted((dict(row) for row in selection["fresh_eval_items"]), key=lambda row: int(row["bank_index"]))
    t19_selection = read_json(repository / "data/manifests/t19_lexical_alias_unicode_control_v0.json")
    source_rows = sorted((dict(row) for row in t19_selection["causal_source_items"]), key=lambda row: int(row["bank_index"]))
    require(bank_hash(source_rows) == go["source_bank_sha256"], "Source bank hash mismatch")
    require(bank_hash(fresh) == go["fresh_eval_bank_sha256"], "Fresh bank hash mismatch")
    t19_codepoints = {
        str(row["codepoint"])
        for key in ("observational_items", "causal_source_items", "causal_eval_items")
        for row in t19_selection[key]
    }
    require(not {str(row["codepoint"]) for row in fresh}.intersection(t19_codepoints), "Fresh bank overlaps T19")
    rows_expected = int(config["population"]["fresh_eval_emoji_items"])
    require(len(fresh) == rows_expected, "Fresh bank count mismatch")

    training_receipt = read_json(training_root / "training_receipt.json")
    require(training_receipt["protocol_id"] == PROTOCOL_ID and training_receipt["status"] == "t20_training_complete", "Training receipt mismatch")
    require(int(training_receipt["capture_forward_calls"]) == len(source_rows) * 3, "Training capture forward count mismatch")
    require(int(training_receipt["intervention_calls"]) == 0, "Training intervention counter nonzero")
    for name, expected in training_receipt["outputs"].items():
        require(sha256(training_root / name) == expected, f"Training output changed: {name}")
    activations = np.load(training_root / "source_activations.npy", allow_pickle=False)
    require(activations.shape == (9, len(source_rows), 3, 3072), "Source activation shape mismatch")
    with np.load(training_root / "subspaces.npz", allow_pickle=False) as values:
        optimized = np.asarray(values["optimized"], dtype=np.float64)
        svd_basis = np.asarray(values["cross_covariance_svd"], dtype=np.float64)
        random_basis = np.asarray(values["random_control"], dtype=np.float64)
        glyph_means = np.asarray(values["glyph_means"], dtype=np.float64)
    for stack, label in ((optimized, "optimized"), (svd_basis, "svd"), (random_basis, "random")):
        require(stack.shape == (9, 3072, 8), f"Subspace shape mismatch: {label}")
        for index in range(9):
            gram = stack[index].T @ stack[index]
            require(float(np.max(np.abs(gram - np.eye(8)))) < 2e-5, f"Subspace not orthonormal: {label}/{index}")
    for index in range(9):
        expected_svd, expected_random, expected_mean = rederive_svd_and_random(
            activations[index, :, 0, :], activations[index, :, 1, :], 8, 2026091000 + index
        )
        require(subspace_distance(svd_basis[index].astype(np.float32).astype(np.float64), expected_svd.astype(np.float64)) < 2e-4, f"SVD basis differs at site {index}")
        require(subspace_distance(random_basis[index].astype(np.float32).astype(np.float64), expected_random.astype(np.float64)) < 2e-4, f"Random basis differs at site {index}")
        require(float(np.max(np.abs(glyph_means[index] - expected_mean))) < 1e-4, f"Glyph mean differs at site {index}")
        require(float(np.max(np.abs(svd_basis[index].T @ random_basis[index]))) < 2e-5, f"Random control overlaps svd at site {index}")

    evaluation_receipt = read_json(evaluation_root / "evaluation_receipt.json")
    require(evaluation_receipt["protocol_id"] == PROTOCOL_ID and evaluation_receipt["status"] == "t20_evaluation_complete_sealed", "Evaluation receipt mismatch")
    require(evaluation_receipt["training_receipt_sha256"] == sha256(training_root / "training_receipt.json"), "Evaluation training binding mismatch")
    require(evaluation_receipt["fresh_eval_bank_sha256"] == bank_hash(fresh), "Evaluation bank binding mismatch")
    require(int(evaluation_receipt["model_forward_calls"]) == rows_expected * 4 * (3 + 2 * 9), "Evaluation forward count mismatch")
    require(int(evaluation_receipt["intervention_rows"]) == rows_expected * 4 * 9 * 9, "Evaluation intervention count mismatch")
    for name, expected in evaluation_receipt["outputs"].items():
        require(sha256(evaluation_root / name) == expected, f"Evaluation output changed: {name}")
    with np.load(evaluation_root / "evaluation_states.npz", allow_pickle=False) as arrays:
        baseline_finals = np.asarray(arrays["baseline_finals"], dtype=np.float32)
        baseline_components = np.asarray(arrays["baseline_components"], dtype=np.float32)
        glyph_conditions = np.asarray(arrays["glyph_conditions"], dtype=np.float32)
        codepoint_conditions = np.asarray(arrays["codepoint_conditions"], dtype=np.float32)
    require(baseline_finals.shape == (rows_expected, 4, 3, 3072), "Baseline shape mismatch")
    require(baseline_components.shape == (9, rows_expected, 4, 2, 3072), "Component shape mismatch")
    require(glyph_conditions.shape == (9, rows_expected, 4, 6, 3072), "Glyph condition shape mismatch")
    require(codepoint_conditions.shape == (9, rows_expected, 4, 5, 3072), "Codepoint condition shape mismatch")

    site_results = read_json(analysis_root / "causal_site_results.json")
    primary_result = read_json(analysis_root / "causal_primary_result.json")
    analysis_receipt = read_json(analysis_root / "analysis_receipt.json")
    require(analysis_receipt["protocol_id"] == PROTOCOL_ID and analysis_receipt["status"] == "t20_analysis_complete", "Analysis receipt mismatch")
    for name, expected in analysis_receipt["outputs"].items():
        require(sha256(analysis_root / name) == expected, f"Analysis output changed: {name}")
    require(analysis_receipt["evaluation_receipt_sha256"] == sha256(evaluation_root / "evaluation_receipt.json"), "Analysis evaluation binding mismatch")

    alias_targets = baseline_finals[:, :, 1]
    codepoint_targets = baseline_finals[:, :, 2]
    recomputed_rows: list[dict[str, Any]] = []
    for site_index, (site, block_index) in enumerate(SITE_ORDER):
        stored = site_results["sites"][site_index]
        require(stored["site"] == site and int(stored["block_index"]) == block_index, f"Site order mismatch at {site_index}")
        glyph_alias_items: dict[str, np.ndarray] = {}
        for condition_index, condition in enumerate(GLYPH_CONDITION_ORDER):
            alias_items, codepoint_items = hits_by_context(glyph_conditions[site_index, :, :, condition_index], alias_targets, codepoint_targets)
            glyph_alias_items[condition] = alias_items
            assert_close(float(np.mean(alias_items)), stored["glyph_conditions"][condition]["alias_top1"], f"{site}:{block_index}:{condition}:alias")
            assert_close(float(np.mean(codepoint_items)), stored["glyph_conditions"][condition]["codepoint_top1"], f"{site}:{block_index}:{condition}:codepoint")
        codepoint_alias_items: dict[str, np.ndarray] = {}
        codepoint_self_items: dict[str, np.ndarray] = {}
        for condition_index, condition in enumerate(CODEPOINT_CONDITION_ORDER):
            alias_items, codepoint_items = hits_by_context(codepoint_conditions[site_index, :, :, condition_index], alias_targets, codepoint_targets)
            codepoint_alias_items[condition] = alias_items
            codepoint_self_items[condition] = codepoint_items
            assert_close(float(np.mean(alias_items)), stored["codepoint_conditions"][condition]["alias_top1"], f"{site}:{block_index}:{condition}:alias")
            assert_close(float(np.mean(codepoint_items)), stored["codepoint_conditions"][condition]["codepoint_top1"], f"{site}:{block_index}:{condition}:codepoint")

        necessity_adjusted = glyph_alias_items["necessity_random"] - glyph_alias_items["necessity_optimized"]
        sufficiency_adjusted = codepoint_alias_items["sufficiency_optimized"] - codepoint_alias_items["sufficiency_random"]
        assert_close(float(np.mean(necessity_adjusted)), stored["necessity_adjusted_effect"], f"{site}:{block_index}:necessity_adjusted")
        assert_close(float(np.mean(sufficiency_adjusted)), stored["sufficiency_adjusted_effect"], f"{site}:{block_index}:sufficiency_adjusted")
        necessity_test = sign_flip(necessity_adjusted, draws=draws, seed=SIGN_FLIP_SEED_BASE[0] + site_index * 10)
        sufficiency_test = sign_flip(sufficiency_adjusted, draws=draws, seed=SIGN_FLIP_SEED_BASE[1] + site_index * 10)
        assert_close(necessity_test["p_value_one_sided"], stored["necessity_test"]["p_value_one_sided"], f"{site}:{block_index}:necessity_p")
        assert_close(sufficiency_test["p_value_one_sided"], stored["sufficiency_test"]["p_value_one_sided"], f"{site}:{block_index}:sufficiency_p")
        necessity_interval = bootstrap(necessity_adjusted, replicates=replicates, seed=BOOTSTRAP_SEED_BASE[0] + site_index * 10)
        sufficiency_interval = bootstrap(sufficiency_adjusted, replicates=replicates, seed=BOOTSTRAP_SEED_BASE[1] + site_index * 10)
        assert_close(necessity_interval["lower_95"], stored["necessity_interval"]["lower_95"], f"{site}:{block_index}:necessity_lower")
        assert_close(sufficiency_interval["lower_95"], stored["sufficiency_interval"]["lower_95"], f"{site}:{block_index}:sufficiency_lower")
        site_iut_p = max(necessity_test["p_value_one_sided"], sufficiency_test["p_value_one_sided"])
        assert_close(site_iut_p, stored["site_iut_p"], f"{site}:{block_index}:iut")

        sufficiency_ceiling = float(np.mean(codepoint_alias_items["full_interchange_glyph"] - codepoint_alias_items["zero_hook"]))
        necessity_ceiling = float(np.mean(glyph_alias_items["zero_hook"] - glyph_alias_items["full_interchange_codepoint"]))
        assert_close(sufficiency_ceiling, stored["sufficiency_ceiling"], f"{site}:{block_index}:sufficiency_ceiling")
        assert_close(necessity_ceiling, stored["necessity_ceiling"], f"{site}:{block_index}:necessity_ceiling")
        self_retrieval_guard = float(np.mean(codepoint_self_items["sufficiency_optimized"]))
        assert_close(self_retrieval_guard, stored["self_retrieval_guard"], f"{site}:{block_index}:guard")

        zero_glyph_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, :, 0] - baseline_finals[:, :, 0]) ** 2)))
        zero_codepoint_rms = float(np.sqrt(np.mean((codepoint_conditions[site_index, :, :, 0] - baseline_finals[:, :, 2]) ** 2)))
        restoration_rms = float(np.sqrt(np.mean((glyph_conditions[site_index, :, :, 4] - baseline_finals[:, :, 0]) ** 2)))
        assert_close(zero_glyph_rms, stored["engineering"]["zero_glyph_final_rms"], f"{site}:{block_index}:zero_glyph_rms", tolerance=1e-12)
        assert_close(zero_codepoint_rms, stored["engineering"]["zero_codepoint_final_rms"], f"{site}:{block_index}:zero_codepoint_rms", tolerance=1e-12)
        assert_close(restoration_rms, stored["engineering"]["restoration_final_rms"], f"{site}:{block_index}:restoration_rms", tolerance=1e-12)
        engineering_pass = max(zero_glyph_rms, zero_codepoint_rms, restoration_rms) <= float(decision["engineering_rms_maximum"])
        require(engineering_pass == bool(stored["engineering"]["pass"]), f"Engineering pass mismatch at {site}:{block_index}")

        practical_and_interval_pass = bool(
            float(np.mean(necessity_adjusted)) >= practical
            and float(np.mean(sufficiency_adjusted)) >= practical
            and necessity_interval["lower_95"] > practical
            and sufficiency_interval["lower_95"] > practical
        )
        require(practical_and_interval_pass == bool(stored["practical_and_interval_pass"]), f"Practical pass mismatch at {site}:{block_index}")
        guard_pass = bool(self_retrieval_guard >= 0.90)
        require(guard_pass == bool(stored["self_retrieval_guard_pass"]), f"Guard pass mismatch at {site}:{block_index}")
        recomputed_rows.append(
            {
                "site": site,
                "block_index": block_index,
                "primary": (site, block_index) in PRIMARY_SITES,
                "site_iut_p": site_iut_p,
                "practical_and_interval_pass": practical_and_interval_pass,
                "guard_pass": guard_pass,
                "engineering_pass": engineering_pass,
                "sufficiency_ceiling": sufficiency_ceiling,
            }
        )

    primary_rows = sorted((row for row in recomputed_rows if row["primary"]), key=lambda row: (row["site_iut_p"], row["site"], row["block_index"]))
    still = True
    verdicts: dict[str, Any] = {}
    positive_sites: list[str] = []
    for index, row in enumerate(primary_rows):
        threshold = 0.05 / (len(primary_rows) - index)
        reject = still and row["site_iut_p"] <= threshold
        still = bool(reject)
        positive = bool(reject and row["practical_and_interval_pass"] and row["guard_pass"] and row["engineering_pass"])
        if positive:
            verdict = "positive"
            positive_sites.append(f"{row['site']}:{row['block_index']}")
        elif row["sufficiency_ceiling"] >= ceiling_minimum:
            verdict = "negative_with_informative_ceiling"
        else:
            verdict = "uncalibratable_at_endpoint"
        verdicts[f"{row['site']}:{row['block_index']}"] = verdict
    stored_primary = {f"{row['site']}:{row['block_index']}": row for row in primary_result["primary_sites"]}
    for key, verdict in verdicts.items():
        require(stored_primary[key]["verdict"] == verdict, f"Verdict mismatch at {key}")
    require(sorted(positive_sites) == sorted(primary_result["positive_sites"]), "Positive site list mismatch")
    require(bool(positive_sites) == bool(primary_result["positive"]), "Primary positive flag mismatch")

    result = {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "t20_independent_validation_pass",
        "primary_positive": bool(primary_result["positive"]),
        "positive_sites": list(primary_result["positive_sites"]),
        "primary_verdicts": verdicts,
        "sites_validated": len(recomputed_rows),
        "evaluation_model_forward_calls": int(evaluation_receipt["model_forward_calls"]),
        "intervention_rows": int(evaluation_receipt["intervention_rows"]),
        "training_capture_forward_calls": int(training_receipt["capture_forward_calls"]),
        "training_batched_forward_passes": int(training_receipt["training_batched_forward_passes"]),
        "analysis_receipt_sha256": sha256(analysis_root / "analysis_receipt.json"),
        "go_manifest_sha256": sha256(repository / "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_go.json"),
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--training-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(
        repository=args.repository,
        training_root=args.training_root,
        evaluation_root=args.evaluation_root,
        analysis_root=args.analysis_root,
        output=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
