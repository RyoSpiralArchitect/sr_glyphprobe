#!/usr/bin/env python3
"""Post-hoc dependence-aware sensitivity analysis for Milestone 2.

This analysis is deliberately separate from the frozen v1 confirmatory
analyzer.  It propagates the dependence introduced by shared, estimated
leave-one-target-group-out prototypes: every stratified target-bootstrap
replicate rebuilds every prototype from that replicate's resampled targets,
jointly for the primary panel, matched-null panels A/B/C, and all fixed
direction seeds.  It then recomputes target scores, the targetwise median of
the three null scores, and the layer mean adjusted effect.

The analysis is post hoc.  Its interval is a sensitivity interval, not a
preregistered confirmatory interval, and it never replaces or reclassifies the
frozen v1 statuses.  It reads stored fingerprints only and does not run a
model.  The C1 causal holdout is never read.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import orjson

import analyze_m2_confirmatory as frozen_v1


ANALYSIS_ID = "glyphprobe-m2-posthoc-dependence-sensitivity-v1"
SCHEMA_VERSION = 1
DEFAULT_BOOTSTRAP_REPLICATES = 20_000
# Reuse the v1 target-bootstrap seed so the fixed-score and rebuilt-prototype
# intervals can be compared under the same stratified resamples.  This choice
# was made after P2 was opened and has no preregistered status.
DEFAULT_BOOTSTRAP_SEED = frozen_v1.DEFAULT_BOOTSTRAP_SEED
DEFAULT_CHUNK_SIZE = 128
EPSILON = frozen_v1.EPSILON


class DependenceSensitivityError(ValueError):
    """Raised when the sensitivity analysis cannot be evaluated exactly."""


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, option=option)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value, pretty=True) + b"\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    _atomic_write(path, b"".join(_json_bytes(dict(row)) + b"\n" for row in rows))


def _ordered_target_grid(
    target_groups: Mapping[str, str],
) -> tuple[tuple[str, ...], tuple[tuple[int, ...], ...]]:
    """Return a group-major target order and indices for the six strata."""

    target_ids: list[str] = []
    group_indices: list[tuple[int, ...]] = []
    for group in frozen_v1.EXPECTED_TARGET_GROUPS:
        group_targets = sorted(
            target_id
            for target_id, observed_group in target_groups.items()
            if observed_group == group
        )
        if not group_targets:
            raise DependenceSensitivityError(f"No targets are available for group {group}")
        start = len(target_ids)
        target_ids.extend(group_targets)
        group_indices.append(tuple(range(start, start + len(group_targets))))
    if len(target_ids) != len(set(target_ids)) or set(target_ids) != set(target_groups):
        raise DependenceSensitivityError("Target groups do not form a unique complete grid")
    return tuple(target_ids), tuple(group_indices)


def _panel_tensor(
    panel: Mapping[str, Any],
    *,
    layers: Sequence[int],
    direction_seeds: Sequence[int],
    strength: float,
    target_ids: Sequence[str],
) -> np.ndarray:
    """Materialize one panel as [layer, seed, condition, target, dimension]."""

    conditions: Sequence[str] = panel["conditions"]
    vectors: Mapping[tuple[int, float, int, str, str], np.ndarray] = panel["vectors"]
    sample = next(iter(vectors.values()))
    tensor = np.empty(
        (
            len(layers),
            len(direction_seeds),
            len(conditions),
            len(target_ids),
            int(sample.size),
        ),
        dtype=np.float64,
    )
    for layer_index, layer in enumerate(layers):
        for seed_index, seed in enumerate(direction_seeds):
            for condition_index, condition_id in enumerate(conditions):
                for target_index, target_id in enumerate(target_ids):
                    tensor[layer_index, seed_index, condition_index, target_index] = (
                        vectors[(int(layer), float(strength), int(seed), condition_id, target_id)]
                    )
    return tensor


def _stack_panels(
    panels: Sequence[Mapping[str, Any]],
    *,
    layers: Sequence[int],
    direction_seeds: Sequence[int],
    strength: float,
    target_ids: Sequence[str],
) -> np.ndarray:
    """Materialize all panels as [panel, layer, seed, condition, target, dim]."""

    tensors = [
        _panel_tensor(
            panel,
            layers=layers,
            direction_seeds=direction_seeds,
            strength=strength,
            target_ids=target_ids,
        )
        for panel in panels
    ]
    shape = tensors[0].shape
    if any(tensor.shape != shape for tensor in tensors[1:]):
        raise DependenceSensitivityError(
            "Stored panel fingerprints cannot be aligned to one common tensor shape"
        )
    return np.stack(tensors, axis=0)


def _stratified_bootstrap_weights(
    *,
    replicates: int,
    seed: int,
    target_count: int,
    group_indices: Sequence[Sequence[int]],
) -> np.ndarray:
    """Generate one joint multiplicity matrix for all panels, layers, and seeds."""

    if replicates <= 0:
        raise DependenceSensitivityError("Bootstrap replicate count must be positive")
    weights = np.zeros((int(replicates), int(target_count)), dtype=np.int16)
    rng = np.random.default_rng(int(seed))
    replicate_rows = np.arange(int(replicates), dtype=np.int64)
    for raw_indices in group_indices:
        indices = np.asarray(raw_indices, dtype=np.int64)
        if indices.size == 0:
            raise DependenceSensitivityError("A bootstrap target stratum is empty")
        draws = rng.integers(0, indices.size, size=(int(replicates), indices.size))
        for draw_column in range(indices.size):
            np.add.at(
                weights,
                (replicate_rows, indices[draws[:, draw_column]]),
                1,
            )
    expected = sum(len(indices) for indices in group_indices)
    if not np.all(weights.sum(axis=1) == expected):
        raise DependenceSensitivityError("Bootstrap multiplicities have invalid totals")
    return weights


def _score_layer_chunk(
    layer_vectors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> np.ndarray:
    """Rebuild prototypes and return one adjusted layer mean per replicate.

    ``layer_vectors`` has shape [panel, seed, condition, target, dimension].
    The same target multiplicities are used for every panel and seed.  For each
    held-out group, its prototype excludes the complete group and is rebuilt
    from the weighted targets in the other five groups.
    """

    if layer_vectors.ndim != 5:
        raise DependenceSensitivityError("Layer fingerprint tensor must have five axes")
    panel_count, seed_count, condition_count, target_count, dimension = (
        layer_vectors.shape
    )
    if panel_count != 4:
        raise DependenceSensitivityError("Exactly four aligned panels are required")
    if seed_count <= 0 or condition_count <= 1 or dimension <= 0:
        raise DependenceSensitivityError("Fingerprint tensor has an invalid shape")
    if weights.ndim != 2 or weights.shape[1] != target_count:
        raise DependenceSensitivityError("Bootstrap weights do not match the target grid")

    batch_size = weights.shape[0]
    panel_target_scores = np.empty(
        (batch_size, panel_count, target_count), dtype=np.float64
    )
    floating_weights = weights.astype(np.float64, copy=False)

    # One weighted sum over all targets is shared by all held-out groups.
    # [B,T] x [P,S,C,T,D] -> [B,P,S,C,D]
    total_sums = np.einsum(
        "bt,psctd->bpscd",
        floating_weights,
        layer_vectors,
        optimize=True,
    )

    for raw_indices in group_indices:
        held_indices = np.asarray(raw_indices, dtype=np.int64)
        held_vectors = layer_vectors[:, :, :, held_indices, :]
        # Remove the resampled multiplicity of the complete held-out group.
        held_sums = np.einsum(
            "bh,pschd->bpscd",
            floating_weights[:, held_indices],
            held_vectors,
            optimize=True,
        )
        training_sums = total_sums - held_sums
        prototype_norms = np.linalg.norm(training_sums, axis=-1, keepdims=True)
        if np.any(prototype_norms <= EPSILON) or not np.all(np.isfinite(prototype_norms)):
            raise DependenceSensitivityError(
                "A resampled leave-one-group-out prototype has zero or non-finite norm"
            )
        prototypes = training_sums / prototype_norms

        # For C conditions, the endpoint
        # mean_c[cos(x_c,p_c) - mean_{k!=c} cos(x_c,p_k)] equals
        # (C*sum_c cos(x_c,p_c) - sum_{c,k} cos(x_c,p_k))/(C*(C-1)).
        same_sum = np.einsum(
            "bpscd,pschd->bpsh",
            prototypes,
            held_vectors,
            optimize=True,
        )
        all_sum = np.einsum(
            "bpsd,pshd->bpsh",
            prototypes.sum(axis=3),
            held_vectors.sum(axis=2),
            optimize=True,
        )
        seed_scores = (
            condition_count * same_sum - all_sum
        ) / (condition_count * (condition_count - 1))
        panel_target_scores[:, :, held_indices] = seed_scores.mean(axis=2)

    target_effects = panel_target_scores[:, 0] - np.median(
        panel_target_scores[:, 1:4], axis=1
    )
    weighted_effect_sum = np.sum(floating_weights * target_effects, axis=1)
    total_multiplicity = np.sum(floating_weights, axis=1)
    if np.any(total_multiplicity <= 0):
        raise DependenceSensitivityError("A bootstrap replicate has no target observations")
    return weighted_effect_sum / total_multiplicity


def _dependence_aware_bootstrap(
    panel_tensors: np.ndarray,
    weights: np.ndarray,
    group_indices: Sequence[Sequence[int]],
    *,
    chunk_size: int,
) -> np.ndarray:
    """Return [layer, replicate] means with replicate-wise refitted prototypes."""

    if panel_tensors.ndim != 6:
        raise DependenceSensitivityError("Panel tensor must have six axes")
    if chunk_size <= 0:
        raise DependenceSensitivityError("Chunk size must be positive")
    layer_count = panel_tensors.shape[1]
    distributions = np.empty((layer_count, weights.shape[0]), dtype=np.float64)
    for layer_index in range(layer_count):
        for start in range(0, weights.shape[0], int(chunk_size)):
            stop = min(start + int(chunk_size), weights.shape[0])
            distributions[layer_index, start:stop] = _score_layer_chunk(
                panel_tensors[:, layer_index],
                weights[start:stop],
                group_indices,
            )
    if not np.all(np.isfinite(distributions)):
        raise DependenceSensitivityError("Bootstrap distribution contains non-finite values")
    return distributions


def _point_estimates(
    panel_tensors: np.ndarray,
    group_indices: Sequence[Sequence[int]],
) -> np.ndarray:
    weights = np.ones((1, panel_tensors.shape[4]), dtype=np.int16)
    return np.asarray(
        [
            _score_layer_chunk(panel_tensors[:, layer_index], weights, group_indices)[0]
            for layer_index in range(panel_tensors.shape[1])
        ],
        dtype=np.float64,
    )


def _fixed_score_bootstrap_for_comparison(
    panels: Sequence[Mapping[str, Any]],
    *,
    layers: Sequence[int],
    strength: float,
    direction_seeds: Sequence[int],
    target_ids: Sequence[str],
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce v1's fixed-prototype resampling under the same joint draws."""

    point_effects = np.empty((len(layers), len(target_ids)), dtype=np.float64)
    for layer_index, layer in enumerate(layers):
        panel_scores = [
            frozen_v1._panel_target_scores(
                panel,
                layer=int(layer),
                strength=float(strength),
                direction_seeds=direction_seeds,
            )[0]
            for panel in panels
        ]
        for target_index, target_id in enumerate(target_ids):
            point_effects[layer_index, target_index] = panel_scores[0][target_id] - float(
                np.median([scores[target_id] for scores in panel_scores[1:]])
            )
    distributions = np.einsum(
        "bt,lt->lb", weights.astype(np.float64), point_effects, optimize=True
    ) / weights.sum(axis=1)[None, :]
    return point_effects, distributions


def _input_record(panel: Mapping[str, Any]) -> dict[str, Any]:
    record = frozen_v1._input_record(panel)
    # Paths are intentionally omitted; hashes and run labels make the output
    # relocatable while binding it to exact stored evidence.
    return record


def _load_strict_panels(
    primary_run: Path,
    matched_null_runs: Sequence[Path],
    *,
    fingerprint_dim: int,
) -> list[dict[str, Any]]:
    if len(matched_null_runs) != 3:
        raise DependenceSensitivityError(
            f"Exactly three matched-null runs are required; observed {len(matched_null_runs)}"
        )
    roles = (
        "primary_colored_shapes",
        "matched_null_a",
        "matched_null_b",
        "matched_null_c",
    )
    run_dirs = (Path(primary_run), *(Path(path) for path in matched_null_runs))
    if len({path.resolve() for path in run_dirs}) != 4:
        raise DependenceSensitivityError("The four run directories must be distinct")
    try:
        panels = [
            frozen_v1._load_panel(
                run_dir,
                label=role,
                fingerprint_dim=int(fingerprint_dim),
                fingerprint_seed=frozen_v1.DEFAULT_FINGERPRINT_SEED,
                layers=frozen_v1.DEFAULT_LAYERS,
                strength=frozen_v1.DEFAULT_STRENGTH,
                direction_seeds=frozen_v1.DEFAULT_DIRECTION_SEEDS,
                expected_targets_per_group=frozen_v1.DEFAULT_TARGETS_PER_GROUP,
            )
            for role, run_dir in zip(roles, run_dirs)
        ]
        frozen_v1._validate_cross_panel_grids(panels)
        frozen_groups, _ = frozen_v1._load_frozen_target_groups()
    except frozen_v1.M2AnalysisError as exc:
        raise DependenceSensitivityError(str(exc)) from exc
    if panels[0]["targets"] != frozen_groups:
        raise DependenceSensitivityError(
            "Ledger target IDs/groups do not match the hash-pinned P2 target bank"
        )
    condition_sets = [set(panel["conditions"]) for panel in panels]
    for left in range(len(condition_sets)):
        for right in range(left + 1, len(condition_sets)):
            if condition_sets[left] & condition_sets[right]:
                raise DependenceSensitivityError(
                    "Condition IDs must remain disjoint across the four fixed panels"
                )
    return panels


def _markdown_report(receipt: Mapping[str, Any]) -> str:
    lines = [
        "# Milestone 2 post-hoc dependence-aware sensitivity v1",
        "",
        "This is a **post-hoc sensitivity analysis**, not a preregistered",
        "confirmatory analysis. It does not overwrite or reclassify the frozen v1",
        "confirmatory statuses.",
        "",
        "## Method",
        "",
        "Each replicate samples eight targets with replacement inside each of the",
        "six frozen target groups. One joint target-multiplicity vector is used for",
        "the primary panel, null panels A/B/C, both layers, and all three fixed",
        "direction seeds. Inside the replicate, every condition prototype is rebuilt",
        "from the resampled targets in the other five groups. Target scores are then",
        "recomputed, direction seeds are averaged within target, the targetwise median",
        "of A/B/C is subtracted from the primary score, and the resulting target",
        "effects are averaged using the replicate multiplicities.",
        "",
        "## Results",
        "",
        "| Layer | Point mean | Rebuilt-prototype 95% interval | Fixed-prototype 95% interval on identical draws |",
        "|---:|---:|:---:|:---:|",
    ]
    for result in receipt["results"]:
        lines.append(
            f"| {result['layer']} | {result['point_mean_adjusted_effect']:.8f} | "
            f"[{result['dependence_aware_percentile_interval_95']['low']:.8f}, "
            f"{result['dependence_aware_percentile_interval_95']['high']:.8f}] | "
            f"[{result['fixed_prototype_comparison_interval_95']['low']:.8f}, "
            f"{result['fixed_prototype_comparison_interval_95']['high']:.8f}] |"
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The method and all interpretation were specified after the P2 outcomes",
            "  were available. The intervals are descriptive sensitivity intervals.",
            "- The empirical target bank is treated as the resampling population; six",
            "  target-group labels and fixed group sizes are conditioned on.",
            "- Panels A/B/C and the three direction seeds are fixed, not sampled from",
            "  broader populations. Joint resampling preserves their target alignment",
            "  but does not quantify panel-selection or seed-selection uncertainty.",
            "- A percentile bootstrap does not by itself justify a hypothesis-test or",
            "  practical-equivalence decision. No p-value, Holm adjustment, or status",
            "  is produced here.",
            "- This analysis is pre-causal and does not establish a tokenization-free,",
            "  semantic, mechanistic, or causal glyph effect.",
            "",
            "The report was generated from stored fingerprints; no model forward pass",
            "and no C1 holdout access occurred.",
            "",
        ]
    )
    return "\n".join(lines)


def analyze_dependence_sensitivity(
    primary_run: Path | None,
    matched_null_runs: Sequence[Path] | None,
    *,
    output_dir: Path,
    bootstrap_replicates: int = DEFAULT_BOOTSTRAP_REPLICATES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    panels: Sequence[Mapping[str, Any]] | None = None,
    fingerprint_dim: int = frozen_v1.DEFAULT_FINGERPRINT_DIM,
    strict_inputs: bool = True,
) -> dict[str, Any]:
    """Run the versioned post-hoc sensitivity and write a receipt and report.

    ``panels`` and ``strict_inputs=False`` exist only for small synthetic tests.
    The command-line interface always validates the frozen P2 evidence.
    """

    if panels is None:
        if primary_run is None or matched_null_runs is None:
            raise DependenceSensitivityError("Four run directories are required")
        panels = _load_strict_panels(
            primary_run,
            matched_null_runs,
            fingerprint_dim=int(fingerprint_dim),
        )
    elif strict_inputs:
        raise DependenceSensitivityError(
            "Injected panels are permitted only for non-strict synthetic validation"
        )
    panels = list(panels)
    if len(panels) != 4:
        raise DependenceSensitivityError("Exactly four panels are required")
    try:
        frozen_v1._validate_cross_panel_grids(panels)
    except frozen_v1.M2AnalysisError as exc:
        raise DependenceSensitivityError(str(exc)) from exc

    target_groups: Mapping[str, str] = panels[0]["targets"]
    target_ids, group_indices = _ordered_target_grid(target_groups)
    panel_tensors = _stack_panels(
        panels,
        layers=frozen_v1.DEFAULT_LAYERS,
        direction_seeds=frozen_v1.DEFAULT_DIRECTION_SEEDS,
        strength=frozen_v1.DEFAULT_STRENGTH,
        target_ids=target_ids,
    )
    weights = _stratified_bootstrap_weights(
        replicates=int(bootstrap_replicates),
        seed=int(bootstrap_seed),
        target_count=len(target_ids),
        group_indices=group_indices,
    )
    point_estimates = _point_estimates(panel_tensors, group_indices)
    distributions = _dependence_aware_bootstrap(
        panel_tensors,
        weights,
        group_indices,
        chunk_size=int(chunk_size),
    )
    point_effects, fixed_distributions = _fixed_score_bootstrap_for_comparison(
        panels,
        layers=frozen_v1.DEFAULT_LAYERS,
        strength=frozen_v1.DEFAULT_STRENGTH,
        direction_seeds=frozen_v1.DEFAULT_DIRECTION_SEEDS,
        target_ids=target_ids,
        weights=weights,
    )
    fixed_point_means = point_effects.mean(axis=1)
    if not np.allclose(point_estimates, fixed_point_means, rtol=0.0, atol=2e-12):
        raise DependenceSensitivityError(
            "The tensorized point endpoint does not reproduce the frozen endpoint"
        )

    results: list[dict[str, Any]] = []
    for layer_index, layer in enumerate(frozen_v1.DEFAULT_LAYERS):
        low, high = np.quantile(distributions[layer_index], (0.025, 0.975))
        fixed_low, fixed_high = np.quantile(
            fixed_distributions[layer_index], (0.025, 0.975)
        )
        results.append(
            {
                "layer": int(layer),
                "point_mean_adjusted_effect": float(point_estimates[layer_index]),
                "dependence_aware_percentile_interval_95": {
                    "low": float(low),
                    "high": float(high),
                    "replicates": int(bootstrap_replicates),
                    "seed": int(bootstrap_seed),
                },
                "fixed_prototype_comparison_interval_95": {
                    "low": float(fixed_low),
                    "high": float(fixed_high),
                    "same_resample_weights": True,
                },
                "bootstrap_distribution_descriptives": {
                    "mean": float(np.mean(distributions[layer_index])),
                    "standard_deviation_ddof1": float(
                        np.std(distributions[layer_index], ddof=1)
                    ),
                    "minimum": float(np.min(distributions[layer_index])),
                    "maximum": float(np.max(distributions[layer_index])),
                },
                "confirmatory_status_assigned": False,
            }
        )

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "m2_dependence_sensitivity_report.md"
    bootstrap_path = output_dir / "m2_dependence_sensitivity_bootstrap.jsonl"
    receipt_path = output_dir / "m2_dependence_sensitivity_receipt.json"
    bootstrap_rows = [
        {
            "analysis_id": ANALYSIS_ID,
            "replicate_index": replicate_index,
            "layer_mean_adjusted_effects": {
                str(layer): float(distributions[layer_index, replicate_index])
                for layer_index, layer in enumerate(frozen_v1.DEFAULT_LAYERS)
            },
        }
        for replicate_index in range(int(bootstrap_replicates))
    ]
    _write_jsonl(bootstrap_path, bootstrap_rows)
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analysis_id": ANALYSIS_ID,
        "protocol_conformant": False,
        "post_hoc": True,
        "overwrites_frozen_v1_status": False,
        "analysis": (
            "stratified target bootstrap with replicate-wise refitting of all "
            "leave-one-target-group-out condition prototypes"
        ),
        "inputs": [_input_record(panel) for panel in panels],
        "parameters": {
            "layers": list(frozen_v1.DEFAULT_LAYERS),
            "strength": frozen_v1.DEFAULT_STRENGTH,
            "direction_seeds": list(frozen_v1.DEFAULT_DIRECTION_SEEDS),
            "fingerprint_dim": int(fingerprint_dim),
            "bootstrap_replicates": int(bootstrap_replicates),
            "bootstrap_seed": int(bootstrap_seed),
            "chunk_size_computational_only": int(chunk_size),
        },
        "resampling_method": {
            "observation_unit": "target",
            "strata": list(frozen_v1.EXPECTED_TARGET_GROUPS),
            "draws_per_stratum": [len(indices) for indices in group_indices],
            "with_replacement": True,
            "joint_target_multiplicities_across_panels_layers_and_seeds": True,
            "prototype_rebuilt_inside_each_replicate": True,
            "prototype_training_set": (
                "resampled targets from all five groups other than the evaluated "
                "target's complete held-out group"
            ),
            "seed_aggregation": "arithmetic mean within target after prototype refit",
            "null_aggregation": "targetwise median of matched-null panels A/B/C",
            "layer_statistic": (
                "multiplicity-weighted mean of primary-minus-null-median target effects"
            ),
            "interval": "2.5th and 97.5th percentiles of rebuilt-prototype replicates",
            "seed_reused_from_frozen_v1_for_paired_method_comparison": True,
            "seed_choice_preregistered_for_this_method": False,
        },
        "validation": {
            "stored_fingerprints_sufficient_for_exact_refit": True,
            "tensor_point_estimate_matches_fixed_v1_endpoint_atol": 2e-12,
            "strict_frozen_p2_evidence_validation": bool(strict_inputs),
            "model_forward_passes": 0,
            "c1_holdout_accessed": False,
            "analyzer_file": Path(__file__).name,
            "analyzer_sha256": _sha256_file(Path(__file__)),
            "frozen_v1_analyzer_dependency_file": Path(frozen_v1.__file__).name,
            "frozen_v1_analyzer_dependency_sha256": _sha256_file(
                Path(frozen_v1.__file__)
            ),
            "python_version": sys.version.split()[0],
            "numpy_version": np.__version__,
            "orjson_version": orjson.__version__,
        },
        "results": results,
        "inference_boundary": {
            "p_values_computed": False,
            "multiplicity_adjustment_computed": False,
            "confirmatory_status_computed": False,
            "practical_equivalence_status_computed": False,
            "interpretation": (
                "post-hoc dependence sensitivity conditional on the fixed panels, "
                "fixed seeds, fixed group labels, and empirical P2 target bank"
            ),
        },
        "limitations": [
            "The method was specified after P2 outcomes were available.",
            "The target bank is treated as the empirical resampling population.",
            "Panel-selection and direction-seed-selection uncertainty are not estimated.",
            "Percentile sensitivity intervals do not supply a confirmatory decision rule.",
            "The analysis does not establish semantics, mechanism, or causality.",
        ],
    }
    report = _markdown_report(receipt)
    _atomic_write(report_path, report.encode("utf-8"))
    receipt["outputs"] = {
        "bootstrap_layer_means": {
            "file": bootstrap_path.name,
            "sha256": _sha256_file(bootstrap_path),
            "row_count": len(bootstrap_rows),
        },
        "report": {
            "file": report_path.name,
            "sha256": _sha256_file(report_path),
        }
    }
    _write_json(receipt_path, receipt)
    return receipt


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-run", type=Path, required=True)
    parser.add_argument(
        "--matched-null-runs",
        type=Path,
        nargs=3,
        metavar=("NULL_A", "NULL_B", "NULL_C"),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        receipt = analyze_dependence_sensitivity(
            args.primary_run,
            args.matched_null_runs,
            output_dir=args.output_dir,
        )
    except (DependenceSensitivityError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = {
        "analysis_id": ANALYSIS_ID,
        "post_hoc": True,
        "receipt": str(
            Path(args.output_dir).resolve() / "m2_dependence_sensitivity_receipt.json"
        ),
        "intervals": {
            str(result["layer"]): result["dependence_aware_percentile_interval_95"]
            for result in receipt["results"]
        },
    }
    print(orjson.dumps(summary).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
