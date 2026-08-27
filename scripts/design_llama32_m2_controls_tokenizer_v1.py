#!/usr/bin/env python3
"""Design Llama controls by deterministic tokenizer-completion enumeration.

This is the prespecified successor to the exhausted v0 single-scalar search.
It enumerates final tokenizer IDs in ascending order after the fixed dominant
emoji prefix, retains only one-grapheme emoji sequences, and applies the full
16-wrapper structural gate. It loads no language-model weights and exposes no
target-bank input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any
import unicodedata

import regex
import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v1.yaml"
DEFAULT_OUTPUT_DIR = (
    ROOT / "validation" / "llama32_3b_instruct_m2_control_design_v1" / "generated"
)
EXPECTED_STATUS = "tokenizer_only_grapheme_completion_design_not_scientific"
PANEL_ROOT = (ROOT / "data" / "emoji_panels").resolve()
WRAPPER_ROOT = (ROOT / "data" / "wrappers").resolve()
VALIDATION_ROOT = (ROOT / "validation").resolve()

V0_SCRIPT = ROOT / "scripts" / "design_llama32_m2_controls_tokenizer_v0.py"
V0_SPEC = importlib.util.spec_from_file_location("glyphprobe_llama_m2_design_v0", V0_SCRIPT)
if V0_SPEC is None or V0_SPEC.loader is None:  # pragma: no cover - import invariant
    raise RuntimeError(f"Could not load v0 design helpers: {V0_SCRIPT}")
V0 = importlib.util.module_from_spec(V0_SPEC)
V0_SPEC.loader.exec_module(V0)
AUDIT = V0.AUDIT


class DesignError(RuntimeError):
    """Raised when a v1 design invariant fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DesignError(message)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_extended_pictographic(value: str) -> bool:
    return regex.fullmatch(r"\p{Extended_Pictographic}", value, regex.VERSION1) is not None


def _is_regional_indicator(value: str) -> bool:
    return regex.fullmatch(r"\p{Regional_Indicator}", value, regex.VERSION1) is not None


def _is_emoji_modifier(value: str) -> bool:
    return regex.fullmatch(r"\p{Emoji_Modifier}", value, regex.VERSION1) is not None


def _is_allowed_emoji_component(value: str) -> bool:
    return (
        _is_extended_pictographic(value)
        or _is_regional_indicator(value)
        or _is_emoji_modifier(value)
        or ord(value) in {0x200D, 0xFE0E, 0xFE0F}
    )


def _has_required_emoji_shape(value: str) -> bool:
    if any(_is_extended_pictographic(char) for char in value):
        return True
    return regex.fullmatch(r"\p{Regional_Indicator}{2}", value, regex.VERSION1) is not None


def _one_grapheme(value: str) -> bool:
    return regex.fullmatch(r"\X", value, regex.VERSION1) is not None


def _name_allowed(names: list[str], forbidden_terms: list[str]) -> bool:
    joined = " + ".join(names).upper()
    return not any(term.upper() in joined for term in forbidden_terms)


def _enumerate_completion_candidates(
    tokenizer: Any,
    contract: dict[str, Any],
    excluded_glyphs: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    prefix = [int(value) for value in contract["fixed_prefix_token_ids"]]
    start = int(contract["final_token_id_start"])
    end = int(contract["final_token_id_end_exclusive"])
    _require(0 <= start < end, "Bad final-token range")
    minimum = int(contract["minimum_scalar_count"])
    maximum = int(contract["maximum_scalar_count"])
    forbidden_terms = list(contract["forbidden_unicode_name_terms"])
    counts = {
        "total_final_token_ids": 0,
        "decoded_empty": 0,
        "decoded_contains_replacement_character": 0,
        "scalar_count_out_of_range": 0,
        "contains_excluded_glyph": 0,
        "unassigned_unicode_name": 0,
        "unicode_name_term_forbidden": 0,
        "not_exactly_one_grapheme": 0,
        "required_emoji_shape_absent": 0,
        "non_emoji_component_present": 0,
        "reencoded_token_ids_mismatch": 0,
        "eligible": 0,
    }
    eligible: list[dict[str, Any]] = []
    for final_token_id in range(start, end):
        counts["total_final_token_ids"] += 1
        token_ids = [*prefix, final_token_id]
        decoded = tokenizer.decode(
            token_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        if not decoded:
            counts["decoded_empty"] += 1
            continue
        if "\ufffd" in decoded:
            counts["decoded_contains_replacement_character"] += 1
            continue
        if not minimum <= len(decoded) <= maximum:
            counts["scalar_count_out_of_range"] += 1
            continue
        if any(glyph in decoded for glyph in excluded_glyphs):
            counts["contains_excluded_glyph"] += 1
            continue
        names = [unicodedata.name(char, "") for char in decoded]
        if not all(names):
            counts["unassigned_unicode_name"] += 1
            continue
        if not _name_allowed(names, forbidden_terms):
            counts["unicode_name_term_forbidden"] += 1
            continue
        if not _one_grapheme(decoded):
            counts["not_exactly_one_grapheme"] += 1
            continue
        if not _has_required_emoji_shape(decoded):
            counts["required_emoji_shape_absent"] += 1
            continue
        if not all(_is_allowed_emoji_component(char) for char in decoded):
            counts["non_emoji_component_present"] += 1
            continue
        reencoded = [
            int(value)
            for value in tokenizer.encode(decoded, add_special_tokens=False)
        ]
        if reencoded != token_ids:
            counts["reencoded_token_ids_mismatch"] += 1
            continue
        eligible.append(
            {
                "candidate_ordinal": len(eligible) + 1,
                "final_token_id": final_token_id,
                "glyph": decoded,
                "codepoints": [f"U+{ord(char):04X}" for char in decoded],
                "unicode_names": names,
                "scalar_count": len(decoded),
                "raw_token_ids": token_ids,
                "raw_prefix_token_ids": prefix,
            }
        )
        counts["eligible"] += 1
    rejection_total = sum(
        value
        for key, value in counts.items()
        if key not in {"total_final_token_ids", "eligible"}
    )
    _require(
        rejection_total + counts["eligible"] == counts["total_final_token_ids"],
        "Candidate accounting mismatch",
    )
    return eligible, counts


def _sequence_slug(value: str) -> str:
    return "_".join(f"u{ord(char):04x}" for char in value)


def _canonical_panel_items(
    tokenizer: Any,
    panel_letter: str,
    output_panel_id: str,
    items: list[dict[str, str]],
    selected_glyphs: set[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in items:
        token_ids = [
            int(value) for value in tokenizer.encode(row["glyph"], add_special_tokens=False)
        ]
        prefix = "p" + "_".join(str(value) for value in token_ids[:-1])
        output.append(
            {
                "id": f"llama32_null_{panel_letter}_{_sequence_slug(row['glyph'])}",
                "glyph": row["glyph"],
                "factors": {
                    "control_family": output_panel_id,
                    "prefix_stratum": prefix,
                    "construction_role": (
                        "deterministic_tokenizer_only_grapheme_replacement"
                        if row["glyph"] in selected_glyphs
                        else "retained_tokenizer_compatible_source_glyph"
                    ),
                },
                "labels": [],
            }
        )
    return output


def _base_receipt(
    *,
    config: dict[str, Any],
    config_path: Path,
    boundary: dict[str, Any],
    prior_path: Path,
    prior: dict[str, Any],
    source_audit_path: Path,
    source_audit: dict[str, Any],
    tokenizer_receipt: dict[str, Any],
    search_counts: dict[str, int],
    eligible: list[dict[str, Any]],
    source_comparisons: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    eligible_hash_rows = [
        {
            key: row[key]
            for key in (
                "candidate_ordinal",
                "final_token_id",
                "glyph",
                "codepoints",
                "unicode_names",
                "raw_token_ids",
            )
        }
        for row in eligible
    ]
    return {
        "schema_version": 1,
        "design_id": config["design_id"],
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
        "prior_negative_branch": {
            "path": str(prior_path.relative_to(ROOT)),
            "sha256": _sha256_file(prior_path),
            "status": prior["status"],
            "eligible_candidate_count": prior["eligible_candidate_count"],
        },
        "source_audit": {
            "path": str(source_audit_path.relative_to(ROOT)),
            "sha256": _sha256_file(source_audit_path),
            "status": source_audit["status"],
            "all_three_transfer_gate_pass": source_audit[
                "all_three_transfer_gate_pass"
            ],
        },
        "tokenizer": tokenizer_receipt,
        "unicode_database_version": unicodedata.unidata_version,
        "regex_version": regex.__version__,
        "search_contract": config["search_contract"],
        "search_filter_order": [
            "decoded_nonempty",
            "no_replacement_character",
            "scalar_count_range",
            "no_excluded_glyph_substring",
            "assigned_unicode_names",
            "forbidden_unicode_name_terms",
            "exactly_one_grapheme",
            "emoji_shape",
            "emoji_components_only",
            "exact_token_id_reencoding",
        ],
        "candidate_search_counts": search_counts,
        "eligible_candidate_order_sha256": _sha256_bytes(
            _json_bytes(eligible_hash_rows)
        ),
        "eligible_candidate_count": len(eligible),
        "selection_contract": config["selection_contract"],
        "source_comparisons": source_comparisons,
    }


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
    ):
        _require(boundary.get(key) is False, f"claim_boundary.{key} must be false")
    selection_contract = config["selection_contract"]
    _require(
        selection_contract["no_language_model_outcome_inspection"] is True,
        "Outcome inspection must be forbidden",
    )
    _require(
        selection_contract["no_manual_candidate_selection"] is True,
        "Manual selection must be forbidden",
    )
    search_contract = config["search_contract"]
    _require(
        search_contract["strategy"] == "tokenizer_final_token_completion",
        "Unexpected search strategy",
    )
    _require(
        search_contract["final_token_id_end_exclusive"]
        == config["tokenizer"]["vocab_size"],
        "Completion range must end at base vocabulary size",
    )

    config_dir = config_path.parent
    prior_spec = config["prior_negative_branch"]
    prior_path = V0._verified_input(
        config_dir,
        prior_spec["path"],
        prior_spec["sha256"],
        allowed_root=VALIDATION_ROOT,
    )
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    _require(prior.get("status") == prior_spec["required_status"], "Prior branch status differs")
    _require(
        prior.get("eligible_candidate_count")
        == prior_spec["required_eligible_candidate_count"],
        "Prior branch candidate count differs",
    )

    source_audit_spec = config["source_audit"]
    source_audit_path = V0._verified_input(
        config_dir,
        source_audit_spec["path"],
        source_audit_spec["sha256"],
        allowed_root=VALIDATION_ROOT,
    )
    source_audit = json.loads(source_audit_path.read_text(encoding="utf-8"))
    _require(
        source_audit.get("status") == source_audit_spec["required_status"],
        "Source audit status differs",
    )
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
    _require(len(source_specs) == 3, "Exactly three source panels are required")
    source_paths = {
        spec["id"]: V0._verified_input(
            config_dir,
            spec["path"],
            spec["sha256"],
            allowed_root=PANEL_ROOT,
        )
        for spec in source_specs
    }
    V0._source_audit_gate(source_audit, source_specs)

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
        expected = bool(spec["required_source_gate_pass"])
        _require(
            comparison["transfer_gate_pass"] is expected,
            f"Live source gate differs for {spec['id']}",
        )
        source_comparisons[spec["id"]] = V0._compact_comparison(comparison)

    all_source_glyphs = {
        row["glyph"] for rows in source_items.values() for row in rows
    }
    excluded_glyphs = {
        *(row["glyph"] for row in reference_items),
        *all_source_glyphs,
        *search_contract["excluded_exact_glyphs"],
    }
    eligible, search_counts = _enumerate_completion_candidates(
        tokenizer, search_contract, excluded_glyphs
    )
    receipt = _base_receipt(
        config=config,
        config_path=config_path,
        boundary=boundary,
        prior_path=prior_path,
        prior=prior,
        source_audit_path=source_audit_path,
        source_audit=source_audit,
        tokenizer_receipt=tokenizer_receipt,
        search_counts=search_counts,
        eligible=eligible,
        source_comparisons=source_comparisons,
    )
    receipt_filename = config["output_contract"]["receipt_filename"]
    if not eligible:
        receipt.update(
            {
                "status": "no_eligible_tokenizer_completion_graphemes",
                "selected_replacements": [],
                "all_three_generated_panels_match": False,
                "outputs": [],
                "decision": (
                    "The fixed tokenizer-completion universe contains no eligible emoji "
                    "grapheme. Freeze this negative branch and authorize no model forward."
                ),
            }
        )
        return {
            receipt_filename: (
                json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
        }, receipt

    specs_by_id = {spec["id"]: spec for spec in source_specs}
    replacement_order = list(selection_contract["replacement_order"])
    _require(
        replacement_order
        == [spec["id"] for spec in source_specs if spec.get("replacement") is not None],
        "Replacement order must equal source-panel order with replacements",
    )
    final_items = {panel_id: list(rows) for panel_id, rows in source_items.items()}
    selected: list[dict[str, Any]] = []
    selected_glyphs: set[str] = set()
    generated_comparisons: dict[str, dict[str, Any]] = {}
    for panel_id in replacement_order:
        spec = specs_by_id[panel_id]
        replacement = spec["replacement"]
        accepted: dict[str, Any] | None = None
        attempted = 0
        for candidate in eligible:
            if candidate["glyph"] in selected_glyphs:
                continue
            attempted += 1
            trial_items = V0._replace_item(
                source_items[panel_id], replacement["source_item_id"], candidate
            )
            trial_items = [{**row, "panel_id": spec["output_id"]} for row in trial_items]
            trial_summary = AUDIT._summary(
                tokenizer, spec["output_id"], trial_items, wrappers
            )
            comparison = AUDIT._compare_summaries(reference_summary, trial_summary)
            if comparison["transfer_gate_pass"]:
                accepted = dict(candidate)
                accepted["attempted_eligible_candidates_for_this_panel"] = attempted
                accepted["source_panel_id"] = panel_id
                accepted["output_panel_id"] = spec["output_id"]
                accepted["replaced_source_item_id"] = replacement["source_item_id"]
                final_items[panel_id] = trial_items
                generated_comparisons[panel_id] = V0._compact_comparison(comparison)
                break
        _require(accepted is not None, f"No contextual tokenizer match for {panel_id}")
        selected.append(accepted)
        selected_glyphs.add(accepted["glyph"])

    for spec in source_specs:
        panel_id = spec["id"]
        if panel_id in generated_comparisons:
            continue
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
    _require(all(len(values) == 10 for values in final_glyph_sets.values()), "Generated panel size or uniqueness failure")
    _require(all(not values & reference_glyphs for values in final_glyph_sets.values()), "Generated panel overlaps reference")
    neutral_glyphs = set(search_contract["excluded_exact_glyphs"])
    _require(all(not values & neutral_glyphs for values in final_glyph_sets.values()), "Generated panel contains excluded neutral")
    panel_ids = list(final_glyph_sets)
    for index, left in enumerate(panel_ids):
        for right in panel_ids[index + 1 :]:
            _require(
                not final_glyph_sets[left] & final_glyph_sets[right],
                f"Generated panels overlap: {left}, {right}",
            )

    selected_by_glyph = {row["glyph"] for row in selected}
    output_files: dict[str, bytes] = {}
    output_manifest: list[dict[str, Any]] = []
    for index, spec in enumerate(source_specs):
        panel_letter = chr(ord("a") + index)
        canonical_items = _canonical_panel_items(
            tokenizer,
            panel_letter,
            spec["output_id"],
            final_items[spec["id"]],
            selected_by_glyph,
        )
        panel = {
            "schema_version": 1,
            "panel_id": spec["output_id"],
            "status": "tokenizer_matched_control_input_not_scientific",
            "construction": {
                "design_id": config["design_id"],
                "tokenizer_model": config["tokenizer"]["model"],
                "tokenizer_revision": config["tokenizer"]["revision"],
                "selection_rule": selection_contract["rule"],
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

    receipt.update(
        {
            "status": "llama32_m2_tokenizer_matched_control_suite_designed",
            "selected_replacements": selected,
            "generated_comparisons": generated_comparisons,
            "all_three_generated_panels_match": all(
                row["transfer_gate_pass"] for row in generated_comparisons.values()
            ),
            "cross_panel_disjoint": True,
            "reference_disjoint": True,
            "excluded_neutral_absent": True,
            "outputs": output_manifest,
            "decision": (
                "The generated suite is tokenizer-matched input for a separately frozen "
                "Llama exploratory protocol. This design authorizes no language-model "
                "forward and is not a scientific result."
            ),
        }
    )
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
                "all_three_generated_panels_match": receipt.get(
                    "all_three_generated_panels_match", False
                ),
                "eligible_candidate_count": receipt["eligible_candidate_count"],
                "selected_replacements": [
                    {
                        "source_panel_id": row["source_panel_id"],
                        "final_token_id": row["final_token_id"],
                        "codepoints": row["codepoints"],
                        "unicode_names": row["unicode_names"],
                    }
                    for row in receipt.get("selected_replacements", [])
                ],
                "output_dir": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
