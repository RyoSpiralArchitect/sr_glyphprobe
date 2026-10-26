#!/usr/bin/env python3
"""Record checks for the local PDF; visual review is a separate human/agent gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "validation/contextual_emoji_working_revision_20261010"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_private_text(text):
    """Reject private-shaped identifiers without embedding a real packet ID."""
    for token in ("/Users/", "/home/", "/Volumes/"):
        assert token not in text, "Private identifier/path in PDF"
    assert not re.search(r"\b(?:author-\d+|pkg_[A-Za-z0-9]{16,})\b", text), "Private identifier/path in PDF"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--visual-review-completed", action="store_true")
    args = parser.parse_args()
    assert not args.output.exists(), "Existing receipt preserved"
    build = ROOT / "paper/build/working_reassessment_20261010"
    assert args.pdf.read_bytes() == (build / "main.pdf").read_bytes()
    log = (build / "main.log").read_text()
    assert not re.search(r"Overfull|undefined|Rerun to get|multiply defined", log, re.I)
    pdf = PdfReader(args.pdf)
    texts = [unicodedata.normalize("NFKC", p.extract_text()) for p in pdf.pages]
    assert len(texts) == 29 and all(len(t) > 500 for t in texts)
    assert "Not submission-ready" in texts[0]
    assert "Conclusion" in texts[10]
    assert "unfinished development extension" in texts[23]
    assert "Table 14" in texts[25] and "710" in texts[25]
    check_private_text("\n".join(texts))
    rendered = sorted(args.renders.glob("final-page-*.png"))
    assert len(rendered) == len(texts)
    assert [p.name for p in rendered] == [f"final-page-{i:02}.png" for i in range(1, 30)]
    assert args.visual_review_completed, "Visual review is required, not inferred"
    suites = ET.parse(FOLDER / "tests_pass.xml").getroot().findall("testsuite")
    totals = {key: sum(int(s.attrib[key]) for s in suites) for key in ("tests", "errors", "failures", "skipped")}
    assert totals == {"tests": 65, "errors": 0, "failures": 0, "skipped": 0}
    previous = ROOT / "output/pdf/glyphprobe_post_review_20261007.pdf"
    assert sha(previous) == "43a5931dd5d3de578818298c8a92fbc9f9244c08d0a821d30fce63e1f4645898"
    sources = [
        "paper/main.tex", "paper/contextual_development_20261010.tex", "paper/checklist.tex",
        "paper/generated/contextual_development_tables_20261010.tex",
        "paper/scripts/build_development_summary_20261010.py",
        "paper/scripts/validate_working_reassessment_20261010.py",
        "paper/references.bib", "paper/neurips_2026.sty", "paper/figures/manifest.json",
        "docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.md",
        "docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.ja.md",
        "paper/WORKING_CLAIMS_20261010.md", "paper/WORKING_CLAIMS_20261010.ja.md",
        "paper/ETHICS_REVIEW.md", "paper/ETHICS_REVIEW.ja.md",
        "paper/COMPUTE_REPORT.md", "paper/COMPUTE_REPORT.ja.md",
        "validation/contextual_emoji_working_revision_20261010/summary.json",
        "validation/contextual_emoji_working_revision_20261010/tests_pass.xml",
    ]
    record = {
        "status": "validated_local_working_draft_not_semantic_or_release_validation",
        "pdf_sha256": sha(args.pdf), "pages": len(texts), "main_text_end_page": 11,
        "development_appendix_pages": [24, 25, 26], "new_tables": [11, 12, 13, 14],
        "overfull_boxes": 0, "undefined_references_or_citations": 0,
        "underfull_warnings_present": "Underfull" in log,
        "rendered_page_sha256": {p.name: sha(p) for p in rendered},
        "visual_review": {
            "all_pages_contact_sheet_checked": True,
            "full_page_detail_checked": [1, 10, 11, 23, 24, 25, 26, 29],
            "observed_clipping_or_overlap": False,
            "performed_separately_from_automated_checks": True,
        },
        "tests": totals,
        "prior_test_failure": "One legacy assertion retained T20-C wording after the pre-existing descriptive rename. Updated to the existing optimized-study wording while preserving the scientific boundary; initial failure receipt retained.",
        "source_sha256": {p: sha(ROOT / p) for p in sources},
        "historical_october7_pdf_unchanged": True,
        "private_item_records_exported": False,
        "new_model_forwards": 0, "gpu_work": False,
        "independent_human_validation": False,
        "public_deposit": False, "git_push": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(record, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": record["status"], "pages": len(texts), "tests": totals,
                      "pdf_sha256": record["pdf_sha256"]}))


if __name__ == "__main__":
    main()
