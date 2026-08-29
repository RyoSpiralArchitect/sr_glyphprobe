from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_glyph_system_reserve_confirmation_v0_result.py"
SPEC = importlib.util.spec_from_file_location("t12_result_validator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_descriptive_summary_and_small_randomization_are_deterministic() -> None:
    values = np.broadcast_to(
        np.asarray([-0.2, -0.1, 0.1, 0.2], dtype=np.float64),
        (9, 8, 4),
    ).copy()
    values[:, :, 2:] += 0.25

    summary = MODULE.descriptive_summary(values)
    first = MODULE.shared_item_swap_randomization_test(values, draws=99, seed=17)
    second = MODULE.shared_item_swap_randomization_test(values, draws=99, seed=17)

    assert np.isclose(summary["global_statistic"], 0.125)
    assert summary["positive_cell_count"] == 72
    assert np.array_equal(first["cell_medians"], second["cell_medians"])
    assert first["exceedances"] == second["exceedances"]
    assert first["p_value"] == second["p_value"]
    assert first["null_statistic_quantiles"] == second["null_statistic_quantiles"]


def test_holm_requires_both_registered_decisions() -> None:
    result = MODULE.holm_correction(
        {"H_ZWJ_FUSION": 0.02, "H_REGIONAL_DUAL": 0.04},
        alpha=0.05,
        hypothesis_order=("H_ZWJ_FUSION", "H_REGIONAL_DUAL"),
    )

    assert result["rejected"] == {
        "H_ZWJ_FUSION": True,
        "H_REGIONAL_DUAL": True,
    }
    assert result["adjusted_p_values"] == {
        "H_ZWJ_FUSION": 0.04,
        "H_REGIONAL_DUAL": 0.04,
    }


def test_git_resident_public_bundle_validates() -> None:
    bundle = ROOT / "artifacts" / "glyph_system_reserve_confirmation_v0"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "validate-public-bundle",
            "--bundle",
            str(bundle),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["status"] == "pass"
    assert payload["outcome_pattern"] == "neither_registered_hypothesis_confirmed"
    assert payload["confirmed_hypotheses"] == []
    assert payload["primary_result_sha256"] == (
        "1dee4bd187c5816d809cec27c4972edb217442e7824ef172a7d5933557d491a6"
    )
    assert MODULE.sha256(bundle / "PUBLIC_MANIFEST.json") == (
        "ee3e5d610d0c7fa3191647bbeb9e44079838e1e0f34da061e0334f7f7ecc244d"
    )
    assert MODULE.sha256(bundle / "SHA256SUMS") == (
        "a81752685e3b8e168a2833fb62b7fa027a71f4ffc9723c77e37c81f695e81a04"
    )


def test_public_bundle_is_bilingual_and_path_scrubbed() -> None:
    bundle = ROOT / "artifacts" / "glyph_system_reserve_confirmation_v0"
    assert (bundle / "README.md").is_file()
    assert (bundle / "README.ja.md").is_file()
    for path in bundle.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "/home/" not in text
