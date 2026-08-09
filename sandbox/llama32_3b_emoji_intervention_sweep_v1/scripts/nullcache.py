#!/usr/bin/env python3
"""Cache the random-direction null across runs.

Every runner in this directory builds its null the same way: N gaussian
directions, RMS-matched to `alpha * rms(target activation)`, injected at
`resid_post / last_nonpad`, seeded deterministically. Given the same protocol
the result is bit-identical, so rebuilding it is pure waste — six runs here have
each spent roughly 2,000 forwards (~6 minutes) reproducing numbers that were
already on disk.

The cache key is a hash of everything that can change a null value: the seed
formula, the target prompt text, alpha, the layer, the draw count, the model
path and the metric settings. Change any of them and the key changes, so a stale
value can never be served — the failure mode is a redundant rebuild, never a
wrong number.

Usage:

    from nullcache import NullCache
    nc = NullCache(out_dir, model_path=..., alpha=..., n=..., seed_formula="...")
    vals = nc.get_or_build(layer=L, target_name=n, target_prompt=p,
                           build=lambda: [...24 floats...])

`vals` is the list of KL values, so callers can take a median, an exceedance
count, or a standard deviation as they see fit.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


class NullCache:
    """Protocol-keyed cache of null KL draws, one JSON file per cache identity."""

    def __init__(self, out_dir, *, model_path: str, alpha: float, n: int,
                 seed_formula: str, site: str = "resid_post",
                 position: str = "last_nonpad", metric: str = "kl_base_to_intervened",
                 extra: dict | None = None, verbose: bool = True):
        self.dir = Path(out_dir) / "_nullcache"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.identity = {
            "model_path": model_path, "alpha": float(alpha), "n": int(n),
            "seed_formula": seed_formula, "site": site, "position": position,
            "metric": metric, "normalisation": "rms_matched_to_alpha_times_target_rms",
            **(extra or {}),
        }
        self.key = hashlib.sha256(
            json.dumps(self.identity, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:16]
        self.path = self.dir / f"{self.key}.json"
        self.verbose = verbose
        self.hits = self.misses = 0
        if self.path.exists():
            blob = json.loads(self.path.read_text(encoding="utf-8"))
            if blob.get("identity") != self.identity:      # hash collision guard
                self.cells = {}
            else:
                self.cells = blob.get("cells", {})
        else:
            self.cells = {}

    @staticmethod
    def _cell(layer: int, target_name: str, target_prompt: str) -> str:
        # the prompt text is part of the key, not just its name, so renaming a
        # target cannot silently reuse another target's draws
        h = hashlib.sha256(target_prompt.encode("utf-8")).hexdigest()[:12]
        return f"L{int(layer)}|{target_name}|{h}"

    def get_or_build(self, *, layer: int, target_name: str, target_prompt: str,
                     build) -> list[float]:
        cell = self._cell(layer, target_name, target_prompt)
        if cell in self.cells:
            self.hits += 1
            return list(self.cells[cell])
        vals = [float(v) for v in build()]
        if len(vals) != self.identity["n"]:
            raise ValueError(f"null builder returned {len(vals)} draws, "
                             f"expected {self.identity['n']}")
        self.cells[cell] = vals
        self.misses += 1
        return list(vals)

    def save(self) -> None:
        self.path.write_text(json.dumps(
            {"identity": self.identity, "cells": self.cells,
             "n_cells": len(self.cells), "written": time.strftime("%Y-%m-%dT%H:%M:%S")},
            ensure_ascii=False, indent=1), encoding="utf-8")
        if self.verbose:
            saved = self.hits * self.identity["n"]
            print(f"null cache {self.key}: {self.hits} hit / {self.misses} miss "
                  f"({saved} forwards skipped) -> {self.path.name}")

    def report(self) -> dict:
        return {"key": self.key, "path": str(self.path), "hits": self.hits,
                "misses": self.misses, "forwards_skipped": self.hits * self.identity["n"]}
