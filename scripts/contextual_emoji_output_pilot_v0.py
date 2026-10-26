#!/usr/bin/env python3
"""Bounded, local-only contextual output pilot; author-defined labels, no claims.

No historical target loader is imported. ``prepare`` tokenizes and binds inputs
without model forwards. ``run`` executes the complete recorded baseline grid,
or an explicitly partial smoke run, with no interventions or generation.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
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
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-output-pilot-v0"
SCHEMA = 1
CONTEXTS = ("p", "q")
VARIANTS = ("a", "b", "absent")
CANDIDATES = ("a", "b")
PROTECTED_NAMES = {
    "p2_confirmatory_targets_v1.jsonl",
    "c1_causal_holdout_targets_v1.jsonl",
}
CLAIM_CEILING = "author_defined_development_labels_only_not_semantic_or_confirmatory"
SCORE_RULE = {
    "add_special_tokens": False,
    "include_eos": False,
    "normalization": "none",
    "boundary": "joint_tokenization_exact_prefix",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_path(path: Path) -> Path:
    """Reject historical-bank names before opening or hashing any requested file."""
    require(path.name not in PROTECTED_NAMES, "Protected historical target access prohibited")
    resolved = path.resolve()
    require(resolved.name not in PROTECTED_NAMES, "Protected historical target access prohibited")
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with safe_path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_read(path: Path) -> dict[str, Any]:
    result = json.loads(safe_path(path).read_text(encoding="utf-8"))
    require(isinstance(result, dict), "Expected a JSON object")
    return result


def json_write(path: Path, value: Any) -> None:
    """Create a durable receipt exclusively; never overwrite a previous result."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def package_versions() -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name in ("torch", "transformers", "tokenizers", "safetensors", "numpy"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def source_receipt(config_path: Path, input_path: Path) -> dict[str, Any]:
    files = {
        "runner": Path(__file__),
        "config": config_path,
        "inputs": input_path,
        "model_provenance": ROOT / "src/glyphprobe/provenance.py",
        "io": ROOT / "src/glyphprobe/io.py",
    }
    hashes = {name: {"path": str(path.resolve()), "sha256": sha256(path)} for name, path in files.items()}
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return {"files": hashes, "git_head": git.stdout.strip() if git.returncode == 0 else None}


def config_read(path: Path) -> dict[str, Any]:
    value = json_read(path)
    require(value.get("protocol_id") == PROTOCOL, "Protocol mismatch")
    for key, expected in SCORE_RULE.items():
        require(value.get("scoring", {}).get(key) == expected, f"Unsupported scoring rule: {key}")
    model = value.get("model", {})
    require(model.get("local_files_only") is True, "Only local model loading is allowed")
    require(model.get("download") is False, "Downloads are prohibited")
    require(model.get("dtype") == "bf16", "This baseline is pinned to BF16")
    pin = model.get("artifact_manifest_sha256")
    require(isinstance(pin, str) and len(pin) == 64 and all(char in "0123456789abcdef" for char in pin),
            "A pre-existing model artifact_manifest_sha256 pin is required")
    require(value.get("scoring", {}).get("J", 1) == 1, "This bounded runner implements one fixed candidate pair")
    budget = value.get("budget", {})
    for key in ("max_sequences", "max_input_tokens", "max_candidate_tokens", "walltime_seconds"):
        require(isinstance(budget.get(key), int) and not isinstance(budget.get(key), bool) and budget[key] > 0,
                f"Invalid budget: {key}")
    require(budget["max_sequences"] <= 288, "This bounded runner permits at most 288 sequence cells")
    require(budget["walltime_seconds"] <= 900, "This bounded runner permits at most 900 seconds")
    return value


def load_blocks(path: Path, expected: int) -> list[dict[str, Any]]:
    rows = []
    with safe_path(path).open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            require(bool(line.strip()), f"Blank input record at line {index}")
            row = json.loads(line)
            require(isinstance(row, dict), f"Expected object at line {index}")
            rows.append(row)
    require(len(rows) == expected, "Input count differs from specified denominator")
    ids = [row.get("block_id") for row in rows]
    require(all(isinstance(key, str) and key for key in ids), "Missing block IDs")
    require(len(set(ids)) == len(ids), "Duplicate block IDs")
    for row in rows:
        require(row.get("design_status") == "author_defined_development", "Non-development input rejected")
        require(row.get("interpretation_status") == "unvalidated_author_defined", "Unsupported interpretation status")
        require(row.get("eta") in (-1, 1) and not isinstance(row["eta"], bool), "eta must be −1 or +1")
        for key in ("family", "emoji_a", "emoji_b", "candidate_a", "candidate_b", "context_p", "context_q"):
            require(isinstance(row.get(key), str) and bool(row[key]), f"Missing field {key}: {row['block_id']}")
        require(row["emoji_a"] != row["emoji_b"], "Emoji alternatives must differ")
        require(row["candidate_a"] != row["candidate_b"], "Candidate alternatives must differ")
        for context in CONTEXTS:
            require(row[f"context_{context}"].count("{emoji}") == 1, "Each context needs one {emoji} slot")
    return rows


def planned_cells(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells = []
    for block in blocks:
        for context in CONTEXTS:
            for variant in VARIANTS:
                emoji = "" if variant == "absent" else block[f"emoji_{variant}"]
                template = block[f"context_{context}"]
                prompt = template.replace("{emoji}", emoji)
                emoji_start = template.index("{emoji}")
                for candidate in CANDIDATES:
                    cells.append({
                        "cell_id": f"{block['block_id']}:{context}:{variant}:{candidate}",
                        "block_id": block["block_id"], "family": block["family"],
                        "context": context, "variant": variant, "candidate": candidate,
                        "prompt": prompt, "continuation": block[f"candidate_{candidate}"],
                        "emoji_surface": emoji, "emoji_char_start": emoji_start,
                        "emoji_char_end": emoji_start + len(emoji),
                        "eta": block["eta"], "status": "planned",
                    })
    return cells


def encode_cell(tokenizer: Any, cell: dict[str, Any], budget: dict[str, int]) -> dict[str, Any]:
    """Use joint tokenization and fail closed on any boundary retokenization."""
    result = dict(cell)
    try:
        prompt_ids = list(map(int, tokenizer.encode(cell["prompt"], add_special_tokens=False)))
        full_ids = list(map(int, tokenizer.encode(cell["prompt"] + cell["continuation"], add_special_tokens=False)))
        require(len(prompt_ids) > 0, "empty_prompt_token_sequence")
        require(full_ids[:len(prompt_ids)] == prompt_ids, "candidate_boundary_retokenized_prompt")
        candidate_ids = full_ids[len(prompt_ids):]
        require(len(candidate_ids) > 0, "empty_candidate_token_sequence")
        require(len(full_ids) <= budget["max_input_tokens"], "input_token_budget_exceeded")
        require(len(candidate_ids) <= budget["max_candidate_tokens"], "candidate_token_budget_exceeded")
        offsets = tokenizer(cell["prompt"], add_special_tokens=False, return_offsets_mapping=True)
        require(list(offsets["input_ids"]) == prompt_ids, "Offset tokenization differs from scoring tokenization")
        bounds = [list(map(int, pair)) for pair in offsets["offset_mapping"]]
        start, end = cell["emoji_char_start"], cell["emoji_char_end"]
        source_positions = [index for index, (left, right) in enumerate(bounds)
                            if start < end and left < end and right > start]
        if cell["variant"] != "absent":
            require(bool(source_positions), "Emoji span has no token offsets")
        result.update({
            "status": "ready", "prompt_token_ids": prompt_ids,
            "candidate_token_ids": candidate_ids, "input_token_ids": full_ids,
            "prompt_token_count": len(prompt_ids), "candidate_token_count": len(candidate_ids),
            "candidate_token_strings": [tokenizer.decode([token], clean_up_tokenization_spaces=False) for token in candidate_ids],
            "emoji_token_positions": source_positions, "emoji_token_count": len(source_positions),
            "emoji_token_offsets": [bounds[index] for index in source_positions],
            "emoji_tokens_cross_span_boundary": any(bounds[index][0] < start or bounds[index][1] > end for index in source_positions),
            "first_candidate_predictor_position": len(prompt_ids) - 1,
        })
    except Exception as error:
        result.update(status="failed_preflight", error_type=type(error).__name__, error=str(error))
    return result


def token_diagnostics(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """No EOS means candidates are token-prefix events, possibly overlapping."""
    pairs: dict[tuple[str, str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for cell in cells:
        pairs[(cell["block_id"], cell["context"], cell["variant"])][cell["candidate"]] = cell
    result = []
    for (block_id, context, variant), pair in pairs.items():
        row: dict[str, Any] = {"block_id": block_id, "context": context, "variant": variant,
                               "status": "unavailable_failed_preflight"}
        if len(pair) == 2 and all(cell["status"] == "ready" for cell in pair.values()):
            a, b = pair["a"]["candidate_token_ids"], pair["b"]["candidate_token_ids"]
            row.update(status="available", candidate_a_token_count=len(a), candidate_b_token_count=len(b),
                       candidates_same_token_sequence=a == b,
                       candidate_a_is_token_prefix_of_b=len(a) <= len(b) and a == b[:len(a)],
                       candidate_b_is_token_prefix_of_a=len(b) <= len(a) and b == a[:len(b)],
                       candidate_event="fixed_continuation_prefix_no_eos_not_normalized_choice")
        result.append(row)
    return result


def artifact_receipt(path: Path) -> dict[str, Any]:
    require(path.is_dir(), "An existing local model snapshot directory is required")
    sys.path.insert(0, str(ROOT / "src"))
    from glyphprobe.provenance import model_artifact_receipt
    return model_artifact_receipt(path)


def prepare(config_path: Path, model_path: Path, output: Path) -> dict[str, Any]:
    require(not output.exists(), "Specification already exists")
    cfg = config_read(config_path)
    input_path = safe_path(ROOT / cfg["inputs"]["path"])
    require(sha256(input_path) == cfg["inputs"]["sha256"], "Input hash mismatch")
    blocks = load_blocks(input_path, cfg["inputs"]["expected_blocks"])
    if "expected_families" in cfg["inputs"]:
        require(len({row["family"] for row in blocks}) == cfg["inputs"]["expected_families"], "Family count mismatch")
    if "expected_blocks_per_family" in cfg["inputs"]:
        require(all(count == cfg["inputs"]["expected_blocks_per_family"] for count in Counter(row["family"] for row in blocks).values()),
                "Blocks per family mismatch")
    cells = planned_cells(blocks)
    require(len(cells) <= cfg["budget"]["max_sequences"], "Planned cells exceed forward budget")
    model_path = model_path.resolve()
    artifact = artifact_receipt(model_path)
    require(artifact["manifest_sha256"] == cfg["model"]["artifact_manifest_sha256"], "Model artifact hash mismatch")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    encoded = [encode_cell(tokenizer, cell, cfg["budget"]) for cell in cells]
    spec = {
        "protocol_id": PROTOCOL, "schema_version": SCHEMA,
        "status": "development_preflight_zero_model_forwards", "created_at_utc": now(),
        "claim_ceiling": CLAIM_CEILING, "confirmatory": False,
        "model_forwards": 0, "generation_calls": 0,
        "intervention_executed": False, "route_instrumented": False,
        "config": cfg, "source": source_receipt(config_path, input_path),
        "model_path": str(model_path), "model_artifact": artifact,
        "runtime_packages": package_versions(), "python_version": platform.python_version(),
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": len(tokenizer),
        "blocks": blocks, "cells": encoded, "candidate_token_diagnostics": token_diagnostics(encoded),
        "denominator": {"planned_blocks": len(blocks), "planned_cells": len(cells),
                        "preflight_counts": dict(Counter(row["status"] for row in encoded))},
    }
    json_write(output, spec)
    return {"status": spec["status"], "specification_sha256": sha256(output),
            "denominator": spec["denominator"], "model_forwards": 0}


def verify_specification(path: Path) -> dict[str, Any]:
    spec = json_read(path)
    require(spec.get("protocol_id") == PROTOCOL and spec.get("schema_version") == SCHEMA, "Specification identity mismatch")
    require(spec.get("status") == "development_preflight_zero_model_forwards", "Not a zero-forward development specification")
    require(spec.get("claim_ceiling") == CLAIM_CEILING and spec.get("confirmatory") is False, "Claim boundary mismatch")
    for name, item in spec["source"]["files"].items():
        require(sha256(Path(item["path"])) == item["sha256"], f"Bound source changed: {name}")
    cfg = config_read(Path(spec["source"]["files"]["config"]["path"]))
    require(cfg == spec["config"], "Specification config differs from bound source")
    blocks = load_blocks(Path(spec["source"]["files"]["inputs"]["path"]), cfg["inputs"]["expected_blocks"])
    require(blocks == spec["blocks"], "Specification blocks differ from bound input")
    raw = planned_cells(blocks)
    require(len(raw) == len(spec["cells"]), "Specification omitted planned cells")
    for expected, stored in zip(raw, spec["cells"], strict=True):
        for key, value in expected.items():
            if key != "status":
                require(stored.get(key) == value, f"Changed cell field: {expected['cell_id']}:{key}")
        require(stored["status"] in ("ready", "failed_preflight"), "Invalid preflight cell status")
        if stored["status"] == "ready":
            require(stored["input_token_ids"] == stored["prompt_token_ids"] + stored["candidate_token_ids"], "Inconsistent token sequence")
            require(stored["prompt_token_count"] == len(stored["prompt_token_ids"]) > 0, "Invalid prompt count")
            require(stored["candidate_token_count"] == len(stored["candidate_token_ids"]) > 0, "Invalid candidate count")
    return spec


def score_logits(logits: Any, input_ids: list[int], prompt_length: int) -> list[float]:
    """Score every candidate token using its preceding-position logit vector."""
    import torch
    require(logits.ndim == 3 and logits.shape[0] == 1, "Expected single-sequence logits")
    require(0 < prompt_length < len(input_ids), "Invalid candidate boundary")
    require(logits.shape[1] == len(input_ids), "Logit sequence length mismatch")
    candidate_ids = torch.tensor(input_ids[prompt_length:], dtype=torch.long, device=logits.device)
    predicting_logits = logits[0, prompt_length - 1:len(input_ids) - 1].float()
    values = torch.log_softmax(predicting_logits, dim=-1).gather(-1, candidate_ids[:, None]).squeeze(-1)
    result = [float(value) for value in values.detach().cpu().tolist()]
    require(len(result) == len(input_ids) - prompt_length, "Candidate tokens omitted")
    require(all(math.isfinite(value) and value <= 1e-6 for value in result), "Nonfinite or positive log probability")
    return result


def score_cell(torch: Any, model: Any, cell: dict[str, Any], device: str) -> dict[str, Any]:
    inputs = torch.tensor([cell["input_token_ids"]], dtype=torch.long, device=device)
    started = time.monotonic()
    with torch.inference_mode():
        output = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), use_cache=False)
        values = score_logits(output.logits, cell["input_token_ids"], cell["prompt_token_count"])
    return {"candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values),
            "elapsed_seconds": time.monotonic() - started}


def model_load(spec: dict[str, Any], device: str) -> tuple[Any, Any, dict[str, Any]]:
    import torch
    from transformers import AutoModelForCausalLM
    require(package_versions() == spec["runtime_packages"], "Runtime packages changed after preparation")
    require(platform.python_version() == spec["python_version"], "Python version changed after preparation")
    require(device == "cuda" and torch.cuda.is_available(), "The recorded BF16 acquisition requires CUDA")
    require(torch.cuda.is_bf16_supported(), "CUDA BF16 unavailable")
    path = Path(spec["model_path"])
    require(artifact_receipt(path) == spec["model_artifact"], "Model artifact changed after preparation")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False, use_fast=True)
    reencoded = [encode_cell(tokenizer, cell, spec["config"]["budget"]) for cell in planned_cells(spec["blocks"])]
    require(reencoded == spec["cells"], "Tokenized cells changed after preparation")
    require(token_diagnostics(reencoded) == spec["candidate_token_diagnostics"], "Candidate token diagnostics changed")
    torch.set_num_threads(4)
    torch.manual_seed(2026100701)
    model = AutoModelForCausalLM.from_pretrained(
        path, local_files_only=True, trust_remote_code=False,
        dtype=torch.bfloat16, attn_implementation="eager",
    ).to(device).eval()
    cfg = spec["config"]["model"]
    require(type(model).__name__ == cfg.get("expected_class", "LlamaForCausalLM"), "Unexpected model class")
    for config_key, model_key in (("expected_layers", "num_hidden_layers"), ("expected_hidden_size", "hidden_size"), ("expected_vocab_size", "vocab_size")):
        if cfg.get(config_key) is not None:
            require(getattr(model.config, model_key) == cfg[config_key], f"Model dimension mismatch: {config_key}")
    parameters = sum(parameter.numel() for parameter in model.parameters())
    if cfg.get("expected_parameters") is not None:
        require(parameters == cfg["expected_parameters"], "Parameter count mismatch")
    require({parameter.dtype for parameter in model.parameters()} == {torch.bfloat16}, "Unexpected parameter dtype")
    model_source = inspect.getsource(type(model).forward).encode()
    attention = model.model.layers[0].self_attn
    runtime = {
        "python": sys.version, "platform": platform.platform(), "packages": package_versions(),
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(), "device": torch.cuda.get_device_name(0),
        "device_capability": list(torch.cuda.get_device_capability(0)),
        "model_class": type(model).__name__, "model_config": model.config.to_dict(),
        "parameters": parameters, "dtype": "bfloat16", "attention": "eager", "use_cache": False,
        "model_forward_source_sha256": hashlib.sha256(model_source).hexdigest(),
        "attention_forward_source_sha256": hashlib.sha256(inspect.getsource(type(attention).forward).encode()).hexdigest(),
        "local_files_only": True, "trust_remote_code": False, "download": False,
        "generation_calls": 0, "route_instrumented": False,
    }
    return torch, model, runtime


def aggregate(blocks: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve missingness: an incomplete block never receives an imputed H."""
    by_id = {row["cell_id"]: row for row in records}
    require(len(by_id) == len(records), "Duplicate result cell IDs")
    rows = []
    for block in blocks:
        prefix = block["block_id"]
        values: dict[str, dict[str, float | None]] = {context: {} for context in CONTEXTS}
        missing = []
        for context in CONTEXTS:
            for variant in VARIANTS:
                pair = [by_id.get(f"{prefix}:{context}:{variant}:{candidate}") for candidate in CANDIDATES]
                if all(row is not None and row["status"] == "completed" for row in pair):
                    values[context][variant] = pair[0]["sequence_logprob_sum"] - pair[1]["sequence_logprob_sum"]
                else:
                    values[context][variant] = None
                    missing.append(f"{context}:{variant}")
        delta = {
            context: values[context]["b"] - values[context]["a"]
            if values[context]["a"] is not None and values[context]["b"] is not None else None
            for context in CONTEXTS
        }
        complete = not missing
        interaction = None
        crossover = None
        if all(delta[context] is not None for context in CONTEXTS):
            interaction = block["eta"] * (delta["q"] - delta["p"])
            crossover = block["eta"] * delta["p"] < 0 < block["eta"] * delta["q"]
        rows.append({
            "block_id": prefix, "family": block["family"], "eta": block["eta"],
            "status": "completed" if complete else "incomplete", "missing_pairs": missing,
            "s": values, "delta_p": delta["p"], "delta_q": delta["q"], "H": interaction,
            "intended_delta_crossover": crossover,
            "claim_ceiling": CLAIM_CEILING,
        })
    complete_rows = [row for row in rows if row["status"] == "completed"]
    families: dict[str, list[float]] = defaultdict(list)
    for row in complete_rows:
        families[row["family"]].append(row["H"])
    family_means = {family: statistics.fmean(values) for family, values in families.items()}
    family_denominators = {}
    for family in sorted({block["family"] for block in blocks}):
        planned = sum(block["family"] == family for block in blocks)
        completed = len(families[family])
        family_denominators[family] = {
            "planned_blocks": planned, "completed_blocks": completed,
            "incomplete_blocks": planned - completed,
            "full_family_mean_H": family_means.get(family) if planned == completed else None,
        }
    return {
        "blocks": rows,
        "denominator": {"planned_blocks": len(blocks), "completed_blocks": len(complete_rows),
                        "incomplete_blocks": len(blocks) - len(complete_rows),
                        "planned_cells": len(blocks) * 12, "recorded_cells": len(records),
                        "cell_status_counts": dict(Counter(row["status"] for row in records))},
        "descriptive_only": True, "confirmatory": False, "claim_ceiling": CLAIM_CEILING,
        "complete_block_mean_H": statistics.fmean(row["H"] for row in complete_rows) if complete_rows else None,
        "family_complete_block_mean_H": family_means,
        "mean_of_available_family_means_H": statistics.fmean(family_means.values()) if family_means else None,
        "family_denominators": family_denominators,
        "planned_population_equal_family_mean_H": statistics.fmean(family_means.values())
            if len(complete_rows) == len(blocks) and family_means else None,
        "available_case_summaries_are_not_full_population_estimates": True,
        "incomplete_population_warning": len(complete_rows) != len(blocks),
        "semantic_claim_supported": False, "route_instrumented": False, "intervention_executed": False,
    }


def execute_cells(cells: list[dict[str, Any]], scorer: Callable[[dict[str, Any]], dict[str, Any]],
                  emit: Callable[[dict[str, Any]], None], max_seconds: float,
                  limit_cells: int | None = None, clock: Callable[[], float] = time.monotonic) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Small testable state machine; stop on failure and retain every planned cell."""
    require(limit_cells is None or 0 <= limit_cells <= len(cells), "Invalid explicit smoke limit")
    started = clock()
    records = []
    stop_reason = None
    attempted = 0
    for index, cell in enumerate(cells):
        result = dict(cell)
        if cell["status"] == "failed_preflight":
            pass
        elif stop_reason is not None:
            result.update(status="not_run", reason=stop_reason)
        elif limit_cells is not None and index >= limit_cells:
            result.update(status="not_run", reason="explicit_partial_smoke_limit")
        elif clock() - started >= max_seconds:
            stop_reason = "walltime_budget_exhausted"
            result.update(status="not_run", reason=stop_reason)
        else:
            attempted += 1
            try:
                values = scorer(cell)
                require(len(values["candidate_token_logprobs"]) == cell["candidate_token_count"], "Incomplete candidate scores")
                require(all(math.isfinite(x) and x <= 1e-6 for x in values["candidate_token_logprobs"]), "Invalid token scores")
                require(math.isclose(values["sequence_logprob_sum"], math.fsum(values["candidate_token_logprobs"]), rel_tol=0, abs_tol=1e-10), "Sequence score is not the token sum")
                result.update(values)
                result["status"] = "completed"
            except BaseException as error:
                # Deliberately retain KeyboardInterrupt/SystemExit as an aborted
                # acquisition and write the unexecuted denominator before exit.
                stop_reason = "stopped_after_cell_failure"
                result.update(status="failed", error_type=type(error).__name__, error=str(error))
        result["recorded_at_utc"] = now()
        emit(result)
        records.append(result)
    return records, {"forward_calls_attempted": attempted, "stop_reason": stop_reason,
                     "elapsed_seconds": clock() - started}


def run(spec_path: Path, output: Path, limit_cells: int | None = None) -> dict[str, Any]:
    spec = verify_specification(spec_path)
    require(not output.exists(), "Run output already exists; use a new directory")
    require(limit_cells is None or 0 <= limit_cells <= len(spec["cells"]), "Invalid smoke limit")
    output.mkdir(parents=True)
    json_write(output / "specification.json", spec)
    initial = {
        "protocol_id": PROTOCOL, "schema_version": SCHEMA, "started_at_utc": now(),
        "status": "started", "claim_ceiling": CLAIM_CEILING, "confirmatory": False,
        "specification_path": str(spec_path.resolve()), "specification_sha256": sha256(spec_path),
        "local_specification_sha256": sha256(output / "specification.json"),
        "source": spec["source"], "model_artifact": spec["model_artifact"],
        "planned_cell_ids": [cell["cell_id"] for cell in spec["cells"]],
        "planned_blocks": len(spec["blocks"]), "planned_cells": len(spec["cells"]),
        "explicit_smoke_cell_limit": limit_cells, "generation_calls": 0,
        "route_instrumented": False, "intervention_executed": False,
    }
    json_write(output / "run_started.json", initial)
    runtime = None
    setup_error = None
    acquisition_started = time.monotonic()
    try:
        torch, model, runtime = model_load(spec, "cuda")
        json_write(output / "runtime.json", runtime)
    except BaseException as error:
        setup_error = {"error_type": type(error).__name__, "error": str(error)}
    with (output / "cells.jsonl").open("x", encoding="utf-8") as handle:
        def emit(row: dict[str, Any]) -> None:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if setup_error is None:
            remaining = max(0.0, spec["config"]["budget"]["walltime_seconds"] - (time.monotonic() - acquisition_started))
            records, progress = execute_cells(
                spec["cells"], lambda cell: score_cell(torch, model, cell, "cuda"), emit,
                remaining, limit_cells=limit_cells,
            )
        else:
            records = []
            for cell in spec["cells"]:
                record = dict(cell)
                if record["status"] != "failed_preflight":
                    record.update(status="not_run", reason="model_setup_failed")
                record["recorded_at_utc"] = now()
                emit(record)
                records.append(record)
            progress = {"forward_calls_attempted": 0, "stop_reason": "model_setup_failed"}
    summary = aggregate(spec["blocks"], records)
    json_write(output / "summary.json", summary)
    all_completed = all(row["status"] == "completed" for row in records)
    final = {
        **initial, "status": "completed" if all_completed else "partial_or_failed",
        "finished_at_utc": now(), "runtime_recorded": runtime is not None,
        "setup_error": setup_error, "progress": progress,
        "elapsed_seconds_including_load": time.monotonic() - acquisition_started,
        "denominator": summary["denominator"],
        "cells_sha256": sha256(output / "cells.jsonl"), "summary_sha256": sha256(output / "summary.json"),
        "semantic_claim_supported": False,
    }
    json_write(output / "run_completed.json", final)
    return final


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="Bind local assets and tokenize; zero model forwards")
    prep.add_argument("--config", type=Path, required=True)
    prep.add_argument("--model-path", type=Path, required=True)
    prep.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("audit", help="Check the source/input-bound specification; zero model forwards")
    check.add_argument("--specification", type=Path, required=True)
    execute = commands.add_parser("run", help="Execute only after the PDF-first gate is verified externally")
    execute.add_argument("--specification", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--limit-cells", type=int, help="Explicit smoke subset; all other cells remain not_run")
    execute.add_argument("--acknowledge-development-only", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.config, args.model_path, args.output)
        elif args.command == "audit":
            spec = verify_specification(args.specification)
            result = {"status": "source_input_audit_pass", "denominator": spec["denominator"], "model_forwards": 0}
        else:
            result = run(args.specification, args.output, args.limit_cells)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result["status"] != "partial_or_failed" else 2
    except Exception as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
