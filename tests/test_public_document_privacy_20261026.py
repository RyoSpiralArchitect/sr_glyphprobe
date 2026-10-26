"""Synthetic privacy checks; no real private records or PDF inputs are read."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["validate_revised_preprint_20261015", "validate_working_reassessment_20261010"])
def document_check(request):
    path = ROOT / "paper/scripts" / (request.param + ".py")
    spec = importlib.util.spec_from_file_location(request.param + "_privacy_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("private_text", [
    "/Users/example/synthetic", "/home/example/synthetic", "/Volumes/example/synthetic",
    "author-999", "pkg_" + "b" * 32, "pkg_" + "Q7" * 16,
])
def test_private_shapes_are_rejected(document_check, private_text):
    with pytest.raises((AssertionError, ValueError), match="Private identifier/path"):
        document_check.check_private_text("Synthetic text " + private_text + ".")


@pytest.mark.parametrize("public_text", [
    "Author-side measurement audit; DOI 10.5281/zenodo.23376699.",
    "The author-only tryout is described through aggregate counts.",
    "Package integrity is separate from semantic qualification.",
])
def test_ordinary_public_prose_is_allowed(document_check, public_text):
    document_check.check_private_text(public_text)
