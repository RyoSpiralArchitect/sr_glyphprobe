from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_emoji_word_incongruence_replication_v0.py"
SPEC = importlib.util.spec_from_file_location("t15b_analysis", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _synthetic_a1(smollm_value: float, mistral_value: float) -> dict[str, object]:
    values = {
        "smollm2_1p7b_base_bf16": smollm_value,
        "mistral7b_instruct_v03_bf16": mistral_value,
    }
    rows = []
    for role, value in values.items():
        for target in MODULE.t15.targets():
            for site_index in MODULE.t15.SITE_INDICES:
                for sign in (-1, 1):
                    rows.append(
                        {
                            "model": role,
                            "site_index": site_index,
                            "target_id": target["id"],
                            "magnitude": 0.25,
                            "sign": sign,
                            "value": value,
                        }
                    )
    return {"target_estimands": rows}


def test_r1_requires_both_frozen_models() -> None:
    supported = MODULE._r1(_synthetic_a1(0.20, 0.10))
    assert supported["decision"] == "support"
    assert supported["replication_support"] is True
    assert all(row["lower_bound_above_zero"] for row in supported["summary"])

    boundary = MODULE._r1(_synthetic_a1(0.20, -0.10))
    assert boundary["decision"] == "not_supported"
    assert boundary["replication_support"] is False
    assert [row["lower_bound_above_zero"] for row in boundary["summary"]] == [
        True,
        False,
    ]


def test_analysis_family_order_and_claim_boundary_are_frozen() -> None:
    assert MODULE.FAMILIES[0] == "R1_pooled_A1_prospective_replication"
    assert len(MODULE.FAMILIES) == 8
    config = MODULE.t15._config()["analysis"]["primary_replication_family"]
    assert config["no_model_pooling_for_decision"] is True
    assert config["magnitude"] == 0.25
    assert "both" in config["decision_rule"]
    assert (
        MODULE.t15._config()["next_gate"].startswith(
            "T15-C may be frozen only after T15-B closes"
        )
    )
