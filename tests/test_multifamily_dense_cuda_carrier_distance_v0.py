from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "multifamily_dense_cuda_carrier_distance_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "multifamily_dense_cuda_carrier_distance_v0", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@dataclass
class Tokenized:
    token_ids: list[int]
    tokens: list[str]


def _config() -> dict:
    return yaml.safe_load(
        (ROOT / "configs" / "multifamily_dense_cuda_carrier_distance_v0.yaml").read_text()
    )


def _panel() -> list[dict]:
    return MODULE._panel(_config())


def _synthetic_spec(raw: list[list[int]]) -> dict:
    return {
        "raw_tokenization_contract": {
            "expected_item_token_count_histogram": dict(
                sorted(__import__("collections").Counter(map(len, raw)).items())
            ),
            "expected_unique_sequence_count": len(set(map(tuple, raw))),
            "shared_prefix_token_ids": MODULE._shared_prefix(raw),
            "ordered_sequence_sha256": MODULE._json_sequence_sha256(raw),
            "matching_family": "synthetic_exact_roster",
        },
        "carrier_token_ids": {"article_a": 7001, "pipe": 7002},
        "combined_sequence_sha256": {
            "article_a": MODULE._json_sequence_sha256(
                [row + [7001] * 8 for row in raw]
            ),
            "pipe": MODULE._json_sequence_sha256([row + [7002] * 8 for row in raw]),
        },
    }


def test_config_freezes_four_dense_cuda_cells_and_t5_endpoint() -> None:
    config = _config()
    assert config["protocol_id"] == MODULE.PROTOCOL_ID
    assert config["models"]["order"] == list(MODULE.MODEL_ROLES)
    assert config["input"]["carrier_order"] == ["article_a", "pipe"]
    assert config["input"]["distance_order"] == [1, 2, 4, 8]
    assert config["runtime"]["backend"] == "transformers"
    assert config["runtime"]["device"] == "cuda"
    assert config["runtime"]["dtype"] == "bfloat16"
    endpoint = config["primary_endpoint"]
    assert endpoint["id"] == "distance1_recurrence_intersection_logdistance_attenuation"
    assert endpoint["distance_contrast_weights"] == [0.375, 0.125, -0.125, -0.375]
    assert endpoint["randomization_draws"] == 19999
    assert endpoint["seed"] == 20260831
    assert endpoint["hypothesis_family"] == list(MODULE.MODEL_ROLES)
    assert config["selection_provenance"]["selected_after_t5_outcomes_were_known"] is True
    assert config["selection_provenance"]["scale_effect_authorized"] is False


def test_panel_is_unchanged_five_by_ten() -> None:
    config = _config()
    panel = _panel()
    assert len(panel) == 50
    assert [item["id"] for item in panel] == [
        f"{family}_slot_{slot:02d}"
        for family in config["panel"]["family_order"]
        for slot in config["panel"]["slot_order"]
    ]


@pytest.mark.parametrize(
    ("raw", "expected_histogram", "expected_prefix"),
    [
        ([[1000 + index] for index in range(50)], {"1": 50}, []),
        (
            [[2000 + index] for index in range(49)] + [[8, 9, 10, 11]],
            {"1": 49, "4": 1},
            [],
        ),
        (
            [[55, 1]] + [[55, 2, 3, 4, 100 + index] for index in range(49)],
            {"2": 1, "5": 49},
            [55],
        ),
    ],
)
def test_exact_raw_roster_accepts_all_three_tokenizer_classes(
    raw: list[list[int]], expected_histogram: dict[str, int], expected_prefix: list[int]
) -> None:
    receipt = MODULE.validate_raw_tokenizations(
        [Tokenized(row, []) for row in raw],
        _panel(),
        _synthetic_spec(raw),
    )
    assert receipt["observed_item_token_count_histogram"] == expected_histogram
    assert receipt["shared_prefix_token_ids"] == expected_prefix
    assert receipt["unique_sequence_count"] == 50


def test_exact_raw_roster_rejects_one_changed_sequence() -> None:
    raw = [[5000 + index] for index in range(50)]
    spec = _synthetic_spec(raw)
    changed = [row.copy() for row in raw]
    changed[17][0] += 100
    with pytest.raises(MODULE.base.ProtocolError, match="ordered-sequence SHA-256"):
        MODULE.validate_raw_tokenizations(
            [Tokenized(row, []) for row in changed], _panel(), spec
        )


def test_carrier_contract_accepts_exact_eight_token_tails_and_rejects_near_miss() -> None:
    raw = [[6100 + index] for index in range(50)]
    spec = _synthetic_spec(raw)
    input_spec = _config()["input"]
    rows = {
        carrier: [
            Tokenized(row + [spec["carrier_token_ids"][carrier]] * 8, [])
            for row in raw
        ]
        for carrier in input_spec["carrier_order"]
    }
    receipt = MODULE.validate_carrier_tokenizations(
        [Tokenized(row, []) for row in raw], rows, _panel(), spec, input_spec
    )
    assert receipt["distance_order"] == [1, 2, 4, 8]
    assert receipt["carriers"]["article_a"]["raw_prefix_preserved_count"] == 50
    assert receipt["carriers"]["pipe"]["unique_combined_sequence_count"] == 50
    rows["pipe"][3].token_ids[-1] += 1
    with pytest.raises(MODULE.base.ProtocolError, match="Raw-plus-carrier contract"):
        MODULE.validate_carrier_tokenizations(
            [Tokenized(row, []) for row in raw], rows, _panel(), spec, input_spec
        )


def test_gemma3_adapter_adds_nested_decoder_path_without_removing_existing_paths() -> None:
    assert MODULE.DenseCudaTransformersBackend._BLOCK_PATHS[0] == (
        "model.language_model.layers"
    )
    assert "model.layers" in MODULE.DenseCudaTransformersBackend._BLOCK_PATHS


def test_outcome_registry_is_complete_and_nonselective() -> None:
    def cells(rejected: set[str]) -> dict[str, dict[str, bool]]:
        return {role: {"holm_reject": role in rejected} for role in MODULE.MODEL_ROLES}

    assert MODULE._outcome_pattern(cells(set(MODULE.MODEL_ROLES))) == (
        "all_four_dense_distance_attenuation_candidate"
    )
    assert MODULE._outcome_pattern(cells({"gemma3_4b_it", "gemma3_12b_it"})) == (
        "gemma3_size_pair_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells({"gemma3_12b_it"})) == (
        "gemma3_12b_only_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells({"gemma2_2b_it", "gemma3_12b_it"})) == (
        "mixed_dense_model_distance_attenuation"
    )
    assert MODULE._outcome_pattern(cells(set())) == "no_dense_model_distance_attenuation"


def test_delegated_surface_restores_t5_globals() -> None:
    before = {
        "protocol": MODULE.t5.PROTOCOL_ID,
        "roles": MODULE.t5.MODEL_ROLES,
        "backend": MODULE.t5.frozen.MLXBackend,
        "runtime": MODULE.t5.base._model_runtime_check,
    }
    with MODULE._delegated_t5_surface():
        assert MODULE.t5.PROTOCOL_ID == MODULE.PROTOCOL_ID
        assert MODULE.t5.MODEL_ROLES == MODULE.MODEL_ROLES
        assert MODULE.t5.frozen.MLXBackend is MODULE.DenseCudaTransformersBackend
        assert MODULE.t5.base._model_runtime_check is MODULE._runtime_check
    assert MODULE.t5.PROTOCOL_ID == before["protocol"]
    assert MODULE.t5.MODEL_ROLES == before["roles"]
    assert MODULE.t5.frozen.MLXBackend is before["backend"]
    assert MODULE.t5.base._model_runtime_check is before["runtime"]


def test_freeze_manifest_binds_static_assets_and_zero_forward_preflight() -> None:
    audit = MODULE.audit_freeze()
    manifest = json.loads((ROOT / MODULE.MANIFEST_PATH).read_text())
    assert audit["status"] == "pass"
    assert audit["frozen_asset_count"] == len(MODULE.FROZEN_ASSET_PATHS)
    assert manifest["model_forward_calls_at_freeze"] == 0
    assert manifest["intervention_calls_at_freeze"] == 0
    assert manifest["generation_calls_at_freeze"] == 0
    assert manifest["protected_target_files_opened_at_freeze"] == 0
    assert set(manifest["model_artifacts"]) == set(MODULE.MODEL_ROLES)
    assert _config()["models"]["order"] == list(MODULE.MODEL_ROLES)


def test_protocol_forbids_intervention_selection_and_scale_overclaim() -> None:
    config = _config()
    forbidden = set(config["forbidden_actions"])
    assert "activation_intervention" in forbidden
    assert "behavioral_generation" in forbidden
    assert "protected_target_access" in forbidden
    assert "post_outcome_model_carrier_distance_layer_family_endpoint_or_seed_selection" in forbidden
    assert "model_scale_or_backend_effect_claim" in forbidden
    assert "inferential_pooling_with_t5" in forbidden
    source = SCRIPT.read_text()
    assert '"intervention_calls": 0' in source
    assert '"generation_calls": 0' in source
    assert '"protected_target_files_opened": 0' in source
    assert '"multiplicity_decision_authorized": False' in source
