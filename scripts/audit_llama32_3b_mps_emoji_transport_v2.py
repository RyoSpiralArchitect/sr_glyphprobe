#!/usr/bin/env python3
"""Model-free, fail-closed preflight for the corrected E2 MPS v2 grid.

V2 preserves the v1 scientific cell and raw-glyph tokenizer contract.  Its one
protocol correction is to freeze the tokenizer's *contextual* emoji span for
each exact source wrapper.  A preceding-space token is 11410 in nine wrappers;
the other seven retain 9468.  This program never loads a language model and
never opens either protected target bank.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


def _load_v1_base() -> Any:
    """Load the frozen v1 implementation as an explicitly bound dependency."""
    path = Path(__file__).with_name("audit_llama32_3b_mps_emoji_transport_v1.py")
    name = "_glyphprobe_llama32_3b_mps_emoji_transport_v1_base_for_v2"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load v1 audit dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_v1_base()

AuditError = _BASE.AuditError
StaticAuthority = _BASE.StaticAuthority
MODEL_ID = _BASE.MODEL_ID
MODEL_REVISION = _BASE.MODEL_REVISION
TOKENIZER_CLASS = _BASE.TOKENIZER_CLASS
TOKENIZER_BASE_VOCAB_SIZE = _BASE.TOKENIZER_BASE_VOCAB_SIZE
TOKENIZER_LENGTH = _BASE.TOKENIZER_LENGTH
EXPECTED_ENVIRONMENT = _BASE.EXPECTED_ENVIRONMENT
EXPECTED_MODEL_ARTIFACT = _BASE.EXPECTED_MODEL_ARTIFACT
EXPECTED_ARCHITECTURE = _BASE.EXPECTED_ARCHITECTURE
TARGET_RELATIVE = _BASE.TARGET_RELATIVE
SOURCE_RELATIVE = _BASE.SOURCE_RELATIVE
TARGET_SHA256 = _BASE.TARGET_SHA256
TARGET_FIRST24_SHA256 = _BASE.TARGET_FIRST24_SHA256
SOURCE_SHA256 = _BASE.SOURCE_SHA256
FORBIDDEN_TARGET_PATHS = _BASE.FORBIDDEN_TARGET_PATHS
FORBIDDEN_TARGET_NAMES = _BASE.FORBIDDEN_TARGET_NAMES
FAMILY_ORDER = _BASE.FAMILY_ORDER
SCOPE_ORDER = _BASE.SCOPE_ORDER
FAMILY_MIDDLE_TOKEN = _BASE.FAMILY_MIDDLE_TOKEN
FULL_PANEL_PATHS = _BASE.FULL_PANEL_PATHS
FULL_PANEL_SHA256 = _BASE.FULL_PANEL_SHA256
CORE_PANEL_PATHS = _BASE.CORE_PANEL_PATHS
MERGED_TOKEN_EXCEPTIONS = _BASE.MERGED_TOKEN_EXCEPTIONS
EXPECTED_FIRST_TOKEN = _BASE.EXPECTED_FIRST_TOKEN
TARGET_IDS = _BASE.TARGET_IDS
TARGET_GROUPS = _BASE.TARGET_GROUPS
WRAPPER_IDS = _BASE.WRAPPER_IDS

PROTOCOL_ID = "glyphprobe-e2-llama32-3b-mps-emoji-transport-v2"
MANIFEST_ID = "llama32_3b_mps_emoji_transport_v2"
MANIFEST_RELATIVE = Path("data/manifests/llama32_3b_mps_emoji_transport_v2.json")
DEFAULT_OUTPUT_RELATIVE = Path(
    "artifacts/llama32_3b_mps_emoji_transport_v2/preflight/tokenization_audit_v2.json"
)
CONFIG_PATHS = {
    (scope, family): Path(f"configs/e2_llama32_3b_mps_{scope}_{family}_v2.yaml")
    for scope in SCOPE_ORDER
    for family in FAMILY_ORDER
}
ANALYZER_RELATIVE = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py")
V1_ANALYZER_RELATIVE = Path("scripts/analyze_llama32_3b_mps_emoji_transport_v1.py")
E1_MATH_RELATIVE = Path("scripts/analyze_emoji_family_exploratory_v1.py")
CRITICAL_FILE_PATHS = (
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.md"),
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V2.ja.md"),
    Path("artifacts/llama32_3b_mps_emoji_transport_v2/README.md"),
    Path("artifacts/llama32_3b_mps_emoji_transport_v2/README.ja.md"),
    Path("docs/HOLDOUT_STATUS.md"),
    Path("docs/HOLDOUT_STATUS.ja.md"),
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.md"),
    Path("docs/LLAMA32_3B_MPS_EMOJI_TRANSPORT_V1_PREFLIGHT_FAILURE.ja.md"),
    Path("validation/llama32_3b_mps_emoji_transport_v1/preflight_failure_receipt.json"),
    Path("validation/holdout_exposure_incidents/2026-08-07-repository-search.json"),
    Path("scripts/audit_llama32_3b_mps_emoji_transport_v1.py"),
    Path("scripts/audit_llama32_3b_mps_emoji_transport_v2.py"),
    Path("scripts/run_llama32_3b_mps_emoji_transport_v2.py"),
    Path("scripts/analyze_llama32_3b_mps_emoji_transport_v2.py"),
    Path("scripts/build_llama32_3b_mps_emoji_transport_v2_bundle.py"),
    Path("scripts/validate_llama32_3b_mps_emoji_transport_v2_bundle.py"),
    V1_ANALYZER_RELATIVE,
    Path("scripts/build_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    Path("scripts/validate_llama32_3b_mps_emoji_transport_v1_bundle.py"),
    E1_MATH_RELATIVE,
    Path("src/glyphprobe/backends/transformers_backend.py"),
    Path("tests/test_llama32_3b_mps_emoji_transport_v2.py"),
    Path("tests/test_analyze_llama32_3b_mps_emoji_transport_v2.py"),
    Path("tests/test_llama32_3b_mps_emoji_transport_v2_bundle.py"),
    Path("tests/test_transformers_explicit_dtype_guard.py"),
    Path("pyproject.toml"),
)

# Exact tokenizer profiles measured with the pinned tokenizer, revision, and
# add_special_tokens=False.  Offsets are absolute character offsets in each
# fixed wrapper.  The 11410 token covers the preceding ASCII space and emoji;
# later span tokens cover only the emoji.
WRAPPER_CONTEXT_PROFILES: dict[str, dict[str, Any]] = {
    "w01_mark_anchor": {
        "first_token": 11410,
        "positions": (2, 3, 4),
        "offsets": ((5, 7), (6, 7), (6, 7)),
        "ordinary_count": 8,
        "outside_sha256": "9e2031793ecbfc03ee75272cf19e80ffe37c4dee5cfdc9ef9a61ebba10fc876f",
    },
    "w02_bracket_continue": {
        "first_token": 9468,
        "positions": (1, 2, 3),
        "offsets": ((1, 2), (1, 2), (1, 2)),
        "ordinary_count": 7,
        "outside_sha256": "323a911a4982240f1777c456c390d5d9c3bdca79ed3564559007bfb9a44dd566",
    },
    "w03_pipe_next": {
        "first_token": 11410,
        "positions": (2, 3, 4),
        "offsets": ((3, 5), (4, 5), (4, 5)),
        "ordinary_count": 10,
        "outside_sha256": "6fcde423201315f40e8c84cfd07164f2255abff99c5ad92ead16d6a1c8e58758",
    },
    "w04_token_state": {
        "first_token": 11410,
        "positions": (2, 3, 4),
        "offsets": ((6, 8), (7, 8), (7, 8)),
        "ordinary_count": 8,
        "outside_sha256": "2dceb3571855fd5121273ff69b1954cd45e0c3dc88cd15b4f5f6ebe3d9c07631",
    },
    "w05_begin_end": {
        "first_token": 9468,
        "positions": (2, 3, 4),
        "offsets": ((6, 7), (6, 7), (6, 7)),
        "ordinary_count": 10,
        "outside_sha256": "0bc075fd84247929d8fbab328ea197127d2dcf323f8c55b458c2ac04020d6589",
    },
    "w06_binary_result": {
        "first_token": 11410,
        "positions": (1, 2, 3),
        "offsets": ((1, 3), (2, 3), (2, 3)),
        "ordinary_count": 9,
        "outside_sha256": "b15dba32114ae62ed8e3e6da32232fc57c19a22d59028231122ed1bfc7909713",
    },
    "w07_symbol_following": {
        "first_token": 9468,
        "positions": (2, 3, 4),
        "offsets": ((7, 8), (7, 8), (7, 8)),
        "ordinary_count": 8,
        "outside_sha256": "6621669507ef1b05ee12769ab38f6037889e6c9e6fc7a3b2641d9c3f20f1f430",
    },
    "w08_pair_q": {
        "first_token": 9468,
        "positions": (2, 3, 4),
        "offsets": ((2, 3), (2, 3), (2, 3)),
        "ordinary_count": 8,
        "outside_sha256": "887f411ec32b356b9439429e5312519606ae1ccfe8a3221678b777d79cdfab72",
    },
    "w09_input_response": {
        "first_token": 9468,
        "positions": (2, 3, 4),
        "offsets": ((6, 7), (6, 7), (6, 7)),
        "ordinary_count": 8,
        "outside_sha256": "977f66cf001d17699effaeed31e5404c97a93458612c736aabc0a92f59566190",
    },
    "w10_sequence_continuation": {
        "first_token": 11410,
        "positions": (3, 4, 5),
        "offsets": ((11, 13), (12, 13), (12, 13)),
        "ordinary_count": 11,
        "outside_sha256": "38c332b27fe4f1b51cada729ecef7ef5cd9546c517a0ff95e130af611040e000",
    },
    "w11_field_anchor": {
        "first_token": 9468,
        "positions": (4, 5, 6),
        "offsets": ((12, 13), (12, 13), (12, 13)),
        "ordinary_count": 10,
        "outside_sha256": "6e62349d3ee9c23e4141ad57044c831afc9c1c258ad2545b0243a7b75dfc6bb9",
    },
    "w12_list_next": {
        "first_token": 11410,
        "positions": (3, 4, 5),
        "offsets": ((6, 8), (7, 8), (7, 8)),
        "ordinary_count": 8,
        "outside_sha256": "1d40991ad47b5e21bde40647c565f14bf8d9cc3ced868f02bc66dcc4f08c34f3",
    },
    "w13_left_right": {
        "first_token": 11410,
        "positions": (1, 2, 3),
        "offsets": ((4, 6), (5, 6), (5, 6)),
        "ordinary_count": 8,
        "outside_sha256": "48db08bde105fa5069a9fb073b6101db7f64d19ec985709264dd4efd1537b34b",
    },
    "w14_codepoint_text": {
        "first_token": 11410,
        "positions": (3, 4, 5),
        "offsets": ((10, 12), (11, 12), (11, 12)),
        "ordinary_count": 9,
        "outside_sha256": "8f376587108d7ea7b83f4bc50df0951e8d24386833d8146a892d2ff54330114f",
    },
    "w15_observation_inference": {
        "first_token": 11410,
        "positions": (2, 3, 4),
        "offsets": ((11, 13), (12, 13), (12, 13)),
        "ordinary_count": 9,
        "outside_sha256": "f6fb3fcf99116d700dcc6383d8b0b67ece3e2e03a2b4bd002de326de8fb05416",
    },
    "w16_slot_completion": {
        "first_token": 9468,
        "positions": (3, 4, 5),
        "offsets": ((7, 8), (7, 8), (7, 8)),
        "ordinary_count": 10,
        "outside_sha256": "d8d4953ea8cb9b501278e89c0e4d926ac093cd007de3771af92a1e4c2a32731f",
    },
}

_V1_EXPECTED_CONFIG = _BASE._expected_config
_V1_VALIDATE_MANIFEST = _BASE._validate_manifest


def _expected_config(scope: str, family: str) -> dict[str, Any]:
    config = deepcopy(_V1_EXPECTED_CONFIG(scope, family))
    config["run"]["name"] = f"e2-llama32-3b-mps-{scope}-{family}-transport-v2"
    return config


def _validate_manifest(
    root: Path,
    manifest_path: Path,
    expected_input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Validate the shared v1 schema plus the v2 analyzer dependency edge."""
    report = _V1_VALIDATE_MANIFEST(root, manifest_path, expected_input_hashes)
    manifest = _BASE._read_json_object(manifest_path, "E2 v2 manifest")
    analysis = manifest.get("analysis")
    _require(isinstance(analysis, Mapping), "Manifest analysis binding is missing")
    dependency = analysis.get("v1_analysis_dependency")
    _require(
        isinstance(dependency, Mapping),
        "Manifest v1 analysis dependency binding is missing",
    )
    expected_path = V1_ANALYZER_RELATIVE.as_posix()
    _require(
        dependency.get("path") == expected_path,
        "Manifest v1 analysis dependency path differs",
    )
    expected_sha256 = _sha256(root / V1_ANALYZER_RELATIVE)
    _require(
        dependency.get("sha256") == expected_sha256,
        "Manifest v1 analysis dependency SHA-256 differs",
    )
    verified = {
        row.get("path"): row.get("sha256")
        for row in report.get("verified_files", [])
        if isinstance(row, Mapping)
    }
    _require(
        verified.get(expected_path) == expected_sha256,
        "Manifest files do not bind the v1 analysis dependency",
    )
    return report


def _configure_base() -> None:
    """Point generic v1 fail-closed helpers at the isolated v2 namespace."""
    _BASE.PROTOCOL_ID = PROTOCOL_ID
    _BASE.MANIFEST_ID = MANIFEST_ID
    _BASE.MANIFEST_RELATIVE = MANIFEST_RELATIVE
    _BASE.DEFAULT_OUTPUT_RELATIVE = DEFAULT_OUTPUT_RELATIVE
    _BASE.CONFIG_PATHS = CONFIG_PATHS
    _BASE.CRITICAL_FILE_PATHS = CRITICAL_FILE_PATHS
    _BASE.ANALYZER_RELATIVE = ANALYZER_RELATIVE
    _BASE.E1_MATH_RELATIVE = E1_MATH_RELATIVE
    _BASE._expected_config = _expected_config
    _BASE._validate_manifest = _validate_manifest


_configure_base()

_require = _BASE._require
_sha256 = _BASE._sha256
_portable_relative = _BASE._portable_relative
_tokenize = _BASE._tokenize
_tokenizer_identity = _BASE._tokenizer_identity
collect_git_authority = _BASE.collect_git_authority
audit_runtime_authority = _BASE.audit_runtime_authority
atomic_no_overwrite = _BASE.atomic_no_overwrite


def load_static_authority(
    root: Path,
    *,
    manifest_path: Path | None = None,
) -> StaticAuthority:
    _configure_base()
    return _BASE.load_static_authority(root, manifest_path=manifest_path)


def _expected_raw_ids(item_id: str) -> tuple[int, ...]:
    """Keep the v1 raw-glyph contract unchanged."""
    return _BASE._expected_raw_ids(item_id)


def _expected_context_ids(item_id: str, wrapper_id: str) -> tuple[int, ...]:
    raw = _expected_raw_ids(item_id)
    return (int(WRAPPER_CONTEXT_PROFILES[wrapper_id]["first_token"]), *raw[1:])


def _outside_sha256(values: tuple[int, ...]) -> str:
    return hashlib.sha256(json.dumps(values).encode("utf-8")).hexdigest()


def audit_tokenizer(tokenizer: Any, authority: StaticAuthority) -> dict[str, Any]:
    identity = _tokenizer_identity(tokenizer)
    items = [
        item for family in FAMILY_ORDER for item in authority.panels["full50"][family]
    ]
    core_ids = {
        item["id"]
        for family in FAMILY_ORDER
        for item in authority.panels["core35"][family]
    }
    raw_records: list[dict[str, Any]] = []
    raw_ids: dict[str, tuple[int, ...]] = {}
    for item in items:
        ids, offsets = _tokenize(tokenizer, item["glyph"])
        expected = _expected_raw_ids(item["id"])
        _require(tuple(ids) == expected, f"Raw token IDs differ for {item['id']}")
        _require(
            offsets == [(0, 1)] * len(ids),
            f"Raw token offsets differ for {item['id']}",
        )
        raw_ids[item["id"]] = tuple(ids)
        raw_records.append(
            {
                "id": item["id"],
                "glyph": item["glyph"],
                "scope": "core35" if item["id"] in core_ids else "full50_only",
                "token_ids": ids,
                "token_count": len(ids),
                "merged_exception": item["id"] in MERGED_TOKEN_EXCEPTIONS,
                "decoded_round_trip_verified": True,
                "utf8_hex": item["glyph"].encode("utf-8").hex(),
                "codepoint": f"U+{ord(item['glyph']):04X}",
            }
        )

    _require(
        sum(len(value) == 3 for value in raw_ids.values()) == 47,
        "Expected 47 three-token glyphs",
    )
    _require(
        sum(len(value) == 2 for value in raw_ids.values()) == 3,
        "Expected three merged glyphs",
    )
    _require(
        all(len(raw_ids[item_id]) == 3 for item_id in core_ids),
        "Core35 is not three-token",
    )
    _require(
        set(WRAPPER_CONTEXT_PROFILES) == set(WRAPPER_IDS),
        "Frozen wrapper profile IDs differ",
    )

    wrapper_records: list[dict[str, Any]] = []
    for wrapper in authority.wrappers:
        wrapper_id = str(wrapper["id"])
        frozen = WRAPPER_CONTEXT_PROFILES[wrapper_id]
        profiles: list[dict[str, Any]] = []
        core_counts: set[int] = set()
        core_positions: set[tuple[int, ...]] = set()
        core_outside: set[tuple[int, ...]] = set()
        full_outside: set[tuple[int, ...]] = set()
        for item in items:
            text = wrapper["template"].format(emoji=item["glyph"])
            ids, offsets = _tokenize(tokenizer, text)
            start = text.index(item["glyph"])
            stop = start + len(item["glyph"])
            positions = tuple(
                index
                for index, (left, right) in enumerate(offsets)
                if left < stop and right > start
            )
            expected_ids = _expected_context_ids(item["id"], wrapper_id)
            expected_positions = tuple(frozen["positions"][: len(expected_ids)])
            expected_offsets = tuple(frozen["offsets"][: len(expected_ids)])
            _require(
                positions == expected_positions,
                f"Contextual positions differ for {wrapper_id}/{item['id']}",
            )
            span_ids = tuple(ids[index] for index in positions)
            _require(
                span_ids == expected_ids,
                f"Contextual emoji IDs differ for {wrapper_id}/{item['id']}",
            )
            span_offsets = tuple(offsets[index] for index in positions)
            _require(
                span_offsets == expected_offsets,
                f"Contextual offsets differ for {wrapper_id}/{item['id']}",
            )
            outside = tuple(
                value for index, value in enumerate(ids) if index not in positions
            )
            _require(
                _outside_sha256(outside) == frozen["outside_sha256"],
                f"Frozen outside tokens differ for {wrapper_id}/{item['id']}",
            )
            expected_count = int(frozen["ordinary_count"]) - (
                1 if item["id"] in MERGED_TOKEN_EXCEPTIONS else 0
            )
            _require(
                len(ids) == expected_count,
                f"Contextual token count differs for {wrapper_id}/{item['id']}",
            )
            full_outside.add(outside)
            if item["id"] in core_ids:
                core_counts.add(len(ids))
                core_positions.add(positions)
                core_outside.add(outside)
            profiles.append(
                {
                    "item_id": item["id"],
                    "token_count": len(ids),
                    "emoji_token_positions": list(positions),
                    "emoji_token_offsets": [list(value) for value in span_offsets],
                    "emoji_token_ids": list(span_ids),
                    "last_nonpad_position": len(ids) - 1,
                    "decoded_round_trip_verified": True,
                    "outside_token_ids_sha256": _outside_sha256(outside),
                }
            )
        _require(len(full_outside) == 1, f"Outside wrapper tokens vary: {wrapper_id}")
        _require(len(core_counts) == 1, f"Core wrapper counts differ: {wrapper_id}")
        _require(
            len(core_positions) == 1, f"Core wrapper positions differ: {wrapper_id}"
        )
        _require(
            len(core_outside) == 1, f"Core wrapper outside tokens differ: {wrapper_id}"
        )
        wrapper_records.append(
            {
                "wrapper_id": wrapper_id,
                "contextual_first_token": frozen["first_token"],
                "ordinary_token_count": frozen["ordinary_count"],
                "merged_exception_token_count": frozen["ordinary_count"] - 1,
                "core35_token_count": next(iter(core_counts)),
                "core35_emoji_token_positions": list(next(iter(core_positions))),
                "core35_emoji_token_offsets": [
                    list(value) for value in frozen["offsets"]
                ],
                "outside_token_ids_sha256": frozen["outside_sha256"],
                "outside_tokens_identical_across_full50": True,
                "profiles": profiles,
            }
        )

    return {
        "identity": identity,
        "raw": raw_records,
        "wrappers": wrapper_records,
        "rules": {
            "v1_raw_contract_preserved": True,
            "full50_raw_token_count_distribution": {"2": 3, "3": 47},
            "raw_merged_exceptions": {
                key: list(value) for key, value in MERGED_TOKEN_EXCEPTIONS.items()
            },
            "contextual_first_token_by_wrapper": {
                key: value["first_token"]
                for key, value in WRAPPER_CONTEXT_PROFILES.items()
            },
            "contextual_first_token_distribution": {"9468": 7, "11410": 9},
            "full50_exceptions_use_contextual_first_token_substitution": True,
            "core35_item_count": 35,
            "core35_exact_contextual_form": (
                "[wrapper_first_token, family_middle_token, 239 + slot]"
            ),
            "core35_slots": list(range(3, 10)),
            "core35_suffix_tokens": list(range(242, 249)),
            "family_middle_tokens": FAMILY_MIDDLE_TOKEN,
            "wrapper_context_profiles_exactly_frozen": True,
            "wrapper_outside_tokens_identical": True,
            "wrapper_core_token_count_position_and_outside_isomorphic": True,
            "decoded_round_trips_verified": True,
        },
        "counts": {
            "raw_glyphs_verified": 50,
            "full50_wrapper_profiles_verified": 800,
            "core35_wrapper_profiles_verified": 560,
            "wrapper_count": 16,
        },
    }


def _assemble_report(
    authority: StaticAuthority,
    *,
    tokenizer: Any,
    runtime_authority: Mapping[str, Any],
    git_authority: Mapping[str, Any],
) -> dict[str, Any]:
    _BASE._validate_runtime_authority(runtime_authority)
    _BASE._validate_git_authority(git_authority)
    tokenization = audit_tokenizer(tokenizer, authority)
    return {
        "schema_version": 1,
        "protocol_id": PROTOCOL_ID,
        "status": "passed",
        "audit_role": "model_free_static_artifact_config_and_contextual_tokenizer_preflight",
        "v1_preflight_outcome": "failed_before_any_model_forward",
        "v2_correction_scope": "contextual_wrapper_token_profile_only",
        "model_forward_count": 0,
        "language_model_loaded": False,
        "scientific_outcomes_inspected": False,
        "p2_content_opened": False,
        "c1_content_opened": False,
        "audited_commit": git_authority["audited_commit"],
        "git_authority": dict(git_authority),
        "environment": dict(runtime_authority["environment"]),
        "model_artifact": dict(runtime_authority["model_artifact"]),
        "architecture": dict(runtime_authority["architecture"]),
        "runtime_parameter_dtype": {
            "measured_in_preflight": False,
            "measurement_stage": runtime_authority[
                "runtime_parameter_dtype_measurement_stage"
            ],
        },
        "static": authority.report,
        "tokenization": tokenization,
        "authorization": {
            "frozen_grid_execution_authorized": True,
            "analysis_authorized_before_grid_completion": False,
            "p2_use_authorized": False,
            "c1_use_authorized": False,
            "causal_claim_authorized": False,
        },
        "claim_boundary": (
            "Environment/artifact/configuration/contextual-tokenizer qualification "
            "for one frozen exploratory Transformers/MPS transport grid; no "
            "language model is loaded and no semantic, mechanistic, causal, "
            "confirmatory, or cross-model result is produced."
        ),
    }


def audit_suite(
    root: Path,
    *,
    tokenizer: Any,
    runtime_authority: Mapping[str, Any],
    git_authority: Mapping[str, Any],
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    authority = load_static_authority(root, manifest_path=manifest_path)
    return _assemble_report(
        authority,
        tokenizer=tokenizer,
        runtime_authority=runtime_authority,
        git_authority=git_authority,
    )


def _load_pinned_tokenizer() -> Any:
    return _BASE._load_pinned_tokenizer()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_repo_root())
    parser.add_argument(
        "--manifest",
        type=Path,
        help=f"frozen protocol manifest (defaults to {MANIFEST_RELATIVE.as_posix()})",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.repo_root.resolve()
    manifest = args.manifest or MANIFEST_RELATIVE
    if not manifest.is_absolute():
        manifest = root / manifest
    output = args.output or (root / DEFAULT_OUTPUT_RELATIVE)
    if not output.is_absolute():
        output = root / output
    try:
        authority = load_static_authority(root, manifest_path=manifest)
        git_authority = collect_git_authority(root)
        runtime_authority = audit_runtime_authority()
        tokenizer = _load_pinned_tokenizer()
        report = _assemble_report(
            authority,
            tokenizer=tokenizer,
            runtime_authority=runtime_authority,
            git_authority=git_authority,
        )
        atomic_no_overwrite(output, report)
    except AuditError as exc:
        print(f"audit_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"status": "passed", "output": _portable_relative(output, root)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
