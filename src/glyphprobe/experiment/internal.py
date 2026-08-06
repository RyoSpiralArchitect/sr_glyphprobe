from __future__ import annotations

import math
import os
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from glyphprobe.analysis.directions import (
    DirectionReplicate,
    build_direction_replicates,
    random_direction,
    scale_intervention,
)
from glyphprobe.analysis.factors import (
    balanced_two_factor_decomposition,
    cosine,
    representation_records,
    same_label_parallelism,
)
from glyphprobe.analysis.metrics import activation_delta_metrics, distribution_metrics
from glyphprobe.analysis.readiness import build_readiness_report
from glyphprobe.analysis.sae import SAEAnalyzer
from glyphprobe.config import ExperimentConfig, ResolvedInputs, resolve_layers
from glyphprobe.io import append_jsonl, read_jsonl, stable_hash, write_json
from glyphprobe.records import ForwardResult, Intervention
from glyphprobe.seed import seed_everything


class InternalExperiment:
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
        self.layers = resolve_layers(cfg.capture.layers, backend.num_layers)
        self.errors = 0
        self.intervention_path = run_dir / "interventions.jsonl"
        self.error_path = run_dir / "errors.jsonl"
        self.completed = {
            str(row.get("task_id"))
            for row in read_jsonl(self.intervention_path)
            if row.get("task_id")
        }
        self.sae = SAEAnalyzer(cfg.sae, model_device=getattr(backend, "device", "cpu"))

    def _guarded(self, stage: str, task_id: str, fn: Any) -> Any | None:
        try:
            return fn()
        except Exception as exc:
            self.errors += 1
            append_jsonl(
                self.error_path,
                {
                    "stage": stage,
                    "task_id": task_id,
                    "error_type": type(exc).__name__,
                    "error": repr(exc),
                    "time": time.time(),
                },
            )
            if self.cfg.run.fail_fast or self.errors >= self.cfg.run.max_errors:
                raise
            return None

    def _tokenization_records(self) -> list[dict[str, Any]]:
        path = self.run_dir / "tokenization.jsonl"
        if path.exists() and self.cfg.run.resume:
            return read_jsonl(path)
        if path.exists():
            path.unlink()
        rows: list[dict[str, Any]] = []
        for item in self.inputs.panel_items:
            raw = self.backend.tokenize(item.glyph)
            wrapper_counts: list[int] = []
            wrapper_tokenization: list[dict[str, Any]] = []
            for wrapper in self.inputs.wrappers:
                rendered = wrapper["template"].format(emoji=item.glyph)
                rendered_tokens = self.backend.tokenize(rendered)
                wrapper_counts.append(len(rendered_tokens.token_ids))
                wrapper_tokenization.append(
                    {
                        "wrapper_id": wrapper["id"],
                        "token_count": len(rendered_tokens.token_ids),
                        "token_ids": rendered_tokens.token_ids,
                        "tokens": rendered_tokens.tokens,
                    }
                )
            row = {
                "emoji_id": item.id,
                "glyph": item.glyph,
                "factors": item.factors,
                "codepoints": [f"U+{ord(char):04X}" for char in item.glyph],
                "unicode_names": [
                    unicodedata.name(char, "<unassigned>") for char in item.glyph
                ],
                "utf8_hex": item.glyph.encode("utf-8").hex(),
                "raw_token_count": len(raw.token_ids),
                "raw_token_ids": raw.token_ids,
                "raw_tokens": raw.tokens,
                "wrapper_total_token_count_min": min(wrapper_counts),
                "wrapper_total_token_count_max": max(wrapper_counts),
                "wrapper_tokenization": wrapper_tokenization,
                "tokenizer_metadata": raw.metadata,
            }
            rows.append(row)
            append_jsonl(path, row)
        neutral = self.backend.tokenize(self.cfg.panel.neutral_glyph)
        neutral_wrapper_tokenization: list[dict[str, Any]] = []
        for wrapper in self.inputs.wrappers:
            rendered = wrapper["template"].format(emoji=self.cfg.panel.neutral_glyph)
            rendered_tokens = self.backend.tokenize(rendered)
            neutral_wrapper_tokenization.append(
                {
                    "wrapper_id": wrapper["id"],
                    "token_count": len(rendered_tokens.token_ids),
                    "token_ids": rendered_tokens.token_ids,
                    "tokens": rendered_tokens.tokens,
                }
            )
        append_jsonl(
            path,
            {
                "emoji_id": "__neutral__",
                "glyph": self.cfg.panel.neutral_glyph,
                "raw_token_count": len(neutral.token_ids),
                "raw_token_ids": neutral.token_ids,
                "raw_tokens": neutral.tokens,
                "wrapper_tokenization": neutral_wrapper_tokenization,
                "tokenizer_metadata": neutral.metadata,
            },
        )
        return rows

    def _capture_sources(self) -> tuple[np.ndarray, np.ndarray]:
        path = self.run_dir / "source_activations.npz"
        if path.exists() and self.cfg.run.resume:
            payload = np.load(path, allow_pickle=False)
            return payload["emoji"], payload["neutral"]
        emoji_rows: list[np.ndarray] = []
        neutral_rows: list[np.ndarray] = []
        for emoji_index, item in enumerate(self.inputs.panel_items):
            wrapper_vectors: list[np.ndarray] = []
            for wrapper_index, wrapper in enumerate(self.inputs.wrappers):
                prompt = wrapper["template"].format(emoji=item.glyph)
                task_id = f"source:{emoji_index}:{wrapper_index}"
                result = self._guarded(
                    "source_capture",
                    task_id,
                    lambda prompt=prompt: self.backend.forward(
                        prompt,
                        capture_layers=self.layers,
                        site=self.cfg.capture.site,
                        position=self.cfg.source.anchor_position,
                        return_attentions=False,
                    ),
                )
                if result is None:
                    raise RuntimeError(f"Source capture failed for {task_id}")
                wrapper_vectors.append(np.stack([result.activations[layer] for layer in self.layers]))
            emoji_rows.append(np.stack(wrapper_vectors))
        for wrapper_index, wrapper in enumerate(self.inputs.wrappers):
            prompt = wrapper["template"].format(emoji=self.cfg.panel.neutral_glyph)
            task_id = f"source:neutral:{wrapper_index}"
            result = self._guarded(
                "source_capture",
                task_id,
                lambda prompt=prompt: self.backend.forward(
                    prompt,
                    capture_layers=self.layers,
                    site=self.cfg.capture.site,
                    position=self.cfg.source.anchor_position,
                ),
            )
            if result is None:
                raise RuntimeError(f"Neutral source capture failed for {task_id}")
            neutral_rows.append(np.stack([result.activations[layer] for layer in self.layers]))
        emoji = np.stack(emoji_rows).astype(np.float32)
        neutral = np.stack(neutral_rows).astype(np.float32)
        np.savez_compressed(
            path,
            emoji=emoji,
            neutral=neutral,
            layers=np.asarray(self.layers, dtype=np.int64),
        )
        return emoji, neutral

    def _directions(
        self, emoji: np.ndarray, neutral: np.ndarray
    ) -> list[DirectionReplicate]:
        replicates = build_direction_replicates(
            emoji,
            neutral,
            seeds=self.cfg.run.seeds,
            replicate_mode=self.cfg.run.replicate_mode,
            wrapper_subsample_fraction=self.cfg.run.wrapper_subsample_fraction,
            centroid_mode=self.cfg.panel.centroid_mode,
        )
        arrays: dict[str, Any] = {"layers": np.asarray(self.layers, dtype=np.int64)}
        metadata: list[dict[str, Any]] = []
        for replicate in replicates:
            arrays[f"directions_seed_{replicate.seed}"] = replicate.directions
            arrays[f"panel_means_seed_{replicate.seed}"] = replicate.panel_means
            arrays[f"generic_seed_{replicate.seed}"] = replicate.generic_emoji_direction
            metadata.append(
                {"seed": replicate.seed, "wrapper_indices": replicate.wrapper_indices}
            )
        np.savez_compressed(self.run_dir / "directions.npz", **arrays)
        write_json(self.run_dir / "direction_replicates.json", metadata)
        return replicates

    def _source_metrics(
        self,
        emoji: np.ndarray,
        replicates: list[DirectionReplicate],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        by_seed = {rep.seed: rep.directions for rep in replicates}
        per_item, per_layer = representation_records(
            emoji,
            by_seed,
            self.inputs.panel_items,
            self.layers,
        )
        item_path = self.run_dir / "source_item_metrics.jsonl"
        layer_path = self.run_dir / "source_layer_metrics.jsonl"
        if item_path.exists():
            item_path.unlink()
        if layer_path.exists():
            layer_path.unlink()
        for row in per_item:
            append_jsonl(item_path, row)
        for layer_pos, row in enumerate(per_layer):
            row["shape_parallelism"] = same_label_parallelism(
                replicates[0].directions[:, layer_pos, :],
                self.inputs.panel_items,
                subtract_factor="shape",
                compare_factor="color",
            )
            append_jsonl(layer_path, row)
        return per_item, per_layer

    def _target_baselines(self) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
        path = self.run_dir / "target_baselines.npz"
        metadata_path = self.run_dir / "target_baselines.jsonl"
        if path.exists() and metadata_path.exists() and self.cfg.run.resume:
            payload = np.load(path, allow_pickle=False)
            return payload["logits"], payload["activations"], read_jsonl(metadata_path)
        if metadata_path.exists():
            metadata_path.unlink()
        logits_rows: list[np.ndarray] = []
        activation_rows: list[np.ndarray] = []
        metadata: list[dict[str, Any]] = []
        for target_index, target in enumerate(self.inputs.targets):
            task_id = f"baseline:{target['id']}"
            result: ForwardResult | None = self._guarded(
                "target_baseline",
                task_id,
                lambda target=target: self.backend.forward(
                    target["prompt"],
                    capture_layers=self.layers,
                    site=self.cfg.capture.site,
                    position=self.cfg.capture.position,
                    return_attentions=self.cfg.capture.return_attentions,
                ),
            )
            if result is None:
                raise RuntimeError(f"Target baseline failed for {task_id}")
            logits_rows.append(result.logits)
            activation_rows.append(np.stack([result.activations[layer] for layer in self.layers]))
            row = {
                "target_index": target_index,
                "target_id": target["id"],
                "group": target.get("group", "unspecified"),
                "prompt_hash": stable_hash(target["prompt"]),
                "token_count": len(result.token_ids),
                "latency_ms": result.latency_ms,
                "peak_memory_bytes": result.peak_memory_bytes,
                "baseline_argmax": int(np.argmax(result.logits)),
            }
            metadata.append(row)
            append_jsonl(metadata_path, row)
        logits = np.stack(logits_rows).astype(np.float32)
        activations = np.stack(activation_rows).astype(np.float32)
        np.savez_compressed(path, logits=logits, activations=activations)
        return logits, activations, metadata

    def _condition_directions(
        self,
        replicate: DirectionReplicate,
        layer_pos: int,
    ) -> Iterable[tuple[str, str, np.ndarray]]:
        for emoji_index, item in enumerate(self.inputs.panel_items):
            yield "emoji", item.id, replicate.directions[emoji_index, layer_pos]
        if self.cfg.controls.include_neutral_direction:
            yield "generic_emoji", "__generic_emoji__", replicate.generic_emoji_direction[layer_pos]
        panel_span = replicate.directions[:, layer_pos, :]
        for index in range(self.cfg.controls.random_directions_per_layer):
            seed = replicate.seed * 1_000_003 + self.layers[layer_pos] * 101 + index
            yield (
                "random",
                f"random_{index:02d}",
                random_direction(
                    panel_span.shape[-1],
                    seed=seed,
                    remove_span=panel_span,
                ),
            )

    def _strength_signs(self, condition_type: str) -> list[tuple[float, int]]:
        values = [(strength, 1) for strength in self.cfg.intervention.strengths]
        if condition_type == "emoji" and self.cfg.controls.sign_flip:
            values.extend((strength, -1) for strength in self.cfg.controls.sign_flip_strengths)
        return values

    def _run_interventions(
        self,
        replicates: list[DirectionReplicate],
        baseline_logits: np.ndarray,
        baseline_activations: np.ndarray,
    ) -> None:
        self.sae.load(self.layers)
        for replicate in replicates:
            seed_everything(
                replicate.seed,
                deterministic_torch=self.cfg.run.deterministic_torch,
            )
            for layer_pos, layer in enumerate(self.layers):
                for condition_type, condition_id, direction in self._condition_directions(
                    replicate, layer_pos
                ):
                    for strength, sign in self._strength_signs(condition_type):
                        signed = np.asarray(direction, dtype=np.float32) * float(sign)
                        for target_index, target in enumerate(self.inputs.targets):
                            task_payload = {
                                "seed": replicate.seed,
                                "layer": layer,
                                "condition_type": condition_type,
                                "condition_id": condition_id,
                                "strength": strength,
                                "sign": sign,
                                "target_id": target["id"],
                                "calibration": "rms",
                            }
                            task_id = stable_hash(task_payload, length=24)
                            if task_id in self.completed:
                                continue
                            target_activation = baseline_activations[target_index, layer_pos]
                            perturbation, scale_meta = scale_intervention(
                                signed,
                                target_activation,
                                strength=strength,
                                normalization=self.cfg.intervention.normalization,
                                clip_mode=self.cfg.intervention.clip.mode,
                                clip_max_ratio=self.cfg.intervention.clip.max_ratio,
                                eps=self.cfg.metrics.epsilon,
                            )
                            intervention = Intervention(
                                layer=layer,
                                vector=perturbation,
                                site=self.cfg.capture.site,
                                position=self.cfg.intervention.position,
                                label=f"{condition_type}:{condition_id}",
                            )

                            def execute() -> dict[str, Any]:
                                result = self.backend.forward(
                                    target["prompt"],
                                    capture_layers=[layer],
                                    site=self.cfg.capture.site,
                                    position=self.cfg.capture.position,
                                    intervention=intervention,
                                    return_attentions=False,
                                )
                                metrics = distribution_metrics(
                                    baseline_logits[target_index],
                                    result.logits,
                                    top_k=self.cfg.metrics.top_k,
                                    rbo_p=self.cfg.metrics.rbo_p,
                                    fingerprint_dim=self.cfg.metrics.fingerprint_dim,
                                    fingerprint_seed=self.cfg.metrics.fingerprint_seed,
                                    save_top_deltas=self.cfg.metrics.save_top_logit_deltas,
                                    eps=self.cfg.metrics.epsilon,
                                )
                                act_metrics = activation_delta_metrics(
                                    target_activation,
                                    result.activations[layer],
                                    perturbation,
                                    eps=self.cfg.metrics.epsilon,
                                )
                                sae_metrics: dict[str, Any] = {"enabled": False}
                                if self.cfg.sae.enabled and condition_type == "emoji":
                                    base_sae = self.sae.analyze(layer, target_activation)
                                    changed_sae = self.sae.analyze(layer, result.activations[layer])
                                    base_ids = set(base_sae.get("top_feature_ids", []))
                                    changed_ids = set(changed_sae.get("top_feature_ids", []))
                                    sae_metrics = {
                                        "enabled": True,
                                        "baseline": base_sae,
                                        "intervened": changed_sae,
                                        "top_feature_jaccard": len(base_ids & changed_ids)
                                        / max(len(base_ids | changed_ids), 1),
                                    }
                                return {
                                    "task_id": task_id,
                                    **task_payload,
                                    "glyph": next(
                                        (
                                            item.glyph
                                            for item in self.inputs.panel_items
                                            if item.id == condition_id
                                        ),
                                        None,
                                    ),
                                    "target_index": target_index,
                                    "target_group": target.get("group", "unspecified"),
                                    "direction_wrapper_indices": replicate.wrapper_indices,
                                    "scale": scale_meta,
                                    "activation": act_metrics,
                                    "distribution": metrics,
                                    "sae": sae_metrics,
                                    "latency_ms": result.latency_ms,
                                    "peak_memory_bytes": result.peak_memory_bytes,
                                    "claim_stage": "pre-causal-screen",
                                }

                            row = self._guarded("intervention", task_id, execute)
                            if row is not None:
                                append_jsonl(self.intervention_path, row)
                                self.completed.add(task_id)

    def _run_zero_hook_controls(
        self,
        baseline_logits: np.ndarray,
        baseline_activations: np.ndarray,
    ) -> None:
        """Run an explicit zero-vector hook once per layer and target.

        This is not a statistical replicate. It detects accidental hook-side mutation,
        dtype conversion, or position mismatch that a baseline-only record cannot see.
        """
        if not self.cfg.controls.zero_direction:
            return
        seed = self.cfg.run.seeds[0]
        for layer_pos, layer in enumerate(self.layers):
            for target_index, target in enumerate(self.inputs.targets):
                payload = {
                    "seed": seed,
                    "layer": layer,
                    "condition_type": "zero",
                    "condition_id": "__zero_hook__",
                    "strength": 0.0,
                    "sign": 0,
                    "target_id": target["id"],
                    "calibration": "zero_hook",
                }
                task_id = stable_hash(payload, length=24)
                if task_id in self.completed:
                    continue
                zero = np.zeros_like(
                    baseline_activations[target_index, layer_pos],
                    dtype=np.float32,
                )

                def execute(
                    *,
                    target=target,
                    target_index=target_index,
                    layer=layer,
                    layer_pos=layer_pos,
                    payload=payload,
                    task_id=task_id,
                    zero=zero,
                ) -> dict[str, Any]:
                    result = self.backend.forward(
                        target["prompt"],
                        capture_layers=[layer],
                        site=self.cfg.capture.site,
                        position=self.cfg.capture.position,
                        intervention=Intervention(
                            layer=layer,
                            vector=zero,
                            site=self.cfg.capture.site,
                            position=self.cfg.intervention.position,
                            label="zero_hook_control",
                        ),
                    )
                    return {
                        "task_id": task_id,
                        **payload,
                        "glyph": None,
                        "target_index": target_index,
                        "target_group": target.get("group", "unspecified"),
                        "direction_wrapper_indices": [],
                        "scale": {
                            "target_activation_rms": float(
                                np.sqrt(
                                    np.mean(
                                        np.square(
                                            baseline_activations[target_index, layer_pos],
                                            dtype=np.float64,
                                        )
                                    )
                                )
                            ),
                            "direction_raw_rms": 0.0,
                            "requested_strength": 0.0,
                            "perturbation_rms": 0.0,
                            "perturbation_to_target_rms": 0.0,
                            "clip_scale": 1.0,
                            "clipped": False,
                        },
                        "activation": activation_delta_metrics(
                            baseline_activations[target_index, layer_pos],
                            result.activations[layer],
                            zero,
                            eps=self.cfg.metrics.epsilon,
                        ),
                        "distribution": distribution_metrics(
                            baseline_logits[target_index],
                            result.logits,
                            top_k=self.cfg.metrics.top_k,
                            rbo_p=self.cfg.metrics.rbo_p,
                            fingerprint_dim=self.cfg.metrics.fingerprint_dim,
                            fingerprint_seed=self.cfg.metrics.fingerprint_seed,
                            save_top_deltas=self.cfg.metrics.save_top_logit_deltas,
                            eps=self.cfg.metrics.epsilon,
                        ),
                        "sae": {"enabled": False},
                        "latency_ms": result.latency_ms,
                        "peak_memory_bytes": result.peak_memory_bytes,
                        "claim_stage": "pre-causal-zero-hook-control",
                    }

                row = self._guarded("zero_hook_control", task_id, execute)
                if row is not None:
                    append_jsonl(self.intervention_path, row)
                    self.completed.add(task_id)

    def _median_kl_for_strength(
        self,
        *,
        direction: np.ndarray,
        layer: int,
        layer_pos: int,
        strength: float,
        baseline_logits: np.ndarray,
        baseline_activations: np.ndarray,
    ) -> float:
        values: list[float] = []
        limit = min(self.cfg.targets.calibration_cases, len(self.inputs.targets))
        for target_index, target in enumerate(self.inputs.targets[:limit]):
            perturbation, _ = scale_intervention(
                direction,
                baseline_activations[target_index, layer_pos],
                strength=strength,
                normalization=self.cfg.intervention.normalization,
                clip_mode=self.cfg.intervention.clip.mode,
                clip_max_ratio=self.cfg.intervention.clip.max_ratio,
            )
            result = self.backend.forward(
                target["prompt"],
                capture_layers=[],
                site=self.cfg.capture.site,
                intervention=Intervention(
                    layer=layer,
                    vector=perturbation,
                    site=self.cfg.capture.site,
                    position=self.cfg.intervention.position,
                    label="iso_kl_calibration",
                ),
            )
            metric = distribution_metrics(
                baseline_logits[target_index],
                result.logits,
                top_k=min(10, self.cfg.metrics.top_k),
                rbo_p=self.cfg.metrics.rbo_p,
                fingerprint_dim=16,
                fingerprint_seed=self.cfg.metrics.fingerprint_seed,
                save_top_deltas=4,
            )
            values.append(float(metric["kl_base_to_intervened"]))
        return float(np.median(values))

    def _calibrate_iso_kl(
        self,
        replicates: list[DirectionReplicate],
        baseline_logits: np.ndarray,
        baseline_activations: np.ndarray,
    ) -> dict[tuple[int, int, int], float]:
        cfg = self.cfg.intervention.iso_kl
        if not cfg.enabled:
            return {}
        path = self.run_dir / "iso_kl_calibration.jsonl"
        existing = read_jsonl(path)
        lookup = {
            (int(row["seed"]), int(row["emoji_index"]), int(row["layer"])): float(
                row["selected_strength"]
            )
            for row in existing
        }
        seeds_to_calibrate = replicates if cfg.per_seed else replicates[:1]
        for replicate in seeds_to_calibrate:
            for layer_pos, layer in enumerate(self.layers):
                for emoji_index, item in enumerate(self.inputs.panel_items):
                    key = (replicate.seed, emoji_index, layer)
                    if key in lookup:
                        continue
                    low, high = cfg.min_strength, cfg.max_strength
                    trace: list[dict[str, float]] = []
                    best_strength = low
                    best_error = math.inf
                    for _ in range(cfg.bisection_steps):
                        mid = 0.5 * (low + high)
                        median_kl = self._median_kl_for_strength(
                            direction=replicate.directions[emoji_index, layer_pos],
                            layer=layer,
                            layer_pos=layer_pos,
                            strength=mid,
                            baseline_logits=baseline_logits,
                            baseline_activations=baseline_activations,
                        )
                        error = abs(median_kl - cfg.target_kl)
                        trace.append({"strength": mid, "median_kl": median_kl})
                        if error < best_error:
                            best_error = error
                            best_strength = mid
                        if median_kl < cfg.target_kl:
                            low = mid
                        else:
                            high = mid
                    row = {
                        "seed": replicate.seed,
                        "emoji_index": emoji_index,
                        "emoji_id": item.id,
                        "layer": layer,
                        "target_kl": cfg.target_kl,
                        "selected_strength": best_strength,
                        "absolute_error": best_error,
                        "within_tolerance": best_error <= cfg.tolerance,
                        "trace": trace,
                    }
                    append_jsonl(path, row)
                    lookup[key] = best_strength
        if not cfg.per_seed:
            first_seed = replicates[0].seed
            for replicate in replicates:
                for layer in self.layers:
                    for emoji_index in range(len(self.inputs.panel_items)):
                        lookup[(replicate.seed, emoji_index, layer)] = lookup[
                            (first_seed, emoji_index, layer)
                        ]
        return lookup

    def _run_iso_kl_evaluation(
        self,
        calibration: dict[tuple[int, int, int], float],
        replicates: list[DirectionReplicate],
        baseline_logits: np.ndarray,
        baseline_activations: np.ndarray,
    ) -> None:
        if not calibration:
            return
        for replicate in replicates:
            for layer_pos, layer in enumerate(self.layers):
                for emoji_index, item in enumerate(self.inputs.panel_items):
                    strength = calibration[(replicate.seed, emoji_index, layer)]
                    direction = replicate.directions[emoji_index, layer_pos]
                    for target_index, target in enumerate(self.inputs.targets):
                        payload = {
                            "seed": replicate.seed,
                            "layer": layer,
                            "condition_type": "emoji",
                            "condition_id": item.id,
                            "strength": strength,
                            "sign": 1,
                            "target_id": target["id"],
                            "calibration": "iso_kl",
                        }
                        task_id = stable_hash(payload, length=24)
                        if task_id in self.completed:
                            continue
                        perturbation, scale_meta = scale_intervention(
                            direction,
                            baseline_activations[target_index, layer_pos],
                            strength=strength,
                            normalization=self.cfg.intervention.normalization,
                            clip_mode=self.cfg.intervention.clip.mode,
                            clip_max_ratio=self.cfg.intervention.clip.max_ratio,
                        )
                        result = self.backend.forward(
                            target["prompt"],
                            capture_layers=[layer],
                            site=self.cfg.capture.site,
                            intervention=Intervention(
                                layer=layer,
                                vector=perturbation,
                                site=self.cfg.capture.site,
                                position=self.cfg.intervention.position,
                                label=f"iso_kl:{item.id}",
                            ),
                        )
                        row = {
                            "task_id": task_id,
                            **payload,
                            "glyph": item.glyph,
                            "target_index": target_index,
                            "target_group": target.get("group", "unspecified"),
                            "direction_wrapper_indices": replicate.wrapper_indices,
                            "scale": scale_meta,
                            "activation": activation_delta_metrics(
                                baseline_activations[target_index, layer_pos],
                                result.activations[layer],
                                perturbation,
                            ),
                            "distribution": distribution_metrics(
                                baseline_logits[target_index],
                                result.logits,
                                top_k=self.cfg.metrics.top_k,
                                rbo_p=self.cfg.metrics.rbo_p,
                                fingerprint_dim=self.cfg.metrics.fingerprint_dim,
                                fingerprint_seed=self.cfg.metrics.fingerprint_seed,
                                save_top_deltas=self.cfg.metrics.save_top_logit_deltas,
                            ),
                            "sae": {"enabled": False},
                            "latency_ms": result.latency_ms,
                            "peak_memory_bytes": result.peak_memory_bytes,
                            "claim_stage": "pre-causal-screen",
                        }
                        append_jsonl(self.intervention_path, row)
                        self.completed.add(task_id)

    @staticmethod
    def _mean_fingerprint(rows: list[dict[str, Any]]) -> np.ndarray:
        values = np.asarray(
            [row["distribution"]["fingerprint"] for row in rows],
            dtype=np.float64,
        )
        mean = values.mean(axis=0)
        norm = np.linalg.norm(mean)
        return mean / norm if norm > 1e-12 else mean

    @staticmethod
    def _condition_target_fingerprints(
        by_condition: dict[str, list[dict[str, Any]]],
    ) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, str]]:
        values: dict[str, dict[str, np.ndarray]] = {}
        groups: dict[str, str] = {}
        for condition_id, rows in by_condition.items():
            target_values: dict[str, np.ndarray] = {}
            for row in rows:
                target_id = str(row["target_id"])
                target_values[target_id] = np.asarray(
                    row["distribution"]["fingerprint"],
                    dtype=np.float64,
                )
                groups[target_id] = str(row.get("target_group", "unspecified"))
            values[condition_id] = target_values
        return values, groups

    @staticmethod
    def _common_targets(values: dict[str, dict[str, np.ndarray]]) -> list[str]:
        if not values:
            return []
        target_sets = [set(target_map) for target_map in values.values()]
        return sorted(set.intersection(*target_sets)) if target_sets else []

    @staticmethod
    def _stratified_half_split(
        target_ids: list[str],
        groups: dict[str, str],
        *,
        seed: int,
    ) -> tuple[list[str], list[str]]:
        """Create deterministic, approximately balanced target halves by group."""
        by_group: dict[str, list[str]] = defaultdict(list)
        for target_id in target_ids:
            by_group[groups.get(target_id, "unspecified")].append(target_id)
        first: list[str] = []
        second: list[str] = []
        for group, group_targets in sorted(by_group.items()):
            ordered = sorted(
                group_targets,
                key=lambda target_id: stable_hash(
                    {"seed": seed, "group": group, "target_id": target_id},
                    length=24,
                ),
            )
            first.extend(ordered[::2])
            second.extend(ordered[1::2])
        # Tiny or singleton groups can leave one side empty. Fall back to a global
        # sealed split rather than manufacturing duplicate observations.
        if not first or not second:
            ordered = sorted(
                target_ids,
                key=lambda target_id: stable_hash(
                    {"seed": seed, "target_id": target_id},
                    length=24,
                ),
            )
            midpoint = max(1, len(ordered) // 2)
            first, second = ordered[:midpoint], ordered[midpoint:]
        return first, second

    @classmethod
    def _fingerprint_separation(
        cls,
        values: dict[str, dict[str, np.ndarray]],
        first_targets: list[str],
        second_targets: list[str],
    ) -> dict[str, Any]:
        condition_ids = sorted(values)
        if len(condition_ids) < 2 or not first_targets or not second_targets:
            return {
                "available": False,
                "same": None,
                "cross": None,
                "separation": None,
                "condition_count": len(condition_ids),
            }
        first_vectors: dict[str, np.ndarray] = {}
        second_vectors: dict[str, np.ndarray] = {}
        for condition_id in condition_ids:
            first_rows = [
                {
                    "distribution": {
                        "fingerprint": values[condition_id][target_id].tolist()
                    }
                }
                for target_id in first_targets
                if target_id in values[condition_id]
            ]
            second_rows = [
                {
                    "distribution": {
                        "fingerprint": values[condition_id][target_id].tolist()
                    }
                }
                for target_id in second_targets
                if target_id in values[condition_id]
            ]
            if not first_rows or not second_rows:
                continue
            first_vectors[condition_id] = cls._mean_fingerprint(first_rows)
            second_vectors[condition_id] = cls._mean_fingerprint(second_rows)
        common = sorted(set(first_vectors) & set(second_vectors))
        if len(common) < 2:
            return {
                "available": False,
                "same": None,
                "cross": None,
                "separation": None,
                "condition_count": len(common),
            }
        same = [cosine(first_vectors[key], second_vectors[key]) for key in common]
        cross = [
            cosine(first_vectors[first], second_vectors[second])
            for first in common
            for second in common
            if first != second
        ]
        same_mean = float(np.mean(same))
        cross_mean = float(np.mean(cross))
        return {
            "available": True,
            "same": same_mean,
            "cross": cross_mean,
            "separation": same_mean - cross_mean,
            "condition_count": len(common),
        }

    @staticmethod
    def _permute_condition_labels_within_target(
        values: dict[str, dict[str, np.ndarray]],
        target_ids: list[str],
        *,
        rng: np.random.Generator,
    ) -> dict[str, dict[str, np.ndarray]]:
        condition_ids = sorted(values)
        permuted = {condition_id: {} for condition_id in condition_ids}
        for target_id in target_ids:
            source_ids = [
                condition_id
                for condition_id in condition_ids
                if target_id in values[condition_id]
            ]
            shuffled_ids = list(rng.permutation(source_ids))
            for destination, source in zip(source_ids, shuffled_ids):
                permuted[destination][target_id] = values[source][target_id]
        return permuted

    def _condition_fingerprint_statistics(
        self,
        by_condition: dict[str, list[dict[str, Any]]],
        *,
        split_seed: int,
        permutation_count: int,
    ) -> dict[str, Any]:
        values, groups = self._condition_target_fingerprints(by_condition)
        target_ids = self._common_targets(values)
        first, second = self._stratified_half_split(
            target_ids,
            groups,
            seed=split_seed,
        )
        point = self._fingerprint_separation(values, first, second)
        if not point["available"]:
            return {
                **point,
                "target_count": len(target_ids),
                "split_first_count": len(first),
                "split_second_count": len(second),
                "repeat_mean": None,
                "repeat_median": None,
                "repeat_ci_low": None,
                "repeat_ci_high": None,
                "permutation_p_greater_equal": None,
                "permutation_null_mean": None,
                "permutation_count": 0,
            }

        repeat_values: list[float] = []
        repeat_count = max(int(self.cfg.metrics.split_half_repeats), 1)
        for index in range(repeat_count):
            repeat_first, repeat_second = self._stratified_half_split(
                target_ids,
                groups,
                seed=split_seed + 104_729 * (index + 1),
            )
            score = self._fingerprint_separation(values, repeat_first, repeat_second)
            if score["available"]:
                repeat_values.append(float(score["separation"]))

        rng = np.random.default_rng(split_seed + 2_147_483_647)
        null_values: list[float] = []
        for _ in range(max(int(permutation_count), 0)):
            permuted = self._permute_condition_labels_within_target(
                values,
                target_ids,
                rng=rng,
            )
            score = self._fingerprint_separation(permuted, first, second)
            if score["available"]:
                null_values.append(float(score["separation"]))

        repeats = np.asarray(repeat_values, dtype=np.float64)
        nulls = np.asarray(null_values, dtype=np.float64)
        observed = float(point["separation"])
        p_value = (
            float((1 + np.sum(nulls >= observed)) / (1 + nulls.size))
            if nulls.size
            else None
        )
        return {
            **point,
            "target_count": len(target_ids),
            "split_first_count": len(first),
            "split_second_count": len(second),
            "repeat_mean": float(np.mean(repeats)) if repeats.size else None,
            "repeat_median": float(np.median(repeats)) if repeats.size else None,
            "repeat_ci_low": float(np.quantile(repeats, 0.025)) if repeats.size else None,
            "repeat_ci_high": float(np.quantile(repeats, 0.975)) if repeats.size else None,
            "repeat_count": int(repeats.size),
            "permutation_p_greater_equal": p_value,
            "permutation_null_mean": float(np.mean(nulls)) if nulls.size else None,
            "permutation_null_std": float(np.std(nulls)) if nulls.size else None,
            "permutation_count": int(nulls.size),
        }

    def _fingerprint_summary(self) -> list[dict[str, Any]]:
        rows = [
            row
            for row in read_jsonl(self.intervention_path)
            if row.get("sign") == 1
            and row.get("calibration") == "rms"
            and row.get("distribution", {}).get("fingerprint")
        ]
        path = self.run_dir / "fingerprint_summary.jsonl"
        if path.exists():
            path.unlink()
        summaries: list[dict[str, Any]] = []
        keys = sorted(
            {
                (int(row["layer"]), float(row["strength"]), int(row["seed"]))
                for row in rows
            }
        )
        for layer, strength, seed in keys:
            subset = [
                row
                for row in rows
                if int(row["layer"]) == layer
                and float(row["strength"]) == strength
                and int(row["seed"]) == seed
            ]
            by_type: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
                lambda: defaultdict(list)
            )
            for row in subset:
                by_type[row["condition_type"]][row["condition_id"]].append(row)

            split_seed = int(
                stable_hash(
                    {
                        "fingerprint_seed": self.cfg.metrics.fingerprint_seed,
                        "layer": layer,
                        "strength": strength,
                        "direction_seed": seed,
                    },
                    length=15,
                ),
                16,
            ) % (2**32 - 1)
            emoji = self._condition_fingerprint_statistics(
                by_type.get("emoji", {}),
                split_seed=split_seed,
                permutation_count=self.cfg.controls.label_shuffle_permutations,
            )
            random = self._condition_fingerprint_statistics(
                by_type.get("random", {}),
                split_seed=split_seed,
                permutation_count=0,
            )
            emoji_sep = emoji.get("separation")
            random_sep = random.get("separation")

            output_factor_decomposition: dict[str, Any] = {
                "available": False,
                "reason": "missing emoji conditions",
            }
            output_shape_parallelism: dict[str, Any] = {
                "available": False,
                "reason": "missing emoji conditions",
            }
            emoji_values, _ = self._condition_target_fingerprints(
                by_type.get("emoji", {})
            )
            if all(item.id in emoji_values for item in self.inputs.panel_items):
                output_vectors: list[np.ndarray] = []
                for item in self.inputs.panel_items:
                    condition_vectors = np.stack(
                        list(emoji_values[item.id].values()),
                        axis=0,
                    )
                    mean_vector = condition_vectors.mean(axis=0)
                    norm = np.linalg.norm(mean_vector)
                    output_vectors.append(
                        mean_vector / norm if norm > self.cfg.metrics.epsilon else mean_vector
                    )
                output_matrix = np.stack(output_vectors)
                output_factor_decomposition = balanced_two_factor_decomposition(
                    output_matrix,
                    self.inputs.panel_items,
                )
                output_shape_parallelism = same_label_parallelism(
                    output_matrix,
                    self.inputs.panel_items,
                    subtract_factor="shape",
                    compare_factor="color",
                )

            advantage = (
                float(emoji_sep) - float(random_sep)
                if emoji_sep is not None and random_sep is not None
                else None
            )
            row = {
                "layer": layer,
                "strength": strength,
                "seed": seed,
                "split_seed": split_seed,
                "emoji_same_split_cosine": emoji.get("same"),
                "emoji_cross_cosine": emoji.get("cross"),
                "emoji_separation": emoji_sep,
                "emoji_condition_count": emoji.get("condition_count", 0),
                "emoji_target_count": emoji.get("target_count", 0),
                "emoji_split_repeat_mean": emoji.get("repeat_mean"),
                "emoji_split_repeat_median": emoji.get("repeat_median"),
                "emoji_split_repeat_ci_low": emoji.get("repeat_ci_low"),
                "emoji_split_repeat_ci_high": emoji.get("repeat_ci_high"),
                "emoji_split_repeat_count": emoji.get("repeat_count", 0),
                "emoji_label_permutation_p": emoji.get(
                    "permutation_p_greater_equal"
                ),
                "emoji_label_permutation_null_mean": emoji.get(
                    "permutation_null_mean"
                ),
                "emoji_label_permutation_null_std": emoji.get(
                    "permutation_null_std"
                ),
                "emoji_label_permutation_count": emoji.get("permutation_count", 0),
                "random_same_split_cosine": random.get("same"),
                "random_cross_cosine": random.get("cross"),
                "random_separation": random_sep,
                "random_condition_count": random.get("condition_count", 0),
                "random_target_count": random.get("target_count", 0),
                "random_split_repeat_mean": random.get("repeat_mean"),
                "random_split_repeat_ci_low": random.get("repeat_ci_low"),
                "random_split_repeat_ci_high": random.get("repeat_ci_high"),
                "emoji_advantage_over_random": advantage,
                "output_factor_decomposition": output_factor_decomposition,
                "output_shape_parallelism": output_shape_parallelism,
            }
            summaries.append(row)
            append_jsonl(path, row)
        return summaries

    @staticmethod
    def _coefficient_of_variation(values: list[float], eps: float = 1e-12) -> float | None:
        array = np.asarray(values, dtype=np.float64)
        if array.size == 0:
            return None
        mean = float(np.mean(array))
        return float(np.std(array) / max(abs(mean), eps))

    def _scalar_balance_summary(self) -> list[dict[str, Any]]:
        rows = [
            row
            for row in read_jsonl(self.intervention_path)
            if row.get("sign") == 1 and row.get("calibration") == "rms"
        ]
        path = self.run_dir / "scalar_balance_summary.jsonl"
        if path.exists():
            path.unlink()
        grouped: dict[tuple[int, float, int, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[
                (
                    int(row["layer"]),
                    float(row["strength"]),
                    int(row["seed"]),
                    str(row["condition_type"]),
                )
            ].append(row)
        output: list[dict[str, Any]] = []
        for (layer, strength, seed, condition_type), group_rows in sorted(grouped.items()):
            ratios = [
                float(row["scale"]["perturbation_to_target_rms"])
                for row in group_rows
            ]
            kls = [
                float(row["distribution"]["kl_base_to_intervened"])
                for row in group_rows
            ]
            logit_rms = [
                float(row["distribution"]["logit_delta_rms"])
                for row in group_rows
            ]
            tvs = [
                float(row["distribution"]["total_variation"])
                for row in group_rows
            ]
            row = {
                "layer": layer,
                "strength": strength,
                "seed": seed,
                "condition_type": condition_type,
                "record_count": len(group_rows),
                "perturbation_ratio_mean": float(np.mean(ratios)),
                "perturbation_ratio_std": float(np.std(ratios)),
                "perturbation_ratio_cv": self._coefficient_of_variation(ratios),
                "perturbation_ratio_max_abs_error": float(
                    np.max(np.abs(np.asarray(ratios) - strength))
                ),
                "clip_fraction": float(
                    np.mean([bool(row["scale"].get("clipped")) for row in group_rows])
                ),
                "kl_median": float(np.median(kls)),
                "kl_iqr": float(np.quantile(kls, 0.75) - np.quantile(kls, 0.25)),
                "kl_cv": self._coefficient_of_variation(kls),
                "logit_delta_rms_median": float(np.median(logit_rms)),
                "logit_delta_rms_cv": self._coefficient_of_variation(logit_rms),
                "total_variation_median": float(np.median(tvs)),
                "claim_stage": "pre-causal-scalar-balance",
            }
            output.append(row)
            append_jsonl(path, row)
        return output

    @staticmethod
    def _adjacent_nondecreasing(values: list[float], tolerance: float = 1e-12) -> float:
        if len(values) < 2:
            return 0.0
        return float(
            np.mean(
                [
                    later + tolerance >= earlier
                    for earlier, later in zip(values[:-1], values[1:])
                ]
            )
        )

    def _dose_response_summary(self) -> list[dict[str, Any]]:
        rows = [
            row
            for row in read_jsonl(self.intervention_path)
            if row.get("sign") == 1
            and row.get("calibration") == "rms"
            and row.get("condition_type") in {"emoji", "random", "generic_emoji"}
        ]
        path = self.run_dir / "dose_response_summary.jsonl"
        if path.exists():
            path.unlink()
        series: dict[
            tuple[int, int, str, str, str],
            list[dict[str, Any]],
        ] = defaultdict(list)
        for row in rows:
            series[
                (
                    int(row["layer"]),
                    int(row["seed"]),
                    str(row["condition_type"]),
                    str(row["condition_id"]),
                    str(row["target_id"]),
                )
            ].append(row)

        aggregate: dict[tuple[int, int, str], list[dict[str, float]]] = defaultdict(list)
        for (layer, seed, condition_type, _condition_id, _target_id), series_rows in series.items():
            ordered = sorted(series_rows, key=lambda row: float(row["strength"]))
            strengths = [float(row["strength"]) for row in ordered]
            if len(set(strengths)) < 2:
                continue
            kl = [float(row["distribution"]["kl_base_to_intervened"]) for row in ordered]
            logit_rms = [float(row["distribution"]["logit_delta_rms"]) for row in ordered]
            tv = [float(row["distribution"]["total_variation"]) for row in ordered]
            aggregate[(layer, seed, condition_type)].append(
                {
                    "kl_adjacent_nondecreasing": self._adjacent_nondecreasing(kl),
                    "logit_rms_adjacent_nondecreasing": self._adjacent_nondecreasing(logit_rms),
                    "tv_adjacent_nondecreasing": self._adjacent_nondecreasing(tv),
                    "kl_last_minus_first": kl[-1] - kl[0],
                    "logit_rms_last_minus_first": logit_rms[-1] - logit_rms[0],
                    "tv_last_minus_first": tv[-1] - tv[0],
                }
            )

        output: list[dict[str, Any]] = []
        for (layer, seed, condition_type), values in sorted(aggregate.items()):
            row = {
                "layer": layer,
                "seed": seed,
                "condition_type": condition_type,
                "series_count": len(values),
                "strength_count": len(self.cfg.intervention.strengths),
                "kl_adjacent_nondecreasing_mean": float(
                    np.mean([value["kl_adjacent_nondecreasing"] for value in values])
                ),
                "logit_rms_adjacent_nondecreasing_mean": float(
                    np.mean(
                        [value["logit_rms_adjacent_nondecreasing"] for value in values]
                    )
                ),
                "tv_adjacent_nondecreasing_mean": float(
                    np.mean([value["tv_adjacent_nondecreasing"] for value in values])
                ),
                "kl_last_minus_first_median": float(
                    np.median([value["kl_last_minus_first"] for value in values])
                ),
                "logit_rms_last_minus_first_median": float(
                    np.median(
                        [value["logit_rms_last_minus_first"] for value in values]
                    )
                ),
                "tv_last_minus_first_median": float(
                    np.median([value["tv_last_minus_first"] for value in values])
                ),
                "claim_stage": "pre-causal-dose-response",
            }
            output.append(row)
            append_jsonl(path, row)
        return output

    def _sign_flip_summary(self) -> list[dict[str, Any]]:
        rows = [
            row
            for row in read_jsonl(self.intervention_path)
            if row.get("condition_type") == "emoji"
            and row.get("calibration") == "rms"
        ]
        path = self.run_dir / "sign_flip_summary.jsonl"
        if path.exists():
            path.unlink()
        indexed: dict[
            tuple[int, int, float, str, str],
            dict[int, dict[str, Any]],
        ] = defaultdict(dict)
        for row in rows:
            indexed[
                (
                    int(row["layer"]),
                    int(row["seed"]),
                    float(row["strength"]),
                    str(row["condition_id"]),
                    str(row["target_id"]),
                )
            ][int(row["sign"])] = row
        grouped: dict[tuple[int, int, float], list[dict[str, float]]] = defaultdict(list)
        for (layer, seed, strength, _condition_id, _target_id), pair in indexed.items():
            if 1 not in pair or -1 not in pair:
                continue
            positive = pair[1]
            negative = pair[-1]
            positive_fp = np.asarray(
                positive["distribution"]["fingerprint"], dtype=np.float64
            )
            negative_fp = np.asarray(
                negative["distribution"]["fingerprint"], dtype=np.float64
            )
            positive_l2 = float(positive["distribution"]["logit_delta_l2"])
            negative_l2 = float(negative["distribution"]["logit_delta_l2"])
            positive_kl = float(positive["distribution"]["kl_base_to_intervened"])
            negative_kl = float(negative["distribution"]["kl_base_to_intervened"])
            grouped[(layer, seed, strength)].append(
                {
                    "fingerprint_cosine": cosine(positive_fp, negative_fp),
                    "antisymmetry_score": -cosine(positive_fp, negative_fp),
                    "logit_l2_ratio_negative_to_positive": negative_l2
                    / max(positive_l2, self.cfg.metrics.epsilon),
                    "kl_ratio_negative_to_positive": negative_kl
                    / max(positive_kl, self.cfg.metrics.epsilon),
                }
            )
        output: list[dict[str, Any]] = []
        for (layer, seed, strength), values in sorted(grouped.items()):
            row = {
                "layer": layer,
                "seed": seed,
                "strength": strength,
                "pair_count": len(values),
                "fingerprint_cosine_median": float(
                    np.median([value["fingerprint_cosine"] for value in values])
                ),
                "antisymmetry_score_median": float(
                    np.median([value["antisymmetry_score"] for value in values])
                ),
                "logit_l2_ratio_negative_to_positive_median": float(
                    np.median(
                        [
                            value["logit_l2_ratio_negative_to_positive"]
                            for value in values
                        ]
                    )
                ),
                "kl_ratio_negative_to_positive_median": float(
                    np.median(
                        [value["kl_ratio_negative_to_positive"] for value in values]
                    )
                ),
                "claim_stage": "pre-causal-sign-symmetry",
            }
            output.append(row)
            append_jsonl(path, row)
        return output

    def _cross_seed_fingerprint_summary(self) -> list[dict[str, Any]]:
        rows = [
            row
            for row in read_jsonl(self.intervention_path)
            if row.get("sign") == 1
            and row.get("calibration") == "rms"
            and row.get("condition_type") in {"emoji", "random"}
        ]
        path = self.run_dir / "cross_seed_fingerprint_summary.jsonl"
        if path.exists():
            path.unlink()
        grouped: dict[
            tuple[int, float, str, str, int],
            list[dict[str, Any]],
        ] = defaultdict(list)
        for row in rows:
            grouped[
                (
                    int(row["layer"]),
                    float(row["strength"]),
                    str(row["condition_type"]),
                    str(row["condition_id"]),
                    int(row["seed"]),
                )
            ].append(row)
        means = {
            key: self._mean_fingerprint(value)
            for key, value in grouped.items()
        }
        layer_strengths = sorted({(key[0], key[1]) for key in means})
        output: list[dict[str, Any]] = []
        for layer, strength in layer_strengths:
            type_stats: dict[str, dict[str, Any]] = {}
            for condition_type in ("emoji", "random"):
                condition_ids = sorted(
                    {
                        key[3]
                        for key in means
                        if key[0] == layer
                        and key[1] == strength
                        and key[2] == condition_type
                    }
                )
                seeds = sorted(
                    {
                        key[4]
                        for key in means
                        if key[0] == layer
                        and key[1] == strength
                        and key[2] == condition_type
                    }
                )
                same: list[float] = []
                cross: list[float] = []
                seed_pairs = 0
                for first_index, first_seed in enumerate(seeds):
                    for second_seed in seeds[first_index + 1 :]:
                        seed_pairs += 1
                        available = [
                            condition_id
                            for condition_id in condition_ids
                            if (layer, strength, condition_type, condition_id, first_seed)
                            in means
                            and (
                                layer,
                                strength,
                                condition_type,
                                condition_id,
                                second_seed,
                            )
                            in means
                        ]
                        for condition_id in available:
                            same.append(
                                cosine(
                                    means[
                                        (
                                            layer,
                                            strength,
                                            condition_type,
                                            condition_id,
                                            first_seed,
                                        )
                                    ],
                                    means[
                                        (
                                            layer,
                                            strength,
                                            condition_type,
                                            condition_id,
                                            second_seed,
                                        )
                                    ],
                                )
                            )
                        for first_condition in available:
                            for second_condition in available:
                                if first_condition == second_condition:
                                    continue
                                cross.append(
                                    cosine(
                                        means[
                                            (
                                                layer,
                                                strength,
                                                condition_type,
                                                first_condition,
                                                first_seed,
                                            )
                                        ],
                                        means[
                                            (
                                                layer,
                                                strength,
                                                condition_type,
                                                second_condition,
                                                second_seed,
                                            )
                                        ],
                                    )
                                )
                same_mean = float(np.mean(same)) if same else None
                cross_mean = float(np.mean(cross)) if cross else None
                type_stats[condition_type] = {
                    "same": same_mean,
                    "cross": cross_mean,
                    "separation": (
                        same_mean - cross_mean
                        if same_mean is not None and cross_mean is not None
                        else None
                    ),
                    "condition_count": len(condition_ids),
                    "seed_count": len(seeds),
                    "seed_pair_count": seed_pairs,
                }
            emoji_sep = type_stats["emoji"]["separation"]
            random_sep = type_stats["random"]["separation"]
            row = {
                "layer": layer,
                "strength": strength,
                "emoji_same_cross_seed_cosine": type_stats["emoji"]["same"],
                "emoji_cross_cross_seed_cosine": type_stats["emoji"]["cross"],
                "emoji_cross_seed_separation": emoji_sep,
                "emoji_condition_count": type_stats["emoji"]["condition_count"],
                "seed_count": type_stats["emoji"]["seed_count"],
                "seed_pair_count": type_stats["emoji"]["seed_pair_count"],
                "random_same_cross_seed_cosine": type_stats["random"]["same"],
                "random_cross_cross_seed_cosine": type_stats["random"]["cross"],
                "random_cross_seed_separation": random_sep,
                "cross_seed_advantage_over_random": (
                    float(emoji_sep) - float(random_sep)
                    if emoji_sep is not None and random_sep is not None
                    else None
                ),
                "claim_stage": "pre-causal-cross-seed-reproducibility",
            }
            output.append(row)
            append_jsonl(path, row)
        return output

    def run(self) -> dict[str, Any]:
        tokenization = self._tokenization_records()
        emoji, neutral = self._capture_sources()
        replicates = self._directions(emoji, neutral)
        source_item_metrics, _ = self._source_metrics(emoji, replicates)
        baseline_logits, baseline_activations, _ = self._target_baselines()
        calibration = self._calibrate_iso_kl(
            replicates,
            baseline_logits,
            baseline_activations,
        )
        self._run_interventions(replicates, baseline_logits, baseline_activations)
        self._run_zero_hook_controls(baseline_logits, baseline_activations)
        self._run_iso_kl_evaluation(
            calibration,
            replicates,
            baseline_logits,
            baseline_activations,
        )
        fingerprint = self._fingerprint_summary()
        scalar_balance = self._scalar_balance_summary()
        dose_response = self._dose_response_summary()
        sign_flip = self._sign_flip_summary()
        cross_seed = self._cross_seed_fingerprint_summary()
        intervention_rows = read_jsonl(self.intervention_path)
        zero_rows = [
            row for row in intervention_rows if row.get("condition_type") == "zero"
        ]
        alignments = [
            float(row["direction_replicate_alignment_mean"])
            for row in source_item_metrics
        ]
        advantages = [
            float(row["emoji_advantage_over_random"])
            for row in fingerprint
            if row.get("emoji_advantage_over_random") is not None
        ]
        permutation_p_values = [
            float(row["emoji_label_permutation_p"])
            for row in fingerprint
            if row.get("emoji_label_permutation_p") is not None
        ]
        cross_seed_advantages = [
            float(row["cross_seed_advantage_over_random"])
            for row in cross_seed
            if row.get("cross_seed_advantage_over_random") is not None
        ]
        emoji_scalar_rows = [
            row for row in scalar_balance if row.get("condition_type") == "emoji"
        ]
        emoji_dose_rows = [
            row for row in dose_response if row.get("condition_type") == "emoji"
        ]
        wrapper_token_counts: dict[str, set[int]] = defaultdict(set)
        for row in tokenization:
            if row.get("emoji_id") == "__neutral__":
                continue
            for wrapper_record in row.get("wrapper_tokenization", []):
                wrapper_token_counts[str(wrapper_record["wrapper_id"])].add(
                    int(wrapper_record["token_count"])
                )
        wrapper_token_count_mismatches = sorted(
            wrapper_id
            for wrapper_id, counts in wrapper_token_counts.items()
            if len(counts) > 1
        )
        summary = {
            "stage": "pre-causal-activation-screen",
            "causal_claim_authorized": False,
            "resolved_layers": self.layers,
            "emoji_count": len(self.inputs.panel_items),
            "wrapper_count": len(self.inputs.wrappers),
            "target_case_count": len(self.inputs.targets),
            "seed_count": len(self.cfg.run.seeds),
            "strength_count": len(self.cfg.intervention.strengths),
            "intervention_record_count": len(intervention_rows),
            "random_control_count": sum(
                row.get("condition_type") == "random" for row in intervention_rows
            ),
            "zero_hook_control_count": len(zero_rows),
            "zero_hook_max_logit_delta_rms": max(
                (
                    float(row["distribution"]["logit_delta_rms"])
                    for row in zero_rows
                ),
                default=None,
            ),
            "zero_hook_max_activation_delta_rms": max(
                (
                    float(row["activation"]["actual_activation_delta_rms"])
                    for row in zero_rows
                ),
                default=None,
            ),
            "glyph_token_counts": [
                int(row["raw_token_count"])
                for row in tokenization
                if row.get("emoji_id") != "__neutral__"
            ],
            "wrapper_token_count_mismatch_ids": wrapper_token_count_mismatches,
            "wrapper_token_count_mismatch_count": len(
                wrapper_token_count_mismatches
            ),
            "median_direction_replicate_alignment": float(np.median(alignments))
            if alignments
            else 0.0,
            "emoji_fingerprint_advantage": float(np.median(advantages))
            if advantages
            else None,
            "median_emoji_label_permutation_p": float(np.median(permutation_p_values))
            if permutation_p_values
            else None,
            "cross_seed_fingerprint_advantage": float(
                np.median(cross_seed_advantages)
            )
            if cross_seed_advantages
            else None,
            "median_emoji_perturbation_ratio_max_abs_error": float(
                np.median(
                    [
                        row["perturbation_ratio_max_abs_error"]
                        for row in emoji_scalar_rows
                    ]
                )
            )
            if emoji_scalar_rows
            else None,
            "median_emoji_kl_dose_monotonicity": float(
                np.median(
                    [
                        row["kl_adjacent_nondecreasing_mean"]
                        for row in emoji_dose_rows
                    ]
                )
            )
            if emoji_dose_rows
            else None,
            "median_sign_antisymmetry": float(
                np.median(
                    [row["antisymmetry_score_median"] for row in sign_flip]
                )
            )
            if sign_flip
            else None,
            "error_count": len(read_jsonl(self.error_path)),
            "iso_kl_enabled": self.cfg.intervention.iso_kl.enabled,
            "sae_enabled": self.cfg.sae.enabled,
        }
        summary["readiness"] = build_readiness_report(summary)
        write_json(self.run_dir / "summary.json", summary)
        return summary
