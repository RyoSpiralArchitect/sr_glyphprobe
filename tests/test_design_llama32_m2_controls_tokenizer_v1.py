from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "design_llama32_m2_controls_tokenizer_v1.py"
CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v1.yaml"
SPEC = importlib.util.spec_from_file_location("design_llama32_m2_controls_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DESIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DESIGN)


class FakeTokenizer:
    values = {
        0: "",
        1: "☁️",
        2: "🟥",
        3: "ab",
        4: "☂",
    }

    def decode(
        self,
        token_ids: list[int],
        *,
        skip_special_tokens: bool,
        clean_up_tokenization_spaces: bool,
    ) -> str:
        assert token_ids[:2] == [11, 22]
        assert skip_special_tokens is False
        assert clean_up_tokenization_spaces is False
        return self.values[token_ids[-1]]

    def encode(self, glyph: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        reverse = {value: key for key, value in self.values.items()}
        return [11, 22, reverse[glyph]]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_config_binds_prior_negative_branch_and_tokenizer_only_inputs() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["status"] == DESIGN.EXPECTED_STATUS
    assert config["prior_negative_branch"]["required_eligible_candidate_count"] == 0
    assert config["selection_contract"]["no_manual_candidate_selection"] is True
    inputs = [
        config["prior_negative_branch"],
        config["source_audit"],
        config["reference_panel"],
        *config["source_panels"],
        config["wrappers"],
    ]
    for row in inputs:
        path = (CONFIG.parent / row["path"]).resolve()
        assert _sha256(path) == row["sha256"]


def test_completion_enumeration_uses_final_token_order_and_fixed_filters() -> None:
    contract = {
        "fixed_prefix_token_ids": [11, 22],
        "final_token_id_start": 0,
        "final_token_id_end_exclusive": 5,
        "minimum_scalar_count": 1,
        "maximum_scalar_count": 8,
        "forbidden_unicode_name_terms": ["RED", "SQUARE"],
    }
    rows, counts = DESIGN._enumerate_completion_candidates(
        FakeTokenizer(), contract, {"☂"}
    )
    assert [row["final_token_id"] for row in rows] == [1]
    assert rows[0]["glyph"] == "☁️"
    assert rows[0]["codepoints"] == ["U+2601", "U+FE0F"]
    assert counts == {
        "total_final_token_ids": 5,
        "decoded_empty": 1,
        "decoded_contains_replacement_character": 0,
        "scalar_count_out_of_range": 0,
        "contains_excluded_glyph": 1,
        "unassigned_unicode_name": 0,
        "unicode_name_term_forbidden": 1,
        "not_exactly_one_grapheme": 1,
        "required_emoji_shape_absent": 0,
        "non_emoji_component_present": 0,
        "reencoded_token_ids_mismatch": 0,
        "eligible": 1,
    }


def test_grapheme_and_component_contract() -> None:
    assert DESIGN._one_grapheme("☁️") is True
    assert DESIGN._one_grapheme("ab") is False
    assert DESIGN._has_required_emoji_shape("☁️") is True
    assert all(DESIGN._is_allowed_emoji_component(char) for char in "☁️")
    assert DESIGN._sequence_slug("☁️") == "u2601_ufe0f"


def test_script_has_no_model_or_target_input_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AutoModel" not in source
    assert "data/targets" not in source
    assert "--target" not in source
    assert "no language-model weights" in source
