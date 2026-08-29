from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_steering_specificity_geometry_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_emoji_steering_specificity_geometry_v0", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _zero_rows(count: int = 2) -> list[dict]:
    return [
        {
            "response_index": index,
            "condition_kind": "zero_direction",
            "magnitude": 0.0,
            "sign": 0,
            "kl_baseline_to_intervened": 0.0,
            "js_divergence": 0.0,
            "total_variation": 0.0,
            "logit_delta_rms": 0.0,
            "baseline_entropy": 2.5,
            "intervened_entropy": 2.5,
            "baseline_argmax_id": 4,
            "intervened_argmax_id": 4,
            "argmax_flip": False,
        }
        for index in range(count)
    ]


def _zero_arrays(count: int = 2) -> dict[str, np.ndarray]:
    return {
        "top_positive_ids": np.tile(np.arange(4, dtype=np.int32), (count, 1)),
        "top_positive_values": np.zeros((count, 4), dtype=np.float32),
        "top_negative_ids": np.tile(np.arange(4, dtype=np.int32), (count, 1)),
        "top_negative_values": np.zeros((count, 4), dtype=np.float32),
        "countsketch": np.zeros((count, 8), dtype=np.float32),
    }


def test_zero_gate_requires_every_scalar_and_array_exactly_noop() -> None:
    result = MODULE.validate_zero_control(_zero_rows(), **_zero_arrays(), vocab_size=8)
    assert result["status"] == "exact_noop_pass"
    assert result["tied_top_ids_allowed_and_range_checked"] is True

    rows = _zero_rows()
    rows[0]["js_divergence"] = np.nextafter(0.0, 1.0)
    with pytest.raises(MODULE.GeometryAnalysisError, match="js_divergence"):
        MODULE.validate_zero_control(rows, **_zero_arrays(), vocab_size=8)

    arrays = _zero_arrays()
    arrays["countsketch"][1, 2] = np.finfo(np.float32).tiny
    with pytest.raises(MODULE.GeometryAnalysisError, match="array is nonzero"):
        MODULE.validate_zero_control(_zero_rows(), **arrays, vocab_size=8)


def test_zero_gate_receipt_is_reusable_and_bound_to_closeout() -> None:
    receipt = {
        "schema_version": 1,
        "analysis_id": MODULE.ANALYSIS_ID,
        "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": "all_pilot_zero_controls_exact_noop",
        "run_binding_root_sha256": "a" * 64,
        "scientific_open_receipt_sha256": "b" * 64,
        "models": [{"model": "pilot", "status": "exact_noop_pass", "rows": 2}],
        "zero_phase_value_open_trace": [
            "external_scientific_open_receipt_validated",
            "zero:jsonl:synthetic",
            "all_pilot_zero_controls_exact_noop",
        ],
        "scientific_values_opened_before_all_zero": False,
    }
    result = MODULE.validate_zero_gate_receipt(
        receipt,
        expected_run_binding_root_sha256="a" * 64,
        expected_scientific_open_receipt_sha256="b" * 64,
        expected_pilot_roles=["pilot"],
    )
    assert result["status"] == "zero_gate_receipt_audit_pass"
    receipt["zero_phase_value_open_trace"].insert(1, "nonzero:npy:forbidden")
    with pytest.raises(MODULE.GeometryAnalysisError, match="open order"):
        MODULE.validate_zero_gate_receipt(receipt)


def test_value_open_state_machine_forbids_early_nonzero_reads(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    gate = MODULE.ValueOpenGate()
    with pytest.raises(MODULE.GeometryAnalysisError, match="not validated"):
        gate.open_jsonl(path, zero_control=True)
    gate.authorize()
    with pytest.raises(MODULE.GeometryAnalysisError, match="before the zero"):
        gate.open_jsonl(path)
    assert gate.open_jsonl(path, zero_control=True) == [{}]
    gate.complete_zero_gate()
    assert gate.open_jsonl(path) == [{}]
    assert gate.trace[0] == "external_scientific_open_receipt_validated"


def test_scientific_open_validator_requires_exact_external_closeout(
    tmp_path: Path,
) -> None:
    run_root = tmp_path / "sealed"
    run_root.mkdir()
    roles = MODULE._config()["acquisition_gate"]["required_role_order"]
    files = [
        {"relative_path": f"{roles[0]}/summary.json", "bytes": 7, "sha256": "a" * 64}
    ]
    receipt = {
        "schema_version": 1,
        "analysis_id": MODULE.ANALYSIS_ID,
        "source_protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": "scientific_open_closeout_complete",
        "scientific_open_authorized": True,
        "independent_hash_verification": True,
        "scientific_values_parsed": False,
        "run_root": str(run_root.resolve()),
        "run_binding_root_sha256": "b" * 64,
        "roles_complete": 9,
        "roles_required": 9,
        "total_verified_files": 1,
        "total_verified_bytes": 7,
        "role_bindings": [
            {"role": role, "role_binding_root_sha256": f"{index:x}" * 64}
            for index, role in enumerate(roles, 1)
        ],
        "canonical_allowed_relative_paths": [files[0]["relative_path"]],
        "verified_file_bindings": files,
    }
    result = MODULE.validate_scientific_open_receipt(receipt, run_root)
    assert result["external_closeout_root_sha256"] == "b" * 64
    receipt["status"] = "queue_complete"
    with pytest.raises(MODULE.GeometryAnalysisError, match="incomplete"):
        MODULE.validate_scientific_open_receipt(receipt, run_root)


def _response_row(
    *, model: str, target: int, group: str, kind: str, level: float
) -> dict:
    return {
        "model": model,
        "condition_kind": kind,
        "target_index": target,
        "target_id": f"target-{target}",
        "target_group": group,
        "kl_baseline_to_intervened": level,
        "js_divergence": level * 2,
        "total_variation": level * 3,
        "logit_delta_rms": level * 4,
        "baseline_entropy": 2.0,
        "intervened_entropy": 2.0 + level / 10,
        "argmax_flip": target == 2,
    }


def test_f4_uses_baseline_entropy_margin_and_reports_group_heterogeneity() -> None:
    logits = np.asarray(
        [[2.0, 1.0, 0.0], [1.5, 1.0, 0.0], [1.1, 1.0, 0.0]], dtype=np.float32
    )
    features = MODULE.baseline_target_features(
        logits, ["target-0", "target-1", "target-2"], ["a", "a", "b"]
    )
    baseline = [{"model": "m", **row} for row in features]
    rows = [
        _response_row(
            model="m",
            target=index,
            group=("a" if index < 2 else "b"),
            kind="item_source_form",
            level=float(index + 1),
        )
        for index in range(3)
    ]
    result = MODULE.analyze_target_sensitivity(baseline, rows)
    assert result["family_id"] == "F4_target_sensitivity"
    assert result["profile_scope"]["level"] == (
        "coarse_condition_kind_pooled_target_diagnostic"
    )
    assert result["profile_scope"]["not_a_fixed_stratum_effect"] is True
    kl = next(
        row
        for row in result["associations"]
        if row["endpoint"] == "kl_baseline_to_intervened"
    )
    assert kl["target_count"] == 3
    assert kl["baseline_top_two_logit_margin_spearman"] == pytest.approx(-1.0)
    group = next(
        row
        for row in result["target_group_heterogeneity"]
        if row["endpoint"] == "kl_baseline_to_intervened"
    )
    assert group["group_means"] == {"a": 1.5, "b": 3.0}
    assert group["interpretation"] == "sensitivity_diagnostic_not_source_specificity"


def test_f5_sign_pair_is_within_model_and_reports_tail_purity() -> None:
    result = MODULE.output_direction_pair_metrics(
        negative_sketch=np.asarray([-1.0, -2.0, 0.0]),
        positive_sketch=np.asarray([1.0, 2.0, 0.0]),
        negative_positive_ids=np.asarray([7, 8]),
        negative_positive_values=np.asarray([0.2, 0.1]),
        negative_negative_ids=np.asarray([1, 2]),
        negative_negative_values=np.asarray([-0.4, -0.2]),
        positive_positive_ids=np.asarray([1, 2]),
        positive_positive_values=np.asarray([0.4, 0.2]),
        positive_negative_ids=np.asarray([7, 8]),
        positive_negative_values=np.asarray([-0.2, -0.1]),
    )
    assert result["countsketch_cosine"] == pytest.approx(-1.0)
    assert result["sign_reversed_countsketch_cosine"] == pytest.approx(1.0)
    assert result["mean_swapped_top64_overlap"] == 1.0
    assert result["top_tail_sign_purity"] == 1.0
    assert MODULE.cosine_at_comparison(np.zeros(3), np.ones(3)) is None


def test_cross_model_concordance_uses_scalar_target_profiles_only() -> None:
    rows = []
    for model, values in (("a", [1.0, 2.0, 3.0]), ("b", [2.0, 4.0, 6.0])):
        rows.extend(
            {
                "model": model,
                "condition_kind": "prototype",
                "endpoint": "kl_baseline_to_intervened",
                "target_index": index,
                "response_mean": value,
            }
            for index, value in enumerate(values)
        )
    result = MODULE.cross_model_scalar_rank_concordance(rows)
    assert len(result) == 1
    assert result[0] == {
        "left_model": "a",
        "right_model": "b",
        "condition_kind": "prototype",
        "endpoint": "kl_baseline_to_intervened",
        "target_count": 3,
        "spearman": result[0]["spearman"],
        "comparison_space": "scalar_target_profile_only",
    }
    assert result[0]["spearman"] == pytest.approx(1.0)


def _geometry_fixture() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict, dict]:
    rng = np.random.default_rng(812)
    deltas = rng.normal(size=(2, 5, 4, 3, 6)).astype(np.float32)
    mask = np.ones((2, 5), dtype=np.bool_)
    mask[0, 2] = False
    mask[0, 4] = False
    deltas[~mask] = np.nan
    directions = np.mean(deltas, axis=2, dtype=np.float64).astype(np.float32)
    item_systems = {0: "atomic_anchor", 1: "zwj"}
    token_rows = {
        (item, view): {
            "raw_token_count": item + view_index + 1,
            "added_count_signature": f"{item}:{view_index}:1:1",
        }
        for item in range(2)
        for view_index, view in enumerate(MODULE.VIEW_ORDER)
        if mask[item, view_index]
    }
    token_rows[(1, "unicode_name")] = dict(token_rows[(1, "glyph")])
    return directions, deltas, mask, item_systems, token_rows


def test_f6_checks_direction_means_missing_forms_and_token_count_strata() -> None:
    directions, deltas, mask, item_systems, token_rows = _geometry_fixture()
    result = MODULE.source_shard_geometry(
        role="synthetic",
        directions=directions,
        wrapper_deltas=deltas,
        view_mask=mask,
        item_start=0,
        item_systems=item_systems,
        token_rows=token_rows,
    )
    assert result["direction_vectors_integrity_checked"] == int(mask.sum()) * 3
    missing = [row for row in result["availability_rows"] if row["status"] != "present"]
    assert {(row["item_index"], row["source_form"]) for row in missing} == {
        (0, "component_name"),
        (0, "decomposed_form"),
    }
    unavailable = [row for row in result["pair_rows"] if row["status"] != "present"]
    assert len(unavailable) == 2
    summary = MODULE.summarize_source_geometry(
        result["dispersion_rows"],
        result["pair_rows"],
        result["availability_rows"],
        integrity_vectors=result["direction_vectors_integrity_checked"],
    )
    assert summary["family_id"] == "F6_source_geometry"
    assert summary["tokenizer_signature_strata"]
    assert {
        row["token_count_signature_exact_match"]
        for row in summary["tokenizer_signature_match_summaries"]
    } == {False, True}
    assert (
        summary["cross_model_vector_comparison"] == "forbidden_different_hidden_spaces"
    )

    changed = directions.copy()
    changed[1, 0, 0, 0] += np.float32(1e-3)
    with pytest.raises(MODULE.GeometryAnalysisError, match="mean integrity"):
        MODULE.source_shard_geometry(
            role="synthetic",
            directions=changed,
            wrapper_deltas=deltas,
            view_mask=mask,
            item_start=0,
            item_systems=item_systems,
            token_rows=token_rows,
        )
