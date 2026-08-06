from __future__ import annotations

import os
import time
from typing import Any

from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.errors import BackendLoadError
from glyphprobe.records import GenerationResult

from .base import Backend


class OpenAICompatibleBackend(Backend):
    """Generation-only adapter for OpenAI-compatible local servers.

    This adapter intentionally exposes no activation-patching capability. vLLM,
    llama.cpp, Ollama, and LM Studio therefore participate in surface controls and
    serving-parity checks, not in the internal residual-stream claim path.
    """

    def __init__(self, config):
        super().__init__(config)
        self.client: Any = None
        self._runtime_logprobs: bool | None = None
        self._server_models: list[str] = []

    def load(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise BackendLoadError(
                "Server backends require `pip install 'glyphprobe[server]'`."
            ) from exc
        api_key = "not-needed"
        if self.config.api_key_env:
            api_key = os.environ.get(self.config.api_key_env, "")
            if not api_key:
                raise BackendLoadError(
                    f"Environment variable {self.config.api_key_env!r} is not set"
                )
        kwargs: dict[str, Any] = {"api_key": api_key}
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url
        self.client = OpenAI(**kwargs)
        self._loaded = True

    @property
    def num_layers(self) -> None:
        return None

    def capabilities(self) -> CapabilityReport:
        enabled = {Capability.GENERATE}
        if self._runtime_logprobs:
            enabled.add(Capability.LOGPROBS)
        if self.config.kind in {"ollama", "lmstudio"}:
            enabled.add(Capability.SERVER_METRICS)
        return CapabilityReport(
            backend=self.config.kind,
            model=self.config.model,
            capabilities={cap: cap in enabled for cap in Capability},
            notes={
                "internal_state": (
                    "The standard OpenAI-compatible API does not expose residual streams, "
                    "attention tensors, or activation patching. Results are surface-observational."
                ),
                "logprobs": (
                    "Runtime-probed because support differs by provider, endpoint, model, and version."
                ),
            },
            metadata={
                "base_url": self.config.base_url,
                "runtime_logprobs": self._runtime_logprobs,
                "server_models": self._server_models,
            },
        )

    def probe(self) -> dict[str, Any]:
        if not self._loaded:
            self.load()
        result: dict[str, Any] = {"models_ok": False, "generation_ok": False}
        try:
            models = self.client.models.list()
            self._server_models = [str(item.id) for item in getattr(models, "data", [])]
            result["models_ok"] = True
            result["models"] = self._server_models
        except Exception as exc:
            result["models_error"] = repr(exc)
        try:
            generation = self.generate(
                "Reply with exactly: OK",
                seed=0,
                generation_overrides={"max_new_tokens": 4, "temperature": 0.0},
            )
            result["generation_ok"] = True
            result["text"] = generation.text
            result["runtime_logprobs"] = self._runtime_logprobs
        except Exception as exc:
            result["generation_error"] = repr(exc)
        return result

    @staticmethod
    def _value(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _parse_logprobs(self, choice: Any) -> dict[str, float]:
        output: dict[str, float] = {}
        logprobs = self._value(choice, "logprobs")
        content = self._value(logprobs, "content") if logprobs is not None else None
        if not content:
            return output
        first = content[0]
        token = self._value(first, "token")
        token_logprob = self._value(first, "logprob")
        if token is not None and token_logprob is not None:
            output[str(token)] = float(token_logprob)
        for entry in self._value(first, "top_logprobs", []) or []:
            item_token = self._value(entry, "token")
            item_logprob = self._value(entry, "logprob")
            if item_token is not None and item_logprob is not None:
                output[str(item_token)] = float(item_logprob)
        return output

    def generate(
        self,
        prompt: str,
        *,
        seed: int,
        intervention=None,
        system_prompt: str | None = None,
        generation_overrides: dict[str, Any] | None = None,
    ) -> GenerationResult:
        if intervention is not None:
            raise BackendLoadError(
                "OpenAI-compatible server backends cannot accept internal activation interventions"
            )
        cfg = self.config.generation.model_dump()
        cfg.update(generation_overrides or {})
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        request: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": int(cfg.get("max_new_tokens", 48)),
            "temperature": float(cfg.get("temperature", 0.0)),
            "top_p": float(cfg.get("top_p", 1.0)),
            "seed": int(seed),
        }
        ask_logprobs = bool(cfg.get("logprobs", True))
        if ask_logprobs:
            request["logprobs"] = True
            request["top_logprobs"] = int(cfg.get("top_logprobs", 20))
        extra_body: dict[str, Any] = {}
        if cfg.get("top_k") is not None:
            extra_body["top_k"] = int(cfg["top_k"])
        if extra_body:
            request["extra_body"] = extra_body

        start = time.perf_counter()
        retries: list[dict[str, Any]] = []
        response: Any = None
        attempt = dict(request)
        # Prefer retaining logprobs. Some servers reject seed or provider-specific
        # extra_body fields while still supporting top-logprob output.
        variants = (
            (),
            ("seed",),
            ("extra_body",),
            ("seed", "extra_body"),
            ("logprobs", "top_logprobs"),
            ("logprobs", "top_logprobs", "seed"),
            ("logprobs", "top_logprobs", "extra_body"),
            ("logprobs", "top_logprobs", "seed", "extra_body"),
        )
        seen: set[tuple[str, ...]] = set()
        for removal in variants:
            normalized = tuple(sorted(key for key in removal if key in request))
            if normalized in seen:
                continue
            seen.add(normalized)
            attempt = {key: value for key, value in request.items() if key not in removal}
            try:
                response = self.client.chat.completions.create(**attempt)
                break
            except Exception as exc:
                retries.append({"removed": list(removal), "error": repr(exc)})
        if response is None:
            raise BackendLoadError(f"All compatible chat-completion attempts failed: {retries}")
        latency_ms = (time.perf_counter() - start) * 1000.0
        choice = response.choices[0]
        message = self._value(choice, "message")
        content = self._value(message, "content", "")
        if isinstance(content, list):
            text = "".join(
                str(self._value(part, "text", ""))
                for part in content
                if self._value(part, "type", "text") == "text"
            )
        else:
            text = str(content or "")
        first_logprobs = self._parse_logprobs(choice)
        self._runtime_logprobs = bool(first_logprobs)
        usage_obj = self._value(response, "usage")
        usage: dict[str, int | float] = {}
        if usage_obj is not None:
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = self._value(usage_obj, key)
                if value is not None:
                    usage[key] = int(value)
        return GenerationResult(
            text=text,
            latency_ms=latency_ms,
            usage=usage,
            first_token_logprobs=first_logprobs,
            metadata={
                "provider": self.config.kind,
                "base_url": self.config.base_url,
                "response_id": self._value(response, "id"),
                "finish_reason": self._value(choice, "finish_reason"),
                "compatibility_retries": retries,
                "request_keys": sorted(attempt),
            },
        )

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        receipt.update(
            {
                "backend_class": type(self).__name__,
                "base_url": self.config.base_url,
                "server_models": self._server_models,
                "runtime_logprobs": self._runtime_logprobs,
                "internal_activation_access": False,
            }
        )
        return receipt
