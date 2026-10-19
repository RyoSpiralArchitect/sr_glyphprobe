#!/usr/bin/env python3
"""Run synthetic T22/T21 checks and emit a source-bound engineering receipt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
TESTS = (
    "tests/test_t22_kv_dissection_v0.py",
    "tests/test_t22_kv_dissection_commands_v0.py",
    "tests/test_t21_glyph_context_path_pilot_v0.py",
)


def validate(output: Path) -> int:
    if output.exists():
        raise FileExistsError(output)
    sources = (
        "scripts/t22_kv_dissection_v0.py",
        "scripts/t21_glyph_context_path_pilot_v0.py",
        "scripts/validate_t22_kv_dissection_v0.py",
        "scripts/validate_t21_glyph_context_path_pilot_v0.py",
        "configs/t21_glyph_context_path_pilot_v0.yaml",
        *TESTS,
    )
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    collect = subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "--collect-only", "-q", *TESTS],
        cwd=ROOT, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    collected = [line for line in collect.stdout.splitlines()
                 if line.startswith("tests/") and "::test_" in line]
    required_tests = {
        "test_gqa_four_operations_match_oracle_and_return_actual_query_weights",
        "test_stock_path_and_close_restore_exact_forward",
        "test_v_only_local_weights_fixed_while_later_query_weights_can_change",
    }
    collected_names = {node.split("::")[-1].split("[")[0] for node in collected}
    if collect.returncode or not collected or not required_tests <= collected_names:
        raise RuntimeError(f"Full synthetic suite could not be collected:\n{collect.stdout}")
    with tempfile.TemporaryDirectory(prefix="glyphprobe-t22-") as directory:
        junit = Path(directory) / "tests.xml"
        command = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", *TESTS,
                   f"--junitxml={junit}"]
        completed = subprocess.run(command, cwd=ROOT, env=environment, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        print(completed.stdout, end="")
        if not junit.is_file():
            raise RuntimeError(f"Test runner produced no results (exit {completed.returncode})")
        suites = ET.parse(junit).getroot().findall("testsuite")
        counts = {key: sum(int(s.get(key, "0")) for s in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
    changed = any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
                  for name, digest in hashes.items())
    passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    ok = (completed.returncode == 0 and passed > 0 and not changed
          and counts["tests"] == len(collected)
          and counts["failures"] == counts["errors"] == counts["skipped"] == 0)
    def version_or_none(name: str) -> str | None:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return None
    receipt = {
        "protocol_id": "glyphprobe-t22-kv-dissection-v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "synthetic_engineering_pass" if ok else "synthetic_engineering_incomplete_or_failed",
        "source_sha256": hashes,
        "sources_changed_during_validation": changed,
        "command": ["python", "-m", "pytest", "-o", "addopts=", "-q", *TESTS],
        "runner_exit_code": completed.returncode,
        "collected_test_count": len(collected),
        "test_counts": {**counts, "passed": passed},
        "runtime": {name: version_or_none(name)
                    for name in ("torch", "transformers", "numpy", "pytest")},
        "test_output_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "scientific_model_forwards": 0,
        "synthetic_model_forwards_executed": passed > 0 and counts["skipped"] == 0,
        "protected_bank_reads": 0,
        "boundary": "Synthetic tiny random models only. No historical Llama artifact replay, real-item acquisition, lexical effect, or confirmatory inference.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if ok else (completed.returncode or 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(validate(args.output))


if __name__ == "__main__":
    main()
