from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_glyph_name_depth_trajectory_v0_result.py"
RESULTS = ROOT / "validation" / "glyph_name_depth_trajectory_v0" / "results"
T10_RESULTS = (
    ROOT
    / "artifacts"
    / "semantic_atlas_cross_model_replication_v0"
    / "analysis"
    / "model_cell_results.json"
)
RESULT_MANIFEST = (
    ROOT / "data" / "manifests" / "glyph_name_depth_trajectory_v0_results.json"
)
EXPECTED_RESULT_MANIFEST_SHA256 = (
    "57a0f67af29f34bdb7370b90f6f5a0ffe3aa3683dc41eb95d27437ab5a12bbe4"
)
SPEC = importlib.util.spec_from_file_location("validate_t17_result", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_result_manifest_binds_every_compact_artifact() -> None:
    manifest = json.loads(RESULT_MANIFEST.read_text(encoding="utf-8"))

    assert _sha256(RESULT_MANIFEST) == EXPECTED_RESULT_MANIFEST_SHA256
    assert manifest["status"] == "complete_exploratory_result_bound"
    for artifact in manifest["artifacts"].values():
        assert _sha256(ROOT / artifact["path"]) == artifact["sha256"]


def test_independent_validator_replays_t10_and_t17(tmp_path: Path) -> None:
    result = MODULE.validate(
        analysis_path=RESULTS / "analysis.json",
        curve_csv_path=RESULTS / "depth_curves.csv",
        figure_path=RESULTS / "depth_curves.svg",
        t10_model_results_path=T10_RESULTS,
        output=tmp_path / "independent_validation.json",
    )

    assert result["status"] == "independent_compact_validation_pass"
    assert result["curve_csv_rows"] == 81
    assert result["figure_model_curves"] == 9
    assert result["figure_points"] == 81
    assert result["headline_checks"] == {
        "all_nine_point_estimates_positive_from_depth_0p375": True,
        "all_nine_bootstrap_lowers_positive_at_depths": [0.5, 0.75, 0.875, 1.0],
        "all_nine_token_matched_point_estimates_positive_from_depth_0p25": True,
        "peak_depth_model_counts": {"0": 2, "0.125": 1, "0.75": 1, "0.875": 5},
        "final_paired_margin_positive_model_count": 9,
        "final_cka_contrast_positive_model_count": 4,
    }
    for replay in result["t10_final_depth_exact_replay"].values():
        assert replay["unrestricted_cell_contrasts_exact"] is True
        assert replay["tokenization_matched_cell_contrasts_exact"] is True


def test_runtime_failures_preceded_candidate_forwards() -> None:
    receipt = json.loads(
        (
            ROOT
            / "validation"
            / "glyph_name_depth_trajectory_v0"
            / "runtime_preflight_failures.json"
        ).read_text(encoding="utf-8")
    )

    assert receipt["scientific_outcome_opened_by_failures"] is False
    assert receipt["repair"]["candidate_model_forward_calls_before_repair"] == 0
    assert all(
        attempt["candidate_model_forward_calls"] == 0 for attempt in receipt["attempts"]
    )
    assert all(
        attempt["model_weights_loaded"] is False for attempt in receipt["attempts"]
    )


def test_t17_results_and_story_are_bilingual() -> None:
    for stem in (
        "GLYPH_NAME_DEPTH_TRAJECTORY_V0_RESULTS",
        "PAPER_STORY_T17_GLYPH_NAME_V0",
    ):
        assert (ROOT / "docs" / f"{stem}.md").is_file()
        assert (ROOT / "docs" / f"{stem}.ja.md").is_file()
