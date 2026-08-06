from __future__ import annotations

import runpy
from pathlib import Path

import pytest


_VALIDATOR_SCRIPT = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "validate_standard_run_artifacts.py"
    ),
    run_name="glyphprobe_standard_run_validator_test",
)
_integrity_outcome = _VALIDATOR_SCRIPT["_integrity_outcome"]


@pytest.mark.parametrize(
    ("all_pass", "expected"),
    [
        (
            True,
            {
                "status": "ready_with_caveats",
                "scientific_result": True,
                "decision": (
                    "Artifact is internally consistent and suitable for designing a "
                    "targeted causal follow-up, with the stated caveats."
                ),
            },
        ),
        (
            False,
            {
                "status": "needs_revision",
                "scientific_result": False,
                "decision": (
                    "Do not use the artifact until failed integrity checks are resolved."
                ),
            },
        ),
    ],
)
def test_integrity_outcome_keeps_status_result_and_decision_consistent(
    all_pass: bool, expected: dict[str, object]
) -> None:
    assert _integrity_outcome(all_pass) == expected
