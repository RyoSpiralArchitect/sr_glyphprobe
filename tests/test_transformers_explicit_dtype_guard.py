from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
import torch

from glyphprobe.backends.transformers_backend import TransformersBackend
from glyphprobe.config import BackendConfig
from glyphprobe.errors import BackendLoadError


class _FakeTokenizer:
    pad_token_id = None
    eos_token_id = 1
    eos_token = "<eos>"
    pad_token = None


class _FakeModel(torch.nn.Module):
    def __init__(
        self, parameter_specs: list[tuple[tuple[int, ...], torch.dtype]]
    ) -> None:
        super().__init__()
        for index, (shape, dtype) in enumerate(parameter_specs):
            self.register_parameter(
                f"weight_{index}",
                torch.nn.Parameter(torch.zeros(shape, dtype=dtype)),
            )
        self.layers = torch.nn.ModuleList([torch.nn.Identity()])
        self.config = SimpleNamespace(hidden_size=4, _commit_hash="fake-commit")
        self.forward_calls = 0

    def forward(self, *args, **kwargs):
        del args, kwargs
        self.forward_calls += 1
        raise AssertionError("the dtype guard must run before any forward")


def _install_fake_transformers(
    monkeypatch: pytest.MonkeyPatch,
    parameter_specs: list[tuple[tuple[int, ...], torch.dtype]],
) -> tuple[dict[str, object], list[_FakeModel]]:
    model_kwargs: dict[str, object] = {}
    models: list[_FakeModel] = []

    class AutoTokenizer:
        @staticmethod
        def from_pretrained(model: str, **kwargs):
            del model, kwargs
            return _FakeTokenizer()

    class AutoModelForCausalLM:
        @staticmethod
        def from_pretrained(model: str, **kwargs):
            del model
            model_kwargs.update(kwargs)
            loaded = _FakeModel(parameter_specs)
            models.append(loaded)
            return loaded

    fake_transformers = ModuleType("transformers")
    fake_transformers.__version__ = "5.0.0"
    fake_transformers.AutoTokenizer = AutoTokenizer
    fake_transformers.AutoModelForCausalLM = AutoModelForCausalLM
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)
    return model_kwargs, models


def _backend(dtype: str) -> TransformersBackend:
    return TransformersBackend(
        BackendConfig(
            kind="transformers",
            model="fake-dtype-guard-model",
            device="cpu",
            dtype=dtype,
            local_files_only=True,
        )
    )


def test_explicit_dtype_guard_accepts_exact_parameter_dtype(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_kwargs, models = _install_fake_transformers(
        monkeypatch,
        [((2, 2), torch.float32), ((3,), torch.float32)],
    )
    backend = _backend("float32")

    backend.load()

    assert backend._loaded is True
    assert model_kwargs["dtype"] is torch.float32
    assert models[0].forward_calls == 0


def test_explicit_dtype_guard_rejects_mixed_parameter_dtypes_with_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, models = _install_fake_transformers(
        monkeypatch,
        [((2, 2), torch.float32), ((3,), torch.float16)],
    )
    backend = _backend("float32")

    with pytest.raises(BackendLoadError) as exc_info:
        backend.load()

    message = str(exc_info.value)
    assert "failed before first forward" in message
    assert "requested_dtype='float32'" in message
    assert "resolved_dtype='torch.float32'" in message
    assert "'torch.float16': 1" in message
    assert "'torch.float32': 1" in message
    assert "unexpected_parameter_tensor_count=1" in message
    assert "unexpected_parameter_element_count=3" in message
    assert models[0].forward_calls == 0
    assert backend._loaded is False


def test_auto_dtype_preserves_loader_selected_parameter_dtype(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model_kwargs, models = _install_fake_transformers(
        monkeypatch,
        [((2, 2), torch.float16)],
    )
    backend = _backend("auto")

    backend.load()

    assert backend._loaded is True
    assert "dtype" not in model_kwargs
    assert "torch_dtype" not in model_kwargs
    assert next(backend.model.parameters()).dtype is torch.float16
    assert models[0].forward_calls == 0
