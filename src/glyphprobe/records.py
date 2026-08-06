from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class TokenizationRecord:
    text: str
    token_ids: list[int]
    tokens: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Intervention:
    layer: int
    vector: np.ndarray
    site: str = "resid_post"
    position: str | int = "last_nonpad"
    label: str = "unnamed"


@dataclass(slots=True)
class ForwardResult:
    token_ids: list[int]
    tokens: list[str]
    logits: np.ndarray
    activations: dict[int, np.ndarray] = field(default_factory=dict)
    attentions: dict[int, np.ndarray] = field(default_factory=dict)
    latency_ms: float = 0.0
    peak_memory_bytes: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationResult:
    text: str
    token_ids: list[int] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    usage: dict[str, int | float] = field(default_factory=dict)
    first_token_logprobs: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
