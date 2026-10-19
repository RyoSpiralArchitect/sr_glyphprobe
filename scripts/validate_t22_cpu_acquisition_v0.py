#!/usr/bin/env python3
"""Read-only audit of stored T22 CPU arrays; no runner imports/model forwards.

This checks persisted readouts and attention, not omitted full hidden tensors,
stock/idle comparisons, or old/new donor-capture pairs. Their acquisition-time
checks remain source-bound claims, explicitly reported separately below.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

PROTOCOL = "glyphprobe-t22-kv-cpu-engineering-canary-v0"
CHECKS = {
    "stock_historical_exact", "stock_t22_exact", "donor_and_reset_captures_exact",
    "same_cpu_legacy_kv_full_hidden_states_exact",
    "same_cpu_legacy_neutral_full_hidden_states_exact",
    "same_slot_no_op_and_roundtrip_exact", "local_v_attention_weights_unchanged",
    "nonreadout_attention_outputs_unchanged", "complete_actual_attention_diagnostics",
}
SOURCE_FILES = {
    "scripts/t22_kv_cpu_canary_v0.py", "scripts/t22_kv_dissection_v0.py",
    "scripts/t21_glyph_context_path_pilot_v0.py", "tests/test_t22_kv_cpu_canary_v0.py",
    "src/glyphprobe/provenance.py", "configs/t21_glyph_context_path_pilot_v0.yaml",
    "validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json",
    "validation/t21_glyph_context_path_confirmation_v0/canary_specification.json",
}
MODEL_FILES = {".gitattributes", "README.md", "config.json", "model-00001-of-00002.safetensors",
               "model-00002-of-00002.safetensors", "model.safetensors.index.json",
               "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json"}
DIMS = {"layers": 28, "hidden_size": 3072, "attention_heads": 24, "kv_heads": 8, "head_dim": 128}
CARRIERS = ("pipe", "article_a")
OPERATIONS = ("none", "k", "v", "kv")
CONDITIONS = ("intact", "reset", "intact_glyph_donor", "intact_suffix_donor",
              "reset_glyph_donor", "reset_suffix_donor", "reset_prefix_donor",
              "reset_prefix_restore_glyph", "reset_prefix_restore_suffix", "reset_roundtrip", "no_op")


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def no_duplicates(pairs):
    value = {}
    for key, entry in pairs:
        check(key not in value, f"Duplicate JSON key: {key}")
        value[key] = entry
    return value


def read(path):
    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates,
                       parse_constant=reject_constant)
    check(isinstance(value, dict), f"Not an object: {path.name}")
    return value


def extension_rows(length):
    return [(operation, position, donor) for operation in OPERATIONS
            for position in ("glyph", "suffix") for donor in range(2)]


def array_schema(tokens, dims=DIMS):
    length = len(tokens["raw"]["glyph"]) + 8
    codepoint_length = len(tokens["raw"]["codepoint_literal"]) + 8
    width, heads = dims["hidden_size"], dims["attention_heads"]
    shapes = {
        "stock_hidden": (length, width), "codepoint_hidden": (codepoint_length, width),
        "reset_states": (2, 2, width),
        "donor_keys": (2, 6, dims["kv_heads"], length, dims["head_dim"]),
        "donor_values": (2, 6, dims["kv_heads"], length, dims["head_dim"]),
        "extension": (16, width), "extension_neutral": (16, width),
        "attention_weights": (2, 6, 16, heads, length),
        "attention_baseline_weights": (2, 6, 16, heads, length),
        "attention_selected_mask": (2, 6, 16, length),
    }
    for name in ("historical", "historical_neutral", "t22", "t22_neutral"):
        shapes["legacy_" + name] = (88, width)
    for name in ("selected_mass", "glyph_mass", "suffix_mass"):
        shapes["attention_" + name] = (2, 6, 16, heads)
    schema = {f"{carrier}_{name}": {"shape": list(shape), "dtype": "bool" if name == "attention_selected_mask" else "float32"}
              for carrier in CARRIERS for name, shape in shapes.items()}
    check(len(schema) == 34, "Independent schema must contain 34 arrays")
    return schema


def validate_arrays(arrays, tokens, dims=DIMS):
    expected = array_schema(tokens, dims)
    check(len(arrays.files) == 34 and set(arrays.files) == set(expected), "NPZ must contain exactly all 34 arrays")
    glyph_length = len(tokens["raw"]["glyph"])
    seq_length = glyph_length + 8
    p = glyph_length + 7
    for name, metadata in expected.items():
        value = arrays[name]
        check(list(value.shape) == metadata["shape"], f"Shape mismatch: {name}")
        check(str(value.dtype) == metadata["dtype"], f"Dtype mismatch: {name}")
        check(np.isfinite(value).all(), f"Nonfinite values: {name}")
        if metadata["dtype"] == "float32" and not name.endswith("_mass"):
            check(((value.view(np.uint32) & np.uint32(65535)) == 0).all(), f"Non-BF16-representable saved values: {name}")
    for carrier in CARRIERS:
        a = lambda label: arrays[f"{carrier}_{label}"]
        check(np.array_equal(a("legacy_historical"), a("legacy_t22")), "Old/new CPU legacy readouts differ")
        check(np.array_equal(a("legacy_historical_neutral"), a("legacy_t22_neutral")), "Old/new CPU neutral readouts differ")
        for row, condition in enumerate(CONDITIONS * 8):
            if condition in ("intact", "reset", "reset_roundtrip", "no_op"):
                check(np.array_equal(a("legacy_historical")[row], a("legacy_historical_neutral")[row]), f"Legacy no-op/roundtrip readout differs: row {row}")
        weights, baseline = a("attention_weights"), a("attention_baseline_weights")
        check((weights >= 0).all() and (weights <= 1).all()
              and (baseline >= 0).all() and (baseline <= 1).all(), "Attention weights outside [0,1]")
        check(np.allclose(weights.sum(axis=-1, dtype=np.float32), 1.0, rtol=0.0, atol=0.004)
              and np.allclose(baseline.sum(axis=-1, dtype=np.float32), 1.0, rtol=0.0, atol=0.004), "Attention probability sums exceed BF16 rounding tolerance")
        check(np.array_equal(weights[1], baseline[1]), "Neutral attention differs from its local baseline")
        selected_mask = np.zeros((2, 6, 16, seq_length), dtype=bool)
        for index, (operation, position, donor) in enumerate(extension_rows(glyph_length)):
            positions = np.arange(glyph_length) if position == "glyph" else np.arange(p - glyph_length, p)
            selected_mask[0, :, index, positions] = True
            if operation in ("none", "v"):
                check(np.array_equal(weights[0, :, index], baseline[0, :, index]), f"Local {operation} weights changed")
            if operation == "none":
                check(np.array_equal(a("extension")[index], a("extension_neutral")[index]), "Reference readout is not a no-op")
        check(np.array_equal(selected_mask, a("attention_selected_mask")), "Selected-position mask differs from independent geometry")
        for name, positions in (("selected", None), ("glyph", np.arange(glyph_length)), ("suffix", np.arange(p - glyph_length, p))):
            mass_mask = selected_mask if positions is None else np.zeros_like(selected_mask)
            if positions is not None:
                mass_mask[..., positions] = True
            reconstructed = (weights * mass_mask[..., None, :]).sum(axis=-1, dtype=np.float32)
            check(np.array_equal(reconstructed, a("attention_" + name + "_mass")), f"{name} attention mass reconstruction failed")
    return {"array_count": 34, "glyph_token_count": glyph_length, "sequence_length": seq_length,
            "legacy_and_neutral_readouts_exact": True, "legacy_no_op_and_roundtrip_readouts_exact": True,
            "reference_extension_readouts_exact": True, "local_none_and_v_weights_exact": True,
            "neutral_weights_exact": True, "specified_selected_masks_exact": True,
            "all_three_float32_attention_mass_reconstructions_exact": True,
            "non_mass_saved_float32_values_bf16_representable": True}


def boundary(value, fields):
    for field in fields:
        check(value.get(field) is False, f"Claim boundary changed: {field}")
    check(value.get("protected_bank_reads") == 0 and value.get("generation_calls") == 0, "Forbidden acquisition activity claimed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--expected-items", type=int, choices=(1, 8))
    parser.add_argument("--expected-acquisition-sha256")
    parser.add_argument("--model-path", type=Path, help="Optional complete independent rehash of all nine model files")
    parser.add_argument("--output", type=Path, help="Write a new JSON report exclusively")
    args = parser.parse_args()
    repo, root = args.repo.resolve(), args.run.resolve()
    acquisition_path, specification_path = root / "acquisition_receipt.json", root / "specification.json"
    acquisition, specification = read(acquisition_path), read(specification_path)
    acquisition_hash, specification_hash = sha(acquisition_path), sha(specification_path)
    if args.expected_acquisition_sha256:
        check(acquisition_hash == args.expected_acquisition_sha256, "External acquisition hash mismatch")
    check(acquisition["protocol_id"] == PROTOCOL and specification["protocol_id"] == PROTOCOL, "Protocol identity mismatch")
    check(acquisition["specification_sha256"] == specification_hash, "Acquisition→spec hash mismatch")
    count = specification["target_count"]
    check(count in (1, 8) and acquisition["target_items"] == count, "Unsupported or inconsistent item count")
    if args.expected_items:
        check(count == args.expected_items, "Unexpected item count")
    expected_stage = "cpu_engineering_timing_pilot" if count == 1 else "cpu_engineering_canary"
    check(specification["stage"] == expected_stage and acquisition["status"] == expected_stage + "_complete", "Invalid completion status")
    check(specification["eligible_target_count"] == 8 and specification["model_dimensions"] == DIMS, "Pinned eligibility or model geometry changed")
    check(specification["carriers"] == list(CARRIERS) and specification["anchor"] == 21
          and specification["distance"] == 8 and specification["active_blocks"] == list(range(22, 28)), "T22 geometry changed")
    check(specification["attention_mass_accumulation"] == "float32_from_recorded_actual_weights", "Mass precision changed")
    check(specification["legacy_rows"] == "original_88_rows_unchanged" and specification["extension_rows"] == "operation_then_position_then_donor_16_rows_separate_batch", "Batch layout changed")
    expected_false = ("scientific_result", "historical_gpu_replay", "historical_gpu_acquisition_gate_changed",
                      "gallery_acquired", "lexical_effect_estimated", "efficacy_screen")
    boundary(specification, expected_false)
    boundary(acquisition, expected_false)
    check(set(specification["source_sha256"]) == SOURCE_FILES, "Unexpected source bindings; will not read arbitrary paths")
    for relative, expected_hash in specification["source_sha256"].items():
        check(sha(repo / relative) == expected_hash, f"Bound source changed: {relative}")
    exposed = read(repo / "validation/t21_glyph_context_path_confirmation_v0/canary_specification.json")
    pilot = read(repo / "validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json")
    check(exposed["target_count"] == 8 and exposed["source_count"] == 128, "Original exposed pool changed")
    check(exposed["target_tokens"] == pilot["target_tokens"][:8]
          and exposed["source_tokens"] == pilot["source_tokens"]
          and exposed["donor_indices"] == pilot["donor_indices"][:8], "Original exposed input equality failed")
    check(specification["target_tokens"] == exposed["target_tokens"][:count]
          and specification["source_tokens"] == exposed["source_tokens"]
          and specification["donor_indices"] == exposed["donor_indices"][:count], "CPU input or donor mapping changed")
    artifact = specification["model_artifact"]
    check(artifact == pilot["model_artifact"] == acquisition["model_artifact"], "Pinned model artifact mismatch")
    check(artifact["file_count"] == 9 and set(artifact["files"]) == MODEL_FILES
          and artifact["total_bytes"] == 6434705789
          and artifact["manifest_sha256"] == "dc5b61a2c4aa123f82e7d0471b4cdb3a7d8de3b6a8db327047fb1b6d05e3bdf4", "Unexpected nine-file pin")
    manifest_payload = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    check(hashlib.sha256(manifest_payload).hexdigest() == artifact["manifest_sha256"]
          and sum(metadata["bytes"] for metadata in artifact["files"].values()) == artifact["total_bytes"],
          "Nine-file manifest digest or byte total is internally inconsistent")
    model_files_rehashed = False
    if args.model_path:
        model = args.model_path.resolve()
        actual_names = {path.relative_to(model).as_posix() for path in model.rglob("*") if path.is_file()}
        check(actual_names == MODEL_FILES, "Model snapshot file inventory changed")
        for name, metadata in artifact["files"].items():
            path = model / name
            check(path.stat().st_size == metadata["bytes"] and sha(path) == metadata["sha256"], f"Model file hash mismatch: {name}")
        model_files_rehashed = True
    runtime = specification["runtime"]
    check(runtime == acquisition["runtime"], "Runtime receipt mismatch")
    for key, expected in {"torch": "2.13.0+cpu", "transformers": "5.15.0", "device": "cpu",
                          "dtype": "bfloat16", "attention": "eager", "interop_threads": 1}.items():
        check(runtime[key] == expected, f"Runtime mismatch: {key}")
    check(isinstance(runtime["threads"], int) and runtime["threads"] > 0, "Invalid CPU thread count")
    check(set(acquisition["checks"]) == CHECKS and all(value is True for value in acquisition["checks"].values()), "Acquisition engineering claims incomplete")
    expected_chunks = {f"item_{index:04d}" for index in range(count)}
    check(set(acquisition["chunks"]) == expected_chunks, "Incomplete or extra acquisition chunks")
    check({path.name for path in root.glob("item_*")} == expected_chunks, "Unexpected item directories")
    reports = []
    totals = Counter()
    for index, tokens in enumerate(specification["target_tokens"]):
        item = root / f"item_{index:04d}"
        receipt_path = item / "receipt.json"
        check(sha(receipt_path) == acquisition["chunks"][item.name], "Acquisition→item receipt hash mismatch")
        receipt = read(receipt_path)
        check(receipt["protocol_id"] == PROTOCOL and receipt["item_index"] == index
              and receipt["specification_sha256"] == specification_hash, "Item identity/spec binding mismatch")
        check(sha(item / "states.npz") == receipt["states_sha256"], "Item NPZ hash mismatch")
        check(set(receipt["checks"]) == CHECKS and all(value is True for value in receipt["checks"].values()), "Item engineering claims incomplete")
        boundary(receipt, ("scientific_result", "historical_gpu_replay"))
        check(receipt["forward_calls"] == 30 and receipt["sequence_forwards"] == 786
              and receipt["offtarget_attention_checks"] == 72, "Unexpected per-item forward/check counts")
        totals.update({"forward_calls": 30, "sequence_forwards": 786, "offtarget_attention_checks": 72})
        length = len(tokens["raw"]["glyph"])
        check(1 <= length <= 3, "Unsupported glyph length")
        for donor in specification["donor_indices"][index]:
            check(0 <= donor < 128 and len(specification["source_tokens"][donor]["raw"]["glyph"]) == length, "Token-count-matched donor mapping invalid")
        for carrier in CARRIERS:
            for row in (tokens, *(specification["source_tokens"][donor] for donor in specification["donor_indices"][index])):
                for view in (("glyph", "codepoint_literal") if row is tokens else ("glyph",)):
                    raw, ids = row["raw"][view], row["sequences"][carrier][view]
                    check(len(ids) == len(raw) + 8 and ids[:len(raw)] == raw, "Original eight-carrier sequence shape changed")
        check(receipt["arrays"] == array_schema(tokens), "Receipt array metadata differs from independent schema")
        with np.load(item / "states.npz", allow_pickle=False) as arrays:
            report = validate_arrays(arrays, tokens)
        report.update({"item_index": index, "receipt_sha256": sha(receipt_path),
                       "states_sha256": receipt["states_sha256"],
                       "elapsed_seconds": receipt["timing_seconds"]["total"],
                       "peak_rss_bytes": receipt["peak_rss_bytes"]})
        reports.append(report)
    check(acquisition["forward_calls_across_items"] == totals["forward_calls"]
          and acquisition["sequence_forwards_across_items"] == totals["sequence_forwards"], "Acquisition count totals mismatch")
    result = {"status": "pass", "protocol_id": PROTOCOL, "independent_validator_sha256": sha(Path(__file__)),
              "acquisition_receipt_sha256": acquisition_hash, "specification_sha256": specification_hash,
              "target_items": count, "arrays_validated": 34 * count, "runtime": runtime,
              "totals": dict(totals), "model_files_independently_rehashed": model_files_rehashed,
              "glyph_token_count_histogram": dict(Counter(str(report["glyph_token_count"]) for report in reports)),
              "items": reports, "scientific_result": False, "historical_gpu_replay": False,
              "model_forwards_this_validation": 0, "protected_bank_reads": 0,
              "saved_readout_and_attention_arrays_reverified": True,
              "omitted_full_hidden_state_stock_capture_and_nonreadout_checks_reverified": False,
              "boundary": "Stored readouts/attention and hash bindings independently checked. Acquisition-time full-hidden-state, stock-idle, donor-capture-pair, and nonreadout comparisons are source-bound claims; those complete tensors are not retained here."}
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError, IndexError, AttributeError, EOFError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "fail", "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise SystemExit(2)
