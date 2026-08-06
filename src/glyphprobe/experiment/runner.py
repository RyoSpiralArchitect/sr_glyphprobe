from __future__ import annotations

import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from glyphprobe.backends.registry import create_backend
from glyphprobe.capabilities import Capability
from glyphprobe.config import ExperimentConfig, ResolvedInputs
from glyphprobe.errors import CapabilityError
from glyphprobe.io import stable_hash, write_json, write_yaml
from glyphprobe.provenance import (
    implementation_receipt,
    input_hash_receipt,
    package_version,
    stable_model_identity,
)
from glyphprobe.reporting import render_markdown_report

from .internal import InternalExperiment
from .plan import build_plan, choose_mode
from .surface import SurfaceExperiment


def _slug(text: str, limit: int = 56) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")
    return value[:limit] or "unnamed"

def _environment_receipt() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": {
            name: package_version(name)
            for name in (
                "glyphprobe",
                "numpy",
                "scipy",
                "torch",
                "mlx",
                "mlx-lm",
                "transformers",
                "transformer-lens",
                "sae-lens",
                "openai",
                "pydantic",
            )
        },
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }


def prepare_run_dir(
    cfg: ExperimentConfig,
    inputs: ResolvedInputs,
    *,
    environment: dict[str, Any],
    model_receipt: dict[str, Any],
) -> tuple[Path, str, dict[str, str], dict[str, Any], dict[str, Any], str]:
    input_hashes = input_hash_receipt(inputs.input_paths)
    implementation = implementation_receipt()
    model_identity = stable_model_identity(model_receipt)
    runtime_identity = {
        "environment": environment,
        "model": model_identity,
    }
    seal_payload = {
        "config": cfg.model_dump(mode="json"),
        "panel": [item.model_dump(mode="json") for item in inputs.panel_items],
        "wrappers": inputs.wrappers,
        "targets": inputs.targets,
        "input_hashes": input_hashes,
        "implementation": implementation,
        "runtime_identity": runtime_identity,
    }
    seal = stable_hash(seal_payload, length=16)
    model_slug = _slug(cfg.backend.model.replace("/", "-"), limit=40)
    run_id = f"{_slug(cfg.run.name)}--{cfg.backend.kind}--{model_slug}--{seal}"
    output_root = cfg.run.output_root
    if not output_root.is_absolute():
        output_root = (inputs.base_dir / output_root).resolve()
    run_dir = output_root / run_id
    if run_dir.exists() and not cfg.run.resume:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = output_root / f"{run_id}--{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    if cfg.run.resume and (run_dir / "receipt.json").exists():
        existing = json.loads((run_dir / "receipt.json").read_text(encoding="utf-8"))
        if existing.get("run_seal") != seal:
            raise RuntimeError(
                "Refusing resume: the existing receipt does not match the current run seal"
            )
    return run_dir, run_id, input_hashes, implementation, model_identity, seal


def run_experiment(
    cfg: ExperimentConfig,
    inputs: ResolvedInputs,
) -> tuple[Path, dict[str, Any]]:
    started = datetime.now(timezone.utc).isoformat()
    environment = _environment_receipt()
    backend_cfg = cfg.backend
    if inputs.backend_validation_receipt is not None:
        backend_cfg = backend_cfg.model_copy(
            update={"validation_receipt": inputs.backend_validation_receipt}
        )
    backend = create_backend(backend_cfg)
    run_dir: Path | None = None
    pre_receipt: dict[str, Any] | None = None

    try:
        backend.load()
        loaded_model_receipt = backend.model_receipt()
        (
            run_dir,
            run_id,
            input_hashes,
            implementation,
            model_identity,
            run_seal,
        ) = prepare_run_dir(
            cfg,
            inputs,
            environment=environment,
            model_receipt=loaded_model_receipt,
        )
        pre_receipt = {
            "schema_version": 1,
            "run_id": run_id,
            "run_seal": run_seal,
            "status": "loaded",
            "started_at": started,
            "config_path": inputs.config_path.name,
            "input_hashes": input_hashes,
            "backend": {
                **cfg.backend.model_dump(mode="json"),
                "api_key_env": cfg.backend.api_key_env,
            },
            "environment": environment,
            "implementation": implementation,
            "model_identity": model_identity,
            "model_receipt": loaded_model_receipt,
            "claim_boundary": "unresolved-until-capability-probe",
        }
        write_json(run_dir / "receipt.json", pre_receipt)
        write_yaml(run_dir / "resolved_config.yaml", cfg.model_dump(mode="json"))
        write_json(
            run_dir / "resolved_inputs.json",
            {
                "panel": [item.model_dump(mode="json") for item in inputs.panel_items],
                "wrapper_ids": [row["id"] for row in inputs.wrappers],
                "target_ids": [row["id"] for row in inputs.targets],
            },
        )
        capabilities = backend.capabilities()
        mode = choose_mode(cfg, capabilities)
        if mode == "internal" and not capabilities.supports(
            Capability.FORWARD_LOGITS,
            Capability.ACTIVATION_PATCH,
        ):
            missing = capabilities.missing(
                Capability.FORWARD_LOGITS,
                Capability.ACTIVATION_PATCH,
            )
            raise CapabilityError(f"Internal experiment missing capabilities: {missing}")
        plan = build_plan(
            cfg,
            inputs,
            capabilities,
            num_layers=backend.num_layers,
        )
        write_json(run_dir / "plan.json", plan)
        write_json(run_dir / "capabilities.json", capabilities.as_plain_dict())
        receipt = {
            **pre_receipt,
            "status": "running",
            "mode": mode,
            "claim_boundary": plan["claim_boundary"],
            "capabilities": capabilities.as_plain_dict(),
            "model_receipt": loaded_model_receipt,
            "plan": plan,
        }
        write_json(run_dir / "receipt.json", receipt)

        if mode == "internal":
            summary = InternalExperiment(cfg, inputs, backend, run_dir).run()
        else:
            summary = SurfaceExperiment(cfg, inputs, backend, run_dir).run()

        finished = datetime.now(timezone.utc).isoformat()
        final_capabilities = backend.capabilities()
        write_json(run_dir / "capabilities.json", final_capabilities.as_plain_dict())
        receipt.update(
            {
                "status": "complete",
                "finished_at": finished,
                "capabilities": final_capabilities.as_plain_dict(),
                "model_receipt": backend.model_receipt(),
                "summary_path": "summary.json",
            }
        )
        write_json(run_dir / "receipt.json", receipt)
        render_markdown_report(run_dir, summary, receipt)
        return run_dir, summary
    except Exception as exc:
        if run_dir is None:
            (
                run_dir,
                run_id,
                input_hashes,
                implementation,
                model_identity,
                run_seal,
            ) = prepare_run_dir(
                cfg,
                inputs,
                environment=environment,
                model_receipt=backend.model_receipt(),
            )
        if pre_receipt is None:
            pre_receipt = {
                "schema_version": 1,
                "run_id": run_id,
                "run_seal": run_seal,
                "started_at": started,
                "config_path": inputs.config_path.name,
                "input_hashes": input_hashes,
                "backend": cfg.backend.model_dump(mode="json"),
                "environment": environment,
                "implementation": implementation,
                "model_identity": model_identity,
                "model_receipt": backend.model_receipt(),
                "claim_boundary": "unresolved-until-capability-probe",
            }
        failed = {
            **pre_receipt,
            "status": "failed",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": repr(exc),
        }
        write_json(run_dir / "receipt.json", failed)
        raise
    finally:
        backend.close()
