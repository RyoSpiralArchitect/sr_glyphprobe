#!/usr/bin/env python3
"""Eight-input, at-most-56-forward numerical diagnostic; never a scientific n.

``prepare`` reads pinned saved records with stdlib only. ``run`` is a separate,
explicit action on the historical offline BF16 CUDA runtime. No tokenizer,
generation, new stimuli, retries, FP32 model fallback, or peer-process changes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
import hashlib
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "glyphprobe-contextual-emoji-prefix-consistency-v0"
ANALYSIS_PATH = "validation/contextual_emoji_measurement_v0/analysis.json"
ANALYSIS_SHA = "806400d78608cc2999f9480d3b82b24a45fd4739f85f52d82a21f3f7cb4b39e8"
ANALYZER_PATH = "scripts/analyze_contextual_emoji_measurement_v0.py"
ANALYZER_SHA = "f6337beb418b04fd2bbef675e6295739c5b5a72d28439549dea1a8a17c7cf59b"
BASE_PATH = "scripts/contextual_emoji_output_pilot_v0.py"
BASE_SHA = "ccce1d18b701708506b61fa20cc1724fed3dd4c44ebfcecde66b20c635944daa"
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
METHODS = ("original_a_1", "original_b_1", "original_a_2", "original_b_2",
           "padded_a", "padded_b", "prefix_only")
POLICY = {"gpu_index": 0, "allocator_cap_mib": 9728, "driver_allowance_mib": 512,
          "minimum_free_before_load_mib": 12288, "minimum_free_before_forward_mib": 4096,
          "walltime_seconds": 600, "maximum_forward_attempts": 56,
          "allow_other_pids": False, "change_peer_processes": False}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def safe(path):
    path = Path(path)
    require(path.name not in PROTECTED and path.resolve().name not in PROTECTED,
            "Protected historical target access prohibited")
    return path.resolve()


def digest(path):
    value = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def decode(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def read(path):
    return decode(safe(path).read_text(encoding="utf-8"))


def write(path, value):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def rows(path):
    lines = safe(path).read_text(encoding="utf-8").splitlines()
    require(lines and all(line.strip() for line in lines), "Empty or blank scientific record")
    return [decode(line) for line in lines]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, safe(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def identity(row):
    return tuple(row[k] for k in ("pair_id", "carrier", "block_id", "context", "cue"))


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_record(row):
    require(row.get("status") == "completed", "Incomplete historical record")
    p, c, full = row["prompt_token_ids"], row["candidate_token_ids"], row["input_token_ids"]
    require(p and c and full == p + c and len(full) <= 160 and
            all(type(t) is int and 0 <= t < 128256 for t in full), "Invalid recorded token IDs")
    require(row["prompt_token_count"] == len(p) and row["candidate_token_count"] == len(c)
            and row["first_candidate_predictor_position"] == len(p) - 1, "Recorded token boundaries differ")
    values = row["candidate_token_logprobs"]
    require(len(values) == len(c) and all(finite(v) and v <= 0 for v in values), "Invalid historical probabilities")
    require(finite(row["sequence_logprob_sum"]) and math.fsum(values) == row["sequence_logprob_sum"],
            "Historical score does not equal exact saved token sum")


def indexed_records(emoji, word, additional):
    result = {}
    for carrier, values in (("emoji", emoji), ("word", word), (None, additional)):
        for row in values:
            validate_record(row)
            if row["variant"] == "absent":
                require(carrier == "emoji", "Unexpected absent record")
                continue
            key = ("original" if carrier else row["pair_id"], carrier or row["carrier_kind"],
                   row["block_id"], row["context"], row["variant"], row["candidate"])
            require(key not in result, "Duplicate scientific cell")
            result[key] = row
    return result


def select_inputs(splits, indexed):
    """Outcome-selected engineering cases plus deterministic length controls."""
    by_id = {}
    for split in splits:
        key = identity(split)
        require(key not in by_id, "Duplicate candidate comparison input")
        require(finite(split["s_prefix"]), "Nonfinite prefix residual")
        require((*key, "a") in indexed and (*key, "b") in indexed, "Missing candidate comparison cell")
        a, b = indexed[(*key, "a")], indexed[(*key, "b")]
        require(a["prompt_token_ids"] == b["prompt_token_ids"], "Candidate prompts differ")
        n = split["shared_prefix_token_count"]
        require(type(n) is int and 0 < n <= min(a["candidate_token_count"], b["candidate_token_count"]),
                "A nonempty shared prefix is required")
        require(a["candidate_token_ids"][:n] == b["candidate_token_ids"][:n] == split["shared_prefix_token_ids"],
                "Shared token prefix differs")
        require(n == min(a["candidate_token_count"], b["candidate_token_count"]) or
                a["candidate_token_ids"][n] != b["candidate_token_ids"][n], "Shared prefix is not maximal")
        require(math.fsum(a["candidate_token_logprobs"][:n]) - math.fsum(b["candidate_token_logprobs"][:n])
                == split["s_prefix"], "Saved residual differs from raw scores")
        by_id[key] = split
    require(set(indexed) == {(*key, c) for key in by_id for c in ("a", "b")}, "Missing/extra input coverage")
    selected, reasons = [], []
    def take(pool, reason, ranked=False, deduplicate_maximum=False):
        available = list(pool) if deduplicate_maximum else [key for key in pool if key not in selected]
        require(available, f"No input available for {reason}")
        order = (lambda key: (-abs(by_id[key]["s_prefix"]), key)) if ranked else (lambda key: key)
        chosen = min(available, key=order)
        if chosen in selected:
            return
        selected.append(chosen)
        reasons.append(reason)
    for group in (("original", "emoji", "affect_01"), ("explicit_negation", "emoji", "affect_03"),
                  ("adjective_pair", "emoji", "thermal_04")):
        take([key for key in by_id if key[:3] == group], "named_group_max_abs_prefix_residual", True)
    take(by_id, "global_max_abs_prefix_residual", True, True)
    control_pools = [[key for key in by_id if key[1] == carrier and
        (indexed[(*key, "a")]["candidate_token_count"] == indexed[(*key, "b")]["candidate_token_count"]) == equal]
        for equal in (True, False) for carrier in ("emoji", "word")]
    for index, pool in enumerate(control_pools):
        take(pool, "equal_length_lexical_control" if index < 2 else "unequal_length_lexical_control")
    while len(selected) < 8:
        previous_count = len(selected)
        for pool in control_pools:
            if len(selected) < 8 and any(key not in selected for key in pool):
                take(pool, "stratified_lexicographic_fill_after_deduplication")
        require(len(selected) > previous_count, "No unused control available to fill eight inputs")
    result = []
    for key, reason in zip(selected, reasons):
        split = by_id[key]
        result.append({"input_id": "/".join(key), "identity": list(key), "selection_reason": reason,
            "historical_prefix_residual": split["s_prefix"],
            "shared_prefix_token_count": split["shared_prefix_token_count"],
            "shared_prefix_token_ids": split["shared_prefix_token_ids"],
            "candidates": {c: indexed[(*key, c)] for c in ("a", "b")}})
    require(len(result) == 8 and len({r["input_id"] for r in result}) == 8, "Exactly eight distinct inputs required")
    return result


def bound_file(root, entry):
    root = safe(root)
    relative = Path(entry["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "Only repository-relative inputs allowed")
    path = safe(root / relative)
    require(path.is_relative_to(root), "Input escaped repository")
    require(digest(path) == entry["sha256"], f"Pinned input differs: {relative}")
    return path


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def differences(left, right, path=()):
    """Retain exact before/after values; never apply a numerical tolerance."""
    if isinstance(left, dict) and isinstance(right, dict):
        require(set(left) == set(right), "Measurement replay keys differ")
        return [d for key in sorted(left) for d in differences(left[key], right[key], (*path, key))]
    if isinstance(left, list) and isinstance(right, list):
        require(len(left) == len(right), "Measurement replay lengths differ")
        return [d for index, (a, b) in enumerate(zip(left, right)) for d in differences(a, b, (*path, index))]
    return [] if left == right else [{"path": list(path), "before": left, "after": right}]


def auxiliary_squared_shift_replay(report):
    """Versioned full-report replay: d*d replaces **2 in one auxiliary field.

    The pinned historical report remains unchanged. This function defines a new
    reference representation rather than making the old reference approximate.
    All acquisition probabilities, H values, prefix diagnostics, other fields,
    and their exact comparisons are preserved.
    """
    result = json.loads(json.dumps(report, allow_nan=False))
    index = {(r["pair_id"], r["carrier"], r["block_id"]): r for r in result["decompositions"]}
    require(len(index) == len(result["decompositions"]) == 144, "Replay requires all 144 decomposition tables")
    require(len(result["coefficient_change_rows"]) == 144, "Replay requires all 144 coefficient-change rows")
    for row in result["coefficient_change_rows"]:
        a, b = [index[pair, row["carrier"], row["block_id"]] for pair in (row["pair_from"], row["pair_to"])]
        delta = [b["t"][c][v] - a["t"][c][v] for c in ("p", "q") for v in ("a", "b")]
        require(all(finite(d) for d in delta), "Nonfinite auxiliary replay input")
        row["mean_squared_cell_shift"] = math.fsum(d * d for d in delta) / 4
    return result


def require_auxiliary_only(changes):
    for change in changes:
        path = change["path"]
        require(len(path) == 3 and path[0] == "coefficient_change_rows" and type(path[1]) is int and
                0 <= path[1] < 144 and path[2] == "mean_squared_cell_shift" and
                finite(change["before"]) and finite(change["after"]),
                "Replay changed a field outside the declared auxiliary squared-shift field")


def load_measurement_replay(root):
    root = safe(root)
    require(digest(root / ANALYSIS_PATH) == ANALYSIS_SHA, "Measurement analysis pin differs")
    require(digest(root / ANALYZER_PATH) == ANALYZER_SHA, "Measurement analyzer pin differs")
    require(digest(root / BASE_PATH) == BASE_SHA, "Historical scoring implementation pin differs")
    saved = read(root / ANALYSIS_PATH)
    inputs = saved["provenance"]["inputs"]
    paths = {k: bound_file(root, v) for k, v in inputs.items()}
    analyzer = module(root / ANALYZER_PATH, "glyphprobe_prefix_measurement")
    fresh = json.loads(json.dumps(analyzer.analyze(root, paths["cells.jsonl"].parent, paths["specification"]), allow_nan=False))
    native_changes = differences(saved, fresh)
    require_auxiliary_only(native_changes)
    portable = auxiliary_squared_shift_replay(fresh)
    require(portable == auxiliary_squared_shift_replay(saved), "Full deterministic multiplication replay differs")
    changes = differences(saved, portable)
    require_auxiliary_only(changes)
    payload = {"protocol_id": "glyphprobe-measurement-portable-squared-shift-replay-v1",
        "parent_analysis_sha256": ANALYSIS_SHA, "parent_analyzer_sha256": ANALYZER_SHA,
        "replay_implementation_sha256": digest(Path(__file__)),
        "operation": "For each coefficient-change row only: mean_squared_cell_shift = math.fsum(d*d for four binary64 contextual-score differences)/4; all other fields unchanged",
        "parent_artifact_modified": False, "model_probability_tolerance": 0,
        "all_other_fields_exactly_equal_to_parent": True,
        "changes_from_parent": changes, "analysis": portable}
    native_receipt = {"protocol_id": "glyphprobe-measurement-native-replay-portability-diagnostic-v1",
        "parent_analysis_sha256": ANALYSIS_SHA,
        "portable_reference_sha256": hashlib.sha256(json_bytes(payload)).hexdigest(),
        "native_replay_exactly_equals_parent": not native_changes,
        "native_replay_differences_from_parent": native_changes,
        "differences_confined_to_declared_auxiliary_field": True,
        "full_deterministic_replay_exactly_equals_portable_reference": True,
        "native_analysis_json_sha256": hashlib.sha256(json_bytes(fresh)).hexdigest(),
        "python": sys.version, "platform": platform.platform(),
        "causal_source_of_native_difference": "not_isolated; native power expression and deterministic multiplication use different operation definitions"}
    return saved, paths, payload, native_receipt


def design(root, portable_reference=None):
    root = safe(root)
    saved, paths, replay, _ = load_measurement_replay(root)
    inputs = saved["provenance"]["inputs"]
    index = indexed_records(rows(paths["emoji_cells"]), rows(paths["word_cells"]), rows(paths["cells.jsonl"]))
    require(len(index) == 1152 and len(saved["candidate_prefix_tail"]["input_splits"]) == 576,
            "Historical denominator differs")
    old, wording = read(paths["emoji_spec"]), read(paths["specification"])
    sources = dict(inputs)
    for name, relative, pin in (("measurement", ANALYSIS_PATH, ANALYSIS_SHA),
            ("measurement_analyzer", ANALYZER_PATH, ANALYZER_SHA), ("baseline_helper", BASE_PATH, BASE_SHA),
            ("model_provenance", "src/glyphprobe/provenance.py", wording["source_files"]["model_provenance"]["sha256"]),
            ("io", "src/glyphprobe/io.py", wording["source_files"]["io"]["sha256"]),
            ("runner", "scripts/contextual_emoji_prefix_consistency_v0.py", digest(Path(__file__)))):
        sources[name] = {"path": relative, "sha256": pin}
        bound_file(root, sources[name])
    replay_entry = {"path": None, "sha256": hashlib.sha256(json_bytes(replay)).hexdigest()}
    if portable_reference is not None:
        reference_path = safe(portable_reference)
        require(reference_path.is_relative_to(root), "Portable reference must be inside repository")
        replay_entry["path"] = str(reference_path.relative_to(root))
        bound_file(root, replay_entry)
        require(read(reference_path) == replay, "Full portable replay reference differs")
        sources["portable_measurement_reference"] = replay_entry
    return {"protocol_id": PROTOCOL, "schema_version": 2,
        "preflight_revision": "portable_deterministic_auxiliary_squared_shift_v1",
        "portable_measurement_reference": replay_entry,
        "status": "prepared_engineering_diagnostic_not_scientific_replication",
        "selection": "posthoc_max_residual_cases_and_lexicographic_length_controls",
        "claim_ceiling": "numerical_path_consistency_only_no_block_H_or_population_verdict",
        "new_stimuli": 0, "new_scientific_n": 0, "tokenizer_calls": 0,
        "generation_calls": 0, "downloads": 0, "prepare_model_forwards": 0,
        "planned_inputs": 8, "planned_forward_attempts": 56, "methods": list(METHODS),
        "compute_policy": dict(POLICY), "source_files": sources,
        "model_path": old["model_path"], "model_artifact": old["model_artifact"],
        "runtime_packages": old["runtime_packages"], "python_version": old["python_version"],
        "historical_runtime": read(paths["runtime"]),
        "scoring": {"dtype": "bfloat16", "attention": "eager", "use_cache": False,
            "seed": 2026100701, "num_threads": 4, "log_softmax_dtype": "float32",
            "historical_parity_tolerance": 0, "same_shape_prefix_tolerance": 0,
            "original_kwargs": "input_ids,attention_mask=ones_like,use_cache=False; implicit positions",
            "padded_kwargs": "right pad token 0; 1 real/0 pad mask; absolute position_ids 0..L-1",
            "padded_normalization": "common rectangle [prompt_length-1:common_total_length-1] before valid-token gather",
            "prefix_only": "prompt plus shared prefix; original kwargs; descriptive cross-shape comparison",
            "same_shape_gate": "exact shared predictor logits hash AND every prefix logprob",
            "changed_geometry_historical_total_parity_required": False},
        "inputs": select_inputs(saved["candidate_prefix_tail"]["input_splits"], index)}


def prepare(root, output):
    root, output = safe(root), safe(output)
    require(not safe(output).exists(), "Refusing to overwrite specification")
    require(output.is_relative_to(root), "Prepared output must be inside repository for portable source binding")
    reference = output.with_name("measurement_portable_replay.json")
    require(not reference.exists(), "Refusing to overwrite portable measurement reference")
    _, _, replay, _ = load_measurement_replay(root)
    write(reference, replay)
    spec = {"created_at_utc": now(), **design(root, reference)}
    write(output, spec)
    return spec


def verify_specification(path, root=ROOT):
    spec = read(path)
    require(isinstance(spec.get("created_at_utc"), str), "Missing preparation timestamp")
    entry = spec.get("portable_measurement_reference", {})
    require(isinstance(entry.get("path"), str), "Missing portable replay reference")
    reference = bound_file(safe(root), entry)
    require({k: v for k, v in spec.items() if k != "created_at_utc"} == design(root, reference),
            "Specification changed after preparation")
    return spec


def call_geometry(case, method):
    require(method in METHODS, "Unplanned forward method")
    candidate = "b" if method.startswith(("original_b", "padded_b")) else "a"
    record = case["candidates"][candidate]
    ids = list(record["input_token_ids"])
    prompt = record["prompt_token_count"]
    prefix = case["shared_prefix_token_count"]
    if method == "prefix_only":
        ids = ids[:prompt + prefix]
    valid = len(ids)
    total = max(len(c["input_token_ids"]) for c in case["candidates"].values()) if method.startswith("padded") else valid
    return {"input_token_ids": ids + [0] * (total - valid),
        "attention_mask": [1] * valid + [0] * (total - valid),
        "position_ids": list(range(total)) if method.startswith("padded") else None,
        "valid_length": valid, "total_length": total, "prompt_length": prompt,
        "candidate_token_ids": ids[prompt:], "predictor_positions": list(range(prompt - 1, valid - 1)),
        "normalization_start": prompt - 1, "normalization_stop": total - 1,
        "shared_prefix_token_count": prefix}


def plans(cases):
    require(len(cases) == 8 and len({c["input_id"] for c in cases}) == 8, "Eight unique inputs required")
    return [{"event_id": f"{c['input_id']}::{method}", "input_id": c["input_id"], "method": method,
             "geometry": call_geometry(c, method)} for c in cases for method in METHODS]


def query_xml():
    return subprocess.run(["nvidia-smi", "-q", "-x"], capture_output=True, text=True,
                          check=True, timeout=5).stdout


def resource_guard(before_load=False, query=query_xml, emit=None, pid=None):
    """Inspect all reported GPU process rows, including graphics processes."""
    observation = {"observed_at_utc": now(), "phase": "before_load" if before_load else "forward_boundary",
                   "own_pid": os.getpid() if pid is None else pid, "status": "blocked"}
    try:
        tree = ET.fromstring(query())
        gpus = tree.findall("gpu")
        require(len(gpus) == 1, "Exactly one observed GPU required")
        gpu = gpus[0]
        def mib(text):
            fields = (text or "").strip().split()
            require(len(fields) == 2 and fields[0].isdigit() and fields[1] == "MiB", "Unparseable GPU memory")
            return int(fields[0])
        total = mib(gpu.findtext("fb_memory_usage/total"))
        free = mib(gpu.findtext("fb_memory_usage/free"))
        processes = {}
        require(gpu.find("processes") is not None, "GPU process inventory unavailable")
        for row in gpu.findall("processes/process_info"):
            raw_pid = (row.findtext("pid") or "").strip()
            require(raw_pid.isdigit() and int(raw_pid) not in processes, "Invalid/duplicate GPU process PID")
            processes[int(raw_pid)] = mib(row.findtext("used_memory"))
        peers = sorted(set(processes) - {observation["own_pid"]})
        minimum = POLICY["minimum_free_before_load_mib" if before_load else "minimum_free_before_forward_mib"]
        observation.update(total_mib=total, free_mib=free, minimum_free_mib=minimum,
            own_process_mib=processes.get(observation["own_pid"], 0), observed_peer_pids=peers,
            process_memory_mib={str(k): v for k, v in processes.items()})
        require(not peers, f"Other GPU PID present: {peers}")
        require(0 < total and 0 <= free <= total, "Invalid free/total VRAM")
        require(free >= minimum, f"Free VRAM {free} MiB below {minimum} MiB")
        require(observation["own_process_mib"] <= POLICY["allocator_cap_mib"] + POLICY["driver_allowance_mib"],
                "Own process exceeded total 10 GiB allowance")
        observation["status"] = "allowed"
    except BaseException as exc:
        observation["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if emit:
            emit(observation)
    return observation


def runtime_identity(torch, model, base):
    return json.loads(json.dumps({"python": sys.version, "platform": platform.platform(),
        "packages": base.package_versions(), "torch": torch.__version__, "cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(), "device": torch.cuda.get_device_name(0),
        "device_capability": list(torch.cuda.get_device_capability(0)),
        "model_class": type(model).__name__, "model_config": model.config.to_dict(),
        "parameters": sum(p.numel() for p in model.parameters()), "dtype": "bfloat16", "attention": "eager", "use_cache": False,
        "model_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model).forward).encode()).hexdigest(),
        "attention_forward_source_sha256": hashlib.sha256(inspect.getsource(type(model.model.layers[0].self_attn).forward).encode()).hexdigest(),
        "local_files_only": True, "trust_remote_code": False, "download": False,
        "generation_calls": 0, "route_instrumented": False}, allow_nan=False))


def load_model(spec, observe, emit_runtime, emit_implementation, deadline, resources):
    base = module(ROOT / BASE_PATH, "glyphprobe_prefix_baseline")
    require(base.package_versions() == spec["runtime_packages"] and
            platform.python_version() == spec["python_version"], "Historical package/Python identity differs")
    require(base.artifact_receipt(Path(spec["model_path"])) == spec["model_artifact"], "Model artifact identity differs")
    deadline()
    observe(True, boundary="preload")
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    import torch
    from transformers import AutoModelForCausalLM
    resources["torch"] = torch
    require(torch.cuda.is_available() and torch.cuda.is_bf16_supported(), "Historical BF16 CUDA required")
    torch.set_num_threads(4)
    torch.manual_seed(2026100701)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(POLICY["allocator_cap_mib"] * 2**20 / total, 0)
    model = AutoModelForCausalLM.from_pretrained(spec["model_path"], local_files_only=True,
        trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="eager").eval()
    resources["model"] = model
    require({p.dtype for p in model.parameters()} == {torch.bfloat16}, "Unexpected parameter dtype")
    runtime = runtime_identity(torch, model, base)
    emit_runtime(runtime)
    from transformers import masking_utils
    source_paths = {"modeling_llama": Path(inspect.getfile(type(model))),
                    "masking_utils": Path(inspect.getfile(masking_utils))}
    emit_implementation({"files": {name: {"path": str(path), "sha256": digest(path)}
                        for name, path in source_paths.items()},
                        "separate_from_historical_core_runtime": True})
    require(runtime == spec["historical_runtime"], "Full historical runtime identity differs")
    deadline()
    observe(True, boundary="before_allocation")
    model.to("cuda")
    torch.cuda.synchronize()
    observe(False, boundary="after_allocation")
    deadline()
    torch.cuda.reset_peak_memory_stats()
    return torch, model, base


def score_call(torch, model, base, case, event, device="cuda"):
    geometry = event["geometry"]
    ids = torch.tensor([geometry["input_token_ids"]], dtype=torch.long, device=device)
    mask = torch.tensor([geometry["attention_mask"]], dtype=torch.long, device=device)
    kwargs = {"input_ids": ids, "attention_mask": mask, "use_cache": False}
    if geometry["position_ids"] is not None:
        kwargs["position_ids"] = torch.tensor([geometry["position_ids"]], dtype=torch.long, device=device)
    started = time.monotonic()
    with torch.inference_mode():
        output = model(**kwargs)
        logits = output.logits
        require(tuple(logits.shape[:2]) == (1, geometry["total_length"]), "Unexpected logits geometry")
        if event["method"].startswith("padded"):
            # Both candidates normalize the same rectangle, even when the valid
            # candidate lengths differ. Padded targets are never scored.
            rectangle = logits[0, geometry["normalization_start"]:geometry["normalization_stop"]].float()
            logprobs = torch.log_softmax(rectangle, dim=-1)
            targets = torch.tensor(geometry["candidate_token_ids"], dtype=torch.long, device=device)
            values = [float(v) for v in logprobs[:len(targets)].gather(-1, targets[:, None]).squeeze(-1).cpu().tolist()]
        else:
            # Byte-for-byte same arithmetic path as the historical scorer.
            values = base.score_logits(logits, geometry["input_token_ids"], geometry["prompt_length"])
        start, n = geometry["prompt_length"] - 1, case["shared_prefix_token_count"]
        shared = logits[0, start:start + n].float().contiguous().cpu()
        require(bool(torch.isfinite(shared).all()), "Nonfinite shared predictor logits")
        shared_hash = hashlib.sha256(shared.numpy().tobytes(order="C")).hexdigest()
    if device == "cuda":
        torch.cuda.synchronize()
    return {"candidate_token_logprobs": values, "sequence_logprob_sum": math.fsum(values),
        "shared_prediction_logits_sha256": shared_hash, "shared_prediction_logits_shape": list(shared.shape),
        "shared_prediction_logits_dtype": "float32", "logits_hash_byte_order": sys.byteorder,
        "normalization_rectangle_shape": [geometry["normalization_stop"] - geometry["normalization_start"], logits.shape[-1]],
        "elapsed_seconds": time.monotonic() - started}


def validate_score(score, event):
    values = score["candidate_token_logprobs"]
    require(len(values) == len(event["geometry"]["candidate_token_ids"]) and
            all(finite(v) and v <= 0 for v in values), "Invalid scored probabilities")
    require(finite(score["sequence_logprob_sum"]) and math.fsum(values) == score["sequence_logprob_sum"],
            "Scored token sum mismatch")
    require(score["shared_prediction_logits_shape"][0] == event["geometry"]["shared_prefix_token_count"] and
            score["shared_prediction_logits_dtype"] == "float32" and
            len(score["shared_prediction_logits_sha256"]) == 64, "Invalid shared predictor logit receipt")


def original_matches(case, event, score):
    candidate = "b" if event["method"].startswith("original_b") else "a"
    expected = case["candidates"][candidate]
    return (score["candidate_token_logprobs"] == expected["candidate_token_logprobs"] and
            score["sequence_logprob_sum"] == expected["sequence_logprob_sum"])


def execute(cases, scorer, before, after, emit, deadline, initial_error=None):
    """Bounded pure orchestration, injectable for CPU-only refusal-path tests."""
    planned = plans(cases)
    by_id = {c["input_id"]: c for c in cases}
    records, attempted, blocked = [], 0, initial_error
    for event in planned:
        row = {**event, "status": "not_run", "forward_attempted": False}
        if blocked is not None:
            row["reason"] = blocked
        else:
            try:
                deadline()
                before(event)
                require(attempted < 56, "Forward-attempt cap reached")
                attempted += 1
                row["forward_attempted"] = True
                score = scorer(by_id[event["input_id"]], event)
                validate_score(score, event)
                row.update(score, status="completed")
                if event["method"].startswith("original"):
                    row["historical_exact_parity"] = original_matches(by_id[event["input_id"]], event, score)
                    require(row["historical_exact_parity"], "Original historical/repeat exact parity failed")
                    if event["method"].endswith("_2"):
                        previous_id = event["event_id"][:-1] + "1"
                        previous = next(r for r in records if r["event_id"] == previous_id)
                        require(previous["shared_prediction_logits_sha256"] == row["shared_prediction_logits_sha256"],
                                "Repeated original predictor logits changed")
                after(event)
                deadline()
            except BaseException as exc:
                blocked = f"{type(exc).__name__}: {exc}"
                if row["status"] == "completed":
                    row["boundary_error_after_score"] = blocked
                else:
                    row["status"] = "failed" if row["forward_attempted"] else "not_run"
                    row["reason"] = blocked
        row["recorded_at_utc"] = now()
        records.append(row)
        emit(row)
    return records, attempted, blocked


def evaluate(cases, records):
    planned = plans(cases)
    require(len(records) == 56 and [r["event_id"] for r in records] == [r["event_id"] for r in planned],
            "Planned 56-event denominator or ordering changed")
    for expected, row in zip(planned, records):
        require(all(row.get(k) == expected[k] for k in ("input_id", "method", "geometry")),
                "Recorded forward geometry differs from plan")
        require(row["status"] in ("completed", "failed", "not_run") and type(row["forward_attempted"]) is bool,
                "Invalid forward status")
        require(row["forward_attempted"] == (row["status"] != "not_run"), "Attempt/status mismatch")
        if row["status"] == "completed":
            validate_score(row, expected)
        else:
            require("candidate_token_logprobs" not in row and "sequence_logprob_sum" not in row,
                    "Uncompleted event carries probabilities")
    diagnostics = []
    for case in cases:
        r = {row["method"]: row for row in records if row["input_id"] == case["input_id"]}
        result = {"input_id": case["input_id"], "historical_exact_parity": None,
                  "repeated_original_exact_equality": None, "padded_prefix_exact_equality": None,
                  "padded_predictor_logits_exact_equality": None}
        if all(r[m]["status"] == "completed" for m in METHODS[:4]):
            result["historical_exact_parity"] = all(original_matches(case, r[m], r[m]) for m in METHODS[:4])
            result["repeated_original_exact_equality"] = all(
                r[f"original_{c}_1"]["candidate_token_logprobs"] == r[f"original_{c}_2"]["candidate_token_logprobs"] and
                r[f"original_{c}_1"]["shared_prediction_logits_sha256"] == r[f"original_{c}_2"]["shared_prediction_logits_sha256"]
                for c in ("a", "b"))
        n = case["shared_prefix_token_count"]
        if r["padded_a"]["status"] == r["padded_b"]["status"] == "completed":
            a, b = r["padded_a"], r["padded_b"]
            result["padded_prefix_exact_equality"] = a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n]
            result["padded_predictor_logits_exact_equality"] = (
                a["shared_prediction_logits_sha256"] == b["shared_prediction_logits_sha256"] and
                a["shared_prediction_logits_shape"] == b["shared_prediction_logits_shape"])
            result["padded_prefix_max_absolute_logprob_difference"] = max(abs(x - y) for x, y in zip(
                a["candidate_token_logprobs"][:n], b["candidate_token_logprobs"][:n]))
        result["full_score_geometry_comparison"] = None
        if all(r[m]["status"] == "completed" for m in ("original_a_1", "original_b_1", "padded_a", "padded_b")):
            original_s = r["original_a_1"]["sequence_logprob_sum"] - r["original_b_1"]["sequence_logprob_sum"]
            padded_s = r["padded_a"]["sequence_logprob_sum"] - r["padded_b"]["sequence_logprob_sum"]
            def preference(value):
                return "a" if value > 0 else "b" if value < 0 else "tie"
            result["full_score_geometry_comparison"] = {
                "s_original": original_s, "s_padded": padded_s,
                "original_preferred_candidate": preference(original_s),
                "padded_preferred_candidate": preference(padded_s),
                "preference_or_tie_changed": preference(original_s) != preference(padded_s),
                "strict_nonzero_polarity_flip": original_s * padded_s < 0,
                "same_candidate_max_absolute_logprob_difference": {c: max(abs(x-y) for x,y in zip(
                    r[f"original_{c}_1"]["candidate_token_logprobs"], r[f"padded_{c}"]["candidate_token_logprobs"])) for c in ("a", "b")},
                "descriptive_only_not_corrected_scores_or_H_verdict": True}
        result["cross_shape_descriptive_comparisons"] = []
        for left, right in (("original_a_1", "original_b_1"), ("original_a_1", "padded_a"),
                            ("original_b_1", "padded_b"), ("original_a_1", "prefix_only"),
                            ("original_b_1", "prefix_only"), ("padded_a", "prefix_only")):
            a, b = r[left], r[right]
            if a["status"] == b["status"] == "completed":
                result["cross_shape_descriptive_comparisons"].append({"left": left, "right": right,
                    "prefix_logprobs_exact_equal": a["candidate_token_logprobs"][:n] == b["candidate_token_logprobs"][:n],
                    "prefix_max_absolute_logprob_difference": max(abs(x-y) for x,y in zip(
                        a["candidate_token_logprobs"][:n], b["candidate_token_logprobs"][:n])),
                    "shared_predictor_logits_exact_equal": a["shared_prediction_logits_sha256"] == b["shared_prediction_logits_sha256"],
                    "not_a_historical_total_parity_gate": True})
        diagnostics.append(result)
    gates = ("historical_exact_parity", "repeated_original_exact_equality", "padded_prefix_exact_equality",
             "padded_predictor_logits_exact_equality")
    completed = all(r["status"] == "completed" for r in records)
    boundaries_admissible = not any("boundary_error_after_score" in r for r in records)
    return {"input_diagnostics": diagnostics, "all_56_scores_completed": completed,
        "all_scored_boundaries_admissible": boundaries_admissible,
        "numerical_gate_passed": completed and boundaries_admissible and all(d[g] is True for d in diagnostics for g in gates),
        "block_H_recomputed": False, "scientific_population_verdict": None,
        "claim_ceiling": "eight outcome-selected engineering inputs; no corrected scientific scores or causal attribution"}


def run(spec_path, output):
    output = safe(output)
    require(not output.exists(), "Refusing to reuse a run directory")
    # Full source/spec/raw validation precedes model import, allocation, or writes.
    spec = verify_specification(spec_path)
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    _, _, _, native_receipt = load_measurement_replay(ROOT)
    write(output / "run_started.json", {"started_at_utc": now(), "pid": os.getpid(), "protocol_id": PROTOCOL,
        "specification_sha256": digest(spec_path), "actual_source_files": spec["source_files"],
        "planned_forward_attempts": 56, "compute_policy": POLICY,
        "measurement_native_replay_portability": native_receipt})
    observations = []
    def deadline():
        require(time.monotonic() - started < 600, "600-second walltime budget exhausted")
    def observe(before_load=False, event=None, boundary=None):
        def record(observation):
            observations.append({**observation, "event_id": event["event_id"] if event else None,
                "boundary": boundary or ("preload" if before_load else "after_allocation")})
        return resource_guard(before_load=before_load, emit=record)
    def runtime_emit(runtime):
        write(output / "runtime.json", runtime)
    def implementation_emit(value):
        write(output / "implementation_sources.json", value)
    def alarm(signum, frame):
        raise TimeoutError("600-second process walltime alarm")
    old_alarm = signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 600)
    torch = model = base = None
    resources = {}
    load_error, records, attempts, error = None, [], 0, None
    try:
        try:
            observe(True)
            torch, model, base = load_model(spec, observe, runtime_emit, implementation_emit, deadline, resources)
        except BaseException as exc:
            load_error = f"{type(exc).__name__}: {exc}"
        with (output / "forwards.jsonl").open("x", encoding="utf-8") as handle:
            def emit(row):
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            records, attempts, error = execute(spec["inputs"],
                lambda case, event: score_call(torch, model, base, case, event),
                lambda event: observe(False, event, "before"),
                lambda event: observe(False, event, "after"), emit, deadline, load_error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_alarm)
        # No signal, priority, pause, or memory operation targets another PID.
        peak = None
        torch = resources.get("torch", torch)
        if torch is not None and torch.cuda.is_initialized():
            peak = {"allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
                    "reserved_mib": torch.cuda.max_memory_reserved() / 2**20}
            model = None
            resources.pop("model", None)
            gc.collect()
            torch.cuda.empty_cache()
        write(output / "occupancy_checks.json", {"observations": observations,
            "maximum_observed_own_process_mib": max((o.get("own_process_mib", 0) for o in observations), default=0)})
    analysis = evaluate(spec["inputs"], records)
    write(output / "diagnostics.json", analysis)
    summary = {"protocol_id": PROTOCOL, "finished_at_utc": now(),
        "status": "completed_numerical_gate_passed" if analysis["numerical_gate_passed"] and error is None else
                  "stopped_partial" if error is not None else "completed_numerical_gate_failed",
        "forward_attempts": attempts, "planned_forward_attempts": 56,
        "status_counts": dict(Counter(r["status"] for r in records)), "stop_reason": error,
        "elapsed_seconds": time.monotonic() - started, "peak_torch_memory_mib": peak,
        "full_runtime_identity_matches_historical": read(output / "runtime.json") == spec["historical_runtime"] if
            (output / "runtime.json").exists() else False,
        "new_scientific_n": 0, "block_H_recomputed": False, "new_stimuli": 0,
        "tokenizer_calls": 0, "generation_calls": 0, "downloads": 0,
        "numerical_gate_passed": analysis["numerical_gate_passed"],
        "artifacts": {name: digest(output / name) for name in
            ("forwards.jsonl", "diagnostics.json", "occupancy_checks.json", "run_started.json")}}
    if (output / "runtime.json").exists():
        summary["artifacts"]["runtime.json"] = digest(output / "runtime.json")
    if (output / "implementation_sources.json").exists():
        summary["artifacts"]["implementation_sources.json"] = digest(output / "implementation_sources.json")
    write(output / "run_completed.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--specification", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        spec = prepare(args.root, args.output)
        result = {"status": spec["status"], "specification_sha256": digest(args.output),
                  "inputs": [i["input_id"] for i in spec["inputs"]], "planned_forward_attempts": 56,
                  "model_forwards": 0, "tokenizer_calls": 0}
    else:
        result = run(args.specification, args.output)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0 if args.command == "prepare" or result["status"] == "completed_numerical_gate_passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
