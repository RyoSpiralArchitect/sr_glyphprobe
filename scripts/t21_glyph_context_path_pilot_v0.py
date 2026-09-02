#!/usr/bin/env python3
"""Receipt-bound, exposed-item T21 attention-path pilot. No reserve reader."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types
from typing import Any
import uuid

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PROTOCOL = "glyphprobe-t21-glyph-context-path-pilot-v0"
CONFIG = Path("configs/t21_glyph_context_path_pilot_v0.yaml")
SPEC = Path("validation/t21_glyph_context_path_pilot_v0/pilot_specification_v1.json")
CONDITIONS = (
    "intact",
    "reset",
    "intact_glyph_donor",
    "intact_suffix_donor",
    "reset_glyph_donor",
    "reset_suffix_donor",
    "reset_prefix_donor",
    "reset_prefix_restore_glyph",
    "reset_prefix_restore_suffix",
    "reset_roundtrip",
    "no_op",
)
CONTEXTS = (("pipe", 4), ("pipe", 8), ("article_a", 4), ("article_a", 8))
ANCHORS = (21, 24)
VIEWS = ("glyph", "alias_label", "codepoint_literal")
METRICS = (
    "alias_margin",
    "donor_margin",
    "alias_top1",
    "codepoint_margin",
    "codepoint_top1",
)
ALL_METRICS = (*METRICS, *(name + "_effect" for name in METRICS))
CONTRASTS = {
    "calibration": ("reset", "reset_prefix_donor"),
    "necessity_absolute": ("reset", "reset_glyph_donor"),
    "necessity_position_adjusted": ("reset_suffix_donor", "reset_glyph_donor"),
    "rescue_absolute": ("reset_prefix_restore_glyph", "reset_prefix_donor"),
    "rescue_position_adjusted": (
        "reset_prefix_restore_glyph",
        "reset_prefix_restore_suffix",
    ),
}
BOUND_FILES = (
    CONFIG,
    Path("scripts/t21_glyph_context_path_pilot_v0.py"),
    Path("scripts/validate_t21_glyph_context_path_pilot_v0.py"),
    Path("tests/test_t21_glyph_context_path_pilot_v0.py"),
    Path("docs/T21_GLYPH_CONTEXT_PATH_PILOT_V0.md"),
    Path("docs/T21_GLYPH_CONTEXT_PATH_PILOT_V0.ja.md"),
    Path("src/glyphprobe/provenance.py"),
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Expected a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(
            value, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def config() -> dict[str, Any]:
    value = yaml.safe_load((ROOT / CONFIG).read_text(encoding="utf-8"))
    require(value["protocol_id"] == PROTOCOL, "Protocol mismatch")
    require(
        value["population"]["confirmatory_reserve_access"] is False,
        "Reserve access is prohibited",
    )
    require(
        tuple(value["intervention"]["conditions"]) == CONDITIONS,
        "Condition order mismatch",
    )
    return value


def input_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cfg = config()["population"]
    for key in ("target_selection", "donor_selection"):
        require(
            sha256(ROOT / cfg[key]) == cfg[key + "_sha256"], f"Changed input: {key}"
        )
    target = read_json(ROOT / cfg["target_selection"])["fresh_eval_items"]
    source = read_json(ROOT / cfg["donor_selection"])["causal_source_items"]
    target = sorted(target, key=lambda row: int(row["bank_index"]))
    source = sorted(source, key=lambda row: int(row["bank_index"]))
    require(
        len(target) == 384 and len(source) == 128, "Exposed population count mismatch"
    )
    require(
        not {row["codepoint"] for row in target} & {row["codepoint"] for row in source},
        "Overlapping donor and target",
    )
    require(
        len({row["alias_label"] for row in target + source}) == 512,
        "Keyword gallery overlap",
    )
    return target, source


def tokenize_rows(tokenizer: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cfg = config()["input"]
    result = []
    for index, row in enumerate(rows):
        raw = {
            view: list(
                map(int, tokenizer.encode(str(row[view]), add_special_tokens=False))
            )
            for view in VIEWS
        }
        sequences = {}
        for carrier, unit in cfg["carriers"].items():
            unit_ids = tokenizer.encode(unit, add_special_tokens=False)
            require(len(unit_ids) == 1, "Carrier must be exactly one token")
            sequences[carrier] = {}
            for view in VIEWS:
                ids = list(
                    map(
                        int,
                        tokenizer.encode(
                            str(row[view]) + unit * 8, add_special_tokens=False
                        ),
                    )
                )
                require(
                    ids == raw[view] + unit_ids * 8,
                    "Prefix or carrier tokenization changed",
                )
                sequences[carrier][view] = ids
        require(
            1 <= len(raw["glyph"]) <= 3,
            "Glyph lacks an equal-count distance-4 suffix control",
        )
        result.append({"index": index, "raw": raw, "sequences": sequences})
    return result


def choose_donors(
    target_rows: list[dict[str, Any]],
    target_tokens: list[dict[str, Any]],
    source_tokens: list[dict[str, Any]],
) -> list[list[int]]:
    result = []
    for row, tokens in zip(target_rows, target_tokens, strict=True):
        length = len(tokens["raw"]["glyph"])
        eligible = [
            i
            for i, value in enumerate(source_tokens)
            if len(value["raw"]["glyph"]) == length
        ]
        require(len(eligible) >= 2, "Insufficient token-matched donors")
        ordered = sorted(
            eligible,
            key=lambda index: hashlib.sha256(
                f"{PROTOCOL}:donor:{row['codepoint']}:{index}".encode()
            ).hexdigest(),
        )
        result.append(ordered[:2])
    return result


def prepare(model_path: Path, output: Path) -> dict[str, Any]:
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoTokenizer

    require(not output.exists(), "Specification already exists")
    cfg = config()
    artifact = model_artifact_receipt(model_path)
    require(
        artifact["manifest_sha256"] == cfg["model"]["artifact_manifest_sha256"],
        "Model artifact changed",
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=False, use_fast=True
    )
    target, source = input_rows()
    target_tokens, source_tokens = (
        tokenize_rows(tokenizer, target),
        tokenize_rows(tokenizer, source),
    )
    specification = {
        "protocol_id": PROTOCOL,
        "status": "specified_before_t21_pilot_forwards",
        "created_at_utc": now(),
        "parent_commit": cfg["parent_commit"],
        "source_sha256": {path.as_posix(): sha256(ROOT / path) for path in BOUND_FILES},
        "input_sha256": {
            cfg["population"][key]: cfg["population"][key + "_sha256"]
            for key in ("target_selection", "donor_selection")
        },
        "model_artifact": artifact,
        "target_tokens": target_tokens,
        "source_tokens": source_tokens,
        "donor_indices": choose_donors(target, target_tokens, source_tokens),
        "target_count": 384,
        "source_count": 128,
        "reserve_count": 195,
        "reserve_access_allowed": False,
        "reserve_model_forwards": 0,
        "pilot_model_forwards_at_specification": 0,
        "contexts": [list(value) for value in CONTEXTS],
        "anchors": list(ANCHORS),
        "conditions": list(CONDITIONS),
        "views": list(VIEWS),
        "token_length_counts": {
            "target": dict(Counter(len(row["raw"]["glyph"]) for row in target_tokens)),
            "source": dict(Counter(len(row["raw"]["glyph"]) for row in source_tokens)),
        },
    }
    write_json(output, specification)
    return {
        "status": "pass",
        "specification_sha256": sha256(output),
        "target_count": 384,
        "reserve_model_forwards": 0,
    }


def audit_spec(path: Path) -> dict[str, Any]:
    value = read_json(path)
    require(
        value["protocol_id"] == PROTOCOL
        and value["status"] == "specified_before_t21_pilot_forwards",
        "Invalid specification",
    )
    require(value["reserve_access_allowed"] is False, "Reserve access is prohibited")
    for relative, expected in {
        **value["source_sha256"],
        **value["input_sha256"],
    }.items():
        require(
            sha256(ROOT / relative) == expected,
            f"Changed specification asset: {relative}",
        )
    require(
        value["target_count"] == 384 and value["source_count"] == 128, "Invalid counts"
    )
    require(value["conditions"] == list(CONDITIONS), "Changed conditions")
    return value


def position_groups(glyph_length: int, distance: int) -> dict[str, tuple[int, ...]]:
    require(
        glyph_length >= 1 and distance > glyph_length,
        "Insufficient preceding suffix positions",
    )
    readout = glyph_length + distance - 1
    return {
        "glyph": tuple(range(glyph_length)),
        "suffix": tuple(range(readout - glyph_length, readout)),
        "prefix": tuple(range(readout)),
    }


def foreign_positions(
    condition: str, glyph_length: int, distance: int
) -> tuple[int, ...]:
    groups = position_groups(glyph_length, distance)
    if condition in ("intact_glyph_donor", "reset_glyph_donor"):
        return groups["glyph"]
    if condition in ("intact_suffix_donor", "reset_suffix_donor"):
        return groups["suffix"]
    if condition == "reset_prefix_donor":
        return groups["prefix"]
    if condition == "reset_prefix_restore_glyph":
        return tuple(i for i in groups["prefix"] if i not in groups["glyph"])
    if condition == "reset_prefix_restore_suffix":
        return tuple(i for i in groups["prefix"] if i not in groups["suffix"])
    require(
        condition in ("intact", "reset", "reset_roundtrip", "no_op"),
        "Unknown condition",
    )
    return ()


class AttentionPath:
    """Instance-local eager attention; modify only specified query outputs."""

    def __init__(self, blocks: Any):
        self.blocks = blocks
        self.mode = "idle"
        self.neutral_path = False
        self.positions: list[int] = []
        self.captured_states: dict[int, Any] = {}
        self.captured_kv: dict[int, tuple[Any, Any]] = {}
        self.rows: list[dict[str, Any]] = []
        self.donor_kv: list[dict[int, tuple[Any, Any]]] = []
        self.resets: dict[int, Any] = {}
        self.offtarget_checks = 0
        self.attention_calls = 0
        self.handles = []
        self.originals = []
        for index, block in enumerate(blocks):
            module = block.self_attn
            self.originals.append(module.forward)
            module.forward = types.MethodType(self._wrapper(index), module)
            if index in ANCHORS:
                self.handles.append(
                    block.register_forward_hook(self._residual_hook(index))
                )

    def _residual_hook(self, index: int) -> Any:
        def hook(_module: Any, _args: Any, output: Any) -> Any:
            raw = output[0] if isinstance(output, tuple) else output
            if self.mode == "capture":
                self.captured_states[index] = raw[0, self.positions].detach().clone()
                return output
            if self.mode != "patch":
                return output
            changed = raw.clone()
            for row_index, row in enumerate(self.rows):
                if row["anchor"] == index and row["condition"].startswith("reset"):
                    changed[row_index, row["position"]] = self.resets[index][
                        row["distance_index"]
                    ]
            return (changed, *output[1:]) if isinstance(output, tuple) else changed

        return hook

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

            require(
                past_key_values is None,
                "This path intervention prohibits cached decoding",
            )
            require(not module.training, "Training-mode attention is prohibited")
            shape = hidden_states.shape[:-1]
            hidden_shape = (*shape, -1, module.head_dim)
            query = module.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            key = module.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            value = module.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)
            query, key = apply_rotary_pos_emb(query, key, *position_embeddings)
            baseline, weights = eager_attention_forward(
                module,
                query,
                key,
                value,
                attention_mask,
                scaling=module.scaling,
                dropout=0.0,
            )
            if self.mode == "capture" and index > min(ANCHORS):
                self.captured_kv[index] = (
                    key[0].detach().clone(),
                    value[0].detach().clone(),
                )
            if self.mode == "patch" and index > min(ANCHORS):
                require(attention_mask is not None, "Causal mask must be explicit")
                changed_key, changed_value = key.clone(), value.clone()
                for row_index, row in enumerate(self.rows):
                    if index <= row["anchor"]:
                        continue
                    donor_key, donor_value = self.donor_kv[row["donor_slot"]][index]
                    require(
                        donor_key.shape == key[row_index].shape,
                        "Donor token positions do not align",
                    )
                    positions = foreign_positions(
                        row["condition"], row["glyph_length"], row["distance"]
                    )
                    if self.neutral_path:
                        positions = ()
                    if positions:
                        changed_key[row_index, :, list(positions)] = donor_key[
                            :, list(positions)
                        ]
                        changed_value[row_index, :, list(positions)] = donor_value[
                            :, list(positions)
                        ]
                    if row["condition"] == "reset_roundtrip":
                        positions = list(range(row["glyph_length"]))
                        changed_key[row_index, :, positions] = donor_key[:, positions]
                        changed_value[row_index, :, positions] = donor_value[
                            :, positions
                        ]
                        changed_key[row_index, :, positions] = key[
                            row_index, :, positions
                        ]
                        changed_value[row_index, :, positions] = value[
                            row_index, :, positions
                        ]
                    p = row["position"]
                    require(
                        torch.equal(
                            changed_key[row_index, :, p:], key[row_index, :, p:]
                        ),
                        "Self/future keys changed",
                    )
                    require(
                        torch.equal(
                            changed_value[row_index, :, p:], value[row_index, :, p:]
                        ),
                        "Self/future values changed",
                    )
                patched, _ = eager_attention_forward(
                    module,
                    query,
                    changed_key,
                    changed_value,
                    attention_mask,
                    scaling=module.scaling,
                    dropout=0.0,
                )
                result = baseline.clone()
                selected = torch.zeros(
                    result.shape[:2], dtype=torch.bool, device=result.device
                )
                for row_index, row in enumerate(self.rows):
                    if index > row["anchor"]:
                        result[row_index, row["position"]] = patched[
                            row_index, row["position"]
                        ]
                        selected[row_index, row["position"]] = True
                require(
                    torch.equal(result[~selected], baseline[~selected]),
                    "Non-readout attention output changed",
                )
                self.offtarget_checks += 1
                baseline = result
            self.attention_calls += 1
            output = module.o_proj(baseline.reshape(*shape, -1).contiguous())
            return output, weights

        return forward

    def close(self) -> None:
        for block, original in zip(self.blocks, self.originals, strict=True):
            block.self_attn.forward = original
        for handle in self.handles:
            handle.remove()


def foreign_gpu_pids() -> list[int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [
        int(line.strip())
        for line in result.stdout.splitlines()
        if line.strip().isdigit() and int(line.strip()) != os.getpid()
    ]


def resource_check(output: Path, boundary: str, started: float) -> None:
    pids = foreign_gpu_pids()
    timed_out = time.perf_counter() - started > float(
        config()["execution"]["pilot_wall_budget_seconds"]
    )
    if pids or timed_out:
        write_json(
            output / f"yield_{uuid.uuid4().hex}.json",
            {
                "protocol_id": PROTOCOL,
                "boundary": boundary,
                "foreign_gpu_pids": pids,
                "runtime_budget_reached": timed_out,
                "time_utc": now(),
                "reserve_model_forwards": 0,
            },
        )
        raise SystemExit(75)


def load_model(
    model_path: Path, specification: dict[str, Any]
) -> tuple[Any, Any, dict[str, Any]]:
    import torch
    import transformers
    from glyphprobe.provenance import model_artifact_receipt
    from transformers import AutoModelForCausalLM
    from transformers.models.llama.modeling_llama import LlamaAttention

    cfg = config()["model"]
    require(
        torch.__version__ == cfg["torch"]
        and transformers.__version__ == cfg["transformers"],
        "Runtime version mismatch",
    )
    require(
        torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        "CUDA BF16 unavailable",
    )
    require(torch.cuda.get_device_name(0) == cfg["device"], "GPU identity mismatch")
    artifact = model_artifact_receipt(model_path)
    require(
        artifact == specification["model_artifact"],
        "Model files changed after specification",
    )
    torch.set_num_threads(4)
    torch.manual_seed(2026092100)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.bfloat16,
        attn_implementation="eager",
    )
    model.to("cuda").eval()
    require(type(model).__name__ == "LlamaForCausalLM", "Unexpected model class")
    require(
        len(model.model.layers) == cfg["layers"]
        and model.config.hidden_size == cfg["hidden_size"],
        "Model dimensions changed",
    )
    require(
        sum(p.numel() for p in model.parameters()) == cfg["parameters"],
        "Parameter count changed",
    )
    require(
        {p.dtype for p in model.parameters()} == {torch.bfloat16},
        "Unexpected parameter dtype",
    )
    receipt = {
        "artifact": artifact,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "python": sys.version,
        "gpu": torch.cuda.get_device_name(0),
        "attention": "eager",
        "llama_attention_source_sha256": hashlib.sha256(
            inspect.getsource(LlamaAttention.forward).encode()
        ).hexdigest(),
        "generation_calls": 0,
        "runtime_modified": False,
    }
    return torch, model, receipt


def capture(
    torch: Any,
    model: Any,
    controller: AttentionPath,
    token_row: dict[str, Any],
    carrier: str,
    view: str,
) -> tuple[np.ndarray, dict[int, Any], dict[int, Any]]:
    ids = token_row["sequences"][carrier][view]
    controller.mode = "capture"
    controller.positions = [
        len(token_row["raw"][view]) + distance - 1 for distance in (4, 8)
    ]
    controller.captured_states, controller.captured_kv = {}, {}
    inputs = torch.tensor([ids], device="cuda", dtype=torch.long)
    with torch.inference_mode():
        output = model.model(
            input_ids=inputs,
            attention_mask=torch.ones_like(inputs),
            use_cache=False,
            return_dict=True,
        )
    final = output.last_hidden_state[0, controller.positions].float().cpu().numpy()
    controller.mode = "idle"
    return final, controller.captured_states, controller.captured_kv


def patch_item(
    torch: Any,
    model: Any,
    controller: AttentionPath,
    token_row: dict[str, Any],
    carrier: str,
    resets: dict[int, Any],
    donor_kv: list[dict[int, Any]],
) -> tuple[np.ndarray, np.ndarray]:
    length = len(token_row["raw"]["glyph"])
    controller.rows = [
        {
            "distance": distance,
            "distance_index": di,
            "anchor": anchor,
            "condition": condition,
            "donor_slot": donor,
            "glyph_length": length,
            "position": length + distance - 1,
        }
        for di, distance in enumerate((4, 8))
        for anchor in ANCHORS
        for donor in range(2)
        for condition in CONDITIONS
    ]
    controller.resets, controller.donor_kv = resets, donor_kv
    controller.mode = "patch"
    ids = token_row["sequences"][carrier]["glyph"]
    inputs = torch.tensor([ids], device="cuda", dtype=torch.long).repeat(
        len(controller.rows), 1
    )
    positions = torch.tensor(
        [row["position"] for row in controller.rows], device="cuda"
    )
    acquired = []
    for neutral in (False, True):
        controller.neutral_path = neutral
        with torch.inference_mode():
            output = model.model(
                input_ids=inputs,
                attention_mask=torch.ones_like(inputs),
                use_cache=False,
                return_dict=True,
            )
        final = (
            output.last_hidden_state[
                torch.arange(len(controller.rows), device="cuda"), positions
            ]
            .float()
            .cpu()
            .numpy()
        )
        acquired.append(final.reshape(2, len(ANCHORS), 2, len(CONDITIONS), -1))
    controller.neutral_path = False
    controller.mode = "idle"
    shaped, reference = acquired
    require(
        np.isfinite(shaped).all() and np.isfinite(reference).all(),
        "Nonfinite intervention states",
    )
    for condition in ("intact", "reset", "no_op", "reset_roundtrip"):
        ci = CONDITIONS.index(condition)
        require(
            np.array_equal(shaped[..., ci, :], reference[..., ci, :]),
            f"Same-slot reference check failed: {condition}",
        )
    return shaped, reference


def verify_chunk(path: Path, specification_hash: str) -> dict[str, Any]:
    receipt = read_json(path / "receipt.json")
    require(
        receipt["specification_sha256"] == specification_hash,
        "Chunk specification mismatch",
    )
    require(
        sha256(path / "states.npz") == receipt["states_sha256"], "Chunk states changed"
    )
    require(
        receipt["no_op_exact"]
        and receipt["roundtrip_exact"]
        and receipt["nonreadout_unchanged"],
        "Chunk engineering check failed",
    )
    return receipt


def check_canary(root: Path, specification_hash: str) -> str:
    receipt = read_json(root / "acquisition_receipt.json")
    require(
        receipt["status"] == "canary_complete" and receipt["target_items"] == 8,
        "Completed eight-item canary is required",
    )
    require(
        receipt["specification_sha256"] == specification_hash,
        "Canary used a different specification",
    )
    require(
        receipt["stock_eager_adapter_exact"] is True
        and receipt["reserve_model_forwards"] == 0,
        "Canary parity or reserve check failed",
    )
    require(
        sha256(root / "source_states.npz") == receipt["source_states_sha256"],
        "Canary source bytes changed",
    )
    covered = []
    for name, expected in receipt["chunks"].items():
        path = root / name
        require(sha256(path / "receipt.json") == expected, "Canary receipt changed")
        chunk = verify_chunk(path, specification_hash)
        covered.extend(range(chunk["start"], chunk["stop"]))
        with np.load(path / "states.npz", allow_pickle=False) as values:
            states, reference = values["intervention"], values["neutral_reference"]
            for ci in (0, 1, 9, 10):
                require(
                    np.array_equal(states[..., ci, :], reference[..., ci, :]),
                    "Canary same-slot control mismatch",
                )
    require(sorted(covered) == list(range(8)), "Canary coverage mismatch")
    return sha256(root / "acquisition_receipt.json")


def run(
    model_path: Path,
    specification_path: Path,
    output: Path,
    *,
    canary: bool = False,
    resume: bool = False,
    canary_root: Path | None = None,
) -> dict[str, Any]:
    specification = audit_spec(specification_path)
    specification_hash = sha256(specification_path)
    require(
        canary or canary_root is not None,
        "A validated canary is required before the full pilot",
    )
    canary_hash = None if canary else check_canary(canary_root, specification_hash)
    started = time.perf_counter()
    count = 8 if canary else 384
    if output.exists():
        require(
            resume, "Output exists; use explicit resume for identical incomplete work"
        )
        require(
            not (output / "acquisition_receipt.json").exists(),
            "Completed run cannot be resumed",
        )
        require(
            sha256(output / "specification.json") == specification_hash,
            "Resume specification mismatch",
        )
    else:
        output.mkdir(parents=True)
        with (output / "specification.json").open("xb") as handle:
            handle.write(specification_path.read_bytes())
    resource_check(output, "before_model_load", started)
    torch, model, model_receipt = load_model(model_path, specification)
    target_tokens, source_tokens = (
        specification["target_tokens"],
        specification["source_tokens"],
    )
    sample = torch.tensor(
        [target_tokens[0]["sequences"]["pipe"]["glyph"]],
        device="cuda",
        dtype=torch.long,
    )
    with torch.inference_mode():
        stock = (
            model.model(
                input_ids=sample,
                attention_mask=torch.ones_like(sample),
                use_cache=False,
                return_dict=True,
            )
            .last_hidden_state.detach()
            .clone()
        )
    controller = AttentionPath(model.model.layers)
    forwards, sequences = 1, 1
    try:
        with torch.inference_mode():
            instrumented = model.model(
                input_ids=sample,
                attention_mask=torch.ones_like(sample),
                use_cache=False,
                return_dict=True,
            ).last_hidden_state
        forwards += 1
        sequences += 1
        require(
            torch.equal(stock, instrumented),
            "Adapter parity with stock eager attention failed",
        )
        width = int(config()["model"]["hidden_size"])
        source_states = np.empty((128, 4, 3, width), np.float32)
        cached_donors: dict[tuple[int, str], dict[int, Any]] = {}
        for index, tokens in enumerate(source_tokens):
            resource_check(output, f"source_{index:03d}", started)
            for ci, carrier in enumerate(("pipe", "article_a")):
                for vi, view in enumerate(VIEWS):
                    final, _states, kv = capture(
                        torch, model, controller, tokens, carrier, view
                    )
                    source_states[index, ci * 2 : ci * 2 + 2, vi] = final
                    if view == "glyph":
                        cached_donors[index, carrier] = kv
                    forwards += 1
                    sequences += 1
            if index % 32 == 31:
                print(
                    json.dumps(
                        {
                            "stage": "donor_capture",
                            "completed": index + 1,
                            "reserve_forwards": 0,
                        }
                    ),
                    flush=True,
                )
        source_path = output / "source_states.npz"
        if source_path.exists():
            stored_source = read_json(output / "source_receipt.json")
            require(
                sha256(source_path) == stored_source["states_sha256"],
                "Stored source states changed",
            )
            with np.load(source_path, allow_pickle=False) as stored:
                require(
                    np.array_equal(source_states, stored["states"]),
                    "Source replay differs on resume",
                )
        else:
            np.savez_compressed(source_path, states=source_states)
            write_json(
                output / "source_receipt.json",
                {
                    "specification_sha256": specification_hash,
                    "states_sha256": sha256(source_path),
                    "source_items": 128,
                    "contexts": 4,
                    "views": 3,
                },
            )
        chunk_size = int(config()["execution"]["chunk_items"])
        chunk_hashes = {}
        for start in range(0, count, chunk_size):
            stop = min(start + chunk_size, count)
            destination = output / f"chunk_{start:04d}_{stop:04d}"
            if destination.exists():
                receipt = verify_chunk(destination, specification_hash)
                require(
                    receipt["start"] == start and receipt["stop"] == stop,
                    "Chunk index changed",
                )
                chunk_hashes[destination.name] = sha256(destination / "receipt.json")
                continue
            stage = output / f".chunk_{start:04d}_{stop:04d}.partial-{uuid.uuid4().hex}"
            stage.mkdir()
            baseline = np.empty((stop - start, 4, 3, width), np.float32)
            final_states = np.empty(
                (stop - start, 4, 2, 2, len(CONDITIONS), width), np.float32
            )
            neutral_states = np.empty_like(final_states)
            chunk_forwards = 0
            for index in range(start, stop):
                resource_check(output, f"target_{index:03d}", started)
                tokens = target_tokens[index]
                for ci, carrier in enumerate(("pipe", "article_a")):
                    resets = None
                    for vi, view in enumerate(VIEWS):
                        final, states, _kv = capture(
                            torch, model, controller, tokens, carrier, view
                        )
                        baseline[index - start, ci * 2 : ci * 2 + 2, vi] = final
                        if view == "codepoint_literal":
                            resets = states
                        forwards += 1
                        sequences += 1
                        chunk_forwards += 1
                    require(resets is not None, "Missing codepoint reset state")
                    donors = [
                        cached_donors[donor, carrier]
                        for donor in specification["donor_indices"][index]
                    ]
                    patched, reference = patch_item(
                        torch, model, controller, tokens, carrier, resets, donors
                    )
                    final_states[index - start, ci * 2 : ci * 2 + 2] = patched
                    neutral_states[index - start, ci * 2 : ci * 2 + 2] = reference
                    forwards += 2
                    sequences += 2 * 2 * 2 * 2 * len(CONDITIONS)
                    chunk_forwards += 2
            np.savez_compressed(
                stage / "states.npz",
                baseline=baseline,
                intervention=final_states,
                neutral_reference=neutral_states,
                item_indices=np.arange(start, stop, dtype=np.int64),
            )
            receipt = {
                "protocol_id": PROTOCOL,
                "specification_sha256": specification_hash,
                "start": start,
                "stop": stop,
                "states_sha256": sha256(stage / "states.npz"),
                "batched_forward_calls": chunk_forwards,
                "no_op_exact": True,
                "roundtrip_exact": True,
                "nonreadout_unchanged": True,
                "reserve_model_forwards": 0,
            }
            write_json(stage / "receipt.json", receipt)
            require(not destination.exists(), "Chunk destination appeared concurrently")
            stage.rename(destination)
            chunk_hashes[destination.name] = sha256(destination / "receipt.json")
            print(
                json.dumps(
                    {
                        "stage": "pilot",
                        "completed": stop,
                        "total": count,
                        "elapsed_seconds": round(time.perf_counter() - started, 2),
                        "reserve_forwards": 0,
                    }
                ),
                flush=True,
            )
        receipt = {
            "protocol_id": PROTOCOL,
            "status": "canary_complete" if canary else "pilot_acquisition_complete",
            "specification_sha256": specification_hash,
            "target_items": count,
            "source_items": 128,
            "reserve_model_forwards": 0,
            "generation_calls": 0,
            "stock_eager_adapter_exact": True,
            "offtarget_checks_this_invocation": controller.offtarget_checks,
            "batched_forward_calls_this_invocation": forwards,
            "sequence_forwards_this_invocation": sequences,
            "elapsed_seconds_this_invocation": time.perf_counter() - started,
            "source_states_sha256": sha256(source_path),
            "chunks": chunk_hashes,
            "model": model_receipt,
            "completed_at_utc": now(),
            "canary_receipt_sha256": canary_hash,
        }
        write_json(output / "acquisition_receipt.json", receipt)
        return {
            "status": receipt["status"],
            "target_items": count,
            "acquisition_receipt_sha256": sha256(output / "acquisition_receipt.json"),
            "reserve_model_forwards": 0,
        }
    finally:
        controller.close()
        del model
        torch.cuda.empty_cache()


def normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    norms = np.linalg.norm(values, axis=-1, keepdims=True)
    require(
        np.isfinite(values).all() and bool((norms > 1e-12).all()),
        "Invalid readout vector",
    )
    return values / norms


def score_states(
    states: np.ndarray,
    own_alias: np.ndarray,
    own_codepoint: np.ndarray,
    source_alias: np.ndarray,
    source_codepoint: np.ndarray,
    donor_indices: np.ndarray,
) -> dict[str, np.ndarray]:
    q = normalize(states)
    own_a, own_c = normalize(own_alias), normalize(own_codepoint)
    source_a, source_c = normalize(source_alias), normalize(source_codepoint)
    result = {name: np.empty(q.shape[:-1], np.float64) for name in METRICS}
    for index in range(len(q)):
        flat = q[index].reshape(-1, q.shape[-1])
        alias_scores = (
            flat @ np.concatenate((own_a[index : index + 1], source_a)).T
        ).reshape(*q.shape[1:-1], 129)
        codepoint_scores = (
            flat @ np.concatenate((own_c[index : index + 1], source_c)).T
        ).reshape(*q.shape[1:-1], 129)
        result["alias_margin"][index] = alias_scores[..., 0] - alias_scores[
            ..., 1:
        ].max(axis=-1)
        result["codepoint_margin"][index] = codepoint_scores[..., 0] - codepoint_scores[
            ..., 1:
        ].max(axis=-1)
        result["alias_top1"][index] = (alias_scores.argmax(axis=-1) == 0).astype(
            np.float64
        )
        result["codepoint_top1"][index] = (
            codepoint_scores.argmax(axis=-1) == 0
        ).astype(np.float64)
        for slot, donor in enumerate(donor_indices[index]):
            result["donor_margin"][index, :, slot] = (
                alias_scores[:, slot, :, 0] - alias_scores[:, slot, :, int(donor) + 1]
            )
    return result


def bootstrap_summary(
    values: np.ndarray, *, seed: int, replicates: int = 20000
) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    require(
        values.ndim == 1 and len(values) >= 2 and np.isfinite(values).all(),
        "Invalid item contrasts",
    )
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, np.float64)
    for start in range(0, replicates, 1000):
        count = min(1000, replicates - start)
        indices = rng.integers(0, len(values), size=(count, len(values)))
        means[start : start + count] = values[indices].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "mean": float(values.mean()),
        "lower_95": float(low),
        "upper_95": float(high),
        "item_sd": float(values.std(ddof=1)),
    }


def pilot_decision(
    metrics: dict[str, np.ndarray], *, replicates: int = 20000
) -> dict[str, Any]:
    rows = []
    for ai, anchor in enumerate(ANCHORS):
        # Item x context x anchor x donor x condition; average inside the item.
        values = metrics["alias_margin_effect"][:, [1, 3], ai].mean(axis=(1, 2))
        summaries = {}
        for ci, (name, (positive, negative)) in enumerate(CONTRASTS.items()):
            delta = (
                values[:, CONDITIONS.index(positive)]
                - values[:, CONDITIONS.index(negative)]
            )
            summaries[name] = bootstrap_summary(
                delta, seed=2026092100 + ai * 100 + ci, replicates=replicates
            )
        passed = all(row["lower_95"] > 0 for row in summaries.values())
        rows.append(
            {
                "anchor": anchor,
                "calibration_pass": summaries["calibration"]["lower_95"] > 0,
                "pilot_screen_pass": passed,
                "contrasts": summaries,
                "selection_score": min(
                    row["lower_95"]
                    for key, row in summaries.items()
                    if key != "calibration"
                ),
            }
        )
    candidates = sorted(
        (row for row in rows if row["pilot_screen_pass"]),
        key=lambda row: (-row["selection_score"], row["anchor"]),
    )
    return {
        "sites": rows,
        "candidate_anchor": candidates[0]["anchor"] if candidates else None,
        "confirmatory_result": False,
        "reserve_access_allowed": False,
        "next_step": "prepare_separate_prospective_protocol"
        if candidates
        else "preserve_reserve_and_report_pilot_boundary",
    }


def analyze(run_root: Path, output: Path) -> dict[str, Any]:
    acquisition = read_json(run_root / "acquisition_receipt.json")
    require(
        acquisition["status"] == "pilot_acquisition_complete"
        and acquisition["target_items"] == 384,
        "Full pilot acquisition is required",
    )
    require(not output.exists(), "Analysis output already exists")
    spec = audit_spec(run_root / "specification.json")
    require(
        sha256(run_root / "specification.json") == acquisition["specification_sha256"],
        "Acquisition specification mismatch",
    )
    require(
        sha256(run_root / "source_states.npz") == acquisition["source_states_sha256"],
        "Source states changed",
    )
    with np.load(run_root / "source_states.npz", allow_pickle=False) as values:
        source = values["states"]
    metrics = {
        name: np.empty((384, 4, 2, 2, len(CONDITIONS)), np.float64)
        for name in ALL_METRICS
    }
    covered = np.zeros(384, dtype=bool)
    for name, digest in sorted(acquisition["chunks"].items()):
        path = run_root / name
        require(sha256(path / "receipt.json") == digest, "Changed chunk receipt")
        receipt = verify_chunk(path, acquisition["specification_sha256"])
        start, stop = int(receipt["start"]), int(receipt["stop"])
        require(not covered[start:stop].any(), "Overlapping chunks")
        covered[start:stop] = True
        with np.load(path / "states.npz", allow_pickle=False) as values:
            baseline, states, neutral = (
                values["baseline"],
                values["intervention"],
                values["neutral_reference"],
            )
            require(
                np.array_equal(values["item_indices"], np.arange(start, stop)),
                "Changed target item order",
            )
        for context in range(4):
            scored = score_states(
                states[:, context],
                baseline[:, context, 1],
                baseline[:, context, 2],
                source[:, context, 1],
                source[:, context, 2],
                np.asarray(spec["donor_indices"][start:stop]),
            )
            neutral_scored = score_states(
                neutral[:, context],
                baseline[:, context, 1],
                baseline[:, context, 2],
                source[:, context, 1],
                source[:, context, 2],
                np.asarray(spec["donor_indices"][start:stop]),
            )
            for metric in METRICS:
                metrics[metric][start:stop, context] = scored[metric]
                metrics[metric + "_effect"][start:stop, context] = (
                    scored[metric] - neutral_scored[metric]
                )
    require(covered.all(), "Missing target items")
    decision = pilot_decision(metrics)
    decision.update(
        {
            "protocol_id": PROTOCOL,
            "status": "pilot_analysis_complete",
            "target_items": 384,
            "context_order": [list(value) for value in CONTEXTS],
            "decision_context_indices": [1, 3],
            "metric": "own_alias_cosine_minus_max_128_fixed_source_alias_cosine",
            "reserve_model_forwards": 0,
            "acquisition_receipt_sha256": sha256(run_root / "acquisition_receipt.json"),
        }
    )
    summaries = []
    for context, (carrier, distance) in enumerate(CONTEXTS):
        for ai, anchor in enumerate(ANCHORS):
            for ki, condition in enumerate(CONDITIONS):
                summaries.append(
                    {
                        "carrier": carrier,
                        "distance": distance,
                        "anchor": anchor,
                        "condition": condition,
                        **{
                            metric: float(metrics[metric][:, context, ai, :, ki].mean())
                            for metric in ALL_METRICS
                        },
                    }
                )
    output.mkdir(parents=True)
    np.savez_compressed(output / "item_metrics.npz", **metrics)
    write_json(output / "pilot_result.json", decision)
    write_json(
        output / "condition_means.json", {"protocol_id": PROTOCOL, "rows": summaries}
    )
    write_json(
        output / "analysis_receipt.json",
        {
            "protocol_id": PROTOCOL,
            "status": "analysis_complete",
            "acquisition_receipt_sha256": sha256(run_root / "acquisition_receipt.json"),
            "specification_sha256": acquisition["specification_sha256"],
            "outputs": {
                name: sha256(output / name)
                for name in (
                    "item_metrics.npz",
                    "pilot_result.json",
                    "condition_means.json",
                )
            },
            "reserve_model_forwards": 0,
            "completed_at_utc": now(),
        },
    )
    return decision


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--model-path", type=Path, required=True)
    prep.add_argument("--output", type=Path, default=ROOT / SPEC)
    audit = sub.add_parser("audit")
    audit.add_argument("--specification", type=Path, default=ROOT / SPEC)
    execute = sub.add_parser("run")
    execute.add_argument("--model-path", type=Path, required=True)
    execute.add_argument("--specification", type=Path, default=ROOT / SPEC)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--canary", action="store_true")
    execute.add_argument("--canary-root", type=Path)
    execute.add_argument("--resume", action="store_true")
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--run-root", type=Path, required=True)
    analysis.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.model_path, args.output)
    elif args.command == "audit":
        audit_spec(args.specification)
        result = {
            "status": "pass",
            "specification_sha256": sha256(args.specification),
            "reserve_access_allowed": False,
        }
    elif args.command == "run":
        try:
            result = run(
                args.model_path,
                args.specification,
                args.output,
                canary=args.canary,
                resume=args.resume,
                canary_root=args.canary_root,
            )
        except Exception as error:
            if args.output.exists():
                write_json(
                    args.output / f"failure_{uuid.uuid4().hex}.json",
                    {
                        "protocol_id": PROTOCOL,
                        "status": "failed_no_scientific_decision",
                        "error_type": type(error).__name__,
                        "message": str(error),
                        "time_utc": now(),
                        "reserve_model_forwards": 0,
                    },
                )
            raise
    else:
        result = analyze(args.run_root, args.output)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
