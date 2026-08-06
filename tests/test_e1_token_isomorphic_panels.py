from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil

import pytest
import yaml

from glyphprobe.config import load_experiment_config


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "audit_e1_token_isomorphic_panels.py"
SPEC = importlib.util.spec_from_file_location(
    "audit_e1_token_isomorphic_panels", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads((ROOT / AUDIT.MANIFEST_PATH).read_text(encoding="utf-8"))


def test_manifest_digest_is_hard_pinned_and_contains_no_pending_values() -> None:
    manifest_path = ROOT / AUDIT.MANIFEST_PATH
    actual = _sha256(manifest_path)
    assert actual == AUDIT.EXPECTED_MANIFEST_SHA256
    assert "PENDING_" not in manifest_path.read_text(encoding="utf-8")
    assert _manifest()["freeze"]["status"] == (
        "frozen_by_public_commit_containing_this_manifest"
    )


def test_manifest_tampering_fails_before_any_input_is_loaded(tmp_path: Path) -> None:
    destination = tmp_path / AUDIT.MANIFEST_PATH
    destination.parent.mkdir(parents=True)
    shutil.copy2(ROOT / AUDIT.MANIFEST_PATH, destination)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(AUDIT.AuditError, match="hard-pinned"):
        AUDIT._load_manifest(tmp_path)


def test_five_families_have_exact_contiguous_disjoint_ranges() -> None:
    manifest = _manifest()
    expected = {
        "sky": (0x1F311, 0x1F31A, 234),
        "food": (0x1F351, 0x1F35A, 235),
        "animals": (0x1F411, 0x1F41A, 238),
        "transport": (0x1F691, 0x1F69A, 248),
        "social": (0x1F911, 0x1F91A, 97),
    }
    assert manifest["token_isomorphism"]["shared_first_token_id"] == 8582
    assert manifest["token_isomorphism"]["shared_slot_suffix_token_ids"] == list(
        range(239, 249)
    )
    assert {
        spec["role"]: (
            int(spec["codepoint_start"][2:], 16),
            int(spec["codepoint_end"][2:], 16),
            spec["family_middle_token_id"],
        )
        for spec in manifest["panels"]
    } == expected

    glyph_sets: list[set[str]] = []
    for spec in manifest["panels"]:
        panel_path = ROOT / spec["path"]
        assert _sha256(panel_path) == spec["sha256"]
        items = yaml.safe_load(panel_path.read_text(encoding="utf-8"))["items"]
        start, end, _ = expected[spec["role"]]
        assert [ord(item["glyph"]) for item in items] == list(range(start, end + 1))
        assert [item["id"] for item in items] == [
            f"{spec['factor_family']}_slot_{index:02d}" for index in range(10)
        ]
        assert [item["factors"]["matched_slot"] for item in items] == [
            f"slot_{index:02d}" for index in range(10)
        ]
        glyph_sets.append({item["glyph"] for item in items})
    assert len(set().union(*glyph_sets)) == 50
    assert sum(len(values) for values in glyph_sets) == 50


def test_configs_resolve_only_exploratory_inputs_and_fixed_cells() -> None:
    manifest = _manifest()
    fixed = manifest["fixed_execution_cell"]
    source_path = (ROOT / manifest["shared_inputs"]["source"]["path"]).resolve()
    target_path = (ROOT / manifest["shared_inputs"]["target"]["path"]).resolve()
    parity_path = (ROOT / manifest["shared_inputs"]["parity"]["path"]).resolve()
    forbidden_names = {Path(value).name for value in AUDIT.FORBIDDEN_TARGET_PATHS}

    plans = []
    assert {row["role"] for row in manifest["role_bindings"]} == {
        row["role"] for row in manifest["panels"]
    }
    assert AUDIT._validate_role_bindings(manifest) == manifest["role_bindings"]
    for panel_spec in manifest["panels"]:
        config_path = ROOT / panel_spec["config_path"]
        assert _sha256(config_path) == panel_spec["config_sha256"]
        config, inputs = load_experiment_config(config_path)
        assert config.run.name == panel_spec["run_name"]
        assert config.backend.kind == "mlx"
        assert config.backend.model == AUDIT.EXPECTED_MODEL_ID
        assert config.backend.revision == AUDIT.EXPECTED_REVISION
        assert config.backend.add_special_tokens is False
        assert config.backend.trust_remote_code is False
        assert config.source.anchor_position == "last_nonpad"
        assert config.capture.site == "resid_post"
        assert config.capture.layers == [2, 4]
        assert config.capture.position == "last_nonpad"
        assert config.capture.return_attentions is False
        assert config.intervention.mode == "activation_add"
        assert config.intervention.strengths == [0.05]
        assert config.intervention.position == "last_nonpad"
        assert config.controls.random_directions_per_layer == 2
        assert config.controls.zero_direction is True
        assert config.controls.sign_flip is False
        assert config.controls.sign_flip_strengths == []
        assert config.controls.label_shuffle_permutations == 0
        assert config.controls.include_neutral_direction is False
        assert config.metrics.rbo_p == 0.90
        assert config.metrics.save_fingerprints is True
        assert config.metrics.epsilon == 1.0e-12
        assert config.surface.emoji_template == "{emoji}\n{prompt}"
        assert config.surface.neutral_template == "{prompt}"
        assert config.surface.system_prompt is None
        assert len(inputs.panel_items) == 10
        assert len(inputs.wrappers) == 16
        assert len(inputs.targets) == 24
        assert config.source.wrappers_file == Path(
            "../data/wrappers/source_wrappers.jsonl"
        )
        assert config.targets.cases_file == Path(
            "../data/targets/prestage_targets.jsonl"
        )
        assert source_path in inputs.input_paths
        assert target_path in inputs.input_paths
        assert parity_path in inputs.input_paths
        assert forbidden_names.isdisjoint({path.name for path in inputs.input_paths})
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        plans.append(AUDIT._expected_plan_counts(raw, 10))

    assert plans == [fixed["expected_forward_calls_per_family"]] * 5
    assert sum(row["total"] for row in plans) == 9880
    assert sum(row["intervention_rows"] for row in plans) == 8880


def test_excluded_bank_check_uses_declarations_without_touching_files(
    tmp_path: Path,
) -> None:
    manifest = _manifest()
    # The check must succeed even under an empty root: it validates known manifest
    # constants and zero-use declarations, never the excluded files themselves.
    reports = AUDIT._validate_excluded_banks(tmp_path, manifest)
    assert {row["path"] for row in reports} == AUDIT.FORBIDDEN_TARGET_PATHS
    assert all(row["e1_model_forward_count_declared"] == 0 for row in reports)
    source = inspect.getsource(AUDIT._validate_excluded_banks)
    assert "_verified_path" not in source
    assert "read_text" not in source
    assert "_sha256" not in source


def test_audit_script_is_tokenizer_only_and_has_no_model_or_backend_loader() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert "mlx_lm" not in source
    assert "create_backend" not in source
    assert "backend.load" not in source


def test_analysis_and_protocol_bindings_are_complete() -> None:
    manifest = _manifest()
    analysis = manifest["fixed_analysis"]
    assert analysis["bootstrap_resamples"] == 20_000
    assert analysis["bootstrap_seed"] == 20_260_808
    assert analysis["primary_layer"] == 2
    assert analysis["secondary_layer"] == 4
    assert analysis["endpoints"] == AUDIT.EXPECTED_ANALYSIS_ENDPOINTS
    assert analysis["mean_estimand"] == AUDIT.EXPECTED_ANALYSIS_MEAN_ESTIMAND
    assert analysis["cli_role_arguments"] == AUDIT.EXPECTED_ANALYSIS_CLI_ROLE_ARGUMENTS
    assert {
        key: analysis[key] for key in AUDIT.EXPECTED_ANALYSIS_DESIGN
    } == AUDIT.EXPECTED_ANALYSIS_DESIGN
    assert analysis["expected_output_rows"] == {
        "family_target_scores.jsonl": 5 * 2 * 24,
        "transfer_target_scores.jsonl": 5 * 4 * 2 * 24,
        "family_cell_summary.jsonl": 5 * 2,
        "transfer_cell_summary.jsonl": 5 * 4 * 2,
    }
    assert analysis["output_unique_keys"] == AUDIT.EXPECTED_OUTPUT_UNIQUE_KEYS
    assert len({tuple(value) for value in analysis["output_unique_keys"].values()}) == 4
    assert not analysis["script_sha256"].startswith("PENDING_")
    assert _sha256(ROOT / analysis["script_path"]) == analysis["script_sha256"]
    assert {row["language"] for row in manifest["protocol_documents"]} == {"en", "ja"}
    for row in manifest["protocol_documents"]:
        assert not row["sha256"].startswith("PENDING_")
        assert _sha256(ROOT / row["path"]) == row["sha256"]


def test_live_pinned_tokenizer_audit_when_snapshot_and_analysis_are_available() -> None:
    pytest.importorskip("transformers")
    manifest = _manifest()
    snapshot = (
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--openai-community--gpt2"
        / "snapshots"
        / AUDIT.EXPECTED_REVISION
    )
    if not all(
        (snapshot / filename).is_file()
        for filename in manifest["tokenizer"]["assets_sha256"]
    ):
        pytest.skip("pinned GPT-2 tokenizer snapshot is not available locally")

    report = AUDIT.audit_suite(ROOT)
    assert report["status"] == "pass"
    assert report["manifest_sha256"] == AUDIT.EXPECTED_MANIFEST_SHA256
    assert report["audit_implementation"] == {
        "path": "scripts/audit_e1_token_isomorphic_panels.py",
        "sha256": _sha256(SCRIPT_PATH),
    }
    assert report["language_model_loaded"] is False
    assert report["model_forward_executed"] is False
    assert report["outcome_data_inspected"] is False
    assert report["token_isomorphism"]["raw_first_and_third_identity"] is True
    assert report["token_isomorphism"]["wrapper_profile_isomorphic"] is True
    assert report["counts"] == {
        "panel_count": 5,
        "items_per_panel": 10,
        "scalar_entries_verified": 50,
        "wrapper_count": 16,
        "wrapper_profiles_verified": 800,
        "fixed_family_layer_strength_seed_cells": 30,
        "planned_forward_calls": 9880,
        "planned_intervention_rows": 8880,
    }
    assert all(
        row["e1_model_forward_count_declared"] == 0 for row in report["excluded_banks"]
    )
    assert report["authorization"]["p2_model_forward_authorized"] is False
    assert report["authorization"]["c1_model_forward_authorized"] is False
    assert report["authorization"]["causal_claim_authorized"] is False
