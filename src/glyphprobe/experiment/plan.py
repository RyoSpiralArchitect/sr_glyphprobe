from __future__ import annotations

from typing import Any

from glyphprobe.capabilities import CapabilityReport, Capability
from glyphprobe.config import ExperimentConfig, ResolvedInputs, resolve_layers


def choose_mode(cfg: ExperimentConfig, capabilities: CapabilityReport) -> str:
    internal = capabilities.supports(Capability.FORWARD_LOGITS, Capability.ACTIVATION_PATCH)
    if cfg.mode == "internal":
        return "internal"
    if cfg.mode == "surface":
        return "surface"
    return "internal" if internal else "surface"


def build_plan(
    cfg: ExperimentConfig,
    inputs: ResolvedInputs,
    capabilities: CapabilityReport,
    *,
    num_layers: int | None,
) -> dict[str, Any]:
    mode = choose_mode(cfg, capabilities)
    emoji_count = len(inputs.panel_items)
    wrapper_count = len(inputs.wrappers)
    target_count = len(inputs.targets)
    surface_target_count = min(target_count, cfg.targets.generation_cases)
    seed_count = len(cfg.run.seeds)
    plan: dict[str, Any] = {
        "mode": mode,
        "backend": cfg.backend.kind,
        "model": cfg.backend.model,
        "emoji_count": emoji_count,
        "wrapper_count": wrapper_count,
        "target_count": target_count,
        "seed_count": seed_count,
    }
    if mode == "surface":
        plan["target_count"] = surface_target_count
        baseline = surface_target_count * seed_count
        emoji = emoji_count * surface_target_count * seed_count
        plan.update(
            {
                "baseline_generations": baseline,
                "emoji_generations": emoji,
                "estimated_generation_calls": baseline + emoji,
                "claim_boundary": "surface-observational-only",
            }
        )
        return plan

    if num_layers is None:
        raise ValueError("Internal plan requires a layer count")
    layers = resolve_layers(cfg.capture.layers, num_layers)
    positive = len(cfg.intervention.strengths)
    negative = len(cfg.controls.sign_flip_strengths) if cfg.controls.sign_flip else 0
    source = (emoji_count + 1) * wrapper_count
    baseline = target_count
    emoji_interventions = emoji_count * len(layers) * target_count * seed_count * (
        positive + negative
    )
    random_interventions = (
        cfg.controls.random_directions_per_layer
        * len(layers)
        * target_count
        * seed_count
        * positive
    )
    generic_interventions = (
        len(layers) * target_count * seed_count * positive
        if cfg.controls.include_neutral_direction
        else 0
    )
    zero_hook_controls = len(layers) * target_count if cfg.controls.zero_direction else 0
    calibration = 0
    iso_eval = 0
    if cfg.intervention.iso_kl.enabled:
        calibration_seeds = seed_count if cfg.intervention.iso_kl.per_seed else 1
        calibration = (
            emoji_count
            * len(layers)
            * calibration_seeds
            * min(cfg.targets.calibration_cases, target_count)
            * cfg.intervention.iso_kl.bisection_steps
        )
        iso_eval = emoji_count * len(layers) * seed_count * target_count
    total = (
        source
        + baseline
        + emoji_interventions
        + random_interventions
        + generic_interventions
        + zero_hook_controls
        + calibration
        + iso_eval
    )
    plan.update(
        {
            "resolved_layers": layers,
            "source_forward_calls": source,
            "target_baseline_calls": baseline,
            "emoji_intervention_calls": emoji_interventions,
            "random_control_calls": random_interventions,
            "generic_emoji_control_calls": generic_interventions,
            "zero_hook_control_calls": zero_hook_controls,
            "iso_kl_calibration_calls_upper_bound": calibration,
            "iso_kl_evaluation_calls": iso_eval,
            "estimated_forward_calls": total,
            "claim_boundary": "pre-causal-activation-screen",
        }
    )
    return plan
