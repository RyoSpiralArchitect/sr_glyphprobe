from __future__ import annotations

import contextlib
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Callable

import numpy as np

from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.errors import BackendLoadError, CapabilityError
from glyphprobe.provenance import model_artifact_receipt
from glyphprobe.records import ForwardResult, GenerationResult, Intervention, TokenizationRecord
from glyphprobe.seed import seed_everything

from .base import Backend


class TransformersBackend(Backend):
    """Raw PyTorch + Hugging Face Transformers backend.

    ``resid_post`` is architecture-agnostic to the extent that a decoder block list
    can be found. The finer sites use conservative submodule-name discovery and are
    always recorded in the receipt; users should verify a new architecture before
    treating those sites as equivalent across model families.
    """

    _BLOCK_PATHS = (
        "model.layers",
        "transformer.h",
        "gpt_neox.layers",
        "model.decoder.layers",
        "decoder.layers",
        "layers",
    )

    def __init__(self, config):
        super().__init__(config)
        self.model: Any = None
        self.tokenizer: Any = None
        self.torch: Any = None
        self.blocks: list[Any] = []
        self.block_path: str | None = None
        self.device: str = "cpu"
        self._d_model: int | None = None
        self.loader_metadata: dict[str, Any] = {}
        self.model_artifact: dict[str, Any] | None = None
        self.model_locator: str | None = None

    @staticmethod
    def _get_path(root: Any, path: str) -> Any | None:
        current = root
        for part in path.split("."):
            if not hasattr(current, part):
                return None
            current = getattr(current, part)
        return current

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
    def _resolve_dtype(torch: Any, name: str, device: str) -> Any | None:
        if name == "auto":
            if device == "cuda":
                return torch.bfloat16
            return None
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
    def _dtype_kwarg_name(transformers_version: str) -> str:
        """Select the public dtype keyword across Transformers major versions."""
        try:
            major = int(transformers_version.split(".", 1)[0])
        except (TypeError, ValueError):
            major = 4
        return "dtype" if major >= 5 else "torch_dtype"

    def load(self) -> None:
        try:
            import torch
            import transformers
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise BackendLoadError(
                "The transformers backend requires `pip install 'glyphprobe[torch]'`."
            ) from exc

        self.torch = torch
        self.device = self._select_device(torch, self.config.device)
        dtype = self._resolve_dtype(torch, self.config.dtype, self.device)
        common = {
            "revision": self.config.revision,
            "trust_remote_code": self.config.trust_remote_code,
            "local_files_only": self.config.local_files_only,
        }
        common = {key: value for key, value in common.items() if value is not None}
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model, **common)
        model_kwargs = dict(common)
        model_kwargs.update(self.config.model_kwargs)
        dtype_kwarg: str | None = None
        if (
            dtype is not None
            and "dtype" not in model_kwargs
            and "torch_dtype" not in model_kwargs
        ):
            dtype_kwarg = self._dtype_kwarg_name(
                str(getattr(transformers, "__version__", "4"))
            )
            model_kwargs[dtype_kwarg] = dtype
        self.model = AutoModelForCausalLM.from_pretrained(self.config.model, **model_kwargs)
        if "device_map" not in model_kwargs:
            self.model.to(self.device)
        self.model.eval()

        artifact_root: Any = None
        if Path(self.config.model).exists():
            artifact_root = Path(self.config.model)
        else:
            try:
                from transformers.utils import cached_file

                cached_config = cached_file(
                    self.config.model,
                    "config.json",
                    revision=self.config.revision,
                    local_files_only=self.config.local_files_only,
                )
                artifact_root = Path(cached_config).parent if cached_config else None
            except Exception:
                artifact_root = None
        if artifact_root is not None:
            if artifact_root.is_file():
                artifact_root = artifact_root.parent
            self.model_artifact = model_artifact_receipt(artifact_root)

        for path in self._BLOCK_PATHS:
            value = self._get_path(self.model, path)
            if value is not None and hasattr(value, "__len__") and len(value) > 0:
                self.blocks = list(value)
                self.block_path = path
                break
        if not self.blocks:
            raise BackendLoadError(
                "Could not discover decoder blocks. Set up a TransformerLens adapter or "
                "extend TransformersBackend._BLOCK_PATHS for this architecture."
            )
        cfg = self.model.config
        commit_hash = getattr(cfg, "_commit_hash", None)
        self.model_locator = (
            f"hf://{self.config.model}@{commit_hash}"
            if not Path(self.config.model).exists() and commit_hash
            else (
                f"local-artifact://{artifact_root.name}#"
                f"{self.model_artifact['manifest_sha256']}"
                if artifact_root is not None and self.model_artifact is not None
                else None
            )
        )
        self._d_model = next(
            (
                int(getattr(cfg, name))
                for name in ("hidden_size", "n_embd", "d_model")
                if getattr(cfg, name, None) is not None
            ),
            None,
        )
        if self.tokenizer.pad_token_id is None and self.tokenizer.eos_token_id is not None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.loader_metadata = {
            "transformers_version": str(getattr(transformers, "__version__", "unknown")),
            "resolved_dtype": str(dtype),
            "dtype_kwarg": dtype_kwarg,
            "model_kwargs": sorted(model_kwargs),
            "local_files_only_requested": self.config.local_files_only,
        }
        self._loaded = True

    @property
    def num_layers(self) -> int:
        return len(self.blocks)

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
            Capability.DETERMINISTIC_FORWARD,
        }
        return CapabilityReport(
            backend="transformers",
            model=self.config.model,
            capabilities={cap: cap in enabled for cap in Capability},
            notes={
                "hook_semantics": (
                    "resid_post is captured at decoder-block output. attn_out/mlp_out use "
                    "architecture-name discovery and require model-family validation."
                ),
                "attention_weights": (
                    "Requested opportunistically; optimized attention implementations may not return them."
                ),
            },
            metadata={
                "num_layers": self.num_layers if self._loaded else None,
                "d_model": self._d_model,
                "block_path": self.block_path,
                "loader_metadata": self.loader_metadata,
            },
        )

    def tokenize(self, text: str) -> TokenizationRecord:
        encoded = self.tokenizer(
            text,
            add_special_tokens=self.config.add_special_tokens,
            return_attention_mask=False,
        )
        ids = [int(value) for value in encoded["input_ids"]]
        tokens = [str(value) for value in self.tokenizer.convert_ids_to_tokens(ids)]
        return TokenizationRecord(
            text=text,
            token_ids=ids,
            tokens=tokens,
            metadata={
                "tokenizer_class": type(self.tokenizer).__name__,
                "vocab_size": int(getattr(self.tokenizer, "vocab_size", len(self.tokenizer))),
            },
        )

    @staticmethod
    def _tensor_from_output(output: Any) -> tuple[Any, Callable[[Any], Any]]:
        if hasattr(output, "shape"):
            return output, lambda value: value
        if isinstance(output, tuple) and output and hasattr(output[0], "shape"):
            return output[0], lambda value: (value, *output[1:])
        if isinstance(output, list) and output and hasattr(output[0], "shape"):
            return output[0], lambda value: [value, *output[1:]]
        raise CapabilityError(f"Cannot identify hidden tensor in module output {type(output)!r}")

    @staticmethod
    def _tensor_from_input(inputs: tuple[Any, ...]) -> tuple[Any, Callable[[Any], tuple[Any, ...]]]:
        if not inputs or not hasattr(inputs[0], "shape"):
            raise CapabilityError("Cannot identify hidden tensor in decoder-block input")
        return inputs[0], lambda value: (value, *inputs[1:])

    def _site_module(self, layer: int, site: str) -> Any:
        block = self.blocks[layer]
        if site in {"resid_post", "resid_pre"}:
            return block
        names = (
            ("self_attn", "attn", "attention")
            if site == "attn_out"
            else ("mlp", "feed_forward", "ffn")
        )
        for name in names:
            if hasattr(block, name):
                return getattr(block, name)
        raise CapabilityError(f"Could not discover {site} module in layer {layer}")

    @staticmethod
    def _position_index(position: str | int, hidden: Any) -> int:
        length = int(hidden.shape[1])
        if isinstance(position, int):
            idx = position if position >= 0 else length + position
        elif position in {"last", "last_nonpad", "anchor"}:
            idx = length - 1
        else:
            raise ValueError(f"Unsupported position: {position}")
        if not 0 <= idx < length:
            raise IndexError(f"Position {idx} outside sequence length {length}")
        return idx

    @contextlib.contextmanager
    def _hooks(
        self,
        *,
        layers: list[int],
        site: str,
        position: str | int,
        intervention: Intervention | None,
        captured: dict[int, np.ndarray] | None,
    ) -> Iterator[None]:
        handles: list[Any] = []
        all_layers = sorted(set(layers + ([intervention.layer] if intervention else [])))
        for layer in all_layers:
            module = self._site_module(layer, site)
            if site == "resid_pre":

                def pre_hook(mod: Any, inputs: tuple[Any, ...], *, layer_idx: int = layer):
                    del mod
                    hidden, rebuild = self._tensor_from_input(inputs)
                    edited = hidden
                    if intervention is not None and intervention.layer == layer_idx:
                        idx = self._position_index(intervention.position, hidden)
                        edited = hidden.clone()
                        vector = self.torch.as_tensor(
                            intervention.vector, device=hidden.device, dtype=hidden.dtype
                        )
                        edited[:, idx, :] = edited[:, idx, :] + vector
                    if captured is not None and layer_idx in layers:
                        idx = self._position_index(position, edited)
                        captured[layer_idx] = (
                            edited[0, idx, :].detach().float().cpu().numpy().copy()
                        )
                    return rebuild(edited)

                handles.append(module.register_forward_pre_hook(pre_hook))
            else:

                def post_hook(
                    mod: Any,
                    inputs: tuple[Any, ...],
                    output: Any,
                    *,
                    layer_idx: int = layer,
                ):
                    del mod, inputs
                    hidden, rebuild = self._tensor_from_output(output)
                    edited = hidden
                    if intervention is not None and intervention.layer == layer_idx:
                        idx = self._position_index(intervention.position, hidden)
                        edited = hidden.clone()
                        vector = self.torch.as_tensor(
                            intervention.vector, device=hidden.device, dtype=hidden.dtype
                        )
                        edited[:, idx, :] = edited[:, idx, :] + vector
                    if captured is not None and layer_idx in layers:
                        idx = self._position_index(position, edited)
                        captured[layer_idx] = (
                            edited[0, idx, :].detach().float().cpu().numpy().copy()
                        )
                    return rebuild(edited) if edited is not hidden else output

                handles.append(module.register_forward_hook(post_hook))
        try:
            yield
        finally:
            for handle in handles:
                handle.remove()

    def _prepare_inputs(self, prompt: str) -> dict[str, Any]:
        encoded = self.tokenizer(
            prompt,
            return_tensors="pt",
            add_special_tokens=self.config.add_special_tokens,
        )
        model_device = next(self.model.parameters()).device
        return {key: value.to(model_device) for key, value in encoded.items()}

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
        capture_layers = capture_layers or []
        for layer in capture_layers:
            if not 0 <= layer < self.num_layers:
                raise IndexError(f"Layer {layer} outside model")
        inputs = self._prepare_inputs(prompt)
        ids = inputs["input_ids"][0].detach().cpu().tolist()
        tokens = [str(value) for value in self.tokenizer.convert_ids_to_tokens(ids)]
        captured: dict[int, np.ndarray] = {}
        if self.torch.cuda.is_available() and str(next(self.model.parameters()).device).startswith("cuda"):
            self.torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        with self.torch.inference_mode(), self._hooks(
            layers=capture_layers,
            site=site,
            position=position,
            intervention=intervention,
            captured=captured,
        ):
            outputs = self.model(
                **inputs,
                use_cache=False,
                output_attentions=return_attentions,
                return_dict=True,
            )
        latency_ms = (time.perf_counter() - start) * 1000.0
        logits_tensor = outputs.logits[0, -1, :]
        logits = logits_tensor.detach().float().cpu().numpy().copy()
        attentions: dict[int, np.ndarray] = {}
        raw_attentions = getattr(outputs, "attentions", None)
        if raw_attentions is not None:
            for layer in capture_layers:
                if layer < len(raw_attentions) and raw_attentions[layer] is not None:
                    attn = raw_attentions[layer][0, :, -1, :]
                    attentions[layer] = attn.detach().float().cpu().numpy().copy()
        peak = None
        if self.torch.cuda.is_available() and str(next(self.model.parameters()).device).startswith("cuda"):
            peak = int(self.torch.cuda.max_memory_allocated())
        return ForwardResult(
            token_ids=[int(value) for value in ids],
            tokens=tokens,
            logits=logits,
            activations=captured,
            attentions=attentions,
            latency_ms=latency_ms,
            peak_memory_bytes=peak,
            metadata={
                "site": site,
                "block_path": self.block_path,
                "intervention_scope": "single full-sequence forward",
            },
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
        seed_everything(seed, deterministic_torch=False)
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        inputs = self._prepare_inputs(full_prompt)
        cfg = self.config.generation.model_dump()
        cfg.update(generation_overrides or {})
        do_sample = cfg.pop("do_sample", None)
        if do_sample is None:
            do_sample = float(cfg.get("temperature", 0.0)) > 0
        if not do_sample:
            cfg.pop("temperature", None)
            cfg.pop("top_p", None)
            cfg.pop("top_k", None)
        cfg.pop("logprobs", None)
        cfg.pop("top_logprobs", None)
        generation_kwargs = {key: value for key, value in cfg.items() if value is not None}
        generation_kwargs["do_sample"] = do_sample
        if self.tokenizer.pad_token_id is not None:
            generation_kwargs.setdefault("pad_token_id", self.tokenizer.pad_token_id)
        prompt_len = int(inputs["input_ids"].shape[1])
        start = time.perf_counter()
        hook_layers: list[int] = []
        if intervention is not None:
            hook_layers = [intervention.layer]
        with self.torch.inference_mode(), self._hooks(
            layers=hook_layers,
            site=intervention.site if intervention else "resid_post",
            position="last_nonpad",
            intervention=intervention,
            captured=None,
        ):
            output = self.model.generate(**inputs, **generation_kwargs)
        latency_ms = (time.perf_counter() - start) * 1000.0
        generated = output[0, prompt_len:].detach().cpu().tolist()
        text = self.tokenizer.decode(generated, skip_special_tokens=True)
        tokens = [str(value) for value in self.tokenizer.convert_ids_to_tokens(generated)]
        return GenerationResult(
            text=text,
            token_ids=[int(value) for value in generated],
            tokens=tokens,
            latency_ms=latency_ms,
            usage={"prompt_tokens": prompt_len, "completion_tokens": len(generated)},
            metadata={
                "intervention_scope": (
                    "hook applied at the final available position on every decode forward"
                    if intervention
                    else "none"
                )
            },
        )

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        cfg = self.model.config if self.model is not None else None
        receipt.update(
            {
                "backend_class": type(self).__name__,
                "model_class": type(self.model).__name__ if self.model is not None else None,
                "tokenizer_class": type(self.tokenizer).__name__ if self.tokenizer is not None else None,
                "block_path": self.block_path,
                "num_layers": self.num_layers if self.blocks else None,
                "d_model": self._d_model,
                "parameter_count": (
                    int(sum(param.numel() for param in self.model.parameters()))
                    if self.model is not None
                    else None
                ),
                "commit_hash": getattr(cfg, "_commit_hash", None) if cfg is not None else None,
                "model_locator": self.model_locator,
                "model_artifact": self.model_artifact,
                "resolved_device": self.device,
                "loader_metadata": self.loader_metadata,
            }
        )
        return receipt
