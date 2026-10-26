from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path
from typing import Any, Iterable

from glyphprobe.io import sha256_file, stable_hash


def package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def implementation_receipt() -> dict[str, Any]:
    """Hash the installed GlyphProbe Python source without embedding its path."""
    package_root = Path(__file__).resolve().parent
    files: dict[str, str] = {}
    for path in sorted(package_root.rglob("*.py")):
        relative = path.relative_to(package_root).as_posix()
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "package_version": package_version("glyphprobe"),
        "source_file_count": len(files),
        "source_tree_sha256": stable_hash(files, length=64),
    }


def model_artifact_receipt(root: Path) -> dict[str, Any]:
    """Hash a local model snapshot as a path-independent file manifest."""
    root = root.resolve()
    files: dict[str, dict[str, Any]] = {}
    total_bytes = 0
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        files[relative] = {"bytes": size, "sha256": sha256_file(path)}
    if not files:
        raise ValueError(f"Model artifact directory contains no files: {root}")
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "manifest_sha256": stable_hash(files, length=64),
        "files": files,
    }


_NON_IDENTITY_KEYS = {
    "load_latency_ms",
    "resolved_model_path",
    "validation_receipt",
    "validation_receipt_sha256",
}


def _without_runtime_noise(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_runtime_noise(item)
            for key, item in sorted(value.items())
            if key not in _NON_IDENTITY_KEYS
        }
    if isinstance(value, list):
        return [_without_runtime_noise(item) for item in value]
    return value


def stable_model_identity(model_receipt: dict[str, Any]) -> dict[str, Any]:
    """Project a model receipt onto fields suitable for a deterministic run seal."""
    payload = _without_runtime_noise(model_receipt)
    return {
        "payload": payload,
        "sha256": stable_hash(payload, length=64),
    }


def input_hash_receipt(paths: Iterable[Path]) -> dict[str, str]:
    """Hash ordered inputs under portable labels rather than absolute paths."""
    result: dict[str, str] = {}
    for index, path in enumerate(paths):
        if path.exists():
            result[f"input_{index:02d}:{path.name}"] = sha256_file(path)
    return result
