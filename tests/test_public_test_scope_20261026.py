"""Synthetic checks of the public test boundary; no historical data are opened."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


_SPEC = importlib.util.spec_from_file_location(
    "public_scope_checks", Path(__file__).with_name("conftest.py")
)
scope = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(scope)

RUNTIME_TEST = (
    "tests/test_contextual_emoji_word_control_v0.py::"
    "test_runtime_identity_compares_actual_baseline_before_forward"
)
PARAMETER_TEST = (
    "tests/test_contextual_emoji_candidate_wording_v0.py::"
    "test_independent_analysis_rejects_mutations"
)


def item(nodeid):
    marks = []
    return SimpleNamespace(nodeid=nodeid, add_marker=marks.append, marks=marks)


def config(root, require_archive=False):
    return SimpleNamespace(rootpath=root, getoption=lambda name: require_archive)


def test_no_module_wide_skip_or_path_escape():
    assert len(scope.ARCHIVE_CLASS_REQUIREMENTS) == 1
    assert all("::" in name for name in scope.ARCHIVE_TEST_REQUIREMENTS)
    for name in (*scope.ARCHIVE_TEST_REQUIREMENTS, *scope.ARCHIVE_CLASS_REQUIREMENTS):
        assert name.startswith("tests/") and "[" not in name
        requirements = scope.archive_requirements(name + "::test_example") if name in scope.ARCHIVE_CLASS_REQUIREMENTS else scope.archive_requirements(name)
        assert requirements
        assert len(requirements) == len(set(requirements))
        assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in requirements)


@pytest.mark.parametrize("suffix", ["[duplicate]", "[a::b[0]]", ""])
def test_parameter_suffix_matches_only_exact_test(suffix):
    assert scope.archive_requirements(PARAMETER_TEST + suffix) == scope.archive_requirements(PARAMETER_TEST)
    assert scope.archive_requirements(PARAMETER_TEST + "_new" + suffix) == ()


def test_class_match_requires_exact_class_and_test_depth():
    name = next(iter(scope.ARCHIVE_CLASS_REQUIREMENTS))
    assert scope.archive_requirements(name + "::test_synthetic")
    assert scope.archive_requirements(name + "Other::test_synthetic") == ()
    assert scope.archive_requirements(name.split("::")[0] + "::OtherTests::test_synthetic") == ()
    assert scope.archive_requirements(name + "::Nested::test_synthetic") == ()


@pytest.mark.parametrize("nodeid", [
    "tests/test_contextual_emoji_candidate_wording_v0.py::test_nonfinite_and_duplicate_json_rejected",
    "tests/test_contextual_emoji_word_control_v0.py::test_duplicate_or_extra_cells_rejected",
    "tests/test_contextual_emoji_matched_shape_v1.py::ScheduleAndExecutionTests::test_completed_gate_and_all_boundaries",
    "tests/test_contextual_emoji_prefix_consistency_v0.py::ExecutionTests::test_all56_attempted_no_extra_forward_and_exact_gates",
    "tests/test_contextual_emoji_two_track_v1.py::RunnerTests::test_contention_before_forward_preserves_missingness",
    "tests/test_revised_preprint_20261015.py::test_qualification_example_matches_prepared_input_exactly",
    "tests/test_revised_preprint_20261015.py::test_reported_new_results_match_checked_records",
    "tests/test_validate_readout_qualification_v1.py::test_any_case",
    "tests/test_t22_kv_dissection_v0.py::test_any_case",
])
def test_unmapped_synthetic_and_public_projection_tests_stay_active(tmp_path, nodeid):
    current = item(nodeid)
    scope.pytest_collection_modifyitems(config(tmp_path), [current])
    assert current.marks == []


def test_missing_archive_is_skip_with_exact_expected_path_not_pass(tmp_path):
    current = item(RUNTIME_TEST)
    scope.pytest_collection_modifyitems(config(tmp_path), [current])
    assert len(current.marks) == 1
    marker = current.marks[0]
    assert marker.name == "skip"
    reason = marker.kwargs["reason"]
    assert scope.archive_requirements(RUNTIME_TEST)[0] in reason
    assert "not a validation pass" in reason


def test_present_invalid_file_is_not_skipped_or_read(tmp_path, monkeypatch):
    path = tmp_path / scope.archive_requirements(RUNTIME_TEST)[0]
    path.parent.mkdir(parents=True)
    path.write_text("Deliberately invalid synthetic data; original test must fail.")
    def no_read(*args, **kwargs):
        raise AssertionError("Scope discovery must not read archive content")
    monkeypatch.setattr(Path, "read_text", no_read)
    monkeypatch.setattr(Path, "read_bytes", no_read)
    current = item(RUNTIME_TEST)
    scope.pytest_collection_modifyitems(config(tmp_path), [current])
    assert current.marks == []


def test_directory_does_not_satisfy_file_requirement(tmp_path):
    path = tmp_path / scope.archive_requirements(RUNTIME_TEST)[0]
    path.mkdir(parents=True)
    assert scope.missing_archive_paths(RUNTIME_TEST, tmp_path) == (str(path.relative_to(tmp_path)),)


def test_complete_fixture_restores_original_test_and_partial_reports_only_missing(tmp_path):
    required = scope.archive_requirements(PARAMETER_TEST)
    for relative in required[:-1]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic placeholder")
    assert scope.missing_archive_paths(PARAMETER_TEST, tmp_path) == required[-1:]
    final = tmp_path / required[-1]
    final.parent.mkdir(parents=True, exist_ok=True)
    final.write_text("synthetic placeholder")
    current = item(PARAMETER_TEST + "[duplicate]")
    scope.pytest_collection_modifyitems(config(tmp_path), [current])
    assert current.marks == []


def test_strict_archive_option_does_not_suppress_missing_evidence(tmp_path):
    current = item(RUNTIME_TEST)
    scope.pytest_collection_modifyitems(config(tmp_path, require_archive=True), [current])
    assert current.marks == []
