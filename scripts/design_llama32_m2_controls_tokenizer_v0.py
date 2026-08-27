#!/usr/bin/env python3
"""Deterministically design Llama 3.2 Milestone 2 controls from tokenizer data.

The script replaces only the source-panel entries that failed the pinned
tokenizer transfer gate. Candidate order, Unicode ranges, semantic exclusions,
and the complete 16-wrapper matching rule are fixed in the input config. It
loads no language-model weights and exposes no target-bank input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable
import unicodedata

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v0.yaml"
DEFAULT_OUTPUT_DIR = (
    ROOT / "validation" / "llama32_3b_instruct_m2_control_design_v0" / "generated"
)
EXPECTED_STATUS = "tokenizer_only_control_design_not_scientific"
PANEL_ROOT = (ROOT / "data" / "emoji_panels").resolve()
WRAPPER_ROOT = (ROOT / "data" / "wrappers").resolve()
VALIDATION_ROOT = (ROOT / "validation").resolve()

AUDIT_SCRIPT = ROOT / "scripts" / "audit_llama32_m2_control_transfer_tokenizer_v0.py"
AUDIT_SPEC = importlib.util.spec_from_file_location("glyphprobe_llama_m2_audit_v0", AUDIT_SCRIPT)
if AUDIT_SPEC is None or AUDIT_SPEC.loader is None:  # pragma: no cover - import invariant
    raise RuntimeError(f"Could not load tokenizer audit helpers: {AUDIT_SCRIPT}")
AUDIT = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(AUDIT)


class DesignError(RuntimeError):
    """Raised when an input or deterministic design invariant fails closed."""


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


def _verified_input(
    config_dir: Path,
    relative: str,
    expected_sha256: str,
    *,
    allowed_root: Path,
) -> Path:
    path = (config_dir / relative).resolve()
    _require(
        path != allowed_root and allowed_root in path.parents,
        f"Input escapes allowed root: {path}",
    )
    _require(path.is_file() and not path.is_symlink(), f"Missing input: {path}")
    actual = _sha256_file(path)
    _require(
        actual == expected_sha256,
        f"Input SHA-256 mismatch for {path.name}: expected {expected_sha256}, got {actual}",
    )
    return path


def _parse_scalar(value: str) -> int:
    _require(isinstance(value, str) and value.startswith("U+"), f"Bad scalar: {value!r}")
    try:
        scalar = int(value[2:], 16)
    except ValueError as exc:
        raise DesignError(f"Bad scalar: {value!r}") from exc
    _require(0 <= scalar <= 0x10FFFF, f"Scalar out of range: {value}")
    _require(not 0xD800 <= scalar <= 0xDFFF, f"Surrogate scalar forbidden: {value}")
    return scalar


def _format_scalar(value: int) -> str:
    return f"U+{value:04X}"


def _iter_scalars(ranges: Iterable[dict[str, str]]) -> Iterable[int]:
    seen: set[int] = set()
    for row in ranges:
        start = _parse_scalar(row["start"])
        end = _parse_scalar(row["end_inclusive"])
        _require(start <= end, f"Reversed scalar range: {row}")
        for scalar in range(start, end + 1):
            _require(scalar not in seen, f"Overlapping scalar ranges at {_format_scalar(scalar)}")
            seen.add(scalar)
            yield scalar


def _name_allowed(name: str, forbidden_terms: Iterable[str]) -> bool:
    upper = name.upper()
    return not any(term.upper() in upper for term in forbidden_terms)


def _enumerate_candidates(
    tokenizer: Any,
    contract: dict[str, Any],
    excluded_glyphs: set[str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    required_count = int(contract["required_raw_token_count"])
    required_prefix = [int(value) for value in contract["required_raw_prefix_token_ids"]]
    allowed_categories = set(contract["allowed_unicode_categories"])
    forbidden_terms = list(contract["forbidden_unicode_name_terms"])
    counts = {
        "total_scalars": 0,
        "excluded_exact_glyph": 0,
        "unassigned_unicode_name": 0,
        "unicode_category_not_allowed": 0,
        "unicode_name_term_forbidden": 0,
        "raw_decode_not_exact": 0,
        "raw_token_count_mismatch": 0,
        "raw_prefix_mismatch": 0,
        "eligible": 0,
    }
    eligible: list[dict[str, Any]] = []
    for scalar in _iter_scalars(contract["scalar_ranges"]):
        counts["total_scalars"] += 1
        glyph = chr(scalar)
        if glyph in excluded_glyphs:
            counts["excluded_exact_glyph"] += 1
            continue
        name = unicodedata.name(glyph, "")
        if not name:
            counts["unassigned_unicode_name"] += 1
            continue
        category = unicodedata.category(glyph)
        if category not in allowed_categories:
            counts["unicode_category_not_allowed"] += 1
            continue
        if not _name_allowed(name, forbidden_terms):
            counts["unicode_name_term_forbidden"] += 1
            continue
        token_ids = [
            int(value) for value in tokenizer.encode(glyph, add_special_tokens=False)
        ]
        decoded = tokenizer.decode(
            token_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        if decoded != glyph:
            counts["raw_decode_not_exact"] += 1
            continue
        if len(token_ids) != required_count:
            counts["raw_token_count_mismatch"] += 1
            continue
        if token_ids[:-1] != required_prefix:
            counts["raw_prefix_mismatch"] += 1
            continue
        eligible.append(
            {
                "candidate_ordinal": len(eligible) + 1,
                "codepoint": _format_scalar(scalar),
                "scalar": scalar,
                "glyph": glyph,
                "unicode_name": name,
                "unicode_category": category,
                "raw_token_ids": token_ids,
                "raw_prefix_token_ids": token_ids[:-1],
            }
        )
        counts["eligible"] += 1
    _require(sum(value for key, value in counts.items() if key != "total_scalars" and key != "eligible") + counts["eligible"] == counts["total_scalars"], "Candidate accounting mismatch")
    return eligible, counts


def _compact_comparison(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "reference_panel_id": value["reference_panel_id"],
        "candidate_panel_id": value["candidate_panel_id"],
        "checks": value["checks"],
        "wrapper_checks": value["wrapper_checks"],
        "transfer_gate_pass": value["transfer_gate_pass"],
    }


def _source_audit_gate(
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
        _require(panel_id in comparisons, f"Source audit lacks comparison for {panel_id}")
        observed = bool(comparisons[panel_id]["transfer_gate_pass"])
        _require(
            observed is bool(spec["required_source_gate_pass"]),
            f"Source gate differs for {panel_id}",
        )
        replacement = spec.get("replacement")
        if replacement is None:
            continue
        _require(panel_id in candidates, f"Source audit lacks profiles for {panel_id}")
        profiles = {
            row["id"]: row for row in candidates[panel_id].get("raw_profiles", [])
        }
        source_item_id = replacement["source_item_id"]
        _require(source_item_id in profiles, f"Source audit lacks {source_item_id}")
        profile = profiles[source_item_id]
        _require(profile["glyph"] == replacement["expected_glyph"], "Failed glyph differs")
        _require(
            _format_scalar(ord(profile["glyph"])) == replacement["expected_codepoint"],
            "Failed codepoint differs",
        )
        _require(
            profile["token_ids"] == replacement["expected_raw_token_ids"],
            "Failed token ids differ",
        )


def _replace_item(
    items: list[dict[str, str]],
    source_item_id: str,
    candidate: dict[str, Any],
) -> list[dict[str, str]]:
    replaced = 0
    output: list[dict[str, str]] = []
    for row in items:
        copy = dict(row)
        if row["id"] == source_item_id:
            copy["glyph"] = candidate["glyph"]
            replaced += 1
        output.append(copy)
    _require(replaced == 1, f"Expected one replacement for {source_item_id}, got {replaced}")
    return output


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
        scalar = ord(row["glyph"])
        prefix = "p" + "_".join(str(value) for value in token_ids[:-1])
        output.append(
            {
                "id": f"llama32_null_{panel_letter}_u{scalar:04x}",
                "glyph": row["glyph"],
                "factors": {
                    "control_family": output_panel_id,
                    "prefix_stratum": prefix,
                    "construction_role": (
                        "deterministic_tokenizer_only_replacement"
                        if row["glyph"] in selected_glyphs
                        else "retained_tokenizer_compatible_source_glyph"
                    ),
                },
                "labels": [],
            }
        )
    return output


def _panel_bytes(panel: dict[str, Any]) -> bytes:
    rendered = yaml.safe_dump(
        panel,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    return rendered.encode("utf-8")


def _write_output_directory_no_overwrite(
    output_dir: Path,
    files: dict[str, bytes],
) -> None:
    output_dir = output_dir.resolve()
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_dir.mkdir()
    except FileExistsError as exc:
        raise DesignError(f"Refusing to overwrite existing output directory: {output_dir}") from exc
    try:
        for filename, payload in files.items():
            _require(Path(filename).name == filename, f"Output filename is not flat: {filename}")
            path = output_dir / filename
            fd, temporary_name = tempfile.mkstemp(prefix=f".{filename}.", dir=output_dir)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.link(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
    except Exception:
        # Keep any partial directory as a visible failure receipt; never overwrite it.
        raise


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
    _require(selection_contract["no_language_model_outcome_inspection"] is True, "Outcome inspection must be forbidden")
    _require(selection_contract["no_manual_candidate_selection"] is True, "Manual selection must be forbidden")

    config_dir = config_path.parent
    source_audit_spec = config["source_audit"]
    source_audit_path = _verified_input(
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
    reference_path = _verified_input(
        config_dir,
        reference_spec["path"],
        reference_spec["sha256"],
        allowed_root=PANEL_ROOT,
    )
    source_specs = list(config["source_panels"])
    _require(len(source_specs) == 3, "Exactly three source panels are required")
    source_paths = {
        spec["id"]: _verified_input(
            config_dir,
            spec["path"],
            spec["sha256"],
            allowed_root=PANEL_ROOT,
        )
        for spec in source_specs
    }
    _source_audit_gate(source_audit, source_specs)

    wrapper_spec = config["wrappers"]
    wrapper_path = _verified_input(
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
        _require(comparison["transfer_gate_pass"] is expected, f"Live source gate differs for {spec['id']}")
        source_comparisons[spec["id"]] = _compact_comparison(comparison)

    all_source_glyphs = {
        row["glyph"]
        for rows in source_items.values()
        for row in rows
    }
    excluded_glyphs = {
        *(row["glyph"] for row in reference_items),
        *all_source_glyphs,
        *config["search_contract"]["excluded_exact_glyphs"],
    }
    eligible, search_counts = _enumerate_candidates(
        tokenizer, config["search_contract"], excluded_glyphs
    )
    if not eligible:
        receipt = {
            "schema_version": 1,
            "design_id": config["design_id"],
            "status": "no_eligible_single_scalar_tokenizer_matches",
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
            "search_contract": config["search_contract"],
            "search_filter_order": [
                "excluded_exact_glyph",
                "assigned_unicode_name",
                "allowed_unicode_category",
                "forbidden_unicode_name_terms",
                "exact_raw_decode",
                "raw_token_count",
                "raw_prefix_token_ids",
            ],
            "candidate_search_counts": search_counts,
            "eligible_candidate_order_sha256": _sha256_bytes(_json_bytes([])),
            "eligible_candidate_count": 0,
            "selected_replacements": [],
            "source_comparisons": source_comparisons,
            "all_three_generated_panels_match": False,
            "outputs": [],
            "decision": (
                "The fixed single-scalar search universe contains no unused candidate "
                "with the required Llama tokenizer structure. Freeze this negative branch; "
                "do not run a language-model forward and do not silently broaden the search."
            ),
        }
        receipt_filename = config["output_contract"]["receipt_filename"]
        output_files = {
            receipt_filename: (
                json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            ).encode("utf-8")
        }
        return output_files, receipt

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
            trial_items = _replace_item(
                source_items[panel_id], replacement["source_item_id"], candidate
            )
            trial_items = [
                {**row, "panel_id": spec["output_id"]} for row in trial_items
            ]
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
                generated_comparisons[panel_id] = _compact_comparison(comparison)
                break
        _require(accepted is not None, f"No contextual tokenizer match for {panel_id}")
        selected.append(accepted)
        selected_glyphs.add(accepted["glyph"])

    # The pass-through panel is independently rechecked under its new panel id.
    for spec in source_specs:
        panel_id = spec["id"]
        if panel_id in generated_comparisons:
            continue
        relabeled = [{**row, "panel_id": spec["output_id"]} for row in final_items[panel_id]]
        final_items[panel_id] = relabeled
        summary = AUDIT._summary(tokenizer, spec["output_id"], relabeled, wrappers)
        comparison = AUDIT._compare_summaries(reference_summary, summary)
        _require(comparison["transfer_gate_pass"] is True, f"Generated panel failed: {panel_id}")
        generated_comparisons[panel_id] = _compact_comparison(comparison)

    reference_glyphs = {row["glyph"] for row in reference_items}
    final_glyph_sets = {
        panel_id: {row["glyph"] for row in rows}
        for panel_id, rows in final_items.items()
    }
    _require(all(len(values) == 10 for values in final_glyph_sets.values()), "Generated panel size or uniqueness failure")
    _require(all(not values & reference_glyphs for values in final_glyph_sets.values()), "Generated panel overlaps reference")
    neutral_glyphs = set(config["search_contract"]["excluded_exact_glyphs"])
    _require(all(not values & neutral_glyphs for values in final_glyph_sets.values()), "Generated panel contains excluded neutral")
    panel_ids = list(final_glyph_sets)
    for index, left in enumerate(panel_ids):
        for right in panel_ids[index + 1 :]:
            _require(not final_glyph_sets[left] & final_glyph_sets[right], f"Generated panels overlap: {left}, {right}")

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
        payload = _panel_bytes(panel)
        output_files[filename] = payload
        output_manifest.append(
            {
                "filename": filename,
                "panel_id": spec["output_id"],
                "bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )

    eligible_hash_rows = [
        {
            key: row[key]
            for key in (
                "candidate_ordinal",
                "codepoint",
                "glyph",
                "unicode_name",
                "unicode_category",
                "raw_token_ids",
            )
        }
        for row in eligible
    ]
    receipt = {
        "schema_version": 1,
        "design_id": config["design_id"],
        "status": "llama32_m2_tokenizer_matched_control_suite_designed",
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
        },
        "source_audit": {
            "path": str(source_audit_path.relative_to(ROOT)),
            "sha256": _sha256_file(source_audit_path),
            "status": source_audit["status"],
            "all_three_transfer_gate_pass": source_audit["all_three_transfer_gate_pass"],
        },
        "tokenizer": tokenizer_receipt,
        "unicode_database_version": unicodedata.unidata_version,
        "search_contract": config["search_contract"],
        "search_filter_order": [
            "excluded_exact_glyph",
            "assigned_unicode_name",
            "allowed_unicode_category",
            "forbidden_unicode_name_terms",
            "exact_raw_decode",
            "raw_token_count",
            "raw_prefix_token_ids",
        ],
        "candidate_search_counts": search_counts,
        "eligible_candidate_order_sha256": _sha256_bytes(_json_bytes(eligible_hash_rows)),
        "eligible_candidate_count": len(eligible_hash_rows),
        "selection_contract": selection_contract,
        "selected_replacements": selected,
        "source_comparisons": source_comparisons,
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
            "Llama exploratory protocol. This design authorizes no language-model forward "
            "and is not a scientific result."
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
    _write_output_directory_no_overwrite(args.output_dir, files)
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
                        "codepoint": row["codepoint"],
                        "unicode_name": row["unicode_name"],
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
