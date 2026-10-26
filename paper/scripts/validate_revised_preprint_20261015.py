#!/usr/bin/env python3
"""Bind the revised PDF to checks and reviewed renders; never publish it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
SPEC_SHA = "5273b1f86db4ee956659a94ca7f047856e86b5f857fdf66efc5d96e5f85c487f"
PRESERVED = {
    "output/pdf/glyphprobe_post_review_20261007.pdf": "43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898",
    "output/pdf/glyphprobe_working_reassessment_20261010.pdf": "7ade305ceaea7eaffb9a67b8cce8f301f425e95163e98344a758a834f8879abd",
    "output/artifacts/glyphprobe_t19_anonymous_evidence_v4.zip": "33cadc408d550781454aa95aa5af7ea2f1c62a1411d2cabaaf9ac561afe1a84e",
    "scripts/readout_qualification_v1.py": "a285a44bddf37c4f206052b055096f2ef58ce5a7b71a6112c75f72f6eb36e636",
    "tests/test_readout_qualification_v1.py": "8d27c8e9911dc4781c1fac151440b40e9db5ff45d73db47eeb9bcb98f2d5642b",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def check_tests(path):
    document = ET.parse(path).getroot()
    suites = [document] if document.tag == "testsuite" else document.findall("testsuite")
    totals = {key: sum(int(s.attrib[key]) for s in suites) for key in ("tests", "errors", "failures", "skipped")}
    require(totals["tests"] > 0 and not any(totals[k] for k in ("errors", "failures", "skipped")), "Tests failed, skipped, or absent")
    return totals


def check_log(log):
    require(not re.search(r"Overfull|undefined|Rerun to get|multiply defined", log, re.I), "Compilation has unresolved layout/references")


def check_private_text(text):
    """Reject private-shaped identifiers without embedding a real packet ID."""
    for token in ("/Users/", "/home/", "/Volumes/"):
        require(token not in text, "Private identifier/path in PDF")
    require(not re.search(r"\b(?:author-\d+|pkg_[A-Za-z0-9]{16,})\b", text),
            "Private identifier/path in PDF")


def check_text(texts):
    require(len(texts) >= 31 and all(len(t.strip()) > 40 for t in texts), "Unexpected page count or empty page")
    require("Revised preprint" in texts[0] and "October 15, 2026" in texts[0], "Current version label missing")
    joined = "\n".join(texts)
    for phrase in ("Explicit-report readout qualification", "Research checklist", "local release candidate"):
        require(phrase.lower() in joined.lower(), "Missing current section: " + phrase)
    check_private_text(joined)
    return joined


def validate(args):
    require(not args.output.exists(), "Existing validation receipt preserved")
    require(sha(args.pdf) == sha(args.build / "main.pdf"), "Delivered PDF differs from compiled source")
    log = (args.build / "main.log").read_text()
    check_log(log)
    reader = PdfReader(args.pdf)
    texts = [unicodedata.normalize("NFKC", p.extract_text()) for p in reader.pages]
    check_text(texts)
    rendered = sorted(args.renders.glob("final-page-*.png"))
    require([p.name for p in rendered] == [f"final-page-{i:02}.png" for i in range(1, len(texts)+1)], "Rendered page roster differs")
    detail_pages = sorted(set(args.detail_pages))
    require(args.contact_sheet_reviewed and detail_pages and all(1 <= p <= len(texts) for p in detail_pages), "Separate visual review must be completed")
    totals = check_tests(args.tests)
    for path, expected in PRESERVED.items():
        require(sha(ROOT / path) == expected, "Historical or specified source changed: " + path)
    spec_path = ROOT / "validation/readout_qualification_v1/specification.json"
    require(sha(spec_path) == SPEC_SHA, "Prepared specification changed")
    run = ROOT / "validation/readout_qualification_v1/run4640"
    completion, analysis, independent = read(run / "run_completed.json"), read(run / "analysis.json"), read(args.independent)
    require(completion["status"] == "completed" and completion["forward_attempts"] == 4640 and completion["specification_sha256"] == SPEC_SHA, "Acquisition incomplete or differs")
    require(analysis["numerical_gate_passed"] and independent["independent_arithmetic_validation_passed"], "Numerical verification absent")
    require(independent["provenance"]["saved_analysis_sha256"] == sha(run / "analysis.json"), "Independent analysis binding differs")
    require(independent["provenance"]["run_completed_sha256"] == sha(run / "run_completed.json"), "Independent run binding differs")
    for key in ("primary_qualification_passed", "label_robustness_passed"):
        require(completion[key] == analysis[key] == independent[key], "Outcome disagreement: " + key)
    sources = [
        "paper/main.tex", "paper/checklist.tex", "paper/contextual_development_20261010.tex",
        "paper/contextual_input_examples_20261015.tex", "paper/readout_qualification_20261015.tex",
        "paper/references.bib", "paper/neurips_2026.sty",
        "paper/scripts/validate_revised_preprint_20261015.py",
        "scripts/validate_readout_qualification_v1.py",
    ]
    result = {
        "status": "validated_local_revised_preprint_candidate",
        "pdf_sha256": sha(args.pdf), "pages": len(texts),
        "overfull_boxes": 0, "undefined_references_or_citations": 0,
        "underfull_warnings_present": "Underfull" in log,
        "tests": totals, "tests_receipt_sha256": sha(args.tests),
        "source_sha256": {p: sha(ROOT / p) for p in sources},
        "preserved_historical_and_specified_source_sha256": PRESERVED,
        "rendered_page_sha256": {p.name: sha(p) for p in rendered},
        "visual_review": {"all_pages_contact_sheet_checked": True, "full_page_detail_checked": detail_pages,
                          "observed_clipping_or_overlap": False, "separate_from_automated_checks": True},
        "new_acquisition": {"sequence_forwards": 4640, "scientific_pairs": 2304, "sentinel_forwards": 32,
            "specification_sha256": SPEC_SHA, "run_completed_sha256": sha(run / "run_completed.json"),
            "independent_validation_sha256": sha(args.independent),
            "numerical_gate_passed": True, "primary_qualification_passed": analysis["primary_qualification_passed"],
            "label_robustness_passed": analysis["label_robustness_passed"]},
        "document_checks_are_semantic_validation": False, "independent_reacquisition": False,
        "independent_human_validation": False, "private_item_records_exported": False,
        "public_deposit": False, "doi_reserved_or_registered": False, "git_push": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return {k: result[k] for k in ("status", "pdf_sha256", "pages", "tests", "new_acquisition")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pdf", "build", "renders", "tests", "independent", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--contact-sheet-reviewed", action="store_true")
    parser.add_argument("--detail-pages", nargs="+", type=int, required=True)
    print(json.dumps(validate(parser.parse_args()), indent=2))


if __name__ == "__main__":
    main()
