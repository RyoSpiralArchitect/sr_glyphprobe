from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "artifacts" / "emoji_steering_specificity_analysis_v0"
MANIFEST = BUNDLE / "PUBLIC_MANIFEST.json"
SUMMARY = BUNDLE / "reporting_summary_v0.json"
CLOSEOUT = (
    ROOT
    / "validation"
    / "emoji_steering_specificity_analysis_v0"
    / "point_results_closeout_979533f.json"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _document(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_public_checksum_ledger_is_current_and_complete() -> None:
    expected = {
        "PUBLIC_MANIFEST.json",
        "README.ja.md",
        "README.md",
        "reporting_summary_v0.json",
    }
    observed: dict[str, str] = {}
    for line in (BUNDLE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", 1)
        assert filename not in observed
        observed[filename] = digest

    assert set(observed) == expected
    for filename, digest in observed.items():
        assert _sha256(BUNDLE / filename) == digest


def test_manifest_binds_summary_closeout_and_six_omitted_sources() -> None:
    manifest = _document(MANIFEST)
    summary = _document(SUMMARY)
    closeout = _document(CLOSEOUT)

    assert manifest["status"] == (
        "share_with_caveats_exploratory_point_evidence_bootstrap_pending"
    )
    assert len(manifest["included_payload"]) == 1
    payload = manifest["included_payload"][0]
    assert payload["path"] == SUMMARY.name
    assert payload["bytes"] == SUMMARY.stat().st_size
    assert payload["sha256"] == _sha256(SUMMARY)

    closeout_binding = manifest["repository_provenance"]["point_results_closeout"]
    assert closeout_binding["bytes"] == CLOSEOUT.stat().st_size
    assert closeout_binding["sha256"] == _sha256(CLOSEOUT)
    assert manifest["input_closeout"] == closeout["input_closeout"]
    assert summary["input_bindings"]["point_results_closeout_json"] == {
        "bytes": CLOSEOUT.stat().st_size,
        "filename": CLOSEOUT.name,
        "sha256": _sha256(CLOSEOUT),
    }

    omitted = manifest["omitted_source_derived_outputs"]
    assert len(omitted) == 6
    assert (
        sum(row["bytes"] for row in omitted)
        == manifest["omitted_source_derived_outputs_bytes"]
    )
    assert {row["path"]: (row["bytes"], row["sha256"]) for row in omitted} == {
        filename: (binding["bytes"], binding["sha256"])
        for filename, binding in closeout["outputs"].items()
    }

    summary_bindings = {
        summary["input_bindings"]["outcomes_point_json"]["filename"]: (
            summary["input_bindings"]["outcomes_point_json"]["bytes"],
            summary["input_bindings"]["outcomes_point_json"]["sha256"],
        ),
        **{
            filename: (binding["bytes"], binding["sha256"])
            for filename, binding in summary["input_bindings"]["geometry_files"].items()
        },
    }
    assert summary_bindings == {
        filename: (binding["bytes"], binding["sha256"])
        for filename, binding in closeout["outputs"].items()
    }


def test_summary_retains_exploratory_and_interval_boundaries() -> None:
    manifest = _document(MANIFEST)
    summary = _document(SUMMARY)
    closeout = _document(CLOSEOUT)

    assert summary["status"] == (
        "post_outcome_reporting_synthesis_complete_bootstrap_pending"
    )
    assert summary["bootstrap"] == {
        "executed_replicates": 0,
        "intervals_included": False,
        "paper_interval_gate_satisfied": False,
        "registered_replicates": 20_000,
        "status": "pending",
    }
    assert summary["reporting_policy"]["all_endpoints_retained"] is True
    assert summary["reporting_policy"]["descriptive_point_synthesis_only"] is True
    assert summary["reporting_policy"]["inferential_selection"] is False
    assert summary["reporting_policy"]["raw_arrays_read"] is False
    assert summary["point_results_closeout_sha256"] == _sha256(CLOSEOUT)
    assert (
        summary["run_binding_root_sha256"]
        == closeout["input_closeout"]["run_binding_root_sha256"]
    )
    assert manifest["interval_gate"]["executed_bootstrap_replicates"] == 0
    assert manifest["claim_boundary"] == {
        "behavioral_steering_claim_authorized": False,
        "causal_or_mechanistic_claim_authorized": False,
        "confirmatory_verdict_authorized": False,
        "emoji_meaning_claim_authorized": False,
        "exact_js_claim_authorized": False,
        "model_population_generality_claim_authorized": False,
        "scale_law_claim_authorized": False,
        "tokenizer_independence_claim_authorized": False,
        "unique_emoji_specificity_claim_authorized": False,
    }


def test_public_bundle_contains_no_machine_local_paths() -> None:
    forbidden = (
        "/Users/",
        "/home/",
        "/tmp/",
        "ryohiga",
        "ryospiralarchitect",
        "Ryos-MacBook",
    )
    for path in BUNDLE.iterdir():
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert not any(value in text for value in forbidden), path
