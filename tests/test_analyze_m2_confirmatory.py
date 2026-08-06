from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "analyze_m2_confirmatory.py"
SPEC = importlib.util.spec_from_file_location("analyze_m2_confirmatory_script", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FINGERPRINT_DIM = 12
GROUPS = (
    "continuation",
    "factual",
    "reasoning",
    "procedural",
    "classification",
    "planning",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unit(index: int) -> list[float]:
    vector = np.zeros(FINGERPRINT_DIM, dtype=np.float64)
    vector[index] = 1.0
    return vector.tolist()


def _resolved_config(role: str) -> dict:
    return {
        "schema_version": 1,
        "mode": "internal",
        "backend": {
            "kind": "mlx",
            "model": "openai-community/gpt2",
            "revision": "607a30d783dfa663caf39e06633721c8d4cfcd7e",
            "device": "gpu",
            "dtype": "float32",
            "local_files_only": True,
            "validation_receipt_sha256": MODULE.PINNED_PARITY_RECEIPT_SHA256,
        },
        "run": {
            "name": f"synthetic-{role}",
            "output_root": "../runs",
            "seeds": [101, 211, 307],
            "replicate_mode": "wrapper_subsample",
        },
        "panel": {"file": f"../data/{role}.yaml", "centroid_mode": "panel"},
        "source": {"wrappers_file": "../data/wrappers/source_wrappers.jsonl"},
        "targets": {
            "cases_file": "../data/targets/p2_confirmatory_targets_v1.jsonl",
            "max_cases": 48,
        },
        "capture": {"site": "resid_post", "layers": [2, 4]},
        "intervention": {"normalization": "rms", "strengths": [0.05]},
        "controls": {
            "random_directions_per_layer": 0,
            "zero_direction": True,
            "sign_flip": False,
            "include_neutral_direction": False,
        },
        "metrics": {
            "fingerprint_dim": FINGERPRINT_DIM,
            "fingerprint_seed": 8_675_309,
        },
        "surface": {"emoji_template": "{emoji}\n{prompt}"},
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _build_runs(tmp_path: Path, *, equivalent: bool = False) -> tuple[Path, list[Path]]:
    roles = ("primary", "null_a", "null_b", "null_c")
    run_dirs: list[Path] = []
    targets = [
        (f"{group[:4]}_{index:02d}", group)
        for group in GROUPS
        for index in range(8)
    ]
    for role in roles:
        run_dir = tmp_path / role
        run_dir.mkdir()
        (run_dir / "resolved_config.yaml").write_text(
            yaml.safe_dump(_resolved_config(role), sort_keys=False), encoding="utf-8"
        )
        (run_dir / "receipt.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "input_hashes": {
                        "input_01:receipt.json": MODULE.PINNED_PARITY_RECEIPT_SHA256,
                        "input_04:p2_confirmatory_targets_v1.jsonl": (
                            MODULE.FROZEN_P2_TARGET_SHA256
                        ),
                    },
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "resolved_inputs.json").write_text(
            json.dumps({"target_ids": [target_id for target_id, _ in targets]}),
            encoding="utf-8",
        )
        rows: list[dict] = []
        condition_ids = [f"{role}_condition_{index:02d}" for index in range(10)]
        for layer in (2, 4):
            for seed in (101, 211, 307):
                for condition_index, condition_id in enumerate(condition_ids):
                    for target_id, target_group in targets:
                        identifiable = (
                            role == "primary" and not equivalent and seed in (101, 211)
                        )
                        fingerprint = _unit(condition_index if identifiable else 10)
                        rows.append(
                            {
                                "layer": layer,
                                "strength": 0.05,
                                "seed": seed,
                                "sign": 1,
                                "calibration": "rms",
                                "condition_type": "emoji",
                                "condition_id": condition_id,
                                "target_id": target_id,
                                "target_group": target_group,
                                "distribution": {"fingerprint": fingerprint},
                            }
                        )
        _write_jsonl(run_dir / "interventions.jsonl", rows)
        run_dirs.append(run_dir)
    return run_dirs[0], run_dirs[1:]


@pytest.fixture()
def positive_analysis(tmp_path: Path) -> tuple[dict, Path]:
    primary, nulls = _build_runs(tmp_path)
    output_dir = tmp_path / "analysis"
    receipt = MODULE.analyze_confirmatory(
        primary,
        nulls,
        output_dir=output_dir,
        fingerprint_dim=FINGERPRINT_DIM,
        bootstrap_replicates=199,
        sign_flip_draws=999,
        strict_protocol=False,
    )
    return receipt, output_dir


def test_positive_effect_is_robust_and_outputs_are_hashed(
    positive_analysis: tuple[dict, Path],
) -> None:
    receipt, output_dir = positive_analysis

    assert [result["status"] for result in receipt["primary_results"]] == [
        MODULE.STATUS_ROBUST,
        MODULE.STATUS_ROBUST,
    ]
    assert all(
        result["bootstrap_ci_95"]["low"] > 0.06
        and result["holm_adjusted_one_sided_p"] < 0.05
        for result in receipt["primary_results"]
    )
    effects_path = output_dir / "m2_target_effects.jsonl"
    report_path = output_dir / "m2_confirmatory_report.md"
    assert receipt["outputs"]["target_effects"]["sha256"] == _sha256(effects_path)
    assert receipt["outputs"]["report"]["sha256"] == _sha256(report_path)
    assert "semantic, mechanistic, or causal glyph effect" in report_path.read_text()
    assert receipt["protocol_conformant"] is False
    assert "NON-PROTOCOL SYNTHETIC VALIDATION" in report_path.read_text()
    assert str(output_dir.parent) not in json.dumps(receipt)
    assert str(output_dir.parent) not in report_path.read_text()


def test_equivalent_effect_gets_protocol_equivalence_status(tmp_path: Path) -> None:
    primary, nulls = _build_runs(tmp_path, equivalent=True)
    receipt = MODULE.analyze_confirmatory(
        primary,
        nulls,
        output_dir=tmp_path / "analysis",
        fingerprint_dim=FINGERPRINT_DIM,
        bootstrap_replicates=99,
        sign_flip_draws=199,
        strict_protocol=False,
    )

    for result in receipt["primary_results"]:
        assert result["mean_adjusted_target_effect"] == pytest.approx(0.0)
        assert result["bootstrap_ci_95"]["low"] == pytest.approx(0.0)
        assert result["bootstrap_ci_95"]["high"] == pytest.approx(0.0)
        assert result["status"] == MODULE.STATUS_EQUIVALENT


def test_cell_grid_mismatch_fails_closed(tmp_path: Path) -> None:
    primary, nulls = _build_runs(tmp_path)
    bad_path = nulls[2] / "interventions.jsonl"
    rows = [json.loads(line) for line in bad_path.read_text().splitlines()]
    rows = [row for row in rows if row["layer"] != 4]
    _write_jsonl(bad_path, rows)

    with pytest.raises(MODULE.M2AnalysisError, match="cell grid"):
        MODULE.analyze_confirmatory(
            primary,
            nulls,
            output_dir=tmp_path / "analysis",
            fingerprint_dim=FINGERPRINT_DIM,
            bootstrap_replicates=9,
            sign_flip_draws=9,
            strict_protocol=False,
        )


def test_direction_seeds_are_nested_not_sample_size(
    positive_analysis: tuple[dict, Path],
) -> None:
    receipt, output_dir = positive_analysis
    boundary = receipt["independence_boundary"]
    assert boundary["effective_n_per_layer"] == 48
    assert boundary["direction_seed_replicates_per_target"] == 3
    assert boundary["direction_seeds_averaged_within_target"] is True
    assert boundary["direction_seeds_counted_as_independent_observations"] is False

    rows = [
        json.loads(line)
        for line in (output_dir / "m2_target_effects.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 2 * 48
    first = rows[0]
    assert list(first["primary_seed_scores"].values()) == pytest.approx([1.0, 1.0, 0.0])
    assert first["primary_score"] == pytest.approx(2.0 / 3.0)
    assert first["adjusted_target_effect_D"] == pytest.approx(2.0 / 3.0)


def test_strict_protocol_rejects_nondefault_parameter_before_reading_runs(
    tmp_path: Path,
) -> None:
    with pytest.raises(MODULE.M2AnalysisError, match="Strict protocol parameter mismatch"):
        MODULE.analyze_confirmatory(
            tmp_path / "primary",
            [tmp_path / "a", tmp_path / "b", tmp_path / "c"],
            output_dir=tmp_path / "analysis",
            delta=0.061,
        )


def test_cli_exposes_no_scientific_parameter_bypass(tmp_path: Path) -> None:
    argv = [
        "--primary-run",
        str(tmp_path / "primary"),
        "--matched-null-runs",
        str(tmp_path / "a"),
        str(tmp_path / "b"),
        str(tmp_path / "c"),
        "--output-dir",
        str(tmp_path / "analysis"),
        "--delta",
        "0.061",
    ]
    with pytest.raises(SystemExit):
        MODULE._build_parser().parse_args(argv)


def test_cli_always_calls_strict_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict = {}

    def fake_analyze(primary: Path, nulls: list[Path], **kwargs: object) -> dict:
        observed.update({"primary": primary, "nulls": nulls, **kwargs})
        return {"primary_results": [{"layer": 2, "status": MODULE.STATUS_UNRESOLVED}]}

    monkeypatch.setattr(MODULE, "analyze_confirmatory", fake_analyze)
    exit_code = MODULE.main(
        [
            "--primary-run",
            str(tmp_path / "primary"),
            "--matched-null-runs",
            str(tmp_path / "a"),
            str(tmp_path / "b"),
            str(tmp_path / "c"),
            "--output-dir",
            str(tmp_path / "analysis"),
        ]
    )

    assert exit_code == 0
    assert observed["strict_protocol"] is True
    assert len(observed["nulls"]) == 3


def test_wrong_frozen_target_input_hash_fails_closed(tmp_path: Path) -> None:
    primary, nulls = _build_runs(tmp_path)
    receipt_path = primary / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["input_hashes"]["input_04:p2_confirmatory_targets_v1.jsonl"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(MODULE.M2AnalysisError, match="missing frozen evidence"):
        MODULE.analyze_confirmatory(
            primary,
            nulls,
            output_dir=tmp_path / "analysis",
            fingerprint_dim=FINGERPRINT_DIM,
            bootstrap_replicates=9,
            sign_flip_draws=9,
            strict_protocol=False,
        )


def test_repository_p2_bank_hash_and_group_grid_are_frozen() -> None:
    groups, path = MODULE._load_frozen_target_groups()

    assert path.name == "p2_confirmatory_targets_v1.jsonl"
    assert len(groups) == 48
    assert set(groups.values()) == set(MODULE.EXPECTED_TARGET_GROUPS)
    assert all(list(groups.values()).count(group) == 8 for group in MODULE.EXPECTED_TARGET_GROUPS)
