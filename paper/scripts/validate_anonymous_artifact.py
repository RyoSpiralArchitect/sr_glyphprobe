#!/usr/bin/env python3
"""Validate the compact, double-blind T19 evidence artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from typing import Callable
import zipfile


ARTIFACT_ID = "glyphprobe_t19_anonymous_evidence_v0"
ARCHIVE_ROOT = ARTIFACT_ID
MANIFEST_NAME = "ARTIFACT_MANIFEST.json"
SUMS_NAME = "SHA256SUMS"
FIXED_ZIP_TIME = (2026, 9, 2, 0, 0, 0)

FORBIDDEN_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".npy",
    ".npz",
    ".parquet",
    ".pt",
    ".pth",
    ".safetensors",
}


class ArtifactValidationError(RuntimeError):
    """Raised when an archive boundary or integrity check fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactValidationError(message)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _forbidden_fragments() -> tuple[bytes, ...]:
    # Construct these at runtime so the validator does not flag its own source.
    slash = b"/"
    dot = b"."
    return (
        b"ryo" + b"higa",
        b"ryo" + b"spiral" + b"architect",
        b"spiral" + b"architect",
        b"spiral" + b"reality",
        slash + b"users" + slash,
        slash + b"private" + slash + b"tmp" + slash,
        slash + b"var" + slash + b"folders" + slash,
        slash + b"home" + slash,
        b"file" + b":" + slash + slash,
        dot + b"codex",
        b"github" + dot + b"com" + slash + b"ryo",
    )


def _safe_path(name: str) -> None:
    require("\\" not in name, f"Backslash in artifact path: {name}")
    path = PurePosixPath(name)
    require(not path.is_absolute(), f"Absolute artifact path: {name}")
    require(path.parts and all(part not in {"", ".", ".."} for part in path.parts), f"Unsafe artifact path: {name}")
    require(path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"Forbidden raw/model file type: {name}")
    require(".git" not in path.parts, f"Git metadata present: {name}")


def _validate_payloads(files: dict[str, bytes]) -> dict[str, object]:
    require(MANIFEST_NAME in files, f"Missing {MANIFEST_NAME}")
    require(SUMS_NAME in files, f"Missing {SUMS_NAME}")
    try:
        manifest = json.loads(files[MANIFEST_NAME].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"Invalid manifest: {exc}") from exc
    require(isinstance(manifest, dict), "Manifest must be a JSON object")
    require(manifest.get("schema_version") == 1, "Unexpected manifest schema")
    require(manifest.get("artifact_id") == ARTIFACT_ID, "Unexpected artifact id")
    require(manifest.get("archive_root") == ARCHIVE_ROOT, "Unexpected archive root")
    rows = manifest.get("files")
    require(isinstance(rows, list), "Manifest files must be a list")

    expected_payloads = set(files) - {MANIFEST_NAME, SUMS_NAME}
    listed_payloads: set[str] = set()
    for row in rows:
        require(isinstance(row, dict), "Manifest file row must be an object")
        name = row.get("path")
        require(isinstance(name, str), "Manifest file path must be a string")
        _safe_path(name)
        require(name not in listed_payloads, f"Duplicate manifest path: {name}")
        listed_payloads.add(name)
        require(name in files, f"Manifest path missing from artifact: {name}")
        require(row.get("bytes") == len(files[name]), f"Byte count mismatch: {name}")
        require(row.get("sha256") == digest_bytes(files[name]), f"SHA-256 mismatch: {name}")
    require(listed_payloads == expected_payloads, "Manifest roster differs from artifact payload roster")

    try:
        sum_lines = files[SUMS_NAME].decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise ArtifactValidationError("SHA256SUMS is not ASCII") from exc
    parsed_sums: dict[str, str] = {}
    for line in sum_lines:
        require(len(line) > 66 and line[64:66] == "  ", f"Malformed SHA256SUMS row: {line!r}")
        sha_value, name = line[:64], line[66:]
        require(name not in parsed_sums, f"Duplicate SHA256SUMS path: {name}")
        parsed_sums[name] = sha_value
    expected_sum_names = set(files) - {SUMS_NAME}
    require(set(parsed_sums) == expected_sum_names, "SHA256SUMS roster differs from payload plus manifest")
    for name, sha_value in parsed_sums.items():
        require(sha_value == digest_bytes(files[name]), f"SHA256SUMS mismatch: {name}")

    forbidden = _forbidden_fragments()
    for name, value in files.items():
        _safe_path(name)
        lowered = value.lower()
        for fragment in forbidden:
            require(fragment not in lowered, f"Forbidden identity/local-path token in {name}")

    boundary = manifest.get("boundary")
    require(isinstance(boundary, dict), "Manifest boundary must be an object")
    require(boundary.get("raw_model_arrays_included") is False, "Raw-array boundary changed")
    require(boundary.get("model_weights_included") is False, "Model-weight boundary changed")
    require(boundary.get("full_raw_replay_supported") is False, "Replay boundary changed")
    require(boundary.get("compact_audit_supported") is True, "Compact-audit boundary changed")

    return {
        "artifact_id": ARTIFACT_ID,
        "payload_files": len(expected_payloads),
        "total_files": len(files),
        "manifest_sha256": digest_bytes(files[MANIFEST_NAME]),
        "status": "anonymous_artifact_validation_pass",
    }


def _read_directory(root: Path) -> dict[str, bytes]:
    require(root.is_dir(), f"Not a directory: {root}")
    files: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Symlink present: {path}")
        if path.is_dir():
            continue
        require(path.is_file(), f"Non-regular entry present: {path}")
        name = path.relative_to(root).as_posix()
        _safe_path(name)
        files[name] = path.read_bytes()
    return files


def _read_zip(path: Path) -> dict[str, bytes]:
    require(path.is_file(), f"Not a zip file: {path}")
    require(zipfile.is_zipfile(path), f"Invalid zip file: {path}")
    files: dict[str, bytes] = {}
    with zipfile.ZipFile(path, "r") as archive:
        require(not archive.comment, "Zip comment must be empty")
        seen: set[str] = set()
        for info in archive.infolist():
            require(info.filename not in seen, f"Duplicate zip entry: {info.filename}")
            seen.add(info.filename)
            require(not info.is_dir(), f"Directory zip entry is not allowed: {info.filename}")
            require(info.date_time == FIXED_ZIP_TIME, f"Non-fixed zip timestamp: {info.filename}")
            require(info.create_system == 3, f"Unexpected zip creator system: {info.filename}")
            mode = info.external_attr >> 16
            require(stat.S_ISREG(mode), f"Non-regular zip entry: {info.filename}")
            require(mode & 0o777 == 0o644, f"Unexpected zip permissions: {info.filename}")
            prefix = ARCHIVE_ROOT + "/"
            require(info.filename.startswith(prefix), f"Unexpected zip root: {info.filename}")
            name = info.filename[len(prefix):]
            _safe_path(name)
            files[name] = archive.read(info)
    return files


def validate(path: Path) -> dict[str, object]:
    reader: Callable[[Path], dict[str, bytes]] = _read_directory if path.is_dir() else _read_zip
    return _validate_payloads(reader(path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Extracted artifact root or artifact zip")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate(args.artifact.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
