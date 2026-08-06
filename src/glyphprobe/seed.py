from __future__ import annotations

import os
import random
from contextlib import contextmanager
from typing import Iterator

import numpy as np


def seed_everything(seed: int, *, deterministic_torch: bool = False) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        if deterministic_torch:
            torch.use_deterministic_algorithms(True, warn_only=True)
    except ImportError:
        pass


@contextmanager
def numpy_seed(seed: int) -> Iterator[np.random.Generator]:
    yield np.random.default_rng(seed)
