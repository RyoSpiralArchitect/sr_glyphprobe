from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import ConfigurationError
from .io import read_jsonl, read_yaml

BackendKind = Literal[
    "mock",
    "transformers",
    "lens",
    "mlx",
    "vllm",
    "llamacpp",
    "ollama",
    "lmstudio",
    "openai",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GenerationConfig(StrictModel):
    max_new_tokens: int = 48
    temperature: float = 0.0
    top_p: float = 1.0
    top_k: int | None = None
    do_sample: bool | None = None
    logprobs: bool = True
    top_logprobs: int = 20

    @field_validator("max_new_tokens", "top_logprobs")
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be positive")
        return value

    @field_validator("temperature")
    @classmethod
    def nonnegative_temperature(cls, value: float) -> float:
        if value < 0:
            raise ValueError("temperature must be non-negative")
        return value

    @field_validator("top_p")
    @classmethod
    def probability_top_p(cls, value: float) -> float:
        if not 0 < value <= 1:
            raise ValueError("top_p must be in (0, 1]")
        return value

    @field_validator("top_k")
    @classmethod
    def positive_optional_top_k(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("top_k must be positive when set")
        return value


class BackendConfig(StrictModel):
    kind: BackendKind = "lens"
    model: str = "openai-community/gpt2"
    revision: str | None = None
    device: str = "auto"
    dtype: str = "auto"
    base_url: str | None = None
    api_key_env: str | None = None
    trust_remote_code: bool = False
    local_files_only: bool = False
    add_special_tokens: bool = True
    model_kwargs: dict[str, Any] = Field(default_factory=dict)
    validation_receipt: Path | None = None
    validation_receipt_sha256: str | None = None
    generation: GenerationConfig = Field(default_factory=GenerationConfig)

    @model_validator(mode="after")
    def validation_receipt_pair(self) -> "BackendConfig":
        if (self.validation_receipt is None) != (self.validation_receipt_sha256 is None):
            raise ValueError(
                "backend.validation_receipt and backend.validation_receipt_sha256 "
                "must be set together"
            )
        if self.validation_receipt_sha256 is not None:
            digest = self.validation_receipt_sha256.lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("backend.validation_receipt_sha256 must be 64 hex characters")
        return self


class RunConfig(StrictModel):
    name: str = "colored-shapes-v1"
    output_root: Path = Path("runs")
    seeds: list[int] = Field(default_factory=lambda: [101, 211, 307])
    deterministic_torch: bool = False
    resume: bool = True
    fail_fast: bool = True
    max_errors: int = 10
    replicate_mode: Literal["wrapper_subsample", "full_direction"] = "wrapper_subsample"
    wrapper_subsample_fraction: float = 0.75

    @field_validator("seeds")
    @classmethod
    def nonempty_unique_seeds(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("at least one seed is required")
        if len(set(value)) != len(value):
            raise ValueError("seeds must be unique")
        return value

    @field_validator("wrapper_subsample_fraction")
    @classmethod
    def valid_fraction(cls, value: float) -> float:
        if not 0 < value <= 1:
            raise ValueError("must be in (0, 1]")
        return value

    @field_validator("max_errors")
    @classmethod
    def positive_max_errors(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_errors must be positive")
        return value


class EmojiItem(StrictModel):
    id: str
    glyph: str
    factors: dict[str, str] = Field(default_factory=dict)
    labels: list[str] = Field(default_factory=list)

    @field_validator("glyph")
    @classmethod
    def nonempty_glyph(cls, value: str) -> str:
        if not value:
            raise ValueError("glyph cannot be empty")
        return value


class PanelConfig(StrictModel):
    file: Path | None = None
    items: list[EmojiItem] = Field(default_factory=list)
    neutral_glyph: str = "·"
    centroid_mode: Literal["panel", "neutral", "none"] = "panel"

    @model_validator(mode="after")
    def source_present(self) -> "PanelConfig":
        if self.file is None and not self.items:
            raise ValueError("panel.file or panel.items is required")
        return self


class SourceConfig(StrictModel):
    wrappers_file: Path
    max_wrappers: int | None = None
    anchor_position: str | int = "last_nonpad"


class TargetConfig(StrictModel):
    cases_file: Path
    max_cases: int | None = None
    calibration_cases: int = 8
    generation_cases: int = 8

    @field_validator("max_cases")
    @classmethod
    def positive_optional_max_cases(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("max_cases must be positive when set")
        return value

    @field_validator("calibration_cases", "generation_cases")
    @classmethod
    def positive_case_count(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("case counts must be positive")
        return value


class CaptureConfig(StrictModel):
    site: Literal["resid_post", "resid_pre", "attn_out", "mlp_out"] = "resid_post"
    layers: list[int | float] = Field(
        default_factory=lambda: [0.15, 0.30, 0.45, 0.60, 0.75, 0.90]
    )
    position: str | int = "last_nonpad"
    return_attentions: bool = False

    @field_validator("layers")
    @classmethod
    def validate_layers(cls, value: list[int | float]) -> list[int | float]:
        if not value:
            raise ValueError("capture.layers cannot be empty")
        for layer in value:
            if isinstance(layer, float) and not 0 <= layer <= 1:
                raise ValueError("float layer coordinates must be in [0, 1]")
            if isinstance(layer, int) and layer < 0:
                raise ValueError("integer layers must be non-negative")
        return value


class ClipConfig(StrictModel):
    mode: Literal["none", "global_rms"] = "global_rms"
    max_ratio: float = 0.25

    @field_validator("max_ratio")
    @classmethod
    def positive_ratio(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("max_ratio must be positive")
        return value


class IsoKLConfig(StrictModel):
    enabled: bool = False
    target_kl: float = 0.03
    tolerance: float = 0.004
    min_strength: float = 0.001
    max_strength: float = 0.35
    bisection_steps: int = 7
    per_seed: bool = False

    @model_validator(mode="after")
    def valid_calibration_range(self) -> "IsoKLConfig":
        if self.target_kl <= 0 or self.tolerance <= 0:
            raise ValueError("target_kl and tolerance must be positive")
        if self.min_strength <= 0 or self.max_strength <= self.min_strength:
            raise ValueError("iso-KL strengths require 0 < min_strength < max_strength")
        if self.bisection_steps <= 0:
            raise ValueError("bisection_steps must be positive")
        return self


class InterventionConfig(StrictModel):
    mode: Literal["activation_add"] = "activation_add"
    normalization: Literal["rms", "l2", "none"] = "rms"
    strengths: list[float] = Field(default_factory=lambda: [0.025, 0.05, 0.10])
    position: str | int = "last_nonpad"
    clip: ClipConfig = Field(default_factory=ClipConfig)
    iso_kl: IsoKLConfig = Field(default_factory=IsoKLConfig)

    @field_validator("strengths")
    @classmethod
    def valid_strengths(cls, value: list[float]) -> list[float]:
        if not value or any(v <= 0 for v in value):
            raise ValueError("all intervention strengths must be positive")
        return sorted(set(value))


class ControlConfig(StrictModel):
    random_directions_per_layer: int = 2
    zero_direction: bool = True
    sign_flip: bool = True
    sign_flip_strengths: list[float] = Field(default_factory=lambda: [0.05])
    label_shuffle_permutations: int = 1000
    include_neutral_direction: bool = True

    @field_validator("random_directions_per_layer", "label_shuffle_permutations")
    @classmethod
    def nonnegative_control_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("control counts must be non-negative")
        return value

    @field_validator("sign_flip_strengths")
    @classmethod
    def positive_sign_flip_strengths(cls, value: list[float]) -> list[float]:
        if any(item <= 0 for item in value):
            raise ValueError("sign-flip strengths must be positive")
        return sorted(set(value))


class MetricConfig(StrictModel):
    top_k: int = 50
    fingerprint_dim: int = 96
    fingerprint_seed: int = 8675309
    split_half_repeats: int = 200
    rbo_p: float = 0.90
    save_top_logit_deltas: int = 32
    save_fingerprints: bool = True
    epsilon: float = 1e-12

    @field_validator("top_k", "fingerprint_dim", "split_half_repeats", "save_top_logit_deltas")
    @classmethod
    def positive_metric_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("metric counts and dimensions must be positive")
        return value

    @field_validator("rbo_p")
    @classmethod
    def valid_rbo_p(cls, value: float) -> float:
        if not 0 < value < 1:
            raise ValueError("rbo_p must be in (0, 1)")
        return value

    @field_validator("epsilon")
    @classmethod
    def positive_epsilon(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("epsilon must be positive")
        return value


class SAEConfig(StrictModel):
    enabled: bool = False
    release: str | None = None
    sae_ids: dict[int, str] = Field(default_factory=dict)
    device: str = "auto"
    top_k_features: int = 32

    @model_validator(mode="after")
    def require_release_when_enabled(self) -> "SAEConfig":
        if self.enabled and not self.release:
            raise ValueError("sae.release is required when SAE analysis is enabled")
        if self.top_k_features <= 0:
            raise ValueError("sae.top_k_features must be positive")
        return self


class SurfaceConfig(StrictModel):
    emoji_template: str = "{emoji}\n{prompt}"
    neutral_template: str = "{prompt}"
    system_prompt: str | None = None
    enabled_logprobs: bool = True


class ExperimentConfig(StrictModel):
    schema_version: int = 1
    mode: Literal["auto", "internal", "surface"] = "auto"
    backend: BackendConfig = Field(default_factory=BackendConfig)
    run: RunConfig = Field(default_factory=RunConfig)
    panel: PanelConfig
    source: SourceConfig
    targets: TargetConfig
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    intervention: InterventionConfig = Field(default_factory=InterventionConfig)
    controls: ControlConfig = Field(default_factory=ControlConfig)
    metrics: MetricConfig = Field(default_factory=MetricConfig)
    sae: SAEConfig = Field(default_factory=SAEConfig)
    surface: SurfaceConfig = Field(default_factory=SurfaceConfig)

    @model_validator(mode="after")
    def mode_backend_contract(self) -> "ExperimentConfig":
        remote = self.backend.kind in {"vllm", "llamacpp", "ollama", "lmstudio", "openai"}
        if self.mode == "internal" and remote:
            raise ValueError(
                "remote OpenAI-compatible backends do not expose internal activation patching; "
                "use mode=surface or mode=auto"
            )
        return self


class ResolvedInputs(StrictModel):
    config_path: Path
    base_dir: Path
    panel_items: list[EmojiItem]
    wrappers: list[dict[str, Any]]
    targets: list[dict[str, Any]]
    input_paths: list[Path]
    backend_validation_receipt: Path | None = None


def _resolve_path(path: Path, base_dir: Path) -> Path:
    path = Path(os.path.expandvars(str(path))).expanduser()
    return path if path.is_absolute() else (base_dir / path).resolve()


def _parse_override_value(raw: str) -> Any:
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _set_dotted(mapping: dict[str, Any], dotted_key: str, value: Any) -> None:
    cursor = mapping
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        child = cursor.get(part)
        if child is None:
            child = {}
            cursor[part] = child
        if not isinstance(child, dict):
            raise ConfigurationError(f"Cannot set {dotted_key}: {part} is not a mapping")
        cursor = child
    cursor[parts[-1]] = value


def load_experiment_config(
    path: str | Path,
    *,
    overrides: list[str] | None = None,
) -> tuple[ExperimentConfig, ResolvedInputs]:
    config_path = Path(path).expanduser().resolve()
    raw = read_yaml(config_path)
    for entry in overrides or []:
        if "=" not in entry:
            raise ConfigurationError(f"Override must be KEY=VALUE, got {entry!r}")
        key, value = entry.split("=", 1)
        _set_dotted(raw, key, _parse_override_value(value))

    cfg = ExperimentConfig.model_validate(raw)
    base_dir = config_path.parent

    input_paths: list[Path] = [config_path]
    backend_validation_receipt: Path | None = None
    if cfg.backend.validation_receipt is not None:
        backend_validation_receipt = _resolve_path(
            cfg.backend.validation_receipt, base_dir
        )
        if not backend_validation_receipt.is_file():
            raise ConfigurationError(
                "Backend validation receipt does not exist: "
                f"{backend_validation_receipt}"
            )
        input_paths.append(backend_validation_receipt)
    panel_items = list(cfg.panel.items)
    if cfg.panel.file is not None:
        panel_path = _resolve_path(cfg.panel.file, base_dir)
        panel_raw = read_yaml(panel_path)
        values = panel_raw.get("items", panel_raw)
        if not isinstance(values, list):
            raise ConfigurationError(f"Panel file must contain a list or items list: {panel_path}")
        panel_items = [EmojiItem.model_validate(item) for item in values]
        input_paths.append(panel_path)

    if not panel_items:
        raise ConfigurationError("The resolved emoji panel is empty")
    ids = [item.id for item in panel_items]
    glyphs = [item.glyph for item in panel_items]
    if len(ids) != len(set(ids)):
        raise ConfigurationError("Emoji panel IDs must be unique")
    if len(glyphs) != len(set(glyphs)):
        raise ConfigurationError("Emoji panel glyphs must be unique")

    wrappers_path = _resolve_path(cfg.source.wrappers_file, base_dir)
    targets_path = _resolve_path(cfg.targets.cases_file, base_dir)
    wrappers = read_jsonl(wrappers_path)
    targets = read_jsonl(targets_path)
    input_paths.extend([wrappers_path, targets_path])

    if cfg.source.max_wrappers is not None:
        wrappers = wrappers[: cfg.source.max_wrappers]
    if cfg.targets.max_cases is not None:
        targets = targets[: cfg.targets.max_cases]
    if not wrappers:
        raise ConfigurationError("No source wrappers were resolved")
    if not targets:
        raise ConfigurationError("No target cases were resolved")
    for row in wrappers:
        if "id" not in row or "template" not in row or "{emoji}" not in row["template"]:
            raise ConfigurationError("Every wrapper needs id and a template containing {emoji}")
    for row in targets:
        if "id" not in row or "prompt" not in row:
            raise ConfigurationError("Every target needs id and prompt")

    return cfg, ResolvedInputs(
        config_path=config_path,
        base_dir=base_dir,
        panel_items=panel_items,
        wrappers=wrappers,
        targets=targets,
        input_paths=input_paths,
        backend_validation_receipt=backend_validation_receipt,
    )


def apply_cli_overrides(
    cfg: ExperimentConfig,
    *,
    backend: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    device: str | None = None,
    dtype: str | None = None,
    emojis: list[str] | None = None,
    output_root: Path | None = None,
) -> ExperimentConfig:
    data = cfg.model_dump(mode="python")
    if backend:
        data["backend"]["kind"] = backend
    if model:
        data["backend"]["model"] = model
    if base_url:
        data["backend"]["base_url"] = base_url
    if device:
        data["backend"]["device"] = device
    if dtype:
        data["backend"]["dtype"] = dtype
    if output_root:
        data["run"]["output_root"] = output_root
    if emojis:
        data["panel"]["file"] = None
        existing = {item.id: item for item in cfg.panel.items}
        inline: list[dict[str, Any]] = []
        for index, glyph in enumerate(emojis):
            match = next((item for item in existing.values() if item.glyph == glyph), None)
            if match:
                inline.append(match.model_dump(mode="python"))
            else:
                inline.append({"id": f"glyph_{index:02d}", "glyph": glyph, "factors": {}})
        data["panel"]["items"] = inline
    return ExperimentConfig.model_validate(data)


def resolve_layers(layer_specs: list[int | float], num_layers: int) -> list[int]:
    if num_layers <= 0:
        raise ConfigurationError("Backend reported no transformer layers")
    resolved: list[int] = []
    for value in layer_specs:
        if isinstance(value, float):
            layer = int(round(value * (num_layers - 1)))
        else:
            layer = value
        if not 0 <= layer < num_layers:
            raise ConfigurationError(
                f"Resolved layer {layer} is outside [0, {num_layers - 1}]"
            )
        resolved.append(layer)
    return sorted(set(resolved))
