#!/usr/bin/env python3
"""Build the deterministic, whitelist-only T19/T20/T21 anonymous archive."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ID = "glyphprobe_t19_anonymous_evidence_v4"
ARCHIVE_ROOT = ARTIFACT_ID
OUTPUT_DIRECTORY = ROOT / "output" / "artifacts"
OUTPUT_ZIP = OUTPUT_DIRECTORY / f"{ARTIFACT_ID}.zip"
OUTPUT_RECEIPT = OUTPUT_DIRECTORY / f"{ARTIFACT_ID}.receipt.json"
OUTPUT_SHA = OUTPUT_DIRECTORY / f"{ARTIFACT_ID}.sha256"
FIXED_ZIP_TIME = (2026, 9, 2, 0, 0, 0)
FIXED_REPRODUCIBILITY_TIMESTAMP = "2026-09-02T00:00:00Z"


DIRECT_FILES = (
    "LICENSE",
    "paper/main.tex",
    "paper/checklist.tex",
    "paper/references.bib",
    "paper/README.md",
    "paper/README.ja.md",
    "paper/CLAIM_TABLE.md",
    "paper/CLAIM_TABLE.ja.md",
    "paper/ASSET_LICENSES.md",
    "paper/ASSET_LICENSES.ja.md",
    "paper/COMPUTE_REPORT.md",
    "paper/COMPUTE_REPORT.ja.md",
    "paper/ETHICS_REVIEW.md",
    "paper/ETHICS_REVIEW.ja.md",
    "paper/figures/manifest.json",
    "paper/figures/t19_causal_sites.pdf",
    "paper/figures/t19_causal_sites.png",
    "paper/figures/t19_design.pdf",
    "paper/figures/t19_design.png",
    "paper/figures/t19_emoji_symbol_boundary.pdf",
    "paper/figures/t19_emoji_symbol_boundary.png",
    "paper/figures/t19_lineage.pdf",
    "paper/figures/t19_lineage.png",
    "paper/figures/t19_model_effects.pdf",
    "paper/figures/t19_model_effects.png",
    "paper/scripts/build_figures.py",
    "tests/test_paper_figure_layout.py",
    "tests/test_final_manuscript_polish.py",
    "docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.md",
    "docs/PAPER_STORY_T19_LEXICAL_NEIGHBORHOOD_V0.ja.md",
    "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.md",
    "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0.ja.md",
    "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.md",
    "docs/T19_LEXICAL_ALIAS_UNICODE_CONTROL_V0_RESULTS.ja.md",
    "configs/t19_lexical_alias_unicode_control_v0.yaml",
    "configs/semantic_atlas_cross_model_replication_v0.yaml",
    "configs/fresh_composite_glyph_lexical_confirmation_v0.yaml",
    "configs/glyph_system_decomposition_v0.yaml",
    "configs/mistral7b_semantic_atlas_v0.yaml",
    "configs/mistral7b_semantic_atlas_reserve_confirmation_v0.yaml",
    "configs/emoji_steering_specificity_harvest_v0.yaml",
    "data/manifests/t19_lexical_alias_unicode_control_v0.json",
    "data/manifests/t19_lexical_alias_unicode_control_v0_freeze.json",
    "data/manifests/t19_lexical_alias_component_causal_v0_go.json",
    "data/manifests/semantic_atlas_cross_model_replication_v0.json",
    "data/manifests/fresh_composite_glyph_lexical_confirmation_v0.json",
    "data/manifests/fresh_composite_glyph_lexical_confirmation_v0_freeze.json",
    "data/manifests/mistral7b_semantic_atlas_selection_v0.json",
    "data/manifests/mistral7b_semantic_atlas_reserve_confirmation_v0.json",
    "data/manifests/glyph_system_decomposition_selection_v0.json",
    "data/manifests/glyph_system_decomposition_v0.json",
    "validation/fresh_composite_glyph_lexical_confirmation_v0/results/cross_model_primary_result.json",
    "validation/semantic_atlas_cross_model_replication_v0/endpoint_semantics_audit.json",
    "validation/semantic_atlas_cross_model_replication_v0/engineering_preflight.json",
    "validation/mistral7b_semantic_atlas_v0/engineering_preflight.json",
    "scripts/t19_lexical_alias_unicode_control_v0.py",
    "scripts/t19_lexical_alias_component_causal_v0.py",
    "scripts/validate_t19_lexical_alias_unicode_control_v0_result.py",
    "scripts/validate_t19_lexical_alias_component_causal_v0_result.py",
    "scripts/fresh_composite_glyph_lexical_confirmation_v0.py",
    "scripts/glyph_system_decomposition_v0.py",
    "scripts/mistral7b_semantic_atlas_v0.py",
    "scripts/semantic_atlas_cross_model_replication_v0.py",
    "scripts/mistral7b_semantic_atlas_reserve_confirmation_v0.py",
    "scripts/emoji_steering_causal_path_v0.py",
    "scripts/emoji_steering_specificity_expansion_v0.py",
    "scripts/emoji_steering_specificity_harvest_v0.py",
    "tests/test_t19_lexical_alias_unicode_control_v0.py",
    "tests/test_t19_lexical_alias_component_causal_v0.py",
    "tests/test_validate_t19_lexical_alias_unicode_control_v0_result.py",
    "tests/test_validate_t19_lexical_alias_component_causal_v0_result.py",
    "paper/figures/t20_causal_ceilings.pdf",
    "paper/figures/t20_causal_ceilings.png",
    "docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.md",
    "docs/T20_LEXICAL_ALIAS_OPTIMIZED_SUBSPACE_CAUSAL_V0.ja.md",
    "configs/t20_lexical_alias_optimized_subspace_causal_v0.yaml",
    "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0.json",
    "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_freeze.json",
    "data/manifests/t20_lexical_alias_optimized_subspace_causal_v0_go.json",
    "scripts/t20_lexical_alias_optimized_subspace_causal_v0.py",
    "scripts/validate_t20_lexical_alias_optimized_subspace_causal_v0_result.py",
    "scripts/t19_lexical_alias_component_causal_posthoc_ceiling_v0.py",
    "tests/test_t20_lexical_alias_optimized_subspace_causal_v0.py",
    "validation/t19_lexical_alias_component_causal_v0/posthoc_ceiling/posthoc_ceiling_result.json",
    "validation/t19_lexical_alias_component_causal_v0/posthoc_ceiling/posthoc_receipt.json",
    "validation/t19_lexical_alias_component_causal_v0/posthoc_ceiling/SHA256SUMS",
)

T21_FILES = (
    "configs/t21_glyph_context_path_pilot_v0.yaml",
    "configs/t21_glyph_context_path_confirmation_v0.yaml",
    "docs/T21_GLYPH_CONTEXT_PATH_PILOT_V0.md",
    "docs/T21_GLYPH_CONTEXT_PATH_PILOT_V0.ja.md",
    "docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.md",
    "docs/T21_GLYPH_CONTEXT_PATH_CONFIRMATION_V0.ja.md",
    "docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.md",
    "docs/T21_GLYPH_CONTEXT_PATH_RESULTS_V0.ja.md",
    "scripts/t21_glyph_context_path_pilot_v0.py",
    "scripts/validate_t21_glyph_context_path_pilot_v0.py",
    "scripts/t21_glyph_context_path_confirmation_v0.py",
    "scripts/validate_t21_glyph_context_path_confirmation_v0.py",
    "scripts/t21_path_inference_v0.py",
    "scripts/export_t21_compact_inference_v0.py",
    "scripts/validate_t21_compact_inference_v0.py",
    "tests/test_t21_glyph_context_path_pilot_v0.py",
    "tests/test_t21_glyph_context_path_confirmation_v0.py",
    "tests/test_t21_path_inference_v0.py",
    "tests/test_t21_compact_and_paper_evidence.py",
    "src/glyphprobe/__init__.py",
    "src/glyphprobe/config.py",
    "src/glyphprobe/provenance.py",
    "validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json",
    "validation/t21_glyph_context_path_pilot_v0/canary/acquisition_receipt.json",
    "validation/t21_glyph_context_path_confirmation_v0/prospective_design.json",
    "validation/t21_glyph_context_path_confirmation_v0/canary_specification.json",
    "validation/t21_glyph_context_path_confirmation_v0/canary/acquisition_receipt.json",
    "validation/t21_glyph_context_path_confirmation_v0/confirmation_specification.json",
)

POST_REVIEW_FILES = (
    "docs/POST_REVIEW_EVIDENCE_PLAN_V0.md",
    "docs/POST_REVIEW_EVIDENCE_PLAN_V0.ja.md",
    "docs/POST_REVIEW_EVIDENCE_RESULTS_V0.md",
    "docs/POST_REVIEW_EVIDENCE_RESULTS_V0.ja.md",
    "scripts/audit_t20_checkpoint_selection_v0.py",
    "scripts/decompose_t21_margin_v0.py",
    "scripts/validate_t21_margin_decomposition_v0.py",
    "scripts/export_t19_compact_predictions_v0.py",
    "scripts/validate_t19_compact_predictions_v0.py",
    "tests/test_post_review_evidence_v0.py",
    "validation/post_review_evidence_v0/t20_checkpoint_selection.json",
    "validation/t19_lexical_alias_unicode_control_v0/compact_v0/predictions.json",
    "validation/t19_lexical_alias_unicode_control_v0/compact_v0/replay_receipt.json",
    "validation/t21_margin_decomposition_v0/decomposition.json",
    "validation/t21_margin_decomposition_v0/reconstruction_receipt.json",
    "validation/t21_margin_decomposition_v0/compact_validation.json",
    "paper/figures/t21_path_summary.pdf",
    "paper/figures/t21_path_summary.png",
)

T21_SHARED_RESULTS = (
    "acquisition_receipt.json",
    "source_receipt.json",
    "analysis_receipt.json",
    "condition_means.json",
    "independent_validation.json",
)

T20_C_VALIDATION_FILES = (
    "design_preflight.json",
    "tokenizer_preflight.json",
    "results/SHA256SUMS",
    "results/analysis_receipt.json",
    "results/causal_primary_result.json",
    "results/causal_site_results.json",
    "results/independent_validation.json",
    "results/training_receipt.json",
    "results/evaluation_receipt.json",
)

T19_L_VALIDATION_FILES = (
    "design_preflight.json",
    "engineering_preflight.json",
    "independent_validation.json",
    "results/SHA256SUMS",
    "results/analysis_receipt.json",
    "results/cross_model_primary_result.json",
    "results/depth_profiles.json",
    "results/model_cell_results.json",
    "tokenizers/gemma2_2b_it_bf16.json",
    "tokenizers/llama32_3b_base_bf16.json",
    "tokenizers/mistral7b_instruct_v03_bf16.json",
    "tokenizers/olmo2_1b_base_bf16.json",
    "tokenizers/qwen25_0p5b_base_bf16.json",
    "tokenizers/qwen25_1p5b_base_bf16.json",
    "tokenizers/qwen25_3b_base_bf16.json",
    "tokenizers/qwen25_7b_base_bf16.json",
    "tokenizers/smollm2_1p7b_base_bf16.json",
)

T19_C_VALIDATION_FILES = (
    "design_preflight.json",
    "independent_validation.json",
    "tokenizer_preflight.json",
    "results/SHA256SUMS",
    "results/analysis_receipt.json",
    "results/causal_primary_result.json",
    "results/causal_site_results.json",
)

T9_PUBLIC_FILES = (
    "PUBLIC_MANIFEST.json",
    "README.md",
    "README.ja.md",
    "analysis/analysis_receipt.json",
    "analysis/cell_metrics.jsonl",
    "analysis/primary_result.json",
    "run/run_receipt.json",
    "run/session_receipt.json",
    "validation/execution_receipt.json",
)

TOKENIZER_ROLES = (
    "gemma2_2b_it_bf16",
    "llama32_3b_base_bf16",
    "mistral7b_instruct_v03_bf16",
    "olmo2_1b_base_bf16",
    "qwen25_0p5b_base_bf16",
    "qwen25_1p5b_base_bf16",
    "qwen25_3b_base_bf16",
    "qwen25_7b_base_bf16",
    "smollm2_1p7b_base_bf16",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_file(
    payloads: dict[str, bytes], source: str, destination: str | None = None
) -> None:
    path = ROOT / source
    if not path.is_file():
        raise FileNotFoundError(f"Required artifact input is missing: {source}")
    name = destination or source
    if name in payloads:
        raise ValueError(f"Duplicate artifact destination: {name}")
    payloads[name] = path.read_bytes()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_payloads() -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for name in DIRECT_FILES:
        add_file(payloads, name)
    for name in T21_FILES:
        add_file(payloads, name)
    for name in POST_REVIEW_FILES:
        add_file(payloads, name)
    for stage in ("pilot", "confirmation"):
        prefix = f"validation/t21_glyph_context_path_{stage}_v0/results"
        for name in T21_SHARED_RESULTS:
            add_file(payloads, f"{prefix}/{name}")
    for name in ("pilot_result.json", "precision_and_quality_report.json"):
        add_file(payloads, f"validation/t21_glyph_context_path_pilot_v0/results/{name}")
    for name in (
        "confirmation_result.json",
        "item_contrasts.json",
        "compact_validation.json",
    ):
        add_file(
            payloads,
            f"validation/t21_glyph_context_path_confirmation_v0/results/{name}",
        )
    for name in T19_L_VALIDATION_FILES:
        prefix = "validation/t19_lexical_alias_unicode_control_v0"
        add_file(payloads, f"{prefix}/{name}")
    for name in T19_C_VALIDATION_FILES:
        prefix = "validation/t19_lexical_alias_component_causal_v0"
        add_file(payloads, f"{prefix}/{name}")
    for name in T20_C_VALIDATION_FILES:
        prefix = "validation/t20_lexical_alias_optimized_subspace_causal_v0"
        add_file(payloads, f"{prefix}/{name}")
    for name in T9_PUBLIC_FILES:
        prefix = "artifacts/mistral7b_semantic_atlas_reserve_confirmation_v0"
        add_file(payloads, f"{prefix}/{name}")
    for role in TOKENIZER_ROLES:
        add_file(
            payloads,
            f"validation/semantic_atlas_cross_model_replication_v0/tokenizers/{role}.json",
        )

    add_file(payloads, "paper/artifact/README.md", "README.md")
    add_file(payloads, "paper/artifact/README.ja.md", "README.ja.md")
    add_file(payloads, "paper/UNICODE_LICENSE.txt", "UNICODE_LICENSE.txt")
    add_file(
        payloads,
        "paper/scripts/validate_anonymous_artifact.py",
        "scripts/validate_anonymous_artifact.py",
    )
    add_file(
        payloads,
        "output/pdf/glyphprobe_t19_first_draft.pdf",
        "paper/glyphprobe_t19_anonymous.pdf",
    )
    payloads["requirements-audit.txt"] = (
        "# Validated compact-audit and figure environment on the manuscript build host.\n"
        "# Acquisition versions are reported separately in paper/COMPUTE_REPORT.md.\n"
        "numpy==2.4.4\n"
        "matplotlib==3.10.9\n"
        "PyYAML==6.0.3\n"
    ).encode("ascii")
    return payloads


def write_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(
        path, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True
    ) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{name}", date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, files[name])


def main() -> int:
    payloads = build_payloads()
    manifest = {
        "archive_root": ARCHIVE_ROOT,
        "artifact_id": ARTIFACT_ID,
        "boundary": {
            "author_identity_metadata_included": False,
            "compact_audit_supported": True,
            "full_raw_replay_supported": False,
            "model_weights_included": False,
            "raw_model_arrays_included": False,
            "scientific_correctness_proven_by_hashes": False,
            "t21_scalar_contrast_statistical_replay_supported": True,
            "t19_prediction_index_statistical_replay_supported": True,
            "t21_posthoc_scalar_decomposition_supported": True,
        },
        "reproducibility_timestamp_utc": FIXED_REPRODUCIBILITY_TIMESTAMP,
        "files": [
            {
                "bytes": len(payloads[name]),
                "path": name,
                "sha256": sha256_bytes(payloads[name]),
            }
            for name in sorted(payloads)
        ],
        "schema_version": 1,
    }
    manifest_bytes = canonical_json(manifest)
    files = dict(payloads)
    files["ARTIFACT_MANIFEST.json"] = manifest_bytes
    files["SHA256SUMS"] = (
        "".join(f"{sha256_bytes(files[name])}  {name}\n" for name in sorted(files))
    ).encode("ascii")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    temporary_zip = OUTPUT_ZIP.with_suffix(".zip.tmp")
    write_zip(temporary_zip, files)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "paper/scripts/validate_anonymous_artifact.py"),
            str(temporary_zip),
        ],
        cwd=ROOT,
        check=True,
    )
    temporary_zip.replace(OUTPUT_ZIP)

    archive_sha = sha256_path(OUTPUT_ZIP)
    receipt = {
        "archive_bytes": OUTPUT_ZIP.stat().st_size,
        "archive_entries": len(files),
        "archive_path": f"output/artifacts/{OUTPUT_ZIP.name}",
        "archive_sha256": archive_sha,
        "artifact_id": ARTIFACT_ID,
        "reproducibility_timestamp_utc": FIXED_REPRODUCIBILITY_TIMESTAMP,
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "payload_files": len(payloads),
        "schema_version": 1,
        "status": "anonymous_artifact_built_and_validated",
    }
    OUTPUT_RECEIPT.write_bytes(canonical_json(receipt))
    OUTPUT_SHA.write_text(f"{archive_sha}  {OUTPUT_ZIP.name}\n", encoding="ascii")
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
