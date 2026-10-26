#!/usr/bin/env python3
"""192 bounded development word-control cells; no generation or interventions.

The original stimuli and emoji baseline are read-only comparators. Only the
already stored word alternatives replace the historical {emoji} slot.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "scripts/contextual_emoji_output_pilot_v0.py"
module_spec = importlib.util.spec_from_file_location("word_control_baseline_helpers", BASELINE_PATH)
baseline = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(baseline)
require, sha256, json_read, json_write = baseline.require, baseline.sha256, baseline.json_read, baseline.json_write
PROTOCOL = "glyphprobe-contextual-emoji-word-control-v0"
CLAIM_CEILING = baseline.CLAIM_CEILING
INPUT_SHA = "3222695420917983d79d84e55364dd07a86b61b29ecc4d6dfdadedccde72f394"
MODEL_SHA = "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4"
COMPARATOR_SHA = {
    "baseline_specification": "04d7d005ee5c6555ef85cf900d79f79b88a50e7681001502ed3cd5be0d95bcd5",
    "baseline_cells": "ce090b817ea5c0ebf5382d1b1994a482f918d06043821d94157c0b2710980d97",
    "baseline_runner": "ccce1d18b701708506b61fa20cc1724fed3dd4c44ebfcecde66b20c635944daa",
    "baseline_runtime": "952139aec861ada4b9c889b36933a0f65c520c393d61d80e308f81b3df41e323",
}


def config_read(path: Path) -> dict[str, Any]:
    cfg = json_read(path)
    require(cfg.get("protocol_id") == PROTOCOL, "Protocol mismatch")
    require(cfg.get("inputs", {}).get("sha256") == INPUT_SHA, "Original stimulus pin required")
    for key, value in (("expected_blocks", 24), ("expected_families", 6), ("expected_blocks_per_family", 4)):
        require(cfg["inputs"].get(key) == value, f"Fixed input denominator required: {key}")
    for key, value in baseline.SCORE_RULE.items():
        require(cfg.get("scoring", {}).get(key) == value, f"Unsupported scoring rule: {key}")
    require(cfg["scoring"].get("J") == 1, "Exactly one unchanged candidate pair required")
    require(cfg["scoring"].get("prompt_slot") == "{emoji}", "Historical input slot must be unchanged")
    model = cfg.get("model", {})
    require(model.get("artifact_manifest_sha256") == MODEL_SHA, "Same model artifact required")
    require(model.get("local_files_only") is True and model.get("download") is False, "Local-only model required")
    require(model.get("dtype") == "bf16", "BF16 required")
    require(cfg.get("runtime", {}).get("require_baseline_python_and_packages") is True, "Baseline runtime equality required")
    budget = cfg.get("budget", {})
    for key, value in (("max_sequences", 192), ("planned_blocks", 24), ("planned_candidate_sequence_cells", 192),
                       ("generation_calls", 0), ("training_steps", 0), ("route_intervention_cells", 0)):
        require(budget.get(key) == value, f"Fixed budget required: {key}")
    for key, upper in (("max_input_tokens", 512), ("max_candidate_tokens", 64), ("walltime_seconds", 900)):
        require(type(budget.get(key)) is int and 0 < budget[key] <= upper, f"Invalid bounded budget: {key}")
    for key, pin in COMPARATOR_SHA.items():
        require(cfg.get("comparators", {}).get(key, {}).get("sha256") == pin, f"Comparator pin mismatch: {key}")
    return cfg


def comparators(cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipts = {}
    for key, pin in COMPARATOR_SHA.items():
        path = baseline.safe_path(ROOT / cfg["comparators"][key]["path"])
        require(sha256(path) == pin, f"Comparator changed: {key}")
        receipts[key] = {"path": str(path), "sha256": pin}
    previous = json_read(Path(receipts["baseline_specification"]["path"]))
    require(previous["protocol_id"] == baseline.PROTOCOL, "Baseline identity mismatch")
    require(previous["model_artifact"]["manifest_sha256"] == MODEL_SHA, "Baseline model mismatch")
    require(previous["source"]["files"]["inputs"]["sha256"] == INPUT_SHA, "Baseline stimuli mismatch")
    return previous, receipts


def source_receipt(config_path: Path, input_path: Path) -> dict[str, Any]:
    receipt = baseline.source_receipt(config_path, input_path)
    receipt["files"]["runner"] = {"path": str(Path(__file__).resolve()), "sha256": sha256(Path(__file__))}
    receipt["files"]["baseline_helpers"] = {"path": str(BASELINE_PATH), "sha256": sha256(BASELINE_PATH)}
    return receipt


def planned_cells(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells = []
    for block in blocks:
        words = block.get("planned_word_alternatives", {})
        require(set(words) == {"a", "b"}, "Exactly the two previously planned words required")
        require(all(isinstance(word, str) and word for word in words.values()) and words["a"] != words["b"], "Distinct nonempty word alternatives required")
        for context in ("p", "q"):
            template = block[f"context_{context}"]
            require(template.count("{emoji}") == 1, "One unchanged historical carrier slot required")
            start = template.index("{emoji}")
            for variant in ("a", "b"):
                surface = words[variant]
                diagonal = (context, variant) in (("p", "a"), ("q", "b"))
                expected_candidate = "a" if block["eta"] * (1 if diagonal else -1) > 0 else "b"
                require(block["orientation"][f"context_{context}"][f"emoji_{variant}"] == expected_candidate,
                        "Stored orientation and eta disagree")
                for candidate in ("a", "b"):
                    cells.append({"cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                        "block_id": block["block_id"], "family": block["family"], "context": context,
                        "variant": variant, "candidate": candidate, "carrier_kind": "word",
                        "prompt": template.replace("{emoji}", surface), "continuation": block[f"candidate_{candidate}"],
                        "carrier_surface": surface, "carrier_char_start": start, "carrier_char_end": start + len(surface),
                        "eta": block["eta"], "status": "planned"})
    require(len({cell["cell_id"] for cell in cells}) == len(cells), "Duplicate planned cell IDs")
    return cells


def encode_cell(tokenizer: Any, cell: dict[str, Any], budget: dict[str, int]) -> dict[str, Any]:
    """Reuse exact baseline tokenization; temporary aliases never enter receipts."""
    temporary = dict(cell)
    for key in ("surface", "char_start", "char_end"):
        temporary[f"emoji_{key}"] = temporary.pop(f"carrier_{key}")
    encoded = baseline.encode_cell(tokenizer, temporary, budget)
    for key in list(encoded):
        if key.startswith("emoji_"):
            encoded[f"carrier_{key[6:]}"] = encoded.pop(key)
    if encoded.get("error") == "Emoji span has no token offsets":
        encoded["error"] = "Word carrier span has no token offsets"
    return encoded


def prepare(config_path: Path, model_path: Path, output: Path) -> dict[str, Any]:
    require(not output.exists(), "Specification already exists")
    cfg = config_read(config_path)
    previous, comparator_receipts = comparators(cfg)
    input_path = baseline.safe_path(ROOT / cfg["inputs"]["path"])
    require(sha256(input_path) == INPUT_SHA, "Original inputs changed")
    blocks = baseline.load_blocks(input_path, 24)
    require(blocks == previous["blocks"], "Baseline blocks changed")
    require(len(Counter(row["family"] for row in blocks)) == 6 and set(Counter(row["family"] for row in blocks).values()) == {4}, "Family denominator mismatch")
    cells = planned_cells(blocks)
    require(len(cells) == 192, "Exactly 192 word cells required")
    require(baseline.package_versions() == previous["runtime_packages"], "Packages differ from emoji baseline")
    require(platform.python_version() == previous["python_version"], "Python differs from emoji baseline")
    artifact = baseline.artifact_receipt(model_path)
    require(artifact["manifest_sha256"] == MODEL_SHA, "Model artifact mismatch")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False, use_fast=True)
    encoded = [encode_cell(tokenizer, cell, cfg["budget"]) for cell in cells]
    spec = {"protocol_id": PROTOCOL, "schema_version": 1, "status": "development_preflight_zero_model_forwards",
        "created_at_utc": baseline.now(), "claim_ceiling": CLAIM_CEILING, "confirmatory": False,
        "model_forwards": 0, "generation_calls": 0, "intervention_executed": False, "route_instrumented": False,
        "config": cfg, "source": source_receipt(config_path, input_path), "comparators": comparator_receipts,
        "model_path": str(model_path.resolve()), "model_artifact": artifact,
        "runtime_packages": baseline.package_versions(), "python_version": platform.python_version(),
        "tokenizer_class": type(tokenizer).__name__, "tokenizer_vocab_size": len(tokenizer),
        "blocks": blocks, "cells": encoded, "candidate_token_diagnostics": baseline.token_diagnostics(encoded),
        "denominator": {"planned_blocks": 24, "planned_cells": 192, "preflight_counts": dict(Counter(row["status"] for row in encoded))}}
    json_write(output, spec)
    return {"status": spec["status"], "specification_sha256": sha256(output), "denominator": spec["denominator"], "model_forwards": 0}


def verify_specification(path: Path) -> dict[str, Any]:
    spec = json_read(path)
    require(spec.get("protocol_id") == PROTOCOL and spec.get("schema_version") == 1, "Specification identity mismatch")
    require(spec.get("status") == "development_preflight_zero_model_forwards", "Not a zero-forward specification")
    require(spec.get("claim_ceiling") == CLAIM_CEILING and spec.get("confirmatory") is False, "Claim boundary mismatch")
    for key in ("intervention_executed", "route_instrumented"):
        require(spec.get(key) is False, f"Unsupported activity: {key}")
    for name, item in spec["source"]["files"].items():
        require(sha256(Path(item["path"])) == item["sha256"], f"Bound source changed: {name}")
    cfg = config_read(Path(spec["source"]["files"]["config"]["path"]))
    require(cfg == spec["config"], "Bound config differs")
    previous, bound = comparators(cfg)
    require(bound == spec["comparators"], "Comparator receipts differ")
    blocks = baseline.load_blocks(Path(spec["source"]["files"]["inputs"]["path"]), 24)
    require(blocks == spec["blocks"] == previous["blocks"], "Bound blocks differ")
    require(spec["runtime_packages"] == previous["runtime_packages"] and spec["python_version"] == previous["python_version"], "Runtime binding differs from baseline")
    raw = planned_cells(blocks)
    require(len(raw) == len(spec["cells"]) == 192, "Planned cells omitted")
    for expected, stored in zip(raw, spec["cells"], strict=True):
        for key, value in expected.items():
            if key != "status":
                require(stored.get(key) == value, f"Changed cell field: {expected['cell_id']}:{key}")
        require(stored["status"] in ("ready", "failed_preflight"), "Invalid preflight status")
        if stored["status"] == "ready":
            require(stored["input_token_ids"] == stored["prompt_token_ids"] + stored["candidate_token_ids"], "Inconsistent token sequence")
            require(stored["prompt_token_count"] == len(stored["prompt_token_ids"]) > 0, "Invalid prompt count")
            require(stored["candidate_token_count"] == len(stored["candidate_token_ids"]) > 0, "Invalid candidate count")
    return spec


def gpu_guard(own_pid: int | None = None) -> dict[str, Any]:
    """Observe other compute PIDs, fail closed, and never manipulate any process."""
    own_pid = os.getpid() if own_pid is None else own_pid
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
                            capture_output=True, text=True, check=False, timeout=5)
    require(result.returncode == 0, "GPU occupancy query failed; no forward allowed")
    rows = [row.strip() for row in result.stdout.splitlines() if row.strip()]
    require(all(row.isdigit() for row in rows), "Unparseable GPU occupancy; no forward allowed")
    other = sorted({int(row) for row in rows} - {own_pid})
    require(not other, f"GPU contention observed; yielding without disturbing PIDs {other}")
    return {"checked_at_utc": baseline.now(), "own_pid": own_pid, "other_compute_pids": other}


def model_load(spec: dict[str, Any]) -> tuple[Any, Any, dict[str, Any]]:
    require(baseline.package_versions() == spec["runtime_packages"], "Packages changed since preparation")
    require(platform.python_version() == spec["python_version"], "Python changed since preparation")
    path = Path(spec["model_path"])
    require(baseline.artifact_receipt(path) == spec["model_artifact"], "Model artifact changed since preparation")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "BF16 CUDA required")
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
    encoded = [encode_cell(tokenizer, cell, spec["config"]["budget"]) for cell in planned_cells(spec["blocks"])]
    require(encoded == spec["cells"], "Tokenized cells changed after preparation")
    require(baseline.token_diagnostics(encoded) == spec["candidate_token_diagnostics"], "Candidate token diagnostics changed")
    gpu_guard()
    torch.set_num_threads(4)
    torch.manual_seed(2026100701)
    model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, trust_remote_code=False,
              dtype=torch.bfloat16, attn_implementation="eager").to("cuda").eval()
    cfg = spec["config"]["model"]
    require(type(model).__name__ == cfg["expected_class"], "Model class mismatch")
    for key, model_key in (("expected_layers", "num_hidden_layers"), ("expected_hidden_size", "hidden_size"), ("expected_vocab_size", "vocab_size")):
        require(getattr(model.config, model_key) == cfg[key], f"Model dimension mismatch: {key}")
    parameters = sum(parameter.numel() for parameter in model.parameters())
    require(parameters == cfg["expected_parameters"], "Parameter count mismatch")
    require({parameter.dtype for parameter in model.parameters()} == {torch.bfloat16}, "Unexpected dtype")
    runtime = {"python": sys.version, "platform": platform.platform(), "packages": baseline.package_versions(),
        "torch": torch.__version__, "cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
        "device": torch.cuda.get_device_name(0), "device_capability": list(torch.cuda.get_device_capability(0)),
        "model_class": type(model).__name__, "model_config": model.config.to_dict(), "parameters": parameters,
        "dtype": "bfloat16", "attention": "eager", "use_cache": False,
        "model_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model).forward).encode()).hexdigest(),
        "attention_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model.model.layers[0].self_attn).forward).encode()).hexdigest(),
        "local_files_only": True, "trust_remote_code": False, "download": False, "generation_calls": 0, "route_instrumented": False}
    verify_runtime_identity(runtime, json_read(Path(spec["comparators"]["baseline_runtime"]["path"])))
    return torch, model, runtime


def verify_runtime_identity(current: dict[str, Any], previous: dict[str, Any]) -> None:
    """Require observed implementation/backend identity before the first forward."""
    for key in ("packages", "torch", "cuda", "cudnn", "device", "device_capability", "model_class",
                "parameters", "dtype", "attention", "use_cache", "model_forward_source_sha256",
                "attention_forward_source_sha256", "local_files_only", "trust_remote_code", "download"):
        require(key in current and key in previous and current[key] == previous[key], f"Baseline runtime identity mismatch: {key}")
    for key in ("num_hidden_layers", "hidden_size", "vocab_size", "num_attention_heads", "num_key_value_heads", "intermediate_size"):
        require(current.get("model_config", {}).get(key) == previous.get("model_config", {}).get(key)
                and key in current.get("model_config", {}), f"Baseline model dimension mismatch: {key}")


def aggregate(blocks: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {row["cell_id"]: row for row in records}
    require(len(by_id) == len(records), "Duplicate result cell IDs")
    expected = {cell["cell_id"] for cell in planned_cells(blocks)}
    require(set(by_id) <= expected, "Unexpected result cells")
    rows = []
    for block in blocks:
        s, aligned, missing = {}, {}, []
        for context in ("p", "q"):
            s[context], aligned[context] = {}, {}
            for variant in ("a", "b"):
                pair = [by_id.get(f"{block['block_id']}:{context}:{variant}:{candidate}") for candidate in ("a", "b")]
                value = None
                if all(row is not None and row["status"] == "completed" for row in pair):
                    value = pair[0]["sequence_logprob_sum"] - pair[1]["sequence_logprob_sum"]
                else:
                    missing.append(f"{context}:{variant}")
                s[context][variant] = value
                label = block["orientation"][f"context_{context}"][f"emoji_{variant}"]
                aligned[context][variant] = None if value is None else ((value > 0) if label == "a" else (value < 0))
        delta = {c: s[c]["b"] - s[c]["a"] if all(s[c][v] is not None for v in ("a", "b")) else None for c in ("p", "q")}
        complete = not missing
        alignment_values = [aligned[c][v] for c in ("p", "q") for v in ("a", "b")]
        rows.append({"block_id": block["block_id"], "family": block["family"], "eta": block["eta"],
            "status": "completed" if complete else "incomplete", "missing_pairs": missing, "s": s,
            "delta_p": delta["p"], "delta_q": delta["q"], "H": block["eta"] * (delta["q"] - delta["p"]) if complete else None,
            "intended_delta_crossover": block["eta"] * delta["p"] < 0 < block["eta"] * delta["q"] if complete else None,
            "absolute_author_alignment": aligned, "absolute_author_alignment_available": sum(x is not None for x in alignment_values),
            "absolute_author_aligned_count": sum(x is True for x in alignment_values),
            "all_four_author_aligned": all(alignment_values) if complete else None, "claim_ceiling": CLAIM_CEILING})
    complete = [row for row in rows if row["status"] == "completed"]
    family_denominators = {}
    for family in sorted({block["family"] for block in blocks}):
        planned = sum(block["family"] == family for block in blocks)
        available = [row for row in complete if row["family"] == family]
        family_denominators[family] = {"planned_blocks": planned, "completed_blocks": len(available),
            "incomplete_blocks": planned - len(available), "full_family_mean_H": statistics.fmean(row["H"] for row in available) if len(available) == planned else None,
            "positive_H_count": sum(row["H"] > 0 for row in available), "intended_delta_crossover_count": sum(row["intended_delta_crossover"] for row in available)}
    return {"blocks": rows, "denominator": {"planned_blocks": len(blocks), "completed_blocks": len(complete),
        "incomplete_blocks": len(blocks) - len(complete), "planned_cells": len(blocks) * 8, "recorded_cells": len(records),
        "cell_status_counts": dict(Counter(row["status"] for row in records)),
        "planned_crossed_input_conditions": len(blocks) * 4,
        "available_absolute_author_alignment_conditions": sum(row["absolute_author_alignment_available"] for row in rows)},
        "positive_H_count": sum(row["H"] > 0 for row in complete),
        "intended_delta_crossover_count": sum(row["intended_delta_crossover"] for row in complete),
        "absolute_author_aligned_count": sum(row["absolute_author_aligned_count"] for row in rows),
        "all_four_author_aligned_block_count": sum(row["all_four_author_aligned"] is True for row in complete),
        "complete_block_mean_H": statistics.fmean(row["H"] for row in complete) if complete else None,
        "family_denominators": family_denominators,
        "planned_population_equal_family_mean_H": statistics.fmean(value["full_family_mean_H"] for value in family_denominators.values()) if len(complete) == len(blocks) and blocks else None,
        "descriptive_only": True, "confirmatory": False, "claim_ceiling": CLAIM_CEILING,
        "available_case_summaries_are_not_full_population_estimates": True, "incomplete_population_warning": len(complete) != len(blocks),
        "semantic_claim_supported": False, "route_instrumented": False, "intervention_executed": False}


def run(spec_path: Path, output: Path) -> dict[str, Any]:
    spec = verify_specification(spec_path)
    require(not output.exists(), "Run output already exists; use a new directory")
    output.mkdir(parents=True)
    json_write(output / "specification.json", spec)
    initial = {"protocol_id": PROTOCOL, "schema_version": 1, "started_at_utc": baseline.now(), "status": "started",
        "claim_ceiling": CLAIM_CEILING, "confirmatory": False, "specification_path": str(spec_path.resolve()),
        "specification_sha256": sha256(spec_path), "local_specification_sha256": sha256(output / "specification.json"),
        "source": spec["source"], "comparators": spec["comparators"], "model_artifact": spec["model_artifact"],
        "planned_cell_ids": [cell["cell_id"] for cell in spec["cells"]], "planned_blocks": len(spec["blocks"]),
        "planned_cells": len(spec["cells"]), "generation_calls": 0, "route_instrumented": False, "intervention_executed": False}
    json_write(output / "run_started.json", initial)
    runtime, setup_error, actual_forwards, guards = None, None, 0, []
    started = time.monotonic()
    try:
        guards.append(gpu_guard())
        torch, model, runtime = model_load(spec)
        json_write(output / "runtime.json", runtime)
    except BaseException as error:
        setup_error = {"error_type": type(error).__name__, "error": str(error)}
    with (output / "cells.jsonl").open("x", encoding="utf-8") as handle:
        def emit(row: dict[str, Any]) -> None:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        def scorer(cell: dict[str, Any]) -> dict[str, Any]:
            nonlocal actual_forwards
            guards.append(gpu_guard())
            actual_forwards += 1
            return baseline.score_cell(torch, model, cell, "cuda")
        if setup_error is None:
            remaining = max(0.0, spec["config"]["budget"]["walltime_seconds"] - (time.monotonic() - started))
            records, progress = baseline.execute_cells(spec["cells"], scorer, emit, remaining)
            progress["scorer_calls_attempted"] = progress["forward_calls_attempted"]
            progress["forward_calls_attempted"] = actual_forwards
        else:
            records = []
            for cell in spec["cells"]:
                row = dict(cell)
                if row["status"] != "failed_preflight":
                    row.update(status="not_run", reason="model_setup_failed")
                row["recorded_at_utc"] = baseline.now()
                emit(row)
                records.append(row)
            progress = {"forward_calls_attempted": 0, "stop_reason": "model_setup_failed"}
    json_write(output / "occupancy_checks.json", {"policy": "fail_closed_other_compute_pid_before_each_forward", "successful_checks": guards})
    summary = aggregate(spec["blocks"], records)
    json_write(output / "summary.json", summary)
    final = {**initial, "status": "completed" if all(row["status"] == "completed" for row in records) else "partial_or_failed",
        "finished_at_utc": baseline.now(), "runtime_recorded": runtime is not None, "setup_error": setup_error,
        "progress": progress, "elapsed_seconds_including_load": time.monotonic() - started, "denominator": summary["denominator"],
        "cells_sha256": sha256(output / "cells.jsonl"), "summary_sha256": sha256(output / "summary.json"),
        "occupancy_checks_sha256": sha256(output / "occupancy_checks.json"), "semantic_claim_supported": False}
    json_write(output / "run_completed.json", final)
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--config", type=Path, required=True)
    prep.add_argument("--model-path", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("audit")
    check.add_argument("--specification", type=Path, required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--specification", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--acknowledge-development-only", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.config, args.model_path, args.output)
        elif args.command == "audit":
            spec = verify_specification(args.specification)
            result = {"status": "source_input_comparator_audit_pass", "denominator": spec["denominator"], "model_forwards": 0}
        else:
            result = run(args.specification, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 2 if result["status"] == "partial_or_failed" else 0
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
