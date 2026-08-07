from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
V1_SCRIPT = ROOT / "scripts" / "analyze_llama32_3b_mps_emoji_transport_v1.py"
V2_SCRIPT = ROOT / "scripts" / "analyze_llama32_3b_mps_emoji_transport_v2.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V1 = _load("focused_transport_v1_pristine", V1_SCRIPT)
V2 = _load("focused_transport_v2_adapter", V2_SCRIPT)


def _groups() -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(range(group * 4, group * 4 + 4)) for group in range(6))


def _vectors(slot_count: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = rng.normal(size=(5, 3, slot_count, 24, 10))
    return values / np.linalg.norm(values, axis=-1, keepdims=True)


def test_v2_namespace_and_public_contract_are_exact() -> None:
    assert V2.ANALYSIS_ID == "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2"
    assert V2.MANIFEST_PATH.as_posix() == (
        "data/manifests/llama32_3b_mps_emoji_transport_v2.json"
    )
    assert V2.PREFLIGHT_PATH.as_posix() == (
        "artifacts/llama32_3b_mps_emoji_transport_v2/preflight/"
        "tokenization_audit_v2.json"
    )
    assert V2.OUTPUT_FILENAMES[-2:] == (
        "llama32_3b_mps_emoji_transport_v2_receipt.json",
        "report.md",
    )
    assert V2.EXPECTED_OUTPUT_ROWS == V1.EXPECTED_OUTPUT_ROWS
    assert V2.OUTPUT_UNIQUE_KEYS == V1.OUTPUT_UNIQUE_KEYS
    assert V2.BOOTSTRAP_REPLICATES == V1.BOOTSTRAP_REPLICATES == 20_000
    assert V2.BOOTSTRAP_SEED == V1.BOOTSTRAP_SEED == 20_260_808
    assert V2.PRIMARY_CRITERION_ID == V1.PRIMARY_CRITERION_ID
    assert V2.PRIMARY_CRITERION_RULE == V1.PRIMARY_CRITERION_RULE
    parameters = inspect.signature(V2.analyze_transport).parameters
    assert "bootstrap_replicates" not in parameters
    assert "bootstrap_seed" not in parameters


def test_v2_ten_role_bindings_use_only_v2_configs_and_run_names() -> None:
    observed = []
    for arm in V2.ARM_ORDER:
        for family in V2.FAMILY_ORDER:
            definition = V2.ARM_DEFINITIONS[arm]
            config = definition["config_paths"][family].as_posix()
            run_name = definition["run_names"][family]
            assert config == f"configs/e2_llama32_3b_mps_{arm}_{family}_v2.yaml"
            assert run_name == f"e2-llama32-3b-mps-{arm}-{family}-transport-v2"
            observed.append((config, run_name))
    assert len(observed) == len(set(observed)) == 10
    assert all("_v1.yaml" not in config for config, _ in observed)
    assert all(not run_name.endswith("-v1") for _, run_name in observed)


@pytest.mark.parametrize("slot_count", [10, 7])
def test_v2_scoring_and_bootstrap_are_bitwise_v1_identical(slot_count: int) -> None:
    vectors = _vectors(slot_count, 711 + slot_count)
    weights_v1, draws_v1 = V1._bootstrap_weights(13, 44, 24, _groups())
    weights_v2, draws_v2 = V2._bootstrap_weights(13, 44, 24, _groups())
    assert np.array_equal(weights_v2, weights_v1)
    assert np.array_equal(draws_v2, draws_v1)
    scores_v1 = V1._score_layer_chunk_by_seed(vectors, weights_v1, _groups())
    scores_v2 = V2._score_layer_chunk_by_seed(vectors, weights_v2, _groups())
    assert np.array_equal(scores_v2, scores_v1)

    tensor = np.stack([vectors, np.roll(vectors, 1, axis=-1)], axis=1)
    bootstrap_v1 = V1._bootstrap_endpoints(
        tensor, weights_v1, draws_v1, _groups(), chunk_size=5
    )
    bootstrap_v2 = V2._bootstrap_endpoints(
        tensor, weights_v2, draws_v2, _groups(), chunk_size=5
    )
    for endpoint in ("matrix_means", "specificity_means", "global_specificity"):
        assert np.array_equal(bootstrap_v2[endpoint], bootstrap_v1[endpoint])


def test_v2_primary_boundary_is_exactly_v1() -> None:
    for interval, expected in (
        ({"low": np.nextafter(0.0, 1.0), "high": 0.2}, True),
        ({"low": 0.0, "high": 0.2}, False),
        ({"low": -0.1, "high": 0.2}, False),
    ):
        assert V2._primary_criterion_met(interval) is expected
        assert V2._primary_criterion_met(interval) is V1._primary_criterion_met(
            interval
        )


def test_v2_manifest_requires_exact_v1_analyzer_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid_manifest = {
        "manifest_id": V2.MANIFEST_ID,
        "analysis": {"v1_analysis_dependency": V2._v1_dependency_record()},
    }
    monkeypatch.setattr(V2, "_ORIGINAL_V1_LOAD_FIXED_AUTHORITY", lambda _root: {})
    monkeypatch.setattr(
        V2,
        "_ORIGINAL_V1_READ_JSON_OBJECT",
        lambda _path, _description: valid_manifest,
    )
    authority = V2._load_fixed_authority_v2(ROOT)
    assert authority["v1_analysis_dependency"] == V2._v1_dependency_record()

    valid_manifest["analysis"]["v1_analysis_dependency"]["sha256"] = "0" * 64
    with pytest.raises(V2.TransportAnalysisError, match="v1 analysis dependency"):
        V2._load_fixed_authority_v2(ROOT)


def test_v2_rejects_dependency_drift_before_reimport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(V2, "V1_ANALYZER_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match="v1 analyzer dependency hash"):
        V2._import_v1_analyzer()


def test_v2_receipt_redirect_adds_v1_provenance_without_touching_v1(
    tmp_path: Path,
) -> None:
    v1_hash_before = hashlib.sha256(V1_SCRIPT.read_bytes()).hexdigest()
    receipt: dict[str, Any] = {
        "analysis_id": V2.ANALYSIS_ID,
        "output_inventory": list(V2.OUTPUT_FILENAMES),
    }
    legacy_destination = tmp_path / V2.V1_OUTPUT_RECEIPT_FILENAME
    V2._write_json_v2(legacy_destination, receipt)
    v2_destination = tmp_path / V2.OUTPUT_RECEIPT_FILENAME
    assert legacy_destination.exists() is False
    stored = json.loads(v2_destination.read_text(encoding="utf-8"))
    assert stored["v1_analysis_dependency"] == V2._v1_dependency_record()
    assert stored["version_transition"] == {
        "predecessor_protocol_id": V2.V1_ANALYSIS_ID,
        "scope": "preflight_implementation_and_version_namespace_only",
        "endpoint_math_changed": False,
        "bootstrap_changed": False,
        "primary_criterion_changed": False,
        "row_contracts_changed": False,
    }
    assert receipt["v1_analysis_dependency"] == V2._v1_dependency_record()
    assert hashlib.sha256(V1_SCRIPT.read_bytes()).hexdigest() == v1_hash_before
    assert v1_hash_before == V2.V1_ANALYZER_SHA256
    assert (
        hashlib.sha256((ROOT / V2.E1_ANALYZER_PATH).read_bytes()).hexdigest()
        == V2.E1_ANALYZER_SHA256
    )


def test_v2_execution_adapter_requires_raw_v2_no_resume_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution = Path("execution.json")
    attempt = Path("attempt.json")
    preflight = Path("preflight.json")
    failed = Path("failed.json")
    monkeypatch.setattr(V2, "EXECUTION_RECEIPT_PATH", execution)
    monkeypatch.setattr(V2, "ATTEMPT_STARTED_RECEIPT_PATH", attempt)
    monkeypatch.setattr(V2, "PREFLIGHT_PATH", preflight)
    monkeypatch.setattr(V2, "FAILED_EXECUTION_RECEIPT_PATH", failed)

    (tmp_path / execution).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "resume_policy": V2.RESUME_POLICY,
                "preflight_path": preflight.as_posix(),
                "attempt_started_receipt": {"path": attempt.as_posix()},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / attempt).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "resume_policy": V2.RESUME_POLICY,
                "preflight": {"path": preflight.as_posix()},
                "manifest": {"path": V2.MANIFEST_PATH.as_posix()},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / preflight).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "audit_role": V2.PREFLIGHT_AUDIT_ROLE,
                "v1_preflight_outcome": V2.V1_PREFLIGHT_OUTCOME,
                "v2_correction_scope": V2.V2_CORRECTION_SCOPE,
                "tokenization": {
                    "rules": {
                        "v1_raw_contract_preserved": True,
                        "wrapper_context_profiles_exactly_frozen": True,
                        "full50_exceptions_use_contextual_first_token_substitution": True,
                        "wrapper_outside_tokens_identical": True,
                        "wrapper_core_token_count_position_and_outside_isomorphic": True,
                        "contextual_first_token_distribution": {"9468": 7, "11410": 9},
                    }
                },
                "authorization": {"frozen_grid_execution_authorized": True},
            }
        ),
        encoding="utf-8",
    )

    def original_validator(root: Path, _authority: dict[str, Any]) -> dict[str, Any]:
        normalized_execution = V2.v1._read_json_object(
            root / execution, "normalized execution"
        )
        normalized_attempt = V2.v1._read_json_object(
            root / attempt, "normalized attempt"
        )
        assert normalized_execution["resume_policy"] == V2.V1_RESUME_POLICY
        assert normalized_attempt["resume_policy"] == V2.V1_RESUME_POLICY
        return {"resume_policy": V2.V1_RESUME_POLICY}

    monkeypatch.setattr(
        V2, "_ORIGINAL_V1_VALIDATE_EXECUTION_RECEIPT", original_validator
    )
    binding = V2._validate_execution_receipt_v2(tmp_path, {})
    assert binding["resume_policy"] == V2.RESUME_POLICY
    assert binding["versioned_protocol_id"] == V2.ANALYSIS_ID

    raw = json.loads((tmp_path / execution).read_text(encoding="utf-8"))
    raw["resume_policy"] = V2.V1_RESUME_POLICY
    (tmp_path / execution).write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(V2.TransportAnalysisError, match="execution resume policy"):
        V2._validate_execution_receipt_v2(tmp_path, {})

    raw["resume_policy"] = V2.RESUME_POLICY
    (tmp_path / execution).write_text(json.dumps(raw), encoding="utf-8")
    (tmp_path / failed).write_text("{}", encoding="utf-8")
    with pytest.raises(V2.TransportAnalysisError, match="Failed-execution"):
        V2._validate_execution_receipt_v2(tmp_path, {})


def test_v2_execution_adapter_rejects_wrong_contextual_preflight_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execution = Path("execution.json")
    attempt = Path("attempt.json")
    preflight = Path("preflight.json")
    failed = Path("failed.json")
    monkeypatch.setattr(V2, "EXECUTION_RECEIPT_PATH", execution)
    monkeypatch.setattr(V2, "ATTEMPT_STARTED_RECEIPT_PATH", attempt)
    monkeypatch.setattr(V2, "PREFLIGHT_PATH", preflight)
    monkeypatch.setattr(V2, "FAILED_EXECUTION_RECEIPT_PATH", failed)
    (tmp_path / execution).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "resume_policy": V2.RESUME_POLICY,
                "preflight_path": preflight.as_posix(),
                "attempt_started_receipt": {"path": attempt.as_posix()},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / attempt).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "resume_policy": V2.RESUME_POLICY,
                "preflight": {"path": preflight.as_posix()},
                "manifest": {"path": V2.MANIFEST_PATH.as_posix()},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / preflight).write_text(
        json.dumps(
            {
                "protocol_id": V2.ANALYSIS_ID,
                "audit_role": V2.PREFLIGHT_AUDIT_ROLE,
                "v1_preflight_outcome": V2.V1_PREFLIGHT_OUTCOME,
                "v2_correction_scope": "raw_contract_changed",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(V2.TransportAnalysisError, match="implementation binding"):
        V2._validate_execution_receipt_v2(tmp_path, {})


def test_v2_source_does_not_name_or_open_protected_banks() -> None:
    source = V2_SCRIPT.read_text(encoding="utf-8")
    assert "p2_confirmatory_targets" not in source
    assert "c1_causal_targets" not in source
