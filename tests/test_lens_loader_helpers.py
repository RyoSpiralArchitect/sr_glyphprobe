from __future__ import annotations

from glyphprobe.backends.lens import TransformerLensBackend


def test_loader_kwarg_filtering() -> None:
    def explicit(model_name: str, device=None, dtype=None):
        del model_name, device, dtype

    accepted, rejected = TransformerLensBackend._accepted_kwargs(
        explicit,
        {"device": "cpu", "dtype": "float32", "revision": "main"},
    )
    assert accepted == {"device": "cpu", "dtype": "float32"}
    assert rejected == ["revision"]

    def variadic(model_name: str, **kwargs):
        del model_name, kwargs

    accepted, rejected = TransformerLensBackend._accepted_kwargs(
        variadic,
        {"device": "cpu", "revision": "main"},
    )
    assert accepted == {"device": "cpu", "revision": "main"}
    assert rejected == []


def test_transformers_dtype_kwarg_tracks_major_version() -> None:
    from glyphprobe.backends.transformers_backend import TransformersBackend

    assert TransformersBackend._dtype_kwarg_name("4.48.3") == "torch_dtype"
    assert TransformersBackend._dtype_kwarg_name("5.0.0") == "dtype"
    assert TransformersBackend._dtype_kwarg_name("unknown") == "torch_dtype"
