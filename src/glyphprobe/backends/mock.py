from __future__ import annotations

import math
import time
from functools import cached_property
from typing import Any

import numpy as np

from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.records import ForwardResult, GenerationResult, Intervention, TokenizationRecord
from glyphprobe.seed import seed_everything

from .base import Backend


def _stable_seed(text: str) -> int:
    import hashlib

    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")


class MockBackend(Backend):
    """A deterministic toy residual stream used for smoke tests and CI.

    It is not a scientific subject. It only verifies that planning, direction
    construction, clipping, metrics, receipts, and reporting form a closed loop.
    """

    _n_layers = 8
    _d_model = 64
    _d_vocab = 512

    def load(self) -> None:
        _ = self.weights
        self._loaded = True

    @cached_property
    def weights(self) -> dict[str, np.ndarray]:
        rng = np.random.default_rng(_stable_seed(self.config.model))
        scale = 1.0 / math.sqrt(self._d_model)
        return {
            "embed": rng.normal(0, scale, size=(self._d_vocab, self._d_model)).astype(np.float32),
            "mix": rng.normal(0, scale, size=(self._n_layers, self._d_model, self._d_model)).astype(np.float32),
            "local": rng.normal(0, scale, size=(self._n_layers, self._d_model, self._d_model)).astype(np.float32),
            "unembed": rng.normal(0, scale, size=(self._d_model, self._d_vocab)).astype(np.float32),
        }

    @property
    def num_layers(self) -> int:
        return self._n_layers

    @property
    def model_dim(self) -> int:
        return self._d_model

    def capabilities(self) -> CapabilityReport:
        enabled = {
            Capability.TOKENIZE,
            Capability.GENERATE,
            Capability.FORWARD_LOGITS,
            Capability.HIDDEN_STATES,
            Capability.ACTIVATION_CACHE,
            Capability.ACTIVATION_PATCH,
            Capability.DETERMINISTIC_FORWARD,
        }
        return CapabilityReport(
            backend="mock",
            model=self.config.model,
            capabilities={cap: cap in enabled for cap in Capability},
            notes={"scientific_status": "CI-only synthetic backend; never use as evidence."},
            metadata={"num_layers": self._n_layers, "d_model": self._d_model},
        )

    def _tokens(self, text: str) -> list[str]:
        # Keep visible code points distinct and fold whitespace runs into one token.
        tokens: list[str] = []
        in_space = False
        for char in text:
            if char.isspace():
                if not in_space:
                    tokens.append("▁")
                in_space = True
            else:
                tokens.append(char)
                in_space = False
        return tokens or ["<empty>"]

    def _token_id(self, token: str) -> int:
        return _stable_seed(token) % self._d_vocab

    def tokenize(self, text: str) -> TokenizationRecord:
        tokens = self._tokens(text)
        return TokenizationRecord(
            text=text,
            token_ids=[self._token_id(tok) for tok in tokens],
            tokens=tokens,
            metadata={"tokenizer": "mock-codepoint"},
        )

    @staticmethod
    def _resolve_position(position: str | int, length: int) -> int:
        if isinstance(position, int):
            return position if position >= 0 else length + position
        if position in {"last", "last_nonpad", "anchor"}:
            return length - 1
        raise ValueError(f"Unsupported position: {position}")

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
        del return_attentions
        if site != "resid_post":
            raise ValueError("MockBackend only supports resid_post")
        start = time.perf_counter()
        record = self.tokenize(prompt)
        ids = np.asarray(record.token_ids, dtype=np.int64)
        h = self.weights["embed"][ids].copy()
        target_pos = self._resolve_position(position, len(ids))
        capture = set(capture_layers or [])
        activations: dict[int, np.ndarray] = {}

        for layer in range(self._n_layers):
            # A tiny causal mixer gives earlier glyphs a path into the final anchor.
            prefix_mean = np.cumsum(h, axis=0) / np.arange(1, len(h) + 1)[:, None]
            mixed = np.tanh(prefix_mean @ self.weights["mix"][layer])
            local = np.tanh(h @ self.weights["local"][layer])
            h = h + 0.45 * mixed + 0.35 * local
            if intervention is not None and intervention.layer == layer:
                idx = self._resolve_position(intervention.position, len(ids))
                if intervention.vector.shape != (self._d_model,):
                    raise ValueError("Mock intervention vector has wrong shape")
                h[idx] = h[idx] + intervention.vector.astype(h.dtype, copy=False)
            if layer in capture:
                activations[layer] = h[target_pos].astype(np.float32, copy=True)

        logits = (h[target_pos] @ self.weights["unembed"]).astype(np.float32)
        elapsed = (time.perf_counter() - start) * 1000.0
        return ForwardResult(
            token_ids=record.token_ids,
            tokens=record.tokens,
            logits=logits,
            activations=activations,
            latency_ms=elapsed,
            metadata={"site": site, "position": target_pos},
        )

    def generate(
        self,
        prompt: str,
        *,
        seed: int,
        intervention: Intervention | None = None,
        system_prompt: str | None = None,
        generation_overrides: dict[str, Any] | None = None,
    ) -> GenerationResult:
        seed_everything(seed)
        cfg = self.config.generation.model_dump()
        cfg.update(generation_overrides or {})
        full = f"{system_prompt}\n{prompt}" if system_prompt else prompt
        start = time.perf_counter()
        result = self.forward(
            full,
            capture_layers=[],
            intervention=intervention,
            position="last_nonpad",
        )
        rng = np.random.default_rng(seed)
        logits = result.logits.astype(np.float64)
        temperature = float(cfg.get("temperature", 0.0))
        n = min(int(cfg.get("max_new_tokens", 8)), 16)
        out_ids: list[int] = []
        for step in range(n):
            shifted = logits + 0.01 * step
            if temperature > 0:
                probs = np.exp((shifted - shifted.max()) / temperature)
                probs /= probs.sum()
                token_id = int(rng.choice(len(probs), p=probs))
            else:
                token_id = int(np.argmax(shifted))
            out_ids.append(token_id)
            logits = np.roll(logits, token_id % 17)
        tokens = [f"tok_{token_id}" for token_id in out_ids]
        text = " ".join(tokens)
        return GenerationResult(
            text=text,
            token_ids=out_ids,
            tokens=tokens,
            latency_ms=(time.perf_counter() - start) * 1000.0,
            usage={"prompt_tokens": len(result.token_ids), "completion_tokens": len(out_ids)},
            metadata={"mock": True},
        )

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        receipt.update(
            {
                "num_layers": self._n_layers,
                "d_model": self._d_model,
                "d_vocab": self._d_vocab,
                "scientific_status": "CI-only synthetic backend",
            }
        )
        return receipt
