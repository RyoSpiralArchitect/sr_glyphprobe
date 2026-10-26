"""Synthetic, CPU-only public packaging tests; no protected or private inputs."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


p = module(ROOT / "paper/scripts/build_public_release_20261015.py", "public_release_tests")
h = module(ROOT / "tests/test_release_candidate_20261015.py", "public_release_old_helpers")
b = p.b


@pytest.fixture(scope="module")
def synthetic_payload(tmp_path_factory):
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buffer = io.BytesIO()
    writer.write(buffer)
    spec = h.synthetic_spec.__wrapped__()
    records = h.synthetic_records.__wrapped__(spec)
    folder = tmp_path_factory.mktemp("public-release-fixture") / "run"
    specification = h.write_raw_fixture(folder, spec, records)
    payload = b.portable_run(ROOT, specification, folder, b.sha(specification))
    for name in ("scripts/readout_qualification_v1.py", "scripts/validate_readout_qualification_v1.py", h.q.PREFIX,
                 "paper/scripts/build_release_candidate_20261015.py", "paper/scripts/build_public_release_20261015.py"):
        payload[name] = b.source_bytes(ROOT / name)
    payload.update({p.PDF_NAME: buffer.getvalue(), "paper/main.tex": b"\\documentclass{article}\nSynthetic paper.\n",
                    "README.md": b"Synthetic public-release fixture.\n"})
    return payload


def test_license_confirmation_is_mandatory(tmp_path, synthetic_payload):
    output = tmp_path / "missing-confirmation.zip"
    with pytest.raises(ValueError, match="license confirmation"):
        p.bundle(synthetic_payload, output)
    assert not output.exists()


def test_final_licenses_scoped_and_historical_exception():
    assert p.license_classification("paper/preprint.pdf").startswith("CC-BY-4.0")
    assert p.license_classification("evidence/new.json").startswith("CC-BY-4.0")
    assert p.license_classification("data/public.jsonl").startswith("CC-BY-4.0")
    assert p.license_classification("scripts/tool.py").startswith("Apache-2.0")
    assert "no_relicensing" in p.license_classification("historical/existing.zip")
    assert p.license_classification("paper/UNICODE_LICENSE.txt") == "Unicode-3.0_notice"
    assert not set(p.STATIC_FILES) & p.OMITTED
    assert "CITATION.cff" in p.STATIC_FILES
    assert "paper/scripts/build_release_candidate_20261015.py" in p.STATIC_FILES
    assert "paper/scripts/validate_public_preprint_20261015.py" in p.STATIC_FILES


@pytest.mark.parametrize("contents", [r"\usepackage[preprint]{neurips_2026}", r"\usepackage{foo,neurips_2026}"])
def test_current_workshop_style_rejected(tmp_path, contents):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/main.tex").write_text(contents)
    with pytest.raises(ValueError, match="workshop style"):
        p.standalone_dependencies(tmp_path)


def test_current_workshop_checklist_rejected(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/main.tex").write_text(r"\input{checklist}")
    (tmp_path / "paper/checklist.tex").write_text("Historical fixture")
    with pytest.raises(ValueError, match="checklist/style"):
        p.standalone_dependencies(tmp_path)


def test_standard_article_accepted(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/main.tex").write_text(r"\documentclass{article}\usepackage{geometry}\input{section}")
    (tmp_path / "paper/section.tex").write_text("Synthetic section")
    assert p.standalone_dependencies(tmp_path) == ["paper/main.tex", "paper/section.tex"]


@pytest.mark.parametrize("change", ["digest", "status", "published"])
def test_wrong_document_receipt_fails_before_output(tmp_path, synthetic_payload, change):
    payload = dict(synthetic_payload)
    receipt = {"status": "validated_standalone_preprint", "pdf_sha256": b.digest_bytes(payload[p.PDF_NAME]),
               "public_deposit": False}
    if change == "digest":
        receipt["pdf_sha256"] = "0" * 64
    elif change == "status":
        receipt["status"] = "unchecked"
    else:
        receipt["public_deposit"] = True
    payload[p.DOCUMENT_VALIDATION] = b.canonical(receipt)
    output = tmp_path / "wrong-receipt.zip"
    with pytest.raises(ValueError):
        p.bundle(payload, output, author_license_confirmed=True)
    assert not output.exists()


@pytest.mark.parametrize("name", sorted(p.OMITTED))
def test_candidate_receipts_and_guides_cannot_describe_current_release(tmp_path, synthetic_payload, name):
    payload = {**synthetic_payload, name: b"Historical candidate"}
    with pytest.raises(ValueError, match="candidate guide/validation"):
        p.bundle(payload, tmp_path / "bad.zip", author_license_confirmed=True)


def test_deterministic_prepared_package_and_stdlib_extracted_verifier(tmp_path, synthetic_payload):
    payload = dict(synthetic_payload)
    payload[p.DOCUMENT_VALIDATION] = b.canonical({"status": "validated_synthetic_document",
        "pdf_sha256": b.digest_bytes(payload[p.PDF_NAME]), "public_deposit": False,
        "source_sha256": {"paper/main.tex": b.digest_bytes(payload["paper/main.tex"])}})
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    result = p.bundle(payload, first, author_license_confirmed=True)
    assert result == p.bundle(payload, second, author_license_confirmed=True)
    assert result["status"] == "prepared_public_release" and not result["published"] and not result["doi_action"]
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        manifest = json.loads(archive.read(p.ARTIFACT_ID + "/ARTIFACT_MANIFEST.json"))
        assert manifest["paper_license_confirmed"] and manifest["public_data_license_confirmed"]
        assert not manifest["public_deposit"] and not manifest["doi_registered"] and not manifest["doi_reserved"]
        archive.extractall(tmp_path / "extract")
    directory = tmp_path / "extract" / p.ARTIFACT_ID
    direct = p.verify_directory(directory)
    assert direct["independent_arithmetic_validation_passed"] and direct["model_forwards"] == 0
    assert not direct["publication_verified"]
    # -S removes site packages: extracted replay has a genuine stdlib-only path.
    command = [sys.executable, "-S", "-B", "paper/scripts/build_public_release_20261015.py", "verify", "."]
    fresh = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=True)
    assert json.loads(fresh.stdout) == direct
    assert not list(directory.rglob("__pycache__"))
    with pytest.raises(ValueError, match="already exists"):
        p.bundle(payload, first, author_license_confirmed=True)


def test_reserved_doi_metadata_does_not_claim_registration(tmp_path, synthetic_payload):
    metadata = {"title": "Synthetic paper", "doi": "10.5281/zenodo.123456", "doi_state": "reserved",
                "creators": [{"name": "Example Author"}], "version": "1.0.0", "publication_date": "2026-10-15"}
    payload = {**synthetic_payload, p.METADATA: b.canonical(metadata)}
    archive_path = tmp_path / "reserved.zip"
    p.bundle(payload, archive_path, author_license_confirmed=True)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(tmp_path / "extract")
        manifest = json.loads(archive.read(p.ARTIFACT_ID + "/ARTIFACT_MANIFEST.json"))
    assert manifest["doi"] == metadata["doi"] and manifest["doi_reserved"]
    assert not manifest["doi_registered"] and not manifest["public_deposit"]
    assert not p.verify_directory(tmp_path / "extract" / p.ARTIFACT_ID)["publication_verified"]


@pytest.mark.parametrize("metadata", [
    {"title": "Synthetic", "doi": "invented", "doi_state": "reserved"},
    {"title": "Synthetic", "doi": "10.5281/zenodo.123456", "doi_state": "published"},
    {"title": "Synthetic", "doi_state": "reserved"},
    {"title": "Synthetic", "password": "not-allowed"},
])
def test_unverified_or_extra_metadata_rejected(metadata):
    with pytest.raises(ValueError):
        p.publication_metadata(b.canonical(metadata))


def test_public_source_and_guides_pass_privacy_scan():
    for name in p.ADDED:
        if name == "CITATION.cff":  # Parent prepares separately; build requires it.
            continue
        b.scan_payload(name, b.source_bytes(ROOT / name))


def test_author_confirmed_metadata_shape_and_url_binding():
    metadata = {
        "title": "Synthetic paper", "resource_type": "publication-preprint",
        "creators": [{"family_name": "Example", "given_name": "Author"}],
        "version": "1.0.0", "publication_date": "2026-10-15", "doi": "10.5281/zenodo.123456",
        "doi_status_at_preparation": "reserved_not_registered",
        "draft_record_url": "https://zenodo.org/uploads/123456", "record_url": "https://zenodo.org/records/123456",
        "author_license_confirmation": {
            "source": "direct_author_confirmation_in_publication_workflow",
            "paper_original_figures_and_new_public_data": "CC-BY-4.0", "project_code": "Apache-2.0",
            "third_party_and_historical_materials": "retain_original_licenses_and_notices"},
        "repository_visibility_at_preparation": "private_pending_history_audit_and_author_decision",
        "conference_acceptance_claimed": False, "new_experiments_in_publication_workflow": False,
    }
    assert p.publication_metadata(b.canonical(metadata)) == metadata
    metadata["record_url"] = "https://zenodo.org/records/999999"
    with pytest.raises(ValueError, match="URL does not match"):
        p.publication_metadata(b.canonical(metadata))


@pytest.mark.parametrize("source", ["paper/main.tex", "paper/PUBLICATION_METADATA_20261015.json", "CITATION.cff"])
def test_changed_document_source_rejected_before_archive(tmp_path, synthetic_payload, source):
    payload = {**synthetic_payload, p.METADATA: b.canonical({"title": "Synthetic paper"}),
               "CITATION.cff": b"cff-version: 1.2.0\n"}
    aliases = {"paper/PUBLICATION_METADATA_20261015.json": p.METADATA}
    bindings = {"paper/main.tex": b.digest_bytes(payload["paper/main.tex"]),
                source: b.digest_bytes(payload[aliases.get(source, source)])}
    payload[p.DOCUMENT_VALIDATION] = b.canonical({"status": "validated_synthetic_document",
        "pdf_sha256": b.digest_bytes(payload[p.PDF_NAME]), "source_sha256": bindings})
    payload[aliases.get(source, source)] += b"\n"
    output = tmp_path / "mismatch.zip"
    with pytest.raises(ValueError, match="Document source binding differs"):
        p.bundle(payload, output, author_license_confirmed=True)
    assert not output.exists()


def test_renamed_metadata_binding_and_extracted_mismatch(tmp_path, synthetic_payload):
    payload = {**synthetic_payload, p.METADATA: b.canonical({"title": "Synthetic paper"})}
    bindings = {"paper/main.tex": b.digest_bytes(payload["paper/main.tex"]),
                "paper/PUBLICATION_METADATA_20261015.json": b.digest_bytes(payload[p.METADATA])}
    payload[p.DOCUMENT_VALIDATION] = b.canonical({"status": "validated_synthetic_document",
        "pdf_sha256": b.digest_bytes(payload[p.PDF_NAME]), "source_sha256": bindings})
    output = tmp_path / "bindings.zip"
    p.bundle(payload, output, author_license_confirmed=True)
    with zipfile.ZipFile(output) as archive:
        archive.extractall(tmp_path / "extract")
    directory = tmp_path / "extract" / p.ARTIFACT_ID
    assert p.verify_directory(directory)["independent_arithmetic_validation_passed"]
    (directory / p.METADATA).write_bytes(payload[p.METADATA] + b"\n")
    with pytest.raises(ValueError, match="Document source binding differs"):
        p.verify_directory(directory)


@pytest.mark.parametrize("sources", [None, {}, {"paper/main.tex": "0" * 64, "paper/absent.tex": "1" * 64}])
def test_absent_document_source_bindings_fail_closed(sources):
    receipt = {"source_sha256": sources}
    with pytest.raises(ValueError):
        p.document_source_bindings(receipt, {"paper/main.tex"}, lambda _: b"Synthetic source")


@pytest.mark.parametrize("state", ["private_pending_history_audit_and_author_decision",
                                  "original_private_curated_public_repository_authorized"])
def test_explicit_repository_preparation_states(state):
    value = {"title": "Synthetic paper", "repository_visibility_at_preparation": state}
    assert p.publication_metadata(b.canonical(value)) == value


def test_repository_publication_cannot_be_inferred():
    with pytest.raises(ValueError, match="Unsupported repository"):
        p.publication_metadata(b.canonical({"title": "Synthetic paper", "repository_visibility_at_preparation": "public"}))

