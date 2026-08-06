from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from glyphprobe.backends.registry import create_backend, default_base_url
from glyphprobe.capabilities import Capability
from glyphprobe.config import BackendConfig, load_experiment_config, resolve_layers
from glyphprobe.errors import CapabilityError
from glyphprobe.records import Intervention


def _write_inputs(root: Path) -> Path:
    (root / "panel.yaml").write_text(
        yaml.safe_dump(
            {
                "items": [
                    {"id": "a", "glyph": "🟤", "factors": {"shape": "circle"}},
                    {"id": "b", "glyph": "🟫", "factors": {"shape": "square"}},
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (root / "wrappers.jsonl").write_text(
        json.dumps({"id": "w0", "template": "Mark: {emoji}\\nAnchor:"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    (root / "targets.jsonl").write_text(
        json.dumps({"id": "t0", "prompt": "Continue."}) + "\n",
        encoding="utf-8",
    )
    config = {
        "mode": "internal",
        "backend": {"kind": "mock", "model": "glyphprobe/mock-64d"},
        "panel": {"file": "panel.yaml"},
        "source": {"wrappers_file": "wrappers.jsonl"},
        "targets": {"cases_file": "targets.jsonl"},
    }
    path = root / "config.yaml"
    path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    return path


def test_config_resolution_and_overrides(tmp_path: Path) -> None:
    path = _write_inputs(tmp_path)
    cfg, inputs = load_experiment_config(
        path,
        overrides=["run.seeds=[7,11]", "capture.layers=[0.0,0.5,1.0]"],
    )
    assert cfg.run.seeds == [7, 11]
    assert [item.glyph for item in inputs.panel_items] == ["🟤", "🟫"]
    assert resolve_layers(cfg.capture.layers, 8) == [0, 4, 7]


def test_remote_backend_defaults_and_does_not_claim_patching() -> None:
    backend = create_backend(BackendConfig(kind="ollama", model="qwen", base_url=None))
    assert backend.config.base_url == default_base_url("ollama")
    report = backend.capabilities()
    plain = report.as_plain_dict()["capabilities"]
    assert plain["activation_patch"] is False
    assert plain["generate"] is True


def test_mlx_backend_requires_pinned_receipt_before_claiming_activation_patch() -> None:
    backend = create_backend(
        BackendConfig(kind="mlx", model="openai-community/gpt2", dtype="float32")
    )
    report = backend.capabilities()
    assert report.supports(
        Capability.TOKENIZE,
        Capability.FORWARD_LOGITS,
        Capability.HIDDEN_STATES,
    )
    assert report.supports(Capability.ACTIVATION_PATCH) is False
    assert report.supports(Capability.GENERATE) is False
    assert report.metadata["supported_sites"] == ["resid_post"]

    backend.parity_validation = {"validated": True}
    assert backend.capabilities().supports(Capability.ACTIVATION_PATCH) is False

    backend.parity_validation = {
        "validated": True,
        "validated_intervention_layers": [2, 4],
    }
    assert backend.capabilities().supports(Capability.ACTIVATION_PATCH)


def test_mlx_intervention_is_limited_to_receipt_validated_layers() -> None:
    backend = create_backend(
        BackendConfig(kind="mlx", model="openai-community/gpt2", dtype="float32")
    )
    backend.blocks = [object()] * 6
    backend.parity_validation = {
        "validated": True,
        "validated_intervention_layers": [2, 4],
    }

    backend._require_validated_intervention_layer(2)
    with pytest.raises(CapabilityError, match="outside the validated receipt scope"):
        backend.forward(
            "probe",
            intervention=Intervention(
                layer=1,
                vector=np.zeros(1, dtype=np.float32),
            ),
        )


def test_mlx_capture_only_is_not_limited_to_intervention_receipt_layers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = create_backend(
        BackendConfig(kind="mlx", model="openai-community/gpt2", dtype="float32")
    )
    backend.blocks = [object()] * 6
    backend.parity_validation = {
        "validated": True,
        "validated_intervention_layers": [2, 4],
    }

    def reached_tokenization(_: str) -> None:
        raise RuntimeError("capture-only reached tokenization")

    monkeypatch.setattr(backend, "tokenize", reached_tokenization)
    with pytest.raises(RuntimeError, match="capture-only reached tokenization"):
        backend.forward("probe", capture_layers=[1])


def test_mlx_private_parity_probe_bypasses_receipt_layer_gate() -> None:
    backend = create_backend(
        BackendConfig(kind="mlx", model="openai-community/gpt2", dtype="float32")
    )
    backend.parity_validation = {"validated": False}
    backend._parity_probe_mode = True

    backend._require_validated_intervention_layer(1)


def test_nested_config_typos_are_rejected(tmp_path: Path) -> None:
    path = _write_inputs(tmp_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["backend"]["revison"] = "typo-must-not-be-ignored"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    try:
        load_experiment_config(path)
    except Exception as exc:
        assert "revison" in str(exc)
    else:
        raise AssertionError("Unknown nested config fields must fail closed")


def test_cli_backend_uses_resolved_validation_receipt_path(tmp_path: Path) -> None:
    from glyphprobe.cli import _resolved_backend_config

    path = _write_inputs(tmp_path)
    receipt = tmp_path / "parity.json"
    receipt.write_text("{}\n", encoding="utf-8")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["backend"].update(
        {
            "validation_receipt": "parity.json",
            "validation_receipt_sha256": "0" * 64,
        }
    )
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    cfg, inputs = load_experiment_config(path)
    backend_cfg = _resolved_backend_config(cfg, inputs)
    assert backend_cfg.validation_receipt == receipt.resolve()
    assert cfg.backend.validation_receipt == Path("parity.json")


def test_yaml_panel_override_preserves_factors(tmp_path: Path) -> None:
    from glyphprobe.cli import _parse_glyphs

    panel_path = tmp_path / "override.yaml"
    panel_path.write_text(
        yaml.safe_dump(
            {
                "items": [
                    {
                        "id": "mystery",
                        "glyph": "🧿",
                        "factors": {"family": "amulet"},
                    }
                ]
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    parsed = _parse_glyphs(None, panel_path)
    assert parsed is not None
    assert parsed[0].glyph == "🧿"
    assert parsed[0].factors == {"family": "amulet"}


def test_packaged_starter_resources_exist() -> None:
    from importlib import resources

    root = resources.files("glyphprobe").joinpath("resources")
    assert root.joinpath("configs", "v1_standard.yaml").is_file()
    assert root.joinpath("configs", "v1_mlx_standard.yaml").is_file()
    assert root.joinpath("configs", "site_matrix.example.yaml").is_file()
    assert root.joinpath("data", "emoji_panels", "colored_shapes.yaml").is_file()


def test_inline_matrix_glyph_list_is_supported() -> None:
    from glyphprobe.cli import _parse_glyphs

    parsed = _parse_glyphs(["🟤", "🟫", "🧿"], None)
    assert parsed == ["🟤", "🟫", "🧿"]
