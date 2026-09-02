#!/usr/bin/env python3
"""Separately specified T21 confirmation; never calls historical text scanners."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import time
import uuid

import numpy as np
import yaml

import t19_lexical_alias_unicode_control_v0 as t19
import t21_glyph_context_path_pilot_v0 as pilot
import t21_path_inference_v0 as stats


ROOT = pilot.ROOT
PROTOCOL = "glyphprobe-t21-glyph-context-path-confirmation-v0"
CONFIG = Path("configs/t21_glyph_context_path_confirmation_v0.yaml")
VALIDATION = Path("validation/t21_glyph_context_path_confirmation_v0")
DESIGN = VALIDATION / "prospective_design.json"
PILOT_RESULTS = Path("validation/t21_glyph_context_path_pilot_v0/results")
BOUND_FILES = (
    *pilot.BOUND_FILES,
    pilot.SPEC,
    CONFIG,
    Path("scripts/t21_glyph_context_path_confirmation_v0.py"),
    Path("scripts/validate_t21_glyph_context_path_confirmation_v0.py"),
    Path("scripts/t21_path_inference_v0.py"),
    Path("tests/test_t21_glyph_context_path_confirmation_v0.py"),
    Path("tests/test_t21_path_inference_v0.py"),
    Path("docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.md"),
    Path("docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.ja.md"),
    Path("scripts/t19_lexical_alias_unicode_control_v0.py"),
    Path("configs/t19_lexical_alias_unicode_control_v0.yaml"),
    Path("scripts/glyph_system_decomposition_v0.py"),
    *(
        PILOT_RESULTS / name
        for name in (
            "pilot_result.json",
            "analysis_receipt.json",
            "acquisition_receipt.json",
            "independent_validation.json",
            "precision_and_quality_report.json",
        )
    ),
)


def config() -> dict:
    cfg = yaml.safe_load((ROOT / CONFIG).read_text(encoding="utf-8"))
    pilot.require(cfg["protocol_id"] == PROTOCOL, "Protocol mismatch")
    pilot.require(cfg["intervention"]["primary_anchor"] == 21, "Candidate changed")
    pilot.require(cfg["population"]["target_count"] == 195, "Target count changed")
    pilot.require(
        cfg["inference"]["contrasts"] == list(stats.NAMES), "Contrast family changed"
    )
    pilot.require(cfg["inference"]["seed"] == stats.INFERENCE_SEED, "Seed changed")
    return cfg


def specify(output: Path) -> dict:
    pilot.require(not output.exists(), "Design already exists")
    cfg = config()
    pilot.audit_spec(ROOT / pilot.SPEC)
    pilot.require(
        pilot.sha256(ROOT / pilot.SPEC) == cfg["pilot"]["specification_sha256"],
        "Pilot specification changed",
    )
    for name, key in (
        ("analysis_receipt.json", "analysis_receipt_sha256"),
        ("acquisition_receipt.json", "acquisition_receipt_sha256"),
        ("precision_and_quality_report.json", "precision_report_sha256"),
    ):
        pilot.require(
            pilot.sha256(ROOT / PILOT_RESULTS / name) == cfg["pilot"][key],
            "Pilot evidence changed",
        )
    result = pilot.read_json(ROOT / PILOT_RESULTS / "pilot_result.json")
    check = pilot.read_json(ROOT / PILOT_RESULTS / "independent_validation.json")
    pilot.require(
        result["candidate_anchor"] == 21
        and check["status"] == "pass"
        and check["candidate_anchor"] == 21
        and check["target_items_validated"] == 384,
        "Pilot progression or validation failed",
    )
    pilot.require(
        check["analysis_receipt_sha256"] == cfg["pilot"]["analysis_receipt_sha256"],
        "Independent validation not bound to pilot",
    )
    report = pilot.read_json(ROOT / PILOT_RESULTS / "precision_and_quality_report.json")
    pilot.require(
        report["inference_code_sha256"]
        == pilot.sha256(ROOT / "scripts/t21_path_inference_v0.py"),
        "Planning code changed",
    )
    design = {
        "protocol_id": PROTOCOL,
        "status": "specified_before_reserve_reconstruction_tokenization_or_model_forward",
        "created_at_utc": pilot.now(),
        "parent_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {p.as_posix(): pilot.sha256(ROOT / p) for p in BOUND_FILES},
        "input_sha256": pilot.audit_spec(ROOT / pilot.SPEC)["input_sha256"],
        "candidate_anchor": 21,
        "target_count": 195,
        "reserve_items_accessed_at_design": 0,
        "reserve_model_forwards_at_design": 0,
        "primary_rule": "all_five_one_sided_simultaneous_95_lower_bounds_positive",
        "registry": "internal_prospective_specification_not_external_registration",
    }
    pilot.write_json(output, design)
    return {
        "status": "design_specified",
        "design_sha256": pilot.sha256(output),
        "reserve_items_accessed": 0,
    }


def audit_design(path: Path) -> dict:
    value = pilot.read_json(path)
    pilot.require(
        value["protocol_id"] == PROTOCOL and value["candidate_anchor"] == 21,
        "Invalid design",
    )
    for relative, expected in {
        **value["source_sha256"],
        **value["input_sha256"],
    }.items():
        pilot.require(
            pilot.sha256(ROOT / relative) == expected,
            f"Changed design asset: {relative}",
        )
    return value


def require_published(path: Path) -> str:
    """Require these exact bytes at origin/main; fetch is an explicit operator step."""
    relative = path.resolve().relative_to(ROOT.resolve()).as_posix()
    published = subprocess.check_output(
        ["git", "show", f"origin/main:{relative}"], cwd=ROOT
    )
    pilot.require(
        published == path.read_bytes(), "Specification is not published at origin/main"
    )
    return subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=ROOT, text=True
    ).strip()


def base_spec(design_path: Path, mode: str) -> dict:
    audit_design(design_path)
    old = pilot.audit_spec(ROOT / pilot.SPEC)
    return {
        "protocol_id": PROTOCOL,
        "status": "specified_before_confirmation_forwards",
        "mode": mode,
        "created_at_utc": pilot.now(),
        "design_sha256": pilot.sha256(design_path),
        "design_path": design_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "model_artifact": old["model_artifact"],
        "source_tokens": old["source_tokens"],
        "source_count": 128,
        "contexts": old["contexts"],
        "anchors": old["anchors"],
        "conditions": old["conditions"],
        "views": old["views"],
        "primary_anchor": 21,
    }


def prepare_canary(design_path: Path, output: Path) -> dict:
    require_published(design_path)
    spec = base_spec(design_path, "exposed_canary")
    old = pilot.audit_spec(ROOT / pilot.SPEC)
    spec.update(
        {
            "target_tokens": old["target_tokens"][:8],
            "donor_indices": old["donor_indices"][:8],
            "target_count": 8,
            "reserve_items_accessed": 0,
            "reserve_model_forwards": 0,
        }
    )
    pilot.write_json(output, spec)
    return {"status": "canary_specified", "specification_sha256": pilot.sha256(output)}


def known_items() -> tuple[dict, list[dict], list[dict], list[dict]]:
    exposed, source = pilot.input_rows()
    selection = pilot.read_json(ROOT / pilot.config()["population"]["donor_selection"])
    symbols = [r for r in selection["observational_items"] if r["kind"] == "symbol"]
    used = [r for r in selection["observational_items"] if r["kind"] == "emoji"]
    used += selection["causal_source_items"] + selection["causal_eval_items"] + exposed
    pilot.require(
        len(symbols) == 55 and len(used) == 759, "Previous allocation counts changed"
    )
    pilot.require(
        len({r["codepoint"] for r in used}) == 759, "Previous allocation overlap"
    )
    return selection, symbols, used, source


def remaining_items(matched: list[dict], used: list[dict]) -> list[dict]:
    by_codepoint = {r["codepoint"]: r for r in matched}
    pilot.require(
        len(by_codepoint) == len(matched) == 954, "Matched emoji pool changed"
    )
    pilot.require(
        len({r["alias_label"] for r in matched}) == 954, "Duplicate matched aliases"
    )
    for row in used:
        actual = by_codepoint.get(row["codepoint"])
        pilot.require(
            actual is not None
            and all(
                actual[k] == row[k]
                for k in (
                    "alias_label",
                    "canonical_label",
                    "glyph",
                    "codepoint_literal",
                    "source_index",
                )
            ),
            "A previously used item has a different allocation",
        )
    used_codepoints = {r["codepoint"] for r in used}
    remaining = sorted(
        (r for r in matched if r["codepoint"] not in used_codepoints),
        key=lambda r: r["source_index"],
    )
    pilot.require(len(remaining) == 195, "Remaining population is not exactly 195")
    return [
        {**r, "bank_index": i, "bank_role": "t21_prospective_confirmation"}
        for i, r in enumerate(remaining)
    ]


def reconstruct_remaining(source_directory: Path) -> tuple[list[dict], dict]:
    """Minimal pure emoji replay; no Git archive or protected target content reads."""
    selection, symbols, used, _source = known_items()
    cfg = t19._config()
    binding = cfg["source_bindings"]["unicode_emoji_test"]
    raw = t19._verify_source(source_directory / "emoji-test.txt", binding)
    parsed = t19.t11._parse_unicode_source(raw)
    pilot.require(
        parsed["version"] == str(binding["version"]), "Unicode version changed"
    )
    pilot.require(
        len(parsed["fully_qualified"]) == binding["expected_fully_qualified_entries"],
        "Unicode entry count changed",
    )
    annotations = t19._cldr_annotations(source_directory)
    maximum = tuple(
        int(p) for p in str(cfg["population"]["maximum_emoji_version"]).split(".")
    )
    candidates, exclusions = [], Counter()
    for source_index, row in enumerate(parsed["fully_qualified"]):
        points = tuple(int(v) for v in row["codepoints"])
        if len(points) != 1:
            exclusions["not_one_codepoint"] += 1
            continue
        if tuple(int(p) for p in str(row["emoji_version"]).split(".")) > maximum:
            exclusions["newer_than_maximum_version"] += 1
            continue
        glyph = chr(points[0])
        annotation = annotations.get(glyph) or annotations.get(glyph + "\ufe0f")
        if annotation is None or not annotation.get("tts"):
            exclusions["missing_cldr_tts"] += 1
            continue
        canonical = str(annotation["tts"][0])
        pilot.require(canonical == str(row["name"]), "CLDR short name changed")
        aliases = t19._strict_aliases(canonical, annotation.get("default", []))
        if not aliases:
            exclusions["no_lexically_disjoint_keyword"] += 1
            continue
        candidates.append(
            {
                "kind": "emoji",
                "glyph_system": "emoji",
                "glyph": glyph,
                "codepoint": f"{points[0]:04X}",
                "codepoints": [f"U+{points[0]:04X}"],
                "codepoint_literal": f"U+{points[0]:04X}",
                "canonical_label": canonical,
                "alias_candidates": aliases,
                "semantic_stratum": str(row["group"]),
                "subgroup": str(row["subgroup"]),
                "emoji_version": str(row["emoji_version"]),
                "source_index": source_index,
            }
        )
    census = selection["candidate_census"]
    pilot.require(
        len(candidates) == census["emoji_before_matching"] == 1064,
        "Emoji candidate census changed",
    )
    pilot.require(
        dict(exclusions) == census["emoji_exclusions"], "Emoji exclusion census changed"
    )
    forbidden = {r["alias_label"] for r in symbols}
    pilot.require(len(forbidden) == 55, "Symbol alias count changed")
    matched = t19._maximum_alias_matching(candidates, forbidden_aliases=forbidden)
    remaining = remaining_items(matched, used)
    pilot.require(
        not {r["alias_label"] for r in matched} & forbidden,
        "Reserved symbol alias reused",
    )
    sources = {"emoji-test.txt": binding["sha256"]}
    for key in ("english_annotations", "english_derived_annotations"):
        item = cfg["source_bindings"]["cldr"][key]
        sources[item["filename"]] = item["sha256"]
    return remaining, {
        "public_source_sha256": sources,
        "candidate_emoji": 1064,
        "matched_emoji": 954,
        "reused_symbol_aliases": 55,
        "previous_emoji_allocations_verified": 759,
        "remaining_emoji": 195,
        "protected_target_content_reads": 0,
        "historical_text_rescan": False,
        "freshness_scope": "unused_in_prior_T19_T20_T21_model_evaluations_only",
    }


def audit_spec(path: Path) -> dict:
    spec = pilot.read_json(path)
    pilot.require(spec["protocol_id"] == PROTOCOL, "Specification protocol mismatch")
    design_path = ROOT / spec["design_path"]
    audit_design(design_path)
    pilot.require(pilot.sha256(design_path) == spec["design_sha256"], "Design changed")
    expected = 8 if spec["mode"] == "exposed_canary" else 195
    pilot.require(spec["mode"] in ("exposed_canary", "confirmation"), "Invalid mode")
    pilot.require(
        spec["target_count"]
        == len(spec["target_tokens"])
        == len(spec["donor_indices"])
        == expected,
        "Specification count mismatch",
    )
    pilot.require(
        spec["conditions"] == list(pilot.CONDITIONS) and spec["anchors"] == [21, 24],
        "Intervention order changed",
    )
    return spec


def verify_acquisition(root: Path, expected_mode: str) -> dict:
    receipt = pilot.read_json(root / "acquisition_receipt.json")
    spec = audit_spec(root / "specification.json")
    count = 8 if expected_mode == "exposed_canary" else 195
    pilot.require(
        receipt["status"] == "acquisition_complete"
        and receipt["mode"] == spec["mode"] == expected_mode,
        "Incomplete or wrong acquisition",
    )
    pilot.require(receipt["target_items"] == count, "Acquisition population changed")
    digest = pilot.sha256(root / "specification.json")
    pilot.require(
        receipt["specification_sha256"] == digest
        and receipt["stock_eager_adapter_exact"],
        "Specification or parity mismatch",
    )
    pilot.require(
        pilot.sha256(root / "source_states.npz") == receipt["source_states_sha256"],
        "Source states changed",
    )
    coverage = []
    for name, expected in receipt["chunks"].items():
        path = root / name
        pilot.require(
            pilot.sha256(path / "receipt.json") == expected, "Chunk receipt changed"
        )
        chunk = pilot.verify_chunk(path, digest)
        coverage.extend(range(chunk["start"], chunk["stop"]))
    pilot.require(
        sorted(coverage) == list(range(count)), "Missing or duplicate target chunks"
    )
    if expected_mode == "exposed_canary":
        pilot.require(
            receipt["original_pilot_canary_bit_exact"]
            and receipt["reserve_items_forwarded"] == 0,
            "Canary exact replay or reserve check failed",
        )
    return receipt


def prepare_confirmation(
    design_path: Path,
    source_directory: Path,
    model_path: Path,
    canary_root: Path,
    output: Path,
) -> dict:
    from transformers import AutoTokenizer
    from glyphprobe.provenance import model_artifact_receipt

    pilot.require(not output.exists(), "Confirmation specification already exists")
    require_published(design_path)
    spec = base_spec(design_path, "confirmation")
    canary = verify_acquisition(canary_root, "exposed_canary")
    pilot.require(
        pilot.read_json(canary_root / "specification.json")["design_sha256"]
        == spec["design_sha256"],
        "Canary design mismatch",
    )
    pilot.require(
        model_artifact_receipt(model_path) == spec["model_artifact"],
        "Model artifact changed",
    )
    # This is the first permitted reconstruction of the unused identities.
    targets, replay = reconstruct_remaining(source_directory)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    target_tokens = pilot.tokenize_rows(tokenizer, targets)
    _old, source = pilot.input_rows()
    source_tokens = pilot.tokenize_rows(tokenizer, source)
    pilot.require(source_tokens == spec["source_tokens"], "Source token plan changed")
    spec.update(
        {
            "target_count": 195,
            "target_items": targets,
            "target_tokens": target_tokens,
            "donor_indices": pilot.choose_donors(targets, target_tokens, source_tokens),
            "selection_replay": replay,
            "reserve_model_forwards_at_specification": 0,
            "canary_receipt_sha256": pilot.sha256(
                canary_root / "acquisition_receipt.json"
            ),
            "canary_completed_at_utc": canary["completed_at_utc"],
            "token_length_counts": dict(
                Counter(len(t["raw"]["glyph"]) for t in target_tokens)
            ),
        }
    )
    pilot.write_json(output, spec)
    return {
        "status": "confirmation_specified",
        "target_count": 195,
        "specification_sha256": pilot.sha256(output),
        "token_length_counts": spec["token_length_counts"],
        "selection_replay": replay,
        "reserve_model_forwards": 0,
    }


def resource_check(output: Path, boundary: str, started: float) -> None:
    pids = pilot.foreign_gpu_pids()
    expired = (
        time.perf_counter() - started > config()["execution"]["wall_budget_seconds"]
    )
    if pids or expired:
        pilot.write_json(
            output / f"yield_{uuid.uuid4().hex}.json",
            {
                "protocol_id": PROTOCOL,
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "wall_budget_reached": expired,
                "created_at_utc": pilot.now(),
            },
        )
        raise SystemExit(75)


def compare_canary(output: Path, original: Path) -> None:
    pilot.check_canary(original, config()["pilot"]["specification_sha256"])
    for name in ("source_states.npz", "chunk_0000_0008/states.npz"):
        with (
            np.load(output / name, allow_pickle=False) as a,
            np.load(original / name, allow_pickle=False) as b,
        ):
            pilot.require(
                set(a.files) == set(b.files), "Canary array inventory changed"
            )
            for key in a.files:
                pilot.require(
                    np.array_equal(a[key], b[key]),
                    "Canary differs from original pilot: " + key,
                )


def run(
    model_path: Path,
    spec_path: Path,
    output: Path,
    *,
    resume: bool = False,
    original_canary: Path | None = None,
) -> dict:
    spec = audit_spec(spec_path)
    require_published(ROOT / spec["design_path"])
    published_commit = require_published(spec_path)
    canary = spec["mode"] == "exposed_canary"
    pilot.require(
        not canary or original_canary is not None, "Canary reference required"
    )
    digest = pilot.sha256(spec_path)
    count = int(spec["target_count"])
    if output.exists():
        pilot.require(
            resume and not (output / "acquisition_receipt.json").exists(),
            "Completed/existing output cannot be overwritten",
        )
        pilot.require(
            pilot.sha256(output / "specification.json") == digest,
            "Resume specification mismatch",
        )
    else:
        output.mkdir(parents=True)
        with (output / "specification.json").open("xb") as f:
            f.write(spec_path.read_bytes())
    started = time.perf_counter()
    resource_check(output, "before_model_load", started)
    torch, model, model_receipt = pilot.load_model(model_path, spec)
    sample = torch.tensor(
        [spec["source_tokens"][0]["sequences"]["pipe"]["glyph"]],
        device="cuda",
        dtype=torch.long,
    )
    with torch.inference_mode():
        stock = (
            model.model(
                input_ids=sample,
                attention_mask=torch.ones_like(sample),
                use_cache=False,
                return_dict=True,
            )
            .last_hidden_state.detach()
            .clone()
        )
    controller = pilot.AttentionPath(model.model.layers)
    calls, sequences = 1, 1
    try:
        with torch.inference_mode():
            instrumented = model.model(
                input_ids=sample,
                attention_mask=torch.ones_like(sample),
                use_cache=False,
                return_dict=True,
            ).last_hidden_state
        calls += 1
        sequences += 1
        pilot.require(
            torch.equal(stock, instrumented), "Stock eager attention parity failed"
        )
        source_states = np.empty((128, 4, 3, 3072), np.float32)
        donor_cache = {}
        for i, tokens in enumerate(spec["source_tokens"]):
            resource_check(output, f"source_{i:03d}", started)
            for ci, carrier in enumerate(("pipe", "article_a")):
                for vi, view in enumerate(pilot.VIEWS):
                    final, _states, kv = pilot.capture(
                        torch, model, controller, tokens, carrier, view
                    )
                    source_states[i, ci * 2 : ci * 2 + 2, vi] = final
                    if view == "glyph":
                        donor_cache[i, carrier] = kv
                    calls += 1
                    sequences += 1
        source_path = output / "source_states.npz"
        if source_path.exists():
            receipt = pilot.read_json(output / "source_receipt.json")
            pilot.require(
                pilot.sha256(source_path) == receipt["states_sha256"],
                "Source replay bytes changed",
            )
            with np.load(source_path, allow_pickle=False) as f:
                pilot.require(
                    np.array_equal(f["states"], source_states),
                    "Source replay is not exact",
                )
        else:
            np.savez_compressed(source_path, states=source_states)
            pilot.write_json(
                output / "source_receipt.json",
                {
                    "specification_sha256": digest,
                    "states_sha256": pilot.sha256(source_path),
                    "source_items": 128,
                },
            )
        chunks = {}
        chunk_size = config()["execution"]["chunk_items"]
        for start in range(0, count, chunk_size):
            stop = min(start + chunk_size, count)
            destination = output / f"chunk_{start:04d}_{stop:04d}"
            if destination.exists():
                old = pilot.verify_chunk(destination, digest)
                pilot.require(
                    old["start"] == start and old["stop"] == stop,
                    "Resume chunk indices changed",
                )
                chunks[destination.name] = pilot.sha256(destination / "receipt.json")
                continue
            stage = output / f".chunk_{start:04d}_{stop:04d}.partial-{uuid.uuid4().hex}"
            stage.mkdir()
            baseline = np.empty((stop - start, 4, 3, 3072), np.float32)
            states = np.empty((stop - start, 4, 2, 2, 11, 3072), np.float32)
            neutral = np.empty_like(states)
            for i in range(start, stop):
                resource_check(output, f"target_{i:03d}", started)
                exposure = output / "exposure" / f"item_{i:03d}.json"
                if not exposure.exists():
                    pilot.write_json(
                        exposure,
                        {
                            "mode": spec["mode"],
                            "target_index": i,
                            "specification_sha256": digest,
                            "forward_started_at_utc": pilot.now(),
                        },
                    )
                tokens = spec["target_tokens"][i]
                for ci, carrier in enumerate(("pipe", "article_a")):
                    resets = None
                    for vi, view in enumerate(pilot.VIEWS):
                        final, capture_states, _kv = pilot.capture(
                            torch, model, controller, tokens, carrier, view
                        )
                        baseline[i - start, ci * 2 : ci * 2 + 2, vi] = final
                        if view == "codepoint_literal":
                            resets = capture_states
                        calls += 1
                        sequences += 1
                    pilot.require(resets is not None, "Missing reset state")
                    donors = [donor_cache[d, carrier] for d in spec["donor_indices"][i]]
                    actual, reference = pilot.patch_item(
                        torch, model, controller, tokens, carrier, resets, donors
                    )
                    states[i - start, ci * 2 : ci * 2 + 2] = actual
                    neutral[i - start, ci * 2 : ci * 2 + 2] = reference
                    calls += 2
                    sequences += 176
            np.savez_compressed(
                stage / "states.npz",
                baseline=baseline,
                intervention=states,
                neutral_reference=neutral,
                item_indices=np.arange(start, stop, dtype=np.int64),
            )
            pilot.write_json(
                stage / "receipt.json",
                {
                    "protocol_id": PROTOCOL,
                    "specification_sha256": digest,
                    "start": start,
                    "stop": stop,
                    "states_sha256": pilot.sha256(stage / "states.npz"),
                    "no_op_exact": True,
                    "roundtrip_exact": True,
                    "nonreadout_unchanged": True,
                    "nonreadout_scope": "local_attention_intervention_only_not_all_downstream_states",
                },
            )
            pilot.require(
                not destination.exists(), "Chunk target appeared concurrently"
            )
            stage.rename(destination)
            chunks[destination.name] = pilot.sha256(destination / "receipt.json")
            print(
                json.dumps(
                    {
                        "stage": spec["mode"],
                        "completed": stop,
                        "total": count,
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                    }
                ),
                flush=True,
            )
        if canary:
            compare_canary(output, original_canary)
        receipt = {
            "protocol_id": PROTOCOL,
            "status": "acquisition_complete",
            "mode": spec["mode"],
            "target_items": count,
            "source_items": 128,
            "reserve_items_forwarded": 0 if canary else count,
            "specification_sha256": digest,
            "published_commit_at_start": published_commit,
            "source_states_sha256": pilot.sha256(source_path),
            "chunks": chunks,
            "stock_eager_adapter_exact": True,
            "original_pilot_canary_bit_exact": True if canary else None,
            "offtarget_attention_checks": controller.offtarget_checks,
            "batched_forward_calls_this_invocation": calls,
            "sequence_forwards_this_invocation": sequences,
            "generation_calls": 0,
            "model": model_receipt,
            "elapsed_seconds_this_invocation": time.perf_counter() - started,
            "completed_at_utc": pilot.now(),
        }
        pilot.write_json(output / "acquisition_receipt.json", receipt)
        return {
            "status": "acquisition_complete",
            "mode": spec["mode"],
            "target_items": count,
            "receipt_sha256": pilot.sha256(output / "acquisition_receipt.json"),
        }
    finally:
        controller.close()
        del model
        torch.cuda.empty_cache()


def analyze(run_root: Path, output: Path) -> dict:
    pilot.require(not output.exists(), "Analysis already exists")
    acquisition = verify_acquisition(run_root, "confirmation")
    spec = audit_spec(run_root / "specification.json")
    with np.load(run_root / "source_states.npz", allow_pickle=False) as f:
        source = f["states"]
    metrics = {
        name: np.empty((195, 4, 2, 2, 11), np.float64) for name in pilot.ALL_METRICS
    }
    for name in sorted(acquisition["chunks"]):
        path = run_root / name
        receipt = pilot.verify_chunk(path, acquisition["specification_sha256"])
        start, stop = receipt["start"], receipt["stop"]
        with np.load(path / "states.npz", allow_pickle=False) as f:
            base, actual, reference = (
                f["baseline"],
                f["intervention"],
                f["neutral_reference"],
            )
            pilot.require(
                np.array_equal(f["item_indices"], np.arange(start, stop)),
                "Item index changed",
            )
        for ci in (0, 1, 9, 10):
            pilot.require(
                np.array_equal(actual[..., ci, :], reference[..., ci, :]),
                "Same-slot control failed",
            )
        for context in range(4):
            common = (
                base[:, context, 1],
                base[:, context, 2],
                source[:, context, 1],
                source[:, context, 2],
                np.asarray(spec["donor_indices"][start:stop]),
            )
            scores = pilot.score_states(actual[:, context], *common)
            neutral = pilot.score_states(reference[:, context], *common)
            for metric in pilot.METRICS:
                metrics[metric][start:stop, context] = scores[metric]
                metrics[metric + "_effect"][start:stop, context] = (
                    scores[metric] - neutral[metric]
                )
    x = stats.contrast_matrix(metrics["alias_margin_effect"])
    primary = stats.simultaneous_lower(x)
    calibration = primary["contrasts"]["calibration"]["directional_pass"]
    verdict = (
        "conditional_path_contribution_supported"
        if primary["all_five_positive"]
        else (
            "joint_path_claim_not_supported"
            if calibration
            else "calibration_unresolved"
        )
    )
    reference_mean = primary["contrasts"]["calibration"]["mean"]
    result = {
        "protocol_id": PROTOCOL,
        "status": "confirmation_analysis_complete",
        "verdict": verdict,
        "target_items": 195,
        "candidate_anchor": 21,
        "primary": primary,
        "mean_effect_relative_to_full_prefix_reference_descriptive": {
            name: row["mean"] / reference_mean if reference_mean > 0 else None
            for name, row in primary["contrasts"].items()
        },
        "secondary_endpoint_means": {
            name: dict(
                zip(
                    stats.NAMES,
                    stats.contrast_matrix(metrics[name]).mean(axis=0).tolist(),
                    strict=True,
                )
            )
            for name in (
                "alias_top1_effect",
                "donor_margin_effect",
                "codepoint_margin_effect",
                "codepoint_top1_effect",
            )
        },
        "secondary_carrier_means": {
            pilot.CONTEXTS[ci][0]: dict(
                zip(
                    stats.NAMES,
                    stats.contrast_matrix(
                        metrics["alias_margin_effect"], contexts=(ci,)
                    )
                    .mean(axis=0)
                    .tolist(),
                    strict=True,
                )
            )
            for ci in (1, 3)
        },
        "secondary_anchor24_means": dict(
            zip(
                stats.NAMES,
                stats.contrast_matrix(metrics["alias_margin_effect"], anchor=24)
                .mean(axis=0)
                .tolist(),
                strict=True,
            )
        ),
        "item_diagnostics_descriptive": stats.diagnostic_summary(x),
        "acquisition_receipt_sha256": pilot.sha256(
            run_root / "acquisition_receipt.json"
        ),
        "design_sha256": spec["design_sha256"],
        "claim_boundary": [
            "One-model conditional attention-message contribution to lexical cosine margin.",
            "This is not a positive result for the previous T19/T20 component-local gate.",
            "No emoji specificity, unique circuit, behavioral steering, or practical-effect-size claim.",
            "Bootstrap intervals are approximate and conditional on fixed source donors/gallery.",
        ],
    }
    conditions = []
    for ci, (carrier, distance) in enumerate(pilot.CONTEXTS):
        for ai, anchor in enumerate(pilot.ANCHORS):
            for ki, condition in enumerate(pilot.CONDITIONS):
                conditions.append(
                    {
                        "carrier": carrier,
                        "distance": distance,
                        "anchor": anchor,
                        "condition": condition,
                        **{
                            name: float(value[:, ci, ai, :, ki].mean())
                            for name, value in metrics.items()
                        },
                    }
                )
    output.mkdir(parents=True)
    np.savez_compressed(output / "item_metrics.npz", **metrics)
    pilot.write_json(output / "confirmation_result.json", result)
    pilot.write_json(
        output / "condition_means.json", {"protocol_id": PROTOCOL, "rows": conditions}
    )
    pilot.write_json(
        output / "analysis_receipt.json",
        {
            "protocol_id": PROTOCOL,
            "status": "analysis_complete",
            "acquisition_receipt_sha256": pilot.sha256(
                run_root / "acquisition_receipt.json"
            ),
            "specification_sha256": acquisition["specification_sha256"],
            "completed_at_utc": pilot.now(),
            "outputs": {
                name: pilot.sha256(output / name)
                for name in (
                    "item_metrics.npz",
                    "confirmation_result.json",
                    "condition_means.json",
                )
            },
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("specify")
    p.add_argument("--output", type=Path, default=ROOT / DESIGN)
    p = sub.add_parser("audit")
    p.add_argument("--design", type=Path, default=ROOT / DESIGN)
    for command in ("prepare-canary", "prepare-confirmation"):
        p = sub.add_parser(command)
        p.add_argument("--design", type=Path, default=ROOT / DESIGN)
        p.add_argument("--output", type=Path, required=True)
        if command == "prepare-confirmation":
            p.add_argument("--source-directory", type=Path, required=True)
            p.add_argument("--model-path", type=Path, required=True)
            p.add_argument("--canary-root", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--model-path", type=Path, required=True)
    p.add_argument("--specification", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--original-canary", type=Path)
    p.add_argument("--resume", action="store_true")
    p = sub.add_parser("analyze")
    p.add_argument("--run-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "specify":
        result = specify(args.output)
    elif args.command == "audit":
        result = audit_design(args.design)
        result = {
            "status": "pass",
            "design_sha256": pilot.sha256(args.design),
            "candidate_anchor": result["candidate_anchor"],
        }
    elif args.command == "prepare-canary":
        result = prepare_canary(args.design, args.output)
    elif args.command == "prepare-confirmation":
        result = prepare_confirmation(
            args.design,
            args.source_directory,
            args.model_path,
            args.canary_root,
            args.output,
        )
    elif args.command == "run":
        result = run(
            args.model_path,
            args.specification,
            args.output,
            resume=args.resume,
            original_canary=args.original_canary,
        )
    else:
        result = analyze(args.run_root, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
