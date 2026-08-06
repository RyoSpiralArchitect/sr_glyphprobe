from __future__ import annotations

import contextlib
import importlib.metadata
import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from glyphprobe.capabilities import Capability, CapabilityReport
from glyphprobe.errors import BackendLoadError, CapabilityError
from glyphprobe.io import sha256_file
from glyphprobe.provenance import (
    implementation_receipt,
    model_artifact_receipt,
    stable_model_identity,
)
from glyphprobe.records import ForwardResult, Intervention, TokenizationRecord

from .base import Backend


class _ResidualBlockProxy:
    """Temporarily capture or edit one MLX decoder-block output.

    MLX-LM model calls are ordinary Python module calls. Replacing selected entries
    in the decoder-block list lets GlyphProbe preserve the existing ``resid_post``
    contract without modifying MLX-LM or copying model-family forward functions.
    Captures remain lazy MLX arrays until the complete forward graph is evaluated.
    """

    def __init__(
        self,
        block: Any,
        *,
        mx: Any,
        layer: int,
        capture_position: str | int,
        intervention: Intervention | None,
        captured: dict[int, Any],
        position_index: Any,
    ) -> None:
        self._block = block
        self._mx = mx
        self._layer = layer
        self._capture_position = capture_position
        self._intervention = intervention
        self._captured = captured
        self._position_index = position_index

    def __getattr__(self, name: str) -> Any:
        return getattr(self._block, name)

    def __call__(self, hidden: Any, *args: Any, **kwargs: Any) -> Any:
        output = self._block(hidden, *args, **kwargs)
        if not hasattr(output, "shape") or len(output.shape) != 3:
            raise CapabilityError(
                "MLX resid_post requires a decoder block returning [batch, sequence, width]"
            )

        edited = output
        if self._intervention is not None and self._intervention.layer == self._layer:
            idx = self._position_index(self._intervention.position, output)
            vector = self._mx.array(
                np.asarray(self._intervention.vector, dtype=np.float32),
                dtype=output.dtype,
            )
            if int(vector.shape[0]) != int(output.shape[-1]):
                raise ValueError(
                    f"Intervention width {vector.shape[0]} does not match model width "
                    f"{output.shape[-1]}"
                )
            edited = output.at[:, idx, :].add(vector)

        capture_idx = self._position_index(self._capture_position, edited)
        self._captured[self._layer] = edited[0, capture_idx, :]
        return edited


class MLXBackend(Backend):
    """Apple-silicon MLX-LM backend for full-sequence ``resid_post`` probes.

    Version 0.1 deliberately exposes only the site that can be defined uniformly
    across the validated GPT-2 and Llama-style MLX-LM decoder blocks. Finer sites
    must receive their own model-family parity receipt before being added.
    """

    _BLOCK_PATHS = ("model.h", "model.layers", "layers")

    def __init__(self, config: Any):
        super().__init__(config)
        self.mx: Any = None
        self.model: Any = None
        self.tokenizer: Any = None
        self.blocks: list[Any] = []
        self.block_path: str | None = None
        self.resolved_model_path: str | None = None
        self.resolved_device: str | None = None
        self.resolved_dtype: str | None = None
        self.model_config: dict[str, Any] = {}
        self.loader_metadata: dict[str, Any] = {}
        self.model_artifact: dict[str, Any] | None = None
        self.model_locator: str | None = None
        self.parity_validation: dict[str, Any] = {
            "validated": False,
            "reason": "no validation receipt was supplied",
        }
        self._parity_probe_mode = False
        self._d_model: int | None = None
        self._parameter_count: int | None = None
        self._previous_device: Any = None

    @staticmethod
    def _get_path(root: Any, path: str) -> Any | None:
        current = root
        for part in path.split("."):
            if not hasattr(current, part):
                return None
            current = getattr(current, part)
        return current

    @staticmethod
    def _package_version(distribution: str) -> str | None:
        try:
            return importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            return None

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

    def _to_numpy_float32(self, value: Any) -> np.ndarray:
        """Materialize an MLX array through an on-device float32 cast."""

        float32_value = value.astype(self.mx.float32)
        self.mx.eval(float32_value)
        return np.array(float32_value, dtype=np.float32, copy=True)

    def _resolve_local_model(self) -> str:
        model = self.config.model
        if Path(model).exists():
            return model
        try:
            from huggingface_hub import snapshot_download

            return str(
                snapshot_download(
                    model,
                    revision=self.config.revision,
                    local_files_only=self.config.local_files_only,
                    allow_patterns=[
                        "*.json",
                        "model*.safetensors",
                        "*.py",
                        "tokenizer.model",
                        "*.tiktoken",
                        "tiktoken.model",
                        "*.txt",
                        "*.jsonl",
                        "*.jinja",
                    ],
                )
            )
        except Exception as exc:
            raise BackendLoadError(
                f"MLX model {model!r} is not available in the local Hugging Face cache"
            ) from exc

    def _select_device(self) -> None:
        self._previous_device = self.mx.default_device()
        requested = self.config.device
        if requested in {"auto", "gpu", "mps"}:
            if not self.mx.metal.is_available():
                raise BackendLoadError("MLX Metal GPU is unavailable on this host")
            self.mx.set_default_device(self.mx.gpu)
        elif requested == "cpu":
            self.mx.set_default_device(self.mx.cpu)
        else:
            raise BackendLoadError(
                "MLX device must be one of auto, gpu, mps, or cpu"
            )
        self.resolved_device = str(self.mx.default_device())

    def _apply_dtype(self) -> None:
        from mlx.utils import tree_flatten

        name = self.config.dtype.lower()
        is_quantized = bool(
            self.model_config.get("quantization")
            or self.model_config.get("quantization_config")
        )
        if is_quantized and name != "auto":
            raise BackendLoadError(
                "Explicit dtype conversion of an MLX quantized model is not validated; "
                "use dtype=auto and a separate parity receipt"
            )
        if name == "auto":
            leaves = [
                value
                for _, value in tree_flatten(self.model.parameters())
                if hasattr(value, "dtype")
            ]
            self.resolved_dtype = str(leaves[0].dtype) if leaves else "unknown"
            return
        mapping = {
            "float32": self.mx.float32,
            "fp32": self.mx.float32,
            "float16": self.mx.float16,
            "fp16": self.mx.float16,
            "bfloat16": self.mx.bfloat16,
            "bf16": self.mx.bfloat16,
        }
        if name not in mapping:
            raise BackendLoadError(f"Unsupported MLX dtype: {self.config.dtype}")
        dtype = mapping[name]
        self.model.set_dtype(dtype)
        self.mx.eval(self.model.parameters())
        self.resolved_dtype = str(dtype)

    @staticmethod
    def _normalize_intervention_layers(value: Any, num_layers: int) -> list[int]:
        if not isinstance(value, list) or not value:
            return []
        if any(
            not isinstance(layer, int)
            or isinstance(layer, bool)
            or not 0 <= layer < num_layers
            for layer in value
        ):
            return []
        if len(set(value)) != len(value):
            return []
        return sorted(value)

    def _validate_parity_receipt(self) -> None:
        receipt_path = self.config.validation_receipt
        expected_sha256 = self.config.validation_receipt_sha256
        if receipt_path is None or expected_sha256 is None:
            return
        receipt_path = Path(receipt_path)
        actual_sha256 = sha256_file(receipt_path)
        if actual_sha256 != expected_sha256.lower():
            raise BackendLoadError(
                "MLX parity receipt SHA-256 does not match backend.validation_receipt_sha256"
            )
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendLoadError(f"Could not read MLX parity receipt: {receipt_path}") from exc

        current_implementation = implementation_receipt()
        current_identity = stable_model_identity(self.model_receipt())
        validated_intervention_layers = self._normalize_intervention_layers(
            receipt.get("intervention_layers"), self.num_layers
        )
        comparisons = {
            "status": receipt.get("status") == "validated_mlx_selected",
            "model": receipt.get("model") == self.config.model,
            "revision": receipt.get("revision") == self.config.revision,
            "dtype": receipt.get("dtype") == self.config.dtype,
            "site": receipt.get("site") == "resid_post",
            "implementation": (
                receipt.get("implementation", {}).get("source_tree_sha256")
                == current_implementation["source_tree_sha256"]
            ),
            "model_identity": (
                receipt.get("mlx_model_identity_sha256") == current_identity["sha256"]
            ),
            "parity_gate": receipt.get("parity", {}).get("pass") is True,
            "speed_gate": receipt.get("benchmark", {}).get("speed_gate", {}).get("pass")
            is True,
            "intervention_layers": bool(validated_intervention_layers),
        }
        failed = [name for name, passed in comparisons.items() if not passed]
        if failed:
            raise BackendLoadError(
                "MLX parity receipt is not valid for this implementation/model cell: "
                + ", ".join(failed)
            )
        self.parity_validation = {
            "validated": True,
            "receipt_sha256": actual_sha256,
            "receipt_status": receipt["status"],
            "implementation_sha256": current_implementation["source_tree_sha256"],
            "model_identity_sha256": current_identity["sha256"],
            "validated_site": receipt["site"],
            "validated_intervention_layers": validated_intervention_layers,
            "validated_prompt_token_counts": receipt.get("benchmark", {}).get(
                "prompt_token_counts", []
            ),
        }

    def _require_validated_intervention_layer(self, layer: int) -> None:
        if self._parity_probe_mode:
            return
        if not self.parity_validation.get("validated", False):
            raise CapabilityError(
                "MLX activation intervention requires a validated, SHA-pinned parity receipt"
            )
        validated_layers = self.parity_validation.get(
            "validated_intervention_layers", []
        )
        if not isinstance(validated_layers, list) or layer not in validated_layers:
            raise CapabilityError(
                f"MLX activation intervention at layer {layer} is outside the "
                f"validated receipt scope {validated_layers!r}"
            )

    def load(self) -> None:
        started = time.perf_counter()
        if self.config.model_kwargs:
            raise BackendLoadError(
                "MLX backend does not yet accept backend.model_kwargs; use a sealed "
                "model artifact and explicit config fields"
            )
        try:
            import mlx.core as mx
            import mlx_lm
            from mlx_lm.utils import get_total_parameters
        except ImportError as exc:
            raise BackendLoadError(
                "The MLX backend requires `pip install 'glyphprobe[mlx]'` on Apple silicon."
            ) from exc

        self.mx = mx
        self._select_device()
        model_path = self._resolve_local_model()
        config_path = Path(model_path) / "config.json"
        try:
            raw_config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BackendLoadError(f"Could not inspect MLX model config: {config_path}") from exc
        if raw_config.get("model_file") and not self.config.trust_remote_code:
            raise BackendLoadError(
                "MLX model config requests custom Python code; set trust_remote_code=true "
                "only after auditing the sealed model revision"
            )
        try:
            self.model, self.tokenizer, self.model_config = mlx_lm.load(
                model_path,
                revision=None if Path(model_path).exists() else self.config.revision,
                return_config=True,
            )
        except Exception as exc:
            raise BackendLoadError(
                f"Could not load MLX-LM model {self.config.model!r}: {exc}"
            ) from exc

        self.resolved_model_path = (
            str(Path(model_path).resolve()) if Path(model_path).exists() else model_path
        )
        artifact_root = Path(model_path)
        if artifact_root.is_file():
            artifact_root = artifact_root.parent
        self.model_artifact = model_artifact_receipt(artifact_root)
        resolved = Path(model_path)
        commit_hash = (
            resolved.name if resolved.parent.name == "snapshots" else self.config.revision
        )
        self.model_locator = (
            f"hf://{self.config.model}@{commit_hash}"
            if not Path(self.config.model).exists() and commit_hash
            else f"local-artifact://{artifact_root.name}#{self.model_artifact['manifest_sha256']}"
        )
        self._apply_dtype()
        for path in self._BLOCK_PATHS:
            value = self._get_path(self.model, path)
            if value is not None and hasattr(value, "__len__") and len(value) > 0:
                self.blocks = value
                self.block_path = path
                break
        if not self.blocks:
            raise BackendLoadError(
                "Could not discover MLX-LM decoder blocks. This model family needs an adapter receipt."
            )
        self._d_model = next(
            (
                int(self.model_config[name])
                for name in ("hidden_size", "n_embd", "d_model")
                if self.model_config.get(name) is not None
            ),
            None,
        )
        self._parameter_count = int(get_total_parameters(self.model))
        self.loader_metadata = {
            "mlx_version": self._package_version("mlx"),
            "mlx_lm_version": self._package_version("mlx-lm"),
            "model_type": self.model_config.get("model_type"),
            "quantization": self.model_config.get("quantization"),
            "local_files_only_requested": self.config.local_files_only,
            "load_latency_ms": (time.perf_counter() - started) * 1000.0,
        }
        self._loaded = True
        self._validate_parity_receipt()

    @property
    def num_layers(self) -> int:
        return len(self.blocks)

    @property
    def model_dim(self) -> int | None:
        return self._d_model

    def capabilities(self) -> CapabilityReport:
        enabled = {
            Capability.TOKENIZE,
            Capability.FORWARD_LOGITS,
            Capability.HIDDEN_STATES,
            Capability.ACTIVATION_CACHE,
            Capability.DETERMINISTIC_FORWARD,
        }
        validated_layers = self.parity_validation.get("validated_intervention_layers")
        if (
            self.parity_validation.get("validated") is True
            and isinstance(validated_layers, list)
            and bool(validated_layers)
        ):
            enabled.add(Capability.ACTIVATION_PATCH)
        return CapabilityReport(
            backend="mlx",
            model=self.config.model,
            capabilities={cap: cap in enabled for cap in Capability},
            notes={
                "hook_semantics": (
                    "resid_post is the edited decoder-block output. Other sites are rejected "
                    "until model-family parity receipts exist."
                ),
                "validation_scope": (
                    "Activation patching is advertised only after a pinned same-model receipt "
                    "passes tokenizer, activation, logit, zero-hook, intervention, and speed gates."
                ),
                "concurrency": (
                    "Selected decoder blocks are temporarily proxied; one backend instance "
                    "must not execute concurrent forward calls."
                ),
            },
            metadata={
                "num_layers": self.num_layers if self._loaded else None,
                "d_model": self._d_model,
                "block_path": self.block_path,
                "supported_sites": ["resid_post"],
                "loader_metadata": self.loader_metadata,
                "parity_validation": self.parity_validation,
            },
        )

    def tokenize(self, text: str) -> TokenizationRecord:
        ids = [
            int(value)
            for value in self.tokenizer.encode(
                text,
                add_special_tokens=self.config.add_special_tokens,
            )
        ]
        tokens = [str(value) for value in self.tokenizer.convert_ids_to_tokens(ids)]
        raw_tokenizer = getattr(self.tokenizer, "_tokenizer", self.tokenizer)
        vocab_size = getattr(self.tokenizer, "vocab_size", None)
        if vocab_size is None:
            vocab_size = len(raw_tokenizer)
        return TokenizationRecord(
            text=text,
            token_ids=ids,
            tokens=tokens,
            metadata={
                "tokenizer_class": type(raw_tokenizer).__name__,
                "vocab_size": int(vocab_size),
            },
        )

    @contextlib.contextmanager
    def _proxies(
        self,
        *,
        layers: list[int],
        position: str | int,
        intervention: Intervention | None,
        captured: dict[int, Any],
    ) -> Iterator[None]:
        originals: dict[int, Any] = {}
        all_layers = sorted(set(layers + ([intervention.layer] if intervention else [])))
        for layer in all_layers:
            originals[layer] = self.blocks[layer]
            self.blocks[layer] = _ResidualBlockProxy(
                originals[layer],
                mx=self.mx,
                layer=layer,
                capture_position=position,
                intervention=intervention,
                captured=captured,
                position_index=self._position_index,
            )
        try:
            yield
        finally:
            for layer, block in originals.items():
                self.blocks[layer] = block

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
        if site != "resid_post":
            raise CapabilityError(
                f"MLX backend currently supports only resid_post, not {site!r}"
            )
        if return_attentions:
            raise CapabilityError("MLX backend does not expose attention weights")
        capture_layers = capture_layers or []
        all_layers = set(capture_layers)
        if intervention is not None:
            self._require_validated_intervention_layer(intervention.layer)
            if intervention.site != site:
                raise CapabilityError(
                    f"Intervention site {intervention.site!r} does not match forward site {site!r}"
                )
            all_layers.add(intervention.layer)
        for layer in all_layers:
            if not 0 <= layer < self.num_layers:
                raise IndexError(f"Layer {layer} outside model")

        tokenized = self.tokenize(prompt)
        if not tokenized.token_ids:
            raise ValueError("MLX backend cannot forward an empty token sequence")
        inputs = self.mx.array([tokenized.token_ids], dtype=self.mx.int32)
        captured_lazy: dict[int, Any] = {}
        self.mx.reset_peak_memory()
        started = time.perf_counter()
        with self._proxies(
            layers=capture_layers,
            position=position,
            intervention=intervention,
            captured=captured_lazy,
        ):
            logits_all = self.model(inputs)
            self.mx.eval(logits_all, *captured_lazy.values())
        latency_ms = (time.perf_counter() - started) * 1000.0

        logits = self._to_numpy_float32(logits_all[0, -1, :])
        captured = {
            layer: self._to_numpy_float32(value)
            for layer, value in captured_lazy.items()
            if layer in capture_layers
        }
        return ForwardResult(
            token_ids=tokenized.token_ids,
            tokens=tokenized.tokens,
            logits=logits,
            activations=captured,
            latency_ms=latency_ms,
            peak_memory_bytes=int(self.mx.get_peak_memory()),
            metadata={
                "site": site,
                "block_path": self.block_path,
                "intervention_scope": "single full-sequence forward",
                "execution": "mlx-evaluated",
            },
        )

    def close(self) -> None:
        self.blocks = []
        self.model = None
        self.tokenizer = None
        if self.mx is not None:
            self.mx.clear_cache()
            if self._previous_device is not None:
                self.mx.set_default_device(self._previous_device)

    def model_receipt(self) -> dict[str, Any]:
        receipt = super().model_receipt()
        resolved = Path(self.resolved_model_path) if self.resolved_model_path else None
        commit_hash = None
        if resolved is not None and resolved.parent.name == "snapshots":
            commit_hash = resolved.name
        receipt.update(
            {
                "backend_class": type(self).__name__,
                "model_class": type(self.model).__name__ if self.model is not None else None,
                "tokenizer_class": (
                    type(getattr(self.tokenizer, "_tokenizer", self.tokenizer)).__name__
                    if self.tokenizer is not None
                    else None
                ),
                "block_path": self.block_path,
                "num_layers": self.num_layers if self.blocks else None,
                "d_model": self._d_model,
                "parameter_count": self._parameter_count,
                "commit_hash": commit_hash,
                "model_locator": self.model_locator,
                "model_artifact": self.model_artifact,
                "resolved_device": self.resolved_device,
                "resolved_dtype": self.resolved_dtype,
                "supported_sites": ["resid_post"],
                "loader_metadata": self.loader_metadata,
                "parity_validation": self.parity_validation,
            }
        )
        return receipt
