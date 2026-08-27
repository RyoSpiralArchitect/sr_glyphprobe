from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
ANALYZER_PATH = ROOT / "scripts" / "analyze_llama32_3b_instruct_mps_m2_bridge_v0.py"
SPEC = importlib.util.spec_from_file_location("llama32_m2_bridge_v0", ANALYZER_PATH)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)

BUILDER_PATH = ROOT / "scripts" / "build_llama32_3b_instruct_mps_m2_bridge_v0_manifest.py"
BUILDER_SPEC = importlib.util.spec_from_file_location("llama32_m2_bridge_builder_v0", BUILDER_PATH)
assert BUILDER_SPEC is not None and BUILDER_SPEC.loader is not None
BUILDER = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(BUILDER)

LAUNCHER_PATH = ROOT / "scripts" / "run_llama32_3b_instruct_mps_m2_bridge_v0.py"
PREFLIGHT_PATH = ROOT / "scripts" / "preflight_llama32_3b_instruct_mps_m2_bridge_v0.py"


def _configs() -> dict[str, Path]:
    return {
        "primary": ROOT / "configs" / "llama32_3b_instruct_mps_m2_primary_v0.yaml",
        "null_a": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_a_v0.yaml",
        "null_b": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_b_v0.yaml",
        "null_c": ROOT / "configs" / "llama32_3b_instruct_mps_m2_null_c_v0.yaml",
    }


def test_four_configs_share_exact_frozen_grid_except_panel_and_run_name() -> None:
    values = {
        role: yaml.safe_load(path.read_text(encoding="utf-8"))
        for role, path in _configs().items()
    }
    for role, value in values.items():
        ANALYZER._validate_config(value, role)
    signatures = [ANALYZER._common_config_signature(value) for value in values.values()]
    assert all(signature == signatures[0] for signature in signatures[1:])
    assert [values[role]["panel"]["file"] for role in ANALYZER.ROLE_ORDER] == [
        "../data/emoji_panels/colored_shapes.yaml",
        "../data/emoji_panels/llama32_m2_matched_null_a_v2.yaml",
        "../data/emoji_panels/llama32_m2_matched_null_b_v2.yaml",
        "../data/emoji_panels/llama32_m2_matched_null_c_v2.yaml",
    ]


def test_identical_panels_have_exactly_zero_adjusted_endpoints() -> None:
    rng = np.random.default_rng(7)
    one_panel = rng.normal(size=(3, 10, 24, 8))
    one_panel /= np.linalg.norm(one_panel, axis=-1, keepdims=True)
    layers = np.stack([one_panel] * 4, axis=0)
    weights = np.ones((1, 24), dtype=np.int16)
    groups = [tuple(range(start, start + 4)) for start in range(0, 24, 4)]
    ensemble, panel_a = ANALYZER._score_layer_chunk(layers, weights, groups)
    assert ensemble.shape == (1,)
    assert panel_a.shape == (1,)
    assert ensemble[0] == 0.0
    assert panel_a[0] == 0.0


def test_primary_decision_constants_are_fixed_and_layer_11_is_non_rescuing() -> None:
    assert ANALYZER.LAYERS == (5, 11)
    assert ANALYZER.STRENGTH == 0.05
    assert ANALYZER.DIRECTION_SEEDS == (101, 211, 307)
    assert ANALYZER.DELTA == 0.06
    assert ANALYZER.BOOTSTRAP_REPLICATES == 20_000
    assert ANALYZER.BOOTSTRAP_SEED == 20260828


def test_raw_and_resolved_depth_specs_are_distinguished() -> None:
    raw = yaml.safe_load(_configs()["primary"].read_text(encoding="utf-8"))
    ANALYZER._validate_config(raw, "primary", resolved=False)
    resolved = dict(raw)
    resolved["capture"] = dict(raw["capture"])
    resolved["capture"]["layers"] = [5, 11]
    ANALYZER._validate_config(resolved, "primary", resolved=True)


def test_static_manifest_surface_is_complete_and_excludes_protected_banks() -> None:
    manifest = BUILDER.build_manifest(ROOT)
    assert manifest["model_artifact"]["manifest_sha256"] == ANALYZER.MODEL_MANIFEST_SHA256
    assert manifest["grid"]["resolved_layers_for_28_layer_model"] == [5, 11]
    assert not set(manifest["static_files"]) & BUILDER.FORBIDDEN
    assert set(manifest["forbidden_paths_absent"]) == BUILDER.FORBIDDEN


def test_launcher_is_outcome_blind_and_resume_is_forbidden() -> None:
    source = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert "summary.json" not in source
    assert "interventions.jsonl" not in source
    assert '"analysis_authorized": True' in source
    assert '"resume_policy": "forbidden_new_versioned_freeze_required"' in source


def test_preflight_loads_only_config_and_tokenizer() -> None:
    source = PREFLIGHT_PATH.read_text(encoding="utf-8")
    assert "AutoConfig" in source
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert '"model_forward_count": 0' in source


def test_executable_surface_excludes_protected_banks_and_model_loading() -> None:
    sources = ANALYZER_PATH.read_text(encoding="utf-8") + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in _configs().values()
    )
    assert "p2_confirmatory_targets_v1.jsonl" not in sources
    assert "c1_confirmatory_targets_v1.jsonl" not in sources
    assert "c1_causal_holdout_targets_v1.jsonl" not in sources
    assert "AutoModel" not in sources
    assert "prestage_targets.jsonl" in sources
