from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "design_llama32_m2_controls_tokenizer_v2.py"
CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v2.yaml"
SPEC = importlib.util.spec_from_file_location("design_llama32_m2_controls_v2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DESIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DESIGN)


class FakeTokenizer:
    def encode(self, glyph: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return [9468, 253, ord(glyph)]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_config_binds_both_negative_branches_and_inputs() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["status"] == DESIGN.EXPECTED_STATUS
    assert [row["required_eligible_candidate_count"] for row in config["prior_negative_branches"]] == [0, 0]
    inputs = [
        *config["prior_negative_branches"],
        config["source_audit"],
        config["reference_panel"],
        *config["source_panels"],
        config["wrappers"],
    ]
    for row in inputs:
        path = (CONFIG.parent / row["path"]).resolve()
        assert _sha256(path) == row["sha256"]


def test_allocation_contract_attains_pigeonhole_lower_bound_on_paper() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    inventory = config["inventory_contract"]
    assert inventory["required_dominant_placements"] == 27
    assert inventory["expected_unique_compatible_dominant_glyphs"] == 25
    assert (
        inventory["required_dominant_placements"]
        - inventory["expected_unique_compatible_dominant_glyphs"]
        == inventory["theoretical_minimum_reused_placements"]
        == 2
    )
    replacements = config["allocation_contract"]["replacements"]
    assert [(row["donor_panel_id"], row["recipient_panel_id"]) for row in replacements] == [
        ("m2_null_prefix_9x253_1x242_a", "m2_null_prefix_9x253_1x242_b"),
        ("m2_null_prefix_9x253_1x242_b", "m2_null_prefix_9x253_1x242_c"),
    ]


def test_replace_exact_item_is_non_mutating_and_fail_closed() -> None:
    items = [
        {"panel_id": "b", "id": "bad", "glyph": "🟁"},
        {"panel_id": "b", "id": "keep", "glyph": "🟄"},
    ]
    donor = {"glyph": "🟀"}
    output = DESIGN._replace_exact_item(items, "bad", donor)
    assert [row["glyph"] for row in output] == ["🟀", "🟄"]
    assert items[0]["glyph"] == "🟁"
    with pytest.raises(DESIGN.DesignError, match="Replacement count differs"):
        DESIGN._replace_exact_item(items, "missing", donor)


def test_reused_item_is_explicitly_annotated() -> None:
    reuse = {
        ("b", "🟀"): {
            "donor_panel_id": "a",
            "rule": "lowest_unicode_scalar",
        }
    }
    rows = DESIGN._canonical_panel_items(
        FakeTokenizer(),
        "b",
        "b",
        "out-b",
        [{"panel_id": "out-b", "id": "x", "glyph": "🟀"}],
        reuse,
    )
    factors = rows[0]["factors"]
    assert factors["construction_role"] == "deterministic_minimum_overlap_reuse"
    assert factors["donor_source_panel_id"] == "a"


def test_analysis_contract_forbids_independence_and_confirmatory_claims() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["claim_boundary"]["independent_control_panels_claimed"] is False
    assert config["analysis_constraints"] == {
        "treat_control_panels_as_independent": False,
        "require_overlap_aware_analysis": True,
        "require_disjoint_panel_a_only_sensitivity": True,
        "confirmatory_claim_authorized": False,
    }


def test_script_has_no_model_or_target_input_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AutoModel" not in source
    assert "data/targets" not in source
    assert "--target" not in source
    assert "no language-model" in source
