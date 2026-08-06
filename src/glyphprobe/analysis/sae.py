from __future__ import annotations

from typing import Any

import numpy as np

from glyphprobe.config import SAEConfig
from glyphprobe.errors import BackendLoadError, ConfigurationError


class SAEAnalyzer:
    """Thin SAELens v6 adapter for feature-space pre-stage measurements."""

    def __init__(self, config: SAEConfig, *, model_device: str):
        self.config = config
        self.model_device = model_device
        self.saes: dict[int, Any] = {}
        self.torch: Any = None

    def load(self, layers: list[int]) -> None:
        if not self.config.enabled:
            return
        try:
            import torch
            from sae_lens import SAE
        except ImportError as exc:
            raise BackendLoadError(
                "SAE analysis requires `pip install 'glyphprobe[sae]'`."
            ) from exc
        self.torch = torch
        device = self.model_device if self.config.device == "auto" else self.config.device
        for layer in layers:
            sae_id = self.config.sae_ids.get(layer)
            if sae_id is None:
                raise ConfigurationError(
                    f"No sae.sae_ids entry for resolved layer {layer}; explicit mapping is required"
                )
            self.saes[layer] = SAE.from_pretrained(
                self.config.release,
                sae_id,
                device=device,
            )

    def analyze(self, layer: int, activation: np.ndarray) -> dict[str, Any]:
        if not self.config.enabled:
            return {"enabled": False}
        sae = self.saes[layer]
        device = next(sae.parameters()).device
        tensor = self.torch.as_tensor(activation, dtype=self.torch.float32, device=device)
        if tensor.ndim == 1:
            tensor = tensor[None, :]
        with self.torch.inference_mode():
            features = sae.encode(tensor)
            reconstruction = sae.decode(features)
        values = features[0].detach().float().cpu().numpy()
        recon = reconstruction[0].detach().float().cpu().numpy()
        top_k = min(self.config.top_k_features, values.size)
        ids = np.argpartition(values, -top_k)[-top_k:]
        ids = ids[np.argsort(values[ids])[::-1]]
        error = recon - np.asarray(activation, dtype=np.float32)
        variance = float(np.var(activation))
        return {
            "enabled": True,
            "feature_l0": int(np.count_nonzero(values)),
            "feature_l1": float(np.abs(values).sum()),
            "feature_l2": float(np.linalg.norm(values)),
            "reconstruction_mse": float(np.mean(error**2)),
            "reconstruction_explained_variance": float(
                1.0 - np.var(error) / max(variance, 1e-12)
            ),
            "top_feature_ids": [int(value) for value in ids],
            "top_feature_values": [float(values[value]) for value in ids],
        }
