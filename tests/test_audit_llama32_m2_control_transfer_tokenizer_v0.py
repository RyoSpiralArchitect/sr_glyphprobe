from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_llama32_m2_control_transfer_tokenizer_v0.py"
CONFIG = ROOT / "configs" / "llama32_3b_instruct_m2_control_transfer_tokenizer_v0.yaml"
SPEC = importlib.util.spec_from_file_location("audit_llama32_m2_transfer_v0", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(prefix: list[int]) -> dict:
    feature = AUDIT._canonical_histogram(
        [{"token_count": 3, "prefix_token_ids": prefix}]
    )
    wrapper = {
        "full_token_count_histogram": AUDIT._canonical_histogram([8]),
        "glyph_span_count_histogram": AUDIT._canonical_histogram([3]),
        "glyph_prefix_histogram": AUDIT._canonical_histogram([prefix]),
        "position_and_outside_histogram": AUDIT._canonical_histogram(
            [
                {
                    "glyph_token_positions": [2, 3, 4],
                    "outside_span_token_ids": [10, 11, 12],
                    "left_boundary_absorbed": False,
                    "right_boundary_absorbed": False,
                }
            ]
        ),
        "full_feature_histogram": AUDIT._canonical_histogram(
            [
                {
                    "full_token_count": 8,
                    "glyph_span_token_count": 3,
                    "glyph_prefix_token_ids": prefix,
                    "glyph_token_positions": [2, 3, 4],
                    "outside_span_token_ids": [10, 11, 12],
                    "left_boundary_absorbed": False,
                    "right_boundary_absorbed": False,
                }
            ]
        ),
    }
    return {
        "panel_id": "panel",
        "item_count": 1,
        "raw_token_count_histogram": AUDIT._canonical_histogram([3]),
        "raw_prefix_histogram": AUDIT._canonical_histogram([prefix]),
        "raw_feature_histogram": feature,
        "wrapper_summaries": {"w01": wrapper},
    }


def test_config_binds_only_panels_wrappers_and_tokenizer_files() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["status"] == AUDIT.EXPECTED_STATUS
    assert config["claim_boundary"] == {
        "scientific_result": False,
        "experimental_grid_authorized": False,
        "model_selection_authorized": False,
        "language_model_loaded": False,
        "study_target_banks_accessed": False,
    }
    panel_specs = [config["reference_panel"], *config["candidate_panels"]]
    for row in panel_specs:
        path = (CONFIG.parent / row["path"]).resolve()
        assert AUDIT.ALLOWED_PANEL_ROOT in path.parents
        assert _sha256(path) == row["sha256"]
    wrapper = config["wrappers"]
    wrapper_path = (CONFIG.parent / wrapper["path"]).resolve()
    assert AUDIT.ALLOWED_WRAPPER_ROOT in wrapper_path.parents
    assert _sha256(wrapper_path) == wrapper["sha256"]


def test_prefix_is_every_token_except_the_final_token() -> None:
    assert AUDIT._prefix([1, 2, 3]) == [1, 2]
    assert AUDIT._prefix([7, 8]) == [7]
    assert AUDIT._prefix([9]) == []


def test_exact_summary_match_passes_transfer_gate() -> None:
    reference = _summary([101, 202])
    candidate = _summary([101, 202])
    comparison = AUDIT._compare_summaries(reference, candidate)
    assert comparison["transfer_gate_pass"] is True
    assert all(comparison["checks"].values())


def test_prefix_change_fails_raw_and_contextual_gate() -> None:
    reference = _summary([101, 202])
    candidate = _summary([101, 999])
    comparison = AUDIT._compare_summaries(reference, candidate)
    assert comparison["transfer_gate_pass"] is False
    assert comparison["checks"]["raw_token_count_histogram_match"] is True
    assert comparison["checks"]["raw_prefix_histogram_match"] is False
    assert comparison["checks"]["all_wrapper_full_feature_histograms_match"] is False


def test_script_has_no_model_or_target_loader_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AutoTokenizer" in source
    assert "AutoModel" not in source
    assert "data/targets" not in source
    assert "language-model weights" in source
