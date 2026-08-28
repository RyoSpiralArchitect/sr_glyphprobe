from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_mistral7b_semantic_atlas_token_structure_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "analyze_mistral7b_semantic_atlas_token_structure_v0", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_token_only_strata_are_complete_and_fixed() -> None:
    selection = json.loads(
        (ROOT / MODULE.canonical.batch1.v0.SELECTION_PATH).read_text(encoding="utf-8")
    )
    acquired = MODULE.canonical.batch1.v0._selection_rows(
        selection, acquired_only=True
    )
    strata = MODULE._strata(acquired)
    assert {name: len(indices) for name, indices in strata.items()} == (
        MODULE.EXPECTED_STRATUM_COUNTS
    )
    assert MODULE.EXPECTED_PREFIX3 == (29473, 1011, 930)


def test_sensitivity_is_explicitly_post_outcome_and_nonconfirmatory() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert '"outcome_known_before_exact_sensitivity_design": True' in source
    assert '"scientific_decision_authorized": False' in source
    assert '"confirmatory_status": False' in source
    assert '"reserved_unrun_model_inputs_forwarded": 0' in source
