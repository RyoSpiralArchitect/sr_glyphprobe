from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import orjson
import yaml


def _default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    raise TypeError(f"Cannot serialize {type(value)!r}")


def json_dumps(value: Any, *, pretty: bool = False) -> str:
    option = orjson.OPT_SORT_KEYS
    if pretty:
        option |= orjson.OPT_INDENT_2
    return orjson.dumps(value, default=_default, option=option).decode("utf-8")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_json(path: Path, value: Any, *, pretty: bool = True) -> None:
    atomic_write_text(path, json_dumps(value, pretty=pretty) + "\n")


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json_dumps(value, pretty=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.write("\n")
        handle.flush()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return rows


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a mapping in {path}")
    return value


def write_yaml(path: Path, value: Any) -> None:
    text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False)
    atomic_write_text(path, text)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any, *, length: int = 16) -> str:
    return sha256_bytes(json_dumps(value, pretty=False).encode("utf-8"))[:length]


def hash_paths(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path): sha256_file(path) for path in paths if path.exists()}
