#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Iterator

import yaml


COMPACT_RUN_FILES = (
    "capabilities.json",
    "cross_seed_fingerprint_summary.jsonl",
    "direction_replicates.json",
    "dose_response_summary.jsonl",
    "fingerprint_summary.jsonl",
    "plan.json",
    "receipt.json",
    "report.md",
    "resolved_config.yaml",
    "resolved_inputs.json",
    "scalar_balance_summary.jsonl",
    "sign_flip_summary.jsonl",
    "source_item_metrics.jsonl",
    "source_layer_metrics.jsonl",
    "summary.json",
    "target_baselines.jsonl",
    "tokenization.jsonl",
)

OMITTED_LARGE_FILES = (
    "interventions.jsonl",
    "directions.npz",
    "source_activations.npz",
    "target_baselines.npz",
)

_URI_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9+.-]*):/{2,}[^\s\"'<>()[\]]*"
)
_POSIX_ABSOLUTE_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\])/(?!/)(?=[^\s/])"
)
_POSIX_DOUBLE_SLASH_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\])//(?=[^/\s]+/[^/\s]+)"
)
_WINDOWS_DRIVE_ABSOLUTE_RE = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]+(?=[^\\/\s])"
)
_WINDOWS_UNC_ABSOLUTE_RE = re.compile(
    r"(?<!\\)\\\\[^\\/\s]+[\\/][^\\/\s]+"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_receipt(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": _sha256(path)}


def _iter_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(key)
            yield from _iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _iter_strings(item)


def _text_fragments(path: Path, text: str) -> Iterator[str]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        yield from _iter_strings(json.loads(text))
    elif suffix == ".jsonl":
        for line in text.splitlines():
            if line.strip():
                yield from _iter_strings(json.loads(line))
    elif suffix in {".yaml", ".yml"}:
        for document in yaml.safe_load_all(text):
            yield from _iter_strings(document)
    else:
        yield text


def _contains_local_absolute_path(text: str) -> bool:
    if text.strip() == "/" or re.fullmatch(r"[A-Za-z]:[\\/]+", text.strip()):
        return True

    file_uri_found = False

    def mask_uri(match: re.Match[str]) -> str:
        nonlocal file_uri_found
        if match.group(1).lower() == "file":
            file_uri_found = True
        return " " * len(match.group(0))

    without_portable_uris = _URI_RE.sub(mask_uri, text)
    if file_uri_found:
        return True
    return any(
        pattern.search(without_portable_uris) is not None
        for pattern in (
            _POSIX_ABSOLUTE_RE,
            _POSIX_DOUBLE_SLASH_RE,
            _WINDOWS_DRIVE_ABSOLUTE_RE,
            _WINDOWS_UNC_ABSOLUTE_RE,
        )
    )


def _assert_public_safe(path: Path) -> None:
    if path.suffix.lower() not in {".json", ".jsonl", ".md", ".yaml", ".yml"}:
        return
    text = path.read_text(encoding="utf-8")
    if any(
        _contains_local_absolute_path(fragment)
        for fragment in _text_fragments(path, text)
    ):
        raise ValueError(f"Refusing to publish a local absolute path from {path}")


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_all_checks_pass(receipt: dict[str, Any], label: str) -> None:
    checks = receipt.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError(f"{label} must contain non-empty checks")
    if any(not isinstance(check, dict) or check.get("pass") is not True for check in checks):
        raise ValueError(f"{label} contains a failed or malformed check")
    passed = receipt.get("passed")
    total = receipt.get("total")
    if type(passed) is not int or type(total) is not int:
        raise ValueError(f"{label} passed/total counts must be integers")
    if passed != total or total != len(checks):
        raise ValueError(f"{label} passed/total counts do not match checks")


def _validate_receipt_coherence(
    *,
    run_dir: Path,
    run_receipt_path: Path,
    parity_receipt_path: Path,
    audit_receipt_path: Path,
) -> dict[str, Any]:
    run_receipt = _load_json_object(run_receipt_path, "run receipt")
    parity_receipt = _load_json_object(parity_receipt_path, "parity receipt")
    audit_receipt = _load_json_object(audit_receipt_path, "audit receipt")
    summary = _load_json_object(run_dir / "summary.json", "run summary")

    if run_receipt.get("status") != "complete":
        raise ValueError("Run receipt status must be complete")
    run_id = run_receipt.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Run receipt must contain a non-empty run_id")
    if run_dir.name != run_id:
        raise ValueError("Run directory name does not match run receipt run_id")
    if run_receipt.get("claim_boundary") != "pre-causal-activation-screen":
        raise ValueError("Run receipt claim boundary is not pre-causal")
    if summary.get("causal_claim_authorized") is not False:
        raise ValueError("Run summary must keep causal_claim_authorized false")

    if audit_receipt.get("status") != "ready_with_caveats":
        raise ValueError("Audit status must be ready_with_caveats")
    if audit_receipt.get("run_id") != run_id:
        raise ValueError("Audit run_id does not match run receipt")
    audit_run_dir = audit_receipt.get("run_dir")
    if not isinstance(audit_run_dir, str) or not audit_run_dir:
        raise ValueError("Audit must contain a non-empty run_dir")
    audit_run_name = audit_run_dir.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    if audit_run_name != run_id:
        raise ValueError("Audit run_dir does not match run receipt")
    if audit_receipt.get("causal_claim_authorized") is not False:
        raise ValueError("Audit must keep causal_claim_authorized false")
    if audit_receipt.get("scientific_result") is not True:
        raise ValueError("Audit must explicitly mark scientific_result true")
    _require_all_checks_pass(audit_receipt, "Audit receipt")

    if parity_receipt.get("status") != "validated_mlx_selected":
        raise ValueError("Parity status must be validated_mlx_selected")
    parity = parity_receipt.get("parity")
    if not isinstance(parity, dict) or parity.get("pass") is not True:
        raise ValueError("Parity receipt must record an overall passing gate")
    _require_all_checks_pass(parity, "Parity gates")
    benchmark = parity_receipt.get("benchmark")
    if (
        not isinstance(benchmark, dict)
        or not isinstance(benchmark.get("speed_gate"), dict)
        or benchmark["speed_gate"].get("pass") is not True
    ):
        raise ValueError("Parity benchmark speed gate must explicitly pass")

    parity_sha256 = _sha256(parity_receipt_path)
    backend = run_receipt.get("backend")
    if not isinstance(backend, dict):
        raise ValueError("Run receipt backend metadata is missing")
    if backend.get("validation_receipt_sha256") != parity_sha256:
        raise ValueError("Run backend parity SHA does not match parity receipt")
    input_hashes = run_receipt.get("input_hashes")
    if not isinstance(input_hashes, dict) or list(input_hashes.values()).count(
        parity_sha256
    ) != 1:
        raise ValueError("Run input hashes do not bind exactly one parity receipt")

    model_receipt = run_receipt.get("model_receipt")
    if not isinstance(model_receipt, dict):
        raise ValueError("Run model receipt is missing")
    parity_validation = model_receipt.get("parity_validation")
    if not isinstance(parity_validation, dict):
        raise ValueError("Run model parity metadata is missing")
    if parity_validation.get("validated") is not True:
        raise ValueError("Run model parity metadata is not validated")
    if parity_validation.get("receipt_sha256") != parity_sha256:
        raise ValueError("Run model parity SHA does not match parity receipt")
    if parity_validation.get("receipt_status") != parity_receipt.get("status"):
        raise ValueError("Run model parity status does not match parity receipt")

    parity_implementation = parity_receipt.get("implementation")
    run_implementation = run_receipt.get("implementation")
    if not isinstance(parity_implementation, dict) or not isinstance(
        run_implementation, dict
    ):
        raise ValueError("Implementation identity is missing from receipts")
    implementation_sha = parity_implementation.get("source_tree_sha256")
    if (
        not isinstance(implementation_sha, str)
        or parity_validation.get("implementation_sha256") != implementation_sha
        or run_implementation.get("source_tree_sha256") != implementation_sha
    ):
        raise ValueError("Parity implementation identity does not match run metadata")

    model_identity_sha = parity_receipt.get("mlx_model_identity_sha256")
    if (
        not isinstance(model_identity_sha, str)
        or parity_validation.get("model_identity_sha256") != model_identity_sha
    ):
        raise ValueError("Parity model identity does not match run metadata")

    parity_layers = parity_receipt.get("intervention_layers")
    prompt_token_counts = benchmark.get("prompt_token_counts")
    if (
        parity_validation.get("validated_site") != parity_receipt.get("site")
        or parity_validation.get("validated_intervention_layers") != parity_layers
        or parity_validation.get("validated_prompt_token_counts")
        != prompt_token_counts
    ):
        raise ValueError("Run model parity scope does not match parity receipt")

    plan = run_receipt.get("plan")
    if not isinstance(plan, dict) or plan.get("resolved_layers") != parity_layers:
        raise ValueError("Run layers do not match validated parity layers")
    for field in ("model", "revision", "dtype"):
        if not (
            backend.get(field)
            == model_receipt.get(field)
            == parity_receipt.get(field)
        ):
            raise ValueError(f"Run/parity {field} metadata does not match")

    return run_receipt


def build(
    *,
    run_dir: Path,
    parity_receipt: Path,
    audit_receipt: Path,
    output_dir: Path,
) -> dict[str, Any]:
    run_receipt_path = run_dir / "receipt.json"
    receipt = _validate_receipt_coherence(
        run_dir=run_dir,
        run_receipt_path=run_receipt_path,
        parity_receipt_path=parity_receipt,
        audit_receipt_path=audit_receipt,
    )

    copied: dict[str, dict[str, Any]] = {}
    parity_dir = output_dir / "mlx_gpt2_parity"
    run_output = output_dir / "v1_standard_mlx"
    destinations = [
        (parity_receipt, parity_dir / "receipt.json"),
        (audit_receipt, run_output / "audit.json"),
    ]
    destinations.extend((run_dir / name, run_output / name) for name in COMPACT_RUN_FILES)
    for source, destination in destinations:
        if not source.is_file():
            raise FileNotFoundError(source)
        _assert_public_safe(source)

    output_dir.mkdir(parents=True, exist_ok=True)
    parity_dir.mkdir(parents=True, exist_ok=True)
    run_output.mkdir(parents=True, exist_ok=True)
    for source, destination in destinations:
        shutil.copy2(source, destination)
        relative = destination.relative_to(output_dir).as_posix()
        copied[relative] = _file_receipt(destination)

    omitted: dict[str, dict[str, Any]] = {}
    for name in OMITTED_LARGE_FILES:
        path = run_dir / name
        if path.is_file():
            omitted[name] = _file_receipt(path)
    if (run_dir / "errors.jsonl").exists():
        raise ValueError("Refusing to publish a run bundle with errors.jsonl")

    manifest = {
        "schema_version": 1,
        "bundle": "glyphprobe-v1-standard-mlx-public-compact",
        "source_run_id": receipt["run_id"],
        "run_seal": receipt["run_seal"],
        "claim_boundary": "pre-causal-activation-screen",
        "causal_claim_authorized": False,
        "included_files": copied,
        "omitted_large_local_files": omitted,
        "omission_reason": (
            "The condition ledger and numeric NPZ arrays are excluded from Git because of "
            "size. Their hashes attest the audited local artifacts but cannot reconstruct them."
        ),
    }
    manifest_path = output_dir / "MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a path-scrubbed compact public bundle.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--parity-receipt", type=Path, required=True)
    parser.add_argument("--audit-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(
        run_dir=args.run_dir.resolve(),
        parity_receipt=args.parity_receipt.resolve(),
        audit_receipt=args.audit_receipt.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    print(f"included={len(manifest['included_files'])}")
    print(f"omitted={len(manifest['omitted_large_local_files'])}")
    print(f"run_seal={manifest['run_seal']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
