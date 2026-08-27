from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "design_llama32_m2_controls_tokenizer_v0.py"
CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_design_v0.yaml"
SPEC = importlib.util.spec_from_file_location("design_llama32_m2_controls_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
DESIGN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DESIGN)


class FakeTokenizer:
    def encode(self, glyph: str, *, add_special_tokens: bool) -> list[int]:
        assert add_special_tokens is False
        return [9468, 253, ord(glyph)]

    def decode(
        self,
        token_ids: list[int],
        *,
        skip_special_tokens: bool,
        clean_up_tokenization_spaces: bool,
    ) -> str:
        assert skip_special_tokens is False
        assert clean_up_tokenization_spaces is False
        return chr(token_ids[-1])


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_config_binds_audit_panels_wrappers_and_tokenizer_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["status"] == DESIGN.EXPECTED_STATUS
    assert config["claim_boundary"] == {
        "scientific_result": False,
        "experimental_grid_authorized": False,
        "model_selection_authorized": False,
        "language_model_loaded": False,
        "study_target_banks_accessed": False,
    }
    inputs = [
        config["source_audit"],
        config["reference_panel"],
        *config["source_panels"],
        config["wrappers"],
    ]
    for row in inputs:
        path = (CONFIG.parent / row["path"]).resolve()
        assert _sha256(path) == row["sha256"]


def test_scalar_iteration_is_range_order_then_ascending_and_rejects_overlap() -> None:
    ranges = [
        {"start": "U+2602", "end_inclusive": "U+2603"},
        {"start": "U+2600", "end_inclusive": "U+2601"},
    ]
    assert list(DESIGN._iter_scalars(ranges)) == [0x2602, 0x2603, 0x2600, 0x2601]
    with pytest.raises(DESIGN.DesignError, match="Overlapping"):
        list(
            DESIGN._iter_scalars(
                [
                    {"start": "U+2600", "end_inclusive": "U+2601"},
                    {"start": "U+2601", "end_inclusive": "U+2602"},
                ]
            )
        )


def test_candidate_enumeration_is_deterministic_and_semantically_filtered() -> None:
    contract = {
        "scalar_ranges": [{"start": "U+2600", "end_inclusive": "U+2603"}],
        "required_raw_token_count": 3,
        "required_raw_prefix_token_ids": [9468, 253],
        "allowed_unicode_categories": ["So"],
        "forbidden_unicode_name_terms": ["BLACK"],
    }
    rows, counts = DESIGN._enumerate_candidates(
        FakeTokenizer(), contract, {"☂"}
    )
    assert [row["codepoint"] for row in rows] == ["U+2601", "U+2603"]
    assert [row["candidate_ordinal"] for row in rows] == [1, 2]
    assert counts == {
        "total_scalars": 4,
        "excluded_exact_glyph": 1,
        "unassigned_unicode_name": 0,
        "unicode_category_not_allowed": 0,
        "unicode_name_term_forbidden": 1,
        "raw_decode_not_exact": 0,
        "raw_token_count_mismatch": 0,
        "raw_prefix_mismatch": 0,
        "eligible": 2,
    }


def test_replacement_changes_exactly_one_declared_slot() -> None:
    items = [
        {"panel_id": "p", "id": "x", "glyph": "☀"},
        {"panel_id": "p", "id": "y", "glyph": "☁"},
    ]
    candidate = {"glyph": "☂"}
    output = DESIGN._replace_item(items, "x", candidate)
    assert [row["glyph"] for row in output] == ["☂", "☁"]
    assert items[0]["glyph"] == "☀"
    with pytest.raises(DESIGN.DesignError, match="Expected one replacement"):
        DESIGN._replace_item(items, "missing", candidate)


def test_output_directory_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "suite"
    DESIGN._write_output_directory_no_overwrite(output, {"panel.yaml": b"items: []\n"})
    assert (output / "panel.yaml").read_bytes() == b"items: []\n"
    with pytest.raises(DESIGN.DesignError, match="Refusing to overwrite"):
        DESIGN._write_output_directory_no_overwrite(output, {"panel.yaml": b"changed\n"})


def test_script_has_no_model_or_target_input_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AutoModel" not in source
    assert "data/targets" not in source
    assert "--target" not in source
    assert "no language-model weights" in source
