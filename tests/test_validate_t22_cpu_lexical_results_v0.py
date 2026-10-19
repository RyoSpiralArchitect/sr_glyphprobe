"""Exercise relocation against archived evidence without model acquisition."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location(
    "independent_t22_audit", ROOT / "scripts/validate_t22_cpu_lexical_results_v0.py")
audit_module = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(audit_module)
SPEC_SHA = "e6da21348028f8fffe6bda879336beeffcbf515e1862271dada2db6f4bf56067"


@pytest.fixture
def relocated(tmp_path, monkeypatch):
    lexical = ROOT / "validation/t22_cpu_lexical_canary_v0"
    acquisition, analysis = tmp_path / "aliases", tmp_path / "analysis"
    parent, validation = tmp_path / "parent", tmp_path / "synthetic.json"
    shutil.copytree(lexical / "acquisition", acquisition)
    shutil.copytree(lexical / "results", analysis)
    shutil.copytree(ROOT / "validation/t22_cpu_engineering_v0/canary", parent)
    shutil.copy2(lexical / "synthetic_validation.json", validation)
    spec = json.loads((acquisition / "specification.json").read_text())
    for name in spec["source_sha256"]:
        dest = tmp_path / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
    real_sha = audit_module.sha

    def relocated_sha(path):
        # Catch any accidental fallback to the original absolute workspace.
        if Path(path).resolve() != Path(audit_module.__file__).resolve():
            assert Path(path).resolve().is_relative_to(tmp_path)
        return real_sha(path)

    monkeypatch.setattr(audit_module, "sha", relocated_sha)
    return tmp_path, acquisition, analysis, parent, validation


def replay(paths):
    repo, acquisition, analysis, parent, validation = paths
    return audit_module.audit(repo, acquisition, analysis, SPEC_SHA,
                              parent_run=parent, validation_receipt=validation)


def test_relocated_archive_replays_without_original_workspace(relocated):
    result = replay(relocated)
    assert result["status"] == "pass"
    assert result["cosine_values_recomputed"] == 66048
    assert result["max_independent_cosine_error"] < 1e-12
    assert result["audit_model_forwards"] == 0


@pytest.mark.parametrize("target,error", [
    ("validation", "Validation receipt changed"),
    ("parent", "Unexpected engineering parent"),
    ("array", "Parent readouts changed"),
])
def test_relocation_does_not_relax_pinned_hashes(relocated, target, error):
    _, _, _, parent, validation = relocated
    path = {"validation": validation, "parent": parent / "acquisition_receipt.json",
            "array": parent / "item_0000/states.npz"}[target]
    with path.open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match=error):
        replay(relocated)
