from __future__ import annotations

import json
from pathlib import Path

import yaml

from glyphprobe.config import load_experiment_config
from glyphprobe.experiment.runner import run_experiment


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_mock_run_is_sealed_and_resumable(tmp_path: Path, monkeypatch) -> None:
    panel = {
        "items": [
            {"id": "brown_circle", "glyph": "🟤", "factors": {"color": "brown", "shape": "circle"}},
            {"id": "brown_square", "glyph": "🟫", "factors": {"color": "brown", "shape": "square"}},
            {"id": "blue_circle", "glyph": "🔵", "factors": {"color": "blue", "shape": "circle"}},
            {"id": "blue_square", "glyph": "🟦", "factors": {"color": "blue", "shape": "square"}},
        ]
    }
    (tmp_path / "panel.yaml").write_text(
        yaml.safe_dump(panel, allow_unicode=True), encoding="utf-8"
    )
    _jsonl(
        tmp_path / "wrappers.jsonl",
        [
            {"id": "w0", "template": "Mark: {emoji}\\nAnchor:"},
            {"id": "w1", "template": "Symbol [{emoji}]\\nContinue:"},
            {"id": "w2", "template": "A {emoji} B\\nResponse:"},
        ],
    )
    _jsonl(
        tmp_path / "targets.jsonl",
        [
            {"id": f"t{i}", "group": f"g{i % 2}", "prompt": f"Explain item {i}."}
            for i in range(4)
        ],
    )
    config = {
        "mode": "internal",
        "backend": {"kind": "mock", "model": "glyphprobe/mock-64d", "device": "cpu"},
        "run": {
            "name": "pytest-smoke",
            "output_root": "runs",
            "seeds": [17],
            "resume": True,
            "wrapper_subsample_fraction": 0.67,
        },
        "panel": {"file": "panel.yaml", "neutral_glyph": "·"},
        "source": {"wrappers_file": "wrappers.jsonl"},
        "targets": {"cases_file": "targets.jsonl", "calibration_cases": 2},
        "capture": {"layers": [0.5]},
        "intervention": {
            "strengths": [0.05],
            "clip": {"mode": "global_rms", "max_ratio": 0.2},
        },
        "controls": {
            "random_directions_per_layer": 2,
            "sign_flip": False,
            "label_shuffle_permutations": 9,
        },
        "metrics": {
            "top_k": 10,
            "fingerprint_dim": 16,
            "split_half_repeats": 5,
            "save_top_logit_deltas": 4,
        },
        "sae": {"enabled": False},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    cfg, inputs = load_experiment_config(config_path)
    run_dir, first = run_experiment(cfg, inputs)
    intervention_count = sum(1 for _ in (run_dir / "interventions.jsonl").open())
    assert first["error_count"] == 0
    assert first["causal_claim_authorized"] is False
    assert (run_dir / "receipt.json").exists()
    assert (run_dir / "fingerprint_summary.jsonl").exists()
    assert (run_dir / "report.md").exists()
    receipt = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["run_seal"] in run_dir.name
    assert receipt["model_identity"]["sha256"]
    assert all("/" not in label for label in receipt["input_hashes"])

    second_dir, second = run_experiment(cfg, inputs)
    assert second_dir == run_dir
    assert second["intervention_record_count"] == first["intervention_record_count"]
    assert sum(1 for _ in (run_dir / "interventions.jsonl").open()) == intervention_count

    from glyphprobe.experiment import runner

    environment = runner._environment_receipt()
    changed_environment = {
        **environment,
        "packages": {**environment["packages"], "numpy": "changed-for-test"},
    }
    monkeypatch.setattr(runner, "_environment_receipt", lambda: changed_environment)
    third_dir, third = run_experiment(cfg, inputs)
    assert third_dir != run_dir
    assert third["intervention_record_count"] == first["intervention_record_count"]
