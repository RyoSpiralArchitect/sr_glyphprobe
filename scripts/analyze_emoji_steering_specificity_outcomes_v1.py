#!/usr/bin/env python3
"""Run the frozen T13-EA F1--F3 analysis under zero-gate amendment v1.

This is intentionally a thin production wrapper.  It reuses the v0 F1--F3
mathematics, compact-output transform, sealed-ledger loaders, and full closeout
auditor without changing them.  The only amendment is the first-open zero
gate: all primitive no-op equalities remain exact, while JS divergence may
carry a bounded float32 round-trip residual of at most eight float32 epsilons.

The original v0 exact-JS gate failure is disclosed in every authorization and
result.  Passing this amended integrity gate authorizes exploratory derivation
only; it is not a confirmatory verdict or scientific result by itself.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import yaml


AMENDMENT_ID = "glyphprobe-emoji-steering-specificity-zero-gate-amendment-v1"
ORIGINAL_ANALYSIS_PATH = Path(
    "scripts/analyze_emoji_steering_specificity_outcomes_v0.py"
)
GEOMETRY_V1_ANALYZER_PATH = Path(
    "scripts/analyze_emoji_steering_specificity_geometry_v1.py"
)
AMENDMENT_AUDIT_PATH = Path(
    "scripts/audit_emoji_steering_specificity_zero_gate_amendment_v1.py"
)
MODEL_CONFIG_PATH = Path("configs/semantic_atlas_cross_model_replication_v0.yaml")
PREFLIGHT_DIRECTORY = Path("validation/emoji_steering_specificity_harvest_v0")
JS_ABS_TOLERANCE = 8.0 * float(np.finfo(np.float32).eps)
ZERO_GATE_STATUS = "primitive_exact_noop_with_bounded_float32_js_roundtrip"
HISTORICAL_V0_ZERO_GATE_STATUS = (
    "failed_closed_on_js_divergence_per_frozen_failure_receipt"
)
V0_CURRENT_PREDICATE_FAIL = "would_fail_nonzero_roundtrip_residual"
V0_CURRENT_PREDICATE_PASS = "would_pass_all_js_exact_zero"


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V0 = _load_module(
    _root() / ORIGINAL_ANALYSIS_PATH,
    "glyphprobe_emoji_steering_specificity_outcomes_v0_for_v1",
)

# Public aliases make the unchanged scientific math and compaction provenance
# explicit.  They also keep synthetic tests independent of any sealed run.
OutcomeAnalysisError = V0.OutcomeAnalysisError
analyze_rows = V0.analyze_rows
compact_production_output = V0.compact_production_output

# Closeout and ledger operations are direct v0 aliases.  Keeping them at module
# scope permits order-only synthetic tests without weakening the production path.
_validate_scientific_open_receipt = V0._validate_scientific_open_receipt
_audit_closeout_same_process = V0._audit_closeout_same_process
_verify_bound_file = V0._verify_bound_file
_read_jsonl = V0._read_jsonl
_load_kind_ledgers = V0._load_kind_ledgers
_acquisition_config = V0._acquisition_config
_sha256 = V0._sha256
_write_json = V0._write_json


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OutcomeAnalysisError(message)


def _load_geometry_v1() -> ModuleType:
    return _load_module(
        _root() / GEOMETRY_V1_ANALYZER_PATH,
        "glyphprobe_emoji_steering_specificity_geometry_v1_for_outcomes_v1",
    )


def _audit_amendment_freeze_same_process() -> dict[str, Any]:
    """Verify the full amendment roster before closeout or value access."""

    module = _load_module(
        _root() / AMENDMENT_AUDIT_PATH,
        "glyphprobe_zero_gate_amendment_v1_audit_for_outcomes_v1",
    )
    auditor = getattr(module, "audit_freeze", None)
    _require(callable(auditor), "Amendment v1 freeze auditor is unavailable")
    result = auditor()
    _require(
        isinstance(result, dict)
        and result.get("status") == "amendment_freeze_audit_pass"
        and result.get("amendment_id") == AMENDMENT_ID
        and result.get("scientific_values_parsed_by_auditor") is False,
        "Amendment v1 freeze audit differs",
    )
    return result


def _model_config() -> dict[str, Any]:
    value = yaml.safe_load((_root() / MODEL_CONFIG_PATH).read_text(encoding="utf-8"))
    _require(isinstance(value, dict), "Model configuration must be a mapping")
    models = value.get("models")
    _require(isinstance(models, dict), "Model configuration is missing models")
    return models


def _validate_preflight_bindings_same_process(
    preflight_directory: Path, roles: list[str]
) -> dict[str, str]:
    """Reuse geometry v1's frozen-receipt binding before any value open."""

    geometry_v1 = _load_geometry_v1()
    result = geometry_v1.V0._validate_preflight_bindings(preflight_directory, roles)
    _require(
        isinstance(result, dict) and list(result) == roles,
        "Frozen preflight role bindings differ",
    )
    return {str(key): str(value) for key, value in result.items()}


def _verify_zero_gate_same_process(
    run_root: Path, run_binding_root: str, preflight_directory: Path
) -> dict[str, Any]:
    """Open only bound pilot-zero values and apply the shared v1 validator."""

    geometry_v1 = _load_geometry_v1()
    verifier = getattr(geometry_v1, "validate_zero_control_v1", None)
    _require(callable(verifier), "Shared v1 zero-control verifier is unavailable")

    config = V0._config()
    pilots = [str(value) for value in config["acquisition_gate"]["pilot_roles"]]
    models = _model_config()
    results: list[dict[str, Any]] = []
    names = (
        "response_ledger.jsonl",
        "top_positive_ids.npy",
        "top_positive_values.npy",
        "top_negative_ids.npy",
        "top_negative_values.npy",
        "countsketch.npy",
    )
    for role in pilots:
        # The full closeout already authenticated this sealed metadata file; the
        # per-file receipt check below prevents any post-closeout substitution.
        _verify_bound_file(run_root / role / "baseline" / "metadata.json", role)
        expectations = geometry_v1.load_zero_gate_expectations(
            run_root, role, preflight_directory
        )
        directory = run_root / role / "pilot" / "zero" / "all-sites"
        for name in names:
            _verify_bound_file(directory / name, role)
        rows = _read_jsonl(directory / "response_ledger.jsonl")
        result = verifier(
            rows,
            top_positive_ids=np.load(
                directory / "top_positive_ids.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            top_positive_values=np.load(
                directory / "top_positive_values.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            top_negative_ids=np.load(
                directory / "top_negative_ids.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            top_negative_values=np.load(
                directory / "top_negative_values.npy",
                mmap_mode="r",
                allow_pickle=False,
            ),
            countsketch=np.load(
                directory / "countsketch.npy", mmap_mode="r", allow_pickle=False
            ),
            vocab_size=int(models[role]["expected_vocab_size"]),
            expected_target_rows=expectations["target_rows"],
            expected_block_indices=expectations["block_indices"],
            expected_depth_fractions=expectations["depth_fractions"],
        )
        _require(
            isinstance(result, dict)
            and result.get("status") == ZERO_GATE_STATUS
            and int(result.get("rows", -1)) == 256,
            f"Amended zero-hook gate failed: {role}",
        )
        _require(
            result.get("historical_v0_exact_js_gate") == HISTORICAL_V0_ZERO_GATE_STATUS,
            f"Historical v0 exact-JS failure is not disclosed: {role}",
        )
        _require(
            result.get("v0_exact_js_predicate_on_current_rows")
            in {V0_CURRENT_PREDICATE_FAIL, V0_CURRENT_PREDICATE_PASS},
            f"Current-row v0 exact-JS diagnostic is missing: {role}",
        )
        residual = result.get("js_residual")
        _require(isinstance(residual, dict), f"JS residual receipt missing: {role}")
        _require(
            float(residual.get("maximum_absolute", float("inf"))) <= JS_ABS_TOLERANCE
            and float(residual.get("tolerance", float("nan"))) == JS_ABS_TOLERANCE,
            f"JS residual receipt exceeds the amendment: {role}",
        )
        results.append({"model": role, **result})

    current_would_fail_roles = [
        str(row["model"])
        for row in results
        if row["v0_exact_js_predicate_on_current_rows"] == V0_CURRENT_PREDICATE_FAIL
    ]
    current_would_pass_roles = [
        str(row["model"])
        for row in results
        if row["v0_exact_js_predicate_on_current_rows"] == V0_CURRENT_PREDICATE_PASS
    ]

    return {
        "status": "all_pilot_zero_controls_amendment_v1_pass",
        "amendment_id": AMENDMENT_ID,
        "run_binding_root_sha256": run_binding_root,
        "models": results,
        "zero_policy": {
            "primitive_noop_equalities": "exact",
            "js_divergence": "absolute_float32_roundtrip_bound",
            "js_absolute_tolerance": JS_ABS_TOLERANCE,
            "js_tolerance_formula": "8 * numpy.finfo(numpy.float32).eps",
        },
        "historical_v0_exact_js_gate": {
            "analysis_id": V0.ANALYSIS_ID,
            "status": HISTORICAL_V0_ZERO_GATE_STATUS,
            "failure_field": "js_divergence",
            "failed_model_roles": "unknown_not_recorded",
            "exact_failed_value": "unknown_not_recorded",
            "authority": "frozen_v0_failure_receipt",
            "failure_disposition": (
                "preserved_negative_procedural_result_with_separate_v1_"
                "numerical_amendment"
            ),
        },
        "v0_exact_js_predicate_on_current_rows": {
            "classification": "counterfactual_diagnostic_not_historical_record",
            "would_fail_model_roles": current_would_fail_roles,
            "would_pass_model_roles": current_would_pass_roles,
        },
        "nonzero_response_values_read_before_gate": False,
    }


def load_authorized_rows(
    run_root: Path,
    scientific_open_receipt: Path,
    preflight_directory: Path = PREFLIGHT_DIRECTORY,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Audit the closeout, pass zero v1, then open nonzero response ledgers."""

    amendment_freeze_audit = _audit_amendment_freeze_same_process()
    root = run_root.expanduser().resolve(strict=True)
    receipt_path = scientific_open_receipt.expanduser().resolve(strict=True)
    resolved_preflight = preflight_directory.expanduser().resolve(strict=True)
    source_config = V0._config()
    all_roles = [
        str(value) for value in source_config["acquisition_gate"]["required_role_order"]
    ]
    preflight_bindings = _validate_preflight_bindings_same_process(
        resolved_preflight, all_roles
    )
    closeout = _validate_scientific_open_receipt(receipt_path, root)
    binding_root = str(closeout["run_binding_root_sha256"])
    closeout_audit = _audit_closeout_same_process(root, receipt_path, binding_root)

    # This is the first scientific-value open.  The function returns only after
    # every pilot's zero controls satisfy the amended gate.
    zero_gate = _verify_zero_gate_same_process(root, binding_root, resolved_preflight)

    acquisition = _acquisition_config()
    roles = [str(value) for value in acquisition["pilot"]["roles"]]
    item_rows: list[dict[str, Any]] = []
    prototype_rows: list[dict[str, Any]] = []
    random_rows: list[dict[str, Any]] = []
    for role in roles:
        item_rows.extend(_load_kind_ledgers(root, role, "item", 12))
        prototype_rows.extend(_load_kind_ledgers(root, role, "prototype", 6))
        random_rows.extend(_load_kind_ledgers(root, role, "random", 8))

    return (
        item_rows,
        prototype_rows,
        random_rows,
        {
            "amendment_id": AMENDMENT_ID,
            "same_process_amendment_freeze_audit": amendment_freeze_audit,
            "preflight_receipt_sha256": preflight_bindings,
            "closeout_sha256": _sha256(receipt_path),
            "same_process_closeout_audit": closeout_audit,
            "zero_hook_gate": zero_gate,
            "value_open_order": [
                "same_process_amendment_freeze_audit",
                "frozen_preflight_receipt_binding",
                "same_process_full_closeout_audit",
                "all_pilot_zero_controls_only",
                "item_response_ledgers",
                "prototype_response_ledgers",
                "random_response_ledgers",
            ],
        },
    )


def _apply_amendment_metadata(
    result: dict[str, Any], authorization: dict[str, Any]
) -> dict[str, Any]:
    """Identify v1 without changing any retained v0 family calculation."""

    original_analysis_id = str(result["analysis_id"])
    _require(
        original_analysis_id == V0.ANALYSIS_ID,
        "The reused F1--F3 result is not from frozen analysis v0",
    )
    result["analysis_id"] = AMENDMENT_ID
    result["status"] = "exploratory_f1_f2_f3_complete_under_zero_gate_amendment_v1"
    result["amendment_v1"] = {
        "amendment_id": AMENDMENT_ID,
        "scope": "first_open_zero_gate_js_float32_roundtrip_only",
        "zero_policy": authorization["zero_hook_gate"]["zero_policy"],
        "historical_v0_exact_js_gate": authorization["zero_hook_gate"][
            "historical_v0_exact_js_gate"
        ],
        "v0_exact_js_predicate_on_current_rows": authorization["zero_hook_gate"][
            "v0_exact_js_predicate_on_current_rows"
        ],
        "no_confirmatory_verdict": True,
    }
    result["original_analysis_v0"] = {
        "analysis_id": original_analysis_id,
        "f1_f2_f3_math": "reused_unchanged",
        "compact_output_transform": "reused_unchanged",
        "historical_exact_js_gate": authorization["zero_hook_gate"][
            "historical_v0_exact_js_gate"
        ],
        "failure_disposition": (
            "preserved_negative_procedural_result_with_separate_v1_numerical_amendment"
        ),
    }
    result["decision_status"] = (
        "exploratory_only_no_primary_no_significance_test_no_confirmatory_verdict"
    )
    result["value_open_authorization"] = authorization
    return result


def analyze_run(
    run_root: Path,
    scientific_open_receipt: Path,
    output: Path,
    *,
    preflight_directory: Path = PREFLIGHT_DIRECTORY,
    bootstrap_replicates: int = 0,
) -> dict[str, Any]:
    resolved_run_root = run_root.expanduser().resolve(strict=True)
    resolved_output = output.expanduser().resolve()
    _require(
        not resolved_output.is_relative_to(resolved_run_root),
        "Analysis output must be outside the sealed run root",
    )
    _require(
        not resolved_output.exists(),
        f"Analysis output already exists: {resolved_output}",
    )
    registered_replicates = int(V0._config()["reporting"]["bootstrap_replicates"])
    _require(
        bootstrap_replicates in {0, registered_replicates},
        "Production execution permits point estimates or the registered bootstrap only",
    )

    item_rows, prototype_rows, random_rows, authorization = load_authorized_rows(
        run_root, scientific_open_receipt, preflight_directory
    )
    result = analyze_rows(
        item_rows,
        prototype_rows,
        random_rows,
        bootstrap_replicates=bootstrap_replicates,
        require_frozen_grid=True,
    )
    result = compact_production_output(result)
    result = _apply_amendment_metadata(result, authorization)
    receipt_path = scientific_open_receipt.expanduser().resolve()
    result["scientific_open_receipt"] = {
        "path": str(receipt_path),
        "sha256": _sha256(receipt_path),
    }
    _write_json(resolved_output, result)
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--run-root", type=Path, required=True)
    result.add_argument("--scientific-open-receipt", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--preflight-directory", type=Path, default=PREFLIGHT_DIRECTORY)
    result.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=0,
        help=(
            "0 writes point estimates with bootstrap explicitly pending; "
            "the only other accepted value is the registered 20000"
        ),
    )
    return result


def main() -> None:
    args = parser().parse_args()
    result = analyze_run(
        args.run_root,
        args.scientific_open_receipt,
        args.output,
        preflight_directory=args.preflight_directory,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(
        json.dumps(
            {
                "analysis_id": result["analysis_id"],
                "original_analysis_id": result["original_analysis_v0"]["analysis_id"],
                "status": result["status"],
                "output": str(args.output.expanduser().resolve()),
                "family_order": result["family_order"],
                "no_confirmatory_verdict": True,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
