from __future__ import annotations

from glyphprobe.config import BackendConfig
from glyphprobe.errors import ConfigurationError

from .base import Backend


_DEFAULT_URLS = {
    "vllm": "http://127.0.0.1:8000/v1",
    "llamacpp": "http://127.0.0.1:8080/v1",
    "ollama": "http://127.0.0.1:11434/v1",
    "lmstudio": "http://127.0.0.1:1234/v1",
}


def default_base_url(kind: str) -> str | None:
    return _DEFAULT_URLS.get(kind)


def create_backend(config: BackendConfig) -> Backend:
    if config.kind == "mock":
        from .mock import MockBackend

        return MockBackend(config)
    if config.kind == "transformers":
        from .transformers_backend import TransformersBackend

        return TransformersBackend(config)
    if config.kind == "lens":
        from .lens import TransformerLensBackend

        return TransformerLensBackend(config)
    if config.kind == "mlx":
        from .mlx_backend import MLXBackend

        return MLXBackend(config)
    if config.kind in {"vllm", "llamacpp", "ollama", "lmstudio", "openai"}:
        from .openai_compat import OpenAICompatibleBackend

        if config.base_url is None and config.kind != "openai":
            config = config.model_copy(update={"base_url": default_base_url(config.kind)})
        return OpenAICompatibleBackend(config)
    raise ConfigurationError(f"Unknown backend kind: {config.kind}")
