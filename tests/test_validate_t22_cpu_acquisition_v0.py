"""Independent stored-array audit tests; NumPy only, no model or runner imports."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_SPEC = importlib.util.spec_from_file_location(
    "independent_t22_cpu_audit",
    Path(__file__).resolve().parents[1] / "scripts/validate_t22_cpu_acquisition_v0.py",
)
audit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(audit)
TINY_DIMS = {"layers": 28, "hidden_size": 16, "attention_heads": 4, "kv_heads": 2, "head_dim": 4}


class Arrays(dict):
    @property
    def files(self):
        return list(self)


def fixture_arrays(glyph_length):
    """Construct coherent synthetic stored arrays, never acquisition evidence."""
    tokens = {"raw": {"glyph": list(range(glyph_length)), "codepoint_literal": [20, 21, 22]}}
    schema = audit.array_schema(tokens, TINY_DIMS)
    arrays = Arrays({name: np.zeros(meta["shape"], dtype=meta["dtype"]) for name, meta in schema.items()})
    length = glyph_length + 8
    p = glyph_length + 7
    # Truncate a float32 uniform probability to exactly representable BF16.
    probability = np.array([1.0 / length], dtype=np.float32)
    probability.view(np.uint32)[:] &= np.uint32(0xFFFF0000)
    for carrier in audit.CARRIERS:
        weights = arrays[f"{carrier}_attention_weights"]
        baseline = arrays[f"{carrier}_attention_baseline_weights"]
        weights.fill(probability[0])
        baseline[:] = weights
        selected = arrays[f"{carrier}_attention_selected_mask"]
        for index, (operation, position, donor) in enumerate(audit.extension_rows(glyph_length)):
            positions = list(range(glyph_length)) if position == "glyph" else list(range(p - glyph_length, p))
            selected[0, :, index, positions] = True
            if operation == "k":
                # A legal K-only attention change; V-only remains locally fixed.
                weights[0, :, index] = 0.0
                weights[0, :, index, :, positions[0]] = 1.0
        for label, positions in (("selected", None), ("glyph", list(range(glyph_length))),
                                 ("suffix", list(range(p - glyph_length, p)))):
            mask = selected if positions is None else np.zeros_like(selected)
            if positions is not None:
                mask[..., positions] = True
            arrays[f"{carrier}_attention_{label}_mass"][:] = (weights * mask[..., None, :]).sum(axis=-1, dtype=np.float32)
    return tokens, arrays


@pytest.mark.parametrize("glyph_length", (1, 2, 3))
def test_independent_array_geometry_handles_mixed_token_lengths(glyph_length):
    tokens, arrays = fixture_arrays(glyph_length)
    result = audit.validate_arrays(arrays, tokens, TINY_DIMS)
    assert result["array_count"] == 34
    assert result["glyph_token_count"] == glyph_length
    assert result["all_three_float32_attention_mass_reconstructions_exact"] is True


@pytest.mark.parametrize("corruption", (
    "missing_array", "wrong_shape", "wrong_dtype", "nonfinite", "non_bf16",
    "legacy_mismatch", "legacy_noop", "reference_extension", "v_weights",
    "neutral_weights", "baseline_range", "zero_probability_sum", "selected_mask", "mass",
))
def test_independent_array_checks_reject_corruption(corruption):
    tokens, arrays = fixture_arrays(2)
    if corruption == "missing_array":
        arrays.pop("pipe_donor_keys")
    elif corruption == "wrong_shape":
        arrays["pipe_stock_hidden"] = arrays["pipe_stock_hidden"][:-1]
    elif corruption == "wrong_dtype":
        arrays["pipe_stock_hidden"] = arrays["pipe_stock_hidden"].astype(np.float64)
    elif corruption == "nonfinite":
        arrays["pipe_stock_hidden"][0, 0] = np.nan
    elif corruption == "non_bf16":
        arrays["pipe_stock_hidden"][0, 0] = np.float32(0.1)
    elif corruption == "legacy_mismatch":
        arrays["pipe_legacy_t22"][0, 0] = 1.0
    elif corruption == "legacy_noop":
        arrays["pipe_legacy_t22"][0, 0] = arrays["pipe_legacy_historical"][0, 0] = 1.0
    elif corruption == "reference_extension":
        arrays["pipe_extension"][0, 0] = 1.0
    elif corruption == "v_weights":
        weights = arrays["pipe_attention_weights"]
        weights[0, :, 8] = 0.0
        weights[0, :, 8, :, 0] = 1.0
    elif corruption == "neutral_weights":
        weights = arrays["pipe_attention_weights"]
        weights[1, :, 4] = 0.0
        weights[1, :, 4, :, 0] = 1.0
    elif corruption == "baseline_range":
        baseline = arrays["pipe_attention_baseline_weights"]
        baseline[0, :, 4] = 0.0
        baseline[0, :, 4, :, 0] = -1.0
        baseline[0, :, 4, :, 1] = 2.0
    elif corruption == "zero_probability_sum":
        arrays["pipe_attention_weights"][0, :, 4] = 0.0
    elif corruption == "selected_mask":
        arrays["pipe_attention_selected_mask"][0, 0, 0, 0] = False
    else:
        arrays["pipe_attention_selected_mass"][0, 0, 0, 0] += 1.0
    with pytest.raises(ValueError):
        audit.validate_arrays(arrays, tokens, TINY_DIMS)


@pytest.mark.parametrize("text", ('{"value":1,"value":2}', '{"value":NaN}', '{"value":Infinity}'))
def test_receipt_json_rejects_ambiguous_or_nonfinite_values(tmp_path, text):
    path = tmp_path / "receipt.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        audit.read(path)


def test_claim_boundary_cannot_be_promoted():
    with pytest.raises(ValueError, match="Claim boundary"):
        audit.boundary({"scientific_result": True, "protected_bank_reads": 0, "generation_calls": 0}, ("scientific_result",))
