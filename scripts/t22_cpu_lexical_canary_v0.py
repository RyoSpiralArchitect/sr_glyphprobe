#!/usr/bin/env python3
"""Frozen descriptive lexical scoring of the eight exposed CPU canary items.

Reuses immutable intervention readouts. Acquires only the original alias-token
gallery and own-alias baselines, with single-sequence eager BF16 forwards.
Never reads a target bank, tokenizes, selects items, or runs a hypothesis test.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import os

import numpy as np
import t22_kv_cpu_canary_v0 as cpu

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-t22-cpu-lexical-eight-descriptive-v0"
CANARY_SHA = "27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901"
OPS = ("none", "k", "v", "kv")
CARRIERS = ("pipe", "article_a")
POSITIONS = ("glyph", "suffix")
TEST = "tests/test_t22_cpu_lexical_canary_v0.py"
DOCS = ("docs/T22_CPU_LEXICAL_CANARY_V0.md", "docs/T22_CPU_LEXICAL_CANARY_V0.ja.md")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def now():
    return datetime.now(timezone.utc).isoformat()


def progress(stage, **values):
    print(json.dumps({"stage": stage, **values}, sort_keys=True), flush=True)


def source_hashes():
    paths = {*cpu.source_hashes(), "scripts/t22_cpu_lexical_canary_v0.py", TEST,
             "scripts/validate_t22_cpu_acquisition_v0.py", "src/glyphprobe/io.py", *DOCS}
    return {name: sha(ROOT / name) for name in sorted(paths)}


def check_sources(spec):
    require(source_hashes() == spec["source_sha256"], "Frozen source changed")
    require(sha(spec["validation_receipt"]) == spec["validation_receipt_sha256"],
            "Synthetic validation receipt changed")


def validate(output):
    """Execute the complete new suite and bind its actual result to sources."""
    require(not output.exists(), "Validation output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    before = source_hashes()
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    base = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", TEST]
    collected = subprocess.run([*base, "--collect-only"], cwd=ROOT, env=env,
                               capture_output=True, text=True, check=True)
    nodes = [line for line in collected.stdout.splitlines() if line.startswith(TEST + "::")]
    require(bool(nodes), "No tests collected")
    xml = output.with_suffix(".junit.xml")
    require(not xml.exists(), "JUnit output already exists")
    run = subprocess.run([*base, f"--junitxml={xml}"], cwd=ROOT, env=env,
                         capture_output=True, text=True)
    print(run.stdout, end="", flush=True)
    suites = ET.parse(xml).getroot().findall("testsuite")
    counts = {key: sum(int(s.get(key, 0)) for s in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    passed = (run.returncode == 0 and counts["tests"] == len(nodes)
              and counts["failures"] == counts["errors"] == counts["skipped"] == 0
              and before == source_hashes())
    receipt = {"protocol_id": PROTOCOL, "status": "pass" if passed else "fail",
               "created_at_utc": now(), "source_sha256": before,
               "counts": counts, "collected": len(nodes), "exit_code": run.returncode,
               "junit_sha256": sha(xml), "numpy": np.__version__,
               "real_model_forwards": 0, "protected_bank_reads": 0}
    write(output, receipt)
    require(passed, "Synthetic validation failed")
    return receipt


def check_alias_inputs(canary):
    require(canary["target_count"] == 8 and len(canary["source_tokens"]) == 128,
            "Exactly the fixed exposed eight and fixed 128 sources are required")
    all_rows = canary["target_tokens"] + canary["source_tokens"]
    require(len({tuple(row["raw"]["alias_label"]) for row in all_rows}) == 136,
            "Alias gallery has a duplicate or target overlap")
    for row in all_rows:
        for carrier in CARRIERS:
            ids, raw = row["sequences"][carrier]["alias_label"], row["raw"]["alias_label"]
            require(bool(raw) and ids[:len(raw)] == raw and len(ids) == len(raw) + 8,
                    "Alias inputs must retain the original eight-token carrier")
            require(all(type(i) is int and i >= 0 for i in ids), "Invalid alias token IDs")


def prepare(canary, validation, output):
    require(not output.exists(), "Output already exists; do not overwrite frozen work")
    checked = read(validation)
    require(checked["status"] == "pass" and checked["source_sha256"] == source_hashes()
            and checked["counts"]["tests"] > 0 and checked["counts"]["skipped"] == 0,
            "Current source-bound complete synthetic pass required")
    require(sha(canary / "acquisition_receipt.json") == CANARY_SHA, "Unexpected CPU canary")
    original = read(canary / "specification.json")
    check_alias_inputs(original)
    output.mkdir(parents=True)
    audit_path = output / "engineering_audit.json"
    command = [sys.executable, str(ROOT / "scripts/validate_t22_cpu_acquisition_v0.py"),
               "--repo", str(ROOT), "--run", str(canary), "--expected-items", "8",
               "--expected-acquisition-sha256", CANARY_SHA, "--output", str(audit_path)]
    with (output / "engineering_audit.log").open("xb") as stream:
        subprocess.run(command, cwd=ROOT, check=True, stdout=stream, stderr=subprocess.STDOUT)
    require(read(audit_path)["status"] == "pass", "Engineering audit did not pass")
    spec = {"protocol_id": PROTOCOL, "stage": "descriptive_eight_exposed_items",
            "created_at_utc": now(), "canary_run": str(canary.resolve()),
            "canary_acquisition_sha256": CANARY_SHA,
            "canary_specification_sha256": sha(canary / "specification.json"),
            "engineering_audit_sha256": sha(audit_path),
            "validation_receipt": str(validation.resolve()),
            "validation_receipt_sha256": sha(validation), "source_sha256": source_hashes(),
            "model_artifact": original["model_artifact"], "runtime": original["runtime"],
            "numpy": np.__version__, "target_tokens": original["target_tokens"],
            "source_tokens": original["source_tokens"], "donor_indices": original["donor_indices"],
            "carriers": list(CARRIERS), "operations": list(OPS), "positions": list(POSITIONS),
            "target_count": 8, "source_count": 128, "distance": 8, "anchor": 21,
            "active_blocks": list(range(22, 28)), "width": 3072,
            "alias_forward_batch": 1, "alias_readout": "final_hidden_after_final_norm_at_last_carrier_token",
            "normalization": "float64_l2", "gallery_columns": "own_then_original_128_sources",
            "tie_rule": "own_first_argmax", "effect": "active_minus_its_identical_slot_neutral",
            "adjusted_decrement": "mean_carrier_donor(effect_suffix_minus_effect_glyph)_within_item",
            "nonadditivity": "adjusted_KV_minus_K_minus_V",
            "uncertainty": "per_item_values_sample_sd_and_range_only_no_population_interval",
            "codepoint_gallery_acquired": False, "hypothesis_tests": False,
            "efficacy_screen": False, "confirmation": False,
            "select_384_exploration_by_canary_sign": False,
            "historical_gpu_replay": False, "protected_bank_reads": 0,
            "generation_calls": 0, "new_intervention_forwards": 0}
    write(output / "specification.json", spec)
    return {"status": "frozen", "specification_sha256": sha(output / "specification.json")}


def load_spec(output):
    spec = read(output / "specification.json")
    require(spec["protocol_id"] == PROTOCOL, "Protocol mismatch")
    check_sources(spec)
    require(np.__version__ == spec["numpy"], "NumPy runtime changed")
    parent = Path(spec["canary_run"])
    require(sha(parent / "acquisition_receipt.json") == spec["canary_acquisition_sha256"] == CANARY_SHA
            and sha(parent / "specification.json") == spec["canary_specification_sha256"],
            "Engineering parent changed")
    require(sha(output / "engineering_audit.json") == spec["engineering_audit_sha256"],
            "Engineering audit changed")
    return spec


def parent_arrays(spec, index):
    parent = Path(spec["canary_run"])
    acquisition = read(parent / "acquisition_receipt.json")
    item = parent / f"item_{index:04d}"
    require(sha(item / "receipt.json") == acquisition["chunks"][item.name], "Parent item receipt changed")
    receipt = read(item / "receipt.json")
    require(sha(item / "states.npz") == receipt["states_sha256"], "Parent raw arrays changed")
    return np.load(item / "states.npz", allow_pickle=False)


def acquire_alias_row(torch, model, tokens, expected_stock=None):
    """Single-sequence stock inference; optionally gate on complete prior glyph states."""
    vectors = []
    forwards = 0
    with torch.inference_mode():
        for carrier in CARRIERS:
            def forward(view):
                nonlocal forwards
                inputs = torch.tensor([tokens["sequences"][carrier][view]], dtype=torch.long, device="cpu")
                hidden = model.model(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                                     use_cache=False, return_dict=True).last_hidden_state
                require(bool(torch.isfinite(hidden).all()), "Nonfinite alias inference")
                forwards += 1
                return hidden[0].float().numpy().copy()
            if expected_stock is not None:
                require(np.array_equal(forward("glyph"), expected_stock[f"{carrier}_stock_hidden"]),
                        f"Full stock glyph replay differs for {carrier}")
            vectors.append(forward("alias_label")[-1])
    result = np.stack(vectors)
    normalize(result)
    return result, forwards


def verify_row(path, spec_hash, width, group, index):
    receipt = read(path / "receipt.json")
    require(receipt["specification_sha256"] == spec_hash and receipt["group"] == group
            and receipt["index"] == index and receipt["forward_calls"] == (4 if group == "target" else 2),
            "Alias row identity/count mismatch")
    require(receipt["stock_glyph_full_state_replayed"] is (group == "target"), "Missing stock replay gate")
    require(sha(path / "states.npz") == receipt["states_sha256"], "Alias row arrays changed")
    with np.load(path / "states.npz", allow_pickle=False) as saved:
        require(saved.files == ["alias"], "Unexpected alias array inventory")
        value = saved["alias"]
    require(value.shape == (2, width) and value.dtype == np.float32, "Alias shape/dtype mismatch")
    require(((value.view(np.uint32) & np.uint32(65535)) == 0).all(), "Non-BF16 alias values")
    normalize(value)
    return value, receipt


def acquire(model_path, output, resume=False):
    spec = load_spec(output)
    require(not (output / "acquisition_receipt.json").exists(), "Completed alias acquisition is immutable")
    chunks = output / "aliases"
    require(resume or not chunks.exists(), "Use explicit --resume for identical incomplete acquisition")
    chunks.mkdir(exist_ok=True)
    spec_hash = sha(output / "specification.json")
    existing = {}
    for group, count in (("target", 8), ("source", 128)):
        for index in range(count):
            path = chunks / f"{group}_{index:04d}"
            if path.exists():
                existing[group, index] = verify_row(path, spec_hash, spec["width"], group, index)
    import torch
    import transformers
    from transformers import AutoModelForCausalLM

    require(cpu._runtime(torch, transformers, 4) == spec["runtime"], "Exact CPU runtime differs from parent")
    progress("model_manifest", status="starting")
    require(cpu._validate_model_artifact(model_path, spec) == spec["model_artifact"], "Model pin differs")
    progress("model_manifest", status="complete")
    started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
        trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="eager").to("cpu").eval()
    require(type(model).__name__ == "LlamaForCausalLM" and cpu._model_dimensions(model) == cpu.MODEL_DIMENSIONS
            and sum(p.numel() for p in model.parameters()) == 3212749824
            and {p.dtype for p in model.parameters()} == {torch.bfloat16}, "Model architecture/dtype mismatch")
    receipts, arrays = {}, {}
    new_calls, logical_calls = 0, 0
    try:
        for group, count in (("target", 8), ("source", 128)):
            rows = []
            for index, tokens in enumerate(spec[group + "_tokens"]):
                check_sources(spec)
                path = chunks / f"{group}_{index:04d}"
                if (group, index) in existing:
                    value, receipt = existing[group, index]
                else:
                    before = time.perf_counter()
                    if group == "target":
                        with parent_arrays(spec, index) as parent:
                            value, calls = acquire_alias_row(torch, model, tokens, parent)
                    else:
                        value, calls = acquire_alias_row(torch, model, tokens)
                    new_calls += calls
                    partial = chunks / f".{path.name}.partial-{uuid.uuid4().hex}"
                    partial.mkdir()
                    np.savez_compressed(partial / "states.npz", alias=value)
                    receipt = {"specification_sha256": spec_hash, "group": group, "index": index,
                               "states_sha256": sha(partial / "states.npz"), "forward_calls": calls,
                               "stock_glyph_full_state_replayed": group == "target",
                               "elapsed_seconds": time.perf_counter() - before, "completed_at_utc": now()}
                    write(partial / "receipt.json", receipt)
                    verify_row(partial, spec_hash, spec["width"], group, index)
                    require(not path.exists(), "Alias destination appeared concurrently")
                    partial.rename(path)
                receipts[path.name] = sha(path / "receipt.json")
                logical_calls += receipt["forward_calls"]
                rows.append(value)
                progress("aliases", group=group, completed=index + 1, total=count,
                         elapsed_seconds=time.perf_counter() - started)
            arrays[group + "_alias"] = np.stack(rows)
        check_sources(spec)
        cpu._validate_model_artifact(model_path, spec)
        check_sources(spec)
        require(logical_calls == 288 and len(receipts) == 136, "Incomplete alias acquisition counts")
        np.savez_compressed(output / "gallery.npz", **arrays)
        receipt = {"protocol_id": PROTOCOL, "status": "alias_acquisition_complete",
                   "specification_sha256": spec_hash, "chunks": receipts,
                   "gallery_sha256": sha(output / "gallery.npz"), "forward_calls_total": logical_calls,
                   "forward_calls_this_invocation": new_calls,
                   "stock_glyph_full_state_replays": 16,
                   "elapsed_seconds_after_manifest_this_invocation": time.perf_counter() - started,
                   "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                   "completed_at_utc": now(), "protected_bank_reads": 0,
                   "generation_calls": 0, "new_intervention_forwards": 0}
        write(output / "acquisition_receipt.json", receipt)
        return receipt
    finally:
        del model


def normalize(value):
    value = np.asarray(value, dtype=np.float64)
    norms = np.linalg.norm(value, axis=-1, keepdims=True)
    require(np.isfinite(value).all() and (norms > 1e-12).all(), "Invalid cosine vector")
    return value / norms


def score_rows(states, own, sources, donors):
    """One own-first 129-column matrix product, as in the historical metric."""
    require(states.shape[0] == 16 and sources.shape == (128, states.shape[-1])
            and own.shape == (states.shape[-1],), "Scoring geometry mismatch")
    require(len(donors) == 2 and all(type(d) is int and 0 <= d < 128 for d in donors),
            "Invalid fixed donor slots")
    gallery = normalize(np.concatenate((own[None], sources)))
    scores = normalize(states) @ gallery.T
    own_score, competitor = scores[:, 0], scores[:, 1:].max(axis=-1)
    donor_score = scores[np.arange(16), np.tile(np.asarray(donors), 8) + 1]
    return {"scores": scores, "own_cosine": own_score, "competitor_cosine": competitor,
            "competitor_index": scores[:, 1:].argmax(axis=-1),
            "donor_cosine": donor_score, "alias_margin": own_score - competitor,
            "donor_margin": own_score - donor_score,
            "alias_top1": (scores.argmax(axis=-1) == 0).astype(np.float64),
            "own_rank": 1 + (scores[:, 1:] > own_score[:, None]).sum(axis=-1)}


def item_contrasts(active, neutral):
    """Input [item,carrier,16]; subtract same slots before averaging contexts."""
    require(active.shape == neutral.shape and active.ndim == 3 and active.shape[1:] == (2, 16),
            "Contrast geometry mismatch")
    effect = (active - neutral).reshape(len(active), 2, 4, 2, 2)
    return {"same_slot_effect": effect,
            "position_adjusted_by_carrier_donor": effect[:, :, :, 1] - effect[:, :, :, 0],
            "adjusted_per_item": (effect[:, :, :, 1] - effect[:, :, :, 0]).mean(axis=(1, 3)),
            "absolute_glyph_decrement_per_item": -effect[:, :, :, 0].mean(axis=(1, 3))}


def describe(values):
    values = np.asarray(values, dtype=np.float64)
    require(values.ndim == 1 and len(values) == 8 and np.isfinite(values).all(), "Exactly eight item values required")
    return {"n_items": 8, "mean": float(values.mean()), "median": float(np.median(values)),
            "sample_sd": float(values.std(ddof=1)), "min": float(values.min()), "max": float(values.max())}


def analyze(acquisition_root, output):
    require(not output.exists(), "Analysis output already exists")
    spec = load_spec(acquisition_root)
    acq = read(acquisition_root / "acquisition_receipt.json")
    spec_hash = sha(acquisition_root / "specification.json")
    require(acq["status"] == "alias_acquisition_complete" and acq["specification_sha256"] == spec_hash,
            "Completed alias acquisition required")
    require(sha(acquisition_root / "gallery.npz") == acq["gallery_sha256"], "Gallery changed")
    require(set(acq["chunks"]) == {f"{group}_{i:04d}" for group, n in (("source", 128), ("target", 8)) for i in range(n)},
            "Incomplete alias inventory")
    with np.load(acquisition_root / "gallery.npz", allow_pickle=False) as gallery:
        require(set(gallery.files) == {"source_alias", "target_alias"}, "Unexpected gallery arrays")
        source, targets = gallery["source_alias"], gallery["target_alias"]
    require(source.shape == (128, 2, spec["width"]) and targets.shape == (8, 2, spec["width"]), "Gallery geometry changed")
    for group, values in (("source", source), ("target", targets)):
        for i, expected in enumerate(values):
            path = acquisition_root / "aliases" / f"{group}_{i:04d}"
            require(sha(path / "receipt.json") == acq["chunks"][path.name], "Alias receipt changed")
            value, _ = verify_row(path, spec_hash, spec["width"], group, i)
            require(np.array_equal(value, expected), "Gallery differs from bound row arrays")
    metrics = {}
    attention = []
    csv_rows = []
    for i in range(8):
        with parent_arrays(spec, i) as parent:
            for c, carrier in enumerate(CARRIERS):
                for n, label in enumerate(("extension", "extension_neutral")):
                    result = score_rows(parent[f"{carrier}_{label}"], targets[i, c], source[:, c], spec["donor_indices"][i])
                    for name, values in result.items():
                        if name not in metrics:
                            metrics[name] = np.empty((8, 2, 2, *values.shape), dtype=values.dtype)
                        metrics[name][i, c, n] = values
                    for row in range(16):
                        operation, position, donor = row // 4, (row // 2) % 2, row % 2
                        csv_rows.append({"item": i, "carrier": carrier, "neutral": bool(n),
                            "operation": OPS[operation], "position": POSITIONS[position], "donor_slot": donor,
                            **{name: float(value[row]) if value.dtype.kind == "f" else int(value[row])
                               for name, value in result.items() if name != "scores"}})
                weights = parent[f"{carrier}_attention_weights"]
                baseline = parent[f"{carrier}_attention_baseline_weights"]
                for operation, op in enumerate(OPS):
                    for position, pos in enumerate(POSITIONS):
                        rows = slice(operation * 4 + position * 2, operation * 4 + position * 2 + 2)
                        local_difference = np.abs(weights[0, :, rows] - baseline[0, :, rows]).max()
                        if op in ("none", "v"):
                            require(local_difference == 0, "Local V/reference routing invariant failed")
                        attention.append({"item": i, "carrier": carrier, "operation": op, "position": pos,
                            "local_max_abs_weight_difference": float(local_difference),
                            "active_minus_neutral_headmean_l1_by_block": np.abs(
                                weights[0, :, rows] - weights[1, :, rows]).sum(axis=-1).mean(axis=(1, 2)).tolist(),
                            **{mass + "_mass_active_minus_neutral_by_block": (
                                parent[f"{carrier}_attention_{mass}_mass"][0, :, rows]
                                - parent[f"{carrier}_attention_{mass}_mass"][1, :, rows]).mean(axis=(1, 2)).tolist()
                               for mass in ("glyph", "suffix")}})
    contrasts = {name: item_contrasts(value[:, :, 0], value[:, :, 1]) for name, value in metrics.items()
                 if name not in ("scores", "competitor_index", "own_rank")}
    primary = contrasts["alias_margin"]["adjusted_per_item"]
    require(np.array_equal(contrasts["alias_margin"]["same_slot_effect"][:, :, 0], np.zeros((8, 2, 2, 2))),
            "Reference operation has nonzero effect")
    error = float(np.max(np.abs(primary - (contrasts["own_cosine"]["adjusted_per_item"]
                                          - contrasts["competitor_cosine"]["adjusted_per_item"]))))
    require(error < 1e-12, "Own/competitor decomposition failed")
    nonadditivity = primary[:, 3] - primary[:, 1] - primary[:, 2]
    summary = {op: {name: describe(value["adjusted_per_item"][:, j]) for name, value in contrasts.items()}
               for j, op in enumerate(OPS)}
    absolute = {op: describe(contrasts["alias_margin"]["absolute_glyph_decrement_per_item"][:, j])
                for j, op in enumerate(OPS)}
    output.mkdir(parents=True)
    saved = {**metrics, "adjusted_margin_per_item": primary, "nonadditivity_per_item": nonadditivity}
    for name, values in contrasts.items():
        for key, value in values.items():
            saved[f"{name}_{key}"] = value
    np.savez_compressed(output / "metrics.npz", **saved)
    with (output / "rows.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=csv_rows[0].keys())
        writer.writeheader()
        writer.writerows(csv_rows)
    write(output / "attention_diagnostics.json", {"blocks": list(range(22, 28)), "rows": attention,
        "boundary": "V preserves local weights at each layer's own input; downstream queries can differ from neutral."})
    result = {"protocol_id": PROTOCOL, "status": "descriptive_analysis_complete", "completed_at_utc": now(),
              "specification_sha256": spec_hash, "alias_acquisition_sha256": sha(acquisition_root / "acquisition_receipt.json"),
              "canary_acquisition_sha256": CANARY_SHA, "source_sha256": source_hashes(),
              "primary_position_adjusted_decrement": summary, "absolute_glyph_margin_decrement": absolute,
              "nonadditivity": describe(nonadditivity), "max_decomposition_error": error,
              "itemwise_adjusted_margin": primary.tolist(), "itemwise_nonadditivity": nonadditivity.tolist(),
              "artifacts_sha256": {p.name: sha(p) for p in output.iterdir()},
              "target_items": 8, "carriers_per_item": 2, "donors_per_item": 2,
              "gallery_sources": 128, "scored_rows": 512, "hypothesis_tests": False,
              "efficacy_screen": False, "confirmation": False, "historical_gpu_replay": False,
              "protected_bank_reads": 0, "analysis_model_forwards": 0,
              "boundary": "Descriptive exposed-eight comparison; no population inference or semantic-mechanism conclusion. Codepoint gallery metrics and 384-item exploration are unrun. Exploration is not selected by these signs."}
    table = ["# T22 exposed-eight CPU lexical comparison", "", "Descriptive means; no population intervals or significance tests.", "",
             "| Operation | Adjusted margin decrement | Absolute glyph margin decrement | Adjusted own cosine | Adjusted max-competitor cosine |",
             "|---|---:|---:|---:|---:|"]
    for op in OPS:
        row = summary[op]
        table.append(f"| {op} | {row['alias_margin']['mean']:.9g} | {absolute[op]['mean']:.9g} | {row['own_cosine']['mean']:.9g} | {row['competitor_cosine']['mean']:.9g} |")
    table += ["", f"KV - K - V adjusted margin: {result['nonadditivity']['mean']:.9g}", "", result["boundary"], ""]
    (output / "report.md").write_text("\n".join(table), encoding="utf-8")
    result["artifacts_sha256"]["report.md"] = sha(output / "report.md")
    write(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate")
    check.add_argument("--output", type=Path, required=True)
    freeze = sub.add_parser("prepare")
    freeze.add_argument("--canary", type=Path, required=True)
    freeze.add_argument("--validation", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--model-path", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    score = sub.add_parser("analyze")
    score.add_argument("--acquisition", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate(args.output)
    elif args.command == "prepare":
        result = prepare(args.canary.resolve(), args.validation.resolve(), args.output.resolve())
    elif args.command == "run":
        result = acquire(args.model_path.resolve(), args.output.resolve(), args.resume)
    else:
        result = analyze(args.acquisition.resolve(), args.output.resolve())
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
