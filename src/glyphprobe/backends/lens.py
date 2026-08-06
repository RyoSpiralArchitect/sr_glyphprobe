from __future__ import annotations

import contextlib
import inspect
import time
from collections.abc import Iterator
from typing import Any

import numpy as np

from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.errors import BackendLoadError, CapabilityError
from glyphprobe.records import ForwardResult, GenerationResult, Intervention, TokenizationRecord
from glyphprobe.seed import seed_everything

from .base import Backend


class TransformerLensBackend(Backend):
    """TransformerLens backend using canonical hook names.

    The loader first uses the current ``TransformerBridge.boot_transformers`` path
    and falls back to ``HookedTransformer.from_pretrained`` for older releases.
    """

    def __init__(self, config):
        super().__init__(config)
        self.model: Any = None
        self.torch: Any = None
        self.device = "cpu"
        self.loader_path: str | None = None
        self.loader_metadata: dict[str, Any] = {}
        self._n_layers: int | None = None
        self._d_model: int | None = None

    @staticmethod
    def _select_device(torch: Any, requested: str) -> str:
        if requested != "auto":
            return requested
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    @staticmethod
    def _resolve_dtype(torch: Any, name: str, device: str) -> Any:
        if name == "auto":
            # TransformerBridge currently defaults to float32. Keep that conservative
            # default instead of silently changing arithmetic when the device changes.
            return torch.float32
        mapping = {
            "float32": torch.float32,
            "fp32": torch.float32,
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
        }
        if name not in mapping:
            raise BackendLoadError(f"Unsupported dtype: {name}")
        return mapping[name]

    @staticmethod
    def _accepted_kwargs(
        callable_obj: Any,
        candidates: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        """Filter loader kwargs without assuming one TransformerLens release.

        A loader that declares ``**kwargs`` receives all candidates. Otherwise unknown
        keys are retained in the receipt and rejected before a potentially misleading
        fallback changes the model-loading semantics.
        """
        signature = inspect.signature(callable_obj)
        accepts_var_kwargs = any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        if accepts_var_kwargs:
            return dict(candidates), []
        accepted = {
            key: value for key, value in candidates.items() if key in signature.parameters
        }
        rejected = sorted(set(candidates) - set(accepted))
        return accepted, rejected

    def load(self) -> None:
        try:
            import torch
        except ImportError as exc:
            raise BackendLoadError("TransformerLens requires PyTorch") from exc
        self.torch = torch
        self.device = self._select_device(torch, self.config.device)
        dtype = self._resolve_dtype(torch, self.config.dtype, self.device)

        bridge_error: Exception | None = None
        bridge_candidates: dict[str, Any] = {
            "device": self.device,
            "dtype": dtype,
            "revision": self.config.revision,
            "trust_remote_code": self.config.trust_remote_code,
            "local_files_only": self.config.local_files_only
            if self.config.local_files_only
            else None,
            **dict(self.config.model_kwargs),
        }
        bridge_candidates = {
            key: value for key, value in bridge_candidates.items() if value is not None
        }
        try:
            from transformer_lens.model_bridge import TransformerBridge

            bridge_kwargs, rejected = self._accepted_kwargs(
                TransformerBridge.boot_transformers,
                bridge_candidates,
            )
            if rejected:
                raise BackendLoadError(
                    "TransformerBridge.boot_transformers does not accept configured model_kwargs: "
                    + ", ".join(rejected)
                )
            self.model = TransformerBridge.boot_transformers(
                self.config.model,
                **bridge_kwargs,
            )
            self.loader_path = "TransformerBridge.boot_transformers"
            self.loader_metadata = {
                "resolved_dtype": str(dtype),
                "accepted_kwargs": sorted(bridge_kwargs),
                "local_files_only_requested": self.config.local_files_only,
            }
        except Exception as exc:  # fallback is intentional across TL generations
            bridge_error = exc
            try:
                from transformer_lens import HookedTransformer

                fallback_candidates: dict[str, Any] = {
                    "device": self.device,
                    "dtype": dtype,
                    "revision": self.config.revision,
                    "trust_remote_code": self.config.trust_remote_code,
                    "local_files_only": self.config.local_files_only
                    if self.config.local_files_only
                    else None,
                    **dict(self.config.model_kwargs),
                }
                fallback_candidates = {
                    key: value
                    for key, value in fallback_candidates.items()
                    if value is not None
                }
                fallback_kwargs, rejected = self._accepted_kwargs(
                    HookedTransformer.from_pretrained,
                    fallback_candidates,
                )
                if rejected:
                    raise BackendLoadError(
                        "HookedTransformer.from_pretrained does not accept configured model_kwargs: "
                        + ", ".join(rejected)
                    )
                self.model = HookedTransformer.from_pretrained(
                    self.config.model,
                    **fallback_kwargs,
                )
                self.loader_path = "HookedTransformer.from_pretrained"
                self.loader_metadata = {
                    "resolved_dtype": str(dtype),
                    "accepted_kwargs": sorted(fallback_kwargs),
                    "bridge_error": repr(bridge_error),
                    "local_files_only_requested": self.config.local_files_only,
                }
            except Exception as fallback_exc:
                raise BackendLoadError(
                    "Could not load TransformerLens. Install `glyphprobe[lens]` and verify "
                    f"that the architecture is supported. Bridge error: {bridge_error!r}; "
                    f"fallback error: {fallback_exc!r}"
                ) from fallback_exc

        cfg = getattr(self.model, "cfg", None)
        self._n_layers = next(
            (
                int(getattr(cfg, name))
                for name in ("n_layers", "num_hidden_layers")
                if cfg is not None and getattr(cfg, name, None) is not None
            ),
            None,
        )
        self._d_model = next(
            (
                int(getattr(cfg, name))
                for name in ("d_model", "hidden_size", "n_embd")
                if cfg is not None and getattr(cfg, name, None) is not None
            ),
            None,
        )
        if self._n_layers is None:
            blocks = getattr(self.model, "blocks", None)
            if blocks is not None:
                self._n_layers = len(blocks)
        if self._n_layers is None:
            raise BackendLoadError("TransformerLens model did not expose a layer count")
        if hasattr(self.model, "eval"):
            self.model.eval()
        self._loaded = True

    @property
    def num_layers(self) -> int:
        if self._n_layers is None:
            raise BackendLoadError("Backend is not loaded")
        return self._n_layers

    @property
    def model_dim(self) -> int | None:
        return self._d_model

    def capabilities(self) -> CapabilityReport:
        enabled = {
            Capability.TOKENIZE,
            Capability.GENERATE,
            Capability.FORWARD_LOGITS,
            Capability.HIDDEN_STATES,
            Capability.ACTIVATION_CACHE,
            Capability.ACTIVATION_PATCH,
            Capability.CANONICAL_HOOKS,
            Capability.DETERMINISTIC_FORWARD,
        }
        return CapabilityReport(
            backend="lens",
            model=self.config.model,
            capabilities={cap: cap in enabled for cap in Capability},
            notes={
                "hook_semantics": "Canonical TransformerLens hook names are used.",
                "generation_intervention": (
                    "Supported when the loaded bridge exposes the hooks context manager; "
                    "otherwise numeric one-step intervention remains available."
                ),
            },
            metadata={
                "loader": self.loader_path,
                "loader_metadata": self.loader_metadata,
                "num_layers": self._n_layers,
                "d_model": self._d_model,
            },
        )

    @staticmethod
    def hook_name(layer: int, site: str) -> str:
        mapping = {
            "resid_pre": "hook_resid_pre",
            "resid_post": "hook_resid_post",
            "attn_out": "hook_attn_out",
            "mlp_out": "hook_mlp_out",
        }
        if site not in mapping:
            raise CapabilityError(f"Unsupported TransformerLens site: {site}")
        return f"blocks.{layer}.{mapping[site]}"

    def _to_tokens(self, text: str) -> Any:
        kwargs: dict[str, Any] = {}
        signature = inspect.signature(self.model.to_tokens)
        if "prepend_bos" in signature.parameters:
            kwargs["prepend_bos"] = self.config.add_special_tokens
        return self.model.to_tokens(text, **kwargs)

    def tokenize(self, text: str) -> TokenizationRecord:
        tokens = self._to_tokens(text)
        ids = [int(value) for value in tokens[0].detach().cpu().tolist()]
        if hasattr(self.model, "to_str_tokens"):
            try:
                str_tokens = [str(value) for value in self.model.to_str_tokens(tokens)]
            except Exception:
                str_tokens = [str(value) for value in ids]
        else:
            tokenizer = getattr(self.model, "tokenizer", None)
            str_tokens = (
                [str(value) for value in tokenizer.convert_ids_to_tokens(ids)]
                if tokenizer is not None
                else [str(value) for value in ids]
            )
        return TokenizationRecord(
            text=text,
            token_ids=ids,
            tokens=str_tokens,
            metadata={"loader": self.loader_path},
        )

    @staticmethod
    def _position_index(position: str | int, activation: Any) -> int:
        length = int(activation.shape[1])
        if isinstance(position, int):
            idx = position if position >= 0 else length + position
        elif position in {"last", "last_nonpad", "anchor"}:
            idx = length - 1
        else:
            raise ValueError(f"Unsupported position: {position}")
        if not 0 <= idx < length:
            raise IndexError(f"Position {idx} outside sequence length {length}")
        return idx

    def _build_hooks(
        self,
        *,
        capture_layers: list[int],
        site: str,
        position: str | int,
        intervention: Intervention | None,
        captured: dict[int, np.ndarray] | None,
    ) -> list[tuple[str, Any]]:
        hooks: list[tuple[str, Any]] = []
        layers = sorted(set(capture_layers + ([intervention.layer] if intervention else [])))
        for layer in layers:
            name = self.hook_name(layer, site)

            def edit_and_capture(act: Any, hook: Any, *, layer_idx: int = layer):
                del hook
                result = act
                if intervention is not None and intervention.layer == layer_idx:
                    idx = self._position_index(intervention.position, act)
                    result = act.clone()
                    vector = self.torch.as_tensor(
                        intervention.vector,
                        device=act.device,
                        dtype=act.dtype,
                    )
                    result[:, idx, :] = result[:, idx, :] + vector
                if captured is not None and layer_idx in capture_layers:
                    idx = self._position_index(position, result)
                    captured[layer_idx] = (
                        result[0, idx, :].detach().float().cpu().numpy().copy()
                    )
                return result

            hooks.append((name, edit_and_capture))
        return hooks

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
        capture_layers = capture_layers or []
        tokens = self._to_tokens(prompt)
        ids = [int(value) for value in tokens[0].detach().cpu().tolist()]
        token_record = self.tokenize(prompt)
        captured: dict[int, np.ndarray] = {}
        hooks = self._build_hooks(
            capture_layers=capture_layers,
            site=site,
            position=position,
            intervention=intervention,
            captured=captured,
        )
        if self.torch.cuda.is_available() and str(tokens.device).startswith("cuda"):
            self.torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        with self.torch.inference_mode():
            logits = self.model.run_with_hooks(tokens, fwd_hooks=hooks)
        latency_ms = (time.perf_counter() - start) * 1000.0
        if isinstance(logits, tuple):
            logits = logits[0]
        final_logits = logits[0, -1, :].detach().float().cpu().numpy().copy()
        peak = None
        if self.torch.cuda.is_available() and str(tokens.device).startswith("cuda"):
            peak = int(self.torch.cuda.max_memory_allocated())
        return ForwardResult(
            token_ids=ids,
            tokens=token_record.tokens,
            logits=final_logits,
            activations=captured,
            latency_ms=latency_ms,
            peak_memory_bytes=peak,
            metadata={
                "site": site,
                "loader": self.loader_path,
                "intervention_scope": "single full-sequence forward",
            },
        )

    @contextlib.contextmanager
    def _hook_context(self, hooks: list[tuple[str, Any]]) -> Iterator[None]:
        if hasattr(self.model, "hooks"):
            with self.model.hooks(fwd_hooks=hooks):
                yield
            return
        raise CapabilityError(
            "This TransformerLens bridge does not expose a hooks context manager for generation"
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
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        cfg = self.config.generation.model_dump()
        cfg.update(generation_overrides or {})
        cfg.pop("logprobs", None)
        cfg.pop("top_logprobs", None)
        do_sample = cfg.pop("do_sample", None)
        if do_sample is None:
            do_sample = float(cfg.get("temperature", 0.0)) > 0
        if not do_sample:
            cfg.pop("temperature", None)
            cfg.pop("top_p", None)
            cfg.pop("top_k", None)
        cfg = {key: value for key, value in cfg.items() if value is not None}
        cfg["do_sample"] = do_sample
        hooks: list[tuple[str, Any]] = []
        context: Any = contextlib.nullcontext()
        if intervention is not None:
            hooks = self._build_hooks(
                capture_layers=[],
                site=intervention.site,
                position="last_nonpad",
                intervention=intervention,
                captured=None,
            )
            context = self._hook_context(hooks)
        start = time.perf_counter()
        with self.torch.inference_mode(), context:
            output = self.model.generate(full_prompt, **cfg)
        latency_ms = (time.perf_counter() - start) * 1000.0
        if isinstance(output, str):
            full_text = output
            text = output[len(full_prompt) :] if output.startswith(full_prompt) else output
            token_ids: list[int] = []
            tokens: list[str] = []
        else:
            tensor = output[0] if getattr(output, "ndim", 1) > 1 else output
            all_ids = [int(value) for value in tensor.detach().cpu().tolist()]
            prompt_ids = self.tokenize(full_prompt).token_ids
            token_ids = all_ids[len(prompt_ids) :]
            tokenizer = getattr(self.model, "tokenizer", None)
            text = tokenizer.decode(token_ids, skip_special_tokens=True) if tokenizer else str(token_ids)
            tokens = (
                [str(value) for value in tokenizer.convert_ids_to_tokens(token_ids)]
                if tokenizer
                else [str(value) for value in token_ids]
            )
            full_text = text
        return GenerationResult(
            text=text,
            token_ids=token_ids,
            tokens=tokens,
            latency_ms=latency_ms,
            usage={"completion_tokens": len(token_ids)},
            metadata={
                "loader": self.loader_path,
                "raw_full_text": full_text,
                "intervention_scope": (
                    "hook applied to the final available position on every decode forward"
                    if intervention
                    else "none"
                ),
            },
        )

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        cfg = getattr(self.model, "cfg", None)
        receipt.update(
            {
                "backend_class": type(self).__name__,
                "loader": self.loader_path,
                "model_class": type(self.model).__name__ if self.model is not None else None,
                "num_layers": self._n_layers,
                "d_model": self._d_model,
                "resolved_device": self.device,
                "config_model_name": getattr(cfg, "model_name", None) if cfg else None,
                "loader_metadata": self.loader_metadata,
            }
        )
        return receipt
