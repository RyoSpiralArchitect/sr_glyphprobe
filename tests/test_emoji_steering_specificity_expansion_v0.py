from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emoji_steering_specificity_expansion_v0.py"
SPEC = importlib.util.spec_from_file_location("t14x_expansion", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _synthetic_wrapper_bank(width: int = 32) -> tuple[np.ndarray, np.ndarray]:
    rows = MODULE.population()
    rng = np.random.default_rng(20260831)
    values = np.full((192, 5, 4, 8, width), np.nan, dtype=np.float32)
    mask = np.zeros((192, 5), dtype=bool)
    system_offsets: dict[str, np.ndarray] = {}
    for item_index, item in enumerate(rows):
        system = str(item["glyph_system"])
        system_offsets.setdefault(system, rng.standard_normal(width).astype(np.float32))
        for view in MODULE.t13.available_views(item):
            view_index = MODULE.t13.VIEW_ORDER.index(view)
            mask[item_index, view_index] = True
            item_offset = rng.standard_normal(width).astype(np.float32) * 0.15
            for wrapper in range(4):
                for site in range(8):
                    values[item_index, view_index, wrapper, site] = (
                        system_offsets[system]
                        + item_offset
                        + rng.standard_normal(width).astype(np.float32) * 0.05
                        + np.float32(wrapper * 0.01 + site * 0.005)
                    )
    return values, mask


def test_design_arithmetic_and_holdout_boundary() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "pass"
    assert design["source_items"] == 192
    assert design["public_targets"] == 32
    assert design["model_cells"] == 6
    assert design["item_directions"] == 552
    assert design["system_view_prototypes"] == 28
    assert design["item_rows"] == 70_656
    assert design["prototype_rows"] == 14_336
    assert design["null_rows"] == 8_192
    assert design["zero_rows"] == 64
    assert design["rows_per_model"] == 93_248
    assert design["rows_total"] == 559_488
    assert design["protected_or_future_target_banks_opened"] == 0


def test_leave_one_wrapper_out_excludes_exact_fold() -> None:
    values = np.arange(2 * 1 * 4 * 1 * 3, dtype=np.float32).reshape(2, 1, 4, 1, 3)
    observed = MODULE._leave_one_wrapper_out(values, 2)
    expected = np.mean(values[:, :, [0, 1, 3], :, :], axis=2)
    assert np.array_equal(observed, expected)


def test_prototypes_and_source_covariance_nulls_are_deterministic() -> None:
    wrapper_deltas, mask = _synthetic_wrapper_bank()
    loo = MODULE._leave_one_wrapper_out(wrapper_deltas, 0)
    prototypes = MODULE._prototype_map(loo, mask, 6)
    assert len(prototypes) == 28
    residuals = MODULE._residual_matrix(loo, mask, 6, prototypes)
    assert residuals.shape[0] >= 500
    assert residuals.shape[1] == 32
    seed = MODULE._null_seed(
        "llama32_3b_base_bf16",
        6,
        0,
        "centered_item_residual_gaussian",
        0,
    )
    first = MODULE._null_direction(residuals, "centered_item_residual_gaussian", seed)
    second = MODULE._null_direction(residuals, "centered_item_residual_gaussian", seed)
    rademacher = MODULE._null_direction(
        residuals, "centered_item_residual_rademacher", seed
    )
    assert np.array_equal(first, second)
    assert not np.array_equal(first, rademacher)
    assert np.isclose(MODULE.t13._rms_rows(first[None, :])[0], 1.0)
    assert np.isclose(MODULE.t13._rms_rows(rademacher[None, :])[0], 1.0)


def test_runtime_group_builders_realize_each_frozen_site_count() -> None:
    wrapper_deltas, mask = _synthetic_wrapper_bank()
    directions = np.mean(wrapper_deltas, axis=2)
    target_rms = np.ones((32, 8), dtype=np.float32)
    role = "llama32_3b_base_bf16"
    item = MODULE._item_groups(role, 6, directions, mask, target_rms)
    prototype = MODULE._prototype_groups(role, 6, wrapper_deltas, mask, target_rms)
    null = MODULE._null_groups(role, 6, wrapper_deltas, mask, target_rms)
    zero = MODULE._zero_groups(role, 6)
    assert sum(len(group[2]) for group in item) == 35_328
    assert sum(len(group[2]) for group in prototype) == 7_168
    assert sum(len(group[2]) for group in null) == 4_096
    assert sum(len(group[2]) for group in zero) == 32
    for groups in (item, prototype, null, zero):
        assert all(len(metadata) == len(vectors) for _, _, metadata, vectors in groups)


def test_protocol_keeps_causal_banks_outside_executable_surface() -> None:
    config = MODULE._config()
    assert "any_future_c1_v2_target_bank" in config["forbidden_research_inputs"]
    assert (
        "opening_or_generating_a_replacement_causal_bank_during_T14X"
        in config["forbidden_actions"]
    )
    source = SCRIPT.read_text(encoding="utf-8")
    assert "c1_causal_holdout_targets_v1.jsonl" not in source
    assert "p2_confirmatory_targets_v1.jsonl" not in source
    assert "t13._yield_if_contended" not in source
    assert (
        config["execution_policy"]["yield_receipt_protocol_owner"] == MODULE.PROTOCOL_ID
    )


def test_contention_receipt_is_owned_by_t14x(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(MODULE.t13, "_foreign_gpu_pids", lambda: [12345])
    with pytest.raises(SystemExit) as raised:
        MODULE._yield_if_contended(tmp_path, "llama32_3b_base_bf16", "before_test")
    assert raised.value.code == 75
    receipt = MODULE._read_json(
        tmp_path / "llama32_3b_base_bf16" / "yield_receipt.json"
    )
    assert receipt["protocol_id"] == MODULE.PROTOCOL_ID
    assert receipt["foreign_gpu_pids"] == [12345]


def test_english_and_japanese_protocols_bind_same_counts() -> None:
    english = (ROOT / "docs" / "EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.md").read_text(
        encoding="utf-8"
    )
    japanese = (
        ROOT / "docs" / "EMOJI_STEERING_SPECIFICITY_EXPANSION_V0.ja.md"
    ).read_text(encoding="utf-8")
    for text in (english, japanese):
        assert "559,488" in text
        assert "93,248" in text
        assert "70,656" in text
        assert "14,336" in text
        assert "8,192" in text
        assert "C1 v2" in text
