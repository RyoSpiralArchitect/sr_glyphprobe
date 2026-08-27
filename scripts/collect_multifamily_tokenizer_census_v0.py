#!/usr/bin/env python3
"""Verify and aggregate the three frozen tokenizer-census node bundles.

This collector is intentionally post hoc and descriptive. It verifies the
hash-bound node artifacts, derives deterministic structural summaries, and
never loads a tokenizer, model, target bank, activation, logit, or behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROTOCOL_ID = "glyphprobe-multifamily-tokenizer-census-v0"
ANALYSIS_ID = "glyphprobe-multifamily-tokenizer-census-v0-posthoc-aggregate-v1"
FROZEN_COMMIT = "e3bea44a145d3c87f41fc5c60f90201b8cea2bdc"
NODES = ("mac1", "mac2", "furnace")
EXPECTED_ITEMS = 115
EXPECTED_CONTEXTS = ("raw", "leading_space", "marker_wrapper", "glyph_prompt")
PAIRWISE_CONTEXTS = ("raw", "leading_space", "glyph_prompt")
EXPECTED_PAIRS = EXPECTED_ITEMS * (EXPECTED_ITEMS - 1) // 2
REQUIRED_BUNDLE_FILES = (
    "tokenizations.jsonl",
    "pairwise_controls.jsonl",
    "summary.json",
    "receipt.json",
    "SHA256SUMS",
)
HASHED_BUNDLE_FILES = REQUIRED_BUNDLE_FILES[:-1]
FOCAL_TARGETS = ("blue_circle", "blue_square")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
LOCAL_PATH_REDACTION = "<local-path-redacted>"

CLAIM_BOUNDARY = (
    "Post hoc descriptive aggregation of the frozen tokenizer-only census. "
    "This artifact performs no model forward, activation capture, intervention, "
    "behavioral or semantic test, confirmation, causal localization, control "
    "freeze, or Phase I gate decision."
)


class CollectionError(RuntimeError):
    """Raised when a source bundle or derived artifact violates the contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CollectionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: Any, *, pretty: bool = True) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2 if pretty else None,
            separators=None if pretty else (",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.partial-{os.getpid()}")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_bytes_atomic(path, json_bytes(value))


def scrub_public_metadata(value: Any) -> Any:
    """Remove machine-local absolute paths from public metadata copies."""

    if isinstance(value, dict):
        return {key: scrub_public_metadata(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_public_metadata(item) for item in value]
    if isinstance(value, str) and value.startswith("/"):
        return LOCAL_PATH_REDACTION
    return value


def absolute_path_values(value: Any, location: str = "$") -> list[str]:
    """Return JSON locations whose string values are absolute local paths."""

    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(absolute_path_values(item, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(absolute_path_values(item, f"{location}[{index}]"))
    elif isinstance(value, str) and value.startswith("/"):
        findings.append(location)
    return findings


def read_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON root must be an object: {path}")
    return value


def read_jsonl(path: Path) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise CollectionError(
                    f"Invalid JSONL at {path}:{line_number}: {exc}"
                ) from exc
            require(
                isinstance(value, dict),
                f"JSONL row must be an object: {path}:{line_number}",
            )
            rows.append(value)
    return rows


def parse_sha256sums(path: Path) -> Mapping[str, str]:
    records: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = raw.split("  ", 1)
        require(len(parts) == 2, f"Malformed SHA256SUMS line {path}:{line_number}")
        digest, name = parts
        require(len(digest) == 64, f"Invalid digest at {path}:{line_number}")
        require(name not in records, f"Duplicate checksum name: {path}:{name}")
        records[name] = digest
    return records


def common_prefix_length(left: Sequence[int], right: Sequence[int]) -> int:
    count = 0
    for left_value, right_value in zip(left, right, strict=False):
        if left_value != right_value:
            break
        count += 1
    return count


def tokenization_signature(rows: Sequence[Mapping[str, Any]]) -> str:
    normalized = [
        {
            "item_id": row["item_id"],
            "context_id": row["context_id"],
            "token_ids": row["token_ids"],
            "offset_mapping": row["offset_mapping"],
            "whole_token_count": row["whole_token_count"],
            "span_token_positions": row["span_token_positions"],
            "span_token_ids": row["span_token_ids"],
            "span_token_count": row["span_token_count"],
            "decoded_text": row["decoded_text"],
            "roundtrip_exact": row["roundtrip_exact"],
        }
        for row in sorted(
            rows, key=lambda value: (value["item_id"], value["context_id"])
        )
    ]
    return hashlib.sha256(json_bytes(normalized, pretty=False)).hexdigest()


def verify_node_bundle(node_dir: Path, node: str) -> Mapping[str, Any]:
    require(node_dir.is_dir(), f"Missing node bundle: {node_dir}")
    for name in REQUIRED_BUNDLE_FILES:
        require((node_dir / name).is_file(), f"Missing node artifact: {node}/{name}")

    sums = parse_sha256sums(node_dir / "SHA256SUMS")
    require(set(sums) == set(HASHED_BUNDLE_FILES), f"Checksum roster differs: {node}")
    for name, expected in sums.items():
        require(sha256(node_dir / name) == expected, f"Checksum differs: {node}/{name}")

    receipt = read_json(node_dir / "receipt.json")
    summary = read_json(node_dir / "summary.json")
    require(receipt.get("protocol_id") == PROTOCOL_ID, f"Protocol differs: {node}")
    require(receipt.get("node") == node, f"Receipt node differs: {node}")
    require(receipt.get("status") == "complete", f"Node is not complete: {node}")
    require(
        receipt.get("model_forward_calls") == 0, f"Model forwards are nonzero: {node}"
    )
    require(
        receipt.get("protected_target_files_opened") == 0,
        f"Protected-target access is nonzero: {node}",
    )
    require(
        summary.get("protocol_id") == PROTOCOL_ID, f"Summary protocol differs: {node}"
    )
    require(summary.get("node") == node, f"Summary node differs: {node}")
    require(
        summary.get("panel_item_count") == EXPECTED_ITEMS, f"Item count differs: {node}"
    )
    require(
        summary.get("context_count") == len(EXPECTED_CONTEXTS),
        f"Context count differs: {node}",
    )
    require(
        receipt.get("successful_labels") == receipt.get("frozen_roster_labels"),
        f"Roster has a failure or reordering: {node}",
    )
    require(
        summary.get("successful_tokenizer_count") == len(receipt["successful_labels"]),
        f"Successful count differs: {node}",
    )

    output_hashes = receipt.get("output_sha256")
    require(isinstance(output_hashes, dict), f"Output hashes missing: {node}")
    for name in ("tokenizations.jsonl", "pairwise_controls.jsonl", "summary.json"):
        require(
            output_hashes.get(name) == sums[name],
            f"Receipt output hash differs: {node}/{name}",
        )

    tokenizations = read_jsonl(node_dir / "tokenizations.jsonl")
    pairwise = read_jsonl(node_dir / "pairwise_controls.jsonl")
    row_counts = receipt.get("row_counts")
    require(isinstance(row_counts, dict), f"Row counts missing: {node}")
    require(
        row_counts.get("tokenizations.jsonl") == len(tokenizations),
        f"Tokenization row count differs: {node}",
    )
    require(
        row_counts.get("pairwise_controls.jsonl") == len(pairwise),
        f"Pairwise row count differs: {node}",
    )
    require(len(pairwise) == EXPECTED_PAIRS, f"Pairwise roster differs: {node}")

    labels = list(receipt["successful_labels"])
    expected_tokenization_rows = len(labels) * EXPECTED_ITEMS * len(EXPECTED_CONTEXTS)
    require(
        len(tokenizations) == expected_tokenization_rows,
        f"Tokenization row roster differs: {node}",
    )
    keys: set[tuple[str, str, str]] = set()
    by_label_items: dict[str, set[str]] = defaultdict(set)
    by_label_contexts: dict[str, set[str]] = defaultdict(set)
    for row in tokenizations:
        require(row.get("protocol_id") == PROTOCOL_ID, f"Row protocol differs: {node}")
        require(row.get("node") == node, f"Row node differs: {node}")
        label = str(row.get("tokenizer_label"))
        require(label in labels, f"Unexpected tokenizer label: {node}/{label}")
        item_id = str(row.get("item_id"))
        context_id = str(row.get("context_id"))
        key = (label, item_id, context_id)
        require(key not in keys, f"Duplicate tokenization key: {node}/{key}")
        keys.add(key)
        by_label_items[label].add(item_id)
        by_label_contexts[label].add(context_id)
    for label in labels:
        require(
            len(by_label_items[label]) == EXPECTED_ITEMS,
            f"Item roster differs: {label}",
        )
        require(
            by_label_contexts[label] == set(EXPECTED_CONTEXTS),
            f"Context roster differs: {label}",
        )

    pair_keys: set[tuple[str, str]] = set()
    for row in pairwise:
        require(row.get("protocol_id") == PROTOCOL_ID, f"Pair protocol differs: {node}")
        require(row.get("node") == node, f"Pair node differs: {node}")
        key = (str(row.get("left_item_id")), str(row.get("right_item_id")))
        require(key not in pair_keys, f"Duplicate item pair: {node}/{key}")
        pair_keys.add(key)
        contexts = row.get("contexts")
        require(isinstance(contexts, dict), f"Pair contexts missing: {node}/{key}")
        require(
            set(contexts) == set(PAIRWISE_CONTEXTS),
            f"Pair contexts differ: {node}/{key}",
        )

    return {
        "node": node,
        "path": node_dir,
        "receipt": receipt,
        "summary": summary,
        "tokenizations": tokenizations,
        "pairwise": pairwise,
        "sha256sums": sums,
    }


def verify_collection(input_root: Path) -> Mapping[str, Mapping[str, Any]]:
    bundles = {node: verify_node_bundle(input_root / node, node) for node in NODES}
    for authority_name in ("config", "manifest", "script"):
        hashes = {
            str(bundle["receipt"][authority_name]["sha256"])
            for bundle in bundles.values()
        }
        require(len(hashes) == 1, f"Frozen {authority_name} hash differs across nodes")

    labels = [
        label
        for bundle in bundles.values()
        for label in bundle["receipt"]["successful_labels"]
    ]
    require(len(labels) == len(set(labels)) == 14, "Combined tokenizer roster differs")

    item_metadata: dict[tuple[str, str], tuple[Any, ...]] = {}
    metadata_fields = (
        "glyph",
        "census_family",
        "construction",
        "base_id",
        "component_ids",
        "codepoints",
        "utf8_hex",
        "contains_zwj",
        "contains_vs16",
        "item_char_span",
        "text_sha256",
    )
    for bundle in bundles.values():
        for row in bundle["tokenizations"]:
            key = (str(row["item_id"]), str(row["context_id"]))
            value = tuple(
                json.dumps(row[field], sort_keys=True) for field in metadata_fields
            )
            if key in item_metadata:
                require(
                    item_metadata[key] == value,
                    f"Item metadata differs across nodes: {key}",
                )
            else:
                item_metadata[key] = value
    require(
        len(item_metadata) == EXPECTED_ITEMS * len(EXPECTED_CONTEXTS),
        "Combined item/context roster differs",
    )
    return bundles


def build_equivalence_classes(
    rows: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    by_label: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_label[str(row["tokenizer_label"])].append(row)
    grouped: dict[str, list[str]] = defaultdict(list)
    for label, label_rows in by_label.items():
        grouped[tokenization_signature(label_rows)].append(label)
    classes: list[Mapping[str, Any]] = []
    ordered = sorted(grouped.items(), key=lambda item: sorted(item[1]))
    for index, (signature, labels) in enumerate(ordered, start=1):
        labels = sorted(labels)
        classes.append(
            {
                "class_id": f"tokenization_output_class_{index:02d}",
                "signature_sha256": signature,
                "member_count": len(labels),
                "labels": labels,
                "representative_label": labels[0],
                "exact_item_context_rows": EXPECTED_ITEMS * len(EXPECTED_CONTEXTS),
            }
        )
    return classes


def histogram(values: Iterable[int]) -> Mapping[str, int]:
    return {str(key): count for key, count in sorted(Counter(values).items())}


def raw_stats(values: Sequence[int]) -> Mapping[str, Any]:
    require(bool(values), "Raw token-count vector is empty")
    return {
        "count": len(values),
        "minimum": min(values),
        "maximum": max(values),
        "mean": round(sum(values) / len(values), 9),
        "median": statistics.median(values),
        "histogram": histogram(values),
    }


def candidate_ids(
    *,
    lookup: Mapping[tuple[str, str, str], Mapping[str, Any]],
    labels: Sequence[str],
    target_id: str,
    candidate_item_ids: Sequence[str],
    context_id: str,
    minimum_prefix: int,
) -> list[str]:
    matches: list[str] = []
    for candidate_id in sorted(candidate_item_ids):
        if candidate_id == target_id:
            continue
        acceptable = True
        for label in labels:
            target = lookup[(label, target_id, context_id)]["span_token_ids"]
            candidate = lookup[(label, candidate_id, context_id)]["span_token_ids"]
            if len(target) != len(candidate):
                acceptable = False
                break
            if common_prefix_length(target, candidate) < minimum_prefix:
                acceptable = False
                break
        if acceptable:
            matches.append(candidate_id)
    return matches


def build_aggregate(bundles: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    rows = [row for bundle in bundles.values() for row in bundle["tokenizations"]]
    pairs = [row for bundle in bundles.values() for row in bundle["pairwise"]]
    classes = build_equivalence_classes(rows)
    representatives = [str(value["representative_label"]) for value in classes]
    label_nodes = {str(row["tokenizer_label"]): str(row["node"]) for row in rows}
    cross_node_exact_groups = [
        {
            "class_id": str(token_class["class_id"]),
            "labels": token_class["labels"],
            "nodes": sorted(
                {label_nodes[str(label)] for label in token_class["labels"]}
            ),
        }
        for token_class in classes
        if len({label_nodes[str(label)] for label in token_class["labels"]}) > 1
    ]
    lookup = {
        (str(row["tokenizer_label"]), str(row["item_id"]), str(row["context_id"])): row
        for row in rows
    }
    raw_rows = [row for row in rows if row["context_id"] == "raw"]
    item_ids = sorted({str(row["item_id"]) for row in raw_rows})
    item_family = {str(row["item_id"]): str(row["census_family"]) for row in raw_rows}
    item_construction = {
        str(row["item_id"]): str(row["construction"]) for row in raw_rows
    }
    raw_lookup = {
        (str(row["tokenizer_label"]), str(row["item_id"])): row for row in raw_rows
    }

    raw_by_class: dict[str, Any] = {}
    wrapper_sensitivity: dict[str, Any] = {}
    for token_class in classes:
        class_id = str(token_class["class_id"])
        label = str(token_class["representative_label"])
        label_items = sorted(
            str(row["item_id"]) for row in raw_rows if row["tokenizer_label"] == label
        )
        raw_by_class[class_id] = {
            "representative_label": label,
            "member_labels": token_class["labels"],
            **raw_stats(
                [
                    int(lookup[(label, item_id, "raw")]["span_token_count"])
                    for item_id in label_items
                ]
            ),
        }
        context_records: dict[str, Any] = {}
        for context_id in EXPECTED_CONTEXTS[1:]:
            count_changed = 0
            ids_changed = 0
            for item_id in label_items:
                raw = lookup[(label, item_id, "raw")]
                contextual = lookup[(label, item_id, context_id)]
                count_changed += (
                    raw["span_token_count"] != contextual["span_token_count"]
                )
                ids_changed += raw["span_token_ids"] != contextual["span_token_ids"]
            context_records[context_id] = {
                "item_count": len(label_items),
                "span_token_count_changed": count_changed,
                "span_token_ids_changed": ids_changed,
            }
        wrapper_sensitivity[class_id] = {
            "representative_label": label,
            "contexts": context_records,
        }

    item_ranges: list[Mapping[str, Any]] = []
    for item_id in item_ids:
        counts = {
            str(token_class["class_id"]): int(
                raw_lookup[(str(token_class["representative_label"]), item_id)][
                    "span_token_count"
                ]
            )
            for token_class in classes
        }
        values = list(counts.values())
        item_ranges.append(
            {
                "item_id": item_id,
                "census_family": item_family[item_id],
                "construction": item_construction[item_id],
                "token_counts": counts,
                "minimum": min(values),
                "maximum": max(values),
                "range": max(values) - min(values),
            }
        )

    composition: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: {"base_delta": [], "component_sum_gap": []}
    )
    for token_class in classes:
        label = str(token_class["representative_label"])
        for item_id in item_ids:
            row = raw_lookup[(label, item_id)]
            construction = str(row["construction"])
            base_id = row.get("base_id")
            if base_id is not None:
                composition[construction]["base_delta"].append(
                    int(row["span_token_count"])
                    - int(raw_lookup[(label, str(base_id))]["span_token_count"])
                )
            component_ids = row.get("component_ids") or []
            if component_ids:
                composition[construction]["component_sum_gap"].append(
                    int(row["span_token_count"])
                    - sum(
                        int(raw_lookup[(label, str(component_id))]["span_token_count"])
                        for component_id in component_ids
                    )
                )
    composition_histograms = {
        construction: {
            relation: {
                "observation_count": len(values),
                "histogram": histogram(values),
            }
            for relation, values in records.items()
            if values
        }
        for construction, records in sorted(composition.items())
    }

    pairwise_counts: dict[str, Any] = {}
    for context_id in PAIRWISE_CONTEXTS:
        class_records: dict[str, Any] = {}
        for token_class in classes:
            class_id = str(token_class["class_id"])
            label = str(token_class["representative_label"])
            counts = Counter()
            for left_id, right_id in itertools.combinations(item_ids, 2):
                left_ids = lookup[(label, left_id, context_id)]["span_token_ids"]
                right_ids = lookup[(label, right_id, context_id)]["span_token_ids"]
                prefix = common_prefix_length(left_ids, right_ids)
                equal_count = len(left_ids) == len(right_ids)
                counts["equal_token_count"] += equal_count
                counts["equal_count_and_prefix_1"] += equal_count and prefix >= 1
                counts["equal_count_and_prefix_2"] += equal_count and prefix >= 2
                counts["exact_span_token_sequence"] += left_ids == right_ids
            class_records[class_id] = {
                "representative_label": label,
                "pair_count": EXPECTED_PAIRS,
                **{key: int(value) for key, value in sorted(counts.items())},
            }
        pairwise_counts[context_id] = class_records

    non_glyph_ids = sorted(
        item_id for item_id in item_ids if item_family[item_id] == "non_glyph_control"
    )
    colored_shape_ids = sorted(
        item_id for item_id in item_ids if item_family[item_id] == "colored_shape"
    )
    focal_records: dict[str, Any] = {}
    for target_id in FOCAL_TARGETS:
        require(target_id in item_ids, f"Missing focal target: {target_id}")
        contexts: dict[str, Any] = {}
        for context_id in PAIRWISE_CONTEXTS:
            by_class: dict[str, Any] = {}
            for token_class in classes:
                class_id = str(token_class["class_id"])
                label = str(token_class["representative_label"])
                target_ids = lookup[(label, target_id, context_id)]["span_token_ids"]
                candidates: dict[str, list[Mapping[str, Any]]] = {}
                for candidate_set_name, candidate_set in (
                    ("non_glyph_controls", non_glyph_ids),
                    ("colored_shapes", colored_shape_ids),
                ):
                    values: list[Mapping[str, Any]] = []
                    for candidate_id in candidate_set:
                        if candidate_id == target_id:
                            continue
                        candidate_span = lookup[(label, candidate_id, context_id)][
                            "span_token_ids"
                        ]
                        if len(target_ids) == len(candidate_span):
                            values.append(
                                {
                                    "item_id": candidate_id,
                                    "span_token_count": len(candidate_span),
                                    "shared_prefix_length": common_prefix_length(
                                        target_ids, candidate_span
                                    ),
                                }
                            )
                    candidates[candidate_set_name] = values
                by_class[class_id] = {
                    "representative_label": label,
                    "target_span_token_count": len(target_ids),
                    "target_span_token_ids": target_ids,
                    **candidates,
                }
            universal: dict[str, Any] = {}
            for candidate_set_name, candidate_set in (
                ("non_glyph_controls", non_glyph_ids),
                ("all_fixed_items", item_ids),
            ):
                universal[candidate_set_name] = {
                    "equal_count": candidate_ids(
                        lookup=lookup,
                        labels=representatives,
                        target_id=target_id,
                        candidate_item_ids=candidate_set,
                        context_id=context_id,
                        minimum_prefix=0,
                    ),
                    "equal_count_and_prefix_1": candidate_ids(
                        lookup=lookup,
                        labels=representatives,
                        target_id=target_id,
                        candidate_item_ids=candidate_set,
                        context_id=context_id,
                        minimum_prefix=1,
                    ),
                    "equal_count_and_prefix_2": candidate_ids(
                        lookup=lookup,
                        labels=representatives,
                        target_id=target_id,
                        candidate_item_ids=candidate_set,
                        context_id=context_id,
                        minimum_prefix=2,
                    ),
                }
            contexts[context_id] = {"by_output_class": by_class, "universal": universal}
        focal_records[target_id] = {"contexts": contexts}

    roundtrip_failures = [row for row in rows if not row["roundtrip_exact"]]

    def focal_candidate_exists(
        target_id: str,
        candidate_set: str,
        match_rule: str,
        *,
        require_all_contexts: bool,
    ) -> bool:
        per_context = [
            bool(
                focal_records[target_id]["contexts"][context_id]["universal"][
                    candidate_set
                ][match_rule]
            )
            for context_id in PAIRWISE_CONTEXTS
        ]
        return all(per_context) if require_all_contexts else any(per_context)

    all_roster_entries_succeeded = all(
        bundle["receipt"]["successful_labels"]
        == bundle["receipt"]["frozen_roster_labels"]
        for bundle in bundles.values()
    )
    focal_all_contexts_closed_by_non_glyph = all(
        focal_candidate_exists(
            target_id,
            "non_glyph_controls",
            "equal_count_and_prefix_1",
            require_all_contexts=True,
        )
        for target_id in FOCAL_TARGETS
    )
    return {
        "schema_version": 1,
        "analysis_id": ANALYSIS_ID,
        "census_protocol_id": PROTOCOL_ID,
        "analysis_role": "posthoc_descriptive_tokenizer_structure_aggregation",
        "claim_boundary": CLAIM_BOUNDARY,
        "integrity": {
            "nodes": list(NODES),
            "node_count": len(NODES),
            "roster_entries": len({row["tokenizer_label"] for row in rows}),
            "successful_roster_entries": sum(
                len(bundle["receipt"]["successful_labels"])
                for bundle in bundles.values()
            ),
            "panel_items": len(item_ids),
            "contexts": list(EXPECTED_CONTEXTS),
            "tokenization_rows": len(rows),
            "pairwise_rows": len(pairs),
            "model_forward_calls": 0,
            "protected_target_files_opened": 0,
            "frozen_authority_sha256": {
                authority_name: next(
                    iter(
                        {
                            bundle["receipt"][authority_name]["sha256"]
                            for bundle in bundles.values()
                        }
                    )
                )
                for authority_name in ("config", "manifest", "script")
            },
        },
        "tokenization_output_classes": classes,
        "unique_output_class_count": len(classes),
        "cross_node_exact_reproduction_groups_on_fixed_panel": cross_node_exact_groups,
        "raw_token_count_by_output_class": raw_by_class,
        "cross_class_raw_item_ranges": item_ranges,
        "cross_class_raw_range_histogram": histogram(
            int(record["range"]) for record in item_ranges
        ),
        "items_with_identical_raw_token_count_across_classes": [
            record["item_id"] for record in item_ranges if record["range"] == 0
        ],
        "wrapper_sensitivity": wrapper_sensitivity,
        "roundtrip": {
            "row_count": len(rows),
            "exact_count": len(rows) - len(roundtrip_failures),
            "failure_count": len(roundtrip_failures),
            "failure_by_label": dict(
                sorted(
                    Counter(
                        str(row["tokenizer_label"]) for row in roundtrip_failures
                    ).items()
                )
            ),
            "failure_by_context": dict(
                sorted(
                    Counter(
                        str(row["context_id"]) for row in roundtrip_failures
                    ).items()
                )
            ),
        },
        "composition_delta_histograms_across_unique_output_classes": composition_histograms,
        "pairwise_match_counts_by_output_class": pairwise_counts,
        "focal_target_control_census": focal_records,
        "decision_relevant_descriptive_flags": {
            "all_roster_entries_succeeded": all_roster_entries_succeeded,
            "cross_node_exact_reproduction_group_count_on_fixed_panel": len(
                cross_node_exact_groups
            ),
            "blue_circle_has_universal_equal_count_prefix_1_candidate_in_any_fixed_context": focal_candidate_exists(
                "blue_circle",
                "all_fixed_items",
                "equal_count_and_prefix_1",
                require_all_contexts=False,
            ),
            "blue_circle_has_universal_equal_count_prefix_1_candidate_in_all_fixed_contexts": focal_candidate_exists(
                "blue_circle",
                "all_fixed_items",
                "equal_count_and_prefix_1",
                require_all_contexts=True,
            ),
            "blue_square_has_universal_equal_count_prefix_1_candidate_in_any_fixed_context": focal_candidate_exists(
                "blue_square",
                "all_fixed_items",
                "equal_count_and_prefix_1",
                require_all_contexts=False,
            ),
            "blue_square_has_universal_equal_count_prefix_1_candidate_in_all_fixed_contexts": focal_candidate_exists(
                "blue_square",
                "all_fixed_items",
                "equal_count_and_prefix_1",
                require_all_contexts=True,
            ),
            "existing_non_glyph_panel_closes_both_focal_prefix_controls_in_all_fixed_contexts": focal_all_contexts_closed_by_non_glyph,
        },
        "interpretation_limits": [
            "The seven output classes are exact equivalence only on the fixed 115 items and four contexts.",
            "Token IDs are compared only within a tokenizer output class, never across vocabularies.",
            "Equal token count or prefix structure does not establish semantic equivalence.",
            "The focal-target summary is post hoc control-design evidence and is not a new frozen control set.",
            "No activation, behavior, mechanism, causality, or cross-model scientific result follows from this aggregation.",
        ],
    }


def source_receipt_record(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    path = Path(bundle["path"])
    receipt = bundle["receipt"]
    return {
        "node": bundle["node"],
        "status": receipt["status"],
        "receipt_sha256": sha256(path / "receipt.json"),
        "summary_sha256": sha256(path / "summary.json"),
        "source_sha256sums_sha256": sha256(path / "SHA256SUMS"),
        "tokenizations_sha256": receipt["output_sha256"]["tokenizations.jsonl"],
        "pairwise_controls_sha256": receipt["output_sha256"]["pairwise_controls.jsonl"],
        "tokenization_rows": receipt["row_counts"]["tokenizations.jsonl"],
        "pairwise_rows": receipt["row_counts"]["pairwise_controls.jsonl"],
        "successful_labels": receipt["successful_labels"],
        "model_forward_calls": receipt["model_forward_calls"],
        "protected_target_files_opened": receipt["protected_target_files_opened"],
    }


def publish_collection(
    *, input_root: Path, output: Path, source_commit: str, script_path: Path
) -> Mapping[str, Any]:
    require(
        source_commit == FROZEN_COMMIT,
        "Source commit must be the public v0 freeze commit",
    )
    bundles = verify_collection(input_root)
    output = output.resolve()
    require(not output.exists(), f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.parent / f".incoming-{output.name}-{os.getpid()}"
    require(not staging.exists(), f"Staging path exists: {staging}")
    staging.mkdir()
    try:
        source_root = staging / "source_nodes"
        for node, bundle in bundles.items():
            node_output = source_root / node
            node_output.mkdir(parents=True)
            for name, value in (
                ("receipt.json", bundle["receipt"]),
                ("summary.json", bundle["summary"]),
            ):
                write_json(node_output / name, scrub_public_metadata(value))
            shutil.copyfile(
                Path(bundle["path"]) / "SHA256SUMS",
                node_output / "SOURCE_SHA256SUMS",
            )
            node_public_files = (
                "receipt.json",
                "summary.json",
                "SOURCE_SHA256SUMS",
            )
            write_bytes_atomic(
                node_output / "SHA256SUMS",
                (
                    "\n".join(
                        f"{sha256(node_output / name)}  {name}"
                        for name in node_public_files
                    )
                    + "\n"
                ).encode("utf-8"),
            )

        aggregate = build_aggregate(bundles)
        write_json(staging / "aggregate.json", aggregate)
        receipt = {
            "schema_version": 1,
            "analysis_id": ANALYSIS_ID,
            "census_protocol_id": PROTOCOL_ID,
            "status": "pass",
            "role": "posthoc_descriptive_collection_receipt",
            "claim_boundary": CLAIM_BOUNDARY,
            "census_freeze_commit": source_commit,
            "model_forward_calls": 0,
            "protected_target_files_opened": 0,
            "source_nodes": {
                node: source_receipt_record(bundle) for node, bundle in bundles.items()
            },
            "script": {
                "path": "scripts/collect_multifamily_tokenizer_census_v0.py",
                "sha256": sha256(script_path),
            },
            "aggregate": {
                "path": "aggregate.json",
                "sha256": sha256(staging / "aggregate.json"),
            },
            "raw_jsonl_publication": {
                "included_in_git_artifact": False,
                "reason": (
                    "Git retains node receipts, summaries, and exact raw-output hashes; "
                    "the 38 MiB raw node tables remain separate run artifacts."
                ),
            },
            "public_source_metadata": {
                "receipt_and_summary_copies": "absolute_paths_redacted",
                "absolute_path_replacement": LOCAL_PATH_REDACTION,
                "source_hashes_reference_original_node_outputs": True,
                "public_node_checksum_ledger": "SHA256SUMS",
                "original_source_checksum_ledger": "SOURCE_SHA256SUMS",
            },
        }
        write_json(staging / "collection_receipt.json", receipt)
        published_files = sorted(
            path.relative_to(staging).as_posix()
            for path in staging.rglob("*")
            if path.is_file()
        )
        checksum_lines = [
            f"{sha256(staging / name)}  {name}" for name in published_files
        ]
        write_bytes_atomic(
            staging / "SHA256SUMS",
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        os.replace(staging, output)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return receipt


def validate_published_output(path: Path, script_path: Path) -> Mapping[str, Any]:
    path = path.resolve()
    require(path.is_dir(), f"Published output missing: {path}")
    sums = parse_sha256sums(path / "SHA256SUMS")
    actual_files = {
        file.relative_to(path).as_posix()
        for file in path.rglob("*")
        if file.is_file() and file.relative_to(path).as_posix() != "SHA256SUMS"
    }
    require(set(sums) == actual_files, "Published checksum roster differs")
    for name, expected in sums.items():
        require(sha256(path / name) == expected, f"Published checksum differs: {name}")
    receipt = read_json(path / "collection_receipt.json")
    aggregate = read_json(path / "aggregate.json")
    require(receipt.get("status") == "pass", "Collection receipt is not pass")
    require(receipt.get("analysis_id") == ANALYSIS_ID, "Receipt analysis ID differs")
    require(
        aggregate.get("analysis_id") == ANALYSIS_ID, "Aggregate analysis ID differs"
    )
    require(
        receipt["aggregate"]["sha256"] == sha256(path / "aggregate.json"),
        "Aggregate receipt hash differs",
    )
    require(
        receipt["script"]["sha256"] == sha256(script_path), "Collector hash differs"
    )
    public_metadata = receipt.get("public_source_metadata")
    require(isinstance(public_metadata, dict), "Public-source metadata policy missing")
    require(
        public_metadata.get("receipt_and_summary_copies") == "absolute_paths_redacted",
        "Public-source path policy differs",
    )
    source_records = receipt.get("source_nodes")
    require(isinstance(source_records, dict), "Source-node records missing")
    require(set(source_records) == set(NODES), "Source-node record roster differs")
    for node in NODES:
        node_path = path / "source_nodes" / node
        node_sums = parse_sha256sums(node_path / "SHA256SUMS")
        require(
            set(node_sums) == {"receipt.json", "summary.json", "SOURCE_SHA256SUMS"},
            f"Public node checksum roster differs: {node}",
        )
        for name, expected in node_sums.items():
            require(
                sha256(node_path / name) == expected,
                f"Public node checksum differs: {node}/{name}",
            )
        source_record = source_records[node]
        require(isinstance(source_record, dict), f"Source-node record invalid: {node}")
        source_ledger = node_path / "SOURCE_SHA256SUMS"
        require(
            source_record.get("source_sha256sums_sha256") == sha256(source_ledger),
            f"Original source-ledger hash differs: {node}",
        )
        source_sums = parse_sha256sums(source_ledger)
        expected_source_sums = {
            "receipt.json": source_record.get("receipt_sha256"),
            "summary.json": source_record.get("summary_sha256"),
            "tokenizations.jsonl": source_record.get("tokenizations_sha256"),
            "pairwise_controls.jsonl": source_record.get("pairwise_controls_sha256"),
        }
        require(
            source_sums == expected_source_sums,
            f"Original source-ledger bindings differ: {node}",
        )
        for name in ("receipt.json", "summary.json"):
            public_copy = read_json(node_path / name)
            findings = absolute_path_values(public_copy)
            require(
                not findings,
                f"Absolute path remains in public source metadata: {node}/{name}",
            )
    return {
        "status": "pass",
        "analysis_id": ANALYSIS_ID,
        "file_count": len(actual_files) + 1,
        "aggregate_sha256": sha256(path / "aggregate.json"),
        "collection_receipt_sha256": sha256(path / "collection_receipt.json"),
        "sha256sums_sha256": sha256(path / "SHA256SUMS"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input-root", type=Path)
    mode.add_argument("--validate-output", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-commit", default=FROZEN_COMMIT)
    parser.add_argument("--validate-input-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    script_path = Path(__file__).resolve()
    try:
        if args.validate_output is not None:
            result = validate_published_output(args.validate_output, script_path)
        else:
            require(
                HEX40_RE.fullmatch(args.source_commit) is not None,
                "Invalid source commit",
            )
            require(args.input_root is not None, "--input-root is required")
            if args.validate_input_only:
                bundles = verify_collection(args.input_root.resolve())
                result = {
                    "status": "pass",
                    "analysis_id": ANALYSIS_ID,
                    "nodes": list(bundles),
                    "tokenization_rows": sum(
                        len(bundle["tokenizations"]) for bundle in bundles.values()
                    ),
                    "pairwise_rows": sum(
                        len(bundle["pairwise"]) for bundle in bundles.values()
                    ),
                }
            else:
                require(args.output is not None, "--output is required for publication")
                publish_collection(
                    input_root=args.input_root.resolve(),
                    output=args.output,
                    source_commit=args.source_commit,
                    script_path=script_path,
                )
                result = validate_published_output(args.output, script_path)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (CollectionError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
