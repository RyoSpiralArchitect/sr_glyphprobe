from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "audit_emoji_steering_specificity_analysis_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_emoji_steering_specificity_analysis_v0", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


@pytest.fixture
def compact_schema(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Keep the production tree while making synthetic arrays deliberately tiny."""

    schema = copy.deepcopy(MODULE._artifact_expectations())
    for model in schema["model_specs"].values():
        model["width"] = 3
        model["vocab"] = 7
        model["batch_size"] = 4
    schema.update(
        {
            "source_observation_rows": (4,) * 12,
            "item_response_rows": (32,) * 12,
            "prototype_response_rows": {system: 256 for system in schema["systems"]},
            "random_response_rows": 32,
            "zero_response_rows": 256,
            "source_shard_items": 1,
            "population_items": 12,
            "present_item_views": 12,
            "source_forward_sequences": 84,
            "top_k": 2,
            "sketch_dimension": 3,
        }
    )
    schema["pilot_response_rows"] = (
        sum(schema["item_response_rows"])
        + sum(schema["prototype_response_rows"].values())
        + 8 * schema["random_response_rows"]
        + schema["zero_response_rows"]
    )
    monkeypatch.setattr(MODULE, "_artifact_expectations", lambda: schema)
    monkeypatch.setattr(
        MODULE,
        "audit_freeze",
        lambda: {"status": "test_only_frozen_boundary_stub"},
    )
    return schema


def _baseline_metadata(role: str, schema: dict[str, Any]) -> dict[str, Any]:
    acquisition = MODULE._acquisition_config()
    target_binding = acquisition["source_bindings"]["public_targets"]
    targets = MODULE._read_jsonl_metadata(ROOT / target_binding["path"])
    preflight = json.loads(
        (ROOT / MODULE.RUNTIME_PREFLIGHT_DIRECTORY / f"{role}.json").read_text(
            encoding="utf-8"
        )
    )
    fractions = [float(value) for value in acquisition["depth"]["normalized_fractions"]]
    layers = int(schema["model_specs"][role]["layers"])
    return {
        "wrapper_ids": list(
            acquisition["source_bindings"]["source_wrappers"]["selected_ids"]
        ),
        "wrapper_token_counts": [1] * 4,
        "target_ids": [str(row["id"]) for row in targets],
        "target_groups": [str(row["group"]) for row in targets],
        "target_token_counts": [
            int(row["token_count"]) for row in preflight["target_rows"]
        ],
        "block_indices": [
            max(0, int(math.floor(fraction * layers)) - 1) for fraction in fractions
        ],
        "depth_fractions": fractions,
    }


def _seal_from_spec(
    directory: Path, role: str, spec: dict[str, Any], schema: dict[str, Any]
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, file_spec in spec["files"].items():
        path = directory / name
        if file_spec["format"] == "npy":
            np.save(
                path,
                np.zeros(tuple(file_spec["shape"]), dtype=file_spec["dtype"]),
                allow_pickle=False,
            )
        elif file_spec["format"] == "jsonl":
            path.write_text("{}\n" * int(file_spec["rows"]), encoding="utf-8")
        else:
            _write_json(path, _baseline_metadata(role, schema))
    files = {
        name: {
            "bytes": (directory / name).stat().st_size,
            "sha256": _sha256(directory / name),
        }
        for name in spec["files"]
    }
    _write_json(
        directory / "receipt.json",
        {
            "schema_version": MODULE.SCHEMA_VERSION,
            "protocol_id": MODULE.SOURCE_PROTOCOL_ID,
            "status": spec["status"],
            "model_role": role,
            **spec["exact"],
            "elapsed_seconds": 0.0,
            "files": files,
        },
    )


def _summary(role: str, pilot: bool, schema: dict[str, Any]) -> dict[str, Any]:
    model = schema["model_specs"][role]
    acquisition = MODULE._acquisition_config()
    runtime_path = ROOT / MODULE.RUNTIME_PREFLIGHT_AGGREGATE_PATH
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime_hash = _sha256(runtime_path)
    return {
        "schema_version": MODULE.SCHEMA_VERSION,
        "protocol_id": MODULE.SOURCE_PROTOCOL_ID,
        "status": "role_complete",
        "model_role": role,
        "pilot_role": pilot,
        "source_shards": 12,
        "population_items": schema["population_items"],
        "present_item_views": schema["present_item_views"],
        "source_forward_sequences": schema["source_forward_sequences"],
        "intervention_response_rows": schema["pilot_response_rows"] if pilot else 0,
        "generation_calls": 0,
        "model_receipt": {
            "model_role": role,
            "artifact_model_id": model["artifact_model_id"],
            "revision": model["revision"],
            "model_class": model["model_class"],
            "parameter_count": model["parameter_count"],
            "parameter_dtype_tensor_counts": {"torch.bfloat16": 1},
            "artifact": runtime["model_artifacts"][role],
            "torch_version": acquisition["runtime"]["critical_versions"]["torch"],
            "transformers_version": acquisition["runtime"]["critical_versions"][
                "transformers"
            ],
            "gpu": acquisition["runtime"]["hardware_pin"],
            "runtime_preflight_aggregate_sha256": runtime_hash,
            "tokenizer_receipt_sha256": runtime["receipt_sha256"][role],
        },
        "freeze_manifest_sha256": _sha256(ROOT / MODULE.ACQUISITION_FREEZE_PATH),
        "runtime_preflight_aggregate_sha256": runtime_hash,
        "elapsed_seconds_this_process": 1.0,
        "completed_at_utc": "2026-08-30T00:00:00+00:00",
    }


def _complete_role(root: Path, role: str, schema: dict[str, Any]) -> None:
    pilot = role in schema["pilots"]
    for spec in MODULE._receipt_specs(role, pilot, schema):
        _seal_from_spec(root / role / spec["relative_directory"], role, spec, schema)
    _write_json(root / role / "summary.json", _summary(role, pilot, schema))


def _complete_run(root: Path, schema: dict[str, Any]) -> None:
    for role in schema["roles"]:
        _complete_role(root, role, schema)


def _update_binding(directory: Path, name: str) -> None:
    receipt_path = directory / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    path = directory / name
    receipt["files"][name] = {
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }
    _write_json(receipt_path, receipt)


def test_design_fixes_complete_exploratory_family_and_queue_blind() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "design_audit_pass"
    assert len(design["required_roles"]) == 9
    assert len(design["pilot_roles"]) == 3
    assert design["scientific_output_family_ids"] == [
        "F1_item_source_form",
        "F2_prototype_depth_dose",
        "F3_random_null_calibration",
        "F4_target_sensitivity",
        "F5_output_direction",
        "F6_source_geometry",
    ]
    assert design["scientific_outcomes_read"] is False


def test_production_artifact_expectations_are_exact() -> None:
    schema = MODULE._artifact_expectations()
    assert schema["source_observation_rows"] == MODULE.SOURCE_OBSERVATION_ROWS
    assert schema["item_response_rows"] == MODULE.ITEM_RESPONSE_ROWS
    assert schema["prototype_response_rows"] == MODULE.PROTOTYPE_RESPONSE_ROWS
    assert schema["pilot_response_rows"] == 127_744
    assert schema["model_specs"]["qwen25_0p5b_base_bf16"]["width"] == 896
    assert schema["model_specs"]["qwen25_0p5b_base_bf16"]["vocab"] == 151_936
    assert schema["model_specs"]["mistral7b_instruct_v03_bf16"]["width"] == 4096
    assert schema["model_specs"]["mistral7b_instruct_v03_bf16"]["vocab"] == 32_768


def test_inventory_stays_closed_without_full_queue(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    baseline = MODULE._receipt_specs(role, True, compact_schema)[0]
    _seal_from_spec(tmp_path / role / "baseline", role, baseline, compact_schema)
    result = MODULE.inventory(tmp_path)
    assert result["status"] == "queue_in_progress"
    assert result["roles_complete"] == 0
    assert result["scientific_open_authorized"] is False
    assert result["scientific_values_parsed"] is False
    assert result["created_at_utc"].endswith("+00:00")
    assert result["inspection_scope"] == "sealed_paths_counts_sizes_and_npy_headers"
    assert len(result["run_binding_root_sha256"]) == 64
    assert "full_nine_role_queue_not_complete" in result["scientific_open_blockers"]


def test_complete_inventory_requires_independent_hash_pass(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    _complete_run(tmp_path, compact_schema)
    content_blind = MODULE.inventory(tmp_path)
    assert content_blind["status"] == "queue_complete"
    assert content_blind["roles_complete"] == 9
    assert content_blind["scientific_open_authorized"] is False
    assert content_blind["role_inventory"][0]["sealed_receipts"] == 40
    assert content_blind["role_inventory"][3]["sealed_receipts"] == 13
    assert all(
        len(row["role_binding_root_sha256"]) == 64
        for row in content_blind["role_inventory"]
    )
    verified = MODULE.inventory(tmp_path, verify_hashes=True)
    assert verified["scientific_open_authorized"] is True
    assert verified["scientific_open_blockers"] == []
    assert len(verified["canonical_file_bindings"]) > 1000
    assert all(row["hashes_verified"] > 0 for row in verified["role_inventory"])


def test_hash_verification_fails_closed_on_same_size_mutation(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    _complete_run(tmp_path, compact_schema)
    role = compact_schema["roles"][0]
    payload = tmp_path / role / "baseline" / "wrapper_activations.npy"
    value = bytearray(payload.read_bytes())
    value[-1] ^= 1
    payload.write_bytes(value)
    unverified = MODULE.inventory(tmp_path)
    assert unverified["scientific_open_authorized"] is False
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Hash changed"):
        MODULE.inventory(tmp_path, verify_hashes=True)


def test_arbitrary_payload_tree_cannot_open(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    directory = tmp_path / role / "baseline"
    directory.mkdir(parents=True)
    np.save(directory / "payload.npy", np.asarray([[1.0, 2.0]], dtype=np.float32))
    _write_json(
        directory / "receipt.json",
        {
            "schema_version": 1,
            "protocol_id": MODULE.SOURCE_PROTOCOL_ID,
            "status": "baseline_complete",
            "model_role": role,
            "generation_calls": 0,
            "files": {},
        },
    )
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Unexpected artifact"):
        MODULE.inventory(tmp_path, verify_hashes=True)


def test_npy_dtype_and_shape_are_header_gated(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    baseline = MODULE._receipt_specs(role, True, compact_schema)[0]
    directory = tmp_path / role / "baseline"
    _seal_from_spec(directory, role, baseline, compact_schema)
    np.save(directory / "wrapper_activations.npy", np.zeros((1, 2), dtype=np.float64))
    _update_binding(directory, "wrapper_activations.npy")
    with pytest.raises(MODULE.AnalysisBoundaryError, match="NPY dtype changed"):
        MODULE.inventory(tmp_path)


def test_baseline_metadata_identity_is_frozen(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    baseline = MODULE._receipt_specs(role, True, compact_schema)[0]
    directory = tmp_path / role / "baseline"
    _seal_from_spec(directory, role, baseline, compact_schema)
    metadata_path = directory / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["target_ids"][0] = "substituted-target"
    _write_json(metadata_path, metadata)
    _update_binding(directory, "metadata.json")
    with pytest.raises(MODULE.AnalysisBoundaryError, match="target metadata changed"):
        MODULE.inventory(tmp_path)


def test_receipt_schema_rows_and_unexpected_stage_fail_closed(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    zero = next(
        spec
        for spec in MODULE._receipt_specs(role, True, compact_schema)
        if spec["kind"] == "pilot_zero"
    )
    directory = tmp_path / role / zero["relative_directory"]
    _seal_from_spec(directory, role, zero, compact_schema)
    receipt_path = directory / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["response_rows"] += 1
    _write_json(receipt_path, receipt)
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Receipt field changed"):
        MODULE.inventory(tmp_path)

    receipt["response_rows"] -= 1
    _write_json(receipt_path, receipt)
    (tmp_path / role / "pilot" / ".zero.stage-test").mkdir()
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Unexpected directory"):
        MODULE.inventory(tmp_path)


def test_symlinked_artifact_is_rejected(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    baseline = MODULE._receipt_specs(role, True, compact_schema)[0]
    run_root = tmp_path / "run"
    directory = run_root / role / "baseline"
    _seal_from_spec(directory, role, baseline, compact_schema)
    target = directory / "wrapper_activations.npy"
    moved = tmp_path / "moved.npy"
    target.replace(moved)
    target.symlink_to(moved)
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Symlink forbidden"):
        MODULE.inventory(run_root)


def test_summary_fields_are_exact(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    role = compact_schema["roles"][0]
    _complete_role(tmp_path, role, compact_schema)
    summary_path = tmp_path / role / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["schema_version"] = 2
    _write_json(summary_path, summary)
    with pytest.raises(MODULE.AnalysisBoundaryError, match="Summary field changed"):
        MODULE.inventory(tmp_path)


def test_verified_external_closeout_is_stable_and_reauditable(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    run_root = tmp_path / "run"
    run_root.mkdir()
    _complete_run(run_root, compact_schema)
    closeout_path = tmp_path / "verified-closeout.json"
    closeout = MODULE.write_verified_closeout(run_root, closeout_path)
    assert closeout["status"] == "scientific_open_closeout_complete"
    assert closeout["scientific_open_authorized"] is True
    assert closeout["independent_hash_verification"] is True
    assert closeout["scientific_values_parsed"] is False
    assert closeout["analysis_freeze_sha256"] == _sha256(ROOT / MODULE.FREEZE_PATH)
    assert closeout["total_verified_files"] == len(closeout["verified_file_bindings"])
    assert MODULE.write_verified_closeout(run_root, closeout_path) == closeout
    audit = MODULE.audit_verified_closeout(run_root, closeout_path)
    assert audit["status"] == "scientific_open_closeout_audit_pass"
    assert audit["run_binding_root_sha256"] == closeout["run_binding_root_sha256"]


def test_closeout_cannot_be_written_inside_run_root(
    tmp_path: Path, compact_schema: dict[str, Any]
) -> None:
    _complete_run(tmp_path, compact_schema)
    with pytest.raises(
        MODULE.AnalysisBoundaryError, match="outside the sealed run root"
    ):
        MODULE.write_verified_closeout(tmp_path, tmp_path / "closeout.json")


def test_freeze_manifest_is_current() -> None:
    assert MODULE.audit_freeze() == {
        "status": "freeze_audit_pass",
        "analysis_id": MODULE.ANALYSIS_ID,
    }
