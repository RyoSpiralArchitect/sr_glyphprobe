#!/usr/bin/env python3
"""Source-bound CPU runner, transport, and adapter validation without weights."""

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
    "tests/test_t22_kv_cpu_canary_v0.py",
    "tests/test_fetch_t22_pinned_model_v0.py",
    "tests/test_t22_kv_dissection_v0.py",
    "tests/test_t22_kv_dissection_commands_v0.py",
    "tests/test_t21_glyph_context_path_pilot_v0.py",
)
SOURCES = (
    "scripts/t22_kv_cpu_canary_v0.py",
    "scripts/fetch_t22_pinned_model_v0.py",
    "scripts/validate_t22_cpu_engineering_v0.py",
    "scripts/t22_kv_dissection_v0.py",
    "scripts/t21_glyph_context_path_pilot_v0.py",
    "scripts/validate_t21_glyph_context_path_pilot_v0.py",
    "configs/t21_glyph_context_path_pilot_v0.yaml",
    "src/glyphprobe/provenance.py",
    "src/glyphprobe/io.py",
    *TESTS,
)


def source_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    before = source_hashes()
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    base = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"]
    collected = subprocess.run([*base, "--collect-only", *TESTS], cwd=ROOT,
                               env=environment, text=True, capture_output=True)
    node_ids = [line for line in collected.stdout.splitlines()
                if line.startswith("tests/") and "::test_" in line]
    mandatory = {"test_cpu_full_item_parity_and_actual_attention_diagnostics",
                 "test_run_real_workflow_with_mocked_pinned_tiny_model",
                 "test_gqa_four_operations_match_oracle_and_return_actual_query_weights"}
    names = {node.split("::")[-1].split("[")[0] for node in node_ids}
    if collected.returncode or not node_ids or not mandatory <= names:
        raise RuntimeError(f"Required complete suite not collected:\n{collected.stdout}{collected.stderr}")
    with tempfile.TemporaryDirectory(prefix="glyphprobe-t22-cpu-") as directory:
        junit = Path(directory) / "tests.xml"
        command = [*base, *TESTS, f"--junitxml={junit}"]
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end="")
        suites = ET.parse(junit).getroot().findall("testsuite")
        counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
    passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    unchanged = before == source_hashes()
    ok = (result.returncode == 0 and unchanged and counts["tests"] == len(node_ids)
          and passed > 0 and counts["failures"] == counts["errors"] == counts["skipped"] == 0)
    versions = {}
    for name in ("torch", "transformers", "numpy", "pytest"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    receipt = {
        "protocol_id": "glyphprobe-t22-cpu-engineering-validation-v0",
        "status": "synthetic_engineering_pass" if ok else "incomplete_or_failed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": before,
        "sources_unchanged_during_validation": unchanged,
        "command": ["python", "-m", "pytest", "-o", "addopts=", "-q", *TESTS],
        "collected_test_count": len(node_ids),
        "test_counts": {**counts, "passed": passed},
        "runner_exit_code": result.returncode,
        "runtime": versions,
        "test_output_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "real_checkpoint_loaded": False,
        "real_canary_items_acquired": 0,
        "historical_gpu_replay": False,
        "scientific_result": False,
        "protected_bank_reads": 0,
        "boundary": "Byte streams and tiny random CPU models only; mocked artifact loading in persistence tests does not validate a real checkpoint or its speed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    raise SystemExit(0 if ok else (result.returncode or 1))


if __name__ == "__main__":
    main()
