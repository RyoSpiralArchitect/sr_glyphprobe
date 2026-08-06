#!/usr/bin/env python3
"""Post-hoc CountSketch folding and matched-panel descriptive comparisons.

The intervention ledger stores normalized CountSketch fingerprints, not raw
logit deltas.  For the same hash seed, a D-dimensional CountSketch can be
folded exactly (up to stored floating-point rounding) to d dimensions when d
divides D: bucket ``b`` in the stored sketch contributes to ``b % d``.  The
folded vector is then renormalized.

This script deliberately fails closed for a new hash seed or a non-divisor
dimension because neither transformation can be recovered from normalized
stored fingerprints without raw logit deltas.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import orjson
import yaml


DEFAULT_FINGERPRINT_SEED = 8_675_309
DEFAULT_SPLIT_HALF_REPEATS = 200
DEFAULT_LABEL_PERMUTATIONS = 1_000
EPSILON = 1e-12


class SensitivityError(ValueError):
    """Raised when stored artifacts cannot support the requested analysis."""


def _json_bytes(value: Any, *, pretty: bool = False) -> bytes:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, option=option)


def _stable_hash(value: Any, *, length: int = 16) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()[:length]


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


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = b"".join(_json_bytes(row) + b"\n" for row in rows)
    _atomic_write(path, payload)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SensitivityError(f"JSONL input does not exist: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise SensitivityError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise SensitivityError(f"Expected an object at {path}:{line_number}")
            rows.append(value)
    return rows


def validate_fold_request(
    *,
    source_dim: int,
    target_dim: int,
    source_seed: int,
    target_seed: int,
) -> None:
    """Validate that a stored normalized sketch can be folded as requested."""

    if source_dim <= 0 or target_dim <= 0:
        raise SensitivityError("CountSketch dimensions must be positive")
    if target_seed != source_seed:
        raise SensitivityError(
            "A new CountSketch seed cannot be reconstructed from a stored normalized "
            f"fingerprint (stored seed {source_seed}, requested seed {target_seed}); "
            "raw logit deltas or a new forward pass are required."
        )
    if target_dim > source_dim or source_dim % target_dim != 0:
        raise SensitivityError(
            f"Target dimension {target_dim} is not a divisor of stored dimension "
            f"{source_dim}; existing bucket collisions cannot be unmixed without raw "
            "logit deltas."
        )


def fold_normalized_countsketch(
    fingerprint: Sequence[float] | np.ndarray,
    target_dim: int,
    *,
    source_seed: int,
    target_seed: int | None = None,
    epsilon: float = EPSILON,
) -> np.ndarray:
    """Fold one normalized CountSketch to a same-seed divisor dimension.

    If ``y = raw_D / ||raw_D||``, summing ``y[b]`` into ``b % d`` yields
    ``raw_d / ||raw_D||``.  Renormalization therefore yields the same normalized
    d-dimensional CountSketch that would have been computed from the raw input.
    """

    vector = np.asarray(fingerprint, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0:
        raise SensitivityError("Fingerprint must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(vector)):
        raise SensitivityError("Fingerprint contains non-finite values")
    resolved_target_seed = source_seed if target_seed is None else int(target_seed)
    validate_fold_request(
        source_dim=int(vector.size),
        target_dim=int(target_dim),
        source_seed=int(source_seed),
        target_seed=resolved_target_seed,
    )
    folded = np.zeros(int(target_dim), dtype=np.float64)
    np.add.at(folded, np.arange(vector.size) % int(target_dim), vector)
    norm = float(np.linalg.norm(folded))
    if norm > epsilon:
        folded /= norm
    return folded.astype(np.float32)


def _extract_fingerprint(row: dict[str, Any], *, line_number: int) -> np.ndarray:
    distribution = row.get("distribution")
    if isinstance(distribution, dict) and distribution.get("fingerprint") is not None:
        value = distribution["fingerprint"]
    else:
        value = row.get("fingerprint")
    if value is None:
        raise SensitivityError(
            f"Row {line_number} has no fingerprint. Aggregate fingerprint_summary.jsonl "
            "cannot be refolded; supply interventions.jsonl or compact per-target rows."
        )
    vector = np.asarray(value, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise SensitivityError(f"Row {line_number} has an invalid fingerprint vector")
    return vector


def compact_fingerprint_rows(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select eligible per-target rows and normalize their on-disk shape.

    Full intervention-ledger rows and compact rows with a top-level
    ``fingerprint`` field are accepted.  A compact row must retain the cell,
    condition, target, and target-group identifiers needed by the split-half
    statistic.
    """

    required = ("layer", "strength", "seed", "condition_type", "condition_id", "target_id")
    compact: list[dict[str, Any]] = []
    source_dim: int | None = None
    seen: set[tuple[int, float, int, str, str, str]] = set()
    for line_number, row in enumerate(rows, start=1):
        if "sign" in row and row.get("sign") != 1:
            continue
        if "calibration" in row and row.get("calibration") != "rms":
            continue
        missing = [field for field in required if field not in row]
        if missing:
            raise SensitivityError(
                f"Row {line_number} is missing required fields: {', '.join(missing)}"
            )
        vector = _extract_fingerprint(row, line_number=line_number)
        if source_dim is None:
            source_dim = int(vector.size)
        elif vector.size != source_dim:
            raise SensitivityError(
                f"Mixed fingerprint dimensions: expected {source_dim}, found "
                f"{vector.size} at row {line_number}"
            )
        normalized = {
            "layer": int(row["layer"]),
            "strength": float(row["strength"]),
            "seed": int(row["seed"]),
            "condition_type": str(row["condition_type"]),
            "condition_id": str(row["condition_id"]),
            "target_id": str(row["target_id"]),
            "target_group": str(row.get("target_group", "unspecified")),
            "fingerprint": vector,
        }
        key = (
            normalized["layer"],
            normalized["strength"],
            normalized["seed"],
            normalized["condition_type"],
            normalized["condition_id"],
            normalized["target_id"],
        )
        if key in seen:
            raise SensitivityError(f"Duplicate condition-target row at input row {line_number}: {key}")
        seen.add(key)
        compact.append(normalized)
    if not compact:
        raise SensitivityError("No eligible +1-sign RMS fingerprint rows were found")
    return compact


def fold_rows(
    rows: Sequence[dict[str, Any]],
    target_dim: int,
    *,
    source_seed: int,
    target_seed: int | None = None,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        folded = fold_normalized_countsketch(
            row["fingerprint"],
            target_dim,
            source_seed=source_seed,
            target_seed=target_seed,
        )
        output.append({**row, "fingerprint": folded})
    return output


def _cosine(first: np.ndarray, second: np.ndarray) -> float:
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    return float(np.dot(first, second) / denominator) if denominator > EPSILON else 0.0


def _stratified_half_split(
    target_ids: Sequence[str], groups: dict[str, str], *, seed: int
) -> tuple[list[str], list[str]]:
    by_group: dict[str, list[str]] = defaultdict(list)
    for target_id in target_ids:
        by_group[groups.get(target_id, "unspecified")].append(target_id)
    first: list[str] = []
    second: list[str] = []
    for group, group_targets in sorted(by_group.items()):
        ordered = sorted(
            group_targets,
            key=lambda target_id: _stable_hash(
                {"seed": seed, "group": group, "target_id": target_id}, length=24
            ),
        )
        first.extend(ordered[::2])
        second.extend(ordered[1::2])
    if not first or not second:
        ordered = sorted(
            target_ids,
            key=lambda target_id: _stable_hash(
                {"seed": seed, "target_id": target_id}, length=24
            ),
        )
        midpoint = max(1, len(ordered) // 2)
        first, second = ordered[:midpoint], ordered[midpoint:]
    return first, second


def _common_targets(values: dict[str, dict[str, np.ndarray]]) -> list[str]:
    if not values:
        return []
    return sorted(set.intersection(*(set(targets) for targets in values.values())))


def _mean_vectors(
    values: dict[str, dict[str, np.ndarray]], target_ids: Sequence[str]
) -> dict[str, np.ndarray]:
    means: dict[str, np.ndarray] = {}
    for condition_id, target_map in values.items():
        vectors = [target_map[target_id] for target_id in target_ids if target_id in target_map]
        if not vectors:
            continue
        mean = np.asarray(vectors, dtype=np.float64).mean(axis=0)
        norm = float(np.linalg.norm(mean))
        means[condition_id] = mean / norm if norm > EPSILON else mean
    return means


def _fingerprint_separation(
    values: dict[str, dict[str, np.ndarray]],
    first_targets: Sequence[str],
    second_targets: Sequence[str],
) -> dict[str, Any]:
    if len(values) < 2 or not first_targets or not second_targets:
        return {
            "available": False,
            "same": None,
            "cross": None,
            "separation": None,
            "condition_count": len(values),
        }
    first = _mean_vectors(values, first_targets)
    second = _mean_vectors(values, second_targets)
    common = sorted(set(first) & set(second))
    if len(common) < 2:
        return {
            "available": False,
            "same": None,
            "cross": None,
            "separation": None,
            "condition_count": len(common),
        }
    same = [_cosine(first[key], second[key]) for key in common]
    cross = [
        _cosine(first[left], second[right])
        for left in common
        for right in common
        if left != right
    ]
    same_mean = float(np.mean(same))
    cross_mean = float(np.mean(cross))
    return {
        "available": True,
        "same": same_mean,
        "cross": cross_mean,
        "separation": same_mean - cross_mean,
        "condition_count": len(common),
    }


def _permute_within_target(
    values: dict[str, dict[str, np.ndarray]],
    target_ids: Sequence[str],
    *,
    rng: np.random.Generator,
) -> dict[str, dict[str, np.ndarray]]:
    condition_ids = sorted(values)
    permuted = {condition_id: {} for condition_id in condition_ids}
    for target_id in target_ids:
        source_ids = [condition_id for condition_id in condition_ids if target_id in values[condition_id]]
        shuffled = list(rng.permutation(source_ids))
        for destination, source in zip(source_ids, shuffled):
            permuted[destination][target_id] = values[source][target_id]
    return permuted


def _condition_statistics(
    rows: Sequence[dict[str, Any]],
    *,
    split_seed: int,
    repeat_count: int,
    permutation_count: int,
) -> dict[str, Any]:
    values: dict[str, dict[str, np.ndarray]] = defaultdict(dict)
    groups: dict[str, str] = {}
    for row in rows:
        target_id = row["target_id"]
        target_group = row["target_group"]
        if target_id in groups and groups[target_id] != target_group:
            raise SensitivityError(
                f"Target {target_id!r} has inconsistent groups: "
                f"{groups[target_id]!r} and {target_group!r}"
            )
        groups[target_id] = target_group
        values[row["condition_id"]][target_id] = np.asarray(row["fingerprint"], dtype=np.float64)
    target_ids = _common_targets(values)
    first, second = _stratified_half_split(target_ids, groups, seed=split_seed)
    point = _fingerprint_separation(values, first, second)
    if not point["available"]:
        return {
            **point,
            "target_count": len(target_ids),
            "repeat_mean": None,
            "repeat_median": None,
            "repeat_ci_low": None,
            "repeat_ci_high": None,
            "repeat_count": 0,
            "permutation_p_greater_equal": None,
            "permutation_null_mean": None,
            "permutation_null_std": None,
            "permutation_count": 0,
        }
    repeat_values: list[float] = []
    for index in range(max(int(repeat_count), 0)):
        repeat_first, repeat_second = _stratified_half_split(
            target_ids, groups, seed=split_seed + 104_729 * (index + 1)
        )
        score = _fingerprint_separation(values, repeat_first, repeat_second)
        if score["available"]:
            repeat_values.append(float(score["separation"]))
    rng = np.random.default_rng(split_seed + 2_147_483_647)
    null_values: list[float] = []
    for _ in range(max(int(permutation_count), 0)):
        permuted = _permute_within_target(values, target_ids, rng=rng)
        score = _fingerprint_separation(permuted, first, second)
        if score["available"]:
            null_values.append(float(score["separation"]))
    repeats = np.asarray(repeat_values, dtype=np.float64)
    nulls = np.asarray(null_values, dtype=np.float64)
    observed = float(point["separation"])
    return {
        **point,
        "target_count": len(target_ids),
        "repeat_mean": float(np.mean(repeats)) if repeats.size else None,
        "repeat_median": float(np.median(repeats)) if repeats.size else None,
        "repeat_ci_low": float(np.quantile(repeats, 0.025)) if repeats.size else None,
        "repeat_ci_high": float(np.quantile(repeats, 0.975)) if repeats.size else None,
        "repeat_count": int(repeats.size),
        "permutation_p_greater_equal": (
            float((1 + np.sum(nulls >= observed)) / (1 + nulls.size)) if nulls.size else None
        ),
        "permutation_null_mean": float(np.mean(nulls)) if nulls.size else None,
        "permutation_null_std": float(np.std(nulls)) if nulls.size else None,
        "permutation_count": int(nulls.size),
    }


def recompute_fingerprint_summaries(
    rows: Sequence[dict[str, Any]],
    *,
    fingerprint_seed: int,
    fingerprint_dim: int,
    split_half_repeats: int,
    label_permutations: int,
) -> list[dict[str, Any]]:
    """Recompute the separation portion of ``fingerprint_summary.jsonl``."""

    grouped: dict[tuple[int, float, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["layer"], row["strength"], row["seed"])].append(row)
    summaries: list[dict[str, Any]] = []
    for (layer, strength, direction_seed), cell_rows in sorted(grouped.items()):
        split_seed = int(
            _stable_hash(
                {
                    "fingerprint_seed": fingerprint_seed,
                    "layer": layer,
                    "strength": strength,
                    "direction_seed": direction_seed,
                },
                length=15,
            ),
            16,
        ) % (2**32 - 1)
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in cell_rows:
            by_type[row["condition_type"]].append(row)
        emoji = _condition_statistics(
            by_type.get("emoji", []),
            split_seed=split_seed,
            repeat_count=split_half_repeats,
            permutation_count=label_permutations,
        )
        random = _condition_statistics(
            by_type.get("random", []),
            split_seed=split_seed,
            repeat_count=split_half_repeats,
            permutation_count=0,
        )
        emoji_separation = emoji.get("separation")
        random_separation = random.get("separation")
        advantage = (
            float(emoji_separation) - float(random_separation)
            if emoji_separation is not None and random_separation is not None
            else None
        )
        summaries.append(
            {
                "layer": layer,
                "strength": strength,
                "seed": direction_seed,
                "split_seed": split_seed,
                "source_statistic": "same-minus-cross split-half cosine",
                "fingerprint_dim": fingerprint_dim,
                "fingerprint_seed": fingerprint_seed,
                "emoji_same_split_cosine": emoji.get("same"),
                "emoji_cross_cosine": emoji.get("cross"),
                "emoji_separation": emoji_separation,
                "emoji_condition_count": emoji.get("condition_count", 0),
                "emoji_target_count": emoji.get("target_count", 0),
                "emoji_split_repeat_mean": emoji.get("repeat_mean"),
                "emoji_split_repeat_median": emoji.get("repeat_median"),
                "emoji_split_repeat_ci_low": emoji.get("repeat_ci_low"),
                "emoji_split_repeat_ci_high": emoji.get("repeat_ci_high"),
                "emoji_split_repeat_count": emoji.get("repeat_count", 0),
                "emoji_label_permutation_p": emoji.get("permutation_p_greater_equal"),
                "emoji_label_permutation_null_mean": emoji.get("permutation_null_mean"),
                "emoji_label_permutation_null_std": emoji.get("permutation_null_std"),
                "emoji_label_permutation_count": emoji.get("permutation_count", 0),
                "random_same_split_cosine": random.get("same"),
                "random_cross_cosine": random.get("cross"),
                "random_separation": random_separation,
                "random_condition_count": random.get("condition_count", 0),
                "random_target_count": random.get("target_count", 0),
                "random_split_repeat_mean": random.get("repeat_mean"),
                "random_split_repeat_ci_low": random.get("repeat_ci_low"),
                "random_split_repeat_ci_high": random.get("repeat_ci_high"),
                "emoji_advantage_over_random": advantage,
                "claim_stage": "post-hoc-countsketch-sensitivity",
            }
        )
    return summaries


def _load_run_settings(run_dir: Path) -> dict[str, int]:
    config_path = run_dir / "resolved_config.yaml"
    if not config_path.is_file():
        raise SensitivityError(f"Missing resolved configuration: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    if not isinstance(config, dict):
        raise SensitivityError(f"Expected a mapping in {config_path}")
    metrics = config.get("metrics") or {}
    controls = config.get("controls") or {}
    return {
        "fingerprint_dim": int(metrics.get("fingerprint_dim", 96)),
        "fingerprint_seed": int(metrics.get("fingerprint_seed", DEFAULT_FINGERPRINT_SEED)),
        "split_half_repeats": int(
            metrics.get("split_half_repeats", DEFAULT_SPLIT_HALF_REPEATS)
        ),
        "label_permutations": int(
            controls.get("label_shuffle_permutations", DEFAULT_LABEL_PERMUTATIONS)
        ),
    }


def fold_run(
    run_dir: Path,
    *,
    output_dir: Path,
    target_dims: Sequence[int],
    rows_path: Path | None = None,
    target_seed: int | None = None,
    split_half_repeats: int | None = None,
    label_permutations: int | None = None,
) -> dict[str, Any]:
    """Fold a run's stored per-target fingerprints and write sensitivity summaries."""

    run_dir = run_dir.resolve()
    settings = _load_run_settings(run_dir)
    input_path = (rows_path or (run_dir / "interventions.jsonl")).resolve()
    raw_rows = _read_jsonl(input_path)
    rows = compact_fingerprint_rows(raw_rows)
    del raw_rows
    observed_dims = {int(np.asarray(row["fingerprint"]).size) for row in rows}
    if observed_dims != {settings["fingerprint_dim"]}:
        raise SensitivityError(
            "Stored fingerprint dimension does not match resolved_config.yaml: "
            f"rows={sorted(observed_dims)}, config={settings['fingerprint_dim']}"
        )
    resolved_target_seed = (
        settings["fingerprint_seed"] if target_seed is None else int(target_seed)
    )
    repeats = (
        settings["split_half_repeats"]
        if split_half_repeats is None
        else int(split_half_repeats)
    )
    permutations = (
        settings["label_permutations"]
        if label_permutations is None
        else int(label_permutations)
    )
    if repeats < 0 or permutations < 0:
        raise SensitivityError("Repeat and permutation counts must be non-negative")
    dimensions = sorted(set(int(dim) for dim in target_dims), reverse=True)
    if not dimensions:
        raise SensitivityError("At least one target dimension is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []
    for target_dim in dimensions:
        validate_fold_request(
            source_dim=settings["fingerprint_dim"],
            target_dim=target_dim,
            source_seed=settings["fingerprint_seed"],
            target_seed=resolved_target_seed,
        )
        folded = fold_rows(
            rows,
            target_dim,
            source_seed=settings["fingerprint_seed"],
            target_seed=resolved_target_seed,
        )
        summaries = recompute_fingerprint_summaries(
            folded,
            fingerprint_seed=resolved_target_seed,
            fingerprint_dim=target_dim,
            split_half_repeats=repeats,
            label_permutations=permutations,
        )
        output_path = output_dir / f"fingerprint_summary.folded-{target_dim}.jsonl"
        _write_jsonl(output_path, summaries)
        outputs.append(
            {
                "target_dim": target_dim,
                "summary_file": output_path.name,
                "summary_sha256": _sha256_file(output_path),
                "cell_count": len(summaries),
            }
        )
    receipt = {
        "schema_version": 1,
        "analysis": "same-seed-divisor-countsketch-fold",
        "input": {
            "run_label": run_dir.name,
            "rows_file": input_path.name,
            "rows_sha256": _sha256_file(input_path),
            "eligible_row_count": len(rows),
        },
        "source_dim": settings["fingerprint_dim"],
        "source_seed": settings["fingerprint_seed"],
        "target_seed": resolved_target_seed,
        "split_half_repeats": repeats,
        "label_permutations": permutations,
        "outputs": outputs,
        "algebraic_guarantee": (
            "For a same-seed divisor dimension, folding bucket b into b % target_dim "
            "and renormalizing equals direct CountSketch of the unavailable raw logit "
            "delta, up to stored fingerprint floating-point rounding."
        ),
        "unsupported_without_raw_logits": ["new CountSketch seeds", "non-divisor dimensions"],
        "summary_scope": (
            "Fingerprint split-half separation and random-direction advantage only; "
            "factor decompositions and other run summaries are not regenerated."
        ),
        "claim_stage": "post-hoc-countsketch-sensitivity",
    }
    receipt_path = output_dir / "countsketch_sensitivity.json"
    _write_json(receipt_path, receipt)
    return receipt


def _cell_key(row: dict[str, Any]) -> tuple[int, float, int]:
    try:
        return int(row["layer"]), float(row["strength"]), int(row["seed"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SensitivityError(f"Summary row has an invalid cell key: {row}") from exc


def _summary_map(path: Path, *, score_field: str) -> dict[tuple[int, float, int], float]:
    rows = _read_jsonl(path)
    output: dict[tuple[int, float, int], float] = {}
    for row in rows:
        key = _cell_key(row)
        if key in output:
            raise SensitivityError(f"Duplicate summary cell {key} in {path}")
        value = row.get(score_field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise SensitivityError(f"Cell {key} has no finite {score_field!r} in {path}")
        output[key] = float(value)
    if not output:
        raise SensitivityError(f"No summary cells found in {path}")
    return output


def _sign(value: float, *, epsilon: float) -> int:
    if value > epsilon:
        return 1
    if value < -epsilon:
        return -1
    return 0


def _midrank_percentile(value: float, null_values: Sequence[float]) -> float:
    equal_flags = [
        math.isclose(item, value, rel_tol=0.0, abs_tol=1e-15)
        for item in null_values
    ]
    below = sum(item < value and not equal for item, equal in zip(null_values, equal_flags))
    equal = sum(equal_flags)
    return float((below + 0.5 * equal) / len(null_values))


def build_matched_panel_report(
    primary_run: Path,
    matched_null_runs: Sequence[Path],
    *,
    score_field: str = "emoji_separation",
    summary_name: str = "fingerprint_summary.jsonl",
    epsilon: float = EPSILON,
) -> dict[str, Any]:
    """Build a descriptive, paired-cell primary-minus-matched-null report.

    No p-value or across-cell confidence interval is produced: cells share
    targets, directions, and often source material, so their count is not used
    as an independent sample size.
    """

    if not matched_null_runs:
        raise SensitivityError("At least one matched-null run is required")
    primary_path = primary_run / summary_name
    primary = _summary_map(primary_path, score_field=score_field)
    null_maps: list[tuple[str, Path, dict[tuple[int, float, int], float]]] = []
    labels: set[str] = set()
    for index, run_dir in enumerate(matched_null_runs, start=1):
        label = run_dir.name or f"matched-null-{index}"
        if label in labels:
            label = f"{label}-{index}"
        labels.add(label)
        path = run_dir / summary_name
        values = _summary_map(path, score_field=score_field)
        if set(values) != set(primary):
            missing = sorted(set(primary) - set(values))
            extra = sorted(set(values) - set(primary))
            raise SensitivityError(
                f"Matched-null cells do not match primary cells for {run_dir}: "
                f"missing={missing}, extra={extra}"
            )
        null_maps.append((label, path, values))

    cells: list[dict[str, Any]] = []
    for layer, strength, direction_seed in sorted(primary):
        key = (layer, strength, direction_seed)
        primary_score = primary[key]
        null_by_panel = {label: values[key] for label, _, values in null_maps}
        null_values = list(null_by_panel.values())
        null_median = float(statistics.median(null_values))
        additive_delta = primary_score - null_median
        primary_sign = _sign(primary_score, epsilon=epsilon)
        delta_sign = _sign(additive_delta, epsilon=epsilon)
        attenuation_defined = abs(primary_score) > epsilon
        relative_attenuation = (
            null_median / primary_score if attenuation_defined else None
        )
        cells.append(
            {
                "layer": layer,
                "strength": strength,
                "seed": direction_seed,
                "primary_score": primary_score,
                "matched_null_scores": null_by_panel,
                "matched_null_count": len(null_values),
                "matched_null_median": null_median,
                "additive_delta_primary_minus_null_median": additive_delta,
                "primary_midrank_percentile_within_matched_nulls": _midrank_percentile(
                    primary_score, null_values
                ),
                "relative_attenuation_null_over_primary": relative_attenuation,
                "relative_attenuation_defined": attenuation_defined,
                "primary_sign": primary_sign,
                "matched_null_median_sign": _sign(null_median, epsilon=epsilon),
                "additive_delta_sign": delta_sign,
                "sign_preserved_after_subtraction": (
                    primary_sign == delta_sign if primary_sign != 0 else None
                ),
                "sign_reversal_after_subtraction": (
                    primary_sign == -delta_sign
                    if primary_sign != 0 and delta_sign != 0
                    else False
                ),
                "matched_null_median_ge_primary": null_median >= primary_score,
            }
        )

    primary_scores = [cell["primary_score"] for cell in cells]
    null_medians = [cell["matched_null_median"] for cell in cells]
    deltas = [cell["additive_delta_primary_minus_null_median"] for cell in cells]
    sources = {
        "primary": {
            "run_label": primary_run.name,
            "summary_file": summary_name,
            "sha256": _sha256_file(primary_path),
        },
        "matched_nulls": [
            {
                "run_label": label,
                "summary_file": summary_name,
                "sha256": _sha256_file(path),
            }
            for label, path, _ in null_maps
        ],
    }
    return {
        "schema_version": 1,
        "analysis": "paired-cell-matched-panel-comparison",
        "score_field": score_field,
        "sources": sources,
        "cells": cells,
        "descriptive_summary": {
            "cell_count": len(cells),
            "primary_median": float(statistics.median(primary_scores)),
            "matched_null_median_across_cells": float(statistics.median(null_medians)),
            "additive_delta_median": float(statistics.median(deltas)),
            "positive_additive_delta_cell_count": sum(value > epsilon for value in deltas),
            "nonpositive_additive_delta_cell_count": sum(value <= epsilon for value in deltas),
        },
        "independence_boundary": {
            "cells_treated_as_independent_samples": False,
            "inferential_statistics_across_cells": False,
            "reason": (
                "Cells share targets, source-derived directions, and experimental "
                "structure. Cell counts and medians are descriptive, not an effective n."
            ),
        },
        "field_definitions": {
            "additive_delta_primary_minus_null_median": (
                "Primary panel score minus the median score across fixed matched-null panels."
            ),
            "primary_midrank_percentile_within_matched_nulls": (
                "Empirical midrank CDF of the primary score within the fixed matched-null "
                "panel scores; its resolution is limited by matched_null_count."
            ),
            "relative_attenuation_null_over_primary": (
                "Matched-null median divided by primary. This ratio is secondary and is "
                "undefined near zero; the additive delta is the preferred field."
            ),
        },
        "claim_stage": "tokenization-control-descriptive-screen",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fold = subparsers.add_parser(
        "fold", help="Fold stored per-target fingerprints to same-seed divisor dimensions"
    )
    fold.add_argument("run_dir", type=Path)
    fold.add_argument("--rows", type=Path, help="Optional compact per-target JSONL rows")
    fold.add_argument("--output-dir", type=Path, required=True)
    fold.add_argument("--target-dim", type=int, action="append", required=True)
    fold.add_argument(
        "--target-seed",
        type=int,
        help="Must equal the stored seed; a new seed fails closed without raw logits",
    )
    fold.add_argument("--split-half-repeats", type=int)
    fold.add_argument("--label-permutations", type=int)

    compare = subparsers.add_parser(
        "compare", help="Compare primary and fixed matched-null panels by paired cell"
    )
    compare.add_argument("primary_run", type=Path)
    compare.add_argument("matched_null_runs", type=Path, nargs="+")
    compare.add_argument("--output", type=Path, required=True)
    compare.add_argument(
        "--score-field",
        default="emoji_separation",
        help=(
            "Summary field to compare. The default compares the ten-condition "
            "same-minus-cross separation directly; emoji_advantage_over_random "
            "remains available as a secondary diagnostic."
        ),
    )
    compare.add_argument("--summary-name", default="fingerprint_summary.jsonl")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "fold":
            receipt = fold_run(
                args.run_dir,
                output_dir=args.output_dir,
                target_dims=args.target_dim,
                rows_path=args.rows,
                target_seed=args.target_seed,
                split_half_repeats=args.split_half_repeats,
                label_permutations=args.label_permutations,
            )
            print(orjson.dumps(receipt).decode("utf-8"))
        else:
            report = build_matched_panel_report(
                args.primary_run,
                args.matched_null_runs,
                score_field=args.score_field,
                summary_name=args.summary_name,
            )
            _write_json(args.output, report)
            print(orjson.dumps(report["descriptive_summary"]).decode("utf-8"))
    except SensitivityError as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
