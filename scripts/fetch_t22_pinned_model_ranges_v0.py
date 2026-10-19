#!/usr/bin/env python3
"""Bounded HTTPS range acquisition, with the original complete artifact pins."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import http.client
import json
import os
from pathlib import Path
import time
from typing import Callable
import urllib.error
import urllib.parse
import urllib.request
import uuid

from fetch_t22_pinned_model_v0 import (
    MODEL_ID, REVISION, expected_manifest, fetch_file, verified,
)
import t21_glyph_context_path_pilot_v0 as historical


PROTOCOL = "glyphprobe-t22-pinned-model-ranges-v0"
PREFIX_TARGET = "model-00001-of-00002.safetensors"


class IncompleteRangeError(ValueError):
    """A response ended before all precisely requested body bytes arrived."""


class _RangeTransportFailure(Exception):
    """A retryable failure specifically from an HTTP open or body read."""

    def __init__(self, exception_type: str):
        super().__init__(exception_type)
        self.exception_type = exception_type


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _progress(**details: object) -> None:
    print(json.dumps(details, sort_keys=True), flush=True)


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Cache metadata must be a JSON object")
    return value


def _write_json(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _file_signature(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _prefix_identity(path: Path | None, total_bytes: int) -> tuple[dict, tuple | None]:
    if path is None:
        return {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}, None
    require(path.is_file() and not path.is_symlink(), "Prefix must be a regular nonsymlink file")
    signature = _file_signature(path)
    require(0 <= signature[2] <= total_bytes, "Prefix exceeds pinned artifact size")
    digest = hashlib.sha256()
    remaining = signature[2]
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(8 * 1024 * 1024, remaining))
            require(bool(chunk), "Prefix shortened while being read")
            digest.update(chunk)
            remaining -= len(chunk)
    require(_file_signature(path) == signature, "Prefix changed while being read")
    return {"bytes": signature[2], "sha256": digest.hexdigest()}, signature


def _chunk_receipt(expected: dict, start: int, end: int, digest: str) -> dict:
    return {"protocol_id": PROTOCOL, "artifact_sha256": expected["sha256"],
            "total_bytes": expected["bytes"], "start": start, "end": end,
            "bytes": end - start + 1, "sha256": digest}


def _validated_chunk(path: Path, expected: dict, start: int, end: int) -> Path:
    require(path.is_dir() and not path.is_symlink(), "Cached range is not a directory")
    receipt_path = path / "receipt.json"
    require(receipt_path.is_file() and not receipt_path.is_symlink(),
            "Cached range receipt is missing or a symlink")
    receipt = _json(receipt_path)
    body = path / "body.bin"
    require(body.is_file() and not body.is_symlink(), "Cached range body is missing or a symlink")
    require(receipt == _chunk_receipt(expected, start, end, receipt.get("sha256", "")),
            "Cached range identity changed")
    require(body.stat().st_size == end - start + 1, "Cached range size changed")
    require(historical.sha256(body) == receipt["sha256"], "Cached range SHA-256 changed")
    return body


def _download_chunk_once(url: str, expected: dict, cache: Path, start: int, end: int,
                         timeout: float, opener: Callable) -> Path:
    destination = cache / f"{start}-{end}"
    if destination.exists() or destination.is_symlink():
        body = _validated_chunk(destination, expected, start, end)
        _progress(file=cache.name, stage="range_cached", start=start, end=end)
        return body
    partial = cache / f".range-{start}-{end}.partial-{uuid.uuid4().hex}"
    partial.mkdir()
    request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
    count, digest = 0, hashlib.sha256()
    with _transport_call(opener, request, timeout=timeout) as response:
        require(urllib.parse.urlsplit(response.geturl()).scheme == "https",
                "Refusing a non-HTTPS redirect")
        require(response.status == 206, "Range response must have status 206")
        require(response.headers.get("Content-Range") == f"bytes {start}-{end}/{expected['bytes']}",
                "Range response Content-Range differs from the request")
        require(response.headers.get("Content-Length") == str(end - start + 1),
                "Range response Content-Length differs from the request")
        with (partial / "body.bin").open("xb") as handle:
            while chunk := _transport_call(response.read, 8 * 1024 * 1024):
                count += len(chunk)
                require(count <= end - start + 1, "Range body exceeds expected length")
                digest.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
    if count != end - start + 1:
        raise IncompleteRangeError("Range body has an incomplete length")
    _write_json(partial / "receipt.json", _chunk_receipt(expected, start, end, digest.hexdigest()))
    require(not destination.exists(), "Range cache destination appeared concurrently")
    partial.rename(destination)
    _progress(file=cache.name, stage="range_verified_locally", start=start, end=end, bytes=count)
    return _validated_chunk(destination, expected, start, end)


def _retryable_transport(error: BaseException) -> bool:
    allowed = (IncompleteRangeError, TimeoutError, ConnectionResetError,
               http.client.IncompleteRead)
    if isinstance(error, allowed):
        return True
    # HTTPError is also a URLError; status failures must never be retried here.
    return (isinstance(error, urllib.error.URLError)
            and not isinstance(error, urllib.error.HTTPError)
            and isinstance(error.reason, allowed))


def _transport_call(operation: Callable, *args: object, **kwargs: object) -> object:
    try:
        return operation(*args, **kwargs)
    except Exception as error:
        if _retryable_transport(error):
            raise _RangeTransportFailure(type(error).__name__) from error
        raise


def _download_chunk(url: str, expected: dict, cache: Path, start: int, end: int,
                    timeout: float, opener: Callable) -> Path:
    for attempt in range(1, 4):
        try:
            return _download_chunk_once(url, expected, cache, start, end, timeout, opener)
        except (IncompleteRangeError, _RangeTransportFailure) as error:
            if attempt == 3:
                raise
            delay = (1, 3)[attempt - 1]
            _progress(file=cache.name, stage="range_transport_retry", start=start,
                      end=end, failed_attempt=attempt, next_attempt=attempt + 1,
                      max_attempts=3,
                      exception_type=(error.exception_type if isinstance(error, _RangeTransportFailure)
                                      else type(error).__name__),
                      backoff_seconds=delay)
            time.sleep(delay)
    raise AssertionError("Unreachable bounded range retry")


def fetch_range_file(destination: Path, url: str, expected: dict, *, cache_root: Path,
                     workers: int = 4, chunk_bytes: int = 64 * 1024 * 1024,
                     prefix_file: Path | None = None, timeout: float = 30,
                     opener: Callable = urllib.request.urlopen) -> None:
    """Reuse bounded cached ranges; publish only after the original full SHA-256.

    A prefix is untrusted until the complete artifact hash passes. It remains
    read-only, including after failure. Incomplete cache directories are kept
    for diagnosis and are never treated as verified chunk inputs.
    """
    require(type(workers) is int and 1 <= workers <= 4, "Workers must be between one and four")
    require(type(chunk_bytes) is int and chunk_bytes > 0, "Chunk size must be positive")
    require(urllib.parse.urlsplit(url).scheme == "https", "HTTPS is required")
    require(type(expected["bytes"]) is int and expected["bytes"] >= 0,
            "Invalid pinned artifact length")
    if destination.exists() or destination.is_symlink():
        require(not destination.is_symlink() and verified(destination, expected),
                f"Existing file does not match the pin: {destination.name}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if prefix_file is not None:
        require(prefix_file.resolve() != destination.resolve(), "Prefix cannot be the destination")
    prefix, prefix_signature = _prefix_identity(prefix_file, expected["bytes"])
    cache = cache_root / destination.name
    require(not cache.is_symlink(), "Cache directory cannot be a symlink")
    cache.mkdir(parents=True, exist_ok=True)
    identity = {"protocol_id": PROTOCOL, "filename": destination.name,
                "expected": expected, "chunk_bytes": chunk_bytes, "prefix": prefix}
    identity_path = cache / "artifact.json"
    if identity_path.exists():
        require(not identity_path.is_symlink() and _json(identity_path) == identity,
                "Range cache artifact/prefix/chunk identity changed")
    else:
        _write_json(identity_path, identity)
    ranges = [(start, min(start + chunk_bytes, expected["bytes"]) - 1)
              for start in range(prefix["bytes"], expected["bytes"], chunk_bytes)]
    chunks: dict[int, Path] = {}
    # Fail on corrupt completed cache entries before starting any new request.
    pending = []
    for start, end in ranges:
        cached = cache / f"{start}-{end}"
        if cached.exists() or cached.is_symlink():
            chunks[start] = _validated_chunk(cached, expected, start, end)
            _progress(file=cache.name, stage="range_cached", start=start, end=end)
        else:
            pending.append((start, end))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_download_chunk, url, expected, cache, start, end,
                                   timeout, opener): start for start, end in pending}
        try:
            for future in as_completed(futures):
                chunks[futures[future]] = future.result()
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    if prefix_file is not None:
        require(_file_signature(prefix_file) == prefix_signature, "Prefix changed during download")
    assembled = cache / f".assembled.partial-{uuid.uuid4().hex}"
    digest, count = hashlib.sha256(), 0
    with assembled.open("xb") as output:
        inputs = ([(prefix_file, prefix["bytes"])] if prefix_file is not None else [])
        inputs += [(chunks[start], end - start + 1) for start, end in ranges]
        for source, remaining in inputs:
            with source.open("rb") as handle:
                while remaining:
                    chunk = handle.read(min(8 * 1024 * 1024, remaining))
                    require(bool(chunk), "Assembly input shortened while being read")
                    remaining -= len(chunk)
                    count += len(chunk)
                    require(count <= expected["bytes"], "Assembled artifact exceeds pinned size")
                    digest.update(chunk)
                    output.write(chunk)
                require(handle.read(1) == b"", "Assembly input grew beyond its recorded length")
        output.flush()
        os.fsync(output.fileno())
    if prefix_file is not None:
        require(_file_signature(prefix_file) == prefix_signature, "Prefix changed during assembly")
    require(count == expected["bytes"], "Assembled artifact size differs from the pin")
    require(digest.hexdigest() == expected["sha256"], "Artifact SHA-256 differs from the pin")
    os.link(assembled, destination)
    assembled.unlink()
    _progress(file=destination.name, stage="pinned_artifact_published", bytes=count)


def fetch_model(output: Path, *, workers: int = 4, chunk_mib: int = 64,
                prefix_file: Path | None = None, cache_root: Path | None = None) -> dict:
    expected = expected_manifest()
    require(type(workers) is int and 1 <= workers <= 4, "Workers must be between one and four")
    require(type(chunk_mib) is int and chunk_mib > 0, "Chunk MiB must be positive")
    output.mkdir(parents=True, exist_ok=True)
    cache_root = cache_root or output.parent / f".{output.name}.t22-range-cache"
    require(not cache_root.resolve().is_relative_to(output.resolve()),
            "Range cache must be outside the immutable model snapshot")
    if prefix_file is not None:
        require(not prefix_file.resolve().is_relative_to(output.resolve()),
                "Move the preserved prefix outside the model snapshot before downloading")
    for relative, metadata in expected["files"].items():
        require(Path(relative).name == relative, "Unexpected nested model file")
        url = (f"https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/"
               f"{urllib.parse.quote(relative)}")
        if relative.endswith(".safetensors"):
            fetch_range_file(output / relative, url, metadata, cache_root=cache_root,
                             workers=workers, chunk_bytes=chunk_mib * 1024 * 1024,
                             prefix_file=prefix_file if relative == PREFIX_TARGET else None)
        else:
            fetch_file(output / relative, url, metadata)
        _progress(verified_file=relative, bytes=metadata["bytes"])
    from glyphprobe.provenance import model_artifact_receipt
    actual = model_artifact_receipt(output)
    require(actual == expected, "Final nine-file model manifest differs")
    return {"status": "pinned_model_verified", "model_id": MODEL_ID,
            "revision": REVISION, "artifact_manifest_sha256": actual["manifest_sha256"],
            "file_count": actual["file_count"], "total_bytes": actual["total_bytes"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--chunk-mib", type=int, default=64)
    parser.add_argument("--prefix-file", type=Path)
    parser.add_argument("--cache-root", type=Path)
    args = parser.parse_args()
    print(json.dumps(fetch_model(args.output, workers=args.workers, chunk_mib=args.chunk_mib,
                                 prefix_file=args.prefix_file, cache_root=args.cache_root),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
