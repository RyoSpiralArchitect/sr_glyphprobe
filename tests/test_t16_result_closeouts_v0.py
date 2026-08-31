from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_t16_closeouts_bind_compact_analysis_hashes() -> None:
    closeout_paths = (
        "validation/t16_operational_semantics_causal_subspace_v0/closeout.json",
        "validation/t16_distributed_late_band_v0/closeout.json",
        "validation/t16_utf_identity_mixing_v0/closeout.json",
    )
    for closeout_path in closeout_paths:
        closeout = _load(closeout_path)
        assert closeout["raw_arrays_copied_from_furnace"] is False

        analyses: list[dict[str, str]] = []
        if "analysis" in closeout:
            analyses.append(closeout["analysis"])
        if "behavior" in closeout:
            analyses.append(closeout["behavior"]["analysis"])
        if "causal_subspace" in closeout:
            analyses.append(closeout["causal_subspace"]["analysis"])

        assert analyses
        for analysis in analyses:
            assert _sha256(analysis["repository_path"]) == analysis["sha256"]


def test_t16_behavior_and_causal_decisions_are_not_conflated() -> None:
    behavior = _load(
        "validation/t16_operational_semantics_causal_subspace_v0/results/"
        "behavior_analysis.json"
    )
    causal = _load(
        "validation/t16_operational_semantics_causal_subspace_v0/results/"
        "causal_analysis.json"
    )
    closeout = _load(
        "validation/t16_operational_semantics_causal_subspace_v0/closeout.json"
    )

    assert behavior["all_four_cells_pass"] is True
    assert behavior["decision"] == "operational_association_and_congruence_supported"
    assert causal["causal_subspace_gate_pass"] is False
    assert causal["decision"] == "causal_subspace_gate_not_supported"
    assert closeout["unrestricted_semantic_understanding_claim_authorized"] is False
    assert closeout["unique_or_complete_circuit_claim_authorized"] is False


def test_t16_distributed_band_keeps_iut_components_separate() -> None:
    analysis = _load("validation/t16_distributed_late_band_v0/results/analysis.json")
    assert analysis["engineering_gates_pass"] is True
    assert analysis["distributed_late_band_iut_pass"] is False
    assert analysis["estimands"]["necessity"]["component_pass"] is True
    assert analysis["estimands"]["sufficiency"]["component_pass"] is False
    assert analysis["estimands"]["treatment"]["component_pass"] is False


def test_t16_utf_exact_n1_and_cross_family_pattern() -> None:
    analysis = _load("validation/t16_utf_identity_mixing_v0/results/analysis.json")
    assert analysis["decision_status"] == "exploratory_no_binary_scientific_gate"
    assert analysis["emoji_meaning_claim_authorized"] is False
    for model in analysis["results"].values():
        for cell in model.values():
            assert set(cell["per_n_medians"]["1"].values()) == {0.0}
            interval = cell["primary_summaries"]["cross_minus_within"][
                "bootstrap_95_percent_interval"
            ]
            assert interval[0] > 0.0


def test_t16_public_documents_remain_bilingual() -> None:
    stems = (
        "T16_OPERATIONAL_SEMANTICS_CAUSAL_SUBSPACE_V0_RESULTS",
        "T16_DISTRIBUTED_LATE_BAND_V0_RESULTS",
        "T16_UTF_IDENTITY_MIXING_V0_RESULTS",
        "PAPER_STORY_T16_V0",
    )
    for stem in stems:
        assert (ROOT / "docs" / f"{stem}.md").is_file()
        assert (ROOT / "docs" / f"{stem}.ja.md").is_file()


def test_t16_integrated_claim_table_resolves_evidence() -> None:
    table = _load("validation/t16_integrated_v0/claim_table.json")
    authorized = [claim for claim in table["claims"] if claim["authorized"]]
    unauthorized = [claim for claim in table["claims"] if not claim["authorized"]]
    assert len(authorized) == 4
    assert len(unauthorized) == 4
    for claim in authorized:
        assert (ROOT / claim["evidence"]).is_file()
