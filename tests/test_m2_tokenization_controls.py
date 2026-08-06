from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest
import yaml

from glyphprobe.config import load_experiment_config


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_m2_tokenization_controls.py"
SPEC = importlib.util.spec_from_file_location("audit_m2_tokenization_controls", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads(
        (ROOT / "data" / "tokenization_controls" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )


def _panel_glyphs(relative_path: str) -> set[str]:
    raw = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
    return {item["glyph"] for item in raw["items"]}


def test_manifest_digest_is_hard_pinned_and_companion_matches() -> None:
    manifest_path = ROOT / AUDIT.MANIFEST_PATH
    actual = _sha256(manifest_path)
    assert actual == AUDIT.EXPECTED_MANIFEST_SHA256
    fields = (ROOT / AUDIT.MANIFEST_SHA_PATH).read_text(encoding="utf-8").split()
    assert fields == [actual, AUDIT.MANIFEST_PATH.as_posix()]


def test_manifest_tampering_fails_even_if_no_panel_is_loaded(tmp_path: Path) -> None:
    destination = tmp_path / "data" / "tokenization_controls"
    destination.mkdir(parents=True)
    shutil.copy2(ROOT / AUDIT.MANIFEST_PATH, destination / "manifest.json")
    shutil.copy2(ROOT / AUDIT.MANIFEST_SHA_PATH, destination / "manifest.sha256")
    with (destination / "manifest.json").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(AUDIT.AuditError, match="hard-pinned"):
        AUDIT._load_manifest(tmp_path)


def test_three_matched_null_panels_are_disjoint_and_exclude_neutral() -> None:
    manifest = _manifest()
    null_specs = [row for row in manifest["panels"] if row["role"] == "matched_null"]
    assert len(null_specs) == 3
    glyph_sets = {row["id"]: _panel_glyphs(row["path"]) for row in null_specs}
    for index, left in enumerate(null_specs):
        for right in null_specs[index + 1 :]:
            assert glyph_sets[left["id"]].isdisjoint(glyph_sets[right["id"]])
    dominant_neutral = next(
        row["glyph"]
        for row in manifest["neutral_controls"]
        if row["id"] == manifest["execution_config_constraints"]["neutral_control_id"]
    )
    assert dominant_neutral == "🟰"
    assert all(dominant_neutral not in glyphs for glyphs in glyph_sets.values())
    assert manifest["matched_null_cross_panel_overlap"] == {
        "maximum_pairwise_glyph_overlap": 0,
        "expected_overlaps": [],
    }


def test_semantic_near_control_is_explicit_and_unique() -> None:
    manifest = _manifest()
    near = manifest["matched_null_inventory"]["conservative_semantic_near_controls"]
    assert near == [
        {
            "glyph": "🟥",
            "codepoint": "U+1F7E5",
            "unicode_name": "LARGE RED SQUARE",
            "panel_id": "m2_null_prefix_9x253_1x242_c",
        }
    ]
    raw = yaml.safe_load(
        (ROOT / "data" / "emoji_panels" / "m2_matched_null_c.yaml").read_text(
            encoding="utf-8"
        )
    )
    rows = [item for item in raw["items"] if item["glyph"] == "🟥"]
    assert len(rows) == 1
    assert rows[0]["factors"]["control_subrole"] == "conservative_semantic_near_control"


def test_control_configs_resolve_without_loading_a_model() -> None:
    manifest = _manifest()
    for panel_spec in manifest["panels"]:
        config_path = ROOT / panel_spec["config_path"]
        assert _sha256(config_path) == panel_spec["config_sha256"]
        config, inputs = load_experiment_config(config_path)
        assert config.backend.model == AUDIT.EXPECTED_MODEL_ID
        assert config.backend.revision == AUDIT.EXPECTED_REVISION
        assert config.backend.local_files_only is True
        assert config.panel.neutral_glyph == "🟰"
        assert "exploratory" in config.run.name
        assert len(inputs.panel_items) == 10
        assert len(inputs.wrappers) == 16
        assert len(inputs.targets) == 24


def test_audit_script_has_no_model_loader() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert "from_pretrained(" in source


def test_live_pinned_tokenizer_audit_when_snapshot_is_available() -> None:
    pytest.importorskip("transformers")
    snapshot = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--openai-community--gpt2"
        / "snapshots"
        / AUDIT.EXPECTED_REVISION
    )
    required = _manifest()["tokenizer"]["assets_sha256"]
    if not all((snapshot / filename).is_file() for filename in required):
        pytest.skip("pinned GPT-2 tokenizer snapshot is not available locally")

    report = AUDIT.audit_suite(ROOT)
    assert report["status"] == "pass"
    assert report["manifest_sha256"] == AUDIT.EXPECTED_MANIFEST_SHA256
    assert report["wrapper_count"] == 16
    assert report["matched_null_disjoint"] is True
    assert report["counts"] == {
        "panel_count": 5,
        "matched_null_panel_count": 3,
        "scalar_entries_verified": 62,
        "wrapper_profile_comparisons": 992,
    }
    null_reports = [row for row in report["panels"] if row["role"] == "matched_null"]
    assert len(null_reports) == 3
    assert all(
        row["prefix_histogram"] == {"8582,242": 1, "8582,253": 9}
        for row in null_reports
    )
    suffix = next(
        row for row in report["panels"] if row["role"] == "suffix_matched_middle_shift"
    )
    assert suffix["prefix_histogram"] == {"8582,236": 10}
    homogeneous = next(
        row
        for row in report["panels"]
        if row["role"] == "prefix_homogeneous_colored_shapes"
    )
    assert homogeneous["prefix_histogram"] == {"8582,253": 10}
