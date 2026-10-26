#!/usr/bin/env python3
"""Build a local, whitelist-only release candidate; never publish or register a DOI.

The current PDF, its bounded TeX dependency closure, one hash-pinned historical
archive, aggregate development evidence and an explicit portable projection of
the readout experiment are included. Private answers and local runtime paths
are neither inputs nor payloads. The original experimental receipts are never
modified. ``verify`` replays the public readout scores using only the stdlib.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ID = "glyphprobe_revised_preprint_20261015"
FIXED_TIME = (2026, 10, 15, 0, 0, 0)
HISTORICAL = "output/artifacts/glyphprobe_t19_anonymous_evidence_v4.zip"
HISTORICAL_SHA = "33cadc408d550781454aa95aa5af7ea2f1c62a1411d2cabaaf9ac561afe1a84e"
FORMAT_URL = "https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip"
FORMAT_SHA = "82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9"
PROTECTED = {"p2_confirmatory_targets_v1.jsonl", "c1_causal_holdout_targets_v1.jsonl"}
FORBIDDEN_PARTS = {".git", ".venv", "venv", "__pycache__", "private", "secrets", "node_modules", "author_packets"}
FORBIDDEN_SUFFIXES = {".safetensors", ".pt", ".pth", ".ckpt", ".npy", ".npz", ".pem", ".key"}
PRIVATE_KEYS = {"packet_id", "participant_id", "participant_name", "respondent_id", "assignment_key",
                "item_assignments", "individual_answers", "human_answers", "free_text", "private_notes",
                "api_key", "access_token", "refresh_token", "password"}
LOCAL_PATH = re.compile(r"/(?:Users|home|Volumes|mnt|root|private|tmp)/[^\s\"'<>]+|[A-Za-z]:\\(?:Users|Temp)\\|(?:file|smb)://")
SECRET = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|pkg_[0-9a-f]{32})\b|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")
STATIC_FILES = (
    "LICENSE", "paper/UNICODE_LICENSE.txt", "paper/ASSET_LICENSES.md", "paper/ASSET_LICENSES.ja.md",
    "paper/COMPUTE_REPORT.md", "paper/COMPUTE_REPORT.ja.md", "paper/ETHICS_REVIEW.md", "paper/ETHICS_REVIEW.ja.md",
    "paper/EXPERIMENT_GUIDE.md", "paper/EXPERIMENT_GUIDE.ja.md",
    "paper/CLAIM_TABLE.md", "paper/CLAIM_TABLE.ja.md",
    "paper/CURRENT_CLAIMS_20261015.md", "paper/CURRENT_CLAIMS_20261015.ja.md",
    "paper/REVISION_NOTES_20261015.md", "paper/REVISION_NOTES_20261015.ja.md",
    "paper/RELEASE_CANDIDATE_20261015.md", "paper/RELEASE_CANDIDATE_20261015.ja.md",
    "paper/WORKING_CLAIMS_20261010.md", "paper/WORKING_CLAIMS_20261010.ja.md",
    "docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.md", "docs/CONTEXTUAL_EMOJI_REASSESSMENT_20261010.ja.md",
    "docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1_ANALYSIS.md", "docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1_ANALYSIS.ja.md",
    "validation/contextual_emoji_working_revision_20261010/summary.json",
    "validation/revised_preprint_20261015/document_validation.json",
    "validation/revised_preprint_20261015/document_validation_v2.json",
    "data/contextual_emoji_development_v0.jsonl", "data/contextual_emoji_candidate_wording_v0.json",
    "scripts/contextual_emoji_two_track_v1.py", "scripts/run_contextual_emoji_two_track_v1.py",
    "scripts/contextual_emoji_prefix_consistency_v0.py", "scripts/contextual_emoji_output_pilot_v0.py",
    "scripts/readout_qualification_v1.py", "src/glyphprobe/provenance.py", "src/glyphprobe/io.py",
    "tests/test_readout_qualification_v1.py", "docs/READOUT_QUALIFICATION_V1.md", "docs/READOUT_QUALIFICATION_V1.ja.md",
    "scripts/validate_readout_qualification_v1.py", "tests/test_validate_readout_qualification_v1.py",
    "scripts/summarize_readout_qualification_v1.py", "tests/test_summarize_readout_qualification_v1.py",
    "paper/generated/readout_qualification_20261015/summary.json",
    "paper/generated/readout_qualification_20261015/projection_receipt.json",
    "docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.md", "docs/CONTEXTUAL_EMOJI_TWO_TRACK_V1.ja.md",
    "paper/scripts/build_release_candidate_20261015.py",
)
RUN_FILES = {"forwards.jsonl", "analysis.json", "run_started.json", "runtime.json",
             "implementation_sources.json", "occupancy_checks.json"}
LOGICAL_KEYS = ("root_id", "family", "split", "positive_proposition", "negative_proposition", "input_id",
                "report_state", "query_polarity", "proposition", "report", "question_form", "question",
                "answer_format", "prompt", "answers", "proposition_supported", "expected_yes", "reference_status")
CANDIDATE_KEYS = ("input_token_ids", "prompt_token_count", "candidate_token_ids", "continuation")
GEOMETRY_KEYS = ("input_token_ids", "attention_mask", "position_ids", "valid_length", "total_length",
                 "prompt_length", "candidate_token_ids", "predictor_positions", "normalization_start",
                 "normalization_stop", "shared_prefix_token_count")
SCORE_KEYS = ("candidate_token_logprobs", "sequence_logprob_sum", "shared_prediction_logits_sha256",
              "shared_prediction_logits_shape", "shared_prediction_logits_dtype", "logits_hash_byte_order",
              "normalization_rectangle_shape")
CAUSAL_KEYS = ("causal_prediction_logits_sha256", "causal_prediction_logits_shape", "causal_prediction_logits_dtype")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def safe_path(path):
    path = Path(path)
    require(path.name not in PROTECTED, "Protected target may not be opened")
    # Only these exact macOS system roots exempt the leading "private";
    # any later private component is still a prohibited participant folder.
    system_roots = {("/", "private", "var"), ("/", "private", "tmp")}
    parts = path.parts[2:] if path.parts[:3] in system_roots else path.parts
    require(not set(parts) & FORBIDDEN_PARTS, "Private or environment path rejected")
    require(path.suffix not in FORBIDDEN_SUFFIXES, "Model/raw/secret payload rejected")
    resolved = path.resolve()
    resolved_parts = resolved.parts[2:] if resolved.parts[:3] in system_roots else resolved.parts
    require(resolved.name not in PROTECTED and not set(resolved_parts) & FORBIDDEN_PARTS, "Unsafe resolved input")
    require(not path.is_symlink(), "Symlink input rejected")
    return path


def relative_name(name):
    path = PurePosixPath(name)
    require(isinstance(name, str) and name and not path.is_absolute() and ".." not in path.parts and
            "\\" not in name and ":" not in name and path.as_posix() == name, "Unsafe relative name")
    require(path.name not in PROTECTED and not set(path.parts) & FORBIDDEN_PARTS and
            path.suffix not in FORBIDDEN_SUFFIXES, "Disallowed payload name")
    return name


def source_bytes(path):
    return safe_path(path).read_bytes()


def sha(path):
    return digest_bytes(source_bytes(path))


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def read(path):
    return decode(source_bytes(path))


def scan_text(text, label):
    require(LOCAL_PATH.search(text) is None, "Local/network path in " + label)
    require(SECRET.search(text) is None, "Possible credential or private packet identity in " + label)


def scan_structure(value, label):
    if isinstance(value, dict):
        require(not PRIVATE_KEYS & value.keys(), "Private field in " + label)
        for key, item in value.items():
            scan_text(str(key), label)
            scan_structure(item, label)
    elif isinstance(value, list):
        for item in value:
            scan_structure(item, label)
    elif isinstance(value, str):
        scan_text(value, label)
    elif isinstance(value, float):
        require(math.isfinite(value), "Nonfinite value in " + label)


def scan_payload(name, data):
    relative_name(name)
    if name.endswith(".pdf"):
        # Fail closed if extraction is unavailable; never silently skip a PDF.
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError("PDF privacy scan requires pypdf") from exc
        reader = PdfReader(io.BytesIO(data))
        require(not reader.is_encrypted, "Encrypted PDF cannot be inspected")
        names = reader.trailer["/Root"].get("/Names", {})
        if hasattr(names, "get_object"):
            names = names.get_object()
        require("/EmbeddedFiles" not in names and "/JavaScript" not in names, "Active/embedded PDF content rejected")
        scan_text(str(reader.metadata), name)
        for page in reader.pages:
            scan_text(page.extract_text() or "", name)
            for annotation in page.get("/Annots", []):
                scan_text(str(annotation.get_object()), name)
        scan_text(data.decode("latin1"), name)
        return "pdf_text_metadata_annotations_and_bytes_scanned"
    if name.endswith(".zip"):
        require(name == "historical/glyphprobe_t19_anonymous_evidence_v4.zip" and
                digest_bytes(data) == HISTORICAL_SHA, "Unapproved or changed opaque archive")
        return "historical_prevalidated_digest_only_not_reinspected"
    text = data.decode("utf-8")
    scan_text(text, name)
    if name.endswith(".json"):
        scan_structure(decode(text), name)
    elif name.endswith(".jsonl"):
        for line in text.splitlines():
            if line.strip():
                scan_structure(decode(line), name)
    return "utf8_privacy_name_and_path_scan"


def tex_dependencies(root):
    """Only literal relative dependencies reached from the manuscript are allowed."""
    pending, found = ["paper/main.tex"], set()
    while pending:
        name = pending.pop()
        relative_name(name)
        require(name.startswith("paper/") and Path(name).suffix in {".tex", ".bib", ".pdf"}, "TeX dependency out of scope")
        if name in found:
            continue
        path = safe_path(root / name)
        require(path.resolve().is_relative_to((root / "paper").resolve()), "TeX dependency escapes paper")
        data = source_bytes(path)
        found.add(name)
        if name.endswith(".tex"):
            # This project resolves inputs from paper/, not the input file's folder.
            for command, value in re.findall(r"\\(input|include|includegraphics|bibliography)(?:\[[^\]]*\])?\{([^}]+)\}", data.decode()):
                require(not any(c in value for c in "\\#$%"), "Nonliteral TeX dependency")
                for item in value.split(","):
                    item = item.strip()
                    suffix = ".pdf" if command == "includegraphics" else ".bib" if command == "bibliography" else ".tex"
                    child = "paper/" + (item if Path(item).suffix else item + suffix)
                    relative_name(child)
                    pending.append(child)
    return sorted(found)


def selected(value, fields):
    require(isinstance(value, dict) and all(k in value for k in fields), "Projection source fields missing")
    return {k: value[k] for k in fields}


def project_specification(spec):
    fields = ("protocol_id", "inventory_sha256", "tokenized_inputs_sha256", "primary", "label_robustness_gate",
              "planned_pairs", "planned_scientific_sequence_scores", "planned_sentinel_forwards",
              "planned_forward_attempts", "independent_fact_roots", "split_roots", "qualification_scoring")
    result = selected(spec, fields)
    result["inputs"] = [selected(row, LOGICAL_KEYS) | {
        "candidates": {k: selected(row["candidates"][k], CANDIDATE_KEYS) for k in ("a", "b")},
        **selected(row, ("shared_prefix_token_count", "causal_predictor_token_count"))} for row in spec["inputs"]]
    result["sentinels"] = [{"input_id": row["input_id"], "shared_prefix_token_count": row["shared_prefix_token_count"],
        "candidates": {k: selected(row["candidates"][k], CANDIDATE_KEYS) for k in ("a", "b")},
        "expected_scores": {k: selected(row["expected_scores"][k], SCORE_KEYS) for k in ("padded_a", "padded_b")}}
        for row in spec["sentinels"]]
    return result


def project_record(row):
    result = selected(row, ("event_id", "phase", "input_id", "method", "status", "forward_attempted"))
    result["geometry"] = selected(row["geometry"], GEOMETRY_KEYS)
    if row["status"] == "completed":
        result.update(selected(row, SCORE_KEYS))
        if row["phase"] == "qualification":
            result.update(selected(row, CAUSAL_KEYS))
    # Preserve whether a boundary error occurred, never include machine paths in its text.
    if "boundary_error_after_score" in row:
        result["boundary_error_after_score"] = "See locally retained raw receipt; error text omitted from public projection."
    return result


def load_module(root, name, relative_path):
    path = safe_path(root / relative_path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def load_analyzer(root):
    return load_module(root, "release_readout_qualification", "scripts/readout_qualification_v1.py")


def load_validator(root):
    return load_module(root, "release_independent_readout_validator", "scripts/validate_readout_qualification_v1.py")


def independent_public_result(root, spec, records, analysis, invalid_run=False):
    """Adapter to the unchanged independent arithmetic implementation.

    Only complete, numerically accepted records satisfy that checker's contract.
    Incomplete runs remain packageable as incomplete evidence, never as a pass.
    """
    if invalid_run or not analysis["numerical_gate_passed"]:
        result = {"status": "not_evaluable_incomplete_or_numerical_gate_failed",
            "independent_arithmetic_validation_passed": None,
            "reason": "Independent complete-run checker requires a complete numerically accepted run.",
            "model_forwards": 0, "tokenizer_calls": 0, "independent_reacquisition": False}
    else:
        result = load_validator(root).recompute(spec, records, analysis)
        result["status"] = "independently_recomputed_public_projection"
    result["public_projection_binding"] = {
        "validator_source_sha256": sha(root / "scripts/validate_readout_qualification_v1.py"),
        "specification_public_sha256": digest_bytes(canonical(spec)),
        "forwards_public_sha256": digest_bytes(b"".join(canonical_line(r) for r in records)),
        "analysis_public_sha256": digest_bytes(canonical(analysis)),
        "adapter": "direct_recompute_on_explicit_public_projection_v1",
        "scientific_logic_changed": False, "raw_receipts_edited": False,
    }
    return result


def portable_run(root, specification, run_directory, expected_sha):
    """Bind originals, project only public fields, replay and compare before writing."""
    require(isinstance(expected_sha, str) and re.fullmatch(r"[0-9a-f]{64}", expected_sha), "Externally retained specification hash required")
    require(sha(specification) == expected_sha, "Externally pinned specification hash differs")
    spec = read(specification)
    receipt_path = run_directory / "run_completed.json"
    receipt = read(receipt_path)
    require(receipt["specification_sha256"] == sha(specification), "Run/specification binding differs")
    require(receipt["source_files"] == spec["source_files"], "Run/source binding differs")
    require(set(receipt["artifacts"]) <= RUN_FILES and {"forwards.jsonl", "analysis.json", "run_started.json"} <= set(receipt["artifacts"]),
            "Unexpected or missing run artifacts")
    raw_hashes = {"specification.json": sha(specification), "run_completed.json": sha(receipt_path)}
    for name, expected in receipt["artifacts"].items():
        relative_name(name)
        require(Path(name).name == name and sha(run_directory / name) == expected, "Raw artifact hash differs")
        raw_hashes[name] = expected
    started = read(run_directory / "run_started.json")
    require(started["protocol_id"] == spec["protocol_id"] and started["specification_sha256"] == expected_sha and
            started["source_files"] == spec["source_files"], "Started-run binding differs")
    for name, expected in spec["source_files"].items():
        relative_name(name)
        require(name in STATIC_FILES and sha(root / name) == expected, "Bound source is missing, unapproved, or changed: " + name)
    analyzer = load_analyzer(root)
    analyzer.validate_inputs(spec["inputs"])
    require(analyzer.object_sha(analyzer.inventory()) == spec["inventory_sha256"] and
            analyzer.object_sha(spec["inputs"]) == spec["tokenized_inputs_sha256"], "Inventory digest differs")
    records = [decode(line) for line in source_bytes(run_directory / "forwards.jsonl").splitlines() if line.strip()]
    public_spec = project_specification(spec)
    public_records = [project_record(row) for row in records]
    original_analysis = analyzer.analyze(spec, records)
    replay = analyzer.analyze(public_spec, public_records)
    require(original_analysis == replay, "Portable projection changes analysis")
    saved_analysis = read(run_directory / "analysis.json")
    if receipt["stop_reason"] is not None:
        # A source/specification error can invalidate otherwise complete scores.
        for result in (original_analysis, replay):
            result.update(numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
                          qualification_status="not_evaluable_numerical_or_incomplete")
        saved_analysis = {k: v for k, v in saved_analysis.items() if k != "execution_error"}
    require(saved_analysis == replay, "Saved analysis differs from score replay")
    for key in ("numerical_gate_passed", "primary_qualification_passed", "label_robustness_passed", "qualification_status", "completed_pairs", "status_counts"):
        require(receipt[key] == replay[key], "Completion receipt differs from replay: " + key)
    independent = independent_public_result(root, public_spec, public_records, replay, receipt["stop_reason"] is not None)
    if independent["independent_arithmetic_validation_passed"] is True:
        raw_check = load_validator(root).recompute(spec, records, original_analysis)
        public_check = {k: v for k, v in independent.items() if k not in ("status", "public_projection_binding")}
        require(raw_check == public_check, "Independent arithmetic changes after public projection")
    public_receipt = selected(receipt, ("protocol_id", "status", "forward_attempts", "planned_forward_attempts",
        "elapsed_seconds", "numerical_gate_passed", "primary_qualification_passed", "label_robustness_passed",
        "qualification_status", "completed_pairs", "status_counts", "peak_torch_memory_mib", "downloads", "generation_calls"))
    public_receipt["source_binding_or_execution_failure"] = receipt["stop_reason"] is not None
    dependencies = {"model_artifact_hashes_only": spec["model_artifact"], "runtime_packages": spec["runtime_packages"],
        "python_version": spec["python_version"], "scoring": spec["scoring"],
        "implementation_source_hashes": {k: {"sha256": v["sha256"]} for k, v in spec["expected_implementation_sources"]["files"].items()},
        "model_files_included": False, "bitwise_reacquisition_claimed": False}
    binding = {"raw_sha256": raw_hashes, "source_sha256": spec["source_files"],
        "projection_policy": "explicit_field_allowlist_v1", "raw_receipts_edited": False,
        "local_paths_and_host_process_metadata_omitted": True,
        "private_participant_records_read": False, "model_forwards_for_projection": 0,
        "scope": "Exact CPU replay of saved-score statistics and recorded equality gates; no independent recomputation of GPU logits."}
    base = "evidence/readout_qualification_v1/"
    return {
        base + "specification.public.json": canonical(public_spec),
        base + "forwards.public.jsonl": b"".join(canonical_line(r) for r in public_records),
        base + "analysis.public.json": canonical(replay),
        base + "run_summary.public.json": canonical(public_receipt),
        base + "runtime_dependencies.public.json": canonical(dependencies),
        base + "projection_binding.json": canonical(binding),
        base + "independent_validation.public.json": canonical(independent),
    }


def canonical_line(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()


def license_classification(name):
    if name == "LICENSE":
        return "Apache-2.0_license_text"
    if name.endswith("UNICODE_LICENSE.txt"):
        return "Unicode-3.0_notice"
    if name.startswith("historical/"):
        return "historical_mixed_assets_see_embedded_notices_no_new_license_grant"
    if name == "paper/revised_preprint.pdf" or name.endswith((".tex", ".bib", ".pdf")):
        return "paper_related_asset_CC-BY-4.0_proposed_author_confirmation_pending"
    if name.startswith("evidence/") or name.endswith((".json", ".jsonl")):
        return "derived_research_record_release_license_pending"
    return "Apache-2.0_project_code_or_documentation_existing_repository_license"


def collect(root, pdf, specification, run_directory, expected_sha):
    payload = {name: source_bytes(root / name) for name in sorted(set(STATIC_FILES) | set(tex_dependencies(root)))}
    payload["paper/revised_preprint.pdf"] = source_bytes(pdf)
    payload["README.md"] = source_bytes(root / "paper/RELEASE_CANDIDATE_20261015.md").replace(
        b"(RELEASE_CANDIDATE_20261015.ja.md)", b"(README.ja.md)")
    payload["README.ja.md"] = source_bytes(root / "paper/RELEASE_CANDIDATE_20261015.ja.md").replace(
        b"(RELEASE_CANDIDATE_20261015.md)", b"(README.md)")
    archive = source_bytes(root / HISTORICAL)
    require(digest_bytes(archive) == HISTORICAL_SHA, "Historical archive changed")
    payload["historical/glyphprobe_t19_anonymous_evidence_v4.zip"] = archive
    payload["DEPENDENCIES.json"] = canonical({
        "neurips_style": {"included": False, "reason": "Redistribution permission not established by this package.",
            "official_archive_url": FORMAT_URL, "official_archive_sha256": FORMAT_SHA,
            "style_file": "paper/neurips_2026.sty", "style_sha256": sha(root / "paper/neurips_2026.sty")},
        "pdf_scan_builder_dependency": "pypdf (not vendored)",
        "public_score_replay_dependencies": "Python standard library only",
        "external_model_assets_included": False,
    })
    payload.update(portable_run(root, specification, run_directory, expected_sha))
    bindings = decode(payload["evidence/readout_qualification_v1/projection_binding.json"])
    for name, expected in bindings["source_sha256"].items():
        require(name in payload and digest_bytes(payload[name]) == expected, "Packaged source differs from acquisition source: " + name)
    return payload


def bundle(payload, output):
    output = Path(output)
    require(not output.exists(), "Output already exists; choose a new candidate path")
    entries = []
    for name, data in sorted(payload.items()):
        scan = scan_payload(name, data)
        entries.append({"path": name, "bytes": len(data), "sha256": digest_bytes(data),
                        "license_classification": license_classification(name), "privacy_check": scan})
    manifest = {"schema_version": 1, "artifact_id": ARTIFACT_ID, "status": "local_release_candidate_not_published",
        "public_deposit": False, "doi_reserved_or_registered": False, "paper_license_confirmed": False,
        "archive_timestamp_is_reproducibility_constant_not_event_time": True,
        "reproducibility_timestamp_utc": "2026-10-15T00:00:00Z", "payload_files": len(entries), "files": entries,
        "scientific_claim": "Packaging integrity and saved-score replay are separate from scientific validity.",
        "human_evidence_boundary": "Aggregate author tryout only; individual answers/assignments/notes are excluded and not independently reproducible.",
        "historical_boundary": "Nested September archive is immutable historical evidence, not the current paper or a refreshed release."}
    manifest_data = canonical(manifest)
    checksums = {name: digest_bytes(data) for name, data in payload.items()}
    checksums["ARTIFACT_MANIFEST.json"] = digest_bytes(manifest_data)
    sums = "".join(f"{checksums[n]}  {n}\n" for n in sorted(checksums)).encode()
    # All checks happen before creation; exclusive mode prevents overwriting receipts.
    output.parent.mkdir(parents=True, exist_ok=True)
    archive_payload = {**payload, "ARTIFACT_MANIFEST.json": manifest_data, "SHA256SUMS": sums}
    with output.open("xb") as handle:
        with zipfile.ZipFile(handle, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(archive_payload.items()):
                info = zipfile.ZipInfo(ARTIFACT_ID + "/" + name, date_time=FIXED_TIME)
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, data, compresslevel=9)
    return {"status": manifest["status"], "archive_bytes": output.stat().st_size, "archive_sha256": sha(output),
            "payload_files": len(entries), "published": False, "doi_action": False}


def verify_directory(directory):
    directory = Path(directory).resolve()
    manifest = read(directory / "ARTIFACT_MANIFEST.json")
    expected = {row["path"] for row in manifest["files"]} | {"ARTIFACT_MANIFEST.json", "SHA256SUMS"}
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    require(actual == expected, "Extracted entry roster differs (verify before Python creates bytecode)")
    for row in manifest["files"]:
        path = directory / relative_name(row["path"])
        data = source_bytes(path)
        require(len(data) == row["bytes"] and digest_bytes(data) == row["sha256"], "Payload differs: " + row["path"])
    sums = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in source_bytes(directory / "SHA256SUMS").decode().splitlines()}
    require(set(sums) == expected - {"SHA256SUMS"}, "Checksum roster differs")
    require(all(sha(directory / relative_name(name)) == expected_hash for name, expected_hash in sums.items()), "Checksum mismatch")
    base = directory / "evidence/readout_qualification_v1"
    analyzer = load_analyzer(directory)
    spec = read(base / "specification.public.json")
    analyzer.validate_inputs(spec["inputs"])
    records = [decode(line) for line in source_bytes(base / "forwards.public.jsonl").splitlines()]
    result = analyzer.analyze(spec, records)
    summary = read(base / "run_summary.public.json")
    if summary["source_binding_or_execution_failure"]:
        result.update(numerical_gate_passed=False, primary_qualification_passed=False, label_robustness_passed=False,
                      qualification_status="not_evaluable_numerical_or_incomplete")
    require(result == read(base / "analysis.public.json"), "Saved-score replay differs")
    independent = independent_public_result(directory, spec, records, result, summary["source_binding_or_execution_failure"])
    require(independent == read(base / "independent_validation.public.json"), "Independent public-score replay differs")
    return {"status": "package_integrity_and_saved_score_replay_passed", "model_forwards": 0,
            "numerical_gate_passed": result["numerical_gate_passed"],
            "primary_qualification_passed": result["primary_qualification_passed"],
            "independent_arithmetic_validation_passed": independent["independent_arithmetic_validation_passed"],
            "not_independent_logit_reconstruction": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--root", type=Path, default=ROOT)
    build.add_argument("--pdf", type=Path, required=True)
    build.add_argument("--specification", type=Path, required=True)
    build.add_argument("--expected-specification-sha256", required=True)
    build.add_argument("--run-directory", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        require(not args.output.exists(), "Output already exists")
        result = bundle(collect(args.root.resolve(), args.pdf, args.specification, args.run_directory,
                                args.expected_specification_sha256), args.output)
    else:
        result = verify_directory(args.directory)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
