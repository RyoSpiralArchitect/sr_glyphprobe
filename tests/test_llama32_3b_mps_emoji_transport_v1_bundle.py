from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_llama32_3b_mps_emoji_transport_v1_bundle",
    "scripts/build_llama32_3b_mps_emoji_transport_v1_bundle.py",
)
VALIDATOR = _load_module(
    "validate_llama32_3b_mps_emoji_transport_v1_bundle",
    "scripts/validate_llama32_3b_mps_emoji_transport_v1_bundle.py",
)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _analysis_rows() -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    target_ids = [f"target_{index:02d}" for index in range(24)]
    panel = [
        {
            "panel_arm": arm,
            "family": family,
            "layer": layer,
            "target_id": target_id,
            "value": 0.0,
        }
        for arm in BUILDER.ARMS
        for family in BUILDER.FAMILIES
        for layer in BUILDER.LAYERS
        for target_id in target_ids
    ]
    transfer = [
        {
            "panel_arm": arm,
            "source_family": source,
            "prototype_family": prototype,
            "layer": layer,
            "target_id": target_id,
            "value": 0.0,
        }
        for arm in BUILDER.ARMS
        for source in BUILDER.FAMILIES
        for prototype in BUILDER.FAMILIES
        if source != prototype
        for layer in BUILDER.LAYERS
        for target_id in target_ids
    ]
    family_cells = [
        {
            "panel_arm": arm,
            "family": family,
            "layer": layer,
            "value": 0.0,
        }
        for arm in BUILDER.ARMS
        for family in BUILDER.FAMILIES
        for layer in BUILDER.LAYERS
    ]
    transfer_cells = [
        {
            "panel_arm": arm,
            "source_family": source,
            "prototype_family": prototype,
            "layer": layer,
            "value": 0.0,
        }
        for arm in BUILDER.ARMS
        for source in BUILDER.FAMILIES
        for prototype in BUILDER.FAMILIES
        if source != prototype
        for layer in BUILDER.LAYERS
    ]
    return target_ids, {
        "panel_target_scores.jsonl": panel,
        "transfer_target_scores.jsonl": transfer,
        "family_cell_summary.jsonl": family_cells,
        "transfer_cell_summary.jsonl": transfer_cells,
    }


def _make_analysis_dir(path: Path) -> Path:
    path.mkdir()
    target_ids, rows = _analysis_rows()
    for filename, values in rows.items():
        _write_jsonl(path / filename, values)
    (path / "report.md").write_text(
        "# Synthetic structural fixture\n", encoding="utf-8"
    )
    hashed_outputs = [
        {
            "filename": filename,
            "sha256": hashlib.sha256((path / filename).read_bytes()).hexdigest(),
            **({"row_count": len(rows[filename])} if filename in rows else {}),
        }
        for filename in BUILDER.ANALYSIS_FILES
        if filename != "llama32_3b_mps_emoji_transport_receipt.json"
    ]
    receipt = {
        "schema_version": 1,
        "analysis_id": BUILDER.PROTOCOL_ID,
        "status": "transport_criterion_not_met",
        "scientific_result": True,
        "analysis_implementation": {
            "path": BUILDER.ANALYZER_PATH.as_posix(),
            "sha256": hashlib.sha256(
                (ROOT / BUILDER.ANALYZER_PATH).read_bytes()
            ).hexdigest(),
        },
        "manifest_binding": {
            "path": BUILDER.FREEZE_MANIFEST_PATH.as_posix(),
            "sha256": "a" * 64,
        },
        "execution_binding": {
            "path": BUILDER.EXECUTION_RECEIPT_PATH.as_posix(),
            "sha256": "b" * 64,
        },
        "data_scope": {
            "ordered_target_ids": target_ids,
            "p2_confirmatory_holdout_accessed": False,
            "c1_causal_holdout_accessed": False,
            "model_forward_passes_by_analyzer": 0,
            "tokenizer_calls_by_analyzer": 0,
        },
        "row_completeness": {
            "published_row_counts": BUILDER.ANALYSIS_EXPECTED_ROWS,
        },
        "output_inventory": list(BUILDER.ANALYSIS_FILES),
        "hashed_outputs_excluding_self": hashed_outputs,
    }
    (path / "llama32_3b_mps_emoji_transport_receipt.json").write_text(
        json.dumps(receipt), encoding="utf-8"
    )
    return path


def test_fixed_cli_exposes_ten_role_ordered_run_arguments() -> None:
    parser = BUILDER._parser()
    run_options = [
        action.option_strings[0]
        for action in parser._actions
        if action.dest.endswith("_run")
    ]
    assert run_options == [
        f"--{arm}-{family}-run" for arm, family in BUILDER.CELL_ORDER
    ]
    assert BUILDER.CONFIG_ORDER == tuple(
        f"configs/e2_llama32_3b_mps_{arm}_{family}_v1.yaml"
        for arm, family in BUILDER.CELL_ORDER
    )
    assert (
        sum(BUILDER.EXPECTED_LEDGER_ROWS[arm] for arm, _ in BUILDER.CELL_ORDER)
        == 15_600
    )
    assert len(BUILDER.RUN_PUBLIC_FILES) == 15
    assert len(BUILDER.RUN_OMITTED_FILES) == 4
    assert BUILDER.RUN_ALL_FILES == VALIDATOR.RUN_ALL_FILES


def test_exact_copy_and_manifest_write_are_identical_only(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "public" / "member.json"
    source.write_text('{"value": 1}\n', encoding="utf-8")
    BUILDER._copy_exact(source, destination)
    original = destination.read_bytes()
    inode = destination.stat().st_ino
    BUILDER._copy_exact(source, destination)
    assert destination.read_bytes() == original
    assert destination.stat().st_ino == inode

    source.write_text('{"value": 2}\n', encoding="utf-8")
    with pytest.raises(BUILDER.BundleBuildError, match="refusing to overwrite"):
        BUILDER._copy_exact(source, destination)
    assert destination.read_bytes() == original

    manifest_path = tmp_path / "manifest.json"
    BUILDER._atomic_write_json(manifest_path, {"value": 1})
    manifest_bytes = manifest_path.read_bytes()
    BUILDER._atomic_write_json(manifest_path, {"value": 1})
    assert manifest_path.read_bytes() == manifest_bytes
    with pytest.raises(BUILDER.BundleBuildError, match="refusing to overwrite"):
        BUILDER._atomic_write_json(manifest_path, {"value": 2})


def test_omitted_jsonl_and_npz_metadata_is_structural_and_hash_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(BUILDER, "MODEL_DIM", 3)
    monkeypatch.setattr(BUILDER, "VOCAB_SIZE", 11)
    monkeypatch.setattr(VALIDATOR, "MODEL_DIM", 3)
    monkeypatch.setattr(VALIDATOR, "VOCAB_SIZE", 11)
    monkeypatch.setattr(
        VALIDATOR,
        "CONDITION_COUNTS",
        {"full50": 2, "core35": 2},
    )
    monkeypatch.setattr(
        VALIDATOR,
        "EXPECTED_LEDGER_ROWS",
        {"full50": 3, "core35": 2},
    )
    ledger = tmp_path / "interventions.jsonl"
    _write_jsonl(ledger, [{"row": index} for index in range(3)])
    ledger_metadata = BUILDER._omitted_file_metadata(
        ledger,
        run_label="synthetic-run",
        condition_count=2,
        expected_ledger_rows=3,
    )
    assert ledger_metadata["row_count"] == 3
    assert ledger_metadata["sha256"] == hashlib.sha256(ledger.read_bytes()).hexdigest()
    VALIDATOR._validate_omitted_record(
        ledger_metadata, arm="full50", run_label="synthetic-run"
    )

    directions = tmp_path / "directions.npz"
    arrays: dict[str, np.ndarray] = {
        "layers": np.asarray(BUILDER.LAYERS, dtype=np.int64)
    }
    for seed in BUILDER.DIRECTION_SEEDS:
        arrays[f"directions_seed_{seed}"] = np.zeros((2, 2, 3), dtype=np.float32)
        arrays[f"panel_means_seed_{seed}"] = np.zeros((2, 2, 3), dtype=np.float32)
        arrays[f"generic_seed_{seed}"] = np.zeros((2, 3), dtype=np.float32)
    np.savez_compressed(directions, **arrays)
    direction_metadata = BUILDER._omitted_file_metadata(
        directions,
        run_label="synthetic-run",
        condition_count=2,
        expected_ledger_rows=3,
    )
    assert direction_metadata["array_count"] == 10
    assert {
        item["key"]: (item["shape"], item["dtype"])
        for item in direction_metadata["arrays"]
    } == BUILDER._expected_npz_layout("directions.npz", 2)
    VALIDATOR._validate_omitted_record(
        direction_metadata, arm="full50", run_label="synthetic-run"
    )

    direction_metadata["arrays"][0]["shape"] = [999]
    with pytest.raises(
        VALIDATOR.BundleValidationError, match="size differs|layout differs"
    ):
        VALIDATOR._validate_omitted_record(
            direction_metadata, arm="full50", run_label="synthetic-run"
        )


def test_analysis_validator_checks_all_four_exact_grids(tmp_path: Path) -> None:
    analysis = _make_analysis_dir(tmp_path / "analysis")
    _, receipt, rows = BUILDER._validate_analysis(
        analysis,
        freeze_sha="a" * 64,
        execution_sha="b" * 64,
    )
    assert receipt["status"] == "transport_criterion_not_met"
    assert {name: len(values) for name, values in rows.items()} == {
        **BUILDER.ANALYSIS_EXPECTED_ROWS
    }

    panel_path = analysis / "panel_target_scores.jsonl"
    panel_rows = rows["panel_target_scores.jsonl"]
    panel_rows[-1] = dict(panel_rows[0])
    _write_jsonl(panel_path, panel_rows)
    with pytest.raises(BUILDER.BundleBuildError, match="duplicate analysis key"):
        BUILDER._validate_analysis(
            analysis,
            freeze_sha="a" * 64,
            execution_sha="b" * 64,
        )


def test_exact_run_inventory_rejects_extra_or_missing_members(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    for filename in BUILDER.RUN_ALL_FILES:
        (run / filename).touch()
    BUILDER._exact_directory(run, BUILDER.RUN_ALL_FILES, "synthetic run")
    (run / "unexpected.txt").touch()
    with pytest.raises(BUILDER.BundleBuildError, match="inventory differs"):
        BUILDER._exact_directory(run, BUILDER.RUN_ALL_FILES, "synthetic run")


def test_absolute_path_scan_fails_without_transforming_evidence(tmp_path: Path) -> None:
    safe = tmp_path / "safe.md"
    unsafe = tmp_path / "unsafe.json"
    safe.write_text("portable/path.json\n", encoding="utf-8")
    unsafe.write_text('{"path":"/Users/example/private/run"}\n', encoding="utf-8")
    assert BUILDER._scan_absolute_paths([safe]) == []
    findings = BUILDER._scan_absolute_paths([unsafe])
    assert len(findings) == 1
    assert findings[0]["match"] == "/Users/example/private/run"
    assert unsafe.read_text(encoding="utf-8").endswith('"}\n')


def test_protected_banks_are_declaration_only_and_not_input_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = {
        "excluded_content_access": {
            "paths": list(VALIDATOR.EXCLUDED_CONTENT),
            "content_opened_or_read": False,
            "content_hashed": False,
            "content_tokenized": False,
            "model_forward_count": 0,
        }
    }
    original_open = Path.open

    def guarded_open(path: Path, *args, **kwargs):
        normalized = path.as_posix()
        assert not any(
            normalized.endswith(value) for value in VALIDATOR.EXCLUDED_CONTENT
        )
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    VALIDATOR._validate_excluded_declaration(manifest)
    for function in (
        BUILDER.build_bundle,
        VALIDATOR.validate_bundle,
        VALIDATOR._validate_excluded_declaration,
    ):
        source = inspect.getsource(function)
        assert "root / EXCLUDED_CONTENT" not in source
        assert "_sha256(root /" + " EXCLUDED" not in source


def test_public_path_guard_rejects_escape_and_symlink(tmp_path: Path) -> None:
    bundle = tmp_path / VALIDATOR.BUNDLE_ROOT
    bundle.mkdir(parents=True)
    with pytest.raises(VALIDATOR.BundleValidationError, match="unsafe public path"):
        VALIDATOR._safe_public_path(
            tmp_path, "artifacts/llama32_3b_mps_emoji_transport_v1/../escape.json"
        )
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    link = bundle / "link.json"
    link.symlink_to(outside)
    with pytest.raises(VALIDATOR.BundleValidationError, match="escapes|symlink"):
        VALIDATOR._safe_public_path(tmp_path, link.relative_to(tmp_path).as_posix())
