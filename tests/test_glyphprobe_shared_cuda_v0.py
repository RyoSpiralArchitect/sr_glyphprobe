"""Resource policy tests and CPU-only hook lifecycle simulation."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("shared_cuda", ROOT / "scripts/glyphprobe_shared_cuda_v0.py")
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)
POLICY = json.loads((ROOT / "configs/contextual_emoji_candidate_wording_v0.json").read_text())["compute_policy"]


def query(free=8540, processes="485817, 23540"):
    return lambda fields, process: processes if process else f"0, 32607, {free}"


def test_read_only_guard_allows_known_peer_but_reserves_headroom():
    r = shared.guard(POLICY, before_allocation=True, query=query())
    assert r["minimum_free_mib_applied"] == 7168
    assert r["observed_peer_pids"] == [485817]
    assert shared.guard(POLICY, query=query(4096))["free_mib"] == 4096


@pytest.mark.parametrize("free,processes,before", [
    (7167, "485817, 23540", True), (4095, "485817, 23540", False),
    (9000, "485817, 23000\n123, 100", False), (9000, "485817, N/A", False)])
def test_unsafe_or_unreadable_state_fails_closed(free, processes, before):
    with pytest.raises(ValueError):
        shared.guard(POLICY, before_allocation=before, query=query(free, processes))


def test_own_driver_allocation_bound(monkeypatch):
    monkeypatch.setattr(shared.os, "getpid", lambda: 22)
    assert shared.guard(POLICY, query=query(5000, "485817, 23000\n22, 3072"))["own_process_mib"] == 3072
    with pytest.raises(ValueError, match="allowance"):
        shared.guard(POLICY, query=query(5000, "485817, 23000\n22, 3073"))


@pytest.mark.parametrize("key,value", [("allocator_cap_mib", 6144), ("minimum_free_mib", 2048),
    ("allowed_peer_pids", []), ("parity_tolerance", 1e-6), ("minimum_call_interval_seconds", float("nan"))])
def test_no_silent_relaxation_of_policy(key, value):
    policy = copy.deepcopy(POLICY)
    policy[key] = value
    with pytest.raises(ValueError):
        shared.validate_policy(policy)


def test_hook_restoration_on_success_and_failure_cpu_simulation(monkeypatch):
    torch = pytest.importorskip("torch")
    calls = []
    original_to = torch.Tensor.to
    def simulated_to(tensor, *args, **kwargs):
        if args and isinstance(args[0], (str, torch.device)) and torch.device(args[0]).type == "cuda":
            calls.append("transfer")
            args = ("cpu",) + args[1:]
        return original_to(tensor, *args, **kwargs)
    monkeypatch.setattr(torch.Tensor, "to", simulated_to)
    cuda = SimpleNamespace(get_device_properties=lambda _: SimpleNamespace(total_memory=32607 * 2**20),
        set_per_process_memory_fraction=lambda *args: calls.append("cap"), synchronize=lambda: calls.append("sync"),
        empty_cache=lambda: calls.append("empty"))
    fake_torch = SimpleNamespace(cuda=cuda)
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.config = SimpleNamespace(tie_word_embeddings=True)
            self.model = torch.nn.Module()
            self.model.embed_tokens = torch.nn.Embedding(8, 4)
            self.model.layers = torch.nn.ModuleList([torch.nn.Linear(4, 4), torch.nn.Linear(4, 4)])
            self.model.norm = torch.nn.LayerNorm(4)
            self.model.rotary_emb = torch.nn.Identity()
            self.lm_head = torch.nn.Linear(4, 8, bias=False)
            self.lm_head.weight = self.model.embed_tokens.weight
        def forward(self, x):
            h = self.model.embed_tokens(x)
            for layer in self.model.layers:
                h = layer(h)
            return self.lm_head(self.model.norm(h))
    model = Toy().eval()
    inputs = torch.tensor([[1, 2]])
    with torch.inference_mode():
        expected = model(inputs).clone()
        stager = shared.DecoderWeightStager(model, fake_torch, POLICY)
        assert torch.equal(model(inputs), expected)
        assert calls.count("sync") == 2
        model.model.layers[0].forward = lambda _: (_ for _ in ()).throw(RuntimeError("synthetic layer failure"))
        with pytest.raises(RuntimeError):
            model(inputs)
        assert calls.count("sync") == 3
        assert all(p.device.type == "cpu" for p in model.parameters())
        stager.release()
        stager.release()
        assert calls.count("empty") == 1 and stager.handles == []
