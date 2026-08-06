from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "build_m2_public_artifact_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_m2_public_bundle_script", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

RUN_ROLES = MODULE.RUN_ROLES
COMPACT_RUN_FILES = MODULE.COMPACT_RUN_FILES
ConfirmatoryFamily = MODULE.ConfirmatoryFamily
build = MODULE.build


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str = "portable\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _config(
    repo: Path,
    relative: str,
    *,
    panel: str,
    source: str,
    targets: str,
    confirmatory: bool = False,
) -> None:
    value = {
        "panel": {"file": f"../data/emoji_panels/{panel}"},
        "source": {"wrappers_file": f"../data/wrappers/{source}"},
        "targets": {"cases_file": f"../data/targets/{targets}"},
        "intervention": {"strengths": [0.05] if confirmatory else [0.025, 0.05, 0.1]},
        "controls": {"sign_flip": not confirmatory},
    }
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=True), encoding="utf-8")


def _make_authority(tmp_path: Path) -> dict[str, Any]:
    repo = tmp_path / "repo"
    panels = {
        "primary": "colored_shapes.yaml",
        "matched_null_a": "m2_matched_null_a.yaml",
        "matched_null_b": "m2_matched_null_b.yaml",
        "matched_null_c": "m2_matched_null_c.yaml",
    }
    for panel in [
        *panels.values(),
        "m2_suffix_matched_middle_shift.yaml",
        "m2_prefix_homogeneous_colored_shapes.yaml",
    ]:
        _write_text(repo / "data" / "emoji_panels" / panel, f"panel_id: {panel}\nitems: []\n")
    for source in ("source_wrappers.jsonl", "milestone2_independent_source_wrappers_v1.jsonl"):
        _write_text(repo / "data" / "wrappers" / source, "{}\n")
    for target in ("prestage_targets.jsonl", "p2_confirmatory_targets_v1.jsonl"):
        _write_text(repo / "data" / "targets" / target, "{}\n")
    parity = repo / "validation" / "mlx_gpt2_parity" / "receipt.json"
    _write_json(parity, {"status": "validated_mlx_selected"})
    _write_text(
        repo / "scripts" / "analyze_m2_confirmatory.py",
        "# frozen confirmatory analyzer\n",
    )
    _write_text(
        repo / "scripts" / "analyze_m2_dependence_sensitivity_v1.py",
        "# post-hoc dependence analyzer\n",
    )

    _config(
        repo,
        "configs/v1_mlx_standard.yaml",
        panel=panels["primary"],
        source="source_wrappers.jsonl",
        targets="prestage_targets.jsonl",
    )
    exploratory_configs = {
        "matched_null_a": "configs/m2_matched_null_a_mlx.yaml",
        "matched_null_b": "configs/m2_matched_null_b_mlx.yaml",
        "matched_null_c": "configs/m2_matched_null_c_mlx.yaml",
    }
    for role, relative in exploratory_configs.items():
        _config(
            repo,
            relative,
            panel=panels[role],
            source="source_wrappers.jsonl",
            targets="prestage_targets.jsonl",
        )
    diagnostic_configs = {
        "suffix_matched_middle_shift": "configs/m2_suffix_matched_middle_shift_mlx.yaml",
        "prefix_homogeneous_colored_shapes": (
            "configs/m2_prefix_homogeneous_colored_shapes_mlx.yaml"
        ),
    }
    for diagnostic, relative in diagnostic_configs.items():
        _config(
            repo,
            relative,
            panel=f"m2_{diagnostic}.yaml",
            source="source_wrappers.jsonl",
            targets="prestage_targets.jsonl",
        )

    p2_rows: list[dict[str, Any]] = []
    p2_configs: dict[tuple[str, str], str] = {}
    for family, source, suffix in (
        ("p2", "source_wrappers.jsonl", ""),
        (
            "independent_source",
            "milestone2_independent_source_wrappers_v1.jsonl",
            "_independent_source",
        ),
    ):
        for role in RUN_ROLES:
            stem = "primary" if role == "primary" else role
            relative = f"configs/m2_p2_{stem}{suffix}_mlx.yaml"
            arm = role if family == "p2" else f"{role}_independent_source"
            _config(
                repo,
                relative,
                panel=panels[role],
                source=source,
                targets="p2_confirmatory_targets_v1.jsonl",
                confirmatory=True,
            )
            p2_configs[(family, role)] = relative
            p2_rows.append(
                {
                    "arm": arm,
                    "path": relative,
                    "panel": f"../data/emoji_panels/{panels[role]}",
                    "source": f"../data/wrappers/{source}",
                    "targets": "../data/targets/p2_confirmatory_targets_v1.jsonl",
                }
            )

    frozen_paths = [
        *(repo / relative for relative in exploratory_configs.values()),
        *(repo / relative for relative in diagnostic_configs.values()),
        *(repo / relative for relative in p2_configs.values()),
        *(repo / "data" / "emoji_panels" / name for name in [
            *panels.values(),
            "m2_suffix_matched_middle_shift.yaml",
            "m2_prefix_homogeneous_colored_shapes.yaml",
        ]),
        repo / "data" / "wrappers" / "source_wrappers.jsonl",
        repo / "data" / "wrappers" / "milestone2_independent_source_wrappers_v1.jsonl",
        repo / "data" / "targets" / "prestage_targets.jsonl",
        repo / "data" / "targets" / "p2_confirmatory_targets_v1.jsonl",
        repo / "scripts" / "analyze_m2_confirmatory.py",
        parity,
    ]
    manifest = repo / "data" / "manifests" / "milestone2_preregistration_v1.json"
    _write_json(
        manifest,
        {
            "manifest_id": "milestone2_preregistration_v1",
            "protocol_id": MODULE.PROTOCOL_ID,
            "files": [
                {
                    "path": path.relative_to(repo).as_posix(),
                    "sha256": _sha256(path),
                }
                for path in frozen_paths
            ],
        },
    )
    audit = repo / "data" / "manifests" / "milestone2_preregistration_audit_v1.json"
    _write_json(
        audit,
        {
            "status": "pass",
            "protocol_id": MODULE.PROTOCOL_ID,
            "manifest_sha256": _sha256(manifest),
            "mlx_validation_receipt_sha256": _sha256(parity),
            "p2_configs": p2_rows,
        },
    )
    return {
        "repo": repo,
        "parity": parity,
        "manifest": manifest,
        "audit": audit,
        "panels": panels,
        "exploratory_configs": {
            "primary": "configs/v1_mlx_standard.yaml",
            **exploratory_configs,
        },
        "diagnostic_configs": diagnostic_configs,
        "p2_configs": p2_configs,
    }


def _input_hashes(repo: Path, config_relative: str, parity: Path) -> dict[str, str]:
    config_path = repo / config_relative
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    references = (
        ("input_00", config_path),
        ("input_01", parity),
        ("input_02", config_path.parent / config["panel"]["file"]),
        ("input_03", config_path.parent / config["source"]["wrappers_file"]),
        ("input_04", config_path.parent / config["targets"]["cases_file"]),
    )
    return {f"{position}:{path.name}": _sha256(path.resolve()) for position, path in references}


def _make_run(
    tmp_path: Path,
    authority: dict[str, Any],
    *,
    label: str,
    config_relative: str,
) -> Path:
    run_id = f"{label}--0123456789abcdef"
    run_dir = tmp_path / "runs" / run_id
    run_dir.mkdir(parents=True)
    config_path = authority["repo"] / config_relative
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    parity_sha = _sha256(authority["parity"])
    input_hashes = _input_hashes(authority["repo"], config_relative, authority["parity"])
    _write_json(
        run_dir / "receipt.json",
        {
            "status": "complete",
            "finished_at": "2026-08-06T00:00:00Z",
            "run_id": run_id,
            "run_seal": "0123456789abcdef",
            "claim_boundary": MODULE.CLAIM_BOUNDARY,
            "config_path": Path(config_relative).name,
            "backend": {"validation_receipt_sha256": parity_sha},
            "input_hashes": input_hashes,
            "model_receipt": {
                "parity_validation": {
                    "validated": True,
                    "receipt_sha256": parity_sha,
                }
            },
        },
    )
    _write_json(
        run_dir / "summary.json",
        {
            "causal_claim_authorized": False,
            "error_count": 0,
            "intervention_record_count": 2,
        },
    )
    (run_dir / "resolved_config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=True), encoding="utf-8"
    )
    for name in COMPACT_RUN_FILES:
        path = run_dir / name
        if path.exists():
            continue
        if name == "dose_response_summary.jsonl" and len(config["intervention"]["strengths"]) < 3:
            continue
        if name == "sign_flip_summary.jsonl" and config["controls"]["sign_flip"] is False:
            continue
        if path.suffix == ".json":
            _write_json(path, {})
        elif path.suffix == ".jsonl":
            _write_text(path, "{}\n")
        elif path.suffix in {".yaml", ".yml"}:
            _write_text(path, "{}\n")
        else:
            _write_text(path, "Portable report.\n")
    _write_text(run_dir / "interventions.jsonl", "{}\n{}\n")
    for name in ("directions.npz", "source_activations.npz", "target_baselines.npz"):
        (run_dir / name).write_bytes(b"synthetic-npz")
    return run_dir


def _make_exploratory_analysis(
    tmp_path: Path, runs: dict[str, Path]
) -> Path:
    analysis = tmp_path / "exploratory-analysis"
    directory_names = {
        "primary": "baseline",
        "matched_null_a": "matched-null-a",
        "matched_null_b": "matched-null-b",
        "matched_null_c": "matched-null-c",
    }
    folded: dict[int, dict[str, Path]] = {dimension: {} for dimension in (48, 32, 24)}
    for role, directory in directory_names.items():
        outputs = []
        for dimension in (48, 32, 24):
            summary = analysis / directory / f"fingerprint_summary.folded-{dimension}.jsonl"
            _write_text(summary, "{}\n" * MODULE.FINGERPRINT_CELL_COUNT)
            folded[dimension][role] = summary
            outputs.append(
                {
                    "target_dim": dimension,
                    "summary_file": summary.name,
                    "summary_sha256": _sha256(summary),
                    "cell_count": MODULE.FINGERPRINT_CELL_COUNT,
                }
            )
        _write_json(
            analysis / directory / "countsketch_sensitivity.json",
            {
                "analysis": "same-seed-divisor-countsketch-fold",
                "input": {
                    "run_label": runs[role].name,
                    "rows_file": "interventions.jsonl",
                    "rows_sha256": _sha256(runs[role] / "interventions.jsonl"),
                },
                "source_dim": MODULE.FINGERPRINT_SOURCE_DIM,
                "source_seed": MODULE.FINGERPRINT_SEED,
                "target_seed": MODULE.FINGERPRINT_SEED,
                "outputs": outputs,
            },
        )
    for dimension in (96, 48, 32, 24):
        sources = []
        for role in RUN_ROLES:
            source = (
                runs[role] / "fingerprint_summary.jsonl"
                if dimension == 96
                else folded[dimension][role]
            )
            run_label = runs[role].name if dimension == 96 else directory_names[role]
            sources.append({"run_label": run_label, "sha256": _sha256(source)})
        _write_json(
            analysis / f"matched_panel_comparison_dim{dimension}.json",
            {
                "analysis": "paired-cell-matched-panel-comparison",
                "sources": {"primary": sources[0], "matched_nulls": sources[1:]},
            },
        )
    return analysis


def _make_diagnostic_analysis(
    tmp_path: Path,
    exploratory_analysis: Path,
    standard_run: Path,
    diagnostic_runs: dict[str, Path],
) -> Path:
    analysis = tmp_path / "diagnostic-analysis"
    specifications = {
        "suffix": {
            "role": "suffix_matched_middle_shift",
            "stem": "suffix_vs_standard",
        },
        "prefix": {
            "role": "prefix_homogeneous_colored_shapes",
            "stem": "prefix_homogeneous_vs_standard",
        },
    }
    for directory, spec in specifications.items():
        run = diagnostic_runs[str(spec["role"])]
        outputs = []
        folded: dict[int, Path] = {}
        for dimension in MODULE.EXPLORATORY_FOLD_DIMS:
            summary = analysis / directory / f"fingerprint_summary.folded-{dimension}.jsonl"
            _write_text(summary, "{}\n" * MODULE.FINGERPRINT_CELL_COUNT)
            folded[dimension] = summary
            outputs.append(
                {
                    "target_dim": dimension,
                    "summary_file": summary.name,
                    "summary_sha256": _sha256(summary),
                    "cell_count": MODULE.FINGERPRINT_CELL_COUNT,
                }
            )
        _write_json(
            analysis / directory / "countsketch_sensitivity.json",
            {
                "analysis": "same-seed-divisor-countsketch-fold",
                "input": {
                    "run_label": run.name,
                    "rows_file": "interventions.jsonl",
                    "rows_sha256": _sha256(run / "interventions.jsonl"),
                },
                "source_dim": MODULE.FINGERPRINT_SOURCE_DIM,
                "source_seed": MODULE.FINGERPRINT_SEED,
                "target_seed": MODULE.FINGERPRINT_SEED,
                "outputs": outputs,
            },
        )
        for dimension in MODULE.EXPLORATORY_ANALYSIS_DIMS:
            if dimension == MODULE.FINGERPRINT_SOURCE_DIM:
                primary = {
                    "run_label": standard_run.name,
                    "summary_file": "fingerprint_summary.jsonl",
                    "sha256": _sha256(standard_run / "fingerprint_summary.jsonl"),
                }
                diagnostic = {
                    "run_label": run.name,
                    "summary_file": "fingerprint_summary.jsonl",
                    "sha256": _sha256(run / "fingerprint_summary.jsonl"),
                }
            else:
                summary_file = f"fingerprint_summary.folded-{dimension}.jsonl"
                standard_fold = (
                    exploratory_analysis / "baseline" / summary_file
                )
                primary = {
                    "run_label": "baseline",
                    "summary_file": summary_file,
                    "sha256": _sha256(standard_fold),
                }
                diagnostic = {
                    "run_label": directory,
                    "summary_file": summary_file,
                    "sha256": _sha256(folded[dimension]),
                }
            _write_json(
                analysis / f"{spec['stem']}_dim{dimension}.json",
                {
                    "analysis": "paired-cell-matched-panel-comparison",
                    "cells": [{} for _ in range(MODULE.FINGERPRINT_CELL_COUNT)],
                    "descriptive_summary": {
                        "cell_count": MODULE.FINGERPRINT_CELL_COUNT
                    },
                    "sources": {
                        "primary": primary,
                        "matched_nulls": [diagnostic],
                    },
                },
            )
    return analysis


def _make_confirmatory_analysis(tmp_path: Path, name: str, runs: dict[str, Path]) -> Path:
    analysis = tmp_path / f"{name}-analysis"
    effects = analysis / "m2_target_effects.jsonl"
    report = analysis / "m2_confirmatory_report.md"
    _write_text(effects, "{}\n")
    _write_text(report, "# Portable confirmatory report\n")
    inputs = []
    for role, panel_role in zip(
        RUN_ROLES,
        ("primary_colored_shapes", "matched_null_a", "matched_null_b", "matched_null_c"),
    ):
        run = runs[role]
        inputs.append(
            {
                "panel_role": panel_role,
                "run_label": run.name,
                "interventions_sha256": _sha256(run / "interventions.jsonl"),
                "resolved_config_sha256": _sha256(run / "resolved_config.yaml"),
                "run_receipt_sha256": _sha256(run / "receipt.json"),
                "resolved_inputs_sha256": _sha256(run / "resolved_inputs.json"),
            }
        )
    _write_json(
        analysis / "m2_confirmatory_receipt.json",
        {
            "protocol_id": MODULE.PROTOCOL_ID,
            "protocol_conformant": True,
            "inputs": inputs,
            "outputs": {
                "target_effects": {
                    "file": effects.name,
                    "sha256": _sha256(effects),
                    "row_count": 1,
                },
                "report": {"file": report.name, "sha256": _sha256(report)},
            },
        },
    )
    return analysis


def _make_dependence_sensitivity(
    tmp_path: Path,
    name: str,
    runs: dict[str, Path],
    repo: Path,
) -> Path:
    analysis = tmp_path / f"{name}-dependence"
    bootstrap = analysis / "m2_dependence_sensitivity_bootstrap.jsonl"
    report = analysis / "m2_dependence_sensitivity_report.md"
    _write_text(
        bootstrap,
        "".join(
            json.dumps({"replicate_index": index}) + "\n"
            for index in range(MODULE.DEPENDENCE_BOOTSTRAP_ROWS)
        ),
    )
    _write_text(report, "# Post-hoc dependence sensitivity\n")
    inputs = []
    for role, panel_role in zip(
        RUN_ROLES,
        ("primary_colored_shapes", "matched_null_a", "matched_null_b", "matched_null_c"),
    ):
        run = runs[role]
        inputs.append(
            {
                "panel_role": panel_role,
                "run_label": run.name,
                "interventions_sha256": _sha256(run / "interventions.jsonl"),
                "resolved_config_sha256": _sha256(run / "resolved_config.yaml"),
                "run_receipt_sha256": _sha256(run / "receipt.json"),
                "resolved_inputs_sha256": _sha256(run / "resolved_inputs.json"),
            }
        )
    _write_json(
        analysis / "m2_dependence_sensitivity_receipt.json",
        {
            "analysis_id": MODULE.DEPENDENCE_ANALYSIS_ID,
            "post_hoc": True,
            "protocol_conformant": False,
            "overwrites_frozen_v1_status": False,
            "inputs": inputs,
            "parameters": {
                "bootstrap_replicates": MODULE.DEPENDENCE_BOOTSTRAP_ROWS,
            },
            "validation": {
                "analyzer_file": MODULE.DEPENDENCE_ANALYZER_FILE,
                "analyzer_sha256": _sha256(
                    repo / "scripts" / MODULE.DEPENDENCE_ANALYZER_FILE
                ),
                "frozen_v1_analyzer_dependency_file": (
                    MODULE.FROZEN_CONFIRMATORY_ANALYZER_FILE
                ),
                "frozen_v1_analyzer_dependency_sha256": _sha256(
                    repo / "scripts" / MODULE.FROZEN_CONFIRMATORY_ANALYZER_FILE
                ),
                "strict_frozen_p2_evidence_validation": True,
                "model_forward_passes": 0,
                "c1_holdout_accessed": False,
            },
            "results": [
                {"layer": layer, "confirmatory_status_assigned": False}
                for layer in (2, 4)
            ],
            "inference_boundary": {
                "p_values_computed": False,
                "multiplicity_adjustment_computed": False,
                "confirmatory_status_computed": False,
                "practical_equivalence_status_computed": False,
            },
            "outputs": {
                "bootstrap_layer_means": {
                    "file": bootstrap.name,
                    "sha256": _sha256(bootstrap),
                    "row_count": MODULE.DEPENDENCE_BOOTSTRAP_ROWS,
                },
                "report": {"file": report.name, "sha256": _sha256(report)},
            },
        },
    )
    return analysis


def _base_inputs(tmp_path: Path) -> dict[str, Any]:
    authority = _make_authority(tmp_path)
    MODULE.PINNED_PARITY_RECEIPT_SHA256 = _sha256(authority["parity"])
    MODULE.PINNED_PREREGISTRATION_MANIFEST_SHA256 = _sha256(authority["manifest"])
    MODULE.PINNED_PREREGISTRATION_AUDIT_SHA256 = _sha256(authority["audit"])
    exploratory_runs = {
        role: _make_run(
            tmp_path,
            authority,
            label=f"exploratory-{role}",
            config_relative=authority["exploratory_configs"][role],
        )
        for role in RUN_ROLES
    }
    return {
        "authority": authority,
        "exploratory_runs": exploratory_runs,
        "exploratory_analysis_dir": _make_exploratory_analysis(tmp_path, exploratory_runs),
        "parity_receipt": authority["parity"],
        "preregistration_manifest": authority["manifest"],
        "preregistration_audit": authority["audit"],
        "output_dir": tmp_path / "public" / "milestone2",
        "manifest_path": tmp_path / "public" / "MILESTONE2_MANIFEST.json",
    }


def _build_kwargs(inputs: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in inputs.items() if key != "authority"}


def _add_confirmatory_family(
    inputs: dict[str, Any], tmp_path: Path, family_name: str
) -> tuple[dict[str, Path], Path]:
    authority = inputs["authority"]
    runs = {
        role: _make_run(
            tmp_path,
            authority,
            label=f"{family_name}-{role}",
            config_relative=authority["p2_configs"][(family_name, role)],
        )
        for role in RUN_ROLES
    }
    inputs.setdefault("confirmatory_families", {})[family_name] = ConfirmatoryFamily(
        runs=runs,
        analysis_dir=_make_confirmatory_analysis(tmp_path, family_name, runs),
    )
    sensitivity = _make_dependence_sensitivity(
        tmp_path,
        family_name,
        runs,
        authority["repo"],
    )
    inputs.setdefault("dependence_sensitivity_dirs", {})[family_name] = sensitivity
    return runs, sensitivity


def _add_diagnostics(
    inputs: dict[str, Any], tmp_path: Path, *, include_analysis: bool = True
) -> dict[str, Path]:
    authority = inputs["authority"]
    runs = {
        role: _make_run(
            tmp_path,
            authority,
            label=f"diagnostic-{role}",
            config_relative=authority["diagnostic_configs"][role],
        )
        for role in MODULE.DIAGNOSTIC_IDS
    }
    inputs["diagnostic_runs"] = runs
    if include_analysis:
        inputs["diagnostic_analysis_dir"] = _make_diagnostic_analysis(
            tmp_path,
            inputs["exploratory_analysis_dir"],
            inputs["exploratory_runs"]["primary"],
            runs,
        )
    return runs


def test_m2_bundle_builds_exploratory_surface_and_records_unexecuted_work(
    tmp_path: Path,
) -> None:
    inputs = _base_inputs(tmp_path)
    manifest = build(**_build_kwargs(inputs))
    assert manifest["input_binding_audit"]["status"] == "pass"
    assert manifest["input_binding_audit"]["run_count"] == 4
    assert manifest["families"]["p2"]["status"] == "unexecuted"
    assert manifest["families"]["independent_source"]["status"] == "unexecuted"
    assert all(row["status"] == "unexecuted" for row in manifest["diagnostics"].values())
    assert len(manifest["omitted_large_local_files"]) == 16
    assert (inputs["output_dir"] / "input_binding_audit.json").is_file()
    binding = json.loads((inputs["output_dir"] / "input_binding_audit.json").read_text())
    assert binding["checks"]["exact_input_hashes"] is True
    assert all(row["exact_input_00_through_04_match"] for row in binding["runs"])


def test_m2_bundle_rejects_incomplete_or_error_run_before_copy(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    receipt_path = inputs["exploratory_runs"]["matched_null_a"] / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["status"] = "running"
    _write_json(receipt_path, receipt)
    with pytest.raises(ValueError, match="status must be complete"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()
    assert not inputs["manifest_path"].exists()


def test_m2_bundle_rejects_any_errors_ledger_before_copy(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _write_text(inputs["exploratory_runs"]["matched_null_b"] / "errors.jsonl", "{}\n")
    with pytest.raises(ValueError, match="errors.jsonl"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()


def test_m2_bundle_rejects_swapped_p2_input_hash_before_copy(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    authority = inputs["authority"]
    runs = {
        role: _make_run(
            tmp_path,
            authority,
            label=f"p2-{role}",
            config_relative=authority["p2_configs"][("p2", role)],
        )
        for role in RUN_ROLES
    }
    receipt_path = runs["primary"] / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    panel_key = next(key for key in receipt["input_hashes"] if key.startswith("input_02:"))
    receipt["input_hashes"][panel_key] = _sha256(
        authority["repo"] / "data/emoji_panels/m2_matched_null_a.yaml"
    )
    _write_json(receipt_path, receipt)
    inputs["confirmatory_families"] = {
        "p2": ConfirmatoryFamily(
            runs=runs,
            analysis_dir=_make_confirmatory_analysis(tmp_path, "p2", runs),
        )
    }
    with pytest.raises(ValueError, match="input_00..04 paths/hashes"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()


def test_m2_bundle_supports_both_complete_confirmatory_families(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    for family_name in ("p2", "independent_source"):
        _add_confirmatory_family(inputs, tmp_path, family_name)
    manifest = build(**_build_kwargs(inputs))
    assert manifest["families"]["p2"]["status"] == "complete"
    assert manifest["families"]["independent_source"]["status"] == "complete"
    assert manifest["input_binding_audit"]["run_count"] == 12
    assert len(manifest["omitted_large_local_files"]) == 50
    for family_name in ("p2", "independent_source"):
        primary = manifest["families"][family_name]["runs"]["primary"]
        assert primary["compact_file_count"] == 15
        assert set(primary["not_produced_compact_files"]) == {
            "dose_response_summary.jsonl",
            "sign_flip_summary.jsonl",
        }
        posthoc = manifest["posthoc_dependence"][family_name]
        assert posthoc["status"] == "complete"
        assert posthoc["post_hoc"] is True
        assert posthoc["omitted_bootstrap"]["row_count"] == 20_000
        public_analysis = (
            inputs["output_dir"] / "analyses" / "posthoc_dependence" / family_name
        )
        assert (public_analysis / "m2_dependence_sensitivity_receipt.json").is_file()
        assert (public_analysis / "m2_dependence_sensitivity_report.md").is_file()
        assert not (public_analysis / "m2_dependence_sensitivity_bootstrap.jsonl").exists()


def test_m2_bundle_rejects_dependence_receipt_for_wrong_ledger(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _, sensitivity = _add_confirmatory_family(inputs, tmp_path, "p2")
    receipt_path = sensitivity / "m2_dependence_sensitivity_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["inputs"][0]["interventions_sha256"] = "0" * 64
    _write_json(receipt_path, receipt)
    with pytest.raises(ValueError, match="interventions_sha256 mismatch"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("post_hoc", False, "post_hoc true"),
        ("protocol_conformant", True, "protocol_conformant false"),
        ("overwrites_frozen_v1_status", True, "must not overwrite"),
    ],
)
def test_m2_bundle_rejects_invalid_dependence_claim_boundaries(
    tmp_path: Path, field: str, value: bool, message: str
) -> None:
    inputs = _base_inputs(tmp_path)
    _, sensitivity = _add_confirmatory_family(inputs, tmp_path, "p2")
    receipt_path = sensitivity / "m2_dependence_sensitivity_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt[field] = value
    _write_json(receipt_path, receipt)
    with pytest.raises(ValueError, match=message):
        build(**_build_kwargs(inputs))


def test_m2_bundle_rejects_dependence_status_or_p_value(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _, sensitivity = _add_confirmatory_family(inputs, tmp_path, "p2")
    receipt_path = sensitivity / "m2_dependence_sensitivity_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["results"][0]["status"] = "robust"
    _write_json(receipt_path, receipt)
    with pytest.raises(ValueError, match="assign no p-value or status"):
        build(**_build_kwargs(inputs))


def test_m2_bundle_rejects_dependence_bootstrap_without_20000_rows(
    tmp_path: Path,
) -> None:
    inputs = _base_inputs(tmp_path)
    _, sensitivity = _add_confirmatory_family(inputs, tmp_path, "p2")
    bootstrap = sensitivity / "m2_dependence_sensitivity_bootstrap.jsonl"
    rows = bootstrap.read_text(encoding="utf-8").splitlines()
    _write_text(bootstrap, "\n".join(rows[:-1]) + "\n")
    with pytest.raises(ValueError, match="exactly 20,000 rows"):
        build(**_build_kwargs(inputs))


def test_m2_bundle_copies_exact_diagnostic_analysis_surface(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _add_diagnostics(inputs, tmp_path)
    manifest = build(**_build_kwargs(inputs))
    assert manifest["diagnostic_analysis"] == {
        "status": "complete",
        "file_count": 16,
        "source_dimension": 96,
        "folded_dimensions": [48, 32, 24],
        "fingerprint_seed": 8_675_309,
        "cell_count_per_comparison": 36,
        "run_roles": list(MODULE.DIAGNOSTIC_IDS),
    }
    public = inputs["output_dir"] / "analyses" / "diagnostics"
    expected = {
        path.as_posix() for path in MODULE._expected_diagnostic_analysis_files()
    }
    observed = {
        path.relative_to(public).as_posix()
        for path in public.rglob("*")
        if path.is_file()
    }
    assert observed == expected


def test_m2_bundle_requires_analysis_dir_for_diagnostic_runs(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _add_diagnostics(inputs, tmp_path, include_analysis=False)
    with pytest.raises(ValueError, match="diagnostic-analysis-dir is required"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()


def test_m2_bundle_rejects_diagnostic_fold_seed_mismatch(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _add_diagnostics(inputs, tmp_path)
    receipt_path = (
        inputs["diagnostic_analysis_dir"] / "suffix" / "countsketch_sensitivity.json"
    )
    receipt = json.loads(receipt_path.read_text())
    receipt["target_seed"] = MODULE.FINGERPRINT_SEED + 1
    _write_json(receipt_path, receipt)
    with pytest.raises(ValueError, match="dimension/seed mismatch"):
        build(**_build_kwargs(inputs))


def test_m2_bundle_rejects_diagnostic_comparison_source_hash(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    _add_diagnostics(inputs, tmp_path)
    comparison_path = (
        inputs["diagnostic_analysis_dir"] / "prefix_homogeneous_vs_standard_dim48.json"
    )
    comparison = json.loads(comparison_path.read_text())
    comparison["sources"]["matched_nulls"][0]["sha256"] = "0" * 64
    _write_json(comparison_path, comparison)
    with pytest.raises(ValueError, match="source hash mismatch"):
        build(**_build_kwargs(inputs))


def test_m2_bundle_rejects_local_path_leak_before_copy(tmp_path: Path) -> None:
    inputs = _base_inputs(tmp_path)
    report = inputs["exploratory_runs"]["matched_null_c"] / "report.md"
    _write_text(report, "Loaded from /Users/private/run/receipt.json\n")
    with pytest.raises(ValueError, match="local absolute path"):
        build(**_build_kwargs(inputs))
    assert not inputs["output_dir"].exists()
