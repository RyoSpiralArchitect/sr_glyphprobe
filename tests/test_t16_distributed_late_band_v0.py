from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "t16_distributed_late_band_v0.py"
SPEC = importlib.util.spec_from_file_location("t16_dp", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_design_has_complete_ordered_late_band() -> None:
    result = MODULE.audit_design()
    assert result["status"] == "design_pass_zero_t16dp_model_forwards"
    assert result["model_forwards"] == 0
    assert result["target_bank_generated"] is False
    assert result["joint_sites"] == [
        {"site": site, "block_index": block}
        for block in range(24, 28)
        for site in ("attn_out", "mlp_out")
    ]


def test_design_counts_are_frozen() -> None:
    result = MODULE.audit_design()
    assert result["target_rows_planned"] == 192
    assert result["response_rows_planned"] == 15_360
    assert result["unique_minimal_or_complete_circuit_claim_authorized"] is False


def test_executor_contains_all_joint_passes() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "necessity_logits" in source
    assert "sufficiency_logits" in source
    assert "restoration_logits" in source
    assert "captured is not None and len(captured) == 8" in source

