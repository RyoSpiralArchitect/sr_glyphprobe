from __future__ import annotations

from pathlib import Path

from glyphprobe.config import EmojiItem, ExperimentConfig, ResolvedInputs
from glyphprobe.experiment.surface import SurfaceExperiment
from glyphprobe.records import GenerationResult


class FakeSurfaceBackend:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, prompt: str, *, seed: int, system_prompt=None, generation_overrides=None):
        self.calls.append(
            {
                "prompt": prompt,
                "seed": seed,
                "system_prompt": system_prompt,
                "generation_overrides": generation_overrides,
            }
        )
        return GenerationResult(
            text=f"answer:{prompt}",
            latency_ms=1.0,
            first_token_logprobs={"a": -0.1, "b": -2.0},
        )


def test_surface_run_resumes_without_regenerating_baselines(tmp_path: Path) -> None:
    cfg = ExperimentConfig.model_validate(
        {
            "mode": "surface",
            "backend": {"kind": "ollama", "model": "fake"},
            "run": {"seeds": [3], "resume": True},
            "panel": {
                "items": [
                    {"id": "a", "glyph": "🟤"},
                    {"id": "b", "glyph": "🟫"},
                ]
            },
            "source": {"wrappers_file": "unused.jsonl"},
            "targets": {"cases_file": "unused.jsonl", "generation_cases": 1},
            "surface": {"enabled_logprobs": False},
        }
    )
    inputs = ResolvedInputs(
        config_path=tmp_path / "config.yaml",
        base_dir=tmp_path,
        panel_items=[EmojiItem(id="a", glyph="🟤"), EmojiItem(id="b", glyph="🟫")],
        wrappers=[{"id": "w", "template": "{emoji}"}],
        targets=[{"id": "t", "prompt": "Question", "group": "g"}],
        input_paths=[],
    )
    first_backend = FakeSurfaceBackend()
    first = SurfaceExperiment(cfg, inputs, first_backend, tmp_path).run()
    assert len(first_backend.calls) == 3
    assert all(call["generation_overrides"] == {"logprobs": False} for call in first_backend.calls)
    assert first["emoji_observation_count"] == 2

    second_backend = FakeSurfaceBackend()
    second = SurfaceExperiment(cfg, inputs, second_backend, tmp_path).run()
    assert second_backend.calls == []
    assert second["observation_count"] == first["observation_count"]
