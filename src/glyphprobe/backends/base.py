from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from glyphprobe.capabilities import CapabilityReport
from glyphprobe.config import BackendConfig
from glyphprobe.records import ForwardResult, GenerationResult, Intervention, TokenizationRecord


class Backend(ABC):
    """Capability-aware backend contract.

    Internal backends implement ``forward`` with optional activation intervention.
    Server backends implement generation and may expose logprobs, but deliberately do
    not pretend to expose residual streams through a standard OpenAI-compatible API.
    """

    def __init__(self, config: BackendConfig):
        self.config = config
        self._loaded = False

    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> CapabilityReport:
        raise NotImplementedError

    @property
    @abstractmethod
    def num_layers(self) -> int | None:
        raise NotImplementedError

    @property
    def model_dim(self) -> int | None:
        return None

    def tokenize(self, text: str) -> TokenizationRecord:
        raise NotImplementedError(f"{type(self).__name__} does not expose tokenization")

    def forward(
        self,
        prompt: str,
        *,
        capture_layers: list[int] | None = None,
        site: str = "resid_post",
        position: str | int = "last_nonpad",
        intervention: Intervention | None = None,
        return_attentions: bool = False,
    ) -> ForwardResult:
        raise NotImplementedError(f"{type(self).__name__} does not expose forward activations")

    def generate(
        self,
        prompt: str,
        *,
        seed: int,
        intervention: Intervention | None = None,
        system_prompt: str | None = None,
        generation_overrides: dict[str, Any] | None = None,
    ) -> GenerationResult:
        raise NotImplementedError(f"{type(self).__name__} does not expose generation")

    def model_receipt(self) -> dict[str, Any]:
        return {
            "backend": self.config.kind,
            "model": self.config.model,
            "revision": self.config.revision,
            "device": self.config.device,
            "dtype": self.config.dtype,
        }

    def close(self) -> None:
        return None
