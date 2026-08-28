from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_semantic_atlas_cross_model_replication_v0_result.py"
BUNDLE = ROOT / "artifacts" / "semantic_atlas_cross_model_replication_v0"
MANIFEST = BUNDLE / "PUBLIC_MANIFEST.json"
EXPECTED_MANIFEST_SHA256 = (
    "90af3c437679399c5a246c1a1c2e603e189761b4693bc3eb74602600361a7306"
)
SPEC = importlib.util.spec_from_file_location("validate_t10_result", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_committed_manifest_binds_ledgers_sessions_validation_and_validator() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert _sha256(MANIFEST) == EXPECTED_MANIFEST_SHA256
    assert manifest["freeze"]["manifest_sha256"] == (
        "8673bc51490460b3e8908f766b592169942bf6a7e88d292c50b427e5283f34a4"
    )
    bindings = manifest["ledger_bindings"]
    assert bindings["analysis_sha256sums_sha256"] == _sha256(
        BUNDLE / "analysis" / "SHA256SUMS"
    )
    assert bindings["independent_validation_sha256"] == _sha256(
        BUNDLE / "validation" / "independent_validation.json"
    )
    assert bindings["validator_script_sha256"] == _sha256(SCRIPT)
    assert len(bindings["models"]) == 9
    for role, values in bindings["models"].items():
        assert values["run_sha256sums_sha256"] == _sha256(
            BUNDLE / "runs" / role / "SHA256SUMS"
        )
        assert values["summary_sha256sums_sha256"] == _sha256(
            BUNDLE / "summaries" / role / "SHA256SUMS"
        )
        for name, expected in values["session_sha256"].items():
            assert expected == _sha256(BUNDLE / "runs" / role / name)


def test_compact_bundle_recomputes_registered_negative_primary() -> None:
    result = MODULE.validate(BUNDLE, None)

    assert result["status"] == "pass"
    assert result["compact_bundle"] == {
        "analysis_ledger_targets_rehashed": 4,
        "summary_ledger_targets_rehashed": 27,
        "run_ledger_targets_rehashed": 18,
        "model_cells": 9,
        "total_model_forward_calls": 15_768,
        "total_readout_vectors": 126_144,
        "total_shards": 333,
    }
    assert result["raw_archive"] == {"provided": False, "status": "not_checked"}
    assert result["cross_model_primary"] == {
        "partial_conjunction_p_value": 0.0001,
        "statistical_pass": True,
        "core_practical_pass_count": 2,
        "practical_pass": False,
        "positive": False,
        "authorized_wording": (
            "cross_model_replication_not_established_under_frozen_rule"
        ),
    }
    assert result["bounded_model_cell_pass_roles"] == [
        "llama32_3b_base_bf16",
        "qwen25_7b_base_bf16",
        "mistral7b_instruct_v03_bf16",
    ]


def test_randomization_and_holm_reimplementation_are_deterministic() -> None:
    order = np.arange(12, dtype=np.int64)
    name = np.tile(order, (8, 1))
    codepoint = np.tile(np.roll(order, 1), (8, 1))
    kwargs = {
        "draws": 99,
        "seed": 17,
        "practical_minimum": 0.02,
        "strata": [list(range(6)), list(range(6, 12))],
    }

    first = MODULE.randomization_component(name, codepoint, **kwargs)
    second = MODULE.randomization_component(name, codepoint, **kwargs)

    assert first == second
    assert first["observed_minimum_cell_contrast"] == 1.0
    assert first["p_value"] == 0.01
    adjusted = MODULE.holm_adjust({"a": 0.01, "b": 0.03, "c": 0.2}, 0.05)
    assert adjusted == {
        "a": {"adjusted_p": 0.03, "reject": True},
        "b": {"adjusted_p": 0.06, "reject": False},
        "c": {"adjusted_p": 0.2, "reject": False},
    }


def test_validation_output_is_atomic_and_no_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    MODULE.write_json_once(output, {"status": "pass"})
    original = output.read_bytes()

    with pytest.raises(MODULE.ValidationError, match="Output already exists"):
        MODULE.write_json_once(output, {"status": "changed"})

    assert output.read_bytes() == original
