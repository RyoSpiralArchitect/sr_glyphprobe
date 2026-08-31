from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emoji_word_incongruence_replication_v0.py"
SPEC = importlib.util.spec_from_file_location("t15b_replication", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_design_arithmetic_and_prospective_boundary() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "design_pass_zero_t15b_model_forwards"
    assert design["model_roles"] == [
        "smollm2_1p7b_base_bf16",
        "mistral7b_instruct_v03_bf16",
    ]
    assert design["t15a_model_role_overlap"] == 0
    assert design["counts"] == {
        "source_prompts": 2_312,
        "source_metric_rows": 4_096,
        "direction_catalog_rows": 1_280,
        "true_conflict_rows": 24_576,
        "cross_axis_null_rows": 172_032,
        "emoji_main_rows": 24_576,
        "word_main_rows": 24_576,
        "zero_rows": 96,
        "rows_per_model": 245_856,
        "rows_total": 491_712,
    }
    assert design["target_audit"]["target_rows"] == 48
    assert design["target_audit"]["axis_lexical_overlap"] == 0
    assert design["model_forwards"] == 0
    assert design["replication_decision_available"] is False
    assert design["semantic_understanding_claim_authorized"] is False
    assert design["causal_claim_authorized"] is False


def test_source_roster_uses_all_nonself_cross_axis_partners() -> None:
    rows = MODULE.source_prompt_records()
    assert len(rows) == 2_312
    assert Counter(row["source_kind"] for row in rows) == {
        "frame": 8,
        "emoji_component": 128,
        "word_component": 128,
        "core_pair": 256,
        "cross_pair": 1_792,
    }
    axes = [row["id"] for row in MODULE.axes()]
    for axis_id in axes:
        partners = {
            row["word_axis_id"]
            for row in rows
            if row["source_kind"] == "cross_pair" and row["axis_id"] == axis_id
        }
        assert partners == set(axes) - {axis_id}


def test_target_bank_is_new_balanced_and_bound() -> None:
    targets = MODULE.targets()
    assert len(targets) == 48
    assert Counter(row["group"] for row in targets) == {
        "narrative": 8,
        "analytical": 8,
        "dialogue": 8,
        "procedural": 8,
        "descriptive": 8,
        "abstract": 8,
    }
    assert len({row["id"] for row in targets}) == 48
    assert len({row["prompt"] for row in targets}) == 48
    assert MODULE._config()["source_bindings"]["untouched_targets"][
        "status_at_design_freeze"
    ] == "never_used_for_any_model_forward"


def test_scoped_profile_does_not_mutate_closed_t15a_module() -> None:
    base = MODULE.base
    protocol = base.PROTOCOL_ID
    config_path = base.CONFIG_PATH
    target_function = base.t13.targets
    before = base.audit_design()
    assert before["counts"]["rows_total"] == 393_472
    MODULE.audit_design()
    after = base.audit_design()
    assert base.PROTOCOL_ID == protocol
    assert base.CONFIG_PATH == config_path
    assert base.t13.targets is target_function
    assert after["counts"]["rows_total"] == 393_472


def test_bilingual_protocols_bind_same_numbers_and_claim_boundary() -> None:
    english = (
        ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.md"
    ).read_text(encoding="utf-8")
    japanese = (
        ROOT / "docs" / "EMOJI_WORD_INCONGRUENCE_REPLICATION_V0.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "2,312" in text
        assert "245,856" in text
        assert "4,096" in text
        assert "491,712" in text
        assert "20,000" in text
        assert "0.025" in text
        assert "T15-C" in text
