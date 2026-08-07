from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from typing import Any

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_llama32_3b_mps_emoji_transport_v2.py"
LAUNCHER_PATH = ROOT / "scripts" / "run_llama32_3b_mps_emoji_transport_v2.py"


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = _load_script("audit_llama32_3b_mps_emoji_transport_v2", AUDIT_PATH)
LAUNCHER = _load_script("run_llama32_3b_mps_emoji_transport_v2", LAUNCHER_PATH)


OUTSIDE_IDS = {
    "w01_mark_anchor": (9126, 25, 198, 15019, 25),
    "w02_bracket_continue": (58, 933, 24433, 25),
    "w03_pipe_next": (87, 765, 765, 379, 198, 5971, 25),
    "w04_token_state": (3404, 25, 198, 1423, 25),
    "w05_begin_end": (11382, 198, 198, 3812, 198, 5207, 25),
    "w06_binary_result": (15, 220, 16, 198, 2122, 25),
    "w07_symbol_following": (15440, 27, 397, 28055, 25),
    "w08_pair_q": (47, 25, 198, 48, 25),
    "w09_input_response": (2566, 7, 340, 2647, 25),
    "w10_sequence_continuation": (14405, 25, 264, 293, 198, 37239, 4090, 25),
    "w11_field_anchor": (1915, 198, 970, 28, 198, 17547, 28),
    "w12_list_next": (1256, 198, 12, 198, 12),
    "w13_left_right": (5530, 10291, 198, 9577, 25),
    "w14_codepoint_text": (2123, 2837, 25, 198, 1199, 25),
    "w15_observation_inference": (38863, 367, 198, 644, 2251, 25),
    "w16_slot_completion": (20470, 362, 28, 26, 32416, 426, 28),
}


class PreTrainedTokenizerFast:
    """Deterministic double for the exact raw and per-wrapper v2 contract."""

    is_fast = True
    vocab_size = AUDIT.TOKENIZER_BASE_VOCAB_SIZE

    def __init__(
        self,
        authority,
        *,
        bad_first_wrapper: str | None = None,
        bad_offset_wrapper: str | None = None,
        bad_outside_wrapper: str | None = None,
    ) -> None:
        self._encoded: dict[str, tuple[list[int], list[tuple[int, int]]]] = {}
        self._decoded: dict[tuple[int, ...], str] = {}
        items = [
            item
            for family in AUDIT.FAMILY_ORDER
            for item in authority.panels["full50"][family]
        ]
        for item in items:
            raw = list(AUDIT._expected_raw_ids(item["id"]))
            self._encoded[item["glyph"]] = (raw, [(0, 1)] * len(raw))
        for wrapper in authority.wrappers:
            wrapper_id = wrapper["id"]
            frozen = AUDIT.WRAPPER_CONTEXT_PROFILES[wrapper_id]
            for item in items:
                text = wrapper["template"].format(emoji=item["glyph"])
                span = list(AUDIT._expected_context_ids(item["id"], wrapper_id))
                if wrapper_id == bad_first_wrapper:
                    span[0] = 9468 if span[0] == 11410 else 11410
                positions = list(frozen["positions"][: len(span)])
                offsets = list(frozen["offsets"][: len(span)])
                if wrapper_id == bad_offset_wrapper:
                    left, right = offsets[0]
                    offsets[0] = (left + 1, right)
                outside = list(OUTSIDE_IDS[wrapper_id])
                if wrapper_id == bad_outside_wrapper:
                    outside[0] += 1
                token_count = len(outside) + len(span)
                ids: list[int | None] = [None] * token_count
                token_offsets: list[tuple[int, int] | None] = [None] * token_count
                for position, token_id, offset in zip(positions, span, offsets):
                    ids[position] = token_id
                    token_offsets[position] = offset
                outside_iter = iter(outside)
                for index in range(token_count):
                    if ids[index] is None:
                        ids[index] = next(outside_iter)
                        token_offsets[index] = (0, 0)
                normalized_ids = [int(value) for value in ids if value is not None]
                normalized_offsets = [
                    value for value in token_offsets if value is not None
                ]
                self._encoded[text] = (normalized_ids, normalized_offsets)

    def __len__(self) -> int:
        return AUDIT.TOKENIZER_LENGTH

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
        ids, offsets = self._encoded[text]
        self._decoded[tuple(ids)] = text
        return {"input_ids": list(ids), "offset_mapping": list(offsets)}

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


def _authority_without_critical_inventory() -> Any:
    panels: dict[str, dict[str, list[dict[str, Any]]]] = {
        "full50": {},
        "core35": {},
    }
    for family in AUDIT.FAMILY_ORDER:
        panels["full50"][family] = yaml.safe_load(
            (ROOT / AUDIT.FULL_PANEL_PATHS[family]).read_text(encoding="utf-8")
        )["items"]
        panels["core35"][family] = yaml.safe_load(
            (ROOT / AUDIT.CORE_PANEL_PATHS[family]).read_text(encoding="utf-8")
        )["items"]
    wrappers = [
        json.loads(line)
        for line in (ROOT / AUDIT.SOURCE_RELATIVE)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    return AUDIT.StaticAuthority(
        root=ROOT,
        panels=panels,
        wrappers=wrappers,
        report={},
    )


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
        "arms": {
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
        },
        "analysis": {
            "analysis_id": AUDIT.PROTOCOL_ID,
            "script_path": AUDIT.ANALYZER_RELATIVE.as_posix(),
            "script_sha256": hashlib.sha256(
                (root / AUDIT.ANALYZER_RELATIVE).read_bytes()
            ).hexdigest(),
            "v1_analysis_dependency": {
                "path": AUDIT.V1_ANALYZER_RELATIVE.as_posix(),
                "sha256": hashlib.sha256(
                    (root / AUDIT.V1_ANALYZER_RELATIVE).read_bytes()
                ).hexdigest(),
            },
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
        "model_artifact": {**AUDIT.EXPECTED_MODEL_ARTIFACT, "files": {}},
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
        "audit_role": LAUNCHER.EXPECTED_AUDIT_ROLE,
        "v1_preflight_outcome": "failed_before_any_model_forward",
        "v2_correction_scope": "contextual_wrapper_token_profile_only",
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
        "tokenization": {
            "rules": {
                "v1_raw_contract_preserved": True,
                "full50_exceptions_use_contextual_first_token_substitution": True,
                "wrapper_context_profiles_exactly_frozen": True,
                "wrapper_outside_tokens_identical": True,
                "wrapper_core_token_count_position_and_outside_isomorphic": True,
                "contextual_first_token_distribution": {"9468": 7, "11410": 9},
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
        json.dumps(_launcher_preflight(manifest_sha256)), encoding="utf-8"
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


def test_v2_configs_preserve_cell_and_isolate_destinations() -> None:
    assert len(AUDIT.CONFIG_PATHS) == 10
    for (scope, family), path in AUDIT.CONFIG_PATHS.items():
        actual = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
        assert actual == AUDIT._expected_config(scope, family)
        assert actual["run"]["resume"] is False
        assert actual["run"]["name"].endswith("-v2")
        assert actual["run"]["name"] not in {
            f"e2-llama32-3b-mps-{scope}-{family}-transport-v1"
        }


def test_contextual_tokenizer_contract_accepts_9468_and_11410() -> None:
    authority = _authority_without_critical_inventory()
    report = AUDIT.audit_tokenizer(PreTrainedTokenizerFast(authority), authority)
    assert report["counts"] == {
        "raw_glyphs_verified": 50,
        "full50_wrapper_profiles_verified": 800,
        "core35_wrapper_profiles_verified": 560,
        "wrapper_count": 16,
    }
    rules = report["rules"]
    assert rules["contextual_first_token_distribution"] == {"9468": 7, "11410": 9}
    assert rules["v1_raw_contract_preserved"] is True
    wrappers = {row["wrapper_id"]: row for row in report["wrappers"]}
    assert wrappers["w01_mark_anchor"]["contextual_first_token"] == 11410
    assert wrappers["w02_bracket_continue"]["contextual_first_token"] == 9468
    assert wrappers["w01_mark_anchor"]["core35_emoji_token_offsets"] == [
        [5, 7],
        [6, 7],
        [6, 7],
    ]


@pytest.mark.parametrize(
    ("keyword", "message"),
    [
        ({"bad_first_wrapper": "w01_mark_anchor"}, "Contextual emoji IDs differ"),
        ({"bad_offset_wrapper": "w03_pipe_next"}, "Contextual offsets differ"),
        ({"bad_outside_wrapper": "w02_bracket_continue"}, "outside tokens differ"),
    ],
)
def test_contextual_contract_fails_closed_on_profile_drift(keyword, message) -> None:
    authority = _authority_without_critical_inventory()
    with pytest.raises(AUDIT.AuditError, match=message):
        AUDIT.audit_tokenizer(PreTrainedTokenizerFast(authority, **keyword), authority)


def test_v2_static_authority_never_opens_protected_banks(monkeypatch) -> None:
    original = Path.open

    def guarded(path: Path, *args, **kwargs):
        if path.name in AUDIT.FORBIDDEN_TARGET_NAMES:
            raise AssertionError(f"protected content opened: {path.name}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)
    authority = AUDIT.load_static_authority(ROOT)
    assert authority.report["protected_banks"]["content_opened"] is False
    assert authority.report["config_count"] == 10


def test_manifest_requires_exact_v1_analyzer_dependency(tmp_path: Path) -> None:
    root = _copy_static_surface(tmp_path / "repo")
    authority = AUDIT.load_static_authority(root)
    manifest = _manifest_for(root, authority)
    path = root / AUDIT.MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest), encoding="utf-8")
    verified = AUDIT.load_static_authority(root, manifest_path=path)
    assert verified.report["manifest"]["present"] is True

    del manifest["analysis"]["v1_analysis_dependency"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(AUDIT.AuditError, match="v1 analysis dependency"):
        AUDIT.load_static_authority(root, manifest_path=path)


def test_cli_rejects_missing_manifest_before_loading_tokenizer(
    tmp_path: Path, monkeypatch
) -> None:
    root = _copy_static_surface(tmp_path / "repo")

    def forbidden_tokenizer_load():
        raise AssertionError("tokenizer loaded before manifest validation")

    monkeypatch.setattr(AUDIT, "_load_pinned_tokenizer", forbidden_tokenizer_load)
    assert (
        AUDIT.main(["--repo-root", str(root), "--output", str(tmp_path / "x.json")])
        == 2
    )


def test_audit_source_has_no_language_model_loader_or_forward() -> None:
    source = AUDIT_PATH.read_text(encoding="utf-8")
    assert "AutoModel" not in source
    assert "create_backend" not in source
    assert ".forward(" not in source
    assert "mlx_lm" not in source
    assert "audit_llama32_3b_mps_emoji_transport_v1.py" in source


def test_launcher_namespaces_and_order_are_v2_only() -> None:
    expected = tuple(
        AUDIT.CONFIG_PATHS[(scope, family)].as_posix()
        for scope in AUDIT.SCOPE_ORDER
        for family in AUDIT.FAMILY_ORDER
    )
    assert LAUNCHER.CONFIG_ORDER == expected
    assert all(value.endswith("-v2") for value in LAUNCHER.RUN_NAMES)
    assert "_v2/" in LAUNCHER.EXECUTION_RECEIPT_RELATIVE.as_posix()
    assert LAUNCHER.RESUME_POLICY == "forbidden_in_v2_new_versioned_freeze_required"


def test_launcher_rejects_v1_style_contextual_preflight(tmp_path: Path) -> None:
    manifest = tmp_path / LAUNCHER.MANIFEST_RELATIVE
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}\n", encoding="utf-8")
    preflight = tmp_path / "preflight.json"
    payload = _launcher_preflight(hashlib.sha256(manifest.read_bytes()).hexdigest())
    payload["audit_role"] = "model_free_static_artifact_config_and_tokenizer_preflight"
    preflight.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(LAUNCHER.ExecutionError, match="audit role differs"):
        LAUNCHER._validate_preflight(tmp_path, preflight)


def test_launcher_allows_only_v2_preflight_descendant(
    tmp_path: Path, monkeypatch
) -> None:
    audited = "a" * 40
    head = "b" * 40

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
    with pytest.raises(LAUNCHER.ExecutionError, match="Only the frozen v2 preflight"):
        LAUNCHER._validate_git_freeze(tmp_path, {"audited_commit": audited})


def test_launcher_failure_is_terminal_and_receipt_only(
    tmp_path: Path, monkeypatch
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
    assert not receipt.exists()
    failed_path = tmp_path / LAUNCHER.FAILED_EXECUTION_RECEIPT_RELATIVE
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    assert failed["status"] == "execution_incomplete_process_failure"
    assert failed["analysis_authorized"] is False
    assert failed["resume_policy"] == LAUNCHER.RESUME_POLICY

    with pytest.raises(
        LAUNCHER.ExecutionError, match="attempt-started receipt already exists"
    ):
        LAUNCHER.execute(
            root=tmp_path,
            preflight_path=preflight,
            receipt_path=receipt,
            python="python3",
        )


def test_launcher_success_binds_attempt_and_all_ten_processes(
    tmp_path: Path, monkeypatch
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
    assert payload["analysis_authorized"] is True
    assert payload["resume_policy"] == LAUNCHER.RESUME_POLICY
    attempt = tmp_path / LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE
    assert payload["attempt_started_receipt"] == {
        "path": LAUNCHER.ATTEMPT_STARTED_RECEIPT_RELATIVE.as_posix(),
        "sha256": hashlib.sha256(attempt.read_bytes()).hexdigest(),
    }
    assert receipt.is_file()
    assert not (tmp_path / LAUNCHER.FAILED_EXECUTION_RECEIPT_RELATIVE).exists()
