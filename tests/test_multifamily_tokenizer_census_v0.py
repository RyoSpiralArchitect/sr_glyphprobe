from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_multifamily_emoji_tokenizers_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_multifamily_emoji_tokenizers_v0", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class CharacterTokenizer:
    is_fast = True
    vocab_size = 0x110000

    def __len__(self) -> int:
        return self.vocab_size

    def __call__(self, text: str, **kwargs: object) -> dict[str, object]:
        assert kwargs["add_special_tokens"] is False
        assert kwargs["return_offsets_mapping"] is True
        return {
            "input_ids": [ord(character) for character in text],
            "offset_mapping": [(index, index + 1) for index in range(len(text))],
        }

    def convert_ids_to_tokens(self, token_ids: list[int]) -> list[str]:
        return [f"U+{token_id:04X}" for token_id in token_ids]

    def decode(self, token_ids: list[int], **kwargs: object) -> str:
        assert kwargs["skip_special_tokens"] is False
        return "".join(chr(token_id) for token_id in token_ids)


@pytest.fixture(scope="module")
def authority() -> AUDIT.StaticAuthority:
    return AUDIT.load_static_authority(
        root=ROOT,
        config_path=ROOT / "configs" / "multifamily_tokenizer_census_v0.yaml",
    )


def test_static_freeze_has_exact_panel_context_and_roster_counts(
    authority: AUDIT.StaticAuthority,
) -> None:
    assert len(authority.items) == 115
    assert len({item["id"] for item in authority.items}) == 115
    assert len({item["glyph"] for item in authority.items}) == 115
    assert [context["id"] for context in authority.contexts] == [
        "raw",
        "leading_space",
        "marker_wrapper",
        "glyph_prompt",
    ]
    assert {
        node: len(entries)
        for node, entries in authority.config["node_rosters"].items()
    } == {"mac1": 5, "mac2": 5, "furnace": 4}


def test_panel_relations_resolve_and_composition_families_are_retained(
    authority: AUDIT.StaticAuthority,
) -> None:
    item_ids = {item["id"] for item in authority.items}
    for item in authority.items:
        if item["base_id"] is not None:
            assert item["base_id"] in item_ids
        assert set(item["component_ids"]).issubset(item_ids)

    by_family: dict[str, int] = {}
    for item in authority.items:
        by_family[item["census_family"]] = by_family.get(item["census_family"], 0) + 1
    assert by_family["colored_shape"] == 10
    assert by_family["modifier"] == 8
    assert by_family["zwj_component"] == 16
    assert by_family["zwj_sequence"] == 8
    assert by_family["regional_flag"] == 4
    assert by_family["variation_selector"] == 7
    assert by_family["keycap"] == 4
    assert by_family["non_glyph_control"] == 8


def test_script_is_tokenizer_only_and_has_no_model_loader() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert "model.forward" not in source
    assert "import torch" not in source
    assert "import mlx" not in source
    assert "p2_confirmatory_targets_v1.jsonl" in source
    assert "c1_causal_holdout_targets_v1.jsonl" in source


def test_character_tokenizer_offsets_cover_only_the_item_span(
    authority: AUDIT.StaticAuthority,
) -> None:
    item = next(item for item in authority.items if item["id"] == "zwj_black_cat")
    context = next(
        context for context in authority.contexts if context["id"] == "leading_space"
    )
    row = AUDIT.tokenize_item(
        tokenizer=CharacterTokenizer(),
        tokenizer_label="fake",
        node="mac2",
        item=item,
        context=context,
    )
    assert row["roundtrip_exact"] is True
    assert row["span_token_count"] == len(item["glyph"])
    assert row["span_token_positions"][0] == 1
    assert row["contains_zwj"] is True


def test_all_pairwise_rows_and_relation_deltas_are_emitted(
    authority: AUDIT.StaticAuthority,
) -> None:
    tokenizer = CharacterTokenizer()
    tokenizations = [
        AUDIT.tokenize_item(
            tokenizer=tokenizer,
            tokenizer_label="fake",
            node="mac2",
            item=item,
            context=context,
        )
        for item in authority.items
        for context in authority.contexts
    ]
    pairwise = AUDIT.build_pairwise_rows(
        authority=authority,
        successful_labels=["fake"],
        tokenizations=tokenizations,
    )
    assert len(pairwise) == 115 * 114 // 2 == 6555
    summary = AUDIT.build_summary(
        authority=authority,
        node="mac2",
        successful_labels=["fake"],
        tokenizer_results=[{"label": "fake", "status": "success"}],
        tokenizations=tokenizations,
        pairwise_rows=pairwise,
    )
    assert summary["pairwise_row_count"] == 6555
    relations = summary["relation_token_count_deltas"]
    assert sum(row["relation"] == "base_delta" for row in relations) == 13
    assert sum(row["relation"] == "component_sum_gap" for row in relations) == 8


def test_roster_arguments_must_match_exactly(authority: AUDIT.StaticAuthority) -> None:
    with pytest.raises(AUDIT.CensusError, match="exactly match"):
        AUDIT.run_census(
            authority=authority,
            node="mac2",
            output=ROOT / "never-created-census-output",
            tokenizer_paths={"mac2_gpt2": ROOT},
        )


def test_manifest_does_not_freeze_protected_target_files(
    authority: AUDIT.StaticAuthority,
) -> None:
    frozen = {record["path"] for record in authority.manifest["frozen_files"]}
    assert "data/targets/p2_confirmatory_targets_v1.jsonl" not in frozen
    assert "data/targets/c1_causal_holdout_targets_v1.jsonl" not in frozen
