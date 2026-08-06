from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Callable

import pytest


_BUNDLE_SCRIPT = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "build_public_artifact_bundle.py"
    ),
    run_name="glyphprobe_public_bundle_test",
)
_assert_public_safe = _BUNDLE_SCRIPT["_assert_public_safe"]
_build = _BUNDLE_SCRIPT["build"]
_COMPACT_RUN_FILES = _BUNDLE_SCRIPT["COMPACT_RUN_FILES"]


def _write_json_value(path: Path, value: str) -> None:
    path.write_text(json.dumps({"value": value}) + "\n", encoding="utf-8")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle_inputs(tmp_path: Path) -> dict[str, Path]:
    run_id = "test-run--0123456789abcdef"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    parity_path = tmp_path / "parity.json"
    audit_path = tmp_path / "audit.json"
    implementation_sha = "a" * 64
    model_identity_sha = "b" * 64
    model = "openai-community/gpt2"
    revision = "c" * 40
    layers = [2, 4, 7, 9]
    prompt_token_counts = [3, 9, 10, 22]

    parity = {
        "status": "validated_mlx_selected",
        "model": model,
        "revision": revision,
        "dtype": "float32",
        "site": "resid_post",
        "intervention_layers": layers,
        "mlx_model_identity_sha256": model_identity_sha,
        "implementation": {"source_tree_sha256": implementation_sha},
        "benchmark": {
            "prompt_token_counts": prompt_token_counts,
            "speed_gate": {"pass": True},
        },
        "parity": {
            "pass": True,
            "checks": [{"id": "parity", "pass": True}],
            "passed": 1,
            "total": 1,
        },
    }
    _write_json(parity_path, parity)
    parity_sha = _sha256(parity_path)

    run_receipt = {
        "status": "complete",
        "run_id": run_id,
        "run_seal": "0123456789abcdef",
        "claim_boundary": "pre-causal-activation-screen",
        "backend": {
            "kind": "mlx",
            "model": model,
            "revision": revision,
            "dtype": "float32",
            "validation_receipt_sha256": parity_sha,
        },
        "input_hashes": {"input_01:receipt.json": parity_sha},
        "implementation": {"source_tree_sha256": implementation_sha},
        "model_receipt": {
            "model": model,
            "revision": revision,
            "dtype": "float32",
            "parity_validation": {
                "validated": True,
                "receipt_sha256": parity_sha,
                "receipt_status": "validated_mlx_selected",
                "implementation_sha256": implementation_sha,
                "model_identity_sha256": model_identity_sha,
                "validated_site": "resid_post",
                "validated_intervention_layers": layers,
                "validated_prompt_token_counts": prompt_token_counts,
            },
        },
        "plan": {
            "claim_boundary": "pre-causal-activation-screen",
            "resolved_layers": layers,
        },
    }
    _write_json(run_dir / "receipt.json", run_receipt)
    _write_json(run_dir / "summary.json", {"causal_claim_authorized": False})

    audit = {
        "status": "ready_with_caveats",
        "run_id": run_id,
        "run_dir": run_id,
        "causal_claim_authorized": False,
        "scientific_result": True,
        "checks": [{"id": "integrity", "pass": True}],
        "passed": 1,
        "total": 1,
    }
    _write_json(audit_path, audit)

    for name in _COMPACT_RUN_FILES:
        path = run_dir / name
        if path.exists():
            continue
        if path.suffix == ".json":
            _write_json(path, {})
        elif path.suffix == ".jsonl":
            path.write_text("{}\n", encoding="utf-8")
        elif path.suffix in {".yaml", ".yml"}:
            path.write_text("{}\n", encoding="utf-8")
        else:
            path.write_text("Portable compact report.\n", encoding="utf-8")
    return {
        "run_dir": run_dir,
        "parity_receipt": parity_path,
        "audit_receipt": audit_path,
        "output_dir": tmp_path / "public",
    }


def _mutate_json(path: Path, mutation: Callable[[dict], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    _write_json(path, value)


def _assert_build_rejected(inputs: dict[str, Path], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _build(**inputs)
    assert not inputs["output_dir"].exists()


@pytest.mark.parametrize(
    "absolute_path",
    [
        "/mnt/research/run/receipt.json",
        "/var/tmp/glyphprobe/summary.json",
        "/Users/example/model-cache/config.json",
        "/",
    ],
)
def test_public_bundle_rejects_any_posix_absolute_path(
    tmp_path: Path, absolute_path: str
) -> None:
    artifact = tmp_path / "artifact.json"
    _write_json_value(artifact, absolute_path)
    with pytest.raises(ValueError, match="local absolute path"):
        _assert_public_safe(artifact)


@pytest.mark.parametrize(
    "absolute_path",
    [
        r"C:\Users\example\glyphprobe\receipt.json",
        "D:/models/gpt2/config.json",
        r"\\server\share\glyphprobe\summary.json",
    ],
)
def test_public_bundle_rejects_windows_absolute_path(
    tmp_path: Path, absolute_path: str
) -> None:
    artifact = tmp_path / "artifact.json"
    _write_json_value(artifact, absolute_path)
    with pytest.raises(ValueError, match="local absolute path"):
        _assert_public_safe(artifact)


def test_public_bundle_rejects_absolute_path_embedded_in_markdown(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "report.md"
    artifact.write_text(
        "The source receipt was read from `/mnt/private/run/receipt.json`.\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="local absolute path"):
        _assert_public_safe(artifact)


def test_public_bundle_rejects_local_file_uri(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    _write_json_value(artifact, "file:///mnt/private/run/receipt.json")
    with pytest.raises(ValueError, match="local absolute path"):
        _assert_public_safe(artifact)


@pytest.mark.parametrize(
    "portable_reference",
    [
        "artifacts/v1_standard_mlx/receipt.json",
        "../validation/mlx_gpt2_parity/receipt.json",
        r"relative\windows\receipt.json",
        r"C:relative\receipt.json",
        "$WORKSPACE/runs/receipt.json",
        "https://example.org/artifacts/v1/receipt.json",
        "s3://public-bucket/glyphprobe/receipt.json",
        "hf://models/example/gpt2/config.json",
        "downloads://glyphprobe/run/receipt.json",
        "urn:sha256:68d232ffffd5afd9",
        "1/1001",
    ],
)
def test_public_bundle_allows_relative_paths_and_portable_uris(
    tmp_path: Path, portable_reference: str
) -> None:
    artifact = tmp_path / "artifact.json"
    _write_json_value(artifact, portable_reference)
    _assert_public_safe(artifact)


def test_public_bundle_accepts_coherent_receipts_before_copy(tmp_path: Path) -> None:
    inputs = _bundle_inputs(tmp_path)
    manifest = _build(**inputs)
    assert manifest["source_run_id"] == inputs["run_dir"].name
    assert manifest["causal_claim_authorized"] is False
    assert (inputs["output_dir"] / "v1_standard_mlx" / "receipt.json").is_file()


def test_public_bundle_rejects_incomplete_run_before_copy(tmp_path: Path) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(inputs["run_dir"] / "receipt.json", lambda row: row.update(status="running"))
    _assert_build_rejected(inputs, "status must be complete")


def test_public_bundle_rejects_old_audit_for_new_run_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)

    def use_old_run(row: dict) -> None:
        row["run_id"] = "old-run--fedcba9876543210"
        row["run_dir"] = row["run_id"]

    _mutate_json(inputs["audit_receipt"], use_old_run)
    _assert_build_rejected(inputs, "Audit run_id does not match")


def test_public_bundle_rejects_mismatched_audit_run_dir_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["audit_receipt"],
        lambda row: row.update(run_dir="different-run--0000000000000000"),
    )
    _assert_build_rejected(inputs, "Audit run_dir does not match")


def test_public_bundle_rejects_unready_audit_status_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["audit_receipt"], lambda row: row.update(status="failed")
    )
    _assert_build_rejected(inputs, "Audit status")


def test_public_bundle_rejects_failed_audit_check_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["audit_receipt"],
        lambda row: row["checks"][0].update({"pass": False}),
    )
    _assert_build_rejected(inputs, "failed or malformed check")


def test_public_bundle_rejects_non_scientific_audit_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["audit_receipt"],
        lambda row: row.update(scientific_result=False),
    )
    _assert_build_rejected(inputs, "scientific_result true")


def test_public_bundle_rejects_failed_parity_status_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["parity_receipt"], lambda row: row.update(status="parity_failed")
    )
    _assert_build_rejected(inputs, "Parity status")


def test_public_bundle_rejects_failed_parity_gate_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)

    def fail_gate(row: dict) -> None:
        row["parity"]["pass"] = False
        row["parity"]["checks"][0]["pass"] = False
        row["parity"]["passed"] = 0

    _mutate_json(inputs["parity_receipt"], fail_gate)
    _assert_build_rejected(inputs, "overall passing gate")


def test_public_bundle_rejects_failed_parity_speed_gate_before_copy(
    tmp_path: Path,
) -> None:
    inputs = _bundle_inputs(tmp_path)
    _mutate_json(
        inputs["parity_receipt"],
        lambda row: row["benchmark"]["speed_gate"].update({"pass": False}),
    )
    _assert_build_rejected(inputs, "speed gate must explicitly pass")


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ("backend", "backend parity SHA"),
        ("input", "input hashes"),
        ("model", "model parity SHA"),
    ],
)
def test_public_bundle_rejects_parity_sha_mismatch_before_copy(
    tmp_path: Path, target: str, message: str
) -> None:
    inputs = _bundle_inputs(tmp_path)
    receipt_path = inputs["run_dir"] / "receipt.json"

    def mismatch(row: dict) -> None:
        if target == "backend":
            row["backend"]["validation_receipt_sha256"] = "0" * 64
        elif target == "input":
            row["input_hashes"]["input_01:receipt.json"] = "0" * 64
        else:
            row["model_receipt"]["parity_validation"]["receipt_sha256"] = "0" * 64

    _mutate_json(receipt_path, mismatch)
    _assert_build_rejected(inputs, message)


@pytest.mark.parametrize("receipt_name", ["audit_receipt", "summary"])
def test_public_bundle_rejects_causal_authorization_before_copy(
    tmp_path: Path, receipt_name: str
) -> None:
    inputs = _bundle_inputs(tmp_path)
    path = (
        inputs["audit_receipt"]
        if receipt_name == "audit_receipt"
        else inputs["run_dir"] / "summary.json"
    )
    _mutate_json(path, lambda row: row.update(causal_claim_authorized=True))
    _assert_build_rejected(inputs, "causal_claim_authorized false")


@pytest.mark.parametrize(
    ("metadata", "message"),
    [
        ("implementation", "implementation identity"),
        ("model_identity", "model identity"),
        ("scope", "parity scope"),
        ("model", "model metadata"),
    ],
)
def test_public_bundle_rejects_model_parity_metadata_mismatch_before_copy(
    tmp_path: Path, metadata: str, message: str
) -> None:
    inputs = _bundle_inputs(tmp_path)
    receipt_path = inputs["run_dir"] / "receipt.json"

    def mismatch(row: dict) -> None:
        parity = row["model_receipt"]["parity_validation"]
        if metadata == "implementation":
            parity["implementation_sha256"] = "0" * 64
        elif metadata == "model_identity":
            parity["model_identity_sha256"] = "0" * 64
        elif metadata == "scope":
            parity["validated_site"] = "resid_pre"
        else:
            row["model_receipt"]["model"] = "different/model"

    _mutate_json(receipt_path, mismatch)
    _assert_build_rejected(inputs, message)
