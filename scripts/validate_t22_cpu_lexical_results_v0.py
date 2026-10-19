#!/usr/bin/env python3
"""Independent NumPy-only audit of lexical readouts, cosines and item contrasts.

Does not import either acquisition/scoring runner or Torch. Full stock replay
and model-manifest comparisons remain source-bound acquisition-time assertions.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

PROTOCOL = "glyphprobe-t22-cpu-lexical-eight-descriptive-v0"
PARENT_SHA = "27c9e58535a872861a87c22d7b82dce7f9e54952bc229511b7231a9693dca901"
OPS, CARRIERS = ("none", "k", "v", "kv"), ("pipe", "article_a")
TOLERANCE = 1e-12


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read(path):
    def pairs(values):
        result = {}
        for key, value in values:
            check(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f"Nonfinite JSON constant: {value}")

    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def near(actual, expected, label):
    actual, expected = np.asarray(actual), np.asarray(expected)
    check(actual.shape == expected.shape and np.isfinite(actual).all()
          and np.isfinite(expected).all(), f"Nonfinite/shape mismatch: {label}")
    error = float(np.max(np.abs(actual - expected))) if actual.size else 0.0
    check(error <= TOLERANCE, f"Numerical mismatch {label}: {error}")
    return error


def unit(array):
    array = np.asarray(array, np.float64)
    length = np.sqrt(np.einsum("...j,...j->...", array, array, optimize=False))[..., None]
    check(np.isfinite(array).all() and (length > 1e-12).all(), "Invalid cosine input")
    return array / length


def statistics(value):
    return {"n_items": 8, "mean": np.mean(value), "median": np.median(value),
            "sample_sd": np.std(value, ddof=1), "min": np.min(value), "max": np.max(value)}


def audit(repo, acquisition, analysis, expected_spec=None):
    spec = read(acquisition / "specification.json")
    spec_hash = sha(acquisition / "specification.json")
    if expected_spec:
        check(spec_hash == expected_spec, "Externally pinned specification mismatch")
    acq, result = read(acquisition / "acquisition_receipt.json"), read(analysis / "result.json")
    check(spec["protocol_id"] == acq["protocol_id"] == result["protocol_id"] == PROTOCOL, "Protocol mismatch")
    check(acq["status"] == "alias_acquisition_complete" and result["status"] == "descriptive_analysis_complete", "Incomplete work")
    check(acq["specification_sha256"] == result["specification_sha256"] == spec_hash, "Specification chain mismatch")
    check(result["alias_acquisition_sha256"] == sha(acquisition / "acquisition_receipt.json"), "Acquisition chain mismatch")
    check(result["source_sha256"] == spec["source_sha256"], "Analysis source bindings differ")
    for name, expected in spec["source_sha256"].items():
        check(name.startswith(("scripts/", "tests/", "docs/", "src/", "configs/", "validation/"))
              and ".." not in Path(name).parts, "Unexpected source path")
        check(sha(repo / name) == expected, f"Frozen source changed: {name}")
    check(sha(spec["validation_receipt"]) == spec["validation_receipt_sha256"], "Validation receipt changed")
    synthetic = read(spec["validation_receipt"])
    check(synthetic["status"] == "pass" and synthetic["source_sha256"] == spec["source_sha256"], "Synthetic source validation mismatch")
    check(sha(acquisition / "engineering_audit.json") == spec["engineering_audit_sha256"], "Engineering audit changed")
    parent = Path(spec["canary_run"])
    check(sha(parent / "acquisition_receipt.json") == spec["canary_acquisition_sha256"] == PARENT_SHA
          and result["canary_acquisition_sha256"] == PARENT_SHA, "Unexpected engineering parent")
    check(sha(parent / "specification.json") == spec["canary_specification_sha256"], "Parent specification changed")
    parent_spec, parent_receipt = read(parent / "specification.json"), read(parent / "acquisition_receipt.json")
    for name in ("model_artifact", "runtime", "target_tokens", "source_tokens", "donor_indices"):
        check(spec[name] == parent_spec[name], f"Changed parent field: {name}")
    check(spec["target_count"] == 8 and spec["source_count"] == 128 and spec["alias_forward_batch"] == 1,
          "Changed sample/gallery/batch size")
    check(acq["forward_calls_total"] == 288 and acq["stock_glyph_full_state_replays"] == 16
          and acq["new_intervention_forwards"] == 0, "Changed acquisition counts")
    for name in ("hypothesis_tests", "efficacy_screen", "confirmation", "historical_gpu_replay"):
        check(result[name] is False and spec[name] is False, f"Claim boundary changed: {name}")
    check(spec["select_384_exploration_by_canary_sign"] is False and spec["protected_bank_reads"] == 0
          and acq["protected_bank_reads"] == 0 and result["protected_bank_reads"] == 0, "Claim/exposure boundary changed")
    for name, expected in result["artifacts_sha256"].items():
        check(Path(name).name == name and sha(analysis / name) == expected, "Analysis artifact changed")
    check(set(result["artifacts_sha256"]) == {"metrics.npz", "rows.csv", "attention_diagnostics.json", "report.md"}, "Artifact inventory mismatch")
    check(sha(acquisition / "gallery.npz") == acq["gallery_sha256"], "Gallery hash mismatch")
    with np.load(acquisition / "gallery.npz", allow_pickle=False) as stored:
        check(set(stored.files) == {"target_alias", "source_alias"}, "Gallery inventory mismatch")
        target, source = stored["target_alias"], stored["source_alias"]
    check(target.shape == (8, 2, 3072) and source.shape == (128, 2, 3072), "Gallery shape mismatch")
    expected_chunks = {f"{g}_{i:04d}" for g, n in (("target", 8), ("source", 128)) for i in range(n)}
    check(set(acq["chunks"]) == expected_chunks, "Alias chunk inventory mismatch")
    calls = 0
    for group, values in (("target", target), ("source", source)):
        check(values.dtype == np.float32 and np.isfinite(values).all()
              and ((values.view(np.uint32) & 65535) == 0).all(), "Invalid/BF16-incompatible gallery values")
        for i, value in enumerate(values):
            path = acquisition / "aliases" / f"{group}_{i:04d}"
            check(sha(path / "receipt.json") == acq["chunks"][path.name], "Alias receipt changed")
            receipt = read(path / "receipt.json")
            check(receipt["specification_sha256"] == spec_hash and receipt["index"] == i
                  and receipt["group"] == group, "Alias row identity mismatch")
            check(receipt["forward_calls"] == (4 if group == "target" else 2)
                  and receipt["stock_glyph_full_state_replayed"] is (group == "target"), "Alias stock gate/count mismatch")
            calls += receipt["forward_calls"]
            check(sha(path / "states.npz") == receipt["states_sha256"], "Alias array changed")
            with np.load(path / "states.npz", allow_pickle=False) as row:
                check(row.files == ["alias"] and np.array_equal(value, row["alias"]), "Gallery and row disagree")
    check(calls == 288, "Per-row forward count mismatch")
    with np.load(analysis / "metrics.npz", allow_pickle=False) as saved:
        metrics = {name: saved[name] for name in saved.files}
    scores = metrics["scores"]
    check(scores.shape == (8, 2, 2, 16, 129) and scores.dtype == np.float64, "Score matrix schema mismatch")
    max_score_error = 0.0
    attention = {(r["item"], r["carrier"], r["operation"], r["position"]): r
                 for r in read(analysis / "attention_diagnostics.json")["rows"]}
    check(len(attention) == 128, "Attention diagnostic coverage mismatch")
    for i in range(8):
        path = parent / f"item_{i:04d}"
        check(sha(path / "receipt.json") == parent_receipt["chunks"][path.name], "Parent item receipt mismatch")
        check(sha(path / "states.npz") == read(path / "receipt.json")["states_sha256"], "Parent readouts changed")
        with np.load(path / "states.npz", allow_pickle=False) as raw:
            for c, carrier in enumerate(CARRIERS):
                gallery = unit(np.concatenate((target[i, c][None], source[:, c])))
                for n, label in enumerate(("extension", "extension_neutral")):
                    independent = np.einsum("ij,kj->ik", unit(raw[f"{carrier}_{label}"]), gallery, optimize=False)
                    max_score_error = max(max_score_error, near(scores[i, c, n], independent, "independent cosine oracle"))
                weights, baseline = raw[f"{carrier}_attention_weights"], raw[f"{carrier}_attention_baseline_weights"]
                for op, operation in enumerate(OPS):
                    for p, position in enumerate(("glyph", "suffix")):
                        rows = slice(op * 4 + p * 2, op * 4 + p * 2 + 2)
                        row = attention[i, carrier, operation, position]
                        local = np.abs(weights[0, :, rows] - baseline[0, :, rows]).max()
                        near(row["local_max_abs_weight_difference"], local, "local weights")
                        if operation in ("none", "v"):
                            check(local == 0, "Local none/V weights changed")
                        near(row["active_minus_neutral_headmean_l1_by_block"],
                             np.abs(weights[0, :, rows] - weights[1, :, rows]).sum(axis=-1).mean(axis=(1, 2)), "downstream weight change")
                        for mass in ("glyph", "suffix"):
                            values = raw[f"{carrier}_attention_{mass}_mass"]
                            near(row[mass + "_mass_active_minus_neutral_by_block"],
                                 (values[0, :, rows] - values[1, :, rows]).mean(axis=(1, 2)), "attention mass")
    # The numerically checked archived own-first matrix defines tie handling.
    derived = {"own_cosine": scores[..., 0], "competitor_cosine": scores[..., 1:].max(axis=-1),
               "competitor_index": scores[..., 1:].argmax(axis=-1),
               "alias_top1": (scores.argmax(axis=-1) == 0).astype(float),
               "own_rank": 1 + (scores[..., 1:] > scores[..., 0, None]).sum(axis=-1)}
    donor = np.empty((8, 2, 2, 16))
    for i in range(8):
        for row in range(16):
            donor[i, :, :, row] = scores[i, :, :, row, spec["donor_indices"][i][row % 2] + 1]
    derived.update(donor_cosine=donor, alias_margin=derived["own_cosine"] - derived["competitor_cosine"],
                   donor_margin=derived["own_cosine"] - donor)
    for name, value in derived.items():
        near(metrics[name], value, name)
    contrasts = {}
    for name, value in derived.items():
        if name in ("own_rank", "competitor_index"):
            continue
        adjusted, absolute = np.zeros((8, 4)), np.zeros((8, 4))
        for i in range(8):
            for c in range(2):
                for op in range(4):
                    for d in range(2):
                        g, s = op * 4 + d, op * 4 + 2 + d
                        glyph_effect = value[i, c, 0, g] - value[i, c, 1, g]
                        suffix_effect = value[i, c, 0, s] - value[i, c, 1, s]
                        adjusted[i, op] += (suffix_effect - glyph_effect) / 4
                        absolute[i, op] -= glyph_effect / 4
        contrasts[name] = adjusted
        near(metrics[name + "_adjusted_per_item"], adjusted, name + " item contrast")
        near(metrics[name + "_absolute_glyph_decrement_per_item"], absolute, name + " absolute decrement")
        for op, operation in enumerate(OPS):
            reported = result["primary_position_adjusted_decrement"][operation][name]
            for stat, expected in statistics(adjusted[:, op]).items():
                near(reported[stat], expected, name + " summary " + stat)
            if name == "alias_margin":
                for stat, expected in statistics(absolute[:, op]).items():
                    near(result["absolute_glyph_margin_decrement"][operation][stat], expected, "absolute summary")
    primary = contrasts["alias_margin"]
    near(primary, contrasts["own_cosine"] - contrasts["competitor_cosine"], "margin decomposition")
    check(np.array_equal(primary[:, 0], np.zeros(8)), "Reference operation changed margin")
    near(result["itemwise_adjusted_margin"], primary, "JSON item contrasts")
    near(metrics["adjusted_margin_per_item"], primary, "NPZ item contrasts")
    nonadditivity = primary[:, 3] - primary[:, 1] - primary[:, 2]
    near(result["itemwise_nonadditivity"], nonadditivity, "nonadditivity")
    near(metrics["nonadditivity_per_item"], nonadditivity, "NPZ nonadditivity")
    for stat, expected in statistics(nonadditivity).items():
        near(result["nonadditivity"][stat], expected, "nonadditivity summary")
    with (analysis / "rows.csv").open() as stream:
        csv_rows = list(csv.DictReader(stream))
    check(len(csv_rows) == 512, "CSV row count mismatch")
    for ordinal, row in enumerate(csv_rows):
        i, c, n, r = np.unravel_index(ordinal, (8, 2, 2, 16))
        check(int(row["item"]) == i and row["carrier"] == CARRIERS[c]
              and row["neutral"] == str(bool(n)) and row["operation"] == OPS[r // 4]
              and row["position"] == ("glyph", "suffix")[(r // 2) % 2]
              and int(row["donor_slot"]) == r % 2, "CSV row alignment mismatch")
        for name, value in derived.items():
            near(float(row[name]), value[i, c, n, r], "CSV " + name)
    return {"status": "pass", "protocol_id": PROTOCOL,
            "independent_validator_sha256": sha(Path(__file__)),
            "specification_sha256": spec_hash, "analysis_result_sha256": sha(analysis / "result.json"),
            "alias_acquisition_sha256": sha(acquisition / "acquisition_receipt.json"),
            "canary_acquisition_sha256": PARENT_SHA, "target_items": 8, "scored_rows": 512,
            "cosine_values_recomputed": 512 * 129, "max_independent_cosine_error": max_score_error,
            "numeric_tolerance": TOLERANCE, "all_item_contrasts_and_summaries_recomputed": True,
            "csv_and_attention_rechecked": True, "stock_full_replay_independently_repeated": False,
            "model_files_independently_rehashed_this_audit": False, "audit_model_forwards": 0,
            "boundary": "Independent stored-data arithmetic and hash audit. Stock full-state replay and model file checks remain source-bound acquisition assertions. Eight exposed items do not provide population or semantic-mechanism conclusions."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--acquisition", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--expected-specification-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check(not args.output.exists(), "Audit output already exists")
    result = audit(args.repo, args.acquisition, args.analysis, args.expected_specification_sha256)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
