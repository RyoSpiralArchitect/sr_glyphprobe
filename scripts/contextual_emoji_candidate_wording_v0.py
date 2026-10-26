#!/usr/bin/env python3
"""Bounded candidate-wording sensitivity: design first, 768 new scores only.

Plan uses only local text/receipts, not a tokenizer/model. Run requires bounded
CUDA weight staging and exact parity on 384 historical crossed cells first.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
helper_spec = importlib.util.spec_from_file_location("wording_helpers", ROOT / "scripts/contextual_emoji_word_control_v0.py")
word = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(word)
shared_spec = importlib.util.spec_from_file_location("wording_shared_cuda", ROOT / "scripts/glyphprobe_shared_cuda_v0.py")
shared = importlib.util.module_from_spec(shared_spec)
shared_spec.loader.exec_module(shared)
base = word.baseline
require, sha256, read, write = base.require, base.sha256, base.json_read, base.json_write
PROTOCOL = "glyphprobe-contextual-emoji-candidate-wording-v0"
PAIRS = ("original", "explicit_negation", "adjective_pair")
CARRIERS = ("emoji", "word")
PANEL_SHA = "480d236a87e40e20a4ea339e0514c2a06a0707ec248413ca0260e56868a52730"
REFERENCE_SHA = {
    "emoji_spec": "04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5",
    "emoji_cells": "ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97",
    "word_spec": "ba8eabb588d48eca68041f475440e64b3f6e0db1fa6ab4f5aa56ee7083b0c519",
    "word_cells": "1026d3001ad4390662bfec608cfeca28d1610f7ba7117b6401494d8fa929ad91",
    "runtime": "952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323",
    "baseline_helper": "ccce1d18b701708506b61fa20cc1724fed3dd4c44ebfcecde66b20c635944daa",
    "word_helper": "1589c0452e127b08d824604a139bab408e1dec87cff0a577d4578bb6d5aecfd4",
}


def load_design(config_path):
    cfg = read(config_path)
    require(cfg.get("protocol_id") == PROTOCOL, "Protocol mismatch")
    require(cfg["inputs"]["sha256"] == word.INPUT_SHA and cfg["candidate_panel"]["sha256"] == PANEL_SHA,
            "Fixed input/panel identity required")
    require(cfg["model_artifact_manifest_sha256"] == word.MODEL_SHA, "Same model required")
    shared.validate_policy(cfg["compute_policy"])
    for key, expected in base.SCORE_RULE.items():
        require(cfg["scoring"].get(key) == expected, f"Unsupported scoring: {key}")
    require(cfg["scoring"]["J_total"] == 3 and cfg["scoring"]["new_pair_ids"] == list(PAIRS[1:])
            and cfg["scoring"]["carrier_kinds"] == list(CARRIERS) and cfg["scoring"]["reuse_original"] is True,
            "Fixed three-pair, two-carrier design required")
    for key, value in {"max_sequences": 768, "new_candidate_sequence_cells": 768,
                       "reused_candidate_sequence_cells": 384, "planned_blocks": 24,
                       "planned_families": 6, "total_crossed_sequence_scores": 1152,
                       "generation_calls": 0, "training_steps": 0, "intervention_cells": 0,
                       "new_absent_cells": 0, "new_parity_forward_cells": 384,
                       "max_total_model_forward_attempts": 1152}.items():
        require(type(cfg["budget"].get(key)) is int and cfg["budget"][key] == value, f"Fixed budget required: {key}")
    for key, upper in (("max_input_tokens", 96), ("max_candidate_tokens", 64), ("walltime_seconds", 900)):
        require(type(cfg["budget"].get(key)) is int and 0 < cfg["budget"][key] <= upper, f"Invalid bound: {key}")
    files = {"runner": {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))},
             "config": {"path": str(config_path.resolve()), "sha256": sha256(config_path)}}
    for key, pin in {"inputs": word.INPUT_SHA, "candidate_panel": PANEL_SHA, **REFERENCE_SHA}.items():
        entry = cfg[key] if key in ("inputs", "candidate_panel") else cfg["references"][key]
        path = base.safe_path(ROOT / entry["path"])
        require(entry["sha256"] == pin and sha256(path) == pin, f"Bound file changed: {key}")
        files[key] = {"path": str(path), "sha256": pin}
    for name, relative in (("model_provenance", "src/glyphprobe/provenance.py"), ("io", "src/glyphprobe/io.py"),
                           ("shared_cuda", "scripts/glyphprobe_shared_cuda_v0.py"),
                           ("analyzer", "scripts/summarize_contextual_emoji_candidate_wording_v0.py")):
        files[name] = {"path": str(ROOT / relative), "sha256": sha256(ROOT / relative)}
    blocks = base.load_blocks(Path(files["inputs"]["path"]), 24)
    old = read(Path(files["emoji_spec"]["path"]))
    control = read(Path(files["word_spec"]["path"]))
    require(blocks == old["blocks"] == control["blocks"], "Historical blocks changed")
    require(old["model_artifact"] == control["model_artifact"] and
            old["model_artifact"]["manifest_sha256"] == word.MODEL_SHA, "Historical model mismatch")
    require(old["runtime_packages"] == control["runtime_packages"] and
            old["python_version"] == control["python_version"], "Historical runtime mismatch")
    panel = read(Path(files["candidate_panel"]["path"]))
    require([p["pair_id"] for p in panel["additional_pairs"]] == list(PAIRS[1:]), "Candidate IDs changed")
    require(panel["status"] == "author_defined_development_not_human_validated", "Candidate claim changed")
    for pair in panel["additional_pairs"]:
        require(pair["positive"] != pair["negative"] and all(isinstance(pair[k], str) and
                pair[k].startswith(" ") and pair[k].endswith(".") for k in ("positive", "negative")),
                "Nonempty literal candidate strings required")
    return cfg, blocks, panel, files, old


def candidates(block, panel, pair_id):
    if pair_id == "original":
        return {"a": block["candidate_a"], "b": block["candidate_b"]}
    pair = next(p for p in panel["additional_pairs"] if p["pair_id"] == pair_id)
    return {"a": pair["positive"] if block["eta"] == 1 else pair["negative"],
            "b": pair["negative"] if block["eta"] == 1 else pair["positive"]}


def cells_for(blocks, panel, pair_ids=PAIRS[1:]):
    cells = []
    for pair_id in pair_ids:
        for block in blocks:
            choices = candidates(block, panel, pair_id)
            for context in ("p", "q"):
                template = block[f"context_{context}"]
                require(template.count("{emoji}") == 1, "Invalid original carrier slot")
                start = template.index("{emoji}")
                for carrier in CARRIERS:
                    for variant in ("a", "b"):
                        label = block["orientation"][f"context_{context}"][f"emoji_{variant}"]
                        sign = block["eta"] * (1 if (context, variant) in (("p", "a"), ("q", "b")) else -1)
                        require(label == ("a" if sign > 0 else "b"), "Original orientation and eta disagree")
                        cue = block[f"emoji_{variant}"] if carrier == "emoji" else block["planned_word_alternatives"][variant]
                        for candidate in ("a", "b"):
                            old_id = f"{block['block_id']}:{context}:{variant}:{candidate}"
                            cells.append({"cell_id": f"{pair_id}:{carrier}:{old_id}", "baseline_cell_id": old_id,
                                "pair_id": pair_id, "carrier_kind": carrier, "block_id": block["block_id"],
                                "family": block["family"], "context": context, "variant": variant,
                                "candidate": candidate, "eta": block["eta"], "prompt": template.replace("{emoji}", cue),
                                "continuation": choices[candidate], "carrier_surface": cue,
                                "carrier_char_start": start, "carrier_char_end": start + len(cue), "status": "planned"})
    require(len(cells) == len({c["cell_id"] for c in cells}), "Duplicate planned cells")
    return cells


def design(config_path):
    cfg, blocks, panel, files, old = load_design(config_path)
    cells = cells_for(blocks, panel)
    require(len(cells) == 768, "Expected 768 new cells")
    return {"protocol_id": PROTOCOL, "schema_version": 1,
        "status": "local_design_only_tokenizer_and_compute_preflight_pending",
        "created_at_utc": base.now(), "config": cfg, "blocks": blocks, "candidate_panel": panel,
        "source_files": files, "cells": cells, "claim_ceiling": base.CLAIM_CEILING,
        "confirmatory": False, "model_forwards": 0, "tokenizer_loaded": False, "model_loaded": False,
        "intervention_executed": False, "generation_calls": 0,
        "baseline_runtime_packages": old["runtime_packages"], "baseline_python_version": old["python_version"],
        "denominator": {"new_cells_planned": 768, "new_cells_completed": 0, "new_cells_not_run": 768,
                        "reused_crossed_cells": 384, "planned_blocks": 24, "candidate_pairs_total": 3},
        "execution_ready": False}


def token_diagnostics(cells):
    rows = []
    for pair_id in PAIRS[1:]:
        for carrier in CARRIERS:
            group = [c for c in cells if c["pair_id"] == pair_id and c["carrier_kind"] == carrier]
            rows.extend({**r, "pair_id": pair_id, "carrier_kind": carrier} for r in base.token_diagnostics(group))
    return rows


def parity_cells(spec):
    """Re-execute original scores only for engineering parity, not new evidence."""
    lookup = {}
    for carrier in CARRIERS:
        path = Path(spec["source_files"][f"{carrier}_cells"]["path"])
        require(sha256(path) == REFERENCE_SHA[f"{carrier}_cells"], "Historical raw scores changed")
        for line in path.read_text(encoding="utf-8").splitlines():
            old = json.loads(line)
            if old["variant"] in ("a", "b"):
                key = carrier, old["cell_id"]
                require(key not in lookup and old["status"] == "completed", "Historical score grid changed")
                lookup[key] = old
    result = cells_for(spec["blocks"], spec["candidate_panel"], ("original",))
    require(len(result) == len(lookup) == 384, "384 parity cells required")
    for cell in result:
        old = lookup[(cell["carrier_kind"], cell["baseline_cell_id"])]
        require(all(cell[k] == old[k] for k in ("prompt", "continuation", "eta")), "Parity stimulus changed")
        for key in ("prompt_token_ids", "candidate_token_ids", "input_token_ids", "prompt_token_count", "candidate_token_count"):
            cell[key] = old[key]
        require(cell["input_token_ids"] == cell["prompt_token_ids"] + cell["candidate_token_ids"], "Parity token boundary changed")
        require(len(cell["input_token_ids"]) <= spec["config"]["budget"]["max_input_tokens"], "Parity token budget exceeded")
        cell.update(status="ready", reference_logprobs=old["candidate_token_logprobs"],
                    reference_sum=old["sequence_logprob_sum"])
    return result


def prepare(config_path, model_path, output):
    require(not output.exists(), "Specification already exists")
    spec = design(config_path)
    spec["preparation_occupancy"] = shared.guard(spec["config"]["compute_policy"], before_allocation=True)
    require(base.package_versions() == spec["baseline_runtime_packages"] and
            platform.python_version() == spec["baseline_python_version"], "Original runtime required")
    artifact = base.artifact_receipt(model_path)
    require(artifact["manifest_sha256"] == word.MODEL_SHA, "Existing model artifact mismatch")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False, use_fast=True)
    spec["cells"] = [word.encode_cell(tokenizer, c, spec["config"]["budget"]) for c in spec["cells"]]
    for cell in parity_cells(spec):
        require(tokenizer.encode(cell["prompt"] + cell["continuation"], add_special_tokens=False)
                == cell["input_token_ids"], "Historical parity token IDs changed")
    spec.update(status="tokenized_preflight_zero_model_forwards", tokenizer_loaded=True,
                model_path=str(model_path.resolve()), model_artifact=artifact,
                tokenizer_class=type(tokenizer).__name__, tokenizer_vocab_size=len(tokenizer),
                candidate_token_diagnostics=token_diagnostics(spec["cells"]),
                preflight_counts=dict(Counter(c["status"] for c in spec["cells"])))
    spec["execution_ready"] = False  # Occupancy, retokenization, and model-load gates remain live requirements.
    write(output, spec)
    return {"status": spec["status"], "specification_sha256": sha256(output), "preflight_counts": spec["preflight_counts"], "model_forwards": 0}


def verify_spec(path):
    spec = read(path)
    require(spec["protocol_id"] == PROTOCOL and spec["status"] == "tokenized_preflight_zero_model_forwards", "Tokenized specification required")
    require(spec["confirmatory"] is False and spec["claim_ceiling"] == base.CLAIM_CEILING
            and spec["model_forwards"] == 0 and spec["intervention_executed"] is False, "Claim boundary changed")
    for key, record in spec["source_files"].items():
        require(sha256(Path(record["path"])) == record["sha256"], f"Bound file changed: {key}")
    current = design(Path(spec["source_files"]["config"]["path"]))
    for key in ("config", "blocks", "candidate_panel", "source_files", "baseline_runtime_packages", "baseline_python_version", "denominator"):
        require(spec[key] == current[key], f"Specification changed: {key}")
    original = read(Path(spec["source_files"]["emoji_spec"]["path"]))
    require(spec["model_artifact"] == original["model_artifact"], "Model artifact identity changed")
    require(spec["tokenizer_class"] == original["tokenizer_class"] and
            spec["tokenizer_vocab_size"] == original["tokenizer_vocab_size"], "Tokenizer identity changed")
    require(len(spec["cells"]) == 768, "Missing planned cells")
    for expected, actual in zip(current["cells"], spec["cells"], strict=True):
        require(all(actual.get(k) == v for k, v in expected.items() if k != "status"), "Planned cell changed")
        require(actual["status"] in ("ready", "failed_preflight"), "Invalid preflight status")
        if actual["status"] == "ready":
            p, c, full = actual["prompt_token_ids"], actual["candidate_token_ids"], actual["input_token_ids"]
            require(p and c and full == p + c and all(type(x) is int and x >= 0 for x in full), "Invalid exact-prefix tokens")
            require(actual["prompt_token_count"] == len(p) and actual["candidate_token_count"] == len(c), "Token count changed")
            require(len(full) <= spec["config"]["budget"]["max_input_tokens"] and
                    len(c) <= spec["config"]["budget"]["max_candidate_tokens"], "Token budget exceeded")
    require(spec["preflight_counts"] == dict(Counter(c["status"] for c in spec["cells"])), "Preflight counts changed")
    return spec


def verify_core_runtime(current, previous):
    """Compare the complete saved representation, including JSON object keys.

Transformers id2label uses integer keys in memory and string keys on disk.
No runtime field is excluded; changed values still fail closed.
"""
    serialized = json.loads(json.dumps(current, ensure_ascii=False, allow_nan=False))
    changed = sorted(k for k in set(serialized) | set(previous) if serialized.get(k) != previous.get(k))
    require(serialized == previous, f"Core runtime identity differs from original acquisition: {changed}")
    return serialized


def load_model(spec):
    policy = spec["config"]["compute_policy"]
    shared.guard(policy, before_allocation=True)
    require(base.package_versions() == spec["baseline_runtime_packages"] and
            platform.python_version() == spec["baseline_python_version"], "Runtime changed")
    path = Path(spec["model_path"])
    require(base.artifact_receipt(path) == spec["model_artifact"], "Model files changed")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "BF16 CUDA required")
    tok = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
    encoded = [word.encode_cell(tok, c, spec["config"]["budget"]) for c in cells_for(spec["blocks"], spec["candidate_panel"])]
    require(encoded == spec["cells"] and token_diagnostics(encoded) == spec["candidate_token_diagnostics"], "Tokenization changed")
    old = read(Path(spec["source_files"]["emoji_spec"]["path"]))
    require(type(tok).__name__ == old["tokenizer_class"] and len(tok) == old["tokenizer_vocab_size"], "Tokenizer identity changed")
    shared.guard(policy, before_allocation=True)
    torch.set_num_threads(4)
    torch.manual_seed(2026100701)
    model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, trust_remote_code=False,
                dtype=torch.bfloat16, attn_implementation="eager").eval()
    require({p.dtype for p in model.parameters()} == {torch.bfloat16}, "Unexpected parameter dtype")
    runtime = {"python": sys.version, "platform": platform.platform(), "packages": base.package_versions(),
        "torch": torch.__version__, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
        "device": torch.cuda.get_device_name(0), "device_capability": list(torch.cuda.get_device_capability(0)),
        "model_class": type(model).__name__, "model_config": model.config.to_dict(),
        "parameters": sum(p.numel() for p in model.parameters()), "dtype": "bfloat16", "attention": "eager", "use_cache": False,
        "model_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model).forward).encode()).hexdigest(),
        "attention_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model.model.layers[0].self_attn).forward).encode()).hexdigest(),
        "local_files_only": True, "trust_remote_code": False, "download": False, "generation_calls": 0, "route_instrumented": False}
    previous_runtime = read(Path(spec["source_files"]["runtime"]["path"]))
    runtime = verify_core_runtime(runtime, previous_runtime)
    stager = shared.DecoderWeightStager(model, torch, policy)
    return torch, model, runtime, stager


def run(spec_path, output):
    spec = verify_spec(spec_path)
    require(not output.exists(), "Run output exists; no overwrite or implicit resume")
    output.mkdir(parents=True)
    write(output / "specification.json", spec)
    start = {"protocol_id": PROTOCOL, "status": "started", "started_at_utc": base.now(),
        "specification_sha256": sha256(spec_path), "local_specification_sha256": sha256(output / "specification.json"),
        "planned_cells": 768, "reused_crossed_cells": 384, "planned_blocks": 24,
        "planned_parity_cells": 384, "maximum_total_forward_attempts": 1152,
        "claim_ceiling": base.CLAIM_CEILING, "confirmatory": False, "generation_calls": 0, "intervention_executed": False}
    write(output / "run_started.json", start)
    error, guards, stager = None, [], None
    actual_forwards = {"parity": 0, "candidate": 0}
    policy = spec["config"]["compute_policy"]
    parity = parity_cells(spec)
    started = time.monotonic()
    try:
        guards.append(shared.guard(policy, before_allocation=True))
        torch, model, runtime, stager = load_model(spec)
        write(output / "runtime.json", runtime)
        guards.append(shared.guard(policy))
    except BaseException as exc:
        error = {"error_type": type(exc).__name__, "error": str(exc)}
    def execute(cells, name, blocked):
        with (output / f"{name}.jsonl").open("x", encoding="utf-8") as handle:
            def emit(row):
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            kind = "parity" if name == "parity" else "candidate"
            def guarded_score(cell):
                guards.append(stager.before_call())
                require(time.monotonic() - started < spec["config"]["budget"]["walltime_seconds"], "Walltime exhausted")
                actual_forwards[kind] += 1
                values = base.score_cell(torch, model, cell, "cuda")
                guards.append(shared.guard(policy))
                if kind == "parity":
                    values["exact_match"] = (values["candidate_token_logprobs"] == cell["reference_logprobs"]
                                             and values["sequence_logprob_sum"] == cell["reference_sum"])
                    if not values["exact_match"]:
                        # Retain diagnostic scores on failure, separately from admitted rows.
                        write(output / "parity_mismatch.json", {"cell_id": cell["cell_id"], **values})
                    require(values["exact_match"], "Exact historical parity failed; new candidate acquisition prohibited")
                return values
            def scorer(cell):
                try:
                    return guarded_score(cell)
                except BaseException:
                    stager.release()  # Release our weights before writing the unrun denominator.
                    raise
            if blocked is None:
                remaining = max(0, spec["config"]["budget"]["walltime_seconds"] - (time.monotonic() - started))
                rows, progress = base.execute_cells(cells, scorer, emit, remaining)
                progress["scorer_calls_attempted"] = progress["forward_calls_attempted"]
                progress["forward_calls_attempted"] = actual_forwards[kind]
                return rows, progress
            rows = []
            for cell in cells:
                row = dict(cell)
                if row["status"] != "failed_preflight":
                    row.update(status="not_run", reason=blocked)
                row["recorded_at_utc"] = base.now()
                emit(row)
                rows.append(row)
            return rows, {"forward_calls_attempted": 0, "scorer_calls_attempted": 0}
    try:
        parity_rows, parity_progress = execute(parity, "parity", "setup_failed" if error else None)
        parity_pass = all(r["status"] == "completed" and r["exact_match"] is True for r in parity_rows)
        rows, progress = execute(spec["cells"], "cells", None if parity_pass else "historical_parity_gate_not_passed")
    finally:
        if stager is not None:
            peak = {"allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                    "reserved_mib": torch.cuda.max_memory_reserved() / 2**20}
            stager.release()
        else:
            peak = None
    write(output / "placement.json", {"policy": policy, "placement_changed_from_historical": True,
        "cpu_weight_storage": True, "arithmetic_device": "cuda", "quantization": False,
        "peak_torch_memory_mib": peak, "core_runtime_equals_historical": (output / "runtime.json").exists(),
        "own_staged_weights_released": stager is not None, "zero_slowdown_guarantee": False})
    write(output / "occupancy_checks.json", {"successful_checks": guards, "policy": policy})
    final = {**start, "status": "completed" if all(r["status"] == "completed" for r in rows) else "partial_or_failed",
        "finished_at_utc": base.now(), "progress": progress, "setup_error": error,
        "parity_passed": parity_pass, "parity_progress": parity_progress,
        "parity_status_counts": dict(Counter(r["status"] for r in parity_rows)),
        "total_model_forward_attempts": sum(actual_forwards.values()),
        "cell_status_counts": dict(Counter(r["status"] for r in rows)), "recorded_cells": len(rows),
        "elapsed_seconds_including_load": time.monotonic() - started,
        "cells_sha256": sha256(output / "cells.jsonl"),
        "occupancy_checks_sha256": sha256(output / "occupancy_checks.json"),
        "placement_sha256": sha256(output / "placement.json"), "parity_sha256": sha256(output / "parity.jsonl"),
        "parity_mismatch_sha256": sha256(output / "parity_mismatch.json") if (output / "parity_mismatch.json").exists() else None,
        "runtime_sha256": sha256(output / "runtime.json") if (output / "runtime.json").exists() else None}
    write(output / "run_completed.json", final)
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "prepare"):
        p = sub.add_parser(name)
        p.add_argument("--config", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
        if name == "prepare":
            p.add_argument("--model-path", type=Path, required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--specification", type=Path, required=True)
    execute = sub.add_parser("run")
    execute.add_argument("--specification", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--acknowledge-development-only", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = design(args.config)
            write(args.output, result)
            result = {k: result[k] for k in ("status", "denominator", "execution_ready", "model_forwards", "tokenizer_loaded")}
        elif args.command == "prepare":
            result = prepare(args.config, args.model_path, args.output)
        elif args.command == "audit":
            spec = verify_spec(args.specification)
            result = {"status": "source_input_audit_pass", "preflight_counts": spec["preflight_counts"], "model_forwards": 0}
        else:
            result = run(args.specification, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if result["status"] == "partial_or_failed" else 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
