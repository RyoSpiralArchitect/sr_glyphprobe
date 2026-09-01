#!/usr/bin/env python3
"""Independent result validator for T18 fresh composite-glyph confirmation."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import tarfile
from typing import Any, Mapping, Sequence

import numpy as np
import yaml


PROTOCOL_ID = "glyphprobe-fresh-composite-glyph-lexical-confirmation-v0"
MODEL_ROLES = (
    "qwen25_0p5b_base_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "smollm2_1p7b_base_bf16",
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "mistral7b_instruct_v03_bf16",
)
CORE_ROLES = (
    "llama32_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "olmo2_1b_base_bf16",
    "gemma2_2b_it_bf16",
)
SYSTEM_ORDER = ("modifier", "zwj", "regional_flag")
VIEW_COUNT = 4
DEPTH_COUNT = 9
SHARD_COUNT = 6
ITEM_COUNT = 192


class ValidationError(RuntimeError):
    """Raised when independent reconstruction disagrees with stored evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def archived_regular_files(root: Path, commit: str) -> dict[str, bytes]:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as handle:
        for member in handle.getmembers():
            if not member.isfile():
                continue
            stream = handle.extractfile(member)
            require(stream is not None, f"Cannot read archived blob: {member.name}")
            result[member.name] = stream.read()
    return result


def stratified_permutation(
    rng: np.random.Generator, item_count: int, strata: Sequence[Sequence[int]]
) -> np.ndarray:
    order = np.arange(item_count, dtype=np.int64)
    flattened = sorted(int(value) for group in strata for value in group)
    require(
        flattened == list(range(item_count)), "Matched strata do not partition items"
    )
    require(all(len(group) >= 2 for group in strata), "Matched stratum is singleton")
    result = order.copy()
    for group in strata:
        indices = np.asarray(group, dtype=np.int64)
        result[indices] = rng.permutation(indices)
    return result


def observed_statistic(
    predictions: Mapping[str, np.ndarray], component: str
) -> tuple[float, dict[str, float]]:
    values: dict[str, float] = {}
    for system in SYSTEM_ORDER:
        name = predictions[f"{component}__{system}__english"]
        codepoint = predictions[f"{component}__{system}__codepoint"]
        require(
            name.shape == codepoint.shape and name.shape[0] == 24,
            "Prediction shape mismatch",
        )
        order = np.arange(name.shape[1], dtype=np.int64)
        values[system] = float(
            np.mean(name == order[None, :]) - np.mean(codepoint == order[None, :])
        )
    return float(np.mean(list(values.values()))), values


def randomization_test(
    predictions: Mapping[str, np.ndarray],
    component: str,
    strata_by_system: Mapping[str, Sequence[Sequence[int]]] | None,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    observed, systems = observed_statistic(predictions, component)
    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(draws):
        values: list[float] = []
        for system in SYSTEM_ORDER:
            name = predictions[f"{component}__{system}__english"]
            codepoint = predictions[f"{component}__{system}__codepoint"]
            count = int(name.shape[1])
            permutation = (
                rng.permutation(count)
                if strata_by_system is None
                else stratified_permutation(rng, count, strata_by_system[system])
            )
            order = np.arange(count, dtype=np.int64)
            values.append(
                float(np.mean(name == permutation[None, :]))
                - float(np.mean(codepoint == order[None, :]))
            )
        exceedances += int(float(np.mean(values)) >= observed)
    return {
        "observed": observed,
        "system_contrasts": systems,
        "exceedances": exceedances,
        "p_value": float((1 + exceedances) / (draws + 1)),
    }


def holm(raw: Mapping[str, float], alpha: float) -> dict[str, dict[str, Any]]:
    ordered = sorted(raw, key=lambda key: (float(raw[key]), key))
    count = len(ordered)
    running = 0.0
    rejected_prefix = True
    result: dict[str, dict[str, Any]] = {}
    for index, key in enumerate(ordered):
        adjusted = max(running, min(1.0, (count - index) * float(raw[key])))
        running = adjusted
        threshold = alpha / (count - index)
        rejected = rejected_prefix and float(raw[key]) <= threshold
        rejected_prefix = rejected
        result[key] = {"adjusted_p": adjusted, "reject": rejected}
    return result


def partial_conjunction(values: Mapping[str, float], r: int) -> dict[str, Any]:
    ordered = sorted((float(value), key) for key, value in values.items())
    m = len(ordered)
    require(1 <= r <= m, "Invalid partial-conjunction rank")
    rth = ordered[r - 1]
    return {
        "rth_role": rth[1],
        "rth_p": rth[0],
        "p_value": min(1.0, (m - r + 1) * rth[0]),
    }


def validate(
    root: Path,
    run_root: Path,
    summary_root: Path,
    analysis: Path,
) -> dict[str, Any]:
    config = yaml.safe_load(
        (root / "configs/fresh_composite_glyph_lexical_confirmation_v0.yaml").read_text(
            encoding="utf-8"
        )
    )
    require(config["protocol_id"] == PROTOCOL_ID, "Config protocol mismatch")
    selection_path = (
        root / "data/manifests/fresh_composite_glyph_lexical_confirmation_v0.json"
    )
    freeze_path = (
        root
        / "data/manifests/fresh_composite_glyph_lexical_confirmation_v0_freeze.json"
    )
    selection = read_json(selection_path)
    freeze = read_json(freeze_path)
    require(
        selection["protocol_id"] == PROTOCOL_ID
        and freeze["protocol_id"] == PROTOCOL_ID,
        "Manifest protocol mismatch",
    )
    require(
        freeze["status"] == "final_execution_freeze_zero_t18_model_forwards",
        "Freeze status changed",
    )
    require(
        int(freeze["model_forwards_at_freeze"]) == 0, "Freeze contains model forwards"
    )
    require(
        sha256(selection_path) == freeze["selection_manifest_sha256"],
        "Selection binding changed",
    )
    for relative, expected in freeze["frozen_assets"].items():
        path = root / relative
        require(
            path.is_file() and sha256(path) == expected,
            f"Frozen asset changed: {relative}",
        )
    items = sorted(selection["items"], key=lambda row: int(row["selection_index"]))
    require(len(items) == ITEM_COUNT, "Selection count changed")
    require(
        Counter(str(row["glyph_system"]) for row in items)
        == Counter({"modifier": 64, "zwj": 96, "regional_flag": 32}),
        "Selection system counts changed",
    )
    for field in (
        "glyph",
        "english_short_name",
        "japanese_short_name",
        "codepoint_literal",
    ):
        values = [str(row[field]) for row in items]
        require(len(values) == len(set(values)), f"Selection view collapsed: {field}")
    exposure = config["source_bindings"]["exposure_tree"]
    archived = archived_regular_files(root, str(exposure["commit"]))
    require(
        len(archived) == int(exposure["tracked_paths"]),
        "Exposure-tree path count changed",
    )
    exposure_hits = {
        str(row["codepoint"]): [
            path
            for path, raw in archived.items()
            if str(row["glyph"]).encode("utf-8") in raw
        ]
        for row in items
    }
    require(
        not any(exposure_hits.values()),
        "Selected exact surface occurs in the frozen exposure tree",
    )

    t10_config = yaml.safe_load(
        (root / "configs/semantic_atlas_cross_model_replication_v0.yaml").read_text(
            encoding="utf-8"
        )
    )
    widths = {
        role: int(t10_config["models"][role]["expected_model_dim"])
        for role in MODEL_ROLES
    }
    run_receipt_hashes: dict[str, str] = {}
    summary_receipt_hashes: dict[str, str] = {}
    total_forwards = 0
    total_vectors = 0
    for role in MODEL_ROLES:
        role_dir = run_root / role
        role_receipt = read_json(role_dir / "role_receipt.json")
        require(
            role_receipt["protocol_id"] == PROTOCOL_ID
            and role_receipt["model_role"] == role,
            "Role receipt mismatch",
        )
        require(
            role_receipt["runtime_t18_token_sequences_match_frozen_preflight"] is True,
            "Runtime tokenizer not admitted",
        )
        total_forwards += int(role_receipt["model_forward_calls"])
        total_vectors += int(role_receipt["readout_vectors"])
        run_receipt_hashes[role] = sha256(role_dir / "role_receipt.json")
        for shard_index in range(SHARD_COUNT):
            shard = role_dir / f"shard_{shard_index:04d}"
            receipt = read_json(shard / "receipt.json")
            for name, expected in receipt["outputs"].items():
                require(
                    sha256(shard / name) == expected,
                    f"Shard output changed: {role}/{shard_index}/{name}",
                )
            start = shard_index * 32
            count = min(32, ITEM_COUNT - start)
            array = np.load(
                shard / "activations.npy", mmap_mode="r", allow_pickle=False
            )
            require(
                array.shape == (count, VIEW_COUNT, 2, 4, DEPTH_COUNT, widths[role]),
                "Shard shape changed",
            )
            require(array.dtype == np.float32, "Shard dtype changed")
        summary = summary_root / role
        summary_receipt = read_json(summary / "summary_receipt.json")
        require(
            summary_receipt["input_role_receipt_sha256"] == run_receipt_hashes[role],
            "Summary/run binding changed",
        )
        for name, expected in summary_receipt["outputs"].items():
            require(
                sha256(summary / name) == expected,
                f"Summary output changed: {role}/{name}",
            )
        summary_receipt_hashes[role] = sha256(summary / "summary_receipt.json")

    stored_receipt = read_json(analysis / "analysis_receipt.json")
    stored_models = read_json(analysis / "model_cell_results.json")
    stored_cross = read_json(analysis / "cross_model_primary_result.json")
    require(
        stored_receipt["input_summary_receipt_sha256"] == summary_receipt_hashes,
        "Analysis/summary binding changed",
    )
    endpoint = config["model_primary_endpoint"]
    draws = int(endpoint["randomization_draws"])
    seed_base = int(endpoint["seed_base"])
    floor = float(endpoint["practical_minimum"])
    reconstructed: dict[str, Any] = {}
    for role_index, role in enumerate(MODEL_ROLES):
        with np.load(
            summary_root / role / "primary_predictions.npz", allow_pickle=False
        ) as stored:
            predictions = {key: np.asarray(stored[key]) for key in stored.files}
        tokenizer = read_json(
            root
            / "validation/fresh_composite_glyph_lexical_confirmation_v0/tokenizers"
            / f"{role}.json"
        )["tokenizer"]
        strata = tokenizer["primary_exact_strata"]["eligible_local_strata_by_system"]
        unrestricted = randomization_test(
            predictions, "unrestricted", None, draws, seed_base + role_index * 10 + 1
        )
        matched = randomization_test(
            predictions, "matched", strata, draws, seed_base + role_index * 10 + 2
        )
        stored = stored_models[role]
        for observed, expected, label in (
            (
                unrestricted["observed"],
                stored["unrestricted_component"][
                    "observed_equal_system_equal_context_contrast"
                ],
                "unrestricted estimate",
            ),
            (
                matched["observed"],
                stored["tokenization_matched_component"][
                    "observed_equal_system_equal_context_contrast"
                ],
                "matched estimate",
            ),
            (
                unrestricted["p_value"],
                stored["unrestricted_component"]["p_value"],
                "unrestricted p",
            ),
            (
                matched["p_value"],
                stored["tokenization_matched_component"]["p_value"],
                "matched p",
            ),
        ):
            require(
                math.isclose(
                    float(observed), float(expected), rel_tol=0.0, abs_tol=1e-15
                ),
                f"{role} {label} changed",
            )
        require(
            unrestricted["exceedances"]
            == int(stored["unrestricted_component"]["exceedances"]),
            f"{role} unrestricted exceedances changed",
        )
        require(
            matched["exceedances"]
            == int(stored["tokenization_matched_component"]["exceedances"]),
            f"{role} matched exceedances changed",
        )
        iut = max(unrestricted["p_value"], matched["p_value"])
        practical = unrestricted["observed"] >= floor and matched["observed"] >= floor
        reconstructed[role] = {
            "iut_p": iut,
            "practical": practical,
            "joint": iut <= float(endpoint["alpha"]) and practical,
        }
    raw = {role: float(reconstructed[role]["iut_p"]) for role in MODEL_ROLES}
    adjusted = holm(raw, float(config["bounded_model_cell_family"]["familywise_alpha"]))
    partial = partial_conjunction(
        {role: raw[role] for role in CORE_ROLES},
        int(config["cross_model_primary"]["r"]),
    )
    practical_count = sum(int(reconstructed[role]["practical"]) for role in CORE_ROLES)
    joint_count = sum(int(reconstructed[role]["joint"]) for role in CORE_ROLES)
    positive = partial["p_value"] <= float(
        config["cross_model_primary"]["alpha"]
    ) and joint_count >= int(config["cross_model_primary"]["r"])
    require(
        math.isclose(
            partial["p_value"],
            float(stored_cross["p_value"]),
            rel_tol=0.0,
            abs_tol=1e-15,
        ),
        "Partial-conjunction p changed",
    )
    require(
        practical_count == int(stored_cross["core_practical_pass_count"]),
        "Core practical count changed",
    )
    require(
        joint_count
        == int(stored_cross["core_joint_statistical_and_practical_pass_count"]),
        "Core joint pass count changed",
    )
    require(positive == bool(stored_cross["positive"]), "Cross-model decision changed")
    for role in MODEL_ROLES:
        require(
            math.isclose(
                adjusted[role]["adjusted_p"],
                float(stored_models[role]["holm_adjusted_p"]),
                rel_tol=0.0,
                abs_tol=1e-15,
            ),
            f"Holm p changed: {role}",
        )
    require(
        total_forwards
        == int(config["acquisition"]["expected_total_model_forward_calls"]),
        "Total forward count changed",
    )
    require(
        total_vectors == int(config["acquisition"]["expected_total_readout_vectors"]),
        "Total vector count changed",
    )
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "independent_validation_pass",
        "selection_manifest_sha256": sha256(selection_path),
        "freeze_manifest_sha256": sha256(freeze_path),
        "run_role_receipt_sha256": run_receipt_hashes,
        "summary_receipt_sha256": summary_receipt_hashes,
        "analysis_receipt_sha256": sha256(analysis / "analysis_receipt.json"),
        "recomputed_randomization_tests": len(MODEL_ROLES) * 2,
        "randomization_draws_per_test": draws,
        "total_model_forward_calls": total_forwards,
        "total_readout_vectors": total_vectors,
        "partial_conjunction_p": partial["p_value"],
        "core_practical_pass_count": practical_count,
        "core_joint_statistical_and_practical_pass_count": joint_count,
        "positive": positive,
        "claim_boundary": stored_receipt["claim_boundary"],
        "raw_activations_committed_to_git": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--summary-root", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = validate(
        args.root.resolve(), args.run_root, args.summary_root, args.analysis
    )
    require(not args.output.exists(), f"Validation output exists: {args.output}")
    write_json(args.output, value)
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
