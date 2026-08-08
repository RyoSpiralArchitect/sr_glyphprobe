"""Injected via PYTHONPATH. Makes transformers>=5.13 tolerate mlx-lm's
string-keyed tokenizer registration (only matters for the MLX path). Harmless
for the transformers backend. Runs with PYTHONNOUSERSITE=1 (Spiralton off).
"""
try:
    from transformers.models.auto import auto_factory

    _orig_register = auto_factory._LazyAutoMapping.register

    def _tolerant_register(self, key, value, exist_ok=False):
        if not hasattr(key, "__module__"):
            self._extra_content[key] = value
            return
        return _orig_register(self, key, value, exist_ok=exist_ok)

    auto_factory._LazyAutoMapping.register = _tolerant_register
except Exception:
    pass
