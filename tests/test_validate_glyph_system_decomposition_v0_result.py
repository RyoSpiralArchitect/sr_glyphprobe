from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_glyph_system_decomposition_v0_result.py"
SPEC = importlib.util.spec_from_file_location("t11_result_validator", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_independent_rank_and_variance_helpers_cover_ties_and_pure_effects() -> None:
    assert np.allclose(MODULE.rankdata(np.asarray([4.0, 2.0, 2.0, 8.0])), [3.0, 1.5, 1.5, 4.0])
    assert MODULE.safe_spearman(np.arange(8), np.arange(8)[::-1]) == -1.0
    assert MODULE.safe_spearman(np.ones(8), np.arange(8)) == 0.0

    grid = np.broadcast_to(np.asarray([0.0, 1.0, 2.0])[:, None, None], (3, 2, 4))
    result = MODULE.balanced_three_way(grid)

    assert result["balanced_shape_model_by_system_by_context"] == [3, 2, 4]
    assert np.isclose(result["components"]["model"]["share_of_total_sum_squares"], 1.0)
    assert all(
        np.isclose(component["share_of_total_sum_squares"], 0.0)
        for name, component in result["components"].items()
        if name != "model"
    )
    assert result["sum_squares_reconciliation_error"] < 1e-12


def test_cell_distribution_keeps_descriptive_interval_directions_separate() -> None:
    rows = []
    for median, interval in ((0.2, [0.1, 0.3]), (-0.2, [-0.3, -0.1]), (0.0, [-0.1, 0.1])):
        rows.append(
            {
                "matched_incorrect_label_advantage": {
                    "glyph_unicode_name": {
                        "median": median,
                        "bootstrap_percentile_95_interval": interval,
                    }
                },
                "decomposition_contrasts": {},
            }
        )

    result = MODULE.metric_cell_distribution(rows, "matched_glyph_unicode_name")

    assert result["count"] == 3
    assert result["median"] == 0.0
    assert result["descriptive_bootstrap_interval_positive_count"] == 1
    assert result["descriptive_bootstrap_interval_negative_count"] == 1
    assert result["descriptive_bootstrap_interval_includes_zero_count"] == 1


def test_validation_output_is_hash_bound_and_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "validation"
    payload = {
        "status": "pass",
        "overall_assessment": "share_with_caveats",
        "independent_recomputations": {
            "stored_item_margin_cell_medians": {"total_checked": 2},
            "cross_model_item_margin_agreement": {"rows_recomputed": 1},
            "balanced_three_way_variance": {"metrics_recomputed": 1},
            "depth_trajectories": {"rows_recomputed": 1},
        },
    }
    report = MODULE.build_report(payload)

    MODULE.write_output(output, payload, report)

    assert MODULE.verify_sha256sums(output) == {
        "independent_validation.json": MODULE.sha256(output / "independent_validation.json"),
        "report.md": MODULE.sha256(output / "report.md"),
    }
    assert json.loads((output / "independent_validation.json").read_text())["status"] == "pass"
    with pytest.raises(MODULE.ValidationError, match="Output already exists"):
        MODULE.write_output(output, payload, report)


def test_checksum_verification_rejects_targets_outside_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    external = tmp_path / "external.txt"
    external.write_text("not bundle data\n", encoding="utf-8")
    (bundle / "SHA256SUMS").write_text(
        f"{MODULE.sha256(external)}  ../external.txt\n",
        encoding="utf-8",
    )

    with pytest.raises(MODULE.ValidationError, match="Unsafe checksum target"):
        MODULE.verify_sha256sums(bundle)


def test_git_resident_public_bundle_validates() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "package_glyph_system_decomposition_v0_public_bundle.py"),
            "validate",
            "--bundle",
            str(ROOT / "artifacts" / "glyph_system_decomposition_v0"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload == {
        "payload_files": 11,
        "public_manifest_sha256": "eea2e21b2a00a81de28b5f55c5214d31891956dd7e90905e76d992553741527d",
        "sha256sums_sha256": "e819f8da7bdbb8f4bc2ec303cdae2720c298c868ff2157a2676c577fee15e163",
        "status": "pass",
    }
