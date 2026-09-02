#!/usr/bin/env python3
"""Reconstruct T20 checkpoint/seed choices from the retained training history."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def audit(receipt: dict) -> dict:
    trajectories = [r for r in receipt["training_receipts"] if "history" in r]
    selected = [r for r in receipt["training_receipts"] if "selected_seed" in r]
    if len(trajectories) != 27 or len(selected) != 9:
        raise ValueError("Expected 27 histories and nine selected sites")
    rows = []
    for row in trajectories:
        history = row["history"]
        if [h["step"] for h in history] != list(range(50, 601, 50)):
            raise ValueError("Checkpoint order changed")
        best = max(history, key=lambda h: h["validation_score"])
        if best["validation_score"] != row["best_validation_score"]:
            raise ValueError("Best validation score differs")
        rows.append(
            {
                "block_index": row["block_index"],
                "site": row["site"],
                "seed": row["seed"],
                "selected_step": best["step"],
                "best_validation_score": best["validation_score"],
                "selected_iteration_pre_update_minibatch_suff_loss": best["suff_loss"],
                "step_600_pre_update_minibatch_suff_loss": history[-1]["suff_loss"],
            }
        )
    choices = []
    seen = set()
    for row in selected:
        key = row["block_index"], row["site"]
        if key in seen:
            raise ValueError("Duplicate selected site")
        seen.add(key)
        candidates = [r for r in rows if (r["block_index"], r["site"]) == key]
        if sorted(r["seed"] for r in candidates) != [0, 1, 2]:
            raise ValueError("Missing or duplicate seed")
        best = min(candidates, key=lambda r: (-r["best_validation_score"], r["seed"]))
        if (best["seed"], best["best_validation_score"]) != (
            row["selected_seed"],
            row["selected_validation_score"],
        ):
            raise ValueError("Selected seed differs")
        choices.append(best)
    return {
        "status": "pass",
        "histories_reconstructed": 27,
        "sites_reconstructed": 9,
        "selected_sites": choices,
        "all_seed_checkpoints": rows,
        "boundary": (
            "Post-hoc audit of saved histories. Losses precede the iteration's update; "
            "the saved basis follows it. No full-set training loss or new verdict is inferred."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = audit(json.loads(args.receipt.read_text()))
    value.update(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        training_receipt_sha256=hashlib.sha256(args.receipt.read_bytes()).hexdigest(),
        auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(
        json.dumps(
            {"status": value["status"], "selected_sites": value["selected_sites"]}
        )
    )


if __name__ == "__main__":
    main()
