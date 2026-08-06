#!/usr/bin/env python3
"""Fail-closed tokenizer-only preflight for the frozen E1 emoji-family screen.

The audit loads a pinned tokenizer, never a language model. It binds the five
panels, five MLX configs, exploratory targets, source wrappers, MLX parity
receipt, excluded holdouts, and the prespecified analysis implementation to one
hard-pinned manifest before any E1 model forward is authorized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unicodedata
from typing import Any, Iterable

import yaml


EXPECTED_MANIFEST_ID = "emoji_family_exploratory_v1"
EXPECTED_PROTOCOL_ID = "glyphprobe-e1-token-isomorphic-emoji-families-v1"
EXPECTED_MANIFEST_SHA256 = (
    "9fb96d5808dc298cbd47ca3586e0f00f793ce23e6627ef7705016f02e1c1d583"
)
EXPECTED_MODEL_ID = "openai-community/gpt2"
EXPECTED_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
MANIFEST_PATH = Path("data/manifests/emoji_family_exploratory_v1.json")
PENDING_ANALYSIS_SHA256 = "PENDING_ANALYZER_SHA256"
FORBIDDEN_TARGET_PATHS = {
    "data/targets/p2_confirmatory_targets_v1.jsonl",
    "data/targets/c1_causal_holdout_targets_v1.jsonl",
}
KNOWN_EXCLUDED_BANK_SHA256 = {
    "data/targets/p2_confirmatory_targets_v1.jsonl": (
        "9913f1c33d611b86ff9f5518fe8203319967187e060b3e6a222ce4e3cf27b324"
    ),
    "data/targets/c1_causal_holdout_targets_v1.jsonl": (
        "8d63cbcd2dd1aa9fb9a40f0217bbcbadde4309c39582fc06fcae0d5892011986"
    ),
}
EXPECTED_ANALYSIS_ENDPOINT_IDS = {
    "within_family_slot_separation_M_diag",
    "ordered_cross_family_same_slot_transfer_M_offdiag",
    "family_specificity_R",
    "equal_family_global_specificity_R_global",
}
EXPECTED_ANALYSIS_ENDPOINTS = {
    "M": {
        "within_family_id": "within_family_slot_separation_M_diag",
        "ordered_cross_family_id": (
            "ordered_cross_family_same_slot_transfer_M_offdiag"
        ),
        "target_value": (
            "seed-averaged matched-slot cosine minus the mean cosine to the nine "
            "mismatched slots"
        ),
        "cell_estimand": (
            "arithmetic mean across the 24 selected target prompts; target median is "
            "secondary description only"
        ),
    },
    "R": {
        "id": "family_specificity_R",
        "target_value": (
            "M[f<-f,t] minus median over M[f<-g,t] for the four g != f prototype "
            "families"
        ),
        "cell_estimand": "arithmetic mean across the 24 selected target prompts",
    },
    "R_global": {
        "id": "equal_family_global_specificity_R_global",
        "cell_estimand": (
            "equal-weight arithmetic mean of the five family-specific R means"
        ),
    },
}
EXPECTED_ANALYSIS_MEAN_ESTIMAND = (
    "Every M and R family/pair cell uses the arithmetic mean across the 24 fixed "
    "targets; R_global is the equal-weight arithmetic mean of the five family R "
    "means. Target medians are secondary descriptions only."
)
EXPECTED_ANALYSIS_CLI_ROLE_ARGUMENTS = {
    "--sky-run": "sky",
    "--food-run": "food",
    "--animals-run": "animals",
    "--transport-run": "transport",
    "--social-run": "social",
    "--output-dir": "output_directory",
}
EXPECTED_ANALYSIS_DESIGN = {
    "secondary_layer_role": "prespecified_negative_comparator",
    "sampling_unit": "target_prompt_cluster",
    "stratification": (
        "four selected targets sampled with replacement inside each of six fixed groups"
    ),
    "paired_resampling": True,
    "rebuild_loto_prototypes_inside_each_replicate": True,
    "direction_seeds_nested_within_target": True,
    "p_values": False,
    "multiplicity_decisions": False,
}
EXPECTED_ANALYSIS_OUTPUTS = [
    "family_target_scores.jsonl",
    "transfer_target_scores.jsonl",
    "family_cell_summary.jsonl",
    "transfer_cell_summary.jsonl",
    "emoji_family_exploratory_receipt.json",
    "report.md",
]
EXPECTED_ANALYSIS_ROW_COUNTS = {
    "family_target_scores.jsonl": 240,
    "transfer_target_scores.jsonl": 960,
    "family_cell_summary.jsonl": 10,
    "transfer_cell_summary.jsonl": 40,
}
EXPECTED_OUTPUT_UNIQUE_KEYS = {
    "family_target_scores.jsonl": ["family", "layer", "target_id"],
    "transfer_target_scores.jsonl": [
        "source_family",
        "prototype_family",
        "layer",
        "target_id",
    ],
    "family_cell_summary.jsonl": ["family", "layer"],
    "transfer_cell_summary.jsonl": ["source_family", "prototype_family", "layer"],
}


class AuditError(RuntimeError):
    """Raised when any E1 freeze invariant fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verified_path(root: Path, relative_path: str, expected_sha256: str) -> Path:
    path = (root / relative_path).resolve()
    _require(path.is_file(), f"missing pinned file: {relative_path}")
    actual = _sha256(path)
    _require(
        actual == expected_sha256,
        f"SHA-256 mismatch for {relative_path}: expected {expected_sha256}, got {actual}",
    )
    return path


def _load_manifest(root: Path) -> tuple[dict[str, Any], str]:
    path = (root / MANIFEST_PATH).resolve()
    _require(path.is_file(), f"missing manifest: {MANIFEST_PATH}")
    actual = _sha256(path)
    _require(
        actual == EXPECTED_MANIFEST_SHA256,
        "manifest SHA-256 is not the hard-pinned E1 suite identity: "
        f"expected {EXPECTED_MANIFEST_SHA256}, got {actual}",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    _require(manifest.get("schema_version") == 1, "unsupported E1 manifest schema")
    _require(
        manifest.get("manifest_id") == EXPECTED_MANIFEST_ID, "unexpected manifest ID"
    )
    _require(
        manifest.get("protocol_id") == EXPECTED_PROTOCOL_ID, "unexpected protocol ID"
    )
    freeze = manifest.get("freeze", {})
    _require(
        freeze.get("status") == "frozen_by_public_commit_containing_this_manifest",
        "public-commit freeze status differs",
    )
    _require(
        freeze.get("prepared_before_e1_model_forward") is True,
        "forward freeze declaration missing",
    )
    _require(
        freeze.get("prepared_before_e1_outcome_inspection") is True,
        "outcome-inspection freeze declaration missing",
    )
    tokenizer = manifest.get("tokenizer", {})
    _require(
        tokenizer.get("model_id") == EXPECTED_MODEL_ID, "unexpected tokenizer model"
    )
    _require(
        tokenizer.get("revision") == EXPECTED_REVISION, "unexpected tokenizer revision"
    )
    return manifest, actual


def _load_pinned_tokenizer(manifest: dict[str, Any]) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - environment-specific message
        raise AuditError(
            "transformers is required for the tokenizer-only E1 preflight"
        ) from exc

    spec = manifest["tokenizer"]
    tokenizer = AutoTokenizer.from_pretrained(
        spec["model_id"],
        revision=spec["revision"],
        local_files_only=bool(spec["local_files_only"]),
    )
    _require(
        type(tokenizer).__name__ == spec["tokenizer_class"], "tokenizer class mismatch"
    )
    _require(
        int(tokenizer.vocab_size) == int(spec["vocab_size"]), "tokenizer vocab mismatch"
    )
    _require(
        bool(getattr(tokenizer, "is_fast", False)),
        "wrapper audit requires a fast tokenizer",
    )

    # Preserve the revision-bearing snapshot path instead of resolving cache symlinks.
    vocab_file = Path(str(tokenizer.init_kwargs.get("vocab_file", ""))).absolute()
    _require(vocab_file.is_file(), "tokenizer did not expose its pinned vocab file")
    snapshot_dir = vocab_file.parent
    _require(
        snapshot_dir.name == spec["revision"],
        "resolved tokenizer snapshot directory does not equal the pinned revision",
    )
    for filename, expected in spec["assets_sha256"].items():
        asset = snapshot_dir / filename
        _require(asset.is_file(), f"missing tokenizer asset: {filename}")
        actual = _sha256(asset)
        _require(
            actual == expected,
            f"tokenizer asset SHA-256 mismatch for {filename}: expected {expected}, got {actual}",
        )
    return tokenizer


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        _require(isinstance(value, dict), f"expected object at {path}:{line_number}")
        rows.append(value)
    return rows


def _load_wrappers(path: Path) -> list[dict[str, str]]:
    wrappers: list[dict[str, str]] = []
    for line_number, row in enumerate(_read_jsonl(path), 1):
        wrapper_id = row.get("id")
        template = row.get("template")
        _require(
            isinstance(wrapper_id, str) and wrapper_id,
            f"wrapper {line_number} has no ID",
        )
        _require(isinstance(template, str), f"wrapper {line_number} has no template")
        _require(
            template.count("{emoji}") == 1,
            f"wrapper {wrapper_id} must contain exactly one emoji placeholder",
        )
        wrappers.append({"id": wrapper_id, "template": template})
    _require(
        len({row["id"] for row in wrappers}) == len(wrappers),
        "wrapper IDs are not unique",
    )
    return wrappers


def _load_panel(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    values = raw.get("items") if isinstance(raw, dict) else raw
    _require(isinstance(values, list), f"panel is not an item list: {path}")
    output: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        _require(isinstance(item, dict), f"panel item {index} is not a mapping: {path}")
        _require(
            isinstance(item.get("id"), str) and item["id"], f"missing item ID: {path}"
        )
        _require(
            isinstance(item.get("glyph"), str) and item["glyph"],
            f"missing glyph: {path}",
        )
        _require(isinstance(item.get("factors"), dict), f"missing factors: {path}")
        _require(isinstance(item.get("labels"), list), f"invalid labels: {path}")
        output.append(item)
    _require(
        len({item["id"] for item in output}) == len(output),
        f"duplicate item IDs: {path}",
    )
    _require(
        len({item["glyph"] for item in output}) == len(output),
        f"duplicate glyphs: {path}",
    )
    return output


def _parse_codepoint(value: str) -> int:
    _require(
        isinstance(value, str) and value.startswith("U+"),
        f"invalid codepoint label: {value!r}",
    )
    try:
        return int(value[2:], 16)
    except ValueError as exc:
        raise AuditError(f"invalid codepoint label: {value!r}") from exc


def _validate_scalar(
    item: dict[str, Any],
    panel_spec: dict[str, Any],
    slot_index: int,
    tokenizer: Any,
    contract: dict[str, Any],
) -> dict[str, Any]:
    item_id = item["id"]
    glyph = item["glyph"]
    expected_codepoint = _parse_codepoint(panel_spec["codepoint_start"]) + slot_index
    expected_codepoint_label = f"U+{expected_codepoint:04X}"
    expected_slot = f"slot_{slot_index:02d}"
    expected_id = f"{panel_spec['factor_family']}_{expected_slot}"
    _require(
        item_id == expected_id,
        f"{panel_spec['id']}: expected item ID {expected_id}, got {item_id}",
    )
    _require(
        len(glyph) == int(contract["required_unicode_scalar_count"]),
        f"{item_id}: glyph must be exactly one Unicode scalar",
    )
    codepoint = ord(glyph)
    _require(
        codepoint == expected_codepoint,
        f"{item_id}: codepoint order differs from manifest",
    )
    _require(
        not 0xD800 <= codepoint <= 0xDFFF,
        f"{item_id}: surrogate code point is forbidden",
    )
    unicode_name = unicodedata.name(glyph, "")
    _require(bool(unicode_name), f"{item_id}: Unicode scalar is unassigned")
    utf8 = glyph.encode("utf-8")
    _require(
        len(utf8) == int(contract["required_utf8_byte_length"]),
        f"{item_id}: expected {contract['required_utf8_byte_length']} UTF-8 bytes",
    )
    factors = item["factors"]
    _require(
        factors.get("family") == panel_spec["factor_family"],
        f"{item_id}: family factor mismatch",
    )
    _require(
        factors.get("matched_slot") == expected_slot, f"{item_id}: slot factor mismatch"
    )
    _require(
        factors.get("codepoint") == expected_codepoint_label,
        f"{item_id}: codepoint factor mismatch",
    )
    _require(
        item["labels"]
        and all(isinstance(value, str) and value for value in item["labels"]),
        f"{item_id}: labels must contain non-empty strings",
    )

    raw_ids = [
        int(value) for value in tokenizer.encode(glyph, add_special_tokens=False)
    ]
    expected_ids = [
        int(contract["shared_first_token_id"]),
        int(panel_spec["family_middle_token_id"]),
        int(contract["shared_slot_suffix_token_ids"][slot_index]),
    ]
    _require(
        len(raw_ids) == int(contract["required_raw_token_count"]),
        f"{item_id}: expected {contract['required_raw_token_count']} raw tokens, got {raw_ids}",
    )
    _require(
        raw_ids == expected_ids,
        f"{item_id}: expected raw IDs {expected_ids}, got {raw_ids}",
    )
    decoded = tokenizer.decode(raw_ids, clean_up_tokenization_spaces=False)
    _require(decoded == glyph, f"{item_id}: tokenizer decode round trip failed")
    return {
        "id": item_id,
        "glyph": glyph,
        "slot": expected_slot,
        "codepoint": expected_codepoint_label,
        "unicode_name": unicode_name,
        "unicode_category": unicodedata.category(glyph),
        "utf8_hex": utf8.hex(),
        "raw_token_ids": raw_ids,
        "decoded_round_trip": True,
    }


def _wrapper_profile(
    tokenizer: Any, wrapper: dict[str, str], glyph: str
) -> dict[str, Any]:
    prefix, suffix = wrapper["template"].split("{emoji}")
    rendered = prefix + glyph + suffix
    start = len(prefix)
    end = start + len(glyph)
    encoded = tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True)
    token_ids = [int(value) for value in encoded["input_ids"]]
    offsets = [(int(left), int(right)) for left, right in encoded["offset_mapping"]]
    positions = [
        index
        for index, (token_start, token_end) in enumerate(offsets)
        if token_start < end and token_end > start
    ]
    _require(
        positions, f"{wrapper['id']}: tokenizer offsets did not locate glyph {glyph}"
    )
    _require(
        positions == list(range(positions[0], positions[-1] + 1)),
        f"{wrapper['id']}: glyph token positions are not contiguous for {glyph}",
    )
    return {
        "wrapper_id": wrapper["id"],
        "token_count": len(token_ids),
        "glyph_token_positions": positions,
        "glyph_span_token_ids": [token_ids[index] for index in positions],
        "outside_span_token_ids": [
            value for index, value in enumerate(token_ids) if index not in positions
        ],
    }


def _validate_wrapper_isomorphism(
    tokenizer: Any,
    wrappers: list[dict[str, str]],
    panel_reports: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    profiles: dict[tuple[str, int, str], dict[str, Any]] = {}
    for panel in panel_reports:
        for slot_index, item in enumerate(panel["items"]):
            for wrapper in wrappers:
                profile = _wrapper_profile(tokenizer, wrapper, item["glyph"])
                _require(
                    profile["glyph_span_token_ids"][1:] == item["raw_token_ids"][1:],
                    (
                        f"{panel['id']}/{item['id']}/{wrapper['id']}: wrapper middle/suffix "
                        "tokens differ from the raw matched-slot contract"
                    ),
                )
                _require(
                    len(profile["glyph_span_token_ids"]) == 3,
                    f"{panel['id']}/{item['id']}/{wrapper['id']}: wrapper glyph span is not three tokens",
                )
                profiles[(panel["role"], slot_index, wrapper["id"])] = profile

    output: list[dict[str, Any]] = []
    first_panel = panel_reports[0]
    first_role = first_panel["role"]
    comparison_count = 0
    for wrapper in wrappers:
        wrapper_id = wrapper["id"]
        canonical = profiles[(first_role, 0, wrapper_id)]
        for panel in panel_reports:
            for slot_index in range(len(panel["items"])):
                current = profiles[(panel["role"], slot_index, wrapper_id)]
                _require(
                    current["token_count"] == canonical["token_count"],
                    f"{panel['id']}/slot_{slot_index:02d}/{wrapper_id}: total token count differs",
                )
                _require(
                    current["glyph_token_positions"]
                    == canonical["glyph_token_positions"],
                    f"{panel['id']}/slot_{slot_index:02d}/{wrapper_id}: glyph positions differ",
                )
                _require(
                    current["outside_span_token_ids"]
                    == canonical["outside_span_token_ids"],
                    f"{panel['id']}/slot_{slot_index:02d}/{wrapper_id}: outside-span tokens differ",
                )
                comparison_count += 1

        for slot_index in range(len(first_panel["items"])):
            slot_profiles = [
                profiles[(panel["role"], slot_index, wrapper_id)]
                for panel in panel_reports
            ]
            first_tokens = {row["glyph_span_token_ids"][0] for row in slot_profiles}
            third_tokens = {row["glyph_span_token_ids"][2] for row in slot_profiles}
            _require(
                len(first_tokens) == 1,
                f"slot_{slot_index:02d}/{wrapper_id}: first token differs",
            )
            _require(
                len(third_tokens) == 1,
                f"slot_{slot_index:02d}/{wrapper_id}: third token differs",
            )

        output.append(
            {
                "wrapper_id": wrapper_id,
                "token_count": canonical["token_count"],
                "glyph_token_positions": canonical["glyph_token_positions"],
                "glyph_span_token_count": len(canonical["glyph_span_token_ids"]),
                "wrapper_span_first_token_id": canonical["glyph_span_token_ids"][0],
                "outside_span_token_ids": canonical["outside_span_token_ids"],
                "profiles_verified": len(panel_reports) * len(first_panel["items"]),
            }
        )
    return output, comparison_count


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(key)
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item)


def _expect_equal(actual: Any, expected: Any, label: str) -> None:
    _require(
        actual == expected, f"{label} differs: expected {expected!r}, got {actual!r}"
    )


def _resolve_from_config(config_path: Path, value: str) -> Path:
    path = Path(value)
    return (
        path.resolve() if path.is_absolute() else (config_path.parent / path).resolve()
    )


def _expected_plan_counts(config: dict[str, Any], panel_size: int) -> dict[str, int]:
    wrapper_count = int(config["source"]["max_wrappers"])
    target_count = int(config["targets"]["max_cases"])
    layer_count = len(config["capture"]["layers"])
    seed_count = len(config["run"]["seeds"])
    strength_count = len(config["intervention"]["strengths"])
    negative_count = (
        len(config["controls"]["sign_flip_strengths"])
        if config["controls"]["sign_flip"]
        else 0
    )
    source = (panel_size + 1) * wrapper_count
    baseline = target_count
    emoji = (
        panel_size
        * layer_count
        * target_count
        * seed_count
        * (strength_count + negative_count)
    )
    random = (
        int(config["controls"]["random_directions_per_layer"])
        * layer_count
        * target_count
        * seed_count
        * strength_count
    )
    generic = (
        layer_count * target_count * seed_count * strength_count
        if config["controls"]["include_neutral_direction"]
        else 0
    )
    zero = layer_count * target_count if config["controls"]["zero_direction"] else 0
    interventions = emoji + random + generic + zero
    return {
        "source": source,
        "target_baseline": baseline,
        "emoji_intervention": emoji,
        "random_control": random,
        "generic_emoji_control": generic,
        "zero_hook_control": zero,
        "total": source + baseline + interventions,
        "intervention_rows": interventions,
    }


def _validate_config(
    root: Path,
    panel_spec: dict[str, Any],
    panel_path: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    config_path = _verified_path(
        root, panel_spec["config_path"], panel_spec["config_sha256"]
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    _require(
        isinstance(config, dict),
        f"config is not a mapping: {panel_spec['config_path']}",
    )
    fixed = manifest["fixed_execution_cell"]
    source_spec = manifest["shared_inputs"]["source"]
    target_spec = manifest["shared_inputs"]["target"]
    parity_spec = manifest["shared_inputs"]["parity"]

    _expect_equal(config.get("schema_version"), 1, f"{config_path}: schema_version")
    _expect_equal(config.get("mode"), fixed["mode"], f"{config_path}: mode")
    for key, expected in fixed["backend"].items():
        _expect_equal(
            config["backend"].get(key), expected, f"{config_path}: backend.{key}"
        )
    _expect_equal(
        config["run"].get("name"), panel_spec["run_name"], f"{config_path}: run.name"
    )
    for key, expected in fixed["run"].items():
        _expect_equal(config["run"].get(key), expected, f"{config_path}: run.{key}")

    resolved_panel = _resolve_from_config(config_path, config["panel"]["file"])
    resolved_source = _resolve_from_config(
        config_path, config["source"]["wrappers_file"]
    )
    resolved_target = _resolve_from_config(config_path, config["targets"]["cases_file"])
    resolved_parity = _resolve_from_config(
        config_path, config["backend"]["validation_receipt"]
    )
    _expect_equal(resolved_panel, panel_path, f"{config_path}: resolved panel")
    _expect_equal(
        resolved_source,
        (root / source_spec["path"]).resolve(),
        f"{config_path}: resolved source",
    )
    _expect_equal(
        resolved_target,
        (root / target_spec["path"]).resolve(),
        f"{config_path}: resolved target",
    )
    _expect_equal(
        resolved_parity,
        (root / parity_spec["path"]).resolve(),
        f"{config_path}: resolved parity",
    )
    _expect_equal(
        config["backend"].get("validation_receipt_sha256"),
        parity_spec["sha256"],
        f"{config_path}: parity receipt SHA",
    )
    relative_target = resolved_target.relative_to(root).as_posix()
    _require(
        relative_target not in FORBIDDEN_TARGET_PATHS,
        f"{config_path}: forbidden P2/C1 target path",
    )
    serialized_strings = list(_iter_strings(config))
    for forbidden in FORBIDDEN_TARGET_PATHS:
        _require(
            all(Path(forbidden).name not in value for value in serialized_strings),
            f"{config_path}: forbidden holdout filename appears in config: {forbidden}",
        )

    _expect_equal(
        config["panel"].get("neutral_glyph"),
        fixed["panel"]["neutral_glyph"],
        f"{config_path}: neutral",
    )
    _expect_equal(
        config["panel"].get("centroid_mode"),
        fixed["panel"]["centroid_mode"],
        f"{config_path}: centroid",
    )
    for key, expected in fixed["source"].items():
        _expect_equal(
            config["source"].get(key), expected, f"{config_path}: source.{key}"
        )
    for key, expected in fixed["targets"].items():
        _expect_equal(
            config["targets"].get(key), expected, f"{config_path}: targets.{key}"
        )
    for key, expected in fixed["capture"].items():
        _expect_equal(
            config["capture"].get(key), expected, f"{config_path}: capture.{key}"
        )
    for key in ("mode", "normalization", "strengths", "position", "clip"):
        _expect_equal(
            config["intervention"].get(key),
            fixed["intervention"][key],
            f"{config_path}: intervention.{key}",
        )
    _expect_equal(
        config["intervention"].get("iso_kl", {}).get("enabled"),
        fixed["intervention"]["iso_kl_enabled"],
        f"{config_path}: intervention.iso_kl.enabled",
    )
    for key, expected in fixed["controls"].items():
        _expect_equal(
            config["controls"].get(key), expected, f"{config_path}: controls.{key}"
        )
    for key, expected in fixed["metrics"].items():
        _expect_equal(
            config["metrics"].get(key), expected, f"{config_path}: metrics.{key}"
        )
    _expect_equal(
        config["sae"].get("enabled"),
        fixed["sae_enabled"],
        f"{config_path}: sae.enabled",
    )
    for key, expected in fixed["surface"].items():
        _expect_equal(
            config["surface"].get(key), expected, f"{config_path}: surface.{key}"
        )

    plan = _expected_plan_counts(
        config, int(manifest["token_isomorphism"]["conditions_per_panel"])
    )
    _expect_equal(
        plan, fixed["expected_forward_calls_per_family"], f"{config_path}: plan counts"
    )
    return {
        "role": panel_spec["role"],
        "config_path": panel_spec["config_path"],
        "config_sha256": panel_spec["config_sha256"],
        "run_name": panel_spec["run_name"],
        "resolved_panel_path": panel_spec["path"],
        "resolved_source_path": source_spec["path"],
        "resolved_target_path": target_spec["path"],
        "resolved_parity_path": parity_spec["path"],
        "forbidden_holdout_path_used": False,
        "plan": plan,
    }


def _validate_role_bindings(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    source = manifest["shared_inputs"]["source"]
    target = manifest["shared_inputs"]["target"]
    parity = manifest["shared_inputs"]["parity"]
    expected = [
        {
            "role": panel["role"],
            "panel_path": panel["path"],
            "panel_sha256": panel["sha256"],
            "config_path": panel["config_path"],
            "config_sha256": panel["config_sha256"],
            "target_path": target["path"],
            "target_sha256": target["sha256"],
            "source_path": source["path"],
            "source_sha256": source["sha256"],
            "parity_path": parity["path"],
            "parity_sha256": parity["sha256"],
        }
        for panel in manifest["panels"]
    ]
    actual = manifest.get("role_bindings")
    _require(isinstance(actual, list), "role-specific input bindings are missing")
    _expect_equal(
        sorted(actual, key=lambda row: row["role"]),
        sorted(expected, key=lambda row: row["role"]),
        "role-specific panel/config/target/source/parity bindings",
    )
    return actual


def _validate_analysis_binding(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    spec = manifest["fixed_analysis"]
    expected = spec.get("script_sha256")
    _require(
        isinstance(expected, str)
        and expected != PENDING_ANALYSIS_SHA256
        and len(expected) == 64,
        "analysis implementation SHA-256 is still pending; executable E1 freeze is incomplete",
    )
    path = _verified_path(root, spec["script_path"], expected)
    _require(
        int(spec["bootstrap_resamples"]) == 20000, "bootstrap replicate count differs"
    )
    _require(int(spec["bootstrap_seed"]) == 20260808, "bootstrap seed differs")
    _require(int(spec["primary_layer"]) == 2, "primary exploratory layer differs")
    _require(int(spec["secondary_layer"]) == 4, "secondary comparator layer differs")
    _expect_equal(
        spec.get("endpoints"), EXPECTED_ANALYSIS_ENDPOINTS, "analysis endpoints"
    )
    endpoint_ids = {
        spec["endpoints"]["M"]["within_family_id"],
        spec["endpoints"]["M"]["ordered_cross_family_id"],
        spec["endpoints"]["R"]["id"],
        spec["endpoints"]["R_global"]["id"],
    }
    _require(
        endpoint_ids == EXPECTED_ANALYSIS_ENDPOINT_IDS, "analysis endpoint IDs differ"
    )
    _require(
        spec.get("output_filenames") == EXPECTED_ANALYSIS_OUTPUTS,
        "analysis output filenames differ",
    )
    _require(
        spec.get("expected_output_rows") == EXPECTED_ANALYSIS_ROW_COUNTS,
        "analysis output row counts differ",
    )
    _require(
        spec.get("output_unique_keys") == EXPECTED_OUTPUT_UNIQUE_KEYS,
        "analysis output unique-key contracts differ",
    )
    _require(
        spec.get("mean_estimand") == EXPECTED_ANALYSIS_MEAN_ESTIMAND,
        "mean estimand differs",
    )
    _expect_equal(
        spec.get("cli_role_arguments"),
        EXPECTED_ANALYSIS_CLI_ROLE_ARGUMENTS,
        "analysis CLI role arguments",
    )
    for key, expected_value in EXPECTED_ANALYSIS_DESIGN.items():
        _expect_equal(spec.get(key), expected_value, f"analysis design field {key}")
    return {
        "script_path": spec["script_path"],
        "script_sha256": _sha256(path),
        "bootstrap_resamples": int(spec["bootstrap_resamples"]),
        "bootstrap_seed": int(spec["bootstrap_seed"]),
        "primary_layer": int(spec["primary_layer"]),
        "secondary_layer": int(spec["secondary_layer"]),
        "secondary_layer_role": spec["secondary_layer_role"],
        "endpoint_ids": sorted(endpoint_ids),
        "endpoints": spec["endpoints"],
        "output_filenames": spec["output_filenames"],
        "expected_output_rows": spec["expected_output_rows"],
        "output_unique_keys": spec["output_unique_keys"],
        "mean_estimand": spec["mean_estimand"],
        "cli_role_arguments": spec["cli_role_arguments"],
        "design": {key: spec[key] for key in EXPECTED_ANALYSIS_DESIGN},
    }


def _validate_protocol_documents(
    root: Path, manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    documents = manifest.get("protocol_documents")
    _require(
        isinstance(documents, list) and len(documents) == 2,
        "English/Japanese protocol binding is incomplete",
    )
    languages: set[str] = set()
    for spec in documents:
        language = spec.get("language")
        _require(
            language in {"en", "ja"} and language not in languages,
            "protocol language binding differs",
        )
        languages.add(language)
        expected = spec.get("sha256")
        _require(
            isinstance(expected, str)
            and not expected.startswith("PENDING_")
            and len(expected) == 64,
            f"{language} protocol SHA-256 is still pending",
        )
        path = _verified_path(root, spec["path"], expected)
        reports.append(
            {
                "language": language,
                "path": spec["path"],
                "sha256": _sha256(path),
            }
        )
    _require(languages == {"en", "ja"}, "English/Japanese protocol pair is incomplete")
    return reports


def _validate_excluded_banks(
    root: Path, manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    del root  # Excluded holdouts must not be opened, read, or re-hashed by this audit.
    reports: list[dict[str, Any]] = []
    paths: set[str] = set()
    for spec in manifest["excluded_banks"]:
        _require(
            spec["path"] in FORBIDDEN_TARGET_PATHS,
            f"unexpected excluded bank: {spec['path']}",
        )
        _require(spec["path"] not in paths, f"duplicate excluded bank: {spec['path']}")
        paths.add(spec["path"])
        _expect_equal(
            spec.get("sha256"),
            KNOWN_EXCLUDED_BANK_SHA256[spec["path"]],
            f"{spec['path']}: known frozen SHA declaration",
        )
        _require(
            spec.get("e1_tokenizer_access_count_declared") == 0,
            f"{spec['path']}: E1 tokenizer-access declaration is not zero",
        )
        _require(
            spec.get("e1_model_forward_count_declared") == 0,
            f"{spec['path']}: E1 model-forward declaration is not zero",
        )
        reports.append(
            {
                "role": spec["role"],
                "path": spec["path"],
                "sha256": spec["sha256"],
                "historical_status": spec["historical_status"],
                "e1_tokenizer_access_count_declared": 0,
                "e1_model_forward_count_declared": 0,
                "verification_scope": (
                    "manifest path and known frozen SHA declaration only; the excluded file "
                    "was not opened, read, re-hashed, tokenized, or sent to a model"
                ),
            }
        )
    _require(paths == FORBIDDEN_TARGET_PATHS, "excluded bank set is incomplete")
    return reports


def audit_suite(root: Path, *, tokenizer: Any | None = None) -> dict[str, Any]:
    root = root.resolve()
    manifest, manifest_sha = _load_manifest(root)
    tokenizer = tokenizer or _load_pinned_tokenizer(manifest)
    contract = manifest["token_isomorphism"]
    _require(
        len(manifest["panels"]) == int(contract["panel_count"]), "panel count differs"
    )
    _require(
        len(contract["shared_slot_suffix_token_ids"])
        == int(contract["conditions_per_panel"]),
        "shared suffix count differs",
    )

    source_spec = manifest["shared_inputs"]["source"]
    source_path = _verified_path(root, source_spec["path"], source_spec["sha256"])
    wrappers = _load_wrappers(source_path)
    _expect_equal(
        len(wrappers), int(source_spec["file_record_count"]), "source record count"
    )
    _expect_equal(
        [row["id"] for row in wrappers],
        source_spec["ordered_ids"],
        "ordered wrapper IDs",
    )

    target_spec = manifest["shared_inputs"]["target"]
    target_path = _verified_path(root, target_spec["path"], target_spec["sha256"])
    targets = _read_jsonl(target_path)
    _expect_equal(
        len(targets), int(target_spec["file_record_count"]), "target file record count"
    )
    selected_targets = targets[: int(target_spec["selected_record_count"])]
    _expect_equal(
        [row.get("id") for row in selected_targets],
        target_spec["ordered_selected_ids"],
        "selected target IDs",
    )
    _expect_equal(
        [row.get("group") for row in selected_targets],
        target_spec["ordered_selected_groups"],
        "selected target groups",
    )

    parity_spec = manifest["shared_inputs"]["parity"]
    parity_path = _verified_path(root, parity_spec["path"], parity_spec["sha256"])
    parity = json.loads(parity_path.read_text(encoding="utf-8"))
    _expect_equal(parity.get("status"), parity_spec["required_status"], "parity status")
    _expect_equal(parity.get("site"), parity_spec["required_site"], "parity site")
    _expect_equal(parity.get("model"), EXPECTED_MODEL_ID, "parity model")
    _expect_equal(parity.get("revision"), EXPECTED_REVISION, "parity revision")
    _require(
        set(parity_spec["required_intervention_layers"]).issubset(
            set(parity.get("intervention_layers", []))
        ),
        "parity receipt does not cover every fixed E1 intervention layer",
    )

    panel_reports: list[dict[str, Any]] = []
    config_reports: list[dict[str, Any]] = []
    all_glyphs: dict[str, str] = {}
    all_ids: set[str] = set()
    roles: set[str] = set()
    middle_tokens: set[int] = set()
    for panel_spec in manifest["panels"]:
        role = panel_spec["role"]
        _require(role not in roles, f"duplicate panel role: {role}")
        roles.add(role)
        middle = int(panel_spec["family_middle_token_id"])
        _require(
            middle not in middle_tokens, f"duplicate family-middle token: {middle}"
        )
        middle_tokens.add(middle)
        panel_path = _verified_path(root, panel_spec["path"], panel_spec["sha256"])
        items = _load_panel(panel_path)
        _expect_equal(
            len(items), int(contract["conditions_per_panel"]), f"{role}: item count"
        )
        _expect_equal(
            _parse_codepoint(panel_spec["codepoint_end"]),
            _parse_codepoint(panel_spec["codepoint_start"]) + len(items) - 1,
            f"{role}: inclusive codepoint range",
        )
        item_reports: list[dict[str, Any]] = []
        for slot_index, item in enumerate(items):
            report = _validate_scalar(item, panel_spec, slot_index, tokenizer, contract)
            _require(
                report["id"] not in all_ids,
                f"duplicate item ID across panels: {report['id']}",
            )
            all_ids.add(report["id"])
            previous = all_glyphs.get(report["glyph"])
            _require(
                previous is None,
                f"glyph overlap across panels: {report['glyph']} in {previous} and {role}",
            )
            all_glyphs[report["glyph"]] = role
            item_reports.append(report)
        panel_reports.append(
            {
                "role": role,
                "id": panel_spec["id"],
                "panel_path": panel_spec["path"],
                "panel_sha256": panel_spec["sha256"],
                "codepoint_range": [
                    panel_spec["codepoint_start"],
                    panel_spec["codepoint_end"],
                ],
                "family_middle_token_id": middle,
                "item_count": len(item_reports),
                "items": item_reports,
            }
        )
        config_reports.append(_validate_config(root, panel_spec, panel_path, manifest))

    _require(
        len(all_glyphs)
        == int(contract["panel_count"]) * int(contract["conditions_per_panel"]),
        "cross-panel glyph overlap or omission detected",
    )
    for slot_index, expected_suffix in enumerate(
        contract["shared_slot_suffix_token_ids"]
    ):
        slot_rows = [panel["items"][slot_index] for panel in panel_reports]
        _require(
            {row["raw_token_ids"][0] for row in slot_rows}
            == {int(contract["shared_first_token_id"])},
            f"slot_{slot_index:02d}: first-token identity failed",
        )
        _require(
            {row["raw_token_ids"][2] for row in slot_rows} == {int(expected_suffix)},
            f"slot_{slot_index:02d}: third-token identity failed",
        )

    wrapper_reports, wrapper_profile_count = _validate_wrapper_isomorphism(
        tokenizer, wrappers, panel_reports
    )
    role_bindings = _validate_role_bindings(manifest)
    excluded_bank_reports = _validate_excluded_banks(root, manifest)
    protocol_reports = _validate_protocol_documents(root, manifest)
    analysis_report = _validate_analysis_binding(root, manifest)
    fixed = manifest["fixed_execution_cell"]
    _expect_equal(
        len(panel_reports)
        * len(fixed["capture"]["layers"])
        * len(fixed["intervention"]["strengths"])
        * len(fixed["run"]["seeds"]),
        int(fixed["fixed_family_layer_strength_seed_cell_count"]),
        "fixed family-layer-strength-seed cell count",
    )
    _expect_equal(
        sum(report["plan"]["total"] for report in config_reports),
        int(fixed["expected_forward_calls_all_families"]),
        "all-family forward plan",
    )
    _expect_equal(
        sum(report["plan"]["intervention_rows"] for report in config_reports),
        int(fixed["expected_intervention_rows_all_families"]),
        "all-family intervention row plan",
    )

    return {
        "schema_version": 1,
        "status": "pass",
        "audit_id": "emoji_family_exploratory_v1_tokenization_preflight",
        "protocol_id": EXPECTED_PROTOCOL_ID,
        "manifest_path": MANIFEST_PATH.as_posix(),
        "manifest_sha256": manifest_sha,
        "freeze_status": manifest["freeze"]["status"],
        "audit_scope": "tokenizer-only structural, input-binding, config-binding, and excluded-bank declaration preflight",
        "audit_implementation": {
            "path": "scripts/audit_e1_token_isomorphic_panels.py",
            "sha256": _sha256(Path(__file__).resolve()),
        },
        "language_model_loaded": False,
        "model_forward_executed": False,
        "outcome_data_inspected": False,
        "claim_boundary": manifest["claim_boundary"],
        "tokenizer": {
            "model_id": EXPECTED_MODEL_ID,
            "revision": EXPECTED_REVISION,
            "class": type(tokenizer).__name__,
            "vocab_size": int(tokenizer.vocab_size),
            "verified_asset_count": len(manifest["tokenizer"]["assets_sha256"]),
        },
        "shared_inputs": {
            "source_path": source_spec["path"],
            "source_sha256": source_spec["sha256"],
            "source_record_count": len(wrappers),
            "target_path": target_spec["path"],
            "target_sha256": target_spec["sha256"],
            "target_file_record_count": len(targets),
            "target_selected_record_count": len(selected_targets),
            "parity_path": parity_spec["path"],
            "parity_sha256": parity_spec["sha256"],
            "parity_layers_cover_fixed_cell": True,
        },
        "token_isomorphism": {
            "shared_first_token_id": int(contract["shared_first_token_id"]),
            "shared_slot_suffix_token_ids": contract["shared_slot_suffix_token_ids"],
            "family_middle_token_ids": {
                panel["role"]: panel["family_middle_token_id"]
                for panel in panel_reports
            },
            "cross_panel_glyph_overlap_count": 0,
            "raw_first_and_third_identity": True,
            "wrapper_profile_isomorphic": True,
        },
        "panels": panel_reports,
        "configs": config_reports,
        "role_bindings": role_bindings,
        "wrappers": wrapper_reports,
        "analysis_binding": analysis_report,
        "protocol_documents": protocol_reports,
        "excluded_banks": excluded_bank_reports,
        "counts": {
            "panel_count": len(panel_reports),
            "items_per_panel": int(contract["conditions_per_panel"]),
            "scalar_entries_verified": len(all_glyphs),
            "wrapper_count": len(wrappers),
            "wrapper_profiles_verified": wrapper_profile_count,
            "fixed_family_layer_strength_seed_cells": int(
                fixed["fixed_family_layer_strength_seed_cell_count"]
            ),
            "planned_forward_calls": int(fixed["expected_forward_calls_all_families"]),
            "planned_intervention_rows": int(
                fixed["expected_intervention_rows_all_families"]
            ),
        },
        "authorization": {
            "e1_model_forward_authorized_now": False,
            "e1_model_forward_conditionally_authorized_after_public_freeze": True,
            "p2_model_forward_authorized": False,
            "c1_model_forward_authorized": False,
            "causal_claim_authorized": False,
            "confirmatory_claim_authorized": False,
        },
    }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the script's parent repository)",
    )
    parser.add_argument(
        "--output", type=Path, help="optional deterministic JSON receipt path"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = audit_suite(args.root)
    except (
        AuditError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        print(
            json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        _atomic_write(args.output.resolve(), text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
