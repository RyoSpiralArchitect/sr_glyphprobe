from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "semantic_atlas_cross_model_replication_v0.py"
SPEC = importlib.util.spec_from_file_location("semantic_atlas_cross_model_replication", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeTokenizer:
    eos_token_id = 0
    vocab_size = 1_200_000

    def encode(self, text: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        if text == " a":
            return [1]
        if text == " |":
            return [2]
        suffixes = ((" a", 1), (" |", 2))
        for unit, token_id in suffixes:
            repeats = 0
            stem = text
            while stem.endswith(unit):
                repeats += 1
                stem = stem[: -len(unit)]
            if repeats:
                return [1000 + ord(char) for char in stem] + [token_id] * repeats
        return [1000 + ord(char) for char in text]

    def decode(
        self,
        ids: list[int],
        *,
        clean_up_tokenization_spaces: bool,
        skip_special_tokens: bool,
    ) -> str:
        assert clean_up_tokenization_spaces is False
        assert skip_special_tokens is False
        pieces: list[str] = []
        for value in ids:
            if value == 1:
                pieces.append(" a")
            elif value == 2:
                pieces.append(" |")
            else:
                pieces.append(chr(value - 1000))
        return "".join(pieces)


def test_population_and_source_bindings_are_exact() -> None:
    result = MODULE.audit_design()

    assert result["status"] == "pass"
    assert result["population_items"] == 292
    assert result["model_cells"] == 9
    assert result["core_cells"] == 4
    assert result["t10_candidate_model_forward_calls"] == 0
    assert len(MODULE.items()) == 292


def test_primary_roster_endpoint_and_acquisition_budget_are_frozen() -> None:
    config = MODULE._config()

    assert tuple(config["endpoints"]["order"]) == MODULE.ENDPOINT_ORDER
    assert config["endpoints"]["primary"]["api_contract"] == "output.hidden_states[-1]"
    assert config["endpoints"]["secondary"]["decision_authorized"] is False
    assert config["endpoints"]["secondary"]["cannot_rescue_primary"] is True
    assert config["models"]["order"] == list(MODULE.model_roles())
    assert len(config["models"]["core"]) == 4
    assert len(config["models"]["extension"]) == 5
    assert config["acquisition"]["item_shard_size"] == 8
    assert config["acquisition"]["expected_shards_per_model"] == 37
    assert config["acquisition"]["expected_model_forward_calls_per_model"] == 1752
    assert config["acquisition"]["expected_total_model_forward_calls"] == 15768
    assert config["acquisition"]["expected_total_readout_vectors"] == 126144


def test_fake_tokenizer_proves_exact_carrier_and_stratum_contracts() -> None:
    result = MODULE._tokenize_roster(FakeTokenizer(), MODULE._config())
    receipt = result["receipt"]

    assert receipt["item_count"] == 292
    assert set(receipt["ordered_sequence_sha256"]["raw"]) == set(MODULE.VIEW_ORDER)
    assert receipt["carriers"]["article_a"]["token_id"] == 1
    assert receipt["carriers"]["pipe"]["token_id"] == 2
    assert receipt["carriers"]["article_a"]["prefix_exact_count"] == 876
    assert receipt["carriers"]["pipe"]["decode_exact_count"] == 876
    strata = receipt["exact_triple_strata"]
    assert strata["eligible_item_count"] >= 250
    assert sorted(index for group in strata["eligible_local_strata"] for index in group) == list(
        range(strata["eligible_item_count"])
    )
    assert all(len(group) >= 2 for group in strata["eligible_local_strata"])


def test_weight_artifact_completeness_fails_on_missing_index_shard(tmp_path: Path) -> None:
    (tmp_path / "model-00001-of-00002.safetensors").write_bytes(b"one")
    (tmp_path / "model.safetensors.index.json").write_text(
        json.dumps(
            {
                "weight_map": {
                    "a": "model-00001-of-00002.safetensors",
                    "b": "model-00002-of-00002.safetensors",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(MODULE.atlas.AtlasError, match="missing shard"):
        MODULE._validate_weight_artifact_completeness(tmp_path)

    (tmp_path / "model-00002-of-00002.safetensors").write_bytes(b"two")
    receipt = MODULE._validate_weight_artifact_completeness(tmp_path)
    assert receipt["weight_file_count"] == 2
    assert receipt["index_file_count"] == 1
    assert receipt["index_referenced_weight_file_count"] == 2


def test_stratified_permutation_never_crosses_exact_strata() -> None:
    groups = [[0, 1, 2], [3, 4], [5, 6, 7, 8]]
    permutation = MODULE.stratified_permutation(np.random.default_rng(11), 9, groups)

    assert sorted(permutation.tolist()) == list(range(9))
    for group in groups:
        assert set(permutation[group].tolist()) == set(group)
    with pytest.raises(MODULE.atlas.AtlasError):
        MODULE.stratified_permutation(np.random.default_rng(1), 4, [[0, 1], [2]])


def test_unrestricted_and_matched_randomization_are_deterministic() -> None:
    item_count = 12
    order = np.arange(item_count, dtype=np.int64)
    name = np.tile(order, (8, 1))
    codepoint = np.tile(np.roll(order, 1), (8, 1))

    unrestricted = MODULE.randomization_test(
        name,
        codepoint,
        draws=99,
        seed=23,
        practical_minimum=0.02,
        strata=None,
    )
    matched = MODULE.randomization_test(
        name,
        codepoint,
        draws=99,
        seed=23,
        practical_minimum=0.02,
        strata=[list(range(6)), list(range(6, 12))],
    )
    matched_again = MODULE.randomization_test(
        name,
        codepoint,
        draws=99,
        seed=23,
        practical_minimum=0.02,
        strata=[list(range(6)), list(range(6, 12))],
    )

    assert unrestricted["observed_minimum_cell_contrast"] == 1.0
    assert unrestricted["p_value"] == 0.01
    assert matched == matched_again
    assert matched["p_value"] == 0.01
    assert matched["practical_pass"] is True

    name[7] = codepoint[7]
    failed = MODULE.randomization_test(
        name,
        codepoint,
        draws=99,
        seed=23,
        practical_minimum=0.02,
        strata=None,
    )
    assert failed["observed_minimum_cell_contrast"] == 0.0
    assert failed["practical_pass"] is False


def test_partial_conjunction_and_holm_rules_are_exact() -> None:
    partial = MODULE.partial_conjunction(
        {"a": 0.001, "b": 0.01, "c": 0.02, "d": 0.8}, r=3
    )
    assert partial["m"] == 4
    assert partial["r"] == 3
    assert partial["rth_smallest_model_role"] == "c"
    assert partial["multiplier"] == 2
    assert partial["p_value"] == pytest.approx(0.04)

    holm = MODULE.holm_adjust({"a": 0.001, "b": 0.01, "c": 0.2}, alpha=0.05)
    assert holm["a"]["reject"] is True
    assert holm["b"]["reject"] is True
    assert holm["c"]["reject"] is False
    assert holm["a"]["adjusted_p"] == pytest.approx(0.003)
    assert holm["b"]["adjusted_p"] == pytest.approx(0.02)


def test_endpoint_semantics_audit_is_bound_and_non_candidate() -> None:
    receipt = MODULE.atlas._read_json(ROOT / MODULE.ENDPOINT_AUDIT_PATH)

    assert receipt["status"] == "pass"
    assert receipt["returned_vs_raw_last_block_max_abs"] > 0.0
    assert receipt["returned_vs_explicit_final_norm_max_abs"] == 0.0
    assert receipt["candidate_model_weights_loaded"] is False
    assert receipt["candidate_population_model_forward_calls"] == 0
    assert receipt["synthetic_model_forward_calls"] == 1


def test_forbidden_actions_block_post_outcome_rescue_and_semantic_claims() -> None:
    config = MODULE._config()
    forbidden = set(config["forbidden_actions"])

    assert "any_t10_candidate_model_forward_before_freeze_commit" in forbidden
    assert "secondary_endpoint_rescue_of_primary" in forbidden
    assert "model_cell_holm_family_rescue_of_cross_model_primary" in forbidden
    assert "post_outcome_threshold_seed_stratum_or_partial_conjunction_change" in forbidden
    assert "semantic_decomposition_causal_mechanistic_behavioral_scale_law_or_model_general_claim" in forbidden
    assert config["secondary_outputs"]["decision_authorized"] is False
    assert config["cross_model_primary"]["independence_claim_authorized"] is False


def test_freeze_audits_if_manifest_exists() -> None:
    if (ROOT / MODULE.FREEZE_PATH).is_file():
        assert MODULE.audit_freeze()["status"] == "pass"
