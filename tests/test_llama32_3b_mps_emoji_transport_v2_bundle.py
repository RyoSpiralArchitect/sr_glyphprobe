from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

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
    "build_llama32_3b_mps_emoji_transport_v2_bundle",
    "scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py",
)
VALIDATOR = _load_module(
    "validate_llama32_3b_mps_emoji_transport_v2_bundle",
    "scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_dependency_fixture(root: Path) -> None:
    files: list[dict[str, str]] = []
    for relative in BUILDER._ADAPTER_BASE_DEPENDENCY_PATHS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
        files.append({"path": relative.as_posix(), "sha256": _sha256(destination)})
    manifest = root / BUILDER.FREEZE_MANIFEST_PATH
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "protocol_id": BUILDER.PROTOCOL_ID,
                "files": files,
            }
        ),
        encoding="utf-8",
    )


def test_v2_specialization_binds_every_public_namespace() -> None:
    assert (
        BUILDER.PROTOCOL_ID
        == VALIDATOR.PROTOCOL_ID
        == ("glyphprobe-e2-llama32-3b-mps-emoji-transport-v2")
    )
    assert (
        BUILDER.BUNDLE_ID
        == VALIDATOR.BUNDLE_ID
        == ("llama32_3b_mps_emoji_transport_v2_public_evidence")
    )
    assert (
        BUILDER.BUNDLE_ROOT
        == VALIDATOR.BUNDLE_ROOT
        == Path("artifacts/llama32_3b_mps_emoji_transport_v2")
    )
    assert (
        BUILDER.ROOT_MANIFEST_PATH
        == VALIDATOR.ROOT_MANIFEST_PATH
        == Path("artifacts/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_MANIFEST.json")
    )
    assert (
        BUILDER.FREEZE_MANIFEST_PATH
        == VALIDATOR.FREEZE_MANIFEST_PATH
        == Path("data/manifests/llama32_3b_mps_emoji_transport_v2.json")
    )
    assert (
        BUILDER.PREFLIGHT_PATH
        == VALIDATOR.PREFLIGHT_PATH
        == (BUILDER.BUNDLE_ROOT / "preflight/tokenization_audit_v2.json")
    )
    assert BUILDER.ATTEMPT_RECEIPT_PATH == VALIDATOR.ATTEMPT_RECEIPT_PATH
    assert BUILDER.EXECUTION_RECEIPT_PATH == VALIDATOR.EXECUTION_RECEIPT_PATH
    assert (
        BUILDER.ANALYZER_PATH
        == VALIDATOR.ANALYZER_PATH
        == Path("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py")
    )
    assert (
        BUILDER.BUILDER_PATH
        == VALIDATOR.BUILDER_PATH
        == Path("scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py")
    )
    assert (
        BUILDER.VALIDATOR_PATH
        == VALIDATOR.VALIDATOR_PATH
        == Path("scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py")
    )


def test_no_v1_experiment_marker_survives_specialized_implementations() -> None:
    assert _sha256(BUILDER._ADAPTER_BASE_PATH) == BUILDER._ADAPTER_BASE_SHA256
    assert _sha256(VALIDATOR._ADAPTER_BASE_PATH) == VALIDATOR._ADAPTER_BASE_SHA256
    old_markers = tuple(BUILDER._ADAPTER_EXPECTED_SOURCE_COUNTS)
    for source in (
        BUILDER._ADAPTER_SPECIALIZED_SOURCE,
        VALIDATOR._ADAPTER_SPECIALIZED_SOURCE,
    ):
        assert all(marker not in source for marker in old_markers)
        assert "p2_confirmatory_targets_v1.jsonl" in source
        assert "c1_causal_holdout_targets_v1.jsonl" in source
        assert "forbidden_in_v2_new_versioned_freeze_required" in source
    assert "transport-v2-launcher-logs" in BUILDER._ADAPTER_SPECIALIZED_SOURCE


def test_fixed_v2_grid_and_compact_inventory_are_exact() -> None:
    expected_configs = tuple(
        f"configs/e2_llama32_3b_mps_{arm}_{family}_v2.yaml"
        for arm, family in BUILDER.CELL_ORDER
    )
    expected_runs = tuple(
        f"e2-llama32-3b-mps-{arm}-{family}-transport-v2"
        for arm, family in BUILDER.CELL_ORDER
    )
    assert BUILDER.CONFIG_ORDER == VALIDATOR.CONFIG_ORDER == expected_configs
    assert BUILDER.RUN_NAMES == VALIDATOR.RUN_NAMES == expected_runs
    assert len(BUILDER.RUN_PUBLIC_FILES) == 15
    assert len(BUILDER.RUN_OMITTED_FILES) == 4
    assert BUILDER.RUN_ALL_FILES == VALIDATOR.RUN_ALL_FILES
    assert BUILDER.EXPECTED_TOTAL_LEDGER_ROWS == 15_600
    assert (
        sum(BUILDER.EXPECTED_LEDGER_ROWS[arm] for arm, _ in BUILDER.CELL_ORDER)
        == 15_600
    )
    receipt = "llama32_3b_mps_emoji_transport_v2_receipt.json"
    assert receipt in BUILDER.ANALYSIS_FILES
    assert receipt in VALIDATOR.ANALYSIS_FILES
    assert "llama32_3b_mps_emoji_transport_receipt.json" not in (BUILDER.ANALYSIS_FILES)


def test_fixed_cli_exposes_ten_v2_role_ordered_run_arguments() -> None:
    parser = BUILDER._parser()
    run_options = [
        action.option_strings[0]
        for action in parser._actions
        if action.dest.endswith("_run")
    ]
    assert run_options == [
        f"--{arm}-{family}-run" for arm, family in BUILDER.CELL_ORDER
    ]


@pytest.mark.parametrize("module", [BUILDER, VALIDATOR])
def test_adapter_dependencies_are_hash_bound_and_fail_closed(
    tmp_path: Path, module: Any
) -> None:
    _make_dependency_fixture(tmp_path)
    module._adapter_validate_dependencies(tmp_path)

    dependency = tmp_path / module._ADAPTER_BASE_DEPENDENCY_PATHS[0]
    dependency.write_bytes(dependency.read_bytes() + b"\n")
    error = (
        module.BundleBuildError if module is BUILDER else module.BundleValidationError
    )
    with pytest.raises(error, match="dependency hash differs"):
        module._adapter_validate_dependencies(tmp_path)


def test_public_entrypoints_cannot_bypass_dependency_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, Path]] = []

    def dependency_check(root: Path) -> None:
        calls.append(("dependency", Path(root)))

    def build_impl(root: Path, **kwargs: Any) -> dict[str, str]:
        calls.append(("build", Path(root)))
        return {"status": "built"}

    def validate_impl(root: Path) -> dict[str, str]:
        calls.append(("validate", Path(root)))
        return {"status": "pass"}

    monkeypatch.setattr(BUILDER, "_adapter_validate_dependencies", dependency_check)
    monkeypatch.setattr(BUILDER, "_adapter_impl_build_bundle", build_impl)
    assert BUILDER.build_bundle(
        tmp_path,
        run_dirs={},
        analysis_dir=tmp_path / "analysis",
    ) == {"status": "built"}
    assert calls == [("dependency", tmp_path), ("build", tmp_path)]

    calls.clear()
    monkeypatch.setattr(VALIDATOR, "_adapter_validate_dependencies", dependency_check)
    monkeypatch.setattr(VALIDATOR, "_adapter_impl_validate_bundle", validate_impl)
    assert VALIDATOR.validate_bundle(tmp_path) == {"status": "pass"}
    assert calls == [("dependency", tmp_path), ("validate", tmp_path)]


def test_bilingual_readmes_bind_policy_without_absolute_paths() -> None:
    readmes = [ROOT / path for path in BUILDER.PUBLIC_README_PATHS]
    assert [path.name for path in readmes] == ["README.md", "README.ja.md"]
    assert all(path.is_file() for path in readmes)
    assert BUILDER._scan_absolute_paths(readmes) == []
    for path in readmes:
        text = path.read_text(encoding="utf-8")
        assert BUILDER.PROTOCOL_ID in text
        assert "15,600" in text
        assert "p2_confirmatory_targets_v1.jsonl" in text
        assert "c1_causal_holdout_targets_v1.jsonl" in text
        assert "absolute" in text or "絶対" in text


def test_protected_banks_remain_declaration_only() -> None:
    assert (
        BUILDER.EXCLUDED_CONTENT
        == VALIDATOR.EXCLUDED_CONTENT
        == (
            "data/targets/p2_confirmatory_targets_v1.jsonl",
            "data/targets/c1_causal_holdout_targets_v1.jsonl",
        )
    )
    manifest = {
        "excluded_content_access": {
            "paths": list(VALIDATOR.EXCLUDED_CONTENT),
            "content_opened_or_read": False,
            "content_hashed": False,
            "content_tokenized": False,
            "model_forward_count": 0,
            "verification_scope": (
                "declaration only; protected banks are outside builder and validator "
                "input surfaces"
            ),
        }
    }
    VALIDATOR._validate_excluded_declaration(manifest)
