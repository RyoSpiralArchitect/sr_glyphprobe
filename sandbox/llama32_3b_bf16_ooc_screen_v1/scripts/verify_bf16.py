#!/usr/bin/env python3
"""Verify the downloaded bf16 snapshot against the frozen v2 model artifact,
using the project's OWN provenance.model_artifact_receipt (via the orjson shim).
"""
from __future__ import annotations

import os
from pathlib import Path

from glyphprobe.provenance import model_artifact_receipt

FROZEN = {
    "model": "mlx-community/Llama-3.2-3B-bf16",
    "revision": "60a99aaf43164077157d64bf909b7b61143c6a6d",
    "file_count": 9,
    "total_bytes": 6_434_705_789,
    "manifest_sha256": "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4",
}


def main() -> int:
    root = Path(os.environ["SNAP"]).resolve()
    r = model_artifact_receipt(root)
    print("snapshot dir      :", root)
    print(f"file_count        : {r['file_count']}  (frozen {FROZEN['file_count']})")
    print(f"total_bytes       : {r['total_bytes']:,}  (frozen {FROZEN['total_bytes']:,})")
    print(f"manifest_sha256   : {r['manifest_sha256']}")
    print(f"frozen  sha256    : {FROZEN['manifest_sha256']}")
    ok = (
        r["file_count"] == FROZEN["file_count"]
        and r["total_bytes"] == FROZEN["total_bytes"]
        and r["manifest_sha256"] == FROZEN["manifest_sha256"]
    )
    print("-" * 60)
    print("per-file:")
    for rel, meta in sorted(r["files"].items()):
        print(f"  {rel:<34} {meta['bytes']:>13,}  {meta['sha256'][:16]}…")
    print("=" * 60)
    print("RESULT            :", "✅ MATCH — identical to the sealed v2 weights"
          if ok else "❌ MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
