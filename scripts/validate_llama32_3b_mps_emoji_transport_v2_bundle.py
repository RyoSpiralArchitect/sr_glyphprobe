#!/usr/bin/env python3
"""Validate the compact public E2 Llama-3.2-3B transport v2 bundle.

The validator is independent of the v2 builder.  It fail-closed specializes
the frozen standalone v1 validator, verifies every version-sensitive binding,
and requires the v2 freeze manifest to hash-bind both frozen v1 base scripts.
It never opens, reads, hashes, or tokenizes either protected target bank.
"""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
from pathlib import Path
from typing import Any


_ADAPTER_BASE_DEPENDENCY_PATHS = (
    Path("scripts/build_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    Path("scripts/validate_llama32_3b_mps_emoji_transport_v1_bundle.py"),
)
_ADAPTER_BASE_PATH = (
    Path(__file__)
    .resolve()
    .with_name("validate_llama32_3b_mps_emoji_transport_v1_bundle.py")
)
_ADAPTER_BASE_SHA256 = (
    "5c0842f9a7907a6da5462796250e35101249798b20dc5909cd3b1eb859346324"
)
_ADAPTER_EXPECTED_SOURCE_COUNTS = {
    "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1": 1,
    "llama32_3b_mps_emoji_transport_v1": 9,
    "LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1": 1,
    "transport-v1": 2,
    "forbidden_in_v1_new_versioned_freeze_required": 1,
    "tokenization_audit_v1": 1,
    "_v1.yaml": 1,
    "llama32_3b_mps_emoji_transport_receipt.json": 4,
}
_ADAPTER_REPLACEMENTS = (
    (
        "glyphprobe-e2-llama32-3b-mps-emoji-transport-v1",
        "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2",
    ),
    (
        "LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1",
        "LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2",
    ),
    (
        "llama32_3b_mps_emoji_transport_v1",
        "llama32_3b_mps_emoji_transport_v2",
    ),
    ("tokenization_audit_v1", "tokenization_audit_v2"),
    ("_v1.yaml", "_v2.yaml"),
    ("transport-v1", "transport-v2"),
    (
        "forbidden_in_v1_new_versioned_freeze_required",
        "forbidden_in_v2_new_versioned_freeze_required",
    ),
    (
        "llama32_3b_mps_emoji_transport_receipt.json",
        "llama32_3b_mps_emoji_transport_v2_receipt.json",
    ),
)


def _adapter_specialize_source() -> str:
    """Return an exact v2 specialization or fail before validation starts."""

    if not _ADAPTER_BASE_PATH.is_file() or _ADAPTER_BASE_PATH.is_symlink():
        raise RuntimeError("Frozen v1 validator dependency is missing or is a symlink")
    payload = _ADAPTER_BASE_PATH.read_bytes()
    if hashlib.sha256(payload).hexdigest() != _ADAPTER_BASE_SHA256:
        raise RuntimeError("Frozen v1 validator dependency hash differs")
    source = payload.decode("utf-8")
    observed = {
        marker: source.count(marker) for marker in _ADAPTER_EXPECTED_SOURCE_COUNTS
    }
    if observed != _ADAPTER_EXPECTED_SOURCE_COUNTS:
        raise RuntimeError(
            "Frozen v1 validator source markers differ; a reviewed v2 adapter is required"
        )
    specialized = source
    for old, new in _ADAPTER_REPLACEMENTS:
        specialized = specialized.replace(old, new)
    leftovers = [old for old, _ in _ADAPTER_REPLACEMENTS if old in specialized]
    if leftovers:
        raise RuntimeError(
            f"V1 validator markers survived v2 specialization: {leftovers}"
        )
    return specialized


_ADAPTER_SPECIALIZED_SOURCE = _adapter_specialize_source()
_adapter_public_module_name = __name__
globals()["__name__"] = "glyphprobe_llama32_3b_mps_transport_v2_validator_impl"
try:
    exec(
        compile(
            _ADAPTER_SPECIALIZED_SOURCE,
            f"{__file__}::<frozen-v1-validator-specialized-for-v2>",
            "exec",
        ),
        globals(),
        globals(),
    )
finally:
    globals()["__name__"] = _adapter_public_module_name


def _adapter_assert_v2_contract() -> None:
    namespace = globals()
    expected_paths = {
        "BUNDLE_ROOT": "artifacts/llama32_3b_mps_emoji_transport_v2",
        "ROOT_MANIFEST_PATH": (
            "artifacts/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2_MANIFEST.json"
        ),
        "FREEZE_MANIFEST_PATH": (
            "data/manifests/llama32_3b_mps_emoji_transport_v2.json"
        ),
        "PREFLIGHT_PATH": (
            "artifacts/llama32_3b_mps_emoji_transport_v2/"
            "preflight/tokenization_audit_v2.json"
        ),
        "ATTEMPT_RECEIPT_PATH": (
            "validation/llama32_3b_mps_emoji_transport_v2/attempt_started_receipt.json"
        ),
        "EXECUTION_RECEIPT_PATH": (
            "validation/llama32_3b_mps_emoji_transport_v2/execution_receipt.json"
        ),
        "ANALYZER_PATH": ("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py"),
        "BUILDER_PATH": ("scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py"),
        "VALIDATOR_PATH": (
            "scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py"
        ),
    }
    expected_scalars = {
        "PROTOCOL_ID": "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2",
        "BUNDLE_ID": "llama32_3b_mps_emoji_transport_v2_public_evidence",
    }
    failures = [
        name
        for name, expected in expected_paths.items()
        if namespace[name].as_posix() != expected
    ]
    failures.extend(
        name
        for name, expected in expected_scalars.items()
        if namespace[name] != expected
    )
    cell_order = namespace["CELL_ORDER"]
    expected_configs = tuple(
        f"configs/e2_llama32_3b_mps_{arm}_{family}_v2.yaml"
        for arm, family in cell_order
    )
    expected_runs = tuple(
        f"e2-llama32-3b-mps-{arm}-{family}-transport-v2" for arm, family in cell_order
    )
    if namespace["CONFIG_ORDER"] != expected_configs:
        failures.append("CONFIG_ORDER")
    if namespace["RUN_NAMES"] != expected_runs:
        failures.append("RUN_NAMES")
    if (
        "llama32_3b_mps_emoji_transport_v2_receipt.json"
        not in namespace["ANALYSIS_FILES"]
    ):
        failures.append("ANALYSIS_FILES")
    if namespace["EXCLUDED_CONTENT"] != (
        "data/targets/p2_confirmatory_targets_v1.jsonl",
        "data/targets/c1_causal_holdout_targets_v1.jsonl",
    ):
        failures.append("EXCLUDED_CONTENT")
    if failures:
        raise RuntimeError(f"Incomplete v2 validator specialization: {failures}")


_adapter_assert_v2_contract()
_adapter_impl_validate_bundle = globals()["validate_bundle"]
_adapter_impl_main = globals()["main"]


def _adapter_validate_dependencies(root: Path) -> None:
    """Require the v2 freeze to bind both immutable adapter dependencies."""

    resolved_root = Path(root).resolve()
    namespace = globals()
    require = namespace["_require"]
    freeze = namespace["_load_json"](
        resolved_root / namespace["FREEZE_MANIFEST_PATH"], "v2 freeze manifest"
    )
    require(
        freeze.get("protocol_id") == namespace["PROTOCOL_ID"],
        "v2 freeze protocol differs",
    )
    for relative in _ADAPTER_BASE_DEPENDENCY_PATHS:
        dependency = resolved_root / relative
        require(
            dependency.is_file() and not dependency.is_symlink(),
            f"missing frozen v1 bundle dependency: {relative}",
        )
        require(
            namespace["_manifest_declared_hash"](freeze, relative)
            == namespace["_sha256"](dependency),
            f"v2 freeze dependency hash differs: {relative}",
        )


def validate_bundle(root: Path) -> dict[str, Any]:
    """Validate v2 public evidence without consulting local raw evidence."""

    _adapter_assert_v2_contract()
    _adapter_validate_dependencies(root)
    return _adapter_impl_validate_bundle(root)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the specialized standalone v2 validator CLI."""

    return _adapter_impl_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
