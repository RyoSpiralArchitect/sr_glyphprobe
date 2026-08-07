from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_llama32_3b_mps_emoji_transport_v1.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_llama32_3b_mps_emoji_transport_v1", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _groups() -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(range(group * 4, group * 4 + 4)) for group in range(6))


def _vectors(slot_count: int, *, seed: int = 1701) -> np.ndarray:
    rng = np.random.default_rng(seed)
    vectors = rng.normal(size=(5, 3, slot_count, 24, 12))
    vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors


def _direct_score(
    vectors: np.ndarray,
    weights: np.ndarray,
    *,
    source: int,
    prototype: int,
    seed: int,
    target: int,
) -> float:
    held_group = next(group for group in _groups() if target in group)
    training = [index for index in range(24) if index not in held_group]
    slot_count = vectors.shape[2]
    prototypes = []
    for slot in range(slot_count):
        total = sum(
            weights[index] * vectors[prototype, seed, slot, index] for index in training
        )
        prototypes.append(total / np.linalg.norm(total))
    prototype_matrix = np.stack(prototypes)
    evaluation = vectors[source, seed, :, target]
    cosine_matrix = evaluation @ prototype_matrix.T
    diagonal = np.diag(cosine_matrix)
    mismatched = (cosine_matrix.sum(axis=1) - diagonal) / (slot_count - 1)
    return float(np.mean(diagonal - mismatched))


def _target_authority() -> tuple[tuple[str, ...], dict[str, str]]:
    target_ids = tuple(f"target_{index:02d}" for index in range(24))
    groups = {
        target_id: MODULE.TARGET_GROUPS[index // 4]
        for index, target_id in enumerate(target_ids)
    }
    return target_ids, groups


def _valid_intervention_row() -> dict[str, Any]:
    scalar_fields = {
        "kl_base_to_intervened",
        "kl_intervened_to_base",
        "js_divergence",
        "total_variation",
        "hellinger",
        "entropy_baseline",
        "entropy_intervened",
        "logit_delta_l2",
        "logit_delta_rms",
        "logit_delta_max_abs",
        "top_k_jaccard",
        "top_k_overlap_fraction",
        "rank_biased_overlap",
        "baseline_top2_margin",
        "intervened_top2_margin",
    }
    distribution = {field: 0.1 for field in scalar_fields}
    distribution.update(
        {
            "entropy_delta": -0.01,
            "logit_cosine": 0.9,
            "probability_cosine": 0.95,
            "argmax_flip": True,
            "baseline_argmax": 1,
            "intervened_argmax": 2,
            "intervened_rank_of_baseline_argmax": 2,
            "baseline_rank_of_intervened_argmax": 3,
            "top_positive_delta_ids": list(range(32)),
            "top_positive_delta_values": [float(value) for value in range(32, 0, -1)],
            "top_negative_delta_ids": list(range(32, 64)),
            "top_negative_delta_values": [float(value) for value in range(-32, 0)],
            "fingerprint": [1.0] + [0.0] * (MODULE.FINGERPRINT_DIM - 1),
        }
    )
    return {
        "task_id": "a" * 24,
        "seed": MODULE.DIRECTION_SEEDS[0],
        "layer": MODULE.LAYERS[0],
        "condition_type": "emoji",
        "condition_id": "sky_slot_00",
        "strength": MODULE.STRENGTH,
        "sign": 1,
        "target_id": "target_00",
        "calibration": "rms",
        "glyph": "☀",
        "target_index": 0,
        "target_group": MODULE.TARGET_GROUPS[0],
        "direction_wrapper_indices": list(
            MODULE.DIRECTION_WRAPPER_INDICES[MODULE.DIRECTION_SEEDS[0]]
        ),
        "scale": {
            "target_activation_rms": 1.0,
            "direction_raw_rms": 1.0,
            "requested_strength": MODULE.STRENGTH,
            "perturbation_rms": MODULE.STRENGTH,
            "perturbation_to_target_rms": MODULE.STRENGTH,
            "clip_scale": 1.0,
            "clipped": False,
        },
        "activation": {
            "actual_activation_delta_rms": MODULE.STRENGTH,
            "actual_to_baseline_rms": MODULE.STRENGTH,
            "intended_activation_delta_rms": MODULE.STRENGTH,
            "actual_to_intended_rms": 1.0,
            "actual_intended_cosine": 1.0,
            "post_activation_cosine": 0.99,
        },
        "distribution": distribution,
        "sae": {"enabled": False},
        "latency_ms": 1.0,
        "peak_memory_bytes": None,
        "claim_stage": "pre-causal-screen",
    }


def test_core35_vectorized_score_matches_seven_slot_brute_force() -> None:
    vectors = _vectors(7)
    weights, _ = MODULE._bootstrap_weights(4, 91, 24, _groups())
    scores = MODULE._score_layer_chunk_by_seed(vectors, weights, _groups())

    for replicate, source, prototype, seed, target in (
        (0, 0, 0, 0, 0),
        (1, 2, 4, 1, 7),
        (3, 4, 1, 2, 23),
    ):
        expected = _direct_score(
            vectors,
            weights[replicate],
            source=source,
            prototype=prototype,
            seed=seed,
            target=target,
        )
        assert scores[replicate, source, prototype, seed, target] == pytest.approx(
            expected, abs=1e-12
        )


def test_one_joint_bootstrap_design_is_reused_by_both_arms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_ids, target_groups = _target_authority()
    monkeypatch.setattr(MODULE, "BOOTSTRAP_REPLICATES", 17)
    group_indices, weights, draws = MODULE._joint_bootstrap_design(
        target_ids, target_groups
    )
    weights_before = weights.copy()
    draws_before = draws.copy()

    full_layer = _vectors(10, seed=8)
    core_layer = _vectors(7, seed=9)
    full_tensor = np.stack([full_layer, np.roll(full_layer, 1, axis=-1)], axis=1)
    core_tensor = np.stack([core_layer, np.roll(core_layer, 1, axis=-1)], axis=1)
    full = MODULE._bootstrap_endpoints(
        full_tensor, weights, draws, group_indices, chunk_size=6
    )
    core = MODULE._bootstrap_endpoints(
        core_tensor, weights, draws, group_indices, chunk_size=6
    )

    assert np.array_equal(weights, weights_before)
    assert np.array_equal(draws, draws_before)
    assert np.all(weights.sum(axis=1) == 24)
    assert all(np.all(weights[:, group].sum(axis=1) == 4) for group in group_indices)
    assert full["global_specificity"].shape == (2, 17)
    assert core["global_specificity"].shape == (2, 17)
    paired = core["global_specificity"] - full["global_specificity"]
    assert paired.shape == (2, 17)


def test_primary_status_uses_strict_lower_bound_greater_than_zero() -> None:
    positive = {"low": np.nextafter(0.0, 1.0), "high": 0.1}
    boundary = {"low": 0.0, "high": 0.1}
    negative = {"low": -0.1, "high": 0.1}
    assert MODULE._primary_criterion_met(positive) is True
    assert MODULE._primary_status(positive) == "transport_criterion_met"
    assert MODULE._primary_criterion_met(boundary) is False
    assert MODULE._primary_status(boundary) == "transport_criterion_not_met"
    assert MODULE._primary_criterion_met(negative) is False


def test_manifest_role_grid_and_frozen_file_hash_fail_closed(tmp_path: Path) -> None:
    roles = {role: {"role": role} for role in MODULE.FAMILY_ORDER}
    assert set(MODULE._manifest_roles({"roles": roles}, "full50")) == set(
        MODULE.FAMILY_ORDER
    )
    missing = dict(roles)
    missing.pop("social")
    with pytest.raises(MODULE.TransportAnalysisError, match="family roles differ"):
        MODULE._manifest_roles({"roles": missing}, "full50")

    frozen = tmp_path / "frozen.json"
    frozen.write_bytes(b"frozen\n")
    expected = hashlib.sha256(frozen.read_bytes()).hexdigest()
    assert MODULE._verified_repo_file(tmp_path, Path("frozen.json"), expected) == frozen
    with pytest.raises(MODULE.TransportAnalysisError, match="SHA-256 mismatch"):
        MODULE._verified_repo_file(tmp_path, Path("frozen.json"), "0" * 64)


def test_ledger_grid_rejects_duplicate_missing_and_extra_tasks() -> None:
    condition_ids = ("slot_00", "slot_01")
    target_ids = ("target_00", "target_01")
    valid = list(MODULE._expected_ledger_task_keys(condition_ids, target_ids))
    MODULE._validate_ledger_task_keys(
        valid, condition_ids, target_ids, arm="core35", role="sky"
    )
    with pytest.raises(MODULE.TransportAnalysisError, match="duplicates"):
        MODULE._validate_ledger_task_keys(
            valid + [valid[0]], condition_ids, target_ids, arm="core35", role="sky"
        )
    with pytest.raises(MODULE.TransportAnalysisError, match="grid differs"):
        MODULE._validate_ledger_task_keys(
            valid[:-1], condition_ids, target_ids, arm="core35", role="sky"
        )
    with pytest.raises(MODULE.TransportAnalysisError, match="grid differs"):
        MODULE._validate_ledger_task_keys(
            valid + [("emoji", 999, 101, "slot_00", "target_00")],
            condition_ids,
            target_ids,
            arm="core35",
            role="sky",
        )


def test_all_distribution_diagnostics_are_mandatory_and_exact() -> None:
    row = _valid_intervention_row()
    MODULE._validate_intervention_metrics(
        row, arm="full50", role="sky", zero_hook=False
    )
    del row["distribution"]["rank_biased_overlap"]
    with pytest.raises(
        MODULE.TransportAnalysisError, match="distribution diagnostic fields differ"
    ):
        MODULE._validate_intervention_metrics(
            row, arm="full50", role="sky", zero_hook=False
        )


def test_layer_roles_are_arm_specific_and_output_publish_never_overwrites(
    tmp_path: Path,
) -> None:
    assert MODULE._layer_role("full50", 5) == "primary"
    assert "depth" in MODULE._layer_role("full50", 11)
    assert "token_isomorphic" in MODULE._layer_role("core35", 5)
    assert "token_isomorphic" in MODULE._layer_role("core35", 11)

    source = tmp_path / "staging"
    destination = tmp_path / "published"
    source.mkdir()
    destination.mkdir()
    (source / "new").write_text("new", encoding="utf-8")
    (destination / "old").write_text("old", encoding="utf-8")
    with pytest.raises(MODULE.TransportAnalysisError, match="overwrite"):
        MODULE._rename_directory_no_replace(source, destination)
    assert (source / "new").read_text(encoding="utf-8") == "new"
    assert (destination / "old").read_text(encoding="utf-8") == "old"


def test_execution_admission_requires_git_freeze_and_no_resume_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preflight_relative = Path("preflight.json")
    execution_relative = Path("execution.json")
    attempt_relative = Path("attempt.json")
    failed_relative = Path("failed.json")
    monkeypatch.setattr(MODULE, "PREFLIGHT_PATH", preflight_relative)
    monkeypatch.setattr(MODULE, "EXECUTION_RECEIPT_PATH", execution_relative)
    monkeypatch.setattr(MODULE, "ATTEMPT_STARTED_RECEIPT_PATH", attempt_relative)
    monkeypatch.setattr(MODULE, "FAILED_EXECUTION_RECEIPT_PATH", failed_relative)
    monkeypatch.setattr(MODULE, "LAUNCHER_LOG_PATH", Path("logs"))
    audited_commit = "a" * 40
    freeze_commit = "b" * 40
    manifest_sha = "c" * 64
    authority: dict[str, Any] = {
        "manifest_sha256": manifest_sha,
        "roles": {arm: {} for arm in MODULE.ARM_ORDER},
    }
    processes = []
    index = 0
    for arm in MODULE.ARM_ORDER:
        for role in MODULE.FAMILY_ORDER:
            config = Path("configs") / f"{arm}-{role}.yaml"
            config_sha = f"{index:064x}"
            authority["roles"][arm][role] = {
                "config": config,
                "config_sha256": config_sha,
                "run_name": f"{arm}-{role}-run",
            }
            log_relative = Path("logs") / f"{index:02d}.log"
            log_path = tmp_path / log_relative
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(f"process {index}\n", encoding="utf-8")
            processes.append(
                {
                    "index": index,
                    "config": config.as_posix(),
                    "config_sha256": config_sha,
                    "started_at": "2026-08-08T00:01:00+00:00",
                    "finished_at": "2026-08-08T00:02:00+00:00",
                    "return_code": 0,
                    "log_path": log_relative.as_posix(),
                    "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
                }
            )
            index += 1
    preflight = {
        "schema_version": 1,
        "protocol_id": MODULE.ANALYSIS_ID,
        "status": "passed",
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "p2_content_opened": False,
        "c1_content_opened": False,
        "audited_commit": audited_commit,
        "git_authority": {
            "audited_commit": audited_commit,
            "origin_main_commit": audited_commit,
            "branch": "main",
            "worktree_clean_before_publication": True,
        },
        "authorization": {"frozen_grid_execution_authorized": True},
        "static": {
            "manifest": {
                "path": MODULE.MANIFEST_PATH.as_posix(),
                "sha256": manifest_sha,
            }
        },
    }
    preflight_path = tmp_path / preflight_relative
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    attempt = {
        "schema_version": 1,
        "protocol_id": MODULE.ANALYSIS_ID,
        "status": "attempt_started_no_process_launched",
        "scientific_outcomes_inspected_by_launcher": False,
        "model_process_count_at_publication": 0,
        "started_at": "2026-08-08T00:00:00+00:00",
        "git_freeze": {
            "audited_commit": audited_commit,
            "execution_commit": freeze_commit,
            "origin_main_commit": freeze_commit,
            "branch": "main",
        },
        "preflight": {
            "path": preflight_relative.as_posix(),
            "sha256": hashlib.sha256(preflight_path.read_bytes()).hexdigest(),
        },
        "manifest": {
            "path": MODULE.MANIFEST_PATH.as_posix(),
            "sha256": manifest_sha,
        },
        "config_order": [
            authority["roles"][arm][role]["config"].as_posix()
            for arm in MODULE.ARM_ORDER
            for role in MODULE.FAMILY_ORDER
        ],
        "run_names": [
            authority["roles"][arm][role]["run_name"]
            for arm in MODULE.ARM_ORDER
            for role in MODULE.FAMILY_ORDER
        ],
        "initial_namespace_check": {
            "resume_allowed": False,
            "run_name_count": 10,
            "existing_run_destination_count": 0,
            "launcher_log_namespace_preexisting": False,
        },
        "launcher_log_namespace": "logs",
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
    }
    attempt_path = tmp_path / attempt_relative
    attempt_path.write_text(json.dumps(attempt), encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "protocol_id": MODULE.ANALYSIS_ID,
        "status": "execution_complete_analysis_not_run",
        "scientific_outcomes_inspected_by_launcher": False,
        "freeze_commit": freeze_commit,
        "audited_commit": audited_commit,
        "branch": "main",
        "attempt_started_receipt": {
            "path": attempt_relative.as_posix(),
            "sha256": hashlib.sha256(attempt_path.read_bytes()).hexdigest(),
        },
        "preflight_path": preflight_relative.as_posix(),
        "preflight_sha256": hashlib.sha256(preflight_path.read_bytes()).hexdigest(),
        "started_at": "2026-08-08T00:00:00+00:00",
        "finished_at": "2026-08-08T00:03:00+00:00",
        "process_isolation": "strictly_sequential_independent_python_processes",
        "simultaneous_full_model_residency": False,
        "resume_policy": "forbidden_in_v1_new_versioned_freeze_required",
        "initial_namespace_check": {
            "resume_allowed": False,
            "run_name_count": 10,
            "existing_run_destination_count": 0,
            "launcher_log_namespace_preexisting": False,
        },
        "processes": processes,
        "completed_process_count": 10,
        "expected_process_count": 10,
        "analysis_authorized": True,
        "failed_execution_receipt_written": False,
    }
    receipt_path = tmp_path / execution_relative
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    binding = MODULE._validate_execution_receipt(tmp_path, authority)
    assert binding["freeze_commit"] == freeze_commit

    failed_path = tmp_path / failed_relative
    failed_path.write_text("{}", encoding="utf-8")
    with pytest.raises(MODULE.TransportAnalysisError, match="Failed-execution"):
        MODULE._validate_execution_receipt(tmp_path, authority)
    failed_path.unlink()

    receipt["resume_policy"] = "allowed"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(MODULE.TransportAnalysisError, match="resume_policy"):
        MODULE._validate_execution_receipt(tmp_path, authority)

    receipt["resume_policy"] = "forbidden_in_v1_new_versioned_freeze_required"
    preflight["git_authority"]["origin_main_commit"] = "d" * 40
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    new_preflight_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
    receipt["preflight_sha256"] = new_preflight_sha
    attempt["preflight"]["sha256"] = new_preflight_sha
    attempt_path.write_text(json.dumps(attempt), encoding="utf-8")
    receipt["attempt_started_receipt"]["sha256"] = hashlib.sha256(
        attempt_path.read_bytes()
    ).hexdigest()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(MODULE.TransportAnalysisError, match="Git authority"):
        MODULE._validate_execution_receipt(tmp_path, authority)
