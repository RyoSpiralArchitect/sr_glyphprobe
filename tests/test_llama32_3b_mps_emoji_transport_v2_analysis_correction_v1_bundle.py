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
    "build_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle",
    "scripts/build_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py",
)
VALIDATOR = _load_module(
    "validate_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle",
    "scripts/validate_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_bundle.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_frozen_base_dependencies_and_v2_namespace() -> None:
    assert _sha256(ROOT / BUILDER.BASE_BUILDER_PATH) == BUILDER.BASE_BUILDER_SHA256
    assert (
        _sha256(ROOT / VALIDATOR.BASE_VALIDATOR_PATH) == VALIDATOR.BASE_VALIDATOR_SHA256
    )
    assert BUILDER.PROTOCOL_ID == VALIDATOR.PROTOCOL_ID
    assert BUILDER.BUNDLE_ROOT == VALIDATOR.BUNDLE_ROOT
    assert BUILDER.ROOT_MANIFEST_PATH == VALIDATOR.ROOT_MANIFEST_PATH
    assert BUILDER.CORRECTION_ID == VALIDATOR.CORRECTION_ID
    assert _sha256(ROOT / BUILDER.HELPER_PATH) == BUILDER.HELPER_SHA256
    assert _sha256(ROOT / VALIDATOR.HELPER_PATH) == VALIDATOR.HELPER_SHA256


def test_run_source_projection_is_temporary_and_preserves_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    run_dir = root / "runs" / "run-id"
    run_dir.mkdir(parents=True)
    (run_dir / "receipt.json").write_text(
        json.dumps({"run_id": run_dir.name}), encoding="utf-8"
    )
    log = root / "runs" / "launcher.log"
    wrapped = b"prefix\nComplete  " + str(run_dir).encode()[:80] + b"\n"
    wrapped += str(run_dir).encode()[80:] + b"\n"
    log.write_bytes(wrapped)
    seen: dict[str, Any] = {}

    def parser(payload: bytes, *, expected_run_dir: Path, expected_run_id: str):
        seen["parser"] = (payload, expected_run_dir, expected_run_id)

    def base_validator(*args: Any, process: dict[str, Any], **kwargs: Any):
        projected = Path(process["log_path"])
        seen["projected"] = projected
        assert projected.read_bytes() == b"Complete  " + str(run_dir).encode() + b"\n"
        return [], [], {"run_id": run_dir.name}

    monkeypatch.setattr(BUILDER.correction, "parse_completion_wrap", parser)
    monkeypatch.setattr(BUILDER, "_ORIGINAL_VALIDATE_RUN_SOURCE", base_validator)
    original = log.read_bytes()
    expected_log_sha256 = _sha256(log)
    original_read_bytes = Path.read_bytes
    source_reads = 0

    def read_bytes_once(path: Path) -> bytes:
        nonlocal source_reads
        if path == log:
            source_reads += 1
            return original if source_reads == 1 else b"concurrent replacement"
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes_once)
    result = BUILDER._corrected_validate_run_source(
        root,
        run_dir,
        arm="full50",
        family="sky",
        analysis_input={},
        process={
            "log_path": str(log.relative_to(root)),
            "log_sha256": expected_log_sha256,
        },
    )
    assert result == ([], [], {"run_id": run_dir.name})
    assert seen["parser"] == (original, run_dir, run_dir.name)
    assert not seen["projected"].exists()
    assert source_reads == 1
    assert original_read_bytes(log) == original


@pytest.mark.parametrize("base_raises", [False, True])
def test_builder_restores_both_base_patches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, base_raises: bool
) -> None:
    original_run_validator = BUILDER.base._validate_run_source
    original_writer = BUILDER.base._atomic_write_json
    monkeypatch.setattr(
        BUILDER, "_validate_correction_authority", lambda root: ({}, {})
    )
    monkeypatch.setattr(
        BUILDER,
        "_analysis_receipt",
        lambda root, analysis: {BUILDER.RECEIPT_CORRECTION_KEY: {}},
    )
    monkeypatch.setattr(
        BUILDER, "_root_correction_block", lambda root, block: {"ok": True}
    )

    def base_build(root: Path, **kwargs: Any):
        assert (
            BUILDER.base._validate_run_source is BUILDER._corrected_validate_run_source
        )
        assert BUILDER.base._atomic_write_json is not original_writer
        if base_raises:
            raise BUILDER.BundleBuildError("stop")
        value: dict[str, Any] = {}
        BUILDER.base._atomic_write_json(root / BUILDER.ROOT_MANIFEST_PATH, value)
        return value

    monkeypatch.setattr(BUILDER.base, "build_bundle", base_build)
    if base_raises:
        with pytest.raises(BUILDER.BundleBuildError, match="stop"):
            BUILDER.build_bundle(tmp_path, run_dirs={}, analysis_dir=tmp_path)
    else:
        manifest = BUILDER.build_bundle(tmp_path, run_dirs={}, analysis_dir=tmp_path)
        assert manifest[BUILDER.ROOT_CORRECTION_KEY] == {"ok": True}
    assert BUILDER.base._validate_run_source is original_run_validator
    assert BUILDER.base._atomic_write_json is original_writer


def test_builder_rejects_a_prepatched_base_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def foreign_validator(*args: Any, **kwargs: Any):
        raise AssertionError("must not be called")

    monkeypatch.setattr(BUILDER.base, "_validate_run_source", foreign_validator)
    with pytest.raises(
        BUILDER.BundleBuildError,
        match="frozen base builder patch state differs before correction",
    ):
        BUILDER.build_bundle(tmp_path, run_dirs={}, analysis_dir=tmp_path)
    assert BUILDER.base._validate_run_source is foreign_validator


def test_final_validator_checks_correction_before_delegating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    root_block = {
        "active_publication_tooling": {"validator": {"path": "active", "sha256": "a"}},
        "base_publication_tooling": {"validator": {"path": "base", "sha256": "b"}},
    }
    monkeypatch.setattr(
        VALIDATOR,
        "_validate_correction_authority",
        lambda root: calls.append("authority") or ({}, {}),
    )
    monkeypatch.setattr(
        VALIDATOR,
        "_validate_correction_blocks",
        lambda root: calls.append("blocks") or root_block,
    )
    monkeypatch.setattr(
        VALIDATOR.base,
        "validate_bundle",
        lambda root: calls.append("base") or {"status": "pass"},
    )
    report = VALIDATOR.validate_bundle(tmp_path)
    assert calls == ["authority", "blocks", "base"]
    assert report["status"] == "pass"
    assert report["correction_revision"] == VALIDATOR.CORRECTION_ID
    assert (
        report["active_bundle_validator"]
        == root_block["active_publication_tooling"]["validator"]
    )


def test_root_block_names_active_and_base_publication_tooling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        VALIDATOR,
        "_binding",
        lambda root, relative: {"path": relative.as_posix(), "sha256": "0" * 64},
    )
    monkeypatch.setattr(
        VALIDATOR,
        "_pinned_binding",
        lambda root, relative, sha256: {
            "path": relative.as_posix(),
            "sha256": sha256,
        },
    )
    block = VALIDATOR._root_correction_block(tmp_path, {"correction_id": "x"})
    assert block["base_protocol_id"] == VALIDATOR.PROTOCOL_ID
    assert block["base_bundle_root"] == VALIDATOR.BUNDLE_ROOT.as_posix()
    assert block["active_publication_tooling"]["validator"]["path"] == (
        VALIDATOR.VALIDATOR_ADAPTER_PATH.as_posix()
    )
    assert block["base_publication_tooling"]["validator"] == {
        "path": VALIDATOR.BASE_VALIDATOR_PATH.as_posix(),
        "sha256": VALIDATOR.BASE_VALIDATOR_SHA256,
    }
    assert block["source_logs_changed"] is False
    assert block["scientific_math_changed"] is False
