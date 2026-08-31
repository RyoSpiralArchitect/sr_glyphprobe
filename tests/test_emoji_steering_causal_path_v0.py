from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emoji_steering_causal_path_v0.py"
SPEC = importlib.util.spec_from_file_location("t14c_causal", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _ToyAttention(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.projection = nn.Linear(width, width, bias=False)

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        return self.projection(hidden)


class _ToyMLP(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.projection = nn.Linear(width, width, bias=False)

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        return self.projection(torch.tanh(hidden))


class _ToyBlock(nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.self_attn = _ToyAttention(width)
        self.mlp = _ToyMLP(width)

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        hidden = hidden + self.self_attn(hidden)
        return hidden + self.mlp(hidden)


class _ToyModel(nn.Module):
    def __init__(self, *, width: int = 8, vocab: int = 17) -> None:
        super().__init__()
        torch.manual_seed(20260831)
        self.embedding = nn.Embedding(vocab, width)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList([_ToyBlock(width) for _ in range(28)])
        self.lm_head = nn.Linear(width, vocab, bias=False)

    def forward(
        self,
        *,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        use_cache: bool,
        return_dict: bool,
    ) -> SimpleNamespace:
        del attention_mask, use_cache, return_dict
        hidden = self.embedding(input_ids)
        for block in self.model.layers:
            hidden = block(hidden)
        return SimpleNamespace(logits=self.lm_head(hidden))


def _toy_patch(site: str, block_index: int) -> dict[str, np.ndarray]:
    model = _ToyModel().eval()
    generator = np.random.default_rng(20260831)
    unit = generator.standard_normal((3, 8)).astype(np.float32)
    unit /= np.sqrt(np.mean(np.square(unit), axis=1, keepdims=True))
    return MODULE.causal_patch_batch(
        torch=torch,
        model=model,
        input_ids_single=torch.tensor([[1, 2, 3, 4]], dtype=torch.long),
        attention_mask_single=torch.ones((1, 4), dtype=torch.long),
        blocks=model.model.layers,
        unit_vectors=unit,
        target_rms=1.0,
        site=site,
        block_index=block_index,
    )


def test_design_arithmetic_and_holdout_boundary() -> None:
    design = MODULE.audit_design()
    assert design["status"] == "pass"
    assert design["fixed_model_role"] == "llama32_3b_base_bf16"
    assert design["signed_conditions_per_target"] == 80
    assert design["localization_targets"] == 32
    assert design["localization_response_records"] == 25_600
    assert design["c1_v2_targets_planned"] == 192
    assert design["c1_v2_response_records_planned"] == 15_360
    assert design["localization_outcomes_opened"] is False
    assert design["c1_v2_bank_generated"] is False
    assert design["c1_v2_target_rows_opened"] == 0
    assert not (ROOT / MODULE.SITE_MANIFEST_PATH).exists()


def test_target_generator_is_deterministic_without_opening_production_seed() -> None:
    first = MODULE.build_target_rows(123)
    second = MODULE.build_target_rows(123)
    changed = MODULE.build_target_rows(124)
    assert first == second
    assert first != changed
    assert len(first) == 192
    assert {row["group"] for row in first} == set(MODULE._TARGET_GROUPS)
    assert all(
        sum(row["group"] == group for row in first) == 16
        for group in MODULE._TARGET_GROUPS
    )
    assert "2026090101" not in SCRIPT.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("site", "block_index"),
    [("attn_out", 24), ("mlp_out", 27), ("resid_pre", 24), ("mlp_out", 22)],
)
def test_causal_patch_shapes_and_restoration_fidelity(
    site: str, block_index: int
) -> None:
    result = _toy_patch(site, block_index)
    assert result["baseline"].shape == (1, 17)
    assert result["zero"].shape == (1, 17)
    assert np.array_equal(result["baseline"], result["zero"])
    for key in ("treatment", "necessity", "sufficiency", "restoration"):
        assert result[key].shape == (3, 17)
        assert np.isfinite(result[key]).all()
    assert np.allclose(result["restoration"], result["treatment"], atol=1e-6)


def test_positive_control_erases_and_reconstructs_treatment() -> None:
    result = _toy_patch("resid_pre", 24)
    repeated_baseline = np.repeat(result["baseline"], 3, axis=0)
    assert np.allclose(result["necessity"], repeated_baseline, atol=1e-6)
    assert np.allclose(result["sufficiency"], result["treatment"], atol=1e-6)
    sufficiency_error = MODULE._scalar_metrics(
        result["treatment"], result["sufficiency"]
    )
    assert np.max(sufficiency_error["js"]) == pytest.approx(0.0, abs=1e-15)
    assert not np.allclose(result["treatment"], repeated_baseline, atol=1e-6)


def test_upstream_sham_has_no_mediation_effect() -> None:
    result = _toy_patch("mlp_out", 22)
    repeated_baseline = np.repeat(result["baseline"], 3, axis=0)
    assert np.allclose(result["necessity"], result["treatment"], atol=1e-6)
    assert np.allclose(result["sufficiency"], repeated_baseline, atol=1e-6)


def test_metric_identity_and_positive_divergence() -> None:
    baseline = np.asarray([[0.2, -0.1, 0.3]], dtype=np.float32)
    identity = MODULE._scalar_metrics(baseline, baseline)
    assert identity["js"][0] == pytest.approx(0.0, abs=1e-15)
    assert identity["tv"][0] == pytest.approx(0.0, abs=1e-15)
    changed = MODULE._scalar_metrics(
        baseline, np.asarray([[0.8, -0.2, -0.4]], dtype=np.float32)
    )
    assert changed["js"][0] > 0
    assert changed["tv"][0] > 0


def test_target_estimands_preserve_target_as_sampling_unit() -> None:
    rows = []
    for target_index in range(2):
        for condition_index in range(80):
            structured = condition_index < 48
            rows.append(
                {
                    "target_id": f"target-{target_index}",
                    "target_group": "continuation",
                    "direction_kind": (
                        "structured_glyph_system_prototype"
                        if structured
                        else "signed_source_covariance_null"
                    ),
                    "treatment_js": 0.4 + target_index if structured else 0.1,
                    "necessity_drop_js": 0.2 + target_index if structured else 0.05,
                    "sufficiency_js": 0.3 + target_index if structured else 0.02,
                }
            )
    estimands = MODULE._target_estimands(rows)
    assert len(estimands) == 2
    assert estimands[0]["treatment_excess_js"] == pytest.approx(0.3)
    assert estimands[0]["necessity_excess_js"] == pytest.approx(0.15)
    assert estimands[0]["sufficiency_excess_js"] == pytest.approx(0.28)


def test_resampling_is_deterministic_and_directional() -> None:
    groups = [group for group in MODULE._TARGET_GROUPS for _ in range(16)]
    values = np.linspace(0.1, 0.3, 192)
    first = MODULE._bootstrap_median(values, groups, replicates=200, seed=17)
    second = MODULE._bootstrap_median(values, groups, replicates=200, seed=17)
    assert np.array_equal(first, second)
    assert np.all(first > 0)
    positive_p = MODULE._sign_flip_p_value(values, draws=999, seed=18)
    negative_p = MODULE._sign_flip_p_value(-values, draws=999, seed=18)
    assert positive_p < 0.05
    assert negative_p > 0.95


def _write_synthetic_localization_site(
    root: Path, site: str, block_index: int, necessity_score: float
) -> None:
    directory = MODULE._site_directory(root, "localization", site, block_index)
    rows = []
    for target_index in range(32):
        for condition_index in range(80):
            structured = condition_index < 48
            treatment_js = 0.01 if structured else 0.002
            necessity_drop = necessity_score if structured else 0.0
            necessity_js = max(0.0, treatment_js - necessity_drop)
            sufficiency_error = 0.0
            if (site, block_index) == ("resid_pre", 24):
                necessity_drop = treatment_js
                necessity_js = 0.0
            if (site, block_index) == ("mlp_out", 22):
                necessity_drop = 0.0
                necessity_js = treatment_js
            rows.append(
                {
                    "schema_version": MODULE.SCHEMA_VERSION,
                    "protocol_id": MODULE.PROTOCOL_ID,
                    "phase": "localization",
                    "site": site,
                    "block_index": block_index,
                    "target_index": target_index,
                    "target_id": f"target-{target_index:02d}",
                    "target_group": "continuation",
                    "condition_index": condition_index,
                    "direction_kind": (
                        "structured_glyph_system_prototype"
                        if structured
                        else "signed_source_covariance_null"
                    ),
                    "treatment_js": treatment_js,
                    "necessity_js": necessity_js,
                    "necessity_drop_js": necessity_drop,
                    "sufficiency_js": treatment_js * 0.5,
                    "sufficiency_error_js": sufficiency_error,
                    "sufficiency_error_logit_rms": 0.0,
                    "restoration_error_js": 0.0,
                    "restoration_error_logit_rms": 0.0,
                }
            )
    directory.mkdir(parents=True)
    ledger = directory / "response_ledger.jsonl"
    MODULE._write_jsonl(ledger, rows)
    MODULE._write_json(
        directory / "receipt.json",
        {
            "protocol_id": MODULE.PROTOCOL_ID,
            "status": "site_complete",
            "phase": "localization",
            "site": site,
            "block_index": block_index,
            "response_rows": 2560,
            "response_ledger_sha256": MODULE._sha256(ledger),
            "maximum_restoration_error_js": 0.0,
            "maximum_restoration_error_logit_rms": 0.0,
            "maximum_explicit_zero_js": 0.0,
        },
    )


def test_frozen_selector_uses_necessity_score_and_fixed_roster(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    localization_root = tmp_path / "localization-run"
    for rank, (site, block_index) in enumerate(MODULE._candidate_sites(), 1):
        _write_synthetic_localization_site(
            localization_root, site, block_index, rank * 0.001
        )
    _write_synthetic_localization_site(localization_root, "resid_pre", 24, 0.0)
    _write_synthetic_localization_site(localization_root, "mlp_out", 22, 0.0)
    summary = MODULE._phase_summary_path(localization_root, "localization")
    MODULE._write_json(
        summary,
        {
            "protocol_id": MODULE.PROTOCOL_ID,
            "status": "localization_complete",
            "response_rows": 25_600,
        },
    )
    fake_freeze = tmp_path / "freeze.json"
    fake_freeze.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(MODULE, "FREEZE_PATH", fake_freeze)
    monkeypatch.setattr(MODULE, "audit_freeze", lambda: {"status": "pass"})
    output = tmp_path / "site-manifest.json"
    selected = MODULE.select_site(localization_root, output)
    assert selected["site"] == "mlp_out"
    assert selected["block_index"] == 27
    manifest = MODULE._read_json(output)
    assert manifest["control_evidence"]["positive_control_pass"] is True
    assert manifest["control_evidence"]["upstream_sham_pass"] is True
    assert manifest["c1_v2_target_rows_generated"] == 0


def test_bilingual_protocols_bind_the_same_causal_counts() -> None:
    english = (ROOT / "docs" / "EMOJI_STEERING_CAUSAL_PATH_V0.md").read_text(
        encoding="utf-8"
    )
    japanese = (ROOT / "docs" / "EMOJI_STEERING_CAUSAL_PATH_V0.ja.md").read_text(
        encoding="utf-8"
    )
    for text in (english, japanese):
        assert "25,600" in text
        assert "15,360" in text
        assert "20,000" in text
        assert "99,999" in text
        assert "C1 v2" in text
