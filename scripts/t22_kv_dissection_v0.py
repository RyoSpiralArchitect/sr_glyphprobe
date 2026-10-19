#!/usr/bin/env python3
"""Exploratory query-local K/V dissection; no protected-bank or model downloader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import t21_glyph_context_path_pilot_v0 as historical


ROOT = historical.ROOT
PROTOCOL = "glyphprobe-t22-kv-dissection-v0"
OPERATIONS = ("none", "k", "v", "kv")
CANARY_SPEC = ROOT / "validation/t21_glyph_context_path_confirmation_v0/canary_specification.json"
CANARY_RECEIPT = ROOT / "validation/t21_glyph_context_path_pilot_v0/canary/acquisition_receipt.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def replace_kv(
    key: Any,
    value: Any,
    donor_key: Any,
    donor_value: Any,
    positions: tuple[int, ...] | list[int],
    operation: str,
    roundtrip: bool = False,
) -> tuple[Any, Any]:
    """Replace non-repeated [KV head, sequence, head_dim] tensors after RoPE.

    Neither the caller's tensors nor its query/mask are mutated. The caller
    must additionally enforce that selected positions precede its readout.
    """
    require(operation in OPERATIONS, "Unknown K/V operation")
    tensors = (key, value, donor_key, donor_value)
    require(all(t.ndim == 3 for t in tensors), "K/V tensors must have rank three")
    require(all(t.shape == key.shape for t in tensors), "K/V shape mismatch")
    require(all(t.dtype == key.dtype for t in tensors), "K/V dtype mismatch")
    require(all(t.device == key.device for t in tensors), "K/V device mismatch")
    require(all(type(p) is int for p in positions), "Positions must be integers")
    require(len(set(positions)) == len(positions), "Duplicate positions")
    require(all(0 <= p < key.shape[1] for p in positions), "Position out of range")
    changed_key, changed_value = key.clone(), value.clone()
    selected = list(positions)
    if operation in ("k", "kv"):
        changed_key[:, selected] = donor_key[:, selected]
        if roundtrip:
            changed_key[:, selected] = key[:, selected]
    if operation in ("v", "kv"):
        changed_value[:, selected] = donor_value[:, selected]
        if roundtrip:
            changed_value[:, selected] = value[:, selected]
    return changed_key, changed_value


def validate_causal_mask(mask: Any, batch: int, length: int) -> None:
    """Accept only the unpadded additive causal mask used by this workflow."""
    import torch

    require(mask is not None and mask.ndim == 4,
            "Explicit rank-four causal mask is required")
    require(torch.is_floating_point(mask), "An additive floating-point mask is required")
    require(mask.shape[-2:] == (length, length) and mask.shape[0] in (1, batch)
            and mask.shape[1] == 1, "Causal mask shape mismatch")
    future = torch.ones((length, length), dtype=torch.bool, device=mask.device).triu(1)
    require(bool((mask[..., future] <= torch.finfo(mask.dtype).min).all()),
            "Future positions must be causally masked for every query")
    require(bool((mask[..., ~future] == 0).all()),
            "Unexpected past/self masking; only unpadded causal inputs are supported")


class AttentionPath(historical.AttentionPath):
    """Reuse T21's capture/reset plumbing with a separate four-operation adapter.

    Rows use T21 conditions and add operation=none/k/v/kv (default kv).
    Diagnostics compare with a local baseline at this layer's actual input.
    They do not assert unchanged downstream routing relative to an intact run.
    """

    def __init__(self, blocks: Any, *, record_attention: bool = True):
        self.diagnostics: list[dict[str, Any]] = []
        self.record_attention = record_attention
        super().__init__(blocks)

    def _wrapper(self, index: int) -> Any:
        def forward(
            module: Any,
            hidden_states: Any,
            position_embeddings: Any = None,
            attention_mask: Any = None,
            past_key_values: Any = None,
            **kwargs: Any,
        ) -> Any:
            import torch
            from transformers.models.llama.modeling_llama import (
                apply_rotary_pos_emb,
                eager_attention_forward,
            )

            require(past_key_values is None and kwargs.get("past_key_value") is None,
                    "Cached decoding is prohibited")
            require(not module.training, "Training-mode attention is prohibited")
            require(hidden_states.ndim == 3, "Unexpected hidden-state shape")
            require(position_embeddings is not None, "RoPE embeddings are required")
            shape = hidden_states.shape[:-1]
            validate_causal_mask(attention_mask, shape[0], shape[1])
            hidden_shape = (*shape, -1, module.head_dim)
            query = module.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            key = module.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            value = module.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            query, key = apply_rotary_pos_emb(query, key, *position_embeddings)
            baseline, weights = eager_attention_forward(
                module, query, key, value, attention_mask,
                scaling=module.scaling, dropout=0.0,
            )
            if self.mode == "capture" and index > min(historical.ANCHORS):
                self.captured_kv[index] = (
                    key[0].detach().clone(), value[0].detach().clone()
                )
            if self.mode == "patch" and index > min(historical.ANCHORS):
                require(len(self.rows) == shape[0], "Patch rows must match batch size")
                changed_key, changed_value = key.clone(), value.clone()
                active: list[tuple[int, dict, str, tuple[int, ...]]] = []
                for row_index, row in enumerate(self.rows):
                    require(row["anchor"] in historical.ANCHORS, "Unsupported anchor")
                    operation = row.get("operation", "kv")
                    require(operation in OPERATIONS, "Unknown K/V operation")
                    if index <= row["anchor"]:
                        continue
                    p = row["position"]
                    require(type(p) is int and 0 <= p < shape[1], "Invalid readout")
                    require(p == row["glyph_length"] + row["distance"] - 1,
                            "Readout geometry mismatch")
                    positions = historical.foreign_positions(
                        row["condition"], row["glyph_length"], row["distance"]
                    )
                    roundtrip = row["condition"] == "reset_roundtrip"
                    if roundtrip:
                        positions = tuple(range(row["glyph_length"]))
                    require(all(0 <= pos < p for pos in positions),
                            "Only past positions may be replaced")
                    if self.neutral_path:
                        positions = ()
                    donor_key, donor_value = self.donor_kv[row["donor_slot"]][index]
                    changed_key[row_index], changed_value[row_index] = replace_kv(
                        key[row_index], value[row_index], donor_key, donor_value,
                        positions, operation, roundtrip=roundtrip,
                    )
                    require(torch.equal(changed_key[row_index, :, p:], key[row_index, :, p:]),
                            "Self/future keys changed")
                    require(torch.equal(changed_value[row_index, :, p:], value[row_index, :, p:]),
                            "Self/future values changed")
                    if operation in ("none", "v"):
                        require(torch.equal(changed_key[row_index], key[row_index]),
                                "V-only/reference changed keys")
                    if operation in ("none", "k"):
                        require(torch.equal(changed_value[row_index], value[row_index]),
                                "K-only/reference changed values")
                    active.append((row_index, row, operation, positions))
                patched, patched_weights = eager_attention_forward(
                    module, query, changed_key, changed_value, attention_mask,
                    scaling=module.scaling, dropout=0.0,
                )
                result, used_weights = baseline.clone(), weights.clone()
                selected = torch.zeros(result.shape[:2], dtype=torch.bool, device=result.device)
                for row_index, row, operation, positions in active:
                    p = row["position"]
                    result[row_index, p] = patched[row_index, p]
                    used_weights[row_index, :, p] = patched_weights[row_index, :, p]
                    selected[row_index, p] = True
                    if operation in ("none", "v"):
                        require(torch.equal(patched_weights[row_index, :, p], weights[row_index, :, p]),
                                "Local V-only/reference attention weights changed")
                    if self.record_attention:
                        actual = used_weights[row_index, :, p].detach().cpu().clone()
                        self.diagnostics.append({
                            "block": index, "row": row_index, "operation": operation,
                            "position": p, "condition": row["condition"],
                            "neutral_path": self.neutral_path,
                            "baseline_weights": weights[row_index, :, p].detach().cpu().clone(),
                            "weights": actual,
                            "selected_positions": positions,
                            "selected_mass": actual[:, list(positions)].sum(dim=-1),
                            "glyph_mass": actual[:, :row["glyph_length"]].sum(dim=-1),
                            "suffix_mass": actual[:, p-row["glyph_length"]:p].sum(dim=-1),
                        })
                require(torch.equal(result[~selected], baseline[~selected]),
                        "Non-readout attention outputs changed")
                query_mask = selected[:, None, :, None].expand_as(weights)
                require(torch.equal(used_weights[~query_mask], weights[~query_mask]),
                        "Non-readout attention weights changed")
                self.offtarget_checks += 1
                baseline, weights = result, used_weights
            self.attention_calls += 1
            output = module.o_proj(baseline.reshape(*shape, -1).contiguous())
            return output, weights

        return forward


def preflight(model_path: Path | None = None, historical_canary: Path | None = None) -> dict:
    """Read-only checks for the historical-runtime canary, never fetch a model."""
    import torch
    import transformers

    expected = historical.config()["model"]
    checks = {
        "cuda_available": torch.cuda.is_available(),
        "torch_matches_historical": torch.__version__ == expected["torch"],
        "transformers_match_historical": transformers.__version__ == expected["transformers"],
        "model_supplied": model_path is not None and model_path.is_dir(),
        "historical_canary_arrays_supplied": False,
        "historical_canary_integrity_matches": False,
        "model_manifest_matches": False,
        "bf16_supported": False,
        "gpu_matches_historical": False,
    }
    if checks["cuda_available"]:
        checks["bf16_supported"] = torch.cuda.is_bf16_supported()
        checks["gpu_matches_historical"] = torch.cuda.get_device_name(0) == expected["device"]
    if checks["model_supplied"]:
        from glyphprobe.provenance import model_artifact_receipt
        checks["model_manifest_matches"] = (
            model_artifact_receipt(model_path)["manifest_sha256"]
            == expected["artifact_manifest_sha256"]
        )
    canary_error = None
    if historical_canary is not None:
        # A directory name, finite array, or unbound receipt is insufficient.
        arrays = historical_canary / "chunk_0000_0008" / "states.npz"
        checks["historical_canary_arrays_supplied"] = arrays.is_file()
        try:
            require(historical.sha256(historical_canary / "acquisition_receipt.json")
                    == historical.sha256(CANARY_RECEIPT), "Not the original canary receipt")
            historical.check_canary(historical_canary, historical.sha256(ROOT / historical.SPEC))
            checks["historical_canary_integrity_matches"] = True
        except (OSError, ValueError, KeyError) as exc:
            canary_error = f"{type(exc).__name__}: {exc}"
    return {
        "protocol_id": PROTOCOL,
        "status": "prerequisites_present" if all(checks.values()) else "blocked",
        "checks": checks,
        "runtime": {"torch": torch.__version__, "transformers": transformers.__version__},
        "required_runtime": {k: expected[k] for k in ("torch", "transformers", "device", "dtype")},
        "historical_canary_error": canary_error,
        "model_forwards": 0,
        "boundary": "Prerequisite inspection only; does not validate arrays, admit acquisition, or establish scientific effects.",
    }


def prepare_canary(output: Path) -> dict:
    """Freeze only the eight historically exposed canary inputs, with no forward."""
    old = historical.audit_spec(ROOT / historical.SPEC)
    exposed = historical.read_json(CANARY_SPEC)
    require(exposed["target_count"] == 8 and exposed["source_count"] == 128,
            "Historical exposed canary counts changed")
    require(exposed["target_tokens"] == old["target_tokens"][:8]
            and exposed["donor_indices"] == old["donor_indices"][:8]
            and exposed["source_tokens"] == old["source_tokens"],
            "Canary inputs differ from the original eight exposed items")
    bound_files = (
        Path(__file__),
        ROOT / "tests/test_t22_kv_dissection_v0.py",
        ROOT / "tests/test_t22_kv_dissection_commands_v0.py",
        ROOT / "scripts/validate_t22_kv_dissection_v0.py",
        ROOT / "docs/T22_KV_DISSECTION_FIRST_STEP_V0.md",
        ROOT / "docs/T22_KV_DISSECTION_FIRST_STEP_V0.ja.md",
        ROOT / historical.SPEC,
        CANARY_SPEC,
        CANARY_RECEIPT,
        ROOT / "scripts/t21_glyph_context_path_pilot_v0.py",
    )
    specification = {
        "protocol_id": PROTOCOL,
        "stage": "engineering_canary_on_eight_previously_evaluated_items",
        "created_at_utc": historical.now(),
        "t22_scientific_model_forwards_at_specification": 0,
        "status": "inputs_specified_acquisition_not_admitted",
        "source_sha256": {
            p.relative_to(ROOT).as_posix(): historical.sha256(p) for p in bound_files
        },
        "target_count": 8,
        "source_count": 128,
        "target_tokens": exposed["target_tokens"],
        "source_tokens": exposed["source_tokens"],
        "donor_indices": exposed["donor_indices"],
        "model_artifact": old["model_artifact"],
        "anchor": 21,
        "active_blocks": list(range(22, 28)),
        "distance": 8,
        "carriers": ["pipe", "article_a"],
        "operations": list(OPERATIONS),
        "position_conditions": ["reset_glyph_donor", "reset_suffix_donor"],
        "reference": "same_batch_slot_with_path_replacement_disabled_reset_preserved",
        "legacy_replay": "entire_original_batch_layout_then_select_block21_distance8",
        "donor_slots": [0, 1],
        "future_acquisition_gate": [
            "synthetic_suite_passes_without_skips",
            "historical_runtime_and_checkpoint_manifest_match",
            "historical_raw_canary_receipts_and_arrays_validate",
            "stock_parity_and_exact_legacy_KV_array_replay",
        ],
        "confirmatory_result": False,
        "scientific_efficacy_screen": False,
        "protected_bank_reads": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    historical.write_json(output, specification)
    return {"status": specification["status"], "target_count": 8,
            "specification_sha256": historical.sha256(output), "model_forwards": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("preflight")
    check.add_argument("--model-path", type=Path)
    check.add_argument("--historical-canary", type=Path)
    check.add_argument("--output", type=Path)
    prepare = sub.add_parser("prepare-canary")
    prepare.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare-canary":
        print(json.dumps(prepare_canary(args.output), indent=2, sort_keys=True))
        return
    result = preflight(args.model_path, args.historical_canary)
    result["adapter_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output:
        historical.write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "prerequisites_present" else 2)


if __name__ == "__main__":
    main()
