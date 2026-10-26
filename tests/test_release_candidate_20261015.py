"""CPU-only packaging/privacy regressions. No private records or real models."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


b = module(ROOT / "paper/scripts/build_release_candidate_20261015.py", "release_candidate_test")
helpers = module(ROOT / "tests/test_readout_qualification_v1.py", "release_candidate_qualification_helpers")
q = helpers.q


@pytest.fixture(scope="module")
def synthetic_spec():
    spec = helpers.spec.__wrapped__()
    for case in spec["sentinels"]:
        if case["shared_prefix_token_count"] == 0:
            for score in case["expected_scores"].values():
                score["shared_prediction_logits_sha256"] = b.digest_bytes(b"")
    spec.update(protocol_id=q.PROTOCOL, inventory_sha256=q.object_sha(q.inventory()),
        tokenized_inputs_sha256=q.object_sha(spec["inputs"]), primary=q.PRIMARY, label_robustness_gate=q.LABEL_GATE,
        planned_pairs=q.PAIRS, planned_scientific_sequence_scores=4608, planned_sentinel_forwards=32,
        planned_forward_attempts=q.MAX_FORWARDS, independent_fact_roots=32,
        split_roots={"development": 16, "reserved_check": 16}, qualification_scoring={"score": "full sum"},
        model_path="/home/imaginary/private-checkpoint", runtime_packages={"torch": "synthetic"},
        python_version="synthetic", scoring={"attention": "eager"},
        model_artifact={"files": {}, "manifest_sha256": "1" * 64, "file_count": 0, "total_bytes": 0},
        expected_implementation_sources={"files": {"modeling": {"path": "/home/imaginary/model.py", "sha256": "2" * 64}}},
        source_files={p: b.sha(ROOT / p) for p in ("scripts/readout_qualification_v1.py", q.PREFIX)})
    return spec


@pytest.fixture(scope="module")
def synthetic_records(synthetic_spec):
    rows = helpers.records(synthetic_spec)
    for row in rows:
        if row["geometry"]["shared_prefix_token_count"] == 0:
            row["shared_prediction_logits_sha256"] = b.digest_bytes(b"")
    return rows


def test_projection_has_no_paths_and_replays_exactly(synthetic_spec, synthetic_records):
    public = b.project_specification(synthetic_spec)
    records = [b.project_record(r) for r in synthetic_records]
    b.scan_structure(public, "spec")
    b.scan_structure(records, "records")
    assert "model_path" not in public
    assert "expected_implementation_sources" not in public
    assert len(public["inputs"]) == 2304
    assert len(records) == 4640
    assert q.analyze(public, records) == q.analyze(synthetic_spec, synthetic_records)


def test_boundary_failure_is_retained_without_host_error(synthetic_records):
    original = copy.deepcopy(synthetic_records[17])
    original["boundary_error_after_score"] = "error opening /home/imaginary/source"
    public = b.project_record(original)
    assert "boundary_error_after_score" in public
    b.scan_structure(public, "row")
    assert original["boundary_error_after_score"].endswith("source")


def test_uncompleted_record_does_not_gain_score(synthetic_records):
    row = {k: synthetic_records[17][k] for k in ("event_id", "phase", "input_id", "method", "geometry")}
    row.update(status="not_run", forward_attempted=False, reason="/home/imaginary/failure")
    public = b.project_record(row)
    assert "candidate_token_logprobs" not in public
    assert public["status"] == "not_run"
    b.scan_structure(public, "row")


@pytest.mark.parametrize("name", ["../escape.txt", "/absolute.txt", "data/private/responses.json",
    "data/targets/p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl", "model.safetensors",
    ".git/config", "cache\\secrets.txt"])
def test_payload_names_fail_closed(name):
    with pytest.raises(ValueError):
        b.relative_name(name)


@pytest.mark.parametrize("text", ["/Users/example/data", "/home/example/data", "smb://host/share",
    "pkg_" + "a" * 32, "ghp_" + "a" * 30, "-----BEGIN PRIVATE KEY-----"])
def test_privacy_scan_blocks_identifiers_paths_and_secrets(text):
    with pytest.raises(ValueError):
        b.scan_text(text, "fixture")


def test_nested_private_key_is_rejected():
    with pytest.raises(ValueError, match="Private field"):
        b.scan_structure({"summary": [{"participant_id": "synthetic"}]}, "fixture")


def test_protected_file_rejected_before_open(tmp_path, monkeypatch):
    path = tmp_path / "p2_confirmatory_targets_v1.jsonl"
    monkeypatch.setattr(Path, "read_bytes", lambda _: pytest.fail("Protected file was opened"))
    with pytest.raises(ValueError, match="Protected target"):
        b.source_bytes(path)


@pytest.mark.parametrize("root", ["/private/var", "/private/tmp"])
def test_exact_macos_temporary_system_roots_are_allowed(root):
    path = Path(root) / "glyphprobe-synthetic-fixture" / "data.json"
    assert b.safe_path(path) == path


@pytest.mark.parametrize("name", [
    "/private/var/glyphprobe-synthetic-fixture/private/data.json",
    "/private/tmp/glyphprobe-synthetic-fixture/private/data.json",
    "/private/temporary/glyphprobe-synthetic-fixture/data.json",
    "/private/tmp-other/glyphprobe-synthetic-fixture/data.json",
    "/ordinary/private/var/glyphprobe-synthetic-fixture/data.json",
    "/ordinary/private/tmp/glyphprobe-synthetic-fixture/data.json",
])
def test_macos_root_exception_does_not_allow_private_folders(name, monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda _: pytest.fail("Private file was opened"))
    with pytest.raises(ValueError, match="Private or environment path"):
        b.source_bytes(name)


def test_actual_tmp_directory_alias_and_resolved_path_are_readable():
    # macOS resolves /tmp to /private/tmp; Linux keeps /tmp unchanged.
    with tempfile.TemporaryDirectory(prefix="glyphprobe-release-test-", dir="/tmp") as folder:
        path = Path(folder) / "synthetic.json"
        path.write_bytes(b'{"synthetic": true}\n')
        assert b.source_bytes(path) == b.source_bytes(path.resolve()) == b'{"synthetic": true}\n'


def test_symlink_rejected(tmp_path):
    target = tmp_path / "ordinary.txt"
    target.write_text("synthetic")
    link = tmp_path / "linked.txt"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="Symlink"):
        b.source_bytes(link)


def test_zip_deterministic_manifest_and_no_overwrite(tmp_path):
    payload = {"README.md": b"Synthetic package fixture.\n", "evidence/data.json": b'{"n": 2}\n'}
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    result = b.bundle(payload, first)
    assert result["status"] == "local_release_candidate_not_published"
    assert not result["published"] and not result["doi_action"]
    assert b.bundle(payload, second)["archive_sha256"] == result["archive_sha256"]
    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first) as archive:
        assert all(i.date_time == b.FIXED_TIME for i in archive.infolist())
        manifest = json.loads(archive.read(b.ARTIFACT_ID + "/ARTIFACT_MANIFEST.json"))
        assert not manifest["public_deposit"] and not manifest["paper_license_confirmed"]
        assert {r["path"] for r in manifest["files"]} == set(payload)
        for row in manifest["files"]:
            assert row["bytes"] == len(payload[row["path"]])
            assert row["sha256"] == b.digest_bytes(payload[row["path"]])
    with pytest.raises(ValueError, match="already exists"):
        b.bundle(payload, first)


def test_scan_failure_creates_no_partial_archive(tmp_path):
    output = tmp_path / "bad.zip"
    with pytest.raises(ValueError, match="Local/network"):
        b.bundle({"data.txt": b"/home/imaginary/secret"}, output)
    assert not output.exists()


def test_arbitrary_nested_archive_is_rejected():
    with pytest.raises(ValueError, match="Unapproved"):
        b.scan_payload("historical/unknown.zip", b"not an archive")


def test_tex_closure_is_literal_and_bounded(tmp_path):
    paper = tmp_path / "paper"
    (paper / "figures").mkdir(parents=True)
    (paper / "main.tex").write_text(r"\input{section}\includegraphics[width=1cm]{figures/a.pdf}\bibliography{references}")
    (paper / "section.tex").write_text("Synthetic section")
    (paper / "figures/a.pdf").write_bytes(b"placeholder; no PDF scan in closure traversal")
    (paper / "references.bib").write_text("@misc{synthetic}")
    assert set(b.tex_dependencies(tmp_path)) == {"paper/main.tex", "paper/section.tex", "paper/figures/a.pdf", "paper/references.bib"}
    (paper / "main.tex").write_text(r"\input{../private/answers}")
    with pytest.raises(ValueError):
        b.tex_dependencies(tmp_path)


def test_pdf_privacy_metadata_scan(tmp_path):
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=50, height=50)
    writer.add_metadata({"/Subject": "/home/imaginary/private-file"})
    path = tmp_path / "test.pdf"
    with path.open("wb") as handle:
        writer.write(handle)
    with pytest.raises(ValueError, match="Local/network"):
        b.scan_payload("paper/test.pdf", path.read_bytes())


def write_raw_fixture(folder, spec, records):
    folder.mkdir()
    spec_path = folder.parent / "specification.json"
    spec_path.write_bytes(b.canonical(spec))
    (folder / "forwards.jsonl").write_bytes(b"".join(b.canonical_line(r) for r in records))
    analysis = q.analyze(spec, records)
    (folder / "analysis.json").write_bytes(b.canonical(analysis))
    (folder / "run_started.json").write_bytes(b.canonical({"protocol_id": spec["protocol_id"],
        "source_files": spec["source_files"], "specification_sha256": b.sha(spec_path)}))
    receipt = {k: analysis[k] for k in ("protocol_id", "numerical_gate_passed", "primary_qualification_passed",
        "label_robustness_passed", "qualification_status", "completed_pairs", "status_counts")}
    receipt.update(status="completed", forward_attempts=4640, planned_forward_attempts=4640, elapsed_seconds=0.0,
        peak_torch_memory_mib=None, downloads=0, generation_calls=0, stop_reason=None,
        specification_sha256=b.sha(spec_path), source_files=spec["source_files"],
        artifacts={p.name: b.sha(p) for p in folder.iterdir()})
    (folder / "run_completed.json").write_bytes(b.canonical(receipt))
    return spec_path


def test_public_run_roundtrip_and_tamper_refusal(tmp_path, synthetic_spec, synthetic_records):
    folder = tmp_path / "run"
    spec_path = write_raw_fixture(folder, synthetic_spec, synthetic_records)
    payload = b.portable_run(ROOT, spec_path, folder, b.sha(spec_path))
    assert len(payload) == 7
    for name, content in payload.items():
        b.scan_payload(name, content)
    summary = json.loads(payload["evidence/readout_qualification_v1/run_summary.public.json"])
    assert summary["primary_qualification_passed"] is True
    assert summary["source_binding_or_execution_failure"] is False
    binding = json.loads(payload["evidence/readout_qualification_v1/projection_binding.json"])
    assert binding["raw_sha256"]["specification.json"] == b.sha(spec_path)
    assert binding["private_participant_records_read"] is False
    (folder / "analysis.json").write_text("{}")
    with pytest.raises(ValueError, match="Raw artifact hash"):
        b.portable_run(ROOT, spec_path, folder, b.sha(spec_path))


def test_extracted_score_replay_and_roster_are_repeatable(tmp_path, synthetic_spec, synthetic_records):
    folder = tmp_path / "run"
    spec_path = write_raw_fixture(folder, synthetic_spec, synthetic_records)
    payload = b.portable_run(ROOT, spec_path, folder, b.sha(spec_path))
    for name in ("scripts/readout_qualification_v1.py", "scripts/validate_readout_qualification_v1.py", q.PREFIX):
        payload[name] = b.source_bytes(ROOT / name)
    archive = tmp_path / "test.zip"
    b.bundle(payload, archive)
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(tmp_path / "extract")
    root = tmp_path / "extract" / b.ARTIFACT_ID
    first = b.verify_directory(root)
    assert first == b.verify_directory(root)
    assert first["model_forwards"] == 0 and first["primary_qualification_passed"] is True
    assert first["independent_arithmetic_validation_passed"] is True
    assert not list(root.rglob("__pycache__"))
    (root / "unexpected.txt").write_text("Synthetic extra file")
    with pytest.raises(ValueError, match="entry roster"):
        b.verify_directory(root)


def test_stopped_run_projection_preserves_numerical_failure(tmp_path, synthetic_spec, synthetic_records):
    folder = tmp_path / "run"
    spec_path = write_raw_fixture(folder, synthetic_spec, synthetic_records)
    receipt = b.read(folder / "run_completed.json")
    analysis = b.read(folder / "analysis.json")
    error = "Source changed at /home/imaginary/model-path"
    analysis.update(numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
                    qualification_status="not_evaluable_numerical_or_incomplete", execution_error=error)
    (folder / "analysis.json").write_bytes(b.canonical(analysis))
    receipt.update(status="stopped_or_gate_failed", stop_reason=error,
        numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
        qualification_status="not_evaluable_numerical_or_incomplete")
    receipt["artifacts"]["analysis.json"] = b.sha(folder / "analysis.json")
    (folder / "run_completed.json").write_bytes(b.canonical(receipt))
    payload = b.portable_run(ROOT, spec_path, folder, b.sha(spec_path))
    for name, value in payload.items():
        b.scan_payload(name, value)
    result = json.loads(payload["evidence/readout_qualification_v1/analysis.public.json"])
    summary = json.loads(payload["evidence/readout_qualification_v1/run_summary.public.json"])
    assert result["numerical_gate_passed"] is False
    assert result["primary_qualification_passed"] is False
    assert summary["source_binding_or_execution_failure"] is True
    assert "execution_error" not in result
    independent = json.loads(payload["evidence/readout_qualification_v1/independent_validation.public.json"])
    assert independent["independent_arithmetic_validation_passed"] is None
    assert independent["status"] == "not_evaluable_incomplete_or_numerical_gate_failed"


def test_external_specification_hash_required(tmp_path, synthetic_spec, synthetic_records):
    folder = tmp_path / "run"
    spec_path = write_raw_fixture(folder, synthetic_spec, synthetic_records)
    with pytest.raises(ValueError, match="Externally pinned"):
        b.portable_run(ROOT, spec_path, folder, "0" * 64)
    with pytest.raises(ValueError, match="Externally retained"):
        b.portable_run(ROOT, spec_path, folder, None)


def test_independent_public_adapter_rejects_false_empty_prefix_hash(synthetic_spec, synthetic_records):
    rows = copy.deepcopy(synthetic_records)
    for row in rows:
        if row["geometry"]["shared_prefix_token_count"] == 0:
            row["shared_prediction_logits_sha256"] = "c" * 64
    # The runner's numerical equality check accepts matching empty-prefix hashes;
    # the independent implementation additionally checks the actual empty digest.
    saved = q.analyze(synthetic_spec, rows)
    assert saved["numerical_gate_passed"] is True
    public_spec = b.project_specification(synthetic_spec)
    public_rows = [b.project_record(r) for r in rows]
    with pytest.raises(ValueError, match="Empty prefix hash"):
        b.independent_public_result(ROOT, public_spec, public_rows, saved)


def test_whitelist_contains_no_private_or_model_assets():
    for path in b.STATIC_FILES:
        b.relative_name(path)
        assert "author_pilot" not in path
        assert "private" not in path
    assert not any(p.endswith(".sty") for p in b.STATIC_FILES)
    assert b.license_classification("paper/revised_preprint.pdf").endswith("author_confirmation_pending")
