#!/usr/bin/env python3
"""Fetch only the nine historical model files and verify every pinned SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Callable
import urllib.parse
import urllib.request

import t21_glyph_context_path_pilot_v0 as historical


MODEL_ID = "mlx-community/Llama-3.2-3B-bf16"
REVISION = "60a99aaf43164077157d64bf909b7b61143c6a6d"
MANIFEST_SHA256 = "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"


def expected_manifest() -> dict:
    value = historical.read_json(historical.ROOT / historical.SPEC)["model_artifact"]
    historical.require(value["manifest_sha256"] == MANIFEST_SHA256,
                       "Historical model manifest changed")
    historical.require(value["file_count"] == len(value["files"]) == 9,
                       "Historical file count changed")
    return value


def verified(path: Path, expected: dict) -> bool:
    return (path.is_file() and path.stat().st_size == expected["bytes"]
            and historical.sha256(path) == expected["sha256"])


def fetch_file(
    destination: Path,
    url: str,
    expected: dict,
    *,
    timeout: float = 30,
    opener: Callable = urllib.request.urlopen,
) -> None:
    """No token guessing, trust bypass, overwrite, or use before verification."""
    historical.require(urllib.parse.urlsplit(url).scheme == "https", "HTTPS is required")
    if destination.exists() or destination.is_symlink():
        historical.require(not destination.is_symlink() and verified(destination, expected),
                           f"Existing file does not match the pin: {destination.name}")
        return
    partial = destination.with_name(destination.name + ".partial")
    count = 0
    digest = hashlib.sha256()
    created_partial = False
    try:
        with opener(url, timeout=timeout) as response:
            historical.require(urllib.parse.urlsplit(response.geturl()).scheme == "https",
                               "Refusing a non-HTTPS redirect")
            with partial.open("xb") as handle:
                created_partial = True
                last_report = 0
                while chunk := response.read(8 * 1024 * 1024):
                    count += len(chunk)
                    historical.require(count <= expected["bytes"], "Artifact exceeds pinned size")
                    digest.update(chunk)
                    handle.write(chunk)
                    if count - last_report >= 64 * 1024 * 1024:
                        print(json.dumps({"file": destination.name, "downloaded_bytes": count,
                                          "expected_bytes": expected["bytes"]}), flush=True)
                        last_report = count
        historical.require(count == expected["bytes"], "Artifact size differs from the pin")
        historical.require(digest.hexdigest() == expected["sha256"],
                           "Artifact SHA-256 differs from the pin")
        # Hard-link publication fails if a destination appeared concurrently.
        os.link(partial, destination)
    finally:
        if created_partial:
            partial.unlink()


def fetch_model(output: Path) -> dict:
    expected = expected_manifest()
    output.mkdir(parents=True, exist_ok=True)
    for relative, metadata in expected["files"].items():
        historical.require(Path(relative).name == relative, "Unexpected nested model file")
        url = (f"https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/"
               f"{urllib.parse.quote(relative)}")
        fetch_file(output / relative, url, metadata)
        print(json.dumps({"verified_file": relative, "bytes": metadata["bytes"]}), flush=True)
    from glyphprobe.provenance import model_artifact_receipt
    actual = model_artifact_receipt(output)
    historical.require(actual == expected, "Final nine-file model manifest differs")
    return {"status": "pinned_model_verified", "model_id": MODEL_ID,
            "revision": REVISION, "artifact_manifest_sha256": actual["manifest_sha256"],
            "file_count": actual["file_count"], "total_bytes": actual["total_bytes"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(fetch_model(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
