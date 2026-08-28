#!/usr/bin/env python3
"""Build compact public evidence for the T8 reserve confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Mapping


PROTOCOL_ID = "glyphprobe-mistral7b-semantic-atlas-reserve-confirmation-v0"
OUTCOME = "transport_robust_late_depth_glyph_name_alignment_confirmed"
EXPECTED: dict[str, str] = {
    "run/run_receipt.json": "736f575b69b3d23f49233aa2fe7af8afa3911f1699fc111fd8a17eb011d72a65",
    "run/session_receipt.json": "8b43d151bcd4f41f28cc149599bc5477c2b3a8f20c1d594032e1ae53bc4998eb",
    "analysis/analysis_receipt.json": "19e7190effec8ac057ac24cf4c893185ed5f64e67a89cef417a5b9e1047d27c1",
    "analysis/primary_result.json": "ea5824a0b6c6fdd966f7920958081b67b9ee06c855ad1b31646e0865a06cb5a9",
    "analysis/cell_metrics.jsonl": "c74e425c75a1d0e220ae07f80db3a0a7391b7e69380cf2db723751fc8c511fe9",
    "validation/execution_receipt.json": "2e17850e474280945732df7e68dacd226e8b008a89c445bce44c2aca72ffe8c6",
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
    session = _read(sources["run/session_receipt.json"])
    analysis = _read(sources["analysis/analysis_receipt.json"])
    primary = _read(sources["analysis/primary_result.json"])
    execution = _read(sources["validation/execution_receipt.json"])
    cell_rows = [
        json.loads(line)
        for line in sources["analysis/cell_metrics.jsonl"]
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    if run.get("protocol_id") != PROTOCOL_ID or run.get("status") != "pass":
        raise RuntimeError("Run receipt mismatch")
    if session.get("protocol_id") != PROTOCOL_ID or session.get("status") != "pass":
        raise RuntimeError("Session receipt mismatch")
    if analysis.get("outcome_pattern") != OUTCOME or not analysis.get(
        "alignment_confirmed"
    ):
        raise RuntimeError("Analysis receipt mismatch")
    if primary.get("outcome_pattern") != OUTCOME or not primary.get(
        "alignment_confirmed"
    ):
        raise RuntimeError("Primary result mismatch")
    if execution.get("status") != "pass" or len(cell_rows) != 8:
        raise RuntimeError("Execution evidence mismatch")

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
            "outcome_pattern": OUTCOME,
            "artifact_role": "compact_public_confirmatory_evidence_without_raw_activations_or_item_rows",
            "freeze": {
                "commit": "952b89d1c1d8a0aa023f40b617432653581a5a85",
                "manifest_sha256": "a678213ad79f3fced9c6cffe502b38e16b49a517cdf9d18ba75ef855a8efcc58",
                "reserve_model_inputs_forwarded_at_freeze": 0,
            },
            "acquisition": {
                "reserve_items": 292,
                "model_forward_calls": 1752,
                "readout_vectors": 7008,
                "shards": 10,
                "partial_shards": 0,
                "raw_activation_bytes_committed": 0,
            },
            "primary": {
                "cell_count": 8,
                "observed_minimum_cell_contrast": primary[
                    "observed_minimum_cell_contrast"
                ],
                "observed_equal_cell_mean_contrast": primary[
                    "observed_equal_cell_mean_contrast"
                ],
                "practical_minimum": primary["practical_minimum"],
                "randomization_draws": primary["randomization_draws"],
                "randomization_seed": primary["randomization_seed"],
                "exceedances": primary["exceedances"],
                "p_value": primary["p_value"],
                "alpha": primary["alpha"],
                "alignment_confirmed": True,
                "t8_reserve_question_closed": True,
            },
            "claim_boundary": {
                "confirmatory_alignment_claim_authorized": True,
                "semantic_claim_authorized": False,
                "causal_claim_authorized": False,
                "tokenizer_independent_claim_authorized": False,
                "model_general_claim_authorized": False,
                "phase_i_gate_closed": False,
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
                "item_retrieval_outcomes_in_git": False,
                "reason": "retain compact claim-complete evidence while keeping raw and item-level data outside Git",
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
        "file_count": len(EXPECTED),
        "public_manifest_sha256": _sha256(output / "PUBLIC_MANIFEST.json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--execution-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sessions = sorted(args.run.glob("session_*.json"))
    if len(sessions) != 1:
        raise RuntimeError("Expected exactly one run session receipt")
    sources = {
        "run/run_receipt.json": args.run / "run_receipt.json",
        "run/session_receipt.json": sessions[0],
        "analysis/analysis_receipt.json": args.analysis / "analysis_receipt.json",
        "analysis/primary_result.json": args.analysis / "primary_result.json",
        "analysis/cell_metrics.jsonl": args.analysis / "cell_metrics.jsonl",
        "validation/execution_receipt.json": args.execution_receipt,
    }
    print(json.dumps(build(sources, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
