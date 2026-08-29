from __future__ import annotations

import importlib.util
from pathlib import Path
import inspect
from types import SimpleNamespace

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "emoji_steering_specificity_harvest_v0.py"
SPEC = importlib.util.spec_from_file_location(
    "emoji_steering_specificity_harvest_v0", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
harvest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harvest)


def test_design_arithmetic_and_protected_boundary() -> None:
    value = harvest.audit_design()
    assert value["status"] == "pass"
    assert value["population_items"] == 192
    assert value["present_item_views"] == 912
    assert value["source_wrappers"] == 4
    assert value["public_targets"] == 32
    assert value["model_cells"] == 9
    assert value["pilot_model_cells"] == 3
    assert value["item_intervention_directions_per_model"] == 552
    assert value["system_view_prototypes_per_model"] == 28
    assert value["pilot_response_rows_per_model"] == 127_744
    assert value["pilot_response_rows_total"] == 383_232
    assert value["protected_target_files_opened"] == 0
    assert value["model_forward_sequences"] == 0


def test_population_is_the_already_exposed_depth_population() -> None:
    rows = harvest.population()
    assert [row["depth_index"] for row in rows] == list(range(192))
    assert all(row["included_in_depth_subset"] for row in rows)
    assert all(row["role"] != "reserve_unrun" for row in rows)
    assert sum(len(harvest.available_views(row)) for row in rows) == 912


def test_depth_mapping_is_unique_and_ends_at_last_block() -> None:
    for role in harvest.model_roles():
        indices = harvest.layer_indices(role)
        layers = int(harvest.t10._model_spec(role)["expected_num_layers"])
        assert len(indices) == len(set(indices)) == 8
        assert indices == tuple(sorted(indices))
        assert indices[-1] == layers - 1


def test_countsketch_hash_is_deterministic_and_total() -> None:
    first_bucket, first_sign = harvest._splitmix64_arrays(257, 32, 2026082907)
    second_bucket, second_sign = harvest._splitmix64_arrays(257, 32, 2026082907)
    assert np.array_equal(first_bucket, second_bucket)
    assert np.array_equal(first_sign, second_sign)
    assert first_bucket.shape == first_sign.shape == (257,)
    assert first_bucket.min() >= 0 and first_bucket.max() < 32
    assert set(np.unique(first_sign)) == {-1.0, 1.0}


def test_response_metrics_zero_and_nonzero_paths() -> None:
    baseline = torch.tensor([[1.0, 0.5, -0.25, 0.0]], dtype=torch.float32)
    intervened = torch.cat(
        (baseline, baseline + torch.tensor([[0.0, 0.2, 0.0, -0.1]])), dim=0
    )
    bucket = torch.tensor([[0, 1, 2, 3]], dtype=torch.long)
    sign = torch.ones((1, 4), dtype=torch.float32)
    value = harvest._response_metrics(
        torch=torch,
        baseline=baseline.expand(2, -1),
        intervened=intervened,
        sketch_bucket=bucket,
        sketch_sign=sign,
        top_k=2,
        sketch_dimension=4,
    )
    assert value["kl"].shape == (2,)
    assert value["positive_ids"].shape == (2, 2)
    assert value["sketch"].shape == (2, 4)
    assert value["kl"][0] == 0.0
    assert value["delta_rms"][0] == 0.0
    assert value["kl"][1] > 0.0
    assert value["delta_rms"][1] > 0.0


def test_item_view_count_matches_frozen_contract() -> None:
    rows = harvest.population()
    count = sum(
        sum(view in harvest.available_views(row) for view in harvest.ITEM_VIEW_ORDER)
        for row in rows
    )
    assert count == 552
    assert count * 32 * 2 == 35_328


def test_queue_script_preserves_frozen_resource_order() -> None:
    text = (
        ROOT / "scripts" / "run_emoji_steering_specificity_harvest_v0_queue.sh"
    ).read_text(encoding="utf-8")
    role_block = text.split("roles=(", 1)[1].split(")", 1)[0]
    listed_roles = [line.strip() for line in role_block.splitlines() if line.strip()]
    assert listed_roles == list(harvest.model_roles())
    assert '>>"$log_dir/$role.log"' in text
    assert 'model_args=(--model-path "$llama32_model_path")' in text
    assert 'model_args=(--model-path "$smollm2_model_path")' in text


def test_runner_uses_t13eh_owned_model_loader() -> None:
    source = inspect.getsource(harvest._load_model)
    assert "t11._load_model" not in source
    assert "audit_preflight" in source
    assert "model_artifact_receipt" in source


class _ToyTokenizer:
    pad_token_id = 0
    eos_token_id = 1

    def __call__(self, text: str, **_kwargs: object) -> dict[str, list[int]]:
        return {"input_ids": [2 + (ord(char) % 62) for char in text]}

    def decode(self, ids: list[int], **_kwargs: object) -> str:
        return " ".join(str(value) for value in ids)


class _ToyBlock(torch.nn.Module):
    def __init__(self, width: int) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(width, width, bias=False)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.linear(value))


class _ToyModel(torch.nn.Module):
    def __init__(self, width: int = 8, vocab: int = 64) -> None:
        super().__init__()
        torch.manual_seed(7)
        self.embedding = torch.nn.Embedding(vocab, width)
        self.layers = torch.nn.ModuleList([_ToyBlock(width), _ToyBlock(width)])
        self.head = torch.nn.Linear(width, vocab, bias=False)

    def forward(self, input_ids: torch.Tensor, **_kwargs: object) -> SimpleNamespace:
        value = self.embedding(input_ids)
        for block in self.layers:
            value = block(value)
        return SimpleNamespace(logits=self.head(value))


def test_capture_and_intervention_hooks_on_toy_model() -> None:
    model = _ToyModel().eval()
    tokenizer = _ToyTokenizer()
    activations, logits, lengths = harvest._capture_prompt_batch(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        blocks=model.layers,
        sites=(0, 1),
        prompts=("ab", "abcd"),
        return_logits=True,
    )
    assert activations.shape == (2, 2, 8)
    assert logits is not None and logits.shape == (2, 64)
    assert lengths == [2, 4]

    bucket_np, sign_np = harvest._splitmix64_arrays(64, 256, 2026082907)
    value = harvest._intervene_batch(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        block=model.layers[0],
        prompt="abcd",
        vectors=np.stack((np.zeros(8, dtype=np.float32), np.ones(8, dtype=np.float32))),
        sketch_bucket=torch.tensor(bucket_np, dtype=torch.long).unsqueeze(0),
        sketch_sign=torch.tensor(sign_np, dtype=torch.float32).unsqueeze(0),
    )
    assert value["kl"][0] == 0.0
    assert value["delta_rms"][0] == 0.0
    assert value["kl"][1] > 0.0
    assert value["sketch"].shape == (2, 256)
