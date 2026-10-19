"""Admission/provenance checks without real-model or protected-bank access."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import t22_kv_dissection_v0 as t22


def test_specification_keeps_exact_exposed_eight_and_cannot_overwrite(tmp_path):
    output = tmp_path / "specification.json"
    result = t22.prepare_canary(output)
    value = json.loads(output.read_text())
    exposed = json.loads(t22.CANARY_SPEC.read_text())
    assert value["target_tokens"] == exposed["target_tokens"]
    assert value["source_tokens"] == exposed["source_tokens"]
    assert value["donor_indices"] == exposed["donor_indices"]
    assert result["model_forwards"] == 0
    assert value["target_count"] == 8
    assert value["confirmatory_result"] is False
    assert value["status"] == "inputs_specified_acquisition_not_admitted"
    with pytest.raises(FileExistsError):
        t22.prepare_canary(output)


def test_specification_rejects_changed_or_expanded_input_pool(tmp_path, monkeypatch):
    value = json.loads(t22.CANARY_SPEC.read_text())
    value["target_tokens"][0]["raw"]["glyph"][0] += 1
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(value))
    monkeypatch.setattr(t22, "CANARY_SPEC", changed)
    with pytest.raises(ValueError, match="eight exposed"):
        t22.prepare_canary(tmp_path / "rejected.json")
    assert not (tmp_path / "rejected.json").exists()
    value["target_count"] = 195
    changed.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="counts changed"):
        t22.prepare_canary(tmp_path / "rejected.json")


def test_preflight_cannot_treat_historical_receipt_as_raw_replay(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    (tmp_path / "acquisition_receipt.json").write_bytes(t22.CANARY_RECEIPT.read_bytes())
    result = t22.preflight(historical_canary=tmp_path)
    assert result["status"] == "blocked"
    assert result["model_forwards"] == 0
    assert result["checks"]["historical_canary_arrays_supplied"] is False
    assert result["checks"]["historical_canary_integrity_matches"] is False
    assert result["historical_canary_error"] is not None


def test_preflight_rejects_finite_unbound_arrays(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    arrays = tmp_path / "chunk_0000_0008"
    arrays.mkdir()
    np.savez(arrays / "states.npz", intervention=np.zeros((8,)), neutral_reference=np.zeros((8,)))
    result = t22.preflight(historical_canary=tmp_path)
    assert result["status"] == "blocked"
    assert result["checks"]["historical_canary_arrays_supplied"] is True
    assert result["checks"]["historical_canary_integrity_matches"] is False
