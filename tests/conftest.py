"""Explicit unavailable-archive boundaries for the public integration.

Historical tests and scientific source pins are unchanged.  These exact tests
need intentionally unpublished operational receipts or intermediate PDFs;
absence is a reported skip, never a successful scientific validation.  An
existing artifact is not inspected here: its original test must validate it.
Synthetic tests outside this exact map continue to run normally.
"""
from pathlib import Path

import pytest


_OUTPUT_SPEC = "validation/contextual_emoji_output_pilot_v0/specification.json"
_WORD_SPEC = "validation/contextual_emoji_word_control_v0/specification.json"
_RUNTIME = "validation/contextual_emoji_output_pilot_v0/full288/runtime.json"
_WORDING = "validation/contextual_emoji_candidate_wording_v0/runtime_fix"
_PREFIX = "validation/contextual_emoji_prefix_consistency_v0/portable_preflight"
_DESIGN_ARCHIVE = (_OUTPUT_SPEC, _WORD_SPEC, _RUNTIME)
_REPLAY_ARCHIVE = _DESIGN_ARCHIVE + (
    f"{_WORDING}/specification.json",
    f"{_WORDING}/shared_trial/occupancy_checks.json",
    f"{_WORDING}/shared_trial/placement.json",
    f"{_WORDING}/shared_trial/run_completed.json",
    f"{_WORDING}/shared_trial/run_started.json",
    f"{_WORDING}/shared_trial/runtime.json",
)
_PREFIX_ARCHIVE = _REPLAY_ARCHIVE + (
    f"{_PREFIX}/specification.json",
    f"{_PREFIX}/independent_validation.json",
    f"{_PREFIX}/run56/runtime.json",
    f"{_PREFIX}/run56/implementation_sources.json",
    f"{_PREFIX}/run56/run_completed.json",
    f"{_PREFIX}/run56/run_started.json",
    f"{_PREFIX}/run56/occupancy_checks.json",
)

# Only this class has an archive-dependent setUp for every test.  Although it
# fabricates new score rows, its fixture first verifies historical provenance.
ARCHIVE_CLASS_REQUIREMENTS = {
    "tests/test_analyze_contextual_emoji_matched_shape_v1.py::MatchedShapeCheckerTests": _PREFIX_ARCHIVE,
}

# Function-level entries deliberately leave neighbouring synthetic tests active.
# Parameter variants share the exact function's requirements; no prefix/glob
# match and no module-wide skip is permitted.
ARCHIVE_TEST_REQUIREMENTS = {
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_fixed_grid_preserves_all_blocks_and_original_orientation": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_synthetic_interaction_and_candidate_stability": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_missing_cell_preserves_denominator_and_nulls_full_estimate": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_independent_analysis_rejects_mutations": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_parity_gate_and_full_missingness_receipts": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_new_data_cannot_be_admitted_without_parity": _DESIGN_ARCHIVE,
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_complete_runtime_comparison_uses_saved_json_key_types": (_RUNTIME,),
    "tests/test_contextual_emoji_matched_shape_v1.py::InventoryTests::test_exact_real_pinned_inventory_and_prior_panel": _PREFIX_ARCHIVE,
    "tests/test_contextual_emoji_matched_shape_v1.py::InventoryTests::test_source_and_spec_overwrite_refused": _PREFIX_ARCHIVE,
    "tests/test_contextual_emoji_prefix_consistency_v0.py::PreparationTests::test_exact_pinned_real_selection_without_model_or_tokenizer": _REPLAY_ARCHIVE,
    "tests/test_contextual_emoji_prefix_consistency_v0.py::PreparationTests::test_portable_payload_hash_and_native_observation_are_separate": _REPLAY_ARCHIVE,
    "tests/test_contextual_emoji_prefix_consistency_v0.py::ExecutionTests::test_mock_run_receipts_bind_all112_forward_boundaries": _REPLAY_ARCHIVE,
    "tests/test_contextual_emoji_prefix_consistency_v0.py::ExecutionTests::test_run_refusal_writes_complete_notrun_receipts_without_loading": _REPLAY_ARCHIVE,
    "tests/test_contextual_emoji_two_track_v1.py::RunnerTests::test_historical_geometry_and_sentinels": (
        "validation/contextual_emoji_matched_shape_v1/specification.json",
    ),
    "tests/test_contextual_emoji_word_control_v0.py::test_runtime_identity_compares_actual_baseline_before_forward": (_RUNTIME,),
    "tests/test_revised_preprint_20261015.py::test_all_preserved_pins_are_actual_file_hashes": (
        "output/pdf/glyphprobe_post_review_20261007.pdf",
        "output/pdf/glyphprobe_working_reassessment_20261010.pdf",
    ),
    "tests/test_working_reassessment_20261010.py::test_raw_model_polarities_recomputed_without_private_join": (
        "validation/contextual_emoji_two_track_v1/specification.json",
    ),
    "tests/test_working_reassessment_20261010.py::test_historical_pdf_preserved_and_successor_scoped": (
        "output/pdf/glyphprobe_post_review_20261007.pdf",
    ),
}


def archive_requirements(nodeid):
    """Return only explicit requirements, ignoring a pytest parameter suffix."""
    name = nodeid.split("[", 1)[0]
    if name in ARCHIVE_TEST_REQUIREMENTS:
        return ARCHIVE_TEST_REQUIREMENTS[name]
    parts = name.split("::")
    if len(parts) == 3:
        return ARCHIVE_CLASS_REQUIREMENTS.get("::".join(parts[:2]), ())
    return ()


def missing_archive_paths(nodeid, root):
    """Metadata-only check: never open an archive or import its runner."""
    return tuple(path for path in archive_requirements(nodeid)
                 if not (Path(root) / path).is_file())


def pytest_addoption(parser):
    parser.addoption(
        "--require-archive-evidence", action="store_true", default=False,
        help="Run archive-dependent tests without public-scope skips; missing evidence fails normally.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--require-archive-evidence"):
        return
    for item in items:
        missing = missing_archive_paths(item.nodeid, config.rootpath)
        if missing:
            reason = (
                "Public integration: expected unpublished archive artifact(s) unavailable: "
                + ", ".join(missing)
                + ". This is not a validation pass; restore the complete archive to run the original test."
            )
            item.add_marker(pytest.mark.skip(reason=reason))
