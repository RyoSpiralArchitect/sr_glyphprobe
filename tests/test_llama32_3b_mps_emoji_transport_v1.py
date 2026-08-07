from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_llama32_3b_mps_emoji_transport_v1.py"
LAUNCHER_PATH = ROOT / "scripts" / "run_llama32_3b_mps_emoji_transport_v1.py"


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_script("audit_llama32_3b_mps_emoji_transport_v1", AUDIT_PATH)
LAUNCHER = _load_script("run_llama32_3b_mps_emoji_transport_v1", LAUNCHER_PATH)


class PreTrainedTokenizerFast:
    """Small deterministic tokenizer double for the frozen emoji lattice."""

    is_fast = True
    vocab_size = AUDIT.TOKENIZER_BASE_VOCAB_SIZE

    def __init__(self, authority) -> None:
        self._glyphs: dict[str, tuple[int, ...]] = {}
        for family in AUDIT.FAMILY_ORDER:
            for item in authority.panels["full50"][family]:
                self._glyphs[item["glyph"]] = AUDIT._expected_raw_ids(item["id"])
        self._decoded: dict[tuple[int, ...], str] = {}

    def __len__(self) -> int:
        return AUDIT.TOKENIZER_LENGTH

    @staticmethod
    def _text_token(character: str, index: int) -> int:
        return 20_000 + ((ord(character) * 257 + index) % 80_000)

    def __call__(
        self,
        text: str,
        *,
        add_special_tokens: bool,
        return_attention_mask: bool,
        return_offsets_mapping: bool,
    ) -> dict[str, object]:
        assert add_special_tokens is False
        assert return_attention_mask is False
        assert return_offsets_mapping is True
        matches = [
            (text.index(glyph), glyph) for glyph in self._glyphs if glyph in text
        ]
        assert len(matches) == 1
        start, glyph = matches[0]
        ids: list[int] = []
        offsets: list[tuple[int, int]] = []
        for index, character in enumerate(text[:start]):
            ids.append(self._text_token(character, index))
            offsets.append((index, index + 1))
        glyph_ids = self._glyphs[glyph]
        ids.extend(glyph_ids)
        offsets.extend([(start, start + 1)] * len(glyph_ids))
        for index, character in enumerate(text[start + 1 :], start + 1):
            ids.append(self._text_token(character, index))
            offsets.append((index, index + 1))
        self._decoded[tuple(ids)] = text
        return {"input_ids": ids, "offset_mapping": offsets}

    def decode(
        self,
        ids: list[int],
        *,
        skip_special_tokens: bool,
        clean_up_tokenization_spaces: bool = False,
    ) -> str:
        assert skip_special_tokens is False
        assert clean_up_tokenization_spaces is False
        return self._decoded[tuple(ids)]


def _copy_static_surface(destination: Path) -> Path:
    for relative in (
        AUDIT.TARGET_RELATIVE,
        AUDIT.SOURCE_RELATIVE,
        *AUDIT.FULL_PANEL_PATHS.values(),
        *AUDIT.CORE_PANEL_PATHS.values(),
        *AUDIT.CONFIG_PATHS.values(),
        *AUDIT.CRITICAL_FILE_PATHS,
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return destination


def _manifest_for(root: Path, authority) -> dict[str, object]:
    paths = {
        AUDIT.TARGET_RELATIVE.as_posix(),
        AUDIT.SOURCE_RELATIVE.as_posix(),
        *(row["path"] for row in authority.report["panels"]),
        *(row["path"] for row in authority.report["configs"]),
        *(row["path"] for row in authority.report["critical_files"]),
    }
    files = [
        {
            "path": relative,
            "sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest(),
        }
        for relative in sorted(paths)
    ]
    arms = {
        scope: {
            family: {
                "config_path": AUDIT.CONFIG_PATHS[(scope, family)].as_posix(),
                "panel_path": (
                    AUDIT.FULL_PANEL_PATHS[family]
                    if scope == "full50"
                    else AUDIT.CORE_PANEL_PATHS[family]
                ).as_posix(),
            }
            for family in AUDIT.FAMILY_ORDER
        }
        for scope in AUDIT.SCOPE_ORDER
    }
    return {
        "schema_version": 1,
        "manifest_id": AUDIT.MANIFEST_ID,
        "protocol_id": AUDIT.PROTOCOL_ID,
        "environment": dict(AUDIT.EXPECTED_ENVIRONMENT),
        "model_artifact": dict(AUDIT.EXPECTED_MODEL_ARTIFACT),
        "architecture": dict(AUDIT.EXPECTED_ARCHITECTURE),
        "files": files,
        "fixed_cell": {
            "backend": {
                "kind": "transformers",
                "model": AUDIT.MODEL_ID,
                "revision": AUDIT.MODEL_REVISION,
                "device": "mps",
                "dtype": "float32",
            },
            "layers": [5, 11],
        },
        "shared_inputs": {
            "target": {
                "path": AUDIT.TARGET_RELATIVE.as_posix(),
                "sha256": AUDIT.TARGET_SHA256,
            },
            "source": {
                "path": AUDIT.SOURCE_RELATIVE.as_posix(),
                "sha256": AUDIT.SOURCE_SHA256,
            },
        },
        "arms": arms,
        "analysis": {
            "analysis_id": AUDIT.PROTOCOL_ID,
            "script_path": AUDIT.ANALYZER_RELATIVE.as_posix(),
            "script_sha256": hashlib.sha256(
                (root / AUDIT.ANALYZER_RELATIVE).read_bytes()
            ).hexdigest(),
            "e1_math_dependency": {
                "path": AUDIT.E1_MATH_RELATIVE.as_posix(),
                "sha256": hashlib.sha256(
                    (root / AUDIT.E1_MATH_RELATIVE).read_bytes()
                ).hexdigest(),
            },
            "status": "frozen_before_outcomes",
        },
    }


def _runtime_authority() -> dict[str, object]:
    return {
        "environment": dict(AUDIT.EXPECTED_ENVIRONMENT),
        "model_artifact": {
            **AUDIT.EXPECTED_MODEL_ARTIFACT,
            "files": {},
        },
        "architecture": {
            **AUDIT.EXPECTED_ARCHITECTURE,
            "commit_hash": AUDIT.MODEL_REVISION,
            "auto_config_only": True,
        },
        "language_model_loaded": False,
        "model_forward_count": 0,
        "runtime_parameter_dtype_measured": False,
        "runtime_parameter_dtype_measurement_stage": (
            "backend_load_pre_forward_and_run_receipt"
        ),
    }


def _git_authority(commit: str = "a" * 40) -> dict[str, object]:
    return {
        "audited_commit": commit,
        "branch": "main",
        "origin_main_commit": commit,
        "worktree_clean_before_publication": True,
    }


def _launcher_preflight(manifest_sha256: str) -> dict[str, object]:
    return {
        "protocol_id": LAUNCHER.PROTOCOL_ID,
        "status": "passed",
        "audited_commit": "a" * 40,
        "git_authority": _git_authority(),
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "static": {
            "manifest": {
                "present": True,
                "path": LAUNCHER.MANIFEST_RELATIVE.as_posix(),
                "sha256": manifest_sha256,
            }
        },
        "environment": dict(LAUNCHER.EXPECTED_ENVIRONMENT),
        "model_artifact": dict(LAUNCHER.EXPECTED_MODEL_ARTIFACT),
        "architecture": dict(LAUNCHER.EXPECTED_ARCHITECTURE),
        "authorization": {"frozen_grid_execution_authorized": True},
    }


def _prepare_launcher_surface(root: Path) -> tuple[Path, Path]:
    for relative in LAUNCHER.CONFIG_ORDER:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    manifest = root / LAUNCHER.MANIFEST_RELATIVE
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}\n", encoding="utf-8")
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    preflight = root / LAUNCHER.PREFLIGHT_RELATIVE
    preflight.parent.mkdir(parents=True, exist_ok=True)
    preflight.write_text(
        json.dumps(_launcher_preflight(manifest_sha256)),
        encoding="utf-8",
    )
    return preflight, root / LAUNCHER.EXECUTION_RECEIPT_RELATIVE


def _frozen_git(_root: Path, *args: str) -> str:
    if args == ("status", "--porcelain"):
        return ""
    if args == ("branch", "--show-current"):
        return "main"
    if args in (("rev-parse", "HEAD"), ("rev-parse", "origin/main")):
        return "b" * 40
    if args == ("diff", "--name-only", f"{'a' * 40}..{'b' * 40}"):
        return LAUNCHER.PREFLIGHT_RELATIVE.as_posix()
    raise AssertionError(args)


def test_static_authority_binds_ten_configs_and_two_panel_scopes() -> None:
    authority = AUDIT.load_static_authority(ROOT)
    assert authority.report["config_count"] == 10
    assert authority.report["panel_count"] == 10
    assert {row["path"] for row in authority.report["critical_files"]} == {
        path.as_posix() for path in AUDIT.CRITICAL_FILE_PATHS
    }
    assert authority.report["planned_counts"] == {
        "full50": {
            "per_family": {
                "source": 176,
                "target_baseline": 24,
                "emoji_intervention": 1440,
                "random_control": 288,
                "zero_hook_control": 48,
                "total": 1976,
                "intervention_rows": 1776,
            },
            "all_families_forward_calls": 9880,
            "all_families_intervention_rows": 8880,
        },
        "core35": {
            "per_family": {
                "source": 128,
                "target_baseline": 24,
                "emoji_intervention": 1008,
                "random_control": 288,
                "zero_hook_control": 48,
                "total": 1496,
                "intervention_rows": 1344,
            },
            "all_families_forward_calls": 7480,
            "all_families_intervention_rows": 6720,
        },
        "combined_forward_calls": 17360,
        "combined_intervention_rows": 15600,
    }
    assert authority.report["shared_inputs"]["target"]["ordered_ids"] == list(
        AUDIT.TARGET_IDS
    )
    assert authority.report["protected_banks"]["content_opened"] is False


def test_tokenizer_double_replays_exact_full50_and_core35_rules() -> None:
    authority = AUDIT.load_static_authority(ROOT)
    report = AUDIT.audit_suite(
        ROOT,
        tokenizer=PreTrainedTokenizerFast(authority),
        runtime_authority=_runtime_authority(),
        git_authority=_git_authority(),
    )
    assert report["protocol_id"] == AUDIT.PROTOCOL_ID
    assert report["status"] == "passed"
    assert report["model_forward_count"] == 0
    assert report["language_model_loaded"] is False
    assert report["p2_content_opened"] is False
    assert report["c1_content_opened"] is False
    assert report["environment"] == AUDIT.EXPECTED_ENVIRONMENT
    assert report["model_artifact"]["manifest_sha256"] == (
        AUDIT.MODEL_ARTIFACT_MANIFEST_SHA256
    )
    assert report["architecture"]["config_class"] == "LlamaConfig"
    assert report["tokenization"]["counts"] == {
        "raw_glyphs_verified": 50,
        "full50_wrapper_profiles_verified": 800,
        "core35_wrapper_profiles_verified": 560,
        "wrapper_count": 16,
    }
    raw = {row["id"]: row["token_ids"] for row in report["tokenization"]["raw"]}
    assert raw["sky_slot_01"] == [9468, 102032]
    assert raw["sky_slot_02"] == [9468, 107569]
    assert raw["social_slot_00"] == [9468, 100701]
    assert raw["animals_slot_03"] == [9468, 238, 242]


def test_static_audit_never_opens_protected_target_names(monkeypatch) -> None:
    original = Path.open

    def guarded(path: Path, *args, **kwargs):
        if path.name in AUDIT.FORBIDDEN_TARGET_NAMES:
            raise AssertionError(f"protected content opened: {path.name}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    authority = AUDIT.load_static_authority(ROOT)
    assert authority.report["protected_banks"]["content_opened"] is False


def test_core_panel_drift_fails_closed(tmp_path: Path) -> None:
    root = _copy_static_surface(tmp_path / "repo")
    path = root / AUDIT.CORE_PANEL_PATHS["sky"]
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["items"][0]["factors"]["matched_slot"] = "slot_99"
    path.write_text(yaml.safe_dump(document, allow_unicode=True), encoding="utf-8")
    with pytest.raises(AUDIT.AuditError, match="Factor binding"):
        AUDIT.load_static_authority(root)


def test_manifest_verifies_every_file_and_role_binding(tmp_path: Path) -> None:
    root = _copy_static_surface(tmp_path / "repo")
    authority = AUDIT.load_static_authority(root)
    manifest = _manifest_for(root, authority)
    path = root / AUDIT.MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    verified = AUDIT.load_static_authority(root, manifest_path=path)
    assert verified.report["manifest"]["present"] is True
    assert verified.report["manifest"]["verified_file_count"] == len(manifest["files"])

    manifest["files"][0]["sha256"] = "0" * 64
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with pytest.raises(AUDIT.AuditError, match="SHA-256 mismatch"):
        AUDIT.load_static_authority(root, manifest_path=path)


def test_manifest_rejects_protected_file_without_opening_it(tmp_path: Path) -> None:
    root = _copy_static_surface(tmp_path / "repo")
    authority = AUDIT.load_static_authority(root)
    manifest = _manifest_for(root, authority)
    manifest["files"].append(
        {
            "path": "data/targets/c1_causal_holdout_targets_v1.jsonl",
            "sha256": "0" * 64,
        }
    )
    path = root / AUDIT.MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AUDIT.AuditError, match="Protected target"):
        AUDIT.load_static_authority(root, manifest_path=path)


def test_manifest_cannot_omit_analyzer_from_critical_inventory(tmp_path: Path) -> None:
    root = _copy_static_surface(tmp_path / "repo")
    authority = AUDIT.load_static_authority(root)
    manifest = _manifest_for(root, authority)
    manifest["files"] = [
        row
        for row in manifest["files"]
        if row["path"] != AUDIT.ANALYZER_RELATIVE.as_posix()
    ]
    path = root / AUDIT.MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AUDIT.AuditError, match="required input"):
        AUDIT.load_static_authority(root, manifest_path=path)


def test_cli_requires_default_manifest_before_loading_tokenizer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _copy_static_surface(tmp_path / "repo")

    def forbidden_tokenizer_load():
        raise AssertionError("tokenizer loaded before manifest validation")

    monkeypatch.setattr(AUDIT, "_load_pinned_tokenizer", forbidden_tokenizer_load)
    assert (
        AUDIT.main(
            [
                "--repo-root",
                str(root),
                "--output",
                str(tmp_path / "preflight.json"),
            ]
        )
        == 2
    )


def test_runtime_authority_rejects_environment_drift() -> None:
    runtime = _runtime_authority()
    runtime["environment"]["torch_version"] = "unexpected"
    with pytest.raises(AUDIT.AuditError, match="environment.torch_version"):
        AUDIT._validate_runtime_authority(runtime)


def test_model_artifact_receipt_is_path_independent(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for root in (first, second):
        (root / "nested").mkdir(parents=True)
        (root / "config.json").write_bytes(b"config")
        (root / "nested" / "weights.bin").write_bytes(b"weights")
    left = AUDIT._model_artifact_receipt(first)
    right = AUDIT._model_artifact_receipt(second)
    assert left == right
    assert left["file_count"] == 2
    assert left["total_bytes"] == len(b"configweights")


def test_audit_receipt_publication_is_atomic_and_no_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "preflight.json"
    AUDIT.atomic_no_overwrite(path, {"status": "passed", "value": 1})
    original = path.read_bytes()
    with pytest.raises(AUDIT.AuditError, match="Refusing to overwrite"):
        AUDIT.atomic_no_overwrite(path, {"status": "failed", "value": 2})
    assert path.read_bytes() == original
    assert json.loads(original)["status"] == "passed"


def test_audit_source_has_no_language_model_loader_or_forward() -> None:
    source = AUDIT_PATH.read_text(encoding="utf-8")
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert "create_backend" not in source
    assert ".forward(" not in source
    assert "mlx_lm" not in source


def test_launcher_order_matches_frozen_config_role_order() -> None:
    expected = tuple(
        AUDIT.CONFIG_PATHS[(scope, family)].as_posix()
        for scope in AUDIT.SCOPE_ORDER
        for family in AUDIT.FAMILY_ORDER
    )
    assert LAUNCHER.CONFIG_ORDER == expected
    assert LAUNCHER.RUN_NAMES == tuple(
        f"e2-llama32-3b-mps-{scope}-{family}-transport-v1"
        for scope in AUDIT.SCOPE_ORDER
        for family in AUDIT.FAMILY_ORDER
    )
    assert all(
        AUDIT._read_yaml(ROOT / relative, "frozen config")["run"]["resume"] is False
        for relative in AUDIT.CONFIG_PATHS.values()
    )


def test_launcher_rejects_invalid_preflight_before_git_or_processes(
    tmp_path: Path,
) -> None:
    preflight = tmp_path / LAUNCHER.PREFLIGHT_RELATIVE
    preflight.parent.mkdir(parents=True, exist_ok=True)
    preflight.write_text(
        json.dumps(
            {
                "protocol_id": AUDIT.PROTOCOL_ID,
                "status": "failed",
                "model_forward_count": 0,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(LAUNCHER.ExecutionError, match="preflight did not pass"):
        LAUNCHER.execute(
            root=tmp_path,
            preflight_path=preflight,
            receipt_path=tmp_path / LAUNCHER.EXECUTION_RECEIPT_RELATIVE,
            python="python3",
        )


def test_launcher_binds_preflight_to_current_manifest_before_git(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest_path = tmp_path / LAUNCHER.MANIFEST_RELATIVE
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("{}\n", encoding="utf-8")
    actual_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    preflight_path = tmp_path / "preflight.json"
    preflight_path.write_text(
        json.dumps(_launcher_preflight(actual_sha256)),
        encoding="utf-8",
    )
    assert LAUNCHER._validate_preflight(tmp_path, preflight_path)["status"] == "passed"

    drifted = _launcher_preflight("0" * 64)
    preflight_path.write_text(json.dumps(drifted), encoding="utf-8")

    def forbidden_git(*_args, **_kwargs):
        raise AssertionError("git invoked before preflight binding passed")

    monkeypatch.setattr(LAUNCHER, "_git", forbidden_git)
    with pytest.raises(LAUNCHER.ExecutionError, match="SHA-256 differs"):
        LAUNCHER.execute(
            root=tmp_path,
            preflight_path=preflight_path,
            receipt_path=tmp_path / LAUNCHER.EXECUTION_RECEIPT_RELATIVE,
            python="python3",
        )


def test_launcher_receipt_publication_is_atomic_and_no_overwrite(
    tmp_path: Path,
) -> None:
    path = tmp_path / "execution.json"
    LAUNCHER._atomic_no_overwrite(path, {"status": "complete"})
    original = path.read_bytes()
    with pytest.raises(LAUNCHER.ExecutionError, match="Refusing to overwrite"):
        LAUNCHER._atomic_no_overwrite(path, {"status": "replacement"})
    assert path.read_bytes() == original


def test_launcher_rejects_existing_run_or_log_namespace(tmp_path: Path) -> None:
    existing_run = tmp_path / "runs" / f"{LAUNCHER.RUN_NAMES[3]}--old-seal"
    existing_run.mkdir(parents=True)
    with pytest.raises(LAUNCHER.ExecutionError, match="destination already exists"):
        LAUNCHER._require_empty_run_namespaces(tmp_path)

    existing_run.rmdir()
    log_dir = tmp_path / LAUNCHER.LAUNCHER_LOG_RELATIVE
    log_dir.mkdir(parents=True)
    with pytest.raises(LAUNCHER.ExecutionError, match="log namespace already exists"):
        LAUNCHER._require_empty_run_namespaces(tmp_path)


def test_launcher_allows_only_receipt_commit_after_audited_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    audited = "a" * 40
    head = "b" * 40
    preflight = {"audited_commit": audited}

    def fake_git(_root: Path, *args: str) -> str:
        values = {
            ("status", "--porcelain"): "",
            ("branch", "--show-current"): "main",
            ("rev-parse", "HEAD"): head,
            ("rev-parse", "origin/main"): head,
            ("diff", "--name-only", f"{audited}..{head}"): (
                f"{LAUNCHER.PREFLIGHT_RELATIVE.as_posix()}\nREADME.md"
            ),
        }
        return values[args]

    monkeypatch.setattr(LAUNCHER, "_git", fake_git)
    monkeypatch.setattr(LAUNCHER, "_git_is_ancestor", lambda *_args: True)
    with pytest.raises(LAUNCHER.ExecutionError, match="Only the frozen preflight"):
        LAUNCHER._validate_git_freeze(tmp_path, preflight)


def test_launcher_stops_at_first_failed_cell_without_receipt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    preflight, receipt = _prepare_launcher_surface(tmp_path)
    calls: list[list[str]] = []

    class Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    def fake_run(command: list[str], **_kwargs) -> Result:
        assert (tmp_path / LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE).is_file()
        calls.append(command)
        return Result(1 if len(calls) == 2 else 0)

    monkeypatch.setattr(LAUNCHER, "_git", _frozen_git)
    monkeypatch.setattr(LAUNCHER, "_git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(LAUNCHER.subprocess, "run", fake_run)
    with pytest.raises(LAUNCHER.ExecutionError, match="failed at"):
        LAUNCHER.execute(
            root=tmp_path,
            preflight_path=preflight,
            receipt_path=receipt,
            python="python3",
        )
    assert len(calls) == 2
    assert calls[0][-1].endswith(LAUNCHER.CONFIG_ORDER[0])
    assert calls[1][-1].endswith(LAUNCHER.CONFIG_ORDER[1])
    assert receipt.exists() is False
    assert (tmp_path / LAUNCHER.LAUNCHER_LOG_RELATIVE).is_dir()
    attempt = json.loads(
        (tmp_path / LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE).read_text(
            encoding="utf-8"
        )
    )
    failed = json.loads(
        (tmp_path / LAUNCHER.FAILED_EXECUTION_RECEIPT_RELATIVE).read_text(
            encoding="utf-8"
        )
    )
    assert attempt["model_process_count_at_publication"] == 0
    assert failed["status"] == "execution_incomplete_process_failure"
    assert failed["recorded_process_count"] == 2
    assert failed["success_execution_receipt_written"] is False


def test_launcher_success_receipt_binds_attempt_start(
    tmp_path: Path,
    monkeypatch,
) -> None:
    preflight, receipt = _prepare_launcher_surface(tmp_path)
    calls: list[list[str]] = []

    class Result:
        returncode = 0

    def fake_run(command: list[str], **_kwargs) -> Result:
        assert (tmp_path / LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE).is_file()
        calls.append(command)
        return Result()

    monkeypatch.setattr(LAUNCHER, "_git", _frozen_git)
    monkeypatch.setattr(LAUNCHER, "_git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(LAUNCHER.subprocess, "run", fake_run)
    payload = LAUNCHER.execute(
        root=tmp_path,
        preflight_path=preflight,
        receipt_path=receipt,
        python="python3",
    )
    assert len(calls) == 10
    assert payload["completed_process_count"] == 10
    attempt_path = tmp_path / LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE
    assert payload["attempt_started_receipt"] == {
        "path": LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE.as_posix(),
        "sha256": hashlib.sha256(attempt_path.read_bytes()).hexdigest(),
    }
    assert receipt.is_file()
    assert (tmp_path / LAUNCHER.FAILED_EXECUTION_RECEIPT_RELATIVE).exists() is False


def test_launcher_generic_process_exception_publishes_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    preflight, receipt = _prepare_launcher_surface(tmp_path)

    def fail_run(_command: list[str], **_kwargs):
        raise OSError("simulated process launch failure")

    monkeypatch.setattr(LAUNCHER, "_git", _frozen_git)
    monkeypatch.setattr(LAUNCHER, "_git_is_ancestor", lambda *_args: True)
    monkeypatch.setattr(LAUNCHER.subprocess, "run", fail_run)
    with pytest.raises(LAUNCHER.ExecutionError, match="launcher failed"):
        LAUNCHER.execute(
            root=tmp_path,
            preflight_path=preflight,
            receipt_path=receipt,
            python="python3",
        )
    failed = json.loads(
        (tmp_path / LAUNCHER.FAILED_EXECUTION_RECEIPT_RELATIVE).read_text(
            encoding="utf-8"
        )
    )
    assert failed["status"] == "execution_incomplete_launcher_exception"
    assert failed["failure"]["error_type"] == "OSError"
    assert failed["failure"]["partial_log_bytes"] == 0
    assert failed["scientific_outcomes_inspected_by_launcher"] is False
    assert receipt.exists() is False
