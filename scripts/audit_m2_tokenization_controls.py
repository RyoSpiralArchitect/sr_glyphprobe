#!/usr/bin/env python3
"""Fail-closed tokenizer-only audit for the frozen Milestone 2 controls.

This script loads a tokenizer, never a model. Candidate controls are accepted
only from their Unicode identity, pinned tokenizer IDs, and tokenization in the
16 frozen source wrappers.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import unicodedata
from typing import Any

import yaml


EXPECTED_SUITE_ID = "glyphprobe-m2-tokenization-controls-v1"
EXPECTED_MODEL_ID = "openai-community/gpt2"
EXPECTED_REVISION = "607a30d783dfa663caf39e06633721c8d4cfcd7e"
EXPECTED_MANIFEST_SHA256 = "29ff22ad1e98c30ce848122c6d37b8feaff22814181150191238ca85ba24ac12"
MANIFEST_PATH = Path("data/tokenization_controls/manifest.json")
MANIFEST_SHA_PATH = Path("data/tokenization_controls/manifest.sha256")


class AuditError(RuntimeError):
    """Raised when any frozen control-suite invariant fails."""


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
    manifest_path = (root / MANIFEST_PATH).resolve()
    sha_path = (root / MANIFEST_SHA_PATH).resolve()
    _require(manifest_path.is_file(), f"missing manifest: {MANIFEST_PATH}")
    _require(sha_path.is_file(), f"missing manifest digest: {MANIFEST_SHA_PATH}")

    actual = _sha256(manifest_path)
    _require(
        actual == EXPECTED_MANIFEST_SHA256,
        "manifest SHA-256 is not the hard-pinned Milestone 2 suite identity: "
        f"expected {EXPECTED_MANIFEST_SHA256}, got {actual}",
    )
    fields = sha_path.read_text(encoding="utf-8").strip().split()
    _require(len(fields) == 2, "manifest.sha256 must contain one digest and one path")
    _require(fields[0] == actual, "manifest.sha256 digest does not match manifest.json")
    _require(fields[1] == MANIFEST_PATH.as_posix(), "manifest.sha256 path is not canonical")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _require(manifest.get("schema_version") == 1, "unsupported control manifest schema")
    _require(
        manifest.get("control_suite_id") == EXPECTED_SUITE_ID,
        "unexpected control suite ID",
    )
    tokenizer_spec = manifest.get("tokenizer", {})
    _require(tokenizer_spec.get("model_id") == EXPECTED_MODEL_ID, "unexpected tokenizer model")
    _require(tokenizer_spec.get("revision") == EXPECTED_REVISION, "unexpected tokenizer revision")
    return manifest, actual


def _load_pinned_tokenizer(manifest: dict[str, Any]) -> Any:
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - environment-dependent message
        raise AuditError(
            "transformers is required for the tokenizer audit; install a GlyphProbe "
            "torch, lens, mlx, or all extra"
        ) from exc

    spec = manifest["tokenizer"]
    tokenizer = AutoTokenizer.from_pretrained(
        spec["model_id"],
        revision=spec["revision"],
        local_files_only=bool(spec["local_files_only"]),
    )
    _require(type(tokenizer).__name__ == spec["tokenizer_class"], "tokenizer class mismatch")
    _require(int(tokenizer.vocab_size) == int(spec["vocab_size"]), "tokenizer vocab mismatch")
    _require(bool(getattr(tokenizer, "is_fast", False)), "offset audit requires a fast tokenizer")

    # Keep the lexical snapshot path here: Hugging Face cache files are symlinks
    # into blobs, and resolving the symlink would erase the revision directory.
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


def _load_panel(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    values = raw.get("items") if isinstance(raw, dict) else raw
    _require(isinstance(values, list), f"panel is not an item list: {path}")
    items: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        _require(isinstance(item, dict), f"panel item {index} is not a mapping: {path}")
        _require(isinstance(item.get("id"), str) and item["id"], f"missing item ID: {path}")
        _require(isinstance(item.get("glyph"), str) and item["glyph"], f"missing glyph: {path}")
        _require(isinstance(item.get("factors", {}), dict), f"invalid factors: {path}")
        _require(isinstance(item.get("labels", []), list), f"invalid labels: {path}")
        items.append(item)
    _require(len({item["id"] for item in items}) == len(items), f"duplicate item IDs: {path}")
    _require(len({item["glyph"] for item in items}) == len(items), f"duplicate glyphs: {path}")
    return items


def _load_wrappers(path: Path) -> list[dict[str, str]]:
    wrappers: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        _require(isinstance(row.get("id"), str), f"wrapper {line_number} has no ID")
        template = row.get("template")
        _require(isinstance(template, str), f"wrapper {line_number} has no template")
        _require(
            template.count("{emoji}") == 1,
            f"wrapper {row['id']} must contain exactly one emoji placeholder",
        )
        wrappers.append({"id": row["id"], "template": template})
    _require(len({row["id"] for row in wrappers}) == len(wrappers), "wrapper IDs are not unique")
    return wrappers


def _validate_scalar(
    item_id: str,
    glyph: str,
    tokenizer: Any,
    constraints: dict[str, Any],
) -> dict[str, Any]:
    _require(len(glyph) == 1, f"{item_id}: glyph must be exactly one Unicode scalar")
    codepoint = ord(glyph)
    _require(not 0xD800 <= codepoint <= 0xDFFF, f"{item_id}: surrogate code point is forbidden")
    codepoint_label = f"U+{codepoint:04X}"
    _require(
        codepoint_label not in set(constraints["forbidden_codepoints"]),
        f"{item_id}: forbidden variation selector or joiner",
    )
    name = unicodedata.name(glyph, "")
    _require(bool(name), f"{item_id}: Unicode scalar has no assigned name")
    utf8 = glyph.encode("utf-8")
    _require(
        len(utf8) == int(constraints["required_utf8_byte_length"]),
        f"{item_id}: expected {constraints['required_utf8_byte_length']} UTF-8 bytes",
    )
    raw_ids = [
        int(value)
        for value in tokenizer.encode(glyph, add_special_tokens=False)
    ]
    _require(
        len(raw_ids) == int(constraints["required_raw_token_count"]),
        f"{item_id}: expected {constraints['required_raw_token_count']} raw tokens, got {raw_ids}",
    )
    return {
        "id": item_id,
        "glyph": glyph,
        "codepoint": codepoint_label,
        "unicode_name": name,
        "unicode_category": unicodedata.category(glyph),
        "utf8_hex": utf8.hex(),
        "raw_token_ids": raw_ids,
    }


def _wrapper_profile(tokenizer: Any, wrapper: dict[str, str], glyph: str) -> dict[str, Any]:
    prefix, suffix = wrapper["template"].split("{emoji}")
    text = prefix + glyph + suffix
    start = len(prefix)
    end = start + len(glyph)
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
    )
    token_ids = [int(value) for value in encoded["input_ids"]]
    offsets = [(int(a), int(b)) for a, b in encoded["offset_mapping"]]
    positions = [
        index
        for index, (token_start, token_end) in enumerate(offsets)
        if token_start < end and token_end > start
    ]
    _require(positions, f"{wrapper['id']}: tokenizer offsets did not locate the glyph")
    _require(
        positions == list(range(positions[0], positions[-1] + 1)),
        f"{wrapper['id']}: glyph token positions are not contiguous",
    )
    outside_ids = [value for index, value in enumerate(token_ids) if index not in positions]
    span_ids = [token_ids[index] for index in positions]
    return {
        "wrapper_id": wrapper["id"],
        "token_count": len(token_ids),
        "glyph_token_positions": positions,
        "glyph_span_token_ids": span_ids,
        "outside_span_token_ids": outside_ids,
    }


def _profiles(tokenizer: Any, wrappers: list[dict[str, str]], glyph: str) -> dict[str, dict[str, Any]]:
    return {row["id"]: _wrapper_profile(tokenizer, row, glyph) for row in wrappers}


def _compare_wrapper_profiles(
    control_id: str,
    control_profiles: dict[str, dict[str, Any]],
    reference_id: str,
    reference_profiles: dict[str, dict[str, Any]],
    *,
    require_outer_span_match: bool = False,
    expected_middle_token_id: int | None = None,
) -> int:
    _require(
        set(control_profiles) == set(reference_profiles),
        f"{control_id}: wrapper IDs differ from {reference_id}",
    )
    for wrapper_id in control_profiles:
        control = control_profiles[wrapper_id]
        reference = reference_profiles[wrapper_id]
        _require(
            control["token_count"] == reference["token_count"],
            f"{control_id}/{wrapper_id}: full token count differs from {reference_id}",
        )
        _require(
            control["glyph_token_positions"] == reference["glyph_token_positions"],
            f"{control_id}/{wrapper_id}: glyph token positions differ from {reference_id}",
        )
        _require(
            len(control["glyph_span_token_ids"]) == 3,
            f"{control_id}/{wrapper_id}: wrapper glyph span is not three tokens",
        )
        _require(
            control["outside_span_token_ids"] == reference["outside_span_token_ids"],
            f"{control_id}/{wrapper_id}: tokens outside glyph span differ from {reference_id}",
        )
        if require_outer_span_match:
            control_span = control["glyph_span_token_ids"]
            reference_span = reference["glyph_span_token_ids"]
            _require(
                control_span[0] == reference_span[0] and control_span[-1] == reference_span[-1],
                f"{control_id}/{wrapper_id}: first or suffix span token differs from {reference_id}",
            )
            _require(
                control_span[1] == expected_middle_token_id,
                f"{control_id}/{wrapper_id}: middle token is not {expected_middle_token_id}",
            )
            _require(
                control_span[1] != reference_span[1],
                f"{control_id}/{wrapper_id}: middle token did not shift",
            )
    return len(control_profiles)


def _prefix_histogram(rows: list[dict[str, Any]]) -> dict[str, int]:
    histogram = Counter(
        f"{row['raw_token_ids'][0]},{row['raw_token_ids'][1]}" for row in rows
    )
    return dict(sorted(histogram.items()))


def _validate_config(
    root: Path,
    panel_spec: dict[str, Any],
    panel_path: Path,
    manifest: dict[str, Any],
    neutral_by_id: dict[str, dict[str, Any]],
) -> None:
    config_path = _verified_path(
        root,
        panel_spec["config_path"],
        panel_spec["config_sha256"],
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    constraints = manifest["execution_config_constraints"]

    def resolve(value: str) -> Path:
        return (config_path.parent / value).resolve()

    _require(config.get("mode") == "internal", f"{config_path}: mode must be internal")
    backend = config.get("backend", {})
    _require(backend.get("kind") == "mlx", f"{config_path}: backend must be mlx")
    _require(backend.get("model") == EXPECTED_MODEL_ID, f"{config_path}: model mismatch")
    _require(backend.get("revision") == EXPECTED_REVISION, f"{config_path}: revision mismatch")
    _require(backend.get("local_files_only") is True, f"{config_path}: tokenizer/model must be local")
    _require(resolve(config["panel"]["file"]) == panel_path, f"{config_path}: panel path mismatch")
    neutral = neutral_by_id[constraints["neutral_control_id"]]["glyph"]
    _require(config["panel"].get("neutral_glyph") == neutral, f"{config_path}: neutral mismatch")
    _require(
        resolve(config["source"]["wrappers_file"])
        == (root / constraints["source_wrappers_path"]).resolve(),
        f"{config_path}: source wrappers are not the frozen audit wrappers",
    )
    _require(
        resolve(config["targets"]["cases_file"])
        == (root / constraints["targets_path"]).resolve(),
        f"{config_path}: this control config must remain on exploratory targets",
    )
    required = constraints["run_name_required_substring"]
    _require(required in config["run"]["name"], f"{config_path}: run name must contain {required!r}")


def audit_suite(root: Path, *, tokenizer: Any | None = None) -> dict[str, Any]:
    root = root.resolve()
    manifest, manifest_sha = _load_manifest(root)
    tokenizer = tokenizer or _load_pinned_tokenizer(manifest)
    constraints = manifest["scalar_constraints"]

    wrappers_spec = manifest["wrappers"]
    wrappers_path = _verified_path(root, wrappers_spec["path"], wrappers_spec["sha256"])
    wrappers = _load_wrappers(wrappers_path)
    _require(
        len(wrappers) == int(wrappers_spec["expected_count"]),
        f"expected {wrappers_spec['expected_count']} wrappers, got {len(wrappers)}",
    )

    reference_spec = manifest["reference_panel"]
    reference_path = _verified_path(root, reference_spec["path"], reference_spec["sha256"])
    reference_items = _load_panel(reference_path)
    _require(len(reference_items) == int(reference_spec["expected_size"]), "reference size mismatch")

    reference_rows: list[dict[str, Any]] = []
    reference_by_id: dict[str, dict[str, Any]] = {}
    reference_profile_by_id: dict[str, dict[str, dict[str, Any]]] = {}
    reference_id_by_prefix: dict[tuple[int, int], str] = {}
    wrapper_comparisons = 0
    for item in reference_items:
        row = _validate_scalar(item["id"], item["glyph"], tokenizer, constraints)
        row["factors"] = item.get("factors", {})
        reference_rows.append(row)
        reference_by_id[item["id"]] = row
        reference_profile_by_id[item["id"]] = _profiles(tokenizer, wrappers, item["glyph"])
        prefix = tuple(row["raw_token_ids"][:2])
        reference_id_by_prefix.setdefault(prefix, item["id"])
    _require(
        _prefix_histogram(reference_rows) == reference_spec["expected_prefix_histogram"],
        "reference prefix histogram differs from the frozen expectation",
    )
    for row in reference_rows:
        prefix = tuple(row["raw_token_ids"][:2])
        canonical_id = reference_id_by_prefix[prefix]
        wrapper_comparisons += _compare_wrapper_profiles(
            row["id"],
            reference_profile_by_id[row["id"]],
            canonical_id,
            reference_profile_by_id[canonical_id],
        )

    neutral_rows: list[dict[str, Any]] = []
    neutral_by_id: dict[str, dict[str, Any]] = {}
    reference_glyphs = {row["glyph"] for row in reference_rows}
    for spec in manifest["neutral_controls"]:
        row = _validate_scalar(spec["id"], spec["glyph"], tokenizer, constraints)
        _require(row["raw_token_ids"] == spec["expected_raw_token_ids"], f"{spec['id']}: raw IDs differ")
        prefix = tuple(spec["reference_prefix"])
        _require(tuple(row["raw_token_ids"][:2]) == prefix, f"{spec['id']}: prefix differs")
        _require(row["glyph"] not in reference_glyphs, f"{spec['id']}: neutral reuses a reference glyph")
        canonical_id = reference_id_by_prefix[prefix]
        wrapper_comparisons += _compare_wrapper_profiles(
            row["id"],
            _profiles(tokenizer, wrappers, row["glyph"]),
            canonical_id,
            reference_profile_by_id[canonical_id],
        )
        neutral_rows.append(row)
        neutral_by_id[row["id"]] = row
    _require(len(neutral_by_id) == len(neutral_rows), "neutral control IDs are not unique")
    _require(len({row["glyph"] for row in neutral_rows}) == len(neutral_rows), "neutral glyphs are not unique")

    panel_specs = manifest["panels"]
    _require(len({spec["id"] for spec in panel_specs}) == len(panel_specs), "panel IDs are not unique")
    panel_reports: list[dict[str, Any]] = []
    matched_null_glyphs: dict[str, set[str]] = {}
    suffix_reference_ids: set[str] = set()
    near_control_specs = {
        row["glyph"]: row
        for row in manifest["matched_null_inventory"]["conservative_semantic_near_controls"]
    }
    seen_near_controls: set[str] = set()
    scalar_entries = len(reference_rows) + len(neutral_rows)

    for panel_spec in panel_specs:
        panel_path = _verified_path(root, panel_spec["path"], panel_spec["sha256"])
        items = _load_panel(panel_path)
        _require(len(items) == int(panel_spec["expected_size"]), f"{panel_spec['id']}: size mismatch")
        _validate_config(root, panel_spec, panel_path, manifest, neutral_by_id)

        item_rows: list[dict[str, Any]] = []
        for item in items:
            row = _validate_scalar(item["id"], item["glyph"], tokenizer, constraints)
            row["factors"] = item.get("factors", {})
            item_rows.append(row)
        scalar_entries += len(item_rows)
        role = panel_spec["role"]

        if role == "matched_null":
            _require(
                not ({row["glyph"] for row in item_rows} & reference_glyphs),
                f"{panel_spec['id']}: matched null reuses a reference glyph",
            )
            _require(
                _prefix_histogram(item_rows) == panel_spec["expected_prefix_histogram"],
                f"{panel_spec['id']}: prefix histogram mismatch",
            )
            for row in item_rows:
                prefix = tuple(row["raw_token_ids"][:2])
                expected_factor = f"p{prefix[0]}_{prefix[1]}"
                _require(
                    row["factors"].get("prefix_stratum") == expected_factor,
                    f"{row['id']}: declared prefix stratum is incorrect",
                )
                near_spec = near_control_specs.get(row["glyph"])
                if near_spec is not None:
                    _require(
                        near_spec["panel_id"] == panel_spec["id"],
                        f"{row['id']}: semantic-near control is in the wrong panel",
                    )
                    _require(
                        row["codepoint"] == near_spec["codepoint"]
                        and row["unicode_name"] == near_spec["unicode_name"],
                        f"{row['id']}: semantic-near control identity differs",
                    )
                    _require(
                        row["factors"].get("control_subrole")
                        == "conservative_semantic_near_control",
                        f"{row['id']}: semantic-near control is not explicitly labeled",
                    )
                    seen_near_controls.add(row["glyph"])
                else:
                    _require(
                        "control_subrole" not in row["factors"],
                        f"{row['id']}: undeclared matched-null subrole",
                    )
                canonical_id = reference_id_by_prefix[prefix]
                wrapper_comparisons += _compare_wrapper_profiles(
                    row["id"],
                    _profiles(tokenizer, wrappers, row["glyph"]),
                    canonical_id,
                    reference_profile_by_id[canonical_id],
                )
            matched_null_glyphs[panel_spec["id"]] = {row["glyph"] for row in item_rows}

        elif role == "suffix_matched_middle_shift":
            expected_middle = int(panel_spec["expected_middle_token_id"])
            for row in item_rows:
                reference_id = row["factors"].get("reference_id")
                _require(reference_id in reference_by_id, f"{row['id']}: unknown reference pair")
                _require(reference_id not in suffix_reference_ids, f"{row['id']}: duplicate reference pair")
                suffix_reference_ids.add(reference_id)
                reference = reference_by_id[reference_id]
                control_ids = row["raw_token_ids"]
                reference_ids = reference["raw_token_ids"]
                _require(control_ids[0] == reference_ids[0], f"{row['id']}: first token differs")
                _require(control_ids[1] == expected_middle, f"{row['id']}: middle token differs")
                _require(control_ids[1] != reference_ids[1], f"{row['id']}: middle token did not shift")
                _require(control_ids[2] == reference_ids[2], f"{row['id']}: suffix token differs")
                wrapper_comparisons += _compare_wrapper_profiles(
                    row["id"],
                    _profiles(tokenizer, wrappers, row["glyph"]),
                    reference_id,
                    reference_profile_by_id[reference_id],
                    require_outer_span_match=True,
                    expected_middle_token_id=expected_middle,
                )
            _require(
                suffix_reference_ids == set(reference_by_id),
                "suffix diagnostic is not a one-to-one cover of the reference panel",
            )

        elif role == "prefix_homogeneous_colored_shapes":
            _require(
                _prefix_histogram(item_rows) == panel_spec["expected_prefix_histogram"],
                f"{panel_spec['id']}: prefix histogram mismatch",
            )
            expected_levels = panel_spec["expected_factor_levels"]
            colors = sorted({row["factors"].get("color") for row in item_rows})
            shapes = sorted({row["factors"].get("shape") for row in item_rows})
            _require(colors == expected_levels["color"], "homogeneous panel color levels differ")
            _require(shapes == expected_levels["shape"], "homogeneous panel shape levels differ")
            cells = {(row["factors"]["color"], row["factors"]["shape"]) for row in item_rows}
            expected_cells = {(color, shape) for color in colors for shape in shapes}
            _require(cells == expected_cells, "homogeneous panel is not a complete 5 x 2 grid")
            for row in item_rows:
                prefix = tuple(row["raw_token_ids"][:2])
                canonical_id = reference_id_by_prefix[prefix]
                wrapper_comparisons += _compare_wrapper_profiles(
                    row["id"],
                    _profiles(tokenizer, wrappers, row["glyph"]),
                    canonical_id,
                    reference_profile_by_id[canonical_id],
                )
        else:
            raise AuditError(f"unknown panel role: {role}")

        panel_reports.append(
            {
                "id": panel_spec["id"],
                "role": role,
                "item_count": len(item_rows),
                "prefix_histogram": _prefix_histogram(item_rows),
                "items": item_rows,
                "wrappers_verified_per_item": len(wrappers),
            }
        )

    overlap_spec = manifest["matched_null_cross_panel_overlap"]
    maximum = int(overlap_spec["maximum_pairwise_glyph_overlap"])
    panel_ids = sorted(matched_null_glyphs)
    for index, left_id in enumerate(panel_ids):
        for right_id in panel_ids[index + 1 :]:
            overlap = matched_null_glyphs[left_id] & matched_null_glyphs[right_id]
            _require(
                len(overlap) <= maximum,
                f"matched-null overlap exceeds {maximum}: {left_id}, {right_id}",
            )
    memberships: dict[str, list[str]] = defaultdict(list)
    for panel_id, glyphs in matched_null_glyphs.items():
        for glyph in glyphs:
            memberships[glyph].append(panel_id)
    actual_overlaps = {
        glyph: sorted(ids) for glyph, ids in memberships.items() if len(ids) > 1
    }
    expected_overlaps = {
        row["glyph"]: sorted(row["panel_ids"])
        for row in overlap_spec["expected_overlaps"]
    }
    _require(actual_overlaps == expected_overlaps, "matched-null cross-panel overlap set differs")
    _require(
        seen_near_controls == set(near_control_specs),
        "declared semantic-near controls are not represented exactly once",
    )

    dominant_neutral = neutral_by_id[
        manifest["execution_config_constraints"]["neutral_control_id"]
    ]["glyph"]
    _require(
        all(dominant_neutral not in glyphs for glyphs in matched_null_glyphs.values()),
        "dominant neutral appears inside a matched-null panel",
    )

    reference_profile_report: dict[str, Any] = {}
    for prefix, item_id in sorted(reference_id_by_prefix.items()):
        profiles = reference_profile_by_id[item_id]
        reference_profile_report[f"{prefix[0]},{prefix[1]}"] = {
            "reference_item_id": item_id,
            "token_count_by_wrapper": {
                wrapper_id: profile["token_count"] for wrapper_id, profile in profiles.items()
            },
            "glyph_token_positions_by_wrapper": {
                wrapper_id: profile["glyph_token_positions"]
                for wrapper_id, profile in profiles.items()
            },
        }

    return {
        "status": "pass",
        "control_suite_id": EXPECTED_SUITE_ID,
        "claim_boundary": (
            "Tokenizer-only construction audit; no model activation, logit, generation, "
            "fingerprint, causal, or semantic result is established."
        ),
        "manifest_sha256": manifest_sha,
        "tokenizer": {
            "model_id": EXPECTED_MODEL_ID,
            "revision": EXPECTED_REVISION,
            "class": type(tokenizer).__name__,
            "vocab_size": int(tokenizer.vocab_size),
            "verified_asset_count": len(manifest["tokenizer"]["assets_sha256"]),
        },
        "wrapper_count": len(wrappers),
        "wrapper_ids": [row["id"] for row in wrappers],
        "reference_prefix_profiles": reference_profile_report,
        "reference_items": reference_rows,
        "neutral_controls": neutral_rows,
        "panels": panel_reports,
        "counts": {
            "panel_count": len(panel_reports),
            "matched_null_panel_count": len(matched_null_glyphs),
            "scalar_entries_verified": scalar_entries,
            "wrapper_profile_comparisons": wrapper_comparisons,
        },
        "matched_null_disjoint": maximum == 0 and not actual_overlaps,
        "conservative_semantic_near_controls": list(near_control_specs.values()),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the script's parent repository)",
    )
    parser.add_argument("--output", type=Path, help="optional JSON receipt path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = audit_suite(args.root)
    except (AuditError, OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
