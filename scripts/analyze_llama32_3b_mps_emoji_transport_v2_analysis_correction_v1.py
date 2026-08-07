#!/usr/bin/env python3
"""Run the frozen v2 analysis with the width-80 log-wrap correction.

The adapter changes only launcher-log admission.  It verifies each original
two-line Rich completion record, projects temporary one-line canonical logs to
the frozen analyzer, and adds explicit correction provenance to the unchanged
v2 receipt.  It does not alter source logs, run evidence, endpoint definitions,
bootstrap behavior, the analysis ID, or the output inventory.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Any


CORRECTION_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2-analysis-correction-v1"
CORRECTION_KEY = "analysis_validation_correction"
BASE_ANALYZER_PATH = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py")
BASE_ANALYZER_SHA256 = (
    "1b9502771c4be7073c78b4eb16097db5f1c648724e5d8af9f076293227b44f56"
)
HELPER_PATH = Path(
    "scripts/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
)
HELPER_SHA256 = "4cf3d5d78ba32120df93c1ba0a0f66c985016c84e5b71c9c1df81148590d22ca"
ADAPTER_PATH = Path(
    "scripts/analyze_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py"
)
CORRECTION_MANIFEST_PATH = Path(
    "data/manifests/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.json"
)
CORRECTION_PREFLIGHT_PATH = Path(
    "validation/llama32_3b_mps_emoji_transport_v2/analysis_correction_v1_preflight.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _import_module(path: Path, name: str, *, sha256: str | None = None) -> ModuleType:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Required implementation is missing or a symlink: {path}")
    if sha256 is not None and _sha256(path) != sha256:
        raise RuntimeError(f"Frozen implementation hash differs: {path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import implementation: {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_SOURCE_ROOT = Path(__file__).resolve().parents[1]
base = _import_module(
    _SOURCE_ROOT / BASE_ANALYZER_PATH,
    "glyphprobe_frozen_llama32_3b_mps_emoji_transport_v2_for_correction_v1",
    sha256=BASE_ANALYZER_SHA256,
)
correction = _import_module(
    _SOURCE_ROOT / HELPER_PATH,
    "glyphprobe_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_helper",
    sha256=HELPER_SHA256,
)

TransportAnalysisError = base.TransportAnalysisError
ANALYSIS_ID = base.ANALYSIS_ID
OUTPUT_FILENAMES = base.OUTPUT_FILENAMES
OUTPUT_RECEIPT_FILENAME = base.OUTPUT_RECEIPT_FILENAME
FAMILY_ORDER = base.FAMILY_ORDER
ARM_ORDER = base.ARM_ORDER
BOOTSTRAP_REPLICATES = base.BOOTSTRAP_REPLICATES
BOOTSTRAP_SEED = base.BOOTSTRAP_SEED
PRIMARY_CRITERION_ID = base.PRIMARY_CRITERION_ID
PRIMARY_CRITERION_RULE = base.PRIMARY_CRITERION_RULE


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TransportAnalysisError(message)


def _binding(root: Path, relative: Path) -> dict[str, str]:
    path = (root / relative).resolve()
    _require(
        path.is_relative_to(root.resolve())
        and path.is_file()
        and not path.is_symlink(),
        f"Correction dependency is missing or unsafe: {relative}",
    )
    return {"path": relative.as_posix(), "sha256": _sha256(path)}


def _source_log(root: Path, process: Mapping[str, Any], label: str) -> bytes:
    relative = process.get("log_path")
    _require(isinstance(relative, str) and relative, f"{label} log path is missing")
    raw_path = Path(relative)
    _require(
        not raw_path.is_absolute()
        and ".." not in raw_path.parts
        and raw_path.as_posix() == relative,
        f"{label} log path must be canonical and repository-relative",
    )
    unresolved = root / raw_path
    _require(
        unresolved.is_file() and not unresolved.is_symlink(),
        f"{label} launcher log is missing or unsafe",
    )
    path = unresolved.resolve()
    _require(
        path.is_relative_to(root),
        f"{label} launcher log is missing or unsafe",
    )
    expected_sha256 = process.get("log_sha256")
    payload = path.read_bytes()
    _require(
        isinstance(expected_sha256, str)
        and hashlib.sha256(payload).hexdigest() == expected_sha256,
        f"{label} launcher log hash differs",
    )
    return payload


def _corrected_validate_runs_against_execution(
    runs: Sequence[Mapping[str, Any]],
    execution_binding: Mapping[str, Any],
    root: Path,
    *,
    original_validator: Any,
) -> None:
    """Validate exact wraps, then delegate through temporary canonical logs."""

    root = Path(root).resolve()
    raw_processes = execution_binding.get("processes")
    _require(
        isinstance(raw_processes, list) and len(raw_processes) == len(runs),
        "Execution/run binding grid differs before correction",
    )
    process_indexes: dict[tuple[Any, Any], int] = {}
    for index, row in enumerate(raw_processes):
        _require(isinstance(row, Mapping), "Execution process row is invalid")
        key = (row.get("panel_arm"), row.get("role"))
        _require(key not in process_indexes, "Execution process roles are not unique")
        process_indexes[key] = index
    _require(
        len(process_indexes) == len(runs),
        "Execution process role bindings are incomplete",
    )

    projected_processes = [dict(row) for row in raw_processes]
    with tempfile.TemporaryDirectory(prefix="glyphprobe-v2-correction-v1-") as temp:
        temp_root = Path(temp)
        seen_keys: set[tuple[Any, Any]] = set()
        for run_index, run in enumerate(runs):
            key = (run.get("panel_arm"), run.get("role"))
            _require(key in process_indexes, f"Missing execution binding for {key}")
            _require(key not in seen_keys, f"Duplicate supplied run binding for {key}")
            seen_keys.add(key)
            process_index = process_indexes[key]
            process = raw_processes[process_index]
            run_dir_value = run.get("run_dir")
            run_id = run.get("run_id")
            _require(
                isinstance(run_dir_value, (str, os.PathLike)),
                f"Invalid run directory for {key}",
            )
            _require(isinstance(run_id, str) and run_id, f"Invalid run ID for {key}")
            run_dir = Path(run_dir_value).resolve()
            _require(
                run_dir.name == run_id, f"Run directory/ID binding differs for {key}"
            )
            log_payload = _source_log(root, process, f"{key[0]}/{key[1]}")
            correction.parse_completion_wrap(
                log_payload,
                expected_run_dir=run_dir,
                expected_run_id=run_id,
            )
            canonical = temp_root / f"{run_index:02d}.log"
            canonical.write_bytes(b"Complete  " + os.fsencode(str(run_dir)) + b"\n")
            projected_processes[process_index]["log_path"] = str(canonical)

        projected_binding = dict(execution_binding)
        projected_binding["processes"] = projected_processes
        original_validator(runs, projected_binding, root)


def analyze_transport(
    full50_sky_run: Path,
    full50_food_run: Path,
    full50_animals_run: Path,
    full50_transport_run: Path,
    full50_social_run: Path,
    core35_sky_run: Path,
    core35_food_run: Path,
    core35_animals_run: Path,
    core35_transport_run: Path,
    core35_social_run: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run unchanged v2 math under two temporary, correction-only patches."""

    root = _SOURCE_ROOT.resolve()
    manifest = correction.validate_correction_manifest(root)
    correction.validate_correction_preflight(root, manifest)
    receipt_block = correction.analysis_validation_correction_block(
        root,
        adapter_path=ADAPTER_PATH,
    )

    original_validator = base.v1._validate_runs_against_execution
    original_writer = base.v1._write_json
    writer_calls = 0

    def corrected_validator(
        runs: Sequence[Mapping[str, Any]],
        execution_binding: Mapping[str, Any],
        validator_root: Path,
    ) -> None:
        _corrected_validate_runs_against_execution(
            runs,
            execution_binding,
            validator_root,
            original_validator=original_validator,
        )

    def corrected_writer(path: Path, value: Any) -> None:
        nonlocal writer_calls
        if (
            isinstance(value, dict)
            and value.get("analysis_id") == ANALYSIS_ID
            and Path(path).name == base.V1_OUTPUT_RECEIPT_FILENAME
        ):
            writer_calls += 1
            _require(writer_calls == 1, "Analysis receipt writer called more than once")
            _require(
                CORRECTION_KEY not in value,
                "Analysis receipt already has a correction block",
            )
            value[CORRECTION_KEY] = receipt_block
        original_writer(path, value)

    base.v1._validate_runs_against_execution = corrected_validator
    base.v1._write_json = corrected_writer
    try:
        receipt = base.analyze_transport(
            full50_sky_run,
            full50_food_run,
            full50_animals_run,
            full50_transport_run,
            full50_social_run,
            core35_sky_run,
            core35_food_run,
            core35_animals_run,
            core35_transport_run,
            core35_social_run,
            output_dir,
        )
    finally:
        base.v1._validate_runs_against_execution = original_validator
        base.v1._write_json = original_writer

    _require(writer_calls == 1, "Analysis correction block was not written")
    _require(
        receipt.get(CORRECTION_KEY) == receipt_block,
        "Returned analysis correction block differs",
    )
    return receipt


analyze_llama32_3b_mps_emoji_transport = analyze_transport


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for arm in ARM_ORDER:
        for role in FAMILY_ORDER:
            parser.add_argument(f"--{arm}-{role}-run", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = analyze_transport(
            args.full50_sky_run,
            args.full50_food_run,
            args.full50_animals_run,
            args.full50_transport_run,
            args.full50_social_run,
            args.core35_sky_run,
            args.core35_food_run,
            args.core35_animals_run,
            args.core35_transport_run,
            args.core35_social_run,
            args.output_dir,
        )
    except (TransportAnalysisError, OSError, RuntimeError, ValueError) as exc:
        print(f"E2 v2 analysis correction blocked: {exc}", file=sys.stderr)
        return 2
    print(
        f"Published {len(receipt['output_inventory'])} corrected E2 v2 files to "
        f"{Path(args.output_dir).resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
