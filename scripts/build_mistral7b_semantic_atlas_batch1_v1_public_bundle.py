#!/usr/bin/env python3
"""Build the compact public evidence bundle for semantic atlas batch-one v1."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping


PROTOCOL_ID = "glyphprobe-mistral7b-semantic-atlas-batch1-v1"
EXPECTED: dict[str, str] = {
    "run/run_receipt.json": "644fcd88c27999af2a5a011c1ba4748e2f78efb79d978dedf7a8118b8335de72",
    "run/session_receipt.json": "b6f001e656b5a10b0739511fb3642af35892491d22eb2df858a7c8512e3dfbdb",
    "validation/batch64_capture_validation_failure.json": "ffd24a94f75cd0ffd64b3e38ece37803d8cb383ca6d9d642f0ecb42f8d5ee704",
    "validation/batch1_capture_validation_pass.json": "52367403f7dfd99c2390498f7c005b29fd555e673dab4231f4983b125cab51d2",
    "analysis/analysis_receipt.json": "d731d9bd794264feb335140b37a722e6c4cc11732d08c255bbd12736f60aaeb0",
    "analysis/cell_metrics.jsonl": "93c752fc0941dbc34b1bc9422247dc7b700ad655ef621d0fd3c1ae2bf8915c8b",
    "analysis/layer_summary.json": "2e6cc8145abcdc141703d9c4675f230da7fd93e2bd93baf90eaa02deea5d8c88",
    "analysis/batch64_sensitivity_receipt.json": "982a08329b5117b880c75097e0250465071b4cd6464695fc9e7ddf288d7cff6e",
    "analysis/batch64_sensitivity_layer_summary.json": "d542bcee2ba217276b5b9f0f4b1aa4a3f6336b643846281a8780c72ba9de06f7",
    "analysis/token_structure_receipt.json": "e766ec48a2682c3b2523f057e939138ab9f78b846a1b416ee22e716292702d85",
    "analysis/token_structure_cell_metrics.jsonl": "1d85c7c31fe9df2e928066f6ecd49eb3f4497d5073d5283ac1e0cb9fcbaba129",
    "analysis/token_structure_layer_summary.json": "684b838536ceae5a403089a0d4413464596e03389b56e477f582a29ae6c79572",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def build(sources: Mapping[str, Path], output: Path) -> dict[str, Any]:
    if set(sources) != set(EXPECTED):
        raise RuntimeError("Public source roster mismatch")
    for relative, expected in EXPECTED.items():
        path = sources[relative]
        if not path.is_file() or _sha256(path) != expected:
            raise RuntimeError(f"Public source hash mismatch: {relative}")
    run = _read(sources["run/run_receipt.json"])
    capture_failure = _read(
        sources["validation/batch64_capture_validation_failure.json"]
    )
    capture_pass = _read(sources["validation/batch1_capture_validation_pass.json"])
    analysis = _read(sources["analysis/analysis_receipt.json"])
    token = _read(sources["analysis/token_structure_receipt.json"])
    if run.get("status") != "pass" or run.get("protocol_id") != PROTOCOL_ID:
        raise RuntimeError("Canonical run receipt mismatch")
    if capture_failure.get("status") != "validation_failed":
        raise RuntimeError("Batch64 failure receipt mismatch")
    if (
        capture_pass.get("status") != "pass"
        or capture_pass.get("passed_case_count") != 18
    ):
        raise RuntimeError("Batch1 validation receipt mismatch")
    if analysis.get("status") != "pass" or token.get("status") != "pass":
        raise RuntimeError("Analysis receipt mismatch")
    if any(
        int(receipt.get("reserved_unrun_model_inputs_forwarded", -1)) != 0
        for receipt in (run, analysis, token)
    ):
        raise RuntimeError("Reserve boundary mismatch")
    stage = output.parent / f".{output.name}.partial-{uuid.uuid4().hex}"
    if output.exists():
        raise RuntimeError("Public output already exists")
    stage.mkdir(parents=True)
    try:
        for relative, source in sources.items():
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        manifest = {
            "schema_version": 1,
            "protocol_id": PROTOCOL_ID,
            "status": "pass",
            "artifact_role": "compact_public_evidence_without_raw_activations_or_item_rows",
            "canonical_capture": {
                "acquired_items": 892,
                "reserved_unrun_items": 292,
                "unique_input_sequences": 5352,
                "model_forward_calls": 5352,
                "readout_vectors": 192672,
                "activation_dtype": "float32",
                "shards": 28,
                "raw_activation_bytes_committed": 0,
            },
            "capture_validation": {
                "batch64_status": "validation_failed_0_of_18",
                "batch1_status": "pass_18_of_18_bit_exact",
            },
            "analysis": {
                "role": "post_acquisition_descriptive_no_decision",
                "complete_cell_rows": 144,
                "token_structure_sensitivity_rows": 576,
                "reserved_unrun_model_inputs_forwarded": 0,
                "confirmatory_status": False,
                "phase_i_gate_closed": False,
            },
            "outcome_summary": {
                "discovery_layer31_glyph_name_top1_equal_cell_mean": 0.13657957781106234,
                "discovery_layer31_glyph_codepoint_top1_equal_cell_mean": 0.0011876484932145104,
                "discovery_top1_chance": 1.0 / 842.0,
                "discovery_layer31_glyph_name_cka_equal_cell_mean": 0.20678813196718693,
                "discovery_layer31_glyph_codepoint_cka_equal_cell_mean": 0.08297279383987188,
                "glyph5_common_prefix_layer31_glyph_name_top1": 0.15065789967775345,
                "glyph5_common_prefix_layer31_glyph_codepoint_top1": 0.001151315838797018,
                "glyph5_name5_layer31_glyph_name_top1": 0.3517441898584366,
                "glyph5_name5_layer31_glyph_codepoint_top1": 0.031976744532585144,
            },
            "files": {
                relative: {
                    "sha256": _sha256(stage / relative),
                    "bytes": (stage / relative).stat().st_size,
                }
                for relative in sorted(sources)
            },
            "raw_data_policy": {
                "raw_activations_in_git": False,
                "item_pair_cosines_in_git": False,
                "reason": "retain compact audit evidence while keeping multi-gigabyte and item-level data outside Git",
            },
        }
        (stage / "PUBLIC_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {
        "status": "pass",
        "output": output.as_posix(),
        "public_manifest_sha256": _sha256(output / "PUBLIC_MANIFEST.json"),
        "file_count": len(EXPECTED),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-receipt", type=Path, required=True)
    parser.add_argument("--session-receipt", type=Path, required=True)
    parser.add_argument("--batch64-failure", type=Path, required=True)
    parser.add_argument("--batch1-pass", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--batch64-analysis", type=Path, required=True)
    parser.add_argument("--token-analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = {
        "run/run_receipt.json": args.run_receipt,
        "run/session_receipt.json": args.session_receipt,
        "validation/batch64_capture_validation_failure.json": args.batch64_failure,
        "validation/batch1_capture_validation_pass.json": args.batch1_pass,
        "analysis/analysis_receipt.json": args.analysis / "analysis_receipt.json",
        "analysis/cell_metrics.jsonl": args.analysis / "cell_metrics.jsonl",
        "analysis/layer_summary.json": args.analysis / "layer_summary.json",
        "analysis/batch64_sensitivity_receipt.json": args.batch64_analysis
        / "analysis_receipt.json",
        "analysis/batch64_sensitivity_layer_summary.json": args.batch64_analysis
        / "layer_summary.json",
        "analysis/token_structure_receipt.json": args.token_analysis
        / "analysis_receipt.json",
        "analysis/token_structure_cell_metrics.jsonl": args.token_analysis
        / "cell_metrics.jsonl",
        "analysis/token_structure_layer_summary.json": args.token_analysis
        / "layer_summary.json",
    }
    print(json.dumps(build(sources, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
