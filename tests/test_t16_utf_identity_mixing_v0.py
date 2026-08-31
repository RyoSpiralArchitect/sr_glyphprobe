from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "t16_utf_identity_mixing_v0.py"
SPEC = importlib.util.spec_from_file_location("t16_utf", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_panel_codepoints_and_factorial_counts() -> None:
    result = MODULE.audit_design()
    assert result["status"] == "design_pass_zero_t16utf_model_forwards"
    assert result["records_per_model"] == 1_440
    assert result["unique_prompts_per_model"] == 1_248
    assert result["model_forwards"] == 0


def test_exact_clone_repeats_bytes() -> None:
    for system_index, system in enumerate(MODULE._systems()):
        for rotation in MODULE.ROTATIONS:
            anchor = system["items"][rotation]["glyph"]
            for n in MODULE.N_VALUES:
                sequence = MODULE._sequence(
                    system_index, rotation, n, "clone_exact_utf"
                )
                assert sequence == anchor * n
                assert sequence.encode("utf-8") == anchor.encode("utf-8") * n


def test_all_conditions_share_anchor_and_n1_prompt() -> None:
    grouped: dict[tuple[str, int, str], list[dict[str, object]]] = {}
    for row in MODULE.records():
        key = (str(row["system_id"]), int(row["rotation"]), str(row["wrapper_id"]))
        if row["n"] == 1:
            grouped.setdefault(key, []).append(row)
    assert len(grouped) == 96
    for values in grouped.values():
        assert {row["mixture"] for row in values} == set(MODULE.MIXTURES)
        assert len({row["sequence_sha256"] for row in values}) == 1
        assert len({row["unique_prompt_index"] for row in values}) == 1


def test_cross_mix_cycles_frozen_system_order() -> None:
    sequence = MODULE._sequence(0, 0, 6, "cross_system_mix")
    expected = "".join(system["items"][0]["glyph"] for system in MODULE._systems())
    assert sequence == expected

