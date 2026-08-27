from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V0 = _load("llama_m2_bridge_analysis_v0_test", "scripts/analyze_llama32_3b_instruct_mps_m2_bridge_v0.py")
V1 = _load("llama_m2_bridge_analysis_v1_test", "scripts/analyze_llama32_3b_instruct_mps_m2_bridge_v1.py")
BUILDER = _load(
    "llama_m2_bridge_analysis_v1_builder_test",
    "scripts/build_llama32_3b_instruct_mps_m2_bridge_analysis_v1_manifest.py",
)


def test_only_depth_representation_contract_changes_the_estimand_is_fixed() -> None:
    for name in (
        "LAYERS",
        "STRENGTH",
        "DIRECTION_SEEDS",
        "FINGERPRINT_DIM",
        "FINGERPRINT_SEED",
        "RANDOM_DIRECTIONS_PER_LAYER",
        "BOOTSTRAP_REPLICATES",
        "BOOTSTRAP_SEED",
        "DELTA",
        "ROLE_ORDER",
    ):
        assert getattr(V1, name) == getattr(V0, name)
    assert inspect.getsource(V1._score_layer_chunk) == inspect.getsource(V0._score_layer_chunk)
    assert inspect.getsource(V1._bootstrap) == inspect.getsource(V0._bootstrap)


def test_v1_accepts_normalized_resolved_config_and_rejects_layer_indices() -> None:
    path = ROOT / "configs" / "llama32_3b_instruct_mps_m2_primary_v0.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    V1._validate_config(config, "primary")
    wrong = copy.deepcopy(config)
    wrong["capture"]["layers"] = [5, 11]
    with pytest.raises(V1.BridgeAnalysisError, match="capture.layers"):
        V1._validate_config(wrong, "primary")


def test_scoring_math_matches_v0_exactly() -> None:
    rng = np.random.default_rng(21)
    vectors = rng.normal(size=(4, 3, 10, 24, 12))
    vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
    weights = np.ones((2, 24), dtype=np.int16)
    weights[1, ::4] = 2
    groups = [tuple(range(start, start + 4)) for start in range(0, 24, 4)]
    v0 = V0._score_layer_chunk(vectors, weights, groups)
    v1 = V1._score_layer_chunk(vectors, weights, groups)
    np.testing.assert_array_equal(v1[0], v0[0])
    np.testing.assert_array_equal(v1[1], v0[1])


def test_manifest_binds_execution_and_excludes_protected_banks() -> None:
    manifest = BUILDER.build_manifest(ROOT)
    assert manifest["analysis_id"] == V1.ANALYSIS_ID
    assert manifest["execution_receipt"]["sha256"] == V1.EXECUTION_RECEIPT_SHA256
    assert manifest["correction"]["scientific_outcomes_seen_before_v1_freeze"] is False
    assert not set(manifest["static_files"]) & BUILDER.FORBIDDEN
    assert set(manifest["forbidden_paths_absent"]) == BUILDER.FORBIDDEN


def test_failed_v0_attempt_is_explicit_and_non_scientific() -> None:
    path = (
        ROOT
        / "validation"
        / "llama32_3b_instruct_mps_m2_bridge_v0"
        / "analysis_v0_failure.json"
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["status"] == "failed_closed_before_scientific_outcome_read"
    assert receipt["files_reached_before_failure"]["run_summary_read"] is False
    assert receipt["files_reached_before_failure"]["intervention_ledger_read"] is False
    assert receipt["claim_boundary"]["scientific_decision_assigned"] is False


def test_v1_analysis_surface_is_model_free_and_public_freeze_gated() -> None:
    source = (ROOT / "scripts" / "analyze_llama32_3b_instruct_mps_m2_bridge_v1.py").read_text(
        encoding="utf-8"
    )
    assert "_validate_public_analysis_freeze" in source
    assert "AutoModel" not in source
    assert "p2_confirmatory_targets_v1.jsonl" not in source
    assert "c1_confirmatory_targets_v1.jsonl" not in source
    assert "c1_causal_holdout_targets_v1.jsonl" not in source
