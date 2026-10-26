"""Published-byte identity and saved-score checks; no model or private inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "artifacts/public_release_20261015"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_published_pdf_and_archive_remain_exact():
    expected = "9f9a34b578b8eeec6dd8f08994fa348ea050d5477c3387663cc885d9cd30d673"
    assert sha(ROOT / "output/pdf/glyphprobe_preprint_20261015.pdf") == expected
    assert sha(PAYLOAD / "paper/preprint.pdf") == expected
    assert sha(ROOT / "output/artifacts/glyphprobe_public_release_20261015_v2.zip") == (
        "36959018915a13b988d83b7db13b9e3bb91b6e3a660649cbc8a270340b68f409"
    )


def test_published_package_replay_retains_negative_scientific_gate():
    spec = importlib.util.spec_from_file_location(
        "public_integration_replay", PAYLOAD / "paper/scripts/build_public_release_20261015.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify_directory(PAYLOAD)
    assert result["status"] == "package_integrity_and_saved_score_replay_passed"
    assert result["numerical_gate_passed"]
    assert result["independent_arithmetic_validation_passed"]
    assert result["primary_qualification_passed"] is False
    assert result["model_forwards"] == 0
    # Publication is external evidence, never inferred from numerical replay.
    assert result["publication_verified"] is False


def test_active_manuscript_and_frozen_qualification_equal_published_sources():
    files = [
        "paper/main.tex", "paper/references.bib",
        "paper/contextual_development_20261010.tex",
        "paper/contextual_input_examples_20261015.tex",
        "paper/readout_qualification_20261015.tex",
        "scripts/readout_qualification_v1.py",
        "tests/test_readout_qualification_v1.py",
    ]
    for name in files:
        assert sha(ROOT / name) == sha(PAYLOAD / name), name


def test_next_theme_is_bilingual_and_does_not_claim_384_acquisition():
    for suffix in (".md", ".ja.md"):
        assert (ROOT / "docs" / ("PAPER_NEXT_THEME_20261026" + suffix)).is_file()
        assert (ROOT / "docs" / ("PUBLIC_INTEGRATION_SCOPE_20261026" + suffix)).is_file()
    audits = list((ROOT / "validation").glob("t22*/**/design_audit.json"))
    assert len(audits) == 1
    audit = json.loads(audits[0].read_text())
    assert audit["acquisition_admitted"] is False
    assert audit["model_forwards"] == 0
