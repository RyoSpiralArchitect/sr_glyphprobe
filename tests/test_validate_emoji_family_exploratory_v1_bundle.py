from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MANIFEST_SHA256 = (
    "c22989ebc9ccaaf5f4652624d61ea11e2a9df4f2148a7886daf50c2fc3e4f53f"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = _load_module(
    "build_emoji_family_exploratory_v1_bundle",
    ROOT / "scripts" / "build_emoji_family_exploratory_v1_bundle.py",
)
VALIDATOR = _load_module(
    "validate_emoji_family_exploratory_v1_bundle",
    ROOT / "scripts" / "validate_emoji_family_exploratory_v1_bundle.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads((ROOT / VALIDATOR.MANIFEST_PATH).read_text(encoding="utf-8"))


def test_public_manifest_and_tooling_are_immutably_bound() -> None:
    manifest_path = ROOT / VALIDATOR.MANIFEST_PATH
    manifest = _manifest()
    assert _sha256(manifest_path) == EXPECTED_MANIFEST_SHA256
    assert manifest["freeze"]["public_freeze_commit"] == VALIDATOR.FREEZE_COMMIT
    assert manifest["tooling"] == {
        "builder_path": BUILDER.BUILDER_PATH.as_posix(),
        "builder_sha256": _sha256(ROOT / BUILDER.BUILDER_PATH),
        "validator_path": BUILDER.VALIDATOR_PATH.as_posix(),
        "validator_sha256": _sha256(ROOT / BUILDER.VALIDATOR_PATH),
    }


def test_full_public_bundle_validation_is_deterministic() -> None:
    first = VALIDATOR.validate_bundle(ROOT)
    second = VALIDATOR.validate_bundle(ROOT)
    assert first == second
    assert first["status"] == "pass"
    assert first["manifest_sha256"] == EXPECTED_MANIFEST_SHA256
    assert first["freeze_commit"] == "0cd4e11610e42253ead9ce9aff9f0b02474a0558"
    assert first["role_bindings_verified"] == 5
    assert first["absolute_path_match_count"] == 0
    assert first["p2_c1_content_accessed"] is False
    assert first["descriptive_random_controls"]["nonpositive_cell_count"] == 10
    assert first["descriptive_random_controls"]["reported_cell_count"] == 30
    assert first["independent_outcome_review"] == {
        "status": "pass",
        "same_input_reanalysis_byte_identical": True,
        "byte_identical_file_count": 6,
    }


def test_inventory_is_exact_and_large_raw_files_are_absent() -> None:
    manifest = _manifest()
    assert manifest["inventory"] == {
        "public_member_scope": (
            "payload files under artifacts/emoji_family_exploratory_v1; "
            "the root manifest is excluded from member byte totals"
        ),
        "role_count": 5,
        "analysis_file_count": 6,
        "per_role_included_file_count": 15,
        "public_member_file_count": 82,
        "public_file_count_including_root_manifest": 83,
        "public_member_total_bytes": 1_237_638,
        "public_jsonl_file_count": 39,
        "public_jsonl_row_count": 1_635,
        "omitted_raw_file_count": 20,
        "omitted_raw_total_bytes": 74_618_134,
        "omitted_intervention_jsonl_rows": 8_880,
    }
    for run in manifest["runs"]:
        public_dir = ROOT / run["public_directory"]
        assert {
            path.name for path in public_dir.iterdir()
        } == VALIDATOR.RUN_PUBLIC_FILES
        assert {
            Path(item["source_path"]).name for item in run["omitted_raw_files"]
        } == set(VALIDATOR.RUN_OMITTED_ROWS)
        assert all(
            item["public_copy_path"] is None for item in run["omitted_raw_files"]
        )
        assert all(
            not (public_dir / filename).exists()
            for filename in VALIDATOR.RUN_OMITTED_ROWS
        )


def test_analysis_hashes_rows_and_random_control_result_are_public() -> None:
    manifest = _manifest()
    assert manifest["analysis"]["output_sha256"] == VALIDATOR.ANALYSIS_SHA256
    assert manifest["analysis"]["expected_jsonl_rows"] == VALIDATOR.ANALYSIS_ROWS
    assert manifest["analysis"]["descriptive_random_control_summary"] == {
        "metric": "emoji_advantage_over_random",
        "comparison": "less_than_or_equal_to_zero",
        "nonpositive_cell_count": 10,
        "reported_cell_count": 30,
        "fraction_nonpositive": 1 / 3,
        "endpoint_observations": False,
        "use": "descriptive_integrity_screen_only",
    }


def test_validator_detects_member_tampering(tmp_path: Path) -> None:
    metadata = _manifest()["preflight"]
    destination = tmp_path / metadata["path"]
    destination.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / metadata["path"], destination)
    destination.write_bytes(destination.read_bytes() + b"\n")
    with pytest.raises(VALIDATOR.BundleValidationError, match="byte count differs"):
        VALIDATOR._verify_public_member(tmp_path, metadata)


def test_builder_member_and_manifest_writes_are_no_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "public" / "evidence.json"
    source.write_text('{"value": 1}\n', encoding="utf-8")
    BUILDER._copy_exact(source, destination)
    original_bytes = destination.read_bytes()
    original_inode = destination.stat().st_ino

    BUILDER._copy_exact(source, destination)
    assert destination.read_bytes() == original_bytes
    assert destination.stat().st_ino == original_inode

    source.write_text('{"value": 2}\n', encoding="utf-8")
    with pytest.raises(BUILDER.BundleBuildError, match="refusing to overwrite"):
        BUILDER._copy_exact(source, destination)
    assert destination.read_bytes() == original_bytes

    manifest_path = tmp_path / "manifest.json"
    BUILDER._atomic_write_json(manifest_path, {"value": 1})
    manifest_bytes = manifest_path.read_bytes()
    manifest_inode = manifest_path.stat().st_ino
    BUILDER._atomic_write_json(manifest_path, {"value": 1})
    assert manifest_path.read_bytes() == manifest_bytes
    assert manifest_path.stat().st_ino == manifest_inode
    with pytest.raises(BUILDER.BundleBuildError, match="refusing to overwrite"):
        BUILDER._atomic_write_json(manifest_path, {"value": 2})
    assert manifest_path.read_bytes() == manifest_bytes


def test_validation_never_opens_p2_or_c1_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_open = Path.open
    forbidden = set(VALIDATOR.EXCLUDED_CONTENT)

    def guarded_open(path: Path, *args, **kwargs):
        normalized = path.as_posix()
        assert not any(normalized.endswith(value) for value in forbidden)
        assert not path.resolve().is_relative_to((ROOT / "runs").resolve())
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    assert VALIDATOR.validate_bundle(ROOT)["p2_c1_content_accessed"] is False
    declaration_source = inspect.getsource(VALIDATOR._validate_excluded_declaration)
    assert "open(" not in declaration_source
    assert "read_" not in declaration_source
    assert "_sha256" not in declaration_source
