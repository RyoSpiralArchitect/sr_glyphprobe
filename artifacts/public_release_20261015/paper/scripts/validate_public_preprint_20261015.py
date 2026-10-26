#!/usr/bin/env python3
"""Bind the standalone PDF to source, numerical checks, and reviewed renders."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unicodedata

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("historical_document_checks", ROOT / "paper/scripts/validate_revised_preprint_20261015.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def validate(args):
    old.require(not args.output.exists(), "Existing validation receipt preserved")
    old.require(old.sha(args.pdf) == old.sha(args.build / "main.pdf"), "Delivered PDF differs from compiled output")
    log = (args.build / "main.log").read_text()
    old.check_log(log)
    pages = [unicodedata.normalize("NFKC", p.extract_text() or "") for p in PdfReader(args.pdf).pages]
    text = "\n".join(pages)
    old.require(len(pages) > 25 and all(len(p.strip()) > 30 for p in pages), "Unexpected page count or blank page")
    for phrase in ("Revised preprint", "10.5281/zenodo.23376699", "Explicit-report readout qualification", "Collaborative development"):
        old.require(phrase in text, "Missing standalone paper content: " + phrase)
    for phrase in ("Research checklist", "Declaration of LLM usage", "/Users/", "/home/", "/Volumes/"):
        old.require(phrase not in text, "Workshop checklist or local path remains")
    source = (ROOT / "paper/main.tex").read_text()
    old.require("neurips_2026" not in source and "\\input{checklist.tex}" not in source, "Workshop dependency remains")
    old.require("CC BY 4.0" in source and "Project code remains Apache-2.0" in source, "License scopes missing")
    images = sorted(args.renders.glob("final-page-*.png"))
    old.require([p.name for p in images] == [f"final-page-{i:02}.png" for i in range(1, len(pages) + 1)], "Render roster differs")
    old.require(args.all_pages_reviewed and args.detail_pages and all(1 <= p <= len(pages) for p in args.detail_pages), "Visual review incomplete")
    tests = old.check_tests(args.tests)
    for path, expected in old.PRESERVED.items():
        old.require(old.sha(ROOT / path) == expected, "Preserved scientific or historical file changed")
    old.require(old.sha(ROOT / "validation/readout_qualification_v1/specification.json") == old.SPEC_SHA, "Prepared specification changed")
    independent_path = ROOT / "validation/readout_qualification_v1/independent_validation.json"
    independent = old.read(independent_path)
    analysis_path = ROOT / "validation/readout_qualification_v1/run4640/analysis.json"
    analysis = old.read(analysis_path)
    old.require(independent["independent_arithmetic_validation_passed"] and analysis["numerical_gate_passed"], "Numerical checks absent")
    old.require(independent["provenance"]["saved_analysis_sha256"] == old.sha(analysis_path), "Independent validation binding differs")
    old.require(not analysis["primary_qualification_passed"] and not analysis["label_robustness_passed"], "Scientific verdict changed")
    sources = ["paper/main.tex", "paper/references.bib", "paper/contextual_development_20261010.tex", "paper/contextual_input_examples_20261015.tex", "paper/readout_qualification_20261015.tex", "paper/PUBLICATION_METADATA_20261015.json", "CITATION.cff", "paper/scripts/validate_public_preprint_20261015.py"]
    result = {
        "status": "validated_standalone_preprint_prepared_for_publication",
        "pdf_sha256": old.sha(args.pdf), "pages": len(pages),
        "source_sha256": {p: old.sha(ROOT / p) for p in sources},
        "tests": tests, "tests_receipt_sha256": old.sha(args.tests),
        "overfull_boxes": 0, "undefined_references_or_citations": 0,
        "underfull_warnings_present": "Underfull" in log,
        "rendered_page_sha256": {p.name: old.sha(p) for p in images},
        "visual_review": {"all_pages_checked": True, "detail_pages": sorted(set(args.detail_pages)), "observed_clipping_or_overlap": False},
        "independent_saved_score_validation_sha256": old.sha(independent_path),
        "numerical_gate_passed": True, "primary_qualification_passed": False, "label_robustness_passed": False,
        "doi": "10.5281/zenodo.23376699", "doi_state_at_validation": "reserved",
        "external_publication_verified_by_this_check": False,
        "document_validation_is_scientific_replication": False,
        "new_model_forwards": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return {k: result[k] for k in ("status", "pdf_sha256", "pages", "tests", "doi")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pdf", "build", "renders", "tests", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--all-pages-reviewed", action="store_true")
    parser.add_argument("--detail-pages", nargs="+", required=True, type=int)
    print(json.dumps(validate(parser.parse_args()), indent=2))
