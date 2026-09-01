#!/usr/bin/env python3
"""Post-hoc full-interchange ceiling for the six frozen T19-C sites.

POST-HOC AND DESCRIPTIVE. This script was written after the registered T19-C
decision was recorded. It does not and cannot change that decision. It answers
one question the registered design left open: what adjusted effect was
attainable at each frozen site at all, measured by replacing the entire site
activation with the same item's other-view activation (full interchange), in
the same single context and on the same 192-item evaluation bank.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping
import uuid

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import t19_lexical_alias_unicode_control_v0 as t19  # noqa: E402
import t19_lexical_alias_component_causal_v0 as t19c  # noqa: E402


PROTOCOL_ID = "glyphprobe-t19-lexical-alias-component-causal-posthoc-ceiling-v0"
SCHEMA_VERSION = 1
STATUS_LABEL = "posthoc_descriptive_not_part_of_registered_decision"


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(model_path: Path, source_root: Path, evaluation_root: Path, output_root: Path) -> dict[str, Any]:
    t19c.audit_go(require_pushed=False)
    evaluation = t19c.validate_evaluation(evaluation_root, source_root)
    if output_root.exists():
        raise RuntimeError(f"Post-hoc output exists: {output_root}")
    stage = output_root.with_name(f".{output_root.name}.stage-{uuid.uuid4().hex}")
    stage.mkdir(parents=True)
    with np.load(evaluation_root / "evaluation_states.npz", allow_pickle=False) as arrays:
        targets = np.asarray(arrays["baseline_targets"], dtype=np.float32)
        baseline_components = np.asarray(arrays["baseline_components"], dtype=np.float32)
    torch, tokenizer, model, blocks, model_receipt = t19c._load_model(model_path)
    rows = t19.causal_items("eval")
    sites = len(t19c.SOURCE_SITE_ORDER)
    width = targets.shape[-1]
    glyph_swap = np.empty((sites, len(rows), 2, width), dtype=np.float32)
    codepoint_swap = np.empty((sites, len(rows), 2, width), dtype=np.float32)
    forwards = 0
    started = time.perf_counter()
    try:
        for item_index, row in enumerate(rows):
            for site_index, (site, block_index) in enumerate(t19c.SOURCE_SITE_ORDER):
                g = baseline_components[site_index, item_index, 0]
                c = baseline_components[site_index, item_index, 1]
                glyph_swap[site_index, item_index] = t19c._forward_replacements(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                    view="glyph", site=site, block_index=block_index,
                    replacements=np.stack((g, c)).astype(np.float32),
                )
                codepoint_swap[site_index, item_index] = t19c._forward_replacements(
                    torch=torch, tokenizer=tokenizer, model=model, blocks=blocks, row=row,
                    view="codepoint_literal", site=site, block_index=block_index,
                    replacements=np.stack((c, g)).astype(np.float32),
                )
                forwards += 2
    finally:
        del model
        torch.cuda.empty_cache()
    np.savez_compressed(stage / "posthoc_states.npz", glyph_swap=glyph_swap, codepoint_swap=codepoint_swap)

    alias_target = targets[:, 0]
    codepoint_target = targets[:, 1]
    site_rows: list[dict[str, Any]] = []
    for site_index, (site, block_index) in enumerate(t19c.SOURCE_SITE_ORDER):
        _zero_glyph_effect, _zero_items, zero_glyph = t19c._retrieval_item_values(glyph_swap[site_index, :, 0], alias_target, codepoint_target)
        _swap_glyph_effect, _swap_items, swapped_glyph = t19c._retrieval_item_values(glyph_swap[site_index, :, 1], alias_target, codepoint_target)
        _zero_cp_effect, _zero_cp_items, zero_codepoint = t19c._retrieval_item_values(codepoint_swap[site_index, :, 0], alias_target, codepoint_target)
        _swap_cp_effect, _swap_cp_items, swapped_codepoint = t19c._retrieval_item_values(codepoint_swap[site_index, :, 1], alias_target, codepoint_target)
        site_rows.append(
            {
                "site": site,
                "block_index": block_index,
                "primary_site_in_t19c": (site, block_index) in t19c.PRIMARY_SITES,
                "zero_hook_glyph": zero_glyph,
                "full_interchange_codepoint_into_glyph": swapped_glyph,
                "zero_hook_codepoint": zero_codepoint,
                "full_interchange_glyph_into_codepoint": swapped_codepoint,
                "necessity_ceiling_alias_top1": float(zero_glyph["alias_top1"] - swapped_glyph["alias_top1"]),
                "sufficiency_ceiling_alias_top1": float(swapped_codepoint["alias_top1"] - zero_codepoint["alias_top1"]),
                "sufficiency_ceiling_composite": float(swapped_codepoint["alias_minus_codepoint_top1"] - zero_codepoint["alias_minus_codepoint_top1"]),
            }
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": STATUS_LABEL,
        "registered_decision_unchanged": True,
        "parent_protocol_id": t19c.PROTOCOL_ID,
        "parent_evaluation_receipt_sha256": evaluation["evaluation_receipt_sha256"],
        "sites": site_rows,
    }
    _write_json(stage / "posthoc_ceiling_result.json", result)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": STATUS_LABEL,
        "model_forward_calls": forwards,
        "intervention_rows": forwards,
        "elapsed_seconds": time.perf_counter() - started,
        "model": model_receipt,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "outputs": {name: _sha256(stage / name) for name in ("posthoc_states.npz", "posthoc_ceiling_result.json")},
    }
    _write_json(stage / "posthoc_receipt.json", receipt)
    t19.engine._write_ledger(stage, ("posthoc_states.npz", "posthoc_ceiling_result.json", "posthoc_receipt.json"))
    os.replace(stage, output_root)
    summary = {
        "status": "pass",
        "sites": [
            {
                "site": row["site"],
                "block_index": row["block_index"],
                "necessity_ceiling_alias_top1": row["necessity_ceiling_alias_top1"],
                "sufficiency_ceiling_alias_top1": row["sufficiency_ceiling_alias_top1"],
            }
            for row in site_rows
        ],
        "model_forward_calls": forwards,
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.model_path, args.source_root, args.evaluation_root, args.output_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
