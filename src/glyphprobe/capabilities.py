from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Capability(StrEnum):
    TOKENIZE = "tokenize"
    GENERATE = "generate"
    FORWARD_LOGITS = "forward_logits"
    LOGPROBS = "logprobs"
    HIDDEN_STATES = "hidden_states"
    ATTENTION_WEIGHTS = "attention_weights"
    ACTIVATION_CACHE = "activation_cache"
    ACTIVATION_PATCH = "activation_patch"
    CANONICAL_HOOKS = "canonical_hooks"
    SAE_ANALYSIS = "sae_analysis"
    DETERMINISTIC_FORWARD = "deterministic_forward"
    SERVER_METRICS = "server_metrics"


class CapabilityReport(BaseModel):
    backend: str
    model: str
    capabilities: dict[Capability, bool] = Field(default_factory=dict)
    notes: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def supports(self, *required: Capability) -> bool:
        return all(self.capabilities.get(cap, False) for cap in required)

    def missing(self, *required: Capability) -> list[Capability]:
        return [cap for cap in required if not self.capabilities.get(cap, False)]

    def as_plain_dict(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["capabilities"] = {str(k): bool(v) for k, v in self.capabilities.items()}
        return data
