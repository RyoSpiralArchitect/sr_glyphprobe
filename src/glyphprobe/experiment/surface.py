from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from glyphprobe.analysis.metrics import logprob_dict_metrics
from glyphprobe.analysis.text import text_delta_metrics
from glyphprobe.config import ExperimentConfig, ResolvedInputs
from glyphprobe.io import append_jsonl, read_jsonl, stable_hash, write_json
from glyphprobe.records import GenerationResult
from glyphprobe.seed import seed_everything


class SurfaceExperiment:
    """Prompt-surface control path for OpenAI-compatible serving backends."""

    def __init__(
        self,
        cfg: ExperimentConfig,
        inputs: ResolvedInputs,
        backend: Any,
        run_dir: Path,
    ):
        self.cfg = cfg
        self.inputs = inputs
        self.backend = backend
        self.run_dir = run_dir
        self.path = run_dir / "surface_observations.jsonl"
        self.error_path = run_dir / "errors.jsonl"
        existing_rows = read_jsonl(self.path)
        self.completed = {
            str(row.get("task_id"))
            for row in existing_rows
            if row.get("task_id")
        }
        self.existing_by_task = {
            str(row["task_id"]): row
            for row in existing_rows
            if row.get("task_id")
        }
        self.errors = 0

    def _record_error(self, task_id: str, exc: Exception) -> None:
        self.errors += 1
        append_jsonl(
            self.error_path,
            {
                "stage": "surface_generation",
                "task_id": task_id,
                "error_type": type(exc).__name__,
                "error": repr(exc),
                "time": time.time(),
            },
        )
        if self.cfg.run.fail_fast or self.errors >= self.cfg.run.max_errors:
            raise exc

    def run(self) -> dict[str, Any]:
        targets = self.inputs.targets[: self.cfg.targets.generation_cases]
        for seed in self.cfg.run.seeds:
            seed_everything(seed)
            for target_index, target in enumerate(targets):
                baseline_payload = {
                    "kind": "baseline",
                    "seed": seed,
                    "target_id": target["id"],
                }
                baseline_id = stable_hash(baseline_payload, length=24)
                baseline_prompt = self.cfg.surface.neutral_template.format(
                    prompt=target["prompt"], emoji=""
                )
                try:
                    existing_baseline = self.existing_by_task.get(baseline_id)
                    if existing_baseline is not None and self.cfg.run.resume:
                        baseline = GenerationResult(
                            text=str(existing_baseline.get("text", "")),
                            latency_ms=float(existing_baseline.get("latency_ms", 0.0)),
                            usage=dict(existing_baseline.get("usage", {})),
                            first_token_logprobs=dict(
                                existing_baseline.get("first_token_logprobs", {})
                            ),
                            metadata={
                                **dict(existing_baseline.get("backend_metadata", {})),
                                "resumed_from_artifact": True,
                            },
                        )
                    else:
                        baseline = self.backend.generate(
                            baseline_prompt,
                            seed=seed,
                            system_prompt=self.cfg.surface.system_prompt,
                            generation_overrides={
                                "logprobs": self.cfg.surface.enabled_logprobs
                            },
                        )
                    if baseline_id not in self.completed:
                        baseline_row = {
                            "task_id": baseline_id,
                            **baseline_payload,
                            "target_index": target_index,
                            "target_group": target.get("group", "unspecified"),
                            "text": baseline.text,
                            "latency_ms": baseline.latency_ms,
                            "usage": baseline.usage,
                            "first_token_logprobs": baseline.first_token_logprobs,
                            "backend_metadata": baseline.metadata,
                            "claim_stage": "surface-observational-only",
                        }
                        append_jsonl(self.path, baseline_row)
                        self.existing_by_task[baseline_id] = baseline_row
                        self.completed.add(baseline_id)
                except Exception as exc:
                    self._record_error(baseline_id, exc)
                    continue

                for item in self.inputs.panel_items:
                    payload = {
                        "kind": "emoji_surface",
                        "seed": seed,
                        "target_id": target["id"],
                        "emoji_id": item.id,
                    }
                    task_id = stable_hash(payload, length=24)
                    if task_id in self.completed:
                        continue
                    prompt = self.cfg.surface.emoji_template.format(
                        emoji=item.glyph,
                        prompt=target["prompt"],
                    )
                    try:
                        changed = self.backend.generate(
                            prompt,
                            seed=seed,
                            system_prompt=self.cfg.surface.system_prompt,
                            generation_overrides={
                                "logprobs": self.cfg.surface.enabled_logprobs
                            },
                        )
                        append_jsonl(
                            self.path,
                            {
                                "task_id": task_id,
                                **payload,
                                "glyph": item.glyph,
                                "factors": item.factors,
                                "target_index": target_index,
                                "target_group": target.get("group", "unspecified"),
                                "text": changed.text,
                                "baseline_task_id": baseline_id,
                                "text_delta": text_delta_metrics(
                                    baseline.text,
                                    changed.text,
                                    glyph=item.glyph,
                                ),
                                "first_token_logprob_delta": logprob_dict_metrics(
                                    baseline.first_token_logprobs,
                                    changed.first_token_logprobs,
                                ),
                                "latency_ms": changed.latency_ms,
                                "baseline_latency_ms": baseline.latency_ms,
                                "usage": changed.usage,
                                "first_token_logprobs": changed.first_token_logprobs,
                                "backend_metadata": changed.metadata,
                                "claim_stage": "surface-observational-only",
                            },
                        )
                        self.completed.add(task_id)
                    except Exception as exc:
                        self._record_error(task_id, exc)

        rows = read_jsonl(self.path)
        emoji_rows = [row for row in rows if row.get("kind") == "emoji_surface"]
        similarity = [
            float(row["text_delta"]["sequence_similarity"])
            for row in emoji_rows
            if row.get("text_delta")
        ]
        exact = [
            bool(row["text_delta"]["exact_match"])
            for row in emoji_rows
            if row.get("text_delta")
        ]
        logprob_available = [
            bool(row.get("first_token_logprob_delta", {}).get("available"))
            for row in emoji_rows
        ]
        summary = {
            "stage": "surface-observational-only",
            "causal_claim_authorized": False,
            "internal_activation_access": False,
            "emoji_count": len(self.inputs.panel_items),
            "target_case_count": len(targets),
            "seed_count": len(self.cfg.run.seeds),
            "observation_count": len(rows),
            "emoji_observation_count": len(emoji_rows),
            "mean_sequence_similarity": float(np.mean(similarity)) if similarity else None,
            "exact_match_fraction": float(np.mean(exact)) if exact else None,
            "logprob_available_fraction": float(np.mean(logprob_available))
            if logprob_available
            else 0.0,
            "error_count": len(read_jsonl(self.error_path)),
            "warning": (
                "These runs measure prompt-surface effects and serving parity. They are not "
                "interchangeable with residual-stream interventions."
            ),
        }
        write_json(self.run_dir / "summary.json", summary)
        return summary
