#!/usr/bin/env python3
"""Cache the random-direction null across runs.

Every runner in this directory builds its null the same way: N gaussian
directions, RMS-matched to `alpha * rms(target activation)`, injected at
`resid_post / last_nonpad`, seeded deterministically. Given the same protocol
AND the same numeric stack the result is bit-identical, so rebuilding it is pure
waste — six runs here have each spent roughly 2,000 forwards (~6 minutes)
reproducing numbers that were already on disk.

The key covers everything that can change a null value: the seed formula, the
target prompt *text*, alpha, the layer, the draw count, the model path, the
site/position/metric, the metric kwargs, **and the numeric stack** (device,
dtype, tokenizer flag, torch/transformers/numpy versions). The last group
matters because this sandbox deliberately does not pin library versions — a
cache keyed without it would serve fp32/MPS nulls to a bf16 or CPU rerun, and
every ratio and exceedance count downstream would be computed against a
denominator from a different stack.

Change anything in the key and the key changes, so a stale value cannot be
served: the failure mode is a redundant rebuild, never a wrong number. A
corrupt or unreadable cache file degrades the same way.

The cache is derived data keyed to an unpinned stack, so `results/_nullcache/`
is gitignored — it must not travel to a machine whose libraries differ.

Usage:

    from nullcache import NullCache
    nc = NullCache(out_dir, model_path=..., alpha=..., n=...,
                   seed_formula="...", stack=NullCache.stack_fingerprint(cfg),
                   metric_kwargs=MK)
    vals = nc.get_or_build(layer=L, target_name=n, target_prompt=p,
                           build=lambda: [...N floats...])
    nc.save()          # safe to call repeatedly; merges with what is on disk

`vals` is the list of KL draws, so callers can take a median, an exceedance
count or a standard deviation as they see fit.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

_RESERVED = {"model_path", "alpha", "n", "seed_formula", "site", "position",
             "metric", "normalisation", "metric_kwargs", "stack"}


class NullCache:
    """Protocol-keyed cache of null KL draws, one JSON file per cache identity."""

    @staticmethod
    def stack_fingerprint(cfg=None) -> dict:
        """Everything about the numeric stack that can move a null value."""
        out = {}
        for mod in ("torch", "transformers", "numpy"):
            try:
                out[mod] = __import__(mod).__version__
            except Exception:                     # pragma: no cover - env dependent
                out[mod] = "unavailable"
        if cfg is not None:
            for attr in ("kind", "device", "dtype", "add_special_tokens"):
                out[attr] = str(getattr(cfg, attr, None))
        return out

    def __init__(self, out_dir, *, model_path: str, alpha: float, n: int,
                 seed_formula: str, stack: dict, metric_kwargs: dict | None = None,
                 site: str = "resid_post", position: str = "last_nonpad",
                 metric: str = "kl_base_to_intervened",
                 extra: dict | None = None, verbose: bool = True):
        extra = dict(extra or {})
        clash = _RESERVED & set(extra)
        if clash:
            raise ValueError(f"extra may not override protocol keys: {sorted(clash)}")
        self.dir = Path(out_dir) / "_nullcache"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.identity = {
            "model_path": model_path, "alpha": float(alpha), "n": int(n),
            "seed_formula": seed_formula, "site": site, "position": position,
            "metric": metric, "normalisation": "rms_matched_to_alpha_times_target_rms",
            "metric_kwargs": dict(sorted((metric_kwargs or {}).items())),
            "stack": dict(sorted(stack.items())),
            **extra,
        }
        self.key = hashlib.sha256(
            json.dumps(self.identity, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:16]
        self.path = self.dir / f"{self.key}.json"
        self.verbose = verbose
        self.hits = self.misses = 0
        self.cells = self._read_disk()

    def _read_disk(self) -> dict:
        """A corrupt or unreadable cache must cost a rebuild, never a crash."""
        if not self.path.exists():
            return {}
        try:
            blob = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            if self.verbose:
                print(f"null cache {self.key}: unreadable ({type(exc).__name__}), "
                      "rebuilding from scratch")
            return {}
        if blob.get("identity") != self.identity:      # hash-collision guard
            return {}
        cells = blob.get("cells", {})
        return {k: v for k, v in cells.items()
                if isinstance(v, list) and len(v) == self.identity["n"]}

    @staticmethod
    def _cell(layer: int, target_name: str, target_prompt: str) -> str:
        # the prompt text is part of the key, not just its name, so renaming a
        # target cannot silently reuse another target's draws
        h = hashlib.sha256(target_prompt.encode("utf-8")).hexdigest()[:12]
        return f"L{int(layer)}|{target_name}|{h}"

    def _check(self, vals, where: str) -> list[float]:
        if len(vals) != self.identity["n"]:
            raise ValueError(f"null {where} has {len(vals)} draws, "
                             f"expected {self.identity['n']}")
        return [float(v) for v in vals]

    def get_or_build(self, *, layer: int, target_name: str, target_prompt: str,
                     build) -> list[float]:
        cell = self._cell(layer, target_name, target_prompt)
        if cell in self.cells:
            self.hits += 1
            return self._check(self.cells[cell], "from cache")
        vals = self._check(build(), "from builder")
        self.cells[cell] = vals
        self.misses += 1
        return list(vals)

    def save(self) -> None:
        """Merge with whatever is on disk, then write atomically.

        Merging matters because the runners share one cache identity and may run
        concurrently; a blind overwrite would discard the other run's cells.
        """
        merged = dict(self._read_disk())
        merged.update(self.cells)
        self.cells = merged
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(
            {"identity": self.identity, "cells": merged, "n_cells": len(merged),
             "written": time.strftime("%Y-%m-%dT%H:%M:%S")},
            ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)
        if self.verbose:
            print(f"null cache {self.key}: {self.hits} hit / {self.misses} miss "
                  f"({self.hits * self.identity['n']} forwards skipped), "
                  f"{len(merged)} cells on disk", flush=True)

    def report(self) -> dict:
        return {"key": self.key, "path": str(self.path), "hits": self.hits,
                "misses": self.misses,
                "forwards_skipped": self.hits * self.identity["n"],
                "identity": self.identity}
