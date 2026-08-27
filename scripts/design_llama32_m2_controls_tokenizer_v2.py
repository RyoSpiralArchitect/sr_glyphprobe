#!/usr/bin/env python3
"""Build the minimum-overlap Llama Milestone 2 control suite.

Two prespecified tokenizer-only searches established that only 25 distinct
dominant-prefix source glyphs are available for 27 required placements. This
script attains the pigeonhole lower bound of two reused placements using a
fixed cyclic donor rule, then checks all 16 wrappers. It loads no language-model
weights and exposes no target-bank input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any
import unicodedata

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v2.yaml"
DEFAULT_OUTPUT_DIR = (
    ROOT / "validation" / "llama32_3b_instruct_m2_control_design_v2" / "generated"
)
EXPECTED_STATUS = "tokenizer_only_minimum_overlap_design_not_scientific"
PANEL_ROOT = (ROOT / "data" / "emoji_panels").resolve()
WRAPPER_ROOT = (ROOT / "data" / "wrappers").resolve()
VALIDATION_ROOT = (ROOT / "validation").resolve()

V0_SCRIPT = ROOT / "scripts" / "design_llama32_m2_controls_tokenizer_v0.py"
V0_SPEC = importlib.util.spec_from_file_location("glyphprobe_llama_m2_design_v0", V0_SCRIPT)
if V0_SPEC is None or V0_SPEC.loader is None:  # pragma: no cover
    raise RuntimeError(f"Could not load v0 design helpers: {V0_SCRIPT}")
V0 = importlib.util.module_from_spec(V0_SPEC)
V0_SPEC.loader.exec_module(V0)
AUDIT = V0.AUDIT


class DesignError(RuntimeError):
    """Raised when a minimum-overlap design invariant fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DesignError(message)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_prior_negative_branches(
    config_dir: Path,
    specs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in specs:
        path = V0._verified_input(
            config_dir,
            spec["path"],
            spec["sha256"],
            allowed_root=VALIDATION_ROOT,
        )
        receipt = json.loads(path.read_text(encoding="utf-8"))
        _require(receipt.get("status") == spec["required_status"], f"Prior status differs: {spec['id']}")
        _require(
            receipt.get("eligible_candidate_count")
            == spec["required_eligible_candidate_count"],
            f"Prior candidate count differs: {spec['id']}",
        )
        rows.append(
            {
                "id": spec["id"],
                "path": str(path.relative_to(ROOT)),
                "sha256": _sha256_file(path),
                "status": receipt["status"],
                "eligible_candidate_count": receipt["eligible_candidate_count"],
            }
        )
    return rows


def _validate_source_audit(
    receipt: dict[str, Any],
    source_specs: list[dict[str, Any]],
) -> None:
    comparisons = {
        row["candidate_panel_id"]: row for row in receipt.get("comparisons", [])
    }
    candidates = {
        row["panel_id"]: row for row in receipt.get("candidates", [])
    }
    for spec in source_specs:
        panel_id = spec["id"]
        _require(panel_id in comparisons, f"Source comparison missing: {panel_id}")
        _require(
            bool(comparisons[panel_id]["transfer_gate_pass"])
            is bool(spec["required_source_gate_pass"]),
            f"Source gate differs: {panel_id}",
        )
        failed = spec.get("failed_source_item")
        if failed is None:
            continue
        profiles = {
            row["id"]: row for row in candidates[panel_id].get("raw_profiles", [])
        }
        _require(failed["id"] in profiles, f"Failed item missing: {failed['id']}")
        profile = profiles[failed["id"]]
        _require(profile["glyph"] == failed["expected_glyph"], "Failed glyph differs")
        _require(profile["token_ids"] == failed["expected_raw_token_ids"], "Failed token ids differ")


def _raw_record(tokenizer: Any, row: dict[str, str]) -> dict[str, Any]:
    profile = AUDIT._raw_profile(tokenizer, row)
    _require(profile["decode_exact"] is True, f"Decode failed: {row['id']}")
    _require(len(row["glyph"]) == 1, f"Source glyph is not a scalar: {row['id']}")
    return {
        "panel_id": row["panel_id"],
        "source_item_id": row["id"],
        "glyph": row["glyph"],
        "codepoint": f"U+{ord(row['glyph']):04X}",
        "unicode_name": unicodedata.name(row["glyph"], None),
        "raw_token_ids": profile["token_ids"],
        "raw_prefix_token_ids": profile["prefix_token_ids"],
        "raw_token_count": profile["token_count"],
    }


def _replace_exact_item(
    items: list[dict[str, str]],
    failed_item_id: str,
    donor: dict[str, Any],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    replaced = 0
    for row in items:
        copy = dict(row)
        if row["id"] == failed_item_id:
            copy["glyph"] = donor["glyph"]
            replaced += 1
        output.append(copy)
    _require(replaced == 1, f"Replacement count differs for {failed_item_id}")
    return output


def _canonical_panel_items(
    tokenizer: Any,
    panel_letter: str,
    source_panel_id: str,
    output_panel_id: str,
    items: list[dict[str, str]],
    reuse_by_recipient_and_glyph: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in items:
        token_ids = [
            int(value) for value in tokenizer.encode(row["glyph"], add_special_tokens=False)
        ]
        prefix = "p" + "_".join(str(value) for value in token_ids[:-1])
        reuse = reuse_by_recipient_and_glyph.get((source_panel_id, row["glyph"]))
        factors: dict[str, Any] = {
            "control_family": output_panel_id,
            "prefix_stratum": prefix,
            "construction_role": (
                "deterministic_minimum_overlap_reuse"
                if reuse is not None
                else "retained_tokenizer_compatible_source_glyph"
            ),
        }
        if reuse is not None:
            factors["donor_source_panel_id"] = reuse["donor_panel_id"]
            factors["allocation_rule"] = reuse["rule"]
        output.append(
            {
                "id": f"llama32_null_{panel_letter}_u{ord(row['glyph']):04x}",
                "glyph": row["glyph"],
                "factors": factors,
                "labels": [],
            }
        )
    return output


def design_controls(
    config_path: Path,
    tokenizer_path: Path,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    _require(isinstance(config, dict), "Config must be a mapping")
    _require(config.get("schema_version") == 1, "Unsupported config schema")
    _require(config.get("status") == EXPECTED_STATUS, "Unexpected config status")
    boundary = config.get("claim_boundary", {})
    for key in (
        "scientific_result",
        "experimental_grid_authorized",
        "model_selection_authorized",
        "language_model_loaded",
        "study_target_banks_accessed",
        "independent_control_panels_claimed",
    ):
        _require(boundary.get(key) is False, f"claim_boundary.{key} must be false")
    allocation = config["allocation_contract"]
    _require(allocation["no_language_model_outcome_inspection"] is True, "Outcome inspection must be forbidden")
    _require(allocation["no_manual_candidate_selection"] is True, "Manual selection must be forbidden")
    constraints = config["analysis_constraints"]
    _require(constraints["treat_control_panels_as_independent"] is False, "Panel dependence must remain explicit")
    _require(constraints["require_overlap_aware_analysis"] is True, "Overlap-aware analysis must be required")
    _require(constraints["require_disjoint_panel_a_only_sensitivity"] is True, "Panel-A sensitivity must be required")
    _require(constraints["confirmatory_claim_authorized"] is False, "Confirmatory claims must be forbidden")

    config_dir = config_path.parent
    prior_rows = _load_prior_negative_branches(
        config_dir, list(config["prior_negative_branches"])
    )
    source_audit_spec = config["source_audit"]
    source_audit_path = V0._verified_input(
        config_dir,
        source_audit_spec["path"],
        source_audit_spec["sha256"],
        allowed_root=VALIDATION_ROOT,
    )
    source_audit = json.loads(source_audit_path.read_text(encoding="utf-8"))
    _require(source_audit.get("status") == source_audit_spec["required_status"], "Source audit status differs")
    _require(
        source_audit.get("all_three_transfer_gate_pass")
        is source_audit_spec["required_all_three_transfer_gate_pass"],
        "Source audit aggregate gate differs",
    )

    reference_spec = config["reference_panel"]
    reference_path = V0._verified_input(
        config_dir,
        reference_spec["path"],
        reference_spec["sha256"],
        allowed_root=PANEL_ROOT,
    )
    source_specs = list(config["source_panels"])
    _require(len(source_specs) == 3, "Exactly three source panels required")
    source_paths = {
        spec["id"]: V0._verified_input(
            config_dir,
            spec["path"],
            spec["sha256"],
            allowed_root=PANEL_ROOT,
        )
        for spec in source_specs
    }
    _validate_source_audit(source_audit, source_specs)

    wrapper_spec = config["wrappers"]
    wrapper_path = V0._verified_input(
        config_dir,
        wrapper_spec["path"],
        wrapper_spec["sha256"],
        allowed_root=WRAPPER_ROOT,
    )
    wrappers = AUDIT._load_wrappers(wrapper_path, int(wrapper_spec["expected_count"]))
    tokenizer, tokenizer_receipt = AUDIT._load_tokenizer(config, tokenizer_path)
    reference_items = AUDIT._load_panel(reference_path, reference_spec["id"])
    source_items = {
        spec["id"]: AUDIT._load_panel(source_paths[spec["id"]], spec["id"])
        for spec in source_specs
    }
    reference_summary = AUDIT._summary(
        tokenizer, reference_spec["id"], reference_items, wrappers
    )
    source_comparisons: dict[str, dict[str, Any]] = {}
    for spec in source_specs:
        summary = AUDIT._summary(tokenizer, spec["id"], source_items[spec["id"]], wrappers)
        comparison = AUDIT._compare_summaries(reference_summary, summary)
        _require(
            comparison["transfer_gate_pass"]
            is bool(spec["required_source_gate_pass"]),
            f"Live source gate differs: {spec['id']}",
        )
        source_comparisons[spec["id"]] = V0._compact_comparison(comparison)

    inventory = config["inventory_contract"]
    dominant_prefix = [int(value) for value in inventory["dominant_prefix_token_ids"]]
    special_prefix = [int(value) for value in inventory["special_prefix_token_ids"]]
    required_count = int(inventory["required_raw_token_count"])
    raw_records = {
        panel_id: [_raw_record(tokenizer, row) for row in rows]
        for panel_id, rows in source_items.items()
    }
    dominant_by_panel = {
        panel_id: [
            row
            for row in rows
            if row["raw_token_count"] == required_count
            and row["raw_prefix_token_ids"] == dominant_prefix
        ]
        for panel_id, rows in raw_records.items()
    }
    special_by_panel = {
        panel_id: [
            row
            for row in rows
            if row["raw_token_count"] == required_count
            and row["raw_prefix_token_ids"] == special_prefix
        ]
        for panel_id, rows in raw_records.items()
    }
    _require(all(len(rows) == 1 for rows in special_by_panel.values()), "Each panel must retain one special-prefix glyph")
    unique_dominant = {
        row["glyph"] for rows in dominant_by_panel.values() for row in rows
    }
    expected_unique = int(inventory["expected_unique_compatible_dominant_glyphs"])
    _require(len(unique_dominant) == expected_unique, "Compatible dominant inventory differs")
    required_placements = int(inventory["required_dominant_placements"])
    lower_bound = required_placements - len(unique_dominant)
    _require(
        lower_bound == inventory["theoretical_minimum_reused_placements"],
        "Pigeonhole lower bound differs",
    )

    final_items = {panel_id: list(rows) for panel_id, rows in source_items.items()}
    reuse_rows: list[dict[str, Any]] = []
    reuse_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    specs_by_id = {spec["id"]: spec for spec in source_specs}
    for replacement in allocation["replacements"]:
        recipient_id = replacement["recipient_panel_id"]
        donor_id = replacement["donor_panel_id"]
        recipient_spec = specs_by_id[recipient_id]
        failed = recipient_spec["failed_source_item"]
        _require(failed is not None, f"Recipient has no failed item: {recipient_id}")
        recipient_original = {row["glyph"] for row in source_items[recipient_id]}
        candidates = sorted(
            (
                row
                for row in dominant_by_panel[donor_id]
                if row["glyph"] not in recipient_original
            ),
            key=lambda row: ord(row["glyph"]),
        )
        _require(candidates, f"No donor candidate for {recipient_id}")
        donor = candidates[0]
        final_items[recipient_id] = _replace_exact_item(
            source_items[recipient_id], failed["id"], donor
        )
        record = {
            "recipient_panel_id": recipient_id,
            "donor_panel_id": donor_id,
            "replaced_source_item_id": failed["id"],
            "rule": replacement["rule"],
            "candidate_count": len(candidates),
            "selected_candidate_ordinal": 1,
            "selected_glyph": donor["glyph"],
            "selected_codepoint": donor["codepoint"],
            "selected_unicode_name": donor["unicode_name"],
            "selected_raw_token_ids": donor["raw_token_ids"],
        }
        reuse_rows.append(record)
        reuse_lookup[(recipient_id, donor["glyph"])] = record

    generated_comparisons: dict[str, dict[str, Any]] = {}
    for spec in source_specs:
        panel_id = spec["id"]
        relabeled = [{**row, "panel_id": spec["output_id"]} for row in final_items[panel_id]]
        final_items[panel_id] = relabeled
        summary = AUDIT._summary(tokenizer, spec["output_id"], relabeled, wrappers)
        comparison = AUDIT._compare_summaries(reference_summary, summary)
        _require(comparison["transfer_gate_pass"] is True, f"Generated panel failed: {panel_id}")
        generated_comparisons[panel_id] = V0._compact_comparison(comparison)

    reference_glyphs = {row["glyph"] for row in reference_items}
    final_glyph_sets = {
        panel_id: {row["glyph"] for row in rows}
        for panel_id, rows in final_items.items()
    }
    _require(all(len(values) == 10 for values in final_glyph_sets.values()), "Panel uniqueness or size differs")
    _require(all(not values & reference_glyphs for values in final_glyph_sets.values()), "Panel overlaps reference")
    pairwise: list[dict[str, Any]] = []
    panel_order = list(allocation["panel_order"])
    for index, left in enumerate(panel_order):
        for right in panel_order[index + 1 :]:
            overlap = sorted(final_glyph_sets[left] & final_glyph_sets[right], key=ord)
            pairwise.append(
                {
                    "left_panel_id": left,
                    "right_panel_id": right,
                    "overlap_count": len(overlap),
                    "overlap_glyphs": overlap,
                    "overlap_codepoints": [f"U+{ord(glyph):04X}" for glyph in overlap],
                }
            )
    total_pairwise = sum(row["overlap_count"] for row in pairwise)
    maximum_pairwise = max(row["overlap_count"] for row in pairwise)
    _require(total_pairwise == allocation["expected_total_pairwise_overlap"], "Total pairwise overlap differs")
    _require(maximum_pairwise == allocation["expected_maximum_pairwise_overlap"], "Maximum pairwise overlap differs")
    final_dominant_placements = [
        row["glyph"]
        for panel_id, rows in final_items.items()
        for row in rows
        if AUDIT._raw_profile(tokenizer, row)["prefix_token_ids"] == dominant_prefix
    ]
    attained_reuse = len(final_dominant_placements) - len(set(final_dominant_placements))
    _require(attained_reuse == lower_bound, "Design does not attain minimum reuse")

    output_files: dict[str, bytes] = {}
    output_manifest: list[dict[str, Any]] = []
    for index, spec in enumerate(source_specs):
        panel_letter = chr(ord("a") + index)
        canonical_items = _canonical_panel_items(
            tokenizer,
            panel_letter,
            spec["id"],
            spec["output_id"],
            final_items[spec["id"]],
            reuse_lookup,
        )
        panel = {
            "schema_version": 1,
            "panel_id": spec["output_id"],
            "status": "tokenizer_matched_minimum_overlap_control_input_not_scientific",
            "construction": {
                "design_id": config["design_id"],
                "tokenizer_model": config["tokenizer"]["model"],
                "tokenizer_revision": config["tokenizer"]["revision"],
                "independent_control_panel": False,
                "requires_overlap_aware_analysis": True,
            },
            "items": canonical_items,
        }
        filename = config["output_contract"]["panel_filenames"][spec["output_id"]]
        payload = V0._panel_bytes(panel)
        output_files[filename] = payload
        output_manifest.append(
            {
                "filename": filename,
                "panel_id": spec["output_id"],
                "bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )

    receipt = {
        "schema_version": 1,
        "design_id": config["design_id"],
        "status": "llama32_m2_tokenizer_matched_minimum_overlap_suite_designed",
        "claim_boundary": {
            **boundary,
            "tokenizer_only": True,
            "model_forward_count": 0,
            "manual_candidate_selection": False,
        },
        "config": {
            "path": str(config_path.relative_to(ROOT)),
            "sha256": _sha256_file(config_path),
        },
        "implementation": {
            "path": str(Path(__file__).resolve().relative_to(ROOT)),
            "sha256": _sha256_file(Path(__file__).resolve()),
            "v0_helper_path": str(V0_SCRIPT.relative_to(ROOT)),
            "v0_helper_sha256": _sha256_file(V0_SCRIPT),
        },
        "prior_negative_branches": prior_rows,
        "source_audit": {
            "path": str(source_audit_path.relative_to(ROOT)),
            "sha256": _sha256_file(source_audit_path),
            "status": source_audit["status"],
        },
        "tokenizer": tokenizer_receipt,
        "inventory_contract": inventory,
        "inventory_observed": {
            "compatible_dominant_by_source_panel": {
                panel_id: len(rows) for panel_id, rows in dominant_by_panel.items()
            },
            "unique_compatible_dominant_glyphs": len(unique_dominant),
            "required_dominant_placements": required_placements,
            "theoretical_minimum_reused_placements": lower_bound,
        },
        "allocation_contract": allocation,
        "selected_reuses": reuse_rows,
        "source_comparisons": source_comparisons,
        "generated_comparisons": generated_comparisons,
        "all_three_generated_panels_match": True,
        "overlap": {
            "pairwise": pairwise,
            "total_pairwise_overlap": total_pairwise,
            "maximum_pairwise_overlap": maximum_pairwise,
            "attained_reused_placements": attained_reuse,
            "attains_theoretical_minimum": attained_reuse == lower_bound,
        },
        "analysis_constraints": constraints,
        "outputs": output_manifest,
        "decision": (
            "The suite attains the unavoidable two-placement overlap lower bound while "
            "matching all tokenizer features in all 16 wrappers. It is exploratory input, "
            "not three independent controls; overlap-aware analysis and a disjoint panel-A-only "
            "sensitivity are mandatory before interpreting model outcomes."
        ),
    }
    receipt_filename = config["output_contract"]["receipt_filename"]
    output_files[receipt_filename] = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return output_files, receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main() -> int:
    args = _parser().parse_args()
    files, receipt = design_controls(args.config, args.tokenizer_path)
    V0._write_output_directory_no_overwrite(args.output_dir, files)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "all_three_generated_panels_match": receipt[
                    "all_three_generated_panels_match"
                ],
                "selected_reuses": receipt["selected_reuses"],
                "overlap": receipt["overlap"],
                "output_dir": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
