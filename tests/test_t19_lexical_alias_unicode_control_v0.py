from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import t19_lexical_alias_unicode_control_v0 as t19  # noqa: E402


def test_three_banks_are_frozen_disjoint_and_alias_unique() -> None:
    audit = t19.audit_selection(rescan_exposure=False)
    assert audit == {
        "status": "pass",
        "observational_items": 110,
        "causal_source_items": 128,
        "causal_eval_items": 192,
        "selection_sha256": audit["selection_sha256"],
        "exposure_rescan": {"performed": False},
        "model_forward_calls": 0,
        "intervention_calls": 0,
    }
    observational = t19.items()
    source = t19.causal_items("source")
    evaluation = t19.causal_items("eval")
    assert Counter(row["kind"] for row in observational) == {
        "emoji": 55,
        "symbol": 55,
    }
    assert [row["selection_index"] for row in observational] == list(range(110))
    assert [row["bank_index"] for row in source] == list(range(128))
    assert [row["bank_index"] for row in evaluation] == list(range(192))
    all_rows = [*observational, *source, *evaluation]
    assert len({row["codepoint"] for row in all_rows}) == 430
    assert len({row["alias_label"] for row in all_rows}) == 430


def test_labels_and_nonemoji_symbol_contract() -> None:
    for row in [*t19.items(), *t19.causal_items("source"), *t19.causal_items("eval")]:
        assert len(row["glyph"]) == 1
        assert t19._words(row["canonical_label"])
        assert t19._words(row["alias_label"])
        assert t19._words(row["canonical_label"]).isdisjoint(
            t19._words(row["alias_label"])
        )
    symbols = [row for row in t19.items() if row["kind"] == "symbol"]
    assert all(row["unicode_category"].startswith("S") for row in symbols)
    assert all(row["prior_repository_text_surface_exposed"] is False for row in symbols)
    manifest = json.loads((ROOT / t19.SELECTION_PATH).read_text(encoding="utf-8"))
    assert manifest["exposure_audit"]["selected_symbol_surface_hits"] == 0
    assert manifest["human_paraphrase_quality_claim_authorized"] is False


def test_design_budget_and_primary_contract() -> None:
    value = t19.audit_design()
    assert value["status"] == "design_pass_zero_t19_model_forwards_or_interventions"
    assert value["expected_model_forward_calls"] == 7_920
    assert value["expected_readout_vectors"] == 285_120
    assert value["model_forwards"] == 0
    assert value["causal_go_gate_open"] is False
    assert [(row["site"], row["block_index"]) for row in value["causal_primary_sites"]] == [
        ("attn_out", 24),
        ("mlp_out", 24),
    ]
    config = t19._config()
    assert config["model_primary_endpoint"]["randomization_draws"] == 19_999
    assert config["cross_model_primary"]["r"] == 3
    assert tuple(config["depth"]["primary_normalized_fractions"]) == t19.PRIMARY_DEPTHS


def test_all_tokenizer_preflights_are_zero_forward_and_above_floor() -> None:
    engineering = json.loads(
        (ROOT / t19.ENGINEERING_PREFLIGHT_PATH).read_text(encoding="utf-8")
    )
    assert engineering["status"] == "nine_tokenizer_preflights_pass_zero_t19_model_forwards"
    assert engineering["model_forwards"] == 0
    assert engineering["minimum_matched_items"] == 63
    assert engineering["minimum_matched_items_by_kind"] == {"emoji": 31, "symbol": 32}
    for role in t19.MODEL_ROLES:
        receipt = json.loads(t19._tokenizer_receipt_path(role).read_text(encoding="utf-8"))
        assert receipt["model_forward_calls"] == 0
        assert receipt["model_weights_loaded"] is False
        assert receipt["t10_reference_surface_sequence_equivalence"] is True
        primary = receipt["tokenizer"]["primary_exact_strata"]
        assert primary["eligible_item_count"] >= 52
        assert min(primary["eligible_item_count_by_kind"].values()) >= 24


def test_strata_receipt_uses_kind_local_permutation_indices() -> None:
    rows = [
        {
            "item_index": index,
            "glyph_kind": kind,
            "a": length,
        }
        for index, (kind, length) in enumerate(
            (("emoji", 1), ("emoji", 1), ("emoji", 2), ("symbol", 1), ("symbol", 1))
        )
    ]
    value = t19._strata_receipt(rows, ("a",))
    assert value["eligible_global_indices_by_kind"] == {
        "emoji": [0, 1],
        "symbol": [3, 4],
    }
    assert value["eligible_local_strata_by_kind"] == {
        "emoji": [[0, 1]],
        "symbol": [[0, 1]],
    }


def test_randomization_and_holm_helpers_are_deterministic() -> None:
    identity = np.tile(np.arange(8), (24, 1))
    shifted = np.tile(np.roll(np.arange(8), 1), (24, 1))
    first = t19._randomization_test(
        identity,
        shifted,
        [list(range(8))],
        draws=31,
        seed=19,
    )
    second = t19._randomization_test(
        identity,
        shifted,
        [list(range(8))],
        draws=31,
        seed=19,
    )
    assert first == second
    assert first["observed"] == 1.0
    rows = [
        {"model_role": role, "model_iut_p": p, "practical_pass": practical}
        for role, p, practical in (
            (t19.MODEL_ROLES[0], 0.001, True),
            (t19.MODEL_ROLES[1], 0.02, True),
            (t19.MODEL_ROLES[2], 0.9, True),
        )
    ]
    adjusted = t19._holm(rows, 0.05)
    assert adjusted[0]["holm_reject"] is True
    assert adjusted[1]["holm_reject"] is True
    assert adjusted[2]["holm_reject"] is False


def test_freeze_gate_is_closed_until_manifest_exists() -> None:
    if (ROOT / t19.FREEZE_PATH).exists():
        pytest.skip("Freeze exists after the execution-freeze stage")
    with pytest.raises(FileNotFoundError):
        t19.audit_freeze()
