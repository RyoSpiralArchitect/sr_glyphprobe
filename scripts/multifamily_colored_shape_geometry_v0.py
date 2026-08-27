#!/usr/bin/env python3
"""Run and analyze the frozen multifamily colored-shape geometry v0 cell.

The script is deliberately one coherent protocol surface. It audits the public
freeze, runs exactly one role-bound observational MLX cell, validates a sealed
run bundle, combines the two predeclared model roles, computes the exhaustive
5! square-label null, applies the two-test Holm correction, and validates the
joint analysis bundle. It never performs an activation intervention or opens a
target bank.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import itertools
import math
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import orjson
import yaml

from glyphprobe.backends.mlx_backend import MLXBackend
from glyphprobe.config import BackendConfig
from glyphprobe.provenance import implementation_receipt


PROTOCOL_ID = "glyphprobe-multifamily-colored-shape-geometry-v0"
SCHEMA_VERSION = 1
MANIFEST_PATH = Path("data/manifests/multifamily_colored_shape_geometry_v0.json")
CONFIG_PATH = Path("configs/multifamily_colored_shape_geometry_v0.yaml")
MODEL_ROLES = ("gemma2_2b_4bit", "olmo3_7b_bf16")
RUN_FILES = ("activations.npz", "observations.jsonl", "run_receipt.json")
FAILED_RUN_FILES = ("run_receipt.json",)
ANALYSIS_FILES = ("layer_statistics.jsonl", "analysis_receipt.json", "report.md")
EPSILON = 1e-12


class ProtocolError(ValueError):
    """Raised when a frozen protocol invariant is not satisfied."""


class PublishedRunFailure(RuntimeError):
    """Raised after a complete failed-run receipt has been atomically published."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    _atomic_write(path, b"".join(_json_bytes(dict(row)) + b"\n" for row in rows))


def _read_json(path: Path, description: str) -> dict[str, Any]:
    _require(path.is_file(), f"Missing {description}: {path}")
    try:
        value = orjson.loads(path.read_bytes())
    except orjson.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON in {description}: {path}") from exc
    _require(isinstance(value, dict), f"Expected object in {description}: {path}")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, Any]]:
    _require(path.is_file(), f"Missing {description}: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = orjson.loads(line)
            except orjson.JSONDecodeError as exc:
                raise ProtocolError(f"Invalid JSONL at {path}:{line_number}") from exc
            _require(isinstance(value, dict), f"Expected object at {path}:{line_number}")
            rows.append(value)
    _require(bool(rows), f"Empty {description}: {path}")
    return rows


def _read_yaml(path: Path, description: str) -> dict[str, Any]:
    _require(path.is_file(), f"Missing {description}: {path}")
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    _require(isinstance(value, dict), f"Expected mapping in {description}: {path}")
    return value


def _write_ledger(directory: Path, filenames: Sequence[str]) -> None:
    lines = [f"{_sha256_file(directory / name)}  {name}\n" for name in sorted(filenames)]
    _atomic_write(directory / "SHA256SUMS", "".join(lines).encode("utf-8"))


def _validate_ledger(directory: Path, expected_files: Sequence[str]) -> None:
    ledger = directory / "SHA256SUMS"
    _require(ledger.is_file(), f"Missing checksum ledger: {ledger}")
    observed: dict[str, str] = {}
    for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split("  ", 1)
        _require(len(parts) == 2, f"Malformed SHA256SUMS line {line_number}")
        digest, name = parts
        _require(len(digest) == 64, f"Malformed digest at SHA256SUMS:{line_number}")
        _require(name not in observed, f"Duplicate ledger entry: {name}")
        observed[name] = digest
    _require(set(observed) == set(expected_files), "Checksum ledger file roster mismatch")
    actual_files = {
        path.name for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS"
    }
    _require(actual_files == set(expected_files), "Output directory file roster mismatch")
    for name, digest in observed.items():
        _require(_sha256_file(directory / name) == digest, f"SHA-256 mismatch: {name}")


def _package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in (
        "glyphprobe",
        "mlx",
        "mlx-lm",
        "transformers",
        "numpy",
        "pydantic",
        "PyYAML",
        "orjson",
    ):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def _declared_requirements(distribution: str) -> list[str]:
    try:
        return list(importlib.metadata.requires(distribution) or [])
    except importlib.metadata.PackageNotFoundError:
        return []


def scrub_local_paths(value: Any, model_path: Path | str | None = None) -> Any:
    """Remove machine-local absolute paths from a publishable receipt."""

    replacements: list[tuple[str, str]] = []
    if model_path is not None:
        replacements.append((str(Path(model_path).resolve()), "<LOCAL_MODEL_ARTIFACT>"))
    replacements.append((str(Path.home()), "<LOCAL_HOME>"))

    if isinstance(value, dict):
        return {str(key): scrub_local_paths(item, model_path) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_local_paths(item, model_path) for item in value]
    if isinstance(value, tuple):
        return [scrub_local_paths(item, model_path) for item in value]
    if isinstance(value, Path):
        value = str(value)
    if isinstance(value, str):
        cleaned = value
        for original, replacement in replacements:
            cleaned = cleaned.replace(original, replacement)
        if cleaned.startswith("/"):
            return "<LOCAL_ABSOLUTE_PATH>"
        return cleaned
    return value


def resolve_layers(num_layers: int, fractions: Sequence[float]) -> list[int]:
    """Resolve frozen depth fractions without inspecting activation outcomes."""

    _require(num_layers > 0, "num_layers must be positive")
    resolved: list[int] = []
    for fraction in fractions:
        value = float(fraction)
        _require(0.0 <= value <= 1.0, "layer fraction outside [0, 1]")
        resolved.append(min(num_layers - 1, math.floor(value * num_layers)))
    _require(len(resolved) == len(set(resolved)), "Resolved layer fractions are not unique")
    return resolved


def shared_prefix_length(first: Sequence[int], second: Sequence[int]) -> int:
    count = 0
    for left, right in zip(first, second, strict=False):
        if int(left) != int(right):
            break
        count += 1
    return count


def minimum_shared_prefix(token_sequences: Sequence[Sequence[int]]) -> int:
    _require(len(token_sequences) >= 2, "At least two token sequences are required")
    return min(
        shared_prefix_length(token_sequences[left], token_sequences[right])
        for left in range(len(token_sequences))
        for right in range(left + 1, len(token_sequences))
    )


def shape_axis_statistic(
    circles: np.ndarray,
    squares: np.ndarray,
    permutation: Sequence[int] | None = None,
) -> float:
    """Mean off-diagonal cosine of five circle-minus-square directions."""

    circles = np.asarray(circles, dtype=np.float64)
    squares = np.asarray(squares, dtype=np.float64)
    _require(circles.ndim == 2, "Circle activation matrix must be rank two")
    _require(circles.shape == squares.shape, "Circle/square activation shapes differ")
    count = circles.shape[0]
    _require(count >= 2, "At least two colors are required")
    order = tuple(range(count)) if permutation is None else tuple(int(x) for x in permutation)
    _require(sorted(order) == list(range(count)), "Invalid square-label permutation")
    directions = circles - squares[list(order)]
    norms = np.linalg.norm(directions, axis=1)
    _require(bool(np.isfinite(directions).all()), "Nonfinite shape direction")
    _require(bool(np.all(norms > EPSILON)), "Degenerate circle-minus-square direction")
    unit = directions / norms[:, None]
    gram = unit @ unit.T
    return float((gram.sum() - count) / (count * (count - 1)))


def exhaustive_shape_axis_test(circles: np.ndarray, squares: np.ndarray) -> dict[str, Any]:
    """Compute the frozen identity pairing and all 5! square-label permutations."""

    count = int(np.asarray(circles).shape[0])
    permutations = list(itertools.permutations(range(count)))
    observed = shape_axis_statistic(circles, squares)
    null = np.asarray(
        [shape_axis_statistic(circles, squares, permutation) for permutation in permutations],
        dtype=np.float64,
    )
    tolerance = 1e-12
    exceedances = int(np.count_nonzero(null >= observed - tolerance))
    return {
        "statistic": observed,
        "permutation_count": len(permutations),
        "greater_equal_count": exceedances,
        "p_greater_equal": float(exceedances / len(permutations)),
        "null_mean": float(null.mean()),
        "null_median": float(np.median(null)),
        "null_minimum": float(null.min()),
        "null_maximum": float(null.max()),
    }


def matched_color_cosine_excess(
    activations: np.ndarray,
    panel_items: Sequence[Mapping[str, Any]],
    colors: Sequence[str],
) -> float:
    """Matched-minus-mismatched cross-shape cosine after panel centering."""

    matrix = np.asarray(activations, dtype=np.float64)
    _require(matrix.ndim == 2, "Activation matrix must be rank two")
    _require(matrix.shape[0] == len(panel_items), "Panel/activation row mismatch")
    centered = matrix - matrix.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=1)
    _require(bool(np.all(norms > EPSILON)), "Degenerate centered panel activation")
    unit = centered / norms[:, None]
    index = {
        (str(item["factors"]["color"]), str(item["factors"]["shape"])): position
        for position, item in enumerate(panel_items)
    }
    matched = [
        float(unit[index[(color, "circle")]] @ unit[index[(color, "square")]])
        for color in colors
    ]
    mismatched = [
        float(unit[index[(left, "circle")]] @ unit[index[(right, "square")]])
        for left in colors
        for right in colors
        if left != right
    ]
    return float(np.mean(matched) - np.mean(mismatched))


def holm_adjust(p_values: Mapping[str, float], alpha: float = 0.05) -> dict[str, dict[str, Any]]:
    """Holm adjusted p-values and step-down decisions for a named family."""

    _require(bool(p_values), "Empty Holm family")
    ordered = sorted((float(value), str(name)) for name, value in p_values.items())
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (value, name) in enumerate(ordered):
        _require(0.0 <= value <= 1.0, f"Invalid p-value for {name}")
        running = max(running, (count - rank) * value)
        adjusted[name] = min(1.0, running)
    decisions: dict[str, bool] = {}
    still_rejecting = True
    for rank, (value, name) in enumerate(ordered):
        threshold = alpha / (count - rank)
        decision = still_rejecting and value <= threshold
        decisions[name] = decision
        if not decision:
            still_rejecting = False
    return {
        name: {
            "raw_p": float(p_values[name]),
            "adjusted_p": adjusted[name],
            "reject": decisions[name],
            "alpha": alpha,
        }
        for name in p_values
    }


def _load_authority(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    manifest = _read_json(root / MANIFEST_PATH, "freeze manifest")
    _require(manifest.get("schema_version") == SCHEMA_VERSION, "Manifest schema mismatch")
    _require(manifest.get("protocol_id") == PROTOCOL_ID, "Manifest protocol mismatch")
    assets = manifest.get("frozen_assets")
    _require(isinstance(assets, dict) and bool(assets), "Missing frozen asset ledger")
    verified: dict[str, str] = {}
    for relative, expected in sorted(assets.items()):
        path = root / relative
        _require(path.is_file(), f"Missing frozen asset: {relative}")
        observed = _sha256_file(path)
        _require(observed == expected, f"Frozen asset SHA-256 mismatch: {relative}")
        verified[relative] = observed
    config = _read_yaml(root / CONFIG_PATH, "frozen config")
    _require(config.get("protocol_id") == PROTOCOL_ID, "Config protocol mismatch")
    return manifest, config, verified


def audit_freeze(root: Path | None = None) -> dict[str, Any]:
    root = _repo_root() if root is None else root
    manifest, config, verified = _load_authority(root)
    implementation = implementation_receipt()
    expected_implementation = manifest.get("implementation")
    _require(isinstance(expected_implementation, dict), "Missing implementation pin")
    _require(
        implementation.get("source_tree_sha256")
        == expected_implementation.get("source_tree_sha256"),
        "GlyphProbe source-tree SHA-256 mismatch",
    )
    _require(tuple(config["models"]["order"]) == MODEL_ROLES, "Model role order mismatch")
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "manifest_sha256": _sha256_file(root / MANIFEST_PATH),
        "frozen_asset_count": len(verified),
        "frozen_assets": verified,
        "implementation": implementation,
        "model_roles": list(MODEL_ROLES),
        "scientific_confirmation": False,
    }


def _load_panel(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    panel_relative = Path(str(config["panel"]["path"])).as_posix().removeprefix("../")
    panel = _read_yaml(root / panel_relative, "colored-shape panel")
    items = panel.get("items")
    _require(isinstance(items, list), "Panel items must be a list")
    expected_count = int(config["panel"]["expected_items"])
    _require(len(items) == expected_count, "Panel item count mismatch")
    colors = [str(value) for value in config["panel"]["colors"]]
    shapes = [str(value) for value in config["panel"]["shapes"]]
    seen_ids: set[str] = set()
    seen_cells: set[tuple[str, str]] = set()
    for item in items:
        _require(isinstance(item, dict), "Panel item must be a mapping")
        item_id = str(item.get("id"))
        glyph = item.get("glyph")
        factors = item.get("factors")
        _require(item_id not in seen_ids, f"Duplicate panel item: {item_id}")
        _require(isinstance(glyph, str) and glyph, f"Missing glyph: {item_id}")
        _require(isinstance(factors, dict), f"Missing factors: {item_id}")
        cell = (str(factors.get("color")), str(factors.get("shape")))
        _require(cell[0] in colors and cell[1] in shapes, f"Unexpected panel cell: {item_id}")
        _require(cell not in seen_cells, f"Duplicate color/shape cell: {cell}")
        seen_ids.add(item_id)
        seen_cells.add(cell)
    _require(seen_cells == set(itertools.product(colors, shapes)), "Incomplete color/shape cross")
    return items


def _new_stage(output: Path) -> Path:
    output = output.resolve()
    _require(not output.exists(), f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))


def _publish_stage(stage: Path, output: Path) -> None:
    os.replace(stage, output.resolve())


def _model_runtime_check(config: Mapping[str, Any]) -> dict[str, Any]:
    versions = _package_versions()
    critical = config["runtime"]["critical_versions"]
    for package, expected in critical.items():
        _require(versions.get(package) == str(expected), f"Runtime version mismatch: {package}")
    requirements = _declared_requirements("mlx-lm")
    return {
        "versions": versions,
        "mlx_lm_declared_requirements": requirements,
        "declared_transformers_requirement_conflict": any(
            requirement.startswith("transformers>=5") for requirement in requirements
        )
        and versions.get("transformers") == "4.57.6",
        "sitecustomize_loaded": "sitecustomize" in sys.modules,
        "user_site_on_sys_path": any("Library/Python" in item for item in sys.path),
    }


def run_model(model_label: str, model_path: Path, output: Path) -> dict[str, Any]:
    """Run one frozen model role and atomically publish a sealed bundle."""

    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    _require(model_label in MODEL_ROLES, f"Unknown model role: {model_label}")
    model_spec = config["models"][model_label]
    artifact_pin = manifest["model_artifacts"][model_label]
    panel_items = _load_panel(root, config)
    runtime = _model_runtime_check(config)
    stage = _new_stage(output)
    backend: MLXBackend | None = None
    started = time.perf_counter()
    try:
        backend = MLXBackend(
            BackendConfig(
                kind="mlx",
                model=str(model_path),
                device=str(config["runtime"]["device"]),
                dtype=str(config["runtime"]["dtype"]),
                local_files_only=bool(config["runtime"]["local_files_only"]),
                trust_remote_code=bool(config["runtime"]["trust_remote_code"]),
                add_special_tokens=bool(config["input"]["add_special_tokens"]),
            )
        )
        backend.load()
        loaded_at = time.perf_counter()
        receipt = backend.model_receipt()
        artifact = receipt.get("model_artifact")
        _require(isinstance(artifact, dict), "Backend omitted model artifact receipt")
        for field in ("manifest_sha256", "file_count", "total_bytes"):
            _require(artifact.get(field) == artifact_pin.get(field), f"Model artifact {field} mismatch")

        expected_type = str(model_spec["expected_model_type"])
        _require(backend.model_config.get("model_type") == expected_type, "Model type mismatch")
        _require(backend.num_layers == int(model_spec["expected_num_layers"]), "Layer count mismatch")
        _require(backend.model_dim == int(model_spec["expected_model_dim"]), "Model width mismatch")
        _require(
            receipt.get("parameter_count") == int(model_spec["expected_parameter_count"]),
            "Parameter count mismatch",
        )
        _require(
            backend.resolved_dtype == str(model_spec["expected_resolved_dtype"]),
            "Resolved dtype mismatch",
        )
        quantized = bool(
            backend.model_config.get("quantization")
            or backend.model_config.get("quantization_config")
        )
        _require(quantized is bool(model_spec["expected_quantized"]), "Quantization flag mismatch")

        fractions = [float(value) for value in config["layers"]["fractions"]]
        layers = resolve_layers(backend.num_layers, fractions)
        primary_fraction = float(config["layers"]["primary_fraction"])
        primary_layer = resolve_layers(backend.num_layers, [primary_fraction])[0]
        _require(primary_layer in layers, "Primary layer missing from fixed layer set")

        tokenizations = [backend.tokenize(str(item["glyph"])) for item in panel_items]
        expected_count = int(model_spec["expected_raw_item_token_count"])
        _require(
            all(len(record.token_ids) == expected_count for record in tokenizations),
            "Raw item token-count contract failed",
        )
        min_prefix = minimum_shared_prefix([record.token_ids for record in tokenizations])
        _require(
            min_prefix >= int(model_spec["minimum_shared_prefix_across_panel"]),
            "Shared-prefix contract failed",
        )

        activation_rows: list[np.ndarray] = []
        observations: list[dict[str, Any]] = []
        for panel_index, (item, tokenized) in enumerate(zip(panel_items, tokenizations, strict=True)):
            result = backend.forward(
                str(item["glyph"]),
                capture_layers=layers,
                site=str(config["input"]["site"]),
                position=str(config["input"]["position"]),
                return_attentions=bool(config["input"]["return_attentions"]),
            )
            _require(bool(np.isfinite(result.logits).all()), f"Nonfinite logits: {item['id']}")
            _require(
                result.logits.shape == (int(model_spec["expected_vocab_size"]),),
                f"Vocabulary/logit width mismatch: {item['id']}",
            )
            layer_vectors: list[np.ndarray] = []
            layer_rms: dict[str, float] = {}
            for layer in layers:
                vector = np.asarray(result.activations[layer], dtype=np.float32)
                _require(vector.shape == (backend.model_dim,), f"Activation width mismatch: {item['id']}")
                _require(bool(np.isfinite(vector).all()), f"Nonfinite activation: {item['id']}")
                layer_vectors.append(vector)
                layer_rms[str(layer)] = float(np.sqrt(np.mean(np.square(vector, dtype=np.float64))))
            activation_rows.append(np.stack(layer_vectors, axis=0))
            observations.append(
                {
                    "panel_index": panel_index,
                    "item_id": str(item["id"]),
                    "glyph": str(item["glyph"]),
                    "color": str(item["factors"]["color"]),
                    "shape": str(item["factors"]["shape"]),
                    "token_ids": [int(value) for value in tokenized.token_ids],
                    "token_pieces": [str(value) for value in tokenized.tokens],
                    "token_count": len(tokenized.token_ids),
                    "activation_rms_by_layer": layer_rms,
                    "logits_finite": True,
                    "logit_argmax": int(np.argmax(result.logits)),
                    "forward_latency_ms": float(result.latency_ms),
                    "peak_memory_bytes": int(result.peak_memory_bytes or 0),
                }
            )

        activations = np.stack(activation_rows, axis=0).astype(np.float32, copy=False)
        item_ids = np.asarray([str(item["id"]) for item in panel_items], dtype=np.str_)
        layer_array = np.asarray(layers, dtype=np.int64)
        np.savez_compressed(
            stage / "activations.npz",
            activations=activations,
            item_ids=item_ids,
            layers=layer_array,
        )
        _write_jsonl(stage / "observations.jsonl", observations)
        data_hashes = {
            name: _sha256_file(stage / name)
            for name in ("activations.npz", "observations.jsonl")
        }
        run_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "experiment_role": config["experiment_role"],
            "claim_boundary": config["claim_boundary"],
            "model_label": model_label,
            "canonical_model_id": model_spec["canonical_model_id"],
            "model": {
                "model_type": expected_type,
                "num_layers": backend.num_layers,
                "model_dim": backend.model_dim,
                "parameter_count": receipt["parameter_count"],
                "resolved_device": backend.resolved_device,
                "resolved_dtype": backend.resolved_dtype,
                "quantized": quantized,
                "artifact": artifact,
                "backend_receipt": scrub_local_paths(receipt, model_path),
            },
            "runtime": runtime,
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "panel": {
                "item_ids": [str(item["id"]) for item in panel_items],
                "colors": list(config["panel"]["colors"]),
                "shapes": list(config["panel"]["shapes"]),
            },
            "tokenization": {
                "context_id": config["input"]["context_id"],
                "add_special_tokens": config["input"]["add_special_tokens"],
                "expected_item_token_count": expected_count,
                "observed_item_token_counts": sorted({len(row.token_ids) for row in tokenizations}),
                "minimum_shared_prefix_across_panel": min_prefix,
                "matching_family": model_spec["matching_family"],
            },
            "capture": {
                "site": config["input"]["site"],
                "position": config["input"]["position"],
                "fractions": fractions,
                "layers": layers,
                "primary_fraction": primary_fraction,
                "primary_layer": primary_layer,
                "array_shape": list(activations.shape),
                "array_dtype": str(activations.dtype),
            },
            "execution": {
                "model_forward_calls": len(panel_items),
                "intervention_calls": 0,
                "generation_calls": 0,
                "protected_target_files_opened": 0,
                "load_elapsed_ms": (loaded_at - started) * 1000.0,
                "total_elapsed_ms_before_close": (time.perf_counter() - started) * 1000.0,
                "forward_latency_ms": [row["forward_latency_ms"] for row in observations],
                "peak_memory_bytes_max": max(row["peak_memory_bytes"] for row in observations),
                "timing_claim_authorized": False,
            },
            "outputs": data_hashes,
            "scientific_confirmation": False,
        }
        _write_json(stage / "run_receipt.json", run_receipt)
        _write_ledger(stage, RUN_FILES)
        backend.close()
        backend = None
        _publish_stage(stage, output)
        return run_receipt
    except Exception as exc:
        if backend is not None:
            backend.close()
            backend = None
        failure = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "fail",
            "model_label": model_label,
            "canonical_model_id": model_spec["canonical_model_id"],
            "error_type": type(exc).__name__,
            "error_message": scrub_local_paths(str(exc), model_path),
            "runtime": runtime,
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "execution": {
                "intervention_calls": 0,
                "generation_calls": 0,
                "protected_target_files_opened": 0,
                "scientific_result_available": False,
            },
        }
        try:
            _write_json(stage / "run_receipt.json", failure)
            _write_ledger(stage, FAILED_RUN_FILES)
            _publish_stage(stage, output)
        except Exception:
            if stage.exists():
                shutil.rmtree(stage)
            raise
        raise PublishedRunFailure(f"Failed run receipt published for {model_label}") from exc
    finally:
        if backend is not None:
            backend.close()
        if stage.exists():
            shutil.rmtree(stage)


def validate_run(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    receipt = _read_json(directory / "run_receipt.json", "run receipt")
    status = receipt.get("status")
    _require(status in {"pass", "fail"}, "Unknown run status")
    _validate_ledger(directory, RUN_FILES if status == "pass" else FAILED_RUN_FILES)
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Run protocol mismatch")
    _require(receipt.get("model_label") in MODEL_ROLES, "Run model role mismatch")
    if status == "fail":
        return {"receipt": receipt, "status": "fail"}
    with np.load(directory / "activations.npz", allow_pickle=False) as bundle:
        _require(set(bundle.files) == {"activations", "item_ids", "layers"}, "NPZ roster mismatch")
        activations = np.asarray(bundle["activations"], dtype=np.float32)
        item_ids = [str(value) for value in bundle["item_ids"].tolist()]
        layers = [int(value) for value in bundle["layers"].tolist()]
    _require(bool(np.isfinite(activations).all()), "Nonfinite sealed activation")
    _require(item_ids == receipt["panel"]["item_ids"], "Sealed item order mismatch")
    _require(layers == receipt["capture"]["layers"], "Sealed layer order mismatch")
    _require(list(activations.shape) == receipt["capture"]["array_shape"], "Array shape mismatch")
    observations = _read_jsonl(directory / "observations.jsonl", "run observations")
    _require(len(observations) == len(item_ids), "Observation row count mismatch")
    _require(
        [str(row["item_id"]) for row in observations] == item_ids,
        "Observation item order mismatch",
    )
    return {
        "status": "pass",
        "receipt": receipt,
        "activations": activations,
        "item_ids": item_ids,
        "layers": layers,
        "observations": observations,
    }


def _panel_activation_views(
    activations: np.ndarray,
    panel_items: Sequence[Mapping[str, Any]],
    colors: Sequence[str],
) -> tuple[np.ndarray, np.ndarray]:
    index = {
        (str(item["factors"]["color"]), str(item["factors"]["shape"])): position
        for position, item in enumerate(panel_items)
    }
    circles = np.stack([activations[index[(color, "circle")]] for color in colors], axis=0)
    squares = np.stack([activations[index[(color, "square")]] for color in colors], axis=0)
    return circles, squares


def _outcome_pattern(primary: Mapping[str, Mapping[str, Any]]) -> str:
    left = primary[MODEL_ROLES[0]]
    right = primary[MODEL_ROLES[1]]
    left_effect = float(left["statistic"])
    right_effect = float(right["statistic"])
    if left_effect * right_effect < 0.0:
        return "opposite_sign_heterogeneity"
    if bool(left["holm_reject"]) and bool(right["holm_reject"]) and min(left_effect, right_effect) > 0:
        return "dual_model_observational_recurrence_candidate"
    if bool(left["holm_reject"]) and not bool(right["holm_reject"]):
        return "gemma_only_heterogeneity"
    if bool(right["holm_reject"]) and not bool(left["holm_reject"]):
        return "olmo_only_heterogeneity"
    return "no_dual_model_recurrence"


def analyze_runs(run_directories: Mapping[str, Path], output: Path) -> dict[str, Any]:
    root = _repo_root()
    manifest, config, verified_assets = _load_authority(root)
    audit = audit_freeze(root)
    _require(tuple(run_directories) == MODEL_ROLES, "Analysis model role order mismatch")
    panel_items = _load_panel(root, config)
    colors = [str(value) for value in config["panel"]["colors"]]
    validated = {role: validate_run(run_directories[role]) for role in MODEL_ROLES}
    for role in MODEL_ROLES:
        _require(validated[role]["status"] == "pass", f"Cannot analyze failed role: {role}")
        receipt = validated[role]["receipt"]
        _require(receipt["model_label"] == role, f"Role binding mismatch: {role}")
        _require(
            receipt["freeze"]["manifest_sha256"] == audit["manifest_sha256"],
            f"Freeze manifest mismatch: {role}",
        )
        pin = manifest["model_artifacts"][role]
        for field in ("manifest_sha256", "file_count", "total_bytes"):
            _require(receipt["model"]["artifact"][field] == pin[field], f"Artifact pin mismatch: {role}")

    layer_rows: list[dict[str, Any]] = []
    primary_tests: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        result = validated[role]
        receipt = result["receipt"]
        activations = result["activations"]
        for layer_position, layer in enumerate(result["layers"]):
            matrix = activations[:, layer_position, :]
            circles, squares = _panel_activation_views(matrix, panel_items, colors)
            exact = exhaustive_shape_axis_test(circles, squares)
            row = {
                "model_label": role,
                "layer": layer,
                "layer_fraction": float(receipt["capture"]["fractions"][layer_position]),
                "is_primary": layer == int(receipt["capture"]["primary_layer"]),
                **exact,
                "matched_color_cross_shape_cosine_excess": matched_color_cosine_excess(
                    matrix, panel_items, colors
                ),
                "mean_activation_rms": float(
                    np.mean(np.sqrt(np.mean(np.square(matrix, dtype=np.float64), axis=1)))
                ),
                "multiplicity_decision_authorized": layer
                == int(receipt["capture"]["primary_layer"]),
            }
            layer_rows.append(row)
            if row["is_primary"]:
                primary_tests[role] = row

    _require(set(primary_tests) == set(MODEL_ROLES), "Missing primary model cell")
    holm = holm_adjust(
        {role: float(primary_tests[role]["p_greater_equal"]) for role in MODEL_ROLES},
        alpha=float(config["primary_endpoint"]["familywise_alpha"]),
    )
    primary_summary: dict[str, dict[str, Any]] = {}
    for role in MODEL_ROLES:
        primary_summary[role] = {
            "layer": int(primary_tests[role]["layer"]),
            "statistic": float(primary_tests[role]["statistic"]),
            "raw_p": float(primary_tests[role]["p_greater_equal"]),
            "holm_adjusted_p": float(holm[role]["adjusted_p"]),
            "holm_reject": bool(holm[role]["reject"]),
        }
    pattern = _outcome_pattern(primary_summary)

    stage = _new_stage(output)
    try:
        _write_jsonl(stage / "layer_statistics.jsonl", layer_rows)
        input_receipts = {
            role: {
                "run_receipt_sha256": _sha256_file(run_directories[role] / "run_receipt.json"),
                "run_ledger_sha256": _sha256_file(run_directories[role] / "SHA256SUMS"),
            }
            for role in MODEL_ROLES
        }
        analysis_receipt = {
            "schema_version": SCHEMA_VERSION,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "analysis_role": "frozen_joint_exploratory_observational_geometry",
            "claim_boundary": config["claim_boundary"],
            "freeze": {
                "manifest_sha256": audit["manifest_sha256"],
                "frozen_assets": verified_assets,
                "implementation": audit["implementation"],
            },
            "inputs": input_receipts,
            "primary_endpoint": config["primary_endpoint"],
            "primary_results": primary_summary,
            "outcome_pattern": pattern,
            "outcome_pattern_definition": config["outcome_pattern_registry"][pattern],
            "layer_row_count": len(layer_rows),
            "permutations_per_cell": math.factorial(len(colors)),
            "intervention_calls": 0,
            "generation_calls": 0,
            "protected_target_files_opened": 0,
            "confirmatory_status": False,
            "phase_i_gate_closed": False,
        }
        _write_json(stage / "analysis_receipt.json", analysis_receipt)
        lines = [
            "# Multifamily colored-shape geometry v0 result\n",
            "\n",
            f"Outcome pattern: `{pattern}`.\n",
            "\n",
            "| Model | Primary layer | Parallelism | Raw exact p | Holm p | Reject |\n",
            "|---|---:|---:|---:|---:|---|\n",
        ]
        for role in MODEL_ROLES:
            cell = primary_summary[role]
            lines.append(
                f"| `{role}` | {cell['layer']} | {cell['statistic']:.9f} | "
                f"{cell['raw_p']:.9f} | {cell['holm_adjusted_p']:.9f} | "
                f"{str(cell['holm_reject']).lower()} |\n"
            )
        lines.extend(
            [
                "\n",
                "This is a frozen observational exploratory result. It is not a semantic, "
                "causal, parity, node-performance, quantization-equivalence, confirmatory, "
                "or Phase I gate result.\n",
            ]
        )
        _atomic_write(stage / "report.md", "".join(lines).encode("utf-8"))
        _write_ledger(stage, ANALYSIS_FILES)
        _publish_stage(stage, output)
        return analysis_receipt
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise


def validate_analysis(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    _validate_ledger(directory, ANALYSIS_FILES)
    receipt = _read_json(directory / "analysis_receipt.json", "analysis receipt")
    _require(receipt.get("protocol_id") == PROTOCOL_ID, "Analysis protocol mismatch")
    _require(receipt.get("status") == "pass", "Analysis status is not pass")
    rows = _read_jsonl(directory / "layer_statistics.jsonl", "layer statistics")
    _require(len(rows) == int(receipt["layer_row_count"]), "Layer row count mismatch")
    _require(
        {str(row["model_label"]) for row in rows} == set(MODEL_ROLES),
        "Analysis model roster mismatch",
    )
    _require(sum(bool(row["is_primary"]) for row in rows) == len(MODEL_ROLES), "Primary row mismatch")
    return {
        "status": "pass",
        "protocol_id": PROTOCOL_ID,
        "outcome_pattern": receipt["outcome_pattern"],
        "layer_row_count": len(rows),
        "scientific_confirmation": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("audit-freeze", help="Validate the public protocol freeze")

    run = subparsers.add_parser("run", help="Run one role-bound model cell")
    run.add_argument("--model-label", choices=MODEL_ROLES, required=True)
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)

    validate_one = subparsers.add_parser("validate-run", help="Validate one sealed model run")
    validate_one.add_argument("directory", type=Path)

    analyze = subparsers.add_parser("analyze", help="Analyze the two predeclared model roles")
    analyze.add_argument("--gemma-run", type=Path, required=True)
    analyze.add_argument("--olmo-run", type=Path, required=True)
    analyze.add_argument("--output", type=Path, required=True)

    validate_joint = subparsers.add_parser("validate-analysis", help="Validate joint analysis")
    validate_joint.add_argument("directory", type=Path)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit-freeze":
        result = audit_freeze()
    elif args.command == "run":
        result = run_model(args.model_label, args.model_path, args.output)
    elif args.command == "validate-run":
        validated = validate_run(args.directory)
        result = {
            "status": validated["status"],
            "protocol_id": PROTOCOL_ID,
            "model_label": validated["receipt"]["model_label"],
        }
    elif args.command == "analyze":
        result = analyze_runs(
            {
                MODEL_ROLES[0]: args.gemma_run,
                MODEL_ROLES[1]: args.olmo_run,
            },
            args.output,
        )
    elif args.command == "validate-analysis":
        result = validate_analysis(args.directory)
    else:  # pragma: no cover
        raise AssertionError(args.command)
    print(_json_bytes(scrub_local_paths(result), pretty=True).decode("utf-8"))


if __name__ == "__main__":
    try:
        main()
    except (ProtocolError, PublishedRunFailure) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
