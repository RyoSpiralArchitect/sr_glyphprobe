from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_steering_specificity_expansion_v0.py"
SPEC = importlib.util.spec_from_file_location("t14xa_analysis", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _metrics(value: float) -> dict[str, object]:
    return {
        "kl_baseline_to_intervened": value,
        "js_divergence": value,
        "total_variation": value,
        "logit_delta_rms": value,
        "baseline_entropy": 1.0,
        "intervened_entropy": 1.0 + value,
        "argmax_flip": value > 0.5,
    }


def _synthetic_rows() -> tuple[list[dict], list[dict], list[dict]]:
    systems = MODULE.t14x._config()["population"]["system_order"]
    views = (
        "glyph",
        "unicode_name",
        "component_name",
        "codepoint_literal",
        "decomposed_form",
    )
    item_rows = []
    prototype_rows = []
    null_rows = []
    for depth in (0.875, 1.0):
        for target_index in range(32):
            target_id = f"target-{target_index:02d}"
            for system_index, system in enumerate(systems):
                for fold in range(4):
                    for sign in (-1, 1):
                        for view_index, view in enumerate(views):
                            value = (
                                1.0
                                + system_index * 0.01
                                + (0.05 if sign == 1 else 0.0)
                                - view_index * 0.1
                            )
                            prototype_rows.append(
                                {
                                    "model": "synthetic_model",
                                    "depth_fraction": depth,
                                    "target_id": target_id,
                                    "glyph_system": system,
                                    "held_out_wrapper_index": fold,
                                    "sign": sign,
                                    "view": view,
                                    **_metrics(value),
                                }
                            )
                for sign in (-1, 1):
                    for view_index, view in enumerate(
                        ("glyph", "unicode_name", "decomposed_form")
                    ):
                        item_rows.append(
                            {
                                "model": "synthetic_model",
                                "depth_fraction": depth,
                                "target_id": target_id,
                                "glyph_system": system,
                                "item_index": system_index,
                                "sign": sign,
                                "view": view,
                                **_metrics(0.9 - view_index * 0.1),
                            }
                        )
            for family_index, family in enumerate(MODULE.t14x.FAMILIES):
                for fold in range(4):
                    for seed_index in range(8):
                        for sign in (-1, 1):
                            null_rows.append(
                                {
                                    "model": "synthetic_model",
                                    "depth_fraction": depth,
                                    "target_id": target_id,
                                    "null_family": family,
                                    "held_out_wrapper_index": fold,
                                    "seed_index": seed_index,
                                    "sign": sign,
                                    **_metrics(0.2 + family_index * 0.02),
                                }
                            )
    return item_rows, prototype_rows, null_rows


def test_design_freezes_complete_family_before_open() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "pass"
    assert design["model_cells"] == 6
    assert design["depth_cells"] == 2
    assert design["target_rows"] == 32
    assert design["response_rows_expected"] == 559_488
    assert design["complete_families"] == list(MODULE.FAMILIES)
    assert design["bootstrap_replicates"] == 20_000
    assert design["source_run_audited"] is False
    assert design["scientific_response_values_read"] is False


def test_endpoint_transform_and_target_bootstrap() -> None:
    row = _metrics(0.25)
    assert MODULE.endpoint_value(row, "entropy_change") == pytest.approx(0.25)
    assert MODULE.endpoint_value(row, "argmax_flip_rate") == 0.0
    records = [
        {"target_id": f"target-{index:02d}", "value": index / 100}
        for index in range(32)
    ]
    first = MODULE.target_summary(records, replicates=200, seed=9)
    second = MODULE.target_summary(records, replicates=200, seed=9)
    assert first == second
    assert first["target_rows"] == 32
    assert first["bootstrap_replicates"] == 200


def test_all_synthetic_complete_families_are_retained() -> None:
    item_rows, prototype_rows, null_rows = _synthetic_rows()
    result = MODULE.analyze_rows(
        item_rows,
        prototype_rows,
        null_rows,
        replicates=20,
        seed=11,
    )
    assert tuple(result) == MODULE.FAMILIES
    assert all(
        value["status"] == "exploratory_complete_family" for value in result.values()
    )
    assert len(result[MODULE.FAMILIES[0]]["summaries"]) == 12
    assert len(result[MODULE.FAMILIES[1]]["summaries"]) == 72
    assert len(result[MODULE.FAMILIES[4]]["summaries"]) == 6


def test_production_open_order_is_fail_closed_in_source() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    function = source[source.index("def analyze_run(") : source.index("def _print(")]
    assert function.index("audit_freeze()") < function.index("t14x.audit_run(run_root)")
    assert function.index("t14x.audit_run(run_root)") < function.index(
        '_load_rows(run_root, "item")'
    )


def test_bilingual_docs_bind_the_same_analysis_counts() -> None:
    english = (
        ROOT / "docs" / "EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.md"
    ).read_text(encoding="utf-8")
    japanese = (
        ROOT / "docs" / "EMOJI_STEERING_SPECIFICITY_EXPANSION_ANALYSIS_V0.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "559,488" in text
        assert "20,000" in text
        assert "7" in text
        assert "T14-C" in text
