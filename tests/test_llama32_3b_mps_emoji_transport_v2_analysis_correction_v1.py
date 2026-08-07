from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CORRECTION = _load_module(
    "llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_tested",
    "scripts/llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py",
)
ANALYZER = _load_module(
    "analyze_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_tested",
    "scripts/analyze_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py",
)
AUDIT = _load_module(
    "audit_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1_tested",
    "scripts/audit_llama32_3b_mps_emoji_transport_v2_analysis_correction_v1.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _long_run(_tmp_path: Path) -> Path:
    # Keep the synthetic absolute prefix short enough that the width-80 split
    # lands inside the run ID, matching every admitted production launcher log.
    # The parser and projection adapter do not require the run directory to
    # exist; only the independently bound launcher log is opened here.
    run = Path("/private/tmp/glyphprobe-v2-test") / (
        "e2-llama32-3b-mps-full50-sky-transport-v2--transformers--"
        "mlx-community-Llama-3.2-3B-bf16--0123456789abcdef"
    )
    encoded = str(run.resolve()).encode("utf-8")
    assert 80 < len(encoded) <= 160
    assert run.name.encode("utf-8") not in encoded[:80]
    assert run.name.encode("utf-8") not in encoded[80:]
    return run


def _wrapped_payload(run: Path) -> bytes:
    encoded = str(run.resolve()).encode("utf-8")
    return b"prefix\nComplete  \n" + encoded[:80] + b"\n" + encoded[80:] + b"\n{\n"


def test_exact_parser_accepts_only_marker_plus_two_path_lines(tmp_path: Path) -> None:
    run = _long_run(tmp_path)
    record = CORRECTION.parse_completion_wrap(
        _wrapped_payload(run),
        expected_run_dir=run,
        expected_run_id=run.name,
    )
    assert record == {
        "parser_contract": CORRECTION.PARSER_CONTRACT,
        "status": "accepted",
        "wrap_width": 80,
        "segment_count": 2,
        "segment_lengths": [80, len(str(run.resolve()).encode("utf-8")) - 80],
        "raw_contiguous_path_match": False,
        "raw_contiguous_run_id_match": False,
    }


@pytest.mark.parametrize(
    "mutation, error",
    [
        ("contiguous", "already contiguous"),
        ("wrong_byte", "Reconstructed completion path differs"),
        ("duplicate", "exactly one marker-only"),
        ("ansi", "ANSI escape bytes"),
        ("short_first", "exactly 80 bytes"),
        ("three_fragments", "top-level JSON"),
    ],
)
def test_exact_parser_rejects_near_misses(
    tmp_path: Path, mutation: str, error: str
) -> None:
    run = _long_run(tmp_path)
    encoded = str(run.resolve()).encode("utf-8")
    payload = _wrapped_payload(run)
    if mutation == "contiguous":
        payload = b"Complete  " + encoded + b"\n{\n"
    elif mutation == "wrong_byte":
        replacement = b"f" if encoded[-1:] != b"f" else b"e"
        payload = (
            b"prefix\nComplete  \n"
            + encoded[:80]
            + b"\n"
            + encoded[80:-1]
            + replacement
            + b"\n{\n"
        )
    elif mutation == "duplicate":
        payload = payload + payload
    elif mutation == "ansi":
        payload = payload.replace(encoded[:1], b"\x1b" + encoded[:1], 1)
    elif mutation == "short_first":
        payload = b"Complete  \n" + encoded[:79] + b"\n" + encoded[79:] + b"\n{\n"
    elif mutation == "three_fragments":
        payload = (
            b"Complete  \n"
            + encoded[:80]
            + b"\n"
            + encoded[80:90]
            + b"\n"
            + encoded[90:]
            + b"\n{\n"
        )
    with pytest.raises(CORRECTION.AnalysisCorrectionError, match=error):
        CORRECTION.parse_completion_wrap(
            payload,
            expected_run_dir=run,
            expected_run_id=run.name,
        )


def test_exact_parser_rejects_wrong_run_id(tmp_path: Path) -> None:
    run = _long_run(tmp_path)
    with pytest.raises(
        CORRECTION.AnalysisCorrectionError,
        match="does not match the resolved directory basename",
    ):
        CORRECTION.parse_completion_wrap(
            _wrapped_payload(run),
            expected_run_dir=run,
            expected_run_id="wrong-run-id",
        )


def test_frozen_base_analyzer_and_scientific_constants_are_reused() -> None:
    assert _sha256(ROOT / ANALYZER.BASE_ANALYZER_PATH) == ANALYZER.BASE_ANALYZER_SHA256
    assert _sha256(ROOT / ANALYZER.HELPER_PATH) == ANALYZER.HELPER_SHA256
    assert ANALYZER.ANALYSIS_ID == CORRECTION.BASE_PROTOCOL_ID
    assert ANALYZER.BOOTSTRAP_REPLICATES == 20_000
    assert ANALYZER.BOOTSTRAP_SEED == 20_260_808
    assert ANALYZER.PRIMARY_CRITERION_ID == ANALYZER.base.PRIMARY_CRITERION_ID
    assert ANALYZER.PRIMARY_CRITERION_RULE == ANALYZER.base.PRIMARY_CRITERION_RULE


def test_projection_delegates_to_original_validator_and_deletes_temp_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path.resolve()
    run = _long_run(root)
    log = root / "runs" / "launcher.log"
    log.parent.mkdir(parents=True)
    log.write_bytes(_wrapped_payload(run))
    original = log.read_bytes()
    expected_log_sha256 = _sha256(log)
    original_read_bytes = Path.read_bytes
    source_reads = 0

    def read_bytes_once(path: Path) -> bytes:
        nonlocal source_reads
        if path == log:
            source_reads += 1
            return original if source_reads == 1 else b"concurrent replacement"
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes_once)
    runs = [
        {
            "panel_arm": "full50",
            "role": "sky",
            "run_dir": run,
            "run_id": run.name,
        }
    ]
    binding = {
        "processes": [
            {
                "panel_arm": "full50",
                "role": "sky",
                "log_path": "runs/launcher.log",
                "log_sha256": expected_log_sha256,
            }
        ]
    }
    projected: list[Path] = []

    def original_validator(run_rows: Any, execution: Any, validator_root: Path) -> None:
        assert run_rows is runs
        assert validator_root == root
        candidate = Path(execution["processes"][0]["log_path"])
        projected.append(candidate)
        assert candidate.read_bytes() == b"Complete  " + str(run).encode() + b"\n"

    ANALYZER._corrected_validate_runs_against_execution(
        runs,
        binding,
        root,
        original_validator=original_validator,
    )
    assert len(projected) == 1 and not projected[0].exists()
    assert source_reads == 1
    assert original_read_bytes(log) == original


def test_source_log_rejects_symlink(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    source = root / "source.log"
    source.write_bytes(b"x")
    link = root / "linked.log"
    link.symlink_to(source)
    with pytest.raises(ANALYZER.TransportAnalysisError, match="missing or unsafe"):
        ANALYZER._source_log(
            root,
            {"log_path": "linked.log", "log_sha256": _sha256(source)},
            "cell",
        )


def test_audit_hashes_and_parses_the_same_single_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.resolve()
    rows: list[dict[str, Any]] = []
    originals: dict[Path, bytes] = {}
    reads: dict[Path, int] = {}
    parsed: list[bytes] = []
    for index, (arm, role) in enumerate(CORRECTION.CELL_ORDER):
        run = root / "runs" / f"run-{index}"
        run.mkdir(parents=True)
        log = (root / "logs" / f"{index}.log").resolve()
        log.parent.mkdir(parents=True, exist_ok=True)
        payload = f"launcher-{index}".encode("ascii")
        log.write_bytes(payload)
        originals[log] = payload
        reads[log] = 0
        rows.append(
            {
                "index": index,
                "panel_arm": arm,
                "role": role,
                "path": log.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "expected_run_relative_path": run.relative_to(root).as_posix(),
                "expected_run_id": run.name,
                "wrap_width": 80,
                "segment_count": 2,
            }
        )

    original_read_bytes = Path.read_bytes

    def read_bytes_once(path: Path) -> bytes:
        resolved = path.resolve()
        if resolved in reads:
            reads[resolved] += 1
            return (
                originals[resolved]
                if reads[resolved] == 1
                else b"concurrent replacement"
            )
        return original_read_bytes(path)

    def parser(
        payload: bytes, *, expected_run_dir: Path, expected_run_id: str
    ) -> dict[str, Any]:
        assert expected_run_dir.name == expected_run_id
        parsed.append(payload)
        return {"status": "accepted"}

    monkeypatch.setattr(Path, "read_bytes", read_bytes_once)
    monkeypatch.setattr(AUDIT.correction, "parse_completion_wrap", parser)
    records = AUDIT._completion_records(root, {"launcher_logs": rows})
    assert len(records) == 10
    assert parsed == [originals[path] for path in sorted(originals)]
    assert set(reads.values()) == {1}


@pytest.mark.parametrize("base_raises", [False, True])
def test_analyzer_restores_scoped_patches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    base_raises: bool,
) -> None:
    original_validator = ANALYZER.base.v1._validate_runs_against_execution
    original_writer = ANALYZER.base.v1._write_json
    monkeypatch.setattr(
        ANALYZER.correction,
        "validate_correction_manifest",
        lambda root: {"ok": True},
    )
    monkeypatch.setattr(
        ANALYZER.correction,
        "validate_correction_preflight",
        lambda root, manifest: {"status": "passed"},
    )
    expected_block = {"correction_id": ANALYZER.CORRECTION_ID}
    monkeypatch.setattr(
        ANALYZER.correction,
        "analysis_validation_correction_block",
        lambda root, adapter_path: expected_block,
    )
    written: list[dict[str, Any]] = []

    def writer(path: Path, value: dict[str, Any]) -> None:
        written.append(dict(value))

    monkeypatch.setattr(ANALYZER.base.v1, "_write_json", writer)

    def base_analysis(*args: Any) -> dict[str, Any]:
        assert (
            ANALYZER.base.v1._validate_runs_against_execution is not original_validator
        )
        assert ANALYZER.base.v1._write_json is not writer
        if base_raises:
            raise ANALYZER.TransportAnalysisError("stop")
        receipt = {"analysis_id": ANALYZER.ANALYSIS_ID, "output_inventory": []}
        ANALYZER.base.v1._write_json(
            Path(ANALYZER.base.V1_OUTPUT_RECEIPT_FILENAME), receipt
        )
        return receipt

    monkeypatch.setattr(ANALYZER.base, "analyze_transport", base_analysis)
    args = [tmp_path / f"run-{index}" for index in range(10)]
    if base_raises:
        with pytest.raises(ANALYZER.TransportAnalysisError, match="stop"):
            ANALYZER.analyze_transport(*args, tmp_path / "analysis")
    else:
        receipt = ANALYZER.analyze_transport(*args, tmp_path / "analysis")
        assert receipt[ANALYZER.CORRECTION_KEY] == expected_block
        assert written[0][ANALYZER.CORRECTION_KEY] == expected_block
    assert ANALYZER.base.v1._validate_runs_against_execution is original_validator
    assert ANALYZER.base.v1._write_json is writer
    monkeypatch.setattr(ANALYZER.base.v1, "_write_json", original_writer)


def test_audit_atomic_publication_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    AUDIT.atomic_no_overwrite(output, {"status": "first"})
    original = output.read_bytes()
    with pytest.raises(
        AUDIT.AnalysisCorrectionError,
        match="Refusing to overwrite",
    ):
        AUDIT.atomic_no_overwrite(output, {"status": "second"})
    assert output.read_bytes() == original
    assert json.loads(output.read_text(encoding="utf-8")) == {"status": "first"}
