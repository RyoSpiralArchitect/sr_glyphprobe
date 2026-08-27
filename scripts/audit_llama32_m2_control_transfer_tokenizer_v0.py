#!/usr/bin/env python3
"""Tokenizer-only transfer gate for GPT-2 Milestone 2 control panels.

The audit asks whether the existing colored-shape reference and all three
Milestone 2 matched-null panels retain the same prespecified token-count and
prefix-panel features under the pinned Llama 3.2 3B Instruct tokenizer.  It
loads no language-model weights and has no target-bank input surface.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = (
    ROOT / "configs" / "llama32_3b_instruct_m2_control_transfer_tokenizer_v0.yaml"
)
DEFAULT_OUTPUT = (
    ROOT
    / "validation"
    / "llama32_3b_instruct_m2_control_transfer_tokenizer_v0"
    / "receipt.json"
)
EXPECTED_STATUS = "tokenizer_only_transfer_gate_not_scientific"
ALLOWED_PANEL_ROOT = (ROOT / "data" / "emoji_panels").resolve()
ALLOWED_WRAPPER_ROOT = (ROOT / "data" / "wrappers").resolve()


class AuditError(RuntimeError):
    """Raised when an input or tokenizer invariant fails closed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        f"Input escapes its allowed root: {path}",
    )
    _require(path.is_file() and not path.is_symlink(), f"Missing input: {path}")
    actual = _sha256_file(path)
    _require(
        actual == expected_sha256,
        f"Input SHA-256 mismatch for {path.name}: expected {expected_sha256}, got {actual}",
    )
    return path


def _load_panel(path: Path, panel_id: str) -> list[dict[str, str]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(
        isinstance(payload, dict) and isinstance(payload.get("items"), list),
        f"Panel has no items list: {path}",
    )
    rows: list[dict[str, str]] = []
    for index, item in enumerate(payload["items"]):
        _require(isinstance(item, dict), f"Panel item {index} is not a mapping")
        item_id = item.get("id")
        glyph = item.get("glyph")
        _require(isinstance(item_id, str) and item_id, f"Missing item id at {index}")
        _require(isinstance(glyph, str) and glyph, f"Missing glyph at {index}")
        rows.append({"panel_id": panel_id, "id": item_id, "glyph": glyph})
    _require(len(rows) == 10, f"Panel {panel_id} must contain exactly 10 items")
    _require(len({row["id"] for row in rows}) == 10, f"Duplicate ids in {panel_id}")
    _require(
        len({row["glyph"] for row in rows}) == 10,
        f"Duplicate glyphs in {panel_id}",
    )
    return rows


def _load_wrappers(path: Path, expected_count: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        wrapper_id = value.get("id")
        template = value.get("template")
        _require(
            isinstance(wrapper_id, str) and wrapper_id,
            f"Wrapper line {line_number} has no id",
        )
        _require(
            isinstance(template, str) and template.count("{emoji}") == 1,
            f"Wrapper {wrapper_id!r} must contain one emoji placeholder",
        )
        rows.append({"id": wrapper_id, "template": template})
    _require(len(rows) == expected_count, "Wrapper count differs from the contract")
    _require(len({row["id"] for row in rows}) == len(rows), "Duplicate wrapper ids")
    return rows


def _prefix(token_ids: list[int]) -> list[int]:
    return list(token_ids[:-1])


def _canonical_histogram(values: Iterable[Any]) -> list[dict[str, Any]]:
    counts = Counter(_json_bytes(value).decode("utf-8") for value in values)
    return [
        {"signature": json.loads(signature), "count": int(count)}
        for signature, count in sorted(counts.items())
    ]


def _raw_profile(tokenizer: Any, item: dict[str, str]) -> dict[str, Any]:
    token_ids = [
        int(value)
        for value in tokenizer.encode(item["glyph"], add_special_tokens=False)
    ]
    _require(token_ids, f"Tokenizer returned no ids for {item['id']}")
    decoded = tokenizer.decode(
        token_ids,
        skip_special_tokens=False,
        clean_up_tokenization_spaces=False,
    )
    return {
        **item,
        "token_ids": token_ids,
        "token_count": len(token_ids),
        "prefix_token_ids": _prefix(token_ids),
        "final_token_id": token_ids[-1],
        "decoded": decoded,
        "decode_exact": decoded == item["glyph"],
    }


def _wrapper_profile(
    tokenizer: Any,
    wrapper: dict[str, str],
    item: dict[str, str],
) -> dict[str, Any]:
    left, right = wrapper["template"].split("{emoji}")
    rendered = left + item["glyph"] + right
    glyph_start = len(left)
    glyph_end = glyph_start + len(item["glyph"])
    encoded = tokenizer(
        rendered,
        add_special_tokens=False,
        return_offsets_mapping=True,
        return_attention_mask=False,
    )
    token_ids = [int(value) for value in encoded["input_ids"]]
    offsets = [(int(start), int(end)) for start, end in encoded["offset_mapping"]]
    positions = [
        index
        for index, (start, end) in enumerate(offsets)
        if end > glyph_start and start < glyph_end
    ]
    _require(positions, f"Offsets did not locate {item['id']} in {wrapper['id']}")
    _require(
        positions == list(range(positions[0], positions[-1] + 1)),
        f"Glyph span is non-contiguous for {item['id']} in {wrapper['id']}",
    )
    position_set = set(positions)
    span_ids = [token_ids[index] for index in positions]
    return {
        "panel_id": item["panel_id"],
        "item_id": item["id"],
        "glyph": item["glyph"],
        "wrapper_id": wrapper["id"],
        "full_token_count": len(token_ids),
        "glyph_token_positions": positions,
        "glyph_span_token_ids": span_ids,
        "glyph_span_token_count": len(span_ids),
        "glyph_prefix_token_ids": _prefix(span_ids),
        "outside_span_token_ids": [
            value for index, value in enumerate(token_ids) if index not in position_set
        ],
        "left_boundary_absorbed": offsets[positions[0]][0] < glyph_start,
        "right_boundary_absorbed": offsets[positions[-1]][1] > glyph_end,
    }


def _summary(
    tokenizer: Any,
    panel_id: str,
    items: list[dict[str, str]],
    wrappers: list[dict[str, str]],
) -> dict[str, Any]:
    raw = [_raw_profile(tokenizer, item) for item in items]
    _require(
        all(row["decode_exact"] for row in raw),
        f"Raw tokenizer round trip failed in {panel_id}",
    )
    contextual = [
        _wrapper_profile(tokenizer, wrapper, item)
        for wrapper in wrappers
        for item in items
    ]
    wrapper_summaries: dict[str, Any] = {}
    for wrapper in wrappers:
        rows = [row for row in contextual if row["wrapper_id"] == wrapper["id"]]
        wrapper_summaries[wrapper["id"]] = {
            "full_token_count_histogram": _canonical_histogram(
                row["full_token_count"] for row in rows
            ),
            "glyph_span_count_histogram": _canonical_histogram(
                row["glyph_span_token_count"] for row in rows
            ),
            "glyph_prefix_histogram": _canonical_histogram(
                row["glyph_prefix_token_ids"] for row in rows
            ),
            "position_and_outside_histogram": _canonical_histogram(
                {
                    "glyph_token_positions": row["glyph_token_positions"],
                    "outside_span_token_ids": row["outside_span_token_ids"],
                    "left_boundary_absorbed": row["left_boundary_absorbed"],
                    "right_boundary_absorbed": row["right_boundary_absorbed"],
                }
                for row in rows
            ),
            "full_feature_histogram": _canonical_histogram(
                {
                    "full_token_count": row["full_token_count"],
                    "glyph_span_token_count": row["glyph_span_token_count"],
                    "glyph_prefix_token_ids": row["glyph_prefix_token_ids"],
                    "glyph_token_positions": row["glyph_token_positions"],
                    "outside_span_token_ids": row["outside_span_token_ids"],
                    "left_boundary_absorbed": row["left_boundary_absorbed"],
                    "right_boundary_absorbed": row["right_boundary_absorbed"],
                }
                for row in rows
            ),
        }
    return {
        "panel_id": panel_id,
        "item_count": len(items),
        "raw_token_count_histogram": _canonical_histogram(
            row["token_count"] for row in raw
        ),
        "raw_prefix_histogram": _canonical_histogram(
            row["prefix_token_ids"] for row in raw
        ),
        "raw_feature_histogram": _canonical_histogram(
            {
                "token_count": row["token_count"],
                "prefix_token_ids": row["prefix_token_ids"],
            }
            for row in raw
        ),
        "wrapper_summaries": wrapper_summaries,
        "raw_profiles": raw,
        "contextual_profiles": contextual,
        "profiles_sha256": hashlib.sha256(
            _json_bytes({"raw": raw, "contextual": contextual})
        ).hexdigest(),
    }


def _compare_summaries(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    wrapper_checks: dict[str, Any] = {}
    reference_wrappers = reference["wrapper_summaries"]
    candidate_wrappers = candidate["wrapper_summaries"]
    _require(
        set(reference_wrappers) == set(candidate_wrappers),
        "Reference and candidate wrapper ids differ",
    )
    for wrapper_id in sorted(reference_wrappers):
        left = reference_wrappers[wrapper_id]
        right = candidate_wrappers[wrapper_id]
        wrapper_checks[wrapper_id] = {
            "full_token_count_histogram_match": (
                left["full_token_count_histogram"] == right["full_token_count_histogram"]
            ),
            "glyph_span_count_histogram_match": (
                left["glyph_span_count_histogram"] == right["glyph_span_count_histogram"]
            ),
            "glyph_prefix_histogram_match": (
                left["glyph_prefix_histogram"] == right["glyph_prefix_histogram"]
            ),
            "position_and_outside_histogram_match": (
                left["position_and_outside_histogram"]
                == right["position_and_outside_histogram"]
            ),
            "full_feature_histogram_match": (
                left["full_feature_histogram"] == right["full_feature_histogram"]
            ),
        }
    checks = {
        "item_count_match": reference["item_count"] == candidate["item_count"],
        "raw_token_count_histogram_match": (
            reference["raw_token_count_histogram"]
            == candidate["raw_token_count_histogram"]
        ),
        "raw_prefix_histogram_match": (
            reference["raw_prefix_histogram"] == candidate["raw_prefix_histogram"]
        ),
        "raw_feature_histogram_match": (
            reference["raw_feature_histogram"] == candidate["raw_feature_histogram"]
        ),
        "all_wrapper_full_feature_histograms_match": all(
            row["full_feature_histogram_match"] for row in wrapper_checks.values()
        ),
    }
    return {
        "reference_panel_id": reference["panel_id"],
        "candidate_panel_id": candidate["panel_id"],
        "checks": checks,
        "wrapper_checks": wrapper_checks,
        "transfer_gate_pass": all(checks.values()),
    }


def _load_tokenizer(config: dict[str, Any], tokenizer_path: Path) -> tuple[Any, dict[str, Any]]:
    tokenizer_path = tokenizer_path.resolve()
    _require(tokenizer_path.is_dir(), f"Tokenizer path is not a directory: {tokenizer_path}")
    tokenizer_spec = config["tokenizer"]
    files: list[dict[str, Any]] = []
    for filename, expected in tokenizer_spec["required_files"].items():
        path = tokenizer_path / filename
        _require(path.is_file() and not path.is_symlink(), f"Missing tokenizer file: {filename}")
        actual = _sha256_file(path)
        _require(
            actual == expected,
            f"Tokenizer SHA-256 mismatch for {filename}: expected {expected}, got {actual}",
        )
        files.append({"path": filename, "bytes": path.stat().st_size, "sha256": actual})
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_path,
        local_files_only=True,
        trust_remote_code=False,
        use_fast=True,
    )
    _require(getattr(tokenizer, "is_fast", False), "A fast tokenizer is required")
    _require(type(tokenizer).__name__ == tokenizer_spec["class"], "Tokenizer class mismatch")
    _require(int(tokenizer.vocab_size) == tokenizer_spec["vocab_size"], "Vocab size mismatch")
    _require(len(tokenizer) == tokenizer_spec["tokenizer_length"], "Tokenizer length mismatch")
    observed_special = {
        key: getattr(tokenizer, key, None)
        for key in ("bos_token_id", "eos_token_id", "pad_token_id")
    }
    _require(
        observed_special == tokenizer_spec["special_token_ids"],
        f"Special token ids differ: {observed_special}",
    )
    return tokenizer, {
        "model": tokenizer_spec["model"],
        "revision": tokenizer_spec["revision"],
        "tokenizer_class": type(tokenizer).__name__,
        "vocab_size": int(tokenizer.vocab_size),
        "tokenizer_length": len(tokenizer),
        "special_token_ids": observed_special,
        "files": files,
        "file_manifest_sha256": hashlib.sha256(_json_bytes(files)).hexdigest(),
        "local_path_recorded": False,
    }


def run_audit(config_path: Path, tokenizer_path: Path) -> dict[str, Any]:
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
    config_dir = config_path.parent
    reference_spec = config["reference_panel"]
    reference_path = _verified_input(
        config_dir,
        reference_spec["path"],
        reference_spec["sha256"],
        allowed_root=ALLOWED_PANEL_ROOT,
    )
    candidate_specs = config.get("candidate_panels")
    _require(isinstance(candidate_specs, list) and len(candidate_specs) == 3, "Need three candidates")
    candidate_paths = [
        _verified_input(
            config_dir,
            spec["path"],
            spec["sha256"],
            allowed_root=ALLOWED_PANEL_ROOT,
        )
        for spec in candidate_specs
    ]
    wrapper_spec = config["wrappers"]
    wrapper_path = _verified_input(
        config_dir,
        wrapper_spec["path"],
        wrapper_spec["sha256"],
        allowed_root=ALLOWED_WRAPPER_ROOT,
    )
    wrappers = _load_wrappers(wrapper_path, int(wrapper_spec["expected_count"]))
    tokenizer, tokenizer_receipt = _load_tokenizer(config, tokenizer_path)
    reference = _summary(
        tokenizer,
        reference_spec["id"],
        _load_panel(reference_path, reference_spec["id"]),
        wrappers,
    )
    candidates = [
        _summary(
            tokenizer,
            spec["id"],
            _load_panel(path, spec["id"]),
            wrappers,
        )
        for spec, path in zip(candidate_specs, candidate_paths, strict=True)
    ]
    comparisons = [_compare_summaries(reference, candidate) for candidate in candidates]
    all_pass = all(row["transfer_gate_pass"] for row in comparisons)
    return {
        "schema_version": 1,
        "audit_id": config["audit_id"],
        "status": (
            "existing_controls_transfer_matched"
            if all_pass
            else "existing_controls_do_not_transfer"
        ),
        "claim_boundary": {
            **boundary,
            "tokenizer_only": True,
            "model_forward_count": 0,
        },
        "data_scope": {
            "study_target_banks_accessed": False,
            "panel_files": [
                str(reference_path.relative_to(ROOT)),
                *[str(path.relative_to(ROOT)) for path in candidate_paths],
            ],
            "wrappers_file": str(wrapper_path.relative_to(ROOT)),
        },
        "config": {
            "path": str(config_path.relative_to(ROOT)),
            "sha256": _sha256_file(config_path),
        },
        "tokenizer": tokenizer_receipt,
        "matching_contract": config["matching_contract"],
        "reference": reference,
        "candidates": candidates,
        "comparisons": comparisons,
        "all_three_transfer_gate_pass": all_pass,
        "decision": (
            "The fixed GPT-2 controls are tokenizer-compatible inputs to a separately "
            "frozen Llama exploratory protocol; this audit still authorizes no model forward."
            if all_pass
            else "Do not reuse the GPT-2 matched-null panels for Llama. Build and freeze "
            "Llama-specific controls from tokenizer-only information before any study forward."
        ),
    }


def _atomic_write_json_no_overwrite(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise AuditError(f"Refusing to overwrite existing receipt: {path}")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise AuditError(f"Refusing to overwrite existing receipt: {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = _parser().parse_args()
    receipt = run_audit(args.config, args.tokenizer_path)
    _atomic_write_json_no_overwrite(args.output, receipt)
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "all_three_transfer_gate_pass": receipt[
                    "all_three_transfer_gate_pass"
                ],
                "output": str(args.output.resolve()),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
