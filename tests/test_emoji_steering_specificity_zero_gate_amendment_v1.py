from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "scripts" / "audit_emoji_steering_specificity_zero_gate_amendment_v1.py"
)
SPEC = importlib.util.spec_from_file_location(
    "audit_emoji_steering_specificity_zero_gate_amendment_v1", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _fixture_root(tmp_path: Path) -> Path:
    copied = {
        MODULE.CONFIG_PATH,
        MODULE.SOURCE_FREEZE_PATH,
        MODULE.CLOSEOUT_PATH,
        MODULE.FAILURE_RECEIPT_PATH,
    }
    for relative in MODULE.FROZEN_INPUTS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative in copied:
            shutil.copy2(ROOT / relative, destination)
        else:
            destination.write_text(f"fixture:{relative}\n", encoding="utf-8")
    return tmp_path


def test_algorithmic_bound_is_exactly_eight_float32_epsilons() -> None:
    expected = float(8 * np.finfo(np.float32).eps)
    assert MODULE.MAXIMUM_ABSOLUTE_JS == expected
    assert expected == 9.5367431640625e-07


def test_repository_design_audit_is_value_blind_and_nonadaptive() -> None:
    result = MODULE.audit_design()
    assert result["status"] == "design_audit_pass_post_failure_nonadaptive"
    assert result["failure_field_known"] == "js_divergence"
    assert result["exact_live_js_residual_magnitude_inspected"] is False
    assert result["nonzero_scientific_values_opened"] is False
    assert result["analysis_output_written_by_failed_v0_attempt"] is False
    assert result["scientific_values_parsed_by_auditor"] is False


def test_failure_receipt_retains_failed_gate_without_magnitude() -> None:
    receipt = json.loads(
        (ROOT / MODULE.FAILURE_RECEIPT_PATH).read_text(encoding="utf-8")
    )
    assert set(receipt) == MODULE.FAILURE_RECEIPT_KEYS
    assert receipt["failure_field"] == "js_divergence"
    assert receipt["exact_failed_value_recorded"] is False
    assert receipt["nonzero_scientific_values_opened"] is False
    assert receipt["analysis_output_written"] is False
    assert receipt["preserved_as_negative_procedural_result"] is True
    assert not any("magnitude" in key or "observed_value" in key for key in receipt)


def test_freeze_and_audit_use_the_exact_code_owned_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    output = Path("data/manifests/test-zero-gate-amendment.json")
    manifest = MODULE.freeze(output)
    assert manifest["input_roster"] == [str(path) for path in MODULE.FROZEN_INPUTS]
    assert set(manifest["inputs"]) == {str(path) for path in MODULE.FROZEN_INPUTS}
    assert manifest["exact_live_js_residual_magnitude_inspected"] is False
    assert manifest["nonzero_scientific_values_opened"] is False

    audit = MODULE.audit_freeze(output)
    assert audit == {
        "status": "amendment_freeze_audit_pass",
        "amendment_id": MODULE.AMENDMENT_ID,
        "input_count": len(MODULE.FROZEN_INPUTS),
        "scientific_values_parsed_by_auditor": False,
    }


def test_freeze_refuses_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    output = Path("data/manifests/test-zero-gate-amendment.json")
    MODULE.freeze(output)
    with pytest.raises(MODULE.AmendmentBoundaryError, match="Refusing to overwrite"):
        MODULE.freeze(output)


def test_freeze_preserves_destination_that_appears_during_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    output = Path("data/manifests/test-zero-gate-amendment.json")
    destination = root / output
    original_link = MODULE.os.link

    def competing_link(source: Path, target: Path) -> None:
        Path(target).write_text("competing manifest\n", encoding="utf-8")
        original_link(source, target)

    monkeypatch.setattr(MODULE.os, "link", competing_link)
    with pytest.raises(MODULE.AmendmentBoundaryError, match="Refusing to overwrite"):
        MODULE.freeze(output)

    assert destination.read_text(encoding="utf-8") == "competing manifest\n"
    assert not list(destination.parent.glob(f".{destination.name}.stage-*"))


def test_audit_detects_a_changed_frozen_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    output = Path("data/manifests/test-zero-gate-amendment.json")
    MODULE.freeze(output)
    changed = root / "scripts" / "analyze_emoji_steering_specificity_geometry_v1.py"
    changed.write_text("changed\n", encoding="utf-8")
    with pytest.raises(MODULE.AmendmentBoundaryError, match="changed"):
        MODULE.audit_freeze(output)


def test_audit_rejects_manifest_roster_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    output = Path("data/manifests/test-zero-gate-amendment.json")
    MODULE.freeze(output)
    manifest_path = root / output
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    removed = str(MODULE.FROZEN_INPUTS[-1])
    manifest["input_roster"].remove(removed)
    manifest["inputs"].pop(removed)
    _write_json(manifest_path, manifest)
    with pytest.raises(MODULE.AmendmentBoundaryError, match="roster"):
        MODULE.audit_freeze(output)


def test_design_rejects_an_observed_residual_selected_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    monkeypatch.setattr(MODULE, "_root", lambda: root)
    config_path = root / MODULE.CONFIG_PATH
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["nonadaptive_basis"]["observed_residual_magnitude_used_to_choose_bound"] = (
        True
    )
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    with pytest.raises(MODULE.AmendmentBoundaryError, match="Observed JS residual"):
        MODULE.audit_design()
