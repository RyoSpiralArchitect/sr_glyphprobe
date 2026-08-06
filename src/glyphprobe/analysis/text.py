from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any


_WORD = re.compile(r"\w+", flags=re.UNICODE)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+", flags=re.MULTILINE)


def _words(text: str) -> list[str]:
    return [value.casefold() for value in _WORD.findall(text)]


def text_delta_metrics(baseline: str, intervened: str, *, glyph: str) -> dict[str, Any]:
    base_words = _words(baseline)
    changed_words = _words(intervened)
    base_set = set(base_words)
    changed_set = set(changed_words)
    return {
        "char_length_baseline": len(baseline),
        "char_length_intervened": len(intervened),
        "char_length_delta": len(intervened) - len(baseline),
        "word_count_baseline": len(base_words),
        "word_count_intervened": len(changed_words),
        "word_count_delta": len(changed_words) - len(base_words),
        "sequence_similarity": float(SequenceMatcher(None, baseline, intervened).ratio()),
        "lexical_jaccard": float(
            len(base_set & changed_set) / max(len(base_set | changed_set), 1)
        ),
        "unique_word_ratio_baseline": float(len(base_set) / max(len(base_words), 1)),
        "unique_word_ratio_intervened": float(len(changed_set) / max(len(changed_words), 1)),
        "line_count_delta": intervened.count("\n") - baseline.count("\n"),
        "bullet_count_baseline": len(_BULLET.findall(baseline)),
        "bullet_count_intervened": len(_BULLET.findall(intervened)),
        "glyph_echo_count": intervened.count(glyph),
        "exact_match": baseline == intervened,
    }
