from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from glyphprobe.backends.lens import TransformerLensBackend
from glyphprobe.backends.mlx_backend import MLXBackend
from glyphprobe.backends.transformers_backend import TransformersBackend
from glyphprobe.config import BackendConfig
from glyphprobe.records import Intervention


class FakeLensModel:
    def __init__(self) -> None:
        self.cfg = SimpleNamespace(n_layers=2, d_model=4, model_name="fake-lens")
        self.tokenizer = SimpleNamespace(
            convert_ids_to_tokens=lambda ids: [f"t{i}" for i in ids],
            decode=lambda ids, skip_special_tokens=True: " ".join(f"t{i}" for i in ids),
        )

    def eval(self) -> None:
        return None

    def to_tokens(self, text: str, prepend_bos: bool = True) -> torch.Tensor:
        del text, prepend_bos
        return torch.tensor([[1, 2]], dtype=torch.long)

    def to_str_tokens(self, tokens: torch.Tensor) -> list[str]:
        return [f"t{int(value)}" for value in tokens[0]]

    def run_with_hooks(self, tokens: torch.Tensor, fwd_hooks: list[tuple[str, object]]):
        del tokens
        hidden = torch.tensor(
            [[[0.0, 0.0, 0.0, 0.0], [1.0, 2.0, 3.0, 4.0]]],
            dtype=torch.float32,
        )
        hooks = dict(fwd_hooks)
        for layer in range(2):
            hidden = hidden + float(layer + 1)
            name = f"blocks.{layer}.hook_resid_post"
            if name in hooks:
                hidden = hooks[name](hidden, SimpleNamespace(name=name))
        weights = torch.arange(20, dtype=torch.float32).reshape(4, 5) / 10.0
        return hidden @ weights


class FakeTokenizer:
    pad_token_id = 0
    eos_token_id = 0
    vocab_size = 8

    def __len__(self) -> int:
        return self.vocab_size

    def __call__(
        self,
        text: str,
        *,
        return_tensors: str | None = None,
        add_special_tokens: bool = True,
        return_attention_mask: bool = True,
    ):
        del text, add_special_tokens, return_attention_mask
        ids = [1, 2]
        if return_tensors == "pt":
            return {
                "input_ids": torch.tensor([ids], dtype=torch.long),
                "attention_mask": torch.ones((1, len(ids)), dtype=torch.long),
            }
        return {"input_ids": ids}

    def convert_ids_to_tokens(self, ids):
        return [f"t{int(value)}" for value in ids]

    def decode(self, ids, skip_special_tokens: bool = True):
        del skip_special_tokens
        return " ".join(f"t{int(value)}" for value in ids)


class ToyBlock(torch.nn.Module):
    def __init__(self, amount: float) -> None:
        super().__init__()
        self.amount = amount
        self.self_attn = torch.nn.Identity()
        self.mlp = torch.nn.Identity()

    def forward(self, hidden: torch.Tensor, **kwargs) -> torch.Tensor:
        del kwargs
        return hidden + self.amount


class ToyHFModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embedding = torch.nn.Embedding(8, 4)
        self.transformer = SimpleNamespace(
            h=torch.nn.ModuleList([ToyBlock(0.5), ToyBlock(1.0)])
        )
        self.blocks = self.transformer.h
        self.head = torch.nn.Linear(4, 8, bias=False)
        self.config = SimpleNamespace(
            hidden_size=4,
            _commit_hash="fake",
        )
        with torch.no_grad():
            self.embedding.weight.copy_(
                torch.arange(32, dtype=torch.float32).reshape(8, 4) / 32.0
            )
            self.head.weight.copy_(
                torch.arange(32, dtype=torch.float32).reshape(8, 4) / 16.0
            )

    def forward(self, input_ids, attention_mask=None, **kwargs):
        del attention_mask, kwargs
        hidden = self.embedding(input_ids)
        for block in self.blocks:
            hidden = block(hidden)
        return SimpleNamespace(logits=self.head(hidden), attentions=None)


def test_transformer_lens_forward_hook_changes_logits() -> None:
    backend = TransformerLensBackend(
        BackendConfig(kind="lens", model="fake", device="cpu", dtype="float32")
    )
    backend.torch = torch
    backend.device = "cpu"
    backend.model = FakeLensModel()
    backend.loader_path = "fake"
    backend._n_layers = 2
    backend._d_model = 4
    backend._loaded = True

    baseline = backend.forward("x", capture_layers=[0, 1])
    changed = backend.forward(
        "x",
        capture_layers=[0, 1],
        intervention=Intervention(
            layer=0,
            vector=np.array([0.5, -0.5, 0.25, -0.25], dtype=np.float32),
        ),
    )
    assert set(changed.activations) == {0, 1}
    assert not np.allclose(baseline.activations[0], changed.activations[0])
    assert not np.allclose(baseline.logits, changed.logits)


def test_raw_transformers_resid_post_hook_changes_logits() -> None:
    backend = TransformersBackend(
        BackendConfig(kind="transformers", model="fake", device="cpu", dtype="float32")
    )
    backend.torch = torch
    backend.device = "cpu"
    backend.tokenizer = FakeTokenizer()
    backend.model = ToyHFModel()
    backend.blocks = list(backend.model.blocks)
    backend.block_path = "transformer.h"
    backend._d_model = 4
    backend._loaded = True

    baseline = backend.forward("x", capture_layers=[0, 1], site="resid_post")
    changed = backend.forward(
        "x",
        capture_layers=[0, 1],
        site="resid_post",
        intervention=Intervention(
            layer=0,
            vector=np.array([0.5, -0.5, 0.25, -0.25], dtype=np.float32),
        ),
    )
    assert set(changed.activations) == {0, 1}
    assert not np.allclose(baseline.activations[0], changed.activations[0])
    assert not np.allclose(baseline.logits, changed.logits)


def test_mlx_numpy_bridge_casts_before_numpy_conversion() -> None:
    float32_sentinel = object()

    class RejectDirectNumpyConversion:
        def __init__(self) -> None:
            self.requested_dtype = None

        def astype(self, dtype):
            self.requested_dtype = dtype
            return np.array([-1.5, 0.0, 2.25], dtype=np.float32)

        def __array__(self, dtype=None, copy=None):
            del dtype, copy
            raise RuntimeError("the source array must be cast before NumPy conversion")

    source = RejectDirectNumpyConversion()
    backend = MLXBackend(
        BackendConfig(kind="mlx", model="fake", device="cpu", dtype="bfloat16")
    )
    backend.mx = SimpleNamespace(float32=float32_sentinel, eval=lambda *values: None)

    converted = backend._to_numpy_float32(source)

    assert source.requested_dtype is float32_sentinel
    assert converted.dtype == np.float32
    np.testing.assert_array_equal(converted, [-1.5, 0.0, 2.25])


def test_mlx_numpy_bridge_handles_real_bfloat16_and_float32() -> None:
    mx = pytest.importorskip("mlx.core")
    backend = MLXBackend(
        BackendConfig(kind="mlx", model="fake", device="cpu", dtype="bfloat16")
    )
    backend.mx = mx

    expected = np.array([-1.5, 0.0, 2.25], dtype=np.float32)
    for source_dtype in (mx.bfloat16, mx.float32):
        source = mx.array(expected, dtype=source_dtype)
        converted = backend._to_numpy_float32(source)

        assert converted.dtype == np.float32
        np.testing.assert_array_equal(converted, expected)
