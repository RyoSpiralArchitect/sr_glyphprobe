#!/usr/bin/env python3
"""Prepare a scoped, licensed public-release ZIP; never upload or mint a DOI.

The acquisition and saved-score replay implementations remain unchanged. The
older candidate builder is an implementation dependency, not the authority for
this release's license, metadata, current paper, or publication status.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ID = "glyphprobe_public_release_20261015"
PDF_NAME = "paper/preprint.pdf"
DOCUMENT_VALIDATION = "evidence/document_validation.public.json"
METADATA = "PUBLICATION_METADATA.json"


def dependency():
    path = Path(__file__).with_name("build_release_candidate_20261015.py")
    spec = importlib.util.spec_from_file_location("public_release_candidate_utilities", path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


b = dependency()
OMITTED = {
    "paper/RELEASE_CANDIDATE_20261015.md", "paper/RELEASE_CANDIDATE_20261015.ja.md",
    "validation/revised_preprint_20261015/document_validation.json",
    "validation/revised_preprint_20261015/document_validation_v2.json",
}
ADDED = (
    "CITATION.cff",
    "paper/scripts/build_public_release_20261015.py",
    "paper/scripts/validate_public_preprint_20261015.py",
    "paper/PUBLIC_RELEASE_20261015.md", "paper/PUBLIC_RELEASE_20261015.ja.md",
    "paper/PUBLIC_LICENSES_20261015.md", "paper/PUBLIC_LICENSES_20261015.ja.md",
    "paper/FORK_REVIEW_PUBLICATION_20261015.md", "paper/FORK_REVIEW_PUBLICATION_20261015.ja.md",
)
STATIC_FILES = tuple(sorted((set(b.STATIC_FILES) - OMITTED) | set(ADDED)))


def license_classification(name):
    if name == "LICENSE":
        return "Apache-2.0_license_text"
    if name.endswith("UNICODE_LICENSE.txt"):
        return "Unicode-3.0_notice"
    if name.startswith("historical/"):
        return "historical_mixed_assets_existing_notices_no_relicensing"
    if name.endswith((".tex", ".bib", ".pdf")):
        return "CC-BY-4.0_author_owned_paper_and_figures_third_party_exceptions_retained"
    if name.startswith(("data/", "evidence/", "validation/", "paper/generated/")) or name == METADATA:
        return "CC-BY-4.0_author_owned_public_data_third_party_exceptions_retained"
    return "Apache-2.0_existing_project_code_and_documentation"


def standalone_dependencies(root):
    names = b.tex_dependencies(root)
    for name in names:
        b.require(Path(name).name != "checklist.tex" and not name.endswith(".sty"),
                  "Workshop checklist/style cannot be a current dependency")
        if name.endswith(".tex"):
            text = b.source_bytes(root / name).decode()
            b.require(not re.search(r"\\usepackage(?:\[[^\]]*\])?\{[^}]*neurips", text, re.I),
                      "Current paper still imports workshop style")
    return names


def document_validation(data, pdf_data):
    value = b.decode(data)
    b.scan_structure(value, "document validation")
    b.require(isinstance(value, dict) and value.get("pdf_sha256") == b.digest_bytes(pdf_data),
              "Document validation does not bind this PDF")
    b.require(isinstance(value.get("status"), str) and value["status"].startswith("validated_"),
              "Document validation status is not validated")
    b.require(value.get("public_deposit", False) is False,
              "Prepublication document validation cannot assert public deposit")
    return value


def document_source_bindings(receipt, names, read_payload):
    """Bind recorded sources to actual packaged bytes, including renamed metadata."""
    sources = receipt.get("source_sha256")
    b.require(isinstance(sources, dict) and "paper/main.tex" in sources,
              "Document validation source bindings are missing")
    aliases = {"paper/PUBLICATION_METADATA_20261015.json": METADATA}
    for source, expected in sources.items():
        b.relative_name(source)
        b.require(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected),
                  "Invalid document source hash")
        name = aliases.get(source, source)
        b.require(name in names, "Validated document source is absent from payload: " + source)
        b.require(b.digest_bytes(read_payload(name)) == expected,
                  "Document source binding differs: " + source)


def publication_metadata(data):
    value = b.decode(data)
    allowed = {"title", "creators", "description", "keywords", "publication_date", "version", "doi", "doi_state",
               "resource_type", "doi_status_at_preparation", "draft_record_url", "record_url",
               "author_license_confirmation", "repository_visibility_at_preparation",
               "conference_acceptance_claimed", "new_experiments_in_publication_workflow"}
    b.require(isinstance(value, dict) and set(value) <= allowed and isinstance(value.get("title"), str)
              and value["title"].strip(), "Unexpected or missing publication metadata")
    b.scan_structure(value, "publication metadata")
    if "doi" in value:
        reserved = value.get("doi_state") == "reserved" or value.get("doi_status_at_preparation") == "reserved_not_registered"
        b.require(isinstance(value["doi"], str) and re.fullmatch(r"10\.\d{4,9}/[^\s]+", value["doi"])
                  and reserved, "Only an externally reserved DOI may be supplied")
        b.require("doi_state" not in value or value["doi_state"] == "reserved", "Contradictory DOI state")
        b.require("doi_status_at_preparation" not in value or value["doi_status_at_preparation"] == "reserved_not_registered",
                  "Contradictory DOI preparation status")
    else:
        b.require("doi_state" not in value and "doi_status_at_preparation" not in value, "DOI state without identifier")
    if "resource_type" in value:
        b.require(value["resource_type"] == "publication-preprint", "Release must remain a preprint")
    for key in ("conference_acceptance_claimed", "new_experiments_in_publication_workflow"):
        b.require(key not in value or value[key] is False, "Unsupported publication metadata claim")
    if "repository_visibility_at_preparation" in value:
        b.require(value["repository_visibility_at_preparation"] in {
            "private_pending_history_audit_and_author_decision",
            "original_private_curated_public_repository_authorized"},
            "Unsupported repository preparation state")
    if "author_license_confirmation" in value:
        b.require(value["author_license_confirmation"] == {
            "source": "direct_author_confirmation_in_publication_workflow",
            "paper_original_figures_and_new_public_data": "CC-BY-4.0", "project_code": "Apache-2.0",
            "third_party_and_historical_materials": "retain_original_licenses_and_notices"},
            "Author-confirmed license scopes differ")
    for key, segment in (("draft_record_url", "uploads"), ("record_url", "records")):
        if key in value:
            match = re.fullmatch(r"10\.5281/zenodo\.(\d+)", value.get("doi", ""))
            b.require(match is not None and value[key] == "https://zenodo.org/" + segment + "/" + match.group(1),
                      "Zenodo URL does not match reserved DOI")
    return value


def collect(root, pdf, specification, run_directory, expected_sha, *, validation=None, metadata=None):
    root = Path(root)
    names = sorted(set(STATIC_FILES) | set(standalone_dependencies(root)))
    payload = {name: b.source_bytes(root / name) for name in names}
    payload[PDF_NAME] = b.source_bytes(pdf)
    for suffix, counterpart in ((".md", ".ja.md"), (".ja.md", ".md")):
        data = b.source_bytes(root / ("paper/PUBLIC_RELEASE_20261015" + suffix))
        # Root README links target packaged paths; paper-local copies retain local links.
        data = data.replace(("(PUBLIC_RELEASE_20261015" + counterpart + ")").encode(),
                            ("(README" + counterpart + ")").encode())
        data = data.replace(b"(PUBLIC_LICENSES_20261015", b"(paper/PUBLIC_LICENSES_20261015")
        payload["README" + suffix] = data
    archive = b.source_bytes(root / b.HISTORICAL)
    b.require(b.digest_bytes(archive) == b.HISTORICAL_SHA, "Historical archive changed")
    payload["historical/glyphprobe_t19_anonymous_evidence_v4.zip"] = archive
    payload["DEPENDENCIES.json"] = b.canonical({
        "current_paper_format": "standard LaTeX article and public TeX packages; no workshop style or checklist",
        "pdf_scan_builder_dependency": "pypdf (not vendored)",
        "public_score_replay_dependencies": "Python standard library only",
        "external_model_assets_included": False,
        "historical_archive_dependency_notices": "Retained inside the unchanged nested historical archive.",
    })
    payload.update(b.portable_run(root, specification, run_directory, expected_sha))
    bindings = b.decode(payload["evidence/readout_qualification_v1/projection_binding.json"])
    for name, expected in bindings["source_sha256"].items():
        b.require(name in payload and b.digest_bytes(payload[name]) == expected,
                  "Packaged source differs from acquisition source: " + name)
    if validation is not None:
        data = b.source_bytes(validation)
        document_validation(data, payload[PDF_NAME])
        payload[DOCUMENT_VALIDATION] = data
    if metadata is not None:
        data = b.source_bytes(metadata)
        publication_metadata(data)
        payload[METADATA] = data
    return payload


def bundle(payload, output, *, author_license_confirmed=False):
    b.require(author_license_confirmed is True, "Explicit author license confirmation is required")
    output = Path(output)
    b.require(not output.exists(), "Output already exists; choose a new release path")
    b.require(PDF_NAME in payload, "Current standalone PDF is missing")
    b.require(not OMITTED & payload.keys(), "Historical candidate guide/validation cannot describe current release")
    if DOCUMENT_VALIDATION in payload:
        receipt = document_validation(payload[DOCUMENT_VALIDATION], payload[PDF_NAME])
        document_source_bindings(receipt, payload, payload.__getitem__)
    metadata = publication_metadata(payload[METADATA]) if METADATA in payload else {}
    entries = [{"path": name, "bytes": len(data), "sha256": b.digest_bytes(data),
                "license_classification": license_classification(name), "privacy_check": b.scan_payload(name, data)}
               for name, data in sorted(payload.items())]
    manifest = {
        "schema_version": 1, "artifact_id": ARTIFACT_ID, "status": "prepared_public_release",
        "public_deposit": False, "doi_action_performed_by_builder": False,
        "doi_reserved": "doi" in metadata, "doi_registered": False, "doi": metadata.get("doi"),
        "externally_supplied_reserved_doi": metadata.get("doi"),
        "metadata_authority": "Operator-supplied; no remote verification or publication by this builder.",
        "paper_license_confirmed": True, "public_data_license_confirmed": True,
        "license_scope": "Own paper, figures and new public data: CC-BY-4.0; project code/docs: Apache-2.0; third-party and historical notices unchanged.",
        "license_guide": "paper/PUBLIC_LICENSES_20261015.md",
        "current_pdf": PDF_NAME, "document_validation_included": DOCUMENT_VALIDATION in payload,
        "archive_timestamp_is_reproducibility_constant_not_event_time": True,
        "reproducibility_timestamp_utc": "2026-10-15T00:00:00Z", "payload_files": len(entries), "files": entries,
        "scientific_claim": "Packaging integrity and saved-score replay are separate from scientific validity.",
        "human_evidence_boundary": "Author-tryout aggregates only; no private answers, assignments, notes, or item-level human replay.",
        "historical_boundary": "Unchanged September mixed-license archive is historical, not the current paper or a newly re-audited bank.",
        "git_visibility": "Not changed by this builder; no public repository URL is assumed.",
    }
    manifest_data = b.canonical(manifest)
    hashes = {name: b.digest_bytes(data) for name, data in payload.items()}
    hashes["ARTIFACT_MANIFEST.json"] = b.digest_bytes(manifest_data)
    sums = "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes)).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        with zipfile.ZipFile(handle, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted({**payload, "ARTIFACT_MANIFEST.json": manifest_data, "SHA256SUMS": sums}.items()):
                info = zipfile.ZipInfo(ARTIFACT_ID + "/" + name, date_time=b.FIXED_TIME)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data, compresslevel=9)
    return {"status": manifest["status"], "archive_bytes": output.stat().st_size,
            "archive_sha256": b.sha(output), "payload_files": len(entries), "published": False, "doi_action": False}


def verify_directory(directory):
    directory = Path(directory).resolve()
    manifest = b.read(directory / "ARTIFACT_MANIFEST.json")
    b.require(manifest.get("artifact_id") == ARTIFACT_ID and manifest.get("status") == "prepared_public_release"
              and manifest.get("public_deposit") is False, "Unexpected public-release manifest")
    b.require(manifest.get("paper_license_confirmed") is True and manifest.get("public_data_license_confirmed") is True,
              "Author license confirmation absent")
    b.require(manifest.get("payload_files") == len(manifest["files"]), "Manifest file count differs")
    for row in manifest["files"]:
        b.require(row["license_classification"] == license_classification(row["path"]), "License classification differs")
    names = {row["path"] for row in manifest["files"]}
    b.require(not OMITTED & names and PDF_NAME in names, "Current release contains candidate-era descriptors")
    b.require(manifest.get("document_validation_included") == (DOCUMENT_VALIDATION in names),
              "Document-validation manifest state differs")
    if DOCUMENT_VALIDATION in names:
        receipt = document_validation(b.source_bytes(directory / DOCUMENT_VALIDATION), b.source_bytes(directory / PDF_NAME))
        document_source_bindings(receipt, names, lambda name: b.source_bytes(directory / name))
    if METADATA in names:
        metadata = publication_metadata(b.source_bytes(directory / METADATA))
        b.require(manifest.get("externally_supplied_reserved_doi") == metadata.get("doi"), "DOI metadata differs")
    else:
        b.require(manifest.get("externally_supplied_reserved_doi") is None, "DOI lacks supplied metadata")
    b.require(manifest.get("doi") == manifest.get("externally_supplied_reserved_doi")
              and manifest.get("doi_reserved") == (manifest.get("doi") is not None)
              and manifest.get("doi_registered") is False, "Reserved/registered DOI boundary differs")
    standalone_dependencies(directory)
    result = b.verify_directory(directory)
    return {**result, "release_artifact_id": ARTIFACT_ID, "publication_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--root", type=Path, default=ROOT)
    for name in ("pdf", "specification", "run-directory", "output"):
        build.add_argument("--" + name, type=Path, required=True)
    build.add_argument("--expected-specification-sha256", required=True)
    build.add_argument("--author-license-confirmed", action="store_true")
    build.add_argument("--document-validation", type=Path)
    build.add_argument("--metadata", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        b.require(args.author_license_confirmed, "Explicit author license confirmation is required")
        payload = collect(args.root.resolve(), args.pdf, args.specification, args.run_directory,
                          args.expected_specification_sha256, validation=args.document_validation, metadata=args.metadata)
        result = bundle(payload, args.output, author_license_confirmed=args.author_license_confirmed)
    else:
        result = verify_directory(args.directory)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
