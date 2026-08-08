"""Minimal stdlib-json-backed stand-in for orjson (smoke/verify only).

glyphprobe.io uses OPT_SORT_KEYS, OPT_INDENT_2, and dumps(..., default=,
option=) -> bytes. For the manifest verification the data is ASCII-only
{relpath: {"bytes": int, "sha256": str}}, so json.dumps with matching
separators + sort_keys is byte-identical to orjson, giving the same sha256.
"""
from __future__ import annotations

import json as _json

OPT_SORT_KEYS = 1 << 0
OPT_INDENT_2 = 1 << 1
OPT_SERIALIZE_NUMPY = 1 << 2
OPT_APPEND_NEWLINE = 1 << 3


def dumps(value, default=None, option: int = 0) -> bytes:
    indent = 2 if (option & OPT_INDENT_2) else None
    text = _json.dumps(
        value,
        default=default,
        sort_keys=bool(option & OPT_SORT_KEYS),
        indent=indent,
        ensure_ascii=False,
        separators=(",", ":") if indent is None else (",", ": "),
    )
    if option & OPT_APPEND_NEWLINE:
        text += "\n"
    return text.encode("utf-8")


def loads(data):
    if isinstance(data, (bytes, bytearray, memoryview)):
        data = bytes(data).decode("utf-8")
    return _json.loads(data)
