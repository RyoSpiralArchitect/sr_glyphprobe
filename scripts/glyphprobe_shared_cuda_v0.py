#!/usr/bin/env python3
"""Explicit bounded CUDA coexistence policy; CPU storage, CUDA arithmetic.

Never changes another process. This is not a VRAM reservation, scheduler
priority, or a promise that another job cannot slow down or grow.
"""
from __future__ import annotations

import os
import math
import subprocess
import time
from datetime import datetime, timezone


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_policy(policy):
    require(policy["mode"] == "staged_shared_cuda", "Shared policy must be explicit")
    require(policy["allowed_peer_pids"] and all(type(p) is int and p > 0 for p in policy["allowed_peer_pids"]), "Explicit peer PIDs required")
    require(policy["allocator_cap_mib"] == 2560 and policy["driver_allowance_mib"] == 512
            and policy["minimum_free_mib"] == 4096, "Conservative fixed bounds required")
    interval = policy["minimum_call_interval_seconds"]
    require(type(interval) in (int, float) and math.isfinite(interval) and 0.1 <= interval <= 1, "Rate limit required")
    require(policy["parity_original_crossed_cells"] == 384 and policy["parity_tolerance"] == 0,
            "All historical crossed cells require exact numerical parity")
    require(policy["no_peer_priority_pause_or_process_changes"] is True and
            policy["not_a_reservation_or_zero_slowdown_guarantee"] is True, "Peer boundaries required")


def guard(policy, before_allocation=False, query=None):
    validate_policy(policy)
    def default_query(fields, process=False):
        flag = "--query-compute-apps=" if process else "--query-gpu="
        result = subprocess.run(["nvidia-smi", flag + fields, "--format=csv,noheader,nounits"],
                                capture_output=True, text=True, check=True, timeout=5)
        return result.stdout.strip()
    query = query or default_query
    gpu = query("index,memory.total,memory.free", False).splitlines()
    require(len(gpu) == 1, "Single observed GPU required")
    fields = [int(x.strip()) for x in gpu[0].split(",")]
    require(len(fields) == 3 and fields[0] == 0, "Unexpected GPU inventory")
    lines = [x.strip() for x in query("pid,used_gpu_memory", True).splitlines() if x.strip()]
    processes = {}
    for line in lines:
        pid, used = [x.strip() for x in line.split(",")]
        require(pid.isdigit() and used.isdigit(), "Unparseable process memory")
        processes[int(pid)] = int(used)
    peers = set(processes) - {os.getpid()}
    require(peers <= set(policy["allowed_peer_pids"]), f"Unapproved/new competing process: {sorted(peers)}")
    minimum = policy["minimum_free_mib"]
    if before_allocation:
        minimum += policy["allocator_cap_mib"] + policy["driver_allowance_mib"]
    require(fields[2] >= minimum, f"Free VRAM {fields[2]} MiB is below shared-run floor {minimum} MiB")
    own = processes.get(os.getpid(), 0)
    require(own <= policy["allocator_cap_mib"] + policy["driver_allowance_mib"], "Observed own process exceeded total allowance")
    return {"observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_mib": fields[1], "free_mib": fields[2], "minimum_free_mib_applied": minimum,
            "own_pid": os.getpid(), "own_process_mib": own, "observed_peer_pids": sorted(peers),
            "allowed_peer_pids": policy["allowed_peer_pids"],
            "process_memory_mib": {str(k): v for k, v in processes.items()}}


class DecoderWeightStager:
    """Keep immutable CPU copies; restore them after each layer, including errors."""
    def __init__(self, model, torch, policy):
        validate_policy(policy)
        self.model, self.torch, self.policy = model, torch, policy
        self.handles, self.cpu_copies = [], []
        self.released = False
        require(model.config.tie_word_embeddings is True, "Only the pinned tied-embedding Llama is supported")
        require(all(p.device.type == "cpu" for p in model.parameters()), "Model must start on CPU")
        try:
            self._install()
        except BaseException:
            self.release()
            raise

    def _install(self):
        model, torch, policy = self.model, self.torch, self.policy
        total = torch.cuda.get_device_properties(0).total_memory
        torch.cuda.set_per_process_memory_fraction(policy["allocator_cap_mib"] * 2**20 / total, 0)
        model.model.embed_tokens.to("cuda")
        model.lm_head.weight = model.model.embed_tokens.weight
        model.model.norm.to("cuda")
        model.model.rotary_emb.to("cuda")
        for layer in model.model.layers:
            params = [(p, p.detach()) for p in layer.parameters()]
            buffers = [(module, key, value) for module in layer.modules()
                       for key, value in module._buffers.items() if value is not None]
            self.cpu_copies.append((params, buffers))
            def restore(params=params, buffers=buffers):
                for parameter, cpu in params:
                    parameter.data = cpu
                for module, key, cpu in buffers:
                    module._buffers[key] = cpu
            def before(module, args, params=params, buffers=buffers, restore=restore):
                try:
                    for parameter, cpu in params:
                        parameter.data = cpu.to("cuda")
                    for owner, key, cpu in buffers:
                        owner._buffers[key] = cpu.to("cuda")
                except BaseException:
                    restore()
                    raise
            def after(module, args, output, restore=restore):
                try:
                    self.torch.cuda.synchronize()
                finally:
                    restore()
                return output
            self.handles.append(layer.register_forward_pre_hook(before))
            self.handles.append(layer.register_forward_hook(after, always_call=True))
        self.last_call = None

    def before_call(self):
        require(not self.released, "Staged model has already been released")
        if self.last_call is not None:
            time.sleep(max(0.0, self.policy["minimum_call_interval_seconds"] - (time.monotonic() - self.last_call)))
        observation = guard(self.policy)
        self.last_call = time.monotonic()
        return observation

    def release(self):
        if self.released:
            return
        for handle in self.handles:
            handle.remove()
        self.handles.clear()
        for params, buffers in self.cpu_copies:
            for parameter, cpu in params:
                parameter.data = cpu
            for module, key, cpu in buffers:
                module._buffers[key] = cpu
        self.model.to("cpu")
        self.torch.cuda.empty_cache()
        self.released = True
